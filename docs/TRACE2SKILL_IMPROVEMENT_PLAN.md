# Trace2Skill Improvement Plan

## 1. Current State Summary

### Inventory

| Category | Skill Count | File Size | Reinforced (>1 success) | Dominant Error Types |
|----------|-------------|-----------|------------------------|---------------------|
| combinational | 57 | 28 KB | 0 / 57 | UNKNOWN (37), SYNTAX (12), LOGIC (6), COVERAGE (4) |
| fsm | 84 | 48 KB | 0 / 84 | LOGIC (75), SYNTAX (4), UNKNOWN (3), TIMING (1), WIDTH (1) |
| fifo | ~54 | 30 KB | 0 / ~54 | UNKNOWN, SYNTAX (mix) |
| axi | ~12 | 6 KB | 0 / ~12 | SYNTAX, LOGIC (mix) |
| timing | 0 | 33 B | 0 / 0 | (empty) |
| **Total** | **~207** | **~112 KB** | **0 / 207** | |

### Critical Observations

1. **Zero reinforcement.** Every single skill has `success_count=1`. Not one has been retrieved and re-used successfully, which means the reinforcement mechanism (increment count on pattern match) has never fired in a meaningful way, or the scoring logic never updates `success_count` in `store_skill()` when a retrieved skill is applied again.

2. **Massive near-duplicate bloat.** Roughly 33 of 57 combinational skills (58%) are near-verbatim duplicates of the same two error patterns: (a) "cocotb runner module missing" and (b) "no test functions discovered in testbench module." The `store_skill()` deduplication check compares exact `(pattern, error_type)` pairs, but the LLM generates slightly different wording each time, so every iteration creates a new skill. In fsm.json, approximately 50 of 84 skills (60%) describe the same fundamental "counter off-by-one" bug with slightly varied wording.

3. **Unconditional storage.** `fix_agent.py` calls `store_skill()` on line 129 for every fix attempt, regardless of whether the fix passes simulation. This means failed fixes and incorrect analyses are stored as "successful" skills, polluting the memory.

4. **Only 2 consumers of 7 agents.** Only `log_analysis_agent.py` (retrieve) and `fix_agent.py` (retrieve + store) use Trace2Skill. The other 5 agents (`rtl_gen`, `testbench`, `spec_parser`, `verification_planner`, `simulation`) have no memory integration.

5. **Prompt undermines the memory system.** The `FIX_PROMPT` in `fix_agent.py` line 38 says: *"Do NOT apply them blindly"* — this instructs the LLM to treat memory as unreliable, defeating the purpose of having a memory system.

6. **No timestamp tracking.** Skills lack `created_at` / `updated_at` fields, making it impossible to evict stale entries or measure recency.

7. **No cross-skill deduplication.** Multiple categories store the same Makefile/cocotb infrastructure error patterns, but there is no cross-category consolidation.

8. **`trace2skill_hits` is never cleared.** Between fix iterations, `trace2skill_hits` in the pipeline state retains values from the previous iteration's log analysis, so hits accumulate and become stale.

---

## 2. Quick Wins (Low Effort, High Impact)

### Quick Win 1: Conditional Storage

| Property | Value |
|----------|-------|
| Effort | 1 hour |
| Impact | HIGH |
| Files Affected | `v1_core/agents/fix_agent.py` |
| Risk | Minimal — only changes store condition |

**Problem:** `fix_agent.py` stores every fix as a skill unconditionally, including failed fixes. The agent runs a fix, stores the skill, then simulation runs later and may fail. This populates the memory with incorrect patterns.

**Before (fix_agent.py ~line 126-135):**
```python
logger.success("Fix generated — storing in Trace2Skill")
store_skill(
    category=category,
    error_type=error_type,
    pattern=error_analysis.get("CAUSE", "unknown pattern"),
    fix=error_analysis.get("FIX_SUGGESTION", ""),
    design_name=state["design_name"]
)
```

