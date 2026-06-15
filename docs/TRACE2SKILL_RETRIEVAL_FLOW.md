# Trace2Skill Retrieval Flow

**Project:** AI-Driven Agentic Framework for RTL-to-GDS  
**File:** `v1_core/utils/trace2skill.py`  
**Last Updated:** 2026-06-15

---

## 1. Complete Retrieval Flow (Step by Step)

### Step 1: Simulation Fails
When simulation produces a log with errors (not `sim_passed`), the pipeline's router function `should_fix_or_end()` in `pipeline.py` (line 19) detects the failure. It checks convergence detection and iteration limits, then returns `"fix"` which routes execution to the **Log Analysis Agent** node.

Relevant code: `pipeline.py`, lines 19-64, specifically:
```python
graph.add_conditional_edges(
    "simulation",
    should_fix_or_end,
    {"fix": "log_analysis", "end": END}
)
```

### Step 2: Log Analysis Calls `call_llm()` with LOG_ANALYSIS_PROMPT
The `log_analysis_agent()` function (line 45 in `log_analysis_agent.py`) builds a structured prompt from `LOG_ANALYSIS_PROMPT` (line 25). The prompt includes:
- The simulation log (`state["sim_log"]`)
- The RTL code (`state["rtl_code"]`)
- An optional verification plan section

The prompt is formatted at **line 70**:
```python
prompt = LOG_ANALYSIS_PROMPT.format(
    sim_log=state["sim_log"],
    rtl_code=state.get("rtl_code", ""),
    verification_plan_section=verification_plan_section
)
```

The LLM call happens at **line 71**:
```python
response = call_llm(prompt=prompt, task="log_analysis")
```

The model used is `deepseek-v4-flash` (configured in `v1_core/utils/model_router.py`).

### Step 3: LLM Responds with Structured Fields
The LLM is instructed to respond in this exact format (from `LOG_ANALYSIS_PROMPT`, line 29-36):
```
ERROR_TYPE: <one of SYNTAX, WIDTH, LOGIC, TIMING, COVERAGE, UNKNOWN>
LOCATION: <file and line number if visible, else UNKNOWN>
CAUSE: <one sentence explaining the root cause>
EXACT_FIX: <the single exact change needed>
FIX_SUGGESTION: <one sentence describing how to fix it>
KEYWORDS: <3 to 5 comma separated keywords from the error>
```

### Step 4: Log Analysis Extracts `error_type` and `keywords` from Response
The response is parsed line-by-line at **lines 75-78**:
```python
error_analysis = {}
for line in response.strip().splitlines():
    if ":" in line:
        key, _, value = line.partition(":")
        error_analysis[key.strip()] = value.strip()
```

Then at **lines 80-81**:
```python
error_type = error_analysis.get("ERROR_TYPE", "UNKNOWN")
keywords = [k.strip() for k in error_analysis.get("KEYWORDS", "").split(",")]
```

The `KEYWORDS` field is split on commas, yielding a list of 3-5 keyword strings.

### Step 5: Log Analysis Calls `_guess_category(design_name)`
At **line 86**:
```python
category = _guess_category(state["design_name"])
```

The `_guess_category()` function (lines 106-117) maps design name to skill category:
```python
def _guess_category(design_name: str) -> str:
    name = design_name.lower()
    if "fifo" in name:          return "fifo"
    if "fsm" in name or "uart" in name or "spi" in name: return "fsm"
    if "axi" in name or "apb" in name: return "axi"
    if "timing" in name:        return "timing"
    return "combinational"
```

### Step 6: Log Analysis Calls `retrieve_skills(category, error_type, keywords)`
At **lines 87-91**:
```python
hits = retrieve_skills(
    category=category,
    error_type=error_type,
    keywords=keywords
)
```

### Step 7: `retrieve_skills` Loads the Correct Category JSON
Inside `retrieve_skills()` (trace2skill.py, line 73), the first action at **line 86** is:
```python
bank = _load(category)
```

Which internally does (line 20-23):
```python
def _load(category: str) -> dict:
    path = SKILLS_DIR / f"{category}.json"
    with open(path) as f:
        return json.load(f)
```

