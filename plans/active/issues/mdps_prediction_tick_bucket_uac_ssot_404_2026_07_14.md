---
doc_type: issue
title: UAC prediction MARKET_DATA bucket template resolves to a decommissioned 404 bucket (cross-repo SSOT drift)
summary:
  bucket_template(AssetGroup.PREDICTION, BucketKind.MARKET_DATA) still returns the long-form
  market-data-tick-prediction-{env}-{pid}, which is now a decommissioned 404 bucket. The prediction→pred migration
  completed (legacy bucket deleted, pred-prd is the sole live SSOT), so the UAC template's deliberate mid-migration
  guard precondition is met and should be flipped to market-data-tick-pred-{env}-{pid}. Fleet-wide
  (UAC/UTL/MDPS/MTDS/IS).
status: resolved
created: 2026-07-14
assigned_vm: planning
parent_epic: infrastructure_master
resolved_by:
  "unified-api-contracts@511a9c62, unified-trading-library@4378685 (verify-only), market-data-processing-service@5febb77
  — all 5 todos complete"
source:
  - plans/active/sports_data_sources_canonical_completion_2026_07_13.md (todo -022, bug (b))
  - unified-api-contracts/unified_api_contracts/canonical/gcs_paths.py (lines 103-113)
  - plans/archive/2026_07/prediction_manifest_canonicalisation_2026_06_01.md
tags: [prediction, bucket-naming, uac, ssot, cross-repo, mdps]
related:
  - sports_data_sources_canonical_completion_2026_07_13
nature: process
asset_group: cross-cutting
stage: [meta]
repos: []
scope: [engineer, admin]
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-14
locked_by:
---

## What I found

While fixing todo -022 bug (a) in `market-data-processing-service` (PREDICTION `instrument_key` derivation — shipped),
bug (b)'s root cause turned out to be a **cross-repo UAC SSOT drift**, not an MDPS-local bug:

- `unified_api_contracts.canonical.gcs_paths.bucket_template(AssetGroup.PREDICTION, BucketKind.MARKET_DATA)` returns
  **`market-data-tick-prediction-{env}-{project_id}`** (the long-form).
- Live probe (2026-07-14, prod, ADC): that resolves to `market-data-tick-prediction-prd-central-element-323112` which
  now **404s (NotFound — bucket decommissioned)**, while `market-data-tick-pred-prd-central-element-323112`
  **HAS_OBJECTS** (the live, canonical SSOT). UTL's `resolve_bucket_name(kind="market-data-tick-prediction")` and UAC's
  `bucket_template(PREDICTION, INSTRUMENTS)` BOTH already return the abbreviated `pred` token — only the PREDICTION
  MARKET_DATA template still points at the dead long-form bucket.
- The UAC template at `gcs_paths.py:113` carries a **deliberate guard comment** (lines 103-112): it was "LEFT AS THE
  LONG FORM" mid-migration to `pred-prd`, warning that flipping before the migration's `--drop-stale` completed would
  point consumers at the less-complete bucket, and to **"Re-evaluate once that migration's Progress Log confirms
  pred-prd is the sole, complete SSOT."**
- That precondition is now **met**: `prediction_manifest_canonicalisation_2026_06_01.md` is **ARCHIVED (completed)** and
  the legacy bucket is **deleted (404)**, so `pred-prd` is the sole live SSOT.

Consumers of the long-form across the fleet (code + tests): `unified-api-contracts` (gcs_paths + test_gcs_paths_facade),
`unified-trading-library` (cloud_constants, manifest_consolidator, upgrade_manifest_to_v8, detect_manifest_divergence +
3 tests — note `_asset_group_for_market_data_bucket` intentionally maps the long-form to `prediction` for asset-group
inference; verify back-compat before/after the flip), `market-data-processing-service` (dependency_checker
OUTPUT_BUCKETS + UPSTREAM_DEPS + 2 tests), `market-tick-data-service` (migrate_prediction_to_pred_prd_v9 coverage test),
`instruments-service` (enumerate_expected_universe test).

## Why it matters

`DependencyChecker.OUTPUT_BUCKETS["PREDICTION"]` and the `UPSTREAM_DEPS_BY_ASSET_GROUP` prediction-tick template resolve
to a 404 bucket. In `mdps_t1_recon_job` this is currently **masked by `SKIP_DEPENDENCY_CHECK=true`**, so it does not
block candle production today (that was bug (a), now fixed) — but the moment the dependency check is unmasked, or any
other consumer resolves the prediction tick bucket via `bucket_template`, it 404s. It is a latent correctness landmine
on a fleet-wide SSOT that already points at deleted infrastructure. `_resolve_upstream_bucket` in the same MDPS file
already works around it by using the UTL resolver directly — an internal inconsistency that the SSOT flip removes.

## Recommended decision