**After:**
```python
# Store is deferred — called by Simulation Agent when sim passes
# Add trace2skill_pending to PipelineState
state["trace2skill_pending"] = {
    "category": category,
    "error_type": error_type,
    "pattern": error_analysis.get("CAUSE", "unknown pattern"),
    "fix": error_analysis.get("FIX_SUGGESTION", ""),
    "design_name": state["design_name"]
}
```

Then in `simulation_agent.py`:
```python
if sim_passed and state.get("trace2skill_pending"):
    from v1_core.utils.trace2skill import store_skill
    pending = state["trace2skill_pending"]
    store_skill(**pending)
    logger.success("Fix verified — stored in Trace2Skill")
```

**Alternative (simpler, recommended):** Pass `sim_passed` as a parameter to `store_skill` and have it return early if `sim_passed` is False. The fix agent already has access to simulation state via the pipeline.

**Risks:** None. This only prevents storing bad data.

---

### Quick Win 2: Eviction Cap with LRU

| Property | Value |
|----------|-------|
| Effort | 2 hours |
| Impact | MEDIUM |
| Files Affected | `v1_core/utils/trace2skill.py` |
| Risk | Low — additive only |

**Problem:** No upper bound on skills per category. With each fix iteration creating a new skill (often near-duplicate), the files grow unboundedly, slowing retrieval and diluting signal.

**Before (`trace2skill.py` ~line 56-68):**
```python
# New skill (no size check)
skill_id = f"{category}_{len(bank['skills']):04d}"
bank["skills"].append({...})
```

**After:**
```python
MAX_SKILLS = 200  # per category

# New skill
skill_id = f"{category}_{len(bank['skills']):04d}"
bank["skills"].append({...})

# Evict if over cap — remove oldest by last_seen (approximately LRU)
if len(bank["skills"]) > MAX_SKILLS:
    bank["skills"].sort(key=lambda s: s.get("last_seen", ""))
    bank["skills"] = bank["skills"][-MAX_SKILLS:]
```

**Risks:** Sorting by `last_seen` requires all skills to have `last_seen` populated (currently they do). Once timestamps are added (Quick Win 3), sort by `updated_at` for true LRU.

**Note:** The initial cap should be set to accommodate the ~57-84 current sizes per category without triggering mass eviction. 200 per category is safe.

---

### Quick Win 3: Timestamp Fields

| Property | Value |
|----------|-------|
| Effort | 1 hour |
| Impact | MEDIUM |
| Files Affected | `v1_core/utils/trace2skill.py` |
| Risk | Low — backward compatible via default |

**Problem:** Skills lack timestamps, making it impossible to implement LRU eviction, measure recency, or track stale skills.

**Before (`trace2skill.py` ~line 58-67):**
```python
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
```

**After:**
```python
import datetime

now = datetime.datetime.utcnow().isoformat()
bank["skills"].append({
    "id": skill_id,
    "category": category,
    "error_type": error_type,
    "pattern": pattern,
    "fix": fix,
    "design_name": design_name,
    "success_count": 1,
    "last_seen": design_name,
    "created_at": now,
    "updated_at": now
})
```

Also update the existing-skill increment path (~line 49-54):
```python
if skill["pattern"] == pattern and skill["error_type"] == error_type:
    skill["success_count"] += 1
    skill["last_seen"] = design_name
    skill["updated_at"] = now
    _save(category, bank)
    return skill["id"]
```

**Risks:** Old skills lack these fields. Handle gracefully with `.get("created_at", "unknown")` in sorting/display.

---

### Quick Win 4: State Clearing for `trace2skill_hits`

| Property | Value |
|----------|-------|
| Effort | 30 minutes |
| Impact | MEDIUM |
| Files Affected | `v1_core/agents/fix_agent.py` |
| Risk | Low — no side effects |

**Problem:** `trace2skill_hits` is set by `log_analysis_agent.py` but never cleared between fix iterations. If the pipeline loops (fix -> simulate -> analyze -> fix again), old hits persist and may reference a different error.

