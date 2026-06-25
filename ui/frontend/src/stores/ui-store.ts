// ============================================================
// UI Store — layout preferences, selections, filters
// ============================================================

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { PipelineVersion, Severity, EventType } from '@/lib/types';

interface UIStoreState {
  // Layout
  sidebarExpanded: boolean;
  sidebarCollapsed: boolean;
  rightPanelOpen: boolean;

  // Dashboard
  selectedBenchmark: string | null;
  selectedVersion: PipelineVersion;
  eventFilter: {
    severity?: Severity;
    eventType?: EventType;
  };

  // Actions
  toggleSidebar: () => void;
  setSidebarCollapsed: (v: boolean) => void;
  toggleRightPanel: () => void;
  setRightPanelOpen: (v: boolean) => void;
  setSelectedBenchmark: (name: string | null) => void;
  setSelectedVersion: (v: PipelineVersion) => void;
  setEventFilter: (filter: { severity?: Severity; eventType?: EventType }) => void;
  clearEventFilter: () => void;
}

export const useUIStore = create<UIStoreState>()(
  devtools(
    persist(
      (set) => ({
        sidebarExpanded: true,
        sidebarCollapsed: false,
        rightPanelOpen: true,

        selectedBenchmark: null,
        selectedVersion: 'v3',
        eventFilter: {},

        toggleSidebar: () =>
          set((state) => ({
            sidebarExpanded: !state.sidebarExpanded,
            sidebarCollapsed: false,
          })),

        setSidebarCollapsed: (v) =>
          set({ sidebarCollapsed: v, sidebarExpanded: v ? false : true }),

        toggleRightPanel: () =>
          set((state) => ({ rightPanelOpen: !state.rightPanelOpen })),

        setRightPanelOpen: (v) => set({ rightPanelOpen: v }),

        setSelectedBenchmark: (name) => set({ selectedBenchmark: name }),

        setSelectedVersion: (v) => set({ selectedVersion: v }),

        setEventFilter: (filter) => set({ eventFilter: filter }),

        clearEventFilter: () => set({ eventFilter: {} }),
      }),
      {
        name: 'ui-store',
        partialize: (state) => ({
          sidebarCollapsed: state.sidebarCollapsed,
          selectedVersion: state.selectedVersion,
          selectedBenchmark: state.selectedBenchmark,
        }),
      }
    ),
    { name: 'ui-store' }
  )
);
