---
doc_type: issue
status: open
nature: issue
scope: [engineer, admin]
related: []
parent_epic: infrastructure_master
title:
  AO durable park wiring missing from a task's backlog entry → a false condition does NOT gate dispatch (3rd premature
  dispatch of the sports loader-migration todo)
summary: >-
  A task durably parked via park_now re-dispatches anyway: the auto_unpark__ prereq exists (false) in the DB but is
  ABSENT from the task's backlog entry, so the dispatcher does not gate on it; and manual_park silently no-ops on a
  stale cooldown parked_condition marker, so the documented re-park recipe cannot re-arm it. Observed on the 3rd
  premature dispatch of sports_taxonomy_p3_consumers-13983a72aba5 ("Move the sports feature loader off its PATH-PREFIX
  read of bucketed odds", still gated on P2's unlanded odds_horizon_bucket re-stamp).
created: 2026-08-11
author: slot-10
source: ["sports_taxonomy_p3_consumers_2026_08_08.md dispatch, 2026-08-11"]
resolved_by:
locked_by:
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
asset_group: [sports, meta]
stage: [meta]
repos: [agent-orchestrator]
tags: [ao, auto-park, dispatch, gated, sports]
drift_direction: advance-code
depends_on: []
---

# AO durable park wiring missing from task entry → false condition does not gate dispatch

## What I found

On 2026-08-11, `sports_taxonomy_p3_consumers-13983a72aba5` ("Move the sports feature loader off its PATH-PREFIX read of
bucketed odds") was dispatched to slot 10 for the **THIRD** time. Slots 22 and 15 (2026-08-09) both skipped it as
premature with `reason_code: GATED` because P2's `odds_horizon_bucket` re-stamp has not landed; slot-15 additionally
durably parked it (`park_now: true`), which per `server/auto_park.py` should create a false `auto_unpark__<task-id>`
prereq on the task's backlog entry that survives every regen tick and blocks dispatch.

Live state on 2026-08-11 (all measured, not assumed):

1. **P2 genuinely not landed**: `plans/active/sports_taxonomy_p2_migration_2026_08_08.md` is 17 open / 0 done; the
   "Consumer enumeration" P0 gate and the `odds_horizon_bucket` re-stamp todo are both unchecked. MDPS
   `bucket_assignment_adapter.py:696` still hard-codes `data_type = "odds_horizon_bucket"`; no `horizon=` GCS path
   segment exists anywhere in MDPS/features-service/UAC; features-service `gcs_reader.read_bucketed_odds` still probes
   the same canonical+legacy `odds_horizon_bucket` prefixes (its `horizon` param filters the `horizon_name` VALUE, not a
   `horizon=` path axis). The loader-migration todo's own text ("must move in the same change as the rename per the
   codex rename rule") makes it a joint change with P2's re-stamp, which has not landed. (Full detail recorded in the P3
   plan's Progress Log, 2026-08-11 slot-10 entry.)
2. **The DB condition is false but does not gate dispatch**: `GET /api/state` →
   `prerequisites["auto_unpark__sports_taxonomy_p3_consumers-13983a72aba5"] = {"value": false, "set_by": "slot-17", "set_at": "2026-08-10T22:11:16Z"}`.
   Yet the task dispatched to slot 10 on 2026-08-11T04:26Z with `priority: 20` (plan-derived, NOT the park's `999`) and
   its only `blocked_reason` was a fleet cooldown from MY OWN GATED skip — no prerequisite block.
   `GET /api/backlog/parked` does not list the task. Conclusion: the task's backlog entry carries NO
   `prereqs.prerequisites` reference to the condition, so the false DB value is irrelevant to
   `pick_next_task`/`claimable_queued_task_ids`. The park wiring (`priority_override` + the prereq attachment) is
   missing from the entry even though the DB condition row survives.
3. **`manual_park` silently no-ops, so the documented re-park recipe cannot re-arm it**: on my GATED skip with
   `park_now: true`, `POST /api/slots/10/skip-current-task` returned `{"auto_parked_condition": null, ...}`.
   `server/auto_park.py::manual_park` returns `None` (no-op) when a cooldown row for the task already carries a
   `parked_condition` — a STALE marker left over from the earlier park/unpark cycle. Because it short-circuits on that
   marker it never re-applies `priority=999` + `priority_override` + the prereq attachment to the current backlog entry,
   so the task stays dispatchable after the fleet cooldown expires.

Net effect: the durable-park mechanism fails for this task class — a false condition row alone does not gate dispatch
unless the task's backlog entry references it, and the re-park path refuses to re-attach it when a stale
`parked_condition` marker exists. This is the likely mechanism behind the repeat premature dispatches (slots 22, 15, 10)
and can silently burn a fleet turn on every cooldown expiry until either P2 lands or an operator hand-unparks/parks the
row.

## Why it matters

- **Repeat fleet-waste on a shared branch**: each premature dispatch costs a full worker session (~1h est, plus the
  boot/read/verify/QG tax) that re-discovers the same "P2 not landed" verdict. Three confirmed so far on one P1 todo.
- **The documented park recipe is not trustworthy**: `park_now: true` is the sanctioned worker-facing way to durably
  gate a task behind an external event (per `server/auto_park.py` + RULES.md §4). When it silently no-ops, a worker's
  well-intentioned GATED park gives only the transient fleet cooldown — a false sense of protection.
- **Silent failure**: `auto_parked_condition: null` is easy to misread as success; nothing pages or logs a distinct
  "park not applied" event.

## Recommended decision

Fix the mechanism in `agent-orchestrator` so a durably-parked task actually stays gated. Concretely:

- **`unpark_task` / the unpark path** should clear the cooldown row's `parked_condition` when it unparks a task, so a
  subsequent `manual_park` sees "not parked" and re-arms instead of no-oping (this is the direct cause of the observed
  no-op).
- **`manual_park`** should not treat a stale `parked_condition` as proof the task is parked when the task's CURRENT
  backlog entry is missing `priority_override`/the prereq — re-apply the full park recipe in that case (idempotency is
  still safe; `save_backlog` is append-only on the prereq list).
- **(belt-and-suspenders)** `pick_next_task`/`claimable_queued_task_ids` could consult the DB `auto_unpark__<task-id>`
  condition even when the YAML prereq is absent, so a false condition ALWAYS gates the task regardless of regen/re-park
  state — this is the property the auto_park docstring already claims ("the prereq still blocks dispatch") and is the
  load-bearing invariant.

Also consider wiring the P3 loader-migration todo onto P2's re-stamp todo (plan-level `depends_on`/`gate_on_depends` or
a dedicated prereq) so it stops being dispatchable before the rename lands — the operator-pass recommendation already
recorded in the P3 plan's Progress Log (slots 15/22/10).

## Follow-ups

- [ ] [CODE] P1. **Fix `agent-orchestrator` park/unpark so a parked task stays gated**: (1) `unpark_task` clears the
      cooldown row's `parked_condition`; (2) `manual_park` re-applies the full park recipe when the task's current
      backlog entry is missing `priority_override`/the prereq instead of no-oping on a stale marker; (3) dispatcher
      gates on the DB `auto_unpark__<task-id>` condition even when the YAML prereq is absent. Add a unit test proving a
      GATED+parked task cannot dispatch while the condition is false (and CAN once cleared true). (repo:
      agent-orchestrator)