**Before (fix_agent.py ~line 137-143):**
```python
return {
    **state,
    "rtl_code": fixed_rtl,
    "testbench_code": "",
    "iteration": state["iteration"] + 1,
    "stage": "fix_applied"
}
```

**After:**
```python
return {
    **state,
    "rtl_code": fixed_rtl,
    "testbench_code": "",
    "trace2skill_hits": [],  # Clear for next iteration
    "trace2skill_pending": None,
    "iteration": state["iteration"] + 1,
    "stage": "fix_applied"
}
```

**Risks:** None. Clearing state between iterations prevents stale data bleed.

---

### Quick Win 5: Hit Logging

| Property | Value |
|----------|-------|
| Effort | 1 hour |
| Impact | LOW |
| Files Affected | `v1_core/agents/fix_agent.py` |
| Risk | Low — logging only |

**Problem:** When a retrieved skill actually matches and is used by the LLM to generate a correct fix, there is no log message. This makes it impossible to measure memory system effectiveness.

**Before (fix_agent.py ~line 87-93):**
```python
if hits:
    known_fixes_text = "\n".join([...])
    logger.info(f"Using {len(hits)} Trace2Skill hint(s) in prompt")
```

**After:**
```python
if hits:
    known_fixes_text = "\n".join([...])
    logger.info(f"Using {len(hits)} Trace2Skill hint(s) in prompt")
    for h in hits:
        logger.info(f"  T2S hit: {h['id']} | {h['pattern'][:80]}...")
```

Also, add post-simulation logging in the calling orchestrator or simulation agent:
```python
# After sim_passed check
if sim_passed and state.get("trace2skill_hits"):
    hit_ids = [h["id"] for h in state["trace2skill_hits"]]
    logger.success(f"Trace2Skill contributed to fix: {', '.join(hit_ids)}")
```

**Risks:** None.

---

## 3. Medium Improvements

### 3a. Dual-Category Retrieval

**Problem:** `_guess_category` returns a single category based on design name. If a FIFO design has a SYNTAX error that matches a pattern stored under "combinational" (e.g., Makefile missing), the retrieval misses it entirely.

**Current behavior (`log_analysis_agent.py` line 86-91):**
```python
category = _guess_category(state["design_name"])
hits = retrieve_skills(
    category=category,
    error_type=error_type,
    keywords=keywords
)
```

**Proposed behavior:**
```python
primary_cat = _guess_category(state["design_name"])
hits = retrieve_skills(primary_cat, error_type, keywords)

# Fallback to combinational if primary returned nothing
if not hits and primary_cat != "combinational":
    fallback_hits = retrieve_skills("combinational", error_type, keywords)
    hits = fallback_hits
```

**Why combinational as fallback:** The combinational category already contains infrastructure-level patterns (Makefile missing, cocotb runner not found, test discovery failure) that apply across all design types.

**Risks:** Double loading of JSON files on miss. Mitigation: cache loaded data in memory (dict) for the session.

---

### 3b. Fuzzy `error_type` Matching

**Problem:** `retrieve_skills()` does an exact match on `error_type` (line 90: `if skill["error_type"] != error_type: continue`). A LOGIC error from `log_analysis_agent.py` will never match a skill stored as UNKNOWN, even if the pattern is identical. Similarly, WIDTH, LOGIC, and UNKNOWN often describe the same class of functional mismatches.

**Current exact-match filter (`trace2skill.py` ~line 89-92):**
```python
for skill in bank["skills"]:
    if skill["error_type"] != error_type:
        continue
```

