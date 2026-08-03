---
doc_type: issue
title: >-
  Stale `instruments-service-agentwork-sports-2026-07-13/` scratch clone was NOT deleted as instructed — its tracked
  work is provably already shipped, but 10 lingering stash entries (~5,000 lines of diffs spanning 2026-07-09..07-25)
  are unproven-unpushed WIP and deleting the directory would drop them irrecoverably
summary: >-
  Operator instruction 2026-07-30 was "delete the stale scratch clone, but FIRST confirm nothing unpushed; if it has
  real unpushed work, do NOT delete it, report that instead." The confirmation step FAILED OPEN on the stash stack. The
  clone's tracked content is clean: its one non-remote branch commit (`bc53bafe`, the catalogue-enumeration-gap script +
  test) and its one untracked file (`sports_attempted_failed_residual_closer_2026_07_13.py`) are BYTE-IDENTICAL to
  versions already on `origin/live-defi-rollout` in the real `instruments-service` clone (`f6f16785` and `98e7a784`
  respectively) — verified by diff, zero delta. But `git stash list` holds 10 entries dated 2026-07-09 through
  2026-07-25 (2 named checkpoints + 1 `quickmerge-36591` + 7 bare `autostash` residue) totalling roughly 5,000 lines of
  diff across adapters, goldens, orchestrator internals and docs. NONE of the 10 reverse-apply cleanly against the
  current `instruments-service` tree, so none is provably already-shipped — though three weeks of surrounding drift is
  sufficient on its own to explain a failed context match, so that is NOT evidence they contain unique work either. It
  is simply unproven in both directions. Per the operator's own stated condition, and per the workspace HARD RULE that
  destroying a stash is UNRECOVERABLE, the directory was left in place (1.2 GB) pending a ruling. The QG false-positive
  that motivated the deletion is independently FIXED and no longer depends on this directory going away.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm, instruments-service]
scope: [engineer, admin]
tags: [cleanup, git, stash, scratch-clone, quality-gates, disk]
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /cursor-configs/SUB_AGENT_MANDATORY_RULES.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/ag_closeout_audit_infra_parked_2026_08_03.md,
  ]
created: 2026-07-30
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.1
assigned_role: NA
drift_direction: flat
source: ["2026-07-30 operator instruction to delete the stale scratch clone (infra-methodology fix pass)"]
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /cursor-configs/SUB_AGENT_MANDATORY_RULES.md,
    agent-orchestrator/scripts/hooks/block_destructive_commands.py,
    scripts/quality_gates/check_repo_docs_ssot.py,
    /plans/epics/infrastructure_master.md,
  ]
---

# Stale agentwork scratch clone — deletion blocked on unproven stash WIP

Directory: `unified-trading-system-repos/.tabs/3/instruments-service-agentwork-sports-2026-07-13/` (1.2 GB, local to
slot 3 only — never pushed anywhere, not part of the per-slot worktree model).

## What was verified (all measured this session, nothing inferred)

| Surface                                           | Finding                                                                                                    | Safe to drop?                                                              |
| ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `git status --porcelain`                          | 1 untracked file: `scripts/backfill/sports_attempted_failed_residual_closer_2026_07_13.py`                 | YES — byte-identical to `origin/live-defi-rollout` (`98e7a784`)            |
| Branch `agentwork/sports_residual_fix_2026_07_13` | 0 commits not reachable from a remote                                                                      | YES — nothing unique                                                       |
| Branch `backup-catalogue-gap-script-2026-07-23`   | 1 commit `bc53bafe` (measure script 407L + test 298L)                                                      | YES — both files byte-identical to `origin/live-defi-rollout` (`f6f16785`) |
| `refs/stash` (10 entries, 2026-07-09..07-25)      | ~5,000 lines of diff: adapters, expected-universe goldens, orchestrator internals, `docs/*_INSTRUMENTS.md` | **UNKNOWN — this is the blocker**                                          |
| `live-defi-rollout` / `main` local branches       | behind remote (2 / 1573), no local-only commits                                                            | YES                                                                        |

