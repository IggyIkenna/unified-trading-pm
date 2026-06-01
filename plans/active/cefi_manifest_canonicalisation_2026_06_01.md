---
title: "CeFi legacy gap-fill + manifest canonicalisation (single-walk) — L3 owner for cefi"
created: 2026-06-01
author: ikenna
parent_epic: epics/mtds_mdps_master.md
assigned_vm: vm-cefi
status: active
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
locked_by: live-defi-rollout
locked_since: 2026-06-01
source:
  - bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md (L3 ordering — cefi had NO owner)
  - _index comparison 2026-06-01 (cefi canonical ~complete: 838 legacy-only captured cells out of 91,602)
master: defi_manifest_canonicalisation_2026_06_01.md (cross-plan canonical-SSOT coordinator)
---

# CeFi legacy gap-fill + manifest canonicalisation (L3 owner for cefi)

> **MASTER**: `defi_manifest_canonicalisation_2026_06_01.md` §MASTER (L3, cefi lane). **Single-walk discipline (HARD
> RULE)**: ONE bundled walk on the cefi `_index` — bundle the 838-cell gap-fill + `pipeline_mode=` partition + v9; do
> NOT open a second walk. `pipeline_mode_partition_migration` + `data_source_provenance` (cefi) ride THIS walk.

## Why this exists — cefi canonical is ~complete, with a small recent gap

The 2026-06-01 `_index` comparison (legacy `market-data-tick-cefi-…` vs canonical `market-data-tick-cefi-prd-…`):

| metric                                         | value                                                                                                                        |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| captured legacy CELLS `(date,venue,data_type)` | 91,602                                                                                                                       |
| canonical CELLS                                | 142,893 (canonical is AHEAD overall)                                                                                         |
| overlap                                        | 90,764                                                                                                                       |
| legacy-only CELLS (canonical MISSING)          | **838**                                                                                                                      |
| legacy-only examples                           | `(2026-03-21, BINANCE-SPOT, book_snapshot_5)`, `(2026-05-14, UPBIT, book_snapshot_5)`, `(2026-05-20, COINBASE-SPOT, trades)` |
| legacy-only by data_type                       | `book_snapshot_5` 363 · `trades` 336 · `derivative_ticker` 83 · `liquidations` 47 · `ohlcv_15s` 3 · `ohlcv_1m` 2             |

So cefi canonical is overall MORE complete than legacy (142k vs 91k cells), but **838 recent cells (2026-03→05,
BINANCE/UPBIT/COINBASE) exist in legacy only** — likely written to legacy right before the writers were drained
2026-06-01. These must land in canonical before L6 deletes the legacy bucket. Legacy layout (2026-06-01 audit):
`raw_tick_data/` (NO `by_date/` sub-tree — different from tradfi) + `processed_candles/`.

## Sequencing — gate before cefi backfill (inherits master HARD RULE)

No cefi backfill until this walk is C-GREEN. L0 tarball-prune blocker
(`issues/pinned_tarball_prune_breaks_vm_deploys_2026_06_01.md`) must be fixed first if run on a VM. (The drained
`mdps-backfill-cefi-main-test` already self-terminated; no live cefi writer — relaunch is gated on C-GREEN.)

## Canonical target form (cefi)

| Dimension       | Legacy                                     | Canonical                                                                             |
| --------------- | ------------------------------------------ | ------------------------------------------------------------------------------------- |
| Bucket          | `market-data-tick-cefi-{project}` (no env) | `market-data-tick-cefi-prd-{project}`                                                 |
| asset-group key | `category=cefi`                            | `asset_group=cefi`                                                                    |
| pipeline_mode   | absent in path                             | `pipeline_mode=` partition (`batch_tardis`/`batch_hyperliquid_rest`/`live_websocket`) |
| schema_version  | legacy spread                              | v9                                                                                    |
| source          | (per `data_source_provenance` cefi)        | `tardis` / `<venue>` multi-source                                                     |

## Phased execution

### P0 — audit

- [ ] [DATA] P0. Confirm the 838 legacy-only cells' DATA objects exist in legacy + are genuinely absent from canonical
      (sample per data_type, esp. `book_snapshot_5`/`trades`). Record exact object count (likely small — recent only).
- [ ] [DATA] P0. Read legacy `_index` `schema_version` distribution + canonical `cefi-prd` current version (target v9).

### C — single-walk (gap-fill + canonicalisation)

- [ ] [DATA] P0. C0 ONE bundled walk: copy the 838-cell legacy DATA objects (`raw_tick_data/` + `processed_candles/`,
      layout-aware — cefi has NO `by_date/`) → canonical `cefi-prd` at canonical path (env-tier + `asset_group=` +
      `pipeline_mode=` partition); write/relabel the matching manifest rows to v9; typed empty-reasons.
      **`category=`→`asset_group=` lands on BOTH the object PATHS and the manifest `_index` ROWS in this walk** (CODE
      side — writers emit `asset_group=` — already shipped via archived `venue_axis_asset_group_vocabulary_2026_04_25`;
      this is historical data+manifest only). Server-side `gcs_copy_object`. Small scope → may run LOCALLY (P0 audit
      decides) — avoids the L0 VM-tarball blocker entirely.
- [ ] [DATA] P0. C-pipeline_mode RIDER: `pipeline_mode=` partition for cefi lands in THIS walk (satisfies
      `pipeline_mode_partition_migration` for cefi).
- [ ] [DATA] P1. C-source RIDER: `data_source_provenance` cefi `source` column lands here (multi-source tardis/venue).

### Verify + handoff

- [ ] [DATA] P0. Post-walk: re-run `(date,venue,data_type)` comparison → **legacy-only CELLS = 0**; canonical v9;
      `pipeline_mode` non-null; **`source` populated on every cell (HARD — zero blank; `source="tardis"` today, ready
      for a future Tardis swap/2nd source) — closes `data_source_provenance` cefi Phase 3**. C-GREEN signal for
      `bucket_name_ssot…` Phase 6/7 cefi legacy bucket decommission.

## Success criteria

- 0 legacy-only cefi cells; canonical `cefi-prd` v9 + `pipeline_mode=` partition + **`source` populated on every cell
  (zero blank — HARD)**.
- Hands C-GREEN to `bucket_name_ssot…` L6 → legacy `market-data-tick-cefi-…` deletable.

## Codex SSOTs

- `codex/02-data/availability-manifest-and-data-status.md` — cefi canonical form.
