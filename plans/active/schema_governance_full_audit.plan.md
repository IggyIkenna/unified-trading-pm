---
name: Schema Governance Full Audit
overview: "Comprehensive schema governance audit across unified-api-contracts (UAC) and unified-internal-contracts (UIC). Covers: (1) canonical normalization quality — logical groupings, field consistency, deviation coverage, normalizer completeness; (2) UIC utilization — adoption matrix across all services, orphaned schemas, missing adoption; (3) cross-contract deduplication — InstrumentRecord conflict resolution, 85+ interface-adapter duplicates; (4) DRY/SoC enforcement — new cursor rule, quality gate STEP 5.12; (5) SCHEMA_GOVERNANCE.md codex doc. Distinct from SCHEMA_CONTRACTS_AUDIT.md (placement violations) and uac_schema_normalization_complete (provider coverage gaps)."
todos:
  # PHASE 1 — UAC Canonical Normalization Quality
  - id: p1-canonical-groupings
    content: "Audit unified_normalised_contracts/ for logical grouping completeness. Verify one canonical schema per concept: trade, order, fill, position, balance, ticker, book, OHLCV, funding rate, liquidation, instrument. Investigate fragments: MarketTrade vs CanonicalTrade, OrderBookSnapshot5 vs CanonicalOrderBook, ProcessedCandle vs CanonicalOhlcvBar. For each fragment: merge, alias, deprecate, or document as intentionally distinct with clear reason. Output: fragmentation decision table."
    status: pending
  - id: p1-field-consistency
    content: "Field naming convention consistency audit across canonical schemas in domain.py and execution.py. Produce a field-consistency matrix: timestamp type (int ns vs int ms vs datetime vs str ISO), price type (Decimal vs str vs float), quantity/size type, venue field naming, instrument_key vs symbol vs instrument_id. Flag all inconsistencies; propose normalisation of field types across the canonical layer."
    status: pending
  - id: p1-deviation-coverage
    content: "For each canonical schema, document optional vs required fields and identify venue-specific data that has no optional home (silently dropped during normalisation). Check: CanonicalOrder (venue-specific order types lost?), CanonicalFill (fee structures captured?), CanonicalDerivativeTicker (all funding/OI fields present?). Add missing optional fields to canonical schemas without breaking the normalised base."
    status: pending
  - id: p1-normalizer-completeness
    content: "Cross-reference all 27 normalise/ modules against active venue adapters in unified_api_contracts_external/. Identify venues with raw schemas but no normalizer function (normalization orphans — raw schema exists, canonical never produced). Produce Coverage Matrix: Venue × Schema Type → has normalizer? Priority check: binance, bybit, okx, coinbase, kraken, deribit, hyperliquid, databento, tardis, kalshi, polymarket."
    status: pending
  - id: p1-schemas-core-boundary
    content: "Audit schemas/ (13 core files: accounts, derivatives, risk, analytics, etc.) for boundary violations against unified_normalised_contracts/. Verify FundingRate (schemas/derivatives.py) does not conflict with CanonicalFundingRate (unified_normalised_contracts/domain.py) — they serve distinct purposes (raw vs canonical). Flag any schemas/ class that duplicates or overlaps with a canonical. Document the permitted schemas/ purpose: non-normalised shared utilities, not canonical outputs."
    status: pending

  # PHASE 1b — UAC Canonical Field Fixes (P0 findings from audit)
  - id: p1b-canonical-funding-rate-predicted-rate
    content: "Add predicted_rate: Decimal | None to CanonicalFundingRate in unified_normalised_contracts/domain.py. schemas/derivatives.py::FundingRate has this field (line 20) but it is silently dropped during normalization — confirmed data loss. File: unified-api-contracts/unified_api_contracts/unified_normalised_contracts/domain.py. DONE 2026-03-06."
    status: completed
  - id: p1b-ohlcv-decimal-precision
    content: "Change CanonicalOhlcvBar.open/high/low/close from float to Decimal in unified_normalised_contracts/domain.py. All other price fields in canonical schemas use Decimal; this is an inconsistency that allows silent precision loss. File: unified-api-contracts/unified_api_contracts/unified_normalised_contracts/domain.py. DONE 2026-03-06."
    status: completed
  - id: p1b-derivative-ticker-adl-rank
    content: "Add adl_rank: int | None to CanonicalDerivativeTicker in unified_normalised_contracts/domain.py. ADL (Auto-Deleveraging) rank is published by Binance, OKX, Deribit and is important for position risk assessment — currently no field for it. File: unified-api-contracts/unified_api_contracts/unified_normalised_contracts/domain.py. DONE 2026-03-06."
    status: completed
  - id: p1b-funding-timestamp-rename
    content: "Rename next_funding_time → next_funding_timestamp in CanonicalFundingRate and CanonicalDerivativeTicker (unified_normalised_contracts/domain.py). Inconsistent suffix vs all other timestamp fields. Updated all normalise/derivative_tickers.py normalizers. DONE 2026-03-06."
    status: completed
  - id: p1b-instrument-id-naming-split
    content: "Document the intentional split: domain.py canonical schemas use instrument_key (VENUE:TYPE:SYMBOL format), execution.py uses instrument_id (venue-specific opaque ID). Added module-level docstrings to both files. DONE 2026-03-06."
    status: completed

  # PHASE 2 — UIC Utilization Audit
  - id: p2-uic-adoption-matrix
    content: "For all 108 public UIC classes (from unified_internal_contracts/__init__.__all__), grep all terminal consumer repos (execution-service, strategy-service, market-data-processing-service, market-tick-data-service, market-data-api, instruments-service, alerting-service, risk-and-exposure-service, position-balance-monitor-service, pnl-attribution-service, ml-inference-service, ml-training-service, features-delta-one-service, features-volatility-service, features-cross-instrument-service, features-onchain-service, features-sports-service, features-calendar-service). Produce UIC Adoption Matrix: Schema × Service → imported? Exclude unified-trading-library (re-exporter, not terminal consumer)."
    status: pending
  - id: p2-orphaned-uic-schemas
    content: "Based on p2-uic-adoption-matrix: list all UIC schemas with 0 terminal consumer importers. Classify each as: (a) correctly defined but not yet adopted — create adoption TODOs linking to the service that should use it; (b) superseded by UAC canonical re-export — mark for removal; (c) prematurely defined — defer to domain/ migration. Output: orphan resolution table."
    status: pending
  - id: p2-missing-adoption-services
    content: "Identify services that define local Pydantic models for concepts already in UIC without importing from UIC. Known instances: strategy-service (PositionData, ExposureData, RiskData → UIC has RiskPosition, ExposureSummary in risk.py), execution-service (SportsBetResult → UIC domain/), market-data-api (OrderBookSnapshot → UIC CanonicalBookUpdate), features-sports-service (14 column list schemas → UIC features.py). Produce missing-adoption remediation table: service × local class × UIC canonical equivalent × action."
    status: pending
  - id: p2-domain-dir-population
    content: "Audit domain/ population status (domain/ is NOT empty as previously assumed — already partially populated as of 2026-03-06 audit). ALREADY DONE: strategy_service/ (domain_events.py, monitoring.py, order.py), execution_service/sports.py, market_data_processing/ (adapter_models.py, candle_schema.py), domain/sports/ (TypedDicts for features-sports-service). STILL MISSING: market-data-api/ (OrderBookSnapshot → CanonicalBookUpdate), features-onchain-service/ (OnchainFeatureRecord). Update SCHEMA_CONTRACTS_AUDIT.md domain/ section to reflect actual completion state."
    status: in_progress
  - id: p2-uic-registry-fix
    content: "Fix 4 stale entries in unified-internal-contracts/schema_registry.json that point to non-existent source files (currently reference UAC re-exports as if they were native UIC definitions). Update each entry to reflect the true canonical location of the schema. DONE 2026-03-06: CanonicalOrderBook, CanonicalTrade, CanonicalLiquidation, CanonicalDerivativeTicker corrected to repo=unified-api-contracts + re_export_via=unified_internal_contracts.market_data."
    status: completed

  # PHASE 3 — Cross-Contract Duplication Resolution
  - id: p3-instrument-record-conflict
    content: "Resolve InstrumentRecord CONFLICT (highest-priority blocker per SCHEMA_CONTRACTS_AUDIT.md): UAC version = 76 fields, float, raw symbols, GCS parquet schema (InstrumentWarehouseRow alias); UIC version = 31 fields, Decimal, normalised, URDI adapter contract. Proposed resolution: UAC owns InstrumentWarehouseRow (parquet/GCS shape, 76 fields); UIC owns InstrumentRecord (adapter contract, 31 fields, Decimal). They serve different purposes — confirm naming clarity. Document decision in both repos (UAC unified_normalised_contracts/domain.py + UIC reference/instrument.py docstrings + this plan)."
    status: pending
  - id: p3-interface-adapter-dupes
    content: "Resolve 34 duplicate models in unified-sports-execution-interface vs UAC and 51 models in unified-market-interface vs UAC. INVESTIGATION DONE 2026-03-06 (agent C): _deribit_models.py, _defi_graph_models.py, _betdaq_models.py, _smarkets_models.py confirmed CORRECTLY PLACED in UAC external schemas already. No action needed — adapter models cursor rule was already applied. Status: RESOLVED."
    status: completed
  - id: p3-ml-interface-dupes
    content: "Resolve ModelVariantConfig/ModelMetadata duplication: UIC ml.py (Pydantic wire schema SSOT) vs UMI models.py (@dataclass with domain methods). INVESTIGATION DONE 2026-03-06: these serve distinct roles — UIC=wire schema, UMI=runtime object. NOT a simple delete. Action: (1) Remove UTL/ml/models.py + ml-training-service/ml/models.py (both are UMI copies — import from UMI); (2) Route UMI to_dict/from_dict through UIC Pydantic model for canonical validation."
    status: pending
  - id: p3-domain-client-dupes
    content: "Resolve InstrumentKey in unified-domain-client/schemas/instrument_key.py (MISPLACE-UIC). INVESTIGATION DONE 2026-03-06: UIC reference/ does NOT have InstrumentKey. UDC version is a @dataclass with from_string(), parse_for_tardis(), and _VENUE_TO_TARDIS mapping. Multiple market-tick-data-service files import via chain through market_tick_data_service.models. Action: Add InstrumentKey to UIC reference/; UDC re-exports from UIC (keeping parse_for_tardis as a utility in UDC adapter layer)."
    status: pending
  - id: p3-uac-uic-boundary-reexports
    content: "DONE 2026-03-06: Added boundary comment to market_data/__init__.py explaining UIC→UAC re-export is permitted; UAC→UIC direction is forbidden. Still pending: verify no UAC module imports from UIC (check test_ac_uic_alignment.py location); add boundary comment to schema_registry.json entries for re-exported types."
    status: in_progress

  # PHASE 4 — SoC Enforcement & DRY Quality Gates
  - id: p4-cursor-rule-schema-governance-index
    content: "Write new cursor rule at unified-trading-pm/cursor-rules/core/schema-governance-index.mdc as a master index pointing to the 6 existing specific import rules (adapter-models-belong-in-uac, no-schema-outside-contracts, service-domain-schema-in-uic, uic-may-import-uac, unified-api-contracts-usage, contracts-integration) and the codex doc (02-data/schema-governance.md). NOTE: The 6 specific rules already exist and are comprehensive — this new rule is an overview/entry-point at priority 95, not a replacement. It also adds Rule 5 (no canonical name collision) and Rule 6 (quality gate advisory) which are NOT yet in any existing rule. DONE 2026-03-06."
    status: completed
  - id: p4-quality-gate-step-513
    content: "Add STEP 5.13 (advisory) to quality gate templates: scan for 'Canonical*' BaseModel subclasses — flag as potential canonical name collision. Added to quality-gates-service-template.sh (DONE 2026-03-06 previous session), quality-gates-library-template.sh, and quality-gates-codex-compliance-snippet.sh (DONE 2026-03-06)."
    status: completed
  - id: p4-no-type-ignore-schema-drift
    content: "INVESTIGATION DONE 2026-03-06 (agent C). No type: ignore comments hide schema drift from local copies diverging from UIC canonical. Findings: (P1) execution_service/engine/execution/types.py — AlgorithmParams TypedDict needs discriminated union; (P2) market_data_processing_service/orchestration_workers.py:320,344 — Optional adapter not narrowed; (P3) execution_service/utils/result.py — type alias syntax upgrade; nautilus_trader and shap are EXEMPT (untyped 3rd-party). No UIC canonical drift hiding found."
    status: completed

  # PHASE 5 — Documentation & Verification
  - id: p5-schema-governance-codex-update
    content: "UPDATE (not create) unified-trading-codex/02-data/schema-governance.md — it already exists with ownership table and domain/ guide. ADDED: (1) Canonical Field Standards table (timestamp=datetime/int ms, price=Decimal, size=Decimal, venue slug, instrument_key vs instrument_id); (2) P0 Canonical Field Issues tracker (all 4 fixes marked resolved 2026-03-06); (3) UIC Adoption Matrix section (link to ADOPTION_MATRIX.md, known orphan categories). 00-SSOT-INDEX.md updated DONE 2026-03-06. DONE 2026-03-06."
    status: completed
  - id: p5-adoption-matrix-publish
    content: "scripts/check_uic_adoption.py CREATED 2026-03-06 in unified-internal-contracts/scripts/. Generates adoption matrix by grepping all 18 terminal consumer repos for UIC class imports. ADOPTION_MATRIX.md is auto-generated by the script. Run: python scripts/check_uic_adoption.py --output docs/ADOPTION_MATRIX.md. Pending: first run + commit of ADOPTION_MATRIX.md."
    status: in_progress
  - id: p5-verification
    content: "Verification: (1) basedpyright UAC unified_normalised_contracts/ — 0 errors ✅ 2026-03-06; (2) schema_registry.json — 0 stale entries ✅; (3) ADOPTION_MATRIX.md — pending first run; (4) STEP 5.13 advisory reports any Canonical* subclasses in services; (5) Interface adapter models: p3-interface-adapter-dupes confirmed RESOLVED ✅; (6) DUPLICATE violations: pending p3-ml-interface-dupes and p3-domain-client-dupes; (7) InstrumentRecord conflict: decision documented in plan body ✅. Still pending: ADOPTION_MATRIX.md first run, InstrumentKey migration, ML wire/runtime alignment."
    status: in_progress
