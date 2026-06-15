---
title: v2 Engine + Venue Build-Out — 22 engineless archetypes + 9 unwired venues
created: 2026-06-15
parent_epic: strategy_master
assigned_vm: vm-trading-core
estimate_class: research
estimate_baseline_ai_days: 55.0
estimate_calibrated_ai_days: 66.0
locked_by: live-defi-rollout
locked_since: 2026-06-15
priority: P2
status: active
---

# v2 Engine + Venue Build-Out

> **Origin**: operator directive 2026-06-15 — after the F47/F48 audit established that the verdict matrix
> reports 22 archetypes + 17 venues as honestly `not_available` (zero engines built, RATIFY-only), the operator
> chose **build all** rather than accept the ratification. This plan decomposes that build-out into per-unit
> tracked todos. **Ground truth from the registry/matrix, NOT the operator's approximate "28+11"**:
> `strategy-service/.../engine/strategies/v2/factory.py:56-86` (29 archetypes registered) +
> `unified-api-contracts/openapi/capability-verdict-matrix.json` (the `not_available` set).

## HARD CONTRACT — real engine or honest absence (the rule that governs every engine todo)

**An archetype todo is DONE only when the engine is REAL**: genuine strategy logic (signal → legs/targets derived
from real features, not a passthrough), a **passing backtest artifact** via `GroupBRunner`
(`engine/strategies/v2/batch_harness.py`), unit tests asserting emitted instructions, registered in
`ARCHETYPE_ENGINE_REGISTRY`, and the verdict matrix regenerated to `available`.

**If the strategy needs data/venue plumbing that does not yet exist** (e.g. an options vol-surface / greeks feed for
the `VOL_*` family, or an L2 orderbook microstructure feed for `MARKET_MAKING_*`): the engine stays **honestly
`not_available` with a documented blocker** (a `BLOCKED-*` todo naming the missing dependency + the operator ask).
**NEVER register a hollow/stub engine to flip the matrix green** — a registered-but-empty engine makes the matrix
LIE (claims `available` with no real strategy), which is strictly worse than the honest `not_available` the ratify
decision deliberately preserved. This is the single most important rule in this plan.

Single-canonical (HARD): reuse the existing base (`BaseArchetypeEngineV2`), the existing families' patterns
(`ml_directional/continuous.py`, `carry_and_yield/staked_basis.py` are the templates), the UAC leg/capability
registries — never fork a parallel engine framework. No service↔service imports. Ship each unit via
`quickmerge --agent --files`. Never invent numbers.

## Phase V — Venue wiring (9 critical slot-token-unwired venues) — MECHANICAL, fully buildable

Each venue is DONE when it appears, consistently-cased, in EVERY SSOT a wired venue must occupy + the verdict
matrix stops rejecting it. Per-venue checklist (template = HYPERLIQUID): (1) `KNOWN_VENUE_TOKENS`
(UAC `internal/architecture_v2/venue_tokens.py`, alnum-stripped form); (2) `VENUE_CATEGORY_MAP` /
`venue_collateral.py` accept entry; (3) execution adapter exists (or scaffold + `BLOCKED-CREDENTIALS` per the
external-data rule — never silently defer); (4) leg eligibility (`archetype_leg_spec.py`); (5) capability registry
(`archetype_capability.py`); (6) regenerate + commit the verdict matrix; (7) `split_scope_tokens` no longer raises.

