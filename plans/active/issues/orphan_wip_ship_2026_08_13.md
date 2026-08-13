---
doc_type: issue
title: >-
  Ship orphan committed-but-unpushed WIP batch 2026-08-13 (slots 22/26/27) — three clean commits stranded off-origin on
  paused slots' unified-trading-pm worktrees
summary: >-
  review(slot1) finding 2026-08-13 (msg 5781, "review 3d" — recurring died-with-unshipped-WIP pattern, prior days
  documented in killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md). Slots 22/26/27 are paused
  (2-day-old pings, no live tmux/processes) yet their unified-trading-pm worktrees each carry exactly one clean
  committed-but-never-pushed commit that content-differs from origin/live-defi-rollout. Verified 2026-08-13 by main: all
  three worktrees are clean (0 dirty), ahead=1, behind ~500 (diverged — rebase required before push). The work is real
  and complete: (a) slot 22 925233d2ba adds the --tranche filter to check_ag_closeout_linkage.py, explicitly closing the
  P3 todo in ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md (still `- [ ]` + task still queued → a fresh
  worker would re-implement it: the rebuild loop review flagged); (b) slot 26 86f944c931 completes + archives
  safe_doc_push_isolation_drops_rename_deletions_2026_08_10.md (ALLOWED_DUPLICATE_STEMS reconciliation; the archival
  exists only in slot 26's local tree); (c) slot 27 40d71294fc is the auto-committed generate_instrument_snapshot.py
  bucket-name fix (env-tiered instruments-store via resolve_bucket_name).
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [orphan-wip, git-drift, recovery, plan-hygiene, died-with-unshipped-wip]
related:
  [
    /plans/active/issues/killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md,
    /plans/active/issues/ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md,
    /plans/active/issues/venv_workspace_openapi_regen_batch11_findings_2026_08_09.md,
  ]
created: "2026-08-13"
author: main agent (agt-25f87f)
source: review(slot1) msg 5781 + main live verification, 2026-08-13
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.2
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
depends_on: []
---

# Ship orphan WIP batch 2026-08-13 (slots 22/26/27)

## What I found

review(slot1) flagged (msg 5781, 11:11Z) that slots 22/26/27 are paused with committed-but-NEVER-pushed work in their
unified-trading-pm worktrees. Main verified 11:25Z: each worktree is clean (0 dirty files) with exactly one unpushed
commit, diverged (ahead=1, behind ~500-585) from origin/live-defi-rollout:

| Slot | SHA (short)  | Commit                                                                                                                                                                                          | What it lands                                                                                                                                                                                            |
| ---- | ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 22   | `925233d2ba` | feat(plan-hygiene): add opt-in `--tranche` filter to `check_ag_closeout_linkage.py`                                                                                                             | Closes the open P3 todo 3 in `ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md` (task `ag_closeout_linkage_baseline_regression_87_vs_69-625963a0ddfd` is still queued → rebuild-loop risk) |
| 26   | `86f944c931` | docs(plans): reconcile last 3 ALLOWED_DUPLICATE_STEMS pairs (cefi/prediction/tradfi ag_closeout_audit slug collisions) + archive `safe_doc_push_isolation_drops_rename_deletions_2026_08_10.md` | The archival + 11 referrer re-points exist ONLY in slot 26's local tree; on origin the plan is still active                                                                                              |
| 27   | `40d71294fc` | chore(orphan-wip): auto-committed by pre-spawn dirty-state gate — `generate_instrument_snapshot.py` bucket-name fix (env-tiered instruments-store via `resolve_bucket_name`)                    | Real code fix, verified end-to-end by the original worker                                                                                                                                                |

All three commits were authored with the slot's own identity (`ikennaigboaka [slot-N·planning]`), are additive/small,
and belong to the unified-trading-pm repo. This is the SAME problem class as
`killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md` (no automated push path; stranded commits only
recover when a live worker lands on the clone or an operator pushes). The systemic fix (that doc's open todo 2) is NOT
in scope here — this batch just ships the current stranded commits before any worker re-implements them.

## Done when (all three SHAs verified on origin)

- [ ] [CODE] P2. **Ship the three orphan commits to `origin/live-defi-rollout`.** For each of
      `.tabs/{22,26,27}/unified-trading-pm`, in that worktree: `git fetch origin live-defi-rollout --quiet`, rebase the
      local commit onto origin (`git pull --rebase --autostash`; these are diverged ahead=1/behind~500 — the rebase is
      required; if a genuine conflict arises, resolve it carefully — the commits are small and additive), then land the
      commit on origin via the normal ship path (quickmerge `--agent --files '<the touched paths>'`; the docs/plans-only
      commit may go via `scripts/dev/safe-doc-push.sh`). Then verify EACH SHA is ancestor-of origin:
      `git fetch origin live-defi-rollout --quiet && git merge-base --is-ancestor <full-sha> origin/live-defi-rollout`.
      The three full SHAs: `925233d2ba5ac4c4d515d5f2427fce3be49f7e7a` (slot 22),
      `86f944c931c2bed64327dfb1f54decd44b4195f4` (slot 26), `40d71294fc9e849c84a41eb3646f51504de55543` (slot 27).
- [ ] [DOCS] P2. **Close the ag_closeout_linkage `--tranche` todo.** Once `925233d2ba` is on origin, verify
      `scripts/plan-hygiene/check_ag_closeout_linkage.py --tranche cefi` runs (additive/opt-in, exit 0) and flip todo 3
      in `plans/active/issues/ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md` to `- [x] ✅` with the
      commit SHA cited (cross-repo flip, `docs(plans):` commit). This retires the still-queued
      `ag_closeout_linkage_baseline_regression_87_vs_69-625963a0ddfd` rebuild-loop task.
