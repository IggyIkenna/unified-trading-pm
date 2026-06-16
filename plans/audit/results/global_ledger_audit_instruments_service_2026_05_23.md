---
type: analysis
title: Global Ledger Audit — instruments-service
epic: global_ledger_pnl_attribution_master
auditor: slot-7 (ikenna-side)
date: "2026-05-23"
status: complete
source:
  - instruments-service/instruments_service/engine/orchestrator.py
  - instruments-service/instruments_service/reference_data/
  - unified-api-contracts/unified_api_contracts/internal/reference/instrument.py
  - unified-api-contracts/unified_api_contracts/registry/market_data_categories.py
  - unified-api-contracts/unified_api_contracts/registry/expected_coverage.py
  - unified-api-contracts/unified_api_contracts/canonical/domain/derivatives/futures.py
  - unified-api-contracts/unified_api_contracts/_instrument_enums.py
---

# Global Ledger Audit — instruments-service

**Scope**: Phase 1 audit from `global_ledger_pnl_attribution_discovery_2026_05_21.md`. Maps what instruments-service
(IS) provides vs what the `PassiveLedger` synthesiser requires. Read-only; no code changes.

**Method**: Static source read across IS orchestrator, all adapter implementations, InstrumentRecord schema, UAC
DATA_TYPES_BY_ASSET_GROUP, and EXPECTED_COVERAGE_BY_ASSET_GROUP. No sampling of live GCS data.

---

## 1. Instrument Metadata Coverage

`InstrumentRecord` is defined in `unified-api-contracts/unified_api_contracts/internal/reference/instrument.py`. It has
**22 stored fields**. Below is the per-field assessment for PassiveLedger synthesis:

| PassiveLedger-required field                                   | Present in InstrumentRecord? | Where stored                                                     | Notes                                                                                                                                                                                                                                                                                                                                                                                       |
| -------------------------------------------------------------- | ---------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `expiry_date`                                                  | **Present**                  | `expiry: datetime \| None`                                       | Hard-enforced non-null for FUTURE / OPTION / EVENT_CONTRACT by model_validator. Stored and written to parquet. `CanonicalFuturesContract.expiry_date` additionally carries the 5-date lifecycle (expiry, last_trading_date, first_notice_date, delivery_date, settlement_date).                                                                                                             |
| `contract_multiplier`                                          | **Partial**                  | `contract_size: Decimal \| None`                                 | Field exists but named `contract_size`. IS adapters populate it (e.g. ES = $50 × index). For DeFi and CeFi perp it is set to Decimal("1"). No separate "contract_multiplier" field; PassiveLedger must read `contract_size`.                                                                                                                                                                |
| `exercise_style` (American vs European)                        | **MISSING**                  | —                                                                | `OptionType` enum only has CALL / PUT (`option_type: OptionType \| None`). No `exercise_style` field on InstrumentRecord. Databento/CBOE adapters do NOT populate it. American option early exercise cannot be detected from IS metadata alone.                                                                                                                                             |
| `settlement_style` (cash vs physical)                          | **Partial — TradFi only**    | Inferred from `_PHYSICAL_DELIVERY_ROOTS` in `futures_factory.py` | For CME/ICE futures the factory derives physical vs cash from the root symbol (CL/GC = physical; ES/NQ = cash). This logic lives in the IS futures factory and the result appears in `CanonicalFuturesContract`. InstrumentRecord itself has no `settlement_style` field. DeFi/CeFi have no equivalent.                                                                                     |
| `dividend_schedule` (ex-div dates, amounts)                    | **MISSING**                  | —                                                                | No `dividend_schedule`, `ex_div_date`, or `dividend_amount` field on InstrumentRecord. IS has a `CanonicalCorporateAction` schema in `reference_data/schemas.py` but it is NOT persisted to parquet by the orchestrator — it is an in-memory reference type only. The TradFi IBKR adapter exists but corporate actions are not written to the instruments bucket.                           |
| `funding_interval` (perp funding: 8h, 1h, etc.)                | **MISSING**                  | —                                                                | No `funding_interval` field on InstrumentRecord. The `FundingRateRef` schema in `reference_data/schemas.py` carries `next_funding_time` but this is also not persisted to parquet. The `source_record_types` dict field on InstrumentRecord could in theory carry this, but no adapter populates it for funding interval.                                                                   |
| `lending_rate_source` (where to get DeFi borrow/lending rates) | **Present via convention**   | `source_archive_url_template: str \| None`                       | IS adapters (Aave, Compound, Lido, Jito, Marinade, Rocket Pool) populate `source_archive_url_template` with the REST/subgraph URL from which MTDS derives the rate. This IS the `lending_rate_source` — the field name in InstrumentRecord is different but the data is there. Additionally `pool_address` / `atoken_address` / `base_asset_contract_address` provide on-chain identifiers. |

