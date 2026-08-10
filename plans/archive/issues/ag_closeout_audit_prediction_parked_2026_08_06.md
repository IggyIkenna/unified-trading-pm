---
doc_type: issue
title: >-
  Prediction tranche closeout-audit findings (2026-08-06) — zero orphans, the one fresh candidate since 2026-08-04 is
  confirmed cross-cutting, corpus fully stable
summary: >-
  Filed by the scheduled `/ag-closeout-audit prediction` run 2026-08-06 (Phases 0-2, read-only; Phase 3 considered and
  found nothing to draft). Live re-run of `generate_ag_closeout_audit_candidates.py --tranche prediction --json` found
  `total_members=47` (was 48 on 2026-08-04 — net corpus shrink) and `never_cited_count=12` (was 12) — 11 of the 12 are
  the SAME basenames flagged `never_cited` on 2026-07-31/08-04 (re-verified via a fresh frontmatter tag/status check:
  unchanged, still genuinely cross-cutting), and the 08-04 orphan
  (`mtds_prediction_backfill_targets_wrong_data_type_scope_2026_08_02.md`) has dropped off the never-cited list, now
  `cited_somewhere` via `prediction_satellite_ao_dispatch_batch7_2026_08_04.md` — confirming batch7's extraction linked
  correctly. The one new never-cited candidate
  (`ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md`) was classified via a real
  Phase-1 Workflow agent: `exclude_cross_cutting` (self-declared cross-AG decision thread, zero citations across all 11
  covering docs, and independently `ao_dispatch_eligible: false` regardless of the AG call). Net: 0 genuinely-orphaned
  prediction-primary docs found. No batch drafted; batch4/batch6/batch7 remain the unchanged live dispatch surface.
  Beyond the candidate script, a `check_ag_closeout_linkage.py` cross-check surfaced 2 prediction-tagged docs
  graph-disconnected from the closeout family (same regression a sibling cefi-tranche run filed corpus-wide today as
  `ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md`) — both fixed directly (1 archived, 0 referrers,
  fully resolved; 1 linked via a new aggregated-sources citation), verified via re-run: 0 prediction-tagged linkage
  orphans remain. parked_findings == 0.
status: resolved
nature: issue
asset_group: [prediction]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [prediction, ag-closeout-audit, orphan-audit, plan-hygiene]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/archive/issues/ag_closeout_audit_prediction_parked_2026_08_04.md,
    /plans/archive/2026_08/issues/ag_closeout_audit_prediction_parked_2026_07_31.md,
    /plans/active/issues/ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md,
    /plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md,
    /plans/active/prediction_satellite_ao_dispatch_batch7_2026_08_04.md,
    /plans/active/issues/ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md,
    /plans/archive/2026_08/issues/mtds_prediction_live_boundary_event_topic_missing_2026_08_03.md,
    /plans/archive/issues/mtds_prediction_rebuild_instrument_type_mismatch_2026_08_01.md,
  ]
created: "2026-08-06"
author: unknown
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.04
assigned_role: data_engineering
drift_direction: none
depends_on: []
resolved_by:
  "2026-08-06 (slot 8, ag_closeout_auditor, dispatch agt-1591dd) — same-run resolution, no operator escalation needed"
locked_by:
locked_since:
source:
  [
    "Scheduled /ag-closeout-audit prediction run 2026-08-06 (ag_closeout_auditor, slot 8, dispatch agt-1591dd), Phases
    0-2 (a real Phase-1 Workflow over the 1 genuinely-fresh candidate, plus a cheap frontmatter re-verification of the
    11 already-thrice-confirmed cross-cutting docs) and Phase 3 (conflict-check step considered, found nothing
    conflict-cleared to draft since nothing was orphaned). Operator was not interactively present during the run;
    nothing this run found needed operator judgment.",
  ]
context_scope:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py,
  ]
---

# Prediction closeout-audit findings, 2026-08-06

