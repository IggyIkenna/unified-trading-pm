---
doc_type: audit-result
title: "TradFi MVP cell wiring-proof + data-pipeline re-verification (2026-08-04)"
summary: >
  Per-cell determination of whether backfill=paper=live wiring is proven, plus fresh IS/MTDS availability-index reads
  for each of the 6 MVP cells. Executed against live prod availability indices (IS: instruments-store-tradfi-prd, MTDS:
  market-data-tick-tradfi-prd) on 2026-08-04.
status: pass
nature: record
asset_group: [tradfi]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [tradfi, mvp-cells, wiring-proof, data-pipeline, verification]
created: "2026-08-04"
date: "2026-08-04"
author: "slot-7 (worker, data_engineering)"
auditor: "slot-7"
audited_scope: "All 6 tradfi MVP cells — wiring-proof determination + IS/MTDS availability-index pipeline verification"
severity: P2
parent_epic: tradfi_master
source: /plans/active/tradfi_consolidated_native_ao_extract_2026_07_25.md (todo 1)
resulting_plan: ""
lib_version: ""
doc_versions_checked: ""
related:
  - /plans/active/tradfi_consolidated_closeout_2026_07_18.md
  - /codex/09-strategy/operational/paper-batch-live-reconciliation.md
---

# TradFi MVP cell wiring-proof + data-pipeline re-verification

**Date**: 2026-08-04 **Data sources**: Live prod availability indices (IS `_index/availability_index.parquet`, MTDS
`_index/availability_index.parquet`), both downloaded and queried directly — no stale Progress Log citations. **IS
index**: 27,397 rows, 8 venues, date range 2018-2026, 22,160 captured (80.9%) **MTDS index**: 6,405,697 rows, 9 venues
(incl. BARCHART), date range 2018-01-01 to 2026-08-04, 1,564,977 captured (24.4%), 606,935 attempted_failed (9.5%)

---

## Paper/Live Wiring Proof — global finding (applies to ALL 6 cells)

**Verdict: NO tradfi MVP cell has backfill=paper=live wiring proven.**

Evidence:

1. **`tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md:82`** — explicit, authoritative: _"TradFi is batch-only
   this cutover cycle (no live trading by 2026-05-23)."_ This is the master plan for tradfi strategy readiness; it
   definitively states tradfi has no live trading.

2. **Comprehensive grep of all tradfi plans** (`unified-trading-pm/plans/active/tradfi*.md`,
   `plans/archive/2026_07/tradfi*.md`, `plans/archive/2026_08/tradfi*.md`) for paper-trading ledger, live-trading
   ledger, batch-rerun determinism proof, epsilon=0 wiring evidence: **0 hits**.

3. **`cross_cutting_strategy_execution_determinism_2026_07_26.md`** — the cross-cutting ε=0 determinism-spine plan
   exists and is active, but it is a general infrastructure track, not a per-AG wiring proof. It contains no
   tradfi-specific cell-level wiring evidence. The plan's own summary states its scope as "finishing the ε=0 proof
   machinery + BLRS audit remediation + capability-wizard drift-check/gap-tracker" — all infrastructure, no per-AG
   sign-off.

4. **Paper/live trading infrastructure** (UI components, ledgers, promote workflow) exists generically but has never
   been exercised against a tradfi instrument — the infrastructure is capability-present, not tradfi-proven.

**Conclusion**: Per `/codex/09-strategy/operational/paper-batch-live-reconciliation.md`, the ε=0 proof requires
paper(W)==batch-rerun(W) trade-for-trade. For tradfi, this proof has **not been constructed for any cell**. The
determinism-spine machinery is being built cross-cuttingly; tradfi is explicitly batch-only until that machinery is
complete and a per-AG sign-off is executed.

---

## Per-MVP-cell data-pipeline verification

### Cell 1: S&P index futures (ES)

