---
doc_type: issue
title: plan_reconciler findings — ci tranche — 2026-08-10
summary: >-
  Daily deep plan-reconciliation run-findings doc for the ci topic tranche, dispatch agt-fb0ce4 (slot 2). Records
  hunter-detected candidates, adversarial-verification outcomes, applied fixes, routed operator questions, and coverage
  for this run. Also the progress journal for the run itself.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [role, plan_reconciler, reconciliation, plan-hygiene, ci, sharded-run]
related:
  [
    /plans/active/issues/plan_reconciler_findings_ci_2026_08_09.md,
    /plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md,
  ]
created: "2026-08-10"
author: plan_reconciler
source: agt-fb0ce4
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline: 0.1
calibrated_ai_days: 0.1
assigned_role: backend_engineer
drift_direction: fix
resolved_by:
locked_by: plan_reconciler (agt-fb0ce4) since 2026-08-10T05:19:46Z
depends_on: []
---

# plan_reconciler findings — ci tranche — 2026-08-10

Dispatch `agt-fb0ce4`, slot 2, tranche `ci`. PM head at run start: `7930a990ec`.

## Scope

**57 docs carry `asset_group: ci`** in `plans/active/` (incl. `issues/`) — computed via a YAML-safe frontmatter parse
(`yaml.safe_load`, same method `docspec.py::parse_frontmatter` uses — comment-safe, avoids the over-match artifact
yesterday's run found in a naive grep). **25 of 57 are inside the 12-hour grace window** (heavy concurrent fleet
activity on this tranche continues — batch12/batch12_finalize pairs, today's `ag_closeout_audit_ci_parked_2026_08_10`,
several same-day issue docs) and are READ-ONLY context this run. **32 are writable** (outside grace) — see Coverage for
the full list.

The `ci` tranche's former epic hub `ci_consolidated_closeout_2026_07_25.md` is already archived
(`plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md`); no active doc carries
`parent_epic: ci_consolidated_closeout` outside the `asset_group: ci` set already captured above.

**Predecessor-run continuity**: `plan_reconciler_findings_ci_2026_08_09.md` (dispatch `agt-04cb0e`, slot 29) is still
`locked_by: plan_reconciler (agt-04cb0e) since 2026-08-09T16:22:00Z` with only 2 commits ever landed against it (start +
one checkpoint) and several sections left `(pending)` — it appears to have died mid-flight before reaching STEP 7 (the
"7 of 8 daily attempts reaped-stale" failure mode the sharded-dispatch design itself cites). Per this skill's own HARD
LIMIT, a `locked_by:` doc is never auto-unlocked by a later run — noted as a routed hygiene finding (see Routed/Filed)
rather than edited directly. `plan_reconciler_ci_late_findings_2026_08_06.md` is fully resolved except 2
deliberately-left-open P3 cosmetic items (archived-doc typo; editorial-judgment title rewrite) — both already correctly
classified as not worth extracting, re-confirmed, not re-litigated this run.

## Flips verified

None this run so far (hunter batch 3/6 report no checkbox-flip candidates with HARD evidence — every open todo checked
is either genuinely open or already correctly flipped).

## Contradictions

