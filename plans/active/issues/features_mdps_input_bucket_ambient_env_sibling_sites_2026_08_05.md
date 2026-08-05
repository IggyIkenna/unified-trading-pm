---
doc_type: issue
title: >-
  MDPS input-bucket resolution leaks ambient DEPLOYMENT_ENV_SHORT (stg 404) — volatility fixed, ~11 sibling sites need
  the prod-forcing sweep
summary: >-
  Confirmed + fixed inline (features-service, volatility family): the MDPS input bucket (`market-data` kind) was
  resolved with the ambient DEPLOYMENT_ENV_SHORT, so a `--env staging`-launched features-e2e benchmark VM resolved the
  never-provisioned `market-data-tick-tradfi-stg-*` tier and 404'd, blocking the TRADFI:volatility re-test
  (data_pipeline_check_mdps_features-056, slot-16 report 2026-08-05). The same ambient-env class remains at ~11 sibling
  MDPS-input sites across features-service (sports, delta_one, cefi calculators, calendar, onchain, cross_instrument).
  Also flags: features-e2e code tarball is a MANUAL build (fix won't reach benchmark VMs until rebuilt), and the
  commodity benchmark's test bucket (`commodity-signals-batch-test-*`) is not provisioned.
status: open
nature: issue
asset_group: [tradfi, cefi, sports, defi, prediction]
stage: [data]
repos: [features-service, deployment-service]
scope: [engineer, admin]
tags: [features-e2e, benchmark, bucket-resolution, staging, env-tiered, deployment_env, mdps, tarball, data-pipeline]
related:
  - /plans/active/data_pipeline_check_mdps_features_2026_07_20.md
  - /plans/archive/issues/cefi_delta_one_benchmark_vm_operator_approved_2026_07_29.md
  - /plans/archive/issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md
  - /plans/active/issues/tarball_stale_window_cefi_live_capture_correctness_risk_2026_08_01.md
created: 2026-08-05
author: slot-8
source: ["data_pipeline_check_mdps_features-056 dispatch 2026-08-05; bucket estate `gcloud storage ls` 2026-08-05"]
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
parent_epic: infrastructure_master
drift_direction: advance-code
resolved_by:
context_scope:
  - /codex/05-infrastructure/bucket-isolation-model.md
  - /codex/05-infrastructure/gcs-object-operations.md
  - /codex/02-data/availability-manifest-and-data-status.md
depends_on: []
locked_by:
locked_since:
---

# MDPS input-bucket resolution leaks ambient DEPLOYMENT_ENV_SHORT

## What I found

1. **CONFIRMED + FIXED inline (volatility family).** `features_service.common.resolve_mdps_candle_bucket` and
   `VolatilityServiceConfig.get_input_bucket` resolved the `market-data` kind with the ambient `DEPLOYMENT_ENV_SHORT`. A
   `--env staging`-launched features-e2e VM (benchmark/test runs set the IAM-safe tier env) resolved
   `market-data-tick-tradfi-stg-*` — a bucket that does NOT exist (the kind is `-test-`/`-prd-` ONLY per
   `configs/cloud-providers.yaml` line ~93-97) — and 404'd, blocking the TRADFI:volatility dependency check + input
   read. This is the exact bug class already fixed for CEFI in `features_service.delta_one._resolve_mdps_bucket`
   (features-service@ff1826b3/529ec90e). Shipped inline: `features-service@cc5c52b8` — forces `deployment_env="prod"` in
   both `resolve_mdps_candle_bucket` branches + `volatility/config.py::get_input_bucket`, with regression tests.

2. **Same class, NOT yet fixed — ~11 sibling MDPS-input sites** (all resolve `kind="market-data"` without forcing
   `deployment_env`; under a `--env staging` launch they resolve the non-existent `-stg-` tier):
   - `features_service/sports/config.py:85-89` — `resolve_bucket(kind="market-data", asset_group="sports")`
   - `features_service/sports/data/gcs_paths.py:71` — same
   - `features_service/delta_one/config.py:191` — `resolve_bucket(kind="market-data", asset_group=asset_group.lower())`
   - `features_service/delta_one/cli/handlers/batch_handler.py:606` —
     `resolve_bucket_name(cloud="gcp", kind="market-data", asset_group="cefi")`
   - `features_service/cefi/calculators/perp_funding_rates.py:72` — cefi
   - `features_service/cefi/calculators/perp_funding_corpus.py:255` — cefi
   - `features_service/calendar/adapters/mtds_fred_reader.py:123` — tradfi
   - `features_service/onchain/config.py:109` — `resolve_bucket(kind="market-data", asset_group=asset_group.lower())`
     (DEFI — relevant to the DEFI:onchain benchmark)
   - `features_service/cross_instrument/engine/raw_data_loader.py:139` — market-data
   - `features_service/cross_instrument/app/calculators/adv.py:474` — market-data
   - `features_service/cross_instrument/app/calculators/prediction_cross_venue_betfair.py:219` — sports

3. **features-e2e code tarball is a MANUAL build** (not CI-automated — the known gap from the CEFI benchmark,
   `create-code-tarballs.sh`). The shipped fix will NOT reach a benchmark VM until the tarball is rebuilt; a relaunch on
   the stale tarball reproduces the failure (cf. `LC_TARBALL_FRESHNESS` / tarball-stale window issue).

4. **Commodity benchmark test bucket not provisioned.** `commodity-signals-batch-test-*` does not exist (only
   `commodity-signals-batch-central-element-323112`). The `IS_TEST_RUN` sink override apparently points the commodity
   writer at a `-test-` bucket that was never created — TRADFI:commodity re-test fails on this even after the MDPS
   bucket fix. Whether this is a code mis-resolution or a pure provisioning gap needs a short diagnosis.

5. **DEFI:onchain gate is recorded OPEN** (perp_funding dependency resolved 2026-08-01 via the CEFI-bucket repoint +
   POLYMARKET-PERP known-outage tolerance; live-verified `available=True` 2026-07-29/30). The DEFI:onchain benchmark has
   NOT been re-run — and its `onchain/config.py:109` is a same-class stg risk under a staging launch, so it should be
   swept (item 2) before that benchmark relaunch.

## Why it matters

`data_pipeline_check_mdps_features-056` ("Remaining per-family real numbers") needs genuine TRADFI/DEFI throughput
numbers once the upstream gates clear. The TRADFI:volatility re-test is unblocked by the shipped fix but still needs a
rebuilt tarball + a benchmark VM run; TRADFI:commodity is additionally blocked on the missing test bucket; DEFI:onchain
is gated on the sibling sweep + a benchmark run. None of these are done, so the -056 checkbox stays `[ ]`.

## Recommended decision

1. Sweep the ~11 sibling MDPS-input sites to force `deployment_env="prod"` (mirror the delta_one / common-helper
   pattern), with per-site regression tests.
2. Rebuild the features-service code tarball (`create-code-tarballs.sh`) before any benchmark relaunch so the fix
   actually reaches the VM.
3. Diagnose/provision the commodity test bucket so the TRADFI:commodity re-test can proceed.
4. Then relaunch the TRADFI:volatility benchmark (unblocked) and the DEFI:onchain benchmark (gate open) to measure the
   real per-family numbers — tracked by -056 itself.

## Todos

- [ ] [DATA] P2. Sweep MDPS-input `kind="market-data"` sites in features-service to force `deployment_env="prod"` (repo:
      features-service) — the 11 sites listed in What I found §2; mirror `resolve_mdps_candle_bucket`, add per-site
      regression tests.
- [x] ✅ [INFRA] P2. Rebuild + republish the features-service code tarball (`create-code-tarballs.sh`) ahead of any
      features-e2e benchmark relaunch (repo: deployment-service) — verified already current at features-service@cc5c52b8
      (dry-run confirmed: tarball manifest SHA matches HEAD, no rebuild needed).
- [ ] [INFRA] P3. Diagnose why `commodity-signals-batch-test-*` resolves for the TRADFI:commodity benchmark
      (`IS_TEST_RUN` sink override vs bucket estate) and provision/fix it (repo: features-service +
      deployment-service/bucket estate).
- [ ] [DATA] P3. Re-verify the DEFI:onchain dependency gate on a recent day once the sibling sweep ships, then relaunch
      the DEFI:onchain features-e2e benchmark to measure the real number (repo: features-service) — remains tracked in
      `data_pipeline_check_mdps_features-056`.
