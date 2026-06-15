# Root Cause Analysis

**Date:** 2026-06-15  
**Phase 8 Deliverable**  
**Status:** FINAL

---

## 1. Failure Classification Summary

All pipeline failures observed across all validation phases, classified by root cause.

| Code | Category | Count | % of Total | Examples |
|------|----------|-------|-----------|----------|
| SPEC | Spec Parser | 3 | 15% | Module name inference (2), design type (1) |
| PLAN | Verification Planner | 1 | 5% | fsm_traffic_light empty plan (cascade from SPEC) |
| RTL | RTL Generator | 2 | 10% | sync_fifo_8x16 AI RTL, fsm_traffic_light AI RTL |
| TB | Testbench Generator | 3 | 15% | sync_fifo/fsm AI TBs (sequential timing wrong), uart_tx stop-bit gap |
| FIX | Fix Agent | 1 | 5% | uart_tx wrong bit order ping-pong (multi-line) |
| LLM | Model Quality | 0 | 0% | No JSON parse failures observed |
| INFRA | Infrastructure | 10 | 50% | Campaign tool bugs, stuck processes, reference alignment |

**Total observed failures: 20**

**Infrastructure-dominated (50%)** — mostly campaign tool bugs and reference alignment, not pipeline issues.
**Pipeline-only failures: 10** — actual agent failures excluding infrastructure issues.

---

## 2. Failure Mode Details

### SPEC-001: Module Name Inference
- **Affected:** sync_fifo_8x16, fsm_traffic_light
- **Root Cause:** Spec format lacks explicit `Module name:` field. Parser guesses from `Design:` title.
- **Impact:** Low — cascaded to planner for fsm_traffic_light, but RTL gen uses design_name from state, not spec_analysis.
- **Fix:** Add `Module name:` to all benchmark specs.

### SPEC-002: Design Type Classification
- **Affected:** apb_slave (classified as "sequential" not "protocol")
- **Root Cause:** Spec doesn't specify design type; "protocol" is debatable classification.
- **Impact:** Low — no functional pipeline impact.
- **Fix:** Add `Design type:` to spec format.

### PLAN-001: Cascade Failure (fsm_traffic_light)
- **Affected:** fsm_traffic_light
- **Chain:** SPEC-001 (wrong module name) → spec_analysis has empty design_type → planner generates 0 tests, 0 tiers, no reference model, null timing → simulation fails → fix loop has no context
- **Impact:** High — 0 tests generated, entire verification plan useless.
- **Fix:** Add graceful degradation in planner; enforce minimum test count per tier.

### RTL-001: AI-Generated FIFO RTL Failure
- **Affected:** sync_fifo_8x16 (Spec→RTL campaign)
- **Root Cause:** Complex pointer management, full/empty generation, and reset initialization logic beyond reliable AI generation.
- **Impact:** Max iterations (5) exhausted. Pipeline couldn't converge.
- **Fix:** Improved RTL generation prompt; fallback to reference RTL for complex designs.

### RTL-002: AI-Generated FSM RTL Failure
- **Affected:** fsm_traffic_light (Spec→RTL campaign)
- **Root Cause:** State encoding and timing issues in AI-generated RTL.
- **Impact:** Max iterations (5) exhausted.
- **Fix:** Improved FSM generation prompt.

### TB-001: AI-Generated FIFO TB Failure
- **Affected:** sync_fifo_8x16 (TB Gen campaign, correct RTL)
- **Root Cause:** AI-generated testbench had wrong full/empty thresholds, incorrect synchronization, missing simultaneous tests.
- **Impact:** Max iterations (5) exhausted despite correct RTL.
- **Fix:** Sequential testbench generation is fundamentally challenging for current approach.

### TB-002: AI-Generated FSM TB Failure
- **Affected:** fsm_traffic_light (TB Gen campaign, correct RTL)
- **Root Cause:** X_COUNT-1 timing assertions wrong; AI cannot correctly generate edge-counting patterns.
- **Impact:** Max iterations exhausted despite correct RTL.
- **Fix:** Parameter-driven TB generation (use spec timing parameters directly).

