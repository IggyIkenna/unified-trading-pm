---
doc_type: plan
title: TradFi satellite AO batch 9 — finalize (reconcile source doc + archive)
summary: >-
  Gated closeout for tradfi_satellite_ao_dispatch_batch9_2026_08_16.md — machine-held via depends_on plus
  gate_on_depends: true until batch9's sole todo is done. Mirrors the batch1-8-finalize pattern: reconcile the source
  doc's checkbox once batch9's todo lands, then archive batch9 via the standard 6-step ritual. Ships `status: active`
  from the start (not draft) — per the 2026-07-30 ruling this skill's SKILL.md documents, a finalize plan carries no
  independent judgment call and gate_on_depends already machine-holds every task until batch9 itself is done.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-9, satellite-docs, archival]
related:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch9_2026_08_16.md,
    /plans/archive/2026_08/issues/tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md,
    /plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch8_2026_08_08_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-17"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.15
estimate_calibrated_ai_days: 0.12
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [tradfi_satellite_ao_dispatch_batch9_2026_08_16]
gate_on_depends: true
source: >-
  Created alongside batch9, same session, mirroring the batch1-8 finalize-plan-coverage rule — every AO-dispatched plan
  needs a companion gated finalize plan.
assigned_role: data_engineering
effort: max
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch9_2026_08_16.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# TradFi satellite AO batch 9 — finalize

> **Machine-gated on `tradfi_satellite_ao_dispatch_batch9_2026_08_16.md`** (`depends_on` plus `gate_on_depends: true`)
> — the dispatcher will not queue any todo below until that plan's sole todo is `done`. `sequential: true` because
> todo 2 (archival) must run after todo 1 (reconciliation). Batch9 itself stays `status: draft` until the operator
> reviews and approves it — this finalize plan needs no separate flip either way.

## Todos

- [ ] [REVIEW] P1. **Reconcile the source doc.** Once batch9's todo 1 lands, flip
      `tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`'s todo 2 checkbox, citing batch9's commit(s)
      and run evidence — verify the actual shipped evidence exists before citing it. Re-check whether the doc now has
      0 open items (checkbox and prose); only flip its `status` to `resolved` if it genuinely reaches 0 open items, and
      never touch it if it carries a non-empty `locked_by`. **Done when**: the source doc is reconciled with verified
      evidence, and its `status` is flipped to `resolved` if it genuinely reaches 0 open items.

- [ ] [DOC] P1. **Archive `tradfi_satellite_ao_dispatch_batch9_2026_08_16.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): add the archive banner → run the codex-alignment check (batch9 creates no new
      durable contract; confirm no drift) → grep the corpus for every referrer of
      `tradfi_satellite_ao_dispatch_batch9_2026_08_16` and fix each path to point at the archived location → clear
      `locked_by` (already empty here, confirm). **Done when**: the plan is moved to `plans/archive/2026_08/`, every
      corpus referrer resolves to the new path, and this finalize doc itself is archived alongside it in the same
      commit.

## Progress Log

- **2026-08-16 (slot 5, review)**: created alongside batch9, same session.
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries).

## Codex SSOTs

No new durable contract is created by this plan. `/codex/11-project-management/` carries the archival ritual;
`plans/PLAN_FORMAT.md` carries the `status: draft` and `gate_on_depends` semantics this plan relies on.