**Proposed:**
```python
# Define error type groups for retrieval broadening
ERROR_TYPE_GROUPS = {
    "FUNCTIONAL": {"LOGIC", "WIDTH", "UNKNOWN"},
    "STRUCTURAL": {"SYNTAX", "COVERAGE"},
    "PERFORMANCE": {"TIMING"}
}

def _error_type_matches(skill_et: str, query_et: str) -> bool:
    """Check if skill error type matches query, with grouping."""
    if skill_et == query_et:
        return True
    # Broader group matching
    for group_name, members in ERROR_TYPE_GROUPS.items():
        if query_et in members and skill_et in members:
            return True
    return False

for skill in bank["skills"]:
    if not _error_type_matches(skill["error_type"], error_type):
        continue
```

**Risks:** Broader matching returns more hits, potentially including irrelevant ones. Mitigation: matches are scored and only top 3 returned; latency impact minimal.

---

### 3c. Remove Near-Duplicates on Write

**Problem:** The current deduplication at `store_skill()` line 49-50 checks exact `pattern == pattern` and `error_type == error_type`. Since the LLM generates slightly different wording each time, near-identical patterns bypass dedup and bloat the skill bank.

**Current dedup check:**
```python
for skill in bank["skills"]:
    if skill["pattern"] == pattern and skill["error_type"] == error_type:
        skill["success_count"] += 1
        ...
        return skill["id"]
```

**Proposed word-overlap dedup:**
```python
def _is_duplicate(new_pattern: str, existing_pattern: str, threshold: float = 0.7) -> bool:
    """Check if new_pattern shares >70% words with existing_pattern."""
    new_words = set(new_pattern.lower().split())
    existing_words = set(existing_pattern.lower().split())
    if not new_words or not existing_words:
        return False
    intersection = new_words & existing_words
    union = new_words | existing_words
    return len(intersection) / len(union) > threshold

def store_skill(category, error_type, pattern, fix, design_name):
    bank = _load(category)
    
    for skill in bank["skills"]:
        if skill["error_type"] == error_type and _is_duplicate(pattern, skill["pattern"]):
            skill["success_count"] += 1
            skill["last_seen"] = design_name
            skill["updated_at"] = datetime.datetime.utcnow().isoformat()
            _save(category, bank)
            return skill["id"]
    
    # New skill (rest unchanged)
```

**Impact analysis:** This would collapse the ~33 combinational near-duplicates (runner missing + test discovery) into roughly 2-3 entries, reducing file size by ~50% and improving retrieval precision.

**Risks:** Word-overlap similarity is simplistic. "Shift left" vs "shift right" share many words but are semantically opposite. Mitigation: raise threshold to 0.8 and add common-signal-word filtering (`{clk, rst, data, tx, rx}` stripped before comparison). For V3, consider embedding-based similarity instead.

---

### 3d. Prompt Instruction Improvement

**Problem:** The `FIX_PROMPT` in `fix_agent.py` actively tells the LLM to distrust memory:

> *"The following are HINTS from memory — use them only if they directly match this exact error. Do NOT apply them blindly:"*

This language trains the LLM to discount retrieved skills, undermining the entire memory system.

**Proposed replacement (line 38-39 of fix_agent.py):**
> *"The following are verified fixes from our skill memory for similar errors. Prefer the fix from memory if it matches the current error pattern. Adapt if needed:"*

**Risks:** The LLM may over-rely on memory for errors that only superficially match. Mitigation: keep the number of hints at 1-3 (already limited), and include `exact_fix` as a separate strong signal.

---

### 3e. Reinforcement Signal

**Problem:** `success_count` is never incremented outside of `store_skill()` when a duplicate pattern is stored. When a retrieved skill is applied and the fix passes simulation, there is no feedback loop to reinforce it.

**Proposed mechanism:**

1. In `fix_agent.py`, record which skill IDs were used as hints:
   ```python
   used_skill_ids = [h["id"] for h in hits] if hits else []
   ```

2. Pass this to the pipeline state:
   ```python
   state["used_skill_ids"] = used_skill_ids
   ```