`git log @{u}..` on the checked-out branch reports `no upstream configured` (an `agentwork/` branch never had one), so
the operator's suggested command alone does not answer the question — `git rev-list --count --all --not --remotes` is
the check that does, and it returns 3 (the one branch commit above + the 2 commit objects behind `stash@{0}`).

## Why this is not just "drop the stashes"

`git stash drop` on foreign/unproven WIP is UNRECOVERABLE and is a named HARD RULE in both
`/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` § Foot-guns and `/cursor-configs/CLAUDE.md` § Multi-agent safety.
Deleting the directory drops all 10 at once with no undo. The already-applied test (`git apply --reverse --check` of
each stash's diff against the current `instruments-service` tree) came back negative for all 10 — but that test has a
known false-negative mode here: three weeks of surrounding churn defeats the context match even for content that DID
ship. So the honest verdict is **unproven, not unsafe** — which under the operator's own stated condition ("if it has
real unpushed work, do NOT delete it") means: do not delete.

## The motivating QG failure is already fixed, independently of this

The stated reason for the deletion was that this directory read as a real repo to
`scripts/quality_gates/check_repo_docs_ssot.py` (its `_iter_repo_docs()` `iterdir()`s every workspace sibling), so its
frozen 3-week-old `docs/` contributed 6 non-baselined violations and failed the gate. That is fixed at the source: the
script now skips `*-agentwork-*` / `scratch-clone` / dot-prefixed directories (`_is_scratch_clone()`), mirroring
`check_frontmatter_schema.py`'s `.claude/`-worktree exclusion. **The gate is green with the directory still present** —
so nothing is blocked on this decision; the only remaining cost is 1.2 GB of disk.

## Todos

- [x] [OPERATOR] P2. Rule on how to retire `.tabs/3/instruments-service-agentwork-sports-2026-07-13/`. **Ruled
      2026-07-30: option A, bundle-then-delete.**
- [x] [SCRIPT] P3. Bundle + verify. `git bundle create --all refs/stash` was tried FIRST and found to only capture
      `stash@{0}` — `refs/stash` is a single ref, and entries 1-9 exist only in its reflog, which plain `git bundle`
      does not walk. Fixed by materialising a temporary named ref per entry (`refs/stash-preserve/0..9`, one
      `git update-ref` per `git rev-parse stash@{N}`), bundling those 10 refs explicitly, then deleting the temporary
      refs (the objects stay reachable via the bundle regardless; the source repo's real `refs/stash` reflog is
      untouched either way). **Verified independently**, not just via `git bundle verify` (which only checks internal
      consistency, not which commits are actually payload): unbundled into a disposable fresh repo and ran
      `git cat-file -e <sha>` for all 10 stash commit SHAs — all 10 PRESENT. Bundle path:
      `.tabs/3/stash-bundles/instruments-service-agentwork-sports-2026-07-13-stashes.bundle` (67.8 MB, local-only, not
      git-tracked — a 94% reduction from the 1.2 GB source directory). **Done when** criteria met: bundle verifies, path
      is cited here (above), all 10 stash SHAs confirmed present by direct unbundle-and-cat-file test (not just
      `bundle verify`).
- [ ] [OPERATOR] P2. **Done-when NO LONGER SATISFIABLE AS WRITTEN — see 2026-08-03 Progress Log entries before acting.**
      Original text: delete `.tabs/3/instruments-service-agentwork-sports-2026-07-13/` now that its 10 stash entries are
      durably bundled + verified above. **This step cannot be done by an agent**: the workspace's own
      `agent-orchestrator/scripts/hooks/block_destructive_commands.py` PreToolUse guardrail unconditionally blocks any
      `rm -rf`/recursive delete for autonomous workers (by design, with no override — its own docstring says not to
      circumvent it), and this is exactly the "filesystem command, no SDK equivalent" case its own block message names
      as an operator-escalation, not a workaround. Original done-when: directory is gone,
      `du -sh .tabs/3/stash-bundles/` confirms the bundle is the only remaining trace. **As of 2026-08-03, BOTH the
      directory AND the bundle are already absent** (see Progress Log) — the directory-gone half is met, but the
      bundle-survives half is NOT, and no agent here performed this delete. Do NOT flip this to `[x]` until the
      `ag_closeout_audit_infra_parked_2026_08_03.md` finding-11 investigation (durable relocation vs. genuine loss of
      the 10 stash entries) resolves — flipping now would silently certify a done-when that isn't actually met.

## Progress Log

- **na-eligibility-audit 2026-07-31**: KEEP-NA, valid (infra tranche, dispatch agt-676f1e) — sole remaining open todo is
  explicitly `[OPERATOR]`-tagged and its own text states the guardrail (`block_destructive_commands.py`) unconditionally
  blocks any agent from running it, no override. Unambiguous human-only action. No other action.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **na-eligibility-audit 2026-08-02** (infra tranche, incremental run): **KEEP-NA, valid — unchanged from the 2026-07-31
  verdict.** In scope only because a context-scout backfill touched the file; no content change since. Read end-to-end;
  `grep -cE '^- \[ \]'` = **1**, matching this verdict's item count. The sole remaining todo is `[OPERATOR] P2` and its
  own text states the blocker precisely: `block_destructive_commands.py`'s PreToolUse guardrail unconditionally refuses
  any recursive delete for autonomous workers, with no override and no §3a-style reversibility carve-out (that carve-out
  is GCS-specific; this is a local filesystem delete). Unambiguous human-only action. Note for a future run:
  `issues/ag_closeout_audit_infra_parked_2026_07_31.md` finding 2 observes this directory already absent from a sandbox
  `.tabs/3`, but that observation is explicitly non-authoritative for the real target host and does not license flipping
  this checkbox.
- **na-eligibility-audit 2026-08-03** (infra tranche, dispatch agt-a41abf): **KEEP-NA, valid — but content updated, do
  not treat as a routine unchanged-refresh.** In scope only because a context-scope backfill touched the file (2 lines
  appended to `context_scope:`, confirmed via `git show` — no content/todo/status change from that commit itself).
  However, `ag_closeout_audit_infra_parked_2026_08_03.md` finding 11 (same day, different scheduled process)
  independently discovered that the "durably bundled" stash backup this doc's sole open todo depends on is now ALSO
  absent, not just the source directory. Independently re-verified here before writing this marker (not trusting the
  other doc's claim secondhand): direct `ls` on both `.tabs/3/instruments-service-agentwork-sports-2026-07-13/` and
  `.tabs/3/stash-bundles/` — both "No such file or directory"; a bounded
  `find /home/ubuntu/unified-trading-system-repos/.tabs -maxdepth 3` sweep (all slots, not just slot 3) for either name
  — zero hits anywhere; confirmed this is the genuine long-running shared host (`ip-172-31-5-118`, uptime 5d9h, load
  24-26 — consistent with many concurrent agent slots, not an ephemeral sandbox), same identity check finding 11 itself
  ran. Updated the sole open todo's text above to flag its done-when as no longer satisfiable as written and
  cross-referenced finding 11's pending `[OPERATOR]` investigation rather than flip the checkbox myself — whether this
  is a durable off-host relocation or a genuine loss of 10 real stash entries (~5,000 lines of unpushed WIP) is external
  knowledge no worker session has, exactly the operator-gated judgment call this doc's own `[OPERATOR]` tag already
  anticipated, just not the specific gap it originally named. Verdict stays KEEP-NA (if anything, more clearly
  operator-gated now, not less) — this is a content-accuracy update, not a reclassification.
