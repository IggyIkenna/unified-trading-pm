---
doc_type: issue
title: "Plan reconciler — CI tranche late-arriving hunter findings (agt-a304c9, 2026-08-06)"
summary:
  "9 findings (2 P0, 2 P1, 3 P2, 2 P3) from contradiction + mechanical hunters that completed after /done. Verified and
  filed."
status: open
resolved_by:
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-reconciler, ci, late-findings, closeout-orphans, dangling-refs]
related:
  [
    /plans/epics/infrastructure_master.md,
    /plans/active/monitoring_control_plane_master_2026_06_10.md,
    /plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /plans/active/issues/mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md,
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_08/mtds_retry_safe_default_audit_2026_07_14.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch9_2026_08_09.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch10_2026_08_09.md,
  ]
context_scope:
  [
    /plans/epics/infrastructure_master.md,
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /plans/active/monitoring_control_plane_master_2026_06_10.md,
  ]
created: 2026-08-06
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
source: agt-a304c9
locked_by:
drift_direction: advance-code
depends_on: []
---

# Late-arriving hunter findings — CI tranche reconciliation 2026-08-06

The contradiction/epic-cluster hunter and mechanical/zero-checkbox hunter returned findings after the run had already
signaled `/done`. All verified and filed here. **9 findings across 4 priority levels.**

---

## P0 — Closeout orphans (6 CI docs + 1 ao-retagged)

The `ci_consolidated_closeout_2026_07_25.md` is ARCHIVED. These 6 ci-tagged docs have no path (related graph ≤3 hops OR
closeout-family textual mention) to their closeout family. Contribute to the corpus-wide "AG-closeout linkage" hard gate
failure (75 orphans vs 69 baseline).

- [x] [DOC] P0. ✅ **Already resolved by 2026-08-09 (round-9 sweep verification)** — Link
      `monitoring_control_plane_master_2026_06_10.md` to its closeout family. Confirmed: `related:` now cites
      `/plans/active/ci_consolidated_closeout_2026_07_25.md` (0-hop, satisfies the ≤3-hop linkage gate). Also has 6
      dangling `plans/active/` refs to archived targets (P1 finding below).
- [x] [DOC] P0. ✅ **Already resolved by 2026-08-09 (round-9 sweep verification)** — Link
      `test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md` to its closeout family. Confirmed: `related:` cites
      `/plans/active/ci_consolidated_closeout_2026_07_25.md`.
- [x] [DOC] P0. ✅ **Already resolved by 2026-08-09 (round-9 sweep verification)** — Link
      `quality_gates_v2_concurrency_and_bookkeeping_job_cost_2026_08_02.md` to its closeout family. Confirmed:
      `related:` cites `/plans/active/ci_consolidated_closeout_2026_07_25.md`.
- [x] [DOC] P0. ✅ **Already resolved by 2026-08-09 (round-9 sweep verification)** — Link
      `breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md` to its closeout family. Confirmed: `related:`
      cites `/plans/active/ci_consolidated_closeout_2026_07_25.md`.
- [x] [DOC] P0. ✅ **Already resolved by 2026-08-09 (round-9 sweep verification)** — Link
      `deployment_api_mtds_meta_missing_blocks_workspace_qg_step_5_83_2026_08_03.md` to its closeout family. Confirmed:
      `related:` cites `/plans/active/ci_consolidated_closeout_2026_07_25.md`.
