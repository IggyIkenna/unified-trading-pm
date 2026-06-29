---
doc_type: issue
title: "IS sports manifest eu regression — 143K+ weather/SFI/TM rows overwritten to expected_unattempted at 2026-06-28T21:31"
created: 2026-06-29
source:
  - plans/active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md
assigned_vm: planning
status: active
priority: P0
summary: "Full-history cleanliness audit (task 007, 2026-06-29) revealed that previously verified gates for three sources have REGRESSED in the IS sports manifest:"
nature: process
asset_group: cross-asset
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

## What I found

Full-history cleanliness audit (task 007, 2026-06-29) revealed that previously
verified gates for three sources have REGRESSED in the IS sports manifest:

| Source | Gate status (2026-06-27) | Status now (2026-06-29 05:13 UTC) | Regression |
|--------|--------------------------|-----------------------------------|------------|
| open_meteo / WEATHER | pending_fetch=0 ✅ | eu=144,072, af=51, **pending_fetch=143,935** ❌ | 143,978 eu rows |
| soccer_football_info / SFI_PROGRESSIVE_STATS | pending_fetch=0 ✅ | eu=137,011, af=10, **pending_fetch=136,833** ❌ | 136,917 eu rows |
| transfermarkt / PLAYER_VALUES | eu=6,845 (expected) ✅ | eu=36,050, **pending_fetch=36,050** ❌ | 34,686 eu rows added |

All regressed eu rows share `written_at=2026-06-28T21:31:49.534565+00:00` and
`service_name=instruments-service`. The eu rows cover the FULL history range
(not a 3-day rolling window), indicating a full-history IS enumeration ran at that time.

**Evidence**: IS manifest `availability_index.parquet` (downloaded 2026-06-29 05:30 UTC,
last written by consolidator at 2026-06-29T05:13:51 UTC).

Previously typed rows (EXPECTED_NO_PROVIDER_COVERAGE) are partially preserved:
- Weather: 16,844 ec rows still typed
- SFI: 11,905 EXPECTED_NO_PROVIDER_COVERAGE + 57,694 EXPECTED_NO_FIXTURE
- TM: 198,461 EXPECTED_NO_PROVIDER_COVERAGE (most survived for TM)

The 2026-06-28T21:31 eu rows have NEWER timestamps than the 2026-06-27 typed rows →
consolidator's last-write-wins picked the eu rows, overwriting the typed ones.

