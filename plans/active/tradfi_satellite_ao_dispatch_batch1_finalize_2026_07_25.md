---
doc_type: plan
title: TradFi satellite AO batch 1 — finalize (reconcile source docs + resolve conflict-gated deferrals + archive)
summary: >-
  Gated closeout for tradfi_satellite_ao_dispatch_batch1_2026_07_25.md — machine-held via depends_on + gate_on_depends:
  true until all 5 of that plan's todos are done. Mirrors the sports batch2_finalize/ batch3_finalize pattern (reconcile
  each of the 4 distinct source docs' checkboxes independently), plus one batch1-specific addition: re-check the 38
  conflict-gated Deferred items once the operator has ruled on the queued decision in
  autonomous_session_operator_decisions_2026_07_25.md.
status: active
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
last_updated: "2026-07-30"
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

- [x] ✅ [REVIEW] P1. **DONE 2026-07-30 — Reconciled all 4 distinct source docs' checkboxes.** Per-doc verdict (each
      commit verified reachable via `git cat-file -e` before citing): -
      `issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` (todo 1, the `EXCHANGE_CODE_TO_NAME` diff) —
      **already reconciled**, no edit needed: `unified-trading-pm@67c4cab32` ("exhaustive EXCHANGE_CODE_TO_NAME diff —
      flip tradfi_satellite_ao_dispatch_batch1-001") already appended the full diff table into this doc on 2026-07-26.
      Doc keeps `status: open` — its sole checkbox (a P1-OPERATOR-DECISION re: CBOE/VX) is a genuinely different,
      still-open item. - `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md` (todo 2, the combined
      cefi/sports-claim-verify + dry-run) — **already reconciled**, no edit needed: both applicable checkboxes already
      read `[x]` (flipped 2026-07-25 and 2026-07-30 respectively, both citing their evidence in-doc). Doc keeps
      `status: active` — its remaining DELETE checkbox is genuinely open (gated on a fresh Part-5 twin-coverage +
      retention check, which the doc's own 2026-07-30 dry-run measured at 0%, not the required 100%). -
      `tradfi_phase_d_terminal_gate_2026_07_24.md` (todos 3 + 4, the CBOE terminal-state DIAG + the VM-preemption
      launcher-naming DOC addition) — todo 3's section ("2026-07-27 — CBOE terminal-state re-check") was **already
      present verbatim**, no edit needed. Todo 4's backtick-wrapped VM-fleet-preemption note was **flipped to a real
      `[x]`** this pass, citing `unified-trading-pm@3ebdd1a4e` (doc-scoping addition) + `deployment-service@db5d3c7`
      (the launcher code fix, already cited in-doc). Doc keeps `status: active` — 2 genuinely open, operator-gated P0/P1
      checkboxes remain (MVP backfill readiness gate; post-backfill reconciliation checkpoint). -
      `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md` (todo 5, the Deribit 1-4 leg cap extension) —
      its one remaining `[ ]` checkbox was **flipped to `[x]`** this pass, citing `instruments-service@9416be7d`. Doc
      keeps `status: active` despite reaching 0 open checkboxes — genuine prose-form remaining work survives in the
      "Scope migration mechanics" item (historical catalog `--apply` rewrite deferred pending operator confirmation,
      non-durable against the self-refreshing `prod/catalog.parquet` roll-up until
      `tradfi_canonical_path_migration_design_2026_07_19.md`'s upstream migration lands). **No doc genuinely reached 0
      open todos (checkbox AND prose-form)**, so no `status: resolved` flips were made — each doc's remaining open item
      (or prose-form caveat) is real and independently verified, not an oversight.
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
