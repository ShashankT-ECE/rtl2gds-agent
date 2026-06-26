'use client';

import { AppShell } from '@/components/layout/app-shell';
import { PageContainer } from '@/components/layout/page-container';
import { SystemHealthPanel } from '@/components/status/system-health-panel';
import { VersionAvailability } from '@/components/status/version-availability';
import { useSystemStatus } from '@/hooks/use-system-status';
import { useSkills } from '@/hooks/use-skills';
import { LoadingSkeleton } from '@/components/shared/loading-skeleton';
import { useJobStore } from '@/stores/job-store';

export default function StatusPage() {
  const { data: status, isLoading } = useSystemStatus();
  const { data: skillData } = useSkills();
  const jobs = useJobStore((s) => s.jobs);

  const activeCount = Object.values(jobs).filter((j) => j.status === 'running').length;
  const completedCount = Object.values(jobs).filter((j) => j.status === 'completed').length;
  const failedCount = Object.values(jobs).filter((j) => j.status === 'failed').length;
  const queuedCount = Object.values(jobs).filter((j) => j.status === 'queued').length;

  return (
    <AppShell>
      <PageContainer
        title="System Status"
        description="Real-time system health and configuration."
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Health */}
          <SystemHealthPanel />

          {/* Versions */}
          <VersionAvailability />

          {/* Job statistics */}
          <div className="rounded-lg border border-border bg-card p-4">
            <h3 className="text-sm font-semibold text-foreground mb-4">Job Statistics</h3>
            <div className="grid grid-cols-4 gap-3">
              {[
                { label: 'Active', value: activeCount, color: 'text-primary' },
                { label: 'Completed', value: completedCount, color: 'text-emerald-500' },
                { label: 'Failed', value: failedCount, color: 'text-destructive' },
                { label: 'Queued', value: queuedCount, color: 'text-muted-foreground' },
              ].map((stat) => (
                <div key={stat.label} className="text-center">
                  <div className={`text-2xl font-bold font-mono ${stat.color}`}>{stat.value}</div>
                  <div className="text-xs text-muted-foreground mt-1">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Provider & Skills */}
          <div className="space-y-6">
            <div className="rounded-lg border border-border bg-card p-4">
              <h3 className="text-sm font-semibold text-foreground mb-3">Configuration</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">LLM Provider</span>
                  <span className="text-foreground">{status?.provider || '—'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Pipeline Mode</span>
                  <span className={status?.pipeline_mode === 'real' ? 'text-primary' : 'text-yellow-400'}>
                    {status?.pipeline_mode || '—'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Benchmarks</span>
                  <span className="text-foreground font-mono">{status?.benchmark_count || '—'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Trace2Skill Total</span>
                  <span className="text-foreground font-mono">{skillData?.total_skills || '—'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </PageContainer>
    </AppShell>
  );
}
