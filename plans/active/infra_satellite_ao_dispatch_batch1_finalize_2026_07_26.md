---
doc_type: plan
title:
  Infra satellite AO batch 1 — finalize (reconcile all 17 source docs + re-check the 10 conflict-gated deferrals +
  archive)
summary: >-
  Gated closeout for `infra_satellite_ao_dispatch_batch1_2026_07_26.md` — machine-held via `depends_on` +
  `gate_on_depends: true` until all 25 of that plan's todos are done, so this can never dispatch early. Batch 1 was
  extracted from 17 DIFFERENT infra satellite plans/issues (not from one parent), so this finalize reconciles each of
  those 17 docs' corresponding checkboxes independently, then re-checks batch 1's own `## Deferred` section — 10 of its
  14 held-back items are CONFLICT-GATED, which is the only category that clears without a human ruling, so each one's
  named competing claim is re-examined to see whether it has since shipped or been superseded and the item can move into
  a batch 2. Only then does the standard archival ritual run on batch 1. The goal is that after this plan, every infra
  satellite doc's real remaining work is either shipped, re-tracked as an explicit new todo, or confirmed still
  correctly gated on a human decision — with the count of genuinely-orphaned infra docs re-measured rather than assumed.
status: draft
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ao-dispatch, close-out, batch-1, satellite-docs, archival, plan-hygiene]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/infra_plan_reconcile_parked_decisions_2026_07_26.md,
    /plans/active/ag_closeout_audit_rollout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [infra_satellite_ao_dispatch_batch1_2026_07_26]
gate_on_depends: true
sequential: true
source: >-
  `/ag-closeout-audit infra` run 2026-07-26 — mirrors the `sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md`
  gated-reconcile-then-archive pattern, per `plans/active/task_template.md` §4's finalize-plan-coverage rule (every AO
  batch plan needs a paired gated finalize).
---

# Infra satellite AO batch 1 — finalize

> **`status: draft` — NOT ingested, NOT dispatched.** Flips to `active` only together with its parent batch, on explicit
> operator approval.