3. In `simulation_agent.py` (or the orchestrator), when simulation passes:
   ```python
   if sim_passed and state.get("used_skill_ids"):
       for skill_id in state["used_skill_ids"]:
           # Parse category from skill_id (e.g., "fsm_0042" -> "fsm")
           cat = skill_id.rsplit("_", 1)[0]
           bank = _load(cat)
           for skill in bank["skills"]:
               if skill["id"] == skill_id:
                   skill["success_count"] += 1
                   skill["updated_at"] = datetime.datetime.utcnow().isoformat()
                   _save(cat, bank)
                   logger.success(f"Reinforced skill {skill_id}: success_count={skill['success_count']}")
   ```

**Risks:** Minimal. The reinforcement is bounded by the maximum number of retrievals per session.

---

## 4. Major Improvements

### 4a. Semantic Retrieval (Embedding-Based)

**Problem:** Current keyword matching (`sum(1 for kw in keywords if kw.lower() in skill["pattern"].lower())`) is fragile. It matches substrings, not semantics. "Makefile missing" won't match "build system cannot locate Makefile" if the LLM extracts different keywords.

**Proposed approach:**

```python
# In trace2skill.py, add embedding storage and retrieval

def _get_embedding(text: str) -> list[float]:
    """Use LLM to generate embedding for text."""
    response = call_llm(
        prompt=f"Generate a 256-dimensional embedding vector for this error pattern as a JSON list of floats: {text}",
        task="embedding"
    )
    return json.loads(response)

def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x*y for x, y in zip(a, b))
    norm_a = sum(x*x for x in a) ** 0.5
    norm_b = sum(y*y for y in b) ** 0.5
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

def store_skill(category, error_type, pattern, fix, design_name):
    # ... existing logic ...
    embedding = _get_embedding(pattern)
    bank["skills"][-1]["embedding"] = embedding

def retrieve_skills(category, error_type, keywords, query_text=None):
    bank = _load(category)
    # If query_text provided, use embedding similarity
    if query_text:
        query_emb = _get_embedding(query_text)
        scored = []
        for skill in bank["skills"]:
            if "embedding" not in skill:
                continue
            sim = _cosine_similarity(query_emb, skill["embedding"])
            scored.append((sim + skill["success_count"] * 0.1, skill))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:3]]
    # Fallback to keyword matching
    # ... existing logic ...
```

**Risks:** High API cost for embedding generation (one call per store + one per retrieve). Mitigation: cache embeddings, batch compute, or use a local sentence-transformers model if available. Potential solution: generate embedding only for patterns that survive dedup (Quick Win 3c), not every attempted store.

---

### 4b. Cross-Category Consolidation

**Problem:** Skills are partitioned by category at write and read time. A UART (FSM) error pattern about "Makefile not found" is stored under "fsm" but should be retrievable when a FIFO design hits the same issue.

**Proposed architecture:**

```python
# Unified skill index
UNIFIED_SKILLS_PATH = SKILLS_DIR / "unified.json"

def _load_unified() -> dict:
    """Load or build unified index from all category files."""
    unified = {"skills": [], "version": "1.0"}
    for cat in VALID_CATEGORIES:
        bank = _load(cat)
        for skill in bank["skills"]:
            # Tag with original category
            skill["design_types"] = [cat]
            unified["skills"].append(skill)
    return unified

def retrieve_skills_global(error_type: str, keywords: list, design_types: list = None) -> list:
    """Retrieve across all categories, optionally filtering by design type."""
    unified = _load_unified()
    matches = []
    for skill in unified["skills"]:
        if design_types and not any(dt in skill.get("design_types", []) for dt in design_types):
            continue
        # Apply same keyword scoring across all skills
        ...
    return sorted_matches[:5]
```

**Risks:** Loading all categories into memory on each retrieval increases latency. Mitigation: LRU cache for parsed data, or migrate to SQLite (4d).

---

### 4c. Multi-Agent Consumption

**Problem:** Only `log_analysis_agent` and `fix_agent` use Trace2Skill. The other 5 agents operate without memory, repeating the same mistakes across sessions.

