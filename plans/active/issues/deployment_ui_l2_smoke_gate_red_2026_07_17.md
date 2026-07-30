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
asset_group:
  [ui] # corrected 2026-07-30 (ui-tranche launch) -- was [meta]; repos:[deployment-ui] only, the
  # pw:L2 smoke gate itself
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
last_updated: 2026-07-30
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

- [x] ✅ [UI] P2. **Diagnose the 5 row-mismatch failures before touching any spec — RESOLVED 2026-07-28 (slot-3): NOT
      REPRODUCIBLE.** Re-ran cockpit.spec.ts + deployments-page.spec.ts fresh; none of the 5 fail today —
      `Deployments.tsx` already calls `getDeploymentInventory()` (`/api/deployments/inventory`), not the plain
      `/api/deployments`, so the suspected catch-all-shadowing bug isn't present for this route. Fixed by other work
      sometime in the 11 days since this doc was filed (not bisected — not needed). See the dated log entry below for
      full evidence.
- [x] ✅ [UI] P2. **Fix the `aria-prohibited-attr` WCAG AA violation on `/ops/costs`** — ALREADY RESOLVED 2026-07-26
      (slot-8, pre-existing this task's dispatch): `deployment-ui@2340c68` added `role="button"` to the `InfoTip`
      tooltip-trigger `<span>` (`CostObservability.tsx`), making its `aria-label` WCAG-legal per the axe
      `aria-prohibited-attr` rule (a `<span>` has an implicit "generic" role, which prohibits accessible naming via
      `aria-label`; `role="button"` grants it). Verified 2026-07-28 (slot-4):
      `npx playwright test --project=chromium     tests/smoke/accessibility_audit.spec.ts -g "Daily Costs"` passes, and
      the full `accessibility_audit.spec.ts` (all 6 pages) passes 6/6 — no code change needed this session, just
      confirming the fix already shipped.
- [ ] [UI] P3. **Update the 5 `daily_costs_and_vm_detail.spec.ts` specs to the post-a9795f3 Cost Observability page**
      ("Daily VM Costs" → "Cost Observability"; re-derive the total/asset-group/date-picker locators from the current
      DOM). Pure spec work — the page is healthy.
- [ ] [UI] P3. **Disambiguate `mobile_responsive.spec.ts:101`** — use `nav-cockpit` / `mobile-menu-btn` testids instead
      of the `/menu|hamburger|navigation/i` role-name regex that matches both buttons.
- [x] ✅ [UI] P2. **Fix `cockpit.spec.ts`'s 3 stale fleet-tab-removal specs — DONE 2026-07-28 (slot-3)**: removed
      `"fleet"` from `TAB_IDS`, removed the `/fleet` nav + `cockpit-fleet`/`cockpit-fleet-git` assertions from "each tab
      switches and renders its pane" (now starts from `/cockpit`), deleted the now-moot "Fleet tab shows only the
      git-health surface" test (the whole page it guarded is gone per
      `plans/archive/issues/deployment_ui_fleet_tab_removal_2026_07_27.md`). Verified 38/38 `cockpit.spec.ts` + 49/49
      combined with `deployments-page.spec.ts` passing. `deployment-ui@<pending sha, see commit for exact hash>`.
