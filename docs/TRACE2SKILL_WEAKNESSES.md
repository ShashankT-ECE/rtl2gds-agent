# Trace2Skill Memory System — Weaknesses Document

**File:** `v1_core/utils/trace2skill.py` (107 lines)
**Storage backend:** 5 JSON files in `skills/` directory
**Total skills:** 207 (combinational=57, fifo=54, fsm=84, axi=12, timing=0)
**Last audited:** 2026-06-15

---

## 1. Storage Weaknesses

### 1a. Unconditional Storage After Every Fix Attempt

`fix_agent.py` line 129 calls `store_skill()` unconditionally after `call_llm()` returns, **regardless of whether the fix actually passes simulation**. The code at lines 126-135:

```python
logger.success("Fix generated — storing in Trace2Skill")

# Store this fix in Trace2Skill memory (category already computed above)
store_skill(
    category=category,
    error_type=error_type,
    pattern=error_analysis.get("CAUSE", "unknown pattern"),
    fix=error_analysis.get("FIX_SUGGESTION", ""),
    design_name=state["design_name"]
)
```

The `logger.success` message on line 126 is misleading — it prints "Fix generated" not "Fix **verified**". The pipeline may loop back to simulation and fail again, but the skill was already committed. This means **failed fixes pollute the skill bank** and are indistinguishable from successful ones.

### 1b. No Eviction Policy

`trace2skill.py` has no eviction mechanism:

- **No maximum size cap** — skills accumulate indefinitely (currently 207).
- **No LRU eviction** — old skills are never pruned.
- **No age-based deletion** — the `last_seen` field exists (line 66) but is a design name string, not a date. No timestamp field is written or checked.
- **No deduplication pressure** — the only dedup is exact pattern+error_type match (lines 49-53), which almost never fires (see 1d).

### 1c. Duplicate Patterns Across Categories — Verified

Reading the skill files confirms near-identical patterns stored as separate entries. Examples:

**combinational.json (57 entries):**
- `combinational_0000` through `combinational_0004` (5 entries): All describe "testbench syntax error on first line" with slightly different wording. All have `success_count=1`.
- `combinational_0005` through `combinational_0009` (5 entries): All describe "cocotb.runner module missing". All have `success_count=1`.
- `combinational_0010` through `combinational_0015` (6 entries): All describe "Makefile missing at workspace/cocotb_build/". All have `success_count=1`.
- `combinational_0050`, `combinational_0053`, `combinational_0055`: Three entries all describing "XOR implemented as XNOR" with different wording.
- `combinational_0052`, `combinational_0054`, `combinational_0056`: Three entries all describing "zero_flag never assigned".

**fifo.json (54 entries):**
- `fifo_0000` through `fifo_0004` (5 entries): All describe "Makefile missing" (same infrastructure error repeated across designs).
- `fifo_0020` through `fifo_0025` (6 entries): All describe "full flag asserts at count=15 instead of 16" or the inverse, each with slightly different wording.
- `fifo_0034` through `fifo_0040` (7 entries): Same "full threshold 15 vs 16" topic repeated.

**fsm.json (84 entries):**
- `fsm_0004` through `fsm_0018` (15 entries): All describe "counter increment vs state transition timing off-by-one" — variations on the same FSM timing bug.
- `fsm_0042` through `fsm_0060` (19 entries): All describe "tx_busy not deasserted in STOP state" — the same UART bug, iterated 19 times.
- `fsm_0063` through `fsm_0067` (5 entries): All describe "LSB-first vs MSB-first shift direction" for UART.

### 1d. All 207 Skills Have `success_count=1`

Every single skill across all 5 category files has `success_count=1`. The deduplication logic at `trace2skill.py` lines 49-53:

```python
for skill in bank["skills"]:
    if skill["pattern"] == skill["pattern"] and skill["error_type"] == error_type:
        skill["success_count"] += 1
```

...**never triggers** because identical bugs produce slightly different `pattern` strings each time. The `pattern` is populated from `error_analysis.get("CAUSE", "unknown pattern")` (fix_agent.py line 132), which is LLM-generated text. Even when the same root cause appears, the LLM words it differently each iteration, so the exact string match fails.

### 1e. No Cross-Category Deduplication

`store_skill()` (trace2skill.py lines 32-70) operates on a single category at a time. It loads one JSON file, checks for duplicates within that file only, and saves back to that file. An error pattern that occurs in both `sync_fifo_8x16` and `uart_tx` (e.g., "Makefile missing" which appears in `fifo_0000`, `fsm_0000`, and `combinational_0010`) creates separate entries in each category with no mechanism to consolidate.

### 1f. Missing and Unused Fields

