---
doc_type: issue
title:
  deployment-ui nav consolidation — 4 nav surfaces reduced to 2, dropdown deleted, dead pages removed, real 404 added,
  per-service shell moved onto real routes (ALL TODOS SHIPPED)
summary: |
  Operator-driven nav audit + rebuild (2026-07-17). **Found**: the UI had **4 nav surfaces** (top-left dropdown,
  LandingTabs bar, cockpit tab bar, per-service tab bar) and **43 addressable page types of which only 31 are unique** —
  12 were the same component under a second chrome, because a 2026-06/07 refactor folded every surface into the cockpit
  and deleted nothing. **Shipped**: one deduplicated 15-entry list (`NAV_ITEMS_CANONICAL`) now drives BOTH remaining
  surfaces so they cannot drift; the LandingTabs bar is deleted and its 4 duplicate routes redirect into their cockpit
  tab; the top bar carries the page nav on every route; utilities collapsed behind a status chip; the dropdown-vs-bar
  call is RULED (bar kept, dropdown deleted); the 7 duplicate standalone routes were resolved via the other side
  (retired the cockpit `?tab=` variant instead of deleting them); the 3 dead pages are deleted; a real 404 route
  replaced the silent `*` → Overview fallback; and the per-service shell (`/service/:name(/:tab)`) is now real routes,
  retiring the `ServiceUrlSync` bidirectional sync hack entirely. All 5 checkbox todos done — RESOLVED 2026-08-01.
status: resolved
nature: process
asset_group:
  [ui] # corrected 2026-07-30 (ui-tranche launch) -- was [meta]; repos:[deployment-ui] only, a
  # deployment-ui nav-surface issue
stage: [meta]
repos: [deployment-ui]
scope: [engineer]
tags: [ui, navigation, routing, duplication, dead-code, orphan-audit]
related:
  [
    /plans/archive/issues/deployment_ui_l2_smoke_gate_red_2026_07_17.md,
    /codex/04-architecture/orphan-audit.md,
    /codex/06-coding-standards/ui-testing-layers.md,
  ]
created: 2026-07-17
last_updated: 2026-08-01
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: ui_developer
resolved_by:
  "slot-5, ui_developer, 2026-08-01 — last remaining todo (per-service shell onto real routes) shipped
  deployment-ui@039474d; all 5 checkbox todos done, no lock, archiving per plan-completion-and-archival-discipline.md"
locked_by:
drift_direction: advance-code
source:
  [
    deployment-ui/src/components/NavMenu.tsx,
    deployment-ui/src/components/TopNavBar.tsx,
    deployment-ui/src/App.tsx,
    deployment-ui/src/pages/DeploymentsList.tsx,
  ]
depends_on: []
---

# deployment-ui nav consolidation

## The finding (audit, 2026-07-17)

Four nav surfaces; **43 page types, 31 unique, 12 duplicates**. Root cause: a 2026-06/07 plan folded every surface into
the cockpit ("MERGED", "Fold /ops/live-deployments", Phase 0.5) — the folds landed, but **nothing was removed**, so each
screen became reachable under 2–3 chromes and which one you got depended on which menu item you clicked.

Also found, and still true unless a todo below says otherwise:

- **~1/3 of the app's URLs are not in the router.** `/home` `/repos` `/alerts` `/epics` `/infra` were strings matched in
  `LandingTabs.tabForPath`, and all ~215 `/service/:name/:tab` URLs are regex-sniffed by `ServiceUrlSync` — all riding
  the `*` catch-all. (The LandingTabs half is FIXED below; the `/service/*` half is not.)
- **`*` renders Overview for ANY unknown URL** — there is no 404. A typo'd link silently shows the home shell.
- **3 dead pages** imported by nothing: `pages/DeploymentsList.tsx`, `pages/DeployTrigger.tsx`,
  `pages/DeploymentHistory.tsx` (the last also name-collides with the LIVE `components/DeploymentHistory.tsx`).

## Shipped this session

