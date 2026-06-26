'use client';

import { cn } from '@/lib/utils';
import { formatEventTimestamp, formatMs } from '@/lib/formatters';
import { SEVERITY_COLORS } from '@/lib/constants';
import type { PipelineEvent, StageInfo } from '@/lib/types';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface JobTimelineProps {
  events: PipelineEvent[];
  stages: StageInfo[];
  totalDurationMs: number;
}

export function JobTimeline({ events, stages, totalDurationMs }: JobTimelineProps) {
  if (events.length === 0) {
    return (
      <div className="text-sm text-muted-foreground text-center py-12">
        No events recorded for this job.
      </div>
    );
  }

  const firstTime = new Date(events[0].timestamp).getTime();
  const lastTime = new Date(events[events.length - 1].timestamp).getTime();
  const totalMs = lastTime - firstTime || 1;

  return (
    <TooltipProvider>
      <div className="space-y-2">
        {/* Stage bars */}
        <div className="flex h-8 rounded-lg overflow-hidden bg-card border border-border">
          {stages.map((stage) => {
            if (!stage.started_at) return null;
            const startMs = new Date(stage.started_at).getTime() - firstTime;
            const durationMs = stage.elapsed_ms || (stage.completed_at
              ? new Date(stage.completed_at).getTime() - new Date(stage.started_at).getTime()
              : 0);
            const widthPct = Math.max(1, (durationMs / totalMs) * 100);
            const leftPct = (startMs / totalMs) * 100;

            const color =
              stage.status === 'completed' ? '#2ea86c' :
              stage.status === 'failed' ? '#e05045' :
              stage.status === 'running' ? '#f09837' : '#374055';

            return (
              <Tooltip key={stage.name}>
                <TooltipTrigger>
                  <div
                    className="h-full transition-all cursor-pointer hover:brightness-125"
                    style={{
                      width: `${widthPct}%`,
                      backgroundColor: color,
                      marginLeft: leftPct > 0 ? `${leftPct - (stage === stages[0] ? 0 : 0)}%` : 0,
                    }}
                  />
                </TooltipTrigger>
                <TooltipContent className="bg-accent border-border text-xs">
                  <p className="font-semibold">{stage.name}</p>
                  <p className="text-muted-foreground">{stage.status} — {formatMs(stage.elapsed_ms)}</p>
                </TooltipContent>
              </Tooltip>
            );
          })}
        </div>

        {/* Event markers */}
        <div className="relative h-6">
          {events.filter(e => !['heartbeat'].includes(e.event_type)).slice(0, 50).map((event) => {
            const eventMs = new Date(event.timestamp).getTime() - firstTime;
            const leftPct = (eventMs / totalMs) * 100;

            return (
              <Tooltip key={event.event_id}>
                <TooltipTrigger>
                  <div
                    className="absolute top-1/2 -translate-y-1/2 h-2 w-2 rounded-full cursor-pointer hover:scale-150 transition-transform"
                    style={{
                      left: `${leftPct}%`,
                      backgroundColor: SEVERITY_COLORS[event.severity] || '#6b7a94',
                    }}
                  />
                </TooltipTrigger>
                <TooltipContent className="bg-accent border-border max-w-xs">
                  <p className="text-xs text-muted-foreground">{formatEventTimestamp(event.timestamp)}</p>
                  <p className="text-sm">{event.message}</p>
                </TooltipContent>
              </Tooltip>
            );
          })}
        </div>

        {/* Time labels */}
        <div className="flex justify-between text-2xs text-muted-foreground font-mono">
          <span>{formatEventTimestamp(events[0].timestamp)}</span>
          <span>{formatEventTimestamp(events[events.length - 1].timestamp)}</span>
        </div>
      </div>
    </TooltipProvider>
  );
}
