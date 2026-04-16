---
title: "Promote UI Fixes — Layout, Tabs, Strategy Switcher"
created: 2026-03-26
status: draft
locked_by: null
repo: unified-trading-system-ui
branch: live-defi-rollout
completion_gates:
  code: "npm run build passes; visual check on /services/promote/* at 2K resolution"
  deployment: "N/A (UI only, mock data)"
  business: "User sign-off on visual"
repo_gates:
  - repo: unified-trading-system-ui
    gate: "build + visual check"
---

# Promote UI Fixes Plan

Based on user review of the current Pipeline page at 2K resolution.

---

## Task 1: Compact the Pipeline Summary Tiles

**Problem:** The 6 stage-count cards (row 1) + 5 metric cards (row 2) take up too much vertical space. Text is too small
to read at 2K.

**Current:** `pipeline-overview.tsx` lines 142-233

- Row 1: `grid-cols-2 sm:grid-cols-3 lg:grid-cols-6` — 6 cards, each with icon + label + count + description +
  conversion %
- Row 2: `grid-cols-2 lg:grid-cols-5` — 5 cards (In Pipeline, Avg Sharpe, Avg Dwell, Velocity, Approved 30d)

**Target:**

- **Merge into a single row of 11 compact cells** (or split into 2 semantic groups side-by-side: "Stage Counts" left,
  "Pipeline Metrics" right).
- Layout: `grid-cols-6 xl:grid-cols-11` at 2K. On smaller screens, wrap gracefully (e.g.
  `grid-cols-3 md:grid-cols-6 xl:grid-cols-11`).
- Each cell: **remove the Card wrapper** — use a simple `div` with a subtle left-border accent or bottom-border divider.
  No CardContent padding overhead.
- **Increase font sizes:**
  - Stage label: `text-xs` → `text-sm`
  - Count number: `text-2xl` → keep `text-2xl` (already large enough)
  - Description: `text-[10px]` → `text-xs`
  - Conversion %: `text-[9px]` → `text-xs`
  - Metric labels: `text-[10px]` → `text-sm`
- **Remove** the ChevronRight connectors between stage cards (they add clutter at small sizes).
- Keep the SLA breach banner below the tiles — it's useful.

**File:** `components/promote/pipeline-overview.tsx` (lines ~140-233)

**Responsive breakpoints (optimised for 2K = ~2560px viewport):**

| Viewport         | Layout                                                        |
| ---------------- | ------------------------------------------------------------- |
| < 640px (sm)     | 2 cols, tiles stack                                           |
| 640-1024 (md)    | 3 cols                                                        |
| 1024-1536 (lg)   | 6 cols (stage tiles on one row, metrics on next)              |
| 1536+ (2xl / 2K) | All 11 in one row, two groups separated by a vertical divider |

---

## Task 2: Remove the "Strategy Promotion" Title Banner

