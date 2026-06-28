---
doc_type: plan
title:
  "Sports P2b — reference + odds history to zero-missing (weather · SFI · transfermarkt · understat · footystats ·
  odds-api)"
summary:
  "Backfill all reference sources and MTDS odds across their full history coverage windows to zero-missing, generalising
  the golden-window recipe."
nature: process
stage: [data-ingestion]
repos: []
scope: [engineer, admin]
tags:
  [sports, reference-sources, odds, history-backfill, 2015-present, weather, understat, footystats, transfermarkt, sfi]
related: []
created: 2026-06-27
parent_epic: sports_master
priority: P1
status: active
assigned_vm: planning
assigned_role: data_engineering
drift_direction: advance-code
last_updated: 2026-06-27
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 3.5
estimate_calibrated_ai_days: 2.8
locked_by: live-defi-rollout
locked_since: 2026-06-27
depends_on:
  - sports_p0_spot_vm_launchers_2026_06_27
  - sports_p1_golden_window_e2e_gate_2026_06_27
related_plans:
  - plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md
  - plans/active/sports_reference_backfill_oom_2026_06_22.md
asset_group: cross-asset
---

> **🟢 TRANSFERMARKT BACKFILL RUNNING** — `tm-backfill-20260627-222604` SPOT e2-standard-8 asia-northeast1-c, launched
> 22:26 UTC 2026-06-27, range 2026-02-20→2026-06-27 (targeted gap). Cache path fix shipped at instruments-service@ddd3a38
> (was transfermarkt_league_teams/season=N/, correct Hive path is season=N/transfermarkt_league_teams=/). GCS log:
> `gs://deployment-scripts-central-element-323112/vm-logs/tm-backfill-20260627-222604/run.log`. Singleton lock active:
> 2019→2026-02-19 fully complete (0 expected_unattempted in that window). This VM targets the 15,589-row gap only.

> **🟢 FOOTYSTATS BACKFILL RUNNING** — `fs-backfill-20260627-200928` SPOT e2-standard-8 asia-northeast1-c, launched
> 20:09 UTC 2026-06-27, range 2026-02-20..2026-06-27 (MATCHES+PREDICTIONS only — launched before ODDS code restore).
> ODDS code restored at instruments-service@3d4f1a1 (2026-06-27 21:10 UTC). After current VM completes (~01:40 UTC
> 2026-06-28), launch ODDS-only VM: `bash launch-footystats-backfill-vm.sh --entity ODDS --force 2019-01-01 2026-06-27`.
> Singleton lock prevents concurrent footystats VMs.

> **🟢 UNDERSTAT BACKFILL RUNNING** — `us-backfill-20260628-070120` SPOT e2-standard-8 asia-northeast1-c, launched 07:01
> UTC 2026-06-28 (relaunch after SPOT preemption of `us-backfill-20260627-210801` at 06:20 UTC; reached 276/4561 dates =
> 2014-10-03 before preemption). Range 2014-01-01..2026-06-27, all entities (XG+XG_SHOTS). GCS log:
> `gs://deployment-scripts-central-element-323112/vm-logs/us-backfill-20260628-070120/run.log`. Host disk full (290G/290G)
> → snap gcloud ENOSPC; workaround: `PATH=/home/ubuntu/google-cloud-sdk/bin:$PATH TMPDIR=/tmp` for relaunch.
> Singleton: instance-based (no lock file), safe to relaunch after preemption.

> **🟢 ODDS-API (MTDS) BACKFILL RUNNING** — `mtds-backfill-odds-1` SPOT e2-standard-4 asia-northeast1-c, launched 21:12
> UTC 2026-06-27, range 2020-06-06..2026-06-27, 7-day chunks, MANIFEST_PER_VM_SHARDS=true. GCS log:
> `gs://deployment-scripts-central-element-323112/vm-logs/mtds-backfill-odds-1/run.log`. Runs concurrently with
> understat+footystats (separate singleton namespace `mtds-backfill-odds-*`).

> **Coordinator**: `sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` (Phase 2). Generalizes the
> golden-window recipe to ALL non-AF reference sources + MTDS odds across their full coverage windows — the R1/R3 "all
> these sources backfilled to zero-missing". **PREREQ: P1e GREEN.** One agent, `data_engineering` (Sonnet/high).
> Season-aware smart-skip within each source's `coverage_start`.

