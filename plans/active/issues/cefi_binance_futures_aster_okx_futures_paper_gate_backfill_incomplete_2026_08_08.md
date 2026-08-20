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
    /plans/archive/2026_08/no_active_paper_run_blocks_p1_2_determinism_recheck_2026_07_31.md,
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
last_updated: 2026-08-20
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
context_scope:
  [
    /plans/archive/2026_08/no_active_paper_run_blocks_p1_2_determinism_recheck_2026_07_31.md,
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
- [ ] [DATA] P2. **Line-1 rewritten 2026-08-19 (`/plan-reconcile`, task_template.md §3 line-1-completeness) — line 1
      previously had no verb at all.** Re-run this exact venue-scoped
      `read_availability_index(columns=, filters=[("venue","in",[...])])` check once the in-flight aggregate backfill
      (`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`) naturally reaches these 3 venues' full chronological
      range, and cite the fresh reachable-coverage numbers here + in the parent doc's Progress Log. Repo:
      instruments-service.
- [x] ✅ [INFRA] P1. **Purge/reclassify the 2,003 stale ASTER `book_snapshot_5`
      `attempted_failed[UpstreamTimestampBiasError]` manifest rows** (see 2026-08-09 DP-FETCH-009 Progress Log entry
      below for full diagnosis) — these represent a structurally-impossible-forever combo (no historical depth endpoint)
      that the 2026-07-15 operator ruling (`/plans/archive/2026_07/cefi_completion_program_2026_07_15.md`) already says
      should carry NO manifest row at all (`_onchain_perp_batch_live_only.py` module docstring). **DONE 2026-08-15**:
      wrote `market-tick-data-service/scripts/retire_aster_book_snapshot5_dead_rows_2026_08_15.py` (CAS
      read-classify-write + retry, pre-apply GCS snapshot, fresh §3a soft-delete-retention gate, per-row content-match
      re-check, post-write verification — same safety model as `restamp_cefi_onchain_perp_venue_chain_2026_07_21.py`
      plus the later-formalized §3a check). Dry-run measured 2,000 live rows matching the exact 4-field signature
      (venue=ASTER, data_type=book_snapshot_5, capture_status=attempted_failed, error_reason=UpstreamTimestampBiasError)
      — 3 fewer than the 2026-08-09 count, expected drift from a live re-measurement, not a stale assumption.
      Soft-delete retention confirmed fresh at 604800s (7d, meets §3a). Manifest confirmed under continuous live write
      traffic (29,579,146 rows at diagnostic read → 29,694,222 rows at CAS read ~10 min later, +115,076 from concurrent
      writers) — validates using CAS over a plain overwrite. `--apply` succeeded on the first CAS attempt: 2,000 rows
      removed (29,694,222 → 29,692,222 total), all post-write invariants passed (row count, zero remaining
      target-signature rows, column set preserved). Pre-apply snapshot:
      `gs://market-data-tick-cefi-prd-central-element-323112/_index/backups/availability_index.pre_aster_book_snapshot5_retire_apply_20260815T102620Z.parquet`.
      Old generation 1786789223350161 → new generation 1786790875420616. Shipped
      market-tick-data-service@6ab13fdf00d74ce72b081f68a2805c7922fdf4ce.

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

- **2026-08-09 (slot 9, data_engineering craft, 5th stale re-dispatch of the same already-parked task)**: Same pattern a
  5th time — `/boot` returned `already_in_progress: true` / `dispatch_reason: "resume"`; `GET /api/backlog/parked`
  confirmed `reason_code: "PARKED"`, `skip_count: 3` at boot time (incremented from 2, so the dispatcher is at least
  counting these bounces). Re-verified the gate independently:
  `gcloud compute instances list --filter="name~cefi-queue-heavy"` shows the SAME instance
  (`cefi-queue-heavy-binancefutu-x17-20260809-083733`, still `RUNNING`, created 2026-08-09T01:37Z) — unchanged since
  slot 4's check; the gate condition remains unmet. Declining to redo the venue-scoped completeness check for the same
  stale-baseline reason given 4 times above. Re-`skip-current-task`ing with `reason_code: "PARKED"`. No new
  cross-reference filed — corroborating evidence of the same already-tracked bug class in
  `/plans/active/issues/backlog_regen_reverted_p1_2_park_2026_08_01.md` (now 5 touches post-park: slot 19 park -> slots
  29, 20, 4, 9 all `resume`). No code/report changes; this Progress Log entry is the only change this turn.

- **2026-08-09 (slot 4, data_pipeline_failure escalation `agt-e488d1`, DP-FETCH-009 root-cause)**: Dispatched off a
  `check_high_attempted_failed` page for `asset_group=cefi data_type=book_snapshot_5` (9,883 `attempted_failed` cells of
  935,767 attempted; 2,193 fresh in the last 1d). Root-caused the dominant slice of the freshness signal — **NOT a live,
  ongoing fetch failure** — and it directly extends this doc's ASTER coverage-gap population (4,897 ASTER
  `attempted_failed` rows measured 2026-08-08 above), so recording here rather than filing a new doc.
  - Queried the live cefi manifest (`gs://market-data-tick-cefi-prd-central-element-323112`,
    `read_availability_index_safe(columns=, filters=[("data_type","=","book_snapshot_5"),("venue","=","ASTER"), ("capture_status","=","attempted_failed")])`,
    targeted row-group-pushdown read): 2,003 rows, ALL `error_reason=UpstreamTimestampBiasError`,
    `service_name=market-tick-data-service`, `transport=rest`, spanning shard `date` 2026-06-23..2026-08-01 (~50
    instruments/day), with `written_at` overwhelmingly in the last ~24h (2,000 of the 2,003 have
    `written_at >= 2026-08-08`). This is 91% of the DP-FETCH-009 fresh-window volume (2,000/2,193).
  - **Confirmed ASTER `book_snapshot_5` is structurally non-batch-fetchable, permanently** (3 independent SSOTs agree):
    `market-tick-data-service/configs/expected_start_dates.yaml` (`ASTER: book_snapshot_5: null # Live-capture-only`),
    UAC
    `unified_api_contracts.registry.market_data_categories.VENUE_DATA_TYPE_NO_BATCH_SOURCE["ASTER"] = frozenset({"book_snapshot_5","liquidations"})`,
    and `aster_adapter.py::fetch_depth`'s own docstring ("NO historical depth endpoint... live-capture-only"). Aster's
    REST book endpoint (`/fapi/v1/depth`) only ever returns the CURRENT snapshot — a batch request for any historical
    day gets back today's timestamps, which correctly fails `raw_tick_hive.validate_day_partition_alignment()` →
    `UpstreamTimestampBiasError` → `record_failed`. This is the manifest doing its job (Path B of the three-category
    empty-output decision), not a misclassification.
  - **Verified the live code (`live-defi-rollout` HEAD, and confirmed on `origin/main` since 2026-07-16T16:32Z, so the
    fix has been on `main` for 3+ weeks) already excludes this combo from every new fetch attempt** — traced the full
    call chain: `onchain_perp_batch_handler.py::_process_venue` calls `_batch_data_types_for_venue(venue, data_types)`
    (`_onchain_perp_batch_live_only.py`) BEFORE any fetch, which calls UAC's
    `venue_data_type_has_batch_source("ASTER", "book_snapshot_5")` → `False` → dropped, never reaches
    `_fetch_shard_rows`/`_fetch_aster`. As a second, independent guard, `_fetch_aster()` itself hard-`raise`s
    `ValueError("Unsupported ASTER data_type: 'book_snapshot_5'")` if ever reached with this data_type (a DIFFERENT
    error string than what's in the manifest). Also confirmed `aster_adapter.py::fetch_depth` (the only function that
    could make the live HTTP call) has **zero call sites** anywhere in the repo, and the sibling
    `_umi_aster.py::fetch_aster_rest` (used by the main `engine/orchestrator` path) only ever fetches
    `trades`/`derivative_ticker`, never `book_snapshot_5`. No currently running or recently-logged VM matches an
    onchain-perp-batch/ASTER launch either (`gcloud compute instances list` clean;
    `gs://deployment-scripts-central-element-323112/vm-logs/` has no `cefi-aster-*`/`cefi-hyperliquid-*` entries newer
    than 2026-07-30).
  - **Conclusion: no live/executable code path today can produce a NEW `UpstreamTimestampBiasError` for (ASTER,
    book_snapshot_5)**. The 2,003 rows are almost certainly PRE-2026-07-13 legacy failure records (from when this combo
    genuinely was attempted, before the exclusion fix landed) whose `written_at` got refreshed by a
    manifest-maintenance/migration process, not by a new fetch. Did not conclusively identify which process refreshed
    `written_at` — checked `restamp_cefi_onchain_perp_venue_chain_2026_07_21.py` (chain-column restamp for this exact
    venue population, lifecycle `oneoff`, still present — a plausible candidate since it does a `written_at`-aware
    per-row rewrite) and ruled out the manifest consolidator itself (`manifest_consolidator.py` only ORDERS by existing
    `written_at`/`attempted_at` to pick a dedup winner, never overwrites them). Did not attempt to pin this further or
    write a manifest-correction script this turn — a genuine row DELETE/retire (not an additive `.add()`) is needed to
    match the 2026-07-15 ruling's "no row at all" target, which is a delete-safety-gated change (see new `[OPERATOR] P1`
    todo above), out of scope for a blind one-shot escalation edit.
  - **DP-FETCH-009 alert disposition**: the underlying manifest state is stale/legacy, not an active pipeline break — no
    code fix shipped this turn (there was no live bug to fix; the exclusion code is already correct and has been for 3+
    weeks). The `check_high_attempted_failed` detector's freshness signal is misleading for any (venue, data_type)
    population whose `written_at` gets refreshed by an unrelated maintenance/migration write without a corresponding new
    fetch attempt — flagging as a possible detector gap worth a separate look (not pursued here; out of this
    escalation's scope). No code/report changes; this Progress Log entry + the new `[OPERATOR] P1` todo are the only
    changes this turn.

- **2026-08-09 (slot 31, data_engineering craft, 6th stale re-dispatch of the same already-parked task)**: Same pattern
  again — `/boot` returned `already_in_progress: true` / `dispatch_reason: "resume"`; `GET /api/backlog/parked`
  confirmed `reason_code: "PARKED"`, `skip_count: 4` at boot time (incremented from 3 at slot 9's check). Re-verified
  the gate independently: `gcloud compute instances list --filter="name~cefi-queue-heavy"` shows the SAME instance
  (`cefi-queue-heavy-binancefutu-x17-20260809-083733`, still `RUNNING`, created 2026-08-09T01:37Z) — unchanged since
  slot 9's check; the gate condition remains unmet. Declining to redo the venue-scoped completeness check for the same
  stale-baseline reason given 5 times above. Re-`skip-current-task`ing with `reason_code: "PARKED"`. No new
  cross-reference filed — corroborating evidence of the same already-tracked bug class in
  `/plans/active/issues/backlog_regen_reverted_p1_2_park_2026_08_01.md` (now 6 touches post-park: slot 19 park -> slots
  29, 20, 4, 9, 31 all `resume`). No code/report changes; this Progress Log entry is the only change this turn.

- **2026-08-09 (slot 16, data_engineering craft, 7th stale re-dispatch of the same already-parked task)**: Same pattern
  again — `/boot` returned
  `dispatch_reason: "tier=1 priority=50 plan_order=0 — highest-rank queued task with prereqs met and no collision"` (not
  even flagged `already_in_progress` this time — a further variant of the same bypass); `GET /api/backlog/parked`
  confirmed `reason_code: "PARKED"`, `skip_count: 5` at boot time (incremented from 4 at slot 31's check). Re-verified
  the gate independently: `gcloud compute instances list --filter="name~cefi-queue-heavy"` shows the SAME instance
  (`cefi-queue-heavy-binancefutu-x17-20260809-083733`, still `RUNNING`, created 2026-08-09T01:37Z) — unchanged since
  slot 31's check; the gate condition remains unmet. Declining to redo the venue-scoped completeness check for the same
  stale-baseline reason given 6 times above. Re-`skip-current-task`ing with `reason_code: "PARKED"`. No new
  cross-reference filed — corroborating evidence of the same already-tracked bug class in
  `/plans/active/issues/backlog_regen_reverted_p1_2_park_2026_08_01.md` (now 7 touches post-park: slot 19 park -> slots
  29, 20, 4, 9, 31, 16 all bypassing the park). No code/report changes; this Progress Log entry is the only change this
  turn.

- **2026-08-09 (slot 13, data_engineering craft, 8th stale re-dispatch of the same already-parked task)**: Same pattern
  again — `/boot` returned `already_in_progress: true` / `dispatch_reason: "resume"`; `GET /api/backlog/parked`
  confirmed `reason_code: "PARKED"`, `skip_count: 6` at boot time (incremented from 5 at slot 16's check). Re-verified
  the gate independently: `gcloud compute instances list --filter="name~cefi-queue-heavy"` shows the SAME instance
  (`cefi-queue-heavy-binancefutu-x17-20260809-083733`, still `RUNNING`, created 2026-08-09T01:37Z) — unchanged since
  slot 16's check; the gate condition remains unmet. Declining to redo the venue-scoped completeness check for the same
  stale-baseline reason given 7 times above. Re-`skip-current-task`ing with `reason_code: "PARKED"`. No new
  cross-reference filed — corroborating evidence of the same already-tracked bug class in
  `/plans/active/issues/backlog_regen_reverted_p1_2_park_2026_08_01.md` (now 8 touches post-park: slot 19 park -> slots
  29, 20, 4, 9, 31, 16, 13 all bypassing the park). No code/report changes; this Progress Log entry is the only change
  this turn.

- **2026-08-09 (slot 32, data_engineering craft, 9th stale re-dispatch of the same already-parked task)**: Same pattern
  again — `/boot` returned `already_in_progress: true` / `dispatch_reason: "resume"`; `GET /api/backlog/parked`
  confirmed `reason_code: "PARKED"`, `skip_count: 7` at boot time (incremented from 6 at slot 13's check). Re-verified
  the gate independently: `gcloud compute instances list --filter="name~cefi-queue-heavy"` shows the SAME instance
  (`cefi-queue-heavy-binancefutu-x17-20260809-083733`, still `RUNNING`, created 2026-08-09T01:37Z) — unchanged since
  slot 13's check; the gate condition remains unmet. Declining to redo the venue-scoped completeness check for the same
  stale-baseline reason given 8 times above. Re-`skip-current-task`ing with `reason_code: "PARKED"`. No new
  cross-reference filed — corroborating evidence of the same already-tracked bug class in
  `/plans/active/issues/backlog_regen_reverted_p1_2_park_2026_08_01.md` (now 9 touches post-park: slot 19 park -> slots
  29, 20, 4, 9, 31, 16, 13, 32 all bypassing the park). No code/report changes; this Progress Log entry is the only
  change this turn.

- **2026-08-09 (slot 5, data_engineering craft, 10th stale re-dispatch of the same already-parked task)**: Same pattern
  again — `/boot` returned `already_in_progress: true` / `dispatch_reason: "resume"`; `GET /api/backlog/parked`
  confirmed `reason_code: "PARKED"`, `skip_count: 8` at boot time (incremented from 7 at slot 32's check). Re-verified
  the gate independently: `gcloud compute instances list --filter="name~cefi-queue-heavy"` shows the SAME instance
  (`cefi-queue-heavy-binancefutu-x17-20260809-083733`, still `RUNNING`, created 2026-08-09T01:37Z) — unchanged since
  slot 32's check; the gate condition remains unmet. Declining to redo the venue-scoped completeness check for the same
  stale-baseline reason given 9 times above. Re-`skip-current-task`ing with `reason_code: "PARKED"`. No new
  cross-reference filed — corroborating evidence of the same already-tracked bug class in
  `/plans/active/issues/backlog_regen_reverted_p1_2_park_2026_08_01.md` (now 10 touches post-park: slot 19 park -> slots
  29, 20, 4, 9, 31, 16, 13, 32, 5 all bypassing the park). No code/report changes; this Progress Log entry is the only
  change this turn.

- **2026-08-09 (slot 27, data_engineering craft, 11th stale re-dispatch of the same already-parked task)**: Same pattern
  again — a heartbeat handoff (not `/boot`) surfaced this task directly, no `already_in_progress` flag on this path;
  `GET /api/backlog/parked` confirmed `reason_code: "PARKED"`, `skip_count: 9` at boot time (incremented from 8 at slot
  5's check). Re-verified the gate independently: `gcloud compute instances list --filter="name~cefi-queue-heavy"` shows
  the SAME instance (`cefi-queue-heavy-binancefutu-x17-20260809-083733`, still `RUNNING`, created 2026-08-09T01:37Z) —
  unchanged since slot 5's check; the gate condition remains unmet. Declining to redo the venue-scoped completeness
  check for the same stale-baseline reason given 10 times above. Re-`skip-current-task`ing with `reason_code: "PARKED"`.
  No new cross-reference filed — corroborating evidence of the same already-tracked bug class in
  `/plans/active/issues/backlog_regen_reverted_p1_2_park_2026_08_01.md` (now 11 touches post-park: slot 19 park -> slots
  29, 20, 4, 9, 31, 16, 13, 32, 5, 27 all bypassing the park). No code/report changes; this Progress Log entry is the
  only change this turn.

- **2026-08-09 (slot 2, data_engineering craft, 12th stale re-dispatch of the same already-parked task)**: Same pattern
  again — a heartbeat handoff surfaced this task directly; `GET /api/backlog/parked` confirmed `reason_code: "PARKED"`,
  `skip_count: 10` at boot time (incremented from 9 at slot 27's check). Re-verified the gate independently:
  `gcloud compute instances list --filter="name~cefi-queue-heavy"` shows the SAME instance
  (`cefi-queue-heavy-binancefutu-x17-20260809-083733`, still `RUNNING`, created 2026-08-09T01:37Z) — unchanged since
  slot 27's check; the gate condition remains unmet. Declining to redo the venue-scoped completeness check for the same
  stale-baseline reason given 11 times above. Re-`skip-current-task`ing with `reason_code: "PARKED"`. No new
  cross-reference filed — corroborating evidence of the same already-tracked bug class in
  `/plans/active/issues/backlog_regen_reverted_p1_2_park_2026_08_01.md` (now 12 touches post-park: slot 19 park -> slots
  29, 20, 4, 9, 31, 16, 13, 32, 5, 27, 2 all bypassing the park). No code/report changes; this Progress Log entry is the
  only change this turn.

- **2026-08-09 (slot 28, data_engineering craft, 13th stale re-dispatch of the same already-parked task)**: Same pattern
  again — a heartbeat handoff surfaced this task directly (`dispatch_reason: "tier=1 priority=50 plan_order=0..."`);
  `GET /api/backlog/parked` confirmed `reason_code: "PARKED"`, `skip_count: 11` at boot time (incremented from 10 at
  slot 2's check). Re-verified the gate independently: `gcloud compute instances list --filter="name~cefi-queue-heavy"`
  shows the SAME instance (`cefi-queue-heavy-binancefutu-x17-20260809-083733`, still `RUNNING`, created
  2026-08-09T01:37Z) — unchanged since slot 2's check; the gate condition remains unmet. Declining to redo the
  venue-scoped completeness check for the same stale-baseline reason given 12 times above. Re-`skip-current-task`ing
  with `reason_code: "PARKED"`. No new cross-reference filed — `backlog_regen_reverted_p1_2_park_2026_08_01.md` already
  tracks this exact bug class as P0/`assigned_vm: NA` (its still-open `[SCRIPT] P2` item 3); this is corroborating
  evidence of the same pattern (now 13 touches post-park: slot 19 park -> slots 29, 20, 4, 9, 31, 16, 13, 32, 5, 27, 2,
  28 all bypassing the park). No code/report changes; this Progress Log entry is the only change this turn.

- **2026-08-10 (slot 17, data_engineering craft, 14th stale re-dispatch of the same already-parked task)**: Same pattern
  again — `/boot` returned `already_in_progress: true` / `dispatch_reason: "resume"`; `GET /api/backlog/parked`
  confirmed `reason_code: "PARKED"`, `skip_count: 12` at boot time (incremented from 11 at slot 28's check). Re-verified
  the gate independently: `gcloud compute instances list --filter="name~cefi-queue-heavy"` shows the SAME instance
  (`cefi-queue-heavy-binancefutu-x17-20260809-083733`, still `RUNNING`, created 2026-08-09T01:37Z) — unchanged since
  slot 28's check, now over 24h with no termination; the gate condition remains unmet. Declining to redo the
  venue-scoped completeness check for the same stale-baseline reason given 13 times above. Re-`skip-current-task`ing
  with `reason_code: "PARKED"`. No new cross-reference filed — `backlog_regen_reverted_p1_2_park_2026_08_01.md` already
  tracks this exact bug class (now 14 touches post-park: slot 19 park -> slots 29, 20, 4, 9, 31, 16, 13, 32, 5, 27, 2,
  28, 17 all bypassing the park). No code/report changes; this Progress Log entry is the only change this turn.

- **2026-08-10 (slot 15, data_engineering craft, 15th stale re-dispatch of the same already-parked task)**: Same pattern
  again — a heartbeat handoff surfaced this task directly (`dispatch_reason: "tier=1 priority=50 plan_order=0..."`);
  `GET /api/backlog/parked` confirmed `reason_code: "PARKED"`, `skip_count: 13` at boot time (incremented from 12 at
  slot 17's check). Re-verified the gate independently: `gcloud compute instances list --filter="name~cefi-queue-heavy"`
  shows the SAME instance (`cefi-queue-heavy-binancefutu-x17-20260809-083733`, still `RUNNING`, created
  2026-08-09T01:37Z) — unchanged since slot 17's check, now ~28h with no termination; the gate condition remains unmet.
  Declining to redo the venue-scoped completeness check for the same stale-baseline reason given 14 times above.
  Re-`skip-current-task`ing with `reason_code: "PARKED"`. No new cross-reference filed —
  `backlog_regen_reverted_p1_2_park_2026_08_01.md` already tracks this exact bug class (now 15 touches post-park: slot
  19 park -> slots 29, 20, 4, 9, 31, 16, 13, 32, 5, 27, 2, 28, 17, 15 all bypassing the park). No code/report changes;
  this Progress Log entry is the only change this turn.

- **2026-08-10 (slot 25, data_engineering craft, 16th stale re-dispatch of the same already-parked task)**: Same pattern
  again — `/boot` returned `already_in_progress: true` / `dispatch_reason: "resume"`; `GET /api/backlog/parked`
  confirmed `reason_code: "PARKED"`, `skip_count: 15` at boot time (incremented from 13 at slot 15's logged check — a
  couple of intermediate dispatches incremented it without logging). Re-verified the gate independently:
  `gcloud compute instances list --filter="name~cefi-queue-heavy"` shows the SAME instance
  (`cefi-queue-heavy-binancefutu-x17-20260809-083733`, still `RUNNING`, created 2026-08-09T01:37Z) — unchanged since
  slot 15's check, now ~32h with no termination; the gate condition remains unmet. Declining to redo the venue-scoped
  completeness check for the same stale-baseline reason given 15 times above. Re-`skip-current-task`ing with
  `reason_code: "PARKED"` + `park_now: true` to reinforce the durable park. No new cross-reference filed —
  `backlog_regen_reverted_p1_2_park_2026_08_01.md` already tracks this exact bug class (now 16 touches post-park: slot
  19 park -> slots 29, 20, 4, 9, 31, 16, 13, 32, 5, 27, 2, 28, 17, 15, 25 all bypassing the park). No code/report
  changes; this Progress Log entry is the only change this turn.

- **2026-08-10 (slot 18, data_engineering craft, 17th stale re-dispatch of the same already-parked task)**: Same pattern
  again — a heartbeat handoff surfaced this task directly (`dispatch_reason: "tier=1 priority=50 plan_order=0..."`, task
  `cefi_binance_futures_aster_okx_futures_paper_gate_backfill_incomplete-f73f17b4c2b8`, `status: dispatched` to slot
  18). Re-verified the gate independently (fresh, not trusting the parked-state read alone):
  `gcloud compute instances list --filter="name~cefi-queue-heavy"` shows the SAME instance
  (`cefi-queue-heavy-binancefutu-x17-20260809-083733`, still `RUNNING`, created 2026-08-09T01:37Z) — unchanged since
  slot 25's check (~2 days with no termination); the gate condition (aggregate backfill reaches these 3 venues' full
  chronological range) remains unmet. Declining to redo the venue-scoped completeness check for the same stale-baseline
  reason given 16 times above. Re-`skip-current-task`ing with `reason_code: "PARKED"` + `park_now: true` to reinforce
  the durable park. No new cross-reference filed — `backlog_regen_reverted_p1_2_park_2026_08_01.md` already tracks this
  exact bug class (now 17 touches post-park: slot 19 park -> slots 29, 20, 4, 9, 31, 16, 13, 32, 5, 27, 2, 28, 17, 15,
  25, 18 all bypassing the park). No code/report changes; this Progress Log entry is the only change this turn.

- **2026-08-10 (slot 6, data_engineering craft, 18th stale re-dispatch of the same already-parked task)**: Same pattern
  again — `/boot` returned `already_in_progress: true` / `dispatch_reason: "resume"`; gate re-verified independently:
  `gcloud compute instances list --filter="name~cefi-queue-heavy"` shows the SAME instance
  (`cefi-queue-heavy-binancefutu-x17-20260809-083733`, still `RUNNING`, created 2026-08-09T01:37Z) — unchanged since
  slot 18's check (~2 days with no termination); the gate condition (aggregate backfill reaches these 3 venues' full
  chronological range) remains unmet. Also confirmed via `GET /api/backlog/parked` that this task is NO LONGER in the
  parked set at all (not just bounce-resumed) — the durable park has fully fallen off, so re-arming it is the point of
  `park_now: true` this turn. Declining to redo the venue-scoped completeness check for the same stale-baseline reason
  given 17 times above. Re-`skip-current-task`ing with `reason_code: "PARKED"` + `park_now: true` to reinforce the
  durable park. No new cross-reference filed — `backlog_regen_reverted_p1_2_park_2026_08_01.md` already tracks this
  exact bug class (now 18 touches post-park: slot 19 park -> slots 29, 20, 4, 9, 31, 16, 13, 32, 5, 27, 2, 28, 17, 15,
  25, 18, 6 all bypassing the park). No code/report changes; this Progress Log entry is the only change this turn.

- **2026-08-16 (slot 10, data_pipeline_failure escalation `agt-522d96`, DP-FETCH-009 root-cause, 2nd occurrence)**:
  Dispatched off a `check_high_attempted_failed` page for `asset_group=cefi data_type=book_snapshot_5` (8,002
  `attempted_failed` cells of 173,333 attempted; 2,260 fresh in the last 1d). This is a DIFFERENT root cause than the
  2026-08-09 ASTER dispatch above (that population was purged 2026-08-15, see the `[INFRA] P1` todo) — extending this
  doc rather than filing a new one since it directly involves the SAME `cefi-queue-heavy-binancefutu-x17-*` backfill VM
  this doc already tracks.
  - Queried the live cefi manifest (`read_availability_index_safe(columns=, filters=[data_type=book_snapshot_5,
    capture_status=attempted_failed])`, targeted row-group-pushdown read): of the 2,260 fresh (`written_at` in the
    last 1d) rows, **2,259 (99.96%) carry `error_reason="Tardis HTTP 403 code=274 concurrent-IP-lock"`** — spread
    across 11 venues (OKX-SPOT 449, BINANCE-SPOT 378, OKX-FUTURES 378, OKX-SWAP 264, BINANCE-FUTURES 229, COINBASE-SPOT
    155, BITFINEX-SPOT 155, KRAKEN-SPOT 150, KRAKEN-FUTURES 51, DERIBIT 32, BITFINEX-FUTURES 18), all shard `date` in
    2020, `written_at` 2026-08-15T23:31Z..2026-08-16T04:34Z.
  - **This is NOT a misclassification** — code=274 (Tardis single-concurrent-IP lock rejection) is correctly routed to
    `attempted_failed` per `tardis_csv_transport.py`'s existing 400-path classification (only 300/140 "impossible
    combination" codes route to `empty_confirmed`; 274 is a genuinely transient/retriable rejection, so
    `attempted_failed` is the honest, correct manifest state — no code fix needed for the classification itself).
  - **Traced the proximate cause**: `gcloud compute instances list --filter=status=RUNNING` at dispatch time showed
    TWO VMs matching `tardis-concurrency-guard.sh`'s `TARDIS_VM_NAME_PATTERN` overlapping in the relevant window —
    `mtds-backfill-cefi-20260815-181733` (started 2026-08-15T17:18Z, via `launch-mtds-backfill-vm.sh`) and
    `cefi-queue-heavy-binancefutu-x17-20260815-220349` (started 2026-08-15T22:03:55Z, via
    `launch-cefi-sharded-backfill.sh` — a preemption-relaunch of the SAME backfill this doc's Progress Log has tracked
    since 2026-08-09). Both launchers correctly `source`+call `tardis_concurrency_guard`/`tardis_guard_reserve_slot`
    (verified via grep — this is not a missing-guard bug), so if these two genuinely overlapped past a mutual guard
    check, it is most likely the ALREADY-KNOWN, ALREADY-MITIGATED ~40s async-VM-visibility race documented in
    `tardis-concurrency-guard.sh`'s own header (2026-07-16T00:58Z incident, closed via the RUNNING+PROVISIONING+STAGING
    status widening) — not a fresh code defect. Did not conclusively pin the exact overlap window (`mtds-backfill-cefi`
    had already self-terminated — `gcloud compute instances describe` returned `NOT FOUND` — by the time this dispatch
    checked, so its exact stop time is unrecoverable from live state).
  - **Verified self-resolved, not currently live**: re-queried the manifest for this exact `error_reason` restricted to
    the last 2h — **0 rows**; max `written_at` for the whole population is 2026-08-16T04:34Z (~8h stale at check time,
    2026-08-16T12:42Z). `gcloud compute instances list` confirms exactly ONE Tardis-consuming VM running right now
    (`cefi-queue-heavy-binancefutu-x17-20260815-220349`) — the cap is currently respected, no active violation.
  - **Noted in passing, NOT shipped (out of this escalation's confirmed-root-cause scope)**: `launch-cefi-sharded-backfill.sh`
    has `DRY_RUN`/`FORCE`/`SINGLE_VM_QUEUE` all defaulting to the literal string `"250"` (line 81-98) — almost
    certainly a copy-paste artifact from the correct `MAX_CONCURRENT="${MAX_CONCURRENT:-250}"` line, since every
    downstream check on these three vars is a strict `== "1"` comparison, so `"250"` is functionally identical to any
    other non-"1" default (confirmed via grep of every callsite) — i.e. cosmetic/confusing but NOT the cause of this
    incident. Not fixing it here since it has zero behavioral effect and isn't this escalation's diagnosed root cause;
    flagging for whoever next touches that launcher's readability.
  - **Also observed (separate, NOT this alert's cause)**: at dispatch time, 304 `cefi-aster-*`/`cefi-hyperliquid-*`
    VMs were concurrently RUNNING (via `launch-cefi-hl-aster-historical-backfill.sh`'s `SHARD_DAYS` fine-sharding,
    `MAX_CONCURRENT=250`). Confirmed these are Tardis-CAP-EXEMPT by design (`tardis-concurrency-guard.sh`'s own
    `TARDIS_CAP_EXEMPT_VENUES=(HYPERLIQUID ASTER EXTENDED-STARKNET COINBASE-CDE)` — HL/ASTER/LIGHTER/EXTENDED never
    open an authenticated `datasets.tardis.dev` connection) so they do not contend for the Tardis lock and are NOT
    implicated in this DP-FETCH-009 finding. Whether 304 concurrently-running e2-highmem-4 VMs is itself a billing-waste
    concern is out of scope for this escalation (that's `/vm-preemption-billing-waste-audit`'s remit, not a DP-FETCH
    finding) — not filing a separate note, flagging here only so a future reader doesn't re-walk the same red herring.
  - **DP-FETCH-009 disposition**: stale/self-resolved, not an active pipeline break — no code fix shipped this turn
    (the classification is already correct; the proximate VM-overlap condition has already cleared; the only
    candidate code smell found has zero behavioral effect). No code/report changes; this Progress Log entry is the
    only change this turn.

- **2026-08-16 (slot 22, data_pipeline_failure escalation `agt-b6c337`, DP-FETCH-009, 3rd occurrence — confirmed
  duplicate dispatch of the same underlying alert slot 10 just resolved above)**: Dispatched off a
  `check_high_attempted_failed` page for `asset_group=cefi data_type=book_snapshot_5` (8,002 `attempted_failed` cells
  of 172,799 attempted; 2,260 fresh in the last 1d) — the same 2,260-fresh-row population slot 10's entry immediately
  above already root-caused (numbers match to within manifest-write drift: 173,333→172,799 attempted).
  - Re-queried the live cefi manifest independently (fresh `download_bytes` + column-pruned read of
    `_index/availability_index.parquet`, not slot 10's cached numbers): of 295,973 total `book_snapshot_5`
    `attempted_failed` rows corpus-wide, **0 rows have `written_at` in the last 1h/2h/4h/8h** — the max `written_at`
    across the entire population is still **2026-08-16T04:34:26Z**, identical to slot 10's finding, at a check time of
    2026-08-16T14:21Z (**~9h50m with zero new writes**). The `error_reason="Tardis HTTP 403 code=274
    concurrent-IP-lock"` slice (5,765 rows corpus-wide) shows the same max `written_at` — confirms this is not a
    live, ongoing failure; it stopped writing hours before this dispatch even started.
  - `gcloud compute instances list --filter="status=RUNNING"` shows exactly **ONE** Tardis-consuming VM
    (`cefi-queue-heavy-binancefutu-x17-20260815-220349`) — the concurrency cap is respected, no active violation.
  - **Conclusion**: identical disposition to slot 10's — stale/self-resolved, not an active pipeline break, no code
    fix needed (classification is correct; the transient VM-overlap condition cleared hours ago). No code changes
    shipped this turn.
  - **Flagging the redispatch itself as the residual gap** (adjacent finding, not fixed here — out of a one-shot
    escalation worker's scope to safely edit the alerting-service dedup/cooldown code): `DP_RUN_MOSTLY_EMPTY`
    (which DP-FETCH-009 reuses per `data-pipeline-alerts.md`'s registry note) has a 1800s (30-min) cooldown entry in
    `_RECURRING_ALERT_COOLDOWNS`, which should have suppressed a re-page for a condition that stopped writing at
    04:34Z — this is the 3rd escalation dispatch for what is functionally the SAME already-diagnosed finding within
    one day (2026-08-09 ASTER occurrence, 2026-08-16 slot-10 Tardis occurrence, 2026-08-16 slot-22/this one). Slot
    10's entry above already flagged the detector's freshness signal as misleading for `written_at`-refreshed-without-
    new-fetch populations; this adds a second data point (the cooldown/dedup layer also isn't preventing the SAME
    stale finding from re-paging a fresh escalation slot hours later). Worth a `/data-pipeline-alerts-reconcile` pass
    on the DP-FETCH-009/`DP_RUN_MOSTLY_EMPTY` cooldown-vs-detector-cadence relationship if this recurs a 4th time. No
    code/report changes; this Progress Log entry is the only change this turn.

- **2026-08-16 (slot 3, data_pipeline_failure escalation `agt-de9c44`, DP-FETCH-009, 4th occurrence today — the
  trigger slot-22's entry above explicitly named)**: Dispatched off a `check_high_attempted_failed` page for
  `asset_group=cefi data_type=book_snapshot_5` (18,945 `attempted_failed` cells of 181,427 attempted [trailing-window
  figures — the detector windows its threshold check, unlike the corpus-wide numbers below]; 11,884 fresh in the last
  1d). This IS the 4th-recurrence trigger slot-22 named — but NOT a repeat of the same stale Tardis-403 finding: a
  fresh, independent, unfiltered query of the live manifest surfaced a THIRD, previously-uncharacterized contributor
  that fully explains why the fresh-window count roughly quintupled since slot-22's check (2,260 → this alert's
  11,884).
  - Queried the live cefi manifest independently (`read_availability_index_safe(columns=[venue, data_type,
    capture_status, error_reason, date, written_at, service_name], filters=[data_type=book_snapshot_5,
    capture_status=attempted_failed])`, targeted row-group-pushdown read, NOT scoped to any single error_reason up
    front): **309,279 total rows corpus-wide** (up from slot-22's 295,973 measured ~7h earlier — the +13,306 delta is
    accounted for below, not unexplained growth). Of the 15,566 rows with `written_at` in the last 24h, **100% resolve
    to exactly 3 error_reasons, zero unexplained**: `CORRECTIVE_MIGRATION_queue_mode_tier3_sentinel_no_prior_capture_
    check_2026_08_16` (13,306, 85.5%), `Tardis HTTP 403 code=274 concurrent-IP-lock` (2,259, 14.5% — the SAME
    population slot-10/slot-22 already root-caused and closed as self-resolved), and `Tardis HTTP 500` (1). Re-checked
    recency on this same population: 0 rows with `written_at` in the last 1h/2h/4h/8h; max `written_at` across the
    WHOLE fresh subset is 2026-08-16T04:38:33Z (~16.5h stale at this dispatch's check time, 2026-08-16T21:09Z) — not
    currently live-writing, matching slot-10/22's own freshness finding.
  - **The new contributor, `CORRECTIVE_MIGRATION_queue_mode_tier3_sentinel_no_prior_capture_check_2026_08_16`
    (13,306 rows, the dominant slice), is NOT a bug — it is the intentional, self-correcting side effect of an
    ALREADY-SHIPPED, ALREADY-CLOSED fix from a DIFFERENT issue doc filed and closed by another slot earlier the same
    day**: `plans/active/issues/cefi_queue_mode_tier3_sentinel_false_empty_confirmed_2026_08_16.md` (all 3 `[CODE]
    P0`/`[DATA] P0` todos `[x]` — verified directly, only 2 unrelated `P3` cleanup items remain open). That doc's own
    root cause: a `SINGLE_VM_QUEUE=1` CeFi Tardis backfill's Tier-3 sentinel fan-out (`sentinels.py::_emit_tier3_for_
    dt`) wrote `empty_confirmed` over shards with a pre-existing real `captured` row, without checking the manifest
    first. The fix (code `market-tick-data-service@f134d16595c3e5d1761ec76a7f40041535a6f4e3` + a CAS-write manifest
    migration script `migrate_cefi_queue_mode_false_empty_confirmed_2026_08_16.py`) deliberately flips every affected
    row `empty_confirmed → attempted_failed` **on purpose**, because `check_shard_freshness(..., retry_failed=True)`
    (the default) then naturally re-attempts them on the next backfill pass — a real captured parquet gets correctly
    re-discovered, a genuinely empty shard gets correctly re-confirmed empty. This population is DESIGNED to sit as
    `attempted_failed` temporarily until re-capture completes, which independently cross-checked evidence confirms is
    already in motion: that doc's todo 3 confirms a fresh relaunch, `cefi-binance-futures-2026-heavy-20260816-182747`
    (2026-08-16T18:27Z, ~2.5h before this dispatch), and a separate same-day peer audit
    (`plans/audit/results/data_pipeline_reconciliation_cefi_2026_08_16.md` §3) independently reached the identical
    "NOT a new problem... already-closed same-day fix" verdict for the same sentinel string on a different venue
    slice (BYBIT-FUTURES). Three independent readings converge — high confidence this is correctly classified.
  - **DP-FETCH-009 disposition**: no code fix needed or shipped this turn — the underlying data-correctness bug
    (Tier-3 sentinel) is already fixed and shipped; the elevated `attempted_failed` count is the deliberate, expected,
    self-healing output of that fix, actively resolving via an already-running relaunched VM; the remaining slice is
    the same already-closed transient Tardis-403 finding. **This is genuinely the 4th same-day dispatch for
    functionally the same underlying "elevated attempted_failed count, no new live bug" disposition** (2026-08-09
    ASTER, slot-10 Tardis-403, slot-22 Tardis-403, this one) — slot-22's entry explicitly flagged a
    `/data-pipeline-alerts-reconcile` pass as warranted once this recurred a 4th time; it has now. Not running that
    reconcile pass myself — it targets alerting-service/deployment-service detector+cooldown code, a different
    repo/scope than this escalation's `market-tick-data-service` target and a materially larger, differently-scoped
    change than a one-shot data_pipeline_failure dispatch should make unreviewed; recommending it explicitly as the
    next actionable step for whoever picks this up next (main/operator/a `/data-pipeline-alerts-reconcile` dispatch).
    $AUTHORING_SLOT for this dispatch (`dp-fleet-monitor`) is not a numeric slot id, so the standard
    ping-authoring-slot step is skipped per this role's own instruction (no real originator to notify; the dispatch-
    time Slack alert already covered the FYI). No code/report changes; this Progress Log entry is the only change
    this turn.
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries) — re-verified all 3 entries resolve on
  disk and remain accurate; the operator ruling + subsequent gating checks since the last marker reference only the
  already-scoped sibling backfill plan, no new dependency.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries).
