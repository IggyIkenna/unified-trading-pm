---
doc_type: codex-ssot
title: Position-risk / margin-health centralization — one asset-group-agnostic pattern across DeFi, CeFi and TradFi
summary: >-
  Any archetype that takes genuine leverage — DeFi on-chain borrowing, CeFi venue-margin, or (once built) TradFi
  broker margin — must read its own position's private risk data (health/margin ratio, LTV, collateral,
  debt/exposure, borrow-capacity, liquidation price) through one centralized, asset-group-agnostic aggregation
  core, never from the generic features-service pipeline and never with archetype- or asset-group-specific wiring.
  Rescoped 2026-08-17 (operator ruling) from a DeFi-only doc that explicitly excluded CeFi margin as "a different
  mechanism entirely" and never mentioned TradFi — exactly the reimplementation-drift path this doc warns against.
  Rescoping surfaced a bigger finding than expected: a second, already-asset-group-agnostic aggregation mechanism
  (`unified_trading_library.margin_and_liquidation` + `margin_event_emitter.py`) already exists, is already
  live-called, and was missed entirely by the 2026-08-16 investigation this doc was originally filed from. See
  "Two parallel mechanisms" below before building anything new.
authoritative_for:
  [leverage-risk-data-sourcing, health-factor-gating-pattern, cross-asset-group-margin-health-aggregation]
status: current
nature: ssot
asset_group: [defi, cefi, tradfi]
stage: [meta]
repos: [strategy-service, execution-service, unified-api-contracts, unified-trading-library]
scope: [engineer]
tags: [defi, cefi, tradfi, risk, margin, health-factor, liquidation, architecture, centralization]
created: 2026-08-16
last_updated: "2026-08-17"
related:
  [
    /plans/active/issues/defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md,
    /plans/active/strategy_service_centralization_fixes_2026_08_16.md,
    /codex/04-architecture/defi-execution-overview.md,
  ]
referenced_by:
owner:
last_reviewed: 2026-08-17
code_refs:
  [
    strategy_service/position/core/defi_health_aggregator.py,
    strategy_service/position/api/routes/positions_health.py,
    strategy_service/position/position_interface/adapters/aave.py,
    strategy_service/position/core/margin_event_emitter.py,
    strategy_service/position/core/venue_balance_tracker.py,
    strategy_service/position/cli/handlers/monitor_handler.py,
    execution_service/defi_execution/monitors/health_factor_monitor.py,
    execution_service/algo_library/deleverage_executor.py,
    unified_trading_library/margin_and_liquidation/liquidation_monitor.py,
    unified_trading_library/margin_and_liquidation/margin_model.py,
    unified_api_contracts/registry/cefi_margin_tiers.py,
    unified_api_contracts/registry/defi_reserve_params.py,
  ]
---

# Position-risk / margin-health centralization

## The rule

**Any archetype that can take genuine leverage — posts on-chain collateral and borrows against it (DeFi), trades
on venue margin (CeFi), or trades on broker margin (TradFi) — must read its own position's private risk data
through one centralized, asset-group-agnostic aggregation core.** Never from the generic per-tick `features` dict
(that pipeline carries market-wide/protocol-level data, not private per-position state), and never with
archetype- or asset-group-specific bespoke wiring that a second archetype or a second asset group would have to
reimplement or copy.

**CeFi margin is not a different mechanism "out of scope."** The original version of this doc said exactly that —
it was wrong, and the code already disagrees with it (see below). What genuinely differs by asset group is
**sourcing** — how you fetch the raw numbers (on-chain call vs. exchange REST/WS vs. broker API) — not the
**math**: collateral value vs. exposure/debt value → a health or margin ratio → a liquidation/maintenance
threshold → distance-to-liquidation. That math is one thing, computed the same way regardless of where the
numbers came from.

## The core is already asset-group-agnostic by design — verified, not assumed

`unified_trading_library.margin_and_liquidation` already does this correctly:

- **`PortfolioInputs`** (`margin_model.py`) is a generic `(instrument_id, quantity, mark_price_usd)` tuple shape
  for `collateral_positions`/`debt_positions`, keyed by `venue`/`account_id`/`client_id` — nothing DeFi-specific.
- **`MarginModelProtocol.compute()`** returns a `HealthFactor` graded by `_grade()`, which explicitly branches
  **"HF mode (DeFi): warning > critical > severe > liquidation as HF descends toward 1.0"** vs. **"MMR mode
  (CeFi): margin_usage_pct rising toward 100"** — both modes, in the same function, today.