- **`last_seen`** (trace2skill.py line 66): Stored as a design name string ("alu_8bit"), not a timestamp. Never used in retrieval, eviction, or reporting.
- **`design_name`** (trace2skill.py line 65): Stored but never used in retrieval. A skill from `alu_8bit` is equally relevant to `sync_fifo_8x16` according to the retrieval logic.
- **No timestamp field**: No `created_at` or `last_used_at` exists. Impossible to know which skills are stale.

---

## 2. Retrieval Weaknesses

### 2a. Single-Category Lookup

`log_analysis_agent.py` line 87 computes exactly **one** category via `_guess_category()` and calls `retrieve_skills()` once. If the guess is wrong, the correct category is never consulted. For example:
- `uart_tx` maps to `"fsm"` — fifo and combinational skills are invisible.
- `apb_slave` maps to `"axi"` — combinational skills (where many infrastructure fixes live) are invisible.

### 2b. Heuristic Category Guessing

`_guess_category()` at log_analysis_agent.py lines 106-117 uses simple substring matching:

```python
def _guess_category(design_name: str) -> str:
    name = design_name.lower()
    if "fifo" in name:           return "fifo"
    if "fsm" in name or "uart" in name or "spi" in name: return "fsm"
    if "axi" in name or "apb" in name: return "axi"
    if "timing" in name:         return "timing"
    return "combinational"
```

Problems:
- `uart_tx` is mapped to `"fsm"` even though its errors are protocol/logic issues, not FSM-specific patterns.
- `apb_slave` is mapped to `"axi"` even though APB is a separate bus protocol.
- Any design name containing "spi" (even `spi_master`) goes to `"fsm"`, which may be wrong.
- Defaults to `"combinational"` for unmatched names, which is semantically meaningless as a category.

### 2c. Primitive Keyword Matching

`trace2skill.py` line 92:

```python
score = sum(1 for kw in keywords if kw.lower() in skill["pattern"].lower())
```

This is a simple Python `in` substring containment check. Examples of failures:
- "clock" will NOT match "clk"
- "full" will NOT match "overflow" (semantically related)
- "threshold" will NOT match "count == 16" (semantically related)
- "lsb" will NOT match "bit 0"

No stemming, no synonym expansion, no embedding-based similarity.

### 2d. No Semantic Similarity

Two errors with identical root cause but different wording produce different pattern strings and will not match. Example from fifo.json:

- `fifo_0020`: "The full flag asserts at count=15 instead of count=16 after 16 writes (FIFO depth is 16)."
- `fifo_0028`: "The full flag is asserted when count reaches 15, but a 16-entry FIFO should assert full when count reaches 16."

These describe the same bug but share few overlapping keywords beyond "full", "FIFO", "count", "15", "16". If keywords from the log happened to be "full_flag", "threshold", "early" — none match either pattern and the skill is missed.

### 2e. Error Type Filter Is Too Strict

`trace2skill.py` line 90:

```python
if skill["error_type"] != error_type:
    continue
```

A `LOGIC` skill will never match a `WIDTH` query, even if the underlying fix is identical. For example, the `PCLK` vs `clk` port mismatch appears 9 times in `axi.json` with error types split between `SYNTAX` (axi_0000, axi_0003, axi_0004, axi_0006, axi_0007) and `LOGIC` (axi_0001, axi_0002, axi_0005, axi_0009). A SYNTAX query would miss the LOGIC entries and vice versa, even though the fix is identical.

### 2f. Hardcoded Limit of 3 Results

`trace2skill.py` line 97:

```python
return [s for _, s in matches[:3]]
```

The top 3 matches are returned regardless of total match count or score distribution. If all 57 combinational skills matched, only 3 would be returned. No pagination, no score threshold.

### 2g. FSM Special Case Further Limits Hits

`fix_agent.py` line 86:

```python
if category == "fsm":
    hits = hits[:1]
```

For FSM-category designs, hits are further reduced from 3 to 1. The comment says "limit to 1 hit for FSM to reduce noise" (line 83), but this actively hides relevant skills. FSM is the largest category (84 skills) with the most diversity (traffic light state machines, UART transmitters). Reducing hits aggressively here means the LLM sees almost no memory hints.

---

## 3. Integration Weaknesses

### 3a. Only 2 of 10 Agents Consume Trace2Skill

The pipeline has 8+ agents (spec_parser, verification_planner, rtl_gen, testbench, simulation, log_analysis, fix, plus V2 agents: synthesis, STA). Only two touch Trace2Skill:

| Agent | Action | File Reference |
|-------|--------|----------------|
| `log_analysis_agent` | Retrieves skills | log_analysis_agent.py line 87-91 |
| `fix_agent` | Consumes retrieved skills, stores new ones | fix_agent.py lines 83-93, 129-135 |

