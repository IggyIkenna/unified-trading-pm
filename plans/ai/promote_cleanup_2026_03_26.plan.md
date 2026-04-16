---
title: "Promote Feature Cleanup — Align Stashed Code with Design"
created: 2026-03-26
status: draft
locked_by: null
repo: unified-trading-system-ui
branch: live-defi-rollout
completion_gates:
  code: "npm run build passes; no lint errors; all promote routes render"
  deployment: "N/A (UI only, mock data)"
  business: "User sign-off on structure"
repo_gates:
  - repo: unified-trading-system-ui
    gate: "build + visual check on /services/promote/*"
---

# Promote Feature Cleanup Plan

## Context

The stashed code (now restored) built a **multi-route architecture** for promote:

- `/services/promote` → redirect to `/services/promote/pipeline`
- `/services/promote/pipeline`, `/services/promote/data-validation`, ... `/services/promote/governance` — 9 separate
  `page.tsx` files under a `(lifecycle)` route group
- A `promote/layout.tsx` (Row-2 PROMOTE_TABS) + `(lifecycle)/layout.tsx` (Row-3 sub-tabs)
- A Zustand store (`promote-lifecycle-store.ts`) shared across routes
- 7 extra routing-infrastructure components in `components/promote/`

The **design doc** (§9) describes exactly this structure and it is internally consistent. However, the original
conversation indicated the user wanted the **simpler single-URL tab approach** (all tabs on `/services/promote`,
client-side tab switching). The stashed code went further than requested.

**This plan documents every problem found and the decision needed, so the user can pick the direction before any code
changes.**

---

## Decision Required: Multi-Route vs Single-URL

### Option A: Keep Multi-Route (current stashed code)

**What already works:**

- 12 route files under `app/(platform)/services/promote/` — all wired
- `promote/layout.tsx` renders Row-2 PROMOTE_TABS + EntitlementGate + ErrorBoundary + PromoteWorkflowBridge
- `(lifecycle)/layout.tsx` renders Row-3 sub-tabs (PromoteLifecycleSubTabs) with stage-gating
- Zustand store holds candidates + selectedId across route transitions
- promote-strategy-context-bar.tsx renders a stepper breadcrumb with Links to each stage route
- Stage gating: locked tabs are visible but not clickable (navDisabled)
- Each stage page is thin: just wraps the matching `*-tab.tsx` component

**Pros:**

- Bookmarkable URLs per stage (`/services/promote/data-validation`)
- Browser back/forward works naturally between stages
- Follows same pattern as other services (data, research, trading) which use route-per-tab
- Design doc §9 matches this structure exactly

**Cons:**

- More files (12 route files + 7 routing-infra components)
- Zustand store required to preserve selectedId across navigations
- More complex than client-side tabs for what is fundamentally a single-strategy review flow

### Option B: Collapse to Single-URL Tabs

**What it means:**

- Delete all `(lifecycle)/*.tsx` route files (9 pages + 1 layout)
- Delete `promote/layout.tsx` and `promote/page.tsx` (redirect)
- Create `promote/page.tsx` (server entry) + `promote-page-client.tsx` ("use client", Shadcn Tabs)
- Delete 7 routing-infra components (promote-lifecycle-frame, promote-lifecycle-stage-page, promote-lifecycle-sub-tabs,
  promote-pipeline-page, promote-stage-access, promote-strategy-context-bar, promote-workflow-bridge)
- Simplify or delete `promote.config.ts` (no stage HREFs needed)
- Simplify or delete `promote-lifecycle-store.ts` (state is local to client component)

**Pros:**

- Fewer files, simpler mental model
- No Zustand store needed for cross-route state
- Tab content lives entirely in components/promote/\*.tsx (already exists)

**Cons:**

- No bookmarkable URLs per stage
- Browser back doesn't navigate between stages
- Doesn't match the pattern used by every other service in the app

---

## Problems Found (regardless of which option)

### P1. Trading overview — promote button already removed

The stashed code already removed the promote button and modal from `trading/overview/page.tsx`. No promote references
remain. **Status: clean.**

### P2. `components/trading/promote-flow-modal.tsx` deleted, moved to `components/promote/`

The stash renames `components/trading/promote-flow-modal.tsx` → `components/promote/promote-flow-modal.tsx`. The
`strategies/grid/page.tsx` and `strategies/[id]/page.tsx` imports are updated to
`@/components/promote/promote-flow-modal`. **Status: clean.**

