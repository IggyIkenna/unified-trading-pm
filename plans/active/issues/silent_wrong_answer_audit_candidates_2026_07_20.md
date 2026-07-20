---
doc_type: issue
title: >-
  Silent-wrong-answer class audit — 26 candidate findings across 8 repos, 2 personally confirmed P0s, the rest
  finder-evidenced but pending adversarial verification
summary: >-
  A 10-lens workshop-style audit for the silent-wrong-answer class (a lookup that cannot fail plus a caller that cannot
  fail) surfaced 26 distinct candidate findings across strategy-service, features-service, e2e-testing, ml-service,
  deployment-service, market-data-processing-service, execution-service, system-integration-tests and UTL. Seven finder
  lenses completed with runtime-executed / object-probed evidence; every adversarial VERIFIER died on a session limit,
  so with two exceptions these are FINDER-EVIDENCED, NOT adversarially verified — treat accordingly. The two exceptions
  are P0s I re-probed against prod GCS myself and confirmed: strategy-service GCSFeatureProvider reads a bare `by_date/`
  prefix that matches zero objects (the DeFi features bucket has only `onchain/` and `_index/`), and the PnL gas-fee
  reader prices every DeFi fill at a hardcoded 1 gwei because its `gas_fees/` path exists in no bucket. The recurring
  shape is a wrong bucket/path/token resolving to nothing, an exception or empty default swallowing the miss, and a
  plausible wrong number or false-green verdict flowing on.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data, features]
repos:
  [
    strategy-service,
    features-service,
    e2e-testing,
    ml-service,
    deployment-service,
    market-data-processing-service,
    execution-service,
    unified-trading-library,
  ]
scope: [engineer, admin]
tags: [silent-failure, data-correctness, pnl-correctness, false-green, buckets, audit]
related:
  [
    silent_wrong_answer_bucket_resolution_class_2026_07_20.md,
    features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md,
    pipeline_smoke_sweep_findings_2026_07_20.md,
  ]
created: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 1.2
assigned_role: backend
drift_direction: advance-code
depends_on: []
source:
  [
    "10-lens silent-wrong-answer audit workflow run 2026-07-20; 7 finder lenses completed, all adversarial verifiers
    died on a session limit so most findings are finder-evidenced only",
  ]
resolved_by:
locked_by:
---

# Silent-wrong-answer audit — candidate findings

## Evidence status — READ THIS FIRST

The finder lenses were rigorous: each finding below was read in the enclosing function and up its caller chain, and
where it makes a bucket/path claim it was object-probed with `gcloud storage ls` (never `buckets describe`, which 403s
for this service account) or runtime-executed against the real resolver in the real repo `.venv`. **But the adversarial
verification pass — three independent refute/reachability/consequence agents per finding — died on a session limit, so
with two exceptions these are UNVERIFIED.** Do not ship a fix on finder evidence alone; re-run the verification pass
first, then fix survivors. The two exceptions are marked **✅ CONFIRMED (re-probed by hand)**.

A cross-cutting caveat the finders themselves flagged: several DeFi findings depend on the unresolved feature_group
**vocabulary ruling** in [[features_onchain_featureless_shards_and_vocabulary_split_2026_07_20]]. A path/prefix fix is
safe under every hypothesis; a NAME re-point is not — it can make a reader hit one of the five feature-less placeholder
shards, converting a detectable total miss into an undetectable partial success.

## P0

| #   | repo · site                                      | finding                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | evidence                                                                                                                                                                                                                                        |
| --- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | strategy-service · `gcs_feature_provider.py:187` | **✅ CONFIRMED.** Reads `by_date/day=…/feature_group=…/` with NO `onchain/` object-key prefix. The DeFi features bucket has only `onchain/` and `_index/` top-level prefixes, so every DeFi feature read returns an empty frame behind the existing `logger.warning`. Reached from live paper + batch (`paper_run_handler`, `batch_data_loading`, `canonical_perp_funding_provider`). Same class as the already-shipped `pnl/engine/orchestrator.py@af1ced80` fix.              | I re-probed prod: bare `by_date/` = "matched no objects"; `onchain/by_date/day=…` is populated. **Being fixed in the in-flight fix wave.**                                                                                                      |
| 2   | strategy-service · `pnl_input_builder.py:56,94`  | **✅ CONFIRMED (deeper than a prefix bug).** `_get_gas_price_at_timestamp` returns a hardcoded `Decimal("1")` (1 gwei) for every DeFi fill because `_load_gas_fee_data` reads `gas_fees/chain_id=…/`, a prefix that exists in NO bucket. `gas_cost_usd` is a real cash outflow subtracted in `compute_pnl_breakdown`, so DeFi realised PnL is systematically overstated. My earlier bucket-repoint fixed the NAME; the PATH is still wrong and gas data's real home is unknown. | I re-probed the resolved tick bucket `market-data-tick-defi-prd`: it has `dex_pools/`, `lending_indices/`, … but **no gas-fee prefix anywhere**. Needs investigation (where does gas data live / is it captured at all), NOT a blind path edit. |

