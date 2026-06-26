'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { AppShell } from '@/components/layout/app-shell';
import { PageContainer } from '@/components/layout/page-container';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useSubmitJob } from '@/hooks/use-job-list';
import { useBenchmarks } from '@/hooks/use-benchmarks';
import { useJobStore } from '@/stores/job-store';
import { useUIStore } from '@/stores/ui-store';
import type { PipelineVersion } from '@/lib/types';
import { VERSION_INFO } from '@/lib/constants';

const PDK_OPTIONS = [
  { label: 'sky130 (Open Source)', value: 'sky130' },
  { label: 'TSMC 7nm (N7)', value: 'tsmc7' },
  { label: 'Intel 18A', value: 'intel18a' },
  { label: 'GlobalFoundries 22FDX', value: 'gf22fdx' },
];

const FLOW_OPTIONS = [
  { label: 'Standard Logic Synthesis', value: 'standard' },
  { label: 'High-Performance / Low Power', value: 'hp_lp' },
  { label: 'Custom Physical Design', value: 'custom' },
];

const VERSIONS: { value: PipelineVersion; label: string }[] = [
  { value: 'v3', label: 'V3 — Full Physical (Spec → GDSII)' },
  { value: 'v2', label: 'V2 — Synthesis + STA' },
  { value: 'v1', label: 'V1 — RTL + Simulation' },
];