`SKILLS_DIR` is defined at **line 15** as `Path(__file__).parent.parent.parent / "skills"`, resolving to `<project_root>/skills/`.

### Step 8: `retrieve_skills` Filters by `error_type` (Exact Match)
At **lines 89-91**:
```python
for skill in bank["skills"]:
    if skill["error_type"] != error_type:
        continue
```

This is a hard filter -- only skills whose `error_type` field exactly matches the current error are considered.

### Step 9: Score Each Match by Keyword Overlap + `success_count`
At **line 92**:
```python
score = sum(1 for kw in keywords if kw.lower() in skill["pattern"].lower())
```

Each keyword that appears as a case-insensitive substring within the skill's `pattern` field contributes 1 point to the keyword match score.

Then at **line 93-94**:
```python
if score > 0:
    matches.append((score + skill["success_count"], skill))
```

The final score is **keyword_matches + success_count**. Only skills with at least 1 keyword match are included.

### Step 10: Sort Descending, Return Top 3
At **lines 96-97**:
```python
matches.sort(key=lambda x: x[0], reverse=True)
return [s for _, s in matches[:3]]
```

Skills are sorted by total score descending. The top 3 (or fewer if fewer matches exist) are returned.

### Step 11: Hits Stored in `state["trace2skill_hits"]`
Back in `log_analysis_agent.py`, line 98-103:
```python
return {
    **state,
    "error_analysis": error_analysis,
    "trace2skill_hits": hits,
    "stage": "log_analysis_done"
}
```

The `trace2skill_hits` field is declared in `PipelineState` (orchestrator.py, line 30):
```python
trace2skill_hits: list       # skills retrieved from memory for this error
```

It is initialized as an empty list in `get_initial_state()` (orchestrator.py, line 65).

### Step 12: Fix Agent Reads `trace2skill_hits` from State
In `fix_agent.py`, at **line 74**:
```python
hits = state["trace2skill_hits"]
```

### Step 13: Fix Agent Formats Hits as `"- Pattern: ... | Fix: ..."` Lines
At **lines 84-93**:
```python
if hits:
    if category == "fsm":
        hits = hits[:1]
    known_fixes_text = "\n".join([
        f"- Pattern: {h['pattern']} | Fix: {h['fix']}"
        for h in hits
    ])
    logger.info(f"Using {len(hits)} Trace2Skill hint(s) in prompt")
else:
    known_fixes_text = "None available"
```

### Step 14: FSM Category Truncates to 1 Hit
At **line 85-86**:
```python
if category == "fsm":
    hits = hits[:1]
```

FSM errors are known to be highly repetitive (many off-by-one counter variants), so only the single highest-scoring hint is passed to reduce noise. All other categories pass up to 3 hits.

### Step 15: Formatted Text Injected into `FIX_PROMPT` as `{known_fixes}`
At **lines 105-117**:
```python
prompt = FIX_PROMPT.format(
    exact_fix=exact_fix,
    error_type=error_type,
    ...
    known_fixes=known_fixes_text,
    ...
    rtl_code=state["rtl_code"]
)
```

The `FIX_PROMPT` template (fix_agent.py, line 18-60) instructs the LLM:
```
The following are HINTS from memory — use them only if they directly match this exact error. Do NOT apply them blindly:
{known_fixes}
```

### Step 16: LLM Reads the Hints
The LLM is told these are optional hints ("HINTS from memory -- use them only if they directly match this exact error. Do NOT apply them blindly"). The LLM must decide whether each hint matches the current error before applying it.

### Step 17: After Generating Fix, Fix Agent Calls `store_skill()`
At **lines 129-135**:
```python
store_skill(
    category=category,
    error_type=error_type,
    pattern=error_analysis.get("CAUSE", "unknown pattern"),
    fix=error_analysis.get("FIX_SUGGESTION", ""),
    design_name=state["design_name"]
)
```

This is called **unconditionally** -- even if the fix does not pass subsequent simulation. The rationale is that even unsuccessful attempts may contain useful pattern information.

---

