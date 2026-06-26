'use client';

import { cn } from '@/lib/utils';
import type { Severity } from '@/lib/types';
import { SEVERITY_COLORS } from '@/lib/constants';

interface SeverityBadgeProps {
  severity: Severity;
  className?: string;
}

const SEVERITY_LABELS: Record<Severity, string> = {
  debug: 'DEBUG',
  info: 'INFO',
  success: 'SUCCESS',
  warning: 'WARN',
  error: 'ERROR',
};

const SEVERITY_BG: Record<Severity, string> = {
  debug: 'bg-muted text-muted-foreground',
  info: 'bg-muted text-foreground',
  success: 'bg-emerald-500/10 text-emerald-500',
  warning: 'bg-yellow-400/10 text-yellow-400',
  error: 'bg-destructive/10 text-destructive',
};

export function SeverityBadge({ severity, className }: SeverityBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded px-1.5 py-0.5 text-2xs font-semibold uppercase tracking-wider',
        SEVERITY_BG[severity],
        className
      )}
    >
      {SEVERITY_LABELS[severity]}
    </span>
  );
}
