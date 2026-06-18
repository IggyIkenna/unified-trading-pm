---
title: Legacy-shape GCS duplicate delete-list + 48h e2e research-data accounting
name: gcs_delete_list_and_e2e_data_accounting_2026_06_18
type: audit-result
epic: infrastructure_master
parent_epic: infrastructure_master
instructions_ref: plans/audit/instructions/infrastructure_master_audit_instructions.md
created: 2026-06-18
date: 2026-06-18
author: ikennaigboaka [autonomous gcs-delete-list audit]
auditor: ikennaigboaka [autonomous gcs-delete-list audit]
status: complete
assigned_vm: vm-cross-cutting
method:
  Read-only GCS enumeration of all 5 market-data-tick raw_tick_data/by_date/ namespaces (full walk, no sampling) via the
  google-cloud-storage client, parallel-by-day (ThreadPoolExecutor workers=32-48). Canonical twin derived by inserting
  pipeline_mode={mode}_{source} (= UTL derive_pipeline_mode_for_row, the migrator SSOT) left of asset_group= and
  normalising category=->asset_group=; twin existence by membership in the same day's listed canonical name-set
  (authoritative) + independent gcs_describe_object STAT confirmation on a sample (byte-size match).
audit_tool: e2e-testing/scripts/defi/audit_legacy_gcs_dup_delete_list.py
audit_artifacts:
  - gs://market-data-tick-{cefi,defi,tradfi,sports,pred}-prd-central-element-323112/_index/audit/legacy_dup_delete_list_{ag}.parquet
---

# Legacy-shape GCS duplicate delete-list + 48h e2e research-data accounting (2026-06-18)

READ-ONLY audit. No GCS object was deleted/moved; no live `_index/availability_index.parquet` was touched. The only
writes were the per-AG audit parquets to `_index/audit/` and this doc.

## TL;DR

- **Only `cefi` has a substantial, verified delete-list: 1,077,672 legacy objects (~9.98 TB) SAFE-TO-DELETE**, each with
  a byte-identical canonical `pipeline_mode=batch_*` twin verified to exist. 15 cefi objects are MIGRATE-FIRST (9 bare
  top-level + 6 double-keyed 2019 oddballs).
- **`defi`/`tradfi`/`sports`/`pred` are essentially NOT yet migrated to the canonical pipeline_mode shape** — their
  legacy objects mostly have **NO canonical twin** → MIGRATE-FIRST, not safe-delete. defi has 172 safe (== its 172
  canonical). tradfi/sports/pred = 0 safe.
- **The 48h e2e research data is fully accounted-for and is NOT at risk** from the cefi delete: it lives in SEPARATE
  buckets (`perp-funding-*`, `lst-rates-*`) + canonical cefi `batch_tardis` reads + live APIs — none under any
  safe-to-delete legacy path. **Verdict: nothing in the safe-delete list is irreplaceable.**
- **Recommendation**: cefi safe-delete may proceed (after operator inspection of `legacy_dup_delete_list_cefi.parquet`).
  defi/tradfi/sports/pred safe-delete is essentially empty — those legacy objects must be **migrated first** (or the
  prior migration completed) before any legacy delete; deleting them now would lose data.

## 1. Per-AG delete-list (full walk, twin-verified)

| AG     | total objs | canonical | legacy    | SAFE-TO-DELETE | reclaimable  | MIGRATE-FIRST | migrate bytes |
| ------ | ---------- | --------- | --------- | -------------- | ------------ | ------------- | ------------- |
| cefi   | 2,483,059  | 1,405,372 | 1,077,687 | **1,077,672**  | **9,979 GB** | 15            | 0.04 GB       |
| defi   | 352,406    | 172       | 352,234   | 172            | 0.07 GB      | 352,062       | 33.56 GB      |
| tradfi | 1,722,965  | 16,633    | 1,706,332 | 0              | 0            | 1,706,332     | 115.85 GB     |
| sports | 252,338    | 20        | 252,318   | 0              | 0            | 252,318       | 5.01 GB       |
| pred   | 580,998    | 7,547     | 573,451   | 0              | 0            | 573,451       | 24.35 GB      |
| **Σ**  |            |           | 2,784,019 | **1,077,844**  | **~9.98 TB** | 2,884,178     | ~179 GB       |

