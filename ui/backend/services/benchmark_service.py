"""
benchmark_service.py — Read benchmark metadata from the benchmarks/ directory.

No caching needed — directories are small and read at request time.
Data is presented through Pydantic schemas, never returned as raw dicts.
"""

import logging
from pathlib import Path
from typing import Optional

from ui.backend.config import settings
from ui.backend.exceptions import BenchmarkNotFoundError
from ui.backend.schemas.benchmark import BenchmarkBug, BenchmarkInfo, BenchmarkListResponse

logger = logging.getLogger(__name__)

# Simple category guess based on keywords in the design name.
_NAME_TO_CATEGORY: dict[str, str] = {
    "alu": "combinational",
    "sync_fifo": "fifo",
    "fsm": "fsm",
    "uart": "combinational",
    "apb": "axi",
    "axi": "axi",
    "spi": "combinational",
    "i2c": "combinational",
}


class BenchmarkService:
    """Reads benchmark metadata from disk — no mutation, no caching."""

    def __init__(self) -> None:
        self._dir = settings.BENCHMARKS_DIR

    def _guess_category(self, name: str) -> str:
        """Infer a skill-category from the benchmark name."""
        for key, cat in _NAME_TO_CATEGORY.items():
            if key in name.lower():
                return cat
        return "combinational"

    def list_all(self) -> BenchmarkListResponse:
        """Return all benchmark designs."""
        results: list[BenchmarkInfo] = []
        if not self._dir.exists():
            logger.warning("Benchmarks directory not found: %s", self._dir)
            return BenchmarkListResponse(benchmarks=[], total=0)

        for entry in sorted(self._dir.iterdir()):
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            info = self._scan_benchmark(entry)
            results.append(info)

        return BenchmarkListResponse(benchmarks=results, total=len(results))

    def get_one(self, name: str) -> BenchmarkInfo:
        """Return metadata for a single benchmark."""
        entry = self._dir / name
        if not entry.is_dir():
            raise BenchmarkNotFoundError(f"Benchmark '{name}' not found")
        return self._scan_benchmark(entry)

    def _scan_benchmark(self, entry: Path) -> BenchmarkInfo:
        """Read one benchmark directory."""
        spec_path = entry / "spec.txt"
        ref_rtl = entry / "reference_rtl.v"
        ref_tb = entry / "reference_tb.py"
        bugs_dir = entry / "bugs"

        # Spec preview
        spec_preview = ""
        if spec_path.exists():
            spec_preview = spec_path.read_text()[:200].strip()

        # Bug variants
        bugs: list[BenchmarkBug] = []
        has_bugs = bugs_dir.exists() and bugs_dir.is_dir()
        if has_bugs:
            for bug_file in sorted(bugs_dir.iterdir()):
                if bug_file.suffix == ".v":
                    bugs.append(BenchmarkBug(
                        bug_id=bug_file.stem,
                        description=f"Bug variant: {bug_file.stem}",
                    ))

        return BenchmarkInfo(
            name=entry.name,
            spec_preview=spec_preview,
            has_reference_rtl=ref_rtl.exists(),
            has_reference_tb=ref_tb.exists(),
            has_bugs=has_bugs,
            bug_count=len(bugs),
            category_guess=self._guess_category(entry.name),
        )
