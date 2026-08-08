---
doc_type: issue
title: >-
  `git commit --only` (partial commit) path-scoping drops the delete side of a staged `git mv` rename — confirmed
  mechanism behind the 2026-08-06 create-only archival commits (dcf897c30, 7accf8ecf), DISTINCT from the prek keeper.rs
  root cause already closed in prek_patch_cache_replays_stale_diff_onto_unrelated_files_2026_07_29.md
summary: >-
  The prek_patch_cache doc's open [REVIEW] P1 asked whether the 2026-08-06 create-only reproduction (a
  `plans/archive/issues/` archival commit that created the new-path file but never removed the old-path duplicate —
  `unified-trading-pm@dcf897c30`; also `7accf8ecf` slot-6 orphan-wip, 160 adds / 0 deletes) was (a) the same
  already-fixed single-process keeper.rs stash/rollback bug, or (b) a distinct concurrent-multi-agent-index-mutation
  bug. Both ruled out by direct reproduction. The mechanism is a THIRD class, git-native and prek-independent: `git
  commit --only -m "<msg>" -- <new-path>` after a `git mv` commits the ADD side of the rename but silently EXCLUDES the
  DELETE side (the old path is not in the `--only` path list). The deletion stays staged in the index and the
  working-tree file stays deleted, so nothing downstream notices until the duplicate twin diverges. Reproduced
  create-only with the patched fork prek 0.4.12 running its full stash/restore cycle, and identically with NO prek
  installed (pure git). Plain `git commit` (full staged set) and `--only` listing BOTH old+new paths both produce proper
  renames. Concurrent partial commits interleave without index corruption and are NOT the cause; concurrent full commits
  abort loudly (index.lock), matching the slot-8 finding. Live corpus consequence: 5 active/archive duplicate pairs
  survive today, each diverged 15-34 diff lines. Prevents recurrence with a create-only guard + workflow fix.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [git, commit-only, partial-commit, rename, archival, create-only, docs-plans, tooling]
