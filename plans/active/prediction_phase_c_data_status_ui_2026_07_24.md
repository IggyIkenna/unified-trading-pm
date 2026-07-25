---
doc_type: plan
title: Prediction Phase C — data-status + honest-coverage UI (split from prediction_consolidated_closeout_2026_07_18)
summary:
  Phase C of the prediction consolidated close-out, split out verbatim (line-cap remediation, 2026-07-24) — RE-ADD the
  data-status "dimensions enumeration" view to deployment-ui/api, confirm honest-coverage rolls up prediction correctly
  + the daily scheduler fires, close the prediction UI drilldown + synthetic OTHER CQG bucket, and check the shared
  DP_CATALOG stale-alert (owned jointly with sports_master).
status: active
nature: process
asset_group: [prediction]
stage: [meta]
repos:
  [
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-service,
    deployment-api,
    deployment-ui,
    features-service,
    e2e-testing,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: [prediction, close-out, data-status, honest-coverage, ui, drilldown, canonical-question-group, dp-catalog]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_phase_ab_residuals_2026_07_24.md,
    /plans/active/prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md,
    /plans/active/prediction_phase_e_football_arb_live_2026_07_24.md,
    /plans/active/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [prediction_phase_ab_residuals_2026_07_24]
gate_on_depends: true
source: >-
  Split from `prediction_consolidated_closeout_2026_07_18.md` (Phase C section, lines 344-369 of that doc as of
  2026-07-18/2026-07-24) per the operator-approved line-cap remediation triage
  `plans/active/issues/plan_line_cap_remediation_2026_07_23.md` (row 22, "4-way split along the plan's own Phase A-E
  boundaries"). Content moved verbatim, not summarized. `depends_on` + `gate_on_depends: true` added 2026-07-24 (plan
  audit finding) to encode this doc's own header text ("gated on Phase B") as a real dispatch gate, matching the Phase E
  sibling's already-correct pattern — Phase B is now carried by `prediction_phase_ab_residuals_2026_07_24.md`.
---

# Prediction Phase C — data-status + honest-coverage UI

> **Split from `prediction_consolidated_closeout_2026_07_18.md` (2026-07-24).** This is the Phase C section of that
> close-out, moved verbatim. For the full historical execution narrative (Progress Log, ticks 1-31, 2026-07-18 through
> 2026-07-20) and shared cross-phase context (the Ground-truth verdict table, the prediction shard-atom definition, the
> MVP universe scope), see the parent doc — none of that content is duplicated here. Sibling phase children:
> `prediction_phase_ab_residuals_2026_07_24.md` (Phase A-B),
> `prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md` (Phase D),
> `prediction_phase_e_football_arb_live_2026_07_24.md` (Phase E — gated on this plan's Phase-B sibling + Phase D).

## Phase C — data-status + honest-coverage (gated on Phase B)

- [ ] [UI] P0. **RE-ADD the data-status "dimensions enumeration" view to deployment-ui/api (operator, 2026-07-18 — "I
      really need to add it back").** Per asset_group, list every distinct `instrument_type` / `data_type` / `venue` /
      `canonical_question_group` present in the manifest/GCS honest-coverage rollup WITH counts, so non-canonical
      naming + duplications are VISIBLE — the standing canonical-drift detector (how we catch the next drift without a
      manual parquet read). NOTE: the underlying query already exists today —
      `GET /data-status/catalogue-filter-options` (`deployment-api/.../routes/data_status/_catalogue.py`) returns
      distinct `{venues, instrument_types, data_types}` and `GET /data-status/prediction-catalogue` returns `cqg_counts`
      — so this is mostly a UI dimensions-panel + wiring task, plus adding the counts/CQG axis to the panel. pw:L2 ✓ +
      regression required for the UI leg. Mirrors the identical tradfi Phase-C todo. (repos: deployment-api,
      deployment-ui)
- [ ] [BACKEND] P1. **Honest-coverage green for prediction** — confirm `measure_honest_coverage.py` rolls up prediction
      correctly once the CQG cluster rows exist again (output
      `gs://central-element-323112-honest-coverage/{date}/coverage.json`); verify the daily scheduler actually fires
      (`measure_honest_coverage.py` header says `last_executed: NEVER`; the Cloud Scheduler `honest-coverage-daily`
      create was pending — `gcloud scheduler jobs describe honest-coverage-daily     --location=asia-northeast1`).
      (repos: instruments-service, deployment-service)
- [ ] [BACKEND] P1. **Close the prediction UI drilldown + synthetic OTHER CQG bucket** — the 3 residuals on the
      catch-all `OTHER` canonical-question-group bucket end-to-end + the deployment-ui 3-level drilldown
      (`venue → canonical_question_group → day`). `predictions_other_bucket_and_ui_drilldown_2026_06_20.md` (3 open).
      (repos: deployment-api, deployment-ui)
- [ ] [BACKEND] P2. **DP_CATALOG stale alert (shared w/ sports)** — the `DP_CATALOG_NOT_RUNNING` alert fired for both
      sports + prediction `prod/catalog.parquet` (~25h stale); confirm the prediction catalogue writer runs on schedule.
      Cross-link `issues/dp_catalog_not_running_sports_prediction_2026_07_15.md` (owned jointly with sports_master).

## Progress Log

- **2026-07-24 (plan-hygiene split) — forked from `prediction_consolidated_closeout_2026_07_18.md`.** This plan carries
  forward the Phase C section verbatim (0 done / 4 open todos at split time). See the parent's Progress Log (ticks 1-31)
  for the full session-by-session history of the prediction close-out overall; none of those ticks closed a Phase C
  item, so there is no Phase-C-specific history to carry forward yet. Future work on this plan logs new entries below.
