// ============================================================
// useReplayDemo — replay saved real pipeline events through the
// job store with compressed timing (~30 seconds total).
//
// When enabled, loads demo/alu_8bit_demo.json, creates a fake
// job in the job store, and dispatches events sequentially.
// ============================================================

'use client';

import { useCallback, useEffect, useRef } from 'react';
import { useJobStore } from '@/stores/job-store';
import { dispatchEvent } from '@/lib/event-handlers';
import { useDemoStore } from '@/stores/demo-store';
import type { PipelineEvent } from '@/lib/types';

const DEMO_DATA_URL = '/demo/alu_8bit_demo.json';
const REPLAY_DURATION_MS = 30000; // compress to 30 seconds

interface DemoEvent {
  event_type: string;
  sequence_num: number;
  elapsed_time: number | null;
  [key: string]: unknown;
}

export function useReplayDemo(): void {
  const demoEnabled = useDemoStore((s) => s.demoEnabled);
  const replayRef = useRef<{
    events: DemoEvent[];
    timer: ReturnType<typeof setTimeout> | null;
    jobId: string;
    index: number;
    startTime: number;
  } | null>(null);

  const stopReplay = useCallback(() => {
    if (replayRef.current) {
      if (replayRef.current.timer) {
        clearTimeout(replayRef.current.timer);
      }
      replayRef.current = null;
    }
  }, []);

  const startReplay = useCallback(async () => {
    // Clean previous
    stopReplay();

    try {
      const resp = await fetch(DEMO_DATA_URL);
      const data = await resp.json();
      const events: DemoEvent[] = data.events;

      if (!events || events.length === 0) {
        console.error('[ReplayDemo] No events in demo data');
        return;
      }

      const jobId = `demo-${Date.now()}`;
      const jobFromEvent = events[0] as unknown as PipelineEvent;
      const benchmark = (jobFromEvent.payload as Record<string, unknown>)?.benchmark as string || 'alu_8bit';
      const pipelineVersion = (jobFromEvent.payload as Record<string, unknown>)?.pipeline_version as string || 'v3';

      // Add a synthetic job to the store so the UI lights up
      useJobStore.getState().addJob({
        job_id: jobId,
        benchmark,
        pipeline_version: pipelineVersion,
        status: 'running',
        created_at: new Date().toISOString(),
        started_at: new Date().toISOString(),
        completed_at: null,
        current_stage: 'running',
        stages: [],
        iteration: 0,
        sim_passed: null,
        timing_met: null,
        drc_passed: null,
        progress_pct: 0,
        event_count: 0,
        error_message: null,
        elapsed_seconds: null,
      });

      // Set as active job
      useJobStore.getState().setActiveJob(jobId);

      // Calculate replay timing
      // Use real elapsed_time if available, otherwise spread evenly
      const totalRealTime = events.length > 1
        ? Math.max(events[events.length - 1].elapsed_time || REPLAY_DURATION_MS / 1000, 1)
        : 30;

      const scale = REPLAY_DURATION_MS / 1000 / totalRealTime; // time compression factor

      const replay = {
        events,
        timer: null as ReturnType<typeof setTimeout> | null,
        jobId,
        index: 0,
        startTime: Date.now(),
      };

      replayRef.current = replay;

      // Schedule events
      const scheduleNext = () => {
        const r = replayRef.current;
        if (!r || r.index >= r.events.length) {
          // All done — ensure final status
          useJobStore.getState().updateJob(r!.jobId, {
            status: 'completed',
            progress_pct: 100,
            completed_at: new Date().toISOString(),
          });

          // Compound state: close still-running stages
          const job = useJobStore.getState().jobs[r!.jobId];
          if (job) {
            for (const s of job.stages) {
              if (s.status === 'running') {
                useJobStore.getState().updateStage(r!.jobId, s.name, {
                  status: 'completed',
                  completed_at: new Date().toISOString(),
                });
              }
            }
          }
          return;
        }

        const event = r.events[r.index] as unknown as PipelineEvent;
        r.index++;

        // Dispatch through the standard event handler pipeline
        dispatchEvent({
          ...event,
          job_id: r.jobId,
          timestamp: new Date().toISOString(),
        });

        // Calculate delay to next event
        const currentEventTime = event.elapsed_time || (r.index * totalRealTime / r.events.length);
        const nextEvent = r.events[r.index];
        let delayMs = 150; // minimum gap between events

        if (nextEvent) {
          const nextTime = nextEvent.elapsed_time || ((r.index + 1) * totalRealTime / r.events.length);
          const realGap = (nextTime - currentEventTime) * 1000;
          delayMs = Math.max(50, Math.round(realGap * scale));
        }

        // Cap at 3 seconds max delay for smooth UX
        delayMs = Math.min(delayMs, 3000);

        r.timer = setTimeout(scheduleNext, delayMs);
      };

      // Start dispatching
      scheduleNext();
    } catch (err) {
      console.error('[ReplayDemo] Failed to load demo data:', err);
    }
  }, [stopReplay]);

  // Toggle replay when demo mode changes
  useEffect(() => {
    if (demoEnabled) {
      // Small delay to let the demo store initialize its UI state
      const t = setTimeout(() => startReplay(), 500);
      return () => clearTimeout(t);
    } else {
      stopReplay();
    }
  }, [demoEnabled, startReplay, stopReplay]);

  // Cleanup on unmount
  useEffect(() => {
    return () => stopReplay();
  }, [stopReplay]);
}
