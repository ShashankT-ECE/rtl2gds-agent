'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { ArrowDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { AgentLogEntry } from './agent-log-entry';
import { EmptyState } from '@/components/shared/empty-state';
import { useEventHistory } from '@/hooks/use-event-history';
import { Radio } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AgentActivityFeedProps {
  jobId: string | null;
  isLive?: boolean;
  className?: string;
}

export function AgentActivityFeed({ jobId, isLive = false, className }: AgentActivityFeedProps) {
  const events = useEventHistory(jobId);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [isAtBottom, setIsAtBottom] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll when new events arrive and user is at bottom
  useEffect(() => {
    if (isAtBottom && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [events.length, isAtBottom]);

  const handleScroll = useCallback(() => {
    if (!containerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    setIsAtBottom(scrollHeight - scrollTop - clientHeight < 40);
  }, []);

  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  if (!jobId) {
    return (
      <div className={cn('rounded-lg border border-border bg-card', className)}>
        <div className="px-4 py-3 border-b border-border bg-surface-container-highest">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px] text-muted-foreground">terminal</span>
            <h3 className="text-sm font-semibold text-foreground">Live Execution Log</h3>
          </div>
        </div>
        <EmptyState
          icon={Radio}
          title="No active pipeline"
          description="Select a benchmark and click Run to begin. Agent events will appear here in real time."
        />
      </div>
    );
  }

  return (
    <div className={cn('rounded-lg border border-border bg-card flex flex-col', className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-surface-container-highest shrink-0">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[16px] text-muted-foreground">terminal</span>
          <h3 className="text-sm font-semibold text-foreground">Live Execution Log</h3>
          {isLive && (
            <span className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-emerald-500">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse-green" />
              LIVE
            </span>
          )}
        </div>
        <span className="text-xs text-muted-foreground font-mono">{events.length} events</span>
      </div>

      {/* Event list */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto max-h-[400px] terminal-scroll bg-black"
      >
        {events.length === 0 ? (
          <div className="py-12">
            <EmptyState
              icon={Radio}
              title="Waiting for events..."
              description="Events will appear as the pipeline executes."
            />
          </div>
        ) : (
          <div className="py-1">
            {events.map((event) => (
              <AgentLogEntry
                key={event.event_id}
                event={event}
                isExpanded={expandedId === event.event_id}
                onToggle={() =>
                  setExpandedId(expandedId === event.event_id ? null : event.event_id)
                }
              />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Scroll-to-bottom FAB */}
      {!isAtBottom && events.length > 0 && (
        <div className="relative">
          <Button
            variant="secondary"
            size="sm"
            className="absolute bottom-3 left-1/2 -translate-x-1/2 rounded-full shadow-lg border-border"
            onClick={scrollToBottom}
          >
            <ArrowDown className="h-3.5 w-3.5 mr-1" />
            New events
          </Button>
        </div>
      )}
    </div>
  );
}
