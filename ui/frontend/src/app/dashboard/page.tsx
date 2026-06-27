'use client';

import { useState, useMemo, useCallback, useEffect } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { PageContainer } from '@/components/layout/page-container';
import { JobRunner } from '@/components/jobs/job-runner';
import { SiliconFlow } from '@/components/pipeline/silicon-flow';
import { AgentActivityFeed } from '@/components/pipeline/agent-activity-feed';
import { JobResultsPanel } from '@/components/jobs/job-results-panel';
import { LiveTerminal } from '@/components/pipeline/live-terminal';
import type { LogLine } from '@/components/pipeline/live-terminal';
import { MetricsDashboard } from '@/components/pipeline/metrics-dashboard';
import { AgentCollaborationView } from '@/components/pipeline/agent-collaboration-view';
import { ExecutionTimeline } from '@/components/pipeline/execution-timeline';
import { StageDetailDrawer } from '@/components/pipeline/stage-detail-drawer';
import { BackendStatusBar } from '@/components/shared/backend-status-bar';
import { useToast } from '@/components/shared/toast';
import { useJobStore } from '@/stores/job-store';
import { useJobStream } from '@/hooks/use-job-stream';
import { useUIStore } from '@/stores/ui-store';
import { useDemoStore } from '@/stores/demo-store';
import { useReplayDemo } from '@/hooks/use-replay-demo';
import { useLiveAgents, useLiveMetrics, useLiveStageDetails } from '@/hooks/use-live-data';
import { STAGE_LABELS } from '@/lib/constants';
import { cn } from '@/lib/utils';

type BottomTab = 'terminal' | 'collaboration' | 'timeline' | 'metrics';

