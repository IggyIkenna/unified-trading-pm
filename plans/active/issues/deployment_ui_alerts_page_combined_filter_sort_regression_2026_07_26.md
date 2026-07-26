---
doc_type: issue
title:
  "deployment-ui Alerts page — combined kind-filter + date-range + column-sort spec fails: vm_down row reappears after
  sort"
summary: >-
  Discovered while running the full deployment-ui `tests/smoke/` suite to verify the 8 pre-existing smoke failures from
  `issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md` (that todo's own 3 named fixes are
  unrelated). A 9th, separate, consistently-reproducing (non-flaky, 3/3 repeat runs) failure on `alerts-page.spec.ts`
  surfaced: after applying the `kind=alert` filter + a date-range bound + a column sort together, the excluded `vm_down`
  row reappears. Filed rather than expanded into scope per this workspace's "pre-existing is not a triage criterion" +
  "do not absorb unplanned scope" rules.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui]
scope: [engineer]
tags: [deployment-ui, smoke-tests, playwright, regression, alerts-page, filter, sort]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md,
  ]
created: 2026-07-26
parent_epic: deployment_and_user_management_master
assigned_vm: planning
source: [infra_satellite_ao_dispatch_batch1-004 (ui_developer worker investigation)]
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: ui_developer
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
---

# Alerts page — combined filter+sort spec fails (vm_down row reappears)

## What I found

While shipping the 3 named fixes in `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s "Fix the 8 pre-existing
deployment-ui smoke failures" todo (Daily Costs / mobile hamburger / nav-menu-dedup — all fixed, see that plan's flip
evidence), the full `npx playwright test --project=chromium tests/smoke/` run surfaced a 9th failure that is NOT one of
the original 8 and NOT related to any of the 3 named areas:

```
tests/smoke/alerts-page.spec.ts:343:3 › Alerts page › kind filter, date range, and column sort
compose correctly when all three are active at once
```

Confirmed non-flaky: reproduces 3/3 on `--repeat-each=3` in isolation (not a full-suite-parallelism artifact — unlike
`stateful-flows.spec.ts`'s "create deployment then find it in history", which DID turn out to be a full-run-only flake
and passes reliably in isolation).

Failure:

```
Error: expect(locator).toHaveCount(expected) failed
Locator:  getByText('VM DOWN: cefi-binance-futures-backfill')
Expected: 0
Received: 1
    at tests/smoke/alerts-page.spec.ts:361:76 (kind filter, date range, and column sort compose ...)
```

The test (added per `deployment_ui_alerts_page_rebuild_2026_07_20.md`'s `[REVIEW]` todo, to prove the independent
filter/sort `useMemo` layers compose rather than one clobbering another):

1. Applies `filter-kind-alert` (should exclude the one `vm_down`-kind row, leaving 4 `alert`-kind rows).
2. Applies a date-range `alert_to=2026-06-10` bound (all 4 remaining rows are dated 2026-06-10, so this should be a
   no-op on the result set).
3. Clicks the Subject column header to sort ascending.
4. Asserts the `vm_down` row (`"VM DOWN: cefi-binance-futures-backfill"`) has count 0 — this is where it fails: the row
   is present after the sort click, despite the kind filter that should have excluded it.

This suggests the sort re-render is re-deriving its row set from a broader (unfiltered, or a stale/wrong-scope) source
rather than composing on top of the already-`kind=alert`-filtered rows — i.e. sort and filter may not be composing
through the same derived-rows pipeline the test's own comment says they should ("proving the independent `useMemo`
layers (filter → sort) compose correctly rather than one clobbering another" — this is exactly the clobbering case the
test was written to catch).

I did not root-cause the exact `useMemo`/state-derivation bug in the Alerts page component itself — that would have
expanded this dispatch beyond its named scope (Daily Costs / mobile / nav-dedup only, with an explicit
`DataStatusTab.tsx` scope guard). Filing per the "big finding" / "pre-existing is not a triage criterion" rule instead.

## Why it matters

A real, reproducible functional regression on the production Alerts page: filtering by kind and then sorting a column
can silently un-exclude rows the kind filter was supposed to remove. An operator using kind-filter + sort on `/alerts`
may see incident rows they explicitly filtered out reappear — a correctness bug in a page whose whole purpose is
filtering signal from noise for on-call triage.

## Recommended decision

Not a judgment call — reproduce, trace the Alerts page's filter/sort state derivation (likely in `src/pages/Alerts.tsx`
or a similarly-named component; the test file's own header names `deployment_ui_alerts_page_rebuild_2026_07_20.md` as
the origin plan for this filter/sort architecture), find where the sort's derived-rows source diverges from the
filter's, and fix so sort composes ON TOP OF the already-filtered set. Do not weaken the test assertion.

## Todos

- [ ] [UI] P2. Root-cause and fix the Alerts page combined kind-filter + date-range + column-sort regression:
      `npx playwright test --project=chromium tests/smoke/alerts-page.spec.ts -g "kind     filter, date range, and column sort compose correctly"`
      must pass — the `vm_down` row must stay excluded after a sort is applied on top of an active kind filter. Trace
      the filter/sort `useMemo` derivation chain in the Alerts page component (see
      `deployment_ui_alerts_page_rebuild_2026_07_20.md` for the original filter/sort design) rather than adjusting the
      test's expectation. (repo: deployment-ui)

## Progress Log

- 2026-07-26 (slot 8, `ui_developer`): Filed while shipping `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s
  deployment-ui smoke-failure todo. Confirmed reproducible (3/3 on `--repeat-each=3`), confirmed unrelated to the Daily
  Costs / mobile / nav fixes shipped in that todo (deployment-ui@2340c68). Not fixed here — out of the dispatched todo's
  named scope.
