'use client';

import { AppShell } from '@/components/layout/app-shell';
import { PageContainer } from '@/components/layout/page-container';
import { SkillCategoryGrid } from '@/components/skills/skill-category-grid';
import { useSkills } from '@/hooks/use-skills';

export default function SkillsPage() {
  const { data } = useSkills();

  return (
    <AppShell>
      <PageContainer
        title="Trace2Skill Knowledge Base"
        description={`${data?.total_skills || 0} skills across 5 categories. The AI's accumulated debugging knowledge from fixing real RTL bugs.`}
      >
        <SkillCategoryGrid />
      </PageContainer>
    </AppShell>
  );
}