- **UAC already has the CeFi-side registry**: `unified_api_contracts/registry/cefi_margin_tiers.py` — MMR/IMR
  per venue per tier, explicitly built "to mirror the shape of `defi_reserve_params.py`... so consumers (UTL
  `margin_and_liquidation` engine, risk-and-exposure-service) can call `get_margin_tier(venue, asset,
notional_usd)` without service-local lookups." Its own docstring notes on-chain perp venues (Hyperliquid,
  Aster) are classified `cefi` and share this same table — there is deliberately no separate perp-margin registry.
- **TradFi has no equivalent registry today** — confirmed by search, nothing named `*tradfi*margin*` exists
  anywhere in UAC. This is the genuine gap, not CeFi.

So the generic core and the CeFi half of the sourcing-registry split are **already built**. The work remaining is:
add a TradFi `MarginModelProtocol` implementation + a TradFi margin/buying-power registry in UAC (mirroring
`cefi_margin_tiers.py`'s shape against a broker's actual margin API, e.g. IBKR), and wire every asset group's
sourcing adapter to actually feed the core live (see gaps below — this part is incomplete for DeFi too).

## Two parallel mechanisms — reconcile before building anything new

**This is the reason this doc was rescoped rather than lightly edited.** There are two aggregation paths in the
codebase today, and the 2026-08-16 investigation that produced the original version of this doc only found one of
them.

**(A) `DeFiHealthAggregator`** (`position/core/defi_health_aggregator.py`) + `positions_health.py` HTTP route.
DeFi-only (imports only `DeFiLendingPosition`/`DeFiAggregatedHealth` from UAC, nothing from
`unified_trading_library.margin_and_liquidation`). HTTP-only, consumed by execution-service's
`run_wallet_preflight_checks`. **Not fed by any live source** — only test code populates it. **Not callable from
any `engine/strategies/v2/**` archetype.**

**(B) `margin_event_emitter.py`** (`position/core/margin_event_emitter.py`), predating (A)'s investigation by 3+
months (its own docstring: "Wave C1 — workspace audit 2026-05-01"). Its docstring states it **is** "the single
canonical producer of `MarginEvent` per UAC `EVENT_TOPIC_REGISTRY`," built on
`unified_trading_library.margin_and_liquidation` (`PortfolioInputs`, `get_margin_model`, `get_pubsub_client`) —
the asset-group-agnostic core described above. It explicitly replaced "the prior pattern of each downstream
service re-deriving HF from its own copy of positions," and states two production consumers: **alerting-service**
(Wave C4) and **risk-and-exposure-service** (Wave C2) — both per the emitter's own docstring, not independently
re-verified in this pass. Confirmed independently by grep:

- `venue_balance_tracker.py` and `position/cli/handlers/monitor_handler.py` call it in production code (not just
  tests) — `monitor_handler.py` is a CLI handler, i.e. a live-run entrypoint, not a dormant path.
- A test file exists specifically for this: `tests/position/unit/test_emit_live_cefi_margin_events.py` — CeFi
  margin events are already exercised through this path.
- **execution-service already consumes `MarginEvent`** in production: `algo_library/deleverage_executor.py`.
- `venue_balance_tracker.py` itself is sports-bookmaker balance tracking (Betfair, Pinnacle) that reuses the same
  `PortfolioInputs`/`MarginModel` shapes from UTL for its own purposes — further evidence the core generalizes
  cleanly beyond DeFi/CeFi in practice, though sports capital tracking is not itself a "leverage" use case and is
  not in this doc's formal scope.

**What this means**: (B) is closer to done, more general, and already cross-service-wired than (A) — and than
this doc's own prior version assumed. Before extending anything (adding TradFi, wiring the two DeFi archetypes'
kill-gates, or building a new UTL extraction), **determine whether (A) and (B) are genuinely redundant** (does
(B)'s `MarginEvent` stream already carry everything an archetype's `on_tick()` gate would need — HF, LTV,
liquidation price, distance-to-liquidation, per-position not just per-portfolio?) and if so, **converge on (B)
and retire (A)** rather than fixing (A) in place and ending up with three overlapping paths. This determination
is P0, tracked in
[defi_leverage_archetypes_health_factor_wrong_source_2026_08_16](/plans/active/issues/defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md),
and must land before the live-feed-wiring todo that follows it.

