"""
job.py — Internal Job data model and state machine.

This is a plain dataclass, NOT a SQLAlchemy / Pydantic model.
Jobs are stored in-memory by JobManager. API serialization goes
through schemas/run.py:RunResponse, never through this module directly.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from uuid import uuid4


class JobStatus(str, Enum):
    """Job lifecycle states.

    Transitions:
        QUEUED → RUNNING → COMPLETED
        QUEUED → CANCELLED
        RUNNING → FAILED
        RUNNING → CANCELLED (cooperative)
    """
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        """True if the job will never transition again."""
        return self in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED)

    @property
    def is_active(self) -> bool:
        """True if the job is consuming resources."""
        return self == JobStatus.RUNNING


@dataclass
class StageRecord:
    """Per-stage timing and status within a job."""
    name: str
    status: str = "pending"  # pending | running | completed | failed | skipped
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    elapsed_ms: Optional[float] = None

    def start(self, now: float) -> None:
        self.status = "running"
        self.started_at = now

    def complete(self, now: float) -> None:
        self.status = "completed"
        self.completed_at = now
        if self.started_at:
            self.elapsed_ms = (now - self.started_at) * 1000

    def fail(self, now: float) -> None:
        self.status = "failed"
        self.completed_at = now
        if self.started_at:
            self.elapsed_ms = (now - self.started_at) * 1000

    def skip(self, now: float) -> None:
        self.status = "skipped"
        self.completed_at = now


@dataclass
class Job:
    """Internal representation of a single pipeline run.

    Fields mirror PipelineState from v1_core/agents/orchestrator.py
    but are intentionally kept minimal — only what the UI needs.
    """
    # Identity
    job_id: str = field(default_factory=lambda: str(uuid4())[:8])
    benchmark: str = ""
    pipeline_version: str = "v1"

    # Lifecycle
    status: JobStatus = JobStatus.QUEUED
    created_at: float = field(default_factory=__import__("time").time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    # Progress
    current_stage: str = "queued"
    stages: dict[str, StageRecord] = field(default_factory=dict)
    progress_pct: float = 0.0

    # Iteration tracking
    iteration: int = 0
    max_iterations: int = 5

    # Results
    sim_passed: Optional[bool] = None
    timing_met: Optional[bool] = None
    drc_passed: Optional[bool] = None
    error_message: Optional[str] = None

    # Request params
    use_reference_rtl: bool = False
    use_reference_tb: bool = False

    # Control
    cancel_requested: bool = False

    # Stats
    event_count: int = 0

    @property
    def elapsed_seconds(self) -> Optional[float]:
        """Wall-clock duration from start to now (or completion)."""
        if self.started_at is None:
            return None
        end = self.completed_at or __import__("time").time()
        return end - self.started_at

    def can_transition_to(self, target: JobStatus) -> bool:
        """Validate state machine transitions."""
        valid = {
            JobStatus.QUEUED: {JobStatus.RUNNING, JobStatus.CANCELLED},
            JobStatus.RUNNING: {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED},
        }
        return target in valid.get(self.status, set())

    def stage_names(self) -> list[str]:
        """Ordered list of expected stages for this pipeline version."""
        base = ["spec_parser", "verification_planner"]
        if not self.use_reference_rtl:
            base.append("rtl_gen")
        if not self.use_reference_tb:
            base.append("testbench")
        base.append("simulation")
        if self.pipeline_version in ("v2", "v3"):
            base.extend(["synthesis", "sta"])
        if self.pipeline_version == "v3":
            base.extend(["openlane", "drc"])
        return base
