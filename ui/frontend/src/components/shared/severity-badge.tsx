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
  debug: 'bg-silicon-700/30 text-silicon-400',
  info: 'bg-silicon-700/30 text-silicon-200',
  success: 'bg-photo-green/10 text-photo-green',
  warning: 'bg-mask-yellow/10 text-mask-yellow',
  error: 'bg-etch-red/10 text-etch-red',
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