## 2. Data Flow Diagram (ASCII)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        LANGGRAPH PIPELINE                            │
│  (pipeline.py)                                                       │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    Simulation fails │ should_fix_or_end() → "fix"
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      LOG ANALYSIS AGENT                              │
│  (log_analysis_agent.py)                                             │
│                                                                      │
│  state["sim_log"] + state["rtl_code"]                                │
│         │                                                            │
│         ▼                                                            │
│  call_llm(LOG_ANALYSIS_PROMPT)                     ← line 71        │
│         │                                                            │
│         ▼                                                            │
│  Parse response → ERROR_TYPE, KEYWORDS, CAUSE, etc. ← lines 75-81  │
│         │                                                            │
│         ├─→ _guess_category(design_name)           ← line 86        │
│         │      │                                                     │
│         │      ▼                                                     │
│         │   "fifo" | "fsm" | "axi" | "timing" | "combinational"     │
│         │                                                           │
│         └─→ retrieve_skills(category, error_type, keywords) ← line 87│
│                  │                                                   │
│                  ▼                                                   │
│            load skills/CATEGORY.json               ← trace2skill.py │
│                  │                                   line 86         │
│                  ▼                                                   │
│            filter by error_type (exact match)       ← line 90-91    │
│                  │                                                   │
│                  ▼                                                   │
│            score = keyword_matches + success_count  ← line 92-94    │
│                  │                                                   │
│                  ▼                                                   │
│            sort descending, return top 3            ← line 96-97    │
│                  │                                                   │
│                  ▼                                                   │
│         state["trace2skill_hits"] = hits           ← log_analysis   │
│                                                       line 101      │
│         state["stage"] = "log_analysis_done"                        │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ state passed to next node
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        FIX AGENT                                     │
│  (fix_agent.py)                                                      │
│                                                                      │
│  hits = state["trace2skill_hits"]                  ← line 74        │
│         │                                                            │
│         ▼                                                            │
│  if category == "fsm": hits = hits[:1]             ← line 85-86     │
│         │                                                            │
│         ▼                                                            │
│  known_fixes_text =                                              │
│    "- Pattern: ... | Fix: ...\n"                    ← line 87-90    │
│         │                                                            │
│         ▼                                                            │
│  FIX_PROMPT.format(known_fixes=known_fixes_text)   ← line 105      │
│         │                                                            │
│         ▼                                                            │
│  call_llm(FIX_PROMPT, task="rtl_fix")              ← line 119      │
│         │                                                            │
│         ▼                                                            │
│  store_skill(category, error_type, pattern, fix,   ← line 129-135  │
│              design_name)                                            │
│         │                                                            │
│         ▼                                                            │
│  state["rtl_code"] = fixed_rtl                    ← line 138       │
│  state["iteration"] += 1                          ← line 141       │
│  state["stage"] = "fix_applied"                   ← line 142       │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                     Testbench → Simulation (loop)
```

---

## 3. Keyword Extraction and Matching

### Extraction

In `log_analysis_agent.py`, lines 74-81:

1. The LLM's text response is split into lines.
2. Each line is split on the first `:` to extract key-value pairs.
3. The value after `KEYWORDS:` is captured as a raw string.
4. This string is split on commas, and each token is stripped of whitespace.

```python
# Line 75-78: Parse all fields from LLM response
for line in response.strip().splitlines():
    if ":" in line:
        key, _, value = line.partition(":")
        error_analysis[key.strip()] = value.strip()

