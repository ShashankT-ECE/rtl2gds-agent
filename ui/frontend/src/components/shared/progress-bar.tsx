'use client';

import { cn } from '@/lib/utils';

interface ProgressBarProps {
  value: number; // 0-100
  variant?: 'default' | 'success' | 'warning' | 'error';
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
  indeterminate?: boolean;
}

const variantStyles = {
  default: 'bg-copper-500',
  success: 'bg-photo-green',
  warning: 'bg-mask-yellow',
  error: 'bg-etch-red',
};

const sizeStyles = {
  sm: 'h-1',
  md: 'h-2',
  lg: 'h-3',
};

export function ProgressBar({
  value,
  variant = 'default',
  size = 'md',
  showLabel = false,
  className,
  indeterminate = false,
}: ProgressBarProps) {
  const pct = Math.min(100, Math.max(0, value));

  return (
    <div className={cn('flex items-center gap-3', className)}>
      <div
        className={cn(
          'flex-1 rounded-full bg-silicon-700 overflow-hidden',
          sizeStyles[size]
        )}
        role="progressbar"
        aria-valuenow={indeterminate ? undefined : pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${indeterminate ? 'In progress' : `${Math.round(pct)}% complete`}`}
      >
        <div
          className={cn(
            'h-full rounded-full transition-all duration-500 ease-out',
            variantStyles[variant],
            indeterminate && 'animate-[progress-indeterminate_2s_ease-in-out_infinite] w-1/3'
          )}
          style={indeterminate ? undefined : { width: `${pct}%` }}
        />
      </div>
      {showLabel && (
        <span className="font-mono text-xs text-silicon-400 tabular-nums min-w-[3.5rem] text-right">
          {indeterminate ? '--' : `${Math.round(pct)}%`}
        </span>
      )}
    </div>
  );
}