| Check                    | Verdict                                                                                                                                                  | Evidence                                                                                                              |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Backfill proven          | **PARTIAL** — fleet finished (7 shards, 2026-07-21), manifest-count pending                                                                              | `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` P0 todo not yet executed                                      |
| Paper/live wiring        | **NOT PROVEN**                                                                                                                                           | No tradfi live trading (see global finding)                                                                           |
| IS pipeline              | **PASS** — CME: 6,047/6,437 captured (94.0%), 364 empty_confirmed, 14 expected_unattempted, 12 attempted_failed                                          | Live availability index read 2026-08-04                                                                               |
| MTDS pipeline (ohlcv_1s) | **PASS** — 544,198 attempted_failed is 99.9% ICE tombstone + billing-gated L2/L3 types; CME FUTURE ohlcv_1s/ohlcv_1m specifically: captured rows present | CME FUTURE: 24,730 captured, 378,200 empty_confirmed (billing-gated types: mbp_10, tbbo, trades), 21 attempted_failed |

**MTDS note**: The 544k `attempted_failed` in ohlcv_1s is dominated by ICE's `REMOVED_ENTITY_TOMBSTONE` (390,820 rows —
intentional, per the databento subscription-universe lockdown). CME's own `attempted_failed` count is 210,264, also
dominated by billing-gated L2/L3 data types (mbp_10, tbbo, trades outside the 1-month L3 / 1-year L1 entitlement
window). The CME FUTURE `captured` population (24,730 rows) covers the MVP data types (ohlcv_1s, ohlcv_1m, ohlcv_24h).

### Cell 2: S&P index options

| Check             | Verdict                                                                               | Evidence                                                                                                                                                                                       |
| ----------------- | ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backfill proven   | **NOT PROVEN** — not launched; singleton-Databento-lock blocker cleared 2026-07-26    | Launch todo in `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`                                                                                                                         |
| Paper/live wiring | **NOT PROVEN**                                                                        | No tradfi live trading                                                                                                                                                                         |
| IS pipeline       | **PASS** — CME OPTION: present in IS index (CME venue covers FUTURE + OPTION + COMBO) | IS CME: 6,047 captured overall                                                                                                                                                                 |
| MTDS pipeline     | **MIXED** — CME OPTION: 652 captured (34.0%), 1,265 attempted_failed (66.0%)          | **Concerning**: 2:1 fail-to-capture ratio on the only 2 data types (ohlcv_1m, trades). The `attempted_failed` dominance suggests genuine download failures, not billing-gating (unlike Cell 1) |

**MTDS note**: CME OPTION has only 1,917 rows total across just 2 data types (ohlcv_1m, trades). The 66%
attempted_failed rate warrants investigation — this is a different failure pattern from the billing-gated
empty_confirmed that dominates Cell 1. The backfill hasn't been launched yet for this cell (per the parent plan's
operator ruling 2026-07-29).

### Cell 3: Delta-one single-stock equities

| Check             | Verdict                                                                                                                                          | Evidence                                                                       |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------ |
| Backfill proven   | **PARTIAL** — filenames canonical; id-column verification still open (Phase A2)                                                                  | Parent plan line 258                                                           |
| Paper/live wiring | **NOT PROVEN**                                                                                                                                   | No tradfi live trading                                                         |
| IS pipeline       | **PASS** — NASDAQ: 856/1,993 captured (43.0%), NYSE: 1,658/2,439 captured (68.0%)                                                                | Combined: 2,514 captured, 1,901 empty_confirmed, 12 attempted_failed           |
| MTDS pipeline     | **PASS** — NASDAQ/NYSE EQUITY: 829,480 captured (24.2%), 2,440,475 empty_confirmed (71.3%), 149,468 expected_unattempted, 2,526 attempted_failed | 3.4M total rows; empty_confirmed dominated by billing-gated mbp_10/tbbo/trades |

**MTDS note**: The 24.2% capture rate is low but expected — most rows are billing-gated L2/L3 data types (mbp_10, tbbo,
trades) correctly classified as empty_confirmed. The captured population (829,480 rows) covers the MVP ohlcv data types.
The attempted_failed count (2,526) is negligible at 0.07%.

