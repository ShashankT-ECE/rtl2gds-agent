"""
benchmark.py — Benchmark metadata response schemas.

Data is read from the benchmarks/ directory at request time.
No caching — directories are small and rarely change.
"""

from typing import Optional

from pydantic import BaseModel, Field


class BenchmarkBug(BaseModel):
    """Summary of a single injected bug variant."""
    bug_id: str = Field(..., description="e.g. 'bug_001_wrong_opcode'")
    description: str = Field(default="", description="Derived from filename or bug manifest")


class BenchmarkInfo(BaseModel):
    """Metadata for one benchmark design."""
    name: str = Field(..., description="Directory name, e.g. 'alu_8bit'")
    spec_preview: str = Field(
        default="", description="First 200 characters of spec.txt"
    )
    has_reference_rtl: bool = False
    has_reference_tb: bool = False
    has_bugs: bool = False
    bug_count: int = 0
    category_guess: Optional[str] = Field(
        default=None,
        description="Inferred category: combinational, fsm, fifo, axi, or timing",
    )


class BenchmarkListResponse(BaseModel):
    """Returned by GET /api/benchmarks."""
    benchmarks: list[BenchmarkInfo]
    total: int
