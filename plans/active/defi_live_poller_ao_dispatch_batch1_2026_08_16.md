---
doc_type: plan
title: DeFi live-poller Tranche 0 — connector-pattern extraction
summary: >-
  First AO-dispatch batch from defi_live_poller_phased_build_2026_08_15.md, operator-approved
  2026-08-16 (dispatch cadence: one batch per tranche, mirroring sports_satellite_ao_dispatch).
  Extracts the two proven live-connector patterns (subgraph-polling, on-chain-liquidation) into
  reusable config-driven base classes, the prerequisite that unlocks Tranches 1-4 (39 venues) at
  N-config-rows-not-N-hand-written-files cost.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, live-capture, connector-pattern]
related:
  [/plans/active/defi_live_poller_phased_build_2026_08_15.md]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: backend_engineer
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 4, 2026-08-16 (dispatch cadence ruling)"
locked_by:
archive_exempt: true
context_scope:
  [
    /plans/active/defi_live_poller_phased_build_2026_08_15.md,
    market-tick-data-service/market_tick_data_service/live/connectors/dex_swap_uniswap_v3_ws.py,
    market-tick-data-service/market_tick_data_service/live/connectors/aave_liquidations_ethereum_ws.py,
  ]
locked_since:
resolved_by:
---

# DeFi live-poller Tranche 0 — connector-pattern extraction

## Todos

- [x] ✅ [DATA] P2. Extract `SubgraphPollingConnector`, a config-driven `WSFeedConnector` parameterized by
      `(protocol, chain, subgraph_id, swap_query_template, pool_query_template)`, generalizing
      `dex_swap_uniswap_v3_ws.py`'s implementation. DoD: `UNISWAP_V3-ETHEREUM` re-implemented on top of the new base
      class with zero behavior change (regression: existing unit tests still pass unmodified). (repo:
      market-tick-data-service) — market-tick-data-service@5ef71f1084. Extracted `SubgraphPollingConnector` into
      `_subgraph_polling_connector.py`; `UniswapV3DexSwapWSFeedConnector` now subclasses it with
      protocol="uniswap_v3"/chain/queries/parsers. All 34 existing unit tests
      (`test_dex_swap_uniswap_v3_ws_connector.py` + `test_aave_liquidations_ws_connector.py`) pass unmodified;
      basedpyright clean (no blanket file-level suppression on the new module).
- [x] ✅ [DATA] P2. Extract `OnChainLiquidationPoller`, a config-driven `WSFeedConnector` parameterized by
      `(protocol, chain, rpc_resolver_key, contract_address, event_topic, log_parser)`, generalizing
      `aave_liquidations_ethereum_ws.py`'s implementation. DoD: `AAVE_V3-ETHEREUM` re-implemented on top of the new
      base class with zero behavior change. (repo: market-tick-data-service) —
      market-tick-data-service@0eb87e61f9. Extracted `OnChainLiquidationPoller` into
      `_onchain_liquidation_poller.py`; `AaveV3EthereumWSFeedConnector` now subclasses it with
      protocol="aave_v3"/chain/contract/topic/log_parser config only — connect/subscribe/unsubscribe/
      pop_reconnect_flag/stream/close are inherited, not redefined. `_parse_log_to_tick` unchanged.
      Existing unit tests (`test_aave_liquidations_ws_connector.py`) pass unmodified; Pass-1
      quality-gates.sh green on 0eb87e61 (basedpyright clean, no new suppressions).

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 4, operator ruling on dispatch cadence)**: extracted from
  `defi_live_poller_phased_build_2026_08_15.md` Tranche 0. Tranches 1-4 (39 venues) stay in the parent plan pending
  the TVL-snapshot re-verification of tranche ordering — do not extract those until this batch's base classes land
  and that ordering is confirmed against real DefiLlama data.
**context-scout 2026-08-17**: populated/refreshed context_scope (3 entries)
- **2026-08-17 (AO worker, slot 11)**: todo 2 shipped — `OnChainLiquidationPoller` extracted,
  `AAVE_V3-ETHEREUM` re-implemented on top with zero behavior change
  (market-tick-data-service@0eb87e61f9). Both Tranche-0 todos now complete — plan archived this
  turn per the completion-and-archival hard rule.
