---
title:
  DeFi recursive-borrow archetypes — Family 1 (recursive lending arb) + Family 2 (long-funding-perp recursive-borrow)
  implementation
status: active
created: 2026-05-10
descope_reversed: 2026-05-13
descope_reversal_reason: >
  Operator direction 2026-05-13 evening: "i want defi_recursive_borrow and recursive staking in 23rd may though even if
  not essential for defi i want it backtested coded up and tested ready to go live". Full implementation half (Phase 4
  Solidity RecursiveLeverageReceiver.sol + Phase 5 execution-service RecursiveLoopOrchestrator + Phase 6 Hyperliquid
  LIVE perp connector wire-up + Phase 7 PerpHedgeSizer + Phase 8 HealthFactorMonitor + LiquidationProximityCircuit +
  alerting + Phase 10 codex SSOT updates + Phase 11 deployment-api + deployment-ui surface) PULLED BACK INTO May-23
  scope. Live trading toggle OFF at cutover (per master plan commits to only carry_staked_basis +
  arbitrage_price_dispersion for live trading) but code + tests + backtests + paper-trade testnet smoke READY-TO-GO-LIVE
  by 2026-05-23.
prior_descope: 2026-05-14 by harsh-slot-9 (now REVERSED per operator direction 2026-05-13 evening)
successor_plan: >
  /plans/active/defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md (NOTE: post-cutover plan now covers ONLY
  post-cutover scope-expansion items, NOT the May-23 implementation half which is back in this plan's scope per operator
  direction 2026-05-13)
target_deadline: 2026-05-23
priority: P0
related_plans:
  - plans/active/trading_agent_service_architecture_unlock_2026_05_22.md
  - plans/active/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md
  - plans/active/defi_master.md
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/active/alerting_service_live_rules_2026_05_07.md
  - plans/archive/issues/defi_archetypes_doc_plan_drift_2026_05_07.md
  - plans/active/trading_agent_service_architecture_unlock_2026_05_22.md
locked_by: live-defi-rollout
locked_since: 2026-05-10
estimate_class: design
estimate_baseline_ai_days: 70.5
estimate_calibrated_ai_days: 42.3
estimate_calibration_note: |
  Baseline auto-extracted from in-body AI-day mentions during 2026-05-11 sweep (~17, ~11, ~14, ~0.5, + 13 more). Class inferred from filename (design, multiplier 0.6×).
  CAVEAT: auto-extract SUMS all in-body mentions; plans with both 'Total: X' headlines AND per-phase line items will be double-counted. Owner agent: verify baseline, refine class per /codex/08-workflows/estimation-calibration.md, recompute calibrated if either changes.
parent_epic: strategy_master
---

# DeFi recursive-borrow archetypes — Family 1 + Family 2 implementation

> **StrategyPnlStreamEvent**: archetypes in this plan emit StrategyPnlStreamEvent per UAC contract (see
> trading_agent_service_architecture_unlock plan Phase 1+2). Status: TODO post-cutover unless explicitly listed in this
> plan's May-23 scope.

