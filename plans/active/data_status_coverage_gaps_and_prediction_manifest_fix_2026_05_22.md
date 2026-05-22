---
title: "Data-Status Coverage Gaps + Prediction IS Manifest Structural Fix"
created: 2026-05-22
author: slot-1
parent_epic: predictions_master
assigned_vm: vm-prediction
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
---

## Context

Diagnostic session 2026-05-22 surfaced three IS data-quality gaps visible in the
deployment-ui data-status panel. All are IS-layer issues (not UAC coverage gaps, not
data-status display bugs per se — though the prediction display is broken as a downstream
symptom of the IS manifest bug).

### Codex SSOTs

- [`codex/02-data/prediction-schema-paths.md`](../../codex/02-data/prediction-schema-paths.md) —
  target shard atom for prediction; currently says "Active migration" pointing to archived Plan A.
  **This plan resumes Plan A's IS half.** Update `last_reviewed` + remove stale "Active migration"
  pointer once Phase 3 ships.
- [`codex/02-data/data-status-drilldown-hierarchy.md`](../../codex/02-data/data-status-drilldown-hierarchy.md) —
  declares IS prediction drilldown: `venue → canonical_question_group → data_type → date`. Currently
  violated by IS writing `data_type=BTC/ETH/etc.`. Update nothing until Phase 3 ships (doc is already
  correct — IS is the laggard).