isProject: true
---

# Schema Governance Full Audit

**Status:** Active — Phase 1b complete; Phases 1, 2, 3, 4 (partial), 5 (partial) remaining
**Last Updated:** 2026-03-06
**SSOT for schema placements:** [SCHEMA_CONTRACTS_AUDIT.md](SCHEMA_CONTRACTS_AUDIT.md)
**SSOT for normalization coverage:** [unified-api-contracts/docs/SCHEMA_NORMALIZATION_GAPS_AUDIT.md](../../../unified-api-contracts/docs/SCHEMA_NORMALIZATION_GAPS_AUDIT.md)
**Master cursor rule:** `unified-trading-pm/cursor-rules/core/schema-governance-index.mdc` ✅ created 2026-03-06
**Codex doc (existing):** `unified-trading-codex/02-data/schema-governance.md` ✅ updated 2026-03-06
**Registry fixed:** `unified-internal-contracts/schema_registry.json` — 4 stale entries corrected ✅
**P0 UAC fixes:** 5/5 complete ✅ (predicted_rate, OHLCV Decimal, adl_rank, next_funding_timestamp, docstrings)

---

## Scope

This plan covers four distinct concerns not addressed by existing schema plans:

| Concern | This Plan | Related Existing Plan |
|---|---|---|
| Canonical shape quality (groupings, field consistency, optional fields) | ✓ Phase 1 | — |
| UIC adoption across services (who imports what) | ✓ Phase 2 | — |
| Cross-contract deduplication resolution | ✓ Phase 3 | SCHEMA_CONTRACTS_AUDIT.md (found the violations; this plan resolves them) |
| SoC cursor rule + quality gate enforcement | ✓ Phase 4 | quality_gate_hardening.plan.md (adds STEP 5.12) |
| SCHEMA_GOVERNANCE.md codex doc | ✓ Phase 5 | — |
| Normalization coverage per data provider | — | [uac_schema_normalization_complete.plan.md](uac_schema_normalization_complete.plan.md) |
| Schema placement violations (finding them) | — | [schema_contracts_full_audit.plan.md](schema_contracts_full_audit.plan.md) |

