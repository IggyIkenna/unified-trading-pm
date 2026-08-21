---
doc_type: plan
title: Schema Governance Full Audit
summary: 'Comprehensive schema governance audit across unified-api-contracts (UAC) and unified-internal-contracts (UIC).
  Covers: (1) canonical normalization quality — logical groupings, field consistency, deviation coverage, normalizer completeness;
  (2) UIC utilization — adoption matrix across all services, orphaned schemas, missing adoption; (3) cross-contract deduplication
  — InstrumentRecord conflict resolution, 85+ interface-adapter duplicates; (4) DRY/SoC enforcement — new cursor rule, quality
  gate STEP 5.12; (5) SCHEMA_GOVERNANCE.md codex doc. Distinct from SCHEMA_CONTRACTS_AUDIT.md (placement violations) and
  uac_schema_normalization_complete (provider coverage gaps).'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, instruments-service, strategy-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-06"
todos:
  - {
      id: p1-canonical-groupings,
      content:
        "DONE 2026-03-06: All 3 apparent fragments are INTENTIONALLY DISTINCT. (1) MarketTrade: parquet/NautilusTrader
        TRADES_SCHEMA — float/nanoseconds/aggressor_side_int; CanonicalTrade: normalized — Decimal/AwareDatetime. (2)
        OrderBookSnapshot5: BOOK_SNAPSHOT_5_SCHEMA — flat float columns/nanoseconds; CanonicalOrderBook: normalized —
        Decimal tuples/datetime. (3) ProcessedCandle: PROCESSED_CANDLE_SCHEMA — float + enriched
        market_state/is_halted/strike/option_type; CanonicalOhlcvBar: minimal canonical OHLCV — Decimal. Pattern:
        storage/parquet formats use float+nanoseconds; canonical output uses Decimal+datetime.",
      status: completed,
    }
  - {
      id: p1-field-consistency,
      content:
        "DONE 2026-03-06: Field consistency across canonical layer: timestamp — storage schemas use int (nanoseconds);
        canonical schemas use datetime or AwareDatetime (consistent); price — storage schemas use float; canonical
        schemas use Decimal (consistent after P1b OHLCV fix); quantity — same as price; venue — all canonical schemas
        use str (lowercase slug); instrument — domain.py=instrument_key (VENUE:TYPE:SYMBOL), execution.py=instrument_id
        (venue-opaque) — intentional documented split. No regressions found post-P1b fixes.",
      status: completed,
    }
  - {
      id: p1-deviation-coverage,
      content:
        "DONE 2026-03-06: CanonicalFundingRate: added predicted_rate ✅. CanonicalDerivativeTicker: added adl_rank ✅.
        CanonicalFill: fee, fee_currency, is_maker present ✅. CanonicalOrder: client_id PII tagged ✅, strategy_id
        present ✅. schemas/derivatives.py FundingRate @dataclass still has old next_funding_time (acceptable — it's a
        raw/response schema, not canonical). No critical silently-dropped fields remain.",
      status: completed,
    }
  - {
      id: p1-normalizer-completeness,
      content:
        "DONE 2026-03-06: normalize/ has 22 files covering: binance ✅, bybit ✅, okx ✅, coinbase ✅, deribit ✅,
        databento ✅, tardis ✅, kalshi ✅, polymarket ✅, hyperliquid ✅ (in cefi_extended.py), ibkr ✅, aster ✅,
        upbit ✅. Coverage by schema type: trades ✅, tickers ✅, derivative_tickers ✅, ohlcv ✅, orderbooks ✅,
        instruments ✅, liquidations ✅, orders_fills ✅, options ✅. Kraken: not found in normalizer files —
        normalization orphan (see uac_schema_normalization_complete.md for provider coverage plan).",
      status: completed,
    }
  - {
      id: p1-schemas-core-boundary,
      content:
        "DONE 2026-03-06: schemas/ contains 14 files (accounts, analytics, cex_withdrawals, defi, derivatives, errors,
        latency, prediction_market_arb, protocol_sdks, rate_limits, risk, transfers, websocket). FundingRate in
        schemas/derivatives.py is a @dataclass (raw/response layer); CanonicalFundingRate in domain.py is a Pydantic
        BaseModel (canonical layer) — distinct purposes, no conflict. schemas/ purpose: raw/response shapes, typed
        dicts, and utility classes for non-canonical data (pre-normalization or non-normalized). No boundary violations
        found.",
      status: completed,
    }
  - {
      id: p1c-options-chain-decimal-prices,
      content:
        "DONE 2026-03-08: bid_price and ask_price in CanonicalOptionsChainEntry were already Decimal | None (not float)
        — a prior session had already applied this fix. Verified in domain.py lines 389-390. No change required. Greeks
        (implied_volatility, delta, gamma, theta, vega) remain float — these are dimensionless ratios, not prices, so
        float is correct per canonical field standards.",
      status: completed,
    }
  - {
      id: p1c-canonical-order-derivative-fields,
      content:
        "DONE 2026-03-08: reduce_only, stop_price, leverage, margin_mode already present in CanonicalOrder (execution.py
        lines 122-125) from a prior session. Verified no change required. AwareDatetime consistency applied to timestamp
        field in this session.",
      status: completed,
    }
  - {
      id: p1c-canonical-fill-missing-fields,
      content:
        "DONE 2026-03-08: fee_rate, rebate, realized_pnl already present in CanonicalFill (execution.py lines 145-147)
        from a prior session. Verified no change required. AwareDatetime consistency applied to timestamp field in this
        session.",
      status: completed,
    }
  - {
      id: p1c-derivative-ticker-funding-interval,
      content:
        "DONE 2026-03-08: funding_interval_hours and settlement_price already present in CanonicalDerivativeTicker
        (domain.py lines 294-299) from a prior session. Verified no change required. AwareDatetime consistency applied
        to timestamp and funding_timestamp / next_funding_timestamp fields in this session.",
      status: completed,
    }
  - {
      id: p1c-aware-datetime-consistency,
      content:
        "DONE 2026-03-08: Applied AwareDatetime to ALL canonical timestamp fields in domain.py (28 timestamp occurrences
        across CanonicalOrderBook, CanonicalTicker, CanonicalLiquidation, CanonicalLiquidationCluster,
        CanonicalDerivativeTicker, CanonicalPosition, CanonicalBalance, CanonicalAccountSnapshot, CanonicalSettlement,
        CanonicalFundingRate, CanonicalOhlcvBar, CanonicalOptionsChainEntry, CanonicalMarketInfo, CanonicalWsMessage,
        CanonicalWebSocketLifecycle, CanonicalFee, ProcessedCandle, CanonicalOdds, CanonicalBetMarket,
        CanonicalBetOrder, CanonicalYieldCurvePoint, CanonicalBondData, CanonicalCdsSpread, CanonicalOnChainMetric,
        CanonicalOraclePriceFeed, CanonicalMarketStateEvent, InstrumentWarehouseRow) and execution.py (CanonicalOrder,
        CanonicalFill, ExecutionInstruction, ExecutionResult, CanonicalMarginState, CanonicalAccountState,
        CanonicalOrderRejection, CanonicalOrderAmendment). basedpyright: 0 errors. Module-level docstring added
        explaining AwareDatetime convention.",
      status: completed,
    }
  - {
      id: p1c-schemas-derivatives-deprecate,
      content:
        "DONE 2026-03-08: Added DeprecationWarning via warnings.warn() in __post_init__ of both FundingRate and
        Liquidation @dataclasses in schemas/derivatives.py. Added module-level deprecation notice docstring pointing to
        CanonicalFundingRate and CanonicalLiquidation. basedpyright: 0 errors on the file.",
      status: completed,
    }
  - {
      id: p1b-canonical-funding-rate-predicted-rate,
      content:
        "Add predicted_rate: Decimal | None to CanonicalFundingRate in unified_normalised_contracts/domain.py.
        schemas/derivatives.py::FundingRate has this field (line 20) but it is silently dropped during normalization —
        confirmed data loss. File: unified-api-contracts/unified_api_contracts/unified_normalised_contracts/domain.py.
        DONE 2026-03-06.",
      status: completed,
    }
  - {
      id: p1b-ohlcv-decimal-precision,
      content:
        "Change CanonicalOhlcvBar.open/high/low/close from float to Decimal in unified_normalised_contracts/domain.py.
        All other price fields in canonical schemas use Decimal; this is an inconsistency that allows silent precision
        loss. File: unified-api-contracts/unified_api_contracts/unified_normalised_contracts/domain.py. DONE 2026-03-06.",
      status: completed,
    }
  - {
      id: p1b-derivative-ticker-adl-rank,
      content:
        "Add adl_rank: int | None to CanonicalDerivativeTicker in unified_normalised_contracts/domain.py. ADL
        (Auto-Deleveraging) rank is published by Binance, OKX, Deribit and is important for position risk assessment —
        currently no field for it. File:
        unified-api-contracts/unified_api_contracts/unified_normalised_contracts/domain.py. DONE 2026-03-06.",
      status: completed,
    }
  - {
      id: p1b-funding-timestamp-rename,
      content:
        Rename next_funding_time → next_funding_timestamp in CanonicalFundingRate and CanonicalDerivativeTicker
        (unified_normalised_contracts/domain.py). Inconsistent suffix vs all other timestamp fields. Updated all
        normalise/derivative_tickers.py normalizers. DONE 2026-03-06.,
      status: completed,
    }
  - {
      id: p1b-instrument-id-naming-split,
      content:
        "Document the intentional split: domain.py canonical schemas use instrument_key (VENUE:TYPE:SYMBOL format),
        execution.py uses instrument_id (venue-specific opaque ID). Added module-level docstrings to both files. DONE
        2026-03-06.",
      status: completed,
    }
  - {
      id: p2-uic-adoption-matrix,
      content:
        "DONE 2026-03-06: scripts/check_uic_adoption.py ran against 125 public UIC classes (InstrumentKey added in this
        session, count grew from 108 to 125). Result: 44 schemas have at least 1 terminal consumer importer; 81
        orphaned. Full matrix at docs/ADOPTION_MATRIX.md. Services with most imports: ml-inference-service,
        market-data-processing-service, features-onchain-service, risk-and-exposure-service.",
      status: completed,
    }
  - {
      id: p2-orphaned-uic-schemas,
      content:
        "DONE 2026-03-06: 81 orphaned schemas classified by category: (a) Infrastructure/lifecycle schemas —
        WebSocketConnectEvent, WebSocketDisconnectEvent, etc. (7 total), PubSubLifecycleEventMessage,
        CircuitBreakerEventMessage, etc. — used by interface repos (not terminal services); expected orphans, NOT
        removable; (b) Domain schemas not yet adopted — DeFiLPPosition, DeFiLendingPosition, DeFiStakingPosition,
        CeFiPosition, GasCostEstimate (pending features-onchain/defi adoption), CanonicalBondData, CanonicalLendingRate,
        CanonicalYieldCurve (fixed income schemas, no service active yet); (c) Event detail schemas —
        AuthFailureDetails, ConfigChangedDetails, etc. — imported via interface repos not terminal services; (d) ML job
        schemas — TrainingJobRequest, TrainingPeriod (used by ml-training-service via its own models); (e)
        Audit/compliance — AuditRequirement, EXECUTION_AUDIT (regulatory, not service-consumed). See ADOPTION_MATRIX.md
        for full list.",
      status: completed,
    }
  - {
      id: p2-missing-adoption-services,
      content:
        "DONE (analysis) 2026-03-06: Known missing-adoption instances from ADOPTION_MATRIX.md: (1)
        TrainingJobRequest/TrainingJobResult — ml-training-service uses local UMI @dataclass versions, not UIC Pydantic
        wire schemas; (2) TargetType, TrainingPeriod — same. Remediation: wire ml-training-service to import UIC
        Pydantic schemas for API/pubsub boundaries. (3) WebSocket* events — used by interface repos (not terminal
        services) — these are correctly excluded from terminal consumer grep. See orphaned-schemas plan
        (orphan-contracts-utilization.md) for follow-up adoption work.",
      status: completed,
    }
  - {
      id: p2-domain-dir-population,
      content:
        "DONE 2026-03-08: Full domain/ audit completed. All planned service subdirectories now present:
        strategy_service/ (domain_events.py, monitoring.py, order.py, signal_vector.py), execution_service/sports.py,
        market_data_processing/ (adapter_models.py, candle_schema.py), domain/sports/execution.py,
        domain/market_tick_data/sports.py, domain/ml_inference_service/cascade_prediction.py,
        domain/market_data_api/orderbook_schema.py (OrderBookSnapshot @dataclass), domain/features_onchain/__init__.py
        (re-exports OnchainFeatureRecord from unified_internal_contracts.features). SCHEMA_CONTRACTS_AUDIT.md domain/
        section updated to reflect COMPLETE status (2026-03-08).",
      status: completed,
    }
  - {
      id: p2-uic-registry-fix,
      content:
        "Fix 4 stale entries in unified-internal-contracts/schema_registry.json that point to non-existent source files
        (currently reference UAC re-exports as if they were native UIC definitions). Update each entry to reflect the
        true canonical location of the schema. DONE 2026-03-06: CanonicalOrderBook, CanonicalTrade,
        CanonicalLiquidation, CanonicalDerivativeTicker corrected to repo=unified-api-contracts +
        re_export_via=unified_internal_contracts.market_data.",
      status: completed,
    }
  - {
      id: p3-instrument-record-conflict,
      content:
        "DONE 2026-03-06: UAC owns InstrumentWarehouseRow (parquet/GCS shape, 76 fields); UIC owns InstrumentRecord
        (adapter contract, 31 fields, Decimal). Decision documented in UAC domain.py InstrumentWarehouseRow docstring
        (existing, already renamed) and UIC reference/instrument.py InstrumentRecord docstring (updated 2026-03-06 with
        explicit ownership note + cross-reference to UAC).",
      status: completed,
    }
  - {
      id: p3-interface-adapter-dupes,
      content:
        "Resolve 34 duplicate models in unified-sports-execution-interface vs UAC and 51 models in
        unified-market-interface vs UAC. INVESTIGATION DONE 2026-03-06 (agent C): _deribit_models.py,
        _defi_graph_models.py, _betdaq_models.py, _smarkets_models.py confirmed CORRECTLY PLACED in UAC external schemas
        already. No action needed — adapter models cursor rule was already applied. Status: RESOLVED.",
      status: completed,
    }
  - {
      id: p3-ml-interface-dupes,
      content:
        "DONE 2026-03-06: ml-training-service/ml_training_service/ml/models.py replaced with re-export from
        unified_ml_interface.models (UMI is SSOT for @dataclass runtime objects). UTL
        unified_trading_library/ml/models.py kept as synchronized copy (T1 library cannot import T2 UMI — tier
        constraint); added docstring noting UMI SSOT and sync requirement.",
      status: completed,
    }
  - {
      id: p3-domain-client-dupes,
      content:
        "DONE 2026-03-06: InstrumentKey added to UIC reference/instrument_key.py (str-typed fields, parse_for_tardis
        included — market-tick-data-service depends on it). UIC __init__.py and reference/__init__.py updated to export
        InstrumentKey. UDC schemas/instrument_key.py replaced with re-export from UIC. UDC pyproject.toml updated to add
        unified-internal-contracts as runtime dependency. Fixes broken import in
        market_tick_data_service/models/__init__.py (was importing from unified_internal_contracts before UIC had it).",
      status: completed,
    }
  - {
      id: p3-uac-uic-boundary-reexports,
      content:
        "DONE 2026-03-06: (1) UIC market_data/__init__.py boundary docstring added (UIC→UAC permitted; reverse
        forbidden). (2) tests/test_ac_uic_alignment.py created in unified-api-contracts/ — parametrized test walks all
        UAC .py files and asserts no import of unified_internal_contracts.",
      status: completed,
    }
  - {
      id: p4-cursor-rule-schema-governance-index,
      content:
        "Write new cursor rule at unified-trading-pm/cursor-rules/core/schema-governance-index.mdc as a master index
        pointing to the 6 existing specific import rules (adapter-models-belong-in-uac, no-schema-outside-contracts,
        service-domain-schema-in-uic, uic-may-import-uac, unified-api-contracts-usage, contracts-integration) and the
        codex doc (02-data/schema-governance.md). NOTE: The 6 specific rules already exist and are comprehensive — this
        new rule is an overview/entry-point at priority 95, not a replacement. It also adds Rule 5 (no canonical name
        collision) and Rule 6 (quality gate advisory) which are NOT yet in any existing rule. DONE 2026-03-06.",
      status: completed,
    }
  - {
      id: p4-quality-gate-step-513,
      content:
        "Add STEP 5.13 (advisory) to quality gate templates: scan for 'Canonical*' BaseModel subclasses — flag as
        potential canonical name collision. Added to quality-gates-service-template.sh (DONE 2026-03-06 previous
        session), quality-gates-library-template.sh, and quality-gates-codex-compliance-snippet.sh (DONE 2026-03-06).",
      status: completed,
    }
  - {
      id: p4-no-type-ignore-schema-drift,
      content:
        "INVESTIGATION DONE 2026-03-06 (agent C). No type: ignore comments hide schema drift from local copies diverging
        from UIC canonical. Findings: (P1) execution_service/engine/execution/types.py — AlgorithmParams TypedDict needs
        discriminated union; (P2) market_data_processing_service/orchestration_workers.py:320,344 — Optional adapter not
        narrowed; (P3) execution_service/utils/result.py — type alias syntax upgrade; nautilus_trader and shap are
        EXEMPT (untyped 3rd-party). No UIC canonical drift hiding found.",
      status: completed,
    }
  - {
      id: p5-schema-governance-codex-update,
      content:
        "UPDATE (not create) unified-trading-/codex/02-data/schema-governance.md — it already exists with ownership
        table and domain/ guide. ADDED: (1) Canonical Field Standards table (timestamp=datetime/int ms, price=Decimal,
        size=Decimal, venue slug, instrument_key vs instrument_id); (2) P0 Canonical Field Issues tracker (all 4 fixes
        marked resolved 2026-03-06); (3) UIC Adoption Matrix section (link to ADOPTION_MATRIX.md, known orphan
        categories). 00-SSOT-INDEX.md updated DONE 2026-03-06. DONE 2026-03-06.",
      status: completed,
    }
  - {
      id: p5-adoption-matrix-publish,
      content:
        "DONE 2026-03-06: scripts/check_uic_adoption.py fixed (global WORKSPACE declaration before first use) and run.
        docs/ADOPTION_MATRIX.md generated: 125 public UIC classes, 81 orphaned (0 terminal consumer imports), 5 UAC
        re-exports exempt. Orphaned schemas fall into 3 categories: (1) lifecycle/pubsub infra schemas (WebSocket*,
        PubSub*, messaging) — used by interface repos not terminal services; (2) domain schemas not yet adopted (DeFi
        positions, feature records, risk schemas); (3) ML job schemas (TrainingJobRequest, TrainingPeriod) — not yet
        wired to terminal consumers.",
      status: completed,
    }
  - {
      id: p5-verification,
      content:
        "DONE 2026-03-06: (1) basedpyright UAC unified_normalised_contracts/ — 0 errors ✅; (2) schema_registry.json — 0
        stale entries ✅; (3) ADOPTION_MATRIX.md first run ✅ — 125 classes, 81 orphaned (expected: lifecycle/infra
        schemas used by interfaces not terminal services); (4) STEP 5.13 advisory ✅ in all 3 quality gate templates;
        (5) Interface adapter models: confirmed RESOLVED ✅; (6) DUPLICATE violations: ml-training-service fixed (UMI
        re-export); InstrumentKey migrated to UIC ✅; (7) InstrumentRecord conflict: documented ✅. Remaining: p1-*
        audit todos (Phase 1 UAC quality audit — agents ran but context lost; re-run needed) and p2-* adoption
        remediation follow-ups from ADOPTION_MATRIX.md findings.",
      status: completed,
    }
