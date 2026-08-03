---
doc_type: plan
title: DeFi satellite AO batch 5 — finalize (reconcile source docs + resolve deferrals + archive)
summary: >-
  Gated closeout for defi_satellite_ao_dispatch_batch5_2026_07_27.md — machine-held via depends_on + gate_on_depends:
  true until all 7 of that plan's todos are done. Mirrors batch1-4-finalize's pattern (reconcile each distinct source
  doc's checkboxes independently once its batch-5 todo lands, then re-check the Deferred conflict-gated/
  operator-gated/time-gated/too-large/human-only items for any that have since cleared), then archives batch5 via the
  standard 6-step ritual. Activated 2026-07-30 alongside its parent batch5 (operator go-ahead); execution stays
  machine-gated on batch5's todos via depends_on + gate_on_depends, not via a draft status.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-5, satellite-docs, archival]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch5_2026_07_27.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch4_2026_07_26_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-30"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.5
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [defi_satellite_ao_dispatch_batch5_2026_07_27]
gate_on_depends: true
source: >-
  `/ag-closeout-audit defi` run 2026-07-27 (autonomous, scheduled ag_closeout_auditor), per task_template.md §4's
  finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan, mirroring the defi
  batch1-4 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/defi_satellite_ao_dispatch_batch5_2026_07_27.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch4_2026_07_26_finalize.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# DeFi satellite AO batch 5 — finalize

**status: active — parent batch5 was operator-approved + dispatched 2026-07-30** (`unified-trading-pm@5a6bbefc3`).
Execution remains machine-held until every batch5 todo is `[x]`, via
`depends_on: [defi_satellite_ao_dispatch_batch5_2026_07_27]` + `gate_on_depends: true` — the redundant `status: draft`
double-gate that finalize plans used to carry was removed corpus-wide in `unified-trading-pm@233ebd614`.

## Todos

- [ ] [DOC] P1. Once all 7 of `defi_satellite_ao_dispatch_batch5_2026_07_27.md`'s todos are `[x]`, reconcile each of the
      7 distinct source docs (see that plan's Todos section, each ending `Source: ...`) — flip/annotate their own
      checkboxes with the batch-5 commit SHA, so a doc read independently (outside this batch) shows accurate state.
      Repo: unified-trading-pm. Done when: all 7 source docs show an annotation citing the batch-5 todo + commit SHA
      that closed their item.
- [ ] [DOC] P2. Re-check the 2 conflict-gated Deferred items (`architecture_v2_drift_leg_specs_and_manifest_residue`
      CARRY_STAKED_BASIS delete-vs-re-leg call; `defi_track5_coverage_mvp_backfill`'s PYTH SPOT-backfill overlap with
      batch3's C6) — if the operator has ruled on the strategy-domain call, or if batch3's C6 Pyth backfill has landed
      and its window is confirmed to fully cover the candidate's window, resolve/close the parked note (fold into a
      batch6 todo if the operator's ruling produces new bounded work; otherwise mark resolved-no-action). Repo:
      unified-trading-pm. Done when: both parked items have an explicit resolved/still-open verdict recorded.
- [ ] [DOC] P2. Re-check the 24-doc non-batchable Deferred taxonomy list for any operator-gated/time-gated item that has
      since cleared (an operator ruling landed, a gating VM/backfill completed, a dependent doc's status changed) — move
      any now-clear item into a fresh batch6 candidate list rather than re-triaging the whole corpus from scratch. Repo:
      unified-trading-pm. Done when: each of the 24 items has a dated re-check note (cleared / still blocked, with the
      specific evidence checked).
- [ ] [DOC] P3. Confirm the known mistag
      (`archive/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md`) has actually been retagged
      away from `asset_group: [defi]` by its already-tracked
      `defi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md:73-76` todo; if still untagged, do not re-draft a new
      todo — just verify the existing todo is still open and note its status here. Repo: unified-trading-pm. Done when:
      a verdict (retagged / still open, citing the batch2-finalize todo state) is recorded.
- [ ] [DOC] P1. Archive `defi_satellite_ao_dispatch_batch5_2026_07_27.md` via the standard 6-step ritual (migrate any
      residual DEFERRED items → banner → codex-alignment check → update CLAUDE.md/codex on any new contract → update
      every referrer's path corpus-wide → clear lock). Repo: unified-trading-pm. Done when: batch5 is in
      `plans/archive/2026_07/` with a superseded_by/archived banner and zero remaining referrers to its old
      `plans/active/` path.

## Progress Log

- 2026-07-27 (slot-4, scheduled `ag_closeout_auditor`): Drafted alongside batch5, both `status: draft`, gated on
  batch5's 7 todos via `depends_on` + `gate_on_depends: true`. No work started — waiting on operator approval of batch5
  first.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- 2026-08-02 (worker, slot-3): De-staled the body banner + `summary:` — both still said `status: draft` while the
  frontmatter had been `active` since 2026-07-30. No todo/gating change: this plan stays machine-held on batch5 via
  `depends_on` + `gate_on_depends: true`. Note for whoever runs todo 1: batch5 now has 3 of 7 todos closed (one more was
  verified-stale + flipped 2026-08-02), so only 4 source docs remain to reconcile, not 7.
