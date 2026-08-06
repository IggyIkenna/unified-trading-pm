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
    /plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /plans/active/issues/mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md,
    /plans/active/issues/ag_closeout_audit_ci_parked_2026_08_06.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_08/mtds_retry_safe_default_audit_2026_07_14.md,
  ]
created: 2026-08-06
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
source: agt-a304c9
locked_by:
---

# Late-arriving hunter findings — CI tranche reconciliation 2026-08-06

The contradiction/epic-cluster hunter and mechanical/zero-checkbox hunter returned findings after the run had already
signaled `/done`. All verified and filed here. **9 findings across 4 priority levels.**

---

## P0 — Closeout orphans (6 CI docs + 1 ao-retagged)

The `ci_consolidated_closeout_2026_07_25.md` is ARCHIVED. These 6 ci-tagged docs have no path (related graph ≤3 hops OR
closeout-family textual mention) to their closeout family. Contribute to the corpus-wide "AG-closeout linkage" hard gate
failure (75 orphans vs 69 baseline).

- [ ] [DOC] P0. **Link `monitoring_control_plane_master_2026_06_10.md` to its closeout family.** Also has 6 dangling
      `plans/active/` refs to archived targets (P1 finding below).
- [ ] [DOC] P0. **Link `test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md` to its closeout family.**
- [ ] [DOC] P0. **Link `quality_gates_v2_concurrency_and_bookkeeping_job_cost_2026_08_02.md` to its closeout family.**
- [ ] [DOC] P0. **Link `breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md` to its closeout family.**
- [ ] [DOC] P0. **Link `deployment_api_mtds_meta_missing_blocks_workspace_qg_step_5_83_2026_08_03.md` to its closeout
      family.**
- [ ] [DOC] P0. **Link `pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md` to its closeout family.**
- [ ] [DOC] P1. **`review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md`** — retagged `[ao]` 2026-08-02; orphan
      against the ao closeout family. Route there.

---

## P1 — Dangling `/plans/active/` refs (targets archived)

- [ ] [DOC] P1. **`monitoring_control_plane_master_2026_06_10.md`** — 6 `plans/active/` refs whose targets are archived:
      `ci_dashboard_deployment_ui_2026_06_10.md`, `fleet_git_health_orchestrator_2026_06_10.md`,
      `ci_status_firestore_side_store_2026_06_10.md`, `cicd_contract_hardening_2026_06_01.md`,
      `plan_line_cap_remediation_2026_07_23.md`, `dashboard_promotion_drain_visibility_2026_06_11.md`. Repoint to
      `plans/archive/` paths.
- [ ] [DOC] P1. **`qg_host_adaptive_resource_governor_2026_07_14.md`** — 4 refs to
      `plans/active/issues/qg_host_governor_severe_contention_2026_07_13.md` (archived; only at
      `plans/archive/issues/`). Repoint.

---

## P2 — Stale index + zero-checkbox docs

- [ ] [DOC] P2. **`plans/epics/infrastructure_master.md:595-597`** — lists `mtds_retry_safe_default_audit_2026_07_14`
      with `status: active`. The plan is archived at `plans/archive/2026_08/` and `status: complete` (L14). Same class
      the epic previously fixed via finding 85 (L748-756). Fix: update to `status: complete`.
- [ ] [DOC] P2. **`ag_closeout_audit_ci_parked_2026_08_06.md`** — zero checkboxes. Contains 18 parked findings with
      actionable recommendations + 6 potential batch6 candidates. All written as prose — convert to tracked `- [ ]`
      [TAG] P<n>. todos.
- [ ] [DOC] P2. **`client_reporting_api_promote_wedge_backmerge_dead_2026_08_06.md`** (GRACE) — zero checkboxes. PR #646
      CONFLICTING, main/LDR diverged. 4 concrete untracked resolution steps. Convert to tracked todos after grace
      expires.

---

## P3 — Cosmetic / cross-reference fixes

- [ ] [DOC] P3. **`ci_satellite_ao_dispatch_batch1_2026_07_26.md:859`** — D1 row hands checker-registration to "the
      finalize plan's todo 2", but the finalize plan carries it as todo 1 (`batch1_finalize` L72, L119-120: "D1 is
      discharged by todo 1 above"). Fix: "todo 2" → "todo 1".
- [ ] [DOC] P3. **`mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md`** — title + frontmatter summary
      assert xdist-worker-leak mechanism; body (L239-241, L121-126) records mechanism was never confirmed and reproduces
      under serial execution. Fix: update title/summary to reflect actual known state.
- [ ] [DOC] P3. **`cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md`** (GRACE) — archive
      candidate: all 5 todos `- [x]`, unlocked. Archive after grace expires.
