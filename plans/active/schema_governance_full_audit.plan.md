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
    content: "Add predicted_rate: Decimal | None to CanonicalFundingRate in unified_normalised_contracts/domain.py. schemas/derivatives.py::FundingRate has this field (line 20) but it is silently dropped during normalization — confirmed data loss. File: unified-api-contracts/unified_api_contracts/unified_normalised_contracts/domain.py."
    status: pending
  - id: p1b-ohlcv-decimal-precision
    content: "Change CanonicalOhlcvBar.open/high/low/close from float to Decimal in unified_normalised_contracts/domain.py. All other price fields in canonical schemas use Decimal; this is an inconsistency that allows silent precision loss. File: unified-api-contracts/unified_api_contracts/unified_normalised_contracts/domain.py."
    status: pending
  - id: p1b-derivative-ticker-adl-rank
    content: "Add adl_rank: int | None to CanonicalDerivativeTicker in unified_normalised_contracts/domain.py. ADL (Auto-Deleveraging) rank is published by Binance, OKX, Deribit and is important for position risk assessment — currently no field for it. File: unified-api-contracts/unified_api_contracts/unified_normalised_contracts/domain.py."
    status: pending
  - id: p1b-funding-timestamp-rename
    content: "Rename next_funding_time → next_funding_timestamp in CanonicalFundingRate (unified_normalised_contracts/domain.py). Inconsistent suffix vs all other timestamp fields. Coordinate update in all normalise/funding_rate normalizers that populate this field."
    status: pending
  - id: p1b-instrument-id-naming-split
    content: "Document the intentional split: domain.py canonical schemas use instrument_key (VENUE:TYPE:SYMBOL format), execution.py uses instrument_id (venue-specific opaque ID). Add a module-level docstring to both files explaining why and when to use each. This is NOT a bug but causes confusion — P1 documentation fix. Files: unified-api-contracts/unified_api_contracts/unified_normalised_contracts/domain.py and execution.py."
    status: pending

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
    content: "Plan population of unified_internal_contracts/domain/ (scaffolded 2026-03-06, currently empty). For each of the 6 MISPLACE-UIC services from SCHEMA_CONTRACTS_AUDIT.md: execution-service, strategy-service, market-data-processing-service, market-data-api, features-onchain-service, features-sports-service — define: (a) target domain/<service-name>/ module path, (b) classes to migrate, (c) importers to update. Respect domain/__init__.py layout rule: each service gets its own subdirectory."
    status: pending
  - id: p2-uic-registry-fix
    content: "Fix 4 stale entries in unified-internal-contracts/schema_registry.json that point to non-existent source files (currently reference UAC re-exports as if they were native UIC definitions). Update each entry to reflect the true canonical location of the schema. DONE 2026-03-06: CanonicalOrderBook, CanonicalTrade, CanonicalLiquidation, CanonicalDerivativeTicker corrected to repo=unified-api-contracts + re_export_via=unified_internal_contracts.market_data."
    status: completed

  # PHASE 3 — Cross-Contract Duplication Resolution
  - id: p3-instrument-record-conflict
    content: "Resolve InstrumentRecord CONFLICT (highest-priority blocker per SCHEMA_CONTRACTS_AUDIT.md): UAC version = 76 fields, float, raw symbols, GCS parquet schema (InstrumentWarehouseRow alias); UIC version = 31 fields, Decimal, normalised, URDI adapter contract. Proposed resolution: UAC owns InstrumentWarehouseRow (parquet/GCS shape, 76 fields); UIC owns InstrumentRecord (adapter contract, 31 fields, Decimal). They serve different purposes — confirm naming clarity. Document decision in both repos (UAC unified_normalised_contracts/domain.py + UIC reference/instrument.py docstrings + this plan)."
    status: pending
  - id: p3-interface-adapter-dupes
    content: "Resolve 34 duplicate models in unified-sports-execution-interface vs UAC and 51 duplicate models in unified-market-interface (_deribit_models.py, _defi_graph_models.py) vs UAC. Produce deduplication table: class name × current location × UAC equivalent × action (move to UAC, alias, remove). All interface adapter Pydantic models must move to UAC per adapter-models-belong-in-uac cursor rule. This also resolves the circular import violation in UAC tests."
    status: pending
  - id: p3-ml-interface-dupes
    content: "Resolve 2 duplicate schemas between unified-ml-interface and UIC ml.py: ModelVariantConfig, ModelMetadata. UIC ml.py is canonical. Remove duplicates from unified-ml-interface; replace with imports from unified_internal_contracts.ml. Run basedpyright on unified-ml-interface after change."
    status: pending
  - id: p3-domain-client-dupes
    content: "Resolve InstrumentKey in unified-domain-client/schemas/instrument_key.py (MISPLACE-UIC). Confirm whether InstrumentKey exists in UIC reference/ or needs to be added. Remove from domain-client; import from UIC. Update all 3+ cross-repo importers of domain-client InstrumentKey."
    status: pending
  - id: p3-uac-uic-boundary-reexports
    content: "Audit all UIC modules that re-export from UAC (known: market_data/__init__.py re-exports CanonicalTicker, CanonicalTrade, CanonicalDerivativeTicker, CanonicalLiquidation, CanonicalOrderBook from unified_api_contracts). Confirm re-export is a permitted convenience layer (UIC→UAC canonical only). Add inline comment documenting this cross-package import boundary. Ensure NO UAC module imports from UIC (check: test_ac_uic_alignment.py import must be moved from UAC test dir to UIC test dir)."
    status: pending

  # PHASE 4 — SoC Enforcement & DRY Quality Gates
  - id: p4-cursor-rule-schema-governance-index
    content: "Write new cursor rule at unified-trading-pm/cursor-rules/core/schema-governance-index.mdc as a master index pointing to the 6 existing specific import rules (adapter-models-belong-in-uac, no-schema-outside-contracts, service-domain-schema-in-uic, uic-may-import-uac, unified-api-contracts-usage, contracts-integration) and the codex doc (02-data/schema-governance.md). NOTE: The 6 specific rules already exist and are comprehensive — this new rule is an overview/entry-point at priority 95, not a replacement. It also adds Rule 5 (no canonical name collision) and Rule 6 (quality gate advisory) which are NOT yet in any existing rule. DONE 2026-03-06."
    status: completed
  - id: p4-quality-gate-step-513
    content: "Add STEP 5.13 (advisory) to quality gate service template: scan service source for 'Canonical*' BaseModel subclasses — flag as potential canonical name collision. STEP 5.12 was already taken (hardcoded protocol names). Added to quality-gates-service-template.sh DONE 2026-03-06. Still needed: quality-gates-library-template.sh, quality-gates-codex-compliance-snippet.sh."
    status: completed
  - id: p4-no-type-ignore-schema-drift
    content: "Grep all service repos for '# type: ignore' comments near schema-related code that suppress type errors caused by local schema copies diverging from UIC canonical types. For each hit: fix root cause by replacing local model with the canonical UIC import. No type: ignore to hide architectural violations (per existing CLAUDE.md rule)."
    status: pending

  # PHASE 5 — Documentation & Verification
  - id: p5-schema-governance-codex-update
    content: "UPDATE (not create) unified-trading-codex/02-data/schema-governance.md — it already exists with ownership table and domain/ guide. ADD the following sections: (1) Canonical Field Standards table (timestamp=int ms, price=Decimal, size=Decimal); (2) UIC Adoption Matrix summary (link to ADOPTION_MATRIX.md); (3) Known P0 canonical field data-loss issues tracker (funding rate predicted_rate, OHLCV float precision, ADL rank gap, timestamp suffix). 00-SSOT-INDEX.md updated DONE 2026-03-06 to add schema governance row linking to this file."
    status: in_progress
  - id: p5-adoption-matrix-publish
    content: "Publish UIC Adoption Matrix (produced by p2-uic-adoption-matrix) as unified-internal-contracts/docs/ADOPTION_MATRIX.md. Add a scripts/check_uic_adoption.py generator script to UIC repo that re-generates the matrix by grepping the workspace. Run as part of UIC release process."
    status: pending
  - id: p5-verification
    content: "Verification checklist: (1) basedpyright passes on UAC unified_normalised_contracts/ and UIC — clean; (2) schema_registry.json has 0 stale entries; (3) ADOPTION_MATRIX.md shows 0 orphaned UIC schemas; (4) quality gate STEP 5.12 reports 0 canonical name duplicates across service repos; (5) all 34+51 interface adapter dupe models removed from unified-sports-execution-interface and unified-market-interface; (6) all 16 DUPLICATE violations from SCHEMA_CONTRACTS_AUDIT.md resolved; (7) InstrumentRecord conflict documented and canonical owner confirmed."
    status: pending
isProject: true
---

# Schema Governance Full Audit

**Status:** Active
**Last Updated:** 2026-03-06
**SSOT for schema placements:** [SCHEMA_CONTRACTS_AUDIT.md](SCHEMA_CONTRACTS_AUDIT.md)
**SSOT for normalization coverage:** [unified-api-contracts/docs/SCHEMA_NORMALIZATION_GAPS_AUDIT.md](../../../unified-api-contracts/docs/SCHEMA_NORMALIZATION_GAPS_AUDIT.md)
**Master cursor rule:** `unified-trading-pm/cursor-rules/core/schema-governance-index.mdc` ✅ created 2026-03-06
**Codex doc (existing):** `unified-trading-codex/02-data/schema-governance.md` (update, not create)
**Registry fixed:** `unified-internal-contracts/schema_registry.json` — 4 stale entries corrected ✅

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
