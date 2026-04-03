---
title: Instrument Schema Cohesion & Market Hours Infrastructure
status: active
priority: P0
created: 2026-03-31
locked_by: live-defi-rollout
locked_since: 2026-03-31
owner: agent
---

# Instrument Schema Cohesion & Market Hours Infrastructure

> **Conflict resolution**: Phase 2A/2B adapter updates overlap with venue_availability_ssot Phase 3 and
> multichain_defi_expansion adapter files. This plan owns field renames and enum values. Phase 3A (MTDS market hours)
> must run AFTER mtds_canonical_sharding_alignment Phase 2 completes its orchestrator.py refactor.

## Context

The instrument definition layer has two systemic problems:

1. **Schema incoherence** — InstrumentRecord (internal, instruments-service writes) and CanonicalInstrument (external,
   warehouse shape) use different enum values, field names, and numeric types for the same concepts. Parquet flattens
   everything to strings with no documented conversion layer. Downstream services silently work around mismatches.

2. **Missing market hours infrastructure** — InstrumentRecord has `is_trading_day`, `regular_open_utc`,
   `regular_close_utc`, `early_close_utc` but is missing `pre_market_open_utc`, `post_market_close_utc`,
   `holiday_calendar`, and `timezone`. MTDS doesn't check trading days before fetching. ML-training has hardcoded
   holiday lists. Execution-service doesn't gate orders on market hours. Strategy-service only checks hours in one
   strategy.

### Pre-Audit Manifest (Blast Radius)

**Schema consumers (25+ repos, 95+ imports of InstrumentRecord):**

| Mismatch                       | InstrumentRecord                       | CanonicalInstrument                              | Parquet                 | Affected        |
| ------------------------------ | -------------------------------------- | ------------------------------------------------ | ----------------------- | --------------- |
| instrument_type values         | lowercase (spot, perp, futures) 9 vals | UPPERCASE (SPOT_PAIR, PERPETUAL, FUTURE) 24 vals | string                  | 40+ files       |
| tick_size/strike/lot_size type | Decimal                                | float                                            | string                  | 20+ files       |
| available_since naming         | available_since                        | available_from_datetime                          | available_from_datetime | 10+ files       |
| lot_size naming                | lot_size                               | min_size                                         | min_size                | 10+ files       |
| asset_class type               | AssetClass enum                        | str                                              | string                  | 7+ files        |
| option_type type               | str                                    | OptionType enum                                  | string                  | 5+ files        |
| settle_asset                   | removed (derivable)                    | settle_asset (explicit)                          | settle_asset            | 45+ normalizers |
| MarginType                     | enum defined, no field                 | inverse: bool                                    | N/A                     | Dead code       |

**Market hours consumers:**

| Service                       | Current State                                                    | Gap                                                                  |
| ----------------------------- | ---------------------------------------------------------------- | -------------------------------------------------------------------- |
| instruments-service/databento | Populates regular_open/close_utc, early_close_utc, auction times | Missing pre/post-market, holiday_calendar, timezone                  |
| MTDS                          | Loads instrument config (never queries it)                       | Fetches on closed markets, can't distinguish closed vs broken        |
| MDPS                          | Full 5-level market state detection                              | Expects pre_market_open, post_market_close — not in InstrumentRecord |
| ML training                   | Hardcoded \_US_HOLIDAYS_2023/2024                                | Will break 2025+; should read is_trading_day                         |
| Strategy                      | Only TradFi momentum checks hours                                | Other strategies blind to market hours                               |
| Execution                     | Market hours for data alignment only                             | No order gating on closed markets                                    |
| Risk                          | No market hours awareness                                        | Pre-trade checks don't include market-open validation                |

### Dependency DAG

```
Phase 1: UAC schema fixes (InstrumentRecord + CanonicalInstrument + parquet alignment)
    ↓ QG gate
Phase 2: instruments-service populates new fields + adapts to unified types
    ↓ QG gate
Phase 3: Downstream consumers (MTDS, MDPS, ML, strategy, execution, risk) — PARALLEL
    ↓ QG gate
Phase 4: Workspace-wide validation
```

---

## Phase 1: UAC Schema Unification [SEQUENTIAL — all in unified-api-contracts]

### 1A. Unify InstrumentType enum

