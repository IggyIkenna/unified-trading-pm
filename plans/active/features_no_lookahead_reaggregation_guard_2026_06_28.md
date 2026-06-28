---
doc_type: plan
title: Features — no-look-ahead guard for candle re-aggregation
summary:
  "Audit + guard every place features re-aggregate or roll candles (resample 1m→5m→1h, rolling windows, PIT joins,
  forward-fill, multi-TF confluence) so the right-edge t_close convention holds and no future value leaks; add a gate
  script + regression tests."
status: active
nature: process
asset_group: [cross-cutting]
stage: [features]
repos: [features-service]
scope: [engineer, admin]
tags: [features, no-look-ahead, right-edge, t_close, leakage, resample, rolling, pit-join, guard]
related:
  [
    ./mdps_features_reduced_artifact_tracker_2026_06_28.md,
    ../active/bar_edge_left_vs_right_remediation_2026_06_08.md,
    ../epics/batch_live_symmetry_master.md,
  ]
created: 2026-06-28
parent_epic: batch_live_symmetry_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: design
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.8
assigned_role: data_engineering
drift_direction: advance-code
last_updated: 2026-06-28
locked_by: NA
locked_since:
supersedes:
superseded_by:
depends_on:
source: [operator request 2026-06-28, ../active/bar_edge_left_vs_right_remediation_2026_06_08.md]
---

# Features — no-look-ahead guard for re-aggregation

No-look-ahead is the heartbeat: a closed candle is stamped on its RIGHT edge (`t_close`). MDPS produces right-edge
candles and the features resampler is already fixed (`candle_resampler.resample_ohlcv` uses
`closed="right", label="right"`; cross-source edge fixture green per `bar_edge_left_vs_right_remediation_2026_06_08`).
This plan closes the **remaining** leakage surface — every other place features touch time — and makes it gate-enforced
so it can't regress.

**Execution model:** Sonnet — single-repo audit + guard from a clear invariant. Escalate to Opus only if the rolling/PIT
audit proves to need cross-repo (UTL/UAC) reasoning.

## Audit surface (from the features-side research)

1. **Rolling / expanding windows** in calculators (moving averages, ATR, technical) — must not include the current
   forming bar's future or peek across the right boundary.
2. **Point-in-time joins** — `available_at` vs `period_end`: a feature must only see data with
   `available_at <= t_close`.
3. **Forward-fill on gaps** — LOCF/ffill must not carry a future observation backward across a gap.
4. **Multi-timeframe confluence** — when a fine-TF feature is joined to a coarse-TF bar, alignment must respect the
   coarse bar's right edge (the coarse bar is known only at its close).

## Todos

- [x] ✅ [AUDIT] P1. Enumerate every resample / `rolling` / `group_by_dynamic` / `resample(...).agg` / ffill / PIT-join
      callsite in features-service; classify each as right-edge-safe or suspect, with file:line. — Gate: a manifest
      table (callsite → verdict → fix-needed) embedded in this plan's Progress Log; zero un-triaged callsites.
      — audit complete 2026-06-28; manifest in Progress Log below.
- [x] ✅ [IMPLEMENT] P1. Fix each suspect callsite to honour `t_close` / `available_at <= t_close`; delete any latent
      open-edge or future-peeking path. — Gate: each fix has a before/after note; no callsite remains classified
      "suspect". — features-service@479da135; 5 center=True rolling fixes + 3 weekly/monthly resample shift(1) fixes; QG green.
- [x] ✅ [IMPLEMENT] P1. Add a **gate script** (mirror of the MDPS STEP 5.92 `check_bar_edge_open_ingestion.py` pattern)
      that AST-flags features-side open-edge / future-peeking patterns (e.g. `closed="left"` on a candle resample,
      `shift(-n)`, ffill without a forward-bound). Wire into features `quality-gates.sh`. — Gate: the gate fails on a
      planted violation fixture and passes clean on the tree.
      — features-service@0018fcf8; `scripts/quality_gates/check_features_no_lookahead.py` (3 AST patterns: rolling-center-true, shift-negative, resample-left-no-shift); 9 planted-violation + clean-code tests green; STEP 5.92 wired into quality-gates.sh; gate exit 0 on current tree (12 baselined intentional targets, 0 new violations).
