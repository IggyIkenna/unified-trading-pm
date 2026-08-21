---
doc_type: plan
title: mempool-feed-integration-2026-06-01
summary: Stub plan — wire a pending-mempool feed (Flashbots Protect / MEV-share / Alchemy private mempool) so live MEV sandwich
  + advanced JIT can ship
status: paused
nature: record
asset_group: defi
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-01
locked_by: live-defi-rollout
locked_since: 2026-05-01
plan_type: infra
owner: ikenna
type: infra
epic: epic-infra
completion_gates: {code: C5, deployment: D3, business: B6}
repo_gates:
- {repo: market-tick-data-service, code: C0, deployment: none, business: none}
- {repo: execution-service, code: C0, deployment: none, business: none}
- {repo: strategy-service, code: C0, deployment: none, business: none}
- {repo: unified-api-contracts, code: C0, deployment: none, business: none}
depends_on: [defi_pipeline_extension_2026_05_01]
isProject: false
---

# Mempool Feed Integration — STUB

This plan is a stub created at the close of Phase 5.4 of the DeFi pipeline extension. **Execution is paused** until the
business case clears the following gate:

> Theoretical sandwich profit per month (computed by
> `strategy_service.engine.strategies.v2.mev.sandwich_theoretical `aggregate_theoretical_profit_usd``) on the
> comprehensive 14-archetype tracer pass exceeds the lowest-tier mempool subscription cost by ≥ 3x for two consecutive
> months.

Do not start work on this plan until the gate is cleared.

## Why this plan exists

The DeFi pipeline extension landed live engines for liquidation-bundle, JIT liquidity, and backrun (all derivable from
confirmed-block data). Sandwich shipped as a theoretical-only tracer because live execution requires pending-tx
visibility — the mempool — which the workspace does not currently collect.

Workspace context: Bloxroute was previously the mempool provider; it was removed (see workspace CLAUDE.md "Removed
providers"). Reintegration is not free — it changes the data-pipeline cost surface materially and adds operational
complexity (relay private keys, bundle simulation, reorg protection).

## Out-of-scope deliverables (when the gate clears)

1. **Provider evaluation**
   - Flashbots Protect — reliable, public-good ethos, free for non-MEV users
   - MEV-share — Flashbots' selective-sharing protocol, fees on profit
   - Alchemy private mempool — paid tier, ETH/L2 coverage
   - bloXroute re-add — was removed; reintegration cost includes restoring per-region websocket adapters
   - Decision criteria: monthly cost vs Phase-8 theoretical profit; mempool latency vs target slot time; geographic
     distribution
2. **Bundle relay design**
   - Flashbots / Eden / bloXroute / Beaverbuild relay selection per chain
   - Bundle simulation pre-submission (eth_callBundle / mev_simBundle)
   - Reorg protection: block-number constraints + tx replacement budget
3. **Sandwich engine promotion**
   - Promote `ARBITRAGE_MEV_SANDWICH` from theoretical-only tracer to full live engine in
     `strategy_service/engine/strategies/v2/mev/`
   - Factory registration; per-block ordering aware `on_tick`
4. **Advanced JIT extension**
   - Current `ArbitrageMevJitLiquidityEngine` reads `jit_pending_swap_size_usd_<pool>` from features; with mempool
     visibility, the feature becomes precise per-pending-tx instead of historical-window inference
5. **MTDS adapter**
   - Add `mempool_<provider>` adapter under `market_tick_data_service/adapters/onchain/` writing `pending_tx_pool_state`
     parquets keyed by (chain, block, tx_hash)
6. **Risk-and-exposure overlay**
   - New alert `MEMPOOL_FEED_STALE` when last-pending-tx age > 12 sec (sandwich loses execution edge) — emitted by
     risk-and-exposure-service

## Risks if executed prematurely

- Per-month subscription cost without theoretical-profit cover destroys the business case
- Reorg protection bugs can cause stuck capital across reorgs (live-fund loss, not theoretical)
- Sandwich is publicly contentious; running one without a clear PR position may be reputationally costly. Plan must
  include a **published policy** stance before launch.

## Trigger to un-pause

Operator sees Phase 8 of `defi_pipeline_extension_2026_05_01.md` publish a comprehensive 14-archetype results table; the
SANDWICH row's `theoretical_profit_per_month_usd` clears the 3x cost-cover gate above for two consecutive months.
Operator removes `status: paused` from the frontmatter and starts Phase 1 work.
