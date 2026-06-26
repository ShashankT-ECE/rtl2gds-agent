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

// Agent icons mapped to stage names
const AGENT_ICONS: Record<string, string> = {
  spec_parser: '🤖',
  verification_planner: '🔍',
  rtl_gen: '⚙️',
  testbench: '🧪',
  testbench_re: '🧪',
  simulation: '💻',
  simulation_re: '💻',
  log_analysis: '🔧',
  fix: '🔧',
  synthesis: '🔲',
  sta: '⏱️',
  openlane: '🏗️',
  drc: '✅',
};

const STATUS_INDICATORS: Record<string, { ring: string; dot: string }> = {
  success: { ring: 'ring-emerald-500/20', dot: 'bg-emerald-500' },
  error: { ring: 'ring-red-500/20', dot: 'bg-red-500' },
  warning: { ring: 'ring-amber-500/20', dot: 'bg-amber-500' },
  info: { ring: 'ring-blue-500/20', dot: 'bg-blue-500' },
  debug: { ring: 'ring-slate-500/20', dot: 'bg-slate-500' },
};

export function AgentLogEntry({ event, isExpanded = false, onToggle }: AgentLogEntryProps) {
  const stageLabel = event.stage ? (STAGE_LABELS[event.stage] || event.stage) : 'SYS';
  const agentIcon = event.stage ? (AGENT_ICONS[event.stage] || '◇') : '◆';
  const indicators = STATUS_INDICATORS[event.severity] || STATUS_INDICATORS.info;

  return (
    <div
      className={cn(
        'group flex items-start gap-3 px-4 py-2 hover:bg-accent/50 cursor-pointer transition-all duration-200',
        'border-l-2 border-l-transparent hover:border-l-border',
        isExpanded && 'bg-accent/30 border-l-border',
        'animate-[fade-in_0.15s_ease-out]'
      )}
      onClick={onToggle}
    >
      {/* Agent icon */}
      <div
        className={cn(
          'relative flex items-center justify-center w-7 h-7 rounded-full shrink-0 mt-0.5 transition-all duration-300',
          'ring-2',
          indicators.ring,
          event.severity === 'success' ? 'bg-emerald-500/10' :
          event.severity === 'error' ? 'bg-red-500/10' :
          event.severity === 'warning' ? 'bg-amber-500/10' :
          'bg-blue-500/10'
        )}
      >
        <span className="text-xs leading-none">{agentIcon}</span>
        {/* Status dot */}
        <span
          className={cn(
            'absolute -bottom-0.5 -right-0.5 h-2 w-2 rounded-full border-2 border-[#0a0a0b]',
            indicators.dot
          )}
        />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          {/* Timestamp */}
          <span className="text-xs font-mono text-muted-foreground shrink-0">
            {formatEventTimestamp(event.timestamp)}
          </span>

          {/* Stage badge */}
          <span className="text-[10px] font-mono text-muted-foreground bg-accent px-1.5 py-0.5 rounded shrink-0">
            {stageLabel}
          </span>

          {/* Severity */}
          <SeverityBadge severity={event.severity} className="shrink-0" />
        </div>

        {/* Message */}
        <p className="text-sm text-foreground/80 mt-0.5 leading-relaxed">
          {event.message}
        </p>

        {/* Meta tags */}
        <div className="flex items-center gap-2 mt-1">
          {event.iteration != null && event.iteration > 0 && (
            <span className="text-[10px] font-mono text-primary bg-primary/10 px-1.5 py-0.5 rounded">
              iter {event.iteration}
            </span>
          )}
          {Object.keys(event.payload).length > 0 && (
            <span className="text-[10px] text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
              payload
              {isExpanded ? ' ▲' : ' ▼'}
            </span>
          )}
        </div>

        {/* Expanded payload */}
        {isExpanded && Object.keys(event.payload).length > 0 && (
          <div className="mt-2 p-3 rounded bg-surface-container-lowest border border-border animate-[fade-in_0.15s_ease-out]">
            <pre className="text-xs font-mono text-muted-foreground overflow-x-auto whitespace-pre-wrap">
              {JSON.stringify(event.payload, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