- [x] ✅ [TEST] P1. Regression suite: a window-W determinism test (a feature computed at bar N depends only on bars ≤ N)
      across resample paths + multi-TF confluence; extends the existing cross-source bar-edge fixture. — Gate:
      `tests/.../test_feature_no_lookahead.py` green; asserts trade-for-trade equivalence of incremental-vs-batch
      feature values at each bar close.
      — features-service@5fd417c9; `tests/delta_one/unit/test_feature_no_lookahead.py`; 6 tests green: TrendlineFeatures (1+10 extra bars) + WeeklyAnchors (weekly 1-bar, new-week, monthly resample, prev-week content check); QG green.
- [ ] [AGENT] P1. features-service QG green; quickmerge `--agent --files`. — Gate: QG green; CI `quality-gates-v2`
      green.

## Current-state delta (audited 2026-06-28)

- **Already right-edge (verified — NOT re-litigated):**
  `features_service/delta_one/app/core/candle_resampler.py::resample_ohlcv`
  (`group_by_dynamic(..., closed="right", label="right")`) + `timeframe_resampler.py`
  (`resample(..., label="right", closed="right")`); regression
  `tests/delta_one/unit/test_cross_source_bar_edge_equivalence.py` green (the 2026-06-08 fix).
- **Remaining surface to audit + guard (the delta):** rolling/expanding windows in `delta_one/app/calculators/*`
  (moving_averages, technical, ATR); PIT joins on `available_at` vs `period_end`; ffill across gaps; multi-TF confluence
  alignment to the coarse bar's right edge. These are the callsites the AUDIT todo enumerates and the gate script flags.

## Notes

- This plan is the features-side companion to the MDPS-side `bar_edge_left_vs_right_remediation_2026_06_08`; it does NOT
  re-litigate the MDPS store (already verified right-edge) — it owns the _features re-aggregation_ surface only.
- Feeds Plan 6's smoke test: the harness asserts no-look-ahead as part of "RUNNABLE".

## Progress Log

### 2026-06-28 — AUDIT -001: callsite manifest (all features-service non-test source)

Search: `rg -n "\.rolling\(|resample\(|group_by_dynamic\(|\.ffill\(|forward_fill\(|merge_asof\(|\.shift\("` +
secondary pass `rg -n "center=True|\.ffill\(|forward_fill\(|merge_asof\(|\.shift\(-"` scoped to
`features_service/` excluding `.venv`, `tests`, `.yaml/.yml/.md`.

#### SAFE callsites (right-edge or past-only)

| file:line | pattern | verdict |
|---|---|---|
| `delta_one/app/core/candle_resampler.py:170` | `group_by_dynamic(..., closed="right", label="right")` | SAFE — explicit right-edge |
| `delta_one/app/core/timeframe_resampler.py:265` | `resample(freq, label="right", closed="right").agg(...)` | SAFE — explicit right-edge |
| `delta_one/app/calculators/sr_memory.py:75-76` | `swing_high_value.ffill()` / `swing_low_value.ffill()` | SAFE — S/R memory LOCF carries past level forward |
| `delta_one/app/calculators/swing_outcome_targets.py:150` | `swing_high_value.ffill()` / `swing_low_value.ffill()` | SAFE — same S/R memory LOCF pattern |
| `delta_one/app/calculators/vwap.py:180,208` | `day_vwap.ffill()` / `week_vwap.ffill()` | SAFE — fills zero-volume gaps within a session group (past value) |
| `delta_one/engine/ohlcv_passthrough.py:65` | `pl.col(col).forward_fill()` | SAFE — fills NaN after left-join on sorted timestamps (carries past candle forward) |
| `multi_timeframe/calculators/tf_confluence_signals.py:221,223` | `pl.col(swing_high_col).forward_fill()` / `swing_low_col` | SAFE — S/R memory LOCF on higher-TF levels |
| `delta_one/app/calculators/weekly_anchors.py:128-131` | `resample("W-MON",...).max().shift(1)` / `.min().shift(1)` / `.last().shift(1)` | SAFE — `.shift(1)` references PREVIOUS week |
| `delta_one/app/calculators/signal_confirmation.py:102,105` | `low.shift(-1).shift(2)` / `high.shift(-1).shift(2)` | SAFE — net shift = +1 (past lag); `shift(-1).shift(2)` = value at t-1 |
| `delta_one/app/calculators/technical_indicators.py` (all rolling) | `.rolling(W).{mean,std,max,min,sum}()` without `center=True` | SAFE — trailing window only |
| `delta_one/app/calculators/moving_averages.py` (all rolling) | `.rolling(W).{mean,std,ewm}()` | SAFE — trailing window only |
| `delta_one/app/calculators/oscillators.py` / ATR / momentum etc. | `.rolling(W).*` without `center` | SAFE — trailing |
| `calendar/engine/calculators/temporal.py:163,265` | `.shift(lag)` with `lag > 0` | SAFE — positive shift = past |
| `calendar/engine/calculators/sentiment_calculator.py:89,94` | `.rolling(5).mean()` | SAFE — trailing |
| `cross_instrument/app/calculators/cointegration_calculator.py:71-72,100` | `.rolling(W).mean()/.std()`, `.shift(1)` | SAFE — trailing + lag-1 |
| `cross_instrument/app/calculators/cross_asset_correlation.py:108` | `.shift(1)` | SAFE — 1-bar lag |
| `onchain/app/calculators/macro_sentiment_calculator.py:193` | `.ffill()` on daily market-cap resampled to minute | SAFE — LOCF of daily data, past value |

