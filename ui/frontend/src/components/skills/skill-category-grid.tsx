'use client';

import { SkillCategoryCard } from './skill-category-card';
import { LoadingSkeleton } from '@/components/shared/loading-skeleton';
import { EmptyState } from '@/components/shared/empty-state';
import { ErrorState } from '@/components/shared/error-state';
import { useSkills } from '@/hooks/use-skills';
import { Brain } from 'lucide-react';

export function SkillCategoryGrid() {
  const { data, isLoading, isError, error, refetch } = useSkills();
  const categories = data?.categories || [];

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <LoadingSkeleton key={i} variant="card" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <ErrorState
        message={error instanceof Error ? error.message : 'Failed to load skills'}
        onRetry={() => refetch()}
      />
    );
  }

  if (categories.length === 0) {
    return (
      <EmptyState
        icon={Brain}
        title="No skills found"
        description="The Trace2Skill knowledge base is empty."
      />
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
      {categories.map((cat) => (
        <SkillCategoryCard key={cat.category} summary={cat} />
      ))}
    </div>
  );
}
