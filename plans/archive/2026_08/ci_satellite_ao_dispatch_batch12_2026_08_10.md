---
doc_type: plan
title: CI satellite AO batch 12 — twelfth AO-dispatch extraction for the ci tranche (infrastructure_master group)
summary: >-
  Round-12 satellite-extraction, `ci` tranche, from the scheduled `/ag-closeout-audit ci` run (2026-08-10, dispatch
  agt-d6ed2a). All 11 prior `ci` batches are archived and no batch currently covers the tranche — Phase 0 found zero
  active covering plans. Delta-checked against the 2026-08-09 final report (`ag_closeout_audit_ci_parked_2026_08_09.md`,
  49 members) rather than re-deriving all 53 current candidates from scratch: cross-referenced every carried-forward doc
  against batch9/10/11's own Progress Logs + Deferred reasoning (all still current, no verdict changes) and gave a full
  fresh Phase-1-style read to the 2 genuinely-new/changed candidates that turned out conflict-clear + AO-eligible, both
  sharing `parent_epic: infrastructure_master`: (1) the `check_archive_candidates.sh --only` vs.
  never-combine-flip-and-mv SSOT conflict (filed 2026-08-09, mid-batch9-finalize execution), and (2) recording the
  live-verified resolution of the Tier-A `ci_status` promotion deadlock (filed 2026-08-09 as a P1 incident; PR #1136
  merged 2026-08-09T12:31Z, live-reverified this run — instruments-service + system-integration-tests both green on
  `main` since, deadlock self-cleared exactly per the doc's own "Immediate unblock" path).
status: complete
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ci, ao-dispatch, close-out, batch-12, satellite-docs, archival-hygiene, ci-status, promotion-gate]
related:
  [
    /plans/active/issues/archive_candidates_hook_vs_no_combine_flip_archival_rule_conflict_2026_08_09.md,
    /plans/active/issues/tier_a_ci_status_gate_unrecoverable_deadlock_2026_08_09.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch12_finalize_2026_08_10.md,
    /plans/archive/2026_08/issues/ag_closeout_audit_ci_parked_2026_08_09.md,
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
effort: medium
sequential: false
drift_direction: advance-code
context_scope:
  [
    /plans/active/issues/archive_candidates_hook_vs_no_combine_flip_archival_rule_conflict_2026_08_09.md,
    /plans/active/issues/tier_a_ci_status_gate_unrecoverable_deadlock_2026_08_09.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    scripts/plan-hygiene/check_archive_candidates.sh,
    scripts/cicd/ldr_to_main_fleet_promote.sh,
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Round-12 satellite-extraction sweep, run 2026-08-10 (`ag_closeout_auditor`, autonomous, slot 27, dispatch agt-d6ed2a),
  against the `ci`-tranche candidate list (53 members: `generate_ag_closeout_audit_candidates.py --tranche ci`).
  Delta-check method (mirrors the 2026-08-09 second-dispatch precedent, Finding 4 of that report): re-derived
  candidates, diffed against yesterday's final 49-member list, cross-checked every carried-forward doc against
  batch9/10/11's own Progress Logs and the 2026-08-09 report's Method-note reasoning (all current, no verdict changes),
  then gave a full fresh per-doc read only to the genuinely-new/changed set. Full disposition ledger in the Progress Log
  below.
---

# CI satellite AO batch 12 (infrastructure_master group)

> **🟢 ARCHIVED 2026-08-10 — COMPLETE.** Both todos done. Finalize plan
> (`ci_satellite_ao_dispatch_batch12_finalize_2026_08_10.md`) reconciled both distinct source docs the 2 todos cite
> (`archive_candidates_hook_vs_no_combine_flip_archival_rule_conflict_2026_08_09.md` — done-with-evidence, codex
> narrowed to mode-2 only; `tier_a_ci_status_gate_unrecoverable_deadlock_2026_08_09.md` — deadlock self-cleared, doc
> stays open with `[OPERATOR]` structural-fix paths #2/#3), then archived this plan via the standard 6-step ritual.
> Finalize archived alongside at `/plans/archive/2026_08/ci_satellite_ao_dispatch_batch12_finalize_2026_08_10.md`.

> **Status: draft.** Per the skill's autonomous-mode rule (`/ag-closeout-audit` SKILL.md § Modes — "Phase 3... is a
> `status: draft` doc creation, which is safe to do autonomously... but flipping it to `status: active` is an operator
> decision"), this batch is authored `status: draft` and is NOT ingested/dispatched until an operator flips it to
> `active`. Unlike batch7-11 (authored `status: active` from creation by a manual pass with real-time operator
> authorization in that session), this batch was drafted by the scheduled autonomous `ag_closeout_auditor` run, which
> has no such standing authorization — the draft safety rail applies here exactly as it did for batch6.

## Same-file contention — read before executing

Todo 1 and todo 2 touch fully disjoint files (todo 1: `agent-orchestrator/server/verify.py` +
`plan-completion-and-archival-discipline.md` and/or `check_archive_candidates.sh`, depending on its own investigation's
outcome; todo 2: `tier_a_ci_status_gate_unrecoverable_deadlock_2026_08_09.md` only) — safe to run concurrently.

## Todos

- [x] ✅ [DOC] P2. **Resolve the `check_archive_candidates.sh --only` vs. never-combine-flip-and-mv SSOT conflict.** —
      unified-trading-pm@a4b2248b6f. Path (a) confirmed: the M3 gap IS closed for mode 1. Direct trial (slot 17,
      scratch-repo simulation) verified `_archival_rename_disposition` detects a same-commit flip+`git mv`; the existing
      test `test_done_accepts_cross_repo_self_archived_with_annotated_checked_line` PASSES. Codex narrowed to mode-2
      only; `archive_exempt` bridge documented for the cross-repo two-commit split. Source doc's both todos now `[x]`.
      See Progress Log for full evidence trail.

  **Resolution (2026-08-10, slot 17): path (a) taken.** Direct trial confirmed `_archival_rename_disposition` detects a
  same-commit flip+`git mv` → `plan_ref_self_archived_with_marker`. Codex narrowed (`79171795f2` + citation-fix
  follow-up); `archive_exempt` bridge already documented + shipped (todo 2 of the source doc). All 3 sub-steps complete:
  investigation done (real trial, not code read), codex rule narrowed to mode-2 only, both source-doc todos flipped with
  citations.

  - Conflict-checked 2026-08-10: grepped `plans/active/` for `check_archive_candidates`,
    `never combine the checkbox flip`, `_mode1_disposition`, `_resolve_current_plan_text` — all hits are incidental
    mentions in unrelated docs (a different `check_archive_candidates.sh --diff-base` incremental-check item in
    `plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md`; various
    `plan_reconciler_findings_*` process journals listing it as a hygiene-check name). Grepped every active plan for
    this doc's own basename — zero hits. No active plan already claims this exact ground.

- [x] ✅ [DOC] P2. **Record the live-verified resolution of the Tier-A `ci_status` promotion deadlock; leave the
      structural-fix ask open.** Full context: `issues/tier_a_ci_status_gate_unrecoverable_deadlock_2026_08_09.md`. The
      doc's own "Suggested resolution paths" #1 (merge `instruments-service#1136` to force a fresh main-branch GREEN)
      already happened — **merged 2026-08-09T12:31:02Z**, `quality-gates-v2` + `sit-gate/fleet-green` both SUCCESS on
      that merge. Re-verify live (do not trust this todo's own citation blind — re-run the checks fresh, since more than
      a day has passed):
      `gh run list --repo IggyIkenna/instruments-service --branch main --workflow quality-gates-v2.yml --limit 5` and
      the equivalent for `system-integration-tests` (the dependent that was also blocked via dep-order) should show
      multiple GREEN `push` runs on `main` after the merge timestamp, confirming `ci_status` self-cleared for real and
      the deadlock has not recurred. Append a `## Resolution (2026-08-10)` section to the source doc citing this
      evidence (mirror the doc's own existing citation style — exact run IDs/timestamps, not paraphrased). **Do NOT
      close or archive the doc** — its own text is explicit that the immediate unblock is a SEPARATE claim from "the
      actual ask of this issue" (the structural fix: stop the Tier-A gate's hard veto on _minting_ a fresh promote PR
      while `ci_status=FAILING`, per its "Suggested resolution paths" #2/#3). That structural fix touches
      `scripts/cicd/ldr_to_main_fleet_promote.sh`'s Tier-A gate — a shared, fleet-wide, high-blast-radius promotion
      mechanism every repo's `ldr_main` promotion depends on — matching this tranche's established caution around
      fleet-wide-promote-touching work (batch7's disposition of a similarly-shaped item: "Modifying the shared fleet
      promote mechanism... is a genuine re-scoping call, not a bounded implementation"). Leave paths #2/#3 as the doc's
      own open, un-extracted ask; do not attempt them here.

  **Done when**: the source doc records the live-reverified resolution with fresh evidence (not the stale already-known
  citation), the doc's `status` stays `open` (structural-fix ask genuinely still outstanding, not a candidate for
  archival), and PM's `quality-gates.sh` is green. Source:
  `issues/tier_a_ci_status_gate_unrecoverable_deadlock_2026_08_09.md` (informational update to a live-incident doc; its
  own 2 remaining "suggested resolution paths" #2/#3 are explicitly NOT extracted here — too_large_or_risky, shared
  fleet-wide gate mechanism).

  - Conflict-checked 2026-08-10: grepped `plans/active/` for `ldr_to_main_fleet_promote.sh`, `Tier-A gate`,
    `ci_status_store.py` — hits are either this doc itself, the distinct (already-known, different-mechanism)
    `ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md` incident (ad-hoc-dispatch starvation of the
    promote-fleet workflow, not the ci_status veto-deadlock this todo addresses), or unrelated docs mentioning the
    mechanism in passing. No active plan claims recording this specific resolution.

## Codex SSOTs (read before executing either todo)

- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the "never combine" rule todo 1 may narrow.
- `/codex/08-workflows/ci-cd-flow.md` — LDR→main gate set, promotion pipeline context for todo 2.
- `plans/active/task_template.md` §4 — the finalize-plan-coverage rule this plan's sibling satisfies.

## Progress Log

- **2026-08-10 (round-12 satellite-extraction sweep, scheduled `ag_closeout_auditor`, slot 27, agt-d6ed2a)** — Authored
  after a delta-check found the 2026-08-09 report's stopping condition ("all remaining orphans are non-batchable
  taxonomy, no batch12 warranted") no longer holds: 2 new docs filed 2026-08-09 (after that report) carry genuinely
  conflict-clear, bounded, worker-determinable work. Both share `parent_epic: infrastructure_master`, combined into one
  batch per the established grouping precedent (batch7/9). Full delta-check + per-doc disposition for every OTHER
  candidate (unchanged from yesterday) is in this run's own report, `issues/ag_closeout_audit_ci_parked_2026_08_10.md`.
- **2026-08-10 (slot 17, infra worker)** — completed todo 1. Direct `verify.check_plan_flip` trial (scratch-repo
  simulation) confirmed `_archival_rename_disposition` detects same-commit flip+`git mv` →
  `plan_ref_self_archived_with_marker`; existing test
  `test_done_accepts_cross_repo_self_archived_with_annotated_checked_line` PASSES. Codex narrowed to mode-2 only
  (`79171795f2` + citation-fix follow-up correcting the stale test-name reference). Source doc's both todos now `[x]`.
  Path (a) taken — the `check_archive_candidates.sh --only` hook and the codex rule now align.
- **2026-08-10 (slot-17, infra) — archived**. `git mv` to `plans/archive/2026_08/` via the standard 6-step ritual —
  banner + `status: complete`, all corpus referrers repointed, INDEX.md regenerated. Finalize plan archived alongside
  (all 3 of its todos done). `check_ag_closeout_linkage.py` 0 orphans (baseline 0) +
  `regenerate_active_plan_inventory.py` clean.
