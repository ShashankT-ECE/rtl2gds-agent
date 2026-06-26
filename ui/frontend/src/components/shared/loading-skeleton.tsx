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
          'rounded-lg bg-card border border-border p-4 animate-pulse',
          className
        )}
      >
        <div className="h-4 w-3/4 bg-muted rounded mb-3" />
        <div className="h-3 w-full bg-muted rounded mb-2" />
        <div className="h-3 w-5/6 bg-muted rounded" />
      </div>
    );
  }

  if (variant === 'rect') {
    return (
      <div
        className={cn(
          'animate-pulse bg-accent rounded-lg border border-border',
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
          className="h-3 bg-muted rounded"
          style={{ width: `${85 - i * 10}%` }}
        />
      ))}
    </div>
  );
}
