---
doc_type: plan
title: defi-e2e-pipeline-completion
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-28'
overview: Complete DeFi pipeline E2E testing across all 7 layers (instruments → tick data → processing → features → strategy → execution → monitoring). Fix remaining data issues, expand venue coverage from 3 to 12, test all 15 DeFi strategies including Solana/BTC/L2/cross-chain, and wire strategy→execution with Tenderly pre-simulation.
type: code
epic: epic-code-completion
locked_by: live-defi-rollout
locked_since: 2026-03-28
completion_gates: {code: C4, deployment: none, business: B1}
repo_gates:
- {repo: market-data-processing-service, code: C0, deployment: none, business: none}
- {repo: features-onchain-service, code: C0, deployment: none, business: none}
- {repo: strategy-service, code: C0, deployment: none, business: none}
- {repo: execution-service, code: C0, deployment: none, business: none}
- {repo: alerting-service, code: C0, deployment: none, business: none}
- {repo: unified-market-interface, code: C0, deployment: none, business: none}
- {repo: unified-trading-library, code: C0, deployment: none, business: none}
- {repo: unified-api-contracts, code: C0, deployment: none, business: none}
- {repo: market-tick-data-service, code: C0, deployment: none, business: none}
- {repo: e2e-testing, code: C0, deployment: none, business: none}
depends_on: [multichain-defi-expansion]
context: "## Pipeline Status (as of 2026-03-28)\n\nL2 (MTDS) → L3 (MDPS) → L4 (features-onchain) confirmed working end-to-end with real Aave data.\n167,530 candles, 17,280 lending rate features written to GCS.\n3/12 venues producing data (Aave V3, Uniswap V2, V4). 9 venues need MTDS re-run.\n\n### Confirmed Working\n- MTDS: 3 venues to GCS (Aave V3, Uniswap V2, V4)\n- MDPS: 24/24 data_type×venue combos, LOCF adapter for lending rates\n- features-onchain: lending_rates → GCS (17,280 rows)\n- Timestamp midnight boundary fix (UTL)\n- String timestamp detection (MDPS base_adapter)\n- Venue name mismatch fix (MDPS process_handler)\n\n### 15 DeFi Strategies (from codex/09-strategy/defi/)\nETH: aave-lending, basis-trade, staked-basis, recursive-staked-basis, market-making-lp,\n     cross-chain-yield-arb, cross-chain-sor-rebalancing, multi-chain-lending-yield\nBTC: btc-basis-trade, btc-lending-yield\nSOL: sol-basis-trade, sol-staked-basis, sol-concentrated-lp, sol-lending-yield\nL2:  l2-basis-trade\n\
  \n### Execution DAG\n```\nPhase 1 (MDPS hardening) ──┐\nPhase 2 (Venue expansion) ─┤──→ Phase 4 (Strategy) ──→ Phase 5 (Execution) ──→ Phase 6 (Monitoring)\nPhase 3 (Infra)  ──────────┘\n```\n"
