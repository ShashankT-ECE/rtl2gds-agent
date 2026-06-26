'use client';

import { X, Download, ExternalLink, Code, FileText, Clock, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { DemoStageDetail } from '@/stores/demo-store';
import { STAGE_LABELS } from '@/lib/constants';

interface StageDetailDrawerProps {
  stage: DemoStageDetail | null;
  isOpen: boolean;
  onClose: () => void;
}

function Section({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="border-t border-border pt-4 first:border-t-0 first:pt-0">
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{title}</h4>
      </div>
      {children}
    </div>
  );
}

function StatRow({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex justify-between py-1 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className={cn('text-foreground', mono ? 'font-mono text-xs' : '')}>{value}</span>
    </div>
  );
}

export function StageDetailDrawer({ stage, isOpen, onClose }: StageDetailDrawerProps) {
  if (!stage || !isOpen) return null;

  const label = STAGE_LABELS[stage.stageName] || stage.stageName;

  const statusColors = {
    pending: 'border-slate-600',
    running: 'border-blue-500',
    completed: 'border-emerald-500',
    failed: 'border-red-500',
    skipped: 'border-slate-600 border-dashed',
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/40 z-40 animate-[fade-in_0.15s_ease-out]"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="fixed inset-y-0 right-0 w-full max-w-lg bg-background border-l border-border z-50 shadow-2xl animate-[slide-in-right_0.3s_ease-out] overflow-y-auto">
        {/* Header */}
        <div className={cn(
          'sticky top-0 bg-background/95 backdrop-blur-sm border-b px-6 py-4 z-10 flex items-start justify-between',
          statusColors[stage.status]
        )}>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-muted-foreground">STAGE REPORT</span>
              <span className={cn(
                'text-[10px] font-bold uppercase px-1.5 py-0.5 rounded border',
                stage.status === 'completed' ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' :
                stage.status === 'running' ? 'text-blue-400 border-blue-500/30 bg-blue-500/10' :
                stage.status === 'failed' ? 'text-red-400 border-red-500/30 bg-red-500/10' :
                'text-slate-400 border-slate-600/50 bg-slate-500/10'
              )}>
                {stage.status.toUpperCase()}
              </span>
            </div>
            <h2 className="text-lg font-bold text-foreground mt-1">{label}</h2>
          </div>
          <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Summary */}
          <Section title="Summary" icon={<FileText className="h-3.5 w-3.5 text-muted-foreground" />}>
            <StatRow label="Status" value={stage.status} />
            {stage.startedAt && (
              <StatRow label="Started" value={new Date(stage.startedAt).toLocaleTimeString('en-US', { hour12: false })} mono />
            )}
            {stage.completedAt && (
              <StatRow label="Completed" value={new Date(stage.completedAt).toLocaleTimeString('en-US', { hour12: false })} mono />
            )}
            {stage.startedAt && stage.completedAt && (
              <StatRow label="Duration" value={`${((new Date(stage.completedAt).getTime() - new Date(stage.startedAt).getTime()) / 1000).toFixed(1)}s`} mono />
            )}
            <StatRow label="Agent" value={stage.agent} mono />
          </Section>

          {/* Execution Logs */}
          {stage.logs.length > 0 && (
            <Section title="Execution Log" icon={<Code className="h-3.5 w-3.5 text-muted-foreground" />}>
              <div className="bg-[#0a0a0b] rounded border border-border p-3 font-mono text-xs space-y-1 max-h-48 overflow-y-auto terminal-scroll">
                {stage.logs.map((log, idx) => (
                  <div key={idx} className="text-slate-400 hover:text-slate-300 transition-colors">
                    {log}
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* Inputs/Outputs */}
          <Section title="IO & Artifacts" icon={<Download className="h-3.5 w-3.5 text-muted-foreground" />}>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <span className="text-2xs font-semibold text-muted-foreground uppercase">Inputs</span>
                <div className="mt-1 space-y-1">
                  {stage.inputs.length > 0 ? stage.inputs.map((inp, idx) => (
                    <div key={idx} className="text-xs text-foreground/80 bg-slate-700/20 px-2 py-1 rounded border border-border font-mono">
                      {inp}
                    </div>
                  )) : (
                    <p className="text-xs text-muted-foreground italic">None</p>
                  )}
                </div>
              </div>
              <div>
                <span className="text-2xs font-semibold text-muted-foreground uppercase">Outputs</span>
                <div className="mt-1 space-y-1">
                  {stage.outputs.length > 0 ? stage.outputs.map((out, idx) => (
                    <div key={idx} className="text-xs text-foreground/80 bg-slate-700/20 px-2 py-1 rounded border border-border font-mono flex items-center justify-between group">
                      {out}
                      <Download className="h-3 w-3 text-muted-foreground opacity-0 group-hover:opacity-100 cursor-pointer" />
                    </div>
                  )) : (
                    <p className="text-xs text-muted-foreground italic">None</p>
                  )}
                </div>
              </div>
            </div>
          </Section>

          {/* Generated Artifacts */}
          {stage.artifacts.length > 0 && (
            <Section title="Generated Artifacts" icon={<ExternalLink className="h-3.5 w-3.5 text-muted-foreground" />}>
              <div className="space-y-1.5">
                {stage.artifacts.map((artifact, idx) => (
                  <button
                    key={idx}
                    className="w-full text-left flex items-center justify-between px-3 py-2 rounded border border-border bg-surface-container-low hover:bg-surface-container transition-colors text-sm"
                  >
                    <span className="font-mono text-xs text-foreground/80">{artifact}</span>
                    <Download className="h-3.5 w-3.5 text-muted-foreground" />
                  </button>
                ))}
              </div>
            </Section>
          )}

          {/* Reports */}
          {stage.reports.length > 0 && (
            <Section title="Reports" icon={<FileText className="h-3.5 w-3.5 text-muted-foreground" />}>
              <div className="space-y-1.5">
                {stage.reports.map((report, idx) => (
                  <button
                    key={idx}
                    className="w-full text-left flex items-center justify-between px-3 py-2 rounded border border-border bg-surface-container-low hover:bg-surface-container transition-colors text-sm"
                  >
                    <div className="flex items-center gap-2">
                      <FileText className="h-3.5 w-3.5 text-blue-400" />
                      <span className="font-mono text-xs text-foreground/80">{report}</span>
                    </div>
                    <ExternalLink className="h-3.5 w-3.5 text-muted-foreground" />
                  </button>
                ))}
              </div>
            </Section>
          )}

          {/* Warnings */}
          {stage.status === 'failed' && (
            <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-4">
              <div className="flex items-center gap-2 text-red-400">
                <AlertTriangle className="h-4 w-4" />
                <span className="text-sm font-semibold">Stage Failed</span>
              </div>
              <p className="text-xs text-red-300/70 mt-2">
                Check the execution log above for error details. The Debug Agent has been notified and will attempt
                to resolve the issue automatically.
              </p>
            </div>
          )}
        </div>
      </div>

      <style jsx>{`
        @keyframes slide-in-right {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
      `}</style>
    </>
  );
}
