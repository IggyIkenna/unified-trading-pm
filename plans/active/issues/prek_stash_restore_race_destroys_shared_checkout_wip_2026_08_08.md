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

- [x] ✅ [BACKEND] P1. **Reproduce deterministically — DONE 2026-08-09 (slot 5, `unified-trading-pm@27ab8aea1c`).**
      Built `scripts/dev/repro-prek-stash-restore-race.sh`: a throwaway scratch repo (mktemp, never touches a real
      workspace repo) with a `local`/`system` hook that only `sleep 3`s (proves the loss needs no fixer/formatter hook
      mutating a file — elapsed wall-clock time during the hook run is sufficient). Session 1 stages `fileA` and runs
      `git commit` (fires the installed prek pre-commit hook); mid-hook (0.8s in, well before the 3s sleep ends) a
      second process — simulating a second session/editor with zero knowledge a stash is in flight — writes a newer edit
      to `fileC`, an unrelated file that was unstaged (dirty) at commit-start and so got swept into prek's stash.
      Confirmed the exact reported mechanism: 3/3 runs, `fileC` ends up reverted to its PRE-EDIT stashed snapshot,
      `git stash list` stays empty, `git status --porcelain` reports the file merely "modified" (not conflicted) — zero
      error, zero conflict marker, zero recovery path. Root cause per prek's own log line each run:
      `slow hook...Failed / files were modified by this hook / Hook changes conflicted with the     saved unstaged changes. Reverting the hook changes`
      — prek diffs the working tree before/after the hook and cannot distinguish "the hook wrote this" from "an
      unrelated external process wrote this during the window"; either way it takes the conflict-rollback branch and
      reinstates the ORIGINAL pre-hook stash, discarding whatever changed in between. Confirmed this reproduces on the
      fleet's already-patched `IggyIkenna/prek` v0.4.12 fork binary in effect on this host (sha256 `27993a6e...7c508`,
      matching the checksum recorded in
      `plans/archive/issues/prek_patch_cache_replays_stale_diff_onto_unrelated_files_2026_07_29.md`) — so this is a
      DISTINCT, still-open hazard, not a regression of that doc's fixed #1889-class index-corruption bug (that fix
      targeted a hook that itself modifies+restages files corrupting the git index; this mechanism needs no hook-side
      file mutation at all, only elapsed time + an external writer). Evidence: script exits 0 ("BUG REPRODUCED") on 3/3
      consecutive runs; full transcript in this doc's Progress Log below.
- [ ] [BACKEND] P1. **Serialise prek per checkout** — a simple flock around the hook invocation in
      `scripts/dev/safe-doc-push.sh` and `scripts/quickmerge.sh` would close the interleaving window without touching
      prek itself. Verify it does not deadlock when quickmerge invokes prek twice in one run (it does today: the commit
      retry re-runs the whole hook batch).
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
- **2026-08-09 (backend_engineer, slot 5)**: Reproduced deterministically per the todo above. Representative run
  (identical across all 3):

  ```
  Unstaged changes detected. Temporarily saving them to `~/.cache/prek/patches/<ts>-<pid>.patch`
  slow hook (widens the stash/restore race window).........................Failed
  - hook id: slow-hook
  - files were modified by this hook
  Hook changes conflicted with the saved unstaged changes. Reverting the hook changes
  Restored unstaged changes from `~/.cache/prek/patches/<ts>-<pid>.patch`

  final fileC content: "fileC v1 (session1, unrelated in-progress edit -- pre-stash snapshot)"
  git stash list (entries): 0
  git status --porcelain:
   M  fileA.txt
    M fileB.txt
    M fileC.txt
  ```

  Session 2's interleaved edit (`"fileC v2 ... MUST SURVIVE"`) never appears anywhere — not in the file, not in a stash,
  not as a conflict. This confirms the issue's core claim precisely: the silent-loss mechanism does not need two prek
  runs racing each other — one prek run's stash-then-restore window is sufficient, as long as ANY other writer (a second
  session, a second prek run, a manual edit) touches a file that was unstaged when the first run's hooks started.
  Script: `scripts/dev/repro-prek-stash-restore-race.sh` (self-contained, scratch-repo only, safe to re-run). Landed as
  `unified-trading-pm@27ab8aea1c` — see this todo's checkbox for the final SHA once pushed.
