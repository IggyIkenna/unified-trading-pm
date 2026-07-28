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
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-ui]
scope: [engineer]
tags: [deployment-ui, smoke-tests, playwright, regression, daily-costs, nav]
related: [/plans/active/issues/deployment_ui_fleet_git_nav_entry_regression_2026_07_28.md]
created: "2026-07-21"
parent_epic: deployment_and_user_management_master
source: discovered running `npx playwright test tests/smoke/` while verifying mtds_data_status_page_parity_2026_07_21.md
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
locked_by: live-defi-rollout
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
- [ ] [UI] P3. Reconcile `nav-menu-dedup.spec.ts`'s expected count (5 → 6, or find and fix the extra entry) — whichever
      the current nav design intends. **UPDATE 2026-07-28**: the original 5→6 drift this item named was briefly resolved
      by deployment-ui@2340c68 (2026-07-26 — "already correct, no fix needed"), but the nav has since drifted further in
      a 2026-07-27 reorg: `nav-menu-dedup.spec.ts` now fails with a DIFFERENT signature (expects 17 entries not 6; a
      `fleet` nav item/route/testid appears to have been dropped), alongside 3 sibling specs (`fleet-git-tab.spec.ts`,
      `cockpit.spec.ts`, `repos-tab.spec.ts` — 13 failures total, confirmed via a fresh full `tests/smoke/` run this
      session). This is now root-caused in detail and gated on an explicit `[OPERATOR]` regression-vs-intentional-fold
      decision in `/plans/active/issues/deployment_ui_fleet_git_nav_entry_regression_2026_07_28.md` — resolve THERE
      (this item's narrower "5→6" framing is stale; do not re-diagnose from scratch here).

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
