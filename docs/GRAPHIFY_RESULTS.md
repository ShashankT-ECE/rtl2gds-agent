# Graphify Integration Results

> Generated: 2026-06-14 | Graphify v0.8.39 | Repo: rtl2gds-agent V1

---

## 1. Dependencies Installed

| Package | Version | Location | Purpose |
|---------|---------|----------|---------|
| `openai` | 2.41.1 | uv tool `graphifyy` env | DeepSeek backend (OpenAI-compatible API) |
| `httpx` | 0.28.1 | uv tool `graphifyy` env | HTTP transport for LLM calls |
| `pydantic` | 2.13.4 | uv tool `graphifyy` env | Response validation |
| `tqdm` | 4.68.2 | uv tool `graphifyy` env | Progress bars during extraction |

**No project-level packages were added.** All Graphify dependencies are isolated in the uv-managed tool environment at `~/.local/share/uv/tools/graphifyy/`. The project `.venv` is untouched.

### Install Command

```bash
uv tool install graphifyy --with openai
```

---

## 2. Commands Executed

### 2.1 Initial extraction (default mode)
```bash
graphify extract . --backend=deepseek
```
- Result: 121 nodes, 164 edges, 14 communities
- Semantic extraction: 5 doc files processed via DeepSeek
- Cost: ~$0.0023 (2,167 in / 7,024 out tokens)

### 2.2 Deep mode extraction (`--mode deep`)
```bash
graphify extract . --backend=deepseek --mode deep
```
- All files cached; incremental scan of 1 changed file
- Required `--force` to fully re-extract

### 2.3 Force update (no LLM, re-extract AST only)
```bash
GRAPHIFY_FORCE=1 graphify update .
```
- Improved coverage: **148 nodes, 188 edges, 17 communities**

### 2.4 Cluster analysis and report
```bash
graphify cluster-only .
```

### 2.5 Call-flow HTML
```bash
graphify export callflow-html .
```

### 2.6 Collapsible tree visualization
```bash
graphify tree .
```

### 2.7 Claude Code integration
```bash
graphify claude install
```

### 2.8 Graph health checks
```bash
graphify diagnose multigraph             # Edge-collapse diagnostic
graphify path "main.py" "fix_agent.py"   # Shortest path analysis
graphify explain "<agent_name>"          # Per-agent neighbor analysis
graphify query "<question>"              # BFS traversal queries
graphify affected "PipelineState"        # Impact chain analysis
```

---

## 3. Generated Files

| File | Path | Size | Description |
|------|------|------|-------------|
| `graph.json` | `graphify-out/graph.json` | 108 KB | Full knowledge graph (148 nodes, 188 edges) |
| `GRAPH_REPORT.md` | `graphify-out/GRAPH_REPORT.md` | 8.1 KB | Cluster report with god nodes, communities, knowledge gaps |
| `graph.html` | `graphify-out/graph.html` | 119 KB | Force-directed graph visualization (D3.js) |
| `GRAPH_TREE.html` | `graphify-out/GRAPH_TREE.html` | 26 KB | D3 collapsible tree visualization |
| `rtl2gds-agent-callflow.html` | `graphify-out/rtl2gds-agent-callflow.html` | 87 KB | Mermaid-based architecture/call-flow diagrams |
| `manifest.json` | `graphify-out/manifest.json` | 5 KB | Per-file scan manifest with AST/semantic hashes |
| `.graphify_analysis.json` | `graphify-out/.graphify_analysis.json` | 8.5 KB | Machine-readable analysis (communities, betweenness) |
| `.graphify_labels.json` | `graphify-out/.graphify_labels.json` | 0.5 KB | Named community labels |
| `.graphify_semantic_marker` | `graphify-out/.graphify_semantic_marker` | 23 B | Semantic extraction marker |
| `.graphify_root` | `graphify-out/.graphify_root` | 1 B | Root directory marker |