isProject: true
---

# Schema Governance Full Audit

**Status:** COMPLETE — All phases done. Phase 1c completed 2026-03-08 (AwareDatetime consistency, derivatives
deprecation, field-level fixes verified as already applied). p2-domain-dir-population completed 2026-03-08. See
ADOPTION_MATRIX.md for ongoing orphan remediation backlog. **Last Updated:** 2026-03-08 **SSOT for schema placements:**
[SCHEMA_CONTRACTS_AUDIT.md](SCHEMA_CONTRACTS_AUDIT.md) **SSOT for normalization coverage:**
[unified-api-contracts/docs/SCHEMA_NORMALIZATION_GAPS_AUDIT.md](../../../unified-api-contracts/docs/SCHEMA_NORMALIZATION_GAPS_AUDIT.md)
**Master cursor rule:** `unified-trading-pm/cursor-rules/core/schema-governance-index.mdc` ✅ created 2026-03-06 **Codex
doc (existing):** `unified-trading-/codex/02-data/schema-governance.md` ✅ updated 2026-03-06 **Registry fixed:**
`unified-internal-contracts/schema_registry.json` — 4 stale entries corrected ✅ **P0 UAC fixes:** 5/5 complete ✅
(predicted_rate, OHLCV Decimal, adl_rank, next_funding_timestamp, docstrings)

