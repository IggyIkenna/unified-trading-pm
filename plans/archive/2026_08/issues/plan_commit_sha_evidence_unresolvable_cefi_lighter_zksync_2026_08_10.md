---
doc_type: issue
title:
  plan-commit-sha-evidence gate red — cefi_lighter_zksync doc cites a non-resolving market-tick-data-service sha
  (13ac6245)
summary: >-
  `check_plan_commit_sha_evidence.py` (PM QG post-gate, `plan_commit_sha_evidence_baseline.yaml` = 0) is red at 1
  unresolvable `<repo>@<sha>` citation: `cefi_lighter_zksync_systemic_collision_2026_08_08.md:241` flips a todo as
  `market-tick-data-service@13ac6245`, but that sha does not resolve in the market-tick-data-service clone (verified
  after a fresh fetch — no object with that prefix under any ref). Introduced by the slot-20 flip commit `2540439aad`
  (2026-08-10); the sha was the worker's in-flight local HEAD and was rebased away on push. With baseline 0 this red
  leaves the PM tree not-green, blocking every PM worker's quickmerge ship.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quality-gates, plan-commit-sha-evidence, evidence, broken-citation]
related:
  [
    /plans/active/issues/cefi_lighter_zksync_systemic_collision_2026_08_08.md,
    /plans/archive/2026_08/issues/tradfi_manifest_casing_tests_red_trunk_2026_08_10.md,
  ]
created: 2026-08-10
author: slot-23 (infra worker, task doc_body_link_checker_blind_to_backtick_citations-002)
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.08
resolved_by:
locked_by:
locked_since:
context_scope: []
supersedes:
superseded_by:
depends_on:
source: [PM quality-gates.sh run 2026-08-10 (slot-23), plan-commit-sha-evidence post-gate red]
assigned_role: infra
drift_direction: advance-code
---

> **ARCHIVED**: resolved 2026-08-10 — the unresolvable `13ac6245` citation is corrected to the landed
> `market-tick-data-service@335c94f1` (slot 20 reconcile + this slot-8 task's line-272 fix).
> `check_plan_commit_sha_evidence.py` green (758 plans, 2853 citations, 0 unresolvable, baseline 0). Successor: none.

# plan-commit-sha-evidence gate red: cefi_lighter_zksync cites fabricated market-tick-data-service@13ac6245

## What I found

`scripts/quality_gates/check_plan_commit_sha_evidence.py` (PM QG post-gate, `plan_commit_sha_evidence_baseline.yaml`
= 0) is red at exactly 1 unresolvable `<repo>@<sha>` citation:

- `plans/active/issues/cefi_lighter_zksync_systemic_collision_2026_08_08.md:241` — a `- [x]` DATA todo flip reads
  `market-tick-data-service@13ac6245 (slot 20, 2026-08-10)`. The sha `13ac6245` does NOT resolve in the
  market-tick-data-service clone: verified after a fresh `git fetch origin live-defi-rollout` —
  `git cat-file -t 13ac6245` fails and `git rev-list --all` has no object with that prefix under any ref.

The cefi LIGHTER-ZKSYNC work itself is real and shipped in market-tick-data-service (e.g. `46db6785` "fix(cefi):
tolerate canonical column-superset in would-patch-duplicate compare", `5c0c7f3f` BROAD comparison, `fa72b743` root cause
audit). The slot-20 worker's in-flight HEAD was `13ac6245` at QG time (corroborated by
`tradfi_manifest_casing_tests_red_trunk_2026_08_10.md` § What I found) but the commit was rebased/force-pushed away on
shipping, so the cited short sha no longer exists on origin. This is a stale local-sha citation, not deliberate
fabrication.

## Why it matters

`plan-commit-sha-evidence` is a hard PM QG post-gate with baseline 0. While red, the PM tree is not green, which blocks
every PM worker's quickmerge ship and will fail the quality-gates-v2 promotion PR. It is exactly the
unresolvable-evidence-citation class the gate exists to catch; the fix must correct the citation, never re-baseline a
fabricated sha into `plan_commit_sha_evidence_baseline.yaml`.

## Recommended decision

A fix-worker (or the slot-20/27 owner once they next touch the doc): correct
`cefi_lighter_zksync_systemic_collision_2026_08_08.md:241` to cite the real market-tick-data-service sha for the
LIGHTER-ZKSYNC content-upgrade fix. Candidate: `46db6785` (the "tolerate canonical column-superset" commit, matching the
todo's DECISION (a) content-upgrade) — confirm it is the intended commit before landing, since the doc is another
worker's active file and was not edited by this task.

- [x] ✅ [DOCS] P1. Fix the unresolvable citation at
      `plans/active/issues/cefi_lighter_zksync_systemic_collision_2026_08_08.md:241`: replace the fabricated short sha
      `13ac6245` with the real sha for the LIGHTER-ZKSYNC content-upgrade commit (candidate `46db6785` — confirm intent
      before landing). Then `python3     scripts/quality_gates/check_plan_commit_sha_evidence.py` must be green
      (baseline 0) and the fix shipped via quickmerge. Repo: unified-trading-pm. **RESOLVED 2026-08-10** — the citation
      is now the landed content-upgrade sha `market-tick-data-service@335c94f1` (the wire-superset three-way-verdict
      commit; the local-only `13ac6245` never reached origin). Line 241's flip was corrected by slot-20's reconcile
      (`c89090ed1d`); this task corrected the last remaining `mtds@13ac6245` at line 272 to
      `market-tick-data-service@335c94f1`. `check_plan_commit_sha_evidence.py` green: 758 plans, 2852 citations, 0
      unresolvable (baseline 0).

## Progress Log

- **2026-08-10 (slot-23)**: filed during `doc_body_link_checker_blind_to_backtick_citations-002` — this task's own PM
  `quality-gates.sh` run surfaced the red post-gate (baseline 0 → 1). Declared a `qg_red` repo-blocker on
  unified-trading-pm so the backend owns the fix dispatch + green signal.
