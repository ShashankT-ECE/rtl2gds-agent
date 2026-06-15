# Trace2Skill Memory System -- Architecture Document

**Project:** AI-Driven Agentic Framework for RTL-to-GDS
**Owner:** Shashank Tumuluri, CBIT Hyderabad ECE
**File:** `v1_core/utils/trace2skill.py`
**Version:** 1.0 (JSON schema version key)

---

## 1. Overview

Trace2Skill is a persistent, file-based memory system for the RTL-to-GDS agentic framework. It stores successful error-fix pairs as structured JSON "skills" so that the agent pipeline can recall and reuse known solutions across runs. There is no ML, no vector database, and no training -- the system is pure structured JSON with keyword-based retrieval.

Source: `v1_core/utils/trace2skill.py`, lines 1-9 (module docstring).

---

## 2. Storage Format

### 2.1 JSON Schema

Each skill category is stored in a separate JSON file at:

```
PROJECT_ROOT/skills/<category>.json
```

Where `PROJECT_ROOT` is resolved as three directories up from `v1_core/utils/trace2skill.py`:
```python
SKILLS_DIR = Path(__file__).parent.parent.parent / "skills"
```
(Source: `trace2skill.py`, line 15.)

### 2.2 Top-Level Structure

Every JSON file has exactly two keys:

| Key | Type | Description |
|-----|------|-------------|
| `version` | string | Schema version identifier. Currently `"1.0"`. |
| `skills` | array | Ordered list of skill objects. |

Example from `skills/combinational.json` (lines 1-3):
```json
{
  "version": "1.0",
  "skills": [
    ...
  ]
}
```

### 2.3 Per-Skill Fields

Each object in the `skills` array has these fields:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | string | Unique identifier within the category | `"combinational_0000"` |
| `category` | string | One of the five valid categories | `"combinational"` |
| `error_type` | string | Error classification (6 types) | `"SYNTAX"` |
| `pattern` | string | Short natural-language description of the error | `"Invalid Python syntax on line 1..."` |
| `fix` | string | Human-readable fix description | `"Correct the syntax error..."` |
| `design_name` | string | Which RTL design produced this skill | `"alu_8bit"` |
| `success_count` | integer | How many times this fix has been reused | `1` |
| `last_seen` | string | Design name from the most recent use | `"alu_8bit"` |

Source: `trace2skill.py`, lines 58-67 (`store_skill` function -- new skill creation).

### 2.4 File Locations

The five live skill files as of this writing:

| File | Content |
|------|---------|
| `skills/combinational.json` | Skills for combinational logic designs (e.g., `alu_8bit`) |
| `skills/fsm.json` | Skills for FSM-related designs (e.g., `uart_tx`, `fsm_traffic_light`) |
| `skills/fifo.json` | Skills for FIFO designs (e.g., `sync_fifo_8x16`) |
| `skills/axi.json` | Skills for bus protocol designs (e.g., `apb_slave`) |
| `skills/timing.json` | Skills for timing-related issues (currently empty: `{"version": "1.0", "skills": []}`) |

---

## 3. Storage Logic

### 3.1 `store_skill()` Function

```python
def store_skill(category: str, error_type: str, pattern: str, fix: str, design_name: str) -> str:
```

Source: `trace2skill.py`, lines 32-70.

**Arguments:**

| Argument | Type | Description |
|----------|------|-------------|
| `category` | str | Must be in `VALID_CATEGORIES` |
| `error_type` | str | One of: SYNTAX, WIDTH, LOGIC, TIMING, COVERAGE, UNKNOWN |
| `pattern` | str | Short description of the error pattern |
| `fix` | str | What was done to fix it |
| `design_name` | str | The RTL design that produced this fix |

**Return value:** The skill ID (string) of the stored/updated skill.

### 3.2 Flow

1. **Category validation** (line 44):
   ```python
   assert category in VALID_CATEGORIES, f"Invalid category: {category}"
   ```
   Raises `AssertionError` if the category is not one of the five valid values.

