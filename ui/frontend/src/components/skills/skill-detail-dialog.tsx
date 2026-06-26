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
      <DialogContent className="max-w-2xl bg-card border-border text-foreground">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3 text-foreground">
            <span className="font-mono text-sm text-muted-foreground">{skill.id}</span>
            {skill.curated && (
              <span className="inline-flex items-center gap-1 text-xs text-primary">
                <Star className="h-3.5 w-3.5 fill-primary" />
                Curated
              </span>
            )}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-5 mt-4">
          {/* Error type */}
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted-foreground">Error Type:</span>
            <ErrorTypeBadge errorType={skill.error_type} />
          </div>

          {/* Pattern */}
          <div>
            <h4 className="text-sm font-semibold text-foreground/80 mb-2">Bug Pattern</h4>
            <p className="text-sm text-muted-foreground bg-muted rounded-lg p-4 border border-border">
              {skill.pattern}
            </p>
          </div>

          {/* Fix */}
          <div>
            <h4 className="text-sm font-semibold text-foreground/80 mb-2">Fix Applied</h4>
            <p className="text-sm text-muted-foreground bg-muted rounded-lg p-4 border border-border">
              {skill.fix}
            </p>
          </div>

          {/* Example code */}
          {skill.example && (
            <div>
              <h4 className="text-sm font-semibold text-foreground/80 mb-2">Example</h4>
              <CodeBlock code={skill.example} language="verilog" maxLines={20} />
            </div>
          )}

          {/* Metadata */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="bg-muted rounded-lg p-3 border border-border">
              <span className="text-muted-foreground text-xs">Design</span>
              <p className="text-foreground/80 font-mono mt-1">{skill.design_name || '—'}</p>
            </div>
            <div className="bg-muted rounded-lg p-3 border border-border">
              <span className="text-muted-foreground text-xs">Category</span>
              <p className="text-foreground/80 font-mono mt-1">{skill.category}</p>
            </div>
            <div className="bg-muted rounded-lg p-3 border border-border">
              <span className="text-muted-foreground text-xs">Success Count</span>
              <p className="text-foreground/80 font-mono mt-1">{skill.success_count}</p>
            </div>
            <div className="bg-muted rounded-lg p-3 border border-border">
              <span className="text-muted-foreground text-xs">Confirmed Count</span>
              <p className="text-foreground/80 font-mono mt-1">{skill.confirmed_count}</p>
            </div>
          </div>

          {skill.last_seen && (
            <p className="text-xs text-muted-foreground">
              Last seen: {formatRelativeTime(skill.last_seen)}
            </p>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
