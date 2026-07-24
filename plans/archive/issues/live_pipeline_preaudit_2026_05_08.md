---
doc_type: issue
title: Live-pipeline pre-audit (Phase 0 of live_pipeline_mtds_mdps_features_2026_05_08)
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    alerting-service,
    batch-live-reconciliation-service,
    client-reporting-api,
    deployment-api,
    deployment-service,
    deployment-ui,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-08
author: tab2-pre-audit
source:
  [
    plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md (Phase 0),
    /codex/05-infrastructure/live-pipeline-architecture.md,
    /codex/05-infrastructure/replay-subsystem.md,
    /codex/02-data/pipeline-mode-partition.md,
    /codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md,
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Live-pipeline pre-audit (Phase 0 of live_pipeline_mtds_mdps_features_2026_05_08)

> **Severity**: P0 audit input — drives Phases 1-13 of `live_pipeline_mtds_mdps_features_2026_05_08`. **Blast radius**:
> 12 repos per `repo_gates` (UAC + UTL + MTDS + MDPS + 8 features-\* repos + instruments-service + alerting-service +
> strategy-service + deployment-api + deployment-ui + deployment-service + PM). Read-only audit; no code changes.
> **Suggested owner**: tab2-pre-audit (this doc) → consumed by Tab-2 sub-agents A/B/C/D shipping Phases 1-13.

## Audit method

- All `rg` searches scoped to `--type py --glob '!.venv*' --glob '!build' --glob '!tests/*'` unless explicitly looking
  for test fixtures (per CLAUDE.md "Analysis Rules").
- Adapter inventory walks `market-tick-data-service/market_tick_data_service/market_interface/adapters/` (the
  live-pipeline path) AND `market_tick_data_service/adapters/` (legacy umi_tick_provider routing — ignored where
  superseded).
- Emergent finding: Phase 1 (UAC streaming events) + Phase 2A (UTL Redis Streams + replay) have ALREADY shipped (commit
  `7d891f69` 2026-05-08 by parallel agents A + B). Section (e) + (g) below reflect the as-shipped state.

## (a) MTDS websocket / streaming code-path inventory

### Already-streaming venues (websocket path lives in `market_interface/adapters/`)

| Venue / venue family                        | File                                                                                                           | WS framework / shape                         | Notes / constraints                                                                                                                                                                       |
| ------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | -------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Binance** (CeFi spot/perp)                | `market_interface/adapters/binance.py` + `websocket/handlers/binance.py`                                       | UTL `connectivity.base_ws` + bespoke handler | Per-key throttling on REST snapshot side; WS feed is per-stream rate-limited                                                                                                              |
| **Bybit** (CeFi spot/perp)                  | `market_interface/adapters/bybit.py`                                                                           | UTL `connectivity.base_ws`                   | Per-key throttling                                                                                                                                                                        |
| **OKX** (CeFi spot/perp)                    | `market_interface/adapters/okx.py`                                                                             | UTL `connectivity.base_ws`                   | Per-key throttling                                                                                                                                                                        |
| **Coinbase** (CeFi spot)                    | `market_interface/adapters/coinbase.py`                                                                        | UTL `connectivity.base_ws`                   | Public-feed throttle                                                                                                                                                                      |
| **Deribit** (CeFi options/perp)             | `market_interface/adapters/deribit.py` + `deribit_ws_mixin.py`                                                 | bespoke `deribit_ws_mixin`                   | RPC-style WS; per-key throttle on private channels                                                                                                                                        |
| **Hyperliquid** (DeFi perp)                 | `market_interface/adapters/defi/live/hyperliquid_ws.py`                                                        | bespoke WS (`websockets` library)            | Public feed; rate-limit on subscription churn                                                                                                                                             |
| **Alchemy** (DeFi onchain)                  | `market_interface/adapters/defi_live/alchemy_adapter.py`                                                       | RPC websocket (`eth_subscribe`)              | API-key throttling per-key/sec                                                                                                                                                            |
| **TheGraph** (DeFi onchain)                 | `market_interface/adapters/defi_live/thegraph_ws_adapter.py`                                                   | Subgraph WS subscriptions                    | Subgraph-specific RL                                                                                                                                                                      |
| **Aster / Lighter / Pacifica**              | `market_interface/adapters/onchain_perps/{aster,hyperliquid,...}_adapter.py`                                   | Mixed (REST + WS for some)                   | **CloudFront IP cooldown** (Lighter / Pacifica per `feedback_lighter_pacifica_cloudfront_quirks` memory) — fresh VM IPs hit transient 429 → relaunch on new IP                            |
| **OptiCodds / Sharp / Polymarket / sports** | `market_interface/adapters/sports/*_adapter.py` + `market_interface/adapters/prediction/polymarket_adapter.py` | mixed REST snapshot + selective WS           | Sports / Prediction: **singleton-lock launchers** (`launch-sfi-forward-poll.sh`, `launch-mtds-prediction-backfill-vm.sh`) — refuses launch if same-prefix VM is RUNNING; `--force` bypass |

### REST-only venues (poll-fallback required for live cascade)

| Venue family                                                                               | Adapter file                                                                                                                   | Why REST-only                                                                      |
| ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| **CCXT (multi-venue)**                                                                     | `market_interface/adapters/cefi/ccxt_adapter.py`                                                                               | CCXT framework predates per-venue WS migration; covers Bitget/Bitfinex/Kraken/etc. |
| **Tardis incremental book**                                                                | `market_interface/adapters/cefi/tardis_incremental_book_adapter.py`                                                            | Historical replay only — not a live source                                         |
| **Databento MBO / equity**                                                                 | `market_interface/adapters/{cefi,tradfi}/databento*.py`                                                                        | Historical-only                                                                    |
| **Upbit**                                                                                  | `market_interface/adapters/cefi/upbit_adapter.py`                                                                              | REST polling                                                                       |
| **TradFi (IBKR / Databento / FRED / OFR)**                                                 | `market_interface/adapters/tradfi/{ibkr,databento,fred,ofr}_adapter.py`                                                        | Trading-hours bound; live polling matches batch shape                              |
| **DeFi (Aave / Curve / Uniswap / Balancer / Morpho / etc.)**                               | `market_interface/adapters/defi/{aave,curve,uniswap_v3,uniswapv2,uniswapv4,balancer,morpho,fluid,instadapp,ethena}_adapter.py` | Subgraph + RPC poll; WS-friendly via `defi_live/` for selected subset              |
| **DeFiLlama / LST adapters**                                                               | `market_interface/adapters/defi/{defillama,lst_etherfi,lst_lido}_adapter.py`                                                   | API poll                                                                           |
| **infra / gas-price**                                                                      | `market_interface/adapters/infra/gas_price_adapter.py`                                                                         | RPC poll                                                                           |
| **Sports core (api_football / footystats / understat / SFI / transfermarkt / open_meteo)** | URDI sources; sports MTDS adapters in `market_interface/adapters/sports/`                                                      | Sources are REST-only by design                                                    |
| **Prediction (Kalshi / Manifold / Polymarket batch)**                                      | `market_interface/adapters/prediction/{kalshi,manifold,polymarket,base_prediction}_adapter.py`                                 | REST + Polymarket has CLOB WS (live-only sub-path)                                 |

### Per-venue connection-pool / rate-limit constraints (Phase 3 must respect)

- **CloudFront cooldowns (Lighter / Pacifica)**: relaunch on new VM IP if 429-spam observed; documented in
  `feedback_lighter_pacifica_cloudfront_quirks` auto-memory + the same memory's "5 quirks" section.
- **Per-key throttling (Bybit / Binance / OKX / Coinbase)**: WS connection counts capped per API key; per-VM
  connection-pool sizing must match `WS_CONNECTIONS_PER_VENUE` config knob (orthogonal to the shard SSOT — does NOT
  appear in the manifest, per
  [`/codex/05-infrastructure/live-pipeline-architecture.md`](/codex/05-infrastructure/live-pipeline-architecture.md) §
  Sharding).
- **Singleton-lock pattern** (sports forward-poll + prediction backfill VMs): launchers refuse to start if a same-prefix
  VM is RUNNING in the zone; `--force` bypass — see launchers `deployment-service/scripts/vm/launch-sfi-forward-poll.sh`
  and `launch-mtds-prediction-backfill-vm.sh`.
- **IP redundancy for high-rate endpoints**: Hyperliquid / Alchemy benefit from multi-VM splay; record in launcher
  VM-name-prefix table per
  [`/codex/05-infrastructure/launcher-script-ssot.md`](/codex/05-infrastructure/launcher-script-ssot.md).

### **Phase-3 sub-todos surfaced by (a)**

1. Every CCXT-routed venue (Bitget / Bitfinex / Kraken / Upbit / etc.) needs an explicit **poll fallback** in the live
   cascade — REST snapshot every `min(15s, venue_rate_limit_window)` so the `CANDLE_BOUNDARY_CROSSED` event still fires
   at 15s aligned boundaries even when WS is unavailable.
2. CloudFront-fronted venues (Lighter / Pacifica) need **per-VM IP-rotation hooks** so a 429 storm triggers a relaunch
   on a fresh external IP rather than blocking the cascade.
3. Singleton-lock launchers (sports forward-poll / prediction-backfill) DO NOT compose with multi-VM parallelism;
   live-pipeline must run a single VM per (asset_group=sports, source) and tolerate the per-source coverage lag —
   explicit acceptance criterion.

## (b) GCS write-site migration status (writegate Phase 2 propagation)

### MTDS

`record_captured` / `record_empty` / `record_failed` calls observed across **20 files** (per
`rg -c "record_captured\(|record_empty\(|record_failed\(|record_expected_empty\(" market_tick_data_service/`):

- `engine/orchestrator.py` (11) — primary write coordinator
- `cli/handlers/{evm_defi,solana_defi,perp_funding,gas_fee,oracle_prices,lending_indices,lst_rates,governance_events,bridge_events,liquidations,mev_events,vault_share_price,dex_pools,dex_swaps,liquidation_events,eigenlayer_rewards,staking_yields}_handler.py`
  (3-9 each)
- `cli/handlers/_defi_manifest.py` (6) — DeFi manifest helper
- `scripts/rebuild_prediction_manifest.py` (2) — script-only, scope=script

**Verdict**: MTDS write-paths are ALL ManifestWriter-routed. No raw `to_parquet(` outside test fixtures +
`engine/mock_data_provider.py`. Phase 2 writegate migration appears complete.

### MDPS

ManifestWriter callsites observed in:

- `market_data_processing_service/app/core/canonical_writer.py` (2) — only PROD callsite

**Other write paths** (raw `to_parquet` / `pq.write_table`) observed in:

- `engine/mock_data_provider.py` (test/mock; scope=mock)
- `cli/handlers/process_handler.py`, `cli/main.py` — orchestration code; route through `canonical_writer` per the
  writegate plan
- `app/core/{cloud_data_provider,candle_processing_service,orchestration_writer,orchestration_base, data_sink,dependency_checker,orchestration_scanner,output_writer_service,live_workers, orchestration_scheduling,data_source,storage_dispatch_worker,candle_write_mixin, polars_candle_engine}.py`
  — verify each routes through `canonical_writer.record_captured`.

**Phase-3 sub-todo**: spot-check each of the 14 MDPS `app/core/*.py` write-path files for direct GCS writes that bypass
`canonical_writer` (writegate plan flagged this as Phase 2.B residual; current state per memory is "ALL via
record_captured" but verify before live cascade — silent placeholder risk per the 2026-05-05 1440-NaN-bar incident).

### features-\* (per-repo per-record-method count)

| Repo                          | record_captured count                                | Notes                                                                                                     |
| ----------------------------- | ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| **features-calendar**         | 2 (orchestrator)                                     | Single PROD callsite; mock_data_provider + seed_mock_data scripts skip                                    |
| **features-cross-instrument** | 1 (paired_dispatch)                                  | Single PROD callsite                                                                                      |
| **features-sports**           | 8+ (cli/handlers/batch_handler) + reconciler scripts | Many call sites, all migrated                                                                             |
| **features-onchain**          | (calls inside `feature_writer.py`) — verify          | Phase 2 scan needed; `feature_writer.py` is the single write surface                                      |
| **features-volatility**       | feature_writer + orchestration_service               | Single write surface; verify ManifestWriter routing                                                       |
| **features-delta-one**        | feature_writer                                       | Single write surface; verify ManifestWriter routing                                                       |
| **features-multi-timeframe**  | (no record_captured grep hits — verify)              | **POTENTIAL GAP**: no ManifestWriter callsite found in PROD code; check post-features-consolidation phase |
| **features-commodity**        | (no record_captured grep hits — verify)              | **POTENTIAL GAP**: same shape as multi-timeframe; check                                                   |

**Phase-3 sub-todo**: features-multi-timeframe + features-commodity have NO `record_captured` grep hits in PROD code
(only `engine/mock_data_provider.py` + `scripts/seed_mock_data.py`). Either (i) they don't write parquet at all (compute
→ broadcast only), (ii) they write via a delegate (features-service-base?), or (iii) they pre-date writegate Phase 2 and
never migrated. Resolve during Phase 0.5 (post-features-consolidation gate from `features_repo_consolidation_2026_05_08`
Phase 7) — once 8 repos collapse into one `features-service`, the write-path table simplifies to a single
`feature_writer.py`.

### instruments-service

ManifestWriter callsites observed in instruments-service production code (per `rg`); explicit inventory deferred to
instruments-service-side audit per `instruments_live_master_2026_05_08` plan.

## (c) MTDS RSS-pause + ParallelPerSymbolRunner integration status

**Per memory `project_mtds_parallelization_fix_2026_05_07`**: ParallelPerSymbolRunner shipped 2026-05-07 at UTL
`streaming/parallel_per_symbol_runner.py` (374 LOC) + 12 unit tests; MTDS Tardis adapter swapped to per-symbol fan-out.
RSS-pause integration was PENDING at 2026-05-07 evening.

### As-of 2026-05-08 verify

`market_tick_data_service/cli/main.py` lines 17 / 81 / 103-128 / 374-378 / 418:

```python
from unified_trading_library import (
    ResourceProfiler,
    ResourceSample,
    ...
)

def _on_memory_warning(sample: ResourceSample) -> None:
    """Inline ``on_memory_warning`` callback that flushes the manifest writer."""
    ...

def _start_resource_profiler() -> ResourceProfiler:
    """Start the process-wide ResourceProfiler wired into the Tardis pipeline.

    ParallelPerSymbolRunner instances inside the Tardis adapter
    can self-register their ``on_memory_warning`` pause hook via the
    profiler's public accessor; under simultaneous high
    RAM both callbacks fire (the inline ``_on_memory_warning`` here flushes
    ...
    """
    profiler = ResourceProfiler(
        ...,
        on_memory_warning=_on_memory_warning,
        ...
    )
```

**Plus** unit tests `tests/unit/test_memory_warning_callback.py` + `tests/unit/test_tardis_resource_profiler_wiring.py`
exercise the active-profiler accessor + ParallelPerSymbolRunner pause-hook self-registration.

**Verdict**: **RSS-pause integration is WIRED** as-of 2026-05-08. Phase 3 inherits a working ParallelPerSymbolRunner +
RSS-pause cascade; no new sub-todo here. Memory entry `project_mtds_parallelization_fix_2026_05_07` is now stale on the
"RSS-pause PENDING" point — to be flagged at next memory sweep but doesn't block live-pipeline work.

## (d) Existing event names per service (Phase 1 NEW-vs-EXISTING delta)

`log_event("…")` callsites per repo (sample of unique upper-case event names):

| Service                            | Existing events (top-level by frequency)                                                                                                                                                                                                               |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **market-tick-data-service**       | `TEST_EVENT_INTEGRATION` (test only — actual progress events come from base_adapter via UTL run_lifecycle / ServiceBootstrap)                                                                                                                          |
| **market-data-processing-service** | `DATA_INGESTION_{STARTED,COMPLETED}` · `LIVE_CYCLE_STARTED` · `LIVE_MODE_{STARTED,STOPPED,FAILED}` · `PROCESSING_{STARTED,COMPLETED}` · `TIMESTAMP_VALIDATION_{STARTED,COMPLETED}` · `VALIDATION_{STARTED,COMPLETED}` · `DEPLOYMENT_FAILED` · `FAILED` |
| **instruments-service**            | `STARTED` · `STOPPED` · `PROCESSING_{STARTED,COMPLETED,FAILED}` · `VALIDATION_FAILED` · `WRITE_FAILED` · `ADAPTER_FETCH_ANOMALY` · `AGGREGATE_LEGACY_ES_OPT_FINISHED` · `AGGREGATE_PROCESSED_OPTIONS_FINISHED`                                         |
| **features-calendar**              | `STARTED` · `STOPPED` · `DATA_BROADCAST` · `TEST_EVENT` · `EVENT_NAME` (placeholder)                                                                                                                                                                   |
| **features-commodity**             | `STARTED` · `STOPPED` · `DATA_INGESTION_{STARTED,COMPLETED}` · `PERSISTENCE_{STARTED,COMPLETED}` · `PROCESSING_STARTED` · `FAILED`                                                                                                                     |
| **features-cross-instrument**      | `STOPPED` · `DATA_BROADCAST` · `PERSISTENCE_STARTED` · `REGIME_DETECTION_{STARTED,COMPLETED}` · `VALIDATION_{STARTED,COMPLETED}` · `FAILED`                                                                                                            |
| **features-delta-one**             | `BUFFER_LOADING_{STARTED,COMPLETED}` · `BUFFER_VALIDATION_{STARTED,COMPLETED}` · `PROCESSING_STARTED` · `VALIDATION_{STARTED,COMPLETED}` · `EVENT_NAME` (placeholder) · `FAILED`                                                                       |
| **features-multi-timeframe**       | `STARTED` · `STOPPED` · `DATA_BROADCAST` · `PROCESSING_COMPLETED` · `FAILED`                                                                                                                                                                           |
| **features-onchain**               | `STARTED` · `STOPPED` · `API_CALL_{STARTED,COMPLETED}` · `DATA_BROADCAST`                                                                                                                                                                              |
| **features-sports**                | `STARTED` · `FAILED`                                                                                                                                                                                                                                   |
| **features-volatility**            | `STOPPED` · `DATA_BROADCAST` · `DATA_INGESTION_{STARTED,COMPLETED}` · `PERSISTENCE_{STARTED,COMPLETED}` · `PROCESSING_{STARTED,COMPLETED}` · `VALIDATION_{STARTED,COMPLETED}` · `FAILED`                                                               |

**Plus workspace-wide via UTL ServiceBootstrap**: `STARTED` / `STOPPED` / `FAILED` are emitted automatically per
CLAUDE.md "ServiceBootstrap" rule (services do NOT emit these manually).

### Phase 1 NEW events (per plan body)

Per the live-pipeline plan Phase 1 spec, three NEW events are introduced:

1. **`CANDLE_BOUNDARY_CROSSED`** — published by MTDS at 15s aligned boundaries.
2. **`CANDLE_COMPUTED`** — published by MDPS after candle aggregation.
3. **`INSTRUMENT_CACHE_REFRESH_TRIGGER`** — published by instruments-service after catalog refresh.

**As-of 2026-05-08 verify**: All three Pydantic event types ALREADY shipped at
`unified-api-contracts/unified_api_contracts/events/streaming.py` (commit `7d891f69`) per Tab-2 sub-agent A (Phase 1
work). Tests live at `unified-api-contracts/tests/unit/test_streaming_events.py`. The actual `log_event(...)` callsites
in MTDS / MDPS / instruments-service that fire these events are Phase 3 / Phase 5 / Phase 10 work.

### Phase-1 sub-todo (already shipped)

`unified_api_contracts/events/streaming.py` exists. Phase 1 in the plan can flip checkbox `[ ]` → `[x]` once Tab-2 main
confirms the as-shipped shape matches the plan body — verify the three event classes match the spec at
`live_pipeline_mtds_mdps_features_2026_05_08.md` lines 137-182.

## (e) `ServiceEmissionPolicy` consumer mapping

Per `rg -ln "ServiceEmissionPolicy|emission_publisher|publish_with_policy|EmissionLifecycleEvent|EmissionDecision"`:

| Repo / file                                                                                     | Role                                                                                                                                              |
| ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `unified-api-contracts/unified_api_contracts/canonical/crosscutting/service_emission_policy.py` | **SSOT** — UAC@58c3b61 slice (a) (4-member StrEnum + 19-row seed dict + EmissionLifecycleEvent + EmissionDecision dataclass + 4 helper functions) |
| `unified-api-contracts/tests/unit/test_service_emission_policy.py`                              | UAC unit tests (48 tests)                                                                                                                         |
| `unified-trading-library/unified_trading_library/emission_publisher.py`                         | UTL@1a7e1d4b helper (`publish_with_policy()` returns frozen `EmissionDecision`)                                                                   |
| `unified-trading-library/tests/events/test_emission_publisher.py`                               | UTL tests                                                                                                                                         |
| `unified-api-contracts/unified_api_contracts/events/streaming.py`                               | UAC streaming events — `CandleComputedEvent.emission_policy` field references the enum                                                            |
| `unified-api-contracts/tests/unit/test_streaming_events.py`                                     | streaming event tests                                                                                                                             |

### Phase-8 sub-todo (consumer wiring)

**No consumer wiring exists yet** outside the SSOT + tests. Phase 8 of the live-pipeline plan owns the wire-in.
Consumer-class mapping per the live-pipeline plan body (the row-by-row table to ship):

| Consumer service                     | Output `data_type`(s)                                                         | Recommended policy                                                                   | Wire-in surface (file:line)                                                                     |
| ------------------------------------ | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------- |
| **market-data-processing-service**   | `ohlcv_15s` · `ohlcv_1m` · `ohlcv_5m` · `ohlcv_15m` · `ohlcv_1h` · `ohlcv_1d` | `STRICT_FAIL` for current bar; `PUBLISHED_DEGRADED` for trailing-window aggregations | `app/core/canonical_writer.py` (call `publish_with_policy()` instead of bare `record_captured`) |
| **features-volatility**              | rolling realised vol, implied vol skew                                        | `PUBLISHED_DEGRADED` (rolling windows tolerate gaps)                                 | `feature_writer.py`                                                                             |
| **features-onchain**                 | LST yields, gas, TVL                                                          | `STRICT_FAIL` for current snapshots; `PUBLISHED_DEGRADED` for moving averages        | `feature_writer.py`                                                                             |
| **features-cross-instrument**        | volatility smile, funding-vs-spot basis                                       | `STRICT_FAIL` (cross-instrument requires per-leg synchrony)                          | `feature_writer.py`                                                                             |
| **features-multi-timeframe**         | multi-tf cascades                                                             | `PUBLISHED_DEGRADED` (cascades tolerate per-tf gaps)                                 | (no `record_captured` grep hit — see (b) sub-todo)                                              |
| **features-delta-one**               | delta-one features                                                            | `STRICT_FAIL` for current; `PUBLISHED_DEGRADED` for rolling                          | `feature_writer.py`                                                                             |
| **features-commodity**               | commodity features                                                            | `PUBLISHED_DEGRADED`                                                                 | (no `record_captured` grep hit — see (b) sub-todo)                                              |
| **features-calendar**                | calendar events / corp actions                                                | `PUBLISHED_OK` (event data, not gap-sensitive)                                       | `engine/calendar_orchestrator.py`                                                               |
| **features-sports**                  | sports features                                                               | `PUBLISHED_DEGRADED` (per-fixture-bundle gaps tolerated)                             | `cli/handlers/batch_handler.py`                                                                 |
| **strategy-service**                 | trade signals                                                                 | `STRICT_FAIL` (signals on stale data are alpha-loss)                                 | TBD per strategy-service archetype audit                                                        |
| **position-balance-monitor-service** | position state                                                                | `STRICT_FAIL` (position drift on stale data is risk-loss)                            | TBD                                                                                             |
| **risk-and-exposure-service**        | risk metrics                                                                  | `STRICT_FAIL`                                                                        | TBD                                                                                             |
| **pnl-attribution-service**          | P&L                                                                           | `BLOCK_CRITICAL` (P&L attribution on incomplete data is regulatory-loss)             | TBD                                                                                             |

Phase 8 will codify this table per service-team approval.

## (f) `ApiKeyReloader` / `start_domain_config_reloaders` callsite inventory (Phase 10 cache-delta hot-reload pattern shape source)

### `ApiKeyReloader` direct usage

`rg -ln "ApiKeyReloader\("`:

- `strategy-service/strategy_service/signal_broadcast/credentials.py` — counterparty signal broadcast (per CLAUDE.md
  "Signal Leasing" rule)
- `instruments-service/scripts/fill_missing_player_stats.py` (script scope)
- `instruments-service/instruments_service/cli/instruments_handler.py` — reference data fetchers
- `features-onchain-service/features_onchain_service/collectors/lst_rewards_bootstrap.py` — onchain key rotation
- `market-tick-data-service/market_tick_data_service/cli/handlers/tick_data_handler.py` — MTDS handler

### `start_domain_config_reloaders` callsite inventory

| Service                               | File                                                                                      |
| ------------------------------------- | ----------------------------------------------------------------------------------------- |
| **features-volatility-service**       | `features_volatility_service/config_reloaders.py`                                         |
| **features-commodity-service**        | `features_commodity_service/config_reloaders.py`                                          |
| **features-multi-timeframe-service**  | `features_multi_timeframe_service/config_reloaders.py`                                    |
| **features-delta-one-service**        | `features_delta_one_service/config_reloaders.py`                                          |
| **features-cross-instrument-service** | `features_cross_instrument_service/config_reloaders.py`                                   |
| **features-onchain-service**          | `features_onchain_service/config_reloaders.py`                                            |
| **features-sports-service**           | `features_sports_service/config_reloaders.py`                                             |
| **features-calendar-service**         | `features_calendar_service/config_reloaders.py`                                           |
| **market-data-processing-service**    | `market_data_processing_service/config_reloaders.py`                                      |
| **alerting-service**                  | `alerting_service/config_reloaders.py` + `alerting_service/cli/handlers/alert_handler.py` |
| **position-balance-monitor-service**  | `position_balance_monitor_service/config_reloaders.py`                                    |
| **pnl-attribution-service**           | `pnl_attribution_service/config_reloaders.py`                                             |
| **client-reporting-api**              | `client_reporting_api/config_reloaders.py`                                                |
| **trading-agent-service**             | `trading_agent_service/config_reloaders.py`                                               |
| **batch-live-reconciliation-service** | `batch_live_reconciliation_service/config_reloaders.py`                                   |
| **ml-inference-service**              | `ml_inference_service/config_reloaders.py`                                                |
| **archive/execution-results-api**     | (archived — skip)                                                                         |

Pattern docs live in
`unified-trading-library/unified_trading_library/{api_key_reloader.py,config_reloader.py,lifecycle_reloader.py,domain_config_reloader.py}`
(117 + 263 + 165 + 299 LOC respectively).

### Phase-10 sub-todo (cache-delta hot-reload mirroring shape)

Phase 10's `InstrumentCacheRefreshTriggerEvent` consumers (MTDS / MDPS / features-service) follow this same pattern:

1. instruments-service publishes the event (already shipped per (d) above: `unified_api_contracts/events/streaming.py`).
2. Each downstream service registers a consumer that:
   - Reads the event via UTL `StreamConsumerGroup` (ships in `unified_trading_library/streaming/redis_stream.py`).
   - Diffs incoming catalog row count vs in-process cache (using `row_count_added_since_last` /
     `row_count_removed_since_last` fields).
   - If delta > 0, fetches the new catalog from instruments-service and updates the in-process cache via the existing
     `start_domain_config_reloaders(...)` callback shape — NO new code path, just a new trigger source (event-driven
     instead of timer-driven).
3. The 16-service callsite list above maps 1:1 to consumer wire-in surfaces. Each service's `config_reloaders.py` gets a
   sibling `instrument_cache_reloader.py` (or extends the existing reloader) per the pattern doc at
   [`/codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md`](/codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md).

**Reference pattern doc**: `unified_trading_library/api_key_reloader.py` shape — periodic reloader with
`RefreshCallback = Callable[[dict[str, str], set[str]], None]` for the new-keys + removed-keys diff. Phase 10 mirrors
this shape with `InstrumentCacheRefreshCallback` (new-instruments + removed-instruments).

## (g) Existing Redis dependency in the workspace (Phase 2A dep-add baseline)

### Redis usage in PRODUCTION code

`rg -lN "redis\." --type py --glob '!.venv*' --glob '!tests/*'`:

| File                                                                            | Purpose                                                                   |
| ------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| **`unified-trading-library/unified_trading_library/streaming/redis_stream.py`** | NEW (Phase 2A) — StreamPublisher + StreamConsumerGroup wrappers (291 LOC) |
| **`unified-trading-library/unified_trading_library/streaming/replay.py`**       | NEW (Phase 2A) — ReplayWatermarkKV + ReplayPublisher (247 LOC)            |
| `unified-trading-library/unified_trading_library/cloud_interface/cache.py`      | UTL cache utility (existing, redis-backed cache helper)                   |
| `deployment-api/deployment_api/utils/cache.py`                                  | deployment-api request-cache (in-memory; no live Redis dep)               |
| `archive/unified-cloud-interface/unified_cloud_interface/cache.py`              | archived (skip)                                                           |

### `redis>=5.0` registration in `pyproject.toml`

| Repo                           | `redis>=5.0` declared?                                                                                                                                                                       |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **unified-trading-library**    | **YES** — `"redis>=5.0.0,<6.0.0"` + `"fakeredis>=2.20.0,<3.0.0"` (test fixture). Comment notes "Quota broker: Redis-backed rate coordination; exercised in integration/SIT with live Redis." |
| unified-api-contracts          | NO — UAC doesn't depend on redis (correct; only event-shape definitions live here)                                                                                                           |
| market-tick-data-service       | NO direct dep — inherits via UTL                                                                                                                                                             |
| market-data-processing-service | NO direct dep — inherits via UTL                                                                                                                                                             |
| strategy-service               | NO direct dep — inherits via UTL                                                                                                                                                             |
| alerting-service               | NO direct dep — inherits via UTL                                                                                                                                                             |

### Verdict

**Phase 2A's `redis>=5.0` dep is ALREADY shipped in UTL** — Streams require ≥5 and the dep is declared. Phase 2A
consumers that need the dep at runtime get it transitively via UTL's `pyproject.toml` (no per-consumer dep adds
required). No sub-todo here.

