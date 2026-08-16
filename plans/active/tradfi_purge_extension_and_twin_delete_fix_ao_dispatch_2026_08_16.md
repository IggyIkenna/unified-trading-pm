---
doc_type: plan
title: TradFi residual catalogue-leg purge extension + twin-delete lookup-bug fix
summary: >-
  Operator-ruled 2026-08-16 (na-eligibility-audit follow-up Q&A round 3) — two TradFi items:
  extend the already-granted 4-leg operator go-ahead to the residual 2-leg catalogue purge
  (NASDAQ/NYSE SPOT_PAIR mis-classification, 318 rows + 12 cefi-singles EQUITY/EQUITY-USD
  rows), and fix the suspected canonical_twin_path() lookup-logic bug BEFORE trusting the 0%
  twin-coverage measurement that gates the legacy-twin bucket delete.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [instruments-service, market-tick-data-service, deployment-service]
scope: [engineer]
tags: [tradfi, canonicalization, manifest, gcs-delete]
related:
  [
    /plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md,
    /plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: data_engineering
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 3, 2026-08-16"
locked_by:
context_scope:
  [
    /plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md,
    /plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
locked_since:
resolved_by:
---

# TradFi residual catalogue-leg purge extension + twin-delete lookup-bug fix

## Todos

- [ ] [DATA] P2. Execute the residual catalogue-leg purge (NASDAQ/NYSE SPOT_PAIR mis-classification, 318 rows, plus
      12 cefi-singles EQUITY/EQUITY-USD rows) from `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` — operator
      extended the already-granted 4-leg go-ahead to cover this residual 2-leg set 2026-08-16. Same mis-classification
      class as the 4 already-approved legs. (repo: instruments-service)
- [ ] [DATA] P1. Investigate and fix the suspected `canonical_twin_path()` lookup-logic bug (root-cause finding dated
      2026-08-09 in `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`) BEFORE trusting the 0% twin-coverage
      measurement that gates the legacy-twin bucket delete. Re-measure twin coverage after the fix. The existing
      "auto-execute once coverage clears 100%" rule stays in force — this todo just makes sure that measurement is
      trustworthy before it's allowed to fire. Do not delete anything as part of this todo; that stays gated on the
      re-measured coverage. (repos: instruments-service, market-tick-data-service, deployment-service)

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 3, operator ruling)**: extracted from
  `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` and `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`.
  The delete itself remains gated on 100% measured twin coverage post-fix — this plan does not authorize the delete,
  only the lookup-bug investigation that determines whether the current 0% measurement can be trusted.