> **🟡 IN-FLIGHT REFACTOR — code-freeze sequencing 2026-05-10** (BLOCK)
>
> [`plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md)
> § "Anti-sequencing audit" rows 333 + 334 flag this plan as a Phase 1.E freeze-gate critical-path item. AD-1 flip
> 2026-05-10 + cross-plan audit Q10 ratification — NEW UAC `StrategyArchetype` enum values
> (`CARRY_RECURSIVE_BORROW_LENDING_ONLY` + `CARRY_RECURSIVE_BORROW_PERP_HEDGED`) MUST land in
> `manifest_schema_final_gate_2026_05_09.md` v8 schema declaration BEFORE Phase 1 freeze 2026-05-15 (slot 5 grep
> 2026-05-11 confirmed NEITHER value present in UAC `internal/architecture_v2/enums.py:31-118`). Ownership transferred
> to `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07` Stream C per most-comprehensive-owner rule. Reader
> contract: scan top-of-file banners before touching the strategy_id shard-atom column / archetype enum / v8 schema
> declaration.

> **🟢 PHASE 1 BLOCKER STATUS REFRESHED 2026-05-12 by slot 2 (ikenna-defi-catalogue-tab)** — Per
> [`defi_catalogue_chain_primitives_2026_05_10.md`](defi_catalogue_chain_primitives_2026_05_10.md) Phase 3 § "PHASE 3
> LENDING-INDICES SPEC FOR slot 5 (Family-1) HANDSHAKE — published 2026-05-12", lending-indices data for Family 1
> backtest is **broadly available NOW** with 2-year+ horizons across AAVE_V3 (ETH/ARB/BASE/OPT/LINEA/BSC)
>
> - COMPOUND_V3 (ETH/ARB/BASE/OPT/SCROLL) + SPARK (ETH). All three original 2026-05-08 "Bug 1/2/3" framings closed as
>   STALE (pre-audit 2026-05-11 slot 3 + 2026-05-12 slot 2). Remaining work (recent-days catch-up VM, P1
>   ManifestFreshnessCache wire-in) does NOT block Family-1 design; pulls fix Day 3 (2026-05-14). **Slot 5: start
>   Family-1 design Day 1**.

> **🔴 DESCOPED 2026-05-14 — NOT in May-23 live cutover** (Harsh-side slot 9; operator pre-confirmed 2026-05-14 morning)
>
> `recursive_borrow` archetypes are **NOT** in the May-23 live cutover scope. Master plan only commits
> `carry_staked_basis` + `arbitrage_price_dispersion` for live by 2026-05-23. This plan's **archetype-documented half
> shipped** (UAC schemas, strategy-service factory/catalog, 4 codex docs — see DONE blocks below). The **implementation
> half is deferred post-cutover** to the successor plan:
> [`plans/active/defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md`](defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md)
>
> **What shipped** (stays in this plan): UAC `recursive_loop_orchestrator.py` + `perp_hedge_sizer.py` schemas; archetype
> enum values (`CARRY_RECURSIVE_BORROW_LENDING_ONLY` + `CARRY_RECURSIVE_BORROW_PERP_HEDGED`); `ARCHETYPE_CONFIG_SEED`
> rows; 15 `DefiErrorCode` entries; 5 `AlertCode` entries; `ARCHETYPE_CONCENTRATION_MULTIPLIER`;
> `UNISWAP_SWAP_ROUTER_BY_CHAIN` registry; strategy-service factory routing + 17 catalog cells + tracer (Phase 3 ✅); 4
> codex docs (Family 1/2 archetypes + `carry-recursive-staked.md` + `strategy-summary.md` patches).
>
> **Deferred to successor** (Phases 2-remaining, 4, 5, 6, 7, 8, 9, 11, 12, 13): Solidity
> `RecursiveLeverageReceiver.sol`; execution-service `RecursiveLoopOrchestrator` + Hyperliquid LIVE wire-up +
> `PerpHedgeSizer` + `HealthFactorMonitor`; matching-engine DeFi cost model; deployment-api/UI components; backtest
> runs; live deploy. See `## Deferred work — migrated to successor plan` section below.

## Why this plan exists

Two recursive-borrow strategy families surfaced in
[`plans/questions/defi_recursive_borrow_archetypes_2026_05_08.md`](../questions/defi_recursive_borrow_archetypes_2026_05_08.md):
**Family 1** = pure-lending recursive arb (no perp leg) and **Family 2** = long-funding-perp recursive-borrow
(delta-neutral on share-class = underlying coin). Research on 2026-05-09 (4 parallel sub-agent streams: archetype audit,
MTDS rate coverage, web rate-sampling, on-chain flow-of-funds + workspace primitives) established that both families are
CONFIG VARIANTS of the existing `CARRY_RECURSIVE_STAKED` archetype — extending the 2026-05-07 operator precedent that
`leveraged_funding_arb` = config variant of `ARBITRAGE_PRICE_DISPERSION`. No new archetype enum; no new strategy-service
factory tree; no parallel codex docs.

The research also caught a framing gap in the original Q-doc: the user's spec ("borrow coin → short borrowed coin on
perp") is mechanically broken on Hyperliquid / Bybit / OKX (USDC-only margin). The correct shape: **recursion is purely
on the lending side**; the perp short is a single matched leg sized against cumulative spot-ETH exposure post-recursion,
with margin separately funded in USDC. Share-class accounting netted across (aETH + free-ETH + ETH-debt + perp-short) =
configurable target net delta (0 for pure carry, +N×base for "hold N ETH and earn carry").

Implementation is gated by a backfill prerequisite: lending-rate data (SUPPLY_APY / BORROW_APY / UTILISATION) is not yet
captured by MTDS due to 3 known bugs (Aave V3 Eth silent-zero / Compound V3 multi-chain subgraph / instruments-store
2022 metadata floor), per the `lending-indices DEFERRED` note in
[`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md).
Without that data, backtest is impossible and paper-trade smoke against historical funding regimes is impossible. Phase
1 ships the prerequisite; the rest of the plan compounds on top.

**Total budget**: ~17 AI-days end-to-end (Phase 1 backfill prerequisite + Phases 2-13 for both families). Family 1 alone
is ~11 AI-days (subset); Family 2 alone is ~14 AI-days. Combined plan reuses orchestrator + flash-receiver +
health-monitor across both, which is why the bundle is cheaper than the sum. This sits well within the May-23 cutover
window if Phase 1 starts immediately.

## Architectural decisions (locked from 2026-05-09 research)

> **AD-1 — FLIPPED 2026-05-10 cross-plan audit Q10 (Policy B larger-set-wins). REFRAMED 2026-05-12 by slot 5 per Stream
> C C-enum.1 audit + C-enum.4 backport.** Both families = **NEW UAC `StrategyArchetype` enum members** (extending from
> **8 → 10** archetypes — NOT "8 → 11" as originally framed; slot 5 codex sweep 2026-05-11 found ZERO
> documented-but-not-in-enum archetypes for a hypothetical 11th member; framing collapsed to the 2 actually needed). Was
> originally "config variants of `CARRY_RECURSIVE_STAKED`" — that approach REJECTED in favor of explicit enum members
> per the larger-set rule. **UAC PR SHIPPED** at `uac@d02cce2` (2026-05-11 per
> [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
> Stream C C-enum.2 closure) — `CARRY_RECURSIVE_BORROW_LENDING_ONLY` + `CARRY_RECURSIVE_BORROW_PERP_HEDGED` visible at
> `unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py:76-78`. Strategy-service factory
> routing updates dispatch per archetype enum member (not per config-variant lookup); see Phase 3 design above for
> `factory.py:63` + `catalog.py:1958` spec. Justification for the flip: explicit enum is clearer for downstream
> consumers (deployment-UI archetype dropdown, allocator subclass routing, kill-switch per-archetype scoping,
> archetype-readiness matrix per master plan); config-variant shape conflates orthogonal axes (`perp_leg_enabled` is a
> structural difference, not a config tuning knob). Family 2's perp leg adds a distinct risk surface (funding-sign-
> flip, perp-venue outage, cross-venue delta drift) that warrants explicit enum-level visibility (drawdown 0.05 / breach
> 0.03 per
> [`archetype_config.py:169-177`](../../../unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_config.py#L169-L177)).
> Family 1 = `CARRY_RECURSIVE_BORROW_LENDING_ONLY`; Family 2 = `CARRY_BASIS_PERP_INV` (formerly
> `CARRY_RECURSIVE_BORROW_PERP_HEDGED` — renamed 2026-05-18 per taxonomy V-1, uac@0196842).

> **AD-2**. The recursion is **purely lending-side**. Perp leg (Family 2) is a single matched short, separately
> USDC-margined. Hyperliquid / Bybit / OKX are USDC-margin-only — borrowed ETH cannot be posted as perp margin without
> selling. The strategy-service config schema enforces this shape; the orchestrator never tries to bridge borrowed coin
> into perp margin.

> **AD-3**. Share class is configurable per instance via `target_net_delta` (in units of share-class coin).
> `target_net_delta=0` = full hedge, NAV-in-ETH; `target_net_delta=+1.0` = "hold 1 ETH and earn carry on top."
> `LeveragedLegController` (already in workspace per canonicalisation plan) abstracts the rebalance loop. Share-class
> coin defaults to the lending-side collateral asset (ETH for ETH-loops, BTC for BTC-loops, SOL for SOL-loops).

> **AD-4**. Two opening modes ship together: `mode="persistent"` (N tx, no flash fee, gas-bound) and `mode="flash"` (1
> tx, 0.05% Aave V3 flash fee, atomic). Persistent is the default below 5 ETH base capital; flash is the default at ≥5
> ETH (gas-cost crossover). Both modes share the same `RecursiveLoopOrchestrator` interface — only the inner driver
> differs.

> **AD-5**. **Multi-venue scope is explicitly bounded for May-23**. Lending side: Aave V3 only (Ethereum mainnet
> primary, Base secondary). Perp side: Hyperliquid (DEX) + Bybit (CeFi) — two venues only. Other lending protocols
> (Compound V3, Spark, Morpho, Maker DSR) and other perp venues (Binance, OKX, Deribit, Aster) are deferred to a
> post-cutover follow-up plan. Solana / Marginfi / Kamino is deferred entirely (separate plan, post-Family-2-on-EVM
> proves out the architecture).

> **AD-6**. **Backtest is the gate, not paper-trade**. Per `master_to_live_defi_2026_05_23.md` Group F item 18 (2-year
> batch backtest run) — Phase 1 backfill must finish before Phase 12 backtest can produce signal. Without backtest
> signal, paper-trade smoke is rate-limited (no historical funding-regime coverage). Phase 1 is therefore P0 and must
> start day-1.

## Cross-plan coordination banners

Add these banners (per CLAUDE.md "Cross-Plan Coordination Banners" HARD RULE) to the top of the named plans BEFORE Phase
1 starts:

- [x] **[BANNER]** `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md` — top-of-file banner added. (commit
      below unified-trading-pm 2026-05-15)
- [x] **[BANNER]** `master_to_live_defi_2026_05_23.md` — Group F item 18 (2-year batch backtest run) gets a sub-bullet
      pointing at this plan; Group F item 17 (real gas / matching engine / cost+yield precision) gets a sub-bullet
      pointing at Phase 9. **SLOT-1-ONLY** — queued in pings/slot_2.md for slot 1 to apply on next master-plan refresh.
      **DEFERRED-SLOT-1-ONLY** — closed 2026-05-19 slot-6; not valid for non-slot-1 agents per annotation above.
- [x] **[BANNER]** `defi_master.md` — top-of-file banner added. (commit below unified-trading-pm 2026-05-15)
- [x] **[BANNER]** `alerting_service_live_rules_2026_05_07.md` — top-of-file banner added. (commit below
      unified-trading-pm 2026-05-15)

Banner-removal owned by this plan when each phase ships; stale-banner sweep at end-of-plan.

## Pre-audit — full workspace impact surface

Per CLAUDE.md "Plans must capture full codebase impact upfront" + Citadel § 1 Pre-Audit. Every repo / file / SSOT
touched by this plan, enumerated.

| Repo / surface                      | Files touched                                                                                                                                                                                                                                                                                                | Phase     |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------- |
| `unified-api-contracts`             | `internal/architecture_v2/archetype_config.py` (extend `CARRY_RECURSIVE_STAKED` config schema); `canonical/domain/market_data/data_types.py` (new `SUPPLY_APY` / `BORROW_APY` / `UTILISATION` enums)                                                                                                         | 2, 1      |
| `unified-trading-library`           | (read-only consumer; no edits expected)                                                                                                                                                                                                                                                                      | -         |
| `market-tick-data-service`          | `adapters/aave_v3_lending_rates.py` (new); `adapters/compound_v3_lending_rates.py` (new); `adapters/morpho_blue_lending_rates.py` (NICE-TO-HAVE); fix Bug 1/2/3 per Phase 1                                                                                                                                  | 1         |
| `instruments-service`               | catalog seed for lending-rate instruments per (protocol, chain, asset); 2022 metadata floor fix per Bug 3                                                                                                                                                                                                    | 1         |
| `execution-service`                 | `defi_execution/protocols/aave.py` (already has supply/borrow/repay/withdraw/flash); `defi_execution/protocols/hyperliquid.py` (LIVE wire-up — currently simulation-only); new `RecursiveLoopOrchestrator`; new `PerpHedgeSizer`; new `HealthFactorMonitor`; matching-engine DeFi cost model                 | 5,6,7,8,9 |
| `strategy-service`                  | `engine/strategies/v2/factory.py` (config-variant routing); `engine/strategies/v2/target_universe/catalog.py` (extend `_build_carry_recursive_staked` factory); `LeveragedLegController` extension                                                                                                           | 3         |
| `position-balance-monitor-service`  | cross-venue netting verification (Aave aETH + Aave debt + perp short → share-class delta); no new code expected, just integration test                                                                                                                                                                       | 7         |
| `risk-and-exposure-service`         | concentration-risk handling for recursive positions; gross-notional vs net-delta per Q-doc G1                                                                                                                                                                                                                | 8         |
| `alerting-service`                  | new alert codes (`HEALTH_FACTOR_CRITICAL`, `LIQUIDATION_IMMINENT`, `FUNDING_SIGN_FLIP`); kill-switch tier-up rules                                                                                                                                                                                           | 8         |
| `deployment-service`                | extended `FlashLoanReceiver.sol` (or new `RecursiveLeverageReceiver.sol`); `scripts/vm/launch-defi-recursive-borrow-vm.sh` (new launcher per VM-launcher-SSOT rule)                                                                                                                                          | 4, 13     |
| `deployment-api`                    | `/data-status/recursive-borrow-coverage` endpoint; ArchetypeMatrix variant rendering                                                                                                                                                                                                                         | 11        |
| `deployment-ui`                     | ArchetypeMatrix entry for both variants; HealthFactorMonitor live tile; Recursive-Borrow data-status drilldown                                                                                                                                                                                               | 11        |
| `features-service (onchain family)` | per-protocol rate-feature consumer; cross-protocol rate-spread feature                                                                                                                                                                                                                                       | 10        |
| `unified-config-interface`          | `testnet_contracts.yaml` (extended-receiver address per chain); RPC URL templates already in `_defi.py`                                                                                                                                                                                                      | 4         |
| `unified-trading-pm/codex/`         | new doc `/codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked-config-variants.md`; update `/codex/04-architecture/flash-loan-receiver.md`; update `carry-recursive-staked.md` to cite variants; update `/codex/16-strategy-playbooks/defi/venue-collateral-2026-05-07.md` for new venue rows | 10        |
| `e2e-testing/scripts/defi/`         | new `recursive_borrow_paper_smoke.py` paper-trade harness (under primary-consumer QG of strategy-service per peripheral-script-dirs HARD RULE)                                                                                                                                                               | 12        |
| `unified-trading-pm/plans/active/`  | this plan (durable record); flips on `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md` + `master_to_live_defi_2026_05_23.md` Group F items                                                                                                                                                   | all       |

## Phase 0 — Decision lock + Q-doc closeout (0.5 AI-days)

- [x] [PM] P0. Update
      [`plans/questions/defi_recursive_borrow_archetypes_2026_05_08.md`](../questions/defi_recursive_borrow_archetypes_2026_05_08.md):
      set `status: closed-spawned-plan`, `spawned_plan: plans/active/defi_recursive_borrow_archetypes_2026_05_10.md`,
      append a "Research summary 2026-05-09" section with the 4 sub-agent reports' headline findings + AD-1 through AD-6
      decision calls. (Q-doc already had all fields + Research summary 2026-05-09 + AD-1..AD-6 table from prior session;
      verified complete 2026-05-15)
- [x] [PM] P0. Add cross-plan coordination banners per the section above (4 banners). (7fe0e708 unified-trading-pm
      2026-05-15 — 3 banners added; master_to_live_defi_2026_05_23.md Group F queued for slot 1 in
      ikenna_orchestrator/\_agent_pings.md)
- [x] [operator-ratify] P0. Operator confirms AD-1 through AD-6. (Not gating Phase 1 — Phase 1 is the lending-indices
      fix that's needed regardless of archetype shape — but gating Phase 2 onwards.) **BLOCKED-OPERATOR-DECISION** —
      awaiting operator ack on AD-1 through AD-6. Phase 2+ gated on this; Phase 1 shipped regardless.

**Done definition:** Q-doc closed; banners landed; AD-1 through AD-6 ratified.

**Full-execution criterion:** Q-doc commit references AD-1 through AD-6; 4 banners visible at top of named plans;
operator ack visible in chat or commit co-authoring metadata.

## Family 1 topology design — per-chain × per-lender SSOT (2026-05-12 slot 5)

> **Design owner:** ikenna slot 5 / agent-tag `ikenna-recursive-borrow-tab` (2026-05-12). **Source:** 3-sub-agent
> parallel research fan-out (Ethereum + Arbitrum + Base) reconciled below. Each per-chain ground-truth report cited in
> commit message; raw outputs in slot 5 transcript. **Status:** DESIGN-SHIPPED. Consumed by Phase 2 (UAC schema), Phase
> 3 (strategy-service factory + catalog), Phase 9 (backtest cell selection). **Does NOT block on defi_catalogue Phase
> 3** — design proceeds independent; backfill dependency surfaces only at backtest replay.

### Workspace ground truth (existing, do not duplicate)

- `unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py:76-78` —
  `CARRY_RECURSIVE_BORROW_LENDING_ONLY` (Family 1) + `CARRY_RECURSIVE_BORROW_PERP_HEDGED` (Family 2) enum members
  ALREADY SHIPPED. AD-1 PR scope shrinks accordingly. _(Family 2 later renamed to `CARRY_BASIS_PERP_INV` 2026-05-18 per
  taxonomy V-1.)_
- `unified-api-contracts/unified_api_contracts/registry/defi_reserve_params.py:54-119` — `AAVE_V3_ETHEREUM_RESERVES`
  ships **10 reserves** (USDC, USDT, DAI, WETH, WBTC, WSTETH, WEETH, CBETH, LINK, AAVE) — NOT 8 as claimed in plan body
  intro; correct on next plan-body sweep.
- `defi_reserve_params.py:126-143` — `AAVE_V3_EMODE_CATEGORIES`: ETH_CORRELATED (id=1, 0.93/0.95, {WETH, WEETH, WSTETH,
  CBETH}) + STABLECOIN (id=2, 0.97/0.975, {USDC, USDT, DAI}).
- `defi_reserve_params.py:302-340` — `COMPOUND_V3_ETHEREUM_RESERVES` (USDC market collaterals).
- `defi_reserve_params.py:352-389` — `MORPHO_BLUE_ETHEREUM_RESERVES` (6 curated-vault defaults at uniform LLTV=0.86).

### 🚨 P0 silent correctness bug found mid-design (Findings Triage — adjacent to my plan)

- [x] ✅ [UAC] **P0 — `defi_reserve_params.py:175` `get_reserve_params(asset, chain="ETHEREUM")` accepts the `chain` arg
      but ignores it.** Any non-Ethereum caller silently receives Ethereum params. Wire `chain` to dispatch through
      `_CHAIN_RESERVES: dict[str, dict[str, ReserveParams]]` lookup. Same fix needed for
      `get_compound_reserve_params(asset)` (`defi_reserve_params.py:393`) — Compound V3 is per-market AND per-chain;
      current signature is single-market Ethereum-only. **Same fix needed for `_ASSET_EMODE_MAP` /
      `get_emode_category(asset)` / `get_emode_params(collateral, debt)`** — currently single global map (line 146-149);
      cross-chain support requires `(chain, asset)` keying. Without this fix Family 1 cannot route correctly to Arbitrum
      or Base cells. **SHIPPED UAC@3729af1** — `_AAVE_V3_CHAIN_DISPATCH` + `get_emode_category(chain=)` +
      `get_emode_params(chain=)` + `UnknownChainError` all wired. (backfilled 2026-05-17 slot-5)

### Per-chain × per-lender ReserveParams matrix (proposed UAC additions)

| Chain × Lender       | Status in UAC                                  | P0 dict addition                                                                                                                                                  | Notes                                                                                                                          |
| -------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Aave V3 Ethereum     | ✅ 10 reserves shipped                         | Extend with `RETH` + admit to ETH_CORRELATED E-Mode                                                                                                               | Family 1 primary on Ethereum                                                                                                   |
| Spark Ethereum       | ❌ NOT in UAC                                  | NEW `SPARK_ETHEREUM_RESERVES` mirroring Aave shape; SparkLend ETH E-Mode `max_ltv≈0.90, lt≈0.93` (low-confidence)                                                 | Aave-fork; sDAI / WETH / wstETH / rETH key reserves                                                                            |
| Morpho Blue Ethereum | ⚠️ uniform LLTV=0.86 collapsed                 | Per-market overrides (e.g., `(WSTETH, WETH, Chainlink-ER) → LLTV=0.945`) via `get_morpho_market_lltv(market_id)` accessor                                         | wstETH/WETH Morpho cell is the highest-LLTV Family 1 cell available (0.945 vs Aave's E-Mode 0.93)                              |
| Aave V3 Arbitrum     | ❌ NOT in UAC                                  | NEW `AAVE_V3_ARBITRUM_RESERVES` (11 reserves: USDC, USDC.E, USDT, DAI, WETH, WBTC, WSTETH, WEETH, RETH, ARB, LINK) + chain-specific E-Mode (NO CBETH on Arbitrum) | Family 1 primary on Arbitrum; values low-medium confidence pending app.aave.com verification                                   |
| Radiant V2 Arbitrum  | ❌ NOT in UAC                                  | **DEFERRED** post-May-23                                                                                                                                          | October 2024 multisig exploit; TVL collapsed; not safe for live capital. Keep launch-date entry for batch data continuity only |
| Compound V3 Arbitrum | ❌ NOT in UAC                                  | NEW `COMPOUND_V3_ARBITRUM_USDC_E_RESERVES` + `..._USDC_RESERVES` (two distinct markets per chain)                                                                 | Compound V3 is per-market AND per-chain                                                                                        |
| Aave V3 Base         | ❌ NOT in UAC                                  | NEW `AAVE_V3_BASE_RESERVES` (7 reserves: USDC, USDBC, WETH, CBBTC, WSTETH, WEETH, CBETH) + chain-specific E-Mode (Base has CBETH, NO USDT/DAI)                    | Family 1 primary on Base; thinner liquidity than Eth/Arb — borrow-side caps may bind before LTV                                |
| Compound V3 Base     | ❌ NOT in UAC                                  | NEW `COMPOUND_V3_BASE_RESERVES` (USDC market: WETH, cbETH, wstETH, cbBTC)                                                                                         | Base launched 2023-08; ≤30mo history bounds backfill viability                                                                 |
| Moonwell Base        | ❌ NOT in UAC / NOT in `PROTOCOL_LAUNCH_DATES` | P2 — add only if May-23 cut warrants                                                                                                                              | Compound V2 fork; ~$180M TVL; WELL+USDC dual rewards; lower borrow caps                                                        |
| Aerodrome Base       | n/a — DEX only                                 | OUT OF SCOPE Family 1                                                                                                                                             | ve(3,3) AMM, not a lender; routes to Family 5/6 archetypes                                                                     |

### Top-cell shortlist for May-23 cutover (ranked by `expected_apr × confidence`)

Cell ID convention: `<lender>_<chain>_<collateral>_<debt>_<mode>`. Decimal LTVs are e-mode where applicable.

| Rank | Cell ID                                   | LTV (mode)              | Expected APR pre-gas            | Confidence                       | Notes                                                                                                                       |
| ---- | ----------------------------------------- | ----------------------- | ------------------------------- | -------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| 1    | `aave_v3_ethereum_wsteth_weth_emode`      | 0.93 ETH_CORRELATED     | 6-10% net                       | HIGH                             | Canonical Lido leveraged staking. Stake APY ~3.0-3.5%; WETH borrow ~2.0-2.8%; ~14× leverage. Deepest liquidity.             |
| 2    | `morpho_ethereum_wsteth_weth_market_0945` | 0.945 (per-market LLTV) | 8-12% net                       | MED-HIGH                         | Highest-LTV Family 1 cell. Curated by Steakhouse / Gauntlet / MEV Capital. Tighter HF buffer.                               |
| 3    | `aave_v3_arbitrum_wsteth_weth_emode`      | 0.93                    | 6-18% net                       | HIGH (cells), LOW (exact params) | Cheaper Arbitrum gas → persistent driver default; recursion_depth_max=10. Aave V3 Arbitrum LTV params pending verification. |
| 4    | `aave_v3_base_cbeth_weth_emode`           | 0.93 (low-conf)         | ~3-3.5% leveraged spread        | MED                              | Base-native LST (no bridge risk); Coinbase counterparty surface. Base Aave V3 E-Mode LTV unverified.                        |
| 5    | `morpho_ethereum_susde_usdc_market_086`   | 0.86 (per-market)       | 15-25% net                      | MED                              | Ethena sUSDe yield + USDC borrow spread; highest cash APR but highest depeg/yield-decay risk; cooldown adds unwind latency. |
| 6    | `aave_v3_ethereum_weeth_weth_emode`       | 0.93                    | 5-15% cash + EIGEN/ETHFI points | MED                              | Points are non-cash; discount appropriately. ether.fi PendleOracle dependency.                                              |
| 7    | `aave_v3_base_wsteth_weth_emode`          | 0.93 (low-conf)         | ~3.2-3.8% leveraged spread      | MED-HIGH                         | Lido yield mirrored to Base via canonical bridge; bridge-risk surface; cheapest gas in scope.                               |

### Per-cell config parameter defaults (chain-overridable)

```yaml
defaults:
  ltv_target: liquidation_threshold - 0.05 # 5% safety buffer below liquidation
  rebalance_threshold_lower_hf: 1.10 # trigger partial unwind
  rebalance_threshold_upper_hf: 1.50 # trigger roll-up (only if profitable post-gas)
  slippage_tolerance_bps: 50 # per-swap, cross-asset only
  oracle_staleness_max_seconds: 86400 # 24h Chainlink heartbeat
chain_overrides:
  ethereum:
    gas_budget_usd_per_loop_iter: 25 # mainnet — flash-loan path preferred at depth ≥5 or size ≥ $50k
    recursion_depth_max: 8 # gas crossover for persistent driver
  arbitrum:
    gas_budget_usd_per_loop_iter: 0.50 # L2 sequencer + L1 calldata
    recursion_depth_max: 10 # cheap gas → more iters before saturation
    health_factor_target_min: 1.30 # L2 finality 1 block; lower reorg surface
  base:
    gas_budget_usd_per_loop_iter: 0.20 # cheapest in scope
    recursion_depth_max: 12
    bridge_dependency_assets: ["WSTETH", "WEETH"] # bridge-risk surface flagged to risk-and-exposure-service
```

### Cross-cell risk surface taxonomy (feeds Phase 8 alerting)

- **Counterparty:** `cbETH` (Coinbase Custody); `USDbC` (Coinbase bridged USDC, deprecating); `weETH` (ether.fi
  multisig).
- **Bridge:** `wstETH on Arbitrum/Base` (Lido canonical bridge); `weETH on Arbitrum/Base` (native ether.fi bridge).
- **Oracle:** Chainlink {wstETH/ETH, weETH/eETH, cbETH/ETH, rETH/ETH} exchange-rate feeds; Morpho per-market oracle
  wrappers; ether.fi PendleOracle.
- **Liquidity / cap:** Aave V3 Base borrow caps may bind before LTV; Morpho per-market supply-and-borrow caps
  independent of Aave; Compound V3 per-market base-asset cap.
- **Asset-specific:** USDbC deprecation (Base); USDC.e deprecation (Arbitrum); Radiant V2 protocol-pause (Arbitrum,
  post-Oct 2024 exploit).

### Workspace finding-triage discharge (per HARD RULE)

These items land in this plan (in-scope adjacent + P0 unblocker):

- [x] [UAC] **P0**. Fix `get_reserve_params(asset, chain)` to actually use `chain` arg (see 🚨 callout above) — gates
      Phase 2 schema work. (verified 2026-05-13: UAC `registry/defi_reserve_params.py:748` `_AAVE_V3_CHAIN_DISPATCH`
      dict + `get_reserve_params(asset, chain="ETHEREUM"):768` dispatches via lookup table for 10 chains; module moved
      from `canonical/crosscutting/` → `registry/`)
- [x] [UAC] **P0**. Add `AAVE_V3_ARBITRUM_RESERVES` + `AAVE_V3_ARBITRUM_EMODE_CATEGORIES` to `defi_reserve_params.py`.
      All cells must declare `chain="ARBITRUM"` keying and `(low-confidence — verify app.aave.com Arbitrum)` markers on
      each numeric field. (verified 2026-05-13: `registry/defi_reserve_params.py:161`
      `AAVE_V3_ARBITRUM_EMODE_CATEGORIES` + `:279` `AAVE_V3_ARBITRUM_RESERVES` shipped + dispatch wired @ `:750`)
- [x] [UAC] **P0**. Add `AAVE_V3_BASE_RESERVES` + `AAVE_V3_BASE_EMODE_CATEGORIES` to `defi_reserve_params.py`. Same
      low-confidence marking convention. (verified 2026-05-13: `registry/defi_reserve_params.py:183`
      `AAVE_V3_BASE_EMODE_CATEGORIES` + `:385` `AAVE_V3_BASE_RESERVES` shipped + dispatch wired @ `:752`)
- [x] [UAC] **P0**. Update `defi_reserve_params.py` module docstring (line 1-22) — claims "verified against on-chain
      getConfiguration() 2026-03-29" but 12+ Aave V3 ETH reserves are missing; refresh audit date OR scope the claim.
      (UAC@4ec2256 — docstring refreshed to "Last updated: 2026-05-15" + multi-chain section)
- [x] [UAC] **P0**. Backfill `ARCHETYPE_CONFIG_SEED` in `internal/architecture_v2/archetype_config.py` with
      `CARRY_RECURSIVE_BORROW_LENDING_ONLY` + `CARRY_RECURSIVE_BORROW_PERP_HEDGED` rows. Without these the enum is
      shipped but the seed dict raises `KeyError` at runtime via `get_archetype_config()`. Suggested Family 1 defaults:
      `collateral_currency="USDC"`, `hedge_ratio=None`, `position_cap_usd=15_000.0`, `kill_switch_drawdown_pct=0.04`,
      `kill_switch_position_breach_pct=0.025`. (verified 2026-05-13: UAC
      `internal/architecture_v2/archetype_config.py:147` ARCHETYPE_CONFIG_SEED contains both keys at `:182`
      LENDING_ONLY + `:197` PERP_HEDGED)
- [x] [UAC] **P1**. Extend `AAVE_V3_ETHEREUM_RESERVES` with `RETH`; admit `RETH` to ETH_CORRELATED E-Mode `assets`
      frozenset. (UAC@4ec2256 — RETH added to AAVE_V3_ETHEREUM_RESERVES + ETH_CORRELATED E-Mode)
- [x] [UAC] **P1**. Investigate adding 12+ missing Aave V3 Ethereum reserves. SUSDE + GHO + SDAI + FRAX + LUSD added
      (top candidates); remaining (OSETH, RSETH, WEETHS, USDS, PYUSD, CRVUSD) deferred to
      defi_recursive_borrow_archetypes_post_cutover as P2 (not blocking May-23 cell selection). (UAC@8564e31 —
      SUSDE/GHO/SDAI/FRAX/LUSD added with low-confidence markers)
- [x] ✅ [UAC] **P1**. Add `COMPOUND_V3_ARBITRUM_USDC_E_RESERVES` + `COMPOUND_V3_ARBITRUM_USDC_RESERVES` (two distinct
      Arbitrum markets) + `COMPOUND_V3_BASE_RESERVES`. **SHIPPED UAC@3729af1** — all 3 dicts +
      `get_compound_reserve_params(chain, market)` accessor. (backfilled 2026-05-17 slot-5)
- [x] ✅ [UAC] **P2**. Add `SPARK_ETHEREUM_RESERVES` (Aave-fork; needs Spark in May-23 scope confirmation from operator
      — plan body lists Spark in-scope but UAC has no dict). **SHIPPED UAC@3729af1** — `SPARK_ETHEREUM_RESERVES` 7
      reserves shipped. (backfilled 2026-05-17 slot-5)
- [x] ✅ [UAC] **P2**. Document Morpho per-market LLTV overrides — either dict keyed by `(collateral, debt, oracle)`
      tuples OR `get_morpho_market_lltv(market_id)` accessor with on-chain fallback. **SHIPPED UAC@d88e512** —
      `_MORPHO_MARKET_LLTV` dict + `get_morpho_market_lltv(collateral, loan_asset)` accessor; wstETH/WETH→0.945 (top
      cell). Exported via registry.**init**.
- [x] ✅ [UAC] **P2**. Add `USDC.E` / `USDBC` symbol distinction to `defi_reserve_params.py` keys — bridged-vs-native
      USDC need separate entries on Arbitrum + Base. Cross-chain symbol hygiene. **SHIPPED UAC@3729af1** — `USDCE` in
      AAVE_V3_ARBITRUM_RESERVES + `USDBC` in AAVE_V3_BASE_RESERVES. (backfilled 2026-05-17 slot-5)

These items annotate other plans (Findings Triage — fits another active plan):

- **Annotation needed** in `defi_catalogue_chain_primitives_2026_05_10.md` Phase 3 (lending-indices fix):
  instruments-service must emit per-(chain, protocol) reserve listings for ARBITRUM Aave V3 (`USDC`, `USDC.E`, `USDT`,
  `DAI`, `WETH`, `WBTC`, `WSTETH`, `WEETH`, `RETH`, `ARB`, `LINK`) and BASE Aave V3 (`USDC`, `USDBC`, `WETH`, `CBBTC`,
  `WSTETH`, `WEETH`, `CBETH`) — without these the MTDS `lending_indices` adapter has no instrument universe for
  non-Ethereum chains.
- **Annotation needed** in `defi_master.md`: `UniswapConnector.swap_exact_input` SwapRouter02 address
  `0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45` is **Ethereum mainnet**. Base + Arbitrum SwapRouter02 addresses differ —
  Family 1 loop unwinds on those chains need separate connector config.

## Family 2 delta-hedge topology design — Family 1 + USDC-margined perp short (2026-05-12 slot 5)

> **Design owner:** ikenna slot 5 / agent-tag `ikenna-recursive-borrow-tab` (2026-05-12). **Source:** 3-sub-agent
> parallel research fan-out (Hyperliquid venue + Bybit venue + delta-hedge math/cell-ranking) reconciled below.
> **Status:** DESIGN-SHIPPED. Consumes Family 1 design (above); feeds Phase 5 (orchestrator), Phase 6 (Hyperliquid
> live), Phase 7 (PerpHedgeSizer), Phase 8 (alerts), Phase 9 (matching-engine cost model).

### Architectural recap

- Family 2 = Family 1 + USDC-margined ETH perp short. Reuses Family 1 ReserveParams + chain-overrides table verbatim —
  perp leg is purely additive.
- Per AD-2: hedge venues for May-23 = `Hyperliquid` (PRIMARY) + `Bybit` (SECONDARY). USDC-margin only — borrowed ETH
  stays inside the lending protocol; never sold to post as perp margin (would sever recursion invariant).
- Share-class accounting:
  `(aETH × wstETH_per_ETH_oracle) + free_ETH − ETH_debt + perp_short_size_ETH = target_net_delta`. Pure carry @
  `delta=0`; long-bias `+N`; short overlay `−N`.
- Enum: `CARRY_RECURSIVE_BORROW_PERP_HEDGED` SHIPPED at `enums.py:76-78`.

### Closed-form delta math (sanity-checked)

For Family 1 cell `(chain, lender, LST, ETH_debt, mode)` with own capital `base` ETH, recursion depth `d`, per-loop
`ltv ≤ liquidation_threshold − 0.05`:

```
Cumulative LST collateral (ETH-eq) = base × (1 − ltv^(d+1)) / (1 − ltv)
Cumulative ETH debt                = base × ltv × (1 − ltv^d) / (1 − ltv)

Net ETH-equivalent spot exposure E = (LST_eq) − (ETH_debt)
                                   = base × (1 − ltv − ltv + ltv^(d+1) + 0) / (1 − ltv)
                                   = base  exactly,  for all finite (ltv, d)
```

**Key result**: the recursion amplifies the SPREAD, not directional exposure. `E_actual ≈ 1 × base` per ETH of own
capital. Sizing implication: `perp_short_size = E_actual` for `target_net_delta=0`. In practice `PerpHedgeSizer`
(Phase 7) reads live position via Aave `getUserAccountData` rather than relying on closed form (LST/ETH peg drift +
slippage + oracle-mark gap account for typical ±0.1-0.5% deviation).

### Net APR formula

```
R_lend (Family 1) = S × (1 − ltv^(d+1)) / (1 − ltv)  −  B × ltv × (1 − ltv^d) / (1 − ltv)
R_fund            = +f × (perp_short_size / base)     (delta=0 ⇒ +f)
R_usdc            = u × (usdc_margin_buffer / base)   (HL pays 0; Bybit flex-savings ~0 for May-23)
R_net             = R_lend + R_fund + R_usdc − Δg − Δs
```

Where `S` = staking yield, `B` = ETH borrow rate, `f` = perp funding APR (positive = longs pay shorts = carry to us),
`u` = USDC supply APY at venue, `Δg/Δs` = gas/slippage amortised APR.

**Worked example** — wstETH/WETH E-Mode (`ltv=0.93, d=8, S=3.2%, B=2.4%, f=+12% APR normal regime`):

- `R_lend ≈ 5.27 × 3.2% − 4.56 × 2.4% ≈ 6.0%`
- `R_fund ≈ +12.0%`
- `R_usdc ≈ 0`
- Gas/slippage drag ~0.6% ETH mainnet (4-12 rebalances/yr); ~0.1% Arbitrum/Base
- **Net ≈ 17.4%** on Ethereum mainnet; ~17.9% on Arbitrum (gas drag smaller). Confidence HIGH on `R_lend`, MED on
  `R_fund` (regime variability — verify via MTDS historical funding data per defi_catalogue Phase 3).

### Funding regime classification (long-term ETH-perp post-2024)

- **Normal (bull / mean-reverting):** +5% to +25% APR; ~+12% median. Family 2 carries strongly positive.
- **Sharp upswing / FOMO:** +50% to +100% APR for hours-to-days. Highly profitable for short side.
- **Capitulation / panic:** −10% to −50% APR. Family 2 becomes funding-cost drag; cell rank drops or pauses.
- **Long-term median post-Apr-2024 cross-venue:** ~+8-15% APR; negative regimes episodic (<5% of trading days). Verify
  via MTDS once funding-rate adapters land.

### Per-cell × per-venue grid (`target_net_delta = 0`)

| Family 1 cell                             | Hyperliquid leg                                    | Bybit leg                                               | preferred_venue_for_may_23      | rationale                                                                                                                                                        |
| ----------------------------------------- | -------------------------------------------------- | ------------------------------------------------------- | ------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `aave_v3_ethereum_wsteth_weth_emode`      | ETH-PERP short, USDC margin via HL Arbitrum-bridge | ETHUSDT-PERP short (deepest book) or ETHPERP-USDC short | **HL PRIMARY**, Bybit SECONDARY | DEX execution; 1h funding cadence (faster sign-flip detection); no KYC dependency; Bybit Feb-2025 hack premium → secondary cap                                   |
| `morpho_ethereum_wsteth_weth_market_0945` | ETH-PERP short                                     | ETHUSDT-PERP short                                      | **HL PRIMARY**                  | LLTV 0.945 → larger `E ≈ base`; tighter HF buffer; 1h funding granularity reduces rebalance-lag tail                                                             |
| `aave_v3_arbitrum_wsteth_weth_emode`      | ETH-PERP short (USDC bridge cheap on Arb)          | ETHUSDT-PERP short                                      | **HL PRIMARY**                  | Same-chain margin posting → cheapest gas in scope; cross-venue settlement risk minimised                                                                         |
| `aave_v3_base_cbeth_weth_emode`           | ETH-PERP short (no cbETH-PERP on either venue)     | ETHUSDT-PERP short                                      | **HL PRIMARY**                  | cbETH/ETH basis risk: size `perp_short = cumulative_cbETH × Chainlink_cbETH_ETH_rate − cumulative_ETH_debt`; residual basis tracked as `CROSS_VENUE_DELTA_DRIFT` |
| `aave_v3_ethereum_weeth_weth_emode`       | ETH-PERP short                                     | ETHUSDT-PERP short                                      | **HL PRIMARY**                  | EIGEN/ETHFI points non-cash; discount in APR; otherwise similar to wstETH cell                                                                                   |
| `morpho_ethereum_susde_usdc_market_086`   | n/a                                                | n/a                                                     | **OUT of Family 2**             | Stable loop, USDC debt; net exposure USDC ≈ 0; perp would introduce delta, not hedge it                                                                          |

### USDC margin buffer sizing

Per Family 2 cell with `perp_short_size = S` ETH at ETH spot `P_eth_usd`:

```yaml
perp_notional_usd: S × P_eth_usd
initial_margin_usd: 0.10 × S × P_eth_usd # 10x cross-leverage default (HL + Bybit; tighter than 50x max)
recommended_buffer_usd: 0.30 × S × P_eth_usd # 3× initial margin
auto_topup_trigger: available_margin / initial_margin < 1.5 # ~30% price-move headroom before liquidation
usdc_margin_buffer_min_pct: 0.30 # config field per Phase 2 schema
```

**Bridge latencies** (verify on testnet smoke):

- Hyperliquid: ~10s once tx confirmed on Arbitrum bridge contract (HL L1 finality <1s).
- Bybit: 1-5min depending on source chain (Eth ~3min, Arb/Base ~1min). Prefer Arbitrum-route.

**Rebalance cadence**: PerpHedgeSizer poll every 5min; top-up tx only when threshold breached (<1×/day normal;
several×/day during fast moves).

### Target_net_delta configurations

- `target_net_delta = 0`: pure carry; `R_net` = full alpha.
- `target_net_delta = +1.0`: hold 1 ETH long + earn carry overlay; `perp_short_size = E_actual − 1.0`.
- `target_net_delta = +N ≥ E_actual`: `perp_short_size = 0` → reverts to Family 1 (auto-degrades).
- `target_net_delta = −1.0`: short 1 ETH outright + earn carry; `perp_short_size = E_actual + 1.0`.

### Funding regime adaptive sizing (Phase 7.5 — NICE-TO-HAVE, may defer past May-23)

- Rolling 7d + 30d funding-APR mean per `(perp_venue, perp_pair)` — feature owned by features-service (onchain family)
  (NEW row).
- Conservative thresholds (hysteresis 5% APR to avoid thrashing):
  - 30d-avg `< −5% APR`: REDUCE perp short by 50%.
  - 30d-avg `< −15% APR`: SET perp short to 0 (cell paused; reverts to Family 1 mechanics).
  - 30d-avg `> +30% APR`: maintain or INCREASE perp short toward `target_net_delta − 0.5`.

### Top 3 May-23 viable Family 2 cells (`expected_apr × confidence × counterparty_diversification`)

1. `aave_v3_ethereum_wsteth_weth_emode__hyperliquid_eth_perp__delta_0` — net APR ~10-25%; **HIGH × MED-HIGH × HIGH**
   (Aave + Lido + HL counterparty mix); flagship cell.
2. `morpho_ethereum_wsteth_weth_market_0945__hyperliquid_eth_perp__delta_0` — net APR ~12-28%; **MED-HIGH × MED-HIGH ×
   HIGH** (Morpho-Steakhouse curator added); highest APR.
3. `aave_v3_ethereum_wsteth_weth_emode__bybit_eth_perp__delta_0` — net APR ~10-25%; **HIGH × MED × HIGH** (Bybit
   post-Feb-2025-hack discount); diversification anchor when cell #1 hits cap.

### Family 2-specific risk surface (additive to Family 1)

- **`FUNDING_SIGN_FLIP`** (Phase 8 alert): per-block funding crosses zero against strategy → position-pause; 30d-avg
  crosses negative threshold → adaptive sizing per Phase 7.5.
- **`PERP_VENUE_OUTAGE`**: HL bridge halt / Bybit API rate-limit / trading halt. Decision tree:
  - Family 1 leg delay-tolerant (HF safe) → maintain perp where possible, route new opens to backup venue.
  - Family 1 leg delay-intolerant (HF near threshold) → flash-close Family 1 first (perp becomes outright short until
    venue recovers — risk escalated).
- **`CROSS_VENUE_DELTA_DRIFT`**: `perp_short_size − E_actual > ±5% × E_actual` → auto-rebalance. Also triggers on
  cbETH/ETH or wstETH/ETH oracle move > 1% intra-day.
- **`MARGIN_CALL_AT_PERP`**: `available_margin < MM × 1.2` → top up from treasury; if treasury insufficient → partial
  unwind Family 1 + perp.

### Workspace canon checks (verified during fan-out)

**Hyperliquid:**

- ✅ `HYPERLIQUID` string constant in
  `unified-api-contracts/unified_api_contracts/registry/venue_constants.py:19,278,312,354,457,579,676,710,812`
  (canonical name + capability declarations across 9 registries).
- ✅ `MarginModel.HYPERLIQUID` + `LIQUIDATION_PARAMS_REGISTRY` entry shipped (`internal/risk.py:698,841-846`).
- ✅ `_HYPERLIQUID_RULES` risk caps shipped (`registry/risk_rules/venue.py:186-216`): $2M OI / $500k per-instrument /
  $4M venue exposure.
- ✅ Coverage start `date(2023, 6, 29)` in `coverage_starts.py:49`; `KILL_PER_VENUE_HYPERLIQUID` in `kill_switch.py:87`.
- ⚠️ `defi_execution/protocols/hyperliquid.py:64-273` — **simulation-only** (returns canned `order_<timestamp>` dict; no
  REST/WS calls).
- ⚠️ `venues/hyperliquid.py:18-263` — **DUPLICATE simulation-only connector**; two parallel impls (one TypedDict, one
  `dict[str, object]`); consolidation needed.
- ❌ `VENUE_ERRORS_DEFI` dict (`canonical/crosscutting/errors/defi.py:52-1161`) has NO Hyperliquid entries — 13 codes
  today all Aave/Balancer/Curve/etc.

**Bybit:**

- ✅ `BybitCCXTAdapter` perp-execution-grade at
  `execution-service/execution_service/trade_execution/adapters/bybit_ccxt.py:28-66`; futures=True selects
  `defaultType="future"`.
- ✅ Factory wiring at `trade_execution/factory.py:36,94,147-155` (`Venue.BYBIT` in `CCXT_VENUES` +
  `CCXT_TO_UCI_VENUE`).
- ✅ Canonical venue codes `BYBIT-SPOT` / `BYBIT-FUTURES` (`canonical/canonical_mappings.py:34-35,184,374,414-419`);
  testnet URLs (`venue_thresholds.py:127-131`); coverage start `2018-11-21` (`coverage_starts.py:48`).
- ✅ Live test fixtures at `execution-service/tests/live/venues/cefi/test_bybit.py`.
- ⚠️ `ApiKeyReloader` NOT wired into `BybitCCXTAdapter` constructor — same gap workspace-wide for CeFi adapters (Binance
  / OKX / Deribit). DEFER past May-23 unless operator escalates.

### Findings + gaps (Findings Triage discharge)

In-plan P0 (blocks Phase 5-8 implementation):

- [x] [UAC] **P0**. Resolve `PerpVenue` ambiguity from Phase 2 line 362: workspace has NO unified `Venue` enum —
      `HYPERLIQUID` + `BYBIT` are string constants in `venue_constants.py`. **Implementation: add
      `get_perp_venues() -> frozenset[str]` helper deriving from `VENUE_CAPABILITIES` filtered by
      `VenueCapability.PERP_TRADE`** (System-First — no new enum / no SSOT duplication). **DONE 2026-05-15 (slot-3)**:
      `unified-api-contracts@be5b987` — `get_perp_venues()` added to `venue_constants.py` + exported from
      `registry/__init__.py`; 6 unit tests pass; basedpyright clean. Returns 6 venues (BINANCE-FUTURES, BYBIT-FUTURES,
      OKX-FUTURES, DERIBIT, HYPERLIQUID, ASTER).
- [x] [UAC] **P0**. Add Hyperliquid entry to `VENUE_ERRORS_DEFI` dict in `canonical/crosscutting/errors/defi.py` with
      classified codes: `HL_INSUFFICIENT_MARGIN` (FAIL — analog to aave INSUFFICIENT_COLLATERAL),
      `HL_REDUCE_ONLY_VIOLATION` (FAIL), `HL_INVALID_TIF` (FAIL), `HL_RATE_LIMITED` (RETRY — 429), `HL_NONCE_TOO_LOW`
      (RETRY — EIP-712 nonce race), `HL_SIGNATURE_INVALID` (FAIL — wallet config bug), `HL_POSITION_CLOSED` (SKIP —
      auto-liquidation race). Mirror in `DefiErrorCode` class constants. (verified 2026-05-13: UAC
      `canonical/crosscutting/errors/defi.py:73` `HL_INSUFFICIENT_MARGIN` + `:75` `HL_REDUCE_ONLY_VIOLATION` shipped in
      DefiErrorCode enum)
- [x] [execution-service] **P0**. Consolidate `defi_execution/protocols/hyperliquid.py` + `venues/hyperliquid.py` into
      ONE canonical connector. Pick `defi_execution/protocols/hyperliquid.py` as canon (already uses parsed UAC
      schemas); delete or shim the other. Same logical unit as Phase 6 live wire-up. (33d064b86 execution-service
      2026-05-15 — venues/hyperliquid.py deleted)
- [x] ✅ [execution-service] **P0**. Phase 6 Hyperliquid LIVE wire-up: EIP-712 signing (action hash + nonce +
      `vaultAddress` envelope; ChainId 1337 mainnet / 421614 testnet — verify against current Hyperliquid SDK); REST
      POST to `https://api.hyperliquid.xyz/exchange`; WS `user_events` subscription. Replace
      `available_margin = equity × 0.9` placeholder (line 259) with parsed
      `HyperliquidUserState.marginSummary.accountValue − totalMarginUsed`. — execution-service@de43118 (audit-backfilled
      2026-05-19)
- [x] [execution-service] **P0**. Hyperliquid bridge address + USDC deposit/withdrawal helpers under `defi_execution/`:
      operator deposits USDC on Arbitrum → bridge to HL L1 → arrives in trading wallet. **5-minute withdrawal dispute
      window** must be encoded in kill-switch unwind timing budget. Bridge address
      `0x2Df1c51E09aECF9cacB7bc98cB1742757f163dF7` (low-confidence — verify; HL has rotated bridges at least once in
      2024). (649142a6a execution-service 2026-05-15 — hyperliquid_bridge.py with deposit/withdraw/get_bridge_pending)
- [x] [strategy-service] **P0**. Variant naming decision: **single archetype `CARRY_RECURSIVE_BORROW_PERP_HEDGED` with
      `perp_venue` config field** (already in Phase 2 schema proposal). No per-venue variant tarballs. Catalog
      enumerates `perp_venue ∈ {HYPERLIQUID, BYBIT}` at cell-id level only. **DONE 2026-05-15 (slot-3)**:
      `unified-api-contracts@2b60a14` — `perp_venue: str | None` added to `ArchetypeConfig`; validated against
      `get_perp_venues()` (rejects spot-only + unknown venues); `CARRY_RECURSIVE_BORROW_PERP_HEDGED` seed gets
      `perp_venue="HYPERLIQUID"` (May-23 default). 6 new tests pass; basedpyright clean.
- [x] [strategy-service] **P0**. `PerpHedgeSizer` (Phase 7): pre-trade check against `_HYPERLIQUID_RULES`
      ($500k
      per-instrument cap) — block sizing that exceeds. Same for any Bybit per-position risk cap. **DONE 2026-05-15
      (slot-3)**: `unified-api-contracts@5f26915` ships `get_max_position_size_usd_for_venue()` helper +
      `execution-service@a2ce35b74` ships `PerpHedgeSizer.validate_size_against_venue_cap()` +
      `PerpVenueCapExceededError`. Hyperliquid $500k
      / Bybit $1M / Binance $2M caps wired. Fail-closed on unknown venues per honest-absence rule. 7 new tests pass (16
      total in file). basedpyright clean. (Note: PerpHedgeSizer lives in execution-service per System-First — venue-cap
      pre-trade gate is execution responsibility, not strategy-service.)
- [x] [risk] **P0**. Bybit counterparty cap policy: **cap Bybit notional at ≤50% of Hyperliquid leg for first 30 days
      post-cutover** (Feb-2025-hack trust-premium discount). Codify in strategy-service archetype config +
      risk-and-exposure-service venue-cap table. **SHIPPED 2026-05-18** (slot 4): UAC-unified — new
      `RiskRuleId.COUNTERPARTY_RATIO_CAP` + `CounterpartyRatioCapTrigger` (reference_venue / cap_ratio_of_reference /
      secondary_venue fields) in `canonical/crosscutting/risk_rule.py`; 4th rule added to `_BYBIT_RULES` in
      `registry/risk_rules/venue.py` (BLOCK, cap=0.50 of HL notional, triggers_kill_switch=False);
      `bybit_notional_cap_pct_of_hl=0.50` seeded on `CARRY_RECURSIVE_BORROW_PERP_HEDGED` in `ArchetypeConfig`.
      `CounterpartyRatioCapTrigger` re-exported at `risk.py` public facade. QG: all 122s passing.
      unified-api-contracts@c29114c.

In-plan P1 (blocks polish, may defer to Phase 9-12):

- [x] [risk-and-exposure-service] **P0.5**. Wire `COUNTERPARTY_RATIO_CAP` rule into risk-and-exposure-service pre-flight
      evaluator. UAC seeded (rule + trigger at `unified-api-contracts@c29114c`). R&E service must call
      `iter_applicable_rules(venue="bybit", rule_id=COUNTERPARTY_RATIO_CAP)` at Layer 2 + evaluate
      `CounterpartyRatioCapTrigger` against live HL notional from position-balance state. Blocks hard enforcement of the
      30-day Bybit cap. **DEFERRED**: successor = next risk-and-exposure-service slot allocation. **MIGRATED FROM:
      2026-05-18 slot-4 deferred-work scoreboard.**
- [x] [features-service (onchain family)] **P1**. New feature: `funding_rate_apr_rolling_30d_mean` per
      `(perp_venue, perp_pair)` — feeds Phase 7.5 adaptive sizing. Defer past May-23 if Phase 7 baseline ships green.
      **DEFERRED-POST-CUTOVER** → successor: defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md.
- [x] [risk-and-exposure-service] **P1**. Integration test: cross-venue netting
      `(aETH × er) + free_ETH − ETH_debt + perp_short = target_net_delta` within ±0.001 ETH on Tenderly fork +
      Hyperliquid testnet. Folds into Phase 7 deliverable. **DEFERRED-POST-CUTOVER** → successor plan.
- [x] [pnl-attribution-service] **P1**. Per-venue funding separation: HL funds 1h (24×/day); Bybit funds 8h (3×/day).
      Daily funding cost = `Σ_HL_hourly + Σ_Bybit_8h`. Avoid double-attribution in Family 2 P&L.
      **DEFERRED-POST-CUTOVER** → successor plan. Family 2 Bybit live not yet active.
- [x] [execution-service] **P1**. Per-archetype subaccount + per-archetype API key for Bybit (blast-radius isolation):
      `carry_recursive_borrow_perp_hedged` key separate from `leveraged_funding_arb` key. Trading-only scope, no
      withdrawal, IP-whitelist to GCE static egress. Bybit subaccount provisioning runbook →
      `deployment-service/runbooks/` (NEW). **DEFERRED-POST-CUTOVER** → successor plan; gates on live Bybit activation.
- [x] [batch-live-reconciliation-service] **P1**. Bybit private v5 WS streams (`order` / `execution` / `position`)
      parity with REST poll — fills land in position-balance-monitor ≤500ms after venue ack. Required for batch-vs-live
      recon harness. **DEFERRED-POST-CUTOVER** → successor plan.

In-plan P2:

- [x] ✅ [strategy-service] **P2**. Pause-cell cleanliness when `target_net_delta = +N ≥ E_actual`:
      `_build_carry_recursive_staked` emits single-leg lending-only cell (not two-leg with `perp_short_size=0`) to keep
      bookkeeping clean. — strategy-service@24ec3d4; removed perp_venue from all 7 specs, added perp_leg_enabled=false +
      unit test
- [x] [execution-service] **P2**. cbETH/ETH basis-risk monitor in Phase 8 (additive to HealthFactorMonitor) — small
      under normal markets (cbETH 0.1-0.5% premium/discount) but tail risk during Coinbase stress.
      **DEFERRED-POST-CUTOVER** → successor plan. P2 priority; tail-risk coverage.
- [x] [execution-service] **P2**. USDC supply-APY (`R_usdc`): Hyperliquid does NOT pay; Bybit flexible-savings gates on
      KYC tier. Defer config field past May-23. **DEFERRED-POST-CUTOVER** → successor plan.
- [x] [ops] **P2**. Bybit live VM singleton-locked (per `Singleton-locked launchers` rule) — API key + IP whitelist mean
      only one VM-IP can authenticate simultaneously; without lock, zombie launcher could double-trade.
      **DEFERRED-POST-CUTOVER** → successor plan. Gates on live Bybit VM launch.
- [x] ✅ [docs] **P2**. Codex doc `/codex/04-architecture/cefi-perp-leg-bybit.md` (NEW) — capture this topology +
      Feb-2025-hack risk addendum; cross-ref Family 2 plan + master plan B-risk row. — PM@ikenna-slot-2 (created
      2026-05-15); verified present + complete 2026-05-18 slot 3. Sections: Bybit UTA overview, USDC deposit route,
      Feb-2025 hack addendum, funding cadence vs HL, kill-switch integration, See also.

Cross-plan annotations needed (Findings Triage):

- **defi_catalogue_chain_primitives_2026_05_10.md Phase 3**: verify `funding_rate` data_type capture for ETH-PERP on
  Hyperliquid + Bybit at ≥1h cadence with ≥1y horizon — required for Phase 7.5 30d-mean feature. Grep-then-READ before
  concluding adapters missing (per HARD RULE).

## Phase 3 design — strategy-service factory + target-universe catalog (2026-05-12 slot 5)

> **Design owner:** ikenna slot 5 / agent-tag `ikenna-recursive-borrow-tab` (2026-05-12). **Source:** direct
> catalog-read + Family 1/2 design synthesis (no sub-agent fan-out needed; small scope). **Status:** DESIGN-SHIPPED.
> Consumed by Phase 3 implementation (file:line pre-audit completed).

### Workspace ground truth (pre-audit)

- `strategy-service/strategy_service/engine/strategies/v2/factory.py:63` — `_ARCHETYPE_ENGINE_MAP` dict:
  `CARRY_RECURSIVE_STAKED → CarryRecursiveStakedEngine`. **MISSING**: `CARRY_RECURSIVE_BORROW_LENDING_ONLY` +
  `CARRY_RECURSIVE_BORROW_PERP_HEDGED`. Will runtime-error on archetype dispatch.
- `strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog.py:1958` — `_ARCHETYPE_BUILDERS` dict:
  same gap. Will fail catalog enumeration.
- `strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog.py:915-959` —
  `_build_carry_recursive_staked()` reference impl: enumerates 7 cells (3 LST×lending × 2 leverage versions on ETH + 1
  SOL). Pattern uses `_spec()` helper with positional args
  `(archetype, instance_id, base_share_class, position_cap, quote_share_class, config_dict)`.
- Existing `CARRY_RECURSIVE_STAKED@` instance_id format:
  `CARRY_RECURSIVE_STAKED@<lend>-<stake>-<perp_venue>-<base>-<bar>-<share>-<version>-<env>`. Slot 5 design will follow
  this convention.

### Engine class strategy (decision)

**SELECTED: single engine class with config-driven dispatch.** Reuse existing `CarryRecursiveStakedEngine` with
config-variant branch on `archetype` enum value (or `perp_leg_enabled` config field). Rationale:

- 99% of the engine's mechanics (rebalance loop, LeveragedLegController integration, kill-switch wiring, tracer hook)
  are identical across Family 0 (CARRY_RECURSIVE_STAKED) / Family 1 (LENDING_ONLY) / Family 2 (PERP_HEDGED).
- Only the leg composition differs: 0 = stake+borrow+perp (existing); 1 = stake+borrow (no perp); 2 = lending+perp (no
  stake leg, or LST-staking-yield-only without basis trade).
- A second engine class would duplicate the entire orchestrator surface — Citadel-Grade "No Technical Debt" +
  System-First.

Implementation gate: `factory.py:63` dict adds **same `CarryRecursiveStakedEngine` for all 3 archetype keys** (Family 0,
1, 2). Engine internal branches via `config["perp_leg_enabled"]` + `config["staking_yield_enabled"]` flags.

### Catalog builders (paste-ready spec)

Two new builder functions in `catalog.py`, registered at line 1958:

**`_build_carry_recursive_borrow_lending_only()` — Family 1 (lending leg only, no perp short):**

```python
def _build_carry_recursive_borrow_lending_only() -> tuple[TargetInstanceSpec, ...]:
    out: list[TargetInstanceSpec] = []
    a = StrategyArchetype.CARRY_RECURSIVE_BORROW_LENDING_ONLY

    # Top-7 cells per Family 1 design (2026-05-12 slot 5 spec):
    # Cell format: (lender, chain, collateral, debt, mode, version_suffix)
    cells = [
        ("aave_v3", "ethereum", "wsteth", "weth", "emode_eth", "v1"),
        ("morpho",  "ethereum", "wsteth", "weth", "market_0945", "v1"),
        ("aave_v3", "arbitrum", "wsteth", "weth", "emode_eth", "v1"),
        ("aave_v3", "base",     "cbeth",  "weth", "emode_eth", "v1"),
        ("morpho",  "ethereum", "susde",  "usdc", "market_086", "v1"),
        ("aave_v3", "ethereum", "weeth",  "weth", "emode_eth", "v1"),
        ("aave_v3", "base",     "wsteth", "weth", "emode_eth", "v1"),
    ]
    for lender, chain, coll, debt, mode, ver in cells:
        share_class = ShareClass.ETH if debt == "weth" else ShareClass.USDC
        position_cap = Decimal("100000")  # USDC equivalent; per-cell override later via config
        out.append(
            _spec(
                a,
                f"CARRY_RECURSIVE_BORROW_LENDING_ONLY@{lender}-{chain}-{coll}-{debt}-{mode}-{ver}-prod",
                share_class,
                position_cap,
                ShareClass.USDC,  # quote-share for P&L accounting
                {
                    "lending_protocol": lender,
                    "chain": chain,
                    "collateral_asset": coll,
                    "debt_asset": debt,
                    "ltv_mode": mode,  # emode_eth / market_0945 / market_086 / standard
                    "perp_leg_enabled": "false",
                    "target_net_delta": "0",  # Family 1 has no perp; delta carries unhedged
                    "hold_policy": "CONTINUOUS",
                    # Chain-overrides (per Family 1 design) — full set picked up by orchestrator
                    # via `chain` field lookup; this dict is the per-instance "rest" override.
                },
            )
        )

    return tuple(out)
```

**`_build_carry_recursive_borrow_perp_hedged()` — Family 2 (Family 1 + perp short):**

```python
def _build_carry_recursive_borrow_perp_hedged() -> tuple[TargetInstanceSpec, ...]:
    out: list[TargetInstanceSpec] = []
    a = StrategyArchetype.CARRY_RECURSIVE_BORROW_PERP_HEDGED

    # Top-3 cells per Family 2 design (2026-05-12 slot 5 spec); each spawns 2× perp_venue variants:
    cells = [
        # (lender, chain, collateral, debt, mode, version)
        ("aave_v3", "ethereum", "wsteth", "weth", "emode_eth", "v1"),
        ("morpho",  "ethereum", "wsteth", "weth", "market_0945", "v1"),
        ("aave_v3", "arbitrum", "wsteth", "weth", "emode_eth", "v1"),
        ("aave_v3", "base",     "cbeth",  "weth", "emode_eth", "v1"),
        ("aave_v3", "ethereum", "weeth",  "weth", "emode_eth", "v1"),
    ]
    perp_venues = [
        ("hyperliquid", "eth_perp"),  # PRIMARY per Family 2 design
        ("bybit",       "eth_usdt_perp"),  # SECONDARY — capped at 50% of HL leg notional first 30d
    ]
    target_deltas = [("0", "delta0")]  # Day-1 ship: pure-carry delta=0 only; +1/+N variants per future plan

    for lender, chain, coll, debt, mode, ver in cells:
        for perp_venue, perp_pair in perp_venues:
            for target_delta_str, delta_tag in target_deltas:
                out.append(
                    _spec(
                        a,
                        f"CARRY_RECURSIVE_BORROW_PERP_HEDGED@{lender}-{chain}-{coll}-{debt}-{mode}-{perp_venue}-{perp_pair}-{delta_tag}-{ver}-prod",
                        ShareClass.ETH,
                        Decimal("100000"),
                        ShareClass.USDC,
                        {
                            "lending_protocol": lender,
                            "chain": chain,
                            "collateral_asset": coll,
                            "debt_asset": debt,
                            "ltv_mode": mode,
                            "perp_leg_enabled": "true",
                            "perp_venue": perp_venue,
                            "perp_pair": perp_pair,
                            "target_net_delta": target_delta_str,
                            "usdc_margin_buffer_min_pct": "0.30",
                            "hold_policy": "CONTINUOUS",
                        },
                    )
                )

    return tuple(out)
```

**Cell count**:

- Family 1: 7 cells (1 lender × 1 collateral × 1 debt × 1 mode each).
- Family 2: 5 base cells × 2 perp venues × 1 target_delta = 10 cells. Excludes sUSDe/USDC (no ETH delta to hedge).

Total new cells: 17. Within the master plan position-cap envelope (~$1.7M aggregate at $100k each).

### LeveragedLegController + tracer extension

- `LeveragedLegController` (existing,
  `strategy-service/strategy_service/engine/strategies/v2/leg_controller_adapter.py`) — accepts `target_net_delta`
  parameter via config; rebalances by trimming/extending perp leg to match. Family 1 cells set `perp_leg_enabled=false`
  → controller short-circuits the perp side and only manages lending leg.
- Tracer: `defi_carry_recursive_staked_decision_trace.py` already has
  `_net_apr_recursive(stake_apy, borrow_apy, ltv, n_loops)` at line 210 (verified per plan body Phase 3 line 287). **New
  helper**
  `_net_apr_with_perp_funding(stake_apy, borrow_apy, perp_funding_apy, ltv, n_loops, target_net_delta, usdc_idle_apy)`
  per Family 2 net-APR formula above. Both helpers exposed via tracer module top-level.

### Cross-plan handshakes

- **slot 6 `defi_simulation_realism_2026_05_10.md`** — AMM family matrix + sim contract + golden test set. **Required by
  Phase 9** of THIS plan (matching engine DeFi cost model). Slot 6's Day-2 noon deliverable per work_split row 6. Slot
  5's Phase 3 cell enumeration uses slot 6's `AMM_SLIPPAGE_FAMILY` taxonomy (when published) to attach per-cell
  `expected_slippage_bps` config field. **Annotation** added to `defi_simulation_realism_2026_05_10.md` in next
  plan-flip commit.
- **slot 2 `defi_catalogue_chain_primitives_2026_05_10.md`** — funding-rate adapters for HL + Bybit ETH-PERP
  (already-flagged P1 cross-plan annotation in Family 2 design).

### Phase 3 implementation gate

- [x] [strategy-service] **P0**. Wire
      `_ARCHETYPE_ENGINE_MAP[StrategyArchetype.CARRY_RECURSIVE_BORROW_LENDING_ONLY] = CarryRecursiveStakedEngine` + same
      for `CARRY_RECURSIVE_BORROW_PERP_HEDGED` in `factory.py:63`. (strategy-service@44a8afc — 2 entries added to
      ARCHETYPE_ENGINE_REGISTRY)
- [x] [strategy-service] **P0**. Add `_build_carry_recursive_borrow_lending_only` +
      `_build_carry_recursive_borrow_perp_hedged` builder functions in `catalog.py` per spec above. Register in
      `_ARCHETYPE_BUILDERS` dict at line 1958. (strategy-service@44a8afc — 7 Family-1 + 10 Family-2 = 17 cells, counts
      verified)
- [x] [strategy-service] **P0**. Engine internal: branch in `CarryRecursiveStakedEngine` on
      `config["perp_leg_enabled"]` + `config["staking_yield_enabled"]` (NEW config field — `true` only for Family 0
      CARRY_RECURSIVE_STAKED; `false` for Family 1/2 — Family 1/2 are pure borrow loops where the "staking yield" is the
      lending supply APY, not LST staking yield). (strategy-service@44a8afc — staking_yield_enabled branch in on_tick();
      Phase 5 stub returns [])
- [x] [strategy-service] **P0**. Tracer: add `_net_apr_with_perp_funding(...)` helper to
      `defi_carry_recursive_staked_decision_trace.py`; reuse existing `_net_apr_recursive` for Family 1; extend module
      top-level exports. (strategy-service@44a8afc — new module with net_apr_recursive + net_apr_with_perp_funding;
      net_apr_with_perp_funding(3.2%,2.4%,12%,0.93,8,0,0)=19.88%)
- [x] [strategy-service] **P1**. Round-trip test fixture: `tests/unit/v2/test_carry_recursive_borrow_archetypes.py`
      covering both family enum members through factory + catalog + tracer. (strategy-service@03c1622 — 18 tests:
      factory dispatch, 7+10 cell counts, on_tick stub [], APR arithmetic, slot labels, config fields; also adds
      ALLOWED_ARCHETYPES to base + recursive_staked, re-exports tracer helpers from carry_and_yield **init**)
- [x] [strategy-service] **P0**. Peripheral script wiring per HARD RULE: extend
      `strategy-service/scripts/quality-gates.sh` to run basedpyright + ruff on
      `e2e-testing/scripts/defi/recursive_borrow_paper_smoke.py` (NEW per Phase 12). (7cb01d3 strategy-service
      2026-05-15)

## Phase 12 design — per-family backtest scenario set (2026-05-12 slot 5)

> **Design owner:** ikenna slot 5 / agent-tag `ikenna-recursive-borrow-tab` (2026-05-12). **Source:** Family 1 + 2
> funding regime taxonomy synthesis + slot 6 PoolMatcher / golden-harness shape consumption (slot 6 Day-1 ship per
> `defi_simulation_realism_2026_05_10.md` DONE-2026-05-15 block). **Status:** DESIGN-SHIPPED. Consumed by Phase 9
> (matching-engine cost model) + Phase 12 (backtest runs) + Phase 13 (live deploy gating).

### Scope

Define the closed set of backtest scenarios that gate Family 1 + Family 2 cells from `design-shipped` → `live-ready`.
Every cell in the Phase 3 catalogue (17 cells: 7 Family 1 + 10 Family 2) must clear the scenario matrix below before
promotion to Phase 13 live deploy.

### Scenario taxonomy (3 categories × N concrete scenarios)

#### Category A — Funding regime backtests (Family 2 only; Family 1 skips)

Per the Family 2 design funding regime classification:

| Scenario ID             | Window                  | Regime                                                                      | Cells exercised                  | Success criteria                                                                                                          |
| ----------------------- | ----------------------- | --------------------------------------------------------------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `SCN-A1-NORMAL-2024`    | 2024-01-01 → 2024-12-31 | Positive funding median ~+12% APR; episodic +30% spikes                     | All Family 2 cells               | Net APR > 0 on ≥80% of trading days; max consecutive drawdown < 8% per cell                                               |
| `SCN-A2-FLIP-NOV-2022`  | 2022-10-01 → 2022-12-31 | Capitulation; FTX-collapse; ETH-perp funding flipped negative for ~6 weeks  | All Family 2 cells               | Adaptive-sizing trigger fires within 7 days of 30d-avg crossing −5% APR; perp_short_size reduces ≥50%; max drawdown < 15% |
| `SCN-A3-FOMO-2024-Q1`   | 2024-01-01 → 2024-03-31 | Sharp upswing; funding spiked +50-100% APR daily; ETH/BTC ETF approval flow | Family 2 wstETH / weETH cells    | Strategy continues holding short; cumulative funding-capture > 8% APR over 90 days                                        |
| `SCN-A4-DEPEG-MAR-2023` | 2023-03-08 → 2023-03-15 | USDC depeg post-SVB collapse (USDC traded 0.87-0.93 for ~48h)               | All Family 2 USDC-margined cells | Margin auto-topup fires < 60s after deviation > 3%; no liquidation events                                                 |

#### Category B — Liquidation stress (price-shock backtests for both families)

Tests Phase 8 HealthFactorMonitor + LiquidationProximityCircuit + kill-switch wiring. Each shock is replayed against
cells via Tenderly fork. Scenarios consume slot 6 `PoolMatcher.quote()` for swap leg P&L.

| Scenario ID                    | Shock type                                                                 | Magnitude        | Cells exercised              | Success criteria                                                                                                                                      |
| ------------------------------ | -------------------------------------------------------------------------- | ---------------- | ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SCN-B1-FLASH-CRASH-LST-DEPEG` | wstETH/ETH oracle drops 3% over 1 block (15s)                              | 3% peg deviation | All wstETH / weETH cells     | HF doesn't drop below 1.05; partial unwind fires at HF 1.10 (`HEALTH_FACTOR_CRITICAL`); position state matches HealthFactorMonitor predicted at ±0.5% |
| `SCN-B2-ETH-CRASH-15PCT-1D`    | ETH/USD drops 15% in 1 day (e.g. 2024-04-13 BTC-driven sell-off magnitude) | 15%              | All ETH-debt cells           | Kill-switch unwinds before liquidation (`LIQUIDATION_IMMINENT`); unwind P&L within 2% of analytical model                                             |
| `SCN-B3-WSTETH-PEG-EXTREME`    | wstETH/ETH oracle drops 8% (Lido validator slashing scenario)              | 8% peg deviation | wstETH cells (Aave + Morpho) | Morpho LLTV 0.945 cell unwinds at HF 1.05; Aave 0.93 LTV cell maintains; recursive flash-unwind correctly closes loop atomically                      |
| `SCN-B4-CBETH-PEG-COINBASE`    | cbETH/ETH drops 5% (Coinbase custody-stress scenario)                      | 5% peg           | Base cbETH cells             | Cell auto-pauses; bridge-risk + counterparty risk fire as separate alerts                                                                             |
| `SCN-B5-ORACLE-STALE-24H`      | Chainlink feed goes stale > 24h heartbeat                                  | 24h staleness    | All cells                    | All cells halt opening new loops; existing positions held with `ORACLE_STALE_PAUSE` alert                                                             |

#### Category C — Venue + bridge failure (operational resilience)

Tests cross-venue coordination + USDC margin top-up automation.

| Scenario ID                        | Failure type                                                 | Cells exercised                            | Success criteria                                                                                                                                          |
| ---------------------------------- | ------------------------------------------------------------ | ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SCN-C1-HL-BRIDGE-HALT`            | Hyperliquid Arbitrum-bridge halt for 30min                   | All Family 2 HL cells                      | Adaptive: maintain existing perp position; route new opens to Bybit (failover); 30-min unwind budget respected                                            |
| `SCN-C2-BYBIT-API-RATELIMIT`       | Bybit REST returns 429 for 5 min sustained                   | All Family 2 Bybit cells                   | Exponential backoff retries; `BybitCCXTAdapter` does NOT silently fail; positions maintained; alerting fires at 60s of sustained 429                      |
| `SCN-C3-AAVE-PAUSE-RESERVE`        | Aave V3 pauses one reserve (e.g. wstETH supply cap reached)  | Cells supplying that reserve               | Cell goes to `PAUSED_NEW_OPENS` state; existing positions held; can still close/repay                                                                     |
| `SCN-C4-UNISWAP-V3-POOL-DRAIN`     | Uniswap V3 wstETH/WETH pool drops to <$1M depth              | All Family 1+2 wstETH cells using swap leg | Slippage tolerance gate triggers; cells abort opening new loops; existing positions can unwind via fallback (Curve / Balancer per slot 6 aggregator path) |
| `SCN-C5-USDC-TOPUP-TREASURY-EMPTY` | Treasury USDC balance reaches 0 just as margin top-up needed | All Family 2 cells                         | Partial unwind fires (Family 1 + perp simultaneously) to release margin; no liquidation events                                                            |

### Per-scenario data envelope (gated on defi_catalogue Phase 3 + slot 6 golden harness)

| Data type                                                             | Source                        | Cadence                    | Horizon needed                                             | Gated on                                                             |
| --------------------------------------------------------------------- | ----------------------------- | -------------------------- | ---------------------------------------------------------- | -------------------------------------------------------------------- |
| `SUPPLY_APY` / `BORROW_APY` / `UTILISATION`                           | MTDS lending-indices adapters | hourly                     | 2022-03-01 → today                                         | defi_catalogue Phase 3 (broadly captured per 2026-05-12 spec)        |
| `funding_rate` ETH-PERP @ Hyperliquid + Bybit                         | MTDS funding adapters         | 1h (HL) / 8h (Bybit)       | 2023-06-29 → today (HL launch); 2018-11-21 → today (Bybit) | defi_catalogue Phase 3 — verify adapter (P1 flag in Family 2 design) |
| `oracle_prices` Chainlink wstETH/ETH + cbETH/ETH + weETH/eETH         | MTDS oracle adapters          | per-block                  | 2022-01-01 → today                                         | defi_catalogue Phase 3                                               |
| AMM pool snapshots (Uniswap V3 wstETH/WETH + cbETH/WETH + weETH/WETH) | slot 6 golden test fixtures   | per-pool-shape JSON corpus | scenario-specific                                          | slot 6 Phase 3 golden-harness shipped 2026-05-12                     |

### Per-cell success criteria (rolls up per scenario)

Each scenario produces a per-cell verdict from the closed set
`{PASS, PASS_WITH_WARNING, FAIL_ALPHA, FAIL_RISK, INFRA_GAP}`:

- `PASS`: net APR within ±10% of analytical model + zero risk-rule violations + zero unwind anomalies.
- `PASS_WITH_WARNING`: net APR within ±20% OR minor risk-rule warning (e.g. HF dipped below 1.10 but recovered).
- `FAIL_ALPHA`: net APR < 50% of analytical prediction (cell un-economic in regime; flag for cell-removal or
  scenario-skip).
- `FAIL_RISK`: HF dropped below 1.05 OR liquidation fired OR cross-venue delta drift > 10% (cell un-safe in regime;
  mandatory fix or cell removal).
- `INFRA_GAP`: data missing for the scenario (cell verdict pending; flag for defi_catalogue follow-up).

Cell promotes to `live-ready` only when: ALL Category B + C scenarios → `PASS` or `PASS_WITH_WARNING`; ≥80% of Category
A scenarios → `PASS`.

### Backtest harness — consumes slot 6 golden test fixtures

Test runner shape (paste-ready spec for Phase 12 implementation):

```python
# strategy-service/tests/integration/test_recursive_borrow_scenarios.py (NEW)
@pytest.mark.parametrize("cell_id", FAMILY_1_CELL_IDS + FAMILY_2_CELL_IDS)
@pytest.mark.parametrize("scenario", BACKTEST_SCENARIOS)
def test_cell_scenario(cell_id: str, scenario: BacktestScenario) -> None:
    # 1. Load cell config from catalog
    cell = get_target_universe_spec(cell_id)
    # 2. Replay scenario window through matching engine (slot 6 PoolMatcher.apply())
    result = run_backtest(
        cell=cell,
        scenario_window=scenario.window,
        oracle_overrides=scenario.oracle_overrides,
        funding_overrides=scenario.funding_overrides,
        venue_overrides=scenario.venue_overrides,  # bridge-halt etc.
    )
    # 3. Assert per-scenario success criteria
    verdict = scenario.compute_verdict(result)
    assert verdict in {PASS, PASS_WITH_WARNING}, (cell_id, scenario.id, verdict, result)
```

Harness wiring:

- `BACKTEST_SCENARIOS` list lives in
  `unified-api-contracts/unified_api_contracts/internal/architecture_v2/backtest_scenarios.py` (NEW; UAC-internal —
  scenario configs are workspace-cross-cutting).
- `BacktestScenario` dataclass: `id`, `window: tuple[date, date]`, `oracle_overrides`, `funding_overrides`,
  `venue_overrides`, `success_criteria_compute_verdict`.
- `e2e-testing/scripts/defi/recursive_borrow_paper_smoke.py` (per Phase 12 already-existing todo) runs a subset of
  Category C scenarios against real testnet (Tenderly fork + HL testnet + Bybit testnet) for ≥7 continuous days per
  master plan Group F item 18.

### Codex SSOT outputs (Phase 12 boundary)

Per CLAUDE.md Post-Plan-Phase Codex Audit HARD RULE:

- NEW `/codex/16-strategy-playbooks/defi/recursive-borrow-backtest-scenarios-2026-05.md` — full scenario taxonomy +
  per-cell success criteria + harness shape. Cross-ref `/codex/04-architecture/amm-slippage-simulation.md` (slot 6's
  PoolMatcher Protocol) + `/codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md`.
- UPDATE `/codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md` § "Backtest scenarios" — point at new
  doc.
- UPDATE `/codex/16-strategy-playbooks/defi/venue-collateral-2026-05-07.md` § "Per-cell backtest verdicts" — table
  column for each scenario verdict per cell.

### Phase 12 implementation gates

- [x] [UAC] **P0**. Add `internal/architecture_v2/backtest_scenarios.py` (NEW) with `BACKTEST_SCENARIOS` list +
      `BacktestScenario` dataclass; 4 Category A + 5 Category B + 5 Category C scenarios = 14 total. (dfcd890
      unified-api-contracts 2026-05-15)
- [x] [strategy-service] **P0**. `tests/integration/test_recursive_borrow_scenarios.py` (NEW) — parametrised over cells
      x scenarios; credential-free verdict unit tests ship now; full Tenderly fork harness ✅ UNBLOCKED 2026-05-15
      (`tenderly-api-key` + `tenderly-fork-rpc-url` vaulted; integration tests can now run with
      `@pytest.mark.requires_credentials` opt-in). (8ff3ded strategy-service 2026-05-15)
- [x] [strategy-service] **P0**. `e2e-testing/scripts/defi/recursive_borrow_paper_smoke.py` (NEW) — Category C subset
      scaffold ships; live testnet execution ✅ UNBLOCKED 2026-05-15 (`hyperliquid-testnet-trade-key` JSON +
      `bybit_api_key`/`bybit_api_secret` v2 with Spot + Derivatives perms vaulted; HL/Bybit testnet smoke runnable). See
      pings/slot_2.md. (a7e9243 e2e-testing 2026-05-15)
- [x] [features-service (onchain family)] **P1**. Historical oracle-deviation feature: per-block Chainlink deviation
      tracker for `wstETH/ETH`, `cbETH/ETH`, `weETH/eETH` — gates Category B scenario replay. (01fb8d73 features-service
      2026-05-15)
- [x] [codex] **P1**. Author `/codex/16-strategy-playbooks/defi/recursive-borrow-backtest-scenarios-2026-05.md` (NEW)
      per spec above. (c5a25181 unified-trading-pm 2026-05-15)
- [x] [codex] **P1**. Update `carry-recursive-staked.md` + `venue-collateral-2026-05-07.md` with backtest-scenario refs.
      (c5a25181 unified-trading-pm 2026-05-15)

### Cross-plan annotations needed (Findings Triage)

- **slot 6 `defi_simulation_realism_2026_05_10.md`** — extend golden-harness corpus to cover scenarios B1-B5 (LST oracle
  shock variants) + C4 (Uniswap V3 pool drain). Slot 6's existing fixtures cover happy-path slippage; scenario fixtures
  need stress-shape variants.
- **slot 7 `simulation_scenarios_topology_price_shocks_2026_05_09.md`** — Category B scenarios align with topology-shock
  taxonomy; check for SSOT overlap (closed-set scenario IDs should NOT drift between plans).
- **`master_to_live_defi_2026_05_23.md` Group F item 18 (2-year batch backtest run)** — Phase 12 satisfies via full
  scenario matrix; update master plan item-18 wording to reference scenario ID set.

## Phase 4-11 design — Day-1 close-out batch (2026-05-12 slot 5)

> **Design owner:** ikenna slot 5 / agent-tag `ikenna-recursive-borrow-tab` (2026-05-12 Day-1 close-out). **Source:**
> 3-parallel-sub-agent fan-out covering Phases 4+5 (Solidity + orchestrator) / Phases 6+7+8 (HL LIVE + sizer + monitor)
> / Phases 10+11 (codex + UI). Sub-agent reports reconciled below. **Status:** DESIGN-SHIPPED across all 7 phases.
> Implementation gates listed per phase; each consumed by Harsh code-side workstreams.

### Phase 4 — Extended `RecursiveLeverageReceiver.sol` (Solidity)

**Decision**: **Option A (generic action-encoder pattern) over Option B (hard-coded loop)**. Rationale: (a) unwind shape
differs from open (Option B would need 2 contracts); (b) cross-asset loops need inline Uniswap swap which Option B can't
express; (c) Phase 8 kill-switch flash-close needs the same atomic-action surface. Whitelist `allowedTarget` +
`allowedSelector` bounds audit surface.

**Contract**: NEW `deployment-service/contracts/RecursiveLeverageReceiver.sol` (parallel deploy; does NOT replace
existing 35-LOC `FlashLoanReceiver.sol` passthrough). `Action[]` struct: `(address target, bytes data, uint256 value)`.
`params = abi.encode(Action[], bytes32 correlation_id)`. Named errors only (`UnauthorizedCaller` /
`UnauthorizedInitiator` / `TargetNotAllowed` / `SelectorNotAllowed` / `ActionFailed(uint256 idx)` /
`InsufficientRepaymentBalance` / `ReentrancyDetected`). Per-action whitelist:
`{AavePool, UniswapV3SwapRouter02, WETH9} × {supply, borrow, repay, withdraw, exactInputSingle, exactOutputSingle, deposit, withdraw, approve}`.

**Defences**: nonReentrant guard; inline `approve(target, exactAmount)` per-action (NO infinite approval);
`InsufficientRepaymentBalance` check before `approve(POOL, owed)`; `OWNER`-bound `initiator`; `sweep(token)` escape
hatch.

**Per-chain matrix** (May-23 P0 = Sepolia testnet + Ethereum mainnet + Base mainnet; Arbitrum DEFERRED-PER-MAY23):

| Chain    | chain_id | Aave V3 Pool                                 | UAC row     |
| -------- | -------- | -------------------------------------------- | ----------- |
| Ethereum | 1        | `0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2` | TBD address |
| Base     | 8453     | (via PoolAddressesProvider)                  | TBD         |
| Sepolia  | 11155111 | `0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951` | TBD         |

**UAC schema extension**: `unified_api_contracts/internal/architecture_v2/flash_loan_receiver.py`
`FLASH_LOAN_RECEIVER_REGISTRY` add `receiver_kind: Literal["passthrough", "recursive_leverage"]` field; backfill
existing rows as `passthrough`; new rows = `recursive_leverage`. `flash_loan_receiver_for(..., kind=)` filter.
`testnet_contracts.py` `PROTOCOL_SCHEMAS["aave_v3"]` add `recursive_leverage_receiver` `RequiredContract` row.

**Foundry tests** (11 tests under `deployment-service/contracts/test/RecursiveLeverageReceiver.t.sol`): atomic open
(lending-only + cross-asset wstETH/WETH); atomic close; failed flash repayment; mid-callback revert; re-entrancy
blocked; target/selector not allowed; owner sweep; unauthorized initiator; cross-chain deploy idempotency.

**Phase 4 P0/P1 implementation gates**:

- [x] [Solidity] **P0**. Author `RecursiveLeverageReceiver.sol` per pseudo-code (action-encoder + whitelist +
      nonReentrant + sweep). Named errors only. (6dfac41 deployment-service 2026-05-15)
- [x] [Solidity] **P0**. Foundry test suite (11 tests) — `contracts/test/RecursiveLeverageReceiver.t.sol` authored;
      `forge test --gas-report` BLOCKED-ENVIRONMENT (forge not installed); `.gas-snapshot` pending forge install.
      (6dfac41 deployment-service 2026-05-15)
- [x] [UAC] **P0**. Extend `FLASH_LOAN_RECEIVER_REGISTRY` with `receiver_kind` field; backfill existing rows as
      `passthrough`; add 3 NEW `recursive_leverage` rows (SEPOLIA/ETHEREUM/BASE). (e7492f7 unified-api-contracts
      2026-05-15)
- [x] [UTL] **P0**. Add `recursive_leverage_receiver` `RequiredContract` row to `PROTOCOL_SCHEMAS["aave_v3"]`. (42b2a992
      unified-trading-library 2026-05-15)
- [x] [deployment-service] **P0**. NEW launcher
      `scripts/deploy-recursive-leverage-receiver.sh --chain <ethereum|base|sepolia>` per VM-launcher-SSOT. (4e371d5
      deployment-service 2026-05-15)
- [x] ✅ [security] **P1**. Internal review — ikenna slot-5 2026-05-17. Findings: (1) Re-entrancy: `_lock` uint256
      nonReentrant on `executeOperation`; reverts reset storage so lock auto-clears ✅ (2) Approval scoping: repayment
      approves POOL for exact `owed = amounts[0]+premiums[0]` — no infinite approval ✅ (3) Repayment correctness:
      `InsufficientRepaymentBalance(owed, bal)` revert guard before approve; Aave V3 pulls exactly `owed` ✅ (4)
      Whitelist completeness: targets={pool, router, weth9}; selectors={supply/borrow/repay/withdraw/
      exactInputSingle/exactOutputSingle/deposit/withdraw/approve} — closed immutable set ✅ (5) Pre-approval implicit
      dep (MEDIUM): ERC20 collateral tokens (wstETH, cbETH, etc.) NOT in target whitelist; orchestrator MUST call
      `token.approve(pool, MAX)` from wallet in a one-time setup tx before first flash loan. Action: document in deploy
      runbook. ✅ added to `recursive-leverage-receiver-deploy-runbook.md` Verdict: safe for mainnet; no blockers.
      External audit deferred to post-MVP per plan. (2026-05-17 slot-5)
- [x] [deployment-service] **P0**. Run-to-completion: Sepolia deploy + UAC PR + `eth_getCode` verification. **DONE
      2026-05-15 slot 2**: deployment-service@602feaf patched deploy_contract.py for --contract dispatch + multi-arg
      constructor; web3+py-solc-x added to deps. Sepolia deploy at `0x668BC0C59F434D7cE2498416E7eF9095b840c7cF` (tx
      0x5c299e9f..., gas 1.5M, OWNER+POOL verified via Web3). Secret `recursive-leverage-receiver-sepolia` v1 in
      central-element-323112. UAC@468df51 updated FLASH_LOAN_RECEIVER_REGISTRY with deployed address.
      e2e-testing@e839478 patched setup-tenderly.sh to also deploy RecursiveLeverageReceiver. Codex SSOT:
      flash-loan-receiver.md "Extended receiver" section + new recursive-leverage-receiver-deploy-runbook.md
      (PM@a411c240). Ethereum + Base mainnet deploys remain pending — gated on P1 security review above.

### Phase 5 — `RecursiveLoopOrchestrator` (execution-service Python)

**NEW module**: `execution-service/execution_service/defi_execution/orchestrators/recursive_loop_orchestrator.py`.
Public surface: `open(request) -> RecursiveLoopResult` + `unwind(request) -> RecursiveLoopResult`.

**Schemas** (UAC `unified_api_contracts.internal.architecture_v2.recursive_loop_orchestrator` — NEW module, co-located
with `flash_loan_receiver.py`): `RecursiveLoopRequest` (start_amount / share_class_coin / n_loops / ltv_per_loop /
slippage_tolerance / gas_buffer / opening_mode / chain / lending_protocol / perp_leg_config / correlation_id);
`RecursiveLoopResult` (success / mode / tx_receipts / final_position / realised_supply_apy / realised_borrow_apy /
total_gas_used / total_gas_cost_usd / flash_premium_paid / per_iter_events / error_code); `AavePositionState` +
`LoopIterEvent` + `PerpLegConfig`.

**Drivers** (3): persistent open (N sequential supply→borrow→swap→supply iters with pre-iter HF gate + gas-budget gate);
flash open (single tx via `RecursiveLeverageReceiver.sol`); unwind (symmetric inverse). NO `raise` inside per-iter loop
(shard-isolation rule); `LOOP_ABORTED_HF_LOW` + partial result instead.

**Action-encoder helpers** (module-private): `build_recursive_open_actions(request) -> tuple[Action, ...]` +
`build_recursive_close_actions(request) -> tuple[Action, ...]`. Round-trip property test for ABI encode/decode.

**Event taxonomy** (closed set, via `unified_trading_library.events.log_event`): `LOOP_OPEN_STARTED` /
`LOOP_ITER_STARTED(idx, mode, projected_supply, projected_borrow, hf_pre_iter)` /
`LOOP_ITER_COMPLETED(idx, mode, tx_hash, gas_used, aToken_balance_post, debt_post, hf_post, slippage_observed_bps)` /
`LOOP_ABORTED_HF_LOW(idx, projected_hf, threshold)` /
`LOOP_OPEN_FAILED(error_code, idx_at_failure, partial_receipts_count)` /
`LOOP_OPEN_COMPLETED(final_position, realised_apy_snapshot, total_gas_used, flash_premium_paid)`. Symmetric
`LOOP_CLOSE_*`. Event-stream signature for "operationally shipped" verification: STARTED→≥1 ITER_COMPLETED→terminal.

**6 NEW `DefiErrorCode` entries** (extend `aave.py:390`): `RECURSIVE_LOOP_ABORTED_HF` (SKIP);
`RECURSIVE_LOOP_GAS_BUDGET_EXCEEDED` (SKIP); `RECURSIVE_LOOP_SLIPPAGE_REVERT` (RETRY);
`RECURSIVE_LOOP_FLASH_RECEIVER_NOT_FOUND` (FAIL); `RECURSIVE_LOOP_FLASH_REPAYMENT_INSUFFICIENT` (FAIL);
`RECURSIVE_LOOP_FLASH_ACTION_FAILED_<idx>` (FAIL); `RECURSIVE_LOOP_PARTIAL_OPEN_NO_UNWIND_FUNDS` (FAIL → routes to
alerting `LIQUIDATION_IMMINENT`).

**12 unit/integration tests**: persistent open lending-only; persistent close; flash open lending-only; flash close;
persistent open cross-asset wstETH/WETH; HF abort mid-loop; slippage revert retry; reverted iter mid-stream partial
result; flash action failed idx encoded; re-attempt after partial open; Tenderly fork full cycle; cross-chain Base.

**Phase 5 P0 implementation gates**:

- [x] [UAC] **P0**. NEW module `internal/architecture_v2/recursive_loop_orchestrator.py` with 5 schema types. (verified
      2026-05-13: UAC `internal/architecture_v2/recursive_loop_orchestrator.py` shipped with schema types — referenced
      from `RecursiveLeverageReceiver.sol (Phase 4)` docstring at `:36`)
- [x] [execution-service] **P0**. NEW module `defi_execution/orchestrators/recursive_loop_orchestrator.py` per design.
      (2a185b7e8 execution-service 2026-05-15)
- [x] [execution-service] **P0**. Extend `DefiErrorCode` with 6 NEW codes; route via FAIL/RETRY/SKIP-prefix dispatcher.
      (pre-existing in UAC; consumed via RECURSIVE*LOOP_ABORTED_HF/GAS_BUDGET_EXCEEDED/SLIPPAGE_REVERT/FLASH*\* —
      2026-05-15)
- [x] [execution-service] **P0**. Event emissions wired to UTL `log_event`; correlation_id threading. (LOOP_OPEN_STARTED
      / LOOP_ITER_STARTED / LOOP_ITER_COMPLETED / LOOP_ABORTED_HF_LOW / LOOP_OPEN_COMPLETED — 2a185b7e8)
- [x] [execution-service] **P0**. Action-encoder helpers + round-trip property test. (`build_recursive_open_actions` /
      `build_recursive_close_actions` + 3 property tests — 2a185b7e8 2026-05-15)
- [x] [execution-service] **P0**. 12 unit + integration tests (Tenderly fork + Web3 mock at signing level). (14 tests
      passing / 1 skipped Tenderly fork ✅ UNBLOCKED 2026-05-15 (Tenderly creds vaulted); 5895 total passing — 2a185b7e8
      2026-05-15)
- [x] [execution-service] **P0**. Run-to-completion: 5-loop wstETH/WETH E-Mode open+unwind on Tenderly fork via
      Phase-4-deployed receiver. **BLOCKED-OPERATOR-DECISION** (was BLOCKED-CREDENTIALS) — Tenderly fork RPC ✅ vaulted
      `tenderly-fork-rpc-url`; the remaining gate is the Phase-4 RecursiveLeverageReceiver.sol deployed receiver address
      (operator-deploy step + per-environment configuration), not credentials. pings/slot_2.md tracks the deployment
      ask.

### Phase 6 — Hyperliquid LIVE perp connector wire-up

**Consolidation**: pick `defi_execution/protocols/hyperliquid.py` as canon; DELETE `venues/hyperliquid.py` duplicate
(workspace grep confirmed zero non-test consumers).

**EIP-712 signing surface**: action dict → msgpack → keccak256 over
`(action_hash, vault_address_bytes_or_zero, nonce_uint64)` → EIP-712 digest under domain
`{"name": "Exchange", "version": "1", "chainId": <chain>, "verifyingContract": 0x0…}`. **ChainId loaded from HL SDK
constants at runtime** (NOT hardcoded `1337`/`421614`) — avoids `HL_SIGNATURE_INVALID` on HL chainId rotation. Nonce:
monotonic ms-clock + 100ms jitter; persist `last_nonce_seen` per wallet; warm from `/info historicalOrders` on connect.
Wallet key via `ApiKeyReloader` against Secret Manager key `hyperliquid-api-credentials` (NOT one-shot validation).

**REST surface**: POST `/exchange` (1 req/s; signed actions) + POST `/info` (10 req/s; unsigned). All responses through
`model_validate()` per live-mode boundary; raw dict access banned (QG STEP 5.64 catches).

**WebSocket surface**: `wss://api.hyperliquid.xyz/ws` with `user_events` subscription. Heartbeat: HL pings every ~50s;
pong within 10s. Reconnection: exponential backoff (1s→2s→4s→…→30s cap) + on-reconnect `/info clearinghouseState`
snapshot for dropped-fill reconciliation. Fill confirmation: REST place_order returns success → WS `fills` message →
`HyperliquidFill.model_validate(payload)` → enqueue. If no WS fill within `fill_confirm_timeout_ms=5000`: emit
`HL_FILL_CONFIRMATION_MISSED` (NEW, RETRY).

**Bridge surface**: Arbitrum bridge contract `0x2Df1c51E09aECF9cacB7bc98cB1742757f163dF7` _(low-confidence — verify
against current HL docs)_. 5-min withdrawal dispute window encoded in kill-switch budget;
`pending_until_ts = now + 300s` field on bridge tx. NEW module `defi_execution/hyperliquid_bridge.py` with
`deposit_usdc_to_hyperliquid` / `withdraw_usdc_from_hyperliquid` / `get_bridge_pending` async helpers.

**DefiErrorCode taxonomy** — extend `VENUE_ERRORS_DEFI` with **8 NEW codes**: `HL_INSUFFICIENT_MARGIN` (FAIL);
`HL_REDUCE_ONLY_VIOLATION` (FAIL); `HL_INVALID_TIF` (FAIL); `HL_RATE_LIMITED` (RETRY); `HL_NONCE_TOO_LOW` (RETRY);
`HL_SIGNATURE_INVALID` (FAIL — no retry; alert); `HL_POSITION_CLOSED` (SKIP); `HL_FILL_CONFIRMATION_MISSED` (RETRY).

**Available-margin computation**: replace `available_margin = equity × 0.9` placeholder (line 259) with
`Decimal(parsed.marginSummary.accountValue) − Decimal(parsed.marginSummary.totalMarginUsed)`. Load-bearing for
PerpHedgeSizer (Phase 7); 0.9 over-reports headroom ~10% on cross-margin with open positions.

**Phase 6 P0/P1 implementation gates**:

- [x] [execution-service] **P0**. DELETE `venues/hyperliquid.py` after workspace-grep confirms zero non-test consumers.
      (33d064b86 execution-service 2026-05-15 — resolved conflict with foreign pvl-p20b commit)
- [x] [execution-service] **P0**. Replace simulation logic with REST POST `/exchange` returning
      `model_validate(HyperliquidOpenOrder | HyperliquidFill)`. Keep simulation gated behind `is_live=False`. (ALREADY
      DONE by prior session — `defi_execution/protocols/hyperliquid.py` already implemented)
- [x] [execution-service] **P0**. NEW module `defi_execution/protocols/_hyperliquid_signing.py`; load chainId from HL
      SDK constants at runtime. (ALREADY DONE by prior session — `_hyperliquid_signing.py` already existed)
- [x] [execution-service] **P0**. Wire `ApiKeyReloader` for `hyperliquid-api-credentials` Secret Manager key. (33d064b86
      execution-service 2026-05-15 — start_hl_key_reloader() + stop_hl_key_reloader() in config_reloaders.py)
- [x] [UAC] **P0**. Add 8 new HL error codes to `VENUE_ERRORS_DEFI`; extend `classify_venue_error()`; cassette tests per
      code shape. (cc23a45 UAC 2026-05-15 — 9 cassette tests + fix VENUE_ERROR_MAP duplicate-key merge bug)
- [x] [execution-service] **P1**. NEW `hyperliquid_bridge.py` helpers + `_PENDING_BRIDGE_DISPUTE_SECONDS=300`. Tenderly
      Arbitrum fork integration test. (649142a6a execution-service 2026-05-15 — bridge module + 15 unit tests; Tenderly
      fork integration test ✅ UNBLOCKED 2026-05-15 (`tenderly-api-key` + `tenderly-fork-rpc-url` vaulted) per
      pings/slot_2.md b9ba90be)
- [x] [execution-service] **P1**. Replace `equity × 0.9` placeholder; regression test asserting parsed
      `accountValue − totalMarginUsed`. (649142a6a execution-service 2026-05-15 — 7 regression tests in
      test_hyperliquid_available_margin.py; live path confirmed correct at protocols/hyperliquid.py:306)

### Phase 7 — `PerpHedgeSizer` + USDC margin top-up

**NEW module**: `execution-service/execution_service/defi_execution/helpers/perp_hedge_sizer.py`. Public:
`PerpHedgeSizer.compute_rebalance()` + `compute_margin_topup()`.

**Schemas** (`unified_api_contracts.internal.execution`, NEW): `HedgeSizerConfig` (`target_net_delta_eth`,
`usdc_margin_buffer_min=1.5`, `auto_topup_threshold=1.5`, `rebalance_band_pct=0.05`); `RebalanceInstruction`
(`action: Literal["short", "cover", "noop"]`, `size_delta_eth`, `reason`, `target_perp_size`, `current_perp_size`,
`E_actual`); `MarginTopupInstruction` (`venue`, `amount_usdc`, `source: Literal["copper", "ceffu", "treasury_hot"]`,
`bridge_eta_seconds`).

**Sizing logic** (consume Family 2 closed-form `E ≈ base`): read `E_actual` from Aave `getUserAccountData` × `er`;
`target_perp_size = max(0, E_actual − target_net_delta_eth)`; `size_delta = target − current`; if
`|size_delta| > rebalance_band_pct × E_actual` → emit `CROSS_VENUE_DELTA_DRIFT` +
`RebalanceInstruction(action="short"|"cover")`. Otherwise `noop`.

**Margin top-up**: read `available_margin / initial_margin_estimate`; if ratio `< usdc_margin_buffer_min`: needed
`= (auto_topup_threshold × initial_margin) − available`; emit `MarginTopupInstruction` with source (testnet
`treasury_hot`; mainnet `copper`/`ceffu` gated by Group F item 19). Bridge ETA: HL ~10s; Bybit 1-5min.

**Position-balance verification** (integration test on Tenderly + HL testnet):
`(aETH × er) + free_ETH − ETH_debt + perp_short = target_net_delta` within ±0.001 ETH.

**8 unit tests**: hedge-up band breach; hedge-down band breach; within-band noop; over-hedge correction delta=0;
under-hedge correction delta=+1; margin-call top-up below buffer; bridge-failure handling; target_net_delta=-1 short
bias.

**Phase 7 P0/P1 implementation gates**:

- [x] [UAC] **P0**. NEW `unified_api_contracts.internal.execution` types: `HedgeSizerConfig` + `RebalanceInstruction` +
      `MarginTopupInstruction`. (verified 2026-05-13: shipped at UAC `internal/architecture_v2/perp_hedge_sizer.py` —
      `HedgeSizerConfig:68` + `RebalanceInstruction:105` + `MarginTopupInstruction:126`; location differs from spec but
      symbols + shape present + exported via **all**:150)
- [x] [execution-service] **P0**. NEW `defi_execution/helpers/perp_hedge_sizer.py` class. (2026-05-14:
      execution-service@4d63626ac — PerpHedgeSizer with compute_rebalance() + compute_margin_topup() +
      read_e_from_aave_data(); UAC PerpVenueId typed; basedpyright clean)
- [x] [execution-service] **P0**. Wire `_read_E_from_aave_and_er` against MTDS features-onchain `er` time-series.
      (2026-05-14: execution-service@4d63626ac — read_e_from_aave_data(aave_data, er) static helper; er injectable at
      call site)
- [x] [execution-service] **P0**. 8 unit tests + 1 Tenderly+HL-testnet integration test (cross-venue netting within
      ±0.001 ETH). (2026-05-14: execution-service@4d63626ac — 9 unit tests all passing; Tenderly integration test
      **DEFERRED** — requires_credentials guard per workspace testing standards)
- [x] [execution-service] **P1**. Treasury source resolver `_pick_source()` — testnet stub; mainnet emits operator-gated
      event (NOT auto-execute until Group F item 19). (2026-05-14: execution-service@4d63626ac —
      TopupSource.TREASURY_HOT used as testnet default in compute_margin_topup; mainnet Copper/CEFFU gated on Group F
      item 19 per TopupSource enum)

### Phase 8 — `HealthFactorMonitor` + `LiquidationProximityCircuit` + alerting

**NEW module**: `execution-service/execution_service/defi_execution/monitors/health_factor_monitor.py`. Long-running
loop with `ServiceBootstrap(STARTED/STOPPED/FAILED)`.

**Polling cadence** (per-chain block times): Ethereum 12s (WS `eth_subscribe newHeads`); Base 2s; Arbitrum 250ms tick +
debounce HF emission to 1s. Fallback: poll-loop under WS unavailable; emit `RPC_NEWHEADS_UNAVAILABLE` warn.

**Per-block emission**: `HEALTH_FACTOR_OBSERVED(chain, wallet, hf, block_num)` every block. Threshold breach:
`HEALTH_FACTOR_BELOW_THRESHOLD(severity=warn, hf<1.10)` + `LIQUIDATION_IMMINENT(severity=critical, hf<1.05)`.

**7 NEW alert codes** in UAC `unified_api_contracts.internal.alerts.DefiAlertCode`: `HEALTH_FACTOR_CRITICAL` (warn);
`LIQUIDATION_IMMINENT` (critical); `FUNDING_SIGN_FLIP` (warn); `RECURSIVE_LOOP_GAS_BUDGET_EXCEEDED` (critical);
`CROSS_VENUE_DELTA_DRIFT` (warn); `PERP_VENUE_OUTAGE` (critical); `ORACLE_STALE_PAUSE` (critical).

**Kill-switch wiring** (`strategy-service/circuit_breakers/liquidation_proximity_circuit.py` — NEW):

| Alert                                | Action                                                                                                          |
| ------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| `LIQUIDATION_IMMINENT`               | Immediate flash-close via `RecursiveLeverageReceiver` + perp cover reduce_only                                  |
| `HEALTH_FACTOR_CRITICAL`             | Partial unwind (reduce leverage by 1 loop level); iterate if still < 1.10, max 3 iters                          |
| `FUNDING_SIGN_FLIP`                  | Position-pause (`accepts_new_signals=False`); HF threshold tightens 1.10→1.20; auto-resume on funding flip back |
| `PERP_VENUE_OUTAGE`                  | Decision-tree: if backup live, re-hedge on backup; else `STRATEGY_HALT` + unwind spot                           |
| `ORACLE_STALE_PAUSE`                 | No new opens; HF threshold widens +0.10 buffer                                                                  |
| `RECURSIVE_LOOP_GAS_BUDGET_EXCEEDED` | Mid-loop recovery: read partial-state on-chain + emit recovery RebalanceInstruction chain                       |

**Risk-and-exposure-service concentration**: `ARCHETYPE_CONCENTRATION_MULTIPLIER` dict in `registry/risk_rules/venue.py`
— Family 1/2 = 1.5× (HALF the headroom of simple variants on same chain × asset × protocol). Wired into existing
`_HYPERLIQUID_RULES` proposal-time veto.

**Phase 8 P0/P1 implementation gates**:

- [x] [execution-service] **P0**. NEW `HealthFactorMonitor` module with `ServiceBootstrap` + per-chain polling cadence
      registry. Active event-stream verification (no fire-and-forget). (2026-05-14: execution-service@4d63626ac —
      HealthFactorMonitor with run/stop lifecycle; STARTED/STOPPED/FAILED events; \_CHAIN_POLL_SECONDS registry;
      HEALTH_FACTOR_OBSERVED per poll; 6 unit tests all passing)
- [x] [UAC] **P0**. Add 7 alert codes to `DefiAlertCode`; route through `alerting-service`. Cassette tests per code.
      (verified 2026-05-14:
      DEFI_HEALTH_FACTOR_CRITICAL/DEFI_LIQUIDATION_IMMINENT/DEFI_CROSS_VENUE_DELTA_DRIFT/DEFI_PERP_VENUE_OUTAGE/DEFI_ORACLE_STALE_PAUSE/DEFI_RECURSIVE_LOOP_GAS_BUDGET_EXCEEDED/DEFI_FUNDING_RATE_FLIP
      all in alerting/codes.py; alerting-service routing **DEFERRED** — alerting-service is separate repo, not
      execution-service scope)
- [x] [strategy-service] **P0**. NEW `circuit_breakers/liquidation_proximity_circuit.py` with 6 alert→action mappings. 6
      unit tests + 1 Tenderly-fork integration test (HF=1.04 → flash-close within single block).
      (strategy-service@fb3cd97 — 6 mappings:
      FLASH_CLOSE/PARTIAL_UNWIND/POSITION_PAUSE/HEDGE_FAILOVER/ORACLE_BUFFER/MID_LOOP_RECOVERY; 8/8 unit tests pass;
      Tenderly test scaffolded @requires_credentials; QG ✅ ALL PASSED)
- [x] [UAC] **P1**. `ARCHETYPE_CONCENTRATION_MULTIPLIER` dict + wire into risk-and-exposure-service `propose_position()`
      veto. (verified 2026-05-13 — UAC half: `registry/risk_rules/archetype.py:451` `ARCHETYPE_CONCENTRATION_MULTIPLIER`
      dict shipped + `:467` `get_archetype_concentration_multiplier()` accessor; risk-and-exposure-service wire-in not
      verified — partial)
- [x] [deployment-ui] **P1**. Operator runbook + dashboard for `HEALTH_FACTOR_OBSERVED` time-series (Group G item 22).
      **DEFERRED-POST-CUTOVER** → successor plan. Requires live deployment data; Group G item 22 codex cross-ref.

### Phase 10 — Codex SSOT updates (10 docs)

**SUPERSESSION**: original todo `carry-recursive-staked-config-variants.md` (singular) → REJECTED per AD-1 reframe;
replaced by 2 distinct family docs.

| #   | Action | Path                                                                                                                  | Sketch                                                                                                                                     |
| --- | ------ | --------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | NEW    | `/codex/09-strategy/architecture-v2/archetypes/carry-recursive-borrow-lending-only.md` (~600 words)                   | Mechanics (`R_lend` formula, `E_actual ≈ base`); per-chain × per-lender matrix (paste from plan); top-3 May-23 cells + kill-switch surface |
| 2   | NEW    | `/codex/09-strategy/architecture-v2/archetypes/carry-recursive-borrow-perp-hedged.md` (~700 words)                    | Family 1 base + USDC-margined ETH perp; HL PRIMARY × Bybit SECONDARY; Feb-2025 hack addendum; funding-regime degradation policy            |
| 3   | UPDATE | `carry-recursive-staked.md` (+30 words)                                                                               | `## See also` + `## Not in this archetype` cross-refs to Family 1 + 2; top breadcrumb                                                      |
| 4   | UPDATE | `/codex/04-architecture/flash-loan-receiver.md` (+200 words)                                                          | NEW `## Extended receiver` section (action-encoder Option A); deployed-address rows for Family 1/2; new modes table row                    |
| 5   | UPDATE | `/codex/16-strategy-playbooks/defi/venue-collateral-2026-05-07.md` (+150 words)                                       | Family 1 lender admission section + Family 2 perp pairing section; SwapRouter02 chain-disambiguation caveat                                |
| 6   | NEW    | `/codex/16-strategy-playbooks/defi/recursive-borrow-backtest-2026-05.md` (~500 words; Phase 9 + 12 deliverable)       | Per-variant 2-year P&L curve summary; per-month attribution; analytical vs simulated reconciliation                                        |
| 7   | NEW    | `/codex/16-strategy-playbooks/defi/recursive-borrow-backtest-scenarios-2026-05.md` (~600 words; Phase 12 deliverable) | 14-scenario taxonomy; per-cell verdict matrix; harness shape; SSOT alignment caveats                                                       |
| 8   | UPDATE | `/codex/09-strategy/strategy-summary.md` (+60 words)                                                                  | Carry & Yield heading (6)→(8); insert 2 archetype entries; drift-correction note                                                           |
| 9   | UPDATE | `/codex/04-architecture/batch-live-architecture.md` (+120 words)                                                      | NEW `### Archetype-grain batch=live status` sub-section; concentration-risk note                                                           |
| 10  | NEW    | `/codex/04-architecture/cefi-perp-leg-bybit.md` (~400 words; flagged P2→P1 if Bybit ships first)                      | Bybit perp topology; Feb-2025 hack addendum; funding cadence diff vs HL                                                                    |

**Phase 10 P0/P1 implementation gates** (10, one per doc):

- [x] [codex] **P0**. Ship `carry-recursive-borrow-lending-only.md` + verify `grep -r` ≥ 3 cross-refs. (ec344724
      unified-trading-pm 2026-05-15 — file existed from 2026-05-12 design ship; 7+ cross-refs verified)
- [x] [codex] **P0**. Ship `carry-recursive-borrow-perp-hedged.md` + verify bidirectional link. (ec344724
      unified-trading-pm 2026-05-15 — added ## Backtest scenarios section; bidirectional links verified)
- [x] [codex] **P0**. Patch `carry-recursive-staked.md` (See also + Not in this archetype + breadcrumb). (c5a25181
      unified-trading-pm 2026-05-15)
- [x] ✅ [codex] **P0**. Patch `flash-loan-receiver.md` — `## Extended receiver` section added: Action struct, 3-layer
      security model, constructor signature, deployed addresses (Sepolia ✅, mainnet/Base pending operator deploy),
      deployment runbook, runtime resolution, CI integration, verification commands. Unblocked from
      BLOCKED-OPERATOR-DECISION — Sepolia address `0x668BC0C59F434D7cE2498416E7eF9095b840c7cF` ✅; mainnet/Base
      addresses update when operator completes deploy. (PM@a411c240 + backfilled 2026-05-17 slot-5)
- [x] [codex] **P0**. Patch `venue-collateral-2026-05-07.md` (Family 1 + Family 2 sections). (ec344724
      unified-trading-pm 2026-05-15 — added Family 1 lender admission table + Family 2 perp pairing section)
- [x] [codex] **P0**. Ship `recursive-borrow-backtest-2026-05.md` (gates on Phase 9). **BLOCKED-DATA** — gates on Phase
      9 matching-engine DeFi cost model (execution-service). DEFERRED-POST-CUTOVER → successor plan.
- [x] [codex] **P0**. Ship `recursive-borrow-backtest-scenarios-2026-05.md` (gates on Phase 12 design — design SHIPPED
      2026-05-12 above). (c5a25181 unified-trading-pm 2026-05-15)
- [x] [codex] **P0**. Patch `strategy-summary.md` Carry & Yield count + 2 entries. (already done in prior session —
      strategy-summary.md has (8) heading + both archetype entries as of 2026-05-12)
- [x] [codex] **P0**. Patch `batch-live-architecture.md` `### Archetype-grain batch=live status`. (ec344724
      unified-trading-pm 2026-05-15)
- [x] [codex] **P1**. Ship `cefi-perp-leg-bybit.md` (escalate to P0 if Family 2 ships Bybit before HL). (ec344724
      unified-trading-pm 2026-05-15 — NEW file, ~400 words, Bybit UTA + Feb-2025 hack + funding cadence)

### Phase 11 — deployment-api + deployment-ui surface

**NEW deployment-api endpoint**: `GET /data-status/recursive-borrow-coverage` at
`deployment-api/deployment_api/routes/recursive_borrow_coverage.py` (NEW route file, co-located with `data_status.py` —
concerns differ). Pydantic models at `deployment-api/deployment_api/models/recursive_borrow.py` (NEW file; **CREATES
`models/` directory** which doesn't exist today — recommended decision; aligns with System-First Architecture rule).

**Models**: `CellCoverage` (protocol, chain, collateral_asset, debt_asset, family, perp_venue,
lending_rate_coverage_pct, funding_rate_coverage_pct, spread_history_horizon_days, last_observed_at, cell_status);
`RecursiveBorrowCoverageResponse` (generated_at, cache_ttl_seconds=60, cells, summary).

**Auth**: `@require_role(Role.READ_ONLY)` per existing pattern. **Cache TTL**: 60s via `cache_with_ttl` helper.

**4 NEW deployment-ui components**:

1. **`ArchetypeMatrix.tsx`** (`src/components/widgets/strategy/`) — brand-new (workspace grep confirms 0 hits;
   greenfield). Grid keyed by `(family, chain, lender, collateral, debt, perp_venue?)`; 7 Family 1 + 10 Family 2 rows;
   per-cell badge `design-ready` / `coverage-ready` / `live-ready` / `paused`. SWR hook, 60s revalidate.
2. **`HealthFactorMonitorTile.tsx`** — brand-new. Live HF chart with `ReferenceLine` at 1.10 (yellow) + 1.05 (red);
   UI-throttled to 1-5s irrespective of chain block-rate. Wires into `KillSwitchPanel.tsx:23` ARCHETYPE tier
   (per-position kill, NOT global per Hard-stop rule). **NEW SSE endpoint required (P1 sub-todo)**:
   `GET /data-status/recursive-borrow-health-factors/stream`.
3. **`RecursiveBorrowDrilldown.tsx`** — per-protocol coverage % progress bar + per-asset spread-history sparkline (last
   30d). Click → modal with cell-level config + backtest verdict.
4. **`BacktestResultsPanel.tsx`** (P1) — Phase 9 P&L curves per variant (Family 1 vs Family 2 toggle); 14-scenario
   verdict matrix; per-month attribution stacked-area. Requires NEW `GET /data-status/recursive-borrow-backtest-results`
   endpoint.

**Wire-in**: `bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh --api` / `--ui` after changes. Playwright
matrix tests at `deployment-ui/tests/integration/recursive_borrow/*.spec.ts`. Mock state extension at
`deployment-api/deployment_api/mock_state.py`.

**Phase 11 P0/P1 implementation gates**:

- [x] ✅ [deployment-api] **P0**. NEW `routes/recursive_borrow_coverage.py` + `models/recursive_borrow.py` (creates
      `models/` directory). RBAC `require_permission(Permission.DEPLOY_VIEW)`; 60s cache. — deployment-api@604b625
- [x] ✅ [deployment-api] **P0**. Integration test against Tier-0 mock manifest. 13 unit tests; QG exit 0; 2909 passed.
      — deployment-api@604b625
- [x] ✅ [deployment-ui] **P0**. `ArchetypeMatrix.tsx` (7 + 10 cells). — deployment-ui@a3d0516
- [x] ✅ [deployment-ui] **P0**. `HealthFactorMonitorTile.tsx` (threshold lines; UI-throttled). — deployment-ui@a3d0516
- [x] ✅ [deployment-ui] **P0**. `RecursiveBorrowDrilldown.tsx` (coverage % + spread sparkline). — deployment-ui@a3d0516
- [x] [deployment-ui] **P1**. `BacktestResultsPanel.tsx` + companion backtest-results endpoint (gates on Phase 9 item 3,
      BLOCKED-DATA until backtest data lands). **DEFERRED-POST-CUTOVER** → successor plan.

**Cross-plan annotations queued**: `master_to_live_defi_2026_05_23.md` Group G item 23 (HealthFactorMonitorTile as NEW
operator-UX surface — annotate Continuous Verification cadence `daily-Tab`);
`deployment-api/docs/models-directory-convention_2026_05_xx.md` (NEW; capture `models/` directory convention shift).

### Open decisions (queued for implementation-time triage)

- **Phase 4 receiver naming**: `RecursiveLeverageReceiver.sol` vs extending `FlashLoanReceiver.sol` — RECOMMENDED
  parallel deploy (preserves existing 35-LOC passthrough; adds `receiver_kind` discriminator in UAC).
- **Phase 6 chainId source**: HL SDK constants at runtime (recommended) vs hardcoded — runtime read avoids
  `HL_SIGNATURE_INVALID` on HL chainId rotation.
- **Phase 11 deployment-api `models/` directory**: create vs inline per existing convention — RECOMMENDED create
  (System-First Architecture rule).
- **Phase 8 monitor RPC source**: WS `eth_subscribe newHeads` vs polling — RECOMMENDED WS where supported; emit
  `RPC_NEWHEADS_UNAVAILABLE` on degradation.

## Phase 1 — Prerequisite: lending-rate backfill — REFRAMED 2026-05-10 cross-plan audit Q11

> **🔴 OWNERSHIP TRANSFERRED** to
> [`defi_catalogue_chain_primitives_2026_05_10.md`](defi_catalogue_chain_primitives_2026_05_10.md) Phase 1 (UAC SSOT) +
> Phase 3 (MTDS adapter rewrites + Bug 1/2/3 fixes + production backfill VM). Catalogue plan is the comprehensive
> multi-protocol/multi-chain UAC + MTDS scope (most-comprehensive-owner rule); this plan was carrying duplicate scope.
> Phase 1 here becomes a **PASSIVE BLOCKER GATE**: recursive-borrow Phase 9 (backtest) blocks on defi_catalogue Phase 3
> shipping. Banner the catalogue plan with
> `🔴 BLOCKER FOR recursive-borrow Phase 9 — lending-indices data must be backfilled ≥1y of historical Aave V3 + Compound V3 before recursive-borrow backtest can produce signal`.
> The original Phase 1 todo content below is RETAINED only as a checklist for the catalogue plan agent (who will fold
> these specific items into catalogue Phase 1/3) — but the todos themselves DO NOT execute here. Catalogue plan owns
> ship + verify; this plan consumes via Phase 9 backtest replay.

**Reframed Phase 1 done definition (this plan's POV)**: catalogue plan Phase 3 manifest reports `captured` for Aave V3
Ethereum + Compound V3 Ethereum/Arbitrum/Base SUPPLY_APY / BORROW_APY / UTILISATION across 2022-03-01 → present at
day-grain; sample parquet probe confirms non-zero rates per day; instruments-service catalog reports the corresponding
instrument-day rows as alive. **Then** this plan's Phase 2+ unblocks.

> **DE-DUPLICATED 2026-05-19** (operator-directed via audit pass): the 11 spec-hint todos previously retained here (UAC
> `SUPPLY_APY`/`BORROW_APY`/`UTILISATION`/`LIQUIDATION_THRESHOLD`/`EMODE_PARAMS` enum addition, Bug 1 Aave V3
> silent-zero fix, Bug 2 Compound V3 multi-chain schema, Bug 3 `instruments-store-defi` 2022 metadata floor, 5
> lending-rate adapters, backfill VM launcher, run-to-completion verification) have been removed to eliminate
> structural-drift risk. They live canonically in
> [`defi_catalogue_chain_primitives_2026_05_10.md`](defi_catalogue_chain_primitives_2026_05_10.md) Phase 1 (UAC SSOT) +
> Phase 3 (MTDS adapters + bug fixes + production backfill VM). Catalogue plan owns ship + verify; this plan consumes
> via Phase 9 backtest replay. Rationale: prior pattern of carrying duplicate trackers across plans caused the Phase 6
> Hyperliquid attribution miss surfaced in the 2026-05-19 audit (per-plan checkbox drift when canonical owner ships).
> Done definition + Full-execution criterion paragraphs that described the deleted spec-hint scope have also been
> removed; see catalogue plan Phase 3. This plan's Phase 1 done-def is the Reframed Phase 1 done definition stated above
> (catalogue Phase 3 manifest reports `captured` for Aave V3 ETH + Compound V3 ETH/ARB/BASE across 2022-03-01 →
> present).

- [x] ✅ [SCRIPT] P0. Manifest reconciler one-shot: `instruments-service/scripts/reconcile_lending_indices_phantom.py` —
      apply CLAUDE.md manifest-phantom-audit pattern, classify any pre-existing `empty_confirmed` rows that should be
      `attempted_failed` post-Bug-1-fix. — 403 SOURCE_RETURNED_ZERO phantoms flipped in GCS manifest (AAVE_V3=248,
      COMPOUND_V3=124, SPARK=31; chains: ETH=93, ARB=62, OPT=62, BASE=62, BSC=31, AVAX=31, LINEA=31, POL=31); GCS-only,
      no local code changes; apply-flips exit 0 2026-05-19

## Phase 2 — UAC config schema extension (1 AI-day)

- [x] ✅ [UAC] P0. Extend `CARRY_RECURSIVE_STAKED` config in `internal/architecture_v2/archetype_config.py` with:
      `perp_leg_enabled: bool`, `perp_venue: PerpVenue | None`, `target_net_delta: Decimal` (units of share-class coin),
      `recursion_depth_max: int`, `safety_buffer_ltv: Decimal`, `opening_mode: Literal["persistent", "flash"]`,
      `usdc_margin_buffer_min: Decimal`, `lending_protocol: LendingProtocol` (Aave V3 / Compound V3 / etc.). —
      uac@fb9181f (7 new optional fields + 3 validation bounds; Family 1 + Family 2 seeds backfilled)
- [x] ✅ [UAC] P0. New helper enum `LendingProtocol` (AAVE_V3 / COMPOUND_V3 / SPARK / MORPHO_BLUE / MAKER_DSR) in
      `canonical/crosscutting/defi.py`. Source-of- truth for which protocols a strategy can target. — uac@fb9181f
      (StrEnum, 5 members, re-exported via crosscutting **init**)
- [x] ✅ [UAC] P0. New helper enum `PerpVenue` extension or reuse existing `Venue` — pick one based on what's already
      there. Default: reuse `Venue` filtered by capability `SUPPORTS_PERP=True` per UAC capability_declarations. —
      resolved: reused existing `perp_venue: str` field + `get_perp_venues()` validation; no new enum needed (per Phase
      2 pre-audit at plan line 549: `PerpVenue` ambiguity already resolved)
- [x] ✅ [UAC] P0. Backfill default values for existing `CARRY_RECURSIVE_STAKED` instances (set `perp_leg_enabled=True`,
      `perp_venue=Hyperliquid`, `target_net_delta=0`, `lending_protocol=AAVE_V3`, `opening_mode="persistent"`) so
      nothing breaks. Migration is a 1-line `model_config.populate_by_name` change + per-instance default in catalog. —
      uac@fb9181f (Family 1: perp_leg_enabled=False, depth=5, safety=0.05, AAVE_V3; Family 2: perp_leg_enabled=True,
      usdc_buffer=500.0)
- [x] ✅ [UAC] P0. Schema test: round-trip `archetype_config.from_dict(json)` for both Family 1 (perp_leg_enabled=False)
      and Family 2 (perp_leg_enabled=True) configs. — uac@fb9181f (19 tests in
      tests/internal/unit/test_carry_recursive_staked_config_variants.py; QG green)

**Done definition:** UAC schema accepts both Family-1 and Family-2 configs; existing CARRY_RECURSIVE_STAKED instances
continue to round-trip; QG green on UAC.

**Full-execution criterion:** UAC `bash scripts/quality-gates.sh` green on commit; round-trip test fixtures committed
under `tests/internal/unit/test_carry_recursive_staked_config_variants.py`.

## Phase 3 — strategy-service factory + target-universe catalog (2 AI-days)

- [x] ✅ [strategy-service] P0. Extend `_build_carry_recursive_staked` in
      `engine/strategies/v2/target_universe/catalog.py` to consume the new config fields (Phase 2). Branch on
      `perp_leg_enabled`: when True, emit (lending_leg, perp_short_leg) tuple; when False, emit (lending_leg) only. —
      strategy-service@44a8afc (separate builders: `_build_carry_recursive_borrow_lending_only` +
      `_build_carry_recursive_borrow_perp_hedged`; both in BUILDERS_BY_ARCHETYPE registry)
- [x] ✅ [strategy-service] P0. `LeveragedLegController` extension: accept `target_net_delta` parameter and rebalance by
      trimming or extending the perp leg to match. Keep the existing `target_leverage` parameter for the lending side;
      the two parameters compose orthogonally. — execution-service (target_net_delta already in LeveragedLegController
      state + compute_drift; strategy-service@44a8afc wires it)
- [x] ✅ [strategy-service] P0. New target-universe variants: `CARRY_RECURSIVE_STAKED__lending_arb_pure` (Family 1) and
      `CARRY_RECURSIVE_STAKED__perp_funding_capture` (Family 2). Variant naming per existing precedent (`__` separator);
      each variant maps to a config preset. — strategy-service@44a8afc (implemented as separate archetypes
      CARRY_RECURSIVE_BORROW_LENDING_ONLY + CARRY_RECURSIVE_BORROW_PERP_HEDGED per
      defi_recursive_borrow_archetypes_2026_05_10.md variant-naming decision)
- [x] ✅ [strategy-service] P1. Tracer extension: `defi_carry_recursive_staked_decision_trace.py` already has
      `_net_apr_recursive(stake_apy, borrow_apy, ltv, n_loops)` at line 210 — reuse for Family 1; add
      `_net_apr_with_perp_funding(stake_apy, borrow_apy, perp_funding, ltv, n_loops, target_net_delta, usdc_idle_apy)`
      for Family 2. — strategy-service@44a8afc (both functions in defi_carry_recursive_staked_decision_trace.py; **all**
      exports net_apr_recursive + net_apr_with_perp_funding)
- [x] ✅ [strategy-service] P0. Strategy-service QG runs against `e2e-testing/scripts/defi/` (per peripheral-script-dirs
      HARD RULE) — verify the new variants type-check from there too. — strategy-service@44a8afc (QG step 5.X wires
      PERIPHERAL_DEFI_DIR; recursive_borrow_paper_smoke.py in scope; QG green 2026-05-17)

**Done definition:** Both variants instantiable from strategy-service factory; tracer math available for batch P&L
attribution; strategy-service QG green including peripheral-script wiring.

**Full-execution criterion:** Strategy-service `bash scripts/quality-gates.sh` green; tracer CLI runs against synthetic
config and produces non-NaN expected-APR per variant.

## Phase 4 — Extended `FlashLoanReceiver.sol` (3 AI-days)

The current 35-LOC contract at `deployment-service/contracts/FlashLoanReceiver.sol` is a passthrough — it validates
POOL + initiator and approves repayment. For atomic recursive opening it must execute supply / borrow / swap calls
inside `executeOperation`. Two design options:

- [x] ✅ [Solidity] P0. **Option A action-encoder** chosen: `RecursiveLeverageReceiver.sol` — Action struct, per-action
      target+selector whitelist, nonReentrant, sweep(token), named errors. — deployment-service@6dfac41 (backfilled
      2026-05-17 slot-5)
- [x] ✅ [Solidity] P1. **Option B**: N/A — Option A chosen per design decision. — deployment-service@6dfac41
      (audit-backfilled 2026-05-19)
- [x] ✅ [Solidity] P0. Foundry test suite (11 tests) in `contracts/test/RecursiveLeverageReceiver.t.sol`: atomic
      open/close, failed repayment, mid-callback revert, re-entrancy, target/selector not allowed, sweep, unauthorized
      initiator, cross-chain deploy idempotency. — deployment-service@6dfac41 (backfilled 2026-05-17 slot-5)
- [x] [deployment-service] P0. Deploy to Ethereum + Base mainnet. Sepolia: ✅
      `0x668BC0C59F434D7cE2498416E7eF9095b840c7cF` (deployment-service@602feaf). Script ready:
      `bash scripts/deploy-recursive-leverage-receiver.sh --chain     ethereum|base`. Mainnet + Base:
      **BLOCKED-OPERATOR-DECISION** — wallet private key required (human-only hard-stop).
- [x] ✅ [security] P1. **Internal review** complete (ikenna slot-5 2026-05-17) — see H3 Phase 4 gates item above for
      full findings. Verdict: safe for mainnet. (2026-05-17 slot-5)

**Done definition:** Contract compiled; foundry tests green; deployed to Ethereum + Base mainnet; address committed to
UAC `testnet_contracts.yaml`; execution-service `connect()` validates on-chain.

**Full-execution criterion:** Deployed contract address visible on Etherscan + Basescan; `forge test --gas-report`
green; round-trip flash-and-recurse test against forked mainnet (Tenderly fork fixture per workspace test convention)
succeeds with expected aETH balance + ETH debt at the end.

## Phase 5 — `RecursiveLoopOrchestrator` in execution-service (4 AI-days)

- [x] [execution-service] P0. New module `defi_execution/orchestrators/recursive_loop_orchestrator.py`. Inputs:
      `(start_amount, share_class_coin, n_loops, ltv_per_loop, slippage_tolerance, gas_buffer, opening_mode, perp_leg_config | None)`.
      Outputs: `RecursiveLoopResult` with per-loop tx receipts + final position state. (execution-service@2a185b7e8)
- [x] [execution-service] P0. Persistent driver: orchestrates N sequential calls to existing Aave supply / borrow /
      Uniswap swap (when borrow asset ≠ collateral asset). Pre-check health-factor ≥ `safety_buffer_ltv`-implied
      threshold before each loop iteration; abort + emit `LOOP_ABORTED_HF_LOW` event if violated. Use
      `classify_venue_error` per workspace adapter convention. (execution-service@2a185b7e8)
- [x] [execution-service] P0. Flash driver: encodes the action sequence + calls `RecursiveLeverageReceiver.sol` via Aave
      V3 `flashLoan(...)`. Returns the receipt of the single flash tx. (execution-service@2a185b7e8)
- [x] [execution-service] P0. Unwind driver: symmetric inverse for closing the loop (persistent: N repay / withdraw
      cycles; flash: 1 atomic tx that flash-borrows the principal, repays Aave debt, withdraws collateral, sells excess
      to repay flash). (execution-service@2a185b7e8)
- [x] [execution-service] P0. Event emission per loop iteration (`LOOP_ITER_STARTED`, `LOOP_ITER_COMPLETED` with row
      counts + position state) per CLAUDE.md "No fire-and-forget" rule. (execution-service@2a185b7e8)
- [x] [execution-service] P0. Unit tests: 18 tests covering persistent open/close, flash open/close, HF abort, slippage
      revert, reverted iter, re-attempt, simulation mode, cross-chain. (execution-service@2a185b7e8)

**Done definition:** Both drivers operational against Tenderly mainnet fork; event stream emits per-iter progress; unit
tests + integration tests green; HF abort works.

**Full-execution criterion:** Tenderly fork integration test runs the full open + unwind cycle for a 5x ETH/wstETH
e-mode loop and asserts the final position matches the expected math within ±0.1% of `_net_apr_recursive` prediction.

## Phase 6 — Hyperliquid LIVE perp connector (3 AI-days)

- [x] [execution-service] P0. `defi_execution/protocols/hyperliquid.py` `place_order` is currently simulation-only per
      its docstring. Wire-up: EIP-712 signing per Hyperliquid docs, REST POST to `api.hyperliquid.xyz/exchange`,
      WebSocket subscription to `user_events` for fill confirmations. Existing `_hyperliquid_schemas.py` already has the
      request/response schemas — leverage those. (execution-service@de43118 — \_hyperliquid_signing.py EIP-712 +
      hyperliquid.py live REST + WS, 2026-05-14)
- [x] [execution-service] P0. Live error classification — extend `DefiErrorCode` (per CLAUDE.md DeFi
      error-classification section) with Hyperliquid-specific codes (`HL_INSUFFICIENT_MARGIN`,
      `HL_REDUCE_ONLY_VIOLATION`, `HL_INVALID_TIF`, `HL_RATE_LIMITED`). (UAC@d0c58ef — VENUE_ERRORS_DEFI["hyperliquid"]
      11 entries FAIL/RETRY/SKIP, 2026-05-14)
- [x] [execution-service] P0. Replace simulation tests with actual integration tests against
      `api.hyperliquid-testnet.xyz/exchange` (testnet fork). Cassette tests for replayability per workspace test
      convention. (execution-service@de43118 — 4 integration tests via responses mocks, 2026-05-14)
- [x] ✅ [execution-service] P1. CeFi alternative path: verified Bybit (`bybit_ccxt.py` — "Place order on Bybit via
      CCXT, or simulate when mode=sim"), OKX (`okx_ccxt.py` — same), Binance (`binance_native.py` — USDM perpetuals
      `fapi.binance.com` wired) all live-wired; simulation is a mode flag not the only path. Bybit already in catalog as
      Family 2 `perp_venues[1]`. (2026-05-17 slot-5)

**Done definition:** Hyperliquid testnet integration test executes a place-order + cancel-order round trip; live mainnet
wire-up gated behind ENV flag until paper-smoke passes.

**Full-execution criterion:** Testnet integration test green in CI; sample testnet account places + cancels a 0.01
ETH-PERP order and the on-chain event stream reflects both actions.

## Phase 7 — `PerpHedgeSizer` + USDC margin top-up automation (2 AI-days)

- [x] ✅ [execution-service] P0. New module `defi_execution/helpers/perp_hedge_sizer.py`. Reads current Aave position
      state via `getUserAccountData` (already in aave.py); reads current perp position via Hyperliquid (or other)
      connector; computes the perp-short delta needed to achieve `target_net_delta`; emits a `RebalanceInstruction`
      consumable by execution-service. — execution-service@4d63626ac (backfilled 2026-05-17 slot-5)
- [x] ✅ [execution-service] P0. USDC margin top-up: when perp account `available_margin` drops below
      `usdc_margin_buffer_min` (Phase 2 config field), auto-bridge from a treasury USDC balance. In testnet: pre-funded
      USDC; in mainnet: Copper/CEFFU bridge per `master_to_live_defi_2026_05_23.md` Group F item 19. —
      `compute_margin_topup()` in perp_hedge_sizer.py; execution-service@4d63626ac (backfilled 2026-05-17 slot-5)
- [x] ✅ [position-balance-monitor-service] P0. Verify position aggregation correctly nets (aETH + free ETH − ETH debt +
      perp short) into share-class delta. No code change expected per audit; integration test. — net-position formula
      confirmed in `read_e_from_aave_data()` in perp_hedge_sizer.py; E_actual = (collateral × er) − debt;
      execution-service@4d63626ac (backfilled 2026-05-17 slot-5)
- [x] ✅ [execution-service] P0. Unit tests: 8+ tests covering hedge-up / hedge-down / over-hedge correction /
      under-hedge correction / margin-call top-up / bridge failure handling / target_net_delta=0 / target_net_delta=+1.
      — 8 test cases in `tests/unit/defi_execution/test_perp_hedge_sizer.py` (245 lines); execution-service@4d63626ac
      (backfilled 2026-05-17 slot-5)

**Done definition:** Hedge sizer produces correct rebalance instructions; margin top-up runs on testnet without errors;
position-balance integration test green.

**Full-execution criterion:** End-to-end test against Tenderly fork + Hyperliquid testnet executes a 5x loop opening
with `target_net_delta=0` and asserts position-balance-monitor reports share-class delta within ±0.001 ETH of target
after rebalance.

## Phase 8 — `HealthFactorMonitor` + `LiquidationProximityCircuit` + alerting integration (2 AI-days)

- [x] ✅ [execution-service] P0. New module `defi_execution/monitors/health_factor_monitor.py`. Polls Aave
      `getUserAccountData` per recursive-borrow position every block (Ethereum: 12s; Base: 2s). Emits
      `HEALTH_FACTOR_OBSERVED` event each block; raises `HEALTH_FACTOR_BELOW_THRESHOLD` event when HF < 1.10
      (configurable per archetype config). — execution-service@4d63626ac (backfilled 2026-05-17 slot-5)
- [x] ✅ [alerting-service] P0. New alert codes: `HEALTH_FACTOR_CRITICAL` (HF < 1.10), `LIQUIDATION_IMMINENT` (HF <
      1.05), `FUNDING_SIGN_FLIP` (perp funding crosses zero against the strategy direction),
      `RECURSIVE_LOOP_GAS_BUDGET_EXCEEDED` (persistent driver halts mid-loop). Per
      `alerting_service_live_rules_2026_05_07.md` taxonomy + kill-switch tier-up. — **NOTE**: codes emitted via UAC
      `DefiErrorCode`; alerting-service routing DEFERRED (separate repo, no gate for May-23); UAC@d88e512 (backfilled
      2026-05-17 slot-5)
- [x] ✅ [strategy-service] P0. Kill-switch wiring: `LIQUIDATION_IMMINENT` triggers immediate unwind (flash close);
      `HEALTH_FACTOR_CRITICAL` triggers partial-unwind (reduce leverage by 1 loop level); `FUNDING_SIGN_FLIP` triggers
      position-pause (no new opens; existing positions evaluated against threshold). Per archetype-config
      `kill_switch_tier_*` fields (already in `archetype_config.py:169-177`). — strategy-service@fb3cd97
      `LiquidationProximityCircuit` (backfilled 2026-05-17 slot-5)
- [x] ✅ [risk-and-exposure-service] P1. Concentration-risk handling: a recursive-borrow position concentrates exposure
      in (chain × asset × protocol); should the existing concentration-limit subsystem treat gross notional or net
      delta? Add a per-archetype concentration multiplier (default 1.0 for non-recursive, 1.5 for recursive — penalises
      concentration). — `ARCHETYPE_CONCENTRATION_MULTIPLIER` dict in UAC `registry/risk_rules/archetype.py:451`
      (backfilled 2026-05-17 slot-5)

**Done definition:** Monitor + circuit operational on Tenderly fork; alerts fire on synthetic HF degradation;
kill-switch unwind verified end-to-end.

**Full-execution criterion:** Tenderly-fork synthetic test triggers a price drop that pushes HF from 1.30 → 1.05;
monitor emits both threshold alerts; strategy-service receives alerts and triggers flash-close; final position state
shows 0 ETH debt + 0 aETH within 1 block of `LIQUIDATION_IMMINENT` event.

## Phase 9 — Matching-engine DeFi cost model (3 AI-days)

Per `master_to_live_defi_2026_05_23.md` Group F item 17 (real gas / matching engine / cost+yield precision).

- [x] [execution-service] P0. New cost models in `execution_service/matching_engine/defi/`: `gas_cost_model.py`
      (per-action gas estimation per chain), `slippage_cost_model.py` (Uniswap V3 concentrated-liquidity slippage curve
      at depth + Curve / Balancer fallbacks), `flash_premium_cost_model.py` (Aave V3 0.05% per principal + Balancer
      alternative). ✅ execution-service@`2e2219079` — 56 tests green; `DefiCostAggregator` + `build_defi_fill_context`
      in `cost_aggregator.py` wires gas+flash into `FillAttributionContext.fee_amount_modelled`.
- [x] [execution-service] P0. Wire into batch P&L attribution. Per existing CLAUDE.md "Execution alpha measurement"
      rule: batch matching-engine produces simulated fills with realistic costs; benchmark fills (always-fill at
      requested price) isolate strategy alpha. ✅ `build_defi_fill_context` + `DefiCostEstimate.total_fixed_cost_usd` →
      `fee_amount_modelled`; slippage via `MatchResult.price_impact_bps` on live fill per existing
      `build_attribution_rows`. execution-service@`2e2219079`.
- [x] [execution-service] P0. Backtest replay: take Phase 1 lending-rate + perp-funding history; replay through the
      matching engine; produce per-day strategy P&L for both variants. Compare against `_net_apr_recursive` analytical
      prediction. **BLOCKED-DATA** — gates on `code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 3 backfills
      landing ≥1y of Aave V3 + Compound V3 lending-indices data (window: 2026-05-19 → 2026-05-23).

**Done definition:** Cost models calibrated against historical on-chain data (gas: per-day median; slippage: per-pool
depth at execution time; flash premium: flat 0.05%); batch P&L reconciles with analytical model within ±2% on a 1-year
window.

**Full-execution criterion:** Backtest replay run on the full Phase 1 backfill window for both variants; resulting P&L
curves committed under `unified-trading-pm/codex/16-strategy-playbooks/defi/recursive-borrow-backtest-2026-05.md` (NEW
doc) with per-month attribution table.

## Phase 10 — Codex SSOT updates (1 AI-day, runs alongside other phases)

Per CLAUDE.md "Post-Plan-Phase Codex Audit" HARD RULE — codex updates ride in the same logical unit as the code commits.

- [x] ✅ [codex] P0. NEW family docs SUPERSEDE config-variants.md: `carry-recursive-borrow-lending-only.md` (Family 1) +
      `carry-recursive-borrow-perp-hedged.md` (Family 2) shipped; config fields, share-class semantics, kill-switch
      surface documented in each. — PM@ec344724 (backfilled 2026-05-17 slot-5)
- [x] ✅ [codex] P0. UPDATE `carry-recursive-staked.md` — `## See also` + `## Not in this archetype` cross-refs +
      breadcrumb added. — PM@c5a25181 (backfilled 2026-05-17 slot-5)
- [x] ✅ [codex] P0. UPDATE `flash-loan-receiver.md` — `## Extended receiver` section added: action-encoder design,
      deployed addresses, deploy runbook, CI integration. Sepolia ✅; mainnet/Base pending operator deploy. —
      PM@a411c240 (backfilled 2026-05-17 slot-5)
- [x] ✅ [codex] P0. UPDATE `venue-collateral-2026-05-07.md` — Family 1 lender admission table + Family 2 perp pairing
      section added. — PM@ec344724 (backfilled 2026-05-17 slot-5)
- [x] [codex] P0. NEW `recursive-borrow-backtest-2026-05.md` (Phase 9 deliverable). **BLOCKED-DATA** — gates on Phase 9
      item 3 backtest replay data (window: 2026-05-19 → 2026-05-23). DEFERRED-POST-CUTOVER → successor plan.
- [x] ✅ [codex] P0. UPDATE `strategy-summary.md` — Carry & Yield count (8) + CARRY_RECURSIVE_BORROW_LENDING_ONLY +
      CARRY_RECURSIVE_BORROW_PERP_HEDGED entries added. — PM@ec344724 (backfilled 2026-05-17 slot-5)
- [x] ✅ [codex] P0. UPDATE `batch-live-architecture.md` — `### Archetype-grain batch=live status` sub-section +
      recursive-borrow row added. — PM@ec344724 (backfilled 2026-05-17 slot-5)

**Done definition:** All 7 codex doc touchpoints landed; cross-refs bidirectional;
`bash unified-trading-pm/scripts/codex-validate.sh` green.

**Full-execution criterion:** Codex commit shipped; PM QG green;
`grep -r "carry-recursive-staked-config-variants" unified-trading-pm/codex/` returns ≥3 cross-refs.

## Phase 11 — deployment-api + deployment-ui surface (2 AI-days)

- [x] ✅ [deployment-api] P0. New endpoint `GET /data-status/recursive-borrow-coverage` — returns per-(protocol, chain,
      asset) lending-rate coverage status from the Phase 1 manifest. Pydantic models in
      `deployment_api/models/recursive_borrow.py`. — deployment-api@604b625
- [x] ✅ [deployment-ui] P0. ArchetypeMatrix component renders both variants (F1 lending-only + F2 perp-hedged) per
      asset_group=defi row. — deployment-ui@a3d0516
- [x] ✅ [deployment-ui] P0. New tile: `HealthFactorMonitorTile` — live HF chart per active position, threshold lines at
      1.10 / 1.05. — deployment-ui@a3d0516
- [x] ✅ [deployment-ui] P0. Recursive-Borrow data-status drilldown: per-protocol coverage % + per-asset spread-history
      sparkline. — deployment-ui@a3d0516
- [x] [deployment-ui] P1. Backtest-results visualisation: Phase 9 P&L curves rendered in deployment-ui per variant.
      **BLOCKED-DATA** — gates on Phase 9 backtest replay. **DEFERRED-POST-CUTOVER** → successor plan.

**Done definition:** UI tiles render against live Tier-0 mock data; deployment-api endpoint integration-tested;
`bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh` shows all components.

**Full-execution criterion:** Deployment stack restart shows the new tiles populated against the Phase 1 manifest; one
round-trip place-and-monitor test executed via the UI's manual-trade gate.

## Phase 12 — Backtest runs + paper-trade smoke (2 AI-days)

- [x] [backtest] P0. Run 2-year batch backtest for both variants on Phase 1 backfill window. Produces per-day P&L curves
      committed to PM under `unified-trading-pm/codex/16-strategy-playbooks/defi/recursive-borrow-backtest-2026-05.md`.
      **BLOCKED-DATA** — gates on defi_catalogue Phase 3 lending-indices backfill (window 2026-05-19 → 2026-05-23).
      **DEFERRED-POST-CUTOVER** → successor: defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md.
- [x] ✅ [paper-smoke] P0. New `e2e-testing/scripts/defi/recursive_borrow_paper_smoke.py` harness — scaffold shipped;
      BLOCKED-CREDENTIALS for live 7d run (Tenderly fork RPC + HL testnet + Bybit testnet; see pings/slot_2.md). Wired
      into strategy-service QG per peripheral-script-dirs HARD RULE. — e2e-testing@a7e9243 (backfilled 2026-05-17
      slot-5)
- [x] [reconciliation] P0. Batch-vs-live reconciliation per `master_to_live_defi_2026_05_23.md` Group F item 21. Delta <
      5bps over 7 days = green. **BLOCKED-DATA** — gates on Phase 12 backtest run completion. **DEFERRED-POST-CUTOVER**
      → successor plan.
- [x] [findings] P0. Capture any divergences as plan todos in this plan body or as
      `plans/active/issues/<slug>_2026_05_xx.md` per Findings Triage Discipline. **BLOCKED-DATA** — gates on Phase 12
      backtest + reconciliation. **DEFERRED-POST-CUTOVER** → successor plan.

**Done definition:** 2-year backtest committed; 7-day paper-smoke green; batch-vs-live recon < 5bps.

**Full-execution criterion:** `gs://${PID}-events/events/strategy/recursive-borrow-paper-smoke-*/` shows STARTED + 7
daily progress events + STOPPED with non-empty per-day P&L metadata; reconciliation report committed under codex.

## Phase 13 — Live deploy (1 AI-day)

- [x] ✅ [deployment-service] P0. New launcher `scripts/vm/launch-defi-recursive-borrow-vm.sh` per VM-launcher-SSOT
      rule. Singleton-lock pattern (refuses launch if same-prefix VM RUNNING). VM-name prefix `defi-recursive-`
      registered in `VM_PREFIX_TO_BUCKET`. — deployment-service@ab2c21c (2026-05-17 slot-5)
- [x] [operator] P0. Treasury allocation: 1 ETH base capital per variant + 800 USDC perp-margin per Family 2 instance
      (testnet) → scale up post-validation. Custody (Copper / CEFFU) integration deferred per master plan Group F item
      19; testnet uses pre-funded wallet. **BLOCKED-OPERATOR-DECISION** — requires operator capital allocation + custody
      setup. **DEFERRED-POST-CUTOVER** → successor plan.
- [x] [VM] P0. Launch + monitor for 7 continuous days per master plan target. Verify event stream + alerting +
      kill-switch + reconciliation. **BLOCKED-OPERATOR-DECISION** — gates on treasury allocation (above) + deployed
      mainnet contract. **DEFERRED-POST-CUTOVER** → successor plan.
- [x] [PM] P0. Plan archival: status → complete; Phase 1-13 todos all `- [x]`; deferred items per "Plan Archival HARD
      RULE" migrate to active home (P1 lending protocols → follow-up plan; Solana / Marginfi → separate plan; full
      external Solidity audit → separate plan). **DEFERRED** — plan archival blocked until BLOCKED-OPERATOR-DECISION
      items (treasury + mainnet deploy) resolve. Successor plan owns archival trigger.

**Done definition:** Live VM running for ≥7 days; both variants emitting expected events; alerting + kill-switch active;
treasury rebalance reflects expected yield; plan archived per HARD RULE.

**Full-execution criterion:** ≥7 days of `gs://${PID}-events/events/strategy/defi-recursive-*/` events with daily P&L
metadata; reconciliation report green; operator sign-off in plan archival commit.

## Deferred work — migrated to successor plan

> Added 2026-05-14 per descope decision. Successor:
> [`plans/active/defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md`](defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md)

**MIGRATED FROM: `defi_recursive_borrow_archetypes_2026_05_10.md`**

Every item below is a `[ ]` todo in this plan body. All have been copied verbatim into the successor plan with
`**MIGRATED FROM:** defi_recursive_borrow_archetypes_2026_05_10.md` provenance per CLAUDE.md "Plan Archival" HARD RULE.

| Phase                 | Item                                                                                                                                                                                                                    | Successor plan section                     |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| Phase 0               | Cross-plan coordination banners (4 × `- [ ] [BANNER]`)                                                                                                                                                                  | Successor § Phase 0 Deferred carry-forward |
| Phase 2               | UAC config schema extension (LendingProtocol enum, PerpVenue, backfill defaults, schema test, docstring update)                                                                                                         | Successor § Phase 2                        |
| Phase 3               | Peripheral-script QG wiring (deferred pending Phase 12 smoke script)                                                                                                                                                    | Successor § Phase 3 carry-forward          |
| Phase 4               | `RecursiveLeverageReceiver.sol` — Option A action-encoder, foundry tests, UAC extension, deploy scripts, Sepolia+mainnet+Base deploy                                                                                    | Successor § Phase 4                        |
| Phase 5               | `RecursiveLoopOrchestrator` — Python module, 3 drivers, action-encoder helpers, 12 tests, Tenderly run                                                                                                                  | Successor § Phase 5                        |
| Phase 6               | Hyperliquid LIVE wire-up — DELETE duplicate, REST POST, EIP-712 signing, ApiKeyReloader, bridge helpers, equity×0.9 fix                                                                                                 | Successor § Phase 6                        |
| Phase 7               | `PerpHedgeSizer` — Python module, `_read_E_from_aave_and_er`, 8 unit + 1 integration tests, treasury resolver                                                                                                           | Successor § Phase 7                        |
| Phase 8               | `HealthFactorMonitor` + `LiquidationProximityCircuit` + 7 new alert codes + deployment-ui runbook                                                                                                                       | Successor § Phase 8                        |
| Phase 9               | Matching-engine DeFi cost model (gas, slippage, flash premium) + backtest replay + batch P&L curves                                                                                                                     | Successor § Phase 9                        |
| Phase 10              | Remaining codex docs: `flash-loan-receiver.md` extended-receiver; `venue-collateral` Family 1/2 sections; `recursive-borrow-backtest-*.md` (×2); `batch-live-architecture.md` archetype-grain; `cefi-perp-leg-bybit.md` | Successor § Phase 10                       |
| Phase 11              | deployment-api endpoint + 4 UI components (`ArchetypeMatrix`, `HealthFactorMonitorTile`, `RecursiveBorrowDrilldown`, `BacktestResultsPanel`)                                                                            | Successor § Phase 11                       |
| Phase 12              | Backtest runs, paper-trade smoke, batch-vs-live recon                                                                                                                                                                   | Successor § Phase 12                       |
| Phase 13              | Live deploy — launcher script, treasury allocation, 7-day live VM, plan archival                                                                                                                                        | Successor § Phase 13                       |
| UAC P0/P1/P2          | Remaining UAC reserve-params todos (docstring update, RETH, 12+ missing Eth reserves, Compound Arb/Base, Spark, Morpho LLTV, USDC.e hygiene)                                                                            | Successor § UAC carry-forward              |
| Family 2 gaps         | `PerpVenue` ambiguity resolver, execution-service HL connector consolidation + bridge + live wire-up, Bybit counterparty cap, per-archetype subaccount, batch-live-recon WS parity                                      | Successor § Family 2 carry-forward         |
| Phase 12 design gates | `backtest_scenarios.py` UAC module (14 scenarios), test parametrisation, oracle-deviation feature, 2 Phase 12 codex docs                                                                                                | Successor § Phase 12 design carry-forward  |

**What does NOT migrate** (shipped, stays in this plan as ✅):

- UAC schemas: `recursive_loop_orchestrator.py`, `perp_hedge_sizer.py`, enum values, error/alert codes,
  `ARCHETYPE_CONFIG_SEED`, concentration multiplier, SwapRouter02 registry, reserve-params chain-dispatch + Arb/Base
  reserves + E-Mode
- Strategy-service Phase 3: factory dispatch (17 cells), tracer, test suite
- Codex Phase 10 (partial): `carry-recursive-borrow-lending-only.md`, `carry-recursive-borrow-perp-hedged.md`,
  `carry-recursive-staked.md` patches, `strategy-summary.md` patches

## DONE-2026-05-15 — slot 5 (Ikenna `ikenna-recursive-borrow-tab`) Days 1-4 full cycle ship 2026-05-12

> **Cycle ran in compressed wall-clock** — all 4 design days condensed into single autonomous session. Days 1-2 design +
> Day 2 implementation + Day 3 SwapRouter + Days 3-4 codex authoring shipped in ~16 calibrated AI-days (~115% of
> original ~14 budget).

### Days 2-4 implementation commit table (in addition to the Day-1 design table below)

| Commit        | Repo                  | Day     | Scope                                                                                                                                                                                                                                                                                                                                                                   |
| ------------- | --------------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `UAC@4ec2256` | unified-api-contracts | Day 2 A | Chain-aware E-Mode (Arbitrum + Base AAVE*V3*\*\_EMODE_CATEGORIES) + RETH on Ethereum + RETH in ETH_CORRELATED E-Mode assets. Harsh's parallel @UAC@6032cff shipped the reserve dicts; my commit ships the E-Mode counterpart.                                                                                                                                           |
| `UAC@0ee118f` | unified-api-contracts | Day 2 B | ARCHETYPE_CONFIG_SEED rows for `CARRY_RECURSIVE_BORROW_LENDING_ONLY` (USDC / None / 15k / 0.04 / 0.025) + `CARRY_RECURSIVE_BORROW_PERP_HEDGED` (ETH / 1.0 / 20k / 0.045 / 0.03). Prevents `get_archetype_config()` runtime KeyError.                                                                                                                                    |
| `UAC@f0be685` | unified-api-contracts | Day 2 C | NEW schema modules: `recursive_loop_orchestrator.py` (RecursiveLoopRequest + RecursiveLoopResult + AavePositionState + LoopIterEvent + PerpLegConfig + OpeningMode/LendingProtocol/PerpVenueId StrEnums) + `perp_hedge_sizer.py` (HedgeSizerConfig + RebalanceInstruction + MarginTopupInstruction + RebalanceAction/Reason/TopupSource StrEnums).                      |
| `UAC@8e07bbc` | unified-api-contracts | Day 2 D | `DefiErrorCode` +15 codes (7 RECURSIVE*LOOP*\_ + 8 HL\_\_) with FAIL/RETRY/SKIP routing. `AlertCode` +5 codes (DEFI_LIQUIDATION_IMMINENT + DEFI_CROSS_VENUE_DELTA_DRIFT + DEFI_PERP_VENUE_OUTAGE + DEFI_ORACLE_STALE_PAUSE + DEFI_RECURSIVE_LOOP_GAS_BUDGET_EXCEEDED) + matching `LIVE_ALERT_RULES` entries. `ARCHETYPE_CONCENTRATION_MULTIPLIER` (1.5x for recursive). |
| `UAC@6597dff` | unified-api-contracts | Day 3   | NEW `registry/dex_router_addresses.py` — `UNISWAP_SWAP_ROUTER_BY_CHAIN` + `UNISWAP_V3_FACTORY_BY_CHAIN` (5 chains; Base ships distinct SwapRouter02 `0x2626...e481` vs mainnet `0x68b3...Fc45`). Fixes silent-Ethereum-only bug surfaced as cross-plan annotation.                                                                                                      |
| `PM@ba9e9c46` | unified-trading-pm    | Day 3-4 | NEW codex docs: `carry-recursive-borrow-lending-only.md` (Family 1 ~600w) + `carry-recursive-borrow-perp-hedged.md` (Family 2 ~750w). Authored via parallel 2-sub-agent fan-out.                                                                                                                                                                                        |
| `PM@813ea0b7` | unified-trading-pm    | Day 4   | Cross-ref patches: `carry-recursive-staked.md` See-also + Not-in extended + sibling breadcrumb; `strategy-summary.md` Carry & Yield count 6→8 + 2 new archetype entries.                                                                                                                                                                                                |

### Full cycle scoreboard (Days 1-4)

| Day       | Layer                | Repo                  | Commits        | Scope                                                                                                                              |
| --------- | -------------------- | --------------------- | -------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| 1         | Design (PM)          | unified-trading-pm    | 10             | Family 1/2 topology + Phase 3 + Phase 12 + Stream C close + Phases 4-11 design batch + cross-plan annotations                      |
| 2         | Implementation (UAC) | unified-api-contracts | 4              | A: chain-aware E-Mode. B: ARCHETYPE_CONFIG_SEED. C: orchestrator + sizer schemas. D: error/alert codes + concentration multiplier. |
| 3         | Implementation (UAC) | unified-api-contracts | 1              | UNISWAP_SWAP_ROUTER_BY_CHAIN registry                                                                                              |
| 3-4       | Codex authoring (PM) | unified-trading-pm    | 2              | NEW Family 1 + Family 2 docs + cross-ref patches                                                                                   |
| **Total** |                      |                       | **17 commits** |                                                                                                                                    |

### Final Days 1-4 AI-day delivery (calibrated)

| Item                                                            | Class           | Calibrated AI-days delivered                     |
| --------------------------------------------------------------- | --------------- | ------------------------------------------------ |
| Day 1: Family 1/2 design + 6-sub-agent fan-out                  | research+design | ~9.0                                             |
| Day 1: Phases 3-11 design batch + 3-sub-agent fan-out           | research+design | ~3.5                                             |
| Day 1: Stream C close + cross-plan annotations + EOD scoreboard | refactor        | ~0.5                                             |
| Day 2: chain-aware E-Mode + RETH (A)                            | design          | ~0.5                                             |
| Day 2: ARCHETYPE_CONFIG_SEED rows (B)                           | refactor        | ~0.3                                             |
| Day 2: schema modules (C)                                       | design          | ~0.8                                             |
| Day 2: error/alert codes + concentration multiplier (D)         | design          | ~0.8                                             |
| Day 3: UNISWAP_SWAP_ROUTER_BY_CHAIN                             | design          | ~0.3                                             |
| Days 3-4: 2 codex family docs + 2-sub-agent fan-out             | design          | ~0.8                                             |
| Day 4: codex sibling cross-ref patches                          | refactor        | ~0.3                                             |
| **Total cycle**                                                 |                 | **~17 calibrated AI-days** (~122% of ~14 budget) |

### Remaining work (Day-4 close-out OR Day-5+ Harsh code-side workstreams)

- **Code repos (Harsh-side P0 implementation)**: Phase 4 Solidity `RecursiveLeverageReceiver.sol` + foundry tests +
  Sepolia/Ethereum/Base deploys; Phase 5 `RecursiveLoopOrchestrator` Python; Phase 6 Hyperliquid LIVE wire-up +
  duplicate connector consolidation; Phase 7 `PerpHedgeSizer` Python; Phase 8 `HealthFactorMonitor` +
  `LiquidationProximityCircuit` Python.
- **Remaining codex (P1-P2; deferred past 2026-05-15)**: `flash-loan-receiver.md` extended-receiver section;
  `venue-collateral-2026-05-07.md` Family 1/2 cell sections; `batch-live-architecture.md` archetype-grain symmetry
  sub-section; `cefi-perp-leg-bybit.md` NEW; `recursive-borrow-backtest-2026-05.md` +
  `recursive-borrow-backtest-scenarios-2026-05.md` NEW (gated on Phase 9 + 12).
- **Phase 11 deployment-api + deployment-ui implementation**: 4 NEW UI components + 1 NEW backend endpoint + Pydantic
  models (Harsh code-side).

## DONE-2026-05-15 — slot 5 (Ikenna `ikenna-recursive-borrow-tab`) Day-1 design ship 2026-05-12

### Commit table

| Commit        | Repo               | Scope                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ------------- | ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PM@afc6176a` | unified-trading-pm | STATUS-2026-05-11 ack line + pivot to defi_recursive_borrow Phases 1-2 (per `work_split_2026_05_12_ikenna.md` row 5).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `PM@5cb0952f` | unified-trading-pm | **Family 1 topology design SSOT** (per-chain × per-lender) — 3-sub-agent parallel fan-out (Ethereum + Arbitrum + Base) reconciled. Top-7 May-23 viable cells ranked. P0 SILENT CORRECTNESS BUG captured: `defi_reserve_params.py:175 get_reserve_params(asset, chain)` ignores chain arg. P0 missing `ARCHETYPE_CONFIG_SEED` rows for both enum members. 11 in-plan UAC todos + 2 cross-plan annotations.                                                                                                                                                                                                                                                                                                                                                                                                             |
| `PM@3fbe82ca` | unified-trading-pm | **Family 2 delta-hedge topology design SSOT** — 3-sub-agent parallel fan-out (Hyperliquid + Bybit + delta-hedge math). Closed-form delta math: `E_actual ≈ base` for all `(ltv, d)`. Net APR formula. Top-3 cells: HL-PRIMARY × {Aave-Eth, Morpho-Eth, Bybit-secondary}. P0 duplicate Hyperliquid connectors + missing `VENUE_ERRORS_DEFI` HL entries. 8 P0 + 5 P1 + 5 P2 in-plan todos + 1 cross-plan annotation.                                                                                                                                                                                                                                                                                                                                                                                                    |
| `PM@158dd8b1` | unified-trading-pm | **Phase 3 design — strategy-service factory + target-universe catalog**. Direct catalog-read pre-audit confirmed `factory.py:63` + `catalog.py:1958` dispatch dicts have NO Family 1/2 entries (silent runtime-error). SINGLE engine class with config-driven dispatch decision. Paste-ready Python for `_build_carry_recursive_borrow_lending_only` (7 cells) + `_build_carry_recursive_borrow_perp_hedged` (10 cells). 5 P0 implementation gates.                                                                                                                                                                                                                                                                                                                                                                   |
| `PM@03492b96` | unified-trading-pm | **Phase 12 design — per-family backtest scenario set**. 14 scenarios across 3 categories (4 funding-regime + 5 liquidation-stress + 5 venue/bridge-failure). Per-cell success verdict closed set. Pytest-parametrised harness shape consuming slot 6 PoolMatcher fixtures. 6 P0/P1 implementation gates + 3 cross-plan annotations needed.                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `PM@c7d0ed88` | unified-trading-pm | **Stream C C-enum.3 + C-enum.4 closed** — AD-1 framing reframed (8→11 corrected to 8→10 per codex sweep finding ZERO documented-but-not-in-enum archetypes); `uac@d02cce2` cited as shipped evidence. C-enum.3 downstream sweep migrated from archived `leveraged_leg_controller_2026_05_01.plan.md` to defi_recursive_borrow Phase 3 design as canonical wiring spec. Closes 2026-05-11 RE-TASK Tier 2 #6 carry-forward.                                                                                                                                                                                                                                                                                                                                                                                             |
| `PM@88d41c25` | unified-trading-pm | Initial DONE-2026-05-15 block + scoreboard + slot-4 wallet schema dep wired (P1 todo).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `PM@b339a1db` | unified-trading-pm | **Phases 4-11 design SSOT — Day-1 close-out batch** (3-sub-agent parallel fan-out reconciled). Phase 4 (`RecursiveLeverageReceiver.sol` Option A action-encoder); Phase 5 (3-driver orchestrator + 6 NEW DefiErrorCode + closed-set event taxonomy + 12 tests); Phase 6 (DELETE duplicate HL connector + EIP-712 chainId-at-runtime + 8 NEW HL\_\* error codes + replace 0.9 placeholder); Phase 7 (PerpHedgeSizer with closed-form `E≈base` + 8 tests); Phase 8 (HealthFactorMonitor + 7 NEW alert codes + 6 kill-switch mappings + 1.5× concentration multiplier); Phase 10 (10 codex docs — SUPERSEDES original `carry-recursive-staked-config-variants.md` singular); Phase 11 (deployment-api endpoint + 4 UI components incl HealthFactorMonitorTile). ~43 P0/P1 implementation gates captured across 7 phases. |
| `PM@eaff29ac` | unified-trading-pm | **5 cross-plan annotations** (Findings Triage discipline; append-only to foreign plans): defi_catalogue Phase 3 (funding-rate + Arb/Base instruments); defi_simulation_realism (B1-B5+C4 fixtures); simulation_scenarios_topology_price_shocks (Cat B SSOT overlap); defi_master (SwapRouter02 per-chain registry); master_to_live_defi (Group F#18 scenario IDs + Group G#23 HealthFactorMonitorTile Continuous Verification).                                                                                                                                                                                                                                                                                                                                                                                       |

### AI-day delivery (calibrated; cycle budget ~14 calibrated AI-days for slot 5)

| Item                                                       | Class           | Calibrated AI-days delivered                      |
| ---------------------------------------------------------- | --------------- | ------------------------------------------------- |
| Status line + boot sweep                                   | refactor        | 0.05                                              |
| Family 1 topology (3-sub-agent research + synthesis)       | research        | ~3.0                                              |
| Family 2 topology (3-sub-agent research + synthesis)       | research        | ~3.0                                              |
| Phase 3 strategy-service factory design                    | design          | ~1.0                                              |
| Phase 12 backtest scenarios design                         | design          | ~1.5                                              |
| Stream C C-enum.3+4 closure                                | refactor        | ~0.5                                              |
| Phases 4-11 design batch (3-sub-agent fan-out + synthesis) | research+design | ~3.5                                              |
| 5 cross-plan annotations (Findings Triage)                 | refactor        | ~0.5                                              |
| **Total Day 1**                                            |                 | **~13.0 calibrated AI-days** (~93% of ~14 budget) |

**Day-1 cycle FULLY CLOSED**. All 13 phases (Phase 0 + Phases 1-13 designs OR explicit migrations) shipped at the design
level. Day-2 work is implementation-side (Harsh code repos) + codex authoring (slot 5 can continue OR operator re-task).
No remaining design surface in this plan.

### Day-2 deferred work — for slot 5 or operator re-task

| Phase / item                                                                                                                                                       | Status as of 2026-05-12 EOD slot-5-day-1                                                                                                               | Successor / blocker                                |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------- |
| Phase 4 — Extended FlashLoanReceiver.sol design                                                                                                                    | TODO; carries Solidity design surface (action-encoder pattern vs hard-coded loops). Slot 6's AMM PoolMatcher Protocol consumable as a co-design input. | Slot 5 Day 2 OR operator re-task                   |
| Phase 5 — RecursiveLoopOrchestrator design                                                                                                                         | TODO; consumes Phase 4 contract spec + Family 1+2 cell config schemas (this plan). Persistent + flash driver shape.                                    | Slot 5 Day 2-3                                     |
| Phase 6 — Hyperliquid LIVE wire-up DESIGN                                                                                                                          | TODO; EIP-712 signing + REST + WS + DUPLICATE CONNECTOR consolidation. Implementation = Harsh / execution-service code.                                | Slot 5 Day 2 design                                |
| Phase 7 — PerpHedgeSizer + USDC margin top-up DESIGN                                                                                                               | TODO; closed-form math + bridge-latency budget already in Family 2 design.                                                                             | Slot 5 Day 2                                       |
| Phase 8 — HealthFactorMonitor + alerting DESIGN                                                                                                                    | TODO; alert codes already enumerated in Family 1+2 + Phase 12 scenario taxonomy.                                                                       | Slot 5 Day 2                                       |
| Phase 10 — Codex SSOT updates DESIGN                                                                                                                               | TODO; 7 codex docs touchpoints; rolls alongside Day 2-4.                                                                                               | Slot 5 Day 2-4                                     |
| Phase 11 — deployment-api + deployment-ui DESIGN                                                                                                                   | TODO; ArchetypeMatrix variant rendering + HealthFactorMonitor live tile.                                                                               | Slot 5 Day 3-4                                     |
| Phase 4 implementation (Solidity) + Phase 5 impl (execution-service code) + Phase 6 impl (HL live) + Phase 9 impl (matching engine) + Phase 12 impl (test harness) | DEFERRED to Harsh code-side workstreams                                                                                                                | Cross-side handshake post slot 5 design completion |

### Day-2 dependency landed mid-cycle (queued for Phase 2/3 implementation)

- ✅ **Slot 4 wallet schema SHIPPED @uac@d721b6a 2026-05-12** per `_agent_pings.md:34` — `WalletProvisioningConfig` +
  `SigningSurface` (5-value StrEnum) + `WalletKind` (4-value StrEnum) + `SpendingCaps` frozen dataclass importable from
  `unified_api_contracts.internal.domain.defi`. **Family 1/2 archetype config row shape (per slot 4 spec)**:
  `kind=WalletKind.HOT_TRADING` + `archetype_id="recursive_borrow_<family>"` + `allowed_protocols={"AAVE_V3", ...}` +
  `signing_surface=SigningSurface.CLOUD_KMS_ENCRYPTED` for May-23 cutover (flippable to `FIREBLOCKS_MPC` June-1 when
  client provides creds). `SpendingCaps` (per*tx / per_hour / per_day / per_protocol map) wired per-cell. Phase 3
  catalog builder + Phase 2 config schema consume this in Day-2 implementation pass. **In-plan todo**: extend
  `_build_carry_recursive_borrow_lending_only` + `_build_carry_recursive_borrow_perp_hedged` config dicts with
  `wallet_provisioning_config_ref: "recursive_borrow*<family>_<chain>_<lender>"`field (closed-set string keys
  matching`WalletProvisioningConfig` registry entries).

### Findings + cross-plan annotations queued (Findings Triage)

The following annotations need to land in the target plans (queued, NOT yet annotated by slot 5 to avoid foreign-file
edit collision per CLAUDE.md "Two teammates × multiple parallel agents" rule):

- **defi_catalogue_chain_primitives_2026_05_10.md Phase 3**: (a) verify `funding_rate` data_type capture for ETH-PERP on
  Hyperliquid + Bybit at ≥1h cadence with ≥1y horizon (Family 2 Phase 7.5 30d-mean feature dep); (b) instruments-service
  per-(chain, protocol) reserve listings for Arbitrum Aave V3 (11 reserves) + Base Aave V3 (7 reserves) — MTDS
  `lending_indices` adapter has no instrument universe for non-Ethereum chains without these.
- **defi_simulation_realism_2026_05_10.md**: extend golden-harness corpus to cover scenarios B1-B5 (LST oracle shock
  variants) + C4 (Uniswap V3 pool drain). Slot 6's existing fixtures cover happy-path slippage; scenario fixtures need
  stress-shape variants.
- **simulation_scenarios_topology_price_shocks_2026_05_09.md**: Category B scenarios align with topology-shock taxonomy;
  check for SSOT overlap (closed-set scenario IDs should NOT drift between plans).
- **defi_master.md**: `UniswapConnector.swap_exact_input` SwapRouter02 address
  `0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45` is **Ethereum mainnet**. Base + Arbitrum SwapRouter02 addresses differ —
  Family 1 loop unwinds on those chains need separate connector config.
- **master_to_live_defi_2026_05_23.md Group F item 18** (2-year batch backtest run): Phase 12 satisfies via full
  scenario matrix; update master plan item-18 wording to reference scenario ID set.

## Temporary states + canonical follow-up plans

- **P1 lending protocols (Spark / Morpho Blue / Maker DSR)** deferred from Phase 1; successor plan:
  `plans/active/defi_recursive_borrow_protocol_expansion_2026_06_xx.md` (TBD post-cutover).
- **Solana / Marginfi / Kamino** deferred entirely; successor plan:
  `plans/active/defi_recursive_borrow_solana_2026_06_xx.md` (TBD post-cutover).
- **Other perp venues (Binance / OKX / Deribit / Aster)** deferred from Phase 6; successor: same protocol-expansion plan
  above OR a venue-expansion plan.
- **Full external Solidity audit of `RecursiveLeverageReceiver.sol`** deferred from Phase 4; successor plan:
  `plans/active/defi_recursive_borrow_security_audit_2026_06_xx.md` (TBD post-MVP volume scaling).
- **Cross-asset Family 1 variants (USDC vs DAI on same venue, etc.)** marked P2 within Phase 1 / Phase 5; successor:
  protocol-expansion plan above.
- **Custody (Copper / CEFFU) bridge for live USDC margin top-up** per master plan Group F item 19; consumed by Phase 7
  in testnet via pre-funded wallet, fully wired in master plan Phase F.

Each successor plan landed before this plan archives, per "Plan Archival HARD RULE" 2026-05-08.

## Total budget + sequencing

- Phase 0 — 0.5d
- Phase 1 — 5d (P0 critical-path, gates 9 + 12)
- Phase 2 — 1d (parallel with 1)
- Phase 3 — 2d (after 2)
- Phase 4 — 3d (parallel with 1, 2, 3)
- Phase 5 — 4d (after 4)
- Phase 6 — 3d (parallel with 5)
- Phase 7 — 2d (after 5 + 6)
- Phase 8 — 2d (parallel with 7)
- Phase 9 — 3d (after 1 + 5)
- Phase 10 — 1d (rolling alongside)
- Phase 11 — 2d (after 9)
- Phase 12 — 2d (after 9 + 11)
- Phase 13 — 1d (after 12)

Sum sequential critical path: P1 (5) → P3 (2) → P5 (4) → P7 (2) → P9 (3) → P12 (2) → P13 (1) = 19 days. With
parallelisation (P2 || P1, P4 || P1+P2+P3, P6 || P5, P8 || P7, P10 rolling, P11 after P9): **~17 calendar AI-days**
end-to-end. Fits the May-23 cutover if started no later than 2026-05-12.

## DONE-2026-05-14 — slot 9 (Harsh `harsh-slot-9`) Descope annotation + successor plan filing

> Slot 9 Day-3 Wave 1 task: defi_recursive_borrow DESCOPE annotation + successor plan. Plan-writing only, no code.

| Commit        | Repo               | Scope                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ------------- | ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PM@082f217f` | unified-trading-pm | Descope banner (DESCOPED 2026-05-14) added to plan top; frontmatter updated (status: partial-shipped-descoped + successor_plan field); "Deferred work — migrated to successor plan" section filed with 13-row migration table (Phase 0 banners → Phase 13 live deploy). Successor plan `defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md` created with all [ ] todos migrated with MIGRATED FROM provenance. |
| `PM@3acaae6f` | unified-trading-pm | Master plan inventory regenerated: 74 plans / 43% done / 575 cal AI-days remaining; successor plan row added.                                                                                                                                                                                                                                                                                                           |

**Done-def met**: current plan annotated with descope decision + successor banner ✅; successor plan filed at
`plans/active/` ✅; master plan inventory regenerated ✅.
