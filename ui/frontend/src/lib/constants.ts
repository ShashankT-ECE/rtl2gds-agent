// ============================================================
// Application constants — API paths, stage definitions, labels
// ============================================================

import type { PipelineVersion } from './types';

// --- API ---

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export const API_PATHS = {
  health: '/health',
  status: '/status',
  benchmarks: '/api/benchmarks',
  benchmark: (name: string) => `/api/benchmarks/${name}`,
  skills: '/api/skills',
  skillCategory: (category: string) => `/api/skills/${category}`,
  run: '/api/run',
  runJob: (jobId: string) => `/api/run/${jobId}`,
  cancelJob: (jobId: string) => `/api/run/${jobId}/cancel`,
  runStream: (jobId: string, after?: number) =>
    `/api/run/stream?job_id=${jobId}${after !== undefined ? `&after=${after}` : ''}`,
} as const;

// --- Pipeline Stages ---

export const V1_STAGES = [
  'spec_parser', 'verification_planner', 'rtl_gen', 'testbench',
  'simulation', 'log_analysis', 'fix', 'testbench_re', 'simulation_re',
] as const;

export const V2_STAGES = [
  'spec_parser', 'verification_planner', 'rtl_gen', 'testbench',
  'simulation', 'synthesis', 'sta',
] as const;

export const V3_STAGES = [
  'spec_parser', 'verification_planner', 'rtl_gen', 'testbench',
  'simulation', 'synthesis', 'sta', 'openlane', 'drc',
] as const;

export const STAGES_BY_VERSION: Record<PipelineVersion, readonly string[]> = {
  v1: V1_STAGES,
  v2: V2_STAGES,
  v3: V3_STAGES,
};

// --- Stage Display Labels ---

export const STAGE_LABELS: Record<string, string> = {
  spec_parser: 'Spec Parser',
  verification_planner: 'Verif. Planner',
  rtl_gen: 'RTL Gen',
  testbench: 'TB Gen',
  testbench_re: 'TB (re)',
  simulation: 'Simulation',
  simulation_re: 'Sim (re)',
  log_analysis: 'Log Analysis',
  fix: 'Fix Agent',
  synthesis: 'Synthesis',
  sta: 'STA',
  openlane: 'OpenLane',
  drc: 'DRC',
};

export const STAGE_AGENTS: Record<string, string> = {
  spec_parser: 'spec_parser_agent',
  verification_planner: 'verification_planner_agent',
  rtl_gen: 'rtl_gen_agent',
  testbench: 'testbench_agent',
  testbench_re: 'testbench_agent',
  simulation: 'simulation_agent',
  simulation_re: 'simulation_agent',
  log_analysis: 'log_analysis_agent',
  fix: 'fix_agent',
  synthesis: 'synthesis_agent',
  sta: 'sta_agent',
  openlane: 'openlane_agent',
  drc: 'drc_agent',
};

// --- FIX LOOP STAGES (show curved return path in flow) ---

export const FIX_LOOP_STAGES = ['log_analysis', 'fix', 'testbench_re', 'simulation_re'];

// --- Version Display Info ---

export const VERSION_INFO: Record<PipelineVersion, { label: string; description: string }> = {
  v1: {
    label: 'V1',
    description: 'RTL generation + simulation + fix loop (~20-30s)',
  },
  v2: {
    label: 'V2',
    description: 'V1 + Yosys synthesis + OpenSTA timing (~30-60s)',
  },
  v3: {
    label: 'V3',
    description: 'V2 + OpenLane 2 physical design + KLayout DRC (~20-45min)',
  },
};

// --- Category Display Info ---

export const CATEGORY_INFO: Record<string, { label: string; icon: string }> = {
  combinational: { label: 'Combinational', icon: 'CircuitBoard' },
  fsm: { label: 'FSM', icon: 'GitBranch' },
  fifo: { label: 'FIFO', icon: 'Layers' },
  axi: { label: 'AXI', icon: 'Network' },
  timing: { label: 'Timing', icon: 'Clock' },
};

// --- Job Status Display ---

export const JOB_STATUS_COLORS: Record<string, string> = {
  queued: '#4f5b73',
  running: '#4e9cf5',
  completed: '#2ea86c',
  failed: '#e05045',
  cancelled: '#6b7a94',
};

export const JOB_STATUS_LABELS: Record<string, string> = {
  queued: 'Queued',
  running: 'Running',
  completed: 'Completed',
  failed: 'Failed',
  cancelled: 'Cancelled',
};

// --- Severity Colors ---

export const SEVERITY_COLORS: Record<string, string> = {
  debug: '#4f5b73',
  info: '#b8c4d6',
  success: '#2ea86c',
  warning: '#e0b030',
  error: '#e05045',
};

// --- Error Type Colors ---

export const ERROR_TYPE_COLORS: Record<string, string> = {
  SYNTAX: '#e05045',
  WIDTH: '#e0b030',
  LOGIC: '#f09837',
  TIMING: '#4e9cf5',
  COVERAGE: '#6b7a94',
  UNKNOWN: '#4f5b73',
};

// --- SSE ---

export const SSE_MAX_RECONNECT_ATTEMPTS = 10;
export const SSE_RECONNECT_BACKOFF_MS = [1000, 2000, 4000, 8000, 16000, 30000];
export const MAX_EVENTS_PER_JOB = 500;

// --- Polling ---

export const POLLING_INTERVAL_MS =
  Number(process.env.NEXT_PUBLIC_POLLING_INTERVAL_MS) || 2000;
