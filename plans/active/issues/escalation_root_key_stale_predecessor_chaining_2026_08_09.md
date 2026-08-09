---
doc_type: issue
title:
  "escalation.py:_resolve_root_key chained new escalations onto an unresolved predecessor with no staleness bound,
  misattributing independent breaks to one ancient ghost chain"
summary: >-
  `server/escalation.py:_resolve_root_key` (ao_escalation_same_root_cause_rollup_2026_08_06) chains a new escalation
  onto its predecessor's `root_key` whenever the predecessor's status is `unresolved`/`abandoned`, with no bound on how
  long ago that predecessor gave up. `reconcile_stale_unresolved_escalations` only re-checks `unresolved` rows within
  `RECONCILE_UNRESOLVED_WINDOW_HOURS` (24h) of giving up, so a predecessor older than that becomes a permanent
  un-reconciled ghost — one that never gets its terminal status corrected even after it's provably been fixed — and
  every future, otherwise-independent occurrence of the same (repo, pr_number, wall_type) keeps inheriting its root_key
  forever. Confirmed live: `agt-3dc7e9` (unified-trading-pm, `ldr_qg_failure`, pr_number=0) gave up unresolved
  2026-08-06 and, un-reconciled, absorbed 12 later escalations through 2026-08-09 — 11 of which resolved via a real
  `qg_v2_green` within minutes, i.e. were independent one-off breaks, not one 4-day chronic failure. This directly
  defeats the rollup feature's own stated purpose (distinguish "one chronic problem" from "many unrelated blips") for
  exactly the oldest, most operator-visible chains. Found while diagnosing an operator-reported "53 attempts, way past
  MAX_REESCALATIONS=10" anomaly that turned out to be a false alarm on a DIFFERENT field (`attempts` conflates
  no-capacity retries with genuine re-escalations; the real capped counter, `reescalations`, was 7 — safely under the
  cap and not exposed via any API route). Fixed same-session: `_resolve_root_key` now breaks the chain once the
  predecessor's give-up time (`resolved_at`, falling back to `created_at`) is older than
  `RECONCILE_UNRESOLVED_WINDOW_HOURS` — the same window the reconciler itself uses, so chaining eligibility tracks
  reconciler visibility (if the reconciler would still re-check it, it can still anchor a chain; once the reconciler has
  given up looking, so does the chainer).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [escalation, root-key, reconciliation, false-attribution]
related:
  [
    /plans/active/issues/escalation_queue_reconciler_false_resolution_via_unrelated_qg_green_2026_08_09.md,
    /plans/archive/issues/escalation_watchdog_retune_and_reconcile_2026_08_07.md,
  ]
created: 2026-08-09
author: main (Claude Code session, operator-directed investigation of an AO dashboard token-usage question)
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by: main
last_updated: 2026-08-09
locked_since:
source: >-
  Operator asked "what actually calls the cicd fallback" while reviewing the AO dashboard's Task Token Usage panel,
  which led to live-querying the orchestrator's escalation queue (via SSM, read-only) to explain a dispatched
  `ldr_qg_failure` escalation. That trail surfaced a "53 attempts vs MAX_REESCALATIONS=10" anomaly the operator asked to
  be investigated and fixed properly. Direct DB inspection (reescalations column, not exposed via any API) showed the
  cap was never actually breached (7 < 10) — the real bug was one row's `unresolved` status never getting reconciled,
  causing indefinite root_key chaining onto it.
---

# escalation.py: root_key chains onto an unresolved predecessor with no staleness bound

## What was found

`_resolve_root_key` (`server/escalation.py`, `ao_escalation_same_root_cause_rollup_2026_08_06`) queries for the most
recent `EscalationQueueRow` matching `(repo, pr_number, wall_type)` with `status IN ("unresolved", "abandoned")` and, if
one exists, inherits its `root_key` — with no bound on how long ago that predecessor gave up.

