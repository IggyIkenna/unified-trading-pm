---
doc_type: issue
title: >-
  Prediction tranche closeout-audit findings (2026-08-04) — one genuinely new orphan since 2026-07-31, extracted cleanly
  into batch7; the 11 prior never-cited candidates remain confirmed cross-cutting
summary: >-
  Filed by the scheduled `/ag-closeout-audit prediction` run 2026-08-04 (Phases 0-3, mostly read-only; Phase 3 drafted
  `prediction_satellite_ao_dispatch_batch7_2026_08_04.md` + its finalize pair). Also flipped a stale checkbox found
  during Phase-0 iterative-drain re-check: `ag_closeout_audit_prediction_parked_2026_07_31.md`'s Finding-2 script fix
  had actually shipped 2026-08-01 but was never marked done. This run's own fresh ground: live re-run of
  `generate_ag_closeout_audit_candidates.py --tranche prediction --json` found `total_members=48` (was 52 on 2026-07-31
  — 5 previously `cited_somewhere` docs archived/resolved in the interim, net corpus shrink) and `never_cited_count=12`
  (was 11 — all 11 prior basenames unchanged and re-confirmed genuinely cross-cutting via a fresh 12-agent Phase-1
  Workflow; +1 new single-tagged `[prediction]` doc created 2026-08-02). The one new doc's remaining work (a bounded P3
  downstream-consumer check) was conflict-checked clean and extracted into batch7 — zero findings needed operator
  escalation this run (parked_findings == 0).
status: resolved
nature: issue
asset_group: [prediction]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [prediction, ag-closeout-audit, orphan-audit, batch-7, plan-hygiene]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_satellite_ao_dispatch_batch7_2026_08_04.md,
    /plans/active/prediction_satellite_ao_dispatch_batch7_2026_08_04_finalize.md,
    /plans/archive/2026_08/issues/ag_closeout_audit_prediction_parked_2026_07_31.md,
    /plans/active/issues/mtds_prediction_backfill_targets_wrong_data_type_scope_2026_08_02.md,
    /plans/archive/issues/prediction_mdps_live_depth_history_not_accumulating_2026_08_04.md,
  ]
created: "2026-08-04"
author: unknown
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.15
estimate_calibrated_ai_days: 0.06
assigned_role: data_engineering
drift_direction: none
depends_on: []
resolved_by:
  "2026-08-04 (slot 11, ag_closeout_auditor, dispatch agt-a7e099) — same-run resolution, no operator escalation needed"
locked_by:
locked_since:
source:
  [
    "Scheduled /ag-closeout-audit prediction run 2026-08-04 (ag_closeout_auditor, slot 11, dispatch agt-a7e099), Phases
    0-3 (a real Phase-1 Workflow over the 12 never-cited candidates, plus a conflict-checked Phase-3 batch draft).
    Operator was not interactively present during the run; the one genuine orphan found had zero conflicts and cleared
    the dispatch-scope eligibility test cleanly, so it was drafted into batch7 rather than parked — nothing in this run
    needed operator judgment.",
  ]
context_scope:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/prediction_satellite_ao_dispatch_batch7_2026_08_04.md,
    /scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py,
  ]
---

# Prediction closeout-audit findings, 2026-08-04

> **Context.** Audit record of today's `/ag-closeout-audit prediction` pass. Written per the skill's "parked findings
> always get a durable issue doc" rule — even though everything this run found resolved cleanly (no
> `BLOCKED-OPERATOR-DECISION`, no unresolved conflict), this is still the durable record of the fresh candidate count
> and the per-doc Phase-1 verdicts, matching every prior day's practice in this tranche (so a future round's
> iterative-drain step 1 has something to cite instead of re-deriving from scratch).

## Headline result

Of 48 prediction-primary candidates (`generate_ag_closeout_audit_candidates.py --tranche prediction --json`), 36 are
`cited_somewhere` (covered by an active/self-dispatched plan) and 12 are `never_cited`. A fresh 12-agent Phase-1
Workflow (`wf_242a15b4-6b2`, 0 errors) classified all 12:

- **11 `exclude_cross_cutting`** — every one carries 4-6 real `asset_group` markers (cefi/defi/tradfi/sports +
  prediction, sometimes + cross-cutting), confirmed via both a frontmatter tag dump and a fresh per-doc content read
  that none is substantively prediction-specific despite the tag. All 11 are the SAME 11 basenames flagged `never_cited`
  on 2026-07-31 (`ag_closeout_audit_rollout_2026_07_25.md`,
  `adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md`,
  `backfill_smoke_write_path_canonical_audit_2026_07_20.md`, `candle_feature_canonical_path_divergence_2026_07_20.md`,
  `estate_orphan_assessment_2026_07_21.md`, `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`,
  `instruments_docs_audit_outstanding_items_2026_07_08.md`, `instruments_remaining_work_audit_2026_07_10.md`,
  `mdps_features_deadcode_consolidation_2026_07_20.md`, `mtds_is_full_adapter_smoketest_findings_2026_07_07.md`,
  `uac_per_venue_seed_fallback_removal_deferred_2026_07_26.md`) — unchanged, still correctly excluded, confirming the
  corpus is stable on this population (2 prior rounds already spot-checked a subset of these with the same verdict).
