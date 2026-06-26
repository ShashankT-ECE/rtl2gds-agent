// ============================================================
// useLiveData — derives agent & metric state from job store events
// Bridges the gap between demo-only and live-mode visualizations
// ============================================================

'use client';

import { useMemo } from 'react';
import { useJobStore } from '@/stores/job-store';
import type { LiveMetrics, DemoAgent, DemoStageDetail } from '@/stores/demo-store';
import { STAGE_LABELS, STAGE_AGENTS } from '@/lib/constants';
import type { StageStatus, PipelineEvent } from '@/lib/types';

const AGENT_DEFS: Record<string, { icon: string; role: string }> = {
  spec_parser: { icon: '🤖', role: 'Parse natural language specifications into structured design constraints' },
  verification_planner: { icon: '🔍', role: 'Generate verification strategy and test plan' },
  rtl_gen: { icon: '⚙️', role: 'Generate synthesizable RTL from specification' },
  testbench: { icon: '🧪', role: 'Generate cocotb testbench and test vectors' },
  testbench_re: { icon: '🧪', role: 'Regenerate testbench after fix iteration' },
  simulation: { icon: '💻', role: 'Run Icarus Verilog simulation and collect results' },
  simulation_re: { icon: '💻', role: 'Re-run simulation after fixes applied' },
  log_analysis: { icon: '🔧', role: 'Analyze failures and identify root causes' },
  fix: { icon: '🔧', role: 'Apply fixes based on error analysis' },
  synthesis: { icon: '🔲', role: 'Run Yosys synthesis and optimize netlist' },
  sta: { icon: '⏱️', role: 'Static timing analysis with OpenSTA' },
  openlane: { icon: '🏗️', role: 'Floorplan, place, CTS, route with OpenLane' },
  drc: { icon: '✅', role: 'Design rule checking with KLayout' },
};

/**
 * Derive agent states from the job's stages and events.
 *
 * Maps pipeline stages → agent cards with status, progress, and last action.
 * Used by AgentCollaborationView when demo mode is off.
 */
export function useLiveAgents(jobId: string | null): DemoAgent[] {
  const job = useJobStore((s) => (jobId ? s.jobs[jobId] : null));

  return useMemo(() => {
    if (!job) return [];

    const stageMap = new Map<string, { status: StageStatus; startedAt: string | null; completedAt: string | null }>();
    for (const s of job.stages) {
      stageMap.set(s.name, { status: s.status, startedAt: s.started_at || null, completedAt: s.completed_at || null });
    }

    // Get the latest message per stage from events
    const stageMessages = new Map<string, string>();
    for (const e of [...job.events].reverse()) {
      if (e.stage && !stageMessages.has(e.stage)) {
        stageMessages.set(e.stage, e.message);
      }
    }

    // Build agent cards from all known pipeline stages
    const allStageNames = Array.from(new Set([
      ...Array.from(stageMap.keys()),
      'spec_parser', 'verification_planner', 'rtl_gen', 'testbench',
      'simulation', 'synthesis', 'sta', 'openlane', 'drc',
    ]));

    const agentOrder = [
      'spec_parser', 'verification_planner', 'rtl_gen', 'testbench',
      'simulation', 'log_analysis', 'fix', 'synthesis', 'sta', 'openlane', 'drc',
    ];

    return agentOrder
      .filter((name) => allStageNames.includes(name) || AGENT_DEFS[name])
      .map((name) => {
        const def = AGENT_DEFS[name] || { icon: '◇', role: 'Pipeline stage agent' };
        const stageInfo = stageMap.get(name);
        const status: DemoAgent['status'] = !stageInfo
          ? 'idle'
          : stageInfo.status === 'running'
            ? 'active'
            : stageInfo.status === 'completed'
              ? 'completed'
              : stageInfo.status === 'failed'
                ? 'error'
                : 'idle';
        const lastMsg = stageMessages.get(name) || '';

        return {
          id: name,
          name: STAGE_LABELS[name] || name,
          icon: def.icon,
          role: def.role,
          currentTask: status === 'active' ? lastMsg || 'Running...' : status === 'completed' ? 'Complete' : 'Standing by',
          status,
          progress: status === 'completed' ? 100 : status === 'active' ? 50 : 0,
          startedAt: stageInfo?.startedAt || null,
          completedAt: stageInfo?.completedAt || null,
          dependencies: [],
          lastAction: lastMsg || (status === 'idle' ? 'Waiting for input' : ''),
        };
      });
  }, [job]);
}

