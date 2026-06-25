"""
run.py — Pipeline job lifecycle endpoints.

POST   /api/run           — start a new pipeline job
GET    /api/run           — list recent jobs
GET    /api/run/{job_id}  — get job status
POST   /api/run/{job_id}/cancel — request cancellation
"""

import asyncio
import concurrent.futures
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from ui.backend.config import settings
from ui.backend.dependencies import get_job_manager
from ui.backend.models.job import Job, JobStatus
from ui.backend.schemas.run import RunRequest, RunListResponse, RunResponse, StageInfo
from ui.backend.services.job_manager import JobManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/run", tags=["run"])


def _job_to_response(job: Job) -> RunResponse:
    """Convert internal Job model to API response."""
    stages = [
        StageInfo(
            name=sr.name,
            status=sr.status,
            started_at=datetime.fromtimestamp(sr.started_at, tz=timezone.utc).isoformat()
            if sr.started_at else None,
            completed_at=datetime.fromtimestamp(sr.completed_at, tz=timezone.utc).isoformat()
            if sr.completed_at else None,
            elapsed_ms=sr.elapsed_ms,
        )
        for sr in job.stages.values()
    ]

    return RunResponse(
        job_id=job.job_id,
        status=job.status.value,
        benchmark=job.benchmark,
        pipeline_version=job.pipeline_version,
        created_at=datetime.fromtimestamp(job.created_at, tz=timezone.utc).isoformat(),
        started_at=datetime.fromtimestamp(job.started_at, tz=timezone.utc).isoformat()
        if job.started_at else None,
        completed_at=datetime.fromtimestamp(job.completed_at, tz=timezone.utc).isoformat()
        if job.completed_at else None,
        elapsed_seconds=round(job.elapsed_seconds, 3) if job.elapsed_seconds else None,
        current_stage=job.current_stage,
        stages=stages,
        iteration=job.iteration,
        sim_passed=job.sim_passed,
        timing_met=job.timing_met,
        drc_passed=job.drc_passed,
        progress_pct=job.progress_pct,
        error_message=job.error_message,
        event_count=job.event_count,
    )


@router.post("", status_code=202)
async def start_run(
    request: RunRequest,
    background_tasks: BackgroundTasks,
    job_manager: JobManager = Depends(get_job_manager),
):
    """Start a new pipeline job. Returns immediately with 202 Accepted.

    The job runs in a background thread. Use GET /api/run/{job_id}
    to poll status, or GET /api/run/stream?job_id={job_id} for SSE.
    """
    job = await job_manager.create_job(
        benchmark=request.benchmark,
        pipeline_version=request.pipeline_version,
        max_iterations=request.max_iterations,
        use_reference_rtl=request.use_reference_rtl,
        use_reference_tb=request.use_reference_tb,
    )

    # Schedule pipeline execution as a background task
    background_tasks.add_task(
        _execute_pipeline_in_background, job.job_id, job_manager
    )

    return {
        "success": True,
        "data": _job_to_response(job).model_dump(),
    }


@router.get("")
async def list_runs(
    status: str = Query(default=None, description="Filter by status"),
    limit: int = Query(default=50, le=100),
    job_manager: JobManager = Depends(get_job_manager),
):
    """List recent pipeline jobs."""
    jobs = await job_manager.list_jobs(status_filter=status, limit=limit)
    return {
        "success": True,
        "data": RunListResponse(
            jobs=[_job_to_response(j) for j in jobs],
            total=len(jobs),
        ).model_dump(),
    }


@router.get("/{job_id}")
async def get_run(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager),
):
    """Get status of a specific job."""
    job = await job_manager.get_job(job_id)
    return {
        "success": True,
        "data": _job_to_response(job).model_dump(),
    }


@router.post("/{job_id}/cancel")
async def cancel_run(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager),
):
    """Request cancellation of a running job.

    Cancellation is cooperative — the job will stop at the next
    stage boundary. Long-running LLM calls may continue until completion.
    """
    job = await job_manager.cancel_job(job_id)
    return {
        "success": True,
        "data": _job_to_response(job).model_dump(),
    }


async def _execute_pipeline_in_background(job_id: str, job_manager: JobManager) -> None:
    """Run the pipeline adapter in a thread-pool executor.

    This function runs on the async event loop but dispatches the
    synchronous pipeline to a thread so it doesn't block the server.
    """
    from ui.backend.main import _app_state
    from ui.backend.services.event_bus import EventBus

    event_bus: EventBus = _app_state["event_bus"]

    # Resolve the right adapter
    if settings.PIPELINE_MODE == "mock":
        from ui.backend.adapters.pipeline_mock import MockPipelineAdapter as Adapter
    else:
        from ui.backend.adapters.pipeline import PipelineAdapter as Adapter

    job = await job_manager.get_job_optional(job_id)
    if job is None:
        return

    adapter = Adapter(
        event_bus=event_bus,
        check_cancelled=lambda: _check_cancelled_sync(job_id, job_manager),
    )

    # Run the synchronous pipeline in a thread pool
    loop = asyncio.get_running_loop()
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            await loop.run_in_executor(
                pool,
                adapter.run,
                job_id,
                job.benchmark,
                job.pipeline_version,
                job.max_iterations,
                job.use_reference_rtl,
                job.use_reference_tb,
            )
    except Exception:
        logger.exception("Pipeline job %s failed", job_id)


def _check_cancelled_sync(job_id: str, job_manager: JobManager) -> bool:
    """Synchronous cancellation check for the pipeline thread."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(
                job_manager.is_cancelled(job_id), loop
            )
            return future.result(timeout=1)
    except Exception:
        pass
    return False
