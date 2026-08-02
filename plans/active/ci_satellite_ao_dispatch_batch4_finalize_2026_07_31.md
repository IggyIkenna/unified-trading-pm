---
doc_type: plan
title: CI satellite AO batch 4 — finalize (reconcile source docs, re-check deferrals, archive)
summary: >-
  Gated closeout for ci_satellite_ao_dispatch_batch4_2026_07_31.md — machine-held via depends_on + gate_on_depends: true
  until all 9 of that plan's todos are done. Reconciles each distinct source doc's checkboxes/prose independently,
  re-checks the Deferred items (D4-1 through D4-20) for whether their blocker has cleared, and archives batch 4 via the
  standard 6-step ritual.
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci, cicd, ao-dispatch, close-out, batch-4, satellite-docs, archival]
related:
  [
    /plans/active/ci_satellite_ao_dispatch_batch4_2026_07_31.md,
    /plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_2026_07_29.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: "2026-07-31"
last_updated: "2026-07-31"
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
depends_on: [ci_satellite_ao_dispatch_batch4_2026_07_31]
gate_on_depends: true
source: >-
  `/ag-closeout-audit ci` run 2026-07-31, per `plans/active/task_template.md` §4's finalize-plan-coverage rule — every
  AO-dispatched plan needs a companion gated finalize plan, mirroring the batch1/batch2 precedent. Authored `status:
  active` (not `draft`) per the skill's 2026-07-30 finding: `gate_on_depends: true` already machine-holds every task
  here until the batch's own todos are `done` (via `_wire_gate_on_depends_prereqs`, which covers a still-draft batch too
  via a derived `gate-upstream-open:<stem>` condition read off the batch file's own checkboxes) — stacking `status:
  draft` on top is a redundant second gate that requires a separate manual flip nobody reliably remembers.
assigned_role: cicd
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/ci_satellite_ao_dispatch_batch4_2026_07_31.md,
    /codex/06-coding-standards/quality-gates.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/08-workflows/deployment-flow.md,
    /codex/04-architecture/ci-alerting.md,
    /plans/active/task_template.md,
  ]
---

# CI satellite AO batch 4 — finalize

> **🔒 GATED, not draft.** `depends_on: [ci_satellite_ao_dispatch_batch4_2026_07_31]` + `gate_on_depends: true` holds
> every todo below until all 9 of batch4's own todos are `done` — this applies whether batch4 is still `status: draft`
> (via the derived `gate-upstream-open:` condition) or has been flipped `active` by the operator (via
> `prereqs.completed_tasks`). No separate flip is needed for THIS doc; it is correctly `status: active` from authoring.
> `sequential: true` because todo 1 must land before todo 2's reconciliation cites it, todo 3 needs both, and todo 4
> (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile all 9 batch-4 todos' source docs.** Each batch-4 todo ends with `Source:` naming one or
      more docs (todo 1 cites two, todo 9 cites one doc's 4 distinct items). For each: flip the corresponding checkbox
      or annotate the corresponding prose section in EVERY cited doc, citing the batch-4 commit that shipped it —
      **verify the cited commit exists and is an ancestor of `origin/live-defi-rollout` before citing it**
      (`git merge-base --is-ancestor`). Then, per doc, re-check whether it now has zero open work **in checkbox AND
      prose form**. Only set `status: resolved` on a doc that genuinely reaches zero — note that several source docs
      (e.g. `stale_staging_versions_manifest_2026_07_23.md`, `qg_sentinel_environment_blind_2026_07_23.md`) carry a
      documented FALSE-CHECKED-checkbox trap; re-verify against live code/state, not just the checkbox glyph, before
      concluding zero-open. **Done when**: every cited doc is flipped/annotated with verified evidence, and each doc
      that genuinely reaches zero open work is `status: resolved`.
- [ ] [REVIEW] P1. **Re-check the conflict-gated Deferred items (D4-1 through D4-4) for whether their blocker has
      cleared.** D4-1 (quickmerge.sh branch-check broadening) — is `scripts/quickmerge.sh` free again (batch-4 todo 1
      landed) AND has batch-4 todo 2's step-2 alias fix landed? If both, D4-1 is ready-for-batch-5 extraction — note it,
      do NOT draft it here. D4-2/D4-3 (the test-impact design-scoping todo + BigQuery verification, both deferred
      because `github_actions_operator_gated_followups_2026_07_17.md` was already claimed by todo 9's sweep) — is that
      file free again (todo 9 landed)? If so, both are ready-for-batch-5, note and do not draft. D4-4
      (`sit_validated_tree_treadmill`'s stuck-gate monitor) — confirm it is still exactly batch1's own still-open todo
      and no new doc has claimed it since. **Done when**: each of D4-1 through D4-4 has either (a) a note that it is
      ready for batch-5 extraction because its blocker cleared, or (b) a re-verified confirmation the blocker is still
      open. Do NOT draft follow-up todos here — this plan's scope is reconciliation, not fresh drafting.
- [ ] [REVIEW] P2. **Re-verify the operator-gated (D4-5 through D4-18), live-incident (D4-19), and needs-re-scoping
      (D4-20) Deferred items have not silently changed state.** In particular: has the operator ruled on D4-10 (the
      `pm_bats_tests` base-service.sh plan-destination question, escalated below)? Has
      `github_actions_billing_wall_recurrence_2026_07_29.md` (D4-19) self-resolved or been operator-closed since
      2026-07-31 — if so, note it is ready for a future batch's fresh triage of its 3 remaining bounded items (2-4), do
      NOT draft them here even if it has resolved. Has `aws_codebuild_terraform_import_pending_2026_07_22.md`'s D1-D4
      rulings table (D4-6) received an answer? For every other item (D4-5, D4-7 through D4-9, D4-11 through D4-18,
      D4-20): confirm no new doc has claimed them and no operator ruling has landed that would newly unblock them.
      **Done when**: each is re-confirmed still in its recorded state, or flagged if changed (flag only — do not
      draft/dispatch a follow-up from this reconciliation todo).
- [ ] [DOC] P1. **Archive `ci_satellite_ao_dispatch_batch4_2026_07_31.md`** via the standard 6-step ritual (CLAUDE.md §
      plan archival): migrate any still-unresolved Deferred item to a tracked follow-up (todos 2-3 above should have
      re-confirmed D4-1 through D4-20 — verify none silently vanishes) → add the archive banner → run the
      codex-alignment check (todo 3's `deployment-flow.md` rewrite and todo 1's `ci-cd-flow.md`/ `per-tab-worktrees.md`
      referrer repoints changed durable contracts — confirm those landings are reflected and no NEW undocumented
      contract exists, e.g. the STAGE 1.6 dormancy-aware dep-gate behavior, the `UnifiedCloudServicesConfig`
      alias-precedence fix, the MTDS auto-merge-arm fix) → update CLAUDE.md/codex if any batch-4 todo established a new
      contract → grep the corpus for every referrer of `ci_satellite_ao_dispatch_batch4_2026_07_31` and repoint each to
      the archived path → clear `locked_by` (already empty; confirm). **Done when**: the plan is in
      `plans/archive/2026_07/`, every corpus referrer resolves, `check_reference_paths.py` has not regressed, and this
      finalize doc is archived alongside it in the same commit.

## Codex SSOTs

- `/codex/06-coding-standards/quality-gates.md` — how the gate composes; ratchet-baseline convention
- `/codex/08-workflows/ci-cd-flow.md` + `/codex/08-workflows/deployment-flow.md` — the pipeline contracts batch-4 todos
  1/3 touch
- `/codex/04-architecture/ci-alerting.md` — the `notify-slack.yml` carrier pattern batch-4 todo 8 uses
- `/codex/11-project-management/` — archival ritual, issue-doc lifecycle
- `plans/active/task_template.md` §4 — the finalize-plan-coverage rule this plan satisfies

## Progress Log

- **2026-07-31** — Drafted alongside `ci_satellite_ao_dispatch_batch4_2026_07_31.md` by `/ag-closeout-audit ci`
  (autonomous mode, `ag_closeout_auditor` scheduled worker, slot 12). Authored `status: active` per the skill's
  2026-07-30 no-double-gate finding — `gate_on_depends: true` alone correctly holds every todo above until batch4's own
  todos are done; batch4 itself remains `status: draft` pending operator approval.
- **context-scout 2026-08-01**: populated/refreshed context_scope (6 entries).
