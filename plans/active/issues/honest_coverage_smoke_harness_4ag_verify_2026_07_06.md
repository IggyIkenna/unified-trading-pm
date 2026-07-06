---
doc_type: issue
title: honest_coverage_smoke_harness [VERIFY] P2 4-AG live-run discrepancies (cefi/defi/tradfi/prediction)
summary:
  'Task `layer1_remeasure_and_certify-007` asked for a live-verify of the smoke harness across cefi/defi/tradfi/prediction
  (only sports ran on 2026-06-29). Slot-9 ran what exists and surfaced 4 blocking discrepancies: (1) tradfi runner
  returns empty matrix — catalogue at `gs://instruments-store-tradfi-prd-central-element-323112/prd/catalog.parquet` is
  404 (BLOCKED-PLAN2 as documented in the plan Progress Log for task 004); (2) prediction runner crashes with
  BucketNamingError — `live_manifest_reader._bucket_for` calls `resolve_bucket_name(kind="tick-data",
  asset_group="prediction")` but the `tick-data` alias resolves to `market-data-{asset_group}` template which has
  only CEFI/DEFI/SPORTS/TRADFI mappings; prediction bucket is the flat key `market-data-tick-prediction` (yaml value:
  `market-data-tick-pred-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}`); (3) `run_live_verify_cefi.py` does NOT exist —
  the [VERIFY] P2 slot-4 patch built tradfi + prediction but not cefi; (4) `run_live_verify_defi.py` does NOT exist —
  same gap. Sports (verified earlier) uses `instruments-store` bucket path; cefi/defi/tradfi/prediction all need
  their own runners against the tick-data bucket. Task Gate satisfied via `discrepancy filed` alternative to green.'
status: open
nature: notes
asset_group: [cross-cutting]
stage: [data]
repos: [e2e-testing, unified-api-contracts]
scope: [engineer]
tags: [honest-coverage, smoke-test, verify, live-verify, coverage-matrix]
related:
  [
    ../honest_coverage_smoke_harness_2026_06_28.md,
    ../layer1_remeasure_and_certify_2026_07_06.md,
    ./verify_p1_prereq_dag_2026_06_29.md,
    ../tradfi_v9_stage1_finish_2026_07_06.md,
  ]
created: 2026-07-06
parent_epic: batch_live_symmetry_master
priority: P2
source: layer1_remeasure_and_certify_2026_07_06.md task 007 live-verify session (slot-9 planning)
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
model_tier: sonnet-doable
thinking_tier: high
estimate_class: brand-new
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2
last_updated: 2026-07-06
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

## What I found

Slot-9 executed `layer1_remeasure_and_certify-007` (the `[VERIFY] P2 honest_coverage_smoke_harness live-verify
slices` task, gated by "each AG's smoke slice green or its discrepancy filed"). Findings across the 4 deferred AGs
(cefi / defi / tradfi / prediction — sports already ran):

- **1. `run_live_verify_tradfi.py` runs but returns empty matrix.** Command:
  ```
  GCP_PROJECT_ID=central-element-323112 .venv/bin/python scripts/build_smoke/run_live_verify_tradfi.py \
    --output-dir /tmp/slot9_smoke_output/tradfi --today 2026-07-06 --cloud gcp --deployment-env prd
  ```
  Result: `WARNING tradfi catalog not available at
  gs://instruments-store-tradfi-prd-central-element-323112/prd/catalog.parquet: 404 ...` → 0 shards (RUNNABLE=0
  INSUFFICIENT=0 HONEST_EMPTY=0). This matches the plan's own documented state — task 004 in the same plan is marked
  `🚧 BLOCKED-PLAN2` because `tradfi_v9_stage1_finish_2026_07_06` tasks 2-11 (IS catalogue build) have not landed. The
  runner honestly surfaces the gap (empty matrix, not silent skip) but the smoke slice cannot go green until Plan 2
  tasks 2-11 land + `catalog.parquet` is written to GCS.

