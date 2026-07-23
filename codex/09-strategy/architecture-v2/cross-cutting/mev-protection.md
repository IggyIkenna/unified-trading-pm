---
doc_type: codex-ssot
title: "Cross-Cutting: MEV Protection (strategy-side)"
summary:
  "Strategy-side MEV policy: per-chain / per-notional / per-action submission-mode rules (FLASHBOTS_PROTECT vs
  PUBLIC_MEMPOOL; JITO_BUNDLE for Solana) mirroring UAC `MevSubmissionMode`. Canonical mechanism + provider table live
  in `04-architecture/mev-protection.md`; Bloxroute is removed, do not re-introduce."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, unified-api-contracts]
scope: [engineer, admin]
tags: [mev, defi, execution, strategy, venue-selection, uac]
related:
  [
    ../../../04-architecture/mev-protection.md,
    /codex/09-strategy/architecture-v2/cross-cutting/execution-policies.md,
    /codex/09-strategy/architecture-v2/cross-cutting/venue-selection-split.md,
    /codex/09-strategy/architecture-v2/cross-cutting/benchmark-fills.md,
  ]
created: 2026-04-17
authoritative_for:
  [strategy-side MEV policy mapping (per-strategy MEV policy YAML + per-chain/per-action submission-mode rules)]
referenced_by:
  [
    /codex/04-architecture/execution-policy.md,
    /codex/04-architecture/mev-protection.md,
    /codex/07-security/mev-protection.md,
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md,
    /codex/09-strategy/architecture-v2/archetypes/liquidation-capture.md,
    /codex/09-strategy/architecture-v2/axes/venue-eligibility.md,
    /codex/09-strategy/architecture-v2/cross-cutting/execution-policies.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Cross-Cutting: MEV Protection (strategy-side)

> **CANONICAL location for the protection mechanism**:
> [`/codex/04-architecture/mev-protection.md`](../../../04-architecture/mev-protection.md). This doc is the
> **strategy-side narrative** scope-narrowed 2026-05-10 per `cross_asset_group_catalogue_audit_2026_05_10` Phase 4 codex
> consolidation. Read the canonical for "what is MEV / threat model / protection mechanisms / provider implementations /
> error codes". Read THIS doc for "per-strategy MEV policy YAML + per-chain rules + per-action-type mapping + monitoring
> metrics".
>
> If editing the implementation / threat model / provider behaviour, edit the canonical, NOT this doc.

> **What it is:** The DeFi-specific execution policy for routing transactions to avoid miner/validator extractable value
> (frontrunning, sandwich attacks, backrunning). MEV protection is a _submission-mode_ choice per transaction,
> configurable per chain + DEX + size.

## Applies to

- DeFi `SWAP` actions on EVM chains (Ethereum mainnet primarily; also Arbitrum/Optimism where MEV bots operate)
- DeFi `LEND`/`BORROW`/`STAKE` typically exempt (smaller MEV surface)
- `LIQUIDATION_CAPTURE` has its own MEV profile (we ARE the MEV bot — use public mempool or private relay per venue's
  competitive landscape)

## MEV submission modes

Mirrors UAC `MevSubmissionMode` enum (canonical:
[`unified_api_contracts.internal.architecture_v2.enums.MevSubmissionMode`](../../../../../unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py)).
Implementation detail + provider table lives in
[canonical mev-protection.md](../../../04-architecture/mev-protection.md) § "MEV submission modes (UAC
`MevSubmissionMode`)".

| Mode                         | Relay                                        | Protection                       | Speed               |
| ---------------------------- | -------------------------------------------- | -------------------------------- | ------------------- |
| `PUBLIC_MEMPOOL`             | standard eth_sendRawTransaction              | None                             | Fastest propagation |
| `FLASHBOTS_PROTECT`          | Flashbots RPC (private pool)                 | Strong (bundle-only inclusion)   | +200-1000ms typical |
| `MEV_BLOCKER`                | MEV Blocker RPC                              | Strong                           | +200-1000ms         |
| `MANIFOLD`                   | Manifold relay                               | Strong; revenue share on backrun | +200-1000ms         |
| `CUSTOM_PRIVATE_RPC`         | Operator-provided RPC                        | Varies (per relay)               | Varies              |
| `JITO_BUNDLE` (NEW Phase 5A) | Jito block-engine RPC                        | Strong (Solana)                  | Solana-specific     |
| `BLOXROUTE`                  | (REMOVED per CLAUDE.md; do not re-introduce) | n/a                              | n/a                 |

**Note:** Bloxroute is removed from our stack (per CLAUDE.md). Do not re-introduce without explicit decision. Solana
DeFi swaps use `JITO_BUNDLE` (private mempool via Jito block-engine RPC), resolved at dispatch time.

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
