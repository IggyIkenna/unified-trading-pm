---
doc_type: issue
title:
  Venue-scoped completeness check confirms BINANCE-FUTURES/ASTER/OKX-FUTURES backfill is NOT complete — the operator's
  paper-run start gate stays NOT-CLEAR
summary: >-
  Per no_active_paper_run_blocks_p1_2_determinism_recheck_2026_07_31.md's `[DIAG] P1` todo (the venue-scoped
  completeness check the operator's "start it, gated on backfill/IS data being complete" ruling required before
  launching a paper-trading VM for these 3 venues), a targeted MTDS manifest read (columns=/filters= row-group pushdown,
  NOT a whole-corpus walk) shows real, material gaps: BINANCE-FUTURES reachable-coverage is only 53.54% (124,316
  attempted_failed rows out of 1,324,736 total), ASTER is 83.6%, OKX-FUTURES is 89.66%. None of the 3 clear a reasonable
  completeness bar for a paper run to safely consume. Per the parent doc's own pre-specified branch rule ("gaps found ->
  file them as a new blocking data-completeness issue"), filing this now. The paper VM must NOT be started for these
  venues yet.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [cefi, honest-coverage, backfill, completeness, paper-trading-gate, data-correctness]
related:
  [
    /plans/active/issues/no_active_paper_run_blocks_p1_2_determinism_recheck_2026_07_31.md,
    /plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md,
    /plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md,
  ]
