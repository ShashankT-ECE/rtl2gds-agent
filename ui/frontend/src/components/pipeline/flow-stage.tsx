'use client';

import { Check, X, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { STAGE_LABELS } from '@/lib/constants';
import type { StageStatus } from '@/lib/types';

interface FlowStageProps {
  name: string;
  label?: string;
  status: StageStatus;
  isInFixLoop?: boolean;
  stageNumber: number;
}

const statusIcon = (status: StageStatus) => {
  switch (status) {
    case 'completed':
      return <Check className="h-3.5 w-3.5 text-photo-green" />;
    case 'failed':
      return <X className="h-3.5 w-3.5 text-etch-red" />;
    case 'running':
      return <Loader2 className="h-3.5 w-3.5 text-copper-500 animate-spin" />;
    default:
      return null;
  }
};

const statusStyles: Record<StageStatus, string> = {
  pending: 'border-silicon-700 bg-transparent text-silicon-500',
  running: 'border-copper-500 bg-copper-500/10 text-copper-500 shadow-[0_0_12px_rgba(240,152,55,0.15)]',
  completed: 'border-photo-green bg-photo-green/10 text-photo-green',
  failed: 'border-etch-red bg-etch-red/10 text-etch-red',
  skipped: 'border-silicon-700 border-dashed bg-transparent text-silicon-600',
};

export function FlowStage({ name, label, status, isInFixLoop = false, stageNumber }: FlowStageProps) {
  const displayLabel = label || STAGE_LABELS[name] || name;

  return (
    <div
      className={cn(
        'flex flex-col items-center gap-1.5 min-w-[80px]',
        isInFixLoop && 'opacity-90'
      )}
    >
      {/* Stage box */}
      <div
        className={cn(
          'relative flex items-center justify-center w-14 h-14 rounded-lg border-2 transition-all duration-300',
          statusStyles[status],
          status === 'running' && 'animate-[pulse-copper_2s_ease-in-out_infinite]',
          status === 'failed' && 'animate-[shake_0.4s_ease-in-out]'
        )}
        title={`${displayLabel} — ${status}`}
      >
        {statusIcon(status)}
        {status === 'pending' && (
          <span className="text-xs font-mono text-silicon-600">{stageNumber}</span>
        )}
      </div>
      {/* Label */}
      <span
        className={cn(
          'text-xs text-center leading-tight max-w-[80px] transition-colors duration-300',
          status === 'running' ? 'text-copper-500 font-medium' : 'text-silicon-400',
          status === 'completed' && 'text-silicon-300',
          status === 'failed' && 'text-etch-red'
        )}
      >
        {displayLabel}
      </span>
      {/* Fix loop indicator */}
      {isInFixLoop && (
        <span className="text-2xs text-silicon-600 font-mono">↺ loop</span>
      )}
    </div>
  );
}
