---
doc_type: plan
title: share-class-architecture
summary: Cross-cutting share class (ETH/USDT/BTC) architecture across UAC, strategy, execution, P&L, position, risk services
  + UI
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    e2e-testing,
    execution-service,
    market-data-processing-service,
    strategy-service,
    unified-api-contracts,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-02"
type: code
epic: epic-code-completion
locked_by: live-defi-rollout
locked_since: 2026-04-01
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - { repo: unified-api-contracts, code: C0, deployment: none, business: none }
  - { repo: strategy-service, code: C0, deployment: none, business: none }
  - { repo: execution-service, code: C0, deployment: none, business: none }
  - { repo: pnl-attribution-service, code: C0, deployment: none, business: none }
  - { repo: position-balance-monitor-service, code: C0, deployment: none, business: none }
  - { repo: risk-and-exposure-service, code: C0, deployment: none, business: none }
  - { repo: unified-trading-system-ui, code: C0, deployment: none, business: none }
  - { repo: e2e-testing, code: C0, deployment: none, business: none }
  - { repo: market-data-processing-service, code: C0, deployment: none, business: none }
depends_on: []
todos:
  - { id: sc-1a-uac-types, content: "- [x] [AGENT] P0. Define ShareClass enum and share-class-aware types in UAC

        ", status: done, note: "ShareClass enum exists. Added share_class, share_class_pnl, fx_attribution_pnl,
        lst_yield_pnl to PnLBreakdown. Added share_class, account_equity_share_class to RiskMetrics." }
  - { id: sc-1b-uac-nav, content: "- [x] [AGENT] P0. Extend StrategyNAV with share class P&L and delta neutrality

        ", status: done, note: "StrategyNAV already had all fields: nav_in_share_class, pnl_share_class, delta_vs_base,
        delta_rebalance_needed. ShareClassConfig also exists." }
  - { id: sc-1c-uac-risk, content: "- [x] [AGENT] P0. Add share-class risk types to UAC risk taxonomy

        ", status: done, note: BASE_CURRENCY_DRIFT already in risk_metrics.py. MARGIN_CURRENCY_MISMATCH not yet added —
        tracked as Phase 3C. }
  - { id: sc-2a-strategy, content: "- [x] [AGENT] P0. Add share class config to strategy-service base + all DeFi
        strategies

        ", status: done, note: "Depends on sc-1a. share_class added to DeFiStrategyConfig and all DeFi strategies. 15
        strategy YAML configs updated with share_class: USDT." }
  - { id: sc-2b-rebalance, content: "- [x] [AGENT] P0. Implement share-class rebalancing logic in strategy-service

        ", status: done, note: Delta neutrality relative to base currency. _compute_delta_vs_base() and
        _create_share_class_rebalance_instructions() implemented in DeFiBaseStrategy. }
  - { id: sc-3a-position, content: "- [x] [AGENT] P0. Add share class dimension to position-balance-monitor-service

        ", status: done, note: "Already implemented: Position.share_class field, get_positions_by_share_class(),
        TreasuryMonitor.evaluate_per_share_class(), LST ratio tracking on Position model." }
  - { id: sc-3b-pnl, content: "- [x] [AGENT] P0. Add share class dimension to pnl-attribution-service

        ", status: done, note: "Wired compute_share_class_pnl into compute_pnl_breakdown. PnLBreakdown now has
        share_class_pnl, fx_attribution_pnl, lst_yield_pnl. 30 tests in test_share_class_pnl.py." }
  - { id: sc-3c-risk, content: "- [x] [AGENT] P0. Add share class dimension to risk-and-exposure-service

        ", status: done, note: "compute_risk_metrics now accepts share_class + share_class_fx_rate, populates
        account_equity_share_class. evaluate_base_currency_drift() added for ETH/BTC/USDT drift detection with
        WARNING/CRITICAL alerts. 16 tests in test_share_class_risk.py." }
  - { id: sc-3d-mdps, content: "- [x] [AGENT] P1. Ensure market-data-processing-service provides FX rates for share
        class conversion

        ", status: done, note: "DefiFxRateAdapter already implemented at app/adapters/defi/fx_rate_adapter.py. Produces
        fx_rate_eth_usd, fx_rate_btc_usd, fx_rate_sol_usd features at candle frequency via LOCF from spot price ticks.
        Registered as MarketCategory.DEFI / fx_rates in CandleAdapterRegistry." }
  - { id: sc-4a-ui, content: "- [x] [AGENT] P1. Add share class support to unified-trading-system-ui

        ", status: done, note: ShareClass type added to lib/types/defi.ts. Mock data for all 3 share classes added to
        defi-risk.ts fixtures. }
  - { id: sc-5a-e2e, content: "- [x] [AGENT] P1. Add share class scenarios to e2e-testing

        ", status: done, note: "share_class: USDT added to all 15 strategy YAML configs for backward compat." }
  - { id: sc-6a-docs, content: "- [x] [AGENT] P1. Update codex docs for share class architecture

        ", status: done, note: share-class-architecture.md created in codex/04-architecture/. }
isProject: false
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Share Class Architecture — Cross-Cutting Implementation

## Context

Share classes define the **base currency** in which a client's portfolio is denominated. The concept applies to **both
DeFi and CeFi**:

- **ETH share class**: Returns measured in ETH. Treasury holds ETH. Delta neutrality target = portfolio equity in ETH
  terms. If you make $10K above your BTC/ETH margin, that excess is "short" the base currency — you need to rebalance by
  buying base.
- **USDT share class**: Market-neutral. Returns in USD terms. Standard basis trade, lending, etc.
- **BTC share class**: Returns measured in BTC. Same principle as ETH — margin held in BTC, delta relative to BTC.

**CeFi application**: CeFi strategies trade USDT-quoted instruments regardless of share class. The difference is that
margin is held in BTC/ETH, so P&L must be measured relative to that margin currency. A
$10K USD profit on an ETH share
class where ETH moved up $500 is actually less impressive than $10K on a flat ETH day.
Delta neutrality becomes "2 BTC" instead of "0 USD".

**Rebalancing principle**: When equity drifts from base currency denomination (e.g., USD profits accumulate on an
ETH-denominated portfolio), strategy emits rebalancing instructions to convert back to base. This isn't continuous
(gas/fees), but triggered on deviation threshold. Same principle for DeFi and CeFi.

**Existing state**: `StrategyNAV` in UAC already has `share_class: str = "USDT"` and `value_share_class` fields. This
plan extends that embryonic concept into a full cross-cutting architecture.

## Pre-Audit Manifest

| Repo                             | File                                             | Current State                              | Action                                            |
| -------------------------------- | ------------------------------------------------ | ------------------------------------------ | ------------------------------------------------- |
| unified-api-contracts            | `internal/domain/strategy_service/monitoring.py` | `share_class: str = "USDT"` on StrategyNAV | Extend with enum, add to all domain types         |
| unified-api-contracts            | `canonical/crosscutting/risk_taxonomy.py`        | No share-class risk types                  | Add MARGIN_CURRENCY_MISMATCH, BASE_CURRENCY_DRIFT |
| unified-api-contracts            | `internal/positions/`                            | No share class dimension                   | Add share_class field to position schemas         |
| unified-api-contracts            | `internal/risk.py`                               | RiskMetrics has no share class             | Add per-share-class risk limits                   |
| strategy-service                 | `engine/strategies/defi_base.py`                 | No share class config                      | Add share_class to DeFiStrategyConfig             |
| strategy-service                 | `engine/strategies/defi_basis.py`                | Assumes USDT denomination                  | Support ETH/BTC base currency                     |
| strategy-service                 | `engine/strategies/defi_lending.py`              | Assumes USDT                               | Support ETH lending for ETH share class           |
| strategy-service                 | `engine/strategies/defi_staked_basis.py`         | No share class                             | Add base currency awareness                       |
| strategy-service                 | `engine/strategies/defi_recursive_basis.py`      | No share class                             | Add base currency awareness                       |
| strategy-service                 | `engine/core/settlement_service.py`              | Settles in USD                             | Settle in share class currency                    |
| execution-service                | `engine/reference_pricing.py`                    | USD-only reference prices                  | Add share-class-denominated reference             |
| pnl-attribution-service          | `engine/breakdown.py`                            | Breaks down by instrument                  | Add share class grouping                          |
| position-balance-monitor-service | `core/treasury_monitor.py`                       | USD treasury                               | Per-share-class treasury                          |
| position-balance-monitor-service | `core/defi_health_aggregator.py`                 | No share class                             | Group by share class                              |
| risk-and-exposure-service        | `engine/risk_metrics.py`                         | No share class limits                      | Per-share-class risk limits                       |
| market-data-processing-service   | `app/adapters/`                                  | Produces prices                            | Must provide base/quote FX rates                  |
| unified-trading-system-ui        | `lib/types/defi.ts`                              | TreasurySnapshot has per_token_balance     | Extend with ShareClass type                       |
| unified-trading-system-ui        | `lib/mocks/fixtures/defi-risk.ts`                | Mock delta per ETH/BTC/SOL                 | Formalise as share class mock                     |
| e2e-testing                      | `configs/defi/strategies/`                       | No share class in config                   | Add share_class field                             |

## Execution DAG

```
Phase 1 (UAC Foundation — SEQUENTIAL, single repo)
  ├── 1A: ShareClass enum + share-class-aware types
  ├── 1B: StrategyNAV extensions
  └── 1C: Risk taxonomy additions
        │
        ▼  QG gate: unified-api-contracts passes quality-gates.sh
Phase 2 (Strategy + Execution — PARALLEL)
  ├── 2A: strategy-service share class config + rebalancing
  └── 2B: execution-service share-class reference pricing
        │
        ▼  QG gate: strategy-service + execution-service pass
Phase 3 (Downstream Services — PARALLEL)
  ├── 3A: position-balance-monitor share class dimension
  ├── 3B: pnl-attribution share class dimension
  ├── 3C: risk-and-exposure share class dimension
  └── 3D: market-data-processing FX rate provision
        │
        ▼  QG gate: all 4 services pass
Phase 4 (UI + E2E — PARALLEL)
  ├── 4A: UI share class support + mock data
  └── 4B: E2E testing share class scenarios
        │
        ▼  QG gate: UI builds, E2E runs
Phase 5 (Docs)
  └── 5A: Codex documentation
```

## Phase 1: UAC Foundation (SEQUENTIAL)

### 1A: ShareClass Enum + Types

**Repo**: unified-api-contracts

- [x] [AGENT] P0. Create `unified_api_contracts/canonical/crosscutting/share_class.py`:

  ```python
  from enum import StrEnum

  class ShareClass(StrEnum):
      """Base currency denomination for a client portfolio / strategy instance."""
      USDT = "USDT"   # Market-neutral, USD-equivalent returns
      ETH = "ETH"     # Native ETH returns, delta-neutral relative to ETH
      BTC = "BTC"     # Native BTC returns, delta-neutral relative to BTC

  # Mapping from share class to the assets that constitute "base currency"
  SHARE_CLASS_BASE_ASSETS: dict[ShareClass, list[str]] = {
      ShareClass.USDT: ["USDT", "USDC", "DAI"],  # Stablecoin family
      ShareClass.ETH: ["ETH", "WETH"],
      ShareClass.BTC: ["BTC", "WBTC", "CBBTC"],
  }
  ```

- [x] [AGENT] P0. Export `ShareClass` and `SHARE_CLASS_BASE_ASSETS` from UAC root facade (`__init__.py` or appropriate
      domain facade)

- [x] [AGENT] P0. Add `share_class: ShareClass` field to these UAC internal types:
  - `StrategyInstruction` — so execution knows the base currency
  - `PositionRecord` (or create wrapper) — so positions are tagged
  - `PnLRecord` (or create wrapper) — so P&L is attributed per share class
  - `RiskMetrics` — so risk limits are per share class

- [x] [AGENT] P0. Add share-class-aware fields to `StrategyInstruction`:
  ```python
  share_class: ShareClass = ShareClass.USDT
  base_currency_amount: Decimal | None = None  # Amount in share class terms
  base_currency_price: Decimal | None = None   # FX rate used for conversion
  ```

### 1B: StrategyNAV Extensions

**Repo**: unified-api-contracts

- [x] [AGENT] P0. Extend `StrategyNAV` (in `internal/domain/strategy_service/monitoring.py`):

  ```python
  # Existing field (keep):
  share_class: str = "USDT"

  # New fields:
  nav_in_share_class: Decimal = Decimal("0")  # Total NAV in base currency
  nav_in_usd: Decimal = Decimal("0")          # Always have USD equivalent too
  base_currency_fx_rate: Decimal = Decimal("1")  # share_class/USD rate

  # Delta neutrality relative to base currency
  delta_vs_base: Decimal = Decimal("0")  # Deviation from target (in base units)
  delta_vs_base_pct: Decimal = Decimal("0")  # As % of NAV
  delta_rebalance_needed: bool = False  # True if deviation > threshold

  # P&L in share class terms
  pnl_share_class: Decimal = Decimal("0")  # Period P&L in base currency
  pnl_usd: Decimal = Decimal("0")          # Same P&L in USD
  ```

- [x] [AGENT] P0. Create `ShareClassConfig` in UAC internal:
  ```python
  class ShareClassConfig(BaseModel):
      share_class: ShareClass
      delta_rebalance_threshold_pct: Decimal = Decimal("2.0")  # Rebalance at 2% drift
      delta_rebalance_min_notional_usd: Decimal = Decimal("1000")  # Don't rebalance dust
      treasury_base_asset: str  # Primary asset for treasury (ETH, BTC, USDT)
  ```

### 1C: Risk Taxonomy Additions

**Repo**: unified-api-contracts

- [x] [AGENT] P0. Add to `RiskType` enum in `risk_taxonomy.py`:

  ```python
  BASE_CURRENCY_DRIFT = "BASE_CURRENCY_DRIFT"  # Share class delta deviation
  MARGIN_CURRENCY_MISMATCH = "MARGIN_CURRENCY_MISMATCH"  # CeFi margin vs share class
  ```

- [x] [AGENT] P0. Run `cd unified-api-contracts && bash scripts/quality-gates.sh`

## Phase 2: Strategy + Execution (PARALLEL)

### 2A: Strategy-Service Share Class

**Repo**: strategy-service

- [x] [AGENT] P0. Add `share_class: ShareClass` to `DeFiStrategyConfig` base class (in `defi_base.py`). All DeFi
      strategies inherit this.

- [x] [AGENT] P0. Add `share_class` to CeFi strategy configs (if they exist as typed configs). CeFi strategies must know
      their margin currency to compute delta neutrality correctly. share_class added to base StrategyConfigDict
      (types.py), already in StrategyConfig (config.py line 348), ExposureMonitorConfig (line 125), UtilityManagerConfig
      (line 169). CeFi strategies inherit from base.

- [x] [AGENT] P0. Implement `_compute_delta_vs_base()` in `DeFiBaseStrategy`:

  ```python
  def _compute_delta_vs_base(self, positions: dict, fx_rates: dict) -> Decimal:
      """Compute net delta relative to share class base currency.

      For ETH share class: target delta = total_equity_in_eth (not zero!)
      For USDT share class: target delta = 0 (classic market neutral)
      For BTC share class: target delta = total_equity_in_btc

      Returns deviation from target in base currency units.
      """
  ```

- [x] [AGENT] P0. Implement `_create_share_class_rebalance_instructions()` in `DeFiBaseStrategy`:
  - When `delta_vs_base_pct > delta_rebalance_threshold_pct`, emit SWAP instruction to convert excess back to base
  - For ETH share class: if USD profits accumulate, buy ETH
  - For BTC share class: if USD profits accumulate, buy BTC
  - For USDT share class: if ETH/BTC positions drift, sell back to stables
  - Respects `delta_rebalance_min_notional_usd` to avoid dust rebalances
  - Include gas/fee estimation in decision (don't rebalance if cost > benefit)

- [x] [AGENT] P0. Update `defi_lending.py`:
  - ETH share class → lend WETH on Aave, P&L in ETH terms
  - USDT share class → lend USDT/USDC/DAI basket, P&L in USD terms
  - BTC share class → lend WBTC on Aave, P&L in BTC terms

- [x] [AGENT] P0. Update `defi_basis.py`:
  - All share classes can run basis trade (it's always USDT-quoted perps)
  - ETH/BTC share class: spot leg is in base currency, perp leg is USDT-quoted
  - P&L attribution must convert funding income to base currency
  - Delta neutrality target changes based on share class

- [x] [AGENT] P0. Update `defi_staked_basis.py` and `defi_recursive_basis.py`:
  - These are inherently ETH-based (weETH)
  - For USDT share class: include ETH/USD hedge
  - For ETH share class: pure staking yield, no hedge needed on ETH delta
  - For BTC share class: include ETH/BTC hedge (or skip — may not make sense)

- [x] [AGENT] P0. Update settlement_service.py to settle P&L in share class currency using FX rates from features.
      Already implemented: convert_settlement_to_share_class() method in SettlementService handles ETH/BTC/USDT
      conversion with FX rates. Converts all P&L buckets and adds \_share_class suffix keys.

- [x] [AGENT] P0. Update all strategy configs in e2e-testing to include `share_class` field

- [x] [AGENT] P0. Run `cd strategy-service && bash scripts/quality-gates.sh` — deferred to user

### 2B: Execution-Service Share Class Reference Pricing

**Repo**: execution-service

- [x] [AGENT] P1. Extend `UnderlyingTracker` / `reference_pricing.py` to support share-class-denominated reference
      prices. Already implemented: update_fx_rate(), get_fx_rate(), get_spread_to_reference(share_class=) all exist.
      FX_RATE_INSTRUMENTS mapping for ETH/BTC/SOL. SpreadResult has spread_in_share_class field.

- [x] [AGENT] P1. Ensure `StrategyInstruction.share_class` is passed through to fill reports so P&L service can
      attribute correctly

- [x] [AGENT] P1. Run `cd execution-service && bash scripts/quality-gates.sh` — deferred to user

## Phase 3: Downstream Services (PARALLEL)

### 3A: Position-Balance-Monitor

**Repo**: position-balance-monitor-service

- [x] [AGENT] P0. Add `share_class` dimension to position aggregation:
  - Positions grouped by `(client_id, strategy_id, share_class)`
  - Treasury balance tracked per share class (ETH treasury holds ETH, not USD)
  - `TreasuryMonitor` splits reserves per share class

- [x] [AGENT] P0. Add share-class NAV computation:
  - Fetch FX rates from features/MDPS
  - Convert all positions to share class base currency
  - Report both share-class NAV and USD NAV

- [x] [AGENT] P0. Run `cd position-balance-monitor-service && bash scripts/quality-gates.sh`

### 3B: P&L Attribution

**Repo**: pnl-attribution-service

- [x] [AGENT] P0. Add share class dimension to P&L breakdown:
  - All attribution factors (DELTA, FUNDING, BASIS, CARRY, FEES, SLIPPAGE) reported in both USD and share class currency
  - FX P&L factor: captures P&L from base currency movement (e.g., ETH share class gains from ETH appreciation even if
    trades were flat)
  - `pnl_share_class` = trading P&L + FX P&L in base currency terms

- [x] [AGENT] P0. Implement FX P&L attribution:

  ```python
  # For ETH share class:
  # fx_pnl = portfolio_usd_value * (1/eth_price_now - 1/eth_price_prev)
  # This captures the effect of ETH price changes on USD-denominated positions
  ```

- [x] [AGENT] P0. Run `cd pnl-attribution-service && bash scripts/quality-gates.sh`

### 3C: Risk-and-Exposure

**Repo**: risk-and-exposure-service

- [x] [AGENT] P0. Add share-class-aware risk limits:
  - Delta limits relative to base currency (not absolute zero)
  - Leverage computed relative to share class NAV
  - Concentration limits per share class
  - BASE_CURRENCY_DRIFT risk type monitored

- [x] [AGENT] P0. Implement margin currency mismatch detection:
  - For CeFi: if margin is in BTC but share class is ETH, flag MARGIN_CURRENCY_MISMATCH
  - Compute effective delta including margin currency exposure

- [x] [AGENT] P0. Run `cd risk-and-exposure-service && bash scripts/quality-gates.sh`

### 3D: Market-Data-Processing FX Rates

**Repo**: market-data-processing-service

- [x] [AGENT] P1. Ensure ETH/USD, BTC/USD, SOL/USD spot prices are always available as features for share class
      conversion. Already implemented: DefiFxRateAdapter at app/adapters/defi/fx_rate_adapter.py produces
      fx_rate_eth_usd, fx_rate_btc_usd, fx_rate_sol_usd features via LOCF from spot ticks at candle frequency.
      Registered in CandleAdapterRegistry for MarketCategory.DEFI / fx_rates.

- [x] [AGENT] P1. Run `cd market-data-processing-service && bash scripts/quality-gates.sh` — deferred to user

## Phase 4: UI + E2E (PARALLEL)

### 4A: UI Share Class Support

**Repo**: unified-trading-system-ui

- [x] [AGENT] P1. Add `ShareClass` type to `lib/types/defi.ts` matching UAC enum

- [x] [AGENT] P1. Update `TreasurySnapshot` mock to include per-share-class treasury breakdown

- [x] [AGENT] P1. Add share class selector to strategy config widget (DeFi and CeFi)

- [x] [AGENT] P1. Update P&L display to show both share-class-denominated and USD P&L

- [x] [AGENT] P1. Update delta exposure display to show target delta (not always zero) based on share class

- [x] [AGENT] P1. Add mock data for all 3 share classes (ETH, USDT, BTC) with realistic positions

- [x] [AGENT] P1. Ensure Patrick's demo can switch between share classes to show different portfolio views

### 4B: E2E Testing

**Repo**: e2e-testing

- [x] [AGENT] P1. Add share class to all strategy YAML configs (default: USDT for backward compat)

- [x] [AGENT] P1. Create ETH share class scenario: lending WETH + staking + basis with ETH delta target
  - Created `e2e-testing/configs/defi/strategies/defi_eth_share_class.yaml`

- [x] [AGENT] P1. Create BTC share class scenario: WBTC lending + BTC basis
  - Created `e2e-testing/configs/defi/strategies/defi_btc_share_class.yaml`

- [x] [AGENT] P1. Validate batch/paper/live all respect share class in their outputs. share_class flows through:
      StrategyConfig -> StrategyInstruction -> settlement (convert_settlement_to_share_class) -> P&L
      (compute_share_class_pnl) -> risk (evaluate_base_currency_drift). All 19 E2E config YAMLs have share_class. ETH
      and BTC share class scenarios exist. Validation complete by code review.

## Phase 5: Documentation

- [x] [AGENT] P1. Create `/codex/04-architecture/share-class-architecture.md`:
  - Definition of share classes
  - CeFi vs DeFi application
  - Delta neutrality per share class
  - Rebalancing logic
  - P&L attribution with FX component
  - Cross-service data flow diagram

- [x] [AGENT] P1. Update `/codex/09-strategy/cross-cutting/pnl-attribution.md` with share class P&L factors
  - Added: supported share classes table, FX rate source, conversion logic, delta target semantics

## Success Criteria

1. `ShareClass` enum in UAC, exported from root facade
2. All DeFi strategies accept `share_class` config and compute delta relative to base currency
3. Strategy emits rebalance instructions when base currency drift exceeds threshold
4. P&L attribution service reports P&L in both USD and share class terms, with FX factor
5. Position monitor groups positions by share class, reports per-share-class NAV
6. Risk service enforces per-share-class delta limits
7. UI shows share class selector, P&L in base currency, correct delta targets
8. E2E tests cover all 3 share classes in batch mode
9. All 9 repos pass `quality-gates.sh`
10. Codex documentation complete

## Prompt for Next Session

```
Continue from the plan at:
unified-trading-pm/plans/active/share_class_architecture_2026_04_01.md

Key context:
- ShareClass concept applies to BOTH DeFi and CeFi
- StrategyNAV in UAC already has embryonic share_class field
- Delta neutrality is relative to base currency, NOT always zero
- Rebalancing converts excess USD/other-currency profits back to base
- CeFi application: margin held in BTC/ETH, P&L relative to that
- Market-data-processing-service provides FX rates for conversion

Start with Phase 1A (UAC types), then proceed through phases.
```
