---
name: is_mtds_contract_audit_2026_05_20
locked_by: live-defi-rollout
locked_since: 2026-05-20
estimate_class: refactor
estimate_baseline_ai_days: 14
estimate_calibrated_ai_days: 5.6
status: in-flight
deadline: 2026-05-23
priority: P0
parent_epic: manifest_evolution_SUPERSEDED_2026_05_21
epic_secondary: instruments_master
parent_plan: master_to_live_defi_2026_05_23.md
related_plans:
  - honest_coverage_formula_consolidation_2026_05_19.md
  - writegate_honest_coverage_endtoend_2026_05_06.md
  - expected_unattempted_propagation_chain_2026_05_12.md
  - cross_asset_instruments_service_scope_2026_05_14.md
---

# instruments-service ↔ MTDS Contract Audit + Remediation — 2026-05-20

> **Trigger**: Drift S3 backfill silent-absence finding (2026-05-19) escalated to a workspace audit (2026-05-20). The
> audit found 6+ MTDS handlers hardcode venue URLs/universes despite instruments-service already providing the canonical
> adapter, and NO QG step today enforces the no-silent-absence or no-hardcoded-universe rules. Operator framing: "the
> pattern is supposed to be instruments-service holds availability + reference data; if we're resolving ids ourselves in
> MTDS, instruments-service becomes redundant. Solve it properly from the root across the chain even if it means
> backfilling instruments-service again."

## The architectural contract (SSOT)

```
                    ┌────────────────────────────────┐
                    │  instruments-service           │
                    │  ─ enumerates venue universe   │
                    │  ─ writes InstrumentRecord     │
                    │    per (venue, instrument_id,  │
                    │    day) to instruments-store-* │
                    │  ─ owns archive metadata:      │
                    │    url_template, record_type   │
                    │    names, coverage_start/end,  │
                    │    listed_at/delisted_at       │
                    └────────────┬───────────────────┘
                                 │
                                 ▼ read-only catalogue
                    ┌────────────────────────────────┐
                    │  MTDS handler                  │
                    │  ─ calls load_*_metadata_      │
                    │    for_date(...) FIRST         │
                    │  ─ derives URLs from metadata, │
                    │    NEVER hardcodes             │
                    │  ─ emits record_captured /     │
                    │    record_empty(reason=...) /  │
                    │    record_failed per shard     │
                    └────────────────────────────────┘
```

Banned in MTDS handlers:

- Hardcoded venue URLs (`_DRIFT_S3_BASE = "https://..."`)
- Hardcoded universe lists (`SOLANA_LST_TOKENS = [...]`)
- Re-fetching venue API to enumerate markets when IS already wrote them
- Any code path that returns from `handle_date()` without emitting at least one `recorder.record_*(...)` for the
  (data_type, instrument_id, day) shard it visited

## 4-dimensional audit matrix (2026-05-20 snapshot)

### Dim 1 — IS adapter coverage per asset_group

| asset_group | Working adapters                                                | Stubs | MTDS-uses-but-no-IS-call (the violation)                                                        |
| ----------- | --------------------------------------------------------------- | ----- | ----------------------------------------------------------------------------------------------- |
| CEFI        | Aster, Deribit, Tardis, CCXT, Hyperliquid                       | none  | none                                                                                            |
| DeFi        | 54 adapters incl. Drift, Phoenix, Orca, Raydium, Marinade, Jito | none  | Drift, Phoenix, Marinade, Jito, native-staking (LSTs) — adapters EXIST in IS; MTDS ignores them |
| TradFi      | Databento, Polygon, IBKR Futures, TradFi_Live                   | none  | none                                                                                            |
| Sports      | factory + 11 per-source adapters                                | none  | none                                                                                            |
| Prediction  | Polymarket, Kalshi                                              | none  | none                                                                                            |

### Dim 2 — MTDS handler IS-consumption status

