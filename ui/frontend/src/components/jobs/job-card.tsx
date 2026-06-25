'use client';

import Link from 'next/link';
import { Check, X, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';
import { JOB_STATUS_COLORS, JOB_STATUS_LABELS } from '@/lib/constants';
import { formatDuration, formatRelativeTime } from '@/lib/formatters';
import type { RunResponse } from '@/lib/types';
import { Badge } from '@/components/ui/badge';

interface JobCardProps {
  job: RunResponse;
}

function ResultIcon({ passed, label }: { passed: boolean | null | undefined; label: string }) {
  if (passed === null || passed === undefined) {
    return <span title={`${label}: not run`}><Minus className="h-3 w-3 text-silicon-600" /></span>;
  }
  return passed ? (
    <span title={`${label}: passed`}><Check className="h-3 w-3 text-photo-green" /></span>
  ) : (
    <span title={`${label}: failed`}><X className="h-3 w-3 text-etch-red" /></span>
  );
}

export function JobCard({ job }: JobCardProps) {
  const completedStages = job.stages.filter(s => s.status === 'completed' || s.status === 'failed').length;
  const totalStages = job.stages.length || 12;
  const stagePct = totalStages > 0 ? (completedStages / totalStages) * 100 : 0;
  const color = JOB_STATUS_COLORS[job.status] || '#6b7a94';

  return (
    <Link
      href={`/jobs/${job.job_id}`}
      className="block rounded-lg border border-silicon-700 bg-silicon-850 hover:border-silicon-600 hover:bg-silicon-800 transition-all p-4"
    >
      <div className="flex items-center gap-4">
        {/* Status icon */}
        <div
          className="h-8 w-8 rounded-full flex items-center justify-center shrink-0"
          style={{ backgroundColor: `${color}20` }}
        >
          <div className="h-3 w-3 rounded-full" style={{ backgroundColor: color }} />
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3">
            <span className="font-mono text-sm text-silicon-200">{job.job_id}</span>
            <span className="text-sm text-silicon-400">{job.benchmark}</span>
            <Badge variant="outline" className="text-xs border-silicon-600 text-silicon-400">
              {job.pipeline_version.toUpperCase()}
            </Badge>
            <Badge
              className="text-xs"
              style={{
                backgroundColor: `${color}15`,
                color,
                borderColor: `${color}30`,
              }}
            >
              {JOB_STATUS_LABELS[job.status] || job.status}
            </Badge>
          </div>

          <div className="flex items-center gap-4 mt-2">
            <span className="text-xs text-silicon-500">{formatRelativeTime(job.created_at)}</span>
            {job.elapsed_seconds != null && (
              <span className="text-xs text-silicon-500 font-mono">{formatDuration(job.elapsed_seconds)}</span>
            )}
          </div>
        </div>

        {/* Stage bar */}
        <div className="hidden md:block w-32">
          <div className="h-1.5 rounded-full bg-silicon-700 overflow-hidden">
            <div
              className="h-full rounded-full bg-copper-500 transition-all"
              style={{ width: `${stagePct}%` }}
            />
          </div>
          <div className="text-2xs text-silicon-600 font-mono mt-1 text-right">
            {completedStages}/{totalStages}
          </div>
        </div>

        {/* Results icons */}
        <div className="flex items-center gap-2">
          <ResultIcon passed={job.sim_passed} label="Sim" />
          <ResultIcon passed={job.timing_met} label="STA" />
          <ResultIcon passed={job.drc_passed} label="DRC" />
        </div>
      </div>
    </Link>
  );
}
