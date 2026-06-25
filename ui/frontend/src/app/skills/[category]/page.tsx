'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageContainer } from '@/components/layout/page-container';
import { SkillTable } from '@/components/skills/skill-table';
import { SkillDetailDialog } from '@/components/skills/skill-detail-dialog';
import { LoadingSkeleton } from '@/components/shared/loading-skeleton';
import { ErrorState } from '@/components/shared/error-state';
import { useSkills } from '@/hooks/use-skills';
import { CATEGORY_INFO } from '@/lib/constants';
import { Button } from '@/components/ui/button';
import type { SkillEntry } from '@/lib/types';

export default function SkillCategoryPage() {
  const params = useParams();
  const router = useRouter();
  const category = params.category as string;
  const info = CATEGORY_INFO[category];
  const [selectedSkill, setSelectedSkill] = useState<SkillEntry | null>(null);
  const { data } = useSkills();
  const summary = data?.categories.find((c) => c.category === category);

  return (
    <AppShell>
      <PageContainer
        title={info?.label || category}
        description={summary
          ? `${summary.total_skills} skills · ${summary.curated_count} curated · ${summary.confirmed_count} confirmed · ${summary.unconfirmed_count} unconfirmed`
          : undefined}
      >
        <Button
          variant="ghost"
          className="text-silicon-400 hover:text-silicon-200"
          onClick={() => router.push('/skills')}
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Categories
        </Button>

        <SkillTable
          category={category}
          onSkillClick={(skill) => setSelectedSkill(skill)}
        />

        <SkillDetailDialog
          skill={selectedSkill}
          open={!!selectedSkill}
          onOpenChange={(open) => {
            if (!open) setSelectedSkill(null);
          }}
        />
      </PageContainer>
    </AppShell>
  );
}