## What counts as "leverage-capable"

An archetype needs this pattern if it posts collateral and/or borrows/trades against it in any asset group. It
does **not** need it for pure supply-side/LP positions (deposit capital, earn yield, no borrowing, no liquidation
exposure) — those archetypes correctly have no health/margin-style gate.

As of 2026-08-16, exactly two archetypes qualify for **DeFi** OWN-leverage risk gating: `CARRY_STAKED_BASIS`
(`staked_basis.py`, when its `LST_AS_MARGIN` structure posts the LST as real on-chain-derived perp margin) and
`CARRY_RECURSIVE_STAKED` (`recursive_staked.py`, a genuine `STAKE→LEND→BORROW→STAKE...` recursive loop).
`rotation_lending.py` and the `defi_lp/*.py` family are supply-side only and correctly excluded. **CeFi and
TradFi leverage-capable archetypes have not yet been inventoried against this same test** — that audit is
unclaimed work, not a stated-zero. Re-verify the DeFi list whenever a new DeFi archetype is added too — don't
assume it's still exactly these two.

**A second, related use case needs the same pattern**: archetypes that monitor OTHER wallets' health factor to
spot third-party liquidation opportunities — `arbitrage_structural/liquidation_capture.py` and
`mev/liquidation_bundle.py` — currently each reimplement the identical gate independently rather than sharing one.
The call shape differs (candidate-wallet parameter, not client-scoped), but it should route through the same
underlying module, not a third and fourth bespoke implementation. A purpose-built circuit breaker,
`strategy_service/circuit_breakers/liquidation_proximity_circuit.py`, has zero callers anywhere — **RULED
2026-08-18: wire it in, don't retire it.** It's complete, purpose-built code mapping 6 `AlertCode`s to graded
responses (flash-close, partial-unwind, position-pause, hedge-failover, oracle-buffer, mid-loop-recovery), and it
doesn't compete with mechanisms A/B — it's a downstream consumer of a `DefiAlert`, not another health-factor
source. The actual gap: nothing upstream emits a `DefiAlert` with one of its 6 codes yet. Full reasoning:
`/plans/active/strategy_service_centralization_fixes_2026_08_16.md`.

## Data model gaps (mechanism A; unverified for B)

`DeFiAggregatedHealth`/`ProtocolHealthBreakdown` (mechanism A's output) has no LTV, borrow-capacity, or
liquidation-price field; `PositionHealthSnapshot` has LTV and a liquidation threshold but the latter is hardcoded
to `MarginModel.AAVE_V3` rather than resolved per the position's actual protocol. **Whether `MarginEvent`
(mechanism B) already carries these fields has not been checked in this pass** — part of the reconciliation above.

## Mode-aware dispatch (target design, not yet built)

Once the reconciliation above lands and one callable/subscribable centralized path is confirmed, the read should
dispatch on execution mode, not fall back to one constant regardless of mode:

- **batch** — real historical data for the window being replayed.
- **live** — real-time poll/subscribe against the actual wallet or account.
- **paper-testnet** — poll a testnet protocol/venue deployment, validating the wiring end-to-end without touching
  production capital.
- **paper-live** — read-only poll of real conditions for the real wallet/account, without executing.

Do not design this dispatch before the reconciliation and the underlying centralized path are settled — sequencing
matters.

## What NOT to do

- Don't add a new bespoke poller or position-specific query inside features-service. Features-service computes
  generic, protocol/market-level data — the same shape every consumer can use regardless of who holds a position.
  Private per-position state belongs in strategy-service's position layer or execution-service, not there.
- Don't let a second or third leverage-capable archetype, in any asset group, copy
  `features.get("health_factor")` as precedent — `recursive_staked.py` did exactly this from `staked_basis.py`,
  deliberately, per its own docstring. Once the centralized path is confirmed, that's the thing to copy instead.
- **Don't build a TradFi (or any new) sourcing adapter against mechanism (A) `DeFiHealthAggregator`** just because
  it's the one this doc used to describe — verify against the reconciliation above first; mechanism (B) is the
  more likely correct extension point, since its core is already asset-group-agnostic and already cross-service.
- Don't assume either centralized module is complete just because it exists and is well-structured. Verify
  current state (which archetypes it's wired to, which fields it carries, which services actually consume it)
  before building on it — this doc's own prior version made exactly this mistake about mechanism (A) while never
  finding mechanism (B).
