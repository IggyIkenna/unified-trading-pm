---
doc_type: plan
title: CI satellite AO batch 1 — finalize (wire the new QG checkers, reconcile source docs, re-check deferrals, archive)
summary: >-
  Gated closeout for ci_satellite_ao_dispatch_batch1_2026_07_26.md — machine-held via depends_on + gate_on_depends: true
  until all 29 of that plan's todos are done. Carries the ONE piece of work the batch deliberately could not contain:
  the single PM `scripts/quality-gates.sh` registration commit for the three new checkers batch-1 todos 2, 6 and 7
  deliver as standalone files (three concurrent todos cannot share that file). Then reconciles each distinct source
  doc's checkboxes/prose independently, re-checks the 6 conflict-gated Deferred items for any whose competing claim has
  since cleared, and archives batch 1 via the standard 6-step ritual.
status: draft
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci, cicd, ao-dispatch, close-out, batch-1, satellite-docs, archival]
related:
  [
    /plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
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
depends_on: [ci_satellite_ao_dispatch_batch1_2026_07_26]
gate_on_depends: true
source: >-
  `/ag-closeout-audit ci` run 2026-07-26, per `plans/active/task_template.md` §4's finalize-plan-coverage rule — every
  AO-dispatched plan needs a companion gated finalize plan, mirroring the sports/defi/cefi batch precedent.
assigned_role: cicd
sequential: true
drift_direction: advance-code
---

# CI satellite AO batch 1 — finalize

> **⚠️ STATUS: `draft` — NOT dispatched.** Flips to `active` only with the batch it gates, on explicit operator
> approval. Drafted 2026-07-26 while the operator was unreachable.

> **Machine-gated on `ci_satellite_ao_dispatch_batch1_2026_07_26.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue anything below until all 29 of that plan's todos are `done`. `sequential: true` because todo
> 1 must land before todo 2's reconciliation cites it, todo 3 needs both, and todo 4 (archival) must run last.

## Todos

- [ ] [INFRA] P1. **Register the three new QG checkers into PM `scripts/quality-gates.sh` in ONE commit.** Batch-1 todos
      2, 6 and 7 each deliver a standalone checker plus a proven red/green run but deliberately do NOT wire in — three
      concurrent todos cannot share one file (CLAUDE.md § Plans: concurrent same-priority todos must touch different
      files). Add all three invocations here: `check_dispatch_listeners.py` (every dispatched `event_type` has a
      listener in the resolved target repo), `check_cloudbuild_template_drift.py` (rendered template vs each consumer's
      committed `cloudbuild.yaml`), `check_no_swallowed_credential_fetch.py` (no `2>/dev/null || true` around a
      credential fetch). Each must be **baseline-ratcheted** (fails only on NEW violations, per the
      `doc_reference_baseline.yaml` / `defi_address_citation_baseline.yaml` convention) so the gate does not turn red on
      day-one pre-existing debt. **Done when**: `bash scripts/quality-gates.sh --no-fix` on PM is GREEN with all three
      wired, each checker is proven to fail the gate on a synthetic new violation, and the three baselines are
      committed.
- [ ] [REVIEW] P1. **Reconcile all 29 todos' source docs.** Each batch-1 todo ends with `Source:` naming one or more
      docs (five todos cite two sources each — the `check_strict_quickmerge` pair, the `full-workspace-sit` pair, the
      cloudbuild-template pair, the fleet version/tag census pair, and the codex `ci-cd-flow.md` todo which cites FOUR).
      For each: flip the corresponding checkbox or annotate the corresponding prose section in EVERY cited doc, citing
      the batch-1 commit that shipped it — **verify the cited commit exists and is an ancestor of
      `origin/live-defi-rollout` before citing it** (`git merge-base --is-ancestor`). Then, per doc, re-check whether it
      now has zero open work **in checkbox AND prose form** — 12 of this tranche's orphans express all their remaining
      work as numbered prose with no checkboxes, so a checkbox count is not an answer. Only set `status: resolved` on a
      doc that genuinely reaches zero. **Done when**: every cited doc is flipped/annotated with verified evidence, and
      each doc that genuinely reaches zero open work is `status: resolved`.
- [ ] [REVIEW] P1. **Re-check the 6 conflict-gated Deferred items (D1-D6) and the 2 time-gated ones (D29-D30).** Each
      names the specific competing claim it collided with, so this is a few greps and reads, not fresh investigation. D1
      is discharged by todo 1 above. For D2-D6: has the competing side shipped, been superseded, or been ruled on? In
      particular D3's five held `scripts/quickmerge.sh` claims are now unblocked as a FILE (batch-1 todo 1 has landed) —
      re-extract them one per subsequent batch in the order D3 lists, and check whether the parked operator questions on
      D3(2)/D3(3) have been answered. For D29: the two-week billing re-pull's earliest date was ~2026-07-31 — if that
      has passed, it is now extractable. **Do NOT draft the follow-up todos here** — this plan's scope is
      reconciliation, not fresh drafting; note each as ready-for-batch-2 instead. Do NOT re-ask an operator question
      that was already escalated; just record that the re-check happened and it is still unanswered. **Done when**: each
      of D1-D6 and D29-D30 has either (a) a note that it is ready for batch-2 extraction because its blocker cleared, or
      (b) a re-verified confirmation the conflict/date is still open.
- [ ] [DOC] P1. **Archive `ci_satellite_ao_dispatch_batch1_2026_07_26.md`** via the standard 6-step ritual (CLAUDE.md §
      plan archival): migrate any still-unresolved Deferred item to a tracked todo elsewhere (todo 3 above should have
      resolved or re-confirmed D1-D6/D29-D30 — verify none silently vanishes, and confirm the 27 operator-gated /
      human-only entries D7-D28 and D31-D33 each still have a live home) → add the archive banner → run the
      codex-alignment check (batch-1 todo 17 changed `/codex/08-workflows/ci-cd-flow.md`, so confirm that landing is
      reflected and no NEW durable contract is undocumented) → update CLAUDE.md/codex if any batch-1 todo established a
      new contract (candidates: the three new QG checkers from todo 1, and the glue-pool liveness alarm) → grep the
      corpus for every referrer of `ci_satellite_ao_dispatch_batch1_2026_07_26` and repoint each to the archived path →
      clear `locked_by` (already empty; confirm). **Done when**: the plan is in `plans/archive/2026_07/`, every corpus
      referrer resolves, `check_reference_paths.py` has not regressed, and this finalize doc is archived alongside it in
      the same commit.

## Codex SSOTs

- `/codex/06-coding-standards/quality-gates.md` — how the gate composes; ratchet-baseline convention
- `/codex/08-workflows/ci-cd-flow.md` — the pipeline contract batch-1 todo 17 edits
- `/codex/11-project-management/` — archival ritual, issue-doc lifecycle
- `plans/active/task_template.md` §4 — the finalize-plan-coverage rule this plan satisfies

## Progress Log

- **2026-07-26** — Drafted alongside `ci_satellite_ao_dispatch_batch1_2026_07_26.md` by `/ag-closeout-audit ci`
  (autonomous mode). Both are `status: draft`; neither is dispatched. Todo 1 exists because the batch's conflict-check
  found PM `scripts/quality-gates.sh` claimed by three separate new checkers — the documented remedy for
  partial-parallelism (parallel work in plan A, the shared gated step in plan B via `depends_on` +
  `gate_on_depends: true`).