2. **Load existing bank** (line 46):
   ```python
   bank = _load(category)
   ```
   Calls `_load()` (lines 20-23), which reads the JSON file at `skills/<category>.json`.

3. **Deduplication** (lines 49-54):
   ```python
   for skill in bank["skills"]:
       if skill["pattern"] == pattern and skill["error_type"] == error_type:
           skill["success_count"] += 1
           skill["last_seen"] = design_name
           _save(category, bank)
           return skill["id"]
   ```
   A skill is considered a duplicate if **both** `pattern` and `error_type` match an existing entry. On match:
   - `success_count` is incremented by 1.
   - `last_seen` is updated to the current `design_name`.
   - The bank is saved and the existing `id` is returned.
   - No new entry is created.

4. **New skill creation** (lines 57-67):
   If no duplicate is found, a new skill object is created:
   ```python
   skill_id = f"{category}_{len(bank['skills']):04d}"
   ```
   The ID is zero-padded to 4 digits (e.g., `combinational_0004`, `fifo_0012`). This means IDs are positional -- if skills are ever deleted, the index resets based on array length.

   The new skill is appended to `bank["skills"]` with `success_count` initialized to 1 and `last_seen` set to the current `design_name`.

5. **Persist** (line 69):
   ```python
   _save(category, bank)
   ```
   Calls `_save()` (lines 26-29), which writes the JSON file with `indent=2` formatting.

### 3.3 Deduplication Semantics

Deduplication is **exact-match only** on the `pattern` string. Two skills are considered the same if:
```
skill["pattern"] == pattern AND skill["error_type"] == error_type
```
- Case sensitivity: `pattern` comparison is case-sensitive (no `.lower()` normalization).
- Partial matches do not trigger deduplication.
- Different categories are stored in separate files, so "fifo" and "combinational" skills with the same pattern and error_type coexist without collision.

---

## 4. Retrieval Logic

### 4.1 `retrieve_skills()` Function

```python
def retrieve_skills(category: str, error_type: str, keywords: list) -> list:
```

Source: `trace2skill.py`, lines 73-97.

**Arguments:**

| Argument | Type | Description |
|----------|------|-------------|
| `category` | str | Restricts search to one category file |
| `error_type` | str | Must match exactly (`skill["error_type"] == error_type`) |
| `keywords` | list | List of strings used for substring matching against `pattern` |

**Return value:** A list of up to 3 skill dicts, sorted by relevance score descending. Empty list if no matches.

### 4.2 Flow

1. **Load bank** (line 86):
   ```python
   bank = _load(category)
   ```
   Reads all skills from `skills/<category>.json`.

2. **Error type filter** (lines 89-91):
   ```python
   for skill in bank["skills"]:
       if skill["error_type"] != error_type:
           continue
   ```
   Any skill whose `error_type` does not match is **discarded immediately** with no score. This is an exact string match.

3. **Keyword scoring** (line 92):
   ```python
   score = sum(1 for kw in keywords if kw.lower() in skill["pattern"].lower())
   ```
   - Each keyword contributes 1 point if it appears as a **substring** of the pattern (case-insensitive).
   - Multiple occurrences of the same keyword do not stack -- it is a binary per-keyword check.
   - There is no TF-IDF, no word-boundary awareness, and no stop-word removal.

4. **Weighted score** (line 94):
   ```python
   matches.append((score + skill["success_count"], skill))
   ```
   The final score is the keyword-match count **plus** the skill's `success_count`. More frequently reused skills rank higher, all else equal.

5. **Sort and limit** (lines 96-97):
   ```python
   matches.sort(key=lambda x: x[0], reverse=True)
   return [s for _, s in matches[:3]]
   ```
   - Sorted descending by the combined score.
   - **Top 3** results returned. If fewer than 3 match, all matches are returned.
   - If zero match, an empty list is returned.

### 4.3 Retrieval Example

Given:
- `keywords = ["syntax", "line 1", "testbench"]`
- A skill with `pattern = "Invalid Python syntax on line 1 of the testbench file."` and `success_count = 1`

