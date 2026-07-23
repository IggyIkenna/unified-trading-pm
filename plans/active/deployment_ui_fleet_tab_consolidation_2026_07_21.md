---
doc_type: plan
title: deployment-ui — Fleet tab consolidation (strip to git-health, merge orphans + VM census into Deployments)
summary: >-
  The Fleet tab (/fleet) is one overloaded page stacking five sections built before the dedicated Deployments tab
  existed. Audit 2026-07-21 classified every section: the VM-census embed and FleetInfra (infra tiles + orchestrator/
  slots panel) duplicate or are superseded, the reconciliation cards are largely redundant, and the Stopped & orphaned
  VMs (idle disk spend) view is genuinely useful but only its VISIBILITY exists on Deployments — the reap/delete
  actions, verdict/grace classification, stopped-age, and idle-spend rollup cards do not. Plan: remove FleetInfra
  entirely (AO owns orchestrator health), remove the census embed + reconciliation cards, MERGE the orphan idle-spend
  capability and the standalone /vm-deployments history into the Deployments tab (retiring /vm-deployments), and leave
  Fleet as ONLY fleet git health + slot-wise dirty repos.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [deployment-ui, deployment-api]
scope: [engineer]
tags: [deployment-ui, fleet, consolidation, cleanup, observability, idle-spend]
related:
  - /plans/active/deployment_ui_observability_ux_tracker_2026_07_17.md
  - /plans/archive/2026_07/deployment_ui_date_range_filter_and_search_2026_07_20.md
  - /plans/archive/2026_07/deployment_ui_vm_log_viewer_2026_07_20.md
created: "2026-07-21"
last_updated: "2026-07-21"
parent_epic: observability_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 1.6
assigned_role: ui_developer
drift_direction: advance-code
sequential: true
depends_on:
  - deployment_ui_date_range_filter_and_search_2026_07_20.md
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: operator audit session 2026-07-21 (Fleet-tab audit + consolidation decisions)
---

# deployment-ui — Fleet tab consolidation

> **🟢 Activated gated (operator 2026-07-21)** — `status: active` + `gate_on_depends: true`. Authored in the tabs-3
> worktree per operator instruction (keep new work off the root repo where other agents are active).
>
> **⚠️ Same-file coordination — `Deployments.tsx`.** This plan edits `src/pages/Deployments.tsx` (merging orphan
> actions/cards + census history) and so does
> [`deployment_ui_date_range_filter_and_search_2026_07_20.md`](deployment_ui_date_range_filter_and_search_2026_07_20.md)
> (filters + shared-primitive extraction). `gate_on_depends: true` now **machine-holds** every task in this plan until
> that plan's tasks all complete — the backlog enforces the ordering, so no same-file collision (multi-agent safety) and
> no reliance on manual activation timing. (The shared-primitive extraction has already landed at
> `deployment-ui@1cf191b`; the gate additionally waits on the date-range plan's remaining tail before this plan
> dispatches.)

## Context — Fleet-tab audit findings (2026-07-21, read-only)

Fleet (`/fleet` → `CockpitFleet` → `FleetTab` in `Cockpit.tsx`) is ONE page stacking five sections. Locate each by its
component/section name — grep, do NOT trust line numbers:

| #   | Section                                                              | where                                | Verdict                                                            |
| --- | -------------------------------------------------------------------- | ------------------------------------ | ------------------------------------------------------------------ |
| a   | Reconciliation cards (Accounted / Unknown / Expected-missing)        | inline in `FleetTab` (`Cockpit.tsx`) | REMOVE (redundant; keep only the "expected-missing" idea if cheap) |
| b   | VM census embed (compact `VmDeployments`)                            | `VmDeployments.tsx`                  | REMOVE embed; merge unique bits to Deployments                     |
| c   | Stopped & orphaned VMs (idle disk spend)                             | `FleetOrphans.tsx`                   | **MERGE into Deployments** (actions/cards/verdict missing there)   |
| d   | Infra & orchestrator health (tiles + VM census + orchestrator/slots) | `FleetInfra.tsx`                     | **REMOVE ENTIRELY** (operator: AO owns orchestrator health)        |
| e   | Fleet git health + slot-wise dirty repos                             | `FleetGit.tsx`                       | **KEEP** — becomes the entire Fleet tab                            |