---

## Phase 1 — UAC Canonical Normalization Quality

### 1.1 Canonical Schema Inventory

**Location:** `unified-api-contracts/unified_api_contracts/unified_normalised_contracts/`

| File | Key Classes | Potential Fragments |
|---|---|---|
| `domain.py` | CanonicalTrade, CanonicalTicker, CanonicalDerivativeTicker, CanonicalOhlcvBar, CanonicalFundingRate, CanonicalLiquidation, CanonicalPosition, CanonicalBalance, CanonicalOrderBook, InstrumentWarehouseRow, **MarketTrade**, **OrderBookSnapshot5**, **ProcessedCandle** | MarketTrade vs CanonicalTrade; OrderBookSnapshot5 vs CanonicalOrderBook; ProcessedCandle vs CanonicalOhlcvBar |
| `execution.py` | CanonicalOrder, CanonicalFill, ExecutionInstruction, ExecutionResult | None known |
| `errors.py` | CanonicalError, CanonicalRateLimitError | None known |

### 1.2 Fragment Investigation Guidance

- **MarketTrade vs CanonicalTrade**: If MarketTrade is a deprecated alias or limited-field subset, alias `MarketTrade = CanonicalTrade` or remove. If it has distinct semantics (e.g., anonymous public trade vs private fill), document the distinction clearly.
- **OrderBookSnapshot5 vs CanonicalOrderBook**: OrderBookSnapshot5 (5-level snapshot) may be a bandwidth-optimised subset. If so, keep with explicit docstring; deprecate if CanonicalOrderBook covers all cases.
- **ProcessedCandle vs CanonicalOhlcvBar**: Likely a transformation artifact. Remove if redundant.

