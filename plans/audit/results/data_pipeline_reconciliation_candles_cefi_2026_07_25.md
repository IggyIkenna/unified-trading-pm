---
doc_type: audit-result
title: "Data-pipeline reconciliation — cefi (2026-07-25), MDPS candle layer (`--layer candles`)"
summary: >-
  Third `/data-pipeline-reconciliation --asset-group cefi --layer candles` run in the defi->prediction->cefi->tradfi
  sequence. S1 (path): CANONICAL against the fully-migrated LOCKED template (5 sampled objects under the most recent
  day-partition on disk, day=2026-07-21, zero oracle violations under both migration-window and fully-migrated modes).
  S3 (manifest): the same headline finding as the other 3 AGs, re-confirmed fresh — exactly the same 6 degenerate rows
  measured 2026-07-20/2026-07-23 (all date=2026-04-14, written_at=2026-04-16), byte-identical, unchanged 4 days after
  the 2026-07-21 candle-writer manifest fix. cefi is the AG with the LATEST candle day-partition of the 4 (2026-07-21,
  the exact day the fix landed) yet STILL shows zero post-fix manifest rows — the single strongest per-AG data point
  against "the fix works but nothing has run since" and for "the fix's manifest-write path is not actually being
  exercised even when a write happens", feeding directly into the new plan's hypothesis (b)/(c) track.
status: partial
nature: record
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm, unified-api-contracts, unified-trading-library, market-data-processing-service]
scope: [engineer, admin]
tags: [reconciliation, canonicalisation, candles, cefi, manifest, object-manifest-disconnect, processed_candles]
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
    data_pipeline_reconciliation_candles_prediction_2026_07_25,
  ]
created: 2026-07-25
resulting_plan: mdps_candle_manifest_population_disconnect_2026_07_25
lib_version:
doc_versions_checked:
audited_scope:
  "asset_group=cefi, layer=candles (processed_candles/), PROD (-prd-) bucket only, read-only, Phases 0->2 per
  /data-pipeline-reconciliation §3h; live oracle spot-check (5 objects, day=2026-07-21, the most recent day on disk) +
  fresh full manifest re-read (2026-07-25) this run; disposition histogram REUSED from the P0 census (2026-07-22) + P8
  verification (2026-07-23), not re-walked"
date: 2026-07-25
auditor: /data-pipeline-reconciliation (--layer candles)
parent_epic: infrastructure_master
severity: P0
skill: data-pipeline-reconciliation
run_date: 2026-07-25
generated_at: 2026-07-25T23:40:00+00:00
---

# Data-pipeline reconciliation — cefi (2026-07-25), MDPS candle layer

**Read-only.** No GCS writes, no manifest writes, no deletes, no VM launches, no `--apply`.

## 0. cefi-specific candle note

Per SKILL.md §3d/§3h, cefi carries the v5/v6 dual chain-tail hazard on raw-tick, which does not apply to the candle atom
the same way (candle `(KEY)` is `instrument_id` for flat-per-contract writes, `ticks.parquet` for chain bundles — same
rule as every other AG). No cefi-specific candle path hazard beyond H1-H5 in `reference-mdps.md` was found this run.

## 1. Bucket paths table

| Surface / layer | `kind`        | Resolved bucket                                    | Reachable?                                                                                                     | Read targeted                                                                                    |
| --------------- | ------------- | -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| candles (S1)    | `market-data` | `market-data-tick-cefi-prd-central-element-323112` | **YES** — delimiter descent of `processed_candles/by_date/` returned 327 day-prefixes (2019-03-30..2026-07-21) | `processed_candles/by_date/` (bounded descent + 5-object sample under `day=2026-07-21`)          |
| manifest (S3)   | (same bucket) | `market-data-tick-cefi-prd-central-element-323112` | YES                                                                                                            | `_index/availability_index.parquet` (fresh download 2026-07-25, 165.65 MB, 9,192,725 total rows) |
| S4 catalogue    | n/a           | —                                                  | **UNAVAILABLE by construction**                                                                                | declared coverage gap, once (§5)                                                                 |

`GCP_PROJECT_ID=central-element-323112` set in env; tier via `deployment_env="prd"` explicitly.

## 2. Index freshness / lock state

`_index/latest.json` (probed 2026-07-25 ~23:03 UTC):
`last_run_at=2026-07-25T23:03:46Z, success=true, verdict=empty, shards_scanned=1, shards_changed=0`. `consolidator.lock`
absent. `consolidator_stall_state.json`: `{"streak": 0, "baseline_shards": 8}` — not stalled. **Fresh,
consolidator-healthy read.**

## 3. Phase 1 — four-surface comparison (candle layer)

### S1 — path (oracle-checked)

