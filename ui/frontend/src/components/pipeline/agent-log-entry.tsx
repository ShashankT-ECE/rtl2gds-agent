'use client';

import { cn } from '@/lib/utils';
import { SeverityBadge } from '@/components/shared/severity-badge';
import { formatEventTimestamp } from '@/lib/formatters';
import { STAGE_LABELS } from '@/lib/constants';
import type { PipelineEvent } from '@/lib/types';

interface AgentLogEntryProps {
  event: PipelineEvent;
  isExpanded?: boolean;
  onToggle?: () => void;
}

export function AgentLogEntry({ event, isExpanded = false, onToggle }: AgentLogEntryProps) {
  const stageLabel = event.stage ? (STAGE_LABELS[event.stage] || event.stage) : 'SYS';

  return (
    <div
      className={cn(
        'group flex items-start gap-3 px-4 py-1.5 hover:bg-silicon-800/50 cursor-pointer transition-colors border-l-2 border-transparent hover:border-silicon-700',
        isExpanded && 'bg-silicon-800/30 border-silicon-700'
      )}
      onClick={onToggle}
    >
      {/* Timestamp */}
      <span className="text-xs font-mono text-silicon-600 shrink-0 pt-0.5 w-[5.5rem]">
        {formatEventTimestamp(event.timestamp)}
      </span>

      {/* Stage badge */}
      <span className="text-xs font-mono text-silicon-500 bg-silicon-800 px-1.5 py-0.5 rounded shrink-0 min-w-[3rem] text-center">
        {stageLabel}
      </span>

      {/* Severity */}
      <SeverityBadge severity={event.severity} className="shrink-0" />

      {/* Message */}
      <span className="text-sm text-silicon-300 flex-1 truncate">
        {event.message}
      </span>

      {/* Iteration (if applicable) */}
      {event.iteration != null && event.iteration > 0 && (
        <span className="text-2xs font-mono text-copper-500 shrink-0 bg-copper-500/10 px-1.5 py-0.5 rounded">
          iter {event.iteration}
        </span>
      )}

      {/* Expand indicator */}
      {Object.keys(event.payload).length > 0 && (
        <span className="text-2xs text-silicon-600 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
          {isExpanded ? '▲' : '▼'}
        </span>
      )}
    </div>
  );
}
