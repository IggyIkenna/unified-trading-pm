---
doc_type: audit-result
title: MDPS engine benchmark — full month April 2026 — Path A vs Path C
summary: >-
  Full-month (April 2026, 30 days × 9 BINANCE-FUTURES perp) MDPS engine benchmark Path A (pure_polars_lazy) vs Path C
  (current_mdps_mixed) — confirms audited targets hold at scale: 10.35× wall (target 3×), 6.11× peak RSS (target 5×),
  8.88× retention (target 7.8×); all three PASS above floor.
status: pass
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [market-data-processing-service]
scope: [engineer, admin]
tags: [mdps, performance, polars, benchmark, data-pipeline, cefi, binance, verification]
related:
  - /plans/audit/results/benchmarks/mdps_engine_comparison_2026_05_28/results.md
  - /plans/audit/results/benchmarks/mdps_engine_comparison_2026_05_28/results_synthetic_stage1_2026_05_28.md
  - ../mdps_plan7_benchmark_report_2026_06_29.md
created: 2026-06-29
audited_scope:
  April 2026 (30 days) × 9 BINANCE-FUTURES perpetual trades, Path A (pure_polars_lazy) vs Path C (current_mdps_mixed),
  per-day + month-aggregate wall/RSS/retention
date: 2026-06-29
auditor: ikennaigboaka
parent_epic: cefi_master
severity: P3
resulting_plan:
lib_version:
doc_versions_checked:
---

# MDPS engine benchmark — full month April 2026 — Path A vs Path C

**Context:** validates that the audited 3× wall / 5× peak RSS / 7.8× retention improvements hold at full-month scale (30
days × 9 BINANCE-FUTURES perp trades).

Paths compared:

- **A** `pure_polars_lazy` — `scan_parquet` LazyFrame + `group_by` + `write_parquet`
- **C** `current_mdps_mixed` — Polars read → `.to_pandas()` → `from_pandas()` → aggregate → write

Venue / instruments: BINANCE-FUTURES / ADAUSDT AVAXUSDT BNBUSDT BTCUSDT DOGEUSDT ETHUSDT LINKUSDT SOLUSDT XRPUSDT Month:
April 2026 (2026-04-01 → 2026-04-30, 30 days)

Library versions: polars 1.38.1 · pandas 2.3.3 · pyarrow 23.0.1 · python 3.13.13

## Per-day results: Path A vs Path C