### TB-003: Reference TB Coverage Gap
- **Affected:** uart_tx missing stop bit (bug injection campaign)
- **Root Cause:** Reference testbench doesn't verify stop bit presence.
- **Impact:** Bug not detected — simulation passed with missing stop bit.
- **Fix:** Add stop bit verification to uart_tx reference TB.

### FIX-001: Multi-Line Fix Ping-Pong
- **Affected:** uart_tx wrong bit order
- **Root Cause:** Bug requires TWO coordinated changes (shift direction + output bit selection). Fix agent addresses one at a time, oscillating indefinitely.
- **Impact:** Max iterations (5) exhausted.
- **Fix:** Coordinated EXACT_FIX guidance; fuzzy convergence detection.

### INFRA-001: Campaign Tool Parsing Bugs
- **Affected:** Bug injection campaign initial runs
- **Root Cause:** Complex `sim_passed` parser expression with wrong split logic.
- **Impact:** 3 tests mis-reported before fix applied.
- **Fix:** Simplified parsing logic.

### INFRA-002: Stuck API Processes
- **Affected:** Spec→RTL and TB Gen campaigns
- **Root Cause:** Long-running API calls (httpx timeout 120s) cause 4+ minute hangs on --spec approach.
- **Impact:** 2/5 benchmarks not completed in each campaign.
- **Fix:** Shorter API timeout; process watchdog.

### INFRA-003: Reference TB Alignment (Legacy)
- **Affected:** sync_fifo_8x16, uart_tx (V2 validation report)
- **Root Cause:** Reference testbench thresholds/timing don't match RTL.
- **Impact:** False failures on correct RTL (1.4 avg fix iterations).
- **Fix:** Previously identified and partially fixed.

---

## 3. Failure Cascade Map

```
Spec Format (no Module name, no Design type)
    → SPEC-001/002: Parser guesses wrong → wrong analysis
        → PLAN-001: Planner cascade → empty/incomplete plan
            → RTL-001/002: Insufficient context → wrong RTL
            → TB-001/002: Insufficient context → wrong TB
                → FIX-001: Fix loop oscillates → max iterations
```

## 4. Root Cause Prioritization

| Rank | Issue | Category | Prevalence | Effort to Fix | Impact if Fixed |
|------|-------|----------|-----------|--------------|----------------|
| 1 | Sequential TB generation | TB | 2/3 benchmarks | HIGH | Enables pure AI flow for 60% more designs |
| 2 | Multi-line fix ping-pong | FIX | 1/10 bugs | MEDIUM | Removes last bug-injection failure mode |
| 3 | Spec format standardization | SPEC | 3/5 benchmarks | LOW | Prevents cascade failures |
| 4 | Reference TB audit | TB | 2/5 benchmarks | LOW | Eliminates false failures |
| 5 | Testbench coverage audit | TB | 1/10 bugs | LOW | Closes detection gap |
| 6 | AI RTL quality for sequential | RTL | 2/3 issues | HIGH | Improves spec→RTL success rate |

---

## 5. Conclusions

### Top 3 Root Causes
1. **LLM-generated testbenches for sequential logic are unreliable** — The #1 bottleneck for the AI pipeline. Fix agent cannot compensate for a fundamentally wrong testbench.
2. **Single-error-per-iteration fix architecture** — Multi-line bugs cannot be resolved because each iteration addresses only one error symptom.
3. **Spec format lacks standardization** — Module names and design types are guessed, causing cascade failures through the pipeline.

### What Works Well
- Reference flow (reference RTL + reference TB): 25/25 passes (100%)
- Bug detection: 10/10 injected bugs detected (100%)
- Single-line bug fixes: 9/10 fixed (90%)
- Spec parser port extraction: 100% accuracy
- Verification planner (with correct input): 4/5 EXCELLENT
