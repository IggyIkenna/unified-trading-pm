---
doc_type: plan
title: Features — no-look-ahead guard for candle re-aggregation
summary:
  "Audit + guard every place features re-aggregate or roll candles (resample 1m→5m→1h, rolling windows, PIT joins,
  forward-fill, multi-TF confluence) so the right-edge t_close convention holds and no future value leaks; add a gate
  script + regression tests."
status: draft
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

- [ ] [AUDIT] P1. Enumerate every resample / `rolling` / `group_by_dynamic` / `resample(...).agg` / ffill / PIT-join
      callsite in features-service; classify each as right-edge-safe or suspect, with file:line. — Gate: a manifest
      table (callsite → verdict → fix-needed) embedded in this plan's Progress Log; zero un-triaged callsites.
- [ ] [IMPLEMENT] P1. Fix each suspect callsite to honour `t_close` / `available_at <= t_close`; delete any latent
      open-edge or future-peeking path. — Gate: each fix has a before/after note; no callsite remains classified
      "suspect".
- [ ] [IMPLEMENT] P1. Add a **gate script** (mirror of the MDPS STEP 5.92 `check_bar_edge_open_ingestion.py` pattern)
      that AST-flags features-side open-edge / future-peeking patterns (e.g. `closed="left"` on a candle resample,
      `shift(-n)`, ffill without a forward-bound). Wire into features `quality-gates.sh`. — Gate: the gate fails on a
      planted violation fixture and passes clean on the tree.
- [ ] [TEST] P1. Regression suite: a window-W determinism test (a feature computed at bar N depends only on bars ≤ N)
      across resample paths + multi-TF confluence; extends the existing cross-source bar-edge fixture. — Gate:
      `tests/.../test_feature_no_lookahead.py` green; asserts trade-for-trade equivalence of incremental-vs-batch
      feature values at each bar close.
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
