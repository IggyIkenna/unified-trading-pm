---
doc_type: issue
title: >-
  Sharded per-tranche audit runs (na-eligibility-auditor / ag-closeout-auditor) have two concurrency defects — worktrees
  created off one clone share `refs/stash` so a `git stash` round-trip can hand one agent's WIP to a sibling, and
  multi-tranche docs can never safely receive the incremental-skip verdict marker, so they are re-read in full forever
summary: >-
  Found live during a real `/na-eligibility-audit --tranche tradfi` run executed as one of 9 concurrent per-tranche
  workers against the same PM clone. (1) STASH RACE — each worker was isolated via `git worktree add`, but a worktree
  created from a clone SHARES that clone's `.git`, and therefore shares the single `refs/stash` ref. A routine `git
  stash push` / `git stash pop` round-trip (used to A/B a ratchet against a pristine tree) pushed this worker's 15-file
  changeset and popped a DIFFERENT agent's autostash instead, silently swapping ~15 tradfi doc edits out of this
  worktree and ~24 unrelated ci/infra doc edits in. No data was lost here (both sides recovered, see Recovery), but the
  same race can silently destroy a sibling's WIP for any agent that then runs `git stash drop` or commits the foreign
  files as its own. (2) MULTI-TRANCHE MARKER GAP — 16 of this tranche's 31 in-scope docs carry 2-6 asset_groups, so up
  to 6 concurrent tranche workers classify the same file in the same wave. Whichever ones write the skill's dated
  Progress-Log verdict marker produce an N-way merge conflict at integration; whichever ones skip it leave the doc
  unmarked, so Phase 0's incremental-skip filter can never skip it and every future daily run re-reads it in full. The
  incremental mode therefore does not actually apply to roughly half the corpus.
status: open
nature: issue
asset_group: [meta, cross-cutting]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags:
  [plan-hygiene, na-eligibility-audit, ag-closeout-audit, concurrency, git, worktrees, sharded-dispatch, incremental]
related:
  [
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: 2026-07-30
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Observed live 2026-07-30 during a real sharded `/na-eligibility-audit` run (tranche=tradfi, one of 9 concurrent
  per-tranche workers against the same unified-trading-pm clone, branch ao-bench-na-tradfi). Both defects were hit in a
  single run; neither is hypothetical.
---

# Sharded per-tranche audits: a shared-`refs/stash` race and a structural incremental-marker gap

## 1. The stash race (data-loss class, hit live)

**Mechanism.** The isolation recipe for a sharded run is `git worktree add <path> -b <branch> HEAD`. That gives each
worker its own working tree and its own `HEAD`, which is what the recipe is for — but a worktree does **not** get its
own `.git`. It shares the parent clone's object store _and its refs_, including the single `refs/stash`. `git stash` is
therefore a **global, shared, LIFO stack across every concurrent worker on that clone.**

**What happened.** This worker ran a perfectly ordinary A/B: stash its own 15-file changeset, re-run
`check_reference_paths.py` against the pristine tree to prove the ratchet delta was pre-existing, then pop. Between the
push and the pop, a sibling agent's own stash traffic interleaved. Result: this worktree came back with **24 modified
ci/infra plan docs it had never touched** (`cicd_mvp_ldr_to_main_pipeline_2026_06_30.md`,
`ldr_to_main_promote_churn_fix_verification_2026_07_27.md`, `qg_sentinel_environment_blind_2026_07_23.md`, …) and
**zero** of its own 15 tradfi edits. `git stash list` contained no entry matching this worker's stash message, and no
stash entry contained any of its files — its changeset had been popped into someone else's tree.

**Why this is worse than an inconvenience.** The failure is silent and it looks like your own work. An agent that
doesn't notice will either (a) `git add` the foreign files and commit another agent's half-finished WIP under its own
branch and commit message, or (b) treat the foreign files as junk and `git checkout HEAD --` / `git stash drop` them —
which is unrecoverable, and is exactly the operation the workspace rules already ban for foreign WIP. The rule as
written ("never `git stash drop` a foreign WIP") assumes you can _tell_ it is foreign. Under this race you cannot: it
arrives in your own worktree as the result of your own `pop`.

**Recovery performed (both sides preserved, nothing dropped).** The foreign changeset was saved to disk as a patch
before anything else was done, then re-pushed to the shared stash under an explicit, greppable message so the owning
agent's normal recovery path finds it:
`stash@{0} — "RECOVERED-foreign-autostash-ci-infra-24files (accidentally popped into ao-bench-na-tradfi worktree 2026-07-30 by a shared-refs/stash race; patch copy at scratchpad/…)"`.
This worker's own 15 edits were then re-applied deterministically from its own session record rather than hunted for in
the stash stack. Net: no work destroyed on either side, ~1 rework cycle lost.

## 2. The multi-tranche marker gap (structural, affects every future run)

Tranche membership is derived from a doc's `asset_group` list, and that list is frequently multi-valued. In this run's
own Phase-0 inventory, **16 of 31 in-scope docs were multi-tranche** — 9 of them spanning 5 or 6 tranches
(`instruments_remaining_work_audit_2026_07_10.md` is in all 6). Since the timer fires all 9 tranches concurrently, those
docs are classified simultaneously by up to 6 workers, each of which the skill instructs to append a dated verdict
marker to the same `## Progress Log` section of the same file.

