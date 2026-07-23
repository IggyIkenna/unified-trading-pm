---
doc_type: codex-ssot
title: DART Manual-Trade Lane — Per-Archetype Scope Specification
summary:
  Per-archetype DART manual-trade lane scope spec — which of the 14 InstructionActionV2 actions (TRADE/SWAP/LEND/BORROW/
  STAKE/UNSTAKE/QUOTE/TRANSFER/BRIDGE/ATOMIC/CANCEL/…) each May-23 critical-path archetype must replicate manually
  through the SAME execution path as automation, the 5 UI BUILD enrichments of existing surfaces, strategy_id
  attribution (FAMILY.ARCHETYPE.slot_id) at /manual/instruction, and CapitalAllocation-respect validation. Phase C
  shipped 2026-05-13.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [alerting-service, batch-live-reconciliation-service, execution-service, unified-trading-system-ui]
scope: [engineer, admin]
tags: [strategy, dart, ui, execution, defi, verification]
related:
  [
    ../../../04-architecture/manual-trade-booking.md,
    /codex/09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md,
    ../archetypes/carry-staked-basis.md,
    ../archetypes/carry-basis-perp.md,
    ../README.md,
  ]
created: 2026-05-08
authoritative_for: [DART manual-trade per-archetype scope + action-type replication matrix]
referenced_by:
  [
    /codex/04-architecture/research-service-and-dart-integration.md,
    /codex/09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md,
  ]
owner:
last_reviewed:
code_refs:
---

# DART Manual-Trade Lane — Per-Archetype Scope Specification

> **Phase C remainder shipped 2026-05-13** (operator direction — pulled forward into May-23 cutover). Routes +
> components + unified dart-client.ts shipped at `unified-trading-system-ui` Phase C implementation:
>
> - `app/(platform)/services/dart/terminal/manual/page.tsx` — dedicated route replacing Sheet deep-link.
> - `app/(platform)/services/dart/terminal/manual/[instructionId]/page.tsx` — per-instruction monitor route.
> - `components/dart/manual-trade-form.tsx` — extracted form component.
> - `components/dart/trade-preview.tsx` — extracted preview component.
> - `components/dart/execution-dispatch.tsx` — dispatch coordinator.
> - `lib/api/dart-client.ts` — unified typed wrappers for 4 DART endpoints.
> - `lib/api/mocks/dart.ts` — mock fixtures wired into mock-handler.ts.
> - `tests/e2e/dart-manual-trade-flow.spec.ts` — Playwright e2e spec. **Reference plan**:
>   `plans/active/dart_manual_trade_ux_refactor_2026_05_13.md`.

> **Plan-of-record**:
> [`plans/active/cross_cutting_may_23_deliverables_2026_05_08.md`](../../../../plans/active/cross_cutting_may_23_deliverables_2026_05_08.md)
> deliverable #4. **Parent epic**:
> [`plans/epics/dart_and_promote_master.md`](../../../../plans/epics/dart_and_promote_master.md) (absorbed from
> `cross_cutting_may_23_SUPERSEDED_2026_05_21.epic.md` 2026-05-21 — use `dart_and_promote_master` for all new
> cross-references). **Live-only success criterion**:
> [`master_to_live_defi_2026_05_23.md`](../../../../plans/active/master_to_live_defi_2026_05_23.md) Group G item 23
> (DART manual-trade gate).

## 1. Why this doc exists

The cross-cutting epic frames deliverable #4 as: _"the UI needs to be able to replicate everything that we're doing"_ —
every automated archetype on the May-23 critical path must have a DART manual-fallback surface that exercises the SAME
code path as the automated lane. The operator-confirmed bar from
[`master_to_live_defi_2026_05_23.md`](../../../../plans/active/master_to_live_defi_2026_05_23.md) Group G item 23 is:

> _"DART terminal in UTS-UI visualizes the strategy archetype end-to-end; operator first puts trades on manually →
> backend executes through the same path as automation → monitor for the gate window → flip switch to automation."_

This doc enumerates **per-archetype manual-replication surfaces** (the WHAT) + **scope-decision matrix per
StrategyInstruction action type** (the WHICH ACTIONS) + **integration discipline** (strategy_id attribution + capital
allocation respect + deferred post-cutover scope).

**Plan-of-record open question #2 resolution** (from the cross-cutting plan):
`Default = operator-only this cycle; external-broker-style DART for non-operator users post-cutover`. This doc binds to
that resolution.

