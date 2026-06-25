"""
common.py — Shared Pydantic models for API responses.

All endpoints return either SuccessResponse or ErrorResponse.
Never return raw dicts from API routes.
"""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Structured error information — never expose raw stack traces."""
    code: str = Field(..., description="Machine-readable error code, e.g. 'JOB_NOT_FOUND'")
    message: str = Field(..., description="Human-readable error description")
    details: Optional[dict[str, Any]] = Field(
        default=None, description="Optional additional context (sanitized)"
    )


class ErrorResponse(BaseModel):
    """Standard error envelope returned for all API errors."""
    success: bool = False
    error: ErrorDetail


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success envelope — all data is nested under ``data``."""
    success: bool = True
    data: T


class PaginationMeta(BaseModel):
    """Metadata for paginated list responses."""
    total: int
    limit: int
    offset: int