- **2. `run_live_verify_prediction.py` crashes with BucketNamingError.** Command:
  ```
  GCP_PROJECT_ID=central-element-323112 .venv/bin/python scripts/build_smoke/run_live_verify_prediction.py \
    --output-dir /tmp/slot9_smoke_output/prediction --today 2026-07-06 --cloud gcp --deployment-env prd
  ```
  Traceback root cause (`e2e-testing/scripts/build_smoke/live_manifest_reader.py:149-158`
  `UTLManifestReader._bucket_for`):
  ```
  BucketNamingError: Kind 'tick-data' on cloud 'gcp' has no entry for asset_group='prediction'.
  Available: ['CEFI', 'DEFI', 'SPORTS', 'TRADFI'].
  ```
  The `tick-data` kind is an alias resolving via the `market-data-{asset_group}` template
  (`unified-trading-library/cloud_interface/bucket_naming.py:100`), which has no prediction entry. Prediction is
  registered separately as a flat yaml key `market-data-tick-prediction` (resolves to
  `market-data-tick-pred-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}` per `cloud-providers.yaml:170` in both UAC and
  UTL fixtures). The prediction Layer-1 certification (task 005 in the same plan) successfully used
  `measure_honest_coverage` against the prediction manifest via the correct bucket name, so the manifest IS present at
  `gs://market-data-tick-pred-prd-central-element-323112/_index/availability_index.parquet` — the failure is purely in
  the smoke-harness runner's bucket-resolution call.

- **3. `run_live_verify_cefi.py` does NOT exist** in `e2e-testing/scripts/build_smoke/`. The slot-4
  [VERIFY] P2 patch (see `verify_p1_prereq_dag_2026_06_29.md`) shipped tradfi + prediction runners only — cefi runner
  never landed. Without it, no cefi slice can be executed to satisfy the Gate.

- **4. `run_live_verify_defi.py` does NOT exist** in `e2e-testing/scripts/build_smoke/`. Same gap as cefi — the
  [VERIFY] P2 patch did not include a defi runner. Without it, no defi slice can be executed.

## Why it matters