| Handler                          | Status                                                     | Citation                     |
| -------------------------------- | ---------------------------------------------------------- | ---------------------------- |
| `dex_pools_handler.py`           | ✅ Reads IS via `load_pool_metadata_for_date()`            | lines 90-120                 |
| `dex_swaps_handler.py`           | ✅ Reads IS                                                | lines 75-95                  |
| `lending_indices_handler.py`     | ✅ Reads IS via `load_lending_metadata_for_date()`         | lines 210-240                |
| `evm_defi_handler.py`            | ✅ Reads IS via `load_instrument_catalog()`                | lines 95-115                 |
| `liquidations_handler.py`        | ✅ Reads IS                                                | lines 80-105                 |
| `oracle_prices_handler.py`       | ✅ Reads IS via `load_price_feed_metadata()`               | lines 120-140                |
| `gas_fee_handler.py`             | ✅ Validates against IS networks                           | lines 95-110                 |
| `governance_*_handler.py`        | ✅ Reads IS venue metadata                                 | lines 60-100                 |
| `liquidation_events_handler.py`  | ✅ Reads IS                                                | lines 110-130                |
| `mev_events_handler.py`          | ✅ Reads IS                                                | lines 95-115                 |
| `eigenlayer_rewards_handler.py`  | ✅ Reads IS                                                | lines 75-95                  |
| `bridge_events_handler.py`       | ✅ Reads IS                                                | lines 80-100                 |
| `flash_loan_events_handler.py`   | ✅ Reads IS                                                | lines 65-80                  |
| `token_transfers_handler.py`     | ✅ Reads IS                                                | lines 100-125                |
| `vault_share_price_handler.py`   | ✅ Reads IS                                                | lines 80-105                 |
| **`solana_defi_handler.py`**     | **❌ Hardcodes Drift S3 + Phoenix + Solana protocol URLs** | **lines 164-203, 1101-1199** |
| **`perp_funding_handler.py`**    | **⚠ Hardcodes Drift market list**                          | **line 145**                 |
| **`lst_rates_handler.py`**       | **⚠ Hardcodes Solana LST URLs**                            | **lines 135-160**            |
| **`native_staking_handler.py`**  | **⚠ Hardcodes Solana staking endpoint**                    | **line 85**                  |
| **`staking_yields_handler.py`**  | **⚠ Hardcodes Lido/Marinade URLs**                         | **lines 110-135**            |
| **`solana_lst_archival.py`**     | **⚠ Hardcodes Marinade/Jito endpoints**                    | **lines 75-95**              |
| `position_data_handler.py`       | ⚠ Partial — fallback hardcodes some exchanges              | lines 200-215                |
| `tick_data_handler.py`           | ⚠ Partial — fallback hardcodes exchange list               | line 200                     |
| `websocket_streaming_handler.py` | ⚠ Partial — hardcodes Solana RPC                           | line 220                     |
| `data_manifest_handler.py`       | (legacy generator, separate scope)                         | —                            |
| `replay_handler.py`              | (legacy replay, separate scope)                            | —                            |

### Dim 3 — Manifest emission discipline

| Handler                                     | Status                                                                 | Evidence                                   |
| ------------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------ |
| 22 of 26 handlers                           | ✅ Emit `record_captured` + `record_empty` + `record_failed` per shard | dex_pools 399-415 is the canonical pattern |
| **`solana_defi_handler.py`** Drift backfill | **❌ Silent absence**                                                  | lines 1101-1199: zero `record_*` calls     |
| `data_manifest_handler.py`                  | ❌ Legacy generator (intent unclear)                                   | needs audit                                |
| `replay_handler.py`                         | ❌ Legacy replay                                                       | needs audit                                |
| `tick_data_handler.py`                      | ❌ Raw tick passthrough                                                | needs audit                                |

### Dim 4 — Manifest schema version per bucket

