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
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
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
  `/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md` (row 22, "4-way split along the plan's own Phase A-E
  boundaries"). Content moved verbatim, not summarized. `depends_on` + `gate_on_depends: true` added 2026-07-24 (plan
  audit finding) to encode this doc's own header text ("gated on Phase B") as a real dispatch gate, matching the Phase E
  sibling's already-correct pattern — Phase B is now carried by `prediction_phase_ab_residuals_2026_07_24.md`.
context_scope:
  [
    /plans/active/prediction_phase_ab_residuals_2026_07_24.md,
    /plans/archive/2026_08/predictions_other_bucket_and_ui_drilldown_2026_06_20.md,
    deployment-api/deployment_api/routes/data_status/_catalogue.py,
    instruments-service/scripts/measure_honest_coverage.py,
    deployment-ui/src/components/AxisValueCensus.tsx,
  ]
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
      create was pending — `gcloud scheduler jobs describe honest-coverage-daily --location=asia-northeast1`). (repos:
      instruments-service, deployment-service)
- [x] ✅ [BACKEND] P1. **DONE 2026-08-07 — pointer target closed.** The sole remaining open item in
      `predictions_other_bucket_and_ui_drilldown_2026_06_20.md`'s P0 section (the pw:L2 VERIFY gate) is now done — 5/5
      playwright tests passing (`tests/smoke/prediction_v9_breakdown.spec.ts`), see that doc's Progress Log for full
      evidence. The catch-all `OTHER` CQG bucket + deployment-ui 3-level drilldown are both shipped and verified.
      (repos: deployment-api, deployment-ui)
- [x] [BACKEND] P2. ✅ **DP_CATALOG stale alert (shared w/ sports)** — the `DP_CATALOG_NOT_RUNNING` alert fired for both
      sports + prediction `prod/catalog.parquet` (~25h stale); confirm the prediction catalogue writer runs on schedule.
      Cross-link `/plans/archive/issues/dp_catalog_not_running_sports_prediction_2026_07_15.md` (owned jointly with
      sports_master; archived 2026-07-30 — doc reached 0 open todos). **DONE (na-eligibility-audit 2026-08-03)** — the
      cited doc's own RE-TRIAGE (2026-07-23) entry directly confirms this: `lifecycle-catalogue-regen-prediction` fixed
      via the 2026-07-15 Cloud Run memory bump (deployment-service@6bfa284) and live-verified promoting daily without
      incident (`prod/catalog.parquet` update time 2026-07-23 01:03:17Z, ~7.8h old, well under the 24h threshold) — "no
      further staleness alerts implied by these fresh timestamps."

## Progress Log

- **na-eligibility-audit 2026-07-31 (prediction tranche)**: KEEP-NA, valid — 4 open, unchanged since the 2026-07-30
  marker (this file's only intervening edit was a referrer-path fix elsewhere in the corpus repointing an archived
  cross-link, not a content change to this doc's own scope). The real
  `depends_on: [prediction_phase_ab_residuals_2026_07_24]`
  - `gate_on_depends: true` gate is re-confirmed still live — the prerequisite doc still carries 7 open todos as of this
    same run. KEEP-NA on that citation alone, per the skill's own rule. Doc stays NA.

- **na-eligibility-audit 2026-07-30 (prediction tranche)**: KEEP-NA, valid — 4 open, and the doc carries
  `depends_on: [prediction_phase_ab_residuals_2026_07_24]` + `gate_on_depends: true` against a prerequisite that is
  still open (9 todos). Per this skill's own rule, a real `depends_on`+`gate_on_depends` gate on a still-open
  prerequisite is KEEP-NA on that citation alone — gate confirmed real by direct read of both docs, not assumed. The P0
  UI item additionally carries the workspace playwright gate.

- **2026-07-24 (plan-hygiene split) — forked from `prediction_consolidated_closeout_2026_07_18.md`.** This plan carries
  forward the Phase C section verbatim (0 done / 4 open todos at split time). See the parent's Progress Log (ticks 1-31)
  for the full session-by-session history of the prediction close-out overall; none of those ticks closed a Phase C
  item, so there is no Phase-C-specific history to carry forward yet. Future work on this plan logs new entries below.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) -- swapped in the real gating dependency
  (phase_ab_residuals), todo 3's target doc, and 2 source paths (the existing catalogue-filter query + the honest-
  coverage script).
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — 2 open items;
  `depends_on: [prediction_phase_ab_residuals_2026_07_24]`
  - `gate_on_depends: true` re-confirmed live — the prerequisite still has 7 open todos and Phase-B `--apply` hasn't
    started, so this doc's own dispatch gate isn't cleared yet.

