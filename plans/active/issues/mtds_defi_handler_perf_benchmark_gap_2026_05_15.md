---
title: MTDS DeFi handler perf benchmark gap — 1k-event model N/A for HTTP-fetch handlers
created: 2026-05-15
author: harsh-slot-9
resolved: 2026-05-15
resolution: NO_ACTION_MAY23 — perf not on critical path; future harness design in Recommended §2
source:
  - harsh_orchestrator/pings/slot_9.md (new-queue item 4)
locked_by: live-defi-rollout
---

## What I found

The MTDS repo has a CeFi benchmark harness (`scripts/benchmark_tardis_stream.py`) that measures wall-time + peak RSS for
the Tardis streaming path (1k+ events, subprocess-isolated `ru_maxrss`). This harness is compute-bound and
event-volume-driven.

DeFi handlers (`lst_rates`, `evm_defi`, `gas_fee`, `solana_defi`, `eigenlayer_rewards`) are **network-bound 1-shot HTTP
fetchers** — they call protocol APIs once per batch window (Lido, Aave, Uniswap subgraph, etc.) and aggregate a handful
of rates per venue. The "wall-time per 1k events" model does not apply: these handlers process O(10) protocol data
points per run, not O(1000) streaming ticks.

## Why it matters

Item 4 of the slot-9 new queue asked for DeFi handler perf benchmarks. Per the queue directive: "skip if no perf harness
exists — file issue doc instead."

A perf harness _exists_ (for CeFi), but is structurally inapplicable to DeFi handlers. Building a DeFi-specific harness
would require mocking the HTTP layer + timing the aggregation logic, which is a design task not a test-fill task.

## Recommended decision

1. **No action needed for May-23 gate**: DeFi handler perf is network-limited by external API latency, not MTDS compute.
   Profiling compute overhead is not on the critical path.
2. **Future work**: If throughput becomes a concern (e.g. Solana Pyth price feed ingestion at high frequency), add a
   pytest-benchmark fixture that measures `_collect_*()` wall-time with mocked HTTP responses. Target:
   `tests/unit/test_defi_handler_benchmarks.py` + `@pytest.mark.benchmark` marks. Gate behind `--run-benchmarks` flag so
   QG stays fast.
3. **Existing harness**: `scripts/benchmark_tardis_stream.py` — covers CeFi only.