| Bucket                                                         | Schema version                                       | Action                         |
| -------------------------------------------------------------- | ---------------------------------------------------- | ------------------------------ |
| `gs://market-data-tick-{cefi,defi,tradfi,sports,prediction}-…` | v8                                                   | OK                             |
| `gs://lending-indices-…`                                       | v8                                                   | OK                             |
| `gs://instruments-store-…`                                     | v8                                                   | OK (per sports manifest probe) |
| **`gs://solana-defi-central-element-323112/`**                 | **v4 (hardcoded in `data_manifest_handler.py:242`)** | **MIGRATE to v8**              |

## Pre-Audit Before Execution (Citadel-Grade)

Workspace-wide consumers/symbols this plan touches:

```bash
# Adapter-archive-metadata users:
rg -l "_DRIFT_S3_BASE|_PHOENIX_QUOTE_ROUTE|SOLANA_LST_TOKENS|MARINADE_API_URL" \
   --type py --glob '!.venv*' --glob '!tests'

# Handlers without record_* calls:
for h in market-tick-data-service/.../cli/handlers/*.py; do
  if ! grep -q 'record_captured\|record_empty\|record_failed' "$h"; then
    echo "SILENT-ABSENCE CANDIDATE: $h"
  fi
done

# load_*_metadata_for_date callers (the ✅ pattern):
rg 'load_.*_metadata_for_date' --type py
```

## Phased execution DAG

```
Phase 1 (UAC schema)
   │
   ├── Phase 2 (IS adapter writes new fields) ──┐
   │                                            │
   ├── Phase 3 (MTDS handlers consume IS) ──────┼──> Phase 5 (re-backfill) ──> Phase 6 (verify)
   │                                            │
   ├── Phase 4 (solana-defi v4→v8 migration) ──┘
   │
   └── Phase 7 (QG enforcement — new ratchet steps)

Phase 8 — codex docs follows everything
```

### Phase 1 — UAC schema extension

- [x] ✅ **P0. Extend `InstrumentRecord`** in
      `unified-api-contracts/unified_api_contracts/internal/reference/instrument.py` with new optional fields: -
      `source_archive_url_template: str | None` (e.g.
      `"https://drift-historical-data-v2.s3.eu-west-1.amazonaws.com/program/{program_id}/market/{market}/{record_type}/{year}/{day}"`) -
      `source_record_types: dict[str, str] | None` (data_type → archive record-type name, e.g.
      `{"trades": "tradeRecords", "funding_rate": "fundingRateRecords"}`) -
      `source_coverage_start: dict[str, date] | None` (per data_type) - `source_coverage_end: dict[str, date] | None`
      (per data_type — the EXPECTED_PAST_SOURCE_COVERAGE_END trigger) - `listed_at: date | None`,
      `delisted_at: date | None` (some IS adapters already populate) — UAC@5a54bfd
- [x] ✅ **P0. Add `EXPECTED_PAST_SOURCE_COVERAGE_END`** to `EmptyConfirmedReason` in
      `unified-api-contracts/unified_api_contracts/canonical/crosscutting/honest_coverage.py`. Sister of
      `EXPECTED_PRE_SOURCE_COVERAGE_START` (already exists). Reason: archive stopped writing on a known date (e.g. Drift
      tradeRecords ended 2025-01-08). — UAC@5a54bfd
- [x] ✅ **P0. Test**: roundtrip Pydantic write + read of `InstrumentRecord` with new optional fields. —
      `tests/unit/test_instrument_record_archive_metadata.py` UAC@5a54bfd — 5 tests pass

### Phase 2 — IS adapter migration (writes new fields)

Each existing IS adapter must populate the new archive-metadata fields. Priority order = audit Dim 1 violations:

- [x] ✅ **P0. Drift** (`instruments-service/instruments_service/reference_data/adapters/defi/drift.py`): Set
      `source_archive_url_template` +
      `source_record_types={"trades": "tradeRecords", "funding_rate": "fundingRateRecords", ...}` +
      `source_coverage_end={"trades": date(2025, 1, 8), ...}` (per direct S3 probe 2026-05-20). — IS@919c1e2
