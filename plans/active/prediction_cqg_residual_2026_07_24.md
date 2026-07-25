---
doc_type: plan
title: Prediction cqg-classifier coverage residual — forked from migration_verification_orphan_safety_2026_06_10
summary: >-
  2 small residual todos forked out of the archived migration-verification/orphan-safety harness plan (2026-07-24 plan
  line-cap remediation split): the operator-gated prediction cqg-classifier coverage decision (before the pred G4 apply)
  and the downstream cqg-grain catalogue wiring it gates.
status: active
nature: process
asset_group:
  [prediction] # corrected 2026-07-25 (ag-closeout-audit orthogonality fix) -- was [cross-cutting], a genuine
  # mistag: cqg-classifier coverage is prediction-market-specific, inherited the parent harness's cross-cutting
  # tag on fork instead of being corrected to its real single-AG scope
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    deployment-ui,
    features-service,
    instruments-service,
    market-data-processing-service,
  ]
scope: [engineer, admin]
tags: [prediction, cqg, classifier, manifest, migration, plan-split, residual]
related:
  [
    /plans/archive/migration_verification_orphan_safety_2026_06_10.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-07-24"
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: design
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.9
assigned_role: data_engineering
drift_direction: advance-code
last_updated: "2026-07-24"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Forked verbatim from `plans/archive/migration_verification_orphan_safety_2026_06_10.md` (its own Progress Log, entries
  dated 2026-06-11 / 2026-06-16) as part of the 2026-07-24 plan line-cap remediation
  (`plans/active/issues/plan_line_cap_remediation_2026_07_23.md`, row 18 / bucket (d)). The parent plan's durable
  protocol (CF-15…CF-21) had already migrated to codex; these 2 todos were the last genuinely-open items in its
  prediction-cqg thread and are tracked here going forward.
---

# Prediction cqg-classifier coverage residual

> **Origin.** This plan is a **fork**, not a new investigation — both todos below are moved **verbatim** from
> `plans/archive/migration_verification_orphan_safety_2026_06_10.md` (now trimmed + unlocked; its full historical
> Progress Log is archived to `plans/audit/results/migration_orphan_safety_goalpost_verification_2026_06_10.md` as an
> Appendix). Read that appendix for the surrounding narrative/evidence if deeper context is needed — nothing below has
> been rewritten or summarized from the original.
>
> **Ordering note**: item 1 (the classifier coverage decision) is the operator-gated prerequisite item 2 references as
> "Blocked-on: 338" — resolve item 1 first.

## Todos

- [ ] [DATA] P1. **Prediction cqg classifier coverage decision BEFORE the pred G4 apply**: 542,169/573,536 objects
      (94.5%) route to `attempted_failed[ClassifierConfidenceLow]` under the operator-corrected contract (None → NOT
      bundled, no "OTHER" fallback), and captured cqg bundles END 2026-04-14 (the 4 trail dates 2026-04-26..29 have real
      trades objects but ZERO classifiable bundles → honest captured→failed downgrade at the canonical grain). Either
      EXTEND the UAC `canonical_question_group` registry coverage (most Polymarket markets are
      sports/politics/entertainment outside the MVP crypto set) or operator-ratify that out-of-registry markets stay
      failed-for-retry. Repos: unified-api-contracts (+ rebuild re-run). Provenance: /tmp/r7_proj/prediction2.log
      2026-06-11.
- [ ] [DATA] P2. **249-b — prediction cqg grain (`prediction_canonical_question_group`) — GATED on operator
      decision 338.** The cqg grain needs deriving the canonical-question-group per conditionId, which is the
      operator-gated cqg-classifier coverage decision (338: 94.5% of objects route to `ClassifierConfidenceLow`). The
      rollup already materialises the cqg grain when `cqg_str` is non-empty (the loader yields `cqg=""` today) — once
      338 resolves the cqg-classifier coverage, wire the cqg into the loader (from the classifier or a
      `_canonical_group` write-back) and the cqg-grain rows emit automatically. Repo: instruments-service +
      unified-api-contracts. Blocked-on: 338.

## Success criteria

1. Operator decision recorded on cqg-classifier registry coverage (extend vs ratify out-of-registry-stays-failed).
2. `prediction_canonical_question_group` cqg-grain rows emit from the catalogue rollup once item 1 resolves; verified by
   re-running `build_instrument_catalogue --asset-group prediction` and reading the promoted `catalog.parquet` back.

## Progress Log

- 2026-07-24 — plan forked from `migration_verification_orphan_safety_2026_06_10.md` (line-cap remediation split); no
  work done yet on either todo beyond what the parent's archived Progress Log already recorded.
