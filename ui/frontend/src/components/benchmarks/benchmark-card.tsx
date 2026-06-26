'use client';

import Link from 'next/link';
import { FileCode, FlaskConical, Bug } from 'lucide-react';
import { CategoryBadge } from './category-badge';
import { cn } from '@/lib/utils';
import { truncate } from '@/lib/formatters';
import type { BenchmarkInfo } from '@/lib/types';

interface BenchmarkCardProps {
  benchmark: BenchmarkInfo;
  isComplete?: boolean;
}

export function BenchmarkCard({ benchmark, isComplete = false }: BenchmarkCardProps) {
  return (
    <Link
      href={`/benchmarks/${benchmark.name}`}
      className={cn(
        'block rounded-lg border border-border bg-card p-5 transition-all duration-200',
        'hover:border-primary/30 hover:bg-accent hover:-translate-y-0.5',
        'hover:shadow-[0_4px_20px_rgba(240,152,55,0.08)]',
        isComplete && 'border-primary/20 shadow-[0_0_20px_rgba(240,152,55,0.05)]'
      )}
    >
      <div className="flex items-start justify-between mb-3">
        <CategoryBadge category={benchmark.category_guess} />
        {isComplete && (
          <span className="inline-flex items-center rounded-full bg-primary/15 text-primary px-2 py-0.5 text-2xs font-semibold border border-primary/20">
            GDSII ✓
          </span>
        )}
      </div>

      <h3 className="text-lg font-semibold text-foreground mb-2 font-mono">
        {benchmark.name}
      </h3>

      <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
        {truncate(benchmark.spec_preview || 'No specification available', 120)}
      </p>

      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        <span className={cn('flex items-center gap-1', benchmark.has_reference_rtl && 'text-emerald-500')}>
          <FileCode className="h-3.5 w-3.5" />
          RTL
        </span>
        <span className={cn('flex items-center gap-1', benchmark.has_reference_tb && 'text-emerald-500')}>
          <FlaskConical className="h-3.5 w-3.5" />
          TB
        </span>
        <span className={cn('flex items-center gap-1', benchmark.bug_count > 0 && 'text-yellow-400')}>
          <Bug className="h-3.5 w-3.5" />
          {benchmark.bug_count} {benchmark.bug_count === 1 ? 'bug' : 'bugs'}
        </span>
      </div>
    </Link>
  );
}