- [ ] [REGISTRY] P1. Wire **balancer_v2** through all 6 SSOTs + verdict matrix. Repo: unified-api-contracts (+ execution-service adapter if absent).
- [ ] [REGISTRY] P1. Wire **balancer_v3**. Repo: unified-api-contracts (+ execution-service).
- [ ] [REGISTRY] P1. Wire **sushiswap_v3**. Repo: unified-api-contracts (+ execution-service).
- [ ] [REGISTRY] P1. Wire **pancakeswap_v3**. Repo: unified-api-contracts (+ execution-service).
- [ ] [REGISTRY] P1. Wire **gmx_v2** (perp DEX — collateral + leg eligibility matter). Repo: unified-api-contracts (+ execution-service).
- [ ] [REGISTRY] P1. Wire **jupiter** (Solana aggregator). Repo: unified-api-contracts (+ execution-service).
- [ ] [REGISTRY] P1. Wire **sommelier**. Repo: unified-api-contracts (+ execution-service).
- [ ] [REGISTRY] P2. Wire **betfair_direct** (sports). Repo: unified-api-contracts (+ execution-service/sports adapter).
- [ ] [REGISTRY] P2. Wire **smarkets_direct** (sports). Repo: unified-api-contracts (+ execution-service/sports adapter).
- [ ] [REGISTRY] P2. Re-confirm against `capability-verdict-matrix.json` the EXACT unwired-venue set before building (the 6 registry-missing FX/BITFINEX/BITGET/KRAKEN + 2 TradFi NASDAQ/NYSE are a SEPARATE class — VENUE_CATEGORY_MAP gaps, F39/F42/F43 — fold them in if still open). Repo: unified-api-contracts.

## Phase E1 — MARKET_MAKING_* engines (5) — gated on an L2 orderbook microstructure feed

Each: confirm the feed exists; if yes build real + backtest + tests + register + matrix-flip; if no, honest `not_available` + blocker todo.

- [ ] [SCRIPT] P2. **MARKET_MAKING_PASSIVE_SPREAD** engine — real or honest-absent (needs L2 book). Repo: strategy-service.
- [ ] [SCRIPT] P2. **MARKET_MAKING_INVENTORY_SKEW** engine — real or honest-absent. Repo: strategy-service.
- [ ] [SCRIPT] P2. **MARKET_MAKING_QUEUE_MICROSTRUCTURE** engine — real or honest-absent (needs queue-position data). Repo: strategy-service.
- [ ] [SCRIPT] P3. **MARKET_MAKING_PREDICTION** engine — real or honest-absent. Repo: strategy-service.
- [ ] [SCRIPT] P3. **MARKET_MAKING_ML_LEAN** engine — real or honest-absent (needs the MM ML model variant). Repo: strategy-service.

## Phase E2 — VOL_* engines (17) — gated on an options vol-surface / greeks feed

