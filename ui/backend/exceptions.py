"""
exceptions.py — Centralized exception handling.

All custom exceptions are defined here.
FastAPI exception handlers convert them into consistent ErrorResponse JSON.
Never expose raw Python tracebacks in API responses.
"""

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from ui.backend.schemas.common import ErrorDetail, ErrorResponse


# ---------------------------------------------------------------------------
# Custom exception hierarchy
# ---------------------------------------------------------------------------

class AppError(Exception):
    """Base exception for application-level errors.

    All subclasses must provide `status_code` and `error_code`.
    """
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details


class NotFoundError(AppError):
    """Resource not found — maps to 404."""
    status_code = 404
    error_code = "NOT_FOUND"


class JobNotFoundError(NotFoundError):
    """Specific job_id not found."""
    error_code = "JOB_NOT_FOUND"


class BenchmarkNotFoundError(NotFoundError):
    """Benchmark name not found."""
    error_code = "BENCHMARK_NOT_FOUND"


class SkillCategoryNotFoundError(NotFoundError):
    """Skill category not found."""
    error_code = "SKILL_CATEGORY_NOT_FOUND"


class ValidationError(AppError):
    """Invalid input — maps to 422."""
    status_code = 422
    error_code = "VALIDATION_ERROR"


class ConflictError(AppError):
    """Resource conflict — maps to 409 (e.g. job already running)."""
    status_code = 409
    error_code = "CONFLICT"


class PipelineError(AppError):
    """Pipeline execution failure — maps to 500."""
    status_code = 500
    error_code = "PIPELINE_ERROR"


class ServiceUnavailableError(AppError):
    """Service temporarily unavailable — maps to 503."""
    status_code = 503
    error_code = "SERVICE_UNAVAILABLE"


# ---------------------------------------------------------------------------
# FastAPI exception handlers
# ---------------------------------------------------------------------------

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Convert AppError subclasses into consistent ErrorResponse."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(
                code=exc.error_code,
                message=exc.message,
                details=exc.details,
            )
        ).model_dump(),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unexpected exceptions — never expose stack traces."""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred. Check server logs for details.",
            )
        ).model_dump(),
    )


def register_handlers(app):
    """Register all exception handlers on a FastAPI application instance."""
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
