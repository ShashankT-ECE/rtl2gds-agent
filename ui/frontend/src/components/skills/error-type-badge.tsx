'use client';

import { cn } from '@/lib/utils';
import { ERROR_TYPE_COLORS } from '@/lib/constants';

interface ErrorTypeBadgeProps {
  errorType: string;
  className?: string;
}

export function ErrorTypeBadge({ errorType, className }: ErrorTypeBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded px-2 py-0.5 text-2xs font-semibold',
        className
      )}
      style={{
        backgroundColor: `${ERROR_TYPE_COLORS[errorType] || ERROR_TYPE_COLORS.UNKNOWN}15`,
        color: ERROR_TYPE_COLORS[errorType] || ERROR_TYPE_COLORS.UNKNOWN,
        border: `1px solid ${ERROR_TYPE_COLORS[errorType] || ERROR_TYPE_COLORS.UNKNOWN}30`,
      }}
    >
      {errorType}
    </span>
  );
}
