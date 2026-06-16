---
scope: [engineer, admin]
---

# Venue Collateral & Token Wrapping -- Cross-Cutting Concern

## Overview

Each venue accepts specific tokens as collateral or margin. DeFi protocols additionally require specific wrapped token
forms (e.g., WETH instead of ETH, weETH instead of eETH). The strategy must ensure tokens are in the correct form before
emitting instructions. This is handled by the `CollateralValidationMixin` which validates and pre-processes tokens
before instruction emission.

## Venue Collateral Matrix

### CeFi Venues (Perp Margin)

| Venue       | Accepted Collateral | Notes                                         |
| ----------- | ------------------- | --------------------------------------------- |
| Hyperliquid | USDC only           | Must swap USDT to USDC before posting margin. |
| Binance     | USDT, BTC, ETH      | USDT is default for linear perps.             |
| OKX         | USDT, BTC, ETH      | USDT is default for linear perps.             |
| Bybit       | USDT, BTC, ETH      | USDT is default for linear perps.             |
| Aster       | USDT, BTC, ETH      | USDT is default for linear perps.             |

### DeFi Venues (Lending Collateral)

| Venue       | Accepted Collateral                   | Notes                               |
| ----------- | ------------------------------------- | ----------------------------------- |
| Aave V3     | WETH, weETH, wstETH, USDC, USDT, WBTC | Must be non-rebasing wrapped forms. |
| Morpho      | WETH, wstETH, USDC                    | Flash loan pool assets.             |
| Compound V3 | WETH, USDC                            | Limited collateral set.             |

## Collateral Haircuts (Aave V3)

Aave V3 applies different loan-to-value ratios per collateral asset. The haircut is `1 - LTV`.

| Collateral | LTV   | Haircut | Liquidation Threshold | Max Leverage |
| ---------- | ----- | ------- | --------------------- | ------------ |
| weETH      | 72.5% | 27.5%   | 75%                   | 3.636x       |
| wstETH     | 79.5% | 20.5%   | 82%                   | 4.88x        |
| WETH       | 82.5% | 17.5%   | 85%                   | 5.71x        |
| USDC       | 86%   | 14%     | 88%                   | 7.14x        |
| USDT       | 75%   | 25%     | 78%                   | 4.00x        |
| WBTC       | 73%   | 27%     | 78%                   | 3.70x        |

These values are from Aave V3 Ethereum mainnet governance parameters. They can change via Aave governance proposals. The
strategy reads current parameters from on-chain via `features-onchain-service` rather than hardcoding.

## Token Wrapping

DeFi protocols require specific wrapped token forms. Rebasing tokens (eETH, stETH) cannot be used as Aave collateral
because their balance changes on every block, which breaks Aave's scaled balance accounting. Wrapping converts them to
non-rebasing equivalents.

| Source Token | Wrapped Token | Wrapping Contract | Why Required                                        |
| ------------ | ------------- | ----------------- | --------------------------------------------------- |
| ETH          | WETH          | WETH9             | Most DeFi protocols require ERC-20 (ETH is native). |
| eETH         | weETH         | EtherFi weETH     | eETH is rebasing. Aave requires non-rebasing.       |
| stETH        | wstETH        | Lido wstETH       | stETH is rebasing. Aave requires non-rebasing.      |

### Wrapping Mechanics

**ETH to WETH:** Deposit ETH to WETH9 contract. 1:1 conversion. Gas: ~45k.

**eETH to weETH:** Wrap via EtherFi's weETH contract. The weETH/eETH rate reflects accumulated staking yield. Gas: ~65k.
The rate is monotonically increasing -- 1 weETH is always worth >= 1 eETH.

**stETH to wstETH:** Wrap via Lido's wstETH contract. The wstETH/stETH rate reflects accumulated staking yield. Gas:
~65k. Same monotonic increase pattern.

Unwrapping follows the reverse path with similar gas costs.

## Instruction Blocking

If a venue does not accept the token the strategy wants to post as collateral, the instruction is **blocked at the
strategy level** -- not failed at execution. The `CollateralValidationMixin` checks venue collateral requirements before
emitting any instruction.

Blocking flow:

1. Strategy generates a `StrategyInstruction` (e.g., TRANSFER USDT to Hyperliquid as margin).
2. `CollateralValidationMixin.validate_collateral()` checks if Hyperliquid accepts USDT.
3. Hyperliquid accepts USDC only. The mixin emits a SWAP (USDT to USDC) instruction BEFORE the TRANSFER.
4. If no swap path exists (e.g., token not tradeable on any allowed venue), the instruction is blocked with a
   `COLLATERAL_BLOCKED` event. The strategy does not proceed with that leg.

This prevents execution-time failures. The strategy adapts at signal time rather than discovering collateral
incompatibility during execution.

## Pre-Processing Pipeline

The `CollateralValidationMixin` runs a pre-processing pipeline on every instruction batch:

```
For each StrategyInstruction:
  1. Check target venue collateral requirements
  2. If token is not accepted:
     a. Check if a wrapping path exists (ETH->WETH, eETH->weETH, stETH->wstETH)
     b. If yes: prepend WRAP instruction
     c. If no wrapping but swap path exists: prepend SWAP instruction
     d. If no path: block instruction, emit COLLATERAL_BLOCKED event
  3. Validate sufficient balance for wrapping/swapping (gas + amount)
  4. Emit pre-processed instruction batch
```

## Implementation

- **UAC registry:** `venue_collateral.py` -- maps venue to accepted collateral tokens
- **UAC registry:** `token_wrapping.py` -- maps source token to wrapped form and wrapping contract
- **Strategy mixin:** `CollateralValidationMixin` in
  `strategy-service/strategy_service/engine/strategies/defi_enhancements.py`
- **Execution pre-processor:** `WrapPreprocessor` in execution-service -- handles WRAP instruction execution (calls
  wrapping contracts on-chain)
- **Venue constants:** `VENUE_COLLATERAL_MATRIX` in
  `unified-api-contracts/unified_api_contracts/registry/venue_constants.py`

## Strategy Applicability

| Strategy               | Collateral Validation | Token Wrapping         | Notes                                     |
| ---------------------- | --------------------- | ---------------------- | ----------------------------------------- |
| Basis Trade            | Yes (CeFi margin)     | No (spot ETH, no DeFi) | USDT->USDC swap for Hyperliquid.          |
| Staked Basis           | Yes (CeFi margin)     | Yes (eETH->weETH)      | Wrapping required for Aave compatibility. |
| Recursive Staked Basis | Yes (CeFi + DeFi)     | Yes (eETH->weETH)      | Both CeFi margin and DeFi collateral.     |
| AAVE Lending           | No (no margin needed) | No (supply USDT/USDC)  | Direct supply, no wrapping needed.        |
| CeFi strategies        | Yes (CeFi margin)     | No                     | Venue-specific margin token requirements. |
