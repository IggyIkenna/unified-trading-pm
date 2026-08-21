---
doc_type: audit-result
title: "Data-pipeline reconciliation — cefi (2026-08-21), raw-tick layer, Tier-1 only"
summary: >-
  Scheduled CEFI Tier-1 spot-check (dispatch agt-26e8f2, slot 28). Both GCP production buckets resolved and were
  reachable; AWS mirror buckets resolved and were reachable but had no status objects. The CEFI market-data
  consolidator's latest cycle failed at 2026-08-21T04:02:23Z with marker_missing_oversized_merge (108,714 shards >
  50,000), so the canonical availability index is stale and all manifest-derived counts are lower-bound/stale as of
  that failed cycle. This is the already-open P0 issue manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md
  reaching its shipped fail-closed safeguard; no new code fix or production write was performed. The fresh read of the
  last consolidated index found 30,801,085 rows, four genuine venue drift values, one instrument_type registry gap,
  and four data_type registry gaps; accepted aliases and bundle-grain values were suppressed. The newest honest-
  coverage rollup is 2026-08-20 and recomputes exactly to 47.40%, a lower bound because instrument_gates_download=true
  and denominator_status=INCOMPLETE.
status: partial
nature: record
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm, market-tick-data-service, unified-api-contracts, instruments-service, deployment-service]
scope: [engineer, admin]
tags: [reconciliation, canonicalisation, census, cefi, honest-coverage, consolidator-oversized-merge, p0-carried]
related: [four-surface-reconciliation-procedure, reconciliation-finding-taxonomy, reconciliation-census-and-compute-tiers, honest-coverage-model, manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19]
created: 2026-08-21
date: 2026-08-21
auditor: "cefi_reconciliation_auditor (scheduled role, slot 28, dispatch agt-26e8f2)"
parent_epic: security_and_cross_cutting_master
severity: P0
skill: data-pipeline-reconciliation
run_date: 2026-08-21
generated_at: 2026-08-21T04:27:02Z
audited_scope: "asset_group=cefi, layer=raw-tick, PROD (-prd-) buckets only, read-only Tier-1 Phase 0 + manifest census + honest-coverage verification"
resulting_plan:
lib_version:
doc_versions_checked:
---

# Data-pipeline reconciliation — cefi (2026-08-21), raw-tick layer, Tier-1 only

**Read-only against production data:** no GCS writes, manifest writes, deletes, VM launches, or code changes. This
scheduled role runs the bounded Tier-1 subset: Phase-0 reachability/freshness, manifest-side distinct-value census,
and honest-coverage freshness/formula verification. It does not run the machine-oracle path sweep, GCS delimiter
descent, per-datapoint sample/schema checks, orphan sweep, or delete-suggestion phase.

## 0. Phase-0 reachability and freshness

All bucket names below were resolved through UTL `resolve_bucket_name(..., deployment_env="prod")`; no bucket name was
hand-authored. Probe time was `2026-08-21T04:27:02Z` (UTC).

| bucket | reachable | status / lock evidence | canonical index evidence | verdict |
| --- | --- | --- | --- | --- |
| `market-data-tick-cefi-prd-central-element-323112` | yes | `_index/consolidator.lock` absent; `_index/consolidator_stall_state.json` = `streak=0`, `baseline_shards=110524` | `availability_index.parquet`: generation `1787254157655029`, last modified `2026-08-20T19:29:17.669Z`, 469,897,537 bytes | **STALE / P0 carried** |
| `instruments-store-cefi-prd-central-element-323112` | yes | lock absent; latest status `success=true`, `verdict=produced`, 4 shards scanned / 3 changed | latest status at `2026-08-21T04:01:22.892Z`; no availability index is used for this census | healthy |
| `market-data-tick-cefi-prd-427895769566` (AWS mirror) | yes | queried with AWS provider; no `_index/latest.json`, lock, or status objects found | no canonical index/status object found | empty mirror / declared gap |
| `instruments-store-cefi-prd-427895769566` (AWS mirror) | yes | queried with AWS provider; no `_index/latest.json`, lock, or status objects found | no canonical index/status object found | empty mirror / declared gap |

### Consolidator finding

The market-data CEFI `_index/latest.json` was written at `2026-08-21T04:02:23.086Z` and reports:

