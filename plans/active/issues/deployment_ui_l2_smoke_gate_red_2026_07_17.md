---
doc_type: issue
title:
  deployment-ui L2 route-smoke gate has been RED on LDR — 12 failures, only 6 are stale specs; 1 is a real a11y
  violation and 5 are a live mock/page row mismatch
summary: |
  Surfaced while rebuilding the deployment-ui nav (2026-07-17, operator-driven, no owning plan). **The `pw:L2 ✓`
  plan-tick rule is unenforceable today**: `npx playwright test --project=chromium tests/smoke/` exits 1 with **12
  failures on a pristine tree** (baselined by stashing all work and re-running — identical list), so no UI todo can
  legitimately carry the `pw:L2 ✓` evidence the workspace requires. Triaged, the 12 are NOT one problem: **6 stale
  specs** (the /ops/costs page was redesigned out from under them), **1 REAL serious WCAG AA violation**
  (`aria-prohibited-attr` on Daily Costs — the test is correct, the page is broken), and **5 unresolved** where the
  mock DEFINES a row the page never renders (same family as the mock-lying bug deployment-ui@0c817d2 fixed the same
  day). Filed so the gate gets back to green and the 5 get a real diagnosis rather than being written off.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [deployment-ui]
scope: [engineer]
tags: [ui, playwright, quality-gates, l2-smoke, a11y, mock-parity, validation]
related:
  [
    /codex/06-coding-standards/ui-testing-layers.md,
    /codex/04-architecture/orphan-audit.md,
    /plans/active/issues/deployment_api_live_mock_parity_2026_07_17.md,
  ]
created: 2026-07-17
last_updated: 2026-07-17
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: frontend_engineering
resolved_by:
locked_by:
drift_direction: advance-code
source:
  [
    deployment-ui/tests/smoke/daily_costs_and_vm_detail.spec.ts#L117,
    deployment-ui/tests/smoke/accessibility_audit.spec.ts#L60,
    deployment-ui/tests/smoke/deployments-page.spec.ts#L14,
    deployment-ui/src/lib/mock-api.ts#L1181,
    deployment-ui/src/pages/CostObservability.tsx#L2007,
  ]
depends_on: []
---

# deployment-ui L2 route-smoke gate is RED on LDR (12 failures)

## Why this matters

`/codex/06-coding-standards/ui-testing-layers.md` §"tick evidence" makes **`pw:L2 ✓`** mandatory on every UI plan tick,
and defines it as "`npx playwright test --project=chromium tests/smoke/` exited 0 in the agent's local environment".
That command **exits 1 today, and did before any of this session's work** — so either UI todos are being ticked without
the evidence (review-blocking per the rule), or they are all silently `[BLOCKED-PLAYWRIGHT]`. A permanently-red gate is
also a broken smoke alarm: it cannot tell you when a NEW regression lands, which is exactly what it exists for.

**Measured baseline (2026-07-17):** `355 passed, 12 failed`. Established by `git stash`-ing every change in the session
and re-running the same spec files on the pristine tree — the failing list was **identical**, so none of the 12 come
from the nav rebuild (deployment-ui@2c98262 · cd304a8 · bb836a5 · 0bde31d · 704062b).

## Correction to an earlier claim (recorded so the wrong number does not survive)

During the session these were repeatedly summarised to the operator as **"12 stale specs, ~30 min of locator updates"**.
**That was wrong** — the label was verified for the /ops/costs cluster and then generalised to the rest without
checking. On inspection only 6 are stale. The a11y one is a real product defect and the 5 row-mismatch ones are
undiagnosed. Do not plan this as a mechanical locator sweep.

## Triage

### A. Genuinely stale specs — 6 (the page moved, the spec did not)

`daily_costs_and_vm_detail.spec.ts` :117 :126 :137 :147 :159 — all five assert against a Daily-Costs page that no longer
exists. `deployment-ui@a9795f3` ("feat(costs): help-guide dialog + top-bar layout refresh") redesigned it: it now
renders `<h1>Cost Observability</h1>` and has no "Daily VM Costs" heading, no "By Asset Group" table, no
`[data-testid=total-usd]`, and no `input[aria-label="Select date"]`. **Verified by loading `/ops/costs` under the test
mock — the page renders correctly**; the specs simply were never updated with the redesign.

`mobile_responsive.spec.ts:101` — a Playwright **strict-mode violation**, not a product bug:
`getByRole("button", { name: /menu|hamburger|navigation/i })` matches **two** buttons — the nav trigger
(`aria-label="Open navigation menu"`) and the mobile hamburger (`aria-label="Open menu"`). Needs a disambiguating
locator (both carry testids: `nav-cockpit` / `mobile-menu-btn`).

### B. A REAL product defect — 1 (do NOT "fix" the spec)

