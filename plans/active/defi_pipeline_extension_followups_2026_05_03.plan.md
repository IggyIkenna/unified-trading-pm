---
locked_by: live-defi-rollout
locked_since: 2026-05-03
plan_type: mixed
asset_group: defi
owner: ikenna
created: 2026-05-03
name: defi-pipeline-extension-followups-2026-05-03
overview:
  Closeout follow-ups to the defi_pipeline_extension Phase 8 ship — calculator fetch_data wiring, target-universe seed
  slots for the 6 new archetypes, instruments-service + MTDS adapters for the 12 new chains and 5 new lending protocols,
  and CODEX ratchet floors back down
type: mixed
epic: epic-code-completion
status: active
completion_gates:
  code: C5
  deployment: D2
  business: B3
repo_gates:
  - repo: market-tick-data-service
    code: C0
    deployment: none
    business: none
  - repo: features-onchain-service
    code: C0
    deployment: none
    business: none
  - repo: execution-service
    code: C0
    deployment: none
    business: none
  - repo: strategy-service
    code: C0
    deployment: none
    business: none
  - repo: instruments-service
    code: C0
    deployment: none
    business: none
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none
depends_on:
  - defi_pipeline_extension_2026_05_01
isProject: false
---

# DeFi Pipeline Extension — Follow-ups Closeout

## Why this plan exists

The defi_pipeline_extension Phase 8 ship landed 14 archetypes (8 existing

- 6 new), 4 features-onchain calculators, the LiquidationFlashLoanReceiver contract, real LP mint/burn + atomic-bundle
  e2e on Tenderly forks, and the MTDS dex_pools handler V3 sqrt_price + tick capture. Six explicit gaps remain — none
  blocking, all surfaced as ratchet targets in the per-repo `quality-gates.sh` files or as `assert missing == {…}` gap
  sets in the strategy-service tests:

1. **Calculator fetch_data() wiring** — concentrated_liquidity_il_realised / pool_invariant_drift /
   vault_share_price_apy stubs return empty until defi_lateral_loader exposes the corresponding feeds.
2. **Target universe seed slots** for the 6 new archetypes (DEFI_LP_CONCENTRATED/POOL/VAULT,
   ARBITRAGE_MEV_BUNDLE/JIT/BACKRUN) — tracked via the explicit gap set in `test_every_v1_archetype_represented`.
3. **Legacy strategy mapping** seeding for the 6 archetypes — greenfield, no legacy code; tracked in
   `test_archetype_coverage_matches_expectation`.
4. **instruments-service adapters** for FLUID / EULER_V2 / RADIANT / VENUS / BENQI — UAC declarations shipped in
   `56e79eb`, adapters not wired.
5. **MTDS chain adapters** for the 12 alt-L1 chains added in `56e79eb` (MANTLE / AURORA / CELO / FANTOM / METIS /
   MOONBEAM + 6 already-on-Alchemy wired via existing onchain.evm framework) — Phase 6.5 of the parent plan.
6. **CODEX ratchet floors** — features-onchain held at 8 (chain*event* scanners 3 oversize methods + 2 sibling-session
   imports); execution-service held at 23 (STEP 5.12b hardcoded cloud URIs).

## Pre-audit manifest

### Calculator fetch_data wiring

- `features-onchain-service/features_onchain_service/app/calculators/concentrated_liquidity_il_realised_calculator.py` —
  `fetch_data()` returns empty; needs
  `defi_lateral_loader.load_date_range(DefiFeedSpec(feed="dex_pools", venue="UNISWAP_V3", chain=..., instrument_type="lp", data_type="dex_pools"), start, end)` +
  per-pool filter.
- `pool_invariant_drift_calculator.py` — same pattern for Curve / Balancer pools.
- `vault_share_price_apy_calculator.py` — needs new `vault_share_price` data type in UAC
  `DATA_TYPES_BY_ASSET_GROUP['defi']` + `defi_lateral_loader` bucket entry + new MTDS handler that pulls ERC-4626 share
  prices from on-chain.
