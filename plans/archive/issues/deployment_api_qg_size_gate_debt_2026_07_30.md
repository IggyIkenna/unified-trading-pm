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
status: resolved # (was: open) 2026-07-31 — all 27 files decomposed, FUNCTION_SIZE_EXTRA_EXCLUDES now empty
nature: issue
asset_group: [ci] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
stage: [meta]
repos: [deployment-api]
scope: [engineer]
tags: [code-quality, function-size, file-size, qg-ratchet, quality-gates, deployment-api]
related:
  - /plans/archive/issues/qg_size_gate_sentinel_skip_root_cause_2026_07_25.md
  - /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md
created: 2026-07-30
last_updated: 2026-07-31 # status flipped resolved -- 0 open todos remain, closing fix deployment-api@2658beb
parent_epic: deployment_and_user_management_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 1.2
assigned_role: infra
drift_direction: advance-code
resolved_by: deployment-api@2658beb
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
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-31 (slot-2, infra craft).** Decomposed 3 oversized methods in
      `deployment_api/services/data_analytics_service.py`. `deployment-api@1653b36`: extracted
      `_completion_rate_stats`/`_build_recommendations` from `analyze_data_patterns()` (was 57L) and
      `_aggregate_one_service` from `aggregate_multi_service_status()` (was 80L); trimmed `get_data_status_turbo()`'s
      docstring (was 53L, all size from the docstring). Pure code motion, no logic changes.
      `FUNCTION_SIZE_EXTRA_EXCLUDES` entry removed — gate passes natively. Verified: 106 targeted tests green
      (`test_data_analytics_service.py`, `test_route_data_status_live.py`), basedpyright clean, ruff clean, full
      `quality-gates.sh` green (145s; one earlier run was SIGTERM'd by the shared-host RAM-pressure watchdog, unrelated
      to this change — clean retry confirmed it). Repo: deployment-api.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-31 (slot-2, infra craft).** Decomposed 6 oversized methods in
      `deployment_api/services/data_query_service.py`. `deployment-api@8b2b8ee`: extracted `_partition_gcs_objects` from
      `list_files_in_path` (was 78L), `_venue_filters_for_asset_group` from `get_venue_filters` (was 67L),
      `_filter_instrument_corpus` from `get_instruments_list` (was 74L), `_dedupe_and_sort_matches` from
      `search_instruments` (was 86L), `_date_range_strs` + `_availability_rows` from `_check_daily_availability` (was
      60L), `_resolve_effective_window` + `_build_availability_response` from `get_instrument_availability` (was 74L) —
      pure code motion + docstring condensing, no logic changes. `FUNCTION_SIZE_EXTRA_EXCLUDES` entry removed — gate
      passes natively. Verified: 127 targeted tests green (`test_data_query_service_helpers.py`,
      `test_data_query_service.py`, `test_route_data_status_live.py`); basedpyright's 2 remaining errors confirmed
      pre-existing (byte-identical against origin, same 2 lines before this change); ruff clean; full `quality-gates.sh`
      green (187s). Repo: deployment-api.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-31 (slot-2, infra craft).** Decomposed 4 oversized methods in
      `deployment_api/services/data_status/cli.py`. `deployment-api@f84a8c3`: extracted `_append_cli_filter_flags` from
      `_build_cli_cmd` (was 59L), `_execute_cli_subprocess` from `run_data_status_cli` (was 58L),
      `_last_updated_for_category` from `get_last_updated_info` (was 60L), `_build_completeness_validation` +
      `_extract_venues_list` from `validate_data_completeness` (was 87L) — pure code motion, no logic changes.
      `FUNCTION_SIZE_EXTRA_EXCLUDES` entry removed — gate passes natively. Verified: 249 targeted tests green
      (`test_data_status_service.py`, `test_route_data_status_live.py`,
      `test_data_status_beta_rollup_and_cli_config.py`, `test_data_status_helpers.py`), basedpyright clean, ruff clean,
      full `quality-gates.sh` green (124s). Repo: deployment-api.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-31 (slot-2, infra craft).** Decomposed 5 oversized methods in
      `deployment_api/services/data_status/coverage.py`. `deployment-api@d7e42ab`: extracted
      `_coverage_summary_guarded_build` from `get_coverage_summary` (was 86L), `_stale_coverage_response` +
      `_refused_coverage_response` from `_coverage_summary_fallback` (was 72L), `_compute_capture_status_counts` +
      `_out_of_window_empty_count` + `_completion_pct` + `_assemble_coverage_entry` from `_build_coverage_for_cat` (was
      145L, the largest single method decomposed in this doc so far), and `_fold_cat_entry_into_totals` from
      `_get_coverage_summary_sync` (was 71L); trimmed `_build_breakdowns`'s docstring (was 57L). Pure code motion +
      docstring condensing, no logic changes — the OOW/4-state/legacy-coercion business-rule comments were preserved
      verbatim on their new homes, not summarised away. `FUNCTION_SIZE_EXTRA_EXCLUDES` entry removed — gate passes
      natively. Verified: 346/347 targeted tests green (the 1 "failure" — `test_thread_pool_disabled_forces_serial` — is
      a pre-existing test-order/global-state pollution issue, confirmed passing in isolation, not a regression from this
      change), basedpyright clean, ruff clean, full `quality-gates.sh` green (158s, full suite doesn't hit the
      isolated-test-order issue). Repo: deployment-api.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-31 (slot-2, infra craft).** Decomposed the oversized method in
      `deployment_api/services/data_status/defi.py` (`_read_defi_merged_index()`, was 107L). `deployment-api@cfd1b8b`:
      extracted `_resolve_defi_main_bucket`, `_collect_defi_index_frames`, and `_postprocess_defi_merged_index` — pure
      code motion, no logic changes. `FUNCTION_SIZE_EXTRA_EXCLUDES` entry removed — gate passes natively. Verified: 252
      targeted tests green (`test_data_status_service.py`, `test_data_status_turbo.py`,
      `test_v4_sub_dimensions_chain_gated_on_defi.py`, `test_chain_breakdown_shards_vs_dates.py`); basedpyright's 5
      remaining errors confirmed pre-existing (byte-identical against origin, same 5 lines before this change); ruff
      clean; full `quality-gates.sh` green (153s). Repo: deployment-api.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-31 (slot-2, infra craft).** Decomposed
      `deployment_api/services/data_status/instrument_coverage.py` (`per_instrument_coverage()`, was 364L — the single
      largest offender listed in this doc's own header). `deployment-api@92f2d41`: extracted
      `_scoped_expected_instruments`, `_split_legacy_and_current_rows`, `_legacy_fallback_entry`,
      `_compute_found_shards`, `_per_instrument_expected_and_count`, `_count_found_shards`,
      `_missing_instruments_and_counts`, `_per_instrument_breakdown` — each extracted block kept fully intact (no code
      split mid-mask-computation) specifically to preserve the review-confirmed pandas index-alignment invariants this
      function's own comments document (bug #2/#3/#4, "2 of 3 reviews independently" caught an index-misalignment bug
      from a prior refactor attempt). Pure code motion + docstring condensing (was 109 lines), no logic changes.
      `FUNCTION_SIZE_EXTRA_EXCLUDES` entry removed — gate passes natively. Verified: 204 targeted tests green, including
      `test_mdps_timeframe_aware_honest_coverage.py` (the exact suite for the documented index-alignment-bug class) and
      `test_per_instrument_cefi_is_provider.py` (the CEFI live-catalog path) — both pass unchanged, positive evidence
      the extraction preserved the subtle invariants; basedpyright's 12 remaining errors confirmed identical message-set
      against origin (diff empty when line numbers stripped); ruff clean; full `quality-gates.sh` green (113s). Repo:
      deployment-api.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-31 (slot-2, infra craft).** Decomposed the oversized method in
      `deployment_api/services/data_status/sports.py` (`_get_reference_expected_dates()`, was 57L).
      `deployment-api@47a63ed`: extracted `_resolve_upstream_bucket` + `_read_upstream_venue_dates` — pure code motion,
      no logic changes. `FUNCTION_SIZE_EXTRA_EXCLUDES` entry removed — gate passes natively. Verified: 246 targeted
      tests green (`test_data_status_turbo.py`, `test_data_status_service.py`), basedpyright clean, ruff clean, full
      `quality-gates.sh` green (137s). Repo: deployment-api.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-31 (slot-2, infra craft).** Decomposed
      `deployment_api/services/data_status/sports_helpers.py` (`sports_honest_coverage()`, was 300L).
      `deployment-api@1a578a6`: the function's existing per-`SportsAxis` if/elif chain was already a clean dispatch
      boundary, so extracted `_sports_entity_rows` (row-filtering) + one helper per axis
      (`_honest_coverage_per_feature`, `_honest_coverage_global_trigger`, `_honest_coverage_per_league_trigger`,
      `_honest_coverage_global`, `_honest_coverage_per_league`) + `_bucket_match_league_coverage` (the periodic-cadence
      bucket-match fix). Pure code motion, no logic changes. Fixed 2 basedpyright regressions the extraction introduced
      along the way: typed `expected_leagues` as `list[LeagueDefinition]` (was inferring `Any` once it crossed a
      function boundary) and kept `meta` as `dict[str, object]` rather than `dict[str, Any]` in the helper signatures —
      both confirmed via a stash-diff against origin (0 errors before, 26 after the first pass, 0 after the fix).
      `FUNCTION_SIZE_EXTRA_EXCLUDES` entry removed — gate passes natively. Verified: 212 targeted tests green
      (`test_coverage_drift.py`, `test_coverage_drift_worker.py`, `test_data_status_service.py`,
      `test_features_sports_per_feature_axis.py`, `test_teams_per_league_axis.py`), basedpyright clean, ruff clean, full
      `quality-gates.sh` green (120s). Repo: deployment-api.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-31 (slot-2, infra craft).** Decomposed 2 oversized methods in
      `deployment_api/services/data_status/venue_resolution.py`. `deployment-api@b94bc25`: extracted
      `_has_data_type_column`/`_maybe_reference_expected_dates`/`_sports_reference_fixture_calendar`/
      `_build_one_venue_entry` from `_build_venue_breakdown` (was 94L), and
      `_cefi_instruments_provider_for_category`/`_mtds_honest_coverage_for_one_venue`/
      `_apply_honest_coverage_to_all_venues`/`_fold_honest_coverage_into_venue`/
      `_fold_legacy_only_venue`/`_base_venue_entry` from `_apply_mtds_honest_coverage` (was 181L) — pure code motion +
      docstring condensing, no logic changes. `FUNCTION_SIZE_EXTRA_EXCLUDES` entry removed — gate passes natively.
      Verified: 430 targeted tests green (broad set given this shared mixin's blast radius —
      `test_data_status_service.py`, `test_mdps_timeframe_aware_honest_coverage.py`,
      `test_mtds_honest_coverage_for_bookmaker.py`, `test_oow_denominator.py`, `test_data_status_turbo.py`, + 9 more),
      basedpyright clean, ruff clean, full `quality-gates.sh` green (128s). Repo: deployment-api.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-31 (slot-2, infra craft).** Decomposed
      `deployment_api/services/deploy_missing_launch.py` (`launch_deploy_missing_vm()`, was 236L).
      `deployment-api@b703131`: extracted `_validate_deploy_missing_row_key`, `_inflight_launch_result`,
      `_run_tarball_freshness_gate`, `_dry_run_launch_result`, `_build_launcher_env`, `_run_launcher_subprocess` — each
      maps to one step of the function's own documented 8-step launch sequence. Pure code motion, no logic changes.
      `FUNCTION_SIZE_EXTRA_EXCLUDES` entry removed — gate passes natively. Verified: 23 targeted tests green
      (`test_deploy_missing_launch.py`), basedpyright clean, ruff clean (3 pre-existing `# noqa` format warnings
      confirmed unchanged via stash-diff), full `quality-gates.sh` green (162s). Repo: deployment-api.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-31 (slot-2, infra craft).** Decomposed 3 oversized methods in
      `deployment_api/services/deployment_manager.py`. `deployment-api@efdbe42`: extracted
      `_calculate_shards_or_raise`/`_resource_requirements_for_compute` from `calculate_quota_requirements` (was 98L);
      `_validate_deployment_request_full`/ `_calculate_and_normalise_shards` from `create_deployment` (was 127L); and
      `_log_deployment_failure`/`_submit_deployment`/`_maybe_warn_cross_region_egress`/
      `_resolve_deployment_image_and_job`/`_call_create_deployment` from `run_deployment_background` (was 155L). Pure
      code motion, no logic changes. `FUNCTION_SIZE_EXTRA_EXCLUDES` entry removed — gate passes natively. Verified: 103
      targeted tests green (`test_deployment_manager.py`, `test_route_deployments.py`,
      `test_route_deployments_mock.py`), basedpyright clean, ruff clean, full `quality-gates.sh` green (100s). Repo:
      deployment-api.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-31 (slot-2, infra craft).** Decomposed
      `deployment_api/services/deployment_state.py` (services-dir file, distinct from `routes/deployment_state.py`
      above). Condensed `list_deployments()`'s 13-line Args/Returns docstring to one line (was 52L); extracted
      `_extract_shards`/`_shard_status_counts`/ `_extract_date_range`/`_build_status_response` from
      `get_deployment_status()` (was 64L). Pure code motion + docstring condensing, no logic changes.
      `FUNCTION_SIZE_EXTRA_EXCLUDES` entry removed — gate passes natively. Verified: AST size check clean, basedpyright
      0 errors, ruff clean, 269 targeted tests green (`test_deployment_caching.py`, `test_deployment_state_reader.py`,
      `test_deployment_state_service.py`, `test_deployments_helpers.py`, `test_route_deployments.py`,
      `test_route_deployments_mock.py`, `test_route_ordering_inventory.py`, `test_service_status_checkers.py`), full
      `quality-gates.sh --no-fix` green (136s, sentinel `efdbe42b30efe09a1e99d873a44b1096d28fbce1`). Repo:
      deployment-api@6fca1a4.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-31 (slot-2, infra craft).** Decomposed
      `deployment_api/services/event_processor.py`. Extracted
      `_update_one_shard_vm_status`/`_apply_shard_event_status`/`_apply_shard_vm_status` from `process_vm_updates` (was
      71L); extracted `_collect_orphan_tuples`/`_fire_orphan_cleanup`/ `_resolve_orphan_cancel_backend` from
      `process_orphan_vm_cleanup` (was 57L) and the former `_fire_orphan_cleanup` (was 53L). Pure code motion, no logic
      changes. `FUNCTION_SIZE_EXTRA_EXCLUDES` entry removed — gate passes natively. Verified: AST size check clean,
      basedpyright 0 errors, ruff clean, 161 targeted tests green (`test_event_processor_service.py`,
      `test_sync_service.py`, `test_event_processor.py`), full `quality-gates.sh --no-fix` green (145s, sentinel
      `1e824699d21451babceadf3d65ce5a570339ce85`). Repo: deployment-api@867d88e.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-31 (slot-2, infra craft).** Decomposed `deployment_api/services/state_manager.py`.
      Extracted `_new_lock_payload`/`_upload_lock_payload`/`_renew_existing_lock` from `try_acquire_deployment_lock`
      (was 73L); extracted `_maybe_delete_expired_state` from `cleanup_state_ttl` (was 64L). Pure code motion, no logic
      changes. `FUNCTION_SIZE_EXTRA_EXCLUDES` entry removed — gate passes natively. Verified: AST size check clean,
      basedpyright 0 errors, ruff clean, 500 targeted tests green run individually per-file (whole-batch collection hit
      a pre-existing circular-import artifact confirmed to reproduce identically on origin HEAD before this change —
      `test_state_manager.py` 43, `test_state_manager_service.py` 25, `test_deployments_helpers.py` 62,
      `test_deployment_state_service.py` 34, `test_sync_service.py` 77, `test_route_deployments.py` 73,
      `test_route_deployment_state.py` 40, `test_background_sync.py` 20, `test_log_analysis.py` 26,
      `test_deployment_worker.py` 13, `test_local_state_manager.py` 27, `test_deployment_processor.py` 60), full
      `quality-gates.sh --no-fix` green (106s, sentinel `1db91b064cac0fcd9dee415fd78e8243aa584c90`). Repo:
      deployment-api@b68758a.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-31 (slot-2, infra craft).** Decomposed `deployment_api/services/sync_service.py`.
      Extracted `_try_acquire_quota_batch`/`_build_shard_orchestrator`/`_launch_acquired_shards` from
      `_acquire_and_launch` (was 76L); extracted `_finalize_and_save_deployment` from `_process_deployment_locked` (was
      56L); extracted `_process_active_states_parallel` from `sync_deployments` (was 55L). Pure code motion, no logic
      changes (the `now` timestamp computation was kept at its original call site, before dispatch/scheduling, to
      preserve exact original semantics rather than recomputing it later). `FUNCTION_SIZE_EXTRA_EXCLUDES` entry removed
      — gate passes natively. Verified: AST size check clean, basedpyright 0 errors, ruff clean, 107 targeted tests
      green (`test_lifespan.py` 10, `test_sync_service.py` 77, `test_background_sync.py` 20), full
      `quality-gates.sh --no-fix` green (107s, sentinel `b68758a4ed87104f2fd33dbd31e4a2e27080b160`). Repo:
      deployment-api@aba3150.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-31 (slot-2, infra craft).** Decomposed
      `deployment_api/services/tarball_staleness.py`. Extracted
      `_ensure_fresh_precheck`/`_log_refresh_outcome`/`_build_refresh_result` from `ensure_fresh` (was 98L). Pure code
      motion, no logic changes (2 pre-existing typing gaps fixed along the way: `_build_refresh_result`'s `log_url`
      param widened to `str | None` to match `trigger_refresh`'s actual return type, and 2 unnecessary quoted
      forward-refs to `RefreshResult` removed per ruff UP037 — `RefreshResult` is already defined above both call
      sites). `FUNCTION_SIZE_EXTRA_EXCLUDES` entry removed — gate passes natively. Verified: AST size check clean,
      basedpyright 0 errors, ruff clean, 38 targeted tests green (`test_tarball_staleness.py` 27,
      `api/test_cost_snapshot.py` 11), full `quality-gates.sh --no-fix` green (128s, sentinel
      `aba3150dd8d15da6ff307ea595d5c7da7b98727b`). Repo: deployment-api@a88d1d9.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-31 (slot-2, infra craft).** Decomposed `deployment_api/utils/path_combinatorics.py`
      — the LAST file in `FUNCTION_SIZE_EXTRA_EXCLUDES`, which is now an empty array. Extracted
      `_build_combinatorics_for_venue` from `_build_combinatorics` (was 63L); extracted
      `_instruments_service_prefixes`/`_feature_group_service_prefixes`/`_calendar_service_prefixes` from
      `get_service_prefixes_for_date` (was 80L, docstring also condensed); extracted
      `_filter_by_asset_group_venues_folders`/`_filter_base_combinatorics` (shared) from `get_combinatorics` (was 52L)
      and `_expand_with_timeframes` from `_get_processing_combinatorics` (was 55L); extracted `_filter_combos_for_date`
      from `get_prefixes_for_date` (was 69L, docstring condensed); extracted `_default_prefix_query`/
      `_gather_parallel_query_results` from `parallel_query_prefixes` (was 70L, docstring condensed). Pure code motion,
      no logic changes. `FUNCTION_SIZE_EXTRA_EXCLUDES` entry removed (array now empty) — gate passes natively. Verified:
      AST size check clean, basedpyright 0 errors, ruff clean, 145 targeted tests green (`test_path_combinatorics.py`
      49+2skip, `test_data_status_turbo.py` 80+1skip, `test_batch_query_engine.py` 16), full `quality-gates.sh --no-fix`
      green (128s, sentinel `a88d1d925812b9accece9f119e8b38a35753614e`). Quickmerge's ruff-format auto-reformatted on
      land; re-verified size gate + basedpyright clean on the post-format tree. Repo: deployment-api@c9ddb43.
