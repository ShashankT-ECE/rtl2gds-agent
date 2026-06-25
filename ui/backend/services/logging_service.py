"""
logging_service.py — Structured per-job logging.

Subscribes to EventBus and writes structured JSON log lines
for each event. A separate log file per job is created in LOG_DIR.
"""

import json
import logging
import os
from datetime import datetime, timezone

from ui.backend.config import settings
from ui.backend.schemas.event import PipelineEvent
from ui.backend.services.event_bus import EventBus

logger = logging.getLogger(__name__)


def _serialize_event(event: PipelineEvent) -> dict:
    """Flatten a PipelineEvent into a JSON-serializable dict."""
    return {
        "event_id": event.event_id,
        "job_id": event.job_id,
        "timestamp": event.timestamp,
        "event_type": event.event_type.value,
        "stage": event.stage,
        "message": event.message,
        "severity": event.severity.value,
        "payload": event.payload,
        "elapsed_time": event.elapsed_time,
        "iteration": event.iteration,
        "sequence_num": event.sequence_num,
    }


class LoggingService:
    """Writes per-job structured logs from EventBus events.

    Each job gets its own JSON-lines log file: LOG_DIR/<job_id>.jsonl
    Also emits human-readable lines to the standard Python logger.
    """

    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._log_dir = settings.LOG_DIR
        self._enabled = True

        # Ensure log directory exists
        self._log_dir.mkdir(parents=True, exist_ok=True)

        # Subscribe to event bus
        self._event_bus.subscribe(self._on_event)

    async def _on_event(self, event: PipelineEvent) -> None:
        """Handle an event — write to job log and standard logger."""
        if not self._enabled:
            return

        # Standard log emission
        log_msg = f"[{event.job_id}] [{event.event_type.value}] {event.message}"
        if event.severity.value == "error":
            logger.error(log_msg)
        elif event.severity.value == "warning":
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

        # Per-job structured log
        try:
            self._write_job_log(event)
        except Exception:
            logger.exception("Failed to write job log for %s", event.job_id)

    def _write_job_log(self, event: PipelineEvent) -> None:
        """Append one JSON line to the per-job log file."""
        log_path = self._log_dir / f"{event.job_id}.jsonl"
        entry = _serialize_event(event)
        with open(log_path, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def disable(self) -> None:
        """Disable log writing (for tests)."""
        self._enabled = False
