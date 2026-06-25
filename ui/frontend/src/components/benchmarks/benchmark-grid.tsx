'use client';

import { BenchmarkCard } from './benchmark-card';
import { LoadingSkeleton } from '@/components/shared/loading-skeleton';
import { EmptyState } from '@/components/shared/empty-state';
import { ErrorState } from '@/components/shared/error-state';
import { useBenchmarks } from '@/hooks/use-benchmarks';
import { Cpu } from 'lucide-react';

export function BenchmarkGrid() {
  const { data, isLoading, isError, error, refetch } = useBenchmarks();
  const benchmarks = data?.benchmarks || [];

  // Completed benchmarks (those with reference RTL, TB, and bugs)
  const completed = ['alu_8bit', 'sync_fifo_8x16', 'fsm_traffic_light', 'uart_tx', 'apb_slave'];

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <LoadingSkeleton key={i} variant="card" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <ErrorState
        message={error instanceof Error ? error.message : 'Failed to load benchmarks'}
        onRetry={() => refetch()}
      />
    );
  }

  if (benchmarks.length === 0) {
    return (
      <EmptyState
        icon={Cpu}
        title="No benchmarks found"
        description="No benchmark designs are available."
      />
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {benchmarks.map((benchmark) => (
        <BenchmarkCard
          key={benchmark.name}
          benchmark={benchmark}
          isComplete={completed.includes(benchmark.name)}
        />
      ))}
    </div>
  );
}
