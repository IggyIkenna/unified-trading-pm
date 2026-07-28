---
doc_type: issue
title:
  "deployment-ui — Fleet Git-Health nav entry appears dropped from NAV_ITEMS_CANONICAL (13 pw:L2 smoke failures, blocks
  the gate fleet-wide)"
summary: >-
  Discovered running the full `npx playwright test --project=chromium tests/smoke/` suite (2026-07-28) to verify 3
  unrelated data-status UI todos in data_status_tab_and_downloads_remediation_2026_06_16.md. 410/423 passed — the
  previously-known prediction_v9_breakdown.spec.ts pre-existing failures are now confirmed FIXED (0 failures there;
  root-caused + fixed same-day by deployment-ui@687d4ce, 2026-06-16). But 13 NEW, unrelated failures now block the same
  `pw:L2` gate: every spec that expects a standalone "Fleet" / "Fleet Git-Health" nav entry (`/fleet` route,
  `cockpit-fleet` / `cockpit-fleet-git` / `fleet-git-page` testids, a `cockpit-tab-*` count of 10) finds it missing.
  Confirmed unrelated to the 3 data-status items (none reference venue-filter/de-dupe-panel/pagination code). Filed per
  "pre-existing is not a triage criterion" rather than silently ignored; NOT fixed here to avoid scope creep / collision
  with whoever is actively in the Cockpit/nav territory (very recent related commits, 2026-07-27).
status: open
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-ui]
scope: [engineer]
tags: [deployment-ui, smoke-tests, playwright, regression, nav, cockpit, fleet-git]
related:
  [
    /plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md,
    /plans/active/issues/deployment_ui_nav_consolidation_2026_07_17.md,
    /plans/active/issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md,
    /codex/06-coding-standards/ui-testing-layers.md,
  ]
created: "2026-07-28"
last_updated: "2026-07-28"
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: frontend_engineering
drift_direction: advance-code
source:
  "discovered running `npx playwright test --project=chromium tests/smoke/` (deployment-ui, slot .tabs/4, HEAD dfa5d0e)
  while verifying data_status_tab_and_downloads_remediation_2026_06_16.md's 3 open [UI] todos"
depends_on: []
resolved_by:
locked_by:
---

# deployment-ui — Fleet Git-Health nav entry regression (13 pw:L2 smoke failures)

## What I found (2026-07-28, full smoke run)

`npx playwright test --project=chromium tests/smoke/` on deployment-ui HEAD `dfa5d0e` (branch `live-defi-rollout`, up to
date with origin): **410 passed, 13 failed** in 2.8m. All 13 failures cluster around one theme — a standalone "Fleet" /
"Fleet Git-Health" nav destination that several specs still expect is not reachable:

| Spec                     | Failing test(s)                                                                                                                                                                                                   |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `cockpit.spec.ts`        | renders all cockpit tabs · each tab switches+renders its pane · "Fleet tab shows only the git-health surface"                                                                                                     |
| `fleet-git-tab.spec.ts`  | top bar's Fleet tab renders proxied fleet-git data · deep-link `/fleet` opens Fleet Git tab · git-health click-through to AO UI · each slot shows snapshot age                                                    |
| `nav-menu-dedup.spec.ts` | nav item "fleet" → `/fleet` · top bar carries the same 17 entries as the dropdown · top bar stays visible off cockpit · bookmark-compat `?tab=` redirects · redirect fires when a service was previously selected |
| `repos-tab.spec.ts`      | repo drill-down cross-links to GitHub / data-status / **fleet**                                                                                                                                                   |

None of the 13 touch `DataStatusTab.tsx`, venue-filter, de-dupe-panel, or pagination code — confirmed unrelated to the 3
UI todos in `data_status_tab_and_downloads_remediation_2026_06_16.md` (Phase A "Venue filter — frontend", Phase B
"Collapse duplicate available/available-dates" + "Pagination visible-count selector"), whose own regression spec
(`tests/unit/components/DataStatusTab.refetch_dedupe_pagination.test.tsx`, vitest) and the data-status-focused smoke
specs (`data_status_coverage_labels.spec.ts`, `mtds_mdps_data_status_parity_2026_07_22.spec.ts`,
`regression-guards.spec.ts`, `data-status-tab-renders.spec.ts`) all pass in this same run.

**Also confirmed**: `prediction_v9_breakdown.spec.ts` has **zero** failures in this run — the pre-existing blocker
`data_status_tab_and_downloads_remediation_2026_06_16.md`'s 2026-06-16 banner cited (2/213 failures, "keeps the
full-suite exit non-zero") was fixed same-day by deployment-ui@`687d4ce` and has stayed fixed since.

## Root-cause pointer (not fixed — see "why not fixed" below)