Scoring:
- "syntax" in pattern.lower()? Yes (+1)
- "line 1" in pattern.lower()? Yes (+1)
- "testbench" in pattern.lower()? Yes (+1)
- Raw score = 3, final score = 3 + 1 (success_count) = 4

---

## 5. Category System

### 5.1 Valid Categories

```python
VALID_CATEGORIES = ["combinational", "fsm", "fifo", "axi", "timing"]
```

Source: `trace2skill.py`, line 17.

### 5.2 Category Guessing

The function `_guess_category()` maps a design name to a skill category:

```python
def _guess_category(design_name: str) -> str:
    name = design_name.lower()
    if "fifo" in name:
        return "fifo"
    if "fsm" in name or "uart" in name or "spi" in name:
        return "fsm"
    if "axi" in name or "apb" in name:
        return "axi"
    if "timing" in name:
        return "timing"
    return "combinational"
```

Source: `log_analysis_agent.py`, lines 106-117.

**Mapping table:**

| Design name contains | Category | Example design names |
|---------------------|----------|---------------------|
| `fifo` | fifo | `sync_fifo_8x16`, `async_fifo` |
| `fsm`, `uart`, `spi` | fsm | `fsm_traffic_light`, `uart_tx`, `spi_master` |
| `axi`, `apb` | axi | `axi_wrapper`, `apb_slave` |
| `timing` | timing | `timing_controller` |
| (none of the above) | combinational | `alu_8bit`, `mux_4to1` |

**Important note:** The checks are ordered and short-circuit. A design named `fifo_uart` would match "fifo" first and be categorized as "fifo", not "fsm". A design named `timing_axi` would match "axi" before "timing".

### 5.3 File-Per-Category Storage

Each category corresponds to exactly one file:
```
skills/combinational.json
skills/fsm.json
skills/fifo.json
skills/axi.json
skills/timing.json
```

This means:
- Retrieval is scoped: the Fix Agent only looks at skills from the same category as the current design.
- Category migration: if a design name changes, its skills are not automatically migrated -- they stay in the old category file.

---

## 6. Integration with Agents

### 6.1 PipelineState Definition

The shared LangGraph state includes a `trace2skill_hits` field:

```python
class PipelineState(TypedDict):
    ...
    trace2skill_hits: list       # skills retrieved from memory for this error
    ...
```

Source: `orchestrator.py`, line 30.

Initialized to an empty list in `get_initial_state()`:

```python
return PipelineState(
    ...
    trace2skill_hits=[],
    ...
)
```

Source: `orchestrator.py`, line 65.

### 6.2 Log Analysis Agent

The Log Analysis Agent is the **writer** of `trace2skill_hits` -- it retrieves skills and stores them in the pipeline state.

**Location:** `v1_core/agents/log_analysis_agent.py`

**Flow (lines 85-102):**

1. After parsing the LLM's classification response, the agent extracts `error_type` and `keywords` from the response.
2. It guesses the category from the design name: `category = _guess_category(state["design_name"])`
3. It calls `retrieve_skills()`:
   ```python
   hits = retrieve_skills(
       category=category,
       error_type=error_type,
       keywords=keywords
   )
   ```
4. The retrieved hits are written back to state:
   ```python
   return {
       **state,
       "trace2skill_hits": hits,
       ...
   }
   ```
5. If the design name is `uart_tx` with a `SYNTAX` error and keywords `["Makefile", "missing", "build"]`, the agent searches `skills/fsm.json` (because "uart" maps to "fsm") for skills with `error_type == "SYNTAX"` whose pattern contains those keywords.

**Imports (line 10):**
```python
from v1_core.utils.trace2skill import retrieve_skills
```

### 6.3 Fix Agent

The Fix Agent is both the **reader** of `trace2skill_hits` (for prompt construction) and the **writer** to persistent storage (via `store_skill()`).

**Location:** `v1_core/agents/fix_agent.py`

**Flow:**

1. **Read hits from state** (line 74):
   ```python
   hits = state["trace2skill_hits"]
   ```

