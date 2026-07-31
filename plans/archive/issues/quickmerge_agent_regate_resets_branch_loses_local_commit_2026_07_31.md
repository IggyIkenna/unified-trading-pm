---
doc_type: issue
title: "quickmerge.sh --agent re-gate resets branch to origin, silently discarding a not-yet-pushed local commit"
summary:
  When `quickmerge.sh --agent` detects its Pass-1 SHA sentinel doesn't match current HEAD ("sentinel invalid — HEAD
  moved"), its retry/re-gate path resets the local branch to `origin/<branch>` rather than rebasing, which silently
  discards any local commit that was never pushed anywhere else. Reproduced 3 times in one session against
  `unified-api-contracts` (a high-churn shared repo) — each time the commit was recoverable via `git reflog` + `git
  merge --ff-only`, but a worker that trusts quickmerge's own "✅ Landed" message without independently verifying via
  `git merge-base --is-ancestor <sha> origin/<branch>` would silently lose the change and falsely believe it shipped.
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quickmerge, git, data-loss, sentinel, ci-cd]
related: []
created: 2026-07-31
parent_epic: infrastructure_master
priority: P1
source: [features_service_coverage_and_script_canon_2026_06_10.md script-canon sweep, slot 10 session 2026-07-31]
assigned_vm: planning
resolved_by: >-
  Both todos done: STAGE 5 no-regression guard shipped unified-trading-pm@f93a618e6 (6 new hermetic bats tests, all 14
  pre-existing tests unaffected); RULES.md/worker.md verification-step docs added unified-trading-pm@cb1d787ad.
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

> **🗄️ ARCHIVED 2026-07-31** — both todos are `[x]`, zero remaining, `locked_by:` empty. Per
> `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`, a doc with every todo done archives
> immediately.

## What I found

Working `unified-api-contracts` (a repo with heavy concurrent commit traffic from other slots this session), I hit the
same failure pattern 3 separate times:

1. Committed a local change (e.g. `64049305 chore(scripts): stamp lifecycle marker on scripts/__init__.py`) on top of
   the then-current HEAD.
2. Ran `bash scripts/quickmerge.sh "<msg>" --agent --files 'scripts/__init__.py'`.
3. Quickmerge logged
   `[unified-api-contracts] ⏳ sentinel invalid (HEAD moved — a peer likely pushed) — retry 1/3 in Ns`, then
   `re-gating (regenerating the Pass-1 sentinel for the current tree)...`, ran a fresh full QG pass, and eventually
   printed `✅ Landed on live-defi-rollout.`
