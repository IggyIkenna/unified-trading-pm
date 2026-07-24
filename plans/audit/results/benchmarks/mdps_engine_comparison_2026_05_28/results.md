---
doc_type: audit-result
title: MDPS engine benchmark — results
summary:
  Baseline MDPS engine benchmark (9 BINANCE-FUTURES perp trades, 2026-04-15) comparing 4 read paths — pure_polars_lazy
  (A), pandas_pyarrow (B), current_mdps_mixed (C), polars_eager (D); A vs C = 0.34× wall and −2153 MB retention delta,
  retention ordering D < A < B < C.
status: pass
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [market-data-processing-service]
scope: [engineer, admin]
tags: [mdps, performance, polars, benchmark, data-pipeline, cefi, binance]
related:
  - /plans/audit/results/benchmarks/mdps_engine_comparison_2026_05_28/results_full_month_binance_2026_04.md
  - /plans/audit/results/benchmarks/mdps_engine_comparison_2026_05_28/results_synthetic_stage1_2026_05_28.md
created: 2026-05-28
audited_scope:
  9 BINANCE-FUTURES perpetual trades parquets for 2026-04-15, 4 read paths
  (pure_polars_lazy/pandas_pyarrow/current_mdps_mixed/polars_eager), subprocess-isolated
date: 2026-05-28
auditor: ComsicTrader
parent_epic: infrastructure_master
severity: P3
resulting_plan:
lib_version:
doc_versions_checked:
---

# MDPS engine benchmark — results

Versions (same across all paths): polars 1.40.1 pandas 3.0.3 pyarrow 24.0.0 python 3.13.9

Data: 9 BINANCE-FUTURES perp trades parquets for 2026-04-15. Each path processes ALL N instruments in a single Python
process, running each in its own subprocess to isolate cross-path arena retention.

## Aggregate per path

| Path | Label              | Total wall (s) | Mean wall/instr (s) | Mean peak RSS (MB) | Final RSS (MB) | Retention vs warmup (MB) |
| ---- | ------------------ | -------------- | ------------------- | ------------------ | -------------- | ------------------------ |
| A    | pure_polars_lazy   | 0.5            | 0.05                | 344                | 468            | 318                      |
| B    | pandas_pyarrow     | 2.6            | 0.28                | 1185               | 1838           | 1570                     |
| C    | current_mdps_mixed | 1.4            | 0.14                | 1861               | 2825           | 2471                     |
| D    | polars_eager       | 0.3            | 0.03                | 625                | 931            | 801                      |

## RSS trajectory across instruments (MB)

Each row shows the RSS measurement AFTER each instrument completes, post `gc.collect()`. Rising numbers = cumulative
arena retention.

| #   | Instrument | A (pure_polars_lazy) | B (pandas_pyarrow) | C (current_mdps_mixed) | D (polars_eager) |
| --- | ---------- | -------------------- | ------------------ | ---------------------- | ---------------- |
| 1   | ADAUSDT    | 177                  | 316                | 436                    | 175              |
| 2   | AVAXUSDT   | 188                  | 362                | 493                    | 215              |
| 3   | BNBUSDT    | 204                  | 474                | 717                    | 310              |
| 4   | BTCUSDT    | 330                  | 1083               | 1744                   | 602              |
| 5   | DOGEUSDT   | 331                  | 1145               | 1829                   | 606              |
| 6   | ETHUSDT    | 466                  | 1794               | 2961                   | 927              |
| 7   | LINKUSDT   | 466                  | 1797               | 2709                   | 927              |
| 8   | SOLUSDT    | 468                  | 1833               | 2779                   | 930              |
| 9   | XRPUSDT    | 468                  | 1838               | 2825                   | 931              |

## Per-instrument wall-clock (s) and peak RSS (MB)

### Path A — pure_polars_lazy

