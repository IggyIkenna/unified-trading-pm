---
doc_type: issue
title: TradFi venue smoke nested launcher has no valid gcloud credentials
summary: >-
  The TradFi venue smoke driver reached all eight non-Databento rows, but every nested backfill launch failed before VM
  creation because the active gcloud service account had no valid credentials. The terminal report is RED and requires
  launcher identity remediation before the canonical capture contract can be re-run.
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

# TradFi venue smoke nested launcher has no valid gcloud credentials

## What I found

The real driver VM `pipeline-e2e-check-mtds-20260820-201322-1bf21a` enumerated the eight current non-Databento TradFi cells and reached the force/skip/canonical legs. Every nested `launch-mtds-backfill-vm.sh` attempt failed before VM creation with `Your current active account [unified-trading-sa@central-element-323112.iam.gserviceaccount.com] does not have any valid credentials`. The driver exited `1` and wrote `data_pipeline_e2e_check_mtds_2026_08_19_tradfi.md` with `total=24`, `passed=0`, `failed=18`, `skipped=6`.

The six cells with captured/manifest evidence were CBOE/ohlcv_24h, ICE/ohlcv_24h, KRX/ohlcv_24h, FX/ohlcv_24h, FRED/ohlcv_1d, and FRED/yield_curve; their force and canonical legs could not complete because of the credential failure. NASDAQ/ohlcv_1h and NYSE/ohlcv_1h were honestly skipped as `no_captured_data_for_cell`. Phase-0 consolidation itself succeeded (`shards=6`, `rows_in=3328`, `rows_out=3328`).

## Why it matters

The smoke contract cannot prove capture, canonical path, manifest atom, or genuine capture status while the nested launcher cannot create its test VM. Retrying the same command only reproduces the credential failure and leaves the eight non-Databento cells unverified.

## Recommended decision

- [ ] [INFRA] P0. Fix `deployment-service/scripts/vm/lib/launcher_common.sh` service-account selection so nested launches use the VM metadata/tier identity with valid credentials rather than the stale `unified-trading-sa` active-account default; add a regression check that a driver VM can create one test-run backfill VM (repo: deployment-service).
- [ ] [BACKEND] P0. Re-run the eight-row MTDS force/skip/canonical contract after the launcher credential fix and require a terminal report with per-row capture, canonical, manifest, and capture-status evidence (repo: market-tick-data-service).
- [ ] [BACKEND] P1. Resolve and record the absent-capture verdicts for NASDAQ/ohlcv_1h and NYSE/ohlcv_1h, including whether the source resolver should retain them in the smoke denominator (repo: unified-api-contracts).