**Plan-of-record open question #4 resolution**: prediction-market manual surface is _backtest-only this cycle_ to match
the prediction_markets epic scope; live wiring is post-cutover work.

This doc is a **peer** to [`operational-modes-matrix.md`](operational-modes-matrix.md) (the orthogonal-axes mode SSOT)
and **builds on** [`../../04-architecture/manual-trade-booking.md`](../../../04-architecture/manual-trade-booking.md)
(the existing ManualInstruction / ManualExecutionMode / `/manual/instruction` API SSOT). The surfaces this doc requires
for May-23 are **enrichments of those existing surfaces**, not greenfield UI.

## 2. StrategyInstruction action-type scope decision matrix

The strategy layer emits a polymorphic `StrategyInstruction` whose actions are enumerated by the UAC SSOT
`unified_api_contracts.internal.architecture_v2.enums.InstructionActionV2` (currently 14 members: `TRADE`, `SWAP`,
`LEND`, `BORROW`, `STAKE`, `UNSTAKE`, `QUOTE`, `TRANSFER`, `BRIDGE`, `ATOMIC`, `CANCEL`, `CONVERT_DUST`, `LP_MINT`,
`LP_BURN`). DART must replicate each action that a May-23 critical-path archetype emits in manual mode. The matrix below
covers the 11 actions in scope for the May-23 cycle; `CONVERT_DUST` + `LP_MINT` + `LP_BURN` ride alongside the DeFi LP
archetype activation per [`plans/epics/strategy_master.md`](../../../../plans/epics/strategy_master.md).

**Legend**: ✅ = required for May-23 cutover (live archetypes that emit this action). ◐ = backtest exec validation only
(archetype emits this action but archetype is backtest-only this cycle). ✗ = post-cutover (no live or backtest archetype
emits this action this cycle, OR the action lives in a deferred archetype family).