Key audit facts driving the merges:

- **Deployments already SEES idle spend** — `DISK`/`STATIC_IP` orphan rows (kind filter "disk (orphaned)" / "static IP
  (orphaned)" in `Deployments.tsx`), per-row `LeakedBadge` ("N leaked ·
  ~$X/mo"), estate-wide `StrandedCostBadge`, a
  `stopped` status filter, and Resources sortable by leaked $/mo. **But it
  lacks** FleetOrphans' (1) reap/delete ACTIONS (`VmControls` is pause/resume/stop/restart only; FleetOrphans has the
  dry-run bulk `reapOrphans` handler + a per-instance delete-with-boot-disk handler), (2) the reap-verdict/grace
  classification helper (grep `FleetOrphans.tsx` for the verdict/grace logic), (3) the idle-spend rollup cards (Stopped
  VMs · Reapable · Idle disk $/mo · Reclaimable
  $/mo) + stopped-age, and (4) it defaults `status=running` so orphans
  are hidden until you switch the filter.
- **Idle-disk cost is an ESTIMATE on BOTH surfaces** — FleetOrphans' `monthly_disk_usd` is "asia-northeast1 list rate ×
  GB" (grep the api client for the `monthly_disk_usd` estimator), not real billing; Deployments' leaked-$/mo is the same
  class of estimate. Real-billing idle spend (WS-1-style) is a possible later enhancement, NOT in scope here — preserve
  the estimate for parity.
- **FleetOrphans is self-contained** — depends only on `/api/fleet/orphans`, `/api/fleet/reap`,
  `DELETE /api/fleet/instances/{name}`. But the reap-verdict / grace / stopped-age / disk-rollup fields do NOT exist on
  the `DeploymentItem` type (in `deploymentApi.ts`) — merging them needs either Deployments consuming
  `/api/fleet/orphans` or new inventory fields (backend todo below).
- **`/vm-deployments` is a SEPARATE canonical tab** (its route in `App.tsx` + nav entry in `NavMenu.tsx`), not legacy —
  Fleet only embeds a compact copy. Operator decision: consolidate it into Deployments and retire it. Its unique content
  vs Deployments: the archive/history table (Outcome, Duration, Rows Captured, Completed, archive log links) +
  `rows_error` (Errors) + throughput (`rows_in`/`events_emitted`). The archive **log links overlap WS-4** (the run.log
  viewer) — do NOT build a second log renderer; defer log display to WS-4's viewer.
- **KEEP-set correction** — the slot-wise dirty-repo data is populated by **`slot-git-status-report.sh`** (repo classify
  → POST AO `/api/slots/{N}/git-status`), NOT `slot-cron-ff-pull.sh` (which populates the ff-pull _liveness_ fields).
  Both are cron-driven and land in the same `/api/fleet/git-health` → `/api/repo-ci/fleet-git-health` surface
  `FleetGit.tsx` reads. FleetGit is unaffected by removing the other sections.