5 real objects sampled under
`processed_candles/by_date/day=2026-07-21/pipeline_mode=batch_aster/timeframe={15s,1m}/ data_type=trades/instrument_type=PERPETUAL/venue=ASTER/…`
— this is the **most recent** candle day-partition of any of the 4 measured asset_groups (2026-07-21, the exact calendar
day the candle-writer manifest fix landed at 17:01 UTC+1). Every sampled object: **zero violations** under both
`require_candle_migration_complete=False` and `=True`. **Verdict: CANONICAL** (sample-based).

### S2 — content / schema

Not independently re-sampled — declared gap, same as defi/prediction. Reused P0/P8 census: cefi's
`NEEDS_CONTENT_CEFI_WIRE_ID`/`QUARANTINE_CORRUPT` classes were already resolved (todo 14/18 of the source issue doc) as
of 2026-07-22.

### S3 — manifest (headline finding — the sharpest per-AG signal of the 4)

Fresh full re-read of `_index/availability_index.parquet` (9,192,725 total rows, downloaded + queried 2026-07-25),
filtered `service_name=="market-data-processing-service"`:

```
rows: 6
all date=2026-04-14
all written_at in [2026-04-16T15:25:11.888861+00:00, 2026-04-16T15:25:11.915172+00:00]
one row per SOURCE data_type: book_snapshot_5, derivative_ticker, futures_chain, liquidations, options_chain, trades
rows with written_at > 2026-07-21T17:01:00+01:00: 0
```

**Byte-identical to the 2026-07-20 and 2026-07-23 measurements** in the source issue doc — the exact same 6 rows,
unchanged across 3 independent measurements spanning 5 days. **This is the single sharpest per-AG data point in this
4-AG run**: cefi has the LATEST live candle day-partition on disk (2026-07-21) of any measured asset_group — objects
exist for the SAME calendar day the fix shipped — yet the manifest shows **zero** rows from that day or any day since.
If a genuine candle-derivation write for `day=2026-07-21` occurred through the fixed writer, it should have called
`record_captured` and left a trace; it did not. This does not by itself prove hypothesis (b) or (c) over (a) — the
`day=2026-07-21` objects could equally have been derived by a run that started before 752eaff (17:01 UTC+1) landed, or
via the migration script (which never writes the manifest) touching an already-existing day — but it is the most
promising single day/AG combination to re-examine for the new plan's todo 1 (check whether `day=2026-07-21`'s objects'
own GCS `time_created` predates or postdates 17:01 UTC+1, which this run did not itself check — see coverage gaps).
**Verdict: `missing_row` for effectively 100% of the live corpus.**

### S4 — catalogue

**UNAVAILABLE by construction**, reported once.

## 4. Corpus-scale disposition — REUSED from P0/P8 (not re-walked)

```
TOTAL live objects (P7-processed / P8 residual, 2026-07-22/23): 940,606 processed; 149-object (0.0158%) permanent
  residual root-caused to a genuine retry-idempotency gap (candle_feature_canonical_path_divergence todo 19),
  source data never at risk.
```

Consistent with this run's own S1 spot-check (no contradiction found in the 5-object sample).

## 5. Typed findings

| Finding                               | Type (taxonomy)                      | Scope                                                             | Suppressed / actionable                                                                                                                                                     |
| ------------------------------------- | ------------------------------------ | ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Candle path shape                     | n/a (CANONICAL)                      | ~940,606 objects                                                  | Not a finding.                                                                                                                                                              |
| Candle manifest population            | **`missing_row`** (headline, shared) | ~940,457 objects (940,606 minus the 149 already-tracked residual) | **ACTIONABLE — NOT suppressed.** Same root cause as the other 3 AGs; cefi's day=2026-07-21 sample is this campaign's strongest single re-investigation lead (see S3 above). |
| 149-object retry-idempotency residual | `unresolved` (already tracked)       | 149 objects                                                       | Already tracked (`candle_feature_canonical_path_divergence_2026_07_20.md` todo 19); not re-flagged as new.                                                                  |
| S4 catalogue absence                  | declared coverage gap                | whole candle layer                                                | Reported once.                                                                                                                                                              |

No new non-canonical-path-inventory entries; no delete suggestions.

## 6. Suppressed accepted-exceptions

0 `migration_pending` suppressions needed this run.

## 7. Coverage gaps

S2/schema not independently re-sampled; the other 326 day-partitions not individually oracle-sampled; **the
`day=2026-07-21` sampled objects' own GCS `time_created` (as opposed to the migration-touched `updated` timestamp) was
not read this run** — that single check would meaningfully narrow the new plan's hypothesis (a) vs (b)/(c) and is
flagged as its cheapest next diagnostic step, not performed here to keep this run within its Phase 1/2 scope.

## 8. Resulting plan

`plans/active/mdps_candle_manifest_population_disconnect_2026_07_25.md` — this AG's evidence is the sharpest single data
point in the plan's todo 1 (root-cause) investigation.
