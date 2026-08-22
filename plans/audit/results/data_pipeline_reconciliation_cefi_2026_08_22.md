---
doc_type: audit-result
title: "Data-pipeline reconciliation — cefi (2026-08-22), raw-tick layer, Tier-1 only"
summary: >-
  Current production metadata confirms fresh market-data and instruments indexes, no consolidator lock, and a
  repeated fail-closed oversized-merge attempt. The current honest-coverage rollup remains 47.40 percent reachable
  coverage and a lower bound. The manifest axis census could not be safely re-measured in this slot because the
  required UTL runtime is unavailable; prior census values are explicitly not treated as current evidence.
status: partial
nature: record
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm, unified-api-contracts, market-tick-data-service]
scope: [engineer, admin]
tags: [reconciliation, canonicalisation, census, cefi, honest-coverage, consolidator-failed-closed, runtime-gap]
related: [four-surface-reconciliation-procedure, reconciliation-census-and-compute-tiers, honest-coverage-model, manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19]
created: 2026-08-22
date: 2026-08-22
auditor: "cefi_reconciliation_auditor (scheduled role, slot 28, dispatch agt-6b2e6d)"
parent_epic: security_and_cross_cutting_master
severity: P1
skill: data-pipeline-reconciliation
run_date: 2026-08-22
generated_at: 2026-08-22T14:15:00+00:00
audited_scope: "asset_group=cefi, raw-tick layer, PROD (-prd-) buckets only, read-only Tier-1 scheduled spot-check"
---

# Data-pipeline reconciliation — cefi (2026-08-22), raw-tick layer, Tier-1 only

**Read-only against production data** — no GCS writes, manifest writes, deletes, VM launches, path-oracle sweep, or
Tier-2 validation. This run directly verified production object metadata/status JSON, current coverage rollups, and
AWS mirror reachability. The manifest axis census was **not** fabricated: the slot lacks the UTL runtime dependency
(`python-dotenv`), so no current distinct-value counts are claimed.

## 0. Phase-0 reachability and freshness

| surface | GCP production result | AWS mirror result | assessment |
| --- | --- | --- | --- |
| market data | `market-data-tick-cefi-prd-central-element-323112` reachable; availability index generation `1787404515850034`, 471,050,320 bytes, updated `2026-08-22T13:15:15.864Z` | `market-data-tick-cefi-prd-427895769566` reachable; delimiter listing returned `KeyCount=0` | GCP index fresh at measurement; AWS mirror empty |
| instruments | `instruments-store-cefi-prd-central-element-323112` reachable; availability index generation `1787407241635843`, 2,996,906 bytes, updated `2026-08-22T14:00:41.646Z` | `instruments-store-cefi-prd-427895769566` reachable; delimiter listing returned `KeyCount=0` | healthy GCP index; AWS mirror empty |

Market-data `_index/consolidator.lock` was absent and `consolidator_stall_state.json` was `{"streak":0,"baseline_shards":110524}`. The latest attempt at `2026-08-22T14:01:48.379497Z` still failed closed:

```text
success=false, verdict=failed, shards_scanned=109403, shards_changed=0,
rows_in=0, rows_out=0, error_reason=marker_missing_oversized_merge:
109402 shards > 50000 — cron full merge infeasible
```

This is carried under the existing consolidator issue, not re-filed as a duplicate. A successful index write did
occur at `13:15:15Z`, so the failed run is an alerting/next-cycle reliability finding rather than evidence that the
index is currently unreadable. The consolidator must still be verified through a genuinely produced cycle under the
existing issue.

`phantom_audit_latest.json` remains stale: `generated_at=2026-07-27T17:38:18.042418Z`, `phantom_count=0`.
`reprobe_audit_latest.json` is current through `2026-08-22T09:01:09.331553Z` with `new_empties=0`,
`disagreements=0`, `proven=0`. Instruments-store has no phantom or reprobe artifacts, a standing coverage gap.

## 1. Manifest census

