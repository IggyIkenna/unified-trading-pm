---
doc_type: audit-result
title: "Data-pipeline reconciliation — prediction (2026-07-25), MDPS candle layer (`--layer candles`)"
summary: >-
  Second `/data-pipeline-reconciliation --asset-group prediction --layer candles` run in the defi->prediction->cefi->
  tradfi sequence. S1 (path): CANONICAL against the fully-migrated LOCKED template (5 sampled objects, zero oracle
  violations under both migration-window and fully-migrated modes) — prediction's Option-A path migration independently
  reconfirmed complete. S3 (manifest): the same headline finding as defi — 168 `market-data-processing-service` manifest
  rows exist total, ALL with `written_at` <= 2026-05-05, i.e. zero rows added since the 2026-07-21 candle-writer
  manifest fix; 583,228+ live candle objects have essentially no contemporary manifest coverage. Notably, prediction's
  candle estate shows NO activity past day=2026-01-14 (the most recent day-partition on disk) — the most stagnant of the
  4 asset_groups measured, worth flagging alongside the manifest gap.
status: partial
nature: record
asset_group: [prediction]
stage: [data]
repos: [unified-trading-pm, unified-api-contracts, unified-trading-library, market-data-processing-service]
scope: [engineer, admin]
tags: [reconciliation, canonicalisation, candles, prediction, manifest, object-manifest-disconnect, processed_candles]
related:
  [
    four-surface-reconciliation-procedure,
    mdps-candle-canonical-reconciliation,
    reconciliation-finding-taxonomy,
    canonical-cutover-register,
    candle_feature_canonical_path_divergence_2026_07_20,
    data_pipeline_reconciliation_skill_2026_07_20,
    mdps_candle_manifest_population_disconnect_2026_07_25,
    data_pipeline_reconciliation_candles_defi_2026_07_25,
  ]
created: 2026-07-25
resulting_plan: mdps_candle_manifest_population_disconnect_2026_07_25
lib_version:
doc_versions_checked:
audited_scope:
  "asset_group=prediction, layer=candles (processed_candles/), PROD (-prd-) bucket only, read-only, Phases 0->2 per
  /data-pipeline-reconciliation §3h; live oracle spot-check (5 objects, day=2026-01-14, the most recent day on disk) +
  fresh full manifest re-read (2026-07-25) this run; disposition histogram REUSED from the P0 census (2026-07-22) + P8
  verification (2026-07-23), not re-walked"
date: 2026-07-25
auditor: /data-pipeline-reconciliation (--layer candles)
parent_epic: infrastructure_master
severity: P0
skill: data-pipeline-reconciliation
run_date: 2026-07-25
generated_at: 2026-07-25T23:35:00+00:00
---

# Data-pipeline reconciliation — prediction (2026-07-25), MDPS candle layer

**Read-only.** No GCS writes, no manifest writes, no deletes, no VM launches, no `--apply`.

## 0. Prediction-layer note

Per SKILL.md §3d, prediction's candle shard atom drops `venue=` in favour of `instrument_type=` as the terminal axis;
per §3c/§3h its S4 catalogue is UNAVAILABLE by construction (no `prediction_catalog_reader.py` exists) — this holds for
candles as it does for raw-tick. Bucket resolution differs from the other 3 AGs: `kind="market-data-tick-prediction"`
resolves the dedicated flat bucket (bucket-name STRING uses `pred`, 4 chars — the dict key stays `PREDICTION`, per
`cloud-providers.yaml`'s own documented convention), not `kind="market-data", asset_group="prediction"` (which has no
registry entry — confirmed by a direct resolver call this run,
`BucketNamingError: ... Available: ['CEFI', 'DEFI', 'SPORTS', 'TRADFI']`).

## 1. Bucket paths table

| Surface / layer | `kind`                        | Resolved bucket                                    | Reachable?                                                                                                     | Read targeted                                                                           |
| --------------- | ----------------------------- | -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| candles (S1)    | `market-data-tick-prediction` | `market-data-tick-pred-prd-central-element-323112` | **YES** — delimiter descent of `processed_candles/by_date/` returned 247 day-prefixes (2025-03-14..2026-01-14) | `processed_candles/by_date/` (bounded descent + 5-object sample under `day=2026-01-14`) |
| manifest (S3)   | (same bucket)                 | `market-data-tick-pred-prd-central-element-323112` | YES                                                                                                            | `_index/availability_index.parquet` (fresh download 2026-07-25, 763,436 total rows)     |
| S4 catalogue    | n/a                           | —                                                  | **UNAVAILABLE by construction** (whole-AG gap, pre-existing for raw-tick too)                                  | declared coverage gap, once (§5)                                                        |

`GCP_PROJECT_ID=central-element-323112` set in env; tier via `deployment_env="prd"` explicitly.

## 2. Index freshness / lock state

`_index/latest.json` (probed 2026-07-25 ~23:48 UTC):
`last_run_at=2026-07-25T23:48:36Z, success=true, verdict=empty, shards_scanned=1, shards_changed=0`. `consolidator.lock`
absent. **Fresh, consolidator-healthy read** — the near-zero candle-manifest count is not a freshness artifact.

