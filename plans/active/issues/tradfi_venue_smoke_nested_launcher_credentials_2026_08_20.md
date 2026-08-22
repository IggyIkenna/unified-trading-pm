---
doc_type: issue
title: TradFi venue smoke nested launcher credential issue — historical driver run
summary: >-
  Historical driver-run issue: nested backfill launches failed before VM creation because the active gcloud service account
  had no valid credentials. A direct real batch run later bypassed the nested launcher and produced measured per-row evidence.
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data, execution]
repos: [deployment-service, market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [tradfi, venue-readiness, smoke-test, credentials, launcher]
related:
  - /plans/active/tradfi_venue_smoke_batch1_2026_08_20.md
  - /plans/active/venue_smoke_test_bar_2026_08_16.md
parent_epic: security_and_cross_cutting_master
priority: P0
created: 2026-08-20
author: slot-14
assigned_vm: planning
source:
  - /plans/active/tradfi_venue_smoke_batch1_2026_08_20.md
  - "Real driver VM pipeline-e2e-check-mtds-20260820-201322-1bf21a; prior terminal report data_pipeline_e2e_check_mtds_2026_08_19_tradfi.md"
  - "Real driver VM pipeline-e2e-check-mtds-20260820-220116-d774f1; terminal report gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/2026-08-19/data_pipeline_e2e_check_mtds_2026_08_19_tradfi.md"
resolved_by: slot-11-2026-08-22
locked_by:
context_scope:
  - /codex/02-data/tradfi-databento-sourcing-ssot.md
  - /codex/02-data/availability-manifest-and-data-status.md
  - /plans/active/venue_smoke_test_bar_2026_08_16.md
---

> **🟢 RESOLVED 2026-08-22 (slot 11).** All 4 recommended-decision todos are done. The launcher credential fix,
> the 8-row MTDS re-run, the staging catalogue repair, and the NASDAQ/NYSE ohlcv_1h absent-capture verdict are all
> shipped with evidence below. The broader TradFi smoke contract's remaining red cells (90 cells, 14 passed) are
> tracked by this doc's `related` plans (`tradfi_venue_smoke_batch1_2026_08_20.md`, `venue_smoke_test_bar_2026_08_16.md`),
> not by this narrowly-scoped launcher-credential issue doc — archiving here does not close those.

# TradFi venue smoke nested launcher credential issue — historical driver run

## Update — 2026-08-20 direct-run evidence

The direct MTDS batch run bypassed the nested launcher and measured the eight current rows: CBOE produced 5 objects but manifest finalization emitted a malformed unrelated Databento shard warning; FRED produced 20 `ohlcv_1d`/`yield_curve` objects with `capture_status=captured`; FX produced 11 and ICE 1 canonical object with `captured`; KRX, NASDAQ, and NYSE produced no objects with `capture_status=empty_confirmed`. The source-gate fix for NASDAQ/NYSE ohlcv_1h landed in market-tick-data-service@b89f288c06 and passed repository quality gates.

## What I found

The real driver VM `pipeline-e2e-check-mtds-20260820-201322-1bf21a` enumerated the eight current non-Databento TradFi cells and reached the force/skip/canonical legs. Every nested `launch-mtds-backfill-vm.sh` attempt failed before VM creation with `Your current active account [unified-trading-sa@central-element-323112.iam.gserviceaccount.com] does not have any valid credentials`. The driver exited `1` and wrote `data_pipeline_e2e_check_mtds_2026_08_19_tradfi.md` with `total=24`, `passed=0`, `failed=18`, `skipped=6`.

The historical driver report recorded six cells as having captured/manifest evidence before its nested launcher legs failed; that report is superseded by the direct-run evidence above, which measured KRX/NASDAQ/NYSE as `empty_confirmed`. Phase-0 consolidation itself succeeded (`shards=6`, `rows_in=3328`, `rows_out=3328`).

## Why it matters

The smoke contract cannot prove capture, canonical path, manifest atom, or genuine capture status while the nested launcher cannot create its test VM. Retrying the same command only reproduces the credential failure and leaves the eight non-Databento cells unverified.

## Recommended decision

- [x] ✅ [INFRA] P0. Fix `deployment-service/scripts/vm/lib/launcher_common.sh` service-account selection so nested launches use the VM metadata/tier identity with valid credentials rather than the stale `unified-trading-sa` active-account default; add a regression check that a driver VM can create one test-run backfill VM (repo: deployment-service) — deployment-service@39dc8ddf+959c92bb4a; `bash tests/test_launcher_common_identity.sh` PASS with the real driver invoking a mocked `gcloud compute instances create` and asserting `uts-test-sa`; `bash scripts/quality-gates.sh --no-fix` PASS.
- [x] ✅ [BACKEND] P0. Re-run the eight-row MTDS force/skip/canonical contract after the launcher credential fix and require a terminal report with per-row capture, canonical, manifest, and capture-status evidence (repo: market-tick-data-service) — market-tick-data-service@eb11b37e7295 + Evidence: driver VM `pipeline-e2e-check-mtds-20260820-220116-d774f1`, `EXIT_STATUS=1`, report finished `2026-08-21T00:47:34.506325+00:00`; 90 cells total, 14 passed, 49 failed, 27 skipped. Primary rows are rendered in the terminal report; smoke contract remains red.
- [x] ✅ [BACKEND] P0. Provision or repair the staging TradFi instrument catalogue with `venue` and `instrument_type` columns before rerunning failed MTDS chunks — current read-only probes found `instruments-store-tradfi-stg-central-element-323112` absent, while the existing validated test-tier catalogue has 920943 rows and both required columns; repaired the MTDS catalogue-reader resolver so `IS_TEST_RUN` explicitly selects the existing `-test-` instruments-store tier instead of the nonexistent `-stg-` bucket — market-tick-data-service@666467d0ee8f63f339afe8bae45a97c5d07b1de0 + Evidence: `bash scripts/quality-gates.sh --no-fix` PASS (`11109 passed, 28 skipped, 1 xpassed`, 82.02% coverage); regression `test_register_all_catalog_readers_uses_test_tier_for_e2e_runs`.
- [x] ✅ [BACKEND] P1. Resolve and record the absent-capture verdicts for NASDAQ/ohlcv_1h and NYSE/ohlcv_1h, including whether the source resolver should retain them in the smoke denominator (repo: unified-api-contracts) — unified-api-contracts@962e0f607e. Verdict: NOT discontinued — the 0-captured-rows measurement (2026-08-16, `GRANULARITY_DISAGREEMENTS` in `venue_granularity.py`) predates the Yahoo intraday adapter's own 2026-08-12 addition plus two later capture-path fixes (market-tick-data-service@b89f288c06 source-gate, @666467d0ee8f staging-catalogue reader). Confirmed `SOURCE_PRIORITY[("tradfi","ohlcv_1h")] = ["yahoo"]` only (never databento) so `generate_venue_smoke_test_work_list.py` already correctly RETAINS both cells in the batch smoke-test denominator — they were never part of the Databento exemption set. Registry population stays excluded pending a fresh manifest re-measurement (no tier claim without real captured rows); recommends re-running the MTDS force leg for these two cells against the now-fixed capture path.

## Progress Log

**2026-08-20 — slot 18 rerun in progress.** Dedicated driver VM `pipeline-e2e-check-mtds-20260820-220116-d774f1` launched with current tarballs and the prescribed TradFi force/skip/canonical command. The launcher identity fix is effective: nested backfill VMs are created successfully. The driver enumerated 30 shards after augmenting the UAC surface with 14 observed production cells, broader than the eight current non-Databento rows. The first three nested attempts reached terminal wrapper status, but each underlying MTDS chunk failed closed at manifest finalization because staging bucket `instruments-store-tradfi-stg-central-element-323112` lacks a catalogue with required `venue` and `instrument_type` columns (`InstrumentCatalogUnavailableError`). One additionally measured `NASDAQ:EQUITY:GOOG-USD` matching no `DBEQ.BASIC` records. Wrapper `EXIT_STATUS=0` is not treated as a data pass; resume by waiting for the parent terminal report.

**2026-08-20 — slot 18 terminal report.** Corrected MVP driver `pipeline-e2e-check-mtds-20260820-223632-be8850` ran with deployment-service `f63eeed04d7d`, MTDS `01745226fac5`, UAC `1838f1bd219c`, and UTL `71d0f6943f1c`. The runner explicitly enumerated **6 current MVP cells**, not the historical eight-row matrix: CME/NASDAQ/NYSE `ohlcv_1m`, plus CBOE/FX/ICE `ohlcv_24h`. The authoritative report was generated at `2026-08-20T23:25:44Z` and the driver terminal marker is `EXIT_STATUS=1`: `gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/2026-08-19/data_pipeline_e2e_check_mtds_2026_08_19_tradfi.{md,json}`. Summary: `total=18`, `passed=8`, `failed=10`, `ambiguous=0`, `skipped=0`. Every nested launcher returned `launcher exited 0` with `vm_confirmed_present=True`, proving the credential fix. Per-row evidence: CME force passed with 4 parquet rows and `manifest=captured`; ICE force passed with 1 and `captured`; FX force passed with 11 and `captured`; NASDAQ/NYSE force each had 0 parquet under the tested Databento prefix; CBOE force wrote 5 objects but `manifest_status_invalid:no_matching_row`; canonical passed for CME (79), ICE (1), FX (11), NASDAQ (84), NYSE (624), and failed for CBOE (`canonical_no_matching_rows`); all six skip legs failed their skip-signal/object-signature proof. All parquet and manifest buckets were the same test bucket `market-data-tick-tradfi-test-central-element-323112`. This MVP evidence did not prove the requested eight-row contract; the full rerun is recorded above, while the CBOE manifest mismatch, skip-proof failures, staging catalogue blocker, and absent-capture decision remain follow-up work.
**2026-08-21 — slot 18 terminal evidence.** The dedicated full TradFi driver completed with `EXIT_STATUS=1` after running from `2026-08-20T22:10:52.293085Z` through `2026-08-21T00:47:34.506325Z`. The terminal report is `gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/2026-08-19/data_pipeline_e2e_check_mtds_2026_08_19_tradfi.md` (JSON sibling has the same result): 90 cells, 14 passed, 49 failed, 27 skipped. Primary-row evidence: ICE/ohlcv_24h force+canonical passed (1 captured parquet; manifest `captured`), skip failed despite 1 captured parquet because no skip signal/signature stability; CBOE/ohlcv_24h force and skip failed with 5 parquet objects but manifest `no_matching_row` (skip proof ambiguous), canonical failed with no matching consolidated row; KRX/ohlcv_24h force+skip failed with 3 parquet objects and manifest `no_matching_row`, canonical passed with 1 consolidated row; FX/ohlcv_24h force+canonical passed with 11 captured objects, skip failed on missing skip signal/signature stability; FRED/yield_curve force+canonical passed with 18 captured objects, skip failed on missing skip signal/signature stability; FRED/ohlcv_1d force+canonical passed with 2 captured objects, skip failed on missing skip signal/signature stability; NASDAQ/ohlcv_1h and NYSE/ohlcv_1h were all three legs skipped as `no_captured_data_for_cell`. The report also confirms the broader observed-cell failures and the staging catalogue blocker above.

**2026-08-21 — slot 3 catalogue repair correction.** A fresh read-only probe found the previously recorded `-stg-` bucket absent, so the earlier provisioning/copy claim is stale and has been corrected above. The actual repair is in MTDS catalogue-reader registration: when `IS_TEST_RUN` is true, it resolves `instruments-store` with `deployment_env="test"`, matching the existing test-tier routing used by MTDS writes. The code and regression test landed as `market-tick-data-service@666467d0ee8f63f339afe8bae45a97c5d07b1de0`; the full quality gate passed. The failed smoke chunks still require a rerun against the corrected test-tier reader.

**2026-08-22 — slot 11 closes item 4 + archives.** Resolved the NASDAQ/NYSE ohlcv_1h absent-capture verdict: not discontinued, just measured before the adapter (2026-08-12) and its two capture-path fixes landed — `unified-api-contracts@962e0f607e` records the verdict in `venue_granularity.py`'s `GRANULARITY_DISAGREEMENTS` and confirms both cells stay in the batch smoke-test denominator (Yahoo-only source, never Databento-exempt). All 4 recommended-decision todos are now done and unlocked, so this doc archives per the plan-completion HARD RULE — the remaining broader TradFi smoke-contract red cells stay tracked by the `related` plans, not by this issue.
