---
doc_type: issue
title: TradFi venue smoke nested launcher credential issue — historical driver run
summary: >-
  Historical driver-run issue: nested backfill launches failed before VM creation because the active gcloud service account
  had no valid credentials. A direct real batch run later bypassed the nested launcher and produced measured per-row evidence.
status: open
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
  - "Real driver VM pipeline-e2e-check-mtds-20260820-201322-1bf21a; terminal report data_pipeline_e2e_check_mtds_2026_08_19_tradfi.md"
resolved_by:
locked_by:
context_scope:
  - /codex/02-data/tradfi-databento-sourcing-ssot.md
  - /codex/02-data/availability-manifest-and-data-status.md
  - /plans/active/venue_smoke_test_bar_2026_08_16.md
---

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
- [ ] [BACKEND] P0. Re-run the eight-row MTDS force/skip/canonical contract after the launcher credential fix and require a terminal report with per-row capture, canonical, manifest, and capture-status evidence (repo: market-tick-data-service).
- [ ] [BACKEND] P1. Resolve and record the absent-capture verdicts for NASDAQ/ohlcv_1h and NYSE/ohlcv_1h, including whether the source resolver should retain them in the smoke denominator (repo: unified-api-contracts).

## Progress Log

**2026-08-20 — slot 18 rerun in progress.** Dedicated driver VM `pipeline-e2e-check-mtds-20260820-220116-d774f1` launched with current tarballs and the prescribed TradFi force/skip/canonical command. The launcher identity fix is effective: nested backfill VMs are created successfully. The driver enumerated 30 shards after augmenting the UAC surface with 14 observed production cells, broader than the eight current non-Databento rows. The first three nested attempts reached terminal wrapper status, but each underlying MTDS chunk failed closed at manifest finalization because staging bucket `instruments-store-tradfi-stg-central-element-323112` lacks a catalogue with required `venue` and `instrument_type` columns (`InstrumentCatalogUnavailableError`). One additionally measured `NASDAQ:EQUITY:GOOG-USD` matching no `DBEQ.BASIC` records. Wrapper `EXIT_STATUS=0` is not treated as a data pass; resume by waiting for the parent terminal report.
