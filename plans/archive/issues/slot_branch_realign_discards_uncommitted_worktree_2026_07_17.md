---
doc_type: issue
title: Slot branch-realign has no dirty-worktree guard — UNCOMMITTED agent work vanished 2x in one session (slot 3)
summary: |
  Sibling to [[slot11_silent_branch_reset_data_loss_2026_07_13]], which is `status: resolved` for the case it covered:
  **committed-but-unpushed** commits discarded by `heal_dead_slot_branch_quarantine()`'s
  `git checkout -B <base> origin/<base>` realign. Its P0 fix
  (`_MIN_AHEAD_COMMIT_AGE_SECONDS_FOR_REALIGN=900`) refuses to realign a repo whose **ahead commits** are <15 min old.
  That guard is keyed entirely on ahead-commit count/age, so a clone with **0 commits ahead and a dirty working tree
  gets neither the age refusal nor the preserve-push** — it goes straight to the realign. There is no
  `git status --porcelain` check anywhere in the heal path (the one at `_branch_state.py:154` belongs to
  `_reclaim_leftover_merged_branch`, a different function, which DOES refuse a dirty tree: "1. Working tree must be
  CLEAN — never touch a tree with uncommitted work"). On 2026-07-17 slot 3 observed 4 "branch: Reset to
  origin/live-defi-rollout" reflog entries in ~90 min across 3 repos, and twice lost uncommitted edits mid-task.
  **Mechanism NOT fully proven** — see § Open question; filing on evidence, not a theory.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-api-contracts, deployment-service, unified-trading-library]
scope: [engineer]
tags: [slot-safety, data-loss, branch-heal, self-healing, uncommitted-work, multi-agent]
related:
  [
    "[[slot11_silent_branch_reset_data_loss_2026_07_13]]",
    "codex/05-infrastructure/per-tab-worktrees.md",
    "codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md",
  ]
created: 2026-07-17
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: engineer
drift_direction: none
depends_on: []
source: >-
  slot session 2026-07-17 — authored while diagnosing the slot-3 dirty-worktree loss; frontmatter completed (stage enum
  + missing keys) by slot main·harsh_pc to unblock the PM lint-codex gate, content untouched
resolved_by: agent-orchestrator@cd559390 (fix direction 1 only; see resolution note)
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Slot branch-realign discards UNCOMMITTED worktree state

## Evidence (slot 3, 2026-07-17, all times BST)

Reflog signature `branch: Reset to origin/live-defi-rollout` (+ the paired
`checkout: moving from live-defi-rollout to live-defi-rollout`) — the exact signature
`scripts/dev/audit-fleet-reflog-resets.sh` pages on, and per [[slot11_silent_branch_reset_data_loss_2026_07_13]] emitted
by `checkout -B`, not by normal agent git usage:

| Time     | Repo                    | Effect on this session                                              |
| -------- | ----------------------- | ------------------------------------------------------------------- |
| 12:39:40 | deployment-service      | —                                                                   |
| 13:01:31 | unified-api-contracts   | **uncommitted `config/cloud-providers.yaml` edit reverted to HEAD** |
| 13:01:33 | unified-trading-library | my uncommitted test edits SURVIVED (see § Open question)            |
| 14:10:00 | unified-api-contracts   | —                                                                   |

Observed directly at ~13:05: `unified_api_contracts/config/cloud-providers.yaml` had reverted to HEAD content and
`git status --porcelain` reported it **clean** — the edit was gone, not stashed, with no error surfaced to the agent.
`deployment-service/configs/cloud-providers.yaml` reverted identically in the same window. Both were re-applied and the
session continued; the loss was noticed only because a quality gate read stale content and failed, i.e. **the failure is
silent by default**.

## Why the 2026-07-13 fix does not cover this

`heal_dead_slot_branch_quarantine()` (`agent-orchestrator/server/worktree_clean_check/_branch_state.py:386+`):

1. Refuse if a provably-LIVE peer owns the slot — the claim/tmux liveness check whose **false-negative gap is the
   documented root cause** of the original incident (a genuinely-live worker with a stale `.agent-claim` classifies
   "dead").
2. Refuse if **ahead commits** are younger than `_MIN_AHEAD_COMMIT_AGE_SECONDS_FOR_REALIGN` (the 2026-07-13 P0 fix).
3. Preserve-push to `origin/wip-preserve/...` if there are ahead commits.
4. `git checkout -B <base> origin/<base>`.

Steps 2 and 3 are both gated on ahead-commit count. **A dirty tree with 0 ahead commits skips both** and lands on step 4
with nothing protecting it — the preserve-push that makes step 4 "recoverable, never discard unrecoverably" never runs,
because there is no commit to preserve. The sibling function `_reclaim_leftover_merged_branch` already encodes the right
instinct (`status --porcelain` non-empty → return False); the heal path simply never got it.

## Open question — mechanism NOT proven (do not act on the theory alone)

`git checkout -B <base> origin/<base>` normally **refuses** ("Your local changes would be overwritten") rather than
silently discarding, and it preserves a local modification when the file is identical between old HEAD and
`origin/<base>`. That does not cleanly explain a _silent_ revert of an uncommitted file — nor why UTL's uncommitted
edits survived a reset in the same 2-second window while UAC's did not. So either:

- the realign is not the mechanism for the uncommitted case (something else in the heal/spawn path — a `git restore` /
  `clean` / re-clone / `refresh-slot-repo.sh` variant — is), or
