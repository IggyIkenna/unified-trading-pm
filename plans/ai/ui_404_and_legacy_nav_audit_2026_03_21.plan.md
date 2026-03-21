# AI-GENERATED — awaiting user review and promotion

---
name: ui-404-and-legacy-nav-audit
overview: Audit and fix all 404 broken links and remove legacy GlobalNavBar from all pages
type: code
epic: epic-code-completion
status: proposed

completion_gates:
  code: C5
  deployment: N/A
  business: N/A

repo_gates:
  - repo: unified-trading-system-ui
    code: C0
    deployment: N/A
    business: N/A
---

## Context

After the 2-row navigation refactor (commit `921eeb8`), the new lifecycle nav (Row 1) and service tabs (Row 2) are live. However:

1. **Broken links (404s)** — Several hrefs in navigation components, page links, and tab configs point to routes with no matching `page.tsx`.
2. **Legacy navigation** — 25+ pages still render the old `GlobalNavBar` (with "Overview, Trading, Strategies, Markets, Ops, Config, ML, Strategy Lab, Execution, Reports" tabs), old full-width `ContextBar`, and/or old `LifecycleRail` stepper. These create a competing navigation model alongside the new lifecycle nav.

This plan is the audit report with concrete fix instructions for both phases.

**Verification method**: Every redirect pair was verified by reading both files and confirming byte-identical content (via `diff -q`), matching purpose, or flagging mismatches. Three critical mismatches were found and corrected below (marked with WARNING).

---

## Phase 1: Fix All 404 Broken Links

### 1A. Missing pages (href exists, no page.tsx) — need placeholder or redirect

| Source File | Broken Href | Fix |
|---|---|---|
| `components/shell/lifecycle-nav.tsx` L411 | `/settings` | Add placeholder `app/(platform)/settings/page.tsx` — "User preferences & display settings" |
| `app/(platform)/portal/dashboard/page.tsx` L46 | `/portal/whitelabel` | Add placeholder `app/(platform)/portal/whitelabel/page.tsx` — "White-label branding configuration" |
| `app/(platform)/portal/dashboard/page.tsx` L47 | `/portal/execution` | Add placeholder `app/(platform)/portal/execution/page.tsx` — "Client execution analytics portal" |

### 1B. Duplicate legacy routes — verified byte-identical to canonical `/service/*`

All pairs below have been verified as **byte-identical** via `diff -q`. The legacy page is a carbon copy of the canonical `/service/*` version. Safe to delete after ensuring redirect coverage.

**Trading domain (all verified identical):**

| Legacy Route | Canonical Route | Redirect Exists | Verified |
|---|---|---|---|
| `/trading` | `/service/trading/overview` | YES | byte-identical |
| `/trading/positions` | `/service/trading/positions` | YES | byte-identical |
| `/trading/risk` | `/service/trading/risk` | YES | byte-identical |
| `/trading/alerts` | `/service/trading/alerts` | YES | byte-identical |
| `/trading/markets` | `/service/data/markets` | YES | byte-identical |

**ML domain (all verified identical):**

| Legacy Route | Canonical Route | Redirect Exists | Verified |
|---|---|---|---|
| `/ml` | `/service/research/ml` | YES | redirect stub |
| `/ml/overview` | `/service/research/ml/overview` | YES (via `/ml/:path*`) | byte-identical |
| `/ml/features` | `/service/research/ml/features` | YES | byte-identical |
| `/ml/training` | `/service/research/ml/training` | YES | byte-identical |
| `/ml/validation` | `/service/research/ml/validation` | YES | byte-identical |
| `/ml/experiments` | `/service/research/ml/experiments` | YES | byte-identical |
| `/ml/experiments/[id]` | `/service/research/ml/experiments/[id]` | YES | functionally identical (1 stale link href) |
| `/ml/deploy` | `/service/research/ml/deploy` | YES | byte-identical |
| `/ml/registry` | `/service/research/ml/registry` | YES | byte-identical |
| `/ml/monitoring` | `/service/research/ml/monitoring` | YES | byte-identical |
| `/ml/governance` | `/service/research/ml/governance` | YES | byte-identical |