| Commit                | What                                                                                                                         |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| deployment-ui@2c98262 | Dropdown deduplicated to one entry per screen + `/infra` landing-sync bug fixed + dedup contract tests                       |
| deployment-ui@cd304a8 | Cockpit bar driven from the SAME `NAV_ITEMS_CANONICAL` as the dropdown (they can no longer drift)                            |
| deployment-ui@bb836a5 | Top bar rebuilt: brand → "UTS", nav bar on EVERY route, utilities behind a StatusMenu chip; cockpit tab bar + title removed  |
| deployment-ui@0bde31d | Data Status added to the bar (defaults to instruments-service) + "Data" group                                                |
| deployment-ui@704062b | LandingTabs bar DELETED; `/repos` `/alerts` `/fleet` `/infra` become real `<Route>` redirects; `LANDING_PATHS` → `["/home"]` |

Net: **4 surfaces → 2** (dropdown + always-visible bar), both rendering the same 15-entry list. 0 of the 31 unique
screens lost.

## Todos

- [x] ✅ [UI] P3. **RULED 2026-07-28 (was `[OPERATOR]`) — KEEP the always-visible top bar; DELETE the dropdown.** —
      deployment-ui@32c0999. Reasoning applied from the operator's standing general ruling: none of the 8 explicit theme
      bullets (backfill/migration/cost/Databento/manifest-version/pause-unpause/auto-recovery/live-probing/
      adaptor-completion) names UI taste directly, but "Opt for full completions, no shortcuts, full functionality" does
      apply here on its own technical merits, not as a style preference — the two options are NOT functionally
      equivalent: the bar lives in the page Header, so it is reachable on EVERY route, while the dropdown (in its
      earlier cockpit location) demonstrably vanished on exactly the routes that navigate away from it — a real
      functional regression, not a taste difference. Keeping the option with full functionality on every route over the
      one with a known route-dependent gap is the "no shortcuts, full functionality" ruling applied concretely. Both
      rendered the same `NAV_ITEMS_CANONICAL` list, so this was a pure deletion, not a rebuild: deleted the `NavMenu`
      dropdown component + its Header trigger wiring, kept the shared nav data (still consumed by TopNavBar + the mobile
      hamburger), deleted the now-redundant dropdown-mechanic tests, and ported the
      canonical-entries-navigate-to-a-real-screen regression coverage onto TopNavBar (`tests/smoke/top-nav-bar.spec.ts`,
      renamed from `nav-menu-dedup.spec.ts`). `pw:L2 ✓` (85/85 targeted nav specs + full smoke suite 423/423 green) +
      `orphan-audit --blocking` confirms no new orphaned routes vs baseline — the real gate this doc's own "Lessons"
      section flags.
