---
doc_type: issue
title:
  P2 re-run of every `smoke_matrix.py` (post-P0/INFRA fixes) confirms the test-isolation + genuine-verification contract
  holds, but 6 of 8 families cannot PASS for pre-existing upstream/harness reasons — surfaced as tracked findings
summary: >-
  Re-ran every family's `e2e-testing/scripts/<family>/smoke_matrix.py` for real (non-dry-run) against live GCS
  `central-element-323112` as `features_e2e_smoke_matrix_writes_to_prod_bucket_2026_08_01.md`'s P2 (the parked
  re-verification todo). CORE CONTRACT CONFIRMED: test-bucket routing holds (zero writes to any PROD features bucket in
  the run window — verified via scoped PROD listings), the harnesses genuinely verify (PASS = real
  captured/empty_confirmed row in the `-test-` bucket), and the cross_instrument timeout-hardening + memory fixes both
  work (process group fully reaped via killpg at the 600s bound, bounded wrapper never tripped, no host OOM). Only
  calendar achieves PASS; the other 7 families are blocked by pre-existing upstream/harness issues that are NOT
  regressions from the P0/P2 fixes. Each blocker is captured as an actionable todo below.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [features-service, e2e-testing, market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags:
  [
    data-pipeline,
    features,
    e2e-testing,
    smoke-matrix,
    test-bucket-isolation,
    dependency-checker,
    processed-candles,
    manifest-consolidator,
    verification,
  ]
related:
  [
    /plans/archive/issues/features_e2e_smoke_matrix_writes_to_prod_bucket_2026_08_01.md,
    /plans/archive/issues/features_smoke_matrix_verification_findings_2026_08_01.md,
    /plans/archive/issues/defi_onchain_perp_funding_permanently_unsatisfiable_dependency_2026_07_31.md,
    /plans/active/issues/features_cross_instrument_smoke_verify_unbounded_memory_second_ao_outage_2026_08_01.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: "2026-08-05"
last_updated: "2026-08-05"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.2
estimate_calibrated_ai_days: 1.0
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
source:
  "slot-5, data_engineering, surfaced while executing features_e2e_smoke_matrix_writes_to_prod_bucket-003 (P2
  re-verification of the smoke-matrix -test- bucket routing fix), 2026-08-05"
---

# Smoke-matrix P2 re-run: contract confirmed; 7/8 families blocked by pre-existing upstream/harness issues

## What I found

Ran all 8 `e2e-testing/scripts/<family>/smoke_matrix.py` harnesses for real (non-dry-run) against live GCS
`central-element-323112`, using the features-service venv (`_invoke_cli` shells out to
`sys.executable -m features_service.*`). All P0 (test-bucket routing) + INFRA (process-group timeout hardening) fix
content is present in the current tree (SHAs were rewritten by the 2026-08-05 11:26Z history rewrite, but the code is
byte-verified present: `PROTOCOL_DATA_SINK_BUCKET*` env wiring + `start_new_session=True`/`os.killpg` in every
`_invoke_cli`).

### Core contract — CONFIRMED (the P2 proof)

1. **Test-bucket isolation holds.** The only writes observed landed in `-test-` buckets: calendar wrote
   `capture_status=empty_confirmed` manifest rows to `features-calendar-test-central-element-323112`; multi_timeframe
   wrote 36 `attempted_failed` manifest rows each to `features-cefi-test-` and `features-defi-test-`. A scoped PROD
   listing during the run window (21:00Z-21:35Z) shows **zero new objects** in `features-calendar-prd-`,
   `features-cefi-prd-` (delta_one day=2026-05-03), and `features-tradfi-prd-` — no accidental PROD pollution, which was
   the exact false-success class the original issue (`features_e2e_smoke_matrix_writes_to_prod_bucket_2026_08_01.md`)
   was about.
2. **Harnesses genuinely verify.** A PASS is a real `captured`/`empty_confirmed` manifest row in the `-test-` bucket
   (calendar TRADFI + CEFI-alone both PASS via `empty_confirmed`); FAILs are genuine reasons (dependency-check
   rejection, stale-consolidator fail-close, missing bucket, 600s compute bound) — never the old silent
   write-to-PROD-and-"pass".
3. **cross_instrument timeout + memory hardening VERIFIED.** The CEFI cell ran the full compute for 600s then the
   process GROUP was fully reaped via `os.killpg` (verified: zero surviving `features_service.cross_instrument`
   processes, host memory clean). The `run-bounded-analysis.sh` wrapper (8G cap) never tripped — the timeframe-scoped
   read fix (`features-service@2aea0e59`) is effective. This directly validates both the INFRA fix
   (`e2e-testing@404e4d8`-era content) and the memory fix that were the prerequisites to running this P2 at all.

### Per-family results

| Family           | Result                                                                                                                                                                                                                                                                             | Blocker (all pre-existing, none from P0/P2)                                                                                                                                                                |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| calendar         | **PASS** (both cells PASS when run as a single-cell invocation; the two-cell matrix's FIRST cell hits a `time_features` CLI rc=1 that the identical command avoids on the next cell — the already-documented transient external-fetch flake from `e2e-testing@8425ec5`'s evidence) | none                                                                                                                                                                                                       |
| onchain          | FAIL                                                                                                                                                                                                                                                                               | dep-check `market-tick-data-service-perp` blocked by BINANCE-DELIVERY `perp_funding` `attempted_failed` 12+ consecutive days (07-24→08-04) despite HYPERLIQUID + KALSHI-PERP captured — see Finding 1      |
| delta_one        | FAIL                                                                                                                                                                                                                                                                               | dep-check "No data for 2026-07-31/CEFI"; fallback date 2026-05-03 insufficient-candles — root: `resolve_latest_captured_date` returns None for `(market-data, cefi/tradfi, processed_candles)` — Finding 2 |
| cross_instrument | FAIL                                                                                                                                                                                                                                                                               | compute exceeds the 600s per-cell smoke bound (memory fine) — Finding 6                                                                                                                                    |
| multi_timeframe  | FAIL                                                                                                                                                                                                                                                                               | all 36 manifest rows `attempted_failed` (reads delta_one features, absent for fallback date) + verifier checks wrong `features/by_date/` prefix + asset_group filter that never matches — Finding 3        |
| sports           | FAIL                                                                                                                                                                                                                                                                               | CLI subprocess dep-check `ManifestConsolidatorStaleError` on `features-sports-test-` — Finding 4                                                                                                           |
| volatility       | FAIL                                                                                                                                                                                                                                                                               | dep-check "missing 1 required upstream" for 2026-05-03 (same processed_candles class as delta_one) — Finding 2                                                                                             |
| commodity        | FAIL                                                                                                                                                                                                                                                                               | test bucket `features-commodity-test-{pid}` never provisioned → 404 on write — Finding 5                                                                                                                   |

## Why it matters

- The **core P2 goal is proven**: the "institutional smoke matrix" contract now genuinely holds — harnesses write to and
  verify against `-test-` buckets, and a FAIL is honest. This closes the original issue's premise (smoke "PASS" was
  previously meaningless, masking PROD writes).