## 3. Phase 1 — four-surface comparison (candle layer)

### S1 — path (oracle-checked)

5 real objects sampled under
`processed_candles/by_date/day=2026-01-14/pipeline_mode=batch_polymarket_clob/ timeframe=15m/data_type=trades/instrument_type=PREDICTION_MARKET/venue=POLYMARKET/…`
(note: prediction's candle path DOES carry `venue=POLYMARKET` on disk today, ahead of the LOCKED target which drops
`venue=` for prediction per SKILL.md §3h — worth a follow-up read of whether the oracle's prediction branch expects
`venue=` present or absent; this run's oracle calls returned **zero violations either way**, so it is not blocking, just
noted for precision). Every sampled object: **zero violations** from `canonical_path_violations()` under both
`require_candle_migration_complete=False` and `=True`. **Verdict: CANONICAL** (sample-based; corpus disposition reused
from P8 below).

### S2 — content / schema

Not independently re-sampled this run — declared gap, same as defi (§3 of the defi companion report). Reused P0/P8
census: prediction's `NEEDS_CONTENT_*` classes = 0 as of 2026-07-23.

### S3 — manifest (headline finding, consistent with defi/cefi/tradfi)

Fresh full re-read of `_index/availability_index.parquet` (763,436 total rows, downloaded + queried 2026-07-25),
filtered `service_name=="market-data-processing-service"`:

```
rows: 168
date value_counts: spread across 2025-03-xx dates (8 rows per date, one per data_type-ish grouping)
written_at range: [2026-04-29T02:04:12Z, 2026-05-05T16:25:51Z]
rows with written_at > 2026-07-21T17:01:00+01:00 (the candle-writer manifest fix): 0
```

Same pattern as defi (0 rows), cefi (6 rows), and tradfi (73 rows, below): **zero candle manifest rows have been written
since the fix landed, across every asset_group measured.** Against **583,228 live candle objects** (P0/P8 count,
2026-07-23) this is a **near-total** disconnect (168 stale rows against 583K+ live objects, none from the fixed writer).
**Verdict: `missing_row` for effectively 100% of the live corpus.**

**Separately worth flagging**: prediction's most recent `processed_candles/` day-partition on disk is `day=2026-01-14` —
over 6 months stale relative to today (2026-07-25), and the most stagnant of the 4 measured asset_groups (defi/cefi/
tradfi all have day-partitions through 2026-07-21/22). This may simply reflect prediction's own market-data cadence (if
PREDICTION_MARKET candle derivation runs less frequently or the venue itself produces less recent data), or it may
indicate the prediction candle derivation pipeline is not running at the same cadence as the other 3 AGs — **not
diagnosed this run** (out of this skill's Phase 1/2 scope; flagged for the new MDPS plan's todo 1 as an additional data
point on hypothesis (a), since a stopped/rare derivation cadence for prediction specifically would be consistent with,
though not by itself proof of, no post-fix write having occurred).

### S4 — catalogue

**UNAVAILABLE by construction**, reported once.

## 4. Corpus-scale disposition — REUSED from P0/P8 (not re-walked)

```
TOTAL live objects (P8, 2026-07-23): 583,228
CANONICAL_NOOP: 583,228 (100%)  |  ORPHAN: 0  |  every other class: 0
```

Consistent with this run's own S1 spot-check.

## 5. Typed findings

| Finding                                               | Type (taxonomy)                                       | Scope              | Suppressed / actionable                                                                                                                      |
| ----------------------------------------------------- | ----------------------------------------------------- | ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Candle path shape                                     | n/a (CANONICAL)                                       | 583,228 objects    | Not a finding.                                                                                                                               |
| Candle manifest population                            | **`missing_row`** (headline, shared across all 4 AGs) | ~583,228 objects   | **ACTIONABLE — NOT suppressed.** Same root cause as defi/cefi/tradfi; tracked in `mdps_candle_manifest_population_disconnect_2026_07_25.md`. |
| Stale candle derivation cadence (prediction-specific) | not yet a taxonomy type — flagged, not classified     | whole AG           | Un-diagnosed observation, handed to the new plan's todo 1 as a data point, not asserted as a defect.                                         |
| S4 catalogue absence                                  | declared coverage gap                                 | whole candle layer | Reported once.                                                                                                                               |

No new non-canonical-path-inventory entries; no delete suggestions.

## 6. Suppressed accepted-exceptions

0 `migration_pending` suppressions needed this run (sample already carries the fully-migrated shape).

## 7. Coverage gaps

S2/schema not independently re-sampled; the other 246 day-partitions not individually oracle-sampled (reused P8's
corpus-wide disposition); the stale-cadence observation not root-caused.

## 8. Resulting plan

`plans/active/mdps_candle_manifest_population_disconnect_2026_07_25.md` — this AG's evidence (168 rows, all stale, 0
post-fix) folds into that plan's cross-AG confirmation table.
