---
doc_type: plan
title: CI/CD consolidated close-out — quickmerge, Cloud Build, GitHub Actions, SIT/promotion pipeline
summary: >-
  New "topic tranche" umbrella (sibling to the 5 asset groups + cross-cutting + ao) for CI/CD-pipeline-internal work:
  quickmerge mechanics, Cloud Build/GitHub Actions workflows, the SIT/promotion gate, version-graduation/release-tag
  machinery, and build/test tooling flakes. Authored 2026-07-25 from a corpus-wide classification pass (33 docs) — part
  of making the AG↔topic partition (5 AGs + cross-cutting + ao + ci + infra) total across the whole plans/issues corpus,
  per operator request.
status:
  active # REVIVED 2026-08-10 per operator ruling BLK-9a03622c option A — re-opened to cover
  # self_hosted_runner_public_repo_revert_2026_08_05.md + shared_ci_workflow_repo_extraction_2026_08_06.md
  # (dual-tagged [ci, infrastructure] P1 plans with no consolidated-closeout coordinator since this doc was
  # archived 2026-07-28)
nature: process
asset_group: [ci] # corrected 2026-08-19 (ag-closeout-audit cross-cutting-tranche run) -- was [cross-cutting]; this
  # is the ci tranche's OWN hub/coordinator doc (title, parent_epic: ci_master, assigned_role: cicd all confirm) --
  # a bare-cross-cutting-tag-on-single-tranche-content mistag invisible to the dual-tag Orthogonality grep since it
  # carried only one tag
stage: [meta]
repos: [unified-trading-pm, deployment-service, agent-orchestrator]
scope: [engineer, admin]
tags: [ci, cicd, close-out, consolidation, quickmerge, github-actions, cloud-build, sit, promotion]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /codex/07-security/self-hosted-runner-security-posture.md,
    /codex/08-workflows/ci-cd-flow.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /codex/06-coding-standards/quality-gates.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: 2026-07-25
last_updated: "2026-08-10"
parent_epic: ci_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 5.0
estimate_calibrated_ai_days: 4.0
assigned_role: cicd
archive_exempt: true # 0-open-todos 2026-08-10: REVIVED per operator ruling BLK-9a03622c option A — active work covering self_hosted_runner_public_repo_revert + shared_ci_workflow_repo_extraction
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

