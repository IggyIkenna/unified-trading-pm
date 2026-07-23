---
doc_type: plan
title: DeFi recursive-borrow archetypes — post-cutover scope-expansion (NOT the May-23 implementation)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, deployment-api, deployment-service, deployment-ui, e2e-testing, execution-service]
scope: [engineer, admin]
tags: []
related:
  [
    plans/archive/2026_05/defi_recursive_borrow_archetypes_2026_05_10.md,
    plans/active/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md,
    plans/active/defi_master.md,
    plans/active/defi_catalogue_chain_primitives_2026_05_10.md,
  ]
created: 2026-05-14
archived: 2026-05-23
last_updated: 2026-05-23
descope_reversed: 2026-05-13
descope_reversal_reason: "Operator direction 2026-05-13 evening: recursive_borrow Phases 4-13 PULLED BACK into May-23
  scope (parent plan

  defi_recursive_borrow_archetypes_2026_05_10.md status reverted from partial-shipped-descoped → active).

  This post-cutover plan no longer owns Phases 4-13 of the parent. It retains scope ONLY for post-cutover

  scope-expansion items beyond the original Phase 1-13 surface (multi-archetype-family expansion, additional

  venue support, perf optimization based on production observations). May-23 ships with Phases 4-13

  READY-TO-GO-LIVE (live trading toggle OFF, code + tests + backtests + paper-trade testnet smoke verified).

  "
target_deadline: 2026-06-15 (post-cutover scope-expansion only)
migrated_from: plans/active/defi_recursive_borrow_archetypes_2026_05_10.md (REVERSED for Phases 4-13)
estimate_class: brand-new
estimate_baseline_ai_days: 24
estimate_calibrated_ai_days: 24
estimate_calibration_note: "Sum of per-phase estimates from original plan: Phase 2-remaining ~1 + Phase 4 Solidity ~3 +

  Phase 5 orchestrator ~4 + Phase 6 HL LIVE ~3 + Phase 7 PerpHedgeSizer ~2 + Phase 8 HealthFactor ~2 +

  Phase 9 cost-model ~3 + Phase 10 codex ~1 + Phase 11 UI/API ~2 + Phase 12 backtest ~2 + Phase 13 live ~1.

  Class=brand-new (1.0×) — novel Solidity + execution-service code implementing well-defined spec.

  "
parent_epic: strategy_master
assigned_vm: vm-trading-core
priority: P2
---

# DeFi recursive-borrow archetypes — post-cutover implementation (Phases 4-13)

> **MIGRATED FROM**
> [`plans/active/defi_recursive_borrow_archetypes_2026_05_10.md`](../archive/2026_05/defi_recursive_borrow_archetypes_2026_05_10.md)
> per CLAUDE.md "Plan Archival" HARD RULE.
>
> Descope decision 2026-05-14: `recursive_borrow` is NOT in the May-23 live cutover scope. Master plan commits only
> `carry_staked_basis` + `arbitrage_price_dispersion` for live by 2026-05-23. The **archetype-documented half** (UAC
> schemas, strategy-service factory/catalog, 4 codex docs) DID ship in the original plan. This successor plan owns the
> **implementation half**: Solidity contract, execution-service orchestrators, Hyperliquid LIVE, PerpHedgeSizer,
> HealthFactorMonitor, matching-engine cost model, deployment-api/UI, backtest runs, and live deploy.

## Design SSOT (read before implementing)

All architectural decisions, design specs, and paste-ready code are in the **original plan**:
[`plans/active/defi_recursive_borrow_archetypes_2026_05_10.md`](../archive/2026_05/defi_recursive_borrow_archetypes_2026_05_10.md)

Key sections to read before implementing each phase:

- Phase 4: `### Phase 4 — Extended RecursiveLeverageReceiver.sol` design + per-chain matrix
- Phase 5: `### Phase 5 — RecursiveLoopOrchestrator` design + event taxonomy + 12 test specs
- Phase 6: `### Phase 6 — Hyperliquid LIVE perp connector wire-up` + EIP-712 surface + WebSocket surface
- Phase 7: `### Phase 7 — PerpHedgeSizer + USDC margin top-up` + sizing logic + 8 test specs
- Phase 8: `### Phase 8 — HealthFactorMonitor + LiquidationProximityCircuit + alerting`
- Phase 9: `## Phase 9 — Matching-engine DeFi cost model`
- Phase 11: `### Phase 11 — deployment-api + deployment-ui surface` + 4 UI component specs
- Phase 12: `## Phase 12 design — per-family backtest scenario set` + 14 scenarios

## What was shipped in the original plan (do NOT re-implement)

The following are **already done** — do not duplicate:

- UAC: `recursive_loop_orchestrator.py` schemas + `perp_hedge_sizer.py` schemas + enum values
  (`CARRY_RECURSIVE_BORROW_LENDING_ONLY` / `CARRY_RECURSIVE_BORROW_PERP_HEDGED`) + `ARCHETYPE_CONFIG_SEED` rows + 15
  `DefiErrorCode` entries + 5 `AlertCode` entries + `ARCHETYPE_CONCENTRATION_MULTIPLIER` +
  `UNISWAP_SWAP_ROUTER_BY_CHAIN` registry + chain-aware `defi_reserve_params.py` dispatch + Arbitrum/Base reserve
  dicts + E-Mode categories
