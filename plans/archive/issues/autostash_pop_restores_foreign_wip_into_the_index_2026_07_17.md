---
doc_type: issue
title:
  git pull --rebase --autostash silently restores FOREIGN dirty files into the INDEX, so a by-name `git add` still
  commits another agent's uncommitted work — the stage-by-name rule gives no protection in a shared checkout
summary:
  The multi-agent safety rule is "stage by name, never git add . / -A", on the assumption that naming your own files is
  sufficient to keep a concurrent agent's uncommitted work out of your commit. In a shared per-slot checkout it is NOT.
  git pull --rebase --autostash (the reconcile step quickmerge STAGE 0.4 and every drift-recovery recipe tell you to
  run) stashes the WHOLE dirty tree - including files owned by other agents - and the pop restores them into the INDEX,
  i.e. already staged. A subsequent git commit commits the index, so it sweeps up every foreign file regardless of what
  you passed to git add. Measured 2026-07-17 - commit unified-trading-pm 1a59516af was intended to add ONE new issue
  doc; it landed with 3 files, silently publishing another agent's in-progress plan edits (157 insertions / 125
  deletions of real content, not a reformat) and a brand-new issue doc they had not yet committed, under this slot's
  authorship and commit message. No data was lost - the content is intact on origin - but their WIP was published
  earlier than intended and mis-attributed. The existing codex guidance only covers the autostash CONFLICT path ("rebase
  --abort + stash by name"); this is the NON-conflict happy path, which is why it is easy to miss. The pre-commit "git
  diff --cached --stat (NO path arg)" inspection step is the one control that would catch it, and it only works if the
  agent actually reads the file list rather than the summary line.
status: resolved
resolved_by: "unified-trading-pm@72bdb200e/@9669098c3/@461a5a0bc — pre-commit case, post-commit case, docs fold"
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [multi-agent-safety, git, autostash, shared-checkout, foreign-wip, process, big-finding, commit-hygiene]
related: [/plans/archive/issues/sports_fixture_round_not_captured_competition_phase_unknown_2026_07_17.md]
created: 2026-07-17
source:
  - Self-caught 2026-07-17 while committing an issue doc to unified-trading-pm, then flagged by the operator ("sure flag
    it"). Found by actually reading `git show --stat` on the pushed commit rather than trusting that `git add
    <one-file>` had scoped it - the pre-commit status check had shown the foreign files as "not staged", which is what
    made the sweep invisible until after the push.
assigned_vm: planning
assigned_role: infra
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
drift_direction: advance-code
parent_epic: agent_operating_framework_master
execution_scope: orchestrator-agent
depends_on: []
last_updated: 2026-07-17
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/issues/sports_fixture_round_not_captured_competition_phase_unknown_2026_07_17.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md,
    scripts/quickmerge.sh,
  ]
---

# `--autostash` restores foreign WIP into the index → by-name `git add` does not scope your commit

> **🟢 RESOLVED 2026-08-02** — all 3 decided fixes shipped (pre-commit case, post-commit case, docs fold):
> `unified-trading-pm@72bdb200e`/`@9669098c3`/`@461a5a0bc`.

## The failure, measured

`unified-trading-pm@1a59516af` was meant to add one new file. It shipped three:

```
157  125   plans/active/data_status_page_ux_and_canonicalisation_2026_07_16.md   <- FOREIGN, real content
187    0   plans/active/issues/sports_fixture_round_..._2026_07_17.md            <- mine (intended)
118    0   plans/active/issues/tradfi_instrument_type_migration_..._2026_07_17.md <- FOREIGN, new file
```

The sequence that produced it (all of it "correct" per the current rules):

```bash
git pull --rebase --autostash origin live-defi-rollout   # reconcile — mandated by the drift recipe
git add plans/active/issues/<my-one-doc>.md              # stage BY NAME — the rule
git commit -F msg                                        # commits the INDEX → swept 2 foreign files
```

## Why the stage-by-name rule does not protect you

`--autostash` = `git stash` + restore. The restore re-applies the stashed changes **and their index state**. Foreign
files that were merely dirty in the working tree come back **staged**. `git commit` then commits the whole index — the
`git add <file>` you ran is irrelevant, because those foreign paths are already in it.

This is the **non-conflict** path. Existing guidance (`/codex/05-infrastructure/per-tab-worktrees.md`, CLAUDE.md
"Multi-agent safety") only addresses the conflict path — _"autostash conflict → `rebase --abort` + stash by name (never
`git stash drop` foreign WIP)"_ — so an agent doing everything right, on the happy path, still sweeps.

It is invisible pre-commit: `git status` correctly reports the foreign files as **"Changes not staged for commit"**
right up until the pull, and the post-pull index is never re-inspected.

## Impact

- **Not data loss.** Content is intact and on origin.
- **Mis-attribution + premature publication.** Another agent's in-progress work is published under your slot's name and
  commit message, before they chose to ship it. On a shipping-gated repo that can push someone else's half-finished
  change past a gate they intended to run themselves.
- **Silent.** Nothing fails. The only tell is reading `git show --stat` AFTER the push.
- The blast radius scales with how dirty the shared checkout is — and PM is routinely dirty across many agents.

## Decided fix (2026-08-01, operator decision — was "Candidate fixes (not yet decided)")

> **The fix splits on whether you've already committed your own work at the moment you reconcile — that's the variable
> that decides fast-forward eligibility, not file-content overlap.** Verified empirically 2026-08-01: a plain `git pull`
> (merge, no rebase) with a dirty non-overlapping file and ZERO local commits ahead of origin is a true fast-forward (no
> new commit object at all); `git pull --rebase` with that same dirty file REFUSES outright regardless of overlap
> (rebase requires an unconditionally clean tree — that's why `--autostash` exists, and why its restage-on-pop behavior
> is the actual hazard). But the instant a local commit already exists ahead of origin (the real "behind-remote" case
> CLAUDE.md's drift recipe targets), a merge-pull is NOT free anymore — it produces a real 2-parent merge commit even
> with zero file overlap, since FF-eligibility is a commit-graph property, not a content one. So the fix is two
> different mechanisms for two different moments, not one blanket replacement.

- [x] ✅ [DEVOPS] P2. **Pre-commit case (haven't committed your own work yet): skip forced rebase.** — **DONE
      2026-08-01, `unified-trading-pm@72bdb200e`.** `scripts/quickmerge.sh` STAGE 0.4 (`_qm_stage_0_4_not_behind_gate`):
      when `git pull --ff-only` fails AND `_QM_AHEAD` is `0`, the gate no longer falls through to
      `git pull --rebase --autostash` — since there is no local commit for rebase to replay, an ff-only failure at
      ahead=0 can only be a working-tree content overlap, so it now reports `PRECOMMIT_WORKING_TREE_CONFLICT` and blocks
      cleanly instead (no stash ever created). The `ahead>0` branch is unchanged (that's the next todo below). Verified
      in a sandboxed clone: ahead=0 + non-overlapping dirty file still fast-forwards cleanly (unaffected); ahead=0 +
      genuine overlapping dirty file now blocks with zero stash activity, vs. the prior code which would have swept the
      whole dirty tree. shellcheck-clean, quality-gates.sh green.
- [x] ✅ [DEVOPS] P2. **Post-commit case (already have a local commit ahead of origin): keep `--rebase --autostash`**
      (this case is genuine commit-graph divergence, not FF-eligible, and rebase is what keeps `live-defi-rollout`
      linear instead of littering it with merge commits) **— but make the autostash-pop safe.** — **DONE 2026-08-02,
      `unified-trading-pm@9669098c3`.** Immediately after `git pull --rebase --autostash`, BEFORE any of this script's
      own `git add <files>`, `_qm_stage_0_4_not_behind_gate`'s post-commit branch (`scripts/quickmerge.sh` ~L746) now
      runs `git restore --staged . 2>/dev/null || true` unconditionally — it only unstages (never touches working-tree
      content, so it can't destroy anything), guaranteeing the index holds only what this run explicitly re-adds
      regardless of what the pop restaged. Verified in a sandboxed clone (peer commit landed on origin, local ahead=1,
      foreign tracked-file dirty edit present pre-rebase): the fix runs as a no-op-or-neutralizer either way the pop
      leaves foreign state (staged or merely working-tree-dirty on this git version) and never touches foreign file
      content. Simpler than the previously-floated `git stash push -- <my paths>` alternative (which needs knowing your
      own dirty paths up front) — dropped that alternative.
- [x] ✅ [DOCS] P2. Fold both halves into `/codex/05-infrastructure/per-tab-worktrees.md` + CLAUDE.md's Multi-agent
      safety block, replacing the current conflict-only guidance ("autostash conflict → rebase --abort + stash by name")
      with: (a) the pre-commit-case FF shortcut, and (b) the post-commit-case `git restore --staged .` step. Both docs
      are currently silent on this non-conflict happy-path hazard entirely. — **DONE 2026-08-02,
      `unified-trading-pm@461a5a0bc`.** `per-tab-worktrees.md`'s Reconciliation step 1 now case-splits by `ahead`-count
      (mirrors the shipped `_qm_stage_0_4_not_behind_gate` code: ahead=0 ff-only-or-`PRECOMMIT_WORKING_TREE_CONFLICT`,
      ahead>0 `--rebase --autostash` then `git restore --staged .` pre-add); a new "Non-conflict autostash-pop hazard"
      subsection (measured incident + both fix halves) is inserted right before the pre-existing conflict-only recovery
      subsection. CLAUDE.md's Multi-agent safety line updated to the same ahead=0/ahead>0 split, kept terse (landed at
      40,953 B, 7 B under the 40,960 B hard cap — `check_agent_rules_size_cap.py` verified green); full detail lives in
      the codex doc per the SSOT pointer already at the end of that paragraph.

**Not adopted** (considered, explicitly declined — recorded so neither is re-proposed without new cause): reordering the
existing pre-commit inspection alone (too weak solo — that exact rule already existed and the incident happened anyway);
a hard pre-commit guard hook diffing staged paths against an agent-supplied file list (real hardening, but its own build
with narrower coverage than the two mechanisms above — could be revisited later as its own P3, not required to close
this decision).

## Do NOT "fix" a sweep by reverting

Once pushed, the foreign content is the other agent's only committed copy of that work. A revert or force-push to "clean
up" the attribution **deletes their uncommitted work** — turning a cosmetic problem into real data loss, and
force-pushing a shared branch is independently banned. The correct response is: leave it, tell the operator, and let the
owning agent carry on (their tree simply shows those files as already-committed after their next pull).

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — the 4 open items sit under a section literally titled
  `Candidate fixes (not yet decided)`, and one (`[DOCS] P2`) is a `/codex/05-infrastructure/per-tab-worktrees.md` +
  CLAUDE.md edit, which is never autonomous. Already ruled the same way in
  `ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s operator-decision Deferred list.
- **2026-08-01 (operator decision session)**: Ruled on the "Candidate fixes" question after re-deriving root cause and
  verifying empirically (see the decided-fix banner above) that rebase's clean-tree requirement — not file overlap — is
  what forces `--autostash` into existence, and that a merge-pull is only cost-free pre-commit (zero local commits ahead
  of origin), not post-commit (where it would create real merge commits on `live-defi-rollout`). Decision: split by case
  — plain merge-pull pre-commit, `git restore --staged .` post-autostash-pop for the rebase/post-commit case, document
  both. Explicitly declined the reorder-only-inspection and hard-guard-hook candidates for now (see "Not adopted"
  above). Still `status: open` — the decision is made, the code/docs changes are not yet shipped.
- **na-eligibility-audit 2026-08-01** (autonomous, tranche `ao`, dispatch agt-8e95ca, slot 2): RECLASSIFY
  `NA -> planning`. The 2026-08-01 operator decision session above resolved the design fork the prior 2026-07-30 KEEP-NA
  verdict was based on — all 3 remaining todos are now bounded implementations of an already-decided fix (case-split
  criteria explicitly stated, doc-fold content pre-specified). Phase 2 conflict-check: grepped
  `restore --staged`/`autostash` and this doc's topic across every active `assigned_vm: planning` doc and this run's own
  finalize drafts — no competing claim found. Also corrected `assigned_role: devops` -> `infra` (`devops` does not match
  any entry in the live `agents/*.md` registry; `infra` is the closest real role for this per-tab-worktrees/CLAUDE.md
  git-mechanics fix).
- **context-scout 2026-08-01**: populated context_scope (2 entries).
- **infra worker 2026-08-01** (slot 16, task `autostash_pop_restores_foreign_wip_into_the_index-001`): shipped the
  pre-commit-case `[DEVOPS] P2` todo — `unified-trading-pm@72bdb200e`. Blocked mid-ship by an unrelated pre-existing
  gate (PM STAGE 1.5 dependency-alignment red, tracked in
  `pm_dependency_alignment_gate_blocks_all_code_pushes_execution_service_mtds_2026_08_01.md`, `[OPERATOR]`-gated);
  declared repo-blocker RB-be17edbd, operator authorized proceeding with that doc's recommended option (A), shipped as a
  separate commit `unified-trading-pm@4871d79fe`. Two remaining todos (post-commit `--restore --staged` safety + the
  docs fold) are untouched — out of scope for this task.
- **data_engineering worker 2026-08-02** (slot 6, task `autostash_pop_restores_foreign_wip_into_the_index-002`): shipped
  the post-commit-case `[DEVOPS] P2` todo — added `git restore --staged . 2>/dev/null || true` immediately after the
  successful `git pull --rebase --autostash` branch in `_qm_stage_0_4_not_behind_gate` (`scripts/quickmerge.sh` ~L746),
  before any of the script's own later `git add` calls. Verified in a sandboxed throwaway clone (peer commit landed on
  origin, local branch ahead=1 with its own committed file, plus a foreign tracked file dirty from another "agent" both
  staged and unstaged variants) that the restore only touches the index — foreign file content and the local committed
  file both survive intact — and is a safe no-op when the pop leaves nothing staged. `bash -n` + `shellcheck -x` clean
  (no new findings near the change; only pre-existing unrelated warnings elsewhere in the file). Remaining todo:
  `[DOCS] P2` fold into `/codex/05-infrastructure/per-tab-worktrees.md` + CLAUDE.md — out of scope for this task.
- **infra worker 2026-08-02** (slot 8, task `autostash_pop_restores_foreign_wip_into_the_index-003`): shipped the
  `[DOCS] P2` fold — the last remaining todo, closing this issue's decided fix end-to-end (both code halves were already
  shipped by the prior two workers above). All 3 todos now `[x]`; no `locked_by` — this doc is archival-eligible as a
  follow-up (left for the next plan-hygiene sweep, per the HARD RULE against bundling a checkbox flip with a `git mv`
  archival in the same commit).