> **Context.** Audit record of today's `/ag-closeout-audit prediction` pass. Written per the skill's "parked findings
> always get a durable issue doc" rule — even though this run found zero orphans and nothing blocked, this is still the
> durable record of the fresh candidate count and the one fresh doc's Phase-1 verdict, matching every prior day's
> practice in this tranche (so a future round's iterative-drain step 1 has something to cite instead of re-deriving from
> scratch).

## Headline result

Of 47 prediction-primary candidates (`generate_ag_closeout_audit_candidates.py --tranche prediction --json`), 35 are
`cited_somewhere` (covered by an active/self-dispatched plan) and 12 are `never_cited`. **Zero genuinely-orphaned
prediction-primary docs remain** — every one of the 12 never-cited candidates classifies `exclude_cross_cutting`.

- **11 re-confirmed `exclude_cross_cutting` (cheap re-verification, not a full re-read)** — these are the SAME 11
  basenames flagged `never_cited` on 2026-07-25/07-31/08-04, each already independently confirmed cross-cutting via TWO
  full Phase-1 Workflow passes (07-31, 08-04) plus two rounds of spot-checks (3-of-11, then 6-of-11) on 07-31 itself.
  Per the skill's own token-cost-for-zero-new-information caution (07-31's third same-day re-dispatch entry), re-running
  a full agent-per-doc Workflow a fifth time over an unchanged population adds no new information — instead, this run
  re-verified all 11 via a direct frontmatter grep (`asset_group` array + `status`): all 11 still carry 4-6 real
  `asset_group` markers spanning multiple/all 5 AGs, all still `status: open`/`active`, byte-identical to the 08-04
  snapshot. Basenames (unchanged since 07-31): `ag_closeout_audit_rollout_2026_07_25.md`,
  `adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md`,
  `backfill_smoke_write_path_canonical_audit_2026_07_20.md`, `candle_feature_canonical_path_divergence_2026_07_20.md`,
  `estate_orphan_assessment_2026_07_21.md`, `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`,
  `instruments_docs_audit_outstanding_items_2026_07_08.md`, `instruments_remaining_work_audit_2026_07_10.md`,
  `mdps_features_deadcode_consolidation_2026_07_20.md`, `mtds_is_full_adapter_smoketest_findings_2026_07_07.md`,
  `uac_per_venue_seed_fallback_removal_deferred_2026_07_26.md`.