> **Machine-gated on `infra_satellite_ao_dispatch_batch1_2026_07_26.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until all 25 tasks in that plan are `done`. `sequential: true` because todo 2
> needs todo 1's reconciliation finished (to know which source docs still have real open work vs are now fully closed),
> and todo 4 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile all 17 source docs' checkboxes.** For each of batch 1's 25 now-done todos: find the
      corresponding checkbox in the source doc its text names (every todo ends with `Source: `<doc>.md``) and flip it
      `[x]`, citing the batch-1 commit(s) that shipped it. **Verify each cited sha actually exists and is an ancestor of
      `origin/live-defi-rollout` (`git merge-base --is-ancestor <sha> origin/live-defi-rollout`) before citing it — do
      not copy batch 1's own evidence line blind.** Several batch-1 todos COMBINED multiple source-doc checkboxes into
      one (the setuptools 3-step chain, the uv `setup.sh` fix + rollout pair, the e2e-login 3-step chain, the
      PROGRESS.json rollout folding three families, the fleet-monitor pair, the launcher-write pair) — flip ALL the
      constituent boxes, not just one per todo, and say in each flip which combined todo covered it. The 17 source docs
      are: `issues/setuptools_fleet_pysec_2026_3447_bump_2026_07_14.md`, `issues/uv_pin_fleet_drift_2026_06_22.md`,
      `issues/e2e_login_persona_handoff_helper_stale_2026_07_22.md`,
      `issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md`,
      `issues/vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md`,
      `issues/session_bound_vm_monitoring_reliability_gap_2026_07_26.md`,
      `utl_uac_reuse_consolidation_remediation_2026_06_10.md`, `issues/issue_docs_remediation_sweep_2026_06_02.md`,
      `codex_violations_ratchet_to_five_2026_06_10.md`, `repo_scripts_governance_audit_2026_06_18.md`,
      `issues/service_dockerfile_pattern_normalization_2026_06_17.md`, `codex_vs_repo_docs_ssot_audit_2026_06_01.md`,
      `issues/prod_terraform_drift_backlog_reconcile_2026_07_24.md`,
      `issues/plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md`, `l0_doc_index_generator_2026_06_24.md`,
      `issues/cve_affected_pinned_deps_remediation_2026_06_18.md`, `stash_pile_workspace_cleanup_2026_06_03.md`,
      `issues/reference_path_convention_2026_07_23.md`. (That list is 18 entries because
      `session_bound_vm_monitoring_reliability_gap` co-sourced one combined todo with the billing-waste doc — reconcile
      both.) **Several of these carry `locked_by: live-defi-rollout`** — flipping a checkbox is fine on a locked doc;
      ARCHIVING one is not (that needs `[unlock-plan]`). **Done when**: every source-doc box corresponding to a done
      batch-1 todo is flipped with a verified sha, and any box that could NOT be flipped is listed with the reason.
      Repo: unified-trading-pm.

- [ ] [REVIEW] P1. **Re-check batch 1's 10 CONFLICT-GATED deferrals — the only category that clears without a ruling.**
      For each, go read the specific competing claim named in batch 1's `## Deferred` and determine whether it has since
      shipped, been superseded, or otherwise resolved; if it has, the conflict is CLEAR and the item becomes a batch-2
      candidate with zero new investigation (this is the cheap path the `/ag-closeout-audit` methodology depends on).
      The 10 and their named competing claims: (1) `PYTEST_UNIT_DIR` vs
      `issues/mtds_ungated_test_families_2026_07_17.md`'s two `[BACKEND] P1` test-fix gates — check whether those 22
      failures are fixed and which approach won; (2)+(3) the 4 `base-service.sh`/`base-library.sh` items vs
      `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` item (3) and
      `tradfi_satellite_ao_dispatch_batch4_2026_07_26.md` — check whether both have landed; (4) `DATA_PIPELINE_SERVICES`
      vs `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` item (B)'s `DataStatusTab` change; (5) `managed-by`
      label vs the wave-launcher terraform item in cross-cutting batch1b; (6) repo_scripts DEPRECATE remediation vs
      cross-cutting batch1 item (k)'s ~60-script cloud-agnostic sweep; (7) the fastapi/starlette + pyarrow/twisted/mako/
      ujson dep work vs whoever last touched `workspace-constraints.toml` / `canonical-dependency-manifest.json`; (8)
      MTDS >900 tail vs cefi batch1 + defi batches 2/3/4's `market_interface/` edits; (9) the corpus-wide sweeps vs the
      concurrent per-tranche reconcile/audit runs; (10) the two sports-doc line-cap splits vs sports batches 3 and 5.
      For each cleared conflict write an explicit batch-2 candidate line (source doc + the specific todo + the evidence
      the conflict cleared); for each still-conflicting one, restate the live competing claim so batch 2 does not have
      to re-derive it. **Done when**: all 10 carry a dated CLEARED-or-STILL-CONFLICTING verdict with evidence, and the
      cleared set is written up as the batch-2 candidate list. Repo: unified-trading-pm.