- `block_priority_gas_distribution_calculator.py` — `gas_fees` feed already in `DEFAULT_LATERAL_BUCKETS`; just needs the
  per-tx variant pulled (the existing lateral_loader returns aggregate gas data, not per-tx priority fees).

### Target universe + legacy mapping

- `strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog.py` (or wherever `TARGET_UNIVERSE`
  lives) — add seed slots for the 6 new archetypes per share-class.
- `strategy-service/.../legacy_strategy_mapping.py` — add empty-legacy entries for greenfield archetypes OR drop them
  from the assert by promoting them to a "no-legacy expected" set.

### instruments-service adapters

- `instruments-service/instruments_service/protocols/` — add `fluid.py`, `euler_v2.py`, `radiant.py`, `venus.py`,
  `benqi.py` mirroring the existing `aave_v3.py` shape (read positions / lending rates / TVL via The Graph subgraphs or
  direct RPC for protocols without subgraphs).
- UAC subgraph IDs for these 5 protocols already declared in
  `unified_api_contracts/registry/capability_declarations/_defi.py` (verify and extend if missing).

### MTDS chain adapters

- `market-tick-data-service/market_tick_data_service/adapters/onchain/evm/` — extend the EVM adapter framework's chain
  list to include MANTLE / AURORA / CELO / FANTOM / METIS / MOONBEAM (+ verify BSC, GNOSIS, BLAST, MODE, LINEA,
  AVALANCHE which are on Alchemy already work).
- Per-chain RPC endpoints already in UAC `CHAIN_RPC_TEMPLATES` (commit `56e79eb`).
- Reorg depth + block-time configs need per-chain entries.

### CODEX ratchet

- `features-onchain-service/features_onchain_service/collectors/chain_event_scanners.py` — 3 methods over 50L:
  - `EtherscanChainEventScanner.scan_distributor_transfers()` — 60L
  - `SolanaChainEventScanner.scan_distributor_transfers()` — 52L
  - `SolanaChainEventScanner._extract_spl_transfers()` — 68L Refactor: extract per-chunk loop bodies into private
    helpers.
- `execution-service/.../*.py` — STEP 5.12b hardcoded cloud URIs flagged ~6 sites. Each needs
  `UCI StorageClient.{download_bytes,upload_bytes, list_blobs}` instead of inline `gs://...` strings.

## Phased execution DAG

