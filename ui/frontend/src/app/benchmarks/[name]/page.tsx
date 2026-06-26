'use client';

import { useParams, useRouter } from 'next/navigation';
import { Play, FileCode, FlaskConical, Bug, ArrowLeft } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageContainer } from '@/components/layout/page-container';
import { CategoryBadge } from '@/components/benchmarks/category-badge';
import { CodeBlock } from '@/components/shared/code-block';
import { LoadingSkeleton } from '@/components/shared/loading-skeleton';
import { ErrorState } from '@/components/shared/error-state';
import { useBenchmark } from '@/hooks/use-benchmarks';
import { useUIStore } from '@/stores/ui-store';
import { Button } from '@/components/ui/button';

export default function BenchmarkDetailPage() {
  const params = useParams();
  const router = useRouter();
  const name = params.name as string;
  const { data: benchmark, isLoading, isError, error, refetch } = useBenchmark(name);
  const setSelectedBenchmark = useUIStore((s) => s.setSelectedBenchmark);

  if (isLoading) {
    return (
      <AppShell>
        <PageContainer title="Loading...">
          <LoadingSkeleton variant="card" />
        </PageContainer>
      </AppShell>
    );
  }

  if (isError || !benchmark) {
    return (
      <AppShell>
        <PageContainer title="Benchmark">
          <ErrorState
            message={error instanceof Error ? error.message : 'Benchmark not found'}
            onRetry={() => refetch()}
          />
        </PageContainer>
      </AppShell>
    );
  }

  const handleRun = () => {
    setSelectedBenchmark(benchmark.name);
    router.push('/dashboard');
  };

  return (
    <AppShell>
      <PageContainer
        title={benchmark.name}
        description={benchmark.category_guess ? `${benchmark.category_guess} design` : undefined}
        actions={
          <Button onClick={handleRun} className="bg-primary hover:bg-primary/90 text-white font-semibold">
            <Play className="h-4 w-4 mr-2" />
            Run This Benchmark
          </Button>
        }
      >
        <Button
          variant="ghost"
          className="text-muted-foreground hover:text-foreground -mt-2"
          onClick={() => router.push('/benchmarks')}
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Benchmarks
        </Button>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Spec */}
          <div className="lg:col-span-2 space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-foreground mb-3">Specification</h2>
              <CodeBlock
                code={benchmark.spec_preview || 'No specification available.'}
                language="text"
                maxLines={30}
              />
            </div>
          </div>

          {/* Sidebar info */}
          <div className="space-y-4">
            <div className="rounded-lg border border-border bg-card p-4">
              <h3 className="text-sm font-semibold text-foreground/80 mb-3">Design Info</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Category</span>
                  <CategoryBadge category={benchmark.category_guess} />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Reference RTL</span>
                  <span className={benchmark.has_reference_rtl ? 'text-emerald-500' : 'text-muted-foreground'}>
                    <FileCode className="h-4 w-4 inline" />
                    {benchmark.has_reference_rtl ? ' Available' : ' N/A'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Reference TB</span>
                  <span className={benchmark.has_reference_tb ? 'text-emerald-500' : 'text-muted-foreground'}>
                    <FlaskConical className="h-4 w-4 inline" />
                    {benchmark.has_reference_tb ? ' Available' : ' N/A'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Bug Variants</span>
                  <span className={benchmark.bug_count > 0 ? 'text-yellow-400' : 'text-muted-foreground'}>
                    <Bug className="h-4 w-4 inline" />
                    {' '}{benchmark.bug_count}
                  </span>
                </div>
              </div>
            </div>

            {/* Bugs list */}
            {benchmark.bugs && benchmark.bugs.length > 0 && (
              <div className="rounded-lg border border-border bg-card p-4">
                <h3 className="text-sm font-semibold text-foreground/80 mb-3">Injected Bugs</h3>
                <div className="space-y-2">
                  {benchmark.bugs.map((bug) => (
                    <div key={bug.bug_id} className="text-sm">
                      <span className="font-mono text-xs text-yellow-400">{bug.bug_id}</span>
                      <p className="text-muted-foreground text-xs mt-0.5">{bug.description || 'No description'}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </PageContainer>
    </AppShell>
  );
}