# Line 81: Extract keywords list
keywords = [k.strip() for k in error_analysis.get("KEYWORDS", "").split(",")]
```

**Example:** If the LLM returns:
```
KEYWORDS: full, count, threshold
```

Then `keywords` becomes `["full", "count", "threshold"]`.

### Comparison Against Skill Pattern (trace2skill.py, line 92)

```python
score = sum(1 for kw in keywords if kw.lower() in skill["pattern"].lower())
```

Rules:
- **Case-insensitive:** Both the keyword and the pattern are lowered before comparison.
- **Substring match:** The keyword need only be a substring of the pattern, not a whole-word match.
- **No stemming or fuzzy matching:** The match is a simple Python `in` operator.
- **Each matching keyword contributes exactly 1** to the keyword portion of the score.

### Scoring Formula

```
total_score = keyword_matches + success_count
```

Where:
- `keyword_matches` = number of keywords that appear as substrings in `skill["pattern"]` (integer, 1 to 5 typically)
- `success_count` = the skill's stored `success_count` field (integer, starts at 1)

**Only skills with `keyword_matches > 0`** are included in the results (line 93: `if score > 0`).

### Example

If `keywords = ["full", "count", "threshold"]` and a skill has:
- `pattern = "The full flag asserts when count equals 16"`
- `success_count = 3`

Then:
- `"full"` in pattern → yes (1)
- `"count"` in pattern → yes (1)
- `"threshold"` in pattern → no (0)
- `keyword_matches = 2`
- `total_score = 2 + 3 = 5`

---

## 4. Ranking Logic

### Primary Sort: Score Descending

In `trace2skill.py`, line 96:
```python
matches.sort(key=lambda x: x[0], reverse=True)
```

The list `matches` contains `(total_score, skill_dict)` tuples. Sorting by `x[0]` descending puts the highest-scored skill first.

### Tiebreaker: Insertion Order (Stable Sort)

Python's `sorted()` and `list.sort()` use a **stable sort** algorithm. When two skills have identical scores, their relative order in the input list is preserved. Since skills are loaded sequentially from the JSON file in their array order, earlier-defined skills win tiebreaks against later-defined ones.

### Limit: Top 3

```python
return [s for _, s in matches[:3]]
```

The top 3 skills (or fewer if `len(matches) < 3`) are returned to the caller.

### FSM Special Case: Limit to 1

In `fix_agent.py`, lines 85-86:
```python
if category == "fsm":
    hits = hits[:1]
```

This truncation happens **after** retrieval, **before** formatting into the prompt. The rationale is that FSM errors tend to involve highly repetitive off-by-one counter patterns, and multiple similar hints can confuse the LLM.

---

## 5. Storage Flow

### Function: `store_skill()`

Located in `trace2skill.py`, lines 32-70.

### Should-Check (line 49-54)

```python
for skill in bank["skills"]:
    if skill["pattern"] == pattern and skill["error_type"] == error_type:
        skill["success_count"] += 1
        skill["last_seen"] = design_name
        _save(category, bank)
        return skill["id"]
