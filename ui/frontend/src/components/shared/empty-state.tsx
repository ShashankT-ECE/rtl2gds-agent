'use client';

import { type LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-16 px-4 text-center',
        className
      )}
    >
      {Icon && (
        <div className="mb-4 rounded-full bg-silicon-800 p-4">
          <Icon className="h-10 w-10 text-silicon-500" />
        </div>
      )}
      <h3 className="text-lg font-semibold text-silicon-200">{title}</h3>
      {description && (
        <p className="mt-2 max-w-md text-sm text-silicon-400">{description}</p>
      )}
      {action && (
        <Button
          variant="outline"
          className="mt-6 border-copper-500 text-copper-500 hover:bg-copper-500/10"
          onClick={action.onClick}
        >
          {action.label}
        </Button>
      )}
    </div>
  );
}