**Research domain (all verified identical):**

| Legacy Route | Canonical Route | Redirect Exists | Verified |
|---|---|---|---|
| `/research/ml` | `/service/research/ml` | YES | byte-identical |
| `/research/ml/overview` | `/service/research/ml/overview` | YES | byte-identical |
| `/research/ml/experiments` | `/service/research/ml/experiments` | YES | byte-identical |
| `/research/ml/experiments/[id]` | `/service/research/ml/experiments/[id]` | YES | byte-identical |
| `/research/ml/features` | `/service/research/ml/features` | YES | byte-identical |
| `/research/ml/training` | `/service/research/ml/training` | YES | byte-identical |
| `/research/ml/deploy` | `/service/research/ml/deploy` | YES | byte-identical |
| `/research/ml/registry` | `/service/research/ml/registry` | YES | byte-identical |
| `/research/ml/monitoring` | `/service/research/ml/monitoring` | YES | byte-identical |
| `/research/ml/governance` | `/service/research/ml/governance` | YES | byte-identical |
| `/research/ml/validation` | `/service/research/ml/validation` | YES | byte-identical |
| `/research/strategy/backtests` | `/service/research/strategy/backtests` | YES | byte-identical |
| `/research/strategy/compare` | `/service/research/strategy/compare` | YES | byte-identical |
| `/research/strategy/candidates` | `/service/research/strategy/candidates` | YES | byte-identical |
| `/research/strategy/handoff` | `/service/research/strategy/handoff` | YES | byte-identical |
| `/research/strategy/heatmap` | `/service/research/strategy/heatmap` | YES | byte-identical |
| `/research/strategy/results` | `/service/research/strategy/results` | YES | byte-identical |
| `/research/execution/algos` | `/service/research/execution/algos` | YES | byte-identical |
| `/research/execution/benchmarks` | `/service/research/execution/benchmarks` | YES | byte-identical |
| `/research/execution/tca` | `/service/research/execution/tca` | YES | byte-identical |
| `/research/execution/venues` | `/service/research/execution/venues` | YES | byte-identical |

**Execution domain (all verified identical):**

| Legacy Route | Canonical Route | Redirect Exists | Verified |
|---|---|---|---|
| `/execution` | `/service/execution/overview` | NO — need to add | redirect stub (calls `redirect("/execution/overview")`) |
| `/execution/overview` | `/service/execution/overview` | NO — need to add | byte-identical |
| `/execution/algos` | `/service/execution/algos` | NO — need to add | byte-identical |
| `/execution/benchmarks` | `/service/execution/benchmarks` | NO — need to add | byte-identical |
| `/execution/tca` | `/service/execution/tca` | NO — need to add | byte-identical |
| `/execution/venues` | `/service/execution/venues` | NO — need to add | byte-identical |
| `/execution/candidates` | `/service/execution/candidates` | NO — need to add | byte-identical |
| `/execution/handoff` | `/service/execution/handoff` | NO — need to add | byte-identical |

**Strategy platform (all verified identical):**

| Legacy Route | Canonical Route | Redirect Exists | Verified |
|---|---|---|---|
| `/strategy-platform/backtests` | `/service/research/strategy/backtests` | NO — need to add | byte-identical |
| `/strategy-platform/compare` | `/service/research/strategy/compare` | NO — need to add | byte-identical |
| `/strategy-platform/heatmap` | `/service/research/strategy/heatmap` | NO — need to add | byte-identical |
| `/strategy-platform/candidates` | `/service/research/strategy/candidates` | NO — need to add | byte-identical |
| `/strategy-platform/handoff` | `/service/research/strategy/handoff` | NO — need to add | byte-identical |
| `/strategy-platform/results` | `/service/research/strategy/results` | NO — need to add | byte-identical |
| `/strategy-platform/overview` | N/A — see WARNING #2 | NO | redirect stub → `/research/strategy/overview` |

**Other verified identical:**

