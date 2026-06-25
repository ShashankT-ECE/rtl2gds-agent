// ============================================================
// useJobStream — SSE connection management for a single job
// ============================================================

'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import { SSEConnection } from '@/lib/sse-client';
import { dispatchEvent } from '@/lib/event-handlers';
import { useSSEStore } from '@/stores/sse-store';
import type { SSEConnectionStatus } from '@/lib/types';

interface UseJobStreamReturn {
  connect: () => void;
  disconnect: () => void;
  status: SSEConnectionStatus | 'idle';
  eventCount: number;
}

export function useJobStream(jobId: string | null): UseJobStreamReturn {
  const connectionRef = useRef<SSEConnection | null>(null);
  const [status, setStatus] = useState<SSEConnectionStatus | 'idle'>('idle');
  const sseStore = useSSEStore();

  const disconnect = useCallback(() => {
    if (connectionRef.current) {
      connectionRef.current.close();
      connectionRef.current = null;
    }
    if (jobId) {
      sseStore.disconnect(jobId);
    }
    setStatus('idle');
  }, [jobId, sseStore]);

  const connect = useCallback(() => {
    if (!jobId) return;

    // Clean up any existing connection
    disconnect();

    sseStore.connect(jobId);

    const connection = new SSEConnection({
      jobId,
      onEvent: (event) => {
        dispatchEvent(event);
        sseStore.updateLastEvent(jobId, event.timestamp);
        sseStore.incrementEventCount(jobId);
      },
      onDone: (data) => {
        sseStore.updateConnectionStatus(jobId, 'disconnected');
      },
      onError: (error) => {
        console.error('SSE error for job', jobId, error);
      },
      onStatusChange: (newStatus) => {
        sseStore.updateConnectionStatus(jobId, newStatus);
        setStatus(newStatus);
      },
    });

    connection.connect();
    connectionRef.current = connection;
  }, [jobId, disconnect, sseStore]);

  // Auto-connect when jobId changes
  useEffect(() => {
    if (jobId) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, [jobId]); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    connect,
    disconnect,
    status,
    eventCount: jobId ? (sseStore.connections[jobId]?.eventCount ?? 0) : 0,
  };
}
