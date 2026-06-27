# Yosys Synthesis Integration — Architecture Plan

## Status: Ready for Implementation

## 1. Current State

The V2 pipeline (`v2_verification/`) already runs real Yosys synthesis via:

- **`v2_verification/agents/synthesis_agent.py`** — LangGraph node that writes RTL to
  `workspace/synthesis/`, calls `_run_synthesis()`, and returns updated PipelineState.
- **`v2_verification/mcp_tools/synthesis_server.py`** — Contains `_run_synthesis()` which
  generates a Yosys TCL script and runs `yosys -Q -s <script>` via `subprocess.run()`.
- Yosys 0.9 is installed at `/usr/bin/yosys`.
- Sky130 PDK liberty file exists at `pdk/sky130/sky130_fd_sc_hd__tt_025C_1v80.lib`.
- The pipeline adapter (`ui/backend/adapters/pipeline.py`) already handles V2 mode and
  emits `SYNTHESIS_RESULT` events with `cell_count`, `area`, `netlist_path`.

### What's Missing

- **No real-time log streaming** — `_run_synthesis()` uses `subprocess.run(capture_output=True)`,
  so Yosys output is only available after the entire run completes.
- **No AGENT_LOG events** during synthesis — the frontend shows a spinner with no detail.
- **No netlist artifact exposure** — the netlist file isn't linked from the result payload.

## 2. Architecture: Same Pattern as Simulation

The simulation integration established a clean monkey-patch pattern that works with the
frozen LangGraph pipeline. **Yosys should follow the same pattern** for consistency:

```
┌─────────────────────────────────────────────────────────────────────┐
│  PipelineAdapter.run()                                              │
│                                                                     │
│  1. Monkey-patch the synthesis agent/tool function BEFORE           │
│     graph.stream() executes the synthesis node                      │
│                                                                     │
│  2. The patched function calls SynthesisExecutor with:              │
│       • Input: RTL file, top module name, liberty file path         │
│       • Callback: on_log_line → publishes AGENT_LOG via EventBus    │
│                                                                     │
│  3. Returns same shape as original _run_synthesis() dict            │
│     so the pipeline state still populates correctly.                │
│                                                                     │
│  4. Restore original function in finally block after pipeline       │
│     execution completes.                                            │
└─────────────────────────────────────────────────────────────────────┘
```

### New File: `ui/backend/services/synthesis_executor.py`

```python
"""
synthesis_executor.py — Yosys synthesis runner with real-time log streaming.

A drop-in replacement for v2_verification.mcp_tools.synthesis_server._run_synthesis()
with the same return signature but:

  - Streams each Yosys / ABC log line via a callback in real-time
  - Saves generated netlist to workspace/artifacts
  - Uses line-buffered subprocess.Popen for the yosys invocation
  - Returns parsed cell_count, area, netlist_path
"""
```

Key design:
- Generate Yosys TCL script (same content as current `_run_synthesis()`)
- Use `subprocess.Popen(["yosys", "-Q", "-s", tcl_path], stdout=..., stderr=STDOUT)`
- Each line → `on_log_line(line)` callback
- After yosys exits, parse output for `Number of cells:`, `Chip area for module`
- Copy netlist to `workspace/<design_name>/<design_name>_netlist.v`
- Return `{"netlist_path", "area", "cell_count", "warnings", "latches_inferred", "log"}`

### Monkey-Patch Target

The existing `_run_synthesis()` function needs to be replaced. Since **V2 is NOT frozen**
(unlike V1), there are two approaches:

**Option A — Monkey-patch (preferred for consistency):**

Monkey-patch `v2_verification.agents.synthesis_agent.synthesis_agent` in the pipeline
adapter's `run()` method, similar to how `simulation_agent.run_simulation` is patched.

The patched function accepts the same `state: PipelineState` argument but internally
calls `SynthesisExecutor.run()` instead of the original `_run_synthesis()`.

**Option B — Direct modification:**

Since `v2_verification` is active development (not frozen), we CAN modify
`synthesis_agent.py` and `synthesis_server.py` directly. Add an `on_log_line`
callback parameter to `_run_synthesis()`.

**Recommendation: Option A** for consistency with the simulation pattern. Both the
frontend and backend integration points are the same.

### Pipeline Adapter Changes (`ui/backend/adapters/pipeline.py`)

In the `run()` method, add a second monkey-patch block alongside the simulation patch:

