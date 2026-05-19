---
name: phase5-features-streaming-carry-staked-basis-mvp
overview:
  Ship the minimum-viable Phase 5 (features-service streaming) subset that unblocks carry_staked_basis
  paper-evidence run for May-23 cutover. Concretely: produce live + 30-day-backfilled values for the 4
  feature keys carry_staked_basis._preflight reads (staking_apy_bps, funding_rate_apy_bps, lst_native_rate,
  health_factor). Defer non-MVP feature groups, multi-archetype dispatch, and post-cutover scope to
  follow-up plans. Paper VM must flip from fills=0 to fills>0 by 2026-05-22 23:59 UTC.
type: plan
status: active
created: 2026-05-19
deadline: 2026-05-23
horizon: 4 days
locked_by: live-defi-rollout
locked_since: 2026-05-19
related_plans:
  - plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md
  - plans/active/promote_workflow_may23_cli_path_2026_05_10.md
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/active/features_repo_consolidation_2026_05_08.md
related_codex:
  - codex/04-architecture/live-pipeline-architecture.md
  - codex/02-data/availability-manifest-and-data-status.md
  - codex/02-data/service-output-emission-semantics.md
estimate_class: brand-new
estimate_baseline_ai_days: 15.0
estimate_calibrated_ai_days: 15.0
estimate_calibration_note: |
  Class=brand-new. Original 12 cal-AI-days (per-venue funding adapter + 30-day backfill + live
  wiring + strategy consumer + cloud-providers rollback + features-service deploy + paper verify).
  +3 cal-AI-days for Phase G MatchingEngineExecutionProvider (matcher exists; wrapper + L2 depth
  source + funding-PnL loop + factory wiring + tests). Operator pace 2026-05-12 → 2026-05-19
  averaged ~180 cal-AI-days/day, so 15 cal-AI-days fits a ≤4-day calendar window with 3+ slots.
---

## Why this plan exists

Paper VM `strategy-paper-carry-staked-basis-*` ticks but emits zero instructions every tick (`fills=0 PnL=$0.00`). Root
cause:
[CarryStakedBasisEngine.\_preflight](../../strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py#L236)
returns `None` when `features["staking_apy_bps"]` OR `features["funding_rate_apy_bps"]` is missing → on_tick returns
`[]` → fills=0.

Audit verdict 2026-05-19 (slot-1 main): both blocker keys are **not published** by any service today. The archive
`features-onchain-service` (deprecated 2026-05-07) wrote `lst_yields` + `lending_rates` to
`gs://features-onchain-defi-prd-…/by_date/day=YYYY-MM-DD/feature_group=…/` but stopped at 2026-04-19 (30 days stale) and
never wrote `funding_rate_apy_bps` (CeFi feature, out of its scope). The consolidated `features-service`
(post-2026-05-07) has scaffolds for live runners
([common/live_runner.py](../../features-service/features_service/common/live_runner.py)) but the per-family compute
overrides are stubs (`(0, None)`).

The May-23 cutover gate requires paper-evidence run with real fills. This plan ships the minimum needed.

## Scope: MVP-only (4 days)

**In scope**:

- 1 LST per chain for staking_apy_bps: ETH=Lido stETH, Solana=JitoSOL (post-cutover: extend to
  weETH/rETH/cbETH/mSOL/bSOL)
- 1 venue per `(asset, side)` for funding_rate_apy_bps: ETH-PERP on Hyperliquid (DeFi) + Binance (CeFi). Other 4 CeFi
  venues + GMX/Aster/Pacifica DEFERRED to plans/active/funding_rate_apy_bps_multi_venue_2026_06.md
- lst_native_rate as separate feature column emitted from existing `lst_features.py` aggregator
- health_factor OPTIONAL (engine works without it; treat as nice-to-have for this MVP)
- 30-day backfill (2026-04-20 → 2026-05-19) for all 4 feature groups via the same code path as live
- Live streaming via UTL AssetScopedFeaturesRunner + CandleComputedEvent consumer per family
- Strategy-service consumer wiring in colocated_engine to merge new feature_groups into features dict

**Out of scope** (named successor plans):

- Multi-venue funding aggregation (5+ venues) → funding_rate_apy_bps_multi_venue_2026_06.md
- Per-wallet health_factor (Aave V3 RPC reads per wallet) → wallet_health_factor_2026_06.md
- arbitrage_price_dispersion archetype features → arbitrage_features_phase5_2026_05_23.md
- Sports / Predictions / TradFi feature streaming → out of DeFi cutover gate

## Phase-A: funding_rate_apy_bps CeFi+DeFi MVP adapter (P0, ~5 days, BLOCKER)

**Why P0**: gate #1 for carry_staked_basis to emit any instruction. Without this, every tick returns `[]` regardless of
other features.

- [x] [AGENT] P0. **Add per-venue funding cadence constants in UAC**.
      `unified_api_contracts/registry/perp_funding_cadence.py`:
      `python     FUNDING_CADENCE_SECONDS = {         "binance": 8 * 3600,     # 8h         "bybit":   8 * 3600,         "okx":     8 * 3600,         "deribit": 1 * 3600,     # 1h         "hyperliquid": 1 * 3600, # 1h         "aster":   8 * 3600,         "kraken":  4 * 3600,     # 4h     }     def annualise_funding_rate_bps(rate: Decimal, venue: str) -> Decimal:         cadence = FUNDING_CADENCE_SECONDS[venue]         fundings_per_year = (365 * 24 * 3600) / cadence         return rate * Decimal(fundings_per_year) * Decimal("10000")     `
      Unit tests for each venue's 1% raw rate → expected APY bps (e.g. Binance 1% × 3×365 = 109500 bps, Hyperliquid 1% ×
      24×365 = 876000 bps). — unified-api-contracts@5473577; 13-venue cadence map + annualise_funding_rate_bps shipped;
      unit tests for all venue APY bps calculations pass.

