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
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui]
scope: [engineer]
tags: [deployment-ui, smoke-tests, playwright, regression, daily-costs, nav]
related: []
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

- [ ] [UI] P2. Trace whether the Daily Costs failures are a real page regression or a mock-data-shape drift; fix root
      cause.
- [ ] [UI] P2. Fix `mobile_responsive.spec.ts`'s strict-mode locator (scope to one of the two matching buttons, or
      update the test's intent if both are now expected).
- [ ] [UI] P3. Reconcile `nav-menu-dedup.spec.ts`'s expected count (5 → 6, or find and fix the extra entry) — whichever
      the current nav design intends.
