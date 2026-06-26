'use client';

import { cn } from '@/lib/utils';
import { CATEGORY_INFO } from '@/lib/constants';

interface CategoryBadgeProps {
  category: string | null;
  className?: string;
}

export function CategoryBadge({ category, className }: CategoryBadgeProps) {
  const info = category ? CATEGORY_INFO[category] : null;
  const label = info?.label || category || 'Unknown';

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-2xs font-semibold uppercase tracking-wider',
        'bg-accent text-muted-foreground border border-border',
        className
      )}
    >
      {label}
    </span>
  );
}
