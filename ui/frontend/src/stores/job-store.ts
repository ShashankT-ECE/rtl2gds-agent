// ============================================================
// Job Store — pipeline job state and event buffers
// ============================================================

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type {
  JobState,
  JobStatus,
  PipelineEvent,
  RunResponse,
  StageInfo,
  StageStatus,
} from '@/lib/types';
import { MAX_EVENTS_PER_JOB } from '@/lib/constants';
import { buildStageMap, getStagesForVersion } from '@/lib/pipeline-utils';
import type { PipelineVersion } from '@/lib/types';

interface JobStoreState {
  // State
  jobs: Record<string, JobState>;
  activeJobId: string | null;

  // Computed (via getters)
  // activeJob, isRunning

  // Actions
  addJob: (job: RunResponse) => void;
  updateJob: (jobId: string, patch: Partial<RunResponse>) => void;
  setActiveJob: (jobId: string | null) => void;
  updateStage: (jobId: string, stage: string, update: Partial<StageInfo>) => void;
  addEvent: (event: PipelineEvent) => void;
  clearCompletedJobs: () => void;
}

function createInitialJobState(job: RunResponse): JobState {
  return {
    ...job,
    events: [],
    sseConnected: false,
  };
}

export const useJobStore = create<JobStoreState>()(
  devtools(
    (set, get) => ({
      jobs: {},
      activeJobId: null,

      addJob: (job) =>
        set((state) => {
          const existing = state.jobs[job.job_id];
          return {
            jobs: {
              ...state.jobs,
              [job.job_id]: existing
                ? { ...existing, ...job }
                : createInitialJobState(job),
            },
            ...(state.activeJobId === null ? { activeJobId: job.job_id } : {}),
          };
        }, false, 'addJob'),

      updateJob: (jobId, patch) =>
        set((state) => {
          const existing = state.jobs[jobId];
          if (!existing) return state;
          return {
            jobs: {
              ...state.jobs,
              [jobId]: { ...existing, ...patch },
            },
          };
        }, false, 'updateJob'),

      setActiveJob: (jobId) =>
        set({ activeJobId: jobId }, false, 'setActiveJob'),

      updateStage: (jobId, stageName, update) =>
        set((state) => {
          const job = state.jobs[jobId];
          if (!job) return state;
          const stages = job.stages.map((s) =>
            s.name === stageName ? { ...s, ...update } : s
          );
          // If stage doesn't exist yet, add it
          if (!stages.find((s) => s.name === stageName)) {
            stages.push({
              name: stageName,
              status: 'pending' as StageStatus,
              ...update,
            });
          }
          return {
            jobs: {
              ...state.jobs,
              [jobId]: { ...job, stages },
            },
          };
        }, false, 'updateStage'),

      addEvent: (event) =>
        set((state) => {
          const job = state.jobs[event.job_id];
          if (!job) return state;
          const events = [...job.events, event];
          // Ring buffer: keep only the last MAX_EVENTS_PER_JOB events
          if (events.length > MAX_EVENTS_PER_JOB) {
            events.splice(0, events.length - MAX_EVENTS_PER_JOB);
          }
          return {
            jobs: {
              ...state.jobs,
              [event.job_id]: {
                ...job,
                events,
                event_count: events.length,
              },
            },
          };
        }, false, 'addEvent'),

      clearCompletedJobs: () =>
        set((state) => {
          const newJobs: Record<string, JobState> = {};
          for (const [id, job] of Object.entries(state.jobs)) {
            const isTerminal: JobStatus[] = ['completed', 'failed', 'cancelled'];
            if (!isTerminal.includes(job.status as JobStatus)) {
              newJobs[id] = job;
            }
          }
          return { jobs: newJobs };
        }, false, 'clearCompletedJobs'),
    }),
    { name: 'job-store' }
  )
);

// Selectors
export const selectActiveJob = (state: JobStoreState): JobState | null =>
  state.activeJobId ? state.jobs[state.activeJobId] ?? null : null;

export const selectIsRunning = (state: JobStoreState): boolean => {
  const job = selectActiveJob(state);
  return job?.status === 'running';
};

export const selectJobList = (state: JobStoreState): JobState[] =>
  Object.values(state.jobs).sort((a, b) =>
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );
