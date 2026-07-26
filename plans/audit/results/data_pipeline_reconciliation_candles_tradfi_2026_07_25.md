---
doc_type: audit-result
title: "Data-pipeline reconciliation — tradfi (2026-07-25), MDPS candle layer (`--layer candles`)"
summary: >-
  Fourth and final `/data-pipeline-reconciliation --asset-group tradfi --layer candles` run in the
  defi->prediction->cefi->tradfi sequence, closing out the campaign. S1 (path): CANONICAL against the fully-migrated
  LOCKED template for the sampled (already-migrated, `COMBO`/`ticks.parquet` bundle) objects — consistent with P8's "0
  outstanding" verdict for tradfi's by_date/ tree; the ~7.1M-object `_quarantine/` residual (unresolvable TradFi
  migration-artifact leaf ids, already tracked as todo 3 of the source issue doc) is reconfirmed structurally
  out-of-scope for this by_date/-only skill pass, not re-diagnosed here. S3 (manifest): the same cross-AG headline
  finding, now confirmed on all 4 measured asset_groups — 73 `market-data-processing-service` manifest rows exist total,
  ALL with `written_at` <= 2026-06-22, i.e. zero rows added since the 2026-07-21 candle-writer manifest fix, against
  534,679+ live (non-quarantined) candle objects. This closes the reconciliation-skill campaign for the candle layer
  across all 4 in-scope asset_groups (sports is out of scope per SKILL.md H1 — a different tree, `processed/`, not
  `processed_candles/`).
status: partial
nature: record
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm, unified-api-contracts, unified-trading-library, market-data-processing-service]
scope: [engineer, admin]
tags: [reconciliation, canonicalisation, candles, tradfi, manifest, object-manifest-disconnect, processed_candles]
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
    data_pipeline_reconciliation_candles_cefi_2026_07_25,
  ]
created: 2026-07-25
resulting_plan: mdps_candle_manifest_population_disconnect_2026_07_25
lib_version:
doc_versions_checked:
audited_scope:
  "asset_group=tradfi, layer=candles (processed_candles/by_date/ ONLY -- _quarantine/ out of scope), PROD (-prd-) bucket
  only, read-only, Phases 0->2 per /data-pipeline-reconciliation §3h; live oracle spot-check (5 objects, day=2026-07-22,
  the most recent day on disk) + fresh full manifest re-read (2026-07-25) this run; disposition histogram REUSED from
  the P0 census (2026-07-22) + P8 verification (2026-07-23), not re-walked"
date: 2026-07-25
auditor: /data-pipeline-reconciliation (--layer candles)
parent_epic: infrastructure_master
severity: P0
skill: data-pipeline-reconciliation
run_date: 2026-07-25
generated_at: 2026-07-25T23:50:00+00:00
---

# Data-pipeline reconciliation — tradfi (2026-07-25), MDPS candle layer

**Read-only.** No GCS writes, no manifest writes, no deletes, no VM launches, no `--apply`.

## 0. tradfi-specific candle note — the ~7.1M-object quarantine residual is OUT of THIS pass's scope, not re-diagnosed

Per SKILL.md §3d, tradfi carries the write-time raising guard and the `batch_massive` read-recognition carve-out on
raw-tick; for candles, the load-bearing tradfi-specific fact is the **already-tracked** ~7.1M-object
`_quarantine/`-relocated residual (unresolvable `E1AF0_*_migrated_*` leaf ids,
`candle_feature_canonical_path_ divergence_2026_07_20.md` todo 3) — 93% of tradfi's original candle corpus. This run's
scope is `processed_candles/ by_date/` only (per its own `audited_scope`); the quarantine tree is a **different,
disjoint** top-level prefix and is correctly out of scope here, exactly as it was for defi's smaller quarantine (1,442
objects, confirmed in the defi companion report). **Not re-diagnosing todo 3 in this run** — it needs a real leaf-id
content-read resolution pass or an operator won't-fix ruling, neither of which this reconciliation pass performs.

## 1. Bucket paths table

| Surface / layer | `kind`        | Resolved bucket                                      | Reachable?                                                                                                     | Read targeted                                                                           |
| --------------- | ------------- | ---------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| candles (S1)    | `market-data` | `market-data-tick-tradfi-prd-central-element-323112` | **YES** — delimiter descent of `processed_candles/by_date/` returned 884 day-prefixes (2020-01-01..2026-07-22) | `processed_candles/by_date/` (bounded descent + 5-object sample under `day=2026-07-22`) |
| manifest (S3)   | (same bucket) | `market-data-tick-tradfi-prd-central-element-323112` | YES                                                                                                            | `_index/availability_index.parquet` (fresh download 2026-07-25, 5,826,709 total rows)   |
| S4 catalogue    | n/a           | —                                                    | **UNAVAILABLE by construction**                                                                                | declared coverage gap, once (§5)                                                        |
| `_quarantine/`  | (same bucket) | `market-data-tick-tradfi-prd-central-element-323112` | not re-probed this run                                                                                         | out of scope for THIS pass — see §0                                                     |

`GCP_PROJECT_ID=central-element-323112` set in env; tier via `deployment_env="prd"` explicitly.

## 2. Index freshness / lock state

`_index/latest.json` (probed 2026-07-25 ~23:48 UTC):
`last_run_at=2026-07-25T23:48:44Z, success=true, verdict=empty, shards_scanned=1, shards_changed=0`. `consolidator.lock`
absent. **Fresh, consolidator-healthy read.**

## 3. Phase 1 — four-surface comparison (candle layer)

### S1 — path (oracle-checked)

5 real objects sampled under
`processed_candles/by_date/day=2026-07-22/pipeline_mode=batch_databento/timeframe=15m/ data_type=ohlcv_1m/instrument_type=COMBO/venue=CME/underlying={CL,GOLD,HEATING-OIL,RBOB-GAS,SILVER}/ticks.parquet`
— a chain-bundle write (`(KEY)` = the `ticks.parquet` bundle name, per the shard-atom rule, not a per-instrument leaf;
this is NOT one of the `E1AF0_*_migrated_*` non-canonical leaf ids the quarantine tree holds — those are
single-instrument writes, structurally different from this `COMBO`/bundle sample). Every sampled object: **zero
violations** under both `require_candle_migration_complete=False` and `=True`. **Verdict: CANONICAL** for the sampled
shape (sample-based; this pass did not sample a single-instrument tradfi leaf, so it does not independently re-confirm
the `by_date/` tree is 100% free of non-canonical leaf ids beyond what P8 already established — see coverage gaps).

### S2 — content / schema

Not independently re-sampled — declared gap, consistent with the other 3 AGs this campaign.

### S3 — manifest (headline finding, 4th and final confirmation)

Fresh full re-read of `_index/availability_index.parquet` (5,826,709 total rows, downloaded + queried 2026-07-25),
filtered `service_name=="market-data-processing-service"`:

```
rows: 73
instrument_type: '' (empty) for all 73 -- pre-dates the D1/instrument_type-add migration's manifest re-key
row_count non-null: 61 of 73
written_at range: [2026-05-05T20:03:32.537739+00:00, 2026-06-22T12:12:27.944733+00:00]
rows with written_at > 2026-07-21T17:01:00+01:00: 0
date value_counts concentrated in 2020-01-xx (12 rows each on several dates) + scattered 2026-01-0x singles
```

Same pattern as the other 3 AGs: **zero candle manifest rows written since the fix landed.** Against **534,679 live
(non-quarantined) candle objects** (P8, 2026-07-23) plus the ~7.1M quarantined-but-real objects, this is a near-total
disconnect on the non-quarantined tree and a complete one on the quarantined tree (quarantined objects would need
content-repair before they could even reach a manifest-eligible state, independent of this finding). **Verdict:
`missing_row` for effectively 100% of the live corpus.** This is the 4th of 4 asset_groups measured fresh today
(alongside defi 0 rows, prediction 168 rows, cefi 6 rows) with **zero** post-2026-07-21 manifest activity — the
campaign-wide pattern is unambiguous: this is a fleet-wide gap, not an asset_group-specific one.

### S4 — catalogue

**UNAVAILABLE by construction**, reported once (campaign-wide, not per-AG — this is the 4th and final time it is
reported in this campaign; see the campaign summary below).

