"""
status.py — System-wide status response.
"""

from pydantic import BaseModel, Field


class VersionInfo(BaseModel):
    """Which pipeline versions are available."""
    v1_available: bool = True
    v2_available: bool = Field(
        default=False, description="True if V2 synthesis/STA agents are importable"
    )
    v3_available: bool = Field(
        default=False, description="True if V3 physical design agents are importable"
    )


class SystemStatusResponse(BaseModel):
    """Returned by GET /status — snapshot of system health."""
    active_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    queued_jobs: int = 0
    total_skills: int = Field(..., description="Sum of skills across all categories")
    benchmark_count: int = Field(..., description="Number of benchmark directories found")
    versions: VersionInfo = Field(default_factory=VersionInfo)
    provider: str = Field(default="deepseek", description="LLM_PROVIDER env value")
    pipeline_mode: str = Field(default="mock", description="Current PIPELINE_MODE setting")
