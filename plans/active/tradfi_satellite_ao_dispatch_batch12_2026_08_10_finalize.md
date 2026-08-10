---
doc_type: plan
title: TradFi satellite AO batch 12 — finalize (reconcile source doc + archive)
summary: >-
  Gated closeout for tradfi_satellite_ao_dispatch_batch12_2026_08_10.md — machine-held via depends_on plus
  gate_on_depends: true until both of that plan's todos are done. Reconciles the 1 source doc
  (`issues/cboe_venue_level_discovery_floor_blocks_yahoo_treasury_pre_2020_2026_08_09.md`, flip/cite both items batch12
  closes), then archives batch12 via the standard 6-step ritual. Ships `status: active` from the start (not draft) — per
  the 2026-07-30 ruling this skill's SKILL.md documents (mirrored from batch11's finalize): a finalize plan carries no
  independent judgment call and gate_on_depends already machine-holds every task until batch12 itself is done, so
  stacking batch12's own draft safety-rail on top of the finalize would be a redundant second gate.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-12, satellite-docs, archival]
related:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch12_2026_08_10.md,
    /plans/active/issues/cboe_venue_level_discovery_floor_blocks_yahoo_treasury_pre_2020_2026_08_09.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch11_2026_08_10.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch11_2026_08_10_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
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
depends_on: [tradfi_satellite_ao_dispatch_batch12_2026_08_10]
gate_on_depends: true
source: >-
  /ag-closeout-audit tradfi run 2026-08-10 (sharded daily `ag_closeout_auditor` worker, dispatch agt-a19d1f, slot 22),
  per task_template.md section 4's finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated
  finalize plan, mirroring the tradfi batch1-11 precedent.
assigned_role: data_engineering
effort: high
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch12_2026_08_10.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# TradFi satellite AO batch 12 — finalize

> **Machine-gated on `tradfi_satellite_ao_dispatch_batch12_2026_08_10.md`** (`depends_on` plus `gate_on_depends: true`)
> — the dispatcher will not queue any todo below until both tasks in that plan are `done`. `sequential: true` because
> archival (todo 2) must run after reconciliation (todo 1). Batch12 itself stays `status: draft` until the operator
> reviews and approves it — this finalize plan needs no separate flip either way (see summary).

## Todos

- [ ] [REVIEW] P1. **Reconcile the source doc.** For
      `issues/cboe_venue_level_discovery_floor_blocks_yahoo_treasury_pre_2020_2026_08_09.md`'s 2 todos, flip each to
      `[x]` citing the batch-12 commit(s) that shipped it — verify the actual shipped commit exists (code diff + passing
      regression tests for todo 1; a live manifest query showing populated pre-2020 CBOE `ohlcv_24h` rows for todo 2)
      before citing. Once both are closed, the source doc has 0 open items — flip its `status` to `resolved`. Repo:
      unified-trading-pm. Done when: the source doc shows both items closed-by-citation and `status: resolved`.
- [ ] [DOC] P1. **Archive `tradfi_satellite_ao_dispatch_batch12_2026_08_10.md`** via the standard 6-step ritual (per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`): add the archived-banner cross-reference,
      run the post-phase codex audit (confirm no new durable contract is owed — this batch documents no new pattern),
      confirm no CLAUDE.md contract changed, update every corpus referrer (this finalize doc,
      `tradfi_consolidated_closeout_2026_07_18.md`'s `related:` if it was ever added there, and the source doc itself),
      `git mv` to `plans/archive/2026_08/`. Repo: unified-trading-pm. Done when: batch12 is at its archived path with
      every referrer updated and this finalize plan's own todos all `[x]`.

## Progress Log

- **2026-08-10 (ag_closeout_auditor, slot 22, dispatch agt-a19d1f)**: created alongside batch12, same run.
