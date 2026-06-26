'use client';

import { cn } from '@/lib/utils';
import { Check, X, Circle, Clock, AlertTriangle, ChevronRight } from 'lucide-react';

interface TimelineEvent {
  time: string;
  event: string;
  detail: string;
  stage: string;
  status: 'completed' | 'running' | 'failed';
}

interface ExecutionTimelineProps {
  events: TimelineEvent[];
  className?: string;
  onEventClick?: (event: TimelineEvent) => void;
}

const statusIcons = {
  completed: <Check className="h-3.5 w-3.5 text-emerald-500" />,
  running: <Circle className="h-3.5 w-3.5 text-blue-500 animate-pulse fill-blue-500" />,
  failed: <X className="h-3.5 w-3.5 text-red-500" />,
};

const statusConnectorColors = {
  completed: 'bg-emerald-500/50',
  running: 'bg-blue-500/50 animate-pulse',
  failed: 'bg-red-500/50',
};

export function ExecutionTimeline({ events, className, onEventClick }: ExecutionTimelineProps) {
  if (events.length === 0) {
    return (
      <div className={cn('rounded-lg border border-border bg-card p-6', className)}>
        <div className="flex flex-col items-center justify-center text-muted-foreground gap-2 py-6">
          <Clock className="h-8 w-8 opacity-20" />
          <p className="text-xs font-semibold uppercase tracking-wider">Timeline Empty</p>
          <p className="text-2xs">Run a pipeline to populate the execution timeline</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('rounded-lg border border-border bg-card overflow-hidden', className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-border bg-surface-container-highest">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[16px] text-muted-foreground">timeline</span>
          <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">
            Execution Timeline
          </h3>
          <span className="text-xs font-mono text-muted-foreground">
            {events.length} events
          </span>
        </div>
        <div className="flex items-center gap-3 text-2xs">
          <span className="flex items-center gap-1 text-emerald-500">
            <Check className="h-3 w-3" /> Complete
          </span>
          <span className="flex items-center gap-1 text-blue-400">
            <Circle className="h-3 w-3 fill-blue-500" /> Active
          </span>
          <span className="flex items-center gap-1 text-red-500">
            <X className="h-3 w-3" /> Failed
          </span>
        </div>
      </div>

      {/* Timeline */}
      <div className="p-4">
        <div className="relative">
          {events.map((event, idx) => (
            <div key={idx} className="relative flex gap-4 pb-2">
              {/* Timeline track */}
              <div className="flex flex-col items-center shrink-0">
                {/* Node */}
                <div
                  className={cn(
                    'relative z-10 flex items-center justify-center w-7 h-7 rounded-full border-2 transition-all duration-300',
                    event.status === 'completed' ? 'border-emerald-500/50 bg-emerald-500/10' :
                    event.status === 'running' ? 'border-blue-500/50 bg-blue-500/10 shadow-[0_0_8px_rgba(59,130,246,0.3)]' :
                    'border-red-500/50 bg-red-500/10'
                  )}
                >
                  {statusIcons[event.status]}
                </div>
                {/* Connector line */}
                {idx < events.length - 1 && (
                  <div
                    className={cn(
                      'w-0.5 flex-1 min-h-[16px]',
                      events[idx + 1].status === 'running' ? 'bg-gradient-to-b from-current to-blue-500/30' :
                      statusConnectorColors[events[idx + 1].status]
                    )}
                  />
                )}
              </div>

              {/* Content */}
              <div
                className={cn(
                  'flex-1 min-w-0 pb-4 last:pb-0',
                  onEventClick && 'cursor-pointer hover:bg-accent/30 rounded px-2 -mx-2 py-1 -my-1 transition-colors'
                )}
                onClick={() => onEventClick?.(event)}
              >
                {/* Time */}
                <span className="text-xs font-mono text-muted-foreground tabular-nums">
                  {event.time}
                </span>

                {/* Event */}
                <div className="flex items-center gap-2 mt-0.5">
                  <p className={cn(
                    'text-sm font-medium',
                    event.status === 'running' ? 'text-blue-400' :
                    event.status === 'failed' ? 'text-red-400' :
                    'text-foreground'
                  )}>
                    {event.event}
                  </p>
                  {event.status === 'running' && (
                    <span className="flex gap-0.5">
                      <span className="h-1 w-1 rounded-full bg-blue-400 animate-pulse" />
                      <span className="h-1 w-1 rounded-full bg-blue-400 animate-pulse" style={{ animationDelay: '0.1s' }} />
                      <span className="h-1 w-1 rounded-full bg-blue-400 animate-pulse" style={{ animationDelay: '0.2s' }} />
                    </span>
                  )}
                </div>

                {/* Detail */}
                <p className="text-xs text-muted-foreground mt-0.5">{event.detail}</p>

                {/* Stage tag */}
                <span className="inline-block mt-1 text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-700/30 text-slate-400 border border-slate-700/50">
                  {event.stage}
                </span>

                {/* Interactive hint */}
                {onEventClick && (
                  <div className="flex items-center gap-1 mt-1 text-2xs text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">
                    <ChevronRight className="h-3 w-3" />
                    Click for details
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