`fakeredis>=2.20.0,<3.0.0` is also declared, supporting the Phase 2 unit-test fixtures already in place
(`tests/unit/streaming/test_*.py` — verify list during Tab-2 sub-agent B's report-back).

## Cross-cutting findings (Phase 3-13 sub-todos surfaced from this audit)

The following findings are NOT pre-existing plan todos but were surfaced by the audit. They get folded into Phase 3 /
Phase 5 / Phase 8 / Phase 10 of the live-pipeline plan:

1. **(a) sub-todo 1** — Poll-fallback for CCXT-routed venues at 15s aligned boundaries. Phase 3 ownership (MTDS).
2. **(a) sub-todo 2** — IP-rotation hooks for CloudFront-fronted venues. Phase 3 ownership (MTDS launcher work in
   `deployment-service/scripts/vm/`).
3. **(a) sub-todo 3** — Singleton-lock launcher constraint accepted as live-pipeline limit for sports / prediction.
   Phase 13 launcher work.
4. **(b) sub-todo** — features-multi-timeframe + features-commodity have no `record_captured` PROD callsite. Verify
   post-features-consolidation gate (Phase 0.5 dependency from `features_repo_consolidation_2026_05_08`).
5. **(b) sub-todo** — Spot-check 14 MDPS `app/core/*.py` write-path files for any direct GCS write bypassing
   `canonical_writer`. Phase 5 ownership (MDPS).
6. **(c)** — Memory entry `project_mtds_parallelization_fix_2026_05_07` "RSS-pause PENDING" is stale; flag for next
   memory sweep. RSS-pause is wired as-of 2026-05-08.
7. **(d)** — Phase 1 (UAC streaming events) already shipped at commit `7d891f69`; checkbox flips on Tab-2 main
   verification of as-shipped shape vs plan body.
8. **(e)** — Phase 8 consumer-class mapping table (above) is the row-by-row wire-in surface. Each row is a Phase 8
   sub-todo.
9. **(f)** — Phase 10 cache-delta hot-reload mirrors the `ApiKeyReloader` shape; 16 callsite surfaces from the inventory
   above are the wire-in targets.
10. **(g)** — Phase 2A's `redis>=5.0` dep is shipped; no per-consumer dep work required.

## What I CAN'T verify from this audit

- **Per-venue rate-limit numerics** — actual req/sec and connection-count caps are venue-specific and need to be tested
  empirically during Phase 3 smoke. The audit only confirms WHICH adapters have per-key throttling logic, not the
  numeric limits.
- **MDPS write-path completeness** — 14 `app/core/*.py` files mention parquet write primitives; whether each routes
  through `canonical_writer.record_captured` requires per-file inspection during Phase 5.
- **features-multi-timeframe / features-commodity write paths** — POST-features-consolidation gate
  (`features_repo_consolidation_2026_05_08` Phase 7) collapses 8 repos into one consolidated `features-service`; the gap
  audit there is more efficient than auditing each pre-consolidation repo separately.
- **Live-pipeline empirical latency** — Redis Stream latency benchmarks per asset_group are Phase 3-6 deliverables, not
  Phase 0 audit material.

## Compose with

- `live_pipeline_mtds_mdps_features_2026_05_08.md` — parent plan; this doc is its Phase 0 artifact.
- `gcs_migration_bundle_pipeline_mode_2026_05_08.md` — owns `pipeline_mode` enum + manifest column extension.
- `features_repo_consolidation_2026_05_08.md` — Phase 7 prerequisite for live-pipeline Phase 5.
- `writegate_honest_coverage_endtoend_2026_05_06.md` — Phase 2 wrote ManifestWriter migration this audit confirms.
- `alerting_service_live_rules_2026_05_07.md` — Phase 9 consumes alert tier table from this plan.
- `instruments_live_master_2026_05_08.md` — owns instruments-service's Phase 10 publisher work.
- `master_to_live_defi_2026_05_23.md` — May-23 cutover master; Group F items 21+22 pivot on this plan's success.