Both available behaviours are wrong:

- **Write the marker** → 6 concurrent appends to the same section of the same file → guaranteed N-way conflict for
  whatever merges the tranche branches.
- **Skip the marker** (what this run did, deliberately) → the doc is never marked → Phase 0's incremental-skip filter
  (skip iff a dated marker exists AND the doc has not been edited since) can never fire for it → **every daily run
  re-reads all 16 in full, forever.** The incremental mode the skill exists to provide simply does not apply to roughly
  half the corpus.

This is a real cost driver for the cadence decision: the "incremental" run is only incremental over the
single-asset-group docs.

## Options (operator ruling wanted on #2; #1 has an obvious mechanical fix)

For **(1) the stash race** — recommended **A**:

- **A [WORKER REC]: make sharded workers stash-free.** Have the dispatch recipe use a real `git clone` (or
  `git worktree add` + an explicit `GIT_INDEX_FILE`/no-stash contract) and add one line to both skills' autonomous-mode
  sections: _never_ `git stash` in a sharded run — to A/B a check against a pristine tree, use a throwaway second
  worktree at `HEAD` instead. Cheap, no infrastructure change.
- B: give each worker its own clone (heavier: full object copy per tranche × 9).
- C: serialise the tranches (kills the concurrency the sharding exists for).

For **(2) the multi-tranche marker gap** — recommended **A**:

- **A [WORKER REC]: assign each doc exactly ONE owning tranche** (first `asset_group`, or an explicit `audit_tranche:`
  frontmatter key when the first entry is wrong) and have every other tranche skip it entirely. Restores incremental
  mode across the whole corpus, removes the conflict class outright, and makes each doc's verdict history
  single-threaded and readable. Cost: an owning-tranche key on the multi-AG docs.
- B: write markers to a per-tranche sidecar index file (e.g. `plans/.na-audit-verdicts/<tranche>.yaml`) instead of into
  the doc body — no conflicts, incremental mode works, but the verdict stops being visible where a human reads it.
- C: keep the status quo and accept that multi-tranche docs are always fully re-read — honest, but it is a permanent
  standing cost that should at least be a stated, deliberate choice rather than an accident.
- Other: operator can type a custom answer.

## Todos

- [x] [OPERATOR] P1. Rule on option A/B/C for the multi-tranche marker gap (§ 2) — this is an ownership/schema design
      call, not a worker-determinable fact, and it changes both `/na-eligibility-audit` and `/ag-closeout-audit`.
      **RULED 2026-07-30: option A (one owning tranche per doc), with the owning tranche derived from `parent_epic`
      rather than from the first `asset_group` entry** — `parent_epic` is single-valued and maps 1:1 onto a real
      `plans/epics/{parent_epic}.md`, and the `parent_epic`→tranche mapping is already blessed in
      `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 2, so no new `audit_tranche:`
      frontmatter key is needed. A non-owning tranche still classifies and reports a shared doc; only the owning tranche
      WRITES to it. Applied to `/cursor-configs/skills/na-eligibility-audit/SKILL.md` § "Primary-owner rule for
      multi-tranche docs" (the statement) and referenced from `/cursor-configs/skills/ag-closeout-audit/SKILL.md` §
      "Running as one of N concurrent sharded tranche workers" (not duplicated).
- [x] [DOC] P1. Once § 1's option is ruled (recommendation A), add the "never `git stash` in a sharded run — use a
      throwaway second worktree to A/B against a pristine tree" rule to both skills' Autonomous/AO-dispatched sections
      and to `/codex/05-infrastructure/per-tab-worktrees.md`, which currently documents worktree isolation without
      noting that `refs/stash` is shared. **DONE 2026-07-30** — added to
      `/cursor-configs/skills/ag-closeout-audit/SKILL.md` § "Running as one of N concurrent sharded tranche workers"
      (rule 2), `/cursor-configs/skills/na-eligibility-audit/SKILL.md` § "NEVER `git stash` as one of several concurrent
      sharded tranche workers", and `/codex/05-infrastructure/per-tab-worktrees.md` § "What worktree isolation does NOT
      cover" (which now states that `refs/stash` is one shared LIFO stack per `.git`, and that a shared scratch/temp
      path is likewise not isolated).
- [ ] [SCRIPT] P2. Have `generate_na_doc_tranche_inventory.py` emit an explicit `owning_tranche` per doc (however § 2 is
      ruled) so a worker can filter to the docs it owns instead of each tranche independently re-deriving membership
      from the full `asset_group` list.
