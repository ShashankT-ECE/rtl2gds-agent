'use client';

import { AppShell } from '@/components/layout/app-shell';
import { PageContainer } from '@/components/layout/page-container';
import { BenchmarkGrid } from '@/components/benchmarks/benchmark-grid';

export default function BenchmarksPage() {
  return (
    <AppShell>
      <PageContainer
        title="Benchmarks"
        description="Explore hardware design benchmarks with specifications, reference implementations, and test suites."
      >
        <BenchmarkGrid />
      </PageContainer>
    </AppShell>
  );
}
