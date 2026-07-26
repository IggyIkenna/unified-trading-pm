---
doc_type: audit-result
title: "Data-pipeline reconciliation — defi (2026-07-25), MDPS candle layer (`--layer candles`)"
summary: >-
  First genuine `/data-pipeline-reconciliation --asset-group defi --layer candles` run (the 2026-07-23
  "data_pipeline_reconciliation_candles_defi_2026_07_23.md" doc was NOT this skill — it was the candle-path migration's
  own P8 verification using the migration script's dry-run classifier; this run is the reconciliation skill itself,
  re-pointed at the UAC oracle per todo 39). S1 (path): confirmed CANONICAL against the FULLY-migrated LOCKED shape
  (`require_candle_migration_complete=True`, zero violations on every sampled object) — the Option-A path migration is
  independently reconfirmed complete for defi. S3 (manifest): HEADLINE FINDING — zero `market-data-processing-service`
  manifest rows have a `written_at` after 2026-07-21 17:01 UTC+1 (the candle-writer manifest fix,
  `mdps@752eaff`/`2d720b4`) — i.e. not one of defi's ~1.12M live candle objects has contemporary manifest coverage, and
  none has been added in the 4 days since the fix shipped. This is unresolved by the path migration (which does not
  write the manifest) and is now scoped as its own MDPS-owned plan,
  `mdps_candle_manifest_population_disconnect_2026_07_25.md`.
status: partial
nature: record
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm, unified-api-contracts, unified-trading-library, market-data-processing-service]
scope: [engineer, admin]
tags: [reconciliation, canonicalisation, candles, defi, manifest, object-manifest-disconnect, processed_candles]
related:
  [
    four-surface-reconciliation-procedure,
    mdps-candle-canonical-reconciliation,
    reconciliation-finding-taxonomy,
    canonical-cutover-register,
    candle_feature_canonical_path_divergence_2026_07_20,
    data_pipeline_reconciliation_skill_2026_07_20,
    mdps_candle_manifest_population_disconnect_2026_07_25,
  ]
created: 2026-07-25
resulting_plan: mdps_candle_manifest_population_disconnect_2026_07_25
lib_version:
doc_versions_checked:
audited_scope:
  "asset_group=defi, layer=candles (processed_candles/), PROD (-prd-) bucket only, read-only, Phases 0->2 per the
  /data-pipeline-reconciliation skill §3h; live oracle spot-check (5 objects, day=2026-07-22) + fresh full manifest
  re-read (2026-07-25) this run; disposition histogram REUSED from the P0 census (2026-07-22) + P8 verification
  (2026-07-23) per single-walk discipline, not re-walked"
date: 2026-07-25
auditor: /data-pipeline-reconciliation (--layer candles)
parent_epic: infrastructure_master
severity: P0
skill: data-pipeline-reconciliation
run_date: 2026-07-25
generated_at: 2026-07-25T23:30:00+00:00
---

# Data-pipeline reconciliation — defi (2026-07-25), MDPS candle layer

**Read-only.** No GCS writes, no manifest writes, no deletes, no backfills, no VM launches, no `--apply`. This run is
`--layer candles` (§3h) — raw-tick was already reconciled for defi on 2026-07-24 and is out of scope here.

## 0. What "candle reconciliation" means for this run, and why the 2026-07-23 doc of the same name is NOT this

Per SKILL.md §3h, S1 is checked against the **LOCKED** candle template via the UAC oracle
(`canonical_path_violations(require_candle_migration_complete=...)`, shipped `uac@6329fc04` 2026-07-22), S3 is driven
off GCS objects (the candle manifest is near-empty by design of the open defect this run's headline finding restates),
and S4 is `UNAVAILABLE` by construction (no candle catalogue exists). The **existing**
`plans/audit/results/data_pipeline_reconciliation_candles_defi_2026_07_23.md` is a **different tool** — the candle-path
migration's own P8 post-`--apply` verification, run via `migrate_candle_canonical_2026_07.py --dry-run`, which reused
this report's filename convention but never invoked the `/data-pipeline-reconciliation` skill or the UAC oracle. This is
the **first** run of the actual skill against the candle layer for defi.

## 1. Bucket paths table

| Surface / layer | `kind`        | Resolved bucket                                    | Reachable?                                                                                                       | Read targeted                                                                                                                    |
| --------------- | ------------- | -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| candles (S1)    | `market-data` | `market-data-tick-defi-prd-central-element-323112` | **YES** — delimiter descent of `processed_candles/by_date/` returned 1,146 day-prefixes (2023-01-01..2026-07-22) | `processed_candles/by_date/` (bounded descent + 5-object sample under `day=2026-07-22`)                                          |
| manifest (S3)   | (same bucket) | `market-data-tick-defi-prd-central-element-323112` | YES                                                                                                              | `_index/availability_index.parquet` (fresh download 2026-07-25, 24,742,605 total rows, column-projected + `service_name` filter) |
| S4 catalogue    | n/a           | —                                                  | **UNAVAILABLE by construction** — no candle catalogue exists for any AG                                          | declared coverage gap, once (§5)                                                                                                 |

Resolved via `resolve_bucket_name(cloud="gcp", kind="market-data", asset_group="defi", deployment_env="prd")` —
identical bucket to raw-tick (Phase-0 resolution unchanged per §3h); `GCP_PROJECT_ID=central-element-323112` set in env,
tier passed explicitly via `deployment_env=`.

## 2. Index freshness / lock state

`_index/latest.json` (probed 2026-07-25 ~22:14 UTC):
`last_run_at=2026-07-25T22:14:04Z, success=true, verdict=produced, shards_scanned=3, shards_changed=2`.
`_index/consolidator.lock` — **absent** (not held). `_index/consolidator_stall_ state.json` —
`{"streak": 0, "baseline_shards": 8}` (not stalled). **The manifest read behind this run's S3 finding is FRESH and
consolidator-healthy, not a stale/locked fallback** — the near-zero candle-row count is not a freshness artifact.

## 3. Phase 1 — four-surface comparison (candle layer)

### S1 — path (oracle-checked against the LOCKED template)

5 real objects sampled under
`processed_candles/by_date/day=2026-07-22/pipeline_mode=batch_onchain_subgraph/ timeframe={15s,1m}/data_type=dex_pool_swaps/instrument_type=POOL/venue=UNISWAP_V3/…`
— every sampled object returns **zero violations** from `canonical_path_violations()` under BOTH
`require_candle_migration_complete=False` AND `require_candle_migration_complete=True`. This means the sampled objects
already carry the fully-migrated LOCKED shape (`instrument_type=` + `pipeline_mode=` present) — independently
reconfirming the P7/P8 migration's "CLEAN" verdict for defi via a **different tool** (the reconciliation skill's own
oracle call, not the migration script's classifier). **Verdict: CANONICAL**, sample-based (5 objects; the full
1,123,415-object corpus disposition is reused from P8 below, not re-walked).

### S2 — content / schema

