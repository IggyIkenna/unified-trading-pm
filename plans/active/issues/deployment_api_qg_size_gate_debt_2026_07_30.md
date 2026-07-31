---
doc_type: issue
title: Decompose deployment-api's 27 pre-existing size-gate violations (unmasked by base-service.sh STEP 5.5z)
summary:
  "unified-trading-pm's base-service.sh STEP 5.5z (qg_size_gate_sentinel_skip_root_cause_2026_07_25.md P0 fix, landed
  2026-07-30) moved the file/function/class/method size checks out of the CODEX_MAX_VIOLATIONS aggregate-tolerance pool
  into a zero-tolerance hard gate. This turned deployment-api's LDR→main promotion PR #430 quality-gates-v2 red: 6 files
  over MAX_FILE_LINES (900) and ~45 functions/methods over MAX_FUNCTION_LINES/MAX_METHOD_LINES, none of them new — all
  silently absorbed for weeks/months by CODEX_MAX_VIOLATIONS=5. Unblocked immediately (ldr_qg_failure escalation
  agt-46da69) by adding all 27 affected files to FUNCTION_SIZE_EXTRA_EXCLUDES (deployment-api/scripts/quality-gates.sh),
  the same sanctioned per-repo allow-list mechanism strategy-service already uses for analogous legacy debt — this is a
  stopgap, not a fix; the actual decomposition work is this doc."
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [deployment-api]
scope: [engineer]
tags: [code-quality, function-size, file-size, qg-ratchet, quality-gates, deployment-api]
related:
  - /plans/archive/issues/qg_size_gate_sentinel_skip_root_cause_2026_07_25.md
created: 2026-07-30
last_updated: 2026-07-30
parent_epic: deployment_and_user_management_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 1.2
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
depends_on: []
source:
  "ldr_qg_failure escalation agt-46da69 (deployment-api#430, 2026-07-30) — CI wall fix filed the decomposition as its
  own follow-up per findings-triage (outside-plan, real work, not folded into the one-shot CI-fix scope)."
---

# Decompose deployment-api's 27 pre-existing size-gate violations

## Why this doc exists

Today's `base-service.sh` STEP 5.5z change (see `qg_size_gate_sentinel_skip_root_cause_2026_07_25.md`) made the
file/function/class/method size checks a zero-tolerance hard gate instead of a `CODEX_MAX_VIOLATIONS`-tolerated class.
deployment-api was one of the 9 repos flagged in that doc's P0 finding as carrying a nonzero `CODEX_MAX_VIOLATIONS` (5)
that was masking real size debt. Re-measuring locally (same AST/byte-count logic as `base-service.sh`) at LDR HEAD
found:

**File-size violations (>900 lines):**

- `deployment_api/routes/deployments_inventory.py` — 2592 L
- `deployment_api/routes/health_consolidator.py` — 1082 L
- `deployment_api/services/data_status/manifest.py` — 1131 L
- `deployment_api/services/data_status/mtds.py` — 1059 L
- `deployment_api/services/cost_observability/service.py` — 1055 L
- `deployment_api/routes/data_status/_live_coverage.py` — 920 L

**Function/method/class-size violations (>200/50/900 lines respectively):** ~45 functions/methods across 24 files, worst
offenders `deployment_api/services/data_status/manifest.py:_build_manifest_category()` (360L),
`deployment_api/services/data_status/instrument_coverage.py:per_instrument_coverage()` (364L),
`deployment_api/services/data_status/sports_helpers.py:sports_honest_coverage()` (300L),
`deployment_api/services/deploy_missing_launch.py:launch_deploy_missing_vm()` (236L),
`deployment_api/routes/deployment_state.py:refresh_deployment_status_sync()` (234L),
`deployment_api/services/data_status/mtds.py:mtds_honest_coverage_for_venue()` (220L). Full per-file list in the
`FUNCTION_SIZE_EXTRA_EXCLUDES` comment block, `deployment-api/scripts/quality-gates.sh` (2026-07-30 commit).

**Immediate unblock (done, see Progress Log)**: all 27 files added to `FUNCTION_SIZE_EXTRA_EXCLUDES` — the same per-repo
allow-list mechanism `strategy-service/scripts/quality-gates.sh` already uses for its own legacy engine/risk modules.
This restores `quality-gates-v2` to green without touching a coverage floor or pragma-skipping anything, but it means
these 27 files are now EXEMPT from the size gate entirely (both dimensions, since one `find` feeds both checks) — any
further growth inside them will not be caught until this doc's decomposition work removes them from the exclude list
file-by-file.

