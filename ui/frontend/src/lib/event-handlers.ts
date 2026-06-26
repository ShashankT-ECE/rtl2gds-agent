// ============================================================
// Event type → Zustand dispatch mapping
// ============================================================

import type { PipelineEvent } from './types';
import { useJobStore } from '@/stores/job-store';

type EventHandler = (event: PipelineEvent) => void;

/** Helper: dump every stage name+status from the store for tracing. */
function traceStages(label: string, jobId: string): void {
  const job = useJobStore.getState().jobs[jobId];
  if (!job) { console.log(`[TRACE] ${label}: job not found`); return; }
  console.log(`[TRACE] ${label}:`, job.stages.map(s => `${s.name}=${s.status}`));
}

/**
 * Dispatch a PipelineEvent to the appropriate store actions.
 * Each event type updates specific job state fields.
 */
export function dispatchEvent(event: PipelineEvent): void {
  const store = useJobStore.getState();
  const { job_id: jobId, event_type: eventType } = event;

  // Always add the event to the job's event buffer
  store.addEvent(event);

  // Handle event-type-specific state updates
  switch (eventType) {
    case 'job_started':
      store.updateJob(jobId, {
        status: 'running',
        started_at: event.timestamp,
        current_stage: 'running',
      });
      break;

    case 'stage_started':
      if (event.stage) {
        // Guard: do not start a stage on a job that has already finished.
        // Late-arriving stage_started events (e.g. from an SSE replay
        // during reconnect) would otherwise resurrect a completed stage
        // back to "running" with no subsequent event to complete it,
        // leaving a perpetual spinner in the silicon-flow diagram.
        const currentJob = useJobStore.getState().jobs[jobId];
        if (currentJob && (currentJob.status === 'completed' || currentJob.status === 'failed' || currentJob.status === 'cancelled')) {
          break;
        }
        store.updateStage(jobId, event.stage, {
          status: 'running',
          started_at: event.timestamp,
        });
        store.updateJob(jobId, { current_stage: event.stage });
      }
      break;

    case 'stage_completed':
      if (event.stage) {
        store.updateStage(jobId, event.stage, {
          status: 'completed',
          completed_at: event.timestamp,
          elapsed_ms: event.elapsed_time ? event.elapsed_time * 1000 : undefined,
        });
        traceStages(`stages after stage_completed(${event.stage})`, jobId);
      }
      break;

    case 'stage_failed':
      if (event.stage) {
        store.updateStage(jobId, event.stage, {
          status: 'failed',
          completed_at: event.timestamp,
        });
      }
      break;

    case 'simulation_result':
      store.updateJob(jobId, {
        sim_passed: event.payload?.passed as boolean | null,
      });
      break;

    case 'synthesis_result':
      break;

    case 'sta_result':
      store.updateJob(jobId, {
        timing_met: event.payload?.timing_met as boolean | null,
      });
      break;

    case 'drc_result':
      store.updateJob(jobId, {
        drc_passed: event.payload?.drc_passed as boolean | null,
      });
      break;

    case 'fix_attempt':
      store.updateJob(jobId, {
        iteration: (event.iteration || (store.jobs[jobId]?.iteration ?? 0) + 1),
      });
      break;

    case 'progress':
      if (typeof event.payload?.percent === 'number') {
        store.updateJob(jobId, { progress_pct: event.payload.percent as number });
      }
      break;

    case 'job_completed':
      store.updateJob(jobId, {
        status: 'completed',
        completed_at: event.timestamp,
        progress_pct: 100,
      });
      // Compound state transition: when the job enters a terminal state,
      // close every stage still marked "running".  A dropped stage_completed
      // event (queue race, edge-proxy truncation, buffer flush) would
      // otherwise leave the last stage node spinning forever.
      {
        const job = useJobStore.getState().jobs[jobId];
        if (job) {
          for (const s of job.stages) {
            if (s.status === 'running') {
              store.updateStage(jobId, s.name, {
                status: 'completed',
                completed_at: event.timestamp,
              });
            }
          }
        }
      }
      break;

    case 'job_failed':
      store.updateJob(jobId, {
        status: 'failed',
        completed_at: event.timestamp,
        error_message: event.message,
      });
      // Same compound-state invariant: close still-running stages.
      {
        const job = useJobStore.getState().jobs[jobId];
        if (job) {
          for (const s of job.stages) {
            if (s.status === 'running') {
              store.updateStage(jobId, s.name, {
                status: 'failed',
                completed_at: event.timestamp,
              });
            }
          }
        }
      }
      break;

    case 'job_cancelled':
      store.updateJob(jobId, {
        status: 'cancelled',
        completed_at: event.timestamp,
      });
      // Same compound-state invariant: close still-running stages.
      {
        const job = useJobStore.getState().jobs[jobId];
        if (job) {
          for (const s of job.stages) {
            if (s.status === 'running') {
              store.updateStage(jobId, s.name, {
                status: 'skipped',
                completed_at: event.timestamp,
              });
            }
          }
        }
      }
      break;

    // These event types are informational only — they're captured by addEvent above
    case 'agent_log':
    case 'llm_call_start':
    case 'llm_call_end':
    case 'tool_call':
    case 'skill_retrieved':
    case 'skill_stored':
    case 'convergence_warning':
    case 'heartbeat':
      break;

    default:
      // Unknown event type — still logged via addEvent
      break;
  }
}