`reconcile_stale_unresolved_escalations` (the passive correction pass — re-polls `unresolved` rows to catch ones that
were actually fixed later, by hand or by an unrelated change) only looks at rows within
`RECONCILE_UNRESOLVED_WINDOW_HOURS` (24h) of their give-up timestamp; its own docstring says re-checking beyond that
"has no visible effect." So once an `unresolved` row ages past 24h, **nothing ever looks at it again** — if it was
actually fixed after that point, its terminal status stays wrong forever.

Combined, these two facts mean: a wall that gave up unresolved once, more than 24h ago, becomes a **permanent chain
anchor**. Every later, independent occurrence of the same wall — even ones that resolve cleanly within minutes —
inherits that ancient root_key, because `_resolve_root_key`'s query has no age cutoff.

**Confirmed live** (direct read-only query against `agent-orchestrator`'s `state.db`, root_key `agt-3dc7e9`):

| escalation_id     | created_at (UTC) | status         | resolution              | reescalations |
| ----------------- | ---------------- | -------------- | ----------------------- | ------------- |
| agt-3dc7e9 (root) | 2026-08-05 09:40 | **unresolved** | still_red_past_deadline | 1             |
| agt-5cd82e        | 2026-08-07 14:23 | resolved       | qg_v2_green             | 0             |
| agt-fb7898        | 2026-08-07 17:18 | resolved       | qg_v2_green             | 0             |
| agt-a873ef        | 2026-08-07 20:14 | resolved       | qg_v2_green             | 0             |
| agt-554235        | 2026-08-07 22:13 | resolved       | qg_v2_green             | 0             |
| agt-872712        | 2026-08-08 04:25 | resolved       | qg_v2_green             | 0             |
| agt-f18b86        | 2026-08-08 06:16 | resolved       | qg_v2_green             | 0             |
| agt-18d24b        | 2026-08-08 10:10 | resolved       | qg_v2_green             | 2             |
| agt-9bdc09        | 2026-08-08 14:13 | resolved       | qg_v2_green             | 2             |
| agt-9f9643        | 2026-08-08 18:09 | resolved       | qg_v2_green             | 0             |
| agt-49f5cc        | 2026-08-08 20:07 | resolved       | qg_v2_green             | 0             |
| agt-e248b6        | 2026-08-08 21:14 | resolved       | qg_v2_green             | 0             |
| agt-558c62        | 2026-08-08 23:08 | resolved       | qg_v2_green             | 7             |
| agt-296a8e        | 2026-08-09 09:52 | resolved       | qg_v2_green             | 0             |

12 of 13 descendants resolved cleanly, most within minutes to hours — these are independent, quickly-fixed breaks, not
one ongoing 4-day incident. Only the root row itself ever failed to resolve, and it never got corrected because it aged
out of the reconciler's window one day after giving up.

This surfaced while investigating an operator-reported anomaly: `agt-558c62`'s `attempts` field read 53, apparently
blowing past `MAX_REESCALATIONS = 10`. That was a **false alarm on the wrong field** — `attempts` increments on every
dispatch attempt including benign no-capacity retries (`retry_queued_escalations`'s failed-dispatch path), conflating it
with `reescalations`, the actual capped counter (verified directly: 7, safely under the cap). `reescalations` isn't
exposed via any API route, which is why this was only checkable via direct DB query — worth a follow-up if this class of
question recurs often enough to justify dashboard exposure, not scoped as part of this fix.

## Fix

`_resolve_root_key` now computes an anchor timestamp from the predecessor (`resolved_at`, falling back to `created_at`)
and breaks the chain — treating this row as a fresh root — once that anchor is older than
`RECONCILE_UNRESOLVED_WINDOW_HOURS`. Reuses the existing constant rather than introducing a new one: chaining
eligibility now tracks reconciler visibility directly (a predecessor the reconciler would still re-check can still
anchor a chain; once the reconciler has given up looking, so does the chainer).

Regression tests added (`tests/test_escalation.py`):

- `test_root_key_breaks_chain_when_predecessor_gave_up_beyond_reconcile_window` — predecessor `resolved_at` >
  `RECONCILE_UNRESOLVED_WINDOW_HOURS` ago → new escalation gets its own root_key.
- `test_root_key_still_inherits_when_predecessor_gave_up_within_reconcile_window` — predecessor within the window →
  unchanged behavior (regression guard against over-correcting).

All 4 pre-existing root_key tests (self-roots / inherits-unresolved / inherits-abandoned / breaks-after-resolved /
transitive-chain) pass unmodified. Full `quality-gates.sh` green (2908 passed) before shipping.

Shipped together with the sibling false-resolution fix in the same commit: `agent-orchestrator@884a9bfe1`
(`live-defi-rollout`).

## What this does NOT fix

- Does not retroactively correct `agt-3dc7e9`'s own stale `unresolved` status — it stays a permanent ghost in the
  historical record (harmless now that nothing chains onto it going forward, but still visibly wrong if anyone reads
  that specific row). A one-off manual `reconcile_stale_unresolved_escalations(window_hours=<large>)` sweep would
  correct it; not run as part of this fix (read-only diagnosis session, deliberately did not mutate orchestrator state
  beyond the code fix itself).
- Does not audit for other root_key chains with the same staleness pattern — this fix prevents NEW instances but doesn't
  sweep existing ones. Unlikely to be many (this pattern requires a wall that both hit the reescalation cap AND never
  independently resolved within 24h AND then reoccurred later), but not verified.
- Does not expose `reescalations` via the `/api/escalations/active` API — the false-alarm root cause (conflating it with
  `attempts`) would recur for the next person diagnosing this the same way from the dashboard alone.

## Todos

- [ ] [BACKEND] P3. Optional: run a one-off
      `reconcile_stale_unresolved_escalations(window_hours=<large>, limit=<large>)` sweep to correct `agt-3dc7e9` and
      any other similarly-stale `unresolved` rows in the historical record. Cosmetic (no future chaining risk post-fix)
      — low priority.
- [ ] [BACKEND] P3. Optional: expose `reescalations` on `GET /api/escalations/active`/`?include_resolved_within_hours=`
      alongside `attempts`, so a future diagnosis doesn't need a direct DB query to tell the two counters apart.

## Progress log

- 2026-08-09 (main): Found while investigating an operator-reported "53 attempts" anomaly (traced to `attempts` vs
  `reescalations` field confusion — not a real cap breach), which surfaced the actual bug: indefinite root_key chaining
  onto a 24h+-stale unresolved predecessor. Fixed `_resolve_root_key` with a staleness bound tied to
  `RECONCILE_UNRESOLVED_WINDOW_HOURS`, added 2 regression tests, verified all pre-existing root_key tests pass
  unmodified, full QG green, shipped `agent-orchestrator@884a9bfe1` via quickmerge (bundled with the sibling
  false-resolution fix in the same commit — both diagnosed and fixed in the same session).
- **round9-cross-cutting-sweep 2026-08-09**: RECLASSIFY — flipped `assigned_vm: NA → planning`
  (`execution_scope: local-only → orchestrator-agent`). Both remaining open todos are explicitly marked "Optional" and
  are bounded, deterministic-outcome technical maintenance (a one-off `reconcile_stale_unresolved_escalations` sweep
  with named args; exposing an existing `reescalations` DB column on an existing API route) — no judgment call, no
  operator gate. Conflict-check: no other active plan references `_resolve_root_key`/
  `reconcile_stale_unresolved_escalations` (grepped `plans/active/`). Carries 2 open todos, so NOT exempt from
  `check_finalize_plan_coverage.py`'s single-open-todo carve-out — authored the gated finalize twin
  `escalation_root_key_stale_predecessor_chaining_finalize_2026_08_09.md` in the same commit (renamed 2026-08-09 to
  match the `<slug>_YYYY_MM_DD.md` filename convention — `check_plan_discipline.py` B-issue-filename; fixed
  independently by two concurrent sessions, converged on the same target name).