- [x] ✅ [SCRIPT] P3. **DONE 2026-07-31 (slot-2, infra craft).** All 27 files decomposed + removed from
      `FUNCTION_SIZE_EXTRA_EXCLUDES` (now an empty array, across every slot's work this doc tracks). Re-measured
      `CODEX_MAX_VIOLATIONS` honestly via `QG_SLICE=lint-codex`: **V=3**, not 0 — STEP 5.5z (2026-07-30) moved
      file/function/class/method size OUT of the `V` aggregate into its own zero-tolerance hard gate on the same day
      this stopgap's exclude list was added, so decomposing the 27 files never touched `V` at all (confirmed: `V` was
      already 3 pre-decomposition, unaffected throughout this doc's work). The 3 honest violations are all PRE-EXISTING
      and unrelated to size: (1) imports-inside-functions — 103 hits, mostly lazy `google.cloud`/ `google.auth` imports
      in `firebase_auth.py`/`health_routes.py`/`workers/_deployment_processor_vm_cleanup.py`; (2) direct cloud SDK
      imports — 2 files (`health_routes.py`, `services/artifact_pipeline/providers.py` — the latter carries a
      `# noqa: TID251` sanctioned-boundary comment that the pre-STEP-5.10 codex check doesn't honor, unlike STEP 5.10
      itself which passes clean); (3) broad `except Exception` — 4 files. Ratcheted `CODEX_MAX_VIOLATIONS` 5→3 to match
      the honest count (per this variable's own established ratchet-to-measured-V history in the file). Full
      `quality-gates.sh --no-fix` green post-ratchet (108s, sentinel `c9ddb43c5cfd071aafa4097db3e64c1c7efead3b`). Repo:
      deployment-api@2658beb. **This closes the plan — every todo above is now done; archive per the
      plan-completion-and-archival-discipline SSOT.**

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
