---
title: Clean-rule re-audit of plans/active/issues/ — 2026-05-20
created: 2026-05-20
author: background agent (delegated by slot-1)
locked_by: live-defi-rollout
codifies_rule_from:
  - /codex/11-project-management/issue-doc-lifecycle.md
  - CLAUDE.md § Citadel-Grade Planning Standards item (9)
---

> **Purpose**: enumerate every dual-tracking violation in `plans/active/issues/` against the new Issue-Doc Lifecycle
> Discipline rule (issue docs surface UNACKED work only; ack → immediate archive; "stays until parent closes" lifecycles
> are dual-tracking and review-blocking). Operator reviews this audit before any `git mv` runs.

## Total files in plans/active/issues/ scanned: 32

## Dual-tracking violations: 18

(21 raw banner + frontmatter hits; 3 are false positives — see "Excluded false positives" below.)

### ACKED-INTO-PLAN (15 files) — archive immediately

#### Sub-bucket 1 — `🟡 SUBSUMED BY MEGA AUDIT` (8 files)

All point at `mega_audit_and_plan_beefup_progression_2026_05_20.md` with a named phase. Findings live in the mega-audit
body; standalone work is explicitly disallowed by the banner ("Do NOT work standalone").

| File                                                                       | Parent plan + phase             | Banner type |
| -------------------------------------------------------------------------- | ------------------------------- | ----------- |
| `execution_service_method_size_violations_workspace_outlier_2026_05_17.md` | mega_audit Phase D6             | 🟡 SUBSUMED |
| `execution_service_test_harness_missing_methods_2026_05_18.md`             | mega_audit Phase C7             | 🟡 SUBSUMED |
| `expected_unattempted_validation_pending_phase3_2026_05_19.md`             | mega_audit Phase A3             | 🟡 SUBSUMED |
| `features_service_todo_audit_2026_05_19.md`                                | mega_audit Phase C4 + C6        | 🟡 SUBSUMED |
| `qg_basedpyright_or_true_bug_2026_05_18.md`                                | mega_audit Phase D (QG ratchet) | 🟡 SUBSUMED |
| `smoke_b_perp_funding_type_schema_drift_2026_05_17.md`                     | mega_audit Phase C4             | 🟡 SUBSUMED |
| `tardis_smarkets_test_regression_2026_05_17.md`                            | mega_audit Phase C0 + C9        | 🟡 SUBSUMED |
| `uac_coverage_excludes_blank_8b_8c_ratchet_2026_05_17.md`                  | mega_audit Phase D + D3         | 🟡 SUBSUMED |

#### Sub-bucket 2 — `🟡 COVERED BY` named active plan (5 files)

Banner cites a named parent plan in `plans/active/`. Findings absorbed; the issue doc is residual dual-tracking.

| File                                                         | Parent plan                                                                                                        | Banner type   |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ | ------------- |
| `bucket_name_ssot_residual_drift_2026_05_18.md`              | `bucket_name_ssot_canonicalisation_2026_05_10.md` Done-def #6                                                      | 🟡 COVERED BY |
| `ml_repo_consolidation_preaudit_2026_05_19.md`               | `ml_repo_consolidation_2026_05_19.md` (Phase 0 artefact)                                                           | 🟡 COVERED BY |
| `paper_defi_pre_run_data_readiness_2026_05_19.md`            | `phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md` + `promote_workflow_may23_cli_path_2026_05_10.md` | 🟡 COVERED BY |
| `prediction_polymarket_phantom_manifest_14403_2026_05_19.md` | `gcs_migration_bundle_pipeline_mode_2026_05_08.md` Phase 3.6 + `gate_3_phantom_audit_runbook_2026_05_13.md`        | 🟡 COVERED BY |
| `strategy_repo_consolidation_preaudit_2026_05_19.md`         | `strategy_repo_consolidation_2026_05_19.md` (Phase 0 artefact)                                                     | 🟡 COVERED BY |

