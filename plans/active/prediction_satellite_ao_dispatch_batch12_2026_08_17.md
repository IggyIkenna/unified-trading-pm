---
doc_type: plan
title: prediction satellite AO dispatch batch 12 — 2026-08-17
summary: >-
  Extraction batch from the prediction tranche's 2026-08-17 /na-eligibility-audit sweep — 3 conflict-cleared,
  bounded/deterministic items pulled directly from 2 source docs via the per-todo RECLASSIFY_SPLIT path (closing the
  loop on 3 MISCLASSIFIED_LIKELY_AO_ELIGIBLE flags an earlier pass today explicitly deferred to "a future pass"). Each
  todo cites its exact source doc; the source docs themselves keep `assigned_vm: NA` for their remaining
  genuinely-operator-gated/judgment items — checkbox reconciliation back into each source doc happens in the paired
  finalize plan. Conflict-checked against every active planning doc under `parent_epic: predictions_master`, the
  tranche's consolidated closeout, and every existing prediction satellite batch (1-11) before drafting — no item here
  duplicates ground an existing dispatched Todos entry already claims.
status: active
nature: process
asset_group: [prediction]
stage: [data]
repos: [unified-trading-pm, market-tick-data-service, unified-api-contracts, instruments-service]
scope: [engineer]
tags: [prediction, ao-dispatch, satellite-batch, na-eligibility-audit, reclassify-split]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_phase_ab_residuals_2026_07_24.md,
    /plans/active/issues/prediction_batch4_deferred_residuals_2026_08_16.md,
  ]
created: "2026-08-17"
last_updated: "2026-08-17"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1.2
estimate_calibrated_ai_days: 1.4
assigned_role: data_engineering
effort: high
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/prediction_phase_ab_residuals_2026_07_24.md,
    /plans/active/issues/prediction_batch4_deferred_residuals_2026_08_16.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    market-tick-data-service/scripts/canonicalize_prediction_manifest_2026_07_18.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/manifest_finalize.py,
  ]
source: >-
  Drafted by the 2026-08-17 /na-eligibility-audit prediction-tranche run (autonomous, dispatch agt-becf6c) — per-todo
  RECLASSIFY_SPLIT path. All 3 items were tagged MISCLASSIFIED_LIKELY_AO_ELIGIBLE by an earlier na-eligibility-audit
  pass today and explicitly deferred to "a future pass"; this run re-assessed each independently against the primary
  bounded-outcome bar and promoted all 3.
---

# prediction satellite AO dispatch batch 12 — 2026-08-17

> **Drafted 2026-08-17 by /na-eligibility-audit (autonomous) — `status: active`, dispatchable.** Every todo below was
> classified bounded/deterministic (worker-determinable outcome, no open design/judgment call) and conflict-checked
> against every active batch/finalize plan + the consolidated closeout for this tranche before being drafted here.

## Todos

- [ ] [DATA] P1. **Apply the standing canonicalization precedent by default to the A0-ambiguous prediction
      `instrument_type`/`data_type` value set; escalate only a genuine tied residual.** Ruled 2026-07-28 (general
      theme — canonicalization should be done properly, not left as an open-ended gate): (1) enumerate the FULL
      A0-ambiguous set live via the existing `enumerate_prediction_dimensions.py` script; (2) resolve each value by
      applying the SAME precedent already established for prediction (operator, 2026-07-18: canonical = UPPERCASE
      enum, the catalogue is SSOT) — default to whichever candidate reading matches the catalogue's clean canonical
      form, recording the specific per-value mapping decisions with evidence cited; (3) do not block the unambiguous
      majority on this. Only if a specific value survives (2) still genuinely tied between two readings with no
      catalogue precedent to break the tie — escalate that SPECIFIC residual value (not the whole todo) as a narrow
      options+recommendation operator question (mirror `sports_satellite_ao_dispatch_batch5_2026_07_26.md`'s per-item
      operator-decision-gate format). Done when: the full ambiguous set is enumerated with a disposition
      (resolved-by-precedent or escalated-as-residual) recorded per value in this doc's Progress Log. Repo:
      market-tick-data-service, instruments-service. Source:
      `plans/active/prediction_phase_ab_residuals_2026_07_24.md` Phase B, item "RULED 2026-07-28 — apply the standing
      canonicalization precedent by default" (line 432).

- [ ] [DIAG] P2. **Root-cause the actively-growing blank/null prediction `instrument_type` manifest rows (~10 rows/day,
      NOT static residue) and ship+verify a fix, or record an accepted-gap reason.** Live counts across 3 dated reads:
      30 (2026-07-20) → 70 (2026-07-24) → 100 (2026-07-27), a consistent ~10 rows/day linear rate — distinct from the
      co-located, static 76-row `prediction` (singular) malformed residual on the same axis, which is dead historical
      residue. Done when: the writer/cron path responsible for the blank stamps is identified by name (file:line) with
      a live-vs-historical verdict — candidates include the per-CID writer path near
      `engine/orchestrator/manifest_finalize._finalize_prediction_bundles` (already known to mis-stamp
      `instrument_type` on bundle rows, though that finding was lowercase `"prediction"`, not blank) or a different
      live/per-CID path — and either a fix ships and is verified against the next day's count, or the ~10/day gap is
      recorded as accepted with a stated reason. Repo: market-tick-data-service. Source:
      `plans/active/prediction_phase_ab_residuals_2026_07_24.md` Phase B, item "prediction manifest blank/null
      `instrument_type` rows are ACTIVELY GROWING" (line 463).

- [ ] [DATA] P3. **Investigate whether the 49 canonical-only POLYMARKET `trades` days (2025-04-19..2025-06-05 +
      2025-06-13, outside the 348-date legacy-bundle range) can recover `title`/`slug`/`event_slug` from the IS
      POLYMARKET reference universe** (`prediction_canonical_question_group`/`market_lifecycle`, which the manifest
      census confirms covers these dates) rather than from the legacy `prediction_trades` bundle (which does not exist
      for these days). Evidence at
      `gs://market-data-tick-pred-prd-central-element-323112/_ops/4bi_scratchpad_2026_08_06/` (46-141 shards/day
      sampled, all `enrichment_fields_present=False`). Done when: a dated verdict is recorded (recoverable — with the
      recovery mechanism identified — or genuinely not recoverable from any live source), committed to this doc's
      Progress Log. Repo: unified-api-contracts + instruments-service (read path) + market-tick-data-service
      (enrichment script, if recoverable). Source:
      `plans/active/issues/prediction_batch4_deferred_residuals_2026_08_16.md` todo 2 (line 92).

## Deferred

None — every item drafted here already cleared the conflict-check (verified against every `parent_epic:
predictions_master` active planning doc, the consolidated closeout, and prediction satellite batches 1-11; no
overlapping claim found — see the 2026-08-17 na-eligibility-audit run's Phase 2 notes).
