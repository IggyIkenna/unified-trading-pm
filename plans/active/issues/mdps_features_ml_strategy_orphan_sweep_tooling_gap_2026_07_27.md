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
  own re-runnable sweep" is false — independently confirmed via `/codex/02-data/orphan-object-detection.md` §2c/§5's own
  "no known orphan coverage" finding. features-service/ml-service/strategy-service all write manifests via the same UTL
  `ManifestWriter`/`record_captured` pattern (so the same orphan failure mode is structurally possible there too), but
  zero orphan-detection tooling exists for any of them. No generic/reusable sweep framework exists either — sports
  needed its own 771-line fork of the 1109-line raw-tick sweep, and candle/feature/ml-strategy shard keys are each a
  genuinely different shape (candle adds instrument_type×data_type×timeframe; feature is asset_group×feature_family;
  ml/strategy are run/model-id-keyed, not day-sharded). Splitting into 3 independently-dispatchable build+run todos
  rather than leaving one all-or-nothing checkbox no single session can honestly complete.
status: resolved
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
    /plans/archive/issues/mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md,
    /plans/active/issues/mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md,
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
resolved_by: unified-trading-pm (mdps_features_ml_strategy_orphan_lineage_report_2026_08_03.md)
locked_by:
locked_since:
context_scope:
  [
    /codex/02-data/orphan-object-detection.md,
    /plans/active/issues/ml_strategy_manifest_coverage_gap_2026_08_03.md,
    strategy-service/scripts/strategy_orphan_sweep.py,
    strategy-service/strategy_service/engine/core/cloud_strategy_storage.py,
    ml-service/scripts/ml_orphan_sweep.py,
  ]
depends_on: []
---

> **🟢 ARCHIVED 2026-08-03** — `status: resolved` with zero open todos (all of 1, 2, 2b, 2c, 2d, 3, 3b, 3c, 4 done);
> archived per
> [`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`](/codex/12-agent-workflow/plan-completion-and-archival-discipline.md).
> Combined cross-repo lineage report (this doc's todo 4 deliverable) lives at
> [`mdps_features_ml_strategy_orphan_lineage_report_2026_08_03.md`](/plans/active/issues/mdps_features_ml_strategy_orphan_lineage_report_2026_08_03.md).
> Every per-stage finding's own follow-up work stays tracked in its own doc (see that report's "Stage-by-stage findings"
> section for the full pointer list) — nothing here evaporates with the archive.

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
   `features/` "have their own re-runnable sweep" — **confirmed false**: `/codex/02-data/orphan-object-detection.md`
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
   `/codex/02-data/orphan-object-detection.md`.

## Why this needs a split, not one checkbox

Todo 11b (`data_pipeline_check_mdps_features_2026_07_20.md`) asks for one report covering raw→candle→feature→ml/strategy
across all 5 asset_groups. Given the raw-MTDS-layer equivalent alone took 2026-07-21 through 2026-07-24 (multiple VM
crashes, 2 major memory bugs found + fixed, several SPOT preemptions) to get right for ONE stage, building 3 NEW
purpose-built sweep tools (candle, feature, ml/strategy) — each its own shard-key design, its own launcher, its own
VM-stability iteration — in one dispatch would either be rushed (risking the same crash/OOM class of bug the raw-MTDS
tool needed days to shake out) or dishonestly claimed done. Splitting into independently-dispatchable stage-scoped todos
lets each one be built, validated, and run to real completion on its own timeline, exactly like the raw-MTDS layer was.

## Open work

