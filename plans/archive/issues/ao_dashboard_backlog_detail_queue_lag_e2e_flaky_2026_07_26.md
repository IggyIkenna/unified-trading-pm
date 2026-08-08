---
doc_type: issue
title: backlog-detail.spec.ts's Queue-lag/sort tests fail reproducibly — seeded E2E-DISPATCHED timestamps don't stick
summary:
  Discovered while building the Backlog Integrity panel (ao_backlog_collision_alert_and_remediation_ui_2026_07_26 todo
  4) and running the full dashboard Playwright suite for regression evidence. Two backlog-detail.spec.ts tests fail
  reproducibly, in isolation, on a clean tree with zero code changes — pre-existing, not caused by that plan's work.
status: resolved
nature: issue
asset_group: [ao] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [dashboard, playwright, e2e, flaky-test, backlog]
related:
  [
    /plans/archive/2026_07/ao_backlog_collision_alert_and_remediation_ui_2026_07_26.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-07-26
author: unknown
last_updated: 2026-08-06
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
source: discovered while running dashboard Playwright regression suite for the Backlog Integrity panel
resolved_by:
  "AO issue-doc sweep 2026-08-06 — agent-orchestrator@e761cb1 fixed the seed_e2e_state.py current_task mismatch;
  live-verified 2/2 passing across 3 consecutive Playwright runs."
locked_by:
drift_direction: advance-code
depends_on: []
context_scope:
  [
    agent-orchestrator/dashboard/tests/e2e/backlog-detail.spec.ts,
    agent-orchestrator/dashboard/tests/e2e/fixtures/seed_e2e_state.py,
    agent-orchestrator/dashboard/tests/e2e/run-e2e-backend.sh,
    /plans/archive/2026_07/ao_backlog_collision_alert_and_remediation_ui_2026_07_26.md,
  ]
---

> **🗄️ ARCHIVED 2026-08-06** — fully resolved. Root cause (`WorkerLivenessWatchdog` reclaim vs. a seed/slot
> `current_task` mismatch) diagnosed and fixed (`agent-orchestrator@e761cb1`); live-verified 2/2 passing across 3
> consecutive Playwright runs. Both todos `[x]`. Duplicate doc
> `/plans/archive/issues/backlog_detail_spec_queue_lag_sort_order_flake_2026_07_30.md` closes via this same fix. No open
> todos, no Deferred items. Surfaced by the 2026-08-06 AO issue-doc sweep.

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

**Two other candidates, raised independently by the confirmed-duplicate doc**
(`backlog_detail_spec_queue_lag_sort_order_flake_2026_07_30.md`, filed 4 days later, same symptom, now `superseded_by`
this doc): (1) `E2E-QUEUED.queued_at` might be stamped by `bootstrap.initialise()` at a different wall-clock point than
the seed script's own later `now`; (2) the frontend `queued_at` sort comparator might be inverted/wrong for a
still-queued row. Both are superseded by the `WorkerLivenessWatchdog` cause confirmed below — folded in here for the
record, not independently investigated.

## Recommended decision

A `data_engineering`/`backend_engineer` pass should: (a) grep the background loops the mock-mode server starts for any
that reconcile/reset a `dispatched` `TaskRow` whose `dispatched_to` slot has no live worker, confirm which one (if any)
fires against this fixture; (b) either seed a rule that's immune to that reconciler (e.g. don't hand-stamp
`dispatched_to` unless a matching slot row also exists), or make the reconciler leave a `mock`-mode-seeded row alone, or
add a short `page.waitForTimeout`/reconciler-disable knob for e2e mode if the reconcile is intentional and the fixture
is just wrong to assume it won't fire.

## Todos

