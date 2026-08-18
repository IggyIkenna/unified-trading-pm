---
doc_type: audit-result
title: "Data-pipeline reconciliation — tradfi (2026-08-17), MDPS candle layer (`--layer candles`)"
summary: >-
  Fifth `/data-pipeline-reconciliation --asset-group tradfi --layer candles` run (after the 2026-07-25 campaign close-
  out). The 07-25 report's HEADLINE finding — a near-total candle-manifest-population disconnect (73 rows total,
  all stale before 2026-06-22, against 534,679+ live candle objects) — is now RESOLVED: the manifest carries
  6,720,871 `market-data-processing-service` rows with `written_at` current through 2026-08-16 (yesterday), all with
  non-null `row_count`. S1 (path): CANONICAL against the fully-migrated LOCKED template on every sampled object
  (0 violations under both `require_candle_migration_complete=False` AND `=True`) — the candle path migration
  (`instrument_type=` addition) that was still "migration_pending" as of 07-25 now appears FULLY COMPLETE on the
  sampled shape (both COMBO-bundle and FUTURE-labeled-bundle objects carry `instrument_type=` on the path). The
  ~7.1M-object `_quarantine/`-relocated residual (unresolvable TradFi migration-artifact leaf ids) remains structurally
  out of this pass's `by_date/`-only scope, not re-diagnosed here, consistent with the 07-25 report's own scoping.
status: partial
nature: record
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm, unified-api-contracts, unified-trading-library, market-data-processing-service]
scope: [engineer, admin]
tags: [reconciliation, canonicalisation, candles, tradfi, manifest, processed_candles, terminal-gate]
related:
  [
    four-surface-reconciliation-procedure,
    mdps-candle-canonical-reconciliation,
    reconciliation-finding-taxonomy,
    canonical-cutover-register,
    candle_feature_canonical_path_divergence_2026_07_20,
    data_pipeline_reconciliation_skill_2026_07_20,
    data_pipeline_reconciliation_candles_tradfi_2026_07_25,
    tradfi_phase_d_terminal_gate_2026_07_24,
  ]
created: 2026-08-17
resulting_plan: tradfi_phase_d_terminal_gate_2026_07_24
lib_version:
doc_versions_checked:
audited_scope:
  "asset_group=tradfi, layer=candles (processed_candles/by_date/ ONLY -- _quarantine/ out of scope), PROD (-prd-)
  bucket only, read-only, Tier-1 in-session; bounded day-prefix descent + 20-object oracle sample under the most
  recent day on disk (day=2026-08-07) + fresh full manifest re-read (2026-08-17); disposition histogram (P0/P7/P8
  figures) REUSED from the 2026-07 campaign, not re-walked this run"
date: 2026-08-17
auditor: /data-pipeline-reconciliation (--layer candles)
parent_epic: security_and_cross_cutting_master
severity: P2
skill: data-pipeline-reconciliation
run_date: 2026-08-17
generated_at: 2026-08-17T05:50:00+00:00
---

# Data-pipeline reconciliation — tradfi (2026-08-17), MDPS candle layer

**Read-only.** No GCS writes, no manifest writes, no deletes, no VM launches, no `--apply`.

## ⭐ VERDICT (lead)

**The 2026-07-25 campaign's headline candle finding — a near-total object↔manifest disconnect — is RESOLVED for
tradfi.** The candle manifest population has grown from 73 stale rows (all `written_at <= 2026-06-22`) to **6,720,871
rows with `written_at` current through 2026-08-16** (yesterday, one day before this run), all carrying a non-null
`row_count`. S1 path canonicality is clean on every sampled object, including under the **strict** `require_candle_
migration_complete=True` mode — the `instrument_type=` path-migration that was still `migration_pending` as of 07-25
now reads as complete on the sampled shape. S4 remains `UNAVAILABLE` by construction (no candle catalogue exists). The
`_quarantine/` residual (~7.1M objects, already tracked) is out of this pass's scope, unchanged.

## 0. tradfi-specific candle note — the ~7.1M-object quarantine residual remains out of THIS pass's scope

