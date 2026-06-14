# Graph Report - .  (2026-06-14)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 148 nodes · 188 edges · 17 communities
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.59)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6f26be54`
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
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]

## God Nodes (most connected - your core abstractions)
1. `PipelineState` - 17 edges
2. `call_llm()` - 10 edges
3. `AI-Driven Agentic Framework for Automated RTL-to-GDS` - 10 edges
4. `fix_agent()` - 8 edges
5. `strip_code_fences()` - 8 edges
6. `log_analysis_agent()` - 7 edges
7. `run_pipeline()` - 7 edges
8. `LangGraph` - 7 edges
9. `rtl_gen_agent()` - 6 edges
10. `testbench_agent()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `get_stats()`  [EXTRACTED]
  main.py → v1_core/utils/trace2skill.py
- `PipelineState` --uses--> `PipelineState`  [INFERRED]
  v1_core/agents/log_analysis_agent.py → v1_core/agents/orchestrator.py
- `StateGraph` --uses--> `PipelineState`  [INFERRED]
  v1_core/pipeline.py → v1_core/agents/orchestrator.py
- `PipelineState` --uses--> `PipelineState`  [INFERRED]
  v1_core/agents/simulation_agent.py → v1_core/agents/orchestrator.py
- `8-bit ALU` --semantically_similar_to--> `8-bit ALU`  [EXTRACTED] [semantically similar]
  benchmarks/alu_8bit/spec.txt → PROJECT_CONTEXT.md

## Import Cycles
- None detected.

## Communities (17 total, 0 thin omitted)

### Community 0 - "Error Analysis & Fix"
Cohesion: 0.29
Nodes (9): get_stats(), _load(), trace2skill.py Persistent memory for the agent system. Stores successful error f, Returns skill count per category. Used in SESSION_HANDOFF updates., Store a successful fix in the skill bank.     Called by Fix Agent after every su, Retrieve relevant skills before calling the LLM.     Called by Fix Agent to chec, retrieve_skills(), _save() (+1 more)

### Community 1 - "Pipeline Orchestration"
Cohesion: 0.18
Nodes (13): get_initial_state(), Returns a fresh PipelineState for a new design run.      Args:         spec: nat, main(), main.py Entry point for the RTL-to-GDS V1 agent pipeline. Usage:   python main.p, StateGraph, build_pipeline(), PipelineState, pipeline.py Wires all V1 agents into a LangGraph state machine. This is the comp (+5 more)

### Community 2 - "RTL & Testbench Generation"
Cohesion: 0.12
Nodes (20): fix_agent(), fix_agent.py Fix Agent — LangGraph node. 1. Checks Trace2Skill hits from Log Ana, LangGraph node — fixes RTL based on error analysis.     Input state fields used:, PipelineState, orchestrator.py LangGraph state definition and pipeline orchestration for V1. Th, Shared state passed between all agents in the LangGraph pipeline.     Every agen, rtl_gen_agent.py RTL Generation Agent — LangGraph node. Takes natural language s, LangGraph node — generates Verilog RTL from natural language spec.      Input st (+12 more)

### Community 3 - "Agent Framework Tools"
Cohesion: 0.13
Nodes (15): AI-Driven Agentic Framework for RTL-to-GDS, cocotb, DeepSeek API, Fix Agent, Icarus Verilog, LangGraph, Log Analysis Agent, MCP (+7 more)

### Community 4 - "Example Designs & Technologies"
Cohesion: 0.14
Nodes (14): 8-bit ALU, AI-Driven Agentic Framework for Automated RTL-to-GDS, 8-bit ALU, cocotb, DeepSeek API, Icarus Verilog, LangGraph, MCP (+6 more)

### Community 5 - "Pipeline State & Simulation"
Cohesion: 0.20
Nodes (8): Cost Tracking, Current Sprint, Known Limitations (acceptable for V1), Last Updated, Next Session, Test Results, Trace2Skill Stats, V1 Status: DONE

### Community 6 - "Simulation Server & Logging"
Cohesion: 0.12
Nodes (9): simulation_agent.py Simulation Agent — LangGraph node. Writes RTL and testbench, LangGraph node — runs Icarus Verilog simulation.     Input state fields used: rt, simulation_agent(), simulation_server.py MCP Tool — runs cocotb 2.x simulation using Makefile approa, Run cocotb simulation using cocotb 2.x Makefile approach.      Args:         rtl, run_simulation(), logger.py Simple logger for the RTL-to-GDS agent pipeline. All agents use this —, model_router.py Single point of contact for all DeepSeek API calls. No agent sho (+1 more)

### Community 7 - "Design Examples & Tools"
Cohesion: 0.40
Nodes (5): alu_8bit, cocotb, Icarus Verilog, sync_fifo_8x16, Trace2Skill

### Community 8 - "EDA Tools & Docker"
Cohesion: 0.67
Nodes (4): Docker, OpenSTA, PyUVM, Yosys

### Community 9 - "Project Context Files"
Cohesion: 0.67
Nodes (3): Claude Code, PROJECT_CONTEXT.md, SESSION_HANDOFF.md

### Community 14 - "Community 14"
Cohesion: 0.22
Nodes (7): Active Version, Code Rules, Daily Startup, Project, Read These Files First, Session End Checklist, V1 Scope

### Community 15 - "Community 15"
Cohesion: 0.25
Nodes (6): Architecture Decisions — DO NOT CHANGE, Benchmark Designs, DeepSeek Model Policy, Excluded from V1 — Do Not Add, Identity, Version Status

### Community 16 - "Community 16"
Cohesion: 0.33
Nodes (6): _guess_category(), log_analysis_agent(), log_analysis_agent.py Log Analysis Agent — LangGraph node. Parses simulation log, LangGraph node — classifies simulation errors.     Input state fields used: sim_, Guess skill category from design name., PipelineState

## Knowledge Gaps
- **47 isolated node(s):** `Read These Files First`, `Project`, `Active Version`, `V1 Scope`, `Code Rules` (+42 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PipelineState` connect `RTL & Testbench Generation` to `Community 16`, `Pipeline Orchestration`, `Simulation Server & Logging`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `fix_agent()` connect `RTL & Testbench Generation` to `Community 16`, `Error Analysis & Fix`, `Pipeline Orchestration`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Why does `store_skill()` connect `Error Analysis & Fix` to `RTL & Testbench Generation`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `PipelineState` (e.g. with `StateGraph` and `PipelineState`) actually correct?**
  _`PipelineState` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `main.py Entry point for the RTL-to-GDS V1 agent pipeline. Usage:   python main.p`, `fix_agent.py Fix Agent — LangGraph node. 1. Checks Trace2Skill hits from Log Ana`, `LangGraph node — fixes RTL based on error analysis.     Input state fields used:` to the rest of the system?**
  _76 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `RTL & Testbench Generation` be split into smaller, more focused modules?**
  _Cohesion score 0.12333333333333334 - nodes in this community are weakly interconnected._
- **Should `Agent Framework Tools` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._