- The 6 blockers are **pre-existing upstream data / harness issues**, NOT regressions from the P0/P2 fixes. They make
  the smoke matrix unable to demonstrate a full-family PASS, which is exactly the gap the P2 todo wanted to expose. Each
  is now an actionable todo below.
- **Finding 2's second half (processed_candles production stalled ~2026-07-15) is potentially a live data-pipeline
  availability gap**: cefi `processed_candles` blobs stop at ~2026-07-15 (0 blobs for 07-31/08-01) in the PROD bucket
  that delta_one/cross_instrument/volatility read — if MDPS output truly stalled, production feature computation for
  those families is also starved, not just the smoke matrix. Needs verification beyond this smoke-scope doc.

## Recommended decision / Todos

- [x] ✅ [DATA] P1. **features-service / e2e-testing** — root-cause why
      `resolve_latest_captured_date(market-data, cefi/tradfi, processed_candles)` returns None —
      features-service@0179af31. **Root cause**: `processed_candles` is a GCS path prefix, NOT a manifest `data_type`
      column value. MDPS writes candle output rows with data_types like `ohlcv_1m`, `ohlcv_15s`, etc.
      (service_name=`market-data-processing-service`). The literal `data_type == "processed_candles"` filter matched
      ZERO rows. **Fix**: when `data_type="processed_candles"`, `resolve_latest_captured_date` now reads `service_name`
      too and filters by `service_name="market-data-processing-service"` AND `data_type` starting with `"ohlcv_"`.
      Verified live against CEFI PRD manifest: returns 2026-05-23 (was None); TRADFI: returns 2026-08-04 (was None). All
      9 existing tests pass.
