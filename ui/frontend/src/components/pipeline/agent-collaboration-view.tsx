'use client';

import { useState } from 'react';
import { cn } from '@/lib/utils';
import type { DemoAgent } from '@/stores/demo-store';

interface AgentCollaborationViewProps {
  agents: DemoAgent[];
  className?: string;
}

function AgentCard({ agent }: { agent: DemoAgent }) {
  const [expanded, setExpanded] = useState(false);

  const statusColors = {
    idle: 'border-slate-600 bg-slate-500/5',
    active: 'border-blue-500/30 bg-blue-500/5 shadow-[0_0_12px_rgba(59,130,246,0.1)]',
    completed: 'border-emerald-500/30 bg-emerald-500/5',
    blocked: 'border-amber-500/30 bg-amber-500/5',
    error: 'border-red-500/30 bg-red-500/5',
  };

  const statusDots = {
    idle: 'bg-slate-500',
    active: 'bg-blue-500 animate-[pulse-blue_2s_ease-in-out_infinite]',
    completed: 'bg-emerald-500',
    blocked: 'bg-amber-500 animate-pulse',
    error: 'bg-red-500 animate-pulse',
  };

  const statusLabels = {
    idle: 'Standing by',
    active: 'Active',
    completed: 'Done',
    blocked: 'Blocked',
    error: 'Error',
  };

  return (
    <div
      className={cn(
        'rounded-lg border p-3 transition-all duration-500 group cursor-pointer',
        statusColors[agent.status],
        agent.status === 'active' && 'scale-[1.02]'
      )}
      onClick={() => setExpanded(!expanded)}
    >
      {/* Header */}
      <div className="flex items-center gap-3">
        {/* Avatar */}
        <div
          className={cn(
            'relative flex items-center justify-center w-10 h-10 rounded-full text-lg shrink-0',
            agent.status === 'active' ? 'bg-blue-500/20 ring-2 ring-blue-500/30' :
            agent.status === 'completed' ? 'bg-emerald-500/20' :
            'bg-slate-500/10'
          )}
        >
          <span>{agent.icon}</span>
          {/* Status dot */}
          <span
            className={cn(
              'absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-background',
              statusDots[agent.status]
            )}
          />
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="text-xs font-bold text-foreground truncate">{agent.name}</h4>
            <span
              className={cn(
                'text-[9px] font-semibold uppercase px-1.5 py-0.5 rounded-full border',
                agent.status === 'active' ? 'text-blue-400 border-blue-500/30 bg-blue-500/10' :
                agent.status === 'completed' ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' :
                agent.status === 'error' ? 'text-red-400 border-red-500/30 bg-red-500/10' :
                'text-slate-400 border-slate-600/50 bg-slate-500/10'
              )}
            >
              {statusLabels[agent.status]}
            </span>
          </div>
          <p className="text-2xs text-muted-foreground truncate mt-0.5">
            {agent.currentTask}
          </p>
        </div>

        {/* Progress indicator */}
        {agent.status === 'active' && (
          <div className="flex items-center gap-1 shrink-0">
            <div className="w-12 h-1.5 bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 rounded-full transition-all duration-700 ease-out"
                style={{ width: `${agent.progress}%` }}
              />
            </div>
            <span className="text-[10px] font-mono text-blue-400 w-7 text-right">
              {agent.progress}%
            </span>
          </div>
        )}

        {/* Expand indicator */}
        <span className="text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity text-xs">
          {expanded ? '▲' : '▼'}
        </span>
      </div>

      {/* Expanded reasoning/details */}
      {expanded && (
        <div className="mt-3 pt-3 border-t border-border space-y-2 animate-[fade-in_0.2s_ease-out]">
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-muted-foreground">Role</span>
              <p className="text-foreground/80 mt-0.5">{agent.role}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Last Action</span>
              <p className="text-foreground/80 mt-0.5">{agent.lastAction}</p>
            </div>
            {agent.startedAt && (
              <div>
                <span className="text-muted-foreground">Started</span>
                <p className="text-foreground/80 mt-0.5 font-mono text-xs">
                  {new Date(agent.startedAt).toLocaleTimeString('en-US', { hour12: false })}
                </p>
              </div>
            )}
            {agent.completedAt && (
              <div>
                <span className="text-muted-foreground">Completed</span>
                <p className="text-foreground/80 mt-0.5 font-mono text-xs">
                  {new Date(agent.completedAt).toLocaleTimeString('en-US', { hour12: false })}
                </p>
              </div>
            )}
            {agent.dependencies.length > 0 && (
              <div className="col-span-2">
                <span className="text-muted-foreground">Dependencies</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {agent.dependencies.map((dep) => (
                    <span
                      key={dep}
                      className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700/30 text-slate-400 border border-slate-700/50 font-mono"
                    >
                      {dep}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Reasoning placeholder — shows the agent's thought process */}
          {agent.status === 'active' && (
            <div className="bg-slate-900/50 rounded p-2 border border-slate-700/30">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-2xs font-semibold text-slate-500 uppercase">Reasoning</span>
                <div className="flex gap-1">
                  <span className="h-1 w-1 rounded-full bg-slate-600 animate-pulse" />
                  <span className="h-1 w-1 rounded-full bg-slate-600 animate-pulse delay-75" />
                  <span className="h-1 w-1 rounded-full bg-slate-600 animate-pulse delay-150" />
                </div>
              </div>
              <p className="text-xs text-muted-foreground italic">
                Analyzing {agent.currentTask.toLowerCase()} using agentic reasoning chain...
              </p>
            </div>
          )}

          {agent.status === 'completed' && (
            <div className="bg-emerald-500/5 rounded p-2 border border-emerald-500/20">
              <span className="text-2xs font-semibold text-emerald-500 uppercase">✓ Completed Successfully</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function AgentCollaborationView({ agents, className }: AgentCollaborationViewProps) {
  const activeCount = agents.filter((a) => a.status === 'active').length;
  const completedCount = agents.filter((a) => a.status === 'completed').length;
  const errorCount = agents.filter((a) => a.status === 'error').length;

  return (
    <div className={cn('rounded-lg border border-border bg-card overflow-hidden', className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-border bg-surface-container-highest">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[16px] text-muted-foreground">groups</span>
          <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">
            AI Collaboration
          </h3>
          <span className="text-xs font-mono text-muted-foreground">
            {agents.length} agents
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs">
          {activeCount > 0 && (
            <span className="flex items-center gap-1.5 text-blue-400">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
              </span>
              {activeCount} active
            </span>
          )}
          {completedCount > 0 && (
            <span className="text-emerald-400">
              ✓ {completedCount} done
            </span>
          )}
          {errorCount > 0 && (
            <span className="text-red-400">
              ⚠ {errorCount} errors
            </span>
          )}
        </div>
      </div>

      {/* Agent cards */}
      <div className="p-4 space-y-2">
        {agents.map((agent) => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>
    </div>
  );
}
