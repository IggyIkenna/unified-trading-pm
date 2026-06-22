---
title:
  "Orchestrator pre-spawn dirty-state gate orphaned a LIVE session's uncommitted WIP (liveness-gating bypassed +
  commit-then-reset-on-push-reject)"
created: 2026-06-22
author: ikennaigboaka
parent_epic: orchestrator_master
priority: P2
source:
  - "git reflog (agent-orchestrator slot-2 clone) 2026-06-22: HEAD@{17-19}"
  - "orphaned commit 2c774030b40e4527f57e0608eb9473ac9e2a8dc7 (chore(orphan-wip))"
  - "server/worktree_clean_check/_orphan.py::commit_and_push_dirty_repos (DirtyStateResolution.COMMIT_AND_PUSH)"
  - "CLAUDE.md § 'Inherited-dirty-WIP — liveness-gated, not identity-gated'"
  - "codex/05-infrastructure/per-tab-worktrees.md § respawn working-tree hygiene"
locked_by: live-defi-rollout
---

## What I found

During the utl_uac P2 read-migration (2026-06-22), a slot-2 agent-orchestrator clone had ~14 files of **uncommitted,
actively-being-edited WIP** (a Wave-4b batch). The reflog shows the orchestrator's own pre-spawn dirty-state gate then
silently orphaned that work in two steps:

```
2eb63b5  HEAD@{19}: commit: ... wave 4a            (last real commit; then 14 files edited, uncommitted)
2c77403  HEAD@{18}: commit: chore(orphan-wip): inherited WIP from predecessor on slot 2 at 2026-06-22T11:31:21Z
6ad6d4a  HEAD@{17}: branch: Reset to origin/live-defi-rollout
```

1. **The gate auto-committed a LIVE session's WIP as "predecessor orphan WIP."** `commit_and_push_dirty_repos`
   (`server/worktree_clean_check/_orphan.py`, `DirtyStateResolution.COMMIT_AND_PUSH`) committed the dirty tree as
   `chore(orphan-wip)` `2c77403`, authored `agent-orchestrator (orphan-wip)`, message: _"inherited WIP from predecessor
   on slot 2 … Auto-committed by agent-orchestrator pre-spawn dirty-state gate."_ The session whose WIP it took was
   **live and mid-edit**, not a dead predecessor.
2. **The push was rejected (slot behind origin), and the recovery `Reset to origin/live-defi-rollout` discarded the
   just-made commit.** `2c77403` never reached origin (origin had advanced to the backmerge `6ad6d4a`); the gate's
   reset-to-origin recovery moved `HEAD` off `2c77403`, leaving it a **dangling commit** (orphaned, not in any ref's
   ancestry).

Net effect: the working tree silently went clean at `6ad6d4a`; the 14 files "vanished." The WIP was **not destroyed**
(`git show 2c77403` still holds all 14 files; recoverable via cherry-pick), but nothing surfaced the dangling sha, so it
read as data loss and the work was needlessly re-done.

## Why it matters

- **It violates the documented liveness rule.** CLAUDE.md § "Inherited-dirty-WIP — liveness-gated, not identity-gated":
  _a DIFFERENT live session's fresh claim OR a file with mtime <120 s → PROTECT, never stomp._ The gate committed-then-
  orphaned a live, actively-edited tree. `server/worktree_clean_check/_orphan.py::commit_and_push_dirty_repos` contains
  **no mtime / `.agent-claim` / heartbeat liveness check** — the liveness discriminator is supposed to gate the
  _decision_ to call it, but in this run it did not protect the live session (interactive sessions may not register the
  liveness signal the gate checks, or the check has a gap).
- **Silent apparent data-loss is an autonomy hazard.** Any interactive operator session or worker mid-edit on a slot can
  have a multi-file uncommitted batch committed to a throwaway orphan-wip commit and then reset away. The recovery path
  (find the dangling sha in the reflog) is non-obvious — the natural (wrong) conclusion is "my work is gone," leading to
  expensive re-doing or, worse, giving up.
- **The gate's own commit is not durable.** Even setting aside the misclassification: COMMIT_AND_PUSH makes a local
  commit, and if the push is rejected because the slot is behind, the recovery resets to origin and **discards its own
  just-made commit** instead of rebasing/preserving it.

## Recommended decision

1. **Enforce the liveness discriminator BEFORE COMMIT_AND_PUSH.** A slot with a provably-live session (fresh
   `.agent-claim`/heartbeat, OR any tracked file with mtime < 120 s) must be PROTECTED — never treated as "predecessor
   orphan WIP." Add the check at the gate's decision point (and/or inside `commit_and_push_dirty_repos` as a defensive
   guard), per the CLAUDE.md rule + `codex/05-infrastructure/per-tab-worktrees.md`.
2. **Never `reset --hard`/`branch -f` away a local-only commit the gate just made.** If COMMIT_AND_PUSH's push is
   rejected (slot behind), the recovery must `pull --rebase --autostash` (replaying the orphan-wip commit onto origin)
   or push it to a `wip-preserve/slot-<N>` ref — so the commit stays reachable. A reset-to-origin that drops an unpushed
   commit is the orphaning bug.
3. **If protection isn't certain, fail safe to preservation, not to a reset.** When the gate cannot confirm liveness AND
   cannot push, leave the orphan-wip commit on a named branch (`origin/wip-preserve/slot-<N>`, the existing convention)
   rather than orphaning it — and log the recovery sha loudly.
4. **Interactive-session liveness:** confirm that an interactive Claude Code session on a slot registers the same
   `.agent-claim`/heartbeat the gate keys off (the symmetric-worker model says an interactive session IS slot N) — if it
   doesn't, the gate will keep mistaking live operator WIP for dead-predecessor leftovers.

Evidence reproducible from the slot-2 clone: `git reflog` (`HEAD@{17}`/`{18}`), `git show 2c77403 --stat`. The
read-migration plan (`utl_uac_reuse_consolidation_remediation_2026_06_10.md`) carries the corrected incident note.
