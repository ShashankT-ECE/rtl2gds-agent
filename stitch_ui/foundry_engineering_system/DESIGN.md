---
name: Foundry Engineering System
colors:
  surface: '#fbf8ff'
  surface-dim: '#d9d9e7'
  surface-bright: '#fbf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f2ff'
  surface-container: '#ededfb'
  surface-container-high: '#e7e7f5'
  surface-container-highest: '#e1e1ef'
  on-surface: '#191b25'
  on-surface-variant: '#434656'
  inverse-surface: '#2e303a'
  inverse-on-surface: '#f0effe'
  outline: '#737688'
  outline-variant: '#c3c5d9'
  surface-tint: '#004ced'
  primary: '#003ec7'
  on-primary: '#ffffff'
  primary-container: '#0052ff'
  on-primary-container: '#dfe3ff'
  inverse-primary: '#b7c4ff'
  secondary: '#565e74'
  on-secondary: '#ffffff'
  secondary-container: '#dae2fd'
  on-secondary-container: '#5c647a'
  tertiary: '#952200'
  on-tertiary: '#ffffff'
  tertiary-container: '#bf3003'
  on-tertiary-container: '#ffddd5'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dde1ff'
  primary-fixed-dim: '#b7c4ff'
  on-primary-fixed: '#001452'
  on-primary-fixed-variant: '#0038b6'
  secondary-fixed: '#dae2fd'
  secondary-fixed-dim: '#bec6e0'
  on-secondary-fixed: '#131b2e'
  on-secondary-fixed-variant: '#3f465c'
  tertiary-fixed: '#ffdbd2'
  tertiary-fixed-dim: '#ffb4a1'
  on-tertiary-fixed: '#3c0800'
  on-tertiary-fixed-variant: '#891e00'
  background: '#fbf8ff'
  on-background: '#191b25'
  surface-variant: '#e1e1ef'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '600'
    lineHeight: 38px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 26px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  code-md:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '450'
    lineHeight: 20px
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '450'
    lineHeight: 16px
  label-caps:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  container-margin: 24px
  gutter: 16px
  density-md: 12px
  density-sm: 8px
  density-xs: 4px
---

## Brand & Style

The design system is engineered for high-stakes electronic design automation, where precision, reliability, and information density are paramount. The aesthetic is rooted in **Modern Corporate Minimalism** with a heavy influence from developer-centric tools like GitHub and Vercel. 

The system prioritizes functional clarity over decorative flair. It avoids trendy blurs or neon aesthetics in favor of a "Foundry" feel: industrial, robust, and mathematically precise. The UI should evoke the feeling of a high-end physical laboratory—clean, well-organized, and built to withstand complex workflows. Success is measured by how quickly an engineer can parse a dense schematic or log file without visual fatigue.

Key principles:
- **Precision over Decoration:** Every line and pixel must serve a functional purpose.
- **High Density:** Optimized for expert users who require maximum data visibility on a single screen.
- **Tactile Logic:** Using subtle borders and tonal shifts to define hierarchy rather than heavy shadows.

## Colors

The palette is anchored in a sophisticated range of Slate and Zinc grays to provide a neutral "workbench" for engineering data. 

- **Primary (Foundry Blue):** A concentrated, professional blue used sparingly for primary actions and active states. It should feel authoritative, not playful.
- **Accents:** Functional colors (Green, Amber, Crimson) are strictly reserved for status indicators, violations, and system health. They use high-chroma values to ensure immediate recognition against the neutral background.
- **Surfaces:** The system defaults to a clean `light` mode. Backgrounds utilize very light grays (`#F8FAFC`) to reduce stark contrast glare, while white (`#FFFFFF`) is reserved for elevated cards and input fields.
- **Borders:** A consistent `#E2E8F0` or `#CBD5E1` is used for structural definition, ensuring sections are distinct without adding visual weight.

## Typography

