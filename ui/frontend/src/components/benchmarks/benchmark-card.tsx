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
        'block rounded-lg border border-silicon-700 bg-silicon-850 p-5 transition-all duration-200',
        'hover:border-copper-500/30 hover:bg-silicon-800 hover:-translate-y-0.5',
        'hover:shadow-[0_4px_20px_rgba(240,152,55,0.08)]',
        isComplete && 'border-copper-500/20 shadow-[0_0_20px_rgba(240,152,55,0.05)]'
      )}
    >
      <div className="flex items-start justify-between mb-3">
        <CategoryBadge category={benchmark.category_guess} />
        {isComplete && (
          <span className="inline-flex items-center rounded-full bg-copper-500/15 text-copper-500 px-2 py-0.5 text-2xs font-semibold border border-copper-500/20">
            GDSII ✓
          </span>
        )}
      </div>

      <h3 className="text-lg font-semibold text-silicon-100 mb-2 font-mono">
        {benchmark.name}
      </h3>

      <p className="text-sm text-silicon-400 mb-4 line-clamp-2">
        {truncate(benchmark.spec_preview || 'No specification available', 120)}
      </p>

      <div className="flex items-center gap-4 text-xs text-silicon-500">
        <span className={cn('flex items-center gap-1', benchmark.has_reference_rtl && 'text-photo-green')}>
          <FileCode className="h-3.5 w-3.5" />
          RTL
        </span>
        <span className={cn('flex items-center gap-1', benchmark.has_reference_tb && 'text-photo-green')}>
          <FlaskConical className="h-3.5 w-3.5" />
          TB
        </span>
        <span className={cn('flex items-center gap-1', benchmark.bug_count > 0 && 'text-mask-yellow')}>
          <Bug className="h-3.5 w-3.5" />
          {benchmark.bug_count} {benchmark.bug_count === 1 ? 'bug' : 'bugs'}
        </span>
      </div>
    </Link>
  );
}
