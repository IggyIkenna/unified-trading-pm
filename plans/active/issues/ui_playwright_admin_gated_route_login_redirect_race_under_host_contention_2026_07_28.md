---
doc_type: issue
title:
  "Playwright specs targeting admin-gated `(platform)` routes intermittently redirect to /login under host contention —
  affects multiple ALREADY-SHIPPED pw:L2-cited specs, not just new work"
summary:
  "While writing the Batch 5 retroactive-Playwright-evidence spec for
  ui_hardcoded_colour_and_localhost_debt_2026_07_21.md, discovered that unified-trading-system-ui Playwright specs which
  seed a synthetic admin persona via `localStorage['portal_user']`/`['portal_token']` (the DemoAuthProvider convention,
  per tests/e2e/playbooks/seed-persona.ts) and navigate to an admin-gated `(platform)` route intermittently land on
  `/login` instead of the target page. Reproduced against TWO pre-existing, unmodified, already-`pw:L2`-cited specs this
  session touched nothing in (tests/smoke/research-real-data.smoke.spec.ts targeting /services/research/execution +
  /paper-trading, and tests/smoke/trading-predictions-colour-migration.smoke.spec.ts targeting
  /services/trading/strategies/... + /services/dart/terminal) under measured extreme host contention (`uptime` load
  averages 13-65 on a 10-core dev machine during this session) — confirming the flakiness is environmental and
  cross-cutting, not specific to any one route or spec. Matches the exact same host-contention blocker class already
  documented by Batches 1 and 4 of the parent issue doc (load 27-35 on 8 cores there); this session's load was
  measurably worse. Not fixed here — root-caused only far enough to rule out a regression in this session's own changes;
  the underlying race (DemoAuthProvider.restore()'s async `fetchAssignedSlotsFromStore` fetch vs. whatever route guard
  fires the redirect) needs a slot with normal host load to reproduce cleanly and fix at the source (e.g. block the
  guard's redirect decision on the restore-promise settling, not on a synchronous localStorage read)."
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer]
tags: [ui, playwright, flaky-test, auth, host-contention, quality-gates]
related:
  [
    /plans/archive/issues/ui_hardcoded_colour_and_localhost_debt_2026_07_21.md,
    /codex/06-coding-standards/ui-testing-layers.md,
  ]
created: "2026-07-28"
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: ui_developer
drift_direction: advance-code
source: [ui_hardcoded_colour_and_localhost_debt_2026_07_21-batch5-retroactive-evidence]
resolved_by:
locked_by:
depends_on: []
---

## What I found

Writing `tests/smoke/marketing-platform-misc-colour-migration.smoke.spec.ts` (the Batch 5
retroactive-Playwright-evidence spec), the two sub-tests that navigate to an admin-gated `(platform)` route
(`/services/research/strategy/heatmap`, seeded via the standard `localStorage['portal_user']`/`['portal_token']`
DemoAuthProvider convention) intermittently rendered the `/login` page instead of the target route — zero console
errors, zero `data-nextjs-dialog-overlay`, just a silent client-side redirect sometime after initial paint.

To rule out a regression in my own change, I ran two **pre-existing, unmodified** specs that use the identical
auth-seeding convention against different admin-gated routes:

- `tests/smoke/research-real-data.smoke.spec.ts` (`/services/research/execution`, `/paper-trading`) — failed 2/2 tests,
  reproduced 3/3 attempts across a fresh run + 2 retries (`--retries=2 --timeout=90000 --workers=1`).
- `tests/smoke/trading-predictions-colour-migration.smoke.spec.ts` (already shipped as part of Batch 4,
  `unified-trading-system-ui@7403a8b8`, itself previously verified `pw:L2 ✓`) — failed 2/3 tests on a single run.

Both show the identical failure signature (`main.first()` empty/not-found, or a target testid never appearing) and, on
inspection via a longer `waitUntil: "networkidle"` navigation, the DOM snapshot at failure time is unambiguously the
`/login?redirect=...` page.