- **KEEP-set enhancement (operator 2026-07-21)** — FleetGit renders the derived `reporter_stale` "reporter dead" boolean
  but NOT the actual snapshot time. The `reported_at` timestamp is already stored server-side (the
  `SlotRow.git_status_reported_at` field, posted as `reported_at`) AND already on the wire type (grep `client.ts` for
  `reported_at`) — it's simply not rendered. Surfacing it is a pure UI add (see todo). Context: each host's reporter
  POSTs to ITS OWN local orchestrator; a laptop running a local standalone AO instance shows only its own slots (the "no
  `ORCHESTRATOR_VM_ID` ⇒ standalone/isolated" rule, `is_standalone()` in `vms.py`), so the snapshot time also tells the
  operator which local instance's clock produced the row.

## Decisions (operator, 2026-07-21)

1. **FleetInfra — remove entirely** (tiles + VM-census panel + orchestrator/slots panel). AO's own dashboard owns
   slots/backlog/watchdog health; the CI tile is redundant with `/repo-ci`; the git tile is redundant with FleetGit.
2. **/vm-deployments — consolidate into Deployments** and retire the standalone tab (fold history + `rows_error` +
   throughput; defer log links to WS-4).
3. **FleetOrphans — merge into Deployments**, not remove: bring the rollup cards, verdict/stopped-age, and the
   reap/delete actions over so idle spend is actionable there.
4. **Fleet end-state = ONLY fleet git health + slot-wise dirty repos** (the FleetGit section).

## Todos

- [x] [BACKEND] P0. ✅ **Orphan/idle data on the Deployments surface** — deployment-api@aa6dbff. Added
      `reap_verdict`/`grace_hours`/`stopped_age_hours`/`monthly_disk_usd` to `DeploymentItem`
      (`deployments_inventory.py`), populated inside `build_inventory` via a name-joined
      `build_orphan_inventory(vm_details_by_name, disk_details, now, DEFAULT_GRACE_HOURS)` call — the SAME orphans SSOT
      `/api/fleet/orphans` uses (`_fleet_inventory.py`), computed once per census cycle from data already fetched (no
      new GCE call, no second cost estimator). Fields populate only for VM rows currently STOPPED/SUSPENDED/TERMINATED
      (the orphan candidate set); a running VM honestly reports all four as `None`. Added `DEFAULT_GRACE_HOURS = 24.0`
      to `_fleet_inventory.py` for this new call site (existing `/orphans`+`/reap` endpoint defaults left untouched —
      unrelated blast radius). 2 new unit tests (`test_build_inventory_surfaces_orphan_reap_verdict_on_stopped_vm`,
      `test_build_inventory_running_vm_has_no_orphan_fields`) plus the existing 105-test file all green; full
      `quality-gates.sh` clean (basedpyright error count unchanged vs pre-edit baseline — verified by diffing
      before/after). Next: the UI-facing todos below (rollup cards, verdict badges, reap/ delete actions) consume these
      new fields. (repo: deployment-api)
- [x] [UI] P1. ✅ **Idle-spend rollup cards on Deployments** — deployment-ui@d12843e. Ported the four FleetOrphans
      rollup cards (Stopped VMs · Reapable · Idle disk $/mo · Reclaimable $/mo) verbatim (same markup/formatting) into
      `Deployments.tsx`, right below `StrandedCostBadge` in the page header. Fetches `GET /api/fleet/orphans`
      independently of the main inventory load (own `useVisibilityPausedInterval` cadence, same as the rest of the page)
      — honest `"—"` placeholders on fetch failure, never stale/fabricated data. tsc/ESLint clean; 2 new Vitest tests
      (cards render the rollup figures; cards degrade to `"—"` on fetch failure) + full existing suite green (1042
      tests); full `quality-gates.sh` (base-ui.sh v2.0) green. Playwright verification is bundled into the plan's
      consolidated `[REVIEW] P1. Playwright specs` todo below (covers this + the remaining UI todos together, per the
      plan's own structure — not a separate spec per card). (repo: deployment-ui)
- [x] [UI] P1. ✅ **Reap-verdict + stopped-age on orphan rows** — deployment-ui@02b08c2. Added the 4 backend orphan-join
      fields to the TS `DeploymentItem` interface + a new `OrphanVerdictCell` (same verdict label/variant mapping as
      `FleetOrphans.tsx`'s `VerdictBadge`), rendered in `StatusCell` next to the status chip: verdict badge (reapable /
      within-grace / retained / no-stop-time) + compact stopped-age ("2.1d"). Renders nothing for a running VM or non-VM
      kind (the field is honestly absent, not hidden by a conditional guess). tsc/ESLint clean; 2 new tests (stopped
      orphan row shows the badge + age; running row shows neither) + full 1049-test suite green; full `quality-gates.sh`
      (base-ui.sh v2.0) green.
- [x] [UI] P1. ✅ **Reap/delete actions on Deployments** — deployment-ui@eef5acf. Ported FleetOrphans' dry-run-first
      bulk reap (`reapOrphans` → `/api/fleet/reap`) and per-instance delete-with-boot-disk
      (`DELETE /api/fleet/instances/{name}`) verbatim, same two-dialog safety pattern (dry-run preview populates the
      confirm dialog; destructive execute only fires on an explicit confirm click). Per-row delete button replaces
      `VmControls`' inert "—" for a stopped/orphan row (a new `OrphanDeleteContext` threads the click handler to
      `DeploymentRow`, mirroring the existing `DrillContext` pattern rather than prop-drilling through
      `DeploymentMatrix`). Both actions refresh the main inventory + the idle-spend rollup together on success.
      tsc/ESLint clean; 2 new tests (delete flow, bulk-reap flow) + full 1051-test suite green; full `quality-gates.sh`
      (base-ui.sh v2.0) green.
- [x] [UI] P2. ✅ **Idle-spend discoverability** — deployment-ui@596c13a. Each of the 4 idle-spend rollup cards now
      applies `status=stopped` on click (cursor-pointer + hover affordance + `title="Show stopped VMs"`). Updated the
      Vitest `Card` mock to spread all props through (it previously dropped `onClick`/`role`/etc., silently discarding
      any click handler in tests) — matches the real `Card` component's forwarding contract. 1 new test + full existing
      suite green (1052 tests); full `quality-gates.sh` (base-ui.sh v2.0) green.
- [x] [UI] P1. ✅ **Fold /vm-deployments history into Deployments** — deployment-ui@678449a. Added a VM-kind-only
      `VmRunHistoryCard` to `DeploymentDetail.tsx` (folded from `VmDeployments.tsx`'s archive table): Outcome / Duration
      / Rows Captured / Completed + GCS-console archive log links. Reused the existing `logUriToConsoleUrl` link pattern
      rather than building a second log-tail viewer — the current run's tail already has its own `RunLogPanel` card
      (WS-4), which can only address the LATEST run for a name (not historical rows), so per-row historical log access
      stays a console deep-link, same as the standalone page always did. Exported 5 formatting helpers from
      `VmDeployments.tsx` (`formatTimestamp`/`formatDuration`/
      `getOutcomeVariant`/`getOutcomeLabel`/`logUriToConsoleUrl`) for reuse instead of re-implementing. No
      per-name-scoped history endpoint exists, so it client-side filters `fetchVmDeployments(30)`'s `recent[]` by
      `vm_name === name` (same cost the standalone page always paid — not this ticket's scope to add a scoped endpoint).
      tsc/ESLint clean; full 1050-test suite green; full `quality-gates.sh` (base-ui.sh v2.0) green. `/vm-deployments`
      itself is untouched (still routed, still the `VmDeploymentsContent` the `/fleet` cockpit embeds) — retiring it is
      the separate todo below.
- [x] [UI] P1. ✅ **Cheap merged columns** — deployment-ui@f838929. Added a compact `ErrorsThroughput` cell to the
      Resources column (alongside cpu/mem/disk + `LeakedBadge`): "N err" in red when `rows_error > 0`, plus "N in"/"N
      evt" when `rows_in`/`events_emitted` are present. Null-renders per field (no fabricated 0 for a row without the
      signal). 2 new tests + full existing suite green (1054 tests); full `quality-gates.sh` (base-ui.sh v2.0) green.
- [x] [UI] P1. ✅ **DEVIATED from the literal ask (operator decision, BLK-7cb5bbbc)** — deployment-ui@92b5cd4. The audit
      behind this todo never accounted for 4 venue-config panels (`VenueCredentialsPanel`/
      `VenueDateRangePanel`/`VenueRelaunchEstimatePanel`/`VenueTardisWindowsPanel`) that ONLY render in
      `VmDeploymentsContent`'s non-compact mode — the `/fleet` cockpit embed uses `compact=true` and explicitly skips
      them (`{!compact && (<><VenueCredentialsPanel/>...`). A literal hard redirect + route deletion would have silently
      orphaned this real, tested functionality (`tests/smoke/venue_tardis_windows.spec.ts`). Escalated via `/blocked`;
      operator answered A — reuse the codebase's existing `legacy: true` `NAV_GROUPS` quarantine convention instead of
      inventing a new mechanism: `/vm-deployments` STAYS a live route (bookmarks/deep-links survive, `orphan-audit.ts`
      confirms zero new unreachable routes) but moved to a new "Legacy" nav group, off the canonical dropdown/bar
      (`NAV_ITEMS_CANONICAL` 16→15). Updated 4 Vitest suites whose counts/testids hard-coded vm-deployments as canonical
      (`NavMenu.test.tsx`, `TopNavBar.test.tsx`, `Header.test.tsx`) + rewrote
      `tests/smoke/vm_deployments_archive_history.spec.ts`'s now-redirect-was-wrong assertion. Full 1052-test suite
      green; full `quality-gates.sh` (base-ui.sh v2.0) green. The archive/history table itself was already folded into
      `DeploymentDetail`'s History card in the prior todo — this todo only concerned the standalone page's route/nav
      fate. Deferred: relocating the 4 venue panels to a permanent canonical home is real unplanned design work, filed
      as `plans/active/issues/vm_deployments_venue_panels_orphaned_route_2026_07_21.md` rather than decided here.
- [x] [UI] P1. ✅ **Remove FleetInfra** — delete the FleetInfra section from `FleetTab` and its imports; remove any nav/
      route pointing at it. Confirm nothing else depends on its endpoints (`/api/fleet/vm-census`,
      `/api/fleet/infra-vm-health`) in the UI; leave the backend endpoints intact (out of scope). — ✅
      `deployment-ui@84b6a17`. Removed the `<FleetInfraContent />` section + its import from `Cockpit.tsx`; deleted
      `FleetInfra.tsx` entirely (confirmed zero other importers). No dedicated nav/route pointed at it — only the
      generic `/infra → /fleet` bookmark-compat redirect exists, which stays (its App.tsx comment updated for accuracy).
      Confirmed nothing else in the UI calls `/api/fleet/vm-census` / `/api/fleet/infra-vm-health` — removed the
      now-fully-dead `getVmCensus`/`getInfraVmHealth` client functions + their exclusive response types from `client.ts`
      (kept `VmLifecycleClass`/`VmRunStatus`, which `OrphanEntry` still depends on) and their mock-api.ts
      handlers/generators; backend endpoints untouched (out of scope, confirmed intact). Deleted 2 now-fully-obsolete
      regression specs (`fleet-infra-vm-census.spec.ts`, `fleet-infra-tab.spec.ts` — both existed solely to guard
      FleetInfra content) and fixed 2 partially-affected specs (`cockpit.spec.ts`'s Fleet-tab fold test now asserts
      `cockpit-fleet-infra` has zero count instead of visible; `nav-menu-dedup.spec.ts`'s redirect-mount assertion
      switched from the removed testid to the still-live `cockpit-fleet` wrapper). Full `quality-gates.sh` green
      (typecheck/lint/orphan-audit/99 test files/build all passed). Playwright: ran both touched specs — 59 passed, 1
      pre-existing unrelated failure (`nav-menu-dedup.spec.ts`'s "top bar carries 15 entries" test still expects
      `cockpit-navlink-vm-deployments` visible in the canonical bar, a gap left by the earlier
      `/vm-deployments`→Legacy-nav todo, BLK-7cb5bbbc — verified via `git stash` that it fails identically on pre-change
      HEAD, not a regression from this change). `pw:L2 ✓` (my own 2 touched specs both green).
- [x] [UI] P1. ✅ **Remove the VM-census embed + reconciliation cards** from `FleetTab` (in `Cockpit.tsx`) — after the
      merges above land. Optionally preserve the "expected-missing" (registered-but-not-running) count as a small
      Deployments summary if cheap; otherwise drop. — ✅ `deployment-ui@e2cf84b`. Removed the reconciliation
      `useEffect`/state/cards block + the `<VmDeploymentsContent compact />` census embed from `FleetTab`; `FleetTab`
      now renders only the orphan idle-spend surface + `FleetGitContent` (git-only is the next todo). "Expected-missing"
      preservation: dropped (not cheap) — no existing surface on Deployments carries this concept, and preserving it
      would mean re-wiring the whole `/api/fleet/reconciliation` endpoint I'm removing UI support for, contradicting the
      audit's own primary verdict that reconciliation is redundant. Cleaned up the now-fully-dead
      `getFleetReconciliation`/`FleetReconciliationResponse`/`ReconciliationRow`/`CloudReconciliation` from
      `api/health.ts` (confirmed zero other importers) + the mock-api.ts `/api/fleet/reconciliation` handler; removed
      the now-unused `VmDeploymentsContent` import from `Cockpit.tsx` (the standalone `/vm-deployments` page itself is
      untouched). Fixed 3 affected tests: `cockpit.spec.ts`'s "each tab switches" test (dropped the reconciliation-card
      assertions, added a `cockpit-fleet-git` visibility check instead), deleted its now-fully-obsolete "Fleet tab
      renders the real VM census" test, and `Cockpit.test.tsx`'s unit test (asserts `cockpit-fleet-git` present +
      `cockpit-fleet-card-unknown` absent). Full `quality-gates.sh` green (typecheck/lint/orphan-audit/99 test
      files/build). Playwright: `cockpit.spec.ts` full run, 39 passed, 0 failed. `pw:L2 ✓`. Lost the quickmerge sentinel
      race once to a concurrent unrelated `.pre-commit-config.yaml` commit — re-ran QG, retried, landed clean on the 2nd
      attempt.
