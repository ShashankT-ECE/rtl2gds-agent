'use client';

import { useState } from 'react';
import { cn } from '@/lib/utils';
import { FlowStage } from './flow-stage';
import { FlowConnector } from './flow-connector';
import { IterationBadge } from './iteration-badge';
import { ConvergenceWarning } from './convergence-warning';
import { ProgressBar } from '@/components/shared/progress-bar';
import { ElapsedTimer } from '@/components/shared/elapsed-timer';
import { useJobStore } from '@/stores/job-store';
import { useUIStore } from '@/stores/ui-store';
import { STAGES_BY_VERSION, VERSION_INFO, FIX_LOOP_STAGES } from '@/lib/constants';
import { getStageRow } from '@/lib/pipeline-utils';
import type { PipelineVersion, StageStatus } from '@/lib/types';
import { Badge } from '@/components/ui/badge';

export function SiliconFlow() {
  const activeJobId = useJobStore((s) => s.activeJobId);
  const activeJob = useJobStore((s) => (s.activeJobId ? s.jobs[s.activeJobId] : null));
  const selectedVersion = useUIStore((s) => s.selectedVersion);
  const setSelectedVersion = useUIStore((s) => s.setSelectedVersion);

  const version: PipelineVersion = (activeJob?.pipeline_version as PipelineVersion) || selectedVersion;
  const stages = STAGES_BY_VERSION[version];
  const jobStages = activeJob?.stages || [];

  // Build stage status map
  const stageStatusMap = new Map<string, StageStatus>();
  for (const s of jobStages) {
    stageStatusMap.set(s.name, s.status);
  }

  const getStatus = (stageName: string): StageStatus =>
    stageStatusMap.get(stageName) || 'pending';

  // Separate stages by row
  const row0 = stages.filter((s) => getStageRow(s, version) === 0);
  const row1 = stages.filter((s) => getStageRow(s, version) === 1);
  const row2 = stages.filter((s) => getStageRow(s, version) === 2);

  // Version tabs
  const versions: PipelineVersion[] = ['v3', 'v2', 'v1'];

  const isRunning = activeJob?.status === 'running';

  return (
    <div className="rounded-lg border border-silicon-700 bg-silicon-850 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-silicon-700">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-semibold text-silicon-200 tracking-wider">
            SILICON DESIGN FLOW
          </h2>
          {activeJobId && (
            <span className="text-xs font-mono text-silicon-500">{activeJobId}</span>
          )}
        </div>
        <div className="flex items-center gap-1">
          {versions.map((v) => (
            <button
              key={v}
              onClick={() => setSelectedVersion(v)}
              className={cn(
                'px-3 py-1 text-xs font-semibold rounded-full transition-all',
                version === v
                  ? 'bg-copper-500/20 text-copper-500 border border-copper-500/30'
                  : 'text-silicon-500 hover:text-silicon-300 hover:bg-silicon-800 border border-transparent'
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
          <p className="text-xs text-silicon-500 text-center">
            {VERSION_INFO[version].description}
          </p>
        )}

        {/* Row 0: Main linear flow */}
        <div className="flex items-center justify-center flex-wrap gap-0">
          {row0.map((stageName, idx) => (
            <div key={stageName} className="flex items-center">
              <FlowStage
                name={stageName}
                status={getStatus(stageName)}
                stageNumber={idx + 1}
              />
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
              <span className="text-2xs text-silicon-600 font-mono">─ fix loop ─</span>
            </div>
          </div>
        )}

        {/* Row 1: Fix loop stages (v1 shows these inline) */}
        {version === 'v1' ? (
          <div className="flex items-center justify-center flex-wrap gap-0">
            {row1.map((stageName, idx) => (
              <div key={stageName} className="flex items-center">
                <FlowStage
                  name={stageName}
                  status={getStatus(stageName)}
                  isInFixLoop
                  stageNumber={row0.length + idx + 1}
                />
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
                  <FlowStage
                    name={stageName}
                    status={getStatus(stageName)}
                    isInFixLoop
                    stageNumber={row0.length + idx + 1}
                  />
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
                <span className="text-2xs text-silicon-600 font-mono">─ physical flow ─</span>
              </div>
            </div>
            <div className="flex items-center justify-center flex-wrap gap-0">
              {row2.map((stageName, idx) => (
                <div key={stageName} className="flex items-center">
                  <FlowStage
                    name={stageName}
                    status={getStatus(stageName)}
                    stageNumber={row0.length + row1.length + idx + 1}
                  />
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
      <div className="px-5 py-3 border-t border-silicon-700 bg-silicon-900/50 flex items-center gap-6">
        {/* Progress bar */}
        <div className="flex-1">
          <ProgressBar
            value={activeJob?.progress_pct || 0}
            variant={activeJob?.status === 'failed' ? 'error' : 'default'}
            showLabel
            indeterminate={!activeJob}
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
          <div className="flex items-center gap-2 text-sm text-silicon-400">
            <span className="text-xs text-silicon-500">Elapsed:</span>
            <ElapsedTimer
              startedAt={activeJob.started_at}
              isRunning={activeJob.status === 'running'}
              className="text-silicon-200"
            />
          </div>
        )}
      </div>
    </div>
  );
}
