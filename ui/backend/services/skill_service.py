"""
skill_service.py — Read Trace2Skill memory data.

Delegates to the existing v1_core/utils/trace2skill.py module.
That module already provides get_stats(), get_curated_skills(), and
retrieve_skills(). This service layer adds aggregation and response
formatting for the REST API.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from ui.backend.config import settings
from ui.backend.exceptions import SkillCategoryNotFoundError
from ui.backend.schemas.skill import (
    SkillCategoryResponse,
    SkillCategorySummary,
    SkillEntry,
    SkillListResponse,
)

logger = logging.getLogger(__name__)

# Skill categories are defined in the frozen trace2skill module.
_VALID_CATEGORIES: list[str] = []


def _get_valid_categories() -> list[str]:
    """Lazily import VALID_CATEGORIES from v1_core.utils.trace2skill."""
    global _VALID_CATEGORIES
    if not _VALID_CATEGORIES:
        try:
            from v1_core.utils.trace2skill import VALID_CATEGORIES
            _VALID_CATEGORIES = list(VALID_CATEGORIES)
        except ImportError:
            # Fallback — trace2skill module may not be importable (e.g. in tests)
            _VALID_CATEGORIES = ["combinational", "fsm", "fifo", "axi", "timing"]
    return _VALID_CATEGORIES


class SkillService:
    """Read-only access to Trace2Skill skill bank files.

    All data comes from the skills/*.json files via the existing
    v1_core/utils/trace2skill module — we never write from here.
    """

    def __init__(self) -> None:
        self._dir = settings.SKILLS_DIR

    # ---- _load delegates to trace2skill._load when available --------------

    @staticmethod
    def _load_bank(category: str) -> dict:
        """Load a skill JSON file. Uses trace2skill if importable, else direct read."""
        try:
            from v1_core.utils.trace2skill import _load
            return _load(category)
        except ImportError:
            import json
            path = settings.SKILLS_DIR / f"{category}.json"
            with open(path) as f:
                return json.load(f)

    # ---- Public API -------------------------------------------------------

    def get_summary(self) -> SkillListResponse:
        """Return category-level summaries for all skill categories."""
        categories: list[SkillCategorySummary] = []
        total = 0

        for cat in _get_valid_categories():
            summary = self._summarize(cat)
            categories.append(summary)
            total += summary.total_skills

        return SkillListResponse(categories=categories, total_skills=total)

    def get_category(self, category: str) -> SkillCategoryResponse:
        """Return full detail for a single category."""
        categories = _get_valid_categories()
        if category not in categories:
            raise SkillCategoryNotFoundError(
                f"Skill category '{category}' not found. "
                f"Valid categories: {', '.join(categories)}"
            )

        bank = self._load_bank(category)
        summary = self._summarize(category)
        skills = [SkillEntry(**s) for s in bank.get("skills", [])]

        return SkillCategoryResponse(category=category, summary=summary, skills=skills)

    def get_stats(self) -> dict[str, int]:
        """Return skill counts per category (for status endpoint)."""
        stats: dict[str, int] = {}
        for cat in _get_valid_categories():
            try:
                bank = self._load_bank(cat)
                stats[cat] = len(bank.get("skills", []))
            except Exception:
                stats[cat] = 0
        return stats

    def total_skills(self) -> int:
        """Total skill count across all categories."""
        return sum(self.get_stats().values())

    # ---- Internal ---------------------------------------------------------

    def _summarize(self, category: str) -> SkillCategorySummary:
        """Build a summary object for one category."""
        bank = self._load_bank(category)
        skills = bank.get("skills", [])
        curated = sum(1 for s in skills if s.get("curated"))
        confirmed = sum(1 for s in skills if s.get("confirmed_count", 0) > 0)
        unconfirmed = len(skills) - confirmed
        error_types = sorted({s.get("error_type", "UNKNOWN") for s in skills})

        return SkillCategorySummary(
            category=category,
            total_skills=len(skills),
            curated_count=curated,
            confirmed_count=confirmed,
            unconfirmed_count=unconfirmed,
            error_types=error_types,
        )
