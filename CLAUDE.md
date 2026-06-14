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
V1 only. Never add V2/V3 features here.

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