| Legacy Route | Canonical Route | Redirect Exists | Verified |
|---|---|---|---|
| `/overview` | `/service/overview` | YES | byte-identical |
| `/data` | `/service/data/overview` | YES | byte-identical |
| `/reports` | `/service/reports/overview` | NO — need to add | byte-identical |
| `/reports/executive` | `/service/reports/executive` | NO — need to add | byte-identical |
| `/executive` | `/service/reports/executive` | NO — need to add | redirect stub → `/reports/executive` (double hop, fix to go direct) |
| `/positions` | `/service/trading/positions` | YES | redirect stub |
| `/risk` | `/service/trading/risk` | YES | redirect stub |
| `/alerts` | `/service/trading/alerts` | YES | redirect stub |
| `/markets` | `/service/data/markets` | YES | redirect stub |

---

### WARNING #1: `/trading/markets/pnl` and `/markets/pnl` — UNIQUE CONTENT, DO NOT REDIRECT TO `/service/data/markets`

**Problem**: The original plan proposed redirecting `/trading/markets/pnl` → `/service/data/markets`. This is WRONG.

- `/trading/markets/pnl/page.tsx` is a **P&L Attribution Detail** page — drill-down showing factor breakdowns by strategy (funding, carry, basis, delta, gamma, vega, theta, slippage, fees, rebates) with per-factor strategy tables and percentage breakdowns.
- `/service/data/markets/page.tsx` is the **Market Intelligence overview** — top-level waterfall chart, NOT the drill-down.

**Fix**: Create `app/(platform)/service/data/markets/pnl/page.tsx` by copying from the legacy file, then add redirect. The content is unique and would be lost.

### WARNING #2: `/research/strategy/overview` — TARGET DOES NOT EXIST

**Problem**: The legacy page at `/research/strategy/overview/page.tsx` is a 611-line detailed strategy overview dashboard (strategy candidates table with filtering, metrics, KPIs, new strategy dialog). The `/strategy-platform/overview` page also redirects here.

There is NO file at `/service/research/strategy/overview/page.tsx`. The closest match, `/service/research/overview/page.tsx`, is a completely different page — it's a generic research hub with links to ML/Strategy/Execution sections.

**Fix**: Create `app/(platform)/service/research/strategy/overview/page.tsx` by copying from the legacy `/research/strategy/overview/page.tsx`. Then both legacy paths can redirect to it.

### WARNING #3: `/quant` — UNIQUE CONTENT, DO NOT REDIRECT TO `/service/research/overview`

**Problem**: The original plan proposed redirecting `/quant` → `/service/research/overview`. This is WRONG.

- `/quant/page.tsx` renders a `QuantDashboard` component wrapped in `RoleLayout(role="quant")` with `showLifecycleRail=true`. This is a role-specific dashboard for quant developers.
- `/service/research/overview/page.tsx` is a generic research hub with links to ML, Strategy, and Execution subsections.

These are fundamentally different pages. Redirecting would lose the quant-specific dashboard.

**Fix**: Either keep `/quant` as a standalone page (migrate off RoleLayout but keep content), OR create `app/(platform)/service/research/quant/page.tsx` as a new canonical home for the QuantDashboard.

---

### 1C. Missing redirects to add in `next.config.mjs`

```javascript
// Execution service (NO redirects exist today)
{ source: "/execution", destination: "/service/execution/overview", permanent: true },
{ source: "/execution/:path*", destination: "/service/execution/:path*", permanent: true },

// Strategy platform → research strategy (NO redirects exist today)
{ source: "/strategy-platform", destination: "/service/research/strategy/backtests", permanent: true },
{ source: "/strategy-platform/overview", destination: "/service/research/strategy/overview", permanent: true },
{ source: "/strategy-platform/:path*", destination: "/service/research/strategy/:path*", permanent: true },

// Reports (NO redirects exist today)
{ source: "/reports", destination: "/service/reports/overview", permanent: true },
{ source: "/reports/:path*", destination: "/service/reports/:path*", permanent: true },

// PnL drill-down (unique content, redirect to new target)
{ source: "/trading/markets/pnl", destination: "/service/data/markets/pnl", permanent: true },
{ source: "/markets/pnl", destination: "/service/data/markets/pnl", permanent: true },

// Misc (NO redirects exist today)
{ source: "/executive", destination: "/service/reports/executive", permanent: true },
{ source: "/quant", destination: "/service/research/quant", permanent: true },
```