- [`codex/02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md) —
  shard-atom matrix; prediction row must match once Phase 3 ships.
- [`codex/02-data/sports-data-source-coverage-matrix.md`](../../codex/02-data/sports-data-source-coverage-matrix.md) —
  sports source windows (api_football 2018-01-01, footystats 2019-01-01); `KNOWN_COVERAGE_GAPS = {}`
  (empty). Phase 2 gaps are confirmed not UAC issues.

### Diagnosis summary

| Issue | Root cause | GCS migration? | Manifest migration? |
|---|---|---|---|
| **IS CeFi recent gap** (BITFINEX-SPOT 18d, BITGET-FUTURES 24d, BITGET-SPOT 23d) | Phase-3 backfill stopped 2026-05-04; BITGET has 5-6 phantom `capture_status=None` rows | No | Purge phantom rows, re-fetch |
| **IS Sports recent gap** (FIXTURE_EVENTS/LINEUPS 38d, ODDS 35d, INJURIES 22d) | `instr-backfill-sports` VM handling historical; recent window never ran | No | Re-fetch fills manifest |
| **IS Prediction manifest structural bug** | IS still writes legacy `data_type=BTC/ETH/SOL/OTHER` with blank `underlying`; archived Plan A never executed IS half; 3,145 of 3,940 rows `capture_status=None` | **YES** — GCS parquets keyed on wrong `data_type` partition must be deleted | **YES** — all 3,940 manifest rows need purge + re-write |

### Prediction bug detail

IS manifest today:
```
data_type = BTC / ETH / SOL / FOOTBALL / OTHER     ← wrong: treating data_type as underlying bucket
underlying = ""                                     ← blank — should hold BTC/ETH/etc.
capture_status = None (3,145 rows) / captured (795) ← majority never finalised
```

Target per UAC `CanonicalQuestionGroup` and `codex/02-data/data-status-drilldown-hierarchy.md`:
```
data_type = prediction_canonical_question_group     ← literal string, one value
canonical_question_group = BTC_UP_DOWN_DAILY        ← CanonicalQuestionGroup enum value
underlying = BTC                                    ← base asset
capture_status = captured / empty_confirmed
```

The deployment-ui then mixes IS `data_type=BTC` rows with MTDS `data_type=prediction_canonical_question_group` rows
at the same hierarchy level — "worst of both worlds": no question-group → underlying → dates breakdown.

---

## Execution Plan

### Phase 1 — IS CeFi gap fill verification (P0)

> Backfill `BITFINEX-SPOT BITGET-FUTURES BITGET-SPOT` for 2025-09-01→2026-05-22 launched
> in-session (PID 17803). These items verify completion and clean up phantom rows.

- [ ] [SCRIPT] P0. **Verify CeFi backfill complete**: poll
  `instruments-service/logs/local-recent-fill-*/summary.log` until all 3 venues report `DONE rc=0`.
  Expected: BITFINEX-SPOT +18 captured, BITGET-FUTURES +18 captured (recent), BITGET-SPOT +18 captured (recent).

- [ ] [SCRIPT] P0. **Purge BITGET phantom rows**: query IS cefi manifest for rows where
  `venue IN (BITGET-FUTURES, BITGET-SPOT) AND capture_status IS NULL`. Verify count ≤ 11 (6+5 known).
  Delete via `scripts/purge_pre_launch_manifest_rows.py` or direct manifest shard edit. Re-run IS cefi
  batch for those specific dates (`--venues BITGET-FUTURES --start-date 2025-09-04 --end-date 2025-09-04`
  etc. per the 11 scattered dates).

- [ ] [SCRIPT] P0. **Verify**: re-query IS cefi manifest — BITFINEX-SPOT, BITGET-FUTURES, BITGET-SPOT
  all 100% captured with no `capture_status=None` rows. Screenshot / log evidence.

### Phase 2 — IS Sports recent-window gap fill (P0)

> `KNOWN_COVERAGE_GAPS = {}` — these are genuinely missing data, not UAC gaps.
> `instr-backfill-sports` VM (34.180.105.8) handles pre-2026-04 historical.
> These items cover the 22-38 day recent window the VM won't reach.

- [ ] [SCRIPT] P0. **api_football recent fill** (FIXTURE_EVENTS, FIXTURE_LINEUPS, FIXTURE_STATS,
  INJURIES, PLAYER_STATS): run local chunked backfill:
  ```bash
  cd instruments-service
  bash scripts/sports_chunked_backfill.sh API_FOOTBALL 2026-04-14 2026-05-22
  ```
  Expected: fills ~38-day gap for FIXTURE_EVENTS/LINEUPS, ~22-day gap for INJURIES.

- [ ] [SCRIPT] P0. **footystats recent fill** (MATCHES, ODDS, STANDINGS, PREDICTIONS):
  ```bash
  bash scripts/sports_chunked_backfill.sh FOOTYSTATS 2026-04-17 2026-05-22
  ```
  Expected: fills ~35-day gap for ODDS, ~10-day gap for MATCHES.

- [ ] [SCRIPT] P0. **Verify sports recent window**: re-query IS sports manifest — all 6 data types have
  `max(captured_date) >= 2026-05-20`. Log counts before/after.

- [ ] [SCRIPT] P1. **Monitor `instr-backfill-sports` VM**: check
  `gcloud compute instances describe instr-backfill-sports --zone=asia-northeast1-c` until STATUS=TERMINATED.
  Verify 3063 missing dates drop to < 200 (residual off-season/no-fixture days are expected
  `empty_confirmed` rows, not missing). If VM terminates with > 200 remaining, dispatch targeted
  re-fill per data-type for the remaining gap.

### Phase 3 — IS Prediction manifest structural fix (P0, main work)

> Resumes archived Plan A IS half.
> Codex SSOT: `codex/02-data/prediction-schema-paths.md` (already describes target state).

#### 3.1 — Fix IS prediction writer (code)

- [ ] [SCRIPT] P0. **Read the IS prediction writer**: open
  `instruments-service/instruments_service/adapters/polymarket/` (or equivalent path) and identify
  where the manifest `record_captured(data_type=<base_asset>)` call is made. Confirm the write site.

- [ ] [SCRIPT] P0. **Fix the writer** to emit the canonical shard atom:
  - `data_type = "prediction_canonical_question_group"` (literal string)
  - `canonical_question_group = <CanonicalQuestionGroup enum value>` (e.g. `BTC_UP_DOWN_DAILY`)
  - `underlying = <base_asset>` (BTC, ETH, etc.)
  Import from `unified_api_contracts.canonical.domain.predictions.canonical_groups.CanonicalQuestionGroup`.
  Use the classifier in `unified_api_contracts.canonical.domain.predictions.classifiers` to map raw
  Polymarket market_id → `CanonicalQuestionGroup`.

- [ ] [TEST] P0. **Update/add unit tests** for the prediction writer: mock the classifier + verify
  manifest `record_captured` is called with correct `data_type`, `canonical_question_group`, `underlying`.
  Run `bash scripts/quality-gates.sh` → exit 0.

#### 3.2 — Purge bad IS prediction manifest rows

- [ ] [SCRIPT] P0. **Snapshot manifest before purge**: download current
  `instruments-store-prediction-central-element-323112/_index/availability_index.parquet` and save to
  `_index/snapshots/pre_prediction_fix_2026_05_22.parquet`.

- [ ] [SCRIPT] P0. **Purge all 3,940 IS prediction manifest rows**: the legacy format is unrecoverable
  (wrong `data_type`, blank `underlying`, 3,145 `capture_status=None` rows). Use
  `scripts/purge_pre_launch_manifest_rows.py` or equivalent manifest purge targeting
  `asset_group=prediction AND venue=POLYMARKET` across all manifest shards (canonical + per_vm).
  Verify row count = 0 after purge.

#### 3.3 — Delete bad IS prediction GCS parquets

- [ ] [SCRIPT] P0. **Enumerate bad GCS parquets**: list objects under
  `gs://instruments-store-prediction-central-element-323112/` where path contains
  `data_type=BTC` / `data_type=ETH` / `data_type=SOL` / `data_type=FOOTBALL` / `data_type=OTHER` /
  `data_type=XRP` / `data_type=CRUDE_OIL` / `data_type=GOLD` / `data_type=SILVER` /
  `data_type=DJIA` / `data_type=NDX` / `data_type=HYPE` / `data_type=BNB` / `data_type=DOGE` /
  `data_type=SPX`.
  Use `unified_trading_library.cloud_interface.gcs_describe_object` to enumerate. Log total count.

- [ ] [SCRIPT] P0. **Delete bad GCS parquets**: use `unified_trading_library.cloud_interface.gcs_delete_object`
  (NOT `gsutil`). Log each deleted path. Verify bucket contains only `_index/` and any
  `data_type=prediction_canonical_question_group/` objects after deletion.

#### 3.4 — Re-run IS prediction backfill

- [ ] [SCRIPT] P0. **Re-fetch IS prediction** with fixed writer: run local IS batch for Polymarket from
  coverage start:
  ```bash
  cd instruments-service
  VM_NAME=local_prediction_fix_$(date +%Y%m%d) MANIFEST_PER_VM_SHARDS=true \
    .venv/bin/instruments-service \
      --operation instruments --mode batch \
      --asset-group PREDICTION \
      --start-date 2024-01-01 --end-date 2026-05-22
  ```
  Coverage start for Polymarket is 2024-01 (per UAC Polymarket coverage probe 2026-05-17).

- [ ] [SCRIPT] P0. **Verify canonical manifest shape**: query IS prediction manifest post-fill.
  Assert:
  - All rows have `data_type = "prediction_canonical_question_group"`
  - All rows have non-blank `canonical_question_group` (valid `CanonicalQuestionGroup` enum value)
  - All rows have non-blank `underlying` (BTC/ETH/SOL/etc.)
  - Zero rows with `capture_status=None`
  - Captured + empty_confirmed = expected day count for coverage window
  Log the counts per `canonical_question_group`.

#### 3.5 — Data-status drilldown prediction display fix

- [ ] [SCRIPT] P1. **Verify drilldown hierarchy**: after IS manifest is correct, reload the deployment-api
  data-status panel for PREDICTION. Confirm hierarchy shows:
  `PREDICTION → POLYMARKET → canonical_question_group → underlying → dates`
  (per `codex/02-data/data-status-drilldown-hierarchy.md` IS prediction row).
  If the UI still mixes IS + MTDS rows at wrong levels, read `data_status_drilldown.py` lines 280-600
  to find the prediction axis routing and fix to use `canonical_question_group` as the primary group key
  instead of `data_type`.

- [ ] [SCRIPT] P1. **Schema column in drilldown**: the UI shows "schema" per `canonical_question_group`.
  The schema definition per group lives in
  `unified_api_contracts.canonical.domain.predictions.canonical_groups.CANONICAL_GROUP_METADATA`.
  Verify the schema link in the UI points to the correct UAC per-group metadata
  (not one flat schema for all Polymarket — each group has its own cadence/shape per `CanonicalQuestionGroup`).

### Phase 4 — Codex alignment (P1)

- [ ] [DOC] P1. **Update `codex/02-data/prediction-schema-paths.md`**: replace "Active migration" pointer
  to archived Plan A with reference to this plan. Update `last_reviewed: 2026-05-22`. Add a section
  confirming IS migration complete once Phase 3.4 ships.

- [ ] [DOC] P1. **Update `codex/02-data/sports-data-source-coverage-matrix.md`**: confirm
  `KNOWN_COVERAGE_GAPS = {}` is still accurate post-Phase 2 recent fills. Add a note that sports
  3063 missing dates were confirmed as unfetched (not UAC gaps) per 2026-05-22 diagnostic.

---

## Verification criteria

| Phase | Green signal |
|---|---|
| 1 | IS cefi manifest: BITFINEX-SPOT 2334/2334, BITGET-FUTURES 561/561, BITGET-SPOT 561/561; zero `capture_status=None` |
| 2 | IS sports manifest: FIXTURE_EVENTS/LINEUPS max_date ≥ 2026-05-20; ODDS max_date ≥ 2026-05-20 |
| 3 | IS prediction manifest: all rows have `data_type=prediction_canonical_question_group` + non-blank `canonical_question_group` + non-blank `underlying`; zero `capture_status=None` |
| 3 | GCS `instruments-store-prediction`: no objects with legacy `data_type=BTC/ETH/etc.` paths |
| 3.5 | UI drilldown shows `PREDICTION → POLYMARKET → canonical_question_group → underlying → dates` |
| 4 | `prediction-schema-paths.md` no longer says "Active migration" |

---

## Temporary states + their canonical follow-up plans

| State | Successor |
|---|---|
| IS prediction manifest fully purged (Phase 3.2) but re-fill not yet run (Phase 3.4) | UI shows PREDICTION 0% — expected transient; complete same session |
| Legacy GCS parquets deleted (Phase 3.3) but new parquets not yet written | Same — complete Phase 3.4 in same session before marking complete |
| Sports VM still running historical (3063 gap) | Phase 2 P1 monitor item; no blocking dependency on Phase 3 |
