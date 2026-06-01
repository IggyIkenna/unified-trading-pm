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
  - _index comparison 2026-06-01 (prediction canonical is the LEAST complete:
      2,039 legacy-only captured cells, only 783 overlap)
master: defi_manifest_canonicalisation_2026_06_01.md (cross-plan canonical-SSOT coordinator)
---

# Prediction manifest + data canonicalisation (L3 owner for prediction)

> **🔎 CROSS-AG FINDING from defi (2026-06-01) — CHECK THE SAME HERE**: defi's CF data-state audit found the legacy
> `_index` **100% NOT v9** (v4/5/6/8 spread), with **no `source`/`asset_group`/`pipeline_mode` COLUMNS** — a FULL
> re-canonicalisation, not the headline cell-count (same shape as the cefi reference incident). **CF-2 gotcha**: the
> migrate tool emitted `asset_group=` to the object PATH but did NOT stamp it as a parquet COLUMN → the rebuilt `_index`
> lacked the column. Fix = stamp `asset_group` (+ `schema_version`/`source`/`pipeline_mode`) as COLUMNS, never rely on
> the consolidator deriving them from the path. **Action**: run a CF data-state audit on prediction's `_index` as
> pre-flight + verify (reusable: `market-tick-data-service/market_tick_data_service/scripts/audit_canonical_form.py` or
> `plans/audit/results/cf_manifest_audit_2026_06_01.py`) — trust the real data-state, never the v9 constant. If the same
> debt shows → fix fully in-walk (scope is a prior, not a ceiling). SSOT:
> `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md`.

> **MASTER**: `defi_manifest_canonicalisation_2026_06_01.md` §MASTER (L3, prediction lane). This plan is the prediction
> analogue of `defi_manifest`'s §C single-walk. **Single-walk discipline (HARD RULE)**: one bundled walk on the
> prediction `_index` — bundle every transform (env-split, `asset_group=`, `pipeline_mode=` partition, v9, **`source`
> stamp** = the data-source API, typed empty-reason). Do NOT open a second walk; `pipeline_mode_partition_migration` +
> `data_source_provenance` ride THIS walk.

## Why this exists — prediction is the LEAST-complete canonical (decommission data-loss risk)

The 2026-06-01 `_index` comparison (legacy `market-data-tick-prediction-…` vs canonical `market-data-tick-pred-prd-…`):

| metric                                         | value                                                                                 |
| ---------------------------------------------- | ------------------------------------------------------------------------------------- |
| captured legacy CELLS `(date,venue,data_type)` | 2,822                                                                                 |
| canonical CELLS                                | 3,086                                                                                 |
| overlap                                        | **783**                                                                               |
| legacy-only CELLS (canonical MISSING)          | **2,039**                                                                             |
| legacy-only by data_type                       | `prediction_canonical_question_group` 289 · `ohlcv_15m`/`15s`/`1d`/`1h`/`1m` 247 each |

So **most historical POLYMARKET prediction data is in legacy ONLY** — deleting the legacy bucket now = data loss. This
plan migrates it into the canonical `market-data-tick-pred-prd-central-element-323112` SSOT before L6 decommission.
Legacy layout (per 2026-06-01 audit): `raw_tick_data/` + `processed_candles/` (NO defi-style per-type prefixes).

## Sequencing — canonical migration is a GATE before any prediction backfill (inherits the master HARD RULE)

No prediction backfill / relaunch of `mdps-prediction-2025` until this walk is C-GREEN (per `bucket_name_ssot…` Phase
4 + master L3-gates-L5). L0 tarball-prune blocker (`issues/pinned_tarball_prune_breaks_vm_deploys_2026_06_01.md`) must
be fixed first if run on a VM.

## Canonical target form (prediction)

