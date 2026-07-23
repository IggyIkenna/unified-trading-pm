---
doc_type: codex-ssot
title: Matching Engine Assumptions
summary:
  "The per-matcher assumption surface for batch backtest fidelity — slippage / commission / latency / venue-liquidity
  proxy defaults for the 5 matcher classes (L0 / L1 / L2 / AMM / Benchmark) plus MatchingEngineConfig defaults; every
  InstructionActionV2 must map to a non-default BenchmarkFillMode before it can dispatch in batch."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service]
scope: [engineer, admin]
tags: [execution, strategy, defi, cefi, sports, ssot]
related:
  [
    /codex/04-architecture/matching-engine-mode-dispatch.md,
    /codex/04-architecture/amm-slippage-simulation.md,
    /codex/04-architecture/strategy-ensemble-topology.md,
    /codex/04-architecture/batch-live-architecture.md,
  ]
created: 2026-05-15
authoritative_for: [matching-engine per-matcher assumption surface, MatchingEngineConfig defaults]
referenced_by:
  [/codex/04-architecture/matching-engine-mode-dispatch.md, /codex/04-architecture/strategy-ensemble-topology.md]
owner:
last_reviewed: 2026-05-17
code_refs:
author: ikenna
sources:
  [
    plans/active/topology_qgroup_gap_closure_2026_05_09.md Phase 1 (GAP-12),
    execution-service/execution_service/matching_engine/engine.py,
    "unified_api_contracts/internal/architecture_v2/enums.py (BenchmarkFillMode, InstructionActionV2)",
  ]
---

# Matching Engine Assumptions

> **Rationale.** Closes GAP-12 (Q4.2.c) from the topology Q-doc. This document records the per-matcher slippage model,
> commission schedule, latency model, and venue-liquidity proxy for each of the 5 matcher classes used in batch backtest
> mode. Required for backtest fidelity per master plan Group F item 18.

---

## Matcher classes

The execution-service matching engine (`execution_service/matching_engine/engine.py`) dispatches on `BookType` to one of
5 matcher classes:

| Matcher            | BookType     | Asset domain                                   | Fill semantics                                     |
| ------------------ | ------------ | ---------------------------------------------- | -------------------------------------------------- |
| `L0Matcher`        | `L0_TOB`     | Sports bookmakers / odds aggregators           | Top-of-book only; fill at best bid/offer or reject |
| `L1Matcher`        | `L1_MBP`     | TradFi (aggressor side)                        | NautilusTrader L1 MBP; fill against aggressor      |
| `L2Matcher`        | `L2_MBP`     | CeFi (order book depth)                        | NautilusTrader L2 MBP; depth-aware partial fills   |
| `AMMMatcher`       | `AMM`        | DeFi swaps (Uniswap V2/V3/V4, Curve, Balancer) | Constant-product x\*y=k; slippage-gated            |
| `BenchmarkMatcher` | `ALPHA_ZERO` | DeFi non-price ops (LEND/STAKE/BORROW/UNSTAKE) | Instant fill at benchmark (no slippage)            |

---

## Per-matcher assumption surface

### L0Matcher (Sports)

- **Slippage model**: none — L0 is TOB-only; the quoted best bid/offer IS the fill price
- **Commission**: 0 bps (bookmaker margin is priced into the quoted odds; not modelled separately)
- **Latency model**: negligible (scraped pre-match prices; no order-execution latency in batch)
- **Venue-liquidity proxy**: binary — fills at quoted size or rejects (no partial fills)
- **Rejection condition**: `best_bid`/`best_offer` absent → reject with `err="best_bid required for L0"`

### L1Matcher (TradFi via NautilusTrader)

- **Slippage model**: aggressor-side crossing; fill price = aggressor level in NautilusTrader book
- **Commission**: configurable per venue; default 0.5 bps maker + 0.5 bps taker (round-trip 1 bps)
- **Latency model**: NautilusTrader simulated exchange latency (configurable; default 50ms round-trip)
- **Venue-liquidity proxy**: L1 MBP depth; fills walk the book up to `size`
- **Rejection condition**: insufficient depth → partial fill (if allowed) or reject

### L2Matcher (CeFi)

- **Slippage model**: depth-aware; fills walk L2 book levels up to order size
- **Commission**: configurable per venue; default 2.0 bps taker (CeFi spot/perp)
- **Latency model**: NautilusTrader L2 venue simulation; default 100ms round-trip
- **Venue-liquidity proxy**: full L2 MBP order book from MTDS candle reconstruction
- **Rejection condition**: total available depth < order size AND partial fill not allowed → reject

### AMMMatcher (DeFi)

