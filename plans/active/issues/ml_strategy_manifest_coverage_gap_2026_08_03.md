---
doc_type: issue
title:
  "ml-service predictions + strategy-service strategy_instructions have ZERO manifest coverage in prod — real
  strategy_instructions objects genuinely orphaned"
summary: >-
  First real-GCS-data run of ml_orphan_sweep.py + strategy_orphan_sweep.py (todo 3b of
  mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md), executed via 2 Tier-2 SPOT VMs. Both corpora's
  availability manifests are completely absent in prod (`_index/availability_index.parquet` not found in either bucket,
  0 captured cells) — not a sweep-tool bug, confirmed via a real `gcloud storage ls` of both buckets. ml-service
  `ml_predictions`: 0 real prediction objects exist yet (0/0/0/0 across A/D/E, F_other_corpus=236 for the real
  ml_models/ml_training_artifacts objects sharing the bucket) — genuinely unused so far, not a gap. strategy-service
  `strategy_instructions`: 7 REAL objects exist in prod with zero manifest coverage — all 7 classify E_orphan_real
  (there is no manifest row to compare against). The real objects also confirmed the `client_id=` path segment the
  todo-3b PATH_REGISTRY fix added is genuinely present in prod paths, though populated EMPTY for all 7
  (`client_id=/strategy_id=.../day=.../instructions.parquet`).
status: open
nature: issue
asset_group: [defi, cefi]
stage: [data]
repos: [ml-service, strategy-service, unified-trading-pm]
scope: [engineer, admin]
tags: [data-correctness, ml, strategy, manifest-completeness, orphan-real, honest-absence, big-finding]
related:
  [
    /plans/active/issues/mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md,
    /plans/active/issues/features_service_manifest_coverage_gap_2026_08_03.md,
    /codex/02-data/orphan-object-detection.md,
  ]
created: "2026-08-03"
last_updated: "2026-08-03"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.7
assigned_role: data_engineering
drift_direction: advance-code
source: >-
  Surfaced 2026-08-03 (slot 3) running the first real-GCS-data validation of ml_orphan_sweep.py (ml-service@b6c87d0c) +
  strategy_orphan_sweep.py (strategy-service@a353a570) via 2 real Tier-2 SPOT VMs, launched through the new
  launch-ml-strategy-orphan-sweep-vm.sh (deployment-service@fb29a8d).
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md,
    /codex/02-data/orphan-object-detection.md,
    ml-service/scripts/ml_orphan_sweep.py,
    strategy-service/scripts/strategy_orphan_sweep.py,
  ]
depends_on: []
---

# ml_predictions + strategy_instructions manifest coverage gap

## What I found

Ran the newly-wired `ml_orphan_sweep.py` / `strategy_orphan_sweep.py` on real prod data via 2 Tier-2 SPOT VMs
(`ml-orph-*` / `strat-orph-*`, `e2-standard-4`, both completed in under 2 minutes, no preemption). Real, measured
results:

| corpus                | bucket                                    | manifest cells | A   | C   | D   | E (orphan_real) | F (other-corpus) |
| --------------------- | ----------------------------------------- | -------------- | --- | --- | --- | --------------- | ---------------- |
| ml_predictions        | ml-store-prd-central-element-323112       | 0 (absent)     | 0   | 2   | 0   | 0               | 236              |
| strategy_instructions | strategy-store-prd-central-element-323112 | 0 (absent)     | 0   | 0   | 0   | 7               | n/a              |

1. **Neither bucket has an `_index/availability_index.parquet` at all** — confirmed via the sweep's own manifest-load
   warning (`no _index/availability_index.parquet in <bucket>`) AND independently via
   `gcloud storage ls gs://ml-store-prd-central-element-323112/_index/` (empty) and the equivalent for strategy-store.
   This is a genuine absence, not a sweep-tool bucket-resolution bug (the same pattern that caught todo 1's real sports
   bucket bug would have caught this too — both buckets resolved correctly and returned real listings).
2. **`ml_predictions` has ZERO real prediction objects in prod today** (A=0, D=0, E=0). The 236 `F_other_corpus` objects
   are real `ml_models`/`ml_training_artifacts` data sharing the bucket (see the sibling
   `mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md` todo-3b fix — this sweep run is what surfaced and
   fixed the sibling-corpus misclassification bug in the same dispatch). This reads as **genuinely unused, not a gap** —
   `ml-service/ml_service/inference/cli/main.py`'s `MLInferenceBatchModeHandler.run()` constructs a `prediction_writer`
   and then discards it (`_ = prediction_writer`) rather than wiring it into the actual inference flow, consistent with
   zero real writes ever having happened.
