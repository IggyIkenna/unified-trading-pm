---
doc_type: issue
title: /vm-deployments' 4 venue-config panels have no canonical home — legacy-quarantined, not relocated
summary: >-
  The Fleet-tab consolidation retired /vm-deployments from canonical nav (legacy-quarantined instead of hard-deleted,
  per BLK-7cb5bbbc) because its non-compact mode is the ONLY place
  VenueCredentialsPanel/VenueDateRangePanel/VenueRelaunchEstimatePanel/VenueTardisWindowsPanel render — the /fleet
  cockpit embed only uses compact mode. The panels still work (route stays live), but they have no permanent,
  discoverable, canonical UI home. This is a P3 design/relocation follow-up, not a bug.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [deployment-ui]
scope: [engineer, admin]
tags: [deployment-ui, fleet, nav, venue-config, follow-up]
related: []
created: "2026-07-21"
parent_epic: observability_master
priority: P3
assigned_vm: planning
resolved_by:
locked_by:
source: [deployment_ui_fleet_tab_consolidation_2026_07_21.md]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# What I found

While implementing the "Retire /vm-deployments" todo in `deployment_ui_fleet_tab_consolidation_2026_07_21.md`, retiring
the route per its literal text (hard redirect + delete) would have silently made 4 venue-config panels unreachable in
the UI:

- `VenueCredentialsPanel` (`src/components/VenueCredentialsPanel.tsx`)
- `VenueDateRangePanel` (`src/components/VenueDateRangePanel.tsx`)
- `VenueRelaunchEstimatePanel` (`src/components/VenueRelaunchEstimatePanel.tsx`)
- `VenueTardisWindowsPanel` (`src/components/VenueTardisWindowsPanel.tsx`, covered by
  `tests/smoke/venue_tardis_windows.spec.ts`)

They only render inside `VmDeploymentsContent({compact: false})` — `src/pages/VmDeployments.tsx:465-471`
(`{!compact && (<><VenueCredentialsPanel/>...`). The `/fleet` cockpit tab embeds this same component but with
`compact={true}` (confirmed via `tests/smoke/cockpit.spec.ts`), which explicitly skips this block. The standalone
`/vm-deployments` page was the ONLY consumer that ever rendered `compact={false}`.

Resolved via `/blocked` escalation (`BLK-7cb5bbbc`) — operator decision A: keep `/vm-deployments` alive as a
legacy-quarantined route (reusing the existing `legacy: true` `NAV_GROUPS` convention in `NavMenu.tsx`) rather than
deleting it, so the panels keep a WORKING but non-canonical home. Shipped `deployment-ui@92b5cd4`.

# Why it matters

The panels are real, tested functionality (venue credential status, date-range config, relaunch cost estimates, Tardis
concurrency windows) that an operator would reasonably expect to find via normal navigation. Today they're only
reachable by a direct URL (`/vm-deployments`) with no canonical nav entry pointing at them — discoverable only to
someone who already knows the URL or finds it in the mobile hamburger's `NAV_LINKS_FLAT` list. This is a workable
stopgap, not a permanent design.

# Recommended decision

A follow-up should decide where these 4 panels' PERMANENT canonical home is — candidates: a new section on `/fleet`
(alongside git health), a new tab/section on `/deployments`, or their own dedicated route with a real canonical nav
entry. This is a genuine design decision (which surface, what layout) that needs a plan owner, not something to decide
unilaterally mid-implementation of an unrelated consolidation task.

## Todos