`accessibility_audit.spec.ts:60` — reports **1 serious WCAG AA violation** on Daily Costs: `aria-prohibited-attr` —
_"Ensure ARIA attributes are not prohibited for an element's role / Elements must only use permitted ARIA attributes"_
(impact: **serious**, https://dequeuniversity.com/rules/axe/4.11/aria-prohibited-attr). The test is doing its job. Fix
the page, not the assertion.

### C. Unresolved — 5 (the mock defines a row the page never renders)

`cockpit.spec.ts:222` `:267` + `deployments-page.spec.ts:14` `:34` `:53` all hinge on two rows:
`deployment-row-sports-backfill-20260621` and `feed-health-cefi-instruments-backfill`.

**These are NOT stale fixtures** — that was the second wrong guess. Both rows are still defined in
`src/lib/mock-api.ts`: `sports-backfill-20260621` lives in `MOCK_DEPLOYMENT_INVENTORY` (declared L1181, served by
`path === "/api/deployments/inventory"` at L3421), and `cefi-instruments-backfill` at L1414. But a real page load of
`/deployments` under the mock renders **18 rows from a different set** (`MOCK_DEPLOYMENTS`, L107) and neither row is
among them. So the data exists and the page does not show it.

**Lead to follow first:** deployment-ui@`0c817d2` — landed the SAME DAY by another agent — is titled _"fix(data-status):
mock-api catch-all shadowed every specific /api/data-status/\* endpoint added since 2026-06-16"_. That is precisely this
failure mode on a different endpoint family. Check whether `/api/deployments/inventory` is similarly shadowed, or
whether `Deployments.tsx` reads `MOCK_DEPLOYMENTS` when the spec assumes the inventory endpoint. **If it is the
shadowing bug, the mock has been lying about `/deployments` for weeks** and the 3 deployments-page specs are
correct-and-failing, not stale.

## Todos

- [ ] [UI] P2. **Diagnose the 5 row-mismatch failures before touching any spec** — establish whether
      `/api/deployments/inventory` is catch-all-shadowed (cf. deployment-ui@0c817d2) or whether `Deployments.tsx` reads
      the wrong mock source. Evidence: mock defines the rows (`mock-api.ts` L1181/L1414); a live `/deployments` load
      renders 18 rows from `MOCK_DEPLOYMENTS` (L107), excluding both. **Outcome decides everything else**: a real
      shadowing bug means these specs are correct and the product/mock is wrong.
- [ ] [UI] P2. **Fix the `aria-prohibited-attr` WCAG AA violation on `/ops/costs`** (serious impact). The
      `accessibility_audit.spec.ts:60` assertion is correct — fix `CostObservability.tsx`, do not relax the test.
- [ ] [UI] P3. **Update the 5 `daily_costs_and_vm_detail.spec.ts` specs to the post-a9795f3 Cost Observability page**
      ("Daily VM Costs" → "Cost Observability"; re-derive the total/asset-group/date-picker locators from the current
      DOM). Pure spec work — the page is healthy.
- [ ] [UI] P3. **Disambiguate `mobile_responsive.spec.ts:101`** — use `nav-cockpit` / `mobile-menu-btn` testids instead
      of the `/menu|hamburger|navigation/i` role-name regex that matches both buttons.
- [ ] [UI] P2. **Re-baseline + green the gate, then state it in the codex** — once the above land,
      `npx playwright test --project=chromium tests/smoke/` must exit 0 so `pw:L2 ✓` becomes truthful evidence again.

## Lessons (carry these; they each cost real time)

- **`tests/e2e/` is NOT covered by the L2 gate.** `pw:L2 ✓` is defined as `tests/smoke/` only, so e2e rot is invisible.
  It had rotted: `tests/e2e/` has **20 failures on a pristine tree**, incl. `cloud-toggle.spec.ts` where all 3 tests saw
  a **blank page** — the spec routed `**/api/**`, which under Vite dev ALSO matches the app's own `/src/api/client.ts`,
  so it 404'd the source module and React never booted. Fixed in deployment-ui@bb836a5 (match on `url.pathname`
  instead). **Any `page.route("**/api/**")` in a Vite-served app is this bug.**
- **`safety-ops-deployment-ui.spec.ts` :33/:42 never passed** — they want a visible "Safety Ops" link in the desktop
  header, but the pre-session header had no page nav at all (it literally said `{/* No page-nav here ... */}`). Verified
  against `git show 7a431f7:src/components/Header.tsx`. Now that a top nav bar exists, the fix is a real option — its
  short label is "Safety", so the `/Safety Ops/i` regex still misses.
- **Baseline by stashing, never by reasoning.** Twice this session a failure "obviously" caused by the change turned out
  to be pre-existing, and once the reverse. `git stash push -- <paths>` → re-run the same spec files → diff the lists.
  Cheap, and the only thing that actually settles attribution.
- **A green count is not a green gate.** `353 passed` looks fine in a log tail; the run still `exit 1`. Always read the
  real exit code — and note `cmd > log; echo $?` captures the **echo's** status, not the command's.
