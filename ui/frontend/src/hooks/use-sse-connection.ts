// ============================================================
// useSSEConnection — aggregate SSE connection status
// ============================================================

'use client';

import { useSSEStore } from '@/stores/sse-store';

export function useSSEConnection() {
  const globalConnected = useSSEStore((s) => s.globalConnected);
  const connections = useSSEStore((s) => s.connections);
  const activeConnections = Object.entries(connections).filter(
    ([, state]) => state.status === 'connected'
  );

  return {
    connected: globalConnected,
    connectionCount: activeConnections.length,
    activeJobIds: activeConnections.map(([id]) => id),
  };
}
