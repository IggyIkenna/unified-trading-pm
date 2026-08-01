---
doc_type: plan
title: DeFi satellite AO batch 7 — finalize (reconcile source docs + archive)
summary: >-
  Gated closeout for defi_satellite_ao_dispatch_batch7_2026_08_01.md — machine-held via depends_on + gate_on_depends:
  true until all 4 of that plan's todos are done. Mirrors batch1-6-finalize's pattern: reconcile each of the 2 distinct
  source docs' checkboxes independently once their batch-7 todo(s) land, re-check the 2 Deferred conflict-found items
  for whether their blocking claim has since cleared, then archive batch7 via the standard 6-step ritual.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-7, satellite-docs, archival]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch7_2026_08_01.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
  ]
created: "2026-08-01"
last_updated: "2026-08-01"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.3
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/defi_satellite_ao_dispatch_batch7_2026_08_01.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
depends_on: [defi_satellite_ao_dispatch_batch7_2026_08_01]
gate_on_depends: true
source: >-
  `/na-eligibility-audit defi` run 2026-08-01 (autonomous, scheduled na_eligibility_auditor), per task_template.md §4's
  finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# DeFi satellite AO batch 7 — finalize

**status: active — gated on batch7's 4 todos via `depends_on` + `gate_on_depends: true`; the dispatcher will not release
these until batch7 is fully done.**

## Todos

- [ ] [DOC] P1. Once all 4 of `defi_satellite_ao_dispatch_batch7_2026_08_01.md`'s todos are `[x]`, reconcile each of the
      2 distinct source docs (`defi_consolidated_closeout_2026_07_18.md` — 3 of the 4 todos;
      `issues/     mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md` — the 4th) — flip/annotate their own
      checkboxes with the batch-7 commit SHA, so a doc read independently (outside this batch) shows accurate state.
      Repo: unified-trading-pm. Done when: both source docs show an annotation citing the batch-7 todo + commit SHA that
      closed their item.
- [ ] [DOC] P2. Re-check the 2 Deferred conflict-found items (the `setup-data-pipeline-vm.sh` canonical-migration `cd`
      bug parked on `defi_consolidated_native_ao_extract_2026_07_25.md`'s in-progress claim; the "QG HARNESS collects
      the wrong test suite" finding parked on `defi_satellite_ao_dispatch_batch6_2026_07_30.md`'s under-evidenced
      verdict) — if the native-extract plan's fix has since shipped, or a scoping read has since evidenced the
      QG-harness finding, resolve/close the parked note (fold into a batch8 todo if new bounded work results; otherwise
      mark resolved-no-action). Repo: unified-trading-pm. Done when: both parked items have an explicit
      resolved/still-open verdict recorded.
- [ ] [DOC] P1. Archive `defi_satellite_ao_dispatch_batch7_2026_08_01.md` via the standard 6-step ritual (migrate any
      residual DEFERRED items → banner → codex-alignment check → update CLAUDE.md/codex on any new contract → update
      every referrer's path corpus-wide → clear lock). Repo: unified-trading-pm. Done when: batch7 is in
      `plans/archive/2026_08/` with a superseded_by/archived banner and zero remaining referrers to its old
      `plans/active/` path.

## Progress Log

- 2026-08-01 (slot-7, scheduled `na_eligibility_auditor`): Drafted alongside batch7, both `status: active`, gated on
  batch7's 4 todos via `depends_on` + `gate_on_depends: true`. No work started — waiting on batch7's todos to land.
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
