---
doc_type: plan
title: token-wrapping-venue-collateral
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [e2e-testing, execution-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-03"
overview: Wrapped/unwrapped token protocol mapping, venue collateral acceptance matrix, collateral haircuts in UAC
type: code
epic: epic-code-completion
locked_by: live-defi-rollout
locked_since: 2026-04-01
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - { repo: unified-api-contracts, code: C0, deployment: none, business: none }
  - { repo: execution-service, code: C0, deployment: none, business: none }
  - { repo: strategy-service, code: C0, deployment: none, business: none }
  - { repo: instruments-service, code: C0, deployment: none, business: none }
  - { repo: e2e-testing, code: C0, deployment: none, business: none }
depends_on: []
todos:
  - { id: tw-1a-token-map, content: "- [x] [AGENT] P0. Create wrapped/unwrapped token mapping registry in UAC

        ", status: done, note: "" }
  - { id: tw-1b-collateral-matrix, content: "- [x] [AGENT] P0. Create venue collateral acceptance matrix in UAC

        ", status: done, note: "" }
  - { id: tw-1c-haircuts, content: "- [x] [AGENT] P0. Formalise collateral haircuts from defi_reserve_params into
        venue-level registry

        ", status: done, note: defi_reserve_params.py already has Aave LTV/liquidation data }
  - { id: tw-2a-strategy-validation, content: "- [x] [AGENT] P0. Add collateral acceptance validation to strategy
        instruction generation

        ", status: done, note: "" }
  - { id: tw-2b-execution-wrapping, content: "- [x] [AGENT] P0. Add auto-wrap/unwrap logic to execution-service handlers

        ", status: done, note: "" }
  - { id: tw-3a-e2e, content: "- [x] [AGENT] P1. Add collateral validation scenarios to e2e-testing

        ", status: done, note: "e2e-testing/scripts/defi/test_collateral_validation.py — 9 scenarios covering wrapping
        lookups, collateral matrix, haircuts, WrapPreprocessor auto-wrap, strategy blocking, and staked basis
        dual-collateral flow" }
  - { id: tw-4a-docs, content: "- [x] [AGENT] P1. Document token wrapping + collateral in codex

        ", status: done, note: unified-trading-pm/codex/04-architecture/token-wrapping-and-collateral.md }
isProject: false
---

# Token Wrapping, Venue Collateral & Protocol Alignment

## Context

DeFi protocols are specific about which token version they accept. Getting this wrong means reverted transactions,
wasted gas, and failed strategies. Key examples:

- **Aave V3**: Works in **WETH** (not native ETH) because they need ERC-20 for accounting. Also accepts **weETH** and
  **wstETH** as collateral but at different LTV haircuts.
- **EtherFi**: Accepts **ETH** or **WETH** for staking, returns **eETH** (rebasing) or **weETH** (non-rebasing wrapped).
- **Lido**: Accepts **ETH**, returns **stETH** (rebasing). **wstETH** is the wrapped non-rebasing version.
- **Uniswap V3**: Usually works with **wrapped** tokens (WETH, not ETH). Some pools support native ETH via multicall.
- **HyperLiquid**: Accepts **USDC** as margin. Does NOT accept eETH, weETH, stETH as collateral for perps.
- **Binance/OKX/Bybit**: Accept coin-margined (BTC, ETH) or USDT-margined perps. Collateral is exchange-specific.
- **Deribit**: BTC and ETH as margin. Also USDC for some products.

If a strategy expects to deposit eETH at HyperLiquid for a short perp position, it must be **blocked** — HyperLiquid
doesn't accept it. The strategy must instead hold separate USDC margin.

Collateral haircuts affect leverage calculations — weETH has max_ltv=0.725 on Aave, meaning only 72.5% of its value
counts as borrowing power. These values already exist in `defi_reserve_params.py` for Aave but aren't formalised across
venues.

## Pre-Audit: Token Wrapping Reality

| Protocol            | Input Token   | Output Token     | Wrapping Required?             | Notes                             |
| ------------------- | ------------- | ---------------- | ------------------------------ | --------------------------------- |
| Aave V3 supply      | WETH          | aWETH            | Yes — must wrap ETH→WETH first | Gateway contract can auto-wrap    |
| Aave V3 supply      | weETH         | aweETH           | No — already ERC-20            | Direct supply                     |
| Aave V3 supply      | wstETH        | awstETH          | No — already ERC-20            | Direct supply                     |
| Aave V3 supply      | USDT/USDC/DAI | aUSDT/aUSDC/aDAI | No — already ERC-20            | Direct supply                     |
| Aave V3 borrow      | WETH          | WETH (debt)      | N/A                            | Borrowed as WETH                  |
| EtherFi stake       | ETH or WETH   | eETH             | Auto-handles both              | weETH requires extra wrap of eETH |
| EtherFi wrap        | eETH          | weETH            | Yes — explicit wrap call       | `weETH.wrap(eETH_amount)`         |
| Lido stake          | ETH           | stETH            | N/A                            | Direct staking, ETH only          |
| Lido wrap           | stETH         | wstETH           | Yes — explicit wrap            | `wstETH.wrap(stETH_amount)`       |
| WETH contract       | ETH           | WETH             | Yes — explicit deposit         | `WETH.deposit{value: amount}()`   |
| WETH contract       | WETH          | ETH              | Yes — explicit withdraw        | `WETH.withdraw(amount)`           |
| Uniswap V3          | WETH ↔ token  | token ↔ WETH     | Must be wrapped                | Router uses WETH internally       |
| Morpho supply       | WETH, weETH   | share tokens     | Same as Aave                   | Market-specific                   |
| Flash loan (Aave)   | WETH          | WETH             | Must repay in WETH             | Flash borrowed as WETH            |
| Flash loan (Morpho) | WETH          | WETH             | Must repay in WETH             | Flash borrowed as WETH            |

## Pre-Audit: Venue Collateral Acceptance

| Venue               | Accepted Margin/Collateral                                                            | NOT Accepted                       | Notes                      |
| ------------------- | ------------------------------------------------------------------------------------- | ---------------------------------- | -------------------------- |
| **Aave V3**         | WETH, USDT, USDC, DAI, WBTC, weETH (0.725 LTV), wstETH (0.795 LTV), cbETH (0.745 LTV) | Native ETH, eETH, stETH (rebasing) | Use wrapped versions       |
| **Morpho Blue**     | Market-specific (WETH, USDC, wstETH, weETH common)                                    | Varies by market                   | Check individual markets   |
| **HyperLiquid**     | USDC only                                                                             | ETH, WETH, weETH, stETH, BTC, USDT | All margin must be USDC    |
| **Aster**           | USDC (primary), USDT                                                                  | Same as HyperLiquid                |                            |
| **Binance Futures** | USDT (linear), BTC/ETH (coin-margined)                                                | LSTs, DeFi tokens                  | Separate linear vs inverse |
| **OKX**             | USDT (linear), BTC/ETH (coin-margined)                                                | LSTs, DeFi tokens                  |                            |
| **Bybit**           | USDT (linear), BTC/ETH (coin-margined)                                                | LSTs, DeFi tokens                  |                            |
| **Deribit**         | BTC, ETH, USDC                                                                        | USDT, LSTs                         | Portfolio margin available |

## Execution DAG

```
Phase 1 (UAC Registries — SEQUENTIAL)
  ├── 1A: Token wrapping registry
  ├── 1B: Venue collateral acceptance matrix
  └── 1C: Collateral haircut formalisation
        │
        ▼  QG gate: UAC passes
Phase 2 (Strategy + Execution — PARALLEL)
  ├── 2A: Strategy collateral validation
  └── 2B: Execution auto-wrap/unwrap
        │
        ▼  QG gate: strategy-service + execution-service pass
Phase 3 (E2E + Docs)
  ├── 3A: E2E collateral validation scenarios
  └── 3B: Codex documentation
```

## Phase 1: UAC Registries (SEQUENTIAL)

### 1A: Token Wrapping Registry

**Repo**: unified-api-contracts

- [ ] [AGENT] P0. Create `registry/token_wrapping.py`:

  ```python
  from dataclasses import dataclass

  @dataclass(frozen=True)
  class TokenWrappingRule:
      """Defines wrapping relationship between tokens."""
      unwrapped: str          # "ETH", "eETH", "stETH"
      wrapped: str            # "WETH", "weETH", "wstETH"
      wrapper_contract: str   # Contract address that performs wrapping
      chain: str              # "ETHEREUM"
      is_rebasing: bool       # True for stETH, eETH; False for WETH, weETH, wstETH
      auto_wrap_supported: bool  # Some protocols auto-wrap for you

  TOKEN_WRAPPING_RULES: list[TokenWrappingRule] = [
      TokenWrappingRule(
          unwrapped="ETH", wrapped="WETH",
          wrapper_contract="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
          chain="ETHEREUM", is_rebasing=False, auto_wrap_supported=True,
      ),
      TokenWrappingRule(
          unwrapped="eETH", wrapped="weETH",
          wrapper_contract="0xCd5fE23C85820F7B72D0926FC9b05b43E359b7ee",
          chain="ETHEREUM", is_rebasing=True, auto_wrap_supported=False,
      ),
      TokenWrappingRule(
          unwrapped="stETH", wrapped="wstETH",
          wrapper_contract="0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0",
          chain="ETHEREUM", is_rebasing=True, auto_wrap_supported=False,
      ),
  ]

  def get_protocol_token(token: str, protocol: str) -> str:
      """Return the token version a protocol actually accepts.

      E.g., get_protocol_token("ETH", "AAVE_V3") → "WETH"
            get_protocol_token("eETH", "AAVE_V3") → "weETH"
            get_protocol_token("ETH", "ETHERFI") → "ETH" (accepts native)
      """

  def needs_wrapping(token: str, target_protocol: str) -> tuple[bool, str | None]:
      """Check if token needs wrapping for target protocol.

      Returns (needs_wrap, wrapped_token_name).
      E.g., needs_wrapping("ETH", "AAVE_V3") → (True, "WETH")
            needs_wrapping("WETH", "AAVE_V3") → (False, None)
      """
  ```

- [ ] [AGENT] P0. Create protocol token acceptance map (which protocol accepts which version):
  ```python
  # Which token version each protocol/venue prefers
  PROTOCOL_TOKEN_PREFERENCE: dict[str, dict[str, str]] = {
      "AAVE_V3": {
          "ETH": "WETH",       # Must wrap
          "eETH": "weETH",     # Must wrap (rebasing not supported)
          "stETH": "wstETH",   # Must wrap
          "WETH": "WETH",      # Already correct
          "weETH": "weETH",    # Already correct
          "wstETH": "wstETH",  # Already correct
          "USDT": "USDT",
          "USDC": "USDC",
          "DAI": "DAI",
          "WBTC": "WBTC",
      },
      "MORPHO": {
          # Same as AAVE_V3 — wrapped tokens only
          "ETH": "WETH", "eETH": "weETH", "stETH": "wstETH",
      },
      "ETHERFI": {
          "ETH": "ETH",        # Accepts native ETH
          "WETH": "WETH",      # Also accepts WETH (auto-unwraps)
      },
      "LIDO": {
          "ETH": "ETH",        # Accepts native ETH only
      },
      "UNISWAP_V3": {
          "ETH": "WETH",       # Router uses WETH internally
      },
      "HYPERLIQUID": {
          "USDC": "USDC",      # Only USDC margin
      },
      "BINANCE_LINEAR": {
          "USDT": "USDT",      # USDT-margined
      },
      "BINANCE_INVERSE": {
          "BTC": "BTC",        # Coin-margined
          "ETH": "ETH",
      },
  }
  ```

### 1B: Venue Collateral Acceptance Matrix

**Repo**: unified-api-contracts

- [ ] [AGENT] P0. Create `registry/venue_collateral.py`:

  ```python
  from dataclasses import dataclass
  from decimal import Decimal

  @dataclass(frozen=True)
  class CollateralAcceptance:
      venue: str              # "HYPERLIQUID", "BINANCE", "AAVE_V3-ETHEREUM"
      token: str              # "USDC", "weETH", "WETH"
      accepted: bool          # Whether venue accepts this as collateral
      haircut_pct: Decimal | None  # E.g., 0.275 means 72.5% LTV (27.5% haircut)
      margin_type: str        # "CROSS", "ISOLATED", "PORTFOLIO"
      notes: str              # Any special conditions

  VENUE_COLLATERAL_MATRIX: list[CollateralAcceptance] = [
      # HyperLiquid — USDC only
      CollateralAcceptance("HYPERLIQUID", "USDC", True, Decimal("0"), "CROSS", "Only accepted margin"),
      CollateralAcceptance("HYPERLIQUID", "ETH", False, None, "", "Not accepted"),
      CollateralAcceptance("HYPERLIQUID", "weETH", False, None, "", "Not accepted — strategy must hold separate USDC"),
      CollateralAcceptance("HYPERLIQUID", "WETH", False, None, "", "Not accepted"),

      # Aster — USDC/USDT
      CollateralAcceptance("ASTER", "USDC", True, Decimal("0"), "CROSS", "Primary margin"),
      CollateralAcceptance("ASTER", "USDT", True, Decimal("0.01"), "CROSS", "Slight haircut"),

      # Aave V3 — from defi_reserve_params.py (import existing data)
      CollateralAcceptance("AAVE_V3-ETHEREUM", "WETH", True, Decimal("0.175"), "ISOLATED", "LTV 82.5%"),
      CollateralAcceptance("AAVE_V3-ETHEREUM", "weETH", True, Decimal("0.275"), "ISOLATED", "LTV 72.5%"),
      CollateralAcceptance("AAVE_V3-ETHEREUM", "wstETH", True, Decimal("0.205"), "ISOLATED", "LTV 79.5%"),
      CollateralAcceptance("AAVE_V3-ETHEREUM", "USDT", True, Decimal("0.23"), "ISOLATED", "LTV 77%"),
      CollateralAcceptance("AAVE_V3-ETHEREUM", "USDC", True, Decimal("0.23"), "ISOLATED", "LTV 77%"),
      CollateralAcceptance("AAVE_V3-ETHEREUM", "WBTC", True, Decimal("0.27"), "ISOLATED", "LTV 73%"),

      # Binance Futures (linear = USDT margin)
      CollateralAcceptance("BINANCE", "USDT", True, Decimal("0"), "CROSS", "Linear futures"),
      CollateralAcceptance("BINANCE", "BTC", True, Decimal("0.05"), "CROSS", "Coin-margined inverse"),
      CollateralAcceptance("BINANCE", "ETH", True, Decimal("0.05"), "CROSS", "Coin-margined inverse"),

      # OKX
      CollateralAcceptance("OKX", "USDT", True, Decimal("0"), "CROSS", "Linear"),
      CollateralAcceptance("OKX", "BTC", True, Decimal("0.05"), "CROSS", "Coin-margined"),
      CollateralAcceptance("OKX", "ETH", True, Decimal("0.05"), "CROSS", "Coin-margined"),

      # Bybit
      CollateralAcceptance("BYBIT", "USDT", True, Decimal("0"), "CROSS", "Linear"),
      CollateralAcceptance("BYBIT", "BTC", True, Decimal("0.05"), "CROSS", "Coin-margined"),

      # Deribit
      CollateralAcceptance("DERIBIT", "BTC", True, Decimal("0"), "PORTFOLIO", "Portfolio margin"),
      CollateralAcceptance("DERIBIT", "ETH", True, Decimal("0"), "PORTFOLIO", "Portfolio margin"),
      CollateralAcceptance("DERIBIT", "USDC", True, Decimal("0.02"), "PORTFOLIO", "Slight haircut"),
  ]

  def venue_accepts_collateral(venue: str, token: str) -> bool:
      """Check if a venue accepts a given token as collateral."""

  def get_collateral_haircut(venue: str, token: str) -> Decimal | None:
      """Get haircut for a token at a venue. None if not accepted."""

  def get_accepted_collateral(venue: str) -> list[str]:
      """Get list of tokens accepted as collateral at a venue."""
  ```

### 1C: Integrate with Existing defi_reserve_params

**Repo**: unified-api-contracts

- [ ] [AGENT] P0. Ensure `defi_reserve_params.py` data (which already has per-asset max_ltv, liquidation_threshold,
      liquidation_bonus for Aave) is the SSOT for DeFi protocol haircuts
- [ ] [AGENT] P0. `VENUE_COLLATERAL_MATRIX` for Aave entries should reference `defi_reserve_params` rather than
      duplicate values
- [ ] [AGENT] P0. Export convenience functions from UAC root: `venue_accepts_collateral()`, `get_collateral_haircut()`,
      `needs_wrapping()`
- [ ] [AGENT] P0. Run `cd unified-api-contracts && bash scripts/quality-gates.sh`

## Phase 2: Strategy + Execution (PARALLEL)

### 2A: Strategy Collateral Validation

**Repo**: strategy-service

- [ ] [AGENT] P0. Add collateral validation to `DeFiBaseStrategy._validate_instruction()`:

  ```python
  def _validate_collateral(self, instruction: StrategyInstruction) -> bool:
      """Block instructions that try to use unsupported collateral at a venue.

      Example: strategy wants to short ETH on HyperLiquid using weETH as margin.
      HyperLiquid only accepts USDC → instruction BLOCKED.
      Strategy must instead emit TRANSFER USDC to HyperLiquid + SHORT instruction.
      """
      from unified_api_contracts import venue_accepts_collateral
      # Check if the collateral token is accepted at the target venue
      # If not, either auto-fix (swap to accepted token) or raise validation error
  ```

- [ ] [AGENT] P0. Add token wrapping validation to instruction generation:

  ```python
  def _ensure_correct_token_version(self, instruction: StrategyInstruction) -> StrategyInstruction:
      """Ensure instruction uses the token version the protocol actually accepts.

      Example: instruction says LEND ETH to AAVE_V3 → auto-correct to LEND WETH.
      If wrapping is needed, prepend a WRAP instruction before the main instruction.
      """
      from unified_api_contracts import needs_wrapping, get_protocol_token
  ```

- [ ] [AGENT] P0. Specifically validate these strategy flows:
  - Staked basis: strategy should NOT try to deposit weETH at HyperLiquid. Must hold separate USDC margin.
  - Recursive basis: Aave supply should use weETH (wrapped), not eETH (rebasing)
  - Lending: Aave supply should use WETH (not native ETH)
  - Basis trade: perp margin matches venue requirement (USDC for HyperLiquid, USDT for Binance linear)

- [ ] [AGENT] P0. Add haircut-aware leverage calculations:

  ```python
  def _compute_max_leverage(self, collateral_token: str, venue: str) -> Decimal:
      """Compute max leverage accounting for collateral haircut.

      weETH on Aave: LTV 0.725 → max leverage = 1 / (1 - 0.725) = 3.64x
      WETH on Aave: LTV 0.825 → max leverage = 1 / (1 - 0.825) = 5.71x
      """
      from unified_api_contracts import get_collateral_haircut
  ```

- [ ] [AGENT] P0. Run `cd strategy-service && bash scripts/quality-gates.sh`

### 2B: Execution Auto-Wrap/Unwrap

**Repo**: execution-service

- [ ] [AGENT] P0. Add wrapping pre-processor to handler pipeline:

  ```python
  class WrapPreprocessor:
      """Inspects instruction token vs protocol expectation, inserts wrap/unwrap steps.

      If instruction says LEND ETH to AAVE_V3:
        1. Insert WRAP instruction (ETH → WETH via WETH contract)
        2. Modify LEND to use WETH

      If instruction says SUPPLY eETH to AAVE_V3:
        1. Insert WRAP instruction (eETH → weETH via weETH contract)
        2. Modify SUPPLY to use weETH
      """
  ```

- [ ] [AGENT] P0. Ensure WETH connector (`weth.py`) handles ETH↔WETH wrapping reliably

- [ ] [AGENT] P0. Ensure EtherFi connector handles eETH→weETH wrapping (already has `wrap()` method — verify it's
      integrated into instruction flow)

- [ ] [AGENT] P0. Ensure Lido connector handles stETH→wstETH wrapping

- [ ] [AGENT] P0. Add validation: if execution receives instruction with unsupported collateral at venue, reject with
      clear error (don't silently fail)

- [ ] [AGENT] P0. Run `cd execution-service && bash scripts/quality-gates.sh`

## Phase 3: E2E + Docs

### 3A: E2E Collateral Validation

**Repo**: e2e-testing

- [ ] [AGENT] P1. Add test scenario: staked basis trade with correct collateral flow:
  1. Stake ETH → get weETH (via EtherFi)
  2. Supply weETH to Aave (accepted, 72.5% LTV)
  3. Short ETH on HyperLiquid with separate USDC margin (NOT weETH)
  4. Verify strategy correctly separates staking collateral from perp margin

- [ ] [AGENT] P1. Add negative test: attempt to use weETH as HyperLiquid margin → verify blocked

- [ ] [AGENT] P1. Add auto-wrapping test: send ETH to Aave → verify auto-wrapped to WETH

- [ ] [AGENT] P1. Verify batch/paper/live all perform same wrapping logic

### 3B: Documentation

- [ ] [AGENT] P1. Create `/codex/04-architecture/token-wrapping-and-collateral.md`:
  - Token wrapping reality table (which protocol accepts what)
  - Venue collateral acceptance matrix
  - Auto-wrapping behavior in execution-service
  - Strategy validation rules
  - How to add new token wrapping rules

## Success Criteria

1. Token wrapping registry in UAC with ETH↔WETH, eETH↔weETH, stETH↔wstETH
2. Venue collateral acceptance matrix in UAC covering all 8+ venues
3. Collateral haircuts formalised (reference defi_reserve_params for Aave)
4. Strategy validates collateral acceptance before emitting instructions
5. Strategy auto-corrects token version (ETH→WETH for Aave)
6. Execution pre-processes wrapping when needed
7. Staked basis correctly separates weETH collateral (Aave) from USDC margin (HyperLiquid)
8. Haircut-aware leverage calculations in strategy
9. E2E tests verify correct token flow end-to-end
10. All 5 repos pass `quality-gates.sh`
