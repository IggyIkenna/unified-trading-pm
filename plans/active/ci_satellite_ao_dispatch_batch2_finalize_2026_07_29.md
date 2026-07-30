---
doc_type: plan
title: CI satellite AO batch 2 — finalize (reconcile source docs, re-check deferrals, archive)
summary: >-
  Gated closeout for ci_satellite_ao_dispatch_batch2_2026_07_29.md — machine-held via depends_on + gate_on_depends: true
  until all 14 of that plan's todos are done. Reconciles each distinct source doc's checkboxes/prose independently,
  re-checks the file-contention Deferred items (E1-E5) for whether the file they were rationed away from is free again,
  re-verifies the operator-gated/role-mismatch/too-large items (E6-E14) for any state change, and archives batch 2 via
  the standard 6-step ritual.
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci, cicd, ao-dispatch, close-out, batch-2, satellite-docs, archival]
related:
  [
    /plans/active/ci_satellite_ao_dispatch_batch2_2026_07_29.md,
    /plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: "2026-07-29"
last_updated: "2026-07-30"
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
depends_on: [ci_satellite_ao_dispatch_batch2_2026_07_29]
gate_on_depends: true
source: >-
  `/ag-closeout-audit ci` run 2026-07-29, per `plans/active/task_template.md` §4's finalize-plan-coverage rule — every
  AO-dispatched plan needs a companion gated finalize plan, mirroring the batch1 precedent.
assigned_role: cicd
sequential: true
drift_direction: advance-code
---

# CI satellite AO batch 2 — finalize

> **⚠️ STATUS: `draft` — NOT dispatched.** Flips to `active` only with the batch it gates, on explicit operator
> approval. Drafted 2026-07-29 as part of a scheduled autonomous `/ag-closeout-audit ci` run.

> **Machine-gated on `ci_satellite_ao_dispatch_batch2_2026_07_29.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue anything below until all 14 of that plan's todos are `done`. `sequential: true` because todo
> 1 must land before todo 2's reconciliation cites it, todo 3 needs both, and todo 4 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile all 14 batch-2 todos' source docs.** Each batch-2 todo ends with `Source:` naming one or
      more docs (todo 1 cites two, todo 6 cites one 7-todo doc, several cite a single doc's multiple items). For each:
      flip the corresponding checkbox or annotate the corresponding prose section in EVERY cited doc, citing the batch-2
      commit that shipped it — **verify the cited commit exists and is an ancestor of `origin/live-defi-rollout` before
      citing it** (`git merge-base --is-ancestor`). Then, per doc, re-check whether it now has zero open work **in
      checkbox AND prose form**. Only set `status: resolved` on a doc that genuinely reaches zero. **Done when**: every
      cited doc is flipped/annotated with verified evidence, and each doc that genuinely reaches zero open work is
      `status: resolved`.
- [ ] [REVIEW] P1. **Re-check the 5 file-contention Deferred items (E1-E5) and re-verify E9-E10 (still-open F4 items).**
      Each names the specific file/blocker it collided with, so this is a few greps and reads, not fresh investigation.
      In particular: is `scripts/quality-gates-base/base-service.sh` free again (batch-2 todo 1 landed)? If so, E1
      (`pm_bats_tests`' BATS phase) and the `--durations=25`/`base-library.sh` half of E2 are both unblocked as FILES —
      note each as ready-for-batch-3 extraction. Is `scripts/quickmerge.sh` free again? If so, E3 (STAGE 1.6 dormancy
      gate) and E4 (delete redundant pre-push hook) are both unblocked as FILES, in that priority order (E4 is P3/fully
      conflict-cleared already — E3 is P2 with an operator-confirmed ruling behind it; note the file contention between
      them for batch-3's own conflict-check to resolve). For E9/E10 (F4 crons/digest-drift-sweep): has the operator
      ruled since 2026-07-29? **Do NOT draft the follow-up todos here** — this plan's scope is reconciliation, not fresh
      drafting; note each as ready-for-batch-3 instead. Do NOT re-ask an operator question that was already escalated
      (E6, E8, E14); just record whether it has been answered. **Done when**: each of E1-E5, E9, E10 has either (a) a
      note that it is ready for batch-3 extraction because its file/blocker cleared, or (b) a re-verified confirmation
      the contention/gate is still open.
- [ ] [REVIEW] P2. **Re-verify E7 and E11-E13 have not silently changed state.** E7 (MTDS DEPLOYMENT_ENV leak,
      duplicate-gated on the sibling race doc's cascade-instrumentation step) — has that sibling doc's blocking step run
      yet? E11 (dirty-deps carve-out sibling docs) — still out of batch-2 todo 5's narrow scope, confirm no new doc has
      claimed them. E12/E13 (role-mismatch, UI-touching) — still waiting on a `[UI]`-capable slot cycle; no action
      needed here beyond confirming they have not been separately picked up. **Done when**: each is re-confirmed still
      in its recorded state, or flagged if changed.
- [ ] [DOC] P1. **Archive `ci_satellite_ao_dispatch_batch2_2026_07_29.md`** via the standard 6-step ritual (CLAUDE.md §
      plan archival): migrate any still-unresolved Deferred item to a tracked follow-up (todos 2-3 above should have
      resolved or re-confirmed E1-E14 — verify none silently vanishes) → add the archive banner → run the
      codex-alignment check (todo 1 above changed `/codex/08-workflows/ci-cd-flow.md` — confirm that landing is
      reflected and no NEW durable contract is undocumented, e.g. the QG sentinel's configuration-binding behavior, the
      new PYTEST_UNIT_DIR fleet-sweep checker) → update CLAUDE.md/codex if any batch-2 todo established a new contract →
      grep the corpus for every referrer of `ci_satellite_ao_dispatch_batch2_2026_07_29` and repoint each to the
      archived path → clear `locked_by` (already empty; confirm). **Done when**: the plan is in
      `plans/archive/2026_07/`, every corpus referrer resolves, `check_reference_paths.py` has not regressed, and this
      finalize doc is archived alongside it in the same commit.

## Codex SSOTs

- `/codex/06-coding-standards/quality-gates.md` — how the gate composes; ratchet-baseline convention
- `/codex/08-workflows/ci-cd-flow.md` — the pipeline contract batch-2 todo 1/2 touch
- `/codex/11-project-management/` — archival ritual, issue-doc lifecycle
- `plans/active/task_template.md` §4 — the finalize-plan-coverage rule this plan satisfies

## Progress Log

- **2026-07-29** — Drafted alongside `ci_satellite_ao_dispatch_batch2_2026_07_29.md` by `/ag-closeout-audit ci`
  (autonomous mode, `ag_closeout_auditor` scheduled worker, slot 7). Both are `status: draft`; neither is dispatched.
