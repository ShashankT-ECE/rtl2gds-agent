'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { AppShell } from '@/components/layout/app-shell';
import { PageContainer } from '@/components/layout/page-container';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useSubmitJob } from '@/hooks/use-job-list';
import { useJobStore } from '@/stores/job-store';
import { useUIStore } from '@/stores/ui-store';
import type { PipelineVersion } from '@/lib/types';

const PDK_OPTIONS = [
  'TSMC 7nm (N7)',
  'TSMC 5nm (N5)',
  'Intel 18A',
  'GlobalFoundries 22FDX',
];

const FLOW_OPTIONS = [
  'Standard Logic Synthesis',
  'High-Performance / Low Power',
  'Custom Physical Design',
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

  const [projectName, setProjectName] = useState('core_processor_v4');
  const [pdk, setPdk] = useState(PDK_OPTIONS[0]);
  const [flow, setFlow] = useState(FLOW_OPTIONS[0]);
  const [version, setVersion] = useState<PipelineVersion>('v3');
  const [maxIterations, setMaxIterations] = useState(5);
  const [files, setFiles] = useState<string[]>(['alu_core.v', 'top_constraints.sdc']);
  const [isDragging, setIsDragging] = useState(false);

  const handleSubmit = async () => {
    // Use the first file name as the benchmark identifier
    setSelectedBenchmark(projectName);

    try {
      const result = await submitJob.mutateAsync({
        benchmark: projectName,
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

  return (
    <AppShell>
      <div className="flex flex-1 overflow-hidden">
        {/* Main Content */}
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-4xl mx-auto flex gap-6">
            {/* Left Column: Form */}
            <div className="flex-1 space-y-6">
              {/* Section 1: Environment Configuration */}
              <div className="bg-card border border-border rounded-lg p-6">
                <div className="border-b border-border pb-4 mb-4 flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-foreground flex items-center gap-3">
                    <span className="bg-accent rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">
                      1
                    </span>
                    Environment Configuration
                  </h2>
                </div>
                <div className="space-y-4">
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
                          <option key={p}>{p}</option>
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
                          <option key={f}>{f}</option>
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

              {/* Section 2: Source Upload */}
              <div className="bg-card border border-border rounded-lg p-6">
                <div className="border-b border-border pb-4 mb-4">
                  <h2 className="text-lg font-semibold text-foreground flex items-center gap-3">
                    <span className="bg-accent rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">
                      2
                    </span>
                    Source Upload
                  </h2>
                  <p className="text-[13px] text-muted-foreground mt-2">
                    Upload your Verilog (.v, .sv) and constraint (.sdc) files.
                  </p>
                </div>
                <div
                  className={`border-2 border-dashed rounded-lg bg-surface-container-lowest p-8 flex flex-col items-center justify-center cursor-pointer transition-colors ${
                    isDragging ? 'border-primary bg-primary/5' : 'border-border hover:border-muted-foreground'
                  }`}
                  onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                  onDragLeave={() => setIsDragging(false)}
                  onDrop={(e) => { e.preventDefault(); setIsDragging(false); }}
                >
                  <span className="material-symbols-outlined text-4xl text-muted-foreground mb-4">upload_file</span>
                  <span className="text-sm text-foreground font-semibold">Drag & Drop files here</span>
                  <span className="text-[13px] text-muted-foreground mt-1">or click to browse</span>
                </div>
                {files.length > 0 && (
                  <div className="mt-4 space-y-2">
                    {files.map((f, i) => (
                      <div
                        key={f}
                        className="flex items-center justify-between p-2 bg-surface-container-lowest border border-border rounded"
                      >
                        <div className="flex items-center gap-2">
                          <span className="material-symbols-outlined text-primary text-sm">description</span>
                          <span className="font-mono text-xs text-foreground">{f}</span>
                          {i === 0 && (
                            <span className="text-[10px] font-bold uppercase text-emerald-500 bg-emerald-500/10 px-1.5 py-0.5 rounded">
                              Uploaded
                            </span>
                          )}
                        </div>
                        <button
                          className="text-muted-foreground hover:text-destructive transition-colors"
                          onClick={() => setFiles(files.filter((_, idx) => idx !== i))}
                        >
                          <span className="material-symbols-outlined text-[16px]">delete</span>
                        </button>
                      </div>
                    ))}
                  </div>
                )}
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
                    <span className="text-sm">Syntax check passed (alu_core.v)</span>
                  </li>
                  <li className="flex items-center text-foreground">
                    <span className="material-symbols-outlined text-emerald-500 mr-3 text-sm">check_circle</span>
                    <span className="text-sm">PDK availability confirmed ({pdk})</span>
                  </li>
                  <li className="flex items-center text-muted-foreground">
                    <span className="material-symbols-outlined mr-3 text-sm animate-pulse">pending</span>
                    <span className="text-sm">Validating constraints (.sdc)...</span>
                  </li>
                </ul>
              </div>
            </div>

            {/* Right Column: Inspector / Summary */}
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
                      TARGET
                    </div>
                    <div className="text-sm text-foreground">{pdk}</div>
                  </div>
                  <div>
                    <div className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground mb-1">
                      FLOW
                    </div>
                    <div className="text-sm text-foreground">{flow}</div>
                  </div>
                  <div className="border-t border-border pt-4">
                    <div className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground mb-3">
                      RESOURCE ESTIMATION
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between font-mono text-xs">
                        <span className="text-muted-foreground">Est. Gate Count:</span>
                        <span className="text-foreground">~120K</span>
                      </div>
                      <div className="flex justify-between font-mono text-xs">
                        <span className="text-muted-foreground">Est. Memory:</span>
                        <span className="text-foreground">32KB</span>
                      </div>
                      <div className="flex justify-between font-mono text-xs">
                        <span className="text-muted-foreground">Version:</span>
                        <span className="text-primary font-semibold">{version.toUpperCase()}</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="p-4 border-t border-border">
                  <Button
                    className="w-full bg-primary text-white hover:bg-primary/90 py-3 font-semibold"
                    onClick={handleSubmit}
                    disabled={submitJob.isPending}
                  >
                    <span className="material-symbols-outlined mr-2 text-sm">play_arrow</span>
                    Ready for RTL Analysis
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </AppShell>
  );
}
