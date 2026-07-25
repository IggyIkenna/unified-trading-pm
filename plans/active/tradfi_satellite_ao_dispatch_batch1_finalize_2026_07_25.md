---
doc_type: plan
title: TradFi satellite AO batch 1 — finalize (reconcile source docs + resolve conflict-gated deferrals + archive)
summary: >-
  Gated closeout for tradfi_satellite_ao_dispatch_batch1_2026_07_25.md — machine-held via depends_on + gate_on_depends:
  true until all 5 of that plan's todos are done. Mirrors the sports batch2_finalize/ batch3_finalize pattern (reconcile
  each of the 4 distinct source docs' checkboxes independently), plus one batch1-specific addition: re-check the 38
  conflict-gated Deferred items once the operator has ruled on the queued decision in
  autonomous_session_operator_decisions_2026_07_25.md.
status: draft
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-1, satellite-docs, archival]
related:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.3
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [tradfi_satellite_ao_dispatch_batch1_2026_07_25]
gate_on_depends: true
source: >-
  /autonomous session 2026-07-25, per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs
  a companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# TradFi satellite AO batch 1 — finalize

> **Machine-gated on `tradfi_satellite_ao_dispatch_batch1_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 5 tasks in that plan are `done`. `sequential: true` because
> todo 2 needs todo 1's reconciliation done first, and todo 3 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile all 4 distinct source docs' checkboxes.** For each of
      `tradfi_satellite_ao_dispatch_batch1_2026_07_25.md`'s 5 now-done todos: flip the corresponding checkbox/ section
      in its named source doc (each todo's text ends with "Source: `<doc>.md`"), citing the batch-1 commit(s) that
      shipped it — verify the actual shipped commit exists before citing it. The 4 source docs:
      `issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md`,
      `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`, `tradfi_phase_d_terminal_gate_2026_07_24.md` (2 todos),
      `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`. For each: after flipping, re-check whether it
      now has 0 open todos remaining. Only flip a doc's `status` to `resolved` if it genuinely reaches 0 open todos
      (checkbox AND prose-form). **Done when**: all 4 source docs' corresponding checkboxes/sections are flipped with
      verified evidence, and any doc that genuinely reaches 0 open todos is flipped to `status: resolved`.
- [ ] [REVIEW] P1. **Resolve the 38 conflict-gated Deferred items from batch1's own Deferred section**, now that the
      operator has (presumably) ruled on the queued decision in `autonomous_session_operator_decisions_2026_07_25.md`.
      For each of the 13 docs listed there: re-read the specific conflicting todo in
      `tradfi_consolidated_closeout_2026_07_18.md` to check if it has since shipped (resolving the conflict by making
      the item redundant/already-covered) or if the operator's ruling clarified which side should execute — if either,
      extract the item as a new tracked todo in a follow-up batch2. If still genuinely unresolved, leave it explicitly
      deferred. Also separately review `tradfi_manifest_content_recovery_completion_2026_07_24.md` (flagged
      too-large/risky by the triage — 5 AO-eligible candidates found) and recommend whether it warrants its own
      dedicated batch2 triage pass. **Done when**: each of the 13 conflict-gated docs has either (a) a new tracked
      todo/plan created because a conflict cleared, or (b) an explicit re-verified confirmation the conflict is still
      open; and a recommendation is recorded for the large/risky doc.
- [ ] [DOC] P1. **Archive `tradfi_satellite_ao_dispatch_batch1_2026_07_25.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todo 2 above
      should have already resolved all of them — verify none remain) → add the archive banner → run the codex-alignment
      check → grep the corpus for every referrer of `tradfi_satellite_ao_dispatch_batch1_2026_07_25` and fix each path
      to point at the archived location → clear `locked_by` (already empty here, confirm). **Done when**: the plan is
      moved to `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this finalize doc itself
      gets archived alongside it in the same commit.