### 1.3 Field Consistency Standards (Target)

| Field | Canonical Target Type | Rationale |
|---|---|---|
| timestamp | `int` (Unix ms) | Consistent with market data standards; nanoseconds only for HFT/latency schemas |
| price | `str` (JSON) or `Decimal` | Never `float` in canonical layer; str preserves venue precision |
| quantity/size | `str` or `Decimal` | Never `float` |
| venue | `str` (lowercase slug) | e.g., `"binance"`, `"deribit"` |
| instrument_key | `str` | Canonical identifier; `symbol` = venue-specific raw field |

### 1.4 Normalizer Coverage Matrix (Template)

| Venue | Trade | OrderBook | OHLCV | Ticker | Deriv Ticker | Order/Fill | Instrument |
|---|---|---|---|---|---|---|---|
| binance | | | | | | | |
| bybit | | | | | | | |
| okx | | | | | | | |
| deribit | | | | | | | |
| hyperliquid | | | | | | | |
| databento | | | | | | | |
| tardis | | | | | | | |
| kalshi | | | | | | | |
| polymarket | | | | | | | |

*To be filled by p1-normalizer-completeness todo.*

---

## Phase 2 — UIC Utilization Audit

### 2.1 UIC Domain Summary (108 classes across 24 files)

| Module | Class Count | Domain |
|---|---|---|
| events.py | ~26 | Lifecycle event types + envelopes |
| pubsub.py | ~17 | Internal Pub/Sub message schemas |
| risk.py | ~15 | Risk metrics, alerts, pre-trade checks |
| ml.py | ~10 | Model metadata, training, inference |
| features.py | 6 | Feature records (delta-one, cross-instrument, etc.) |
| market_data/ (6 files) | ~19 | OHLCV, book, option quote, options chain + UAC re-exports |
| positions/ (4 files) | 5 | CeFi + DeFi positions |
| reference/ (2 files) | 6 | InstrumentRecord, InstrumentDefinition, enums |
| alerting/ | 1 | AlertEvent |
| connectivity/ | 7 | WebSocket lifecycle events |
| schemas/errors.py | 6 | Error classification, DLQ |
| schemas/audit.py | 2 | Audit retention + requirements |
| messaging.py | 2 | MessagingScope, MessagingTopic (enums) |
| defi.py | 2 | GasCostEstimate |
| reporting/ | 1 | FeeStructure |

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

