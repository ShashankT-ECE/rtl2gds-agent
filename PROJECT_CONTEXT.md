# PROJECT_CONTEXT.md

## Identity
Name: AI-Driven Agentic Framework for Automated RTL-to-GDS
Owner: Shashank Tumuluri, CBIT Hyderabad ECE (B.Tech 2023-2027)
GitHub: github.com/ShashankT-ECE/rtl-to-gds-agent
Primary goal: Demo to Tessolve Semiconductors → full-time offer
Secondary goal: IEEE/DAC/ICCAD publication

## Architecture Decisions — DO NOT CHANGE
- Orchestration: LangGraph
- LLM: DeepSeek API (model_router.py selects model per task)
- Tool Bridge: MCP (Model Context Protocol)
- Simulation: Icarus Verilog + cocotb
- Memory: Trace2Skill (custom JSON in skills/ folder — not an external package)

## Excluded from V1 — Do Not Add
PyUVM, Yosys, OpenSTA, OpenLane, Docker, Sky130, KLayout, Magic

## Version Status
V1 Core Loop: IN PROGRESS
V2 Verification + Synthesis: NOT STARTED
V3 Physical Flow: NOT STARTED

## DeepSeek Model Policy
Simple tasks, formatting, log classification → deepseek-v4-flash
RTL generation, testbench generation, log analysis → deepseek-v4-flash
Root cause reasoning, complex multi-hop errors → deepseek-v4-flash with thinking mode enabled
Architecture decisions, hardest problems only → deepseek-v4-pro

Use deepseek-v4-pro sparingly — only when flash is clearly not good enough.
deepseek-chat and deepseek-reasoner are deprecated July 24 2026, do not use them.

## Benchmark Designs
1. 8-bit ALU — manual ground truth, combinational, located in benchmarks/alu_8bit/
2. Sync FIFO 8x16 — manual ground truth, sequential, located in benchmarks/sync_fifo_8x16/