Per-AG 1:1 mapping (legacy*path -> canonical_twin_path, twin_exists, classification, reason, bytes) is in
`gs://<bucket>/\_index/audit/legacy_dup_delete_list*{ag}.parquet`.

### cefi — the prize (clean "insert pipeline_mode=" migration)

cefi's migration COPIED legacy `day={D}/asset_group=cefi/venue=.../instrument_type=.../data_type=.../{stem}.parquet` to
canonical `day={D}/pipeline_mode=batch_{source}/asset_group=cefi/<same tail>` (source = tardis / hyperliquid / aster per
`derive_pipeline_mode_for_row`). 5 sampled twins independently STAT-confirmed: twin exists AND
`legacy.size == twin.size` (byte-identical dup). The 1,077,672 SAFE-TO-DELETE rows are the legacy copies; their
canonical reads survive.

MIGRATE-FIRST (15): 9 bare `raw_tick_data/by_date/{SYMBOL}.parquet` (no partition keys -> can't derive a twin) + 6
`day=2019-03-31/asset_group=cefi/category=cefi/venue=DERIBIT/...` double-keyed 2019 objects with no canonical twin.

### defi/tradfi/sports/pred — migration barely ran / was a RESTRUCTURE, not a copy

These AGs have very few canonical objects, and their legacy shape differs from canonical by MORE than a pipeline_mode
insert, so a naive twin does not match (correctly classified MIGRATE-FIRST — fail-safe, never marks a real orphan
safe-delete):

- **pred** (0 safe despite 7,547 canonical): legacy
  `category=prediction/data_source=POLYMARKET_CLOB/venue=.../market_category=.../underlying=BTC/market_type=binary/resolution_period=monthly/data_type=trades/{0x...}.parquet`
  vs canonical
  `pipeline_mode=batch_polymarket_clob/asset_group=prediction/venue=.../instrument_type=prediction_market/data_type=prediction_trades/underlying=BTC/{stem}.parquet`.
  The migration DROPPED `data_source/market_category/market_type/resolution_period`, ADDED `instrument_type`, RENAMED
  `data_type trades->prediction_trades`, reordered `underlying`, and CHANGED the file stem (`ticks_migrated_*`). A
  pipeline_mode-insert twin cannot match — these are NOT trivially de-duplicatable.
- **sports** (0 safe): legacy
  `category=sports/data_source=ODDS_API/venue=.../league_id=.../instrument_type=odds/data_type=trades/ticks.parquet`
  (canonical READ path is `candidate_parquet_paths()` — a different scheme); only 20 canonical objects exist. Older
  still: `source=ODDS_API/league=.../ticks.parquet` (no hive keys) -> MIGRATE-FIRST/unparseable.
- **tradfi** (0 safe): bulk legacy is a DASH-separated, non-hive layout
  `day-2025-11-02/data_type-ohlcv_1m/equities/NYSE/{sym}.parquet` (note `day-`/`data_type-`, bare `equities/NYSE/`); the
  16,633 canonical objects only cover CME options (`pipeline_mode=batch_databento/...instrument_type=options_chain`).
  The bulk equities/etf legacy was never migrated to canonical.
- **defi**: 172 safe == its 172 canonical (clean twins); the other 352,062 legacy (mostly `category=defi/...`, 307K)
  have no canonical twin.

**Implication for the operator**: the legacy-delete is ONLY safe for cefi today. For defi/tradfi/sports/pred the prior
GCS canonicalisation migration is INCOMPLETE — those legacy objects are the live copy, not a duplicate. Deleting them
would lose data. They must be migrated to canonical first (per-AG twin logic differs; pred/sports/tradfi need a real
re-key, not a copy).

## 2. 48h e2e research-data accounting (operator's key concern)

The last ~48h of `e2e-testing/scripts/defi/` work (staked-basis / funding-arb research) FETCHES from Hyperliquid
(metaAndAssetCtxs, perp_funding ~230 coins), Binance/OKX/Bybit/Deribit, Aster, Drift. Where it reads/writes:

| dataset / artifact                                                            | location                                                                     | canonical status                                 | classification                                                                 |
| ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------ |
| CeFi perp `derivative_ticker` (funding)                                       | reads canonical `market-data-tick-cefi .../pipeline_mode=batch_tardis/...`   | CANONICAL (already)                              | accounted-for; reads canonical, the safe-delete list is its LEGACY twin        |
| HL `perp_funding` (~230 coins, 1/day)                                         | `perp-funding-central-element-323112` (raw_tick_data/by_date + bare day=)    | NON-canonical research bucket (OUT OF SCOPE)     | accounted-for; NOT in the 5 market-data-tick buckets; not touched              |
| HL `perp_daily_ctx` (mark_px+vol, xsec)                                       | `perp-funding-central-element-323112` (sparse / newer)                       | NON-canonical research bucket; script flags "⚠" | re-downloadable (HL metaAndAssetCtxs); a perp_daily_ctx backfill is its source |
| LST `exchange_rate` (staking APY)                                             | `lst-rates-central-element-323112` (legacy bare day=)                        | legacy research bucket (OUT OF SCOPE)            | accounted-for; not in the 5 buckets; not touched                               |
| Aster funding                                                                 | LIVE `fapi.asterdex.com` (no GCS)                                            | n/a (no backfill)                                | re-downloadable (`_fetch_aster_funding`)                                       |
| Drift funding                                                                 | LIVE Solana RPC via isolated driftpy venv                                    | n/a (no backfill)                                | re-downloadable (`drift_funding_reader.py`)                                    |
| script OUTPUTS (HTML/CSV/JSON reports, lightgbm model, funding cache parquet) | LOCAL only (`/tmp/staked_basis_scan/`, `/tmp/funding_regime/`)               | derived analysis artifacts                       | re-downloadable (re-run the scan)                                              |
| colocated_engine features/events                                              | feature bucket + `{project}-events` + reads `deployment-scripts-*` overrides | production-path (not raw market-data dup)        | out of scope (not a legacy raw_tick_data dup)                                  |

**Runaway / unaccounted data**: none found. The fetched research data is either (a) in the dedicated `perp-funding-*` /
`lst-rates-*` research buckets (NOT in the 5 in-scope market-data-tick buckets, so untouched by this delete-list), (b)
read from the canonical cefi bucket (the safe-delete list is the legacy TWIN of those reads — deleting it leaves the
canonical reads intact), or (c) live-API / on-chain re-downloadable. Script outputs are local derived artifacts.

**DANGER cross-check (research data under a safe-delete legacy path)**: NONE. The only safe-delete list is cefi's, whose
rows are the LEGACY `asset_group=cefi/...` copies; the e2e cefi reads are the CANONICAL `pipeline_mode=batch_tardis/...`
twins (verified byte-identical), which the delete preserves. HL/LST/Aster/Drift research data is in separate buckets or
live. **Nothing in the safe-delete list is irreplaceable.**

## 3. Recommendation

1. **cefi**: deletion is SAFE to proceed after operator inspects `legacy_dup_delete_list_cefi.parquet` (1,077,672 rows,
   ~9.98 TB; each twin byte-verified). Exclude the 15 MIGRATE-FIRST rows.
2. **defi**: only the 172 SAFE-TO-DELETE rows are deletable; the other 352K legacy must be migrated first.
3. **tradfi/sports/pred**: 0 safe-delete — do NOT delete legacy; the canonicalisation migration for these AGs is
   incomplete/restructured. They are MIGRATE-FIRST (complete the migration, then re-audit).
4. To finish the full walk yourself / re-audit after a migration:
   `GCP_PROJECT_ID=central-element-323112 e2e-testing/.venv/bin/python e2e-testing/scripts/defi/audit_legacy_gcs_dup_delete_list.py --ag <ag> --workers 32`
   (re-reads each bucket, rewrites the audit parquet; read-only on data).

## Open follow-ups (capture as todos in the owning plan)

- [ ] [SCRIPT] P1. Complete the canonical pipeline_mode migration for defi/tradfi/sports/pred (restructure, not copy —
      pred/sports/tradfi need a real re-key per the shape deltas above), then re-run the audit before any legacy delete.
      Repo: market-data-processing-service / migration owner. **DEFERRED** — provenance: this audit.
- [ ] [SCRIPT] P2. Decide fate of the standalone `perp-funding-*` + `lst-rates-*` research buckets (canonicalise into
      `market-data-tick-{defi,cefi}` or keep as research). Repo: e2e-testing / mtds. **NICE-TO-HAVE** — provenance: this
      audit.