`src/components/NavMenu.tsx`'s `NAV_GROUPS_CANONICAL` (the single source both the dropdown and the always-visible top
bar render from, per the 2026-07-17 nav-consolidation doc) currently has **16 ids**:
`cockpit, home, epics, deploy, deployments, venue-config, data-status, consolidators, costs, vm-resource-comparison, artifacts, repos, alerts, safety, chaos, launch`.
**There is no `fleet` id anywhere in the array**, and `grep -rn "cockpit-fleet-git\|FleetGitTab" src/` (excluding tests)
returns nothing, and `grep -n '"/fleet"' src/App.tsx` returns nothing — no route, no page component, no testid emits
`cockpit-fleet-git` / `fleet-git-page` in current source.

Separately, `PLAIN_ROUTE_TO_TAB_ID` (same file — the map deciding which nav ids render as `cockpit-tab-<id>` vs
`cockpit-navlink-<id>`) has exactly **9** entries, while `nav-menu-dedup.spec.ts:98` (updated 2026-07-27, commit
`d78de0b "fix(observability): update nav-count assertions for new vm-resource-comparison entry"`) asserts
`page.locator('[data-testid^="cockpit-tab-"]')` has count **10** — the actual DOM has 9. The comment directly above that
assertion (`// "vm-resource-comparison" added 2026-07-27, deployment_durable_operational_data_bigquery_2026_07_21.md`)
shows the test's count was deliberately bumped assuming a 10th cockpit-tab entry would exist; it doesn't.

**Timing**: the most recent commits touching this territory are all 2026-07-27 — `d78de0b` (bumped the count assertion),
`af3e756 feat(observability): VM resource rolling-window view + cross-VM comparison page`,
`fb1da34 feat(ops/artifacts): default /ops/artifacts to What's running tab`,
`74c0a7d feat(ops/artifacts): Phase 3b cross-links`. It's plausible the Fleet Git-Health nav entry was folded away (into
`repos`? `artifacts`?) as part of the same reorg that added `vm-resource-comparison`, without the corresponding spec
updates / compat redirects the 2026-07-17 nav-consolidation doc's own "Lessons" section warns is required ("a fold that
deletes nothing doubles the surface" / "deleting a nav surface costs ~25 spec updates — budget the test churn").

## Why not fixed here

This is genuinely ambiguous between two different fixes with opposite direction, and I don't have enough context to pick
correctly without guessing (task_template.md finding S: a todo whose scope is unclear stays non-dispatchable until
named, not guessed):

- **(a) Regression** — Fleet Git-Health was meant to stay a distinct top-level nav entry and got dropped by accident
  during the 2026-07-27 reorg → restore the `fleet` id to `NAV_GROUPS_CANONICAL` (+ its route/testids/tab-id mapping),
  which should also resolve the `cockpit-tab-*` count-of-10 assertion.
- **(b) Intentional fold** — Fleet Git-Health was deliberately consolidated into another surface (`repos`/CI? per
  `repos-tab.spec.ts`'s failing "cross-links to GitHub / data-status / fleet" assertion, or `artifacts`) as part of the
  same reorg that shipped `vm-resource-comparison` and `fb1da34`'s "What's running" default → in that case the 13 specs
  above are the ones that need updating (assert the new location + a compat redirect for old `/fleet` deep-links, per
  the nav-consolidation doc's established pattern for prior folds), not the component.

Also: this touches the exact same nav/cockpit files (`NavMenu.tsx`, `TopNavBar.tsx`, `Cockpit.tsx`) as very recent,
still-fresh commits — fixing it blind risks colliding with whoever is currently iterating there.

## Todos

- [ ] [OPERATOR] P2. **Decide (a) vs (b) above** — was Fleet Git-Health's nav entry an accidental drop or an intentional
      fold during the 2026-07-27 reorg? Check with whoever authored `af3e756`/`d78de0b`/`fb1da34` or the source plan
      (`deployment_durable_operational_data_bigquery_2026_07_21.md`) for intent.
- [ ] [UI] P2. **Once (a)/(b) is decided, land the fix** — either restore the `fleet` nav id + route + testids (path a),
      or update the 13 failing specs to assert the new surface + add a `/fleet` compat redirect (path b, mirroring
      `deployment_ui_nav_consolidation_2026_07_17.md`'s LandingTabs-deletion precedent). Done-when:
      `npx playwright test --project=chromium tests/smoke/` exits 0 (`pw:L2 ✓`).

## Progress Log

- **2026-07-28** — Filed while verifying `data_status_tab_and_downloads_remediation_2026_06_16.md`'s 3 open `[UI]` todos
  via a fresh full `pw:L2` run. Confirmed unrelated to those 3 items and confirmed the plan's previously-cited
  `prediction_v9_breakdown.spec.ts` blocker is independently already fixed (deployment-ui@687d4ce, 2026-06-16) — this is
  a newly-introduced, separate blocker on the same gate.
