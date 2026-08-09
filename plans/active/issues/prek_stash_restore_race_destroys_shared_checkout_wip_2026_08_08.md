---
doc_type: issue
title: prek stash/restore cycle silently destroys uncommitted WIP on a shared checkout
summary: >-
  Every prek/pre-commit run stashes unstaged changes to a patch and restores them afterwards. On a shared multi-session
  checkout two concurrent runs interleave, and one session's restore reverts another session's in-progress file to HEAD
  with no error, no conflict, and no stash entry. Measured three times in one session on the same file; recovered only
  because a scratchpad backup existed. This is a silent data-loss class, not a merge conflict.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [git, prek, pre-commit, multi-agent, data-loss, shared-checkout]
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-08
last_updated: "2026-08-08"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
drift_direction: fix-regression
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Hit three times while shipping the AO context-probe fix (2026-08-08 interactive session, slot 1).
depends_on: []
---

# prek stash/restore race destroys uncommitted WIP on a shared checkout

## What happens

Each prek run prints, around the hook batch:

```
Unstaged changes detected. Temporarily saving them to `~/.cache/prek/patches/<ts>-<pid>.patch`
...hooks...
Restored unstaged changes from `~/.cache/prek/patches/<ts>-<pid>.patch`
```

The patch is captured at run START. If a SECOND session edits a file while the first session's hooks are running, the
first session's **restore** reinstates its own older snapshot over the newer edit — reverting the file to HEAD content
from the second session's point of view. There is no error, no conflict marker, and **no stash entry to recover from**:
`git stash list` is empty and `git status` reports the file clean, so every normal recovery path reports "nothing was
lost."

## Measured evidence (2026-08-08, slot 1)

`unified-trading-pm/scripts/dev/precompact-watcher.py` was reverted from a 545-line edited version to the 354-line HEAD
version **three separate times** within minutes, twice within seconds of being restored:

1. After a `safe-doc-push.sh` run in the same checkout (that script runs prek).
2. Immediately after a manual `cp` restore — verified present, then absent on the very next command.
3. Again after `git add`, which is why the mandatory no-path-arg `git diff --cached --stat` showed the file **missing
   from the index** despite `git add` having reported success.

Recovery only worked because the file had been copied to the session scratchpad first. Without that backup the work was
unrecoverable — it is not in any commit, not in any stash, and not on disk.

## Why this is worse than ordinary multi-agent contention

The documented multi-agent hazards (`/codex/05-infrastructure/per-tab-worktrees.md`) are all things that FAIL LOUDLY: a
rejected push, a rebase conflict, a dirty-tree refusal. This one succeeds silently and reports a clean tree, so the
standard "check `git status`, check `git stash list`" recovery ritual actively confirms the wrong conclusion.

## Todos

- [ ] [BACKEND] P1. **Reproduce deterministically** — two concurrent prek runs in one checkout with an interleaved edit
      to a third file, and confirm the restore reverts it. Needed before any fix, since the mechanism above is inferred
      from three consistent observations plus prek's own log lines, not from a controlled repro.
- [x] [BACKEND] P1. ✅ **Serialise prek per checkout** — `unified-trading-pm@d38f16f66`. Added `locked_git_commit()` /
      `_qm_locked_git_commit()` to `scripts/dev/safe-doc-push.sh` / `scripts/quickmerge.sh` — a flock scoped to the
      checkout's own `.git` dir, held only around the single `git commit` call, wired into every commit call site in
      both scripts (incl. quickmerge's amend path + both retry paths). Mirrors quickmerge's existing cascade-lock
      convention (same FD-open/flock/unlock/FD-close shape + degrade-to-unlocked-if-flock-unavailable), a distinct lock
      file for a distinct critical section. Verified via a new regression test
      (`scripts/quality-gates-base/tests/test-quickmerge-commit-lock.sh`, following the existing
      `test-quickmerge-cascade-lock.sh` pattern — extracts the REAL functions from both scripts, not a replica): (1) two
      concurrent commits, one from each script, on the same checkout never interleave their pre-commit hook invocations
      (confirmed via a negative control that the same test correctly FAILS against the pre-fix unlocked call sites —
      proof the test would have caught the original bug), and (2) three sequential locked-commit calls in one process
      complete without a self-deadlock, directly answering this todo's own "does not deadlock when quickmerge invokes
      prek twice (up to 15x) in one run" requirement. QG green, landed + ancestry-verified on origin.
- [ ] [BACKEND] P2. **Make the loss loud** — have the wrapper checksum each unstaged file before the stash and compare
      after the restore, failing the run when a file changed underneath it. Even without a fix, a loud failure beats
      silent reversion.
- [ ] [DOCS] P2. **Add the scratchpad-backup rule to the multi-agent safety SSOT** — "back up uncommitted WIP to the
      scratchpad BEFORE running any git-touching command in a shared checkout, and verify the backup before trusting
      it." That is what saved the work here, and it is not currently written down anywhere.

## Codex SSOTs

- `/codex/05-infrastructure/per-tab-worktrees.md` — multi-agent safety invariants this extends
- `/codex/12-agent-workflow/commit-push-flip-rule.md` — the mandatory no-path-arg staged check that exposed it

## Progress Log

- **2026-08-08 (interactive session, slot 1)**: Filed after losing the same file three times while shipping the AO
  context-probe fix. Root cause inferred from prek's own stash/restore log lines bracketing every hook batch. Work was
  recovered from a session scratchpad backup and landed as `unified-trading-pm@8bff8f5792`.
- **context-scout 2026-08-09**: populated/refreshed context_scope (3 entries).
- **na-corpus-hygiene 2026-08-09**: RECLASSIFY — `assigned_vm: NA → planning`, `execution_scope → orchestrator-agent`.
  All 4 remaining todos (deterministic repro, flock-serialize prek, checksum-verify the stash/restore, add the
  scratchpad-backup rule) are bounded scoped code/doc changes with a stated done-when, per
  `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` §5 — no open-ended judgment call. No
  `locked_by`; the only cross-reference is an `[OPERATOR]` attention-nudge in
  `operator_action_items_consolidated_2026_08_08.md` ("worth a priority look"), not a competing work claim.
- **2026-08-09, slot-22 (backend_engineer), task `prek_stash_restore_race_destroys_shared_checkout_wip-e67fac2fe47f`**:
  shipped the "Serialise prek per checkout" todo — `unified-trading-pm@d38f16f66`, checkbox flipped above with full
  evidence. Live-witnessed the exact race mechanism firsthand while shipping this same commit (prek's own "Unstaged
  changes detected... Restored unstaged changes" lines fired twice mid-session on an unrelated frontmatter-auto-fixer
  byproduct file, harmlessly in that case, but the identical mechanism). The other 3 todos (deterministic repro,
  checksum-verify the stash/restore, scratchpad-backup-rule doc addition) remain open — not attempted this session, each
  is independently scoped per the file-collision discipline (repro needs no code change and doesn't touch either script;
  the checksum-verify todo touches the SAME two scripts this fix just changed, so should be sequenced after this todo
  rather than run concurrently with it — which is exactly what happened).
