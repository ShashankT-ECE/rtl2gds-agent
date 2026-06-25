// ============================================================
// TanStack Query hooks for benchmark endpoints
// ============================================================

'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { API_PATHS } from '@/lib/constants';
import type { BenchmarkInfo, BenchmarkListResponse } from '@/lib/types';

export function useBenchmarks() {
  return useQuery({
    queryKey: ['benchmarks'],
    queryFn: async () => {
      const res = await api.get<BenchmarkListResponse>(API_PATHS.benchmarks);
      return res.data;
    },
    staleTime: 5 * 60 * 1000, // 5 min — static data
  });
}

export function useBenchmark(name: string | undefined) {
  return useQuery({
    queryKey: ['benchmarks', name],
    queryFn: async () => {
      if (!name) throw new Error('Benchmark name is required');
      const res = await api.get<BenchmarkInfo>(API_PATHS.benchmark(name));
      return res.data;
    },
    enabled: !!name,
    staleTime: 5 * 60 * 1000,
  });
}
