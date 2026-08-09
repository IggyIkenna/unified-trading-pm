---
doc_type: plan
title:
  Cross-cutting satellite AO batch 8 — instruments_master bounded residual (MVP-toggle real-data verify) extracted from
  the round9 2026-08-09 sweep
summary: >-
  Eighth AO-dispatch batch for the cross-cutting tranche, produced by the round9 2026-08-09 RECLASSIFY +
  satellite-extraction sweep. Pulls 1 bounded item out of `mvp_scope_catalogue_tagging_2026_06_08.md`
  (`instruments_master`): the real-data verify of the MVP data-status toggle (`scope=mvp|could_exist|all`), flagged as
  a likely-AO-eligible candidate by two prior na-eligibility-audit passes (2026-08-07, 2026-08-08) but never extracted
  because it shared the doc with a genuinely operator-gated design question. That design question (features/strategy/
  model MVP sections) has since been substantially resolved via prior extractions (P2a → batch1b, P2b shipped, P2b-2 →
  batch2), so this pass extracts the one remaining bounded item on its own.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta, data]
repos: [deployment-api, instruments-service]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-8, satellite-docs, instruments-master, mvp-scope]
related:
  [
    /plans/active/mvp_scope_catalogue_tagging_2026_06_08.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/mvp_scope_catalogue_tagging_2026_06_08.md,
    deployment-api/deployment_api/routes/data_status/_coverage_scope.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/mvp_scope.py,
  ]
source: >-
  round9 RECLASSIFY + satellite-batch-extraction sweep 2026-08-09 (cross-cutting tranche); this specific item was
  previously flagged `MISCLASSIFIED_LIKELY_AO_ELIGIBLE` by na-eligibility-audit 2026-08-07/08-08 but never extracted.
assigned_role: data_engineering
effort: medium
sequential: false
drift_direction: advance-code
---

# Cross-cutting satellite AO batch 8 (instruments_master) — bounded-item extraction

> **Status: active.** Single-todo batch — exempt from the finalize-twin requirement per
> `check_finalize_plan_coverage.py`'s single-open-todo carve-out; archival folds into this todo's own done-when.

## Todos

- [ ] [DATA] P2. **Real-data verify of the MVP data-status toggle.** Source: `mvp_scope_catalogue_tagging_2026_06_08.md`
      (its "Verify" `[DATA] P2` todo, line ~215). Unit-level parity is already covered
      (`deployment-api@3390c98`'s `test_route_venue_year_coverage_scope.py` asserts denominator monotonicity
      `mvp ≤ could_exist ≤ all`) — this todo is the real-DATA verify against live GCP/manifest state: (1) re-confirm
      the 5 per-AG instruments consolidators are still ENABLED with a fresh `_index` heartbeat (the doc's own prior
      note says this was true as of `mvp_catalogue_finalization_v10_2026_06_27.md` G0, 2026-06-27 — needs a fresh
      re-check, not assumed still true 6+ weeks later); (2) once confirmed, hit
      `GET /api/data-status/venue-year-coverage?scope=mvp` vs `?scope=could_exist` vs `?scope=all` for a sample
      asset_group and confirm: with MVP ON, coverage reads ~100% for captured MVP cells and does NOT count non-MVP
      catalogued instruments as missing; with MVP OFF, the full could-exist universe is shown (the gap is honest, not
      hidden). Done when: both checks are run against live prod (or `-test`) infra with cited evidence (consolidator
      heartbeat timestamp; sample API response showing the expected monotonic relationship), and the source doc's own
      "Verify" checkbox is flipped citing this evidence. Repo: deployment-api + instruments-service (read-only
      verification, no code change expected unless the verify surfaces a real gap — if so, file that as its own
      finding per the standard findings-triage rule, don't fix it inline here).

## Progress Log

- **2026-08-09**: Batch authored via the round9 cross-cutting RECLASSIFY + satellite-extraction sweep. 1 item
  extracted — flagged by na-eligibility-audit twice (2026-08-07, 2026-08-08) as "closer to a bounded check... possible
  MISCLASSIFIED_LIKELY_AO_ELIGIBLE" but never previously extracted; the source doc's other design-call item has since
  been resolved/extracted separately (P2a → `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`, P2b shipped
  `unified-api-contracts@0fb9821b`, P2b-2 → `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md`), leaving this
  as the one clean remaining bounded item.
