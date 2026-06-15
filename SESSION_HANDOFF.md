# SESSION_HANDOFF.md

## Last Updated
Date: 2026-06-15 | Session: 4 — END OF DAY

## V2 Status: PIPELINE ROBUST, REFERENCE RTLs IN PLACE

## Completed This Session
- [x] V2 pipeline crash-fixes: None-guards in timing_opt, STA router, GraphRecursionError fix
- [x] Logger Rich bracket fix: all 5 functions use escape() from rich.markup
- [x] Simulation log sanitization: brackets replaced before logger calls
- [x] Pipeline agent error wrapping: _safe_agent_call around every node
- [x] Yosys 0.9 TCL compatibility: hierarchy/proc/opt/memory/techmap sequence
- [x] OpenSTA TCL output: -o flags instead of shell > redirection
- [x] Synthesis failure guard: netlist check routes to END instead of STA
- [x] Reference RTL library: copied workspace generated RTLs to benchmarks/*/reference_rtl.v
- [x] main.py auto-detects reference_rtl.v: skips LLM RTL generation when found
- [x] v2_verification/pipeline.py accepts rtl_code param for reference RTL flow
- [x] spec_parser_agent.py created: parses spec into structured JSON
- [x] spec_analysis field added to PipelineState + get_initial_state()
- [x] spec_parser wired as FIRST node in both v1 and v2 pipelines
- [x] Reference model requirement added to testbench prompt
- [x] spec_analysis injected into RTL_PROMPT and TB_PROMPT
- [x] sync_fifo_8x16 --v2: pipeline runs clean (no crashes, sim fails on testbench quality)
- [x] uart_tx spec.txt created
- [x] apb_slave spec.txt created

## Known Issues (unresolved)
- sync_fifo_8x16 simulation fails because LLM-generated testbench has wrong expected values
  - Reference model pattern added but LLM writes both model and assertions, both agree on wrong values
  - Fix: hand-written reference testbench at benchmarks/sync_fifo_8x16/reference_tb.py
- No STA data for combinational designs (ALU) — expected, no clock port
- Yosys 28 liberty warnings on ALU synth — harmless (unsupported pin attributes in Sky130)

## Next Session Tasks (priority order)
1. Write reference testbench for sync_fifo_8x16 at benchmarks/sync_fifo_8x16/reference_tb.py
2. Run sync_fifo_8x16 --v2 with both reference RTL + reference testbench
3. Run uart_tx through V1 pipeline (LLM generates RTL + testbench)
4. Run apb_slave through V1 pipeline
5. Run uart_tx --v2 and apb_slave --v2 once simulation passes

## Commands
V1:  python3 main.py --benchmark <name>
V2:  python3 main.py --benchmark <name> --v2
V2 with reference RTL: python3 main.py --benchmark <name> --v2 --rtl benchmarks/<name>/reference_rtl.v
Auto-detect: reference_rtl.v in benchmark folder is auto-used by main.py

## Test Results
| Benchmark      | V1     | V2 Sim | V2 Synth      | V2 STA   |
|----------------|--------|--------|---------------|----------|
| alu_8bit       | PASS   | PASS   | 131 cells/778 | N/A (comb)|
| sync_fifo_8x16 | FAIL*  | -      | -             | -        |
| uart_tx        | TODO   | -      | -             | -        |
| apb_slave      | TODO   | -      | -             | -        |

*sync_fifo_8x16: sim fails on testbench quality, not RTL. Reference RTL exists but LLM testbench has wrong expected values.

## File Inventory — V2
- docker/Dockerfile.simulation, Dockerfile.synthesis
- v2_verification/mcp_tools/synthesis_server.py (Yosys 0.9 TCL)
- v2_verification/mcp_tools/sta_server.py (OpenSTA TCL)
- v2_verification/agents/synthesis_agent.py
- v2_verification/agents/sta_agent.py
- v2_verification/agents/timing_opt_agent.py
- v2_verification/pipeline.py (full conditional graph with spec_parser)
- v1_core/agents/spec_parser_agent.py (new)
- benchmarks/*/reference_rtl.v (3 designs)
- benchmarks/uart_tx/spec.txt
- benchmarks/apb_slave/spec.txt

## Cost Tracking
Check DeepSeek dashboard for session 4 total