- [x] [AGENT] P0. Merge the two InstrumentType enums into ONE in `internal/reference/instrument.py`. Use UPPERCASE
      values (canonical standard). Map: `spot`→`SPOT_PAIR`, `perp`→`PERPETUAL`, `futures`→`FUTURE`, `option`→`OPTION`,
      `pool`→`POOL`, `lending_market`→`LENDING`, `lst`→`LST`, `yield`→`YIELD_BEARING`, `etf`→`ETF`. Add missing values
      from canonical enum: `EQUITY`, `COMMODITY`, `CURRENCY`, `INDEX`, `BOND`, `A_TOKEN`, `DEBT_TOKEN`, `STAKING`,
      `PREDICTION_MARKET`, `EXCHANGE_ODDS`, `FIXED_ODDS`, `PROP`, `CDS`, `SPOT_ASSET`. Remove PERP legacy alias from
      canonical enum (consolidate to PERPETUAL). Delete the duplicate InstrumentType from
      `canonical/domain/reference/__init__.py` — re-export from internal.
- [x] [AGENT] P0. Update ALL instrument_type string literals across UAC source (normalizers, external/, registry/,
      tests). Search: `"spot"`, `"perp"`, `"futures"`, `"lending_market"`, `"yield"` — replace with enum references or
      UPPERCASE strings. ~100 locations. (All remaining string literals in UAC are already UPPERCASE; normalize.py files
      use lowercase only as lookup keys mapping TO uppercase, which is correct translation-table behavior.)

### 1B. Unify field names

- [x] [AGENT] P0. Rename InstrumentRecord `available_since` → `available_from_datetime` and `available_to` →
      `available_to_datetime` to match parquet schema. Update instruments-service adapters that set these fields.
- [x] [AGENT] P0. Rename InstrumentRecord `lot_size` → `min_size` to match parquet schema.
- [x] [AGENT] P1. Add `settle_asset: str | None = None` back to InstrumentRecord. It was removed as "derivable" but
      CanonicalInstrument has it, parquet has it, and 45+ normalizers populate it. Derivation logic is wrong for quanto
      contracts.

### 1C. Unify numeric types