```python
def run(self, job_id, benchmark, pipeline_version, ...):
    seq = 0
    start_time = time.time()

    # -- simulation monkey-patch (existing) --
    import v1_core.agents.simulation_agent as _sim_mod
    _original_run_sim = ...
    _sim_mod.run_simulation = _patched_run_sim

    # -- synthesis monkey-patch (NEW for v2/v3) --
    if pipeline_version in ("v2", "v3"):
        import v2_verification.agents.synthesis_agent as _synth_mod
        _original_synthesis = _synth_mod.synthesis_agent

        def _publish_synth_log(line: str) -> None:
            nonlocal seq
            seq += 1
            self._event_bus.publish(PipelineEvent(
                job_id=job_id,
                event_type=EventType.AGENT_LOG,
                stage="synthesis",
                message=f"[yosys] {line}",
                severity=Severity.INFO,
                payload={"log_line": line, "synth_stream": True},
                elapsed_time=time.time() - start_time,
                sequence_num=seq,
            ))

        def _patched_synthesis(state) -> dict:
            from ui.backend.services.synthesis_executor import run_synthesis
            rtl_code = state.get("rtl_code", "")
            design_name = state.get("design_name", "")
            liberty_file = settings.PROJECT_ROOT / "pdk/sky130/sky130_fd_sc_hd__tt_025C_1v80.lib"

            # Write RTL to workspace
            rtl_path = settings.WORKSPACE_DIR / design_name / f"{design_name}.v"
            rtl_path.parent.mkdir(parents=True, exist_ok=True)
            rtl_path.write_text(rtl_code)

            result = run_synthesis(
                rtl_file=str(rtl_path),
                top_module=design_name,
                liberty_file=str(liberty_file),
                on_log_line=_publish_synth_log,
            )

            # Build synthesis_report text (same format as original)
            ...
            return {**state, "netlist_path": ..., "synthesis_report": ..., ...}

        _synth_mod.synthesis_agent = _patched_synthesis
    ```

### Sequence Number Management

Synthesis log events share the same `seq` counter as pipeline events (via `nonlocal seq`),
exactly like the simulation patch. This guarantees monotonic sequence numbers.

### Update: SYNTHESIS_RESULT Payload

Add `netlist_path` and the waveform file (if generated by ABC) to the payload:

```python
"payload": {
    "cell_count": cell_count,
    "area": area,
    "netlist_path": netlist_path,
    "warnings": warnings_count,
    "latches_inferred": latches_inferred,
}
```

## 3. File Manifest

| File | Action | Purpose |
|------|--------|---------|
| `ui/backend/services/synthesis_executor.py` | **CREATE** | Streaming Yosys runner |
| `ui/backend/adapters/pipeline.py` | **MODIFY** | Add synthesis monkey-patch in `run()` |
| `ui/frontend/...` | **None** | No frontend changes needed — existing event format preserved |

## 4. Dependencies / Prerequisites

| Dependency | Status | Notes |
|-----------|--------|-------|
| `yosys` binary | ✅ `/usr/bin/yosys` v0.9 | Must be on PATH |
| Sky130 PDK `.lib` | ✅ `pdk/sky130/sky130_fd_sc_hd__tt_025C_1v80.lib` | Hardcoded path in synthesis_agent |
| ABC (bundled with yosys) | ✅ | Yosys 0.9 includes ABC for tech mapping |

## 5. Edge Cases & Safety

| Case | Handling |
|------|----------|
| Yosys not installed | Return `{"netlist_path": "", "cell_count": 0, "area": 0}` — `_parse_synthesis_report` handles empty strings |
| Liberty file missing | Catch `FileNotFoundError`, return empty results |
| Netlist not generated | Check `netlist_path.exists()` before updating state |
| Synthesis hangs | Pipeline timeout (`PIPELINE_TIMEOUT_SECONDS` = 600s) kills the thread |
| Latch inference | Already handled by `synthesis_agent` — routes to fix loop |
| Combinational design | Yosys still generates a netlist; STA reports no timing data (WNS=None) |

## 6. Testing

After implementation:

```bash
# Start backend in real mode
PIPELINE_MODE=real python -m ui.backend.main

# Submit V2 job with reference RTL + TB
curl -X POST http://localhost:8000/api/run \
  -H "Content-Type: application/json" \
  -d '{"benchmark":"alu_8bit","pipeline_version":"v2","use_reference_rtl":true,"use_reference_tb":true}'

# Verify:
# - SSE stream shows [yosys] AGENT_LOG events during synthesis
# - SYNTHESIS_RESULT with cell_count > 0
# - Netlist saved to workspace/alu_8bit/alu_8bit_netlist.v
# - Job completes with sim_passed=true + synthesis data
```

## 7. Next After Synthesis

Once synthesis streaming is working:

1. **STA integration** — Same pattern: create `sta_executor.py`, monkey-patch `sta_agent`
   in the pipeline adapter. STA uses OpenSTA (already in `v2_verification/mcp_tools/sta_server.py`).

2. **DRC / Physical flow** — Part of V3 pipeline. Uses OpenLane + KLayout.
   Requires the full physical flow infrastructure.

3. **Artifact download** — Wire netlist VCD/FST files to the existing
   `/api/run/{job_id}/artifacts/{filename}` endpoint.
