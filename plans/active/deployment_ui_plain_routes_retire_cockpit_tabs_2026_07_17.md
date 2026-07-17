---
doc_type: plan
title: deployment-ui — one URL scheme — plain routes, retire `?tab=`
summary: >-
  The UI mixes two URL schemes — plain `/vm-deployments` and `/cockpit?tab=deployments` — so the same screen is
  reachable two ways and which chrome you get depends on which link you clicked. Standardise on PLAIN routes and retire
  the `?tab=` scheme, using a React Router layout route to keep the cockpit's shared chrome + prefetch context. This
  also FIXES a real bug the tab scheme caused: because the cockpit shell owns the URL, embedded tabs cannot own their
  query params, so `DeploymentsContent` abandons the URL for local state when embedded — silently losing filter
  deep-linking.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [deployment-ui]
scope: [engineer]
tags: [deployment-ui, routing, url-scheme, refactor, cockpit, deep-link]
related:
  - deployment_observability_expansion_2026_07_08.md
created: "2026-07-17"
last_updated: "2026-07-17"
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
assigned_role: ui_developer
model_tier: opus-required
drift_direction: advance-code
sequential: true
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source: operator decision 2026-07-17 (interactive session — "keep the plain, remove the cockpit?tab= format")
---

# deployment-ui — one URL scheme: plain routes, retire `?tab=`

> **Dispatch:** local/interactive (`assigned_vm: NA`, `execution_scope: local-only`) — same track as the rest of this
> session's work. **Operator decision 2026-07-17**: keep plain `/page` URLs, remove the `/cockpit?tab=page` scheme.

