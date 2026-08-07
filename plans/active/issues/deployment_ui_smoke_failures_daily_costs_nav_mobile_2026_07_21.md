---
doc_type: issue
title: deployment-ui — 8 pre-existing smoke failures (Daily Costs page, mobile nav hamburger, nav-menu-dedup)
summary: >-
  Discovered while running the full deployment-ui smoke suite to verify an unrelated fix (MTDS instrument-search
  visibility, mtds_data_status_page_parity_2026_07_21.md). Confirmed unrelated to that change (none reference the
  touched files/constants). Filed rather than silently ignored per this workspace's "pre-existing is not a triage
  criterion" rule; not fixed here to avoid scope creep on an unrelated dispatch.
status: open
nature: process
asset_group:
  [ui] # corrected 2026-07-30 (ui-tranche launch) -- was [infrastructure]; repos:[deployment-ui]
  # only, smoke-test failures in deployment-ui's own pages
stage: [meta]
repos: [deployment-ui]
scope: [engineer]
tags: [deployment-ui, smoke-tests, playwright, regression, daily-costs, nav]
related: [/plans/archive/issues/deployment_ui_fleet_git_nav_entry_regression_2026_07_28.md]
created: "2026-07-21"
author: unknown
parent_epic: deployment_and_user_management_master
source: discovered running `npx playwright test tests/smoke/` while verifying mtds_data_status_page_parity_2026_07_21.md
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
locked_by: live-defi-rollout
context_scope:
  [
    /plans/archive/issues/deployment_ui_fleet_git_nav_entry_regression_2026_07_28.md,
    /codex/06-coding-standards/ui-testing-layers.md,
    deployment-ui/tests/smoke/top-nav-bar.spec.ts,
  ]
locked_since: 2026-05-21
assigned_vm: planning
resolved_by:
---

# deployment-ui smoke failures — Daily Costs / mobile nav / nav-menu-dedup

Full `tests/smoke/` run (2026-07-21): 396 passed, 8 failed. All 8 are on pages/components unrelated to
`DataStatusTab.tsx`/`CLIPreview.tsx`/`ServiceDetails.tsx`/`api/client.ts` (grep confirmed no references to those files
or their MTDS-related constants).

## Failures

1. `accessibility_audit.spec.ts` — "A11y: Daily Costs has no critical/serious WCAG AA violations" — fails.
2. `daily_costs_and_vm_detail.spec.ts` — 5 failures: heading at `/ops/costs`, total USD on load, "By Asset Group" table
   cefi row, date picker present/interactive, error alert on API failure. Suggests the Daily Costs page itself may not
   be rendering as the tests expect (mock data shape drift, or a real page regression) — needs its own trace.
3. `mobile_responsive.spec.ts` — "hamburger menu is visible and opens nav" (iPhone SE viewport) — strict-mode violation:
   `getByRole('button', {name: /menu|hamburger|navigation/i})` now resolves to 2 elements (`nav-cockpit` AND
   `mobile-menu-btn`), where the test expects exactly one. Likely a recent nav change added a second matching button.
4. `nav-menu-dedup.spec.ts` — "the always-visible top bar carries the same 15 entries as the dropdown" — expected 5
   `cockpit-navlink-*` entries, found 6. A nav entry was likely added without updating this test's expected count.

## Todos

- [x] ✅ [UI] P2. Trace whether the Daily Costs failures are a real page regression or a mock-data-shape drift; fix root
      cause. **RESOLVED** — neither, exactly: the old Daily Costs page was fully redesigned into the Cost Observability
      page (multi-cloud spend/waste breakdown); the 5 failing assertions in the old `daily_costs_and_vm_detail.spec.ts`
      were testing DOM structure (heading/total-usd/By-Asset-Group table/date-picker/error-alert) that no longer existed
      on `/ops/costs` — test obsolescence, not an app regression — plus one genuine WCAG a11y bug (the CostObservability
      info-tooltip trigger was missing `role="button"`, an axe `aria-prohibited-attr` violation). Both were already
      fixed by deployment-ui@2340c68 (slot-8, 2026-07-26): deleted the obsolete DailyCosts test block (coverage now
      lives in `cost-observability.spec.ts`) + added `role="button"` to `CostObservability`'s InfoTip. Freshly
      re-verified this session (deployment-ui HEAD e98c575):
      `npx playwright test --project=chromium tests/smoke/accessibility_audit.spec.ts     tests/smoke/daily_costs_and_vm_detail.spec.ts tests/smoke/cost-observability.spec.ts`
      — 33/33 passed. No new code change needed; this todo closes on the pre-existing fix + fresh verification.
