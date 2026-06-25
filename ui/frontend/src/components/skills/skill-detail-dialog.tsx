'use client';

import { Star } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ErrorTypeBadge } from './error-type-badge';
import { CodeBlock } from '@/components/shared/code-block';
import { formatRelativeTime } from '@/lib/formatters';
import type { SkillEntry } from '@/lib/types';

interface SkillDetailDialogProps {
  skill: SkillEntry | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SkillDetailDialog({ skill, open, onOpenChange }: SkillDetailDialogProps) {
  if (!skill) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl bg-silicon-850 border-silicon-700 text-silicon-200">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3 text-silicon-100">
            <span className="font-mono text-sm text-silicon-400">{skill.id}</span>
            {skill.curated && (
              <span className="inline-flex items-center gap-1 text-xs text-copper-500">
                <Star className="h-3.5 w-3.5 fill-copper-500" />
                Curated
              </span>
            )}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-5 mt-4">
          {/* Error type */}
          <div className="flex items-center gap-3">
            <span className="text-sm text-silicon-400">Error Type:</span>
            <ErrorTypeBadge errorType={skill.error_type} />
          </div>

          {/* Pattern */}
          <div>
            <h4 className="text-sm font-semibold text-silicon-300 mb-2">Bug Pattern</h4>
            <p className="text-sm text-silicon-400 bg-silicon-900 rounded-lg p-4 border border-silicon-700">
              {skill.pattern}
            </p>
          </div>

          {/* Fix */}
          <div>
            <h4 className="text-sm font-semibold text-silicon-300 mb-2">Fix Applied</h4>
            <p className="text-sm text-silicon-400 bg-silicon-900 rounded-lg p-4 border border-silicon-700">
              {skill.fix}
            </p>
          </div>

          {/* Example code */}
          {skill.example && (
            <div>
              <h4 className="text-sm font-semibold text-silicon-300 mb-2">Example</h4>
              <CodeBlock code={skill.example} language="verilog" maxLines={20} />
            </div>
          )}

          {/* Metadata */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="bg-silicon-900 rounded-lg p-3 border border-silicon-700">
              <span className="text-silicon-500 text-xs">Design</span>
              <p className="text-silicon-300 font-mono mt-1">{skill.design_name || '—'}</p>
            </div>
            <div className="bg-silicon-900 rounded-lg p-3 border border-silicon-700">
              <span className="text-silicon-500 text-xs">Category</span>
              <p className="text-silicon-300 font-mono mt-1">{skill.category}</p>
            </div>
            <div className="bg-silicon-900 rounded-lg p-3 border border-silicon-700">
              <span className="text-silicon-500 text-xs">Success Count</span>
              <p className="text-silicon-300 font-mono mt-1">{skill.success_count}</p>
            </div>
            <div className="bg-silicon-900 rounded-lg p-3 border border-silicon-700">
              <span className="text-silicon-500 text-xs">Confirmed Count</span>
              <p className="text-silicon-300 font-mono mt-1">{skill.confirmed_count}</p>
            </div>
          </div>

          {skill.last_seen && (
            <p className="text-xs text-silicon-500">
              Last seen: {formatRelativeTime(skill.last_seen)}
            </p>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
