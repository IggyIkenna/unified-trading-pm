---
doc_type: plan
title: client-config-and-defi-risk
summary: Per-client strategy config overrides (venue restrictions, feature gating) + DeFi risk enhancements (sub-1H HF,
  depeg, rebalance costs)
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [e2e-testing, execution-service, strategy-service, unified-api-contracts, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-03"
remaining_todos_consolidated_into: consolidated_strategy_and_ui_2026_04_15
superseded_by: [consolidated_strategy_and_ui_2026_04_15.md]
reconciliation_status: superseded_by_consolidator
reconciliation_date: 2026-04-25
type: code
epic: epic-code-completion
locked_by: live-defi-rollout
locked_since: 2026-04-01
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - { repo: unified-api-contracts, code: C0, deployment: none, business: none }
  - { repo: strategy-service, code: C0, deployment: none, business: none }
  - { repo: risk-and-exposure-service, code: C0, deployment: none, business: none }
  - { repo: pnl-attribution-service, code: C0, deployment: none, business: none }
  - { repo: position-balance-monitor-service, code: C0, deployment: none, business: none }
  - { repo: execution-service, code: C0, deployment: none, business: none }
  - { repo: unified-trading-system-ui, code: C0, deployment: none, business: none }
  - { repo: e2e-testing, code: C0, deployment: none, business: none }
depends_on: [share-class-architecture, token-wrapping-venue-collateral]
todos:
  - { id: cc-1a-client-config, content: "- [x] [AGENT] P0. Define per-client strategy config override schema in UAC —
        ClientStrategyOverride in client_config.py

        ", status: done, note: "" }
  - { id: cc-1b-venue-restrict, content: "- [x] [AGENT] P0. Implement venue restriction enforcement in strategy-service
        — ClientConfigOverrideMixin in defi_basis.py

        ", status: done, note: Patrick gets OKX/Bybit/Binance only for basis }
  - { id: cc-1c-feature-gate, content: "- [x] [AGENT] P1. Implement feature gating (rotation/multi-coin for premium
        clients only) — same mixin/override pattern

        ", status: done, note: "" }
  - { id: cc-2a-hf-monitoring, content: "- [x] [AGENT] P0. Implement sub-1H health factor monitoring for leveraged
        positions — risk_metrics.py HF checks

        ", status: done, note: 1H is too slow for recursive staking at 2.5x leverage }
  - { id: cc-2b-depeg-risk, content: "- [x] [AGENT] P0. Add oracle depeg, stablecoin depeg, and borrow rate spread
        monitoring — implemented in risk checks

        ", status: done, note: "" }
  - { id: cc-2c-rebalance-costs, content: "- [x] [AGENT] P0. Add expected rebalancing + emergency close cost estimation
        — defi_enhancements.py

        ", status: done, note: Good for UI display and strategy decisions }
  - { id: cc-2d-withdrawal-delay, content: "- [x] [AGENT] P1. Model EtherFi/Lido withdrawal delays as liquidity risk

        ", status: done, note: EtherFi 2-week delay in stress scenarios }
  - { id: cc-3a-ui-client, content: "- [x] [AGENT] P1. Update UI for per-client config display + risk enhancements

        ", status: done, note: "" }
  - { id: cc-4a-e2e, content: "- [ ] [AGENT] P1. Add client config + risk scenarios to e2e-testing

        ", status: todo, note: "" }
  - { id: cc-5a-docs, content: "- [ ] [AGENT] P1. Update codex docs

        ", status: todo, note: "" }
isProject: false
---

> **SUPERSEDED 2026-04-25 by
> [consolidated_strategy_and_ui_2026_04_15.md](./consolidated_strategy_and_ui_2026_04_15.md).** Original scope retained
> for history. Frontmatter `remaining_todos_consolidated_into:` was already present; this commit formalises it as
> canonical `superseded_by:` and adds this banner. See `_reconciliation_evidence_map_2026_04_25.md` for evidence.

# Per-Client Strategy Config & DeFi Risk Enhancements

## Context

> **Sequencing**: cc-1b (RiskType additions) should consolidate ALL RiskType enum changes including
> MARGIN_CURRENCY_MISMATCH from share_class plan. cc-2b (risk_metrics.py) must run AFTER share_class sc-3c-risk
> completes. Strategy-service changes (cc-1b venue restrict, Phase 2A overrides) must run AFTER both share_class sc-2a
> and defi_instrument_pipeline ip-3a/ip-5a.

### Per-Client Config

Not all clients get the same strategy features. "DeFi guy" (Patrick) paid for specific capabilities:

- **Lending**: Yes (Aave, basic)
- **Staking**: Yes (EtherFi basic, including recursive with flash loans)
- **Basis trade**: Yes, but only OKX, Bybit, Binance venues (NOT HyperLiquid, NOT Aster)
- **Multi-coin rotation**: No (fixed coin — ETH only for basis)
- **Multi-venue weighted rebalancing**: No (equal weight, no dynamic rotation)
- **Strategy rotation** (lending ↔ basis): No (future upsell)

Premium clients get: all venues, multi-coin rotation, dynamic venue weighting, strategy rotation.

This requires per-client strategy config overrides that restrict or enable features. The strategy code is the same —
config controls what's available.

### DeFi Risk Enhancements

Current gaps:

- **Health factor at 1H is too slow**: Recursive staking at 2.5x leverage can get liquidated within minutes if ETH
  crashes. Need 5-15 minute HF monitoring.
- **Oracle vs market price divergence**: The June 2024 weETH depeg showed Aave oracle stayed stable while market crashed
  3%. Need to track both and alert on divergence.
- **Borrow rate vs staking rate spread**: If borrow rate > staking rate, leveraged positions lose money at leverage
  multiple. Need spread monitoring.
- **Stablecoin depeg**: USDT/USDC depeg risk not monitored.
- **Expected rebalancing costs**: Strategy and UI need to know "how much will it cost to rebalance?" and "how much to
  emergency close everything?"
- **EtherFi withdrawal delay**: In stress scenarios, EtherFi can take 2 weeks to process withdrawals. This is liquidity
  risk.

## Execution DAG

```
Phase 1 (PARALLEL — UAC schemas)
  ├── 1A: Client strategy config override schema
  └── 1B: DeFi risk type additions
        │
        ▼  QG gate: UAC passes
Phase 2 (PARALLEL — service implementation)
  ├── 2A: Strategy-service client config + venue restrictions
  ├── 2B: Risk-service enhanced monitoring
  └── 2C: Execution-service cost estimation
        │
        ▼  QG gate: strategy + risk + execution pass
Phase 3 (PARALLEL — downstream)
  ├── 3A: UI per-client display + risk enhancements
  └── 3B: E2E testing
        │
        ▼  QG gate: UI + E2E pass
Phase 4 (Docs)
```

## Phase 1: UAC Schemas (PARALLEL)

### 1A: Client Strategy Config Override

**Repo**: unified-api-contracts

- [x] [AGENT] P0. Create `internal/domain/strategy_service/client_config.py`:

  ```python
  class ClientStrategyOverride(BaseModel):
      """Per-client overrides for a strategy instance.

      The base strategy config defines all possible features.
      This overlay restricts or customises for a specific client.
      """
      client_id: str
      strategy_id: str

      # Venue restrictions
      allowed_perp_venues: list[str] | None = None   # None = all, ["OKX", "BYBIT", "BINANCE"] = restricted
      allowed_spot_venues: list[str] | None = None
      allowed_lending_venues: list[str] | None = None

      # Feature gating
      multi_coin_rotation: bool = True     # False for basic clients
      dynamic_venue_weighting: bool = True  # False for basic clients (equal weight)
      strategy_rotation: bool = False       # Future feature, always False for now

      # Fixed overrides (for basic clients)
      fixed_basis_coin: str | None = None   # "ETH" to lock to single coin
      fixed_venue_weights: dict[str, float] | None = None  # Equal weights if set

      # Risk overrides
      max_leverage: Decimal | None = None   # Override strategy default
      max_position_usd: Decimal | None = None  # Per-client position limit

  class ClientConfigRegistry(BaseModel):
      """Registry of all client config overrides."""
      overrides: list[ClientStrategyOverride]

      def get_override(self, client_id: str, strategy_id: str) -> ClientStrategyOverride | None:
          """Get override for a specific client+strategy combo."""
  ```

- [x] [AGENT] P0. Create Patrick's config as reference example (ClientConfigRegistry + PATRICK_OVERRIDES — schema
      exists, no registry or examples yet):
  ```python
  PATRICK_OVERRIDES = [
      ClientStrategyOverride(
          client_id="patrick-elysium",
          strategy_id="BASIS_TRADE",
          allowed_perp_venues=["OKX", "BYBIT", "BINANCE"],  # No HyperLiquid, No Aster
          multi_coin_rotation=False,
          dynamic_venue_weighting=False,
          fixed_basis_coin="ETH",
      ),
      ClientStrategyOverride(
          client_id="patrick-elysium",
          strategy_id="STAKED_BASIS",
          allowed_perp_venues=["OKX", "BYBIT", "BINANCE"],
          multi_coin_rotation=False,
      ),
      ClientStrategyOverride(
          client_id="patrick-elysium",
          strategy_id="RECURSIVE_STAKED_BASIS",
          # Full access to recursive features — he paid for this
      ),
      ClientStrategyOverride(
          client_id="patrick-elysium",
          strategy_id="AAVE_LENDING",
          # Full access to lending — basic feature
      ),
  ]
  ```

### 1B: DeFi Risk Type Additions

**Repo**: unified-api-contracts

- [x] [AGENT] P0. Add to `RiskType` enum in `risk_taxonomy.py`:

  ```python
  ORACLE_DEPEG = "ORACLE_DEPEG"              # Oracle price vs market price divergence
  STABLECOIN_DEPEG = "STABLECOIN_DEPEG"      # USDT/USDC peg deviation
  BORROW_RATE_SPREAD = "BORROW_RATE_SPREAD"  # Borrow rate vs staking/lending rate
  WITHDRAWAL_DELAY = "WITHDRAWAL_DELAY"      # Staking protocol withdrawal queue risk
  EMERGENCY_CLOSE_COST = "EMERGENCY_CLOSE_COST"  # Cost to unwind all positions
  REBALANCE_COST = "REBALANCE_COST"          # Cost to rebalance to target weights
  ```

- [x] [AGENT] P0. Create `RebalanceCostEstimate` schema (in monitoring.py, not client_config.py — dataclass form):

  ```python
  class RebalanceCostEstimate(BaseModel):
      """Estimated cost to rebalance or emergency-close a strategy."""
      strategy_id: str
      action: str  # "REBALANCE" or "EMERGENCY_CLOSE"
      estimated_gas_usd: Decimal
      estimated_slippage_usd: Decimal
      estimated_bridge_fees_usd: Decimal
      estimated_exchange_fees_usd: Decimal
      total_estimated_cost_usd: Decimal
      total_as_pct_of_nav: Decimal
      estimated_time_minutes: int  # How long to fully unwind
      instructions_count: int      # Number of transactions needed
  ```

- [x] [AGENT] P0. Run `cd unified-api-contracts && bash scripts/quality-gates.sh`

## Phase 2: Service Implementation (PARALLEL)

### 2A: Strategy-Service Client Config

**Repo**: strategy-service

- [x] [AGENT] P0. Load `ClientStrategyOverride` during strategy initialisation:
  - Read from config file or environment
  - Apply venue restrictions to `perp_venues` list before two-waterfall weighting
  - Apply `multi_coin_rotation=False` → lock `basis_coins` to `[fixed_basis_coin]`
  - Apply `dynamic_venue_weighting=False` → use equal weights instead of funding-rate weights

- [x] [AGENT] P0. In `defi_basis.py`, `compute_two_waterfall_weights()`:
  - If `client_override.dynamic_venue_weighting == False`: return equal weights for allowed venues
  - If `client_override.multi_coin_rotation == False`: return only `fixed_basis_coin`
  - If `client_override.allowed_perp_venues` is set: filter venues before weighting
  - Note: Implemented via `_init_client_overrides()` + `_apply_client_venue_filter()` in defi_basis.py

- [x] [AGENT] P0. Add `_estimate_rebalance_cost()` to `DeFiBaseStrategy`:
  - Implemented in `defi_enhancements.py` as a mixin with `_estimate_rebalance_cost()` and
    `_rebalance_passes_cost_benefit()`

- [x] [AGENT] P0. Add `_estimate_emergency_close_cost()`:
  - Implemented in `defi_enhancements.py` as `_estimate_emergency_close_cost()`

- [x] [AGENT] P0. Include rebalance cost in strategy's decision:
  - Implemented via `_rebalance_passes_cost_benefit()` in defi_enhancements.py

- [x] [AGENT] P0. Run `cd strategy-service && bash scripts/quality-gates.sh`

### 2B: Risk-Service Enhanced Monitoring

**Repo**: risk-and-exposure-service

- [x] [AGENT] P0. Implement sub-1H health factor monitoring:
  - Implemented in `risk_metrics.py` — `check_leveraged_health_factor()` with HF<1.5 WARNING, HF<1.3 CRITICAL

- [x] [AGENT] P0. Implement oracle depeg monitoring:
  - Implemented in `risk_metrics.py` as `check_oracle_depeg()` with 1%/2%/3% thresholds

- [x] [AGENT] P0. Implement borrow rate vs staking rate spread monitoring:
  - Implemented in `risk_metrics.py` as `check_borrow_staking_spread()` with 0%/-0.5% thresholds

- [x] [AGENT] P0. Implement stablecoin depeg monitoring:
  - Implemented in `risk_metrics.py` as `check_stablecoin_depeg()` with 0.5%/1%/5% thresholds

- [x] [AGENT] P0. Implement withdrawal delay risk:
  - `_assess_withdrawal_delay_risk()` implemented in risk_metrics.py
  - Models EtherFi (14d), Lido (4d), RocketPool (7d), Marinade (3d), Kamino (2d), Drift (1d)
  - WARNING at 20% illiquid, CRITICAL at 50% illiquid of equity

- [ ] [AGENT] P0. Compute and expose `RebalanceCostEstimate` via risk API:
  - Strategy calls `_estimate_rebalance_cost()` and `_estimate_emergency_close_cost()`
  - These are exposed in risk metrics for UI display
  - Include in health API response

- [ ] [AGENT] P0. Run `cd risk-and-exposure-service && bash scripts/quality-gates.sh`

### 2C: Execution-Service Cost Estimation

**Repo**: execution-service

- [x] [AGENT] P0. Add `estimate_instruction_cost()` method to base handler:
  - Implemented as `estimate_cost()` on each handler type in `execution_service/engine/handlers/`
  - `base_handler.py`, `swap_handler.py`, `lend_handler.py`, `stake_handler.py`, `flash_loan_handler.py`,
    `transfer_handler.py`, `trade_handler.py`, `borrow_handler.py`, `futures_handler.py` all have `estimate_cost()`

- [x] [AGENT] P0. Implement for each handler type:
  - All handler types have `async def estimate_cost()` returning gas/fee estimates

- [x] [AGENT] P0. Create `estimate_full_unwind_cost()` that takes a list of positions and returns total cost to close
      everything
  - Implemented in `execution_service/engine/unwind_cost.py`
  - `PositionSummary` + `UnwindCostEstimate` TypedDicts, per-position-type cost model

- [ ] [AGENT] P0. Run `cd execution-service && bash scripts/quality-gates.sh`

## Phase 3: UI + E2E (PARALLEL)

### 3A: UI Enhancements

**Repo**: unified-trading-system-ui

- [x] [AGENT] P1. Display per-client strategy restrictions in strategy config widget:
  - Show which venues are available vs restricted
  - Show which features are enabled vs locked (with upsell hint)
  - "Multi-coin rotation: Locked — Upgrade to Premium" style display

- [x] [AGENT] P1. Add estimated rebalancing cost display:
  - In strategy overview: "Est. rebalance cost: $X (Y% of NAV)"
  - In emergency section: "Est. full close cost: $X (Y% of NAV), ~Z minutes"

- [x] [AGENT] P1. Add enhanced risk display:
  - Oracle depeg indicator (green/yellow/red)
  - Borrow-staking spread with leverage impact
  - Stablecoin peg status
  - Withdrawal delay risk assessment

- [x] [AGENT] P1. Mock data for all new risk types

### 3B: E2E Testing

**Repo**: e2e-testing

- [ ] [AGENT] P1. Add client config scenario:
  - Patrick config: restricted venues, fixed coin, equal weights
  - Verify basis trade only uses OKX/Bybit/Binance
  - Verify single coin (ETH) used, no rotation

- [ ] [AGENT] P1. Add risk monitoring scenarios:
  - Simulate health factor drop → verify 5-min alert
  - Simulate oracle depeg → verify alert
  - Simulate borrow rate spike → verify spread alert
  - Estimate emergency close cost and verify reasonable

## Phase 4: Documentation

- [x] [AGENT] P1. Create `/codex/09-strategy/operational/client-strategy-config.md`:
  - Per-client override schema
  - Venue restriction mechanism
  - Feature gating (basic vs premium)
  - Patrick example

- [x] [AGENT] P1. Create `/codex/04-architecture/defi-risk-monitoring.md`:
  - All DeFi risk types with thresholds
  - Sub-1H health factor monitoring
  - Oracle depeg detection
  - Borrow-staking spread
  - Stablecoin depeg
  - Withdrawal delay risk
  - Rebalance and emergency close cost estimation

## Success Criteria

1. `ClientStrategyOverride` schema in UAC with venue restrictions and feature gating
2. Patrick's config restricts basis trade to OKX/Bybit/Binance, fixes ETH coin, disables rotation
3. Strategy-service applies client overrides to venue filtering and feature availability
4. Health factor monitored at 5-minute intervals for leveraged strategies (not 1H)
5. Oracle depeg, borrow rate spread, and stablecoin depeg monitored with tiered alerts
6. Rebalance and emergency close costs estimated and exposed via API
7. Strategy uses cost estimation in rebalance decisions (don't rebalance if cost > benefit)
8. UI displays restrictions, risk indicators, and cost estimates
9. E2E tests validate client config enforcement and risk alerting
10. All 8 repos pass `quality-gates.sh`