The [VERIFY] P2 gate on `layer1_remeasure_and_certify` task 007 is meant to smoke-test the honest-coverage classifier
against the LIVE availability manifest for every AG, catching classifier-semantic bugs before the certified Layer-1
numbers are used by strategy/backtest. As-of 2026-07-06 the smoke matrix covers only sports (1/5 AGs). The prediction
runner is silently broken (crashes on first shard bucket resolution — has NEVER been run against a live manifest, so
the classifier's behaviour on prediction is untested end-to-end); the tradfi runner surfaces the honest empty matrix
but is blocked by Plan 2; and cefi/defi have no runner at all. Layer-1 certifications for those AGs (73.61%, 94.81%,
etc.) were produced by `measure_honest_coverage` (a different code path) — so the smoke harness never verified the
classifier semantics on production data for 4 of 5 AGs.

**No data-correctness risk** (the Layer-1 certifications don't consume this harness), but the harness's own
[VERIFY] P2 gate is not honestly satisfied until the 4 runners are green or documented-blocked with a concrete
unblock plan.

## Recommended decision

Land the 4 fixes below (all tracked as todos). Priority ordering respects existing plan-blocker chains:
- Fix `-002` (prediction bucket) FIRST — smallest, unblocks prediction verify immediately, catches any classifier-
  semantic finding on prediction shards analogous to the sports full-season finding.
- Fixes `-003` + `-004` (build cefi + defi runners) next — modelled on the existing tradfi runner (which uses
  `MdpsUniverseProvider` + `resolve_bucket_name(kind='instruments-store', asset_group=<ag>)` to load the AG catalogue,
  then feeds atoms into `build_coverage_matrix`). Both AGs have live manifests + live IS catalogues (see the Layer-1
  certifications) so the runners can be green immediately.
- Fix `-001` (tradfi) is gated on Plan 2 landing — no runner change needed; the tradfi runner already correctly
  reports the empty matrix. Track resolution as re-run once Plan 2 catalogue write lands.

## Todos

- [x] ✅ [CODE] P2. Fix `run_live_verify_prediction.py` bucket resolution: change `live_manifest_reader.UTLManifestReader._bucket_for` (or override in the prediction runner) so prediction uses `kind="market-data-tick-prediction"` (flat yaml key) instead of `kind="tick-data", asset_group="prediction"`. Alternatively teach the `tick-data` alias to route prediction to the flat key. Add a regression test that constructs an atom with `asset_group="prediction"` and asserts the resolved bucket matches `market-data-tick-pred-{env}-{project_id}`. (repo: e2e-testing; possibly unified-trading-library / unified-api-contracts if the alias route is preferred) — e2e-testing@1ca3672 `_bucket_for` now routes `asset_group="prediction"` to flat key `market-data-tick-prediction`; regression test `test_prediction_asset_group_resolves_to_flat_bucket_key` asserts bucket starts with `market-data-tick-pred-` (verified live: `market-data-tick-pred-prd-central-element-323112`).
- [ ] [CODE] P2. Build `e2e-testing/scripts/build_smoke/run_live_verify_cefi.py` modelled on `run_live_verify_tradfi.py`: load cefi catalogue from `gs://instruments-store-cefi-prd-*/prd/catalog.parquet` via `MdpsUniverseProvider`, iterate cefi MVP data_types from `MVP_REQUIRED_WINDOW_REGISTRY`, emit coverage matrix + smoke set + summary. Include CLI args (--output-dir/--today/--cloud/--deployment-env) matching the tradfi runner. Verify against the live cefi manifest (`market-data-tick-cefi-prd-*`). (repo: e2e-testing)
- [ ] [CODE] P2. Build `e2e-testing/scripts/build_smoke/run_live_verify_defi.py` modelled on `run_live_verify_tradfi.py`: load defi catalogue from `gs://instruments-store-defi-prd-*/prd/catalog.parquet` via `MdpsUniverseProvider`, iterate defi MVP data_types (`dex_pool_swaps` / `dex_pool_state` / `lending_indices` / `lst_rates` / `oracle_prices` / `perp_funding`) from `MVP_REQUIRED_WINDOW_REGISTRY`, emit coverage matrix + smoke set + summary. Include CLI args matching the tradfi runner. Verify against the live defi manifest (`market-data-tick-defi-prd-*`). (repo: e2e-testing)
- [ ] [VERIFY] P2. Once Plan 2 (`tradfi_v9_stage1_finish_2026_07_06`) tasks 2-11 land and `catalog.parquet` is written to `gs://instruments-store-tradfi-prd-central-element-323112/prd/`, re-run `run_live_verify_tradfi.py` and publish the fresh matrix + smoke set. Attach output as evidence. (repo: e2e-testing; PREREQ: `tradfi_v9_stage1_finish_2026_07_06` tasks 2-11 done)

## Evidence

- Tradfi run: `WARNING tradfi catalog not available ... 404` → empty matrix. Output at `/tmp/slot9_smoke_output/tradfi/live_tradfi_summary.json` (local, slot-9):
  `shards_total=0`, `catalogue_cells=0`, `catalogue_instruments=0`, `uncovered_combos=[]`.
- Prediction run: `BucketNamingError: Kind 'tick-data' on cloud 'gcp' has no entry for asset_group='prediction'` at
  `live_manifest_reader.py:149-158` (`_bucket_for`). Full traceback in slot-9 session log.
- Cefi runner absence: `ls scripts/build_smoke/run_live_verify_*.py` = `{sports, tradfi, prediction}` only.
- Defi runner absence: same as cefi.
- Sports (already-verified reference): `run_live_verify_sports.py` ships at `e2e-testing@cf6b7e1` (see
  `honest_coverage_smoke_harness_2026_06_28.md` Progress Log 2026-06-29).