**Proposed integration per agent:**

| Agent | Store Trigger | Store Content | Retrieve Trigger |
|-------|--------------|---------------|-----------------|
| **rtl_gen** | After successful RTL generation + simulation pass | Known-good RTL patterns per design type (parameter values, module structure) | Before generating RTL for a known design type |
| **testbench** | After successful testbench generation + simulation pass | Testbench templates, port mappings, stimulus patterns | Before generating testbench for a known design |
| **spec_parser** | After spec parsing + successful downstream use | Known spec formats, parameter mappings, corrections | Before parsing a new spec file |
| **verification_planner** | After verification plan + tests pass | Coverage patterns, test sequences, expected behavior templates | Before building verification strategy for a design type |
| **simulation** | N/A (no LLM calls) | N/A | N/A directly; signals reinforcement to fix_agent |

**Risks:** High effort. Each agent needs its own prompt instructions and store/retrieve points. Must be phased in gradually.

---

### 4d. Database-Backed Storage (SQLite)

**Problem:** Concurrent writes to JSON files can corrupt data (multiple agents writing simultaneously is not safe). JSON deserialization of ~100+ skills on every retrieve call is also wasteful.

**Proposed migration:**

```python
import sqlite3

DB_PATH = SKILLS_DIR / "trace2skill.db"

def _init_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            error_type TEXT NOT NULL,
            pattern TEXT,
            fix TEXT,
            design_name TEXT,
            success_count INTEGER DEFAULT 1,
            last_seen TEXT,
            created_at TEXT,
            updated_at TEXT,
            embedding BLOB,
            quality_score REAL DEFAULT 1.0
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_category_error 
        ON skills(category, error_type)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_success_count
        ON skills(success_count DESC)
    """)
    conn.commit()
    conn.close()

def retrieve_skills_sql(category, error_type, keywords):
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.execute(
        "SELECT * FROM skills WHERE category=? AND error_type=? ORDER BY success_count DESC LIMIT 5",
        (category, error_type)
    )
    rows = cur.fetchall()
    conn.close()
    # Convert to dicts and apply keyword scoring
    ...
```

**Benefits:** Atomic writes, efficient queries, no full-file rewrites, concurrent-safe via WAL mode, easy to add columns.

**Migration path:** Keep JSON files as read-only backup. Write to SQLite only. If SQLite is missing, fall back to JSON.

**Risks:** Medium. Requires adding `sqlite3` dependency (stdlib in Python 3). Schema changes require migration logic.

---

### 4e. Skill Quality Scoring

**Problem:** All skills are treated equally. A skill stored from a fluke fix (wrong fix that happened to pass) has equal weight to a well-tested pattern.

**Proposed mechanism:**

```python
# In skill schema
skill["quality_score"] = 1.0  # default
skill["quality_signals"] = {
    "fixes_applied": 1,      # times this fix was used
    "fixes_failed": 0,       # times this fix was used but sim failed
    "user_verified": False,   # user confirmed fix is correct
    "auto_generated": True    # True = from LLM, False = from human
}

# In retrieval, weight by quality score
score = keyword_score + success_count * 0.5 + skill.get("quality_score", 1.0) * 2.0
```

When a retrieved skill is followed by a failed simulation, decrease quality:
```python
skill["quality_score"] = max(0.0, skill["quality_score"] - 0.1)
```

When a retrieved skill is followed by a passed simulation, increase quality:
```python
skill["quality_score"] = min(1.0, skill["quality_score"] + 0.05)"
```

**Risks:** Low. Quality scoring is additive and doesn't break existing behavior.

---

## 5. V3 Readiness Assessment

