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
  **CORRECTION 2026-08-14 (slot 29)**: the "feature shipped" read of the 17 tranche refs was WRONG — those were
  docstring/comment prose about the tranche concept, not an implemented `--tranche` CLI flag (the script had no argparse
  at all; `--tranche cefi` silently no-op'd). Slot 22's own `453a4558c4` verdict (SUPERSEDED, do not ship) still stands
  on its own merits — the real feature just didn't exist anywhere until this task implemented it fresh, see the
  Done-when section's todo 2.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [orphan-wip, git-drift, recovery, plan-hygiene, died-with-unshipped-wip]
related:
  [
    /plans/active/issues/killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md,
    /plans/archive/2026_08/issues/ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md,
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
resolved_by: slot-29, 2026-08-14
locked_by:
locked_since:
depends_on: []
---

# Ship orphan WIP batch 2026-08-13 (slots 3/17/19/22/27/33)

> **🟢 ARCHIVED 2026-08-14 — RESOLVED.** Both todos done: 5 of 6 planned commits shipped as-is; slot 17 UAC's `3f4fc235`
> found to be a second supersession trap (same class as slot 22's) — shipped a small real fix (stale comment) in its
> place instead. See the Done-when section + Progress Log for full per-row detail and all shipped SHAs.

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

- [x] ✅ [CODE] P2. **Ship the six orphan commits to `origin/live-defi-rollout`.** DONE 2026-08-14 (slot 29) — 5 of 6
      shipped as planned; slot 17 UAC's `3f4fc235` turned out to be a SEVENTH supersession trap (same class as slot
      22's), discovered live during rebase/cherry-pick, not shipped as-is. Final per-row outcome:
  - slot 3 instruments-service `94bdb901`: **already on origin** (rebased form `5f2f806b` — landed by a peer before this
    task started; no action needed).
  - slot 17 deployment-service `557650ff` → shipped as `deployment-service@6a189157fa`. QG surfaced a REAL pre-existing
    bug in the commit's own test (`test_co_located_archetypes_sum_onto_one_instance` asserted
    `required_vcpu == pytest.approx(baseline_vcpu + contribution_total)` without accounting for the implementation's
    `math.ceil()` — this exact archetype/client/instrument combo (2×MARKET_MAKING_CONTINUOUS +
    3×ARBITRAGE_PRICE_DISPERSION, 10 instruments each, standard tier) deterministically sums to 9.5, which `math.ceil`s
    to 10; not caused by any upstream drift — no other origin commit ever touched this file). Fixed the test assertion
    to `math.ceil()` the expectation, amended the commit, re-ran QG green, shipped.
  - slot 17 unified-api-contracts `3f4fc235` (register spark oracle source): **SUPERSEDED, NOT shipped as-is** — a
    cherry-pick attempt hit real conflicts in `_source_priority_data.py` + 3 test files because a LATER, broader
    "2026-08-12 WIRE REAL CAPTURE" batch (radiant/spark/compound_v3/fluid together) already landed the functional
    SOURCE_PRIORITY/pipeline_mode/SOURCE_MODE_CAPABILITY/test content on origin — same trap class as slot 22's, just not
    caught by the 2026-08-13 18:00Z review (which apparently pattern-matched on "tranche"/comment mentions rather than
    verifying the actual registered entries). ONE genuine gap remained: `_defi.py`'s `PROTOCOL_CAPABILITIES["spark"]`
    comment still read "aspirational: capture not yet wired" even though the rest of the registry already treats it as
    wired — fixed that stale comment as a small standalone commit, shipped as `unified-api-contracts@b889eb329b` (first
    attempt hit the known `quickmerge_agent_regate_resets_branch_loses_local_commit` pattern — a duration-budget re-gate
    timeout reset the branch to origin, discarding the rebased commit from the tip; recovered via
    `git merge --ff-only <dangling-sha>` from reflog per RULES.md, re-shipped clean).
  - slot 19 unified-api-contracts `a4751bbb` → shipped as `unified-api-contracts@6a001ea497` (confirmed genuinely NOT on
    origin before shipping — `("defi","rewards")` was still `["onchain_subgraph"]` pre-ship).
  - slot 22 unified-trading-pm `453a4558c4`: confirmed SUPERSEDED per this doc's own table — correctly skipped. (See
    todo 2 below: the "already on origin" premise for the underlying feature turned out to be FALSE on closer inspection
    — the feature was re-implemented fresh, see that todo's note.)
  - slot 27 unified-trading-pm `2ab7fa7abf` → shipped as `unified-trading-pm@498222736c`. Local HEAD had been
    re-committed to a different SHA (`7d96db87c1`, content-IDENTICAL diff vs `2ab7fa7abf` — confirmed via
    `git diff 2ab7fa7abf 7d96db87c1` returning empty for the touched file) by an interim rebase; shipped that current
    HEAD, same fix (env-tiered `instruments-store` bucket resolution via `resolve_bucket_name`).
  - slot 33 instruments-service `a62db2bc` → shipped as `instruments-service@dc8f13b914` (confirmed genuinely NOT on
    origin before shipping — `_resolve_leg_symbol` absent from origin's `symbology.py` pre-ship). All SHAs re-verified
    ancestor-of-origin in the same session, post-ship.
- [x] ✅ [DOCS] P2. **Close the ag_closeout_linkage `--tranche` todo.** DONE 2026-08-14 (slot 29) — the "slot 22's
      feature is ALREADY on origin" premise was **FALSE**: `check_ag_closeout_linkage.py` had NO `--tranche` handling at
      all (no argparse, only ad-hoc `"--only"/"--quiet"/"--update-baseline" in sys.argv` checks) — the 17 "tranche" hits
      the earlier review counted were docstring/comment prose about the tranche CONCEPT, not an implemented CLI flag.
      Live-verified: `--tranche cefi` silently no-op'd and ran the full-corpus check regardless (exit 0 was a false
      proxy for "the flag works" — see workspace measurement-claims-discipline rule). Since the underlying
      `ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md` todo 3 independently describes this as bounded,
      precedented, AO-dispatchable work (mirrors `generate_ag_closeout_audit_candidates.py --tranche`), implemented it
      for real rather than falsely flipping the checkbox: added an additive/opt-in `--tranche <name>` diagnostic mode
      (scopes the printed orphan list + count to one tranche, always exits 0 since the corpus-wide baseline isn't
      per-tranche decomposable — no-flag mode unchanged) + fixed a latent `_orphans_for()` bug that KeyError'd the
      moment the closeout_family dict was scoped to fewer than all tranches. Shipped as `unified-trading-pm@aa2cefd82d`.
      Flipped that doc's todo 3 with this real SHA (see its own Progress Log).

## Progress Log

### 2026-08-14 — resolved by slot 29 (infra)

Both todos done. Summary: 5 of the 6 planned commits shipped as-is; slot 17's UAC commit turned out to be a second
supersession trap this doc's own review didn't catch (same class as slot 22's, caught live via cherry-pick conflicts) —
shipped a small real fix (stale comment) in its place instead of either falsely shipping stale content or falsely
closing the todo. The `--tranche` todo's "already on origin" premise was also false (a doc-comment-count false positive,
not an implemented flag) — implemented the feature for real rather than propagating the false premise into a checkbox
flip. One genuine pre-existing test bug found and fixed in slot 17 deployment-service's own commit (QG caught it, not
this review — `math.ceil` rounding vs. a `pytest.approx` assertion that never accounted for it). All 7 resulting commits
(6 shipped + 1 additional --tranche implementation) verified ancestor-of-origin post-ship. No outstanding orphan WIP
remains from this batch.