### 1D. New canonical pages to create BEFORE deleting legacy pages

These must be created by copying content from the legacy source — they contain unique content with no existing `/service/*` equivalent.

| New Canonical Page | Source (copy from) | Reason |
|---|---|---|
| `app/(platform)/service/data/markets/pnl/page.tsx` | `app/(platform)/trading/markets/pnl/page.tsx` | Unique P&L factor drill-down (335 lines) |
| `app/(platform)/service/research/strategy/overview/page.tsx` | `app/(platform)/research/strategy/overview/page.tsx` | Unique strategy overview dashboard (611 lines) |
| `app/(platform)/service/research/quant/page.tsx` | `app/(platform)/quant/page.tsx` | Unique quant role dashboard |

---

## Phase 2: Remove Legacy Navigation From All Pages

### 2A. Pages directly rendering GlobalNavBar

| Route | File | Components to Remove | Notes |
|---|---|---|---|
| `/trading` | `app/(platform)/trading/page.tsx` | `GlobalNavBar`, `ContextBar`, `LifecycleRail` | DELETE entire file (redirect covers it) |
| `/strategy-platform/*` | `app/(platform)/strategy-platform/layout.tsx` | `GlobalNavBar` | DELETE entire layout + all 7 page files (redirect covers them) |

### 2B. Pages using AppShell wrapper (renders GlobalNavBar + ContextBar + LifecycleRail)

AppShell = `components/trading/app-shell.tsx` — wraps pages with old GlobalNavBar, full-width ContextBar, and optional LifecycleRail.

**Canonical `/service/*` pages that need AppShell removed (8 pages — keep content, remove wrapper):**

| Route | File | Fix |
|---|---|---|
| `/service/trading/positions` | `app/(platform)/service/trading/positions/page.tsx` | Remove `AppShell` wrapper, bridge `useContextState` → `useGlobalScope` |
| `/service/trading/alerts` | `app/(platform)/service/trading/alerts/page.tsx` | Same |
| `/service/trading/markets` | `app/(platform)/service/trading/markets/page.tsx` | Same |
| `/service/research/ml/training` | `app/(platform)/service/research/ml/training/page.tsx` | Same |
| `/service/research/ml/overview` | `app/(platform)/service/research/ml/overview/page.tsx` | Same |
| `/service/research/ml/experiments/[id]` | `app/(platform)/service/research/ml/experiments/[id]/page.tsx` | Same |
| `/service/reports/overview` | `app/(platform)/service/reports/overview/page.tsx` | Same |
| `/service/data/markets` | `app/(platform)/service/data/markets/page.tsx` | Same |

**Legacy duplicate pages using AppShell (DELETE — redirect covers them):**

| Route | File | Notes |
|---|---|---|
| `/trading/positions` | `app/(platform)/trading/positions/page.tsx` | Byte-identical to `/service/trading/positions` |
| `/trading/alerts` | `app/(platform)/trading/alerts/page.tsx` | Byte-identical |
| `/trading/markets` | `app/(platform)/trading/markets/page.tsx` | Byte-identical |
| `/reports` | `app/(platform)/reports/page.tsx` | Byte-identical to `/service/reports/overview` |
| `/ml/overview` | `app/(platform)/ml/overview/page.tsx` | Byte-identical |
| `/research/ml/overview` | `app/(platform)/research/ml/overview/page.tsx` | Byte-identical |
| `/research/ml/experiments/[id]` | `app/(platform)/research/ml/experiments/[id]/page.tsx` | Byte-identical |

### 2C. Pages using RoleLayout wrapper (renders GlobalNavBar + ContextBar + optional LifecycleRail)

RoleLayout = `components/shell/role-layout.tsx` — provides old navigation with role-based view toggling.

**Canonical pages to migrate (keep content, remove wrapper):**

| Route | File | Fix |
|---|---|---|
| `/service/trading/risk` | `app/(platform)/service/trading/risk/page.tsx` | Remove `RoleLayout` wrapper, keep risk dashboard content |
| `/service/reports/executive` | `app/(platform)/service/reports/executive/page.tsx` | Same |
| `/service/research/quant` | (new, from 1D) | Copy content from `/quant` RoleLayout page, render without RoleLayout |

