---
doc_type: issue
title: backlog-detail.spec.ts's Queue-lag/sort tests fail reproducibly — seeded E2E-DISPATCHED timestamps don't stick
summary:
  Discovered while building the Backlog Integrity panel (ao_backlog_collision_alert_and_remediation_ui_2026_07_26 todo
  4) and running the full dashboard Playwright suite for regression evidence. Two backlog-detail.spec.ts tests fail
  reproducibly, in isolation, on a clean tree with zero code changes — pre-existing, not caused by that plan's work.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [dashboard, playwright, e2e, flaky-test, backlog]
related: [/plans/active/ao_backlog_collision_alert_and_remediation_ui_2026_07_26.md]
created: 2026-07-26
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: local-only
priority: P2
estimate_class: research
source: discovered while running dashboard Playwright regression suite for the Backlog Integrity panel
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
---

# backlog-detail.spec.ts Queue-lag/sort tests fail reproducibly

## What was found

Running `npx playwright test --project=chromium tests/e2e/backlog-detail.spec.ts` in complete isolation (fresh `.venv`,
fresh browsers, no other project running concurrently, verified no stray `uvicorn`/`vite` processes on the e2e ports
beforehand) fails 2 of 5 tests, every time:

1. `"Queue lag / Duration columns render the expected span or blank for every seeded row"` —
   `getByTestId('backlog-queue-lag-E2E-DISPATCHED')` expected `"15m"`, received `"—"`.
2. `"clicking a timestamp header sorts chronologically with correct asc/desc toggling"` — ascending `queued_at` sort
   returns `[DONE, QUEUED, DISPATCHED]` instead of the expected `[DONE, DISPATCHED, QUEUED]` (E2E-QUEUED and
   E2E-DISPATCHED are swapped).

**Confirmed NOT caused by the Backlog Integrity panel work**: reproduced identically with that plan's entire diff
(`src/App.tsx`, `src/layout.tsx`, `src/api.ts`, `src/types.ts`, `playwright.config.ts`) `git stash`ed — i.e. on the
exact pre-existing tree.

## Why it matters

Both failures point at the same root cause: `seed_e2e_state.py` sets `E2E-DISPATCHED.queued_at = now - 20m`,
`.dispatched_at = now - 5m`, `.status = "dispatched"`, `.dispatched_to = 1` directly via SQLAlchemy right after
`bootstrap.initialise()` — but by the time the test reads the table, those fields read as if the row had reverted to a
fresh queued state (blank queue-lag = no `dispatched_at`; sort sorts as if `queued_at` were recent, not 20m ago).

**Leading hypothesis (not confirmed — no fix attempted)**: `run-e2e-backend.sh` runs in `ORCHESTRATOR_MODE=mock` with no
real worker ever spawned into slot 1, yet the seed script stamps `dispatched_to=1` as if a live dispatch happened. One
of the ~17 background loops the server starts (`WorkerLivenessWatchdog`, `BlockedQueueReconciler`, `AutoParkReconciler`,
`PlanRegenLoop`, etc. — all visible in the webServer's own startup log) may treat a "dispatched to a slot with no live
worker" row as stale/orphaned and reset it back to a fresh queued state (`queued_at=now`, `dispatched_at=None`) on its
own tick — which would exactly reproduce both symptoms. This would make the failure a RACE between that reconciler's
tick interval and how long the test takes to reach the assertion (explaining why it might not fail in a fast/lucky run,
though every run in this session did fail). Not traced further — out of scope for the todo this was found under (a
UI-only Backlog Integrity panel task).

## Recommended decision

A `data_engineering`/`backend_engineer` pass should: (a) grep the background loops the mock-mode server starts for any
that reconcile/reset a `dispatched` `TaskRow` whose `dispatched_to` slot has no live worker, confirm which one (if any)
fires against this fixture; (b) either seed a rule that's immune to that reconciler (e.g. don't hand-stamp
`dispatched_to` unless a matching slot row also exists), or make the reconciler leave a `mock`-mode-seeded row alone, or
add a short `page.waitForTimeout`/reconciler-disable knob for e2e mode if the reconcile is intentional and the fixture
is just wrong to assume it won't fire.

## Todos

- [ ] [BACKEND] P2. Identify which background loop (if any) resets a `dispatched`+`dispatched_to` `TaskRow` when the
      target slot has no live worker, confirm it's the cause of the `E2E-DISPATCHED` seed drift described above (add a
      log line / breakpoint / temporarily disable loops one at a time against the isolated e2e backend). Repo:
      agent-orchestrator.
- [ ] [SCRIPT] P2. Once root-caused, fix either the seed script (`tests/e2e/fixtures/seed_e2e_state.py`) or the
      reconciler so `backlog-detail.spec.ts`'s Queue-lag/sort tests pass deterministically on every run — re-run
      `npx playwright test --project=chromium tests/e2e/backlog-detail.spec.ts` 3× in a row as the done-condition (no
      flake). Repo: agent-orchestrator.

## Codex SSOTs

- None specific — this is dashboard e2e test infra, not a documented pattern.
