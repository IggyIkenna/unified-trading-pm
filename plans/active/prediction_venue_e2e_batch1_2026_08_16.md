---
doc_type: plan
title: prediction venue e2e wiring batch 1 — 2026-08-16
summary: >-
  Fresh carve-out from venue_e2e_wiring_2026_08_16.md's "Fork per-asset-group dispatch batches" P0 todo — walks
  contract steps 1-9 across every prediction (venue, data_type) row from `unified-api-contracts/scripts/
  generate_venue_work_list.py` (4 rows, measured 2026-08-16; re-run the script, this count is not a constant).
  Not an extraction from another source doc — no operator-gated item mixed in, per task_template.md §3 finding Y.
status: active
nature: process
asset_group: [prediction]
stage: [data, features, strategy, execution]
repos:
  [
    unified-api-contracts,
    unified-trading-library,
    instruments-service,
    market-tick-data-service,
    features-service,
    strategy-service,
    execution-service,
  ]
scope: [engineer]
tags: [venue-readiness, e2e-wiring, prediction, ao-dispatch, satellite-batch]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
drift_direction: advance-code
depends_on: []
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
assigned_role: backend_engineer
effort: medium
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /codex/06-coding-standards/integration-testing-layers.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    unified-api-contracts/scripts/generate_venue_work_list.py,
  ]
source: >-
  Forked from `venue_e2e_wiring_2026_08_16.md`'s "Fork per-asset-group dispatch batches" P0 todo, 2026-08-16
  interactive session, per the operator-selected "per contract-step-group" decomposition.
---

# prediction venue e2e wiring batch 1 — 2026-08-16

> **Parent**: [`/plans/active/venue_e2e_wiring_2026_08_16.md`](/plans/active/venue_e2e_wiring_2026_08_16.md) (W4).
> The contract steps this plan walks, and the hard rules it must not violate, live in the parent — not restated here.
> Row list: `unified-api-contracts/scripts/generate_venue_work_list.py --csv PATH` filtered to
> `asset_group=prediction`.

## Todos

- [x] ✅ [BACKEND] P0. **Steps 1-5 per unit — done 2026-08-16.** SHIPPED — `unified-trading-pm@<pending-sha>`. Real
      per-row verdict, evidence cited, via 3 parallel research passes across instruments-service,
      market-tick-data-service, and features-service:
      | Row | Step 2 (instrument resolution) | Steps 3-4 (batch capture / live adapter) | Step 5 (feature consumption) |
      | --- | --- | --- | --- |
      | KALSHI, book_snapshot_5 | PASS — `KalshiReferenceDataAdapter`, coverage window `kalshi.py:1359-1360` | **PARTIAL — live only** (`KalshiClobWSFeedConnector`, `kalshi_clob_ws.py:354`); no batch collector found (`kalshi_adapter.py` has zero `book_snapshot_5` refs) | **FAIL** — `_ingest_prediction` (`batch_handler.py:167-176`) only lists `venue=POLYMARKET` parquets; KALSHI structurally excluded |
      | KALSHI, trades | PASS — same resolver | PASS — batch `kalshi_adapter.py:245`, live `kalshi_trades_ws.py:192` | **FAIL** — same structural KALSHI exclusion (`batch_handler.py:117-129`) |
      | POLYMARKET, book_snapshot_5 | PASS — `PolymarketReferenceDataAdapter`, coverage window `parsing.py:221-222` | PASS — batch `polymarket_adapter.py:347`, live `polymarket_clob_ws.py:306` | **FAIL** — `PolymarketMicrostructureCalculator.required_columns` is trades-only (`polymarket_microstructure_calculator.py:36-37`); book-consuming groups (`book_depth_bands`/`liquidity_walls`) are filtered out of PREDICTION entirely (`batch_handler.py:797-812`) |
      | POLYMARKET, trades | PASS — same resolver | PASS — batch `polymarket_adapter.py:476`, live `polymarket_trades_ws.py:149` | **PASS** — real, wired, enabled-by-default compute (`polymarket_microstructure_calculator.py:47-81`) |

      **Only 1 of 4 rows (POLYMARKET, trades) clears step 5.** Root cause is 2 real code gaps in
      `features-service`, tracked as their own todos below — NOT the archetype-declaration issue this doc originally
      (wrongly) assumed; that correction is recorded above. Never trust a stale "expect X" claim over live evidence.
