---
doc_type: issue
title:
  55-item cross-repo CODE_QUICK fix backlog from the 1-2-open-todo triage — 2 shipped, 1 blocked on QG, 52 undispatched
summary: >-
  Follow-up to the checkbox-honesty pass (prose-trap fix batch + 22-doc archival). Of 420 docs with 1-2 open todos, a
  keyword pre-filter narrowed to 281 "plausibly quick" candidates, which a 9-way parallel read-only classification pass
  split into 22 DOC_ONLY_QUICK (done, see doc_only_quick_fix_pass_2026_07_28 batch — actually landed inline, no separate
  doc), 55 CODE_QUICK (touch real service code in ~15 other repos, need per-repo quality-gates.sh + commit — this doc),
  and 204 NOT_QUICK (correctly left untouched — operator-gated, VM/backfill-gated, or genuinely needs investigation
  despite the low todo count). Operator explicitly chose "implement them all now" over drafting an AO plan or just
  handing over the list (2026-07-28). This doc exists so the remaining ~52 items aren't lost to context compaction
  before they're dispatched.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos:
  [
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-pm,
    unified-trading-library,
    features-service,
    agent-orchestrator,
    instruments-service,
    deployment-service,
    deployment-api,
    unified-trading-system-ui,
    market-data-processing-service,
    ml-service,
    trading-agent-service,
  ]
scope: [engineer]
tags: [cross-repo, code-fix, backlog, plan-hygiene, checkbox-honesty]
related: []
created: "2026-07-28"
parent_epic: infrastructure_master
source: "main session, 2026-07-28, following the checkbox-honesty pass on the 1-2-open-todo bucket"
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
---

# Cross-repo CODE_QUICK fix backlog (55 items, 2 shipped, 1 blocked, 52 undispatched)

## Status per repo

- [x] **unified-api-contracts (2 items) — SHIPPED**: `unified-api-contracts@cb9e97dfd`. Deleted dead
      `service_emission_policy.py`; retrofitted 7 lending protocols' `instrument_types` to `[A_TOKEN, DEBT_TOKEN]`. Both
      source PM docs (`uac_service_emission_policy_duplicate_module_2026_07_27.md`,
      `defi_lending_protocol_capabilities_instrument_types_stale_atoken_debttoken_2026_07_27.md`) flipped + archived.

- [ ] [CODE] P1. **market-tick-data-service (~15 items) — BLOCKED on quality-gates.sh, real violations, not transient.**
      An agent implemented most of the batch (uncommitted, working tree only as of last check — verify current state,
      may have been lost or superseded by concurrent activity since): dead-code cleanup, base_defi_adapter success-key
      fix, Tardis epoch-unit fix, Solana address-primitives extraction (`cli/handlers/_solana_pda.py`), CAS DNS-resolver
      swap, dtype-coercion fix, wallclock field-derivation fix, autouse-fixture test pattern, progress checkpoint,
      VM-name collision hash. Full assigned-vs-not-mine file disambiguation saved at
      `/private/tmp/claude-501/-Users-ikennaigboaka-Code-unified-trading-system-repos--tabs-4/60ea16ec-43a4-4dcc-a3f2-7baea3767b5e/scratchpad/mtds_my_files.txt`
      (26 files) — do NOT stage/commit anything in that repo not on this list, it's a shared clone with a different
      concurrent session's WIP interleaved (confirmed: `_umi_extended.py` + 3 related Starknet-funding-timestamp files
      are NOT mine, leave them alone). **quality-gates.sh FAILED with 2 real violations** (log at
      `/private/tmp/claude-501/.../scratchpad/mtds_qg_run.log`): `rebuild_prediction_manifest.py` 909L and
      `engine/orchestrator/__init__.py` 912L both exceed the 900-line file-size gate; `base_defi_adapter.py`'s
      `_download_all_instruments()` is 56L, over the function-size cap. These need real trimming/splitting, not a quick
      fix — next session should re-verify what's actually still in the working tree (a lot of concurrent activity has
      happened since), then either finish the QG fix or re-scope.