```
Phase 1 — Calculator fetch_data wiring (PARALLEL within phase)
   ├─ 1.1 [PARALLEL] Add ``vault_share_price`` data type to UAC + lateral_loader bucket
   ├─ 1.2 [PARALLEL] Wire concentrated_liquidity_il_realised.fetch_data → dex_pools feed
   ├─ 1.3 [PARALLEL] Wire pool_invariant_drift.fetch_data → dex_pools feed (Curve + Balancer)
   ├─ 1.4 [SEQUENTIAL on 1.1] Wire vault_share_price_apy.fetch_data → vault_share_price feed
   ├─ 1.5 [PARALLEL] Wire block_priority_gas_distribution.fetch_data → gas_fees feed (per-tx variant)
   └─ 1.6 GATE — features-onchain QG green; ratchet MIN_COVERAGE 63 → 66

Phase 2 — MTDS handlers for missing feeds (SEQUENTIAL after Phase 1.1)
   ├─ 2.1 New ``vault_share_price_handler.py`` — per-vault ERC-4626 share-price snapshots
   │      (Yearn V3, Morpho, Aave Vaults, Sommelier, MetaMorpho — top 40 vaults)
   └─ 2.2 GATE — MTDS QG green; smoke-test handler against staging GCS bucket

Phase 3 — Target universe + legacy seeding (PARALLEL within phase, SEQUENTIAL after Phase 1)
   ├─ 3.1 [PARALLEL] Add target slots for 6 archetypes (per share class — operator picks counts)
   ├─ 3.2 [PARALLEL] Drop the 6 archetypes from the "no-legacy" gap set OR seed empty rows
   ├─ 3.3 GATE — strategy-service QG green; tighten test_every_v1_archetype_represented +
   │      test_archetype_coverage_matches_expectation back to ``missing == set()`` /
   │      ``missing == {CARRY_BASIS_DATED, STAT_ARB_CROSS_SECTIONAL}`` only

Phase 4 — instruments-service adapters (PARALLEL within phase)
   ├─ 4.1 [PARALLEL] FLUID adapter (5 chains: ETHEREUM/ARBITRUM/BASE/OPTIMISM/POLYGON)
   ├─ 4.2 [PARALLEL] EULER_V2 adapter (ETHEREUM/ARBITRUM)
   ├─ 4.3 [PARALLEL] RADIANT adapter (ETHEREUM/ARBITRUM/BSC)
   ├─ 4.4 [PARALLEL] VENUS adapter (BSC/ETHEREUM)
   ├─ 4.5 [PARALLEL] BENQI adapter (AVALANCHE)
   └─ 4.6 GATE — instruments-service QG green; smoke-test adapter for one chain per protocol

Phase 5 — MTDS chain adapters for 12 alt-L1s (PARALLEL within phase)
   ├─ 5.1 [PARALLEL] Verify already-on-Alchemy chains (BSC/AVALANCHE/LINEA/BLAST/MODE/GNOSIS) flow
   │      end-to-end via existing onchain.evm framework — no new code if the framework
   │      iterates ``CHAIN_RPC_TEMPLATES`` keys directly.
   ├─ 5.2 [PARALLEL] Wire MANTLE / AURORA / CELO / FANTOM / METIS / MOONBEAM via public RPCs
   │      (UAC ``CHAIN_RPC_TEMPLATES`` ships them; framework just needs to register them as
   │      iterated chain candidates).
   ├─ 5.3 [PARALLEL] Per-chain reorg depth + block-time configs (UAC ``CHAIN_RPC_TEMPLATES`` may
   │      need expansion to a typed ``ChainConfig`` rather than a flat dict[int, str] of URLs).
   └─ 5.4 GATE — MTDS QG green; smoke 1 block / chain capture per chain on staging.

Phase 6 — CODEX ratchet ratchet-down (PARALLEL within phase)
   ├─ 6.1 [PARALLEL] Refactor chain_event_scanners.py — split 3 oversize methods (~60L each →
   │      ≤50L each via per-chunk helper extraction)
   ├─ 6.2 [PARALLEL] STEP 5.12b cleanup in execution-service — replace inline ``gs://...``
   │      strings with UCI StorageClient calls (~6 sites)
   └─ 6.3 GATE — features-onchain CODEX_MAX_VIOLATIONS 8 → 1 (original floor);
                 execution-service 23 → 22 or lower (delta = sites cleaned up)

Phase 7 — Closeout (SEQUENTIAL after all phases)
   ├─ 7.1 Workspace QG sweep across all 7 repos
   ├─ 7.2 Memory: project_defi_pipeline_extension_followups_closeout_2026_05_03.md
   ├─ 7.3 Update parent plan (defi_pipeline_extension_2026_05_01.plan.md) — flip
   │      remaining ``[ ]`` todos to ``[x]`` for items this plan resolves
   └─ 7.4 GATE — all repo_gates at C5; plan eligible for archive
```

## Success criteria

| Phase | Code Gate                                         | Deployment Gate | Business Gate                                       |
| ----- | ------------------------------------------------- | --------------- | --------------------------------------------------- |
| 1     | C5 (features-onchain + UAC + MTDS lateral_loader) | D2              | B3 — calculate_features() now ingests live data     |
| 2     | C5 (MTDS)                                         | D2              | B3 — vault_share_price feed populates manifest      |
| 3     | C5 (strategy-service)                             | none            | B1 — TARGET_UNIVERSE catalogues all 24 archetypes   |
| 4     | C5 (instruments-service)                          | none            | B1 — 5 new lending protocols readable from manifest |
| 5     | C5 (MTDS)                                         | D2              | B3 — 12 chains' instruments + market data captured  |
| 6     | C3 (lint/codex green)                             | none            | none                                                |
| 7     | C5 all                                            | D2 all          | B3 all                                              |

