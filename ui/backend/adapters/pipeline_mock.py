"""
pipeline_mock.py — Mock pipeline adapter that simulates execution.

Emits realistic structured events through the EventBus without running
any EDA tools or LLM calls. Useful for:
  - Frontend development
  - SSE streaming tests
  - CI/CD without EDA tool dependencies

The stage sequence mirrors each pipeline version's actual stages.
Delays are configurable — default values simulate realistic cadence.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional

from ui.backend.config import settings
from ui.backend.models.job import Job
from ui.backend.schemas.event import EventType, PipelineEvent, Severity
from ui.backend.services.event_bus import EventBus

logger = logging.getLogger(__name__)


# Per-version stage sequences (names match actual agent nodes).
_MOCK_STAGES: dict[str, list[tuple[str, float]]] = {
    "v1": [
        ("spec_parser", 0.3),
        ("verification_planner", 0.2),
        ("rtl_gen", 1.5),
        ("testbench", 0.8),
        ("simulation", 1.2),
        ("log_analysis", 0.3),
        ("fix", 0.5),
        ("testbench_re", 0.6),
        ("simulation_re", 0.4),
    ],
    "v2": [
        ("spec_parser", 0.3),
        ("verification_planner", 0.2),
        ("rtl_gen", 1.5),
        ("testbench", 0.8),
        ("simulation", 1.2),
        ("synthesis", 2.0),
        ("sta", 1.5),
    ],
    "v3": [
        ("spec_parser", 0.3),
        ("verification_planner", 0.2),
        ("rtl_gen", 1.5),
        ("testbench", 0.8),
        ("simulation", 1.2),
        ("synthesis", 2.0),
        ("sta", 1.5),
        ("openlane", 3.0),
        ("drc", 1.0),
    ],
}

# Sample payloads per stage — injected into stage_completed events.
_MOCK_PAYLOADS: dict[str, dict[str, Any]] = {
    "spec_parser": {"parsed_operations": 4, "confidence": 0.95},
    "verification_planner": {"test_cases": 6, "corner_cases": 2},
    "rtl_gen": {"lines": 45, "module_name": "mock_design"},
    "testbench": {"test_count": 12, "framework": "cocotb"},
    "testbench_re": {"test_count": 12, "framework": "cocotb", "re_run": True},
    "simulation": {"passed": True, "tests_run": 12, "tests_passed": 12, "coverage_pct": 98.2},
    "simulation_re": {"passed": True, "tests_run": 12, "tests_passed": 12, "coverage_pct": 98.2, "re_run": True},
    "log_analysis": {"error_type": "NONE", "analysis_complete": True},
    "fix": {"skill_hits": 2, "changes_made": 1},
    "synthesis": {"cell_count": 142, "area": "450 sq µm", "frequency": "100 MHz"},
    "sta": {"timing_met": True, "wns": 6.59, "tns": 0.0, "critical_path": "Y[7] via ALU logic"},
    "openlane": {"gds_path": "workspace/physical/mock/runs/run_01/final/gds/mock.gds"},
    "drc": {"drc_passed": True, "violations": 0},
}


class MockPipelineAdapter:
    """Simulates a full pipeline run with structured events.

    Call run() from a thread — it blocks until the simulated pipeline
    completes, emitting events through the EventBus as it progresses.
    """

    def __init__(self, event_bus: EventBus, check_cancelled: Optional[Callable[[], bool]] = None):
        self._event_bus = event_bus
        self._check_cancelled = check_cancelled or (lambda: False)

    def run(self, job_id: str, benchmark: str, pipeline_version: str = "v1",
            max_iterations: int = 5, use_reference_rtl: bool = False,
            use_reference_tb: bool = False) -> dict[str, Any]:
        """Run the mock pipeline synchronously. Returns final PipelineState-like dict."""
        stages = _MOCK_STAGES.get(pipeline_version, _MOCK_STAGES["v1"])
        start_time = time.time()
        seq = 0

        # ---- JOB_STARTED ----
        seq += 1
        self._event_bus.publish(PipelineEvent(
            job_id=job_id,
            event_type=EventType.JOB_STARTED,
            stage="start",
            message=f"Mock {pipeline_version} pipeline started for {benchmark}",
            severity=Severity.INFO,
            payload={
                "benchmark": benchmark,
                "pipeline_version": pipeline_version,
                "max_iterations": max_iterations,
                "use_reference_rtl": use_reference_rtl,
                "use_reference_tb": use_reference_tb,
                "mode": "mock",
            },
            sequence_num=seq,
        ))

        # ---- Stages ----
        sim_passed = False
        timing_met = False
        drc_passed = False
        iteration = 0

        # Track which stages are in the fix loop for event emission
        _FIX_LOOP_STAGES = {"log_analysis", "fix", "testbench_re", "simulation_re"}

        for stage_name, delay in stages:
            if self._check_cancelled():
                seq += 1
                self._event_bus.publish(PipelineEvent(
                    job_id=job_id,
                    event_type=EventType.JOB_CANCELLED,
                    stage=stage_name,
                    message="Job cancelled by user request",
                    severity=Severity.WARNING,
                    elapsed_time=time.time() - start_time,
                    sequence_num=seq,
                ))
                return {"sim_passed": sim_passed, "cancelled": True}

            # Stage start
            seq += 1
            self._event_bus.publish(PipelineEvent(
                job_id=job_id,
                event_type=EventType.STAGE_STARTED,
                stage=stage_name,
                message=f"Starting {stage_name}",
                severity=Severity.INFO,
                elapsed_time=time.time() - start_time,
                sequence_num=seq,
                iteration=iteration if stage_name == "fix" else None,
            ))

            # Simulate work
            time.sleep(delay)

            # Stage completed (or failed randomly for realism in simulation)
            payload = _MOCK_PAYLOADS.get(stage_name, {}).copy()
            seq += 1

            # Emit fix_attempt at the start of each fix-loop cycle
            if stage_name in _FIX_LOOP_STAGES and stage_name == "log_analysis":
                iteration += 1
                seq += 1
                self._event_bus.publish(PipelineEvent(
                    job_id=job_id,
                    event_type=EventType.FIX_ATTEMPT,
                    stage=stage_name,
                    message=f"Fix attempt {iteration} — simulation failed, analysing logs",
                    severity=Severity.WARNING,
                    iteration=iteration,
                    elapsed_time=time.time() - start_time,
                    sequence_num=seq,
                ))

            # Emit skill_retrieved during log_analysis
            if stage_name == "log_analysis":
                seq += 1
                self._event_bus.publish(PipelineEvent(
                    job_id=job_id,
                    event_type=EventType.SKILL_RETRIEVED,
                    stage=stage_name,
                    message="Retrieved 2 matching skills from Trace2Skill",
                    severity=Severity.INFO,
                    payload={"skill_ids": ["comb_curated_001", "comb_0003"], "match_count": 2},
                    iteration=iteration,
                    elapsed_time=time.time() - start_time,
                    sequence_num=seq,
                ))

            # Emit skill_stored after fix
            if stage_name == "fix":
                seq += 1
                self._event_bus.publish(PipelineEvent(
                    job_id=job_id,
                    event_type=EventType.SKILL_STORED,
                    stage=stage_name,
                    message="Stored fix attempt in Trace2Skill (tentative)",
                    severity=Severity.INFO,
                    payload={"skill_id": f"comb_{iteration:04d}", "tentative": True},
                    iteration=iteration,
                    elapsed_time=time.time() - start_time,
                    sequence_num=seq,
                ))

            # Simulate potential fix loop (V1 only)
            if stage_name == "simulation" and iteration == 0:
                # First simulation always passes in mock
                sim_passed = True
                seq += 1
                self._event_bus.publish(PipelineEvent(
                    job_id=job_id,
                    event_type=EventType.SIMULATION_RESULT,
                    stage=stage_name,
                    message="Simulation passed — all tests pass",
                    severity=Severity.SUCCESS,
                    payload={"passed": True, "tests_run": 12, "tests_passed": 12, "coverage_pct": 98.2},
                    elapsed_time=time.time() - start_time,
                    sequence_num=seq,
                ))

            elif stage_name in ("simulation", "simulation_re"):
                sim_passed = True
                seq += 1
                self._event_bus.publish(PipelineEvent(
                    job_id=job_id,
                    event_type=EventType.SIMULATION_RESULT,
                    stage=stage_name,
                    message="Simulation passed — all tests pass" if stage_name == "simulation_re" else "Simulation passed",
                    severity=Severity.SUCCESS,
                    payload={"passed": True, "tests_run": 12, "tests_passed": 12, "coverage_pct": 98.2},
                    elapsed_time=time.time() - start_time,
                    sequence_num=seq,
                    iteration=iteration if stage_name == "simulation_re" else None,
                ))

            if stage_name == "synthesis":
                seq += 1
                self._event_bus.publish(PipelineEvent(
                    job_id=job_id,
                    event_type=EventType.SYNTHESIS_RESULT,
                    stage=stage_name,
                    message=f"Synthesis complete — {payload.get('cell_count', '?')} cells",
                    severity=Severity.SUCCESS,
                    payload=payload,
                    elapsed_time=time.time() - start_time,
                    sequence_num=seq,
                ))

            if stage_name == "sta":
                timing_met = True
                seq += 1
                self._event_bus.publish(PipelineEvent(
                    job_id=job_id,
                    event_type=EventType.STA_RESULT,
                    stage=stage_name,
                    message=f"Timing met — WNS={payload.get('wns', 'N/A')}",
                    severity=Severity.SUCCESS if timing_met else Severity.WARNING,
                    payload=payload,
                    elapsed_time=time.time() - start_time,
                    sequence_num=seq,
                ))

            if stage_name == "drc":
                drc_passed = True
                seq += 1
                self._event_bus.publish(PipelineEvent(
                    job_id=job_id,
                    event_type=EventType.DRC_RESULT,
                    stage=stage_name,
                    message="DRC clean — 0 violations",
                    severity=Severity.SUCCESS,
                    payload={"drc_passed": True, "violations": 0},
                    elapsed_time=time.time() - start_time,
                    sequence_num=seq,
                ))

            self._event_bus.publish(PipelineEvent(
                job_id=job_id,
                event_type=EventType.STAGE_COMPLETED,
                stage=stage_name,
                message=f"Completed {stage_name} in {delay:.1f}s",
                severity=Severity.SUCCESS,
                payload=payload,
                elapsed_time=time.time() - start_time,
                sequence_num=seq,
                iteration=iteration if stage_name in ("log_analysis", "fix") else None,
            ))

            # Progress update
            elapsed = time.time() - start_time
            total_estimate = sum(d for _, d in stages)
            pct = min(95, int(100 * elapsed / total_estimate))
            seq += 1
            self._event_bus.publish(PipelineEvent(
                job_id=job_id,
                event_type=EventType.PROGRESS,
                message=f"Progress: {pct}%",
                severity=Severity.INFO,
                payload={"percent": pct},
                elapsed_time=elapsed,
                sequence_num=seq,
            ))

        # ---- JOB_COMPLETED ----
        total_elapsed = time.time() - start_time
        seq += 1
        self._event_bus.publish(PipelineEvent(
            job_id=job_id,
            event_type=EventType.JOB_COMPLETED,
            message=f"Pipeline complete. Simulation={'PASS' if sim_passed else 'FAIL'}, "
                    f"Timing={'MET' if timing_met else 'NOT MET'}, "
                    f"DRC={'CLEAN' if drc_passed else 'FAIL'}",
            severity=Severity.SUCCESS,
            payload={
                "sim_passed": sim_passed,
                "timing_met": timing_met,
                "drc_passed": drc_passed,
                "total_iterations": iteration,
                "total_elapsed": round(total_elapsed, 3),
                "final_stage": stages[-1][0] if stages else "unknown",
            },
            elapsed_time=total_elapsed,
            sequence_num=seq,
        ))

        logger.info("Mock pipeline %s for %s completed in %.1fs",
                    pipeline_version, benchmark, total_elapsed)

        return {
            "sim_passed": sim_passed,
            "timing_met": timing_met,
            "drc_passed": drc_passed,
            "total_elapsed": total_elapsed,
        }