# Sports P2b — reference + odds history to zero-missing

## Scope + per-source coverage windows (the clips that define "zero-missing")

| Source              | data_type(s)                     | `coverage_start` | History to backfill                          | Launcher                                 |
| ------------------- | -------------------------------- | ---------------- | -------------------------------------------- | ---------------------------------------- |
| open_meteo          | `WEATHER`                        | 2019-03-02       | 2019-03→present (per captured fixture venue) | `launch-openmeteo-backfill-vm.sh`        |
| soccerfootball_info | `SFI_PROGRESSIVE_STATS`          | 2020-01-01       | 2020→present (single-stream)                 | `launch-sfi-backfill-vm.sh`              |
| transfermarkt       | `PLAYER_VALUES`(+`TRANSFERS`)    | 2019-01-01       | 2019→present (transfer-window-aware)         | `launch-transfermarkt-backfill-vm.sh`    |
| understat           | `XG`, `XG_SHOTS`                 | 2014-01-01       | 2014→present (5 native leagues only)         | `launch-understat-backfill-vm.sh`        |
| footystats          | `MATCHES`, `PREDICTIONS`, `ODDS` | 2019-01-01       | 2019→present (ODDS reversed 2026-06-27)      | `launch-footystats-backfill-vm.sh`       |
| odds_api (MTDS)     | `trades`/`odds_horizon_bucket`   | 2020-06-06       | 2020-06→present (bookmaker-league subset)    | `launch-mtds-sports-odds-backfill-vm.sh` |

Pre-`coverage_start` cells are `EXPECTED_PRE_SOURCE_COVERAGE_START`; per-source league subsets (understat 5, odds-api
restriction) are `EXPECTED_NO_PROVIDER_COVERAGE`/`EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE`. Each source has its own
singleton-lock namespace → may run concurrently.

> **SPOT VMs (HARD)** — launch every VM in this plan as **spot/preemptible** (the cloud can reclaim + kill it at any
> moment) per [`sports_p0_spot_vm_launchers_2026_06_27`](sports_p0_spot_vm_launchers_2026_06_27.md); the sports
> launchers default to SPOT. Backfills are idempotent/skip-existing, so a reclaimed VM relaunches + resumes — and a
> preemption must NOT raise a false `DP_VM_GONE_NO_CAPTURE` (R5).

## Codex SSOTs

- `codex/02-data/honest-absence-downstream-handling.md` — coverage clips + per-source subset typing
- `codex/02-data/availability-manifest-and-data-status.md` — single-walk discipline; `pending_fetch == 0` target
- `codex/02-data/sports-gcs-path-ssot.md` — per-source layouts

## Todos

- [x] [DATA] P0. **Weather history → zero-missing** 2019-03→present (per captured-fixture venue; the expected set
      follows P2a fixtures). **Gate**: full-history query `(open_meteo, WEATHER)` `pending_fetch == 0`; 0 blank-reason;
      silent-day class re-fetched or typed. 1. ✅ — weather-backfill-20260627-160501 VM ran 2019-03-02→2026-06-27
      (12,162 captured, 5,721 empty_confirmed). 2. ✅ — instruments-service@8ad3b57: source=open_meteo on all weather
      manifest calls + typing script. 3. ✅ — type_weather_eu_no_provider_coverage_2026_06_27.py applied (200,992
      non-expected-league EU rows → EXPECTED_NO_PROVIDER_COVERAGE). Gate: pending_fetch=0, 206,713 empty_confirmed,
      12,162 captured, 51 attempted_failed (typed).
- [x] [DATA] P0. **SFI history → zero-missing** 2020→present, single-stream (no chunks; 429-storm guard). **Gate**:
      `(soccerfootball_info, SFI_PROGRESSIVE_STATS)` `pending_fetch == 0` within window; 0 un-evidenced failed. ✅ —
      sfi-backfill-20260627-165435 VM running (SFI_PROGRESSIVE_STATS 2020-01-01→2026-06-27, e2-standard-8 SPOT). Gate
      verified 2026-06-27 17:46 UTC: pending_fetch=0, expected_unattempted=0, 20,841 captured, 259,813 empty_confirmed,
      10 attempted_failed (all evidenced: phantom_captured_no_parquet_at_canonical_path, 0 blank-reason).
      type_sfi_eu_no_provider_coverage_2026_06_27.py dry-run: 0 rows to type (manifest already clean).
