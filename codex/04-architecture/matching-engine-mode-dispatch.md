---
scope: [engineer, admin]
title: Matching Engine — Mode Dispatch and Matcher Selection
updated: 2026-05-15
owner: topology_qgroup_gap_closure_2026_05_09 Phase 8
closes: GAP-14, GAP-15
last_reviewed: 2026-05-17
---

# Matching Engine Mode Dispatch

## Mode-to-Matcher Routing Rule

`OperationalMode` determines whether an instruction routes to the matching engine (simulation) or the live connector
(real exchange):

| `OperationalMode` | Routing                                  | Notes                                                 |
| ----------------- | ---------------------------------------- | ----------------------------------------------------- |
| `BATCH`           | Matching engine (always-fill simulation) | BenchmarkFillMode per `BENCHMARK_FILL_MODE_BY_ACTION` |
| `PAPER`           | Matching engine (always-fill simulation) | Same as BATCH; fills are virtual                      |
| `LIVE`            | Live venue connector                     | Real order submission via venue adapter               |
| `MANUAL`          | Live venue connector → manual queue      | Operator-approved orders only                         |

**Rule**: BATCH and PAPER never touch a real venue. LIVE and MANUAL never touch the matching engine for fills.

## Matcher Selection Matrix

The matching engine picks one of five `BaseMatcher` implementations based on the asset-domain and book-data shape of the
instruction:

| Matcher            | Book type                             | Asset domain                         | Commission                               | Slippage model                   |
| ------------------ | ------------------------------------- | ------------------------------------ | ---------------------------------------- | -------------------------------- |
| `L0Matcher`        | `L0_TOB` (best bid/ask only)          | Sports / Prediction (bookmaker odds) | 0 bps (bookmakers charge no commission)  | Odds movement only               |
| `L1Matcher`        | `L1_MBP` (trades with aggressor side) | TradFi (NautilusTrader-compatible)   | 0.5 bps default                          | Market impact via NautilusTrader |
| `L2Matcher`        | `L2_MBP` (order book depth, 5 levels) | CeFi (CEX spot/perp)                 | 2.0 bps taker                            | Slippage from depth walk         |
| `AMMMatcher`       | Pool state (x\*y=k or CLMM)           | DeFi (DEX swaps, LP mint/burn)       | AMM pool fee (e.g. 30 bps for 0.3% pool) | Price impact from pool size      |
| `BenchmarkMatcher` | N/A (benchmark price only)            | Alpha-zero / always-fill baseline    | 0 slippage                               | Fill at exact benchmark price    |

## BenchmarkFillMode per Action

`BENCHMARK_FILL_MODE_BY_ACTION` (UAC `unified_api_contracts.internal`) is the SSOT mapping every `InstructionActionV2`
to its `BenchmarkFillMode`:

| InstructionActionV2             | BenchmarkFillMode | Reference price source                                    |
| ------------------------------- | ----------------- | --------------------------------------------------------- |
| TRADE                           | ARRIVAL_MID       | Mid-price at instruction timestamp                        |
| SWAP                            | POOL_MID_AT_BLOCK | AMM pool mid at the block of execution                    |
| LEND / BORROW / STAKE / UNSTAKE | FUNDING_SNAPSHOT  | Protocol rate snapshot at instruction time                |
| QUOTE                           | PASSIVE_BBO       | Best bid or offer at passive side                         |
| TRANSFER                        | ARRIVAL_MID       | Mid-price at transfer timestamp (for notional accounting) |
| BRIDGE                          | POOL_MID_AT_BLOCK | Destination chain pool mid                                |
| ATOMIC                          | ARRIVAL_MID       | Mid-price at atomic bundle timestamp                      |
| CANCEL                          | PASSIVE_BBO       | BBO at cancel time (for slippage attribution)             |
| CONVERT_DUST                    | POOL_MID_AT_BLOCK | Pool mid for dust conversion                              |
| LP_MINT / LP_BURN               | POOL_MID_AT_BLOCK | Pool mid at block of LP position change                   |

## BATCH Mode Always-Fill Contract

In BATCH mode the matching engine MUST fill every instruction (no partial fills, no rejections). The `MatchingEngine` is
constructed with `always_fill=True`. This is the "Batch = Live, only fill source differs" invariant: strategy logic is
identical in BATCH and LIVE; the only difference is that BATCH fills use the benchmark price from
`BENCHMARK_FILL_MODE_BY_ACTION` while LIVE fills use real venue execution.

`BenchmarkMatcher` enforces this: every call returns a `MatchResult(filled=True, fill_price=benchmark_price)`.

## OperationalMode Dispatch (code location)

The mode-based fork lives at the execution-service instruction router:

- BATCH/PAPER → `engine/backtest/node_builder.py` `BATCH_FILL_ALGO_TYPES` gate → `BenchmarkMatcher`
- LIVE/MANUAL → `engine/live/` → venue adapter → real order

Transfer instructions follow the same fork via `engine/transfers/factory.py` `make_transfer_adapter()`.

## Test Coverage

`tests/unit/matching_engine/test_mode_dispatch.py` (GAP-14/15 acceptance):

- 5 × 2 matrix: each matcher (L0/L1/L2/AMM/Benchmark) × mode (BATCH vs LIVE) = 10 cells
- BATCH mode asserts matching engine called, live connector NOT called
- LIVE mode asserts live connector called, matching engine NOT called
- BenchmarkFillMode per action: asserts every `InstructionActionV2` value has a non-None entry in
  `BENCHMARK_FILL_MODE_BY_ACTION`
