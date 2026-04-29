---
name: instruments-service-metadata-refactor-2026-04-29
overview:
  Extend InstrumentRecord with optional DeFi metadata fields, populate them in instruments-service adapters, refactor
  MTDS DeFi handlers to consume instruments-store-defi parquets instead of re-querying The Graph subgraphs each cycle.
type: code
epic: epic-code-completion
status: active
completion_gates:
  code: C5
  deployment: none
  business: none
repo_gates:
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: instruments-service
    code: C0
    deployment: none
    business: none
  - repo: market-tick-data-service
    code: C0
    deployment: none
    business: none
depends_on: []
isProject: false
todos:
  - id: phase-0-pre-audit-embedded
    content: |
      - [x] [HUMAN] P0. Pre-audit findings (from session 2026-04-29 audit)
        - InstrumentRecord (UAC) has 22 generic fields, all TradFi/CeFi-shaped (tick_size, expiry, strike, session times, etc.)
        - No fields for DeFi-specific contract metadata: pool_address, token_a/b_address, token_a/b_decimals, fee_bps, atoken_address, debt_token_address, contract_address, method_selector
        - instruments-service DeFi adapters DO query subgraphs that return these fields, but DROP them when mapping into InstrumentRecord
        - 4 of 8 main MTDS DeFi handlers can be refactored to consume instruments-store-defi: dex_pools, dex_swaps, lending_indices, liquidations
        - 2 of 8 are already correct (no refactor): oracle_prices (static Chainlink registry), lst_rates (static LST contract registry)
        - Phase-2 handlers (8 event-typed handlers) deferred — per-protocol metadata needs not yet enumerated
    status: done

  - id: phase-1-uac-schema-extension
    content: |
      - [ ] [AGENT] P0. Extend InstrumentRecord with optional DeFi metadata fields
        - File: unified-api-contracts/unified_api_contracts/internal/reference/instrument.py
        - Add optional fields (None default for non-DeFi venues):
          - contract_address: str | None — pool / reserve / vault / market address
          - token_a_address: str | None
          - token_a_decimals: int | None
          - token_a_symbol: str | None
          - token_b_address: str | None
          - token_b_decimals: int | None
          - token_b_symbol: str | None
          - fee_bps: int | None — DEX fee tier (Uniswap V3 fee, Balancer pool fee)
          - atoken_address: str | None — Aave aToken
          - debt_token_address: str | None — Aave variable-debt token
          - rate_method_selector: str | None — for static-registry LSTs (optional, for parity)
        - Update `__all__` exports through facade chain (registry/__init__.py, defi facade)
        - Add unit tests: empty defaults for TradFi/CeFi fixtures, populated for DeFi fixtures
        - QG: bash scripts/quality-gates.sh — must pass file-size cap, ruff, basedpyright
    status: todo

  - id: phase-2a-aave-v3-adapter
    content: |
      - [ ] [AGENT] P0. Aave V3 adapter emits aToken + debtToken + decimals
        - File: instruments-service/instruments_service/reference_data/adapters/defi/aave_v3.py
        - Subgraph query already returns these (lines ~44-62) — extract `aToken.id`, `vToken.id`, `decimals` and populate the new InstrumentRecord fields
        - Same approach for Compound V3, Spark, Morpho adapters
        - Tests: parquet round-trip preserves new fields; existing TradFi/CeFi adapters still emit None
    status: todo
    blocked_by: phase-1-uac-schema-extension

  - id: phase-2b-uniswap-balancer-curve-adapters
    content: |
      - [ ] [AGENT] P0. Uniswap V2/V3/V4 + Balancer + Curve adapters emit pool_address + token0/1 + fee_tier
        - Files: instruments_service/reference_data/adapters/defi/{uniswap_v2,v3,v4,balancer,curve,sushiswap}.py
        - Subgraph queries already return token0.id / token1.id / decimals / feeTier — extract
        - Populate: contract_address (pool id), token_a/b_address + decimals + symbol, fee_bps
        - Tests: round-trip preserves; coverage for each protocol
    status: todo
    blocked_by: phase-1-uac-schema-extension

  - id: phase-2c-eigenlayer-adapter
    content: |
      - [ ] [AGENT] P1. EigenLayer adapter (operator + strategy enumeration)
        - New file or extension of existing eigenlayer.py
        - Required by eigenlayer_rewards handler (currently no instruments-service source)
        - Lower priority — eigenlayer_rewards is small surface area
    status: todo
    blocked_by: phase-1-uac-schema-extension

  - id: phase-3-mtds-handler-refactor-dex
    content: |
      - [ ] [AGENT] P0. Refactor dex_pools_handler + dex_swaps_handler to consume instruments-store-defi
        - Files: market-tick-data-service/market_tick_data_service/cli/handlers/{dex_pools,dex_swaps}_handler.py
        - Add `_load_pool_metadata_from_instruments(venue, chain, date)` helper that reads gs://instruments-store-defi-{pid}/{venue}/{chain}/date={D}/instruments.parquet
        - Use the loaded pool_address + token0/1 + fee_bps for the time-series subgraph query (drop the dynamic discovery part)
        - Fallback to subgraph re-query if instruments parquet missing for date (graceful degradation, log warning)
        - Tests: mock GCS read returns N pools, handler queries subgraph time-series only with those addresses
    status: todo
    blocked_by: phase-2b-uniswap-balancer-curve-adapters

  - id: phase-3-mtds-handler-refactor-lending
    content: |
      - [ ] [AGENT] P0. Refactor lending_indices_handler + liquidations_handler to consume instruments-store-defi
        - Files: market-tick-data-service/market_tick_data_service/cli/handlers/{lending_indices,liquidations}_handler.py
        - Same pattern as dex handler refactor
        - Tests: mock GCS read returns N reserves, handler queries indices/liquidation time-series only
    status: todo
    blocked_by: phase-2a-aave-v3-adapter

  - id: phase-4-cohesion-validation
    content: |
      - [ ] [AGENT] P0. Parity validation between subgraph and instruments-emitted metadata
        - Build a one-shot script that: for each (venue, chain, date) in instruments-store-defi, fetches the same metadata via subgraph and diffs
        - Acceptance: 100% match for pool_address / token0/1 / fee_bps / decimals on the latest 30 days
        - Catches drift where adapters serialise stale data (e.g., subgraph adds a new pool same day but adapter ran earlier)
        - Document in plan: maximum tolerable lag between adapter run and MTDS handler run (e.g., < 1 day)
    status: todo
    blocked_by: phase-3-mtds-handler-refactor-dex

  - id: phase-5-deployment-api-compat
    content: |
      - [ ] [AGENT] P1. Verify deployment-api data-status still works
        - Backwards-compat check: existing instruments-store-defi parquets without new fields should still be readable
        - InstrumentRecord additions are all Optional[None] so no schema break
        - data-status reader (deployment-api) doesn't index new fields, so no UI-side change required
    status: todo
    blocked_by: phase-3-mtds-handler-refactor-dex

  - id: phase-6-defer-static-registry-handlers
    content: |
      - [x] [HUMAN] P0. NOT REFACTORED — oracle_prices + lst_rates
        - Chainlink feeds are static UAC registry-driven (CHAINLINK_FEEDS_BY_CHAIN); no dynamic discovery from instruments-service would help
        - LST contracts (Lido, RocketPool, etc.) are static, hardcoded in lst_rates_handler.py:_LST_TOKENS
        - Decision: Keep both as-is. Adding instruments-service emission for these would duplicate maintenance burden.
        - Cross-link: UAC LST_TOKEN_GENESIS + LST_VENUE_TO_TOKENS already SSOT for these (committed in 56ff55a, 04f2c55)
    status: done

  - id: phase-7-phase-2-handlers-deferred
    content: |
      - [ ] [HUMAN] P2. Phase-2 event-typed handlers (8 handlers)
        - liquidation_events, flash_loan_events, staking_yields, position_data, token_transfers, bridge_events, governance_events, mev_events
        - Per-protocol metadata needs not yet enumerated
        - Each handler currently re-queries protocol-specific subgraphs
        - Deferred until Phase-1 + Phase-2 + Phase-3 of this plan land and we have a working refactor template
        - Open questions: do these warrant own InstrumentRecord fields, or a sibling DefiEventMetadata model?
    status: todo

  - id: phase-8-final-qg
    content: |
      - [ ] [SCRIPT] P0. Workspace QG validation
        - cd unified-api-contracts && bash scripts/quality-gates.sh
        - cd instruments-service && bash scripts/quality-gates.sh
        - cd market-tick-data-service && bash scripts/quality-gates.sh
        - All green → C5 reachable for the 3 repos
    status: todo
    blocked_by: phase-4-cohesion-validation
