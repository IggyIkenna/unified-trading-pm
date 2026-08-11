---
doc_type: audit-result
title: Verdict pack — PREDICTION (G4 pre-apply, R7/R3 2026-06-11)
summary:
  PREDICTION G4 pre-apply verdict (06-11) — projected v9 545,855 rows; legacy category=/data_source= parser added
  (573,536 of 578,162 now parse); removed=3,588 legacy raw-grain superseded by cqg bundle atom. OPEN P1 BLOCKER — cqg
  classifier covers only 1,355/573,536 objects (94.5% ClassifierConfidenceLow), UAC registry decision needed.
status: partial
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [manifest, honest-coverage, data-status, prediction, migration, canonicalisation, uac, escalation]

  - /plans/audit/results/r3_beta_renders_2026_06_11/verdict_cefi.md
  - ../r3_verdict_packs_2026_06_17/verdict_prediction.md
created: 2026-06-11
audited_scope:
  PREDICTION projected-v9 index vs live _index (G4 dry-run), cqg-bundle atom migration diff + cqg-classifier coverage
  assessment
date: 2026-06-11
auditor: ikennaigboaka
parent_epic: predictions_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
---

# Verdict pack — PREDICTION (G4 pre-apply, R7/R3 2026-06-11)

**Projection**: 545,855 rows. Legacy `category=/data_source=` parser added (578,162 pre-apply objects were 99.5%
unparseable → 573,536 parse).

**Adjudicated diff**: removed=3,588 (legacy raw-grain trades/prediction_trades cells superseded BY DESIGN by the cqg
bundle atom) · captured_regressions=4 (trace to the classifier finding below).

**OPEN P1 (operator decision PRE-APPLY)**: the cqg classifier covers only 1,355 of 573,536 objects — 94.5% land
ClassifierConfidenceLow; captured bundles end 2026-04-14. UAC registry decision needed before the prediction apply. The
prediction dry-plan sign-off rides this decision.

**Evidence**: beta/live renders. Sweep: E=0/unknown=0 (19:02Z).

**G4 --apply for prediction: AWAITING OPERATOR (blocked on cqg-classifier P1)**
