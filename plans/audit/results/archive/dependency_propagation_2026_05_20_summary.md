---
doc_type: audit-result
title: A5 — Dependency-fail propagation summary
summary:
  A5 automated dependency-fail propagation scan (4757 files, 40 EmptyConfirmedReason members) — 5 review-blocking
  warn-but-proceed files across ml-inference/ml/strategy/features batch handlers; 0 silent catches / blank reasons /
  freeform reasons detected; recommends a new check_dependency_fail_propagation.py QG ratchet.
status: fail
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    execution-service,
    features-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    ml-service,
  ]
scope: [engineer, admin]
tags: [audit, data-correctness, quality-gates, data-pipeline, ml, features]
related: [/plans/audit/results/archive/dependency_propagation_2026_05_20.md]
created: 2026-05-20
audited_scope:
  4757 files across 9 consumer services scanned per service×mode for DependencyError/StaleUpstreamError raises, silent
  catches, blank/freeform reason literals, warn-but-proceed patterns
date: 2026-05-20
auditor: semver
parent_epic: infrastructure_master
severity: P0
resulting_plan:
lib_version:
doc_versions_checked:
---

# A5 — Dependency-fail propagation summary

_Generated: 2026-05-20T11:27:22.909293+00:00_

Files scanned: 4757

Known EmptyConfirmedReason enum members harvested from UAC: 40

## Per-service × mode summary

| Service                        | Batch handlers | Live handlers | Files raising DependencyError | Files raising StaleUpstreamError | Silent catches | Blank `reason=""` | Freeform reason |
| ------------------------------ | -------------: | ------------: | ----------------------------: | -------------------------------: | -------------: | ----------------: | --------------: |
| execution-service              |              3 |             0 |                             3 |                                1 |              0 |                 0 |               0 |
| features-service               |              7 |             0 |                             5 |                                0 |              0 |                 0 |               0 |
| instruments-service            |              0 |             0 |                             1 |                                0 |              0 |                 0 |               0 |
| market-data-processing-service |              0 |             0 |                             3 |                                0 |              0 |                 0 |               0 |
| market-tick-data-service       |              1 |             0 |                             0 |                                0 |              0 |                 0 |               0 |
| ml-inference-service           |              1 |             1 |                             2 |                                0 |              0 |                 0 |               0 |
| ml-service                     |              1 |             1 |                             4 |                                0 |              0 |                 0 |               0 |
| ml-training-service            |              0 |             0 |                             2 |                                0 |              0 |                 0 |               0 |
| strategy-service               |              3 |             0 |                             2 |                                2 |              0 |                 0 |               0 |

## Review-blocking violations (silent catches + blank reasons + freeform reasons)

Per the data-pipeline-correctness HARD RULE, every consumer-side miss MUST raise loudly (batch) or raise
StaleUpstreamError (live). Patterns below are **all** the silent-swallowing patterns the scanner detected.

Total files with review-blocking violations: **5**

### `ml-inference-service/ml_inference_service/cli/handlers/batch_handler.py` (batch_handler)

- Warn-but-proceed pattern (lines): [79, 259]

### `ml-service/ml_service/inference/cli/handlers/batch_handler.py` (batch_handler)

- Warn-but-proceed pattern (lines): [79, 259]

### `strategy-service/strategy_service/cli/handlers/batch_handler.py` (batch_handler)

- Warn-but-proceed pattern (lines): [130, 502]

### `features-service/features_service/commodity/adapters/eia_ng.py` (batch_handler)

- Warn-but-proceed pattern (lines): [70]

### `features-service/features_service/commodity/adapters/eia_crude.py` (batch_handler)

- Warn-but-proceed pattern (lines): [61]

## Next actions

- Every review-blocking violation must be either (a) fixed in code (raise loudly), or (b) given an operator-acked
  `BLOCKED-OPERATOR-DECISION` explaining why the silent path is correct.
- Wire a new QG step `scripts/quality_gates/check_dependency_fail_propagation.py` that ratchets these counts down per
  service × mode.
- Per CLAUDE.md HARD RULE, slots doing layer-N+1 work on services with open A5 violations are review-blocked.
