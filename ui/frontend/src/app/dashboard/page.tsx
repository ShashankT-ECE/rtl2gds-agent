'use client';

import { AppShell } from '@/components/layout/app-shell';
import { PageContainer } from '@/components/layout/page-container';
import { JobRunner } from '@/components/jobs/job-runner';
import { SiliconFlow } from '@/components/pipeline/silicon-flow';
import { AgentActivityFeed } from '@/components/pipeline/agent-activity-feed';
import { JobResultsPanel } from '@/components/jobs/job-results-panel';
import { useJobStore } from '@/stores/job-store';
import { useJobStream } from '@/hooks/use-job-stream';
import { useUIStore } from '@/stores/ui-store';

export default function DashboardPage() {
  const activeJobId = useJobStore((s) => s.activeJobId);
  const activeJob = useJobStore((s) => (s.activeJobId ? s.jobs[s.activeJobId] : null));
  const rightPanelOpen = useUIStore((s) => s.rightPanelOpen);
  const toggleRightPanel = useUIStore((s) => s.toggleRightPanel);

  // Connect SSE stream for active job
  useJobStream(activeJobId);

  const isLive = activeJob?.status === 'running';

  return (
    <AppShell>
      <div className="flex gap-6">
        {/* Center content */}
        <div className="flex-1 min-w-0 space-y-6">
          <PageContainer title="Dashboard">
            <JobRunner />
            <SiliconFlow />
            <AgentActivityFeed
              jobId={activeJobId}
              isLive={isLive}
              className="min-h-[300px]"
            />
          </PageContainer>
        </div>

        {/* Right panel — results */}
        {rightPanelOpen && (
          <div className="hidden xl:block w-80 shrink-0">
            <div className="sticky top-[4.5rem]">
              <JobResultsPanel />
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
