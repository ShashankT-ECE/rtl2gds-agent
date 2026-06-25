# Integration Gaps Report — Phase 2 Frontend ↔ Backend

**Generated:** 2026-06-25
**Method:** Line-by-line comparison of backend mock adapter, event schemas, API routers, frontend event handlers, constants, and SSE client.

---

## 1. API Endpoint Verification

| Frontend call (constants.ts) | Backend route (routers/) | Status |
|------|------|--------|
| `/health` | `GET /health` | ✅ Match |
| `/status` | `GET /status` | ✅ Match |
| `/api/benchmarks` | `GET /api/benchmarks` | ✅ Match |
| `/api/benchmarks/${name}` | `GET /api/benchmarks/{name}` | ✅ Match |
| `/api/skills` | `GET /api/skills` | ✅ Match |
| `/api/skills/${category}` | `GET /api/skills/{category}` | ✅ Match |
| `/api/run` (POST) | `POST /api/run` | ✅ Match |
| `/api/run` (GET) | `GET /api/run` | ✅ Match |
| `/api/run/${jobId}` | `GET /api/run/{job_id}` | ✅ Match |
| `/api/run/${jobId}/cancel` | `POST /api/run/{job_id}/cancel` | ✅ Match |
| `/api/run/stream?job_id=` | `GET /api/run/stream` | ✅ Match |

**All 11 API endpoints match. No routing gaps.**

---

## 2. SSE Event Type Verification

### Backend EventType enum (19 types):
`job_started`, `job_completed`, `job_failed`, `job_cancelled`, `stage_started`, `stage_completed`, `stage_failed`, `agent_log`, `llm_call_start`, `llm_call_end`, `tool_call`, `fix_attempt`, `skill_retrieved`, `skill_stored`, `convergence_warning`, `simulation_result`, `synthesis_result`, `sta_result`, `drc_result`, `heartbeat`, `progress`

### Frontend event-handlers.ts handled types:
`job_started`, `stage_started`, `stage_completed`, `stage_failed`, `simulation_result`, `sta_result`, `drc_result`, `fix_attempt`, `progress`, `job_completed`, `job_failed`, `job_cancelled`, `agent_log`, `llm_call_start`, `llm_call_end`, `tool_call`, `skill_retrieved`, `skill_stored`, `convergence_warning`, `heartbeat`

**All 19 event types recognized by frontend. No type name mismatches.**

---

## 3. CRITICAL GAP: Stage Name Mismatch During Fix Loop (V1)

### Problem
The frontend distinguishes fix-loop stages with `_re` suffixes:

```
Frontend V1_STAGES (constants.ts):
  row 0 (main):  spec_parser → verification_planner → rtl_gen → testbench → simulation
  row 1 (fix):   log_analysis → fix → testbench_re → simulation_re
```

The backend mock reuses the SAME stage names on the second pass:

```
Backend V1 mock stages (pipeline_mock.py):
  spec_parser, verification_planner, rtl_gen, testbench, simulation,
  log_analysis, fix, testbench, simulation  ← same names, no _re suffix!
```

### Impact
When the backend emits `stage_started` with `stage="testbench"` a second time, the frontend's `updateStage` function finds the existing `testbench` StageInfo (already `completed` from the first pass) and updates its status to `running`. This causes:

1. **Flow diagram bug:** The main-row "TB Gen" stage goes from ✓ (completed) back to ⏳ (running). The fix-loop "TB (re)" stage never activates.
2. **Stage list confusion:** Only one "TB Gen" entry appears with its status bouncing between completed and running.
3. **Fix loop visualization never rendered:** The fix-loop row in SiliconFlow remains all "pending" because no `_re` stage names are ever emitted.

### Additionally: fix_attempt events never emitted
The backend mock does NOT emit `fix_attempt` events, so `iteration` stays at 0 even after going through `log_analysis` and `fix` stages.

### Additionally: Frontend V2/V3 stage lists include fix loop stages
```
Frontend V2_STAGES includes: log_analysis, fix, testbench_re, simulation_re
Backend V2 mock stages: spec_parser, verification_planner, rtl_gen, testbench, simulation, synthesis, sta
```
Same for V3 — frontend lists fix loop stages that the backend V2/V3 mocks never emit.

---

## 4. MINOR GAP: Missing `coverage_pct` in simulation_result

### Problem
Backend `simulation_result` payload:
```json
{"passed": true, "tests_run": 12, "tests_passed": 12}
```

Frontend Results Panel reads `payload.coverage_pct`:
```typescript
{simEvent.payload?.coverage_pct != null && (
  <div>Coverage: {String(simEvent.payload.coverage_pct)}%</div>
)}
```

### Impact
The Results Panel always shows "Coverage: --" (the coverage line never renders) because `coverage_pct` is never in the payload. Minor cosmetic issue.

---

## 5. MINOR GAP: Frontend does not reconnect SSE on page navigation

### Problem
`useJobStream` only auto-connects when `jobId` changes. If a user navigates to `/jobs/[jobId]` while a different job is running, the SSE reconnection with `after=<seq>` should replay missed events for that specific job. This works currently because each job detail page creates a new SSE connection.

### Impact
No functional gap for single-job viewing. Would be an issue if we supported viewing multiple active jobs simultaneously (out of scope for Phase 2).

---

## 6. VERIFIED: Payload field name consistency

| Event Type | Backend Payload Keys | Frontend Reads | Status |
|---|---|---|---|
| simulation_result | `passed`, `tests_run`, `tests_passed` | `passed` (→ sim_passed), `coverage_pct` | ⚠️ `coverage_pct` missing |
| synthesis_result | `cell_count`, `area`, `frequency` | `cell_count`, `area`, `frequency` | ✅ |
| sta_result | `timing_met`, `wns`, `tns`, `critical_path` | `timing_met`, `wns`, `tns`, `critical_path` | ✅ |
| drc_result | `drc_passed`, `violations` | `drc_passed`, `violations` | ✅ |
| progress | `percent` | `percent` | ✅ |

---

## 7. VERIFIED: SSE Wire Format

Backend SSE router emits:
```
event: pipeline_event
data: <JSON string of PipelineEvent>

event: heartbeat
data: {"timestamp": "..."}

event: done
data: {"job_id": "...", "status": "...", "total_events": N}

event: error
data: {"error": "..."}
```

Frontend SSE client listens for:
- `pipeline_event` → parses JSON as `PipelineEvent` ✅
- `heartbeat` → parses JSON as `SSEHeartbeatEvent` ✅
- `done` → parses JSON as `SSEDoneEvent` ✅
- `error` → parses JSON for error message ✅

**SSE wire format is fully compatible.**

---

## 8. SUMMARY: Gaps to fix

| # | Severity | Gap | Fix approach |
|---|----------|-----|-------------|
| 1 | **CRITICAL** | Backend reuses stage names for fix loop; frontend expects `_re` suffixes | Fix backend mock to emit `testbench_re` and `simulation_re` for fix-loop stages |
| 2 | **MEDIUM** | Backend mock never emits `fix_attempt` events | Add `fix_attempt` event emission in mock's fix-loop stages |
| 3 | **MINOR** | `coverage_pct` missing from simulation_result payload | Add `coverage_pct` to backend mock's simulation payload |
| 4 | **LOW** | V2/V3 stage lists differ (frontend includes fix loop, backend mock doesn't) | Align — remove fix loop stages from V2/V3 frontend stage lists since V2/V3 don't have fix loops in current mock |