### P3. `service-tabs.tsx` — `navDisabled` prop added

The stash added `navDisabled?: boolean` and `navDisabledTitle?: string` to `ServiceTab` interface, plus rendering logic
for disabled tabs (visible but not clickable, with Lock icon). This is used by `PromoteLifecycleSubTabs` for
stage-gating.

- **If Option A:** Keep — it's used.
- **If Option B:** The props can stay (harmless), but nothing will use them. Clean up is optional.

### P4. `service-tabs.tsx` — `PROMOTE_TABS` import from config

Line 9 imports `PROMOTE_PIPELINE_HREF` from promote.config. The `PROMOTE_TABS` array uses it for the "Strategy
Promotion" tab href.

- **If Option A:** Keep.
- **If Option B:** `PROMOTE_TABS` should point to `/services/promote` instead of `/services/promote/pipeline`. The
  promote.config.ts simplification would need to happen first.

### P5. `lifecycle-nav.tsx` — promote primaryHref override

Lines 207-210: special-cases `nav.stage === "promote"` to link to `/services/promote` instead of using the first
dropdown item. This works for both options since `/services/promote` exists in both (it either redirects to pipeline or
serves the single page).

- **Both options:** Keep as-is.

### P6. `lifecycle-mapping.ts` — promote route entry

Line 317-325: maps `/services/promote/pipeline` as the promote stage entry. The `stageServiceMap` (line 707-720) lists
two promote items: "Strategy Promotion" at `/services/promote/pipeline` and "Candidates (Legacy)" at
`/services/research/strategy/candidates`.

- **If Option A:** Keep — `/services/promote/pipeline` is a real route.
- **If Option B:** Change to `/services/promote` (single URL).

### P7. `lib/config/services/promote.config.ts`

Defines `PROMOTE_LIFECYCLE_BASE`, `PROMOTE_PIPELINE_HREF`, `STAGE_HREFS`, `promoteHrefForStage()`, and
`PROMOTE_LIFECYCLE_NAV` array.

- **If Option A:** Keep — all used by route pages, sub-tabs, context bar.
- **If Option B:** Drastically simplify — only need `PROMOTE_LIFECYCLE_BASE = "/services/promote"`. Delete stage hrefs
  and nav definitions.

### P8. `lib/stores/promote-lifecycle-store.ts`

Zustand store with `candidates`, `selectedId`, `recordWorkflow`, `reset()`. Used by 7 routing-infra components.

- **If Option A:** Keep — essential for cross-route state.
- **If Option B:** Could be replaced with `useState` in the client component, OR keep for demo reset consistency (the
  store's `reset()` is called by `resetDemo()`). Keeping the store is harmless and follows the Zustand convention.

### P9. `lib/reset-demo.ts`

Line 4 imports and line 14 calls `usePromoteLifecycleStore.getState().reset()`.

- **Both options:** Keep — demo reset should clear promote state regardless of routing approach.

### P10. `lib/config/index.ts`

Re-exports all promote.config symbols (PROMOTE_LIFECYCLE_BASE, PROMOTE_PIPELINE_HREF, etc.).

- **If Option A:** Keep.
- **If Option B:** Simplify to only export what remains after promote.config simplification.

### P11. `next.config.mjs`

The stash added `turbopackFileSystemCacheForBuild: true` to `experimental`. No promote-specific redirects were added.
`/services/promote` → pipeline redirect is done in `page.tsx` (server-side `redirect()`), not in next.config.

- **Both options:** No change needed.

### P12. `app/globals.css`

The stash added 3 lines (checked: line count went from 394 to 397). Need to verify what was added — likely a minor style
tweak.

- **Both options:** Verify and keep if valid.

### P13. `__tests__/lib/stores/stores.test.ts`

Added test for promote-lifecycle-store `reset()`.

- **If Option A:** Keep.
- **If Option B:** Keep if store is kept; delete if store is deleted.

### P14. `.cursorrules` — architecture diagram

Currently shows `services/promote/` and `components/promote/`. This is correct for both options.

- **Both options:** No change needed.

### P15. `UI_STRUCTURE_MANIFEST.json`

Lines 233-307: promote section lists multi-route structure with all 9 lifecycle sub-routes plus the redirect page.
References `promote/layout.tsx`, `(lifecycle)/layout.tsx`, store, config.

- **If Option A:** Keep — matches reality.
- **If Option B:** Collapse to single entry for `/services/promote` with `page.tsx` + `promote-page-client.tsx`.

### P16. `docs/promote lifecycle tab/PROMOTE_LIFECYCLE_DESIGN.md` §9

Design doc §9 describes the multi-route structure.

- **If Option A:** Keep — matches.
- **If Option B:** Update to reflect single-URL approach.

### P17. `docs/STRUCTURE_COMPONENTS.md`

Updated promote-flow-modal path. Reads: "full lifecycle lives under `/services/promote/*` (canonical entry
`/services/promote/pipeline`; `/services/promote` redirects)".

