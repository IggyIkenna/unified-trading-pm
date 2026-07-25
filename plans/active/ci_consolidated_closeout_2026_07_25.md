---
doc_type: plan
title: CI/CD consolidated close-out — quickmerge, Cloud Build, GitHub Actions, SIT/promotion pipeline
summary: >-
  New "topic tranche" umbrella (sibling to the 5 asset groups + cross-cutting + ao) for CI/CD-pipeline-internal work:
  quickmerge mechanics, Cloud Build/GitHub Actions workflows, the SIT/promotion gate, version-graduation/release-tag
  machinery, and build/test tooling flakes. Authored 2026-07-25 from a corpus-wide classification pass (33 docs) — part
  of making the AG↔topic partition (5 AGs + cross-cutting + ao + ci + infra) total across the whole plans/issues corpus,
  per operator request.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, deployment-service, agent-orchestrator]
scope: [engineer, admin]
tags: [ci, cicd, close-out, consolidation, quickmerge, github-actions, cloud-build, sit, promotion]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/ao_consolidated_closeout_2026_07_25.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: 2026-07-25
last_updated: "2026-07-25"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 5.0
estimate_calibrated_ai_days: 4.0
assigned_role: cicd
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Corpus-wide classification pass (unified-trading-pm, 2026-07-25) splitting CI/CD-flavored docs (previously all
  `asset_group: cross-cutting`, spread across `infrastructure_master`/`deployment_and_user_management_master`/
  `orchestrator_master`/`strategy_master`) into this CI tranche, per operator request to make the 5-AG + cross-cutting +
  ao + ci + infra topic partition total (zero orphans) for sharded `/plan-reconcile` and `/ag-closeout-audit` runs.
---

# CI/CD consolidated close-out

> **Purpose.** One place to see all CI/CD-pipeline-internal work. This plan **references** the source docs; it does not
> duplicate their content. Distinct from `ao_consolidated_closeout_2026_07_25.md` — CI/CD is the build/ship pipeline
> (quickmerge → LDR → SIT → main); AO is the agent-dispatch substrate that RUNS the pipeline's automation.

## Reachability map

1. **Quickmerge mechanics** → Track 1
2. **Cloud Build / GitHub Actions workflow bugs** → Track 2
3. **SIT gate / promotion-pipeline correctness** → Track 3
4. **Version-graduation / release-tag machinery** → Track 4
5. **Build/test tooling + CI-cost** → Track 5

## Track 1 — Quickmerge mechanics · P0/P1

**Sources**:
[issues/qg_sentinel_environment_blind_2026_07_23.md](/plans/active/issues/qg_sentinel_environment_blind_2026_07_23.md)
(QG sentinel blind to the `ENVIRONMENT` dimension, dev-vs-prod gate laundering) ·
[issues/quickmerge_untracked_new_files_silent_noop_2026_06_23.md](/plans/active/issues/quickmerge_untracked_new_files_silent_noop_2026_06_23.md)
(quickmerge silently no-ops on new-file-only ships) ·
[issues/provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md](/plans/active/issues/provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md)
(provenance gate hand-overridden + the strict-quickmerge hook installed in zero clones) ·
[issues/stale_staging_versions_manifest_2026_07_23.md](/plans/active/issues/stale_staging_versions_manifest_2026_07_23.md)
(`workspace-manifest.json` `staging_versions` frozen, breaks the quickmerge dependency gate) ·
[issues/quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md](/plans/active/issues/quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md)
(`quickmerge.sh` `ENVIRONMENT` auto-detect bug on `live-defi-rollout`) ·
[issues/orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md](/plans/active/issues/orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md)
(GitHub Actions self-hosted-runner WIF job steps overwrite the shared gcloud config fleet-wide).

**Close-out criterion**: QG sentinel environment-aware; quickmerge new-file-only ships no longer no-op; provenance gate
re-enforced + hook installed fleet-wide; `staging_versions` unfreezes; `ENVIRONMENT` auto-detect fixed; WIF job-step
isolation fixed on self-hosted runners.

## Track 2 — Cloud Build / GitHub Actions workflow bugs · P1/P2