### Claude Integration Changes
| File | Change |
|------|--------|
| `CLAUDE.md` | Added `## graphify` section with knowledge graph usage rules |
| `.claude/settings.json` | Added PreToolUse hooks for Bash (grep/find) and Read/Glob (source files) |

---

## 4. Graph Statistics

### Node Counts
| Category | Count |
|----------|-------|
| **Total nodes** | **148** |
| Code entities | 85 |
| Rationale nodes (docstrings) | 29 |
| Document nodes | 29 |
| Concept nodes | 5 |

### Edge Counts
| Type | Count |
|------|-------|
| **Total edges** | **188** |
| `contains` | 50 |
| `references` | 37 |
| `rationale_for` | 29 |
| `imports` | 25 |
| `calls` | 20 |
| `imports_from` | 10 |
| `uses` | 7 |
| `conceptually_related_to` | 7 |
| `semantically_similar_to` | 2 |
| `inherits` | 1 |

### Extraction Quality
| Metric | Value |
|--------|-------|
| EXTRACTED edges | 94% (177) |
| INFERRED edges | 6% (11) |
| AMBIGUOUS edges | 0% (0) |
| INFERRED confidence | 0.59 avg |
| Import cycles | **None detected** |
| Post-build graph type | Undirected Graph (188 edges preserved) |
| Same-endpoint collapsed edges | 0 (no multigraph issues) |

### Communities
| Metric | Value |
|--------|-------|
| Communities | 17 |
| Largest community | Community 2 (25 nodes) — "RTL & Testbench Generation" |
| Most cohesive | Community 8 (0.67) — "EDA Tools & Docker" |
| Least cohesive | Community 6 (0.12) — "Simulation Server & Logging" |

### Top God Nodes (Most Connected)
| Node | Degree | Role |
|------|--------|------|
| `PipelineState` | 17 | Cross-community bridge |
| `call_llm()` | 10 | Central LLM dispatch (model_router.py) |
| `AI-Driven Agentic Framework...` | 10 | Project identity node |
| `fix_agent()` | 8 | Error correction hub |
| `strip_code_fences()` | 8 | Utility shared across agents |
| `log_analysis_agent()` | 7 | Error classification |
| `run_pipeline()` | 7 | Pipeline entry point |
| `LangGraph` | 7 | Orchestration framework |
| `rtl_gen_agent()` | 6 | RTL generation |
| `testbench_agent()` | 6 | Testbench generation |

---

## 5. Python Modules Discovered

17 Python modules across the V1 codebase:

```
main.py                                      Entry point
v1_core/__init__.py                          Core package
v1_core/agents/__init__.py                   Agents package
v1_core/agents/fix_agent.py                  Fix Agent
v1_core/agents/log_analysis_agent.py         Log Analysis Agent
v1_core/agents/orchestrator.py               Orchestrator (state + init)
v1_core/agents/rtl_gen_agent.py              RTL Generation Agent
v1_core/agents/simulation_agent.py           Simulation Agent
v1_core/agents/testbench_agent.py            Testbench Agent
v1_core/mcp_tools/__init__.py                MCP tools package
v1_core/mcp_tools/simulation_server.py       Simulation MCP tool
v1_core/pipeline.py                          LangGraph pipeline wiring
v1_core/tests/__init__.py                    Tests package
v1_core/utils/__init__.py                    Utilities (strip_code_fences)
v1_core/utils/logger.py                      Logging utility
v1_core/utils/model_router.py                DeepSeek API router
v1_core/utils/trace2skill.py                 Trace2Skill memory system
```

---

## 6. V1 Agent Analysis

### 6.1 Orchestrator
- **Node**: `orchestrator.py` (degree 3)
- **Community**: Community 2 — "RTL & Testbench Generation"
- **Key functions**: `get_initial_state()`, `PipelineState` definition
- **Connections**: Contains `PipelineState` definition and `get_initial_state()`
- **Caveat**: Lower degree because orchestrator.py is primarily a state definition file (the actual orchestration logic lives in pipeline.py)

