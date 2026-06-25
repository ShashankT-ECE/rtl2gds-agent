"""
skill.py — Trace2Skill response schemas.
"""
from typing import Optional

from pydantic import BaseModel, Field


class SkillEntry(BaseModel):
    """A single skill record from the skill bank."""
    id: str
    category: str
    error_type: str
    pattern: str
    fix: str
    design_name: Optional[str] = None
    success_count: int = 0
    confirmed_count: int = 0
    curated: bool = False
    last_seen: Optional[str] = None


class SkillCategorySummary(BaseModel):
    """Aggregated summary for one skill category."""
    category: str
    total_skills: int
    curated_count: int = Field(..., description="Skills with curated=True")
    confirmed_count: int = Field(..., description="Skills with confirmed_count > 0")
    unconfirmed_count: int = Field(..., description="Skills with confirmed_count == 0")
    error_types: list[str] = Field(default_factory=list, description="Distinct error types")


class SkillCategoryResponse(BaseModel):
    """Full detail for one category."""
    category: str
    summary: SkillCategorySummary
    skills: list[SkillEntry]


class SkillListResponse(BaseModel):
    """Returned by GET /api/skills — all categories summarized."""
    categories: list[SkillCategorySummary]
    total_skills: int