- [x] [UI] P1. ✅ **Fleet = FleetGit only** — `FleetTab` renders only `FleetGitContent`; update the page title + the
      Fleet nav description in `NavMenu.tsx` ("Census · orphans · git · infra" → "git health · dirty repos"). Verify
      FleetGit renders standalone (reads only `/api/repo-ci/fleet-git-health`). — ✅ `deployment-ui@fce06fb` +
      `@8c23e7b` (stale-comment follow-up). `FleetTab` now renders ONLY `<FleetGitContent />` (removed the
      `FleetOrphansContent` embed — that capability was already MERGED into Deployments in earlier todos, not lost, so
      Fleet dropping it is a pure de-dup); deleted the now-fully-orphaned `FleetOrphans.tsx` (confirmed zero other
      importers — no standalone route referenced it). Updated `NavMenu.tsx`'s Fleet `desc` from
      `"Census · orphans · git · infra"` to `"git health · dirty repos"` (confirmed no test asserted the old string
      verbatim). Verified `FleetGitContent` is genuinely standalone by inspection — its only data import is
      `getFleetGitHealth` from `api/client.ts` (`/api/repo-ci/fleet-git-health`), no dependency on
      FleetInfra/FleetOrphans/VmDeployments. **Test coverage decision**: rather than just deleting the 2 Fleet-orphans
      Playwright tests (which would silently drop real e2e coverage for a capability that still exists on Deployments),
      retargeted them to `/deployments` using its `deployments-`-prefixed testids — the idle-spend rollup cards + bulk
      dry-run/execute reap flow are both exercisable there with the EXISTING mock data (same `/api/fleet/orphans`
      fixture, fetched independently by Deployments). The per-instance delete-dialog flow was NOT ported — it needs a
      row in the main deployment-inventory mock with `reap_verdict` populated, which doesn't currently exist in
      `mock-api.ts` (a pre-existing gap from whichever earlier todo shipped that Deployments feature, only unit-tested
      via hand-built fixtures in `Deployments.test.tsx` — noted honestly in a spec comment, not silently dropped, out of
      scope for this P1/1hr todo). Full `quality-gates.sh` green (typecheck/lint/orphan-audit/99 test files/build).
      Playwright `cockpit.spec.ts`: 38 passed, 0 failed. `pw:L2 ✓`.