- **1 freshly classified `exclude_cross_cutting`** —
  [`issues/ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md`](/plans/active/issues/ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md),
  created 2026-08-04 (postdates the 08-04 audit's own candidate snapshot, so no prior round could have seen it). Tagged
  `[cefi, defi, tradfi, sports, prediction]`. A real Phase-1 Workflow agent (`wf_d151c1f3-aee`) read it in full, grepped
  all 11 current covering docs for its basename (zero hits in every one), and found: (1) its own "Recommended decision"
  section explicitly declines a prediction-specific finding, asking to fold both its todos into the SAME A/B/C decision
  thread already open on `mdps_features_deadcode_consolidation_2026_07_20.md` (itself one of the 11 confirmed
  cross-cutting exclusions above) "since splitting into a third parallel decision thread on the same theme adds
  coordination overhead for no benefit"; (2) todo 1 (`launch-ml-training-vm.sh`) is a fully generic,
  asset-group-agnostic launcher per `/codex/05-infrastructure/vm-launcher-runbook.md` — zero prediction-specific
  content; (3) every non-AG-tag frontmatter axis (`parent_epic: infrastructure_master`, `repos: [deployment-service]`,
  `assigned_role: infra`) signals infra filing, not prediction filing; (4) independent of the cross-cutting call, the
  remaining work is also NOT `ao_dispatch_eligible` — the doc's own text says the fix "needs a design call this P3
  mechanical-deletion todo didn't scope," an explicit self-declared non-adjudicated operator/architect choice on both
  todos. Full agent reasoning in `wf_d151c1f3-aee`'s journal.

**Corpus delta vs 2026-08-04**: `total_members` 48→47 (net shrink — the 08-04 orphan
`mtds_prediction_backfill_targets_wrong_data_type_scope_2026_08_02.md` is no longer `never_cited`; confirmed
`cited_somewhere` now via `prediction_satellite_ao_dispatch_batch7_2026_08_04.md`, verifying that extraction's citation
linked correctly). `never_cited_count` held at 12 (11 carryover + 1 new, replacing the 1 that graduated to
`cited_somewhere`).

**parked_findings ledger**: 0 findings needed operator escalation this run == 0 entries requiring a
`BLOCKED-OPERATOR-DECISION` marker in this doc. Balanced. This doc exists as an audit-trail record, not because anything
is stuck.

## Linkage-gate cross-check (beyond the candidate script) — 2 mechanical fixes applied

Per the skill's own guidance ("do not fully trust `asset_group` alone without a linkage check"), also ran
`check_ag_closeout_linkage.py` (the stricter graph/mention-based safety net, distinct from
`generate_ag_closeout_audit_candidates.py`'s citation-heuristic) as an extra cross-check beyond what Phase 0's candidate
script covers. It flagged 2 prediction-tagged docs this run's candidate list did not surface (both excluded from
`generate_ag_closeout_audit_candidates.py`'s member set for good reason — one `status: resolved`, the other
`assigned_vm: planning` self-dispatched — so neither is a genuine "orphan" in this skill's sense, but both were
genuinely graph-disconnected from the closeout family, which is real linkage debt). This is the SAME corpus-wide
regression a sibling `cefi`-tranche run filed today as
[`ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md`](/plans/active/issues/ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md)
(84 orphans measured at the time this run cross-checked, corpus-wide, 2 tagged `prediction`) — that doc is
`asset_group: [cross-cutting]`, owned by a different tranche and actively referenced by multiple concurrent workers
today, so per the primary-owner rule it was NOT edited directly here; instead both prediction-owned contributing docs
were fixed directly (squarely this tranche's own file ownership, no collision risk):

1. **Archived**
   [`issues/mtds_prediction_live_boundary_event_topic_missing_2026_08_03.md`](/plans/archive/2026_08/issues/mtds_prediction_live_boundary_event_topic_missing_2026_08_03.md)
   (`unified-trading-pm`, this commit) — `status: resolved`, all 3 todos `[x]` (root cause retracted as a false positive
   same-day, per its own Resolution section: "Doc is archive-eligible"), 0 corpus-wide referrers (verified via
   corpus-wide grep before moving), 0 deferred prose to migrate, no new codex contract to stub (an investigation
   self-correction, already covered by CLAUDE.md's existing "grep-then-READ" rule). 6-step archival ritual applied in
   abbreviated form (steps 1/3/4 were no-ops given the above). This ALSO closes its linkage-gate flag as a side effect —
   `check_ag_closeout_linkage.py`'s `TARGET_DIRS` is `plans/active` only, so an archived doc drops out of its candidate
   scan entirely.
2. **Added a citation** for
   [`issues/mtds_prediction_rebuild_instrument_type_mismatch_2026_08_01.md`](/plans/archive/issues/mtds_prediction_rebuild_instrument_type_mismatch_2026_08_01.md)
   to `prediction_consolidated_closeout_2026_07_18.md`'s "Manifest / CQG / phantom" aggregated-sources bucket (this
   commit) — self-dispatched (`assigned_vm: planning`), so not orphaned in the ag-closeout-audit sense, but had no
   `related:`/mention link back to its closeout family. Noted in the new citation: its `[OPERATOR] P2` todo 2 reads
   `[ ]` at the top level but its own body text describes all remaining steps as DONE 2026-08-03 — flagged as an
   apparent stale checkbox for a future pass to verify/flip rather than edited here (self-dispatched, active AO-dispatch
   target; outside this audit's remit to mutate its substantive content).

**Verified both fixes**: re-ran `check_ag_closeout_linkage.py` after both edits — zero `prediction`-tagged hits remain
(was 2), corpus-wide count 84→82. The remaining 82 are other tranches' territory, already tracked in the cross-cutting
regression doc above; not this tranche's scope to fix further.

## Iterative-drain re-check (prior parked docs' own open items)

Before fresh Phase-1 triage, re-checked both prior parked docs' still-open items per the skill's iterative-drain rule:

- `ag_closeout_audit_prediction_parked_2026_07_31.md` Finding 1 (2 adapter dead-code A-vs-B judgment calls —
  `issues/is_polymarket_dead_fixture_cross_reference_2026_07_31.md`,
  `issues/mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md`) — **re-confirmed still open, no change**.
  Both still `status: open` / `assigned_vm: NA`; `git log` on both shows only context-scout `context_scope` backfills
  and an unrelated archival commit since 08-04 — no operator decision taken. Correctly non-batchable, same reasoning as
  every prior round.
- `ag_closeout_audit_prediction_parked_2026_08_04.md` — `status: resolved`, both its own items (the stale-checkbox fix
  and the batch7 extraction) already closed same-run on 08-04. Nothing to re-check.

## Phase 3 — no batch drafted

Nothing orphaned to extract; the conflict-check step has no candidate input this round. The live dispatch surface is
unchanged: `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` (1 open, in-progress),
`prediction_satellite_ao_dispatch_batch6_2026_07_29.md` (3 open), and
`prediction_satellite_ao_dispatch_batch7_2026_08_04.md` (1 open, `status: draft` — still pending operator approval to
dispatch; its `_finalize` sibling is `active` per the no-double-gate convention) continue to carry all real remaining
bounded prediction work.

## Codex SSOTs

- `/cursor-configs/skills/ag-closeout-audit/SKILL.md` § "Parked findings ALWAYS get a durable issue doc" — why this doc
  exists even though nothing is genuinely blocked.
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3 — the conflict-check protocol (no
  candidates reached it this round).

## Progress Log

- **2026-08-06 (slot 8, ag_closeout_auditor, dispatch agt-1591dd):** Filed by the scheduled
  `/ag-closeout-audit prediction` run. Phase 0: re-ran the candidate script live (47 members, 12 never_cited — 11
  carryover + 1 new), re-checked both prior parked docs' own open items (Finding 1 from 07-31 re-confirmed still
  correctly open, no operator action taken). Phase 1: cheap frontmatter re-verification of the 11 carryover
  cross-cutting docs (no drift) + a real 1-agent Workflow (`wf_d151c1f3-aee`, 0 errors) classifying the 1 fresh
  candidate. Phase 2: 0 orphans of 47. Phase 3: no batch drafted — nothing conflict-cleared to extract, live dispatch
  surface (batch4/batch6/batch7) unchanged. Beyond the skill's core procedure, cross-checked
  `check_ag_closeout_linkage.py` (its stricter graph/mention safety net) and found + fixed 2 prediction-tagged linkage
  gaps directly (both squarely this tranche's own file ownership, no collision risk): archived
  `mtds_prediction_live_boundary_event_topic_missing_2026_08_03.md` (0 referrers, 0 open todos, self-declared
  archive-eligible — `unified-trading-pm`, this commit) and added a missing aggregated-sources citation for
  `mtds_prediction_rebuild_instrument_type_mismatch_2026_08_01.md` to the closeout hub (`unified-trading-pm`, this
  commit) — re-verified 0 prediction-tagged linkage orphans remain post-fix. Did not touch the cross-tranche regression
  doc itself (`ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md`, `asset_group: [cross-cutting]`, filed
  same-day by the sibling cefi-tranche run) per the primary-owner rule. parked_findings ledger: 0 findings this run
  needed to escalate == 0 entries marked `BLOCKED-OPERATOR-DECISION`. Balanced (the 2 linkage fixes were mechanical,
  same category as 08-04's precedent, not operator-escalations).
