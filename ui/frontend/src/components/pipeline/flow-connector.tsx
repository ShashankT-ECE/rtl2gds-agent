'use client';

import { cn } from '@/lib/utils';
import type { StageStatus } from '@/lib/types';

interface FlowConnectorProps {
  sourceStatus: StageStatus;
  targetStatus: StageStatus;
  direction?: 'horizontal' | 'vertical';
  isLoopback?: boolean;
}

export function FlowConnector({
  sourceStatus,
  targetStatus,
  direction = 'horizontal',
  isLoopback = false,
}: FlowConnectorProps) {
  const isActive = sourceStatus === 'completed' || sourceStatus === 'running';
  const isFlow = isActive && (targetStatus === 'running' || targetStatus === 'pending');

  if (direction === 'vertical') {
    return (
      <div className="flex flex-col items-center py-1">
        <div
          className={cn(
            'w-0.5 h-6 relative overflow-hidden',
            isLoopback ? 'border-l-2 border-dashed border-silicon-600' : 'bg-silicon-700',
            isActive && !isLoopback && 'bg-copper-500/50'
          )}
        >
          {isFlow && !isLoopback && (
            <div className="absolute top-0 left-0 w-full h-2 bg-copper-500 rounded-full animate-[flow-particle_1.5s_ease-in-out_infinite]" />
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center px-0.5">
      {/* Arrow line */}
      <div
        className={cn(
          'relative w-8 h-0.5',
          isLoopback ? 'border-t-2 border-dashed border-silicon-600' : 'bg-silicon-700',
          isActive && !isLoopback && 'bg-copper-500/50'
        )}
      >
        {/* Arrow head */}
        <div
          className={cn(
            'absolute right-0 top-1/2 -translate-y-1/2 w-0 h-0',
            'border-t-[4px] border-t-transparent',
            'border-b-[4px] border-b-transparent',
            'border-l-[6px]',
            isActive && !isLoopback ? 'border-l-copper-500' : 'border-l-silicon-600'
          )}
        />
        {/* Data flow particles */}
        {isFlow && !isLoopback && (
          <>
            <div className="absolute top-0 left-0 w-1.5 h-1.5 rounded-full bg-copper-500 animate-[flow-particle_1.5s_ease-in-out_infinite]" />
            <div className="absolute top-0 left-0 w-1.5 h-1.5 rounded-full bg-copper-500 animate-[flow-particle_1.5s_ease-in-out_0.5s_infinite]" />
          </>
        )}
      </div>
    </div>
  );
}
