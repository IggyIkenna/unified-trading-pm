---
doc_type: issue
title:
  "Combined cross-repo orphan/lineage report (MTDS→MDPS→features→ml/strategy) — the report
  data_pipeline_check_mdps_features_2026_07_20.md todo 11b asked for"
summary: >-
  Synthesizes the 4 stage-scoped orphan/lineage findings produced by
  mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md's todos 1-3c (build+validate 3 new sweep tools — MDPS
  candle, features, ml/strategy — since only raw-MTDS had one before this work) into the single cross-repo report todo
  11b of data_pipeline_check_mdps_features_2026_07_20.md originally asked for. Does NOT re-litigate or duplicate any
  per-stage finding's own open todos — those stay tracked in their own docs; this is a read-only rollup + status
  snapshot across all 4 pipeline stages, written to close out 11b's non-checkbox pointer. Headline: every stage now has
  working orphan-detection tooling (a corpus-wide capability gap that didn't exist before this line of work), real
  prod-data sweeps ran on all 4 stages, and 3 of 4 stages have their real orphans already root-caused + backfilled; the
  raw-MTDS layer (stage 0, pre-existing tooling) is also fully swept + backfilled. Remaining open work is small,
  bounded, and already tracked per-stage — no new corpus-wide gap surfaced by this synthesis.
status: resolved
nature: record
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [orphan, orphan-real, lineage, manifest-completeness, mdps, features, ml, strategy, mtds, cross-repo, report]
related:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /plans/archive/issues/mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md,
    /plans/active/issues/estate_orphan_assessment_2026_07_21.md,
    /plans/active/issues/mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md,
    /plans/active/issues/features_service_manifest_coverage_gap_2026_08_03.md,
    /plans/active/issues/ml_strategy_manifest_coverage_gap_2026_08_03.md,
    /plans/active/issues/strategy_ml_orphan_coverage_design_gaps_2026_08_03.md,
    /codex/02-data/orphan-object-detection.md,
  ]
created: "2026-08-03"
last_updated: "2026-08-03"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: advance-code
source: >-
  Written 2026-08-03 (slot 4) as todo 4 of mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md, once todos
  1-3c had all landed real per-stage findings.
resolved_by: slot-4-2026-08-03
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md,
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /codex/02-data/orphan-object-detection.md,
  ]
depends_on: []
---

# Combined cross-repo orphan/lineage report — MTDS → MDPS → features → ml/strategy

## Why this doc exists

`data_pipeline_check_mdps_features_2026_07_20.md` todo 11b asked for one cross-repo orphan/lineage audit report covering
the full pipeline. `mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md` (todo 11b-scope) found that report
was not honestly writable in one dispatch — no orphan-detection tooling existed for 3 of the 4 stages, and the
raw-MTDS-layer tool alone took 2026-07-21..24 to stabilize. It split the work into todos 1-3c (build

- validate 3 new sweep tools, one per stage, each on real prod data via Tier-2 SPOT VMs) before this report could be
  written honestly. All of todos 1-3c are now done. This doc is that report — a read-only synthesis, not a new
  investigation. Every open item below is a pointer to its own already-tracked doc, not a duplicate checkbox.

## Stage-by-stage findings

### Stage 0 — Raw tick / reference data (instruments-service, MTDS) — pre-existing tooling

Source: [`estate_orphan_assessment_2026_07_21.md`](estate_orphan_assessment_2026_07_21.md). The only stage with working
orphan tooling BEFORE this line of work (`migration_orphan_sweep.py`). All 5 asset_groups swept + backfilled to
completion 2026-07-21..24:

| asset_group | E_orphan_real found           | Backfill status                                    |
| ----------- | ----------------------------- | -------------------------------------------------- |
| sports      | 214,319 (+34,385 legacy-dup)  | DONE — 97,606 + 4 cells recorded                   |
| cefi        | 935,714 (8.5M-object walk)    | DONE — 53,345 cells recorded (1 corrupt-file skip) |
| tradfi      | swept clean                   | n/a — clean exit                                   |
| prediction  | 3,137,183 (6.6M-object walk)  | DONE — 5,719 cells, 0 errors                       |
| defi        | 15,865,384 → 637,738 residual | DONE — 637,523 converted after 22h self-healing    |

Only open item: todo 6 in that doc (a batching-hardening refactor to `backfill_orphan_class_e.py --apply` so a SPOT
preemption doesn't lose 100% of an in-flight backfill's progress) — non-blocking, doesn't affect data correctness.

### Stage 1 — MDPS candle layer — NEW tooling (todo 1)

Source:
[`mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md`](mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md).
`candle_orphan_sweep.py` built + validated, ran full-corpus on real prod data via 5 Tier-2 SPOT VMs:

| asset_group | Manifest coverage found | Backfill status     |
| ----------- | ----------------------- | ------------------- |
| cefi        | 460/405,956 (0.11%)     | DONE — 25,593 cells |
| tradfi      | 4,388/541,322 (0.81%)   | DONE — 22,905 cells |
| prediction  | 13,281/583,228 (2.28%)  | DONE — 1,609 cells  |
| defi        | 0/1,131,367 (0%)        | DONE — 36,145 cells |
| sports      | 59,540/59,540 (100%)    | already clean       |

Root cause: two bugs, both fixed — a going-forward-only self-lock fix that never touched non-ohlcv `data_type`s, and an
active DeFi streaming-write bug that silently swallowed `record_captured` exceptions with no `attempted_failed` fallback
(`market-data-processing-service@93a3680`). Total 86,252 cells backfilled across 4 AGs, zero
escalated/read_failed/verify_failed.

Only open item: verifying the DeFi `dex_pool_swaps` source-mistag correction campaign (a separate, smaller finding —
~394/1,155 days processed as of last log, checkpoint-driven resume, in flight) to full-corpus completion.

