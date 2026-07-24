---
doc_type: plan
title: mev-protection-and-execution-enhancements
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
remaining_todos_consolidated_into: consolidated_defi_data_pipeline_2026_04_15
superseded_by: [consolidated_defi_data_pipeline_2026_04_15.md]
reconciliation_status: superseded_by_consolidator
reconciliation_date: 2026-04-25
overview:
  MEV protection framework (Flashbots pipes, private mempool), execution algo comparison, basis trade dynamic coin
  selection
type: code
epic: epic-code-completion
locked_by: live-defi-rollout
locked_since: 2026-04-01
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - { repo: unified-api-contracts, code: C0, deployment: none, business: none }
  - { repo: execution-service, code: C0, deployment: none, business: none }
  - { repo: strategy-service, code: C0, deployment: none, business: none }
  - { repo: e2e-testing, code: C0, deployment: none, business: none }
depends_on: [token-wrapping-venue-collateral]
todos:
  - { id: mev-1a-framework, content: "- [x] [AGENT] P0. Create MEV protection framework in execution-service (Flashbots
        pipes)

        ", status: done, note: Pipes only — paid subscriptions not required yet }
  - { id: mev-1b-protected-rpc, content: "- [x] [AGENT] P1. Add protected RPC configuration (MEV Blocker, Flashbots
        Protect)

        ", status: done, note: "PROTECTED_RPC_URLS dict added to UAC _defi.py, exported from capability_declarations and
        registry __init__.py" }
  - { id: mev-2a-basis-coins, content: "- [x] [AGENT] P0. Implement dynamic coin selection for basis trade from
        instrument registry

        ", status: done, note: _get_eligible_basis_coins() added to BasisTradeStrategy; wired into _scan_percoin_keys() }
  - { id: mev-2b-rebalance-costbenefit, content: "- [x] [AGENT] P0. Add rebalance cost-benefit analysis to basis trade

        ", status: done, note: _should_rebalance() added; wired into _build_rebalance_instructions() as cost-benefit
        gate }
  - { id: mev-2c-algo-comparison, content: "- [x] [AGENT] P1. Create execution algo comparison framework (TWAP vs VWAP
        vs direct)

        ", status: done, note: AlgoComparisonRunner skeleton in execution_service/algo_library/algo_comparison.py with
        AlgoRunResult and ComparisonReport }
  - { id: mev-3a-e2e, content: "- [ ] [AGENT] P1. Add MEV + execution scenarios to e2e-testing

        ", status: todo, note: "" }
  - { id: mev-4a-docs, content: "- [x] [AGENT] P1. Document MEV protection + execution enhancements in codex

        ", status: done, note: /codex/07-security/mev-protection.md created in unified-trading-pm }
isProject: false
---

> **SUPERSEDED 2026-04-25 by
> [consolidated_defi_data_pipeline_2026_04_15.md](./consolidated_defi_data_pipeline_2026_04_15.md).** Original scope
> retained for history. Frontmatter `remaining_todos_consolidated_into:` was already present; this commit formalises it
> as canonical `superseded_by:` and adds this banner. See `_reconciliation_evidence_map_2026_04_25.md` for evidence.

# MEV Protection & Execution Enhancements

## Context

### MEV Protection

DeFi on-chain transactions are visible in the mempool before inclusion. Sandwich attacks can extract value from large
swaps. Current state: Tenderly pre-simulation catches reverts and measures expected slippage, but there's no protection
against frontrunning once the transaction hits the real mempool.

**Approach**: Build the pipes/framework now. Full implementation requires paid subscriptions (Flashbots relay, private
RPC providers) that aren't needed for testnet/paper trading. But the code paths should be ready so flipping to
production is a config change, not a code change.

### Execution Enhancements

Three related improvements:

1. **Dynamic coin selection for basis trade**: Currently limited to config-defined coins. Should dynamically select from
   instrument registry based on funding rates.
2. **Rebalance cost-benefit analysis**: Don't rebalance if gas/slippage exceeds the yield improvement.
3. **Execution algo comparison**: Different DeFi operations need different algos (TWAP for large swaps, direct for
   lending, etc.). Framework to compare and select.

## Execution DAG

```
Phase 1 (PARALLEL — framework + config)
  ├── 1A: MEV protection framework in execution-service
  └── 1B: Protected RPC configuration in UAC/config
        │
        ▼  QG gate: execution-service + UAC pass
Phase 2 (PARALLEL — strategy enhancements)
  ├── 2A: Dynamic coin selection for basis
  ├── 2B: Rebalance cost-benefit analysis
  └── 2C: Execution algo comparison framework
        │
        ▼  QG gate: strategy-service + execution-service pass
Phase 3 (E2E + Docs)
  ├── 3A: E2E scenarios
  └── 3B: Codex documentation
```

## Phase 1: MEV Protection Framework (PARALLEL)

### 1A: MEV Protection Framework

**Repo**: execution-service

- [x] [AGENT] P0. Create `execution_service/defi_execution/mev/` package:

  ```
  mev/
  ├── __init__.py
  ├── protection.py       # MEVProtectionProvider interface
  ├── flashbots.py        # Flashbots bundle submission
  ├── private_mempool.py  # Private RPC submission (MEV Blocker, etc.)
  └── config.py           # MEV protection configuration
  ```

  Note: config.py not present — config is inlined in protection.py factory args.

- [x] [AGENT] P0. Define `MEVProtectionProvider` interface:

  ```python
  class MEVProtectionProvider(Protocol):
      """Interface for MEV protection strategies."""

      async def submit_transaction(
          self,
          signed_tx: bytes,
          chain_id: int,
          max_block_number: int | None = None,
      ) -> TxSubmissionResult:
          """Submit transaction with MEV protection.

          Instead of broadcasting to public mempool, routes through
          protected channel (Flashbots relay, private mempool, etc.)
          """
          ...

      async def submit_bundle(
          self,
          signed_txs: list[bytes],
          target_block: int,
          chain_id: int,
      ) -> BundleSubmissionResult:
          """Submit atomic bundle (all-or-nothing in single block).

          Used for flash loan sequences where partial execution = loss.
          """
          ...

      def estimate_protection_cost(self, tx_type: str) -> Decimal:
          """Estimate additional cost of MEV protection (tips, relay fees)."""
          ...
  ```

- [x] [AGENT] P0. Implement `FlashbotsProvider`:

  ```python
  class FlashbotsProvider(MEVProtectionProvider):
      """Flashbots bundle submission for Ethereum mainnet.

      Requires:
      - Flashbots relay endpoint (https://relay.flashbots.net)
      - Signing key for bundle authentication
      - Target block number for inclusion

      Bundle format: eth_sendBundle RPC call to relay
      """

      def __init__(self, relay_url: str, auth_signer: Any):
          self.relay_url = relay_url or "https://relay.flashbots.net"
          self.auth_signer = auth_signer

      async def submit_bundle(self, signed_txs, target_block, chain_id):
          # Build Flashbots bundle payload
          # Sign with auth key
          # POST to relay
          # Return inclusion status
          ...
  ```

- [x] [AGENT] P0. Implement `PrivateMempoolProvider`:

  ```python
  class PrivateMempoolProvider(MEVProtectionProvider):
      """Submit transactions via private RPC endpoints that don't broadcast to public mempool.

      Options:
      - MEV Blocker (https://rpc.mevblocker.io) — free, OFA-based
      - Flashbots Protect (https://rpc.flashbots.net) — free, Flashbots relay
      - BloxRoute (paid) — private transactions

      Simply replaces the standard RPC endpoint for tx submission.
      """
  ```

- [x] [AGENT] P0. Implement `NoProtectionProvider` (passthrough for testnet/paper):

  ```python
  class NoProtectionProvider(MEVProtectionProvider):
      """No MEV protection — submit directly to public mempool.

      Used for: testnet, Tenderly forks, paper trading.
      """
  ```

- [x] [AGENT] P0. Create `MEVProtectionConfig`:

  ```python
  class MEVProtectionConfig(BaseModel):
      enabled: bool = False
      provider: str = "none"  # "flashbots", "private_mempool", "none"
      relay_url: str = "https://relay.flashbots.net"
      private_rpc_url: str = "https://rpc.flashbots.net"  # Flashbots Protect
      max_tip_gwei: Decimal = Decimal("3")  # Max priority fee for Flashbots
      bundle_timeout_blocks: int = 5  # How many blocks to try before giving up
  ```

- [x] [AGENT] P0. Integrate MEV protection into swap handler pipeline:

  ```python
  # In swap_handler.py:
  async def execute(self, instruction):
      # 1. Build transaction
      tx = self.build_swap_tx(instruction)

      # 2. Pre-simulate on Tenderly (existing)
      sim_result = await self.tenderly.simulate(tx)
      if sim_result.reverted:
          return error_fill(...)

      # 3. Submit via MEV protection provider (NEW)
      result = await self.mev_provider.submit_transaction(
          signed_tx=self.sign(tx),
          chain_id=instruction.chain_id,
      )
      return fill_from_result(result)
  ```

- [x] [AGENT] P0. Wire MEV provider selection based on execution mode:
  - `batch` mode → `NoProtectionProvider` (Tenderly fork, no MEV)
  - `paper` mode → `NoProtectionProvider` (Tenderly fork)
  - `live` mode → Based on config (`FlashbotsProvider` or `PrivateMempoolProvider`)

- [ ] [AGENT] P0. Run `cd execution-service && bash scripts/quality-gates.sh`

### 1B: Protected RPC Configuration

**Repo**: unified-api-contracts, unified-config-interface

- [x] [AGENT] P1. Add MEV-protected RPC URLs to chain config in UAC:

  ```python
  # In CHAIN_RPC_TEMPLATES or similar:
  PROTECTED_RPC_URLS = {
      "ETHEREUM": {
          "flashbots_protect": "https://rpc.flashbots.net",
          "mev_blocker": "https://rpc.mevblocker.io",
      },
      "ARBITRUM": {
          # Arbitrum has native MEV protection via sequencer
          "default": "standard RPC is already protected",
      },
  }
  ```

- [ ] [AGENT] P1. Note: L2 chains (Arbitrum, Base, Optimism) have sequencer-level ordering that inherently protects
      against most MEV. MEV protection is primarily an L1 Ethereum concern.

## Phase 2: Strategy Enhancements (PARALLEL)

### 2A: Dynamic Coin Selection for Basis Trade

**Repo**: strategy-service

- [x] [AGENT] P0. In `defi_basis.py`, make coin selection dynamic from instrument registry:

  ```python
  def _get_eligible_basis_coins(self) -> list[str]:
      """Get coins eligible for basis trade from instrument registry.

      Uses UAC's hyperliquid_aster_mvp_base_assets (21 coins) as the universe.
      Filters to coins that:
      1. Have perp instrument definitions at allowed venues
      2. Have spot instrument definitions for the swap leg
      3. Have funding rate features available
      4. Are not excluded by client config

      Returns list of coin symbols sorted by average funding rate.
      """
      from unified_api_contracts import INSTRUMENT_TYPES_BY_VENUE
      # Get all perp instruments at allowed venues
      # Filter to coins with both spot and perp available
      # Intersect with client_override.allowed_coins if set
  ```

- [ ] [AGENT] P0. Verify all 21 MVP base assets have:
  - Perp instrument on HyperLiquid (confirmed in venue_mapping)
  - Spot price feed in MTDS (check each: SOL, BTC, ETH, AVAX, ADA, SUSHI, CAKE, XRP, DOGE, XLM, LTC, ALGO, FIL, TRX,
    BNB, LINK, MATIC, APT, VET, ATOM, NEAR)
  - Funding rate features in features service
  - If any missing, add to instrument pipeline plan as dependency

- [ ] [AGENT] P0. Add `funding_rate_{COIN}_{VENUE}` feature key pattern to strategy config:

  ```python
  # Dynamic feature key construction:
  for coin in eligible_coins:
      for venue in allowed_venues:
          feature_key = f"funding_rate_{coin}_{venue}"
          if feature_key in features:
              coin_venue_rates.append((coin, venue, features[feature_key]))
  ```

- [ ] [AGENT] P0. Run `cd strategy-service && bash scripts/quality-gates.sh`

### 2B: Rebalance Cost-Benefit Analysis

**Repo**: strategy-service

- [x] [AGENT] P0. In basis trade rebalancing decision, add cost-benefit check:

  ```python
  def _should_rebalance(
      self,
      current_weights: dict[str, Decimal],
      target_weights: dict[str, Decimal],
      current_positions: dict,
      features: dict,
  ) -> tuple[bool, str]:
      """Decide whether to rebalance based on cost vs benefit.

      Benefit = expected additional yield from moving to target weights
        = sum((target_weight - current_weight) * venue_funding_rate) * holding_period

      Cost = estimated execution cost to move positions
        = gas for swaps + slippage on exits + slippage on entries
        + bridge fees if cross-chain + exchange fees on perp closes/opens

      Rebalance only if: benefit > cost * safety_margin (e.g., 1.5x)

      Returns: (should_rebalance, reason_string)
      """
  ```

- [ ] [AGENT] P0. Add cost estimation for each rebalancing action:
  - Close perp at venue A: estimated slippage from order book depth feature
  - Open perp at venue B: estimated slippage
  - Swap spot if different coin: gas + AMM slippage
  - Bridge if cross-chain: gas + bridge fee + time cost
  - Total = sum of all legs

- [ ] [AGENT] P0. Make the `safety_margin` configurable (default 1.5x = only rebalance if benefit is 50% more than cost)

- [ ] [AGENT] P0. Log rebalance decisions with full cost-benefit breakdown for analysis

### 2C: Execution Algo Comparison Framework

**Repo**: execution-service

- [ ] [AGENT] P1. Create execution algo recommendation per DeFi operation type:

  ```python
  DEFI_ALGO_RECOMMENDATIONS: dict[str, str] = {
      "SWAP_SMALL": "DIRECT",       # < $10K swap — just execute directly
      "SWAP_MEDIUM": "SOR_TWAP",    # $10K-$100K — split across time
      "SWAP_LARGE": "ADAPTIVE_TWAP", # > $100K — adaptive based on vol
      "LEND": "DIRECT",             # No price impact for lending
      "BORROW": "DIRECT",           # No price impact for borrowing
      "STAKE": "DIRECT",            # No price impact for staking
      "UNSTAKE": "DIRECT",          # No price impact
      "FLASH_LOAN": "ATOMIC",       # Must be atomic
      "PERP_TRADE": "TWAP",         # Split CeFi perp trades over time
      "BRIDGE": "DIRECT",           # No algo needed
  }
  ```

- [ ] [AGENT] P1. Add algo selection to instruction metadata:

  ```python
  # In StrategyInstruction or execution routing:
  recommended_algo = DEFI_ALGO_RECOMMENDATIONS.get(
      f"{operation_type}_{size_bucket}",
      "DIRECT"
  )
  ```

- [x] [AGENT] P1. Create algo comparison backtest capability:

  ```python
  class AlgoComparisonRunner:
      """Run same set of instructions through different algos and compare alpha.

      For a given set of historical instructions:
      1. Run with DIRECT (baseline)
      2. Run with TWAP (N slices)
      3. Run with VWAP
      4. Compare: alpha_bps = (algo_fill - baseline_fill) / baseline_fill * 10000

      Output: per-instruction and aggregate comparison metrics
      """
  ```

- [ ] [AGENT] P1. Specifically for swaps: simulate slippage at different trade sizes using AMM math:

  ```python
  def simulate_swap_impact(
      pool_reserves: tuple[Decimal, Decimal],
      trade_size: Decimal,
      fee_tier: Decimal,
      n_slices: int = 1,  # 1 = direct, >1 = TWAP
  ) -> Decimal:
      """Simulate price impact of a swap given pool state.

      For Uniswap V3: use concentrated liquidity math (tick-by-tick)
      For constant product: x * y = k
      """
  ```

- [ ] [AGENT] P1. Run `cd execution-service && bash scripts/quality-gates.sh`

## Phase 3: E2E + Docs

### 3A: E2E Scenarios

**Repo**: e2e-testing

- [ ] [AGENT] P1. Add MEV protection integration test:
  - Paper mode: verify `NoProtectionProvider` used (Tenderly fork)
  - Config test: verify switching to `flashbots` provider changes code path
  - NOTE: Cannot fully test Flashbots without mainnet — verify pipes are wired

- [ ] [AGENT] P1. Add dynamic coin selection test:
  - Configure basis trade with 5+ eligible coins
  - Verify strategy selects coins with highest funding rates
  - Verify coins without funding features are excluded

- [ ] [AGENT] P1. Add rebalance cost-benefit test:
  - Set up basis trade with small yield differential
  - Set high gas costs
  - Verify strategy chooses NOT to rebalance (cost > benefit)
  - Set low gas costs
  - Verify strategy DOES rebalance

- [ ] [AGENT] P1. Add algo comparison test:
  - Run same swap through DIRECT vs TWAP
  - Verify alpha measurement is computed and logged

### 3B: Documentation

- [x] [AGENT] P1. Create `/codex/07-security/mev-protection.md`:
  - MEV threat model for DeFi trades
  - Protection strategies (Flashbots, private mempool, L2 sequencer)
  - Configuration per chain
  - Cost of protection (tips, relay fees)
  - Which operations need protection (swaps yes, lending no)

- [ ] [AGENT] P1. Create `/codex/09-strategy/cross-cutting/execution-algo-selection.md`:
  - Algo recommendations per DeFi operation type
  - Cost-benefit rebalancing framework
  - Dynamic coin selection from instrument registry
  - Comparison methodology

## Success Criteria

1. MEV protection framework with `FlashbotsProvider`, `PrivateMempoolProvider`, `NoProtectionProvider`
2. Swap handler wired to use MEV provider based on execution mode
3. Protected RPC URLs configured for Ethereum mainnet
4. L2 chains documented as inherently protected
5. Dynamic coin selection uses instrument registry (21 MVP coins)
6. Rebalance cost-benefit analysis prevents unprofitable rebalancing
7. Algo recommendations per DeFi operation type
8. Algo comparison backtest capability
9. All batch/paper/live modes wired correctly (NoProtection for batch/paper, configurable for live)
10. All 4 repos pass `quality-gates.sh`