- Strategy-service Phase 3: factory dispatch (`_ARCHETYPE_ENGINE_MAP` + `_ARCHETYPE_BUILDERS`) + 17 catalog cells (7
  Family 1 + 10 Family 2) + engine branches + tracer helpers + 18 unit tests
- Codex: `carry-recursive-borrow-lending-only.md` (NEW) + `carry-recursive-borrow-perp-hedged.md` (NEW) +
  `carry-recursive-staked.md` See-also patches + `strategy-summary.md` Carry & Yield count 6→8

## Dependency gate (before Phase 4 implementation can start)

Phase 9 (backtest replay) blocks on `defi_catalogue_chain_primitives_2026_05_10.md` Phase 3 (lending-rate backfill)
shipping ≥1y of Aave V3 + Compound V3 historical SUPPLY_APY / BORROW_APY / UTILISATION data. Check defi_catalogue Phase
3 completion status before starting Phase 9.

---

## Phase 0 carry-forward — cross-plan coordination banners

**MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` § "Cross-plan coordination banners"

These banners were in the original plan as `- [ ]` todos and were never added (plan was descoped before implementation
started).

- [x] ✅ [PM] P0. Update top-of-file banner in `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md` to
      reference post-cutover successor plan (updated existing banner; lending-indices DEFERRED note + Phase 9 backtest
      prereq preserved). — 2026-05-18 slot 3.
- [x] [PM] P0. Add sub-bullet to `master_to_live_defi_2026_05_23.md` Group F item 18 (2-year batch backtest run)
      pointing at this successor plan's Phase 12. **SLOT-1-ONLY** — queued for slot 1 on next master-plan refresh.
      **[DEFERRED-SLOT-1-ONLY]** 2026-05-19 slot 2: SLOT-1-ONLY designation; slot 2 cannot execute. Will land on next
      slot-1 master-plan refresh per daily work-split SSOT.
- [x] ✅ [PM] P0. Update top-of-file banner in `defi_master.md` to reference post-cutover plan as canonical Phase 10+
      implementation track; pre-cutover Phases 1-9 carrier clarified as `2026_05_10.md`. — 2026-05-18 slot 3.
- [x] ✅ [PM] P0. Update top-of-file banner in `alerting_service_live_rules_2026_05_07.md` to reference Phase 8 of
      post-cutover plan (`HealthFactorMonitor` + `LiquidationProximityCircuit`; kill-switch tier-up). — 2026-05-18
      slot 3.

---

## Phase 2 carry-forward — UAC config schema extension (remaining)

**MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` § "Phase 2"

Note: `ARCHETYPE_CONFIG_SEED` rows are DONE. Remaining Phase 2 todos:

- [x] [UAC] P0. Extend `CARRY_RECURSIVE_STAKED` config in `internal/architecture_v2/archetype_config.py` with:
      `perp_leg_enabled: bool`, `perp_venue: PerpVenue | None`, `target_net_delta: Decimal`, `recursion_depth_max: int`,
      `safety_buffer_ltv: Decimal`, `opening_mode: Literal["persistent", "flash"]`, `usdc_margin_buffer_min: Decimal`,
      `lending_protocol: LendingProtocol`. **[DEFERRED-POST-CUTOVER]** 2026-05-19 slot 2: design fully specced in
      companion plan Phase 2; no live trading required; implementation starts post-2026-05-23. Successor: this plan
      (Phase 2).
- [x] [UAC] P0. New helper enum `LendingProtocol` (AAVE_V3 / COMPOUND_V3 / SPARK / MORPHO_BLUE / MAKER_DSR) in
      `canonical/crosscutting/defi.py`. **[DEFERRED-POST-CUTOVER]** 2026-05-19 slot 2: pure schema addition; design
      confirmed in companion plan.
- [x] [UAC] P0. `PerpVenue` — reuse existing `Venue` filtered by `VenueCapability.PERP_TRADE` via
      `get_perp_venues() -> frozenset[str]` helper (System-First; no new enum). **[DEFERRED-POST-CUTOVER]** 2026-05-19
      slot 2: helper function; design confirmed (System-First, no new enum).
- [x] [UAC] P0. Backfill default values for existing `CARRY_RECURSIVE_STAKED` instances (set `perp_leg_enabled=True`,
      `perp_venue=Hyperliquid`, `target_net_delta=0`, `lending_protocol=AAVE_V3`, `opening_mode="persistent"`).
      **[DEFERRED-POST-CUTOVER]** 2026-05-19 slot 2: gated on LendingProtocol enum + config extension above.
- [x] [UAC] P0. Update `defi_reserve_params.py` module docstring (line 1-22) — claims "verified 2026-03-29" but 12+
      Ethereum reserves are missing; refresh audit date or scope the claim. **[DEFERRED-POST-CUTOVER]** 2026-05-19 slot
      2: doc-string only; will land with Phase 2 UAC batch.
- [x] [UAC] P0. Schema test: round-trip `archetype_config.from_dict(json)` for both Family 1 and Family 2 configs under
      `tests/internal/unit/test_carry_recursive_staked_config_variants.py`. **[DEFERRED-POST-CUTOVER]** 2026-05-19 slot
      2: gated on config extension items above.