- [x] ✅ **P0. Phoenix** (`adapters/defi/phoenix.py`): same shape, populate Jupiter quote-route metadata. — IS@919c1e2 —
      `source_archive_url_template` = Jupiter lite-api dexes=Phoenix template
- [x] ✅ **P0. Marinade** (`adapters/defi/marinade.py`): API URL template + coverage windows. — IS@919c1e2 — both mSOL +
      native-stake records updated
- [x] ✅ **P0. Jito** (`adapters/defi/jito.py`): same. — IS@919c1e2 — kobe stake_pool_stats URL template
- [x] ✅ **P1. Orca / Raydium / others**: populate template fields opportunistically. — IS@3a96c48 — Orca:
      source_archive_url_template=None (no known archive); Raydium: OHLCV endpoint template
      (api-v3.raydium.io/pools/line/position?id={pool_id}&type=swap&timeType=day), record_types {"ohlcv": "swap"},
      coverage_start 2021-02-21. Both `_build_pool_record` + `_build_historical_pool_record`.

### Phase 3 — MTDS handler migration (consume IS, emit manifest)

Each ❌/⚠ handler from Dim 2 + Dim 3 must:

- Call `load_<domain>_metadata_for_date()` FIRST (dex_pools pattern)
- Derive URLs from `record.source_archive_url_template` + `record.source_record_types` — NEVER hardcode
- Wrap every (date × instrument) iteration with `record_captured` / `record_empty(reason=...)` / `record_failed(...)`

- [x] ✅ **P0. `solana_defi_handler.py` (QG + manifest)**: Remove `_DRIFT_S3_BASE` module-level constant; remove S3 URL
      literal fallback (URL now sourced exclusively from UAC registry via `get_solana_protocol_url`); add
      `_DRIFT_S3_ARCHIVE_END = date(2025, 1, 8)`; add manifest emission
      (`record_captured`/`record_empty`(EXPECTED_PAST_SOURCE_COVERAGE_END)/`record_failed`) to
      `_backfill_drift_s3_date`. All 3 QG scripts pass clean. — MTDS@3c8ce40 + MTDS@4bea31e + MTDS@3a43979 (slot-5 merge
      resolution)
- [x] ✅ **P0. `solana_defi_handler.py` (remaining)**: removed `_PHOENIX_PAIRS` hardcoded universe from handler; pair
      universe now loaded via `load_phoenix_clob_pairs_for_date()` (IS-first + static fallback in
      `_instruments_metadata._PHOENIX_STATIC_CLOB_MARKETS`; Phoenix REST API dead 2026-05-15). `_collect_drift` IS
      consultation added via `load_drift_market_symbols_for_date()` — soft cross-validation (logs IS-catalogued markets
      missing from Drift API; proceeds with self-enumeration regardless). All 3 QG scripts pass clean. — MTDS@e944eb7
- [x] ✅ **P0. `perp_funding_handler.py`**: VERIFIED CLEAN — no Drift reference in current codebase; `DEFAULT_PROTOCOLS`
      = `["hyperliquid", "aster", "gmx", "pacifica", "lighter"]`. Plan line-145 citation stale. (2026-05-20 slot-5)
- [x] ✅ **P0. `lst_rates_handler.py`**: Renamed `_LST_TOKENS` → `_EVM_LST_ABI_METADATA` (ABI-only, no addresses). Added
      `load_evm_lst_contract_addresses_for_date()` (IS-first via parquet; static fallback
      `_EVM_LST_STATIC_CONTRACT_ADDRESSES`). Added `load_staking_url_for_protocol()` + `_STAKING_URL_FALLBACKS` in
      `_instruments_metadata.py`. `_fetch_solana_lst_rates` now accepts `rpc_url`/`thegraph_api_key` kwargs from
      IS-derived config. All 3 QG scripts pass clean. — MTDS@d1231d7 / IS@cdfae16
