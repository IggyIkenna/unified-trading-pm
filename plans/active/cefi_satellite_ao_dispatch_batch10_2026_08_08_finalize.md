---
doc_type: plan
title: CeFi satellite AO batch 10 — finalize (reconcile source docs + re-check deferrals + archive)
summary: >-
  Finalize twin for `cefi_satellite_ao_dispatch_batch10_2026_08_08.md` (drafted 2026-08-08 by the /ag-closeout-audit
  skill, slot 8, dispatch agt-6bc9c4). Reconciling 6 source docs' checkboxes once batch10's 6 todos land, asking the
  operator to unlock the 2 fully-done-but-locked docs found this run, and archiving batch10 via the 6-step ritual.
  `status: active` from the start per the 2026-07-30 no-double-gate ruling; `gate_on_depends: true` machine-holds every
  todo until batch10's own tasks are done.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-10, finalize, iterative-drain]
related:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch10_2026_08_08.md,
    /plans/active/cefi_satellite_ao_dispatch_batch9_2026_08_07_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
effort: high
sequential: true
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cefi_satellite_ao_dispatch_batch10_2026_08_08]
gate_on_depends: true
source: >-
  /ag-closeout-audit skill run 2026-08-08 (scheduled autonomous dispatch, agent-orchestrator slot 8, dispatch
  agt-6bc9c4, tranche=cefi), paired with `cefi_satellite_ao_dispatch_batch10_2026_08_08.md` per task_template.md §4's
  finalize-plan-coverage rule.
context_scope:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch10_2026_08_08.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# CeFi satellite AO batch 10 — finalize

> **Status: active from the start (2026-07-30 ruling — no double gate).** `gate_on_depends: true` already machine-holds
> every todo below until batch10's own 6 tasks are `done`, regardless of batch10's own `status` (draft or active). Only
> the batch itself needs `status: draft` + explicit operator approval; this finalize plan carries no independent
> judgment call. **Machine-gated on `cefi_satellite_ao_dispatch_batch10_2026_08_08.md`** (`depends_on` +
> `gate_on_depends: true`) — the dispatcher will not queue any todo below until all 6 tasks in that plan are `done`.
> `sequential: true` because todo 2 depends on todo 1's reconciliation, and todo 3 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile all 6 source docs' checkboxes.** Batch 10's 6 todos draw from 6 distinct source docs —
      for each landed todo, flip/append the corresponding checkbox/status text in its named source doc citing the
      shipping commit: (1) `issues/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` (Phase C); (2)
      `issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` (Finding 8/10, append investigation result
      to Findings — do not flip a checkbox that doesn't exist for an audit-only item); (3)
      `issues/cefi_track7_candle_bundle_regeneration_vm_2026_08_04.md` (Relaunch todo); (4)
      `issues/coverage_floor_new_backfill_gaps_found_2026_07_27.md` AND its duplicate in
      `issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md` (keep both in sync); (5)
      `issues/tarball_stale_window_cefi_live_capture_correctness_risk_2026_08_01.md` (both Open Questions items); (6)
      `issues/cefi_residual_followups_after_honest_done_2026_07_17.md` (line 718 P3 checkbox). **Verify each cited
      commit is reachable on `origin/live-defi-rollout` before citing it.** **Done when**: every landed todo's source
      checkbox/section is flipped or appended with a verified commit, and each source doc's remaining-open count is
      explicitly re-stated.
- [ ] [OPERATOR] P1. **Ask the operator to unlock the 2 fully-done-but-locked docs for archival**:
      `issues/cefi_coinbase_cde_urdi_zero_records_2026_07_28.md` and `issues/cefi_universe_capture_rule_2026_06_23.md`
      (both all-`[x]`, both carry `locked_by: live-defi-rollout`). If the operator approves, unlock and run the standard
      6-step archival ritual on each (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`). If the
      operator declines or is unreachable, leave both as-is and note the decision here. **Done when**: the operator has
      been asked and their answer (approve/decline/deferred) is recorded, with archival executed only on approval.
- [ ] [REVIEW] P1. **Re-check the 32 non-batchable Deferred items from batch10 for cleared gates before batch11's
      Phase-1 re-triage** (per the skill's iterative-drain methodology — check the prior batch's Deferred section first,
      before spinning fresh Phase-1 agents). In particular: (a) has the operator ruled on
      `issues/deribit_combo_perpetual_partition_move_2026_07_21.md`'s separate future review (the one item flagged for
      an operator decision)? (b) has `issues/cefi_content_migration_fleet_half_incomplete_2026_07_26.md`'s conflicting
      active claim shipped or gone stale? (c) has `issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md`'s
      ON_DEMAND VM reached a terminal state? For each item where the gate has cleared, record it explicitly as a
      "batch11 candidate," do NOT draft a todo here. **Done when**: all 32 Deferred items have a dated re-check note
      (cleared → batch11 candidate, or still-blocked → unchanged) in this finalize doc's Progress Log.
- [ ] [DOC] P1. **Archive `cefi_satellite_ao_dispatch_batch10_2026_08_08.md`** via the standard 6-step ritual: confirm
      the Deferred/Archivable/Cross-tranche/Orthogonality-fixes sections (informational, never batch todos) need no
      separate migration → add the archive banner → run the codex-alignment check (batch10 creates no new durable
      contract beyond the 2 orthogonality retags already landed directly on their source docs; confirm still true) →
      grep the corpus for every referrer of `cefi_satellite_ao_dispatch_batch10_2026_08_08` and repoint each to the
      archived path → clear `locked_by` (already empty, confirm). **Done when**: the plan is moved to
      `plans/archive/2026_08/`, every corpus referrer resolves to the new path, `run_hygiene_sweep.sh` stays green, and
      this finalize doc is archived alongside it in the same commit.

## Codex SSOTs

- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual (todo 4) and the
  locked-plan-needs-human-unlock rule (todo 2).
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — the shared conflict-check protocol
  that shaped batch10's extraction.

## Progress Log

- **2026-08-08** — drafted by the `/ag-closeout-audit` cefi run (slot 8, dispatch agt-6bc9c4) alongside batch10;
  authored `status: active` per the 2026-07-30 no-double-gate ruling, machine-held by `gate_on_depends: true` until
  batch10's todos are done.
