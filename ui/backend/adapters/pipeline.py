"""
pipeline.py — Real pipeline adapter wrapping the frozen RTL2GDS pipeline.

This adapter:
  1. Calls build_pipeline() / build_v2_pipeline() / build_v3_pipeline()
  2. Uses graph.stream(stream_mode=["updates", "debug"]) for per-node events
  3. Emits the same structured event stream as the mock adapter
  4. NEVER modifies the frozen pipeline source code

PIPELINE_MODE=real gates usage of this adapter.
"""

import logging
import re
import time
from pathlib import Path
from typing import Any, Callable, Optional

from ui.backend.config import settings
from ui.backend.schemas.event import EventType, PipelineEvent, Severity
from ui.backend.services.event_bus import EventBus

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Stage metadata — must match frontend V1_STAGES / V2_STAGES / V3_STAGES
# ---------------------------------------------------------------------------

# Primary stage sequences (first pass, no fix loop)
_PRIMARY_STAGES: dict[str, list[str]] = {
    "v1": [
        "spec_parser", "verification_planner", "rtl_gen", "testbench", "simulation",
    ],
    "v2": [
        "spec_parser", "verification_planner", "rtl_gen", "testbench", "simulation",
        "synthesis", "sta",
    ],
    "v3": [
        "spec_parser", "verification_planner", "rtl_gen", "testbench", "simulation",
        "synthesis", "sta", "openlane", "drc",
    ],
}

# Nodes that belong to the fix loop (may execute multiple times if sim fails).
_FIX_LOOP_NODES: set[str] = {"log_analysis", "fix", "testbench", "simulation"}

# Nodes that may appear in a timing-optimisation loop (V2/V3).
_TIMING_LOOP_NODES: set[str] = {"synthesis", "sta", "timing_opt"}

# Estimated total stage count for progress calculation (accounts for typical
# fix-loop iterations).
_ESTIMATED_TOTAL: dict[str, int] = {"v1": 9, "v2": 9, "v3": 11}


# Agent log messages for each stage (emitted as agent_log events during execution)
_AGENT_LOG_MESSAGES: dict[str, str] = {
    "spec_parser": "Analyzing specification — extracting interfaces, clocks, and constraints",
    "verification_planner": "Planning verification strategy — coverage goals, test plan, corner cases",
    "rtl_gen": "Generating synthesizable RTL with DeepSeek LLM",
    "testbench": "Writing cocotb testbench with directed and random test vectors",
    "simulation": "Launching Icarus Verilog simulation — checking functional correctness",
    "log_analysis": "Analyzing simulation failures — identifying root cause and error type",
    "fix": "Applying fix from Trace2Skill memory — retrying with correction",
    "synthesis": "Running Yosys synthesis with sky130 — optimizing netlist",
    "sta": "Running OpenSTA static timing analysis — checking setup/hold",
    "openlane": "Launching OpenLane physical design flow — macro placement, CTS, routing",
    "drc": "Running KLayout DRC — verifying manufacturability",
}


# ===================================================================
# PipelineAdapter
# ===================================================================