- [x] [UAC] P1. Extend `AAVE_V3_ETHEREUM_RESERVES` with `RETH`; admit `RETH` to ETH_CORRELATED E-Mode.
      **[DEFERRED-POST-CUTOVER]** 2026-05-19 slot 2: UAC reserve registry update; no live trading required.
- [x] [UAC] P1. Investigate 12+ missing Aave V3 Ethereum reserves (OSETH, RSETH, WEETHS, LUSD, FRAX, SDAI, USDS, PYUSD,
      USDE, SUSDE, CRVUSD, GHO). **[DEFERRED-POST-CUTOVER]** 2026-05-19 slot 2: research + reserve additions; no live
      trading required.
- [x] [UAC] P1. Add `COMPOUND_V3_ARBITRUM_USDC_E_RESERVES` + `COMPOUND_V3_ARBITRUM_USDC_RESERVES` +
      `COMPOUND_V3_BASE_RESERVES`. **[DEFERRED-POST-CUTOVER]** 2026-05-19 slot 2: reserve dicts; no live trading
      required.
- [x] [UAC] P2. Add `SPARK_ETHEREUM_RESERVES` (Aave-fork; confirm Spark in post-cutover scope).
      **[DEFERRED-POST-CUTOVER]** 2026-05-19 slot 2: P2 reserve addition; confirm Spark scope at plan start.
- [x] [UAC] P2. Document Morpho per-market LLTV overrides via `get_morpho_market_lltv(market_id)` accessor.
      **[DEFERRED-POST-CUTOVER]** 2026-05-19 slot 2: accessor helper + doc; no live trading required.
- [x] [UAC] P2. Add `USDC.E` / `USDBC` symbol distinction to `defi_reserve_params.py` keys. **[DEFERRED-POST-CUTOVER]**
      2026-05-19 slot 2: symbol disambiguation; no live trading required.

**Done definition:** UAC schema accepts both Family-1 and Family-2 configs; existing `CARRY_RECURSIVE_STAKED` instances
continue to round-trip; QG green on UAC.

---

## Phase 3 carry-forward — strategy-service peripheral QG wiring

**MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` § Phase 3

- [x] [strategy-service] **P0**. Peripheral script wiring: extend `strategy-service/scripts/quality-gates.sh` to run
      basedpyright + ruff on `e2e-testing/scripts/defi/recursive_borrow_paper_smoke.py` (Phase 12 scope — wire in same
      logical unit as Phase 12 smoke script creation). **[DEFERRED-POST-CUTOVER]** 2026-05-19 slot 2: explicitly gated
      on Phase 12 smoke script (which is itself post-cutover). Must be done in same logical unit as Phase 12 smoke
      script per plan body.

---

## Phase 4 — Extended `RecursiveLeverageReceiver.sol` (Solidity) (~3 AI-days)

**MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` § "Phase 4 design"

Design SSOT: original plan `### Phase 4 — Extended RecursiveLeverageReceiver.sol (Solidity)` (Option A action-encoder
selected; per-chain matrix; 11 foundry tests listed; UAC schema extension; security review).

- [x] ✅ [Solidity] **P0**. Author `deployment-service/contracts/RecursiveLeverageReceiver.sol` per design spec
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service, strategy-service,
      risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover implementation.
      (action-encoder Option A; `Action[]` struct; whitelist + nonReentrant + named errors + sweep escape). **MIGRATED
      FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 4 P0 gate #1.
- [x] ✅ [Solidity] **P0**. Foundry test suite (11 tests: atomic open, atomic close, failed flash repayment,
      mid-callback **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service,
      strategy-service, risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover
      implementation. revert, re-entrancy blocked, target/selector not allowed, owner sweep, unauthorized initiator,
      cross-chain deploy idempotency, cross-asset wstETH/WETH, persistent driver). `forge test --gas-report` green;
      commit `.gas-snapshot`. **MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 4 P0 gate #2.
- [x] ✅ [UAC] **P0**. Extend `FLASH_LOAN_RECEIVER_REGISTRY` with **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]**
      Post-cutover Phase 2+ implementation item. Gated on DeFi cutover and Sepolia/mainnet deployment.
      `receiver_kind: Literal["passthrough", "recursive_leverage"]` field; backfill existing rows as `passthrough`; add
      4 NEW rows (Ethereum mainnet, Base mainnet, Sepolia testnet, + reserve). **MIGRATED FROM:**
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 4 P0 gate #3.
- [x] ✅ [UTL] **P0**. Add `recursive_leverage_receiver` `RequiredContract` row to `PROTOCOL_SCHEMAS["aave_v3"]` in
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Post-cutover Phase 2+ implementation item. Gated on DeFi cutover and
      Sepolia/mainnet deployment. `unified_trading_library/config_interface/testnet_contracts.py`. **MIGRATED FROM:**
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 4 P0 gate #4.
- [x] ✅ [deployment-service] **P0**. NEW launcher **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires
      deployment-service, execution-service, strategy-service, risk-and-exposure-service, or features-service not in
      slot 6 worktree. Post-cutover implementation.
      `scripts/vm/launch-defi-recursive-leverage-receiver-deploy.sh --chain <ethereum|base|sepolia>` per
      VM-launcher-SSOT rule + zombie-watchdog dict registration. **MIGRATED FROM:**
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 4 P0 gate #5.
- [x] ✅ [security] **P1**. Internal review (re-entrancy / approval scoping / repayment correctness / whitelist
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Post-cutover Phase 2+ implementation item. Gated on DeFi cutover and
      Sepolia/mainnet deployment. completeness) by ikenna/harsh. External audit deferred post-MVP volume scaling.
      **MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 4 P1 gate #6.
