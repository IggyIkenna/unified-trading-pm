---
title: Sports golden-window attempted_failed remediation — mostly misclassification, not missing data
created: 2026-06-24
parent_epic: sports_master
source:
  - "Coverage audit 2026-06-24: golden window (2025-09-01..2025-11-30) instruments 98.0% / market-data 94.1%; ~5,900 attempted_failed cells"
locked_by: live-defi-rollout
priority: P2
status: active
---

## Diagnosis (measured 2026-06-24)
Golden window is effectively at 100% on FIXTURES/MATCHES/TEAMS/VENUES/LEAGUES/ODDS/XG/STANDINGS/PLAYER_STATS. The
~5,900 `attempted_failed` cells are **mostly misclassification, not missing data**:
- **~258 PLAYER_VALUES + FIXTURE_LINEUPS + FIXTURE_STATS** — phantom false-positive: parquet EXISTS on disk; the phantom
  reconciler probed `candidate_parquet_paths` WITHOUT the row's `pipeline_mode=`, so it missed the post-migration
  canonical path. NOT a gap.
- **~165 XG_SHOTS (0% in-window)** — understat over-broad 404: a single per-league 404 flips ALL that-day expected
  leagues to `record_failed(HTTP_NOT_FOUND)` instead of `record_empty`; the genuinely-missing leagues are an honest
  understat coverage gap, not failures.
- **5,265 market-data `trades` (BETFAIR/MATCHBOOK/PINNACLE, source=api_football)** — WRONG SOURCE: the canonical
  sports bookmaker-odds source is **odds-api** (`batch_odds_api`), not api_football. api_football is per-fixture detail
  only. These cells are redundant/wrong-source → wipe (verify odds-api covers them first).
- **~90 INJURIES** — real upstream `ApiFootballResponseError`; retry.

Also surfaced: **no Slack alert fires on `attempted_failed`** — the VM exit-code monitor classifies exit0+some-capture
as CLEAN even with thousands of failed cells, so a partial-failure backfill is invisible (the operator's "why don't
alerts trigger on VM ERRORs" — confirmed gap).

## Fixes
- [x] ✅ #1 [SCRIPT] P1. Phantom reconciler: pass row `pipeline_mode` into `candidate_parquet_paths` so canonical
  post-migration parquets aren't false-flagged. — instruments-service@c01bb1c (QG-green). Cross-asset-group blast
  radius (the reconciler runs for every AG).
- [ ] #1b [SCRIPT] P1. Prod: `reconcile_phantom_manifest_rows_all.py --asset-group sports --unphantom --apply` re-run
  flips the ~258 false phantoms back to `captured` (consolidator-paused, verify manifest).
- [ ] #2 [CODE] P2. understat per-league 404 scoping (`understat.py`): adapter exposes WHICH leagues errored; orchestrator
  records `record_failed` only for errored leagues, `record_empty(EXPECTED_NO_FIXTURE)` for the rest. Mirrors the
  transfermarkt per-league error-dict pattern. (Same file the off-season-guard agent just shipped — coordinate.)
- [x] ✅ #3 [DATA] P1. api_football sports odds wipe DONE (operator: full wipe, odds-api is canonical). Dropped ALL
  1,398,423 source=api_football MTDS-sports rows (trades + odds_horizon_bucket_* + ARBITRAGE_OPPORTUNITY) + deleted
  231,532 `batch_api_football` GCS objects. `_index` 1,760,262 → 361,839. `trades` now odds_api 211,299 captured /
  **0 failed / 100.0%** (golden-window 5,265 failures gone). Snapshot:
  `_index/snapshots/pre_api_football_wipe_2026_06_24.parquet` (reversible). Consolidator paused→resumed. Script:
  `market-tick-data-service/.../scripts/wipe_api_football_sports_odds_2026_06_24.py` (oneoff; commit pending a clean
  MTDS tree — foreign WIP present; delete after GCS-orphan-sweep).
- [ ] #3b [DATA] P2. odds-api backfill gaps surfaced by the wipe: 3 leagues odds_api doesn't carry
  (`soccer_uefa_champs_league`, `soccer_china_superleague`, `soccer_russia_premier_league`, 2025-H2) + the in-scope
  gap-dates behind the former 112,653 api_football failures — backfill via odds-api (the canonical source), not
  api_football. (UEFA Champions League is the notable one.)
- [x] ✅ #4 [CODE] P2. attempted_failed Slack alert in deployment-service — deployment-service@cb330f7 (QG-green, 8 tests): per (asset_group, data_type)
  failure-batch alert so an exit0 backfill that fails thousands of cells is no longer invisible. (Gate on real failures,
  not misclassified honest-absence — fix #1/#2/#3 first so it isn't noisy.)
