'use client';

import { AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ConvergenceWarningProps {
  message?: string;
  className?: string;
}

export function ConvergenceWarning({
  message = 'Convergence warning: identical errors detected. The fix loop may be stuck.',
  className,
}: ConvergenceWarningProps) {
  return (
    <div
      className={cn(
        'flex items-start gap-3 rounded-lg border border-yellow-400/30 bg-yellow-400/5 p-4',
        className
      )}
    >
      <AlertTriangle className="h-5 w-5 text-yellow-400 shrink-0 mt-0.5" />
      <div>
        <h4 className="text-sm font-semibold text-yellow-400">Convergence Warning</h4>
        <p className="text-sm text-muted-foreground mt-1">{message}</p>
      </div>
    </div>
  );
}
