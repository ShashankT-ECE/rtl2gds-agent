"""
job_manager.py — In-memory job tracking service.

Creates, reads, updates, and lists pipeline jobs.
Subscribes to EventBus to update job state from events (single source of truth).
Thread-safe via asyncio.Lock for concurrent reads from SSE/status endpoints.
"""

import asyncio
import logging
from typing import Optional

from ui.backend.config import settings
from ui.backend.exceptions import (
    ConflictError,
    JobNotFoundError,
    ValidationError,
)
from ui.backend.models.job import Job, JobStatus, StageRecord
from ui.backend.schemas.event import EventType, PipelineEvent, Severity
from ui.backend.services.event_bus import EventBus

logger = logging.getLogger(__name__)

# Stages shared by all pipeline versions.
_STAGE_ORDER = [
    "spec_parser",
    "verification_planner",
    "rtl_gen",
    "testbench",
    "simulation",
    "log_analysis",
    "fix",
    "synthesis",
    "sta",
    "timing_opt",
    "openlane",
    "drc",
]


class JobManager:
    """Thread-safe in-memory job store.

    Single writer (the pipeline adapter via events), multiple readers
    (SSE connections, status API). Lock protects only dict mutations,
    not the full pipeline execution.
    """

    def __init__(self, event_bus: EventBus) -> None:
        self._jobs: dict[str, Job] = {}
        self._events: dict[str, list[PipelineEvent]] = {}
        self._lock = asyncio.Lock()
        self._event_bus = event_bus

        # Subscribe to event bus for automatic state updates
        self._event_bus.subscribe(self._on_event)

    # ---- Event handler (called from EventBus on the async loop) -----------

    async def _on_event(self, event: PipelineEvent) -> None:
        """React to a pipeline event — update job state."""
        job_id = event.job_id

        # Store event
        async with self._lock:
            if job_id not in self._events:
                self._events[job_id] = []
            self._events[job_id].append(event)

            job = self._jobs.get(job_id)
            if job is None:
                return
            job.event_count = len(self._events[job_id])

        # Update job state based on event type
        evtype = event.event_type

        if evtype == EventType.JOB_STARTED:
            async with self._lock:
                if job and job.can_transition_to(JobStatus.RUNNING):
                    job.status = JobStatus.RUNNING
                    job.started_at = __import__("time").time()
                    job.current_stage = "running"

        elif evtype == EventType.STAGE_STARTED:
            stage_name = event.stage or event.payload.get("stage", "")
            async with self._lock:
                if job:
                    job.current_stage = stage_name
                    sr = job.stages.setdefault(stage_name, StageRecord(name=stage_name))
                    sr.start(__import__("time").time())

        elif evtype == EventType.STAGE_COMPLETED:
            stage_name = event.stage or event.payload.get("stage", "")
            async with self._lock:
                if job:
                    sr = job.stages.setdefault(stage_name, StageRecord(name=stage_name))
                    sr.complete(__import__("time").time())

        elif evtype == EventType.STAGE_FAILED:
            stage_name = event.stage or event.payload.get("stage", "")
            async with self._lock:
                if job:
                    sr = job.stages.setdefault(stage_name, StageRecord(name=stage_name))
                    sr.fail(__import__("time").time())

        elif evtype == EventType.SIMULATION_RESULT:
            async with self._lock:
                if job:
                    job.sim_passed = event.payload.get("passed", False)

        elif evtype == EventType.STA_RESULT:
            async with self._lock:
                if job:
                    job.timing_met = event.payload.get("timing_met", False)

        elif evtype == EventType.DRC_RESULT:
            async with self._lock:
                if job:
                    job.drc_passed = event.payload.get("drc_passed", False)

        elif evtype == EventType.JOB_COMPLETED:
            async with self._lock:
                if job and job.can_transition_to(JobStatus.COMPLETED):
                    job.status = JobStatus.COMPLETED
                    job.completed_at = __import__("time").time()
                    job.progress_pct = 100.0

        elif evtype == EventType.JOB_FAILED:
            async with self._lock:
                if job and job.can_transition_to(JobStatus.FAILED):
                    job.status = JobStatus.FAILED
                    job.completed_at = __import__("time").time()
                    job.error_message = event.message

        elif evtype == EventType.JOB_CANCELLED:
            async with self._lock:
                if job and job.status != JobStatus.CANCELLED:
                    job.status = JobStatus.CANCELLED
                    job.completed_at = __import__("time").time()

        elif evtype == EventType.FIX_ATTEMPT:
            async with self._lock:
                if job:
                    job.iteration = event.iteration or job.iteration + 1

        elif evtype == EventType.PROGRESS:
            async with self._lock:
                if job:
                    job.progress_pct = event.payload.get("percent", job.progress_pct)

        # Evict oldest jobs if over limit
        await self._maybe_evict()

    # ---- Public API -------------------------------------------------------

    async def create_job(self, benchmark: str, pipeline_version: str,
                         max_iterations: int = 5, use_reference_rtl: bool = False,
                         use_reference_tb: bool = False) -> Job:
        """Create a new queued job. Validates benchmark name."""
        from pathlib import Path
        spec_path = settings.BENCHMARKS_DIR / benchmark / "spec.txt"
        if not spec_path.exists():
            raise ValidationError(f"Benchmark '{benchmark}' not found")

        # Check concurrency limit
        async with self._lock:
            active = sum(1 for j in self._jobs.values() if j.status.is_active)
            if active >= settings.MAX_CONCURRENT_JOBS:
                raise ConflictError(
                    f"Max concurrent jobs ({settings.MAX_CONCURRENT_JOBS}) reached. "
                    "Wait for the current job to finish."
                )

            # Check for duplicate running job on same benchmark
            for j in self._jobs.values():
                if j.benchmark == benchmark and j.status.is_active:
                    raise ConflictError(
                        f"A job for '{benchmark}' is already {j.status.value} "
                        f"(job_id={j.job_id})"
                    )

            job = Job(
                benchmark=benchmark,
                pipeline_version=pipeline_version,
                max_iterations=max_iterations,
                use_reference_rtl=use_reference_rtl,
                use_reference_tb=use_reference_tb,
            )
            self._jobs[job.job_id] = job
            self._events[job.job_id] = []
            logger.info("Job %s created for benchmark=%s v=%s",
                        job.job_id, benchmark, pipeline_version)
            return job

    async def get_job(self, job_id: str) -> Job:
        """Get a job by ID. Raises JobNotFoundError if missing."""
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise JobNotFoundError(f"Job '{job_id}' not found")
            return job

    async def get_job_optional(self, job_id: str) -> Optional[Job]:
        """Get a job by ID, returning None if missing (no exception)."""
        async with self._lock:
            return self._jobs.get(job_id)

    async def list_jobs(self, status_filter: Optional[str] = None,
                        limit: int = 50) -> list[Job]:
        """List recent jobs, optionally filtered by status."""
        async with self._lock:
            jobs = list(self._jobs.values())
            if status_filter:
                jobs = [j for j in jobs if j.status.value == status_filter]
            # Most recent first
            jobs.sort(key=lambda j: j.created_at, reverse=True)
            return jobs[:limit]

    async def cancel_job(self, job_id: str) -> Job:
        """Request cancellation. Sets the cooperative flag; pipeline checks it."""
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise JobNotFoundError(f"Job '{job_id}' not found")
            if job.status.is_terminal:
                raise ConflictError(f"Job '{job_id}' is already {job.status.value}")
            job.cancel_requested = True
            logger.info("Cancellation requested for job %s", job_id)
            return job

    async def is_cancelled(self, job_id: str) -> bool:
        """Check if cancellation has been requested (called from pipeline thread)."""
        # No lock needed for a simple boolean read
        job = self._jobs.get(job_id)
        return job.cancel_requested if job else False

    async def get_events(self, job_id: str, after_seq: int = 0) -> list[PipelineEvent]:
        """Get all events for a job after a given sequence number.

        Used by SSE endpoint to replay events after client reconnect.
        """
        async with self._lock:
            if job_id not in self._jobs:
                raise JobNotFoundError(f"Job '{job_id}' not found")
            events = self._events.get(job_id, [])
            if after_seq == 0:
                return list(events)
            return [e for e in events if e.sequence_num > after_seq]

    async def get_stats(self) -> dict[str, int]:
        """Get aggregate job counts for the status endpoint."""
        async with self._lock:
            counts = {"queued": 0, "running": 0, "completed": 0, "failed": 0, "cancelled": 0}
            for j in self._jobs.values():
                counts[j.status.value] += 1
            return counts

    # ---- Internal ---------------------------------------------------------

    async def _maybe_evict(self) -> None:
        """Evict oldest completed/failed/cancelled jobs if over memory limit."""
        async with self._lock:
            terminal = [j for j in self._jobs.values() if j.status.is_terminal]
            if len(terminal) > settings.MAX_JOBS_IN_MEMORY:
                # Sort oldest first
                terminal.sort(key=lambda j: j.completed_at or j.created_at)
                to_remove = terminal[:len(terminal) - settings.MAX_JOBS_IN_MEMORY]
                for j in to_remove:
                    del self._jobs[j.job_id]
                    self._events.pop(j.job_id, None)
                if to_remove:
                    logger.info("Evicted %d old jobs from memory", len(to_remove))