## P1

| #   | repo · site                                                        | finding                                                                                                                                                                                                                                                                                                                                                                                                     |
| --- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 3   | strategy-service · `exposure_monitor.py:159`                       | A missing price (`utility_manager.get_price` returns `0.0`, three silent returns, no raise) **drops the position from exposures**, so equity, hourly P&L, HWM, drawdown and Aave LTV/health-factor are all computed on a truncated position set. Drawdown feeds the protective circuit-breaker, so this can mis-arm or mis-suppress it.                                                                     |
| 4   | market-data-processing-service · `build_continuous_engine.py:69`   | `_resolve_tradfi_bucket()` passes `kind="market-data-tick-tradfi"` (a bucket-name FRAGMENT). Post-UTL-fix this now **raises `BucketNamingError`**, so the Panama-canal back-adjusted continuous-futures stage dies at line 1 and has never produced output. Any `instrument_type=continuous_future` strategy/feature/backtest silently evaluates on nothing.                                                |
| 5   | features-service · `paired_dispatch.py:246`                        | `paired_price_dispersion` reads `by_date/day=…/feature_group=…/` — missing the Fold-A `delta_one/` prefix AND carrying a spurious `by_date/` segment; the kernel returns an empty frame but reports `success=True`. UAC's 13-row `PAIRED_DISPERSION_CATALOG` produces no dispersion features for every date the job ran.                                                                                    |
| 6   | UTL + client-reporting-api · `client_factory.py:129`               | Two public `get_secret` implementations disagree: `unified_trading_library.get_secret` returns `None`+warning, `…cloud_interface.get_secret` raises `RuntimeError`. client-reporting-api catches only `RuntimeError`, so a missing exchange API key becomes a credential dict full of `None` **counted and logged as loaded** — live NAV/reporting + emergency-close build CCXT clients with `apiKey=None`. |
| 7   | deployment-service · `meta_targets.py:89`                          | data-pipeline monitors silently DROP the prediction asset_group: `kind="market-data"` has no PREDICTION entry and `except Exception: continue` swallows the raise, so DP-FETCH-009 (high `attempted_failed`) and consolidator-cron freshness report clean over 4 of 5 asset_groups.                                                                                                                         |
| 8   | e2e-testing · `validate_shards_4pillar.py:487`                     | `overall_green=True` for every instruments-store bucket because it samples a `raw_tick_data/` prefix that does not exist there (`checked=0` scored as pass). The default `stores=["tick","instruments"]` run scores HALF the matrix green without reading a single instruments parquet.                                                                                                                     |
| 9   | e2e-testing · `validate_shards_4pillar.py:181`                     | Pillar-3 (schema) and pillar-2 (NaN) are vacuous for 51 of 61 `(asset_group, data_type)` pairs — the "4-pillar" check degrades to `row_count > 0`. This is the harness MTDS quality-gates STEP 5.88 runs and the batch+live matrix delegates its batch verdict to.                                                                                                                                          |
| 10  | e2e-testing · `validate_batch_live_smoke_matrix.py:526`            | The live=batch symmetry verdict can never be `divergent` — the only divergence branch is logically unreachable, so `report.divergent` is structurally always 0 and the daily scheduled live=batch invariant proof cannot fail on divergence.                                                                                                                                                                |
| 11  | deployment-service · `data_status_venue_utils.py:195`              | Venue-coverage smoke can NEVER report a missing venue — `missing_venues` is empty by construction, always prints "100% complete venue coverage", defeating its stated purpose of catching a dead venue adapter.                                                                                                                                                                                             |
| 12  | system-integration-tests · `test_conftest_bucket_resolution.py:27` | SIT `required_gcs_buckets` enumerates env-tier-less names — 41 of 42 are 404 — and two unit tests pin the tier-less shape as correct, so the "all required GCS buckets exist" smoke is vacuous.                                                                                                                                                                                                             |

## P2

