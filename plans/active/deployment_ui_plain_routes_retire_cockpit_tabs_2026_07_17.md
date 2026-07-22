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

- [x] ✅ [UI] P0. ~~Layout-route scaffold~~ — **not needed** (deployment-ui@079b29e). Discovered on inspection that the
      shared chrome (`Header` + `TopNavBar`) ALREADY lives above `<Routes>` in `App.tsx`, and
      `LifecyclePrefetchProvider` is mounted per-subtab, not at cockpit level — so there is no cross-pane state to
      preserve and no `<Outlet/>` layout route is required. Each pane is a plain top-level route with its own `<main>`
      wrapper; the chrome persists for free. `/cockpit` stays the health rollup (`CockpitHealth`).
- [x] ✅ [UI] P0. `Deployments.tsx` — collapsed all 7 `embedded ?` branches onto the URL; deleted the `localX` state +
      the `embedded` prop. `/deployments?umbrella=batch&status=failed` now applies BOTH filters (proven: the
      `deployments-page.spec.ts` status=failed deep-link test passes unweakened). `onDrill` kept (slide-over).
      deployment-ui@079b29e.
- [x] ✅ [UI] P0. `DeploymentDetail.tsx` — its 2 `embedded` branches are the `div`-vs-`main` wrapper + back-link toggle
      for the slide-over (NOT a URL dual-path), so they are correct and KEPT. Only `Deployments.tsx` had the URL
      dual-path. deployment-ui@079b29e.
- [x] ✅ [UI] P0. Converted the 10 tab bodies to plain routes: `CockpitHealth`=/cockpit, `CockpitDeploy`=/deploy,
      `DeploymentsPage`=/deployments, `CockpitFleet`=/fleet, `CockpitConsolidators`=/consolidators, `CockpitCi`=/ci,
      `CockpitAlerts`=/alerts, `CockpitLaunch`=/launch, `CockpitChaos`=/chaos, `CockpitSafety`=/safety-ops. Retired
      `searchParams.get("tab")` + `VALID_TABS` + `onTabChange`. deployment-ui@079b29e.
- [x] ✅ [UI] P1. `NAV_GROUPS` SSOT → plain routes; `cockpitTabIdFor`/`navItemIsActive` match plain paths (kept the
      `cockpit-tab-*` vs `cockpit-navlink-*` testid split via a route→tabId map so specs keep driving the bar). Deleted
      the `legacy: true` "Duplicate routes — pending removal" group + its render block. deployment-ui@079b29e.
- [x] ✅ [UI] P1. Deleted `/ops/live-deployments` (`LiveDeploymentsContent` now renders in `DeploymentsPage`) + dead
      `pages/DeploymentsList.tsx` + its test. Kept `/vm-deployments` + `/deployments/:name` (Alerts deep-links to the
      latter; verified `alerts-page.spec.ts` still targets it). deployment-ui@079b29e.
- [x] ✅ [UI] P1. Swept the `src` `?tab=` refs → plain paths (`Cockpit.tsx` tiles + CONSOLES, `DeploymentDetail`
      consolidator/redeploy links, `VmControls`, `FleetInfra` href). `/repos`→`/ci`, `/infra`→`/fleet` kept as
      bookmark-compat redirects (no nav entry). deployment-ui@079b29e.
- [x] ✅ [UI] P1. Swept the test `?tab=` refs → plain paths across 9 spec files (`nav-menu-dedup` CANONICAL table,
      `cockpit`, `deployments-*`, `fleet-*`, `repos-tab`, `url-sync`, `nav_and_header`, `accessibility_audit`). The
      deep-link assertions were KEPT and pass on the canonical surface — the proof the bug is fixed.
      deployment-ui@079b29e.
- [x] ✅ [REVIEW] P1. Refreshed `scripts/.orphan-audit-baseline.json` (adds the 2 intentional compat redirects `/repos`,
      `/infra` as known orphans); `npm run orphan-audit:blocking` → ✅ no new orphans. deployment-ui@079b29e.
- [x] ✅ [REVIEW] P1. Gates green: `type-check` clean, `lint` clean, vitest **987 passed**, orphan-audit green, build
      passes; **pw:L2 ✓** full smoke suite **364 passed** — regression specs `nav-menu-dedup.spec.ts` +
      `deployments-page.spec.ts` (deep-link proof) + `cockpit.spec.ts` all green. The 7 remaining playwright failures
      are PRE-EXISTING in `CostObservability.tsx` (a11y span + DailyCosts, 5) and `Header.tsx` (mobile hamburger
      strict-mode) — untouched files, verified failing identically at HEAD via stash. deployment-ui@079b29e.
