---
doc_type: issue
title:
  "2026-08-10 /ag-closeout-audit infra + ci run — 0 real orphans; 8 corpus-wide linkage-only gaps mechanically fixed
  across both tranches"
summary: >-
  infra's 2026-08-10 pass found 9 `check_ag_closeout_linkage.py`-confirmed orphans at run start; all 9 turned out to be
  linkage-only gaps (5 batch/finalize plans + `codex_vs_repo_docs_ssot_audit` finalize + `reference_path_convention`
  finalize missing a `related:` link to `infra_consolidated_closeout_2026_07_25.md`, plus 1 self-dispatched issue doc
  `broad_except_as_binding_form_blind_spot_2026_08_09.md` with real open AO-dispatched work just missing the same link)
  — 0 genuine orphans remain for infra after the mechanical fix. ci's pass found 3 orphans at run start (its
  consolidated-closeout doc is archived, `plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md` — a known
  pre-existing condition, not a new gap); all 3 were the same linkage-only shape (a finalize plan + its paired issue doc
  + a self-dispatched openapi-regen findings doc) — 0 genuine orphans remain for ci either.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ci, ag-closeout-audit, parked-findings, linkage-fix, clean-run]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch12_2026_08_09.md,
    /plans/active/infra_satellite_ao_dispatch_batch13_2026_08_09.md,
    /plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01_finalize_2026_07_27.md,
    /plans/active/reference_path_convention_2026_07_23_finalize_2026_08_08.md,
    /plans/active/issues/broad_except_as_binding_form_blind_spot_2026_08_09.md,
    /plans/active/pm_bats_tests_never_invoked_by_quality_gates_2026_07_26_finalize_2026_08_08.md,
    /plans/active/issues/pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md,
    /plans/active/issues/venv_workspace_openapi_regen_batch11_findings_2026_08_09.md,
    /scripts/plan-hygiene/check_ag_closeout_linkage.py,
  ]
created: "2026-08-10"
author: "slot-26 (ag_closeout_auditor, all-tranche mode)"
last_updated: "2026-08-10"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.05
estimate_calibrated_ai_days: 0.04
assigned_role: infra
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope: [/scripts/plan-hygiene/check_ag_closeout_linkage.py]
source: >-
  `/ag-closeout-audit all` run 2026-08-10 (ag_closeout_auditor scheduled worker, slot 26, one-shot, no $TRANCHE set).
---

# Parked findings — 2026-08-10 `/ag-closeout-audit infra` + `ci` (part of the `all`-mode run)

## Resolved this run (not parked findings — mechanical linkage fixes, 0 real orphans remain)

**infra (9 fixed)**: `infra_satellite_ao_dispatch_batch12_2026_08_09.md`, `…batch12_finalize`, `…batch13_2026_08_09.md`,
`…batch13_finalize`, `codex_vs_repo_docs_ssot_audit_2026_06_01_finalize_2026_07_27.md`,
`reference_path_convention_2026_07_23_finalize_2026_08_08.md` (all missing a `related:` link to
`infra_consolidated_closeout_2026_07_25.md`, added) + `issues/broad_except_as_binding_form_blind_spot_2026_08_09.md`
(self-dispatched, `assigned_vm: planning`, 2 real open todos — same missing-link gap, fixed).

**ci (3 fixed)**: `pm_bats_tests_never_invoked_by_quality_gates_2026_07_26_finalize_2026_08_08.md` +
`issues/pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md` (missing a `related:` link to the ARCHIVED
`ci_consolidated_closeout_2026_07_25.md` — still a valid link target per `check_ag_closeout_linkage.py`'s own design)

- `issues/venv_workspace_openapi_regen_batch11_findings_2026_08_09.md` (self-dispatched, `assigned_vm: planning`, 2 real
  open P3 todos — same gap).

All fixes verified via re-run of `check_ag_closeout_linkage.py`: infra and ci both show 0 orphans in the post-fix
corpus-wide sweep (14 total remaining, all in other tranches — see `ag_closeout_audit_ao_parked_2026_08_10.md`,
`…cross_cutting_parked_2026_08_10.md`, `…defi_parked_2026_08_10.md`, `…tradfi_parked_2026_08_10.md`).

## Todos

None — 0 real orphans, 0 operator-decision-requiring findings for either tranche this run.

## Progress Log

- **2026-08-10** — `/ag-closeout-audit all` run (autonomous mode, task-less one-off, slot 26). Phase 0: corpus-wide
  `check_ag_closeout_linkage.py` sweep found 9 infra + 3 ci orphans, all linkage-only (verified via direct read: every
  flagged doc either already had real coverage as a self-dispatched `assigned_vm: planning` plan, or was gating
  scaffolding for one). Fixed all 12 by appending the tranche's closeout-family path to each doc's `related:` list.
  Re-ran the check: infra and ci both 0. No Phase-1 Workflow dispatch needed for either tranche (nothing survived the
  linkage-only pre-filter). Ledger: 0 operator-decision-requiring findings + 12 mechanical fixes (not counted as parked
  findings) — **balanced**.
