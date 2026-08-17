---
doc_type: plan
title: defi venue e2e wiring batch 1 — 2026-08-16
summary: >-
  Fresh carve-out from venue_e2e_wiring_2026_08_16.md's "Fork per-asset-group dispatch batches" P0 todo — walks
  contract steps 1-9 across every defi (venue, data_type) row from `unified-api-contracts/scripts/
  generate_venue_work_list.py` (200 rows, measured 2026-08-16; re-run the script, this count is not a constant).
  Not an extraction from another source doc — no operator-gated item mixed in, per task_template.md §3 finding Y.
status: active
nature: process
asset_group: [defi]
stage: [data, features, strategy, execution]
repos:
  [
    unified-api-contracts,
    unified-trading-library,
    instruments-service,
    market-tick-data-service,
    features-service,
    strategy-service,
    execution-service,
  ]
scope: [engineer]
tags: [venue-readiness, e2e-wiring, defi, ao-dispatch, satellite-batch]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
drift_direction: advance-code
depends_on: []
estimate_class: infra
estimate_baseline_ai_days: 6.0
estimate_calibrated_ai_days: 4.8
assigned_role: backend_engineer
effort: medium
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /codex/06-coding-standards/integration-testing-layers.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    unified-api-contracts/scripts/generate_venue_work_list.py,
  ]
source: >-
  Forked from `venue_e2e_wiring_2026_08_16.md`'s "Fork per-asset-group dispatch batches" P0 todo, 2026-08-16
  interactive session, per the operator-selected "per contract-step-group" decomposition.
---

# defi venue e2e wiring batch 1 — 2026-08-16

> **Parent**: [`/plans/active/venue_e2e_wiring_2026_08_16.md`](/plans/active/venue_e2e_wiring_2026_08_16.md) (W4).
> The contract steps this plan walks, and the hard rules it must not violate, live in the parent — not restated here.
> Row list: `unified-api-contracts/scripts/generate_venue_work_list.py --csv PATH` filtered to `asset_group=defi`.

## Todos

- [x] ✅ [BACKEND] P0. **Steps 1-5 per unit — done 2026-08-16.** SHIPPED — `unified-trading-pm@285cefec7a`.
      4 parallel research passes, scoped by shared architecture (135 real defi venues, not 192 — see the
      correction below) since exhaustive per-venue checking isn't tractable at this scale.
      **Scope correction**: defi's real venue universe is `ALL_DEFI_VENUES` = **135** unique protocol-chain venues
      (measured), not the 192 cross-AG total this batch's own frontmatter cited — that 192 figure was always the
      whole-corpus denominator across every asset_group, not defi-specific; fixing the mislabel here rather than
      letting it propagate further.
      **Step 2 (instrument resolution) — 105/135 (≈78%) have a real `VENUE_TO_ADAPTER_KEY` entry**, stricter than
      the 127/135 capability-declaration figure already tracked. Beyond the already-tracked 8-venue gap, **22 NEW
      venues** are capability-declared but have no resolvable adapter mapping at all — new gap todo below.
      **Steps 3-4 (batch/live) — batch is broad** (50 protocol×chain subgraph deployments + RPC/REST for
      oracle_prices, ~121 venue keys via shared per-data-type handlers). **Live coverage is only ~13%** (16 real
      connectors vs. ~121 batch-covered venues; `oracle_prices`, the biggest data_type at 49 venues, has ZERO live
      connectors) — architecturally honest (`NotImplementedError` scaffolds, not faked), and **already tracked**
      in `defi_live_poller_phased_build_2026_08_15.md`/`cross_ag_live_capture_parity_2026_08_14.md`, cited not
      duplicated.
      **Step 5 (feature consumption, checked for the 6 biggest data_types = 170/200 rows) — only 2/6 clean PASS**
      (`lending_indices`, `lst_rates` — the archetype family defi was originally built around). Found a genuinely
      new structural bug: features-service's onchain dispatch (`FEATURE_GROUPS`, a closed 13-name enumeration in
      `onchain/cli/parser.py`) is NARROWER than its calculator registry — `oracle_prices` and `dex_pool_state` each
      have a real, implemented calculator that's simply unreachable (not wired into the dispatch if/elif chain).
      `dex_pool_swaps`/`staking_yields` have no consumer implementation at all — genuinely unimplemented, not just
      unwired. 2 new gap todos below (dispatch-table gap; missing-implementation gap).