| #   | repo · site                                                                    | finding                                                                                                                                                                                                                                                                        |
| --- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 13  | execution-service · `l2_depth_provider.py:240`                                 | L2 + Solana AMM depth providers call `resolve_bucket_name` with bucket-name FRAGMENTS and two kwargs it does not accept → `TypeError` on every batch depth load. Latent until `load_date()` is wired into a batch/paper run (its documented public API).                       |
| 14  | deployment-service · `data_status_venue_utils.py:139` + `config_loader.py:556` | `data-status --check-venues --asset-group prediction` resolves an EMPTY bucket string (`ConfigLoader.get_bucket_name` returns `""` on unknown domain/asset_group) and reports 100% missing coverage for data that exists. `--asset-group` is free text with no `click.Choice`. |
| 15  | features-service · `smoke_matrix.py:222` (×8 matrices)                         | All eight features smoke matrices score `--dry-run` cells as PASS, producing a totals line identical to a real green run.                                                                                                                                                      |
| 16  | features-service · `smoke_matrix.py:204`                                       | features-onchain manifest assertion is not scoped to the `feature_group`, so with `--all-handlers` one asset_group-level row passes all 11 handler cells (and an `empty_confirmed` row passes them with no parquet). Directly relevant to the featureless-shard P0.            |
| 17  | market-data-processing-service · `smoke_matrix.py:177`                         | MDPS/MTDS/IS smoke_matrix verify no freshness — stale `-test-` artefacts from a prior run satisfy both assertions, so a broken compute path reports PASS.                                                                                                                      |
| 18  | market-data-processing-service · `smoke_matrix.py:499`                         | MDPS smoke_matrix has no PROVED-NOTHING guard (its sibling `pipeline_e2e_check.py:1978` does) — an all-skipped run exits 0.                                                                                                                                                    |
| 19  | e2e-testing · `validate_batch_live_smoke_matrix.py:430`                        | Downgrades its own verification errors to `no-data` ("an honest absence"), so a GCS/manifest outage turns the whole batch dimension green with no exit-code change.                                                                                                            |
| 20  | system-integration-tests · `test_coverage_matrix_cells.py:31`                  | Pins the fabricated long-form `instruments-store-prediction-test-{pid}` (404); real is `…-pred-test-…`. The PREDICTION coverage-matrix cell skips forever and the suite reports green.                                                                                         |
| 21  | UTL · `asset_group.py:17`                                                      | `get_bucket_for_category` has three impls through two public doors; the `config_interface` pair fabricates `{asset_group}-store-{pid}` (404) and the unit tests assert the fabricated names. No live consumer today, so the defect is the green verdict.                       |
| 22  | strategy-service · `compute_handler.py:65`                                     | A fills READ FAILURE becomes an empty DataFrame indistinguishable from a genuine no-trade hold day; attribution for that date is silently absent from the parquet and the run exits 0.                                                                                         |

## P3

| #   | repo · site                                                 | finding                                                                                                                                                                                                                  |
| --- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 23  | unified-trading-pm · `prediction_pipeline_e2e_check.py:303` | Prints "ALL PHASES PASSED" unconditionally and skips every Phase-2 assertion when zero trades come back. Manual driver, not gated — low blast radius.                                                                    |
| 24  | execution-service · `tenderly.py:226`                       | Fork funding uses 18 decimals for WBTC (real: 8) — a request for 1 WBTC funds 10^10 WBTC. `_TOKEN_DECIMALS` omits WBTC and defaults to 18. Backtest/paper balance-constrained paths start effectively unbounded in WBTC. |

## Recommended handling

1. **Do not mass-fix on finder evidence.** Re-run the adversarial verification pass (three lenses per finding) now that
   limits have reset; ship only survivors, most-severe first.
2. **Findings 1, 4, 5, 16 and the smoke-matrix set (15, 17, 18)** overlap the DeFi featureless-shard work and the
   false-green harness class already being fixed — reconcile against those before touching, to avoid double edits.
3. **Finding 2 (gas fees)** is not a code one-liner: it needs an answer to "where does DeFi gas-fee data actually live,
   and is it captured at all". That is a data-pipeline question, not a bucket-string fix.
4. **A structural observation the finder made** (worth an operator decision): prediction's flat-kind special-case has
   now been missed at four separate per-asset_group call sites. The durable fix is probably one resolver-level helper
   that maps an asset_group to the correct `(kind, asset_group)` pair, rather than a fifth per-site branch.

## Honest coverage gaps the finders named

- No TypeScript sweep (`unified-trading-system-ui`, `deployment-ui`) and no shell-launcher sweep
  (`deployment-service/scripts/vm/`) — string-interpolated bucket names in shell are a plausible unswept home for this
  class.
- `*_bucket()` helpers that hardcode a name inline (bypassing both resolvers) would not appear in a resolver-call tally.
- `e2e-testing/scripts/strategy/backtest_from_wizard_config.py:191` passes `kind="raw_tick_data"` which runtime-raises
`BucketNamingError`; its caller chain to a live entry point was not traced, so it is recorded but unreported.
</content>