4. **The commit was NOT actually on `origin/live-defi-rollout`.** `git log -1 --oneline` on HEAD showed a DIFFERENT
   (peer's) commit as the tip, and `git merge-base --is-ancestor <my-sha> origin/live-defi-rollout` returned false.
5. `git reflog` showed the true sequence: at some point in the retry loop, the branch pointer was reset directly to
   `origin/<branch>` (`branch: Reset to origin/live-defi-rollout` reflog entries), which silently dropped my commit from
   the branch tip. My commit object itself survived (dangling, recoverable via reflog + `git merge --ff-only`) — but if
   I had trusted the "✅ Landed" message and moved on, the change would have been lost with zero visible error.

On the 2nd occurrence, the reflog showed quickmerge had actually done the RIGHT thing first — a proper
`pull --rebase --autostash origin live-defi-rollout` that correctly rebased my commit onto the new peer tip (producing a
new sha, still containing my change) — and then a SUBSEQUENT `branch: Reset to origin/live-defi-rollout` discarded even
that correctly-rebased commit. So the reset isn't just "instead of rebase" — it can fire even AFTER a successful rebase,
as an apparently unconditional re-sync step somewhere later in the retry/re-gate flow.

Separately (related, not identical): a fresh standalone `quality-gates.sh` run on a repo whose content-hash matches a
prior green run hits the (intentional, documented "H5") content-sentinel HIT path, which correctly skips re-running
tests but ALSO skips refreshing `.qg_last_passed_sha` — so if that content was originally hashed on a DIRTY (pre-commit)
tree, the SHA sentinel can permanently lag behind a legitimate new commit with identical content, triggering the same
"sentinel invalid" retry path on every future quickmerge attempt. Workaround used this session: overwrite
`.qg_content_sentinel` with a dummy value to force a genuine re-run. Real fix: commit BEFORE ever running
`quality-gates.sh` (already the documented HARD RULE in `unified-trading-pm/agents/RULES.md` — my own violation of that
rule triggered this secondary issue, not a script bug).

## Why it matters

This is silent data loss with no error surfaced to the worker unless they independently verify against `origin/<branch>`
after every `--agent` quickmerge call — which is not currently a stated requirement anywhere in
`RULES.md`/`worker.md`/`SUB_AGENT_MANDATORY_RULES.md`. Any worker on a high-churn shared repo (this session:
`unified-api-contracts`, `deployment-service`) is at risk of quietly losing committed work while reporting it as
shipped. This is exactly the class of incident the workspace already tracks precedent for
(`shared_clone_concurrent_commit_message_swap_2026_07_28.md`) but the destructive-reset mechanism itself does not yet
have a fix or a documented safe workaround.

## Recommended decision

- [x] ✅ [SCRIPT] P1. **DONE 2026-07-31.** Locate the branch-reset call inside `quickmerge.sh`'s sentinel-invalid
      retry/re-gate path (search for `git reset` / `Reset to origin` near the `sentinel invalid (HEAD moved` log line)
      and change it to preserve local commits — either skip the reset when local HEAD is a strict descendant of the
      pre-retry state (nothing to lose), or always rebase (never hard-reset) onto the new origin tip before re-gating.
      Repo: unified-trading-pm. **Investigation finding**: no literal `git reset` call exists anywhere in
      `quickmerge.sh`, and the sentinel retry loop itself (near the "sentinel invalid" log line) only calls
      `_qm_stage_0_4_not_behind_gate` (pull --ff-only / pull --rebase --autostash, both non-destructive) — matching this
      doc's own "somewhere later in the retry/re-gate flow... apparently unconditional" caveat (the author couldn't pin
      the exact line either, only the reflog symptom). Found the operationally-identical anti-pattern
      (`checkout -B <branch> origin/<branch>`, which produces the exact "branch: Reset to origin/<branch>" reflog
      signature) unprotected in **STAGE 5**'s branch-selection block (both the `--dep-branch` and manifest-branch arms)
      — the SAME anti-pattern already flagged + partially fixed once before in `cascade_dep_branch` (2026-07-22,
      `quickmerge_silently_reset_unpushed_commit_2026_07_22.md`), but that fix only covered the cascade function, not
      this second occurrence. Rather than patch the two `checkout -B` call sites individually (which only protects
      against loss FROM those two exact lines, and the precise trigger condition for the sentinel-invalid case remains
      unconfirmed), shipped a **root-cause-agnostic safety net** (`unified-trading-pm@f93a618e6`): a QG-certified-commit
      snapshot (`_QM_PRE_STAGE5_HEAD` + `_QM_PRE_STAGE5_BRANCH`) taken the instant Stage 3 (quality gates) finishes,
      verified via `git merge-base --is-ancestor` immediately after STAGE 5's branch-checkout block, scoped to fire only
      when `$BRANCH` is the SAME branch name we snapshotted (a genuinely new PR branch off `origin/main` not containing
      it is expected, not a regression). On detection: preserves the lost commit to
      `refs/wip-preserve/quickmerge-stage5-regate-<sha12>` (mirroring the cascade fix's own preserve-ref convention) and
      hard-fails with an explicit recovery command, instead of silently proceeding to push. This catches the failure
      class regardless of which exact code path causes it (the two known `checkout -B` sites, or anything else that
      might move the branch pointer during STAGE 5). 6 new hermetic bats tests
      (`tests/test_quickmerge_stage5_no_regression_guard.bats`, real local git fixtures — no network): the guard fires +
      durably preserves on a literal repro of the destructive `checkout -B` call, stays silent on the safe
      plain-checkout path, stays silent on genuine new-branch creation, and stays silent when nothing was snapshotted.
      All 14 pre-existing `test_quickmerge_dep_tier_gate.bats` tests still pass unchanged (no regression). `bash -n`
      syntax-clean.
- [x] ✅ [DOC] P2. **DONE 2026-07-31 — `unified-trading-pm@cb1d787ad`.** Add an explicit post-`--agent`-quickmerge
      verification step to `RULES.md` § 2 / `worker.md` § DONE:
      `git fetch origin <branch> --quiet && git merge-base     --is-ancestor <your-sha> origin/<branch>` — treat a "✅
      Landed" message as unverified until this check passes; on failure, recover via `git reflog` +
      `git merge --ff-only <sha>` and retry. Repo: unified-trading-pm. Added to `agents/RULES.md` § 2 (right after the
      ship-loop code snippet) and `agents/worker.md` § DONE (new step b1, between capturing the SHA and the cross-repo
      plan-flip step), both cross-referencing the STAGE 5 no-regression guard shipped for the sibling `[SCRIPT] P1` todo
      as the mechanical belt to this manual-check suspenders. Independently verified via `git merge-base --is-ancestor`
      against `origin/live-defi-rollout` before this flip (practicing the exact discipline being documented).
