'use client';

import { XCircle, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = 'Something went wrong',
  message,
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-16 px-4 text-center',
        className
      )}
    >
      <div className="mb-4 rounded-full bg-etch-red/10 p-4">
        <XCircle className="h-10 w-10 text-etch-red" />
      </div>
      <h3 className="text-lg font-semibold text-silicon-200">{title}</h3>
      <p className="mt-2 max-w-md text-sm text-silicon-400">{message}</p>
      {onRetry && (
        <Button
          variant="outline"
          className="mt-6 border-silicon-600 text-silicon-300 hover:bg-silicon-800"
          onClick={onRetry}
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          Retry
        </Button>
      )}
    </div>
  );
}
