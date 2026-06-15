# AI Pipeline Audit

**Date:** 2026-06-15  
**Author:** Lead Validation Engineer  
**Status:** COMPLETE

---

## 1. Agent Responsibilities

### 1.1 Spec Parser Agent
- **File:** `v1_core/agents/spec_parser_agent.py`
- **Position:** FIRST node in every pipeline
- **Input:** `state.spec` — natural language hardware specification
- **Output:** `state.spec_analysis` — structured JSON with module_name, design_type, inputs, outputs, behavior, corner_cases, clock, reset
- **LLM:** deepseek-v4-flash
- **Prompt Style:** Structured JSON generation with required schema
- **Failure Mode:** Returns empty analysis (`{"design_type": "unknown"}`) on JSON parse failure
- **Strengths:** Simple prompt, explicit JSON schema, markdown stripping
- **Weaknesses:** No input validation beyond JSON parse, single-shot (no retry on failure), no spec versioning

### 1.2 Verification Planner Agent
- **File:** `v1_core/agents/verification_planner_agent.py`
- **Position:** SECOND node (after spec_parser, before rtl_gen)
- **Input:** `state.spec_analysis`
- **Output:** `state.verification_plan` — structured JSON with 3 verification tiers, reference_model_code, forbidden_behaviors, timing_requirements
- **LLM:** deepseek-v4-flash
- **Prompt Style:** Generates tiered verification plan with reference model Python function
- **Failure Mode:** Returns empty plan on JSON parse failure
- **Strengths:** Forces generation of reference model function, enforces 3-tier structure
- **Weaknesses:** Generated reference_model_code may not be syntactically valid Python; no validation of reference model; single-shot generation

### 1.3 RTL Generation Agent
- **File:** `v1_core/agents/rtl_gen_agent.py`
- **Position:** THIRD node (after verification_planner)
- **Input:** `state.spec`, `state.spec_analysis`, `state.design_name`
- **Output:** `state.rtl_code` — Verilog HDL
- **LLM:** deepseek-v4-flash
- **Prompt Style:** Verilog generation with strict rules (synthesizable only, clean coding)
- **Strengths:** Forces module name to match design_name, strips code fences
- **Weaknesses:** No linting or syntax validation of generated Verilog; no width/signal consistency check; no test for sensitivity list correctness

### 1.4 Testbench Generation Agent
- **File:** `v1_core/agents/testbench_agent.py`
- **Position:** FOURTH node (after rtl_gen)
- **Input:** `state.rtl_code`, `state.verification_plan`, `state.spec_analysis`, `state.iteration`
- **Output:** `state.testbench_code` — cocotb Python testbench
- **LLM:** deepseek-v4-flash
- **Prompt Style:** Cocotb 2.x compliant testbench with reference model, FIFO-specific requirements, timing-specific requirements
- **Special Cases:** FIFO detection appends FIFO_TB_REQUIREMENTS; timing parameter detection appends TIMING_TB_REQUIREMENTS
- **Strengths:** Uses verification plan reference_model_code; includes regeneration note for fix loop; appends specialized test requirements by design type
- **Weaknesses:** FIFO detection is heuristic (string match); long prompt may cause truncation; no testbench syntax validation before invocation

### 1.5 Simulation Agent
- **File:** `v1_core/agents/simulation_agent.py`
- **Position:** FIFTH node (after testbench)
- **Input:** `state.rtl_code`, `state.testbench_code`, `state.design_name`
- **Output:** `state.sim_log`, `state.sim_passed`
- **Tool:** `simulation_server.py` (Icarus Verilog + cocotb via MCP)
- **Strengths:** Writes files to workspace, handles reference vs generated testbench paths
- **Weaknesses:** No timeout enforcement on simulation; no crash recovery

