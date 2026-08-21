---
doc_type: audit-result
title: "Data-pipeline reconciliation — cefi (2026-08-21), raw-tick layer, Tier-1 only"
summary: >-
  Scheduled CEFI Tier-1 reconciliation. The production market-data consolidator's latest cycle failed closed because
  108714 shards exceeded the unprovable-merge limit; the last successful canonical index write remains readable and
  is under the 24-hour freshness budget. Instruments-store is healthy. The bounded manifest census finds four genuine
  venue dialects, 58655 rows across unregistered data types, and 3910 index instrument-type rows; the prior lowercase
  casing residual is now zero. Honest coverage increased to 47.40 percent but remains a lower bound because its
  denominator is incomplete and instrument-gated.
status: partial
nature: record
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm, unified-api-contracts, market-tick-data-service]
scope: [engineer, admin]
tags: [reconciliation, canonicalisation, census, cefi, honest-coverage, consolidator-failed-closed, depth-of-book-10-carried]
related: [four-surface-reconciliation-procedure, reconciliation-finding-taxonomy, reconciliation-census-and-compute-tiers, honest-coverage-model, manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19]
created: 2026-08-21
date: 2026-08-21
auditor: "cefi_reconciliation_auditor (scheduled role, slot 28, dispatch agt-26e8f2)"
parent_epic: security_and_cross_cutting_master
severity: P1
skill: data-pipeline-reconciliation
run_date: 2026-08-21
generated_at: 2026-08-21T04:46:57+00:00
audited_scope: "asset_group=cefi, raw-tick layer, PROD (-prd-) buckets only, read-only Tier-1 scheduled spot-check"
resulting_plan:
lib_version:
doc_versions_checked:
---

# Data-pipeline reconciliation — cefi (2026-08-21), raw-tick layer, Tier-1 only

**Read-only against production data** — no GCS writes, manifest writes, deletes, VM launches, path-oracle sweep, or
Tier-2 validation. This scheduled role covers Phase 0 reachability/freshness, the §3f distinct-value census, and
honest-coverage verification. The manifest census used bounded calendar-year reads with predicate pushdown; it did not
perform a whole-corpus object walk.

## 0. Phase-0 reachability and freshness

| surface | GCP production result | AWS mirror result | assessment |
| --- | --- | --- | --- |
| market data | `market-data-tick-cefi-prd-central-element-323112` reachable; `_index/availability_index.parquet` generation `1787254157655029`, 469,897,537 bytes, last modified `2026-08-20T19:29:17.669Z` | `market-data-tick-cefi-prd-427895769566` reachable, but no top-level prefixes and no index object | Last successful index write is ~8.6 hours old at measurement, within the 24-hour budget. |
| instruments | `instruments-store-cefi-prd-central-element-323112` reachable; availability index 2,848,368 bytes, last modified `2026-08-21T04:01:22.624Z`, generation `1787284882609783` | `instruments-store-cefi-prd-427895769566` reachable, but empty at top level | Healthy current GCP index; AWS mirror remains empty. |

The market-data `_index/consolidator.lock` was absent and `_index/consolidator_stall_state.json` reported
`{"streak":0,"baseline_shards":110524}`. However, the latest market-data `_index/latest.json` attempt at
`2026-08-21T04:02:23.085Z` failed closed:

```text
success=false, verdict=failed, shards_scanned=108715, shards_changed=0,
error_reason=marker_missing_oversized_merge: 108714 shards > 50000 — cron full merge infeasible
```

This is corroborated by the existing open P0 issue
[`manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md`](/plans/active/issues/manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md), whose shipped guard is intended to fail closed and alert rather than re-enter the historical timeout/lock wedge. It is not reported as a duplicate issue here. The consolidated census below is therefore explicitly based on the last successful index generation, not on the failed attempt.

Other market-data artifacts: `phantom_audit_latest.json` is stale (generated `2026-07-27T17:38:18Z`, 24 days old),
`reprobe_audit_latest.json` is current through `2026-08-20T09:00:58Z` (`new_empties=13`, `disagreements=9`), and no
lock was held at the probe. Instruments-store has no phantom or reprobe artifacts, a standing coverage gap.

## 1. Manifest census

The last successful consolidated manifest contained **30,764,419 rows**, read as eight bounded date windows:

| capture status | rows |
| --- | ---: |
| captured | 10,888,214 |
| empty_confirmed | 7,155,106 |
| attempted_failed | 1,156,302 |
| expected_unattempted | 11,564,797 |
| total | 30,764,419 |

All 25 UAC-declared CEFI venues had manifest presence (no C−M orphan declaration). The UAC canonical venue registry
and `CEFI_VENUE_ACCEPTED_NONCANONICAL_ALIASES` were checked before classifying drift.

### Venue axis

Accepted aliases, suppressed rather than filed as findings: `BYBIT-FUTURES` 30,782 rows (30,782
`empty_confirmed`), `OKEX-FUTURES` 36 rows (all `empty_confirmed`), and `CRYPTOFACILITIES` 10 rows (all
`empty_confirmed`), **30,828 rows total**. These are live registry-approved dialects, not canonicalization failures.

Genuine unaccepted M−C values, **10,067 rows total**:

- `OKX`: 5,225, all `attempted_failed`.
- `BINANCE-DELIVERY`: 4,838 (`empty_confirmed=4,255`, `attempted_failed=578`, `captured=5`).
- `KALSHI_PERP`: 2, all `attempted_failed`.
- `OKX-OPTIONS`: 2, all `attempted_failed`.

These are carried findings; no new issue document was created because the values and counts are already represented by
the daily CEFI reconciliation trail. No GCS path/content oracle was run in this role.

### Instrument-type and data-type axes

- The previously observed lowercase casing residuals are now **zero** in the current consolidated index:
  `perpetual=0`, `future=0`, `spot_pair=0`. This confirms no observed regrowth of the shipped active-writer casing fix.
- `index`: 3,910 rows, all `captured`; this remains a noncanonical instrument-type value and is carried for the
  existing CEFI registry-gap follow-up.
- The accepted bundle-grain values `futures_chain` and `options_chain` remain governed by the UAC/MTDS accepted
  bundle exception; they were not promoted to findings.
- Unregistered data types: `depth_of_book_10` **58,634** rows (`captured=20,939`, `empty_confirmed=37,629`,
  `attempted_failed=66`); `perp_daily_ctx` **11** rows (all `captured`); and `ohlcv_15m`, `ohlcv_15s`, `ohlcv_1d`,
  `ohlcv_1h`, `ohlcv_5m` **2 each** (10 total, all `captured`). Combined data-type drift is **58,655 rows**.
- `chain` is blank for the CEFI manifest and is not treated as a finding because chain is inapplicable to this asset
  group under the canonical schema.

`depth_of_book_10` is carried against the existing open corrective-migration issue
[`dp_fetch_009_cefi_depth_of_book_10_corrective_migration_overreach_2026_08_16.md`](/plans/active/issues/dp_fetch_009_cefi_depth_of_book_10_corrective_migration_overreach_2026_08_16.md); this run does not create a duplicate.

## 2. Honest coverage

No `2026-08-21/coverage.json` existed at measurement. The freshest rollup was
`2026-08-20/coverage.json`, generated `2026-08-20T20:56:32Z` in
`central-element-323112-honest-coverage`:

| metric | CEFI value |
| --- | ---: |
| captured | 10,538,345 |
| attempted_failed | 855,304 |
| expected_unattempted | 10,839,811 |
| empty_confirmed | 6,602,176 |
| total | 28,835,636 |
| published reachable coverage | 47.40% |
| published all-shards coverage | 36.55% |
| out-of-window | 82.57% |
| denominator status | INCOMPLETE |
| instrument gates download | true |

Formula recheck: `10,538,345 / (10,538,345 + 855,304 + 10,839,811) = 47.40%`, matching the published value after
rounding. Because `denominator_complete=false` and `instrument_gates_download=true`, 47.40% is a lower bound, not a
complete coverage claim. The rollup improved from 45.57% on 2026-08-19, while layer-1 completeness decreased from
94.52% to 90.79%; the denominator change is not interpreted as a data regression without a complete denominator.

## 3. Findings and follow-up

1. **P1, carried/live:** the latest market-data consolidator cycle failed closed on the oversized unprovable merge.
   Verify the deployed cron image and a subsequent genuine successful cycle under the existing P0 issue; do not clear
   the finding based only on `streak=0` or a successful process exit.
2. **P2, carried:** resolve or explicitly accept `BINANCE-DELIVERY`, bare `OKX`, `KALSHI_PERP`, and `OKX-OPTIONS`
   venue dialect rows.
3. **P2, carried:** resolve the `depth_of_book_10` registry/data population gap under DP-FETCH-009.
4. **P4, carried:** classify `index`, `perp_daily_ctx`, and the five singleton OHLCV intervals; retain only if
   supported by an explicit registry or migration exception.
5. **Coverage gap:** regenerate the stale market-data phantom audit and add the missing instruments-store phantom and
   reprobe artifacts, following the existing reconciliation procedure.

- [ ] [INFRA] P0. Existing market-data CEFI consolidator issue remains live; deploy the corrective image and verify a genuinely produced cycle.
- [ ] [DATA] P2. Resolve `BINANCE-DELIVERY` venue drift (4,838 rows).
- [ ] [DATA] P2. Resolve the `depth_of_book_10` registry gap (58,634 rows, 20,939 captured).
- [ ] [INFRA] P3. Refresh the stale CEFI `phantom_audit` artifact.
- [ ] [DATA] P4. Resolve `instrument_type=index` (3,910 captured rows).
- [ ] [DIAG] P4. Confirm whether `perp_daily_ctx` (11 captured rows) is an intended pilot.
- [ ] [DATA] P4. Resolve the five singleton OHLCV data-type registry gaps.
## 4. Explicitly out of scope

No machine-oracle path sweep, filename/id validation, parquet-content sample, Tier-2 VM, orphan-object scan, delete
proposal, GCS descent, service code change, deployment, or VM launch was performed.

## 5. Evidence and method

- GCP and AWS bucket names were resolved through the UTL bucket resolver with production project/account identifiers;
  no inline bucket derivation was used.
- Index metadata and JSON artifacts were read through UTL storage helpers.
- Census reads used the consolidated availability index with date-window predicate pushdown and exact axis filters;
  no whole-corpus GCS walk was performed.
- Canonical and accepted values came from the UAC/MTDS registry, not a reimplemented local vocabulary.