**Summary**: InstrumentRecord provides expiry, contract_size, lending URL, and on-chain addresses. It is **missing
exercise_style, settlement_style on a field-level basis (TradFi inferred only via factory), and dividend_schedule
entirely**.

---

## 2. Carry-Family Rate Handlers

**Critical architectural clarification**: instruments-service does NOT write carry-family rates (`lending_indices`,
`lst_rates`, `perp_funding`, `native_staking_rates`) to parquet itself. IS writes InstrumentRecord metadata (one parquet
per venue per date under `instrument_availability/by_date/`). The carry rates are written by **MTDS** handlers. IS
provides the InstrumentRecord metadata (pool_address, atoken_address, source_archive_url_template) that MTDS handlers
consume to derive where to fetch rates.

This is the IS→MTDS contract codified in `codex/04-architecture/instruments-service-as-ssot-for-mtds.md`.

### What IS adapters DO provide

| Adapter                        | InstrumentType emitted         | Key metadata for rate derivation                                                                    | source_archive_url_template                                                     |
| ------------------------------ | ------------------------------ | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `lido.py`                      | YIELD_BEARING                  | `base_asset_contract_address` (stETH/wstETH), `base_asset_decimals=18`                              | `https://api.lido.fi/v1/protocol/steth/apr/last`                                |
| `rocket_pool.py`               | YIELD_BEARING                  | `base_asset_contract_address` (rETH), `base_asset_decimals=18`                                      | Not populated (gap — see §5)                                                    |
| `aave_v3.py`                   | LENDING (A_TOKEN + DEBT_TOKEN) | `pool_address` (reserve.id), `atoken_address`, `base_asset_contract_address`, `base_asset_decimals` | Not populated (subgraph URL provided at request time via `get_subgraph_id()`)   |
| `compound_v3.py`               | LENDING                        | `pool_address` (comet proxy), `base_asset_contract_address`, `base_asset_decimals`                  | Not populated (same pattern as Aave)                                            |
| `jito.py`                      | STAKING                        | `base_asset_contract_address` (JITOSOL mint), `base_asset_decimals=9`                               | `https://kobe.mainnet.jito.network/api/v1/stake_pool_stats` + MEV URL           |
| `marinade.py`                  | STAKING                        | `base_asset_contract_address`, `base_asset_decimals=9`                                              | `https://api.marinade.finance/msol/apy/365d`                                    |
| `solana_native_staking.py`     | STAKING                        | `base_asset_contract_address` (SOL mint), `base_asset_decimals=9`                                   | Not populated (RPC-based)                                                       |
| `ethena.py`                    | YIELD_BEARING                  | EVM addresses                                                                                       | Populated                                                                       |
| `etherfi.py`                   | YIELD_BEARING                  | EVM addresses                                                                                       | Populated                                                                       |
| `ccxt_adapter.py` (CeFi perps) | PERPETUAL                      | `base_asset`, `quote_asset`, `margin_type`                                                          | `source_record_types` contains `"funding_rate": "fundingRateRecords"` for Drift |

### Carry-family data_types — WHERE they are written

