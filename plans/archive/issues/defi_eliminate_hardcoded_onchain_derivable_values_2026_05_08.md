---
title:
  "DeFi: eliminate hardcoded on-chain-derivable values — write-once SSOT script for immutable facts (launch dates /
  token decimals) + remove stale fallbacks for governance-controlled values + dynamic-at-runtime for live reads (e2e
  fixture block numbers)"
created: 2026-05-08
author: ikenna
source:
  - unified-api-contracts/unified_api_contracts/registry/chain_env.py:144-192 (PROTOCOL_LAUNCH_DATES — 49 hardcoded
    entries)
  - unified-api-contracts/unified_api_contracts/registry/chain_env.py:146 (AAVEV3 ETHEREUM = "2022-03-14" — provably
    wrong, actual = 2023-01-27)
  - features-onchain-service/features_onchain_service/app/calculators/aave_risk_calculator.py:40-62 (_DEFAULT_LTV per
    token + _FALLBACK_LTV=0.70 + _FALLBACK_LIQ_THRESHOLD=0.75 stale fallbacks)
  - instruments-service/instruments_service/reference_data/adapters/defi/aave_v3.py:38-40 (intent comment "resolved
    dynamically via binary search on aToken contract address (eth_getCode)")
  - e2e-testing/tests/execution/test_mev_protection_e2e.py (block_number=12345678 hardcoded)
  - .cursor/rules/no-empty-fallbacks.mdc workspace rule (no try/except fallback imports)
  - operator directive 2026-05-08:
      "the whole point of the blockchain is that pretty much all the data is on the damn blockchain, and we have Alchemy
      and Graph to get real data for everything... they dont change so we could grab them once i guess and have a ssot
      script then dump to uac i.e. change the current to what the truth is so that its canoncal rather than hacking it
      based off the data we collected"
  - tab 9 incident 2026-05-08 — mtds-lending-indices-20260508-114519 reproduces Bug 1 because UAC
    PROTOCOL_LAUNCH_DATES["ETHEREUM","AAVEV3"]="2022-03-14" causes AAVE V3 ETH 2022-03-14→2023-01-27 dates to
    record_empty(SOURCE_RETURNED_ZERO) instead of record_expected_empty(EXPECTED_PRE_GENESIS_CHAIN)
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# DeFi: eliminate hardcoded on-chain-derivable values

> **Severity**: P0 for the AAVEV3 ETHEREUM launch-date error (active VM is mis-routing today, contaminating writegate
> Phase 2.E `EXPECTED_PRE_GENESIS_CHAIN` taxonomy); P1 for the broader 49-entry table + LTV fallbacks; P2 for
> e2e-testing fixtures. **Blast radius**: UAC `chain_env.py` (49 launch-date entries) + features-onchain-service (LTV
> fallbacks) + execution-service (address constants — milder, mostly correct) + e2e-testing (block-number fixtures) +
> new `unified-trading-pm/scripts/onchain_truth/` SSOT generator. **Suggested owner**: `defi_master_2026_05_07.md` Phase
> X (new). Composes with: `defi_protocol_governance_parameters_refresh_2026_05_08.md` (overlaps on Aave rate params at
> the consumer side), `writegate_honest_coverage_endtoend_2026_05_06.md` Phase 2.E (the `EXPECTED_PRE_GENESIS_CHAIN`
> taxonomy that depends on correct launch dates), and `mtds_streaming_and_backpressure_2026_05_07.md` (the
> lending-indices VM uses these dates for pre-launch skip decisions).

## What I found

The principle behind the 2026-05-08 operator directive: blockchain data IS on the blockchain. We have Alchemy + Graph +
direct RPC. Hardcoded values are anti-pattern wherever they represent on-chain truth. But the right SHAPE depends on the
volatility class of the value:

### Three categories — different fix shape per category

| Category                                    | Volatility                    | Right shape                                                                                                              | Examples                                                                                               |
| ------------------------------------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| **A — Immutable historical facts**          | Write-once at protocol deploy | One-time SSOT script derives via on-chain → commits canonical values to UAC. Re-run only if new (chain, protocol) added. | Protocol launch dates, token decimals, token symbols, factory contract addresses, chain genesis blocks |
| **B — Slow-changing governance-controlled** | Changes via DAO vote (months) | Time-versioned parquet refresh (issue 11 governance refresh) + remove stale-fallback consumers                           | Aave LTV / liquidation threshold / IRM curve, Compound borrow caps, Morpho market params               |
| **C — Real-time live reads**                | Per-block / per-tick          | Dynamic at runtime, NO caching, NO fallback — fail loud on RPC error                                                     | Latest block number, gas price, current pool depth, mempool state, oracle price                        |

The current workspace conflates all three categories under "hardcoded constants in UAC." The fix is differentiated, not
uniform.

### Cat A — `PROTOCOL_LAUNCH_DATES` table is hardcoded with at least one P0-wrong entry

[chain_env.py:144-192](../../../unified-api-contracts/unified_api_contracts/registry/chain_env.py#L144-L192) — 49
hardcoded `(chain, protocol)` launch dates. Each is a write-once historical fact that's empirically derivable from
on-chain. The values today were likely seeded from DefiLlama / docs / memory, not from on-chain truth — confirmed by the
AAVEV3 ETHEREUM "2022-03-14" entry which is **49 days off** from the actual deployment of 2023-01-27.

**Specific wrong entry, P0 severity** (live VM impact today):

- `("ETHEREUM", "AAVEV3"): "2022-03-14"` ← wrong. Actual mainnet deployment 2023-01-27. Caused
  `mtds-lending-indices-20260508-114519` Tab 9 reproducer: AAVE V3 ETH 2022-2023 dates emit
  `record_empty(SOURCE_RETURNED_ZERO)` instead of `record_expected_empty(EXPECTED_PRE_GENESIS_CHAIN)` — violates
  writegate Phase 2.E taxonomy AND wastes RPC quota on guaranteed-empty fetches.

**Other entries to verify** (likely correct but spot-check needed):

- All Compound V3 entries (6 chains)
- All Uniswap V2/V3/V4 entries (8 chains)
- All Curve, Balancer, SushiSwap entries
- All LST entries (Lido, Rocketpool, EtherFi, Frax, Stader, Kelp, Renzo)
- All Solana protocol entries (Marinade, Jito, Sanctum, etc.)

**On-chain derivation method**: Per protocol's known mainnet proxy address, binary-search
`eth_getCode(address, block_number=N)` → first block where code is non-empty →
`eth_getBlockByNumber(block, true).timestamp`. For protocols with named deploy events, query Graph subgraph
`min(block.timestamp where event.contract == proxy)`.

### Cat B — `aave_risk_calculator.py` has stale-fallback LTV constants (workspace anti-pattern)

[aave_risk_calculator.py:40-62](../../../features-onchain-service/features_onchain_service/app/calculators/aave_risk_calculator.py#L40-L62):

```python
_DEFAULT_LTV = {
    "WETH": 0.825,
    "WBTC": 0.73,
    "USDC": 0.77,
    # ...
}
_FALLBACK_LTV = 0.70
_FALLBACK_LIQ_THRESHOLD = 0.75
```

These are FALLBACKS used when on-chain `PoolDataProvider.getReserveConfigurationData(asset)` read fails. **Per workspace
`.cursor/rules/no-empty-fallbacks.mdc` rule, this fallback shape is banned.** Two compounding problems:

1. The fallback values themselves drift via Aave governance — `WETH=0.825` was correct at code-time; current on-chain
   value may be 0.80 or 0.85 depending on subsequent votes.
2. The fallback hides on-chain RPC errors — calculator silently produces output using stale defaults instead of failing
   loud + alerting operator.

This composes with issue 11 (governance params refresh) — that issue covers the refresh + time-versioning at
instruments-service grain; this issue removes the consumer-side stale fallback at features-onchain-service grain.

### Cat C — e2e-testing fixtures hardcode block numbers + balances

[e2e-testing/tests/execution/test_mev_protection_e2e.py] — repeated `block_number=12345678` literal for Tenderly fork
fixtures. Should call `eth_blockNumber()` at test runtime OR use Tenderly's `/fork/latest`. Synthetic balances +
bankroll values in sports backtests (`scripts/sports/arb_rolling_backtest.py: --bankroll 10000`) similarly.

These are test-only but they violate the workspace `Live = batch` principle: tests written against fake on-chain state
don't validate real-world semantics. When Aave changes its `liquidation_threshold` via governance, our integration tests
don't catch the strategy-side breakage because they use frozen fixtures.

### Q1.5 — execution-service contract addresses: mostly correct, one cleanup

[execution-service/execution_service/venues/uniswap.py] hardcodes
`SWAP_ROUTER=0x68b34..., QUOTER=0x61fFE..., FACTORY=0x1F98...`. These ARE Cat A immutable values — Uniswap V3 router is
a singleton proxy, won't change. So hardcoding is acceptable, but they should reference UAC `testnet_contracts.yaml`
registry rather than inlining literals. Cleanup, not anti-pattern.

## Why it matters

- **Active VM mis-routing today**: the AAVEV3 ETHEREUM date error is producing wrong manifest rows on the running
  `mtds-lending-indices-20260508-114519` VM right now. Per Tab 9, AAVE V3 ETH 2022-03-14 → 2023-01-27 dates are
  recording `SOURCE_RETURNED_ZERO` instead of `EXPECTED_PRE_GENESIS_CHAIN`. Composes badly with writegate Phase 2.E
  reason taxonomy — the manifest's reason classifier can't distinguish "venue legitimately had no data" from "we asked
  before the protocol existed."
- **`Live = batch` violation**: live mode would naturally hit the chain and observe "contract not deployed" via
  `eth_getCode == 0x`. Batch's hardcoded date diverges from that reality.
- **Compounds with the broader honest-coverage promise**: writegate's coverage % math depends on the manifest's expected
  universe being correct. Wrong launch date → wrong "alive instrument-day" universe → wrong denominator → wrong %.
- **Stale-fallback masks operator alerts**: when Aave RPC is down OR when governance just changed LTV,
  features-onchain-service's `_FALLBACK_LTV=0.70` produces silently-wrong APR / risk computations. Strategies size
  against bad numbers; nobody knows.
- **Trust in UAC degrades**: every wrong hardcoded value in UAC is a small bet against the principle that UAC is
  canonical. Once one is wrong, every consumer reasonably distrusts the rest. The fix has to be systemic
  (truth-derivation script), not one-off.

## Recommended decision

### Phase 1 (P0, immediate) — Fix the AAVEV3 ETHEREUM date + audit Cat A immutable values via SSOT script

Write `unified-trading-pm/scripts/onchain_truth/derive_protocol_launch_dates.py`:

```python
"""
Derives canonical protocol launch dates from on-chain via binary search on eth_getCode.

For each (chain, protocol_address) in INPUT, finds the first block where eth_getCode != 0x,
then reads block.timestamp. Output is a CSV that drops into UAC chain_env.py PROTOCOL_LAUNCH_DATES.

Run on a same-region GCE VM (cross-region RPC is slow). Re-run only when adding a new (chain, protocol).
"""

INPUT = [
    # (chain, protocol, contract_address_to_probe, source_method)
    ("ETHEREUM", "AAVEV3", "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2", "binary_search_eth_getCode"),
    ("ARBITRUM", "AAVEV3", "0x794a61358D6845594F94dc1DB02A252b5b4814aD", "binary_search_eth_getCode"),
    # ... 47 more
]
```

Output committed to UAC alongside the existing `PROTOCOL_LAUNCH_DATES` table, with an explicit comment per entry citing
`block_number + tx_hash + verified_at_timestamp`. Script idempotent — re-run produces identical output (the past doesn't
change), serves as SSOT regenerator if the table is ever in dispute again.

**Pre-commit gate** (PM `quality-gates.sh` STEP X.YY): any change to `PROTOCOL_LAUNCH_DATES` MUST cite the corresponding
`block_number + tx_hash` in a comment OR be paired with a re-run of `derive_protocol_launch_dates.py` evidenced in the
commit message. Eliminates the "someone seeded from DefiLlama / memory / vibes" failure mode.

**Concrete output**: `("ETHEREUM", "AAVEV3"): "2022-03-14"` →
`("ETHEREUM", "AAVEV3"): "2023-01-27"  # block 16496789, tx 0xfd2cee1c..., verified 2026-05-08`. Plus a paired manifest
cleanup (per issue 12) — `record_empty(SOURCE_RETURNED_ZERO)` rows for AAVE V3 ETH 2022 dates re-classified to
`record_expected_empty(EXPECTED_PRE_GENESIS_CHAIN)`.

### Phase 2 (P1) — Cat A audit beyond launch dates

Same SSOT-script pattern for:

- **Token decimals**: derive via `ERC20.decimals()` per token — write-once. Today's status: spot-check whether
  instruments-service hardcodes decimals or reads on-chain. If hardcoded, the script regenerates the truth.
- **Token symbols**: derive via `ERC20.symbol()` per token. Less critical (display), but same pattern.
- **Factory contract addresses**: cross-check execution-service hardcoded constants against UAC
  `testnet_contracts.yaml`. Lift inline addresses to the registry.
- **Chain genesis dates**: derive via `eth_getBlockByNumber(0, true).timestamp` per chain. Today's status: per CLAUDE.md
  "EXPECTED_PRE_GENESIS_CHAIN" rule, these dates exist in UAC; verify they match on-chain truth.

### Phase 3 (P1) — Cat B remove stale-fallback LTV constants

`aave_risk_calculator.py:40-62` deletion:

```python
# REMOVE: _DEFAULT_LTV, _FALLBACK_LTV, _FALLBACK_LIQ_THRESHOLD

# REPLACE with: read from PoolDataProvider on-chain at calculator init OR
# read from time-versioned governance_params parquet (per issue 11 Phase 2)
def get_ltv(asset_address: str, asof: datetime) -> float:
    return governance_params.lookup(
        protocol="aave_v3",
        chain="ethereum",
        asset=asset_address,
        asof=asof,
        field="ltv",
    )  # raises if no asof match — NO FALLBACK
```

Composes with issue 11's Phase 2 time-versioned governance_params parquet. When that lands, `aave_risk_calculator` reads
from it; when it's not yet shipped, calculator fails loud (per workspace no-fallback rule). Operator gets immediate
signal.

### Phase 4 (P2) — Cat C dynamic-at-runtime test fixtures

- e2e-testing test_mev_protection_e2e: replace `block_number=12345678` with `eth_blockNumber()` at fixture setup time,
  OR use Tenderly fork's `/fork/latest` block.
- Sports e2e backtest fixtures: same pattern — read from real exchange API balance (or unified-trading-library
  deterministic fixtures derived from real historical data, not synthetic constants).
- New e2e-testing rule (`.claude/CLAUDE.md` per-repo extension OR workspace rule): "test fixtures MUST NOT hardcode
  on-chain-derivable values; use dynamic reads or Tenderly fork latest."

### Phase 5 — Workspace lint rule

New PM `quality-gates.sh` STEP X.YZ: AST-walk for hardcoded `block_number=` literals in test files + hardcoded
address-like strings (0x... 40-char hex) outside of UAC registry files. Fail PR-time on new instances. Existing
instances grandfathered + tracked in a one-time cleanup tier.

## Acceptance criteria

- [ ] `derive_protocol_launch_dates.py` SSOT script shipped + run; UAC `PROTOCOL_LAUNCH_DATES` table updated with
      truth-derived values + per-entry block_number/tx_hash comments.
- [ ] AAVEV3 ETHEREUM specifically: 2022-03-14 → 2023-01-27. Manifest rows for AAVE V3 ETH 2022 dates re-classified from
      `SOURCE_RETURNED_ZERO` to `EXPECTED_PRE_GENESIS_CHAIN`.
- [ ] Pre-commit gate: changes to PROTOCOL_LAUNCH_DATES require block_number + tx_hash citation in comment OR
      script-re-run evidence in commit message.
- [ ] Cat A audit complete: token decimals, factory addresses, chain genesis dates all spot-checked against on-chain
      truth.
- [ ] `aave_risk_calculator.py` `_DEFAULT_LTV` + `_FALLBACK_LTV` + `_FALLBACK_LIQ_THRESHOLD` deleted; on-chain read OR
      governance_params parquet lookup with no fallback.
- [ ] e2e-testing block_number=12345678 instances replaced with dynamic reads.
- [ ] PM QG step X.YZ added: lint for hardcoded block_numbers + hex addresses outside UAC.
- [ ] Manifest cleanup per issue 12: every entity affected by date corrections gets
      `record_expected_empty(EXPECTED_PRE_GENESIS_CHAIN)` retroactive flip.
- [ ] Smoke test: re-run `mtds-lending-indices-20260508-114519`-style backfill for AAVE V3 ETH; verify pre-2023-01-27
      dates emit `EXPECTED_PRE_GENESIS_CHAIN` and 2023-01-27+ dates emit captured rows.

## Open questions

- For non-EVM chains (Solana protocols), `eth_getCode` doesn't apply. Solana program-deployment timestamp derivation:
  query `getSignaturesForAddress(program_id)` + take first signature's `blockTime`. Implement per-chain-kind in the SSOT
  script.
- For protocols that migrated proxy addresses (Aave V2 → V3 same chain): which address counts as "the protocol's
  launch"? Recommend: each major version has its own (chain, protocol) entry, distinct deploy date.
- For Hyperliquid (covered in `defi_chain_coverage_and_clob_venues_2026_05_08.md`): no `eth_getCode` equivalent until L1
  chain identity lands. Phase 1 EVM + Solana only; Hyperliquid + Starknet in Phase 1.5.
- Coordination with issue 11 governance params refresh: the LTV fallback removal in Phase 3 of THIS issue depends on
  issue 11's Phase 2 time-versioned governance_params parquet being shipped. Sequence: ship issue 11 Phase 2 first, then
  this issue's Phase 3.
- Coordination with issue 12 manifest cleanup mandate: the AAVEV3 ETH date correction is exactly the kind of "entity
  change requires manifest cleanup" case that issue 12 codifies. Verify the cleanup workflow handles "value-correction"
  cases (re-classify existing manifest rows) not just add/remove.
- Should the SSOT script live in `unified-trading-pm/scripts/onchain_truth/` (PM repo) or
  `unified-api-contracts/scripts/onchain_truth/` (UAC repo)? UAC is more natural since the output lands in UAC. Default:
  UAC repo.
- For test fixtures: is there an appetite to convert e2e tests to use Tenderly forks pinned to a known good block +
  checkpoint, refreshed quarterly? That's a hybrid between Cat A (write-once) and Cat C (dynamic) — pinned at known
  state but updated when real-world state diverges materially.
