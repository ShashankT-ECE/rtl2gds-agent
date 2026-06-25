'use client';

import { Activity, CheckCircle, XCircle } from 'lucide-react';
import { useHealth } from '@/hooks/use-system-status';
import { LoadingSkeleton } from '@/components/shared/loading-skeleton';
import { cn } from '@/lib/utils';

export function SystemHealthPanel() {
  const { data, isLoading, isError } = useHealth();

  if (isLoading) return <LoadingSkeleton lines={3} />;

  const healthy = !isError && data?.status === 'ok';

  return (
    <div className={cn(
      'rounded-lg border p-4',
      healthy ? 'border-photo-green/30 bg-photo-green/5' : 'border-etch-red/30 bg-etch-red/5'
    )}>
      <div className="flex items-center gap-3">
        {healthy ? (
          <CheckCircle className="h-8 w-8 text-photo-green" />
        ) : (
          <XCircle className="h-8 w-8 text-etch-red" />
        )}
        <div>
          <h3 className="text-lg font-semibold text-silicon-100">
            {healthy ? 'System Operational' : 'System Degraded'}
          </h3>
          <p className="text-sm text-silicon-400">
            {healthy
              ? `API v${data?.api_version || '1'} — Version ${data?.version || 'unknown'}`
              : 'Backend is unreachable'}
          </p>
        </div>
      </div>
    </div>
  );
}
