---
doc_type: issue
title: /ag-closeout-audit scope gap — asset_group infrastructure/meta docs invisible to all 9 tranches
summary: >-
  The 9-tranche partition (cefi/defi/tradfi/prediction/sports/cross-cutting/ao/ci/infra) only ever sweeps `asset_group:
  cross-cutting` (plus the 5 AGs) when building tranche membership, but `plans/PLAN_FORMAT.md:88` also declares
  `infrastructure` and `meta` as valid `asset_group` enum values — sweeping those 2 additional values returns ~48
  unlisted active docs, so the partition's stated "total coverage of the plans/issues corpus" claim was false by ~48
  docs. Resolved as `autonomous_session_operator_decisions_2026_07_25.md` entry #32 (option A): the SKILL.md fix (widen
  `all` mode + every tranche's membership rule to also sweep `infrastructure`/`meta`) already landed; this doc tracks
  the remaining corpus-wide triage of the ~48-doc delta the widened rule now surfaces. 4 of the ~48 (all
  ci-tranche-relevant) were already found and given a live home by the ci-tranche's own 2026-07-26 audit pass — see
  `ci_consolidated_closeout_2026_07_25.md`'s Progress Log for that subset; the remainder is unmeasured.
status: resolved
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ag-closeout-audit, scope-gap, plan-hygiene, asset-group, triage]
related:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /plans/PLAN_FORMAT.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: agent_operating_framework_master
assigned_vm: planning
priority: P2
locked_by:
resolved_by: "unified-trading-pm@3a5b294ef, 2026-07-31 — check_ag_closeout_linkage.py rewrite, baseline re-seeded 32->69"
source: >-
  ci tranche audit (2026-07-26), Phase-3 conflict-check — "four tranche members listed in NO consolidated closeout at
  all, found by sweeping beyond asset_group: cross-cutting." Generalized to all 9 tranches, resolved as
  autonomous_session_operator_decisions_2026_07_25.md entry #32.
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/PLAN_FORMAT.md,
    /scripts/plan-hygiene/check_ag_closeout_linkage.py,
    /plans/active/issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md,
  ]
---

# /ag-closeout-audit scope widening — triage the ~48-doc delta

> **🟢 RESOLVED 2026-08-02** — all 3 todos shipped, culminating in the 2026-07-31 `check_ag_closeout_linkage.py`
> rewrite (`unified-trading-pm@3a5b294ef`, baseline re-seeded 32→69, verified green).

## What's already done

- [x] [DOC] P2. Widen `cursor-configs/skills/ag-closeout-audit/SKILL.md`'s membership rule so `all` mode (and every
      single-tranche run) also sweeps `asset_group: infrastructure` and `asset_group: meta`, not just `cross-cutting` +
      the 5 AGs. ✅ DONE 2026-07-26.
- [x] [REVIEW] P2. 4 of the ~48 docs (ci-tranche-relevant, found by the ci tranche's own 2026-07-26 audit sweeping
      beyond `cross-cutting`) already triaged and given a live home:
      `/plans/archive/issues/check_strict_quickmerge_blind_to_dirty_deps_carveout_2026_07_23.md` (archived 2026-07-30) +
      `issues/quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21.md` (both `[meta]`) cited as
      `Source:`/Deferred-table entries in `ci_satellite_ao_dispatch_batch1_2026_07_26.md`;
      `issues/hatch_vcs_main_tag_ancestry_gap_breaks_cross_repo_pip_install_2026_07_26.md` +
      `issues/ci_registry_drift_uac_utl_stale_tag_version_conflict_2026_07_26.md` (both `[infrastructure]`) already
      `assigned_vm: planning` and actively dispatched. See `ci_consolidated_closeout_2026_07_25.md`'s Progress Log for
      the full note.

## Todos

- [x] [REVIEW] P2. **Run the corpus-wide sweep for the remaining delta**:
      `rg -l '^asset_group:.*\[.*infrastructure' plans/active` and the equivalent for `meta`, minus the 4
      already-triaged docs above, minus anything already covered by an existing tranche's Sources list under its
      epic-based membership rule. **Done when**: every remaining doc in the delta is classified into exactly one of the
      9 tranches (or explicitly ruled genuinely out-of-scope, with why), with the classification recorded either here or
      in the receiving tranche's own consolidated-closeout doc. ✅ DONE 2026-07-28 — see "Classification record" below.
