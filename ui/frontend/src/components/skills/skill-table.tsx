'use client';

import { useState } from 'react';
import { Star, Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ErrorTypeBadge } from './error-type-badge';
import { LoadingSkeleton } from '@/components/shared/loading-skeleton';
import { EmptyState } from '@/components/shared/empty-state';
import { ErrorState } from '@/components/shared/error-state';
import { useSkillCategory } from '@/hooks/use-skills';
import { truncate } from '@/lib/formatters';
import { Brain } from 'lucide-react';
import type { SkillEntry } from '@/lib/types';

interface SkillTableProps {
  category: string;
  onSkillClick: (skill: SkillEntry) => void;
}

export function SkillTable({ category, onSkillClick }: SkillTableProps) {
  const { data, isLoading, isError, error, refetch } = useSkillCategory(category);
  const [sortField, setSortField] = useState<keyof SkillEntry>('confirmed_count');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  const skills = data?.skills || [];

  const sorted = [...skills].sort((a, b) => {
    const aVal = a[sortField];
    const bVal = b[sortField];
    if (aVal === undefined || aVal === null || bVal === undefined || bVal === null) return 0;
    if (aVal < bVal) return sortDir === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortDir === 'asc' ? 1 : -1;
    return 0;
  });

  if (isLoading) return <LoadingSkeleton lines={8} />;
  if (isError) return <ErrorState message={error instanceof Error ? error.message : 'Failed to load'} onRetry={() => refetch()} />;
  if (skills.length === 0) return <EmptyState icon={Brain} title="No skills in this category" description="No Trace2Skill entries found." />;

  return (
    <div className="rounded-lg border border-silicon-700 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-silicon-700 bg-silicon-850">
              {['ID', 'Error Type', 'Pattern', 'Fix', 'Design', 'Success', 'Confidence', ''].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-silicon-500 uppercase tracking-wider">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((skill) => (
              <tr
                key={skill.id}
                className="border-b border-silicon-700/50 hover:bg-silicon-800/50 cursor-pointer transition-colors"
                onClick={() => onSkillClick(skill)}
              >
                <td className="px-4 py-3 font-mono text-xs text-silicon-400 flex items-center gap-2">
                  {skill.curated && <Star className="h-3 w-3 text-copper-500 fill-copper-500" />}
                  {skill.id}
                </td>
                <td className="px-4 py-3">
                  <ErrorTypeBadge errorType={skill.error_type} />
                </td>
                <td className="px-4 py-3 text-silicon-300 max-w-[200px] truncate">
                  {truncate(skill.pattern, 80)}
                </td>
                <td className="px-4 py-3 text-silicon-300 max-w-[200px] truncate">
                  {truncate(skill.fix, 80)}
                </td>
                <td className="px-4 py-3 text-silicon-500 font-mono text-xs">
                  {skill.design_name || '—'}
                </td>
                <td className="px-4 py-3 text-silicon-400 font-mono text-xs">
                  {skill.success_count}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-1.5 rounded-full bg-silicon-700 min-w-[60px]">
                      <div
                        className="h-full rounded-full bg-plasma-blue transition-all"
                        style={{ width: `${Math.min(100, (skill.confirmed_count / Math.max(1, skill.success_count)) * 100)}%` }}
                      />
                    </div>
                    <span className="text-xs text-silicon-500 font-mono w-8">
                      {skill.confirmed_count}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <Button variant="ghost" size="icon" className="h-7 w-7 text-silicon-500 hover:text-silicon-200">
                    <Eye className="h-3.5 w-3.5" />
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