**Secondary batch**: 94 eu rows per source written at `2026-06-29T01:30:55` (same pattern,
smaller batch — likely the daily IS enumeration's 3-day rolling window).

## Why it matters

1. **Data correctness regression**: Three sources previously verified at pending_fetch=0
   are now showing 100K+ pending_fetch. The manifest now reports these dates as "not yet
   fetched" when data was confirmed present.
2. **Gate block for task 007**: Full-history cleanliness gate cannot flip until this is
   fixed AND understat VM completes (ETA ~2026-07-01) AND footystats VMs complete.
3. **Recurring risk**: If the IS process continues running periodically, re-typing every
   time is not sustainable. The root cause must be fixed.

## Root cause (partial)

The IS sports batch (`instruments-service --operation instruments --mode batch
--asset-group sports`) at 2026-06-28T21:31:49 UTC wrote `expected_unattempted` rows
for the FULL sports history range (not just recent dates). These rows were merged into
the main index by the consolidator at 05:13 UTC on 2026-06-29.

The IS batch mode does not currently check whether a row is already `empty_confirmed`
(typed) before writing a new `expected_unattempted` row. Since the new rows have newer
`written_at`, they win in last-write-wins consolidation.

**Root cause to identify**: What triggered the full-history sports IS enumeration at
21:31 UTC on 2026-06-28? Candidates:
- A scheduled job in the sports scheduler (`launch-sports-scheduler-vm.sh` VM daemon)
- A manual operator trigger
- A Cloud Scheduler job that runs full-history backfill periodically

## Recommended decision

1. **Immediate (P0)**: Identify the IS process/job that ran at 21:31 UTC on 2026-06-28
   and emitted full-history eu rows. Check sports scheduler VM logs for that timeframe.
2. **Fix (P0)**: In instruments-service IS batch mode, before writing `expected_unattempted`
   for a (date, venue, data_type, league) row, check if the row already has a
   non-`expected_unattempted` status. If already confirmed/typed, skip. This prevents
   the IS batch from overwriting typing script output.
3. **After fix (P1)**: Re-run the three typing scripts to restore correct state:
   - `type_weather_eu_no_provider_coverage_2026_06_27.py --apply`
   - `type_sfi_eu_no_provider_coverage_2026_06_27.py --apply`
   - `type_tm_non_provider_coverage_2026_06_27.py --apply`
4. **Verify (P1)**: Re-run task 007 full-history audit after fix + re-typing + all VMs complete.

## Todos

- [x] [INVESTIGATE] P0. Identify IS process that wrote full-history eu rows at 2026-06-28T21:31 UTC (check sports scheduler VM + Cloud Scheduler logs). (repo: instruments-service)
      ✅ — 2026-06-29: Root cause confirmed via git log + plan progress log. Trigger = `run_sports_enrichment_core_p2a_2026_06_27.sh` coordinator (PID 4003012, planning VM) — its `sports_chunked_backfill.sh` invocation for FIXTURE_EVENTS (from 2020-06-06→today) ran the IS batch at 21:31 UTC. IS batch `_enumerate_v2_sports` writes `expected_unattempted` for the COMPLETE cross-join (all entities × all dates), not just the requested entity — so WEATHER, SFI_PROGRESSIVE_STATS, and PLAYER_VALUES rows were stamped with newer timestamps, overwriting the typing scripts' `empty_confirmed` rows via last-write-wins consolidation. Evidence: `sports_p2_history_apifootball_2015_to_present_2026_06_27.md` progress log §2026-06-28: "FIXTURE_EVENTS EU attempted_at = 2026-06-28T21:31 (active enumeration ~10 min ago)" + "Gate FAILS — enrichment coordinator (PID 4003012, planning VM) is still running". Secondary batch at 01:30:55 UTC = same coordinator continuing on subsequent entity/chunk. NOT Cloud Scheduler (runs 13:30 UTC) and NOT sports-scheduler-vm (Tier-1 uses lookback=1/lookahead=7, not full history).
- [x] [CODE] P0. Fix instruments-service IS batch mode to skip writing expected_unattempted rows when the manifest already shows non-eu status for that (date, venue, data_type, league) key — prevents typing scripts from being overwritten. (repo: instruments-service)
      ✅ — instruments-service@1835e11: `_download_manifest` in `enumerate_expected_universe.py` now also downloads all `_index/per_vm/` shards and pd.concat them into the manifest df before building the present_set. The `_enumerate_v2_sports` check `if row_key not in present_set` then correctly sees typed rows even if they haven't been consolidated yet — preventing eu overwrite. Root cause was race between typing script (writes empty_confirmed per-VM shard) and enumerator (reads only consolidated index, misses shard, writes eu → newer timestamp wins consolidation).
- [x] [SCRIPT] P1. Re-run type_weather_eu_no_provider_coverage_2026_06_27.py --apply after IS batch fix is deployed. (repo: instruments-service)
      ✅ — 2026-06-29T05:37: applied. 144,072 WEATHER eu rows re-typed → empty_confirmed(EXPECTED_NO_PROVIDER_COVERAGE). Per-VM shard written: gs://instruments-store-sports-prd-central-element-323112/_index/per_vm/type-weather-eu-20260629.parquet. Consolidator merges next cycle.
- [x] [SCRIPT] P1. Re-run type_sfi_eu_no_provider_coverage_2026_06_27.py --apply after IS batch fix is deployed. (repo: instruments-service)
      ✅ — 2026-06-29T05:37: applied. 137,011 SFI eu rows re-typed → empty_confirmed(EXPECTED_NO_PROVIDER_COVERAGE). Per-VM shard: type-sfi-eu-20260629.parquet.
- [x] [SCRIPT] P1. Re-run type_tm_non_provider_coverage_2026_06_27.py --apply after IS batch fix is deployed. (repo: instruments-service)
      ✅ — 2026-06-29T05:38: applied. 0 non-TM-covered PLAYER_VALUES eu rows found. 36,050 TM eu rows = TM-covered leagues that need backfill.
- [x] [DATA] P1. Launch TM backfill VM to re-cover 2021-01-01→2026-06-29 and resolve 34,686 regression eu rows (47 leagues × 738 dates, written_at 2026-06-28T21:31 by regression enum, overwriting previously captured/empty_confirmed rows in the consolidated index).
      ✅ — 2026-06-29T06:03: `tm-backfill-20260629-060317` SPOT e2-standard-8 asia-northeast1-c launched for range 2021-01-01→2026-06-29. Tarball updated to instruments-service@051e5a8 (includes enumerate fix @1835e11). GCS log: `gs://deployment-scripts-central-element-323112/vm-logs/tm-backfill-20260629-060317/run.log`. After VM completes: consolidator merges → TM pending_fetch returns to near 0 (baseline 6,845 for window-closed dates).
- [ ] [VERIFY] P2. Re-run task 007 full-history audit after all VMs complete (Understat ~2026-07-01, TM ~2026-07-01, Footystats) + typing re-applied → flip plan checkbox. (repo: unified-trading-pm)
