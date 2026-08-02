---
doc_type: plan
title: CI satellite AO batch 5 — finalize (reconcile source docs, re-check deferrals, archive)
summary: >-
  Gated closeout for ci_satellite_ao_dispatch_batch5_2026_08_02.md — machine-held via depends_on + gate_on_depends: true
  until all 6 of that plan's todos are done. Reconciles each distinct source doc's checkboxes/prose independently,
  re-checks the Deferred items (D5-1 through D5-7) for whether their blocker has cleared, and archives batch 5 via the
  standard 6-step ritual. Carries one batch-specific check the batch itself cannot contain: confirming the cloudbuild
  drift baseline was ratcheted DOWN (never up) by todo 1's two-step rollout.
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci, cicd, ao-dispatch, close-out, batch-5, satellite-docs, archival]
related:
  [
    /plans/active/ci_satellite_ao_dispatch_batch5_2026_08_02.md,
    /plans/active/ci_satellite_ao_dispatch_batch4_2026_07_31.md,
    /plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: "2026-08-02"
last_updated: "2026-08-02"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.6
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ci_satellite_ao_dispatch_batch5_2026_08_02]
gate_on_depends: true
source: >-
  Authored alongside `ci_satellite_ao_dispatch_batch5_2026_08_02.md` per `plans/active/task_template.md` §4's
  finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan, mirroring the
  batch1/batch2/batch4 precedent. Authored `status: active` (not `draft`) per the same 2026-07-30 no-double-gate finding
  batch4's finalize records: `gate_on_depends: true` already machine-holds every task here until the batch's own todos
  are `done`, including while the batch is still `draft` (via the derived `gate-upstream-open:<stem>` condition).
assigned_role: cicd
sequential: true
drift_direction: advance-code
---

# CI satellite AO batch 5 — finalize

> **🔒 GATED, not draft.** `depends_on: [ci_satellite_ao_dispatch_batch5_2026_08_02]` + `gate_on_depends: true` holds
> every todo below until all 6 of batch5's own todos are `done` — this applies whether batch5 is still `status: draft`
> (via the derived `gate-upstream-open:` condition) or has been flipped `active`. No separate flip is needed for THIS
> doc. `sequential: true` because todo 2's reconciliation cites todo 1's verification, todo 3 needs both, and todo 4
> (archival) must run last.

## Todos

- [ ] [VERIFY] P1. **Confirm todo 1's cloudbuild rollout ratcheted the drift baseline DOWN, never up, and left no
      consumer un-guarded.** This is the one check the batch itself structurally cannot make: todo 1 touches 15 repos
      across two ordered steps, so only a post-hoc pass can see the whole result. Re-run
      `.venv/bin/python scripts/quality_gates/check_cloudbuild_template_drift.py --show` and diff it against
      `scripts/quality_gates/cloudbuild_template_drift_baseline.yaml`: every count must be ≤ its 2026-07-28 seed, the
      residual non-zero counts must each map to a category-(b) "intentional permanent divergence" entry recorded in todo
      1's classification, and no repo may have been added at a NEW non-zero count. Then grep every one of the 19
      consumers' committed `cloudbuild.yaml` for the empty-tag guard and list any that lack it. **Done when**: the
      baseline diff is recorded with a per-repo before/after table, every residual is justified, and either all 19
      consumers carry the guard or the exceptions are named with reasons.
- [ ] [REVIEW] P1. **Reconcile all 6 batch-5 todos' source docs.** Each batch-5 todo ends with `Source:` naming one or
      more docs (todos 3 and 4 cite two distinct items in the SAME doc — flip them independently, not as one). For each:
      flip the corresponding checkbox or annotate the corresponding prose section in EVERY cited doc, citing the batch-5
      commit that shipped it — **verify the cited commit exists and is an ancestor of `origin/live-defi-rollout` before
      citing it** (`git merge-base --is-ancestor`). Then, per doc, re-check whether it now has zero open work **in
      checkbox AND prose form**; only set `status: resolved` on a doc that genuinely reaches zero. Note that
      `post_cutover_silent_assumption_sweep_2026_07_23.md` will NOT reach zero (its superseded/time-gated set stays open
      by design) and that `github_actions_operator_gated_followups_2026_07_17.md` may be concurrently edited by batch4's
      todo 9 — re-pull before writing. **Done when**: every cited doc is flipped/annotated with verified evidence, and
      each doc that genuinely reaches zero open work is `status: resolved`.
- [ ] [REVIEW] P1. **Re-check the Deferred items D5-1 through D5-7 for whether their blocker has cleared.** D5-1
      (quickmerge.sh branch-check broadening) — have BOTH batch4 todo 1 and batch4 todo 2 landed? If so it is
      ready-for-batch-6 extraction; note it, do NOT draft it here. D5-2/D5-3 (F3's semver-agent and cloudbuild halves) —
      are the workflow-template rollout mechanism and the consumer `cloudbuild.yaml` files free again (batch-5 todos 4
      and 1 landed)? If so both are ready-for-batch-6. D5-4 — has the operator ruled on the billing-token fork? D5-5 —
      confirm batch4 is still the live home for D4-5..D4-18 and none has silently vanished. D5-6 — has
      `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` left `status: open`? D5-7 — has the pnpm migration
      been given its own plan? **Done when**: each of D5-1 through D5-7 has either (a) a note that it is ready for
      batch-6 extraction because its blocker cleared, or (b) a re-verified confirmation the blocker is still open. Do
      NOT draft follow-up todos here — this plan's scope is reconciliation, not fresh drafting.
- [ ] [DOC] P1. **Archive `ci_satellite_ao_dispatch_batch5_2026_08_02.md`** via the standard 6-step ritual (CLAUDE.md §
      plan archival): migrate any still-unresolved Deferred item to a tracked follow-up (todo 3 above should have
      re-confirmed D5-1 through D5-7 — verify none silently vanishes) → add the archive banner → run the codex-alignment
      check (todo 1 changes the cloudbuild template contract and todo 4 changes the `quality-gates-v2` CI-status
      dispatch contract; confirm `/codex/08-workflows/ci-cd-flow.md` reflects both, and that the two-step "resolve
      drift, then roll out" procedure is captured as a durable contract rather than living only in this batch) → update
      CLAUDE.md/codex if any batch-5 todo established a new contract → grep the corpus for every referrer of
      `ci_satellite_ao_dispatch_batch5_2026_08_02` and repoint each to the archived path → clear `locked_by` (already
      empty; confirm). **Done when**: the plan is in `plans/archive/2026_08/`, every corpus referrer resolves,
      `check_reference_paths.py` has not regressed, and this finalize doc is archived alongside it in the same commit.

## Codex SSOTs

- `/codex/06-coding-standards/quality-gates.md` — how the gate composes; the shrinking-ratchet baseline convention todo
  1 above verifies
- `/codex/08-workflows/ci-cd-flow.md` — the pipeline contracts batch-5 todos 1 and 4 touch
- `/codex/11-project-management/` — archival ritual, issue-doc lifecycle
- `plans/active/task_template.md` §4 — the finalize-plan-coverage rule this plan satisfies

## Progress Log

- **2026-08-02** — Drafted alongside `ci_satellite_ao_dispatch_batch5_2026_08_02.md`. Authored `status: active` per the
  no-double-gate precedent batch4's finalize records; batch5 itself remains `status: draft` pending the operator's flip.
  Todo 1 exists because batch-5's todo 1 spans 15 repos in two ordered steps, so whether the drift baseline actually
  ratcheted DOWN is only observable after the whole batch lands — the same partial-parallelism remedy batch1's finalize
  used for its three-checker registration commit.
