// ============================================================
// Demo Mode Store — realistic event simulation engine
// Generates believable RTL→GDS pipeline events for demos
// ============================================================

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type {
  PipelineEvent,
  Severity,
  EventType,
  JobStatus,
  StageStatus,
} from '@/lib/types';
import { STAGES_BY_VERSION } from '@/lib/constants';
import type { PipelineVersion } from '@/lib/types';

// Agent definitions for the collaboration view
export interface DemoAgent {
  id: string;
  name: string;
  icon: string;
  role: string;
  currentTask: string;
  status: 'idle' | 'active' | 'completed' | 'blocked' | 'error';
  progress: number;
  startedAt: string | null;
  completedAt: string | null;
  dependencies: string[];
  lastAction: string;
}

// Stage detail for the interactive pipeline
export interface DemoStageDetail {
  stageName: string;
  status: StageStatus;
  startedAt: string | null;
  completedAt: string | null;
  agent: string;
  inputs: string[];
  outputs: string[];
  logs: string[];
  artifacts: string[];
  reports: string[];
}

// Live metrics
export interface LiveMetrics {
  area: number;           // μm²
  power: number;          // mW
  timingSlack: number;    // ns
  violations: number;
  runtime: number;        // seconds
  tokensConsumed: number;
  iterations: number;
  memoryUsage: number;    // MB
  successProbability: number; // 0-100
  cellCount: number;
  frequency: number;      // MHz
}

interface DemoStoreState {
  // Mode
  demoEnabled: boolean;
  toggleDemo: () => void;
  setDemoEnabled: (v: boolean) => void;

  // Simulation state
  isSimulating: boolean;
  simJobId: string | null;
  simStartTime: string | null;
  simSeqNum: number;
  simStageIndex: number;
  simTimer: ReturnType<typeof setInterval> | null;

  // Simulated data
  agents: DemoAgent[];
  stageDetails: DemoStageDetail[];
  metrics: LiveMetrics;
  timelineEvents: Array<{
    time: string;
    event: string;
    detail: string;
    stage: string;
    status: 'completed' | 'running' | 'failed';
  }>;

  // Actions
  startSimulation: (version?: PipelineVersion) => void;
  stopSimulation: () => void;
  generateEvent: () => PipelineEvent | null;
}

