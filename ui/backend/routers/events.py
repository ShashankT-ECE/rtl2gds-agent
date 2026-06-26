"""
events.py — SSE (Server-Sent Events) streaming endpoint.

GET /api/run/stream?job_id=<id>&after=<seq_num>

The client opens a long-lived HTTP connection and receives
text/event-stream data. Events are delivered in order, with
heartbeats every SSE_HEARTBEAT_INTERVAL seconds to keep the
connection alive.

Reconnection: clients pass ?after=<last_seq_num> on reconnect
to replay missed events. The server replays historical events
first, then streams new events.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from ui.backend.config import settings
from ui.backend.dependencies import get_job_manager, get_sse_manager
from ui.backend.services.job_manager import JobManager
from ui.backend.services.sse_adapter import SSEManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/run", tags=["events"])


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.get("/stream")
async def stream_events(
    job_id: str = Query(..., description="Job ID to stream events for"),
    after: int = Query(default=0, description="Replay events after this sequence number"),
    job_manager: JobManager = Depends(get_job_manager),
    sse_manager: SSEManager = Depends(get_sse_manager),
) -> StreamingResponse:
    """SSE endpoint — streams pipeline events for a job.

    - Replays historical events after the given sequence number first
    - Then streams live events as they arrive
    - Sends heartbeat every SSE_HEARTBEAT_INTERVAL seconds
    - Sends ``event: done`` when the job reaches a terminal state
    - Client reconnects with ``?after=<last_seq>`` to resume
    """

    async def event_generator():
        # Verify job exists
        job = await job_manager.get_job_optional(job_id)
        if job is None:
            yield _sse_line("error", json.dumps({"error": f"Job '{job_id}' not found"}))
            return

        # Phase 1: Replay historical events
        try:
            historical = await job_manager.get_events(job_id, after_seq=after)
            for event in historical:
                yield _sse_event("pipeline_event", event.model_dump_json())
                await asyncio.sleep(0)  # yield to event loop
        except Exception:
            logger.exception("Error replaying events for job %s", job_id)

        # Phase 2: Subscribe for live events
        queue = await sse_manager.subscribe(job_id)
        heartbeat_interval = settings.SSE_HEARTBEAT_INTERVAL

        try:
            while True:
                # Check if job is already done
                current = await job_manager.get_job_optional(job_id)
                if current and current.status.is_terminal:
                    # --- Wait + drain: terminal event queue race ---
                    #
                    # EventBus.publish() schedules JobManager._on_event
                    # before SSEManager._on_event on the same event loop.
                    # When the SSE generator wakes and finds is_terminal
                    # from JobManager, the queue may still be empty because
                    # SSEManager hasn't run yet.  Without a brief wait the
                    # generator yields the ``done`` event without the
                    # terminal pipeline_event (JOB_COMPLETED / JOB_FAILED),
                    # so the frontend never fires the compound state
                    # transition that closes still-running stages.
                    #
                    # Fixed: contend with the event loop once before
                    # sending done so SSEManager can enqueue the event.
                    try:
                        event = await asyncio.wait_for(
                            queue.get(), timeout=1.0,
                        )
                        yield _sse_event(
                            "pipeline_event", event.model_dump_json(),
                        )
                    except asyncio.TimeoutError:
                        pass

                    # Drain any remaining events
                    while not queue.empty():
                        try:
                            event = queue.get_nowait()
                            yield _sse_event("pipeline_event", event.model_dump_json())
                        except asyncio.QueueEmpty:
                            break

                    # --- Done ---
                    yield _sse_event("done", json.dumps({
                        "job_id": job_id,
                        "status": current.status.value,
                        "total_events": current.event_count,
                    }))

                    # --- Sentinel flush ---
                    # Force edge proxies (Railway, Vercel) to flush their
                    # buffer so the client receives the ``done`` chunk.
                    await asyncio.sleep(0.2)
                    yield _sse_event("stream_end", json.dumps({
                        "job_id": job_id,
                        "reason": "stream_closed",
                    }))
                    break

                # Wait for next event or heartbeat timeout
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=heartbeat_interval)
                    yield _sse_event("pipeline_event", event.model_dump_json())
                except asyncio.TimeoutError:
                    yield _sse_event("heartbeat", json.dumps({
                        "timestamp": _iso_now(),
                    }))

        except asyncio.CancelledError:
            logger.debug("SSE connection cancelled for job %s", job_id)
        finally:
            await sse_manager.unsubscribe(job_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


def _sse_event(event: str, data: str) -> str:
    """Format a standard SSE message."""
    return f"event: {event}\ndata: {data}\n\n"


def _sse_line(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"