- [x] ✅ [INFRA] P1. Shipped via quickmerge `--agent --files` — deployment-ui@079b29e landed on live-defi-rollout;
      flipping these checkboxes in the same turn (`docs(plans):`).
- [ ] [REVIEW] P2. Post-phase doc audit: (a) ✅ DONE 2026-07-21 (plan-reconcile consolidation pass) —
      `deployment_observability_expansion_2026_07_08.md`'s `[UI] P3 ✅ KEEP (operator-confirmed 2026-07-11)` decision
      now carries a `⚠️ SUPERSEDED 2026-07-21` note recording that the "alongside the cockpit tab" framing is stale (no
      cockpit tab remains to be "alongside"), while the underlying KEEP-the-route decision still holds. (b) STILL OPEN —
      stub/refresh the routing convention in codex so "plain routes, one scheme, layout route for shared chrome" is the
      written rule and the `?tab=` pattern cannot regrow (checked `codex/06-coding-standards/` — no existing doc covers
      this; `ui-testing-layers.md` covers the route-smoke _test_ layer, not the URL-scheme _convention_ — needs a new
      stub or a new section in an existing doc).

## Success criteria

- ONE URL scheme: every screen has exactly one plain canonical URL; `?tab=` resolves nowhere and
  `searchParams.get("tab")` is gone.
- `/deployments?umbrella=batch&status=failed` applies BOTH filters (the deep-link bug is fixed, proven by the existing
  smoke assertions passing unweakened).
- No `embedded ?` URL dual-path remains in `Deployments.tsx` (the 2 in `DeploymentDetail.tsx` are the slide-over wrapper
  toggle, not a URL path — correctly kept).
- The shared shell does NOT remount between screens (Header+TopNavBar live above `<Routes>`, no layout route needed),
  and `/cockpit` still renders the health rollup.
- Nav uses plain routes only; the legacy quarantine group and its routes are gone together; orphan-audit green.
- tsc + ESLint + Vitest + Playwright green; pw:L2 ✓ cited.

## Progress Log

- **2026-07-17 (slot 5, Opus — local)** — Plan authored from the interactive design decision. Prior work in the tree was
  STASHED (`stash@{0}` "obsolete-2026-07-17: /deployments deletion + ?tab= test retarget") — it deleted `/deployments`
  and retargeted the smoke specs ONTO `?tab=`, i.e. exactly backwards under this decision. The two salvageable pieces
  from it are already captured as todos here (delete `/ops/live-deployments`; delete the dead `DeploymentsList.tsx`).
  The 3 honestly-failing deep-link tests from that attempt are the evidence motivating this plan — they are the
  regression proof to keep GREEN at the end.

- **2026-07-17 (slot 5, Opus — local) — SHIPPED deployment-ui@079b29e.** All 11 build/ship todos done in one pass (only
  the P2 doc-audit remains). Two design facts simplified it below the 0.8-day estimate:
  1. **No layout route needed** — the shared chrome already lives above `<Routes>`, so each pane is just a plain
     top-level route with its own `<main>`; the chrome persists for free.
  2. **DeploymentDetail's `embedded` is NOT a URL dual-path** — it toggles the `div`/`main` wrapper + back-link for the
     slide-over, so it stayed. Only `Deployments.tsx` carried the URL dual-path (7 branches), which is the deep-link bug
     this fixes. The refactor was remarkably clean: after the src edits, `tsc` flagged exactly 3 dangling refs (1
     caller + 2 test imports). Final gates: tsc + eslint clean, vitest **987 passed**, orphan-audit green, build green,
     playwright smoke **364 passed**. The 7 remaining playwright failures are PRE-EXISTING (CostObservability
     a11y/DailyCosts + Header mobile hamburger) — untouched files, verified failing identically at HEAD by stashing this
     work and re-running. They are out of scope (different files/agents) and flagged to the operator.
- **STASH CLEANUP:** the obsolete `stash@{0}` from the first (backwards) attempt can be dropped — every salvageable
  piece landed in 079b29e. Left in place for the operator to drop (`git stash drop` is agent-banned on foreign WIP, but
  this one is mine — dropping it is safe once the operator confirms).

## Codex SSOTs

- `codex/06-coding-standards/ui-testing-layers.md` — the UI gate (tsc/ESLint/Vitest/Playwright; pw:L2 + cited spec).