class PipelineAdapter:
    """Wraps the frozen LangGraph pipelines as an event-emitting adapter.

    Uses ``graph.stream(stream_mode=["updates","debug"])`` to intercept
    per-node execution events and emits the same rich event stream as
    ``MockPipelineAdapter`` — stage_started, stage_completed, progress,
    simulation_result, synthesis_result, sta_result, drc_result,
    fix_attempt, skill_retrieved, skill_stored, job_completed.

    Does not modify v1_core/, v2_verification/, or v3_physical/.
    """

    def __init__(self, event_bus: EventBus,
                 check_cancelled: Optional[Callable[[], bool]] = None):
        self._event_bus = event_bus
        self._check_cancelled = check_cancelled or (lambda: False)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self, job_id: str, benchmark: str, pipeline_version: str = "v1",
            max_iterations: int = 5, use_reference_rtl: bool = False,
            use_reference_tb: bool = False) -> dict[str, Any]:
        """Execute the real pipeline synchronously with per-stage events.

        Called from a thread-pool executor — blocks until pipeline finishes
        while emitting events through the EventBus in real time.
        """
        start_time = time.time()
        seq = 0

        # -- JOB_STARTED -------------------------------------------------
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

        # -- Load input files --------------------------------------------
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
        if use_reference_tb:
            ref_tb = settings.BENCHMARKS_DIR / benchmark / "reference_tb.py"
            if ref_tb.exists():
                reference_tb_path = str(ref_tb.resolve())

        # -- Build graph + state -----------------------------------------
        graph, initial_state = self._build(pipeline_version, spec, benchmark,
                                           rtl_code, reference_tb_path)

        # -- Streaming state tracking ------------------------------------
        iteration = 0               # current fix-loop iteration
        seen: dict[str, int] = {}   # node_name → execution count
        final_state: dict[str, Any] = {}
        total_estimate = _ESTIMATED_TOTAL.get(pipeline_version,
                                              len(_PRIMARY_STAGES.get(pipeline_version, [])))
        completed = 0

        try:
            # ============================================================
            # Per-node event loop (real-time streaming)
            # ============================================================
            for event in graph.stream(
                initial_state,
                stream_mode=["updates", "debug"],
                config={"recursion_limit": 50},
            ):
                # --- Cancellation guard ---
                if self._check_cancelled():
                    seq += 1
                    self._event_bus.publish(PipelineEvent(
                        job_id=job_id,
                        event_type=EventType.JOB_CANCELLED,
                        message="Job cancelled by user request",
                        severity=Severity.WARNING,
                        elapsed_time=time.time() - start_time,
                        sequence_num=seq,
                    ))
                    return {"sim_passed": False, "cancelled": True}

                mode, data = event

                # ========================================================
                # Debug events — task start
                # ========================================================
                if mode == "debug" and data.get("type") == "task":
                    node_name = data["payload"]["name"]
                    count = seen.get(node_name, 0)
                    seen[node_name] = count + 1

                    # --- Determine display name (fix-loop renames) ------
                    display = node_name
                    if node_name in _FIX_LOOP_NODES and count > 0:
                        if node_name == "testbench":
                            display = "testbench_re"
                        elif node_name == "simulation":
                            display = "simulation_re"
                    elif node_name == "synthesis" and count > 0:
                        display = "synthesis"  # timing-opt re-run
                    elif node_name == "sta" and count > 0:
                        display = "sta"  # timing-opt re-run

                    # --- Fix-attempt event (first log_analysis of each loop) ---
                    if node_name == "log_analysis":
                        iteration = count
                        if iteration > 0:
                            seq += 1
                            self._event_bus.publish(PipelineEvent(
                                job_id=job_id,
                                event_type=EventType.FIX_ATTEMPT,
                                stage=node_name,
                                message=f"Fix attempt {iteration} — "
                                        f"simulation failed, analysing logs",
                                severity=Severity.WARNING,
                                iteration=iteration,
                                elapsed_time=time.time() - start_time,
                                sequence_num=seq,
                            ))

                    # --- Stage started ---
                    seq += 1
                    self._event_bus.publish(PipelineEvent(
                        job_id=job_id,
                        event_type=EventType.STAGE_STARTED,
                        stage=display,
                        message=f"Starting {display}",
                        severity=Severity.INFO,
                        elapsed_time=time.time() - start_time,
                        sequence_num=seq,
                        iteration=iteration if node_name in ("log_analysis", "fix") else None,
                    ))

                    # --- Agent log: what this stage is doing ---
                    seq += 1
                    agent_msg = _AGENT_LOG_MESSAGES.get(node_name, f"Executing {display}")
                    self._event_bus.publish(PipelineEvent(
                        job_id=job_id,
                        event_type=EventType.AGENT_LOG,
                        stage=display,
                        message=agent_msg,
                        severity=Severity.INFO,
                        elapsed_time=time.time() - start_time,
                        sequence_num=seq,
                        iteration=iteration if node_name in ("log_analysis", "fix") else None,
                    ))

                # ========================================================
                # Update events — node completed
                # ========================================================
                elif mode == "updates":
                    node_name = list(data.keys())[0]
                    state_update = data[node_name]
                    final_state = state_update
                    count = seen.get(node_name, 1)

                    # --- Display name (matches start event) -------------
                    display = node_name
                    if node_name in _FIX_LOOP_NODES and count > 1:
                        if node_name == "testbench":
                            display = "testbench_re"
                        elif node_name == "simulation":
                            display = "simulation_re"

                    completed += 1
                    elapsed = time.time() - start_time

                    # --- Skill events (log_analysis, fix) ---------------
                    if node_name == "log_analysis":
                        hits = state_update.get("trace2skill_hits", [])
                        if hits:
                            seq += 1
                            self._event_bus.publish(PipelineEvent(
                                job_id=job_id,
                                event_type=EventType.SKILL_RETRIEVED,
                                stage=display,
                                message=f"Retrieved {len(hits)} matching "
                                        f"skills from Trace2Skill",
                                severity=Severity.INFO,
                                payload={
                                    "skill_ids": [h.get("skill_id", str(h))
                                                  for h in hits[:5]],
                                    "match_count": len(hits),
                                },
                                iteration=iteration,
                                elapsed_time=elapsed,
                                sequence_num=seq,
                            ))

                    if node_name == "fix":
                        pending = state_update.get("pending_skill_id", "")
                        if pending:
                            seq += 1
                            self._event_bus.publish(PipelineEvent(
                                job_id=job_id,
                                event_type=EventType.SKILL_STORED,
                                stage=display,
                                message="Stored fix attempt in Trace2Skill "
                                        "(tentative)",
                                severity=Severity.INFO,
                                payload={"skill_id": pending, "tentative": True},
                                iteration=iteration,
                                elapsed_time=elapsed,
                                sequence_num=seq,
                            ))

                    # --- Result events ----------------------------------
                    if node_name == "simulation":
                        sim_passed = state_update.get("sim_passed", False)
                        sim_log = state_update.get("sim_log", "")
                        tests_run = len(re.findall(r'testcase name=', sim_log))
                        failures_in_log = len(re.findall(
                            r'<failure', sim_log
                        )) if not sim_passed else 0
                        tests_passed = tests_run - failures_in_log

                        seq += 1
                        self._event_bus.publish(PipelineEvent(
                            job_id=job_id,
                            event_type=EventType.SIMULATION_RESULT,
                            stage=display,
                            message=("Simulation passed — all tests pass"
                                     if sim_passed else "Simulation failed"),
                            severity=Severity.SUCCESS if sim_passed else Severity.ERROR,
                            payload={
                                "passed": sim_passed,
                                "tests_run": tests_run,
                                "tests_passed": tests_passed,
                                "coverage_pct": state_update.get("coverage_pct", 0.0),
                            },
                            elapsed_time=elapsed,
                            sequence_num=seq,
                            iteration=iteration if count > 1 else None,
                        ))

                    elif node_name == "synthesis":
                        report = state_update.get("synthesis_report", "")
                        cell_count, area = _parse_synthesis_report(report)
                        seq += 1
                        self._event_bus.publish(PipelineEvent(
                            job_id=job_id,
                            event_type=EventType.SYNTHESIS_RESULT,
                            stage=node_name,
                            message=f"Synthesis complete — {cell_count} cells",
                            severity=Severity.SUCCESS,
                            payload={
                                "cell_count": cell_count,
                                "area": area,
                                "netlist_path": state_update.get("netlist_path", ""),
                            },
                            elapsed_time=elapsed,
                            sequence_num=seq,
                        ))

                    elif node_name == "sta":
                        timing_met = state_update.get("timing_met", False)
                        wns = state_update.get("wns", 0.0)
                        seq += 1
                        self._event_bus.publish(PipelineEvent(
                            job_id=job_id,
                            event_type=EventType.STA_RESULT,
                            stage=node_name,
                            message=f"Timing {'met' if timing_met else 'not met'} "
                                    f"— WNS={wns}",
                            severity=Severity.SUCCESS if timing_met else Severity.WARNING,
                            payload={
                                "timing_met": timing_met,
                                "wns": wns,
                                "tns": state_update.get("tns", 0.0),
                                "critical_path": state_update.get("critical_path", ""),
                            },
                            elapsed_time=elapsed,
                            sequence_num=seq,
                        ))

                    elif node_name == "drc":
                        drc_passed = state_update.get("drc_passed", False)
                        violations = state_update.get("drc_violations", 0)
                        seq += 1
                        self._event_bus.publish(PipelineEvent(
                            job_id=job_id,
                            event_type=EventType.DRC_RESULT,
                            stage=node_name,
                            message=("DRC clean — 0 violations" if drc_passed
                                     else f"DRC failed — {violations} violations"),
                            severity=Severity.SUCCESS if drc_passed else Severity.WARNING,
                            payload={
                                "drc_passed": drc_passed,
                                "violations": violations,
                                "gds_path": state_update.get("gds_path", ""),
                            },
                            elapsed_time=elapsed,
                            sequence_num=seq,
                        ))

                    # --- Stage completed (with extracted payload) -------
                    payload = _extract_payload(node_name, state_update)
                    seq += 1
                    self._event_bus.publish(PipelineEvent(
                        job_id=job_id,
                        event_type=EventType.STAGE_COMPLETED,
                        stage=display,
                        message=f"Completed {display}",
                        severity=Severity.SUCCESS,
                        payload=payload,
                        elapsed_time=elapsed,
                        sequence_num=seq,
                        iteration=(iteration
                                   if node_name in ("log_analysis", "fix")
                                   else None),
                    ))

                    # --- Progress update --------------------------------
                    pct = min(95, int(100 * completed / total_estimate))
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

        except Exception as exc:
            elapsed = time.time() - start_time
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

        # ================================================================
        # JOB_COMPLETED
        # ================================================================
        total_elapsed = time.time() - start_time
        sim_passed = final_state.get("sim_passed", False)
        timing_met = final_state.get("timing_met", False)
        drc_passed = final_state.get("drc_passed", False)

        seq += 1
        self._event_bus.publish(PipelineEvent(
            job_id=job_id,
            event_type=EventType.JOB_COMPLETED,
            message=(f"Pipeline complete. "
                     f"Simulation={'PASS' if sim_passed else 'FAIL'}, "
                     f"Timing={'MET' if timing_met else 'N/A'}, "
                     f"DRC={'CLEAN' if drc_passed else 'N/A'}"),
            severity=Severity.SUCCESS,
            payload={
                "sim_passed": sim_passed,
                "timing_met": timing_met,
                "drc_passed": drc_passed,
                "total_iterations": final_state.get("iteration", iteration),
                "total_elapsed": round(total_elapsed, 3),
            },
            elapsed_time=total_elapsed,
            sequence_num=seq,
        ))

        logger.info("Pipeline %s for %s completed in %.1fs",
                    pipeline_version, benchmark, total_elapsed)
        return dict(final_state)

    # ------------------------------------------------------------------
    # Graph + state builder
    # ------------------------------------------------------------------

    def _build(self, version: str, spec: str, benchmark: str,
               rtl_code: str, reference_tb_path: str):
        """Return ``(compiled_graph, initial_state)`` for *version*."""
        from v1_core.agents.orchestrator import get_initial_state

        skip_rtl = bool(rtl_code)
        skip_tb = bool(reference_tb_path)

        if version == "v1":
            from v1_core.pipeline import build_pipeline
            graph = build_pipeline(skip_rtl_gen=skip_rtl, skip_testbench=skip_tb)
            state = get_initial_state(spec=spec, design_name=benchmark)

        elif version == "v2":
            from v2_verification.pipeline import build_v2_pipeline
            graph = build_v2_pipeline(skip_rtl_gen=skip_rtl,
                                      skip_testbench=skip_tb)
            state = get_initial_state(spec=spec, design_name=benchmark)
            state.update({
                "netlist_path": "", "synthesis_report": "",
                "timing_met": False, "wns": 0.0, "tns": 0.0,
                "critical_path": "", "timing_iterations": 0,
            })

        elif version == "v3":
            from v3_physical.pipeline import build_v3_pipeline
            graph = build_v3_pipeline(skip_rtl_gen=skip_rtl,
                                      skip_testbench=skip_tb)
            state = get_initial_state(spec=spec, design_name=benchmark)
            state.update({
                "netlist_path": "", "synthesis_report": "",
                "timing_met": False, "wns": 0.0, "tns": 0.0,
                "critical_path": "", "timing_iterations": 0,
            })

        else:
            raise ValueError(f"Unknown pipeline version: {version}")

        if rtl_code:
            state["rtl_code"] = rtl_code
        if reference_tb_path:
            state["reference_tb_path"] = reference_tb_path

        return graph, state


