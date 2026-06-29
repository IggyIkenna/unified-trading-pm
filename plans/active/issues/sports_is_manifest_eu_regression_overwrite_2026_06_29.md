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

- [ ] [INVESTIGATE] P0. Identify IS process that wrote full-history eu rows at 2026-06-28T21:31 UTC (check sports scheduler VM + Cloud Scheduler logs). (repo: instruments-service)
- [ ] [CODE] P0. Fix instruments-service IS batch mode to skip writing expected_unattempted rows when the manifest already shows non-eu status for that (date, venue, data_type, league) key — prevents typing scripts from being overwritten. (repo: instruments-service)
- [ ] [SCRIPT] P1. Re-run type_weather_eu_no_provider_coverage_2026_06_27.py --apply after IS batch fix is deployed. (repo: instruments-service)
- [ ] [SCRIPT] P1. Re-run type_sfi_eu_no_provider_coverage_2026_06_27.py --apply after IS batch fix is deployed. (repo: instruments-service)
- [ ] [SCRIPT] P1. Re-run type_tm_non_provider_coverage_2026_06_27.py --apply after IS batch fix is deployed. (repo: instruments-service)
- [ ] [VERIFY] P2. Re-run task 007 full-history audit after all VMs complete + typing re-applied → flip plan checkbox. (repo: unified-trading-pm)
