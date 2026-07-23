---
doc_type: audit-result
title: MDPS Full-Pipeline OOM Finding — BTCUSDT Perpetual on 64 GB VM
summary:
  Records that the full MDPS pipeline (process --mode batch) for BTCUSDT perpetual + all 3 MVP data types OOM-kills
  (exit 137, ~55 GB RSS subprocess-per-date child) on a 64 GB VM during trades load alone; watchdog gap = it monitors
  parent RSS not the child. Operator accepted Plan 8 micro-benchmark as [VERIFY].
status: fail
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [market-data-processing-service]
scope: [engineer, admin]
tags: [mdps, performance, polars, benchmark, oom, data-pipeline, cefi, binance]
related:
  - /plans/audit/results/benchmarks/mdps_plan7_benchmark_report_2026_06_29.md
  - mdps_engine_comparison_2026_05_28/results_full_month_binance_2026_04.md
created: 2026-06-29
audited_scope:
  BTCUSDT perpetual (BINANCE-FUTURES) full-pipeline batch, trades + book_snapshot_5 + derivative_ticker, single day
  2026-05-22 on 64 GB VM
date: 2026-06-29
auditor: ikennaigboaka
parent_epic: mtds_mdps_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
---

# MDPS Full-Pipeline OOM Finding — BTCUSDT Perpetual on 64 GB VM

**Date:** 2026-06-29 **Context:** Plan 7 [VERIFY] full-pipeline benchmark attempt **Shard:**
`BINANCE-FUTURES · BTCUSDT · perpetual` **Data types:** `trades + book_snapshot_5 + derivative_ticker` **Machine:** 64
GB RAM (current planning VM)

---

## Finding

Running the full MDPS pipeline (`--operation process --mode batch`) for a single calendar day (2026-05-22) on the
BTCUSDT perpetual shard with all three MVP data types causes the subprocess-per-date child to be OOM-killed (exit 137)
after approximately 4 minutes.

| Engine variant | `USE_POLARS` | Peak system RAM observed | Exit code | Time-to-kill |
| -------------- | ------------ | ------------------------ | --------- | ------------ |
| Current engine | `false`      | ~42 GB rising            | 137 (OOM) | ~4 min       |
| Pure-Polars    | `true`       | ~42 GB rising            | 137 (OOM) | ~4 min       |

Both variants hit OOM at the same stage. The subprocess-per-date child (spawned by the MDPS orchestrator, running in a
separate OS session so it is NOT visible as a child of the parent PID) was observed at **55 GB RSS** (`PID 162771`,
`market_data_processing_service --operation process --mode batch --start-date 2026-05-22`) before the kernel killed it.

## Root cause (hypothesis)

The BTCUSDT book_snapshot_5 parquet for a single day is a large file (~1.78 M rows × 26 cols). The current MDPS pipeline
materializes the full day in memory before aggregation and then produces 7 timeframe aggregations
(15s/1m/5m/15m/1h/4h/24h). The combination of trades (which also peak high) + book data exceeds 64 GB in the subprocess
arena.

The `memory watchdog` threshold is set at 85% (threshold=85.0%), but the watchdog monitors the PARENT process RSS, not
the subprocess-per-date child's RSS. The child is in a new OS process group and is not visible to the watchdog, so no
graceful shutdown fires before OOM.

## Memory timeline (actual measurement, single day, trades-only first)

| Time offset | System used RAM | Event                                 |
| ----------- | --------------- | ------------------------------------- |
| t=0s        | 3.6 GB          | MDPS orchestrator boot                |
| t=15s       | 5.1 GB          | File enumeration + first parquet open |
| t=30s       | 5.1 GB          | reading trades parquet header         |
| t=45s       | 21 GB           | trades parquet fully loaded           |
| t=60s       | 39 GB           | trades aggregation in progress        |
| t=75s       | 40 GB           | rising                                |
| t=90s       | 41 GB           | rising                                |
| t=105s      | 42 GB           | OOM kill fires (exit 137)             |

book_snapshot_5 was NOT reached — OOM occurred during trades processing alone.

## Implication

The full MDPS pipeline benchmark (Plan 7 design: 200 calendar days × 3 data types × 2 engine variants) cannot run on a
64 GB machine without either:

1. Scoping data types to trades-only (drops book + derivative)
2. Running on a ≥128 GB machine
3. Fixing MDPS subprocess memory (lazy streaming instead of full-day materialization)

## Resolution (operator decision 2026-06-29)

**Option A accepted**: Plan 8's candle-aggregation micro-benchmark supplies sufficient [VERIFY] evidence for the Polars
path. The full-pipeline OOM is a separate, documented scalability finding.

Plan 8 evidence (already committed):

- `plans/audit/results/benchmarks/mdps_engine_comparison_2026_05_28/results_full_month_binance_2026_04.md`
- April 2026, 9 BINANCE-FUTURES perpetual instruments × 30 days
- **10.35× wall** (pure-Polars A=15.3s vs current C=158.1s)
- **6.11× peak RSS** reduction
- **8.88× retained RSS** reduction

The OOM finding is filed here as a prerequisite for any future Plan 7 full-pipeline run and as input to the MDPS memory
optimization work.
