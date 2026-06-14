"""
trace2skill.py
Persistent memory for the agent system.
Stores successful error fixes as skills in skills/ JSON files.
No ML, no training — just structured JSON memory.

Two functions agents will use:
- store_skill: called by Fix Agent after every successful fix
- retrieve_skills: called by Fix Agent before calling the LLM
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
    Store a successful fix in the skill bank.
    Called by Fix Agent after every successful correction.

    Args:
        category: one of combinational, fsm, fifo, axi, timing
        error_type: SYNTAX, WIDTH, LOGIC, TIMING, COVERAGE, UNKNOWN
        pattern: short description of the error pattern seen
        fix: what was done to fix it
        design_name: which design this came from
    """
    assert category in VALID_CATEGORIES, f"Invalid category: {category}"

    bank = _load(category)

    # If same pattern already exists, just increment count
    for skill in bank["skills"]:
        if skill["pattern"] == pattern and skill["error_type"] == error_type:
            skill["success_count"] += 1
            skill["last_seen"] = design_name
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
        "last_seen": design_name
    })

    _save(category, bank)
    return skill_id


def retrieve_skills(category: str, error_type: str, keywords: list) -> list:
    """
    Retrieve relevant skills before calling the LLM.
    Called by Fix Agent to check if we already know how to fix this.

    Args:
        category: one of combinational, fsm, fifo, axi, timing
        error_type: SYNTAX, WIDTH, LOGIC, TIMING, COVERAGE, UNKNOWN
        keywords: list of keywords from the error log

    Returns:
        list of matching skill dicts, sorted by success_count
    """
    bank = _load(category)
    matches = []

    for skill in bank["skills"]:
        if skill["error_type"] != error_type:
            continue
        score = sum(1 for kw in keywords if kw.lower() in skill["pattern"].lower())
        if score > 0:
            matches.append((score + skill["success_count"], skill))

    matches.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in matches[:3]]


def get_stats() -> dict:
    """Returns skill count per category. Used in SESSION_HANDOFF updates."""
    stats = {}
    for cat in VALID_CATEGORIES:
        bank = _load(cat)
        stats[cat] = len(bank["skills"])
    return stats
