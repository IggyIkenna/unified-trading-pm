---
title: Resolved-issues archive audit — 2026-05-20
created: 2026-05-20
author: background agent (delegated by slot-1 main)
source:
  - operator directive 2026-05-20 "without clean issues outside this known audit we don't have a clean base"
  - 56 issue docs in plans/active/issues/ with `resolved:` frontmatter field
locked_by: live-defi-rollout
---

## Bucket counts

- ARCHIVE-CLEAN: 33
- ARCHIVE-WITH-SPOT-CHECK: 6
- RESOLUTION-SUSPECT: 11
- META: 6

Total: 56 (one file may be referenced under both ARCHIVE-CLEAN and META if it's a "shipped audit"; net unique files = 56).

---

## ARCHIVE-CLEAN list (33) — safe bulk archive

Resolution cites a concrete commit SHA or verifiable artefact + dated within the last 14 days. High trust.

| File | Resolution citation | Resolved date |
|---|---|---|
| alerting_service_codex_violations_d5_d7_2026_05_14.md | alerting-service@6a01b98 + UAC@0d7c8ca | 2026-05-14 |
| b_015_smoke_b_mdps_handler_gap_vault_share_price_2026_05_16.md | features-service@550cdaba | 2026-05-16 |
| b_015_smoke_vms_phantom_manifest_silent_skip_2026_05_15.md | ml-training@876f0e5 + deployment-service@a6f746f + features-service@d687df7d | 2026-05-17 |
| classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md | OPS-VERIFIED — classifier ran clean 2026-05-14 (TypeError gone) | 2026-05-14 |
| client_reporting_api_coverage_below_floor_2026_05_14.md | client-reporting-api@3b891b8 (coverage 75.10%) | 2026-05-17 |
| compound_kamino_lending_rates_gaps_2026_05_15.md | features-service@f448bb1a + @5b3599b4 + @a735750a | 2026-05-17 |
| databento_chunk_iteration_int_timestamp_2026_05_16.md | market-tick-data-service@f19ff5f | 2026-05-16 |
| databento_payment_required_classifier_missing_2026_05_17.md | UAC@50f3939 + MTDS@f42d6c0 | 2026-05-17 |
| defi_classifier_missing_catalog_crossref_2026_05_13.md | unified-trading-library@513d79fb + instruments-service@3670534 | 2026-05-17 |
| defi_features_pipeline_not_run_2026_05_14.md | ml-training@876f0e5 + deployment@a6f746f + features@d687df7d + instruments@b64877f + deployment@d65da47 | 2026-05-17 |
| defi_handler_phantom_risk_structural_2026_05_15.md | MTDS@f657431 + MTDS@c1e6963 (re-verified slot-3 2026-05-16) | 2026-05-16 |
| defi_legacy_blank_reclassification_2026_05_13.md | full fix shipped per body § "RESOLVED 2026-05-13 ~16:25 BST" | 2026-05-13 |
| deployment_api_shard_axis_matrix_uac_drift_2026_05_14.md | slot-8 Ikenna fix per body § "RESOLVED 2026-05-14" | 2026-05-14 |
| emerging_perp_adapters_diagnosed_2026_05_13.md | ASTER@b0419960 + HYPERLIQUID@74e77ebf | 2026-05-16 |
| execution_service_betfairlightweight_requests_dep_conflict_2026_05_16.md | both sides resolved 2026-05-16 (slot-4 + slot-1) | 2026-05-16 |
| expected_unattempted_propagation_gap_2026_05_12.md | uac@0457b0e + mdps@3f70cf6 + @f50db4e | 2026-05-17 |
| features_onchain_defi_processing_findings_2026_05_17.md | features-service@d687df7d (B-015 gate UNBLOCKED 2026-05-17 02:08 UTC) | 2026-05-17 |
| features_service_qg_test_path_mismatch_2026_05_15.md | features-service/scripts/quality-gates.sh PYTEST_UNIT_DIR override (verified 2026-05-17 by slot-3) | 2026-05-17 |
| features_service_size_violations_2026_05_14.md | features-service@29cd4ea6 | 2026-05-14 |
| features_vm_uv_resolution_unsatisfiable_2026_05_16.md | risk-and-exposure-service@83b10e0 + ml-training-service@876f0e5 + deployment-service@a6f746f | 2026-05-17 |
| helius_solana_rpc_for_validation_2026_05_13.md | MTDS@4cea371 + execution-service@a300f7caa + MTDS@348c171 | 2026-05-16 |
| honest_coverage_cron_vm_scheduling_2026_05_14.md | deployment-ui@365c32f + deployment-service@19454f1 | 2026-05-15 |
| lending_indices_phantom_manifest_rows_2026_05_17.md | instruments-service@b64877f (verified clean: 65 real / 0 phantom) | 2026-05-17 |
| mtds_market_interface_test_failures_2026_05_14.md | mtds@1515170 (1770 passed, 0 failed) | 2026-05-15 |
| phase_3c_lending_rate_model_0_of_60_pass_2026_05_13.md | execution-service@f45a5f669 + @70825a432 + UAC@215ed3e (gate GREEN 2026-05-17 06:55 UTC) | 2026-05-17 |
| sit_may23_critical_path_coverage_gaps_2026_05_15.md | system-integration-tests@3872ce2 (28 tests pass) | 2026-05-16 |
| sports_classifier_weather_no_fixture_2026_05_13.md | instruments-service@f799109 + utl@79c72bad | 2026-05-16 |
| strategy_paper_vm_nautilus_trader_missing_dep_2026_05_14.md | e2e-testing@4e4a5da | 2026-05-14 |
| strategy_service_phase10_codex_drift_2026_05_15.md | execution-service@7957371d + strategy-service@f01d12d | 2026-05-17 |
| strategy_service_qg_ltv_threshold_violations_2026_05_15.md | strategy-service inline annotations (verified 2026-05-17 slot-3) | 2026-05-17 |
| utl_configstore_resolve_save_path_oom_2026_05_15.md | utl@93ff771 (root cause fixed) | 2026-05-15 |
| utl_qg_failures_2026_05_15.md | unified-trading-library@e8bb4fd2 + UTL@828d6ff3 | 2026-05-17 |
| validate_manifest_coverage_stale_catalogue_path_2026_05_17.md | market-tick-data-service@c758048 | 2026-05-17 |

Bulk-archive command (operator runs):
```bash
cd /Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/1/unified-trading-pm/plans/active/issues/
mkdir -p ../../archive/issues/  # already exists; idempotent
git mv \
  alerting_service_codex_violations_d5_d7_2026_05_14.md \
  b_015_smoke_b_mdps_handler_gap_vault_share_price_2026_05_16.md \
  b_015_smoke_vms_phantom_manifest_silent_skip_2026_05_15.md \
  classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md \
  client_reporting_api_coverage_below_floor_2026_05_14.md \
  compound_kamino_lending_rates_gaps_2026_05_15.md \
  databento_chunk_iteration_int_timestamp_2026_05_16.md \
  databento_payment_required_classifier_missing_2026_05_17.md \
  defi_classifier_missing_catalog_crossref_2026_05_13.md \
  defi_features_pipeline_not_run_2026_05_14.md \
  defi_handler_phantom_risk_structural_2026_05_15.md \
  defi_legacy_blank_reclassification_2026_05_13.md \
  deployment_api_shard_axis_matrix_uac_drift_2026_05_14.md \
  emerging_perp_adapters_diagnosed_2026_05_13.md \
  execution_service_betfairlightweight_requests_dep_conflict_2026_05_16.md \
  expected_unattempted_propagation_gap_2026_05_12.md \
  features_onchain_defi_processing_findings_2026_05_17.md \
  features_service_qg_test_path_mismatch_2026_05_15.md \
  features_service_size_violations_2026_05_14.md \
  features_vm_uv_resolution_unsatisfiable_2026_05_16.md \
  helius_solana_rpc_for_validation_2026_05_13.md \
  honest_coverage_cron_vm_scheduling_2026_05_14.md \
  lending_indices_phantom_manifest_rows_2026_05_17.md \
  mtds_market_interface_test_failures_2026_05_14.md \
  phase_3c_lending_rate_model_0_of_60_pass_2026_05_13.md \
  sit_may23_critical_path_coverage_gaps_2026_05_15.md \
  sports_classifier_weather_no_fixture_2026_05_13.md \
  strategy_paper_vm_nautilus_trader_missing_dep_2026_05_14.md \
  strategy_service_phase10_codex_drift_2026_05_15.md \
  strategy_service_qg_ltv_threshold_violations_2026_05_15.md \
  utl_configstore_resolve_save_path_oom_2026_05_15.md \
  utl_qg_failures_2026_05_15.md \
  validate_manifest_coverage_stale_catalogue_path_2026_05_17.md \
  ../../archive/issues/
```

---

## ARCHIVE-WITH-SPOT-CHECK (6)

Resolution looks done but cites no SHA, or vague "slot N" attribution. Spot-verify with the one-liner before archive.

| File | Spot-check command | Expected pass condition |
|---|---|---|
| sports_classifier_player_values_cadence_2026_05_13.md | `cd unified-trading-library && git log --since=2026-05-13 --until=2026-05-15 --grep="PLAYER_VALUES" --oneline` | non-empty (slot-4 player-values rule landed) |
| sports_classifier_sfi_footystats_fixture_pin_2026_05_13.md | `cd unified-trading-library && git log --since=2026-05-13 --until=2026-05-15 --grep="footystats\|SFI_PROGRESSIVE" --oneline` | non-empty |
| sports_classifier_extension_followup_2026_05_13.md | `cd unified-trading-library && git log --since=2026-05-13 --until=2026-05-15 --grep="classifier" --oneline` and verify 4 child issues all resolved | child issues all RESOLVED |
| mtf_intraday_micro_regime_policy_2026_05_14.md | `cd unified-api-contracts && grep -n "intraday_regime\|micro_regime" unified_api_contracts/internal/emission_policies.py` | NAN_FILL entries present |
| mtb_p6e_qg_sweep_2026_05_15.md | `cd ml-training-service && bash scripts/quality-gates.sh 2>&1 \| grep -E "coverage\|FAIL\|PASS" \| head` | coverage ≥70% (ml-training@7e18af8 referenced in resolution) |
| utl_bump_label_mismatch_audit_2026_05_15.md | n/a — audit doc concludes "no action needed on shipped versions" | n/a (audit-complete; archive as historical record) |

---

## RESOLUTION-SUSPECT (11) — re-open candidates

Resolution claim is partial, deferred, or contradicted by named follow-up work. Recommend either RE-OPEN (strip `resolved:` + add `RE-OPENED 2026-05-20` note) or convert to BLOCKED-* status per CLAUDE.md taxonomy.

| File | Why suspect | Recommended action |
|---|---|---|
| **gcp_sa_private_key_in_git_history_execution_service_2026_05_15.md** | Key is dead BUT BFG history scrub "DEFERRED-MAINTENANCE-WINDOW per body" — git history still leaks SA private key across 5 repos. Severity was P0. | RE-OPEN as P3 with `BLOCKED-OPERATOR-DECISION` (force-push-to-main approval); cross-link to companion github_pat issue |
| **github_pat_in_instruments_service_env_2026_05_15.md** | PAT revoked (returns 401) BUT BFG scrub "DEFERRED-MAINTENANCE-WINDOW; batched with companion gcp_sa_private_key issue" | RE-OPEN with same BLOCKED status; archive only after BFG runs |
| deprecated_pattern_sweep_2026_05_15.md | P1+P2 shipped; P3 (UTL 126 type:ignore) + P4 (bare noqa audit) "explicit P3 sprint-aligned with per-repo team named successors" — successor plans not named in frontmatter | Add explicit successor plan filename to resolution block, then archive |
| emerging_perp_venue_adapters_broken_2026_05_13.md | 4/5 venues unblocked; EXTENDED-STARKNET "remains BLOCKED-OPERATOR-DECISION (canonical API URL)" | RE-OPEN as `BLOCKED-OPERATOR-DECISION` per CLAUDE.md taxonomy; file operator ping |
| features_service_deprecated_launcher_wrappers_misroute_2026_05_16.md | PARTIAL — onchain wrapper redirected; "remaining (P3 follow-up): launch-features-backfill-vm.sh keeps legacy delegation for 7 family wrappers" | RE-OPEN as P3 with named successor or archive only after follow-up plan named |
| features_service_volatility_test_failures_2026_05_15.md | MOSTLY-SHIPPED 48→13 failures (73% reduction); "remaining 13 — slot-4 picks up the long tail" | RE-OPEN as P2-narrow-scope; 13 failures still in QG step |
| lst_apr_sourcing_method_validated_2026_05_14.md | Validation work ✅ + Marinade BLOCKED-OPERATOR-DECISION ✅; "Single P2 SCRIPT remains DEFERRED-POST-CUTOVER (coinbase_wrapped_assets.py)" | Archive — has named DEFERRED-POST-CUTOVER successor scope acceptable per CLAUDE.md; verify successor plan exists |
| test_memory_bloat_workspace_2026_05_15.md | Structural fix landed (PYTEST_WORKERS=1 + ulimit cap); "Per-repo memray audit + UTL <1 GB RSS optimization is NICE-TO-HAVE follow-up, NOT blocking May-23" | Archive — root-cause fixed; NICE-TO-HAVE follow-up acceptable |
| uac_qg_preexisting_size_violations_2026_05_14.md | Short-term: raised `CODEX_MAX_VIOLATIONS=5` (config bump, NOT a code fix); 5 files still exceed thresholds. "P2 + P3 follow-ups are nice-to-haves" | RE-OPEN as P3 — the original violations still exist; threshold was raised to mask them |
| utl_qg_preexisting_failures_2026_05_14.md | SUBSTANTIVELY-SHIPPED 4/5 categories; "Item 2 (3 backward-compat shims) partially done; remaining instances dispersed across UTL — file as P3 ongoing-cleanup" | RE-OPEN as P3 or move to UTL-ongoing-cleanup plan with successor named |
| solana_defi_coverage_gaps_2026_05_13.md | "SPLIT INTO 5 SUCCESSOR PLANS" — meta-tracker. Marinade follow-up explicitly OPEN per resolution: "Open Marinade follow-up has separate issue marinade_solana_subgraph_registration_2026_05_17.md" | META — see below; archive the tracker, keep marinade issue open |

---

## META (6) — misplaced or tracker docs

Not really issue docs — these are audit reports / trackers / decision logs that landed in `issues/` by accident.

| File | What it actually is | Suggested move target |
|---|---|---|
| audit_wave1_quality_2026_05_13.md | Wave-1 retrospective for slots 2-9 execution review (19 findings catalogued; child issues self-routed) | `plans/archive/issues/` is fine (it's a closed audit); consider `plans/audit/` if that dir exists |
| codex_04_architecture_drift_audit_2026_05_15.md | Full pass over codex/04-architecture/ — drift audit report | `plans/archive/issues/` (audit closed clean, only 3 lines of stale ref cleanup) |
| mtb_p6e_qg_sweep_2026_05_15.md | B-014 rollout 6-repo QG result table (sweep report, not an issue) | `plans/archive/issues/` (sweep complete, all 6 repos ≥70%) |
| solana_defi_coverage_gaps_2026_05_13.md | Triage doc that split scope into 5 successor plans (meta-tracker) | `plans/archive/issues/` (its role was scope-split, now complete) |
| utl_bump_label_mismatch_audit_2026_05_15.md | Historical bump-label audit (no retroactive fix; "current next-bump correct") | `plans/archive/issues/` (audit-complete, historical record) |
| writegate_phase_6_6_7_9_alpha_vs_beta_decision_2026_05_14.md | Scope-audit / decision verdict doc (α-vs-β framing audit) | `plans/archive/issues/` (decision recorded, Gate 4 FIRED) |

Note: all 6 META files can safely archive in the same `git mv` batch — they are closed records, not live issues. The "META" tag is just informational to flag that future similar audit/sweep/decision docs would be better placed in `plans/audit/` or as plan-internal appendices rather than `issues/`.

---

## Suggested batched commands (operator-ready)

After spot-checking the 6 ARCHIVE-WITH-SPOT-CHECK entries:

```bash
cd /Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/1/unified-trading-pm/plans/active/issues/

# Batch 1: 33 ARCHIVE-CLEAN (command in § ARCHIVE-CLEAN list above)

# Batch 2: 6 ARCHIVE-WITH-SPOT-CHECK (after each spot-check passes)
git mv \
  sports_classifier_player_values_cadence_2026_05_13.md \
  sports_classifier_sfi_footystats_fixture_pin_2026_05_13.md \
  sports_classifier_extension_followup_2026_05_13.md \
  mtf_intraday_micro_regime_policy_2026_05_14.md \
  mtb_p6e_qg_sweep_2026_05_15.md \
  utl_bump_label_mismatch_audit_2026_05_15.md \
  ../../archive/issues/

# Batch 3: 6 META (all closed audit/tracker/decision docs)
git mv \
  audit_wave1_quality_2026_05_13.md \
  codex_04_architecture_drift_audit_2026_05_15.md \
  solana_defi_coverage_gaps_2026_05_13.md \
  writegate_phase_6_6_7_9_alpha_vs_beta_decision_2026_05_14.md \
  ../../archive/issues/
# (mtb_p6e_qg_sweep + utl_bump_label_mismatch_audit already moved in Batch 2)

# Batch 4: 9 RESOLUTION-SUSPECT that operator decides are archive-OK (lst_apr + test_memory_bloat may pass on review)
# Do NOT auto-archive — operator reviews each first.

# Commit
git add -A
git commit -m "$(cat <<'EOF'
docs(plans): archive 45 resolved issue docs per audit 2026-05-20

Archives 33 ARCHIVE-CLEAN + 6 ARCHIVE-WITH-SPOT-CHECK + 6 META per
plans/active/issues/resolved_issues_archive_audit_2026_05_20.md.

11 RESOLUTION-SUSPECT entries retained in active/issues/ pending
operator triage (see audit doc § RESOLUTION-SUSPECT).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Most worrying RESOLUTION-SUSPECT entries (operator attention)

1. **`gcp_sa_private_key_in_git_history_execution_service_2026_05_15.md`** — P0 security issue downgraded to P3 "DEFERRED-MAINTENANCE-WINDOW" because BFG history scrub requires force-push to 5 repos. Key is dead but **git history still contains the private key file**. Any cloning of these 5 repos by anyone (including future contractors / open-sourcing) leaks the historical key. Operator should decide: schedule force-push window OR accept residual risk + document acceptance.
2. **`github_pat_in_instruments_service_env_2026_05_15.md`** — Same pattern as above. PAT revoked but git history still contains `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` substring. Same operator decision needed.
3. **`uac_qg_preexisting_size_violations_2026_05_14.md`** — "Fix" was raising `CODEX_MAX_VIOLATIONS=5` to mask 5 over-threshold files. The files (alerting/rules.py 994L, defi.py 1365L, etc.) still violate. This is a debt-deferral disguised as a resolution — should be RE-OPENED or have a named successor plan.
4. **`emerging_perp_venue_adapters_broken_2026_05_13.md`** — 4/5 fine; EXTENDED-STARKNET still BLOCKED-OPERATOR-DECISION. Per CLAUDE.md "External Data Is Always Available" rule, this should be `BLOCKED-OPERATOR-DECISION` status (closed-set design call on canonical API URL), not `resolved:`. File operator ping if not already done.

---

## Notes

- All 56 files dated within last 14 days (created 2026-05-12..17; today 2026-05-20) — no stale resolutions.
- No duplicate root-causes detected (sports_classifier_extension_followup IS the parent of player_values + sfi_footystats + weather, with explicit child_issues frontmatter — handled cleanly).
- 4 child sports_classifier_* docs form a coherent cluster — archive together.
- B-015 chain (paper-trade gate) generated 7 issue docs that all resolved 2026-05-17 with overlapping SHAs (features-service@d687df7d, ml-training@876f0e5, deployment-service@a6f746f) — bulk-archive safe.
- Recommendation: if operator wants the lowest-friction path, archive the 33 ARCHIVE-CLEAN today; defer the 6 spot-check + 11 suspect to a per-item decision pass; flag the 2 security issues for an explicit accept-residual-risk-or-scrub decision.
