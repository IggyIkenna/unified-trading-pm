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

- [x] ✅ [REVIEW] P2. **Verify both source-doc todos shipped as specified, then reconcile citations.** —
      unified-trading-pm@9f12d04a8d (issue-doc flip) + independent re-verification this session (slot 21, 2026-08-13).
      Confirmed all three sub-items directly against live code, not the source doc's self-report: (a)
      `scripts/quality-gates-base/base-service.sh` [~L1103-1172] BATS phase detects `bats` on PATH + any `tests/*.bats`
      files (`find tests -name "*.bats"`), runs them, and is WARN-ONLY BY DEFAULT — genuinely mirrors the actionlint
      transitional pattern at [5.5] (both: run if tool present, `log_warn` non-fatal on findings by default, hard-fail
      is an explicit opt-in — actionlint via its own re-harden-after-templates-propagate note, BATS via the
      `BATS_HARD_FAIL` env var checked at L1160). (b) CI-side wiring verified in `unified-trading-ci`
      `.github/workflows/python-quality-gates-v2.yml`: "Install bats-core" (L496-509) + "Add tools to PATH" (L524-525,
      `echo "$HOME/.local/act-tools/bin" >> "$GITHUB_PATH"`) both run before the "Run Quality Gates" step (L862,
      `bash scripts/quality-gates.sh --no-fix`) — bats-core genuinely lands on PATH before the gate that would run it;
      the source doc's premise that CI wiring needed a fix was confirmed stale, no fix was needed there (matches the
      2026-08-09 progress-log finding). (c) Re-harden did NOT flip base-service.sh's shared fleet-wide default (which
      correctly stays WARN-ONLY for every other repo, since only PM's own `.bats` baseline has ever been measured clean)
      — instead PM opted in per-repo via `BATS_HARD_FAIL=1` at `scripts/quality-gates.sh:19`, gated on PM's own suite
      re-measured clean at 0/320 (was 60/229, both root-cause fixtures fixed under
      `pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md` todo G, unified-trading-pm@ef552936b3) BEFORE
      the opt-in, not after — satisfies the "confirmed clean baseline, not before" requirement at PM's own repo scope
      (the todo's own `(repo: unified-trading-pm)` qualifier), not a fleet-wide flip. Both commits independently
      re-verified as ancestors of `origin/live-defi-rollout` this session:
      `git merge-base --is-ancestor d3f7b6497 origin/live-defi-rollout` ✅ and
      `git merge-base --is-ancestor ef552936b3 origin/live-defi-rollout` ✅. **D4-10**:
      `ci_satellite_ao_dispatch_batch4_2026_07_31.md` was archived to
      `plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md` (unified-trading-pm@f005f1f564, prior to
      this session) — its D4-10 row + "Escalated to the operator" question 1 already carry the
      round5-ci-question-resolution RESOLVED annotation (strikethrough + resolution note), and the archival banner names
      D4-10 as "now operator-ruled and independently dispatchable directly in their own source docs." Already correctly
      annotated, not re-opened or re-litigated — no further edit needed there. No contradiction remains between the
      source doc's Todos section (both `[x]`) and its na-eligibility-audit verdict history (round7 RECLASSIFY →
      dispatchable → both todos shipped).

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

- **2026-08-13 (slot 21, review craft)**: Flipped todo 1 — independently re-verified both source-doc todos against live
  code (not the self-report): base-service.sh's BATS phase genuinely mirrors the actionlint warn-only pattern, CI-side
  PATH wiring was already correct (no fix needed), and the re-harden opted PM into `BATS_HARD_FAIL=1` only after its own
  suite was confirmed clean (0/320) — a PM-repo-scoped opt-in per the todo's own `(repo: unified-trading-pm)` qualifier,
  not a fleet-wide base-service.sh default flip. Both commits (`d3f7b6497`, `ef552936b3`) re-verified as ancestors of
  `origin/live-defi-rollout`. D4-10 in the now-archived `ci_satellite_ao_dispatch_batch4_2026_07_31.md` was already
  correctly annotated as resolved prior to this session (`unified-trading-pm@f005f1f564`) — left as-is, not
  re-litigated. Todos 2 (codex doc update) and 3 (archive source doc) remain open for a future dispatch.
