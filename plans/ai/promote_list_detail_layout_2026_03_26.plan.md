---
title: "Promote — List/Detail Split Layout (ML Training Pattern)"
created: 2026-03-26
status: draft
locked_by: null
repo: unified-trading-system-ui
branch: live-defi-rollout
completion_gates:
  code: "npm run build passes; all 9 promote routes render in split layout"
  deployment: "N/A (UI only, mock data)"
  business: "User sign-off on layout"
repo_gates:
  - repo: unified-trading-system-ui
    gate: "build + visual check"
---

# Promote — List/Detail Split Layout

## Problem

1. **Strategy switching requires returning to Pipeline** — every time you want to look at a different strategy, you navigate back to `/services/promote/pipeline`, select, then get sent to the strategy's current stage tab. This is slow and disorienting.

2. **Most stage tabs are sparse** — Data Validation, Execution Readiness, Paper Trading, Capital Allocation, Feature Stability, etc. each have a small amount of content but stretch full-width across the screen. Bad space utilisation at 2K.

3. **Only Model Assessment and Governance are data-dense** — these two tabs have multiple sub-panels and genuinely use the width.

## Solution

Adopt the **list/detail split layout** used by `ml/training/page.tsx`:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Row-1: Lifecycle nav  (Acquire > Research > Promote > Trading ...) │
├─────────────────────────────────────────────────────────────────────┤
│  Row-3: Sub-tabs (Pipeline | Data | Model | Risk | Exec | ...)     │
├────────────────────┬────────────────────────────────────────────────┤
│  LEFT PANEL (1/3)  │  RIGHT PANEL (2/3)                            │
│                    │                                                │
│  Filter chips:     │  [Stage tab content for selected strategy]     │
│  [All] [Risk&Str]  │                                                │
│  [Governance] ...  │  ┌── Strategy Name v1.2 ── stage stepper ──┐  │
│                    │  │                                          │  │
│  Strategy cards:   │  │  (tab content rendered here)             │  │
│  ┌──────────────┐  │  │                                          │  │
│  │ BTC Arb v3   │  │  │                                          │  │
│  │ Crypto │ 75% │  │  │                                          │  │
│  │ Risk&Stress  │  │  │                                          │  │
│  ├──────────────┤  │  │                                          │  │
│  │ ETH Basis    │  │  │                                          │  │
│  │ Crypto │ 40% │  │  │                                          │  │
│  │ Model Assmt  │  │  │                                          │  │
│  ├──────────────┤  │  │                                          │  │
│  │ ...          │  │  │                                          │  │
│  └──────────────┘  │  └──────────────────────────────────────────┘  │
└────────────────────┴────────────────────────────────────────────────┘
```

### Key differences from current architecture

| Aspect | Current | New |
|--------|---------|-----|
| Strategy list | Full pipeline page at `/services/promote/pipeline` | Always-visible left panel on every tab |
| Strategy switching | Navigate to Pipeline → click → redirected to stage tab | Click strategy in left panel → right panel updates |
| Tab content width | Full viewport width | 2/3 viewport (detail panel) |
| Pipeline route | Separate page with summary tiles + filters + table | Left panel IS the strategy list; summary tiles move to top of detail panel (or a dedicated Pipeline tab) |
| Context bar | Shows above tab content with strategy name + stepper | Moves into the detail panel header |

### Pipeline tab specifically

When the **Pipeline** sub-tab is active, the right panel shows:
- The compact summary tiles (from Task 1 of prior plan — already done)
- The strategy table with full columns (Sharpe, Max DD, Stage, SLA, Progress, etc.)
- Essentially what `pipeline-overview.tsx` renders today, but inside the 2/3 detail area

When **any other sub-tab** is active, the right panel shows:
- Strategy context bar (name + version + stage stepper)
- The stage-specific tab content

The left panel is **always the same** regardless of which sub-tab is active — it's the strategy list with filters.

---

## Architecture

### New component: `promote-split-layout.tsx`

This is the core layout wrapper that all promote pages share. Lives in `components/promote/`.

```tsx
// components/promote/promote-split-layout.tsx
"use client";

