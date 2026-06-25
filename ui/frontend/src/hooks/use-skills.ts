// ============================================================
// TanStack Query hooks for skill endpoints
// ============================================================

'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { API_PATHS } from '@/lib/constants';
import type { SkillListResponse, SkillCategoryResponse } from '@/lib/types';

export function useSkills() {
  return useQuery({
    queryKey: ['skills'],
    queryFn: async () => {
      const res = await api.get<SkillListResponse>(API_PATHS.skills);
      return res.data;
    },
    staleTime: 2 * 60 * 1000, // 2 min
  });
}

export function useSkillCategory(category: string | undefined) {
  return useQuery({
    queryKey: ['skills', category],
    queryFn: async () => {
      if (!category) throw new Error('Category is required');
      const res = await api.get<SkillCategoryResponse>(API_PATHS.skillCategory(category));
      return res.data;
    },
    enabled: !!category,
    staleTime: 2 * 60 * 1000,
  });
}