todos:
- {id: mdps-data-type-per-venue, content: "- [x] [AGENT] P0. MDPS: filter data_types per-venue by reading `data_type` column from raw parquet.\n  Only run adapters for data types that exist in the file (e.g. Aave: rate_indices/utilization/oracle_prices/risk_params,\n  Uniswap: swaps/liquidity). Zero-config, self-describing. Prevents wasteful no-op adapter runs.\n", status: done, note: 'Worker filters tick_data by data_type column. Adapters declare related_data_types. 24/24 combos pass, correct per-venue data_type filtering.'}
- {id: mdps-venue-name-alignment, content: "- [ ] [AGENT] P1. UAC `VENUES_BY_CATEGORY` uses old names (AAVE_V3_ETH, UNISWAP_V2-ETH) while GCS paths use canonical\n  (AAVE_V3-ETHEREUM, UNISWAP_V2-ETHEREUM). Align UAC venue names to canonical PROTOCOL-CHAIN format. Update all consumers.\n", status: pending}
- {id: mdps-manifest-writer, content: "- [ ] [AGENT] P1. Wire ManifestWriter to write data availability catalogue after MDPS processing.\n  Downstream services (features-onchain, strategy) should discover available data from manifest, not list_blobs scanning.\n", status: pending}
- {id: mdps-aave-graph-bulk-perf, content: "- [ ] [AGENT] P2. Verify Aave Graph bulk query optimization (reserveParamsHistoryItems) performance vs per-block RPC.\n  Previous session added bulk query but didn't verify. Target: <2min for 51 instruments (was 11min via RPC).\n", status: pending}
- {id: venue-expansion-mtds, content: "- [ ] [AGENT] P0. Re-run MTDS for all 12 DeFi venues: Aave V3, Uniswap V2/V3/V4, Curve, Balancer, Morpho, Euler,\n  Fluid, Lido, EtherFi, Ethena. Fix remaining adapter issues (Curve liquidity #031, Fluid ABI #032).\n  Verify data in GCS for all venues.\n", status: pending}
- {id: venue-expansion-mdps, content: "- [ ] [AGENT] P0. Run MDPS for all 12 venues. Verify candle output per venue/data_type. Document which\n  venue+data_type combinations produce real data vs empty (e.g. Uniswap has no oracle_prices).\n", status: pending}
- {id: venue-expansion-features, content: "- [ ] [AGENT] P1. Run features-onchain for ALL feature groups (not just lending_rates): macro_sentiment,\n  lending_rates, lst_yields, aave_utilization, aave_risk_params, protocol_rewards, flash_loan_availability.\n  Verify output in GCS.\n", status: pending}
- {id: infra-api-key-centralization, content: "- [ ] [AGENT] P1. Centralize API key management: remove 10 duplicated `_ensure_alchemy_client` from DeFi adapters.\n  Use ApiKeyReloader at service level (MTDS/MDPS). Adapters receive keys via factory params.\n  See issue #037 in e2e-testing/docs/defi/issues.md.\n", status: pending}
- {id: infra-shard-error-aggregation, content: "- [ ] [AGENT] P2. UTL: shared shard-level error/warning aggregation framework. Per-(venue, instrument, data_type) counters,\n  end-of-day summary, structured error details. Replace ad-hoc per-service implementations.\n  See issue #019/#020 in e2e-testing/docs/defi/issues.md.\n", status: pending}
- {id: strategy-defi-signal-gen, content: "- [x] [AGENT] P0. Test strategy-service DeFiBaseStrategy with real features from GCS.\n  Start with aave-lending strategy (simplest: supply USDT, earn APY).\n  Verify: signal generation, position recovery (is_deployed), batch_handler signal-only mode.\n  Strategy reads features from features-onchain GCS output, generates ENTER/EXIT/HOLD signals.\n", status: done, note: 'GCSFeatureProvider created. 17,280 features loaded. DEPLOY signals generated at 1% APY threshold. Real Aave supply APY=1.88%.'}
- {id: strategy-multi-defi, content: "- [ ] [AGENT] P1. Test remaining ETH DeFi strategies: basis-trade, staked-basis, recursive-staked-basis.\n  Each requires different feature groups and instruments. Verify signal correctness against strategy codex docs.\n", status: pending}
- {id: strategy-multichain, content: "- [ ] [AGENT] P2. Test multi-chain strategies: sol-basis-trade, sol-lending-yield, btc-basis-trade, btc-lending-yield,\n  l2-basis-trade. Requires multi-chain data from Phase 2 + multichain-defi-expansion plan.\n  Verify chain-aware routing, gas cost models, cross-chain SOR.\n", status: pending}
- {id: execution-tenderly-presim, content: "- [ ] [AGENT] P0. Test execution-service DeFi adapter with Tenderly pre-simulation.\n  Aave V3 supply/withdraw on Tenderly fork. Verify: tx simulation, gas estimation, error classification\n  (13 DefiErrorCode values), FILL_COMPLETED event emission.\n", status: pending, note: 'Partial: Tenderly VNet creation, wallet funding (100ETH/10K USDC/DAI), FlashLoanReceiver deployment all work. Supply tx reverts — likely approve() issue (#061).'}
- {id: execution-signal-to-fill, content: "- [ ] [AGENT] P0. Wire strategy signals → execution-service. Test full flow:\n  strategy generates ENTER signal → execution receives via Redis/Pub/Sub → Tenderly pre-sim → execute on fork →\n  FILL_COMPLETED event → position-balance-monitor updates.\n", status: pending}
- {id: execution-multichain, content: "- [ ] [AGENT] P2. Test multi-chain execution: Solana (SPL token operations), BTC-on-ETH (WBTC/cbBTC wrapping),\n  L2 bridging (cross-chain SOR). Requires multichain-defi-expansion plan completion.\n", status: pending}
- {id: alerting-defi-rules, content: "- [ ] [AGENT] P0. Test alerting-service DeFi rules: check_tx_simulation (P1), check_position_liquidated (P0),\n  health_factor alerts, gas spike alerts. Verify alert emission via Pub/Sub.\n", status: pending}
- {id: alerting-defi-dashboard, content: "- [ ] [AGENT] P2. Verify DeFi alert visibility in unified-trading-system-ui (health dashboard, alert feed).\n  Check alert→UI flow: alerting-service → Pub/Sub → API gateway → WebSocket → UI.\n", status: pending}
- {id: e2e-full-pipeline-run, content: "- [ ] [AGENT] P0. Full E2E pipeline run: instruments → MTDS → MDPS → features-onchain → strategy → execution → alerting.\n  All 12 venues, aave-lending strategy end-to-end. Document results in e2e-testing/docs/defi/.\n", status: pending}
- {id: e2e-issues-doc-final, content: "- [ ] [AGENT] P1. Final update of e2e-testing/docs/defi/issues.md with all findings.\n  Update e2e-testing/docs/architecture.md with pipeline flow diagrams.\n  Create e2e-testing/docs/defi/strategy-coverage.md mapping 15 strategies → test status.\n", status: pending}
---

