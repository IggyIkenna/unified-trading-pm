# Stream D: Risk Matrix & P&L Attribution — Implementation Specification

**Plan**: `contracts-observability-risk-cleanup` (uac_errors_package_cleanup_2026_03_16.plan.md) **Phase**: 5, Stream D
**Status**: Implementation spec — agents follow this, not the plan YAML summaries

---

## Architectural Decisions

### UAC vs UIC Placement Rule

If ANY external source (Deribit, TARDIS, venues) provides the data type, the schema belongs in **UAC**. Internal
computation uses the same UAC schema. One type, two sources (external feed OR internal calc).

| Schema                          | Location                | Reason                                                                |
| ------------------------------- | ----------------------- | --------------------------------------------------------------------- |
| RiskType enum                   | **UAC**                 | External venues report on these dimensions (delta, vega from Deribit) |
| GreeksExposure (per-instrument) | **UAC**                 | Deribit/TARDIS provide delta,gamma,vega,theta directly                |
| PortfolioGreeksSnapshot         | **UAC** (already there) | Aggregation of external data                                          |
| PortfolioPnLAttribution         | **UAC** (already there) | Aggregation of external data dimensions                               |
| StrategyRiskProfile             | **UIC**                 | Internal config — no venue provides subscription profiles             |
| RiskPnLNode (aggregation tree)  | **UIC**                 | Internal aggregation hierarchy                                        |
| ExtendedPnLAttribution          | **UIC**                 | Internal P&L decomposition computation                                |
| CustomRiskType definitions      | **UIC**                 | Internal evaluation logic                                             |
| CustomRiskScenarioConfig        | **UCI**                 | Runtime parameters, hot-reloadable from GCS                           |
| RiskMetrics, VaR, AlertMessage  | **UIC** (stay)          | Internal computations                                                 |

### Existing Schemas (DO NOT DUPLICATE)

| Schema                       | Location                                   | What it has                                                    | Reuse strategy                                                                                          |
| ---------------------------- | ------------------------------------------ | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `CanonicalOptionsChainEntry` | UAC derivatives/:78-95                     | delta, gamma, theta, vega, IV per option                       | Source of per-instrument Greeks from external                                                           |
| `PortfolioGreeksSnapshot`    | UAC position/:139-148                      | total_delta/gamma/theta/vega/rho + per_underlying list         | Portfolio-level Greeks — EXTEND with RiskType keying                                                    |
| `UnderlyingGreeksBreakdown`  | UAC position/:127-136                      | Per-underlying Greeks (delta,gamma,theta,vega,rho)             | Already does underlying-level — REUSE                                                                   |
| `PortfolioPnLAttribution`    | UAC position/:151-168                      | 11 P&L fields + by_asset_class + by_strategy dicts             | EXTEND — add dict[RiskType, Decimal] alongside existing fields                                          |
| `RiskGroupSummary`           | UAC position/:171-185                      | Per-underlying: net_delta/gamma/theta/vega, gross/net exposure | REUSE for underlying-level netting                                                                      |
| `PortfolioView`              | UAC position/:188-213                      | Full snapshot: positions, greeks, pnl, risk_groups             | Top-level output — EXTEND with RiskPnLNode tree                                                         |
| `GreeksExposure`             | UIC risk.py:214-235                        | Per-instrument: delta,gamma,theta,vega,rho                     | DUPLICATE of UAC — move to UAC or delete (UAC already has per-underlying via UnderlyingGreeksBreakdown) |
| `PnLBreakdown`               | UIC risk.py:188-211                        | 6 dimensions: delta,funding,basis,interest_rate,greeks,mtm     | Keep in UIC as simplified internal view                                                                 |
| `ExposureSummary`            | UIC risk.py:131-140                        | gross/net/long/short, by_venue, by_instrument                  | REUSE — extend with by_underlying, by_strategy                                                          |
| `CrossVenueAggregator`       | PBMS core/cross_venue_aggregator.py:59-246 | Per-instrument cross-venue aggregation                         | EXTEND with RiskType-aware aggregation                                                                  |

---

