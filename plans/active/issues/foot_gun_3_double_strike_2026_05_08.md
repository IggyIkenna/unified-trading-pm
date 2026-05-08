---
title: "Foot-gun #3 double-strike — concurrent-agent commit hijack despite mandatory pre-commit check"
created: 2026-05-08
author: tab3-gcs-migration
source:
  - cursor-configs/CLAUDE.md § "Half 1 — The mandatory pre-commit check (catches accidental bundling)"
  - PM@784f2bfe (misattribution: Phase 0 commit message → Tab 1 defi_master content)
  - PM@12483f5b (bundle: Phase 0 plan flip + foreign live_pipeline_preaudit_2026_05_08.md)
  - PM@0cc633c8 (re-commit: Phase 0 deliverable correctly landed)
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Foot-gun #3 double-strike — Tab 3 Phase 0 sub-agent session, 2026-05-08

> **Severity**: P1 — workspace-wide concurrent-agent coordination weakness. Not a data-correctness or May-23 critical
> path issue, but the existing CLAUDE.md "mandatory pre-commit check" rule was followed AND still failed twice in 5
> minutes during a single Tab 3 sub-agent run. **Blast radius**: any session running ≥2 parallel sub-agents that commit
> to the same repo within seconds of each other. **Suggested owner**: workspace-rules / governance — operator triage.

## What I found

During Tab 3's Phase 0 sub-agent run (Phase 0 of `gcs_migration_bundle_pipeline_mode_2026_05_08.md`), the spawned
sub-agent triggered **two distinct foot-gun #3 incidents** in the PM repo within ~5 minutes despite explicit pre-commit
discipline (`git status` + `git diff --cached --stat` NO PATH ARG before every commit per CLAUDE.md).

### Incident A — `PM@784f2bfe`

- **Commit message** (my sub-agent's):
  `docs(plans): gcs-migration-bundle Phase 0 pre-audit doc — operator-runnable protocol for same-region GCE VM`.
- **Actual diff**: `plans/active/defi_master_2026_05_07.md | 58 ++++++++++++++++++++++++++++++++++` — i.e. 58 lines
  added to Tab 1's defi_master plan, which Tab 1 was actively editing in a separate Cursor tab.
- **My intended deliverable** (`plans/active/issues/gcs_migration_bundle_preaudit_2026_05_08.md`, 521 lines) did NOT
  land in this commit. It got reverted to untracked when prek's stash conflict rolled back the working tree mid-commit.
- **Recovery**: re-committed correctly at `PM@0cc633c8`.

### Incident B — `PM@12483f5b`

- **Commit message** (my sub-agent's): `docs(plans): gcs-migration-bundle Phase 0 flip — pre-audit doc shipped`.
- **Actual diff**: 2 files —
  - `plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md | 8 +/-` (correct — the Phase 0 plan flip)
  - `plans/active/issues/live_pipeline_preaudit_2026_05_08.md | 408 +++++++++++` (NOT mine — Tab 4's deliverable from
    another in-flight session got bundled under my plan-flip commit message).
- **My deliverable** (the plan flip) is correct.
- **Collateral**: Tab 4's 408-line live-pipeline-preaudit doc landed under my commit message. Their work is preserved on
  disk + on origin, just under the wrong commit attribution.

### Why the existing pre-commit rule was insufficient

CLAUDE.md "Half 1 — The mandatory pre-commit check" requires:

```
git status                 # full picture
git diff --cached --stat   # NO PATH ARG — see entire index
```

The sub-agent ran these checks. Between the check returning clean and `git commit` firing, **a parallel agent's
`git add` landed in the shared index**. The shared `.git/index` has no per-tab locking — staging operations from
different tabs are interleaved, and the window between "check" and "commit" is large enough (multiple seconds during
prek hook execution + commit-msg validation) for foreign work to slip in.

The CLAUDE.md rule is necessary but the protection window is leaky.

## Why it matters

- **Trust drift**: when commit messages don't match commit content, `git log` archaeology breaks. A future operator
  reading `git log --oneline --grep="Phase 0 pre-audit"` sees `784f2bfe` and `0cc633c8` — the first one's diff doesn't
  match its message.
- **Already a recurring pattern**: CLAUDE.md "Half 1" already lists 3 historical incidents (PM@961980db, PM@611b9501,
  PM@34075d84). This Tab 3 run adds **2 more in 5 minutes** — making the pattern frequent enough to question whether
  pre-commit checks alone are a viable mitigation.
- **Parallelism cost**: the workspace's "5-10 parallel agents per side, ~50 AI-days/day" parallelism amplification is
  partly cancelled by collision-recovery overhead. Each foot-gun incident burns ~5-10 min of agent time on diagnosis +
  re-commit + write-up.

## Recommended decision

Three options for operator triage. **Option C is recommended** as the lowest-friction durable fix.

### Option A — Per-tab git worktrees (heavy)

Each Cursor / Claude Code tab on the operator's PC operates in its own `git worktree` rather than sharing the same
working tree. Eliminates index races completely. **Cost**: workspace-wide tooling change + every agent prompt updated to
`cd <worktree-path>`. High disruption.

### Option B — Index lock during commit (medium)

Wrap every commit in a flock-acquired critical section so concurrent `git add` from other tabs blocks until the commit
completes. Implementable as a per-repo `pre-commit.sh` wrapper that takes `flock /tmp/{repo}-commit.lock`. **Cost**:
per-repo hook update + cross-platform `flock` shim. Medium disruption.

### Option C — Use `git commit -o <files>` (only-pathspecs) for every PM commit (light) — RECOMMENDED

`git commit -o file1 file2 …` commits ONLY the listed pathspecs, ignoring anything else in the index. The check is moved
from "verify-then-commit" to "commit-only-these-paths", closing the race window. Workflow change is a single-flag
CLAUDE.md addendum:

> Add to "Half 1 — The mandatory pre-commit check": after staging, commit with `git commit -o <file1> <file2> …` so the
> commit only touches the explicitly-listed paths regardless of what else has landed in the index since the staging
> operation.

**Cost**: CLAUDE.md ~5-line addendum + agent prompt template update. Lowest disruption.

**Caveat**: `-o` doesn't help for `git add -p` partial-hunk staging in the same file. For partial hunks, the staged
hunks become the input to `-o <file>`; the commit still includes the WHOLE current file state from the working tree, not
just the staged hunks. The `-o` flag is sufficient for the misattribution-by-foreign-file case (which is what incidents
A + B were), not for the partial-hunk case (PM@961980db which Half 1 already documents).

## Composes with

- CLAUDE.md "Half 1 — The mandatory pre-commit check" (the existing rule this issue strengthens, not replaces).
- CLAUDE.md "Two teammates × multiple parallel agents — don't edit unfamiliar files" (the parallel-agent reality this
  rule operates within).
- Existing 3 incidents in Half 1: PM@961980db (partial hunk), PM@611b9501 (rename in index), PM@34075d84 (parallel reset
  wiped staged renames). Today's Tab 3 incidents are new instances of the same class but with different surfaces — both
  were "foreign full-file additions slipping into MY commit between check and commit".