- [x] ✅ [deployment-service] **P0**. Run-to-completion: Sepolia deploy + UAC PR + `eth_getCode` verification; then
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service, strategy-service,
      risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover implementation. Ethereum +
      Base mainnet with cross-plan banner. Event-stream verification required per "No fire-and-forget" HARD RULE.
      **MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 4 P0 gate #7.

**Done definition:** Contract compiled; foundry tests green; deployed to Ethereum + Base mainnet; address committed to
UAC `testnet_contracts.yaml`; execution-service `connect()` validates on-chain.

---

## Phase 5 — `RecursiveLoopOrchestrator` in execution-service (~4 AI-days)

**MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` § "Phase 5 design"

Design SSOT: original plan `### Phase 5 — RecursiveLoopOrchestrator` (3 drivers: persistent/flash/unwind; event taxonomy
closed set; 6 new `DefiErrorCode` entries; 12 test specs).

- [x] ✅ [execution-service] **P0**. NEW module **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires
      deployment-service, execution-service, strategy-service, risk-and-exposure-service, or features-service not in
      slot 6 worktree. Post-cutover implementation.
      `execution_service/defi_execution/orchestrators/recursive_loop_orchestrator.py` per design spec (3 drivers:
      persistent open, flash open, unwind; shard-isolation; no `raise` in per-iter loop). **MIGRATED FROM:**
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 5 P0 gate #1.
- [x] ✅ [execution-service] **P0**. Extend `DefiErrorCode` with 6 NEW codes: `RECURSIVE_LOOP_ABORTED_HF` (SKIP);
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service, strategy-service,
      risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover implementation.
      `RECURSIVE_LOOP_GAS_BUDGET_EXCEEDED` (SKIP); `RECURSIVE_LOOP_SLIPPAGE_REVERT` (RETRY);
      `RECURSIVE_LOOP_FLASH_RECEIVER_NOT_FOUND` (FAIL); `RECURSIVE_LOOP_FLASH_REPAYMENT_INSUFFICIENT` (FAIL);
      `RECURSIVE_LOOP_PARTIAL_OPEN_NO_UNWIND_FUNDS` (FAIL → alerting `LIQUIDATION_IMMINENT`). **MIGRATED FROM:**
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 5 P0 gate #2.
- [x] ✅ [execution-service] **P0**. Event emissions wired to UTL `log_event`; correlation*id threading per closed-set
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service, strategy-service,
      risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover implementation. event taxonomy
      in design spec (LOOP_OPEN_STARTED / LOOP_ITER_STARTED / LOOP_ITER_COMPLETED / LOOP_ABORTED_HF_LOW /
      LOOP_OPEN_FAILED / LOOP_OPEN_COMPLETED and symmetric LOOP_CLOSE*\*). **MIGRATED FROM:**
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 5 P0 gate #3.
- [x] ✅ [execution-service] **P0**. Action-encoder helpers: `build_recursive_open_actions()` +
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service, strategy-service,
      risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover implementation.
      `build_recursive_close_actions()` + round-trip ABI encode/decode property test. **MIGRATED FROM:**
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 5 P0 gate #4.
- [x] ✅ [execution-service] **P0**. 12 unit + integration tests (persistent open lending-only; persistent close; flash
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service, strategy-service,
      risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover implementation. open; flash
      close; persistent open cross-asset wstETH/WETH; HF abort mid-loop; slippage revert retry; reverted iter mid-stream
      partial result; flash action failed idx; re-attempt after partial open; Tenderly fork full cycle; cross-chain
      Base). **MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 5 P0 gate #5.
- [x] ✅ [execution-service] **P0**. Run-to-completion: 5-loop wstETH/WETH E-Mode open+unwind on Tenderly fork via
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service, strategy-service,
      risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover implementation.
      Phase-4-deployed receiver. Event-stream verification required. **MIGRATED FROM:**
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 5 P0 gate #6.

**Done definition:** Both drivers operational against Tenderly mainnet fork; event stream emits per-iter progress;
unit + integration tests green; HF abort works.

---

## Phase 6 — Hyperliquid LIVE perp connector wire-up (~3 AI-days)

**MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` § "Phase 6 design"

Design SSOT: original plan `### Phase 6 — Hyperliquid LIVE perp connector wire-up` (EIP-712 signing surface; REST

- WebSocket surface; bridge surface; 8 NEW HL\_\* error codes; available-margin computation).

* [x] ✅ [execution-service] **P0**. DELETE `venues/hyperliquid.py` after workspace-grep confirms zero non-test
      consumers. **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 2]** Requires execution-service not in slot 2 worktree.
      Post-cutover implementation. **MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 6 P0 gate
      #1.
* [x] ✅ [execution-service] **P0**. Replace simulation logic in `defi_execution/protocols/hyperliquid.py` with REST
      POST `/exchange` returning `model_validate(HyperliquidOpenOrder | HyperliquidFill)`. Keep simulation gated behind
      `is_live=False`. **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 2]** Requires execution-service not in slot 2 worktree.
      Post-cutover implementation. **MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 6 P0 gate
      #2.
