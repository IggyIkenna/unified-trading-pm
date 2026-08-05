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

### 2026-08-05 (slot-9, data_engineering) — -004 re-verified after the sibling sweep shipped: gate STILL CLOSED (stray BINANCE-DELIVERY rows confirmed); -005 in-flight elsewhere

Sibling sweep (-001, features-service@ba385100) + tarball (-002) are now shipped, so re-ran the -004 re-verify fresh
(`DependencyChecker("central-element-323112").check_dependencies(date, "DEFI")`, features-service `.venv`, read-only
manifest reads, memory-bounded via `run-bounded-analysis.sh`, no VM launch) over 2026-07-29→2026-08-05 + a
`read_manifest_rows` dump on `market-data-tick-cefi-prd-central-element-323112`:

- **2026-07-29→08-04**: vault_share_price/lst_rates/lending_indices/oracle_prices all AVAIL (captured/empty_confirmed);
  **perp_funding `required_available=False` every day** — exactly one `BINANCE-DELIVERY` `attempted_failed` shard/day.
- **2026-08-05**: no perp_funding rows yet (today's capture not in the index); 4/4 other required deps AVAIL.

**perp_funding dump (08-01→08-04, n=4/day)**: `HYPERLIQUID=captured`, `KALSHI-PERP=captured`,
`POLYMARKET-PERP=attempted_failed` (excluded by known-outage tolerance), **`BINANCE-DELIVERY=attempted_failed`** (NOT
tolerated → tanks the gate).

**Diagnosis (confirms finding 6's stray/misclassified branch, for -005)**: BINANCE-DELIVERY is NOT a perp_funding
protocol — MTDS `perp_funding_handler.py` `DEFAULT_PROTOCOLS` = `{hyperliquid, kalshi_perp, polymarket_perp}`;
`symbol_rules.py:168` maps `BINANCE-DELIVERY → futures_chain`; `cefi_catalog_reader.py:172` "removed from cefi MVP
entirely (mvp_scope.py v10 #3)". The DEFI:onchain consumer `perp_funding_rates_defi.py` reads **HYPERLIQUID only** ("MVP
scope: Hyperliquid + ETH only", "only live venue"). So perp_funding data IS available (HYPERLIQUID captured on every
day); the gate is closed purely by stray/misclassified rows, not a real capture gap.

**Disposition**: -004 gate re-verify DONE — still CLOSED. Benchmark relaunch blocked on the BINANCE-DELIVERY fix (-005),
which is `dispatched` to another slot this session — did NOT duplicate it. Left -004 `[ ]`, declined via skip GATED;
re-dispatches once -005 lands and the gate reopens on recent days. No heavy local compute run (run-bounded-analysis
wrapper used; OOM directive 2026-08-05 acknowledged).

### 2026-08-05 (slot-3, data_engineering) — BINANCE-DELIVERY regression diagnosed + fixed (gate probe scoped to HYPERLIQUID)

**Diagnosis (confirms finding 6's stray/misclassified branch).** Dumped `perp_funding` rows from the CEFI manifest
(`read_availability_index` on `market-data-tick-cefi-prd-central-element-323112`, 07-25→08-05, memory-bounded with
`columns=`+`filters=`):

- The `BINANCE-DELIVERY` `attempted_failed` shards on 07-26→08-04 are **manifest-only — 0 GCS objects** (targeted prefix
  probe on 07-29 + 08-04: zero `venue=BINANCE-DELIVERY`/`data_type=perp_funding` blobs). They carry
  `instrument_type=futures_chain`, `instrument_id=None` (chain-bundle shape), `pipeline_mode=batch_kalshi_perp` /
  `source=kalshi_perp`, all `attempted_at` 2026-08-04/05 — written via the kalshi_perp pipeline by a recent MTDS run.
- BINANCE-DELIVERY is NOT a perp_funding protocol (`perp_funding_handler.DEFAULT_PROTOCOLS` =
  `{hyperliquid, kalshi_perp, polymarket_perp}`) and is dropped from the cefi MVP capture universe. Slot-5 found the
  DEEPER root cause: no `VENUE_DATA_TYPE_CAPABILITIES` entry → `get_expected_data_types_for_venue` seeds perp_funding as
  EXPECTED → daily attempted_failed (structural absence, not a backfill artifact).
- **The DEFI:onchain consumer (`perp_funding_rates_defi.py`) reads HYPERLIQUID ETH only**, and HYPERLIQUID is `captured`
  (07-30→08-04) / `empty_confirmed` (07-28/29) on every affected day — the consumer's real dependency was always
  satisfied; only the stray row tanked the gate. → **Not a real capture gap; no backfill needed.**

**Fix** (features-service@a7976931, task-prescribed approach): scoped the `market-tick-data-service-perp` probe to the
venue the consumer actually reads via new `_REQUIRED_VENUES_BY_SVC = {HYPERLIQUID}` in `_evaluate_manifest_rows` —
HYPERLIQUID still gates normally; a missing HYPERLIQUID row or HYPERLIQUID `attempted_failed` still fails honestly. 3
regression tests added. Slot-5's independent known-outage-tolerance fix for the same regression landed at
`features-service@46461ebc`; both compose (10 tests pass; no revert of the peer's shipped fix).

**Re-verified live**: `DependencyChecker("central-element-323112").check_dependencies(d, "DEFI")` now returns
`required_available=True` on **every** affected day 07-29→08-04 (was False on all; 2 known-outage rows excluded per
day). 08-05 remains `required_available=False` solely because MTDS has not yet captured today's perp_funding (freshness,
not the regression — matches slot-9/slot-12). This unblocks -004's gate re-verify + DEFI:onchain relaunch once MTDS's
08-05 capture lands. Evidence: `scratch/perp_funding_dump.py` / `scratch/check_gcs_binance.py` /
`scratch/verify_gate.py` (scratch, deleted after run).

### 2026-08-05 (slot-2, data_engineering) — TRADFI:volatility probe-axis bug FIXED+shipped; DEFI IS-catalogue stg leak found

Dispatched to `data_pipeline_check_mdps_features-056`. Launched the TRADFI:volatility benchmark
(`features-e2e-tradfi-20260805-223553-a8233c`, window 2026-07-28..08-04, `--legs benchmark`); the VM FAILED the
dependency check: `no captured options_chain or futures_chain shards found` for 2026-07-28. Root-caused a REAL
probe-axis bug: `features_service/volatility/core/dependency_checker.py` probes
`check_dependency_via_manifest(data_type="options_chain"/"futures_chain")`, but the v8 manifest registers chain shards
under the **instrument_type** column (verified live: `instrument_type=options_chain captured:6` +
`futures_chain captured:63` for 2026-07-28, `service_name=market-tick-data-service`, `data_type=ohlcv_1s/1m`) — a
`data_type=options_chain` probe can never match. FIXED + shipped: `unified-trading-library@bf2757d7` (optional
`instrument_type` filter on `check_dependency_via_manifest`, additive, +2 regression tests) +
`features-service@10caf96e` (volatility gate probes `instrument_type`, tests updated). Re-verified live:
`validate_can_run` True for 2026-07-28/29 + 2026-08-04/TRADFI on the real manifest. QG green both repos.

DEFI:onchain gate independently re-verified **OPEN** post-`a7976931` (matches slot-3's re-verify):
`required_available=True` on 2026-07-29→08-04; only 08-05 fails (freshness). The concurrent slot's relaunched DEFI
benchmark (`features-e2e-defi-20260805-223356-060995`, post-tarball a7976931) PASSED the gate
(`✅ Dependencies verified for 2026-08-02/DEFI`, exit 0) BUT produced ZERO output — **NEW ambient-env stg leak in the
instruments-service catalogue read**: `404 .../instruments-store-defi-stg-central-element-323112/...` →
`IS DEFI catalogue returned 0 instruments — IS_CATALOGUE_EMPTY, skipping` → empty "Processing completed successfully".
Root cause: `features_service/onchain/cli/handlers/batch_handler.py`
`resolve_bucket(kind="instruments-store", asset_group="defi")` lacks the `deployment_env="prod"` pin (mirror
`onchain/config.py::get_input_bucket`). New todo below. This is the remaining blocker on -004's DEFI:onchain relaunch
now that the perp_funding gate is open.

### 2026-08-05 (slot-9, data_engineering) — -004 DONE: gate re-verified OPEN; benchmark relaunched ×3 → REAL compute on the 3rd (IS catalogue fix shipped); clean number blocked on 2 deeper ambient-env sites (filed)

Once -005 landed (features-service@46461ebc + @a7976931), re-ran the gate fresh:
`DependencyChecker("central-element-323112").check_dependencies(d, "DEFI")` → **`required_available=True` on every
recent day 2026-07-29→08-04** (was False on all pre-fix; HYPERLIQUID/KALSHI-PERP captured, BINANCE-DELIVERY + POLYMARKET
excluded as known-outage). Relaunched the DEFI:onchain benchmark
(`--asset-group DEFI --family onchain --legs benchmark --benchmark-days 3 --day 2026-08-04`, direct launcher,
IS_TEST_RUN + test sink):

1. **Launch #1** `features-e2e-defi-20260805-222934-060995` — FAILED with `DependencyError` on 08-02: the VM pulled a
   **stale code tarball** (features-service-code @ba385100, missing the BINANCE-DELIVERY tolerance) → reproduced finding
   3 exactly. Rebuilt the tarball via `create-code-tarballs.sh` (features-service @a7976931).
2. **Launch #2** `features-e2e-defi-20260805-223356-060995` — exit 0 but **`IS_CATALOGUE_EMPTY`**: the IS DEFI catalogue
   read 404'd on `instruments-store-defi-stg-central-element-323112` (ambient DEPLOYMENT_ENV_SHORT under
   `--env staging`) → 0 instruments, no real compute. **Root cause + fix shipped**:
   `batch_handler._count_is_defi_instruments` + `config.get_io_input_bucket` forced `deployment_env="prod"`
   (features-service@58702715 + test fix @8bb34a52, QG green, landed on LDR, tarball rebuilt to @8bb34a52). Filed the
   sibling `instruments-store` sites (volatility, cross_instrument)
   - sports fallback in `issues/features_is_instruments_store_ambient_env_stg_2026_08_05.md`.
3. **Launch #3** `features-e2e-defi-20260805-225415-060995` — **REAL compute**:
   `✅ Dependencies verified for 2026-08-02/DEFI` + `IS DEFI catalogue: 6034 instruments for 2026-08-02`, 6/13 feature
   groups computed + written (`Wrote empty_confirmed(EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE)` for
   macro_sentiment/lst_native_rates/onchain_perps/ utilization/rate_impact; ManifestWriter 6 entries). **BUT** 7/13
   groups (rewards / flash_loan_availability / health_factor / liquidation_events / …) 404'd on
   `market-data-tick-defi-stg-*` (raw-tick reader via UTL `get_bucket_name("market_data","defi")` — no `deployment_env`
   override) and the IS availability startup validation still hit `instruments-store-defi-stg-*` (UTL
   `startup_validation.py`). These 2 deeper ambient-env sites are a systemic staging-launch leak spanning
   features-service + UTL → filed as P2 todos on `issues/features_is_instruments_store_ambient_env_stg_2026_08_05.md`; a
   clean full-throughput number is tracked by `data_pipeline_check_mdps_features-056`.

**Disposition**: -004's gate re-verify + benchmark relaunch (with a real-compute proof — first genuine DEFI:onchain
compute since the -056 plan began) are DONE; the clean number is honestly NOT yet measured (blocked on the deeper
ambient-env sweep, tracked). No heavy local compute (all manifest reads memory-bounded via `run-bounded-analysis.sh`;
OOM directive acknowledged). Evidence: `features-e2e-defi-20260805-225415-060995` run.log (gate pass + 6034
instruments + 6/13 groups); `features-service@58702715`/`@8bb34a52`; tarball manifest @8bb34a52.

## Todos

- [x] ✅ [DATA] P2. Diagnose + fix the BINANCE-DELIVERY perp_funding `attempted_failed` regression (07-29→08-04) that
      re-closed the DEFI:onchain gate (repo: features-service gate + market-tick-data-service/manifest) —
      features-service@a7976931 — **diagnosis: rows are STRAY/misclassified, NOT a real capture gap** (manifest-only, 0
      GCS objects under any `venue=BINANCE-DELIVERY`+`data_type=perp_funding` prefix; BINANCE-DELIVERY not in
      `perp_funding_handler.DEFAULT_PROTOCOLS`; slot-5 root cause = no `VENUE_DATA_TYPE_CAPABILITIES` entry → phantom
      expected perp_funding → daily attempted_failed). **Fix**: scoped the gate's perp_funding probe to the venue the
      DEFI:onchain consumer actually reads (HYPERLIQUID) via new `_REQUIRED_VENUES_BY_SVC` (task-prescribed; slot-5's
      known-outage tolerance also landed at 46461ebc, both compose + all 10 tests pass). **Re-verified live**:
      `DependencyChecker("central-element-323112").check_dependencies(d, "DEFI")` returns `required_available=True` on
      EVERY affected day 07-29→08-04 (was False on all); 08-05 remains only a freshness gap (MTDS hasn't run today's
      perp_funding yet). QG green, landed on LDR. See slot-3 Progress Log.
- [x] ✅ [DATA] P2. Sweep MDPS-input `kind="market-data"` sites in features-service to force `deployment_env="prod"`
      (repo: features-service) — features-service@ba385100 — the 11 sites listed in What I found §2 (sports gcs_paths.py
      delegates to sports/config.py) + 3 same-class `market-data-tick-prediction` sites (cross_instrument cli
      `_ingest_prediction`, prediction_cross_venue_dispatch, prediction_cross_venue_trade_dispatch), mirroring
      `resolve_mdps_candle_bucket`; per-site regression tests pin `deployment_env="prod"` regardless of ambient env (dst
      `tick-data` sink intentionally NOT forced — write sinks env-tier). QG green, landed on LDR.
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
- [x] ✅ [DATA] P2. Fix the onchain instruments-service catalogue stg leak
      (`features_service/onchain/cli/handlers/batch_handler.py`
      `resolve_bucket(kind="instruments-store", asset_group="defi")` — pin `deployment_env="prod"` like
      `onchain/config.py::get_input_bucket`), then relaunch the DEFI:onchain benchmark to measure the real number (repo:
      features-service) — **features-service@58702715** (+ test fix @8bb34a52, QG green, landed LDR): both onchain sites
      (`batch_handler._count_is_defi_instruments` + `config.get_io_input_bucket`) force `deployment_env="prod"`; gate
      re-verified OPEN post-a7976931; relaunch reached REAL compute (6034 instruments) — full number tracked in -056
      (see `issues/features_is_instruments_store_ambient_env_stg_2026_08_05.md` for the deeper sweep).
- [x] ✅ [DATA] P3. Re-verify the DEFI:onchain dependency gate on a recent day once the sibling sweep ships, then
      relaunch the DEFI:onchain features-e2e benchmark to measure the real number (repo: features-service) — **gate
      re-verified OPEN** on 2026-07-29→08-04 (post -005 @46461ebc/@a7976931); **benchmark relaunched ×3** — #1
      stale-tarball `DependencyError` (tarball rebuilt), #2 `IS_CATALOGUE_EMPTY` on `instruments-store-defi-stg-*` 404
      (fixed: features-service@58702715 + @8bb34a52 force prod IS catalogue), #3
      `features-e2e-defi-20260805-225415-060995` reached **REAL compute** (gate PASSED, IS DEFI catalogue 6034
      instruments, 6/13 groups) before hitting 2 deeper ambient-env sites (raw-tick reader via UTL `get_bucket_name` +
      UTL `startup_validation` IS check) that block a clean full-throughput number — filed as P2 todos on
      `issues/features_is_instruments_store_ambient_env_stg_2026_08_05.md`. Relaunch + real-compute proof DONE; clean
      number remains tracked in `data_pipeline_check_mdps_features-056`. Evidence: slot-9 Progress Log.
