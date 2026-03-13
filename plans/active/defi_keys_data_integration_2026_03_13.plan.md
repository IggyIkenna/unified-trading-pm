---
name: defi-keys-data-integration-2026-03-13
overview: >
  Consolidates all API key provisioning, VCR cassette recording, DeFi testnet data, data freshness SLAs, and production
  backfill into a single plan. 30 vendor API keys across 4 phases, VCR cassettes for all venues including 3 missing
  interface repos (audit §10 FAIL), FreshnessMonitor implementation with per-venue SLAs for 33 venues, and 5-step
  production data backfill pipeline. Milestone-gated.
type: mixed
epic: epic-data
status: active

completion_gates:
  code: C4
  deployment: D3
  business: none

repo_gates:
  - repo: unified-api-contracts
    code: C4
    deployment: none
    business: none
    readiness_note: "VCR cassettes committed here."
  - repo: unified-market-interface
    code: C4
    deployment: none
    business: none
    readiness_note: "Cassettes added (audit §10 fix)."
  - repo: unified-trade-execution-interface
    code: C4
    deployment: none
    business: none
    readiness_note: "Cassettes added (audit §10 fix)."
  - repo: unified-reference-data-interface
    code: C4
    deployment: none
    business: none
    readiness_note: "Cassettes added (audit §10 fix)."

depends_on:
  - cicd_code_rollout_master_2026_03_13
  # Blocker: Plan 1 Phase 3 (interfaces hardened) blocks Phase 2 (cassette recording).

supersedes:
  - api_keys_and_auth
  - data_availability_live_expectations_2026_03_10
  - defi_dev_testnet_data_rollout_2026_03_13
  - production_backfill_step_by_step_2026_03_10

