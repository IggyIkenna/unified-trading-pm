---
title: "Prediction manifest + data canonicalisation (legacy→canonical, single-walk) — L3 owner for prediction"
created: 2026-06-01
author: ikenna
parent_epic: epics/mtds_mdps_master.md
assigned_vm: vm-prediction
status: active
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
locked_by: live-defi-rollout
locked_since: 2026-06-01
source:
  - bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md (L3 ordering — prediction had NO owner)
  - _index comparison 2026-06-01 (prediction canonical is the LEAST complete: 2,039 legacy-only captured cells, only 783 overlap)
master: defi_manifest_canonicalisation_2026_06_01.md (cross-plan canonical-SSOT coordinator)
---

# Prediction manifest + data canonicalisation (L3 owner for prediction)

> **MASTER**: `defi_manifest_canonicalisation_2026_06_01.md` §MASTER (L3, prediction lane). This plan is the prediction
> analogue of `defi_manifest`'s §C single-walk. **Single-walk discipline (HARD RULE)**: one bundled walk on the
> prediction `_index` — bundle every transform (env-split, `asset_group=`, `pipeline_mode=` partition, v9, source-N/A,
> typed empty-reason). Do NOT open a second walk; `pipeline_mode_partition_migration` + `data_source_provenance` ride
> THIS walk.

## Why this exists — prediction is the LEAST-complete canonical (decommission data-loss risk)

The 2026-06-01 `_index` comparison (legacy `market-data-tick-prediction-…` vs canonical `market-data-tick-pred-prd-…`):

| metric | value |
| --- | --- |
| captured legacy CELLS `(date,venue,data_type)` | 2,822 |
| canonical CELLS | 3,086 |
| overlap | **783** |
| legacy-only CELLS (canonical MISSING) | **2,039** |
| legacy-only by data_type | `prediction_canonical_question_group` 289 · `ohlcv_15m`/`15s`/`1d`/`1h`/`1m` 247 each |

So **most historical POLYMARKET prediction data is in legacy ONLY** — deleting the legacy bucket now = data loss. This
plan migrates it into the canonical `market-data-tick-pred-prd-central-element-323112` SSOT before L6 decommission.
Legacy layout (per 2026-06-01 audit): `raw_tick_data/` + `processed_candles/` (NO defi-style per-type prefixes).

## Sequencing — canonical migration is a GATE before any prediction backfill (inherits the master HARD RULE)

No prediction backfill / relaunch of `mdps-prediction-2025` until this walk is C-GREEN (per
`bucket_name_ssot…` Phase 4 + master L3-gates-L5). L0 tarball-prune blocker
(`issues/pinned_tarball_prune_breaks_vm_deploys_2026_06_01.md`) must be fixed first if run on a VM.

## Canonical target form (prediction)

| Dimension | Legacy | Canonical |
| --- | --- | --- |
| Bucket | `market-data-tick-prediction-{project}` (long-form, no env) | `market-data-tick-pred-prd-{project}` (short token `pred` + env) |
| asset-group key | `category=prediction` | `asset_group=prediction` |
| pipeline_mode | absent in path | `pipeline_mode=` hive partition (`batch_polymarket_clob`/`batch_polymarket_gamma_api`) |
| schema_version | legacy spread | v9 |
| source | N/A (prediction venue ≠ source; document N/A per `data_source_provenance`) | — |

## Phased execution

### P0 — pre-walk audit + scope
- [ ] [DATA] P0. Confirm the 2,039 legacy-only cells' underlying DATA objects exist in legacy (not phantom manifest
      rows) and are genuinely absent from canonical — sample per data_type (`prediction_canonical_question_group`,
      `ohlcv_*`). Record the real object count to migrate.
- [ ] [DATA] P0. Read the legacy `_index` `schema_version` distribution + confirm canonical `pred-prd` current version
      (the migration target is v9).

### C — single-walk migration (legacy `prediction` → canonical `pred-prd`)
- [ ] [DATA] P0. C0 ONE bundled walk: copy legacy `raw_tick_data/` + `processed_candles/` objects → canonical
      `pred-prd` at the canonical path (env-tier + `asset_group=` + `pipeline_mode=` partition); rewrite manifest rows to
      v9; typed empty-reasons. Server-side `gcs_copy_object` (layout-aware: prediction = `raw_tick_data/`/`processed_candles/`).
      RUN ON A VM via `VM_TASK=canonical-migration` (gated on L0 tarball-prune fix) OR locally if object count is small
      (P0 audit decides).
- [ ] [DATA] P0. C-pipeline_mode RIDER: the `pipeline_mode=` partition for prediction lands in THIS walk (satisfies
      `pipeline_mode_partition_migration_2026_06_01.md` for prediction — do NOT run it separately).
- [ ] [DOCS] P1. Document prediction `source` = N/A (venue ≠ source) per `data_source_provenance` PREDICTION todo.

### Verify + handoff to decommission
- [ ] [DATA] P0. Post-walk: re-run the `(date,venue,data_type)` comparison → **legacy-only CELLS = 0**; canonical
      `_index` all v9; `pipeline_mode` non-null. This is the C-GREEN signal `bucket_name_ssot…` Phase 6/7 waits on for
      the prediction legacy bucket decommission.

## Success criteria
- 0 legacy-only prediction cells (canonical holds all historical POLYMARKET data + question-groups).
- Canonical `pred-prd` `_index` = v9 + `pipeline_mode=` partition present.
- `mdps-prediction-2025` relaunch unblocked (writes canonical-only).
- Hands C-GREEN to `bucket_name_ssot…` L6 → legacy `market-data-tick-prediction-…` deletable.

## Codex SSOTs
- `codex/02-data/availability-manifest-and-data-status.md` — prediction canonical form.
