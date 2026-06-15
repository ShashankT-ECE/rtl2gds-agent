# Graph Report - rtl2gds-agent  (2026-06-15)

## Corpus Check
- 48 files · ~27,977 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 353 nodes · 459 edges · 32 communities (27 shown, 5 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 21 edges (avg confidence: 0.6)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4a572744`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Error Analysis & Fix|Error Analysis & Fix]]
- [[_COMMUNITY_Pipeline Orchestration|Pipeline Orchestration]]
- [[_COMMUNITY_RTL & Testbench Generation|RTL & Testbench Generation]]
- [[_COMMUNITY_Agent Framework Tools|Agent Framework Tools]]
- [[_COMMUNITY_Example Designs & Technologies|Example Designs & Technologies]]
- [[_COMMUNITY_Pipeline State & Simulation|Pipeline State & Simulation]]
- [[_COMMUNITY_Simulation Server & Logging|Simulation Server & Logging]]
- [[_COMMUNITY_Design Examples & Tools|Design Examples & Tools]]
- [[_COMMUNITY_EDA Tools & Docker|EDA Tools & Docker]]
- [[_COMMUNITY_Project Context Files|Project Context Files]]
- [[_COMMUNITY_Python Package Init|Python Package Init]]
- [[_COMMUNITY_Python Package Init|Python Package Init]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]

## God Nodes (most connected - your core abstractions)
1. `PipelineState` - 28 edges
2. `Graphify Integration Results` - 15 edges
3. `call_llm()` - 14 edges
4. `strip_code_fences()` - 10 edges
5. `AI-Driven Agentic Framework for Automated RTL-to-GDS` - 10 edges
6. `fix_agent()` - 9 edges
7. `2. Commands Executed` - 9 edges
8. `log_analysis_agent()` - 8 edges
9. `6. V1 Agent Analysis` - 8 edges
10. `apb_reset()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `PipelineState` --uses--> `PipelineState`  [INFERRED]
  v2_verification/agents/sta_agent.py → v1_core/agents/orchestrator.py
- `PipelineState` --uses--> `PipelineState`  [INFERRED]
  v2_verification/agents/synthesis_agent.py → v1_core/agents/orchestrator.py
- `StateGraph` --uses--> `PipelineState`  [INFERRED]
  v2_verification/pipeline.py → v1_core/agents/orchestrator.py
- `main()` --calls--> `Path`  [INFERRED]
  main.py → v2_verification/mcp_tools/sta_server.py
- `PipelineState` --uses--> `PipelineState`  [INFERRED]
  v2_verification/agents/timing_opt_agent.py → v1_core/agents/orchestrator.py

## Import Cycles
- None detected.

## Communities (32 total, 5 thin omitted)

### Community 0 - "Error Analysis & Fix"
Cohesion: 0.05
Nodes (41): 10. Recommendations, 11. Claude Code Integration, 12. V2 Handoff, 1. Dependencies Installed, 3. Generated Files, 4. Graph Statistics, 5. Python Modules Discovered, 6.1 Orchestrator (+33 more)

### Community 1 - "Pipeline Orchestration"
Cohesion: 0.13
Nodes (18): get_initial_state(), orchestrator.py LangGraph state definition and pipeline orchestration for V1. Th, Returns a fresh PipelineState for a new design run.      Args:         spec: nat, main(), main.py Entry point for the RTL-to-GDS V1 agent pipeline. Usage:   python main.p, get_stats(), Returns skill count per category. Used in SESSION_HANDOFF updates., build_pipeline() (+10 more)

### Community 2 - "RTL & Testbench Generation"
Cohesion: 0.07
Nodes (40): fix_agent(), fix_agent.py Fix Agent — LangGraph node. 1. Checks Trace2Skill hits from Log Ana, LangGraph node — fixes RTL based on error analysis.     Input state fields used:, _guess_category(), log_analysis_agent(), log_analysis_agent.py Log Analysis Agent — LangGraph node. Parses simulation log, LangGraph node — classifies simulation errors.     Input state fields used: sim_, Guess skill category from design name. (+32 more)

### Community 3 - "Agent Framework Tools"
Cohesion: 0.13
Nodes (15): AI-Driven Agentic Framework for RTL-to-GDS, cocotb, DeepSeek API, Fix Agent, Icarus Verilog, LangGraph, Log Analysis Agent, MCP (+7 more)

### Community 4 - "Example Designs & Technologies"
Cohesion: 0.14
Nodes (14): 8-bit ALU, AI-Driven Agentic Framework for Automated RTL-to-GDS, 8-bit ALU, cocotb, DeepSeek API, Icarus Verilog, LangGraph, MCP (+6 more)

### Community 5 - "Pipeline State & Simulation"
Cohesion: 0.15
Nodes (11): All 5 Benchmarks: V1 PASS + V2 COMPLETE, Bugs Fixed This Session, Commands, Complete Results, Completed This Session, Core Benchmarks, Cost Tracking, Known Issues (+3 more)

### Community 6 - "Simulation Server & Logging"
Cohesion: 0.07
Nodes (25): simulation_agent.py Simulation Agent — LangGraph node. Writes RTL and testbench, LangGraph node — runs Icarus Verilog simulation.     Input state fields used: rt, simulation_agent(), sta_agent.py STA (Static Timing Analysis) Agent — LangGraph node. Runs OpenSTA t, LangGraph node — runs OpenSTA static timing analysis on the synthesized netlist., sta_agent(), simulation_server.py MCP Tool — runs cocotb 2.x simulation using Makefile approa, Run cocotb simulation using cocotb 2.x Makefile approach.      Args:         rtl (+17 more)

### Community 7 - "Design Examples & Tools"
Cohesion: 0.40
Nodes (5): alu_8bit, cocotb, Icarus Verilog, sync_fifo_8x16, Trace2Skill

### Community 8 - "EDA Tools & Docker"
Cohesion: 0.67
Nodes (4): Docker, OpenSTA, PyUVM, Yosys

### Community 9 - "Project Context Files"
Cohesion: 0.67
Nodes (3): Claude Code, PROJECT_CONTEXT.md, SESSION_HANDOFF.md

### Community 10 - "Python Package Init"
Cohesion: 0.18
Nodes (17): apb_read(), apb_reset(), apb_write(), reference_tb.py Hand-written reference testbench for APB Slave (apb_slave). Grou, Write different values to all 4 registers, read all back., Read from invalid address 0xFF — verify PSLVERR=1., Read from all registers before writing — verify 0 (reset value)., APB write transfer to given word-aligned address. (+9 more)

### Community 11 - "Python Package Init"
Cohesion: 0.16
Nodes (17): reference_tb.py Hand-written reference testbench for synchronous FIFO (sync_fifo, Write the 15th entry and verify full=1., After full=1, attempt another write. Verify:       - full stays 1       - count, Write 15 entries, read all 15 back, verify data order matches write order.     A, Test simultaneous read+write when FIFO has entries.     Write new data while rea, Write one word to FIFO. Drives signals AFTER RisingEdge., Read one word from FIFO. Returns data after it's stable.      NOTE: The Timer(1p, After reset, verify:       - empty=1, full=0, count=0       - wr_en, rd_en, din (+9 more)

### Community 14 - "Community 14"
Cohesion: 0.20
Nodes (8): Active Version, Code Rules, Daily Startup, graphify, Project, Read These Files First, Session End Checklist, V1 Scope

### Community 15 - "Community 15"
Cohesion: 0.25
Nodes (6): Architecture Decisions — DO NOT CHANGE, Benchmark Designs, DeepSeek Model Policy, Excluded from V1 — Do Not Add, Identity, Version Status

### Community 16 - "Community 16"
Cohesion: 0.13
Nodes (15): check_state(), do_reset(), reference_tb.py Hand-written reference testbench for traffic light FSM. Ground t, Verify GREEN state holds for GREEN_COUNT=19 cycles,     then transitions to YELL, Verify YELLOW state holds for YELLOW_COUNT=4 cycles,     then transitions back t, Assert async reset, wait 3 clocks, deassert., Read state_out after a RisingEdge with VPI safety delay., Wait for RisingEdge, then check state_out == expected. (+7 more)

### Community 17 - "Community 17"
Cohesion: 0.19
Nodes (15): reference_tb.py Hand-written reference testbench for UART Transmitter (uart_tx)., Send 0xFF: verify all data bits high., Verify tx_busy=1 during transmission and 0 after completion., Send a byte through the UART TX by pulsing tx_start., Monitor the tx line and return the received byte.     Waits for start bit, sampl, After reset, verify tx=1 and tx_busy=0., Send 0x55 (alternating 01010101), verify each bit on tx line at correct baud tim, Send 0x00: verify start bit low, all data bits low, stop bit high. (+7 more)

### Community 18 - "Community 18"
Cohesion: 0.19
Nodes (13): build_v2_pipeline(), PipelineState, StateGraph, pipeline.py V2 LangGraph pipeline extending V1 with synthesis and static timing, Router after the STA node.      Returns the destination label:       "end", Router after the synthesis node.      If synthesis failed (no netlist, zero cell, Build and compile the V2 LangGraph pipeline.      Args:         skip_rtl_gen: If, Wrap an agent call in try/except so a crash doesn't kill the pipeline. (+5 more)

### Community 19 - "Community 19"
Cohesion: 0.18
Nodes (11): synthesis_agent.py Synthesis Agent — LangGraph node for V2 RTL-to-GDS pipeline., LangGraph node — runs Yosys synthesis on the generated RTL code.      Input stat, synthesis_agent(), main(), synthesis_server.py MCP Tool — wraps Yosys synthesis via TCL scripts for V2 RTL-, Run Yosys synthesis on the given RTL file.          Args:             rtl_file:, Run the MCP server over stdio., Execute Yosys synthesis and return parsed results.      This is deliberately a p (+3 more)

### Community 20 - "Community 20"
Cohesion: 0.23
Nodes (11): reference_tb.py Hand-written reference testbench for 8-bit ALU. Ground truth — n, Verify zero_flag=1 for operations that produce Y=0x00.     Tests each opcode wit, Pure Python reference model of the ALU.      Args:         A: 8-bit input A, Verify zero_flag=0 for operations that produce Y != 0x00., Test all 8 opcodes with boundary value combinations.     Boundary values: 0x00,, Test additional edge cases not covered by boundary value matrix:     - Alternati, reference_model(), test_additional_edge_cases() (+3 more)

### Community 21 - "Community 21"
Cohesion: 0.22
Nodes (9): 2.1 Initial extraction (default mode), 2.2 Deep mode extraction (`--mode deep`), 2.3 Force update (no LLM, re-extract AST only), 2.4 Cluster analysis and report, 2.5 Call-flow HTML, 2.6 Collapsible tree visualization, 2.7 Claude Code integration, 2.8 Graph health checks (+1 more)

## Knowledge Gaps
- **94 isolated node(s):** `alu_8bit`, `apb_slave`, `fsm_traffic_light`, `sync_fifo_8x16`, `uart_tx` (+89 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PipelineState` connect `RTL & Testbench Generation` to `Pipeline Orchestration`, `Community 18`, `Community 19`, `Simulation Server & Logging`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Why does `Graphify Integration Results` connect `Error Analysis & Fix` to `Community 21`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Why does `fix_agent()` connect `RTL & Testbench Generation` to `Pipeline Orchestration`, `Community 18`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `PipelineState` (e.g. with `PipelineState` and `PipelineState`) actually correct?**
  _`PipelineState` has 13 INFERRED edges - model-reasoned connections that need verification._
- **What connects `alu_8bit`, `reference_tb.py Hand-written reference testbench for 8-bit ALU. Ground truth — n`, `Pure Python reference model of the ALU.      Args:         A: 8-bit input A` to the rest of the system?**
  _188 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Error Analysis & Fix` be split into smaller, more focused modules?**
  _Cohesion score 0.047619047619047616 - nodes in this community are weakly interconnected._
- **Should `Pipeline Orchestration` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._