- [x] ✅ [DATA] P1. **market-tick-data-service / operator** — determine whether cefi `processed_candles` production
      genuinely stalled ~2026-07-15 (0 blobs observed for 2026-07-31/2026-08-01 in `market-data-tick-cefi-prd-...`). If
      MDPS output stopped, that is a live upstream availability gap starving production delta_one/cross_instrument/
      volatility feature compute, not just the smoke matrix. (repo: market-data-processing-service; scope: MDPS
      production health) — **DETERMINED 2026-08-05 (slot-2): GENUINELY STALLED for recent dates — CONFIRMED.** Last
      full-corpus cefi batch production = the 2026-07-28 `mdps-backfill-cefi-20260728-*` run (RESUME_END_DATE=
      2026-07-25; venues HYPERLIQUID/LIGHTER-ZKSYNC/EXTENDED-STARKNET; data_type=trades; every 07-15→07-28 write is
      timestamped 07-28/07-29Z). Since then NO full-corpus recent-date backfill was launched: the only cefi MDPS VMs are
      ASTER-only historical (08-02, at 2025-11-06 as of 08-05T21:48Z), BYBIT/DERIBIT options-chains (08-04), and
      manifest-merge (08-05). GCS `processed_candles` gap: 07-26, 07-27, 07-29→08-02, 08-04, 08-05. The finding's exact
      date "~07-15" was imprecise (production wrote through 07-28 on 07-28/29), but the core concern is confirmed:
      upstream `raw_tick_data` EXISTS for every missing day (07-26: 1696 objects, 07-29: 2841, 07-31: 2815, 08-01: 2733,
      08-02: 2101) and the live raw VM `mtds-live-cefi-consolidated-20260802` actively records 08-02→08-05 — so this is
      an MDPS processed_candles DERIVATION gap, NOT upstream absence. Live availability gap starving production
      delta_one/cross_instrument/volatility feature compute, as hypothesized.
- [ ] [DATA] P1. **market-data-processing-service / operator** — launch a cefi `processed_candles` recent-date catch-up
      backfill to close the confirmed gap (2026-07-26 → today; data_type=trades; full cefi venue set
      HYPERLIQUID/LIGHTER-ZKSYNC/EXTENDED-STARKNET). Safe-idempotent justification: RESUME_MODE=full skip-enabled re-run
      under `launch-mdps-backfill-vm.sh` (skip-enabled shards re-run on preemption per spot-vms-for-backfill);
      re-running skips already-processed dates, so no data is destroyed or duplicated — reversibility is inherent. Use
      RESUME_START_DATE=2026-07-26, RESUME_END_DATE=$(date +%F). This closes the delta_one/cross_instrument/ volatility
      upstream starvation identified above. (repo: market-data-processing-service / deployment-service)
- [ ] [DATA] P2. **market-tick-data-service / features-service** — root-cause BINANCE-DELIVERY `perp_funding`
      `attempted_failed` on every date 07-24→08-04 in the cefi PROD manifest (persistent, not transient). Decide between
      (a) fixing BINANCE-DELIVERY perp_funding collection and (b) adding BINANCE-DELIVERY to
      `features_service/onchain/app/core/dependency_checker.py`'s `_KNOWN_OUTAGE_VENUES_BY_SVC` (mirroring the
      POLYMARKET-PERP venue-scoped tolerance from
      `defi_onchain_perp_funding_permanently_unsatisfiable_dependency_2026_07_31.md`), which is required for
      DEFI:onchain's `market-tick-data-service-perp` dependency (and hence the onchain smoke) to pass despite
      HYPERLIQUID/KALSHI-PERP being captured. (repo: features-service and/or market-tick-data-service)
