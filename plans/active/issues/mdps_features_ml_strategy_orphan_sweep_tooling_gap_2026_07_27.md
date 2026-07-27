---
doc_type: issue
title:
  "No orphan-detection tooling exists for the MDPS/features/ml/strategy pipeline layers — only raw-MTDS has a working
  sweep; the cross-repo lineage audit (todo 11b) needs 3 new purpose-built tools, not a config change to the existing
  one"
summary: >-
  Scoped while working data_pipeline_check_mdps_features_2026_07_20.md todo 11b ("cross-repo orphan/lineage audit,
  MTDS→MDPS→features→ml/strategy"). Confirmed `migration_orphan_sweep.py` (the only working orphan sweep in the corpus,
  proven on sports/cefi/defi/tradfi/prediction over 2026-07-21..24) explicitly excludes
  `processed_candles/`/`processed_data/`/`features/` and its own source comment's claim that those corpora "have their
  own re-runnable sweep" is false — independently confirmed via `codex/02-data/orphan-object-detection.md` §2c/§5's own
  "no known orphan coverage" finding. features-service/ml-service/strategy-service all write manifests via the same UTL
  `ManifestWriter`/`record_captured` pattern (so the same orphan failure mode is structurally possible there too), but
  zero orphan-detection tooling exists for any of them. No generic/reusable sweep framework exists either — sports
  needed its own 771-line fork of the 1109-line raw-tick sweep, and candle/feature/ml-strategy shard keys are each a
  genuinely different shape (candle adds instrument_type×data_type×timeframe; feature is asset_group×feature_family;
  ml/strategy are run/model-id-keyed, not day-sharded). Splitting into 3 independently-dispatchable build+run todos
  rather than leaving one all-or-nothing checkbox no single session can honestly complete.
