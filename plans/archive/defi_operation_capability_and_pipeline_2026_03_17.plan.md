---
doc_type: plan
title: defi-operation-capability-and-pipeline-2026-03-17
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    alerting-service,
    deployment-service,
    execution-service,
    instruments-service,
    strategy-service,
    unified-trading-system-ui,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-17"
overview:
  Wire operation-level capability validation into all interfaces, resolve SSOT flags, and complete DeFi end-to-end MVP
  pipeline
type: code
epic: epic-code-completion
completion_gates: { code: C4, deployment: none, business: none }
repo_gates:
  - { repo: unified-api-contracts, code: C2, deployment: none, business: none }
  - { repo: unified-trade-execution-interface, code: C0, deployment: none, business: none }
  - { repo: unified-defi-execution-interface, code: C0, deployment: none, business: none }
  - { repo: unified-market-interface, code: C0, deployment: none, business: none }
  - { repo: unified-sports-execution-interface, code: C0, deployment: none, business: none }
  - { repo: unified-reference-data-interface, code: C0, deployment: none, business: none }
  - { repo: execution-service, code: C0, deployment: none, business: none }
  - { repo: features-onchain-service, code: C0, deployment: none, business: none }
  - { repo: strategy-service, code: C0, deployment: none, business: none }
  - { repo: alerting-service, code: C0, deployment: none, business: none }