| Dimension | Current State | V3 Target | Gap Assessment | Priority |
|-----------|---------------|-----------|----------------|----------|
| **Skill capacity** | Unlimited (207) | 500 with eviction | No immediate gap, but eviction needed for long-term health | Low |
| **Retrieval accuracy** | Keyword-only exact match on error_type | Semantic + keyword + fuzzy matching | **Large gap.** Current retrieval misses ~60% of relevant skills due to exact error_type filter and fragile keyword overlap | HIGH |
| **Storage durability** | JSON file (single-writer) | JSON + backup or SQLite | Small gap. Single-writer is fragile but manageable for single-pipeline runs | Medium |
| **Consumer coverage** | 2 agents (log_analysis, fix) | All 7 agents | **Large gap.** 5 of 7 agents have no memory integration | HIGH |
| **Quality control** | No validation before storage | Conditional store + dedup + scoring | **Large gap.** 58% of combinational skills are near-duplicates; failed fixes pollute memory | HIGH |
| **Self-improvement** | None (all success_count=1) | Reinforcement loop with pass/fail feedback | **Large gap.** Zero reinforcement means the system learns nothing across iterations | HIGH |
| **Cross-session persistence** | File-based | File-based + versioning | Small gap. Version field exists (1.0) but unused | Low |
| **Deduplication** | Exact match only | Word-overlap + embedding similarity | **Large gap.** Near-identical LLM outputs bypass dedup every time | HIGH |
| **Prompt alignment** | "Do NOT apply blindly" | "Prefer memory when matching" | Medium gap. Current prompt actively sabotages memory | Medium |

### Gap Severity Summary

- **Critical gaps:** Retrieval accuracy, quality control, self-improvement, deduplication
- **Major gaps:** Consumer coverage
- **Minor gaps:** Storage durability, cross-session persistence
- **No gap:** Capacity

---

## 6. Implementation Roadmap

### Phase 1 — Stabilization (Week 1)
*Target: Stop the bleeding. Prevent bad data from entering the system.*

| Day | Task | Depends On | Effort |
|-----|------|------------|--------|
| 1 | Conditional storage (Quick Win 1) | None | 1h |
| 1 | State clearing for `trace2skill_hits` (Quick Win 4) | None | 30min |
| 2 | Timestamp fields (Quick Win 3) | None | 1h |
| 2 | Eviction cap with LRU (Quick Win 2) | Quick Win 3 | 2h |
| 3 | Near-duplicate removal on write (Medium 3c) | Quick Win 3 | 3h |
| 4 | Word-overlap threshold tuning | Medium 3c | 1h |
| 5 | Hit logging (Quick Win 5) | None | 1h |
| 5 | Integration testing | All above | 2h |

**Phase 1 Exit Criteria:**
- No new skills stored if simulation fails
- `trace2skill_hits` cleared between iterations
- All skills have timestamps
- Categories capped at 200 skills with LRU eviction
- Near-duplicate skills collapsed (combinational expected to drop from 57 to ~20)
- Retrieval of each skill logged

---

### Phase 2 — Accuracy Improvement (Week 2-3)
*Target: Make retrieval actually useful.*

| Day | Task | Depends On | Effort |
|-----|------|------------|--------|
| 6-7 | Dual-category retrieval (Medium 3a) | Phase 1 | 2h |
| 7-8 | Fuzzy error_type matching (Medium 3b) | Phase 1 | 2h |
| 8 | Prompt instruction fix (Medium 3d) | Phase 1 | 30min |
| 9-10 | Reinforcement signal (Medium 3e) | Phase 1 + Quick Win 1 | 3h |
| 10-11 | Cross-session hit rate tracking | Medium 3e | 2h |
| 12-13 | Regression testing on 5 benchmarks | All above | 4h |

**Phase 2 Exit Criteria:**
- Fallback to combinational when primary category yields no hits
- Error type groups (FUNCTIONAL, STRUCTURAL) for broadened matching
- Prompt says "Prefer from memory" instead of "Don't apply blindly"
- `success_count` increments when retrieved fix leads to passing simulation
- Measurable improvement in fix iteration count across 5 benchmarks

---

