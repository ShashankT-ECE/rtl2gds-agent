'use client';

import { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { formatDuration } from '@/lib/formatters';

interface ElapsedTimerProps {
  startedAt: string | null | undefined;
  isRunning?: boolean;
  className?: string;
}

export function ElapsedTimer({ startedAt, isRunning = false, className }: ElapsedTimerProps) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!startedAt) {
      setElapsed(0);
      return;
    }

    const start = new Date(startedAt).getTime();

    const update = () => {
      setElapsed((Date.now() - start) / 1000);
    };

    update();

    if (isRunning) {
      const interval = setInterval(update, 250);
      return () => clearInterval(interval);
    }
  }, [startedAt, isRunning]);

  return (
    <span className={cn('font-mono text-sm tabular-nums', className)}>
      {formatDuration(elapsed)}
    </span>
  );
}