```text
success=false, verdict=failed, shards_scanned=108715, shards_changed=0,
rows_in=0, rows_out=0, incremental=false,
error_reason=marker_missing_oversized_merge: 108714 shards > 50000 — cron full merge infeasible
```

The canonical index therefore predates the failed cycle by roughly 8h58m at probe time. This is not a new phantom-lock
finding: the active P0 issue `/plans/active/issues/manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md`
records the shipped `_UNPROVABLE_MERGE_MAX_SHARDS=50000` safeguard and leaves the MTDS image rebuild as its unresolved
deployment todo. Today’s error is that safeguard firing as designed, while the production cron image still has not
been verified as carrying both shipped fixes. Manifest-derived values below are a lower-bound snapshot of the last
successful consolidated index, not a claim about post-2026-08-20T19:29Z writes.

Status objects also show the failure is not a silent lock:

- `_index/phantom_audit_latest.json`: `phantom_count=0`, generated `2026-07-27T17:38:18.042Z` — 24 days stale.
- `_index/reprobe_audit_latest.json`: generated `2026-08-20T09:00:58.824Z`, day `2026-08-20`, `new_empties=13`,
  `disagreements=9`, `ambiguous=0`, `proven=0`, `reclassified=0`.
- `_index/consolidator_stall_state.json`: `streak=0`; this does not make the canonical index fresh because the latest
  cycle failed rather than producing a consolidated output.

## 1. Manifest-side distinct-value census

The bounded read used the consolidated CEFI index with columns `venue`, `instrument_type`, `data_type`, and
`capture_status`. It returned **30,801,085 rows**. The UAC canonical vocabulary and the deployment-api accepted-
exception registry were checked separately; accepted values are shown as suppressed, not silently dropped.

### Venue axis

`C − M` (canonical CEFI venue declarations absent from the snapshot): **empty for the 25 declared venues**.

Suppressed accepted aliases:

- `BYBIT-FUTURES`: 30,782 rows, all `empty_confirmed`.
- `OKEX-FUTURES`: 36 rows, all `empty_confirmed`.
- `CRYPTOFACILITIES`: 10 rows, all `empty_confirmed`.

Genuine `M − C` values (typed as `non_canonical_axis_value`, carried unless otherwise noted):

- `OKX`: 5,225 rows, all `attempted_failed` — bare-OKX historical residue.
- `BINANCE-DELIVERY`: 4,838 rows (`empty_confirmed=4,255`, `attempted_failed=578`, `captured=5`).
- `KALSHI_PERP`: 2 rows, all `attempted_failed`; not the canonical `KALSHI-PERP` spelling.
- `OKX-OPTIONS`: 2 rows, all `attempted_failed`.

### Instrument-type axis

- Suppressed accepted bundle-grain values: `futures_chain` = 175,484
  (`empty_confirmed=121,386`, `expected_unattempted=43,867`, `attempted_failed=10,231`); `options_chain` = 36,382
  (`empty_confirmed=24,394`, `expected_unattempted=8,580`, `attempted_failed=3,408`).
- `index`: 3,910 rows, all `captured` — **`non_canonical_axis_value`**, carried registry gap associated with
  DERIBIT `volatility_index`.
- Blank spellings: `None` = 197,346 (`empty_confirmed=160,821`, `attempted_failed=36,525`) and empty string =
  157,337, all `empty_confirmed`; these are honest-absence/legacy failure rows and not asserted as a new casing issue.
- C2a instrument-type casing remains `migration_pending` under the D1 ruling; no case-only finding was emitted.

### Data-type axis

The UAC CEFI data-type registry includes `futures_chain` and `options_chain`; those values are not findings here.
Genuine `non_canonical_axis_value` values are:

- `depth_of_book_10`: 58,634 (`empty_confirmed=37,629`, `captured=20,939`, `attempted_failed=66`), carried writer/
  registry gap.
- `perp_daily_ctx`: 11, all `captured`, carried pilot/scope question.
- `ohlcv_5m`, `ohlcv_15s`, `ohlcv_1h`, `ohlcv_1d`: 2 rows each, all `captured`, carried undeclared data types.

The canonical `ohlcv_1m` value is not a finding (32,963 rows: `empty_confirmed=17,827`, `captured=13,436`,
`expected_unattempted=1,700`).

### Chain axis

No nonblank CEFI chain value was observed in the manifest snapshot; no chain-axis finding was emitted.

### Surface verdict boundary