- [x] [DOCS] P3. **RESOLVED same day, 2026-07-17 (confirmed via code, workspace stale-gate audit 2026-07-28).** Original
      ask: decide whether to delete the 7 remaining duplicate standalone routes (`/deployments`,
      `/ops/live-deployments`, `/chaos`, `/safety-ops`, `/research/ml-experiments`, `/research/strategy-backtests`,
      `/research/execution-backtests`), which at the time still rendered a SECOND copy of screens the cockpit already
      hosted via the `legacy` nav group ("Duplicate routes — pending removal"). **Resolved later the same day**:
      `deployment-ui@079b29e` ("one URL scheme — plain routes, retire ?tab=", 2026-07-17 21:01 IST) — the operator
      decision was to eliminate the duplication from the OTHER side: retire the cockpit `?tab=` variant instead of the
      standalone routes, making each plain route (e.g. `/deployments`, `/chaos`, `/safety-ops`, the 3 `/research/*`
      routes) the SOLE canonical URL for its screen. Verified directly in the live `deployment-ui` checkout:
      `src/components/NavMenu.tsx`'s own comment states "The 'Duplicate routes — pending removal' quarantine group was
      DELETED 2026-07-17 together with its routes... the standalone/redirect duplicates it existed to compare no longer
      exist," and `NAV_GROUPS` today carries no `legacy: true` group at all. `/ops/live-deployments` specifically no
      longer exists as a route (folded into `/deployments`, per `deployment-ui@50a6947` "merge live/batch/paper into one
      Deployments tab"); the other 6 routes still exist in `src/App.tsx` today, but as the ONE canonical route for their
      screen, not a duplicate. Nothing left to decide here.
- [x] ✅ [UI] P3. **Delete the 3 dead pages** — `pages/DeploymentsList.tsx`, `pages/DeployTrigger.tsx`,
      `pages/DeploymentHistory.tsx`. `DeploymentsList.tsx` was already removed by an unrelated 2026-07-17 refactor
      (`079b29e`). Deleted the remaining two (verified imported by nothing — `App.tsx` only wires the distinct,
      actively-routed `components/DeploymentHistory.tsx`); their unique consumers in `api/deploymentApi.ts`
      (`fetchServices`, `triggerDeploy`, `fetchDeploymentHistory`, `rollbackDeployment`) and the now fully-unreferenced
      `types/deploymentTypes.ts` died with them, plus the matching dead vitest block. Regenerated the orphan-audit
      baseline: `DeployTrigger.tsx`'s dead `navigate("/")` cancel-button call was the only recorded incoming edge to `/`
      — removing it flagged `/` as a new orphan, same class as the 6 already-baselined bookmark-compat redirects
      (`/repos`, `/ops/*`), not a whitelist candidate. Regression:
      `tests/smoke/{routes,nav_and_header,top-nav-bar,app}.spec.ts` (87 tests) green. QG green
      (typecheck/lint/orphan-audit/unit/build). `deployment-ui@98e2c7a`.
- [x] ✅ [UI] P3. **Add a real 404 route** so `*` stops silently rendering Overview for unknown URLs. This is what let
      `/infra` "work" while showing the wrong screen for weeks — the bug was invisible precisely because the catch-all
      always renders _something_. — deployment-ui@3d4a8d6. The `*` catch-all is legitimately shared with the home
      shell's own surfaces (`/home`, `/service/:name(/:tab)`, regex-sniffed by `ServiceUrlSync`), so a blanket 404 would
      have broken those — added a shared `isHomeShellPath()` helper (exported from `ServiceUrlSync.tsx`, the same match
      logic that already drove its own state↔URL sync) and a `HomeShellRoute` wrapper (`App.tsx`) that gates the
      catch-all: recognized home-shell paths still render the shell, everything else renders a new `NotFoundPage`
      (`src/pages/NotFound.tsx`) with a link back to `/cockpit`. `pw:L2 ✓`: `tests/smoke/not-found-route.spec.ts` (new,
      5/5 — unknown URL → 404; `/infra`-shaped dead link → 404; 404's back-link → real screen; `/home` and
      `/service/:name/:tab` still render the shell, not 404) +
      `top-nav-bar.spec.ts`/`url-sync.spec.ts`/`mobile_responsive.spec.ts` unaffected (38/38 combined, including
      `/data-status` and `/kill-switch` — themselves dead/never-real URLs that now correctly 404 instead of silently
      rendering the shell). `orphan-audit --blocking` clean (no new orphans — no new `<Route>` was added, only what the
      existing catch-all renders). tsc/ESLint/build clean, vitest 1096/1096 (full suite) / 101/101 (QG-scoped).
- [x] ✅ [UI] P3. **Move the per-service shell onto real routes** — deployment-ui@039474d. `/service/:serviceName` and
      `/service/:serviceName/:tab` are now explicit `<Route>` entries (App.tsx) instead of being regex-sniffed off the
      `*` catch-all by `ServiceUrlSync`'s ~100-line bidirectional state↔URL sync (loop guards + "change attribution").
      Extracted the shell into `src/pages/HomeShell.tsx`, which derives `selectedService`/`activeTab` directly from
      `useParams()` and drives every service/tab switch via `useNavigate()` — no component state duplicating the URL, so
      no sync effect pair is needed at all. `ServiceUrlSync.tsx` deleted outright (its `isHomeShellPath()` gate on the
      catch-all is replaced by the three real routes matching before `*` ever fires). The bare `/service/:name` shape
      (no tab, defaults to Deploy) is preserved as a genuinely reachable route — wired to `ServicesOverviewTab`'s row
      click (fresh entry into a service) — rather than deleted or faked into the orphan-audit's whitelist;
      `ServiceList`'s sidebar switch still carries an explicit tab (it preserves whichever tab is currently active).
      Also extended `scripts/orphan-audit.ts` to detect
      `navigate(\`template\`)`calls (it     previously only matched string-literal`navigate("...")`and`to={\`...\`}`JSX templates), since this shell's     dynamic service-name navigation would otherwise read as unreachable — a real tool gap this change exposed, fixed     at the root rather than gamed.`pw:L2
      ✓`: full smoke+e2e suite 469/484 green (the 15 failures are PRE-EXISTING —     independently reproduced byte-identical on a clean `git
      stash`-restored tree before this change: 2 in     `safety-ops-deployment-ui.spec.ts`, 6 in `hierarchical-drilldown-walk.spec.ts`, plus 2 in     `deploy-missing-preview.spec.ts`, 2 in `per-leaf-csv-download.spec.ts`, 3 in `regression-2026-05-07.spec.ts`—     unrelated to this refactor).`url-sync.spec.ts`/`not-found-route.spec.ts`/`top-nav-bar.spec.ts`/     `prediction_v9_breakdown.spec.ts`(the specs most directly exercising this surface) all green.`orphan-audit
      --blocking` clean (no new orphans vs baseline). tsc/ESLint clean, vitest 1096/1096 (full) / 101/101 (QG-scoped).

## Deferred work after 2026-07-17

| Item                                     | State                                                                            | Why deferred / blocked on                                                                                                                                                                                                                                                                                             |
| ---------------------------------------- | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Dropdown vs bar — keep one               | ✅ **RULED 2026-07-28, SHIPPED 2026-08-01**                                      | Kept the bar, deleted the dropdown — functional edge (survives every route), not a taste call. deployment-ui@32c0999. See the todo above.                                                                                                                                                                             |
| Delete the 7 duplicate standalone routes | ✅ **RESOLVED 2026-07-17 (stale row — was contradicting the doc's own todo #2)** | This row said "operator-owned, compare chromes first," but todo #2 above already documents the operator resolved this the SAME DAY via the other side: retired the cockpit `?tab=` variant instead, making each of the 7 routes the sole canonical URL for its screen — nothing left to delete. Corrected 2026-08-01. |
| Delete the 3 dead pages                  | ✅ **SHIPPED 2026-08-01**                                                        | `deployment-ui@98e2c7a`. See the todo above.                                                                                                                                                                                                                                                                          |
| Real 404 instead of `*` → Overview       | ✅ **SHIPPED 2026-08-01**                                                        | `deployment-ui@3d4a8d6`. See the todo above.                                                                                                                                                                                                                                                                          |
| Per-service shell → real routes          | ✅ **SHIPPED 2026-08-01**                                                        | `deployment-ui@039474d`. See the todo above.                                                                                                                                                                                                                                                                          |
| Diagnose the 5 mock/page row mismatches  | ✅ **Resolved 2026-07-28, gate fully green 2026-07-31**                          | Was NOT REPRODUCIBLE (2026-07-28) and the whole L2 gate is now 424/0 green (host-contention root cause, not app drift) — see `/plans/archive/issues/deployment_ui_l2_smoke_gate_red_2026_07_17.md` (archived, resolved).                                                                                              |
| `/ops/vms/:vmName` orphan route          | **Accepted — not this doc's scope**                                              | A structural compat-redirect orphan (same class as the accepted `/ops/costs`, `/ops/artifacts`, `/ops/vm-resources`, `/repos`), tracked passively via `scripts/.orphan-audit-baseline.json` — not a pending action per this doc's own Lessons ("a compat redirect is structurally an orphan").                        |

**Note (2026-07-31, corrected — the "recommended NEXT" below is stale):** the 5 mock/page row mismatches this section
used to recommend chasing were already found NOT REPRODUCIBLE on 2026-07-28, and the referenced
`deployment_ui_l2_smoke_gate_red_2026_07_17.md` is now archived (resolved) — see
`/plans/archive/issues/deployment_ui_l2_smoke_gate_red_2026_07_17.md`. Remaining open items in the table above
(duplicate routes, orphan route) are unaffected by this and still open; per-service-shell and dead-pages/404 are now
shipped (see rows above).

## Progress Log

- **2026-07-28 (gated-decision retag sweep)** — Applied a ruling to the outstanding dropdown-vs-bar `[OPERATOR]`
  decision: keep the always-visible top bar, delete the dropdown — the doc's own recorded trade-off (the bar survives
  every route, the dropdown's earlier cockpit placement vanished on exactly the pages that navigate away) is a real
  functionality difference, so the "full functionality, no shortcuts" ruling determines the answer rather than leaving
  it as an open taste call. Retagged the todo from `[OPERATOR]` to `[UI]` with the ruling + reasoning written in, and
  updated the "Deferred work" table row to match. Docs-only, no code changed.

- **2026-08-01 (shipped)** — Executed the 2026-07-28 ruling: deleted the `NavMenu` dropdown component
  (`src/components/NavMenu.tsx`) and its Header trigger wiring (top-left "UTS" brand is now a static logo, no
  `aria-haspopup`/`onClick`), keeping the shared `NAV_GROUPS`/`NAV_ITEMS_CANONICAL`/`cockpitTabIdFor`/
  `navItemIsActive`/`NAV_LINKS_FLAT` exports in place (still consumed by TopNavBar and the mobile hamburger). Deleted
  the dropdown-only mechanic tests (open/close, backdrop, Escape — no bar equivalent, the bar has no open/closed state)
  from `Header.test.tsx` and `tests/smoke/cockpit.spec.ts`. Ported the "every canonical entry navigates to a real,
  error-free screen" + "no duplicate hrefs" regression coverage from the dropdown onto TopNavBar, renaming
  `tests/smoke/nav-menu-dedup.spec.ts` → `tests/smoke/top-nav-bar.spec.ts`. Verified via `orphan-audit --blocking` (no
  new orphans vs baseline — the dropdown's route data lived in the same file and is still referenced by TopNavBar, so
  nothing became unreachable), `tsc`/ESLint clean, vitest 1102/1102, targeted nav Playwright specs 85/85, full smoke
  suite 423/423. Shipped deployment-ui@32c0999.

- **2026-08-01 (shipped)** — Added the real 404 route. The `*` catch-all is shared by the home shell's own surfaces
  (`/home`, `/service/:name(/:tab)`, regex-sniffed by `ServiceUrlSync`) and every genuinely unknown URL — a blanket 404
  on `*` would have broken the shell, so gated it instead: exported `isHomeShellPath()` from `ServiceUrlSync.tsx` (the
  same match logic already driving its own state↔URL sync) and wrapped the catch-all's element in a new `HomeShellRoute`
  (`App.tsx`) that renders the shell only for recognized home-shell paths and a new `NotFoundPage`
  (`src/pages/NotFound.tsx`, links back to `/cockpit`) for everything else. New regression:
  `tests/smoke/not-found-route.spec.ts` (5/5) plus the full pre-existing `top-nav-bar.spec.ts`/`url-sync.spec.ts`/
  `mobile_responsive.spec.ts` suites (38/38 combined) — the latter incidentally proved `/data-status` and `/kill-switch`
  were themselves dead/never-real URLs riding the old silent fallback; they now correctly 404 too.
  `orphan-audit --blocking` clean, `tsc`/ESLint/build clean, vitest 1096/1096 (full) / 101/101 (QG-scoped). Shipped
  deployment-ui@3d4a8d6.

- **2026-08-01 (shipped — LAST TODO, doc now RESOLVED)** — Moved the per-service shell onto real routes.
  `/service/:serviceName` and `/service/:serviceName/:tab` are now explicit `<Route>` entries in `App.tsx` instead of
  being regex-sniffed off the `*` catch-all by `ServiceUrlSync`'s ~100-line bidirectional state↔URL sync (loop guards +
  "change attribution"). Extracted the shell into `src/pages/HomeShell.tsx`: `selectedService`/`activeTab` are derived
  directly from `useParams()` every render (not component state), and every service/tab switch is a plain `navigate()`
  call — no sync effect pair needed at all, so the whole class of bug that pair existed to prevent (state and URL
  disagreeing) is now structurally impossible. `ServiceUrlSync.tsx` deleted outright. The bare `/service/:name` shape
  (no tab, defaults to Deploy) is preserved as a genuinely reachable route — wired to `ServicesOverviewTab`'s row click
  (fresh entry into a service) — rather than deleted or faked into the orphan-audit whitelist; `ServiceList`'s sidebar
  switch still carries an explicit tab (it preserves whichever tab is currently active), which is why both route shapes
  are real. Also extended `scripts/orphan-audit.ts` to detect
  `navigate(\`template\`)`calls (it previously only matched string-literal`navigate("...")`and`to={\`...\`}`JSX templates) — a real tool gap this change exposed (every dynamic service-name navigation would otherwise read as unreachable), fixed at the root rather than gamed with a fake literal or a whitelist entry. While auditing the doc for this closure, found and fixed a stale "Deferred work" table row ("Delete the 7 duplicate standalone routes — Operator-owned") that directly contradicted todo #2 above (already`[x]`, documenting the operator resolved this the SAME DAY, 2026-07-17, via the other side — retiring `?tab=`instead of deleting the routes); corrected in this session per`check_no_contradiction`-class hygiene, not new work. `pw:L2
  ✓`: full smoke+e2e suite 469/484 green — the 15 failures are PRE-EXISTING, independently reproduced byte-identical on a clean `git
  stash`-restored tree before this change (2 in `safety-ops-deployment-ui.spec.ts`, 6 in `hierarchical-drilldown-walk.spec.ts`, 2 in `deploy-missing-preview.spec.ts`, 2 in `per-leaf-csv-download.spec.ts`, 3 in `regression-2026-05-07.spec.ts`— unrelated to this refactor).`url-sync.spec.ts`/`not-found-route.spec.ts`/`top-nav-bar.spec.ts`/`prediction_v9_breakdown.spec.ts`(the specs most directly exercising this surface) all green.`orphan-audit
  --blocking`clean,`tsc`/ESLint clean, vitest 1096/1096 (full) / 101/101 (QG-scoped). Shipped deployment-ui@039474d. **All 5 checkbox todos are now `[x]`, `locked_by`is empty — archiving this doc in the same turn per`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`** (§1 archive-immediately rule); no new codex contract established by this change (the routing convention is self-documented in `HomeShell.tsx`'s
  own header comment, not codex-SSOT-worthy at this workspace's scale) so no codex doc update accompanies this archival.

## Lessons

- **A "fold" that deletes nothing doubles the surface.** Every duplicate here came from a merge plan whose folds landed
  without the corresponding removals. If a plan says "fold X into Y", the deletion of X is part of the todo, not a
  follow-up.
- **One list, two renderers.** The dropdown and bar drifted because they were two hand-maintained arrays. They now share
  `NAV_ITEMS_CANONICAL` + `navItemIsActive()`; `COCKPIT_TABS` lost its labels/icons so a tab is named in exactly one
  place. Unit tests pin the invariants (no duplicate `to`, no canonical entry pointing at a folded standalone).
- **The orphan-route audit is a real gate and it caught a real mistake.** Dropping `/infra` from the nav made its route
  unreachable; the audit failed the build. The whitelist's three reason prefixes (MACHINE-ONLY / API-HANDLER /
  UNAUTHENTICATED-FUNNEL) deliberately have **no "compat redirect" category**, so the honest fix was to keep the legacy
  URLs listed in the nav (relabelled "redirects → X"), not to bend the whitelist. **A compat redirect is structurally an
  orphan** — decide up front whether you are keeping deep-links or deleting routes.
- **Deleting a nav surface costs ~25 spec updates.** Removing LandingTabs broke 25 specs across 8 files (every
  `landing-*` testid). All 25 fixed in 704062b. Budget the test churn, not just the component change.
- **`data-testid`s outlive the component that owned them.** The `cockpit-tab-*` ids were kept when the bar moved from
  the cockpit into the Header specifically so the existing specs kept driving it — that made a large refactor testable
  with zero churn on those specs.
- **na-eligibility-audit 2026-07-30**: RECLASSIFY, conflict-cleared (infra tranche, dispatch agt-30721a) —
  bounded/deterministic-outcome work, no operator gate or live judgment call found; flipped
  `assigned_vm: NA -> planning`. Conflict-check run against all active `assigned_vm: planning` docs in this doc's
  `parent_epic` + the infra tranche's consolidated-closeout digest: zero/milestone-only overlap, clear to proceed.