- **If Option A:** Keep.
- **If Option B:** Update to "full lifecycle lives at `/services/promote`".

### P18. Mock data in `components/promote/`

`mock-data.ts` (1,649 lines) and `mock-fixtures.ts` (673 lines) live in components/. Per .cursorrules Rule 6, mocks
should be in `lib/mocks/`. However, these are not MSW handlers — they're fixture data used directly by components. This
is a known migration target but not blocking.

- **Both options:** Flag for future migration to `lib/mocks/fixtures/`.

---

## Recommended Action Items (by option)

### If Option A (keep multi-route) — minimal cleanup

| #   | Task                                                  | Files   |
| --- | ----------------------------------------------------- | ------- |
| A1  | Verify `npm run build` passes                         | —       |
| A2  | Visual smoke test: navigate all 9 promote sub-routes  | browser |
| A3  | Verify stage-gating works (locked tabs not navigable) | browser |
| A4  | Flag P18 (mock data location) as future cleanup       | —       |

### If Option B (collapse to single-URL) — significant refactor

| #   | Task                                                                | Files                                                                                                                                                                                                                          |
| --- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| B1  | Delete 9 lifecycle route pages                                      | `(lifecycle)/*.tsx`                                                                                                                                                                                                            |
| B2  | Delete `(lifecycle)/layout.tsx`                                     | 1 file                                                                                                                                                                                                                         |
| B3  | Replace `promote/layout.tsx` with thin server page.tsx              | 1 file                                                                                                                                                                                                                         |
| B4  | Create `promote-page-client.tsx` with Shadcn Tabs + all tab content | 1 file                                                                                                                                                                                                                         |
| B5  | Delete 7 routing-infra components                                   | `promote-lifecycle-frame.tsx`, `promote-lifecycle-stage-page.tsx`, `promote-lifecycle-sub-tabs.tsx`, `promote-pipeline-page.tsx`, `promote-stage-access.ts`, `promote-strategy-context-bar.tsx`, `promote-workflow-bridge.tsx` |
| B6  | Simplify `promote.config.ts`                                        | 1 file                                                                                                                                                                                                                         |
| B7  | Simplify `lib/config/index.ts` exports                              | 1 file                                                                                                                                                                                                                         |
| B8  | Update `lifecycle-mapping.ts` promote entry                         | 1 file                                                                                                                                                                                                                         |
| B9  | Update `service-tabs.tsx` PROMOTE_TABS href                         | 1 file                                                                                                                                                                                                                         |
| B10 | Update `UI_STRUCTURE_MANIFEST.json`                                 | 1 file                                                                                                                                                                                                                         |
| B11 | Update design doc §9                                                | 1 file                                                                                                                                                                                                                         |
| B12 | Update `STRUCTURE_COMPONENTS.md`                                    | 1 file                                                                                                                                                                                                                         |
| B13 | Keep store (for demo reset) but simplify if possible                | 1 file                                                                                                                                                                                                                         |
| B14 | `npm run build`                                                     | —                                                                                                                                                                                                                              |
| B15 | Visual smoke test                                                   | browser                                                                                                                                                                                                                        |

---

## My Recommendation

**Option A** — the multi-route approach is already built, internally consistent, matches the design doc, follows the
same pattern as every other service in the app, and gives bookmarkable URLs. The cost of keeping it is zero; the cost of
collapsing to single-URL is ~15 tasks including deleting files, rewriting the page client, and updating 6+ reference
files.

The only reason to go with Option B is if you specifically want the simpler single-page structure and don't need
bookmarkable stage URLs.
