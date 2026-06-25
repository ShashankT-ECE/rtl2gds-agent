"""
event_bus.py — Publish-subscribe event bus for in-process pipeline events.

This is the architectural backbone. The pipeline (running synchronously in a thread)
emits events via publish(). Async subscribers (JobManager, SSEManager, Logging)
receive those events via asyncio.run_coroutine_threadsafe.

Single source of truth: all pipeline state changes flow through this bus.
No polling, no separate status cache — job state is derived from events.
"""

import asyncio
import logging
from typing import Awaitable, Callable, Optional

from ui.backend.schemas.event import PipelineEvent

logger = logging.getLogger(__name__)

EventHandler = Callable[[PipelineEvent], Awaitable[None]]


class EventBus:
    """In-memory pub/sub event bus.

    Thread-safe: publish() can be called from any thread;
    subscribers always receive events on the bound asyncio event loop.
    """

    def __init__(self) -> None:
        self._subscribers: list[EventHandler] = []
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._event_count: int = 0

    def attach_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Bind to a specific event loop (called during FastAPI lifespan startup)."""
        self._loop = loop
        logger.debug("EventBus attached to event loop")

    @property
    def event_count(self) -> int:
        return self._event_count

    def subscribe(self, handler: EventHandler) -> None:
        """Register an async handler to receive all events."""
        if handler not in self._subscribers:
            self._subscribers.append(handler)

    def unsubscribe(self, handler: EventHandler) -> None:
        """Remove a previously registered handler."""
        try:
            self._subscribers.remove(handler)
        except ValueError:
            pass

    def publish(self, event: PipelineEvent) -> None:
        """Thread-safe publish. Called from the pipeline (sync, in a thread).

        Schedules async dispatch on the bound event loop for every subscriber.
        Does NOT block the pipeline thread.
        """
        self._event_count += 1
        if self._loop is None or self._loop.is_closed():
            logger.warning("EventBus.publish called before loop attached; event dropped")
            return

        for handler in self._subscribers:
            # run_coroutine_threadsafe returns a concurrent.futures.Future.
            # We don't await it — fire-and-forget from the pipeline thread.
            asyncio.run_coroutine_threadsafe(self._dispatch(handler, event), self._loop)

    async def _dispatch(self, handler: EventHandler, event: PipelineEvent) -> None:
        """Safely invoke one handler — suppress errors so one bad subscriber
        cannot break all others."""
        try:
            await handler(event)
        except Exception:
            logger.exception(
                "EventBus subscriber %s failed processing event %s (type=%s)",
                getattr(handler, "__name__", handler),
                event.event_id,
                event.event_type,
            )

    # ---- Testing helpers ----

    async def apublish(self, event: PipelineEvent) -> None:
        """Async publish — awaits all handlers. Useful in tests only."""
        self._event_count += 1
        await asyncio.gather(
            *(self._dispatch(h, event) for h in self._subscribers),
            return_exceptions=True,
        )