1. **`quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md`** — self-contradiction (P3, one doc): the
   `## Suggested next steps` numbered list (items 2 and 4) still read as "not yet fixed"/"not done this session", but
   the `## Todos` section below it was already corrected 2026-08-07 (na-eligibility-audit) to state both steps shipped
   (`unified-trading-library@dc1dc7df`; fleet grep "none found"). Independently re-verified: Todos section is
   authoritative (carries the sha + dated correction marker). **FIXED**: annotated items 2+4 in the numbered list as
   done, citing the Todos section — `unified-trading-pm` (this run's commit).
2. **`ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md`** — self-contradiction (P1, one doc), hunter
   batch 1: the `## Deferred work after 2026-08-06` table (2 rows) was never resynced after later checkboxes flipped —
   "Fix the 6 plan-hygiene ratchets" shows `[x] DONE — closed 2026-08-07` at line 594 but the table still says "Not
   done" at line 703 (+ a "Recommended NEXT item" pointer at line 706 telling a reader to redo already-finished work);
   "Downsize CI VM / planning VM" shows both `[x] DONE 2026-08-08`/`[x] DONE 2026-08-07` at lines 638/687 but the table
   still says "Operator-owned... pending" at line 701. Independently re-verifying line numbers before fixing (see
   Progress Log) — not yet applied as of this checkpoint.
3. **`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`** — stale "protected repos" list (P1, hunter batch
   1): line 845's "6 explicitly-protected repos" (incl. `greeks-service`, `ibkr-gateway-infra`, `instruments-service`,
   `fund-administration-service`) is superseded — 4 of those 6 were public repos REMOVED from self-hosted entirely on
   2026-08-05 per the live `scripts/workflow-templates/self-hosted-qg-repos.txt` header and corroborated by
   `ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md`'s own more-current list. Not yet independently
   re-verified against the live file or fixed as of this checkpoint.
4. **K=cores/4 physical-vs-logical-core disagreement** (P2, hunter batch 1, cross-doc): `ci_vm_io_starvation_audit...`
   (2026-08-06) claims the governor code uses physical cores (`floor(8/4)=2`); `qg_host_adaptive_resource_governor...`
   (2026-08-09, "NEW FINDING") claims it actually uses `lscpu -p=core` logical-CPU counting with no HT dedup, so K could
   be up to 2x too permissive on this host class. This is a claim about actual CODE behavior — provable by reading
   `_qg_governor_default_k()` directly. Not yet independently verified as of this checkpoint.

## Doc-drift

Batch 1's codex checks came back clean (4 codex docs spot-checked, no drift). Batch 4 found one real item — see Codex
corrections below. Batches 2/5/6 still arriving.

- **`fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md:related`** doesn't list
  `github_actions_operator_gated_followups_2026_07_17.md` even though named directly in that doc's own "Why this plan
  exists" prose (batch 4, P3, mechanical). Not yet fixed as of this checkpoint.