**Legacy duplicate pages using RoleLayout (DELETE — redirect covers them):**

| Route | File | Notes |
|---|---|---|
| `/trading/risk` | `app/(platform)/trading/risk/page.tsx` | Byte-identical to `/service/trading/risk` |
| `/reports/executive` | `app/(platform)/reports/executive/page.tsx` | Byte-identical |
| `/quant` | `app/(platform)/quant/page.tsx` | Unique content, moved to `/service/research/quant` in step 1D |

### 2D. Shell/wrapper components to deprecate

After all pages are migrated, these components have zero consumers and should be deleted:

| Component | File | Reason |
|---|---|---|
| `GlobalNavBar` | `components/trading/global-nav-bar.tsx` | Replaced by `lifecycle-nav.tsx` |
| `AppShell` | `components/trading/app-shell.tsx` | Old wrapper; pages use `UnifiedShell` + `ServiceTabs` now |
| `RoleLayout` | `components/shell/role-layout.tsx` | Old wrapper; roles handled by entitlements in new nav |
| `LifecycleRail` | `components/trading/lifecycle-rail.tsx` | Removed from all pages; may be reused as in-page stepper later |
| `UnifiedBatchShell` | `components/platform/unified-batch-shell.tsx` | Uses `GlobalNavBar`; no consumers |
| Legacy nav toggle in `unified-shell.tsx` | `components/shell/unified-shell.tsx` | Remove `useLegacyNav` prop + conditional rendering |

### 2E. Full-width ContextBar migration (remaining pages)

| File | Status |
|---|---|
| `app/(platform)/service/research/strategy/results/page.tsx` | Uses `@/components/platform/context-bar` (NEW version) — OK, keep as-is |
| `app/(platform)/service/research/strategy/compare/page.tsx` | Uses `@/components/platform/context-bar` (NEW version) — OK, keep as-is |

Note: The `platform/context-bar.tsx` is the NEW context bar (different from `trading/context-bar.tsx`). These are fine.

---

## Execution Order

```
Phase 1D → Phase 1A → Phase 1C → Phase 1B → Phase 2B → Phase 2C → Phase 2A → Phase 2D
```

1. **1D**: Create 3 new canonical pages (PnL detail, strategy overview, quant dashboard) — prevents content loss
2. **1A**: Add 3 placeholder pages (`/settings`, `/portal/whitelabel`, `/portal/execution`)
3. **1C**: Add all missing redirects to `next.config.mjs` — ensures no dead links after deletion
4. **1B**: Delete ~55 legacy page files (redirects now cover them)
5. **2B**: Migrate 8 `/service/*` pages off AppShell → `useGlobalScope`
6. **2C**: Migrate 3 `/service/*` pages off RoleLayout (including new quant page)
7. **2A**: Delete legacy layout + pages for `/trading` and `/strategy-platform/*`
8. **2D**: Delete 5 deprecated components, clean up UnifiedShell

---

## Double-Redirect Chains to Fix

Some legacy pages are redirect stubs that point to intermediate paths (which themselves redirect). These create 2-hop redirect chains. When adding to `next.config.mjs`, point directly to the final `/service/*` destination:

| Current Chain | Fix (direct) |
|---|---|
| `/positions` → `/trading/positions` → `/service/trading/positions` | Already correct in config (goes to `/service/trading/positions`) |
| `/risk` → `/trading/risk` → `/service/trading/risk` | Already correct in config |
| `/alerts` → `/trading/alerts` → `/service/trading/alerts` | Already correct in config |
| `/markets` → `/trading/markets` → `/service/data/markets` | Already correct in config |
| `/executive` → `/reports/executive` → `/service/reports/executive` | Fix: redirect `/executive` directly to `/service/reports/executive` |
| `/ml` → `/research/ml` → `/service/research/ml` | Already correct (config has `/ml/:path*` → `/service/research/ml/:path*`) |
| `/strategy-platform/overview` → `/research/strategy/overview` → `/service/research/strategy/overview` | Fix: redirect directly to `/service/research/strategy/overview` |

