// ============================================================
// TypeScript type definitions — mirror Pydantic backend schemas
// ============================================================

// --- Enums ---

export type JobStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
export type StageStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
export type PipelineVersion = 'v1' | 'v2' | 'v3';
export type Severity = 'debug' | 'info' | 'success' | 'warning' | 'error';

export const EVENT_TYPES = [
  'job_started', 'job_completed', 'job_failed', 'job_cancelled',
  'stage_started', 'stage_completed', 'stage_failed',
  'agent_log', 'llm_call_start', 'llm_call_end', 'tool_call',
  'fix_attempt', 'skill_retrieved', 'skill_stored', 'convergence_warning',
  'simulation_result', 'synthesis_result', 'sta_result', 'drc_result',
  'heartbeat', 'progress',
] as const;

export type EventType = typeof EVENT_TYPES[number];

export const ERROR_TYPES = ['SYNTAX', 'WIDTH', 'LOGIC', 'TIMING', 'COVERAGE', 'UNKNOWN'] as const;
export type ErrorType = typeof ERROR_TYPES[number];

export const SKILL_CATEGORIES = ['combinational', 'fsm', 'fifo', 'axi', 'timing'] as const;
export type SkillCategory = typeof SKILL_CATEGORIES[number];

// --- API Response Envelope ---

export interface SuccessResponse<T> {
  success: true;
  data: T;
}

export interface ErrorDetail {
  code: string;
  message: string;
  details?: Record<string, unknown> | null;
}

export interface ErrorResponse {
  success: false;
  error: ErrorDetail;
}

export type ApiResponse<T> = SuccessResponse<T> | ErrorResponse;

// --- Health & Status ---

export interface HealthResponse {
  status: string;
  version: string;
  api_version: string;
}

export interface VersionInfo {
  v1_available: boolean;
  v2_available: boolean;
  v3_available: boolean;
}

export interface SystemStatusResponse {
  active_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  queued_jobs: number;
  total_skills: number;
  benchmark_count: number;
  versions: VersionInfo;
  provider: string;
  pipeline_mode: string;
}

// --- Benchmarks ---

export interface BenchmarkBug {
  bug_id: string;
  description: string;
}

export interface BenchmarkInfo {
  name: string;
  spec_preview: string;
  has_reference_rtl: boolean;
  has_reference_tb: boolean;
  has_bugs: boolean;
  bug_count: number;
  category_guess: string | null;
  bugs?: BenchmarkBug[];
}

export interface BenchmarkListResponse {
  benchmarks: BenchmarkInfo[];
  total: number;
}

// --- Skills ---

export interface SkillEntry {
  id: string;
  category: string;
  error_type: string;
  pattern: string;
  fix: string;
  design_name?: string | null;
  success_count: number;
  confirmed_count: number;
  curated: boolean;
  last_seen?: string | null;
  example?: string;
}

export interface SkillCategorySummary {
  category: string;
  total_skills: number;
  curated_count: number;
  confirmed_count: number;
  unconfirmed_count: number;
  error_types: string[];
}

export interface SkillListResponse {
  categories: SkillCategorySummary[];
  total_skills: number;
}

export interface SkillCategoryResponse {
  category: string;
  summary: SkillCategorySummary;
  skills: SkillEntry[];
}

// --- Pipeline Events ---

export interface PipelineEvent {
  event_id: string;
  job_id: string;
  timestamp: string;
  event_type: EventType;
  stage?: string | null;
  message: string;
  severity: Severity;
  payload: Record<string, unknown>;
  elapsed_time?: number | null;
  iteration?: number | null;
  sequence_num: number;
}

// --- Jobs ---

export interface StageInfo {
  name: string;
  status: StageStatus;
  started_at?: string | null;
  completed_at?: string | null;
  elapsed_ms?: number | null;
}

export interface RunRequest {
  benchmark: string;
  pipeline_version: PipelineVersion;
  max_iterations: number;
  use_reference_rtl: boolean;
  use_reference_tb: boolean;
}

export interface RunResponse {
  job_id: string;
  status: JobStatus;
  benchmark: string;
  pipeline_version: string;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  elapsed_seconds?: number | null;
  current_stage: string;
  stages: StageInfo[];
  iteration: number;
  sim_passed?: boolean | null;
  timing_met?: boolean | null;
  drc_passed?: boolean | null;
  progress_pct: number;
  error_message?: string | null;
  event_count: number;
}

export interface RunListResponse {
  jobs: RunResponse[];
  total: number;
}

// --- SSE ---

export interface SSEDoneEvent {
  job_id: string;
  status: JobStatus;
  total_events: number;
}

export interface SSEErrorEvent {
  error: string;
}

export interface SSEHeartbeatEvent {
  timestamp: string;
}

// --- Job State (extended, for Zustand store) ---

export interface JobState extends RunResponse {
  events: PipelineEvent[];
  sseConnected: boolean;
}

// --- SSE Connection ---

export type SSEConnectionStatus = 'connecting' | 'connected' | 'disconnected';

export interface SSEConnectionState {
  status: SSEConnectionStatus;
  lastEventAt: string | null;
  eventCount: number;
  reconnectAttempt: number;
}
