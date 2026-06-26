'use client';

import { useState } from 'react';
import { Play, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { useBenchmarks } from '@/hooks/use-benchmarks';
import { useSubmitJob } from '@/hooks/use-job-list';
import { useJobStore } from '@/stores/job-store';
import { useUIStore } from '@/stores/ui-store';
import { VERSION_INFO } from '@/lib/constants';
import type { PipelineVersion, RunRequest } from '@/lib/types';
import { cn } from '@/lib/utils';

export function JobRunner() {
  const { data: benchmarkData } = useBenchmarks();
  const submitJob = useSubmitJob();
  const isRunning = useJobStore((s) => {
    const job = s.activeJobId ? s.jobs[s.activeJobId] : null;
    return job?.status === 'running' || job?.status === 'queued';
  });
  const selectedBenchmark = useUIStore((s) => s.selectedBenchmark);
  const setSelectedBenchmark = useUIStore((s) => s.setSelectedBenchmark);
  const selectedVersion = useUIStore((s) => s.selectedVersion);
  const setSelectedVersion = useUIStore((s) => s.setSelectedVersion);
  const setActiveJob = useJobStore((s) => s.setActiveJob);

  const [maxIterations, setMaxIterations] = useState(5);
  const [useRefRTL, setUseRefRTL] = useState(false);
  const [useRefTB, setUseRefTB] = useState(false);

  const benchmarks = benchmarkData?.benchmarks || [];
  const versions: PipelineVersion[] = ['v3', 'v2', 'v1'];

  const handleSubmit = async () => {
    if (!selectedBenchmark) return;

    const request: RunRequest = {
      benchmark: selectedBenchmark,
      pipeline_version: selectedVersion,
      max_iterations: maxIterations,
      use_reference_rtl: useRefRTL,
      use_reference_tb: useRefTB,
    };

    try {
      const result = await submitJob.mutateAsync(request);
      setActiveJob(result.job_id);
    } catch {
      // Error handled by TanStack Query
    }
  };

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex flex-wrap items-end gap-4">
        {/* Benchmark selector */}
        <div className="flex-1 min-w-[200px]">
          <Label className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground mb-1.5 block">
            Benchmark
          </Label>
          <Select
            value={selectedBenchmark || ''}
            onValueChange={setSelectedBenchmark}
            disabled={isRunning}
          >
            <SelectTrigger className="bg-surface-container-lowest border-border text-foreground h-9">
              <SelectValue placeholder="Select benchmark..." />
            </SelectTrigger>
            <SelectContent className="bg-card border-border">
              <div className="text-xs text-muted-foreground px-2 py-1 font-semibold">Complete (GDSII Verified)</div>
              {benchmarks.filter(b => ['alu_8bit','sync_fifo_8x16','fsm_traffic_light','uart_tx','apb_slave'].includes(b.name)).map((b) => (
                <SelectItem key={b.name} value={b.name} className="text-foreground focus:bg-accent focus:text-foreground">
                  {b.name}
                </SelectItem>
              ))}
              <div className="text-xs text-muted-foreground px-2 py-1 font-semibold mt-1">In Progress</div>
              {benchmarks.filter(b => !['alu_8bit','sync_fifo_8x16','fsm_traffic_light','uart_tx','apb_slave'].includes(b.name)).map((b) => (
                <SelectItem key={b.name} value={b.name} className="text-foreground focus:bg-accent focus:text-foreground">
                  {b.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Version selector */}
        <div>
          <Label className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground mb-1.5 block">
            Version
          </Label>
          <div className="flex gap-1">
            {versions.map((v) => (
              <button
                key={v}
                onClick={() => setSelectedVersion(v)}
                disabled={isRunning}
                className={cn(
                  'px-3 py-1.5 text-xs font-semibold rounded border transition-all',
                  selectedVersion === v
                    ? 'bg-primary/10 text-primary border-primary/30'
                    : 'text-muted-foreground border-border hover:border-muted-foreground hover:text-foreground'
                )}
                title={VERSION_INFO[v].description}
              >
                {v.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Max iterations */}
        <div className="w-20">
          <Label className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground mb-1.5 block">
            Iterations
          </Label>
          <Input
            type="number"
            min={1}
            max={20}
            value={maxIterations}
            onChange={(e) => setMaxIterations(Number(e.target.value))}
            disabled={isRunning}
            className="bg-surface-container-lowest border-border text-foreground h-9 w-20 text-center font-mono"
          />
        </div>

        {/* Toggles */}
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Switch
              checked={useRefRTL}
              onCheckedChange={setUseRefRTL}
              disabled={isRunning}
            />
            <Label className="text-xs text-muted-foreground cursor-pointer" onClick={() => setUseRefRTL(!useRefRTL)}>
              Ref RTL
            </Label>
          </div>
          <div className="flex items-center gap-2">
            <Switch
              checked={useRefTB}
              onCheckedChange={setUseRefTB}
              disabled={isRunning}
            />
            <Label className="text-xs text-muted-foreground cursor-pointer" onClick={() => setUseRefTB(!useRefTB)}>
              Ref TB
            </Label>
          </div>
        </div>

        {/* Submit */}
        <Button
          onClick={handleSubmit}
          disabled={!selectedBenchmark || isRunning || submitJob.isPending}
          className="bg-primary text-white hover:bg-primary/90 font-semibold h-9 px-5"
        >
          {submitJob.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
          ) : (
            <span className="material-symbols-outlined text-[16px] mr-1">play_arrow</span>
          )}
          Run Pipeline
        </Button>
      </div>

      {submitJob.isError && (
        <p className="text-xs text-destructive mt-3">
          {(submitJob.error as Error)?.message || 'Failed to start job'}
        </p>
      )}
    </div>
  );
}
