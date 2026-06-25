"""
dependencies.py — FastAPI dependency injection for singleton services.

All services live on app.state (populated during lifespan).
These dependency functions retrieve them — FastAPI calls them
automatically when a route handler parameter uses Depends().
"""

from fastapi import Request

from ui.backend.services.benchmark_service import BenchmarkService
from ui.backend.services.event_bus import EventBus
from ui.backend.services.job_manager import JobManager
from ui.backend.services.skill_service import SkillService
from ui.backend.services.sse_adapter import SSEManager


def _get_service(request: Request, key: str):
    """Generic getter from app.state. Raises AttributeError if key missing."""
    service = getattr(request.app.state, key, None)
    if service is None:
        raise RuntimeError(
            f"Service '{key}' not initialized. Check that lifespan() ran."
        )
    return service


def get_job_manager(request: Request) -> JobManager:
    return _get_service(request, "job_manager")


def get_event_bus(request: Request) -> EventBus:
    return _get_service(request, "event_bus")


def get_sse_manager(request: Request) -> SSEManager:
    return _get_service(request, "sse_manager")


def get_benchmark_service(request: Request) -> BenchmarkService:
    return _get_service(request, "benchmark_service")


def get_skill_service(request: Request) -> SkillService:
    return _get_service(request, "skill_service")