Flip the UAC template to the abbreviated `pred` token (the migration guard's precondition is verified met), then update
the dependent consumers/tests fleet-wide in one coordinated change. This is the root fix; it strictly improves
correctness (the old target is already deleted, so nothing can regress to it). Verify UTL's dual-name back-compat
recognition (`_asset_group_for_market_data_bucket`) is preserved for reading any legacy-named references before
flipping.

- [x] ✅ [SCHEMA] P1. Flip `(AssetGroup.PREDICTION, BucketKind.MARKET_DATA)` in `canonical/gcs_paths.py` from
      `market-data-tick-prediction-{env}-{project_id}` to `market-data-tick-pred-{env}-{project_id}`, and replace the
      stale mid-migration guard comment with a note that the migration completed (legacy bucket deleted 2026-07-12, plan
      `prediction_manifest_canonicalisation_2026_06_01.md` archived). (repo: unified-api-contracts) —
      unified-api-contracts@511a9c62.
- [x] ✅ [SCHEMA] P1. Update `tests/unit/test_gcs_paths_facade.py` PREDICTION MARKET_DATA expectation to the `pred`
      token. (repo: unified-api-contracts) — unified-api-contracts@511a9c62 (same commit; required to keep QG green
      after the template flip). Supplementary: unified-api-contracts@41827a6e adds an explanatory comment on the
      PREDICTION MARKET_DATA parametrize case matching the existing INSTRUMENTS-case convention.
- [x] ✅ [BACKEND] P1. Re-verify + update UTL prediction-bucket references and their tests (`cloud_constants.py`,
      `manifest_consolidator.py`, `upgrade_manifest_to_v8.py`, `detect_manifest_divergence.py`, `test_bucket_naming.py`,
      `test_cloud_constants.py`, `test_manifest_consolidator.py`) — KEEP `_asset_group_for_market_data_bucket`
      recognizing BOTH tokens for back-compat asset-group inference. (repo: unified-trading-library) —
      **unified-trading-library@4378685**. Re-verified: NO code change needed. All 4 named UTL modules resolve the
      prediction market-data bucket via `resolve_bucket_name(kind="market-data-tick-prediction")`, which reads the
      SEPARATE `unified_api_contracts/config/cloud-providers.yaml` kind-map SSOT — not the `canonical/gcs_paths.py`
      `bucket_template()` per-(AssetGroup,BucketKind) dict item -001 flips. Confirmed live in the packaged yaml
      (`cloud-providers.yaml:160,326`): `market-data-tick-prediction` already maps to
      `market-data-tick-pred-${DEPLOYMENT_ENV_SHORT}-${...}` on BOTH GCP and AWS — unaffected by the gcs_paths.py
      drift/flip. `_asset_group_for_market_data_bucket`'s regex (`manifest_consolidator.py:392`,
      `r"market-data-tick-(cefi|defi|tradfi|sports|prediction|pred)\b"`) already recognizes both tokens (back-compat
      preserved, tests at `test_manifest_consolidator.py:1602-1614` pass unchanged). `test_bucket_naming.py` /
      `test_cloud_constants.py` already assert the abbreviated `pred` token for the resolved bucket name.
      `quality-gates.sh` full run GREEN (580s), sentinel = HEAD, tree unmodified.
- [x] ✅ [BACKEND] P2. Update MDPS `test_dependency_checker_sports_prediction.py` +
      `test_consolidator_preflight_sports.py` to assert the `pred` token now that OUTPUT_BUCKETS/UPSTREAM_DEPS resolve
      via the flipped UAC template. (repo: market-data-processing-service) — **market-data-processing-service@5febb77**.
      Updated 4 assertions in `test_dependency_checker_sports_prediction.py` (`test_prediction_in_output_buckets`,
      `test_get_output_bucket_prediction`, `test_prediction_mtds_bucket`,
      `test_prediction_dep_check_passes_when_present`) that test `OUTPUT_BUCKETS`/`UPSTREAM_DEPS_BY_ASSET_GROUP` — the
      path that calls `bucket_template()` directly and was affected by the flip. `test_consolidator_preflight_sports.py`
      needed **NO change** — its PREDICTION tests
      (`test_prediction_calls_assert_consolidator_healthy_for_both_flat_kinds`) mock `resolve_bucket_name` and assert on
      the `kind=` yaml-key argument (`"market-data-tick-prediction"`), the same already-correct yaml-key path as todo 3
      — unaffected by the `gcs_paths.py` dict flip. 46/46 MDPS tests green; also re-ran 17 UAC + 18 UTL
      prediction-scoped tests, all green (no regressions). `quality-gates.sh` full run GREEN, sentinel = HEAD
      (`3d889a7`→amended `5febb77` for the Quickmerge trailer).
- [x] ✅ [DATA] P2. Update the long-form assertions in `market-tick-data-service`
      `test_migrate_prediction_to_pred_prd_v9_coverage.py` and `instruments-service`
      `test_enumerate_expected_universe.py` (they reference the now-deleted legacy bucket as `LEGACY` — keep as an
      explicit legacy constant or update per the flip). (repo: market-tick-data-service, instruments-service) —
      **Re-verified: NO code change needed.** `test_migrate_prediction_to_pred_prd_v9_coverage.py`'s
      `LEGACY =     "market-data-tick-prediction-test-project"` constant tests the **migration script's**
      move-FROM-legacy logic (`migrate_prediction_to_pred_prd_v9.py`) — a standalone script taking explicit bucket-name
      arguments, not routed through `bucket_template()`; keeping it as an explicit legacy constant (the issue doc's own
      suggested option) is correct since the script's job is specifically to move data OUT of that bucket.
      `test_enumerate_expected_universe.py` already asserts the canonical `pred-{tier}-` shape and explicitly asserts
      `pred != "market-data-tick-prediction-test-project"` — its `_default_bucket_for("prediction")` resolves via
      `resolve_bucket_name(kind="market-data-tick-prediction")`, the same already-correct yaml-key path as todos 3/4's
      verification. 91 MTDS + 14 IS tests in the named files re-ran green, confirming no regression from the flip.
      Follow-up (independent concurrent verification): landed doc-only comment clarifications so both files no longer
      read as stale — `test_enumerate_expected_universe.py`'s "slated for L6 delete" comment now says "deleted
      2026-07-12"; `test_migrate_prediction_to_pred_prd_v9_coverage.py`'s `LEGACY` constant now carries an explicit
      comment stating it is the intentional historical migration-source name, not the live UAC SSOT. No assertions
      changed (none were needed). — instruments-service@0a1f13e9, market-tick-data-service@9ed52332.