Unchanged from 07-25: per SKILL.md §3d/§3h and `candle_feature_canonical_path_divergence_2026_07_20.md` todo 3, the
`_quarantine/`-relocated unresolvable `E1AF0_*_migrated_*` leaf-id population (~93% of tradfi's original candle corpus
per the 07-25 report's P7/P8 figures) is a separate, disjoint top-level prefix from `processed_candles/by_date/`, and
this pass's scope (per its own `audited_scope`) is `by_date/` only. **Not re-diagnosed or re-measured this run** — it
still needs a real leaf-id content-read resolution pass or an operator won't-fix ruling.

## 1. Bucket paths table

| Surface / layer | `kind`        | Resolved bucket                                      | Reachable?                                                                                  | Read targeted                                                                            |
| ---------------- | ------------- | ------------------------------------------------------ | ---------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| candles (S1)     | `market-data` | `market-data-tick-tradfi-prd-central-element-323112`   | **YES** — delimiter descent of `processed_candles/by_date/` returned 1,815 day-prefixes (up from 07-25's 884) | `processed_candles/by_date/` (bounded descent + 30-object sample under `day=2026-08-07`, the most recent day on disk) |
| manifest (S3)    | (same bucket) | `market-data-tick-tradfi-prd-central-element-323112`   | YES                                                                                          | `_index/availability_index.parquet` (same fresh download used for the raw-tick pass, 2026-08-17, 14,457,858 total rows) |
| S4 catalogue     | n/a           | —                                                        | **UNAVAILABLE by construction**                                                                | declared coverage gap, once (§5)                                                             |
| `_quarantine/`   | (same bucket) | `market-data-tick-tradfi-prd-central-element-323112`   | not re-probed this run (probed for the sibling raw-tick report, same session)                    | out of scope for THIS pass — see §0                                                          |

`GCP_PROJECT_ID=central-element-323112` set in env; tier via `deployment_env="prd"` explicitly.

**Day-prefix count grew from 884 (07-25) to 1,815 (08-17)** — more than doubled, consistent with continued candle
backfill activity in the intervening 3.5 weeks.

## 2. Index freshness / lock state

Same `_index/` snapshot used for the sibling raw-tick report (single manifest download, reused per single-walk
discipline): `availability_index.parquet` blob updated `2026-08-17T05:26:52Z`; `_index/consolidator.lock` PRESENT at
probe time (`started_at=2026-08-17T05:32:54Z`) — the published parquet predates the lock by ~6 minutes, so this is a
stable snapshot, not a mid-write read (full detail in the sibling raw-tick report §Phase 0).

## 3. Phase 1 — four-surface comparison (candle layer)

### S1 — path (oracle-checked)

20 real objects sampled under `processed_candles/by_date/day=2026-08-07/pipeline_mode=batch_databento/timeframe=15m/`,
spanning both `data_type=ohlcv_1m` chain-bundle writes (`instrument_type=COMBO`, e.g. `venue=CME/underlying=6A/
ticks.parquet`) and `data_type=ohlcv_15m`/`ohlcv_1m` writes now carrying `instrument_type=FUTURE` (e.g.
`venue=CBOE/underlying=VIX/ticks.parquet`, `venue=CME/underlying=AUD/ticks.parquet`) — **every sampled object: zero
violations under BOTH `require_candle_migration_complete=False` and `=True`.**

**This is a material change from 07-25**, which reported: _"this pass did not sample a single-instrument tradfi leaf,
so it does not independently re-confirm the `by_date/` tree is 100% free of non-canonical leaf ids"_ and treated the
`instrument_type=` addition as still `migration_pending`. This run's sample — which DOES include `instrument_type=`
on every sampled path, for both COMBO and FUTURE-labeled bundle types — passing under the **strict** mode as well as
the lenient mode indicates the path migration has progressed to (at least the sampled slice of) completion. **Not a
100% corpus-wide claim** — 20 objects from one day, see coverage gaps (§7).

### S2 — content / schema

Not independently re-sampled this run — declared gap, consistent with the 07-25 report's own scope.

### S3 — manifest (headline finding — RESOLVED)

Fresh full re-read of `_index/availability_index.parquet` (14,457,858 total rows, same download as the raw-tick pass),
filtered `service_name=="market-data-processing-service"`:

```
rows: 6,720,871   (was 73 on 2026-07-25 — a ~92,000x increase)
row_count non-null: 6,720,871 of 6,720,871 (100%, was 61/73 on 07-25)
written_at range: [2026-06-22T05:51:07Z, 2026-08-16T13:54:30Z]
```

**Verdict: RESOLVED.** The 07-25 report's headline finding was "zero candle manifest rows written since the fix
landed" (`written_at` frozen at ≤2026-06-22 across all 4 measured asset_groups). This run measures 6,720,871 rows with
`written_at` current through **yesterday** (2026-08-16), with 100% non-null `row_count` (up from 61/73 = 83.6%). The
candle write path is now calling `record_captured` per shard, consistent with the manifest-writer fix referenced in
`mdps_candle_manifest_population_disconnect_2026_07_25.md` having landed and held for tradfi.

**Not independently cross-checked against a fresh full GCS object count this run** (would require a new whole-corpus
walk, review-blocking per single-walk discipline) — this run reuses the 07-25 P7/P8 figures (7,646,831 total
processed objects, 534,679 live/non-quarantined) as historical context only; the true current live-object count is
likely higher given the day-prefix count more than doubled. See coverage gaps (§7) for the recommended follow-up.

### S4 — catalogue

**UNAVAILABLE by construction**, reported once (no candle catalogue exists for any asset_group — unchanged structural
fact).

## 4. Corpus-scale disposition — REUSED from the 07-25 campaign (not re-walked)

```
P7-processed (2026-07-22/23): 7,646,831 objects
P8-live (by_date/, 2026-07-23): 534,679 objects
Gap (in _quarantine/, unresolvable leaf ids, todo 3): 7,112,152 objects (93.0% of the P7-processed total)
```

**Historical context only** — day-prefix count has grown from 884 to 1,815 since these figures were measured; a fresh
object-count walk (VM-scale, out of this Tier-1 dispatch's scope) would be needed to refresh them.

## 5. Typed findings

| Finding                                   | Type (taxonomy)                                | Scope                | Status                                                                          |
| ------------------------------------------- | ------------------------------------------------- | ----------------------- | ---------------------------------------------------------------------------------- |
| Candle path shape (by_date/ sample)         | n/a (CANONICAL)                                    | 20 sampled objects       | Not a finding for the sampled shape — clean under both oracle modes.               |
| Candle manifest population                  | was `missing_row` (headline, 07-25)                | ~6.72M manifest rows now | **RESOLVED** — see §3 S3.                                                          |
| Quarantined unresolvable leaf ids           | `non_canonical_id` (already tracked)               | ~7,112,152 objects (07-23 figure, not re-measured) | Already tracked (`candle_feature_canonical_path_divergence_2026_07_20.md` todo 3); not re-diagnosed. |
| S4 catalogue absence                        | declared coverage gap                              | whole candle layer       | Unchanged, structural.                                                            |

No new non-canonical-path-inventory entries this run; no delete suggestions.

## 6. Suppressed accepted-exceptions

0 `migration_pending` suppressions needed this run — the sampled shape passed under the STRICT
(`require_candle_migration_complete=True`) mode, so nothing needed the lenient-mode suppression.

## 7. Coverage gaps

- S2/schema not independently re-sampled.
- The `_quarantine/` tree (~7.1M objects, 07-23 figure) not re-probed this run (out of scope, already tracked).
- **The S3 "resolved" verdict is not cross-checked against a fresh GCS object count** — recommend a bounded
  delimiter-descent object-count refresh (not a full walk) to confirm the 6.72M manifest rows are keeping pace with
  the now-1,815-day-prefix corpus, rather than trusting the manifest-row-count trend alone.
- Only 20 objects from ONE day (`2026-08-07`) were oracle-sampled for S1 — this is a spot-check, not a corpus-wide
  claim; the "path migration now complete" verdict is directional, not certified.
- A single-instrument (non-bundle) tradfi candle leaf was not distinctly sampled this run (all 20 sampled objects were
  bundle-grain `ticks.parquet` writes) — this pass does not independently re-confirm flat-per-contract candle leaf
  canonicality beyond the bundle-grain sample.

## 8. Todos

- [ ] **P3 [DATA]** Refresh the P7/P8 corpus-scale disposition figures (day-prefix count has more than doubled since
      07-25, 884→1,815) — a bounded delimiter-descent object-count, not a full walk, would be sufficient to confirm
      the manifest-row growth (73→6.72M) is proportionate to the on-disk object growth rather than over- or
      under-representing it. (repo: market-tick-data-service or deployment-service)
- [ ] **P3 [DATA]** Sample at least one flat-per-contract (non-bundle) tradfi candle leaf in a future reconciliation
      pass — this run's S1 sample was 100% bundle-grain (`ticks.parquet`); the flat-leaf population's canonicality is
      not independently confirmed by this run. (repo: unified-trading-pm, reconciliation skill)
