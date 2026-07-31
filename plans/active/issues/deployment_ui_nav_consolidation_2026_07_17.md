---
doc_type: issue
title:
  deployment-ui nav consolidation — 4 nav surfaces reduced to 2 (shipped); 7 duplicate routes + a dropdown-vs-bar call
  remain operator-owned
summary: |
  Operator-driven nav audit + rebuild (2026-07-17). **Found**: the UI had **4 nav surfaces** (top-left dropdown,
  LandingTabs bar, cockpit tab bar, per-service tab bar) and **43 addressable page types of which only 31 are unique** —
  12 were the same component under a second chrome, because a 2026-06/07 refactor folded every surface into the cockpit
  and deleted nothing. **Shipped**: one deduplicated 15-entry list (`NAV_ITEMS_CANONICAL`) now drives BOTH remaining
  surfaces so they cannot drift; the LandingTabs bar is deleted and its 4 duplicate routes redirect into their cockpit
  tab; the top bar carries the page nav on every route; utilities collapsed behind a status chip. **Remains**: an
  operator call on dropdown-vs-bar, deletion of the 7 still-standalone duplicates, and three genuinely dead pages the
  audit found. Also documents why the `*` catch-all silently renders Overview for any unknown URL.
status: open
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
last_updated: 2026-07-17
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: ui_developer
resolved_by:
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

- [ ] [UI] P3. **RULED 2026-07-28 (was `[OPERATOR]`) — KEEP the always-visible top bar; DELETE the dropdown.** Reasoning
      applied from the operator's standing general ruling: none of the 8 explicit theme bullets
      (backfill/migration/cost/Databento/manifest-version/pause-unpause/auto-recovery/live-probing/adaptor-completion)
      names UI taste directly, but "Opt for full completions, no shortcuts, full functionality" does apply here on its
      own technical merits, not as a style preference — the two options are NOT functionally equivalent: the bar lives
      in the page Header, so it is reachable on EVERY route, while the dropdown (in its earlier cockpit location)
      demonstrably vanished on exactly the routes that navigate away from it — a real functional regression, not a taste
      difference. Keeping the option with full functionality on every route over the one with a known route-dependent
      gap is the "no shortcuts, full functionality" ruling applied concretely. Both currently render the same
      `NAV_ITEMS_CANONICAL` list, so this is a pure deletion, not a rebuild — delete the dropdown component + its
      now-redundant tests/mocks, keep the bar as the sole nav surface. `pw:L2 ✓` + cited regression spec covering the
      removal (confirm no orphaned route becomes unreachable once the dropdown is gone — the orphan-route audit this
      doc's own "Lessons" section flags as the real gate here).
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
- [ ] [UI] P3. **Delete the 3 dead pages** — `pages/DeploymentsList.tsx`, `pages/DeployTrigger.tsx`,
      `pages/DeploymentHistory.tsx`. Verified imported by nothing (they are an earlier generation of the UI); the
      workspace rule is "delete deprecated code, no shims". Check `api/deploymentApi.ts` / `types/deploymentTypes.ts`
      for consumers that die with them.
- [ ] [UI] P3. **Add a real 404 route** so `*` stops silently rendering Overview for unknown URLs. This is what let
      `/infra` "work" while showing the wrong screen for weeks — the bug was invisible precisely because the catch-all
      always renders _something_.
- [ ] [UI] P3. **Move the per-service shell onto real routes** — ~215 `/service/:name/:tab` URLs are regex-sniffed off
      the catch-all by `ServiceUrlSync`, which needs a 100-line bidirectional state↔URL sync with loop guards and
      "change attribution" only because `selectedService`/`activeTab` are component state instead of route params.
      Largest remaining source of routing complexity.

## Deferred work after 2026-07-17

| Item                                     | State                                                   | Why deferred / blocked on                                                                                                                                                                                                |
| ---------------------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Dropdown vs bar — keep one               | ✅ **RULED 2026-07-28**                                 | Keep the bar, delete the dropdown — functional edge (survives every route), not a taste call. See the retagged todo above.                                                                                               |
| Delete the 7 duplicate standalone routes | **Operator-owned**                                      | Operator wants to compare chromes first. Mechanical once decided.                                                                                                                                                        |
| Delete the 3 dead pages                  | **Not done**                                            | Blocked on nobody. Small + clear.                                                                                                                                                                                        |
| Real 404 instead of `*` → Overview       | **Not done**                                            | Blocked on nobody.                                                                                                                                                                                                       |
| Per-service shell → real routes          | **Not done**                                            | Blocked on nobody, but it is the biggest chunk; do it AFTER the dropdown/bar call so the nav is settled.                                                                                                                 |
| Diagnose the 5 mock/page row mismatches  | ✅ **Resolved 2026-07-28, gate fully green 2026-07-31** | Was NOT REPRODUCIBLE (2026-07-28) and the whole L2 gate is now 424/0 green (host-contention root cause, not app drift) — see `/plans/archive/issues/deployment_ui_l2_smoke_gate_red_2026_07_17.md` (archived, resolved). |
| `/ops/vms/:vmName` orphan route          | **Not done**                                            | Pre-existing, unchanged by this session; the orphan audit reports it every run.                                                                                                                                          |

**Note (2026-07-31, corrected — the "recommended NEXT" below is stale):** the 5 mock/page row mismatches this section
used to recommend chasing were already found NOT REPRODUCIBLE on 2026-07-28, and the referenced
`deployment_ui_l2_smoke_gate_red_2026_07_17.md` is now archived (resolved) — see
`/plans/archive/issues/deployment_ui_l2_smoke_gate_red_2026_07_17.md`. Remaining open items in the table above
(duplicate routes, dead pages, real 404, per-service shell, orphan route) are unaffected by this and still open.

## Progress Log

- **2026-07-28 (gated-decision retag sweep)** — Applied a ruling to the outstanding dropdown-vs-bar `[OPERATOR]`
  decision: keep the always-visible top bar, delete the dropdown — the doc's own recorded trade-off (the bar survives
  every route, the dropdown's earlier cockpit placement vanished on exactly the pages that navigate away) is a real
  functionality difference, so the "full functionality, no shortcuts" ruling determines the answer rather than leaving
  it as an open taste call. Retagged the todo from `[OPERATOR]` to `[UI]` with the ruling + reasoning written in, and
  updated the "Deferred work" table row to match. Docs-only, no code changed.

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