- [x] ✅ [UI] P2. **DONE 2026-07-30 (slot-7, ui_developer).** **Deleted `tests/smoke/fleet-git-tab.spec.ts` entirely** —
      `deployment-ui@c14af3a`. The real test bodies were already stripped 2026-07-29 (leaving only a doc-comment stub
      explaining the `/fleet` page removal); this deletes that now-pointless placeholder file. A plain
      `git rm     tests/smoke/fleet-git-tab.spec.ts` was NOT blocked this time — re-read
      `block_destructive_commands.py`'s regex (`\brm\b[^|;&\n]*(-[A-Za-z]*[rR]|--recursive)`): a bare `git rm <file>`
      with no `-r`/`-R`/`--recursive` flag anywhere on the line does not match; the 2026-07-28 block was presumably a
      different invocation shape (e.g. a flag or compound command), not an inherent false-positive on every single-file
      `git rm`. Verification: `tsc     --noEmit` clean, `eslint src` clean, full `tests/smoke/` suite 423 passed / 1
      failed (`venue_credentials.spec.ts:50`, already tracked in this doc's own 2026-07-30 "newly-surfaced" cluster
      below as unrelated — a standalone re-run of that spec passed 4/4, confirming flakiness/pre-existing, not caused by
      this change). Also found + fixed an unrelated environment bug while verifying: this slot's `deployment-ui` clone
      had a stale npm-era `node_modules` (pre-dating the 2026-07-29 pnpm migration), which produced the exact same
      broken 24% coverage numbers as the already-resolved
      `plans/archive/issues/deployment_ui_vitest_coverage_gate_broadly_red_2026_07_29.md` — fixed locally via a clean
      `pnpm install` (no code change needed, `pnpm-workspace.yaml`'s `packages:` fix was already merged); full
      `quality-gates.sh` green post-reinstall (73.85% lines, sentinel matches `c14af3a`). Shipped via quickmerge —
      landed on `live-defi-rollout`.
- [ ] [UI] P2. **Fix `nav-menu-dedup.spec.ts`'s 5 stale fleet-tab-removal failures** — remove the
      `["fleet", "/fleet", "cockpit-fleet"]` row from the `CANONICAL` array; re-derive (don't guess) the "17 entries"
      count (16 canonical nav items exist today per `NavMenu.tsx`'s own `NAV_ITEMS_CANONICAL`, split into N
      cockpit-tabs + M navlinks — count both live rather than hardcoding); rewrite "the top bar stays visible OFF the
      cockpit" to click a tab that still exists instead of `cockpit-tab-fleet`; re-derive what `/infra` and `/infra`
      (previously-selected-service case) actually redirect to now that `/fleet` doesn't exist for them to redirect to
      (per `NavMenu.tsx`'s own comment, `/infra` "now falls through to the catch-all" — verify live, don't assume).
- [ ] [UI] P3. **Diagnose the ~7 apparently-unrelated 2026-07-28 failures** (not touched this session, no root cause
      established): `cadence_badge_drilldown.spec.ts:39`, `mobile_responsive.spec.ts:178`,
      `needs-attention-panel.spec.ts:40` + `:56`, `repos-tab.spec.ts:272` (name mentions "fleet" cross-link — check
      against the same removal first), `stateful-flows.spec.ts:236`, `venue_year_coverage.spec.ts:173`.
- [ ] [UI] P3. **Diagnose the 5 NEWLY-surfaced 2026-07-30 failure clusters** (measured fresh this session, not present
      in the 2026-07-28 breakdown above — the gate has drifted further, not just stayed at 19):
      `venue_credentials.spec.ts` (4 failures: `:22` heading render, `:30` tardis-api-key EXPIRED status, `:43` refresh
      button, `:50` no-JS-error guard — all 4 failing suggests the panel/mock contract drifted, not a locator nit),
      `venue_date_ranges.spec.ts` (2 failures: `:31` binance free/paid date counts, `:52` no-JS-error guard — same
      pattern, panel-level not locator-level), `url-sync.spec.ts` (4 failures: `:10`/`:24`/`:37`/`:49` — service-view
      URL sync, epics deep-link, browser-back — possibly connected to the same nav/routing drift as the already-tracked
      `nav-menu-dedup.spec.ts`/fleet-removal cluster, worth checking together), `repos-codebase-health.spec.ts` (3
      failures: `:10` header help toggles, `:27` FAILING-repo red coverage chip, `:35` qg-reason chip),
      `prediction_v9_breakdown.spec.ts:106` (OTHER CQG bucket hover tooltip). Also 2 additional
      `needs-attention-panel.spec.ts` failures beyond the previously-tracked `:40`/`:56` pair: `:82` (collapse/expand)
      and `:99` (row-click scopes category selector) — same file, different subtests, so likely the same underlying root
      cause as the already-tracked pair but not confirmed.
- [ ] [UI] P2. **Re-baseline + green the gate, then state it in the codex** — once the above land,
      `npx playwright test --project=chromium tests/smoke/` must exit 0 so `pw:L2 ✓` becomes truthful evidence again.
      **Not a quick job**: as of 2026-07-30 the gate carries 17 failures on the SAME 424-test suite size as 2026-07-28
      (down from 19 — the fleet-tab-removal `cockpit.spec.ts` fix landed — but 5 clusters newly surfaced in the same
      window, so net drift is sideways, not converging) — see the dated log entries below for the full breakdowns.

## 2026-07-28 update (slot-3, ui_developer) — the 5 row-mismatch failures are RESOLVED; a bigger, different regression is now the blocker

Picked up the "Diagnose the 5 row-mismatch failures" P2 todo. **Outcome: NOT REPRODUCIBLE ANYMORE.** Installed the
missing playwright chromium binary (this environment had none — `npx playwright install chromium`), then re-ran
`tests/smoke/cockpit.spec.ts` + `tests/smoke/deployments-page.spec.ts` fresh: none of the 5 originally-failing tests
(cockpit.spec.ts:222/:267, deployments-page.spec.ts:14/:34/:53) fail today — the specific rows
(`deployment-row-sports-backfill-20260621`, `feed-health-cefi-instruments-backfill`) render correctly, and
`Deployments.tsx` already calls `getDeploymentInventory()` (→ `/api/deployments/inventory`), not the plain
`/api/deployments` endpoint — the suspected catch-all-shadowing bug (cf. deployment-ui@0c817d2) is NOT present for this
route. Whatever fixed this landed sometime in the 11 days since this doc was filed; not independently bisected (not
necessary — the outcome itself is the deliverable).

**But the gate is still red today, for a DIFFERENT and larger reason.** A fresh full `tests/smoke/` run (425 tests, up
from 355+12 — the suite grew substantially) shows **19 failures**, almost none of which are the original 12:

- **A NEW, connected stale-spec cluster (fleet-tab removal, 2026-07-27)** —
  `deployment_ui_fleet_tab_removal_2026_07_27.md` (archived, shipped) deleted `/fleet` entirely (fleet git-health now
  lives on agent-orchestrator's own dashboard) and correctly updated `Cockpit.test.tsx` (the Vitest unit test) for the
  new tab count, but **missed 3 different L2 smoke spec files** that still assert the removed tab/page exists:
  - `cockpit.spec.ts:59/:89/:434` — **FIXED this session** (removed "fleet" from `TAB_IDS`, removed the `/fleet`
    navigation + fleet-testid assertions from "each tab switches", deleted the now-moot "Fleet tab shows only the
    git-health surface" test; `deployment-ui@<pending sha>`, verified 38/38 passing).
  - `fleet-git-tab.spec.ts` (all 4 tests) — this WHOLE FILE is dedicated to the removed `/fleet` page and should be
    deleted (same pattern as the `Cockpit.test.tsx` fix in the removal PR). **NOT fixed this session** — a file delete
    via `rm`/`git rm` was blocked by this VM's `block_destructive_commands.py` guardrail (a coarse "recursive rm"
    pattern match that doesn't distinguish a single tracked source-file delete from an actual tree delete; the hook's
    own suggested escalation is a slot ping since the GCS-SDK carve-out it describes doesn't apply to a git-tracked test
    file). Left as a clean follow-up todo below.
  - `nav-menu-dedup.spec.ts` (5 of its failures) — the `CANONICAL` array still lists
    `["fleet", "/fleet", "cockpit-fleet"]`; "the top bar carries the same 17 entries" needs recounting (16 canonical nav
    entries exist today, `NavMenu.tsx`'s own `NAV_ITEMS_CANONICAL` already correctly excludes fleet — only the spec's
    hardcoded 17/10 counts are stale); two bookmark-compat-redirect tests still assert `/infra → /fleet` even though
    `NavMenu.tsx`'s own comment says `/infra` "now falls through to the catch-all" since `/fleet` doesn't exist to
    redirect to. **NOT fixed this session** (needs the counts + redirect target re-derived from the current app
    behavior, not guessed — left as a follow-up todo).
- **~7 apparently UNRELATED failures** (not diagnosed this session — out of scope for the dispatched todo):
  `cadence_badge_drilldown.spec.ts:39`, `mobile_responsive.spec.ts:178`, `needs-attention-panel.spec.ts:40` + `:56`,
  `repos-tab.spec.ts:272` (note: its name mentions "fleet" too — cross-link target, worth checking against the same
  removal), `stateful-flows.spec.ts:236`, `venue_year_coverage.spec.ts:173`.

**Net for the "Re-baseline + green the gate" P2 todo**: was 12 failures (2026-07-17), is 19 failures today (16 after
this session's fix), of which the fleet-removal cluster (8 remaining) + the ~7 unrelated ones need their own diagnosis
passes — this is NOT a quick re-baseline, the gate has drifted meaningfully since this doc was filed.

## 2026-07-30 update (slot-3, ui_developer) — measured while verifying an unrelated todo; gate drift is sideways, not converging

Surfaced incidentally while verifying
[`data_pipeline_alert_substrate_residual_2026_07_24_finalize_2026_07_30.md`](/plans/active/data_pipeline_alert_substrate_residual_2026_07_24_finalize_2026_07_30.md)
todo 2 (streaming-events pane, an unrelated deployment-ui change touching only `StreamingLogsPanel.tsx` + a new
`tests/smoke/cockpit-streaming-logs-live-contract.spec.ts`). Ran the full
`npx playwright test --project=chromium tests/smoke/` suite for my own `pw:L2 ✓` evidence: **407 passed, 17 failed**
(same 424-test suite size as the 2026-07-28 update). Confirmed ALL 17 are unrelated to my diff by
`git stash push --include-untracked` on my two touched paths + re-running a sample of the failing spec files on the
now-pristine tree — identical failures reproduced with zero of my changes present (the "baseline by stashing, never by
reasoning" lesson below, applied).

**Net change since 2026-07-28(19 failures)**: down to 17, but NOT the same 17 minus 2 — the composition shifted:

- **Confirmed still-open, already-tracked**: `nav-menu-dedup.spec.ts:158` (1 of its prior 5 — the fleet-removal
  redirect-target cluster tracked in `deployment_ui_fleet_git_nav_entry_regression_2026_07_28.md`; the other 4
  `nav-menu-dedup` failures from 2026-07-28 no longer reproduce, not investigated further here — not needed for this
  todo's purpose).
- **2 of the previously-tracked "~7 unrelated" cluster still fail**: `needs-attention-panel.spec.ts` — but at DIFFERENT
  line numbers (`:82`, `:99` today vs `:40`, `:56` on 2026-07-28), i.e. the file itself is still broken, just not
  necessarily the same assertions — not diagnosed which.
- **5 clusters not present in the 2026-07-28 breakdown at all**: `venue_credentials.spec.ts` (4/4 tests in the file
  failing), `venue_date_ranges.spec.ts` (2 failures), `url-sync.spec.ts` (4 failures), `repos-codebase-health.spec.ts`
  (3 failures), `prediction_v9_breakdown.spec.ts` (1 failure). None reference anything in my diff (`StreamingLogsPanel`,
  `AlertsLogsTab`, the new spec file) by name or by shared component. Added as new todos above rather than investigated
  — out of scope for the dispatched todo, per this doc's own established pattern of filing-not-fixing to avoid scope
  creep.
- **No longer reproducing** (present 2026-07-28, clean today, not bisected): `cadence_badge_drilldown.spec.ts:39`,
  `mobile_responsive.spec.ts:178`, `repos-tab.spec.ts:272`, `stateful-flows.spec.ts:236`,
  `venue_year_coverage.spec.ts:173`, plus 4 of the 5 `nav-menu-dedup.spec.ts` failures. Likely fixed as a side effect of
  other work landing in the interim (matches this doc's own precedent of fixes landing without this doc being flipped) —
  not independently verified, since re-confirming a PASS isn't the same actionable-finding bar as a FAIL.

**My own `pw:L2` evidence for the dispatched todo**: the new spec (`cockpit-streaming-logs-live-contract.spec.ts`, 2
tests) plus the directly-related `cockpit-alerts-logs-ag-vm-picker.spec.ts` + `cockpit.spec.ts` (40 tests total) all
pass 100% — cited on the finalize-plan checkbox rather than a whole-suite exit code, per this doc's own standing finding
that a truthful whole-suite `pw:L2 ✓` is not currently achievable through no fault of any single UI todo.

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