**Sources**:
[issues/build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md](/plans/active/issues/build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md)
(Cloud Build/tarball-launcher AWS-lane bugs + image-tag/provenance gaps) ·
[issues/aws_codebuild_pr_approval_status_noise_2026_06_25.md](/plans/active/issues/aws_codebuild_pr_approval_status_noise_2026_06_25.md)
(AWS CodeBuild cosmetic failure-status noise on promote PRs) ·
[issues/base_image_digest_sweep_broken_fleet_builds_red_2026_07_18.md](/plans/active/issues/base_image_digest_sweep_broken_fleet_builds_red_2026_07_18.md)
(digest-drift-sweep GHA workflow never dispatches → fleet Cloud Builds red) ·
[issues/aws_codebuild_terraform_import_pending_2026_07_22.md](/plans/active/issues/aws_codebuild_terraform_import_pending_2026_07_22.md)
(terraform import owed for AWS CodeBuild projects/webhooks) ·
[issues/cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md](/plans/active/issues/cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md)
(`rollout-cloudbuild.py` template drift would regress fleet Cloud Build fixes) ·
[issues/mutable_git_sha_tag_restamping_cloudbuild_2026_07_13.md](/plans/active/issues/mutable_git_sha_tag_restamping_cloudbuild_2026_07_13.md)
(Cloud Build re-stamps mutable git-sha image tags on rebuild) ·
[issues/cassette_drift_check_calls_deleted_script_and_swallows_it_2026_07_17.md](/plans/active/issues/cassette_drift_check_calls_deleted_script_and_swallows_it_2026_07_17.md)
(`cassette-drift-check.yml` calls a deleted script, silently green) ·
[issues/digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md](/plans/active/issues/digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md)
(`digest-drift-sweep.yml` `GITHUB_TOKEN` cross-repo scope bug, silent no-op since birth) ·
[issues/github_actions_deploy_sa_overbroad_secret_access_2026_07_24.md](/plans/active/issues/github_actions_deploy_sa_overbroad_secret_access_2026_07_24.md)
(github-actions-deploy SA has over-broad project-wide Secret Manager access) ·
`github_actions_ci_cost_reduction_2026_07_15.md` + `github_actions_cost_reduction_options_analysis_2026_07_15.md` +
`github_actions_operator_gated_followups_2026_07_17.md` + `github_actions_staging_machinery_shutdown_2026_07_24.md` (GHA
cost-reduction program: options analysis → redirect index → operator-gated followups → dead staging-machinery shutdown).

**Close-out criterion**: every named workflow bug fixed + verified green on a real run (digest-sweep dispatches,
cassette-drift-check calls a real script, token scope fixed); the GHA cost-reduction program's operator-gated followups
closed; the deploy SA's Secret Manager access scoped down.

## Track 3 — SIT gate / promotion-pipeline correctness · P1

**Sources**:
[issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md](/plans/active/issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md)
(SIT gate compares against a moving LDR tip, can block breaking promotes indefinitely) ·
[issues/promotion_lag_alert_hides_provenance_block_2026_07_17.md](/plans/active/issues/promotion_lag_alert_hides_provenance_block_2026_07_17.md)
(promotion-lag alert masks the real quickmerge provenance-block root cause) ·
[issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md](/plans/active/issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md)
(three unrelated failures all surfaced as one generic "PROMOTION LAG" alert) ·
[issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md](/plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md)
(UAC value-only config edits break UTL untested — no gate/SIT catches it) ·
[issues/post_cutover_silent_assumption_sweep_2026_07_23.md](/plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md)
(post-staging-cutover audit: release-tagging/breaking-gate mechanisms broken since the cutover) ·
`cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` (the LDR→SIT→main pipeline MVP redesign itself — the entry point most of
this Track's findings trace back to).

**Close-out criterion**: SIT compares against a pinned (not moving) LDR reference; promotion-lag alerting disambiguates
its 3+ distinct root causes; a real gate catches UAC-value-only/UTL-untested breakage; the post-cutover
release-tagging/breaking-gate mechanisms repaired.

## Track 4 — Version-graduation / release-tag machinery · P2

**Sources**:
[issues/reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17.md](/plans/active/issues/reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17.md)
(`reconcile-release-tags` creating zero tags post-D13 `version_source` migration) ·
[issues/d13_orphaned_version_readers_and_manifest_drift_2026_07_17.md](/plans/active/issues/d13_orphaned_version_readers_and_manifest_drift_2026_07_17.md)
(orphaned version-readers + `workspace-manifest.json` `versions{}` cache drift post-D13 — the REPO version manifest, not
the data manifest, despite the filename).

**Close-out criterion**: release-tag creation resumes; orphaned version-readers repointed at the D13 SSOT.

## Track 5 — Build/test tooling + CI-cost · P2/P3

**Sources**: [ui_build_warm_cache_2026_06_17.md](/plans/active/ui_build_warm_cache_2026_06_17.md) (UI build warm-cache
to keep QG builds incremental) ·
[issues/mtds_deployment_env_race_survives_single_worker_2026_07_23.md](/plans/active/issues/mtds_deployment_env_race_survives_single_worker_2026_07_23.md)
(pytest `DEPLOYMENT_ENV` test-pollution race, reproduces even serially) ·
[capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md](/plans/active/capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md)
(live P1 item: CI-runner-blocked `generate-unified-openapi.sh` regen needing `.venv-workspace` on a CI runner).

**Close-out criterion**: UI build cache warm across QG runs; the pytest env-race root-caused + fixed; the OpenAPI regen
unblocked on a CI runner.

## Codex SSOTs (read before touching a track)

`/codex/08-workflows/ci-cd-flow.md`, `/codex/06-coding-standards/quality-gates.md`.

## Progress Log

- **2026-07-25** — Doc authored from the same corpus-wide classification pass as
  `ao_consolidated_closeout_2026_07_25.md`. 33 docs classified into this CI tranche (2 from `orchestrator_master` + 10
  from `deployment_and_user_management_master` + 1 from `strategy_master` + 20 reclassified out of
  `infrastructure_master`'s "pure-infra" bucket). No fixes applied in this pass — pure consolidation for
  `/ag-closeout-audit`/`/plan-reconcile` sharding.
