"""
trace2skill.py
Persistent memory for the agent system.
Stores successful error fixes as skills in skills/ JSON files.
No ML, no training — just structured JSON memory.

Two-phase storage:
  1. store_skill_tentative: called by Fix Agent after generating a fix (before verification)
  2. confirm_skill / reject_skill: called after the subsequent simulation PASSES / FAILS

Retrieve functions:
  - get_curated_skills: returns only curated=True entries (highest confidence)
  - retrieve_skills: returns top-k best matching skills (confirmed_count > 0 only)
"""

import json
from pathlib import Path

SKILLS_DIR = Path(__file__).parent.parent.parent / "skills"

VALID_CATEGORIES = ["combinational", "fsm", "fifo", "axi", "timing"]


def _load(category: str) -> dict:
    path = SKILLS_DIR / f"{category}.json"
    with open(path) as f:
        return json.load(f)


def _save(category: str, data: dict):
    path = SKILLS_DIR / f"{category}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def store_skill(category: str, error_type: str, pattern: str, fix: str, design_name: str):
    """
    Store a fix in the skill bank with confirmed_count=0.
    Called by Fix Agent after generating a fix (before simulation confirms it works).
    Returns the skill_id so the pipeline can confirm or reject it later.

    Args:
        category: one of combinational, fsm, fifo, axi, timing
        error_type: SYNTAX, WIDTH, LOGIC, TIMING, COVERAGE, UNKNOWN
        pattern: short description of the error pattern seen
        fix: what was done to fix it
        design_name: which design this came from

    Returns:
        skill_id (str) — used by confirm_skill() / reject_skill()
    """
    assert category in VALID_CATEGORIES, f"Invalid category: {category}"

    bank = _load(category)

    # If same pattern already exists, just increment success_count
    for skill in bank["skills"]:
        if skill["pattern"] == pattern and skill["error_type"] == error_type:
            skill["success_count"] += 1
            skill["last_seen"] = design_name
            # Reset confirmed_count so the pipeline re-confirms on next pass
            skill["confirmed_count"] = skill.get("confirmed_count", 0)
            _save(category, bank)
            return skill["id"]

    # New skill
    skill_id = f"{category}_{len(bank['skills']):04d}"
    bank["skills"].append({
        "id": skill_id,
        "category": category,
        "error_type": error_type,
        "pattern": pattern,
        "fix": fix,
        "design_name": design_name,
        "success_count": 1,
        "confirmed_count": 0,
        "curated": False,
        "last_seen": design_name
    })

    _save(category, bank)
    return skill_id


def confirm_skill(skill_id: str, category: str):
    """
    Called after simulation confirms the fix worked.
    Increments confirmed_count so this skill is trusted for future retrievals.

    Args:
        skill_id: the id returned by store_skill()
        category: one of combinational, fsm, fifo, axi, timing
    """
    if not skill_id or not category:
        return
    assert category in VALID_CATEGORIES, f"Invalid category: {category}"

    bank = _load(category)
    for skill in bank["skills"]:
        if skill["id"] == skill_id:
            skill["confirmed_count"] = skill.get("confirmed_count", 0) + 1
            _save(category, bank)
            return

    # Skill not found — may have been removed during curation, silently ignore


def reject_skill(skill_id: str, category: str):
    """
    Called after simulation fails (fix didn't work).
    Removes the tentative skill from the bank so bad fixes don't pollute memory.

    Args:
        skill_id: the id returned by store_skill()
        category: one of combinational, fsm, fifo, axi, timing
    """
    if not skill_id or not category:
        return
    assert category in VALID_CATEGORIES, f"Invalid category: {category}"

    bank = _load(category)
    before = len(bank["skills"])
    bank["skills"] = [s for s in bank["skills"] if s["id"] != skill_id]
    if len(bank["skills"]) < before:
        _save(category, bank)


def get_curated_skills(category: str, error_type: str) -> list:
    """
    Returns only curated=True entries for the given category and error_type.
    Used by Fix Agent to place high-confidence curated fixes at the top of the prompt.

    Args:
        category: one of combinational, fsm, fifo, axi, timing
        error_type: SYNTAX, WIDTH, LOGIC, TIMING, COVERAGE, UNKNOWN

    Returns:
        list of matching skill dicts (curated=True only)
    """
    assert category in VALID_CATEGORIES, f"Invalid category: {category}"
    bank = _load(category)
    return [
        s for s in bank["skills"]
        if s.get("curated") is True and s["error_type"] == error_type
    ]


def retrieve_skills(category: str, error_type: str, keywords: list, top_k: int = 5) -> list:
    """
    Retrieve relevant skills before calling the LLM.
    Called by Fix Agent to check if we already know how to fix this.

    Rules:
    - Only returns entries with confirmed_count > 0 (verified fixes only)
    - Error_type exact match is required (never return SYNTAX fix for LOGIC error)
    - Curated entries always appear first (sorted by confirmed_count desc)
    - Non-curated entries sorted by confirmed_count desc

    Args:
        category: one of combinational, fsm, fifo, axi, timing
        error_type: SYNTAX, WIDTH, LOGIC, TIMING, COVERAGE, UNKNOWN
        keywords: list of keywords from the error log
        top_k: max number of results to return (default 5)

    Returns:
        list of matching skill dicts, sorted by score (curated first, then confirmed_count)
    """
    bank = _load(category)
    matches = []

    for skill in bank["skills"]:
        # Only return verified fixes
        if skill.get("confirmed_count", 0) <= 0:
            continue
        # Error_type exact match
        if skill["error_type"] != error_type:
            continue

        score = sum(1 for kw in keywords if kw.lower() in skill["pattern"].lower())
        if score > 0:
            # Boost curated entries
            if skill.get("curated"):
                score += 100  # curated entries always float to top
            score += skill.get("confirmed_count", 0)
            matches.append((score, skill))

    matches.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in matches[:top_k]]


def get_stats() -> dict:
    """Returns skill count per category. Used in SESSION_HANDOFF updates."""
    stats = {}
    for cat in VALID_CATEGORIES:
        bank = _load(cat)
        stats[cat] = len(bank["skills"])
    return stats
