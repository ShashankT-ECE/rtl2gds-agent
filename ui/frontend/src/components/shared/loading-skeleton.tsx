'use client';

import { cn } from '@/lib/utils';

interface LoadingSkeletonProps {
  className?: string;
  lines?: number;
  variant?: 'text' | 'card' | 'rect';
}

export function LoadingSkeleton({ className, lines = 3, variant = 'text' }: LoadingSkeletonProps) {
  if (variant === 'card') {
    return (
      <div
        className={cn(
          'rounded-lg bg-silicon-850 border border-silicon-700 p-4 animate-pulse',
          className
        )}
      >
        <div className="h-4 w-3/4 bg-silicon-700 rounded mb-3" />
        <div className="h-3 w-full bg-silicon-700 rounded mb-2" />
        <div className="h-3 w-5/6 bg-silicon-700 rounded" />
      </div>
    );
  }

  if (variant === 'rect') {
    return (
      <div
        className={cn(
          'animate-pulse bg-silicon-800 rounded-lg border border-silicon-700',
          className
        )}
      />
    );
  }

  return (
    <div className={cn('space-y-2 animate-pulse', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-3 bg-silicon-700 rounded"
          style={{ width: `${85 - i * 10}%` }}
        />
      ))}
    </div>
  );
}
