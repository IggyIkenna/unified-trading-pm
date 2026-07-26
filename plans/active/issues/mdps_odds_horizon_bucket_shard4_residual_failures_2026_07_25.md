---
doc_type: issue
title:
  MDPS odds_horizon_bucket reprocess shard4 (2025-01-01..2026-07-25) — 22 attempted_failed + 4 LOSS-GUARD-BLOCKED dates,
  all honest upstream gaps
summary: >-
  The 4-way sharded MDPS `odds_horizon_bucket` reprocess (sports_satellite_ao_dispatch_batch2_2026_07_24.md's league_id
  casing migration, step 3) completed on all 4 shards. Shards 1-3 (2020-06-06..2024-12-31) had ZERO failures. Shard4
  (2025-01-01..2026-07-25) exited rc=1 with 22 attempted_failed + 4 LOSS-GUARD-BLOCKED dates out of 571. Investigated
  every distinct failure class by direct GCS read — all are honest, correctly-classified upstream data gaps or
  protective refusals, NOT script defects and NOT silent data loss. Filed for tracking + eventual retry, per
  findings-closure discipline — no code fix needed, but the retriable dates should not be forgotten.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer]
tags: [sports, mdps, odds-horizon-bucket, attempted-failed, loss-guard, honest-absence, league-id]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/active/issues/mdps_odds_horizon_bucket_reprocess_launch_prep_2026_07_25.md,
    /plans/active/issues/sports_league_id_swap_silently_reverted_toctou_2026_07_25.md,
    /plans/active/issues/odds_api_raw_ingestion_gap_2026_06_21_24_2026_07_26.md,
  ]
created: 2026-07-25
assigned_vm: NA
parent_epic: sports_master
execution_scope: local-only
priority: P2
estimate_class: infra
source: sports_satellite_ao_dispatch_batch2_2026_07_24.md, league_id casing migration todo, step (3) execution
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
---

# MDPS odds_horizon_bucket reprocess shard4 residual — 26 dates, all honest gaps

## What I found

Ran the sharded reprocess (`launch-mdps-sports-bucket-vm.sh`, 4 VMs, `force` mode) per
`mdps_odds_horizon_bucket_reprocess_launch_prep_2026_07_25.md`'s ready-to-execute recipe:

| Shard                                | Range                 | Dates | Success | Empty | Failed | Loss-guard-blocked | exit  |
| ------------------------------------ | --------------------- | ----- | ------- | ----- | ------ | ------------------ | ----- |
| `mdps-sports-bucket-20260725-035949` | 2020-06-06→2021-12-31 | 574   | 532     | 42    | 0      | 0                  | 0     |
| `mdps-sports-bucket-20260725-040027` | 2022-01-01→2023-06-30 | 546   | 493     | 53    | 0      | 0                  | 0     |
| `mdps-sports-bucket-20260725-040053` | 2023-07-01→2024-12-31 | 550   | 446     | 104   | 0      | 0                  | 0     |
| `mdps-sports-bucket-20260725-040119` | 2025-01-01→2026-07-25 | 571   | 449     | 96    | **22** | **4**              | **1** |

Total 166,751 shards / ~5.4M bucketed rows written across all 4. Only shard4 has a residual. Read the FULL `run.log`
(not just the tail) to classify every one of the 22+4 dates — 3 distinct classes, all honest:

1. **18 dates: `ADAPTER_RETURNED_EMPTY_OUTPUT`** (2025-07-31, 08-05, 08-12, 08-13, 08-21, 08-26, 09-02, 09-03, 09-04,
   09-09, 09-10, 10-07, 10-14, 11-11, 11-13, 12-18, 12-24, 12-31) — raw data present but the adapter's zombie-tick
   filter removes every row. **Already pre-vetted as working-as-designed** in
   `mdps_odds_horizon_bucket_reprocess_launch_prep_2026_07_25.md`'s own dry-run investigation (which hit this exact
   pattern on 2025-09-02/03, confirmed intentional honest-absence hardening per the 2026-06-22
   `UnprovenHonestAbsenceError` fix — not a bug). Correctly recorded `attempted_failed` (retriable), never a false
   `empty_confirmed`.