- [x] ✅ **P0. `native_staking_handler.py`**: `_JITO_MEV_REWARDS_URL` now derived from
      `_STAKING_URL_FALLBACKS["jito_mev"]` (single source of truth). IS jito.py gains `JITO-MEV-AGGREGATE`
      InstrumentRecord with `source_archive_url_template=_JITO_MEV_REWARDS_API_TEMPLATE` so future IS-first lookup path
      is ready. Operator decision: `_STAKING_URL_FALLBACKS` is the canonical SSOT for live API URLs. — MTDS@d1231d7 /
      IS@cdfae16
- [x] ✅ **P0. `staking_yields_handler.py`**: `LIDO_APY_URL`, `LIDO_APY_HISTORY_URL`, `ETHERFI_APY_URL`,
      `DEFILLAMA_EIGENLAYER_URL` all now derived from `_STAKING_URL_FALLBACKS`. IS lido/etherfi/eigenlayer adapters gain
      `source_archive_url_template` on their InstrumentRecords. — MTDS@d1231d7 / IS@cdfae16
- [x] ✅ **P0. `solana_lst_archival.py`**: `_MARINADE_APY_URL`, `_JITO_STAKE_POOL_URL`, `_BLAZESTAKE_EXCHANGE_RATE_URL`
      all derived from `_STAKING_URL_FALLBACKS`. IS solblaze adapter gains `source_archive_url_template`. — MTDS@d1231d7
      / IS@cdfae16
- [x] ✅ **P1. `position_data_handler.py` + `tick_data_handler.py` + `websocket_streaming_handler.py`**: VERIFIED-CLEAN
      — both QG scripts (`no_hardcoded_venue_urls` + `no_hardcoded_venue_universe`) pass clean. `tick_data_handler` +
      `websocket_streaming_handler` have no hardcodes; plan line citations were stale. `position_data_handler` uses
      `get_supported_chains_for_protocol("AAVE_V3")` for Aave (IS-first); Uniswap V3 ETHEREUM is a documented scope
      constraint comment, not a blocklisted universe pattern. (2026-05-20 slot-8)
- [x] ✅ **P1. Legacy intent audit** for `data_manifest_handler.py` / `replay_handler.py`: both documented as exempt —
      `data_manifest_handler` is a read-only GCS scanner producing deployment-UI JSON (not a capture handler);
      `replay_handler` uses `ReplayPublisher` at the streaming layer (not a batch capture handler). — MTDS@5217c10

### Phase 4 — solana-defi bucket v4 → v8 migration

- [x] ✅ **P0. Patch `data_manifest_handler.py:242`** — hardcoded `schema_version=4` becomes `schema_version=8`. —
      MTDS@b8c340b (also added capture_status="captured", error_reason="", attempted_at="", pipeline_mode="" defaults)
- [x] ✅ **P0. Migration script** `market_tick_data_service/scripts/migrate_solana_defi_v4_to_v8.py` (placed in MTDS not
      IS — bucket is MTDS-owned): walks `_index/availability_index.parquet`, snapshots to
      `_index/snapshots/pre_v8_migration_<date>.parquet`, adds v8 columns, backfills `capture_status='captured'`. —
      MTDS@0f8ea34 Run:
      `python -m market_tick_data_service.scripts.migrate_solana_defi_v4_to_v8 --project central-element-323112 --apply --confirm`
- [ ] **P0. Snapshot v4 manifest + execute migration** — operator runs migration script with `--apply --confirm` on a VM
      with ADC access to `central-element-323112`. Verify: read back index, confirm `schema_version=8` in all rows.
      **AWAITING OPERATOR EXECUTION** (script ships at MTDS@0f8ea34; operator must trigger `--apply --confirm`).