- [x] [BACKEND] P2. **CLOSED 2026-08-06.** Root cause confirmed:
      `WorkerLivenessWatchdog._reclaim_orphaned_dispatched_tasks` (120s grace period) reclaims the seeded
      `E2E-DISPATCHED` row because the fixture's `SlotRow.current_task` didn't match the seeded task — documented in
      `dashboard/tests/e2e/fixtures/seed_e2e_state.py:217-225`. Original text follows. Identify which background loop
      (if any) resets a `dispatched`+`dispatched_to` `TaskRow` when the target slot has no live worker, confirm it's the
      cause of the `E2E-DISPATCHED` seed drift described above (add a log line / breakpoint / temporarily disable loops
      one at a time against the isolated e2e backend). Repo: agent-orchestrator.
- [x] [SCRIPT] P2. **CLOSED 2026-08-06 — `agent-orchestrator@e761cb1`.** Fixed the seed fixture to set
      `current_task="E2E-DISPATCHED"`, closing the mismatch the watchdog reclaim keyed on. **Live-verified**: ran
      `npx playwright test --project=chromium tests/e2e/backlog-detail.spec.ts -g "Queue lag|sorts chronologically"` 3
      consecutive times — 2/2 passed every run, matching this todo's own done-condition. Original text follows. Once
      root-caused, fix either the seed script (`tests/e2e/fixtures/seed_e2e_state.py`) or the reconciler so
      `backlog-detail.spec.ts`'s Queue-lag/sort tests pass deterministically on every run — re-run
      `npx playwright test --project=chromium tests/e2e/backlog-detail.spec.ts` 3× in a row as the done-condition (no
      flake). Repo: agent-orchestrator.

## Codex SSOTs

- None specific — this is dashboard e2e test infra, not a documented pattern.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **na-eligibility-audit 2026-08-02** (autonomous, tranche `ao`): KEEP-NA, valid — this doc was deliberately flipped
  `assigned_vm: planning` → `NA` + `execution_scope: local-only` by the 2026-07-31 operator directive
  `unified-trading-pm@14478ca26` ("work these interactively now rather than queue behind AO's current busy backlog"). A
  dated operator ruling is not re-litigated by this skill. Both todos re-read and still accurate: the `E2E-DISPATCHED`
  seed drift is unfixed and the root cause is still an untested hypothesis.
- **na-eligibility-audit 2026-08-03** (ao tranche): KEEP-NA, valid — re-affirmed. Standing operator ruling
  (`unified-trading-pm@14478ca26`) directly covers this doc, independently re-verified real via `git show`, not
  re-litigated. Independently confirmed both items still open and accurate: no commit has touched the seed script or
  investigated the reconciler loops since filing.
- **context-scout 2026-08-03**: re-scouted; context_scope unchanged (4 entries), still accurate.
- **context-scout 2026-08-03 (re-pass, updated methodology)**: re-verified, unchanged (4 entries) — still the right
  minimal set for both open todos.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (4 entries), still accurate.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **2026-08-06 (slot-10, duplicate-reconciliation)**: Active twin unique provenance merged — SCRIPT P2 fix was shipped
  as a side-effect of `ao_done_categorization_display_and_quickmerge_gate_2026_08_06.md`; the sibling doc
  `/plans/archive/issues/backlog_detail_spec_queue_lag_sort_order_flake_2026_07_30.md` had already credited the fix
  while these two checkboxes were left unflipped, surfaced by `/plan-reconcile ao` 2026-08-06. Active twin
  `plans/active/issues/ao_dashboard_backlog_detail_queue_lag_e2e_flaky_2026_07_26.md` removed (create-only archival
  duplicate reconciliation).
- **ao_satellite_ao_dispatch_batch5 2026-08-08** (§3 formal-closure,
  `ao_tranche_full_content_audit_findings_2026_07_31.md`): folded the duplicate doc's two extra root-cause candidates
  into "Why it matters" above, and added the missing `superseded_by:` frontmatter pointer on that doc (was `resolved_by`
  prose only). Both docs now internally consistent: survivor `status: resolved` + fix cited, duplicate
  `status: resolved` + `superseded_by:` this doc, both archived.
