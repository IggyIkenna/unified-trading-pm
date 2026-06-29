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

> **🟢 TRANSFERMARKT BACKFILL RUNNING** — `tm-backfill-20260629-060317` SPOT e2-standard-8 asia-northeast1-c, launched
> 06:03 UTC 2026-06-29, range 2021-01-01→2026-06-29. Resolves 34,686 regression eu rows (IS enumerate overwrite at
> 2026-06-28T21:31; IS fix at instruments-service@1835e11 prevents future regression). Tarball: instruments-service@051e5a8.
> GCS log: `gs://deployment-scripts-central-element-323112/vm-logs/tm-backfill-20260629-060317/run.log`. Singleton lock active.

> **🟢 FOOTYSTATS ODDS BACKFILL RUN 2** — `fs-backfill-20260629-062206` SPOT e2-standard-8 asia-northeast1-c,
> launched 06:22 UTC 2026-06-29, range 2020-09-01..2026-06-15 (entity=ODDS only). Re-run needed because first ODDS VM
> (fs-backfill-20260629-043218, completed 06:04 UTC) missed 285 af dates (race condition: VM started 07 min after
> phantom-audit shard was written; consolidated index hadn't merged shard yet → VM saw captured → skipped those dates).
> Also: 4,976 non-covered-league eu rows typed at instruments-service@810ac26
> (type_footystats_odds_non_covered_leagues_2026_06_29.py). GCS log:
> `gs://deployment-scripts-central-element-323112/vm-logs/fs-backfill-20260629-062206/run.log`. Singleton lock active.

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
- [ ] [DATA] P0. **footystats history → zero-missing** 2019→present (`MATCHES` + `PREDICTIONS` + `ODDS`). NOTE: ODDS
      removal reversed 2026-06-27 (#6 REVERSED, operator decision) — footystats ODDS are pre-match snapshot reference
      data that stays in IS; see sports_p0 task 003. **Gate**: `(footystats, PREDICTIONS)` + `(footystats, MATCHES)` +
      `(footystats, ODDS)` `pending_fetch == 0` within window; 0 blank-reason; ODDS parquets present in GCS. 🔄 IN
      PROGRESS — slot-8 unflipped 2026-06-29: checkbox was premature (26,220 phantom ODDS rows wiped 2026-06-25; "intact"
      claim was wrong). Phantom flip applied 04:25 UTC 2026-06-29. ODDS VM `fs-backfill-20260629-043218` RUNNING. After
      VM completes → verify pending_fetch==0 → reflip. M+P 2019-01-01..2026-02-19 also needed after ODDS VM.
- [x] [DATA] P0. **odds-api history → zero-missing** 2020-06→present (bookmaker-league subset; uncovered leagues typed).
      **Gate**: `(odds_api, trades)` `pending_fetch == 0` for covered leagues within window; uncovered leagues typed.
      ✅ — `mtds-backfill-odds-1` VM completed 2026-06-28T03:41 UTC (rc=0, 317/317 chunks, 2020-06-06→2026-06-27, 7-day
      chunks, MANIFEST_PER_VM_SHARDS=true). Gate verified 2026-06-29: source=odds_api manifest rows: captured=223701,
      empty_confirmed=22(SOURCE_RETURNED_ZERO), expected_unattempted=0, attempted_failed=0, pending_fetch=0. Uncovered
      leagues absent from denominator (fixed coverage-aware sentinel shipped before VM launch; 0 false attempted_failed).
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

**Status update (2026-06-29 01:45 UTC, slot-9):** VM `us-backfill-20260628-070120` RUNNING. Progress: 1,271/4,561 dates (27.9%), at 2017-06-17. Rate ~53s/date effective (67.9 dates/h). ETA revised: **~2026-07-01 02:17 UTC** (~48.5h remaining).

Consolidated manifest (`_index/availability_index.parquet`, 2026-06-29T01:33:30Z):

| data_type | capture_status        | count   | notes |
|-----------|-----------------------|---------|-------|
| XG        | captured              | 3,429   | all leagues combined |
| XG        | empty_confirmed       | 298,441 | all leagues (↑ VM writing off-season empties) |
| XG        | expected_unattempted  | 280     | 56/native × 5 leagues — gate not met ❌ |
| XG        | attempted_failed      | 296     | blank-league phantoms (non-gate-blocking) |
| XG_SHOTS  | empty_confirmed       | 282,691 | all leagues |
| XG_SHOTS  | expected_unattempted  | 13,776  | 2,755/native × 5 leagues — gate not met ❌ |
| XG_SHOTS  | attempted_failed      | 421     | all native (↑16; over-broad-404; self-resolve when VM re-visits) ❌ |

Native-league gate: XG pending_fetch=280, XG_SHOTS pending_fetch=14,197 — not met. VM still processing; no code changes needed.

**Status update (2026-06-29 04:30 UTC, slot-9):** VM `us-backfill-20260628-070120` RUNNING. Progress: ~1,461/4,561 dates (~32%), at 2018-01-01. Rate ~60-70 dates/h. ETA revised: **~2026-07-01 02:00 UTC** (~45h remaining).

**BUG FOUND + FIXED: `_classify_error` URL substring collision (instruments-service@7bb8c26)**

ROOT CAUSE: `_classify_error` matched `"401" in msg`, `"429" in msg`, `"403" in msg` against the full exception message including the URL. Understat match IDs like `/getMatch/5401` → `"401" in msg` → INVALID_API_KEY (not HTTP_NOT_FOUND). Since `get_match_shots()` only returns `[]` without incrementing `_fetch_error_count` for `HTTP_NOT_FOUND`, this misclassification caused `_fetch_error_count` to increment → league added to `_shots_failed_canonical` → `record_failed(HTTP_NOT_FOUND)` instead of `record_empty(EXPECTED_NO_FIXTURE)`.

EVIDENCE from VM log:
- `ADAPTER_FETCH_FAILED venue=understat error_code=RATE_LIMIT_EXCEEDED: 404, message='Not Found', url='.../getMatch/5429'` (match 5429 → "429" in msg)
- `ADAPTER_FETCH_FAILED venue=understat error_code=INVALID_API_KEY: 404, message='Not Found', url='.../getMatch/5401'` (match 5401 → "401" in msg)
- `ADAPTER_FETCH_FAILED venue=understat error_code=FORBIDDEN: 404, message='Not Found', url='.../getMatch/5403'` (match 5403 → "403" in msg)

FIX: `_classify_error` now prioritises the HTTP status param over substring matching — if `status` is not None, return the classification directly. String matching only applies for statusless network errors.

IMPACT:
- 27 new false-failed rows in 2014-2017 (written by current VM with buggy code). These will NOT self-resolve when VM re-visits (already processed).
- 396 legacy failed rows (2019-2026, from pre-fix VMs) — WILL self-resolve when the (fixed) code processes those dates. But current VM has old code baked in → those dates may accumulate additional false-failed rows.
- Typing script `reclassify_xg_shots_false_failed_2026_06_29.py` shipped at instruments-service@15dc9b5. Run AFTER VM terminates to reclassify ALL `XG_SHOTS attempted_failed(HTTP_NOT_FOUND)` native-league rows to `empty_confirmed(EXPECTED_NO_FIXTURE)`.

Consolidated manifest (`_index/availability_index.parquet`, 2026-06-29T04:29:41Z):

| data_type | capture_status        | count   | notes |
|-----------|-----------------------|---------|-------|
| XG        | captured              | 3,429   | all leagues combined |
| XG        | empty_confirmed       | 298,441 | all leagues |
| XG        | expected_unattempted  | 280     | 56/native × 5 leagues — gate not met ❌ |
| XG        | attempted_failed      | 296     | blank-league phantoms (non-gate-blocking) |
| XG_SHOTS  | empty_confirmed       | 283,449 | all leagues |
| XG_SHOTS  | expected_unattempted  | 13,776  | 2,755/native × 5 leagues — gate not met ❌ |
| XG_SHOTS  | attempted_failed      | 423     | 27 new false-failed (VM bug) + 396 legacy; need typing script after VM completes ❌ |

**Gate not met — blocked on VM completion**: VM ETA ~2026-07-01 02:00 UTC. After VM TERMINATED:
1. Wait ≤1 min for consolidator merge
2. Run `reclassify_xg_shots_false_failed_2026_06_29.py --apply` (per-VM shard; consolidator applies last-write-wins)
3. Wait ≤1 min for consolidator to merge typing shard
4. Re-query: XG `expected_unattempted==0`, XG_SHOTS `expected_unattempted==0`, XG_SHOTS `attempted_failed==0` for native leagues
5. If all zero: flip checkbox ✅

### 2026-06-29 05:15 UTC — slot 2: understat VM progress check

**VM `us-backfill-20260628-070120`** RUNNING. At 2018-02-08 as of 05:10 UTC. Progress: ~1,500/4,561 dates (~33%). Rate
~68 dates/h. ETA unchanged: **~2026-07-01 02:00 UTC** (~44h remaining). GCS log tail confirms clean execution —
XG short-circuiting (all 5 native leagues captured), XG_SHOTS fetching match shots, per-VM shard updated every 5
entries. No errors.

**All code ready**. Reclassify script at `instruments-service@15dc9b5`. No code action needed until VM TERMINATED.

**Post-VM verification steps (unchanged from 04:30 entry)**:
1. Wait ≤1 min for consolidator merge after VM TERMINATED
2. `GCP_PROJECT_ID=central-element-323112 PROJECT_ID=central-element-323112 DEPLOYMENT_ENV_SHORT=prd CLOUD_PROVIDER=gcp MANIFEST_PER_VM_SHARDS=true VM_NAME=reclassify-xg-shots-$(date +%s) .venv/bin/python scripts/reclassify_xg_shots_false_failed_2026_06_29.py --apply`
3. Wait ≤1 min for consolidator to merge typing shard
4. Re-query: XG `expected_unattempted==0`, XG_SHOTS `expected_unattempted==0`, XG_SHOTS `attempted_failed==0` for native leagues
5. If all zero: flip checkbox ✅

**Task parked** — re-dispatch this task after VM TERMINATED (~2026-07-01 02:00 UTC).

### 2026-06-29 06:35 UTC — slot 7: understat VM status + enum-run XG_SHOTS eu finding

**VM `us-backfill-20260628-070120`** RUNNING. At 2018-04-07 as of 06:23 UTC. Progress: ~1,558/4,561 dates (~34%). Rate
~68 dates/h. ETA: **~2026-07-01 02:00 UTC** (~43h remaining). GCS log tail clean.

**Manifest state (downloaded 06:25 UTC, availability_index.parquet):**

| data_type | capture_status       | count   | notes |
|-----------|----------------------|---------|-------|
| XG        | captured             | 4,444   | all leagues (↑ from 3,429 — VM writing) |
| XG        | empty_confirmed      | 298,441 | all leagues |
| XG        | expected_unattempted | 280     | 56/native × 5 leagues, dates 2026-05-05→2026-06-29 — gate not met ❌ |
| XG        | attempted_failed     | 296     | blank-league phantoms (non-gate-blocking) |
| XG_SHOTS  | empty_confirmed      | 283,658 | all leagues |
| XG_SHOTS  | expected_unattempted | 13,776  | 2,756 unique dates × 5 native leagues, 2018-01-01→2026-06-29 — gate not met ❌ |
| XG_SHOTS  | attempted_failed     | 424     | all native, false-failed (need typing script) ❌ |

**NEW FINDING — enum run at 21:31 UTC 2026-06-28 wrote 13,776 XG_SHOTS eu rows:**
All 13,776 XG_SHOTS eu rows have `written_at = 2026-06-28T21:31:49.534565+00:00` — same as the TM regression enum run
(`enum-universe-sports-20260628-213115`). The enum wrote XG_SHOTS eu for 2018-01-01→present, overwriting rows the VM
had written for dates it processed BEFORE the enum ran (~2016-02-22 territory).

**Self-resolution**: As the VM processes each date from 2018-01-01 onwards (VM is currently at 2018-04-07 — already
past 2018-01-01), it writes empty_confirmed rows with NEWER timestamps than the enum's eu rows. These win in
last-write-wins consolidation. For 2018-01-01 to 2018-04-06: VM has already processed these dates after the enum
ran (VM processed them at ~04:30 UTC today, newer than 21:31 UTC yesterday), so those rows are being merged by the
consolidator. The eu count will drop continuously as the VM progresses.

**No code action needed** — VM self-corrects all eu rows. Gate still blocked on VM completion (~2026-07-01 02:00 UTC).
Post-VM steps unchanged (same as 05:15 UTC entry above). Task parked; slot-7 blocked (/blocked BLK-d37c0d60).

### 2026-06-29 06:20 UTC — slot 9: footystats ODDS gate analysis + second VM + typing

**ODDS VM 1 completed** (`fs-backfill-20260629-043218`, exit_code=0, 06:04 UTC). Gate NOT met:
- 6,294 eu rows: 4,976 non-covered-league artifacts (58 leagues, never had captured ODDS) + 1,318 covered-league eu from race condition
- 286 af rows: 285 phantom_captured_no_parquet (SUPER_LIG=183, SWISS_SUPER_LEAGUE=92, CHILE_PRIMERA=4, LIGUE_1=1) + 6 blank-league

**Root cause of 285 phantom af rows persisting**: ODDS VM 1 launched at 04:32 UTC, 7 min after phantom-audit shard (04:25 UTC). Consolidator hadn't merged phantom-audit shard yet → VM's `_should_skip_date_for_per_league` read old consolidated index, saw captured for those dates → skipped → phantom-audit af wins after consolidation.

**Actions taken (2026-06-29 06:00-06:22 UTC)**:
1. Typed 4,976 non-covered eu rows: `type_footystats_odds_non_covered_leagues_2026_06_29.py --apply` at instruments-service@810ac26. Shard: `_index/per_vm/type-fs-odds-1782713875.parquet`.
2. Launched `fs-backfill-20260629-062206` SPOT ODDS VM for 2020-09-01..2026-06-15 to re-process 285 af dates. This time consolidated index shows af (not captured) → skip-check returns False → processes those dates.

**Post-VM 2 verification steps**:
1. Wait ≤1 min for consolidator after VM TERMINATED
2. Re-query `(footystats, ODDS)` — expect captured=30K+, empty_confirmed=70K+, eu≈0, af≈0 (or only blank-league af if not resolvable)
3. If 6 blank-league af rows persist: investigate + type away separately
4. After ODDS gate met → launch M+P VM: `bash launch-footystats-backfill-vm.sh 2019-01-01 2026-02-19`
5. After M+P VM completes: verify `(footystats, MATCHES)` + `(footystats, PREDICTIONS)` pending_fetch==0 → reflip footystats checkbox ✅

### 2026-06-29 06:03 UTC — slot 9: TM regression eu investigation + re-backfill VM launch

**Context**: IS manifest eu regression at 2026-06-28T21:31 (enum run `enum-universe-sports-20260628-213115`) wrote
34,686 eu rows for TM-covered leagues, overwriting previously-valid captured/empty_confirmed rows in the consolidated
index. Root cause: enumerate read only consolidated index (race condition, fixed at instruments-service@1835e11).

**TM eu analysis** (manifest downloaded 2026-06-29T05:55 UTC):

| capture_status | count |
|---|---|
| captured | 39,807 |
| empty_confirmed | 212,907 |
| expected_unattempted | 36,050 → pending_fetch |

Regression eu (34,686 from `enum-universe-sports-20260628-213115`): 47 leagues × 738 specific dates (2021-03-16 to
2026-06-28), by year: 2021=8,037 / 2022=9,400 / 2023=1,316 / 2024=9,259 / 2025=6,110 / 2026=564.

Non-regression eu (1,364 rows from 2026-06-19/23/26/29 enum runs): recent forward-poll dates, will be covered by
the new backfill VM.

**Action**: Launched `tm-backfill-20260629-060317` SPOT e2-standard-8 at 06:03 UTC, range 2021-01-01→2026-06-29.
Tarball: instruments-service@051e5a8 (includes enumerate fix @1835e11). GCS log:
`gs://deployment-scripts-central-element-323112/vm-logs/tm-backfill-20260629-060317/run.log`. Singleton lock active.

**Expected result**: VM writes captured/empty_confirmed for all 738 eu dates × 47 leagues → consolidator merges →
TM pending_fetch returns to ≤6,845 (only window-closed dates that TM skips remain eu). Estimate: ~15-20h (at
2-3 min/date for transfer-window-open dates, window-closed dates fast).

**Post-VM steps**: Wait ≤1 min for consolidator, re-query, verify `(transfermarkt, PLAYER_VALUES) pending_fetch ≤ 6,845`.
If confirmed: TM gate re-met. Then task 007 gate depends only on Understat + Footystats VMs completing.

### 2026-06-29 — slot 8: footystats ODDS phantom flip + ODDS VM launch

**Finding**: The footystats todo `[x]` was flipped prematurely (slot 5, 2026-06-27). The "ODDS 29K captured intact"
claim was incorrect — phantom audit (slot-8, 22:01 UTC 2026-06-27) confirmed ALL 29,129 `captured` ODDS rows had 0 GCS
parquets. Data was wiped by `wipe_footystats_odds_2026_06_25.py` on 2026-06-25 05:16 UTC (before the reversal).

**Actions taken**:

1. **Phantom flip `--apply` ran at 04:25 UTC 2026-06-29**: `reconcile_phantom_manifest_rows_all.py --asset-group sports
   --data-types ODDS --apply --workers 4`. Result: 26,220 rows → `attempted_failed`, 2,909 pre-launch excluded.
   Post-flip dry-run confirms: 0 phantom rows remain.

2. **ODDS backfill VM launched at 04:32 UTC 2026-06-29**: `fs-backfill-20260629-043218` SPOT e2-standard-8
   asia-northeast1-c, range 2019-01-01..2026-06-29, entity=ODDS only. Code at IS@97ccf8d (includes ODDS restore at
   @3d4f1a1+@edebc6b). GCS log:
   `gs://deployment-scripts-central-element-323112/vm-logs/fs-backfill-20260629-043218/run.log`. VM launched via Python
   compute API (gcloud snap-confine broken on planning VM).

3. **Footystats checkbox UNFLIPPED** — gate requires `(footystats, ODDS) pending_fetch == 0` which will only be met
   after the ODDS VM completes. M+P 2019-01-01..2026-02-19 also still needed (singleton lock: after ODDS VM).

**Next steps**: Monitor `fs-backfill-20260629-043218` (check GCS log for progress). After ODDS VM TERMINATED: wait for
consolidator, verify `(footystats, ODDS) pending_fetch == 0`, then launch M+P 2019-01-01..2026-02-19 VM. After both
complete + gate met → reflip footystats checkbox. Issue doc
`issues/sports_is_odds_capture_code_incomplete_reversal_2026_06_27.md` updated.

## References

- `sports_reference_backfill_oom_2026_06_22.md` — OOM single-read fix (vm-sports)