---

# instruments-service → MTDS metadata refactor

## Why

MTDS DeFi handlers currently re-query subgraphs/RPCs each cycle for instrument metadata (pool addresses, token decimals,
fee tiers, reserve addresses). instruments-service runs the same protocol adapters daily and writes to
`gs://instruments-store-defi-{pid}/...`, but its `InstrumentRecord` schema is TradFi/CeFi-shaped and DROPS the
DeFi-specific fields. The result: ~50% redundant TheGraph compute-unit consumption per pipeline cycle.

This plan extends `InstrumentRecord` with optional DeFi metadata fields, populates them in the per-protocol adapters,
and refactors 4 MTDS handlers (dex_pools, dex_swaps, lending_indices, liquidations) to consume them. `oracle_prices` and
`lst_rates` are intentionally left as-is (static-registry by design, no dynamic discovery benefit).

## Phased execution DAG

```
Phase 1 (UAC schema)
    │
    ├─→ Phase 2a (Aave V3 / Compound V3 / Spark / Morpho adapters) ─┐
    │                                                                 │
    ├─→ Phase 2b (Uniswap V2/V3/V4 / Balancer / Curve adapters)  ───┤
    │                                                                 │
    └─→ Phase 2c (EigenLayer adapter, P1)                            │
                                                                      │
                                          Phase 3 (MTDS handler refactor — dex + lending)
                                                                      │
                                                            Phase 4 (Cohesion validation)
                                                                      │
                                                            Phase 5 (deployment-api compat)
                                                                      │
                                                                Phase 8 (Workspace QG)
```

