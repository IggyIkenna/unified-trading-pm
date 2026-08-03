---
doc_type: plan
title: DeFi satellite AO batch 6 — finalize (reconcile source docs + resolve deferrals + archive)
summary: >-
  Gated closeout for defi_satellite_ao_dispatch_batch6_2026_07_30.md — machine-held via depends_on + gate_on_depends:
  true until all 20 of that plan's todos are done. Mirrors batch1-5-finalize's pattern (reconcile each distinct source
  doc's checkboxes independently once its batch-6 todo lands, then re-check the Deferred conflict-gated/
  operator-gated/time-gated/too-large/human-only items for any that have since cleared), then archives batch6 via the
  standard 6-step ritual. status: draft until the operator approves batch6 itself.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-6, satellite-docs, archival]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch6_2026_07_30.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_satellite_ao_dispatch_batch5_2026_07_27_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.7
estimate_calibrated_ai_days: 0.6
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [defi_satellite_ao_dispatch_batch6_2026_07_30]
gate_on_depends: true
source: >-
  `/ag-closeout-audit defi` run 2026-07-30 (autonomous, scheduled ag_closeout_auditor), per task_template.md §4's
  finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan, mirroring the defi
  batch1-5 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/defi_satellite_ao_dispatch_batch6_2026_07_30.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_satellite_ao_dispatch_batch5_2026_07_27_finalize.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# DeFi satellite AO batch 6 — finalize

**status: draft — activated only after its parent batch6 is operator-approved and dispatched.**

## Todos

- [ ] [DOC] P1. Once all 20 of `defi_satellite_ao_dispatch_batch6_2026_07_30.md`'s todos are `[x]`, reconcile each of
      the ~21 distinct source docs (see that plan's Todos section, each ending `Source: ...`) — flip/annotate their own
      checkboxes with the batch-6 commit SHA, so a doc read independently (outside this batch) shows accurate state.
      Repo: unified-trading-pm. Done when: all source docs show an annotation citing the batch-6 todo + commit SHA that
      closed their item.
- [ ] [DOC] P2. Re-check the 2 conflict-gated Deferred items (`defi_venue_lst_rates_residual_2026_07_24.md`'s SUSHISWAP
      classic-vs-V3 alias call; `issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md`'s item-2 sweep vs
      whole-doc operator-gate) — if the operator has ruled, resolve/close the parked note (fold into a batch7 todo if
      the ruling produces new bounded work; otherwise mark resolved-no-action). Repo: unified-trading-pm. Done when:
      both parked items have an explicit resolved/still-open verdict recorded.
- [ ] [DOC] P2. Re-check the 27-doc non-batchable Deferred taxonomy list for any operator-gated/time-gated item that has
      since cleared (an operator ruling landed, a gating VM/backfill completed, a dependent doc's status changed) — move
      any now-clear item into a fresh batch7 candidate list rather than re-triaging the whole corpus from scratch. Repo:
      unified-trading-pm. Done when: each item has a dated re-check note (cleared / still blocked, with the specific
      evidence checked).
- [ ] [DOC] P3. Verify the `mtds_dex_pools_swaps_backfill_verification_2026_07_24.md` todos 3+5 re-checks (held pending
      this batch's todo-6-superseding fix landing) are now actionable — if the subgraph-cascade fix todo above has
      shipped, fold todos 3+5 into a batch7 candidate; otherwise leave deferred. Repo: unified-trading-pm. Done when: a
      verdict is recorded.
- [ ] [DOC] P1. Archive `defi_satellite_ao_dispatch_batch6_2026_07_30.md` via the standard 6-step ritual (migrate any
      residual DEFERRED items → banner → codex-alignment check → update CLAUDE.md/codex on any new contract → update
      every referrer's path corpus-wide → clear lock). Repo: unified-trading-pm. Done when: batch6 is in
      `plans/archive/2026_07/` (or the current month's archive dir) with a superseded_by/archived banner and zero
      remaining referrers to its old `plans/active/` path.

## Progress Log

- 2026-07-30 (slot-2, scheduled `ag_closeout_auditor`): Drafted alongside batch6, both `status: draft`, gated on
  batch6's 20 todos via `depends_on` + `gate_on_depends: true`. No work started — waiting on operator approval of batch6
  first.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
