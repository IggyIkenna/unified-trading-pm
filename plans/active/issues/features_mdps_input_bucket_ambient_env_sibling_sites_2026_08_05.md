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

5. **DEFI:onchain gate — CORRECTED 2026-08-05 (slot-12) by a fresh re-verify: now CLOSED.** The "gate OPEN /
   perp_funding resolved 08-01 / live-verified `available=True` 07-29/30" framing from 2026-08-05 (slot-8) is STALE: a
   `DependencyChecker("central-element-323112")` sweep over 2026-07-31→2026-08-05
   (`features_service.onchain.app.core. dependency_checker`) shows perp_funding (required=True, the one dep that was
   "resolved") is MISSING on every recent day — see finding 6. The DEFI:onchain benchmark has NOT been re-run, and its
   `onchain/config.py:109` is a same-class stg risk under a staging launch, so it should be swept (item 2) before that
   benchmark relaunch.
6. **NEW 2026-08-05 (slot-12): DEFI:onchain gate re-closed by a BINANCE-DELIVERY perp_funding regression.** The CEFI
   manifest (`market-data-tick-cefi-prd-central-element-323112`) now carries a `BINANCE-DELIVERY` `attempted_failed`
   shard for perp_funding on EVERY day 2026-07-29→2026-08-04, plus NO manifest rows at all for 2026-08-05. The gate only
   tolerates `POLYMARKET-PERP` (`_KNOWN_OUTAGE_VENUES_BY_SVC`); BINANCE-DELIVERY is not among the perp_funding handler's
   3 live protocols (HYPERLIQUID/KALSHI_PERP/POLYMARKET_PERP — Aster/Lighter retired, GMX removed), so it looks like a
   stray/misclassified manifest row that tanked the whole dependency. At the 08-01 verification the same days had only 3
   rows (1 POLYMARKET attempted_failed → excluded → `available=True`); the BINANCE-DELIVERY rows were added afterwards.
   Every other required dep (vault_share_price/lst_rates/lending_indices/oracle_prices) is available on all recent days.

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
4. Then relaunch the TRADFI:volatility benchmark (unblocked) and the DEFI:onchain benchmark (gate re-closed on the
   BINANCE-DELIVERY perp_funding regression — fix finding 6's todo first) to measure the real per-family numbers —
   tracked by -056 itself.

## Progress Log

### 2026-08-05 (slot-12, data_engineering) — DEFI:onchain gate re-verified CLOSED on all recent days (perp_funding BINANCE-DELIVERY regression)

Ran `DependencyChecker("central-element-323112").check_dependencies(date, "DEFI")` (features-service, repo `.venv`,
GCP_PROJECT_ID=central-element-323112; read-only manifest reads, no VM launch) over 2026-07-31→2026-08-05 + a
perp_funding manifest dump (`read_manifest_rows` on `market-data-tick-cefi-prd-central-element-323112`). Result:

- **2026-07-29→08-04**: vault_share_price (24-35 rows), lst_rates (36-74), lending_indices (1959-2124), oracle_prices
  (1749-1815) all AVAIL (captured/empty_confirmed); **perp_funding MISS every day** — exactly one `BINANCE-DELIVERY`
  `attempted_failed` shard on each day (POLYMARKET-PERP also attempted_failed but is excluded by the gate's known-outage
  tolerance). → `required_ok=False` on every day.
- **2026-08-05**: no perp_funding manifest rows at all in the CEFI bucket (today's capture not yet in the index); 4/4
  other required deps AVAIL; MDPS (optional for DEFI) has no 08-05 rows yet either.

Benchmark relaunch for DEFI:onchain is therefore gated twice: (a) the perp_funding regression above (new P2 todo), and
(b) the sibling MDPS-input sweep (-001) + tarball rebuild (-002) not yet shipped (`onchain/config.py:109` still un-swept
at features-service@cc5c52b8). Left -004 checkbox `[ ]` — not false-completing a gated relaunch. Evidence:
`_defi_onchain_gate_check_2026_08_05.py` / `_perp_funding_manifest_dump_2026_08_05.py` (scratch, deleted after run).

## Todos

- [ ] [DATA] P2. Diagnose + fix the BINANCE-DELIVERY perp_funding `attempted_failed` regression (07-29→08-04) that
      re-closed the DEFI:onchain gate (repo: features-service gate + market-tick-data-service/manifest) — determine
      whether the rows are stray/misclassified (remove/clean them or scope the gate's perp_funding probe to the venues
      the DEFI:onchain consumer actually reads, i.e. HYPERLIQUID per `perp_funding_rates_defi.py`) or a real capture gap
      (backfill), then re-verify the gate reopens on recent days. See finding 6 + Progress Log.
- [ ] [DATA] P2. Sweep MDPS-input `kind="market-data"` sites in features-service to force `deployment_env="prod"` (repo:
      features-service) — the 11 sites listed in What I found §2; mirror `resolve_mdps_candle_bucket`, add per-site
      regression tests.
- [x] ✅ [INFRA] P2. Rebuild + republish the features-service code tarball (`create-code-tarballs.sh`) ahead of any
      features-e2e benchmark relaunch (repo: deployment-service) — verified already current at features-service@cc5c52b8
      (dry-run confirmed: tarball manifest SHA matches HEAD, no rebuild needed).
- [x] ✅ [INFRA] P3. Diagnose why `commodity-signals-batch-test-*` resolves for the TRADFI:commodity benchmark
      (`IS_TEST_RUN` sink override vs bucket estate) and provision/fix it (repo: features-service +
      deployment-service/bucket estate) — **diagnosis: pure provisioning gap.** `_test_bucket()` in
      `pipeline_e2e_check.py:649-652` derives `commodity-signals-batch-test-{pid}` from the flat `features-commodity`
      kind by string-inserting `-test-` (since the kind is non-env-tiered, `deployment_env="test"` is a no-op). The
      bucket was never provisioned; only `commodity-signals-batch-central-element-323112` existed. **Fix: provisioned
      `gs://commodity-signals-batch-test-central-element-323112`** (ASIA-NORTHEAST1, uniform-bucket-level-access,
      labels: managed-by=terraform-canonical, env=test, kind=features-commodity).
- [ ] [DATA] P3. Re-verify the DEFI:onchain dependency gate on a recent day once the sibling sweep ships, then relaunch
      the DEFI:onchain features-e2e benchmark to measure the real number (repo: features-service) — remains tracked in
      `data_pipeline_check_mdps_features-056`.
