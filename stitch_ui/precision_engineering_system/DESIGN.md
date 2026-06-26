---
name: Precision Engineering System
colors:
  surface: '#131315'
  surface-dim: '#131315'
  surface-bright: '#39393b'
  surface-container-lowest: '#0e0e10'
  surface-container-low: '#1c1b1d'
  surface-container: '#201f22'
  surface-container-high: '#2a2a2c'
  surface-container-highest: '#353437'
  on-surface: '#e5e1e4'
  on-surface-variant: '#c3c5d9'
  inverse-surface: '#e5e1e4'
  inverse-on-surface: '#313032'
  outline: '#8d90a2'
  outline-variant: '#434656'
  surface-tint: '#b7c4ff'
  primary: '#b7c4ff'
  on-primary: '#002682'
  primary-container: '#0052ff'
  on-primary-container: '#dfe3ff'
  inverse-primary: '#004ced'
  secondary: '#c6c5cf'
  on-secondary: '#2f3038'
  secondary-container: '#4a4b53'
  on-secondary-container: '#bcbbc5'
  tertiary: '#ffb4a1'
  on-tertiary: '#611300'
  tertiary-container: '#bf3003'
  on-tertiary-container: '#ffddd5'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#dde1ff'
  primary-fixed-dim: '#b7c4ff'
  on-primary-fixed: '#001452'
  on-primary-fixed-variant: '#0038b6'
  secondary-fixed: '#e3e1ec'
  secondary-fixed-dim: '#c6c5cf'
  on-secondary-fixed: '#1a1b22'
  on-secondary-fixed-variant: '#46464e'
  tertiary-fixed: '#ffdbd2'
  tertiary-fixed-dim: '#ffb4a1'
  on-tertiary-fixed: '#3c0800'
  on-tertiary-fixed-variant: '#891e00'
  background: '#131315'
  on-background: '#e5e1e4'
  surface-variant: '#353437'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
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
  gutter: 16px
  margin-safe: 24px
  panel-sidebar: 280px
  panel-inspector: 320px
---

## Brand & Style

This design system is engineered for VLSI automation, prioritizing high-density information architecture and technical precision. The aesthetic is inspired by high-end developer tools, merging the structural clarity of GitHub with the streamlined, dark-mode focused sophistication of Linear. 

The emotional response should be one of "Expert Utility"—the interface stays out of the way of the engineer's workflow while providing absolute confidence in data accuracy. The design style is **Modern Corporate** with a heavy emphasis on **Minimalism** and **Low-contrast outlines**. It avoids decorative flourishes in favor of structural integrity, utilizing crisp borders, monospaced data visualization, and subtle micro-interactions to signify system intelligence.

## Colors

The palette is rooted in a deep, professional grayscale using Zinc and Slate scales to create clear hierarchical planes. 

- **Primary:** Industrial Blue (#0052ff) is used sparingly for primary actions, active states, and focus indicators to maintain a high-signal environment.
- **Surface:** The background uses a true-dark neutral (#09090b), with container levels rising through subtle shifts in the Zinc scale.
- **Accents:** Success, Warning, and Error colors are saturated to ensure visibility against dark surfaces, used primarily for status badges, node states, and terminal alerts.
- **Borders:** A consistent "low-contrast" border strategy using `Zinc-800` for default states and `Zinc-700` for hover/active states.

## Typography

Typography is split between **Inter** for structural UI and **JetBrains Mono** for all engineering data, coordinates, and terminal output. 

- **Density:** Font sizes are slightly smaller than standard consumer apps (13px/14px for body) to facilitate the high-density requirements of VLSI tooling.
- **Hierarchy:** Use `label-caps` for section headers within sidebars and inspector panels. 
- **Tabular Figures:** Ensure JetBrains Mono is used for all numerical data in grids to maintain vertical alignment across rows.

## Layout & Spacing

This design system utilizes a **Fixed Grid** approach for toolbars and sidebars, with a **Fluid** central viewport for schematics or data grids.

- **Rhythm:** A 4px baseline grid ensures tight, predictable spacing.
- **Panels:** Standardized widths for sidebars (280px) and inspectors (320px) provide a consistent workspace.
- **Density Settings:** Components should prioritize `compact` vertical padding (e.g., 4px-8px for list items) to maximize visible data on a single screen.
- **Responsive:** On smaller screens, sidebars collapse into icons rather than reflowing, preserving the engineer's mental map of the workspace.

## Elevation & Depth

Depth is achieved through **Tonal Layering** and **Low-contrast outlines** rather than traditional shadows.

- **Level 0 (Background):** #09090b (Zinc-950).
- **Level 1 (Cards/Panels):** #18181b (Zinc-900) with a 1px border of #27272a (Zinc-800).
- **Level 2 (Popovers/Modals):** #27272a (Zinc-800) with a subtle 8px blur shadow (0% opacity, effectively just a border-light).
- **Active State:** Elements being dragged or actively focused should use a subtle glow effect using the primary color at 10% opacity.

## Shapes

The shape language is "Technical-Soft." A consistent **4px (0.25rem)** radius is used for all interactive elements like buttons, input fields, and chips. 

- **Outer Containers:** Larger cards use a 6px radius.
- **Internal Elements:** Nested items (like tags inside a card) use a 2px radius to maintain visual harmony.
- **Strictness:** Do not use pill-shaped elements; maintain the rectangular structural integrity of the grid.

## Components

### Buttons
- **Primary:** Solid #0052ff with white text. No gradient.
- **Secondary:** Transparent background with Zinc-800 border.
- **Ghost:** No border, appears only on hover with a Zinc-800 background.

### Data Grids
- **Header:** Zinc-900 background, 1px bottom border, JetBrains Mono labels.
- **Cells:** High-density (28px height), vertical borders enabled to separate complex data columns.

### Terminal & Code
- **Background:** Pure black (#000000).
- **Text:** JetBrains Mono. Success/Error colors used for log levels.
- **Scrollbars:** Minimalist, 4px wide, Zinc-700, appearing only on hover.

### Cards
- 1px solid border (#27272a). No shadow.
- Header section separated by a 1px horizontal line.

### Loading States
- Use **Subtle Shimmers** (Linear Gradients moving from Zinc-900 to Zinc-800) for skeleton loaders. Avoid spinning icons for complex data views.

### Input Fields
- Dark background, Zinc-800 border. On focus: 1px Blue-600 border with no outer glow. Monospaced font for numerical inputs.