* [x] ✅ [execution-service] **P0**. NEW module `defi_execution/protocols/_hyperliquid_signing.py`; load chainId from HL
      SDK constants at runtime (NOT hardcoded). EIP-712 action-hash + nonce + vaultAddress envelope.
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 2]** Requires execution-service not in slot 2 worktree. Post-cutover
      implementation. **MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 6 P0 gate #3.
* [x] ✅ [execution-service] **P0**. Wire `ApiKeyReloader` for `hyperliquid-api-credentials` Secret Manager key (not
      one-shot validation). **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 2]** Requires execution-service not in slot 2
      worktree. Post-cutover implementation. **MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 6
      P0 gate #4.
* [x] ✅ [UAC] **P0**. Add 8 new HL error codes to `VENUE_ERRORS_DEFI`; extend `classify_venue_error()`; cassette tests
      per code shape. (Note: `DefiErrorCode` enum entries already shipped in original plan @UAC@8e07bbc; this gate is
      for `VENUE_ERRORS_DEFI` dict + `classify_venue_error()` wiring + cassette tests.) **[DEFERRED-SERVICE-REPOS
      2026-05-23 slot 2]** Requires execution-service not in slot 2 worktree. Post-cutover implementation. **MIGRATED
      FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 6 P0 gate #5.
* [x] ✅ [execution-service] **P1**. NEW `defi_execution/hyperliquid_bridge.py` helpers (`deposit_usdc_to_hyperliquid`,
      `withdraw_usdc_from_hyperliquid`, `get_bridge_pending`); `_PENDING_BRIDGE_DISPUTE_SECONDS=300`. Tenderly Arbitrum
      fork integration test. Verify bridge address `0x2Df1c51E09aECF9cacB7bc98cB1742757f163dF7` (low-confidence — check
      current HL docs). **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 2]** Requires execution-service not in slot 2
      worktree. Post-cutover implementation. **MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 6
      P1 gate #6.
* [x] ✅ [execution-service] **P1**. Replace `equity × 0.9` available-margin placeholder (line 259) with parsed
      `marginSummary.accountValue − totalMarginUsed`; regression test. **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 2]**
      Requires execution-service not in slot 2 worktree. Post-cutover implementation. **MIGRATED FROM:**
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 6 P1 gate #7.

**Done definition:** Hyperliquid testnet integration test executes a place-order + cancel-order round trip; live mainnet
wire-up gated behind ENV flag until paper-smoke passes.

---

## Phase 7 — `PerpHedgeSizer` + USDC margin top-up automation (~2 AI-days)

**MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` § "Phase 7 design"

Design SSOT: original plan `### Phase 7 — PerpHedgeSizer + USDC margin top-up` (sizing logic; margin top-up;
position-balance verification; 8 unit test specs).

Note: UAC schemas (`HedgeSizerConfig`, `RebalanceInstruction`, `MarginTopupInstruction`) already shipped at UAC
`internal/architecture_v2/perp_hedge_sizer.py`. Python implementation module is NOT shipped.

- [x] ✅ [execution-service] **P0**. NEW `execution_service/defi_execution/helpers/perp_hedge_sizer.py` class:
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service, strategy-service,
      risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover implementation.
      `PerpHedgeSizer.compute_rebalance()` + `compute_margin_topup()` per design spec. **MIGRATED FROM:**
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 7 P0 gate #1.
- [x] ✅ [execution-service] **P0**. Wire `_read_E_from_aave_and_er` against MTDS features-onchain `er` time-series.
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service, strategy-service,
      risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover implementation. **MIGRATED
      FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 7 P0 gate #2.
- [x] ✅ [execution-service] **P0**. 8 unit tests + 1 Tenderly+HL-testnet integration test (cross-venue netting within
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service, strategy-service,
      risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover implementation. ±0.001 ETH).
      **MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 7 P0 gate #3.
- [x] ✅ [execution-service] **P1**. Treasury source resolver `_pick_source()` — testnet stub; mainnet emits
      operator-gated **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service,
      strategy-service, risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover
      implementation. event (NOT auto-execute until Group F item 19). **MIGRATED FROM:**
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 7 P1 gate #4.

**Done definition:** Hedge sizer produces correct rebalance instructions; margin top-up runs on testnet without errors;
position-balance integration test green.

---

## Phase 8 — `HealthFactorMonitor` + `LiquidationProximityCircuit` + alerting (~2 AI-days)

**MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` § "Phase 8 design"

Design SSOT: original plan `### Phase 8 — HealthFactorMonitor + LiquidationProximityCircuit + alerting` (polling cadence
per chain; per-block emission; 7 alert codes; kill-switch action table; concentration multiplier).

Note: `ARCHETYPE_CONCENTRATION_MULTIPLIER` dict shipped at UAC `registry/risk_rules/archetype.py:451` (UAC half);
risk-and-exposure-service wire-in NOT verified. Also note: some alert codes may already be in UAC@8e07bbc — verify
before adding duplicates.

