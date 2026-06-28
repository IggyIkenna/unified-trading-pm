---
doc_type: plan
title: Execution fidelity tiers — UAC governs high/low-fidelity matching by available data
summary:
  "Make UAC declare, per instrument and per mode (live/batch), which execution matching fidelity is possible given the
  data we actually have — L2-tick / candle+book-columns / OHLC-bar — and have execution-service select the path
  accordingly, keeping the e2e 1m-candle determinism spine green."
status: draft
nature: design
asset_group: [cross-cutting]
stage: [execution, backtest]
repos: [execution-service, unified-api-contracts]
scope: [engineer, admin]
tags: [execution, matching, fidelity, uac, l2-mbp, l1-mbp, candle-matching, book-columns, capability]
related:
  [
    ./mdps_features_reduced_artifact_tracker_2026_06_28.md,
    ./mdps_book_microstructure_precompute_columns_2026_06_28.md,
    ./mvp_for_mdps_and_features_universe_uac_2026_06_28.md,
    ../epics/execution_master.md,
  ]
created: 2026-06-28
parent_epic: execution_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: design
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 2.4
assigned_role: backend-engineer
model_tier: opus-required
thinking_tier: high
drift_direction: advance-code
last_updated: 2026-06-28
locked_by: NA
locked_since:
supersedes:
superseded_by:
depends_on: [mdps_book_microstructure_precompute_columns_2026_06_28, mvp_for_mdps_and_features_universe_uac_2026_06_28]
gate_on_depends: true
source: [operator request 2026-06-28]
---

# Execution fidelity tiers — UAC-governed

Matching is on tick or on candle depending on what granularity we have. Today `book_type.py` hard-maps
L1*MBP→TradFi-bars, L2_MBP→CeFi-ticks, etc. With the candle becoming the portable artifact (and carrying book-summary
columns from Plan 1), there's a **middle tier**: matching off a candle that \_also* carries intra-bar book stats —
better than pure OHLC, short of a full L2 book walk. This plan makes UAC the SSOT for **what fidelity is possible** per
instrument and per mode (live vs batch), and has execution select the path — so strategies can choose high- or
low-fidelity execution knowing what the data supports.

**Execution model:** Opus / thinking high — a contract spanning UAC capability + the execution matching engine; needs
both reasoned together.

**Prereqs:** Plan 1 (candle book columns define the middle tier) + Plan 3 (UAC universe is where capability lives).

## The three fidelity tiers

| Tier                       | Data required                        | Matching                                              | Where available                            |
| -------------------------- | ------------------------------------ | ----------------------------------------------------- | ------------------------------------------ |
| **L2-tick (high)**         | trades + book_snapshot_5 ticks       | full book walk (L2_MBP)                               | GCP, CeFi/prediction, where ticks exist    |
| **candle+book-cols (mid)** | candle with intra-bar book summaries | fill at time-weighted spread, slippage off mean depth | anywhere the Plan-1 candle exists          |
| **OHLC-bar (low)**         | plain OHLCV candle                   | OHLC-endpoint / close fill (L1-style; e2e 1m spine)   | anywhere a candle exists (TradFi 1m, etc.) |

## Todos

- [ ] [DESIGN] P1. (opus) Define a UAC capability function `execution_fidelity(instrument, mode)` → {L2_TICK,
      CANDLE_BOOK_COLS, OHLC_BAR} based on what data_types the instrument actually has live and in batch
      (source-governed, e.g. TradFi 1m → OHLC_BAR only). — Gate: reviewed signature + decision table; returns the
      correct tier for a CeFi-with-ticks vs TradFi-1m vs candle-only instrument.
- [ ] [IMPLEMENT] P1. Add the **candle+book-cols matcher** to execution-service: a fill model that uses the Plan-1
      intra-bar book columns (time-weighted spread for fill price, mean depth for slippage/partial-fill). Slot it
      between L1_MBP OHLC and L2_MBP in the matching-engine selection. — Gate: the matcher fills a known order against a
      candle carrying book columns and produces a deterministic, documented fill.
- [ ] [IMPLEMENT] P1. Wire execution path selection to read `execution_fidelity(...)` instead of the hard-coded
      book_type→domain map; a strategy may request a max tier and execution clamps to what the data supports. — Gate:
      selection chooses L2 where ticks exist, candle+book-cols where only the Plan-1 candle exists, OHLC-bar for TradFi
      1m; unit tests per tier.
- [ ] [TEST] P1. Keep the determinism spine green: the e2e-testing 1m-candle `test_live_persist_determinism` (paper(W)
      == batch-rerun(W), ε=0) still passes; add a tier-selection test + a candle+book-cols fill regression. — Gate: e2e
      determinism test green; new tests green.
- [ ] [AGENT] P1. execution-service + UAC QG green; quickmerge `--agent --files`. — Gate: QG green; CI
      `quality-gates-v2` green.

## Current-state delta (audited 2026-06-28)

- **Today:** `execution_service/utils/book_type.py` hard-maps `should_use_bar_data` / `get_data_type_for_loading`
  (L1_MBP→TradFi tbbo+trades / bar_mode; L2_MBP→CeFi trades+book; AMM→DeFi); `matching_engine/engine.py` carries L0_TOB
  / L1_MBP / L2_MBP / AMM matchers; `matching_engine/trade_matcher.py` passive/aggressive fills; e2e
  `test_live_persist_determinism` is the 1m-candle ε=0 spine.
- **Delta:** a UAC `execution_fidelity(instrument, mode)` capability + a NEW candle+book-cols matcher (consumes Plan 1
  columns) slotted between L1 OHLC and L2 tick; path selection reads the capability instead of the hardcoded map; the
  most-liquid-SPOT selector from Plan 3 feeds spot-leg execution.

## Notes

- This formalises the "lossy-by-design" caveat from Plan 1 as a first-class tier rather than a silent limitation: exact
  L2 matching needs ticks (GCP-side); the portable candle gets the mid tier.
- Does NOT change live trading behaviour or arm anything — backtest/paper matching fidelity + the capability contract
  only. Live execution path changes, if any, are a separate plan under execution_master.
