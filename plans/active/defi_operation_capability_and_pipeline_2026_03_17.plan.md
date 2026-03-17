---
name: defi-operation-capability-and-pipeline-2026-03-17
overview:
  Wire operation-level capability validation into all interfaces, resolve SSOT flags, and complete DeFi end-to-end MVP
  pipeline
type: code
epic: epic-code-completion
status: active

completion_gates:
  code: C4
  deployment: none
  business: none

repo_gates:
  - repo: unified-api-contracts
    code: C2
    deployment: none
    business: none
  - repo: unified-trade-execution-interface
    code: C0
    deployment: none
    business: none
  - repo: unified-defi-execution-interface
    code: C0
    deployment: none
    business: none
  - repo: unified-market-interface
    code: C0
    deployment: none
    business: none
  - repo: unified-sports-execution-interface
    code: C0
    deployment: none
    business: none
  - repo: unified-reference-data-interface
    code: C0
    deployment: none
    business: none
  - repo: execution-service
    code: C0
    deployment: none
    business: none
  - repo: features-onchain-service
    code: C0
    deployment: none
    business: none
  - repo: strategy-service
    code: C0
    deployment: none
    business: none
  - repo: alerting-service
    code: C0
    deployment: none
    business: none

depends_on:
  - defi-keys-data-integration-2026-03-13