| Action type | May-23 surface | Archetypes that emit it (live cycle = bold)                                                                                                                                                   | Operator-replicable surface required (UI route + venue/protocol coverage)                                                                                                                                                                                                                                               | Strategy ID attribution required? |
| ----------- | -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| `TRADE`     | ✅             | **CARRY_BASIS_PERP**, **CARRY_BASIS_DATED**, **ML_DIRECTIONAL_CONTINUOUS**, **CARRY_STAKED_BASIS** (CeFi short perp leg), `RULES_DIRECTIONAL_*`, `STAT_ARB_*`, `ML_DIRECTIONAL_EVENT_SETTLED` | Existing `ManualTradingPanel` + `/services/trading/book` page in unified-trading-system-ui — limit / market / stop order types across CeFi venues `Bybit / Deribit / Binance / OKX`. Hyperliquid + Aster perp coverage required for the 6-venue carry hedge leg per master plan deadline.                               | ✅ — every fill                   |
| `SWAP`      | ✅             | **CARRY_STAKED_BASIS** (DEX swap to acquire LST collateral)                                                                                                                                   | New DART panel: per-chain × per-protocol DEX swap. Solana → Pacifica + Jito + Marinade; Ethereum → Uniswap_v3 + Curve; Arbitrum → Uniswap_v3 + Camelot; Base → Uniswap_v3 + Aerodrome. Wires through `execution-service` `UniswapConnector.swap_exact_input()` (live) + DEX matching engine (backtest).                 | ✅                                |
| `LEND`      | ✅             | **CARRY_STAKED_BASIS** (Aave deposit), `YIELD_ROTATION_LENDING` (post-cutover — backtest-only this cycle)                                                                                     | New DART panel: per-chain × per-protocol lend. Aave_v3 across Ethereum / Arbitrum / Base. Wires through `execution-service` Aave connector.                                                                                                                                                                             | ✅                                |
| `BORROW`    | ✅             | **CARRY_STAKED_BASIS** (Aave borrow against LST collateral)                                                                                                                                   | Same DART panel as `LEND`; mode toggle. Aave_v3 across Ethereum / Arbitrum / Base.                                                                                                                                                                                                                                      | ✅                                |
| `STAKE`     | ✅             | **CARRY_STAKED_BASIS** (acquire LST: Lido stETH on Ethereum; Jito jitoSOL + Marinade mSOL on Solana; bSOL via Sanctum on Solana)                                                              | New DART panel: per-chain LST staking. Ethereum → Lido. Solana → Jito + Marinade + Sanctum.                                                                                                                                                                                                                             | ✅                                |
| `UNSTAKE`   | ✅             | **CARRY_STAKED_BASIS** (close-out: redeem LST → underlying)                                                                                                                                   | Same panel as `STAKE`; mode toggle.                                                                                                                                                                                                                                                                                     | ✅                                |
| `QUOTE`     | ✗              | `MARKET_MAKING_CONTINUOUS`, `MARKET_MAKING_EVENT_SETTLED` (both post-cutover)                                                                                                                 | Out-of-scope this cycle. Manual quote surface is post-cutover work paired with market-making archetype activation.                                                                                                                                                                                                      | ✗ (when activated: ✅)            |
| `TRANSFER`  | ✅             | **CARRY_STAKED_BASIS** (operator funds DeFi wallet from CEX), **CARRY_BASIS_PERP** (cross-venue rebalance)                                                                                    | New DART panel: per-(source, dest) account transfer. CEX → DeFi wallet (Binance/OKX/Bybit → on-chain wallet). Sub-account moves within CeFi venue. Wires through `execution-service` `INTERNAL_SUBACCOUNT` + `CEX_WITHDRAWAL_DEPOSIT` + `ON_CHAIN_TRANSFER` primitives per `strategy-summary.md` § Transfer primitives. | ✅                                |
| `BRIDGE`    | ✅             | **CARRY_STAKED_BASIS** (cross-chain rebalance), `YIELD_ROTATION_LENDING` (post-cutover)                                                                                                       | Same DART panel as `TRANSFER`; mode toggle for cross-chain. Across / Stargate / LayerZero per `strategy-summary.md`. Required cross-chain pairs: Ethereum ↔ Arbitrum, Ethereum ↔ Base, Solana ↔ Ethereum (via Wormhole / Allbridge if Across not yet supported on Solana — confirm at impl time).                       | ✅                                |
| `ATOMIC`    | ✅             | **CARRY_STAKED_BASIS** (flash-loan-backed open: Aave flash loan → swap → stake → deposit → borrow → repay, all in one tx)                                                                     | New DART panel: bundled action submission. Wires through `execution-service` flash-loan receiver (`FlashLoanReceiver.sol` deployed per chain). Operator submits the bundle shape via UI, backend executes atomically.                                                                                                   | ✅                                |
| `CANCEL`    | ✅             | All archetypes that emit live orders (`TRADE`, pending DEX swaps, pending bridges)                                                                                                            | Already covered by `/manual/cancel` endpoint per [`manual-trade-booking.md`](../../../04-architecture/manual-trade-booking.md). DART surface = "cancel my last in-flight" button per archetype context.                                                                                                                 | ✅                                |

## 3. Per-archetype manual-fallback map

The full canonical archetype set lives in UAC `unified_api_contracts.internal.architecture_v2.enums.StrategyArchetype`
(the SSOT). This spec materialises the **May-23 live + immediate-backtest subset** of those archetypes — the live carry
leads, their backtest siblings, and the manual surfaces those archetypes emit. Each archetype's manual-fallback
requirement is enumerated below.

> **Scope note.** Post-cutover archetypes (full Phase 9 expansions: MEV, DeFi LP, market-making sub-variants, full vol
> surface, prediction MM, cross-domain event arb, portfolio sleeves) extend this spec under
> [`plans/epics/strategy_master.md`](../../../../plans/epics/strategy_master.md) (supersedes
> `strategy_and_dart_master_SUPERSEDED_2026_05_21.md`). The UAC enum is the always-authoritative count; this doc cites
> the live + backtest subset by name.

### Live archetypes for May-23 (manual surface = ✅ required)

- **CARRY_STAKED_BASIS** — DeFi LST collateral + leverage carry. Manual surfaces: `SWAP` (acquire underlying), `STAKE`
  (LST mint), `LEND` (Aave deposit), `BORROW` (loop), `TRADE` (CeFi short perp leg hedge), `ATOMIC` (flash-loan-backed
  open + close), `TRANSFER` + `BRIDGE` (cross-venue / cross-chain rebalance), `CANCEL`. Asset-group: defi (lead) + cefi
  (hedge leg). Chains: Solana (Pacifica + Jito + Marinade), Ethereum (Lido + Aave + Uniswap + Curve), Arbitrum
  (Aave_v3 + Camelot), Base (Aave_v3 + Aerodrome). **Master plan deadline-critical**.
- **CARRY_BASIS_PERP** — long spot / short perp basis carry. Manual surfaces: `TRADE` (limit + market + stop) on each of
  the 6 perp venues — Bybit, Deribit, Binance, OKX, Hyperliquid, Aster. `CANCEL`. Asset-group: cefi. **Master plan
  deadline-critical**.
- **CARRY_BASIS_DATED** — long spot / short dated future basis carry. Manual surfaces: `TRADE` for spot leg + dated
  future leg + `CANCEL`. Venues: same 4 CeFi venues + TradFi (CME) for ES / SPY-equivalent dated. _Live for crypto;
  TradFi extension is roadmap_.
- **ML_DIRECTIONAL_CONTINUOUS** — CeFi ML signal-driven directional. Manual surfaces: `TRADE` + `CANCEL` on the 4 CeFi
  venues + ML training trigger (pause / resume / retrain). The training trigger wires to `ml-training-service` API.

### Backtest exec-validation archetypes (manual surface = ◐ required for backtest validation only)

- **ML_DIRECTIONAL_EVENT_SETTLED** — ML-driven prediction-market trades. Manual surfaces: prediction-market trade
  placement (Polymarket / Kalshi / Opinion-Trade backtest) + `CANCEL`. **Backtest-only this cycle** per plan open
  question #4 resolution.
- **RULES_DIRECTIONAL_CONTINUOUS** — rules-based directional (CeFi / TradFi). Manual surface: `TRADE` + `CANCEL`, shares
  CeFi-venue panel with `ML_DIRECTIONAL_CONTINUOUS`. **Backtest-only this cycle**.
- **RULES_DIRECTIONAL_EVENT_SETTLED** — rules-based event-settled (sports / prediction). Manual surfaces: sports bet
  placement (backtest exec validation) + prediction-market trade placement (backtest). **Backtest-only this cycle**.

### Post-cutover archetypes (manual surface = ✗ scope-out this cycle)

The following archetypes are NOT in scope for May-23 manual surfaces. They will land their manual surfaces alongside
their archetype activation in the post-cutover roadmap (see
[`plans/epics/strategy_master.md`](../../../../plans/epics/strategy_master.md)).

- **MARKET_MAKING_CONTINUOUS** + **MARKET_MAKING_EVENT_SETTLED** — `QUOTE` action surfaces deferred.
- **EVENT_DRIVEN** — macro / earnings / scheduled-event surfaces deferred.
- **VOL_TRADING_OPTIONS** — option-structure surfaces (`CALL_SPREAD`, `BUTTERFLY`, `RISK_REVERSAL`, etc.) deferred. UI
  shape will piggyback on TradFi options chain UI when activated.
- **STAT_ARB_PAIRS_FIXED** + **STAT_ARB_CROSS_SECTIONAL** — stat-arb pair-trade surfaces deferred. Manual `TRADE`
  surface piggybacks on existing CeFi-venue panels when activated; only the pair-bundling submission UI is new.
- **ARBITRAGE_PRICE_DISPERSION** + arbitrage-mev-\* sub-archetypes (`backrun`, `jit_liquidity`, `liquidation_bundle`,
  `sandwich`) — deferred. MEV surfaces require special infra (private mempool + bundler integration).
- **LIQUIDATION_CAPTURE** — deferred.
- **CARRY_RECURSIVE_STAKED** + **YIELD_STAKING_SIMPLE** + **YIELD_ROTATION_LENDING** — deferred-rollout, but their
  manual surfaces piggyback on the **CARRY_STAKED_BASIS** surfaces (same `SWAP` / `STAKE` / `LEND` / `BORROW` /
  `TRANSFER` / `BRIDGE` panels). When activated post-cutover, no new manual UI surface is needed; only the archetype's
  routing logic.
- **DEFI*LP*\*** (concentrated / pool / vault) — deferred. New action-type semantic (LP add / remove) not yet wired into
  `StrategyInstruction`; action-type extension is part of the LP archetype activation work.

## 4. Required manual surfaces (the 5 BUILDs Harsh Tab 6 ships)

Per the cross-cutting plan deliverable #4 [BUILD] subitems, Harsh T6's implementation work is bounded to **5 enrichments
of existing surfaces** (not greenfield UI). Each row references the existing surface it enriches.

1. **DART manual DeFi swap / lend / borrow / stake** for `CARRY_STAKED_BASIS` across enabled chains.
   - **Existing surface**: `unified-trading-system-ui/components/trading/manual/manual-trading-panel.tsx` (CeFi-only
     today).
   - **Enrichment**: add a "DeFi Action" tab to `ManualTradingPanel` with chain selector (Solana / Ethereum / Arbitrum /
     Base) → protocol selector (Pacifica / Jito / Marinade / Lido / Aave_v3 / Uniswap_v3 / Curve / Camelot / Aerodrome)
     → action selector (`SWAP` / `STAKE` / `UNSTAKE` / `LEND` / `BORROW` / `ATOMIC`). Wires through existing
     `/manual/instruction` API endpoint with `category` field set to `defi`.
   - **Backend**: `execution-service`'s DeFi connectors (`AaveConnector`, `UniswapConnector`, LST connectors) already
     handle `SWAP` / `LEND` / `BORROW` / `STAKE` / `UNSTAKE` / `ATOMIC`. No new connector code; new UI form fields +
     validation only.

2. **DART manual CeFi order placement** across the 4 live CeFi venues + Hyperliquid + Aster.
   - **Existing surface**: `manual-trading-panel.tsx` already supports CeFi limit / market / stop. The
     [`manual-trade-booking.md`](../../../04-architecture/manual-trade-booking.md) doc shows venue list resolves
     dynamically from UAC `CAPABILITY_DECLARATIONS` registry.
   - **Enrichment**: verify Hyperliquid + Aster are in `CAPABILITY_DECLARATIONS` for the manual-instruction venue list;
     if not, add them. Verify TWAP / VWAP / ICEBERG / SOR / BEST_PRICE algos are exposed for each.
   - **Backend**: Already shipped. Verification only.

3. **DART manual ML training trigger** — pause / resume / retrain per ML archetype.
   - **Existing surface**: NEW — no existing surface in `unified-trading-system-ui` today. The closest existing
     primitive is the `dart/strategy-param-version-bump-modal.tsx` component (which handles param version bumps but not
     training lifecycle).
   - **Build**: new `MlTrainingControlPanel` component under `components/dart/` mounting at `/services/dart/ml-training`
     route. Per-archetype model registry entry → action buttons (`pause` / `resume` / `retrain`). Wires to
     `ml-training-service` API (`POST /training/{archetype}/{action}`).
   - **Backend**: `ml-training-service` API endpoint per action — existing CLI surfaces an equivalent — verify endpoint
     is exposed before May-23.

4. **DART manual sports bet placement** — backtest exec validation only.
   - **Existing surface**: `manual-trading-panel.tsx` may already support sports category (per `manual-trade-booking.md`
     "Category tabs"). Verify.
   - **Backend**: backtest matching engine — no live wiring. Operator submits a bet (instrument = fixture_id, side =
     home / away / draw), matching engine returns simulated fill. Wires to `execution-service` matching-engine path with
     `OperationalMode.BACKTEST`.
   - **Backtest-only**. Live wiring is deferred per [`sports_master.md`](../../../../plans/epics/sports_master.md)
     post-cutover scope.

5. **DART manual prediction-market trade** — Polymarket / Kalshi / Opinion-Trade / CME-event-arb (backtest-only).
   - **Existing surface**: `manual-trading-panel.tsx` may already support prediction category. Verify.
   - **Backend**: backtest matching engine. Operator submits a market_id + side + size; matching engine returns
     simulated fill against the canonical_question_group's CLOB (per [`prediction-markets.md`](prediction-markets.md)).
   - **Backtest-only** per plan open question #4 resolution.

## 5. Strategy ID attribution discipline

Every manual trade submitted via DART **must** be tagged with a derived strategy_id at the `/manual/instruction` API
boundary. The schema is:

```text
FAMILY.ARCHETYPE.slot_id
# where slot_id = archetype@venue-asset-instrument-period-quote-env
# e.g. CARRY.CARRY_STAKED_BASIS.carry_staked_basis@BYBIT-defi-ETH_STAKING-1d-USDC-prod
```