**Problem:** The header block with Rocket icon, title text ("Strategy Promotion / Review, assess..."), and badges ("2
awaiting approval", "AUM: $108M") wastes vertical space. The page identity is already clear from the nav tabs.

**Current:** `components/promote/promote-lifecycle-frame.tsx` lines 23-51

**Target:** Delete the entire `<div className="flex flex-col sm:flex-row ...">` block (lines 24-51). Keep the
`{!onPipeline && <PromoteStrategyContextBar />}` and `{children}` below it.

The resulting component becomes:

```tsx
export function PromoteLifecycleFrame({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() || "";
  const onPipeline = pathname === PROMOTE_PIPELINE_HREF || pathname === `${PROMOTE_PIPELINE_HREF}/`;

  return (
    <div className="h-full bg-background flex flex-col">
      <main className="flex-1 p-4 space-y-4 overflow-auto">
        {!onPipeline && <PromoteStrategyContextBar />}
        {children}
      </main>
    </div>
  );
}
```

Imports to remove: `Rocket`, `Badge`, `usePromoteLifecycleStore` (if no longer used after deletion — check).

**File:** `components/promote/promote-lifecycle-frame.tsx`

---

## Task 3: Remove Row-2 Legacy Tabs (PROMOTE_TABS)

**Problem:** The Row-2 tabs ("Strategy Promotion", "Review Queue", "Execution Analysis", "Risk Review", "Approval
Status") navigate to legacy pages outside `/services/promote/`. They duplicate what the 9 lifecycle sub-tabs already
cover.

**Current:**

- `PROMOTE_TABS` defined in `components/shell/service-tabs.tsx` lines 196-206
- Rendered by `app/(platform)/services/promote/layout.tsx` line 19: `<ServiceTabs tabs={PROMOTE_TABS} ...>`
- Links to:
  - `/services/promote/pipeline` (Strategy Promotion) — overlaps with Row-3 Pipeline sub-tab
  - `/services/research/strategy/candidates` (Review Queue) — legacy page, 669 lines
  - `/services/execution/tca` (Execution Analysis) — TCA page, 532 lines
  - `/services/trading/risk` (Risk Review) — risk dashboard, 2763 lines
  - `/services/research/strategy/handoff` (Approval Status) — handoff page, 584 lines

**Target:**

### 3a. Archive the 4 legacy pages (do NOT delete)

Move to `archive/` at the root of the UI repo, keeping folder structure intact:

```
archive/
├── services/
│   ├── research/strategy/candidates/page.tsx   (669 lines)
│   ├── research/strategy/handoff/page.tsx      (584 lines)
│   └── execution/tca/page.tsx                  (532 lines)
└── NOTE: trading/risk/page.tsx is NOT archived — it's a live trading page used by TRADING_TABS
```

**Important:** `/services/trading/risk` is referenced by `TRADING_TABS` (line 224:
`{ label: "Risk", href: "/services/trading/risk" }`) and `OBSERVE_TABS`. It is a live page — do NOT move it. Only move
the 3 pages that are exclusively accessed via the legacy PROMOTE_TABS links.

After archiving, update `PROMOTE_TABS` or remove references so no tabs point to dead routes.

### 3b. Review legacy pages for reusable concepts

| Legacy page                 | Useful concepts                                                                                                                                                                                                     | Target promote tab                                                                                                                                     |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `candidates/page.tsx`       | Workflow stage rail (Pending → Approved → Promoted); metrics strip (Sharpe, Sortino, hit rate, profit factor); resolved strategies table; review comment thread                                                     | **Pipeline** (stage rail inspiration); **Model Assessment** (metric snapshot)                                                                          |
| `execution/tca/page.tsx`    | Per-order TCA (slippage, market impact, timing, arrival price); benchmark delta cards (VWAP/TWAP/IS); cost breakdown in bps; slippage distribution histogram                                                        | **Execution Readiness** (cost analysis); **Paper Trading** (paper vs live execution quality)                                                           |
| `strategy/handoff/page.tsx` | `canPromote` gate logic; structured risk checklist (value vs limit, pass/fail); config diff table; champion baseline metrics; approval chain UI; deployment switches (shadow first, auto-rollback, gradual rollout) | **Governance** (approval chain + deployment switches); **Champion/Challenger** (config diff + champion metrics); **Risk & Stress** (checklist pattern) |

These concepts should be noted for future enhancement of the promote tabs, but are **not blocking** this task. The
immediate action is: archive files, remove the Row-2 tabs.

### 3c. Remove PROMOTE_TABS from layout

**Option (recommended):** Make `promote/layout.tsx` render **only** the EntitlementGate + ErrorBoundary +
WorkflowBridge, without any Row-2 `ServiceTabs`. The 9 lifecycle sub-tabs (rendered by `(lifecycle)/layout.tsx` →
`PromoteLifecycleSubTabs`) become the only tab row.

Updated `promote/layout.tsx`:

```tsx
"use client";

import type { ReactNode } from "react";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { EntitlementGate } from "@/components/platform/entitlement-gate";
import { PromoteWorkflowBridge } from "@/components/promote/promote-workflow-bridge";

export default function PromoteServiceLayout({ children }: { children: ReactNode }) {
  return (
    <EntitlementGate entitlement="execution-basic" serviceName="Strategy Promotion">
      <ErrorBoundary>
        <PromoteWorkflowBridge>{children}</PromoteWorkflowBridge>
      </ErrorBoundary>
    </EntitlementGate>
  );
}
```

Remove `PROMOTE_TABS` export from `service-tabs.tsx` (or keep it but stop importing it in the layout). Clean up the
`PROMOTE_PIPELINE_HREF` import from `service-tabs.tsx` if `PROMOTE_TABS` was the only consumer.

**Files:**

- `app/(platform)/services/promote/layout.tsx`
- `components/shell/service-tabs.tsx` (remove or comment out PROMOTE_TABS)
- Archive: `app/(platform)/services/research/strategy/candidates/page.tsx` →
  `archive/services/research/strategy/candidates/page.tsx`
- Archive: `app/(platform)/services/research/strategy/handoff/page.tsx` →
  `archive/services/research/strategy/handoff/page.tsx`
- Archive: `app/(platform)/services/execution/tca/page.tsx` → `archive/services/execution/tca/page.tsx`

---

## Task 4: Add Strategy Switcher Dropdown to Non-Pipeline Pages

**Problem:** Once you select a strategy from Pipeline and navigate to a stage tab (e.g. Data Validation), you can't
switch to another strategy without going back to Pipeline.

**Current:** `promote-strategy-context-bar.tsx` shows: `Pipeline > {strategy name} v{version}` + stage stepper dots. No
way to change strategy.

**Target:** Add a dropdown/combobox to `promote-strategy-context-bar.tsx` that lets you switch between strategies
without leaving the current tab.

**Design:**

```
[Pipeline ›] [BTC Funding Arb v3 ▾] ───── [●─●─●─○─○─○] stage stepper
                    ↓ dropdown
              ┌─────────────────────────────────┐
              │ 🔍 Search strategies...          │
              ├─────────────────────────────────┤
              │ BTC Funding Arb v3    Crypto  ✓ │
              │ ETH Basis Carry v1.1  Crypto    │
              │ Cross-Exchange MM v1  Crypto    │
              │ GBP/USD Mean Rev v1   FX        │
              │ Equity Momentum L/S   Equities  │
              │ ...                              │
              └─────────────────────────────────┘
```

**Implementation:**

- Use Shadcn `Popover` + `Command` (combobox pattern) from the UI primitives.
- Trigger: the strategy name + version badge becomes a clickable button with a chevron-down icon.
- Content: searchable list of all candidates from the store (`usePromoteLifecycleStore`).
- Each item shows: name, version, asset class badge, current stage badge.
- On select: call `setSelectedId(id)` on the store. The page re-renders with the new strategy's data. **Do NOT
  navigate** — stay on the same tab/route.
- Currently selected strategy gets a checkmark.

**File:** `components/promote/promote-strategy-context-bar.tsx`

**Dependencies:** `@/components/ui/popover`, `@/components/ui/command` (both should already exist as Shadcn primitives —
verify).

---

## Task 5: Increase Font Sizes Globally Across Promote Pages

**Problem:** Text at `text-[9px]`, `text-[10px]`, `text-[11px]` is barely readable at 2K resolution.

**Target minimum sizes:**

| Current          | Target           | Where used                                   |
| ---------------- | ---------------- | -------------------------------------------- |
| `text-[9px]`     | `text-xs` (12px) | Conv %, SLA days, descriptions, footnotes    |
| `text-[10px]`    | `text-xs` (12px) | Badges, filter labels, table cells, metadata |
| `text-[11px]`    | `text-sm` (14px) | Stage card labels                            |
| `text-xs` (12px) | `text-sm` (14px) | Table headers, section labels                |

**Files affected (grep for `text-\[9px\]`, `text-\[10px\]`, `text-\[11px\]`):**

- `components/promote/pipeline-overview.tsx` — heaviest user
- `components/promote/promote-lifecycle-frame.tsx` — badges (if not deleted by Task 2)
- `components/promote/promote-strategy-context-bar.tsx` — version badge
- `components/promote/promote-workflow-actions.tsx` — button labels
- `components/promote/helpers.tsx` — if any formatting helpers produce small text
- All `*-tab.tsx` files under `components/promote/` — scan each

**Approach:** Global find-and-replace within `components/promote/`:

1. `text-[9px]` → `text-xs`
2. `text-[10px]` → `text-xs`
3. `text-[11px]` → `text-sm`

Then visually verify nothing looks oversized. The table in pipeline-overview may need column width adjustments after
font bump.

---

## Execution Order

| Order | Task                                             | Effort | Dependencies                                |
| ----- | ------------------------------------------------ | ------ | ------------------------------------------- |
| 1     | Task 2: Remove title banner                      | S      | None                                        |
| 2     | Task 3: Remove Row-2 legacy tabs + archive pages | M      | None                                        |
| 3     | Task 5: Font size bump                           | S      | None (but easier to verify after Tasks 1-2) |
| 4     | Task 1: Compact pipeline tiles                   | M      | Task 5 (font sizes affect layout)           |
| 5     | Task 4: Strategy switcher dropdown               | M      | None                                        |

Tasks 1-3 can be parallelised across agents. Task 4 is independent. Task 5 (fonts) should go before Task 1 (tiles) since
font sizes affect tile dimensions.

---

## Files Summary

| Action         | File                                                                |
| -------------- | ------------------------------------------------------------------- |
| EDIT           | `components/promote/pipeline-overview.tsx`                          |
| EDIT           | `components/promote/promote-lifecycle-frame.tsx`                    |
| EDIT           | `components/promote/promote-strategy-context-bar.tsx`               |
| EDIT           | `app/(platform)/services/promote/layout.tsx`                        |
| EDIT           | `components/shell/service-tabs.tsx`                                 |
| EDIT           | All `components/promote/*-tab.tsx` (font sizes)                     |
| MOVE → archive | `app/(platform)/services/research/strategy/candidates/page.tsx`     |
| MOVE → archive | `app/(platform)/services/research/strategy/handoff/page.tsx`        |
| MOVE → archive | `app/(platform)/services/execution/tca/page.tsx`                    |
| DO NOT TOUCH   | `app/(platform)/services/trading/risk/page.tsx` (live trading page) |
| VERIFY         | `components/ui/popover.tsx`, `components/ui/command.tsx` exist      |

---

## Out of Scope (noted for future)

- Mock data migration from `components/promote/` to `lib/mocks/fixtures/` (P18 from prior plan)
- Integrating concepts from archived legacy pages into promote tabs
- Additional UI changes the user mentioned they want to discuss after these 5 tasks