- **`shared_ci_workflow_repo_extraction_2026_08_06.md` todo 3's premise is false** (batch 4, P3): its cited
  "UNCONFIRMED" propagation-mechanism gap was already resolved the PREVIOUS DAY in
  `self_hosted_runner_public_repo_revert_2026_08_05.md` todo 1 (DONE 2026-08-05) — `rollout-workflow-templates.sh`
  byte-copies via a directory glob (confirmed at line 410), no per-file registration needed. Batch 4 independently
  triple-confirmed (script read, file-existence-since-2026-06-27, sibling doc's already-resolved todo 1). Recommend
  closing todo 3 as moot, not doing the work. Not yet fixed as of this checkpoint.
- **`github_actions_operator_gated_followups_2026_07_17.md`'s Phase-7 "fully shipped" checkbox lacks a forward-pointer**
  (batch 4, P3) to the later, much larger `self_hosted_runner_public_repo_revert_2026_08_05.md` (17-18 of the same
  fanned-out repos reverted back to `ubuntu-latest` for public-repo billing/visibility reasons) — doc 1 only records an
  unrelated single-repo caveat (deployment-ui/host-contention). Not currently misleading in a P0/P1 sense (both docs are
  individually accurate for their own dates), but worth a pointer. Not yet fixed as of this checkpoint.

## Codex corrections applied (mechanical, evidence-cited)

- **`/codex/08-workflows/ci-cd-flow.md:1258-1262`** claims `staging-lock-check.yml` is "still full content —
  deliberately NOT yet converted, see todo 11 in `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md`" —
  but that todo 11 is `[x]` **DONE 2026-08-08** (all 24 repos converted, template source deleted). Independently
  re-verified via `ls scripts/workflow-templates/`: `staging-lock-check.yml` is genuinely absent (only
  `image-build-gate.yml`, `notify-slack.yml`, `quality-gates-v2.yml.tmpl` remain, matching the plan's own
  dry-run-verified claim). Qualifies for the mechanical codex-staleness auto-apply carve-out (STEP 5.f2): HARD evidence
  (live filesystem + a verified-DONE todo), single unambiguous substitution, no HARD-STOP governance area touched, no
  new measurement needed. **Not yet applied as of this checkpoint** — queued for the consolidated STEP 5 pass once all
  hunter batches land, so the codex edit and its citation land together.

## Hygiene fixes

**Applied (hunter batch 3, independently re-verified before fixing):**

1. `quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21.md` `related:` entry pointed to
   `plans/active/issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md`, which no longer exists
   there — confirmed via `ls` (target absent at that path, present at
   `plans/archive/issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md`, `status: resolved`).
   Repointed to the leading-slash archive path.
2. `mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md` had 2 of 3 `related:` entries missing the
   leading-slash repo-root-relative convention — confirmed both targets exist at their stated paths (not dangling, pure
   format). Added leading slashes to both.

Corpus-wide `run_hygiene_sweep.sh --ci` hard failures at run start (3): `prettier proseWrap continuation-padding`
(ratchet), `Reference path convention` (ratchet), `assigned_vm:NA corpus size` (ratchet). Per 2026-08-09's precedent,
checked whether any land in-tranche before actioning — **none do** (corpus-wide ratchets with standing owners, not
ci-tranche findings): re-ran `check_reference_paths.py` directly (no `--quiet`) mid-run — both its format (62
violations, baseline 81) and existence (61 dangling, baseline 86) sub-checks currently PASS their ratchets (the `--ci`
sweep's FAIL at run-start was a transient snapshot on this high-churn shared branch, not a stable state — see Progress
Log), and zero of the 123 itemized violations touch any `asset_group: ci` doc as either violator or target.
`assigned_vm:NA corpus size` is a pure corpus-wide count ratchet with no per-tranche attribution and an explicitly
disjoint owner (`/na-eligibility-audit` — this skill does not adjudicate NA-classification correctness, per its own
scope note). No ci-tranche hygiene action needed from the Phase-0 corpus-wide checks.

## Filed

(pending)

## Archive candidates (operator review)

- **`ui_build_warm_cache_2026_06_17.md`** — flagged by today's `ag_closeout_audit_ci_parked_2026_08_10.md` as now
  zero-open-work, archival blocked only by `locked_by: live-defi-rollout`. Independently re-verified: 0 open / 4 done
  checkboxes (`grep -cE '^[[:space:]]*[-*] \[ \]'` / `\[x\]`), `status: complete`, `locked_since:` blank. **This is the
  same `locked_by: live-defi-rollout` placeholder-lock defect** a sibling ui-tranche run root-caused and filed today as
  `/plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md` (P1, `[OPERATOR]`, pending an
  A/B/C ruling — NOT a genuine lock, traced to `scripts/plans/fix_epic_frontmatter_2026_05_21.py:133`). Not re-filed as
  a duplicate; this doc is 2 more corroborating hits for that ticket, not a new finding. Also found in-tranche with the
  identical signature (`locked_since: 2026-05-21`, predating the doc's own later `created:` date — the same "impossible
  claim" tell): `plans/active/issues/quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md` and
  `plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md` (both `status: open`, not
  independently re-checked for done-ness since the lock is the blocking question either way). Left that corpus-wide doc
  itself untouched — it's <12h old (created today by the ui-tranche run), inside this run's own grace window, and not
  mine to edit; the corroboration lives here with a cross-reference instead, for a future `all` pass (or the operator
  ruling once it lands) to consolidate. **Parked, not archived** — per HARD LIMITS, `locked_by:` is never auto-unlocked
  regardless of how confident the evidence.

## Refuted (dropped by verify)

- **`plan_reconciler_ci_late_findings_2026_08_06.md`'s 2 remaining open todos** (batch1 D1 "todo 2"→"todo 1" typo on an
  archived doc; the mtds monkeypatch-leak title/summary editorial rewrite) — re-read in full this run (not delegated to
  a hunter, already fully read directly): both were re-confirmed as recently as the 2026-08-09 round-9 sweep as
  correctly-left-open (cosmetic-on-an-archived-doc not worth a dedicated pass; genuine editorial-characterization
  judgment call, not a deterministic grep-and-fix). No new evidence this run changes either determination — not
  re-extracted, not re-litigated, candidate dropped.
- **`plan_reconciler_findings_ci_2026_08_09.md`** — 0 open / 0 done checkboxes (pure narrative run-journal, not a
  todo-tracked doc) — not a done-but-unchecked candidate by construction. Its `locked_by:` staleness is tracked
  separately (see Filed).

## Coverage (hunters / batches / docs)

Writable set (32 docs, outside 12h grace):

- plans/active/ci_pipeline_speed_and_cost_redesign_2026_08_05.md
- plans/active/ci_vm_exposure_remediation_2026_08_06.md
- plans/active/fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md
- plans/active/github_actions_operator_gated_followups_2026_07_17.md
- plans/active/issues/archive_candidates_hook_vs_no_combine_flip_archival_rule_conflict_2026_08_09.md
- plans/active/issues/aws_codebuild_terraform_import_pending_2026_07_22.md
- plans/active/issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md
- plans/active/issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md
- plans/active/issues/credential_ask_orphan_checker_ping_format_stale_2026_07_27.md
- plans/active/issues/deployment_api_mtds_meta_missing_blocks_workspace_qg_step_5_83_2026_08_03.md
- plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md
- plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md
- plans/active/issues/mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md
- plans/active/issues/mtds_deployment_env_race_survives_single_worker_2026_07_23.md
- plans/active/issues/operator_ruling_record_gcloud_wif_poisoning_2026_08_08.md
- plans/active/issues/plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md
- plans/active/issues/plan_reconciler_ci_late_findings_2026_08_06.md
- plans/active/issues/plan_reconciler_findings_ci_2026_08_09.md
- plans/active/issues/pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md
- plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md
- plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md
- plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued3_2026_08_03.md
- plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md
- plans/active/issues/qg_sentinel_environment_blind_2026_07_23.md
- plans/active/issues/quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md
- plans/active/issues/quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21.md
- plans/active/issues/workflow_template_drift_repeated_during_phase7_rollout_2026_07_27.md
- plans/active/monitoring_control_plane_master_2026_06_10.md
- plans/active/qg_host_adaptive_resource_governor_2026_07_14.md
- plans/active/self_hosted_runner_public_repo_revert_2026_08_05.md
- plans/active/shared_ci_workflow_repo_extraction_2026_08_06.md
- plans/active/ui_build_warm_cache_2026_06_17.md

(hunters/batches to be filled in as STEP 3 runs)

## Plans not reached

(pending)

## Progress Log

- **2026-08-10 05:19 UTC** — Run started. FF'd PM + all 25 sibling repo clones (all clean, no reconciliation needed —
  earlier slot-boot heartbeat nudges about dirty repos were stale/already-resolved by the time of first check).
  `run_hygiene_sweep.sh --ci` completed (exit 1: 3 corpus-wide hard failures, none yet confirmed in-tranche).
  `build_health_digest.sh`/`extract_plan_skeleton.sh` kicked off in background — host is heavily contended (multiple
  sibling slots running concurrent hygiene sweeps at the same time, matching yesterday's run's observation). Computed
  ci-tranche population via YAML-safe frontmatter parse: 57 docs, 25 grace / 32 writable.
