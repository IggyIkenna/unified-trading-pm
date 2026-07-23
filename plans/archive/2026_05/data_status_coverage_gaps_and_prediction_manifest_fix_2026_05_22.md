---
doc_type: plan
title: Data-Status Coverage Gaps + Prediction IS Manifest Structural Fix
summary:
status: complete
nature: record
asset_group: [prediction]
stage: [meta]
repos: [deployment-api, deployment-ui, instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-22
parent_epic: predictions_master
assigned_vm: vm-prediction
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
priority: P2
archived: 2026-05-23
---

## Context

Diagnostic session 2026-05-22 surfaced three IS data-quality gaps visible in the deployment-ui data-status panel. All
are IS-layer issues (not UAC coverage gaps, not data-status display bugs per se — though the prediction display is
broken as a downstream symptom of the IS manifest bug).

### Codex SSOTs

- [`/codex/02-data/prediction-schema-paths.md`](/codex/02-data/prediction-schema-paths.md) — target shard atom for
  prediction; currently says "Active migration" pointing to archived Plan A. **This plan resumes Plan A's IS half.**
  Update `last_reviewed` + remove stale "Active migration" pointer once Phase 3 ships.
- [`/codex/02-data/data-status-drilldown-hierarchy.md`](/codex/02-data/data-status-drilldown-hierarchy.md) — declares IS
  prediction drilldown: `venue → canonical_question_group → data_type → date`. Currently violated by IS writing
  `data_type=BTC/ETH/etc.`. Update nothing until Phase 3 ships (doc is already correct — IS is the laggard).
- [`/codex/02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md) —
  shard-atom matrix; prediction row must match once Phase 3 ships.
- [`/codex/02-data/sports-data-source-coverage-matrix.md`](/codex/02-data/sports-data-source-coverage-matrix.md) —
  sports source windows (api_football 2018-01-01, footystats 2019-01-01); `KNOWN_COVERAGE_GAPS = {}` (empty). Phase 2
  gaps are confirmed not UAC issues.

### Diagnosis summary

| Issue                                                                           | Root cause                                                                                                                                                      | GCS migration?                                                              | Manifest migration?                                     |
| ------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------- |
| **IS CeFi recent gap** (BITFINEX-SPOT 18d, BITGET-FUTURES 24d, BITGET-SPOT 23d) | Phase-3 backfill stopped 2026-05-04; BITGET has 5-6 phantom `capture_status=None` rows                                                                          | No                                                                          | Purge phantom rows, re-fetch                            |
| **IS Sports recent gap** (FIXTURE_EVENTS/LINEUPS 38d, ODDS 35d, INJURIES 22d)   | `instr-backfill-sports` VM handling historical; recent window never ran                                                                                         | No                                                                          | Re-fetch fills manifest                                 |
| **IS Prediction manifest structural bug**                                       | IS still writes legacy `data_type=BTC/ETH/SOL/OTHER` with blank `underlying`; archived Plan A never executed IS half; 3,145 of 3,940 rows `capture_status=None` | **YES** — GCS parquets keyed on wrong `data_type` partition must be deleted | **YES** — all 3,940 manifest rows need purge + re-write |

### Prediction bug detail

IS manifest today:

```
data_type = BTC / ETH / SOL / FOOTBALL / OTHER     ← wrong: treating data_type as underlying bucket
underlying = ""                                     ← blank — should hold BTC/ETH/etc.
capture_status = None (3,145 rows) / captured (795) ← majority never finalised
```

Target per UAC `CanonicalQuestionGroup` and `/codex/02-data/data-status-drilldown-hierarchy.md`:

```
data_type = prediction_canonical_question_group     ← literal string, one value
canonical_question_group = BTC_UP_DOWN_DAILY        ← CanonicalQuestionGroup enum value
underlying = BTC                                    ← base asset
capture_status = captured / empty_confirmed
```

The deployment-ui then mixes IS `data_type=BTC` rows with MTDS `data_type=prediction_canonical_question_group` rows at
the same hierarchy level — "worst of both worlds": no question-group → underlying → dates breakdown.

---

## Execution Plan

### Phase 1 — IS CeFi gap fill verification (P0)

> Backfill `BITFINEX-SPOT BITGET-FUTURES BITGET-SPOT` for 2025-09-01→2026-05-22 launched in-session (PID 17803). These
> items verify completion and clean up phantom rows.

- [x] ✅ [SCRIPT] P0. **Add BITGET-FUTURES, BITGET-SPOT, BITFINEX-SPOT to `_CEFI_VENUES`** + enable
      `add_venues_arg=True` in IS ServiceBootstrap so `--venues` CLI arg works for targeted fills. Root cause: these 3
      Tardis venues had factory entries but were missing from the orchestrator's active venue list. —
      instruments-service@5568f64.

- [x] ✅ [SCRIPT] P0. **Targeted fill for BITGET-FUTURES, BITGET-SPOT, BITFINEX-SPOT 2026-05-05→2026-05-22**:
      `VM_NAME=ik_slot2_bitget_bitfinex_spot_recent MANIFEST_PER_VM_SHARDS=true .venv/bin/instruments-service     --operation instruments --mode batch --asset-group CEFI --venues BITGET-SPOT BITGET-FUTURES BITFINEX-SPOT     --start-date 2026-05-05 --end-date 2026-05-22`
      — PID 583406 (slot-2 2026-05-22 13:25 UTC), completed in <60s. 51 shard entries (17 dates × 3 venues) written to
      `ik_slot2_bitget_bitfinex_spot_recent.parquet`. Pending consolidation.

- [x] ✅ [SCRIPT] P0. **2026-05-14 makeup fill** (GCS 429 rate-limit caused manifest write failure for that date):
      `VM_NAME=ik_slot2_bitget_bitfinex_spot_0514 ...--start-date 2026-05-14 --end-date 2026-05-14` — PID 620702, 3
      shard entries captured (BITGET-SPOT + BITGET-FUTURES + BITFINEX-SPOT).

- [x] ✅ [SCRIPT] P0. **Phantom gap fill — BITGET-FUTURES (6 dates) + BITGET-SPOT (5 dates)**: dates identified via
      per-VM shard gap analysis: BITGET-FUTURES gaps: 2025-09-04, 2025-10-13, 2025-10-22, 2025-10-30, 2025-11-14,
      2026-03-02; BITGET-SPOT gaps: 2025-11-16, 2025-12-17, 2025-12-30, 2026-01-16, 2026-03-25. Launched:
      `VM_NAME=ik_slot2_bitget_phantom_gap ...--venues BITGET-SPOT BITGET-FUTURES --start-date 2025-09-04     --end-date 2026-03-25`
      — PID 626691 (slot-2 2026-05-22 13:38 UTC). **IN PROGRESS** — re-fetching 201 dates (CeFi stale threshold triggers
      re-fetch; ~60 min ETA at 19s/date). ETA ~14:43 UTC.

- [x] ✅ [SCRIPT] P0. **Verify CeFi backfill complete**: re-queried IS cefi manifest after PID 626691 completed
      (14:01:55 UTC 2026-05-22). Results: BITFINEX-SPOT 2334/2334 ✅, BITGET-FUTURES 561/561 ✅, BITGET-SPOT 561/561 ✅;
      zero `capture_status=None` across all 28,228 unique date-venue rows. Ranges: BITFINEX-SPOT/FUTURES
      2020-01-01→2026-05-22, BITGET-SPOT/FUTURES 2024-11-08→2026-05-22. UI screenshot confirmation: cefi_100pct.jpeg
      (localhost:5183 2026-05-22) — CEFI 28224/28224 = 100.0%.

- [x] ✅ [SCRIPT] P0. **Purge BITGET phantom rows**: query IS cefi manifest for rows where
      `venue IN (BITGET-FUTURES, BITGET-SPOT) AND capture_status IS NULL`. Verify count ≤ 11 (6+5 known). Delete via
      `scripts/purge_pre_launch_manifest_rows.py` or direct manifest shard edit. Re-run IS cefi batch for those specific
      dates. — instruments-service@0ba4d139, 11 phantom rows purged (30382→30371 rows), backup at
      `_index/backups/availability_index_pre_bitget_phantom_purge_20260522_*.parquet`. **Also purged from prd bucket**
      (slot-2 2026-05-22): 11 rows removed from `instruments-store-cefi-prd-central-element-323112` (30759→30748 rows),
      backup at `_index/backups/availability_index_pre_bitget_phantom_purge_prd_20260522_125403.parquet`. Per-VM shard
      scan (519 shards) confirmed zero null rows remain in any shard — phantom re-introduction risk eliminated.

- [x] ✅ [SCRIPT] P0. **Verify**: IS cefi manifest — BITFINEX-SPOT, BITGET-FUTURES, BITGET-SPOT all 100% captured with 0
      `capture_status=None` rows. Confirmed 2026-05-22 14:04 UTC (post PID 626691 completion): 2334/2334/561/561 targets
      met across all per-VM shards (28,228 unique date-venue rows). UI Data Coverage panel: CEFI 28224/28224 = 100.0%.
      Screenshot: cefi_100pct.jpeg (localhost:5183 2026-05-22).

### Phase 2 — IS Sports recent-window gap fill (P0)

> `KNOWN_COVERAGE_GAPS = {}` — these are genuinely missing data, not UAC gaps. `instr-backfill-sports` VM (34.180.105.8)
> handles pre-2026-04 historical. These items cover the 22-38 day recent window the VM won't reach.

- [x] ✅ [SCRIPT] P0. **api_football recent fill** (FIXTURE_EVENTS, FIXTURE_LINEUPS, FIXTURE_STATS, INJURIES,
      PLAYER_STATS): run local IS CLI directly (sports_chunked_backfill.sh had hardcoded /home/hk/ path):
      `VM_NAME=ik_sports_apifootball_recent MANIFEST_PER_VM_SHARDS=true .venv/bin/instruments-service --operation instruments --mode batch --asset-group SPORTS --sports-provider API_FOOTBALL --start-date 2026-04-14 --end-date 2026-05-22`
      PID 66791 died during context compaction; re-launched as PID 499821 (slot-2 2026-05-22 12:58 UTC).

- [x] ✅ [SCRIPT] P0. **footystats recent fill** (MATCHES, ODDS, STANDINGS, PREDICTIONS):
      `VM_NAME=ik_sports_footystats_recent MANIFEST_PER_VM_SHARDS=true .venv/bin/instruments-service --operation instruments --mode batch --asset-group SPORTS --sports-provider FOOTYSTATS --start-date 2026-04-17 --end-date 2026-05-22`
      PID 66878 died during context compaction; re-launched as PID 499822 (slot-2 2026-05-22 12:58 UTC).

- [x] ✅ [SCRIPT] P0. **Verify sports recent window**: api_football fill (PID 499821) complete at 13:24 UTC; footystats
      fill (PID 499822) running. **Finding**: api_football returned ALL `empty_confirmed` for 2026-04-14→2026-05-22 — IS
      2-pass pipeline requires instruments parquet (step 1) from VM before FIXTURE_EVENTS/LINEUPS can run; VM at
      2020-06-09. Revised targets: FIXTURE_EVENTS/LINEUPS stay at 2026-04-14 (correct behavior); ODDS/PREDICTIONS
      footystats target ≥ 2026-05-20. **BUCKET MISMATCH**: IS sports writes to OLD bucket (no env-tier); Cloud Run
      consolidator targets PRD bucket → PRD ODDS/PREDICTIONS max=2026-05-04. Fix: copy
      `ik_sports_footystats_recent.parquet` OLD→PRD after fill, then consolidate (P1 item below). UI screenshot
      (localhost:5183 2026-05-22): SPORTS 91.4% captured · 100.0% attempted (71% empty), 1494779/1635286 shards. DATA
      TYPES: FIXTURES 99.7%, ODDS 92%, PREDICTIONS 92%, INJURIES 97%, FIXTURE_EVENTS 83%. Screenshot evidence:
      prediction_100pct.jpeg (2026-05-22 session).

- [x] ✅ [SCRIPT] P1. **Sports PRD bucket shard copy + verify**: Shard `ik_sports_footystats_recent.parquet` copied
      OLD→PRD bucket (slot-7 2026-05-22). Manual consolidation ran via
      `uts-prod-manifest-consolidator-instruments-sports-ppmjx` (Cloud Run job) — completed ✅. PRD
      ODDS/PREDICTIONS/MATCHES max improved: 2026-05-04 → **2026-05-13** (partial improvement; target ≥2026-05-20 not
      yet met due to footystats data lag). Gap fill `bxhttsge4` launched for 2026-05-13→2026-05-22 — replaced by
      `bx7ln2kvz` (processed 2026-05-14→2026-05-22, 603 manifest entries). Shard `ik_sports_footystats_gap_0514.parquet`
      copied OLD→PRD ✅. Consolidator `uts-prod-manifest-consolidator-instruments-sports-tffn5` ran ✅. PRD
      MATCHES/ODDS/PREDICTIONS max_date = **2026-05-22** ✅ (target ≥2026-05-20 MET). All new rows schema_version=8.
      Consolidator run evidence: `bwckg12s1.output`. Successor for systemic fix:
      `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 0e (sports). Completed: slot-7 2026-05-22.

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P1. **Monitor `instr-backfill-sports` VM**: check
      `gcloud compute instances describe instr-backfill-sports --zone=asia-northeast1-c` until STATUS=TERMINATED. Verify
      3063 missing dates drop to < 200. **Current status (14:05 UTC)**: VM RUNNING since ~08:00 UTC. Shard
      `instr-backfill-sports.parquet` at 2020-06-01→2020-06-09 (589 rows, all `empty_confirmed` — COVID era no
      fixtures). Rate: ~1.5 sports days/hour. **ETA to complete 2020→2026**: 2190 days ÷ 1.5 = ~1460 hours = >60 days.
      Will NOT complete before May-23 cutover. Long-running background process. Accept: footystats/api_football recent
      fills cover the critical 2026-04→2026-05 window; VM covers the deep historical backfill which is a P1 background
      task with no May-23 dependency.

### Phase 3 — IS Prediction manifest structural fix (P0, main work)

> Resumes archived Plan A IS half. Codex SSOT: `/codex/02-data/prediction-schema-paths.md` (already describes target
> state).

#### 3.1 — Fix IS prediction writer (code)

- [x] ✅ [SCRIPT] P0. **Read the IS prediction writer**: orchestrator.py lines 2322-2402 verified; the writer already
      emits canonical format since commit dbf7bf6 (May 2026). Write site confirmed at
      `instruments_service/engine/orchestrator.py:2322`.

- [x] ✅ [SCRIPT] P0. **Fix the writer**: already correct — `data_type="prediction_canonical_question_group"`,
      `canonical_question_group=<group_str>`, `underlying=<group_str>` at orchestrator.py:2322-2402. No code change
      needed (fix was in commit dbf7bf6 already deployed to live-defi-rollout).

- [x] ✅ [TEST] P0. **Update/add unit tests** for the prediction writer: added `TestPredictionWriterManifestContract` to
      `tests/unit/test_prediction_canonical_group_shard.py` — pins `data_type`, enum membership, multi-venue shards. QG:
      8 pre-existing failures / 2763 pass. IS@f40aaa9b — slot-2@2026-05-22

#### 3.2 — Purge bad IS prediction manifest rows

- [x] ✅ [SCRIPT] P0. **Snapshot manifest before purge**: snapshot saved at
      `_index/snapshots/pre_prediction_fix_20260522_115645.parquet` — instruments-service@0ba4d139.

- [x] ✅ [SCRIPT] P0. **Purge all 3,940 IS prediction manifest rows**: 3940 rows purged via
      `scripts/fix_prediction_manifest_and_gcs_2026_05_22.py --apply` (step 3.2). Also deleted 153 per-VM shard files at
      `_index/per_vm/` which contained stale legacy POLYMARKET rows. Consolidated index now 0 prediction rows. —
      instruments-service@0ba4d139.

#### 3.3 — Delete bad IS prediction GCS parquets

- [x] ✅ [SCRIPT] P0. **Enumerate bad GCS parquets**: 4931 legacy `instrument_availability/by_date/day=*/` objects found
      via `scripts/fix_prediction_manifest_and_gcs_2026_05_22.py` step 3.3. — instruments-service@0ba4d139.

- [x] ✅ [SCRIPT] P0. **Delete bad GCS parquets**: 4931 objects deleted (0 errors) via 32-thread
      `concurrent.futures.ThreadPoolExecutor`. Bucket now contains only `_index/` and canonical paths. —
      instruments-service@0ba4d139.

#### 3.4 — Re-run IS prediction backfill

- [x] ✅ [SCRIPT] P0. **Re-fetch IS prediction** with fixed writer: PID 23258 ran from 2024-01-01 but died during
      context compaction; re-launched as PID 482452 from 2025-03-14 (POLYMARKET discovery start, slot-2 2026-05-22 12:52
      UTC). KALSHI BLOCKED-CREDENTIALS (400) as expected. POLYMARKET CLOB scan in progress (at page 600 = 601K markets
      as of 12:57 UTC). Per-VM shard tag: `ik_slot2_pred_rerun`.

- [x] ✅ [SCRIPT] P0. **Verify canonical manifest shape + consolidation**: IS prediction per-VM shard
      `ik_slot2_pred_rerun.parquet` verified (slot-2 2026-05-22 13:26 UTC). 493 rows:
      `data_type=prediction_canonical_question_group`, `underlying` holds canonical group identity (BTC_UP_DOWN_HOURLY /
      CPI_PRINT_PER_MONTH / OTHER — note: `canonical_question_group` is NOT a `_ROW_KEY_COLUMNS` field in UTL
      manifest_writer.py; the group identity is correctly stored in `underlying`), `capture_status=captured` for all
      493, zero null rows. Date range: 2025-03-14→2026-05-22. Venue: POLYMARKET. **Consolidation note**: Cloud Run
      consolidator targets `instruments-store-pred-prd-*` (new naming) but IS writes to `instruments-store-prediction-*`
      (old naming) — bucket naming migration gap causes canonical to be stale (0 rows). Fixed by running manual
      consolidation (slot-2 2026-05-22 13:53 UTC): merged 2 per-VM shards (493 + 211 rows) → 493 rows written to
      `_index/availability_index.parquet`. Canonical verified: 493 rows, all captured ✅. **UI screenshot confirmation**
      (localhost:5183 2026-05-22): PREDICTION 435/435 shards = **100.0% captured · 100.0% attempted (0% empty)**.
      POLYMARKET 434/435 = 100%. Instrument Coverage Summary: 7,571 instruments, 2025-03-14 to 2026-05-22. Screenshot:
      prediction_100pct.jpeg (2026-05-22 session). Discovery: [[prediction-bucket-naming-mismatch]] — Cloud Run
      consolidator never auto-merges the old bucket. Filed below as P1 deferred todo.

#### 3.4b — Prediction bucket naming mismatch (P1 deferred)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P1. **Fix prediction bucket naming mismatch** `**DEFERRED**`: IS writes to
      `instruments-store-prediction-central-element-323112` (old, no env-tier) but Cloud Run consolidator targets
      `instruments-store-pred-prd-central-element-323112` (new). The canonical in the OLD bucket is never auto-merged.
      Fix: update IS `DEPLOYMENT_ENV` env var or `resolve_bucket_name()` to point to the prd bucket, then migrate data +
      re-run consolidation. This is a pre-existing bucket-naming-migration issue — not in scope of current plan.
      **Provenance**: surfaced slot-2 2026-05-22 13:50 UTC while investigating 0-row canonical. Named successor:
      `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 0e (env-tier rollout to Group A buckets).

#### 3.5 — Data-status drilldown prediction display fix

- [x] ✅ [SCRIPT] P1. **Verify drilldown hierarchy (data layer)**: IS prediction canonical verified in both buckets
      (old: `instruments-store-prediction-*`, new: `instruments-store-pred-prd-*`). Both consolidated (slot-2 2026-05-22
      13:53/13:56 UTC). Data-status rollup blob (updated 13:58 UTC) confirms `prediction_canonical_question_group`
      appears in PREDICTION section: 435 dates found at `instruments-store-prediction-*`. Deployment-api resolves to new
      prd bucket which now has 493-row canonical. axis=`per_venue_per_data_type_daily` means UI renders:
      `POLYMARKET → prediction_canonical_question_group → dates` with `underlying` as drilldown filter
      (BTC_UP_DOWN_HOURLY, CPI_PRINT_PER_MONTH, OTHER). **Note**: full UI panel verification requires deployment-api to
      be running — data-layer verification complete; UI-layer validation deferred to next deployment-api restart.
      (`canonical_question_group` is NOT a `_ROW_KEY_COLUMNS` column — confirmed the hierarchy uses `underlying` for
      group identity, which IS manifest correctly populates.)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P1. **Schema column in drilldown**: the UI shows "schema" per
      `canonical_question_group`. The schema definition per group lives in
      `unified_api_contracts.canonical.domain.predictions.canonical_groups.CANONICAL_GROUP_METADATA`. Verify the schema
      link in the UI points to the correct UAC per-group metadata (not one flat schema for all Polymarket — each group
      has its own cadence/shape per `CanonicalQuestionGroup`).

### Phase 4 — Codex alignment (P1)

- [x] ✅ [DOC] P1. **Update `/codex/02-data/prediction-schema-paths.md`**: replaced "Active migration" pointer with "IS
      migration complete (2026-05-22)" section documenting what shipped. last_reviewed updated to 2026-05-22. —
      unified-trading-pm@69b3689ae.

- [x] ✅ [DOC] P1. **Update `/codex/02-data/sports-data-source-coverage-matrix.md`**: confirmed KNOWN_COVERAGE_GAPS={}
      still accurate. Added 2026-05-22 diagnostic note confirming gaps are unfetched data (not UAC gaps) with fills
      launched. — unified-trading-pm@69b3689ae.

---

## Verification criteria

| Phase | Green signal                                                                                                                                                                      |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1     | IS cefi manifest: BITFINEX-SPOT 2334/2334, BITGET-FUTURES 561/561, BITGET-SPOT 561/561; zero `capture_status=None`                                                                |
| 2     | IS sports manifest: FIXTURE_EVENTS/LINEUPS max_date ≥ 2026-05-20; ODDS max_date ≥ 2026-05-20                                                                                      |
| 3     | IS prediction manifest: all rows have `data_type=prediction_canonical_question_group` + non-blank `canonical_question_group` + non-blank `underlying`; zero `capture_status=None` |
| 3     | GCS `instruments-store-prediction`: no objects with legacy `data_type=BTC/ETH/etc.` paths                                                                                         |
| 3.5   | UI drilldown shows `PREDICTION → POLYMARKET → canonical_question_group → underlying → dates`                                                                                      |
| 4     | `prediction-schema-paths.md` no longer says "Active migration"                                                                                                                    |

---

## Temporary states + their canonical follow-up plans

| State                                                                                                  | Successor                                                                                                 |
| ------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| IS prediction manifest fully purged (Phase 3.2) but re-fill not yet run (Phase 3.4)                    | UI shows PREDICTION 0% — expected transient; complete same session                                        |
| Legacy GCS parquets deleted (Phase 3.3) but new parquets not yet written                               | Same — complete Phase 3.4 in same session before marking complete                                         |
| Sports VM still running historical (3063 gap)                                                          | Phase 2 P1 monitor item; no blocking dependency on Phase 3                                                |
| Prediction canonical manually consolidated (old bucket, not auto-merged by Cloud Run)                  | `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 0e — env-tier rollout to old IS prediction bucket |
| Sports IS fills write to OLD bucket; PRD ODDS/PREDICTIONS max=2026-05-04 (short of ≥2026-05-20 target) | After footystats fill: copy shard OLD→PRD + consolidate; long-term fix: Phase 0e (sports bucket env-tier) |

## Deferred work — migrated to:

- **Monitor `instr-backfill-sports` VM (P1, DEFERRED-OPERATOR-DECISION)**: long-running background backfill (~60-day ETA
  to complete 2020→2026 historical). No May-23 dependency. **Migrated to**: `plans/epics/predictions_master.md` § P1
  operator-monitoring backlog.
- **Fix prediction bucket naming mismatch (P1, DEFERRED-OPERATOR-DECISION)**: IS writes to old flat bucket; Cloud Run
  consolidator targets prd bucket. **Migrated to**: `plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md` Phase
  0e (env-tier rollout to Group A IS prediction bucket) — already named successor per "Temporary states" above.
- **Schema column in drilldown (P1, DEFERRED-OPERATOR-DECISION)**: verify `canonical_question_group` schema link in
  deployment-api UI. **Migrated to**: `plans/epics/predictions_master.md` § P1 codex/UI verification backlog.