Phase 6 (oracle_prices / lst_rates skip) and Phase 7 (Phase-2 handlers deferred) run out-of-band — no blocker on this
plan's main path.

## Pre-audit manifest

Audit completed 2026-04-29. Findings embedded in todo `phase-0-pre-audit-embedded`.

Key file paths to extend:

| Repo                | File                                                                                              | Action                                                                                                              |
| ------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| UAC                 | `unified_api_contracts/internal/reference/instrument.py`                                          | Add 11 optional DeFi fields to `InstrumentRecord`                                                                   |
| UAC                 | `unified_api_contracts/registry/__init__.py`                                                      | Re-export if any new helpers added                                                                                  |
| instruments-service | `instruments_service/reference_data/adapters/defi/aave_v3.py`                                     | Populate `atoken_address`, `debt_token_address`, `decimals` from existing subgraph response                         |
| instruments-service | `instruments_service/reference_data/adapters/defi/{uniswap_v2,v3,v4,balancer,curve,sushiswap}.py` | Populate `contract_address`, `token_a/b_*`, `fee_bps` from existing subgraph response                               |
| MTDS                | `market_tick_data_service/cli/handlers/dex_pools_handler.py`                                      | New `_load_pool_metadata_from_instruments()` helper; replace dynamic discovery; subgraph query only for time-series |
| MTDS                | `market_tick_data_service/cli/handlers/dex_swaps_handler.py`                                      | Same pattern                                                                                                        |
| MTDS                | `market_tick_data_service/cli/handlers/lending_indices_handler.py`                                | Same pattern                                                                                                        |
| MTDS                | `market_tick_data_service/cli/handlers/liquidations_handler.py`                                   | Same pattern                                                                                                        |

## Success criteria

- **C5**: All 3 repos green QG, PRs merged to live-defi-rollout
- **Functional**: 4 refactored MTDS handlers query the subgraph only for time-series data; metadata reads come from
  instruments-store-defi parquets
- **Parity gate**: Phase 4 cohesion script reports 100% match between subgraph and instruments-emitted metadata across
  the latest 30 days
- **No regression**: existing instruments-store-defi parquets without the new fields are still readable (Optional[None]
  backwards-compat)
- **Observability**: per-handler subgraph CU usage drops by ~50% (one query per cycle vs two before — instrument list
  query removed)

## Out-of-scope (separate plans)

- Phase-2 event-typed handlers (liquidation_events, flash_loan_events, etc.) — deferred until Phase-1/2/3 of this plan
  land
- Cross-protocol pool aggregation (e.g. unified DEX pool universe across UniV2/V3/V4) — orthogonal feature
- Real-time invalidation if a pool is added between adapter run and handler run — fallback-to-subgraph already covers
  this case

## Cross-links

- Audit findings: session 2026-04-29 (this conversation)
- Related shipped commits:
  - UAC `04f2c55` — `LST_VENUE_TO_TOKENS` (sibling SSOT pattern for static registries)
  - UAC `56ff55a` — pufETH genesis bump (data-quality fix that surfaced the audit)
  - deployment-api `37c1a45` — Phase-2 alias wiring (downstream cleanup the audit identified)
- Related codex SSOTs:
  - `codex/02-data/availability-manifest-and-data-status.md` — manifest v5 honest coverage
  - `codex/02-data/contracts-scope-and-layout.md` — UAC import surface rules
