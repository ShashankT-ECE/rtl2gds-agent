# V2 Validation Plan

## Overview
Validate the V2 pipeline reliability across 5 benchmarks. Each benchmark runs through simulation → fix loop → synthesis → STA. Bug injection tests evaluate the fix loop. Results determine V2 readiness for V3 (OpenLane) and Tessolve demo.

## 1. Benchmarks Under Test
| # | Benchmark | Type | Design Size | Expected Behavior |
|---|-----------|------|-------------|-------------------|
| 1 | alu_8bit | Combinational | 131 cells | All ops correct, zero flag |
| 2 | sync_fifo_8x16 | Sequential | 648 cells | Full/empty/count correct |
| 3 | fsm_traffic_light | FSM | 10 cells | State timing correct |
| 4 | uart_tx | Sequential/FSM | 180 cells | Serial TX correct |
| 5 | apb_slave | Protocol | 527 cells | APB read/write correct |

## 2. Metrics to Collect
| Category | Metric | Collection Method |
|----------|--------|-------------------|
| Pass/Fail | sim_passed | Pipeline state |
| Runtime | wall clock time | `time` command |
| Simulation Iterations | iteration count | Pipeline state |
| Fix Iterations | iteration count (when fix loop engaged) | Pipeline state |
| Synthesis Success | netlist_path non-empty | Pipeline state |
| Cells | cell_count | Synthesis report |
| Area | area | Synthesis report |
| STA Success | timing_met | Pipeline state |
| Slack | wns, tns | Pipeline state |
| Convergence | stuck_count | Pipeline state |
| Error Patterns | error_analysis.ERROR_TYPE | Pipeline state |
| Warnings | synthesis_report warnings | Synthesis output |
| Latches | latches_inferred | Synthesis report |

## 3. Success Criteria
| Criterion | Threshold |
|-----------|-----------|
| V1 Pipeline Pass Rate | ≥ 90% (23/25 runs) |
| V2 Pipeline Pass Rate | ≥ 85% (21/25 runs) |
| Average Fix Iterations | ≤ 3 |
| Max Iterations Used | ≤ 5 (pipeline limit) |
| Synthesis Success Rate | ≥ 95% |
| STA Success Rate (non-combinational) | ≥ 90% |
| Convergence Trigger Rate | ≤ 10% (stuck_count ≥ 2) |
| Bug Detection Rate | ≥ 80% (8/10 bugs) |
| Bug Fix Rate | ≥ 50% (5/10 bugs fixed within loop) |

## 4. Failure Classification
| Class | Code | Description | Root Cause |
|-------|------|-------------|------------|
| RTL Gen Issue | RTL | Bad RTL generated | LLM quality |
| Testbench Issue | TB | Bad testbench | LLM quality / reference model |
| Simulation Issue | SIM | Sim crash/timeout | Icarus / cocotb / infrastructure |
| Fix-Agent Issue | FIX | Fix made things worse | LLM / Trace2Skill |
| Synthesis Issue | SYNTH | Yosys failure / latches | RTL quality / Liberty |
| STA Issue | STA | OpenSTA crash / no data | Timing constraints / infrastructure |
| Infrastructure | INFRA | Import error / MCP error | Python / environment |
| LLM Response | LLM | JSON parse fail / wrong format | Model quality |
| Convergence | CONV | stuck_count ≥ 2 | Repeated identical error |

## 5. Test Matrix
| Test ID | Benchmark | Pipeline | Iterations | Bug File |
|---------|-----------|----------|------------|----------|
| R01-R05 | alu_8bit | V2 | 5 | None |
| R06-R10 | sync_fifo_8x16 | V2 | 5 | None |
| R11-R15 | fsm_traffic_light | V2 | 5 | None |
| R16-R20 | uart_tx | V2 | 5 | None |
| R21-R25 | apb_slave | V2 | 5 | None |
| B01 | alu_8bit | V2 | 1 | bug_001_wrong_opcode.v |
| B02 | alu_8bit | V2 | 1 | bug_002_missing_zero_flag.v |
| B03 | sync_fifo_8x16 | V2 | 1 | bug_001_wrong_full_flag.v |
| B04 | sync_fifo_8x16 | V2 | 1 | bug_002_no_reset.v |
| B05 | fsm_traffic_light | V2 | 1 | bug_001_wrong_count.v |
| B06 | fsm_traffic_light | V2 | 1 | bug_002_wrong_transition.v |
| B07 | uart_tx | V2 | 1 | bug_001_wrong_bit_order.v |
| B08 | uart_tx | V2 | 1 | bug_002_missing_stop_bit.v |
| B09 | apb_slave | V2 | 1 | bug_001_wrong_address.v |
| B10 | apb_slave | V2 | 1 | bug_002_pslverr_inverted.v |

## 6. Execution Strategy
1. Run clean V2 pipeline × 5 per benchmark (25 runs total)
2. Run bug-injected V2 pipeline × 1 per bug file (10 runs total)
3. Collect structured results per run
4. Analyze failure modes and patterns
5. Produce final report with readiness assessment

## 7. Environment
- Python 3.10
- Icarus Verilog 11.0
- cocotb 2.0.1
- Yosys 0.9
- OpenSTA 3.1.0
- PDK: Sky130
- LLM: DeepSeek via model_router.py