| | UAC (InstrumentWarehouseRow) | UIC (InstrumentRecord) |
|---|---|---|
| Fields | 76 (float, raw symbols, venue mappings) | 31 (Decimal, normalised) |
| Purpose | GCS parquet storage row | URDI adapter output contract |
| Consumers | instruments-service (reads from GCS) | unified-reference-data-interface (adapter output) |
| Resolution | Keep as InstrumentWarehouseRow (rename confirmed) | Keep as InstrumentRecord (URDI adapter SSOT) |

**Decision:** These are intentionally different shapes serving different layers. Rename removes confusion. No merge required.

### 3.2 Interface Adapter Duplicate Summary

| Interface Repo | Duplicate Count | UAC Target |
|---|---|---|
| unified-sports-execution-interface | 34 models | `unified_api_contracts_external/{venue}/schemas.py` per venue |
| unified-market-interface | 51 models (_deribit_models.py, _defi_graph_models.py) | `unified_api_contracts_external/deribit/schemas.py` + defi adapters |
| unified-ml-interface | 2 models (ModelVariantConfig, ModelMetadata) | `unified_internal_contracts/ml.py` (UIC, not UAC) |
| unified-domain-client | 1 model (InstrumentKey) | `unified_internal_contracts/reference/` |

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
        grep -v "unified_api_contracts\|unified_internal_contracts" || true)
    if [ -n "$hits" ]; then
        echo "WARN: POTENTIAL_SCHEMA_DUPLICATE — class '${name}' defined in service source:"
        echo "$hits"
        SCHEMA_COLLISION_COUNT=$((SCHEMA_COLLISION_COUNT + 1))
    fi
