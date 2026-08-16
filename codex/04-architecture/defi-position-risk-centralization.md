---
doc_type: codex-ssot
title: DeFi position-risk centralization — the strategy-agnostic, venue-agnostic pattern
summary: >-
  Any archetype that takes genuine on-chain DeFi leverage (posts collateral, borrows against it) must read its own
  position's private risk data — health factor, LTV, collateral, debt, borrow-capacity, liquidation price — through
  one centralized module, never from the generic features-service pipeline and never with archetype-specific
  wiring. Documents the intended pattern and its current (not-yet-complete) implementation state, filed after an
  audit found two live archetypes reading a meaningless generic feature key for liquidation gating.
authoritative_for: [defi-leverage-risk-data-sourcing, health-factor-gating-pattern]
status: current
nature: ssot
asset_group: [defi]
stage: [meta]
repos: [strategy-service, execution-service, unified-api-contracts]
scope: [engineer]
tags: [defi, risk, health-factor, liquidation, architecture, centralization]
created: 2026-08-16
last_updated: "2026-08-16"
related:
  [
    /plans/active/issues/defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md,
    /codex/04-architecture/defi-execution-overview.md,
  ]
referenced_by:
owner:
last_reviewed:
code_refs:
  [
    strategy_service/position/core/defi_health_aggregator.py,
    strategy_service/position/api/routes/positions_health.py,
    strategy_service/position/position_interface/adapters/aave.py,
    execution_service/defi_execution/monitors/health_factor_monitor.py,
  ]
---

# DeFi position-risk centralization

## The rule

**Any archetype that can take genuine on-chain DeFi leverage — posts collateral to a lending protocol, borrows
against it, or otherwise carries real liquidation exposure — must read its own position's private risk data
through one centralized, strategy-agnostic, venue-agnostic module.** Never from the generic per-tick `features`
dict (that pipeline carries market-wide/protocol-level data, not private per-wallet position state), and never
with archetype-specific bespoke wiring that a second archetype would have to reimplement or copy.

This is distinct from **CEX margin/leverage**, which is a different mechanism entirely (venue-reported account
health, not on-chain state) and out of this doc's scope.

## What counts as "DeFi-leverage-capable"

An archetype needs this pattern if it posts on-chain collateral and/or borrows against it. It does **not** need it
for pure supply-side/LP positions (deposit capital, earn yield, no borrowing, no liquidation exposure) — those
archetypes correctly have no health-factor-style gate.

As of 2026-08-16, exactly two archetypes qualify: `CARRY_STAKED_BASIS` (`staked_basis.py`, when its `LST_AS_MARGIN`
structure posts the LST as real on-chain-derived perp margin) and `CARRY_RECURSIVE_STAKED` (`recursive_staked.py`,
a genuine `STAKE→LEND→BORROW→STAKE...` recursive loop). `rotation_lending.py` and the `defi_lp/*.py` family are
supply-side only and correctly excluded. Re-verify this list whenever a new DeFi archetype is added — don't assume
it's still exactly these two.

## The centralized module (current state — not yet complete)

- **`strategy_service/position/core/defi_health_aggregator.py`** (`DeFiHealthAggregator`) — the aggregation logic.
  Already venue/protocol-agnostic by construction (iterates whatever `DeFiLendingPosition` objects it's handed,
  keyed by protocol/chain, no protocol-specific branching) and `client_id`-scoped. Outputs combined health factor,
  collateral/debt USD, weighted APY, riskiest protocol, per-chain breakdown.
- **`strategy_service/position/api/routes/positions_health.py`** — serves `PositionHealthSnapshot`: LTV, margin
  ratio, liquidation threshold, maintenance margin. Complements the aggregator's fields.

**Neither is callable from the strategy engine today.** Both sit behind HTTP routes
(`position/api/routes/risk.py:248,271`), consumed by execution-service's `run_wallet_preflight_checks`, not by any
`engine/strategies/v2/**` archetype. **Neither is fed by a live source today** — only test code calls
`update_wallet_health_from_lending`. A stub adapter (`position/position_interface/adapters/aave.py`) that looks
like it should feed the aggregator raises `NotImplementedError` on its data methods and returns the wrong schema
(`CanonicalPosition` instead of `DeFiLendingPosition`) even if implemented. The one genuinely working live poller
is execution-service's `defi_execution/monitors/health_factor_monitor.py` (real per-wallet `getUserAccountData()`
calls) — not yet wired to feed the aggregator.

**Data model gaps**: the aggregator's output has no LTV, borrow-capacity, or liquidation-price field;
`PositionHealthSnapshot` has LTV and a liquidation threshold but the latter is hardcoded to `MarginModel.AAVE_V3`
rather than resolved per the position's actual protocol.

Full findings, root cause, and the fix todo list:
[defi_leverage_archetypes_health_factor_wrong_source_2026_08_16](/plans/active/issues/defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md).

## Mode-aware dispatch (target design, not yet built)

Once a callable centralized path exists, the read should dispatch on execution mode, not fall back to one constant
regardless of mode:

- **batch** — real historical data for the window being replayed.
- **live** — real-time poll against the actual wallet.
- **paper-testnet** — poll a testnet protocol deployment, validating the wiring end-to-end without touching
  production wallets or capital.
- **paper-live** — read-only poll of real mainnet data for the real wallet, without executing — paper trading
  against genuine current conditions rather than a stale or fabricated number.

Do not design this dispatch before the underlying centralized call exists — sequencing matters, per the issue
doc's todo list.

## What NOT to do

- Don't add a new bespoke poller or wallet-specific query inside features-service. Features-service computes
  generic, protocol/market-level data — the same shape every consumer can use regardless of who holds a position.
  Private per-wallet state belongs in strategy-service's position layer or execution-service, not there.
- Don't let a second or third DeFi-leverage archetype copy `features.get("health_factor")` as precedent —
  `recursive_staked.py` did exactly this from `staked_basis.py`, deliberately, per its own docstring. Once the
  centralized path exists, that's the thing to copy instead.
- Don't assume the centralized module is complete just because it exists and is well-structured. As of this
  writing it's a good foundation with real gaps (no live feed, not callable from the engine layer, incomplete
  field coverage) — verify current state against the issue doc before building on it.
