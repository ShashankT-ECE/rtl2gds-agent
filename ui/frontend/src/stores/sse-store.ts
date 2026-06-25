// ============================================================
// SSE Store — SSE connection tracking
// ============================================================

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { SSEConnectionState, SSEConnectionStatus } from '@/lib/types';

interface SSEStoreState {
  connections: Record<string, SSEConnectionState>;
  globalConnected: boolean;

  connect: (jobId: string) => void;
  disconnect: (jobId: string) => void;
  updateConnectionStatus: (jobId: string, status: SSEConnectionStatus) => void;
  updateLastEvent: (jobId: string, timestamp: string) => void;
  incrementEventCount: (jobId: string) => void;
}

export const useSSEStore = create<SSEStoreState>()(
  devtools(
    (set, get) => ({
      connections: {},
      globalConnected: false,

      connect: (jobId) =>
        set((state) => {
          const newConnections = {
            ...state.connections,
            [jobId]: {
              status: 'connecting' as SSEConnectionStatus,
              lastEventAt: null,
              eventCount: 0,
              reconnectAttempt: 0,
            },
          };
          return {
            connections: newConnections,
            globalConnected: Object.values(newConnections).some(
              (c) => c.status === 'connected'
            ),
          };
        }, false, 'sseConnect'),

      disconnect: (jobId) =>
        set((state) => {
          const { [jobId]: _, ...rest } = state.connections;
          return {
            connections: rest,
            globalConnected: Object.values(rest).some(
              (c) => c.status === 'connected'
            ),
          };
        }, false, 'sseDisconnect'),

      updateConnectionStatus: (jobId, status) =>
        set((state) => {
          const existing = state.connections[jobId];
          if (!existing) return state;
          const newConnections = {
            ...state.connections,
            [jobId]: { ...existing, status },
          };
          return {
            connections: newConnections,
            globalConnected: Object.values(newConnections).some(
              (c) => c.status === 'connected'
            ),
          };
        }, false, 'sseUpdateStatus'),

      updateLastEvent: (jobId, timestamp) =>
        set((state) => {
          const existing = state.connections[jobId];
          if (!existing) return state;
          return {
            connections: {
              ...state.connections,
              [jobId]: { ...existing, lastEventAt: timestamp },
            },
          };
        }, false, 'sseUpdateLastEvent'),

      incrementEventCount: (jobId) =>
        set((state) => {
          const existing = state.connections[jobId];
          if (!existing) return state;
          return {
            connections: {
              ...state.connections,
              [jobId]: {
                ...existing,
                eventCount: existing.eventCount + 1,
              },
            },
          };
        }, false, 'sseIncrementEventCount'),
    }),
    { name: 'sse-store' }
  )
);
