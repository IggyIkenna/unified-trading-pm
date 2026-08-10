---
doc_type: plan
title: TradFi satellite AO batch 6 — finalize (reconcile source docs + resolve deferrals + archive)
summary: >-
  Gated closeout for tradfi_satellite_ao_dispatch_batch6_2026_08_01.md — machine-held via depends_on plus
  gate_on_depends: true until all 4 of that plan's todos are done. Mirrors the batch1-5-finalize pattern: reconcile each
  distinct source doc's checkboxes once its batch-6 todo lands, then re-check batch6's own Deferred too-large-or-risky /
  operator-gated / precondition-changed items for any that have since cleared (in particular: did the CME
  instrument-definitions re-fetch get a dedicated plan; did batch5's todo 2 finally clear the MDPS blocker gating
  tradfi_sp500_ml_and_arb_backtest_readiness; has the legacy-twin-bucket 0%-coverage root cause been investigated), then
  archive batch6 via the standard 6-step ritual. Ships `status: active` from the start (not draft) — per the 2026-07-30
  ruling this skill's SKILL.md documents, a finalize plan carries no independent judgment call (its content is fully
  decided at authoring time) and gate_on_depends already machine-holds every task until batch6 itself is done, so
  stacking batch6's own draft safety-rail on top of the finalize would be a redundant second gate nobody reliably
  remembers to lift.
status: archived
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-6, satellite-docs, archival]
related:
  [
    /plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch6_2026_08_01.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/tradfi_satellite_ao_dispatch_batch5_2026_07_29_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-01"
last_updated: "2026-08-01"
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
depends_on: [tradfi_satellite_ao_dispatch_batch6_2026_08_01]
gate_on_depends: true
source: >-
  /ag-closeout-audit tradfi run 2026-08-01 (autonomous mode, scheduled daily `ag_closeout_auditor` worker, dispatch
  agt-d7b683, slot 2), per task_template.md section 4's finalize-plan-coverage rule — every AO-dispatched plan needs a
  companion gated finalize plan, mirroring the tradfi batch1-5 precedent.
assigned_role: data_engineering
effort: max
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch6_2026_08_01.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# TradFi satellite AO batch 6 — finalize

> **Machine-gated on `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md`** (`depends_on` plus `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 4 tasks in that plan are `done`. `sequential: true` because
> todo 2 (deferred re-check) needs todo 1's reconciliation done first, and todo 3 (archival) must run last. Batch6
> itself stays `status: draft` until the operator reviews and approves it — this finalize plan needs no separate flip
> either way (see summary).

## Todos

- [x] ✅ [REVIEW] P1. **Reconcile all 4 distinct source docs.** For each of
      `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md`'s now-done todos, flip or update the corresponding checkbox in
      its named source doc (each todo's text ends with "Source: `<doc>.md`"), citing the batch-6 commit(s) that shipped
      it — verify the actual shipped commit exists before citing it. For every source doc: after reconciling, re-check
      whether it now has 0 open items (checkbox and prose). Only flip a doc's `status` to `resolved` if it genuinely
      reaches 0 open items, and never touch a doc carrying a non-empty `locked_by`. **Done when**: all 4 source docs are
      reconciled with verified evidence, and any doc that genuinely reaches 0 open items is flipped to
      `status: resolved`. — **Done 2026-08-10.** Todos #1 (null-id) and #4 (BASE_ASSET) were already reconciled by
      slot-7. Todo #2 (ES_OPT) and #3 (anomalous Sundays) reconciled in this session:
      `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` ES_OPT checkboxes flipped + anomalous Sundays deferred
      table updated with root cause. Source docs #1/#4 already archived — no further action needed.

- [x] ✅ [REVIEW] P1. **Re-check batch6's own Deferred sections now that time has passed.** For the 3 too-large-or-risky
      items, the 3 operator-gated items, the 1 precondition-changed item (legacy-twin-bucket delete), and the 1
      flagged-not-batched cross-tranche item (`mtds_is_full_adapter_smoketest_findings_2026_07_07.md`): re-read the
      specific gating ground to check whether it has since cleared — if the operator has ruled, a dedicated plan has
      been authored for the CME re-fetch, batch5's todo 2 finally shipped (clearing
      `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`), or the legacy-twin 0%-coverage root cause has been
      investigated, extract it as a new tracked todo in a follow-up `batch7` (do NOT draft it directly here); if still
      genuinely unresolved, leave it explicitly deferred and do NOT re-ask an already-asked operator question. For the
      cross-tranche-owned smoketest-findings doc, check whether the owning tranche has since acted on it (or dispatch a
      note to that tranche's own audit if not, rather than adopting it into tradfi). **Done when**: each
      Deferred/flagged item has either (a) a note that it is ready for `batch7` extraction because its gate cleared, or
      (b) an explicit re-verified confirmation the gate is still open, with evidence cited. — **Done 2026-08-10.**
      Re-verified all 8 items: 3 too-large-or-risky (still gated — CME re-fetch no dedicated plan yet; batch5 todo #2
      still `[ ]` open; data_completion items unchanged), 3 operator-gated (no new rulings since batch5), 1
      precondition-changed (legacy-twin 0%-coverage still uninvestigated), 1 cross-tranche (smoketest-findings — item 4
      `fetch_yahoo_equities` confirmed still-open as of 2026-08-01 audit, no action by owning tranche). All 8 unchanged
      from batch6's own deferred assessment — ready for batch7 extraction when triggered.

- [x] ✅ [DOC] P1. **Archive `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todo 2 above
      should have already resolved or re-confirmed all of them — verify none silently vanish) → add the archive banner →
      run the codex-alignment check (batch6 creates no new durable contract; confirm no drift) → grep the corpus for
      every referrer of `tradfi_satellite_ao_dispatch_batch6_2026_08_01` and fix each path to point at the archived
      location → clear `locked_by` (already empty here, confirm). **Done when**: the plan is moved to
      `plans/archive/2026_08/`, every corpus referrer resolves to the new path, and this finalize doc itself is archived
      alongside it in the same commit.

## Codex SSOTs

No new durable contract is created by this plan. `/codex/11-project-management/` carries the archival ritual;
`plans/PLAN_FORMAT.md` carries the `status: draft` and `gate_on_depends` semantics this plan relies on.

## Progress Log

- **context-scout 2026-08-03**: re-verified context_scope (4 entries, all resolving) — finalize gate, code-free; no
  changes needed.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).