2. **4 dates: `RAW_ODDS_SHAPE_UNRECOGNIZED`** (2026-06-21, 06-22, 06-23, 06-24) — NEW pattern, not previously seen.
   Directly verified via `gcloud storage ls -r` on the raw bucket for all 4 dates: **only `instrument_type=sport`
   meta-snapshot files exist** (`ODDS_API:SPORT:soccer_epl.parquet` / `...soccer_italy_serie_a.parquet`, under both
   `pipeline_mode=batch_odds_api` and `pipeline_mode=live_odds_api`) — **zero real `instrument_type=odds`
   `data_type=trades` objects** for any of the 4 days. This is a genuine 4-consecutive-day upstream ingestion gap (the
   odds fetch pipeline apparently only wrote sport-metadata snapshots those days, not real odds), not a script defect —
   the reprocessor correctly identified these as non-consumable and refused to fabricate output, recording
   `attempted_failed`.
3. **4 dates: `LOSS_GUARD_BLOCKED`** (2025-02-16, 2025-08-14, 2025-09-18, 2025-10-23) — the loss-guard (added per this
   same migration's `UnprovenHonestAbsenceError`-class hardening) refused to re-derive because doing so would have
   SHRUNK the corpus vs. what's already on disk (3-62 (fixture,bookmaker) observations would be lost per date).
   **Working exactly as designed** — "Upstream is thinner than its own descendant — refusing to shrink the date."
   Existing shards for those 4 dates were left untouched; **zero data was lost**.

## Why it matters

No code fix is needed — every one of the 26 dates is a correctly-classified honest state, not a defect introduced by
this migration or the reprocess script. But `attempted_failed` is a RETRIABLE state, not a terminal one — these 26 dates
should be picked up again on a future `full`-mode (resume-friendly, not `force`) re-run of shard4's range once/if the
underlying upstream odds source backfills 2026-06-21..24 and the loss-guard-blocked dates' true observation counts
stabilize. Left untracked, this manifest residual would silently persist forever (nothing currently re-polls just these
26 dates).

## Recommended decision

- No P0/P1 action — file for future retry, does not block flipping the parent league_id-casing-migration checkbox in
  `sports_satellite_ao_dispatch_batch2_2026_07_24.md` (steps 1-3 of that todo are otherwise clean; `batch_footystats`
  copy+swap, step 4, is tracked separately in `mdps_odds_horizon_bucket_reprocess_launch_prep_2026_07_25.md`'s
  addendum).
- Optionally escalate the 4 `RAW_ODDS_SHAPE_UNRECOGNIZED` dates (2026-06-21..24) to whoever owns the odds_api raw
  ingestion pipeline, since 4 consecutive days of only-metadata-no-real-data is unusual and may indicate a real upstream
  fetch problem worth a separate look (out of scope for this reprocess task itself).

## Todos

- [ ] [DATA] P2. Re-run shard4's range (`bash scripts/vm/launch-mdps-sports-bucket-vm.sh 2025-01-01 2026-07-25 full` —
      note `full`, not `force`, so it resumes/skips already-captured days and only retries the 22 `attempted_failed` + 4
      `LOSS_GUARD_BLOCKED` dates) once the upstream odds_api source for 2026-06-21..24 has real data and/or enough time
      has passed for the loss-guard-thin dates to catch up; verify manifest afterward. (repo:
      market-data-processing-service, deployment-service)
- [x] ✅ [DATA] P3. **DONE 2026-07-26 (slot-10)** — Flagged the 2026-06-21..24 4-day only-meta-snapshot gap to the
      odds_api raw-ingestion owner. Escalation issue doc:
      `issues/odds_api_raw_ingestion_gap_2026_06_21_24_2026_07_26.md` (re-verified the gap live via a scoped
      `gcloud storage ls -r` on exactly the 4 dates, both `pipeline_mode` variants — unchanged from this doc's original
      finding). Cross-linked both directions (this doc's `related:` above + the new doc's own `related:`). No
      backfill/re-derivation attempted — escalation/documentation only, per the todo's own scope.
