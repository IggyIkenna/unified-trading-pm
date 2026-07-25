---
doc_type: plan
title: Deployment registry Firestore Phase 0 — finalize (reconcile + archive)
summary: >-
  Gated closeout for deployment_registry_firestore_p0_unblock_2026_07_14.md — machine-held via depends_on +
  gate_on_depends: true until all of that plan's todos are done, so this never dispatches early. Phase 0 is
  self-contained (its own checkboxes are the source of truth, not extracted from other docs), so this finalize plan's
  job is narrower than a batch-extraction finalize: confirm the plan's own evidence lines are real (cited commits
  exist), spin off the Resources-column verification follow-up if it surfaces anything, then run the standard archival
  ritual and hand off to Phase 1 (deployment_registry_firestore_migration_2026_07_14.md, the master plan this was carved
  out of).
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [firestore, deployment-registry, observability, close-out, archival]
related:
  [
    /plans/active/deployment_registry_firestore_p0_unblock_2026_07_14.md,
    /plans/active/deployment_registry_firestore_migration_2026_07_14.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.3
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [deployment_registry_firestore_p0_unblock_2026_07_14]
gate_on_depends: true
source: >-
  task_template.md §4 "Every AO-dispatched plan needs a gated finalize plan" (operator ruling 2026-07-24) — Phase 0
  reached assigned_vm: planning with no companion finalize plan; authored to close the coverage gap, mirroring
  sports_closeout_batch1_finalize_2026_07_24.md's pattern for a self-contained (non-extraction) plan.
assigned_role: infra
sequential: true
drift_direction: advance-code
---

# Deployment registry Firestore Phase 0 — finalize

> **Machine-gated on `deployment_registry_firestore_p0_unblock_2026_07_14.md`** (`depends_on` + `gate_on_depends: true`)
> — the dispatcher will not queue any todo below until every task in that plan is `done`. `sequential: true` because
> todo 2 (archival) must run after todo 1 (evidence reconciliation) confirms there is nothing left dangling.

## Todos

- [ ] [REVIEW] P1. **Reconcile Phase 0's own evidence lines.** Phase 0 is self-contained (its checkboxes ARE the source
      of truth, not extracted from other docs), so this is a verification pass, not a cross-doc reconciliation: for each
      `- [x]` todo, confirm the cited `<repo>@<sha>` actually exists (`git log`/`git show`, don't trust the citation
      blindly) and that any evidence claiming a live-verified outcome (e.g. the dual-write parity diff, the Cloud Run
      env-var flip) is independently re-checkable from the Progress Log detail, not just asserted. Flag any todo whose
      evidence doesn't hold up as a new follow-up todo rather than silently re-flipping it. **Done when**: every `[x]`
      todo's citation is confirmed real, and any gaps found are tracked as new todos (not silently dropped).
- [ ] [REVIEW] P2. **Check whether the Resources-column live-verification todo surfaced new work.** Phase 0's last open
      todo at authoring time was "[REVIEW] P2. Verify against the DEPLOYED API with REAL (non-mock) data — confirm the
      inline Resources column..." — read its outcome; if it found the column still doesn't populate end-to-end against
      real data, that is itself a new tracked gap (spin off a small follow-up todo/plan), not something to close
      silently. **Done when**: the verification's actual outcome is read, and either confirmed clean or a new follow-up
      todo is filed for whatever it found.
- [ ] [DOC] P2. **Archive `deployment_registry_firestore_p0_unblock_2026_07_14.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any DEFERRED items to a tracked todo elsewhere → add the archive banner →
      run the codex-alignment check (does `/codex/05-infrastructure/deployment-observability.md` need a status update
      now that the reaper scheduling + SIGTERM handler + dual-write rollout shipped) → update CLAUDE.md/codex if any new
      durable contract resulted → grep the corpus for every referrer of
      `deployment_registry_firestore_p0_unblock_2026_07_14` (including this doc's own `depends_on` self-reference and
      `deployment_registry_firestore_migration_2026_07_14.md`'s Phase-0 pointer) and fix each path to the archived
      location → clear `locked_by` (already empty here, confirm). **Done when**: the plan is moved to
      `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this finalize doc itself gets
      archived alongside it in the same commit (nothing left for it to gate once Phase 0 is archived).