const DEMO_AGENTS: DemoAgent[] = [
  {
    id: 'spec-parser',
    name: 'Spec Parser',
    icon: '🤖', // 🤖
    role: 'Parse natural language specifications into structured design constraints',
    currentTask: 'Analyzing specification...',
    status: 'idle',
    progress: 0,
    startedAt: null,
    completedAt: null,
    dependencies: [],
    lastAction: 'Waiting for input',
  },
  {
    id: 'verification-planner',
    name: 'Verification Planner',
    icon: '🔍', // 🔍
    role: 'Generate verification strategy and test plan',
    currentTask: 'Planning verification...',
    status: 'idle',
    progress: 0,
    startedAt: null,
    completedAt: null,
    dependencies: ['spec-parser'],
    lastAction: 'Waiting for specification',
  },
  {
    id: 'rtl-generator',
    name: 'RTL Generator',
    icon: '⚙️', // ⚙️
    role: 'Generate synthesizable RTL from specification',
    currentTask: 'Generating RTL...',
    status: 'idle',
    progress: 0,
    startedAt: null,
    completedAt: null,
    dependencies: ['spec-parser'],
    lastAction: 'Waiting for specification',
  },
  {
    id: 'testbench-agent',
    name: 'Testbench Agent',
    icon: '🧪', // 🧪
    role: 'Generate cocotb testbench and test vectors',
    currentTask: 'Writing testbench...',
    status: 'idle',
    progress: 0,
    startedAt: null,
    completedAt: null,
    dependencies: ['rtl-generator'],
    lastAction: 'Waiting for RTL',
  },
  {
    id: 'simulation-agent',
    name: 'Simulation Agent',
    icon: '💻', // 💻
    role: 'Run Icarus Verilog simulation and collect results',
    currentTask: 'Running simulation...',
    status: 'idle',
    progress: 0,
    startedAt: null,
    completedAt: null,
    dependencies: ['testbench-agent'],
    lastAction: 'Waiting for testbench',
  },
  {
    id: 'debug-agent',
    name: 'Debug Agent',
    icon: '🔧', // 🔧
    role: 'Analyze failures and propose fixes',
    currentTask: 'Monitoring for failures...',
    status: 'idle',
    progress: 0,
    startedAt: null,
    completedAt: null,
    dependencies: ['simulation-agent'],
    lastAction: 'Standing by',
  },
  {
    id: 'synthesis-agent',
    name: 'Synthesis Agent',
    icon: '🔲', // 🔲
    role: 'Run Yosys synthesis and optimize netlist',
    currentTask: 'Synthesizing...',
    status: 'idle',
    progress: 0,
    startedAt: null,
    completedAt: null,
    dependencies: ['simulation-agent'],
    lastAction: 'Waiting for verified RTL',
  },
  {
    id: 'sta-agent',
    name: 'STA Agent',
    icon: '⏱️', // ⏱️
    role: 'Static timing analysis with OpenSTA',
    currentTask: 'Analyzing timing...',
    status: 'idle',
    progress: 0,
    startedAt: null,
    completedAt: null,
    dependencies: ['synthesis-agent'],
    lastAction: 'Waiting for netlist',
  },
  {
    id: 'physical-design-agent',
    name: 'Physical Design Agent',
    icon: '🏗️', // 🏗️
    role: 'Floorplan, place, CTS, route with OpenLane',
    currentTask: 'Floorplanning...',
    status: 'idle',
    progress: 0,
    startedAt: null,
    completedAt: null,
    dependencies: ['sta-agent'],
    lastAction: 'Waiting for timing closure',
  },
  {
    id: 'drc-agent',
    name: 'DRC Agent',
    icon: '✅', // ✅
    role: 'Design rule checking with KLayout',
    currentTask: 'Checking DRC...',
    status: 'idle',
    progress: 0,
    startedAt: null,
    completedAt: null,
    dependencies: ['physical-design-agent'],
    lastAction: 'Waiting for GDSII',
  },
];

const INITIAL_METRICS: LiveMetrics = {
  area: 0,
  power: 0,
  timingSlack: 0,
  violations: 0,
  runtime: 0,
  tokensConsumed: 0,
  iterations: 0,
  memoryUsage: 0,
  successProbability: 0,
  cellCount: 0,
  frequency: 0,
};

