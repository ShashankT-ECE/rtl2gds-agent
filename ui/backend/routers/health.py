"""
health.py — Liveness and system-status endpoints.
"""

import time

from fastapi import APIRouter, Depends

from ui.backend import __version__
from ui.backend.dependencies import get_benchmark_service, get_job_manager, get_skill_service
from ui.backend.schemas.health import HealthResponse
from ui.backend.schemas.status import SystemStatusResponse, VersionInfo
from ui.backend.services.benchmark_service import BenchmarkService
from ui.backend.services.job_manager import JobManager
from ui.backend.services.skill_service import SkillService

router = APIRouter(tags=["health"])

_START_TIME = time.time()


def _check_version_availability() -> VersionInfo:
    """Detect which pipeline versions are importable."""
    v2_available = False
    v3_available = False
    try:
        from v2_verification.pipeline import run_v2_pipeline  # noqa: F401
        v2_available = True
    except ImportError:
        pass
    try:
        from v3_physical.pipeline import run_v3_pipeline  # noqa: F401
        v3_available = True
    except ImportError:
        pass
    return VersionInfo(v1_available=True, v2_available=v2_available, v3_available=v3_available)


@router.get("/health")
async def health_check():
    """Liveness check — returns 200 if the server is running."""
    return {
        "success": True,
        "data": HealthResponse(
            status="ok",
            version=__version__,
            api_version="v1",
        ).model_dump(),
    }


@router.get("/status")
async def system_status(
    job_manager: JobManager = Depends(get_job_manager),
    skill_service: SkillService = Depends(get_skill_service),
    benchmark_service: BenchmarkService = Depends(get_benchmark_service),
):
    """System-wide status — active jobs, skills, version availability."""
    from ui.backend.config import settings

    stats = await job_manager.get_stats()
    benchmarks = benchmark_service.list_all()

    return {
        "success": True,
        "data": SystemStatusResponse(
            active_jobs=stats["running"],
            completed_jobs=stats["completed"],
            failed_jobs=stats["failed"],
            queued_jobs=stats["queued"],
            total_skills=skill_service.total_skills(),
            benchmark_count=benchmarks.total,
            versions=_check_version_availability(),
            provider="deepseek",
            pipeline_mode=settings.PIPELINE_MODE,
        ).model_dump(),
    }