status: open
nature: issue
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos:
  [
    market-data-processing-service,
    features-service,
    ml-service,
    strategy-service,
    instruments-service,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [orphan, orphan-real, single-walk, manifest-completeness, mdps, features, ml, strategy, tooling-gap]
related:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /plans/active/issues/estate_orphan_assessment_2026_07_21.md,
    /plans/active/issues/mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md,
    /codex/02-data/orphan-object-detection.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-27"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 4.5
estimate_calibrated_ai_days: 4.5
assigned_role: data_engineering
drift_direction: advance-code
source: >-
  Surfaced 2026-07-27 (slot-15, infra) while scoping data_pipeline_check_mdps_features_2026_07_20.md todo 11b before
  attempting a full cross-repo lineage audit in-session.
resolved_by:
locked_by:
locked_since:
depends_on: []
---

# No orphan-detection tooling for MDPS/features/ml/strategy — todo 11b needs 3 new tools, not one VM run

## What I found

Dispatched a scoping sub-agent, then independently verified its key claim. Facts:

1. **Raw-MTDS layer (instruments-service) is the only stage with a working orphan sweep.** `migration_orphan_sweep.py`
   (1109 lines) classifies every GCS object against the manifest into A_canonical_manifested / B_legacy_duplicate /
   C_manifest_infra / D_junk / E_orphan_real (real data, zero manifest row). Proven on real infra 2026-07-21..24 for
   sports/cefi/defi/tradfi/prediction via `launch-orphan-sweep-vm.sh` — see `estate_orphan_assessment_2026_07_21.md` for
   the full multi-day history (several VM crashes/OOMs/preemptions before it stabilized on `e2-highmem-8` with
   checkpointed, column-projected reads).
2. **MDPS candle layer has NO equivalent.** `migration_orphan_sweep.py`'s `_DATA_PREFIXES` covers only
   `raw_tick_data/`/`day=`; its own source comment (line 112) asserts `processed_candles/`/`processed_data/`/
   `features/` "have their own re-runnable sweep" — **confirmed false**: `codex/02-data/orphan-object-detection.md`
   §2c/§5 already documents this exact claim as unverified/false and states those corpora have "no known orphan
   coverage." The only candle-orphan work that exists is
   `issues/mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md` — CEFI-only, scoped narrowly to files that
   lost their `record_captured` write during pre-fix-era OOM crashes (3 known venues, one known day); "corpus-wide
   extent... unknown," not a general sweep.
3. **features-service/ml-service/strategy-service all use the same manifest pattern, with zero orphan tooling.** All
   three import `ManifestWriter`/`record_captured`/manifest-guard helpers from unified-trading-library
   (`features-service/.../manifest_window_guard.py`, `ml-service/.../manifest_gap_handler.py` +
   `manifest_inference_guard.py`, `strategy-service/.../strategy_manifest.py`) — so the same "real object, zero manifest
   row" failure mode is structurally possible in all three. `ml-service` and `strategy-service` have zero
   orphan/sweep/reconcile scripts at all; `features-service` has one hit (`features_sports_reconcile_available_at.py`,
   an `available_at` timestamp fix, not orphan detection).
4. **No generic/reusable framework exists.** `migration_orphan_sweep.py` is hard-coded to the raw-tick shard key
   (`asset_group, venue, chain, instrument_type, data_type` + the `raw_tick_data/`/`day=` path shape,
   `unified_api_contracts.canonical_path_templates`) — proof it isn't parameterizable: sports required its own 771-line
   fork (`migration_orphan_sweep_sports.py`), not a config flag on the shared tool. Candle/feature/ml-strategy shard
   keys are each a genuinely different shape (candle adds `instrument_type × data_type × timeframe`; feature is
   `asset_group × feature_family`; ml/strategy are run/model-id-keyed, not day-sharded at all). The REUSABLE part is the
   design pattern, not the code: single-walk discipline, the A-E classification taxonomy, `record_captured`-only
   backfill (never delete), `is_covered()`'s wildcard-tolerant manifest match — documented at
   `codex/02-data/orphan-object-detection.md`.

## Why this needs a split, not one checkbox

Todo 11b (`data_pipeline_check_mdps_features_2026_07_20.md`) asks for one report covering raw→candle→feature→ml/strategy
across all 5 asset_groups. Given the raw-MTDS-layer equivalent alone took 2026-07-21 through 2026-07-24 (multiple VM
crashes, 2 major memory bugs found + fixed, several SPOT preemptions) to get right for ONE stage, building 3 NEW
purpose-built sweep tools (candle, feature, ml/strategy) — each its own shard-key design, its own launcher, its own
VM-stability iteration — in one dispatch would either be rushed (risking the same crash/OOM class of bug the raw-MTDS
tool needed days to shake out) or dishonestly claimed done. Splitting into independently-dispatchable stage-scoped todos
lets each one be built, validated, and run to real completion on its own timeline, exactly like the raw-MTDS layer was.

## Open work

- [ ] 1. [SCRIPT] P1. **Build + validate an MDPS candle-layer orphan sweep** (new script in
      `market-data-processing-service/scripts/`, name TBD) — mirror `migration_orphan_sweep.py`'s A-E taxonomy against
      `processed_candles/by_date/` per asset_group (shard key: day, venue, chain, instrument_type, data_type, timeframe;
      note the real measured DEFI path segment ORDER is `timeframe/data_type/instrument_type/venue`, NOT the cefi-analog
      `venue/instrument_type/data_type` — verify per-AG before assuming one shape). ALSO check manifest coverage under
      BOTH the source `data_type` vocabulary and the aggregated `mdps_data_type_key()` vocabulary (the newly-discovered
      false "never populated" class from `issues/candle_feature_canonical_path_divergence_2026_07_20.md` todo 7). Repo:
      market-data-processing-service. Launch on a Tier-2 SPOT VM per the heavy-I/O rule, never in-session — budget for
      the SAME class of iteration (memory/preemption) the raw-MTDS sweep needed. Feeds
      `mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md`'s corpus-wide backfill scope.
- [ ] 2. [SCRIPT] P2. **Build + validate a features-service orphan sweep** — same A-E taxonomy pattern, shard key
      `asset_group × feature_family × day`. Repo: features-service. VM-run, never in-session.
- [ ] 3. [SCRIPT] P2. **Build + validate an ml/strategy orphan sweep** — genuinely different shape (run/model-id-keyed,
      not day-sharded); scope the actual shard key first before writing the sweep (may need its own design pass, not a
      mechanical port of the day-sharded pattern). Repo: ml-service, strategy-service. VM-run, never in-session.
- [ ] 4. [DOC] P2. Once todos 1-3 land real per-stage findings, write the combined cross-repo lineage report
      `data_pipeline_check_mdps_features_2026_07_20.md` todo 11b actually asks for, then flip that todo.
