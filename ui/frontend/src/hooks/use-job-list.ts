// ============================================================
// TanStack Query hooks for job endpoints
// ============================================================

'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { API_PATHS } from '@/lib/constants';
import type { RunResponse, RunListResponse, RunRequest } from '@/lib/types';
import { useJobStore } from '@/stores/job-store';

export function useJobList(status?: string) {
  return useQuery({
    queryKey: ['jobs', status],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (status) params.set('status', status);
      const path = `${API_PATHS.run}${params.toString() ? '?' + params.toString() : ''}`;
      const res = await api.get<RunListResponse>(path);
      return res.data;
    },
    staleTime: 5_000,
    refetchInterval: 5_000,
  });
}

export function useJob(jobId: string | undefined) {
  return useQuery({
    queryKey: ['jobs', jobId],
    queryFn: async () => {
      if (!jobId) throw new Error('Job ID is required');
      const res = await api.get<RunResponse>(API_PATHS.runJob(jobId));
      return res.data;
    },
    enabled: !!jobId,
    staleTime: 2_000,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && (data.status === 'running' || data.status === 'queued')) {
        return 2_000;
      }
      return false;
    },
  });
}

export function useSubmitJob() {
  const queryClient = useQueryClient();
  const addJob = useJobStore((s) => s.addJob);

  return useMutation({
    mutationFn: async (request: RunRequest) => {
      const res = await api.post<RunResponse>(API_PATHS.run, request);
      return res.data;
    },
    onSuccess: (data) => {
      addJob(data);
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['status'] });
    },
  });
}

export function useCancelJob() {
  const queryClient = useQueryClient();
  const updateJob = useJobStore((s) => s.updateJob);

  return useMutation({
    mutationFn: async (jobId: string) => {
      const res = await api.post<RunResponse>(API_PATHS.cancelJob(jobId));
      return res.data;
    },
    onSuccess: (data) => {
      updateJob(data.job_id, { status: 'cancelled' });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
}
