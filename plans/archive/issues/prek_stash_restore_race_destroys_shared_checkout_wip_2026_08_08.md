---
doc_type: issue
title: prek stash/restore cycle silently destroys uncommitted WIP on a shared checkout
summary: >-
  Every prek/pre-commit run stashes unstaged changes to a patch and restores them afterwards. On a shared multi-session
  checkout two concurrent runs interleave, and one session's restore reverts another session's in-progress file to HEAD
  with no error, no conflict, and no stash entry. Measured three times in one session on the same file; recovered only
  because a scratchpad backup existed. This is a silent data-loss class, not a merge conflict.
status: resolved
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
last_updated: "2026-08-09"
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
  unified-trading-pm@d38f16f66 (todo 2) + unified-trading-pm@f8a307bad (todo 3) + this session's todo-4 commit, see
  Progress Log
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Hit three times while shipping the AO context-probe fix (2026-08-08 interactive session, slot 1).
depends_on: []
---

> **🟢 ARCHIVED 2026-08-09 — RESOLVED.** All 4 todos done: deterministic repro
> (`scripts/dev/repro-prek-stash-restore-race.sh`), the flock serialization fix (`unified-trading-pm@d38f16f66`), the
> checksum-verify loud-failure fix (`unified-trading-pm@f8a307bad`), and the scratchpad-backup HARD RULE now documented
> as item 4 of `/codex/05-infrastructure/per-tab-worktrees.md` § "What worktree isolation does NOT cover". 0 open todos,
> unlocked.

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

- [x] [BACKEND] P1. **Reproduce deterministically** — two concurrent prek runs in one checkout with an interleaved edit
      to a third file, and confirm the restore reverts it. Needed before any fix, since the mechanism above is inferred
      from three consistent observations plus prek's own log lines, not from a controlled repro. — ✅
      `unified-trading-pm/scripts/dev/repro-prek-stash-restore-race.sh` reproduces it deterministically (see Progress
      Log).
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
- [x] [BACKEND] P2. ✅ **Make the loss loud** — `unified-trading-pm@f8a307bad`. Both `locked_git_commit`
      (safe-doc-push.sh) and the main commit-retry loop (quickmerge.sh) now checksum (`git hash-object`) every
      already-unstaged file right before their `git commit` call — exactly the set prek's own stash captures — and
      compare after the call returns. A changed checksum on a file neither script touched is the silent-revert
      signature; both scripts now hard-stop with an actionable message (citing this issue doc) instead of reporting a
      clean tree. No auto-fix/auto-restore attempted (we don't know which version is "right", and must never overwrite
      foreign WIP either way). Verified: 2 new regression tests added to
      `scripts/quality-gates-base/tests/test-quickmerge-commit-lock.sh` extracting the real `_prek_race_snapshot`/
      `_prek_race_check` functions — one asserts detection on a synthesized silent-revert, one asserts no false positive
      on an untouched unstaged file (both pass; full 6/6 suite green). Full `quality-gates.sh` Pass-1 green.
- [x] [DOCS] P2. ✅ **Add the scratchpad-backup rule to the multi-agent safety SSOT** — `unified-trading-pm@<pending>`.
      Added item 4 to the "What worktree isolation does NOT cover" list in
      `/codex/05-infrastructure/per-tab-worktrees.md` documenting the prek stash/restore race mechanism (cites this
      issue doc + the deterministic repro script) plus the HARD RULE: "back up uncommitted WIP to the scratchpad BEFORE
      running any git-touching command in a shared checkout, and verify the backup before trusting it." That is what
      saved the work here, and it is now written down.

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
- **2026-08-09 (slot 19, backend_engineer)**: Todo 1 done — deterministic repro shipped at
  `scripts/dev/repro-prek-stash-restore-race.sh`. Built a disposable scratch repo (mktemp, never touches the real
  checkout) with `prek install`ed as the real `.git/hooks/pre-commit` and a deliberately slow local hook (`sleep 8`),
  then ran two GENUINELY concurrent `git commit`s racing on a shared third file (`victim.txt`): Session A edits
  `victim.txt` then commits its own `fileA.txt` (slow hook); ~1.5s in, once A's stash-checkout has reset `victim.txt`
  back to the pre-edit baseline, Session B edits `victim.txt` again and commits its own `fileB.txt` with `--no-verify`
  so B's own restore lands near-instantly. Confirmed mechanism end to end: prek's log shows
  `Unstaged changes detected. Temporarily saving them to .../patches/<ts>-<pid>.patch` at A's commit start, then — once
  B's edit has already landed and A's slow hook finally exits —
  `Hook changes conflicted with the saved unstaged changes. Reverting the hook changes` /
  `Restored unstaged changes from <patch>`, which silently reapplies A's STALE snapshot over B's
  already-committed-and-restored newer edit. Final state: `victim.txt` holds A's old content, B's edit is gone;
  `git stash list` is empty (prek uses its own `~/.cache/prek/patches/` cache, not a real git stash) and
  `git status --short` shows only an unremarkable ` M victim.txt` — exactly the "no error, no conflict marker, no stash
  entry" signature the issue describes, now reproduced on demand rather than inferred from log lines. One correction to
  the original write-up: prek DOES print a `Failed`/"files were modified by this hook" line and a nonzero exit to the
  SLOWER session's own terminal (session A here) — so the originating commit itself is not perfectly silent — but the
  VICTIM session (B, whose already-landed edit gets clobbered) sees nothing at all: no error, no stash entry,
  `git status` reads clean-ish. That asymmetry is exactly why this class evaded detection three times in the original
  incident (the agent editing the file has no reason to suspect a DIFFERENT process's commit just silently reverted it).
  Also confirmed manual `prek run --all-files` (no real `git commit`) does NOT trigger the stash/restore path at all —
  the hazard is specific to prek running as the actual git pre-commit hook (matches how
  `safe-doc-push.sh`/`quickmerge.sh` invoke it). Script kept as `Lifecycle: permanent` — worth a follow-up run against
  the now-shipped todo-2 flock fix (`unified-trading-pm@d38f16f66`, landed concurrently by slot-22 above) to confirm it
  actually closes the interleaving window, and again once todo 3's checksum-verify lands.
- **2026-08-09 (slot 32, infra worker adopting backend_engineer craft for this task)**: Shipped the last open todo —
  added item 4 to the "What worktree isolation does NOT cover" list in `/codex/05-infrastructure/per-tab-worktrees.md`,
  documenting the prek stash/restore race mechanism (citing this issue doc + the deterministic repro script from the
  prior entry) and the scratchpad-backup HARD RULE. Backed up both edited files to the session scratchpad and verified
  the copies (`diff -q`) before running any git command, per the very rule being added — practicing what the new rule
  states. All 4 todos now done; archiving this doc per the plan-completion-and-archival-discipline SSOT's 6-step ritual
  (flip committed first at the still-active path, `git mv` to `plans/archive/issues/` follows as a separate commit).