depends_on: [defi-keys-data-integration-2026-03-13]
todos:
  - { id: p1-uac-types-done, content: "- [x] [AGENT] P0. Add OperationEnvDetail, OperationDetail,
        UnsupportedOperationError types + validate_operation() to UAC capability.py

        ", status: done, note: "Completed 2026-03-17. 3 new types, 1 new function, additive extension of
        SourceCapability (new fields only)." }
  - { id: p1-uac-populate-done, content: "- [x] [AGENT] P0. Populate operation_details, base_urls, margin_model for all
        77 sources across _cefi.py, _defi.py, _tradfi.py, _sports.py, _altdata.py

        ", status: done, note: "Completed 2026-03-17. 53 sources with operation_details, 24 data-only with empty
        (fallback)." }
  - { id: p1-uac-exports-done, content: "- [x] [AGENT] P0. Update registry/__init__.py exports for new types

        ", status: done, note: Completed 2026-03-17. }
  - { id: p1-uac-tests, content: "- [x] [AGENT] P0. Unit tests for validate_operation() — happy path,
        UnsupportedOperationError, fallback to source-level, unknown source

        ", status: done, note: "" }
  - { id: p1-uac-parametrized-test, content: "- [x] [AGENT] P1. Parametrized integration test across all 53 sources with
        operation_details — bootstrap + validate per source

        ", status: done, note: "" }
  - { id: p1-uac-qg, content: "- [x] [AGENT] P0. Run UAC quality-gates.sh — must pass before Phase 2

        ", status: done, note: "" }
  - { id: p2-venue-context, content: "- [x] [AGENT] P0. Build resolve_venue_context() in UAC registry — bridges
        SportsVenueType/SportsAuthMethod/CAPTCHA_RISK/SUPPORTED_MARKET_TYPES + operation_details into one VenueContext
        object

        ", status: done, note: "VenueContext returns: execution_pattern, auth_method, signing_scheme, captcha_risk,
        supported_markets, operation_env_detail" }
  - { id: p2-venue-context-scraper, content: "- [x] [AGENT] P1. Populate VenueContext for web scraper venues
        (DraftKings, Bet365, etc.) — auth=LOGIN_CREDENTIALS, captcha from SPORTS_CAPTCHA_RISK, no operation_details

        ", status: done, note: "" }
  - { id: p2-compose-validation, content: "- [x] [AGENT] P0. Create compose_validation() chaining validate_instruction()
        (structural) → validate_operation() (runtime) — single call: validate_full(venue, instruction_type, operation,
        order_type, instrument_type, env)

        ", status: done, note: "" }
  - { id: p2-tests, content: "- [x] [AGENT] P1. Unit tests for resolve_venue_context() (CLOB, DeFi, scraper, data-only)
        + compose_validation() (structural+runtime combos)

        ", status: done, note: "" }
  - { id: p3-utei-wire, content: "- [x] [AGENT] P0. Wire validate_operation() into UTEI factory.py:get_order_adapter() —
        preflight before adapter creation

        ", status: done, note: "" }
  - { id: p3-udei-wire, content: "- [x] [AGENT] P0. Wire validate_operation() into UDEI protocol connectors — preflight
        in connect()/execute() for supply, borrow, flash_loan, stake

        ", status: done, note: "" }
  - { id: p3-umi-wire, content: "- [x] [AGENT] P1. Wire validate_operation() into UMI factory.py:get_adapter() —
        base_url resolution + data_fidelity awareness

        ", status: done, note: "" }
  - { id: p3-usei-wire, content: "- [x] [AGENT] P1. Wire validate_operation() into USEI adapter entry points — preflight
        for sports execution

        ", status: done, note: "" }
  - { id: p3-urdi-wire, content: "- [x] [AGENT] P2. Wire validate_operation() into URDI adapters — preflight for
        reference data fetches

        ", status: done, note: "" }
  - { id: p3-exec-svc-wire, content: "- [x] [AGENT] P0. Wire compose_validation() into execution-service order handler —
        replace ad-hoc venue checks

        ", status: done, note: "" }
  - { id: p4-decorator, content: "- [x] [AGENT] P1. Build @requires_operation_validation decorator in UAC — calls
        validate_operation() before method body

        ", status: done, note: Decorator extracts venue+operation+env from method args or self attributes }
  - { id: p4-apply-decorator, content: "- [x] [AGENT] P1. Apply decorator to UTEI, UDEI, USEI adapter/protocol methods
        (place_order, cancel, supply, borrow, etc.)

        ", status: done, note: "" }
  - { id: p4-ci-check, content: "- [x] [AGENT] P2. Add CI check in quality-gates.sh — grep for raw httpx/requests/ccxt
        calls in adapter code without @requires_operation_validation

        ", status: done, note: "" }
  - { id: p5-flag1-hl-classification, content: "- [x] [HUMAN+AGENT] P0. FLAG 1: Resolve Hyperliquid CeFi vs DeFi
        classification — UAC says cefi, UMI says onchain_perps, codex says DeFi. Pick one, update all repos.

        ", status: done, note: "Impacts: VENUE_CATEGORY_MAP, UMI factory category, execution-service chain
        classification, capability_declarations placement" }
  - { id: p5-flag2-utei-vs-udei, content: "- [x] [HUMAN] P0. FLAG 2: Resolved — both UTEI and UDEI are canonical for
        their instruction type. execution-service orchestrates: TRADE → UTEI (CCXT), TRANSFER/LEND/BORROW/STAKE → UDEI
        (protocol). No dedup needed.

        ", status: done, note: "Decided 2026-03-17. The split is by instruction type, not by venue. Execution-service is
        the orchestrator." }
  - { id: p5-flag3-cassette-ssot, content: "- [x] [AGENT] P1. FLAG 3: Investigated — no duplicates. Local UTEI/UMI
        cassettes cover execution endpoints (order_submit, position_risk), UAC covers reference data (exchangeInfo,
        tickers). Contribute locals to UAC via PR (expected workflow).

        ", status: done, note: Investigated 2026-03-17. No deletion needed. }
  - { id: p5-flag4-defi-config, content: "- [x] [HUMAN+AGENT] P1. FLAG 4: Resolved — elysium-defi-system deleted from
        system. DeFi config SSOT is UDEI DeFiConnectorConfig + UCI UnifiedCloudConfig.

        ", status: done, note: "Resolved 2026-03-18: elysium-defi-system deleted. UDEI DeFiConnectorConfig + UCI
        UnifiedCloudConfig are the canonical DeFi config sources." }
  - { id: p5-flag5-feature-pipeline, content: "- [x] [HUMAN] P0. FLAG 5: Resolved — feature pipeline
        (features-onchain-service). NOT DeFiYieldMonitor shortcut. Onchain features service already exists, less bolt-on
        maintenance. Strategies must not fetch data.

        ", status: done, note: Decided 2026-03-17. DeFiYieldMonitor in strategy-service is a violation of
        strategies-never-fetch-data rule. }
  - { id: p5-flag6-testnet-yaml, content: "- [x] [AGENT] P2. FLAG 6: Verified — YAML schema exactly matches Python
        loader. chain_id→protocol→contract_name→address structure. No mismatches.

        ", status: done, note: "Verified 2026-03-17. KNOWN_TESTNET_CHAIN_IDS has 4 extra chains (Goerli, Arb/Opt/Base
        Sepolia) not in YAML — benign." }
  - { id: p5-flag7-settlement-ssot, content: "- [x] [AGENT] P1. FLAG 7: SSOT VIOLATION CONFIRMED — 3 SettlementType defs
        (UIC + pnl.py + settlement_service.py), all divergent. Fix: add LST_YIELD + GAS_REBATE to UIC, delete 2 local
        defs, import from UIC.

        ", status: done, note: "Investigated 2026-03-17. UIC has 9 members (StrEnum), pnl.py has 8 (Enum, missing
        LP_FEE), settlement_service.py has 6 (Enum, has unique LST_YIELD+GAS_REBATE)." }
  - { id: p5-flag8-venue-slas, content: "- [x] [AGENT] P2. FLAG 8: Found — UIC
        domain/data_quality/venue_freshness_slas.py (32 venues, not 33 — 2 CeFi missing). Fix: add 2 missing CeFi
        venues, add to SSOT-INDEX.

        ", status: done, note: Investigated 2026-03-17. CeFi comment says 9 but lists 7. File not in SSOT-INDEX. }
  - { id: p6-verify-operation-details, content: "- [x] [AGENT] P1. Verify all 77 operation_details entries match actual
        adapter implementations — cross-reference signing_scheme and required_credential

        ", status: done, note: "" }
  - { id: p6-hl-missing-ops, content: "- [x] [AGENT] P2. Add missing Hyperliquid operations to capability
        (spot_transfer, approve_agent, approve_builder_fee — from SDK signing.py)

        ", status: done, note: "" }
  - { id: p6-base-url-drift, content: "- [x] [AGENT] P2. Verify base_urls match CCXT sandbox URLs and
        testnet_contracts.yaml addresses — no drift between registries

        ", status: done, note: "" }
  - { id: p6-codex-docs, content: "- [x] [AGENT] P1. Update unified-trading-codex with operation capability registry
        docs — signing schemes, credential types, how to add a venue, how validate_operation() works

        ", status: done, note: "" }
  - { id: p7-secrets-hl-done, content: "- [x] [HUMAN] P0. Load Hyperliquid mainnet + testnet API keys into Secret
        Manager (hyperliquid-trade-key, hyperliquid-testnet-trade-key)

        ", status: done, note: "Completed 2026-03-17. Mainnet: 0x6C00..., Testnet: 0x4f68... Both verified via address
        derivation." }
  - { id: p7-secrets-tier1, content: "- [x] [HUMAN] P0. Tier 1 secrets already in Secret Manager: alchemy-api-key (Nov
        2025), thegraph-api-key x9 (Nov 2025/Jan 2026), graph-api-key (Nov 2025). Only missing: wallet-private-key for
        on-chain DeFi signing.

        ", status: done, note: "Verified 2026-03-17 via gcloud secrets list. Previously listed as needed — was wrong,
        already existed." }
  - { id: p7-secrets-tier2, content: "- [x] [HUMAN] P1. Tier 2 secrets already in Secret Manager: aavescan-api-key (Nov
        2025), tardis-api-key (Oct 2025) + backup + full variants.

        ", status: done, note: "Verified 2026-03-17 via gcloud secrets list. Previously listed as needed — was wrong,
        already existed." }
  - { id: p7-secrets-tier3, content: "- [x] [HUMAN] P2. Load Tier 3 secrets: tenderly-fork-rpc-url (Week 2)

        ", status: done, note: SEE defi-keys-data-integration-2026-03-13 Phase 1 }
  - { id: p7-testnet-hl-done, content: "- [x] [HUMAN] P0. Fund Hyperliquid testnet — faucet claim, API key creation,
        order lifecycle verified

        ", status: done, note: Completed 2026-03-17. 999 USDC on testnet. Place/cancel order tested successfully via SDK
        signing. }
  - { id: p7-testnet-sepolia, content: "- [x] [HUMAN] P1. Get Sepolia ETH from faucet (~1 ETH for gas) for on-chain DeFi
        testnet

        ", status: done, note: "" }
  - { id: p7-confirm-wallet, content: "- [x] [HUMAN] P0. Confirmed: same wallet for testnet+mainnet. Chain priority:
        Ethereum + Arbitrum (Hyperliquid L1 on Arbitrum).

        ", status: done, note: "Decided 2026-03-17. Wallet: 0x992ebFe04DB05f964C45BCE3D73Ca4c81715a79f for both envs." }
  - { id: p8-vcr-confirm, content: "- [x] [HUMAN] P0. Confirmed: mainnet reads + testnet writes. If no testnet exists,
        real mainnet only if required (not optional).

        ", status: done, note: Decided 2026-03-17. }
  - { id: p8-vcr-priority-a, content: "- [x] [AGENT] P0. Record 9 strategy-blocking cassettes — HL
        user_state/funding/l2_book/candle/ticker + TheGraph Aave+Uniswap + DefiLlama TVL+yields

        ", status: done, note: SEE defi-keys-data-integration-2026-03-13 Phase 2 for full endpoint list }
  - { id: p8-vcr-priority-b, content: "- [x] [AGENT] P0. Record 5 execution-blocking cassettes — HL
        order/fill/open_order (testnet) + Alchemy getReserveData/getUserAccountData

        ", status: done, note: "" }
  - { id: p8-vcr-priority-c, content: "- [x] [AGENT] P2. Record remaining stubs across 14 DeFi protocols

        ", status: done, note: "" }
  - { id: p9-feature-aave-supply-apy, content: "- [x] [AGENT] P0. Build aave_supply_apy calculator in
        features-onchain-service (reads Alchemy RPC → publishes to Pub/Sub)

        ", status: done, note: "" }
  - { id: p9-feature-aave-utilization, content: "- [x] [AGENT] P0. Build aave_utilization calculator in
        features-onchain-service

        ", status: done, note: "" }
  - { id: p9-feature-aave-liquidity-index, content: "- [x] [AGENT] P0. Build aave_liquidity_index calculator in
        features-onchain-service

        ", status: done, note: "" }
  - { id: p9-feature-lst, content: "- [x] [AGENT] P0. Build lst_staking_apy + weeth_rate calculators in
        features-onchain-service (EtherFi)

        ", status: done, note: "" }
  - { id: p9-feature-health-factor, content: "- [x] [AGENT] P0. Build health_factor calculator in
        features-onchain-service (Aave V3)

        ", status: done, note: "" }
  - { id: p9-feature-funding-verify, content: "- [x] [AGENT] P1. Verify funding_rate already works for Hyperliquid via
        features-delta-one-service CeFi path

        ", status: done, note: "" }
  - { id: p10-web3-signing, content: "- [x] [AGENT] P0. Wire Web3 transaction signing + broadcast for on-chain execution
        (Aave supply/borrow/repay, Uniswap swap) — needs wallet-private-key in SM

        ", status: done, note: "" }
  - { id: p10-confirm-mode, content: "- [x] [HUMAN] P0. Confirmed: testnet first, THEN paper trading. Paper trading live
        = simulated fills on real data + order simulation (no real execution).

        ", status: done, note: Decided 2026-03-17. }
  - { id: p10-confirm-ui, content: "- [x] [HUMAN] P1. Confirmed: skip DeFi UI for now — UI refactor in progress. Revisit
        after refactor.

        ", status: done, note: "Decided 2026-03-17. UI plan: ui-platform-redesign-2026-03-17." }
  - { id: p10-ui-wire, content: "- [x] [AGENT] P1. SKIPPED — DeFi UI wiring deferred per human decision. UI refactor in
        progress.

        ", status: done, note: Deferred 2026-03-17. }
  - { id: p10-alert-p0, content: "- [x] [AGENT] P0. Wire P0 DeFi alerts — health_factor < 1.2, weETH depeg > 2%

        ", status: done, note: "" }
  - { id: p10-alert-p1, content: "- [x] [AGENT] P1. Wire P1 DeFi alerts — Aave utilization > 95%, funding rate flip,
        feature staleness > 2x SLA

        ", status: done, note: "" }
  - { id: p10-confirm-alerting, content: "- [x] [HUMAN] P1. Confirmed: Telegram for DeFi alerts for now.

        ", status: done, note: Decided 2026-03-17. }
  - { id: p11-backfill-hl, content: "- [x] [AGENT] P1. Backfill Hyperliquid trades — Tardis (2024-10→2025-03) + S3
        archive (2025-03+)

        ", status: done, note: SEE defi-keys-data-integration-2026-03-13 Phase 4 }
  - { id: p11-backfill-aave, content: "- [x] [AGENT] P1. Backfill Aave rates/indices — TheGraph + Alchemy (~1 year
        hourly)

        ", status: done, note: "" }
  - { id: p11-backfill-uniswap-lst, content: "- [x] [AGENT] P2. Backfill Uniswap pool data + weETH/stETH rates

        ", status: done, note: "" }
  - { id: p11-backfill-features, content: "- [x] [AGENT] P2. Compute features over backfilled data via
        features-onchain-service

        ", status: done, note: "" }
  - { id: p12-delete-backfill-scripts, content: "- [x] [AGENT] P0. Delete the 5 standalone backfill scripts (they bypass
        the real services) and delete backfill/ data from GCS. Scripts:
        market-tick-data-service/scripts/backfill_hyperliquid_trades.py, backfill_defi_orchestrator.py,
        features-onchain-service/scripts/backfill_aave_rates.py, backfill_uniswap_pools.py, backfill_lst_rates.py

        ", status: done, note: Scripts duplicated what the services already do via CLI. Data landed in wrong GCS path
        (backfill/ instead of service canonical paths). }
  - { id: p12-instruments-config-harden, content: "- [x] [AGENT] P0. Harden instruments-service config.py — remove empty
        string defaults for all 8 sink_bucket_* fields, ethereum_rpc_url, uniswap_v3_graph_url. Use bucket template
        pattern (instruments-store-{category}-{project_id}, instruments-store-{category}-test-{project_id} for mock)
        computed from gcp_project_id. Fail loud if required config is missing.

        ", status: done, note: Currently all 8 bucket fields default to '' — service silently fails on write. }
  - { id: p12-market-tick-config-harden, content: "- [x] [AGENT] P0. Harden market-tick-data-service config.py — replace
        hardcoded 'mock-market-data-bucket' with template. Real: market-data-tick-{category}-{project_id}. Mock
        (CLOUD_MOCK_MODE=true): market-data-tick-{category}-test-{project_id}. Same -test- convention all other buckets
        use. Same directory structure under both. Fail loud if GCP_PROJECT_ID or category not set.

        ", status: done, note: "Test buckets already exist (market-data-tick-defi-test-central-element-323112, etc.).
        Convention: -test- inserted before {project_id} when mock mode." }
  - { id: p12-strategy-config-defi, content: "- [x] [AGENT] P0. Fix strategy-service config.py — parameterize
        market_data_bucket_template by category (currently hardcoded to 'cefi'). Fail loud if no strategy YAML path for
        non-default modes. DeFi strategies must read from market-data-tick-defi-{P}, not cefi.

        ", status: done, note: "Hardcoded 'market-data-tick-cefi-{project_id}' means DeFi strategies never find DeFi
        market data." }
  - { id: p12-live-batch-bucket-convention, content: "- [x] [AGENT] P1. Establish live/ vs by_date/ bucket convention.
        Same bucket, live/ prefix at root for streaming micro-batches (1-5 min window parquet files), by_date/ for daily
        accumulated batch. Hive partitioning (venue=X/instrument=Y/) under both. End-of-day GCS compose merges live
        windows into daily partition. Document in codex 02-data/ and update UCI StorageDataSource to support live vs
        batch routing.

        ", status: done, note: "GCS compose supports up to 32 objects per call (chain for more). Same convention works
        on S3. PubSub subscribers do the micro-batching, not per-event writes." }
  - { id: p12-run-pipeline-via-cli, content: "- [ ] [AGENT] P1. Run DeFi pipeline end-to-end via actual service CLIs:
        (1) instruments-service --asset-group DEFI, (2) market-tick-data-service --mode download --asset-group DEFI, (3)
        features-onchain-service --operation compute --mode batch --asset-group DEFI --feature-group ALL. Verify data
        lands in canonical GCS paths.

        ", status: todo, note: Depends on p12-instruments-config-harden and p12-market-tick-config-harden completing
        first. }
  - { id: p12-tenderly-fork-provisioned, content: "- [x] [AGENT] P1. Create deterministic Tenderly Virtual TestNet fork
        pinned to ETH mainnet block 24681163 (2026-03-18). API key + fork RPC URL in Secret Manager. Codex docs updated.

        ", status: done, note: "Completed 2026-03-18. tenderly-api-key + tenderly-fork-rpc-url in SM. Fork: chain ID
        73571, sync disabled. Slug: uts-deterministic-eth-mainnet-blk-24681163." }
  - { id: p13-udei-remove-sm-reads, content: "- [x] [AGENT] P0. UDEI: Remove direct Secret Manager reads from base.py
        _load_wallet_credentials(). Service (execution-service) should fetch wallet private key + RPC URL from SM, pass
        via config dict. Move RPC URL templates (lines 39-44) to UAC capability_declarations/_defi.py base_urls. Remove
        CredentialsRegistry import from UDEI.

        ", status: done, note: "UDEI is the main outlier — reads its own keys from SM. All other interfaces either
        accept keys as params (UTEI, USEI) or don't need them (UMI, UEI, UFI)." }
  - { id: p13-urdi-remove-sm-reads, content: "- [x] [AGENT] P1. URDI: Remove project_id-based internal SM lookups from
        adapters (tardis, databento, polygon, betfair, ibkr). Factory should accept explicit api_key params like UTEI
        does. Services pass keys in.

        ", status: done, note: Currently factory accepts project_id and adapters internally call get_secret_client for
        rate-limit keys. }
  - { id: p13-uci-credential-injection, content: "- [x] [AGENT] P1. UCI: Ensure CredentialsRegistry is reference-only
        (secret name constants), not used for direct fetching inside interfaces. Services call get_secret_client
        themselves, pass resolved values to interfaces. Prepare for per-service IAM (dev/staging/prod service accounts
        with different SM access).

        ", status: done, note: UCI CredentialsRegistry constants are fine to keep as the SSOT for secret names. The
        change is that interfaces don't call get_secret_client() — services do. }
  - { id: p13-uac-rpc-url-registry, content: "- [x] [AGENT] P1. UAC: Move RPC URL templates (Alchemy chain templates,
        Tenderly fork mappings) from UDEI base.py to capability_declarations/_defi.py alongside existing base_urls. Add
        fork_mode → RPC resolution mapping. Single place for all DeFi chain connectivity info.

        ", status: done, note: UDEI base.py lines 39-44 have hardcoded Alchemy URL templates per chain_id. These belong
        in UAC capability registry where base_urls already live. }
  - { id: p13-exec-svc-inject-keys, content: "- [x] [AGENT] P0. execution-service: Update DeFi execution path to fetch
        wallet key + RPC URL from SM, pass to UDEI connector via config dict. Currently UDEI fetches its own — after
        p13-udei-remove-sm-reads, exec-svc must provide them.

        ", status: done, note: Pairs with p13-udei-remove-sm-reads. Both must land together. }
  - { id: p13-codex-convention-doc, content: "- [x] [AGENT] P1. Document the interface credential convention in codex
        04-architecture/. Interfaces are API-keyless: define connectivity + protocol logic. Services inject keys at
        runtime via factory/constructor params. UAC holds static mappings (URLs, chain configs). UCI CredentialsRegistry
        is the SSOT for secret names only.

        ", status: done, note: "Completed 2026-03-18. Created
        unified-trading-/codex/04-architecture/interface-credential-convention.md. Covers per-interface pattern table,
        anti-patterns, rationale." }
  - { id: p13-delete-elysium-defi, content: "- [x] [AGENT] P0. Delete elysium-defi-system: removed from
        workspace-manifest.json, runtime-topology.yaml, code-workspace, derived-dependency-manifest.json, all active
        plans, codex audit yaml, epics, system-topology.json, variables.tf, provision-defi-testnet.sh. Deleted local
        repo directory. Deleted GitHub repo.

        ", status: done, note: Completed 2026-03-18. All references removed from config/manifest/plan files. p5-flag4
        closed (elysium config no longer exists). }
---

Schema migrations: UDEI → UIC ---

- id: p14-operationtype-to-uic content: |
  - [x] [AGENT] P0. Move OperationType enum from UDEI types.py to UIC. Delete UDEI local def + exec-svc duplicate
        (models/operations.py). Update all imports across UDEI, execution-service, strategy-service. status: done note:
        "Duplicated in 3 repos: UDEI, exec-svc, strategy-svc. UIC is the SSOT for internal enums shared across
        services."

- id: p14-ordertype-to-uic content: |
  - [x] [AGENT] P0. Move OrderType enum from UDEI instructions.py to UIC. Delete exec-svc duplicate
        (models/instruction.py). Update all imports. status: done note: "Duplicated in UDEI + exec-svc."

- id: p14-positiontype-to-uic content: |
  - [x] [AGENT] P0. Move PositionType enum from UDEI position.py to UIC. Delete exec-svc duplicate (models/position.py).
        Update all imports. status: done note: "Duplicated in UDEI + exec-svc."

- id: p14-executionstatus-to-uic content: |
  - [x] [AGENT] P1. Move ExecutionStatus enum from exec-svc models/execution_result.py to UIC. Update imports. status:
        done note: "Used by exec-svc + pnl-svc + risk-svc."

- id: p14-marketstate-to-uic content: |
  - [x] [AGENT] P1. Move MarketState StrEnum from exec-svc models/instruction.py to UIC. Update imports. status: done
        note: "Used across execution chain."

- id: p14-txresult-types-to-uic content: |
  - [x] [AGENT] P0. Move SwapResult, TxResult, SwapQuoteResult, PoolStateResult, ConnectorStateDict TypedDicts from UDEI
        base.py to UIC. These are execution result schemas crossing service boundaries. status: done note: "UDEI base.py
        defines 5 TypedDicts that exec-svc and strategy-svc also reference."

- id: p14-execution-instruction-to-uic content: |
  - [x] [AGENT] P0. Move ExecutionInstruction dataclass from UDEI instructions.py to UIC. This is the strategy→execution
        contract. Update all imports across UDEI, exec-svc, strategy-svc. status: done note: "Core cross-service
        contract. Strategy emits it, exec-svc consumes it."

- id: p14-order-fill-types-to-uic content: |
  - [x] [AGENT] P1. Move OrderFill, OrderData, OrderStatus, Position, OpenOrder TypedDicts from UDEI cefi_base.py to
        UIC. Update imports. status: done note: "CeFi execution result types shared across UTEI and exec-svc."

# --- Schema migrations: UDEI → UAC ---

- id: p14-defi-datasource-to-uac content: |
  - [x] [AGENT] P1. Move DeFiDataSource enum from UDEI config.py to UAC registry. It classifies external data providers
        (alchemy, thegraph, self_hosted) — same domain as SourceCapability. status: done note: "External provider
        classification belongs in UAC alongside capability declarations."

- id: p14-subgraph-ids-to-uac content: |
  - [x] [AGENT] P1. Consolidate all TheGraph subgraph IDs into UAC capability_declarations/_defi.py. Currently
        scattered: UDEI config.py (thegraph_subgraph_id field), aave.py (hardcoded), instruments-service (hardcoded).
        Single dict in UAC. status: done note: "Subgraph IDs are external venue metadata — same as base_urls."

# --- Config migration: UDEI config.py → empty ---

- id: p14-delete-udei-config content: |
  - [x] [AGENT] P0. After all schema migrations complete: delete DeFiDataSourceConfig and DeFiConnectorConfig from UDEI
        config.py. Interfaces don't own config — they receive config dicts from services. Venue connectivity metadata
        (RPC routing, subgraph IDs) lives in UAC. Secret names live in UCI CredentialsRegistry. Runtime params
        (timeouts, fallbacks) are service config. status: done note: "Depends on p14-defi-datasource-to-uac and
        p14-subgraph-ids-to-uac completing first. UDEI config.py should be empty or deleted after this."

# --- Error codes migration ---

- id: p14-defi-error-codes-to-uac content: |
  - [x] [AGENT] P1. Move DefiErrorCode class (13 error codes) from UDEI aave.py to UAC
        canonical/crosscutting/errors/defi.py (where the error classifications already live). UDEI imports from UAC.
        status: done note: "Error codes are already partially in UAC (VENUE_ERRORS_DEFI). DefiErrorCode should live
        alongside them."

# --- Benchmark types ---

- id: p14-benchmarktype-to-uic content: |
  - [x] [AGENT] P2. Move BenchmarkType enum from exec-svc models/benchmark.py to UIC. Update imports. status: done note:
        "Lower priority — only used within execution domain. Agent running."

# =====================================================================

# PHASE 15: Schema SSOT Audit Remediation (2026-03-20)

# Found by full workspace audit — duplicates and misplacements

# Gate: All affected repo QGs pass

# =====================================================================

- id: p15-strategy-positiontype-fix content: |
  - [x] [AGENT] P0. Fix strategy-service PositionType — it redefines locally despite UIC having the canonical version.
        Delete local def in strategy_service/models/position.py, import from UIC. Also move PositionSide
        (LONG/SHORT/NEUTRAL) to UIC. status: done note: "strategy-svc has PositionType(SPOT_ASSET, PERPETUAL, FUTURE,
        POOL) + exec-svc has PositionType(A_TOKEN, DEBT_TOKEN, LST, YIELD_BEARING). UIC version has all. strategy-svc
        must import from UIC."

- id: p15-consolidate-position-models content: |
  - [x] [AGENT] P0. Consolidate DeFiPosition (exec-svc) + StrategyPosition (strategy-svc) into single UIC Position
        domain. Both track: instrument, amount, entry_price, pnl. DeFi adds: health_factor, liquidation_threshold.
        Strategy adds: index-based tracking. UIC should have the superset. Both repos import from UIC. status: done
        note: "Parallel implementations of same domain concept. exec-svc version is more complete for DeFi lending."

- id: p15-execution-result-to-uic content: |
  - [x] [AGENT] P0. Move ExecutionResult + SignalExecutionResult dataclasses from exec-svc models/execution_result.py to
        UIC. Consumed by risk-service, analytics, backtesting, PnL attribution — cross-service contracts. status: done
        note: "ExecutionStatus already moved to UIC. The result dataclasses that use it should follow."

- id: p15-instructiontype-to-uic content: |
  - [x] [AGENT] P0. Move InstructionType StrEnum from exec-svc utils/instruction_type.py to UIC. Values: TRADE, SWAP,
        ZERO_ALPHA, OPTIONS_COMBO, FUTURES_ROLL, PREDICTION_BET, SPORTS_BET, SPORTS_EXCHANGE. Determines algorithm
        selection across all execution paths. status: done note: "Different from OperationType (which is the DeFi
        operation enum). InstructionType is the execution routing classifier."

- id: p15-defi-alert-types-to-uac content: |
  - [x] [AGENT] P1. Move DefiAlertType StrEnum from alerting-service rules/defi_rules.py to UAC canonical alert
        taxonomy. Values: HEALTH_FACTOR_CRITICAL, WEETH_DEPEG, AAVE_UTILIZATION_SPIKE, FUNDING_RATE_FLIP, FEATURE_STALE.
        Same pattern as venue error codes. status: done note: "Alert definitions are external domain classification —
        belongs in UAC alongside DefiErrorCode."

- id: p15-defi-alert-model-to-uic content: |
  - [x] [AGENT] P1. Move DefiAlert BaseModel from alerting-service to UIC. Alert output model consumed by risk,
        monitoring, UI services. status: done note: "Pairs with p15-defi-alert-types-to-uac."

isProject: false
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

## Execution DAG

```
Phase 1 (UAC types — DONE) ──────────────────────────────┐
Phase 2 (Sports bridge + compose_validation — UAC)        │
  ├── resolve_venue_context()     PARALLEL                │
  └── compose_validation()        PARALLEL                │
           ↓ QG gate: UAC pass                            │
Phase 3 (Wire into interfaces — PARALLEL)                 │
  ├── UTEI ─┐                                             │
  ├── UDEI  │  All run in parallel                        │
  ├── UMI   │  Each repo's QG must pass                   │
  ├── USEI  │                                             │
  ├── URDI  │                                             │
  └── exec  ┘                                             │
           ↓ QG gate: all interface QGs pass              │
Phase 4 (Enforcement — decorator + CI)                    │
           ↓                                              │
Phase 5 (SSOT flags — PARALLEL, some need [HUMAN])  ◄────┘
Phase 6 (Cleanup + docs)
           ↓
Phase 7 (Secrets + testnet — [HUMAN] — blocks 8-10)
           ↓
Phase 8 (VCR cassettes — needs secrets)
           ↓
Phase 9 (Feature calculators — needs cassettes for testing)
           ↓
Phase 10 (Execution + UI + Alerting — PARALLEL)
           ↓
Phase 11 (Historical backfill)
```

## Cross-References to Existing Plans

| Topic                            | Existing Plan                                   | What It Covers                     | What THIS Plan Adds                                                  |
| -------------------------------- | ----------------------------------------------- | ---------------------------------- | -------------------------------------------------------------------- |
| DeFi secrets (30 keys, 4 phases) | `defi-keys-data-integration-2026-03-13` Phase 1 | Full secret provisioning lifecycle | References it; adds Tier 1/2/3 confirmations as human gates          |
| VCR cassette recording           | `defi-keys-data-integration-2026-03-13` Phase 2 | All venues, recording protocol     | References it; adds priority A/B/C split + approach confirmation     |
| Historical backfill              | `defi-keys-data-integration-2026-03-13` Phase 4 | 5-step pipeline                    | References it; scopes to DeFi-specific backfill                      |
| Strategy expansion (4 DeFi)      | `strategy-system-citadel-master-2026-03-15`     | 21 strategies, manifest, maturity  | Does NOT duplicate; this plan focuses on feature calculator blockers |
| CI/CD pipeline                   | `cicd-code-rollout-master-2026-03-13`           | 67-repo rollout                    | Does NOT duplicate; this plan adds validation CI check only          |
| QG remediation                   | `quality-gates-systemic-remediation-2026-03-16` | 69-repo audit                      | Does NOT duplicate; this plan scopes QG to interface wiring repos    |
| Registry completeness            | `registry-completeness-implementation-detail`   | Instrument types, enums            | Does NOT duplicate; this plan adds operation-level capability layer  |
| Mock E2E                         | `production-mock-e2e-plan-d90c8f20`             | VCR + mock replay for all repos    | Does NOT duplicate; this plan focuses on DeFi-specific cassettes     |

## What's New in This Plan (Not in Any Existing Plan)

1. **Operation-level capability validation** — `validate_operation()`, `resolve_venue_context()`, `compose_validation()`
   — entirely new registry layer
2. **Interface wiring** — preflight checks in UTEI/UDEI/UMI/USEI/URDI — not covered anywhere
3. **@requires_operation_validation decorator** — enforcement mechanism — not covered anywhere
4. **SSOT flag resolution** (flags 1-8) — discovered during DeFi research, not tracked elsewhere
5. **DeFi feature calculators** (aave_supply_apy, etc.) — referenced in defi-keys-data-integration as "P0 blocker" but
   no implementation plan exists
6. **DeFi alerting** (health factor, depeg, utilization) — no plan covers this
7. **DeFi UI wiring** — no plan covers DeFi-specific UI integration

## Phase 16 — Remaining Items (added 2026-03-21)

todos:

- id: p16-gas-price-adapter content: |
  - [x] [AGENT] P2. Build gas price time series adapter in UMI — single time series per chain using eth_feeHistory.
        Store in market-data-tick-defi-{P}/by_date/day={date}/data_type=gas_price/ethereum.parquet. Needed for accurate
        backtest gas cost simulation. status: done
- id: p16-documentation-update content: |
  - [x] [AGENT] P1. Update CLAUDE.md, codex docs, cursor rules for all DeFi improvements from this session — interface
        credential convention, schema consolidation, Tenderly fork usage, flash loan receiver, reusable integration test
        fixtures. status: done
- id: p16-commit-all-changes content: |
  - [ ] [HUMAN] P0. Review + QG sweep + commit uncommitted changes across ~15 repos from 2026-03-21 session. DONE
        (2026-03-21): UAC, UMI, MTDS, MDPS, unified-trading-system-ui. REMAINING: UIC, UDEI, URDI, UCI,
        execution-service, strategy-service, instruments-service, deployment-service, alerting-service, codex, PM.
        status: todo
- id: p16-tenderly-fork-deploy-debug content: |
  - [x] [AGENT] P2. Debug Tenderly fork contract deployment failure — receiver deploys on Sepolia but fails on Virtual
        TestNets. Likely free tier quota or EVM version issue. Not blocking — Sepolia is the real testnet. status: done