### 6.2 RTL Generation Agent
- **Node**: `rtl_gen_agent()` (degree 6)
- **Community**: Community 2 — "RTL & Testbench Generation"
- **Source**: `v1_core/agents/rtl_gen_agent.py`
- **Connections**:
  - Imported by `pipeline.py` (imports)
  - Calls `call_llm()` (model_router.py)
  - Calls `strip_code_fences()` (utils/__init__.py)
  - References `PipelineState` (orchestrator.py)
- **Verdict**: Correctly captured

### 6.3 Testbench Agent
- **Node**: `testbench_agent()` (degree 6)
- **Community**: Community 2 — "RTL & Testbench Generation"
- **Source**: `v1_core/agents/testbench_agent.py`
- **Connections**:
  - Imported by `pipeline.py` (imports)
  - Calls `call_llm()` (model_router.py)
  - Calls `strip_code_fences()` (utils/__init__.py)
  - References `PipelineState` (orchestrator.py)
- **Verdict**: Correctly captured

### 6.4 Simulation Agent
- **Node**: `simulation_agent()` (degree 5)
- **Community**: Community 6 — "Simulation Server & Logging"
- **Source**: `v1_core/agents/simulation_agent.py`
- **Connections**:
  - Imported by `pipeline.py` (imports)
  - Calls `run_simulation()` (simulation_server.py)
  - References `PipelineState` (orchestrator.py)
- **Verdict**: Correctly captured, has its own community (simulation concern separation)

### 6.5 Log Analysis Agent
- **Node**: `log_analysis_agent()` (degree 7)
- **Community**: Community 16 — unnamed (0.33 cohesion)
- **Source**: `v1_core/agents/log_analysis_agent.py`
- **Connections**:
  - Imported by `pipeline.py` (imports)
  - Calls `call_llm()` (model_router.py)
  - Calls `_guess_category()` (internal)
  - Calls `retrieve_skills()` (trace2skill.py)
  - References `PipelineState` (orchestrator.py)
- **Verdict**: Correctly captured, bridges Error Analysis and Pipeline communities

### 6.6 Fix Agent
- **Node**: `fix_agent()` (degree 8)
- **Community**: Community 2 — "RTL & Testbench Generation" (partially)
- **Source**: `v1_core/agents/fix_agent.py`
- **Connections**:
  - Imported by `pipeline.py` (imports)
  - Calls `call_llm()` (model_router.py)
  - Calls `strip_code_fences()` (utils/__init__.py)
  - Calls `store_skill()` (trace2skill.py)
  - Calls `_guess_category()` (log_analysis_agent.py)
  - References `PipelineState` (orchestrator.py)
- **Verdict**: Correctly captured, highest agent degree (most connected)

### V1 Architecture Mapping
```
main.py
  └─ run_pipeline()
       └─ StateGraph
            ├─ rtl_gen_agent() ──→ call_llm() ──→ strip_code_fences()
            ├─ testbench_agent() ──→ call_llm() ──→ strip_code_fences()
            ├─ simulation_agent() ──→ run_simulation()
            ├─ log_analysis_agent() ──→ call_llm() ──→ retrieve_skills()
            │                              └──→ _guess_category()
            └─ fix_agent() ──→ call_llm() ──→ store_skill()
                               └──→ strip_code_fences()
                               └──→ _guess_category()
```

All functions, imports, and call relationships are correctly captured in the graph.

---

## 7. Verilog/SystemVerilog Coverage

**0 Verilog/SystemVerilog entities found in the graph.**

This is **expected and correct** for the current repo state:

- Graphify fully supports `.v`, `.sv`, `.svh` extensions in `CODE_EXTENSIONS`
- The Verilog files (`alu.v`, `fifo.v`) **do not exist in the repo** — they are generated at runtime by the pipeline
- Only spec files (`spec.txt`) are checked into version control
- Once the pipeline generates Verilog files, running `graphify update .` will pick them up