This role’s Tier-1 subset did not run the four-surface per-shard machine-oracle/content comparison. Accordingly, S1
path structure, S2 parquet content, and S4 catalogue are **not assessed**, rather than reported clean. S3 is assessed
only at manifest vocabulary/capture-status aggregate grain above. A stale consolidated index makes even S3 counts a
lower bound. No Tier-2 100%-corpus claim is made.

## 2. Honest coverage

The newest available rollup is `2026-08-20/coverage.json`, generated at `2026-08-20T20:56:32Z`; the current
`2026-08-21/coverage.json` did not exist at probe time. It measured all five asset groups with `partial=false` and no
failed groups. CEFI values were:

```text
captured=10,538,345
attempted_failed=855,304
expected_unattempted=10,839,811
empty_confirmed=6,602,176
published coverage_pct=47.40
denominator_status=INCOMPLETE
instrument_gates_download=true
layer1_completeness_pct=90.79
```

Formula re-check (the CK3-certified honest-coverage formula, excluding `empty_confirmed`):

`reachable_coverage = captured / (captured + attempted_failed + expected_unattempted)`

`10,538,345 / (10,538,345 + 855,304 + 10,839,811) = 10,538,345 / 22,233,460 = 47.4017%`, matching the published
`47.40%` after rounding. This is a **lower bound**, because `instrument_gates_download=true` and
`denominator_status=INCOMPLETE`; no denominator-complete claim is made.

## 3. Findings and carried todos

- [ ] [INFRA] P0. **Existing active issue remains live:** market-data CEFI consolidator latest cycle failed with
  `marker_missing_oversized_merge` and the canonical index is stale. The active issue’s unresolved MTDS image rebuild
  must deploy the shipped cutoff and locked-no-op liveness fix, then verify a genuinely produced hourly cycle with a
  new canonical generation. Do not relaunch a large backfill or treat this snapshot as current until then.
- [ ] [DATA] P2. `BINANCE-DELIVERY` venue drift (4,838 rows; status distribution above), carried.
- [ ] [DATA] P2. `depth_of_book_10` data-type registry gap (58,634 rows, 20,939 captured), carried.
- [ ] [INFRA] P3. `phantom_audit` status is 24 days stale, carried.
- [ ] [DATA] P4. `instrument_type=index` (3,910 captured rows), carried.
- [ ] [DIAG] P4. `perp_daily_ctx` (11 captured rows), confirm scope or expected pilot.
- [ ] [DATA] P4. `ohlcv_{5m,15s,1h,1d}` (2 captured rows each), carried registry gaps.

No issue document or service code was edited by this run; the P0 is already filed and the accepted-exception
classification is already represented in the live registry.

## 4. Explicit coverage gaps

- Canonical market-data manifest is stale after a failed consolidator cycle; all manifest counts are lower bounds.
- AWS CEFI mirrors are reachable but empty of the probed status objects; no AWS data census was inferred.
- `phantom_audit_latest.json` on the market-data bucket is 24 days stale.
- `instruments-store-cefi` has no phantom/reprobe status objects.
- S1 path oracle, S2 content/schema/id sample, S4 catalogue comparison, GCS-side vocabulary descent, orphan sweep,
  and delete suggestions were not run under this role’s Tier-1 boundary.

## Progress Log

- **cefi_reconciliation_auditor 2026-08-21** [dispatch agt-26e8f2, slot 28]: Phase 0, manifest-side census, and
  honest-coverage verification completed read-only. Both GCP buckets resolved/reachable; AWS mirrors resolved/reachable
  but empty of status objects. The newest market-data consolidator cycle failed closed at 04:02Z with
  `marker_missing_oversized_merge` (`108714 > 50000`), leaving the canonical index at generation
  `1787254157655029` from 19:29Z on 08-20. This is the existing P0 issue’s unresolved deployment/image step, not a new
  lock regression. Last consolidated snapshot: 30,801,085 rows; genuine venue drift = OKX, BINANCE-DELIVERY, KALSHI_PERP,
  OKX-OPTIONS; instrument gap = index; data-type gaps = depth_of_book_10, perp_daily_ctx, ohlcv_5m/15s/1h/1d. Newest
  coverage rollup 08-20 recomputed exactly to 47.40% using captured/(captured+attempted_failed+expected_unattempted),
  lower bound with incomplete denominator. No code, GCS, manifest, VM, or issue-doc writes performed.