> **🟡 CROSS-AGENT — READ BEFORE STARTING.** This REVERSES the direction `harshkantariya [slot-2·harsh_pc]` drove on
> 2026-07-17 (5 commits, 12:33→15:21: "one entry per screen", "drive the cockpit bar from the same SSOT", "delete the
> LandingTabs bar — redirect its duplicates into the cockpit"), which folded standalone pages INTO cockpit tabs and
> pointed the nav at tabs. `Cockpit.tsx` / `NavMenu.tsx` / `App.tsx` are his recently-touched files. The operator
> authorised this reversal interactively (2026-07-17, "i was doing that but now working on different surface — you go
> ahead"). **Do not start a second agent in these files concurrently** (workspace rule: different repos safe, same file
> never).

## Context (read first — self-contained)

Two schemes coexist today:

- **Plain**: `/cockpit`, `/home`, `/epics`, `/vm-deployments`, `/vm-deployments/:id`, `/deployments`,
  `/deployments/:name`, `/chaos`, `/safety-ops`, `/ops/costs`, `/ops/vms/:vmName`, `/ops/live-deployments`,
  `/research/*`, `/service/:svc/data-status`.
- **Tab**: `/cockpit?tab={health,deploy,deployments,fleet,consolidators,ci,alerts,launch,chaos,safety}` (10 tabs,
  [`Cockpit.tsx:1348`](../../deployment-ui/src/pages/Cockpit.tsx) — `searchParams.get("tab") ?? "health"`).

**Why plain wins (evidence, not taste).** The cockpit shell OWNS the URL, so an embedded tab cannot own its own query
params without colliding with `?tab=`. That forced the dual-path in
[`Deployments.tsx:998`](../../deployment-ui/src/pages/Deployments.tsx):

```ts
// Embedded filters live in local state (no URL writes); standalone reads/writes the URL.
const statusFilter = embedded ? localStatus : (searchParams.get("status") ?? "running");
```

So `/cockpit?tab=deployments&status=failed` **silently ignores `status`** — filter deep-linking exists ONLY on the
standalone `/deployments`. Measured 2026-07-17: retargeting the smoke specs onto the tab made 3 deep-link tests fail
honestly (`umbrella=batch` / `status=failed` never applied). Plain `/deployments?status=failed` has no such collision,
and collapsing the dual-path deletes ~9 `embedded ?` branches.

**Why it's cheaper than it looks.** All 10 tab bodies are ALREADY extracted as chrome-less `*Content` components — the
exact precondition a layout route needs. This is rewiring, not rewriting; `Cockpit.tsx` (1473 lines) mostly becomes a
shell. Only **2 files** carry real `embedded ?` branches (`Deployments.tsx` 7, `DeploymentDetail.tsx` 2).

**Measured blast radius (2026-07-17):** 10 tabs · 2 files with dual-paths (9 branches) · 29 `?tab=` refs in `src` · ~112
in tests · top bar = 10 `cockpit-tab-*` + 5 `cockpit-navlink-*` (converting makes all 15 uniform NavLinks).

**Gotchas (must honour):** `/cockpit` STAYS as the health rollup — it just stops being a router. Keep the shared shell
(`LifecyclePrefetchContext`, top bar) via a **layout route** so tab switches don't remount/refetch — losing that is the
one real cost of naive deletion. `scripts/orphan-audit.ts` fails any declared route with no inbound `<Link>`, and its
whitelist has NO "compat redirect" category — so nav entries + routes must move together. UI gates only (tsc / ESLint /
Vitest / Playwright — no Python). Playwright **L2** evidence + a cited regression spec is required per tick
(`codex/06-coding-standards/ui-testing-layers.md`).

## Todos

- [ ] [UI] P0. Layout-route scaffold: add a `<CockpitLayout>` route element carrying the shared chrome (top bar +
      `LifecyclePrefetchContext` + `ErrorBoundary`) with an `<Outlet/>`, and nest the tab screens under it so switching
      screens does NOT remount the shell or refetch. `/cockpit` remains the health rollup (its own nested index route),
      no longer a router. No behaviour change yet — both schemes still resolve.
- [ ] [UI] P0. `Deployments.tsx` — collapse the 7 `embedded ?` branches onto the URL-backed path (mode/`umbrella`,
      cloud, status, asset_group, kind, launched_by, region). Delete the `localX` state + the `embedded` prop. THE
      DEEP-LINK FIX: `/deployments?umbrella=batch&status=failed` must apply both filters. Keep `onDrill` (the slide-over
      is a legitimate presentation choice, independent of the URL scheme).
- [ ] [UI] P0. `DeploymentDetail.tsx` — collapse its 2 `embedded ?` branches the same way; keep the slide-over embed.
- [ ] [UI] P0. Convert the 10 `TabsContent` bodies into nested plain routes under the layout: `/deployments` (already
      exists — keep, it is canonical), plus `/deploy`, `/fleet`, `/consolidators`, `/ci`, `/alerts`, `/launch`,
      `/chaos`, `/safety-ops`, and `/cockpit` (health). Reuse each existing `*Content` verbatim. Retire
      `searchParams.get("tab")` + `VALID_TABS` + `onTabChange`.
- [ ] [UI] P1. `NAV_GROUPS` SSOT (`NavMenu.tsx`) → plain routes only; the top bar becomes 15 uniform NavLinks (kills the
      `cockpit-tab-*` vs `cockpit-navlink-*` split — the very inconsistency that motivated this). Delete the
      `legacy: true` "Duplicate routes — pending removal" group AND its routes together (orphan-audit rule).
- [ ] [UI] P1. Delete the now-genuinely-duplicate surfaces: `/ops/live-deployments` (its `LiveDeploymentsContent`
      renders inside `/deployments`) and the dead `pages/DeploymentsList.tsx` + its test (verified 2026-07-17: 0
      non-test refs). Keep `/vm-deployments` and `/deployments/:name` (Alerts deep-links to the latter).
- [ ] [UI] P1. Sweep the 29 `?tab=` refs in `src` → plain paths (incl. `Cockpit.tsx` `CONSOLES`, redirect routes
      `/repos` `/alerts` `/fleet` `/infra`, and any `to="/cockpit?tab=..."`).
- [ ] [UI] P1. Sweep the ~112 `?tab=` refs across `tests/` + `*.test.tsx` → plain paths. `nav-menu-dedup.spec.ts`'s
      `CANONICAL` table is the SSOT list to rewrite; `deployments-page.spec.ts` keeps its deep-link assertions (they
      should now PASS on the canonical surface — that is the proof the bug is fixed, so do NOT weaken them).
- [ ] [REVIEW] P1. Refresh `scripts/.orphan-audit-report.json` baseline; `npm run orphan-audit:blocking` green with no
      NEW orphans.
- [ ] [REVIEW] P1. Gates: `npm run type-check` + `npm run lint` + `npm run test -- --run` (979+ passing) +
      `npx playwright test` green. **pw:L2 ✓** cited with the regression spec name per the UI gate.
- [ ] [INFRA] P1. Ship (quickmerge `--agent --files`, cite sha) + flip these checkboxes in the SAME turn
      (`docs(plans):`).
- [ ] [REVIEW] P2. Post-phase doc audit: (a) `deployment_observability_expansion_2026_07_08.md` carries a now-SUPERSEDED
      `[UI] P3 ✅ KEEP (operator-confirmed 2026-07-11)` decision on the standalone `/deployments` route — its stated
      rationale ("URL-param-backed mode + filters for alert deep-links") is exactly what this plan makes universal;
      record the supersession rather than silently contradicting it. (b) Stub/refresh the routing convention in codex so
      "plain routes, one scheme, layout route for shared chrome" is the written rule and the `?tab=` pattern cannot
      regrow.

## Success criteria

- ONE URL scheme: every screen has exactly one plain canonical URL; `?tab=` resolves nowhere and
  `searchParams.get("tab")` is gone.
- `/deployments?umbrella=batch&status=failed` applies BOTH filters (the deep-link bug is fixed, proven by the existing
  smoke assertions passing unweakened).
- No `embedded ?` dual-paths remain in `Deployments.tsx` / `DeploymentDetail.tsx`.
- The shared shell still does NOT remount between screens (layout route), and `/cockpit` still renders the health
  rollup.
- Nav = 15 uniform NavLinks; the legacy quarantine group and its routes are gone together; orphan-audit green.
- tsc + ESLint + Vitest + Playwright green; pw:L2 ✓ cited.

## Progress Log

- **2026-07-17 (slot 5, Opus — local)** — Plan authored from the interactive design decision. Prior work in the tree was
  STASHED (`stash@{0}` "obsolete-2026-07-17: /deployments deletion + ?tab= test retarget") — it deleted `/deployments`
  and retargeted the smoke specs ONTO `?tab=`, i.e. exactly backwards under this decision. The two salvageable pieces
  from it are already captured as todos here (delete `/ops/live-deployments`; delete the dead `DeploymentsList.tsx`).
  The 3 honestly-failing deep-link tests from that attempt are the evidence motivating this plan — they are the
  regression proof to keep GREEN at the end.

## Codex SSOTs

- `codex/06-coding-standards/ui-testing-layers.md` — the UI gate (tsc/ESLint/Vitest/Playwright; pw:L2 + cited spec).