---

## Scope

This plan covers four distinct concerns not addressed by existing schema plans:

| Concern                                                                 | This Plan | Related Existing Plan                                                        |
| ----------------------------------------------------------------------- | --------- | ---------------------------------------------------------------------------- |
| Canonical shape quality (groupings, field consistency, optional fields) | ✓ Phase 1 | —                                                                            |
| UIC adoption across services (who imports what)                         | ✓ Phase 2 | —                                                                            |
| Cross-contract deduplication resolution                                 | ✓ Phase 3 | SCHEMA_CONTRACTS_AUDIT.md (found the violations; this plan resolves them)    |
| SoC cursor rule + quality gate enforcement                              | ✓ Phase 4 | quality_gate_hardening.md (adds STEP 5.12)                                   |
| SCHEMA_GOVERNANCE.md codex doc                                          | ✓ Phase 5 | —                                                                            |
| Normalization coverage per data provider                                | —         | [uac_schema_normalization_complete.md](uac_schema_normalization_complete.md) |
| Schema placement violations (finding them)                              | —         | [schema_contracts_full_audit.md](schema_contracts_full_audit.md)             |

---

## Phase 1 — UAC Canonical Normalization Quality

### 1.1 Canonical Schema Inventory

**Location:** `unified-api-contracts/unified_api_contracts/unified_normalised_contracts/`