### Phase 3 — Expansion (Month 2)
*Target: Semantic retrieval, cross-category, multi-agent.*

| Week | Task | Depends On | Effort |
|------|------|------------|--------|
| 1 | Embedding-based similarity (Major 4a) | Phase 2 | 1 week |
| 1 | Cross-category index (Major 4b) | Phase 2 | 3 days |
| 2 | SQLite migration (Major 4d) | Phase 1 | 1 week |
| 2-3 | Multi-agent integration — rtl_gen (Major 4c) | Phase 2 | 3 days |
| 3 | Multi-agent integration — testbench | Major 4c | 2 days |
| 3-4 | Multi-agent integration — spec_parser + verification_planner | Major 4c | 3 days |
| 4 | Quality scoring (Major 4e) | Phase 2 | 2 days |
| 4 | Full regression + tuning | All | 3 days |

**Phase 3 Exit Criteria:**
- Embedding-based retrieval operational (fallback to keyword if API unavailable)
- Single unified index with design_type tags
- SQLite backing with JSON fallback
- All 7 agents store and retrieve skills
- Quality scores tracked and used in retrieval ranking

---

## 7. Recommendation

**Assessment: (c) Needs Medium improvements before V3**

### Justification

The current Trace2Skill system has structural flaws that prevent it from functioning as a reliable memory system:

1. **Zero reinforcement across 207 skills** means the system has never demonstrated its core value proposition — learning from past fixes. Every fix starts from scratch.

2. **58% near-duplicate bloat** in combinational skills means retrieval precision is poor. The top-3 results are statistically likely to be three variations of "no test functions found" rather than the actual error pattern.

3. **The prompt actively discourages using memory.** This is a design contradiction: invest engineering effort to build a memory system, then tell the LLM not to trust it.

4. **Unconditional storage of failed fixes** means the memory contains noise and errors, making it damaging rather than helpful to retrieve from.

### Why not (a) "Ready as-is"?

The system cannot pass a simple adversarial test: if you delete all skills and re-run the pipeline, performance should be identical because zero skills have been reinforced. A system with no measurable impact is not ready for V3.

### Why not (b) "Quick Wins only"?

Quick Wins prevent bad data from entering the system, but they don't fix the existing data quality issues or the retrieval accuracy. Phase 2 improvements (fuzzy matching, prompt fix, reinforcement) are essential to make the existing 207 skills actually useful.

### Why not (d) "Major improvements required"?

The major improvements (semantic retrieval, SQLite, multi-agent, quality scoring) are valuable but not blocking for V3. The system can function effectively with keyword + fuzzy matching if data quality is high and the prompt is aligned. SQLite and multi-agent can be deferred to V3.1+.

### Recommended Pre-V3 Sprint (2 weeks)

| Priority | Item | Type | Criticality |
|----------|------|------|-------------|
| P0 | Conditional storage | Quick Win 1 | Blocking — prevents data corruption |
| P0 | Prompt instruction fix | Medium 3d | Blocking — fixes design contradiction |
| P0 | Near-duplicate dedup | Medium 3c | Blocking — essential for data quality |
| P1 | State clearing | Quick Win 4 | High — prevents stale iteration bugs |
| P1 | Reinforcement signal | Medium 3e | High — enables measurable learning |
| P2 | Fuzzy error_type matching | Medium 3b | Medium — improves recall |
| P2 | Dual-category retrieval | Medium 3a | Medium — broadens coverage |
| P3 | Timestamp fields | Quick Win 3 | Low — enables LRU |
| P3 | Eviction cap | Quick Win 2 | Low — future-proofing |
| P3 | Hit logging | Quick Win 5 | Low — observability |

After completing these items, Trace2Skill would be V3-ready with the following characteristics:
- ~25-35 high-quality deduplicated skills after initial cleanup
- Reinforcement tracking on every successful fix
- Broad-match retrieval across categories and error type groups
- LLM prompt aligned to prefer memory
- Timestamps and eviction for long-term health