The current consolidated index is reachable and newer than the prior report, but the required census reader could not
run in this slot: the assigned workspace has no service `.venv`, and importing UTL fails immediately because
`python-dotenv` is unavailable. The deployment API axis-census route could not be used without its service bearer
credential. Therefore the following are **not current measurements** and are intentionally not repeated from the
2026-08-21 report:

- venue `M−C` drift counts;
- instrument-type counts;
- data-type drift counts;
- `C−M` orphan declarations.

This is a declared **coverage gap**, not a clean census. The next run must restore the documented UTL runtime or use the
deployed axis-census route, then re-measure from the current consolidated index with bounded predicate-pushdown reads.

## 2. Honest coverage

`central-element-323112-honest-coverage/2026-08-22/coverage.json` was found and generated at `2026-08-22T01:01:20Z`.
The CEFI rollup is unchanged from the preceding day:

| metric | CEFI value |
| --- | ---: |
| captured | 10,538,345 |
| attempted_failed | 855,304 |
| expected_unattempted | 10,839,811 |
| empty_confirmed | 6,602,176 |
| total | 28,835,636 |
| published reachable coverage | 47.40% |
| published all-shards coverage | 36.55% |
| denominator status | INCOMPLETE |
| instrument gates download | true |

Formula recheck using the SSOT reachable-coverage formula:
`10,538,345 / (10,538,345 + 855,304 + 10,839,811) = 47.40%` after rounding.
`empty_confirmed` is excluded from this reachable denominator. Because the denominator is incomplete and
`instrument_gates_download=true`, 47.40% is a lower bound, not a complete coverage claim.

## 3. Findings and follow-up

- **P1, carried/live:** the market-data CEFI consolidator continues to fail closed on an oversized unprovable merge;
  verify the deployed guard and a genuinely produced cycle under
  [`manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md`](/plans/active/issues/manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md).
- **P3, carried:** market-data `phantom_audit_latest.json` is 26 days stale at the time of this report.
- **Coverage gap:** instruments-store phantom/reprobe artifacts are absent.
- **Coverage gap:** current axis census was not measured because the slot's required UTL runtime is unavailable.

## 4. Todos

- [ ] [INFRA] P0. Verify the deployed CEFI consolidator guard and one genuinely produced post-guard cycle; do not clear the existing issue from `streak=0` alone.
- [ ] [INFRA] P3. Refresh the stale CEFI `phantom_audit` artifact.
- [ ] [DATA] P2. Re-run the bounded CEFI axis census from the current consolidated generation after restoring the UTL runtime or an authenticated axis-census route; classify venue, instrument-type, data-type, and `C−M` results with accepted suppressions.
- [ ] [INFRA] P3. Add or restore instruments-store phantom and reprobe artifacts, or document the approved coverage-gap disposition.

## 5. Explicitly out of scope

No machine-oracle path sweep, filename/id validation, parquet-content sample, Tier-2 VM, orphan-object scan, delete
proposal, GCS delimiter descent, service-code change, deployment, or VM launch was performed.

## 6. Evidence and method

- GCP object metadata and JSON status objects were read through the authenticated Cloud Storage JSON API; no objects
  were modified.
- AWS mirror reachability used read-only delimiter listings; both mirrors returned zero keys.
- Bucket names were the canonical production names from the prior UTL-resolved report; no `-test-` bucket was queried.
- Coverage values came directly from the current `coverage.json`; the formula was independently recalculated.
- The liveness endpoint was unavailable (`localhost:8765` refused the connection); the slot's required git fetch was
  also blocked by the read-only filesystem. These bootstrap limitations are recorded rather than hidden.

## Progress Log

- **cefi_reconciliation_auditor 2026-08-22** [dispatch agt-6b2e6d, slot 28]: Phase 0 and honest-coverage verification
  complete against production metadata. Market-data and instruments indexes are fresh; no lock is present; the
  consolidator still fails closed on `109402 > 50000` unprovable shards. The current axis census was not measured
  because UTL cannot import without `python-dotenv` in this slot; no stale census numbers were presented as current.