- [x] ✅ [UI] P3. Decide the permanent canonical home for the 4 venue-config panels
      (`VenueCredentialsPanel`/`VenueDateRangePanel`/`VenueRelaunchEstimatePanel`/`VenueTardisWindowsPanel`) currently
      only reachable via the legacy-quarantined `/vm-deployments` route — candidates: a new `/fleet` section, a new
      `/deployments` tab, or a dedicated canonical route with a real nav entry. Once relocated, delete the
      `legacy: true` group in `NavMenu.tsx` + the `/vm-deployments` route in `App.tsx` for real (matching the original
      todo's literal intent), and retire `tests/smoke/venue_tardis_windows.spec.ts`'s `/vm-deployments` navigation
      target to point at the new home. (repo: deployment-ui) — `deployment-ui@ddecdec`. **Decision: a dedicated
      canonical route, `/venue-config`**, grouped under "Deploy & Deployments" in `NavMenu.tsx` (not `/fleet` — that
      heading is now explicitly git-health/orphan-VM infra observability, a different concern per its own 2026-07-21
      "FleetInfra removed" note; not a `/deployments` tab either — the site retired its whole `?tab=` scheme 2026-07-17
      in favor of one-URL-per-screen, so adding a new in-page tab would resurrect the exact pattern that consolidation
      just eliminated). Created `src/pages/VenueConfig.tsx` (new page, all 4 panels), wired `/venue-config` in
      `App.tsx`, added a real `NavMenu.tsx` entry (`KeyRound` icon, "Deploy & Deployments" group). Retargeted all 4
      panels' regression specs (`venue_date_ranges`/`venue_relaunch_estimate`/`venue_credentials`/
      `venue_tardis_windows.spec.ts`) from `/vm-deployments` to `/venue-config`; added a new smoke check
      (`nav_and_header.spec.ts`) for the page rendering without a JS error. **Discovery mid-implementation**: the
      original todo's premise ("the /fleet cockpit embed only uses compact mode") was already stale — grepped the live
      code and found NO consumer anywhere actually passes `compact={true}` to `VmDeploymentsContent` today (the Fleet
      tab embed described in this issue doc's own "What I found" section doesn't exist in current `Cockpit.tsx`); the
      `compact` prop was fully dead code, removed. Also found `VmDeploymentsContent` still has 2 genuinely unique,
      still-linked-to features with no other home: the fleet-wide "Reconcile Registry" button and the raw active+archive
      VM table (its `/vm-deployments/:deploymentId` drill-down route is STILL actively linked from
      `DeploymentDetail.tsx`'s History card, confirmed via grep — do NOT delete that route). Deleting
      `/vm-deployments` + the `NavMenu.tsx` legacy group "for real" today would silently drop the reconcile action with
      no replacement home — filed as its own follow-up todo below rather than rushing a regression. Fixed 3 pre-existing
      STALE test assertions found while updating the nav-count contract for the new canonical entry
      (`TopNavBar.test.tsx`'s "4 screens"/`toHaveLength(15)`, `NavMenu.test.tsx`'s `toHaveLength(15)`,
      `nav-menu-dedup.spec.ts`'s stale `vm-deployments`-in-canonical-list assertion that predates this session — none of
      these were self-consistent with each other even before my change). `tsc --noEmit` clean, `eslint` clean on all
      touched files, unit tests (`NavMenu.test.tsx` + `TopNavBar.test.tsx`, 19 tests) pass. Playwright: could not run
      in-session (same host-contention/missing-libatk blocker already documented in this session's other UI tasks) —
      specs are written/retargeted, not fabricated-green.
- [ ] [UI] P3. Relocate `VmDeploymentsContent`'s 2 remaining features (discovered above, not part of the original scope)
      before `/vm-deployments` + `NavMenu.tsx`'s `legacy: true` group can be deleted for real: the fleet-wide "Reconcile
      Registry" action (`reconcileVmDeployments()`) and the raw active+archive VM table. Natural candidates: the
      reconcile action as a global button on `/deployments` (`DeploymentsPage`) or `/fleet`; the active+archive table
      may be fully redundant with `/deployments`' own unified live/batch/paper listing (verify before assuming — don't
      blind-duplicate). Once both have a real home, delete `VmDeployments.tsx` (its `.tsx` file, not
      `VmDeploymentDetails.tsx` — the `:deploymentId` drill-down stays, linked from `DeploymentDetail.tsx`'s History
      card), the `/vm-deployments` route in `App.tsx`, the `legacy: true` group in `NavMenu.tsx`, and retire
      `tests/smoke/vm_deployments_archive_history.spec.ts` + `vm_deployments_reconcile.spec.ts`'s `/vm-deployments`
      navigation targets. (repo: deployment-ui)