- [x] [DOC] P0. ✅ **Already resolved (superseded)** — Link `pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md`
      to its closeout family. That doc is now `assigned_vm: planning` (self-dispatched, per
      `ag_closeout_audit_ci_parked_2026_08_09.md`'s "state change" note) and its own body already discusses the
      closeout-linkage question directly — no separate ci-tranche action needed.
- [x] [DOC] P1. ✅ **Already resolved (stale on arrival)** —
      `review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md` was retagged `[ao]` 2026-08-02, four days BEFORE this
      finding was filed (2026-08-06) — the routing note was already satisfied at filing time. Not a ci-tranche action;
      the `ao` tranche's own closeout audit owns any residual linkage there.

---

## P1 — Dangling `/plans/active/` refs (targets archived)

- [x] ✅ [DOC] P1. **`monitoring_control_plane_master_2026_06_10.md`** — 6 `plans/active/` refs whose targets are
      archived: `ci_dashboard_deployment_ui_2026_06_10.md`, `fleet_git_health_orchestrator_2026_06_10.md`,
      `ci_status_firestore_side_store_2026_06_10.md`, `cicd_contract_hardening_2026_06_01.md`,
      `plan_line_cap_remediation_2026_07_23.md`, `dashboard_promotion_drain_visibility_2026_06_11.md`. Repoint to
      `plans/archive/` paths. **Re-verified still-open 2026-08-09 (round-9 sweep)** — exact current paths confirmed:
      `plans/archive/2026_06/ci_dashboard_deployment_ui_2026_06_10.md`,
      `plans/archive/2026_06/fleet_git_health_orchestrator_2026_06_10.md`,
      `plans/archive/2026_06/ci_status_firestore_side_store_2026_06_10.md`,
      `plans/archive/2026_06/cicd_contract_hardening_2026_06_01.md`,
      `plans/archive/issues/plan_line_cap_remediation_2026_07_23.md`,
      `plans/archive/issues/dashboard_promotion_drain_visibility_2026_06_11.md`. **Extracted to
      `ci_satellite_ao_dispatch_batch10_2026_08_09.md` todo 1** — separate batch number from the other 2 extracted items
      below because this doc's own `parent_epic: observability_master` differs from theirs (`infrastructure_master`),
      per the established batch7/batch8 parent_epic-grouping precedent. **DONE 2026-08-09 (slot 31)**: all 6 refs
      repointed in `monitoring_control_plane_master_2026_06_10.md` (5 in the `related:` frontmatter list, 1 inline body
      prose at the line-cap-remediation split banner) to their leading-slash archive paths; `check_reference_paths.py`
      clean (both format + existence checks under baseline, no new violations). Evidence: unified-trading-pm (this
      commit).
- [x] [DOC] P1. ✅ — Fixed all 4 refs in `qg_host_adaptive_resource_governor_2026_07_14.md` (`related:`, `source:`,
      Codex-SSOTs inline, Phase-6 body) — repointed from the stale `plans/active/issues/...` path to
      `/plans/archive/issues/qg_host_governor_severe_contention_2026_07_13.md`, verified with
      `check_reference_paths.py --only`. Via `ci_satellite_ao_dispatch_batch9_2026_08_09.md` todo 1 —
      unified-trading-pm@a52672b6d (verified ancestor of `origin/live-defi-rollout` via
      `git merge-base     --is-ancestor`, 2026-08-09; batch9's own progress-log cited a bogus, non-resolving SHA
      `89925f0c6` for this todo — corrected there in the same pass).

---

## P2 — Stale index + zero-checkbox docs

- [x] [DOC] P2. ✅ — Updated `plans/epics/infrastructure_master.md:595-597` index entry for
      `mtds_retry_safe_default_audit_2026_07_14` from `status: active` to
      `status: complete (archived 2026-08-06 — 5/5 todos done; fleet-wide STEP 5.104 lint in base-service.sh is the     durable pin)`,
      matching the sibling `cicd_mvp_ldr_to_main_pipeline_2026_06_30` entry's established format (L536). Epic stays
      under its 2000-line hard cap. Via `ci_satellite_ao_dispatch_batch9_2026_08_09.md` todo 2 —
      unified-trading-pm@930f7393e (verified ancestor of `origin/live-defi-rollout` via
      `git merge-base     --is-ancestor`, 2026-08-09).
- [x] [DOC] P2. ✅ **Moot — target doc never existed in git history.** `ag_closeout_audit_ci_parked_2026_08_06.md` —
      confirmed via `git log --all --diff-filter=A` (this doc's own 2026-08-09 Progress Log entry, slot-22): the corpus
      only ever had `_2026_08_07`/`_08`/`_09` daily-rotating snapshots. Nothing to convert.
- [x] [DOC] P2. ✅ **Moot — superseded.** `client_reporting_api_promote_wedge_backmerge_dead_2026_08_06.md` is now
      `assigned_vm: planning` (self-dispatched, confirmed 2026-08-09) — it dispatches under its own steam; no separate
      ci-tranche conversion action needed.

---

## P3 — Cosmetic / cross-reference fixes

- [ ] [DOC] P3. DEFERRED (low-value, archived-doc cosmetic) — **`ci_satellite_ao_dispatch_batch1_2026_07_26.md:859`** —
      D1 row hands checker-registration to "the finalize plan's todo 2", but the finalize plan carries it as todo 1
      (`batch1_finalize` L72, L119-120: "D1 is discharged by todo 1 above"). Fix: "todo 2" → "todo 1". Re-verified
      2026-08-09: both `batch1` and `batch1_finalize` are now ARCHIVED (`plans/archive/2026_08/`) — editing an archived
      doc for an internal off-by-one text reference is not worth a dedicated pass; left open but not extracted this
      round.
- [ ] [DOC] P3. NOT AO-ELIGIBLE (judgment call) —
      **`mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md`** — title + frontmatter summary assert
      xdist-worker-leak mechanism; body (L239-241, L121-126) records mechanism was never confirmed and reproduces under
      serial execution. Re-read 2026-08-09: the title already hedges ("appears to leak"), and rewriting it to precisely
      reflect a still-under-investigation mechanism (xdist-ordering vs. serial- reproducing) is an editorial
      characterization call, not a deterministic grep-and-fix — left open, not extracted.
- [x] [DOC] P3. ✅ **Already resolved (archived).**
      `cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md` is now at `plans/archive/issues/` —
      grace expired and the archive already happened.

## Progress Log

- **context-scout 2026-08-14**: populated context_scope (3 entries).

- **2026-08-09, slot-22 (backend_engineer)**: found this doc's own `related:` list failing QG's `check_reference_paths`
  (3 dangling entries) while shipping an unrelated task. `ag_closeout_audit_ci_parked_2026_08_06.md` never existed in
  git history (checked `git log --all --diff-filter=A`) — the corpus only ever had `_2026_08_07`/`_08`/`_09`
  daily-rotating snapshots, so removed that entry outright. The other two
  (`ci_satellite_ao_dispatch_batch1_2026_07_26.md`
  - its `_finalize` sibling) simply moved to `plans/archive/2026_08/` since this doc was filed — repointed both to their
    archive path. All three are pure path/reference fixes, no content judgment involved — the findings/todos above are
    untouched.
- **2026-08-09, round-9 combined RECLASSIFY + satellite-extraction sweep (`ci` tranche)**: re-verified all 9 remaining
  findings against live corpus state. **8 of 14 total todos closed**: 6 P0 closeout-linkage findings confirmed already
  resolved (all 6 target docs' `related:` now cite `/plans/active/ci_consolidated_closeout_2026_07_25.md`) + 1 P1
  (review_role routing, stale-on-arrival) + 2 P2 (1 moot target-never-existed, 1 moot self-dispatched-supersede) + 1 P3
  (cloudbuild already archived). **3 genuinely-still-open, bounded items extracted across TWO batches** (split by
  `parent_epic`, per the batch7/batch8 grouping precedent): `ci_satellite_ao_dispatch_batch9_2026_08_09.md`
  (`parent_epic: infrastructure_master`, todos 1-2: repoint 4 dangling refs in
  `qg_host_adaptive_resource_governor_2026_07_14.md`, fix stale `status: active` in
  `plans/epics/infrastructure_master.md:595-597`) and `ci_satellite_ao_dispatch_batch10_2026_08_09.md`
  (`parent_epic: observability_master`, todo 1: repoint 6 dangling refs in
  `monitoring_control_plane_master_2026_06_10.md`). **2 items left open, not extracted**: batch1 D1 typo (archived-doc
  cosmetic, not worth a dedicated pass) and the mtds title/summary rewrite (editorial characterization judgment call,
  not a deterministic fix). This doc's own `assigned_vm: NA` stays correct — the doc remains a live findings-tracker
  with genuine residual (non-extracted) items, not a candidate for whole-doc RECLASSIFY.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-08-10** (ci tranche, autonomous, dispatch agt-74eff9) [body-hash:f0bf533d397b6bf2]: KEEP-NA,
valid — grep confirms exactly 2 open todos (lines 129, 135), matching the phase0 figure; 7 of the doc's 9 tracked
findings are already closed via checkmarks (mostly 'already resolved by round-9 sweep verification' or 'moot --
superseded'). The 2 remaining P3 items are each explicitly self-classified in-doc as judgment/priority calls, not
bounded fixes: (1) an archived-doc off-by-one cross-reference typo, explicitly deferred as 'low-value... not worth a
dedicated pass'; (2) a title/summary editorial rewrite of a sibling doc, explicitly self-classified 'NOT AO-ELIGIBLE
(judgment call)...