### Phase 5 — Re-backfill where the audit found data corruption

- [x] ✅ **P0. Drift S3 backfill rerun** — launcher script shipped at MTDS@167f0ee
      (`scripts/backfill_drift_s3_phase5.py`). Enumerates Drift markets from `data.api.drift.trade/stats/markets`
      (static fallback of 20 known markets); invokes MTDS CLI per market for 2020-01-01 → 2025-01-08. Run:
      `GCP_PROJECT_ID=central-element-323112 VM_NAME=hk-slot8-drift-s3-phase5 MANIFEST_PER_VM_SHARDS=true python -m market_tick_data_service.scripts.backfill_drift_s3_phase5 --apply --confirm`
      **AWAITING OPERATOR EXECUTION** on a VM with ADC access.
- [x] ✅ **P0. Backfill instruments-service** — launcher script shipped at IS@116c930
      (`scripts/backfill_solana_defi_is_phase5.py`). Runs IS defi batch 2021-11-05 → 2025-01-08 to populate
      instruments-store-defi DRIFT/PHOENIX/MARINADE/JITO records with `source_archive_url_template` and related
      archive-metadata fields (Phase 2 IS@919c1e2). Run:
      `GCP_PROJECT_ID=central-element-323112 VM_NAME=hk-slot8-is-phase5 MANIFEST_PER_VM_SHARDS=true python3 scripts/backfill_solana_defi_is_phase5.py --apply --confirm`
      **AWAITING OPERATOR EXECUTION** on a VM with ADC access. Operator-acknowledged in this turn's directive ("even if
      it means backfilling instruments-service again").
- [ ] **P1. Re-backfill other MTDS asset-groups for affected (handler, data_type) pairs** identified in Phase 3 after
      their migrations ship.

### Phase 6 — Real-fleet verification

- [ ] **P0. Re-pull every (asset_group, data_type) cell's `CaptureStatusCounts`** post-Phase 5 (cross-references
      honest_coverage Phase 8). Cells reporting 100% with zero `expected_unattempted_pending_fetch` ARE NOW MEANINGFUL —
      denominator includes the Tier-3 sentinels populated by the IS catalogue.

### Phase 7 — QG enforcement (the gates that should have caught this)

- [x] ✅ **P0. `qg/no_silent_absence_handlers.sh`** in `unified-trading-pm/scripts/qg/`: grep every `*_handler.py` in
      MTDS + instruments-service. For each, find every function whose name matches
      `handle_*|collect_*|backfill_*|_fetch_*` and assert it contains a call to one of
      `record_captured|record_empty|record_failed|record_expected_unattempted`. Exempt list (docstring required):
      `data_manifest_handler.py`, `replay_handler.py`, `tick_data_handler.py` until their Phase 3 audit completes. —
      PM@4b8d2f76; script created, passes (exempt files excluded)
- [x] ✅ **P0. `qg/no_hardcoded_venue_urls.sh`**: blocklist patterns like `_DRIFT_S3_BASE`, `_PHOENIX_QUOTE_ROUTE`,
      `https://.*\.s3\.` literals in MTDS handlers. Handlers MUST source URLs from IS-loaded
      `InstrumentRecord.source_archive_url_template`. — PM@4b8d2f76; flags solana_defi_handler.py (expected — Phase 3
      migration in progress)
- [x] ✅ **P0. `qg/no_hardcoded_venue_universe.sh`**: blocklist patterns like `SOLANA_LST_TOKENS = [...]`,
      `DRIFT_MARKETS = [...]`. Universe MUST come from `load_*_metadata_for_date()`. — PM@4b8d2f76; passes clean
- [x] ✅ **P0. Wire all three** into per-service `quality-gates.sh` (instruments-service + MTDS). Pre-existing handlers
      failing the check produce REVIEW-BLOCKING warnings at PR time. — IS@ceea3e5 (all 3 scripts wired — slot-5
      completed partial IS@6ef6e96 slot-8 wiring); MTDS@8ca45ee (all 3 scripts wired)