> **🟢 REVIVED 2026-08-10 per operator ruling BLK-9a03622c option A.** Two substantial, shipped, dual-tagged
> `[ci, infrastructure]` P1 plans (`self_hosted_runner_public_repo_revert_2026_08_05.md` +
> `shared_ci_workflow_repo_extraction_2026_08_06.md`) had no consolidated-closeout coordinator after this doc was
> archived 2026-07-28. Un-archiving restores the original partition (rather than widening
> `infra_consolidated_closeout`'s scope or accepting a permanent coverage gap). Both plans are now registered under this
> umbrella.
>
> **Next action**: the next `/ag-closeout-audit ci` tranche should verify both plans' remaining work is tracked under
> this closeout and fold any new ci-tagged issues into a fresh batch plan.

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
[issues/qg_sentinel_environment_blind_2026_07_23.md](/plans/archive/issues/qg_sentinel_environment_blind_2026_07_23.md)
(QG sentinel blind to the `ENVIRONMENT` dimension, dev-vs-prod gate laundering) ·
[issues/quickmerge_untracked_new_files_silent_noop_2026_06_23.md](/plans/archive/issues/quickmerge_untracked_new_files_silent_noop_2026_06_23.md)
(quickmerge silently no-ops on new-file-only ships) ·
[issues/provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md](/plans/archive/issues/provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md)
(provenance gate hand-overridden + the strict-quickmerge hook installed in zero clones) ·
[issues/stale_staging_versions_manifest_2026_07_23.md](/plans/archive/issues/stale_staging_versions_manifest_2026_07_23.md)
(`workspace-manifest.json` `staging_versions` frozen, breaks the quickmerge dependency gate — resolved + archived
2026-08-01) ·
[issues/quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md](/plans/active/issues/quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md)
(`quickmerge.sh` `ENVIRONMENT` auto-detect bug on `live-defi-rollout`) ·
[issues/orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md](/plans/archive/issues/orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md)
(GitHub Actions self-hosted-runner WIF job steps overwrite the shared gcloud config fleet-wide) ·
[issues/mtds_is_historical_quickmerge_bypass_backlog_2026_08_16.md](/plans/active/issues/mtds_is_historical_quickmerge_bypass_backlog_2026_08_16.md)
(MTDS + instruments-service 8-commit-each historical strict-quickmerge bypass backlog, operator decision pending —
added 2026-08-19 ag-closeout-audit cross-cutting retag).

**Close-out criterion**: QG sentinel environment-aware; quickmerge new-file-only ships no longer no-op; provenance gate
re-enforced + hook installed fleet-wide; `staging_versions` unfreezes; `ENVIRONMENT` auto-detect fixed; WIF job-step
isolation fixed on self-hosted runners.

## Track 2 — Cloud Build / GitHub Actions workflow bugs · P1/P2

**Sources**:
[issues/build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md](/plans/active/issues/build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md)
(Cloud Build/tarball-launcher AWS-lane bugs + image-tag/provenance gaps) ·
[issues/aws_codebuild_pr_approval_status_noise_2026_06_25.md](/plans/archive/issues/aws_codebuild_pr_approval_status_noise_2026_06_25.md)
(AWS CodeBuild cosmetic failure-status noise on promote PRs) ·
[issues/base_image_digest_sweep_broken_fleet_builds_red_2026_07_18.md](/plans/archive/issues/base_image_digest_sweep_broken_fleet_builds_red_2026_07_18.md)
(digest-drift-sweep GHA workflow never dispatches → fleet Cloud Builds red) ·
[issues/aws_codebuild_terraform_import_pending_2026_07_22.md](/plans/archive/2026_08/issues/aws_codebuild_terraform_import_pending_2026_07_22.md)
(terraform import owed for AWS CodeBuild projects/webhooks — RESOLVED 2026-08-10, all 7 todos shipped, archived) ·
[issues/cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md](/plans/archive/issues/cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md)
(`rollout-cloudbuild.py` template drift would regress fleet Cloud Build fixes) ·
[archive/issues/mutable_git_sha_tag_restamping_cloudbuild_2026_07_13.md](/plans/archive/issues/mutable_git_sha_tag_restamping_cloudbuild_2026_07_13.md)
(Cloud Build re-stamps mutable git-sha image tags on rebuild) ·
[issues/cassette_drift_check_calls_deleted_script_and_swallows_it_2026_07_17.md](/plans/archive/issues/cassette_drift_check_calls_deleted_script_and_swallows_it_2026_07_17.md)
(`cassette-drift-check.yml` calls a deleted script, silently green) ·
[issues/digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md](/plans/archive/issues/digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md)
(`digest-drift-sweep.yml` `GITHUB_TOKEN` cross-repo scope bug, silent no-op since birth) ·
[issues/github_actions_deploy_sa_overbroad_secret_access_2026_07_24.md](/plans/archive/issues/github_actions_deploy_sa_overbroad_secret_access_2026_07_24.md)
(github-actions-deploy SA has over-broad project-wide Secret Manager access) ·
`/plans/archive/2026_07/github_actions_ci_cost_reduction_2026_07_15.md` +
`github_actions_cost_reduction_options_analysis_2026_07_15.md` +
`github_actions_operator_gated_followups_2026_07_17.md` + `github_actions_staging_machinery_shutdown_2026_07_24.md` (GHA
cost-reduction program: options analysis → redirect index → operator-gated followups → dead staging-machinery shutdown)
·
[issues/deployment_api_ar_repo_override_audit_and_iam_probe_2026_08_07.md](/plans/archive/issues/deployment_api_ar_repo_override_audit_and_iam_probe_2026_08_07.md) (archived 2026-08-19, resolved)
(deployment-api Artifact-Registry-repo-override allowlist audit + startup-time IAM capability probe; retagged `[ci]`
2026-08-16 from a `[cross-cutting]` mistag, `/ag-closeout-audit cross-cutting` parked finding 4) ·
[issues/glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md](/plans/active/issues/glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md)
(two self-hosted glue-runner systemd units left inactive, stalling UAC LDR→main promotion + cascading a Tier-A CI
outage across 11 dependent repos; retagged `[ci]` 2026-08-16 from a `[cross-cutting]` mistag, same parked-findings run,
finding 6).

**Close-out criterion**: every named workflow bug fixed + verified green on a real run (digest-sweep dispatches,
cassette-drift-check calls a real script, token scope fixed); the GHA cost-reduction program's operator-gated followups
closed; the deploy SA's Secret Manager access scoped down; the AR-repo-override audit + IAM probe items landed; the two
stopped glue-runner systemd units restarted and the crash-loop watchdog extended to catch a cleanly-`inactive` unit.

## Track 3 — SIT gate / promotion-pipeline correctness · P1

**Sources**:
[issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md](/plans/archive/issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md)
(SIT gate compares against a moving LDR tip, can block breaking promotes indefinitely) ·
[issues/promotion_lag_alert_hides_provenance_block_2026_07_17.md](/plans/archive/issues/promotion_lag_alert_hides_provenance_block_2026_07_17.md)
(promotion-lag alert masks the real quickmerge provenance-block root cause) ·
[issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md](/plans/active/issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md)
(three unrelated failures all surfaced as one generic "PROMOTION LAG" alert) ·
[issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md](/plans/archive/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md)
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
[issues/reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17.md](/plans/archive/issues/reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17.md)
(`reconcile-release-tags` creating zero tags post-D13 `version_source` migration) ·
[issues/d13_orphaned_version_readers_and_manifest_drift_2026_07_17.md](/plans/archive/issues/d13_orphaned_version_readers_and_manifest_drift_2026_07_17.md)
(orphaned version-readers + `workspace-manifest.json` `versions{}` cache drift post-D13 — the REPO version manifest, not
the data manifest, despite the filename).

**Close-out criterion**: release-tag creation resumes; orphaned version-readers repointed at the D13 SSOT.

## Track 5 — Build/test tooling + CI-cost · P2/P3

**Sources**: [ui_build_warm_cache_2026_06_17.md](/plans/archive/2026_08/ui_build_warm_cache_2026_06_17.md) (UI build
warm-cache to keep QG builds incremental) ·
[issues/mtds_deployment_env_race_survives_single_worker_2026_07_23.md](/plans/archive/issues/mtds_deployment_env_race_survives_single_worker_2026_07_23.md)
(pytest `DEPLOYMENT_ENV` test-pollution race, reproduces even serially) ·
[capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md](/plans/active/capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md)
(live P1 item: CI-runner-blocked `generate-unified-openapi.sh` regen needing `.venv-workspace` on a CI runner).

**Close-out criterion**: UI build cache warm across QG runs; the pytest env-race root-caused + fixed; the OpenAPI regen
unblocked on a CI runner.

## Todos

- [x] ✅ [DOC] P2. **This tranche has no native dispatch vehicle of its own — 30 of 34 tranche docs are orphaned** — per
      the 2026-07-26 `/ag-closeout-audit ci` entry below, this doc carries zero `- [ ]` todos (a reachability digest
      only) and 12 of the 30 orphans express ALL their remaining work as numbered prose with zero checkboxes; do not
      treat this doc's own checkbox-free format as evidence the CI/CD tranche's remaining work is tracked or done — see
      `ci_satellite_ao_dispatch_batch1_2026_07_26.md` (status: draft) for the extracted subset. **Verified accurate
      2026-07-28** — re-read the doc in full: the caveat correctly matches the Progress Log's own 2026-07-26
      `/ag-closeout-audit ci` findings (30/34 orphaned, 12 prose-only) recorded immediately below it. No correction
      needed; checkbox flipped to record the verification.

## Codex SSOTs (read before touching a track)

`/codex/08-workflows/ci-cd-flow.md`, `/codex/06-coding-standards/quality-gates.md`.

## Progress Log

- **context-scout 2026-08-19**: re-verified context_scope (3 entries) unchanged, all resolve on disk.
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries)
- **2026-07-25** — Doc authored from the same corpus-wide classification pass as
  `ao_consolidated_closeout_2026_07_25.md`. 33 docs classified into this CI tranche (2 from `orchestrator_master` + 10
  from `deployment_and_user_management_master` + 1 from `strategy_master` + 20 reclassified out of
  `infrastructure_master`'s "pure-infra" bucket). No fixes applied in this pass — pure consolidation for
  `/ag-closeout-audit`/`/plan-reconcile` sharding.
- **2026-07-26 — `/ag-closeout-audit ci` (autonomous mode). Headline: THIS TRANCHE HAS NO DISPATCH VEHICLE.** Phase 0
  measured it: this doc carries **zero `- [ ]` todos** (it is a reachability digest, `assigned_vm: NA` +
  `execution_scope: local-only`), **no `ci_satellite_ao_dispatch_batch*` plan has ever existed** (checked
  `plans/active/` and `plans/archive/2026_*/`), and all 30 Source docs above are `assigned_vm: NA`/unset. Being listed
  in a Track's Sources is discoverability, not dispatch — so every remaining open item in this tranche is currently
  tracked-but-unworked. Phase 1 read all 34 tranche-primary docs end-to-end: **30 orphaned** (20
  `orphaned_partial_coverage`, 10 `orphaned_never_touched`), 2 `archivable_now`
  (`/plans/archive/2026_07/github_actions_ci_cost_reduction_2026_07_15.md`, now a pure redirect index that says so
  itself, and `github_actions_cost_reduction_options_analysis_2026_07_15.md`, a closed decision record whose Appendix-4
  `☐` items are explicitly "reference checklist, not dispatch todos"), and 2 NOT orphaned because they are already
  AO-dispatched. A recurring trap: **12 of the 30 orphans express ALL their remaining work as numbered prose with zero
  checkboxes**, so a checkbox count answers nothing here.
  - **Drafted (both `status: draft`, NOT dispatched — flipping to `active` is the operator's call)**:
    [/plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md](/plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md)
    (29 conflict-cleared bounded todos, 33 Deferred by taxonomy) +
    [/plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md](/plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md)
    (`depends_on` + `gate_on_depends: true` + `sequential: true`). Shipped `unified-trading-pm@03d9ed87e`.
  - **Phase-3 conflict-check result worth carrying forward**: `scripts/quickmerge.sh` is claimed by **6** docs in this
    tranche and PM `scripts/quality-gates.sh` by **3**, so the batch dispatches exactly ONE quickmerge.sh todo and
    pushes every new-QG-checker wire-in into the gated finalize plan. Four more files were rationed the same way. This
    is the tranche's dominant structural constraint — expect batch 2+ to be gated on file contention, not on ideas.
  - **Four tranche members are listed in NO consolidated closeout at all** (found by sweeping beyond
    `asset_group: cross-cutting`): `archive/issues/check_strict_quickmerge_blind_to_dirty_deps_carveout_2026_07_23.md`
    and `issues/quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21.md` (both
    `asset_group: [meta]`, both orphaned — the first has **zero** referrers corpus-wide), plus
    `issues/hatch_vcs_main_tag_ancestry_gap_breaks_cross_repo_pip_install_2026_07_26.md` and
    `issues/ci_registry_drift_uac_utl_stale_tag_version_conflict_2026_07_26.md` (both `asset_group: [infrastructure]`,
    both already `assigned_vm: planning` and actively dispatched). All four are cited as `Source:` docs or in the
    Deferred tables of the batch plan, so they now have a live home. **Deliberately NOT added to the Track Sources
    above** — `infrastructure` and `meta` are valid `asset_group` values the 9-tranche partition's membership rule never
    swept, so which tranche owns them is an escalated operator question, not a mechanical fix.
- **2026-08-09 — `/ag-closeout-audit ci` (autonomous, second same-day dispatch, slot 24, `agt-09695d`), Orthogonality
  HARD CHECK retag pass.** Found 5 docs still dual-tagged `[ci, cross-cutting]`/`[cross-cutting, ci]` (2 of them —
  `image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md` and
  `glue_pool_starvation_monitor_stale_jobs_after_runner_revert_2026_08_07.md` — already flagged as mistags by the
  2026-08-08 cross-cutting tranche run per SKILL.md's own history, never retagged since). Content-verified 3 as
  unambiguous CI/CD-pipeline-mechanics-only (no cross-AG scope) and retagged to bare `[ci]`:
  [/plans/active/issues/image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md](/plans/active/issues/image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md)
  (GitHub Actions self-hosted-runner strand blocking LDR→main promotion),
  [/plans/archive/2026_08/issues/glue_pool_starvation_monitor_stale_jobs_after_runner_revert_2026_08_07.md](/plans/archive/2026_08/issues/glue_pool_starvation_monitor_stale_jobs_after_runner_revert_2026_08_07.md)
  (CI alert-tuning incident), and the
  [/plans/archive/2026_08/ci_satellite_ao_dispatch_batch8_2026_08_09.md](/plans/archive/2026_08/ci_satellite_ao_dispatch_batch8_2026_08_09.md)
  +finalize pair (batch-extraction docs are single-tranche by construction). Left 2 unretagged as genuinely ambiguous
  (`assigned_role_devops_invalid_value_corpus_wide_2026_08_08.md` — content is corpus-wide, not ci-specific;
  `plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md` — plan-hygiene-tooling content reads closer to
  `infra`/`meta` than `ci`, needs a dedicated owner decision, not a guess). Post-retag linkage re-run (per SKILL.md's
  own "necessary but not sufficient" warning) found
  `image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07` newly orphaned within `ci`'s own family (this
  Progress Log entry IS that link-back fix) — the other 2 retagged docs were already reachable and needed no further
  linkage fix. Re-verified 0→0 new orphans after this entry landed.
- **/ci-reconcile 2026-08-18**: filed
  [/plans/archive/2026_08/issues/mdps_main_qg_tests_slice_oserror_cannot_send_2026_08_18.md](/plans/archive/2026_08/issues/mdps_main_qg_tests_slice_oserror_cannot_send_2026_08_18.md)
  — market-data-processing-service `main` branch `quality-gates-v2` regressed MAIN_GREEN -> FAILING
  (QG_SLICE=tests, single `OSError: cannot send (already closed?)` signature, flake-vs-real
  regression unconfirmed; a re-run was dispatched to test the flake hypothesis). This entry IS the
  link-back fix for that doc's `asset_group: [ci]` family membership.
- **/ci-reconcile 2026-08-18 (second pass, same day)**: filed
  [/plans/archive/2026_08/issues/fleet_wide_qg_cascade_pm_manifest_race_plus_silent_webhook_gap_2026_08_18.md](/plans/archive/2026_08/issues/fleet_wide_qg_cascade_pm_manifest_race_plus_silent_webhook_gap_2026_08_18.md)
  — root-caused the 13-repo simultaneous QG RED/GREEN cascade (PM-manifest-validity single point of failure via
  `run-all-validators.sh`, cloned into every repo's own checks slice) and a silent SLACK_CI_WEBHOOK_URL gap on 9
  repos. Both fixed live this session (`unified-trading-pm@176ff63dab` validator retry + gh secret repropagation
  from GSM); 3 follow-up audit/hardening todos remain open. This entry IS the link-back fix for that doc's
  `asset_group: [ci]` family membership.
- **context-scout 2026-08-14**: populated context_scope (3 entries).
- **na-eligibility-audit 2026-08-17** [body-hash:498e5d37d2cac002]: KEEP-NA, valid -- Zero open todos of its own (it is a reachability-map/coordination hub over 5 Tracks), but explicitly not moot: `archive_exempt: true` is set in frontmatter with a clear stated reason, and the doc carries a dated REVIVED banner (2026-08-10, operator ruling BLK-9a03622c option A) explaining it was un-archived specifically because archiving it left two substantial shipped P1 plans with no consolidated-closeout coordinator. The banner names a live, still-open 'next action' (verify both plans' remaining work is tracked here; fold new ci-tagged issues into a fresh batch plan). This is a standing coordination hub deliberately kept alive, not a stale/moot doc.
- **na-eligibility-audit 2026-08-19** (cross-cutting tranche): KEEP-NA, valid — 0 open todos (a reachability-map hub over 5 Tracks, not primary work itself) but explicitly not moot: archive_exempt:true + REVIVED 2026-08-10 per operator ruling BLK-9a03622c to keep coordinating 2 shipped dual-tagged.
- **interactive slot-1, 2026-08-20**: filed
  [/plans/active/issues/agent_orchestrator_qg_cancel_notifier_same_sha_rerun_gap_2026_08_20.md](/plans/active/issues/agent_orchestrator_qg_cancel_notifier_same_sha_rerun_gap_2026_08_20.md)
  — agent-orchestrator's "QG slice CANCELLED/TIMED-OUT" notifier pages correctly-by-design on a cancelled run that is
  still the ref tip, but doesn't recognize a same-sha rerun that succeeds seconds later as non-actionable (a gap in
  `supersede-check`'s coverage, filed alongside the same day's UAC publish-ordering-race root-cause deep-dive in
  [/plans/active/issues/cloud_build_uac_publish_ordering_race_recurrence_strategy_service_2026_08_20.md](/plans/active/issues/cloud_build_uac_publish_ordering_race_recurrence_strategy_service_2026_08_20.md)).
  This entry IS the link-back fix for that doc's `asset_group: [ci]` family membership.
- **ci_reconciler 2026-08-21**: filed
  [/plans/active/issues/deployment_service_historical_quickmerge_bypass_backlog_2026_08_21.md](/plans/active/issues/deployment_service_historical_quickmerge_bypass_backlog_2026_08_21.md)
  — `deployment-service` carries a 19-commit-remaining, month-old, multi-identity strict-quickmerge bypass backlog
  (dated 2026-07-09 through 2026-07-20, 7+ distinct slot/host identities), the same shape as the sibling
  `mtds_is_historical_quickmerge_bypass_backlog_2026_08_16.md` finding — not currently blocking a live promote PR,
  needs an operator bulk-bless/re-ship/show-and-wait decision per `/ci-reconcile` §4's size/authorship gate. This
  entry IS the link-back fix for that doc's `asset_group: [ci]` family membership.
