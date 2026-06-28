---
doc_type: plan
title: Features — read book-microstructure from candle columns, not raw snapshots
summary:
  "Repoint book_microstructure_feature_extractor at the new precomputed candle columns so the ~100 CeFi/prediction
  microstructure features compute from the self-contained candle, with a parity assertion vs the raw-snapshot path."
status: draft
nature: process
asset_group: [cefi, prediction]
stage: [features]
repos: [features-service]
scope: [engineer, admin]
tags: [features, book-microstructure, candle-columns, parity, reduced-data]
related:
  [
    ./mdps_features_reduced_artifact_tracker_2026_06_28.md,
    ./mdps_book_microstructure_precompute_columns_2026_06_28.md,
    ../epics/features_and_ml_master.md,
  ]
created: 2026-06-28
parent_epic: features_and_ml_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
last_updated: 2026-06-28
locked_by: NA
locked_since:
supersedes:
superseded_by:
depends_on: [mdps_book_microstructure_precompute_columns_2026_06_28]
gate_on_depends: true
source: [operator request 2026-06-28]
---

# Features — read book columns, not raw snapshots

`features_service/cefi/book_microstructure_feature_extractor.py` currently computes spread/microprice/imbalance/
queue-position/depth from raw `book_snapshot_5` rows. Plan 1 bakes those as intra-bar summary columns on the candle.
This plan repoints the extractor at the columns, so features run off the self-contained candle and never need book
ticks.

**Execution model:** Sonnet — single-repo refactor from a clear spec (the Plan 1 column contract). The only subtlety is
the parity fixture; bounded.

**Prereq:** Plan 1 (`mdps_book_microstructure_precompute_columns`) must be review-confirmed (task-level `prereqs`) — the
column contract is its output.

## Todos

- [ ] [IMPLEMENT] P1. Repoint `book_microstructure_feature_extractor` to read the precomputed candle columns (spread
      twmean/std/…, microprice mean/tilt, imbalance mean/std/close, depth per level, queue) instead of aggregating raw
      `book_snapshot_5`. Delete the now-dead raw-snapshot aggregation path (no-tech-debt). — Gate: extractor imports no
      `book_snapshot_5` reader; computes all prior microstructure features from columns.
- [ ] [TEST] P1. **Parity fixture** — on a captured BINANCE-FUTURES book day, assert the column-derived microstructure
      features match the legacy raw-snapshot-derived features within a declared ε (document ε per feature; some are
      exact, time-weighted ones are near-exact). — Gate: `tests/.../test_book_microstructure_parity.py` green; ε table
      in the test docstring.
- [ ] [VERIFY] P1. Run the CeFi delta-one feature pass end-to-end on a real candle shard carrying the new columns; read
      back and confirm the microstructure feature group writes non-zero rows (ties to the features e2e WRITE path). —
      Gate: named command + GCS `-test` path + observed row count.
- [ ] [AGENT] P1. features-service `quality-gates.sh` green (no `reportUnknown*` regression per the colocated-pipeline
      strictness rule); quickmerge `--agent --files`. — Gate: QG green; CI `quality-gates-v2` green.

## Current-state delta (audited 2026-06-28)

- **Exists:** `features_service/cefi/book_microstructure_feature_extractor.py` computes the ~100 microstructure features
  (spread / microprice / microprice_tilt / imbalance / queue / depth) from raw `book_snapshot_5` rows today.
- **Blocked-on (dispatch-gating prereq):** Plan 1's candle columns — the column contract IS Plan 1's output, so this
  plan can only land after Plan 1 ships the columns.
- **Delta:** repoint the extractor to read the precomputed columns, delete the raw-snapshot aggregation path
  (no-tech-debt), and add the parity fixture vs the legacy path (declared ε per feature).

## Notes

- This plan does NOT change which instruments get features — that is Plan 3 (MVP-for-features universe). It only changes
  the _data source_ of the microstructure family.
- Right-edge correctness of the columns is Plan 1's responsibility; Plan 4 owns no-look-ahead on any re-aggregation the
  extractor does on top.