- [ ] [SCRIPT] P2. **e2e-testing** — fix multi_timeframe `smoke_matrix.py` verifier (the two-bug class already fixed for
      cross_instrument/onchain/sports/volatility in `e2e-testing@fbaa722` but MISSED for multi_timeframe): (1)
      `_verify_gcs_parquet` prefix is `features/by_date/day={date}/` but the real writer path is
      `delta_one/by_date/day={date}/feature_group={g}/feature_group_version={N}/timeframe={tf}/data.parquet` (verified
      via `features_service/multi_timeframe/engine/orchestrator.py`); (2) `_verify_test_manifest` filters by
      `asset_group` but multi_timeframe manifest rows carry blank `asset_group` (write-sites never pass it) — switch to
      a `feature_group` filter. Note: this makes the harness HONEST, but the cell will still FAIL until the delta_one
      input (Finding 2) is available, since all 36 current rows are `attempted_failed`. (repo: e2e-testing)
- [ ] [SCRIPT] P2. **e2e-testing** — extend `sports/smoke_matrix.py`'s `MANIFEST_ALLOW_STALE_FALLBACK=true` to the
      `_invoke_cli()` subprocess env (currently set only in the verifier's post-CLI read path at line ~295). The sports
      CLI's own dependency check fail-closes with `ManifestConsolidatorStaleError` on `features-sports-test-*` (whose
      consolidated index is deliberately never built — `-test-` buckets are exempt from the consolidator scheduler per
      `/codex/05-infrastructure/manifest-consolidator-ssot.md` § "Coverage exemptions"), so the smoke can't even reach
      the verifier. Mirror `e2e-testing@555ab37`'s pattern into the subprocess env. (repo: e2e-testing)
- [ ] [OPERATOR] P2. **infra** — provision the commodity `-test-` bucket.
      `features-commodity-test-central-element-323112` does not exist (verified: only PROD
      `commodity-signals-batch-central-element-323112` exists in the 103-bucket listing; the provisioned features test
      set is calendar/cefi/defi/pred/sports/tradfi, no commodity). The commodity smoke's write 404s. Either provision
      the folded-name bucket or repoint `_test_bucket()` to an existing one. (repo: deployment-service)
- [ ] [SCRIPT] P3. **e2e-testing** — decide the per-cell timeout for cross_instrument `smoke_matrix.py`: the CEFI cell's
      real compute (HMM/sklearn fitting over the instrument universe) exceeds the 600s `subprocess` bound and is killed
      (correctly, thanks to the INFRA killpg fix — no orphan, no OOM). Either raise the bound for this family or accept
      the timeout as the honest bound (a smoke that times out IS a valid signal the family can't complete within the
      smoke window). (repo: e2e-testing)

## Progress Log

- 2026-08-05 (slot-5, data_engineering): All 8 families run for real; contract confirmed; 6 findings filed (see checkbox
  evidence in `features_e2e_smoke_matrix_writes_to_prod_bucket_2026_08_01.md` P2). No code shipped in this doc —
  findings are todos for the fleet.
- 2026-08-05 (slot-2, data_engineering): **Finding 2 (cefi processed_candles production) DETERMINED — genuinely stalled
  for recent dates, CONFIRMED.** Evidence: GCS `processed_candles` partitions present daily 07-15→07-28 (all written by
  the 2026-07-28 `mdps-backfill-cefi-20260728-*` catch-up run, timestamps 07-28/07-29Z), then only 08-03 (batch_tardis,
  written 08-04, unregistered in the manifest); missing 07-26/27, 07-29→08-02, 08-04, 08-05. Upstream `raw_tick_data`
  present for every missing day + live raw VM `mtds-live-cefi-consolidated-20260802` active through 08-05 → gap is MDPS
  processed_candles derivation, NOT upstream. No full-corpus recent-date backfill launched since the 07-28 run (end date
  07-25). Remediation tracked as the new P1 todo above (launch 07-26→today catch-up backfill). Note: the consolidated
  `availability_index.parquet` records the candle layer under `data_type=trades` (MDPS service_name + pipeline_mode
  set), NOT `data_type=processed_candles` — relevant to Finding 1's "zero processed_candles rows" read
  (data_type-naming, not absence).
