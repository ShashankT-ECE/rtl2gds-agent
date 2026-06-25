"""
event.py — Structured pipeline event schemas.

This is the core of the UI architecture. Every observable pipeline
occurrence is modeled as a typed event with consistent fields.
Events flow: Pipeline → EventBus → SSE Adapter → Frontend.

Never stream raw console output — always emit typed events.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """All recognised pipeline event types.

    Keep this extensible — add new types as the pipeline evolves.
    """
    # ---- Job lifecycle ----
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    JOB_CANCELLED = "job_cancelled"

    # ---- Stage transitions ----
    STAGE_STARTED = "stage_started"
    STAGE_COMPLETED = "stage_completed"
    STAGE_FAILED = "stage_failed"

    # ---- Agent activity ----
    AGENT_LOG = "agent_log"
    LLM_CALL_START = "llm_call_start"
    LLM_CALL_END = "llm_call_end"
    TOOL_CALL = "tool_call"

    # ---- Fix loop ----
    FIX_ATTEMPT = "fix_attempt"
    SKILL_RETRIEVED = "skill_retrieved"
    SKILL_STORED = "skill_stored"
    CONVERGENCE_WARNING = "convergence_warning"

    # ---- Results ----
    SIMULATION_RESULT = "simulation_result"
    SYNTHESIS_RESULT = "synthesis_result"
    STA_RESULT = "sta_result"
    DRC_RESULT = "drc_result"

    # ---- System ----
    HEARTBEAT = "heartbeat"
    PROGRESS = "progress"


class Severity(str, Enum):
    """Standard severity levels for events."""
    DEBUG = "debug"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class PipelineEvent(BaseModel):
    """A single structured event emitted by the pipeline.

    Every event must have all required fields populated.
    The payload dict carries event-type-specific structured data.
    """
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    job_id: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    event_type: EventType
    stage: Optional[str] = Field(default=None, description="Current pipeline stage name")
    message: str = Field(..., description="Human-readable description")
    severity: Severity = Severity.INFO
    payload: dict[str, Any] = Field(
        default_factory=dict, description="Structured data specific to this event_type"
    )
    elapsed_time: Optional[float] = Field(
        default=None, description="Seconds since job start"
    )
    iteration: Optional[int] = Field(default=None, description="Current fix-loop iteration")
    sequence_num: int = Field(..., description="Monotonically increasing per job")

    def sse_data(self) -> str:
        """Serialize to JSON string for SSE ``data:`` field."""
        return self.model_dump_json()

    @classmethod
    def heartbeat(cls, job_id: str, seq: int) -> "PipelineEvent":
        return cls(
            job_id=job_id,
            event_type=EventType.HEARTBEAT,
            message="heartbeat",
            sequence_num=seq,
        )