| Passive event type             | data_type in UAC           | Written by                   | Shard key                             | IS provides                                                                                   |
| ------------------------------ | -------------------------- | ---------------------------- | ------------------------------------- | --------------------------------------------------------------------------------------------- |
| Perp funding receipt (CeFi)    | `derivative_ticker` (CeFi) | MTDS Tardis adapter          | (venue, date, instrument)             | InstrumentRecord with `instrument_type=PERPETUAL`, `base_asset`, `quote_asset`, `margin_type` |
| Perp funding receipt (DeFi)    | `perp_funding`             | MTDS perp_funding_handler    | (venue, chain, date, symbol)          | InstrumentRecord for Drift/Hyperliquid/GMX/Aster/Pacifica with `source_archive_url_template`  |
| DeFi lending interest (supply) | `lending_indices`          | MTDS lending_indices_handler | (venue, chain, date, instrument_type) | AaveV3/CompoundV3/Morpho InstrumentRecord with pool_address + atoken_address                  |
| LST staking reward             | `lst_rates`                | MTDS lst_rates_handler       | (venue, date)                         | Lido/RocketPool/Jito/Marinade InstrumentRecord with source_archive_url_template               |
| Solana native staking          | `native_staking_rates`     | MTDS native_staking_handler  | (venue, chain, date)                  | SolanaNativeStaking InstrumentRecord (RPC-based, no URL template)                             |
| TradFi futures settlement      | `trades` + `ohlcv_1m`      | MTDS Databento adapter       | (venue, date, symbol)                 | CanonicalFuturesContract with expiry_date / settlement_date / lifecycle_phase                 |
| TradFi dividend                | NONE written by IS         | Not captured                 | —                                     | CanonicalCorporateAction schema exists but IS does not write it to parquet                    |

---

## 3. PassiveLedger Synthesiser Sufficiency

For each passive event type, can IS metadata alone synthesise the event WITHOUT a live listener?

| Passive Event Type                                | Synthesisable from IS alone?           | Rationale                                                                                                                                                                                                                                                                                                                                                                                      |
| ------------------------------------------------- | -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CeFi perp funding receipt**                     | Partial                                | IS provides InstrumentRecord (PERPETUAL, base_asset, margin_type). The ACTUAL rate (fundingRate, next_funding_time, funding_interval) is NOT in IS — it is in MTDS `derivative_ticker` parquet. PassiveLedger can compute funding P&L only after reading MTDS derivative_ticker rows for the period. IS tells you WHICH instruments are perps and their margin type; MTDS tells you the rates. |
| **DeFi perp funding receipt (Drift/Hyperliquid)** | Partial                                | Same as CeFi. IS provides InstrumentRecord (PERPETUAL + source_archive_url_template). Actual funding rates live in MTDS `perp_funding` parquet.                                                                                                                                                                                                                                                |
| **DeFi lending interest (Aave supply APY)**       | Partial                                | IS provides pool_address + atoken_address (where to fetch rates) but the actual rate timeseries is in MTDS `lending_indices`. IS also does NOT store the funding interval (supply APY accrual cadence). PassiveLedger REQUIRES MTDS `lending_indices`.                                                                                                                                         |
| **LST staking reward (Lido stETH APR)**           | Partial                                | IS provides `source_archive_url_template` = Lido APR endpoint. The actual per-epoch APR timeseries is in MTDS `lst_rates`. IS cannot synthesise the dollar amount of reward without querying MTDS.                                                                                                                                                                                             |
| **Solana native staking reward**                  | Partial                                | IS provides STAKING InstrumentRecord (SOL mint). Rates come from MTDS `native_staking_rates` (Solana RPC). IS alone insufficient.                                                                                                                                                                                                                                                              |
| **TradFi futures settlement (cash)**              | YES — from IS CanonicalFuturesContract | IS writes `futures_contracts.parquet` per venue per date with `expiry_date`, `settlement_date`, `lifecycle_phase`. PassiveLedger can determine settlement date purely from IS. The settlement P&L amount requires the mark-to-market price at settlement (from MTDS tick data), but the WHEN and IS_PHYSICAL/IS_CASH can come from IS alone.                                                   |
| **TradFi futures settlement (physical)**          | PARTIAL                                | IS `CanonicalFuturesContract` carries physical-vs-cash inference via `_PHYSICAL_DELIVERY_ROOTS` in futures_factory.py, written to `futures_contracts.parquet`. But IS has no `settlement_style` field on InstrumentRecord itself — only CanonicalFuturesContract has this baked in. PassiveLedger can get it from futures_contracts parquet but NOT from InstrumentRecord directly.            |
| **Equity option early exercise (American)**       | NO                                     | IS has no `exercise_style` field. American vs European is NOT derivable from IS metadata. PassiveLedger requires either a live listener (exchange notification) or an external reference (OCC exercise notices). Critically, American exercise timing is discretionary — no deterministic synthesiser can generate it from static metadata alone.                                              |
| **Equity dividend**                               | NO                                     | IS does NOT write dividend schedules to parquet (CanonicalCorporateAction exists in-memory only). No ex-div date, cash amount, or record date is persisted. PassiveLedger REQUIRES a live listener (IBKR corporate action events) OR a separate dividend calendar data source.                                                                                                                 |