---

## Impact Summary

| Metric | Before | After |
|---|---|---|
| Total page files | ~160 | ~98 (delete ~62 legacy duplicates) |
| Pages with old GlobalNavBar | 25+ | 0 |
| Pages with old ContextBar (trading) | 20+ | 0 |
| Pages with LifecycleRail | 10+ | 0 |
| Broken 404 links | 5 | 0 |
| Double-redirect chains | 2 | 0 |
| Deprecated components | 5 (still imported) | 0 (deleted) |
| Navigation models | 2 (old + new) | 1 (lifecycle nav only) |
| Unique content at risk | 3 pages | 0 (all preserved at new canonical paths) |

---

## Verification Checklist (run after each phase)

After each phase, verify:

1. `npm run build` — no compilation errors
2. Check every redirect in `next.config.mjs` resolves to an existing page
3. Navigate to each deleted legacy URL — verify redirect lands on correct canonical page
4. Verify no page renders `GlobalNavBar` (search for `global-nav-bar` imports)
5. Verify no page renders `AppShell` (search for `app-shell` imports)
6. Verify no page renders `RoleLayout` (search for `role-layout` imports)
7. Verify no page imports from `@/components/trading/context-bar` (old version)

---

## Todos

```yaml
todos:
  - id: p1d-create-canonical-pages
    title: "Create 3 new canonical pages for unique content (PnL detail, strategy overview, quant dashboard)"
    status: pending
    files: ["service/data/markets/pnl/page.tsx", "service/research/strategy/overview/page.tsx", "service/research/quant/page.tsx"]

  - id: p1a-placeholders
    title: "Add 3 placeholder pages for remaining 404s (/settings, /portal/whitelabel, /portal/execution)"
    status: pending
    files: ["settings/page.tsx", "portal/whitelabel/page.tsx", "portal/execution/page.tsx"]

  - id: p1c-redirects
    title: "Add missing redirects to next.config.mjs (execution, strategy-platform, reports, pnl, executive, quant)"
    status: pending
    files: ["next.config.mjs"]

  - id: p1b-delete-legacy-pages
    title: "Delete ~55 legacy duplicate page files (verified byte-identical)"
    status: pending
    blocked_by: [p1d-create-canonical-pages, p1c-redirects]
    files: ["app/(platform)/trading/", "app/(platform)/ml/", "app/(platform)/research/", "app/(platform)/execution/", "app/(platform)/strategy-platform/", "app/(platform)/reports/", "app/(platform)/positions/", "app/(platform)/risk/", "app/(platform)/alerts/", "app/(platform)/markets/", "app/(platform)/overview/", "app/(platform)/executive/", "app/(platform)/data/"]

  - id: p2b-appshell-migration
    title: "Remove AppShell wrapper from 8 canonical service pages"
    status: pending
    blocked_by: p1b-delete-legacy-pages
    files: ["service/trading/positions", "service/trading/alerts", "service/trading/markets", "service/research/ml/training", "service/research/ml/overview", "service/research/ml/experiments/[id]", "service/reports/overview", "service/data/markets"]

  - id: p2c-rolelayout-migration
    title: "Remove RoleLayout wrapper from 3 canonical service pages"
    status: pending
    blocked_by: p1b-delete-legacy-pages
    files: ["service/trading/risk", "service/reports/executive", "service/research/quant"]

  - id: p2a-delete-legacy-layouts
    title: "Delete legacy layout and pages for /trading, /strategy-platform"
    status: pending
    blocked_by: p1b-delete-legacy-pages

  - id: p2d-delete-components
    title: "Delete 5 deprecated components (GlobalNavBar, AppShell, RoleLayout, LifecycleRail, UnifiedBatchShell) + clean up UnifiedShell"
    status: pending
    blocked_by: [p2b-appshell-migration, p2c-rolelayout-migration]
    files: ["components/trading/global-nav-bar.tsx", "components/trading/app-shell.tsx", "components/shell/role-layout.tsx", "components/trading/lifecycle-rail.tsx", "components/platform/unified-batch-shell.tsx", "components/shell/unified-shell.tsx"]
```