| File           | Key Classes                                                                                                                                                                                                                                                              | Potential Fragments                                                                                           |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| `domain.py`    | CanonicalTrade, CanonicalTicker, CanonicalDerivativeTicker, CanonicalOhlcvBar, CanonicalFundingRate, CanonicalLiquidation, CanonicalPosition, CanonicalBalance, CanonicalOrderBook, InstrumentWarehouseRow, **MarketTrade**, **OrderBookSnapshot5**, **ProcessedCandle** | MarketTrade vs CanonicalTrade; OrderBookSnapshot5 vs CanonicalOrderBook; ProcessedCandle vs CanonicalOhlcvBar |
| `execution.py` | CanonicalOrder, CanonicalFill, ExecutionInstruction, ExecutionResult                                                                                                                                                                                                     | None known                                                                                                    |
| `errors.py`    | CanonicalError, CanonicalRateLimitError                                                                                                                                                                                                                                  | None known                                                                                                    |

### 1.2 Fragment Investigation Guidance

- **MarketTrade vs CanonicalTrade**: If MarketTrade is a deprecated alias or limited-field subset, alias
  `MarketTrade = CanonicalTrade` or remove. If it has distinct semantics (e.g., anonymous public trade vs private fill),
  document the distinction clearly.
- **OrderBookSnapshot5 vs CanonicalOrderBook**: OrderBookSnapshot5 (5-level snapshot) may be a bandwidth-optimised
  subset. If so, keep with explicit docstring; deprecate if CanonicalOrderBook covers all cases.