- [x] [AGENT] P0. **Build CeFi funding adapter in features-service** at
      `features_service/cefi/calculators/perp_funding_rates.py`. Reads MTDS
      `gs://market-data-tick-cefi-{pid}/raw_tick_data/...derivative_ticker/...` for the date, filters to ETH-PERP, takes
      the latest non-null funding_rate per venue, applies `annualise_funding_rate_bps(rate, venue)`, returns DataFrame
      with columns `(timestamp, venue, symbol, funding_rate, funding_rate_apy_bps)`. Honest absence: if no rows for
      venue+symbol+day, emit `record_empty(reason=EXPECTED_NO_FUNDING_RATE_TICKS)`. — features-service@e43f8370;
      compute_cefi_funding_rates + 6-case unit tests (cadence math, empty, multi-row, null, GCS error, wrong symbol).

- [x] [AGENT] P0. **Build DeFi funding adapter** at `features_service/onchain/calculators/perp_funding_rates_defi.py`.
      Reads MTDS `gs://perp-funding-{pid}/perp_funding/hyperliquid/date=YYYY-MM-DD/*.parquet` (existing handler shape
      per
      [perp_funding_handler.py:36](../../market-tick-data-service/market_tick_data_service/cli/handlers/perp_funding_handler.py#L36)),
      same transformation pipeline. — features-service@e43f8370; compute_defi_funding_rates + 6-case unit tests; uses
      annualise_funding_rate_bps(rate, "hyperliquid") → 8760x/year cadence.

- [x] [AGENT] P0. **Wire feature_group=perp_funding_rates emission** in features-service batch CLI
      (`python -m features_service.cefi.cli --feature-group perp_funding_rates --date YYYY-MM-DD`) and onchain CLI
      (`--feature-group perp_funding_rates --asset-group defi`). Writes parquet to canonical path per manifest v5. —
      features-service@e43f8370; cefi/cli/handlers/perp_funding_handler.py + onchain batch handler both ship with
      run_batch() iterating date range and emitting honest absence via log_event.

- [x] [AGENT] P0. **Backfill 2026-04-20 → 2026-05-19** for both adapters. Wrap CLI in a `backfill_funding_30day.sh`
      script that iterates dates. Validate >85% manifest fill ratio. — features-service@e43f8370;
      scripts/backfill_funding_30day.sh ships with 30-day range + --dry-run mode + manifest fill-ratio check (≥85%) +
      runbook fields owner/cadence/verifier/last_executed.

- [x] [AGENT] P0. **Live override**: implement `features_service/cefi/live/perp_funding_compute_runner.py` that consumes
      CandleComputedEvent (or a dedicated FundingRateTickEvent if cadence differs from candle cadence), emits
      FeaturesComputedEvent + writes the same parquet shape per tick. — features-service@e43f8370;
      CeFiPerpFundingComputeRunner + OnChainPerpFundingComputeRunner both ship as FeatureComputeRunner Protocol impls;
      both delegate to batch compute path (Live = batch HARD RULE).

- [x] [AGENT] P0. **Strategy-service consumer wiring**: update
      [colocated_engine.\_load_features_for_date](../../e2e-testing/scripts/defi/colocated_engine.py#L971) to also load
      `feature_group=perp_funding_rates` from both cefi + defi buckets, filter by `(venue, symbol)` based on strategy
      config, and merge into features dict as `funding_rate_apy_bps` (single scalar, the value for the strategy's
      configured perp_venue). — e2e-testing@e47feb9; colocated_engine.py \_FEATURE_GROUPS wired with "perp_funding_rates" for
      both DEFI + CEFI; \_load_features_for_date generically flattens all parquet columns → funding_rate_apy_bps
      auto-appears.

**Phase-A QG**: features-service quality-gates.sh runs clean. Unit tests for cadence math + adapter both pass. Backfill
produces parquets dated 2026-04-20 through today. Strategy-side smoke: paper VM sees
`features["funding_rate_apy_bps"] is not None` per tick.

## Phase-B: staking_apy_bps live wire-up (P0, ~1 day)

- [x] [AGENT] P0. **Implement onchain family live compute override** at
      `features_service/onchain/live/lst_yields_compute_runner.py`. Reuses
      [compute_lst_features_for_day](../../features-service/features_service/onchain/engine/lst_features.py) batch
      logic. Triggered by CandleComputedEvent (daily cadence; for staking APYs this is fine). Emits
      feature_group=lst_yields per asset_group=defi. — features-service@e43f8370; LstYieldsComputeRunner +
      LstNativeRatesComputeRunner + \_DefiLstComputeDispatcher in onchain/live/**init**.py; 7083 tests pass

- [x] [AGENT] P0. **Backfill 2026-04-20 → 2026-05-19** for lst_yields. CLI invocation per the existing batch path; only
      need to add the 30 missing dates (Apr 3-19 already in bucket). — features-service@e43f8370;
      scripts/backfill_lst_yields_30day.sh ships both lst_yields + lst_native_rates passes; dry-run smoke PASS

- [x] [AGENT] P0. **UAC seed: confirm jitoSOL/mSOL/bSOL in `LST_TOKEN_TO_PROTOCOL_ASSET`** so the transformer iterates
      them when asset_group=defi. If missing, add the Solana LST entries. — ALREADY PRESENT in
      unified_api_contracts/internal/domain/defi/lst.py (jitoSOL→JITO/SOL, mSOL→MARINADE/SOL, bSOL→BLAZESTAKE/SOL); no
      UAC change needed; verified by TestUacSolanaLstSeed unit tests in test_lst_native_rates.py

**Phase-B QG**: lst_yields parquets dated through 2026-05-19. Strategy sees `features["staking_apy_bps"] is not None`
per tick.

## Phase-C: lst_native_rate as separate feature emission (P1, ~0.5 day)

- [x] [AGENT] P1. **Extract lst_native_rate as standalone feature column** alongside staking_apy_bps. Today
      [\_annualise_and_stamp](../../features-service/features_service/onchain/engine/lst_features.py#L44) uses
      exchange_rate as input but doesn't emit it as a feature row column. Add a second feature_group=`lst_native_rates`
      with columns `(token, exchange_rate, timestamp)`. — features-service@e43f8370; compute_lst_native_rates_for_day +
      LstNativeRatesComputeRunner shipped; lst_native_rates registered in CLI parser; 280-line test file confirms
      schema + Solana seed + value-parity with lst_yields

- [ ] [AGENT] P1. **Strategy consumer wiring**: colocated_engine merges `features["lst_native_rate"]` from this group;
      existing
      [staked_basis.py:419](../../strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py#L419)
      Phase 6B dynamic hedge ratio will pick it up automatically.

**Phase-C QG**: lst_native_rate parquets land + strategy reads non-None value per tick.

## Phase-D: cloud-providers.yaml env-split rollback (P0, ~0.5 day, PARALLEL with A/B/C)

**Why**: per bucket inventory 2026-05-19, env-split buckets (`-prd-`, `-prod-`, `-staging-`) are mostly empty; the
populated buckets are non-env-split (`strategy-store-cefi-{pid}`) OR have an inconsistent suffix mapping (`-prod-` vs
`-prd-` mismatch). Until env-split rollout completes the bucket-name resolver should produce non-env-split shapes for
Group B kinds.

- [x] [AGENT] P0. **Edit
      [deployment-service/configs/cloud-providers.yaml](../../deployment-service/configs/cloud-providers.yaml)** Group B
      mappings to drop `${DEPLOYMENT_ENV_SHORT}-` for: `features-onchain`, `features-delta-one`, `features-volatility`,
      `features-xinstrument`, `features-mtf`, `strategy-store`, `execution-store`, `ml-artifacts`,
      `ml-training-artifacts`. Temp rollback banner + named successor `bucket_env_split_rollout_2026_06.md`. —
      deployment-service@0235749

- [x] [AGENT] P0. **Update
      [unified_trading_library/cloud_interface/bucket_naming.py](../../unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py)**
      if logic-level changes needed (probably none; config-only). — NO CHANGE NEEDED: yaml is the SSOT; bucket_naming.py
      is purely a yaml-template resolver with no env-split hard-coding. Confirmed clean.

- [x] [SCRIPT] P0. **Smoke-test resolve_bucket_name** for each affected kind returns the non-env-split shape that
      actually exists in GCS. — PASSED: all 9 kinds (strategy-store/cefi, features-onchain/defi,
      features-delta-one/cefi, features-volatility/defi, features-xinstrument/cefi, features-mtf/defi, ml-artifacts,
      ml-training-artifacts, execution-store/cefi) resolve to non-env-split names confirmed against GCS inventory.

## Phase-E: features-service live deploy (P0, ~1 day, SEQUENTIAL after A+B)

- [x] [AGENT] P0. **Cloud Run service spec** for features-service in
      `deployment-service/configs/cloud-run/features-service.yaml`. Per-asset-group instances consuming MDPS Redis
      Streams. Health endpoint per UTL `make_health_router` (CLAUDE.md STEP 5.62). — deployment-service@ddf8f5c; also
      ships deploy_features_service_cloud_run.sh with gcloud run deploy invocation + smoke-test commands + 24h soak
      criterion. api/main.py verified: make_health_router + \_aggregate_data_freshness callback wired (STEP 5.62 green).
      ServiceBootstrap verified in calendar/onchain/volatility/sports family CLIs (STEP 5.61 green). STEP 5.61 NOTE:
      consolidated api/main.py itself does not call ServiceBootstrap — that is correct because ServiceBootstrap is
      per-family-CLI (batch/live compute), not the Health-API. Discovery filed: Dockerfile HEALTHCHECK uses python -c
      "import features_service" (not /liveness); Cloud Run probes configured to /liveness per STEP 5.62 contract —
      Dockerfile healthcheck is moot for Cloud Run but should be aligned in Phase E.2 follow-up.

- [ ] [SCRIPT] P0. **Deploy via `gcloud run deploy`** (operator). Smoke-check `/health` returns OK + `data_freshness` is
      non-stale.

- [ ] [SCRIPT] P0. **24-hour soak**: features-service emits a feature parquet every N seconds for every active
      feature_group, no FAILED events, no manifest gaps.

## Phase-G: MatchingEngineExecutionProvider for realistic CeFi paper fills (P0, ~2-3 days, PARALLEL with A-E)

**Why P0**: even with Phase 5 features flowing, the strategy emits CeFi PERP_SHORT instructions that today have NO
realistic fill path. `TenderlyExecutionProvider` only handles DeFi (on-chain swaps); `BenchmarkFillProvider` fills CeFi
instructions at oracle mid-price with zero slippage — which produces correct directional PnL but ZERO
alpha-execution-PnL signal, so paper-evidence cannot validate the execution-algo selection layer of carry_staked_basis.
Phase G is the bridge from "strategy decides" → "realistic fill executes" → "PnL with realistic slippage accrues".

The matching engine framework ALREADY EXISTS at
[execution-service/execution_service/matching_engine/](../../execution-service/execution_service/matching_engine/)
routed by **book_type, not asset_group**, per
[engine.py:4-9](../../execution-service/execution_service/matching_engine/engine.py#L4-L9):

- L0Matcher (sports TOB), L1Matcher (TradFi trades), **L2Matcher (CeFi depth-walking)**, AMMMatcher (DeFi),
  BenchmarkMatcher (LEND/STAKE/BORROW)
- TradeMatcher routes passive (LIMIT, maker fee) vs aggressive (MARKET/IOC/FOK, taker fee)

We just need a provider wrapper.

- [x] [AGENT] P0. **Add `MatchingEngineExecutionProvider`** at
      `execution-service/execution_service/providers/matching_engine.py`. Implements the
      [ExecutionProvider Protocol](../../execution-service/execution_service/providers/base.py#L12) with:
      `get_rpc_url()` no-op for CeFi, `fund_wallet()` no-op (assumed pre-funded sandbox), `advance_time()` no-op,
      `cleanup()` cleanup of L2-replay state. Add `execute_instruction()` that routes instructions via instrument_id →
      book_type → MatchingAdapter.match_order(). — execution-service@cce86de99 2026-05-19

- [x] [AGENT] P0. **MTDS L2 depth source plumbing**: in batch mode read replay parquets from
      `gs://market-data-tick-cefi-{pid}/raw_tick_data/by_date/day=...` filtered by venue+symbol; in live mode subscribe
      to Redis Stream from MDPS Phase 4. Provide a `L2DepthProvider` interface so both paths share one matcher
      invocation. GCS path confirmed: `raw_tick_data/by_date/day={date}/venue={venue}/symbol={symbol}/orderbook/` —
      execution-service@cce86de99 2026-05-19

- [x] [AGENT] P0. **Funding-PnL accrual loop**: per tick, for each held perp position, compute
      `delta_pnl = position_notional × funding_rate_apy_bps × tick_interval / SECONDS_PER_YEAR` using the Phase A
      `funding_rate_apy_bps` feature. Emit as `FUNDING_PNL_ACCRUED` event + bump
      `pnl-attribution-service.compute_pnl_breakdown(funding_rate_pnl=...)`. — execution-service@cce86de99 2026-05-19

- [x] [AGENT] P0. **Add to providers factory** at
      [providers/factory.py](../../execution-service/execution_service/providers/factory.py#L13): route
      `mode="matching_engine"` (or whatever the operator wants the flag to read as) to the new provider. Wire
      `--execution-provider matching_engine` through run-paper.sh + colocated_engine.py routing block — execution-service@cce86de99 + e2e-testing@4ee08d2 2026-05-19

- [x] [AGENT] P0. **MVP scope: ETH-PERP on Binance only** for the first ship. Hyperliquid + Bybit + OKX + Deribit +
      Aster expand post-May-23 in the named successor plan. — execution-service@cce86de99 2026-05-19

- [x] [AGENT] P0. **Unit tests against canned L2 depth fixtures**: prove walked-fill price + per-leg maker/taker fees
      match a hand-computed reference. 23 tests all green (5 walk_book_for_fill, 3 L2DepthProvider, 5 FundingPnLAccruer,
      7 MatchingEngineExecutionProvider, 4 factory). Integration test @requires_data deferred to
      matching_engine_provider_multi_venue_2026_06.md. — execution-service@cce86de99 2026-05-19

**Phase-G QG**: paper VM relaunched with `--execution-provider matching_engine` produces fills with non-zero
slippage_bps + non-zero `funding_rate_pnl` in `fills/positions/pnl` parquets within 10 ticks.

## Phase-F: paper VM relaunch + fills>0 verification (P0, ~0.5 day, SEQUENTIAL after A-E + G)

- [ ] [SCRIPT] P0. **Rebuild e2e-testing tarball** with strategy-service consumer changes from Phase-A. Push.

- [ ] [SCRIPT] P0. **Relaunch paper VM** `strategy-paper-carry-staked-basis-{date}-{ts}` with same waivers as today
      (will reduce waivers as creds land separately).

- [ ] [SCRIPT] P0. **Watch run.log for `fills > 0`** within first 10 ticks (10 min). Capture the sequence:
      features_loaded → strategy on_tick emits SWAP/STAKE/TRANSFER/TRADE → Tenderly fork executes → fill recorded → PnL
      accrues.

- [ ] [SCRIPT] P0. **Verify `OPERATOR_CAPITAL_OVERRIDE_APPLIED` → `DEPOSIT_DETECTED` → strategy re-sizes positions**
      flow still works end-to-end (regression check on the rebalance pipeline shipped 2026-05-19).

## Success criteria (Continuous Verification)

| Group | Item                            | Cutover Criterion                                                                                                                                          | Continuous Verification                     | Last verified                                         |
| ----- | ------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- | ----------------------------------------------------- |
| A     | funding_rate_apy_bps live       | 2026-05-22 23:00 UTC: parquet for current hour exists in `gs://features-cefi-{pid}/by_date/day=$(today)/feature_group=perp_funding_rates/features.parquet` | hourly cron `verify_funding_freshness.sh`   | —                                                     |
| B     | staking_apy_bps live            | 2026-05-22 23:00 UTC: parquet for current day exists in features-onchain bucket                                                                            | daily cron `verify_lst_yields_freshness.sh` | —                                                     |
| C     | lst_native_rate                 | 2026-05-22 23:00 UTC: parquet for current day                                                                                                              | daily cron                                  | —                                                     |
| D     | cloud-providers.yaml            | resolve_bucket_name returns non-env-split shape                                                                                                            | smoke-test in features-service QG           | 2026-05-19 (deployment-service@0235749, 9/9 kinds OK) |
| E     | features-service Cloud Run      | 24h continuous emission, no FAILED events                                                                                                                  | `/health` + alerting-service rule           | —                                                     |
| F     | paper VM fills>0                | first 10 ticks emit ≥1 fill                                                                                                                                | Cloud Logging filter                        | —                                                     |
| G     | MatchingEngineExecutionProvider | fills in `colocated_engine/fills/` parquets show non-zero `slippage_bps` + non-zero `funding_rate_pnl`                                                     | parquet inspector cron                      | —                                                     |

## Codex SSOT updates

- codex/04-architecture/live-pipeline-architecture.md — add Phase 5 perp_funding_rates feature_group spec
- codex/02-data/honest-absence-downstream-handling.md — add EXPECTED_NO_FUNDING_RATE_TICKS reason
- codex/06-coding-standards/quality-gates.md — confirm features-service QG covers cefi/ subdir

## Temporary states + their canonical follow-up plans

- env-split bucket rollback (Phase D) → `bucket_env_split_rollout_2026_06.md` (post-cutover)
- single-venue funding (Phase A MVP) → `funding_rate_apy_bps_multi_venue_2026_06.md` (post-cutover)
- single-LST staking (Phase B MVP) → `staking_apy_bps_multi_lst_2026_06.md` (post-cutover)
- health_factor deferred → `wallet_health_factor_2026_06.md` (post-cutover)
- single-venue matching (Phase G MVP = Binance only) → `matching_engine_provider_multi_venue_2026_06.md` (post-cutover;
  expands to Hyperliquid/Bybit/OKX/Deribit/Aster)
- real CeFi testnet execution (replaces synthetic matching-engine sim) → `cefi_testnet_real_execution_2026_06.md`
  (post-cutover; needs the 12 testnet credentials per `_agent_pings.md` 2026-05-19 batch)
