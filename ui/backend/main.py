"""
main.py — FastAPI application factory and entry point.

Creates a FastAPI app with:
  - Structured logging
  - CORS middleware
  - Centralized exception handlers
  - All routers mounted
  - Static file hosting for ui/frontend/
  - Singleton services via app.state (not global variables)
  - Lifespan-based startup/shutdown

Run with:
    python -m ui.backend.main
or:
    uvicorn ui.backend.main:app --reload
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from ui.backend import __version__
from ui.backend.config import settings
from ui.backend.exceptions import register_handlers
from ui.backend.services.benchmark_service import BenchmarkService
from ui.backend.services.event_bus import EventBus
from ui.backend.services.job_manager import JobManager
from ui.backend.services.logging_service import LoggingService
from ui.backend.services.skill_service import SkillService
from ui.backend.services.sse_adapter import SSEManager

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level state (for background task access when Depends() is unavailable)
# ---------------------------------------------------------------------------

_app_state: dict = {}


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create all singleton services and wire them together."""
    logger.info("=" * 60)
    logger.info("RTL2GDS Agent — Web UI Backend v%s", __version__)
    logger.info("Pipeline mode: %s", settings.PIPELINE_MODE)
    logger.info("=" * 60)

    import asyncio

    # Core infrastructure
    event_bus = EventBus()

    # Services (subscribe to event_bus where needed)
    job_manager = JobManager(event_bus=event_bus)
    sse_manager = SSEManager(event_bus=event_bus)
    logging_service = LoggingService(event_bus=event_bus)
    benchmark_service = BenchmarkService()
    skill_service = SkillService()

    # Bind event bus to the running asyncio loop
    event_bus.attach_loop(asyncio.get_running_loop())

    # Store on app.state for Depends() access
    app.state.event_bus = event_bus
    app.state.job_manager = job_manager
    app.state.sse_manager = sse_manager
    app.state.logging_service = logging_service
    app.state.benchmark_service = benchmark_service
    app.state.skill_service = skill_service

    # Also expose module-level for background tasks
    _app_state["event_bus"] = event_bus
    _app_state["job_manager"] = job_manager

    logger.info(
        "Services ready — %d benchmarks, %d skills",
        benchmark_service.list_all().total,
        skill_service.total_skills(),
    )

    yield

    logger.info("Shutting down...")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Build and return a fully configured FastAPI application."""
    app = FastAPI(
        title="RTL2GDS Agent API",
        description="REST API for the AI-driven RTL-to-GDSII pipeline",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS — allow all origins for Phase 1 (local dev)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Centralized exception handling (converts AppError→ErrorResponse)
    register_handlers(app)

    # Mount routers
    from ui.backend.routers import health, benchmarks, skills, run, events

    app.include_router(health.router)
    app.include_router(benchmarks.router)
    app.include_router(skills.router)
    # IMPORTANT: events router must come before run router so that
    # GET /api/run/stream matches the specific path, not /api/run/{job_id}
    app.include_router(events.router)
    app.include_router(run.router)

    # Static file hosting (ui/frontend/)
    static_dir = settings.STATIC_DIR
    static_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    logger.info("App created — %d routes registered", len(app.routes))
    return app


# Module-level app instance (used by uvicorn)
app = create_app()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "ui.backend.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
