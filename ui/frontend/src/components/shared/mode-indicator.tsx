'use client';

import { FlaskConical, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useSystemStatus } from '@/hooks/use-system-status';

interface ModeIndicatorProps {
  className?: string;
}

export function ModeIndicator({ className }: ModeIndicatorProps) {
  const { data: status } = useSystemStatus();
  const mode = status?.pipeline_mode || 'mock';
  const isMock = mode === 'mock';

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold',
        isMock
          ? 'bg-mask-yellow/15 text-mask-yellow'
          : 'bg-copper-500/15 text-copper-500',
        className
      )}
      title={isMock ? 'Simulated pipeline — no EDA tools running' : 'Live pipeline with EDA tools'}
    >
      {isMock ? (
        <FlaskConical className="h-3 w-3" />
      ) : (
        <Zap className="h-3 w-3" />
      )}
      {isMock ? 'MOCK' : 'REAL'}
    </div>
  );
}