export function PromoteSplitLayout({ children }: { children: React.ReactNode }) {
  // grid-cols-1 on mobile, grid-cols-[340px_1fr] on lg+
  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-[340px_1fr] gap-0 overflow-hidden">
        {/* Left: strategy list panel (always visible) */}
        <PromoteStrategyListPanel />
        {/* Right: tab content (children from route) */}
        <div className="flex-1 overflow-auto p-4 space-y-4 border-l border-border">
          {children}
        </div>
      </div>
    </div>
  );
}
```

### New component: `promote-strategy-list-panel.tsx`

Extracted from `pipeline-overview.tsx`. Contains:
- Status filter chips (All, by stage, by asset class)
- Scrollable list of strategy cards
- Each card shows: name, version, asset class, current stage badge, progress bar, SLA indicator
- Click selects strategy + stays on current route (updates store's `selectedId`)
- Active strategy is visually highlighted

Filters to include (from current Pipeline filters):
- Asset class dropdown
- Stage filter (stage chips, like the ML training page's Running/Queued/Completed/Failed chips)
- Archetype dropdown (or remove if too many — could go behind a "More filters" popover)

### Changes to existing files

| File | Change |
|------|--------|
| `(lifecycle)/layout.tsx` | Wrap children in `<PromoteSplitLayout>` instead of just rendering `<PromoteLifecycleSubTabs />` + `{children}`. Sub-tabs render above the grid. |
| `promote-lifecycle-frame.tsx` | Remove or simplify — the context bar logic moves into the split layout's right panel header. |
| `promote-pipeline-page.tsx` | The Pipeline tab's right panel shows summary tiles + the strategy table (reuse from `pipeline-overview.tsx`). The left panel already handles selection. |
| `pipeline-overview.tsx` | Refactor: extract strategy list into `promote-strategy-list-panel.tsx`. What remains is the summary tiles + table (rendered in Pipeline tab's right panel). |
| `promote-strategy-context-bar.tsx` | Simplify — remove the strategy switcher dropdown (just added in prior task) since the left panel now handles switching. Keep the strategy name + stage stepper for the right panel header. |
| `promote-lifecycle-stage-page.tsx` | Remove `<PromoteLifecycleFrame>` wrapper (it's redundant with the split layout). Directly render the no-strategy-selected state or the tab content. |
| All `(lifecycle)/*/page.tsx` route files | No change — they already render thin wrappers around tab components. |
| `promote-lifecycle-sub-tabs.tsx` | No change — still renders Row-3 sub-tabs above the split layout. |

### Updated `(lifecycle)/layout.tsx`

```tsx
"use client";

import type { ReactNode } from "react";
import { PromoteLifecycleSubTabs } from "@/components/promote/promote-lifecycle-sub-tabs";
import { PromoteSplitLayout } from "@/components/promote/promote-split-layout";

export default function PromoteLifecycleSectionLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <>
      <PromoteLifecycleSubTabs />
      <PromoteSplitLayout>{children}</PromoteSplitLayout>
    </>
  );
}
```

---

## Left Panel Strategy Card Design

Each strategy card in the left panel:

```
┌──────────────────────────────────┐
│ BTC Funding Arb v3          ▸   │
│ funding-rate-arb · Crypto       │
│ ████████████░░░░  75%  Risk&Str │
│ SLA: 3d/7d · On track          │
└──────────────────────────────────┘
```

- Name + version (bold)
- Archetype + asset class (muted)
- Progress bar + percentage + current stage badge
- SLA status

Active card: `bg-primary/5 border-l-2 border-primary`

---

## Responsive Behavior

| Viewport | Behavior |
|----------|----------|
| < 1024px (mobile/tablet) | Single column — left panel collapses into a dropdown/sheet at the top. Sub-tabs + tab content take full width. |
| 1024-1536px (lg) | Split: left panel 340px fixed, right panel fills remaining space. |
| 1536px+ (2K/xl) | Same split, but left panel could expand slightly to ~380px. Right panel has plenty of room. |

On mobile, the left panel becomes a `Sheet` (slide-in drawer) or a collapsible section above the content — triggered by a "Select Strategy" button.

---

## Task Breakdown

| # | Task | File(s) | Effort |
|---|------|---------|--------|
| 1 | Create `promote-strategy-list-panel.tsx` — extract strategy list from `pipeline-overview.tsx` | NEW: `components/promote/promote-strategy-list-panel.tsx`, EDIT: `pipeline-overview.tsx` | M |
| 2 | Create `promote-split-layout.tsx` — the grid wrapper | NEW: `components/promote/promote-split-layout.tsx` | S |
| 3 | Update `(lifecycle)/layout.tsx` to use `PromoteSplitLayout` | EDIT: `app/(platform)/services/promote/(lifecycle)/layout.tsx` | S |
| 4 | Update `promote-lifecycle-frame.tsx` — remove wrapper, keep context bar in detail header | EDIT: `components/promote/promote-lifecycle-frame.tsx` | S |
| 5 | Update `promote-lifecycle-stage-page.tsx` — remove PromoteLifecycleFrame wrapper | EDIT: `components/promote/promote-lifecycle-stage-page.tsx` | S |
| 6 | Simplify `promote-strategy-context-bar.tsx` — remove combobox switcher (left panel handles it), keep name + stepper | EDIT: `components/promote/promote-strategy-context-bar.tsx` | S |
| 7 | Update `promote-pipeline-page.tsx` — Pipeline tab now shows tiles + table in right panel (list is already in left panel) | EDIT: `components/promote/promote-pipeline-page.tsx`, EDIT: `pipeline-overview.tsx` | M |
| 8 | Mobile responsiveness — Sheet fallback for left panel on < lg | EDIT: `promote-split-layout.tsx` | S |
| 9 | Visual verification at 2K | Browser | S |

### Execution order

Tasks 1-2 first (create new components), then 3-7 in parallel (wiring), then 8 (mobile), then 9 (verify).

---

## What Does NOT Change

- The 9 sub-tab routes and their `page.tsx` files — unchanged
- The tab content components (`*-tab.tsx`) — unchanged
- The Zustand store — unchanged (still manages `selectedId` + `candidates`)
- The workflow actions — unchanged
- `promote.config.ts`, `promote-lifecycle-sub-tabs.tsx` — unchanged
- `promote/layout.tsx` (the outer layout with EntitlementGate) — unchanged