done
```

---

## Phase 5 — Verification Checklist

| Check | Command | Pass Condition |
|---|---|---|
| UAC canonical type-clean | `run_timeout 120 basedpyright unified-api-contracts/unified_api_contracts/unified_normalised_contracts/` | 0 errors |
| UIC type-clean | `run_timeout 120 basedpyright unified-internal-contracts/unified_internal_contracts/` | 0 errors |
| UIC adoption | `python unified-internal-contracts/scripts/check_uic_adoption.py` | 0 orphaned schemas |
| Schema name collisions | STEP 5.12 in quality gate | 0 warnings |
| Schema registry | `python -c "import json; r=json.load(open('schema_registry.json')); print(len(r))"` | All entries resolve |
| Duplicate resolution | Review SCHEMA_CONTRACTS_AUDIT.md DUPLICATE section | 16/16 resolved |
| Conflict resolution | InstrumentRecord naming documented | Decision recorded |

---

## Dependency

Feeds into:
- [orphan-contracts-utilization.plan.md](orphan-contracts-utilization.plan.md) (plan #11) — adoption matrix informs orphan remediation priorities
- [uac_schema_normalization_complete.plan.md](uac_schema_normalization_complete.plan.md) (plan #11b) — normalizer completeness gaps from p1-normalizer-completeness go here
- [quality_gate_hardening.plan.md](quality_gate_hardening.plan.md) (plan #2c) — STEP 5.12 to be added per p4-quality-gate-step-512
