'use client';

import Link from 'next/link';
import { cn } from '@/lib/utils';
import { ErrorTypeBadge } from './error-type-badge';
import { CATEGORY_INFO } from '@/lib/constants';
import type { SkillCategorySummary } from '@/lib/types';

interface SkillCategoryCardProps {
  summary: SkillCategorySummary;
}

export function SkillCategoryCard({ summary }: SkillCategoryCardProps) {
  const info = CATEGORY_INFO[summary.category];
  const label = info?.label || summary.category;

  return (
    <Link
      href={`/skills/${summary.category}`}
      className={cn(
        'block rounded-lg border border-silicon-700 bg-silicon-850 p-6 transition-all duration-200',
        'hover:border-plasma-blue/30 hover:bg-silicon-800 hover:-translate-y-0.5',
        'hover:shadow-[0_4px_20px_rgba(78,156,245,0.08)]'
      )}
    >
      <h3 className="text-sm font-semibold text-silicon-400 uppercase tracking-wider mb-4">
        {label}
      </h3>

      <div className="text-4xl font-bold text-copper-500 mb-3 font-mono">
        {summary.total_skills}
      </div>

      <div className="text-xs text-silicon-400 mb-4 space-y-0.5">
        <div className="flex justify-between">
          <span>Curated</span>
          <span className="text-photo-green font-mono">{summary.curated_count}</span>
        </div>
        <div className="flex justify-between">
          <span>Confirmed</span>
          <span className="text-plasma-blue font-mono">{summary.confirmed_count}</span>
        </div>
        <div className="flex justify-between">
          <span>Unconfirmed</span>
          <span className="text-silicon-500 font-mono">{summary.unconfirmed_count}</span>
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5">
        {summary.error_types.map((type) => (
          <ErrorTypeBadge key={type} errorType={type} />
        ))}
      </div>
    </Link>
  );
}