- **1 `orphaned_never_touched`** — `issues/mtds_prediction_backfill_targets_wrong_data_type_scope_2026_08_02.md`,
  created 2026-08-02 (one day after the last full audit ran 2026-07-31, so no prior round could have seen it).
  Single-tagged `[prediction]`, genuinely prediction-specific content (Polymarket/Kalshi `PREDICTION_MARKET` canonical
  rows, `prediction_canonical_question_group` bundling). Its own cross-cutting parent plan
  (`mtds_available_at_cross_asset_backfill_2026_07_13.md`, tagged `[tradfi, defi, prediction]`) explicitly defers the
  remaining question to this doc rather than claiming it ("the trades/book_snapshot_5 question is tracked separately in
  the new issue doc, not blocking this plan further") — confirmed via direct read, not just citation-grep. One bounded
  P3 todo remains (check for a real downstream consumer of `available_at` on `trades`/`book_snapshot_5` prediction
  rows). Conflict-checked clean against all 11 covering docs + the parent plan — extracted into
  [`prediction_satellite_ao_dispatch_batch7_2026_08_04.md`](/plans/active/prediction_satellite_ao_dispatch_batch7_2026_08_04.md)
  (paired with a `gate_on_depends`-held finalize plan), `status: draft` pending operator approval to dispatch.

**parked_findings ledger**: 0 findings needed operator escalation this run (the one orphan cleared conflict-check and
dispatch-scope eligibility cleanly) == 0 entries requiring a `BLOCKED-OPERATOR-DECISION` marker in this doc. Balanced.
This doc exists as an audit-trail record, not because anything is stuck.

## Stale-checkbox fix (found during iterative-drain step 1, applied directly — not parked)

Before running fresh Phase-1 triage, re-checked `ag_closeout_audit_prediction_parked_2026_07_31.md`'s own two open
findings per the skill's iterative-drain rule. Finding 2's `[SCRIPT] P2` todo (extend
`generate_ag_closeout_audit_candidates.py::_covering_paths()` to resolve the closeout hub's own `depends_on:`) was still
`[ ]` but had actually shipped 2026-08-01 (`unified-trading-pm@be7269449`, by the tradfi-tranche sibling run, same
shared cross-tranche script) — live-verified (`--tranche prediction --json` now returns 11 `covering_paths` including
all 4 Phase A-E children, was 7 before the fix; the named regression test exists). Flipped `[x]` with full evidence
directly in that doc (mechanical, no judgment call — see that doc's own Todos/Progress-Log, not repeated here). Finding
1 (2 adapter dead-code docs, operator-gated A-vs-B judgment) re-confirmed still correctly open — no operator action
taken on either since 2026-07-31.

## Also confirmed (no action needed)

`issues/prediction_mdps_live_depth_history_not_accumulating_2026_08_04.md` — today's data-correctness FAIL-verdict
finding (raw prediction depth history overwrites per-flush; the processed candle/book store has zero live-mode objects)
— is `assigned_vm: planning`, `status: open`, and was actively worked by 3 other slots today (3 of 5 todos closed
same-day: root-caused the MDPS live-mode gap as fleet-wide not prediction-specific, fixed the `timer-candles` CLI
dispatch bug, and decided not to operationally launch `mdps-features-live` after 2 failed pilots). Self-dispatched —
correctly not an orphan, no batch action needed from this audit.

## Codex SSOTs

- `/cursor-configs/skills/ag-closeout-audit/SKILL.md` § "Parked findings ALWAYS get a durable issue doc" — why this doc
  exists even though nothing is genuinely blocked.
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3 — the conflict-check protocol
  applied before drafting batch7.

## Progress Log

- **2026-08-04 (slot-11, ag_closeout_auditor, dispatch agt-a7e099):** Filed by the scheduled
  `/ag-closeout-audit prediction` run. Phase 0: re-ran the candidate script live (48 members, 12 never_cited, +1 vs
  2026-07-31), re-checked the prior parked doc's own open items (found + fixed the stale Finding-2 checkbox). Phase 1:
  real 12-agent Workflow (`wf_242a15b4-6b2`, 0 errors) classified all 12 never-cited candidates. Phase 3: conflict-
  checked the 1 genuine orphan against all 11 covering docs + its cross-cutting parent plan, found zero overlap,
  extracted into `prediction_satellite_ao_dispatch_batch7_2026_08_04.md` + gated finalize pair (both `status: draft` /
  `active` per the no-double-gate convention). parked_findings ledger: 0 findings this doc needed to escalate == 0
  entries marked `BLOCKED-OPERATOR-DECISION`. Balanced.