#### LOOK-AHEAD bugs (confirmed, fix-needed in -002)

| file:line | pattern | look-ahead mechanism | fix |
|---|---|---|---|
| `delta_one/app/calculators/fibonacci.py:304-305` | `rolling(roll_win, center=True).max()/.min()` | `center=True` — window spans `[t-W//2, t+W//2]`; uses future bars to detect swing H/L | Replace `center=True` with trailing right-edge; shift result back `W//2` to mark at bar of detection |
| `delta_one/app/calculators/market_structure.py:96-97` | `rolling(local_window, center=True).max()/.min()` | Same — swing pivot detection peeks forward | Same fix: trailing window, right-edge stamp |
| `delta_one/app/calculators/market_structure_sequence.py:97-98` | `rolling(roll_win, center=True).max()/.min()` | Same | Same fix |
| `delta_one/app/calculators/swing_outcome_targets.py:119-120` | `rolling(local_window, center=True).max()/.min()` | Same — swing detection within target calculator | Same fix |
| `delta_one/app/calculators/trendline.py:127,130` | `rolling(roll_win, center=True).max()/.min()` | Same | Same fix |
| `delta_one/app/calculators/weekly_anchors.py:98-100` | `resample("W-MON", label="left", closed="left").{first,max,min}()` then `reindex(ffill)` | Current-week aggregate broadcast to all bars in week; bar at Mon 00:00 sees Fri's high | Replace with running `expanding().max()` within weekly group, or use `.shift(1)` to reference prior week |
| `delta_one/app/calculators/weekly_anchors.py:110-113` | same resample pattern for `monday_high/low` | Monday bars see end-of-day Monday high/low at first Monday bar | Use `cummax`/`cummin` within Monday group or accept 1-bar lag |
| `delta_one/app/calculators/weekly_anchors.py:144-145` | `resample("MS", label="left", closed="left").{max,min}()` then `reindex(ffill)` | Current-month aggregate broadcast to all bars in month | Use running intra-month `expanding().max()` or shift(1) to prior month |

#### Intentionally look-ahead (target/label computation — NOT a bug)

| file:line | pattern | rationale |
|---|---|---|
| `delta_one/app/calculators/targets.py:61,63,80,83,92,93,106,116` | `df["close"].shift(-horizon)` and `rolling(W).std().shift(-horizon)` | ML target labels: forward returns, future volatility, max drawdown. Correct to peek forward — these are NOT input features |
| `delta_one/app/calculators/swing_outcome_targets.py:152-153` | `df["high"].shift(-1).rolling(L).max()` / `df["low"].shift(-1).rolling(L).min()` | Outcome classification horizon — computes max high/min low over next L bars after a swing; target label, not feature |

#### No PIT-join (`merge_asof`) callsites found in features-service source (0 hits)

**Summary: 5 confirmed look-ahead bugs in `center=True` swing-detection callsites + 3 in `weekly_anchors.py` resample.
Fix scope for -002: 8 callsites across 6 files.**
