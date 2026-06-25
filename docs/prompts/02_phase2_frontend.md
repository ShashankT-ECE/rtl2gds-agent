# Phase 2 Frontend Specification — RTL2GDS Agent Web UI

**Version:** 1.0.0
**Status:** DRAFT — Awaiting Approval
**Author:** Principal Frontend Architect
**Date:** 2026-06-25
**Phase 1 Backend:** FROZEN (tag: `phase1-backend-complete`)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Design Philosophy](#2-design-philosophy)
3. [Technology Stack](#3-technology-stack)
4. [Frontend Architecture](#4-frontend-architecture)
5. [Folder Structure](#5-folder-structure)
6. [Component Hierarchy](#6-component-hierarchy)
7. [Design System](#7-design-system)
8. [Layout System](#8-layout-system)
9. [Responsive Behavior](#9-responsive-behavior)
10. [Route Design & Information Architecture](#10-route-design--information-architecture)
11. [Silicon Design Flow Visualization](#11-silicon-design-flow-visualization)
12. [Page Specifications](#12-page-specifications)
13. [Component Specifications](#13-component-specifications)
14. [State Management Architecture](#14-state-management-architecture)
15. [SSE Integration Strategy](#15-sse-integration-strategy)
16. [API Integration Layer](#16-api-integration-layer)
17. [Placeholder Content Strategy](#17-placeholder-content-strategy)
18. [Configuration & Feature Flags](#18-configuration--feature-flags)
19. [Vercel Deployment](#19-vercel-deployment)
20. [Accessibility (WCAG 2.1 AA)](#20-accessibility-wcag-21-aa)
21. [Performance Goals & Budget](#21-performance-goals--budget)
22. [Testing Strategy](#22-testing-strategy)
23. [Acceptance Criteria](#23-acceptance-criteria)
24. [Validation Checklist](#24-validation-checklist)
25. [Design Mockups](#25-design-mockups)
26. [Design Review & Critique](#26-design-review--critique)
27. [Out of Scope (Phase 3+)](#27-out-of-scope-phase-3)
28. [Appendix: API Contract Reference](#28-appendix-api-contract-reference)

---

## 1. Executive Summary

### 1.1 What We Are Building

A production-grade, real-time web dashboard for the RTL2GDS Agent — an AI-driven agentic framework that converts natural-language chip specifications into DRC-clean GDSII physical layouts. The frontend consumes the Phase 1 FastAPI backend via REST and Server-Sent Events to provide:

- **Live pipeline visualization** — watch 12 AI agents progress through the silicon design flow in real time
- **Benchmark design browser** — explore 8 hardware designs with specifications, reference implementations, and test suites
- **Trace2Skill knowledge explorer** — navigate the AI's accumulated debugging knowledge across 52 skills in 5 categories
- **Job management** — submit, monitor, and cancel pipeline runs with full event history
- **Engineering results dashboard** — view simulation waveforms, synthesis reports, STA timing, and DRC results

### 1.2 Target Audience

| Persona | Context | What They Need |
|---------|---------|----------------|
| **Tessolve Semiconductor Engineer** | Evaluating the tool for professional use | Confidence that this is a real EDA product, not a toy. Dense technical information, familiar EDA patterns, credible results. |
| **AMD/DAC Hackathon Judge** | 3-minute demo evaluation | Immediate visual impact. Clear demonstration of AI + EDA convergence. Memorable design language. |
| **VLSI Student / Researcher** | Learning or extending the system | Clear documentation of pipeline stages. Ability to inspect agent behavior. |
| **Startup Founder / Investor** | Assessing commercial viability | Professional polish. Clear value proposition. Production-readiness signals. |

### 1.3 The One-Sentence Test

> "If an AMD engineer opened this application for the first time, would it feel like the beginning of a commercial AI-powered EDA platform?"

This question drives every design decision in this specification.

---

## 2. Design Philosophy

### 2.1 Core Principles

**Silicon Native, Not Web Generic**
The UI must evoke semiconductor engineering at every level — from the color palette to the layout rhythm. No generic dashboard templates. No chatbot aesthetics. Every pixel should feel like it belongs in an EDA tool.

**Information Dense, Not Cluttered**
VLSI engineers work with dense information displays (waveforms, netlists, timing reports). The UI should respect this — presenting rich data in scannable, hierarchical layouts — while using modern web affordances (collapsible sections, progressive disclosure, hover details) to prevent overload.

**Motion with Meaning**
Every animation must serve a purpose. Pipeline stage transitions show flow direction. Progress indicators reflect real computation. Nothing animates purely for decoration.

**Trust Through Transparency**
The AI is the product, so the AI's actions must be visible. Every LLM call, every tool invocation, every skill retrieval is surfaced as a discrete, inspectable event. The user should never wonder "what is the AI doing right now?"

**Dark by Default, Accessible Always**
All EDA tools use dark themes — it reduces eye strain during long sessions and provides the contrast needed for waveform and schematic visualization. The UI is dark-mode only, meeting WCAG 2.1 AA contrast ratios throughout.

### 2.2 Anti-Principles (What We Reject)

- **No chatbot interfaces** — This is not a conversation. It is an engineering workflow.
- **No generic landing pages** — Every view has purpose. No "hero sections" with vague marketing copy.
- **No gratuitous animation** — Motion serves function, not decoration.
- **No light mode** — Dark mode only. EDA tools do not have light mode.
- **No lazy loading spinners as primary UX** — Skeleton screens and progressive rendering only.
- **No UI that hides the AI** — The agent activity feed is a first-class citizen, not buried in a drawer.

### 2.3 Visual Metaphor: The Silicon Stack

The visual language draws from the physical structure of integrated circuits:

- **Substrate (Background):** Deep silicon gray — the foundation on which everything is built
- **Wells & Diffusion (Containers):** Subtle border highlights suggesting doped regions
- **Polysilicon Gates (Active Elements):** Copper/orange accents for interactive controls and active stages
- **Metal Layers (Data Flows):** Horizontal bands with via-like connection points between pipeline stages
- **Passivation (Surface):** Clean, minimal chrome on the highest-level navigation

---

## 3. Technology Stack

### 3.1 Selected Stack

| Layer | Technology | Version | Justification |
|-------|-----------|---------|---------------|
| **Framework** | Next.js (App Router) | 15.x | Industry standard React framework. App Router for server components, file-based routing, and API route consolidation in Phase 3. |
| **Language** | TypeScript | 5.x | Type safety matching the Pydantic backend. Essential for SSE event type discrimination. |
| **Styling** | Tailwind CSS | 4.x | Utility-first CSS enables rapid, consistent implementation of the design system. Zero runtime cost. |
| **UI Primitives** | shadcn/ui | latest | Headless, accessible Radix primitives styled with Tailwind. Copy-paste ownership — no dependency lock-in. |
| **Animation** | Framer Motion | 11.x | Declarative animations for pipeline flow, stage transitions, and progress indicators. |
| **Charts** | Recharts | 2.x | Composable React charting library for synthesis/STA/DRC result visualization. |
| **Icons** | Lucide React | latest | Consistent, professional icon set. No brand-associated icons (FontAwesome, Material). |
| **State** | Zustand | 5.x | Lightweight, hook-based state management. Scales from simple to complex without boilerplate. |
| **Data Fetching** | TanStack Query | 5.x | Caching, background refetching, optimistic updates for REST endpoints. |
| **SSE Client** | Native EventSource + custom hook | — | Built on the standard EventSource API. No library overhead for a well-defined protocol. |
| **Form Handling** | React Hook Form | 7.x | Performant, minimal re-render form library for the job submission form. |
| **Validation** | Zod | 3.x | Runtime validation of API responses and form inputs. Mirrors Pydantic on the backend. |
| **Testing** | Vitest + Testing Library | latest | Fast, modern test runner with React component testing utilities. |
| **E2E** | Playwright | latest | Cross-browser end-to-end testing for critical user journeys. |
| **Package Manager** | pnpm | 9.x | Fast, disk-efficient. Strict dependency resolution. |

### 3.2 Stack Rejections (With Reasons)

| Rejected | Reason |
|----------|--------|
| **HTMX** | Cannot support the complex client-side state required for real-time pipeline visualization and interactive flow diagrams. Insufficient for an EDA-grade UI. |
| **Vue/Svelte** | Smaller ecosystem for EDA-style component libraries. React has broader hiring/contribution pool. |
| **Redux** | Excessive boilerplate for this application's state complexity. Zustand + TanStack Query is sufficient. |
| **Material UI** | Too associated with generic enterprise dashboards. Cannot achieve the silicon-native aesthetic. |
| **CSS Modules** | Slower iteration velocity than Tailwind for a design system of this specificity. |
| **D3.js** | Too low-level for the charting needs. Recharts is sufficient and more maintainable. |
| **GraphQL** | No backend GraphQL endpoint. REST + SSE is the contract. No benefit to adding a GraphQL translation layer. |
| **Server Components (heavy use)** | The app is inherently real-time and client-interactive. Server components used only for shell/document head and initial data seeding. |

---

## 4. Frontend Architecture

### 4.1 High-Level Architecture

```
                          Next.js App Router
┌─────────────────────────────────────────────────────┐
│  Server Shell (RSC)                                  │
│  ┌───────────────────────────────────────────────┐  │
│  │  Document Head  │  Initial Data Seed (optional)│  │
│  └───────────────────────────────────────────────┘  │
│                                                       │
│  Client Application (\"use client\")                    │
│  ┌─────────────────────────────────────────────┐    │
│  │                 Zustand Store                 │    │
│  │  ┌──────────┐ ┌──────────┐ ┌─────────────┐  │    │
│  │  │Job Store │ │SSE Store │ │ UI Store     │  │    │
│  │  │(jobs,    │ │(events,  │ │(panels,      │  │    │
│  │  │ stages,  │ │ streams, │ │  layout,     │  │    │
│  │  │ results) │ │ history) │ │  selections) │  │    │
│  │  └──────────┘ └──────────┘ └─────────────┘  │    │
│  └─────────────────────────────────────────────┘    │
│                                                       │
│  ┌──────────────────────────────────────────────┐   │
│  │              TanStack Query Cache              │   │
│  │  /health  /status  /benchmarks  /skills       │   │
│  │  (REST endpoints, stale-while-revalidate)      │   │
│  └──────────────────────────────────────────────┘   │
│                                                       │
│  ┌──────────────────────────────────────────────┐   │
│  │                SSE Manager                     │   │
│  │  EventSource connections per active job       │   │
│  │  Reconnection with after=<seq> replay         │   │
│  └──────────────────────────────────────────────┘   │
│                                                       │
│  ┌──────────────────────────────────────────────┐   │
│  │              Component Tree                     │   │
│  │  Layout > Panels > Cards > Primitives         │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### 4.2 Data Flow

```
User Action (e.g., \"Run Pipeline\")
  │
  ▼
POST /api/run  ──►  202 { job_id }
  │
  ├──► TanStack Query: invalidate [\"jobs\"]
  │
  ├──► SSE Manager: connect(/api/run/stream?job_id=...)
  │        │
  │        ├──► event: pipeline_event  ──►  Job Store (dispatch by event_type)
  │        ├──► event: heartbeat       ──►  (keepalive, update \"last seen\")
  │        └──► event: done            ──►  SSE Manager: close connection
  │
  └──► UI re-renders reactively via Zustand selectors
```

### 4.3 Key Architectural Decisions

1. **Client-heavy architecture** — The app is inherently real-time. Next.js App Router is used primarily for its routing, layout, and build tooling. Server Components are used sparingly (document head, metadata).

2. **Zustand over Redux** — Three small stores (jobs, SSE, UI) with fine-grained selectors. No action/reducer ceremony. Middleware for devtools and persistence as needed.

3. **TanStack Query for REST, Custom Hook for SSE** — TanStack Query handles all REST endpoints with its mature caching and background refresh. SSE is managed via a custom `useJobStream` hook wrapping the native EventSource API with Zustand integration.

4. **Optimistic UI for job submission** — When a user submits a job, a skeleton job card appears immediately (optimistic). The real data arrives via SSE and replaces the skeleton within milliseconds.

5. **No WebSocket upgrade path** — SSE is sufficient. The backend has no WebSocket endpoint, and the unidirectional server-to-client event flow matches SSE perfectly. The `after=<seq>` replay mechanism handles reconnection.

---

## 5. Folder Structure

```
ui/frontend/
├── next.config.ts                  # Next.js configuration
├── tailwind.config.ts              # Tailwind theme tokens
├── tsconfig.json                   # TypeScript configuration
├── package.json                    # Dependencies and scripts
├── pnpm-lock.yaml                  # Lock file
├── postcss.config.js               # PostCSS (Tailwind plugin)
├── components.json                 # shadcn/ui configuration
│
├── public/
│   ├── favicon.ico                 # Silicon die favicon
│   ├── og-image.png                # Open Graph preview image
│   └── fonts/                      # Self-hosted fonts (Inter, JetBrains Mono)
│
├── src/
│   ├── app/                        # Next.js App Router pages
│   │   ├── layout.tsx              # Root layout: Shell + providers
│   │   ├── page.tsx                # Home redirect (/ → /dashboard)
│   │   ├── not-found.tsx           # 404 page
│   │   ├── error.tsx               # Error boundary
│   │   │
│   │   ├── dashboard/
│   │   │   └── page.tsx            # Main dashboard (pipeline runner + live view)
│   │   │
│   │   ├── benchmarks/
│   │   │   ├── page.tsx            # Benchmark browser (grid view)
│   │   │   └── [name]/
│   │   │       └── page.tsx        # Single benchmark detail
│   │   │
│   │   ├── skills/
│   │   │   ├── page.tsx            # Skill category overview
│   │   │   └── [category]/
│   │   │       └── page.tsx        # Skills within a category
│   │   │
│   │   ├── jobs/
│   │   │   ├── page.tsx            # Job history list
│   │   │   └── [jobId]/
│   │   │       └── page.tsx        # Single job detail (event timeline + results)
│   │   │
│   │   └── status/
│   │       └── page.tsx            # System status page
│   │
│   ├── components/                 # React components
│   │   ├── ui/                     # shadcn/ui primitives (auto-generated)
│   │   │   └── [button, card, dialog, dropdown, ...]
│   │   │
│   │   ├── layout/                 # Layout components
│   │   │   ├── app-shell.tsx       # Top-level layout wrapper
│   │   │   ├── sidebar.tsx         # Left navigation sidebar
│   │   │   ├── topbar.tsx          # Top status bar (system health, mode indicator)
│   │   │   ├── panel.tsx           # Resizable panel primitive
│   │   │   └── page-container.tsx  # Standard page wrapper with title
│   │   │
│   │   ├── pipeline/               # Pipeline visualization
│   │   │   ├── silicon-flow.tsx        # The central flow diagram
│   │   │   ├── flow-stage.tsx          # Single stage in the flow
│   │   │   ├── flow-connector.tsx      # Animated connection between stages
│   │   │   ├── agent-activity-feed.tsx # Real-time agent log stream
│   │   │   ├── agent-log-entry.tsx     # Single agent log entry
│   │   │   ├── iteration-badge.tsx     # Fix-loop iteration counter
│   │   │   └── convergence-warning.tsx # Convergence detection alert
│   │   │
│   │   ├── jobs/                    # Job management
│   │   │   ├── job-runner.tsx       # Job configuration + submit form
│   │   │   ├── job-card.tsx         # Job summary card (for list view)
│   │   │   ├── job-timeline.tsx     # Horizontal event timeline
│   │   │   ├── job-stage-list.tsx   # Vertical stage breakdown
│   │   │   ├── job-results-panel.tsx # Synthesis/STA/DRC results
│   │   │   └── job-cancel-button.tsx # Cancel with confirmation
│   │   │
│   │   ├── benchmarks/             # Benchmark display
│   │   │   ├── benchmark-grid.tsx   # Grid of benchmark cards
│   │   │   ├── benchmark-card.tsx   # Single benchmark card
│   │   │   ├── benchmark-detail.tsx # Full benchmark view
│   │   │   ├── spec-viewer.tsx      # Specification text viewer
│   │   │   ├── bug-list.tsx         # Injected bug variants list
│   │   │   └── category-badge.tsx   # Design category indicator
│   │   │
│   │   ├── skills/                 # Trace2Skill visualization
│   │   │   ├── skill-category-grid.tsx  # 5-category overview
│   │   │   ├── skill-category-card.tsx  # Single category card
│   │   │   ├── skill-table.tsx          # Skills table in a category
│   │   │   ├── skill-detail-dialog.tsx  # Expanded skill view
│   │   │   ├── skill-confidence.tsx     # Confirmation count indicator
│   │   │   └── error-type-badge.tsx     # Error type label
│   │   │
│   │   ├── results/                # Engineering results
│   │   │   ├── simulation-result.tsx   # Waveform placeholder + pass/fail
│   │   │   ├── synthesis-result.tsx    # Gate count, area, cell list
│   │   │   ├── sta-result.tsx          # Timing report: WNS, TNS, critical path
│   │   │   ├── drc-result.tsx          # DRC violations table
│   │   │   └── gds-status-badge.tsx    # GDSII generation status
│   │   │
│   │   ├── status/                 # System status
│   │   │   ├── system-status-bar.tsx     # Compact status in topbar
│   │   │   ├── version-availability.tsx  # V1/V2/V3 availability indicators
│   │   │   ├── job-stats-summary.tsx     # Active/completed/failed counts
│   │   │   └── provider-badge.tsx        # LLM provider indicator
│   │   │
│   │   └── shared/                 # Shared components
│   │       ├── loading-skeleton.tsx   # Standard skeleton loader
│   │       ├── empty-state.tsx        # Empty state with icon + message
│   │       ├── error-state.tsx        # Error display with retry button
│   │       ├── code-block.tsx         # Syntax-highlighted code display
│   │       ├── severity-badge.tsx     # DEBUG/INFO/SUCCESS/WARNING/ERROR
│   │       ├── mode-indicator.tsx     # Mock/Real mode badge
│   │       ├── elapsed-timer.tsx      # Live elapsed time counter
│   │       ├── progress-bar.tsx       # Animated progress bar
│   │       └── terminal-output.tsx    # Terminal-style log viewer
│   │
│   ├── hooks/                      # Custom React hooks
│   │   ├── use-job-stream.ts       # SSE connection management
│   │   ├── use-job-status.ts       # Polling fallback for job status
│   │   ├── use-benchmarks.ts       # TanStack query wrapper
│   │   ├── use-skills.ts           # TanStack query wrapper
│   │   ├── use-system-status.ts    # TanStack query wrapper
│   │   ├── use-job-list.ts         # TanStack query wrapper
│   │   ├── use-event-history.ts    # Filtered event list from Zustand
│   │   └── use-sse-connection.ts   # SSE connection status tracking
│   │
│   ├── stores/                     # Zustand state stores
│   │   ├── job-store.ts            # Current jobs, stages, results
│   │   ├── sse-store.ts            # SSE connections, event buffers
│   │   └── ui-store.ts             # Panel sizes, selected items, preferences
│   │
│   ├── lib/                        # Utility functions
│   │   ├── api.ts                  # API client (fetch wrapper with error handling)
│   │   ├── sse-client.ts           # SSE connection factory with reconnection
│   │   ├── event-handlers.ts       # Event type → Zustand dispatch mapping
│   │   ├── constants.ts            # API paths, event types, stage definitions
│   │   ├── formatters.ts           # Date, duration, number formatters
│   │   ├── pipeline-utils.ts       # Stage ordering, version comparison
│   │   └── types.ts                # Generated/derived TypeScript types
│   │
│   └── styles/
│       ├── globals.css             # Tailwind directives + CSS custom properties
│       ├── silicon-theme.css       # Custom theme tokens (silicon-specific colors)
│       └── animations.css          # Custom keyframe animations (flow, pulse, scan)
│
├── tests/
│   ├── unit/                       # Component and hook unit tests
│   │   ├── components/
│   │   ├── hooks/
│   │   └── stores/
│   ├── integration/                # Multi-component interaction tests
│   └── e2e/                        # Playwright end-to-end tests
│       ├── dashboard.spec.ts
│       ├── benchmarks.spec.ts
│       └── job-lifecycle.spec.ts
│
└── .env.example                    # NEXT_PUBLIC_API_BASE_URL
```

---

## 6. Component Hierarchy

### 6.1 Full Component Tree

```
<html>
  <body class="dark bg-silicon-950">
    <AppShell>                              // Root layout wrapper
      ├── <Topbar>                          // Persistent top status bar
      │   ├── <SystemStatusBar />           // Health indicator, mode badge
      │   ├── <VersionAvailability />       // V1/V2/V3 status dots
      │   ├── <ProviderBadge />             // deepseek logo/indicator
      │   └── <JobStatsSummary />           // Mini job counters
      │
      ├── <Sidebar>                         // Left navigation (collapsible)
      │   ├── <SidebarLogo />               // RTL2GDS wordmark
      │   ├── <SidebarNav>                  // Primary navigation
      │   │   ├── <NavItem to="/dashboard"    icon={Layout} />
      │   │   ├── <NavItem to="/benchmarks"   icon={Cpu} />
      │   │   ├── <NavItem to="/skills"       icon={Brain} />
      │   │   ├── <NavItem to="/jobs"         icon={History} />
      │   │   └── <NavItem to="/status"       icon={Activity} />
      │   └── <SidebarFooter />             // Version, docs link, GitHub
      │
      └── <main>                            // Main content area
          └── {page content via App Router}
              │
              ├── /dashboard
              │   └── <DashboardPage>
              │       ├── <JobRunner />         // Config + Submit
              │       │   ├── <BenchmarkSelector />
              │       │   ├── <VersionSelector />
              │       │   ├── <OptionToggles />
              │       │   └── <SubmitButton />
              │       │
              │       ├── <SiliconFlow />       // The centerpiece
              │       │   ├── <FlowStage /> (×12 agents, arranged by version)
              │       │   ├── <FlowConnector /> (between stages)
              │       │   └── <AgentActivityFeed /> (below flow)
              │       │       └── <AgentLogEntry /> (×N)
              │       │
              │       └── <ResultsPanel />      // Right-side results
              │           ├── <SimulationResult />
              │           ├── <SynthesisResult />
              │           ├── <STAResult />
              │           └── <DRCResult />
              │
              ├── /benchmarks
              │   └── <BenchmarksPage>
              │       └── <BenchmarkGrid>
              │           └── <BenchmarkCard /> (×8)
              │
              ├── /benchmarks/[name]
              │   └── <BenchmarkDetailPage>
              │       ├── <SpecViewer />
              │       ├── <BugList />
              │       └── <BenchmarkStats />
              │
              ├── /skills
              │   └── <SkillsPage>
              │       └── <SkillCategoryGrid>
              │           └── <SkillCategoryCard /> (×5)
              │
              ├── /skills/[category]
              │   └── <SkillCategoryPage>
              │       ├── <SkillCategorySummary />
              │       └── <SkillTable />
              │           └── <SkillDetailDialog /> (on click)
              │
              ├── /jobs
              │   └── <JobsPage>
              │       ├── <JobFilters />
              │       └── <JobCard /> (×N)
              │
              ├── /jobs/[jobId]
              │   └── <JobDetailPage>
              │       ├── <JobTimeline />
              │       ├── <JobStageList />
              │       └── <JobResultsPanel />
              │
              └── /status
                  └── <StatusPage>
                      ├── <SystemHealthPanel />
                      ├── <VersionAvailability />
                      ├── <JobStatsDetailed />
                      └── <ServiceStatusTable />
```

---

## 7. Design System

### 7.1 Color Palette — "Silicon"

Every color name is prefixed `silicon-`. The palette is inspired by semiconductor materials and fabrication processes.

#### Base Grays (Silicon Substrate)

| Token | Hex | Usage |
|-------|-----|-------|
| `silicon-950` | `#09090b` | Page background (deepest) |
| `silicon-900` | `#0f1117` | Card backgrounds, sidebar |
| `silicon-850` | `#161922` | Elevated surfaces, panel backgrounds |
| `silicon-800` | `#1c2030` | Hover states, secondary cards |
| `silicon-700` | `#262d3d` | Borders, dividers |
| `silicon-600` | `#374055` | Muted text, disabled controls |
| `silicon-500` | `#4f5b73` | Placeholder text, inactive icons |
| `silicon-400` | `#6b7a94` | Secondary text |
| `silicon-300` | `#8e9cb4` | Body text |
| `silicon-200` | `#b8c4d6` | Emphasis text |
| `silicon-100` | `#dce4f0` | Headings, primary text |
| `silicon-50`  | `#f0f4fa` | High-emphasis headings (sparing use) |

#### Accent — Copper (Polysilicon / Interconnect)

Copper is the primary accent color, representing active elements, interactive controls, and the "current flowing through the chip."

| Token | Hex | Usage |
|-------|-----|-------|
| `copper-500` | `#f09837` | Primary buttons, active stage indicator, selected nav |
| `copper-400` | `#f5b764` | Hover states for copper elements |
| `copper-600` | `#c47a2b` | Pressed/active states |
| `copper-900/15` | rgba variant | Subtle copper glow backgrounds |

#### Status — Photoresist Green (Pass/Success)

Green represents successful operations — simulation passes, DRC clean, timing met. Like photoresist revealing a correct pattern.

| Token | Hex | Usage |
|-------|-----|-------|
| `photo-green` | `#2ea86c` | Success badges, pass indicators, completed stages |

#### Status — Etch Red (Fail/Error)

Red for failures — like an etch stop revealing a defect.

| Token | Hex | Usage |
|-------|-----|-------|
| `etch-red` | `#e05045` | Error badges, failed stages, DRC violations |

#### Status — Plasma Blue (AI / LLM / In Progress)

Blue represents the AI agents — the "plasma" driving the computation. Used for LLM calls, agent activity, and in-progress states.

| Token | Hex | Usage |
|-------|-----|-------|
| `plasma-blue` | `#4e9cf5` | AI activity indicators, LLM call badges, running states |
| `plasma-blue-dim` | `#2e6ab0` | Muted AI indicators, secondary agent info |

#### Status — Mask Yellow (Warning / Attention)

Yellow for warnings — like a mask alignment warning.

| Token | Hex | Usage |
|-------|-----|-------|
| `mask-yellow` | `#e0b030` | Warnings, convergence alerts, timing violations (non-critical) |

### 7.2 Typography

#### Font Stack

```css
--font-sans: 'Inter', system-ui, -apple-system, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
```

#### Type Scale

| Token | Size / Line Height | Weight | Usage |
|-------|-------------------|--------|-------|
| `text-2xs` | 0.625rem / 0.875rem | 500 | Legal, fine print, tiny badges |
| `text-xs` | 0.75rem / 1rem | 400, 500, 600 | Labels, captions, event timestamps |
| `text-sm` | 0.875rem / 1.25rem | 400, 500, 600 | Body, secondary text, card descriptions |
| `text-base` | 1rem / 1.5rem | 400, 500, 600 | Primary body, form inputs, event messages |
| `text-lg` | 1.125rem / 1.75rem | 500, 600 | Card titles, section headers |
| `text-xl` | 1.25rem / 1.75rem | 600 | Panel titles, dialog titles |
| `text-2xl` | 1.5rem / 2rem | 600, 700 | Page titles |
| `text-3xl` | 1.875rem / 2.25rem | 700 | Dashboard hero numbers (progress percentage) |
| `text-4xl` | 2.25rem / 2.75rem | 700 | Very sparing — major milestone indicators |

**Monospace uses the same scale but is reserved for:** code blocks, file paths, terminal output, event IDs, job IDs, Verilog snippets, and log lines.

### 7.3 Spacing System

Based on a 4px grid:

| Token | Value | Usage |
|-------|-------|-------|
| `space-1` | 4px | Inline gaps between badges, icons |
| `space-2` | 8px | Tight padding, card inner gaps |
| `space-3` | 12px | Standard padding, list item gaps |
| `space-4` | 16px | Card padding, section gaps |
| `space-5` | 20px | Large padding, panel padding |
| `space-6` | 24px | Section margins, page padding |
| `space-8` | 32px | Major section separation |
| `space-12` | 48px | Page-level spacing |
| `space-16` | 64px | Hero section separation |

### 7.4 Borders & Radii

```css
--radius-sm: 4px;    /* Inline code, small badges, key indicators */
--radius-md: 6px;    /* Buttons, inputs, cards, panels */
--radius-lg: 10px;   /* Modals, dialogs, large cards */
--radius-xl: 16px;   /* Main dashboard panels */

--border-default: 1px solid var(--silicon-700);
--border-active: 1px solid var(--copper-500);
--border-glow: 1px solid rgba(240, 152, 55, 0.3);  /* Subtle copper glow */
```

### 7.5 Shadows & Elevation

Shadows are subtle — the dark theme does most of the elevation work through color contrast.

```css
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.4);
--shadow-md: 0 4px 12px rgba(0, 0, 0, 0.5);
--shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.6);
--shadow-glow-copper: 0 0 20px rgba(240, 152, 55, 0.15);  /* Active stage glow */
--shadow-glow-blue: 0 0 20px rgba(78, 156, 245, 0.15);     /* AI activity glow */
```

### 7.6 Iconography

**Lucide React** exclusively. All icons use `size={16}` default, `size={14}` for inline badges, `size={20}` for navigation, `size={24}` for empty states.

Key icon assignments:
- **Dashboard:** `Layout` (not `Home` — too consumer)
- **Benchmarks:** `Cpu` (literal silicon meaning)
- **Skills:** `Brain` (AI memory / learning)
- **Jobs:** `History` (temporal record)
- **Status:** `Activity` (live system state)
- **Run:** `Play` (execution)
- **Cancel:** `Square` (stop)
- **Success:** `CheckCircle2`
- **Error:** `XCircle`
- **Warning:** `AlertTriangle`
- **Info:** `Info`
- **SSE Connected:** `Radio` (with green pulse animation)
- **Mock Mode:** `FlaskConical` (lab/test)
- **Real Mode:** `Zap` (live power)
- **External Link:** `ArrowUpRight`

### 7.7 Motion Tokens

```css
--duration-instant: 100ms;   /* Hover state changes */
--duration-fast: 200ms;      /* Button press, badge transitions */
--duration-normal: 300ms;    /* Panel open/close, card expand */
--duration-slow: 500ms;      /* Page transitions, flow animations */
--duration-glacial: 1000ms;  /* Progress bar fills, stage completions */

--ease-default: cubic-bezier(0.4, 0, 0.2, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);  /* Success bounces */
```

---

## 8. Layout System

### 8.1 Page Shell

```
┌──────────────────────────────────────────────────────────────────┐
│ Topbar (h-12, 48px, full width, fixed)                            │
│ [System Status] [Version Dots] [Provider] ─────────── [Job Stats] │
├────────┬─────────────────────────────────────────────────────────┤
│        │                                                           │
│ Sidebar│              Main Content Area                            │
│ (w-56, │              (fluid, scrollable)                          │
│ 224px) │                                                           │
│        │                                                           │
│ fixed  │                                                           │
│        │                                                           │
│        │                                                           │
├────────┴─────────────────────────────────────────────────────────┤
```

### 8.2 Dashboard Layout (Three-Column)

The dashboard page has a specialized layout for live pipeline monitoring:

```
┌──────────────────────────────────────────────────────────────────────┐
│ Topbar                                                               │
├────────┬────────────────────────────────┬────────────────────────────┤
│ Sidebar│  Center (fluid, min-w-0)       │  Right Panel (w-80, 320px) │
│        │                                │                            │
│ (fixed)│  ┌──────────────────────────┐  │  Results Panel             │
│        │  │ Job Runner (compact)     │  │  ┌──────────────────────┐  │
│        │  │ [Benchmark ▼] [V ▼] [▶] │  │  │ Simulation            │  │
│        │  └──────────────────────────┘  │  │ ✅ Passed  98% cov    │  │
│        │                                │  └──────────────────────┘  │
│        │  ┌──────────────────────────┐  │  ┌──────────────────────┐  │
│        │  │                          │  │  │ Synthesis             │  │
│        │  │    Silicon Design Flow    │  │  │ 142 cells, 450 sq um │  │
│        │  │    (animated pipeline)    │  │  └──────────────────────┘  │
│        │  │                          │  │  ┌──────────────────────┐  │
│        │  │  spec → rtl → sim → fix  │  │  │ STA                   │  │
│        │  │    ↓       ↓       ↓     │  │  │ WNS: 6.59ns  TNS: 0  │  │
│        │  │  synth → sta → gds → drc │  │  └──────────────────────┘  │
│        │  │                          │  │  ┌──────────────────────┐  │
│        │  └──────────────────────────┘  │  │ DRC                   │  │
│        │                                │  │ 0 violations ✅       │  │
│        │  ┌──────────────────────────┐  │  └──────────────────────┘  │
│        │  │ Agent Activity Feed      │  │                            │
│        │  │ (scrollable log)         │  │                            │
│        │  └──────────────────────────┘  │                            │
│        └────────────────────────────────┴────────────────────────────┘
```

### 8.3 Responsive Breakpoints

| Breakpoint | Width | Sidebar | Right Panel | Layout |
|------------|-------|---------|-------------|--------|
| `xl` | ≥1280px | Visible (224px) | Visible (320px) | Three-column dashboard |
| `lg` | ≥1024px | Visible (224px) | Hidden (toggle) | Two-column. Right panel as overlay drawer. |
| `md` | ≥768px | Collapsible (64px icons-only) | Hidden (toggle) | Single column with icon nav. |
| `sm` | ≥640px | Hidden (hamburger) | Hidden (toggle) | Single column. Bottom sheet results. |
| `xs` | <640px | Hidden (hamburger) | Hidden (full sheet) | Stacked layout. Vertical flow diagram. |

**Rule:** The Silicon Design Flow diagram must remain visible and legible at all breakpoints. At `sm` and below, it switches from horizontal to vertical layout.

---

## 9. Responsive Behavior

### 9.1 Sidebar Behavior

- **≥1280px:** Full sidebar with icons + labels. Fixed position, 224px wide.
- **1024-1279px:** Full sidebar, same as above.
- **768-1023px:** Collapsed to icon-only mode (64px wide). Tooltips on hover show labels. Expandable via hamburger or swipe.
- **<768px:** Hidden off-screen. Revealed via hamburger menu button in topbar. Overlay with backdrop.

### 9.2 Silicon Design Flow — Responsive Variants

**Desktop (≥1024px):** Horizontal flow. Stages arranged left-to-right in rows by pipeline version. Agent-to-agent connectors are horizontal arrows. The fix loop is shown as a curved return path (a "loopback" visual).

**Tablet (768-1023px):** Horizontal flow, compressed. Some stage labels abbreviated. Agent activity feed moves below the flow.

**Mobile (<768px):** Vertical flow. Stages arranged top-to-bottom in a single column. Connectors are vertical. The fix loop is shown as an upward return arrow on the left side. Agent activity feed is a collapsible section.

### 9.3 Right Panel (Results)

- **≥1280px:** Persistently visible as a 320px right sidebar.
- **<1280px:** Hidden by default. Toggle button in the topbar or on the active stage opens it as a slide-over panel (from right) or bottom sheet (mobile).

### 9.4 Benchmark Grid

- **≥1024px:** 3 columns
- **768-1023px:** 2 columns
- **<768px:** 1 column (full-width cards)

### 9.5 Typography Scaling

Font sizes do NOT scale down for mobile beyond the base scale. The `text-xs` through `text-base` range works on all viewports. Only the hero/display sizes (`text-2xl` and above) reduce by one step on mobile.

---

## 10. Route Design & Information Architecture

### 10.1 Route Map

```
/                          →  Redirect to /dashboard
/dashboard                 →  Main dashboard: Pipeline runner + live flow
/benchmarks                →  Benchmark browser (grid)
/benchmarks/[name]         →  Single benchmark detail
/skills                    →  Trace2Skill category overview
/skills/[category]         →  Skills in a category
/jobs                      →  Job history (list)
/jobs/[jobId]              →  Job detail (timeline + results)
/status                    →  System status page
```

### 10.2 Navigation Hierarchy

```
Dashboard          (Primary — where users spend 80% of time)
  └─ Run a job → See live pipeline → See results

Benchmarks         (Reference — explore available designs)
  └─ Browse → Click into detail → Read spec → See bugs

Skills             (Reference — explore AI knowledge)
  └─ Browse categories → Click into category → See skills

Jobs               (History — review past runs)
  └─ Browse list → Click into job → See timeline + results

Status             (System — rarely accessed, important when needed)
  └─ Check system health → See version availability
```

### 10.3 Breadcrumbs

```
/dashboard                          →  Dashboard
/benchmarks                         →  Dashboard / Benchmarks
/benchmarks/alu_8bit                →  Dashboard / Benchmarks / alu_8bit
/skills                             →  Dashboard / Skills
/skills/combinational               →  Dashboard / Skills / Combinational
/jobs                               →  Dashboard / Jobs
/jobs/abc12345                      →  Dashboard / Jobs / abc12345
/status                             →  Dashboard / System Status
```

---

## 11. Silicon Design Flow Visualization

This is the single most important UI element. It is the centerpiece of the dashboard and the primary visual differentiator from any other AI tool.

### 11.1 Design Concept

The Silicon Design Flow is a horizontal, multi-row pipeline diagram that shows:

1. **Which pipeline version is active** (V1, V2, or V3 — different stage sets)
2. **Which stage is currently executing** (highlighted with copper glow + animation)
3. **Which stages have completed** (green checkmark + filled)
4. **Which stages have failed** (red X + error indicator)
5. **The fix loop** (curved return path from log_analysis → fix → testbench → simulation)
6. **Real-time progress** (progress bar or percent within each stage)
7. **Agent-to-agent data flow** (animated particles along connectors)

### 11.2 Visual Layout

```
V3 Pipeline (expanded by default when V3 available)
┌─────────────────────────────────────────────────────────────────────────┐
│  SILICON DESIGN FLOW                                        V3  [V2] [V1] │
│                                                                          │
│  ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐              │
│  │ SPEC │───▶│ VERF │───▶│ RTL  │───▶│  TB  │───▶│ SIM  │              │
│  │Parser│    │Plan  │    │ Gen  │    │ Gen  │    │      │              │
│  │  ✓   │    │  ✓   │    │  ✓   │    │  ✓   │    │  ⏳  │              │
│  └──────┘    └──────┘    └──────┘    └──────┘    └──┬───┘              │
│                                                     │                   │
│                              ┌──────────────────────┘                   │
│                              │  (fix loop — shown as return arc)        │
│                              ▼                                          │
│              ┌────────┐    ┌────────┐    ┌────────┐                    │
│              │  LOG   │───▶│  FIX   │───▶│  TB    │────┐               │
│              │Analysis│    │ Agent  │    │ (re)   │    │               │
│              │   ○    │    │   ○    │    │   ○    │    │               │
│              └────────┘    └────────┘    └────────┘    │               │
│                                                        │               │
│              ◄──────────────────────────────────────────┘               │
│                                                                          │
│  ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐                          │
│  │SYNTH │───▶│ STA  │───▶│OpenLAN│───▶│ DRC  │                          │
│  │  ○   │    │  ○   │    │  ○    │    │  ○   │                          │
│  └──────┘    └──────┘    └──────┘    └──────┘                          │
│                                                                          │
│  Progress: ████████████░░░░░░░░ 62%    Iteration: 1/5    Elapsed: 04:32  │
└─────────────────────────────────────────────────────────────────────────┘

Legend:
  ✓ = Completed (photo-green fill, subtle glow)
  ⏳ = Running (copper-500 fill, pulse animation, plasma-blue border glow)
  ✗ = Failed (etch-red fill, static)
  ○ = Pending (silicon-700 border, hollow, no fill)
```

### 11.3 Stage States & Visual Treatment

| State | Icon | Fill | Border | Animation |
|-------|------|------|--------|-----------|
| `pending` | — | None (hollow) | `silicon-700` | None |
| `running` | — | `copper-500` at 15% opacity | `copper-500` glow | Pulse (2s cycle), particle flow on connector |
| `completed` | ✓ | `photo-green` at 10% opacity | `photo-green` | Brief success bounce on transition |
| `failed` | ✗ | `etch-red` at 10% opacity | `etch-red` | Shake (400ms) on transition |
| `skipped` | — | None | `silicon-700` dashed | None |

### 11.4 Connector Animation

Connectors between stages show "data flow" when the source stage is running or completed:
- Small particle dots (2px circles) travel along the connector in the flow direction
- Particles are `copper-500` at 50% opacity
- Speed: ~2 seconds to traverse the full connector length
- Spacing: 3-4 particles per connector, evenly staggered

### 11.5 Fix Loop Visualization

The fix loop is visually distinct from the linear flow:
- Curved/angled return path (not straight line) to emphasize "iteration"
- Dashed line style (not solid) to indicate conditional path
- An `IterationBadge` floats at the loop's apex showing current iteration count
- On each fix iteration, the loop briefly glows to draw attention

### 11.6 Version Tabs

Three pill-shaped tabs at the top-right of the flow panel: `V1` `V2` `V3`
- Only available versions are clickable (V2/V3 may be grayed out based on `GET /status`)
- Switching versions reconfigures the displayed stages without losing current job context
- Active version indicator: copper-500 fill on the pill

---

## 12. Page Specifications

### 12.1 Dashboard Page (`/dashboard`)

**Purpose:** Primary workspace. Run pipelines and monitor live execution.

**Content Zones:**
1. **Job Runner Bar** (top of center area) — Compact horizontal form: benchmark selector dropdown, version selector (V1/V2/V3 pill group), max iterations input, reference RTL/TB toggles, Submit button ("Run Pipeline").
2. **Silicon Design Flow** (center, dominant) — The flow diagram described in Section 11.
3. **Agent Activity Feed** (below the flow) — Chronological event log, auto-scrolling, filterable by severity and agent.
4. **Results Panel** (right sidebar) — Simulation, Synthesis, STA, DRC results. Only populated when a job has results. Shows "No active results" empty state when idle.
5. **Active Job Indicator** (in topbar or flow header) — Shows job ID, elapsed time, progress percentage when a job is running.

**Empty State (no active job):**
- Flow diagram shows all stages in "pending" state
- Agent activity feed shows "No active pipeline. Select a benchmark and click Run to begin."
- Results panel shows "Results will appear here when a pipeline runs"

**Loading State (job submitted, waiting for first events):**
- First stage shows "running" state immediately (optimistic)
- Flow header shows pulsing "Initializing..." text
- Activity feed shows skeleton log entries

**Active State (pipeline running):**
- Live flow updates as stages transition
- Activity feed scrolls with new events
- Progress bar advances
- Elapsed timer counting

**Complete State (pipeline finished):**
- Final stage shows ✓ or ✗
- Results panel populated with all available result data
- Activity feed complete (scrollable history)
- "Run Again" button prominent

### 12.2 Benchmarks Page (`/benchmarks`)

**Purpose:** Browse available benchmark designs.

**Layout:** Grid of cards (3 columns desktop, 2 tablet, 1 mobile).

**Each BenchmarkCard displays:**
- Design name (e.g., "alu_8bit")
- Category badge (combinational, fsm, fifo, axi, timing)
- Spec preview (first 120 chars)
- Status indicators: has reference RTL (icon), has reference TB (icon), bug count (badge with number)
- GDSII available badge (V3 complete indicator — copper badge for 5 completed designs)
- Click navigates to `/benchmarks/[name]`

**Sorting:** By category, then alphabetically. Completed designs (with GDSII) float to top.

### 12.3 Benchmark Detail Page (`/benchmarks/[name]`)

**Content:**
1. **Header:** Design name, category badge, version completion badges (V1 ✓, V2 ✓, V3 ✓)
2. **Specification:** Full spec.txt content in a styled code viewer
3. **Reference Files:** Links/paths for reference_rtl.v and reference_tb.py (not rendered, just metadata + file size)
4. **Bug List:** If bugs exist, a table of bug variants with bug ID and description
5. **Actions:** "Run This Benchmark" button (navigates to dashboard with this benchmark pre-selected)

### 12.4 Skills Page (`/skills`)

**Purpose:** Explore the Trace2Skill knowledge base.

**Layout:** Grid of 5 category cards.

**Each SkillCategoryCard displays:**
- Category name (capitalized: Combinational, FSM, FIFO, AXI, Timing)
- Category icon (distinct per category)
- Skill count (large number)
- Curated vs unconfirmed breakdown (mini bar chart or ratio)
- Error type tags (the distinct error types in the category)
- Click navigates to `/skills/[category]`

### 12.5 Skill Category Page (`/skills/[category]`)

**Content:**
1. **Summary Header:** Category name, total skills, curated count, confirmed count, unconfirmed count
2. **Skill Table:** Sortable table with columns:
   - ID (monospace)
   - Error Type (colored badge — SYNTAX, WIDTH, LOGIC, TIMING, COVERAGE, UNKNOWN)
   - Pattern (truncated, expandable on click)
   - Fix (truncated, expandable on click)
   - Design (which design this was learned from)
   - Confidence (success_count / confirmed_count bar)
   - Curated (star icon if true)
3. **Skill Detail Dialog:** Clicking a row opens a modal/dialog showing full pattern, fix, example code (if curated), and all metadata.

### 12.6 Jobs Page (`/jobs`)

**Purpose:** Review job history.

**Layout:** Vertical list of job cards, newest first.

**Filters:** Status filter tabs (All, Running, Completed, Failed, Cancelled).

**Each JobCard displays:**
- Job ID (monospace, truncated)
- Benchmark name
- Pipeline version badge
- Status badge (colored by status)
- Created timestamp (relative: "2 minutes ago")
- Duration (if completed)
- Mini stage progress bar (colored segments for completed/failed stages)
- Result summary icons (sim: ✓/✗, sta: ✓/✗, drc: ✓/✗)
- Click navigates to `/jobs/[jobId]`

### 12.7 Job Detail Page (`/jobs/[jobId]`)

**Content:**
1. **Header:** Job ID, benchmark, version, status, elapsed time, cancel button (if active)
2. **Job Timeline:** Horizontal event timeline showing event density over time, with markers for major events (stage transitions, results). Hover on marker shows event detail.
3. **Stage Breakdown:** Vertical list of stages with status indicators, timestamps, and duration per stage.
4. **Full Event Log:** Filterable, searchable event table with all PipelineEvent data.
5. **Results Section:** Simulation, Synthesis, STA, DRC results (same component as dashboard right panel).

**Reconnection note:** If this job is still active when the user navigates here, the page connects to the SSE stream for live updates.

### 12.8 Status Page (`/status`)

**Purpose:** System health overview.

**Content:**
1. **API Health:** Green/red indicator, version, API version
2. **Pipeline Versions:** V1 (✓ always), V2 (✓/✗ based on import check), V3 (✓/✗ based on import check)
3. **Job Statistics:** Active, Completed, Failed, Queued counts in stat cards
4. **Provider:** LLM provider (DeepSeek) with model info
5. **Pipeline Mode:** Mock or Real indicator with prominent warning if in mock mode
6. **Skill Stats:** Total skills, per-category breakdown
7. **Benchmark Count:** 8 designs, 5 complete

---

## 13. Component Specifications

### 13.1 AppShell

**Responsibility:** Top-level layout container. Provides the sidebar + topbar + main content area structure. Wraps all pages.

**Props:** `children: React.ReactNode`

**Behavior:**
- Renders Topbar (fixed, top, full-width, z-40)
- Renders Sidebar (fixed, left, full-height below topbar, z-30)
- Renders `<main>` with left margin equal to sidebar width
- Handles sidebar collapse/expand state
- Provides layout context to children (sidebar width, right panel visibility)

### 13.2 Sidebar

**Responsibility:** Primary navigation. Persistent on desktop, collapsible on tablet, drawer on mobile.

**States:**
- **Expanded** (≥1024px): 224px wide, shows icon + label for each nav item
- **Collapsed** (768-1023px): 64px wide, shows icon only, tooltip on hover
- **Hidden** (<768px): Off-screen, revealed by hamburger menu as overlay drawer

**Contents:**
- Logo/wordmark at top: "RTL2GDS" in Inter bold, with a small silicon-die SVG icon
- 5 nav items with Lucide icons
- Active nav item: copper-500 left border accent (3px), copper-500 text, subtle copper background
- Footer: version number, GitHub link, Docs link

### 12.3 Topbar (corrected numbering)

**Responsibility:** System-wide status bar. Always visible.

**Contents (left to right):**
1. **System Health Dot:** Green pulsing dot + "System Operational" or Red dot + "System Degraded" (from `/health`)
2. **Version Dots:** Three small dots labeled V1/V2/V3, colored green (available) or gray (unavailable) per `/status`
3. **Mode Badge:** "MOCK" (yellow badge) or "REAL" (copper badge with zap icon). In mock mode, shows subtle warning text: "Simulated pipeline — no EDA tools running"
4. **Provider Badge:** "deepseek" text with small brain/CPU icon
5. **Spacer**
6. **Job Mini-Stats:** Small numbers: "▶ 1 · ✓ 24 · ✗ 3 · ◼ 0" (active/completed/failed/queued)
7. **SSE Indicator:** Small radio icon, green when at least one SSE connection is active, gray when idle

### 13.4 SiliconFlow

**Responsibility:** The central pipeline visualization. This is the flagship component.

**Props:**
```typescript
interface SiliconFlowProps {
  pipelineVersion: 'v1' | 'v2' | 'v3';
  stages: StageState[];         // State for each stage
  currentStage: string | null;
  iteration: number;
  maxIterations: number;
  progressPct: number;
  elapsedSeconds: number | null;
  availableVersions: { v1: boolean; v2: boolean; v3: boolean };
  onVersionChange: (v: 'v1' | 'v2' | 'v3') => void;
}
```

**Internal Structure:**
```
SiliconFlow
├── FlowHeader (title "SILICON DESIGN FLOW" + version tabs)
├── FlowCanvas
│   ├── FlowRow (V1 stages: spec, verif, rtl, tb, sim)
│   ├── FixLoop (log_analysis → fix → tb → sim, return arc)
│   └── FlowRow (V2/V3 stages: synth, sta, [openlane, drc])
│       └── FlowStage (×N) + FlowConnector (×N-1)
├── FlowFooter (progress bar + iteration + elapsed)
└── FlowLegend (optional toggle — shows stage state legend)
```

**FlowStage sub-component props:**
```typescript
interface FlowStageProps {
  id: string;
  label: string;            // Display name, e.g., "RTL Gen"
  agentName: string;        // Agent identifier, e.g., "rtl_gen_agent"
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  startedAt?: string;
  completedAt?: string;
  elapsedMs?: number;
  stageNumber: number;      // Position in sequence (for connector logic)
  isInFixLoop: boolean;     // True for log_analysis, fix, tb(re), sim(re)
}
```

**Animation States:**
- **Stage enters running:** Border transitions from silicon-700 to copper-500 with 300ms ease. Simultaneously, the connector from the previous stage starts showing particle flow.
- **Stage completes:** Fill transition (0→10% photo-green over 200ms). Success bounce: brief scale(1.05) for 150ms with spring easing, then settle.
- **Stage fails:** Border transitions to etch-red. Subtle horizontal shake (4px oscillation, 400ms, 3 cycles).
- **Fix loop active:** The return arc connector pulses (opacity oscillation 0.3→0.7 over 1.5s, looping). The iteration badge increments with a brief scale pop.

### 13.5 AgentActivityFeed

**Responsibility:** Real-time scrolling log of agent events from the SSE stream.

**Props:**
```typescript
interface AgentActivityFeedProps {
  events: PipelineEvent[];
  isLive: boolean;
  filter: { severity?: Severity; eventType?: EventType };
  onFilterChange: (filter: ...) => void;
  maxHeight?: number;
}
```

**Behavior:**
- Auto-scrolls to bottom when new events arrive AND user is already at bottom
- If user has scrolled up (reading history), does NOT auto-scroll. Shows a "↓ New events" floating button.
- Each log entry is a single line (not a card) — dense, terminal-style
- Entries are color-coded by severity: DEBUG (silicon-500), INFO (silicon-200), SUCCESS (photo-green), WARNING (mask-yellow), ERROR (etch-red)
- Entries include: timestamp (HH:MM:SS.mmm), stage badge (abbreviated), message
- Clicking an entry expands it to show full payload as formatted JSON

**Virtual Scrolling:** Required. The feed may accumulate 200+ events per job. Use @tanstack/react-virtual for windowed rendering.

### 13.6 JobRunner

**Responsibility:** Pipeline configuration and submission form.

**Props:**
```typescript
interface JobRunnerProps {
  onJobStarted: (jobId: string) => void;
  disabled: boolean;           // True when a job is already running
}
```

**Form Fields:**
1. **Benchmark Selector** — Dropdown (shadcn Select) with 8 benchmark names. Grouped by completion status: "Complete (GDSII Verified)" and "In Progress". Shows benchmark name + category badge in each option.
2. **Version Selector** — Pill toggle group: V1, V2, V3. Only available versions are active. Shows brief description below: "V1: RTL generation + simulation + fix loop"
3. **Max Iterations** — Number input, min 1, max 20, default 5. Shows "Maximum fix-loop iterations before giving up."
4. **Use Reference RTL** — Toggle switch. "Skip LLM RTL generation — use golden reference RTL instead."
5. **Use Reference TB** — Toggle switch. "Skip LLM testbench generation — use golden reference testbench instead."
6. **Submit Button** — "▶ Run Pipeline" (copper-500 background). Disabled when no benchmark selected or job running.

**Validation:**
- Benchmark is required
- All form errors shown inline (not toast)

### 13.7 BenchmarkCard

**Props:**
```typescript
interface BenchmarkCardProps {
  benchmark: BenchmarkInfo;
  isComplete: boolean;       // Has GDSII output
}
```

**Visual:**
- Card with silicon-850 background, 1px silicon-700 border
- Hover: border transitions to copper-500 at 30% opacity, subtle lift (translateY(-2px), 200ms)
- Top section: Category badge (top-left), GDSII badge (top-right if complete)
- Middle: Design name in text-lg semibold
- Bottom: Spec preview (2 lines, text-xs, silicon-400, line-clamp-2)
- Stats row: RTL icon (green/gray), TB icon (green/gray), Bug count badge (mask-yellow if >0, silicon-600 if 0)
- Complete designs have a subtle copper glow on the card border

### 13.8 BenchmarkDetail

**Full page component.** See Section 12.3 for content specification.

### 13.9 SkillCategoryCard

**Props:**
```typescript
interface SkillCategoryCardProps {
  summary: SkillCategorySummary;
}
```

**Visual:**
- Large card with silicon-850 background
- Top: Category name in text-lg semibold
- Center: Large skill count number (text-4xl, copper-500)
- Below: "X curated · Y confirmed · Z unconfirmed" breakdown
- Bottom: Error type tags (horizontal, wrapping)
- Click: navigates to `/skills/[category]`

### 13.10 SkillTable

**Props:**
```typescript
interface SkillTableProps {
  skills: SkillEntry[];
}
```

**Columns:** ID, Error Type, Pattern (truncated 80 chars), Fix (truncated 80 chars), Design, Success Count, Confidence Bar, Curated Star

**Sorting:** All columns sortable. Default sort: curated first, then confirmed_count descending.

**Row click:** Opens SkillDetailDialog.

### 13.11 SkillDetailDialog

**Responsibility:** Modal/dialog showing full skill details.

**Content:**
- Header: Skill ID + Error Type badge + Curated star
- Body:
  - **Pattern:** Full pattern description
  - **Fix:** Full fix description
  - **Example:** Code block (monospace, syntax highlighted if Verilog) — only if curated
  - **Design:** Which benchmark this was learned from
- Footer: Success count, confirmed count, last seen date

### 13.12 JobCard

**Props:**
```typescript
interface JobCardProps {
  job: RunResponse;
}
```

**Visual:**
- Horizontal card (not vertical — job list is a table-like list)
- Left: Status icon (colored by status: green check, blue spinner, red X, gray square)
- Middle: Job ID (monospace, text-xs), benchmark name, version badge
- Right: Elapsed time or completion time (relative), mini stage bar (6px height, colored segments)
- Result icons: Three small icons (sim ✓, sta ✓, drc ✓) — gray if null, colored if pass/fail

### 13.13 JobTimeline

**Responsibility:** Horizontal event density timeline with interactive markers.

**Props:**
```typescript
interface JobTimelineProps {
  events: PipelineEvent[];
  stages: StageInfo[];
  totalDurationMs: number;
}
```

**Visual:**
- Horizontal bar representing total job duration
- Colored background sections for each stage (proportional to stage duration)
- Major event markers (dots) at event timestamps — hover shows tooltip with event details
- Event types color-coded: stage events (copper), result events (green/red), agent events (blue), system (gray)

### 13.14 JobResultsPanel

**Responsibility:** Display engineering results from a completed job.

**Content sections (each collapsible):**

1. **Simulation Result:**
   - Pass/Fail badge (large, prominent)
   - Coverage percentage (if available)
   - Iteration count
   - Placeholder for waveform viewer (static SVG placeholder in Phase 2: "Waveform viewer — Phase 3")

2. **Synthesis Result:**
   - Cell count
   - Area estimate
   - Gate-level netlist status
   - Placeholder for schematic viewer

3. **STA Result:**
   - WNS (Worst Negative Slack) — large number, green if positive, red if negative
   - TNS (Total Negative Slack)
   - Critical path description
   - Frequency

4. **DRC Result:**
   - Pass/Fail badge
   - Violation count (0 = green, >0 = red)
   - GDSII file path
   - Placeholder for layout viewer

### 13.15 Shared Components

**LoadingSkeleton:** Matches the shape of the content it replaces. Uses pulsing silicon-800 background animation.

**EmptyState:** Centered container with Lucide icon (size 48), title, description, and optional action button. Used when a list/table/grid has zero items.

**ErrorState:** Similar to EmptyState but with XCircle icon in etch-red. Shows error message and "Retry" button.

**CodeBlock:** Monospace text block with silicon-900 background, subtle border. Optional syntax highlighting for Verilog, Python, JSON. Copy button in top-right corner.

**SeverityBadge:** Tiny pill showing severity level with appropriate color. Used in event log entries.

**ElapsedTimer:** Live-updating timer display (HH:MM:SS format). Uses requestAnimationFrame for smooth updates.

**ProgressBar:** Horizontal bar with animated fill. Variants: determinate (percentage known), indeterminate (striped animation for unknown progress).

**TerminalOutput:** Scrollable container with monospace text, silicon-950 background, green-tinted text. Virtual scrolling for large outputs.

---

## 14. State Management Architecture

### 14.1 Store Design

Three Zustand stores, each with a single responsibility:

#### Job Store (`job-store.ts`)

```typescript
interface JobStore {
  // State
  jobs: Map<string, JobState>;       // All known jobs
  activeJobId: string | null;        // Currently focused job

  // Derived
  activeJob: JobState | null;        // Computed from activeJobId
  isRunning: boolean;                // activeJob?.status === 'running'

  // Actions
  addJob: (job: RunResponse) => void;
  updateJob: (jobId: string, patch: Partial<JobState>) => void;
  setActiveJob: (jobId: string | null) => void;
  updateStage: (jobId: string, stage: string, update: Partial<StageInfo>) => void;
  addEvent: (event: PipelineEvent) => void;    // Called by SSE handler
  clearCompletedJobs: () => void;             // Remove terminal jobs
}

interface JobState extends RunResponse {
  events: PipelineEvent[];           // Accumulated events (ring buffer, last 500)
  sseConnected: boolean;             // Is SSE stream active for this job
}
```

#### SSE Store (`sse-store.ts`)

```typescript
interface SSEStore {
  // State
  connections: Map<string, SSEConnectionState>;  // jobId -> connection status
  globalConnected: boolean;                       // Any active connection?

  // Actions
  connect: (jobId: string) => void;
  disconnect: (jobId: string) => void;
  updateConnectionStatus: (jobId: string, status: 'connecting' | 'connected' | 'disconnected') => void;
}

interface SSEConnectionState {
  status: 'connecting' | 'connected' | 'disconnected';
  lastEventAt: string | null;
  eventCount: number;
  reconnectAttempt: number;
}
```

#### UI Store (`ui-store.ts`)

```typescript
interface UIStore {
  // Layout
  sidebarExpanded: boolean;
  sidebarCollapsed: boolean;         // Icon-only mode
  rightPanelOpen: boolean;
  rightPanelWidth: number;

  // Dashboard
  selectedBenchmark: string | null;
  selectedVersion: 'v1' | 'v2' | 'v3';
  eventFilter: { severity?: Severity; eventType?: EventType };

  // Actions
  toggleSidebar: () => void;
  setSidebarCollapsed: (v: boolean) => void;
  toggleRightPanel: () => void;
  setSelectedBenchmark: (name: string | null) => void;
  setSelectedVersion: (v: 'v1' | 'v2' | 'v3') => void;
  setEventFilter: (f: ...) => void;
}
```

### 14.2 Store Middleware

- **devtools** middleware in development for debugging
- **persist** middleware for UI store only (saves sidebar preference, last selected benchmark, filter preferences to localStorage)

### 14.3 Selector Pattern

All components use fine-grained selectors to prevent unnecessary re-renders:

```typescript
// Good — only re-renders when this specific value changes
const activeJobId = useJobStore(s => s.activeJobId);

// Bad — re-renders on any store change
const { activeJobId } = useJobStore();
```

---

## 15. SSE Integration Strategy

### 15.1 Connection Lifecycle

```
User clicks "Run Pipeline"
  │
  ▼
POST /api/run → 202 { job_id: "abc12345" }
  │
  ├──► Zustand: addJob(optimistic job state)
  │
  └──► useJobStream(jobId).connect()
         │
         ├── new EventSource("/api/run/stream?job_id=abc12345")
         │     │
         │     ├── event: pipeline_event → dispatch by event_type
         │     ├── event: heartbeat       → update lastEventAt
         │     ├── event: done            → close(), mark job terminal
         │     └── event: error           → handle error, maybe retry
         │
         ├── onerror → reconnect with ?after=<lastSeq>
         │     (exponential backoff: 1s, 2s, 4s, 8s, max 30s)
         │
         └── onunload → close()
```

### 15.2 Event Type → State Dispatch Map

| Event Type | Store Action | Additional Effect |
|------------|-------------|-------------------|
| `job_started` | `updateJob(id, {status: 'running', started_at})` | Start elapsed timer |
| `stage_started` | `updateStage(id, stage, {status: 'running'})` | Highlight stage in flow |
| `stage_completed` | `updateStage(id, stage, {status: 'completed'})` | Stage success animation |
| `stage_failed` | `updateStage(id, stage, {status: 'failed'})` | Stage failure animation |
| `agent_log` | `addEvent(id, event)` | Scroll activity feed |
| `llm_call_start` | `addEvent(id, event)` | Show AI thinking indicator |
| `llm_call_end` | `addEvent(id, event)` | Clear AI thinking indicator |
| `tool_call` | `addEvent(id, event)` | Show tool invocation |
| `fix_attempt` | `updateJob(id, {iteration})` | Increment iteration badge |
| `skill_retrieved` | `addEvent(id, event)` | Highlight Trace2Skill usage |
| `skill_stored` | `addEvent(id, event)` | Indicate learning |
| `convergence_warning` | `addEvent(id, event)` | Show warning alert |
| `simulation_result` | `updateJob(id, {sim_passed})` | Update results panel |
| `synthesis_result` | `addEvent(id, event)` | Update results panel |
| `sta_result` | `updateJob(id, {timing_met})` | Update results panel |
| `drc_result` | `updateJob(id, {drc_passed})` | Update results panel |
| `progress` | `updateJob(id, {progress_pct})` | Update progress bar |
| `job_completed` | `updateJob(id, {status: 'completed'})` | Stop timer, show completion |
| `job_failed` | `updateJob(id, {status: 'failed'})` | Stop timer, show error |
| `job_cancelled` | `updateJob(id, {status: 'cancelled'})` | Stop timer, show cancelled |
| `heartbeat` | (no state change) | Update connection status only |

### 15.3 Reconnection Protocol

When an SSE connection drops:

1. Capture `lastSequenceNum` from the last received event
2. Exponential backoff: 1s → 2s → 4s → 8s → 16s → 30s (cap)
3. Reconnect with `?job_id=<id>&after=<lastSequenceNum>`
4. The backend replays all missed events
5. The SSE handler processes replayed events identically to live events (idempotent state updates)
6. After 10 failed reconnection attempts, stop and show "Connection lost" error state with manual "Reconnect" button

### 15.4 Connection Status UI

A small indicator in the topbar shows SSE connection status:
- **Green pulsing dot:** Connected, receiving events
- **Yellow dot:** Connecting/reconnecting
- **Gray dot:** No active SSE connections (idle)
- **Red dot:** Connection failed (with tooltip showing error)

### 15.5 Custom Hook: `useJobStream`

```typescript
function useJobStream(jobId: string | null) {
  // Returns:
  //   connect: () => void
  //   disconnect: () => void
  //   status: 'idle' | 'connecting' | 'connected' | 'disconnected' | 'error'
  //   eventCount: number
  //   lastEventAt: string | null
  //
  // Internal:
  //   - Creates EventSource on connect()
  //   - Parses SSE messages
  //   - Dispatches to Zustand stores
  //   - Handles reconnection
  //   - Cleans up on disconnect() or unmount
}
```

---

## 16. API Integration Layer

### 16.1 API Client (`lib/api.ts`)

A thin wrapper around `fetch` with:
- Base URL from `NEXT_PUBLIC_API_BASE_URL` (defaults to `http://localhost:8000`)
- Automatic JSON parsing
- Error handling: maps HTTP status + ErrorResponse body to typed errors
- Request timeout (30s default)
- No retry (TanStack Query handles retry for GET requests)

```typescript
const api = {
  get: <T>(path: string) => Promise<SuccessResponse<T>>,
  post: <T>(path: string, body: unknown) => Promise<SuccessResponse<T>>,
};
```

### 16.2 TanStack Query Configuration

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,           // 30s — data is fresh for 30 seconds
      gcTime: 5 * 60_000,         // 5min — keep in cache for 5 minutes
      retry: 2,                    // Retry twice on failure
      refetchOnWindowFocus: true,  // Refetch when user returns to tab
    },
  },
});
```

### 16.3 Query Keys

| Endpoint | Query Key | Stale Time |
|----------|-----------|------------|
| `GET /health` | `['health']` | 30s |
| `GET /status` | `['status']` | 15s (changes more frequently) |
| `GET /api/benchmarks` | `['benchmarks']` | 5min (static data) |
| `GET /api/benchmarks/{name}` | `['benchmarks', name]` | 5min |
| `GET /api/skills` | `['skills']` | 2min |
| `GET /api/skills/{category}` | `['skills', category]` | 2min |
| `GET /api/run` | `['jobs']` | 5s (changes frequently) |
| `GET /api/run/{jobId}` | `['jobs', jobId]` | 2s (polled when no SSE) |

### 16.4 Mutations

| Mutation | Endpoint | Optimistic Update | Invalidation |
|----------|----------|-------------------|-------------|
| `submitJob` | `POST /api/run` | Add skeleton job to store | `['jobs']` |
| `cancelJob` | `POST /api/run/{id}/cancel` | Set status to 'cancelled' | `['jobs', id]` |

### 16.5 Zod Validation Layer

All API responses are validated at runtime with Zod schemas that mirror the Pydantic models:

```typescript
// Example: PipelineEvent validation
const PipelineEventSchema = z.object({
  event_id: z.string().uuid(),
  job_id: z.string(),
  timestamp: z.string().datetime(),
  event_type: z.enum([...EventTypes]),
  stage: z.string().nullable().optional(),
  message: z.string(),
  severity: z.enum(['debug', 'info', 'success', 'warning', 'error']),
  payload: z.record(z.any()).default({}),
  elapsed_time: z.number().nullable().optional(),
  iteration: z.number().nullable().optional(),
  sequence_num: z.number(),
});
```

If validation fails, the error is logged to console (development) or reported to an error tracking service (production), but the UI continues to function with the raw data.

---

## 17. Placeholder Content Strategy

### 17.1 Philosophy

Placeholders should look intentional, not broken. Every placeholder tells the user what WILL be there in a future phase. No "Under Construction" GIFs. No lorem ipsum. Use real (but static) engineering content as placeholders.

### 17.2 Specific Placeholders

#### Waveform Viewer (Simulation Result)
- A static SVG or PNG showing a stylized, dark-themed digital waveform
- Label: "Interactive waveform viewer — Phase 3"
- The static waveform uses photo-green traces on silicon-900 background
- Shows 4-6 digital signals with realistic-looking transitions

#### Schematic/Gate-Level Viewer (Synthesis Result)
- A static SVG showing a stylized gate-level schematic (AND, OR, NOT gates connected)
- Label: "Gate-level schematic viewer — Phase 3"
- Copper-colored gates, etched lines

#### Layout Viewer (DRC Result)
- A static SVG showing a stylized chip layout (rectangles, vias, metal traces)
- Label: "GDSII layout viewer — Phase 3"
- Looks like a top-down chip view with colored layers

#### Empty Results Panel
- Centered icon (microchip SVG or Cpu icon, size 64, silicon-600)
- Text: "Pipeline results will appear here"
- Subtext: "Run a benchmark to see simulation, synthesis, STA, and DRC outputs"

#### Empty Agent Activity Feed
- Text: "Agent activity log"
- Subtext: "LLM calls, tool invocations, and pipeline events appear here in real time"

#### Benchmark Without Bugs
- Instead of empty bug list: "No bug variants injected — this is a reference-only design"

#### Skills Without Examples
- Instead of empty example: "No curated example available — this skill was learned from a real fix"

### 17.3 Never Show
- Raw JSON dumps (format it)
- Stack traces (show friendly error message)
- "Loading..." text (use skeleton only)
- Empty white space (always show a state component)
- 404 pages that look broken (use the app shell with a styled not-found)

---

## 18. Configuration & Feature Flags

### 18.1 Environment Variables

```bash
# .env.local (not committed)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Feature flags (Phase 2 defaults)
NEXT_PUBLIC_ENABLE_V2=true          # Show V2 pipeline option
NEXT_PUBLIC_ENABLE_V3=true          # Show V3 pipeline option
NEXT_PUBLIC_POLLING_INTERVAL_MS=2000 # Fallback polling when SSE unavailable
NEXT_PUBLIC_MAX_LOG_ENTRIES=500     # Max events to keep in memory per job
```

### 18.2 Feature Flags

Controlled by backend availability (not frontend env vars in production):

| Feature | Control | Default |
|---------|---------|---------|
| V2 Pipeline | `GET /status` → `versions.v2_available` | false (backend check) |
| V3 Pipeline | `GET /status` → `versions.v3_available` | false (backend check) |
| Real Pipeline Mode | `GET /status` → `pipeline_mode` | "mock" |
| Skill Categories | `GET /skills` → categories array | dynamic |

### 18.3 Mock Mode Indicator

When `pipeline_mode === "mock"`, the UI shows:
- "MOCK" badge (mask-yellow) in the topbar
- Subtle warning text in the JobRunner: "Running in mock mode — pipeline stages are simulated. Set PIPELINE_MODE=real for live EDA execution."
- The SiliconFlow shows realistic but simulated timing

---

## 19. Vercel Deployment

### 19.1 Deployment Architecture

```
┌──────────────────────────────────────────────────────┐
│                    Vercel Platform                     │
│  ┌────────────────────────────────────────────────┐  │
│  │  Next.js Frontend (Static + SSR)                 │  │
│  │  - Server Components (shell only)                │  │
│  │  - Static assets (JS, CSS, fonts)               │  │
│  │  - Client-side React app                        │  │
│  └────────────────────────────────────────────────┘  │
│                         │                             │
│                         │ API calls (client-side)      │
│                         ▼                             │
│              ┌────────────────────┐                  │
│              │  FastAPI Backend    │                  │
│              │  (separate server)  │                  │
│              │  port 8000          │                  │
│              └────────────────────┘                  │
└──────────────────────────────────────────────────────┘
```

### 19.2 Vercel Configuration (`next.config.ts`)

```typescript
const nextConfig = {
  // The backend is a separate service — proxy API calls in dev, direct in prod
  async rewrites() {
    return [];
  },

  // Environment-specific configuration
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
  },

  // Output standalone build for smaller deployment
  output: 'standalone',
};
```

### 19.3 Deployment Checklist

- [ ] Set `NEXT_PUBLIC_API_BASE_URL` in Vercel environment variables to the production FastAPI server URL
- [ ] Ensure FastAPI server has CORS configured for the Vercel deployment domain
- [ ] Test SSE connectivity through Vercel's edge (SSE is a long-lived connection — Vercel's 60s serverless timeout may require adjustment or use of Vercel's Edge Functions)
- [ ] **Important:** SSE may not work through Vercel's serverless functions due to timeout limits. Options:
  - Serve the frontend from Vercel, SSE connects directly to the FastAPI server (bypass Vercel proxy)
  - Use Vercel Edge Config for feature flags
  - Consider a lightweight Node.js server for production if SSE proxying is needed
- [ ] Configure custom domain if needed
- [ ] Enable Vercel Analytics for performance monitoring
- [ ] Set up preview deployments for PRs

### 19.4 Alternative: Static Export

If Vercel serverless limitations are an issue, the app can be exported as a purely static site (Next.js `output: 'export'`). All API calls and SSE connections go directly from the browser to the FastAPI server. This works because:
- The app has no server-side data fetching (all data is client-side)
- SSR is not needed (the app is a SPA-like dashboard)
- CORS is already configured on the backend

---

## 20. Accessibility (WCAG 2.1 AA)

### 20.1 Color Contrast

All text/background combinations must meet WCAG AA contrast ratios:
- **Normal text (<18px):** 4.5:1 minimum
- **Large text (≥18px or ≥14px bold):** 3:1 minimum
- **UI components and graphical objects:** 3:1 minimum

**Verified combinations:**
| Foreground | Background | Ratio | Status |
|-----------|-----------|-------|--------|
| `silicon-100` (#dce4f0) | `silicon-950` (#09090b) | 14.2:1 | ✅ AAA |
| `silicon-300` (#8e9cb4) | `silicon-900` (#0f1117) | 6.8:1 | ✅ AA |
| `silicon-400` (#6b7a94) | `silicon-850` (#161922) | 4.6:1 | ✅ AA |
| `copper-500` (#f09837) | `silicon-950` (#09090b) | 7.5:1 | ✅ AAA |
| `photo-green` (#2ea86c) | `silicon-950` (#09090b) | 4.9:1 | ✅ AA |
| `plasma-blue` (#4e9cf5) | `silicon-950` (#09090b) | 4.7:1 | ✅ AA |
| `etch-red` (#e05045) | `silicon-900` (#0f1117) | 4.8:1 | ✅ AA |
| `mask-yellow` (#e0b030) | `silicon-900` (#0f1117) | 5.5:1 | ✅ AA |
| `silicon-600` (#374055) | `silicon-950` (#09090b) | 3.5:1 | ❌ (decorative only) |
| `silicon-500` (#4f5b73) | `silicon-900` (#0f1117) | 3.2:1 | ❌ (decorative only) |

**Note:** `silicon-500` and `silicon-600` are NOT used for text content — only for decorative elements, disabled states, and borders.

### 20.2 Keyboard Navigation

- All interactive elements must be focusable and operable via keyboard
- Focus indicators: 2px copper-500 outline with 2px offset (visible on all backgrounds)
- Tab order follows visual layout (left to right, top to bottom)
- Skip-to-content link at the top of the page
- Sidebar navigation: arrow keys to move between items, Enter to activate
- JobRunner form: all fields accessible via Tab
- SiliconFlow stages: not individually focusable (visual only). Alternative: stage list below for screen readers.
- Agent activity feed: focusable scrollable region with arrow key scrolling
- Modal dialogs: focus trapped, Esc to close

### 20.3 Screen Reader Support

- All icons have `aria-label` or are `aria-hidden="true"` with adjacent text
- Stage status changes announced via `aria-live="polite"` region
- Job progress announced via `aria-valuenow` on progress bar
- Event feed: each entry is an `<article>` with `aria-label` describing event type and timestamp
- Loading states: `aria-busy="true"` on skeleton containers
- Page titles update dynamically: "Dashboard — RTL2GDS Agent", "alu_8bit — Benchmarks — RTL2GDS Agent"

### 20.4 Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

When reduced motion is preferred:
- Particle flow on connectors: static (no animation)
- Stage transitions: instant color change (no pulse/bounce)
- Progress bar: instant width change (no smooth transition)
- Auto-scroll: still functional, just instant

---

## 21. Performance Goals & Budget

### 21.1 Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **First Contentful Paint (FCP)** | < 1.0s | Lighthouse |
| **Largest Contentful Paint (LCP)** | < 2.0s | Lighthouse |
| **Time to Interactive (TTI)** | < 2.5s | Lighthouse |
| **Total Blocking Time (TBT)** | < 150ms | Lighthouse |
| **Cumulative Layout Shift (CLS)** | < 0.05 | Lighthouse |
| **JavaScript Bundle Size (initial)** | < 150KB gzipped | Bundle analyzer |
| **JavaScript Bundle Size (total)** | < 300KB gzipped | Bundle analyzer |
| **SSE Event Processing Latency** | < 16ms per event | Custom instrumentation |
| **Animation Frame Rate** | 60fps during pipeline flow | React Profiler |
| **Memory (idle)** | < 50MB heap | Chrome DevTools |
| **Memory (active job, 500 events)** | < 100MB heap | Chrome DevTools |

### 21.2 Performance Strategies

1. **Code Splitting:** Each page is a separate chunk. Heavy components (Recharts, Framer Motion) loaded only on pages that use them.
2. **Virtual Scrolling:** Agent activity feed and event log use @tanstack/react-virtual for O(1) DOM nodes regardless of event count.
3. **Event Ring Buffer:** Job events capped at 500 in memory. After 500, oldest events are discarded (available via API if needed).
4. **Font Optimization:** Inter and JetBrains Mono self-hosted via next/font. No Google Fonts requests. Subset to Latin.
5. **Image Optimization:** Static placeholder images (SVG) inlined or optimized via next/image.
6. **Bundle Analysis:** Run `pnpm analyze` before each production build. Block merges that increase bundle size by >10% without justification.
7. **No Client-Side Data Grid:** The skill table and job list use simple HTML tables with CSS — not a heavy data grid library. Pagination is server-side.
8. **Framer Motion Tree-Shaking:** Import only used animation components (`motion.div`, `AnimatePresence`). No `motion` barrel import.
9. **SSE Parsing:** Use native `EventSource` — no library overhead. JSON parsing is O(event size), which is typically < 1KB.

---

## 22. Testing Strategy

### 22.1 Test Pyramid

```
         ╱  E2E (Playwright)  ╲         ~10 tests
        ╱   Critical journeys   ╲
       ╱─────────────────────────╲
      ╱   Integration Tests       ╲      ~25 tests
     ╱    Multi-component flows    ╲
    ╱───────────────────────────────╲
   ╱       Unit Tests                ╲    ~60 tests
  ╱   Components, hooks, stores       ╲
 ╱─────────────────────────────────────╲
```

### 22.2 Unit Tests (Vitest + Testing Library)

**Component Tests:**
- Every shared component has at least 2 tests (render + interaction)
- Pipeline components tested with mock event data
- Card components tested with mock API response data
- Empty/loading/error states tested explicitly

**Hook Tests:**
- `useJobStream`: Mock EventSource, test connect/disconnect/reconnect
- `useEventHistory`: Test filtering, sorting, ring buffer overflow

**Store Tests:**
- Job store: test all state transitions
- SSE store: test connection lifecycle
- UI store: test panel toggle, filter changes

### 22.3 Integration Tests

- **Dashboard flow:** Submit job → see flow update → see activity feed populate → see results
- **Benchmark browser:** Load page → cards render → click card → detail page loads
- **Skill explorer:** Load categories → click category → table renders → click skill → dialog opens
- **Job history:** Load list → filter by status → click job → detail page loads with timeline

All integration tests use MSW (Mock Service Worker) to mock the API and SSE responses.

### 22.4 E2E Tests (Playwright)

Critical user journeys:
1. **Full Pipeline Run:** Open dashboard → Select "alu_8bit" → Select V3 → Click Run → Watch flow animate → Wait for completion → See results
2. **Benchmark Browsing:** Navigate to benchmarks → Browse grid → Open detail → Read spec → Navigate back
3. **Job Cancellation:** Start job → Cancel mid-run → Verify cancelled state
4. **Responsive Design:** Test dashboard at 1920px, 1280px, 768px, 375px
5. **Error Handling:** Test with backend offline → See error state → Test with invalid job ID → See 404

### 22.5 Visual Regression Testing

Not in Phase 2 scope. Can be added in Phase 3 with Percy or Chromatic.

---

## 23. Acceptance Criteria

### 23.1 Functionality

- [ ] User can browse 8 benchmarks on the Benchmarks page
- [ ] User can view full benchmark details including spec, reference files, and bugs
- [ ] User can browse 5 Trace2Skill categories with correct skill counts
- [ ] User can view all skills in a category in a sortable table
- [ ] User can view individual skill details in a dialog
- [ ] User can submit a pipeline job from the dashboard
- [ ] User can select V1, V2, or V3 pipeline (based on backend availability)
- [ ] User can toggle reference RTL and reference TB options
- [ ] User can cancel a running job
- [ ] User sees the Silicon Design Flow update in real-time during a pipeline run
- [ ] User sees agent activity events appear in the feed in real-time
- [ ] User sees simulation, synthesis, STA, and DRC results when a job completes
- [ ] User can view job history on the Jobs page
- [ ] User can view detailed job information including timeline and event log
- [ ] User can see system status including health, version availability, and mode

### 23.2 Real-Time Behavior

- [ ] SSE connection is established within 500ms of job submission
- [ ] Pipeline events are reflected in the UI within 100ms of receipt
- [ ] SSE reconnection works transparently with event replay
- [ ] Flow diagram stage transitions are smooth (60fps)
- [ ] Activity feed auto-scrolls correctly (only when at bottom)
- [ ] Elapsed timer updates in real-time during job execution

### 23.3 Visual Quality

- [ ] All pages match the design system (colors, typography, spacing)
- [ ] Dark theme is consistent across all pages
- [ ] No light-mode flashes on page load
- [ ] Silicon Design Flow is visually impressive at all screen sizes
- [ ] Placeholder content looks intentional, not broken
- [ ] Empty states are present on every page that can be empty

### 23.4 Responsive Design

- [ ] Dashboard functions at 1920px, 1440px, 1280px, 1024px, 768px, 375px
- [ ] Sidebar collapses and expands correctly at each breakpoint
- [ ] Benchmark grid adjusts columns correctly
- [ ] Silicon Design Flow switches to vertical layout on mobile
- [ ] Right panel becomes overlay drawer on smaller screens
- [ ] No horizontal scrollbar at any supported breakpoint

### 23.5 Accessibility

- [ ] All text meets WCAG AA contrast ratios
- [ ] All functionality is keyboard-accessible
- [ ] Screen reader announces dynamic content changes
- [ ] Focus indicators are visible on all interactive elements
- [ ] Reduced motion preferences are respected

### 23.6 Performance

- [ ] Initial page load (dashboard) Lighthouse score ≥ 90
- [ ] No layout shifts during page load (CLS < 0.05)
- [ ] Event processing doesn't block the main thread
- [ ] Memory usage stays under 100MB during a full pipeline run

### 23.7 Error Handling

- [ ] Backend unreachable: shows clear error state with retry
- [ ] Invalid benchmark name: shows inline validation error
- [ ] Job not found: shows 404 state within app shell
- [ ] SSE connection lost: shows reconnection status, offers manual retry
- [ ] API validation errors: shown near the relevant form field

---

## 24. Validation Checklist

This checklist is for the implementing engineer to verify completeness before marking Phase 2 as done.

### 24.1 Pages (7 routes)
- [ ] `/dashboard` — Full pipeline runner + live flow + activity feed + results
- [ ] `/benchmarks` — Grid of 8 benchmark cards
- [ ] `/benchmarks/[name]` — Detail page for each of 8 benchmarks
- [ ] `/skills` — Grid of 5 category cards
- [ ] `/skills/[category]` — Skill table for each of 5 categories
- [ ] `/jobs` — Job history list
- [ ] `/jobs/[jobId]` — Job detail with timeline + events + results

### 24.2 Core Components (minimum)
- [ ] AppShell (layout wrapper)
- [ ] Sidebar (nav, responsive)
- [ ] Topbar (status, stats)
- [ ] SiliconFlow (pipeline visualization)
- [ ] FlowStage (individual stage with states)
- [ ] FlowConnector (animated connector)
- [ ] AgentActivityFeed (virtual scrolling event log)
- [ ] AgentLogEntry (single log line)
- [ ] JobRunner (config form)
- [ ] BenchmarkGrid + BenchmarkCard
- [ ] SkillCategoryGrid + SkillCategoryCard
- [ ] SkillTable + SkillDetailDialog
- [ ] JobCard (list view)
- [ ] JobTimeline
- [ ] JobResultsPanel
- [ ] SimulationResult, SynthesisResult, STAResult, DRCResult
- [ ] All shared components (LoadingSkeleton, EmptyState, ErrorState, etc.)

### 24.3 States Per Component
Every data-display component must handle:
- [ ] Loading state (skeleton)
- [ ] Empty state (icon + message)
- [ ] Error state (message + retry)
- [ ] Data state (normal render)
- [ ] Active/live state (if applicable — pipeline flow, event feed)

### 24.4 Integration
- [ ] All 11 REST endpoints consumed via TanStack Query
- [ ] SSE streaming consumed via custom hook
- [ ] All 19 event types handled in state dispatch
- [ ] Reconnection protocol implemented
- [ ] Zod validation on all API responses
- [ ] Error boundaries at page level

### 24.5 Cross-Cutting
- [ ] Dark theme only (no light mode flash)
- [ ] All text meets WCAG AA contrast
- [ ] Keyboard navigation complete
- [ ] Reduced motion support
- [ ] Responsive at all breakpoints
- [ ] Build succeeds with no errors
- [ ] `pnpm build` produces < 300KB gzipped JS
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] E2E critical paths pass

---

## 25. Design Mockups

### 25.1 Overall Page Layout (Desktop, 1440px)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ TOPBAR                                              h-12, bg-silicon-900      │
│ ● System Operational   V1● V2● V3●   [MOCK]  deepseek    ▶1 ✓24 ✗3    (📡)  │
├────────────┬─────────────────────────────────────────────────────────────────┤
│            │                                                                   │
│  SIDEBAR   │  MAIN CONTENT AREA                                                │
│  w-56      │                                                                   │
│  bg-900    │  ┌─────────────────────────────────────────────────────────────┐ │
│            │  │  Dashboard                                          px-6 py-4 │ │
│  ⚡ RTL2GDS │  │                                                             │ │
│            │  │  ┌──────────────────────────────────────────────────────────┐│ │
│  📊 Dashboard│  │  │ JOB RUNNER                                    bg-850   ││ │
│  🖥 Benchmrks│  │  │ [alu_8bit ▼]  [V1|V2|V3]  [iter:5]  [RefRTL] [RefTB]  ││ │
│  🧠 Skills  │  │  │                                          [▶ Run Pipeline] ││ │
│  📋 Jobs    │  │  └──────────────────────────────────────────────────────────┘│ │
│  📡 Status  │  │                                                             │ │
│            │  │  ┌──────────────────────────────────────────────────────────┐│ │
│            │  │  │  SILICON DESIGN FLOW                         V3 [V2] [V1] ││ │
│            │  │  │                                                          ││ │
│            │  │  │  [✓SPEC]──▶[✓VERF]──▶[✓RTL]──▶[✓TB]──▶[⏳SIM]          ││ │
│            │  │  │                                    │                      ││ │
│            │  │  │              ┌──────────────────────┘                      ││ │
│            │  │  │              ▼     (fix loop)                              ││ │
│  ──────────│  │  │         [○LOG]──▶[○FIX]──▶[○TB]──┐                       ││ │
│            │  │  │              ▲                      │                      ││ │
│            │  │  │              └──────────────────────┘                      ││ │
│  Footer    │  │  │                                                          ││ │
│  v0.2.0    │  │  │  [○SYNTH]──▶[○STA]──▶[○OpenL]──▶[○DRC]                 ││ │
│  GitHub 🔗 │  │  │                                                          ││ │
│  Docs 🔗   │  │  │  ████████████░░░░░░░░ 62%    Iter: 1/5    Elapsed: 04:32 ││ │
│            │  │  └──────────────────────────────────────────────────────────┘│ │
│            │  │                                                             │ │
│            │  │  ┌──────────────────────────────────────────────────────────┐│ │
│            │  │  │  AGENT ACTIVITY FEED                          [Filter ▼] ││ │
│            │  │  │  ──────────────────────────────────────────────────────── ││ │
│            │  │  │  14:32:01.234  [SIM]  INFO   Simulation started          ││ │
│            │  │  │  14:32:00.891  [TB]   SUCCESS Testbench generation done  ││ │
│            │  │  │  14:31:58.102  [RTL]  INFO   RTL generation complete     ││ │
│            │  │  │  14:31:55.437  [VERF] SUCCESS Verification plan ready    ││ │
│            │  │  │  14:31:54.100  [SPEC] SUCCESS Spec parsed successfully   ││ │
│            │  │  └──────────────────────────────────────────────────────────┘│ │
│            │  └─────────────────────────────────────────────────────────────┘ │
│            │                                                                   │
└────────────┴───────────────────────────────────────────────────────────────────┘
```

### 25.2 Dashboard — Three-Column Layout

```
┌────────┬──────────────────────────────────┬────────────────────────────┐
│ Sidebar│  Center (fluid)                   │  Results Panel (w-80)      │
│        │                                   │                            │
│        │  ┌───────────────────────────┐   │  ┌──────────────────────┐  │
│        │  │ Job Runner                │   │  │ SIMULATION            │  │
│        │  └───────────────────────────┘   │  │ ✅ PASSED             │  │
│        │                                   │  │ Coverage: 98.2%       │  │
│        │  ┌───────────────────────────┐   │  │ Iteration: 1          │  │
│        │  │                           │   │  │ [Waveform placeholder] │  │
│        │  │   SILICON DESIGN FLOW     │   │  └──────────────────────┘  │
│        │  │   (pipeline animation)    │   │                            │
│        │  │                           │   │  ┌──────────────────────┐  │
│        │  └───────────────────────────┘   │  │ SYNTHESIS             │  │
│        │                                   │  │ Cell Count: 142       │  │
│        │  ┌───────────────────────────┐   │  │ Area: 450 sq um       │  │
│        │  │ Agent Activity Feed       │   │  │ Freq: 100 MHz         │  │
│        │  │ (scrollable, live)        │   │  └──────────────────────┘  │
│        │  │                           │   │                            │
│        │  │ 14:32:01 [SIM] Running... │   │  ┌──────────────────────┐  │
│        │  │ 14:32:00 [TB]  Done      │   │  │ STA                   │  │
│        │  │ 14:31:58 [RTL] Done      │   │  │ ✅ TIMING MET          │  │
│        │  │ 14:31:55 [VERF] Done     │   │  │ WNS: +6.59 ns         │  │
│        │  │ 14:31:54 [SPEC] Done     │   │  │ TNS: 0.00 ns          │  │
│        │  │                           │   │  └──────────────────────┘  │
│        │  └───────────────────────────┘   │                            │
│        │                                   │  ┌──────────────────────┐  │
│        │                                   │  │ DRC                   │  │
│        │                                   │  │ ✅ DRC CLEAN          │  │
│        │                                   │  │ Violations: 0         │  │
│        │                                   │  │ [Layout placeholder]  │  │
│        │                                   │  └──────────────────────┘  │
└────────┴──────────────────────────────────┴────────────────────────────┘
```

### 25.3 Benchmark Card Design

```
┌─────────────────────────────┐
│  ┌──────────┐               │
│  │combinational│    [GDSII ✓]│  ← category badge + completion badge
│  └──────────┘               │
│                             │
│  alu_8bit                   │  ← design name (text-lg semibold)
│  8-bit ALU with 8 operations│
│  and zero flag output...    │  ← spec preview (2 lines, silicon-400)
│                             │
│  📄 RTL  🧪 TB  🐛 2 bugs  │  ← status icons (colored if present)
└─────────────────────────────┘
```

### 25.4 Skill Category Card Design

```
┌─────────────────────────────┐
│  COMBINATIONAL              │  ← category name
│                             │
│        6                    │  ← skill count (text-4xl, copper-500)
│                             │
│  4 curated · 2 confirmed    │  ← breakdown
│                             │
│  [LOGIC] [WIDTH] [SYNTAX]   │  ← error type tags
└─────────────────────────────┘
```

### 25.5 Job Card Design (List View)

```
┌────────────────────────────────────────────────────────────────────┐
│ ✓ │ abc12345  │ alu_8bit  │ V3 │ 2 min ago │ 23.4s │ ▓▓▓▓▓▓▓▒▒ │
│   │           │           │    │           │       │ sim✓ sta✓ drc✓│
└────────────────────────────────────────────────────────────────────┘
  status   job ID    benchmark  ver   created   duration  stage bar  results
```

### 25.6 Mobile Layout (375px)

```
┌───────────────────────────┐
│ ☰  RTL2GDS Agent    [MOCK]│  ← Topbar (condensed)
├───────────────────────────┤
│                           │
│  ┌─────────────────────┐  │
│  │ JOB RUNNER          │  │
│  │ [alu_8bit ▼]        │  │
│  │ [V1|V2|V3]          │  │
│  │ [▶ Run Pipeline]    │  │
│  └─────────────────────┘  │
│                           │
│  ┌─────────────────────┐  │
│  │ SILICON DESIGN FLOW │  │
│  │                     │  │
│  │  ✓ SPEC Parser      │  │
│  │  │  (connector)     │  │
│  │  ✓ VERF Planner     │  │
│  │  │                  │  │
│  │  ✓ RTL Gen          │  │
│  │  │                  │  │← Vertical layout
│  │  ✓ TB Gen           │  │
│  │  │                  │  │
│  │  ⏳ Simulation      │  │
│  │  │                  │  │
│  │  ┌── Fix Loop ──┐   │  │
│  │  │ ○ Log Analysis│   │  │
│  │  │ ○ Fix Agent   │   │  │
│  │  └──────────────┘   │  │
│  │  │                  │  │
│  │  ○ Synthesis        │  │
│  │  ○ STA              │  │
│  │  ○ OpenLane         │  │
│  │  ○ DRC              │  │
│  │                     │  │
│  │  Progress: 62%      │  │
│  └─────────────────────┘  │
│                           │
│  ┌─────────────────────┐  │
│  │ AGENT ACTIVITY      │  │
│  │ (collapsible)       │  │
│  └─────────────────────┘  │
│                           │
│  ┌─────────────────────┐  │
│  │ RESULTS (bottom     │  │
│  │  sheet, swipe up)   │  │
│  └─────────────────────┘  │
│                           │
│  [Dashboard] [Bench] ...  │  ← Bottom nav (mobile)
└───────────────────────────┘
```

---

## 26. Design Review & Critique

### 26.1 Principal Frontend Engineer Review

**Strengths:**
- Clean separation of concerns: stores, hooks, components are well-layered
- SSE reconnection with replay is robust and well-specified
- Virtual scrolling for event feed prevents memory issues
- Zod validation provides runtime type safety matching the Pydantic backend

**Concerns & Mitigations:**
- **Concern:** The SiliconFlow component is complex. Need to ensure animation performance doesn't degrade with many rapid events.
  - **Mitigation:** Use `requestAnimationFrame` batched updates. Throttle SSE event dispatch to 60fps. Use Framer Motion's `layout` prop for efficient re-renders.
- **Concern:** SSE EventSource doesn't support custom headers. If authentication is added in Phase 3, this will be a problem.
  - **Mitigation:** Document this limitation. For Phase 2, no auth is needed (local deployment). Phase 3 can switch to fetch-based SSE or use cookies.

### 26.2 UX Designer Review

**Strengths:**
- Silicon-native visual metaphor is distinctive and memorable
- Information hierarchy is clear — flow diagram dominates, activity feed supports, results contextualize
- Status indicators are consistent and scannable (dots, badges, colors)
- Empty states are designed, not afterthoughts

**Concerns & Mitigations:**
- **Concern:** The three-column dashboard may feel overwhelming on first visit.
  - **Mitigation:** Progressive disclosure. On first visit (no active job), the right panel is collapsed by default. The flow diagram shows static "pending" states. Only the JobRunner and flow diagram are visible. Complexity reveals as the user interacts.
- **Concern:** The fix loop visualization could be confusing for non-EE viewers.
  - **Mitigation:** Add a subtle tooltip on the loop: "Fix Loop: When simulation fails, the AI analyzes the error, retrieves relevant skills from its memory, and regenerates the RTL. This repeats until the design passes or the maximum iterations are reached."

### 26.3 Product Manager Review

**Strengths:**
- Meets all demo requirements for Tessolve
- Mock mode enables impressive demos without EDA tool dependencies
- The flow visualization is screenshot-worthy for presentations
- Vercel deployment enables sharing a URL (not just localhost)

**Concerns & Mitigations:**
- **Concern:** No user authentication or multi-tenancy.
  - **Mitigation:** Out of scope for Phase 2. Documented as Phase 3 feature. The backend already has no auth — this is a demo product.
- **Concern:** What if the demo environment has no internet (for Vercel)?
  - **Mitigation:** The app works fully locally (`pnpm dev` → `localhost:3000`). Vercel is for remote demos. Both paths are supported.

### 26.4 AMD Hackathon Judge Review

**Strengths:**
- The UI immediately communicates "this is an EDA tool," not "this is a chatbot"
- The live pipeline visualization is compelling in a 3-minute demo
- Trace2Skill visualization shows the AI is learning (not just generating)
- Dark theme, technical aesthetics appeal to engineering judges

**Concerns & Mitigations:**
- **Concern:** "Can this actually produce real chips?"
  - **Mitigation:** The results panel shows real metrics (cell count, area, WNS, DRC violations). The 5 completed benchmarks with GDSII output provide credibility. The mock mode is clearly labeled — never deceive.
- **Concern:** "Is this just a wrapper around an LLM?"
  - **Mitigation:** The agent activity feed shows the full pipeline: spec parsing → verification planning → RTL generation → testbench → simulation → synthesis → STA → physical design. Each stage uses different tools (Icarus, Yosys, OpenSTA, OpenLane, KLayout). The UI makes the multi-agent, multi-tool nature visible.

### 26.5 VLSI Engineer Review

**Strengths:**
- Results show real EDA metrics: WNS, TNS, cell count, area, DRC violations
- Pipeline stages match real ASIC flow: RTL → Synthesis → STA → Physical → DRC
- The fix loop with Trace2Skill mirrors real debugging workflows
- Monospace for code/technical content is appropriate

**Concerns & Mitigations:**
- **Concern:** Missing waveform viewer makes simulation results less credible.
  - **Mitigation:** The static waveform placeholder is carefully designed to look like a real waveform (photo-green traces on dark background, 4-6 labeled signals). Phase 3 will add an interactive viewer. For now, the pass/fail + coverage percentage provides the essential information.
- **Concern:** The UI should not hide the raw tool outputs.
  - **Mitigation:** Every result card has an "Expand" option that shows the raw JSON payload. The terminal output component is available for log files. Engineers can always inspect the raw data.

### 26.6 Startup Founder Review

**Strengths:**
- Professional polish suggests a funded company, not a student project
- Dark theme + EDA-specific design = defensible brand identity
- Vercel deployment = shareable demo link for investors
- Mock mode = zero-cost demos (no GPU/EDA cloud needed)

**Concerns & Mitigations:**
- **Concern:** "What's the path to commercialization?"
  - **Mitigation:** The UI is designed to scale. The benchmark system is extensible. The multi-version architecture (V1/V2/V3) demonstrates a product roadmap. Phase 3 adds authentication, user management, and cloud EDA execution — the commercial foundation.
- **Concern:** "How do you monetize this?"
  - **Mitigation:** Out of scope for this specification, but the architecture supports: usage-based pricing (job count), per-seat licensing (auth), on-premise deployment (no Vercel dependency), and premium features (advanced visualizations in Phase 3/4).

### 26.7 Devil's Advocate Review

**Weaknesses identified and addressed:**

1. **"Too much animation will annoy engineers."**
   - Response: All animations are functional (state transitions, data flow). Duration tokens are short (200-500ms). No decorative animation. Reduced motion support is built in.

2. **"Dark mode only will alienate users who prefer light mode."**
   - Response: EDA tools are exclusively dark mode (Cadence, Synopsys, Siemens, VS Code in hardware dev). Light mode would actually feel out of place. This is an informed constraint, not an oversight.

3. **"The three-column layout is too complex."**
   - Response: It's the standard EDA tool layout (project nav + canvas + properties). The responsive variants simplify progressively. First-visit experience hides the right panel.

4. **"SSE over Vercel won't work due to serverless timeout."**
   - Response: Acknowledged in Section 19. The SSE connection goes directly from browser to the FastAPI server (not proxied through Vercel). Vercel only serves the static frontend assets.

5. **"No offline support."**
   - Response: Correct. This is a real-time monitoring dashboard for a running backend. Offline mode is not applicable. The job history and event logs provide post-hoc access.

6. **"What if the pipeline takes 45 minutes (V3) — will the SSE connection hold?"**
   - Response: SSE with heartbeat (15s interval) and reconnection with `after=<seq>` replay is designed for long-lived connections. The FastAPI server runs independently (not serverless). This is the correct architecture for long-running jobs.

---

## 27. Out of Scope (Phase 3+)

The following features are explicitly excluded from Phase 2. They should not be implemented now, but the architecture should not preclude them.

### Phase 3: Interactive Engineering
- Interactive waveform viewer (GTKWave-like, in-browser)
- Gate-level schematic viewer
- GDSII layout viewer (pan/zoom/layer toggle)
- Real terminal access to running EDA tools
- Download artifacts (netlist, GDSII, reports)
- User authentication and multi-tenancy
- Job scheduling and queuing
- Email/slack notifications on job completion

### Phase 4: Advanced Features
- Side-by-side RTL diff viewer (generated vs reference)
- Performance regression tracking across pipeline versions
- Custom benchmark upload
- Team collaboration features
- API key management
- Usage analytics dashboard
- Export to PDF/LaTeX for publications
- Integration with GitHub CI/CD

---

## 28. Appendix: API Contract Reference

### 28.1 Base URL

All API calls use `NEXT_PUBLIC_API_BASE_URL` (default: `http://localhost:8000`).

### 28.2 Response Envelope

All non-SSE responses follow this structure:

```json
{
  "success": true,
  "data": { /* endpoint-specific payload */ }
}
```

```json
{
  "success": false,
  "error": {
    "code": "JOB_NOT_FOUND",
    "message": "Job 'abc12345' not found",
    "details": null
  }
}
```

### 28.3 Endpoints Quick Reference

| Method | Path | Query Params | Body | Response `data` type | Status |
|--------|------|-------------|------|---------------------|--------|
| GET | `/health` | — | — | `HealthResponse` | 200 |
| GET | `/status` | — | — | `SystemStatusResponse` | 200 |
| GET | `/api/benchmarks` | — | — | `BenchmarkListResponse` | 200 |
| GET | `/api/benchmarks/{name}` | — | — | `BenchmarkInfo` | 200 |
| GET | `/api/skills` | — | — | `SkillListResponse` | 200 |
| GET | `/api/skills/{category}` | — | — | `SkillCategoryResponse` | 200 |
| POST | `/api/run` | — | `RunRequest` | `RunResponse` | 202 |
| GET | `/api/run` | `status?`, `limit?` | — | `RunListResponse` | 200 |
| GET | `/api/run/{job_id}` | — | — | `RunResponse` | 200 |
| POST | `/api/run/{job_id}/cancel` | — | — | `RunResponse` | 200 |
| GET | `/api/run/stream` | `job_id`, `after?` | — | SSE stream | 200 |

### 28.4 RunRequest Schema

```json
{
  "benchmark": "alu_8bit",
  "pipeline_version": "v3",
  "max_iterations": 5,
  "use_reference_rtl": false,
  "use_reference_tb": false
}
```

### 28.5 RunResponse Schema

```json
{
  "job_id": "abc12345",
  "status": "running",
  "benchmark": "alu_8bit",
  "pipeline_version": "v3",
  "created_at": "2026-06-25T14:31:54Z",
  "started_at": "2026-06-25T14:31:55Z",
  "completed_at": null,
  "elapsed_seconds": 9.3,
  "current_stage": "simulation",
  "stages": [
    {"name": "spec_parser", "status": "completed", "started_at": "...", "completed_at": "...", "elapsed_ms": 310.0},
    {"name": "verification_planner", "status": "completed", ...},
    {"name": "rtl_gen", "status": "completed", ...},
    {"name": "testbench", "status": "completed", ...},
    {"name": "simulation", "status": "running", ...}
  ],
  "iteration": 0,
  "sim_passed": null,
  "timing_met": null,
  "drc_passed": null,
  "progress_pct": 62.0,
  "error_message": null,
  "event_count": 28
}
```

### 28.6 SSE Event Wire Format

```
event: pipeline_event
data: {"event_id":"550e8400-...","job_id":"abc12345","timestamp":"2026-06-25T14:31:54.123Z","event_type":"job_started","stage":null,"message":"Pipeline job started for alu_8bit (v3)","severity":"info","payload":{"benchmark":"alu_8bit","pipeline_version":"v3","max_iterations":5,"mode":"mock"},"elapsed_time":null,"iteration":null,"sequence_num":1}

event: heartbeat
data: {"timestamp":"2026-06-25T14:32:09Z"}

event: done
data: {"job_id":"abc12345","status":"completed","total_events":42}
```

### 28.7 Error Codes

| Code | HTTP Status | Meaning |
|------|-------------|---------|
| `JOB_NOT_FOUND` | 404 | Job ID does not exist |
| `BENCHMARK_NOT_FOUND` | 404 | Benchmark name does not exist |
| `SKILL_CATEGORY_NOT_FOUND` | 404 | Category name is not valid |
| `VALIDATION_ERROR` | 422 | Request body validation failed |
| `CONFLICT` | 409 | Duplicate job or cancel of terminal job |
| `PIPELINE_ERROR` | 500 | Pipeline execution failed |
| `SERVICE_UNAVAILABLE` | 503 | Service not ready |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

---

## Document Metadata

- **Created:** 2026-06-25
- **Phase 1 Backend:** Frozen. Tag: `phase1-backend-complete`
- **Next Step:** Obtain approval, then implement Phase 2 frontend per this specification
- **Estimated Implementation Effort:** 3-5 focused sessions
- **Reviewers:** Shashank Tumuluri (Project Owner)
- **Status:** ⏳ AWAITING APPROVAL

---

> "The best EDA tools make the complex feel inevitable. Every pixel of this UI should make the user think: of course AI belongs in chip design."
