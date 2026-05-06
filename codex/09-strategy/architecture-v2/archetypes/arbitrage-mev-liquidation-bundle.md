---
scope: [engineer, admin]
topology_requirements:
  isolation:
    execution-service: isolated
  latency_budget_ms: 150
  min_sla_tier: high
---

<!-- POST_PLAN_BANNER_2026_05_06_FINAL -->

> **Post-2026-05-06** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md) before code/doc
> changes informed by this doc. Active plans: writegate-honest-coverage, predictions-canonical_question_group,
> data-status-multi-axis-shard. If this doc disagrees with active plans, the plans win. Flag conflicts to user.

# Archetype: `ARBITRAGE_MEV_LIQUIDATION_BUNDLE`

> **Family:** `ARBITRAGE_STRUCTURAL`. **Settlement model:** ATOMIC bundle — all-or-nothing within a single transaction.
> **Code module:** `strategy-service/strategy_service/engine/strategies/v2/mev/liquidation_bundle.py`.

## What it does

Liquidates under-collateralised lending positions using flash-loan funding inside a single atomic transaction; the
engine never holds the capital required to repay protocol debt. Extends the `LIQUIDATION_CAPTURE` archetype with
zero-capital execution: one wallet plus one deployed `FlashLoanReceiver` contract per chain is enough to run across
protocols.

## Atomic flow (single tx, reverts on any failure)

1. `flashLoan(asset=debt_asset, amount=debt_amount)` — borrow the repay amount.
2. `liquidationCall(borrower, debt_asset, debt_amount)` — protocol pays collateral + bonus.
3. `swap(collateral_asset → debt_asset)` on Uniswap V3 (or Curve / Balancer).
4. `repay(flash_loan + flash_fee)`.
5. Profit = collateral_value - debt_amount - flash_fee - swap_loss - gas_cost.

## Profit estimate (closed-form)

```python
from strategy_service.engine.strategies.v2.mev.liquidation_bundle import (
    estimate_bundle_profit_usd,
)

profit_usd = estimate_bundle_profit_usd(
    debt_amount_usd=Decimal("10000"),
    liq_bonus_pct=Decimal("5"),       # 5% liq bonus
    flash_loan_fee_bps=Decimal("9"),  # Aave V3 flash fee
    gas_cost_usd=Decimal("20"),
    swap_slippage_bps=Decimal("50"),
)
# profit_usd = $418.50
```

The engine emits a bundle only when `profit_usd >= min_net_profit_usd`.

## Required feature keys

Numeric (`features: dict[str, float]`):

- `liq_candidate_debt_amount_<id>`
- `liq_candidate_health_factor_<id>` — must be < 1 to be liquidatable
- `liq_candidate_liq_bonus_pct_<id>`
- `flash_loan_fee_bps_<flash_source>`
- `gas_price_gwei_<chain>`

String metadata (`self.params`):

- `cand_<id>_borrower`
- `cand_<id>_debt_asset`
- `cand_<id>_collateral`
- `cand_<id>_pool` — `AAVE_V3` | `COMPOUND_V3` | `MORPHO_BLUE` | `FLUID` | `EULER_V2` | `RADIANT` | `VENUS` | `BENQI`
- `cand_<id>_chain`

## Wire format

`InstructionActionV2.ATOMIC` with three legs in this order:

```
leg 0: BORROW   asset=debt_asset       venue=AAVE_V3 (flash)
leg 1: TRADE    instrument=COL/DEBT    venue=AAVE_V3 (the lending protocol)
leg 2: SWAP     instrument=COL/DEBT    venue=UNISWAPV3 (repay leg)
```

execution-service `aave_flash_bundle.py` consumes the payload and packs it into a single tx via the deployed
`FlashLoanReceiver` contract (`deployment-service/contracts/FlashLoanReceiver.sol`).

## Risks

- **Bundle revert mid-tx** — if Aave's price-oracle update lands in a later block, the position's HF flips back above 1
  and the `liquidationCall` reverts. Loss is gas only (atomic).
- **Reorg** — unlike sandwich, liquidation bundles are robust to reorg since the same opportunity is re-broadcast next
  block; missed-block risk is gas-only.
- **Flash-loan source pricing** — Aave V3 flash fee is 9 bps, Balancer is 0 bps (free), Maker DAI flash mint is 0 bps
  but DAI-denominated only. Wire each candidate's optimal source via param; `flash_loan_source` is operator-set.

## Plan

`plans/active/defi_pipeline_extension_2026_05_01.plan.md` Phase 5.1.