## 4. Corpus-scale disposition — REUSED from P0/P8 (not re-walked)

```
P7-processed (2026-07-22/23): 7,646,831 objects (survived 3 severe SPOT-preemption storms, recovered fully)
P8-live (by_date/, 2026-07-23): 534,679 objects
Gap (in _quarantine/, unresolvable leaf ids, todo 3): 7,112,152 objects (93.0% of the P7-processed total)
```

Consistent with this run's own day-prefix count (884 day-prefixes on `by_date/` today) and S1 spot-check (no
contradiction found).

## 5. Typed findings

| Finding                             | Type (taxonomy)                                        | Scope                            | Suppressed / actionable                                                                                                                        |
| ----------------------------------- | ------------------------------------------------------ | -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Candle path shape (by_date/ sample) | n/a (CANONICAL)                                        | 534,679 objects                  | Not a finding for the sampled shape.                                                                                                           |
| Candle manifest population          | **`missing_row`** (headline, shared, 4th confirmation) | ~534,679 objects (by_date/ only) | **ACTIONABLE — NOT suppressed.** Same root cause as defi/prediction/cefi; campaign-wide, not tradfi-specific.                                  |
| Quarantined unresolvable leaf ids   | `non_canonical_id` (already tracked)                   | ~7,112,152 objects               | Already tracked (`candle_feature_canonical_path_divergence_2026_07_20.md` todo 3); not re-diagnosed, out of this pass's `by_date/`-only scope. |
| S4 catalogue absence                | declared coverage gap                                  | whole candle layer               | Reported once per AG per the skill's own rule; this is the 4th/final report in the campaign.                                                   |

No new non-canonical-path-inventory entries; no delete suggestions (the quarantine tree already has a disposition —
content-repair-pending — and is not a duplicate-delete candidate).

## 6. Suppressed accepted-exceptions

0 `migration_pending` suppressions needed this run (sampled shape already fully migrated).

## 7. Coverage gaps

S2/schema not independently re-sampled; the `_quarantine/` tree (~7.1M objects) not re-probed this run (out of scope,
already tracked); a single-instrument (non-`COMBO`) tradfi leaf was not sampled this run, so this pass does not itself
re-confirm the `by_date/` tree's 100% canonical-leaf claim beyond reusing P8.

## 8. Campaign summary — defi -> prediction -> cefi -> tradfi, `--layer candles`, 2026-07-25

All 4 in-scope asset_groups (sports excluded per SKILL.md H1 — `processed/`, not `processed_candles/`) reconciled this
campaign. **Cells reconciled: 4/4.** **S1 (path)**: CANONICAL on every sampled object, all 4 AGs, both oracle modes —
independently reconfirms the Option-A path migration's P7/P8 "CLEAN" verdict via the reconciliation skill's own oracle
call rather than the migration script's classifier. **S3 (manifest)**: identical headline finding on all 4 AGs — **0
candle manifest rows with `written_at` after 2026-07-21 17:01 UTC+1** (defi 0, prediction 168-all-stale, cefi
6-all-stale, tradfi 73-all-stale), against a combined ~2.2M+ non-quarantined live candle objects (plus tradfi's ~7.1M
quarantined). **S4**: UNAVAILABLE by construction, all 4 AGs, reported once each. **Findings by type**: `missing_row`
(headline, all 4 AGs) · already-tracked `non_canonical_id` (tradfi quarantine, ~7.1M) · already-tracked residual (cefi,
149 objects) · one un-diagnosed observation (prediction's stale 2026-01-14 day-partition ceiling). **Delete suggestions:
0** (nothing new; existing quarantine/residual items already have a disposition). **Coverage gaps still open**:
S2/schema sampling deferred on all 4 AGs; the tradfi quarantine tree and cefi's `day=2026-07-21` `time_created` check
are the two highest-value next reads, both handed to
`plans/active/mdps_candle_manifest_population_disconnect_2026_07_25.md`. **Unruled axes still blocking**: none —
D1/D2/D3 and the candle path migration are all RULED and (for the path) COMPLETE; the manifest-population gap is a
genuine, newly-scoped defect, not an open ruling question.