3. **`strategy_instructions` has 7 REAL objects in prod with zero manifest coverage** — all classify `E_orphan_real` (no
   manifest row exists to compare against, since the manifest itself is absent). Real object paths (from the run log):
   - `strategy_instructions/client_id=/strategy_id=DEFI_ETH_BASIS_MULTI_HUF_1H_V1/day=2025-06-15/instructions.parquet`
   - `strategy_instructions/client_id=/strategy_id=DEFI_ETH_BASIS_MULTI_HUF_1H_V1/day=2025-06-16/instructions.parquet`
   - `strategy_instructions/client_id=/strategy_id=DEFI_ETH_RECURSIVE_HEDGED_ALL_HYPERLIQUID_HUF_1H/day=2025-06-15/instructions.parquet`
   - `strategy_instructions/client_id=/strategy_id=DEFI_ETH_STAKED_BASIS_HYPERLIQUID_SCE_1H/day=2025-06-15/instructions.parquet`
   - `strategy_instructions/client_id=/strategy_id=DEFI_ETH_STAKED_BASIS_HYPERLIQUID_SCE_1H/day=2025-06-16/instructions.parquet`
   - `strategy_instructions/client_id=/strategy_id=DEFI_ETH_YLD_AAVE_USDC_HUF_1H_V1/day=2025-06-15/instructions.parquet`
   - `strategy_instructions/client_id=/strategy_id=DEFI_ETH_YLD_AAVE_USDC_HUF_1H_V1/day=2025-06-16/instructions.parquet`

   These are real strategy backtest/paper artifacts from 2025-06-15/16 — genuinely captured by
   `gcs_storage_service.py::write_instructions` at some point, but never registered via `strategy_manifest.py`'s
   `StrategyManifestRecorder`. Confirms the todo-3b PATH_REGISTRY fix's `client_id=` segment is real (the sweep's
   grain-tolerant `is_covered()` blank-`client_id`-as-wildcard match — already built for exactly this case — worked
   correctly against real data), just populated EMPTY for these particular 7 objects (an early/pre-multi-client-era
   write, plausibly).

## Why this is a big finding, not backfill-in-this-session scope

Per this repo's data-pipeline-correctness HARD RULE, an absent manifest for a corpus with real backing data is a
correctness gap (not an operational choice) — `strategy_instructions` objects exist that no downstream consumer using
the manifest (completion-checking, coverage reporting) can see. But root-causing WHY the manifest was never populated (a
`StrategyManifestRecorder` wiring gap? an env/bucket mismatch between the writer and where `record_captured` calls
landed?) is a genuine investigation, not a mechanical fix — exactly the class of judgment call this doc's own "Why this
needs a split" section (parent issue) argues should be its own todo, not folded into "validate the tool" scope.

## Open work

- [ ] 1. [SCRIPT] P2. **Investigate why `strategy_instructions` has zero manifest rows in prod** — grep
      `StrategyManifestRecorder`/`record_captured` call sites in `strategy-service`, confirm whether they're wired into
      the live paper/backtest write path at all, or exist but never fire (env mismatch, exception swallowed, etc.).
      Repo: strategy-service.
- [ ] 2. [SCRIPT] P2. **Backfill `record_captured` manifest rows for the 7 real `strategy_instructions` orphans** listed
      above (additive-only, `NEVER delete` per the sweep's own printed warning) — once todo 1 confirms the row shape
      (`client_id`/`strategy_id`/`date`/`data_type="strategy_instructions"`/`capture_status="captured"`) a recorder
      should write going forward. No existing `backfill_*_class_e.py` tool exists for strategy-service yet (unlike
      features-service's `backfill_feature_orphan_class_e.py`) — build one mirroring that pattern, or a one-off script
      for this small (7-object) case if todo 1 finds this is a one-time historical gap rather than an ongoing wiring
      bug. Repo: strategy-service.
- [ ] 3. [DOC] P3. **Confirm `ml_predictions` is genuinely intentionally unwired** (not a silently-broken feature) —
      check with the operator or a design doc whether ml-service inference was ever meant to persist predictions in prod
      yet, or if `MLInferenceBatchModeHandler`'s discarded `prediction_writer` is itself a gap worth its own todo. If
      genuinely not-yet-built, no action needed beyond this note. Repo: ml-service.

## Progress Log

- **2026-08-03** (AO dispatch, slot 3) — Filed after running the real-GCS-data validation VMs for todo 3b of
  `mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md`. Both sweeps ran cleanly against real prod buckets
  (correct bucket resolution, no crashes); the manifest-absence + real-orphan findings above are genuine data gaps this
  validation run surfaced, out of that todo's own "validate the tool" scope.
