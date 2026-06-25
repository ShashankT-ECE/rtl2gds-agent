"""
pipeline.py — Real pipeline adapter wrapping the frozen RTL2GDS pipeline.

This adapter:
  1. Calls existing run_pipeline() / run_v2_pipeline() / run_v3_pipeline()
  2. Emits structured events from the final PipelineState
  3. NEVER modifies the frozen pipeline source code

For V3, we can optionally intercept agent nodes since build_v3_pipeline()
is a public function. For V1/V2, the run_pipeline()/run_v2_pipeline()
entry points don't expose the graph for interception, so we get
coarse-grained events (job_started → job_completed/failed) from the
final state.

PIPELINE_MODE=real gates usage of this adapter.
"""

import logging
import time
from pathlib import Path
from typing import Any, Callable, Optional

from ui.backend.config import settings
from ui.backend.schemas.event import EventType, PipelineEvent, Severity
from ui.backend.services.event_bus import EventBus

logger = logging.getLogger(__name__)


class PipelineAdapter:
    """Wraps the frozen LangGraph pipelines as an event-emitting adapter.

    Does not modify v1_core/, v2_verification/, or v3_physical/.
    Uses the existing public entry points and emits events from the
    PipelineState returned by each.
    """

    def __init__(self, event_bus: EventBus,
                 check_cancelled: Optional[Callable[[], bool]] = None):
        self._event_bus = event_bus
        self._check_cancelled = check_cancelled or (lambda: False)

    def run(self, job_id: str, benchmark: str, pipeline_version: str = "v1",
            max_iterations: int = 5, use_reference_rtl: bool = False,
            use_reference_tb: bool = False) -> dict[str, Any]:
        """Execute the real pipeline synchronously.

        Called from a thread-pool executor — blocks until pipeline finishes.
        Emits job_started before execution and job_completed/job_failed after.
        """
        start = time.time()
        seq = 0

        # ---- JOB_STARTED ----
        seq += 1
        self._event_bus.publish(PipelineEvent(
            job_id=job_id,
            event_type=EventType.JOB_STARTED,
            stage="start",
            message=f"Pipeline {pipeline_version} started for {benchmark}",
            severity=Severity.INFO,
            payload={
                "benchmark": benchmark,
                "pipeline_version": pipeline_version,
                "max_iterations": max_iterations,
                "use_reference_rtl": use_reference_rtl,
                "use_reference_tb": use_reference_tb,
                "mode": "real",
            },
            sequence_num=seq,
        ))

        # ---- Load inputs ----
        spec_path = settings.BENCHMARKS_DIR / benchmark / "spec.txt"
        if not spec_path.exists():
            raise FileNotFoundError(f"Benchmark spec not found: {spec_path}")
        spec = spec_path.read_text()

        rtl_code = ""
        reference_tb_path = ""

        if use_reference_rtl:
            ref_rtl = settings.BENCHMARKS_DIR / benchmark / "reference_rtl.v"
            if ref_rtl.exists():
                rtl_code = ref_rtl.read_text()
                logger.info("Using reference RTL for %s", benchmark)

        if use_reference_tb:
            ref_tb = settings.BENCHMARKS_DIR / benchmark / "reference_tb.py"
            if ref_tb.exists():
                reference_tb_path = str(ref_tb.resolve())
                logger.info("Using reference testbench for %s", benchmark)

        # ---- Route to pipeline version ----
        pipeline_fn = PIPELINE_FUNCTIONS.get(pipeline_version)
        if pipeline_fn is None:
            raise ValueError(f"Unknown pipeline version: {pipeline_version}")

        try:
            final_state = pipeline_fn(
                spec=spec,
                design_name=benchmark,
                rtl_code=rtl_code,
                reference_tb_path=reference_tb_path,
            )
        except Exception as exc:
            elapsed = time.time() - start
            seq += 1
            self._event_bus.publish(PipelineEvent(
                job_id=job_id,
                event_type=EventType.JOB_FAILED,
                message=f"Pipeline failed: {exc}",
                severity=Severity.ERROR,
                payload={"error": str(exc)},
                elapsed_time=elapsed,
                sequence_num=seq,
            ))
            raise

        elapsed = time.time() - start
        sim_passed = final_state.get("sim_passed", False)
        timing_met = final_state.get("timing_met", False)
        drc_passed = final_state.get("drc_passed", False)

        # Emit result events from final state
        seq += 1
        self._event_bus.publish(PipelineEvent(
            job_id=job_id,
            event_type=EventType.SIMULATION_RESULT,
            stage="simulation",
            message="Simulation PASSED" if sim_passed else "Simulation FAILED",
            severity=Severity.SUCCESS if sim_passed else Severity.ERROR,
            payload={
                "passed": sim_passed,
                "coverage_pct": final_state.get("coverage_pct", 0),
                "iteration": final_state.get("iteration", 0),
            },
            elapsed_time=elapsed,
            iteration=final_state.get("iteration"),
            sequence_num=seq,
        ))

        if pipeline_version in ("v2", "v3") and final_state.get("synthesis_report"):
            seq += 1
            self._event_bus.publish(PipelineEvent(
                job_id=job_id,
                event_type=EventType.SYNTHESIS_RESULT,
                stage="synthesis",
                message=f"Synthesis complete — {final_state.get('cell_count', '?')} cells",
                severity=Severity.SUCCESS,
                payload={
                    "netlist_path": final_state.get("netlist_path", ""),
                    "cell_count": final_state.get("cell_count", 0),
                },
                elapsed_time=elapsed,
                sequence_num=seq,
            ))

        if pipeline_version in ("v2", "v3") and final_state.get("wns") is not None:
            seq += 1
            wns = final_state.get("wns", 0)
            self._event_bus.publish(PipelineEvent(
                job_id=job_id,
                event_type=EventType.STA_RESULT,
                stage="sta",
                message=f"Timing {'met' if timing_met else 'not met'} — WNS={wns}",
                severity=Severity.SUCCESS if timing_met else Severity.WARNING,
                payload={
                    "timing_met": timing_met,
                    "wns": wns,
                    "tns": final_state.get("tns", 0),
                    "critical_path": final_state.get("critical_path", ""),
                },
                elapsed_time=elapsed,
                sequence_num=seq,
            ))

        if pipeline_version == "v3" and final_state.get("gds_path"):
            seq += 1
            self._event_bus.publish(PipelineEvent(
                job_id=job_id,
                event_type=EventType.DRC_RESULT,
                stage="drc",
                message=f"DRC {'clean' if drc_passed else 'violations found'}",
                severity=Severity.SUCCESS if drc_passed else Severity.WARNING,
                payload={
                    "drc_passed": drc_passed,
                    "violations": final_state.get("drc_violations", 0),
                    "gds_path": final_state.get("gds_path", ""),
                },
                elapsed_time=elapsed,
                sequence_num=seq,
            ))

        # ---- JOB_COMPLETED ----
        seq += 1
        self._event_bus.publish(PipelineEvent(
            job_id=job_id,
            event_type=EventType.JOB_COMPLETED,
            message=f"Pipeline complete in {elapsed:.1f}s",
            severity=Severity.SUCCESS,
            payload={
                "sim_passed": sim_passed,
                "timing_met": timing_met,
                "drc_passed": drc_passed,
                "total_iterations": final_state.get("iteration", 0),
                "total_elapsed": round(elapsed, 3),
            },
            elapsed_time=elapsed,
            sequence_num=seq,
        ))

        logger.info("Pipeline %s for %s completed in %.1fs", pipeline_version, benchmark, elapsed)
        return dict(final_state)


# ---- Registry of pipeline entry points (imported lazily) ------------------

def _import_pipeline_functions() -> dict[str, Callable]:
    """Lazily import pipeline functions to avoid import-time failures
    when EDA tools are not installed."""
    funcs: dict[str, Callable] = {}

    try:
        from v1_core.pipeline import run_pipeline
        funcs["v1"] = run_pipeline
    except ImportError as e:
        logger.warning("V1 pipeline not available: %s", e)

    try:
        from v2_verification.pipeline import run_v2_pipeline
        funcs["v2"] = run_v2_pipeline
    except ImportError as e:
        logger.warning("V2 pipeline not available: %s", e)

    try:
        from v3_physical.pipeline import run_v3_pipeline
        funcs["v3"] = run_v3_pipeline
    except ImportError as e:
        logger.warning("V3 pipeline not available: %s", e)

    return funcs


PIPELINE_FUNCTIONS = _import_pipeline_functions()