- [ ] [CODE] P2. **unified-trading-pm scripts (~14 items) — UNDISPATCHED.** Source docs:
      mdps_candle_manifest_population_disconnect_2026_07_25 (run-bounded-analysis.sh RLIMIT_AS hardening),
      test_build_index_deterministic_races_on_concurrent_corpus_writes_2026_07_25 (frozen tmp_path fixture),
      defi_citation_ratchet_tabs_path_exclusion_bug_2026_07_21 (drop redundant absolute-path check in
      check_defi_address_citations.py), plan_discipline_unquoted_deferred_by_design_false_positive_2026_07_27
      (regex-exclusion extension + baseline), credential_ask_orphan_checker_ping_format_stale_2026_07_27 (BLK-<id>
      regex), quickmerge_agent_files_pure_deletion_gap_2026_07_26 (--files staging loop fall-through),
      qg_workspace_root_template_drift_12_repos_2026_07_24 (WORKSPACE_ROOT= across 12 repos),
      plan_health_tests_leak_real_slack_alerts_2026_07_24 (env-var fallback),
      plan_priority_policy_qg_validation_2026_07_28 (new hygiene script),
      shared_host_ram_exhaustion_kills_background_qg_2026_07_27 (SIGTERM trap + worker.md doc),
      qg_5_83_adapter_contract_regression_workspace_scan_timeout_2026_07_27 (timeout constant),
      quickmerge_silent_push_failure_under_contention_2026_07_27 (push exit-code check + retry, fix already drafted in
      the doc), ui_coverage_ts_venue_category_v2_rename_gap_2026_07_10 (generator-script half only, UI half is separate
      item below).

- [ ] [CODE] P2. **unified-trading-library (4 items) — UNDISPATCHED.**
      manifest_index_read_oom_canonical_cache_2026_06_24 (cap `_CANONICAL_CACHE`, evict on bucket-change in
      `_state.py`), read_availability_index_slim_silent_valueerror_swallow_2026_07_27 (narrow the broad except),
      manifest_reader_silent_empty_on_missing_project_id_2026_07_24 (`_read_index.py` exception fix + unit test),
      bucket_fold_features_2026_07_17 (remove dead `_KIND_ALIASES`, partial — terraform half is deployment-service).

