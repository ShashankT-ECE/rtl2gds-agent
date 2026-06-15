# CLAUDE.md
Claude Code reads this file automatically at the start of every session.

## Read These Files First
1. PROJECT_CONTEXT.md
2. SESSION_HANDOFF.md

## Project
Name: AI-Driven Agentic Framework for RTL-to-GDS
Owner: Shashank Tumuluri, CBIT Hyderabad ECE
Goal: Demo to Tessolve Semiconductors
LLM: DeepSeek API via v1_core/utils/model_router.py
Orchestration: LangGraph
Tool bridge: MCP

## Active Version
V1 code is FROZEN — never modify v1_core/. V2 development is active in v2_verification/.

## V1 Scope
Agents: Orchestrator, RTL Gen, Testbench, Simulation, Log Analysis, Fix
Tools: Icarus Verilog, cocotb
Memory: Trace2Skill (local JSON in skills/)
No Docker, No Yosys, No PyUVM, No OpenLane in V1.

## Code Rules
- All agents are LangGraph nodes
- All LLM calls go through v1_core/utils/model_router.py only
- All EDA tool calls go through mcp_tools/ only
- Fix Agent must check Trace2Skill before calling LLM
- Fix Agent must write to Trace2Skill after every successful fix

## Daily Startup
cd ~/projects/rtl2gds-agent
source .venv/bin/activate
claude

## Session End Checklist
1. Update SESSION_HANDOFF.md
2. git add -A && git commit -m "session: description"

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