related:
  [
    /plans/archive/issues/prek_patch_cache_replays_stale_diff_onto_unrelated_files_2026_07_29.md,
    /plans/archive/issues/plan_health_tests_leak_real_slack_alerts_2026_07_24.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: 2026-08-06
author: slot-6
last_updated: "2026-08-06"
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: review
priority: P1
estimate_class: research
source: [prek_patch_cache_replays_stale_diff_onto_unrelated_files-002 review task, slot-6, 2026-08-06]
drift_direction: worsening-slowly
depends_on: []
locked_by:
resolved_by:
context_scope:
  [
    /scripts/plan-hygiene/check_create_only_archive_commits.py,
    /scripts/plan-hygiene/find_moved_doc_referrers.sh,
    /scripts/plan-hygiene/run_hygiene_sweep.sh,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# `git commit --only` drops rename deletions → create-only archival commits

## What I found

The mechanism is a git-native partial-commit path-scoping hazard, **not** prek and **not** concurrency.

**Reproduction (all on a scratch repo, driving a real `git commit` through prek's installed-hook path, matching the
production archival shape — `prek` on PATH = the patched fork `0.4.12`, sha256 `27993a6e...7c508` byte-matching
`IggyIkenna/prek@v0.4.12`'s `prek-x86_64-unknown-linux-musl` release asset):**

| Scenario | Command after `git mv active/foo.md archive/foo.md`                              | Result                                                            |
| -------- | -------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| A        | `git commit --only -m "archive" -- archive/foo.md` (patched prek, hook restages) | **CREATE-ONLY** (adds=1 deletes=0) — delete stays staged in index |
| B        | `git commit -m "archive"` (plain, full staged set, patched prek)                 | proper rename (R100)                                              |
| C        | `git commit --only -m "archive" -- archive/foo.md active/foo.md` (both paths)    | proper rename (R100)                                              |
| D        | `git commit --only -m "archive" -- archive/foo.md` (**NO prek**)                 | **CREATE-ONLY** (adds=1 deletes=0)                                |

Scenario A is the exact production shape the 2026-08-06 archival worker used (`git commit --only -- <exact paths>`, per
its own Progress Log finding 3). prek's "Unstaged changes detected, temporarily saving them to `<patch>`... Restored
unstaged changes from `<patch>`" cycle runs to completion in A and does **not** corrupt anything — the staged
rename-delete survives both the stash and the restore, sitting untouched in the index. The drop is purely git's `--only`
semantics: a partial commit builds a temp index = HEAD + staged changes **to the listed paths only**, so the deletion at
the unlisted `active/foo.md` path is excluded. Scenario D proves prek is not a prerequisite.

**Why this was miscast as "same mechanism" or "concurrent":**

- (a) same-as-this-doc → ruled out. The single-process keeper.rs stash/rollback bug this doc root-caused is **fixed on
  this host**: patched `0.4.12` fork binary in effect (sha256 match), and the corruption harness
  (`scripts/hooks/prek-keeper-fix/prek-corruption-harness.sh`) reports `clean=5 corrupt=0`. The create-only reproduces
  with no prek at all.
- (b) concurrent-multi-agent-index-mutation → ruled out. Two `git commit --only` processes raced on the same worktree
  (both exit 0, interleaved, prek cycles intact): each committed exactly its listed paths, no index corruption, no state
  loss — the create-only shape came solely from `--only` scoping. Two concurrent FULL commits: one aborts loudly
  (`nothing to commit` / exit 1) — the slot-8 index.lock finding, not a silent-corruption vector. Additionally, on this
  host (`ip-172-31-5-118`) unified-trading-pm is per-slot isolated (each `.tabs/<N>/unified-trading-pm` is its own clone
  with its own `.git`), so cross-slot concurrent index mutation on a shared worktree is not even structurally possible
  here — the doc's 2026-08-06 entry claim to the contrary does not hold on this host.

**Production instances — both create-only, both consistent with add-side-staged / delete-side-not-committed:**

- `dcf897c30` (harsh_pc main, 2026-08-06 16:10, "AO issue-doc sweep — archive 7 resolved"): 6 `A`
  `plans/archive/issues/` adds, **0** `D` entries. The sweep's OTHER archival commits the same day (`90bd02e28`,
  `1774a9d97`, `59dd15d8b`, `ec94443ff`, `9f7d4b020`) all landed as **proper renames** (R0xx) — so this is
  commit-specific command usage, not a systemic mechanism firing on every commit.
- `7accf8ecf` (slot-6 orphan-wip inheritance, this host, 2026-08-06 07:58): 160 `A`, **0** `D` — inherited WIP whose
  staged state had the archive adds but not the active-path deletions.

**Live corpus consequence (checked 2026-08-06):** 5 active/archive duplicate pairs survive today, each **diverged**
15-34 diff lines (both copies evolved independently since the create-only commit — the exact two-diverging-copies hazard
the prek_patch_cache doc warned about):

- `ao_dashboard_backlog_detail_queue_lag_e2e_flaky_2026_07_26` (34 diff lines)
- `backlog_detail_spec_queue_lag_sort_order_flake_2026_07_30` (15)
- `host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26` (18)
- `orchestrator_planregen_prune_wipes_backlog_on_transient_zero_derivation_2026_07_25` (16)
- `orchestrator_vm_swap_exhaustion_masked_as_cpu_2026_07_29` (17)

(The `7accf8ecf` twins were cleaned by later work; `plan_health_tests_leak_real_slack_alerts_2026_07_24.md` was fixed in
`a62bdd8ea`.)

## Why it matters

A create-only archival commit silently leaves a live `plans/active/issues/` twin that the rest of the fleet still reads
as "open/unresolved" (the AO dispatch backlog is derived from `- [ ]` todos in `plans/active/**`), while the
intended-canonical copy sits in `plans/archive/issues/`. The two then diverge — as all 5 current duplicates already have
— so a later unrelated edit to one copy produces contradictory docs (the exact failure `dcf897c30` caused for
`plan_health_tests_leak_real_slack_alerts`). Nothing in the ship path catches it today: `check_reference_paths.py` and
`find_moved_doc_referrers.sh` only look forward from the surviving path; no check verifies "archive copy added ⇒ old
path deleted in the same commit".

## Recommended decision

Treat this as a distinct failure class from the prek keeper bug (which stays closed): the create-only shape is a git
partial-commit usage hazard in the archival workflow. Fix the workflow (plain `git commit` after `git mv`, or `--only`
listing both paths), add a create-only guard so the shape hard-fails the gate, and reconcile the 5 live diverged
duplicates. Do NOT reopen the prek_patch_cache doc's single-process root cause — it was correctly fixed and this is not
a recurrence of it.

**Note — a sanctioned fix already ships:** `scripts/dev/safe-doc-push.sh` (added 2026-08-01, `0e48d252f`) is the
CLAUDE.md-sanctioned path for pure doc/plan-flips and commits with a plain `git commit` (full staged set, not `--only`),
so a `git mv` archival pushed through it lands as a proper rename. The archival workflow should route through it (or an
equivalent plain-commit path) rather than a bare `git commit --only -- <new-paths>`.

## Todos

- [x] ✅ [SCRIPT] P1. **Create-only archival-commit guard** — a check that, for any commit adding a
      `plans/archive/issues/*.md` file whose `plans/active/issues/*.md` twin exists in the commit's parent AND still
      exists in the commit's tree, hard-fails with a pointer to the two-path `--only` fix. Wire into
      `scripts/plan-hygiene/run_hygiene_sweep.sh` as a new check. Verify: fails on the 5 known live duplicates (all
      currently present), passes on a proper rename, passes on a clean corpus. (repo: unified-trading-pm) —
      unified-trading-pm@5bfe78fca (`check_create_only_archive_commits.py` + wired into `run_hygiene_sweep.sh` as a hard
      check). Verified: fails on the 5 known duplicate pairs at HEAD; `--commit` mode flags the create-only signature on
      `7accf8ecf`; scratch-repo reproduction confirms proper rename (`R100`) + clean corpus pass and the two-path
      `--only` fix clears it.
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-06 (slot-10) — 5 active duplicate twins removed.** Diffed all 5 pairs: archive
      copies are canonical/superset (status: resolved, ARCHIVED banner, CLOSED todo prefixes); pair 1
      (`ao_dashboard_backlog_detail_queue_lag_e2e_flaky_2026_07_26`) had unique active-only provenance (fix shipped as
      side-effect of `ao_done_categorization_display_and_quickmerge_gate`, sibling doc had credited it while checkboxes
      were unflipped) — merged into archive Progress Log. Satellite plan reference updated
      (`/plans/active/issues/host_saturation...` → `/plans/archive/issues/host_saturation...`). All 5 active twins
      `git rm`'d. Zero duplicate pairs verified corpus-wide post-removal. Original text: **Reconcile the 5 live diverged
      duplicate pairs** — for each of `ao_dashboard_backlog_detail_queue_lag_e2e_flaky_2026_07_26`,
      `backlog_detail_spec_queue_lag_sort_order_flake_2026_07_30`,
      `host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26`,
      `orchestrator_planregen_prune_wipes_backlog_on_transient_zero_derivation_2026_07_25`,
      `orchestrator_vm_swap_exhaustion_masked_as_cpu_2026_07_29`: diff active twin vs archive twin (15-34 diff lines
      each, both evolved), merge any unique active-only content into the archive copy, `git rm` the stale active
      duplicate, re-verify zero duplicate pairs corpus-wide. (repo: unified-trading-pm)
- [x] ✅ [SCRIPT] P3. **Archival-workflow fix** — update
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (and any runbook the archival ritual points
      to) to require, after any `git mv` archival: route the commit through `scripts/dev/safe-doc-push.sh` (plain
      full-staged-set commit) or, if a bare `git commit --only` is used, list BOTH old and new paths; and a post-commit
      `git status --porcelain` check confirming no staged deletions were left uncommitted. (repo: unified-trading-pm) —
      unified-trading-pm@4ad2f00f4. Added a new "The archival commit itself must not drop the rename's delete side
      (RULED 2026-08-08)" subsection to the archival-discipline doc (both required commit shapes + the post-commit
      `git status --porcelain` verification step, cross-referencing the shipped `check_create_only_archive_commits.py`
      backstop). Also cross-referenced from `codex/11-project-management/plan-hygiene.md`'s archive-destination note
      (the only other doc directly instructing `git mv` for archival) so the hazard is visible from both entry points.
- [x] ✅ [SCRIPT] P3. **DONE 2026-08-06 (slot-6) — the parent doc archived.** The resolved parent doc
      `prek_patch_cache_replays_stale_diff_onto_unrelated_files_2026_07_29.md` was moved to `plans/archive/issues/` via
      `git mv` (`status: resolved`, ARCHIVED banner added) and every path referrer updated corpus-wide (the old
      `plans/active/issues/` path references → `plans/archive/issues/`, across 14 files: 6 plans + 8 scripts;
      keyword/historical bare-filename mentions intentionally left as-is). Shipped in the archival commit
      (unified-trading-pm, 2026-08-06). (repo: unified-trading-pm)

## Progress Log

- 2026-08-06 (slot-15, review): **SHA correction** — P1's shipped evidence was first cited as
  `unified-trading-pm@20e9d748c` (pre-rebase LOCAL commit object, still present in this slot's clone). Quickmerge
  squash-landed the change on LDR as `unified-trading-pm@5bfe78fca` (on `origin/live-defi-rollout`). `20e9d748c` is a
  dangling object — not on any branch/ref, unresolvable in sibling clones → would have tripped the
  `plan-commit-sha-evidence` ratchet (at baseline=2 boundary). Evidence above corrected to `5bfe78fca`.
- 2026-08-06 (slot-15, review): P1 shipped — `scripts/plan-hygiene/check_create_only_archive_commits.py` (new) + wired
  into `run_hygiene_sweep.sh` as a hard check (unified-trading-pm@5bfe78fca). Behavior verified: HEAD scan hard-fails on
  the 5 live duplicate pairs; `--commit <sha>` mode flags the exact create-only signature on `7accf8ecf` (147
  archive-issue adds with surviving active twins); scratch-repo reproduction confirms proper rename (`R100`) and clean
  corpus pass, create-only fails, and the two-path `--only` fix clears it. Incidental: while running PM Pass-1 QG, hit a
  pre-existing `plan-commit-sha-evidence` ratchet red (4 > baseline 2) caused by 3 fabricated/unresolvable
  `<repo>@<sha>` citations on done todos in OTHER plans; corrected them as small+clear findings (small+clear triage
  bucket) to the real SHAs found via repo history — `deployment-service@1c4457`→`1c1e445`,
  `unified-trading-ci@4dcd37d`→`f20c59f`, `instruments-service@aaa0866c`→dropped (pair-mate `eca688ac6` resolves).
  OOM-directive acknowledgement: none of slot-15's processes were OOM-killed today; no heavy RAM/IO ran locally.
- 2026-08-06 (slot-6, review): filed after determining the mechanism for the prek_patch_cache doc's open [REVIEW] P1.
  Patched `IggyIkenna/prek@v0.4.12` confirmed in effect on this host (sha256 byte-match + harness `clean=5 corrupt=0`).
  Create-only reproduced in 4 controlled scenarios (above) — `git commit --only <new-path>` after `git mv` drops the
  delete side, prek-independent, single-process; concurrency ruled out. 5 live diverged duplicate pairs found in the
  corpus. Evidence in the parent doc's Progress Log + this doc.
- 2026-08-06 (slot-6, review): the parent `prek_patch_cache...` doc was archived (all todos done, mechanism named) via
  `git mv` to `plans/archive/issues/` + `status: resolved` + ARCHIVED banner + corpus-wide referrer sweep (14 files).
  This doc's `related:` updated to the archive path; the archival P3 todo flipped.
- **context-scout 2026-08-07**: populated context_scope (4 entries) — added
  `scripts/plan-hygiene/check_create_only_archive_commits.py` (the shipped guard script itself, P1's actual deliverable,
  not previously cited); the 3 pre-existing entries (the two referrer/hygiene scripts + the archival-discipline codex
  doc the remaining open P3 todo targets) re-verified, still resolve.
- 2026-08-08 (slot-26, review): P3 shipped — `unified-trading-pm@4ad2f00f4`. Added the "The archival commit itself must
  not drop the rename's delete side (RULED 2026-08-08)" subsection to
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (both required commit shapes —
  `safe-doc-push.sh`/full-staged-set commit, or two-path `--only` — plus the mandatory post-commit
  `git status --porcelain` verification), and cross-referenced it from `plan-hygiene.md`'s archive-destination note (the
  only other doc directly instructing `git mv` for archival; no separate runbook doc names the archival git-commands
  beyond these two). Every todo in this doc is now `[x]` with no `locked_by` — archival-eligible per the 6-step ritual
  on the next pass.