- [ ] [REVIEW] P1. **Re-measure the infra tranche's orphan count and close the coverage-gap that made batch 1
      necessary.** Two parts. (a) Re-run the `/ag-closeout-audit infra` classification over the tranche's now-updated
      docs and report the new orphan count against the 2026-07-26 baseline of **29 orphaned of 34 tranche-primary docs**
      — the number should have dropped by roughly the number of source docs batch 1 fully closed, and any doc that did
      NOT move should be named with why (operator-gated / human-only / too-large is a legitimate answer; "still orphaned
      for no stated reason" is not). (b) Fix the structural cause: `infra_consolidated_closeout_2026_07_25.md` carries
      ZERO `- [ ]` todos and has no aggregated-sources sibling, so nothing in the infra covering set dispatches anything
      and every satellite doc is orphaned by construction. Either give the hub real todos for the work only it can own
      (its 4 Track close-out criteria), or add the `<ag>_consolidated_closeout_aggregated_sources_*` sibling the 5 AGs
      have so the digest role is explicit and separate — and state which model was chosen and why. Also register the two
      tranche members that were NOT in the hub's Sources list when this audit ran
      (`issues/session_bound_vm_monitoring_reliability_gap_2026_07_26.md` and
      `issues/infra_plan_reconcile_parked_decisions_2026_07_26.md`) using proper `[text](path)` markdown links, not bare
      backticked filenames — prettier can wrap a long bare filename across a line break and silently break the substring
      match `scripts/plan-hygiene/check_ag_closeout_linkage.py` relies on. Then run that linkage check. **Done when**:
      the new orphan count is reported with per-doc reasons for anything that did not move,
      `check_ag_closeout_linkage.py` reports 0 orphans, and the hub's dispatch-vs-digest model is explicitly stated in
      the hub itself. Repo: unified-trading-pm.

- [ ] [DOCS] P2. **Archive batch 1 per the 6-step ritual, and only then.** In order: (1) migrate every still-open
      Deferred item out of batch 1 into a real home — a batch-2 plan for the cleared conflicts, the reconcile register
      `issues/infra_plan_reconcile_parked_decisions_2026_07_26.md` for the operator-gated ones (append them in the same
      structured question+options+recommendation format the existing 6 use), and a named standalone-plan todo for the
      too-large ones (`artifact_pipeline_observability`, the 20-repo codex-vs-repo-docs sweep, the schema-provenance
      migration) — **nothing may be lost to archival**; (2) add the archival banner + set `status: superseded` with
      `superseded_by:` pointing at the batch-2 plan if one was created; (3) run the codex-alignment check against the
      SSOTs batch 1 cites; (4) update CLAUDE.md / codex if any batch-1 todo established a NEW durable contract (the
      PROGRESS.json launcher-conformance list and the plan-hygiene runtime retirement both plausibly do); (5) **update
      every referrer's path corpus-wide** — grep for `infra_satellite_ao_dispatch_batch1_2026_07_26` and repoint each
      hit to the archived path, using leading-slash repo-root-relative form (this is the step the pre-2026-07-23 5-step
      ritual never named, and the exact gap that produced three separate dangling-reference regressions on 2026-07-25);
      (6) clear the lock (batch 1 has none, so this is a no-op — confirm rather than assume). Then physically move it
      under `plans/archive/2026_07/`. **Done when**: `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci --no-regen` is
      0 hard, `python3 scripts/plan-hygiene/check_reference_paths.py` shows no NEW dangling reference above its
      baseline, and `.venv/bin/python scripts/plans/regenerate_active_plan_inventory.py` reports 0 orphans. Repo:
      unified-trading-pm.

## Why this finalize plan looks different from the AG ones

The 5 asset groups' finalize plans reconcile satellite docs against a closeout hub that itself carries real dispatchable
todos. Infra's hub carries none, which is why todo 3(b) above exists at all: without fixing the hub's dispatch-vs-digest
ambiguity, the next `/ag-closeout-audit infra` run would re-derive the same "everything is orphaned by construction"
verdict no matter how much batch 1 shipped. Reconciling the checkboxes without closing that structural gap would make
the orphan count look better while leaving the mechanism that produced it untouched.

## Codex SSOTs

`/codex/11-project-management/` (findings triage, archival ritual, issue-doc lifecycle) ·
`/codex/11-project-management/cross-reference-path-convention.md` · `plans/PLAN_FORMAT.md` (`status: draft` semantics) ·
`plans/active/task_template.md` §4 (finalize-plan-coverage rule)

## Progress Log

- **2026-07-26** — Drafted alongside `infra_satellite_ao_dispatch_batch1_2026_07_26.md` by `/ag-closeout-audit infra`
  (Autonomous mode). Left `status: draft` — flips to `active` only with its parent, on explicit operator approval.
