---
doc_type: issue
title: "CEFI COINBASE-CDE — URDI returns zero records, real crash on all 3 legs"
summary: >-
  /data-pipeline-check-is mid-backfill spot-check for cefi (day=2026-03-15) found COINBASE-CDE is a genuine data gap,
  not the known raw-vs-canonical-id checker false-positive that affected the other 23 venues in the same run.
  COINBASE-CDE crashes with a real Traceback ("URDI returned zero records") on force, skip, AND live legs — confirmed
  via both the checker's own no_parquet_at verdict and direct VM run.log inspection.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [cefi, coinbase-cde, urdi, data-gap, pipeline-e2e-check]
related:
  [
    /plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-07-28"
priority: P1
parent_epic: cefi_master
assigned_vm: NA
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by: live-defi-rollout
locked_since: 2026-05-21
source: >-
  Found during the /data-pipeline-check-is mid-backfill spot-check for cefi (todo 2 of
  cefi_track2_coverage_backfill_checkpoints_2026_07_25.md), day=2026-03-15, run 2026-07-28. Ground-truth VM run.log
  confirmed a real Traceback distinct from the run's other 25 venues' known checker false-positive/expected-absence
  patterns.
resolved_by:
---

# CEFI COINBASE-CDE — URDI returns zero records, real crash on all 3 legs

## Finding

During the `/data-pipeline-check-is` mid-backfill spot-check for cefi
(`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` todo 2), day `2026-03-15`, **COINBASE-CDE** was the ONE
genuine gap out of 26 MVP cefi venues checked — every other checked venue that showed a "failed" checker verdict was
confirmed via ground-truth run.log inspection to be the documented raw-vs-canonical-instrument-id migration
false-positive (real writes, checker just can't match rows during the migration — see `/data-pipeline-check-is` skill's
"Read the VM run.log as ground truth" section). COINBASE-CDE is different: it fails for real, on all three legs (force,
skip, live), with a genuine Python Traceback.

**Ground-truth run.log** (force-leg, VM `instr-backfill-cefi-pchk-0727220654-f-coinbase-cde`):

```
2026-07-27 23:48:21,569 INFO Venue override from CLI: ['COINBASE-CDE']
2026-07-27 23:48:22,296 INFO COINBASE-CDE: fetched 118 FUTURE instruments
2026-07-27 23:48:22,297 INFO URDI[COINBASE-CDE]: fetched 118 instruments
2026-07-27 23:48:22,416 ERROR URDI returned zero records for date=2026-03-15 asset_groups=['CEFI']. Venues attempted: ['COINBASE-CDE']. Check URDI adapter coverage and network connectivity.
2026-07-27 23:48:22,416 WARNING Handler InstrumentsHandler failed on payload 1: URDI returned zero records for date=2026-03-15 asset_groups=['CEFI']. Venues attempted: ['COINBASE-CDE']. Check URDI adapter coverage and network connectivity.
Traceback (most recent call last):
    return await _handle_zero_records(
  File "/home/ikennaigboaka/workspace/instruments/instruments_service/engine/orchestrator/process_zero_records.py", line 88, in _handle_zero_records
    return _zero_records_non_sports(
  File "/home/ikennaigboaka/workspace/instruments/instruments_service/engine/orchestrator/process_zero_records.py", line 698, in _zero_records_non_sports
RuntimeError: URDI returned zero records for date=2026-03-15 asset_groups=['CEFI']. Venues attempted: ['COINBASE-CDE']. Check URDI adapter coverage and network connectivity.
```

Note: URDI successfully fetches 118 FUTURE instruments for COINBASE-CDE (the reference-data catalogue call works), but
then reports "zero records" for the date — the crash happens in the transition between catalogue-fetch and per-date
record materialization, not in URDI's venue-list resolution.

**Checker verdicts (all 3 legs, consistent `no_parquet_at` — no parquet ever written)**:

| Leg   | Status | Parquet | Manifest             | Reason                                                                                                  |
| ----- | ------ | ------- | -------------------- | ------------------------------------------------------------------------------------------------------- |
| force | failed | 0       | no_matching_row      | `no_parquet_at:.../venue=COINBASE-CDE/; manifest_status_invalid:no_matching_row`                        |
| skip  | failed | 0       | no_matching_row      | `no_parquet_at:.../venue=COINBASE-CDE/; manifest_status_invalid:no_matching_row; skip_signal_not_found` |
| live  | failed | 0       | expected_unattempted | `no_parquet_at:.../venue=COINBASE-CDE/; manifest_status_invalid:expected_unattempted`                   |

Report: `instruments-service/pipeline_e2e_check_reports/data_pipeline_e2e_check_is_2026_03_15.md` (live-leg data;
force+skip ground-truth captured via direct VM run.log inspection, not separately persisted as the checker's own report
was superseded by the live-leg run using the same output filename).

## Scope note (not part of this finding)

Two other venues checked in the same run — KALSHI-PERP and POLYMARKET-PERP — also showed `no_parquet_at` on force+skip.
These are NOT the same class of bug: their ground-truth run.log showed a clean `exit_code=0` with
`"No active venues for date=2026-03-15"` (no Traceback), and the live leg's own MVP-scope check independently confirmed
both are `not_in_mvp_scope` — i.e. they are not true MVP-scoped venues for the current cutover and/or didn't exist as of
this historical spot-check date. No follow-up needed for these two.

## Todos

- [ ] [DATA] P1. **Root-cause why URDI/`process_zero_records.py::_zero_records_non_sports` treats COINBASE-CDE as
      genuinely zero-record for 2026-03-15** despite successfully fetching 118 FUTURE instruments moments earlier in the
      same run. Check whether COINBASE-CDE's date-filtering logic (`instruments after date filter`, per the pattern seen
      in other venues' logs) is dropping all 118 instruments for this date, or whether the crash is upstream of that
      filter. Repo: instruments-service. **Done when**: root cause identified and either fixed or explicitly confirmed
      as expected (e.g. COINBASE-CDE genuinely had zero listed instruments as of 2026-03-15) with evidence cited here.
- [ ] [DATA] P1. **Re-run `/data-pipeline-check-is --asset-group CEFI --venue COINBASE-CDE --day 2026-03-15` once the
      root cause is fixed** to confirm the venue now passes all 3 legs. Repo: instruments-service. **Done when**: a
      fresh run shows COINBASE-CDE passing (or a documented reason it's expected to stay absent for this date).

## Codex SSOTs

`/codex/02-data/four-surface-reconciliation-procedure.md` (venue-day gap classification),
`.claude/skills/data-pipeline-check-is/SKILL.md` (ground-truth run.log verification method — no new pattern introduced
by this doc, just applying the documented method to a genuinely-real finding).