- [ ] [CODE] P2. **features-service (6 items) — UNDISPATCHED.** candle_canonical_path_migration_execution_2026_07_24
      (DataLoader chain-bundle detection — note: source doc now ARCHIVED, all 17 todos done, but verify this specific
      18th item wasn't already covered), cli_shard_split_flag_coverage_audit_2026_07_24 (4 MTDS chain-scoping flags +
      dead-handler check), features_cross_instrument_uses_start_date_not_end_date_2026_07_27 (end_date fallback),
      features_commodity_public_api_403_from_gcp_vm_2026_07_27 (User-Agent header),
      pipeline_e2e_check_non_canonical_input_misclassifies_absent_data_2026_07_27 (`_scan_input_coverage` filter fix +
      test), silent_wrong_answer_audit_candidates_2026_07_20 (2 already-drafted stashed fixes, need reconciling against
      peer's concurrent commit).

- [ ] [CODE] P2. **agent-orchestrator (~5 items) — UNDISPATCHED.**
      ao_done_gate_checkbox_flip_blind_to_self_archived_plan_ref_2026_07_26 (verify.py Mode-2 fallback + regression
      test), ao_m3_verify_plan_flip_blind_to_archival_rename_2026_07_26 (check_plan_flip git-rename following),
      spawn_base_role_stale_display_when_different_role_adopts_session_2026_07_25 (conditional-logic fix),
      ci_escalation_wall_type_mismatch_silent_human_only_2026_07_27 (WALL_TYPES grep+fold, partial — also touches
      unified-trading-pm workflow ymls).

- [ ] [CODE] P2. **unified-api-contracts (1 more item) — UNDISPATCHED.**
      prediction_satellite_ao_dispatch_batch5_2026_07_26's cqg-wiring half (the dead-code half already shipped via
      market-tick-data-service's batch, see above — verify current split).

- [ ] [CODE] P2. **instruments-service (~4-5 items) — UNDISPATCHED.**
      sports_t0_t1_dependency_gate_never_wired_2026_07_15 (thread `date=` through 6 call sites of
      `create_sports_reference_adapter()`), sports_player_stats_empty_write_followups_2026_07_26 (empty-write guard
      pattern), instruments_service_run_tag_flag_not_applied_2026_07_08 (--run-tag wiring + test),
      prediction_satellite_ao_dispatch_batch5_2026_07_26 (instruments-service half of cqg wiring),
      mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08 (baseline-ratchet `--update-baseline`,
      mechanical, shared with 4 other repos below).

- [ ] [CODE] P2. **deployment-service (~3 items) — UNDISPATCHED.**
      deployment_service_scheduler_job_name_reconstruction_bug_2026_07_27 (mirror unified-trading-library@080a84a0's
      `scheduler_env_prefix()` fix + live-verify), bucket_fold_features_2026_07_17 (terraform IAM Group-B join half),
      mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08 (baseline-ratchet, mechanical).

- [ ] [CODE] P2. **deployment-api (2 items) — UNDISPATCHED.** sports_manifest_read_staleness_budget_missing_2026_07_15
      (mirror the shipped "sports": 1800 entry into health_consolidator.py),
      deployment_api_cloud_build_600s_timeout_flake_2026_07_27 (raise cloudbuild.yaml timeout).

- [ ] [CODE] P2. **unified-trading-system-ui (2 items) — UNDISPATCHED.**
      ui_coverage_ts_venue_category_v2_rename_gap_2026_07_10 (VenueAssetGroupV2->VenueCategoryV2 rename + CROSS_CATEGORY
      member, UI half), ui_hardcoded_colour_and_localhost_debt_2026_07_21 (Batch 5 Playwright regression spec, needs
      `pw:L2 ✓` per the UI playwright-gate HARD RULE).

- [ ] [CODE] P3. **mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08 — mechanical baseline-ratchet re-run
      across 5 repos (deployment-service, instruments-service, ml-service, trading-agent-service, agent-orchestrator).**
      Identical `--update-baseline` command in each, config-only, hard-clamped down-only. Cheapest item in this whole
      backlog — good candidate to dispatch first next session.

## Full classification data (for re-deriving scope if this doc goes stale)

Raw per-doc classification (path | BUCKET | reason) for all 281 candidates, plus the mechanically-filtered 139
NOT_QUICK-by-keyword and the 420-doc 1-2-open-todo source list, are saved in the session scratchpad — NOT durable, will
vanish with the session:
`/private/tmp/claude-501/-Users-ikennaigboaka-Code-unified-trading-system-repos--tabs-4/60ea16ec-43a4-4dcc-a3f2-7baea3767b5e/scratchpad/{quick_candidates.tsv,not_quick_mechanical.tsv,one_to_two_todo_files.tsv,qc_batch_*}`.
If this issue doc and its per-repo item list above survive, the scratchpad files are not needed — everything actionable
is already transcribed above. If you need the 204 NOT_QUICK docs' reasoning (why they were correctly excluded), that's
in `qc_batch_*` — lower priority to save since excluding them was a negative/no-action result.

## Progress log

**2026-07-28** — Initial fan-out: 9 parallel read-only agents classified 281 docs. 2 parallel repo-fix agents dispatched
for Round 1 (market-tick-data-service, unified-api-contracts). unified-api-contracts shipped cleanly (`cb9e97dfd`).
market-tick-data-service hit 2 real quality-gates.sh violations (not transient — genuine file/function size overages)
and was left uncommitted, working-tree only, pending a proper trim. Rounds 2-6 (11 more repos, ~50 items) never got
dispatched — session moved to `/pre-compact` checkpointing before starting them, given context usage hit ~65%. This doc
captures the full remaining scope so it survives compaction.