## Risks & mitigations

| Risk                                                                                 | Mitigation                                                                                                                     |
| ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| ERC-4626 vault discovery is open-ended (1000s of vaults)                             | Cap at top-40 by TVL via DefiLlama Yields filter (existing pattern from `aave_lending_calculator.py`)                          |
| Public RPC rate limits on the 6 alt-L1 chains                                        | Implement existing singleton-launcher pattern; switch to QuickNode / Alchemy paid tiers via Secret Manager when load justifies |
| Reorg depth differs across chains                                                    | Per-chain `ChainConfig` schema in UAC; conservative defaults (5 blocks for L2s, 12 for ETH-mainnet, 50 for BSC)                |
| Phase 5 chain expansion cascades into instruments-service expectations not yet wired | Phase 4 + 5 marked parallel — both lands together                                                                              |
| target_universe seed-slot counts are operator judgment, not engineering              | Phase 3.1 marked AGENT-asks — plan stops for operator input on slot counts per share class before continuing                   |

## What this plan does NOT do

- Does NOT add the live MEV sandwich engine — gated on the separate `mempool_feed_integration_2026_06_01.plan.md` stub
  (still paused).
- Does NOT extend coverage to non-EVM chains beyond Solana — Bitcoin / Cosmos / Polkadot are out of scope until the
  business case clears.
- Does NOT add new data types to MTDS beyond `vault_share_price` — the existing `dex_pools` / `gas_fees` taxonomy covers
  everything else.
- Does NOT touch UAC enum surface beyond the `vault_share_price` data type add — no new InstructionAction /
  StrategyArchetype values.

## Todos

### Phase 1 — Calculator fetch_data wiring

- id: p1-1-vault-data-type content: |
  - [ ] [AGENT] P0. Add `vault_share_price` to UAC `DATA_TYPES_BY_ASSET_GROUP['defi']` + a `vault-share-price-{project}`
        bucket entry in `defi_lateral_loader.DEFAULT_LATERAL_BUCKETS`. Includes a corresponding
        `DefiFeedSpec(feed="vault_share_price", venue=<vault_protocol>, chain=...)` schema convention. status: todo
- id: p1-2-concentrated-fetch content: |
  - [ ] [AGENT] P0. Wire `ConcentratedLiquidityIlRealisedCalculator.fetch_data()` to pull from `dex_pools` lateral feed
        for UNISWAP_V3 venue across all chains in CHAIN_RPC_TEMPLATES. Filter by pool_address from per-strategy params;
        group by (pool_address, day) for the annualised drift calculation. status: todo
- id: p1-3-pool-invariant-fetch content: |
  - [ ] [AGENT] P0. Wire `PoolInvariantDriftCalculator.fetch_data()` to pull from `dex_pools` for CURVE + BALANCER
        venues. Detect pool_type from venue (CURVE → CURVE_STABLE; BALANCER → BALANCER_WEIGHTED) and pass through to
        `calculate_features()`. status: todo
- id: p1-4-vault-fetch content: |
  - [ ] [AGENT] P0. Wire `VaultSharePriceApyCalculator.fetch_data()` to pull from `vault_share_price` feed (added in
        1.1). Sequential after 1.1. status: todo
- id: p1-5-priority-gas-fetch content: |
  - [ ] [AGENT] P0. Wire `BlockPriorityGasDistributionCalculator.fetch_data()` to pull per-tx `gas_fees` rows. Existing
        lateral_loader bucket already in place; verify the schema includes `priority_fee_gwei` per row (not just
        aggregate). status: todo
- id: p1-6-gate content: |
  - [ ] [AGENT] P0. GATE — cd features-onchain-service && bash scripts/quality-gates.sh passes; ratchet MIN_COVERAGE
        from 63 to 66 (original floor). status: todo

### Phase 2 — MTDS vault_share_price handler