### 1.6 Log Analysis Agent
- **File:** `v1_core/agents/log_analysis_agent.py`
- **Position:** SIXTH node (only runs when simulation fails)
- **Input:** `state.sim_log`, `state.rtl_code`, `state.verification_plan`
- **Output:** `state.error_analysis` — structured error classification with ERROR_TYPE, LOCATION, CAUSE, EXACT_FIX, FIX_SUGGESTION, KEYWORDS
- **LLM:** deepseek-v4-flash with thinking mode enabled
- **Error Taxonomy:** SYNTAX, WIDTH, LOGIC, TIMING, COVERAGE, UNKNOWN
- **Memory Integration:** Calls `retrieve_skills()` from Trace2Skill with design category and error keywords
- **Strengths:** Structured error classification; integrates Trace2Skill memory; includes verification plan context for debugging
- **Weaknesses:** Response parsing is line-based (brittle); EXACT_FIX field quality depends on LLM accuracy; UNKNOWN type is a catch-all

### 1.7 Fix Agent
- **File:** `v1_core/agents/fix_agent.py`
- **Position:** SEVENTH node (after log_analysis)
- **Input:** `state.error_analysis`, `state.trace2skill_hits`, `state.rtl_code`, `state.verification_plan`
- **Output:** `state.rtl_code` (corrected), `state.testbench_code` (cleared for regeneration), `state.iteration` (incremented)
- **LLM:** deepseek-v4-flash (simple) or deepseek-v4-flash with thinking (LOGIC/TIMING errors)
- **Memory Integration:** Calls `store_skill()` after every fix attempt
- **Strengths:** Uses EXACT_FIX from log analysis for targeted correction; limits Trace2Skill hits for FSM to reduce noise; clears testbench for full regeneration after fix
- **Weaknesses:** Regenerates ENTIRE module for a single-line change (risks introducing new issues); no surgical line-level editing capability; stores fix even if fix didn't actually pass simulation

### 1.8 Orchestrator
- **File:** `v1_core/agents/orchestrator.py`
- **Role:** Defines PipelineState TypedDict with all shared state fields

---

## 2. Current Flow

### V1 Pipeline Flow (v1_core/pipeline.py)
```
spec_parser → verification_planner → rtl_gen → testbench → simulation
                                                                |
                                                    (fail)      |   (pass)
                                                    ↓           ↓
                                              log_analysis → END
                                                    ↓
                                                fix
                                                    ↓
                                              testbench (regenerated)
                                                    ↓
                                              simulation (loop)
```

### V2 Pipeline Flow (v2_verification/pipeline.py)
```
spec_parser → verification_planner → rtl_gen → testbench → simulation
                                                                |
                                                    (fail)      |   (pass)
                                                    ↓           ↓
                                              log_analysis → synthesis
                                                    ↓           |
                                                fix           sta
                                                    ↓        /    \
                                              testbench  timing   timing
                                                    ↓      met    NOT met
                                              simulation   |       |
                                                (loop)    END   timing_opt
                                                                     |
                                                                 synthesis
                                                                     |
                                                                   sta (loop max 3×)
```

### Key Flow Decisions
1. **Fix loop max iterations:** 5 (configurable via state.max_iterations)
2. **Convergence detection:** Stuck at 2 consecutive identical errors → force END
3. **Reference flow shortcut:** If `rtl_code` is provided, skip rtl_gen; if `reference_tb_path` provided, skip testbench
4. **V2 timing opt loop max:** 3 iterations
5. **Safe agent wrapping:** V2 wraps all agent calls in try/except so agent crashes don't kill pipeline

---

## 3. Current Limitations

### 3.1 LLM-Dependent Weaknesses

| Limitation | Impact | Severity |
|-----------|--------|----------|
| Single-shot generation (no retry on parse failure) | Empty spec_analysis / verification_plan on JSON parse failure | High |
| No validation of generated Verilog syntax | Syntactically invalid Verilog wastes fix loop iterations | Medium |
| No validation of generated testbench Python syntax | Python syntax errors crash simulation | Medium |
| EXACT_FIX quality depends on LLM accuracy | Wrong fix guidance causes incorrect corrections | High |
| Full-module regeneration for single-line fix | Risk of introducing new bugs during fix | Medium |
| No semantic consistency check across generated files | RTL may not match spec_analysis may not match verification_plan | High |