- **Slippage model**: constant-product x\*y=k with pool reserves; `slippage_bps = |fill_px - mid_px| / mid_px * 10_000`
- **Commission**: pool fee bps (default 30 bps for Uniswap V3 0.3% pool; configurable per pool)
- **Latency model**: 0 (batch) / blockchain confirmation time (live); in batch, treat as instantaneous
- **Venue-liquidity proxy**: pool reserves from MTDS on-chain tick data
- **Rejection condition**: `quote.slippage_bps > max_slippage_bps` (default 100 bps) → reject with `SLIPPAGE_EXCEEDED`;
  pool unavailable → reject with `POOL_UNAVAILABLE`

### BenchmarkMatcher (ALPHA_ZERO — LEND/STAKE/BORROW/UNSTAKE)

- **Slippage model**: none — benchmark fill at the reference rate (LST APR / lending rate)
- **Commission**: 0 (protocol fees are embedded in APR; not separately modelled)
- **Latency model**: 0 (benchmark fills are instantaneous in batch)
- **Venue-liquidity proxy**: unlimited — benchmark ops are modelled as always-available
- **Rejection condition**: none in batch; live connectors may reject on insufficient protocol liquidity

---

## BenchmarkFillMode per InstructionActionV2

`BenchmarkFillMode` (UAC `unified_api_contracts.internal.architecture_v2.enums`) declares how the matching engine fills
each action type in benchmark/batch mode. Every `InstructionActionV2` member must declare a non-default mode:

| Action         | BenchmarkFillMode   | Rationale                                                            |
| -------------- | ------------------- | -------------------------------------------------------------------- |
| `TRADE`        | `ARRIVAL_MID`       | Fill at mid-price at bar arrival (standard equity/futures benchmark) |
| `SWAP`         | `POOL_MID_AT_BLOCK` | Fill at AMM pool mid-price at the block timestamp                    |
| `LEND`         | `PROTOCOL_RATE`     | Fill at the lending protocol rate (Aave/Compound) at bar time        |
| `BORROW`       | `PROTOCOL_RATE`     | Same as LEND — borrow rate at protocol                               |
| `STAKE`        | `PROTOCOL_RATE`     | Fill at LST staking APR at bar time                                  |
| `UNSTAKE`      | `PROTOCOL_RATE`     | Mirror of STAKE                                                      |
| `QUOTE`        | `ARRIVAL_MID`       | Reference price only — no fill; ARRIVAL_MID is the reference         |
| `TRANSFER`     | `ARRIVAL_MID`       | Asset value at transfer time; chain fee modelled separately          |
| `BRIDGE`       | `ARRIVAL_MID`       | Bridge output at mid; bridge slippage modelled as fixed bps          |
| `ATOMIC`       | `POOL_MID_AT_BLOCK` | Atomic on-chain bundle; AMM semantics                                |
| `CANCEL`       | `ARRIVAL_MID`       | No fill; cancellation uses arrival price for P&L accounting          |
| `CONVERT_DUST` | `POOL_MID_AT_BLOCK` | Dust conversion via AMM at block mid                                 |
| `LP_MINT`      | `POOL_MID_AT_BLOCK` | LP share minted at pool mid-price at block                           |
| `LP_BURN`      | `POOL_MID_AT_BLOCK` | LP share burned at pool mid-price at block                           |

The matching engine MUST respect `BenchmarkFillMode` under `BATCH` + always-fill mode. If a new action type is added to
`InstructionActionV2`, a corresponding `BenchmarkFillMode` entry is mandatory before that action can be dispatched in
batch.

---

## MatchingEngineConfig (UAC)

`MatchingEngineConfig` in `unified_api_contracts.internal.architecture_v2` (to be shipped with Phase 1.9) holds the
configurable matching assumptions:

```python
class MatchingEngineConfig(BaseModel):
    max_slippage_bps: int = 100          # AMM reject threshold
    l1_commission_bps: float = 0.5       # TradFi maker/taker per side
    l2_commission_bps: float = 2.0       # CeFi taker
    l0_commission_bps: float = 0.0       # Sports (margin in odds)
    amm_pool_fee_bps: int = 30           # Default Uniswap V3 0.3%
    l1_latency_ms: int = 50              # NautilusTrader L1 sim
    l2_latency_ms: int = 100             # NautilusTrader L2 sim
    always_fill: bool = True             # Batch mode: fill if slippage gated
```

All fields are configurable per-archetype via strategy-service config; defaults above reflect the standard 2026-05-23
backtest assumptions. Any deviation from defaults must be documented in the archetype's `StrategyConfig` with a
`matching_engine_config_override` field.

---

## Enforcement

GAP-16 (topology plan Phase 8) requires a pytest in strategy-service or execution-service asserting every
`InstructionActionV2` member maps to a non-default `BenchmarkFillMode`. This is the test gate for MAY-23 acceptance.

---

## Relationship to other codex docs

- **Strategy ensemble topology**: [`strategy-ensemble-topology.md`](strategy-ensemble-topology.md)
- **Batch-live architecture**: [`batch-live-architecture.md`](batch-live-architecture.md)
- **AMM slippage mathematics**: [`amm-slippage-simulation.md`](amm-slippage-simulation.md)
