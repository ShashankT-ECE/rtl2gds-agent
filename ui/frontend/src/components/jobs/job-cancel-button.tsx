'use client';

import { Square, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useCancelJob } from '@/hooks/use-job-list';

interface JobCancelButtonProps {
  jobId: string;
  isRunning: boolean;
}

export function JobCancelButton({ jobId, isRunning }: JobCancelButtonProps) {
  const cancelJob = useCancelJob();

  if (!isRunning) return null;

  return (
    <Button
      variant="outline"
      size="sm"
      className="border-destructive/30 text-destructive hover:bg-destructive/10 hover:text-destructive"
      onClick={() => cancelJob.mutate(jobId)}
      disabled={cancelJob.isPending}
    >
      {cancelJob.isPending ? (
        <Loader2 className="h-4 w-4 animate-spin mr-2" />
      ) : (
        <Square className="h-4 w-4 mr-2" />
      )}
      Cancel Job
    </Button>
  );
}