// Realistic stage event templates
const STAGE_EVENTS: Record<string, Array<{ type: EventType; message: string; severity: Severity; delayMs: number }>> = {
  spec_parser: [
    { type: 'stage_started', message: 'Parsing design specification...', severity: 'info', delayMs: 800 },
    { type: 'agent_log', message: 'Extracted module interface: input [7:0] a, b; output [15:0] result', severity: 'info', delayMs: 600 },
    { type: 'agent_log', message: 'Identified clock domain: single clock @ 100MHz', severity: 'info', delayMs: 400 },
    { type: 'agent_log', message: 'Detected reset: active-high synchronous', severity: 'info', delayMs: 400 },
    { type: 'stage_completed', message: 'Specification parsed successfully', severity: 'success', delayMs: 300 },
  ],
  verification_planner: [
    { type: 'stage_started', message: 'Generating verification strategy...', severity: 'info', delayMs: 600 },
    { type: 'agent_log', message: 'Coverage goals: 95% statement, 90% branch', severity: 'info', delayMs: 500 },
    { type: 'agent_log', message: 'Test plan: 12 directed tests, 4 random tests', severity: 'info', delayMs: 400 },
    { type: 'agent_log', message: 'Edge cases identified: overflow, zero-input, max-value', severity: 'warning', delayMs: 300 },
    { type: 'stage_completed', message: 'Verification plan ready', severity: 'success', delayMs: 300 },
  ],
  rtl_gen: [
    { type: 'stage_started', message: 'Generating RTL from specification...', severity: 'info', delayMs: 500 },
    { type: 'llm_call_start', message: 'LLM: Generating ALU module with DeepSeek', severity: 'info', delayMs: 1200 },
    { type: 'llm_call_end', message: 'LLM: Generated 85 lines of RTL', severity: 'success', delayMs: 300 },
    { type: 'tool_call', message: 'Tool: Running basic syntax check', severity: 'info', delayMs: 500 },
    { type: 'stage_completed', message: 'RTL generation complete', severity: 'success', delayMs: 300 },
  ],
  testbench: [
    { type: 'stage_started', message: 'Generating cocotb testbench...', severity: 'info', delayMs: 600 },
    { type: 'llm_call_start', message: 'LLM: Generating test vectors for corner cases', severity: 'info', delayMs: 1000 },
    { type: 'tool_call', message: 'Tool: Validating testbench syntax', severity: 'info', delayMs: 400 },
    { type: 'stage_completed', message: 'Testbench ready with 16 test cases', severity: 'success', delayMs: 400 },
  ],
  simulation: [
    { type: 'stage_started', message: 'Launching Icarus Verilog simulation...', severity: 'info', delayMs: 700 },
    { type: 'tool_call', message: 'Tool: iverilog -o sim.vvp alu.v tb_alu.v', severity: 'debug', delayMs: 500 },
    { type: 'tool_call', message: 'Tool: vvp sim.vvp +define+COCOTB', severity: 'debug', delayMs: 800 },
    { type: 'simulation_result', message: '14/16 tests passing, 2 failures in overflow case', severity: 'warning', delayMs: 600 },
    { type: 'stage_completed', message: 'Simulation complete — 87.5% pass rate', severity: 'warning', delayMs: 300 },
  ],
  log_analysis: [
    { type: 'stage_started', message: 'Analyzing simulation failures...', severity: 'info', delayMs: 500 },
    { type: 'agent_log', message: 'Error type: LOGIC — overflow flag not set on max input', severity: 'error', delayMs: 400 },
    { type: 'skill_retrieved', message: 'Trace2Skill: Found similar overflow fix (85% confidence)', severity: 'info', delayMs: 500 },
    { type: 'stage_completed', message: 'Root cause identified', severity: 'success', delayMs: 300 },
  ],
  fix: [
    { type: 'stage_started', message: 'Applying fix for overflow bug...', severity: 'info', delayMs: 600 },
    { type: 'fix_attempt', message: 'Fix attempt 1: Added overflow detection logic', severity: 'info', delayMs: 800 },
    { type: 'skill_stored', message: 'Trace2Skill: Stored new fix pattern for overflow', severity: 'success', delayMs: 300 },
    { type: 'stage_completed', message: 'Fix applied successfully', severity: 'success', delayMs: 300 },
  ],
  testbench_re: [
    { type: 'stage_started', message: 'Regenerating testbench with fix coverage...', severity: 'info', delayMs: 500 },
    { type: 'llm_call_start', message: 'LLM: Adding directed tests for overflow scenario', severity: 'info', delayMs: 800 },
    { type: 'stage_completed', message: 'Testbench updated with 2 new tests', severity: 'success', delayMs: 300 },
  ],
  simulation_re: [
    { type: 'stage_started', message: 'Re-running simulation with fixes...', severity: 'info', delayMs: 600 },
    { type: 'simulation_result', message: '16/16 tests passing', severity: 'success', delayMs: 700 },
    { type: 'stage_completed', message: 'All tests passing!', severity: 'success', delayMs: 300 },
  ],
  synthesis: [
    { type: 'stage_started', message: 'Running Yosys synthesis with sky130...', severity: 'info', delayMs: 800 },
    { type: 'tool_call', message: 'Tool: yosys -p "synth -top alu; abc -liberty sky130_fd_sc_hd.lib"', severity: 'debug', delayMs: 1200 },
    { type: 'synthesis_result', message: 'Synthesis: 248 cells, 0.0142 mm² area', severity: 'success', delayMs: 500 },
    { type: 'stage_completed', message: 'Synthesis complete — 248 standard cells', severity: 'success', delayMs: 300 },
  ],
  sta: [
    { type: 'stage_started', message: 'Running static timing analysis...', severity: 'info', delayMs: 700 },
    { type: 'tool_call', message: 'Tool: opensta -no_splash -exit sta.tcl', severity: 'debug', delayMs: 1000 },
    { type: 'sta_result', message: 'STA: WNS = +0.08ns, TNS = 0.00ns — timing MET', severity: 'success', delayMs: 500 },
    { type: 'stage_completed', message: 'Timing analysis complete — slack positive', severity: 'success', delayMs: 300 },
  ],
  openlane: [
    { type: 'stage_started', message: 'Launching OpenLane physical design flow...', severity: 'info', delayMs: 1000 },
    { type: 'tool_call', message: 'Stage: Floorplanning — core area 80×80μm', severity: 'debug', delayMs: 800 },
    { type: 'tool_call', message: 'Stage: Placement — HPWL 4.2μm', severity: 'debug', delayMs: 800 },
    { type: 'tool_call', message: 'Stage: CTS — inserted 12 clock buffers', severity: 'debug', delayMs: 800 },
    { type: 'tool_call', message: 'Stage: Routing — 98.2% routed, 0 shorts', severity: 'debug', delayMs: 900 },
    { type: 'agent_log', message: 'OpenLane: GDSII generated successfully', severity: 'success', delayMs: 500 },
    { type: 'stage_completed', message: 'Physical design complete — GDSII ready', severity: 'success', delayMs: 400 },
  ],
  drc: [
    { type: 'stage_started', message: 'Running DRC with KLayout...', severity: 'info', delayMs: 700 },
    { type: 'tool_call', message: 'Tool: klayout -b -r drc_check.lyrdb -rd input=output.gds', severity: 'debug', delayMs: 1200 },
    { type: 'drc_result', message: 'DRC: 0 violations — CLEAN', severity: 'success', delayMs: 500 },
    { type: 'stage_completed', message: 'DRC passed — design is DRC clean!', severity: 'success', delayMs: 300 },
  ],
};

