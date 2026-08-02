---
doc_type: plan
title: Cross-cutting satellite AO batch 4 — finalize (reconcile source docs + re-check deferrals + archive)
summary: >-
  Gated closeout for cross_cutting_satellite_ao_dispatch_batch4_2026_08_02.md — machine-held via depends_on +
  gate_on_depends: true until all 4 todos are done. Reconciles each named source doc's checkboxes independently, then
  re-checks batch 4's own Deferred items (1 too-large-for-a-batch-todo, 1 operator-gated) for whether the gating ground
  has cleared, and archives the batch via the standard 6-step ritual.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-4, archival]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch4_2026_08_02.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch3_2026_08_01_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-02"
last_updated: "2026-08-02"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: data_engineering
sequential: true
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cross_cutting_satellite_ao_dispatch_batch4_2026_08_02]
gate_on_depends: true
context_scope:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch4_2026_08_02.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
source: >-
  /ag-closeout-audit cross-cutting re-invocation 2026-08-02, per task_template.md § 4's finalize-plan-coverage rule —
  every AO-dispatched plan needs a companion gated finalize plan.
---

# Cross-cutting satellite AO batch 4 — finalize

> **Machine-gated on
> [`cross_cutting_satellite_ao_dispatch_batch4_2026_08_02.md`](/plans/active/cross_cutting_satellite_ao_dispatch_batch4_2026_08_02.md)**
> (`depends_on` + `gate_on_depends: true`) — the dispatcher will not queue any todo below until all 4 of that plan's
> todos are `done`. This plan itself ships `status: active` (not `draft`) per the 2026-07-30 no-double-gate finding —
> `gate_on_depends` alone already covers both an active AND a still-draft upstream batch, so a second `status: draft`
> rail here would just be a redundant manual flip nobody reliably remembers. `sequential: true` because todo 2 needs
> todo 1's reconciliation finished, and todo 3 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile every named source doc's checkboxes.** Batch 4's 4 todos cite 3 distinct source docs
      (each todo's text ends with `Source:`). For each: flip the corresponding checkbox, citing the batch commit that
      shipped it — verify the commit actually exists before citing it. After flipping, re-check each source doc for 0
      remaining open items (checkbox AND prose-form) and only then consider flipping its `status` to `resolved`.
      Specifically: `issues/batch_live_recon_cloud_run_job_stage0_never_succeeded_2026_07_30.md` (todo 3 was its last
      open item — flip and check for 0 remaining), `issues/pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md`
      (this was its last open item — flip and check for 0 remaining), `daily_trading_analyst_llm_job_design_2026_07_29.md`
      (2 of this batch's todos cite its §5 — flip both corresponding checkboxes; this doc's `status` stays `active`
      regardless, since its 3 too-large-deferred items + 1 operator-gated item remain genuinely open — do NOT flip its
      status to resolved). **Done when**: every cited source checkbox is flipped with verified evidence and no doc's
      `status` was advanced past what its remaining items actually support.
- [ ] [REVIEW] P2. **Re-check batch 4's own Deferred items now that time has passed.** For the "too-large-for-a-batch-
      todo" entry (`daily_trading_analyst_llm_job_design_2026_07_29.md`'s 3-item build chain) and the 1 operator-gated
      entry (its `[OPERATOR] P2` escalation-N/assigned_vm-default decision): re-read the specific gating ground and
      decide whether it has cleared. Route the too-large entry to exactly one of — promoted to its own standalone plan
      already (note the plan's name/path), still not picked up (re-confirm it's still accurately described as
      too-large, don't just re-park it reflexively), or resolved independently. For the operator-gated entry: **do NOT
      re-surface an operator question already asked** — if still unruled, leave it be rather than re-asking. Also
      verify the 2 `[ao, cross-cutting]` dual-tag mistags this run found
      (`context_scout_completion_and_plan_brainstorm_skill_2026_07_30.md`,
      `omniroute_llm_gateway_pilot_design_2026_07_30.md`) plus the broader `ao`/`ci`/`sports`-owned mistag population
      recorded in `issues/ag_closeout_audit_cross_cutting_parked_2026_08_02.md` were actually picked up/retagged by
      their owning tranches' next audit passes — if any is still un-retagged after a reasonable interval, note that
      plainly rather than assuming it was handled. **Done when**: every Deferred entry and every parked mistag carries a
      dated re-verification verdict with its routing named.
- [ ] [DOC] P1. **Archive `cross_cutting_satellite_ao_dispatch_batch4_2026_08_02.md`** via the standard 6-step ritual:
      migrate any still-Deferred item to a tracked todo elsewhere (todo 2 above should have routed both) → add the
      archive banner → run the codex-alignment check (this batch introduces no new durable contract beyond the
      `DATA_EPICS` script fix, which already shipped independently — confirm that is still true before archiving) →
      grep the corpus for every referrer of this batch or this finalize and fix each path → confirm `locked_by` is
      empty on both. **Done when**: both docs are in `plans/archive/2026_08/`, every corpus referrer resolves to the
      new path, and `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports 0 hard failures and 0 orphans.

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`,
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`.

## Progress Log

- **2026-08-02** — Drafted alongside batch4 (`/ag-closeout-audit cross-cutting`, autonomous, dispatch `agt-b09d86`, slot
  10). `status: active` from creation (no-double-gate finding); `gate_on_depends: true` holds every todo until batch4's
  4 todos are done.
