'use client';

import { useRef, useEffect, useState, useCallback } from 'react';
import { Copy, Pause, Play, Trash2, ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface LogLine {
  timestamp: string;
  level: 'DEBUG' | 'INFO' | 'SUCCESS' | 'WARNING' | 'ERROR';
  message: string;
  stage?: string;
}

interface LiveTerminalProps {
  lines: LogLine[];
  isLive?: boolean;
  className?: string;
}

const LEVEL_STYLES: Record<LogLine['level'], string> = {
  DEBUG: 'text-slate-500',
  INFO: 'text-blue-400',
  SUCCESS: 'text-emerald-400',
  WARNING: 'text-amber-400',
  ERROR: 'text-red-400',
};

const LEVEL_BADGES: Record<LogLine['level'], string> = {
  DEBUG: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  INFO: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  SUCCESS: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  WARNING: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  ERROR: 'bg-red-500/10 text-red-400 border-red-500/20',
};

export function LiveTerminal({ lines, isLive = false, className }: LiveTerminalProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const [isAtBottom, setIsAtBottom] = useState(true);
  const [paused, setPaused] = useState(false);
  const [copied, setCopied] = useState(false);

  // Auto-scroll
  useEffect(() => {
    if (!paused && isAtBottom && bottomRef.current && lines.length > 0) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [lines, isAtBottom, paused]);

  const handleScroll = useCallback(() => {
    if (!containerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    setIsAtBottom(scrollHeight - scrollTop - clientHeight < 40);
  }, []);

  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    setIsAtBottom(true);
  }, []);

  const clearTerminal = useCallback(() => {
    // In a real terminal this would clear the buffer
    // For now it scrolls to top
    containerRef.current?.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  const copyAll = useCallback(() => {
    const text = lines
      .map((l) => `${l.timestamp} ${l.level.padEnd(7)} ${l.message}`)
      .join('\n');
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [lines]);

  return (
    <div className={cn('rounded-lg border border-border bg-card flex flex-col overflow-hidden', className)}>
      {/* Terminal header — mimics a real terminal window */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-surface-container-highest shrink-0">
        {/* Left: window buttons (decorative) */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-full bg-red-500/60" />
            <span className="h-3 w-3 rounded-full bg-amber-500/60" />
            <span className="h-3 w-3 rounded-full bg-emerald-500/60" />
          </div>
          <span className="text-xs font-mono text-muted-foreground ml-2">rtl2gds — bash — 80×24</span>
        </div>

        {/* Right: actions */}
        <div className="flex items-center gap-1">
          <span className="text-2xs font-mono text-muted-foreground mr-2">
            {lines.length} lines
            {isLive && (
              <span className="ml-1 text-emerald-500 animate-pulse">●</span>
            )}
          </span>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0"
            onClick={() => setPaused(!paused)}
            title={paused ? 'Resume scrolling' : 'Pause scrolling'}
          >
            {paused ? <Play className="h-3 w-3" /> : <Pause className="h-3 w-3" />}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0"
            onClick={copyAll}
            title={copied ? 'Copied!' : 'Copy all'}
          >
            <Copy className="h-3 w-3" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0"
            onClick={clearTerminal}
            title="Clear terminal"
          >
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>
      </div>

      {/* Terminal output */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto font-mono text-sm leading-relaxed bg-[#0a0a0b] p-4 max-h-[500px] terminal-scroll"
      >
        {lines.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground gap-3 py-12">
            <div className="relative">
              <span className="text-4xl opacity-30">▋</span>
              <span className="absolute inset-0 text-4xl opacity-10 animate-pulse">▋</span>
            </div>
            <div className="text-center space-y-1">
              <p className="text-xs font-semibold uppercase tracking-wider">Terminal Ready</p>
              <p className="text-2xs">
                {isLive ? 'Waiting for pipeline events...' : 'Start a pipeline to see execution logs'}
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-0.5">
            {lines.map((line, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 group hover:bg-white/[0.02] px-1 py-0.5 rounded transition-colors"
              >
                {/* Timestamp */}
                <span className="text-xs text-slate-600 shrink-0 select-none">
                  {line.timestamp}
                </span>

                {/* Level badge */}
                <span
                  className={cn(
                    'text-[10px] font-bold uppercase px-1.5 py-0.5 rounded border shrink-0 select-none',
                    LEVEL_BADGES[line.level]
                  )}
                >
                  {line.level}
                </span>

                {/* Stage (if present) */}
                {line.stage && (
                  <span className="text-[10px] text-slate-600 shrink-0 bg-slate-800/30 px-1 py-0.5 rounded font-mono">
                    {line.stage}
                  </span>
                )}

                {/* Message */}
                <span className={cn('flex-1', LEVEL_STYLES[line.level])}>
                  {line.message}
                </span>

                {/* Copy line button */}
                <button
                  className="opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                  onClick={() => {
                    navigator.clipboard.writeText(
                      `${line.timestamp} ${line.level} ${line.message}`
                    );
                  }}
                  title="Copy line"
                >
                  <Copy className="h-3 w-3 text-slate-600 hover:text-slate-400" />
                </button>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Terminal status bar */}
      <div className="flex items-center justify-between px-4 py-1.5 border-t border-border bg-surface-container-lowest shrink-0">
        <div className="flex items-center gap-4 text-2xs font-mono text-muted-foreground">
          <span className={cn(isLive ? 'text-emerald-500' : 'text-slate-600')}>
            {isLive ? '● STREAMING' : paused ? '⏸ PAUSED' : '● IDLE'}
          </span>
          <span>utf-8</span>
          <span>bash</span>
        </div>
        <div className="flex items-center gap-3 text-2xs font-mono text-muted-foreground">
          <span>Ln {lines.length}, Col 80</span>
          {!isAtBottom && lines.length > 0 && (
            <button
              onClick={scrollToBottom}
              className="text-primary hover:text-primary/80 transition-colors flex items-center gap-1"
            >
              <ChevronDown className="h-3 w-3" />
              Jump to bottom
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// Helper to create LogLine from raw data
export function createLogLine(
  timestamp: string,
  level: LogLine['level'],
  message: string,
  stage?: string
): LogLine {
  return { timestamp, level, message, stage };
}

export type { LogLine };
