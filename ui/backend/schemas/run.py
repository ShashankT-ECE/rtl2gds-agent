"""
run.py — Job run request and response schemas.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class RunRequest(BaseModel):
    """POST /api/run request body — start a pipeline job."""
    benchmark: str = Field(
        ...,
        description="Benchmark name, e.g. 'alu_8bit'",
        examples=["alu_8bit", "uart_tx"],
    )
    pipeline_version: Literal["v1", "v2", "v3"] = "v1"
    max_iterations: int = Field(default=5, ge=1, le=20)
    use_reference_rtl: bool = Field(
        default=False, description="Skip LLM RTL generation, use reference RTL if available"
    )
    use_reference_tb: bool = Field(
        default=False, description="Skip LLM testbench generation, use reference TB if available"
    )

    @field_validator("benchmark")
    @classmethod
    def benchmark_must_be_safe(cls, v: str) -> str:
        if not v or "/" in v or ".." in v or "\\" in v:
            raise ValueError("Invalid benchmark name")
        return v.strip()


class StageInfo(BaseModel):
    """Status of one pipeline stage."""
    name: str = Field(..., description="Stage name, e.g. 'rtl_gen', 'simulation'")
    status: Literal["pending", "running", "completed", "failed", "skipped"] = "pending"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    elapsed_ms: Optional[float] = None


class RunResponse(BaseModel):
    """Job status — returned by POST /api/run, GET /api/run/{job_id}."""
    job_id: str
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    benchmark: str
    pipeline_version: str
    created_at: str = Field(..., description="ISO 8601")
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    elapsed_seconds: Optional[float] = None
    current_stage: str = "queued"
    stages: list[StageInfo] = []
    iteration: int = 0
    sim_passed: Optional[bool] = None
    timing_met: Optional[bool] = None
    drc_passed: Optional[bool] = None
    progress_pct: float = 0.0
    error_message: Optional[str] = None
    event_count: int = 0


class RunListResponse(BaseModel):
    """Returned by GET /api/run — list of recent jobs."""
    jobs: list[RunResponse]
    total: int