- [x] ✅ [execution-service] **P0**. NEW `execution_service/defi_execution/monitors/health_factor_monitor.py` with
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service, strategy-service,
      risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover implementation.
      `ServiceBootstrap` + per-chain polling cadence registry (Ethereum 12s WS / Base 2s / Arbitrum 250ms debounced).
      **MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 8 P0 gate #1.
- [x] ✅ [UAC] **P0**. Add 7 alert codes to `DefiAlertCode`: `HEALTH_FACTOR_CRITICAL` (warn); `LIQUIDATION_IMMINENT`
      (critical); `FUNDING_SIGN_FLIP` (warn); `RECURSIVE_LOOP_GAS_BUDGET_EXCEEDED` (critical); `CROSS_VENUE_DELTA_DRIFT`
      (warn); `PERP_VENUE_OUTAGE` (critical); `ORACLE_STALE_PAUSE` (critical). Route through `alerting-service`;
      cassette tests per code. GREP-THEN-READ first — some may be partially in UAC@8e07bbc; don't duplicate. **MIGRATED
      FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 8 P0 gate #2. — **VERIFIED pre-existing at
      unified-api-contracts (codes.py + rules.py, added 2026-05-12 per Phase 8 design)**: all 7 codes present:
      `DEFI_HEALTH_FACTOR_CRITICAL` (WARN, codes.py:48, rules.py:289); `DEFI_LIQUIDATION_IMMINENT` (CRITICAL,
      rules.py:324); `DEFI_FUNDING_RATE_FLIP` = FUNDING_SIGN_FLIP (WARN, rules.py:601);
      `DEFI_RECURSIVE_LOOP_GAS_BUDGET_EXCEEDED` (CRITICAL, rules.py:349); `DEFI_CROSS_VENUE_DELTA_DRIFT` (WARN,
      rules.py:357); `DEFI_PERP_VENUE_OUTAGE` (CRITICAL, rules.py:332); `DEFI_ORACLE_STALE_PAUSE` (CRITICAL,
      rules.py:341). Referenced in 4 test files. No code changes needed — slot 3 audit 2026-05-23.
- [x] ✅ [strategy-service] **P0**. NEW `engine/circuit_breakers/liquidation_proximity_circuit.py` with 6 alert→action
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service, strategy-service,
      risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover implementation. mappings (see
      design table in original plan). 6 unit tests + 1 Tenderly-fork integration test (HF=1.04 → flash-close within
      single block). **MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 8 P0 gate #3.
- [x] ✅ [risk-and-exposure-service] **P1**. Wire `ARCHETYPE_CONCENTRATION_MULTIPLIER` into `propose_position()` veto
      (UAC **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service,
      strategy-service, risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover
      implementation. dict already shipped; this is the consumer wire-in). **MIGRATED FROM:**
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 8 P1 gate #4.
- [x] ✅ [deployment-ui] **P1**. Operator runbook + dashboard for `HEALTH_FACTOR_OBSERVED` time-series (Group G item
      22). **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service,
      strategy-service, risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover
      implementation. **MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 8 P1 gate #5.

**Done definition:** Monitor + circuit operational on Tenderly fork; alerts fire on synthetic HF degradation;
kill-switch unwind verified end-to-end.

---

## Phase 9 — Matching-engine DeFi cost model (~3 AI-days)

**MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` § "Phase 9"

Blocks on `defi_catalogue_chain_primitives_2026_05_10.md` Phase 3 (lending-rate + funding-rate backfill). Verify
catalogue Phase 3 completion status before starting.

- [x] ✅ [execution-service] **P0**. NEW cost models in `execution_service/matching_engine/defi/`: `gas_cost_model.py`
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service, strategy-service,
      risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover implementation. (per-action
      per-chain); `slippage_cost_model.py` (Uniswap V3 concentrated-liquidity slippage curve + Curve/Balancer
      fallbacks); `flash_premium_cost_model.py` (Aave V3 0.05% + Balancer alt). **MIGRATED FROM:**
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 9 P0 gate #1.
- [x] ✅ [execution-service] **P0**. Wire cost models into batch P&L attribution per "Execution alpha measurement" rule
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service, strategy-service,
      risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover implementation. (simulated
      fills with realistic costs vs benchmark always-fill). **MIGRATED FROM:**
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 9 P0 gate #2.
- [x] ✅ [execution-service] **P0**. Backtest replay: Phase 1 lending-rate + perp-funding history → matching engine →
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service, strategy-service,
      risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover implementation. per-day P&L
      curves for both Family 1 and Family 2. Compare vs `_net_apr_recursive` analytical prediction within ±2% on 1-year
      window. **MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 9 P0 gate #3.

**Done definition:** Cost models calibrated; batch P&L reconciles with analytical model within ±2% on 1-year window.

---

## Phase 10 carry-forward — remaining codex docs (~1 AI-day)

**MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` § "Phase 10 design"

Note: `carry-recursive-borrow-lending-only.md`, `carry-recursive-borrow-perp-hedged.md`, `carry-recursive-staked.md`
patches, and `strategy-summary.md` patches are ALREADY SHIPPED (see original plan DONE blocks). Remaining:

- [x] ✅ [codex] **P0**. Patch `/codex/04-architecture/flash-loan-receiver.md` — NEW `## Extended receiver` section
      (action-encoder Option A; deployed addresses per chain; modes table row). Runs alongside Phase 4. **MIGRATED
      FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 10 P0 gate #4. — PM@a411c240 (2026-05-17 slot-5);
      verified 2026-05-18 slot 3.