## Acceptance

- [x] ✅ [SCRIPT] P1. **DONE 2026-07-31 (slot-2, infra craft)** — `deployment-api@75584a8` (split) +
      `deployment-api@17361fd` (exclude-list cleanup). Decomposed `deployment_api/routes/deployments_inventory.py`
      (2592L) into a 6-module facade package
      (`deployments_inventory/{__init__,_classification,_registry_io,     _mock_data,_aggregation,_routes}.py`, every
      module <900L), mirroring the 2026-06-11 `routes/deployments` precedent (pure code motion). The precedent's own
      docstring ("patched module-level collaborators resolved through the facade module at call time") turned out to be
      load-bearing here: `tests/mocks.py`'s `patch_inventory_secondary_census` + ~120 `patch()`/`patch.object()` call
      sites across `test_route_deployments_inventory.py` and 8 other test files target
      `deployment_api.routes.     deployments_inventory.<name>` directly (27 distinct "seam" collaborators — `_cfg`,
      `get_storage_client`, `_load_registry_entries`, `CostObservabilityService`, etc.) — every submodule resolves these
      via `import ... as _inv; _inv.<name>(...)` at call time rather than a direct import, so the existing patch surface
      keeps intercepting regardless of which file now defines/calls the seam. Verified empirically, not just by
      inspection: all 186 tests across every consuming test file pass unchanged; `basedpyright`/`ruff` clean (fixed 2
      real gaps found along the way — 120 `reportPrivateUsage` cross-submodule accesses needing
      `# pyright: ignore[reportPrivateUsage]` per the same precedent convention, and 4 `pool.map(lambda ...)` call sites
      losing type inference through the `_inv.` indirection, fixed by replacing the lambdas with explicitly-typed nested
      functions); full `quality-gates.sh` green both before and after removing the now-obsolete
      `FUNCTION_SIZE_EXTRA_EXCLUDES` entry (confirmed `✅ File size OK` with the exclude removed).
- [x] ✅ [SCRIPT] P1. **2026-07-31 (slot-5, infra craft)** — `deployment-api@0b4c6a8`. Extracted the named
      `_build_manifest_category()` (360L) + its data_type-grouping/MTDS-annotation helpers into a NEW sibling module
      `manifest_category_builder.py`, inserted into the mixin chain between `missing_shards` and `manifest` (pure code
      motion; updated the chain-description docstring in all 9 sibling mixin files for consistency). Decomposed the 360L
      method itself down to ~20 small helper methods, EVERY ONE ≤50L (the real `MAX_METHOD_LINES` gate, not just the
      file-size cap) — `manifest_category_builder.py` needs NO exclude-list entry at all. `manifest.py` itself shrank
      1131L→683L. Verified: 257 tests green
      (`test_data_status_service.py`/`test_data_status_turbo.py`/`test_data_status_beta_rollup_and_cli_config.py`),
      `basedpyright` clean (only 3 pre-existing errors remain, confirmed byte-identical against origin before this
      change — not introduced by this decomposition), full `quality-gates.sh` green. **2026-07-31 (slot-8, infra craft)
      — `deployment-api@a42a57e`**: decomposed the remaining 4 oversized methods (`get_manifest_status` 147L,
      `_get_manifest_status_sync` 132L, `_dispatch_category_builds` 102L, `_live_build_fallback` 71L) into a NEW sibling
      `manifest_status_helpers.py` (`ManifestStatusHelpersMixin`, inserted between `manifest_category_builder` and
      `manifest`), using two small dataclasses (`_ManifestBuildRequest`, `_CategoryBuildContext`) to bundle the ~10
      params travelling together across the internal call chain so every extracted method's own signature stays short.
      `run_bounded` / `ThreadPoolExecutor` / `slice_rollup_to_window` call sites stayed physically in `manifest.py` —
      `tests/unit/test_data_status_service.py` / `tests/unit/services/test_manifest_source.py` /
      `tests/unit/test_data_status_beta_rollup_and_cli_config.py` patch each by the literal module path
      `deployment_api.services.data_status.manifest.<name>`, which only intercepts a bare-name lookup resolved through
      the PATCHED module's own globals — moving those specific calls would have silently stopped the patches from taking
      effect (caught empirically: an early draft moved `mtds_expected_dates_for_venue_dt`-style logic and broke 2
      seeded-denominator tests the same way on the sibling `mtds.py` todo above). Also respected the mixin chain's
      ordering invariant (an earlier link can never call a method defined only on a later one) when deciding which leaf
      helpers were safe to move. Updated one test (`test_both_pools_cap_fan_out_with_max_build_workers`) whose
      `inspect.getsource()` assertion targeted the now-split-out pool-instantiation code — same regression-guard intent,
      now sourced from the two dispatch-leg methods that actually contain it. `manifest.py`'s
      `FUNCTION_SIZE_EXTRA_EXCLUDES` entry REMOVED — both the 900L file-size gate and the 50L method-size gate now pass
      natively for `manifest.py` (577L) and the new `manifest_status_helpers.py` (346L). Full `quality-gates.sh` green
      (5052 tests pass, 0 regressions).
