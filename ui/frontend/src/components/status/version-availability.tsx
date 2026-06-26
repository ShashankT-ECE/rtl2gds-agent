'use client';

import { Check, X } from 'lucide-react';
import { useSystemStatus } from '@/hooks/use-system-status';
import { LoadingSkeleton } from '@/components/shared/loading-skeleton';
import { cn } from '@/lib/utils';

export function VersionAvailability() {
  const { data, isLoading } = useSystemStatus();
  const versions = data?.versions;

  if (isLoading) return <LoadingSkeleton lines={3} />;

  const versionInfo = [
    { label: 'V1 — Simulation + Fix Loop', available: versions?.v1_available !== false },
    { label: 'V2 — Synthesis + STA', available: versions?.v2_available === true },
    { label: 'V3 — Physical Design + DRC', available: versions?.v3_available === true },
  ];

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <h3 className="text-sm font-semibold text-foreground mb-3">Pipeline Versions</h3>
      <div className="space-y-2">
        {versionInfo.map((v) => (
          <div key={v.label} className="flex items-center gap-3">
            {v.available ? (
              <Check className="h-4 w-4 text-emerald-500" />
            ) : (
              <X className="h-4 w-4 text-muted-foreground" />
            )}
            <span className={cn('text-sm', v.available ? 'text-foreground' : 'text-muted-foreground')}>
              {v.label}
            </span>
          </div>
        ))}
      </div>
      {data?.pipeline_mode === 'mock' && (
        <div className="mt-3 pt-3 border-t border-border">
          <p className="text-xs text-yellow-400">
            ⚠ Running in mock mode — pipeline stages are simulated. Set PIPELINE_MODE=real for live EDA tool execution.
          </p>
        </div>
      )}
    </div>
  );
}