- there is a path where the checkout is forced or the tree is reset first.

**Reproduce before fixing.** Whoever picks this up should confirm the actual command by instrumenting the heal path (or
grepping the orchestrator for `restore`/`clean -fd`/`checkout -f`/`-B` call sites) rather than assuming step 4. The
first fix below is safe and correct regardless of which command turns out to be responsible.

## Fix direction

1. **[INFRA] P1 — refuse to touch a dirty tree, full stop.** Add a `git status --porcelain` check to
   `heal_dead_slot_branch_quarantine()` alongside the existing ahead-commit guard: non-empty → no-op + log + leave
   quarantined for the human page (`_alert_branch_quarantine`), exactly as the <15-min ahead-commit case does. Mirrors
   `_reclaim_leftover_merged_branch`'s existing rule. This is the same "recoverability over liveness" principle the
   original fix chose; it just was not extended to uncommitted work, because that incident was about commits.
2. **[INFRA] P2 — preserve, don't only refuse.** For a dirty tree worth rescuing, a `git stash create` + push to
   `refs/wip-preserve/...` gives the uncommitted case the same durable escape hatch commits already get, instead of
   relying on the agent noticing.
3. **[VERIFY] P2 — extend the fleet audit.** `scripts/dev/audit-fleet-reflog-resets.sh` only correlates a reset with a
   preceding `commit:` reflog line, so **it structurally cannot see this class** — uncommitted loss leaves no reflog
   trace at all. Any "0 findings" from it is not evidence that uncommitted work is safe. Consider a periodic
   worktree-hash snapshot per slot, or accept that detection here is inherently best-effort and prioritise fix 1.
4. **[DOCS] P3** — `codex/05-infrastructure/per-tab-worktrees.md` currently frames inherited-dirty-WIP as LIVENESS-gated
   ("dead claim → inherit + commit; live claim / mtime <120s → PROTECT"). That rule is written for _agents_; note that
   the orchestrator's own heal path does not honour the same protection for uncommitted work.

## Workaround until fixed

Commit early (committed work now has the <15-min guard + preserve-push), or keep `git diff > patch` backups. This
session kept per-repo patches under the scratchpad after the first loss; that is what made the second one a 30-second
re-apply instead of a re-derivation.

## Provenance

Found while shipping `bucket_estate_consolidation_to_sub100_2026_07_13`'s asset-group parity sweep. Diagnosed read-only
via `git reflog show`, `git status`, and reading `_branch_state.py`. **agent-orchestrator was not modified** — the
mechanism is unproven and that repo is the live orchestrator runtime; guessing at a fix there is precisely the overreach
this session already made once (see the plan's ⚠️ CORRECTION MID-TASK banner).

## Resolution (2026-07-22) — fix direction 1 only

`agent-orchestrator@cd559390`. Implemented fix direction 1 exactly as specified: `heal_dead_slot_branch_quarantine` now
runs a `git status --porcelain` check per stop-state repo, immediately before the `checkout -B` — a non-empty result
refuses the realign (leaves the repo quarantined, logs the reason) regardless of ahead-commit count/age, closing the gap
the ahead-commit guard never covered. Mirrors `_reclaim_leftover_merged_branch`'s existing clean-tree rule exactly, per
the doc's own recommendation. New regression test `test_heal_refuses_realign_of_a_dirty_tree_with_zero_ahead_commits`
reproduces the exact gap (a `wrong_branch` stop-state, 0 ahead commits, an uncommitted staged edit) and asserts the edit
survives untouched. Full `agent-orchestrator quality-gates.sh` green (1579 passed).

**Deliberately NOT implemented**: fix direction 2 (preserve the dirty tree via `git stash create` + push before
realigning, so the repo can still be healed automatically rather than left quarantined). This would require actively
clearing the dirty working tree as part of the automated heal — closer to the class of operation CLAUDE.md's own hard
rule bans outright ("Never `git reset --hard`/`clean -fd`/`restore` uncommitted work") even with a preserve-first step,
and the doc itself marks it P2 (lower priority than fix 1, which it explicitly calls "safe and correct regardless of
which command turns out to be responsible"). Leaving the repo quarantined + paging a human (`_alert_branch_quarantine`,
unchanged) is the safe outcome for now — todo/fix-direction 2 stays open as a follow-up if quarantine-and-page proves
too disruptive in practice. Fix directions 3 (extend the reflog audit — it structurally cannot see this class either
way) and 4 (docs note) also remain open.

**On the "Open question" (mechanism NOT proven for the uncommitted case)**: while investigating the sibling
`quickmerge_silently_reset_unpushed_commit_2026_07_22.md` / `utl_shared_clone_commits_repeatedly_reset_2026_07_22.md`
docs the SAME session, `scripts/quickmerge.sh`'s `cascade_dep_branch()` was confirmed as the root cause for the
**committed**-commit class of silent reset (unconditional `checkout -B` in a shared ancestor clone). That function also
`git stash push -u` any dirty tree before switching branches and attempts a `stash pop` after — a plausible, NOT YET
independently verified, candidate mechanism for THIS doc's uncommitted-edit case too (a stash that never gets popped
back would read exactly as observed: file content reverted to HEAD, `git status --porcelain` clean, recoverable via
`git stash list` rather than reflog). Recording this as a lead for whoever picks up the still-open "Open question", not
as a second confirmed root cause — the fix shipped here (refuse-on-dirty in the heal path) is correct and complete
regardless of which mechanism is eventually confirmed.
