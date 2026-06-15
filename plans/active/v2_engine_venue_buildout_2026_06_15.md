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

- [x] ✅ [REGISTRY] P1. Wire **balancer_v2** through all 6 SSOTs + verdict matrix. Repo: unified-api-contracts. — UAC@7565c0c: token `balancerv2` added to `_DEFI_DEX_TOKENS`; verdict matrix regenerated (unbuildable-slot cleared, available 12977→14977); leg-eligible + capability already present; DEX swaps route via execution-service SwapHandler `BALANCER` protocol prefix. `split_scope_tokens(('balancerv2',…))` no longer raises.
- [x] ✅ [REGISTRY] P1. Wire **balancer_v3**. Repo: unified-api-contracts. — UAC@7565c0c: token `balancerv3` added; matrix cleared; SwapHandler `BALANCER` prefix.
- [x] ✅ [REGISTRY] P1. Wire **sushiswap_v3**. Repo: unified-api-contracts. — UAC@7565c0c: token `sushiswapv3` added; matrix cleared; DEX SwapHandler routing.
- [x] ✅ [REGISTRY] P1. Wire **pancakeswap_v3**. Repo: unified-api-contracts. — UAC@7565c0c: token `pancakeswapv3` added; matrix cleared; DEX SwapHandler routing.
- [x] ✅ [REGISTRY] P1. Wire **gmx_v2** (perp DEX — collateral + leg eligibility matter). Repo: unified-api-contracts. — UAC@7565c0c: token `gmxv2` added to `_DEFI_PERP_TOKENS`; matrix cleared; collateral covered by existing `GMX` rows in `venue_collateral.py` (those rows already describe GMX-V2 economics — no separate `gmx_v2` row; a lowercase `gmx_v2` collateral key fails `test_collateral_matrix_venues_are_known`, which keys on registry UPPERCASE `VENUE-CHAIN` names); leg-eligible already; GMX in execution-service DeFi/custody DEX venue set.
- [x] ✅ [REGISTRY] P1. Wire **jupiter** (Solana aggregator). Repo: unified-api-contracts. — UAC@7565c0c: token `jupiter` added to `_DEFI_DEX_TOKENS`; matrix cleared; `JupiterConnector` exists in execution-service `defi_execution/protocols/jupiter.py`.
- [x] ✅ [REGISTRY] P1. Wire **sommelier**. Repo: unified-api-contracts. — UAC@7565c0c: token `sommelier` added to `_DEFI_STAKING_TOKENS` (ERC-4626 yield-vault family); matrix cleared; leg-eligible (DEX_LP yield-vault seed `("yearn_v3","morpho","sommelier")`).
- [x] ✅ [REGISTRY] P2. Wire **betfair_direct** (sports). Repo: unified-api-contracts. — UAC@7565c0c: token `betfairdirect` added to `_SPORTS_TOKENS`; matrix cleared; `BetfairAdapter` + `betfair_direct` data-source live in execution-service `SportsExecutionRouter`.
- [x] ✅ [REGISTRY] P2. Wire **smarkets_direct** (sports). Repo: unified-api-contracts. — UAC@7565c0c: tokens `smarkets`+`smarketsdirect` added to `_SPORTS_TOKENS`; matrix cleared; leg-eligible. Token/matrix/leg-eligibility (this todo's verdict-matrix scope) COMPLETE. **Live execution adapter = BLOCKED-CREDENTIALS** (no Smarkets order path today — only Betfair/Matchbook adapters exist) → tracked in the [ADAPTER] todo below + ping `ikenna_orchestrator/pings/slot_1.md`.
- [ ] [REGISTRY] P2. Re-confirm against `capability-verdict-matrix.json` the EXACT unwired-venue set before building (the 6 registry-missing FX/BITFINEX/BITGET/KRAKEN + 2 TradFi NASDAQ/NYSE are a SEPARATE class — VENUE_CATEGORY_MAP gaps, F39/F42/F43 — fold them in if still open). Repo: unified-api-contracts.
- [ ] [ADAPTER] P2. **[BLOCKED-CREDENTIALS: Smarkets exchange API key + account]** Build the **Smarkets** live execution adapter in execution-service (`sports_execution/adapters/exchanges/smarkets.py` mirroring `matchbook.py` — OddsAdapter+BettingAdapter, session auth/retry, UAC `classify_venue_error()` + `ADAPTER_FETCH_FAILED`, add `smarkets_direct` to `SupportedDataSource` + `_build_smarkets` in `routing.py`) + UAC `external/smarkets/schemas.py` response models + `BOOKMAKER_REGISTRY["smarkets"]` (venue_manifest + provider_api_versions already carry `smarkets`); unit tests on mocks + integration tests `@pytest.mark.requires_credentials` (skipped by default). Repo: execution-service (+ unified-api-contracts schema). **Found 2026-06-15 (Phase V wiring)**: Smarkets is leg-eligible (`archetype_leg_spec_seeds`) + now token-wired in `KNOWN_VENUE_TOKENS`, but has NO execution order path today (only Betfair + Matchbook adapters exist; Smarkets has UAC reference data only). Status BLOCKED-CREDENTIALS per external-data-always-available rule — see ping `ikenna_orchestrator/pings/slot_1.md`. NOTE — `matchbook_direct` + `trader_joe` were ALSO surfaced as matrix-unbuildable and were token-wired in the SAME Phase V batch (the SSOT enumerated 11 unbuildable venues, not the transcribed 9); matchbook already has an execution adapter; trader_joe routes through the generic DEX SwapHandler — both fully clear, no adapter gap.

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

> **Operator decisions 2026-06-15 (source routing + constraint):**
> - **BUILD THE CODE + CONNECTIVITY-TEST IT (prove we can pull the data) — do NOT run backfills yet.** Backfills
>   wait for explicit go + (where applicable) the paid vendor.
> - **Live crypto options** → **Deribit public REST** (option chains + mark IV, free, no creds); **greeks computed
>   in-house** in greeks-service.
> - **Historical crypto options** → **Tardis** = **BLOCKED-CREDENTIALS** (scaffold the adapter + file the named
>   ask; do not backfill until [ack]). Use Deribit's own history only if it exposes it; otherwise wait for Tardis.
> - **TradFi options (historical)** → **Massive** (the existing TradFi route — extend it, don't add a new vendor).
>
> **BATCH == LIVE canonical-schema mapping (HARD — CLAUDE.md "Live = batch"):** every source is just an input to
> the SAME canonical pipeline. The live Deribit connector, the Tardis historical adapter, and the Massive TradFi
> route ALL map to the **identical canonical schema + data_types** (`CanonicalOptionsChain` /`options_chain`,
> `greeks_snapshot`, `implied_vol_surface`) — same fields, same units, `available_at` per-row at write-time. **NO
> live-only data_type, NO source-specific field set, NO read-time derivation.** Greeks/IV-surface output is the
> canonical `greeks_snapshot`/`implied_vol_surface` shape regardless of which source fed the chain. An engine reading
> the feed MUST NOT be able to tell live from batch. This is verified before any engine (E2) consumes it.

- [ ] [SCRIPT] P1. **Build + connectivity-test the options vol-surface + greeks feed (NO backfill).** (a) UAC: register `greeks_snapshot` + `implied_vol_surface` + live-capable crypto `options_chain` data_types in `data_type_capability.py`. (b) instruments-service: Deribit public options-chain adapter (enumerate strikes/expiries → `CanonicalOptionsChain`) + a connectivity test proving a live pull. (c) MTDS: live options-chain + mark-IV handler (Deribit public); Tardis historical adapter SCAFFOLD = BLOCKED-CREDENTIALS (ping: ikenna_orchestrator/pings/slot_7.md); Massive for TradFi-options history. (d) greeks-service: in-house delta/gamma/vega/theta + IV-surface computation, wired + tested on a mock chain. (e) features-service: expose vol-surface/greeks features to the engine feature dict. Unblocks all 17 VOL_*. Repos: unified-api-contracts + instruments-service + market-tick-data-service + greeks-service + features-service.
  - ✅ **part (b) — instruments-service Deribit public options-chain adapter** — instruments-service@99a320d. `DeribitOptionsReferenceDataAdapter` (`reference_data/adapters/cefi/deribit_options_adapter.py`, <100 lines logic) enumerates option instruments (strikes/expiries) for BTC/ETH/SOL/BNB/XRP via Deribit public `/public/get_instruments?kind=option` → `CanonicalOptionsChain` (calls/puts/strikes), and attaches venue mark IV (fractional) + underlying index mark via `/public/ticker`. Errors classified via UAC `classify_venue_error()` + `ADAPTER_FETCH_FAILED` emit; shard-level isolation per currency/leg; registered singleton in factory (`deribit_options`, `DERIBIT-OPTIONS`); no engine→adapter import. `CanonicalOptionsChain` extended with `mark_iv_by_instrument` + `underlying_mark` (schema-additive, SCHEMA_PROVENANCE_EXEMPT). Unit tests on MOCKED Deribit JSON (7 tests, run in QG `--block-network`). QG `--no-fix` exit 0. **CONNECTIVITY PROOF (live Deribit, ran 2026-06-15 via `scripts/deribit_options_connectivity_check.py BTC`, exit 0):** BTC nearest expiry 2026-06-16T08:00Z, **23 strikes / 23 calls / 23 puts, 46 mark-IV legs, 11 distinct expiries**; underlying_mark 66849.03; sample mark_iv `BTC-16JUN26-56000-C → 0.9088` (90.88% annualised, fractional). NOT a backfill.
  - ✅ **part (a) — UAC canonical schemas + data_types + SOURCE_PRIORITY** — unified-api-contracts@fcc01ac. NEW `canonical/domain/derivatives/greeks.py`: `CanonicalGreeksSnapshot` (per-leg delta/gamma/vega/theta/rho + iv_used + iv_source), `CanonicalIVSurfacePoint` (field-for-field mirror of greeks-service `iv_surface.SurfacePoint` — single-canonical convergence, ONE shape both produce), `CanonicalImpliedVolSurface` (mirror of `IVSurface`; honest-absence empty `points`). Exported through derivatives/__init__ → domain/__init__ → root facade + both `__all__`s. `CanonicalOptionsChain` LEFT local in IS (SCHEMA_PROVENANCE_EXEMPT — IS reference-data public interface, not a cross-service domain contract; greeks-service consumes plain `OptionQuote`, never the IS type → no coupling forces promotion). data_type_capability: live-capable crypto `options_chain`/`greeks_snapshot`/`implied_vol_surface` (DERIBIT, live_capable=True); TradFi CME options_chain row UNCHANGED (live_capable=False). SOURCE_PRIORITY: `(cefi|tradfi, greeks_snapshot|implied_vol_surface) → ["greeks_service"]` (new COMPUTED_SOURCE); crypto `(cefi, options_chain)` KEEPS `["tardis"]` (tardis=BATCH primary, deribit=LIVE/REPLAY via venue-override — batch==live, same pattern as cefi trades); tradfi `(tradfi, options_chain)=["massive","databento"]` already present. New `greeks_service` source wired into COMPUTED_SOURCES + SOURCE_MODE_CAPABILITY {B,L,R} + EMISSION_LATENCY 0 + PipelineMode BATCH/LIVE/REPLAY_GREEKS_SERVICE + AVAILABILITY_AT_SEMANTICS tick_timestamp + validity-matrix COMPUTED_SERVICE_OUTPUT exclusions. Unit test (7 tests) + all SOURCE_PRIORITY/pipeline_mode/availability/capability round-trips green. QG `--no-fix` exit 0. **batch==live holds: live (Deribit) + historical (Tardis) + TradFi (Massive) all emit the IDENTICAL canonical options_chain/greeks_snapshot/implied_vol_surface — no live-only data_type, no source-specific field set.**
  - ✅ **part (d) — greeks-service in-house greeks + IV-surface assembler** — greeks-service@0299b03. In-house BS delta/gamma/vega/theta/rho (+ vanna/volga) + IV solver ALREADY existed (`kernels/black_scholes.py`, reused — not duplicated) with analytic ATM tests. NEW IV-surface assembler `kernels/iv_surface.py` (`assemble_iv_surface` → `IVSurface` of `SurfacePoint`s: IV by strike/moneyness x expiry/tenor-years from an option chain + underlying mark + per-leg mark IV; UTC datetimes; Decimal; fits IV in-house via `implied_vol_from_price` when only a mark price is present; honest-absence drops legs with no usable IV — no synthetic node). UNIT tests on KNOWN analytic cases (6 tests): mark_iv passthrough, **fitted-IV round-trip recovers a known 20% vol to <1e-3** (priced via BS kernel then solved back), moneyness/tenor correctness, index grouping, honest-absence drop. QG `--no-fix` exit 0. No service↔service import (takes plain `OptionQuote` inputs, not the IS chain type). **Parts (a) UAC data_types / (c) MTDS handler+Tardis scaffold / (e) features-service remain — separate later wave (concurrent agent owns UAC).**
- [ ] [SCRIPT] P2. **Build + connectivity-test the L2 microstructure feed (NO backfill).** Register `queue_position` + `order_flow_imbalance` (+ `depth_of_book_10`) data_types (UAC); MTDS WebSocket handler scaffolds (`book_snapshot_5` already live); expose book-microstructure features (spread/imbalance/microprice) from `book_snapshot_5` in features-service. Unblocks MARKET_MAKING_PASSIVE_SPREAD + INVENTORY_SKEW first (L5-sufficient), then QUEUE_MICROSTRUCTURE (needs queue_position). Repos: market-tick-data-service + features-service + unified-api-contracts.

> **E1/E2 below are BLOCKED-DATA pending Phase D** — do not build until the corresponding feed lands.

## Codex SSOT updates

- [ ] [DOC] P2. If any engine family ships, update `codex/09-strategy/architecture-v2/archetypes/` with the new engine contracts + which remain honestly-absent and why.

## Progress Log

(loop handoff lands here — never a separate *_HANDOFF.md / *_SUMMARY.md)

### 2026-06-15 — Phase D P1 (a)+(c)+(e) [in progress]

**Canonical schema settled (single-canonical, converges with greeks-service@0299b03):**
- New UAC file `canonical/domain/derivatives/greeks.py`: `CanonicalGreeksSnapshot` (per-leg
  greeks: delta/gamma/vega/theta/rho + iv_used + iv_source), `CanonicalIVSurfacePoint`
  (mirrors greeks-service `iv_surface.SurfacePoint` field-for-field:
  instrument_key/strike/expiry/right/moneyness/tenor_years/implied_vol/iv_source),
  `CanonicalImpliedVolSurface` (mirrors `IVSurface`: underlying/venue/underlying_mark/as_of/points).
  greeks-service's local dataclasses are SCHEMA_PROVENANCE_EXEMPT in-memory kernel I/O; the
  UAC types are the wire/manifest shape the assembled surface serialises to — ONE shape, no divergence.
  Exported through derivatives/__init__ → domain/__init__ → root facade + both __all__s.
- `CanonicalOptionsChain` provenance decision: LEFT local in instruments-service with its
  `SCHEMA_PROVENANCE_EXEMPT` note (it is the IS reference-data public interface, folded from
  unified-reference-data-interface — service-specific, not a general domain contract crossing a
  service boundary; greeks-service consumes plain OptionQuote inputs, never the IS chain type, so
  no cross-service coupling forces promotion). The canonical CONVERGENCE point is the
  greeks_snapshot/implied_vol_surface output, which IS now in UAC. Noted reason per schema-provenance rule.

**(a) UAC data_types + SOURCE_PRIORITY registered:**
- `data_type_capability.py`: live-capable crypto `options_chain` (DERIBIT, live_capable=True),
  `greeks_snapshot` (DERIBIT), `implied_vol_surface` (DERIBIT) — all live+batch. TradFi CME
  options_chain row UNCHANGED (live_capable=False).
- SOURCE_PRIORITY: `(cefi, greeks_snapshot)`/`(cefi, implied_vol_surface)`/`(tradfi, greeks_snapshot)`/
  `(tradfi, implied_vol_surface)` → `["greeks_service"]` (new COMPUTED_SOURCE). Crypto `options_chain`
  KEEPS `(cefi, options_chain): ["tardis"]` — tardis=BATCH primary, deribit=LIVE/REPLAY via venue-override
  (SAME pattern as cefi trades → batch==live preserved; deribit is NOT index-0 because it is live/replay-only).
  TradFi `(tradfi, options_chain): ["massive","databento"]` already present (Massive route).
  New `greeks_service` source: COMPUTED_SOURCES + SOURCE_MODE_CAPABILITY {BATCH,LIVE,REPLAY} +
  EMISSION_LATENCY 0 + PipelineMode BATCH/LIVE/REPLAY_GREEKS_SERVICE + validity-matrix exclusion
  (COMPUTED_SERVICE_OUTPUT x4). Unit test `test_greeks_snapshot_schema.py` (7 tests: exports, field
  parity with SurfacePoint, honest-absence, iv provenance, batch==live identical dump, extra-forbid).

**STILL TODO this session:** UAC QG green + quickmerge; (c) MTDS live handler + connectivity test +
Tardis scaffold (BLOCKED-CREDENTIALS ping) + Massive route; (e) features-service vol/greeks features.
