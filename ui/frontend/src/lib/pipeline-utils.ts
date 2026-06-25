// ============================================================
// Pipeline utility functions
// ============================================================

import type { PipelineVersion, StageInfo, StageStatus } from './types';
import { STAGES_BY_VERSION, FIX_LOOP_STAGES } from './constants';

/**
 * Get the ordered list of stage names for a pipeline version, including
 * fix-loop expansion (testbench_re, simulation_re).
 */
export function getStagesForVersion(version: PipelineVersion): readonly string[] {
  return STAGES_BY_VERSION[version];
}

/**
 * Determine if a stage is part of the fix loop.
 */
export function isFixLoopStage(stageName: string): boolean {
  return FIX_LOOP_STAGES.includes(stageName);
}

/**
 * Get the display row for a stage: 0 = main linear flow, 1 = fix loop, 2 = V2/V3 physical stages.
 */
export function getStageRow(stageName: string, version: PipelineVersion): number {
  if (version === 'v1') {
    return isFixLoopStage(stageName) ? 1 : 0;
  }
  // For V2/V3: fix loop stages are row 1, synthesis/sta/openlane/drc are row 2
  if (isFixLoopStage(stageName)) return 1;
  if (['synthesis', 'sta', 'openlane', 'drc'].includes(stageName)) return 2;
  return 0; // Main linear flow: spec, verif, rtl, tb, sim
}

/**
 * Calculate overall progress from stages.
 */
export function calculateProgress(stages: StageInfo[]): number {
  if (!stages || stages.length === 0) return 0;
  const weights: Record<StageStatus, number> = {
    completed: 1,
    failed: 1,
    running: 0.5,
    pending: 0,
    skipped: 1,
  };
  const total = stages.reduce((sum, s) => sum + (weights[s.status] ?? 0), 0);
  return Math.round((total / stages.length) * 100);
}

/**
 * Determine which stage is currently active from a list.
 */
export function getCurrentStage(stages: StageInfo[]): string | null {
  const running = stages.find(s => s.status === 'running');
  if (running) return running.name;
  // Return the last non-pending stage
  const active = [...stages].reverse().find(s => s.status !== 'pending');
  return active ? active.name : null;
}

/**
 * Build a map of stage name to StageInfo from an array.
 */
export function buildStageMap(stages: StageInfo[]): Map<string, StageInfo> {
  return new Map(stages.map(s => [s.name, s]));
}