```

**Exact match** on **both** `pattern` (the CAUSE string from error analysis) **and** `error_type`. If a pair with identical pattern and error_type exists:
- `success_count` is incremented by 1
- `last_seen` is updated to the current design name
- The file is saved
- The existing skill's ID is returned

### New Entry (line 56-69)

```python
skill_id = f"{category}_{len(bank['skills']):04d}"
bank["skills"].append({
    "id": skill_id,
    "category": category,
    "error_type": error_type,
    "pattern": pattern,
    "fix": fix,
    "design_name": design_name,
    "success_count": 1,
    "last_seen": design_name
})
_save(category, bank)
return skill_id
```

- ID format: `{category}_{zero-padded-4-digit-index}`
- `success_count` always starts at 1
- `last_seen` set to the current design name
- The file is saved immediately

### Called Unconditionally

In `fix_agent.py`, line 126:
```python
logger.success("Fix generated — storing in Trace2Skill")
```

The `store_skill()` call at lines 129-135 runs **before** the fix is verified by re-simulation. This is by design -- even failed fix attempts document patterns that may help in future iterations. There is no check on whether the fix actually passes simulation before storing.

### Arguments Passed (fix_agent.py, lines 129-135)

| Parameter     | Source                                          |
|---------------|-------------------------------------------------|
| `category`    | `_guess_category(state["design_name"])`         |
| `error_type`  | `error_analysis.get("ERROR_TYPE", "UNKNOWN")`   |
| `pattern`     | `error_analysis.get("CAUSE", "unknown pattern")`|
| `fix`         | `error_analysis.get("FIX_SUGGESTION", "")`      |
| `design_name` | `state["design_name"]`                          |

---

## 6. Visual Trace: Concrete Example

### Scenario

| Field       | Value                |
|-------------|----------------------|
| Design      | `sync_fifo_8x16`     |
| Error       | LOGIC                |
| Keywords    | `["full", "count", "threshold"]` |
| Category    | `fifo` (guessed from design name containing "fifo") |

### Step-by-Step Trace

#### Step A: `_guess_category("sync_fifo_8x16")` → `"fifo"`
File: `log_analysis_agent.py`, line 86. The design name contains "fifo", so the function at lines 109-110 returns `"fifo"`.

#### Step B: `retrieve_skills("fifo", "LOGIC", ["full", "count", "threshold"])`
File: `trace2skill.py`, line 73.

#### Step C: Load `skills/fifo.json`
File: `trace2skill.py`, line 86. The JSON file has 54 entries (fifo_0000 to fifo_0053).

#### Step D: Filter by `error_type == "LOGIC"`
File: `trace2skill.py`, lines 89-91.

Skills **retained** (error_type="LOGIC"): fifo_0005 through fifo_0053 (excluding fifo_0012, fifo_0026 which are "WIDTH", and fifo_0000/fifo_0002/fifo_0004 which are "UNKNOWN", and fifo_0001/fifo_0003 which are "SYNTAX").

That is approximately 44 skills with LOGIC error_type.

#### Step E: Score Each by Keyword Match + success_count
File: `trace2skill.py`, lines 92-94.

Consider a few specific skills from fifo.json:

**Skill fifo_0005** (line 57-63):
```json
{
  "id": "fifo_0005",
  "error_type": "LOGIC",
  "pattern": "The full flag is asserted when count equals 16, but a 16-entry FIFO should assert full when count equals 16 ...",
  "success_count": 1
}
```
- Keyword "full" in pattern → YES (+1)
- Keyword "count" in pattern → YES (+1)
- Keyword "threshold" in pattern → NO (+0)
- `keyword_matches = 2`
- `total_score = 2 + 1 = 3`

**Skill fifo_0006** (line 65-72):
```json
{
  "id": "fifo_0006",
  "error_type": "LOGIC",
  "pattern": "The full flag asserts when count reaches 16...",
  "success_count": 1
}
```
- Keyword "full" in pattern → YES (+1)
- Keyword "count" in pattern → YES (+1)
- `keyword_matches = 2`
- `total_score = 2 + 1 = 3`

**Skill fifo_0041** (line 415-422):
```json
{
  "id": "fifo_0041",
  "error_type": "LOGIC",
  "pattern": "The rst_n input is declared but never used...",
  "success_count": 1
}
```
- Keyword "full" → NO (+0)
- Keyword "count" → NO (+0)
- Keyword "threshold" → NO (+0)
- `keyword_matches = 0`
- **Excluded** (score=0, filtered by `if score > 0`)

**Skill fifo_0018** (line 185-192):
```json
{
  "id": "fifo_0018",
  "error_type": "LOGIC",
  "pattern": "The full flag asserts when count reaches 16 after the 16th write...",
  "success_count": 1
}
```
- "full" → YES (+1)
- "count" → YES (+1)
- "threshold" → NO (+0)
- `total_score = 2 + 1 = 3`

**Skill fifo_0019** (line 195-202):
```json
{
  "id": "fifo_0019",
  "error_type": "LOGIC",
  "pattern": "The full flag is incorrectly gated with wr_en...",
  "success_count": 1
}
```
- "full" → YES (+1)
- "count" → NO (+0)
- "threshold" → NO (+0)
- `keyword_matches = 1`
- `total_score = 1 + 1 = 2`

Skills with "full" OR "count" OR "threshold" in their pattern will match. Those with neither (like fifo_0041 about rst_n) get excluded.

#### Step F: Sort Descending, Take Top 3
File: `trace2skill.py`, lines 96-97.

Assuming most LOGIC skills in fifo.json have patterns containing "full" and "count" (as most are about full/empty flag issues), they all score around 3 (2 keyword matches + 1 success_count). The top 3 would be the first 3 skills encountered in the stable sort that score 3, likely:

1. `fifo_0005` (score=3) — "The full flag is asserted when count equals 16..."
2. `fifo_0006` (score=3) — "The full flag asserts when count reaches 16..."
3. `fifo_0007` (score=3) — "The full and empty flags are driven by both..."

Some skills score 2 (only "full" match) or potentially 3+ if they had higher `success_count`, but all fifo skills currently have `success_count=1`.

**Important observation:** Since all fifo LOGIC skills have `success_count=1` and most contain both "full" and "count" in their pattern, the keyword match portion is the same for most entries (2), and the tiebreaker is insertion order. This means the **first 3 LOGIC skills in the JSON array** are returned nearly every time for this keyword set.

#### Step G: Hits Stored in State
`log_analysis_agent.py`, line 101:
```python
"trace2skill_hits": hits   # list of 3 skill dicts
```

State is returned (lines 98-103):
```python
return {
    **state,
    "error_analysis": error_analysis,
    "trace2skill_hits": hits,
    "stage": "log_analysis_done"
}
```

#### Step H: Fix Agent Processes Hits
`fix_agent.py`, line 74 reads hits, line 85 checks category.

Since `category == "fifo"` (not "fsm"), the FSM truncation does not apply. All 3 hits pass through.

#### Step I: Format as Known Fixes Text
`fix_agent.py`, lines 87-90 produce:
```
- Pattern: The full flag is asserted when count equals 16, but a 16-entry FIFO should assert full when count equals 16 ... | Fix: Correct the count update condition to use wr_en and rd_en directly...
- Pattern: The full flag asserts when count reaches 16, but a 16-entry FIFO should assert full when count is 16... | Fix: Move the full and empty flag assignments to combinational logic...
- Pattern: The full and empty flags are driven by both a sequential always block... | Fix: Delete the lines "full <= (count == 5'd16);" and "empty <= (count == 5'd0);"...
```

#### Step J: Injected into FIX_PROMPT
`fix_agent.py`, line 111:
```python
known_fixes=known_fixes_text,
```

The `FIX_PROMPT` tells the LLM (lines 38-39):
```
The following are HINTS from memory — use them only if they directly match this exact error. Do NOT apply them blindly:
[3 hints inserted here]
```

#### Step K: Store the Attempt
After the LLM generates a fix, `fix_agent.py` lines 129-135 call:
```python
store_skill(
    category="fifo",
    error_type="LOGIC",
    pattern=error_analysis.get("CAUSE", "unknown pattern"),
    fix=error_analysis.get("FIX_SUGGESTION", ""),
    design_name="sync_fifo_8x16"
)
```

If the exact (CAUSE, LOGIC) pair already exists in fifo.json, its `success_count` is incremented. Otherwise, a new entry like `fifo_0054` is appended.

---

## 7. Skill Bank Statistics

| Category       | Entries | Error Types Present                        | Designs Represented           |
|----------------|---------|--------------------------------------------|-------------------------------|
| `combinational`| 57      | SYNTAX, UNKNOWN, LOGIC, COVERAGE           | alu_8bit                      |
| `fifo`         | 54      | LOGIC, UNKNOWN, SYNTAX, WIDTH              | sync_fifo_8x16                |
| `fsm`          | 84      | LOGIC, UNKNOWN, SYNTAX, TIMING, WIDTH      | uart_tx, fsm_traffic_light    |
| `axi`          | 12      | LOGIC, SYNTAX, UNKNOWN                     | apb_slave                     |
| `timing`       | 0       | (empty)                                    | (none)                        |
| **Total**      | **207** |                                            |                               |

---

## 8. Key Design Decisions

| Decision | Rationale | Code Location |
|----------|-----------|--------------|
| Unconditional `store_skill()` | Capture patterns even from failed attempts; future iterations may benefit | `fix_agent.py:129-135` |
| FSM truncation to 1 hit | FSM off-by-one errors are repetitive; multiple hints increase hallucination | `fix_agent.py:85-86` |
| Case-insensitive substring matching | Broad matching tolerates LLM keyword variation | `trace2skill.py:92` |
| `success_count` as score additive (not multiplier) | Avoids over-weighting frequently-seen generic errors | `trace2skill.py:94` |
| Keyword filter (`score > 0`) | Ensures only semantically relevant skills are returned | `trace2skill.py:93` |
| Stable sort tiebreaker | Predictable, deterministic ordering | `trace2skill.py:96` (Python's TimSort) |
| Prompt says "HINTS" not "FIX" | Prevents blind application of memory to wrong context | `fix_agent.py:38-39` |