- [ ] [BACKEND] P2. **Gap: KALSHI has a live book_snapshot_5 connector
      (`market_tick_data_service/live/connectors/kalshi_clob_ws.py:354`) but no batch/backfill collector** —
      `kalshi_adapter.py`'s `download_batch` is trades-only. Cannot backfill KALSHI order-book history; live-only
      capture means no historical replay/backtest for this data_type. Done-when: a batch collector exists (mirroring
      `PolymarketAdapter._build_book_snapshot_5_rows`, `polymarket_adapter.py:347`) or this is explicitly ruled
      out-of-scope with a cited reason.
- [ ] [BACKEND] P1. **Gap: `features-service`'s PREDICTION ingest path structurally excludes KALSHI entirely.**
      `_ingest_prediction`/`_list_polymarket_parquets` (`features_service/cross_instrument/cli/handlers/
      batch_handler.py:117-129,167-176`) hard-filter to `venue=POLYMARKET` — KALSHI trades and book_snapshot_5 are
      both real, captured (batch+live for trades; live-only for book), but orphaned at the feature layer regardless.
      Done-when: KALSHI is ingested alongside POLYMARKET for PREDICTION (or the exclusion is confirmed intentional
      with a cited reason — e.g. KALSHI's `polymarket_market_microstructure` fit is genuinely different and needs
      its own calculator, not a blind extension of the filter).
- [ ] [BACKEND] P1. **Gap: no feature_group consumes POLYMARKET book_snapshot_5.**
      `PolymarketMicrostructureCalculator` is trades-only (`polymarket_microstructure_calculator.py:36-37`), and
      the generically-applicable book-consuming groups (`book_depth_bands`/`liquidity_walls`/`order_flow_inference`/
      `microstructure`/`flow_interaction`) are all filtered out of PREDICTION by
      `_filter_feature_groups_for_asset_group` (`batch_handler.py:797-812`) — real captured book data (batch+live,
      confirmed PASS above) is fully orphaned. Done-when: at least one feature_group reads POLYMARKET
      book_snapshot_5, or the gap is confirmed intentional with a cited reason.
- [ ] [BACKEND] P0. **Steps 6-8 per unit — strategy and execution**, across the same 4 rows. **Gated by the step-5
      result above**: only (POLYMARKET, trades) has a real feature output to feed strategy today; the other 3 rows
      cannot meaningfully reach steps 6-8 until their respective gap todos above close. Scope this todo to
      (POLYMARKET, trades) first: does a position adapter resolve in batch/live/paper; is POLYMARKET declared in
      the archetype/slot catalogues for `MARKET_MAKING_CONTINUOUS`/`_INVENTORY_SKEW`/`_QUEUE_MICROSTRUCTURE`; does
      an execution adaptor handle every `InstructionActionV2` those archetypes emit. Done-when: a real per-step
      verdict for that one row, plus `BLOCKED-ON` markers for the other 3 citing the specific gap todo each depends
      on.
- [ ] [BACKEND] P0. **Step 9 per unit — transfers**, across the same 4 rows. Every applicable `BusTransferType`
      has a working rail, instruments-service through execution-service. Done-when: same per-row verdict discipline.
- [ ] [BACKEND] P1. **Record every NEW gap found while executing steps 6-9 above as its own tracked todo** in this
      file — never as prose only, same discipline the steps 1-5 sweep above already followed.
- [ ] [BACKEND] P0. **Confirm the parent plan's hard rules held across steps 1-3 above**: strategy-service never
      read MTDS directly; execution fails closed on granularity (`refuse_unservable`, never silently clamped);
      credentials gated RUNNING not BUILDING; no new service-to-service dependency was introduced. Done-when: a
      clean `quality-gates.sh` run across every repo touched by this batch.

## Progress Log

**2026-08-16 — Steps 1-5 swept, 2 real gaps found.** SHIPPED — `unified-trading-pm@<pending-sha>`. 3 parallel
research passes (instruments-service, market-tick-data-service, features-service) produced a real, cited per-row
verdict for all 4 rows. Step 2 (instrument resolution) passes for both venues on all 4 rows. Steps 3-4 (batch
capture / live adapter) pass for 3/4 rows; KALSHI book_snapshot_5 is live-only (no batch collector — tracked as a
P2 gap). Step 5 (feature consumption) passes for exactly 1/4 rows (POLYMARKET, trades) — the other 3 fail due to 2
structural gaps in features-service (KALSHI hard-excluded from the PREDICTION ingest path; no feature_group reads
POLYMARKET book data), both now tracked as P1 gap todos, not left as prose. Steps 6-8 rescoped to the 1 passing row
first, with the other 3 explicitly `BLOCKED-ON` their respective gap todo. Confirms the earlier archetype-count
correction was right to make: the real blocker for prediction was never archetype declaration, it was these 2 code
gaps — a different root cause than what this doc originally (wrongly) assumed.
