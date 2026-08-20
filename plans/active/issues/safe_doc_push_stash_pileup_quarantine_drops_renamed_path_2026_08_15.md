---
doc_type: issue
title:
  safe-doc-push.sh's stash-pileup quarantine re-stage retries a rename's OLD path, which no longer exists — 6/6 attempts
  fail
summary: >-
  Hit live 2026-08-15 archiving an issue doc (git mv plans/active/issues/<x>.md -> plans/archive/issues/<x>.md, staged
  as a rename). scripts/dev/safe-doc-push.sh detected 16 accumulated autostash/safety-snapshot entries, decided the
  chain was "extreme," and quarantined the current dirty tree into a NEW named stash before its pull — but the
  quarantine-then-restage retry loop calls `git add <old-active-path>` on every attempt (1-6), and the old path no
  longer exists on disk once a rename is staged (git mv already removed it), so every attempt fails with "pathspec did
  not match any files" and the script exhausts all 6 retries and exits non-zero. The staged rename itself was never
  actually lost (git status still showed it intact after the failed run), so this is a false-failure / retry-loop bug,
  not a data-loss one — but it defeats safe-doc-push for any archival (git mv) commit whenever a slot's stash list has
  grown past the quarantine threshold, forcing a manual `git commit --only` fallback (which is documented as sanctioned
  in plan-completion-and-archival-discipline.md, so the workaround was safe, but the primary tool should not fail here).
status: open
nature: issue
asset_group: [infrastructure] # corrected 2026-08-19 (ag-closeout-audit cross-cutting, Phase 1 Workflow) -- was [cross-cutting]; a safe-doc-push.sh git-tooling bug, not data-pipeline scope
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [safe-doc-push, plan-hygiene, archival, git, tooling-bug]
related:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/issues/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-15"
last_updated: 2026-08-20
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
assigned_role: infra
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
source:
  measured shipping quickmerge_first_early_exit_missing_unpushed_commits_carveout_2026_08_15.md's own archival commit
  (slot-14)
drift_direction: advance-code
depends_on: []
context_scope:
  [
    scripts/dev/safe-doc-push.sh,
    /plans/active/issues/safe_doc_push_extreme_stash_quarantine_drops_renamed_file_content_2026_08_15.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/issues/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md,
  ]
---

# safe-doc-push.sh's stash-quarantine retry loop can't re-stage a rename (old path is gone)

## What I found

`bash scripts/dev/safe-doc-push.sh "<msg>" --files '<old-active-path> <new-archive-path>'` archiving a `git mv`'d issue
doc, on a slot whose `git stash list` had accumulated 16 entries:

```
⚠ 16 autostash/safety-snapshot entries in the stash list — the autostash CHAIN may be active.
🛑 16 entries is extreme — quarantining current dirty tree into a named stash BEFORE the pull...
── attempt 1/6 ──
❌ could not stage named files -- 'git add' failed for a non-lock reason:
fatal: pathspec '<old-active-path>' did not match any files
── attempt 2/6 ── (same) ... 6/6 all fail identically
❌ Exhausted 6 attempts.
```

The named `--files` list correctly includes BOTH the old and new paths (per this workspace's own rename-deletion
convention). But once the tree is quarantined into a stash and the script tries to re-stage from the restored/ popped
state, its `git add` call is (apparently) issued against the old-active path unconditionally, without checking whether
that path still exists on disk — which it doesn't, because `git mv` already removed it before the script ever ran. Every
one of the 6 retry attempts hits the identical `fatal: pathspec ... did not match any files` and the loop never
succeeds.