`VOL_TRADING_OPTIONS` (engine #27) already exists as the base pattern. Each variant: confirm the options data
(vol surface, greeks, option chains from Deribit/options venues) exists; if yes build real + backtest + tests +
register + matrix-flip; if no, honest `not_available` + a single shared blocker todo for the missing options feed.

- [ ] [SCRIPT] P2. **VOL_STRADDLE** — real or honest-absent. Repo: strategy-service.
- [ ] [SCRIPT] P2. **VOL_VARIANCE_SWAP** — real or honest-absent. Repo: strategy-service.
- [ ] [SCRIPT] P2. **VOL_DISPERSION** — real or honest-absent. Repo: strategy-service.
- [ ] [SCRIPT] P2. **VOL_TERM_STRUCTURE_ARB** — real or honest-absent. Repo: strategy-service.
- [ ] [SCRIPT] P2. **VOL_TERM_STRUCTURE_SLOPE** — real or honest-absent. Repo: strategy-service.
- [ ] [SCRIPT] P2. **VOL_ARB_RV_IV** — real or honest-absent. Repo: strategy-service.
- [ ] [SCRIPT] P3. **VOL_0DTE_GAMMA_SCALPING** — real or honest-absent. Repo: strategy-service.
- [ ] [SCRIPT] P3. **VOL_CARRY** — real or honest-absent. Repo: strategy-service.
- [ ] [SCRIPT] P3. **VOL_CROSS_ASSET_SPREAD** — real or honest-absent. Repo: strategy-service.
- [ ] [SCRIPT] P3. **VOL_LEAPS_CONVEXITY** — real or honest-absent. Repo: strategy-service.
- [ ] [SCRIPT] P3. **VOL_MARKET_MAKING** — real or honest-absent. Repo: strategy-service.
- [ ] [SCRIPT] P3. **VOL_ML_LEAN** — real or honest-absent (needs the vol ML model variant). Repo: strategy-service.
- [ ] [SCRIPT] P3. **VOL_OVERLAY_COVERED_CALLS** — real or honest-absent. Repo: strategy-service.
- [ ] [SCRIPT] P3. **VOL_OVERLAY_PROTECTIVE_PUT** — real or honest-absent. Repo: strategy-service.
- [ ] [SCRIPT] P3. **VOL_RATIO_SPREAD** — real or honest-absent. Repo: strategy-service.
- [ ] [SCRIPT] P3. **VOL_SPREAD_STRUCTURES** — real or honest-absent. Repo: strategy-service.
- [ ] [SCRIPT] P3. **VOL_SYNTHETIC_DELTA** — real or honest-absent. Repo: strategy-service.

## Phase E0 — prerequisite data audit (BLOCKING gate for E1/E2) — ✅ DONE 2026-06-15

- [x] [SCRIPT] P1. ✅ **Audited the options vol-surface/greeks + L2 microstructure feeds.** VERDICT: **zero of the 22 engines are real-buildable today — the upstream data does not exist.** (a) VOL_* (17): `CanonicalOptionsChain` schema exists (instruments-service `reference_data/schemas.py:19-27`) but NO captured options data, NO `greeks_snapshot`/`implied_vol_surface` data_type (UAC `registry/data_type_capability.py`), only TradFi CME `options_chain` registered `live_capable=False`. (b) MARKET_MAKING_* (5): `book_snapshot_5` IS live-capable for CeFi (Binance/OKX/Bybit/Deribit/Coinbase/Upbit) but `queue_position`/`order_flow_imbalance`/deeper-L2 absent + features-service exposes no book-microstructure features to the engine. (c) `GroupBRunner.on_tick` is feature-agnostic (`dict[str,float]`) but receives an empty dict for vol/microstructure → no real backtest possible.

> **E0 VERDICT — the build-out is gated on a DATA-PIPELINE build, not strategy code.** Building any engine now
> would violate the real-or-honest-absent HARD CONTRACT (hollow engine, lying matrix). The real unlock is
> **Phase D below**. Until Phase D lands, all 22 engines stay honestly `not_available` with the blockers filed.

## Phase D — upstream data feeds (the REAL prerequisite that unblocks E1/E2)

Per the external-data-always-available rule, a missing feed is NOT a license to defer — it is a build (adapter
scaffold + UAC contract + manifest emission + unit tests on mocks; integration tests `@requires_credentials`) plus
a named operator credential ask. These are the engines' true predecessors.

- [ ] [SCRIPT] P1. **Build the options vol-surface + greeks feed** — register `greeks_snapshot` + `implied_vol_surface` (or `vol_surface`) data_types in UAC `data_type_capability.py`; add a live Deribit (+ other options-venue) options-chain + greeks adapter in instruments-service/MTDS; wire greeks-service to compute delta/gamma/vega/theta + IV surface; emit to features. Operator ask: confirm options-data source/credentials (Deribit public is free for chains; greeks computed in-house). Unblocks all 17 VOL_*. Repos: instruments-service + market-tick-data-service + greeks-service + unified-api-contracts.
- [ ] [SCRIPT] P2. **Extend the L2 microstructure feed** — register `queue_position` + `order_flow_imbalance` (+ `depth_of_book_10`) data_types; add MTDS WebSocket handlers; expose book-microstructure features (spread/imbalance/microprice) from `book_snapshot_5` in features-service. Unblocks MARKET_MAKING_PASSIVE_SPREAD + INVENTORY_SKEW first (L5-sufficient), then QUEUE_MICROSTRUCTURE (needs queue_position). Repos: market-tick-data-service + features-service + unified-api-contracts.

> **E1/E2 below are BLOCKED-DATA pending Phase D** — do not build until the corresponding feed lands.

## Codex SSOT updates

- [ ] [DOC] P2. If any engine family ships, update `codex/09-strategy/architecture-v2/archetypes/` with the new engine contracts + which remain honestly-absent and why.

## Progress Log

(loop handoff lands here — never a separate *_HANDOFF.md / *_SUMMARY.md)