- id: p2-1-vault-handler content: |
  - [ ] [AGENT] P0. New `market-tick-data-service/.../cli/handlers/vault_share_price_handler.py` mirroring the existing
        `flash_loan_events_handler.py` pattern: pulls top-40 ERC-4626 vaults by TVL via DefiLlama Yields, reads
        `totalAssets()` + `totalSupply()` per vault per day via multicall, writes to canonical
        `raw_tick_data/by_date/day=…/asset_group=defi/venue={VENUE}-{CHAIN}/instrument_type=vault/data_type=vault_share_price/ticks.parquet`.
        Manifest recorder + record_captured/record_empty/record_failed per vault. status: todo
- id: p2-2-gate content: |
  - [ ] [AGENT] P0. GATE — cd market-tick-data-service && bash scripts/quality-gates.sh passes; smoke launch on 1 chain
        × 1 day on staging VM (~5 min); verify parquet lands in canonical path + manifest row gets `captured` status.
        status: todo

### Phase 3 — Target universe + legacy seeding

- id: p3-1-target-slots-operator content: |
  - [ ] [AGENT] P1. Operator-input gate: ASK for slot counts per (archetype, share-class) for the 6 new archetypes.
        Default seed proposal: 1 slot per archetype × USDC share class to start (6 new TARGET_UNIVERSE rows), expand per
        business need. Operator confirms before ship. status: todo
- id: p3-2-target-add-rows content: |
  - [ ] [AGENT] P1. After 3.1 confirmed: add the agreed slots to TARGET_UNIVERSE; tighten
        `test_every_v1_archetype_represented` back to `assert missing == set()`. status: todo
- id: p3-3-legacy-seed content: |
  - [ ] [AGENT] P1. For the 6 greenfield archetypes: drop them from the "permitted gap" set in
        `test_archetype_coverage_matches_expectation` and instead promote them into a new `GREENFIELD_ARCHETYPES` set in
        `archetype_defaults.py` that the test asserts against separately. The original gap set tightens back to
        `{CARRY_BASIS_DATED, STAT_ARB_CROSS_SECTIONAL}`. status: todo
- id: p3-4-gate content: |
  - [ ] [AGENT] P1. GATE — cd strategy-service && bash scripts/quality-gates.sh passes. status: todo

### Phase 4 — instruments-service adapters

- id: p4-1-fluid content: |
  - [ ] [AGENT] P2. instruments-service: FLUID adapter mirroring aave_v3.py shape. 5 chains
        (ETHEREUM/ARBITRUM/BASE/OPTIMISM/POLYGON). status: todo
- id: p4-2-euler-v2 content: |
  - [ ] [AGENT] P2. EULER_V2 adapter (ETHEREUM/ARBITRUM). status: todo
- id: p4-3-radiant content: |
  - [ ] [AGENT] P2. RADIANT adapter (ETHEREUM/ARBITRUM/BSC). status: todo
- id: p4-4-venus content: |
  - [ ] [AGENT] P2. VENUS adapter (BSC/ETHEREUM). Compound-fork pattern. status: todo
- id: p4-5-benqi content: |
  - [ ] [AGENT] P2. BENQI adapter (AVALANCHE). Compound-fork pattern. status: todo
- id: p4-6-gate content: |
  - [ ] [AGENT] P2. GATE — cd instruments-service && bash scripts/quality-gates.sh passes; smoke 1 chain per protocol on
        staging. status: todo

### Phase 5 — MTDS chain adapters for 12 alt-L1s

- id: p5-1-already-on-alchemy content: |
  - [ ] [AGENT] P2. Verify BSC / AVALANCHE / LINEA / BLAST / MODE / GNOSIS flow end-to-end via the existing onchain.evm
        framework. If the framework iterates `CHAIN_RPC_TEMPLATES.keys()` directly, no new code; if it has a hardcoded
        chain list, extend it. status: todo
- id: p5-2-public-rpc-chains content: |
  - [ ] [AGENT] P2. Wire MANTLE / AURORA / CELO / FANTOM / METIS / MOONBEAM. The `CHAIN_RPC_TEMPLATES` entries shipped
        in commit `56e79eb` are public-RPC URLs (api_key substitution is a no-op). Verify the framework's RPC client
        tolerates URLs without `{api_key}` placeholders. status: todo
