"""
benchmarks.py — Benchmark listing and detail endpoints.
"""

from fastapi import APIRouter, Depends

from ui.backend.dependencies import get_benchmark_service
from ui.backend.services.benchmark_service import BenchmarkService

router = APIRouter(prefix="/api/benchmarks", tags=["benchmarks"])


@router.get("")
async def list_benchmarks(
    service: BenchmarkService = Depends(get_benchmark_service),
):
    """List all available benchmark designs with metadata."""
    return {
        "success": True,
        "data": service.list_all().model_dump(),
    }


@router.get("/{name}")
async def get_benchmark(
    name: str,
    service: BenchmarkService = Depends(get_benchmark_service),
):
    """Get detailed metadata for a specific benchmark."""
    return {
        "success": True,
        "data": service.get_one(name).model_dump(),
    }