| Dimension       | Legacy                                                      | Canonical                                                                                                                                                                                                                                                                                                                      |
| --------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Bucket          | `market-data-tick-prediction-{project}` (long-form, no env) | `market-data-tick-pred-prd-{project}` (short token `pred` + env)                                                                                                                                                                                                                                                               |
| asset-group key | `category=prediction`                                       | `asset_group=prediction`                                                                                                                                                                                                                                                                                                       |
| pipeline_mode   | absent in path                                              | `pipeline_mode=` hive partition (`batch_polymarket_clob`/`batch_polymarket_gamma_api`)                                                                                                                                                                                                                                         |
| schema_version  | legacy spread                                               | v9                                                                                                                                                                                                                                                                                                                             |
| source          | blank `""` today                                            | `source` COLUMN stamped = the data-source API (`polymarket_clob`/`polymarket_gamma_api`/`kalshi_*`) on every cell — HARD, swap-resilient per `data_source_provenance` Phase 6. **Venue ≠ source**: Polymarket/Kalshi stay VENUES (cross-venue dispersion is feature-layer); each venue's cell still stamps its own API source. |

## Phased execution

### P0 — pre-walk audit + scope

> **Scope is a prior, not a ceiling — fix-fully-autonomously (HARD RULE)**: the headline ("2,039 legacy-only") is a
> coarse prior. Read DATA-STATE. If the audit finds MORE form debt than implied (e.g. cefi turned out 100% v8 / no
> source / no asset_group / blank pipeline_mode — a full re-canonicalisation), fix ALL of it in this one walk — NOT
> descoped, deferred, post-cutover, or `BLOCKED-OPERATOR-DECISION` (a data-state gap is not a design fork). SSOT:
> `canonical_form_cross_service_audit_checklist.md` § "Audit scope is a PRIOR, not a ceiling".

- [x] ✅ [DATA] P0. Legacy→canonical diff (slot-4 tool, 2026-06-01): **2,039 legacy-only cells confirmed** (legacy 2,822
      · canonical 805 · overlap 783) — matches the headline; mostly `POLYMARKET ohlcv_*` + `prediction_canonical_question_group`
      from 2025-03-14 on. Per-data_type object counts resolved in the C0 copy walk (idempotent). Data-loss risk on delete
      → these MUST land in canonical before L6.
- [x] ✅ [DATA] P0. Canonical `pred-prd` `_index` DATA-STATE: **100% v8** (0/16,812 v9 — CF-1 RED); **`asset_group` col
      present** (CF-2 rows GREEN) but **object PATHS still `category=prediction`** + **`data_source=POLYMARKET_CLOB` in
      path** (CF-2 paths RED, CF-4 source-in-path); **`pipeline_mode` blank 0/16,812 + no path segment** (CF-3 RED); **no
      `source` column** (CF-4 RED); **no `available_at` column** (CF-8 RED — only `written_at`); CF-5 typed GREEN
      (`EXPECTED_PRE_VENUE_LAUNCH` 2,280 / `SOURCE_RETURNED_ZERO` 41). **CF-7 drift**: venue includes `UNKNOWN` + blank
      `''`; data_type includes blank `''` + `prediction_trades`/`trades` — diagnose/relabel in the walk. Path sample:
      `raw_tick_data/by_date/day=2025-03-14/category=prediction/data_source=POLYMARKET_CLOB/venue=POLYMARKET`.

### C — single-walk migration (legacy `prediction` → canonical `pred-prd`)

- [ ] [DATA] P0. **Phase 0 — layout audit (MANDATORY, blocking — slot-2 DeFi lesson 2026-06-01)**: enumerate ALL
      top-level trees + nested layouts in the prediction source + canonical buckets before the walk (`raw_tick_data/`,
      `processed_candles/`, the 6-dimension `day=/category=/data_source=/venue=/…/market_category=/…` polymarket layout);
      classify duplicate (keep freshest) vs complementary (migrate all → canonical v9). The existing
      `rebuild_prediction_manifest.py` (ManifestWriter rebuild) is the manifest-side template. Cover every in-scope
      layout or the walk is incomplete (review-blocking). SSOT: `plans/audit/results/cf_data_state_audit_slot4_2026_06_01.md` § grounded recipe Phase 0.