## p5-risk-taxonomy-schema: RiskType Enum

### File to create

`unified-api-contracts/unified_api_contracts/canonical/crosscutting/risk_taxonomy.py` (NEW — ~60 lines)

### Schema definition

```python
"""Risk type taxonomy — all risk dimensions across strategy types.

External venues provide data for many of these (Deribit: delta/gamma/vega/theta,
exchanges: funding rates). Schema lives in UAC because external sources report on
these dimensions. Internal computation uses the same enum.
"""
from __future__ import annotations
from enum import StrEnum

class RiskType(StrEnum):
    """Comprehensive risk dimension taxonomy."""
    # First order — direct price/rate sensitivities
    DELTA = "delta"                         # directional price
    VEGA = "vega"                           # volatility
    THETA = "theta"                         # time decay
    RHO = "rho"                             # interest rate (parallel shift)
    FUNDING = "funding"                     # perpetual funding rates
    BASIS = "basis"                         # spot-futures divergence
    CARRY = "carry"                         # cost of carry
    FX = "fx"                               # currency exposure
    LIQUIDITY = "liquidity"                 # market impact / bid-ask
    # Second order — higher-order sensitivities
    GAMMA = "gamma"                         # convexity (d²V/dS²)
    VOLGA = "volga"                         # vol-of-vol (d²V/dσ²)
    VANNA = "vanna"                         # delta-vol cross (d²V/dSdσ)
    SLIDE = "slide"                         # vol surface time decay
    # Structural — portfolio/position structure risks
    DURATION = "duration"                   # term structure sensitivity
    CONVEXITY = "convexity"                 # duration sensitivity to rate changes
    SPREAD = "spread"                       # bid-ask / credit / cross-venue spread
    CONCENTRATION = "concentration"         # single-name / venue exposure
    # Operational — infrastructure risks
    VENUE_PROTOCOL = "venue_protocol"       # exchange/protocol downtime risk
    CORRELATION = "correlation"             # cross-asset correlation breakdown
    # Domain-specific
    EDGE_DECAY = "edge_decay"               # sports: edge erosion over time
    MARKET_SUSPENSION = "market_suspension" # sports: market suspension risk
    PROTOCOL_RISK = "protocol_risk"         # DeFi: smart contract risk
    IMPERMANENT_LOSS = "impermanent_loss"   # DeFi: LP impermanent loss

class RiskCategory(StrEnum):
    """Groups RiskTypes for UI display."""
    FIRST_ORDER = "first_order"
    SECOND_ORDER = "second_order"
    STRUCTURAL = "structural"
    OPERATIONAL = "operational"
    DOMAIN_SPECIFIC = "domain_specific"

RISK_TYPE_CATEGORIES: dict[RiskCategory, list[RiskType]] = {
    RiskCategory.FIRST_ORDER: [RiskType.DELTA, RiskType.VEGA, RiskType.THETA, RiskType.RHO,
        RiskType.FUNDING, RiskType.BASIS, RiskType.CARRY, RiskType.FX, RiskType.LIQUIDITY],
    RiskCategory.SECOND_ORDER: [RiskType.GAMMA, RiskType.VOLGA, RiskType.VANNA, RiskType.SLIDE],
    RiskCategory.STRUCTURAL: [RiskType.DURATION, RiskType.CONVEXITY, RiskType.SPREAD, RiskType.CONCENTRATION],
    RiskCategory.OPERATIONAL: [RiskType.VENUE_PROTOCOL, RiskType.CORRELATION],
    RiskCategory.DOMAIN_SPECIFIC: [RiskType.EDGE_DECAY, RiskType.MARKET_SUSPENSION,
        RiskType.PROTOCOL_RISK, RiskType.IMPERMANENT_LOSS],
}
```

### Export chain

1. `canonical/crosscutting/__init__.py` — add `from .risk_taxonomy import *`
2. `canonical/domain/__init__.py` — add import + re-export
3. Root `__init__.py` — add to imports + `__all__`
4. Root facade `risk.py` (if exists) or create — re-export for `from unified_api_contracts.risk import RiskType`

### Downstream impact