### Stage 2 — features-service layer — NEW tooling (todo 2/2b/2c/2d)

Source: [`features_service_manifest_coverage_gap_2026_08_03.md`](features_service_manifest_coverage_gap_2026_08_03.md).
`feature_orphan_sweep.py` built + validated for all 8 UAC `FeatureFamily` members, ran on real prod data via Tier-2 SPOT
VMs:

| family / AG                      | Orphan finding                                           | Status                                       |
| -------------------------------- | -------------------------------------------------------- | -------------------------------------------- |
| onchain / defi                   | 783/1,733 orphaned (45%)                                 | DONE — all 783 backfilled                    |
| sports / sports                  | 67,077/191,831 orphaned (35%)                            | DONE — backfilled, E now 0                   |
| calendar / global                | 6 phantom-captured manifest rows, 0 backing objects      | OPEN — root-cause needs an operator decision |
| delta_one, volatility, commodity | genuinely clean / 4 real orphans (commodity, backfilled) | DONE                                         |

Only open item: todo 4 (`[OPERATOR]` P1) in that doc — root-cause the calendar phantom-row anomaly (live writer bug vs
one-time historical artifact); this is an inverse-orphan class the sweep taxonomy doesn't natively classify, not a gap
in the tool itself.

### Stage 3 — ml/strategy layer — NEW tooling (todo 3/3b/3c)

Source: [`ml_strategy_manifest_coverage_gap_2026_08_03.md`](ml_strategy_manifest_coverage_gap_2026_08_03.md) +
[`strategy_ml_orphan_coverage_design_gaps_2026_08_03.md`](strategy_ml_orphan_coverage_design_gaps_2026_08_03.md).
`ml_orphan_sweep.py` + `strategy_orphan_sweep.py` built + validated on real prod data:

- **ml_predictions**: 0 real objects exist in prod (A/D/E all 0; `F_other_corpus=236` for sibling `ml_models`/
  `ml_training_artifacts` sharing the bucket, correctly excluded, not misclassified as junk after the `F_other_corpus`
  fix). Not a coverage gap — the writer is simply not yet wired to publish predictions.
- **strategy_instructions**: manifest completely ABSENT in prod (`_index/availability_index.parquet` not found in either
  bucket). 7 real objects exist, 100% orphan rate for the corpus that exists. Root cause confirmed ACTIVE: a blanket
  `except Exception: logger.warning` in `write_instructions_to_gcs` was silently swallowing the real manifest write
  failure (hardened to `logger.exception` — `strategy-service@788dfa08` — though the underlying exception itself is not
  yet pinpointed).
- **strategy_orders / strategy_positions / strategy_pnl**: confirmed DEAD CODE (zero live callers, no
  `PROTOCOL_DATA_SINK_BACKEND` wired in Cloud Run terraform) — not a real orphan-coverage gap today.
- **backtest_results**: genuinely untracked by any manifest — zero `ManifestWriter` calls anywhere near its write path.
- **ml_models / ml_model_metadata / ml_training_artifacts**: live writer, zero manifest coverage — the one real,
  unresolved coverage gap among the three deferred families.

Open items (all already tracked, none new): the 7-object `strategy_instructions` backfill + the ml_predictions
intentionality confirmation (`ml_strategy_manifest_coverage_gap_2026_08_03.md` todos 2/3); 3 `[OPERATOR]`-gated
wire-up-or-delete/manifest-design decisions for strategy_orders/positions/pnl, backtest_results, and
ml_models/metadata/training_artifacts (`strategy_ml_orphan_coverage_design_gaps_2026_08_03.md` todos 1-3, with a gated
todo 4 to build tooling once those land).

## Cross-repo lineage summary

| Stage         | Tooling before this work | Tooling now            | Real prod sweep run                        | Root-caused | Backfilled                                               |
| ------------- | ------------------------ | ---------------------- | ------------------------------------------ | ----------- | -------------------------------------------------------- |
| MTDS (raw)    | ✅ existed               | ✅                     | ✅ all 5 AGs                               | ✅          | ✅ all 5 AGs                                             |
| MDPS (candle) | ❌ none                  | ✅ new                 | ✅ all 5 AGs                               | ✅          | ✅ 4/5 AGs (sports already clean)                        |
| features      | ❌ none                  | ✅ new, all 8 families | ✅ 5 families × applicable AGs + commodity | ✅          | ✅ 2/2 real gap families                                 |
| ml/strategy   | ❌ none                  | ✅ new, 2 corpora      | ✅ both corpora                            | ✅          | ⏳ strategy_instructions backfill still open (7 objects) |

**Bottom line**: the corpus-wide capability gap this line of work opened against (only raw-MTDS had a working orphan
sweep; MDPS/features/ml/strategy had zero) is closed — every pipeline stage now has a validated, real-prod-data-run
orphan sweep tool. Every REAL orphan population this synthesis surfaced across all 4 stages has either already been
backfilled or has a small, bounded, already-tracked follow-up (never a new corpus-wide unknown). The only stage with
genuinely undefined orphan coverage left is 3 ml/strategy sub-corpora that are dead code, untracked-by-design, or simply
never wired to the manifest — each is now a scoped `[OPERATOR]` decision in its own doc, not an open-ended audit gap.

## Disposition

This closes the reporting deliverable `data_pipeline_check_mdps_features_2026_07_20.md` todo 11b asked for. Flipping
that doc's non-checkbox 11b pointer to reference this report in the same commit. `11c` (migrate existing candle/ feature
data to zero orphans) remains gated on 11b per its own `depends_on: 11b` note — that gate is now satisfied by this
report; 11c's own scope (a real GCS-write migration run) is unchanged and untouched by this doc.