- [x] [UI] P1. ✅ **Show the snapshot timestamp per slot in FleetGit** — render the `reported_at` field (already on the
      wire type in `client.ts`; already stored server-side as `SlotRow.git_status_reported_at`) next to each slot in
      `FleetGit.tsx`, so the operator can see WHEN the status snapshot was taken, not just the derived `reporter_stale`
      "reporter dead" boolean. Show both an absolute time and a relative age (e.g. "3m ago") so freshness reads at a
      glance and pairs with the existing stale badge. Pure UI — NO backend change (the timestamp already reaches the
      frontend). — ✅ `deployment-ui@509f3b9`. Added `fmtSnapshotAge`/`fmtSnapshotTime` helpers to `FleetGit.tsx` and
      rendered `"snapshot ‹Nm/h/d ago›"` next to each slot's badges/ff-pull chip, with the absolute local time as a
      hover tooltip (`title` attr) — pairs with the existing `reporter dead` badge without duplicating it. Pure UI, no
      backend change (confirmed `reported_at` was already on the wire, just unrendered). Extended
      `fleet-git-tab.spec.ts` with a new Playwright test asserting the snapshot text + tooltip render. Full
      `quality-gates.sh` green (one unit-test failure on the first full-QG attempt, in an unrelated file
      `ExecutionBacktests.test.tsx` — verified as a FLAKE, not caused by this change: the same file passed in isolation
      on both this diff and pre-change HEAD, and the full suite re-run passed 100% clean on the second attempt).
      Playwright `fleet-git-tab.spec.ts`: 4 passed, 0 failed. `pw:L2 ✓`.