> **✅ RESOLVED 2026-05-08 via Option A** (`uac@5083d65`). Operator GREENLIT. The canonical grammar is the existing
> 6-axis slot grammar: `FAMILY.ARCHETYPE.slot_id` where `slot_id = archetype@venue-asset-instrument-period-quote-env`.
> No `vN` field — material config changes produce a new `slot_id` value rather than incrementing a version suffix.
> Reference: `cross_cutting_may_23_deliverables_2026_05_08.md` § "Open questions" Q2/Q3.

The `/manual/instruction` API already has a `strategy_id: str` field per
[`manual-trade-booking.md`](../../../04-architecture/manual-trade-booking.md). DART UI populates this field from the
selected archetype + venue + instrument_type combination using `unified_api_contracts.strategy.format_strategy_id`.

**Used downstream by**:

- **PnL attribution** — `pnl-attribution-service` rolls up manual fills by strategy_id alongside automated fills, so the
  operator can see "this manual carry trade contributed $X" attributable to the same archetype as the automated lane.
- **Batch-vs-live reconciliation** — `batch-live-reconciliation-service` compares manual fills against the
  matching-engine fills the same archetype would have produced, isolating execution alpha from strategy alpha (per
  CLAUDE.md "Batch = Live: Unified Pipeline Architecture" rule).
- **Alerting** — `alerting-service` rules emit strategy_id per fired alert (per cross-cutting epic deliverable #2
  use-case "alerting (which strategy fired)"). Manual-fill alerts carry the derived strategy_id so the operator can
  correlate "manual trade X breached threshold Y on archetype Z."

## 6. Capital allocation respect