- id: p5-3-chain-config content: |
  - [ ] [AGENT] P2. UAC `CHAIN_RPC_TEMPLATES` schema lift from `dict[int, str]` to `dict[int, ChainConfig]` with fields:
        `rpc_url`, `reorg_depth`, `avg_block_time_s`, `native_gas_token`. Per-chain values seeded from chain docs
        (ETH=12, BSC=50, MANTLE=10s). All current callers updated in the same PR. status: todo
- id: p5-4-gate content: |
  - [ ] [AGENT] P2. GATE — cd market-tick-data-service && bash scripts/quality-gates.sh passes; smoke 1 block / chain
        capture per chain on staging. status: todo

### Phase 6 — CODEX ratchet floors

- id: p6-1-scanner-refactor content: |
  - [ ] [AGENT] P2. Refactor `features_onchain_service/collectors/chain_event_scanners.py`: split
        `EtherscanChainEventScanner.scan_distributor_transfers` (60L),
        `SolanaChainEventScanner.scan_distributor_transfers` (52L), and `SolanaChainEventScanner._extract_spl_transfers`
        (68L) into per-chunk private helpers. Target ≤50L per method per workspace standard. status: todo
- id: p6-2-cloud-uri-cleanup content: |
  - [ ] [AGENT] P2. STEP 5.12b cleanup in execution-service: replace inline `gs://…` strings with
        `UCI StorageClient.{download_bytes,upload_bytes,list_blobs}` calls. ~6 sites identified by the QG run. status:
        todo
- id: p6-3-ratchet-down content: |
  - [ ] [AGENT] P2. After 6.1: ratchet features-onchain `CODEX_MAX_VIOLATIONS` 8 → 1 (original floor). After 6.2:
        ratchet execution-service `CODEX_MAX_VIOLATIONS` 23 → max(0, 23 - sites_cleaned). Both ratchets are atomic with
        their respective refactor commits. status: todo

### Phase 7 — Closeout

- id: p7-1-workspace-qg content: |
  - [ ] [AGENT] P2. Run `bash scripts/quality-gates.sh` across all 7 repo_gates repos. All green. status: todo
- id: p7-2-memory-closeout content: |
  - [ ] [AGENT] P2. Memory: `project_defi_pipeline_extension_followups_closeout_2026_05_03.md` summarising commits per
        repo + key decisions. Update INDEX. status: todo
- id: p7-3-parent-plan-flip content: |
  - [ ] [AGENT] P2. Update `plans/active/defi_pipeline_extension_2026_05_01.plan.md` — flip remaining `[ ]` todos to
        `[x]` for items this plan resolves (Phase 4.1.c, 4.2.c, 4.3.c, 6.4, 6.5, 6.6 of the parent plan). status: todo
- id: p7-4-gate content: |
  - [ ] [AGENT] P2. GATE — all repo_gates at C5; plan eligible for archive. status: todo

## Resumption pointers

- The MTDS dex_pools handler V3 sqrt_price + tick capture (commit `c36f7f7`) already lands sqrt_price + tick in the
  parquet schema. Phase 1.2/1.3 just need to read those columns; no further MTDS work for the V3 family.
- The richer `LiquidationFlashLoanReceiver.sol` (deployment-service `3ab2989`) is deployed end-to-end on Tenderly fork;
  live mainnet deploy is a separate operator-driven step (deploy + record contract addresses in UAC
  `config/testnet_contracts.yaml` for execution-service preflight validation).
- Calculator parity tests (30 tests in `test_defi_pipeline_extension_calculators.py`) exercise the `calculate_features`
  paths but assume the input frame is supplied. After Phase 1 wires fetch_data, add 4 integration tests (one per
  calculator) that exercise the full `await calc.fetch_data(start, end)` → `calc.calculate_features(...)` round-trip
  against a staging GCS fixture.