---

## 4. Manifest Shape

### What data_types does IS write?

IS uses `PipelineMode.BATCH_INSTRUMENTS_SERVICE` for all non-sports/prediction writes. It does NOT write data_type-keyed
shards — the primary output is InstrumentRecord metadata, manifested at the venue level.

| Output                                    | GCS path pattern                                                                            | Manifest shard key                                                 | pipeline_mode                            |
| ----------------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ---------------------------------------- |
| CeFi instrument metadata                  | `instrument_availability/by_date/day={d}/venue={V}/instruments.parquet`                     | `{date, venue}`                                                    | `BATCH_INSTRUMENTS_SERVICE`              |
| DeFi instrument metadata                  | `instrument_availability/by_date/day={d}/venue={V}/chain={C}/instruments.parquet`           | `{date, venue, chain}`                                             | `BATCH_INSTRUMENTS_SERVICE`              |
| TradFi instrument metadata                | `instrument_availability/by_date/day={d}/venue={V}/instruments.parquet`                     | `{date, venue}`                                                    | `BATCH_INSTRUMENTS_SERVICE`              |
| TradFi futures contracts                  | `instrument_availability/by_date/day={d}/venue={V}/futures_contracts.parquet`               | `{date, venue}`                                                    | `BATCH_INSTRUMENTS_SERVICE`              |
| Sports fixtures                           | `instrument_availability/by_date/day={d}/venue=API_FOOTBALL/league={L}/instruments.parquet` | `{date, data_type=FIXTURES, league_id}`                            | `BATCH_API_FOOTBALL`                     |
| Sports entities (injuries, lineups, etc.) | Same bucket, by data_type                                                                   | `{date, data_type}`                                                | Per `_SPORTS_DATA_TYPE_TO_PIPELINE_MODE` |
| Prediction instruments                    | Per canonical_question_group                                                                | `{date, data_type=prediction_canonical_question_group, venue}`     | `BATCH_FOOTYSTATS` / `BATCH_ODDS_API`    |
| Prediction market lifecycle               | `market_lifecycle/by_canonical_group/group={g}/day={d}/market_lifecycle.parquet`            | `{date, data_type=prediction_market_lifecycle, venue, underlying}` | `BATCH_POLYMARKET` / `BATCH_KALSHI`      |

**Shard atom (non-sports/prediction): `(date, venue)` for CeFi/TradFi; `(date, venue, chain)` for DeFi.**

### Carry-rate data_types — NOT written by IS

The following data_types appear in `DATA_TYPES_BY_ASSET_GROUP["defi"]` but are written by MTDS, not IS:

- `lending_indices` — MTDS lending_indices_handler
- `lst_rates` — MTDS lst_rates_handler
- `perp_funding` — MTDS perp_funding_handler
- `native_staking_rates` — MTDS native_staking_handler
- `dex_pools`, `dex_swaps` — MTDS dex_pools_handler / dex_swaps_handler

