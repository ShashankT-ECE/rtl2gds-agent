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
    <div className="rounded-lg border border-silicon-700 bg-silicon-850 p-4">
      <h3 className="text-sm font-semibold text-silicon-200 mb-3">Pipeline Versions</h3>
      <div className="space-y-2">
        {versionInfo.map((v) => (
          <div key={v.label} className="flex items-center gap-3">
            {v.available ? (
              <Check className="h-4 w-4 text-photo-green" />
            ) : (
              <X className="h-4 w-4 text-silicon-600" />
            )}
            <span className={cn('text-sm', v.available ? 'text-silicon-300' : 'text-silicon-600')}>
              {v.label}
            </span>
          </div>
        ))}
      </div>
      {data?.pipeline_mode === 'mock' && (
        <div className="mt-3 pt-3 border-t border-silicon-700">
          <p className="text-xs text-mask-yellow">
            ⚠ Running in mock mode — pipeline stages are simulated. Set PIPELINE_MODE=real for live EDA tool execution.
          </p>
        </div>
      )}
    </div>
  );
}