The following agents have NO interaction with Trace2Skill:
- `spec_parser_agent` — could contribute specs-to-skills mapping
- `verification_planner_agent`
- `rtl_gen_agent` — could learn from past RTL generation mistakes
- `testbench_agent` — could learn from past testbench bugs
- `simulation_agent`
- `synthesis_agent` (V2)
- `sta_agent` (V2)

### 3b. Prompt Instructions Undermine Retrieval Usefulness

`fix_agent.py` line 38 in the FIX_PROMPT:

```
The following are HINTS from memory — use them only if they directly match
this exact error. Do NOT apply them blindly:
```

This instruction tells the LLM to be **skeptical** of the memory system — the one mechanism designed to accelerate fixes. This creates perverse outcomes:
- When the skill is a poor LLM-generated paraphrase of the same bug, the LLM is told to ignore it ("only if they directly match").
- When the skill is genuinely useful but worded differently, the LLM is told to treat it skeptically.

### 3c. State Not Cleared Between Fix Iterations

`trace2skill_hits` is initialized as an empty list in `orchestrator.py` line 65. However, it is set once by `log_analysis_agent` (line 101) and never reset between fix iterations. The pipeline graph (pipeline.py) shows:

```
simulation → log_analysis → fix → testbench → simulation → log_analysis → ...
```

On the second pass through `log_analysis_agent`, `trace2skill_hits` is overwritten. However, there is no explicit clearing logic, and if an error occurs mid-pipeline, stale hits could persist from a previous run.

### 3d. No Pipeline-Level Logging or Instrumentation

`pipeline.py` does not log whether Trace2Skill returned hits, which skills were used, or whether they contributed to a fix. There is no instrumentation to measure:
- **Hit rate**: How often does retrieval return >=1 skill?
- **Precision**: How often is a retrieved skill actually relevant?
- **Fix acceleration**: Are fixes faster (fewer iterations) when hits exist?

The only logging is in `log_analysis_agent.py` lines 94-96, which logs hit count but not quality.

### 3e. `get_stats()` Prints But No Action Is Taken

`main.py` lines 96-101 call `get_stats()` after every run and log the skill counts per category. However, this data is never used to:
- Trigger eviction of over-represented categories
- Alert on unchecked growth
- Recommend deduplication
- Inform any automated decision

The count output is purely informational and has no feedback loop.

---

## 4. Data Quality Weaknesses

### 4a. 207 Skills, 0 Reinforced

Every single skill across all 5 categories has `success_count=1`. The deduplication logic (trace2skill.py lines 49-53) never increments because each pattern is a unique LLM-generated string. The system has **no ability to learn which patterns repeat** — it cannot distinguish between a one-off infrastructure glitch and a recurring design bug.

### 4b. Approximately 50% of Skills Are Infrastructure Errors, Not Design Bugs

Analysis of skill content reveals roughly half describe environment/configuration issues:

| Category | Infrastructure Skills | Count | Examples |
|----------|---------------------|-------|----------|
| combinational | cocotb.runner missing, Makefile missing, test discovery failure | ~30 of 57 | `combinational_0005`-`0009`, `0010`-`0015`, `0017`-`0050` |
| fifo | Makefile missing | ~5 of 54 | `fifo_0000`-`0004` |
| fsm | Makefile missing, VPI root handle not found | ~5 of 84 | `fsm_0000`-`0003`, `fsm_0046` |
| axi | Undefined macro references | ~2 of 12 | `axi_0003`, `axi_0006` |

These infrastructure errors represent transient environment issues, not reusable design knowledge. They inflate the skill count and reduce the signal-to-noise ratio for actual design bugs.

### 4c. Severe Category Imbalance

| Category | Skills | % of Total |
|----------|--------|-----------|
| fsm | 84 | 40.6% |
| combinational | 57 | 27.5% |
| fifo | 54 | 26.1% |
| axi | 12 | 5.8% |
| timing | 0 | 0% |

`fsm` has 84 skills (7x the average of non-zero categories), while `timing` has 0 — despite timing being a critical concern in the V2 pipeline. The imbalance means:
- FSM designs see the most competition among skills but get the most aggressive limiting (fix_agent.py line 86 caps to 1 hit).
- Timing-related designs get zero help from memory despite being the hardest V2 problems.

### 4d. No Quality Scoring or Feedback

Once a skill is stored, there is no mechanism to:
- Rate it as helpful or unhelpful
- Track whether the LLM actually used it
- Downgrade or remove skills that were retrieved but did not help
- Correlate skills with fix success/failure

A skill that always returns irrelevant results has the same standing as a skill that consistently provides the exact fix.

### 4e. Skill Patterns Are LLM-Generated, Not Structured

The `pattern` field comes from `error_analysis.get("CAUSE", "unknown pattern")` (fix_agent.py line 132), which is the output of `log_analysis_agent`'s LLM call. This means:
- Two runs of the same bug produce different pattern text (LLM nondeterminism).
- Patterns contain prose descriptions rather than structured data (e.g., error codes, signal names).
- The retrieval's keyword matching (trace2skill.py line 92) is fighting against LLM-generated variability.