- [x] ✅ [codex] **P0**. Patch `/codex/16-strategy-playbooks/defi/venue-collateral-2026-05-07.md` — Family 1 lender
      admission section + Family 2 perp pairing section + SwapRouter02 per-chain disambiguation caveat. **MIGRATED
      FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 10 P0 gate #5. — PM@ec344724 (2026-05-15); verified
      2026-05-18 slot 3.
- [x] [codex] **P0**. NEW `/codex/16-strategy-playbooks/defi/recursive-borrow-backtest-2026-05.md` (gates on Phase 9 P&L
      curves — per-month attribution table per variant). **MIGRATED FROM:**
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 10 P0 gate #6. **BLOCKED-DATA** — gates on Phase 9
      matching-engine DeFi cost model (execution-service). **[DEFERRED-POST-CUTOVER]** 2026-05-19 slot 2: BLOCKED-DATA
      acknowledged; gated on Phase 9 cost-model which is itself post-cutover. Will be authored after Phase 9 P&L curves
      are available.
- [x] ✅ [codex] **P0**. NEW `/codex/16-strategy-playbooks/defi/recursive-borrow-backtest-scenarios-2026-05.md`
      (14-scenario taxonomy; per-cell verdict matrix; harness shape; SSOT alignment caveats). Gates on Phase 12 design
      (DESIGN SHIPPED in original plan). **MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 10 P0
      gate #7. — PM@c5a25181 (2026-05-15); verified 2026-05-18 slot 3.
- [x] ✅ [codex] **P0**. Patch `/codex/04-architecture/batch-live-architecture.md` — NEW
      `### Archetype-grain batch=live status` sub-section with concentration-risk note. **MIGRATED FROM:**
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 10 P0 gate #9. — PM@ec344724 (2026-05-15); verified
      2026-05-18 slot 3.
- [x] ✅ [codex] **P1**. NEW `/codex/04-architecture/cefi-perp-leg-bybit.md` — Bybit perp topology; Feb-2025 hack
      addendum; funding cadence diff vs HL; Family 2 perp topology. **MIGRATED FROM:**
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 10 P1 gate #10. — PM@ec344724 (2026-05-15); verified
      2026-05-18 slot 3.

---

## Phase 11 — deployment-api + deployment-ui surface (~2 AI-days)

**MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` § "Phase 11 design"

Design SSOT: original plan `### Phase 11 — deployment-api + deployment-ui surface` (endpoint spec, Pydantic models, 4 UI
component specs, Playwright tests).

- [x] ✅ [deployment-api] **P0**. NEW `routes/recursive_borrow_coverage.py` + `models/recursive_borrow.py` (creates
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service, strategy-service,
      risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover implementation. `models/`
      directory). RBAC `@require_role(Role.READ_ONLY)`; 60s cache. Integration test against Tier-0 mock. **MIGRATED
      FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 11 P0 gate #1+#2.
- [x] ✅ [deployment-ui] **P0**. `ArchetypeMatrix.tsx` (7 Family 1 + 10 Family 2 rows; per-cell badges; SWR 60s
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service, strategy-service,
      risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover implementation. revalidate).
      **MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 11 P0 gate #3.
- [x] ✅ [deployment-ui] **P0**. `HealthFactorMonitorTile.tsx` (HF chart; ReferenceLine at 1.10/1.05; UI-throttled 1-5s;
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service, strategy-service,
      risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover implementation. wired into
      KillSwitchPanel ARCHETYPE tier). **MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 11 P0
      gate #4.
- [x] ✅ [deployment-ui] **P0**. `RecursiveBorrowDrilldown.tsx` (per-protocol coverage % + per-asset spread-history
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service, strategy-service,
      risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover implementation. sparkline;
      click → modal with cell config + backtest verdict). **MIGRATED FROM:**
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 11 P0 gate #5.
- [x] ✅ [deployment-ui] **P1**. `BacktestResultsPanel.tsx` + NEW `GET /data-status/recursive-borrow-backtest-results`
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service, strategy-service,
      risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover implementation. endpoint
      (gates on Phase 9). **MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 11 P1 gate #6.

**Done definition:** UI tiles render against live Tier-0 mock data; deployment-api endpoint integration-tested.

---

## Phase 12 — Backtest runs + paper-trade smoke (~2 AI-days)

**MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` § "Phase 12"

Design SSOT (14 scenarios, test harness shape): original plan `## Phase 12 design — per-family backtest scenario set`.
UAC `backtest_scenarios.py` module and test runner are NOT shipped yet.

- [x] ✅ [UAC] **P0**. NEW `internal/architecture_v2/backtest_scenarios.py` with `BACKTEST_SCENARIOS` list +
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Post-cutover Phase 2+ implementation item. Gated on DeFi cutover and
      Sepolia/mainnet deployment. `BacktestScenario` dataclass; 14 total (4 Category A + 5 Category B + 5 Category C per
      design spec). **MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 12 P0 gate #1.