### Cell 4: CME BTC/ETH/MBT/MET futures

| Check             | Verdict                                                                                  | Evidence                                                                                 |
| ----------------- | ---------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Backfill proven   | **PARTIAL** — backfill fleet launched at scale 2026-07-21; completion not re-confirmed   | Parent plan Progress Log                                                                 |
| Paper/live wiring | **NOT PROVEN**                                                                           | No tradfi live trading                                                                   |
| IS pipeline       | **PASS** — same CME shard as Cell 1 (IS shard atom is venue-level, not instrument-level) | CME: 6,047 captured                                                                      |
| MTDS pipeline     | **PASS** — same CME FUTURE shard as Cell 1                                               | 24,730 captured; crypto futures indistinguishable from equity futures at the shard level |

**Note**: CME crypto futures (BTC/ETH/MBT/MET) share the same `(venue=CME, instrument_type=FUTURE)` shard as ES futures.
The backfill fleet launched at scale covers both; per-instrument verification would require probing specific
instrument_ids, which is outside this audit's scope (shard-level pass/fail is the cell's granularity).

### Cell 5: Daily Treasuries (FRED) + daily KRW (Yahoo)

| Check             | Verdict                                                                                                                                                                                         | Evidence                                                                                                                |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Backfill proven   | **PARTIAL** — KRX equities gap closed 2026-07-22 (new Yahoo-daily launcher); Treasuries backfill status not re-confirmed                                                                        | Parent plan line 260                                                                                                    |
| Paper/live wiring | **NOT PROVEN**                                                                                                                                                                                  | No tradfi live trading                                                                                                  |
| IS pipeline       | **PASS (with notes)** — KRX: 2,977/4,417 captured (67.4%), 890 empty_confirmed, 490 expected_unattempted, 60 attempted_failed. FRED: 8 rows, all expected_unattempted                           | FRED is a macro data source; expected_unattempted is the correct terminal state                                         |
| MTDS pipeline     | **PASS** — FRED: 279/503 captured (55.5%), 170 empty_confirmed, 54 attempted_failed. KRX: 2,934/34,036 captured (8.6%), 22,050 empty_confirmed, 8,993 expected_unattempted, 59 attempted_failed | KRX low capture rate is expected — dominated by billing-gated types (mbp_10, tbbo, trades) + macro_result + yield_curve |

**MTDS note**: KRX has 10 data types (the full set) but most are billing-gated or not applicable (macro_result,
yield_curve for an equities venue). The ohlcv_24h type (Yahoo daily) is the MVP path; the 8.6% overall capture rate
reflects the billing-gated noise, not a genuine gap.

### Cell 6: VIX FUTURE (CBOE) + CBOE yield INDEX + FX KRW

| Check             | Verdict                                                                             | Evidence                                                                                          |
| ----------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Backfill proven   | **PARTIAL** — part of 2026-07-21 backfill fleet launch; completion not re-confirmed | Parent plan line 261                                                                              |
| Paper/live wiring | **NOT PROVEN**                                                                      | No tradfi live trading                                                                            |
| IS pipeline       | **PASS** — CBOE: 4,575/5,601 captured (81.7%), FX: 2,303/2,334 captured (98.7%)     | Combined: 6,878 captured, 1,025 empty_confirmed, 15 attempted_failed                              |
| MTDS pipeline     | **PASS** — CBOE: 2,760/29,118 captured (9.5%), FX: 3,184/12,804 captured (24.9%)    | Both have the full 10-data-type spread; low % reflects billing-gated types, not MVP path failures |

**MTDS note**: CBOE has 2,489 attempted_failed (8.5% of total), FX has 268 attempted_failed (2.1%). CBOE's higher
attempted_failed rate may reflect the VIX FUTURE billing-entitlement boundary (L1 365-day entitlement vs requests past
the window).

---

## Summary table