| Instrument | Size (MB) | Wall (s) | Peak RSS (MB) | RSS after (MB) |
| ---------- | --------- | -------- | ------------- | -------------- |
| ADAUSDT    | 4.2       | 0.03     | 177           | 177            |
| AVAXUSDT   | 3.6       | 0.02     | 188           | 188            |
| BNBUSDT    | 6.8       | 0.03     | 204           | 204            |
| BTCUSDT    | 30.3      | 0.09     | 330           | 330            |
| DOGEUSDT   | 9.3       | 0.03     | 331           | 331            |
| ETHUSDT    | 46.8      | 0.14     | 466           | 466            |
| LINKUSDT   | 2.9       | 0.02     | 466           | 466            |
| SOLUSDT    | 14.7      | 0.04     | 468           | 468            |
| XRPUSDT    | 9.3       | 0.03     | 468           | 468            |

### Path B — pandas_pyarrow

| Instrument | Size (MB) | Wall (s) | Peak RSS (MB) | RSS after (MB) |
| ---------- | --------- | -------- | ------------- | -------------- |
| ADAUSDT    | 4.2       | 0.10     | 316           | 316            |
| AVAXUSDT   | 3.6       | 0.09     | 362           | 362            |
| BNBUSDT    | 6.8       | 0.15     | 474           | 474            |
| BTCUSDT    | 30.3      | 0.58     | 1091          | 1083           |
| DOGEUSDT   | 9.3       | 0.16     | 1145          | 1145           |
| ETHUSDT    | 46.8      | 0.97     | 1812          | 1794           |
| LINKUSDT   | 2.9       | 0.07     | 1797          | 1797           |
| SOLUSDT    | 14.7      | 0.25     | 1833          | 1833           |
| XRPUSDT    | 9.3       | 0.15     | 1838          | 1838           |

### Path C — current_mdps_mixed

| Instrument | Size (MB) | Wall (s) | Peak RSS (MB) | RSS after (MB) |
| ---------- | --------- | -------- | ------------- | -------------- |
| ADAUSDT    | 4.2       | 0.05     | 436           | 436            |
| AVAXUSDT   | 3.6       | 0.04     | 493           | 493            |
| BNBUSDT    | 6.8       | 0.08     | 717           | 717            |
| BTCUSDT    | 30.3      | 0.29     | 1744          | 1744           |
| DOGEUSDT   | 9.3       | 0.08     | 1829          | 1829           |
| ETHUSDT    | 46.8      | 0.46     | 2961          | 2961           |
| LINKUSDT   | 2.9       | 0.05     | 2961          | 2709           |
| SOLUSDT    | 14.7      | 0.12     | 2779          | 2779           |
| XRPUSDT    | 9.3       | 0.09     | 2825          | 2825           |

### Path D — polars_eager

| Instrument | Size (MB) | Wall (s) | Peak RSS (MB) | RSS after (MB) |
| ---------- | --------- | -------- | ------------- | -------------- |
| ADAUSDT    | 4.2       | 0.02     | 175           | 175            |
| AVAXUSDT   | 3.6       | 0.02     | 215           | 215            |
| BNBUSDT    | 6.8       | 0.02     | 310           | 310            |
| BTCUSDT    | 30.3      | 0.06     | 602           | 602            |
| DOGEUSDT   | 9.3       | 0.02     | 606           | 606            |
| ETHUSDT    | 46.8      | 0.08     | 927           | 927            |
| LINKUSDT   | 2.9       | 0.01     | 927           | 927            |
| SOLUSDT    | 14.7      | 0.02     | 930           | 930            |
| XRPUSDT    | 9.3       | 0.01     | 931           | 931            |

## Headline comparison

- **A pure-polars-lazy** vs **C current-mdps-mixed**: 0.34× wall, -2153 MB retention delta
- **B pandas-pyarrow** vs **C current-mdps-mixed**: 1.89× wall, -901 MB retention delta
- **D polars-eager** vs **C current-mdps-mixed**: 0.22× wall, -1670 MB retention delta
- **A pure-polars-lazy** vs **B pandas-pyarrow**: 0.18× wall, -1251 MB retention delta
