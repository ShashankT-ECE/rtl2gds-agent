"""
health.py — Health-check response schemas.
"""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Returned by GET /health — indicates server liveness."""
    status: str = "ok"
    version: str = Field(..., description="Backend version from __version__")
    api_version: str = Field(default="v1", description="API version identifier")