- [x] ✅ [SCRIPT] P1. Decompose `deployment_api/services/data_status/mtds.py` (1059L, contains the 220L
      `mtds_honest_coverage_for_venue()`). Remove its exclude entry once compliant. — deployment-api@a483514: split into
      `mtds_meta.py` (category/PREDICTION metadata), `mtds_defi_alias.py` (DEFI alias maps + canonicaliser),
      `mtds_expected.py` (expected-venues/-dates helpers), `mtds_dt_entries.py` (per-dt coverage-entry builders);
      `mtds.py` (376L) stays the re-export facade every caller/test imports from. `mtds_honest_coverage_for_venue`
      shrunk 220L → ~150L (venue-row filtering + per-dt dispatch extracted to `mtds_dt_entries.py`, but the
      `mtds_expected_dates_for_venue_dt()` call itself stays inline in `mtds.py` so the existing `unittest.mock.patch`
      target in `tests/unit/test_data_status_seeded_4state_denominator.py` keeps intercepting it).
      `FUNCTION_SIZE_EXTRA_EXCLUDES` entry for `mtds.py` removed. Full `quality-gates.sh` green (5052 tests pass, 0
      regressions).
- [x] ✅ [SCRIPT] P1. **DONE 2026-07-31 (slot-2, infra craft)** — `deployment-api@fc093fd`. Decomposed
      `deployment_api/services/cost_observability/service.py` (1055L, 6 oversized methods) into 5 sibling modules:
      `row_builders.py` (DuckDB-cell coercion + generic `BreakdownRow` builders: `_agg_row`/`_grouped`/`_by_sku`/
      `_by_day`/`_finalize_rows`, all stateless), `resource_rows.py` (the resource/bucket/waste dimension's SQL fetch +
      storage-class/cost-component aggregation + row assembly — the pure-data half of `_by_resource`),
      `stopped_vm_disk.py` (the `stopped_vm_disk` waste kind's query + row builder), `summary_rows.py` (`summarize()`'s
      per-cloud aggregation + `CloudSummary` row assembly), `breakdown_dimensions.py` (`breakdown()`'s per-dimension
      dispatch — the 148L method, the largest offender). Every extracted function is a pure function of its explicit
      arguments (no `self`); the 4 live-GCP waste cross-ref methods (`_unattached_disk_names` et al) +
      `_waste_cross_refs()` stayed instance methods on `CostObservabilityService` (need `self._cfg` + a
      `ThreadPoolExecutor` fan-out) and are passed into the extracted dispatch functions as bound callables. Kept every
      previously-private method NAME as a thin delegating wrapper on the class (`_by_resource`,
      `_stopped_vm_disk_waste_rows`, `breakdown`, `summarize`, `per_resource_daily`) so `waste.py`'s
      `cost_observability.service._stopped_vm_disk_waste_rows` cross-reference and every `unittest.mock.patch`/
      `svc.<name>` test target (`_cost_component`, `_AVG_DAYS_PER_MONTH`, `_BREAKDOWN_LIMIT`, `gcp_facts`/`aws_facts`/
      `github_facts`/`list_unattached_disk_names` et al) kept working unchanged — re-exported the two svc-attribute-
      tested private names (`_cost_component`, `_AVG_DAYS_PER_MONTH`) via `__all__` per the `mtds.py` facade convention.
      Cross-module private-name imports (`_f`/`_s`/`_agg_row`/etc.) needed `# pyright: ignore     [reportPrivateUsage]`
      per import, same as the `deployments_inventory` precedent. `FUNCTION_SIZE_EXTRA_EXCLUDES` entry removed. Verified:
      full `quality-gates.sh` green both before AND after the exclude removal (`✅ File size     OK`,
      `✅ Function/class/method size OK`, 5052 tests pass — 0 regressions, incl. every `test_cost_observability.py`
      case; basedpyright warn-only errors unchanged from pre-existing baseline, confirmed not a regression).
