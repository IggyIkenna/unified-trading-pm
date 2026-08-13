---
doc_type: issue
title: >-
  Ship orphan committed-but-unpushed WIP batch 2026-08-13 (slots 3/17/19/22/27/33) — six substantive commits stranded
  off-origin on paused slots' worktrees across unified-trading-pm / instruments-service / deployment-service /
  unified-api-contracts
summary: >-
  REVIEWED 2026-08-13 18:00Z (review msg 5932) + verified by main (agt-5d141a) on-tree: six dead slots
  (3/17/19/22/27/33, paused, 2-day-old pings, no live tmux) each carry exactly one clean committed-but-never-pushed
  commit (ahead=1, behind 33-179, tree clean) that content-differs from origin/live-defi-rollout. VERIFIED per-slot: (a)
  slot 3 instruments-service `94bdb901` docs(tests) correct stale TradFiMvpRule underlier claims; (b) slot 17
  deployment-service `557650ff` feat derive live compute sizing per deployment-profile instance (709 ins) + slot 17
  unified-api-contracts `3f4fc235` feat register spark oracle source for SPARK-ETHEREUM/oracle_prices; (c) slot 19
  unified-api-contracts `a4751bbb` feat declare AAVE_V3 rewards as real wired capture surface; (d) slot 27
  unified-trading-pm `2ab7fa7abf` generate_instrument_snapshot.py bucket-name fix (env-tiered instruments-store via
  resolve_bucket_name — origin has 0 resolve_bucket_name refs, fix NOT shipped); (e) slot 33 instruments-service
  `a62db2bc` fix drop unresolvable CME UD combo legs. SUPERSEDED (do NOT ship): slot 22 unified-trading-pm `453a4558c4`
  --tranche filter to check_ag_closeout_linkage.py — origin's copy already carries 17 tranche refs (feature shipped).
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

# Ship orphan WIP batch 2026-08-13 (slots 3/17/19/22/27/33)

## What I found (REVISED 2026-08-13 18:00Z — replaces the earlier slots-22/26/27 draft)

review(slot1) roundup (msg 5932, 18:00Z) flagged slots 3/17/19/22/27/33 as paused with committed-but-NEVER-pushed work.
Main (agt-5d141a) verified each on-tree (18:04Z): every worktree clean (0 dirty), ahead=1, behind 33-179. Verified table
(real SHAs to ship / drop):

| Slot | Repo                  | SHA (short)  | Commit                                                                                                                                  | Verdict (on-tree verified)                                                                                            |
| ---- | --------------------- | ------------ | --------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| 3    | instruments-service   | `94bdb901`   | docs(tests): correct stale "real TradFiMvpRule underlier" claims after v25 narrowing                                                    | SHIP (not on origin)                                                                                                  |
| 17   | deployment-service    | `557650ff`   | feat(deployment): derive live compute sizing per deployment-profile instance                                                            | SHIP (not on origin; 709 ins)                                                                                         |
| 17   | unified-api-contracts | `3f4fc235`   | feat(defi): register the spark oracle source for SPARK-ETHEREUM/oracle_prices                                                           | SHIP (not on origin)                                                                                                  |
| 19   | unified-api-contracts | `a4751bbb`   | feat(defi): declare AAVE_V3 rewards as a real, wired capture surface                                                                    | SHIP (not on origin)                                                                                                  |
| 22   | unified-trading-pm    | `453a4558c4` | feat(plan-hygiene): add opt-in `--tranche` filter to check_ag_closeout_linkage.py                                                       | **SUPERSEDED — DO NOT SHIP.** Origin scripts/plan-hygiene/check_ag_closeout_linkage.py already has 17 `tranche` refs. |
| 27   | unified-trading-pm    | `2ab7fa7abf` | chore(orphan-wip): auto-committed by pre-spawn dirty-state gate — generate_instrument_snapshot.py bucket-name fix (resolve_bucket_name) | SHIP (not on origin; origin has 0 resolve_bucket_name refs)                                                           |
| 33   | instruments-service   | `a62db2bc`   | fix(tradfi): drop unresolvable CME UD: combo legs instead of killing the venue                                                          | SHIP (not on origin)                                                                                                  |

NOTE: an EARLIER draft of this issue (slots 22/26/27, SHAs `925233d2ba`/`86f944c931`/`40d71294fc`) is STALE — slot 26's
commit was since resolved (ahead=0), slot 22's --tranche feature is already on origin, and the current slot SHAs differ
(re-authored). The table above is the verified current state; ship exactly these.

These commits were authored with the slot's own identity (`ikennaigboaka [slot-N·planning]`), are additive/small, and
span four repos (unified-trading-pm, instruments-service, deployment-service, unified-api-contracts). Same problem class
as `killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md` (no automated push path; stranded commits
only recover when a live worker lands on the clone or an operator pushes).

## Done when (all six SHIP SHAs verified on origin; slot 22 confirmed skipped)

- [ ] [CODE] P2. **Ship the six orphan commits to `origin/live-defi-rollout`.** For each of the SHIP rows above, in the
      owning slot worktree `.tabs/<slot>/<repo>`: `git fetch origin live-defi-rollout --quiet`, rebase the local commit
      onto origin (`git pull --rebase --autostash`; these are diverged ahead=1/behind 33-179 — the rebase is required;
      if a genuine conflict arises, resolve it carefully — the commits are small and additive), then land the commit on
      origin via the normal ship path (quickmerge `--agent --files '<the touched paths>'`; the docs/plans-only commit
      may go via `scripts/dev/safe-doc-push.sh`). Then verify EACH SHA is ancestor-of origin:
      `git fetch origin live-defi-rollout --quiet && git merge-base --is-ancestor <full-sha> origin/live-defi-rollout`.
      SHIP SHAs: `94bdb901` (slot 3), `557650ff` (slot 17 dep), `3f4fc235` (slot 17 UAC), `a4751bbb` (slot 19),
      `2ab7fa7abf` (slot 27), `a62db2bc` (slot 33). DO NOT ship slot 22 `453a4558c4` (superseded on origin).
- [ ] [DOCS] P2. **Close the ag_closeout_linkage `--tranche` todo** (slot 22's feature is ALREADY on origin): verify
      `scripts/plan-hygiene/check_ag_closeout_linkage.py --tranche cefi` runs (additive/opt-in, exit 0) and flip todo 3
      in `plans/active/issues/ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md` to `- [x] ✅` with the
      origin commit SHA cited (cross-repo flip, `docs(plans):` commit). This retires the still-queued
      `ag_closeout_linkage_baseline_regression_87_vs_69-625963a0ddfd` rebuild-loop task.
