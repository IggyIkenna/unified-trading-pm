# Cross-Cutting: MEV Protection

> **What it is:** The DeFi-specific execution policy for routing transactions to avoid miner/validator extractable value
> (frontrunning, sandwich attacks, backrunning). MEV protection is a _submission-mode_ choice per transaction,
> configurable per chain + DEX + size.

## Applies to

- DeFi `SWAP` actions on EVM chains (Ethereum mainnet primarily; also Arbitrum/Optimism where MEV bots operate)
- DeFi `LEND`/`BORROW`/`STAKE` typically exempt (smaller MEV surface)
- `LIQUIDATION_CAPTURE` has its own MEV profile (we ARE the MEV bot — use public mempool or private relay per venue's
  competitive landscape)

## MEV submission modes

| Mode                                  | Relay                           | Protection                       | Speed               |
| ------------------------------------- | ------------------------------- | -------------------------------- | ------------------- |
| `PUBLIC_MEMPOOL`                      | standard eth_sendRawTransaction | None                             | Fastest propagation |
| `FLASHBOTS_PROTECT`                   | Flashbots RPC (private pool)    | Strong (bundle-only inclusion)   | +200-1000ms typical |
| `MEV_BLOCKER`                         | MEV Blocker RPC                 | Strong                           | +200-1000ms         |
| `MANIFOLD`                            | Manifold relay                  | Strong; revenue share on backrun | +200-1000ms         |
| `BLOXROUTE` (deprecated in our stack) | Bloxroute public                | Medium                           | Fastest             |
| `CUSTOM_PRIVATE_RPC`                  | Operator-provided RPC           | Varies                           | Varies              |

**Note:** Bloxroute is removed from our stack (per CLAUDE.md). Do not re-introduce without explicit decision.

## Policy mapping

Strategies reference a MEV policy (artifact-versioned):

```yaml
mev_policy_id: mainnet-swap-standard-v3
version: 3
rules:
  - when:
      chain: ETHEREUM
      notional_usd: { ">=": 10_000 }
    then:
      submission_mode: FLASHBOTS_PROTECT
      max_blocks_to_wait: 25
      slippage_bps_max: 30
      backrun_share: accept_up_to_50_percent

  - when:
      chain: ETHEREUM
      notional_usd: { "<": 10_000 }
    then:
      submission_mode: PUBLIC_MEMPOOL
      slippage_bps_max: 50

  - when:
      chain: ARBITRUM
    then:
      submission_mode: PUBLIC_MEMPOOL # less MEV on L2
      slippage_bps_max: 20

  - when:
      chain: OPTIMISM
    then:
      submission_mode: PUBLIC_MEMPOOL

  - when:
      chain: BASE
    then:
      submission_mode: PUBLIC_MEMPOOL

  - when:
      chain: POLYGON
    then:
      submission_mode: PUBLIC_MEMPOOL

  - when:
      chain: BSC
    then:
      submission_mode: PUBLIC_MEMPOOL # BSC has validator extraction; different profile
```

## MEV modes × action type

| Action            | Typical MEV exposure     | Default mode                                 |
| ----------------- | ------------------------ | -------------------------------------------- |
| SWAP (DEX, large) | High — sandwich risk     | FLASHBOTS_PROTECT                            |
| SWAP (DEX, small) | Low                      | PUBLIC_MEMPOOL                               |
| LEND / BORROW     | Low                      | PUBLIC_MEMPOOL                               |
| STAKE / UNSTAKE   | Low                      | PUBLIC_MEMPOOL                               |
| LIQUIDATION       | Competitive — WE extract | PUBLIC_MEMPOOL with flash-loan atomic bundle |
| TRANSFER / BRIDGE | Low                      | PUBLIC_MEMPOOL                               |

## Slippage handling

MEV protection doesn't eliminate slippage — it just makes sandwich slippage less likely. Strategy still sets
`slippage_bps_max`:

- **Without MEV protection**: tighter slippage tolerance invites failure (bot squeezes the tolerance)
- **With MEV protection**: tighter tolerance works; sandwich bots can't front-run

## Block-inclusion tradeoffs

- FLASHBOTS_PROTECT: bundle-only inclusion; if no builder picks it within `max_blocks_to_wait`, tx expires and can retry
- PUBLIC_MEMPOOL: faster inclusion but vulnerable to frontrunning

## Benchmark fills interaction

Benchmark fills in batch mode use the **pre-block mid** at swap-request time (not the filled price). Live mode measures
`execution_alpha = filled_price - benchmark_mid`. MEV protection's job is to minimize the gap — and attribute
`adverse_selection = worst_case_unprotected - actual_filled` for cost analysis.

## Integration with execution-policy

MEV mode is one of the algo params. `MEV_PROTECTED_SWAP` is an algo in the library
([execution-policies.md](execution-policies.md)) that wraps the underlying swap with private-relay submission.

## Monitoring

- **MEV capture rate**: fraction of our txns that detected a sandwich attempt that was blocked
- **Private-relay success rate**: fraction of submitted bundles that got included within deadline
- **Cost of protection**: delay (ms) per successful private-relay submission
- **Revenue from backrun sharing** (Manifold / MEV-share): per-tx capture

## Provider operational notes

| Provider               | Status      | Notes                                    |
| ---------------------- | ----------- | ---------------------------------------- |
| Flashbots              | Active      | Default for Ethereum mainnet large swaps |
| MEV Blocker            | Backup      | Available as fallback                    |
| Manifold               | Opt-in      | Use when backrun revenue share valuable  |
| Bloxroute              | **REMOVED** | Per CLAUDE.md; do not re-introduce       |
| Eden                   | Not active  | Consider if Flashbots congested          |
| Builder network direct | Future      | For very large institutional routing     |

## Not in this doc

- **Liquidation flash-loan bundle** — the strategy-side execution algo in [execution-policies.md](execution-policies.md)
- **Oracle-update frontrunning arb** — niche arbitrage strategy (signal source mempool)
- **Centralized-exchange front-running** — N/A (CEXes handle internally)
- **Policy storage + versioning internals** — [execution-policies.md](execution-policies.md) and artifact-versioning
- **Per-venue adapter mechanics** — execution-service/adapters/

## Cross-references

- Execution policies: [execution-policies.md](execution-policies.md)
- Venue selection: [venue-selection-split.md](venue-selection-split.md)
- Archetype that competes for MEV: [../archetypes/liquidation-capture.md](../archetypes/liquidation-capture.md)
- Benchmark fills: [benchmark-fills.md](benchmark-fills.md)
