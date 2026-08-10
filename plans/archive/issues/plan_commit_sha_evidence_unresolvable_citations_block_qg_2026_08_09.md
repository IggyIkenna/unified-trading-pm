---
doc_type: issue
title: >-
  Plan commit-SHA evidence gate RED corpus-wide — 2 unresolvable `<repo>@<sha>` citations block quickmerge on
  unified-trading-pm for every worker
summary: >-
  `check_plan_commit_sha_evidence.py` (a corpus-wide, non-file-scoped quickmerge post-gate check) is failing with 2
  unresolvable citations against baseline 0: `unified-trading-pm@07dbb2cb9b` (cited twice in
  git_health_not_clean_since_pinned_constant_2026_07_27.md) and `market-tick-data-service@5ea59b90` (cited in
  cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md). Neither SHA exists in the respective repo's local git
  history (`git cat-file -e` fails on both) — confirmed via `git log --all`. Discovered as a blocker while shipping an
  unrelated broad-except-narrowing task (neither citing doc was touched by that work). Since this check is corpus-wide
  (not scoped to the committer's own diff), it blocks EVERY worker trying to quickmerge unified-trading-pm right now,
  not just the one who introduced the fabricated citation.
status: resolved
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci, quality-gates, plan-evidence, qg-red, repo-blocker]
related:
  [
    /plans/archive/issues/git_health_not_clean_since_pinned_constant_2026_07_27.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md,
  ]
created: 2026-08-09
author: slot-8 (infra)
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: backend_engineer
drift_direction: advance-code
sequential: false
locked_by:
context_scope: [scripts/quality_gates/check_plan_commit_sha_evidence.py, plans/PLAN_FORMAT.md]
resolved_by: slot-8 (infra), 2026-08-09
source: >-
  Discovered 2026-08-09 (slot-8, infra) while shipping unrelated work: `bash scripts/quickmerge.sh` failed at its
  post-gate check suite on `plan-commit-sha-evidence`, unrelated to the files being shipped.
depends_on: []
---

> **🟢 ARCHIVED 2026-08-09** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Both citations corrected (`unified-trading-pm@d094b9b8e7`,
> `market-tick-data-service@b9f41a49`), independently converged with a concurrent slot's fix — no remaining open item.
> Filed directly into the archive since it was never committed at an active path.

# Plan commit-SHA evidence gate RED — 2 fabricated/unresolvable citations block unified-trading-pm quickmerge

## What I found

`python3 scripts/quality_gates/check_plan_commit_sha_evidence.py --workspace-root <ws>` reports:

```
Scanned 754 plan(s), 2668 `<repo>@<sha>` citation(s) found, 2668 checkable against a present sibling clone — 2 unresolvable.

Unresolvable commit-SHA citations: 2 (baseline 0).
  - unified-trading-pm/plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md:302: [todo] market-tick-data-service@5ea59b90
  - unified-trading-pm git_health_not_clean_since_pinned_constant_2026_07_27.md:119 (now archived): [todo] unified-trading-pm@07dbb2cb9b
```

Verified both directly:

```
$ cd unified-trading-pm && git cat-file -e 07dbb2cb9b   → fatal: Not a valid object name
$ cd market-tick-data-service && git cat-file -e 5ea59b90 → fatal: Not a valid object name
```

Neither SHA is reachable via `git log --all` in the respective repo's local clone either — these are not
"not-yet-fetched" commits, they don't exist. `git_health_not_clean_since_pinned_constant_2026_07_27.md` cites
`unified-trading-pm@07dbb2cb9b` twice (lines 139, 274) as completion evidence for two different todos.

This check is corpus-wide (scans all 754 plans, not scoped to a committer's own diff) and runs as a quickmerge post-gate
step — so it currently blocks EVERY worker's `bash scripts/quickmerge.sh --agent` on unified-trading-pm, not just
whoever introduced the fabricated citation.

## Why it matters

Same class as `pm_qg_broad_except_ratchet_red_finops_regression_2026_08_09.md` — a zero-tolerance evidence gate that's
currently red for the whole fleet blocks shipping unrelated, unrelated-file work. A fabricated `<repo>@<sha>` citation
is exactly the failure mode `check_plan_commit_sha_evidence.py` exists to catch (per `plans/PLAN_FORMAT.md` § 8c) — a
completion claim citing a commit that was never actually made.

## Recommended decision

Two todos, both bounded and worker-determinable:

## Todos

- [x] [BACKEND] P1. Investigate `git_health_not_clean_since_pinned_constant_2026_07_27.md` lines 139 and 274 — determine
      what commit (if any) actually delivered the work each `- [x]` claims, and either correct the citation to the real
      SHA or, if the work was never actually committed, revert the checkbox to `- [ ]` and reopen the todo. Repo:
      unified-trading-pm. — DONE 2026-08-09 (slot-8, infra): the work was real, just mis-cited — corrected both
      citations to `unified-trading-pm@d094b9b8e7` (verified via `git cat-file -e`, message matches verbatim).
- [x] [BACKEND] P1. Investigate `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md:302` — determine what commit
      in `market-tick-data-service` actually delivered the work the `[todo]` citation claims, and either correct the
      citation to the real SHA or revert the checkbox to `- [ ]` and reopen the todo. Repo: unified-trading-pm (citing
      doc) / market-tick-data-service (target repo to verify against). — DONE 2026-08-09 (slot-8, infra): corrected to
      `market-tick-data-service@b9f41a49`, confirmed on origin via `git cat-file -e` (matches the
      `quickmerge_agent_regate_resets_branch_loses_local_commit_2026_07_31.md` pattern — the originally cited local SHA
      was lost to a quickmerge regate, this is the surviving commit with identical content).

## Progress Log

- **2026-08-09 (slot-8, infra)**: Filed after `check_plan_commit_sha_evidence.py` blocked quickmerge on an unrelated
  broad-except-narrowing commit; verified both citations are genuinely unresolvable (not a local-clone fetch gap) via
  direct `git cat-file -e` in each cited repo. Declaring a `qg_red` repo-blocker so the fleet's RepoHealthWatcher
  handles the wait/notify while these 2 citations get corrected.
- **2026-08-09 (slot-8, infra)**: Both citations corrected in place (see todos above) and re-verified resolvable. All
  todos done, no lock — archiving per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`.
