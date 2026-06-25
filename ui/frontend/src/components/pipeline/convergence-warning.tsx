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
        'flex items-start gap-3 rounded-lg border border-mask-yellow/30 bg-mask-yellow/5 p-4',
        className
      )}
    >
      <AlertTriangle className="h-5 w-5 text-mask-yellow shrink-0 mt-0.5" />
      <div>
        <h4 className="text-sm font-semibold text-mask-yellow">Convergence Warning</h4>
        <p className="text-sm text-silicon-400 mt-1">{message}</p>
      </div>
    </div>
  );
}
