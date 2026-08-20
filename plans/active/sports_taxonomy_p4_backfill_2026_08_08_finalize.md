---
doc_type: plan
title: Sports taxonomy P4 — finalize (terminal coverage verdict + close the convergence doc + archive)
summary: >-
  Gated closeout for sports_taxonomy_p4_backfill_2026_08_08.md. Confirms the derived layer genuinely reached the
  2020-06-06 floor on a MEASURED count of target artifacts rather than an activity signal, closes out the stale C3
  pre-launch-corpus todo against the already-standing floor ruling, reconciles the all-vendor honest-coverage
  convergence doc, runs a billing-waste audit over the SPOT fleet the campaign used, and archives P4 — the last phase of
  the sports canonicalisation chain.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, backfill, finalize, archival, honest-coverage, data-floor]
related:
  [
    /plans/active/sports_taxonomy_p4_backfill_2026_08_08.md,
    /plans/archive/2026_08/sports_prelaunch_cf5_verify_residual_2026_07_24.md,
    /plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md,
    /codex/02-data/sports-2020-06-data-floor.md,
  ]
created: 2026-08-08
last_updated: 2026-08-17
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
assigned_role: data_engineering
effort: high
supersedes:
superseded_by:
resolved_by:
drift_direction: advance-code
depends_on: [sports_taxonomy_p4_backfill_2026_08_08]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/sports_taxonomy_p4_backfill_2026_08_08.md,
    /codex/02-data/sports-2020-06-data-floor.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
source: >-
  task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan.
locked_by:
locked_since:
---

# Sports taxonomy P4 — finalize

> **Machine-gated** on `sports_taxonomy_p4_backfill_2026_08_08.md`. This is the last phase of the sports
> canonicalisation chain — its archival closes the chain.

## Todos

- [ ] [REVIEW] P1. **Terminal coverage verdict, measured per data_type.** Confirm `odds_snapshot`, `odds_movement`, the
      relocated arbitrage series and the `horizon` axis each reach 2020-06-06 with only `captured` / `empty_confirmed` —
      zero unreconciled `attempted_failed` or `expected_unattempted`. Measure the COUNT of target artifacts created,
      entity-scoped, on `time_created`; an entity-agnostic or activity-based check can pass for hours while the target
      entity writes nothing. The audit's starting state was 13 of ~2,250 days. **Done when**: per-type day coverage and
      status breakdown are recorded and meet the bar, or the shortfall is filed as a `- [ ]` todo.
- [ ] [REVIEW] P1. **Close out the stale C3 pre-launch-corpus todo.**
      `sports_prelaunch_cf5_verify_residual_2026_07_24.md` offers a choice already foreclosed by the 2026-07-21 floor
      ruling (`unified-api-contracts@8cdf7808`) — flip its checkbox citing the ruling and P4's delete evidence, and if
      that leaves the doc at zero open todos, archive it via the 6-step ritual. **Done when**: the todo is flipped
      citing the floor ruling, and the doc is archived if empty.
- [ ] [REVIEW] P1. **Reconcile `/plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md`.**
      That doc carries the operator's "100% honest coverage, IS and MTDS, including odds_api" mandate for sports — P4 is
      what discharges it. Flip its checkboxes with the measured evidence rather than duplicating its tracking, and
      archive it if it reaches zero open todos. **Done when**: its state reflects the measured outcome.
- [ ] [REVIEW] P2. **Run `/vm-preemption-billing-waste-audit` over the campaign's SPOT fleet** and confirm no VM was
      preempted without recovery and no structurally non-retriable `attempted_failed` shard is being re-attempted every
      wave. **Done when**: the audit is run and its result recorded.
- [ ] [REVIEW] P2. **Confirm the whole chain's exception sets are still empty.** Re-check the three sports
      accepted-exception sets one final time — a backfill that re-introduced non-canonical values would silently undo
      P2's work, and this is the last gate before the chain closes. **Done when**: all three are re-measured empty.
- [ ] [DOC] P2. **Archive `sports_taxonomy_p4_backfill_2026_08_08.md`** via the standard 6-step ritual, including the
      codex-alignment check against the 2020-06 floor SSOT, the corpus-wide referrer-path fixup, and archiving this
      finalize doc alongside it in the same commit. **Done when**: the plan is in `plans/archive/2026_08/`, every
      referrer resolves, and this doc is archived with it.

## Progress Log

- **2026-08-08** — Authored alongside the parent per the finalize-plan-coverage rule.
- **context-scout 2026-08-17**: re-verified context_scope (4 entries), unchanged.