- [x] ✅ [DOC] P3 — unified-trading-pm@3a5b294ef. Once the delta is fully classified, add a corpus-wide regression check
      (or extend `check_ag_closeout_linkage.py`, which does not currently catch this class) so a future doc tagged
      `infrastructure`/`meta` cannot silently re-accumulate outside every tranche's membership sweep.

      **MEASURED 2026-07-30 (`/ag-closeout-audit ao`, autonomous) — the gap is bigger and sharper than "does not
                                                                                                                                                                                                                                                                                                                                                                  currently catch this class", and it is now a REAL regression rather than a latent one.**
                                                                                                                                                                                                                                                                                                                                                                  `check_ag_closeout_linkage.py:REAL_AGS` is still literally `("cefi", "defi", "tradfi", "prediction", "sports")`,
                                                                                                                                                                                                                                                                                                                                                                  and its main loop skips any doc whose single `asset_group` value is not in that tuple
                                                                                                                                                                                                                                                                                                                                                                  (`if len(ag_values) != 1 or ag_values[0] not in REAL_AGS: continue`). Its module docstring additionally declares
                                                                                                                                                                                                                                                                                                                                                                  `infrastructure` EXEMPT "by construction" — correct when that value was a generic marker, **wrong since the
                                                                                                                                                                                                                                                                                                                                                                  2026-07-27 schema expansion** (`unified-trading-pm@a97bc7bed`) made `ao`/`ci`/`infrastructure` real dedicated
                                                                                                                                                                                                                                                                                                                                                                  enum values and the `infra` tranche's own membership signal. Net effect: **the standing linkage gate that
                                                                                                                                                                                                                                                                                                                                                                  `/ag-closeout-audit`'s SKILL.md cites as its safety net runs for only 5 of the 9 tranches** — `ao`, `ci` and
                                                                                                                                                                                                                                                                                                                                                                  `infra` docs are silently skipped, so the check reporting `0 orphan(s)` says nothing at all about them. Measured
                                                                                                                                                                                                                                                                                                                                                                  today by re-running the check's OWN functions with `REAL_AGS` widened (read-only, nothing shipped): `ao` 46
                                                                                                                                                                                                                                                                                                                                                                  single-AG members / **15** would-be orphans; `infrastructure` 45 / **14**; `ci` 30 / **30**. The `ci` 30/30 is a
                                                                                                                                                                                                                                                                                                                                                                  second, independent defect, not a backlog: `closeout_family_for("ci")` resolves to the EMPTY set because
                                                                                                                                                                                                                                                                                                                                                                  `ci_consolidated_closeout_2026_07_25.md` now lives in `plans/archive/2026_07/` while the check only globs
                                                                                                                                                                                                                                                                                                                                                                  `plans/active` — so even with `REAL_AGS` widened, every `ci` doc would fail both signals against a family that
                                                                                                                                                                                                                                                                                                                                                                  does not exist. This is the same closeout-archival failure mode already recorded in
                                                                                                                                                                                                                                                                                                                                                                  `generate_ag_closeout_audit_candidates.py`'s docstring (`…membership_stale_after_closeout_archival_2026_07_29`),
                                                                                                                                                                                                                                                                                                                                                                  recurring in a sibling checker. **So this todo needs three things, not one**: (a) widen `REAL_AGS` to the real
                                                                                                                                                                                                                                                                                                                                                                  enum and drop the now-wrong `infrastructure` exemption from the docstring, (b) make `closeout_family_for` resolve
                                                                                                                                                                                                                                                                                                                                                                  an ARCHIVED closeout family (or fail loudly instead of silently returning an empty set — a family of zero must
                                                                                                                                                                                                                                                                                                                                                                  never read as "nothing to check"), (c) only then re-baseline, using the honest measured counts above rather than
                                                                                                                                                                                                                                                                                                                                                                  today's vacuous `0`. Do NOT simply widen `REAL_AGS` and re-baseline to 59 — that would ratchet in the `ci`
                                                                                                                                                                                                                                                                                                                                                                  family-resolution bug as if it were legitimate pre-existing debt.

                                                              **RESOLVED 2026-07-31 (slot-4) — all three parts shipped, `check_ag_closeout_linkage.py` re-written, not
                                                              patched.** Along the way found that a SIBLING issue doc,
                                                              `issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md`, had already marked its own equivalent
                                                              todo `[x] DONE 2026-07-30` with detailed evidence (`COVERED_ASSET_GROUPS`, `_CLOSEOUT_FILENAME_PREFIX`, a
                                                              re-seeded baseline of 32) — but `git log --follow -- scripts/plan-hygiene/check_ag_closeout_linkage.py` shows
                                                              only the file's ORIGINAL 2026-07-25 commit ever touched it; that fix was never actually committed on any branch
                                                              (confirmed via `git log --all -p -S "COVERED_ASSET_GROUPS"`, zero hits). The "32" baseline that doc's claim
                                                              produced was therefore never enforced by running code — every invocation since 2026-07-30 was silently still
                                                              gated on the stale hard-coded `REAL_AGS` tuple. (a) `REAL_AGS` replaced with `COVERED_ASSET_GROUPS =
                                                              docspec.ASSET_GROUP - {"meta"}` (10 tranches); docstring corrected — `infrastructure`/`ao`/`ci` are no longer
                                                              described as exempt, only `meta` (and multi-value docs) are. (b) `closeout_family_for()` now searches
                                                              `plans/active` **and** `plans/archive` (`closeout_search_paths()`), which genuinely resolves the `ao`/`ci`
                                                              families (both archived-only) instead of the empty-set-as-silent-continue the prior unshipped design would
                                                              still have hit for `ci`; `build_related_graph()` takes an `extra_nodes` param so an active doc's `related:`
                                                              edge into an archived closeout doc is actually recorded (previously dropped by `target in graph` since the
                                                              graph's node set never included archived paths); an empty family for any covered tranche now prints an
                                                              unconditional `⚠️  EMPTY closeout family (UNENFORCED)` line to stderr, even under `--quiet` — verified this
                                                              path is reachable (not dead code) via a live negative test, not just a code read. (c) Honest full-corpus
                                                              measurement against the real widened code: `ao` 11/44, `cefi` 3, `ci` 11/38, `cross-cutting` 29, `defi` 4,
                                                              `infrastructure` 7, `sports` 1, `tradfi` 3 (`prediction` 0, `ui` 0) = **69 total**, baseline re-seeded 32 → 69
                                                              with the reasoning recorded in `ag_closeout_linkage_baseline.yaml`'s own header (same documented-exception
                                                              shape as the 2026-07-30 0→32 re-seed). Every one of the 69 pre-dates this session (spot-verified `git cat-file
                                                              -e HEAD:<path>`); none were newly introduced. Corroboration: the 29 `cross-cutting` orphans this run measured
                                                              match, near-exactly by name, the 29 never-cited docs `ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_
                                                              30.md`'s Progress Log manually enumerated on 2026-07-30 — strong independent evidence the widened signal
                                                              (graph BFS + body-text mention) is measuring the same real thing that manual investigation found, not an
                                                              artifact of this session's own code. `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` confirms the
                                                              linkage check now passes green (`✅ PASS [hard] AG-closeout linkage`) at the honest baseline; the sweep's two
                                                              other pre-existing failures (`Terminal-status-archived`, `assigned_vm:NA corpus size`) are unrelated and
                                                              unchanged by this fix (verified against a clean `git stash`'d tree). **Sibling doc's todos 1-3 corrected in the
                                                              same commit** — see its own Progress Log entry for the retraction + real evidence.

## Classification record — remaining delta (2026-07-28)

**`infrastructure` re-check**: as `cursor-configs/skills/ag-closeout-audit/SKILL.md` now documents (updated 2026-07-27,
`unified-trading-pm@a97bc7bed`), `asset_group: infrastructure` is a real dedicated enum value and IS the `infra`
tranche's own membership signal — every doc tagged `infrastructure` is _self-classifying_ into `infra` by construction;
no separate per-doc fold-in sweep is needed for this half of the todo. Spot-checked: 59 `infrastructure`-tagged docs
exist corpus-wide today; 39 are already textually cited inside the `infra_*.md` closeout family, the other 20 are
new-since-last-audit findings still awaiting a batch — that residual is `infra` tranche's own orphan-projection question
(`/ag-closeout-audit infra`'s job going forward), not a visibility gap this issue tracks.

**`meta` sweep** (the one genuine remaining gap per SKILL.md): `rg -l '^asset_group:.*\[.*meta' plans/active` returns 59
hits; 1 (`task_template.md`) is a false-positive grep match against an in-body enum example, not real frontmatter
(actual tag `[cross-cutting]`) — excluded. Of the true 58, **2 were already triaged** (the `check_strict_quickmerge_…`
and `quickmerge_sentinel_race_…` docs noted above), and 12 more carry `meta` alongside a real AG/`infrastructure` tag
(e.g. `[sports, defi, meta]`) — those were never actually invisible (the tranche sweep matches on the OTHER tag
already), so they're excluded as non-delta. That leaves **56 single/no-other-tag `meta` docs** as the true corpus,
classified below by content read (not tranche-hint grep) into whichever of `ao`/`ci`/`infra`/`cross-cutting` its subject
matter actually is — `meta` never had a dedicated tranche and none of these 56 are genuinely cross-AG first-party AG
content, so none classify into a real AG tranche.

**A — already covered** (15 docs; a real body-text or `related:` mention already exists inside the receiving tranche's
own closeout-family docs — confirmed by exact-stem grep against each of `ao_*.md`/`ci_*.md`/`infra_*.md` listed as the
citing file):

| Doc                                                                                                      | Tranche | Cited in                                                                                                                               |
| -------------------------------------------------------------------------------------------------------- | ------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `ao_open_issues_consolidated_close_out_2026_07_17.md`                                                    | ao      | `ao_consolidated_closeout_2026_07_25.md`, `ao_satellite_ao_dispatch_batch1_2026_07_26.md`, `ao_fleet_observability_kpis_2026_07_20.md` |
| `deployment_registry_firestore_p0_unblock_2026_07_14.md`                                                 | infra   | `infra_capture_and_devops_leftovers_finalize_2026_07_25.md`                                                                            |
| `issues/ao_docs_reconciliation_2026_07_15.md`                                                            | ao      | `ao_open_issues_consolidated_close_out_2026_07_17.md`                                                                                  |
| `issues/ao_residuals_after_dispatch_hardening_2026_07_17.md`                                             | ao      | `ao_open_issues_consolidated_close_out_2026_07_17.md`                                                                                  |
| `/plans/archive/issues/claude_code_settings_symlink_chain_broken_2026_07_23.md`                          | infra   | `infra_consolidated_closeout_2026_07_25.md`                                                                                            |
| `/plans/archive/issues/deployment_ui_l2_smoke_gate_red_2026_07_17.md` (archived, resolved 2026-07-31)    | infra   | `infra_consolidated_closeout_2026_07_25.md`                                                                                            |
| `/plans/archive/issues/instruments_service_run_tag_flag_not_applied_2026_07_08.md` (archived, resolved)  | infra   | `infra_consolidated_closeout_2026_07_25.md`                                                                                            |
| `issues/qg_workspace_root_template_drift_12_repos_2026_07_24.md`                                         | infra   | `infra_consolidated_closeout_2026_07_25.md`                                                                                            |
| `archive/issues/quickmerge_agent_files_pure_deletion_gap_2026_07_26.md`                                  | infra   | `infra_consolidated_closeout_2026_07_25.md`                                                                                            |
| `issues/regen_positional_task_ids_not_content_stable_2026_07_17.md`                                      | ao      | `ao_satellite_ao_dispatch_batch1_2026_07_26.md`, `ao_open_issues_consolidated_close_out_2026_07_17.md`                                 |
| `/plans/archive/issues/ui_hardcoded_colour_and_localhost_debt_2026_07_21.md`                             | infra   | `infra_consolidated_closeout_2026_07_25.md` (ARCHIVED — resolved, unified-trading-system-ui@145bf5dd)                                  |
| `/plans/archive/issues/ui_repos_eslint_base_config_never_wired_no_explicit_any_unenforced_2026_07_21.md` | infra   | `infra_consolidated_closeout_2026_07_25.md` (ARCHIVED — resolved, unified-trading-system-ui@ff811a8c)                                  |
| `/plans/archive/issues/unified_trading_system_ui_codex_violations_far_exceed_estimate_2026_07_21.md`     | infra   | `infra_consolidated_closeout_2026_07_25.md` (ARCHIVED — resolved, unified-trading-system-ui@030d2575)                                  |
| `issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md`                          | ao      | `ao_satellite_ao_dispatch_batch1_2026_07_26.md`                                                                                        |
| `qg_host_adaptive_resource_governor_2026_07_14.md`                                                       | ao      | `ao_open_issues_consolidated_close_out_2026_07_17.md`                                                                                  |

**B — freshly classified** (41 docs; genuinely had zero mention anywhere in the `ao`/`ci`/`infra`/`cross-cutting` family
— this is the real "was invisible to all 9 tranches" population; each now has a home, one-line why):

| Doc                                                                                                              | Tranche       | Why                                                                        |
| ---------------------------------------------------------------------------------------------------------------- | ------------- | -------------------------------------------------------------------------- |
| `/plans/archive/2026_07/asset_group_ao_ci_infra_schema_expansion_2026_07_27.md`                                  | infra         | corpus retag/schema-hygiene tooling (org hygiene)                          |
| `data_pipeline_alerts_batch_remediation_2026_07_15.md`                                                           | cross-cutting | data-pipeline alerts spanning sports/cefi/defi/tradfi, no single AG        |
| `deployment_durable_operational_data_bigquery_2026_07_21.md`                                                     | infra         | deployment/VM observability persistence                                    |
| `deployment_registry_firestore_migration_2026_07_14.md`                                                          | infra         | deployment registry infra migration (overview)                             |
| `deployment_registry_firestore_p0_unblock_2026_07_14_finalize_2026_07_27.md`                                     | infra         | gated finalize of the above, same family                                   |
| `deployment_registry_firestore_p3_cutover_2026_07_14.md`                                                         | infra         | same family, Phase 3                                                       |
| `deployment_registry_firestore_p5_verify_2026_07_14.md`                                                          | infra         | same family, Phase 5                                                       |
| `deployment_ui_observability_ux_tracker_2026_07_17.md`                                                           | infra         | deployment-ui workstream tracker                                           |
| `issues/adapter_contract_regression_ratchet_60s_timeout_flaky_under_contention_2026_07_27.md`                    | ci            | QG step timeout flake under shared-host contention                         |
| `/plans/archive/issues/ag_closeout_auditor_one_shot_complete_no_agentrow_2026_07_26.md`                          | ao            | AO dispatch entry-point / AgentRow bug                                     |
| `issues/agent_reply_cannot_address_a_different_role_silent_cross_role_blind_spot_2026_07_22.md`                  | ao            | AO `/reply` endpoint routing bug                                           |
| `issues/alerts_endpoint_per_object_gcs_read_performance_2026_07_23.md`                                           | infra         | deployment-api/alerting-service backend perf                               |
| `issues/ao_dashboard_backlog_detail_queue_lag_e2e_flaky_2026_07_26.md`                                           | ao            | AO dashboard Playwright flake                                              |
| `issues/ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md`                                                | ao            | AO server DB-lock/shutdown outage                                          |
| `/plans/archive/issues/ao_m3_verify_plan_flip_blind_to_archival_rename_2026_07_26.md`                            | ao            | AO `/done` M3 verification gate bug — RESOLVED, agent-orchestrator@587c8db |
| `/plans/archive/issues/blocked_marker_continuation_line_not_scanned_2026_07_26.md`                               | ao            | `regen_backlog_from_plan.py` parser bug                                    |
| `issues/cloud_build_router_concurrency_drops_dispatch_2026_07_27.md`                                             | ci            | `cloud-build-router.yml` concurrency-group bug                             |
| `issues/cost_observability_deferred_followups_2026_07_10.md`                                                     | infra         | deployment `/ops/costs` UI follow-ups                                      |
| `issues/credential_ask_orphan_checker_ping_format_stale_2026_07_27.md`                                           | infra         | plan-hygiene checker false positive                                        |
| `archive/issues/defi_citation_ratchet_tabs_path_exclusion_bug_2026_07_21.md`                                     | ci            | QG script path-exclusion bug (tooling, not defi content)                   |
| `issues/deployment_api_live_mock_parity_2026_07_17.md`                                                           | infra         | deployment-api live/mock contract drift                                    |
| `issues/deployment_api_sigabrt_crash_loop_2026_07_24.md`                                                         | infra         | deployment-api crash loop                                                  |
| `/plans/archive/issues/deployment_ui_nav_consolidation_2026_07_17.md`                                            | infra         | deployment-ui nav rebuild — RESOLVED + ARCHIVED 2026-08-01                 |
| `issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md`                                         | ao            | AO `gate_on_depends` dispatcher wiring bug                                 |
| `issues/host_root_disk_full_transient_2026_07_13.md`                                                             | infra         | shared-host disk-capacity incident                                         |
| `issues/manifest_consolidator_cadence_cost_audit_2026_07_20.md`                                                  | cross-cutting | manifest-consolidator spend, cross-AG data-pipeline infra                  |
| `/plans/archive/issues/manifest_reader_silent_empty_on_missing_project_id_2026_07_24.md`                         | cross-cutting | UTL manifest reader silent-swallow bug (resolved 2026-07-28)               |
| `issues/mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md`                                    | ci            | test-env leak blocking quickmerge                                          |
| `issues/mtds_sports_catalog_reader_timeout_test_flaky_under_contention_2026_07_27.md`                            | ci            | same flaky-under-contention class as adapter_contract_regression           |
| `issues/nohup_detached_background_process_killed_by_orphan_reap_2026_07_27.md`                                   | ao            | AO `orphan_reap` sweep kills detached background work                      |
| `archive/issues/plan_discipline_unquoted_deferred_by_design_false_positive_2026_07_27.md`                        | infra         | plan-hygiene checker false positive                                        |
| `issues/production_readiness_checklist_file_missing_2026_07_24.md`                                               | infra         | deployment-service + codex governance doc gap                              |
| `issues/qg_5_83_adapter_contract_regression_workspace_scan_timeout_2026_07_27.md (archived)`                     | ci            | QG step 5.83 timeout root doc                                              |
| `/plans/archive/issues/read_availability_index_slim_silent_valueerror_swallow_2026_07_27.md`                     | cross-cutting | same UTL-manifest-reader family as the above (resolved 2026-07-28)         |
| `/plans/archive/issues/repo_health_watcher_false_positive_green_recurrence_2026_07_25.md` (archived, 2026-07-31) | ao            | AO `RepoHealthWatcher` false-green recurrence (resolved)                   |
| `archive/issues/shared_host_tmp_tmpfs_full_2026_07_26.md` (archived, 2026-07-30)                                 | infra         | shared-host `/tmp` capacity incident (resolved, 0 open todos)              |
| `issues/sit_gate_fleet_green_auto_retrigger_stuck_2026_07_27.md`                                                 | ci            | `sit-gate/fleet-green` CI gate stuck                                       |
| `/plans/archive/issues/slot_stale_spawn_base_role_stuck_task_less_2026_07_25.md`                                 | ao            | AO slot-dispatcher stale-role bug                                          |
| `archive/issues/test_build_index_deterministic_races_on_concurrent_corpus_writes_2026_07_25.md`                  | ci            | doc-index determinism test, same flake class                               |
| `/plans/archive/issues/uac_service_emission_policy_duplicate_module_2026_07_27.md`                               | cross-cutting | UAC duplicate-module bug, shared schema layer                              |
| `issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md`                                 | ao            | AO worker interactive-session teardown behavior                            |

No doc in either list was genuinely out-of-scope of the 9-tranche partition — every one landed in `ao`/`ci`/`infra`/
`cross-cutting`. Group A needs no further action (already discoverable via body-text mention, same signal
`check_ag_closeout_linkage.py` accepts for the 5 real AGs). Group B is now recorded here as each doc's tranche home;
folding these into a receiving tranche's next `/ag-closeout-audit` orphan pass (so they get picked up for batch
extraction like any other tranche member) is normal tranche-audit business going forward, not further work this issue
needs to track.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
