'use client';

import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageContainer } from '@/components/layout/page-container';
import { JobStageList } from '@/components/jobs/job-stage-list';
import { JobTimeline } from '@/components/jobs/job-timeline';
import { JobResultsPanel } from '@/components/jobs/job-results-panel';
import { JobCancelButton } from '@/components/jobs/job-cancel-button';
import { ElapsedTimer } from '@/components/shared/elapsed-timer';
import { ProgressBar } from '@/components/shared/progress-bar';
import { LoadingSkeleton } from '@/components/shared/loading-skeleton';
import { ErrorState } from '@/components/shared/error-state';
import { useJob } from '@/hooks/use-job-list';
import { useJobStream } from '@/hooks/use-job-stream';
import { useJobStore } from '@/stores/job-store';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { JOB_STATUS_COLORS, JOB_STATUS_LABELS } from '@/lib/constants';
import { formatRelativeTime } from '@/lib/formatters';

export default function JobDetailPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.jobId as string;
  const { data: job, isLoading, isError, error, refetch } = useJob(jobId);
  const storeJob = useJobStore((s) => s.jobs[jobId]);

  // Connect SSE if job is still active
  useJobStream(job?.status === 'running' || job?.status === 'queued' ? jobId : null);

  const displayJob = storeJob || job;
  const isRunning = displayJob?.status === 'running' || displayJob?.status === 'queued';
  const events = storeJob?.events || [];
  const statusColor = JOB_STATUS_COLORS[displayJob?.status || ''] || '#6b7a94';

  if (isLoading) {
    return (
      <AppShell>
        <PageContainer title="Job Details">
          <LoadingSkeleton variant="card" />
        </PageContainer>
      </AppShell>
    );
  }

  if (isError || !displayJob) {
    return (
      <AppShell>
        <PageContainer title="Job">
          <ErrorState
            message={error instanceof Error ? error.message : 'Job not found'}
            onRetry={() => refetch()}
          />
        </PageContainer>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <PageContainer
        title={
          <div className="flex items-center gap-3">
            <span className="font-mono text-silicon-400">{displayJob.job_id}</span>
            <Badge
              style={{
                backgroundColor: `${statusColor}15`,
                color: statusColor,
                borderColor: `${statusColor}30`,
              }}
            >
              {JOB_STATUS_LABELS[displayJob.status] || displayJob.status}
            </Badge>
          </div>
        }
        actions={
          <div className="flex items-center gap-3">
            <JobCancelButton jobId={displayJob.job_id} isRunning={isRunning} />
          </div>
        }
      >
        <Button
          variant="ghost"
          className="text-silicon-400 hover:text-silicon-200"
          onClick={() => router.push('/jobs')}
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Jobs
        </Button>

        {/* Quick stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="rounded-lg border border-silicon-700 bg-silicon-850 p-4">
            <div className="text-xs text-silicon-500">Benchmark</div>
            <div className="text-sm font-semibold text-silicon-200 mt-1">{displayJob.benchmark}</div>
          </div>
          <div className="rounded-lg border border-silicon-700 bg-silicon-850 p-4">
            <div className="text-xs text-silicon-500">Version</div>
            <div className="text-sm font-semibold text-silicon-200 mt-1">{displayJob.pipeline_version.toUpperCase()}</div>
          </div>
          <div className="rounded-lg border border-silicon-700 bg-silicon-850 p-4">
            <div className="text-xs text-silicon-500">Created</div>
            <div className="text-sm font-semibold text-silicon-200 mt-1">{formatRelativeTime(displayJob.created_at)}</div>
          </div>
          <div className="rounded-lg border border-silicon-700 bg-silicon-850 p-4">
            <div className="text-xs text-silicon-500">Elapsed</div>
            <div className="text-sm font-semibold text-silicon-200 mt-1">
              <ElapsedTimer startedAt={displayJob.started_at} isRunning={isRunning} />
            </div>
          </div>
        </div>

        {/* Progress */}
        <div className="rounded-lg border border-silicon-700 bg-silicon-850 p-4">
          <ProgressBar
            value={displayJob.progress_pct || 0}
            variant={displayJob.status === 'failed' ? 'error' : displayJob.status === 'completed' ? 'success' : 'default'}
            size="lg"
            showLabel
          />
          {displayJob.error_message && (
            <p className="text-sm text-etch-red mt-2">{displayJob.error_message}</p>
          )}
        </div>

        {/* Stages + Timeline grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Stage breakdown */}
          <div className="rounded-lg border border-silicon-700 bg-silicon-850">
            <div className="px-4 py-3 border-b border-silicon-700">
              <h3 className="text-sm font-semibold text-silicon-200">Stage Breakdown</h3>
            </div>
            <div className="p-4">
              <JobStageList stages={displayJob.stages} />
            </div>
          </div>

          {/* Event timeline */}
          <div className="rounded-lg border border-silicon-700 bg-silicon-850">
            <div className="px-4 py-3 border-b border-silicon-700">
              <h3 className="text-sm font-semibold text-silicon-200">
                Event Timeline
                <span className="ml-2 text-xs text-silicon-500 font-normal">
                  {displayJob.event_count} events
                </span>
              </h3>
            </div>
            <div className="p-4">
              <JobTimeline
                events={events.length > 0 ? events : []}
                stages={displayJob.stages}
                totalDurationMs={(displayJob.elapsed_seconds || 0) * 1000}
              />
            </div>
          </div>
        </div>

        {/* Results section */}
        <div className="max-w-md">
          <JobResultsPanel />
        </div>
      </PageContainer>
    </AppShell>
  );
}