2. **Guess category** (lines 77-78):
   ```python
   from v1_core.agents.log_analysis_agent import _guess_category
   category = _guess_category(state["design_name"])
   ```

3. **Format known fixes for prompt** (lines 84-93): (See Section 7 below.)

4. **Construct FIX_PROMPT** (lines 105-117) with the formatted `known_fixes` injected.

5. **Call LLM** (lines 119-123) and extract the fixed RTL.

6. **Store the fix** (lines 129-135):
   ```python
   store_skill(
       category=category,
       error_type=error_type,
       pattern=error_analysis.get("CAUSE", "unknown pattern"),
       fix=error_analysis.get("FIX_SUGGESTION", ""),
       design_name=state["design_name"]
   )
   ```
   - `pattern` is the `CAUSE` field from the error analysis.
   - `fix` is the `FIX_SUGGESTION` field from the error analysis.
   - **Note:** The category is recomputed by calling `_guess_category()` again, rather than being passed from the Log Analysis Agent. Both agents should agree on the category because they use the same function on the same `design_name`.

**Imports (lines 12-13):**
```python
from v1_core.utils.trace2skill import store_skill
```

### 6.4 Orchestrator

The Orchestrator defines the shared state type and initialization function. It has no direct interaction with Trace2Skill beyond defining the state field.

Source: `v1_core/agents/orchestrator.py`

### 6.5 main.py

At the end of every pipeline run, `main.py` calls `get_stats()` to print a per-category skill count:

```python
from v1_core.utils.trace2skill import get_stats

stats = get_stats()
for category, count in stats.items():
    logger.info(f"  {category}: {count} skills stored")
```

Source: `main.py`, lines 14, 97-100.

The `get_stats()` function (trace2skill.py lines 100-106) iterates all categories and returns a dict:
```python
def get_stats() -> dict:
    stats = {}
    for cat in VALID_CATEGORIES:
        bank = _load(cat)
        stats[cat] = len(bank["skills"])
    return stats
```

---

## 7. Prompt Injection

### 7.1 FIX_PROMPT Template

The FIX_PROMPT is defined in `fix_agent.py`, lines 18-60. The critical section for Trace2Skill is lines 38-39:

```
The following are HINTS from memory -- use them only if they directly match this exact error. Do NOT apply them blindly:
{known_fixes}
```

The full context of the instruction block makes clear that:
- Hits are presented as hints, not mandatory changes.
- The LLM is instructed not to apply them blindly.
- The hint is positioned between the error analysis and the RTL code in the prompt.

### 7.2 Known Fixes Formatting

In `fix_agent.py`, lines 87-89:

```python
known_fixes_text = "\n".join([
    f"- Pattern: {h['pattern']} | Fix: {h['fix']}"
    for h in hits
])
```

Each hit becomes one line in the format:
```
- Pattern: <pattern field> | Fix: <fix field>
```

Example output:
```
- Pattern: The Makefile path is missing or the build directory was not generated before invoking make. | Fix: Ensure the build directory and Makefile are generated by running the appropriate setup or configuration step before invoking make.
```

### 7.3 FSM Hit Limiting

In `fix_agent.py`, lines 84-86:

```python
if hits:
    if category == "fsm":
        hits = hits[:1]
```

For FSM designs, only **1 hit** is injected into the prompt, regardless of how many were retrieved. This is a pragmatic guard against overfitting: FSM errors tend to be highly state-dependent, and multiple hints risk confusing the LLM into applying an irrelevant fix.

### 7.4 Fallback

When no hits are available (line 93):
```python
known_fixes_text = "None available"
```

The prompt then reads:
```
The following are HINTS from memory -- use them only if they directly match this exact error. Do NOT apply them blindly:
None available
```

---

## 8. State Lifecycle of `trace2skill_hits`

### 8.1 Timeline

