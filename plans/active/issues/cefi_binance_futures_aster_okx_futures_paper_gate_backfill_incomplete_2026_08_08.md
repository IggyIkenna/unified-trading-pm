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