todos:
  # =====================================================================
  # PHASE 1: Operation Capability Validation (UAC — already started)
  # Gate: UAC quality-gates.sh pass
  # =====================================================================
  - id: p1-uac-types-done
    content: |
      - [x] [AGENT] P0. Add OperationEnvDetail, OperationDetail, UnsupportedOperationError types + validate_operation() to UAC capability.py
    status: done
    note: "Completed 2026-03-17. 3 new types, 1 new function, backwards-compatible extension of SourceCapability."

  - id: p1-uac-populate-done
    content: |
      - [x] [AGENT] P0. Populate operation_details, base_urls, margin_model for all 77 sources across _cefi.py, _defi.py, _tradfi.py, _sports.py, _altdata.py
    status: done
    note: "Completed 2026-03-17. 53 sources with operation_details, 24 data-only with empty (fallback)."

  - id: p1-uac-exports-done
    content: |
      - [x] [AGENT] P0. Update registry/__init__.py exports for new types
    status: done
    note: "Completed 2026-03-17."

  - id: p1-uac-tests
    content: |
      - [ ] [AGENT] P0. Unit tests for validate_operation() — happy path, UnsupportedOperationError, fallback to source-level, unknown source
    status: todo
    note: ""

  - id: p1-uac-parametrized-test
    content: |
      - [ ] [AGENT] P1. Parametrized integration test across all 53 sources with operation_details — bootstrap + validate per source
    status: todo
    note: ""

  - id: p1-uac-qg
    content: |
      - [ ] [AGENT] P0. Run UAC quality-gates.sh — must pass before Phase 2
    status: todo
    note: ""

  # =====================================================================
  # PHASE 2: Sports Bridge + Composed Validation (UAC)
  # Gate: UAC quality-gates.sh pass
  # PARALLEL within phase
  # =====================================================================
  - id: p2-venue-context
    content: |
      - [ ] [AGENT] P0. Build resolve_venue_context() in UAC registry — bridges SportsVenueType/SportsAuthMethod/CAPTCHA_RISK/SUPPORTED_MARKET_TYPES + operation_details into one VenueContext object
    status: todo
    note:
      "VenueContext returns: execution_pattern, auth_method, signing_scheme, captcha_risk, supported_markets,
      operation_env_detail"

  - id: p2-venue-context-scraper
    content: |
      - [ ] [AGENT] P1. Populate VenueContext for web scraper venues (DraftKings, Bet365, etc.) — auth=LOGIN_CREDENTIALS, captcha from SPORTS_CAPTCHA_RISK, no operation_details
    status: todo
    note: ""

  - id: p2-compose-validation
    content: |
      - [ ] [AGENT] P0. Create compose_validation() chaining validate_instruction() (structural) → validate_operation() (runtime) — single call: validate_full(venue, instruction_type, operation, order_type, instrument_type, env)
    status: todo
    note: ""

  - id: p2-tests
    content: |
      - [ ] [AGENT] P1. Unit tests for resolve_venue_context() (CLOB, DeFi, scraper, data-only) + compose_validation() (structural+runtime combos)
    status: todo
    note: ""

  # =====================================================================
  # PHASE 3: Wire into Interfaces (PARALLEL across repos)
  # Gate: Each repo's quality-gates.sh pass
  # Depends on: Phase 1 complete (UAC types exist)
  # =====================================================================
  - id: p3-utei-wire
    content: |
      - [ ] [AGENT] P0. Wire validate_operation() into UTEI factory.py:get_order_adapter() — preflight before adapter creation
    status: todo
    note: ""

  - id: p3-udei-wire
    content: |
      - [ ] [AGENT] P0. Wire validate_operation() into UDEI protocol connectors — preflight in connect()/execute() for supply, borrow, flash_loan, stake
    status: todo
    note: ""

  - id: p3-umi-wire
    content: |
      - [ ] [AGENT] P1. Wire validate_operation() into UMI factory.py:get_adapter() — base_url resolution + data_fidelity awareness
    status: todo
    note: ""

  - id: p3-usei-wire
    content: |
      - [ ] [AGENT] P1. Wire validate_operation() into USEI adapter entry points — preflight for sports execution
    status: todo
    note: ""

  - id: p3-urdi-wire
    content: |
      - [ ] [AGENT] P2. Wire validate_operation() into URDI adapters — preflight for reference data fetches
    status: todo
    note: ""

  - id: p3-exec-svc-wire
    content: |
      - [ ] [AGENT] P0. Wire compose_validation() into execution-service order handler — replace ad-hoc venue checks
    status: todo
    note: ""

  # =====================================================================
  # PHASE 4: Enforcement (decorator + CI)
  # Gate: All interface QGs pass
  # Depends on: Phase 3 complete
  # =====================================================================
  - id: p4-decorator
    content: |
      - [ ] [AGENT] P1. Build @requires_operation_validation decorator in UAC — calls validate_operation() before method body
    status: todo
    note: "Decorator extracts venue+operation+env from method args or self attributes"

  - id: p4-apply-decorator
    content: |
      - [ ] [AGENT] P1. Apply decorator to UTEI, UDEI, USEI adapter/protocol methods (place_order, cancel, supply, borrow, etc.)
    status: todo
    note: ""

  - id: p4-ci-check
    content: |
      - [ ] [AGENT] P2. Add CI check in quality-gates.sh — grep for raw httpx/requests/ccxt calls in adapter code without @requires_operation_validation
    status: todo
    note: ""

  # =====================================================================
  # PHASE 5: SSOT Flag Resolution (PARALLEL)
  # These are ambiguities discovered during DeFi pipeline research.
  # Some need human decisions [HUMAN], others are investigative [AGENT].
  # =====================================================================
  - id: p5-flag1-hl-classification
    content: |
      - [ ] [HUMAN+AGENT] P0. FLAG 1: Resolve Hyperliquid CeFi vs DeFi classification — UAC says cefi, UMI says onchain_perps, codex says DeFi. Pick one, update all repos.
    status: todo
    note:
      "Impacts: VENUE_CATEGORY_MAP, UMI factory category, execution-service chain classification,
      capability_declarations placement"

  - id: p5-flag2-utei-vs-udei
    content: |
      - [x] [HUMAN] P0. FLAG 2: Resolved — both UTEI and UDEI are canonical for their instruction type. execution-service orchestrates: TRADE → UTEI (CCXT), TRANSFER/LEND/BORROW/STAKE → UDEI (protocol). No dedup needed.
    status: done
    note: "Decided 2026-03-17. The split is by instruction type, not by venue. Execution-service is the orchestrator."

  - id: p5-flag3-cassette-ssot
    content: |
      - [ ] [AGENT] P1. FLAG 3: Consolidate cassette locations — delete local copies in UTEI/UMI tests/cassettes/, all reference AC external/<venue>/mocks/ SSOT path
    status: todo
    note: ""

  - id: p5-flag4-defi-config
    content: |
      - [ ] [HUMAN+AGENT] P1. FLAG 4: Resolve DeFi config SSOT — Elysium DeFiSystemConfig vs UDEI DeFiConnectorConfig vs UCI UnifiedCloudConfig. Pick canonical, deprecate rest.
    status: todo
    note: ""

  - id: p5-flag5-feature-pipeline
    content: |
      - [x] [HUMAN] P0. FLAG 5: Resolved — feature pipeline (features-onchain-service). NOT DeFiYieldMonitor shortcut. Onchain features service already exists, less bolt-on maintenance. Strategies must not fetch data.
    status: done
    note: "Decided 2026-03-17. DeFiYieldMonitor in strategy-service is a violation of strategies-never-fetch-data rule."

  - id: p5-flag6-testnet-yaml
    content: |
      - [ ] [AGENT] P2. FLAG 6: Verify testnet_contracts.yaml matches TestnetContractRegistry loader expectations — field names, chain IDs, protocol keys
    status: todo
    note: ""

  - id: p5-flag7-settlement-ssot
    content: |
      - [ ] [AGENT] P1. FLAG 7: Check if strategy-service imports UIC SettlementType or defines its own — fix if SSOT violation
    status: todo
    note: ""

  - id: p5-flag8-venue-slas
    content: |
      - [ ] [AGENT] P2. FLAG 8: Find where venue SLAs for 33 venues are defined — add to SSOT index if missing
    status: todo
    note: ""

  # =====================================================================
  # PHASE 6: Cleanup + Docs
  # Depends on: Phase 5 human decisions made
  # =====================================================================
  - id: p6-verify-operation-details
    content: |
      - [ ] [AGENT] P1. Verify all 77 operation_details entries match actual adapter implementations — cross-reference signing_scheme and required_credential
    status: todo
    note: ""

  - id: p6-hl-missing-ops
    content: |
      - [ ] [AGENT] P2. Add missing Hyperliquid operations to capability (spot_transfer, approve_agent, approve_builder_fee — from SDK signing.py)
    status: todo
    note: ""

  - id: p6-base-url-drift
    content: |
      - [ ] [AGENT] P2. Verify base_urls match CCXT sandbox URLs and testnet_contracts.yaml addresses — no drift between registries
    status: todo
    note: ""

  - id: p6-codex-docs
    content: |
      - [ ] [AGENT] P1. Update unified-trading-codex with operation capability registry docs — signing schemes, credential types, how to add a venue, how validate_operation() works
    status: todo
    note: ""

  # =====================================================================
  # PHASE 7: DeFi Secrets + Testnet (HUMAN — blocks Phases 8-10)
  # SEE ALSO: defi-keys-data-integration-2026-03-13 Phase 1
  # =====================================================================
  - id: p7-secrets-hl-done
    content: |
      - [x] [HUMAN] P0. Load Hyperliquid mainnet + testnet API keys into Secret Manager (hyperliquid-trade-key, hyperliquid-testnet-trade-key)
    status: done
    note: "Completed 2026-03-17. Mainnet: 0x6C00..., Testnet: 0x4f68... Both verified via address derivation."

  - id: p7-secrets-tier1
    content: |
      - [x] [HUMAN] P0. Tier 1 secrets already in Secret Manager: alchemy-api-key (Nov 2025), thegraph-api-key x9 (Nov 2025/Jan 2026), graph-api-key (Nov 2025). Only missing: wallet-private-key for on-chain DeFi signing.
    status: done
    note: "Verified 2026-03-17 via gcloud secrets list. Previously listed as needed — was wrong, already existed."

  - id: p7-secrets-tier2
    content: |
      - [x] [HUMAN] P1. Tier 2 secrets already in Secret Manager: aavescan-api-key (Nov 2025), tardis-api-key (Oct 2025) + backup + full variants.
    status: done
    note: "Verified 2026-03-17 via gcloud secrets list. Previously listed as needed — was wrong, already existed."

  - id: p7-secrets-tier3
    content: |
      - [ ] [HUMAN] P2. Load Tier 3 secrets: infura-api-key, bloxroute-api-key, pyth-api-key, tenderly-fork-rpc-url (Week 2)
    status: todo
    note: "SEE defi-keys-data-integration-2026-03-13 Phase 1"

  - id: p7-testnet-hl-done
    content: |
      - [x] [HUMAN] P0. Fund Hyperliquid testnet — faucet claim, API key creation, order lifecycle verified
    status: done
    note: "Completed 2026-03-17. 999 USDC on testnet. Place/cancel order tested successfully via SDK signing."

  - id: p7-testnet-sepolia
    content: |
      - [ ] [HUMAN] P1. Get Sepolia ETH from faucet (~1 ETH for gas) for on-chain DeFi testnet
    status: todo
    note: ""

  - id: p7-confirm-wallet
    content: |
      - [x] [HUMAN] P0. Confirmed: same wallet for testnet+mainnet. Chain priority: Ethereum + Arbitrum (Hyperliquid L1 on Arbitrum).
    status: done
    note: "Decided 2026-03-17. Wallet: 0x992ebFe04DB05f964C45BCE3D73Ca4c81715a79f for both envs."

  # =====================================================================
  # PHASE 8: VCR Cassette Recording (needs Tier 1 secrets)
  # SEE ALSO: defi-keys-data-integration-2026-03-13 Phase 2
  # Depends on: Phase 7 Tier 1 secrets loaded
  # =====================================================================
  - id: p8-vcr-confirm
    content: |
      - [x] [HUMAN] P0. Confirmed: mainnet reads + testnet writes. If no testnet exists, real mainnet only if required (not optional).
    status: done
    note: "Decided 2026-03-17."

  - id: p8-vcr-priority-a
    content: |
      - [ ] [AGENT] P0. Record 9 strategy-blocking cassettes — HL user_state/funding/l2_book/candle/ticker + TheGraph Aave+Uniswap + DefiLlama TVL+yields
    status: todo
    note: "SEE defi-keys-data-integration-2026-03-13 Phase 2 for full endpoint list"

  - id: p8-vcr-priority-b
    content: |
      - [ ] [AGENT] P0. Record 5 execution-blocking cassettes — HL order/fill/open_order (testnet) + Alchemy getReserveData/getUserAccountData
    status: todo
    note: ""

  - id: p8-vcr-priority-c
    content: |
      - [ ] [AGENT] P2. Record remaining stubs across 14 DeFi protocols
    status: todo
    note: ""

  # =====================================================================
  # PHASE 9: DeFi Feature Calculators (P0 — blocks strategy-service)
  # Depends on: Phase 7 secrets + Phase 8 cassettes for testing
  # =====================================================================
  - id: p9-feature-aave-supply-apy
    content: |
      - [ ] [AGENT] P0. Build aave_supply_apy calculator in features-onchain-service (reads Alchemy RPC → publishes to Pub/Sub)
    status: todo
    note: ""

  - id: p9-feature-aave-utilization
    content: |
      - [ ] [AGENT] P0. Build aave_utilization calculator in features-onchain-service
    status: todo
    note: ""

  - id: p9-feature-aave-liquidity-index
    content: |
      - [ ] [AGENT] P0. Build aave_liquidity_index calculator in features-onchain-service
    status: todo
    note: ""

  - id: p9-feature-lst
    content: |
      - [ ] [AGENT] P0. Build lst_staking_apy + weeth_rate calculators in features-onchain-service (EtherFi)
    status: todo
    note: ""

  - id: p9-feature-health-factor
    content: |
      - [ ] [AGENT] P0. Build health_factor calculator in features-onchain-service (Aave V3)
    status: todo
    note: ""

  - id: p9-feature-funding-verify
    content: |
      - [ ] [AGENT] P1. Verify funding_rate already works for Hyperliquid via features-delta-one-service CeFi path
    status: todo
    note: ""

  # =====================================================================
  # PHASE 10: DeFi Execution + UI + Alerting (PARALLEL)
  # Depends on: Phase 9 features working
  # =====================================================================
  - id: p10-web3-signing
    content: |
      - [ ] [AGENT] P0. Wire Web3 transaction signing + broadcast for on-chain execution (Aave supply/borrow/repay, Uniswap swap) — needs wallet-private-key in SM
    status: todo
    note: ""

  - id: p10-confirm-mode
    content: |
      - [x] [HUMAN] P0. Confirmed: testnet first, THEN paper trading. Paper trading live = simulated fills on real data + order simulation (no real execution).
    status: done
    note: "Decided 2026-03-17."

  - id: p10-confirm-ui
    content: |
      - [x] [HUMAN] P1. Confirmed: skip DeFi UI for now — UI refactor in progress. Revisit after refactor.
    status: done
    note: "Decided 2026-03-17. UI plan: ui-platform-redesign-2026-03-17."

  - id: p10-ui-wire
    content: |
      - [x] [AGENT] P1. SKIPPED — DeFi UI wiring deferred per human decision. UI refactor in progress.
    status: done
    note: "Deferred 2026-03-17."

  - id: p10-alert-p0
    content: |
      - [ ] [AGENT] P0. Wire P0 DeFi alerts — health_factor < 1.2, weETH depeg > 2%
    status: todo
    note: ""

  - id: p10-alert-p1
    content: |
      - [ ] [AGENT] P1. Wire P1 DeFi alerts — Aave utilization > 95%, funding rate flip, feature staleness > 2x SLA
    status: todo
    note: ""

  - id: p10-confirm-alerting
    content: |
      - [x] [HUMAN] P1. Confirmed: Telegram for DeFi alerts for now.
    status: done
    note: "Decided 2026-03-17."

  # =====================================================================
  # PHASE 11: Historical Data Backfill (Day 2)
  # SEE ALSO: defi-keys-data-integration-2026-03-13 Phase 4
  # Depends on: Phase 9 features working + Phase 7 Tardis key
  # =====================================================================
  - id: p11-backfill-hl
    content: |
      - [ ] [AGENT] P1. Backfill Hyperliquid trades — Tardis (2024-10→2025-03) + S3 archive (2025-03+)
    status: todo
    note: "SEE defi-keys-data-integration-2026-03-13 Phase 4"

  - id: p11-backfill-aave
    content: |
      - [ ] [AGENT] P1. Backfill Aave rates/indices — TheGraph + Alchemy (~1 year hourly)
    status: todo
    note: ""

  - id: p11-backfill-uniswap-lst
    content: |
      - [ ] [AGENT] P2. Backfill Uniswap pool data + weETH/stETH rates
    status: todo
    note: ""

  - id: p11-backfill-features
    content: |
      - [ ] [AGENT] P2. Compute features over backfilled data via features-onchain-service
    status: todo
    note: ""

isProject: false
---

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