`uptime` during this session measured load averages as high as **64.57 / 44.97 / 36.93** on a 10-core machine (dropping
to single digits by the end of the session) — i.e. 4-6x per-core contention. This exactly matches the host-contention
flakiness class already documented twice in the parent issue doc's own Progress Log (Batch 1: "severe host contention
(load 31-35 on 8 cores)... `net::ERR_CONNECTION_RESET`-class timeouts"; Batch 4: "measured load 27.64/8 cores").

## Why it matters

`DemoAuthProvider.restore()` (`lib/auth/demo-provider.ts`) is `async` and does a real `fetch()` to
`/api/v1/admin-strategy-assignments/resolved?org_id=...` (`fetchAssignedSlotsFromStore`) before setting `this.user`. If
whatever route guard consumes `useAuth()`'s `{user, loading}` state decides "unauthenticated" before this promise
settles — plausible under load, where the fetch (against a backend that likely isn't running in this dev-server
mock-mode context) takes longer to resolve/fail — the guard fires a client-side redirect to `/login` even though a valid
demo persona WAS seeded correctly in localStorage. This is a genuine race, not a permanent break: the persona lookup
itself (`getPersonaById("admin")`) succeeds (verified — `lib/auth/personas.ts` has a real `id: "admin"` /
`email: "admin@odum.internal"` entry matching every spec's seed exactly).

This means **any existing `pw:L2 ✓`-cited spec that seeds `portal_user`/`portal_token` and navigates to an admin-gated
`(platform)` route is silently flaky under host contention** — a CI/local-dev reliability gap independent of whatever
feature the spec is actually guarding. Two already-shipped, previously-verified specs reproduced it this session on an
otherwise-idle attempt sequence, which is concerning for CI trustworthiness if CI runners are ever similarly contended.

## Recommended fix (not done here — root-causing further needs a normal-load slot)

1. Reproduce on a slot with `uptime` load comfortably under 1x-per-core, to get a clean baseline of whether the race
   exists even without contention or is purely load-amplified.
2. Instrument (or read) the actual route-guard component consuming `useAuth()` to find exactly what condition triggers
   the `/login` redirect, and whether it correctly awaits `DemoAuthProvider.restore()`'s promise (likely surfaced via a
   `loading` flag) before deciding "no user" — if the guard fires on a synchronous read before restore's fetch settles,
   that is the fix target.
3. Consider whether `fetchAssignedSlotsFromStore`'s real `fetch()` call should be short-circuited in
   `NEXT_PUBLIC_MOCK_API=true` mode (skip the network round-trip entirely for demo personas) rather than only catching
   the eventual failure — would remove the source of the delay outright.
4. Once fixed, re-run `research-real-data.smoke.spec.ts` and `trading-predictions-colour-migration.smoke.spec.ts` (both
   untouched by this issue) to confirm they now pass reliably under a light load-simulation (or just confirm normal-load
   green, since reproducing artificial contention deterministically is its own effort).

## Todos

- [ ] [ENGINEER] P2. Root-cause + fix the `DemoAuthProvider`/route-guard async race that lets an admin-gated
      `(platform)` route redirect to `/login` despite a correctly-seeded `portal_user`/`portal_token` persona, per the
      4-step recommended fix above. Re-verify `tests/smoke/research-real-data.smoke.spec.ts` and
      `tests/smoke/trading-predictions-colour-migration.smoke.spec.ts` (both pre-existing, both reproduced failing here)
      pass reliably afterward.

## Codex SSOTs

`/codex/06-coding-standards/ui-testing-layers.md`.

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY, conflict-cleared (infra tranche, dispatch agt-30721a) —
  bounded/deterministic-outcome work, no operator gate or live judgment call found; flipped
  `assigned_vm: NA -> planning`. Conflict-check run against all active `assigned_vm: planning` docs in this doc's
  `parent_epic` + the infra tranche's consolidated-closeout digest: zero/milestone-only overlap, clear to proceed.