### 3.2 Infrastructure Weaknesses

| Limitation | Impact | Severity |
|-----------|--------|----------|
| No simulation timeout | Infinite loop in Verilog hangs pipeline | Medium |
| No crash recovery in simulation agent | Icarus segfault kills pipeline | Medium |
| Trace2Skill grows unbounded | Skill file size increases indefinitely | Low |
| No parallel execution of agent tasks | Sequential execution = slower pipeline | Low |
| No caching of LLM responses | Identical prompts waste API calls | Medium |

### 3.3 Architectural Weaknesses

| Limitation | Impact | Severity |
|-----------|--------|----------|
| V1 code frozen, all new dev in v2_verification/ | V1 bugs never fixed | Medium |
| No diff-based fix (whole module replacement) | Fix agent can introduce regressions | High |
| No testbench comparison against verification plan | Testbench may not cover all required tests | Medium |
| Heuristic FIFO detection in testbench agent | Non-FIFO designs with "fifo" in code get wrong prompts | Low |
| No cross-benchmark skill consolidation | Skills stored per design type may duplicate | Low |
| Model router thinking mode not used for log_analysis | Log analysis might miss subtle errors despite thinking being available | Low |

### 3.4 Pipeline Integration Weaknesses

| Limitation | Impact | Severity |
|-----------|--------|----------|
| V2 pipeline treats all agent failures as non-fatal | Agent silently fails, state may be incomplete | Medium |
| No stage transition validation | Pipeline could skip stages if state is corrupted | Medium |
| No logging of LLM response times | Cannot detect API performance degradation | Low |
| recursion_limit=50 required for V2 pipeline | High iteration counts could hit recursion limit | Low |

---

## 4. Benchmark Coverage

### Current State

| Benchmark | Type | Cells | Spec | Reference RTL | Reference TB | Bug Files | Synthesizable | STA |
|-----------|------|-------|------|---------------|-------------|-----------|---------------|-----|
| alu_8bit | Combinational | 131 | ✅ spec.txt | ✅ reference_rtl.v | ✅ reference_tb.py | 2 bugs | ✅ | N/A (comb) |
| sync_fifo_8x16 | Sequential | 648 | ✅ spec.txt | ✅ reference_rtl.v | ✅ reference_tb.py | 2 bugs | ✅ | ✅ |
| fsm_traffic_light | FSM | 10 | ✅ spec.txt | ✅ reference_rtl.v | ✅ reference_tb.py | 2 bugs | ✅ | ✅ |
| uart_tx | Sequential | 180 | ✅ spec.txt | ✅ reference_rtl.v | ✅ reference_tb.py | 2 bugs | ✅ | ✅ |
| apb_slave | Protocol | 527 | ✅ spec.txt | ✅ reference_rtl.v | ✅ reference_tb.py | 2 bugs | ✅ | ✅ |

### Coverage Gaps

| Gap | Impact |
|-----|--------|
| Only 5 benchmarks, all small (<650 cells) | Not representative of real designs |
| No design with multiple clock domains | Cross-domain timing not tested |
| No design with asynchronous interfaces | CDC issues not tested |
| No design with external SRAM/DRAM interface | Memory interface not tested |
| No design with PLL/clock generator | Clock generation circuits not tested |
| All benchmarks are known-working designs | No adversarial or malicious RTL testing |

### Bug Injection Coverage