> **Migration-script performance contract (HARD — codified 2026-06-01, defi C0 lesson)**: the walk script MUST be
> parallel (`ThreadPoolExecutor` — GCS I/O releases the GIL → 5–10×; a bare `for obj` loop is review-blocking) + wire
> `--workers`/`--start-date`/`--end-date` (date-shardable across VMs — no dead args) + `gcs_copy_object` for path-only
> moves (server-side ~250×) / download+transform+upload only for content changes + unbuffered progress logging
> (`python -u`, counter every ~1000) + per-object `try/except…continue` isolation + idempotent re-runs. SSOT:
> `codex/05-infrastructure/gcs-object-operations.md` § "Migration-script performance contract".

- [ ] [DATA] P0. C0 ONE bundled walk: copy legacy `raw_tick_data/` + `processed_candles/` objects → canonical `pred-prd`
      at the canonical path (env-tier + `asset_group=` + `pipeline_mode=` partition); rewrite manifest rows to v9; typed
      empty-reasons. **`category=`→`asset_group=` lands on BOTH the object PATHS and the manifest `_index` ROWS in this
      walk** (CODE side — writers emit `asset_group=` — already shipped via archived
      `venue_axis_asset_group_vocabulary_2026_04_25`; this is historical data+manifest only). Server-side
      `gcs_copy_object` (layout-aware: prediction = `raw_tick_data/`/`processed_candles/`). RUN ON A VM via
      `VM_TASK=canonical-migration` (gated on L0 tarball-prune fix) OR locally if object count is small (P0 audit
      decides).
- [ ] [DATA] P0. C-pipeline_mode RIDER: the `pipeline_mode=` partition for prediction lands in THIS walk (satisfies
      `pipeline_mode_partition_migration_2026_06_01.md` for prediction — do NOT run it separately).
- [ ] [DATA] P1. C-source RIDER: stamp `source` = the data-source API (`polymarket_clob` / `polymarket_gamma_api` /
      `kalshi_*`) on every prediction cell in THIS walk (path/pipeline*mode → `source` column), re-consolidate into the
      `_index` — HARD, swap-resilient (a future Polymarket data-provider change stays distinguishable). Closes
      `data_source_provenance` Phase 6 prediction. **Venue ≠ source invariant preserved**: Polymarket/Kalshi remain
      VENUES (cross-venue dispersion is a feature-layer concern, not a source merge); when Kalshi lands it is a venue
      addition AND its cells stamp `kalshi*\*` as source. Do NOT open a separate prediction source walk.

### Verify + handoff to decommission

- [ ] [DATA] P0. Post-walk: re-run the `(date,venue,data_type)` comparison → **legacy-only CELLS = 0**; canonical
      `_index` all v9; `pipeline_mode` non-null; **`source` populated on every cell (HARD — zero blank; the API source
      per venue) — closes `data_source_provenance` Phase 6 prediction**. This is the C-GREEN signal `bucket_name_ssot…`
      Phase 6/7 waits on for the prediction legacy bucket decommission.

## Success criteria

- 0 legacy-only prediction cells (canonical holds all historical POLYMARKET data + question-groups).
- Canonical `pred-prd` `_index` = v9 + `pipeline_mode=` partition present + **`source` stamped on every cell (zero blank
  — HARD; the API source per venue, swap-resilient)**.
- `mdps-prediction-2025` relaunch unblocked (writes canonical-only).
- Hands C-GREEN to `bucket_name_ssot…` L6 → legacy `market-data-tick-prediction-…` deletable.

## Codex SSOTs

- `codex/02-data/availability-manifest-and-data-status.md` — prediction canonical form.