---

## 8. Graphify Correctness Assessment

### What the graph gets right:
- ✅ All 6 V1 agents captured as distinct nodes with correct connections
- ✅ All 17 Python source files discovered
- ✅ Pipeline dependency chain correctly mapped (main → pipeline → agents → utils)
- ✅ `call_llm()` correctly identified as central hub (10 edges, highest degree after PipelineState)
- ✅ Trace2Skill memory system correctly linked to Fix Agent and Log Analysis Agent
- ✅ No false import cycles detected
- ✅ DeepSeek API, LangGraph, cocotb, Icarus Verilog captured as key infrastructure nodes

### What the graph gets partially:
- ⚠️ `orchestrator.py` has degree 3 (low) — this is because orchestrator defines PipelineState but pipeline.py does the actual orchestration weaving
- ⚠️ Community structure merges Fix Agent into "RTL & Testbench Generation" community (Community 2) rather than "Error Analysis & Fix" (Community 0) — the graph reflects that fix_agent.py imports from the same utilities as the generation agents

### What could be improved:
- 🔲 Semantic extraction depth — only doc/spec files got LLM-based extraction; code files get AST-only extraction
- 🔲 Inferred edges (11) have moderate confidence (0.59) — manual verification recommended
- 🔲 47 isolated nodes suggest some connections are missed (mostly doc-derived metadata nodes)

---

## 9. Limitations

1. **No runtime-generated code**: Verilog files generated by the pipeline are not in the repo, so graphify can't capture them until they exist
2. **AST-only for Python code**: Graphify does not apply LLM-based semantic extraction to `.py` files — it uses tree-sitter AST parsing, which captures calls and imports but not higher-level semantic relationships between agents
3. **Doc-heavy sections produce weakly-connected nodes**: The CLAUDE.md, PROJECT_CONTEXT.md, and SESSION_HANDOFF.md produce many metadata nodes with ≤1 connection (47 isolated nodes)
4. **No Makefile support**: The benchmark Makefiles are not in CODE_EXTENSIONS, so build configuration relationships aren't captured
5. **Community labeling misses 3 communities**: Communities 14, 15, 16 are not named (labeled "Community N" rather than a meaningful name)
6. **Undirected graph**: The post-build graph is undirected — direction is preserved only in edge metadata, not in the graph algorithm itself

---

## 10. Recommendations

### For V2 Development
1. **Embed graphify in the daily workflow**: Run `graphify update .` after each significant code change (AST-only, free)
2. **Periodic semantic refresh**: Run `graphify extract . --mode deep --force` weekly to capture evolving semantics
3. **Use `graphify query` before codebase exploration**: This is now enforced by the PreToolUse hooks installed via `graphify claude install`
4. **Consult GRAPH_REPORT.md for architecture reviews**: The god nodes and community structure give an instant overview
5. **Track graph diffs in code review**: Use `graphify path` and `graphify affected` to understand impact of changes
6. **Verify generated RTL/testbench appears**: After running the pipeline, check `graphify update .` picks up the generated `.v` files

### For Repository Organization
1. **Add inline documentation for key connections**: Higher docstring quality improves semantic extraction
2. **Use consistent naming conventions**: The "AI-Driven Agentic Framework" node appears with two different suffix variants (with/without "Automated"), causing duplicate nodes
3. **Reduce isolated nodes**: Add cross-references between markdown files and code modules

---

## 11. Claude Code Integration

### What was installed

The `graphify claude install` command made two changes:

**A. CLAUDE.md section** — Added a `## graphify` section with four rules:
1. Before codebase questions, run `graphify query "<question>"`
2. For navigation, check `graphify-out/wiki/index.md` (if exists)
3. For broad architecture review, read `GRAPH_REPORT.md`
4. After code changes, run `graphify update .`