IS writes instrument metadata that MTDS reads to derive these. The is IS→MTDS contract is enforced by QG STEP 5.70
(`no_hardcoded_venue_urls.sh`, `no_hardcoded_venue_universe.sh`).

---

## 5. Gaps to PassiveLedger

### Gap 1 — exercise_style MISSING from InstrumentRecord (CRITICAL for options)

- `InstrumentRecord` has `option_type: OptionType | None` (CALL/PUT) but NO `exercise_style`.
- Databento adapter parses `option_type` from the `instrument_class` column but does not capture American vs European
  from the Databento definition schema.
- American option early exercise is a P2 passive event that CANNOT be synthesised from IS alone.
- **Required**: Add `exercise_style: Literal["american", "european"] | None` to InstrumentRecord and populate from
  Databento's `exercise_style` field (present in their `definition` schema). Until then, PassiveLedger cannot handle
  American exercise events without a live listener.

### Gap 2 — settlement_style NOT surfaced as an InstrumentRecord field

- Physical vs cash settlement is inferred by `futures_factory.py` `_PHYSICAL_DELIVERY_ROOTS` frozenset and written only
  to `CanonicalFuturesContract.delivery_date` semantics.
- `InstrumentRecord` itself has no `settlement_style` field.
- PassiveLedger readers of InstrumentRecord parquet cannot determine settlement type directly; they must additionally
  read `futures_contracts.parquet` and cross-reference.
- **Required**: Either expose `settlement_style` on `InstrumentRecord` directly or document that PassiveLedger MUST join
  with `futures_contracts.parquet` for TradFi instruments.

### Gap 3 — dividend_schedule NOT written to any parquet

- `CanonicalCorporateAction` dataclass exists in `instruments_service/reference_data/schemas.py` but the orchestrator
  NEVER writes it to GCS.
- The TradFi IBKR adapter exists at `reference_data/adapters/tradfi/ibkr.py` but IS does not call it for corporate
  actions in the orchestrator dispatch.
- Equity dividend receipts are a passive event that IS ENTIRELY ABSENT from IS parquet output.
- **Required**: PassiveLedger equity dividend synthesis requires either (a) writing CanonicalCorporateAction to a new
  parquet partition from IS, or (b) sourcing from an external dividend calendar (Databento corporate actions endpoint,
  IBKR, Bloomberg) via MTDS as a new `dividend_events` data_type.

### Gap 4 — funding_interval not stored

- No `funding_interval` field on InstrumentRecord.
- Perp funding accrual cadence (8h for most CeFi, 1h for Hyperliquid, per-epoch for Solana) is not derivable from IS
  metadata. MTDS derivative_ticker rows carry `next_funding_time` but the regular interval must be inferred from the
  venue's known convention.
- **Required**: PassiveLedger must hardcode or infer funding intervals from venue-level rules (UAC VenueMapping or a new
  per-venue funding interval registry). IS cannot supply this per-row.

### Gap 5 — rocket_pool.py missing source_archive_url_template

- `rocket_pool.py` does not set `source_archive_url_template` (it is None).
- This means MTDS's rETH handler cannot derive the rate URL from IS metadata and must hardcode it.
- Violates the IS→MTDS contract QG STEP 5.70.
- **Required**: Add `source_archive_url_template` to the Rocket Pool adapter pointing to the rETH exchange rate endpoint
  (e.g. Rocket Pool API or The Graph subgraph).

### Gap 6 — Sanctum (Solana LST aggregator) has no IS adapter

- `_SOLANA_DEFI_VENUES` and `_STATIC_DEFI_VENUES` do not include Sanctum.
- The `sanctum.py` adapter file EXISTS in `adapters/defi/` but is not registered in the orchestrator venue lists.
- Sanctum aggregates many Solana LST exchange rates (100+ validators).
- **Required for PassiveLedger Solana LST completeness**: Register Sanctum-SOLANA in `_SOLANA_DEFI_VENUES` and wire its
  InstrumentRecord output.