- **No breakage** — purely additive (new file, new symbols)
- risk-and-exposure-service, PBMS will START importing RiskType when they implement risk matrix
- UIC schemas that reference risk dimensions (PnLBreakdown, GreeksExposure) can adopt RiskType enum keys

### File size

- New file: ~60 lines (well under 900)
- UAC `__init__.py`: +3 lines (896→~849 after Phase 1 removals + this addition)

---

## p5-risk-strategy-subscription: StrategyRiskProfile

### File to modify

`unified-internal-contracts/unified_internal_contracts/domain/risk_service/risk.py` — add after CorrelationEntry
(~line 291)

### Schema definition (~20 lines added to risk.py)

```python
class StrategyRiskProfile(BaseModel):
    """Which risk types a strategy subscribes to. Unsubscribed = zero in matrix."""
    strategy_type: str                          # MOM, BASIS, YIELD, OPTIONS, SPORTS, ARB
    subscribed_risks: list[str]                 # RiskType.value strings
    custom_risk_ids: list[str] = Field(default_factory=list)  # user-defined custom risk IDs
```

### Config schema — add to UCI

`unified-config-interface/unified_config_interface/config.py` — add after existing config classes:

```python
class StrategyRiskSubscriptionConfig(BaseModel):
    """Loaded from GCS: gs://config/risk/strategy_risk_subscriptions.yaml"""
    profiles: dict[str, list[str]]  # strategy_type → [RiskType.value strings]
    model_config = {"extra": "forbid"}
```

### Default config in GCS

Path: `gs://config/risk/strategy_risk_subscriptions.yaml`

```yaml
profiles:
  MOM: [delta, funding, liquidity, venue_protocol, concentration, fx]
  BASIS: [delta, basis, funding, duration, venue_protocol, liquidity, carry]
  YIELD: [delta, protocol_risk, liquidity, concentration, fx, impermanent_loss]
  OPTIONS: [delta, gamma, vega, theta, rho, volga, vanna, slide, duration, venue_protocol]
  SPORTS: [edge_decay, market_suspension, concentration, liquidity]
  ARB: [delta, venue_protocol, liquidity, spread, correlation]
```

### Loading pattern

risk-and-exposure-service loads on startup via UCI singleton pattern (existing — see `RiskAndExposureServiceConfig` in
config.py). Add field:

```python
risk_subscription_config_path: str = Field(
    default="gs://config/risk/strategy_risk_subscriptions.yaml",
    validation_alias=AliasChoices("RISK_SUBSCRIPTION_CONFIG_PATH")
)
```

### DRY compliance

- Uses existing strategy_type strings from strategy-service/cli/resolvers.py (MOM, BASIS, YIELD)
- Does NOT re-declare strategy type definitions
- RiskType values imported from UAC risk_taxonomy.py

### Downstream impact

- **No breakage** — additive schema + config
- Consumers adopt by adding risk_subscription_config_path to their service config

---

## p5-risk-aggregation-hierarchy: RiskPnLNode Tree

### File to modify

`unified-internal-contracts/unified_internal_contracts/domain/risk_service/risk.py` — add after StrategyRiskProfile

### Schema definition (~45 lines)

```python
class RiskAggregationLevel(StrEnum):
    COMPANY = "company"
    CLIENT = "client"
    ACCOUNT = "account"
    STRATEGY = "strategy"
    UNDERLYING = "underlying"
    INSTRUMENT = "instrument"

class RiskPnLNode(BaseModel):
    """Single node in Company→Client→Account→Strategy→Underlying→Instrument tree."""
    level: RiskAggregationLevel
    level_id: str                                                   # company_id, client_id, etc.
    risk_by_type: dict[str, Decimal] = Field(default_factory=dict)  # RiskType.value → exposure
    pnl_by_type: dict[str, Decimal] = Field(default_factory=dict)   # RiskType.value → P&L
    var_by_type: dict[str, Decimal] = Field(default_factory=dict)   # RiskType.value → marginal VaR
    children: list["RiskPnLNode"] = Field(default_factory=list)
    subscribed_risks: list[str] = Field(default_factory=list)       # from StrategyRiskProfile

class DurationBucket(StrEnum):
    OVERNIGHT = "overnight"
    ONE_WEEK = "1w"
    ONE_MONTH = "1m"
    THREE_MONTH = "3m"
    SIX_MONTH = "6m"
    ONE_YEAR = "1y"
    TWO_YEAR_PLUS = "2y+"

class TermStructureExposure(BaseModel):
    """Duration risk decomposed by maturity bucket."""
    underlying: str
    exposures_by_bucket: dict[str, Decimal]  # DurationBucket.value → exposure
```