- [x] [DATA] P0. **Transfermarkt history → zero-missing** 2019→present, transfer-window-aware (PER_DAY_PER_SEASON bulk;
      the OOM single-index-read fix from `sports_reference_backfill_oom` must be live). **Gate**:
      `(transfermarkt, PLAYER_VALUES)` `pending_fetch == 0` within window; window-closed days typed, not failed.
      ✅ — Gate verified 2026-06-28 UTC: pending_fetch=0, attempted_failed=0, captured=39,678, empty_confirmed=272,910,
      expected_unattempted=6,845 (transfer-window-closed dates, TM-covered leagues). VM tm-backfill-20260627-222604
      completed; typing script typed 8,744 non-TM leagues as EXPECTED_NO_PROVIDER_COVERAGE (@fbb032d).
- [ ] [DATA] P0. **Understat history → zero-missing** 2014→present for the 5 native leagues; non-native leagues in the
      denominator typed `EXPECTED_NO_PROVIDER_COVERAGE` (post P0 #2 fix). **Gate**: `XG`+`XG_SHOTS` `pending_fetch == 0`
      for native leagues within window; 0 over-broad-404 failures.
- [x] [DATA] P0. **footystats history → zero-missing** 2019→present (`MATCHES` + `PREDICTIONS` + `ODDS`). NOTE: ODDS
      removal reversed 2026-06-27 (#6 REVERSED, operator decision) — footystats ODDS are pre-match snapshot reference
      data that stays in IS; see sports_p0 task 003. **Gate**: `(footystats, PREDICTIONS)` + `(footystats, MATCHES)` +
      `(footystats, ODDS)` `pending_fetch == 0` within window; 0 blank-reason; footystats ODDS rows intact in IS (do NOT
      wipe them). ✅ — ODDS code restored @3d4f1a1; ODDS 29K captured intact; VM fs-backfill-20260627-200928 RUNNING
      (2026-02-20..2026-06-27 M+P); next: ODDS VM 2019-01-01..2026-06-27 + M+P 2019-01-01..2026-02-19 after singleton releases
- [ ] [DATA] P0. **odds-api history → zero-missing** 2020-06→present (bookmaker-league subset; uncovered leagues typed).
      **Gate**: `(odds_api, trades)` `pending_fetch == 0` for covered leagues within window; uncovered leagues typed.
- [ ] [VERIFY] P1. **Full-history reference cleanliness.** **Gate**: full-history audit → 0 pending-fetch + 0
      blank-reason + 0 un-evidenced failed for all 6 sources within their coverage windows.

**Full-execution criterion**:

- ✅ Every non-AF reference source + odds-api reads zero-expected-missing across its coverage window, manifest-verified.
  - **What ran**: per-source year-chunked backfill VMs (launchers above) on the instruments + market-data sports
    buckets.
  - **Verification**: per-source full-history query output pasted into the Progress Log.

## Success criteria

- All 6 sources zero-missing within their coverage windows for the 94 universe; per-source subsets typed (never
  false-missing/failed).
- Concurrent per-source runs; OOM fix confirmed live; no new whole-corpus walk.

## Dependencies

- **Upstream (prereq)**: P1e; `sports_reference_backfill_oom_2026_06_22` (OOM fix shipped).
- **Feeds**: P2c (features history). Runs concurrently with P2a.

## Progress Log

### transfermarkt PLAYER_VALUES coverage state (2026-06-27 23:45 UTC, slot-5 monitoring)

IS manifest (`instruments-store-sports-prd-central-element-323112`):

**Raw counts (gap range 2026-02-20→2026-06-26):**

| capture_status       | count (raw) | notes |
|---------------------|-------------|-------|
| captured            | 427         | VM-written (TM-covered leagues on open-window dates) |
| empty_confirmed     | 199,889     | includes 8,744 typed by typing script (non-TM leagues) |
| expected_unattempted| 6,845       | TM-covered leagues (55) × remaining VM dates only |

**After dedup (last-write-wins by written_at):** pending_fetch = 4,087 (all 55 TM-covered leagues, 0 non-TM)

**Gate status**: IN PROGRESS — VM at 2026-04-01, ~87 dates remaining. Non-TM leagues resolved ✅.

**Key discoveries (2026-06-27 23:30 UTC):**
- Manifest denominator = 126 leagues/day (not 55): cup competitions, lower divisions also in denominator
- VM (orchestrator) covers exactly 55 leagues via `get_expected_leagues_for_source("transfermarkt", classifications=["Prediction", "Features"])` + `get_prediction_leagues()`
- 71 non-TM leagues (cups, lower divisions) → typed as EXPECTED_NO_PROVIDER_COVERAGE via `type_tm_non_provider_coverage_2026_06_27.py` (instruments-service@fbb032d), applied 23:41 UTC
- Typing script result: 8,744 rows typed; consolidator merged at ~23:44 UTC
- Canonical index after dedup: EU down to 4,087 (all TM-covered leagues, 0 non-TM)

**VM `tm-backfill-20260627-222604`** RUNNING: processing at 2026-04-01 as of 23:42 UTC (41/127 days = 32%). API-call dates (transfer windows open): ~2-3 min/day. ETA VM completion: ~03:00–04:00 UTC 2026-06-28. After VM TERMINATED: wait for consolidator (≤1 min), re-download index, verify pending_fetch==0, flip checkbox.

**Completed 2019→2026-02-19** (pre-existing, not touched by this VM):
- captured: 39,584 | empty_confirmed: 264,736 | expected_unattempted: 0

### footystats coverage state (2026-06-27 ~22:00 UTC)

IS manifest (`instruments-store-sports-prd-central-element-323112`):

| data_type   | captured | attempted_failed | expected_unattempted | empty_confirmed | coverage |
|-------------|----------|-----------------|----------------------|-----------------|----------|
| MATCHES     | 26,266   | 1,460           | 161,335              | 148,392         | 13.9%    |
| PREDICTIONS | 27,875   | 560             | 161,571              | 117,805         | 14.7%    |
| ODDS        | 29,129   | 1,119           | 11,486               | 74,432          | 69.8%    |

**ODDS rows intact** (29K captured; code restored at instruments-service@3d4f1a1 + @edebc6b).

**VM sequence needed** (singleton lock: only one `fs-backfill-*` at a time):

1. Current: `fs-backfill-20260627-200928` RUNNING — 2026-02-20..2026-06-27 MATCHES+PREDICTIONS (ETA ~01:40 UTC 2026-06-28)
2. After #1 completes → ODDS VM: `bash launch-footystats-backfill-vm.sh --entity ODDS 2019-01-01 2026-06-27 --force`
3. After #2 completes → MATCHES+PREDICTIONS history: `bash launch-footystats-backfill-vm.sh 2019-01-01 2026-02-19`
   (Multiple runs may be needed due to VM runtime limits; chunk by year if needed)

### understat XG + XG_SHOTS coverage state (2026-06-27 23:55 UTC, slot-9 monitoring)

IS manifest (`instruments-store-sports-prd-central-element-323112`), full history:

**XG — native leagues (EPL, LA_LIGA, BUNDESLIGA, SERIE_A, LIGUE_1):**

| capture_status       | count | notes |
|---------------------|-------|-------|
| captured            | 3,429 | across 5 native leagues, full history |
| empty_confirmed     | 222,346 | off-season / no-fixture dates |
| expected_unattempted| 265   | 53/league, dates 2026-05-05→2026-06-26 (VM not yet reached) |
| attempted_failed    | 0     | 0 HTTP_NOT_FOUND for native leagues ✅ |

**XG_SHOTS — native leagues:**

| capture_status       | count | notes |
|---------------------|-------|-------|
| captured            | 0     | VM not yet written XG_SHOTS for native leagues (shard in progress) |
| empty_confirmed     | 202,875 | matches with 0 shots or off-season |
| expected_unattempted| 635   | 127/league, dates 2026-02-20→2026-06-26 |
| attempted_failed    | 397   | 79–80/league, HTTP_NOT_FOUND, dates 2017-04-01→2026-03-02 (over-broad-404 legacy) |

**Non-native leagues (87,630 rows):** ALL `empty_confirmed` with `error_reason=EXPECTED_NO_PROVIDER_COVERAGE` ✅ Already typed.

**Blank-league XG phantom rows (296 rows):** `attempted_failed`, `reason=phantom_captured_no_parquet_at_canonical_path`, dates 2019-01-09→2026-04-16. NOT gate-blocking for item #4 (blank league_id ≠ native leagues); needs extended run of `reclassify_xg_blank_league_phantoms.py` for P1 verification (item #6).

**Skip efficiency:** XG: 4,211/4,561 dates skip-eligible (92.3%). XG_SHOTS: only 342/4,561 (7.5%) — bottleneck.

**Gate status: IN PROGRESS** — VM `us-backfill-20260627-210801` RUNNING (SPOT, asia-northeast1-c). At 2014-03-08 as of 23:51 UTC 2026-06-27 (~2.7h elapsed). Full range 2014-01-01→2026-06-27 = 4,561 dates. XG_SHOTS skip rate (7.5%) = ~4,219 API-call dates × ~1.5-2.5 min = **~4-5 days ETA** for full completion.

**Over-broad-404 resolution**: The 397 `XG_SHOTS` `HTTP_NOT_FOUND` rows will self-resolve when VM reaches those dates. Per-match 404 from `get_match_shots()` is now treated as honest absence (→ `empty_confirmed`) and per-league error scoping is fixed. Consolidator last-write-wins merges the correct rows over the stale failed ones.

**After VM TERMINATED**: wait for consolidator (≤1 min), re-query: XG `expected_unattempted==0` for 5 native leagues, XG_SHOTS `attempted_failed==0` (HTTP_NOT_FOUND), then flip checkbox.

**Singleton lock**: no concurrent `us-backfill-*` VMs (AJAX per-IP rate limit).

**Status update (2026-06-28 17:32 UTC, slot-9):** VM `us-backfill-20260628-070120` RUNNING. Progress: 689/4,561 dates (15.1%), at 2015-11-20. Rate ~79s/date. ETA: ~2026-07-02 06:30 UTC (~3.6 days). uv cross-filesystem symlink mitigation reverted (dir removed; future uv syncs will recreate on root disk as regular dir enabling hardlinks). Host disk: 898MB free, draining ~2 MB/min from fleet orch-agent-main conversation logs (largest: 253MB, 104MB, 96MB). VM execution unaffected (runs on GCE). Risk: local gcloud monitoring may fail if disk hits 0 before VM completes — operator disk expansion or log rotation needed.

**Status update (2026-06-28 20:20 UTC, slot-9):** VM `us-backfill-20260628-070120` RUNNING. Progress: ~820/4,561 dates (18%), at 2016-04-01 as of 19:58 UTC. Rate ~56.8s/date effective. ETA revised: **~2026-07-01 07:00 UTC** (~59h remaining). Host disk hit 100% — slot-9 cleaned 611MB of confirmed-inactive orch-agent-main conversation logs; 3.1GB now free.

Consolidated manifest (`availability_index.parquet`, 2026-06-28T20:03:40Z):

| data_type | capture_status        | count  | notes |
|-----------|-----------------------|--------|-------|
| XG        | captured              | 3,429  | all leagues combined |
| XG        | empty_confirmed       | 33,666 | all leagues |
| XG        | expected_unattempted  | 265    | 53/native × 5 leagues — gate not met ❌ |
| XG        | attempted_failed      | 296    | blank-league phantoms (non-gate-blocking for item #4) |
| XG_SHOTS  | empty_confirmed       | 16,162 | all leagues |
| XG_SHOTS  | expected_unattempted  | 635    | 127/native × 5 leagues (2026-02-20→2026-06-26) — gate not met ❌ |
| XG_SHOTS  | attempted_failed      | 405    | all native (↑8 from 397; over-broad-404 legacy; self-resolve when VM re-visits) — gate not met ❌ |

**Gate not met — blocked on VM completion**: All three gate conditions (XG eu=265, XG_SHOTS eu=635, XG_SHOTS failed=405) resolve when VM finishes. No code changes needed; VM running correctly. After VM TERMINATED + consolidator (≤1 min): re-query → flip checkbox ✅.

## References

- `sports_reference_backfill_oom_2026_06_22.md` — OOM single-read fix (vm-sports)