### Gap 7 — native_staking_rates / vault_share_price / governance_proposals deferred in DATA_TYPES

- The comment in `expected_coverage.py` line 311 notes: "These 3 data_type families are NOT yet in
  DATA_TYPES_BY_ASSET_GROUP['defi']" — tracked as
  `plans/active/issues/defi_coverage_capability_alignment_2026_05_22.md`.
- `native_staking_rates` specifically is needed for Solana validator staking reward synthesis.
- Until this is registered, the coverage denominator silently excludes it.

---

## 6. Coverage Transparency

**Sampling vs exhaustive walk**: This audit was performed by static code reading — NOT by sampling GCS parquet or
walking manifest rows. For a complete data-state picture (how much IS data actually exists in production), run
`python3 scripts/verify_instrument_manifest_coverage.py` and cross- reference
`scripts/enumerate_expected_universe.py --asset-group defi`.

**Remaining coverage gaps** (per static analysis):

- exercise_style on all OPTION records: 0% (field does not exist)
- dividend_schedule on all EQUITY records: 0% (parquet not written)
- funding_interval on all PERPETUAL records: 0% (field does not exist)
- Rocket Pool source_archive_url_template: 0% (adapter does not set it)
- Sanctum LST instruments: 0% (adapter not wired in orchestrator)

---

## 7. Conclusions for PassiveLedger Architecture

| Passive Event                      | Can IS synthesise without live listener?      | What IS provides                                                         | What is missing                                                |
| ---------------------------------- | --------------------------------------------- | ------------------------------------------------------------------------ | -------------------------------------------------------------- |
| CeFi perp funding receipt          | NO — needs MTDS `derivative_ticker` for rates | PERPETUAL InstrumentRecord (base_asset, margin_type)                     | Actual funding rate timeseries (MTDS) + funding interval       |
| DeFi perp funding receipt          | NO — needs MTDS `perp_funding`                | PERPETUAL InstrumentRecord + source_archive_url_template                 | Rate timeseries (MTDS)                                         |
| DeFi lending interest              | NO — needs MTDS `lending_indices`             | LENDING InstrumentRecord (pool_address, atoken_address)                  | Rate timeseries (MTDS)                                         |
| LST staking reward                 | NO — needs MTDS `lst_rates`                   | YIELD_BEARING/STAKING InstrumentRecord + source_archive_url_template     | Rate timeseries (MTDS)                                         |
| Solana native staking reward       | NO — needs MTDS `native_staking_rates`        | STAKING InstrumentRecord (SOL mint, decimals)                            | Per-epoch APY (MTDS/Solana RPC)                                |
| TradFi futures cash settlement     | YES from IS                                   | CanonicalFuturesContract (expiry_date, settlement_date, lifecycle_phase) | Settlement mark price (MTDS tick data)                         |
| TradFi futures physical settlement | PARTIAL                                       | CanonicalFuturesContract (derives physical from root)                    | settlement_style not on InstrumentRecord; delivery logistics   |
| American option early exercise     | NO                                            | CALL/PUT OptionType on InstrumentRecord                                  | exercise_style field ABSENT; exercise timing non-deterministic |
| Equity dividend                    | NO — nothing in IS parquet                    | CanonicalCorporateAction in-memory only, NOT persisted                   | Entire dividend schedule                                       |

**Verdict**: IS is NECESSARY but NOT SUFFICIENT for PassiveLedger synthesis. IS provides the instrument universe,
carry-rate source URLs, and TradFi settlement dates. The actual rate timeseries (the amounts for accrual-based passive
events) all flow from MTDS. The PassiveLedger must consume both IS InstrumentRecord parquet and MTDS carry-rate parquets
to synthesise passive P&L events. Three fields are structurally absent from InstrumentRecord and require schema
additions (exercise_style, settlement_style, dividend_schedule) before American exercise and dividend passive events can
be synthesised at all.