### Integration with existing PBMS

PBMS `CrossVenueAggregator.build_portfolio_view()` (cross_venue_aggregator.py line ~115) currently returns
`PortfolioView`. EXTEND (don't replace) to ALSO produce a `RiskPnLNode` tree:

```python
# ADD method to CrossVenueAggregator
def build_risk_tree(
    self, company_id: str, client_id: str, account_id: str,
    portfolio_view: PortfolioView, risk_profiles: dict[str, StrategyRiskProfile]
) -> RiskPnLNode:
    """Build Company→Client→Account→Strategy→Underlying→Instrument tree from PortfolioView."""
```

This method reads existing `PortfolioView.positions` (list of `AggregatedPosition`, each with instrument_id,
strategy_id, underlying, per_venue breakdowns) and groups them into the hierarchy.

### DRY compliance

- `RiskPnLNode.risk_by_type` uses dict[str, Decimal] keyed by RiskType.value → extensible without schema changes when
  new RiskTypes are added
- Replaces the need for separate per-level schemas (no CompanyRisk, ClientRisk, etc.)
- `children` field enables tree traversal without type proliferation
- EXTENDS PortfolioView — doesn't replace it. PortfolioView remains the flat snapshot; RiskPnLNode is the hierarchical
  risk view derived from it.

### Downstream impact

- PBMS: add `build_risk_tree()` method — no existing methods modified
- risk-and-exposure-service: add `/risk/matrix` endpoint returning RiskPnLNode
- UIs: consume RiskPnLNode tree for drill-down views

### File size

- risk.py: 308 + 20 (StrategyRiskProfile) + 45 (hierarchy) = ~373 lines (under 900)

---

## p5-risk-new-dimensions: Computation Modules

### Directory to create

`risk-and-exposure-service/risk_and_exposure_service/core/risk_dimensions/` (NEW)

### File structure

```
core/risk_dimensions/
├── __init__.py              # exports all compute functions (~15 lines)
├── duration.py              # duration + convexity computation (~100 lines)
├── second_order_vol.py      # volga, vanna, slide (~120 lines)
├── spread.py                # spread risk computation (~80 lines)
├── venue_protocol.py        # venue/protocol risk scoring (~100 lines)
└── sports_domain.py         # edge_decay, market_suspension (~80 lines)
```

### duration.py — Key functions

```python
def compute_duration(instrument_type: str, expiry: date | None, funding_reset_hours: float | None) -> Decimal:
    """Duration in days. Spot=0, Perp≈0, Futures=days_to_expiry, Options=complex, DeFi=lock_period."""

def compute_convexity(instrument_type: str, duration: Decimal, ...) -> Decimal:
    """Second derivative of duration. How duration changes when rates change."""

def compute_term_structure_exposure(positions: list[AggregatedPosition]) -> list[TermStructureExposure]:
    """Group positions into DurationBucket and sum exposure per bucket per underlying."""
```

Input: `AggregatedPosition` from UAC (position/:83-109) — has `instrument_type`, `expiry` fields. Output:
`TermStructureExposure` from UIC (new schema above).

### second_order_vol.py — Key functions

```python
def compute_volga(greeks: CanonicalOptionsChainEntry, vol_surface: dict) -> Decimal:
    """d²V/dσ² — vol-of-vol risk. Inputs from UAC derivatives/:78-95."""

def compute_vanna(greeks: CanonicalOptionsChainEntry, vol_surface: dict) -> Decimal:
    """d²V/(dS·dσ) — delta-vol cross sensitivity."""

def compute_slide(greeks: CanonicalOptionsChainEntry, vol_surface: dict, dt_days: int) -> Decimal:
    """Vol surface time decay. Front vol decays faster than back vol."""
```

Input: `CanonicalOptionsChainEntry` from UAC — has delta, gamma, vega, theta, IV. Vol surface: dict of (expiry, strike)
→ implied_vol from TARDIS mark_iv/bid_iv/ask_iv. Returns Decimal("0") for non-options (subscription model filters before
calling).

### venue_protocol.py — Key functions

```python
def compute_venue_risk(
    positions_by_venue: dict[str, list[AggregatedPosition]],
    breaker_states: dict[str, CircuitBreakerEvent],
    venue_downtime_history: dict[str, list[tuple[datetime, timedelta]]]
) -> dict[str, Decimal]:
    """Per-venue: max loss if venue is down for N hours. Uses exposure × downtime probability."""
```

Input: `CircuitBreakerEvent` from UIC (risk.py:238-259). Position data: `AggregatedPosition.per_venue`
(VenuePositionBreakdown list).

### DRY compliance

- All functions consume existing UAC/UIC schemas as inputs — no re-declaration
- All functions return Decimal values that feed into `RiskPnLNode.risk_by_type[RiskType.value]`
- Each file is ~80-120 lines — well under 900 limit
- New directory, no existing files modified

---

## p5-risk-pnl-attribution-engine: ExtendedPnLAttribution

### File to modify

`unified-internal-contracts/unified_internal_contracts/domain/risk_service/risk.py`

### Schema definition (~20 lines, add after PnLBreakdown at line 211)

```python
class ExtendedPnLAttribution(BaseModel):
    """P&L attributed to each RiskType. Dict-based — no schema change when adding new risk types."""
    client_id: str
    strategy_id: str | None = None
    underlying: str | None = None
    instrument_id: str | None = None
    level: RiskAggregationLevel
    timestamp: datetime
    pnl_by_risk_type: dict[str, Decimal]  # RiskType.value → P&L Decimal
    total_pnl: Decimal
    residual_pnl: Decimal                 # unexplained — large residual = missing risk factor
    fees: Decimal = Decimal("0")
```

### Relationship to existing schemas

- `PortfolioPnLAttribution` (UAC position/:151-168) has 11 named fields (delta_pnl, gamma_pnl, etc.) → Keep for
  backwards compatibility. ExtendedPnLAttribution is the dict-based successor.
- `PnLBreakdown` (UIC risk.py:188-211) has 6 dimensions → Keep as simplified internal view. ExtendedPnLAttribution is
  the comprehensive version.
- Adding volga_pnl, vanna_pnl, slide_pnl etc. requires NO schema change with dict approach — just new keys in
  `pnl_by_risk_type`.

### Computation module

Create: `risk-and-exposure-service/risk_and_exposure_service/core/pnl_engine.py` (~150 lines)

```python
def compute_extended_pnl_attribution(
    positions: list[AggregatedPosition],
    market_data_t0: MarketSnapshot,
    market_data_t1: MarketSnapshot,
    risk_profile: StrategyRiskProfile,
) -> ExtendedPnLAttribution:
    """Decompose P&L change into contributions from each subscribed RiskType."""
```

For each subscribed risk type, compute the P&L contribution:

- delta_pnl = sum(position_delta × price_change) per position
- gamma_pnl = 0.5 × sum(position_gamma × price_change²) per position
- etc.

Aggregate up hierarchy using `RiskPnLNode.children` — instrument → underlying → strategy → account → client → company.

Store daily: `gs://risk/{client_id}/pnl_attribution/{date}.json`

---

## p5-risk-custom-risk-types: Two-Layer Architecture

### Layer 1: Fixed schema (UIC — needs restart)

Add to `unified-internal-contracts/unified_internal_contracts/domain/risk_service/risk.py` (~25 lines):

```python
class CustomRiskEvaluationMethod(StrEnum):
    RATE_SENSITIVITY = "rate_sensitivity"        # what if rate X changes by Y bps?
    SCENARIO_PNL = "scenario_pnl"               # daily P&L under scenario
    THRESHOLD_BREACH = "threshold_breach"        # at what level does P&L turn negative?

class CustomRiskTypeDefinition(BaseModel):
    risk_id: str                                # "eth_borrow_rate_sensitivity"
    display_name: str                           # "ETH Borrow Rate Sensitivity"
    evaluation_method: CustomRiskEvaluationMethod
    applicable_strategies: list[str]            # ["RECURSIVE_STAKED_BASIS", "STAKED_BASIS"]
    description: str
```

### Layer 2: Dynamic parameters (UCI/GCS — hot-reloadable)

Add to `unified-config-interface/unified_config_interface/config.py`:

```python
class CustomRiskScenarioConfig(BaseModel):
    risk_id: str
    shocks: list[float]                         # [0.005, 0.01, 0.02, 0.05]
    metric: str                                 # "daily_pnl_change" | "break_even_level"
    underlying: str | None = None               # "ETH" or None for strategy-wide
    reference_rate: str | None = None           # "eth_borrow_rate" | "btc_funding_rate"
    model_config = {"extra": "forbid"}
```

GCS path: `gs://config/{strategy_id}/custom_risks.yaml`

### Layer 3: Evaluation engine

Create: `risk-and-exposure-service/risk_and_exposure_service/core/custom_risk_evaluator.py` (~120 lines)

```python
def evaluate_custom_risk(
    definition: CustomRiskTypeDefinition,
    scenario: CustomRiskScenarioConfig,
    positions: list[AggregatedPosition],
    current_rates: dict[str, float],
) -> dict[str, Decimal]:
    """Returns {shock_value: pnl_impact} for each shock in scenario.shocks."""
```

Dispatches by `CustomRiskEvaluationMethod`:

- `rate_sensitivity`: perturb rate by shock, recompute daily P&L, return delta
- `scenario_pnl`: apply full scenario, return projected daily P&L
- `threshold_breach`: binary search for rate level where P&L turns negative

Results appear in `RiskPnLNode.risk_by_type` using `risk_id` as key.

---

## p5-risk-matrix-visualization: UI Implementation

### TypeScript types to create

File: `trading-analytics-ui/src/types/risk-matrix.ts` (~80 lines) Mirror UAC/UIC Python schemas 1:1:

```typescript
export enum RiskType {
  DELTA = "delta",
  GAMMA = "gamma" /* ... all 24 values */,
}
export enum RiskCategory {
  FIRST_ORDER = "first_order" /* ... */,
}
export enum RiskAggregationLevel {
  COMPANY = "company",
  CLIENT = "client" /* ... */,
}
export enum DurationBucket {
  OVERNIGHT = "overnight",
  ONE_WEEK = "1w" /* ... */,
}

export interface RiskPnLNode {
  level: RiskAggregationLevel;
  level_id: string;
  risk_by_type: Record<string, number>; // RiskType value → exposure
  pnl_by_type: Record<string, number>;
  var_by_type: Record<string, number>;
  children: RiskPnLNode[];
  subscribed_risks: string[];
}

export interface ExtendedPnLAttribution {
  /* mirrors UIC */
}
export interface TermStructureExposure {
  /* mirrors UIC */
}
export interface CustomRiskTypeDefinition {
  /* mirrors UIC */
}
```

### Pages to create

1. `src/pages/RiskMatrixPage.tsx` — heatmap (rows=underlying, cols=RiskType, cells=exposure)
2. `src/pages/PnLAttributionPage.tsx` — waterfall + over-time stacked area
3. `src/components/risk/AggregationLevelSelector.tsx` — Company→Client→Account→Strategy→Underlying→Instrument toggle
4. `src/components/risk/TermStructureView.tsx` — duration bucket chart
5. `src/components/risk/VenueRiskPanel.tsx` — circuit breaker states
6. Strategy-specific tabs: `OptionsRiskTab.tsx`, `SportsRiskTab.tsx`, `DeFiRiskTab.tsx`

### Data sources

- `/risk/matrix` endpoint on risk-and-exposure-service (NEW — returns RiskPnLNode tree)
- `/portfolio` endpoint on PBMS (existing — returns PortfolioView)
- GCS daily snapshots for over-time P&L charts

### DRY compliance

- TypeScript types mirror Python schemas exactly — consider OpenAPI generation in CI
- No manual type duplication — if Python schema changes, TypeScript must update
- Reuse existing UI components from trading-analytics-ui (Card, Badge, Select from @unified-trading/ui-kit)

---

## Cumulative File Size Analysis (ALL phases combined)

UAC `__init__.py` is the critical file — currently 896/900 lines. After ALL phases: 896 - 48 (removed re-exports) + 3
(RiskType) = **~851 lines (49 margin)**. All other files are well under limit. Full breakdown:

| File                               | Current | Net Delta | Final | Margin |
| ---------------------------------- | ------- | --------- | ----- | ------ |
| UAC `__init__.py`                  | 896     | -45       | ~851  | 49     |
| UAC `canonical/__init__.py`        | 283     | -23       | ~260  | 640    |
| UAC `canonical/domain/__init__.py` | 487     | -18       | ~469  | 431    |
| UAC `analytics.py`                 | 202     | -100      | ~102  | 798    |
| UAC `connectivity.py`              | 116     | -50       | ~66   | 834    |
| UAC `risk.py`                      | 160     | DELETE    | 0     | —      |
| UAC `risk_taxonomy.py` (NEW)       | 0       | +60       | ~60   | 840    |
| UAC errors/`defi.py`               | 414     | +80       | ~494  | 406    |
| UAC errors/`tradfi.py` (NEW)       | 0       | +250      | ~250  | 650    |
| UIC `__init__.py`                  | 717     | +25       | ~742  | 158    |
| UIC domain `risk.py`               | 308     | +205      | ~513  | 387    |
| UIC `factor_exposure.py`           | 68      | +50       | ~118  | 782    |

**RISK**: UAC root `__init__.py` at 851/900. If future Phase 5 additions need more re-exports, this file could exceed
the limit. Consider refactoring: domain facades (errors.py, market.py, execution.py, risk.py) should be the public entry
points, not a 900-line root **init**.py. This is a pre-existing architectural smell — the plan should not make it worse.

## GreeksExposure Migration (DRY fix)

### Current state

- UIC `risk.py:214-235`: `GreeksExposure` (per-instrument: delta,gamma,theta,vega,rho)
- UAC `position/:127-148`: `UnderlyingGreeksBreakdown` + `PortfolioGreeksSnapshot` (per-underlying + portfolio-level)

### Problem

GreeksExposure in UIC is a per-instrument view of data that comes from external sources (Deribit/TARDIS). By the
external-source rule, it belongs in UAC.

### Resolution

Option A: Move GreeksExposure from UIC to UAC canonical/domain/derivatives/ (alongside CanonicalOptionsChainEntry)
Option B: Delete GreeksExposure from UIC — UAC already has UnderlyingGreeksBreakdown which is the same data at the
underlying level, and CanonicalOptionsChainEntry at the instrument level.

**Recommended: Option B** — UAC already has both granularities:

- Per-instrument: `CanonicalOptionsChainEntry` (delta, gamma, theta, vega per option)
- Per-underlying: `UnderlyingGreeksBreakdown` (aggregated delta, gamma, theta, vega, rho)
- Portfolio: `PortfolioGreeksSnapshot` (total + per_underlying list)

GreeksExposure in UIC adds `client_id`, `strategy_id`, `position_quantity` which are internal context. These should be
fields on the RiskPnLNode (which already has level_id for client/strategy) rather than a separate schema.

### Pre-audit for GreeksExposure consumers

- risk-and-exposure-service (multiple files in core/ and tests/)
- PBMS greeks_aggregator.py
- Need full import scan before removing

### Add to Phase 2

If proceeding with Option B: add GreeksExposure removal to p2c (UIC cleanup). Update consumers to use
PortfolioGreeksSnapshot from UAC + RiskPnLNode context fields.

---

## p5-emergency-exit-playbooks: Emergency Exit Playbook System

### Problem

Kill switch blocks new orders but does NOT unwind existing positions. "Close all positions" means completely different
things per strategy type.

### Per-Strategy Exit Definitions

| Strategy               | Exit Type                   | Steps                                                      | Order Matters?                              |
| ---------------------- | --------------------------- | ---------------------------------------------------------- | ------------------------------------------- |
| MOM (spot/perp)        | MARKET_CLOSE                | sell to flat                                               | No                                          |
| BASIS                  | ATOMIC_UNWIND               | close perp + close spot simultaneously                     | YES — naked exposure if one-sided           |
| RECURSIVE_STAKED_BASIS | DELEVERAGE_SEQUENCE         | 1. repay debt → 2. withdraw collateral → 3. swap to stable | YES — wrong order = liquidation             |
| OPTIONS                | DELTA_HEDGE or MARKET_CLOSE | hedge to delta-neutral, then optionally close              | YES — close one leg of spread = naked gamma |
| SPORTS                 | STOP_NEW_ONLY               | block new bets (existing settle by event)                  | N/A                                         |
| LENDING/STAKING        | UNSTAKE_QUEUE               | initiate unbonding (7-28 day wait!)                        | Time-dependent                              |

### Schema (UIC domain/risk_service/risk.py)

```python
class EmergencyExitType(StrEnum):
    MARKET_CLOSE = "market_close"
    ATOMIC_UNWIND = "atomic_unwind"
    DELEVERAGE_SEQUENCE = "deleverage_sequence"
    DELTA_HEDGE = "delta_hedge"
    STOP_NEW_ONLY = "stop_new_only"
    UNSTAKE_QUEUE = "unstake_queue"

class EmergencyExitStep(BaseModel):
    order: int = Field(description="execution sequence — same order = simultaneous")
    action: str = Field(description="close_perp, sell_spot, repay_debt, withdraw_collateral, etc.")
    instrument_filter: str | None = None
    urgency: str = Field(default="immediate", description="immediate | best_effort | queued")
    max_slippage_bps: int = Field(default=50)
    timeout_seconds: int = Field(default=300)

class EmergencyExitPlaybook(BaseModel):
    strategy_type: str
    exit_type: EmergencyExitType
    steps: list[EmergencyExitStep]
    description: str

class ClientRiskTolerance(BaseModel):
    client_id: str
    max_drawdown_pct: Decimal = Field(description="kill switch trigger: e.g. 10.0 = -10%")
    max_var_breach_pct: Decimal = Field(default=Decimal("150"), description="e.g. 150 = 1.5x VaR limit")
    auto_kill_switch_timeout_minutes: int = Field(default=30)
    emergency_exit_override: str | None = Field(default=None, description="close_all | hedge_only | stop_new_only")
```

### Config (GCS via UCI)

Path: `gs://config/emergency/exit_playbooks.yaml` Path: `gs://config/clients/{client_id}/risk_tolerance.yaml`

UCI config class:

```python
class EmergencyExitConfig(BaseModel):
    playbooks: dict[str, EmergencyExitPlaybook]
    model_config = {"extra": "forbid"}
```

### Execution Flow

1. risk-and-exposure-service monitors client drawdown/VaR thresholds
2. Threshold breached → activates kill switch with auto_deactivate_after_minutes from client config
3. Kill switch activation → loads exit playbook for each active strategy
4. Per-strategy: execution-service sends orders per playbook step sequence
5. Steps with same `order` value execute simultaneously (ATOMIC_UNWIND)
6. Steps with ascending `order` values execute sequentially (DELEVERAGE_SEQUENCE)
7. Progress tracked: which step are we on, what's filled, what's pending
8. Monitoring UI shows: active exit tracker, per-step status, fill progress

### DRY Compliance

- Reuses existing kill switch infrastructure (execution-service/engine/kill_switch.py)
- Reuses existing auto_deactivate_after_minutes (just added in p5-cb-kill-switch-auto-deactivate)
- Reuses ClientRiskTolerance.auto_kill_switch_timeout_minutes for the timeout
- Strategy-service already has domain knowledge per strategy type — exit logic lives there