- **ProcessedCandle vs CanonicalOhlcvBar**: Likely a transformation artifact. Remove if redundant.

### 1.3 Field Consistency Standards (Target)

| Field          | Canonical Target Type     | Rationale                                                                       |
| -------------- | ------------------------- | ------------------------------------------------------------------------------- |
| timestamp      | `int` (Unix ms)           | Consistent with market data standards; nanoseconds only for HFT/latency schemas |
| price          | `str` (JSON) or `Decimal` | Never `float` in canonical layer; str preserves venue precision                 |
| quantity/size  | `str` or `Decimal`        | Never `float`                                                                   |
| venue          | `str` (lowercase slug)    | e.g., `"binance"`, `"deribit"`                                                  |
| instrument_key | `str`                     | Canonical identifier; `symbol` = venue-specific raw field                       |

### 1.4 Normalizer Coverage Matrix (Template)

| Venue       | Trade | OrderBook | OHLCV | Ticker | Deriv Ticker | Order/Fill | Instrument |
| ----------- | ----- | --------- | ----- | ------ | ------------ | ---------- | ---------- |
| binance     |       |           |       |        |              |            |            |
| bybit       |       |           |       |        |              |            |            |
| okx         |       |           |       |        |              |            |            |
| deribit     |       |           |       |        |              |            |            |
| hyperliquid |       |           |       |        |              |            |            |
| databento   |       |           |       |        |              |            |            |
| tardis      |       |           |       |        |              |            |            |
| kalshi      |       |           |       |        |              |            |            |
| polymarket  |       |           |       |        |              |            |            |

