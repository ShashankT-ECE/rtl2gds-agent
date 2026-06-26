'use client';

import { Check, X, Activity } from 'lucide-react';
import { useJobStore } from '@/stores/job-store';
import { useDemoStore } from '@/stores/demo-store';
import { EmptyState } from '@/components/shared/empty-state';
import { cn } from '@/lib/utils';

interface ResultCardProps {
  title: string;
  status: 'pass' | 'fail' | 'pending';
  children: React.ReactNode;
  placeholder?: string;
}

function ResultCard({ title, status, children, placeholder }: ResultCardProps) {
  return (
    <div className="rounded-lg border border-border bg-card overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <h4 className="text-xs font-semibold text-foreground uppercase tracking-wider">{title}</h4>
        {status === 'pass' && <Check className="h-4 w-4 text-emerald-500" />}
        {status === 'fail' && <X className="h-4 w-4 text-destructive" />}
        {status === 'pending' && <span className="text-2xs text-muted-foreground">PENDING</span>}
      </div>
      <div className="p-4">
        {status === 'pending' && placeholder ? (
          <p className="text-xs text-muted-foreground">{placeholder}</p>
        ) : (
          children
        )}
      </div>
    </div>
  );
}

export function JobResultsPanel() {
  const activeJob = useJobStore((s) => (s.activeJobId ? s.jobs[s.activeJobId] : null));
  const demoEnabled = useDemoStore((s) => s.demoEnabled);
  const demoStageDetails = useDemoStore((s) => s.stageDetails);
  const demoMetrics = useDemoStore((s) => s.metrics);

  // Build demo result status from stage completions
  const demoSimComplete = demoStageDetails.some(
    (s) => (s.stageName === 'simulation' || s.stageName === 'simulation_re') && s.status === 'completed'
  );
  const demoSynthComplete = demoStageDetails.some(
    (s) => s.stageName === 'synthesis' && s.status === 'completed'
  );
  const demoStaComplete = demoStageDetails.some(
    (s) => s.stageName === 'sta' && s.status === 'completed'
  );
  const demoDrcComplete = demoStageDetails.some(
    (s) => s.stageName === 'drc' && s.status === 'completed'
  );
  const showDemoResults = demoEnabled && (demoSimComplete || demoSynthComplete || demoStaComplete || demoDrcComplete);

  if (!activeJob && !showDemoResults) {
    return (
      <div className="rounded-lg border border-border bg-card">
        <div className="px-4 py-3 border-b border-border">
          <h3 className="text-sm font-semibold text-foreground">RESULTS</h3>
        </div>
        <EmptyState
          icon={Activity}
          title="No results yet"
          description="Pipeline results will appear here when a job runs. Start a pipeline to see simulation, synthesis, STA, and DRC outputs."
        />
      </div>
    );
  }

  const simStatus: 'pass' | 'fail' | 'pending' = activeJob
    ? (activeJob.sim_passed === true ? 'pass' : activeJob.sim_passed === false ? 'fail' : 'pending')
    : (demoSimComplete ? 'pass' : 'pending');
  const staStatus: 'pass' | 'fail' | 'pending' = activeJob
    ? (activeJob.timing_met === true ? 'pass' : activeJob.timing_met === false ? 'fail' : 'pending')
    : (demoStaComplete ? 'pass' : 'pending');
  const drcStatus: 'pass' | 'fail' | 'pending' = activeJob
    ? (activeJob.drc_passed === true ? 'pass' : activeJob.drc_passed === false ? 'fail' : 'pending')
    : (demoDrcComplete ? 'pass' : 'pending');

  // Get latest result payloads from events
  const simEvent = activeJob ? [...activeJob.events].reverse().find(e => e.event_type === 'simulation_result') : null;
  const synthEvent = activeJob ? [...activeJob.events].reverse().find(e => e.event_type === 'synthesis_result') : null;
  const staEvent = activeJob ? [...activeJob.events].reverse().find(e => e.event_type === 'sta_result') : null;
  const drcEvent = activeJob ? [...activeJob.events].reverse().find(e => e.event_type === 'drc_result') : null;

  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="px-4 py-3 border-b border-border">
        <h3 className="text-sm font-semibold text-foreground">RESULTS</h3>
      </div>
      <div className="p-4 space-y-3">
        {/* Simulation */}
        <ResultCard title="Simulation" status={simStatus} placeholder="Awaiting simulation results...">
          {(simEvent || demoSimComplete) && (
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Status</span>
                <span className={simStatus === 'pass' ? 'text-emerald-500' : 'text-destructive'}>
                  {simStatus === 'pass' ? 'PASSED' : simStatus === 'fail' ? 'FAILED' : 'PENDING'}
                </span>
              </div>
              {(simEvent?.payload?.coverage_pct != null || demoSimComplete) && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Coverage</span>
                  <span className="text-foreground font-mono">
                    {simEvent?.payload?.coverage_pct != null ? `${String(simEvent.payload.coverage_pct)}%` : '87.5%'}
                  </span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-muted-foreground">Iteration</span>
                <span className="text-foreground font-mono">{activeJob?.iteration ?? demoMetrics.iterations}</span>
              </div>
              {/* Waveform placeholder */}
              <div className="mt-3 rounded bg-background border border-border p-4">
                <svg width="100%" height="60" viewBox="0 0 300 60" className="opacity-30">
                  <rect width="300" height="60" fill="#09090b" />
                  {[15, 25, 35, 45].map((y, i) => (
                    <g key={i}>
                      <text x="5" y={y + 4} fill="#4f5b73" fontSize="6" fontFamily="monospace">
                        {`signal_${i}`}
                      </text>
                      <polyline
                        points={`50,${y} 70,${y} 70,${y - 10} 90,${y - 10} 90,${y} 130,${y} 130,${y - 10} 170,${y - 10} 170,${y} 200,${y} 200,${y - 10} 230,${y - 10} 230,${y} 260,${y}`}
                        fill="none"
                        stroke="#2ea86c"
                        strokeWidth="2"
                      />
                    </g>
                  ))}
                </svg>
                <p className="text-2xs text-muted-foreground text-center mt-2">Interactive waveform viewer — Phase 3</p>
              </div>
            </div>
          )}
        </ResultCard>

        {/* Synthesis */}
        <ResultCard title="Synthesis" status={synthEvent || demoSynthComplete ? 'pass' : 'pending'} placeholder="Awaiting synthesis results...">
          {(synthEvent || demoSynthComplete) && (
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Cell Count</span>
                <span className="text-foreground font-mono">
                  {synthEvent?.payload?.cell_count != null ? String(synthEvent.payload.cell_count) : demoMetrics.cellCount}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Area</span>
                <span className="text-foreground font-mono">
                  {synthEvent?.payload?.area != null ? String(synthEvent.payload.area) : `${(demoMetrics.area / 1000000).toFixed(4)}`}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Frequency</span>
                <span className="text-foreground font-mono">
                  {synthEvent?.payload?.frequency != null ? String(synthEvent.payload.frequency) : `${demoMetrics.frequency}`}
                </span>
              </div>
            </div>
          )}
        </ResultCard>

        {/* STA */}
        <ResultCard title="STA" status={staStatus} placeholder="Awaiting timing analysis...">
          {(staEvent || demoStaComplete) && (
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Timing</span>
                <span className={staStatus === 'pass' ? 'text-emerald-500 font-semibold' : 'text-destructive font-semibold'}>
                  {staStatus === 'pass' ? 'MET' : 'VIOLATED'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">WNS</span>
                <span className="text-emerald-500 font-mono">
                  {staEvent?.payload?.wns != null ? `${String(staEvent.payload.wns)} ns` : `${demoMetrics.timingSlack} ns`}
                </span>
              </div>
              {staEvent?.payload?.tns != null && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">TNS</span>
                  <span className="text-foreground font-mono">{String(staEvent.payload.tns)} ns</span>
                </div>
              )}
            </div>
          )}
        </ResultCard>

        {/* DRC */}
        <ResultCard title="DRC" status={drcStatus} placeholder="Awaiting DRC results...">
          {(drcEvent || demoDrcComplete) && (
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">DRC Status</span>
                <span className={drcStatus === 'pass' ? 'text-emerald-500 font-semibold' : 'text-destructive font-semibold'}>
                  {drcStatus === 'pass' ? 'CLEAN' : 'VIOLATIONS'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Violations</span>
                <span className="text-emerald-500 font-mono">
                  {drcEvent?.payload?.violations != null ? String(drcEvent.payload.violations) : demoMetrics.violations}
                </span>
              </div>
              {/* Layout placeholder */}
              <div className="mt-3 rounded bg-background border border-border p-4">
                <svg width="100%" height="60" viewBox="0 0 300 60" className="opacity-30">
                  <rect width="300" height="60" fill="#09090b" />
                  <rect x="80" y="10" width="140" height="40" fill="none" stroke="#4f5b73" strokeWidth="1" />
                  <rect x="100" y="15" width="30" height="30" fill="none" stroke="#f09837" strokeWidth="0.5" opacity="0.5" />
                  <rect x="140" y="15" width="30" height="30" fill="none" stroke="#f09837" strokeWidth="0.5" opacity="0.5" />
                  <rect x="180" y="15" width="25" height="30" fill="none" stroke="#f09837" strokeWidth="0.5" opacity="0.5" />
                  <line x1="130" y1="25" x2="140" y2="25" stroke="#4e9cf5" strokeWidth="0.5" opacity="0.5" />
                  <line x1="170" y1="25" x2="180" y2="25" stroke="#4e9cf5" strokeWidth="0.5" opacity="0.5" />
                </svg>
                <p className="text-2xs text-muted-foreground text-center mt-2">GDSII layout viewer — Phase 3</p>
              </div>
            </div>
          )}
        </ResultCard>
      </div>
    </div>
  );
}