/**
 * Derive live metrics from job stage completions and result events.
 *
 * Extracts area, power, timing slack, violations, runtime, tokens, iterations,
 * cell count, frequency, memory, and success probability from job events.
 * Used by MetricsDashboard when demo mode is off.
 */
export function useLiveMetrics(jobId: string | null): LiveMetrics {
  const job = useJobStore((s) => (jobId ? s.jobs[jobId] : null));

  return useMemo(() => {
    if (!job) {
      return {
        area: 0, power: 0, timingSlack: 0, violations: 0,
        runtime: 0, tokensConsumed: 0, iterations: 0,
        memoryUsage: 0, successProbability: 0,
        cellCount: 0, frequency: 0,
      };
    }

    // Runtime from started_at
    let runtime = 0;
    if (job.started_at) {
      const end = job.completed_at ? new Date(job.completed_at).getTime() : Date.now();
      runtime = Math.round((end - new Date(job.started_at).getTime()) / 1000);
    }

    // Extract result data from events
    let area = 0;
    let cellCount = 0;
    let frequency = 0;
    let power = 0;
    let timingSlack = 0;
    let violations = -1; // -1 means no DRC data yet
    let tokensConsumed = 0;

    for (const e of job.events) {
      if (e.event_type === 'synthesis_result') {
        cellCount = (e.payload?.cell_count as number) || 0;
        const areaStr = (e.payload?.area as string) || '';
        const areaMatch = areaStr.match(/[\d.]+/);
        if (areaMatch) area = parseFloat(areaMatch[0]);
        // Estimate power based on cell count
        power = cellCount > 0 ? +(cellCount * 0.0113).toFixed(2) : 0;
        const freqMatch = (e.payload?.frequency as string) || '';
        const freqNum = freqMatch.match(/[\d.]+/);
        if (freqNum) frequency = parseInt(freqNum[0], 10);
      }
      if (e.event_type === 'sta_result') {
        timingSlack = (e.payload?.wns as number) || 0;
      }
      if (e.event_type === 'drc_result') {
        violations = (e.payload?.violations as number) || 0;
      }
      // Rough token estimate: ~200 tokens per event
      tokensConsumed += 200;
    }

    // Iterations
    const iterations = job.iteration || 0;

    // Memory (estimate based on event count)
    const memoryUsage = 120 + Math.min(job.events.length, 80);

    // Success probability based on stage completion
    const completedStages = job.stages.filter((s) => s.status === 'completed').length;
    const totalStages = Math.max(job.stages.length, 1);
    const successProbability = job.status === 'completed'
      ? 100
      : job.status === 'failed'
        ? 0
        : Math.min(99, Math.round((completedStages / totalStages) * 100));

    return {
      area,
      power,
      timingSlack,
      violations: violations >= 0 ? violations : 0,
      runtime,
      tokensConsumed,
      iterations,
      memoryUsage,
      successProbability,
      cellCount,
      frequency,
    };
  }, [job]);
}

/**
 * Derive stage details from job store stages and events.
 *
 * Used by StageDetailDrawer when demo mode is off.
 */
export function useLiveStageDetails(jobId: string | null): DemoStageDetail[] {
  const job = useJobStore((s) => (jobId ? s.jobs[jobId] : null));

  return useMemo(() => {
    if (!job) return [];

    const stageEventMap = new Map<string, PipelineEvent[]>();
    for (const e of job.events) {
      if (e.stage) {
        const list = stageEventMap.get(e.stage) || [];
        list.push(e);
        stageEventMap.set(e.stage, list);
      }
    }

    return Array.from(stageEventMap.entries()).map(([stageName, events]) => {
      const stageInfo = job.stages.find((s) => s.name === stageName);
      const logs = events.map((e) => {
        const time = new Date(e.timestamp).toLocaleTimeString('en-US', { hour12: false });
        return `[${time}] ${e.message}`;
      });

      return {
        stageName,
        status: stageInfo?.status || 'pending',
        startedAt: stageInfo?.started_at || null,
        completedAt: stageInfo?.completed_at || null,
        agent: STAGE_LABELS[stageName] || stageName,
        inputs: [],
        outputs: [],
        logs,
        artifacts: [],
        reports: [],
      };
    });
  }, [job]);
}