This design system uses a dual-font strategy to balance readability with technical precision.

1.  **Inter:** Used for all UI chrome, navigation, and standard data entry. It is chosen for its exceptional legibility at small sizes and its neutral, modern tone.
2.  **JetBrains Mono:** Used for all "engineering data"—logs, coordinates, hardware metrics, and code snippets. The increased character spacing and distinct glyphs prevent errors in reading complex strings of text.

**Scaling & Hierarchy:**
- Headlines are kept tight and bold to create clear section anchoring.
- Body text is optimized at 14px for standard density and 13px for high-density sidebars.
- `label-caps` is used for metadata headers and table column titles to provide structural contrast without increasing font size.

## Layout & Spacing

The layout philosophy follows a **strict 4px grid system** to ensure mathematical alignment across all components. 

- **Grid:** A 12-column fluid grid is used for dashboard views, but the core work area (the EDA canvas/editor) uses a "No Grid" contextual layout with fixed-width sidebars (usually 280px or 320px).
- **Density:** This is a high-density system. Vertical padding in lists and tables should default to `8px` (`density-sm`) to maximize the amount of information visible on-screen.
- **Breakpoints:** 
    - **Desktop (1440px+):** Full multi-pane view (Left Navigation, Center Canvas, Right Properties).
    - **Tablet (1024px):** Sidebars become collapsible drawers.
    - **Mobile:** Not a primary target for engineering tasks; views reflow to single-column "Monitoring Only" modes with simplified metrics.

## Elevation & Depth

Depth is conveyed through **Tonal Layering and Low-Contrast Outlines** rather than traditional shadows. This maintains a "flat" engineering feel that doesn't distract from technical drawings.

- **Level 0 (Background):** `#F8FAFC` — The base canvas.
- **Level 1 (Cards/Panels):** `#FFFFFF` with a `1px` border of `#E2E8F0`.
- **Level 2 (Popovers/Modals):** `#FFFFFF` with a subtle, tight shadow (`0 4px 6px -1px rgb(0 0 0 / 0.1)`) and a slightly darker border `#CBD5E1`.

**Focus States:** Use a `2px` Foundry Blue ring with a `2px` white offset to ensure the active element is unmistakable in a dense UI.

## Shapes

The design system uses a **Soft** shape language (`0.25rem` or `4px` base radius). 

- **Small Radius (4px):** Standard for buttons, input fields, and small tags. This provides a modern feel without looking "bubbly" or consumer-grade.
- **Medium Radius (8px):** Used for main content cards and modals to create a clear container hierarchy.
- **Sharp (0px):** Used for the EDA canvas elements and status bars that span the full width of the viewport to emphasize their industrial nature.

## Components

- **Buttons:** Primary buttons use a solid Foundry Blue background with white text. Secondary buttons use a white background with a Slate-300 border. No gradients; use subtle state shifts (e.g., Background darken by 5% on hover).
- **Data Tables:** High-density rows (32px height). Column headers use `label-caps`. Cell text uses `body-sm` or `code-sm` depending on data type. Borders are horizontal only; no vertical dividers between columns unless comparing specific metrics.
- **Status Grids:** Small 8x8px square indicators (Engineered Green/Amber/Crimson) used to show status across large arrays. Use a tooltip for detail on hover.
- **Pipeline Indicators:** Horizontal tracks with circular nodes. Completed steps are solid blue; active steps use a blue pulse border; pending steps are Slate-200.
- **Input Fields:** Inset appearance with a 1px border. On focus, the border changes to Foundry Blue. Use JetBrains Mono for inputs involving coordinates or numerical values.
- **Cards:** White background, 1px Slate-200 border, 8px corner radius. Header sections within cards should have a subtle bottom border.
- **Icons:** 16px or 20px stroke-based icons. Use a consistent 1.5px or 2px stroke weight. Avoid filled icons unless indicating an "Active" or "Selected" toggle state.