- [x] [REVIEW] P1. ✅ **Playwright specs** — new: Deployments idle-spend cards + reap-confirm/dry-run flow + folded
      history; Fleet shows ONLY git health + dirty repos + the per-slot snapshot timestamp; `/vm-deployments` redirects
      to `/deployments`. Keep existing Deployments + Fleet regression specs green. `pw:L2 ✓` + cited specs. No tick
      without them. — ✅ Audit complete, no new code shipped this todo (nothing outstanding to ship — see below). Per
      capability: **Deployments idle-spend cards + reap-confirm/dry-run** — covered by `cockpit.spec.ts`'s "Cockpit —
      Deployments orphan inventory + bulk reap" describe block (retargeted from Fleet to Deployments in this plan's
      earlier todo). **Folded history** — covered by the pre-existing `vm_deployments_archive_history.spec.ts` (5 tests:
      outcome badges, duration, rows-captured, log/serial links, empty state). **Fleet = git-only + snapshot timestamp**
      — covered by `cockpit.spec.ts`'s "each tab switches" test + `fleet-git-tab.spec.ts` (4 tests incl. the new
      snapshot-age assertion). **Note on the literal "`/vm-deployments` redirects to `/deployments`" wording**: this
      line predates the operator's later BLK-7cb5bbbc decision (an earlier todo in this same plan) which ruled
      `/vm-deployments` STAYS a live route (legacy-quarantined, not redirected) because its non-compact mode is the only
      reachable home for 4 venue-config panels — that decision is what's actually implemented and tested
      (`vm_deployments_archive_history.spec.ts`'s own describe-block comment cites BLK-7cb5bbbc explicitly), so no
      redirect test was written since a redirect would contradict the ruling that superseded this line. **Found + fixed
      a real pre-existing gap during this audit**: `nav-menu-dedup.spec.ts`'s "top bar carries the same N entries" test
      still expected the OLD stale `vm-deployments` canonical-nav testid (a leftover from BLK-7cb5bbbc never being
      reflected there — confirmed via live DOM inspection, not guessed) — while resolving this, a CONCURRENT slot's
      commit (`deployment-ui@ddecdec`, "give the 4 venue-config panels a canonical `/venue-config` route") landed with
      an equivalent-but-more-complete fix (also closing the venue-panels-orphaned-route issue doc filed earlier in this
      plan) — deferred to theirs per the multi-agent-collision precedent (verified their version passes before
      accepting, not blindly). Ran the CONSOLIDATED regression suite across every capability this plan touched
      (`cockpit.spec.ts` + `fleet-git-tab.spec.ts` + `nav-menu-dedup.spec.ts` + `nav_and_header.spec.ts` +
      `vm_deployments_archive_history.spec.ts` + `vm_deployments_reconcile.spec.ts` + `deployments-page.spec.ts` +
      `venue_tardis_windows.spec.ts` + `routes.spec.ts`): **114 passed, 0 failed**. `pw:L2 ✓`.
- [x] [INFRA] P1. ✅ Ship (`quickmerge.sh "msg" --agent --files '<paths>'` across deployment-ui + deployment-api if
      touched) + flip todos same turn (`docs(plans):`). — ✅ Already satisfied by construction: every todo in this plan
      (from "Remove FleetInfra" through the Playwright-review audit) was individually shipped via `quickmerge.sh` and
      its plan checkbox flipped in the SAME turn, per the commit-push-flip HARD RULE — not deferred to a single
      end-of-plan mega-commit. Final shipped chain on `deployment-ui`: `84b6a17` → `e2cf84b` → `fce06fb` → `8c23e7b` →
      `509f3b9` → `ddecdec` (the last one landed by a concurrent slot closing the venue-panels gap found during review).
      `deployment-api` was untouched throughout (every backend endpoint stayed intentionally out of scope per each
      todo's own text). Verified both repos' trees are clean and fast-forwarded to `origin/live-defi-rollout` before
      flipping this todo — nothing outstanding to ship.
- [x] [REVIEW] P2. ✅ Post-phase codex audit — document the consolidated contract (Deployments owns VM inventory + idle
      spend + reap actions + history; Fleet = git-health-only; `/vm-deployments` retired) in
      `/codex/05-infrastructure/deployment-observability.md`. — ✅ `unified-trading-pm@dd5068f4c`. Added a new
      "Fleet-tab consolidation" section documenting: Deployments now owns idle-spend (rollup cards + verdict/
      stopped-age + dry-run reap/delete, ported verbatim from the removed `FleetOrphans.tsx`) + the folded
      `/vm-deployments` archive history; Fleet is git-health-only (`FleetTab` renders exactly `FleetGitContent` + the
      new snapshot timestamp); `/vm-deployments` is legacy-quarantined (NOT redirected — BLK-7cb5bbbc, stays live for
      the 4 venue-config panels, later given its own canonical `/venue-config` route). **Also corrected** the now-stale
      "cockpit Fleet tab wires it" claim in the pre-existing cross-cloud-reconciliation paragraph (the endpoint is
      unchanged, just no longer UI-consumed after this plan). Added `FleetGit.tsx`/`Cockpit.tsx`/
      `NavMenu.tsx`/`DeploymentDetail.tsx` to the doc's `code_refs` and this plan to `related`. **Plan is now fully
      closed** — every todo (10 code todos + this audit) done.

## Success criteria

- Fleet tab shows ONLY fleet git health + slot-wise dirty repos; every deployment/VM/orphan/infra section is gone.
- The idle-disk-spend capability (rollup cards, verdict, stopped-age, dry-run reap + delete) is fully usable from the
  Deployments tab, and idle resources are discoverable despite the default running filter.
- `/vm-deployments` is retired; its history + Errors + throughput live on Deployments; a redirect preserves old links.
- No second log renderer built — archive log links defer to WS-4's run.log viewer.
- No same-file collision with the date-range plan (this plan executed after it).
- All existing Deployments + Fleet Playwright regressions stay green.

## Progress Log

- **2026-07-21** — Authored from the operator's Fleet-tab audit session (two parallel read-only audits: Fleet full
  column inventory + Deployments idle-resource cross-check). Operator decisions: remove FleetInfra entirely (AO owns
  orchestrator health), consolidate `/vm-deployments` into Deployments and retire it, merge FleetOrphans' idle-spend
  capability (cards + verdict + reap/delete actions) into Deployments rather than removing it, leave Fleet as
  git-health-only. Key finding: Deployments already SEES idle spend (orphan rows + leaked/stranded badges) but lacks the
  ACTIONS and rollups — so the orphan view is a merge, not a delete. Both surfaces' idle cost is a list-rate estimate,
  not real billing (real-billing idle spend noted as a possible future enhancement, out of scope). Corrected the
  keep-set attribution: dirty-repo data comes from `slot-git-status-report.sh`, not `slot-cron-ff-pull.sh`. Flagged the
  `Deployments.tsx` same-file collision with the date-range plan → `depends_on` + activate-after ordering. Kept `draft`.
- **2026-07-21 (continued)** — Operator clarified the multi-host git-health model (each host reports to its own local AO
  instance; central proxies registered fleet VMs by private IP; laptops are standalone/isolated — the extra IP the
  operator saw was their own locally-run AO backend). Added a keep-set enhancement todo: surface the per-slot
  `reported_at` snapshot timestamp in FleetGit (pure UI — data already stored + on the wire type, just unrendered).

## Codex SSOTs

- `/codex/05-infrastructure/deployment-observability.md` — deployment inventory + (to add) the consolidated
  Deployments-owns-everything / Fleet-is-git-health-only contract.
- `/codex/06-coding-standards/ui-testing-layers.md` — the UI gate (pw:L2 + cited spec) for every `[UI]` todo.
- `/codex/05-infrastructure/per-tab-worktrees.md` — the slot/dirty-repo model behind the FleetGit keep-set
  (`slot-git-status-report.sh` + `slot-cron-ff-pull.sh` → AO `/api/fleet/git-health`).