| Date       | A wall (s) | C wall (s) | wall ratio (C/A) | A peak RSS (MB) | C peak RSS (MB) | peak ratio (C/A) | A ret (MB) | C ret (MB) | ret ratio (C/A) |
| ---------- | ---------- | ---------- | ---------------- | --------------- | --------------- | ---------------- | ---------- | ---------- | --------------- |
| 2026-04-01 | 0.54       | 6.28       | 11.67×           | 321             | 2160            | 6.73×            | 286        | 2727       | 9.52×           |
| 2026-04-02 | 0.58       | 6.90       | 11.84×           | 350             | 2276            | 6.51×            | 342        | 2908       | 8.51×           |
| 2026-04-03 | 0.49       | 3.52       | 7.17×            | 238             | 1279            | 5.38×            | 174        | 1383       | 7.93×           |
| 2026-04-04 | 0.34       | 2.22       | 6.57×            | 182             | 892             | 4.89×            | 92         | 977        | 10.66×          |
| 2026-04-05 | 0.42       | 3.74       | 8.88×            | 240             | 1348            | 5.62×            | 192        | 1681       | 8.76×           |
| 2026-04-06 | 0.55       | 6.22       | 11.31×           | 337             | 2165            | 6.43×            | 323        | 2701       | 8.36×           |
| 2026-04-07 | 0.70       | 8.28       | 11.87×           | 410             | 2712            | 6.61×            | 441        | 3604       | 8.18×           |
| 2026-04-08 | 0.57       | 6.52       | 11.46×           | 336             | 2217            | 6.59×            | 322        | 2845       | 8.84×           |
| 2026-04-09 | 0.56       | 6.02       | 10.66×           | 334             | 2016            | 6.04×            | 315        | 2513       | 7.97×           |
| 2026-04-10 | 0.47       | 4.98       | 10.65×           | 280             | 1779            | 6.37×            | 245        | 2207       | 9.02×           |
| 2026-04-11 | 0.41       | 3.55       | 8.57×            | 240             | 1372            | 5.70×            | 183        | 1738       | 9.48×           |
| 2026-04-12 | 0.45       | 4.67       | 10.36×           | 274             | 1684            | 6.15×            | 228        | 2029       | 8.89×           |
| 2026-04-13 | 0.61       | 6.81       | 11.07×           | 371             | 2419            | 6.52×            | 392        | 3246       | 8.28×           |
| 2026-04-14 | 0.59       | 6.77       | 11.44×           | 355             | 2284            | 6.44×            | 367        | 3094       | 8.44×           |
| 2026-04-15 | 0.49       | 5.21       | 10.62×           | 295             | 1920            | 6.51×            | 267        | 2477       | 9.28×           |
| 2026-04-16 | 0.65       | 6.57       | 10.16×           | 329             | 2199            | 6.69×            | 280        | 2734       | 9.78×           |
| 2026-04-17 | 0.60       | 7.48       | 12.50×           | 364             | 2474            | 6.80×            | 356        | 3148       | 8.83×           |
| 2026-04-18 | 0.43       | 4.19       | 9.80×            | 246             | 1549            | 6.29×            | 178        | 1840       | 10.32×          |
| 2026-04-19 | 0.48       | 5.37       | 11.08×           | 292             | 1858            | 6.36×            | 256        | 2313       | 9.03×           |
| 2026-04-20 | 0.52       | 5.97       | 11.40×           | 323             | 2149            | 6.65×            | 306        | 2734       | 8.94×           |
| 2026-04-21 | 0.51       | 5.66       | 11.07×           | 321             | 2060            | 6.42×            | 299        | 2611       | 8.74×           |
| 2026-04-22 | 0.54       | 6.31       | 11.64×           | 337             | 2198            | 6.51×            | 332        | 2824       | 8.49×           |
| 2026-04-23 | 0.54       | 5.95       | 10.91×           | 328             | 2061            | 6.29×            | 315        | 2579       | 8.20×           |
| 2026-04-24 | 0.43       | 4.19       | 9.66×            | 248             | 1483            | 5.98×            | 196        | 1770       | 9.02×           |
| 2026-04-25 | 0.32       | 2.05       | 6.34×            | 172             | 811             | 4.73×            | 70         | 774        | 11.00×          |
| 2026-04-26 | 0.41       | 3.00       | 7.40×            | 213             | 1101            | 5.17×            | 132        | 1278       | 9.69×           |
| 2026-04-27 | 0.50       | 5.20       | 10.49×           | 290             | 1792            | 6.18×            | 248        | 2155       | 8.67×           |
| 2026-04-28 | 0.54       | 3.85       | 7.19×            | 277             | 1368            | 4.95×            | 243        | 1675       | 6.88×           |
| 2026-04-29 | 0.57       | 6.37       | 11.18×           | 317             | 1983            | 6.25×            | 298        | 2454       | 8.23×           |
| 2026-04-30 | 0.45       | 4.23       | 9.49×            | 252             | 1414            | 5.60×            | 207        | 1729       | 8.37×           |

## Month-level aggregate

| Metric                        | Path A | Path C | Ratio (C/A) | Audited target |
| ----------------------------- | ------ | ------ | ----------- | -------------- |
| Total wall time (s)           | 15.3   | 158.1  | 10.35×      | 3×             |
| Mean peak RSS/instrument (MB) | 296    | 1834   | 6.11×       | 5×             |
| Mean daily retention (MB)     | 263    | 2292   | 8.88×       | 7.8×           |
| Sum daily retention (MB)      | 7886   | 68749  | 8.72×       | —              |

## Verdict

- **Wall-time speedup**: 10.15× mean daily C/A ratio → ✅ above 2.5× floor (audited 3×)
- **Peak RSS reduction**: 6.11× mean daily C/A ratio → ✅ above 4× floor (audited 5×)
- **Retention reduction**: 8.88× mean daily C/A ratio → ✅ above 6× floor (audited 7.8×)

The full-month run confirms the engine benchmark ratios at real Binance data scale. Combined with the
subprocess-per-date isolation (shipped as item 2), the full 30-day production workload benefits from BOTH the per-day
efficiency gain AND the daily arena-reset from process exit.
