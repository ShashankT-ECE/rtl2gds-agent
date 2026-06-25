// ============================================================
// useEventHistory — filtered event list from Zustand store
// ============================================================

'use client';

import { useMemo } from 'react';
import { useJobStore } from '@/stores/job-store';
import type { PipelineEvent, Severity, EventType } from '@/lib/types';

// Stable reference — never changes, so Zustand's Object.is check
// sees equality and doesn't trigger re-renders when there's no data.
const EMPTY_EVENTS: readonly PipelineEvent[] = Object.freeze([]);

interface EventFilter {
  severity?: Severity;
  eventType?: EventType;
  searchQuery?: string;
}

export function useEventHistory(jobId: string | null, filter?: EventFilter) {
  const events = useJobStore((state): readonly PipelineEvent[] => {
    if (!jobId) return EMPTY_EVENTS;
    const job = state.jobs[jobId];
    return job?.events ?? EMPTY_EVENTS;
  });

  const filtered = useMemo(() => {
    if (!filter || (!filter.severity && !filter.eventType && !filter.searchQuery)) {
      return events;
    }

    return events.filter((event) => {
      if (filter.severity && event.severity !== filter.severity) return false;
      if (filter.eventType && event.event_type !== filter.eventType) return false;
      if (filter.searchQuery) {
        const query = filter.searchQuery.toLowerCase();
        if (
          !event.message.toLowerCase().includes(query) &&
          !(event.stage || '').toLowerCase().includes(query)
        ) {
          return false;
        }
      }
      return true;
    });
  }, [events, filter]);

  return filtered;
}