- [x] ✅ [BACKEND] P1. **Gap: 22 defi venues are capability-declared but have no resolvable
      `VENUE_TO_ADAPTER_KEY` entry — done 2026-08-16, all 22 already carry a cited reason, no code needed.**
      This todo's own premise was checked against the wrong file: the earlier steps-1-5 sweep read only
      `venue_adapter_keys.py` (the resolved-adapter registry) and never cross-referenced
      `unified-api-contracts/unified_api_contracts/registry/defi_venues.py`'s `DEFI_VENUE_PHASE` dict, where
      every one of the 22 already carries an explicit `"pipeline"` classification under a section-header
      comment naming the reason — verified by reading each entry's surrounding comment directly, not inferred:
      - `ACROSS-ETHEREUM`/`STARGATE-ETHEREUM`/`FLASHBOTS-ETHEREUM`/`ALCHEMY-ONCHAIN`/`COMPOUND-ETHEREUM`/
        `UNISWAP-ETHEREUM` — NOT "zero adapter class" or "legacy aliases" as originally characterized; they're
        governance/MEV/bridge/gas-oracle analytics venues under "Pipeline (Ethereum analytics / governance /
        MEV — NOT IS-producible)" / "Pipeline (Alchemy multi-chain gas-fee oracles — NOT IS-producible)".
        `defi_venues.py`'s own `DEFI_VENUE_MTDS_ADAPTER_VERIFIED_NOT_YET_SCHEDULED` docstring additionally cites
        per-venue MTDS-side evidence for `ALCHEMY`/`FLASHBOTS`/`ACROSS`/`STARGATE`: "STILL-BROKEN: crash-looping
        cron or never scheduled at all, two with no SchemaContract registered" (2026-07-22 design doc).
      - `METEORA-SOLANA`/`LIFINITY-SOLANA`/`PHOENIX-SOLANA` — already cited in `venue_adapter_keys.py` itself
        (measurably dead upstreams, 404/522/NXDOMAIN, re-verified 2026-07-22).
      - `AAVE_V3-{SCROLL,ZKSYNC}`, `COMPOUND_V3-SCROLL` — "Pipeline (Scroll / zkSync — NOT IS-producible)".
      - `COMPOUND_V3-POLYGON` — "Pipeline (Polygon — NOT IS-producible)"; `venue_adapter_keys.py`'s own
        `SUBGRAPH_IDS["compound_v3"]` additionally notes "subgraph returns 0 markets (Compound V3 not active on
        Polygon)".
      - `MORPHO-ARBITRUM` — checked most carefully since `venue_adapter_keys.py`'s own comment reads as if this
        should be live ("ARBITRUM now has real major-asset liquidity... wired into morpho_adapter.py's
        `_CHAIN_ID_BY_CHAIN`"); `defi_venues.py` has the newer, more specific ruling: "not in IS-producible set
        despite having rows (not in `_build_defi_venues()`)" — deliberately still pipeline. Did NOT add an
        explicit key entry here on the strength of the older comment alone; the newer citation governs.
      - `MORPHO-OPTIMISM`/`MORPHO-POLYGON`, `YEARN_V3-OPTIMISM`, `PANCAKESWAP_V3-ARBITRUM` — each under its own
        "Pipeline (... — NOT IS-producible)" section header.
      - `MORPHOVAULTS-ETHEREUM`/`FRAX-ETHEREUM` — "Pipeline (Ethereum vaults / analytics — NOT IS-producible)";
        `FRAX` additionally has the same MTDS-side "stopped dead 2026-06-21, no scheduler" citation as the
        analytics group above.
      - `BEEFY-POLYGON`/`IDLE-POLYGON` — "Pipeline (Polygon catalogue Phase 1A, slot 5 2026-05-11)".
      No `VENUE_TO_ADAPTER_KEY` / `DEFI_VENUE_PHASE` edits made — every branch of the done-when ("real entry OR
      confirmed intentionally excluded with a cited reason") already resolves to the second branch, and writing
      speculative adapter code or forcing a phase flip against these citations would contradict already-ruled
      decisions, not close a gap.
- [x] ✅ [BACKEND] P1. **Gap: features-service's onchain dispatch table is narrower than its calculator
      registry — done 2026-08-17.** SHIPPED — `features-service@affaa7e850`. Wired all 3 previously-dead
      calculators into `onchain/cli/parser.py`'s `FEATURE_GROUPS` and `engine/orchestrator.py`'s
      `_dispatch_feature_group` if/elif chain: `chainlink_peg_deviation` (oracle_prices — reused the existing
      per-day `data_loader.load_oracle_prices` loader + a pandas/polars conversion shim, since the calculator's
      own `fetch_data` is standalone-empty by design, same caller-injected pattern as `lst_features.py`);
      `concentrated_liquidity_il_realised` and `pool_invariant_drift` (dex_pool_state — both already implement a
      real `fetch_data` via `read_canonical_defi_parquets`, so wired directly mirroring the existing
      `_process_rate_impact`/`_process_onchain_regime` dispatch pattern). New wiring test
      `tests/onchain/unit/test_dispatch_table_narrower_than_registry_wiring.py` (9 tests, all passing) proves
      each calculator is registry-reachable via `_dispatch_feature_group` end-to-end with mocked data and
      produces real, non-empty feature output (peg-deviation bps, IL pct, drift bps) for at least one defi venue —
      satisfying the done-when. Full `quality-gates.sh` green on the shipped SHA.
- [ ] [BACKEND] P2. **Gap: `dex_pool_swaps` and `staking_yields` have no feature_group consumer at all** — unlike
      the dispatch-table gap above, these are genuinely unimplemented (no calculator reads `dex_pool_swaps`
      anywhere; `staking_yields`'s only near-match, `lst_staking_calculator.py`, is an unrelated live DefiLlama
      pull that bypasses the manifest and also isn't dispatched). Done-when: a real implementation exists and is
      wired, or the gap is confirmed intentional with a cited reason.
- [x] ✅ [BACKEND] P0. **Steps 6-8 per unit — done 2026-08-16, 0/45 rows reach a genuinely complete
      end-to-end state.** SHIPPED — `unified-trading-pm@9f23cf22e5`. 2 parallel research passes (strategy-
      service archetype/slot + position-adapter chain-suffix mechanics; execution-service `InstructionActionV2`
      routing), scoped to the 45 `lending_indices`/`lst_rates` rows (31 protocol families) that cleared step 5;
      `oracle_prices`/`dex_pool_state`/`dex_pool_swaps`/`staking_yields` rows stay `BLOCKED-ON` their step-5 gap
      todos above, unchanged.
      **Step 6 (position adapter) — chain is NEVER part of the resolvable venue identity.**
      `strategy_service/position/position_interface/factory.py::get_position_adapter` normalizes
      `venue.lower().replace("-", "_")` (`factory.py:346`) and matches only BARE protocol tokens (`case "aave" |
      "aave_v3":`, `"morpho"`, `"kamino"`, `factory.py:108,115,143`) — a composite `PROTOCOL-CHAIN` string like
      `AAVE_V3-ARBITRUM` would normalize to `aave_v3_arbitrum`, match nothing, and raise `ValueError: Unknown
      venue`. Confirmed this is by design, not a bug: chain selection is a separate config field
      (`rpc_url`/`fork_mode`/`alchemy_rpc_url`, `routing.py:99-102,147-153`) threaded alongside the bare protocol
      venue, never encoded in it — `archetype_slots_defi.py:110-113` passes `"lending_protocol":
      "AAVE_V3_ETHEREUM"` and chain as two independent fields. So AAVE_V3's 8 chain rows are 1 resolvable
      protocol-level adapter reused via RPC config, not 8 independent venues — the right check granularity is
      per-PROTOCOL, not per-(protocol,chain) row. Dedicated adapters exist for `aave`/`aave_v3`, `morpho`,
      `kamino` only (`factory.py:106-146`); every other lending protocol
      (BENQI/COMPOUND_V3/EULER_V2/FLUID/MARGINFI/RADIANT/SOLEND/SPARK/VENUS) falls through to
      `_generic_token_balance_adapter`, which is LST-scoped by design (its own docstring: "NOT vault-share
      protocols... NOT the genuinely stateful protocols") and resolves `None` for all 9 → **FAIL, no adapter at
      all**. For LST protocols, `_generic_token_balance_adapter` needs BOTH a `LST_VENUE_TO_TOKENS` entry AND a
      real address in `LST_TOKEN_ADDRESS_BY_CHAIN`
      (`unified-api-contracts/unified_api_contracts/registry/lst_token_addresses.py`) — only 6 of 18 have both
      (LIDO, ROCKETPOOL, ETHERFI, PUFFER, JITO, MARINADE); the other 12
      (ANKR/BINANCE/COINBASE/ETHENA/MAKER/MANTLE/SANCTUM/SOLANA-NATIVE/SOLBLAZE/STADER/STAKEWISE/SWELL) **FAIL** —
      10 of those (all but BINANCE, SOLANA-NATIVE, which have no `LST_VENUE_TO_TOKENS` entry at all) have a real
      `LST_VENUE_TO_TOKENS` symbol + `LST_TOKEN_GENESIS` date but NO address in `LST_TOKEN_ADDRESS_BY_CHAIN` —
      new gap todo below (registry-appears-complete-but-isn't).
      **Step 7 (archetype/slot declaration)** — per protocol, across all 5 target archetypes
      (`archetype_slots_defi.py`, `target_universe/catalog_carry.py`, `catalog_staked_basis.py`,
      `catalog_yield_defi.py`): lending — AAVE_V3/COMPOUND_V3/KAMINO/MORPHO/SPARK declared in ≥1 archetype;
      BENQI/EULER_V2/FLUID/MARGINFI/RADIANT/SOLEND/VENUS (7) declared in **none**. AAVE-PLASMA is **ambiguous** —
      the catalogue only ever emits the bare `"aave"` token, never a Plasma-chain-disambiguated form, so whether
      it's the same resolvable adapter as `AAVE_V3-*` or orphaned isn't determinable from code alone (new gap
      todo below). LST — LIDO/ROCKETPOOL/ETHERFI/JITO/MARINADE/ETHENA declared in ≥1 archetype; the other 12 (same
      set that also fails step 6, plus PUFFER which PASSES step 6 but has **zero** archetype declaration)
      declared in **none**. Also found: UAC's own `archetype_consumers` column claims `CARRY_STAKED_BASIS`/
      `CARRY_STAKED_BASIS_DATED` consume all 28 `lending_indices` rows, but neither archetype's slot code
      references any lending protocol anywhere (LST + perp-hedge only) — stale/over-broad UAC declaration, new
      gap todo below.
      **Step 8 (execution, `InstructionActionV2`) — THREE parallel non-equivalent facades found, same failure
      class as the prediction batch's `PredictionBetHandler` finding.** The real live path is
      `DeFiAdapter`/`_dispatch_defi_operation` (`execution_service/adapters/defi_adapter.py:223-237`), reached via
      `LiveExecutionHandler._handle_defi_instruction`, which its own comment says "BYPASSES `InstructionRouter`"
      (`live_execution_handler.py:709-711`). It only branches on `SWAP/LEND/BORROW/STAKE` — **no WITHDRAW, REPAY,
      or UNSTAKE branch exists at that layer at all**, so even a fully-wired protocol can enter but never exit a
      position (new P0 gap todo below — a correctness/safety gap, not just coverage). It is constructed with
      exactly 5 live connectors (`uniswap, aave, lido, symbiotic, jupiter`, `live_execution_handler.py:534-538`).
      Net per-protocol: **AAVE_V3 — PARTIAL** (LEND/BORROW live via `self._aave.supply/borrow`, no WITHDRAW/REPAY)
      — the best result in the batch. **LIDO — PARTIAL** (STAKE live, no UNSTAKE) — the other best result.
      Everything else — **FAIL or NOT-FOUND**: MORPHO/KAMINO/ETHERFI/JITO/MARINADE/PUFFER/ROCKETPOOL/SOLBLAZE
      have real, complete connector modules in `defi_execution/protocols/` that are simply never constructed at
      the one live entry point (dispatch-table-narrower-than-registry pattern, same class as the features-service
      gap already tracked above — new gap todo below); COMPOUND_V3/EULER_V2/FLUID have UAC param types only, no
      connector file; BENQI/MARGINFI/RADIANT/SOLEND/SPARK and
      ANKR/BINANCE/COINBASE/ETHENA/MAKER/MANTLE/SANCTUM/SOLANA-NATIVE/STADER/STAKEWISE/SWELL have zero reference
      anywhere in execution-service. The other two facades are dead ends: `InstructionRouter`/`HandlerRegistry`
      (keyed on `OperationType`, not `InstructionActionV2`) only feeds backtest `BenchmarkMatcher` simulation
      (instant fill, never a real connector), and `OnChainExecutionService` is fully orphaned (zero call sites
      outside itself/tests) with `deposit/withdraw/borrow/repay/stake` methods that only call
      `RateImpactEngine.simulate_rate_impact()` and fabricate `success=True` — never touching a real connector.
      Backtest `LendHandler`/`StakeHandler.SUPPORTED_VENUES` advertise MORPHO/COMPOUND_V3/EULER_V2/FLUID/ETHERFI
      as "supported," which is not live-reachable — a paper≠live divergence risk, new gap todo below.
      **Net result: 0 of 45 rows / 31 protocol families reach a genuinely complete end-to-end state** — matching
      the 0/4 pattern the prediction batch found. AAVE_V3 and LIDO are the closest (2 of 3 legs real, both
      missing their exit-side execution action). Every other protocol fails at least 2 of the 3 steps.
      `BLOCKED-ON` markers: all `oracle_prices`/`dex_pool_state`/`dex_pool_swaps`/`staking_yields` rows stay
      blocked on their step-5 gap todos above (unchanged, not re-investigated here).
- [x] ✅ [BACKEND] P0. **Gap: execution-service's live DeFi path has no exit-side action at all — DONE 2026-08-17
      (slot-17).** `DeFiAdapter._dispatch_defi_operation` (`execution_service/adapters/defi_adapter.py`) now
      routes `WITHDRAW`/`REPAY` into `_execute_lending` (calling `AAVEConnector.withdraw()`/`.repay()`, both
      already complete + live-wired via `_execute_live_withdraw`/`_execute_live_repay`) and `UNSTAKE` into
      `_execute_staking` (calling `LidoConnector.unstake()`, already complete + live-wired via `_unstake_live` —
      honestly reports `staked_token="stETH"`, not WETH, since the Lido withdrawal queue isn't wired; also wired
      `SymbioticConnector.withdraw()` for UNSTAKE, same pattern). This was purely a dispatch-table gap — every
      connector method already existed. **Also fixed the upstream routing gate**: `DEFI_OPERATIONS` frozenset in
      `live_execution_handler.py` was missing `WITHDRAW`/`REPAY` — without this fix those instructions would have
      misrouted to `adapter_type="trade"` and never reached the new dispatch code at all. **Also fixed the true
      root gap**: UAC's `InstructionActionV2` enum had no `WITHDRAW`/`REPAY` members at all, so no caller could
      even construct such an instruction — added both (+ the paired `BENCHMARK_FILL_MODE_BY_ACTION` completeness
      dict entry, caught by `execution-service`'s own exhaustiveness test). New unit tests:
      `test_execute_withdraw`, `test_execute_repay`, `test_execute_unstake_lido`,
      `test_execute_unstake_unsupported_venue`; fixed `test_execute_unsupported_operation` (asserted UNSTAKE was
      unsupported — no longer true) and `test_defi_operations_constant`. Full `quality-gates.sh` green both repos.
      Evidence: `unified-api-contracts@03ff79e8b8` (InstructionActionV2 WITHDRAW/REPAY) +
      `unified-api-contracts@73a7594285` (BENCHMARK_FILL_MODE_BY_ACTION follow-up) +
      `execution-service@b8115edffc` (dispatch + routing-gate + tests).
- [x] ✅ [BACKEND] P1. **Gap: execution-service's live `DeFiAdapter` wires only 5 of 12+ fully-built protocol
      connectors — DONE 2026-08-17 (slot-25).** SHIPPED — `execution-service@f6535b12a2`. Wired 6 of the 7
      remaining connectors into `DeFiAdapter.__init__`/`ensure_connected`/dispatch and
      `LiveExecutionHandler._build_defi_adapter`: `morpho.py` (LEND/BORROW/WITHDRAW/REPAY via `market_id`, not
      per-asset — new `_execute_morpho_lending`), `kamino.py` (same 4 ops via `KaminoDepositParams`/
      `KaminoBorrowParams`, requires explicit `reserve_address`/`market_address` in instruction params — fails
      loud rather than guessing an on-chain address, new `_execute_kamino_lending`), `etherfi.py`/`puffer.py`/
      `rocket_pool.py`/`marinade.py` (STAKE/UNSTAKE — Puffer uses `deposit`/`withdraw`, not `stake`/`unstake`,
      a different verb than the other three; new per-connector `_execute_*_staking` methods). `solblaze.py`
      **intentionally excluded** — its own module docstring ("Live-capability status") confirms
      `stake()`/`unstake()` stay simulation-only (`supports_live=False` by design, needs the `spl-stake-pool`
      SDK which isn't a repo dependency); constructing it with `is_live=True` raises
      `SimulationOnlyConnectorError` (confirmed live via a first QG run that caught exactly this). 20 new unit
      tests in `tests/unit/test_defi_adapter.py` (7 connector fixtures + dispatch/fail-loud/ensure_connected
      coverage). Full `quality-gates.sh` green (file/function-size gates required extracting
      `_build_solana_defi_connectors` + moving connector-type imports to module level in
      `live_execution_handler.py`, since the pre-existing per-symbol lazy-import style re-triggered isort
      resplitting on `--fix`).
- [x] ✅ [BACKEND] P1. **Gap: three parallel, non-equivalent DeFi execution facades exist in
      execution-service — done 2026-08-17, divergence confirmed intentional/harmless + backtest
      lists corrected via live-wired annotations.** SHIPPED — `execution-service@3c21af4a4e`.
      Full consolidation to one live-authoritative facade was assessed and
      rejected as the wrong fix for a bounded gap-todo: `InstructionRouter`/`HandlerRegistry`
      feeding backtest `BenchmarkMatcher` simulation (never a real connector) is the SAME
      backtest-vs-live-connector split used for every other asset class in this service (TradFi/
      CeFi trade/futures/options handlers all delegate to the same `BenchmarkMatcher` pattern) —
      not a DeFi-specific defect, and collapsing it would mean either backtest DeFi ops start
      hitting real connectors (breaks backtest determinism/safety) or live DeFi ops start
      routing through the backtest-oriented router (contradicts `live_execution_handler.py`'s own
      documented BYPASS, which exists for a cited live-safety reason — CRIT-2 kill-switch +
      freshness-gate ordering, `live_execution_handler.py:709-711`). Documented this as the
      intentional/harmless branch of the done-when, with citations, directly in the 3 facade
      files rather than only in this plan (so any future reader hits the citation in-place):
      `engine/routing/instruction_router.py`'s class docstring now states the BACKTEST-ONLY scope
      + cites this gap todo + the live-bypass + paper-batch-live-reconciliation.md's actual
      invariant (numerical determinism, not code-path identity); `services/
      onchain_execution_service.py`'s module docstring now states plainly it is NOT
      live-authoritative, fully orphaned, and every method is a preview/estimate that never
      submits a real transaction — kept for its legitimate pre-trade estimation use, not deleted
      (it has a real, passing test file — `tests/unit/test_onchain_execution_service.py` — and
      deleting working estimation tooling isn't what this gap asked for). **Backtest
      SUPPORTED_VENUES lists corrected**: `LendHandler`/`StakeHandler`'s class docstrings
      (`engine/handlers/{lend,stake}_handler.py`) now explicitly separate "backtest/simulation
      reachability" (the SUPPORTED_VENUES set, unchanged — narrowing it would break legitimate
      pre-live-wiring backtest research, not requested by the done-when) from "live-wired"
      (cross-referencing `DeFiAdapter`'s actual constructed connectors: AAVE_V3 LEND/BORROW/
      WITHDRAW/REPAY + LIDO STAKE only, as of 2026-08-17) — so `MORPHO-*`/`COMPOUND_V3-*`/
      `EULERV2-*`/`FLUID-*`/`ETHERFI` no longer read as ambiguously "supported" without
      qualification; each docstring cites the already-open "DeFiAdapter wires only 5 of 12+"
      P1 gap todo above as the tracked fix for the underlying narrow-wiring gap itself (this
      todo's own scope is the facade/list-honesty finding, not re-doing that sibling gap's work).
      Zero code-BEHAVIOR changes (docstrings/comments only) — no test changes needed;
      `quality-gates.sh` green on the shipped SHA.
- [x] ✅ [BACKEND] P1. **Gap: `LST_TOKEN_ADDRESS_BY_CHAIN` is missing addresses for 10 LST tokens that
      `LST_VENUE_TO_TOKENS`/`LST_TOKEN_GENESIS` already declare — done 2026-08-17.** SHIPPED —
      `unified-api-contracts@9b982906fa`. 3 of the 10 had a real cited address already present elsewhere in the
      fleet and were migrated in: **cbETH/swETH** from `execution-service/execution_service/defi_execution/
      protocols/eigenlayer.py`'s `LST_TOKEN_ADDRESSES` dict (the real ERC-20 token addresses — distinct from
      that same file's `CBETH_STRATEGY`/`SWETH_STRATEGY` EigenLayer vault addresses, which are protocol
      contracts, not tokens, and were correctly NOT used); **bSOL** from `protocols/solblaze.py`'s
      `BSOL_MINT`, closing the module's own prior "held out pending cross-check" note. The other 7
      (ETHENA sUSDe / MAKER sDAI / MANTLE mETH / STADER ETHx / STAKEWISE osETH / ANKR ankrETH /
      SANCTUM sanctumSOL) have **no cited on-chain address anywhere in this codebase** — grepped fleet-wide;
      every reference found (`execution_service/cli/defi_rebasing_yield_decision_trace.py`, `kelpdao.py`) is a
      bare symbol string used for APY classification, never a contract address. Per the registry module's own
      explicit provenance rule ("no address here was authored, inferred, or extrapolated... copy it from a
      cited source, never derive"), adding one without an in-repo citation would be the exact fabrication that
      rule exists to prevent — documented in-code (`lst_token_addresses.py`) as a "DELIBERATELY ABSENT" block
      with the reason, rather than left as a silent gap. Remaining work (sourcing a cited address for those
      7 from an external, verifiable source) is out of this bounded task's scope — not tracked further here
      since it needs an operator/external-source decision, not more code search.
- [ ] [BACKEND] P2. **Gap: UAC's `archetype_consumers` over-declares `CARRY_STAKED_BASIS`/
      `CARRY_STAKED_BASIS_DATED` as consumers of all 28 `lending_indices` rows, but neither archetype's slot code
      references any lending protocol at all** — `strategy_service/engine/strategies/v2/target_universe/
      catalog_staked_basis.py` is LST + perp-hedge only (zero `lending_protocol`/AAVE-family references).
      Done-when: the UAC `archetype_consumers` declaration for `lending_indices` rows is corrected to drop these
      2 archetypes, or a real lending-consumption path is added to justify keeping them.
- [ ] [BACKEND] P2. **Gap: AAVE-PLASMA's protocol identity is ambiguous in the archetype catalogue** — every
      slot/catalogue reference to Aave uses the bare `"aave"` token (e.g. `archetype_slots_defi.py`,
      `catalog_yield_defi.py`), never a Plasma-chain-disambiguated form, so whether `AAVE-PLASMA` resolves
      through the same path as `AAVE_V3-*` rows or is silently orphaned isn't determinable from code alone.
      Done-when: the catalogue explicitly confirms (or denies) AAVE-PLASMA coverage, or this is confirmed
      genuinely unresolvable pending an upstream disambiguation decision with a cited reason.
- [x] ✅ [BACKEND] P0. **Step 9 per unit — done 2026-08-16, 1 major finding escalated as MORE urgent than the
      cefi sibling.** SHIPPED — `unified-trading-pm@285cefec7a`. Transfer routing is generic/chain-scoped, not
      per-protocol — `classify_transfer_type` routes purely on wallet type + custody_provider, the specific
      protocol (Aave/Uniswap/Lido/...) never enters the transfer path.
      **Major finding, escalated to a dedicated P0 issue doc + the operator directly**:
      [defi_cloud_kms_silent_wrong_chain_id_fallback_2026_08_16](/plans/active/issues/defi_cloud_kms_silent_wrong_chain_id_fallback_2026_08_16.md)
      — `CloudKmsCustodyProvider._resolve_chain_id()` (the real, provisioned May-23-cutover default custody
      surface) silently resolves an unmapped chain (LINEA/PLASMA/SCROLL/ZKSYNC) to `chain_id=1` (Ethereum)
      instead of failing loud like UAC's own canonical resolver does. **Confirmed REACHABLE-BUT-GATED, not dead
      code** — unlike the cefi CCXT-withdraw stub: the custody provider is genuinely constructed with real
      HSM-backed keys, and `AAVE_V3-LINEA` is already wired end-to-end elsewhere in execution-service and marked
      `"live"`. Zero fail-loud guard exists upstream. The only remaining gates (system-wide pre-live-trading
      status, live `wallet_provisioning.json` content) are not fully verifiable from a repo checkout — the issue
      doc's first todo is checking that live config, since it determines real urgency.
      **Copper custody path confirmed clean** — chain-agnostic by design (passes `chain` as an opaque string),
      real non-stub `create_transfer` calls, covers ASTER/HYPERLIQUID/LIGHTER-ZKSYNC/POLYMARKET-PERP already
      confirmed in the cefi batch.
- [x] ✅ [BACKEND] P1. **Record every gap found — done 2026-08-16.** 12 genuinely new gaps tracked across steps
      1-5, 6-8, and 9 (22 unresolved venues, the dispatch-table-narrower bug, the 2 unimplemented data_types, the
      cloud_kms chain-id issue doc, the no-exit-side-execution-action gap, the DeFiAdapter-narrower-than-registry
      gap, the 3-parallel-facades gap, the missing-LST-addresses gap, the over-broad UAC archetype_consumers
      gap, and the AAVE-PLASMA identity-ambiguity gap); 2 apparent gaps (the ~13% live-connector coverage, the
      already-tracked 8-venue capability gap) confirmed already tracked elsewhere, not duplicated.
- [x] ✅ [BACKEND] P0. **Confirm the parent plan's hard rules held — done 2026-08-16, trivially satisfied.** This
      batch's steps 1-9 sweep was investigation/documentation only — zero code was changed in any touched repo
      (the 2 new issue docs are plan-corpus docs, not code changes).

## Progress Log

**2026-08-16 — steps 6-8 swept, 6 more real gaps found — 0/45 rows (31 protocol families) reach a complete
end-to-end state.** SHIPPED — `unified-trading-pm@9f23cf22e5`. 2 parallel research passes (strategy-service
archetype/slot + position-adapter mechanics; execution-service `InstructionActionV2` routing), scoped to the 45
`lending_indices`/`lst_rates` rows that cleared step 5. Confirmed chain is never part of the resolvable position-
adapter venue identity (protocol-only match, chain via RPC config) — so the right check granularity is per-
protocol-family, not per-(protocol,chain) row. Position adapter resolves for only 9/31 protocols (AAVE_V3/
MORPHO/KAMINO dedicated; LIDO/ROCKETPOOL/ETHERFI/PUFFER/JITO/MARINADE via the generic LST-balance path).
Archetype/slot declaration covers 11/31. Execution (`InstructionActionV2` via the real live `DeFiAdapter` path,
which explicitly bypasses `InstructionRouter`) only wires AAVE (LEND/BORROW) and LIDO (STAKE) live, and neither
has an exit-side action at all (no WITHDRAW/REPAY/UNSTAKE dispatch exists) — the same "looks wired, routes
through the wrong/older facade" failure class the prediction batch found, compounded here by two dead facades
(backtest-only `InstructionRouter`, fully-orphaned `OnChainExecutionService` that fabricates `success=True`) and
7 fully-built-but-unregistered protocol connectors. 6 new gap todos tracked: no-exit-side-action (P0),
DeFiAdapter-narrower-than-registry (P1), 3-parallel-facades/paper-live-divergence-risk (P1), missing-LST-
addresses-despite-registered-symbols (P1), over-broad UAC `archetype_consumers` for `lending_indices` (P2),
AAVE-PLASMA identity ambiguity (P2). Net: AAVE_V3 and LIDO are the closest to end-to-end (2 of 3 legs real, both
missing their exit action); every other protocol fails at least 2 of the 3 steps. Remaining open: none — this
batch's steps 1-9 are now all resolved or gap-tracked.

**2026-08-16 — full contract sweep done, 1 escalated finding MORE urgent than cefi's, 6 new gaps total.**
SHIPPED — `unified-trading-pm@285cefec7a`. 4 parallel research passes plus a dedicated reachability check.
Scope-corrected the batch's own denominator (135 real defi venues, not the 192 cross-AG total this doc originally
cited). Instrument resolution: 105/135 real (22 new gap venues beyond the already-tracked 8). Live capture is
only ~13% of batch coverage — large but already tracked elsewhere, not duplicated. Feature consumption: only
`lending_indices`/`lst_rates` (the original archetype family) are genuinely wired; found a real dispatch-table-
narrower-than-registry bug affecting `oracle_prices`/`dex_pool_state`, and confirmed `dex_pool_swaps`/
`staking_yields` have no implementation at all. The most serious finding: `CloudKmsCustodyProvider` silently
resolves an unmapped chain to `chain_id=1` instead of failing loud — confirmed REACHABLE-BUT-GATED (not dead
code, unlike the cefi sibling), with a real provisioned custody path and `AAVE_V3-LINEA` already live-wired
elsewhere in execution-service. Escalated to a dedicated P0 issue doc + the operator directly.

**2026-08-16 — slot 12: dispatched onto this same "Steps 1-5" scope after it had already landed; shipped a
complementary structural cross-check instead of duplicating.** SHIPPED — `unified-api-contracts@5770b51a72`
(`scripts/verify_defi_venue_e2e_steps1_5.py`, permanent/re-runnable). By the time this session's `/boot` resolved,
todo #1 above (`unified-trading-pm@285cefec7a`) had already shipped a more thorough, registry-grounded sweep — not
duplicating it. The new script instead runs a different, cheaper, FILE-PRESENCE-based structural check per defi
row (200 rows, reused verbatim from `generate_venue_work_list.py`): does an `instruments-service` adapter file
exist matching the venue (step 2), does an MTDS handler file reference both the venue and data_type tokens (step
3, manifest reconciliation explicitly NOT live-checked), does a `live/connectors/*_ws.py` file match the venue
(step 4, distinguishing real adapters from declared `_scaffold_ws.py` stubs), does any UAC
`FEATURE_REQUIRED_INPUTS` entry declare the data_type for a defi feature_group (step 5). Measured this run: step2
170/200 PASS; step3 54 PASS / 29 PARTIAL / 117 FAIL; step4 19 PASS / 181 FAIL; step5 59 PASS / 141 NONE. Broadly
consistent with the peer sweep's headline numbers (adapter/live-coverage gaps large, feature consumption narrow)
via an independent method (filename/text presence vs. `VENUE_TO_ADAPTER_KEY` registry lookup) — a useful standing
cross-check for future re-runs of this batch, not a substitute for the registry-grounded analysis already landed.
No new gap todos added from this run: its FAIL/NONE counts are structurally consistent with the already-tracked
gaps above (the 22-venue adapter gap, the ~13% live coverage, the narrow feature dispatch) rather than revealing a
distinct defect class.

**2026-08-16 — 22-venue adapter gap resolved, all already cited, zero code changes needed.** Investigated the
"22 defi venues... no resolvable `VENUE_TO_ADAPTER_KEY` entry" P1 gap todo by reading `defi_venues.py`'s
`DEFI_VENUE_PHASE` dict (not just `venue_adapter_keys.py`, which is what the originating sweep checked). Every
one of the 22 already carries an explicit `"pipeline"` classification under a section-comment reason there —
governance/MEV/bridge/gas-oracle analytics (not IS-producible by architecture), dead/low-liquidity/inactive
subgraphs, or staged Phase-1A rollout. Full per-venue citation list in the flipped todo below. One near-miss
worth flagging for future readers: `MORPHO-ARBITRUM`'s comment in `venue_adapter_keys.py` reads as if it should
already be live (real liquidity, wired into the adapter's chain map) — `defi_venues.py` carries the newer,
overriding citation ("not in IS-producible set despite having rows"). Deferred to the newer source rather than
adding a key on the older comment's strength alone. No code shipped (correctly — the gap resolves via the
already-cited-reason branch of the done-when, not a code fix); this batch's own hard-rule confirmation todo above
already established zero code changes for steps 1-5/9, and this todo continues that pattern.
**context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