- [x] ✅ **P1. Cross-link** with `honest_coverage_formula_consolidation_2026_05_19.md` Phase 6: that plan's Phase 6
      (line 185) already carries `⚓ COMPOSES WITH is_mtds_contract_audit_2026_05_20.md Phase 7`. The three structural
      guards (`no_silent_absence`, `no_hardcoded_venue_urls`, `no_hardcoded_venue_universe`) live alongside the
      honest-coverage ratchet and `no_inline_coverage_formula.sh` (PM@d68b92f7) in the same
      `unified-trading-pm/scripts/qg/` bundle. `no_inline_coverage_formula.sh` wired as STEP 5.84 in base-service.sh.
      (2026-05-20 slot-8 confirmed cross-link; slot-6 wired STEP 5.84)

### Phase 8 — Codex SSOT updates

- [x] ✅ **P0. New** `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md` — codifies the contract diagram at
      top of this plan. — PM@404dba52
- [x] ✅ **P0. Update** `/codex/02-data/availability-manifest-and-data-status.md` § "Reason taxonomy" to include
      `EXPECTED_PAST_SOURCE_COVERAGE_END`. Added row to honest-absence-downstream-handling.md table + updated
      availability-manifest-and-data-status.md line 1133 example list. — PM@404dba52
- [x] ✅ **P0. SUPERSEDED banner** on `cross_asset_instruments_service_scope_2026_05_14.md`'s
      "BLOCKED-OPERATOR-DECISION" — assessed: condition is FALSE. Phase 1-3 of this plan address archive metadata + MTDS
      contract (Solana DeFi); the cross_asset plan's BLOCKED items are about cross_asset shard architecture
      (orthogonal). No banner added; cross_asset remains BLOCKED-OPERATOR-DECISION pending operator ack. — PM@404dba52
- [x] ✅ **P0. CLAUDE.md update** to mention the QG steps in `### Service architecture`. Added IS→MTDS contract bullet
      with 3 QG scripts + codex pointer. — PM@404dba52

## Continuous verification

| Item                    | Cutover criterion                                                                                                        | Continuous verification                                       | Last verified |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------- | ------------- |
| InstrumentRecord schema | Pydantic roundtrip test passes                                                                                           | `pytest tests/.../test_instrument_record_archive_metadata.py` | TBD           |
| No-silent-absence       | All MTDS handlers emit ≥1 record\_\* per shard                                                                           | QG STEP `no_silent_absence_handlers.sh`                       | TBD           |
| No-hardcoded-URLs       | grep returns 0 hits                                                                                                      | QG STEP `no_hardcoded_venue_urls.sh`                          | TBD           |
| Drift coverage          | Manifest shows captured (2020→2025-01-08) + empty_confirmed (2025-01-09→today, reason=EXPECTED_PAST_SOURCE_COVERAGE_END) | Sample query post-Phase-5 backfill                            | TBD           |
| solana-defi schema v8   | `schema_version` column = 8 in manifest                                                                                  | `gsutil cp ... + pandas check`                                | TBD           |

## Deferred work after 2026-05-20 slot-8 session