created: 2026-08-08
author: worker (slot 33)
source: >-
  Ran no_active_paper_run_blocks_p1_2_determinism_recheck_2026_07_31.md's [DIAG] P1 todo — a venue-scoped
  read_availability_index(columns=, filters=[("venue","in",[...])]) spot-check against the live cefi manifest
  (gs://market-data-tick-cefi-prd-central-element-323112), NOT the full 10.28M-row unfiltered measure_honest_coverage.py
  --asset-group cefi walk (that run was externally killed on the shared host before completing — the targeted filtered
  read is both the safer AND the faster path for a 3-venue question).
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
drift_direction: none
parent_epic: batch_live_symmetry_master
depends_on: []
last_updated: 2026-08-08
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
context_scope:
  [
    /plans/active/issues/no_active_paper_run_blocks_p1_2_determinism_recheck_2026_07_31.md,
    /plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
---

# BINANCE-FUTURES/ASTER/OKX-FUTURES backfill incomplete — paper-run gate stays closed

## What I found

Measured (2026-08-08, live prod manifest `gs://market-data-tick-cefi-prd-central-element-323112`, targeted
`read_availability_index(columns=["venue","data_type","capture_status","date"], filters=[("venue","in",[...])])` read —
3,174,368 rows across the 3 venues, NOT a full-corpus walk):

| venue           | total rows | captured | attempted_failed | expected_unattempted | empty_confirmed | reachable coverage % |
| --------------- | ---------- | -------- | ---------------- | -------------------- | --------------- | -------------------- |
| BINANCE-FUTURES | 1,324,736  | 660,900  | 124,316          | 449,106              | 90,414          | **53.54%**           |
| ASTER           | 1,666,549  | 809,247  | 4,897            | 153,905              | 698,500         | **83.60%**           |
| OKX-FUTURES     | 183,083    | 126,813  | 3,244            | 11,376               | 41,650          | **89.66%**           |

(`reachable coverage % = captured / (captured + attempted_failed + expected_unattempted)`, the same denominator
`measure_honest_coverage.py`'s `_count_statuses` uses — excludes `empty_confirmed`, legitimate honest absence.)

Trailing-14-day capture is NOT silently broken for any of the 3 (every day 2026-07-25..2026-08-08 has rows for all 3
venues — no blackout gap in the recent window), but the HISTORICAL backfill is far from complete for BINANCE-FUTURES
specifically: 124,316 `attempted_failed` rows sitting in the denominator is a real, substantial gap, not rounding noise.
This is consistent with the sibling finding already on record
(`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`: 44.96% full-cefi-aggregate pre-backfill baseline, and that
aggregate backfill itself has failed/preempted 7 times across 12 days and is only ~10.7% through its remaining
chronological scope) — this venue-scoped number is the first confirmation that specifically BINANCE-FUTURES (not just
the aggregate) carries a comparable-magnitude gap.

## Why it matters

`no_active_paper_run_blocks_p1_2_determinism_recheck_2026_07_31.md`'s `[DECISION]` item was RULED by the operator
2026-08-08: "Start it to ensure pipes work, but gate on backfill/IS data being complete through the strategy layer for
these venues first (else missing-data risk)." A paper strategy run trading BINANCE-FUTURES against a manifest that is
only 53.54% reachable-complete would consume silently-gapped historical data through the strategy layer — exactly the
missing-data risk the operator's gating condition exists to prevent. The gate stays CLOSED for all 3 venues;
BINANCE-FUTURES is the binding constraint.

## Recommended decision

Do not start the paper-trading VM for these 3 venues yet. Two paths to clear the gate, either resolves this:

1. **Let the in-flight aggregate backfill (`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`) reach these 3
   venues' full chronological range** and re-run this exact venue-scoped check — but that backfill is 7x
   failed/preempted and only ~10.7% through its remaining scope, so this could be a long wait with no committed ETA.
2. **Prioritize a venue-scoped backfill pass specifically for BINANCE-FUTURES/ASTER/OKX-FUTURES** (narrower, faster than
   waiting on the full chronological aggregate) — a strategy-desk/data-pipeline priority call, since it means
   re-ordering the existing backfill's venue traversal order or launching a dedicated venue-scoped backfill VM.

Either way, this is a genuine open question about backfill ordering/priority, not a mechanical fix this issue doc can
resolve unilaterally — flagging per the "big finding" triage rule (data-correctness, blocks a strategy-desk decision).

## Todos

- [x] ✅ [DECISION] P1. **RULED 2026-08-09 (operator): wait for the in-flight aggregate backfill
      (`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`) to reach BINANCE-FUTURES/ASTER/OKX-FUTURES naturally**
      through its own chronological traversal — option 1 taken, option 2 (a dedicated venue-scoped backfill pass)
      explicitly rejected. Repo: N/A (strategy-desk/data-pipeline priority decision).
- [ ] [DATA] P2. Once the in-flight aggregate backfill (`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`)
      naturally reaches these 3 venues' full chronological range, re-run this exact venue-scoped
      `read_availability_index(columns=, filters=[("venue","in",[...])])` check and cite the fresh reachable-coverage
      numbers here + in the parent doc's Progress Log. Repo: instruments-service.

## Progress Log (append-only)

- 2026-08-08 (slot 33, `no_active_paper_run_blocks_p1_2_determinism_recheck-001`): filed after running the parent doc's
  `[DIAG] P1` venue-scoped completeness check. Full unfiltered `measure_honest_coverage.py --asset-group cefi` run was
  attempted first (per the todo's primary suggestion) but was externally killed on the shared host before completing
  (10.28M-row full cefi manifest read — heavy, matches the class of incident
  `/codex/05-infrastructure/vm-launcher-runbook.md`'s heavy-compute-on-shared-host rule warns against); switched to the
  lighter, targeted `read_availability_index(columns=, filters=[("venue","in",[...])])` row-group-pushdown read (the
  todo's own stated alternative — "a targeted IS/MTDS spot-check") which completed cleanly and answers the exact 3-venue
  question without a whole-corpus walk.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (3 entries), still accurate.
- **2026-08-09 (operator ruling)**: RULED — wait for the in-flight aggregate backfill
  (`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`) to reach BINANCE-FUTURES/ASTER/OKX-FUTURES naturally; do
  NOT run a dedicated venue-scoped backfill pass. Todo 1 flipped (decision recorded); todo 2's re-check trigger reworded
  to match (no longer conditional on "if option 2"). Doc stays `assigned_vm: planning` — todo 2 remains genuinely open,
  gated on the aggregate backfill's own progress.
- **2026-08-09 (slot 19, data_engineering)**: Dispatched on todo 2; checked its stated precondition BEFORE re-running
  the check. Per the sibling backfill plan's own most-recent same-day entry
  (`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`'s 2026-08-09 cross-reference finding), the in-flight
  aggregate backfill has NOT reached these 3 venues' full chronological range: it walks chronologically FORWARD from
  2019-01-01 across all `heavy` venues (incl. BINANCE-FUTURES/OKX-FUTURES; ASTER is a separate CAP-EXEMPT native-REST
  venue not gated the same way) in lockstep via `SINGLE_VM_QUEUE`, and after 8 relaunches/preemptions over 13 days is
  only at day ~42-469 of the ~2769-day `2019-01-01..present` span (~1.5-17%) — nowhere near "present." Re-running the
  venue-scoped completeness check now would just reproduce essentially the same result as the 2026-08-08 baseline
  (53.54%/83.60%/89.66%) and risks misrepresenting an unfinished backfill's state as a fresh, meaningful re-measurement
  — the exact data-pipeline-correctness concern the sibling plan already hit and declined to do the same way
  (2026-07-28, slot-13: declined to re-run that plan's own POST-BACKFILL gate against the same still-mid-run VM).
  Declining to run the check this turn.

  This task has no machine-level `prereqs.prerequisites` gate (unlike the sibling plan's `-004`/`-005` POST-BACKFILL
  gate todos, which already carry `prereqs.prerequisites: [cefi-track2-backfill-vm-terminated]`), so absent a durable
  park it will likely be re-dispatched to a future worker before the backfill actually completes, repeating this same
  wasted turn — filing `/blocked` recommending main attach that SAME already-existing condition to this task's backlog
  entry (no new condition needed). No code/report changes made; this Progress Log entry is the only change this turn.

- **2026-08-09 (slot 19, resolving BLK-f089c03b)**: Main answered option A (durable park) — reuse
  `cefi-track2-backfill-vm-terminated` via a `backlog.yaml` hand-edit per RULES.md § "Adding new conditions mid-cycle".
  That file is gitignored and lives only in the root `agent-orchestrator` clone (`data/config/backlog.yaml`), which is
  READ-ONLY for this worker per the session boot guardrail ("root-clone reads are READ-ONLY... never edit, commit, or
  run work in root clones") — no slot copy exists to edit. Used the sanctioned alternative instead:
  `POST /api/backlog/{task_id}/park` (`server/routes/backlog.py`'s `auto_park.manual_park`), the API endpoint built
  specifically to close "main/a worker cannot hand-edit backlog.yaml directly" (its own docstring cites
  `ao_park_disposition_blocked_answer_no_follow_through_2026_07_31`). Same functional outcome as the recommended YAML
  edit (`priority=999` + `priority_override: true` + a false gating prerequisite blocks re-dispatch), but the
  prerequisite is a task-specific synthetic condition
  (`auto_unpark__cefi_binance_futures_aster_okx_futures_paper_gate_backfill_incomplete-f73f17b4c2b8`) rather than the
  exact shared `cefi-track2-backfill-vm-terminated` condition — confirmed parked via `GET /api/backlog/parked`. **Unpark
  trigger**: once the sibling plan's coverage-backfill VM (`cefi-queue-heavy-binancefutu-x17-...`) measurably
  self-terminates (the same event `cefi-track2-backfill-vm-terminated` gates on), flip this task's condition via
  `POST /api/prerequisites/auto_unpark__cefi_binance_futures_aster_okx_futures_paper_gate_backfill_incomplete-f73f17b4c2b8 {"value": true}`
  (or use the dashboard's "Dispatch now" on the parked-tasks view). Closing BLK-f089c03b as resolved. No code/report
  changes; this Progress Log entry + the backlog park are the only changes this turn.

- **2026-08-09 (slot 29, data_engineering craft, stale re-dispatch of the same already-parked task)**: This task landed
  on slot 29 as `already_in_progress: true` / `dispatch_reason: resume` despite the durable park recorded above
  (confirmed still `reason_code: PARKED`, `skip_count: 2` via `GET /api/backlog/parked` at boot time) — a dispatcher
  timing artifact, not a genuine unpark. Re-verified the underlying gate condition directly rather than trusting the
  park's freshness alone: `gcloud compute instances describe cefi-queue-heavy-binancefutu-x17-20260727-210013` now
  returns `NOT FOUND` (the specific VM name the park's unpark-trigger prose cites no longer exists), but
  `gcloud compute instances list --filter="name~cefi-queue-heavy"` shows a **relaunched** instance
  (`cefi-queue-heavy-binancefutu-x17-20260809-083733`, status `RUNNING`, created 2026-08-09T01:37Z) — the backfill is
  still actively mid-run under a new VM name after another preemption/relaunch cycle, not measurably self-terminated.
  The gate condition (VM genuinely terminates, not just renamed) is still unmet; re-running the venue-scoped
  completeness check now would reproduce the same stale-baseline risk already declined twice above. Declining to redo
  the check. Skipping this dispatch back to the dispatcher (task stays correctly parked); no code/check re-run
  performed. This Progress Log entry is the only change this turn.

- **2026-08-09 (slot 20, data_engineering craft, 3rd stale re-dispatch of the same already-parked task)**: Same pattern
  again — `/boot` returned `already_in_progress: true` / `dispatch_reason: "resume"`; `GET /api/backlog/parked`
  confirmed `reason_code: "PARKED"`, `skip_count: 2` at boot time. Re-verified the gate independently:
  `gcloud compute instances list --filter="name~cefi-queue-heavy"` shows the SAME instance slot 29 found
  (`cefi-queue-heavy-binancefutu-x17-20260809-083733`, still `RUNNING`, created 2026-08-09T01:37Z) — the backfill has
  not terminated since slot 29's check; the gate condition remains unmet. Declining to redo the check for the same
  stale-baseline reason already given twice above. **Noting for the record**: this is now 3 consecutive redispatches of
  a durably-parked task (slot 19's park via `POST /api/backlog/{task_id}/park`, then slots 29 and 20 both landing
  `dispatch_reason: resume`) — this park was applied via the sanctioned API endpoint (`auto_park.manual_park`), not a
  `backlog.yaml` hand-edit, so it is a DIFFERENT code path than the one already root-caused in the sibling AO-mechanism
  doc `/plans/active/issues/backlog_regen_reverted_p1_2_park_2026_08_01.md` (which found the hand-edit case never wrote
  to disk at all). Cross-referencing there rather than duplicating a new doc, since that is the standing SSOT for this
  bug class; out of craft scope for a data_engineering worker to root-cause the AO dispatch code itself. Skipping this
  dispatch back to the dispatcher; no code/check re-run performed. This Progress Log entry is the only change this turn.

- **2026-08-09 (slot 4, data_engineering craft, 4th stale re-dispatch of the same already-parked task)**: Same pattern a
  4th time — `/boot` returned `already_in_progress: true` / `dispatch_reason: "resume"`; `GET /api/backlog/parked`
  confirmed `reason_code: "PARKED"`, `skip_count: 2` at boot time (unchanged from slots 29/20's reads). Re-verified the
  gate independently: `gcloud compute instances list --filter="name~cefi-queue-heavy"` shows the SAME instance
  (`cefi-queue-heavy-binancefutu-x17-20260809-083733`, still `RUNNING`, created 2026-08-09T01:37Z) — the backfill has
  not terminated since slot 20's check; the gate condition remains unmet. Declining to redo the venue-scoped
  completeness check for the same stale-baseline reason given 3 times above. Re-`skip-current-task`ing with
  `reason_code: "PARKED"` + `park_now: true` to reinforce the durable park rather than let it silently expire. No new
  cross-reference filed — `/plans/active/issues/backlog_regen_reverted_p1_2_park_2026_08_01.md` already tracks this
  exact bug class (API-park `resume`-bypass variant) as its still-open `[SCRIPT] P2` item 3; this is corroborating
  evidence of the same pattern (now 4 touches post-park: slot 19 park -> slots 29, 20, 4 all `resume`), not a new
  finding. No code/report changes; this Progress Log entry is the only change this turn.
