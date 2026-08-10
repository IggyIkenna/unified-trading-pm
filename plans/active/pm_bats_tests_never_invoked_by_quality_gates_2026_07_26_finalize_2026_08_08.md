---
doc_type: plan
title: PM bats-tests-never-invoked — finalize (reconcile + archive)
summary: >-
  Gated closeout for the retroactive reclassification of
  issues/pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md (NA → planning, 2026-08-08 na-eligibility-audit
  round7 RECLASSIFY sweep). Machine-held via depends_on + gate_on_depends: true until both of that doc's own todos (add
  the warn-only BATS phase to base-service.sh, then re-harden to a hard failure) are done. Verifies the shipped commits,
  updates the quality-gates codex doc if the new phase changes its documented gate composition, reconciles
  ci_satellite_ao_dispatch_batch4_2026_07_31.md's D4-10 escalated-question entry, and archives the source doc via the
  standard 6-step ritual once genuinely zero open work remains.
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, bats, shell-tests, quality-gates, ao-dispatch, close-out, reclassification, na-audit]
related:
  [
    /plans/active/issues/pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch6_2026_08_08.md,
    /codex/06-coding-standards/quality-gates.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.3
assigned_role: cicd
effort: high
sequential: true
drift_direction: advance-code
depends_on: [pm_bats_tests_never_invoked_by_quality_gates_2026_07_26]
gate_on_depends: true
source: >-
  Authored alongside the 2026-08-08 na-eligibility-audit round7 RECLASSIFY sweep's flip of
  issues/pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md (NA → planning), per plans/active/task_template.md
  §4's finalize-plan-coverage rule and the retroactive-reclassification naming convention in
  /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md §1(b).
context_scope:
  [
    /plans/active/issues/pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md,
    /codex/06-coding-standards/quality-gates.md,
    scripts/quality-gates-base/base-service.sh,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md,
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
---

# PM bats-tests-never-invoked — finalize

> **🔒 GATED, not draft.** `depends_on: [pm_bats_tests_never_invoked_by_quality_gates_2026_07_26]` +
> `gate_on_depends: true` holds every todo below until both of that doc's own todos (the warn-only BATS phase, then the
> re-harden-to-hard-failure) are `done`. Authored `status: active` (not `draft`) per the established no-double-gate
> precedent used by every other batch/finalize pair in this tranche — the gate mechanism already machine-holds this plan
> regardless of the source doc's own status.

## Todos

- [ ] [REVIEW] P2. **Verify both source-doc todos shipped as specified, then reconcile citations.** Confirm (a) the BATS
      phase in `scripts/quality-gates-base/base-service.sh` detects `bats` on PATH + any `tests/*.bats` files, runs
      them, and is WARN-ONLY on first landing (mirrors the existing actionlint transitional pattern at base-service.sh
      [5.5] — verify it actually mirrors that pattern, not just that a phase exists); (b) the CI-side bats-core install
      step (`.github/actions/setup-python-tools/action.yml`) puts the binary on the same PATH `quality-gates.sh` reads
      inside the job (the source doc's own stated wiring requirement); (c) the re-harden todo only flips WARN → hard
      failure after a confirmed clean fleet-wide baseline, not before. Cite the shipping commit(s) on both of the source
      doc's todos, verified ancestors of `origin/live-defi-rollout` (`git merge-base --is-ancestor`). Then flip
      `ci_satellite_ao_dispatch_batch4_2026_07_31.md`'s D4-10 row to note the escalated plan-destination question
      resolved (cite the 2026-08-08 na-eligibility-audit round7 marker in the source doc) and the work itself shipped —
      do not re-open or re-litigate the authority question there. **Done when**: both commits are cited and verified,
      D4-10 is annotated (not deleted — historical trail), and no contradiction remains between the source doc's Todos
      section and its own na-eligibility-audit verdict history.

- [ ] [DOC] P3. **Update `/codex/06-coding-standards/quality-gates.md` if the new BATS phase changes the documented gate
      composition** (e.g. if quality-gates.md enumerates each check phase quality-gates.sh runs, add the BATS phase in
      its warn-only and, later, hard-fail states; skip this todo with a one-line note if the codex doc is already
      phase-agnostic and needs no edit). **Done when**: either the codex doc is updated and accurate against the shipped
      phase, or a note confirms no update was needed and why.

- [ ] [DOC] P3. **Archive the source doc via the standard 6-step ritual** once todo 1 confirms both its todos are
      genuinely done and no other open item remains in its body: migrate any still-open follow-up to a tracked todo →
      add the archive banner → confirm no other active doc's contract needs updating beyond todo 2 above → grep the
      corpus for every referrer of `pm_bats_tests_never_invoked_by_quality_gates_2026_07_26` and repoint each to the
      archived path → clear `locked_by` (already empty) → move to `plans/archive/2026_08/issues/`. **Done when**: the
      doc is archived, every corpus referrer resolves, and `check_reference_paths.py` has not regressed.

## Codex SSOTs

- `/codex/06-coding-standards/quality-gates.md` — gate composition, warn-only → hard-fail transitional pattern
  (actionlint precedent at `base-service.sh` [5.5])
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — retroactive-reclassification naming
  shape (b) this finalize doc follows

## Progress Log

- **2026-08-08** — Drafted alongside the na-eligibility-audit round7 RECLASSIFY flip of
  `issues/pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md`. Authored `status: active` per the established
  no-double-gate precedent; `gate_on_depends: true` already machine-holds every task here until the source doc's own 2
  todos are done.
