'use client';

import { cn } from '@/lib/utils';
import { STAGE_LABELS } from '@/lib/constants';
import type { StageStatus } from '@/lib/types';

interface FlowStageProps {
  name: string;
  label?: string;
  status: StageStatus;
  isInFixLoop?: boolean;
  stageNumber: number;
  onClick?: (stageName: string) => void;
  elapsedMs?: number | null;
}

const statusIcon = (status: StageStatus) => {
  switch (status) {
    case 'completed':
      return (
        <span className="relative">
          <span className="material-symbols-outlined text-[14px] text-emerald-500">check</span>
          <span className="absolute inset-0 rounded-full bg-emerald-500/20 scale-150 animate-[pulse-green_2s_ease-in-out_infinite]" />
        </span>
      );
    case 'failed':
      return <span className="material-symbols-outlined text-[14px] text-destructive">close</span>;
    case 'running':
      return (
        <span className="relative">
          <span className="material-symbols-outlined text-[14px] text-primary animate-spin">progress_activity</span>
          <span className="absolute -inset-1 rounded-full bg-primary/10 animate-[pulse-blue_2s_ease-in-out_infinite]" />
        </span>
      );
    default:
      return null;
  }
};

const statusStyles: Record<StageStatus, string> = {
  pending: 'border-border bg-transparent text-muted-foreground',
  running: 'border-primary bg-[#1e293b] text-primary shadow-[0_0_12px_rgba(0,82,255,0.3)] scale-110',
  completed: 'border-emerald-500 bg-emerald-500/10 text-emerald-500',
  failed: 'border-destructive bg-destructive/10 text-destructive',
  skipped: 'border-border border-dashed bg-transparent text-muted-foreground/50',
};

const statusTooltip: Record<StageStatus, string> = {
  pending: 'Queued',
  running: 'Running...',
  completed: 'Completed',
  failed: 'Failed',
  skipped: 'Skipped',
};

export function FlowStage({ name, label, status, isInFixLoop = false, stageNumber, onClick, elapsedMs }: FlowStageProps) {
  const displayLabel = label || STAGE_LABELS[name] || name;

  return (
    <div
      className={cn(
        'flex flex-col items-center gap-1.5 min-w-[84px] group',
        isInFixLoop && 'opacity-90',
        onClick && 'cursor-pointer'
      )}
      onClick={() => onClick?.(name)}
    >
      {/* Stage circle */}
      <div
        className={cn(
          'relative flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all duration-500',
          statusStyles[status],
          status === 'running' && 'animate-pulse-border',
          status === 'failed' && 'animate-[shake_0.4s_ease-in-out]',
          onClick && 'hover:scale-125 hover:shadow-lg'
        )}
        title={`${displayLabel} — ${statusTooltip[status]}${elapsedMs ? ` (${(elapsedMs / 1000).toFixed(1)}s)` : ''}${onClick ? ' — Click for details' : ''}`}
      >
        {statusIcon(status)}
        {status === 'pending' && (
          <span className="text-xs font-mono text-muted-foreground group-hover:text-foreground transition-colors">{stageNumber}</span>
        )}

        {/* Hover glow effect */}
        {onClick && (
          <div className="absolute inset-0 rounded-full opacity-0 group-hover:opacity-100 bg-white/5 transition-opacity duration-300" />
        )}
      </div>

      {/* Label */}
      <span
        className={cn(
          'text-xs text-center leading-tight max-w-[84px] transition-all duration-300',
          status === 'running' ? 'text-primary font-semibold' : 'text-muted-foreground',
          status === 'completed' && 'text-foreground/80',
          status === 'failed' && 'text-destructive',
          onClick && 'group-hover:text-foreground'
        )}
      >
        {displayLabel}
      </span>

      {/* Fix loop indicator */}
      {isInFixLoop && (
        <span className="text-2xs text-muted-foreground font-mono">↺ loop</span>
      )}

      {/* Elapsed time indicator */}
      {elapsedMs && status === 'completed' && (
        <span className="text-2xs text-muted-foreground font-mono tabular-nums">
          {(elapsedMs / 1000).toFixed(1)}s
        </span>
      )}
    </div>
  );
}