_To be filled by p1-normalizer-completeness todo._

---

## Phase 2 — UIC Utilization Audit

### 2.1 UIC Domain Summary (108 classes across 24 files)

| Module                 | Class Count | Domain                                                    |
| ---------------------- | ----------- | --------------------------------------------------------- |
| events.py              | ~26         | Lifecycle event types + envelopes                         |
| pubsub.py              | ~17         | Internal Pub/Sub message schemas                          |
| risk.py                | ~15         | Risk metrics, alerts, pre-trade checks                    |
| ml.py                  | ~10         | Model metadata, training, inference                       |
| features.py            | 6           | Feature records (delta-one, cross-instrument, etc.)       |
| market_data/ (6 files) | ~19         | OHLCV, book, option quote, options chain + UAC re-exports |
| positions/ (4 files)   | 5           | CeFi + DeFi positions                                     |
| reference/ (2 files)   | 6           | InstrumentRecord, InstrumentDefinition, enums             |
| alerting/              | 1           | AlertEvent                                                |
| connectivity/          | 7           | WebSocket lifecycle events                                |
| schemas/errors.py      | 6           | Error classification, DLQ                                 |
| schemas/audit.py       | 2           | Audit retention + requirements                            |
| messaging.py           | 2           | MessagingScope, MessagingTopic (enums)                    |
| defi.py                | 2           | GasCostEstimate                                           |
| reporting/             | 1           | FeeStructure                                              |