> **Operator-attention boundary case** (sub-bucket 2): `strategy_repo_consolidation_preaudit_2026_05_19.md` banner
> itself notes "corrects the earlier 'ZERO cross-repo imports' fact-report — that correction must land in the parent
> plan body before Phase 4 import-rewrite." Before archiving, ensure the 25-imports correction is migrated into the
> parent plan's body, or the consolidation will regress on archival.

#### Sub-bucket 3 — `🔴 RE-OPENED` with named successor (2 files)

Banner re-opens the doc but explicitly names mega_audit Phase D as successor. Per new rule, RE-OPENED with named
successor = ACKED-INTO-PLAN (not STILL-UNACKED).

| File                                               | Named successor                               | Banner type  |
| -------------------------------------------------- | --------------------------------------------- | ------------ |
| `uac_qg_preexisting_size_violations_2026_05_14.md` | mega_audit Phase D (cross-cutting QG ratchet) | 🔴 RE-OPENED |
| `utl_qg_preexisting_failures_2026_05_14.md`        | mega_audit Phase D (cross-cutting QG ratchet) | 🔴 RE-OPENED |

### ACKED-INTO-CODE (3 files) — archive immediately

| File                                                                | Commit SHA(s)                                                                         | Banner / frontmatter                       |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------ |
| `emerging_perp_venue_adapters_broken_2026_05_13.md`                 | instruments-service@`35f920e`, MTDS@`78e3b28`, MTDS@`412af64` (5 of 5 venues fixed)   | `resolved: 2026-05-20` / FULLY-RESOLVED    |
| `gcp_sa_private_key_in_git_history_execution_service_2026_05_15.md` | Key dead (`NOT_FOUND`); BFG scrub split to `bfg_history_scrub_sequence_2026_05_20.md` | `resolved: 2026-05-15` / SECURITY-RESOLVED |
| `github_pat_in_instruments_service_env_2026_05_15.md`               | PAT revoked (HTTP 401); BFG scrub split to `bfg_history_scrub_sequence_2026_05_20.md` | `resolved: 2026-05-15` / SECURITY-RESOLVED |

### ACKED-OUT-OF-SCOPE (0 files)

None observed in this sweep.

### ACKED-AS-INVALID (0 files)

None observed.

## STILL-UNACKED (3 files) — KEEP IN active/issues/

- **`bfg_history_scrub_sequence_2026_05_20.md`** — operator approved 2026-05-20 ("sure do it"), but execution has not
  landed. Body grep-matched the audit regex only because it _quotes_ a future banner template, not because the doc
  itself is acked. Trigger to archive: BFG executed across all 5 repos + force-push verified
  - companion `gcp_sa_private_key` + `github_pat` archive sweep done.