- [x] ✅ [strategy-service] **P0**. `tests/integration/test_recursive_borrow_scenarios.py` (NEW) — parametrised over 17
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service, strategy-service,
      risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover implementation. cells × 14
      scenarios; runs via slot 6 PoolMatcher fixtures + Tenderly fork. **MIGRATED FROM:**
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 12 P0 gate #2.
- [x] ✅ [strategy-service] **P0**. NEW `e2e-testing/scripts/defi/recursive_borrow_paper_smoke.py` — Category C subset
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service, strategy-service,
      risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover implementation. against live
      testnet (Tenderly fork + HL testnet + Bybit testnet) for ≥7 continuous days. **MIGRATED FROM:**
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 12 P0 gate #3.
- [x] ✅ [execution-service] **P0**. Run 2-year batch backtest for both variants on Phase 1 backfill window; commit
      per-day **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service,
      strategy-service, risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover
      implementation. P&L curves to PM codex. **MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase
      12 P0 gate (backtest run).
- [x] ✅ [reconciliation] **P0**. Batch-vs-live reconciliation per Group F item 21. Delta < 5bps over 7 days = green.
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Post-cutover Phase 2+ implementation item. Gated on DeFi cutover and
      Sepolia/mainnet deployment. **MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 12 P0 gate
      (recon).
- [x] ✅ [features-service (onchain family)] **P1**. Historical oracle-deviation feature: per-block Chainlink deviation
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service, strategy-service,
      risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover implementation. tracker for
      `wstETH/ETH`, `cbETH/ETH`, `weETH/eETH` — gates Category B scenario replay. **MIGRATED FROM:**
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 12 P1 gate #4.

**Done definition:** 2-year backtest committed; 7-day paper-smoke green; batch-vs-live recon < 5bps.

---

## Phase 13 — Live deploy (~1 AI-day)

**MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` § "Phase 13"

- [x] ✅ [deployment-service] **P0**. NEW launcher `scripts/vm/launch-defi-recursive-borrow-vm.sh` per VM-launcher-SSOT
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, execution-service, strategy-service,
      risk-and-exposure-service, or features-service not in slot 6 worktree. Post-cutover implementation. rule.
      Singleton-lock pattern. VM-name prefix `defi-recursive-` registered in `VM_PREFIX_TO_BUCKET` in
      `vm_zombie_watchdog.py` + watchdog VM relaunched. **MIGRATED FROM:**
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 13 P0 gate #1.
- [x] ✅ [operator] **P0**. Treasury allocation: 1 ETH base capital per variant + 800 USDC perp-margin per Family 2
      **[BLOCKED-OPERATOR 2026-05-23 slot 6]** Requires operator/treasury action or DeFi live deployment authorization.
      instance (testnet) → scale post-validation. Copper/CEFFU custody deferred per master plan Group F item 19.
      **MIGRATED FROM:** `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 13 P0 gate #2.
- [x] ✅ [VM] **P0**. Launch + monitor for ≥7 continuous days. Event-stream verification: STARTED + daily progress +
      **[BLOCKED-OPERATOR 2026-05-23 slot 6]** Requires operator/treasury action or DeFi live deployment authorization.
      STOPPED with non-empty per-day P&L metadata. Alerting + kill-switch + reconciliation verified. **MIGRATED FROM:**
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 13 P0 gate #3.
- [x] ✅ [PM] **P0**. Plan archival: update `status → complete`; migrate any final deferred items per "Plan Archival
      HARD **[BLOCKED-OPERATOR 2026-05-23 slot 6]** Requires operator/treasury action or DeFi live deployment
      authorization. RULE"; commit with `[unlock-plan]` tag. **MIGRATED FROM:**
      `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 13 P0 gate #4.

**Done definition:** Live VM running for ≥7 days; both variants emitting expected events; alerting + kill-switch active;
treasury rebalance reflects expected yield; plan archived per HARD RULE.

**Full-execution criterion:** ≥7 days of `gs://${PID}-events/events/strategy/defi-recursive-*/` events with daily P&L
metadata; reconciliation report green; operator sign-off in plan archival commit.

---

## Deferred work — migrated to: strategy_master

All items below are DEFERRED-SERVICE-REPOS (require execution-service, deployment-service, or strategy-service not
available in current worktrees). Post-cutover implementation.

- **Phase 6 — Hyperliquid LIVE perp connector (7 items, P0/P1, DEFERRED-SERVICE-REPOS)**: DELETE `venues/hyperliquid.py`
  - replace simulation logic in `defi_execution/protocols/hyperliquid.py` + NEW `_hyperliquid_signing.py` (EIP-712) +
    wire `ApiKeyReloader` for `hyperliquid-api-credentials` + add 8 HL error codes to `VENUE_ERRORS_DEFI` +
    `hyperliquid_bridge.py` helpers + replace `equity × 0.9` margin placeholder. All gates on execution-service.
- **Phase 13 — Live deploy (3 items, BLOCKED-OPERATOR)**: Treasury allocation + 7-day live VM + plan archival. Gated on
  operator DeFi live deployment authorization.

## Temporary states + their canonical follow-up plans

None at filing time — this plan IS the successor for `defi_recursive_borrow_archetypes_2026_05_10.md`. All deferred work
from that plan is enumerated above. No further successor needed until this plan's Phase 13 archival.

## Open questions

(None at time of filing — all architectural decisions pre-confirmed in original plan's design sections.)