**B. PreToolUse hooks** — Added to `.claude/settings.json`:
1. **Bash hook** (grep/find/rg) — Prompts Claude to query graphify before raw searching
2. **Read/Glob hook** (source files) — Prompts Claude to query graphify before reading source files

### Impact
- ✅ **Non-breaking**: Hooks are advisory (never block), fail open, and only trigger when a graph exists
- ✅ **Zero latency overhead**: Hooks inspect the command/path with a cheap `python3 -c` check before deciding
- ✅ **No external dependencies**: Uses `python3` which is always available where graphify runs
- ✅ **Subagent enforcement**: The Read/Glob hook text explicitly says "This rule applies to subagents too"

### What was NOT changed
- No new dependencies in `requirements.txt` or `.venv`
- No Docker configuration changes
- No CI/CD pipeline changes
- No runtime behavior changes for the V1 pipeline
- The project venv is untouched

---

## 12. V2 Handoff

### How to use Graphify during V2 development

#### Daily Commands
```bash
# After code changes (free, no API cost):
graphify update .

# After adding new files or major refactors:
graphify extract . --backend=deepseek --mode deep  # ~$0.002 per run

# Regenerate cluster report and visualization:
graphify cluster-only .
```

#### Exploration Commands
```bash
# Find how a component connects to the system:
graphify explain "<function_or_module>" --graph graphify-out/graph.json

# Trace impact of changing a module:
graphify affected "module_name" --graph graphify-out/graph.json

# Find relationships between two components:
graphify path "<component_A>" "<component_B>" --graph graphify-out/graph.json

# Ask a natural language question about architecture:
graphify query "How does the simulation agent connect to the pipeline?"

# Interactive visualizations (open in browser):
xdg-open graphify-out/graph.html            # Force-directed graph
xdg-open graphify-out/rtl2gds-agent-callflow.html  # Architecture diagrams
xdg-open graphify-out/GRAPH_TREE.html       # Collapsible file tree
```

#### V2-Specific Recommendations
1. **Add `.v` file generation to graphify workflow**: Configure post-pipeline hooks to run `graphify update .` so generated RTL is captured
2. **Test new agents against the graph**: After adding Yosys, OpenSTA, or PyUVM agents, verify they appear correctly with `graphify explain "new_agent"`
3. **Monitor community cohesion**: As V2 grows the codebase, check that new modules don't create overly fragmented communities
4. **Keep CLAUDE.md graphify section**: The installed hooks and rules will guide V2 development toward graph-aware exploration
5. **Re-extract after V2 milestone**: Run a fresh `graphify extract . --mode deep --force` after each V2 milestone to capture evolved architecture

#### Graph Freshness Policy
- The knowledge graph is **not live** — it reflects code at the time of extraction
- Always run `graphify update .` before relying on graph data during a session
- If the graph is stale, Claude Code's PreToolUse hooks will remind you

---

## Appendix A: uv Tool Environment

Graphify is installed as an isolated uv-managed tool:

```
Tool:   graphifyy v0.8.39
Binary: ~/.local/share/uv/tools/graphifyy/bin/graphify
Python: ~/.local/share/uv/tools/graphifyy/bin/python3 (Python 3.14)
```

The tool environment is isolated from the project's `.venv` (Python 3.10.12). This is correct — no cross-contamination between graphify and the V1 pipeline.

## Appendix B: Token Cost

| Operation | Input Tokens | Output Tokens | Estimated Cost |
|-----------|-------------|--------------|----------------|
| Initial extraction | 2,167 | 7,024 | ~$0.0023 |
| Deep mode | 0 (cached) | 0 (cached) | $0.00 |
| Cluster/community naming | 0 | 0 (no API used) | $0.00 |
| Claude integration | N/A | N/A | $0.00 |
| **Total** | **~2,167** | **~7,024** | **~$0.0023** |