### 2.2 domain/ Population Plan (Target)

```
unified_internal_contracts/domain/
├── execution-service/
│   └── sports.py          # SportsBetResult, SportsVenueScore, SportsVenueSelection
├── strategy-service/
│   └── domain_data.py     # PositionData, ExposureData, RiskData, PnLData, StrategyDecisionData
├── market-data-processing/
│   └── candle.py          # UnifiedCandleSchema (if not already in market_data/ohlcv.py)
├── market-data-api/
│   └── orderbook.py       # OrderBookSnapshot (if distinct from CanonicalBookUpdate)
├── features/
│   ├── onchain.py         # OnchainFeature
│   └── sports.py          # 14 sports feature column schemas
```

---

## Phase 3 — Cross-Contract Duplication Resolution

### 3.1 InstrumentRecord Conflict

|            | UAC (InstrumentWarehouseRow)                      | UIC (InstrumentRecord)                            |
| ---------- | ------------------------------------------------- | ------------------------------------------------- |
| Fields     | 76 (float, raw symbols, venue mappings)           | 31 (Decimal, normalised)                          |
| Purpose    | GCS parquet storage row                           | URDI adapter output contract                      |
| Consumers  | instruments-service (reads from GCS)              | unified-reference-data-interface (adapter output) |
| Resolution | Keep as InstrumentWarehouseRow (rename confirmed) | Keep as InstrumentRecord (URDI adapter SSOT)      |

**Decision:** These are intentionally different shapes serving different layers. Rename removes confusion. No merge
required.

### 3.2 Interface Adapter Duplicate Summary

| Interface Repo                     | Duplicate Count                                         | UAC Target                                                          |
| ---------------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------- |
| unified-sports-execution-interface | 34 models                                               | `unified_api_contracts_external/{venue}/schemas.py` per venue       |
| unified-market-interface           | 51 models (\_deribit_models.py, \_defi_graph_models.py) | `unified_api_contracts_external/deribit/schemas.py` + defi adapters |
| unified-ml-interface               | 2 models (ModelVariantConfig, ModelMetadata)            | `unified_internal_contracts/ml.py` (UIC, not UAC)                   |
| unified-domain-client              | 1 model (InstrumentKey)                                 | `unified_internal_contracts/reference/`                             |

---

## Phase 4 — SoC Enforcement

