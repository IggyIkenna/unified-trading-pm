---
doc_type: plan
title: prediction satellite AO dispatch batch 11 — 2026-08-13
summary: >-
  Extraction batch from the prediction tranche's 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full sweep — 2
  conflict-cleared, bounded/deterministic items pulled directly from 1 source docs (RECLASSIFY_SPLIT bounded items from
  the NA audit, orphaned_never_touched/orphaned_partial_coverage bounded items from the AG-closeout audit). Each todo
  cites its exact source doc; the source docs themselves are NOT touched by this batch (checkbox reconciliation back
  into each source doc happens in the paired finalize plan). Conflict-checked against every existing active
  batch/finalize plan for this tranche via basename-citation cross-reference before drafting — no item here duplicates
  ground an existing dispatched Todos entry already claims.
status: active
nature: process
asset_group: [prediction]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [prediction, ao-dispatch, satellite-batch, na-eligibility-audit, ag-closeout-audit]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md,
  ]
created: "2026-08-13"
last_updated: "2026-08-20" # was 2026-08-13 -- stale vs the 2026-08-17 context-scout body edit; corrected 2026-08-19 (/plan-reconcile predictions_master)
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [prediction_phase_ab_residuals_2026_07_24]
gate_on_depends: true
# depends_on added 2026-08-19 (/plan-reconcile predictions_master) -- both todos below were only ever
# prose-gated on this doc's open-todo count reaching 0 (see each todo's own text), never machine-enforced;
# 2 separate dispatched workers (slot-29, slot-12, both 2026-08-14) had to independently self-skip after
# wasted round-trips discovering the gate live. Encodes the already-stated intent as a real dispatch gate,
# does not change it. (moved off the depends_on line 2026-08-19 -- the inline comment was breaking
# gate_on_depends_unmet_upstreams_on_disk()'s dep_stem parsing, 500'ing GET /api/backlog fleet-wide;
# see /plans/active/issues/backlog_500_malformed_depends_on_comment_2026_08_19.md
context_scope:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_phase_ab_residuals_2026_07_24.md,
    /plans/active/prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  Drafted by the 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full-corpus sweep (interactive session).
  Operator-approved 2026-08-13 — flipped to `status: active`, dispatchable (see body banner). [Corrected 2026-08-17
  (plan_reconciler): this field previously still read as awaiting approval, self-contradicting the already-approved
  `status:` field above it and the body banner below.]
---

# prediction satellite AO dispatch batch 11 — 2026-08-13

> **Operator-approved 2026-08-13 — `status: active`, dispatchable.** Every todo below was classified
> bounded/deterministic (worker-determinable outcome, no open design/judgment call) by the 2026-08-13 full-sweep audit
> and conflict-checked against this tranche's existing active batches before being drafted here.

## Todos

- [ ] [CODE] P2. **GATED — do not run until `prediction_phase_ab_residuals_2026_07_24.md` reaches 0 open todos
      (currently 4, re-verified 2026-08-19).** Run `data-pipeline-check-is --asset-group prediction --day 2026-08-05`
      (fallback `2026-06-28`) once that gate clears; cite the report path. Source:
      `plans/active/prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md`

      **NOT ACTIONABLE 2026-08-14 (slot-29, backend_engineer) — gate still open, re-verified live.** Same gate as the
          `data-pipeline-check-mtds` todo below: `prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md` is
          `depends_on: [prediction_phase_ab_residuals_2026_07_24]` + `gate_on_depends: true`. Live-checked
          `prediction_phase_ab_residuals_2026_07_24.md` today: still **6 open `- [ ]` todos** (recounted 2026-08-17 by plan_reconciler — A1 resolved 2026-08-15, dropping the count from 7) (unchanged from every prior
          re-check). Skipping (`reason_code: GATED`) rather than running the pipeline-check prematurely; re-check
          `prediction_phase_ab_residuals_2026_07_24.md`'s open-todo count before re-attempting. **CORRECTED 2026-08-19
          (plan_reconciler, `/plan-reconcile predictions_master`)**: live recount today is **4 open** `- [ ]` todos, not
          6 (`grep -c '^- \[ \]' plans/active/prediction_phase_ab_residuals_2026_07_24.md` = 4, matching that doc's own
          2026-08-18 na-eligibility-audit marker) — gate conclusion unchanged (4 &gt; 0, still not dispatchable), only
          the stale count corrected.

- [ ] [CODE] P2. **GATED — do not run until `prediction_phase_ab_residuals_2026_07_24.md` reaches 0 open todos
      (currently 4, re-verified 2026-08-19).** Run `data-pipeline-check-mtds --asset-group prediction --day 2026-08-05`
      (fallback `2026-06-28`) once that gate clears; cite the report path. Source:
      `plans/active/prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md`

      **NOT ACTIONABLE 2026-08-14 (slot-12, backend_engineer) — gate still open, re-verified live.** The Phase D source
      plan is `depends_on: [prediction_phase_ab_residuals_2026_07_24]` + `gate_on_depends: true`. Live-checked
      `prediction_phase_ab_residuals_2026_07_24.md` today: still **6 open `- [ ]` todos** (recounted 2026-08-17 by plan_reconciler — A1 resolved 2026-08-15, dropping the count from 7) (unchanged from every prior
      na-eligibility-audit re-check since 2026-08-06/07/09/10). **CORRECTED 2026-08-19 (plan_reconciler, `/plan-reconcile
      predictions_master`)**: live recount today is **4 open**, matching the sibling todo's correction above — gate
      conclusion unchanged. The P0 manifest-migration todo's `--apply` landed the
      (a)/(b)/(c) items 2026-07-19 but the CQG-bundle normalization decision (i) and the old-row tombstone-sweep
      strategy (ii) remain genuinely open/undecided — Phase-B is not fully closed, so the gate has not cleared. Skipping
      (`reason_code: GATED`) rather than running the pipeline-check prematurely; re-check
      `prediction_phase_ab_residuals_2026_07_24.md`'s open-todo count before re-attempting.

## Deferred

None — every item drafted here already cleared the conflict-check. Items that did NOT clear (genuinely operator-gated,
time-gated, or too-large-for-a-batch-todo) were left in their source docs and are not duplicated here; see the
2026-08-13 audit's full classification data for the complete list.

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries) -- added
  prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md, the explicit `Source:` doc both todos cite and the gate
  they're waiting on.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries).