- **round11 RECLASSIFY + satellite-extraction sweep 2026-08-09 (prediction tranche)**: KEEP-NA, valid — re-checked
  against the full round-11 precedent set (IAM self-service default, D16 all-repos carve, S5.1 tiering,
  plan-destination-default-to-AO for auto-filed findings, escalation-N=3-days, reversibility-qualified deletes
  agent-executable after a fresh check, Option B retirement, GSM secret `deepseek-v4-pro-api-key` + 5 Slack webhooks) —
  none of these clear a `depends_on`+`gate_on_depends: true` mechanical gate; re-confirmed live that
  `prediction_phase_ab_residuals_2026_07_24` still carries 7 open todos. Gate not cleared. No reclassification.
- **na-eligibility-audit 2026-08-10 (prediction tranche)**: KEEP-NA, valid — re-verified live, 2 open, unchanged.
  `depends_on: [prediction_phase_ab_residuals_2026_07_24]` + `gate_on_depends: true` still open (prerequisite still
  status:active, **CORRECTED 2026-08-16 (plan_reconciler): 6 open todos, not 7** — dropped 7→6 on 2026-08-15 per the
  closeout hub's own re-verified snapshot). Doc stays NA — gate conclusion unaffected by the count correction.

- **na-eligibility-audit 2026-08-17** [body-hash:fc1a49343a0f6665]: KEEP-NA, valid — 2 open (RE-ADD data-status
  dimensions-enumeration UI view, honest-coverage green verification). `depends_on:
  [prediction_phase_ab_residuals_2026_07_24]` + `gate_on_depends: true` re-confirmed live — prerequisite still carries
  6 open todos, gate not cleared. KEEP-NA on that citation alone, consistent with 5 prior audit passes (07-30 through
  08-10). Doc stays NA.

- **na-eligibility-audit 2026-08-17 (prediction tranche, re-verify)** [body-hash:fdb7258ca90655c0]: KEEP-NA, valid —
  real `depends_on: [prediction_phase_ab_residuals_2026_07_24]` + `gate_on_depends: true` gate re-confirmed still
  open (6 todos) — KEEP-NA on that citation alone. Separate finding, not overriding the gate: the dimensions-
  enumeration panel this doc's P0 todo asks for has substantially shipped cross-cuttingly via Track-6
  (`deployment-ui@3fb6779` AxisValueCensus panel), though the CQG-axis addition the todo also names is confirmed
  still missing (0 `cqg`/`canonical_question_group` hits in either shipped file) — real residual scope survives once
  the gate clears. Doc stays NA.

- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries) -- added
  deployment-ui/src/components/AxisValueCensus.tsx, the shipped panel the residual CQG-axis addition needs to land in
  per the 2026-08-17 na-eligibility-audit finding directly above.
- **na-eligibility-audit 2026-08-18** [body-hash:201325ea5c74f377]: KEEP-NA, valid -- depends_on+gate_on_depends:true on prediction_phase_ab_residuals_2026_07_24 re-confirmed live still open (status:active, 4 open todos). Doc stays NA on the citation alone, per the never-re-litigate rule.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries).
