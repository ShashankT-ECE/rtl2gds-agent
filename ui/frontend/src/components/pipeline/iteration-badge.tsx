'use client';

import { RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';

interface IterationBadgeProps {
  iteration: number;
  maxIterations: number;
  className?: string;
}

export function IterationBadge({ iteration, maxIterations, className }: IterationBadgeProps) {
  if (iteration === 0) return null;

  const isWarning = iteration >= maxIterations - 1;

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-mono font-semibold',
        isWarning
          ? 'bg-mask-yellow/15 text-mask-yellow border border-mask-yellow/30'
          : 'bg-copper-500/10 text-copper-500 border border-copper-500/30',
        className
      )}
    >
      <RefreshCw className={cn('h-3 w-3', iteration > 0 && 'animate-spin')} />
      Fix Loop: {iteration}/{maxIterations}
    </div>
  );
}
