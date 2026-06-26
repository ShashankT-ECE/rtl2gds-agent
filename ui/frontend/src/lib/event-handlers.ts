// ============================================================
// Event type → Zustand dispatch mapping
// ============================================================

import type { PipelineEvent } from './types';
import { useJobStore } from '@/stores/job-store';

type EventHandler = (event: PipelineEvent) => void;

/**
 * Dispatch a PipelineEvent to the appropriate store actions.
 * Each event type updates specific job state fields.
 */
export function dispatchEvent(event: PipelineEvent): void {
  const store = useJobStore.getState();
  const { job_id: jobId, event_type: eventType } = event;

  console.log('[SSE-DEBUG] dispatchEvent:',
    'type=', eventType,
    'seq=', event.sequence_num,
    'stage=', event.stage,
    'payload.percent=', (event.payload as any)?.percent);

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
      // Synthesis results are captured in job.events — no dedicated job field yet
      // The frontend reads synthesis data from event payloads directly
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
        console.log('[SSE-DEBUG] progress → updateJob progress_pct=',
          event.payload.percent,
          'jobId=', jobId);
        store.updateJob(jobId, { progress_pct: event.payload.percent as number });
        const after = useJobStore.getState().jobs[jobId]?.progress_pct;
        console.log('[SSE-DEBUG] progress → store after update: progress_pct=', after);
      } else {
        console.log('[SSE-DEBUG] progress → SKIPPED: no percent in payload, payload=',
          JSON.stringify(event.payload));
      }
      break;

    case 'job_completed':
      console.log('[SSE-DEBUG] job_completed → BEFORE updateJob, current state=',
        'progress_pct=', store.jobs[jobId]?.progress_pct,
        'status=', store.jobs[jobId]?.status,
        'jobId=', jobId);
      store.updateJob(jobId, {
        status: 'completed',
        completed_at: event.timestamp,
        progress_pct: 100,
      });
      console.log('[SSE-DEBUG] job_completed → AFTER updateJob, new state=',
        'progress_pct=', useJobStore.getState().jobs[jobId]?.progress_pct,
        'status=', useJobStore.getState().jobs[jobId]?.status);
      break;

    case 'job_failed':
      store.updateJob(jobId, {
        status: 'failed',
        completed_at: event.timestamp,
        error_message: event.message,
      });
      break;

    case 'job_cancelled':
      store.updateJob(jobId, {
        status: 'cancelled',
        completed_at: event.timestamp,
      });
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
