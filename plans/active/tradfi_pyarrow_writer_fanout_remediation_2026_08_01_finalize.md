---
doc_type: plan
title:
  TradFi pyarrow per-symbol-writer fan-out remediation — finalize (reconcile source docs + resolve deferral + archive)
summary: >-
  Gated closeout for tradfi_pyarrow_writer_fanout_remediation_2026_08_01.md — machine-held via depends_on plus
  gate_on_depends: true until both of that plan's todos are done. Reconciles the outcome back into
  `issues/tradfi_backfill_oom_remediation_2026_06_24.md`'s P3 todo and
  `tradfi_backfill_throughput_followups_2026_07_24.md`'s bundled OOM digest line, re-checks whether the parent plan's
  own Deferred structural-options note now needs to become a real tracked follow-up, then archives the parent via the
  standard 6-step ritual. Ships `status: active` from the start (not draft) — per the 2026-07-30 ruling
  `cursor-configs/skills/ag-closeout-audit/SKILL.md` documents, a finalize plan carries no independent judgment call
  (its content is fully decided at authoring time) and gate_on_depends already machine-holds every task until the parent
  is done, so a separate draft safety-rail on top would be a redundant second gate nobody reliably remembers to lift.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [tradfi, backfill, oom, pyarrow, close-out, archival]
related:
  [
    /plans/active/tradfi_pyarrow_writer_fanout_remediation_2026_08_01.md,
    /plans/active/issues/tradfi_backfill_oom_remediation_2026_06_24.md,
    /plans/active/tradfi_backfill_throughput_followups_2026_07_24.md,
  ]
created: "2026-08-01"
last_updated: "2026-08-01"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: backend_engineer
sequential: true
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [tradfi_pyarrow_writer_fanout_remediation_2026_08_01]
gate_on_depends: true
source: >-
  Authored alongside tradfi_pyarrow_writer_fanout_remediation_2026_08_01.md per task_template.md §4's mandatory
  finalize-plan-coverage rule (operator ruling 2026-07-24) — every AO-dispatched multi-todo plan needs a companion gated
  finalize plan. Mirrors the tradfi satellite-batch finalize precedent
  (`tradfi_satellite_ao_dispatch_batch6_2026_08_01_finalize.md`).
context_scope:
  [
    /plans/active/tradfi_pyarrow_writer_fanout_remediation_2026_08_01.md,
    /plans/active/issues/tradfi_backfill_oom_remediation_2026_06_24.md,
    /plans/active/tradfi_backfill_throughput_followups_2026_07_24.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# TradFi pyarrow per-symbol-writer fan-out remediation — finalize

> **Machine-gated on `tradfi_pyarrow_writer_fanout_remediation_2026_08_01.md`** (`depends_on` plus
> `gate_on_depends: true`) — the dispatcher will not queue any todo below until both tasks in that plan are `done`.
> `sequential: true` because todo 2 (deferral re-check) reads todo 1's reconciliation output, and todo 3 (archival) must
> run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile both named source docs.** For each of
      `tradfi_pyarrow_writer_fanout_remediation_2026_08_01.md`'s now-done todos (worst-case writer-path confirmation +
      memray measurement; the low-risk pyarrow tuning fix or negative finding), update
      `issues/tradfi_backfill_oom_remediation_2026_06_24.md`'s `[TRADFI] P3` todo — flip it `[x]` with the shipped
      commit(s) cited (verify each cited commit actually exists and touches the claimed file before citing it) if the
      parent plan's outcome fully resolves it, or append a dated note explaining what remains open (e.g. the
      structural-options deferral) if it doesn't fully resolve. Also update
      `tradfi_backfill_throughput_followups_2026_07_24.md`'s bundled "Backfill-VM startup OOM rc137 + OOM remediation
      baked default + consolidator throughput/backlog monitor" digest line to drop or update the pyarrow-fan-out portion
      per the actual outcome. **Done when**: both docs are reconciled with verified evidence citations, and
      `issues/tradfi_backfill_oom_remediation_2026_06_24.md` is re-checked for whether it now has 0 open items overall
      (it likely still carries the sibling `[CODE] P1` `vm-exec-with-gcs-tee.sh` stall-watchdog todo and the `[DATA] P2`
      relaunch-babysit todo from its 2026-07-31 findings — only flip its `status` to `resolved` if it genuinely reaches
      0 open items).

- [ ] [REVIEW] P1. **Re-check the parent plan's "Deferred — needs its own dedicated design pass" section now that time
      has passed.** Read todo 1's reconciled outcome above: if it recorded "no safe tuning knob helped enough" (or the
      worst-case memray measurement shows peak RSS still threatens the current machine ceiling despite the tuning), that
      is the stated trigger for a fresh design pass on the structural options (shared-writer batching / capped-writer
      eager-close) — extract it as a new tracked todo in a follow-up plan or issue doc (do NOT draft the design decision
      directly here; that is exactly the open-ended judgment call `task_template.md` §4 keeps out of a single todo). If
      the tuning fix (or the worst-case measurement) instead shows the mechanism is no longer a concern, record that
      explicitly and do not spin up unnecessary follow-up work. **Done when**: either (a) a new follow-up todo/plan
      reference is filed with a one-line pointer here, or (b) an explicit note that no follow-up is warranted, with the
      evidence cited.

- [ ] [DOC] P1. **Archive `tradfi_pyarrow_writer_fanout_remediation_2026_08_01.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): confirm todo 2 above left no follow-up silently dropped → add the archive banner
      → run the codex-alignment check (this plan creates no new durable contract; confirm no drift actually occurred,
      e.g. if todo 1 of the parent shipped a real pyarrow-tuning pattern worth a codex note) → grep the corpus for every
      referrer of `tradfi_pyarrow_writer_fanout_remediation_2026_08_01` (including this finalize doc's own `related:`
      backlinks and `tradfi_backfill_throughput_followups_2026_07_24.md`'s digest) and fix each path to point at the
      archived location → clear `locked_by` (already empty here, confirm). **Done when**: the plan is moved to
      `plans/archive/2026_08/`, every corpus referrer resolves to the new path, and this finalize doc itself is archived
      alongside it in the same commit.

## Codex SSOTs

No new durable contract is created by this plan. `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`
carries the archival ritual; `plans/PLAN_FORMAT.md` carries the `status`/`gate_on_depends` semantics this plan relies
on.
