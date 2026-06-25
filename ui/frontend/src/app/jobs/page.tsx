'use client';

import { useState } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { PageContainer } from '@/components/layout/page-container';
import { JobCard } from '@/components/jobs/job-card';
import { LoadingSkeleton } from '@/components/shared/loading-skeleton';
import { EmptyState } from '@/components/shared/empty-state';
import { ErrorState } from '@/components/shared/error-state';
import { useJobList } from '@/hooks/use-job-list';
import { History } from 'lucide-react';
import { cn } from '@/lib/utils';

const STATUS_TABS = [
  { label: 'All', value: undefined },
  { label: 'Running', value: 'running' },
  { label: 'Completed', value: 'completed' },
  { label: 'Failed', value: 'failed' },
  { label: 'Cancelled', value: 'cancelled' },
];

export default function JobsPage() {
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);
  const { data, isLoading, isError, error, refetch } = useJobList(statusFilter);
  const jobs = data?.jobs || [];

  return (
    <AppShell>
      <PageContainer
        title="Job History"
        description="Review past pipeline runs and their results."
      >
        {/* Filter tabs */}
        <div className="flex gap-2 flex-wrap">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.label}
              onClick={() => setStatusFilter(tab.value)}
              className={cn(
                'px-3 py-1.5 text-xs font-medium rounded-full border transition-all',
                statusFilter === tab.value
                  ? 'bg-silicon-800 text-silicon-200 border-silicon-600'
                  : 'text-silicon-500 border-transparent hover:text-silicon-300 hover:border-silicon-700'
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Job list */}
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <LoadingSkeleton key={i} variant="card" />
            ))}
          </div>
        ) : isError ? (
          <ErrorState
            message={error instanceof Error ? error.message : 'Failed to load jobs'}
            onRetry={() => refetch()}
          />
        ) : jobs.length === 0 ? (
          <EmptyState
            icon={History}
            title="No jobs found"
            description={
              statusFilter
                ? `No ${statusFilter} jobs. Try a different filter.`
                : 'No pipeline jobs have been run yet. Start one from the Dashboard.'
            }
          />
        ) : (
          <div className="space-y-3">
            {jobs.map((job) => (
              <JobCard key={job.job_id} job={job} />
            ))}
          </div>
        )}
      </PageContainer>
    </AppShell>
  );
}