function buildPipelineStages(version: PipelineVersion): string[] {
  const stages = STAGES_BY_VERSION[version] as readonly string[];
  // For V2/V3, add fix loop + re-test after simulation
  if (version === 'v2' || version === 'v3') {
    const result: string[] = [];
    for (const s of stages) {
      result.push(s);
      if (s === 'simulation') {
        result.push('log_analysis', 'fix', 'testbench_re', 'simulation_re');
      }
    }
    return result;
  }
  return [...stages];
}

export const useDemoStore = create<DemoStoreState>()(
  devtools(
    persist(
      (set, get) => ({
        demoEnabled: false,
        toggleDemo: () => set((s) => {
          const next = !s.demoEnabled;
          if (next) {
            // When enabling demo, auto-start simulation
            setTimeout(() => get().startSimulation(), 500);
          } else {
            get().stopSimulation();
          }
          return { demoEnabled: next };
        }),
        setDemoEnabled: (v) => set({ demoEnabled: v }),

        isSimulating: false,
        simJobId: null,
        simStartTime: null,
        simSeqNum: 0,
        simStageIndex: -1,
        simTimer: null,

        agents: DEMO_AGENTS.map((a) => ({ ...a })),
        stageDetails: [],
        metrics: { ...INITIAL_METRICS },
        timelineEvents: [],

        startSimulation: (version = 'v3') => {
          const state = get();
          // Clean up existing timer
          if (state.simTimer) clearInterval(state.simTimer);

          const jobId = `demo-${Date.now()}`;
          const stages = buildPipelineStages(version);
          const now = new Date().toISOString();

          // Initialize stage details
          const stageDetails: DemoStageDetail[] = stages.map((name) => ({
            stageName: name,
            status: 'pending' as StageStatus,
            startedAt: null,
            completedAt: null,
            agent: name,
            inputs: [],
            outputs: [],
            logs: [],
            artifacts: [],
            reports: [],
          }));

          set({
            isSimulating: true,
            simJobId: jobId,
            simStartTime: now,
            simSeqNum: 0,
            simStageIndex: 0,
            simTimer: null,
            agents: DEMO_AGENTS.map((a) => ({ ...a, status: 'idle' as const, progress: 0, startedAt: null, completedAt: null })),
            stageDetails,
            metrics: { ...INITIAL_METRICS },
            timelineEvents: [{
              time: new Date().toLocaleTimeString('en-US', { hour12: false }),
              event: 'Pipeline Started',
              detail: `Job ${jobId} initiated with ${version.toUpperCase()} flow`,
              stage: 'pipeline',
              status: 'running' as const,
            }],
          });

          // Start the simulation loop
          const timer = setInterval(() => {
            get().generateEvent();
          }, 150);

          set({ simTimer: timer });
        },

        stopSimulation: () => {
          const state = get();
          if (state.simTimer) {
            clearInterval(state.simTimer);
          }
          set({
            isSimulating: false,
            simTimer: null,
          });
        },

        generateEvent: () => {
          const state = get();
          if (!state.isSimulating) return null;

          const stages = state.stageDetails;
          const stageIdx = state.simStageIndex;
          if (stageIdx >= stages.length) {
            // All stages complete — finish simulation
            get().stopSimulation();
            const now = new Date().toLocaleTimeString('en-US', { hour12: false });
            set((s) => ({
              metrics: { ...s.metrics, successProbability: 100 },
              timelineEvents: [...s.timelineEvents, {
                time: now,
                event: 'GDSII Exported',
                detail: 'Design is DRC-clean and ready for tapeout',
                stage: 'complete',
                status: 'completed' as const,
              }],
            }));
            return null;
          }

          const stageName = stages[stageIdx].stageName;
          const eventTemplates = STAGE_EVENTS[stageName] || [];
          const stageEvents = stages[stageIdx];

          // Find the next event to emit for this stage
          const emittedCount = stageEvents.logs.length;
          if (emittedCount >= eventTemplates.length) {
            // This stage is complete, move to next
            set((s) => ({
              simStageIndex: s.simStageIndex + 1,
            }));
            return get().generateEvent(); // recurse to next stage
          }

          const template = eventTemplates[emittedCount];
          const seqNum = state.simSeqNum + 1;
          const now = new Date();
          const eventId = crypto.randomUUID();
          const timestamp = now.toISOString();
          const timeStr = now.toLocaleTimeString('en-US', { hour12: false });

          // Build the event
          const event: PipelineEvent = {
            event_id: eventId,
            job_id: state.simJobId!,
            timestamp,
            event_type: template.type,
            stage: stageName,
            message: template.message,
            severity: template.severity,
            payload: {},
            elapsed_time: null,
            iteration: null,
            sequence_num: seqNum,
          };

          // Add type-specific payload
          if (template.type === 'simulation_result') {
            event.payload = { passed: emittedCount === eventTemplates.length - 1 ? true : false, coverage_pct: 87.5 };
          } else if (template.type === 'synthesis_result') {
            event.payload = { cell_count: 248, area: '0.0142', frequency: '450' };
          } else if (template.type === 'sta_result') {
            event.payload = { timing_met: true, wns: 0.08, tns: 0.0, critical_path: 'alu/core/result_reg[15]/D' };
          } else if (template.type === 'drc_result') {
            event.payload = { drc_passed: true, violations: 0 };
          } else if (template.type === 'fix_attempt') {
            event.iteration = 1;
          }

          // Update stage details
          const updatedStageDetails = [...state.stageDetails];
          const detail = updatedStageDetails[stageIdx];
          if (template.type === 'stage_started') {
            detail.status = 'running';
            detail.startedAt = timestamp;
          } else if (template.type === 'stage_completed') {
            detail.status = 'completed';
            detail.completedAt = timestamp;
          }
          detail.logs.push(`[${timeStr}] ${template.message}`);

          // Update timeline
          const timelineEvents = [...state.timelineEvents];
          if (template.type === 'stage_started' || template.type === 'stage_completed' || template.type === 'stage_failed') {
            timelineEvents.push({
              time: timeStr,
              event: template.message,
              detail: `Stage: ${stageName}`,
              stage: stageName,
              status: template.type === 'stage_failed' ? 'failed' : template.type === 'stage_started' ? 'running' : 'completed',
            });
          }

          // Update metrics progressively
          const metrics = { ...state.metrics };
          const totalStages = stages.length;
          const completedStages = updatedStageDetails.filter((s) => s.status === 'completed').length;
          const runningStages = updatedStageDetails.filter((s) => s.status === 'running').length;
          metrics.runtime = Math.round((now.getTime() - new Date(state.simStartTime!).getTime()) / 1000);
          metrics.iterations = event.iteration || metrics.iterations;
          metrics.tokensConsumed += Math.floor(Math.random() * 500) + 200;
          metrics.memoryUsage = Math.round(120 + Math.random() * 80);
          metrics.successProbability = Math.min(100, Math.round((completedStages / totalStages) * 100));

          if (stageName === 'synthesis' && template.type === 'synthesis_result') {
            metrics.area = 14200;
            metrics.cellCount = 248;
            metrics.frequency = 450;
            metrics.power = 2.8;
          }
          if (stageName === 'sta' && template.type === 'sta_result') {
            metrics.timingSlack = 0.08;
          }
          if (stageName === 'drc' && template.type === 'drc_result') {
            metrics.violations = 0;
          }

          // Update agents
          const updatedAgents = state.agents.map((agent) => {
            const agentStageMap: Record<string, string> = {
              spec_parser: 'spec-parser',
              verification_planner: 'verification-planner',
              rtl_gen: 'rtl-generator',
              testbench: 'testbench-agent',
              testbench_re: 'testbench-agent',
              simulation: 'simulation-agent',
              simulation_re: 'simulation-agent',
              log_analysis: 'debug-agent',
              fix: 'debug-agent',
              synthesis: 'synthesis-agent',
              sta: 'sta-agent',
              openlane: 'physical-design-agent',
              drc: 'drc-agent',
            };
            const agentId = agentStageMap[stageName];
            if (agentId !== agent.id) return agent;

            if (template.type === 'stage_started') {
              return { ...agent, status: 'active' as const, currentTask: template.message, startedAt: timestamp, progress: 10 };
            }
            if (template.type === 'stage_completed') {
              return { ...agent, status: 'completed' as const, completedAt: timestamp, progress: 100, lastAction: template.message, currentTask: 'Complete' };
            }
            if (template.type === 'agent_log') {
              return { ...agent, currentTask: template.message, progress: Math.min(100, agent.progress + 25), lastAction: agent.currentTask };
            }
            return agent;
          });

          set({
            simSeqNum: seqNum,
            stageDetails: updatedStageDetails,
            timelineEvents,
            metrics,
            agents: updatedAgents,
          });

          return event;
        },
      }),
      {
        name: 'demo-store',
        partialize: (state) => ({ demoEnabled: state.demoEnabled }),
      }
    ),
    { name: 'demo-store' }
  )
);
