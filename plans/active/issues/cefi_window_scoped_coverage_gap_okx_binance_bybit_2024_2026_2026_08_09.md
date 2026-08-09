---
doc_type: issue
title: >-
  Window-scoped honest-coverage measurement (OKX/BINANCE/BYBIT, 2024-01-01→present) confirms coverage NOT complete —
  48.90% overall, and the trailing 90d is WORSE (24.70%) than the full-window average
summary: >-
  cefi_satellite_ao_dispatch_batch11 todo 10 ran the blocking-prerequisite window-scoped honest-coverage measurement the
  2-year ML_DIRECTIONAL_CONTINUOUS config-grid backtest (cefi_ml_directional_continuous_live_2026_06_20.md) needs before
  it can be scheduled. Result: 48.90% reachable coverage for OKX-SPOT/-SWAP/-FUTURES + BINANCE-SPOT/-FUTURES + BYBIT
  over 2024-01-01→present (2,980,916 scoped manifest rows) — materially below complete, confirming and quantifying the
  operator's 2026-08-08 "not confirmed" finding. The gap concentrates almost entirely in `trades` and `book_snapshot_5`
  (10.6%-46.3% coverage per venue) vs. `derivative_ticker`/`liquidations` (58%-97%) — exactly the two data_types the
  grid backtest needs for LOB/trade-level fidelity. Most concerning: the trailing ~90 days (>= 2026-05-11) measure WORSE
  than the full-window average (24.70% vs 48.90% overall; OKX-SPOT 12.21%, BINANCE-SPOT 13.13%, BYBIT 18.66%) —
  backwards from what a live-capital gate needs, and a signal this may be an ongoing live/near-real-time capture health
  problem for these venue+data_type combos, not just a historical-backfill gap that the unrelated from-2019
  chronological backfill (cefi_track2_coverage_backfill_checkpoints_2026_07_25.md, currently at ~10.7% through,
  last_completed_date=2019-10-21) will eventually fix by reaching 2024-2026. Also found: `futures_chain` shows 0%
  coverage for BINANCE-FUTURES (228 attempted_failed) and BYBIT (1251 attempted_failed) — every attempt failed, not an
  absence gap, suggesting a distinct correctness bug rather than a coverage gap.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [instruments-service, market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags:
  [
    cefi,
    honest-coverage,
    data-pipeline,
    backfill,
    trades,
    book_snapshot_5,
    futures_chain,
    live-capital-gate,
    okx,
    binance,
    bybit,
  ]
related:
  [
    /plans/active/cefi_ml_directional_continuous_live_2026_06_20.md,
    /plans/active/cefi_satellite_ao_dispatch_batch11_2026_08_09.md,
    /plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: "2026-08-09"
author: slot-5
priority: P1
parent_epic: cefi_master
source: >-
  Discovered 2026-08-09 executing cefi_satellite_ao_dispatch_batch11 todo 10 (window-scoped honest-coverage measurement,
  itself extracted from cefi_ml_directional_continuous_live_2026_06_20.md line 180). Measured by reusing
  instruments-service/scripts/measure_honest_coverage.py's bounded, column-pruned manifest reader (_read_manifest +
  _count_statuses) — a single read of the cefi availability-index parquet, filtered in-memory to the target venue set +
  date window; no new whole-corpus GCS walk.
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: fix
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
resolved_by:
locked_by:
depends_on: []
---

# Window-scoped cefi honest-coverage gap — OKX/BINANCE/BYBIT, 2024-2026

## What I found

Filtered the cefi availability-index manifest (10,537,552 total rows) to venue in {OKX-SPOT, OKX-SWAP, OKX-FUTURES,
BINANCE-SPOT, BINANCE-FUTURES, BYBIT} and date >= 2024-01-01 (2,980,916 scoped rows).

**Overall**: captured=1,295,524 / attempted_failed=94,706 / expected_unattempted=1,258,908 / empty_confirmed=331,778 →
**coverage_pct = 48.90%** (reachable formula: captured / (captured + attempted_failed + expected_unattempted)).

**Per venue**: OKX-FUTURES 80.51%, OKX-SWAP 64.18%, BINANCE-FUTURES 57.46%, BINANCE-SPOT 45.25%, BYBIT 35.99%,
**OKX-SPOT 29.34%** (worst).

**Per (venue, data_type)** — the gap is concentrated:

| venue           | data_type         | coverage_pct                                                                      |
| --------------- | ----------------- | --------------------------------------------------------------------------------- |
| BINANCE-FUTURES | trades            | 12.09%                                                                            |
| BYBIT           | trades            | 10.58%                                                                            |
| BYBIT           | book_snapshot_5   | 15.90%                                                                            |
| BINANCE-FUTURES | book_snapshot_5   | 24.75%                                                                            |
| OKX-SWAP        | trades            | 23.47%                                                                            |
| OKX-SWAP        | book_snapshot_5   | 25.26%                                                                            |
| OKX-SPOT        | trades            | 27.25%                                                                            |
| OKX-SPOT        | book_snapshot_5   | 31.35%                                                                            |
| BINANCE-SPOT    | book_snapshot_5   | 44.13%                                                                            |
| BINANCE-SPOT    | trades            | 46.33%                                                                            |
| OKX-FUTURES     | trades            | 45.60%                                                                            |
| BINANCE-FUTURES | futures_chain     | **0.00%** (228 attempted_failed, 0 expected_unattempted — every attempt failed)   |
| BYBIT           | futures_chain     | **0.00%** (1,251 attempted_failed, 0 expected_unattempted — every attempt failed) |
| —               | derivative_ticker | 58%-97% (healthy across all venues)                                               |
| —               | liquidations      | 59%-78% (healthy across all venues)                                               |

**Recency check** (trailing ~90d, date >= 2026-05-11) is WORSE than the full-window average: overall 24.70% (vs. 48.90%
full-window). Per venue: OKX-SPOT 12.21%, BINANCE-SPOT 13.13%, BYBIT 18.66%, OKX-SWAP 30.51%, BINANCE-FUTURES 38.71%,
OKX-FUTURES 48.47% — every single venue's most-recent-90d number is lower than its full-window number.

Full raw output (overall + per-venue + per-(venue,data_type) + recency breakdown) is in this same commit's Progress Log
entry on `/plans/active/cefi_ml_directional_continuous_live_2026_06_20.md` and
`/plans/active/cefi_satellite_ao_dispatch_batch11_2026_08_09.md` todo 10.

## Why it matters

1. **Blocks the P0 live-capital backtest-fidelity gate.** `cefi_ml_directional_continuous_live_2026_06_20.md`'s 2-year
   config-grid run cannot be scheduled until coverage for exactly this venue/window is confirmed complete (operator
   ruling, 2026-08-08). It is now confirmed — and confirmed incomplete, in exactly the two data_types (`trades` /
   `book_snapshot_5`) the LOB/trade-level backtest actually consumes.
2. **The recency regression is the more urgent signal.** A historical-backfill gap (data never captured back in
   2024/2025) is one failure mode; a WORSENING trend into the present (last-90d coverage lower than the 2-year average,
   in every single venue) is a different, more urgent one — it points at an ongoing live/near-real-time capture problem
   for `trades`/`book_snapshot_5` on these 6 venues, not just an unfinished historical backfill. If uninvestigated, the
   gap keeps growing every day rather than shrinking, and no from-2019 chronological backfill fixes an ongoing
   capture-side problem.
3. **`futures_chain` at exactly 0.00% with 100% attempted_failed** (not merely low, but every single attempt failing) on
   BINANCE-FUTURES and BYBIT is a distinct signature from a coverage gap — it reads as a broken adapter/endpoint/ auth
   path for that specific (venue, data_type), not "not yet captured."

## Recommended decision

Fix at the root per the data-pipeline-correctness HARD RULE (no deadline deferrals). Suggested split below; an operator
can re-prioritize P0 vs P1 if the live-capture investigation (item 1) surfaces something urgent enough to reorder.

## Action items

- [ ] [DATA] P0. **Investigate why trailing-90d `trades`/`book_snapshot_5` coverage for OKX-SPOT/-SWAP/-FUTURES,
      BINANCE-SPOT/-FUTURES, BYBIT is WORSE than the full 2024-2026 window average** (24.70% vs. 48.90% overall, every
      venue individually worse in the recent window than its own full-window number). Check whether the live/
      near-real-time capture cron/scheduler for these venue+data_type combos is degraded, under-scoped, or was recently
      changed — this is a distinct question from "was 2024/2025 ever backfilled." Repo: market-tick-data-service. **Done
      when**: root cause identified (live-capture config/cron issue vs. genuine venue-side outage vs. something else)
      and either fixed or filed as its own more specific issue if the fix is large.
- [ ] [DATA] P1. **Root-cause the 0.00% `futures_chain` coverage for BINANCE-FUTURES (228 attempted_failed) and BYBIT
      (1,251 attempted_failed)** — every attempt failed, 0 captured, 0 expected_unattempted. Check the adapter/endpoint
      for a broken auth path, changed API contract, or misrouted request. Repo: market-tick-data-service. **Done when**:
      root cause identified + fixed (or filed separately if genuinely large), and a sample re-attempt for each venue
      captures successfully.
- [ ] [DATA] P1. **Confirm whether `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`'s chronological
      2019→present backfill is actually scoped to close this `trades`/`book_snapshot_5` gap for these 6 venues once it
      reaches 2024-2026**, or whether it needs a targeted supplement for exactly this venue×data_type×window slice
      (don't rely on the from-2019 backfill reaching 2024 organically — per item 1 above, this may be a live-capture
      issue the historical backfill would never touch). Repo: instruments-service (read-only research + doc update).
      **Done when**: the cross-reference is confirmed one way or the other and recorded in that plan's Progress Log; if
      not covered, a targeted backfill todo is filed there (not duplicated here).
- [ ] [DATA] P2. **Backfill/re-attempt `trades` + `book_snapshot_5` for OKX-SPOT and BYBIT specifically** (the two
      worst-performing venues, 27-32% and 11-16% coverage respectively for these data_types) over 2024-01-01→present,
      once items 1 and 3 above determine whether this is a live-capture fix, a historical backfill, or both. Repos:
      deployment-service (VM launch), market-tick-data-service. **Done when**: a re-run of this same window-scoped
      measurement shows OKX-SPOT and BYBIT `trades`/`book_snapshot_5` coverage materially improved (cite the new %).

## Progress Log

- **2026-08-09** — filed from cefi_satellite_ao_dispatch_batch11 todo 10's window-scoped honest-coverage measurement. No
  fix applied yet — this is the findings-closure filing per RULES.md §4.5.