- [x] [AGENT] P1. Change CanonicalInstrument `tick_size`, `min_size`, `strike` from `float | None` to `Decimal | None`
      to match InstrumentRecord. Parquet stores as string regardless — no data change. Update any code that constructs
      CanonicalInstrument with float values. (Already done: canonical/domain/reference/**init**.py lines 84-87 show
      `Decimal | None` for all three fields.)

### 1D. Unify enum usage

- [x] [AGENT] P1. Change InstrumentRecord `option_type: str | None` → `option_type: OptionType | None`. Re-export
      OptionType from internal alongside InstrumentRecord.
- [x] [AGENT] P1. Change CanonicalInstrument `asset_class: str | None` → `asset_class: AssetClass | None`. Re-export
      AssetClass from canonical alongside CanonicalInstrument.
- [x] [AGENT] P1. Remove dead MarginType enum OR add `margin_type: MarginType | None = None` to InstrumentRecord.
      Decision: add it — execution-service needs it for inverse/linear/quanto routing. Remove `inverse: bool` from
      CanonicalInstrument (replaced by margin_type).

### 1E. Add market hours fields to InstrumentRecord

- [x] [AGENT] P0. Add to InstrumentRecord: `pre_market_open_utc: str | None = None`,
      `post_market_close_utc: str | None = None`, `holiday_calendar: str | None = None` (exchange_calendars key, e.g.
      "XNYS"), `timezone: str | None = None` (e.g. "America/New_York"), `auction_open_utc: str | None = None`,
      `auction_close_utc: str | None = None`.
- [x] [AGENT] P0. Add matching columns to INSTRUMENTS_PARQUET_SCHEMA in `internal/domain/instruments/__init__.py`. All
      string type, nullable=True.
- [x] [AGENT] P0. Add matching fields to CanonicalInstrument (already has trading_hours_open/close, holiday_calendar,
      auction_open/close_utc — verify alignment and add any missing).
- [ ] [AGENT] P1. Update `instrument_validation.py` — require `holiday_calendar` and `timezone` for TradFi instruments
      (asset_class in {EQUITY, COMMODITY, FX, FIXED_INCOME}).

### 1F. Document serialization contract

- [x] [AGENT] P1. Add docstring to InstrumentRecord documenting the field name mapping to parquet columns
      (available_from_datetime, min_size, etc.) and type flattening (Decimal→str, enum→str.value,
      datetime→datetime64[ns]).

**QG gate: `cd unified-api-contracts && bash scripts/quality-gates.sh`**

---

## Phase 2: instruments-service Adapts to Unified Schema [SEQUENTIAL]

### 2A. Adapt adapters to new InstrumentType values

- [x] [AGENT] P0. Update ALL 25+ URDI adapters in `instruments_service/reference_data/adapters/` to use UPPERCASE
      InstrumentType enum values. Search for: `instrument_type="spot"` → `instrument_type=InstrumentType.SPOT_PAIR`,
      `"perp"` → `InstrumentType.PERPETUAL`, `"futures"` → `InstrumentType.FUTURE`, `"option"` →
      `InstrumentType.OPTION`, `"pool"` → `InstrumentType.POOL`, `"lending_market"` → `InstrumentType.LENDING`, `"lst"`
      → `InstrumentType.LST`, `"yield"` → `InstrumentType.YIELD_BEARING`, `"etf"` → `InstrumentType.ETF`. ~60 locations
      across adapters.

### 2B. Adapt field names

- [x] [AGENT] P0. Update all adapters: `available_since=` → `available_from_datetime=`, `lot_size=` → `min_size=`. Also
      update `available_to=` → `available_to_datetime=` where used. ~40 locations.
- [x] [AGENT] P0. Populate `settle_asset` in CeFi/TradFi adapters (Tardis, Databento, OKX, Binance, Bybit, Deribit,
      Coinbase). For spot: None. For linear derivatives: quote_asset. For inverse: base_asset.

### 2C. Populate new market hours fields

- [ ] [AGENT] P0. In databento.py adapter: populate `pre_market_open_utc`, `post_market_close_utc`, `holiday_calendar`,
      `timezone`, `auction_open_utc`, `auction_close_utc` from the existing `_EXCHANGE_HOURS` dict. Add pre/post-market
      times: NYSE/NASDAQ pre-market 04:00 ET, post-market 20:00 ET. CME: no distinct pre/post (near-24h session). Add
      `holiday_calendar` mapping: CME→"XCME", NYSE→"XNYS", NASDAQ→"XNAS", ICE→"IFEU", CBOE→"XCBO". Add `timezone`
      mapping: CME→"America/Chicago", NYSE/NASDAQ→"America/New_York", ICE→"Europe/London".
- [x] [AGENT] P1. In CeFi adapters (Tardis, Binance, Bybit, etc.): set `timezone="UTC"`, `holiday_calendar=None` (24/7
      markets). No pre/post-market concept.
- [x] [AGENT] P1. In DeFi adapters: same as CeFi — `timezone="UTC"`, no holidays.

### 2D. Use OptionType enum and MarginType

- [x] [AGENT] P1. Update OKX, Deribit, Databento adapters: `option_type="call"` → `option_type=OptionType.CALL`. Update
      Tardis, Bybit: populate `margin_type=MarginType.LINEAR` or `MarginType.INVERSE` based on contract type.

### 2E. Update orchestrator field name references

- [x] [AGENT] P0. Update `engine/orchestrator.py` and any other service code referencing old field names
      (`available_since`, `lot_size`).

**QG gate: `cd instruments-service && bash scripts/quality-gates.sh`**

---

## Phase 3: Downstream Consumers [PARALLEL — independent repos]

### 3A. MTDS: Skip closed markets

- [x] [AGENT] P0. In `market-tick-data-service/engine/orchestrator.py`: before fetching tick data for TradFi venues,
      load instrument definitions and check `is_trading_day`. If False, skip the fetch and log
      `"venue=%s: market closed (is_trading_day=False), skipping"`. Keep CeFi/DeFi unconditional (24/7).
- [ ] [AGENT] P1. Add diagnostic: when a TradFi venue returns 0 rows on a trading day, log WARNING (potential upstream
      issue). When 0 rows on non-trading day, log INFO (expected).

### 3B. MDPS: Read new fields from InstrumentRecord

- [x] [AGENT] P0. In `market-data-processing-service/app/utils/market_state_detector.py`: read `pre_market_open_utc` and
      `post_market_close_utc` from instrument metadata instead of expecting local-time
      `pre_market_open`/`post_market_close`. Parse ISO datetime string to UTC datetime. (Already done:
      market_state_detector.py lines 218-233 read `pre_market_open_utc` and `post_market_close_utc` directly from
      instrument_metadata dict.)
- [x] [AGENT] P1. Read `holiday_calendar` from instrument metadata instead of hardcoded `CALENDAR_MAPPING`. Fall back to
      CALENDAR_MAPPING if field is None (backwards compat during rollout). (Already done: market_state_detector.py line
      205 reads `holiday_calendar` from metadata with CALENDAR_MAPPING as fallback.)
- [x] [AGENT] P1. Read `timezone` from instrument metadata. Remove hardcoded timezone assumptions.

### 3C. ML training: Remove hardcoded holidays

- [ ] [AGENT] P0. In `ml-training-service/app/core/data_filters.py`: replace `filter_market_hours()` hardcoded NYSE
      09:30-16:00 ET with reading `regular_open_utc`/`regular_close_utc` from instrument metadata passed as parameter.
- [ ] [AGENT] P0. In `ml-training-service/app/core/mock_feature_generator.py`: remove `_US_HOLIDAYS_2023` and
      `_US_HOLIDAYS_2024` frozensets. Replace `_filter_trading_days()` with reading `is_trading_day` from instrument
      parquet for the date range.

### 3D. Strategy: Generalise market hours check

- [x] [AGENT] P1. Extract `_is_market_hours()` from `tradfi_momentum.py` into a shared utility in
      `strategy_service/engine/core/market_hours_utils.py`. All TradFi strategies should use it.
- [ ] [AGENT] P1. In strategy base class or config: add `market_hours_only: bool = True` default for TradFi strategies.
      DeFi/sports strategies default False.

### 3E. Execution: Add market-hours order gate

- [x] [AGENT] P0. In execution-service pre-trade flow: add market hours check. If `is_trading_day=False` or current time
      outside `regular_open_utc`/`regular_close_utc` (with `early_close_utc` override), reject TradFi orders with reason
      `"MARKET_CLOSED"`. CeFi/DeFi orders pass unconditionally.
- [ ] [AGENT] P1. Add expiry guard: if instrument `status=EXPIRED` or `expiry < now`, reject with reason
      `"INSTRUMENT_EXPIRED"`.

### 3F. Risk: Add market-hours pre-trade check

- [x] [AGENT] P1. In `risk-and-exposure-service/core/pre_trade_check_engine.py`: add a `market_hours_check` that reads
      instrument metadata. For TradFi instruments, fail pre-trade if market is closed. This is defence-in-depth
      (execution-service also checks, but risk should too).

### 3G. Update instrument_type references across all consumers

- [x] [AGENT] P0. Across ALL downstream repos: update any hardcoded lowercase instrument_type string comparisons to use
      UPPERCASE or the InstrumentType enum. Blast radius from pre-audit: execution-service, strategy-service,
      ml-training-service, features-\*, pnl-attribution-service, market-tick-data-service,
      market-data-processing-service. ~50 locations total. (Audited: no lowercase instrument_type string comparisons
      found in downstream service source files. All enum/string usage is already UPPERCASE.)

### 3H. Update field name references across all consumers

- [x] [AGENT] P0. Across ALL downstream repos: update `available_since` → `available_from_datetime`, `lot_size` →
      `min_size`, `settlement_asset` → `settle_asset` where referenced. Blast radius from pre-audit: execution-service
      (settle_asset reads from GCS — already correct), instruments-service URDI archive (settlement_asset — needs
      update).

### 3I. features-volatility-service: Remove local OptionType

- [x] [AGENT] P1. Delete local OptionType definition from features-volatility-service. Import from
      `unified_api_contracts` instead.

**QG gate: Run quality-gates.sh on EACH affected repo.**

---

## Phase 4: Workspace-Wide Validation [SEQUENTIAL]

- [ ] [AGENT] P0. Run `bash scripts/quality-gates.sh` on all affected repos: unified-api-contracts, instruments-service,
      market-tick-data-service, market-data-processing-service, ml-training-service, strategy-service,
      execution-service, risk-and-exposure-service, features-volatility-service, pnl-attribution-service,
      unified-trading-library, system-integration-tests.
- [ ] [AGENT] P0. Run instruments pipeline for all 3 categories (CEFI, DEFI, TRADFI) and verify: (a) all venues
      return >0 instruments, (b) new fields populated for TradFi, (c) parquet schema matches INSTRUMENTS_PARQUET_SCHEMA.
- [ ] [AGENT] P1. Run MTDS pipeline for a TradFi weekend date — verify it skips NYSE/NASDAQ/CME with "market closed" log
      instead of fetching 0 rows.

---

## Success Criteria

- [x] ONE InstrumentType enum (UPPERCASE, 24 values) used everywhere
- [x] ONE set of field names (available_from_datetime, min_size, settle_asset) across InstrumentRecord,
      CanonicalInstrument, and parquet
- [x] Decimal for financial precision (tick_size, strike, min_size) in both model classes
- [x] OptionType enum enforced in InstrumentRecord (not bare str)
- [x] MarginType field on InstrumentRecord (replaces inverse: bool)
- [x] Market hours fields (pre/post-market, holiday_calendar, timezone, auction times) on InstrumentRecord
- [ ] MTDS skips closed TradFi markets
- [ ] Execution-service rejects TradFi orders on closed markets
- [ ] ML training reads is_trading_day from instruments (no hardcoded holidays)
- [ ] All 12 affected repos pass QG
