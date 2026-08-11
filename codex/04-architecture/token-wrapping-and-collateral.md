---
doc_type: codex-ssot
title: Token Wrapping and Venue Collateral
summary:
  Wrapped/unwrapped token protocol mapping (Aave/Morpho need WETH/weETH/wstETH) plus the per-venue collateral acceptance
  matrix and haircuts — exposed via the UAC registry (needs_wrapping / venue_accepts_collateral /
  get_collateral_haircut), auto-wrapped in execution-service WrapPreprocessor and enforced by the strategy-service
  CollateralValidationMixin.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [e2e-testing, execution-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: [defi, execution, collateral, token-wrapping, uac, strategy, aave, registry]
related:
  [
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/04-architecture/defi-execution-overview.md,
    /codex/04-architecture/flash-loan-receiver.md,
    /codex/04-architecture/strategy-service-architecture.md,
  ]
created: 2026-04-03
authoritative_for: [token wrapping rules + venue collateral acceptance matrix]
referenced_by:
owner:
last_reviewed: 2026-08-24
code_refs:
---

# Token Wrapping and Venue Collateral

## Overview

DeFi protocols are specific about which token version they accept. Getting this wrong means reverted transactions,
wasted gas, and failed strategies. This document covers:

- The wrapped/unwrapped token protocol mapping (which protocols require which token form)
- The venue collateral acceptance matrix (what can be posted as margin at each venue)
- Auto-wrapping behaviour in execution-service
- Collateral validation in strategy-service
- How to extend the registries

---

## Token Wrapping Reality

| Protocol / Use Case | Input Token                         | Required Token | Notes                                     |
| ------------------- | ----------------------------------- | -------------- | ----------------------------------------- |
| Aave V3 supply      | ETH                                 | WETH           | Must wrap; Gateway contract can auto-wrap |
| Aave V3 supply      | eETH                                | weETH          | Rebasing not supported; wrap required     |
| Aave V3 supply      | stETH                               | wstETH         | Rebasing not supported; wrap required     |
| Aave V3 supply      | WETH / weETH / wstETH / USDC / USDT | (same)         | Already correct ERC-20 form               |
| Morpho Blue         | ETH                                 | WETH           | Same as Aave — ERC-20 only                |
| EtherFi stake       | ETH or WETH                         | eETH           | Auto-handles both input forms             |
| EtherFi wrap        | eETH                                | weETH          | Explicit `weETH.wrap(eETH_amount)` call   |
| Lido stake          | ETH                                 | stETH          | ETH only; stETH returned directly         |
| Lido wrap           | stETH                               | wstETH         | Explicit `wstETH.wrap(stETH_amount)` call |
| WETH contract       | ETH                                 | WETH           | `WETH.deposit{value: amount}()`           |
| WETH contract       | WETH                                | ETH (exit)     | `WETH.withdraw(amount)`                   |
| Uniswap V3          | ETH                                 | WETH           | Router uses WETH internally               |
| Flash loan (Aave)   | —                                   | WETH           | Borrowed and repaid as WETH               |

---

## Venue Collateral Acceptance Matrix

| Venue                | Accepted Collateral | Haircut | Notes                        |
| -------------------- | ------------------- | ------- | ---------------------------- |
| **AAVE_V3-ETHEREUM** | WETH                | 17.5%   | LTV 82.5%                    |
|                      | weETH               | 27.5%   | LTV 72.5%                    |
|                      | wstETH              | 20.5%   | LTV 79.5%                    |
|                      | USDC / USDT         | 23%     | LTV 77%                      |
|                      | WBTC                | 27%     | LTV 73%                      |
| **HYPERLIQUID**      | USDC only           | 0%      | All perp margin must be USDC |
|                      | ETH / WETH / weETH  | —       | NOT accepted                 |
| **ASTER**            | USDC                | 0%      | Primary margin               |
|                      | USDT                | 1%      | Slight haircut               |
| **BINANCE**          | USDT                | 0%      | Linear futures               |
|                      | BTC / ETH           | 5%      | Coin-margined inverse        |
| **OKX**              | USDT                | 0%      | Linear                       |
|                      | BTC / ETH           | 5%      | Coin-margined                |
| **BYBIT**            | USDT                | 0%      | Linear                       |
|                      | BTC                 | 5%      | Coin-margined                |
| **DERIBIT**          | BTC / ETH           | 0%      | Portfolio margin             |
|                      | USDC                | 2%      | Slight haircut               |

Haircut = `1 - max_ltv`. Max leverage for a recursive Aave position is `1 / (1 - max_ltv)`.

**SSOT for Aave haircuts**: `unified_api_contracts/registry/defi_reserve_params.py` (per-asset LTV, liquidation
threshold, liquidation bonus). The `VENUE_COLLATERAL_MATRIX` entries for Aave reference these values — they are not
duplicated.

---

## UAC Registry Functions

All collateral and wrapping logic is exposed from the UAC registry facade:

```python
from unified_api_contracts.registry import (
    needs_wrapping,
    venue_accepts_collateral,
    get_collateral_haircut,
    get_accepted_collateral,
    get_protocol_token,
)
```

### `needs_wrapping(token, protocol) -> tuple[bool, str | None]`

Returns `(True, "WETH")` if wrapping is needed, `(False, None)` otherwise.

```python
needs_wrapping("ETH", "AAVE_V3")     # -> (True, "WETH")
needs_wrapping("eETH", "AAVE_V3")    # -> (True, "weETH")
needs_wrapping("WETH", "AAVE_V3")    # -> (False, None)
needs_wrapping("USDC", "HYPERLIQUID")  # -> (False, None)
```

### `venue_accepts_collateral(venue, token) -> bool`

```python
venue_accepts_collateral("HYPERLIQUID", "USDC")    # -> True
venue_accepts_collateral("HYPERLIQUID", "weETH")   # -> False
venue_accepts_collateral("AAVE_V3-ETHEREUM", "weETH")  # -> True
```

### `get_collateral_haircut(venue, token) -> Decimal | None`

Returns `None` if the venue does not accept the token.

```python
get_collateral_haircut("AAVE_V3-ETHEREUM", "weETH")   # -> Decimal("0.275")
get_collateral_haircut("HYPERLIQUID", "weETH")        # -> None
```

---

## Auto-Wrapping in execution-service

`execution_service/engine/preprocessors/wrap_preprocessor.py` implements `WrapPreprocessor`.

It inspects each `ExecutionInstruction` and inserts wrap/unwrap steps when needed:

**Entry flows (wrap before protocol interaction):**

```
ETH  + AAVE_V3 instruction  → [WRAP ETH->WETH, LEND WETH@AAVE_V3]
eETH + AAVE_V3 instruction  → [WRAP eETH->weETH, LEND weETH@AAVE_V3]
WETH + AAVE_V3 instruction  → [LEND WETH@AAVE_V3]  (no wrap needed)
```

**Exit flows (unwrap after withdrawal):**

```
WITHDRAW weETH from AAVE_V3  → [WITHDRAW weETH, UNWRAP weETH->eETH]
WITHDRAW WETH from AAVE_V3   → [WITHDRAW WETH, UNWRAP WETH->ETH]
```

The preprocessor is applied in the execution pipeline before any connector is invoked. Unsupported collateral tokens
raise `ValueError` with a clear error message — they are never silently dropped.

### Wrap venues

| Wrap type       | Venue used         | Connector          |
| --------------- | ------------------ | ------------------ |
| ETH_TO_WETH     | `WETH`             | `WethConnector`    |
| EETH_TO_WEETH   | `ETHERFI-ETHEREUM` | `EtherFiConnector` |
| WETH_TO_ETH     | `WETH`             | `WethConnector`    |
| WEETH_TO_EETH   | `ETHERFI-ETHEREUM` | `EtherFiConnector` |
| WSTETH_TO_STETH | `LIDO-ETHEREUM`    | `LidoConnector`    |

---

## Collateral Validation in strategy-service

`strategy_service/engine/strategies/defi_enhancements.py` provides `CollateralValidationMixin`.

DeFi strategies inherit from this mixin and call `_validate_instructions(instructions)` before emitting final
instructions.

**Behaviour:**

1. **Auto-wrap**: if `token_in` needs wrapping for `to_venue`, the instruction is updated to use the wrapped form. The
   original token is recorded in `metadata["auto_wrapped_from"]`.
2. **Collateral block**: if `to_venue` does not accept the (possibly auto-wrapped) token, the instruction is removed
   (returns `None` from `_validate_collateral`). A `logger.warning` is emitted.

```python
# Example: strategy emits ETH -> AAVE_V3
# After _validate_instructions: token is auto-corrected to WETH

instructions = self._validate_instructions([
    StrategyInstruction(token_in="ETH", to_venue="AAVE_V3-ETHEREUM", ...)
])
# instructions[0].token_in == "WETH"
# instructions[0].metadata["auto_wrapped_from"] == "ETH"

# Example: strategy tries to deposit weETH at HyperLiquid
instructions = self._validate_instructions([
    StrategyInstruction(token_in="weETH", to_venue="HYPERLIQUID", ...)
])
# instructions == []  (blocked, warning logged)
```

### Haircut-aware leverage: `max_leverage_for_token`

```python
from strategy_service.engine.strategies.defi_enhancements import max_leverage_for_token

max_leverage_for_token("weETH")   # -> Decimal("3.64")  (LTV 72.5%)
max_leverage_for_token("WETH")    # -> Decimal("5.71")  (LTV 82.5%)
```

Used in recursive staking strategies to cap the loop iteration count.

---

## Strategy-Specific Collateral Rules

### Staked Basis (`CARRY_STAKED_BASIS`) — two collateral-posting modes

The staked-basis engine (`strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py`) derives the
collateral-posting structure at preflight from the UAC `VENUE_COLLATERAL_MATRIX` via `_derive_structure()`. Two modes,
each with different margin requirements and sizing rules:

#### `LST_AS_MARGIN` (capital-efficient, default when venue accepts the LST)

The perp venue accepts the LST itself as cross-margin (e.g. BYBIT accepts stETH/wstETH, DERIBIT accepts stETH).
`stake_fraction == 1.0` — the staked LST IS the margin, so no spare cash buffer is needed. This is the original
single-collateral-pool path.

#### `USDC_MARGIN_BUFFERED` (collateral down-size, shipped 2026-06-17 Phase A)

When the perp venue does NOT accept the LST but DOES accept a stablecoin (USDC/USDT), the slot is still doable —
**deposit the stable as perp margin and size the staked leg DOWN** by a margin-call buffer so the hedge can't be
liquidated on an adverse move.

| Component           | Value                                         | SSOT                                                                    |
| ------------------- | --------------------------------------------- | ----------------------------------------------------------------------- |
| Buffer default      | `0.20` (20%)                                  | `staked_basis.py:238` `_DEFAULT_MARGIN_BUFFER_PCT`                      |
| Stake fraction      | `f = 1 - margin_buffer_pct`                   | `staked_basis.py:407` engine-derived                                    |
| Stable preference   | USDC, then USDT                               | `staked_basis.py:243` `_PERP_MARGIN_STABLE_PREFERENCE`                  |
| Margin token        | venue's first accepted stable                 | `staked_basis.py:367-370` `_derive_structure()`                         |
| Perp haircut source | STABLE collateral row in UAC matrix           | `staked_basis.py:369` `get_collateral_haircut()`                        |
| Per-venue override  | `margin_buffer_pct` engine param              | `staked_basis.py:391` `decimal_param(params, "margin_buffer_pct", ...)` |
| Param schema        | `PARAM_SCHEMA_REGISTRY["CARRY_STAKED_BASIS"]` | `param_schema.py:144-152`                                               |

Funds sit in TWO places (stable at the perp venue + LST on-chain), so the slot carries a **cross-exchange / dual-deposit
capital cost** that `CarryStakedBasisRankAllocator` penalises at `archetypes_rank.py`
`_DUAL_DEPOSIT_CROSS_EXCHANGE_COST_BPS = 150` (confirmed-standing value, operator ruling 2026-08-08).

**Venues exercising this path**: Aster (USDC/USDT), Hyperliquid (USDC-only) — both USDC-only perp venues where the LST
cannot be posted as margin.

**Test coverage**: `tests/unit/engine/strategies/v2/test_carry_staked_basis_usdc_margin_buffered.py` +
`tests/unit/portfolio_allocator/test_staked_basis_collateral_penalty.py`.

**Plan**: `plans/active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md` Phase A.

#### Rejection (venue accepts neither LST nor stable)

If the perp venue accepts neither the LST nor a stablecoin, `_derive_structure()` returns `None` — the slot is rejected
at preflight. No silent placeholder; no SPLIT_STAKE fallback (deleted 2026-05-05 — no `f < 1` regime dominates the
alternatives; see `staked_basis.py:205-222` for the proof).

---

### Legacy Staked Basis (`STAKED_BASIS` — pre-v2)

The pre-v2 strategy had two separate collateral pools that must not be mixed:

| Pool        | Token | Venue            | Purpose               |
| ----------- | ----- | ---------------- | --------------------- |
| A (lending) | weETH | AAVE_V3-ETHEREUM | Yield from staked ETH |
| B (margin)  | USDC  | HYPERLIQUID      | Short ETH perp margin |

The `CollateralValidationMixin` enforces this: any instruction with `weETH` directed at `HYPERLIQUID` is blocked. The
strategy must hold separate USDC for perp margin.

### Recursive Staked Basis (`RECURSIVE_STAKED_BASIS`)

Aave supply uses **weETH** (not eETH). The `needs_wrapping` check in strategy validation ensures eETH is auto-corrected
to weETH before the instruction reaches execution-service.

Loop leverage is capped using `max_leverage_for_token("weETH")` ≈ 3.64x.

### AAVE Lending (`AAVE_LENDING`)

Aave supply uses **WETH** (not native ETH). Auto-wrap is applied if strategy emits `ETH`.

### Basis Trade (`BASIS_TRADE`)

Perp margin must match the venue requirement:

- HyperLiquid → USDC
- Binance linear → USDT
- Binance inverse → BTC or ETH

---

## Extending the Registries

### Add a new token wrapping rule

Edit `unified_api_contracts/registry/token_wrapping.py`:

```python
TOKEN_WRAPPING_RULES.append(
    TokenWrappingRule(
        unwrapped="cbETH",
        wrapped="wcbETH",
        wrapper_contract="0x...",
        chain="ETHEREUM",
        is_rebasing=False,
        auto_wrap_supported=False,
        balance_tracking_form="wrapped",
    )
)
```

Then update `PROTOCOL_TOKEN_PREFERENCE` for any protocol that requires the wrapped form.

### Add a new venue collateral entry

Edit `unified_api_contracts/registry/venue_collateral.py`:

```python
VENUE_COLLATERAL_MATRIX.append(
    CollateralAcceptance(
        venue="NEW_VENUE",
        token="USDC",
        accepted=True,
        haircut_pct=Decimal("0"),
        margin_type="CROSS",
        notes="Primary margin for NEW_VENUE",
    )
)
```

Run `cd unified-api-contracts && bash scripts/quality-gates.sh` after any change.

---

## E2E Validation

Scenarios are in `e2e-testing/scripts/defi/test_collateral_validation.py`:

```bash
# From workspace root
python e2e-testing/scripts/defi/test_collateral_validation.py
```

Covers: wrapping lookups, collateral matrix, haircuts, WrapPreprocessor entry/exit flows, strategy blocking, and the
full staked basis dual-collateral flow.