- **`defi_46day_backfill_launch_status_2026_05_20.md`** — 🟢 LAUNCHED banner, but this IS an operational tracker for
  in-flight VMs (T+10min verification armed; banner says "removed when manifest divergence A3 confirms zero
  MISSING_EXPECTED"). Trigger to archive: A3 confirms or VMs terminate STOPPED with manifest green. Note: this is the
  closest call in the audit — arguably an A3-acked-into-plan today; defaulted to STILL-UNACKED because the 12-VM
  operational state has no other tracker in `plans/active/`.
- **`defi_upstream_46day_full_backfill_2026_05_16.md`** — parent of the launch-status tracker above; same rationale.
  Could be archived when its child closes.

## Bulk archive command (do NOT execute until operator review)

```bash
cd unified-trading-pm
git mv plans/active/issues/execution_service_method_size_violations_workspace_outlier_2026_05_17.md \
       plans/active/issues/execution_service_test_harness_missing_methods_2026_05_18.md \
       plans/active/issues/expected_unattempted_validation_pending_phase3_2026_05_19.md \
       plans/active/issues/features_service_todo_audit_2026_05_19.md \
       plans/active/issues/qg_basedpyright_or_true_bug_2026_05_18.md \
       plans/active/issues/smoke_b_perp_funding_type_schema_drift_2026_05_17.md \
       plans/active/issues/tardis_smarkets_test_regression_2026_05_17.md \
       plans/active/issues/uac_coverage_excludes_blank_8b_8c_ratchet_2026_05_17.md \
       plans/active/issues/bucket_name_ssot_residual_drift_2026_05_18.md \
       plans/active/issues/ml_repo_consolidation_preaudit_2026_05_19.md \
       plans/active/issues/paper_defi_pre_run_data_readiness_2026_05_19.md \
       plans/active/issues/prediction_polymarket_phantom_manifest_14403_2026_05_19.md \
       plans/active/issues/strategy_repo_consolidation_preaudit_2026_05_19.md \
       plans/active/issues/uac_qg_preexisting_size_violations_2026_05_14.md \
       plans/active/issues/utl_qg_preexisting_failures_2026_05_14.md \
       plans/active/issues/emerging_perp_venue_adapters_broken_2026_05_13.md \
       plans/active/issues/gcp_sa_private_key_in_git_history_execution_service_2026_05_15.md \
       plans/active/issues/github_pat_in_instruments_service_env_2026_05_15.md \
       plans/archive/issues/
git commit -m "docs(plans): archive 18 acked issue docs per clean-rule sweep 2026-05-20"
```

## Excluded false positives (3)

These hit the banner regex but are NOT dual-tracking violations:

- `bfg_history_scrub_sequence_2026_05_20.md` — body quotes a future "🟢 RESOLVED 2026-05-20" banner template used during
  BFG execution; the doc itself is operator-approved-but-unexecuted. Kept active.
- `defi_46day_backfill_launch_status_2026_05_20.md` and `defi_upstream_46day_full_backfill_2026_05_16.md` — 🟢 LAUNCHED
  banner is operational status, not an ack-into-another-plan. See STILL-UNACKED rationale above.

## Notable patterns observed

**Mega-audit centroid (8 of 18 violations).** The `mega_audit_and_plan_beefup_progression_2026_05_20.md` triage sweep on
the same day this audit ran absorbed 8 issue docs in one motion (Phase C0/C4/C6/C7/C9 + D/D3/D6). The 🟡 SUBSUMED BY
MEGA AUDIT banner is internally consistent (every one cites a specific phase). This is the single largest cleanup
opportunity — bulk-archiving these 8 files reduces active/issues/ by 25% and removes the orchestration ambiguity where
slots could pick up subsumed work standalone.

**Phase-0 pre-audit artefacts (2 files) belong elsewhere.** `ml_repo_consolidation_preaudit` and
`strategy_repo_consolidation_preaudit` are diagnostic artefacts feeding named consolidation plans — these should live
under `plans/audit/` (mirroring the mega-audit C-audit location convention) rather than `plans/active/issues/`. The
`ml_repo_consolidation_preaudit` banner itself flags this future convention. Operator may want a follow-up move
(active/issues → plans/audit/) rather than archive.

**Security pair (2 files) gated on hygiene scrub (1 file).** The two `resolved: 2026-05-15` security issues (GCP SA key,
GitHub PAT) chain into the still-open `bfg_history_scrub_sequence_2026_05_20.md`. The security issues are correctly
acked-into-code (keys are dead) — archive them now; BFG hygiene plan stays active until executed. The cross-references
in the BFG plan's frontmatter `related_plans` will continue to resolve against archived parents.

**RE-OPENED pattern composes correctly with the new rule.** Two QG-debt issues (`uac_qg_preexisting_size_violations`

- `utl_qg_preexisting_failures`) were re-opened today with the explicit successor named in the banner — this is exactly
  the "named successor = ack-into-plan" path the new SSOT requires. No special handling needed.