```
Pipeline Start
    |
    | trace2skill_hits = [] (initialized by get_initial_state)
    v
spec_parser_agent       -- trace2skill_hits untouched (empty)
    |
    v
verification_planner    -- trace2skill_hits untouched (empty)
    |
    v
rtl_gen_agent           -- trace2skill_hits untouched (empty)
    |
    v
testbench_agent         -- trace2skill_hits untouched (empty)
    |
    v
simulation_agent        -- trace2skill_hits untouched (empty)
    |
    | (if simulation fails)
    v
log_analysis_agent      -- SETS trace2skill_hits = retrieve_skills(...)
    |
    v
fix_agent               -- READS trace2skill_hits for prompt
                        -- CALLS store_skill() after every successful fix
    |
    v
testbench_agent         -- trace2skill_hits UNCHANGED (still contains previous hits)
    |
    v
simulation_agent        -- trace2skill_hits UNCHANGED
    |
    | (if fails again)
    v
log_analysis_agent      -- OVERWRITES trace2skill_hits with fresh retrieval
    |
    v
fix_agent               -- reads the new hits
                        -- stores the fix again (dedup increments count)
```

### 8.2 Key Observations

1. **Initial state** is an empty list (`orchestrator.py`, line 65).
2. **Set only by** `log_analysis_agent`, which overwrites the field with fresh retrieval results on every invocation (`log_analysis_agent.py`, line 101).
3. **Read only by** `fix_agent` (`fix_agent.py`, line 74), which uses it for prompt construction.
4. **Not cleared** between fix iterations. However, since `log_analysis_agent` runs before `fix_agent` in every fix loop iteration, the hits are refreshed each cycle. Stale hits are only possible if `log_analysis_agent` is skipped -- which it never is in the current pipeline.
5. **No other agent** reads or modifies `trace2skill_hits`. It is purely a communication channel between Log Analysis and Fix agents.

---

## 9. File Summary

| File | Role |
|------|------|
| `v1_core/utils/trace2skill.py` | Core implementation: `store_skill()`, `retrieve_skills()`, `get_stats()`, `_load()`, `_save()` |
| `v1_core/agents/log_analysis_agent.py` | Retrieves skills via `_guess_category()` + `retrieve_skills()`, writes to state |
| `v1_core/agents/fix_agent.py` | Reads hits from state, injects into FIX_PROMPT, calls `store_skill()` after fix |
| `v1_core/agents/orchestrator.py` | Defines `trace2skill_hits` in `PipelineState`, initializes to `[]` |
| `v1_core/pipeline.py` | Wires agents in LangGraph; no direct Trace2Skill involvement |
| `v2_verification/pipeline.py` | V2 pipeline; reuses V1 agents including Trace2Skill, no additional integration |
| `main.py` | Calls `get_stats()` after each pipeline run to log skill counts |
| `skills/*.json` | Persistent storage (5 files, one per category) |

---

## 10. Limitations and Design Notes

1. **No deletion or pruning.** Skills accumulate indefinitely. There is no mechanism to remove low-quality or obsolete skills.

2. **Pattern-based dedup is exact and case-sensitive.** The same semantic error phrased slightly differently creates a separate skill entry.

3. **Keyword retrieval is substring-based, not semantic.** A keyword "synt" matches "syntax" but not "parse error" -- there is no synonym expansion or embedding.

4. **Category is derived from design name only.** A design whose name does not contain any category keyword always falls back to "combinational", which may be incorrect.

5. **No cross-category retrieval.** The Fix Agent only searches one category file. If the best fix for an FSM design happens to be stored under "combinational", it will not be found.

6. **`version` key is present but unused.** The JSON schema declares `"version": "1.0"`, but no code reads or validates this field. It is purely documentary.

7. **FSM hit limit is a heuristic.** The `hits[:1]` truncation for FSM designs (fix_agent.py line 86) has no formal justification in the code -- it is an empirical guard against overfitting.

8. **Store is called unconditionally.** The Fix Agent calls `store_skill()` after every invocation (fix_agent.py line 129), even if the fix was wrong or the subsequent simulation still fails. The success_count is incremented on subsequent dedup matches regardless of whether the fix was actually successful.