---

## 5. Architectural Weaknesses

### 5a. File-Based Storage Is Fragile

Skills are stored as plain JSON files in `skills/`. This has multiple failure modes:
- File could be deleted or corrupted by disk errors.
- A malformed `store_skill()` call writing garbage JSON (e.g., if the file is empty or truncated) corrupts the entire category.
- No validation on load — `_load()` (trace2skill.py lines 20-23) has no try/except. An empty or corrupted file causes a hard crash.

### 5b. No Concurrent Write Safety

`_save()` (trace2skill.py lines 26-29) opens the file with `"w"` mode — any concurrent write from a second pipeline instance would:
- Read stale state (read-write race)
- Overwrite another instance's changes (last-writer-wins)
- Cause partial writes if the process is killed mid-write

There is no file locking, atomic write, or transaction mechanism.

### 5c. Single-Process Assumption

The entire architecture assumes one pipeline runs at a time. There is:
- No sharding of skill storage across processes.
- No replication for fault tolerance.
- No read replicas for parallel retrieval.
- No write queue for concurrent store operations.

### 5d. No Backup or Restore Mechanism

Skills are ephemeral to the filesystem:
- No export function to save skills to a portable format.
- No import function to reload skills from a backup.
- No versioning — skills are overwritten in-place.
- If the `skills/` directory is lost, all accumulated memory is gone permanently.

### 5e. Error Type Enum Is Too Coarse

The 6-category error taxonomy (`SYNTAX, WIDTH, LOGIC, TIMING, COVERAGE, UNKNOWN`) defined in log_analysis_agent.py lines 15-22 is too coarse for meaningful retrieval. The error type filter (trace2skill.py line 90) requires exact match, which means:
- A `SYNTAX` fix for a missing `endmodule` keyword is invisible to a `LOGIC` query, even if a similar structural issue might apply.
- `UNKNOWN` is a catch-all that groups fundamentally different errors into one bucket, making retrieval within that category nearly useless.

---

## Summary Table

| # | Weakness | Severity | Source File(s) | Key Lines |
|---|----------|----------|----------------|-----------|
| 1a | Unconditional storage (failed fixes pollute) | **Critical** | fix_agent.py | 126-135 |
| 1b | No eviction policy | High | trace2skill.py | 32-70 (entire function) |
| 1c | Duplicate patterns across categories | High | All skill JSONs | Verified in 5 files |
| 1d | All success_count=1 (dedup never fires) | **Critical** | trace2skill.py, all skills | 49-53 |
| 1e | No cross-category dedup | Medium | trace2skill.py | 44-54 |
| 1f | Missing/unused fields (no timestamp) | Medium | trace2skill.py | 58-66 |
| 2a | Single-category lookup | **Critical** | log_analysis_agent.py | 87-91 |
| 2b | Heuristic category guessing | High | log_analysis_agent.py | 106-117 |
| 2c | Primitive keyword matching | High | trace2skill.py | 92 |
| 2d | No semantic similarity | High | trace2skill.py | 92-93 |
| 2e | Error type filter too strict | Medium | trace2skill.py | 90-91 |
| 2f | Hardcoded limit of 3 results | Medium | trace2skill.py | 97 |
| 2g | FSM further limited to 1 hit | Medium | fix_agent.py | 85-86 |
| 3a | Only 2 of 10 agents consume it | High | Various | All agent files |
| 3b | Prompt hints undermine usefulness | High | fix_agent.py | 38 (in prompt) |
| 3c | State not cleared between iterations | Medium | pipeline.py, orchestrator.py | No reset logic |
| 3d | No pipeline-level logging/instrumentation | High | pipeline.py | Throughout |
| 3e | get_stats() prints but no action | Low | main.py | 96-101 |
| 4a | 207 skills, 0 reinforced | **Critical** | All skill JSONs | All entries |
| 4b | ~50% are infrastructure errors | High | All skill JSONs | Verified in data |
| 4c | Category imbalance (fsm=84, timing=0) | Medium | All skill JSONs | Counts |
| 4d | No quality scoring | High | trace2skill.py, fix_agent.py | No feedback path |
| 4e | Skill patterns are LLM-generated | Medium | fix_agent.py | 132 |
| 5a | File-based storage is fragile | High | trace2skill.py | 20-29 |
| 5b | No concurrent write safety | Medium | trace2skill.py | 26-29 |
| 5c | Single-process assumption | Low | trace2skill.py | Architecture |
| 5d | No backup/restore | Medium | — | No export/import exists |
| 5e | Error type enum too coarse | Medium | log_analysis_agent.py, trace2skill.py | 15-22, 90 |