**Not data loss**: after the failed run, `git status --porcelain` still showed the rename intact and correctly staged
(`RM <old-path> -> <new-path>`), so the quarantine-then-restore round-trip itself worked — only the re-stage-and-commit
step is broken for a renamed path. Workaround used: `git commit --only -m "<msg>" -- <old-path> <new-path>` directly
(the sanctioned fallback shape per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § "archival
commit itself"), which committed and pushed cleanly on the first try with all pre-commit hooks green.

## Why it matters

Any archival (`git mv`) commit on a slot whose stash list has grown past the quarantine threshold cannot ship via the
primary `safe-doc-push.sh` path at all — it fails deterministically, not intermittently, so every such commit on an
affected slot has to fall back to the manual `git commit --only` shape. This is the SAME class of gap the
plan-completion-and-archival-discipline.md doc already documents for the isolated-worktree copy path (renames needing
explicit deletion propagation) — this is a second, distinct place in the same script where a rename's old-path deletion
isn't accounted for, this time in the stash-quarantine retry loop rather than the isolated worktree copy step.

## Recommended decision

Fix the retry loop's `git add` call to skip (or `git rm --cached`, if needed) any named path that is absent from the
working tree AND already staged as the source side of a rename — mirroring the deletion-propagation fix already shipped
for the isolated-worktree copy path. Add a regression test that stages a `git mv` under a simulated high-stash-count
quarantine trigger and confirms the retry loop succeeds instead of exhausting.

## Open work (tracked todos)

- [ ] [BACKEND] P2. In `unified-trading-pm/scripts/dev/safe-doc-push.sh`, fix the stash-quarantine re-stage retry loop
      so a `--files` path that is the OLD side of an already-staged `git mv`/rename (absent on disk, present only as the
      staged deletion half of a rename) is not re-`git add`ed as if it were a plain modified file — skip it, or resolve
      it the same way the isolated-worktree copy-and-rm fix already does. Add a regression test: stage a `git mv`
      archival rename, force the quarantine path (16+ synthetic stash entries), confirm the retry loop succeeds instead
      of exhausting all 6 attempts. (repo: unified-trading-pm)
- [ ] [DATA] P3. **Re-derive and reapply a lost citation-fix edit to
      `/plans/active/cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md`.** (a KEEP-NA-STALE-DUPLICATE checkbox
      pointing at wherever the corresponding item's real extraction landed) — dropped by the SEVENTH data point below,
      the exact content was never committed and is not preserved anywhere outside this todo's own description. The
      doc is currently 1092L, over the 1000-line hard cap (pre-existing, not caused by the lost edit, which was
      net-zero lines) — `check_line_caps.sh` blocks ANY commit touching it until it's split, so this can't land via
      the normal path regardless; split it first (a separate, standing problem — grep `check_line_caps.sh`'s own
      output for the current split candidates), then re-run a citation check against its open items before reapplying.
      (repo: unified-trading-pm)

- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries).

## Progress Log

- **na-eligibility-audit 2026-08-17** [body-hash:b5cdd939b6b5fc0a]: KEEP-NA, valid -- Todo 1 (stash-quarantine retry-loop fix) is a standing ruling: an earlier same-day pass proposed RECLASSIFY_WHOLE, overridden on conflict-check as an actively-worked, state-dependent/elusive repro bug across 6+ investigation passes -- not re-litigated. Todo 2 (re-derive a lost citation-fix edit to cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md, added after that ruling) is a new, genuinely compound item (split an over-line-cap doc + re-derive lost content) -- moderate-confidence MISCLASSIFIED_LIKELY_AO_ELIGIBLE flag for a future pass, P3/low urgency, not acted on this run. Cross-cutting tranche audit.
- **na-eligibility-audit 2026-08-17 (slot 29/agt-be514e), SEVENTH data point, further new variant**: a plain modified
  file (not a rename) deliberately excluded from a `safe-doc-push.sh` `--files` list via `git restore --staged`
  (correctly leaving its working-tree content intact per this repo's own prescribed pattern) survived ONE
  quarantine-then-pull round-trip intact, then was silently dropped (reverted to exactly `origin`'s content, zero
  trace) by a SECOND quarantine cycle during a later push attempt in the SAME session — `git diff origin/...` showed
  byte-for-byte match afterward, and neither attempt's log named the file in any "restored stale content" or similar
  self-heal message the way the renamed-path variant does. So the failure isn't confined to renames: the quarantine
  mechanism can silently drop ANY dirty file not in the current run's `--files`, across repeated cycles, with no
  warning printed at all in this variant (contrast the renamed-path variant, which at least self-detects and logs).
  Concrete cost: one real, small, uncommitted edit lost (see the new P3 todo above) — low-stakes this time, but the
  mechanism doesn't distinguish low- from high-stakes content.
- **na-eligibility-audit 2026-08-19** (cross-cutting tranche): KEEP-NA, valid — 2 open todos: todo 1 (stash-quarantine retry-loop fix) carries an explicit standing ruling — an earlier same-day RECLASSIFY_WHOLE proposal was overridden on conflict-check as an actively-worked, state-dependent/elusive. (1/2 items tagged MISCLASSIFIED_LIKELY_AO_ELIGIBLE for next-run reassessment.)
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries).
