---
doc_type: plan
title: DeFi satellite AO batch 8 — finalize (reconcile source doc + archive)
summary: >-
  Gated closeout for defi_satellite_ao_dispatch_batch8_2026_08_02.md — machine-held via depends_on + gate_on_depends:
  true until that plan's todo is done. Mirrors batch1-7-finalize: reconcile the single source doc
  (lst_rate_honest_coverage_2026_07_21.md Phase 3) once the batch-8 todo lands, re-check the 2 Deferred
  classified-but-not-extracted items for whether their blocking condition has since cleared, then archive batch8 via the
  standard 6-step ritual.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-8, satellite-docs, archival]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch8_2026_08_02.md,
    /plans/active/lst_rate_honest_coverage_2026_07_21.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
  ]
created: "2026-08-02"
last_updated: "2026-08-02"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/defi_satellite_ao_dispatch_batch8_2026_08_02.md,
    /plans/active/lst_rate_honest_coverage_2026_07_21.md,
    /plans/active/issues/defi_catalog_dp_catalog_001_shrink_blocked_2026_08_02.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
depends_on: [defi_satellite_ao_dispatch_batch8_2026_08_02]
gate_on_depends: true
source: >-
  `/na-eligibility-audit defi` run 2026-08-02 (autonomous, scheduled na_eligibility_auditor), per task_template.md §4's
  finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# DeFi satellite AO batch 8 — finalize

**status: active — gated on batch8's todo via `depends_on` + `gate_on_depends: true`; the dispatcher will not release
these until batch8 is fully done.**

## Todos

- [ ] [DOC] P1. Once `defi_satellite_ao_dispatch_batch8_2026_08_02.md`'s todo is `[x]`, reconcile the single source doc
      [`/plans/active/lst_rate_honest_coverage_2026_07_21.md`](/plans/active/lst_rate_honest_coverage_2026_07_21.md) —
      flip/annotate its Phase-3 `[MTDS] P3` checkbox with the batch-8 evidence (VM name + `run.log` verdict per surface,
      not just a commit SHA — this is a runtime-verification todo, so the proof is the log, per that plan's own
      wording). Repo: unified-trading-pm. Done when: the source plan's Phase-3 item shows an annotation citing the
      batch-8 todo and its measured force/skip verdicts.
- [ ] [DOC] P2. Re-check the 2 Deferred classified-but-not-extracted items in batch8: (a) the composite-venue fold
      stale-checkbox correction — confirm it stayed closed and that
      `issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md`'s remaining `[PM] P2` delete-phase item is
      still the only open work there; (b) `issues/defi_catalog_dp_catalog_001_shrink_blocked_2026_08_02.md`'s
      `[DATA] P2` vanished-VM forensics — if the operator's R3 decision has landed and main's standing hold is lifted,
      that item is now extractable, so fold it into a batch9 todo; if the hold is still live, record that plainly and
      leave it. Repo: unified-trading-pm. Done when: both items have an explicit resolved/still-held verdict recorded.
- [ ] [DOC] P1. Archive `defi_satellite_ao_dispatch_batch8_2026_08_02.md` via the standard 6-step ritual (migrate any
      residual DEFERRED items → banner → codex-alignment check → update CLAUDE.md/codex on any new contract → update
      every referrer's path corpus-wide → clear lock). Repo: unified-trading-pm. Done when: batch8 is in
      `plans/archive/2026_08/` with an archived banner and zero remaining referrers to its old `plans/active/` path.

## Progress Log

- 2026-08-02 (scheduled `na_eligibility_auditor`, tranche=defi, autonomous): Drafted alongside batch8, both
  `status: active`, gated on batch8's todo via `depends_on` + `gate_on_depends: true`. No work started — waiting on
  batch8's todo to land.
- **context-scout 2026-08-03**: populated/refreshed context_scope (4 entries).