# ===================================================================
# Payload helpers
# ===================================================================


def _extract_payload(stage_name: str, state: dict[str, Any]) -> dict[str, Any]:
    """Build a ``stage_completed`` payload from the PipelineState.

    Extracts the same keys the mock adapter provides so the frontend sees
    identical payload shapes.
    """
    if stage_name == "spec_parser":
        sa = state.get("spec_analysis", {})
        return {
            "parsed_operations": len(sa.get("behavior", [])),
            "confidence": 0.95,
            "module_name": sa.get("module_name", state.get("design_name", "")),
        }

    if stage_name == "verification_planner":
        vp = state.get("verification_plan", {})
        tiers = vp.get("verification_tiers", [])
        total = sum(len(t.get("tests", [])) for t in tiers)
        return {"test_cases": total, "corner_cases": len(vp.get("corner_cases", []))}

    if stage_name == "rtl_gen":
        rtl = state.get("rtl_code", "")
        return {
            "lines": len(rtl.splitlines()) if rtl else 0,
            "module_name": state.get("design_name", ""),
        }

    if stage_name == "testbench":
        tb = state.get("testbench_code", "")
        return {
            "test_count": len(re.findall(r'def test_', tb)) if tb else 0,
            "framework": "cocotb",
        }

    if stage_name == "simulation":
        sim_log = state.get("sim_log", "")
        tests_run = len(re.findall(r'testcase name=', sim_log))
        return {
            "passed": state.get("sim_passed", False),
            "tests_run": tests_run,
            "tests_passed": tests_run if state.get("sim_passed") else 0,
            "coverage_pct": state.get("coverage_pct", 0.0),
        }

    if stage_name == "log_analysis":
        ea = state.get("error_analysis", {})
        return {
            "error_type": ea.get("ERROR_TYPE", "UNKNOWN"),
            "analysis_complete": True,
            "skill_hits": len(state.get("trace2skill_hits", [])),
        }

    if stage_name == "fix":
        return {
            "skill_hits": len(state.get("trace2skill_hits", [])),
            "changes_made": 1 if state.get("rtl_code") else 0,
        }

    if stage_name == "synthesis":
        report = state.get("synthesis_report", "")
        cell_count, area = _parse_synthesis_report(report)
        return {"cell_count": cell_count, "area": area,
                "netlist_path": state.get("netlist_path", "")}

    if stage_name == "sta":
        return {
            "timing_met": state.get("timing_met", False),
            "wns": state.get("wns", 0.0),
            "tns": state.get("tns", 0.0),
            "critical_path": state.get("critical_path", ""),
        }

    if stage_name == "openlane":
        return {"gds_path": state.get("gds_path", "")}

    if stage_name == "drc":
        return {
            "drc_passed": state.get("drc_passed", False),
            "violations": state.get("drc_violations", 0),
        }

    return {}


def _parse_synthesis_report(report: str) -> tuple[int, str]:
    """Extract ``(cell_count, area_str)`` from a synthesis report string."""
    cell_count = 0
    area = "N/A"
    m = re.search(r'Cell count:\s+(\d+)', report)
    if m:
        cell_count = int(m.group(1))
    m = re.search(r'Area:\s+([\d.]+)', report)
    if m:
        area = f"{m.group(1)} sq µm"
    return cell_count, area
