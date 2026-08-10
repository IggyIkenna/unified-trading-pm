---
doc_type: plan
title: TradFi satellite AO batch 7 — finalize (reconcile source docs + resolve deferrals + archive)
summary: >-
  Gated closeout for tradfi_satellite_ao_dispatch_batch7_2026_08_06.md — machine-held via depends_on plus
  gate_on_depends: true until all 4 of that plan's todos are done. Mirrors the batch1-6-finalize pattern: reconcile each
  distinct source doc's checkboxes once its batch-7 todo lands, then re-check batch7's own Deferred sections (too-large-
  or-risky / operator-gated / self-dispatched-stale-tag / already-drafted-elsewhere / cross-tranche-flagged) for any
  that have since cleared, then archive batch7 via the standard 6-step ritual. Ships `status: active` from the start
  (not draft) — per the 2026-07-30 ruling this skill's SKILL.md documents, a finalize plan carries no independent
  judgment call and gate_on_depends already machine-holds every task until batch7 itself is done, so stacking batch7's
  own draft safety-rail on top of the finalize would be a redundant second gate.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-7, satellite-docs, archival]
related:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch7_2026_08_06.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch6_2026_08_01.md,
    /plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch6_2026_08_01_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-06"
last_updated: "2026-08-06"
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
depends_on: [tradfi_satellite_ao_dispatch_batch7_2026_08_06]
gate_on_depends: true
source: >-
  /ag-closeout-audit tradfi run 2026-08-06 (autonomous mode, sharded daily `ag_closeout_auditor` worker, dispatch
  agt-7d91ed, slot 3), per task_template.md section 4's finalize-plan-coverage rule — every AO-dispatched plan needs a
  companion gated finalize plan, mirroring the tradfi batch1-6 precedent.
assigned_role: data_engineering
effort: max
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch7_2026_08_06.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# TradFi satellite AO batch 7 — finalize

> **Machine-gated on `tradfi_satellite_ao_dispatch_batch7_2026_08_06.md`** (`depends_on` plus `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 4 tasks in that plan are `done`. `sequential: true` because
> todo 2 (deferred re-check) needs todo 1's reconciliation done first, and todo 3 (archival) must run last. Batch7
> itself stays `status: draft` until the operator reviews and approves it — this finalize plan needs no separate flip
> either way (see summary).

## Todos

- [ ] [REVIEW] P1. **Reconcile all 5 distinct source docs.** For each of
      `tradfi_satellite_ao_dispatch_batch7_2026_08_06.md`'s now-done todos, flip or update the corresponding checkbox in
      its named source doc (each todo's text ends with "Source: `<doc>.md`" — note todo 2 cites 2 source docs), citing
      the batch-7 commit(s) that shipped it — verify the actual shipped commit exists before citing it. For every source
      doc: after reconciling, re-check whether it now has 0 open items (checkbox and prose). Only flip a doc's `status`
      to `resolved` if it genuinely reaches 0 open items, and never touch a doc carrying a non-empty `locked_by`. **Done
      when**: all 5 source docs are reconciled with verified evidence, and any doc that genuinely reaches 0 open items
      is flipped to `status: resolved`.

- [ ] [REVIEW] P1. **Re-check batch7's own Deferred/Flagged sections now that time has passed.** For the too-large-or-
      risky items, the operator-gated items, the self-dispatched-stale-tag items, the already-drafted-elsewhere items,
      and the cross-tranche-flagged items: re-read the specific gating ground to check whether it has since cleared — if
      the operator has ruled, a dedicated plan has been authored,
      `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` or
      `tradfi_forexfactory_econ_calendar_consensus_capture_2026_07_30.md` has been promoted out of draft, or a stale
      `[OPERATOR]` tag has been corrected, extract it as a new tracked todo in a follow-up `batch8` (do NOT draft it
      directly here); if still genuinely unresolved, leave it explicitly deferred and do NOT re-ask an already-asked
      operator question. For the cross-tranche-flagged items, check whether the owning tranche has since acted (or
      dispatch a note to that tranche's own audit if not, rather than adopting it into tradfi). **Done when**: each
      Deferred/Flagged item has either (a) a note that it is ready for `batch8` extraction because its gate cleared, or
      (b) an explicit re-verified confirmation the gate is still open, with evidence cited.

- [ ] [DOC] P1. **Archive `tradfi_satellite_ao_dispatch_batch7_2026_08_06.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred/Flagged items to a tracked todo elsewhere (todo 2
      above should have already resolved or re-confirmed all of them — verify none silently vanish) → add the archive
      banner → run the codex-alignment check (batch7 creates no new durable contract; confirm no drift) → grep the
      corpus for every referrer of `tradfi_satellite_ao_dispatch_batch7_2026_08_06` and fix each path to point at the
      archived location → clear `locked_by` (already empty here, confirm). **Done when**: the plan is moved to
      `plans/archive/2026_08/`, every corpus referrer resolves to the new path, and this finalize doc itself is archived
      alongside it in the same commit.

## Progress Log

- **context-scout 2026-08-07**: refreshed context_scope (4 entries, unchanged) — `*_finalize` gate doc, genuinely
  code-free (all 3 todos are checkbox-reconciliation/re-triage/archival, no code target); the gating parent batch, the
  umbrella closeout, the audit methodology, and the archival-ritual codex doc remain the correct minimal set.
- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).

## Codex SSOTs

No new durable contract is created by this plan. `/codex/11-project-management/` carries the archival ritual;
`plans/PLAN_FORMAT.md` carries the `status: draft` and `gate_on_depends` semantics this plan relies on.