| Benchmark | Bug Class | Bug File | Type |
|-----------|-----------|----------|------|
| alu_8bit | Logic bug | bug_001_wrong_opcode.v | XNOR instead of XOR (opcode 100) |
| alu_8bit | Interface bug | bug_002_missing_zero_flag.v | zero_flag output never assigned |
| sync_fifo_8x16 | Boundary-condition bug | bug_001_wrong_full_flag.v | full threshold at 15 instead of 16 |
| sync_fifo_8x16 | RTL coding bug (no reset) | bug_002_no_reset.v | rst_n removed from all sequential blocks |
| fsm_traffic_light | Logic bug | bug_001_wrong_count.v | RED_COUNT changed from 15 to 10 |
| fsm_traffic_light | Logic bug | bug_002_wrong_transition.v | GREEN→RED and YELLOW→GREEN instead of correct transitions |
| uart_tx | Interface bug | bug_001_wrong_bit_order.v | MSB-first instead of LSB-first |
| uart_tx | Logic bug | bug_002_missing_stop_bit.v | DATA→IDLE skip, no stop bit |
| apb_slave | Interface bug | bug_001_wrong_address.v | PADDR[4:3] instead of [3:2] for address decode |
| apb_slave | Logic bug | bug_002_pslverr_inverted.v | PSLVERR asserts on valid addresses instead of invalid |

**Bug Class Distribution:**
- Logic bugs: 5 (wrong_opcode, wrong_count, wrong_transition, missing_stop_bit, pslverr_inverted)
- Interface bugs: 3 (missing_zero_flag, wrong_bit_order, wrong_address)
- Boundary-condition bugs: 1 (wrong_full_flag)
- RTL coding bugs: 1 (no_reset)
- Syntax bugs: 0

**Gap:** No syntax-related bug files exist. No test for the parser's SYNTAX error classification.

---

## 5. Bug Injection Infrastructure

### Injection Method
Bug injection is done via **pre-written Verilog files** stored in each benchmark's `bugs/` directory. Each bug file contains a single, targeted defect in an otherwise correct reference RTL. Files are human-readable with a comment header describing the injected bug.

### How Bugs Are Used
The `--rtl` flag in `main.py` loads a bug file instead of the reference RTL:
```bash
python main.py --benchmark alu_8bit --rtl benchmarks/alu_8bit/bugs/bug_001_wrong_opcode.v
```

The pipeline then runs normally: spec_parser → planner → (skip rtl_gen because RTL provided) → testbench → simulation. The fix loop should detect and repair the bug.

### Bug Categories Targeted
| Category | Description | Example |
|----------|-------------|---------|
| Syntax | Compile-error in Verilog | Missing semicolon, wrong port list |
| Logic | Wrong functional behavior | Wrong opcode, wrong count, wrong transition |
| Boundary | Off-by-one or edge | Wrong full flag threshold |
| Interface | Signal misuse | Wrong bit order, wrong address decode |
| RTL Coding | Style issues with functional impact | No reset, latch inference |

### Limitations of Current Infrastructure
1. **No syntax bugs** — All 10 existing bugs are logic/interface/boundary types. No Verilog syntax errors exist.
2. **Manual injection** — Bugs must be hand-written, not generated.
3. **No synthetic bugs** — All bugs are manually crafted to be "plausible" errors.
4. **No multi-bug tests** — Each file has exactly one bug.
5. **No bug severity levels** — No distinction between "obvious" and "subtle" bugs.
6. **No RTL coding style bugs** — No blocking-vs-nonblocking violations, no latch inference cases.
7. **No bug_003 files** — Only 2 bugs per benchmark (10 total, not 15+).

---

## 6. Trace2Skill Memory Analysis

### Skill Bank Structure
- **Storage:** JSON files in `skills/` directory, one per category
- **Categories:** combinational, fsm, fifo, axi, timing
- **Entry Schema:** id, category, error_type, pattern, fix, design_name, success_count, last_seen
- **Retrieval:** Matches error type + keyword scoring, returns top 3 sorted by score × success_count
- **Storage:** Called by fix_agent after EVERY fix attempt (regardless of success)

### Current Skill Counts
(To be populated after Phase 2 campaign)

### Observations
1. No eviction policy → skills accumulate forever
2. No quality scoring → stored even if fix didn't ultimately pass
3. Category guessing from design name is heuristic (e.g., "uart" → "fsm", "apb" → "axi")
4. Single-level keyword matching — no semantic similarity
5. No cross-category retrieval (FIFO errors won't help FSM designs)