Not independently re-validated this run (Tier-1 sampled id/schema smoke was not run against candles this pass — the
`-500-object cap allowance was spent on the S1 oracle sample + the manifest re-read instead, given the S3 finding was the higher-value question to nail down fresh). **Declared gap** — carried from the P0/P8 census's own schema disposition (`NEEDS_CONTENT_*`
classes = 0 for defi as of 2026-07-23), not independently re-verified today.

### S3 — manifest (the headline finding)

Fresh, full re-read of the consolidated `_index/availability_index.parquet` (24,742,605 total rows, downloaded + queried
2026-07-25), filtered `service_name=="market-data-processing-service"`:

```
rows matching service_name=="market-data-processing-service": 0
```

**Zero.** Not 6 degenerate rows like cefi — literally none for defi, consistent with the 2026-07-20/2026-07-23
measurements in `candle_feature_canonical_path_divergence_2026_07_20.md` (also 0). **Cross-AG confirmation this run
performed fresh** (not carried forward): tradfi and prediction were ALSO re-read fresh today and show, respectively, 73
rows (max `written_at` = 2026-06-22) and 168 rows (max `written_at` = 2026-05-05) — **in NEITHER case does any row's
`written_at` fall after 2026-07-21 17:01 UTC+1**, the timestamp of the candle-writer manifest fix
(`market-data-processing-service@752eaff` + same-day `@2d720b4`). Across all 4 asset_groups measured today, **zero
candle manifest rows have been written since the fix landed** — this is new information beyond the 2026-07-23
measurement (which only established the historical gap was unchanged; this run establishes the gap has ALSO not begun
closing in the 4 days since the fix, across the whole fleet, not just defi). **Verdict: `missing_row` for effectively
100% of the live corpus** — see the finding + suppression discussion below.

### S4 — catalogue

**UNAVAILABLE by construction** for the entire candle layer (no candle catalogue exists for any asset_group) — reported
once, per §3c/§3h, not per shard.

## 4. Corpus-scale disposition — REUSED from the P0 census + P8 verification (not re-walked)

Per single-walk discipline, this run does not re-walk the defi candle corpus (P8, 2026-07-23, already performed the ONE
sanctioned fresh enumeration + dry-run classify for this campaign). Reused verbatim from
`data_pipeline_reconciliation_candles_defi_2026_07_23.md` (the migration's own P8 doc):

```
TOTAL live objects (2026-07-23 fresh enumeration): 1,123,415
CANONICAL_NOOP: 1,123,415 (100%)  |  ORPHAN: 0  |  every other class: 0
```

**This run's own S1 oracle spot-check (5 objects, today) is CONSISTENT with that disposition** — no contradiction found.
The 1,442 `_quarantine/`-relocated objects (QUARANTINE_CORRUPT at census time) are structurally out of
`processed_candles/by_date/` scope by design (§4a "reality→register" direction; already tracked, not a new finding).

## 5. Typed findings

| Finding                      | Type (taxonomy)                 | Scope                                        | Suppressed / actionable                                                                                                                                                                |
| ---------------------------- | ------------------------------- | -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Candle path shape            | n/a (CANONICAL)                 | 1,123,415 objects                            | Not a finding — S1 confirmed clean, both migration-window and fully-migrated oracle modes.                                                                                             |
| Candle manifest population   | **`missing_row`** (headline)    | ~1,123,415 objects (100% of the live corpus) | **ACTIONABLE — NOT suppressed.** Not `migration_pending` (AE-6 covers path-shape deltas, not manifest population). Root-caused as its own MDPS-owned plan (see Resulting plan, above). |
| S4 catalogue absence         | declared coverage gap           | whole candle layer                           | Reported once (this section), never per-shard.                                                                                                                                         |
| Quarantine-relocated objects | `legacy_duplicate`/`unresolved` | 1,442 objects (`_quarantine/`)               | Already tracked (`candle_feature_canonical_path_divergence_2026_07_20.md` todo 2/3); out of `by_date/` scope by design, not re-flagged here.                                           |

No new non-canonical-path-inventory entries; no delete suggestions (nothing new to suggest — the only quarantined
material is already tracked and parked pending content-repair, not a duplicate-delete candidate).

## 6. Suppressed accepted-exceptions

`migration_pending` axes (missing `instrument_type=`/`pipeline_mode=`, split-brain `pipeline_mode`, SOURCE-vs-aggregated
`data_type` on the manifest) — **0 instances suppressed this run**, because the sample already carries the
fully-migrated shape (the migration completed 2026-07-22/23, before this run). This is a change from what an earlier
candle-layer run (pre-migration) would have suppressed heavily.

## 7. Coverage gaps

- S2/schema not independently re-sampled this run (declared, §3).
- S4 unavailable by construction (declared, §3h).
- The 4,700+ non-`day=2026-07-22` day-partitions were not individually oracle-sampled — reused the P8 corpus-wide
  disposition instead of re-walking.

## 8. Resulting plan

`plans/active/mdps_candle_manifest_population_disconnect_2026_07_25.md` (filed same day, per
`data_pipeline_reconciliation_skill_2026_07_20.md` todo 40) — root-causes the S3 finding above and scopes the fix +
historical backfill. Cross-AG evidence gathered for THIS report (tradfi/prediction fresh manifest re-reads) directly
seeded that plan's todo 1.
