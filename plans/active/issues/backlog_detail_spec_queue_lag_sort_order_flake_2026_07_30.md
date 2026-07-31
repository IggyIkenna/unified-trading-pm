---
doc_type: issue
title: agent-orchestrator backlog-detail.spec.ts queue_lag timestamp-sort order flake
summary: >-
  Two Playwright tests in backlog-detail.spec.ts (row-order assertion + timestamp-sort asc/desc toggle)
  deterministically fail against the current e2e fixture — E2E-QUEUED sorts as older than E2E-DISPATCHED when ascending,
  the reverse of what both the fixture's own comments and both tests expect. Reproduced on a clean, unmodified checkout
  — pre-existing, unrelated to the provider-badge work that surfaced it.
status: open
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, playwright, e2e, flake]
related: [/plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md]
created: 2026-07-30
parent_epic: orchestrator_master
priority: P3
assigned_vm: NA
resolved_by:
locked_by:
source:
  [
    "full `npx playwright test --project=chromium` run during the DeepSeek plan's [UI] P1 provider-badge todo,
    2026-07-30",
  ]
execution_scope: local-only
assigned_role: infra
drift_direction: advance-code
depends_on: []
---

# agent-orchestrator backlog-detail.spec.ts queue_lag sort-order flake

## What I found

While adding the DeepSeek/Claude provider badge (`deepseek_claude_blended_provider_routing_2026_07_28.md` [UI] P1), a
full `npx playwright test --project=chromium` run surfaced 2 failures in `tests/e2e/backlog-detail.spec.ts`, both about
the same underlying row order:

- `Queue lag / Duration columns render the expected span or blank for every seeded row` (line 78)
- `clicking a timestamp header sorts chronologically with correct asc/desc toggling` (line 127)

Both expect ascending `queued_at` sort to read `[E2E-DONE, E2E-DISPATCHED, E2E-QUEUED]` (oldest first — DONE
`queued_at=now-90m`, DISPATCHED `now-20m`, QUEUED `now`, per `seed_e2e_state.py`'s own comments). The actual DOM order
is `[E2E-DONE, E2E-QUEUED, E2E-DISPATCHED]` — E2E-QUEUED sorts as OLDER than E2E-DISPATCHED, the opposite of what its
`queued_at=now` (freshest of the three) should produce.

## Verified pre-existing, not caused by my change

Reproduced identically (same two tests, same wrong order) on a clean checkout with every provider-badge file change
`git stash`-ed away — confirms this is unrelated to the SlotRow/account additions that change touched, and predates this
session. Not investigated further (out of scope for the DeepSeek plan); the two candidate root causes worth checking
first:

1. `E2E-QUEUED`'s `queued_at` is stamped by `bootstrap.initialise()` internally, at a DIFFERENT point in wall-clock time
   than `dispatched.queued_at = now - timedelta(minutes=20)` (a separate `now = datetime.now(UTC)` captured AFTER
   `initialise()` returns in `_seed_backlog_state()`) — if `initialise()`'s own stamp uses a source that ends up earlier
   than expected relative to the script's `now`, or if some other write re-stamps it, this order would flip.
2. The frontend sort itself (`backlog-sort-queued_at` click handler) might have an inverted comparator or be sorting on
   the wrong field for the still-queued (no `dispatched_at`) row specifically — worth checking if `queued_at` sort for a
   still-queued row falls back to a different timestamp than the two already-dispatched rows use.

## Recommended next step

- [ ] [INFRA] P3. **Duplicate — tracked and already AO-dispatchable under
      `/plans/active/issues/ao_dashboard_backlog_detail_queue_lag_e2e_flaky_2026_07_26.md`** (`assigned_vm: planning`,
      same two `backlog-detail.spec.ts` test failures, same symptom, filed 4 days earlier with a more complete
      root-cause hypothesis — a background reconciler resetting a mock-mode-seeded `dispatched` row). Not reclassifying
      this doc; that doc is the one to dispatch. Root-cause and fix the `backlog-detail.spec.ts` queue_lag
      ascending-sort order flake — either `seed_e2e_state.py`'s `E2E-QUEUED` timestamp isn't landing where its own
      comment says, or the queued_at sort comparator is inverted/wrong for a still-queued row. Done when: both
      currently-failing tests in `tests/e2e/backlog-detail.spec.ts` pass consistently across 3 consecutive local runs
      (done via the other doc's todos, not this one).

## Progress Log

- **na-eligibility-audit 2026-07-31**: KEEP-NA-STALE (infra tranche, dispatch agt-676f1e) — this doc's sole open todo
  duplicates `/plans/active/issues/ao_dashboard_backlog_detail_queue_lag_e2e_flaky_2026_07_26.md`, which is already
  `assigned_vm: planning` (found via conflict-check surface (a): active planning docs in
  `parent_epic: orchestrator_master` — the initial grep against only the `ao_satellite_ao_dispatch_batch*` docs missed
  it because a first-pass search incorrectly filtered on `status: active`, excluding this issue doc's `status: open`;
  broadening the search to any status surfaced the duplicate). Not reclassifying — flipping `assigned_vm` here would
  dispatch a second worker onto already-claimed work. Fixed the checkbox citation to point at the authoritative doc per
  the KEEP-NA-STALE rule; `assigned_vm: NA` left as-is (zero backlog impact, pure hygiene).
