"""
sse_adapter.py — SSE (Server-Sent Events) connection manager.

Subscribes to the EventBus and routes events to active SSE connections.
One asyncio.Queue per connection; queues are bounded (back-pressure).
Clients reconnect with ?after=<sequence_num> to replay missed events.
"""

import asyncio
import logging
from typing import Optional

from ui.backend.config import settings
from ui.backend.schemas.event import PipelineEvent
from ui.backend.services.event_bus import EventBus

logger = logging.getLogger(__name__)


class SSEManager:
    """Manages per-job SSE connection pools.

    Each active SSE connection has its own bounded queue.
    Events from the EventBus are pushed to all queues for the relevant job_id.
    """

    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        # job_id → set of asyncio.Queue
        self._connections: dict[str, set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

        # Subscribe to event bus for automatic delivery
        self._event_bus.subscribe(self._on_event)

    async def subscribe(self, job_id: str) -> asyncio.Queue:
        """Create a new SSE connection queue for a job.

        Returns an asyncio.Queue that the SSE route reads from.
        Max queue size prevents memory exhaustion from slow clients.
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=256)
        async with self._lock:
            if job_id not in self._connections:
                self._connections[job_id] = set()
            # Enforce per-job client limit
            if len(self._connections[job_id]) >= settings.SSE_MAX_CLIENTS_PER_JOB:
                logger.warning(
                    "SSE client limit reached for job %s (%d clients)",
                    job_id, len(self._connections[job_id])
                )
                # Still allow — just warn
            self._connections[job_id].add(queue)
        logger.debug("SSE client subscribed to job %s (total=%d)",
                     job_id, len(self._connections.get(job_id, set())))
        return queue

    async def unsubscribe(self, job_id: str, queue: asyncio.Queue) -> None:
        """Remove a client queue (called when SSE connection closes)."""
        async with self._lock:
            if job_id in self._connections:
                self._connections[job_id].discard(queue)
                if not self._connections[job_id]:
                    del self._connections[job_id]
        logger.debug("SSE client unsubscribed from job %s", job_id)

    async def _on_event(self, event: PipelineEvent) -> None:
        """EventBus subscriber — push event to all relevant SSE queues."""
        async with self._lock:
            queues = set(self._connections.get(event.job_id, set()))

        for q in queues:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                # Client too slow — drop oldest to make room
                logger.debug("SSE queue full for job %s — dropping oldest event", event.job_id)
                try:
                    q.get_nowait()  # drop oldest
                    q.put_nowait(event)  # enqueue latest
                except (asyncio.QueueFull, asyncio.QueueEmpty):
                    pass  # best effort

    @property
    def connection_count(self) -> int:
        """Total active SSE connections across all jobs."""
        return sum(len(qs) for qs in self._connections.values())