- [x] ✅ [SCRIPT] P1. **DONE 2026-07-31 (slot-5, infra craft)** — `deployment-api@c11f56f`. Decomposed
      `deployment_api/routes/health_consolidator.py` (1082L) into a 6-module facade package
      (`health_consolidator/{__init__,_models,_classify,_catalog,_reads,_mock}.py`, every module ≤523L), mirroring the
      2026-07-31 `deployments_inventory` precedent. Every module-qualified seam the test suite patches by name
      (`resolve_bucket_name` / `get_storage_client` / `consolidated_blob_age_sec` / `per_vm_shard_backlog` /
      `per_vm_shards_exist` / `read_availability_index` / `_compute_consolidator_health` — all patched as
      `deployment_api.routes.health_consolidator.<name>` in `tests/unit/test_route_health_overview.py`) stayed
      physically in the facade `__init__.py` (`_ag_health`, `_consolidator_health`, `_build_consolidators`,
      `object_delta_for_bucket`, the stale-while-revalidate cache, and the route handler) rather than using the
      `deployments_inventory`-style `_inv.`-indirection trick, since none of the patch-sensitive functions needed to
      move — everything extracted (pydantic models, freshness/verdict classification, catalog loading, per-bucket
      cheap-read helpers, the mock-mode estate) takes its GCS client as a plain argument, never reads the module-level
      collaborator off its own globals. Verified: full `quality-gates.sh` green (5052 tests pass, 0 regressions,
      `✅ File size OK`, `✅ Function/class/method size OK`); `FUNCTION_SIZE_EXTRA_EXCLUDES` entry for
      `health_consolidator.py` removed from `deployment-api/scripts/quality-gates.sh`.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-31 (slot-2, infra craft)** — `deployment-api@16403d1`. Split the 3 independent
      endpoint groups into sibling modules (pure code motion, mirroring the `mtds.py`/`manifest.py` precedents):
      `_live_coverage.py` (575L, keeps `/live`), `_live_coverage_honest.py` (147L, new, `/honest-coverage`),
      `_live_coverage_venue_year.py` (236L, new, `/venue-year-coverage`). All three keep resolving patched collaborators
      through the package facade (`_ds`) at call time, so every existing test-patch target
      (`deployment_api.routes.data_status.<name>`) kept intercepting unchanged — confirmed via a pre-check of every test
      file's `patch()` targets (all facade-qualified or original-library-qualified, none `_live_coverage`- internal).
      Verified: 112 targeted endpoint tests green, full `quality-gates.sh` green (5052 tests, 0 regressions, native
      `✅ File size OK` / `✅ Function/class/method size OK` with the `FUNCTION_SIZE_EXTRA_EXCLUDES` entry removed).
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-31 (slot-2, infra craft) — split from the original combined
      breakdowns_core.py+breakdowns_domain.py todo per this doc's own "one todo per file" note.** Extracted helpers from
      the 6 oversized methods in `deployment_api/services/data_status/breakdowns_core.py` (`_build_single_venue_entry`
      127L, `_build_feature_group_breakdown_uac` 95L, `_build_instrument_type_breakdown` 110L,
      `_build_underlying_breakdown` 70L, `_build_data_type_breakdown` 112L, `_classify_data_type_for_venue` 100L — the
      last was 65 lines of docstring over 34 lines of real logic; trimmed the docstring instead of splitting logic).
      `deployment-api@2efb2a0`: 8 new helper methods (mechanical, pure code motion — every extracted line moved
      verbatim, no logic changes), each named for what it builds (`_build_base_venue_entry`,
      `_apply_type_dimension_breakdown`, `_apply_optional_venue_dimensions`, `_expected_feature_group_entries`,
      `_unexpected_feature_group_entries`, `_build_single_instrument_type_entry`, `_nest_underlying_or_data_type`,
      `_apply_child_weighted_aggregation`, `_build_single_underlying_entry`, `_build_single_data_type_entry`,
      `_resolve_data_type_expected_dates`, `_split_actionable_vs_blocked`). Also de-duplicated
      `capture_status_counts`/`counts` (two identical dict literals) into one shared dict under two keys.
      `breakdowns_core.py`'s `FUNCTION_SIZE_EXTRA_EXCLUDES` entry removed — both file-size (899L) AND function-size
      gates now pass natively. Verified: 331 targeted tests green, basedpyright shows only the 2 pre-existing errors
      (confirmed byte-identical against baseline), full `quality-gates.sh` green (5052 tests, 0 regressions). Repo:
      deployment-api.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-31 (slot-2, infra craft).** Extracted helpers from the 8 oversized methods in
      `deployment_api/services/data_status/breakdowns_domain.py` (`_build_league_breakdown`,
      `_build_defi_sub_dimension_breakdown`, `_build_chain_breakdown`, `_build_feature_group_breakdown`,
      `_build_underlying_grouping`, `_build_data_type_grouping`, `_build_sports_entity_entry`,
      `_build_v4_sub_dimensions`), same mechanical pure-code-motion pattern as the `breakdowns_core.py` sibling above.
      `deployment-api@7013ab3`: file 894L (started 895L; extraction grew it past the 900L cap mid-work, recovered by
      condensing docstrings), zero methods over `MAX_METHOD_LINES=50`. Hit and fixed one MRO name collision along the
      way — `_build_single_underlying_entry` already existed on `CoreBreakdownsMixin` (a subclass of
      `DomainBreakdownsMixin` in this file's inheritance chain), silently shadowing the new same-named helper and
      calling the wrong 7-arg method with 8 args; renamed to `_build_single_underlying_grouping_entry` and verified no
      other new helper name collides anywhere in the mixin chain. `breakdowns_domain.py`'s
      `FUNCTION_SIZE_EXTRA_EXCLUDES` entry removed — both file-size and function-size gates now pass natively. Verified:
      267 targeted tests green (incl. the two test files that `patch.object()` `_build_sports_entity_entry` and
      `_build_v4_sub_dimensions` by name), basedpyright clean, full `quality-gates.sh` green (102s). Repo:
      deployment-api.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-31 (slot-2, infra craft).** Decomposed the function-size-only violation in
      `deployment_api/routes/deployment_state.py` (`refresh_deployment_status_sync()`, was 234L).
      `deployment-api@a3524df`: extracted `_refresh_cloud_run_batch_shards`, `_vm_zones_for_shards`,
      `_refresh_vm_shards_in_zone`, `_refresh_vm_shards`, `_flag_succeeded_shards_with_log_errors` — pure code motion,
      no logic changes; main function now ~55L. `FUNCTION_SIZE_EXTRA_EXCLUDES` entry removed — gate passes natively.
      Verified: 92 targeted tests green (`test_deployment_state_helpers.py`, `test_route_deployment_state.py`,
      `test_deployment_state_service.py`), basedpyright clean, ruff clean, full `quality-gates.sh` green (104s). Repo:
      deployment-api.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-31 (slot-2, infra craft).** Decomposed
      `deployment_api/services/artifact_pipeline/service.py` (`ArtifactPipelineService.health()`, was 165L).
      `deployment-api@2898e2f`: extracted each of the 7 independent condition checks (`_live_failed_condition`,
      `_recent_failed_builds_condition`, `_duplicate_builds_condition`, `_floating_tag_condition`,
      `_hand_deployed_condition`, `_tarball_lane_condition`, `_registry_sprawl_condition`, plus the always-on
      `_aws_not_read_condition`) into named module-level functions returning `HealthCondition | None`, filtered into the
      conditions list — pure code motion, no logic changes. `FUNCTION_SIZE_EXTRA_EXCLUDES` entry removed — gate passes
      natively. Verified: 46 targeted tests green (`tests/unit/api/test_artifact_pipeline.py`), basedpyright clean, ruff
      clean, full `quality-gates.sh` green (121s). Repo: deployment-api.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in
      `deployment_api/services/data_analytics_service.py`. Remove its exclude entry once compliant; re-run
      `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in
      `deployment_api/services/data_query_service.py`. Remove its exclude entry once compliant; re-run
      `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in `deployment_api/services/data_status/cli.py`.
      Remove its exclude entry once compliant; re-run `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in
      `deployment_api/services/data_status/coverage.py`. Remove its exclude entry once compliant; re-run
      `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in
      `deployment_api/services/data_status/defi.py`. Remove its exclude entry once compliant; re-run `quality-gates.sh`
      to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in
      `deployment_api/services/data_status/instrument_coverage.py` (`per_instrument_coverage()`, 364L). Remove its
      exclude entry once compliant; re-run `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in
      `deployment_api/services/data_status/sports.py`. Remove its exclude entry once compliant; re-run
      `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in
      `deployment_api/services/data_status/sports_helpers.py` (`sports_honest_coverage()`, 300L). Remove its exclude
      entry once compliant; re-run `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in
      `deployment_api/services/data_status/venue_resolution.py`. Remove its exclude entry once compliant; re-run
      `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in
      `deployment_api/services/deploy_missing_launch.py` (`launch_deploy_missing_vm()`, 236L). Remove its exclude entry
      once compliant; re-run `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in
      `deployment_api/services/deployment_manager.py`. Remove its exclude entry once compliant; re-run
      `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in `deployment_api/services/deployment_state.py`
      (a different file from `routes/deployment_state.py` above — same basename, different directory). Remove its
      exclude entry once compliant; re-run `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in `deployment_api/services/event_processor.py`.
      Remove its exclude entry once compliant; re-run `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in `deployment_api/services/state_manager.py`.
      Remove its exclude entry once compliant; re-run `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in `deployment_api/services/sync_service.py`.
      Remove its exclude entry once compliant; re-run `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in
      `deployment_api/services/tarball_staleness.py`. Remove its exclude entry once compliant; re-run `quality-gates.sh`
      to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in `deployment_api/utils/path_combinatorics.py`.
      Remove its exclude entry once compliant; re-run `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P3. Once every file above is decomposed and removed from `FUNCTION_SIZE_EXTRA_EXCLUDES`, re-measure
      `CODEX_MAX_VIOLATIONS` honestly (currently 5) and ratchet it down if the size class was the only thing keeping it
      non-zero — verify actual `V` via `QG_SLICE=lint-codex`, don't guess.

## Progress Log

- 2026-07-30 (slot 14, ldr_qg_failure escalation agt-46da69): Root-caused via the already-filed
  `qg_size_gate_sentinel_skip_root_cause_2026_07_25.md` P0 entry (base-service.sh STEP 5.5z, same-day change) — this is
  fleet-wide exposure, deployment-api being one of 9 flagged repos. Confirmed locally (direct AST/byte-count
  re-measurement, same logic as the gate) that all 27 violations are pre-existing, not introduced by PR #430 or any
  recent deployment-api commit. Unblocked the promotion PR by adding all 27 files to `FUNCTION_SIZE_EXTRA_EXCLUDES` in
  `deployment-api/scripts/quality-gates.sh` — verified locally: `✅ File size OK` / `✅ Function/class/method size OK` /
  `✅ ALL QUALITY GATES PASSED`. Filed this doc for the real decomposition work per findings-triage (outside the
  one-shot CI-fix scope). Not assigning `assigned_vm: planning` yet per the default-human rule — an operator/main-agent
  call on whether to AO-dispatch this (each todo above is independently bounded/deterministic once split further, so it
  would likely qualify, but that's a destination decision this escalation role doesn't make unilaterally).
- **na-eligibility-audit 2026-07-31**: RECLASSIFY, conflict-cleared (infra tranche, dispatch agt-676f1e) — this doc's
  own 2026-07-30 entry above already flagged every todo as independently bounded/deterministic and deferred only the
  destination call, which this audit exists to make. Conflict-check run against
  `parent_epic: deployment_and_user_management_master` (no other active `assigned_vm: planning` doc in this epic) + the
  infra tranche's consolidated-closeout digest: zero overlap, clear to proceed. Flipped `assigned_vm: NA -> planning`,
  `execution_scope: local-only -> orchestrator-agent`. Also split the final bundled "remaining function-size-only
  violators" todo (19 files in one checkbox) into 19 one-file todos, per this doc's own "one todo per file recommended
  when this doc is worked... split at dispatch time if promoted to `assigned_vm: planning`" note — total open todo count
  is now 27 (was 9), still well under the 10-100 authoring cap.
- 2026-07-31 (slot-2, infra craft): Flipped todo 1 — decomposed `deployment_api/routes/deployments_inventory.py` (2592L,
  the largest offender) into a 6-module facade package. See the flipped checkbox above for the full evidence chain
  (patch-surface mapping, basedpyright/ruff fixes, test verification). `deployment-api@75584a8` (split) +
  `deployment-api@17361fd` (removed the now-obsolete `FUNCTION_SIZE_EXTRA_EXCLUDES` entry, re-verified `✅ File size OK`
  with it gone). 8 P1/P2 decomposition todos remain open for follow-up dispatch.
- 2026-07-31 (slot-8, infra craft): Flipped todo 3 — decomposed `deployment_api/services/data_status/mtds.py` (1059L)
  into `mtds_meta.py` / `mtds_defi_alias.py` / `mtds_expected.py` / `mtds_dt_entries.py`, keeping `mtds.py` (376L) as
  the re-export facade every existing caller + test imports from unchanged. Also shrunk `mtds_honest_coverage_for_venue`
  from 220L to under the 200L function-size gate. First full-QG pass surfaced 2 genuine regressions
  (`tests/unit/test_data_status_seeded_4state_denominator.py`'s
  `unittest.mock.patch.object(_dss_mod, "mtds_expected_dates_for_venue_dt", ...)` stopped intercepting calls once that
  call moved into the new `mtds_dt_entries.py` module — `patch.object` only affects the attribute on the patched module,
  not a same-named import bound into a different module's globals) — fixed by keeping the
  `mtds_expected_dates_for_venue_dt()` call physically inside `mtds.py`'s own function body and only extracting the
  seeded/derived dispatch + count bookkeeping into `mtds_dt_entries.py` helpers that take `expected_dates` as a
  parameter. Re-verified: `deployment-api@a483514`, full `quality-gates.sh` green (5052 tests pass, `✅ File size OK`,
  `✅ Function/class/method size OK`, 0 regressions). 7 P1/P2 decomposition todos remain open for follow-up dispatch.
- 2026-07-31 (slot-5, infra craft): Flipped todo — decomposed `deployment_api/routes/health_consolidator.py` (1082L)
  into a 6-module facade package. See the flipped checkbox above for the full evidence chain (which functions stayed in
  the facade to preserve the test-patch surface, verification detail). `deployment-api@c11f56f`. 6 P1/P2 decomposition
  todos remain open for follow-up dispatch.
- 2026-07-31 (slot-8, infra craft): Completed todo 2 (previously PARTIAL) — decomposed `manifest.py`'s last 4 oversized
  methods into a new `manifest_status_helpers.py` sibling, removing `manifest.py`'s `FUNCTION_SIZE_EXTRA_EXCLUDES` entry
  entirely. See the flipped checkbox above for the full evidence chain (mock.patch call-site constraints, the
  mixin-ordering invariant, the dataclass-bundling technique used to keep every extracted method under 50L).
  `deployment-api@a42a57e`. 6 P1/P2 decomposition todos remain open for follow-up dispatch.
- 2026-07-31 (slot-2, infra craft): Flipped todo 4 — decomposed `deployment_api/services/cost_observability/service.py`
  (1055L, 6 oversized methods incl. the 148L `breakdown()`) into 5 sibling modules (`row_builders.py`/
  `resource_rows.py`/`stopped_vm_disk.py`/`summary_rows.py`/`breakdown_dimensions.py`); see the flipped checkbox above
  for the full evidence chain. Rebased onto 2 peer decompositions (`health_consolidator.py`@c11f56f,
  `manifest.py`@a42a57e) mid-task with no conflicts. `deployment-api@fc093fd`. 21 P2 decomposition todos remain open for
  follow-up dispatch.
- 2026-07-31 (slot-2, infra craft): Flipped the `_live_coverage.py` todo — split into 3 sibling modules by endpoint
  (`_live_coverage.py`/`_live_coverage_honest.py`/`_live_coverage_venue_year.py`, 575L/147L/236L). See the flipped
  checkbox above for the full evidence chain (patch-surface pre-check, verification detail). `deployment-api@16403d1`.
  20 P2 decomposition todos remain open for follow-up dispatch.
