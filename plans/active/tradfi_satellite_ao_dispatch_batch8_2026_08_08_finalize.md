---
doc_type: plan
title: TradFi satellite AO batch 8 — finalize (reconcile source docs + resolve deferrals + archive)
summary: >-
  Gated closeout for tradfi_satellite_ao_dispatch_batch8_2026_08_08.md — machine-held via depends_on plus
  gate_on_depends: true until all 3 of that plan's todos are done. Mirrors the batch1-7-finalize pattern: reconcile each
  distinct source doc's checkboxes once its batch-8 todo lands, then re-check batch8's own Deferred sections
  (too-large-or-risky / operator-gated / conflict-gated / already-in-flight / already-drafted-elsewhere / time-gated /
  cross-tranche-flagged) for any that have since cleared, then archive batch8 via the standard 6-step ritual. Ships
  `status: active` from the start (not draft) — per the 2026-07-30 ruling this skill's SKILL.md documents, a finalize
  plan carries no independent judgment call and gate_on_depends already machine-holds every task until batch8 itself is
  done, so stacking batch8's own draft safety-rail on top of the finalize would be a redundant second gate.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-8, satellite-docs, archival]
related:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch8_2026_08_08.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch7_2026_08_06.md,
    /plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch7_2026_08_06_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [tradfi_satellite_ao_dispatch_batch8_2026_08_08]
gate_on_depends: true
source: >-
  /ag-closeout-audit tradfi run 2026-08-08 (autonomous mode, sharded daily `ag_closeout_auditor` worker, dispatch
  agt-ea6423, slot 6), per task_template.md section 4's finalize-plan-coverage rule — every AO-dispatched plan needs a
  companion gated finalize plan, mirroring the tradfi batch1-7 precedent.
assigned_role: data_engineering
effort: max
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch8_2026_08_08.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# TradFi satellite AO batch 8 — finalize

> **Machine-gated on `tradfi_satellite_ao_dispatch_batch8_2026_08_08.md`** (`depends_on` plus `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 3 tasks in that plan are `done`. `sequential: true` because
> todo 2 (deferred re-check) needs todo 1's reconciliation done first, and todo 3 (archival) must run last. Batch8
> itself stays `status: draft` until the operator reviews and approves it — this finalize plan needs no separate flip
> either way (see summary).

## Todos

- [ ] [REVIEW] P1. **Reconcile all 3 distinct source docs.** For each of
      `tradfi_satellite_ao_dispatch_batch8_2026_08_08.md`'s now-done todos, flip or update the corresponding checkbox in
      its named source doc (each todo's text ends with "Source: `<doc>.md`"), citing the batch-8 commit(s) that shipped
      it — verify the actual shipped commit exists before citing it. For every source doc: after reconciling, re-check
      whether it now has 0 open items (checkbox and prose). Only flip a doc's `status` to `resolved` if it genuinely
      reaches 0 open items, and never touch a doc carrying a non-empty `locked_by`. Note
      `features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md` will NOT reach 0 open items even if
      its todo 3 (item 1, malformed ticks) ships clean — its item 2 (force+skip proof) stays open, time-gated on
      upstream MDPS backfill; do not flip that doc's status. **Done when**: all 3 source docs are reconciled with
      verified evidence, and any doc that genuinely reaches 0 open items is flipped to `status: resolved`.

- [ ] [REVIEW] P1. **Re-check batch8's own Deferred/Flagged sections now that time has passed.** For the too-large-
      or-risky items, the operator-gated items, the conflict-gated item, the already-in-flight item, the
      already-drafted-elsewhere item, the time-gated item, and the cross-tranche-flagged items: re-read the specific
      gating ground to check whether it has since cleared — if the operator has ruled, a dedicated plan has been
      authored, `tradfi_forexfactory_econ_calendar_consensus_capture_2026_07_30.md` has been promoted out of draft,
      `governance_sweep_deferred_followups_2026_08_06.md`'s own conflicting `[DIAG] P2` todo has resolved (clearing
      `tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`'s todo 1 for extraction),
      `tradfi_satellite_ao_dispatch_batch7_2026_08_06.md`'s todo 3 has landed (clearing
      `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md` for a delete-todo draft), or a stale tag has been
      corrected, extract it as a new tracked todo in a follow-up `batch9` (do NOT draft it directly here); if still
      genuinely unresolved, leave it explicitly deferred and do NOT re-ask an already-asked operator question. For the
      cross-tranche-flagged items, check whether the owning tranche has since acted (or dispatch a note to that
      tranche's own audit if not, rather than adopting it into tradfi). **Done when**: each Deferred/Flagged item has
      either (a) a note that it is ready for `batch9` extraction because its gate cleared, or (b) an explicit
      re-verified confirmation the gate is still open, with evidence cited.

- [ ] [DOC] P1. **Archive `tradfi_satellite_ao_dispatch_batch8_2026_08_08.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred/Flagged items to a tracked todo elsewhere (todo 2
      above should have already resolved or re-confirmed all of them — verify none silently vanish) → add the archive
      banner → run the codex-alignment check (batch8 creates no new durable contract; confirm no drift) → grep the
      corpus for every referrer of `tradfi_satellite_ao_dispatch_batch8_2026_08_08` and fix each path to point at the
      archived location → clear `locked_by` (already empty here, confirm). **Done when**: the plan is moved to
      `plans/archive/2026_08/`, every corpus referrer resolves to the new path, and this finalize doc itself is archived
      alongside it in the same commit.

## Progress Log

- **2026-08-08 (ag_closeout_auditor, slot 6)**: created alongside batch8, same run.
- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).

## Codex SSOTs

No new durable contract is created by this plan. `/codex/11-project-management/` carries the archival ritual;
`plans/PLAN_FORMAT.md` carries the `status: draft` and `gate_on_depends` semantics this plan relies on.
