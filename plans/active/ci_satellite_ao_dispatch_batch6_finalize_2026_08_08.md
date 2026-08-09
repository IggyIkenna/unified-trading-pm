---
doc_type: plan
title: CI satellite AO batch 6 — finalize (reconcile source docs, re-check deferrals, archive)
summary: >-
  Gated closeout for ci_satellite_ao_dispatch_batch6_2026_08_08.md — machine-held via depends_on + gate_on_depends: true
  until all 12 of that plan's todos are done. Reconciles each distinct source doc's checkboxes/prose independently,
  re-checks the Deferred items (D6-1 through D6-29) for whether their blocker has cleared, flips the 2 confirmed
  stale-checkbox items in github_actions_operator_gated_followups_2026_07_17.md and
  post_cutover_silent_assumption_sweep_2026_07_23.md that batch6's own Phase 1 audit found already-done-but-unflipped,
  and archives batch 6 via the standard 6-step ritual.
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci, cicd, ao-dispatch, close-out, batch-6, satellite-docs, archival]
related:
  [
    /plans/active/ci_satellite_ao_dispatch_batch6_2026_08_08.md,
    /plans/active/ci_satellite_ao_dispatch_batch5_2026_08_02.md,
    /plans/active/ci_satellite_ao_dispatch_batch4_2026_07_31.md,
    /plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.9
estimate_calibrated_ai_days: 0.7
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ci_satellite_ao_dispatch_batch6_2026_08_08]
gate_on_depends: true
source: >-
  Authored alongside `ci_satellite_ao_dispatch_batch6_2026_08_08.md` per `plans/active/task_template.md` §4's
  finalize-plan-coverage rule. Authored `status: active` (not `draft`) per the established 2026-07-30 no-double-gate
  finding (batch4/batch5's finalize plans record the same): `gate_on_depends: true` already machine-holds every task
  here until the batch's own todos are `done`, including while the batch is still `draft` (via the derived
  `gate-upstream-open:<stem>` condition).
assigned_role: cicd
effort: high
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/ci_satellite_ao_dispatch_batch6_2026_08_08.md,
    /codex/06-coding-standards/quality-gates.md,
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/task_template.md,
  ]
---

# CI satellite AO batch 6 — finalize

> **🔒 GATED, not draft.** `depends_on: [ci_satellite_ao_dispatch_batch6_2026_08_08]` + `gate_on_depends: true` holds
> every todo below until all 12 of batch6's own todos are `done` — this applies whether batch6 is still `status: draft`
> or has been flipped `active`. No separate flip is needed for THIS doc. `sequential: true` because todo 2's
> reconciliation needs todo 1's verification current, and todo 3 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile all 12 batch-6 todos' source docs.** Each batch-6 todo ends with `Source:` naming a doc.
      For each: flip the corresponding checkbox or annotate the corresponding prose section, citing the batch-6 commit
      that shipped it — **verify the cited commit exists and is an ancestor of `origin/live-defi-rollout` before citing
      it** (`git merge-base --is-ancestor`). **Also flip the 2 confirmed-already-done-but-unflipped stale checkboxes
      batch6's own Phase 1 audit surfaced** (see D6-8, D6-9 in batch6's Deferred table): the ldr-docs-gate-firing
      verification + the codex staging-re-entry item in `github_actions_operator_gated_followups_2026_07_17.md` (both
      closed by `unified-trading-pm@97970974e` and a batch1 [VERIFY] P2 todo, 2026-07-26 — verify the ancestor
      relationship before flipping, do not trust the citation blind), and the F3
      `cascade-qg-ordering.yml`/`sit-gate.yml` success-reporting item in
      `post_cutover_silent_assumption_sweep_2026_07_23.md` (closed by batch5's `[INFRA] P2` todo, 2026-08-07 — same
      ancestor-verify-first rule). Then, per doc, re-check whether it now has zero open work **in checkbox AND prose
      form**; only set `status: resolved` on a doc that genuinely reaches zero. **Done when**: every cited doc (batch-6
      sources plus the 2 stale-checkbox docs above) is flipped/annotated with verified evidence, and each doc that
      genuinely reaches zero open work is `status: resolved`.
- [ ] [REVIEW] P1. **Re-check the Deferred items D6-1 through D6-29 for whether their blocker has cleared.** D6-1/D6-2
      (the two parked `scripts/workflow-templates/` claims) — has todo 9 landed, freeing the mechanism? If so both are
      ready-for-batch-7 extraction; note it, do NOT draft it here. D6-3 — has batch4's todo 1 landed
      (`scripts/quickmerge.sh` freed)? D6-4 through D6-14 (operator-gated) — has any received a ruling since 2026-08-08?
      D6-15 through D6-19 (time-gated/live-incident) — has the incident's own Progress Log shown resolution, or has the
      stated elapsed-time gate passed? D6-20 through D6-22 (needs-re-scoping) — has anyone supplied the missing scope
      decision? D6-23 through D6-29 (too-large/human-only) — unchanged confirmation only. **Done when**: each of D6-1
      through D6-29 has either (a) a note that it is ready for batch-7 extraction because its blocker cleared, or (b) a
      re-verified confirmation the blocker is still open. Do NOT draft follow-up todos here — this plan's scope is
      reconciliation, not fresh drafting.
- [ ] [DOC] P1. **Archive `ci_satellite_ao_dispatch_batch6_2026_08_08.md`** via the standard 6-step ritual (CLAUDE.md §
      plan archival): migrate any still-unresolved Deferred item to a tracked follow-up (todo 2 above should have
      re-confirmed D6-1 through D6-29 — verify none silently vanishes) → add the archive banner → run the
      codex-alignment check (confirm `/codex/08-workflows/ci-cd-flow.md` and `/codex/04-architecture/ci-alerting.md`
      reflect any new contract this batch's todos established, e.g. the escalation-dispatch cooldown guard in todo 6) →
      update CLAUDE.md/codex if warranted → grep the corpus for every referrer of
      `ci_satellite_ao_dispatch_batch6_2026_08_08` and repoint each to the archived path → clear `locked_by` (already
      empty; confirm). **Done when**: the plan is in `plans/archive/2026_08/`, every corpus referrer resolves,
      `check_reference_paths.py` has not regressed, and this finalize doc is archived alongside it in the same commit.

## Codex SSOTs

- `/codex/06-coding-standards/quality-gates.md` — how the gate composes
- `/codex/08-workflows/ci-cd-flow.md` — the pipeline contracts several batch-6 todos touch
- `/codex/04-architecture/ci-alerting.md` — the dedup/recovery-bookend contract todos 3, 4, 6 establish or extend
- `/codex/11-project-management/` — archival ritual, issue-doc lifecycle
- `plans/active/task_template.md` §4 — the finalize-plan-coverage rule this plan satisfies

## Progress Log

- **2026-08-08** — Drafted alongside `ci_satellite_ao_dispatch_batch6_2026_08_08.md`. Authored `status: active` per the
  established no-double-gate precedent (batch4/batch5's finalize plans record the same reasoning); batch6 itself remains
  `status: draft` pending the operator's flip.
