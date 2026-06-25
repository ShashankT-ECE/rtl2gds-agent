"""
skills.py — Trace2Skill memory endpoints.
"""

from fastapi import APIRouter, Depends

from ui.backend.dependencies import get_skill_service
from ui.backend.services.skill_service import SkillService

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("")
async def list_skills(
    service: SkillService = Depends(get_skill_service),
):
    """List all skill categories with summary statistics."""
    return {
        "success": True,
        "data": service.get_summary().model_dump(),
    }


@router.get("/{category}")
async def get_skill_category(
    category: str,
    service: SkillService = Depends(get_skill_service),
):
    """Get all skills in a specific category."""
    return {
        "success": True,
        "data": service.get_category(category).model_dump(),
    }
