# RTL2GDS Agent — Web UI Backend (Phase 1)

Backend infrastructure for the AI-Driven Agentic Framework for RTL-to-GDS.

## Architecture

```
Pipeline (frozen) → Adapter → EventBus → SSE → Frontend
                              ↕
                         JobManager
```

- **Pipeline**: runs in a background thread (never blocks the event loop)
- **EventBus**: single source of truth — all state derived from events
- **SSE**: Server-Sent Events for real-time pipeline monitoring
- **Mock adapter**: default (`PIPELINE_MODE=mock`) for UI dev without EDA tools

## Quick Start

```bash
cd ~/projects/rtl2gds-agent
source .venv/bin/activate
python -m ui.backend.main
```

Server starts at http://localhost:8000.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness check |
| GET | `/status` | System-wide status |
| GET | `/api/benchmarks` | List all benchmarks |
| GET | `/api/benchmarks/{name}` | Single benchmark detail |
| GET | `/api/skills` | Trace2Skill category summaries |
| GET | `/api/skills/{category}` | All skills in a category |
| POST | `/api/run` | Start a pipeline job |
| GET | `/api/run` | List recent jobs |
| GET | `/api/run/{job_id}` | Job status |
| POST | `/api/run/{job_id}/cancel` | Cancel a job |
| GET | `/api/run/stream?job_id=` | SSE event stream |

OpenAPI docs: http://localhost:8000/docs

## Configuration

All settings via environment variables or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `PIPELINE_MODE` | `mock` | `mock` (synthetic events) or `real` (run actual pipeline) |
| `APP_PORT` | `8000` | Server port |
| `LOG_LEVEL` | `INFO` | Python log level |
| `MAX_CONCURRENT_JOBS` | `1` | Max simultaneous pipeline runs |
| `PIPELINE_TIMEOUT_SECONDS` | `600` | Max seconds per job |
| `SSE_HEARTBEAT_INTERVAL` | `15` | Seconds between SSE heartbeats |

## Running Tests

```bash
pytest tests/test_api.py -v
```

Tests use the mock adapter — no EDA tools required.

## Frozen Pipeline

This backend **wraps** the existing pipeline — it never modifies:

- `v1_core/`
- `v2_verification/`
- `v3_physical/`

## Integration Points for Phase 2 (Frontend)

1. **SSE endpoint** (`GET /api/run/stream`) — consume with `EventSource` in the browser
2. **REST API** — all endpoints return JSON compatible with any frontend framework
3. **Event types** — `schemas/event.py` defines all event types the frontend should handle
4. **Job lifecycle** — poll `GET /api/run/{job_id}` or stream SSE for real-time updates
