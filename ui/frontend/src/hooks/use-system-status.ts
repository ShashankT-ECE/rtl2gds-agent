// ============================================================
// TanStack Query hooks for health & status endpoints
// ============================================================

'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { API_PATHS } from '@/lib/constants';
import type { HealthResponse, SystemStatusResponse } from '@/lib/types';

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const res = await api.get<HealthResponse>(API_PATHS.health);
      return res.data;
    },
    staleTime: 30_000,
    refetchInterval: 30_000,
  });
}

export function useSystemStatus() {
  return useQuery({
    queryKey: ['status'],
    queryFn: async () => {
      const res = await api.get<SystemStatusResponse>(API_PATHS.status);
      return res.data;
    },
    staleTime: 15_000,
    refetchInterval: 15_000,
  });
}