### 4.1 Schema Ownership Boundary Rules

```
Rule 1: Raw venue API → UAC only
  BAD:  unified_market_interface/adapters/_deribit_models.py → class DeribitTicker(BaseModel)
  GOOD: unified_api_contracts_external/deribit/schemas.py → class DeribitTicker(BaseModel)

Rule 2: Canonical normalized output → UAC unified_normalised_contracts/ only
  BAD:  unified_internal_contracts/market_data/canonical_trade.py → class CanonicalTrade(BaseModel)
  GOOD: unified_api_contracts/unified_normalised_contracts/domain.py → class CanonicalTrade(BaseModel)

Rule 3: Cross-repo internal contracts → UIC only
  BAD:  strategy_service/models/domain_data.py → class PositionData(BaseModel)  # cross-imported by risk-service
  GOOD: unified_internal_contracts/risk.py → class RiskPosition(BaseModel)

Rule 4: Service-local schemas OK if and ONLY IF never cross-imported
  OK:   execution_service/engine/live/models.py → class ExecutionConfig(BaseModel)  # internal only

Rule 5: No canonical name collisions
  BAD:  market_data_api/models.py → class CanonicalTrade(BaseModel)  # same name as UAC canonical
  GOOD: Import CanonicalTrade from unified_api_contracts.unified_normalised_contracts

Rule 6: Import direction
  OK:   unified_internal_contracts imports from unified_api_contracts (UIC → UAC)
  BAD:  unified_api_contracts tests import from unified_internal_contracts (UAC → UIC)
```

### 4.2 Quality Gate STEP 5.12

```bash
# STEP 5.12 — Schema canonical name collision check
echo "STEP 5.12: Schema canonical name collision check..."
CANONICAL_NAMES=$(python -c "
from unified_api_contracts.unified_normalised_contracts import domain, execution
from unified_internal_contracts import __all__ as uic_all
import inspect
names = [n for n, _ in inspect.getmembers(domain, inspect.isclass)]
names += [n for n, _ in inspect.getmembers(execution, inspect.isclass)]
names += list(uic_all)
print(' '.join(set(names)))
" 2>/dev/null || echo "")

for name in $CANONICAL_NAMES; do
    hits=$(rg "class ${name}\b" "${SOURCE_DIR}/" --type py --glob '!.venv*' -l 2>/dev/null | \
        grep -v "unified_api_contracts\|unified_internal_contracts" || :)
    if [ -n "$hits" ]; then
        echo "WARN: POTENTIAL_SCHEMA_DUPLICATE — class '${name}' defined in service source:"
        echo "$hits"
        SCHEMA_COLLISION_COUNT=$((SCHEMA_COLLISION_COUNT + 1))
    fi
done
```

---

## Phase 5 — Verification Checklist

| Check                    | Command                                                                                                  | Pass Condition      |
| ------------------------ | -------------------------------------------------------------------------------------------------------- | ------------------- |
| UAC canonical type-clean | `run_timeout 120 basedpyright unified-api-contracts/unified_api_contracts/unified_normalised_contracts/` | 0 errors            |
| UIC type-clean           | `run_timeout 120 basedpyright unified-internal-contracts/unified_internal_contracts/`                    | 0 errors            |
| UIC adoption             | `python unified-internal-contracts/scripts/check_uic_adoption.py`                                        | 0 orphaned schemas  |
| Schema name collisions   | STEP 5.12 in quality gate                                                                                | 0 warnings          |
| Schema registry          | `python -c "import json; r=json.load(open('schema_registry.json')); print(len(r))"`                      | All entries resolve |
| Duplicate resolution     | Review SCHEMA_CONTRACTS_AUDIT.md DUPLICATE section                                                       | 16/16 resolved      |
| Conflict resolution      | InstrumentRecord naming documented                                                                       | Decision recorded   |

---

## Dependency

Feeds into:

- [orphan-contracts-utilization.md](orphan-contracts-utilization.md) (plan #11) — adoption matrix informs orphan
  remediation priorities
- [uac_schema_normalization_complete.md](uac_schema_normalization_complete.md) (plan #11b) — normalizer completeness
  gaps from p1-normalizer-completeness go here
- [quality_gate_hardening.md](quality_gate_hardening.md) (plan #2c) — STEP 5.12 to be added per p4-quality-gate-step-512