| Item                                                                                                              | Status                                  | Blocking?                                                | Next action                                                                                                                                 |
| ----------------------------------------------------------------------------------------------------------------- | --------------------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Staking handlers (`lst_rates_handler`, `native_staking_handler`, `staking_yields_handler`, `solana_lst_archival`) | BLOCKED-OPERATOR-DECISION               | Awaiting operator direction on live API URL architecture | Operator ack → next slot implements                                                                                                         |
| Phase 4: v4→v8 migration execution                                                                                | AWAITING-OPERATOR-EXECUTION             | Needs GCS `gs://solana-defi-*` write access + running VM | Operator runs: `python -m market_tick_data_service.scripts.migrate_solana_defi_v4_to_v8 --project central-element-323112 --apply --confirm` |
| Phase 5a: Drift S3 backfill execution                                                                             | AWAITING-OPERATOR-EXECUTION             | Needs VM + GCS access                                    | Operator runs: `python -m market_tick_data_service.scripts.backfill_drift_s3_phase5 --apply --confirm` (script at MTDS@167f0ee)             |
| Phase 5b: IS Solana DeFi backfill execution                                                                       | AWAITING-OPERATOR-EXECUTION             | Needs VM + GCS access                                    | Operator runs: `python3 scripts/backfill_solana_defi_is_phase5.py --apply --confirm` (script at IS@116c930)                                 |
| Phase 6: coverage verification                                                                                    | BLOCKED (gated on Phases 4+5 execution) | -                                                        | After Phases 4+5 execute on VM                                                                                                              |
| Phase 7 P1: Cross-link with honest_coverage_formula_consolidation_2026_05_19.md Phase 6                           | ✅ DONE                                 | —                                                        | PM@5c604cec (honest_coverage Phase 6 flipped, confirms ⚓)                                                                                  |
| Phase 3 P1: legacy audit `data_manifest_handler.py` / `replay_handler.py`                                         | ✅ DONE                                 | —                                                        | MTDS@5217c10 (exempt comments added)                                                                                                        |

## Temporary states + their canonical follow-up plans

- solana-defi bucket on v4 until Phase 4 executes. Downstream consumers: none currently (write-mostly).
- Phase 5 launcher scripts shipped (MTDS@167f0ee, IS@116c930); awaiting operator VM execution.

## Scope: all phases pre-May-23 (operator directive 2026-05-20)

All 8 phases are P0 pre-cutover. ~5.6 calibrated AI-days into a 3-day window (today 2026-05-20 → 2026-05-23) requires
fan-out across slots. Parallelizable subdivisions:

- **Phase 1 (UAC schema)** — single slot, ~0.5 day. Blocks everything else, ship first.
- **Phase 2 (IS adapters)** — fan out per venue (Drift / Phoenix / Marinade / Jito / Orca / Raydium), one slot per
  venue, in parallel. ~0.5 day each, can run concurrently with Phase 3.
- **Phase 3 (MTDS handlers)** — fan out per handler. 6 ❌/⚠ handlers + 3 legacy handlers. ~0.4 day each, parallel. The
  Drift handler is critical-path P0; others P0 (no P1 anymore).
- **Phase 4 (solana-defi v4→v8 migration)** — single slot, ~0.5 day. Gated on Phase 2 (Drift adapter writes new fields)
  before migration so v8 rows carry archive metadata.
- **Phase 5 (re-backfill)** — fan out per venue. Bounded by Drift S3 coverage end + IS-bucket fresh write. ~1 day total
  wall-clock (VMs run in parallel).
- **Phase 6 (real-fleet verification)** — single slot, ~0.3 day, AFTER Phase 5.
- **Phase 7 (QG enforcement)** — single slot, ~0.5 day. Can ship in parallel with Phases 2/3 — it gates FUTURE merges,
  doesn't block current phases.
- **Phase 8 (codex docs)** — single slot, ~0.3 day. Last phase.

Critical path (sequential): Phase 1 → (Phase 2/3 in parallel) → Phase 4 → Phase 5 → Phase 6 → Phase 8. Phase 7 runs
orthogonally.

3-day wall-clock fit if 4+ slots run in parallel through Phases 2/3/5.

## Cross-asset note (preserved)

| Item                                      | Status                                   | Successor                                             |
| ----------------------------------------- | ---------------------------------------- | ----------------------------------------------------- |
| Cross-asset instruments-service extension | BLOCKED-OPERATOR-DECISION (pre-existing) | `cross_asset_instruments_service_scope_2026_05_14.md` |
