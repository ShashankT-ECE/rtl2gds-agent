'use client';

import { cn } from '@/lib/utils';
import { FlowStage } from './flow-stage';
import { FlowConnector } from './flow-connector';
import { IterationBadge } from './iteration-badge';
import { ConvergenceWarning } from './convergence-warning';
import { ProgressBar } from '@/components/shared/progress-bar';
import { ElapsedTimer } from '@/components/shared/elapsed-timer';
import { useJobStore } from '@/stores/job-store';
import { useUIStore } from '@/stores/ui-store';
import { useDemoStore } from '@/stores/demo-store';
import { STAGES_BY_VERSION, VERSION_INFO } from '@/lib/constants';
import { getStageRow } from '@/lib/pipeline-utils';
import type { PipelineVersion, StageStatus } from '@/lib/types';

interface SiliconFlowProps {
  onStageClick?: (stageName: string) => void;
}

export function SiliconFlow({ onStageClick }: SiliconFlowProps) {
  const activeJobId = useJobStore((s) => s.activeJobId);
  const activeJob = useJobStore((s) => (s.activeJobId ? s.jobs[s.activeJobId] : null));
  const selectedVersion = useUIStore((s) => s.selectedVersion);
  const setSelectedVersion = useUIStore((s) => s.setSelectedVersion);

  // Demo mode: read stage status from the demo store so the flow visualization
  // reflects the simulated pipeline, not the (empty) job store.
  const demoEnabled = useDemoStore((s) => s.demoEnabled);
  const demoStageDetails = useDemoStore((s) => s.stageDetails);
  const demoMetrics = useDemoStore((s) => s.metrics);

  const version: PipelineVersion = (activeJob?.pipeline_version as PipelineVersion) || selectedVersion;
  const stages = STAGES_BY_VERSION[version];
  const jobStages = activeJob?.stages || [];

  console.log('[SSE-DEBUG] SiliconFlow render:',
    'progress_pct=', activeJob?.progress_pct,
    'status=', activeJob?.status,
    'stageCount=', jobStages.length,
    'activeJobId=', activeJobId?.substring(0, 8));
  // Extra logging specifically for the problematic stage
  const simRe = jobStages.find((s: any) => s.name === 'simulation_re' || s.name === 'Sim(re)');
  if (simRe) {
    console.log('[SSE-DEBUG] SiliconFlow → simulation_re stage:',
      'name=', JSON.stringify(simRe.name),
      'status=', simRe.status,
      'started_at=', simRe.started_at,
      'completed_at=', simRe.completed_at);
  } else {
    console.log('[SSE-DEBUG] SiliconFlow → simulation_re stage NOT FOUND in jobStages');
  }
  // Also log all stages if simulation_re is still running
  if (activeJob?.status === 'completed' && simRe?.status === 'running') {
    console.warn('[SSE-DEBUG] BUG: simulation_re still running after job completed!',
      'allStages=', JSON.stringify(jobStages.map((s: any) => ({ n: s.name, st: s.status }))));
  }

  // Build stage status map + elapsed map
  const stageStatusMap = new Map<string, StageStatus>();
  const stageElapsedMap = new Map<string, number | null>();
  for (const s of jobStages) {
    stageStatusMap.set(s.name, s.status);
    stageElapsedMap.set(s.name, s.elapsed_ms || null);
  }

  // When demo is active, overlay demo stage statuses so the flow shows real progress
  if (demoEnabled) {
    for (const ds of demoStageDetails) {
      // Only set if we don't already have a live status (demo should not clobber real data)
      if (!stageStatusMap.has(ds.stageName) || stageStatusMap.get(ds.stageName) === 'pending') {
        stageStatusMap.set(ds.stageName, ds.status);
      }
    }
  }

  const getStatus = (stageName: string): StageStatus =>
    stageStatusMap.get(stageName) || 'pending';

  const getElapsed = (stageName: string): number | null =>
    stageElapsedMap.get(stageName) || null;

  // Separate stages by row
  const row0 = stages.filter((s) => getStageRow(s, version) === 0);
  const row1 = stages.filter((s) => getStageRow(s, version) === 1);
  const row2 = stages.filter((s) => getStageRow(s, version) === 2);

  // Version tabs
  const versions: PipelineVersion[] = ['v3', 'v2', 'v1'];

  // Shared FlowStage props
  const buildStageProps = (stageName: string, idx: number, baseNum: number, isLoop = false) => ({
    name: stageName,
    status: getStatus(stageName),
    stageNumber: baseNum + idx + 1,
    isInFixLoop: isLoop,
    onClick: onStageClick,
    elapsedMs: getElapsed(stageName),
  });

  return (
    <div className="rounded-lg border border-border bg-card overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-border">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-semibold text-foreground tracking-wider">
            SILICON DESIGN FLOW
          </h2>
          {activeJobId && (
            <span className="text-xs font-mono text-muted-foreground">{activeJobId}</span>
          )}
        </div>
        <div className="flex items-center gap-1">
          {versions.map((v) => (
            <button
              key={v}
              onClick={() => setSelectedVersion(v)}
              className={cn(
                'px-3 py-1 text-xs font-semibold rounded transition-all',
                version === v
                  ? 'bg-primary/10 text-primary border border-primary/30'
                  : 'text-muted-foreground hover:text-foreground hover:bg-accent border border-transparent'
              )}
            >
              {v.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Flow canvas */}
      <div className="p-6 space-y-6">
        {/* Version description */}
        {!activeJob && (
          <p className="text-xs text-muted-foreground text-center">
            {VERSION_INFO[version].description}
          </p>
        )}

        {/* Row 0: Main linear flow */}
        <div className="flex items-center justify-center flex-wrap gap-0">
          {row0.map((stageName, idx) => (
            <div key={stageName} className="flex items-center">
              <FlowStage {...buildStageProps(stageName, idx, 0)} />
              {idx < row0.length - 1 && (
                <FlowConnector
                  sourceStatus={getStatus(stageName)}
                  targetStatus={getStatus(row0[idx + 1])}
                />
              )}
            </div>
          ))}
        </div>

        {/* Fix loop connection indicator */}
        {row1.length > 0 && version !== 'v1' && (
          <div className="flex items-center justify-center">
            <div className="flex items-center gap-2">
              <span className="text-2xs text-muted-foreground font-mono">─ fix loop ─</span>
            </div>
          </div>
        )}

        {/* Row 1: Fix loop stages */}
        {version === 'v1' ? (
          <div className="flex items-center justify-center flex-wrap gap-0">
            {row1.map((stageName, idx) => (
              <div key={stageName} className="flex items-center">
                <FlowStage {...buildStageProps(stageName, idx, row0.length, true)} />
                {idx < row1.length - 1 && (
                  <FlowConnector
                    sourceStatus={getStatus(stageName)}
                    targetStatus={getStatus(row1[idx + 1])}
                    isLoopback
                  />
                )}
              </div>
            ))}
          </div>
        ) : (
          row1.length > 0 && (
            <div className="flex items-center justify-center flex-wrap gap-0">
              {row1.map((stageName, idx) => (
                <div key={stageName} className="flex items-center">
                  <FlowStage {...buildStageProps(stageName, idx, row0.length, true)} />
                  {idx < row1.length - 1 && (
                    <FlowConnector
                      sourceStatus={getStatus(stageName)}
                      targetStatus={getStatus(row1[idx + 1])}
                      isLoopback
                    />
                  )}
                </div>
              ))}
            </div>
          )
        )}

        {/* Row 2: V2/V3 physical stages */}
        {row2.length > 0 && (
          <>
            <div className="flex items-center justify-center">
              <div className="flex items-center gap-2">
                <span className="text-2xs text-muted-foreground font-mono">─ physical flow ─</span>
              </div>
            </div>
            <div className="flex items-center justify-center flex-wrap gap-0">
              {row2.map((stageName, idx) => (
                <div key={stageName} className="flex items-center">
                  <FlowStage {...buildStageProps(stageName, idx, row0.length + row1.length)} />
                  {idx < row2.length - 1 && (
                    <FlowConnector
                      sourceStatus={getStatus(stageName)}
                      targetStatus={getStatus(row2[idx + 1])}
                    />
                  )}
                </div>
              ))}
            </div>
          </>
        )}

        {/* Convergence warning */}
        {activeJob && activeJob.iteration >= 4 && (
          <ConvergenceWarning className="mx-8" />
        )}
      </div>

      {/* Footer with progress */}
      <div className="px-5 py-3 border-t border-border bg-muted/30 flex items-center gap-6">
        {/* Progress bar */}
        <div className="flex-1">
          <ProgressBar
            value={
              demoEnabled
                ? demoMetrics.successProbability
                : (activeJob?.progress_pct || 0)
            }
            variant={activeJob?.status === 'failed' ? 'error' : 'default'}
            showLabel
            indeterminate={!activeJob && !demoEnabled}
          />
        </div>

        {/* Iteration badge */}
        {activeJob && (
          <IterationBadge
            iteration={activeJob.iteration}
            maxIterations={5}
          />
        )}

        {/* Elapsed timer */}
        {activeJob?.started_at && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="text-xs text-muted-foreground">Elapsed:</span>
            <ElapsedTimer
              startedAt={activeJob.started_at}
              isRunning={activeJob.status === 'running'}
              className="text-foreground"
            />
          </div>
        )}
      </div>
    </div>
  );
}