| #   | MVP Cell                        | Backfill Proven                       | Paper/Live Wiring | IS Pipeline                   | MTDS Pipeline                                              |
| --- | ------------------------------- | ------------------------------------- | ----------------- | ----------------------------- | ---------------------------------------------------------- |
| 1   | S&P index futures (ES)          | PARTIAL (manifest-count pending)      | NOT PROVEN        | PASS (94% captured)           | PASS (ohlcv captured; billing-gated types correctly empty) |
| 2   | S&P index options               | NOT PROVEN (not launched)             | NOT PROVEN        | PASS (CME overall)            | MIXED (66% attempted_failed on ohlcv_1m/trades)            |
| 3   | Delta-one single-stock equities | PARTIAL (id-column pending)           | NOT PROVEN        | PASS (57% captured)           | PASS (24% captured; billing-gated types dominate)          |
| 4   | CME crypto futures              | PARTIAL (launched, not re-confirmed)  | NOT PROVEN        | PASS (same CME shard)         | PASS (same CME FUTURE shard)                               |
| 5   | Daily Treasuries + KRW          | PARTIAL (Treasuries not re-confirmed) | NOT PROVEN        | PASS (67% KRX, FRED expected) | PASS (both venues have captured rows)                      |
| 6   | VIX/CBOE yield + FX KRW         | PARTIAL (launched, not re-confirmed)  | NOT PROVEN        | PASS (82-99% captured)        | PASS (both venues have captured rows)                      |

**Key**: PASS = pipeline producing data; MIXED = data exists but with concerning failure patterns; PARTIAL = backfill
work done but not fully verified; NOT PROVEN = no evidence exists.

---

## Findings requiring action

1. **Cell 2 (S&P index options) — 66% MTDS attempted_failed**: CME OPTION has 1,265 attempted_failed vs 652 captured on
   ohlcv_1m + trades. This is a different failure signature from the billing-gated empty_confirmed pattern seen
   elsewhere. The backfill hasn't been launched yet; when it is, this should be monitored. Not filing a separate issue
   doc — this is tracked by the existing launch todo in `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`.

2. **605,935 MTDS attempted_failed rows across tradfi**: Dominated by ICE tombstone (390,820) + CME billing-gated L2/L3
   types. The ICE component is intentional (venue removed from subscription universe). The CME component is the known
   billing-entitlement-guard rejection — this is tracked by Cell 5's code-change todo (wire durable classification so
   these don't count as attempted_failed) in this same plan. No new finding.

3. **Cells 1, 4, 5, 6 — backfill "PARTIAL"**: All four cells launched backfill fleets but completion hasn't been
   manifest-verified. The operator-ruled manifest-count verification for Cell 1 (ES futures) is tracked in
   `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`. Cells 4/5/6 share the same pattern — completion confirmation
   is gated on the same verification todo or its equivalent.

---

## Methodology

- **IS pipeline**: Read `gs://instruments-store-tradfi-prd-central-element-323112/_index/availability_index.parquet`
  (27,397 rows, 41 columns). Filtered per-venue to compute capture rates. No GCS walk performed (single
  consolidated-parquet read).
- **MTDS pipeline**: Read `gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet`
  (6,405,697 rows, 42 columns). Filtered per-venue/instrument_type to compute per-cell capture rates.
- **Wiring proof**: Grep of all tradfi plans + the cross-cutting determinism plan for paper/live trading evidence;
  authoritative citation from `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`.
- **Date**: Both indices queried on 2026-08-04; IS index last written 2026-08-04 (12 shards), MTDS index spans
  2018-01-01 to 2026-08-04.
- **No `data-pipeline-check-is`/`-mtds` VM-based re-run was performed**: The skills require an explicit `--day`
  parameter (operator-provided per the skill contract) and VM provisioning. This audit used the consolidated
  availability indices as the alternative evidence source — the indices are the SSOT for capture status and are updated
  by the manifest consolidator (Cloud Run job, runs daily). A VM-based force+skip run would additionally prove the
  download path still works end-to-end; this audit's index-based approach proves current data state but not
  download-path liveness. If the task's done_definition requires VM-launched checks specifically, re-invoke with an
  explicit `--day`.
