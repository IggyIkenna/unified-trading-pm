---
doc_type: plan
title: Data-source provenance enforcement — all asset groups (split from M-1)
summary: >-
  Extracted 2026-07-24 from data_completion_to_100_all_ag_2026_06_21.md (M-1) per the plan line-cap remediation
  (plans/active/issues/plan_line_cap_remediation_2026_07_23.md, bucket-(d) split, operator-approved). This is the
  still-inline residual of the already-archived `data_source_provenance_all_asset_groups_2026_06_01.md` (source column +
  SOURCE_PRIORITY enforcement across cefi/defi/tradfi/sports/prediction), migrated VERBATIM — no scope added, dropped,
  or reworded. M-1 remains the coordinator hub for cross-cutting work and owns the shared Progress Log.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, alerting-service, client-reporting-api, deployment-api, deployment-service, deployment-ui]
scope: [engineer, admin]
tags: [backfill, manifest, source-provenance, data-completion, data-correctness]
related:
  [
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
parent_epic: mtds_mdps_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
last_updated: 2026-07-24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  data_completion_to_100_all_ag_2026_06_21 (M-1) -- extracted 2026-07-24, plan line-cap remediation
  (plans/active/issues/plan_line_cap_remediation_2026_07_23.md) bucket-(d) split, operator-approved.
drift_direction: advance-code
---

# Data-source provenance enforcement — all asset groups

> **Split from M-1 on 2026-07-24** (`data_completion_to_100_all_ag_2026_06_21.md`, plan line-cap remediation,
> `plans/active/issues/plan_line_cap_remediation_2026_07_23.md` bucket-(d) split, operator-approved). This plan carries
> M-1's still-inline `data_source_provenance_all_asset_groups_2026_06_01.md` fold-in residual **verbatim**; M-1 stays
> the coordinator hub (measured snapshot, per-AG launch matrix, cross-cutting scope, shared Progress Log).
>
> **Read M-1 first** for the program-level snapshot + launch matrix. This plan is the `source` column /
> `SOURCE_PRIORITY` enforcement tail specifically (write-path gate, historical backfill, read-path resolver, per all
> five asset groups).

### From `data_source_provenance_all_asset_groups_2026_06_01.md` (archived 2026-07-13 -- Data-source provenance enforced across all asset groups (source column + SOURCE_PRIORITY))

- [ ] [SCRIPT] P1. Write `backfill_defi_source_column.py` (copy tradfi template) — stamps the known historical source
      **per data_type** (most defi → `onchain_subgraph`; `oracle_prices` → resolve pyth vs chainlink from the existing
      `pipeline_mode`/path; `native_staking_rates` → solana_rpc vs helius_rpc). Idempotent. **(MIGRATED FROM:
      `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P1. Backfill the existing DeFi corpus — run now, parallel in-region VMs sharded by `day=` (see § Migration
      scope); fold into the defi canonicalisation migration (`defi_manifest_canonicalisation_2026_06_01.md`) if open,
      else run direct; manifest re-consolidation after. **(MIGRATED FROM:
      `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [MTDS] P1. Thread `source="tardis"` through every CeFi adapter write + extend
      `record_empty_for_shard`/`record_failed_for_shard` to accept + forward `source`.
      `market-data-processing-service/.../core/canonical_writer.py`. (No `SOURCE_PRIORITY` change needed yet — `tardis`
      is already the declared source; expand the list only when the alternative actually lands.) **PARTIAL-VERIFIED
      (slot-3 cefi run-readiness re-audit 2026-06-04):** the **captured** write-path already auto-derives + stamps
      `source="tardis"` for cefi on BOTH surfaces — UAC `SOURCE_PRIORITY` registers `("cefi", <data_type>) → ["tardis"]`
      (source_priority.py:152-160), the MTDS raw-tick writer derives via `get_primary_source` (mtds@4e5fa57f), and the
      MDPS candle writer derives via `_resolve_primary_source_for_candle` (canonical_writer.py:1316-1319). REMAINING for
      this item: confirm the `record_empty_for_shard` / `record_failed_for_shard` empty/failed paths likewise forward
      `source` (the captured path is done), + the [TEST] below, + the [DATA] historical backfill (rides the cefi
      C-source RIDER). Repo: market-data-processing-service. **(MIGRATED FROM:
      `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [TEST] P1. CeFi unit test: a cefi cell without `source=` raises; `source="tardis"` persists; a future
      `["<alt>", "tardis"]` registry expansion resolves two sources by priority. **(MIGRATED FROM:
      `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P1. Backfill `source="tardis"` onto the existing cefi corpus — **fold into
      `cefi_manifest_canonicalisation_2026_06_01.md` C-source rider** (its single bundled walk owns the cefi `_index`;
      do NOT open a separate cefi source walk — single-walk discipline). If that walk has not launched, run direct (see
      § Migration scope, two steps): (1) data-parquet column backfill — **write `backfill_cefi_source_column.py`** (copy
      tradfi template) then fan across same-region VMs, sharded by `day=` (no egress, idempotent); (2) manifest
      re-consolidation after. Labels the corpus before any Tardis swap. **(MIGRATED FROM:
      `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P1. Backfill the existing sports corpus — **fold into `sports_manifest_canonicalisation_2026_06_01.md`
      C-source rider** (its single bundled walk owns the sports `_index`; do NOT open a separate sports source walk —
      single-walk discipline). If that walk has not launched, run direct (parallel in-region VMs sharded by `day=`, see
      § Migration scope) + manifest re-consolidation after. Confirms sports source moves path→column for the whole
      corpus. **(MIGRATED FROM: `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)**

- [ ] [TEST] P0. Prove the consumer read path resolves source priority for **cefi/defi/tradfi** (not just tradfi):
      2-source cell (same instrument+ts from two providers, co-mingled in one folder) → consumer emits exactly ONE
      resolved row via `select_primary_available_source()`. No silent double-count. Cover features-service consumers.
      **PARTIAL — resolution PRIMITIVES proven generic (uac@559dc81b: select_primary picks index-0 primary per cell;
      detect_dual_source_conflicts surfaces overlaps). REMAINING: wire the resolver into the cefi/tradfi consumer read
      paths — currently dead code (see finding below).** **⚠️ SPORTS DESCOPED 2026-06-03 (slot-4 read-path audit):
      sports multi-source is `FIELD_UNION`, NOT same-field source-pick — different providers contribute DIFFERENT fields
      per fixture (API-Football base + FootyStats predictions + Understat xG), merged by
      `features_service/sports/exporters/derived_features_exporter.py::_merge_provider_columns` ("left-merge
      non-overlapping provider columns" — the resolver docstring's rule-4, explicitly "handled at the consumer/writer
      layer, NOT by select_primary"); odds are per-bookmaker (each `venue=` is a DISTINCT instrument, not the same
      metric twice). So `select_primary_available_source` does not apply to sports — sports reads are already correct.
      Remaining scope is **cefi/tradfi** same-field dual-source ONLY (e.g. tradfi databento/massive), owned by this
      cross-AG plan, not slot-4 sports.** **TRADFI SLICE DONE + LAYER CORRECTED (slot-6 2026-06-05, UAC@637288d4 +
      mtds@0579438):** the read-path resolution is wired at the **MDPS raw read** (the actual co-mingle surface — two
      `pipeline_mode=`-partitioned objects per cell, NOT row-level co-mingle in one parquet; see the resolved FINDING
      below). `_resolve_multi_source_blobs` collapses a 2-source cell to exactly ONE primary-source object → no
      double-aggregate; regression `tests/unit/test_orchestration_scanner_multi_source.py` asserts 2-source→1 primary
      (databento>massive; massive>yahoo for ohlcv_15m) + the no-op guards. This covers tradfi (the only live 2-source
      pair). **REMAINING for full P0:** cefi when its 2nd source lands (same MDPS path, no new wiring — just a cefi
      regression case) → so this P0 is tradfi-complete; leave open for the cefi-2nd-source case. **(MIGRATED FROM:
      `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [UTL] P1. **FINDING (2026-06-01 read-path audit)**: `manifest_consolidator.py` dedup key (`_BASE_DEDUP_COLS` +
      `_OPTIONAL_DEDUP_COLS`) **omits `source`** — two source rows for one `(date, venue, data_type, …)` cell collapse
      to ONE row by last-write-wins on `(attempted_at, written_at)`, NOT by `SOURCE_PRIORITY`. Matches the shipped
      tradfi **union** model (per-source provenance lives in the parquet `source` column), so not a data-loss bug today.
      **Decision (sequence with the data-side backfill)**: if per-source _manifest_ rows must be preserved, add `source`
      to `_OPTIONAL_DEDUP_COLS` — but that changes consolidation cardinality for all asset groups (naive consumers would
      then see N rows/cell), so it must land WITH the read-path resolver wiring above. Do NOT change unilaterally.
      **(MIGRATED FROM: `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS consolidation
      ruling.)**

- [ ] [TEST] P1. **`available_at` parity across sources (batch = live)**: rows from any source for a cell are
      timestamped with the live-mode `available_at` of the `SOURCE_PRIORITY` top entry — NOT each vendor's slower
      archive time. A 2-source fixture asserts identical `available_at` derivation per cell, so swapping/adding a source
      never shifts the lookahead. (Covers the tradfi audit item (n) generalised to all asset groups.) **(MIGRATED FROM:
      `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [QG] P1. **(checker DONE, wiring REMAINING)** Checker generalised —
      `check_tradfi_source_explicit_at_record_captured.py` now flags only when a callsite's resolved
      `(category, data_type)` (literal or module-constant) is multi-source per `source_required()` AND `source=` is
      absent; covers `record_captured` + `add`; degrades to no-op if UAC absent (PM@5bba69651, slot ref). Verified
      catches defi/tradfi multi-source-blank, skips single-source (auto-stamp). **REMAINING: wire into MTDS + MDPS
      `quality-gates.sh` — blocked until the checker reaches LDR (can't wire a clean repo to a PM script not yet
      promoted).** **(MIGRATED FROM: `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)**

- [ ] [MTDS] P1. **A12a — wire the upstream instruments-service DeFi-catalog PREFLIGHT into the REMAINING DeFi collect
      handlers** (shared gate landed 2026-06-04 slot-2: UAC `PreflightTrigger.DEFI_COLLECT_DAILY` +
      `INSTRUMENTS_PREFLIGHT_REQUIREMENTS[(DEFI,"defi_market_data")]` → `instrument-catalog` within 24h, exported from
      UAC top-level; MTDS `_defi_manifest.assert_defi_catalog_fresh()` wraps
      `unified_trading_library.instruments_preflight.run_preflight` and routes honest absence — `record_failed` per
      shard, never raises in a per-venue loop). **WIRED so far**: `dex_pools_handler` (arbitrage critical path) +
      `lst_rates_handler` (carry critical path). **REMAINING** DeFi collect handlers in
      `market-tick-data-service/market_tick_data_service/cli/handlers/` to call `assert_defi_catalog_fresh(...)` at
      their `process()` chokepoint before the source fetch + record honest absence on a stale catalog:
      `dex_swaps_handler`, `lending_indices_handler`, `perp_funding_handler`, `oracle_prices_handler`,
      `liquidations_handler`, `liquidation_events_handler`, `staking_yields_handler`, `eigenlayer_rewards_handler`,
      `vault_share_price_handler`, `gas_fee_handler`, `bridge_events_handler`, `governance_events_handler`,
      `governance_proposals_handler`, `mev_events_handler`, `token_transfers_handler`, `position_data_handler`,
      `aggregator_route_handler`, `flash_loan_events_handler`, `jupiter_quote_handler`, `phoenix_orderbook_handler`,
      `orca_whirlpool_state_handler`, `raydium_classic_amm_handler`, `drift_v2_historical_handler`,
      `solana_defi_handler`, `evm_defi_handler`. (Existing handler tests that call `process()` must patch
      `assert_defi_catalog_fresh` → True, as done for dex_pools/lst_rates.) **Codex SSOT**: add a DeFi row to the
      instruments-preflight-chain doc (`/codex/04-architecture/instruments-preflight-chain.md`). **(MIGRATED FROM:
      `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] ❌ [DATA] P1. OBSOLETE/WONTFIX. ~~TradFi backfill UNBLOCKED (`MASSIVE_API_KEY` provided by operator 2026-06-01) —
      run the dual-source backfill per `tradfi_massive_dual_source_2026_05_28.md` Phase 5: stamp `source=databento` on
      legacy tradfi rows + ingest MASSIVE via **S3 flat-files** for bulk history (flat-files are independent of the REST
      tier — the bulk path; REST for incremental/live). Unblock the dual-source plan's deferred table accordingly.~~
      **Massive was REMOVED as a TradFi source 2026-07-19** (operator ruling: Databento = batch SoT, Yahoo = daily;
      routing DELETED `uac@a2beed46`/`mtds@362a487e`) and its GCS corpus **PURGED 2026-07-21** (accepted permanent
      loss); `tradfi_massive_dual_source_2026_05_28.md` itself now carries a `status: superseded` banner ("OBSOLETE — do
      not build"). No MASSIVE ingestion remains possible or wanted. The still-valid half (zero-blank `source` on every
      tradfi cell, including legacy rows) is already covered generically by the P0 "Data parquets" / "Manifest" todos
      below in this same doc — no separate carve-out needed. SSOT: `/codex/02-data/tradfi-databento-sourcing-ssot.md`,
      `plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md`. **(MIGRATED FROM:
      `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [AUDIT] P1. After enforcement lands, read ACTUAL `source` column distribution per (asset_group, venue, data_type)
      in prod manifests/parquets — confirm **zero blank source on EVERY cell, all asset groups** (not just
      multi-source). Data-state, NOT constant (manifest-v8 lesson: constant said 8 while 0% of rows were v8). Report
      per-cell histogram. **TOOL BUILT (read-only)**:
      `scripts/quality_gates/audit_source_column_distribution.py --manifest-path <gs-uri> [--strict]` — per-cell
      `source` histogram, classifies GREEN/RED(external-blank)/EXEMPT(computed/unregistered) via
      `external_sources_for()`; `--strict` exits 1 on any external-vendor blank. PM slot ref. **PROD RUN still
      sequenced** AFTER the bucket remediation + enforcement deploy + backfill (running pre-backfill correctly reports
      ~100% blank = the baseline). Re-run post-backfill to confirm zero-blank. **(MIGRATED FROM:
      `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P0. **Write-path** — universal gate live (`source` blank OR not-in-`SOURCE_PRIORITY` → raise) for every
      asset group; every MTDS/MDPS writer (cefi/defi/sports/prediction/tradfi) stamps `source`; QG STEP 5.64
      generalised + green. **(MIGRATED FROM: `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per
      MTDS consolidation ruling.)**

- [ ] [DATA] P0. **Data parquets** — `source` column populated on every ingested cell across all five asset groups, read
      from ACTUAL prod rows (data-state, not the constant): **zero blank `source`**. Sports migrated path→column. MDPS
      candles carry the inherited upstream source. **(MIGRATED FROM:
      `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P0. **Manifest** — re-consolidated; manifest `source` populated for every cell; multi-source cells = two
      rows. **(MIGRATED FROM: `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS consolidation
      ruling.)**

- [ ] [DATA] P0. **Downstream** — consumer read path resolves source priority for every multi-source asset group (one
      row per instrument+ts, no double-count); `detect_dual_source_conflicts()` surfaces divergence; `available_at`
      parity holds. **(MIGRATED FROM: `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)**

- [ ] [DATA] P0. **Sequencing honoured** — source backfill ran behind / folded into the running tick-bucket remediation,
      on canonical buckets, no race. **(MIGRATED FROM: `data_source_provenance_all_asset_groups_2026_06_01.md`,
      2026-07-13 per MTDS consolidation ruling.)**

- [ ] [CODEX] P1. **Codex + audit instructions** updated to the universal rule; audit result archived when every todo
      above is `[x]`.

Scope exemptions (by design, not gaps): features-service / strategy / execution outputs (computed — no vendor source).
**(MIGRATED FROM: `data_source_provenance_all_asset_groups_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**
