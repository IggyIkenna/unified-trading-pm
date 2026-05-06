---
scope: [engineer, admin]
topology_requirements:
  isolation:
    execution-service: shared
  latency_budget_ms: 1000
  min_sla_tier: standard
---

<!-- POST_PLAN_BANNER_2026_05_06_FINAL -->

> **Post-2026-05-06** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md) before code/doc
> changes informed by this doc. Active plans: writegate-honest-coverage, predictions-canonical_question_group,
> data-status-multi-axis-shard. If this doc disagrees with active plans, the plans win. Flag conflicts to user.

# Archetype: `DEFI_LP_VAULT`

> **Family:** `MARKET_MAKING`. **Settlement model:** ERC-4626 deposit / redeem. **Code module:**
> `strategy-service/strategy_service/engine/strategies/v2/defi_lp/vault.py`.

## What it does

Deposits into an ERC-4626 vault (Yearn V3, Morpho MetaMorpho, Aave Vaults, Sommelier, etc.) and holds while realised APY
stays above `min_apy_bps`. Exits on APY-below-floor OR drawdown breach.

Share price `pps = totalAssets / totalSupply` accretes over time net of the vault's perf + management fees. The
features-onchain `vault_share_price_apy` calculator emits annualised share-price drift as
`vault_share_price_apy_bps_<vault>`, which is the engine's primary input.

## State machine

```
NEUTRAL --apy >= min_apy--> DEPOSITED --apy < min_apy OR drawdown >= max-->  WITHDRAWN
```

## Required params

- `vault_address` — ERC-4626 contract
- `venue` — `YEARN_V3` | `MORPHO` | `AAVE_VAULT` | `SOMMELIER` | ...
- `stake_fraction` — equity fraction (default `1.0`)
- `min_apy_bps` — exit floor (default `100` = 1%)
- `max_drawdown_bps` — exit ceiling on drawdown (default `500` = 5%)

## Required feature keys

- `vault_share_price_<vault_address>`
- `vault_share_price_apy_bps_<vault_address>`
- `vault_drawdown_bps_<vault_address>`

## Risks

- **Strategy concentration** — many ERC-4626 vaults are thin wrappers over a single underlying yield strategy.
  Diversification from the vault itself is illusory; treat each vault as a single-strategy bet.
- **Withdraw queues** — some vaults gate withdrawals behind an epoch queue; emergency exit may take days. Verify via the
  vault's `previewRedeem` ABI before deploying real capital.
- **Perf fee step-changes** — operators of the underlying vault can raise the perf fee mid-deposit. APY drops without an
  underlying yield change; engine exits on the new realised APY.

## Plan

`plans/active/defi_pipeline_extension_2026_05_01.plan.md` Phase 4.3.