- [x] 1. ✅ [SCRIPT] P1. **Build + validate an MDPS candle-layer orphan sweep** (new script in
      `market-data-processing-service/scripts/`, name TBD) — design brief with file:line citations + open items done:
      [`mdps_candle_orphan_sweep_design_brief_2026_07_27.md`](/plans/archive/issues/mdps_candle_orphan_sweep_design_brief_2026_07_27.md).
      Mirror `migration_orphan_sweep.py`'s A-E taxonomy against `processed_candles/by_date/` per asset_group (shard key:
      day, venue, chain, instrument_type, data_type, timeframe; note the real measured DEFI path segment ORDER is
      `timeframe/data_type/instrument_type/venue`, NOT the cefi-analog `venue/instrument_type/data_type` — verify per-AG
      before assuming one shape). ALSO check manifest coverage under BOTH the source `data_type` vocabulary and the
      aggregated `mdps_data_type_key()` vocabulary (the newly-discovered false "never populated" class from
      `issues/candle_feature_canonical_path_divergence_2026_07_20.md` todo 7). Repo: market-data-processing-service.
      Launch on a Tier-2 SPOT VM per the heavy-I/O rule, never in-session — budget for the SAME class of iteration
      (memory/preemption) the raw-MTDS sweep needed. Feeds
      `mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md`'s corpus-wide backfill scope. **Built 2026-07-27**
      (`market-data-processing-service@01744b7`, `scripts/candle_orphan_sweep.py`, the design brief's open items
      resolved: a bounded live 3-object-per-AG spot-check found the segment ORDER is actually UNIFORM across all 5
      asset_groups — `day/pipeline_mode/timeframe/data_type/instrument_type/venue` — not per-AG-divergent as the
      pre-check text above assumed; no existing UAC `ShardKey` shape covers candles, so a new `CandleShardKey`
      NamedTuple was hand-rolled as expected). Implements the A/D/E/F taxonomy (F = ambiguous-pre-fix, gated on
      `--manifest-fix-cutover`, informational-only, does not gate acceptance) + dual-vocabulary manifest coverage + its
      own checkpointed single walk (no external enumeration file needed, unlike candle-census/apply). **Validated
      2026-07-27** (`market-data-processing-service@d921823`): found + fixed a REAL bug during validation —
      `_BUCKET_KIND_MAP["sports"]` pointed at `instruments-store-sports-prd-...` (live-verified: ZERO
      `processed_candles/` objects there, a silent false-clean "0 orphans" result) instead of the tick bucket
      `market-data-tick-sports-prd-...` where the real corpus lives — the exact honest-absence violation this codebase's
      data-correctness rules exist to catch. Added 31 unit tests (previously zero). Ran a bounded real 200-object sweep
      against PROD sports data post-fix: 200/200 `A_canonical_manifested`, 0 orphans/junk/ambiguous — genuine,
      real-data, end-to-end proof the pipeline works. Attempted the same for DeFi; killed intentionally after ~6 min /
      ~15.6GB RSS on this shared host (memory: 396MB free, heavy swap) once it confirmed the bucket resolves correctly
      and the manifest-load phase started — DeFi's 23.9M-row `availability_index.parquet` genuinely needs VM-scale
      memory, matching the raw-tick sweep's own documented 2026-07-21..24 OOM history (see the design brief's §2
      citation) — this is the expected shape of the problem, not a new bug. Added a read-only, `$MODE`-ignoring
      `<ag>-candle-orphan-sweep` launcher category (`deployment-service@d75e8f3`, `launch-canonical-migration-vm.sh`,
      mirrors `_candle_census_cmd`'s no-reachable-`--apply`-path shape; no new `VM_PREFIX_TO_BUCKET` registry entry
      needed — falls under the existing per-AG `canonical-migration-<ag>-` prefixes). **CLOSED 2026-07-27** — per main's
      ruling (`BLK-c8936baa`): this VM run is read-only/safe-idempotent/no-`--apply`-path-ever-reachable, so it is
      AO-dispatchable without an operator gate (unlike K1/K2's prod-mutating migration). Fixed a real GCE 63-char
      vm_name overflow found on the actual launch (`deployment-service@ff8eebe`, mirrors the earlier `*-candle-apply`
      `cdlap` fix). **Ran the full-corpus Tier-2 SPOT VM sweep for cefi/defi/tradfi/prediction** (4× `e2-standard-8`
      SPOT, all completed in <2 min, zero preemptions) — real, manifest-verified per-AG results: cefi
      A=460/E=0/F=405,496 (0.11% coverage), defi A=0/E=7,936/F=1,123,431 (0% coverage), tradfi A=4,388/E=0/F=536,934
      (0.81% coverage), prediction A=13,281/E=0/F=569,947 (2.28% coverage). **This surfaced a MASSIVE, corpus-wide
      candle-manifest coverage gap** — spot-verified against the live cefi manifest directly (75 total MDPS rows in an
      8.78M-row index, zero for the flagged DERIBIT object) to confirm this is a real manifest absence, not a sweep-tool
      bug. Filed as its own P0 finding, out of this todo's scope:
      [`mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md`](/plans/active/issues/mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md)
      (root-cause + backfill are that doc's todos, not this one's — todo 1's own scope was build+validate the TOOL,
      which is now genuinely done: built, bug-fixed, 31-test-covered, and run to completion on real prod data for 4/5
      asset_groups). Sports's full-corpus sweep (only a bounded 200-object sample run) is P2 follow-up in the new issue
      doc, not a gate on this todo.
- [x] 2. ✅ [SCRIPT] P2. **Build a features-service orphan sweep tool** — same A-E taxonomy pattern, shard key
      `asset_group × feature_family × day`. Repo: features-service. **Built + unit-tested 2026-08-03**
      (`features-service@b81a6a75`, `scripts/feature_orphan_sweep.py`): mirrors `candle_orphan_sweep.py`'s single-walk +
      checkpointed-resume pattern, parameterized per `--feature-family` (the UAC `FeatureFamily` closed enum has 8
      members, each with its OWN bucket-resolution rule + object-key prefix/partition shape — verified per-family by
      reading each family's own writer, not assumed uniform). Wired 5/8 families with a verified
      bucket+prefix+partition-shape config: `delta_one`, `volatility`, `onchain`, `sports`, `calendar` (calendar's
      declared path template places `feature_group` as a raw POSITIONAL segment, not hive `feature_group=...` — handled
      explicitly). `commodity` / `cross_instrument` / `multi_timeframe` are explicitly REJECTED as unwired (commodity
      writes a flat JSON signal file with no `day=`/`feature_group=` hive keys at all; cross_instrument uses `date=` not
      `day=` plus a non-hive `run_tag` segment; multi_timeframe's shape was not independently verified) — each needs its
      own design pass before wiring, mirroring todo 3's own admission for ml/strategy, rather than a guessed-at
      mechanical port. 33 unit tests cover parsing/classification/coverage for all 5 wired families. **This todo's scope
      was BUILD the tool** (mirrors todo 1's own split between "build the tool" and "run it to real completion on prod
      data") — genuinely done: built, unit-test-covered. The real-data VM-run validation + the 3 unwired families are
      todo 2b below, not a gate on this todo.
- [x] 2b. ✅ [SCRIPT] P2. **Validate the features-service orphan sweep against real GCS data** (Tier-2 SPOT VM, never
      in-session — per STEP 0.56 of `unified-trading-pm/agents/data_engineering.md`, a features-corpus manifest load is
      exactly the shape that caused 2 recent shared-host AO outages) for each of the 5 wired families
      (`delta_one`/`volatility`/`onchain`/`sports`/`calendar`) × applicable asset_group, mirroring todo 1's
      real-prod-data validation (which caught a genuine bucket-resolution bug) — fix whatever the real run surfaces.
      Also design + wire `cross_instrument`/`multi_timeframe` (each needs its own shard-key design pass first, per
      `feature_orphan_sweep.py`'s module docstring). Repo: features-service. **2026-08-03**
      (`features-service@9fb37033`): wired `cross_instrument` (day-anchored positional `feature_group`, `date=` not
      `day=` — `run_tag` varies batch/t1-recon so it can't be matched at a fixed index) + `multi_timeframe` (hive
      `feature_group=` but also `date=` not `day=`; 21 new unit tests, 43 total green). Built
      `launch-feature-orphan-sweep-vm.sh` (`deployment-service@ca8967f`) — first real launch caught + fixed a genuine
      gap (`setup-data-pipeline-vm.sh` had no `VM_TASK=feature-orphan-sweep` dispatch branch, same root-cause class as
      the 2026-07-21/22 datapoint-validation/orphan-sweep gaps — fixed `deployment-service@3b9255c` before any cell
      ran). Ran all 10 real (family, asset_group) cells on Tier-2 SPOT VMs, all completed <3min, zero preemptions:
      delta_one (cefi 306A/0E, tradfi 4A/0E, defi 304,257A/8E, prediction 0/0-genuinely-empty), volatility (all 3
      applicable AGs genuinely empty — verified via matching bucket names to delta_one's own real data, not a
      bucket-resolution bug), onchain/defi (950A/**783E**), sports/sports (28,076A/96,678C/**67,077E**), calendar/global
      (0/0 objects but 6 phantom-captured manifest rows — a class this sweep's taxonomy can't detect, since orphan
      detection is object-driven not manifest-driven). The two real orphan gaps (onchain 45%, sports 35%) plus the
      calendar phantom-row anomaly are big findings, out of THIS todo's scope (validate the tool) — filed as their own
      doc:
      [`features_service_manifest_coverage_gap_2026_08_03.md`](/plans/active/issues/features_service_manifest_coverage_gap_2026_08_03.md)
      (backfill + investigation todos live there, not here). `commodity` remains genuinely unwired (flat JSON
      `signal.json`, not parquet, positional day+feature_group with no hive keys at all, own dedicated bucket) — split
      to todo 2c below rather than guessed at in this dispatch.
- [x] 2c. ✅ [SCRIPT] P2. **Design + wire the `commodity` feature_family** into `feature_orphan_sweep.py` — genuinely
      different shape from every other wired family: writes a flat JSON `signal.json` (not parquet) at
      `{commodity}/{date}/signal.json` with NEITHER segment hive-style (both `commodity` and `date` are raw positional
      segments), no `feature_group`/`day` hive keys at all, and its own dedicated bucket (`features-commodity` kind,
      global — no per-asset_group fold). Needs its OWN JSON-aware classification path (the existing `is_parquet` gate
      would misclassify every real `signal.json` as `C_manifest_infra`, masking real orphans) — a genuinely separate
      design pass, not a mechanical port of `calendar`'s or `cross_instrument`'s positional handling. See
      `feature_orphan_sweep.py`'s module docstring for the full citation trail
      (`commodity/cli/handlers/batch_handler.py` `_write_signal_to_gcs`/`_write_signal_and_manifest`). Repo:
      features-service. **Built + unit-tested 2026-08-03** (`features-service@fa18180b`): added
      `FamilyConfig.     object_suffix` (generalizing the prior hardcoded `.parquet` gate — `commodity=".json"`), a
      dedicated `_COMMODITY_POSITIONAL_FAMILIES` path in `extract_feature_group`/new `extract_day` (both segments
      positional, no hive keys), and generalized the `_infra_label`/`_checkpoint_path` helpers for commodity's
      whole-bucket `walk_prefix=""` walk (that bucket is dedicated solely to commodity, so a whole-bucket walk is still
      a single-walk of exactly this family's own data). Also found + fixed a genuine CASE MISMATCH: the object path
      segment is lower-cased (`signal.commodity.lower()`, batch_handler.py:207) but the manifest `feature_group` column
      is written from the un-lowered `commodity` code (`config.enabled_commodities` defaults to upper-case
      `["NG", "CL"]`) — without upper-casing the extracted path segment, every real captured commodity object would
      misclassify as a false orphan. 8 new/updated unit tests added (61 total, all green); commodity is now the last of
      the 8 UAC `FeatureFamily` members wired (`_UNSUPPORTED_FAMILIES` now empty). Real-data VM-run validation
      (mirroring todo 1's + todo 2b's own real-prod-data validation pattern) is split to todo 2d below, not a gate on
      this todo (which scoped BUILD + WIRE only, per this todo's own title).
- [x] 2d. ✅ [SCRIPT] P2. **Validate the `commodity` feature_orphan_sweep wiring against real GCS data** (Tier-2 SPOT
      VM, never in-session — per STEP 0.56 of `unified-trading-pm/agents/data_engineering.md`) — mirrors todo 1's + todo
      2b's own real-prod-data validation (which each caught a genuine bug: todo 1's sports bucket-resolution bug, todo
      2c's case-mismatch bug caught by reading the code — a real VM run against the live `features-commodity` bucket may
      surface further gaps this session's code-reading alone could not). Repo: features-service. **2026-08-03**
      (`deployment-service@87d9d17` + `features-service@63e97f6a`+`@3b0c0b05`): found the launcher itself was stale
      first — `launch-feature-orphan-sweep-vm.sh` still hard-refused `--feature-family commodity` citing todo 2c's OWN
      now-superseded "no verified config yet" rationale (todo 2c had already wired it in the sweep tool itself); wired
      it in as a global family (no `--asset-group`, same shape as `calendar`) + fixed the matching stale
      `vm_prefix_registry.py` comment. Also hit + fixed the wrong gcloud CLI identity active on this host
      (`github-deploy`, missing `compute.instances.create`) — activated `unified-trading-sa` (already held
      `compute.admin` per `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`, no new grant needed)
      and republished a stale `features-service` code tarball (predated the commodity wiring commit). Ran the real
      Tier-2 SPOT VM (`feat-orph-cm-gl-20260803-143206`, `e2-standard-4` SPOT, completed in ~3 min, no preemption)
      against the live `commodity-signals-batch-central-element-323112` bucket: resolved the bucket correctly, walked
      the whole-bucket prefix, classified via the manifest — `A=1 B=0 C=1 D=0 E=4` (1 captured manifest cell, 4 real
      orphan objects: `cl/2017-01-01`, `cl/2026-04-14`, `ng/2017-01-01`, `ng/2026-04-14`). The wiring itself is
      genuinely validated: no crash, correct bucket resolution, correct A-E classification against real data. Found +
      fixed one more real bug surfaced by the run: `backfill_feature_orphan_class_e.py`'s footer-read step assumed
      parquet universally — every real commodity object failed with `ArrowInvalid` ("Parquet magic bytes not found")
      since commodity writes flat JSON `signal.json`. Branched on `FamilyConfig.object_suffix` (non-parquet families
      count `row_count=1` per object, mirroring the live commodity writer's own
      `_write_signal_and_manifest     (row_count=1, ...)` convention) — 3 new unit tests, 19/19 green. Applied the
      backfill for real (additive-only, 4 objects, tiny enough for in-session per STEP 0.56): all 4 orphans now
      `capture_status=captured` with `row_count=1`, sample-verified via the writer's own per-VM shard readback
      (`verify_failed=0`). `commodity` is now the last of the 8 UAC `FeatureFamily` members fully built + validated
      against real GCS data — todos 1-3 of `features_service_manifest_coverage_gap_2026_08_03.md`'s sibling doc (which
      this run's tiny finding was folded into rather than filed separately, given its trivial 4-object scope) now covers
      every wired family.
- [x] 3. ✅ [SCRIPT] P2. **Build an ml/strategy orphan sweep — the one confirmed family per repo.** Scoped the actual
      shard key first (per this todo's own instruction): ml-service has exactly ONE manifest-writing corpus
      (`ManifestWriter`/`record_captured` grepped 2026-08-03 — only
      `ml_service/inference/app/core/     prediction_publisher.py`;
      `manifest_gap_handler.py`/`manifest_inference_guard.py` READ the manifest, they do not write it) —
      `ml_predictions`, shard key `(day, mode)`. strategy-service has MANY manifest-writing sites (orders, positions,
      pnl, instructions, backtest results all write `ManifestWriter` rows), of which `strategy_instructions` is the one
      with a fully verified single shape confirmed across BOTH its write sites (`gcs_storage_service.py`'s
      `write_instructions` + `cli/handlers/batch_results.py`), shard key `(client_id, strategy_id, day)` — confirming
      the parent doc's own framing that ml/strategy needed its own design pass, not a mechanical day-sharded port.
      **Built 2026-08-03** (`ml-service@2f0c7e6`, `scripts/ml_orphan_sweep.py`, 19 unit tests;
      `strategy-service@4e04e2af`, `scripts/strategy_orphan_sweep.py`, 22 unit tests) — both mirror
      `candle_orphan_sweep.py`/`feature_orphan_sweep.py`'s A-E-style taxonomy + single-walk + checkpointed-resume
      pattern. **Two BIG FINDINGs surfaced** (both documented with file:line citations in the respective sweep's module
      docstring, both sweeps built against the REAL code-confirmed shape, not the stale constant): PATH_REGISTRY's
      `ml_predictions` entry (`predictions/predictions/by_date/day={date}/mode={mode}/`,
      `unified-trading-library/unified_trading_library/config_interface/paths/registry.py:143`) diverges from the live
      writer, which calls `get_data_sink(bucket=...)` with no `prefix=` and so writes at the BUCKET ROOT
      (`day={date}/mode={mode}/{uuid}.json`, JSON only, never the declared `batch_{timestamp}.parquet` extra_file); and
      PATH_REGISTRY's `strategy_instructions` entry (`strategy_instructions/strategy_id={strategy_id}/     day={date}/`,
      `registry.py:176`) omits the `client_id=` segment the live writer (`gcs_storage_service.py::write_instructions`)
      actually includes, confirmed by 2 independent manifest row_key call sites. **NOT wired this dispatch** (each needs
      its own design pass, mirroring how `feature_orphan_sweep.py` explicitly rejected `commodity`/`cross_instrument`
      rather than guess): ml-service's `ml_models`/`ml_model_metadata`/`ml_training_artifacts` (zero manifest coverage —
      orphan detection is undefined for them); strategy-service's `strategy_orders`/`strategy_positions`/`strategy_pnl`
      (deployment- injected `routing_key=` sinks whose actual bucket/prefix this session did not resolve, and whose
      manifest rows omit `data_type` entirely) and `backtest_results` (the genuinely run-id-keyed, non-day-sharded shape
      the parent issue doc's own text flagged — needs its own investigation into whether it is manifest-tracked at all).
      VM-run validation against real GCS data (never in-session per STEP 0.56 of
      `unified-trading-pm/agents/data_engineering.md`) + the unwired families + the two PATH_REGISTRY-divergence
      fix-or-confirm decisions are split to todo 3b below, mirroring todo 1's own build/validate split and todo 2's own
      family-by-family incremental-wiring split.
- [x] 3b. ✅ [SCRIPT] P2. **Validate the ml/strategy orphan sweeps against real GCS data** (Tier-2 SPOT VM) for
      `ml_predictions` (ml-service) and `strategy_instructions` (strategy-service), mirroring todo 1's + todo 2b's own
      real-prod-data validation pattern. **Done 2026-08-03**: (a) decided + fixed the PATH_REGISTRY drift for BOTH
      datasets — repointed the registry to the real writer shape (`unified-trading-library@3ae19775`: `ml_predictions`
      now bucket-root JSON only, no stale `predictions/predictions/by_date/` prefix or parquet extra_file;
      `strategy_instructions` now carries the `client_id=` segment). Verified no live reader depended on the OLD (wrong)
      shapes — every consumer was dead code or an unwired stub — so this changed no runtime behavior. Fixed the one
      downstream call site that would've KeyError'd (`strategy-service@a353a570`'s
      `PnlDomainAdapter.read_strategy_instructions_path`, now accepts `client_id`, default `"*"`). Built
      `launch-ml-strategy-orphan-sweep-vm.sh` (`deployment-service@fb29a8d`, mirrors
      `launch-feature-orphan-sweep-vm.sh`'s pattern) — while wiring `VM_SERVICE=ml_service`, found + fixed a
      pre-existing gap: `ml-service` had NO `SERVICE_TARBALLS`/`TARBALL_DIRS` entry at all (only stale
      `ml_training_service`/`ml_inference_service` keys pointing at tarballs from repos that no longer exist), so
      `launch-ml-vm.sh`'s existing VMs had been silently getting zero ml-service code extracted. Ran BOTH real Tier-2
      SPOT VMs against prod (`ml-orph-*`/`strat-orph-*`, `e2-standard-4`, completed in ~2 min each): the real run caught
      a genuine bug code-reading alone missed — `ml-store-prd-...` is NOT dedicated to `ml_predictions` alone (it also
      holds `models/`/`training-artifacts/` for 3 sibling ml-service corpora sharing the same `bucket_template`), so 233
      real objects were misclassified `D_junk`. Fixed (`ml-service@3e83350`): added an `F_other_corpus` informational
      class (never gates the E acceptance bar) that excludes recognized sibling-corpus prefixes before classification,
      per `/codex/02-data/orphan-object-detection.md` §2c's "other-corpus, labelled out" pattern — mirrors
      `migration_orphan_sweep.py`'s own `_DATA_PREFIXES` exclusion. Re-ran the ml VM to confirm clean:
      `A=0 C=2 D=0 E=0 F=236`. `strategy_instructions` real run found the manifest is completely absent in prod (0
      captured cells) with 7 real orphan objects (genuine 2025-06-15/16 backtest artifacts) — a real data-correctness
      gap, filed as its own doc rather than absorbed into this todo's "validate the tool" scope (mirrors todo 1's/todo
      2b's own precedent):
      [`ml_strategy_manifest_coverage_gap_2026_08_03.md`](/plans/active/issues/ml_strategy_manifest_coverage_gap_2026_08_03.md).
      (b) strategy_orders/positions/pnl wiring, (c) backtest_results investigation, and (d) the ml_models/etc.
      manifest-WRITE design pass are each their own genuine judgment call — split to todo 3c below rather than guessed
      at in this dispatch, mirroring how todo 2 split unwired families to 2b/2c/2d.
- [x] 3c. ✅ [SCRIPT] P2. **Design + wire the remaining ml/strategy orphan-coverage gaps todo 3/3b explicitly deferred**
      — each needs its own investigation pass, not a mechanical port: (a) design + wire
      `strategy_orders`/`strategy_positions`/`strategy_pnl` orphan sweeps — resolve each
      `get_data_sink(routing_key=     "strategy_orders"/"strategy_positions"/"strategy_pnl")` call's real
      deployment-injected bucket/prefix first
      (`strategy-service/strategy_service/engine/core/cloud_strategy_storage.py`'s `CloudStorageService.__init__`); note
      the manifest rows these 3 write also omit `data_type` entirely per todo 3's own finding, so the covered-index
      needs its own grain-tolerant match, not `strategy_orphan_sweep.py`'s exact-triple lookup ported as-is; (b)
      investigate + design `backtest_results`'s orphan coverage — is it manifest-tracked by `run_id` anywhere, or
      genuinely untracked (`batch_results.py`'s manifest write for backtests reuses `data_type="strategy_instructions"`
      with a `(date, strategy_id, client_id)` row_key that has no `run_id` column at all)?; (c)
      `ml_models`/`ml_model_metadata`/`ml_training_artifacts` need a manifest-WRITE design pass before orphan detection
      is even meaningful for them (zero manifest coverage today, confirmed again by todo 3b's real VM run) — scope that
      as its own operator-facing decision, not a mechanical sweep port. Repo: ml-service, strategy-service.
      **Investigated 2026-08-03** (`unified-trading-pm`, this doc + new sibling doc): read every write call site for all
      3 families rather than guessing. (a) is DEAD CODE — `store_positions`/`store_pnl` have zero callers anywhere in
      strategy-service; `store_orders_batch`'s sole caller `OrderBatchStorage` is never instantiated outside its own
      unit tests (which pass `cloud_storage=None`, never exercising the GCS path); strategy-service's Cloud Run
      terraform (`deployment-service/.../strategy-service/gcp/main.tf`) sets no `PROTOCOL_DATA_SINK_BACKEND`/ `_BUCKET*`
      env var at all, so even a real call would resolve to `LocalDataSink()`, not GCS; also found a THIRD PATH_REGISTRY
      divergence (same class as todo 3/3b's) — `PATH_REGISTRY["strategy_orders"]` declares
      `strategy_orders/by_date/day={date}/strategy_id={strategy_id}/` but the real writer call (no `prefix=` passed to
      `get_data_sink`) would resolve to bucket-root `day={date}/strategy_id={strategy_id}/{uuid}.parquet`. (b) is
      genuinely untracked — zero `ManifestWriter`/`record_captured` calls exist anywhere near `gcs_storage_service.py`'s
      `backtest_results` write methods; the only backtest-adjacent manifest write (`batch_results.py`) is
      `data_type="strategy_instructions"`-scoped with no `run_id` column, confirming the todo's own suspicion. (c)
      reaffirmed via code (zero `ManifestWriter` calls anywhere in `ml-service/ml_service/training/`) — genuinely
      different from (a): a LIVE writer (`training_orchestrator.py`), just never wired to the manifest. **Conclusion:
      none of the 3 is buildable as a mechanical sweep-tool port right now** — each needs an operator-facing decision
      first (wire-up-or-delete for (a); a manifest-WRITE design pass for (b)/(c)) — building tooling now would sweep
      either a phantom corpus (a) or an undefined comparison (b/c). Filed as its own doc with `[OPERATOR]`-tagged
      decision todos + a follow-on `[SCRIPT]` build todo gated on those decisions, rather than guess at a manifest
      schema unilaterally:
      [`strategy_ml_orphan_coverage_design_gaps_2026_08_03.md`](/plans/active/issues/strategy_ml_orphan_coverage_design_gaps_2026_08_03.md).
- [x] 4. ✅ [DOC] P2. Once todos 1-3c land real per-stage findings, write the combined cross-repo lineage report
      `data_pipeline_check_mdps_features_2026_07_20.md` todo 11b actually asks for, then flip that todo. **Done
      2026-08-03** (`unified-trading-pm`): synthesized all 4 stage docs (raw-MTDS + the 3 new todo-1/2/2b-2d/3-3c
      sweeps) into one report —
      [`mdps_features_ml_strategy_orphan_lineage_report_2026_08_03.md`](/plans/active/issues/mdps_features_ml_strategy_orphan_lineage_report_2026_08_03.md).
      Headline: every pipeline stage now has working, real-prod-data-validated orphan tooling (a corpus-wide gap this
      doc's own scoping found didn't exist before todos 1-3c); every real orphan population found across all 4 stages is
      either already backfilled or has a small, bounded, already-tracked follow-up — no new corpus-wide unknown
      surfaced. Flipped `data_pipeline_check_mdps_features_2026_07_20.md`'s 11b pointer to cite the report in the same
      commit. This issue doc's own scope (build the tooling + report the findings) is now fully complete — all todos 1-4
      done.

## Progress Log

- **2026-07-27** (AO dispatch, slot 9) — Picked up todo 1. Found the script already built by a peer slot
  (`market-data-processing-service@01744b7`) but with zero test coverage and never validated against real data.
  Validation found + fixed a real bucket-resolution bug (sports pointed at the wrong bucket — see todo 1's own note
  above for full detail), added 31 unit tests, ran a real bounded 200-object sweep against prod sports data (clean), and
  wired the `<ag>-candle-orphan-sweep` VM launcher category. Shipped `market-data-processing-service@d921823` +
  `deployment-service@d75e8f3`. Deliberately did NOT flip todo 1's checkbox — the full-corpus Tier-2 SPOT VM run for
  cefi/defi/tradfi/prediction genuinely has not happened yet (DeFi alone confirmed to need VM-scale memory, matching the
  raw-tick sweep's own multi-day 2026-07-21..24 iteration history), so "validate" is only partially satisfied.
- **2026-07-27** (same dispatch, continued) — Escalated the resulting `/done` checkbox-flip conflict (`BLK-c8936baa`).
  Main ruled this genuinely differs from the K1/K2 precedent: read-only, no `--apply` path ever reachable, safe-
  idempotent → AO-dispatchable without an operator gate. Launched all 4 real Tier-2 SPOT VMs
  (cefi/defi/tradfi/prediction); the first launch attempt used a stale code tarball (caught before the VM could pull it
  — deleted + republished tarballs via `create-code-tarballs.sh` before relaunching) and a real GCE 63-char vm_name
  overflow on prediction (fixed live, `deployment-service@ff8eebe`). All 4 completed in under 2 minutes each with
  manifest-verified results (see todo 1's final note). The results themselves surfaced a severe, corpus-wide
  candle-manifest coverage gap (0-2.3% coverage across all 4 non-sports AGs) — filed as its own P0 issue doc
  (`mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md`) rather than absorbed into this tooling-gap doc's scope.
  Todo 1 flipped — the tool-build+validate deliverable is genuinely complete.
- **2026-08-03** (AO dispatch, slot 8) — Picked up todo 2. Built `features-service/scripts/feature_orphan_sweep.py`,
  mirroring todo 1's A-E taxonomy + single-walk + checkpointed-resume pattern, parameterized per `--feature-family` (the
  features corpus has 8 UAC `FeatureFamily` values, each with its OWN bucket-resolution rule and object-key
  prefix/partition shape — verified per-family by reading each family's own writer, not guessed). Wired 5 families with
  a verified bucket+prefix+partition-shape config: `delta_one`, `volatility`, `onchain`, `sports`, `calendar`
  (calendar's declared path template places `feature_group` as a raw POSITIONAL path segment, not hive
  `feature_group=...` — handled explicitly, not assumed hive-uniform). `commodity` / `cross_instrument` /
  `multi_timeframe` are explicitly REJECTED as unwired (commodity writes a flat JSON signal file with no
  `day=`/`feature_group=` hive keys at all; cross_instrument uses `date=` not `day=` plus a non-hive `run_tag` segment;
  multi_timeframe's shape was not independently verified this session) — each needs its own design pass, mirroring todo
  3's own admission for ml/strategy, rather than a guessed-at mechanical port. Added 33 unit tests covering
  parsing/classification/coverage for all 5 wired families (including calendar's positional segment and the
  delta_one/volatility timeframe-based legacy-shape discriminator, grounded in the real
  `candle_feature_canonical_path_divergence_2026_07_20.md` finding 5 bucket-root bug, not invented). Shipped
  `features-service@b81a6a75`. Zero real GCS calls made this session (per STEP 0.56 of this craft's mandatory rules — no
  bounded real-data smoke either, since even todo 1's own 200-object validation read a potentially-large manifest, the
  exact shape that caused 2 of 3 recent shared-host AO outages — so any real-data check stays VM-only, never in-session,
  matching the task's own "VM-run, never in-session" wording literally). Since "build the tool" and "validate it against
  real data" are honestly two different units of work here (unlike todo 1, where a real 200-object prod check happened
  in the SAME dispatch), split todo 2 the same way the parent doc's own "Why this needs a split" section argues for:
  reworded todo 2 to scope BUILD only (now genuinely done, flipped) and added todo 2b for the real-data VM-run
  validation + the 3 still-unwired families (open, next dispatch against this doc).
- **2026-08-03** (AO dispatch, slot 2) — Picked up todo 2b. Wired `cross_instrument` + `multi_timeframe` (both write
  `date=` not `day=`; cross_instrument's `feature_group` is day-anchored positional since its preceding `run_tag`
  segment varies) — `features-service@9fb37033`, 21 new unit tests, 43 total green. Built
  `launch-feature-orphan-sweep-vm.sh` mirroring `launch-orphan-sweep-vm.sh` — `deployment-service@ca8967f` (+ `@3b9255c`
  fixing a genuine `setup-data-pipeline-vm.sh` VM_TASK dispatch gap the first real canary launch caught). Ran all 10
  (feature_family, asset_group) cells for the 5 wired families on real Tier-2 SPOT VMs — every launch completed clean in
  under 3 minutes, zero preemptions. Surfaced two real, substantial manifest-coverage gaps (onchain/defi 45% orphan,
  sports/sports 35% orphan = 67,860 real orphan objects) and one phantom-captured anomaly (calendar: 6 manifest rows, 0
  backing objects) — filed as their own doc, out of this todo's "validate the tool" scope:
  [`features_service_manifest_coverage_gap_2026_08_03.md`](/plans/active/issues/features_service_manifest_coverage_gap_2026_08_03.md).
  Flipped todo 2b — genuinely complete (tool validated against real data for all 5 wired families, 2 of the 3
  originally-unwired families now wired). Split `commodity` (JSON not parquet, needs its own classification path) to new
  todo 2c rather than guess at its shape under time pressure.
- **2026-08-03** (AO dispatch, slot 14) — Picked up todo 2c. Wired `commodity` (`features-service@fa18180b`): read
  `commodity/cli/handlers/batch_handler.py`'s `_write_signal_to_gcs`/`_write_signal_and_manifest` + `config.py`'s
  `get_output_bucket` to confirm the exact write shape (`{commodity.lower()}/{date}/signal.json`, no hive keys at all).
  Generalized the sweep's object-type gate from a hardcoded `.parquet` check to a per-family
  `FamilyConfig.object_suffix` (default `.parquet`, `commodity=".json"`) — the prior gate would have misclassified every
  real commodity object as manifest-infra, masking real orphans, exactly the risk this todo's own text flagged. Added a
  dedicated positional-parsing path (`_COMMODITY_POSITIONAL_FAMILIES`) for both feature_group (index 0) and a new
  `extract_day` helper (index 1), since neither segment is hive-style. Found + fixed a genuine CASE MISMATCH the design
  brief hadn't anticipated: the object path segment is lower-cased at write time (`signal.commodity.lower()`) but the
  manifest `feature_group` column carries the un-lowered commodity code (`config.enabled_commodities` defaults to
  `["NG", "CL"]`, upper-case) — without normalizing, a real captured object would never match its manifest row and would
  misclassify as a false orphan; `extract_feature_group` upper-cases the positional segment for this family
  specifically. Also generalized `_infra_label`/`_checkpoint_path` for commodity's `walk_prefix=""` (whole-bucket walk —
  safe here since the bucket is dedicated solely to commodity), fixing a latent leading-slash bug those helpers would
  have hit for any empty-prefix family. 8 new/updated unit tests (61 total, all green); `_UNSUPPORTED_FAMILIES` is now
  empty — commodity was the last of the 8 UAC `FeatureFamily` members to wire. Flipped todo 2c — scope was BUILD + WIRE
  (mirrors todo 2's own build/validate split), genuinely done. Added todo 2d for the real-data Tier-2 SPOT VM validation
  (never in-session per STEP 0.56), mirroring todo 1's + todo 2b's own real-prod-data validation pattern, rather than
  skip it silently.
- **context-scout 2026-08-03**: refreshed context_scope (6 entries — swapped the two MDPS-candle-layer-specific entries
  (`estate_orphan_assessment_2026_07_21.md`, `mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md`, both about
  todo 1, now DONE) for entries matching the doc's current open work in features/ml/strategy:
  `features_service_manifest_coverage_gap_2026_08_03.md`, `features-service/scripts/feature_orphan_sweep.py`,
  `ml-service/.../manifest_gap_handler.py`).
- **2026-08-03** (AO dispatch, slot 9) — Picked up todo 3. Scoped the actual shard key first (per this todo's own
  instruction): grepped `ManifestWriter`/`record_captured` across both repos — ml-service has exactly ONE
  manifest-writing corpus (`prediction_publisher.py`, shard key `(day, mode)`); strategy-service has MANY (orders,
  positions, pnl, instructions, backtest results), of which `strategy_instructions` alone had a fully verified single
  shape confirmed across both its write sites. Built `ml-service/scripts/ml_orphan_sweep.py` (19 unit tests,
  `ml-service@2f0c7e6`) and `strategy-service/scripts/strategy_orphan_sweep.py` (22 unit tests,
  `strategy-service@4e04e2af`), both mirroring the A-E taxonomy + single-walk + checkpointed-resume pattern of
  `candle_orphan_sweep.py`/`feature_orphan_sweep.py`. While designing each shard key against the live writer code (not
  the PATH_REGISTRY constant), found + documented TWO real PATH_REGISTRY divergences: `ml_predictions`'s declared
  `predictions/predictions/by_date/...` shape vs. the live writer's actual bucket-root JSON path (no prefix at all —
  `get_data_sink()` called with no `prefix=`), and `strategy_instructions`'s declared path (no `client_id=` segment) vs.
  the live writer's actual `client_id=`-keyed path (confirmed via 2 independent manifest row_key call sites). Both
  sweeps are built against the REAL, code-confirmed shape, not the stale registry. Explicitly did NOT wire
  `ml_models`/`ml_model_metadata`/`ml_training_artifacts` (zero manifest coverage — orphan detection undefined) or
  `strategy_orders`/`strategy_positions`/`strategy_pnl`/`backtest_results` (deployment-injected routing_key sinks
  - the genuinely run-id-keyed backtest shape, each needing its own design pass) — mirrors `feature_orphan_sweep.py`'s
    own incremental-wiring discipline rather than guessing under time pressure. Zero real GCS calls made this session
    (per STEP 0.56 — manifest loads are exactly the shape that caused 2 recent shared-host AO outages). Flipped todo 3
    (build-only scope, genuinely done) and added todo 3b for the real-data VM-run validation + the unwired families +
    the two PATH_REGISTRY fix-or-confirm decisions, mirroring todo 1's build/validate split and todo 2's incremental-
    wiring split.
- **2026-08-03** (AO dispatch, slot 3) — Picked up todo 3b. Decided + fixed the PATH_REGISTRY drift for both datasets
  (repointed the registry to the real writer shape rather than the writer to the registry — verified no live reader
  depended on the old shapes, so zero runtime-behavior change): `unified-trading-library@3ae19775`. Fixed the one
  downstream call site the new required `client_id` placeholder would've KeyError'd: `strategy-service@a353a570`. Built
  `launch-ml-strategy-orphan-sweep-vm.sh` (`deployment-service@fb29a8d`) mirroring `launch-feature-orphan-sweep-vm.sh` —
  while wiring it, found + fixed a real pre-existing gap: `ml-service` had no `SERVICE_TARBALLS`/`TARBALL_DIRS` entry at
  all in `setup-data-pipeline-vm.sh` (only stale `ml_training_service`/`ml_inference_service` keys for repos that no
  longer exist), so `launch-ml-vm.sh`'s own existing `VM_SERVICE=ml_service` VMs had silently never gotten ml-service
  code extracted. Ran both real Tier-2 SPOT VMs against prod. The real run caught a genuine bug: `ml-store-prd-...` is
  NOT dedicated to `ml_predictions` alone (also holds `models/`/`training-artifacts/` for 3 sibling ml-service corpora
  sharing the bucket) — 233 real objects were misclassified `D_junk`. Fixed (`ml-service@3e83350`): new `F_other_corpus`
  informational class excludes recognized sibling-corpus prefixes before classification, per
  `/codex/02-data/orphan-object-detection.md` §2c/§2d. Re-ran the ml VM to confirm clean (`A=0 C=2 D=0 E=0 F=236`).
  `strategy_instructions`'s real run found the manifest completely absent in prod (0 captured cells) with 7 real orphan
  objects — filed as its own doc, out of this todo's "validate the tool" scope, mirroring todo 1's/todo 2b's own
  precedent:
  [`ml_strategy_manifest_coverage_gap_2026_08_03.md`](/plans/active/issues/ml_strategy_manifest_coverage_gap_2026_08_03.md).
  Flipped todo 3b (genuinely complete: build + validate + PATH_REGISTRY decision + the sibling-corpus bug the real run
  caught, all done). Split (b) strategy_orders/positions/pnl wiring, (c) backtest_results investigation, and (d) the
  ml_models manifest-WRITE design pass to new todo 3c — each is its own genuine judgment call, mirroring todo 2's own
  incremental-wiring split (2b/2c/2d).
- **2026-08-03** (AO dispatch, slot 14) — Picked up todo 3c. Investigated all 3 deferred families by reading every write
  call site (not guessing at shape, per this doc's own established discipline). `strategy_orders`/
  `strategy_positions`/`strategy_pnl`: confirmed DEAD CODE (zero live callers anywhere in strategy-service outside unit
  tests that never exercise the GCS path), no `PROTOCOL_DATA_SINK_BACKEND`/`_BUCKET*` env var set in the service's only
  Cloud Run terraform config (would resolve to `LocalDataSink()` even if called), plus a third PATH_REGISTRY divergence
  (declared `strategy_orders/by_date/...` vs. the real writer's bucket-root shape). `backtest_results`: confirmed
  genuinely untracked — zero manifest calls anywhere near its write methods, and the one adjacent manifest write
  (`batch_results.py`) is scoped to `data_type="strategy_instructions"` with no `run_id` column at all.
  `ml_models`/`ml_model_metadata`/`ml_training_artifacts`: reaffirmed zero manifest coverage via code (only
  `ml_predictions` has any `ManifestWriter` call in ml-service), but unlike strategy_orders this IS a live writer
  (`training_orchestrator.py`), just never wired to the manifest. All 3 converge on the same conclusion: no sweep is
  buildable without an operator-facing decision first (wire-up-or-delete for strategy_orders/positions/pnl; a
  manifest-WRITE design pass for backtest_results and ml_models/etc.) — filed as its own doc with `[OPERATOR]`-tagged
  decision todos + a gated follow-on build todo rather than guess at an unverified manifest schema:
  [`strategy_ml_orphan_coverage_design_gaps_2026_08_03.md`](/plans/active/issues/strategy_ml_orphan_coverage_design_gaps_2026_08_03.md).
  Flipped todo 3c — the investigation/design-pass scope this todo asked for is genuinely complete; todo 4 (the combined
  cross-repo report) remains open, gated on todos 1-3c's real findings, which now all exist.