todos:
  # ── Phase 1: SECRET PROVISIONING [HUMAN] ───────────────────────────────────
  # Exit criteria: All 30 vendor API keys in GCP Secret Manager
  # Blocker: None (can start immediately)

  - id: secrets-verify-tardis
    content: >
      - [ ] [SCRIPT] P0. Tardis API key already in Secret Manager. Verify access: run `gcloud secrets versions access
      latest --secret=tardis-api-key` and confirm non-empty response.
    status: pending

  - id: secrets-http-vendors
    content: >
      - [ ] [HUMAN] P0. Load 7 HTTP vendor API keys into GCP Secret Manager: databento-api-key, thegraph-api-key,
      alchemy-api-key, aavescan-api-key, envio-api-key, openbb-fmp-api-key, openbb-fred-api-key. All have existing
      accounts — keys just need to be stored.
    status: pending

  - id: secrets-defi-endpoints
    content: >
      - [ ] [HUMAN] P0. Load 16 DeFi endpoint credentials: TheGraph (subgraph API), Alchemy (mainnet), Defillama (public
      but rate-limited), Hyperliquid (mainnet+testnet), Aave (subgraph), Compound (subgraph), Uniswap (subgraph), Curve
      (subgraph), Balancer (subgraph), 1inch (API key), Paraswap (API key), dYdX (API key), GMX (subgraph), Synthetix
      (subgraph), Lido (subgraph), Rocket Pool (subgraph).
    status: pending

  - id: secrets-ws-vendors
    content: >
      - [ ] [HUMAN] P1. Load 3 WebSocket vendor credentials: binance-api-key+secret, deribit-client-id+secret,
      ibkr-username+password (for TWS gateway).
    status: pending

  - id: secrets-phase3-procurement
    content: >
      - [ ] [HUMAN] P2. Procure and load 8 Phase 3 vendor API keys (accounts needed): pinnacle-api-key, odds-api-key,
      api-football-key, glassnode-api-key, arkham-api-key, soccer-football-info-key, footystats-api-key,
      coinglass-api-key.
    status: pending

  - id: secrets-phase4-vendors
    content: >
      - [ ] [HUMAN] P3. Procure and load 6 Phase 4 vendor credentials: betfair-api-key+session, kalshi-api-key,
      coinbase-api-key+secret, bloxroute-auth-header, smarkets-api-key, betdaq-api-key.
    status: pending

  - id: secrets-defi-testnet
    content: >
      - [ ] [HUMAN] P1. Load DeFi testnet secrets: alchemy-api-key-testnet (Sepolia), tenderly-fork-rpc-url,
      hyperliquid-testnet-api-credentials, wallet-dev-private-key (test wallet only, never production).
    status: pending

  - id: secrets-bootstrap
    content: >
      - [ ] [HUMAN] P0. Bootstrap secrets for CI: TELEGRAM_BOT_TOKEN on 3 new repos (ml-inference-api, ml-training-api,
      trading-analytics-api), ANTHROPIC_API_KEY for SIT (system-integration-tests), GCP_SA_KEY for CI service account
      authentication.
    status: pending

  # ── Phase 2: VCR CASSETTE RECORDING ────────────────────────────────────────
  # Exit criteria: All venues have cassettes, cassette schema parity test passes
  # Blocker: Phase 1 (secrets loaded); Plan 1 Phase 3 (interfaces hardened)

  - id: cassette-tardis
    content: >
      - [ ] [AGENT] P0. Record Tardis VCR cassette. Steps: (1) configure vcr_endpoints.py entry for Tardis, (2) run
      cassette recording script with Tardis API key from SM, (3) commit cassette YAML to
      unified-api-contracts/tests/cassettes/, (4) verify `pytest tests/test_cassette_schema_parity.py` passes.
    status: pending
    depends_on: [secrets-verify-tardis]

  - id: cassette-http-vendors
    content: >
      - [ ] [AGENT] P1. Record VCR cassettes for 7 HTTP vendors: databento, thegraph, alchemy, aavescan, envio,
      openbb-fmp, openbb-fred. For each: configure vcr_endpoints.py, record, commit, verify parity.
    status: pending
    depends_on: [secrets-http-vendors]

  - id: cassette-defi-endpoints
    content: >
      - [ ] [AGENT] P1. Record VCR cassettes for 16 DeFi endpoints. Group by protocol type: Subgraph-based (TheGraph,
      Aave, Compound, Uniswap, Curve, Balancer, GMX, Synthetix, Lido, Rocket Pool), REST-based (Defillama, Hyperliquid,
      1inch, Paraswap, dYdX). For each: configure, record, commit, verify.
    status: pending
    depends_on: [secrets-defi-endpoints]

  - id: cassette-missing-interface-repos
    content: >
      - [ ] [AGENT] P0. Add VCR cassettes to 3 repos flagged in audit §10 FAIL: unified-market-interface,
      unified-trade-execution-interface, unified-reference-data-interface. Each needs at least 1 cassette per venue it
      supports. This resolves the audit FAIL.
    status: pending
    depends_on: [cassette-tardis]

  - id: cassette-ws-approach
    content: >
      - [ ] [AGENT] P2. Design and implement WebSocket cassette approach for Binance, Deribit, IBKR. Options: (a) record
      WS frames to YAML like HTTP cassettes, (b) use MockWebSocketFeed from
      `unified-market-interface/tests/fixtures/mock_ws_server.py`. Likely (b) is correct — WS cassettes are replay-only,
      not schema-parity.
    status: pending
    depends_on: [secrets-ws-vendors]

  # ── Phase 3: DATA FRESHNESS & SLAs ─────────────────────────────────────────
  # Exit criteria: FreshnessMonitor deployed, per-venue SLAs, stale data alerts fire within 60s
  # Blocker: Plan 1 Phase 3 (library tiers green)

  - id: freshness-monitor-class
    content: >
      - [ ] [AGENT] P1. Implement FreshnessMonitor base class in unified-trading-library. Interface:
      `check_freshness(venue, data_type) -> FreshnessResult` with `is_stale`, `last_update_ts`, `sla_seconds`,
      `staleness_seconds`. Per-source freshness contracts defined in unified-internal-contracts as Pydantic models.
    status: pending

  - id: freshness-venue-slas
    content: >
      - [ ] [AGENT] P1. Define per-venue SLA for all 33 venues: 9 CeFi (Binance 1s, Deribit 5s, etc.), 9 TradFi (IBKR
      30s, etc.), 14 DeFi (Hyperliquid 10s, Aave 60s, etc.), 1 Onchain Perps. SLAs stored in unified-internal-contracts
      as venue_freshness_slas.py.
    status: pending

  - id: freshness-alerting
    content: >
      - [ ] [AGENT] P2. Wire FreshnessMonitor alerts through UEI. When `is_stale=True`, emit `DATA_STALE` event via
      `log_event()`. Alerting-service subscribes and fires Telegram/PagerDuty. Target: alert fires within 60s of data
      going stale.
    status: pending
    depends_on: [freshness-monitor-class, freshness-venue-slas]

  # ── Phase 4: PRODUCTION BACKFILL ───────────────────────────────────────────
  # Exit criteria: 1yr tick data per venue, features computed, ML models trained, backtests validated
  # Blocker: Phase 1-2 (secrets + cassettes); Plan 1 Phase 4 (services deployed)

  - id: backfill-instruments-metadata
    content: >
      - [ ] [SCRIPT] P0. Step 1: Instruments metadata backfill. Run instruments-service in batch mode to populate GCS
      with instrument definitions for all 33 venues. Gate: instrument count matches expected per venue.
    status: pending

  - id: backfill-tick-data
    content: >
      - [ ] [SCRIPT] P0. Step 2: Tick data backfill (1 year per venue). Run market-tick-data-service backfill jobs per
      venue. Order: CeFi first (highest volume), then TradFi, then DeFi. Gate: data completeness check per venue (no
      gaps > SLA threshold).
    status: pending
    depends_on: [backfill-instruments-metadata]

  - id: backfill-features
    content: >
      - [ ] [SCRIPT] P1. Step 3: Feature computation. Run all features-* services in batch mode against backfilled tick
      data. Gate: feature count and date range match expectations.
    status: pending
    depends_on: [backfill-tick-data]

  - id: backfill-ml-training
    content: >
      - [ ] [SCRIPT] P1. Step 4: ML model training. Run ml-training-service against computed features. Gate: model
      metrics meet minimum thresholds (Sharpe, accuracy, etc.).
    status: pending
    depends_on: [backfill-features]

  - id: backfill-validation
    content: >
      [SCRIPT+HUMAN] P0. Step 5: Backtest validation. Run strategy-service backtests against historical data. Human
      reviews PnL curves, drawdown, and risk metrics. Gate: no anomalous results, metrics within historical bounds.
    status: pending
    depends_on: [backfill-ml-training]
---

## Notes

### Inter-Plan Blockers

- **This plan Phase 1 (secrets) blocks Plan 1 Phase 5** — production backfill needs API keys
- **Plan 1 Phase 3 (interfaces hardened) blocks this plan Phase 2** — cassette recording needs working interfaces
- **This plan Phase 2 (cassettes) blocks Plan 1 Phase 6 audit** — audit §10 FAIL requires VCR cassettes in 3 repos