export default function NewProjectPage() {
  const router = useRouter();
  const submitJob = useSubmitJob();
  const setActiveJob = useJobStore((s) => s.setActiveJob);
  const setSelectedBenchmark = useUIStore((s) => s.setSelectedBenchmark);
  const { data: benchmarkData } = useBenchmarks();
  const benchmarks = benchmarkData?.benchmarks || [];

  const [benchmark, setBenchmark] = useState('alu_8bit');
  const [projectName, setProjectName] = useState('ALU 8-Bit Processor');
  const [pdk, setPdk] = useState('sky130');
  const [flow, setFlow] = useState('standard');
  const [version, setVersion] = useState<PipelineVersion>('v1');
  const [maxIterations, setMaxIterations] = useState(5);

  const handleSubmit = async () => {
    setSelectedBenchmark(benchmark);

    try {
      const result = await submitJob.mutateAsync({
        benchmark,
        pipeline_version: version,
        max_iterations: maxIterations,
        use_reference_rtl: false,
        use_reference_tb: false,
      });
      setActiveJob(result.job_id);
      router.push('/dashboard');
    } catch {
      // Error handled by TanStack Query
    }
  };

  const pdkLabel = PDK_OPTIONS.find(p => p.value === pdk)?.label || pdk;
  const flowLabel = FLOW_OPTIONS.find(f => f.value === flow)?.label || flow;

  return (
    <AppShell>
      <div className="flex flex-1 overflow-hidden">
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-4xl mx-auto flex gap-6">
            {/* Left Column: Form */}
            <div className="flex-1 space-y-6">
              {/* Section 1: Design Selection */}
              <div className="bg-card border border-border rounded-lg p-6">
                <div className="border-b border-border pb-4 mb-4 flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-foreground flex items-center gap-3">
                    <span className="bg-accent rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">
                      1
                    </span>
                    Design Selection
                  </h2>
                </div>
                <div className="space-y-4">
                  <div>
                    <Label className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground mb-2 block">
                      Benchmark Design
                    </Label>
                    <select
                      className="w-full bg-surface-container-lowest border border-border rounded px-3 py-2 font-mono text-sm text-foreground focus:outline-none focus:border-primary"
                      value={benchmark}
                      onChange={(e) => {
                        setBenchmark(e.target.value);
                        setProjectName(e.target.value.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()));
                      }}
                    >
                      {benchmarks.map((b) => (
                        <option key={b.name} value={b.name}>
                          {b.name} {b.has_bugs ? `(${b.bug_count} bugs)` : '(reference)'}
                        </option>
                      ))}
                    </select>
                    <p className="text-[11px] text-muted-foreground mt-1">
                      Select an existing benchmark design. Upload support for custom RTL is in development.
                    </p>
                  </div>
                  <div>
                    <Label className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground mb-2 block">
                      Project Name
                    </Label>
                    <Input
                      className="bg-surface-container-lowest border-border font-mono text-sm text-foreground"
                      type="text"
                      value={projectName}
                      onChange={(e) => setProjectName(e.target.value)}
                    />
                  </div>
                </div>
              </div>

              {/* Section 2: Environment Configuration */}
              <div className="bg-card border border-border rounded-lg p-6">
                <div className="border-b border-border pb-4 mb-4">
                  <h2 className="text-lg font-semibold text-foreground flex items-center gap-3">
                    <span className="bg-accent rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">
                      2
                    </span>
                    Environment Configuration
                  </h2>
                </div>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground mb-2 block">
                        Target PDK
                      </Label>
                      <select
                        className="w-full bg-surface-container-lowest border border-border rounded px-3 py-2 font-mono text-sm text-foreground focus:outline-none focus:border-primary"
                        value={pdk}
                        onChange={(e) => setPdk(e.target.value)}
                      >
                        {PDK_OPTIONS.map((p) => (
                          <option key={p.value} value={p.value}>{p.label}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <Label className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground mb-2 block">
                        Tool Flow Preset
                      </Label>
                      <select
                        className="w-full bg-surface-container-lowest border border-border rounded px-3 py-2 font-mono text-sm text-foreground focus:outline-none focus:border-primary"
                        value={flow}
                        onChange={(e) => setFlow(e.target.value)}
                      >
                        {FLOW_OPTIONS.map((f) => (
                          <option key={f.value} value={f.value}>{f.label}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div>
                    <Label className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground mb-2 block">
                      Pipeline Version
                    </Label>
                    <div className="flex gap-2">
                      {VERSIONS.map((v) => (
                        <button
                          key={v.value}
                          onClick={() => setVersion(v.value)}
                          className={`px-3 py-2 text-xs font-semibold rounded border transition-all flex-1 text-center ${
                            version === v.value
                              ? 'bg-primary/10 text-primary border-primary/30'
                              : 'text-muted-foreground border-border hover:text-foreground hover:border-muted-foreground'
                          }`}
                          title={VERSION_INFO[v.value]?.description}
                        >
                          {v.label}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="w-24">
                    <Label className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground mb-2 block">
                      Iterations
                    </Label>
                    <Input
                      type="number"
                      min={1}
                      max={20}
                      value={maxIterations}
                      onChange={(e) => setMaxIterations(Number(e.target.value))}
                      className="bg-surface-container-lowest border-border font-mono text-sm text-foreground text-center"
                    />
                  </div>
                </div>
              </div>

              {/* Section 3: Pre-flight Checks */}
              <div className="bg-card border border-border rounded-lg p-6">
                <div className="border-b border-border pb-4 mb-4">
                  <h2 className="text-lg font-semibold text-foreground flex items-center gap-3">
                    <span className="bg-accent rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">
                      3
                    </span>
                    Pre-flight Checks
                  </h2>
                </div>
                <ul className="space-y-3">
                  <li className="flex items-center text-foreground">
                    <span className="material-symbols-outlined text-emerald-500 mr-3 text-sm">check_circle</span>
                    <span className="text-sm">Benchmark design available ({benchmark})</span>
                  </li>
                  <li className="flex items-center text-foreground">
                    <span className="material-symbols-outlined text-emerald-500 mr-3 text-sm">check_circle</span>
                    <span className="text-sm">PDK configuration: {pdkLabel}</span>
                  </li>
                  <li className="flex items-center text-foreground">
                    <span className="material-symbols-outlined text-emerald-500 mr-3 text-sm">check_circle</span>
                    <span className="text-sm">Pipeline ready: {version.toUpperCase()} ({VERSION_INFO[version]?.description})</span>
                  </li>
                </ul>
              </div>
            </div>

            {/* Right Column: Summary */}
            <div className="w-[320px] flex-shrink-0">
              <div className="sticky top-6 bg-card border border-border rounded-lg flex flex-col">
                <div className="p-4 border-b border-border bg-accent">
                  <h3 className="text-[11px] font-bold uppercase tracking-widest text-foreground">
                    Pipeline Summary
                  </h3>
                </div>
                <div className="p-4 flex-1 overflow-y-auto space-y-4">
                  <div>
                    <div className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground mb-1">
                      PROJECT
                    </div>
                    <div className="font-mono text-sm text-foreground">{projectName}</div>
                  </div>
                  <div>
                    <div className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground mb-1">
                      BENCHMARK
                    </div>
                    <div className="font-mono text-sm text-foreground">{benchmark}</div>
                  </div>
                  <div>
                    <div className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground mb-1">
                      PDK
                    </div>
                    <div className="text-sm text-foreground">{pdkLabel}</div>
                  </div>
                  <div>
                    <div className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground mb-1">
                      FLOW
                    </div>
                    <div className="text-sm text-foreground">{flowLabel}</div>
                  </div>
                  <div className="border-t border-border pt-4">
                    <div className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground mb-3">
                      PIPELINE
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between font-mono text-xs">
                        <span className="text-muted-foreground">Version:</span>
                        <span className="text-primary font-semibold">{version.toUpperCase()}</span>
                      </div>
                      <div className="flex justify-between font-mono text-xs">
                        <span className="text-muted-foreground">Max Iterations:</span>
                        <span className="text-foreground">{maxIterations}</span>
                      </div>
                      <div className="flex justify-between font-mono text-xs">
                        <span className="text-muted-foreground">Est. Runtime:</span>
                        <span className="text-foreground">{version === 'v1' ? '20-30s' : version === 'v2' ? '30-60s' : '20-45m'}</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="p-4 border-t border-border">
                  <Button
                    className="w-full bg-primary text-white hover:bg-primary/90 py-3 font-semibold"
                    onClick={handleSubmit}
                    disabled={submitJob.isPending || !benchmark}
                  >
                    <span className="material-symbols-outlined mr-2 text-sm">play_arrow</span>
                    {submitJob.isPending ? 'Starting Pipeline...' : 'Launch Pipeline'}
                  </Button>
                  {submitJob.isError && (
                    <p className="text-xs text-destructive mt-2 text-center">
                      {(submitJob.error as Error)?.message || 'Failed to start job'}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </AppShell>
  );
}