Every DART manual submission **must** respect the capital-allocation constraints declared per
`(client, archetype, venue)` in the `CapitalAllocation` matrix (cross-cutting plan deliverable #3 — owned by Tab 6.B).

The validation helper `validate_allocation_respect(allocation, position_value_usd, drawdown_pct)` runs at the
`/manual/instruction` API boundary and raises `AllocationViolation` if:

- `position_value_usd > allocation.initial_capital_usd × allocation.max_position_pct`, OR
- `drawdown_pct > allocation.max_drawdown_pct`.

The DART UI displays the active `CapitalAllocation` cap inline above the order-entry form, and shows a confirmation
warning before submission. Operator override requires an explicit `--force-allocation-override` flag (HUMAN-ONLY; not
exposed in UI; only available via CLI for emergency unwinds).

**Out-of-scope for May-23**: per-operator-role permissions on allocation overrides. All operators on the cluster have
override capability this cycle; granular role-based access is post-cutover work.

## 7. Defer post-cutover

> **[DELTA 2026-05-22]** May-23 cutover landed 2026-05-23. Items below remain deferred; post-cutover tracking in
> [`dart_and_promote_master.md`](../../../../plans/epics/dart_and_promote_master.md).

The following are **explicitly NOT in scope** for May-23 cutover. They are documented here so operators don't expect
them and so the cross-cutting plan body can flip its [DESIGN] checkbox without ambiguity.

- **Third-party operator UI / external broker DART** — the manual lane this cycle is operator-only (Ikenna + Harsh +
  designated workspace operators). External counterparties / clients receiving a DART-style UI is deferred per plan open
  question #2 resolution.
- **Granular role-based access (RBAC)** for non-Ikenna operators on cluster — deferred. Audit-log of every manual click
  via the existing `unified-events-interface` event stream is sufficient for May-23 (every manual instruction emits a
  `MANUAL_INSTRUCTION_SUBMITTED` event with `submitted_by` operator identity per
  [`manual-trade-booking.md`](../../../04-architecture/manual-trade-booking.md)).
- **Tamper-evident audit trail** (cryptographic chaining of MANUAL_INSTRUCTION events) — deferred. Light audit-log via
  the event stream is acceptable for a 3-day manual gate window.
- **Live wiring for prediction-market and sports manual trades** — backtest-only this cycle per plan open questions #2
  - #4.
- **Manual surfaces for `MARKET_MAKING_*`, `EVENT_DRIVEN`, `VOL_TRADING_OPTIONS`, `STAT_ARB_*`, `ARBITRAGE_*`,
  `LIQUIDATION_CAPTURE`, `DEFI_LP_*`** — deferred per § 3 above. Each ships its manual surface alongside its archetype
  activation in the post-cutover roadmap.
- **`QUOTE` action manual surface** — deferred (no live archetype emits `QUOTE` this cycle).
- **DART v2 archetype roadmap** (full 46-archetype + 9-family rollout per UAC v2 enum) — tracked in
  [`plans/epics/dart_and_promote_master.md`](../../../../plans/epics/dart_and_promote_master.md).

## 8. Cross-references

- [`plans/active/cross_cutting_may_23_deliverables_2026_05_08.md`](../../../../plans/active/cross_cutting_may_23_deliverables_2026_05_08.md)
  — plan-of-record (this doc is its deliverable #4).
- [`plans/epics/dart_and_promote_master.md`](../../../../plans/epics/dart_and_promote_master.md) — current parent epic
  (supersedes `cross_cutting_may_23_SUPERSEDED_2026_05_21.epic.md`; 5 non-negotiable deliverables for May-23 +
  post-cutover roadmap).
- [`plans/active/master_to_live_defi_2026_05_23.md`](../../../../plans/active/master_to_live_defi_2026_05_23.md) Group G
  item 23 — live-only success criterion (DART manual-trade gate).
- [`plans/active/issues/cross_cutting_strategy_catalogue_already_shipped_2026_05_08.md`](../../../plans/active/issues/cross_cutting_strategy_catalogue_already_shipped_2026_05_08.md)
  — Tab 6.A finding that strategy_id grammar is already shipped (this spec consumes whichever grammar lands
  post-triage).
- [`/codex/04-architecture/manual-trade-booking.md`](../../../04-architecture/manual-trade-booking.md) — existing
  ManualInstruction / `/manual/instruction` API SSOT (this doc enriches, not replaces).
- [`/codex/09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md`](operational-modes-matrix.md) — peer
  doc (orthogonal-axes mode SSOT).
- [`/codex/09-strategy/operational/onboarding-checklist.md`](../../operational/onboarding-checklist.md) — strategy
  onboarding flow that the manual lane integrates with (every onboarded strategy gets a manual fallback automatically).
- [`/codex/09-strategy/operational/client-onboarding.md`](../../operational/client-onboarding.md) — per-client manual
  lane setup flow.
- [`/codex/09-strategy/strategy-summary.md`](../../strategy-summary.md) — 8-family / 18-archetype baseline (codex SSOT;
  stale relative to UAC v2 enum's 9-family / 46-archetype shape — see issue doc above).
- [`/codex/09-strategy/architecture-v2/README.md`](../README.md) — architecture-v2 SSOT entry point.

### Archetype docs referenced by this spec (May-23 live + backtest subset)

- [`carry-staked-basis.md`](../archetypes/carry-staked-basis.md) — **live May-23 lead**.
- [`carry-basis-perp.md`](../archetypes/carry-basis-perp.md) — **live May-23**.
- [`carry-basis-dated.md`](../archetypes/carry-basis-dated.md) — live May-23 (crypto), TradFi roadmap.
- [`carry-recursive-staked.md`](../archetypes/carry-recursive-staked.md) — post-cutover.
- [`ml-directional-continuous.md`](../archetypes/ml-directional-continuous.md) — **live May-23 (CeFi)**.
- [`ml-directional-event-settled.md`](../archetypes/ml-directional-event-settled.md) — backtest May-23.
- [`rules-directional-continuous.md`](../archetypes/rules-directional-continuous.md) — backtest May-23.
- [`rules-directional-event-settled.md`](../archetypes/rules-directional-event-settled.md) — backtest May-23.
- [`yield-staking-simple.md`](../archetypes/yield-staking-simple.md) — post-cutover (piggybacks).
- [`yield-rotation-lending.md`](../archetypes/yield-rotation-lending.md) — post-cutover (piggybacks).
- [`market-making-continuous.md`](../archetypes/market-making-continuous.md) — post-cutover.
- [`market-making-event-settled.md`](../archetypes/market-making-event-settled.md) — post-cutover.
- [`event-driven.md`](../archetypes/event-driven.md) — post-cutover.
- [`vol-trading-options.md`](../archetypes/vol-trading-options.md) — post-cutover.
- [`stat-arb-pairs-fixed.md`](../archetypes/stat-arb-pairs-fixed.md) — post-cutover.
- [`stat-arb-cross-sectional.md`](../archetypes/stat-arb-cross-sectional.md) — post-cutover.
- [`arbitrage-price-dispersion.md`](../archetypes/arbitrage-price-dispersion.md) — post-cutover.
- [`liquidation-capture.md`](../archetypes/liquidation-capture.md) — post-cutover.
