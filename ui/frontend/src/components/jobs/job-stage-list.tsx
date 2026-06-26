'use client';

import { Check, X, Loader2, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';
import { STAGE_LABELS } from '@/lib/constants';
import { formatMs } from '@/lib/formatters';
import type { StageInfo, StageStatus } from '@/lib/types';

interface JobStageListProps {
  stages: StageInfo[];
}

function StageStatusIcon({ status }: { status: StageStatus }) {
  switch (status) {
    case 'completed': return <Check className="h-4 w-4 text-emerald-500" />;
    case 'failed': return <X className="h-4 w-4 text-destructive" />;
    case 'running': return <Loader2 className="h-4 w-4 text-primary animate-spin" />;
    case 'skipped': return <Minus className="h-4 w-4 text-muted-foreground" />;
    default: return <div className="h-4 w-4 rounded-full border border-border" />;
  }
}

const statusBg: Record<StageStatus, string> = {
  pending: 'bg-transparent',
  running: 'bg-primary/5',
  completed: 'bg-emerald-500/5',
  failed: 'bg-destructive/5',
  skipped: 'bg-transparent',
};

export function JobStageList({ stages }: JobStageListProps) {
  if (!stages || stages.length === 0) {
    return <p className="text-sm text-muted-foreground text-center py-8">No stage data available.</p>;
  }

  return (
    <div className="space-y-1">
      {stages.map((stage, idx) => (
        <div
          key={stage.name}
          className={cn(
            'flex items-center gap-3 px-4 py-2.5 rounded-md transition-colors',
            statusBg[stage.status]
          )}
        >
          <span className="text-xs text-muted-foreground font-mono w-6">{idx + 1}</span>
          <StageStatusIcon status={stage.status} />
          <span className={cn(
            'flex-1 text-sm',
            stage.status === 'completed' && 'text-foreground',
            stage.status === 'running' && 'text-primary font-medium',
            stage.status === 'failed' && 'text-destructive',
            stage.status === 'pending' && 'text-muted-foreground',
          )}>
            {STAGE_LABELS[stage.name] || stage.name}
          </span>
          {stage.elapsed_ms != null && (
            <span className="text-xs text-muted-foreground font-mono">{formatMs(stage.elapsed_ms)}</span>
          )}
        </div>
      ))}
    </div>
  );
}