export default function DashboardPage() {
  const activeJobId = useJobStore((s) => s.activeJobId);
  const activeJob = useJobStore((s) => (s.activeJobId ? s.jobs[s.activeJobId] : null));
  const rightPanelOpen = useUIStore((s) => s.rightPanelOpen);
  const toggleRightPanel = useUIStore((s) => s.toggleRightPanel);

  // Demo mode
  const demoEnabled = useDemoStore((s) => s.demoEnabled);
  const toggleDemo = useDemoStore((s) => s.toggleDemo);
  const isSimulating = useDemoStore((s) => s.isSimulating);

  // Real demo replay — dispatches saved pipeline events into the job store
  useReplayDemo();

  // Live data (derived from job store events — fed by the real demo replay
  // when demo mode is active, or by the SSE stream for live jobs)
  const liveAgents = useLiveAgents(activeJobId);
  const liveMetrics = useLiveMetrics(activeJobId);
  const liveStageDetails = useLiveStageDetails(activeJobId);

  const { addToast } = useToast();

  // Connect SSE stream for active job (only when not in demo mode)
  useJobStream(!demoEnabled ? activeJobId : null);

  const isLive = (demoEnabled && isSimulating) || activeJob?.status === 'running';

  // Bottom panel tabs
  const [activeTab, setActiveTab] = useState<BottomTab>('terminal');

  // Stage detail drawer
  const [selectedStage, setSelectedStage] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const openStageDrawer = useCallback((stageName: string) => {
    setSelectedStage(stageName);
    setDrawerOpen(true);
  }, []);

  const closeStageDrawer = useCallback(() => {
    setDrawerOpen(false);
    setTimeout(() => setSelectedStage(null), 300);
  }, []);

  // --- Unified data: when demo mode is active, the replay hook feeds the
  // --- job store with real captured events, so we always read from live.

  // Agents, metrics, stage details — always from the job store.
  // In demo mode, the replay dispatches events through dispatchEvent()
  // which populates the same stores.
  const agents = liveAgents;
  const metrics = liveMetrics;
  const stageDetails = liveStageDetails;

  // Build terminal log lines from job store events
  const terminalLines = useMemo((): LogLine[] => {
    if (!activeJob) return [];
    return activeJob.events.map((e) => {
      const time = new Date(e.timestamp).toLocaleTimeString('en-US', { hour12: false });
      let level: LogLine['level'] = 'INFO';
      if (e.severity === 'success') level = 'SUCCESS';
      else if (e.severity === 'error') level = 'ERROR';
      else if (e.severity === 'warning') level = 'WARNING';
      else if (e.severity === 'debug') level = 'DEBUG';
      return {
        timestamp: time,
        level,
        message: e.message,
        stage: e.stage ? (STAGE_LABELS[e.stage] || e.stage) : undefined,
      };
    });
  }, [activeJob]);

  // Build timeline events from active job
  const timelineEvents = useMemo(() => {
    if (!activeJob) return [];
    return activeJob.events
      .filter((e) =>
        ['stage_started', 'stage_completed', 'stage_failed', 'job_started', 'job_completed', 'job_failed'].includes(e.event_type)
      )
      .map((e) => {
        const time = new Date(e.timestamp).toLocaleTimeString('en-US', { hour12: false });
        let status: 'completed' | 'running' | 'failed' = 'completed';
        if (e.event_type === 'stage_started' || e.event_type === 'job_started') status = 'running';
        else if (e.event_type === 'stage_failed' || e.event_type === 'job_failed') status = 'failed';
        return {
          time,
          event: e.message,
          detail: e.stage ? `Stage: ${STAGE_LABELS[e.stage] || e.stage}` : 'Pipeline',
          stage: e.stage || 'pipeline',
          status,
        };
      });
  }, [activeJob]);

  // Notify on demo enable or live job start
  useEffect(() => {
    if (demoEnabled && isSimulating) {
      addToast({
        type: 'info',
        title: 'Demo Mode Active',
        message: 'Replaying real RTL-to-GDSII pipeline results from local EDA execution (iverilog, Yosys, OpenSTA, OpenLane).',
        duration: 5000,
      });
    }
  }, [demoEnabled, isSimulating, addToast]);

  // Notify when a live job starts
  useEffect(() => {
    if (!demoEnabled && activeJob?.status === 'running') {
      addToast({
        type: 'success',
        title: 'Pipeline Running',
        message: `Job ${activeJob.job_id} executing ${activeJob.benchmark} on ${activeJob.pipeline_version}`,
        duration: 5000,
      });
    }
  }, [activeJob?.status, activeJob?.job_id, demoEnabled, addToast]);

  const tabLabels: { key: BottomTab; label: string; icon: string }[] = [
    { key: 'terminal', label: 'Terminal', icon: 'terminal' },
    { key: 'collaboration', label: 'AI Agents', icon: 'groups' },
    { key: 'timeline', label: 'Timeline', icon: 'timeline' },
    { key: 'metrics', label: 'Metrics', icon: 'monitoring' },
  ];

  // Which stage detail to show in the drawer
  const selectedStageDetail = useMemo(() => {
    if (!selectedStage) return null;
    return stageDetails.find((s) => s.stageName === selectedStage) || null;
  }, [selectedStage, stageDetails]);

  return (
    <AppShell>
      {/* Backend status bar */}
      <div className="px-6 pt-4">
        <BackendStatusBar />
      </div>

      {/* Demo mode toggle */}
      <div className="flex items-center justify-between px-6 pt-3">
        <div className="flex items-center gap-2">
          <span className="text-2xs font-semibold uppercase tracking-wider text-muted-foreground">
            Mode
          </span>
          <button
            onClick={toggleDemo}
            className={cn(
              'relative inline-flex h-6 w-11 items-center rounded-full transition-all duration-300',
              demoEnabled
                ? 'bg-blue-600 shadow-[0_0_8px_rgba(37,99,235,0.4)]'
                : 'bg-slate-700'
            )}
          >
            <span
              className={cn(
                'inline-flex h-4 w-4 items-center justify-center rounded-full bg-white text-[8px] font-bold transition-all duration-300',
                demoEnabled ? 'translate-x-6' : 'translate-x-1'
              )}
            >
              {demoEnabled ? '⬡' : '◯'}
            </span>
          </button>
          <span className={cn(
            'text-xs font-medium transition-colors',
            demoEnabled ? 'text-blue-400' : 'text-muted-foreground'
          )}>
            {demoEnabled ? 'Demo Mode' : 'Live Mode'}
          </span>
          {demoEnabled && (
            <span className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-[10px] font-medium text-amber-400">
              <span className="material-symbols-outlined text-[12px]">verified</span>
              Real results from local EDA execution
            </span>
          )}
          {isLive && (
            <span className="flex items-center gap-1 text-[10px] text-emerald-500 font-mono">
              <span className="relative flex h-1.5 w-1.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500" />
              </span>
              {demoEnabled ? 'Running simulation' : 'Live pipeline'}
            </span>
          )}
        </div>

        {/* Keyboard shortcuts hint */}
        <div className="hidden lg:flex items-center gap-3 text-2xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <kbd className="px-1 py-0.5 rounded bg-slate-700/50 border border-slate-600/50 font-mono text-[10px]">⌘K</kbd>
            Search
          </span>
          <span className="flex items-center gap-1">
            <kbd className="px-1 py-0.5 rounded bg-slate-700/50 border border-slate-600/50 font-mono text-[10px]">⌘B</kbd>
            Toggle sidebar
          </span>
        </div>
      </div>

      <div className="flex gap-6 px-6 pt-4">
        {/* Center content */}
        <div className="flex-1 min-w-0 space-y-6">
          <PageContainer title="Dashboard">
            <JobRunner />

            {/* Pipeline visualization */}
            <SiliconFlow onStageClick={openStageDrawer} />

            {/* Agent Activity Feed */}
            <AgentActivityFeed
              jobId={activeJobId}
              isLive={isLive}
              className="min-h-[200px]"
            />
          </PageContainer>
        </div>

        {/* Right panel — results */}
        {rightPanelOpen && (
          <div className="hidden xl:block w-80 shrink-0">
            <div className="sticky top-[4.5rem] space-y-4">
              <JobResultsPanel />
            </div>
          </div>
        )}
      </div>

      {/* Bottom panel — tabbed view */}
      <div className="px-6 pt-4 pb-6 space-y-4">
        {/* Tabs */}
        <div className="flex items-center gap-1 border-b border-border">
          {tabLabels.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={cn(
                'flex items-center gap-1.5 px-4 py-2.5 text-xs font-semibold uppercase tracking-wider transition-all border-b-2 -mb-px',
                activeTab === tab.key
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              )}
            >
              <span className="material-symbols-outlined text-[14px]">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab content — all four tabs now work in both demo and live mode */}
        <div className="animate-[fade-in_0.2s_ease-out]">
          {activeTab === 'terminal' && (
            <LiveTerminal
              lines={terminalLines}
              isLive={isLive}
              className="min-h-[300px]"
            />
          )}

          {activeTab === 'collaboration' && (
            <AgentCollaborationView
              agents={agents}
              className="min-h-[300px]"
            />
          )}

          {activeTab === 'timeline' && (
            <ExecutionTimeline
              events={timelineEvents}
              className="min-h-[300px]"
              onEventClick={(event) => {
                if (event.stage && event.stage !== 'pipeline') {
                  openStageDrawer(event.stage);
                }
              }}
            />
          )}

          {activeTab === 'metrics' && (
            <MetricsDashboard
              metrics={metrics}
              isLive={isLive}
              className="min-h-[300px]"
            />
          )}
        </div>
      </div>

      {/* Stage Detail Drawer — now works with both demo and live data */}
      <StageDetailDrawer
        stage={selectedStageDetail}
        isOpen={drawerOpen}
        onClose={closeStageDrawer}
      />
    </AppShell>
  );
}