- [x] ✅ [UI] P2. Fix `mobile_responsive.spec.ts`'s strict-mode locator (scope to one of the two matching buttons, or
      update the test's intent if both are now expected). **RESOLVED** — also already fixed by the same
      deployment-ui@2340c68 (slot-8, 2026-07-26): scoped the hamburger locator to the `mobile-menu-btn` testid (it had
      started strict-mode-colliding with the always-visible `nav-cockpit` button, whose aria-label also matched the old
      `menu|hamburger|navigation` regex) and asserts against the `mobile-nav` testid instead of a generic
      `nav`/`[role=navigation]` locator. Freshly re-verified this session:
      `npx playwright test --project=chromium tests/smoke/mobile_responsive.spec.ts` — 10/10 passed.
- [x] ✅ [UI] P3. Reconcile `nav-menu-dedup.spec.ts`'s expected count (5 → 6, or find and fix the extra entry) —
      whichever the current nav design intends. **UPDATE 2026-07-28**: the original 5→6 drift this item named was
      briefly resolved by deployment-ui@2340c68 (2026-07-26 — "already correct, no fix needed"), but the nav has since
      drifted further in a 2026-07-27 reorg: `nav-menu-dedup.spec.ts` now fails with a DIFFERENT signature (expects 17
      entries not 6; a `fleet` nav item/route/testid appears to have been dropped), alongside 3 sibling specs
      (`fleet-git-tab.spec.ts`, `cockpit.spec.ts`, `repos-tab.spec.ts` — 13 failures total, confirmed via a fresh full
      `tests/smoke/` run this session). This is now root-caused in detail and gated on an explicit `[OPERATOR]`
      regression-vs-intentional-fold decision in
      `/plans/archive/issues/deployment_ui_fleet_git_nav_entry_regression_2026_07_28.md` — resolve THERE (this item's
      narrower "5→6" framing is stale; do not re-diagnose from scratch here). **RESOLVED 2026-08-01 (slot-4,
      ui_developer craft)**: the gating doc was resolved+archived 2026-07-29 (operator-directed path (b) — Fleet
      Git-Health nav entry deliberately removed, its only home is now agent-orchestrator's own dashboard;
      `deployment-ui@067f7cd` updated `nav-menu-dedup.spec.ts` to the new 16-entry CANONICAL count). Confirmed `067f7cd`
      is an ancestor of my slot's current HEAD, then freshly re-ran
      `npx playwright test --project=chromium tests/smoke/nav-menu-dedup.spec.ts` — **19/19 passed** (21.0s), including
      "the always-visible top bar carries the same 16 entries as the dropdown". No new code change needed; this item
      closes on the already-shipped fix + fresh verification, `pw:L2 ✓`.

## Progress Log

- **2026-07-28** — Worked item 1 (Daily Costs trace + fix). Found both item 1 and item 2 were already fixed by
  deployment-ui@2340c68 (2026-07-26) but the checkboxes here were never flipped (no commit touching this doc since
  filing) — flipped both with fresh re-verification evidence. Ran the full `tests/smoke/` suite (424 tests) for item 3:
  confirmed it has drifted past its original "5→6" framing into a larger, already-tracked regression — updated its
  description to point at `deployment_ui_fleet_git_nav_entry_regression_2026_07_28.md` rather than duplicating that
  doc's investigation. Also found and fixed one small unrelated pre-existing flake in
  `tests/smoke/vm-resource-rolling-window.spec.ts` ("filters by service name" raced `.count()` against the in-flight
  mock fetch instead of waiting for a row like its sibling test does) — outside this doc's scope, fixed inline per the
  small+clear findings-triage rule, shipped as its own commit.
- **2026-08-01 (slot-4, ui_developer craft)** — Dispatched item 3 with a STALE brief (the "5 → 6" framing this todo's
  own text already flagged as superseded). Pre-task conflict check: read the gating doc
  `/plans/archive/issues/deployment_ui_fleet_git_nav_entry_regression_2026_07_28.md` first (per the "grep-then-READ, not
  grep-then-conclude" rule) rather than re-diagnosing from scratch — found it RESOLVED + ARCHIVED 2026-07-29,
  operator-directed path (b), `deployment-ui@067f7cd`. Verified `067f7cd` is an ancestor of my slot's current
  deployment-ui HEAD, then froze-verified live rather than trusting the citation: ran
  `npx playwright test --project=chromium tests/smoke/nav-menu-dedup.spec.ts` fresh — 19/19 passed. Flipped item 3
  citing this evidence; no code change needed (all 3 items in this doc are now done).
- **context-scout 2026-08-03**: refreshed context_scope (3 entries, unchanged) — all 3 todos are now done; entries still
  resolve and remain accurate for anyone verifying/closing this doc.
- **context-scout 2026-08-03**: corrected a dead path — `nav-menu-dedup.spec.ts` (cited in this doc's own prose/earlier
  context_scope) no longer exists on disk; its coverage was renamed/consolidated into
  `deployment-ui/tests/smoke/top-nav-bar.spec.ts` (confirmed via the live "the always-visible top bar carries all 16
  canonical entries" test). Swapped the entry to the real current file.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (3 entries), unchanged.
