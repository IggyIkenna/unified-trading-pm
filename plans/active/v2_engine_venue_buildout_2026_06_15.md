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

> **Origin**: operator directive 2026-06-15 — after the F47/F48 audit established that the verdict matrix reports 22
> archetypes + 17 venues as honestly `not_available` (zero engines built, RATIFY-only), the operator chose **build all**
> rather than accept the ratification. This plan decomposes that build-out into per-unit tracked todos. **Ground truth
> from the registry/matrix, NOT the operator's approximate "28+11"**:
> `strategy-service/.../engine/strategies/v2/factory.py:56-86` (29 archetypes registered) +
> `unified-api-contracts/openapi/capability-verdict-matrix.json` (the `not_available` set).

## HARD CONTRACT — real engine or honest absence (the rule that governs every engine todo)

**An archetype todo is DONE only when the engine is REAL**: genuine strategy logic (signal → legs/targets derived from
real features, not a passthrough), a **passing backtest artifact** via `GroupBRunner`
(`engine/strategies/v2/batch_harness.py`), unit tests asserting emitted instructions, registered in
`ARCHETYPE_ENGINE_REGISTRY`, and the verdict matrix regenerated to `available`.

**If the strategy needs data/venue plumbing that does not yet exist** (e.g. an options vol-surface / greeks feed for the
`VOL_*` family, or an L2 orderbook microstructure feed for `MARKET_MAKING_*`): the engine stays **honestly
`not_available` with a documented blocker** (a `BLOCKED-*` todo naming the missing dependency + the operator ask).
**NEVER register a hollow/stub engine to flip the matrix green** — a registered-but-empty engine makes the matrix LIE
(claims `available` with no real strategy), which is strictly worse than the honest `not_available` the ratify decision
deliberately preserved. This is the single most important rule in this plan.

Single-canonical (HARD): reuse the existing base (`BaseArchetypeEngineV2`), the existing families' patterns
(`ml_directional/continuous.py`, `carry_and_yield/staked_basis.py` are the templates), the UAC leg/capability registries
— never fork a parallel engine framework. No service↔service imports. Ship each unit via `quickmerge --agent --files`.
Never invent numbers.

## Phase V — Venue wiring (9 critical slot-token-unwired venues) — MECHANICAL, fully buildable

Each venue is DONE when it appears, consistently-cased, in EVERY SSOT a wired venue must occupy + the verdict matrix
stops rejecting it. Per-venue checklist (template = HYPERLIQUID): (1) `KNOWN_VENUE_TOKENS` (UAC
`internal/architecture_v2/venue_tokens.py`, alnum-stripped form); (2) `VENUE_CATEGORY_MAP` / `venue_collateral.py`
accept entry; (3) execution adapter exists (or scaffold + `BLOCKED-CREDENTIALS` per the external-data rule — never
silently defer); (4) leg eligibility (`archetype_leg_spec.py`); (5) capability registry (`archetype_capability.py`); (6)
regenerate + commit the verdict matrix; (7) `split_scope_tokens` no longer raises.

- [x] ✅ [REGISTRY] P1. Wire **balancer_v2** through all 6 SSOTs + verdict matrix. Repo: unified-api-contracts. —
      UAC@7565c0c: token `balancerv2` added to `_DEFI_DEX_TOKENS`; verdict matrix regenerated (unbuildable-slot cleared,
      available 12977→14977); leg-eligible + capability already present; DEX swaps route via execution-service
      SwapHandler `BALANCER` protocol prefix. `split_scope_tokens(('balancerv2',…))` no longer raises.
- [x] ✅ [REGISTRY] P1. Wire **balancer_v3**. Repo: unified-api-contracts. — UAC@7565c0c: token `balancerv3` added;
      matrix cleared; SwapHandler `BALANCER` prefix.
- [x] ✅ [REGISTRY] P1. Wire **sushiswap_v3**. Repo: unified-api-contracts. — UAC@7565c0c: token `sushiswapv3` added;
      matrix cleared; DEX SwapHandler routing.
- [x] ✅ [REGISTRY] P1. Wire **pancakeswap_v3**. Repo: unified-api-contracts. — UAC@7565c0c: token `pancakeswapv3`
      added; matrix cleared; DEX SwapHandler routing.
- [x] ✅ [REGISTRY] P1. Wire **gmx_v2** (perp DEX — collateral + leg eligibility matter). Repo: unified-api-contracts. —
      UAC@7565c0c: token `gmxv2` added to `_DEFI_PERP_TOKENS`; matrix cleared; collateral covered by existing `GMX` rows
      in `venue_collateral.py` (those rows already describe GMX-V2 economics — no separate `gmx_v2` row; a lowercase
      `gmx_v2` collateral key fails `test_collateral_matrix_venues_are_known`, which keys on registry UPPERCASE
      `VENUE-CHAIN` names); leg-eligible already; GMX in execution-service DeFi/custody DEX venue set.
- [x] ✅ [REGISTRY] P1. Wire **jupiter** (Solana aggregator). Repo: unified-api-contracts. — UAC@7565c0c: token
      `jupiter` added to `_DEFI_DEX_TOKENS`; matrix cleared; `JupiterConnector` exists in execution-service
      `defi_execution/protocols/jupiter.py`.
- [x] ✅ [REGISTRY] P1. Wire **sommelier**. Repo: unified-api-contracts. — UAC@7565c0c: token `sommelier` added to
      `_DEFI_STAKING_TOKENS` (ERC-4626 yield-vault family); matrix cleared; leg-eligible (DEX_LP yield-vault seed
      `("yearn_v3","morpho","sommelier")`).
- [x] ✅ [REGISTRY] P2. Wire **betfair_direct** (sports). Repo: unified-api-contracts. — UAC@7565c0c: token
      `betfairdirect` added to `_SPORTS_TOKENS`; matrix cleared; `BetfairAdapter` + `betfair_direct` data-source live in
      execution-service `SportsExecutionRouter`.
- [x] ✅ [REGISTRY] P2. Wire **smarkets_direct** (sports). Repo: unified-api-contracts. — UAC@7565c0c: tokens
      `smarkets`+`smarketsdirect` added to `_SPORTS_TOKENS`; matrix cleared; leg-eligible. Token/matrix/leg-eligibility
      (this todo's verdict-matrix scope) COMPLETE. **Live execution adapter = BLOCKED-CREDENTIALS** (no Smarkets order
      path today — only Betfair/Matchbook adapters exist) → tracked in the [ADAPTER] todo below + ping
      `ikenna_orchestrator/pings/slot_1.md`.
- [ ] [REGISTRY] P2. Re-confirm against `capability-verdict-matrix.json` the EXACT unwired-venue set before building
      (the 6 registry-missing FX/BITFINEX/BITGET/KRAKEN + 2 TradFi NASDAQ/NYSE are a SEPARATE class — VENUE_CATEGORY_MAP
      gaps, F39/F42/F43 — fold them in if still open). Repo: unified-api-contracts.
- [ ] [ADAPTER] P2. **[BLOCKED-CREDENTIALS: Smarkets exchange API key + account]** Build the **Smarkets** live execution
      adapter in execution-service (`sports_execution/adapters/exchanges/smarkets.py` mirroring `matchbook.py` —
      OddsAdapter+BettingAdapter, session auth/retry, UAC `classify_venue_error()` + `ADAPTER_FETCH_FAILED`, add
      `smarkets_direct` to `SupportedDataSource` + `_build_smarkets` in `routing.py`) + UAC
      `external/smarkets/schemas.py` response models + `BOOKMAKER_REGISTRY["smarkets"]` (venue_manifest +
      provider_api_versions already carry `smarkets`); unit tests on mocks + integration tests
      `@pytest.mark.requires_credentials` (skipped by default). Repo: execution-service (+ unified-api-contracts
      schema). **Found 2026-06-15 (Phase V wiring)**: Smarkets is leg-eligible (`archetype_leg_spec_seeds`) + now
      token-wired in `KNOWN_VENUE_TOKENS`, but has NO execution order path today (only Betfair + Matchbook adapters
      exist; Smarkets has UAC reference data only). Status BLOCKED-CREDENTIALS per external-data-always-available rule —
      see ping `ikenna_orchestrator/pings/slot_1.md`. NOTE — `matchbook_direct` + `trader_joe` were ALSO surfaced as
      matrix-unbuildable and were token-wired in the SAME Phase V batch (the SSOT enumerated 11 unbuildable venues, not
      the transcribed 9); matchbook already has an execution adapter; trader_joe routes through the generic DEX
      SwapHandler — both fully clear, no adapter gap.

## Phase E1 — MARKET*MAKING*\* engines (5) — gated on an L2 orderbook microstructure feed

Each: confirm the feed exists; if yes build real + backtest + tests + register + matrix-flip; if no, honest
`not_available` + blocker todo.

- [ ] [SCRIPT] P2. **MARKET_MAKING_PASSIVE_SPREAD** engine — real or honest-absent (needs L2 book). Repo:
      strategy-service.
- [ ] [SCRIPT] P2. **MARKET_MAKING_INVENTORY_SKEW** engine — real or honest-absent. Repo: strategy-service.
- [ ] [SCRIPT] P2. **MARKET_MAKING_QUEUE_MICROSTRUCTURE** engine — real or honest-absent (needs queue-position data).
      Repo: strategy-service.
- [ ] [SCRIPT] P3. **MARKET_MAKING_PREDICTION** engine — real or honest-absent. Repo: strategy-service.
- [ ] [SCRIPT] P3. **MARKET_MAKING_ML_LEAN** engine — real or honest-absent (needs the MM ML model variant). Repo:
      strategy-service.

## Phase E2 — VOL\_\* engines (17) — gated on an options vol-surface / greeks feed

`VOL_TRADING_OPTIONS` (engine #27) already exists as the base pattern. Each variant: confirm the options data (vol
surface, greeks, option chains from Deribit/options venues) exists; if yes build real + backtest + tests + register +
matrix-flip; if no, honest `not_available` + a single shared blocker todo for the missing options feed.

- [ ] [SCRIPT] P2. **VOL_STRADDLE** — real engine SHIPPED (template wave).
  - code: strategy-service@62bc95af, unit-tested; **BACKTEST-PENDING** (needs Tardis historical per-strike surface).
    `VolStraddleEngine` (`engine/strategies/v2/vol_trading/straddle.py`): trades ATM-vol level — long straddle (BUY ATM
    call+put) when `iv_atm` cheap vs a realised-vol/term reference, short (SELL both) when rich; size = vega budget,
    scaled down by `max_position_vega`; legs = the two ATM option legs (delta-neutral at inception). Leg-derivation unit
    tests pin long-vs-short side + ATM selection + vega cap. **NOT registered** in `ARCHETYPE_ENGINE_REGISTRY` + verdict
    matrix UNCHANGED (no passing backtest → registering would make the matrix lie). **DVOL-vs-Tardis**: surface-dependent
    only at the per-strike level — straddle itself is ATM-only, but its backtest still needs the historical ATM-IV vs
    realised series; Deribit DVOL gives the implied index (ATM-proxy) credential-free but NOT the exact per-strike ATM
    option marks → Tardis preferred for a faithful backtest. No backfill run (operator constraint).
- [ ] [SCRIPT] P2. **VOL_VARIANCE_SWAP** — real engine SHIPPED (template wave).
  - code: strategy-service@64da164d, unit-tested; **BACKTEST-PENDING** (needs Tardis historical per-strike surface).
    `VolVarianceSwapEngine` (`engine/strategies/v2/vol_trading/variance_swap.py`): replicates variance exposure via a
    **1/K²-weighted OTM strip** (ATM anchor + 25d call wing + 25d put wing; each wing sized `variance_notional/moneyness²`
    so the deeper-relative-to-forward put wing carries MORE contracts — the canonical Demeterfi replication profile);
    trades long/short variance vs a surface-implied **fair-variance estimate** (`iv_atm²` lifted by a configurable skew
    convexity loading) compared to realised variance (`rv²`). Leg-derivation unit tests pin the 1/K² weights + side +
    fair-var-vs-realised. **NOT registered** + matrix UNCHANGED. **DVOL-vs-Tardis**: surface-dependent — the strip needs
    a historical **per-strike IV surface** (skew/wing IVs), which Deribit public history does NOT expose (mark-IV history
    pruned to ~1d, expired instruments empty) → **needs Tardis** for any backtest. No backfill run. **Feed-key gap
    flagged**: features-service exposes the surface as aggregated scalar buckets (`iv_atm`, `iv_25d_call/put`,
    `iv_skew_25d`, term) — NOT a per-strike IV-by-moneyness grid; the strip is built from the 3 canonical buckets. A
    denser strip needs a per-strike surface feature (not yet exposed).
- [ ] [SCRIPT] P2. **VOL_DISPERSION** — real or honest-absent. Repo: strategy-service.
- [ ] [SCRIPT] P2. **VOL_TERM_STRUCTURE_ARB** — real or honest-absent. Repo: strategy-service.
- [ ] [SCRIPT] P2. **VOL_TERM_STRUCTURE_SLOPE** — real or honest-absent. Repo: strategy-service.
- [ ] [SCRIPT] P2. **VOL_ARB_RV_IV** — real or honest-absent. Repo: strategy-service.
- [ ] [SCRIPT] P3. **VOL_0DTE_GAMMA_SCALPING** — real or honest-absent. Repo: strategy-service.
- [ ] [SCRIPT] P3. **VOL_CARRY** — real engine SHIPPED (template wave).
  - code: strategy-service@697e0641, unit-tested; **BACKTEST-PENDING** (but **DVOL-index-backtestable** — see note).
    `VolCarryEngine` (`engine/strategies/v2/vol_trading/carry.py`): harvests the volatility-risk-premium — when `iv_atm`
    exceeds realised vol (`rv`) by ≥ `entry_vrp` it **SELLS** the ATM straddle (short vol) + adds a **delta-hedge** leg
    on the underlying (units = `-package_delta`, sign-flipping with the delta sign; omitted on honest delta absence);
    **flattens** (buys the straddle back) when the carry inverts (`vrp ≤ exit_vrp`); holds while the premium persists.
    One-sided premium-harvest (only ever shorts vol), unlike the symmetric VOL_STRADDLE. Leg-derivation unit tests pin
    open/hold/flatten + the delta-hedge sign + honest-absence hedge omission. **NOT registered** + matrix UNCHANGED.
    **DVOL-vs-Tardis**: this is the ONE template-wave engine **backtestable from FREE Deribit DVOL history** — DVOL is
    the implied-vol index (ATM-proxy) back to 2021 credential-free and realised vol comes from the underlying close
    series, so `iv_atm - rv` carry needs NO per-strike surface. **Candidate for an early DVOL-index backtest greenlight**
    ahead of the surface-dependent VOL_STRADDLE/VARIANCE_SWAP (which need Tardis). No backfill run.
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

- [x] [SCRIPT] P1. ✅ **Audited the options vol-surface/greeks + L2 microstructure feeds.** VERDICT: **zero of the 22
      engines are real-buildable today — the upstream data does not exist.** (a) VOL*\* (17): `CanonicalOptionsChain`
      schema exists (instruments-service `reference_data/schemas.py:19-27`) but NO captured options data, NO
      `greeks_snapshot`/`implied_vol_surface` data_type (UAC `registry/data_type_capability.py`), only TradFi CME
      `options_chain` registered `live_capable=False`. (b) MARKET_MAKING*\* (5): `book_snapshot_5` IS live-capable for
      CeFi (Binance/OKX/Bybit/Deribit/Coinbase/Upbit) but `queue_position`/`order_flow_imbalance`/deeper-L2 absent +
      features-service exposes no book-microstructure features to the engine. (c) `GroupBRunner.on_tick` is
      feature-agnostic (`dict[str,float]`) but receives an empty dict for vol/microstructure → no real backtest
      possible.

> **E0 VERDICT — the build-out is gated on a DATA-PIPELINE build, not strategy code.** Building any engine now would
> violate the real-or-honest-absent HARD CONTRACT (hollow engine, lying matrix). The real unlock is **Phase D below**.
> Until Phase D lands, all 22 engines stay honestly `not_available` with the blockers filed.

## Phase D — upstream data feeds (the REAL prerequisite that unblocks E1/E2)

Per the external-data-always-available rule, a missing feed is NOT a license to defer — it is a build (adapter
scaffold + UAC contract + manifest emission + unit tests on mocks; integration tests `@requires_credentials`) plus a
named operator credential ask. These are the engines' true predecessors.

> **Operator decisions 2026-06-15 (source routing + constraint):**
>
> - **BUILD THE CODE + CONNECTIVITY-TEST IT (prove we can pull the data) — do NOT run backfills yet.** Backfills wait
>   for explicit go + (where applicable) the paid vendor.
> - **Live crypto options** → **Deribit public REST** (option chains + mark IV, free, no creds); **greeks computed
>   in-house** in greeks-service.
> - **Historical crypto options** → **Tardis** = **BLOCKED-CREDENTIALS** (scaffold the adapter + file the named ask; do
>   not backfill until [ack]). Use Deribit's own history only if it exposes it; otherwise wait for Tardis.
> - **TradFi options (historical)** → **Massive** (the existing TradFi route — extend it, don't add a new vendor).
>
> **BATCH == LIVE canonical-schema mapping (HARD — CLAUDE.md "Live = batch"):** every source is just an input to the
> SAME canonical pipeline. The live Deribit connector, the Tardis historical adapter, and the Massive TradFi route ALL
> map to the **identical canonical schema + data_types** (`CanonicalOptionsChain` /`options_chain`, `greeks_snapshot`,
> `implied_vol_surface`) — same fields, same units, `available_at` per-row at write-time. **NO live-only data_type, NO
> source-specific field set, NO read-time derivation.** Greeks/IV-surface output is the canonical
> `greeks_snapshot`/`implied_vol_surface` shape regardless of which source fed the chain. An engine reading the feed
> MUST NOT be able to tell live from batch. This is verified before any engine (E2) consumes it.

- [x] ✅ [SCRIPT] P1. **Build + connectivity-test the options vol-surface + greeks feed (NO backfill).** ALL of
      (a)+(b)+(c)+(d)+(e) shipped — see sub-bullets. batch==live holds end-to-end: Deribit live + Tardis historical +
      Massive TradFi all emit the IDENTICAL canonical `options_chain` (CanonicalOptionsChainEntry, IV fractional,
      source-tagged deribit/tardis/massive); greeks-service computes the canonical
      `greeks_snapshot`/`implied_vol_surface` from any of them; features-service exposes them as `dict[str,float]`. NO
      backfill run (operator constraint). Repos: unified-api-contracts@fcc01ac + instruments-service@99a320d +
      market-tick-data-service@4d32528 + greeks-service@0299b03 + features-service@73daa7fd. (a) UAC: register
      `greeks_snapshot` + `implied_vol_surface` + live-capable crypto `options_chain` data*types in
      `data_type_capability.py`. (b) instruments-service: Deribit public options-chain adapter (enumerate
      strikes/expiries → `CanonicalOptionsChain`) + a connectivity test proving a live pull. (c) MTDS: live
      options-chain + mark-IV handler (Deribit public); Tardis historical adapter SCAFFOLD = BLOCKED-CREDENTIALS (ping:
      ikenna_orchestrator/pings/slot_1.md); Massive for TradFi-options history. (d) greeks-service: in-house
      delta/gamma/vega/theta + IV-surface computation, wired + tested on a mock chain. (e) features-service: expose
      vol-surface/greeks features to the engine feature dict. Unblocks all 17 VOL*\*. Repos: unified-api-contracts +
      instruments-service + market-tick-data-service + greeks-service + features-service.
  - ✅ **part (b) — instruments-service Deribit public options-chain adapter** — instruments-service@99a320d.
    `DeribitOptionsReferenceDataAdapter` (`reference_data/adapters/cefi/deribit_options_adapter.py`, <100 lines logic)
    enumerates option instruments (strikes/expiries) for BTC/ETH/SOL/BNB/XRP via Deribit public
    `/public/get_instruments?kind=option` → `CanonicalOptionsChain` (calls/puts/strikes), and attaches venue mark IV
    (fractional) + underlying index mark via `/public/ticker`. Errors classified via UAC `classify_venue_error()` +
    `ADAPTER_FETCH_FAILED` emit; shard-level isolation per currency/leg; registered singleton in factory
    (`deribit_options`, `DERIBIT-OPTIONS`); no engine→adapter import. `CanonicalOptionsChain` extended with
    `mark_iv_by_instrument` + `underlying_mark` (schema-additive, SCHEMA_PROVENANCE_EXEMPT). Unit tests on MOCKED
    Deribit JSON (7 tests, run in QG `--block-network`). QG `--no-fix` exit 0. **CONNECTIVITY PROOF (live Deribit, ran
    2026-06-15 via `scripts/deribit_options_connectivity_check.py BTC`, exit 0):** BTC nearest expiry 2026-06-16T08:00Z,
    **23 strikes / 23 calls / 23 puts, 46 mark-IV legs, 11 distinct expiries**; underlying_mark 66849.03; sample mark_iv
    `BTC-16JUN26-56000-C → 0.9088` (90.88% annualised, fractional). NOT a backfill.
  - ✅ **part (a) — UAC canonical schemas + data_types + SOURCE_PRIORITY** — unified-api-contracts@fcc01ac. NEW
    `canonical/domain/derivatives/greeks.py`: `CanonicalGreeksSnapshot` (per-leg delta/gamma/vega/theta/rho + iv_used +
    iv_source), `CanonicalIVSurfacePoint` (field-for-field mirror of greeks-service `iv_surface.SurfacePoint` —
    single-canonical convergence, ONE shape both produce), `CanonicalImpliedVolSurface` (mirror of `IVSurface`;
    honest-absence empty `points`). Exported through derivatives/**init** → domain/**init** → root facade + both
    `__all__`s. `CanonicalOptionsChain` LEFT local in IS (SCHEMA_PROVENANCE_EXEMPT — IS reference-data public interface,
    not a cross-service domain contract; greeks-service consumes plain `OptionQuote`, never the IS type → no coupling
    forces promotion). data_type_capability: live-capable crypto `options_chain`/`greeks_snapshot`/`implied_vol_surface`
    (DERIBIT, live_capable=True); TradFi CME options_chain row UNCHANGED (live_capable=False). SOURCE_PRIORITY:
    `(cefi|tradfi, greeks_snapshot|implied_vol_surface) → ["greeks_service"]` (new COMPUTED_SOURCE); crypto
    `(cefi, options_chain)` KEEPS `["tardis"]` (tardis=BATCH primary, deribit=LIVE/REPLAY via venue-override —
    batch==live, same pattern as cefi trades); tradfi `(tradfi, options_chain)=["massive","databento"]` already present.
    New `greeks_service` source wired into COMPUTED_SOURCES + SOURCE_MODE_CAPABILITY {B,L,R} + EMISSION_LATENCY 0 +
    PipelineMode BATCH/LIVE/REPLAY_GREEKS_SERVICE + AVAILABILITY_AT_SEMANTICS tick_timestamp + validity-matrix
    COMPUTED_SERVICE_OUTPUT exclusions. Unit test (7 tests) + all SOURCE_PRIORITY/pipeline_mode/availability/capability
    round-trips green. QG `--no-fix` exit 0. **batch==live holds: live (Deribit) + historical (Tardis) + TradFi
    (Massive) all emit the IDENTICAL canonical options_chain/greeks_snapshot/implied_vol_surface — no live-only
    data_type, no source-specific field set.**
  - ✅ **part (c) — MTDS live options-chain + Tardis scaffold + Massive route** — market-tick-data-service@4d32528. (1)
    `cli/handlers/deribit_options_chain_handler.py` `DeribitOptionsChainHandler` (UnifiedServiceHandler +
    DefiManifestRecorder): records `source="deribit"`, `pipeline_mode=LIVE_DERIBIT`, per-currency/per-expiry shard
    isolation, `classify_venue_error("deribit",...)` + `ADAPTER_FETCH_FAILED`; Deribit `mark_iv` percent → /100
    fractional → canonical `options_chain` (`CanonicalOptionsChainEntry`). NO backfill run. (2) **CONNECTIVITY PROOF
    (real Deribit live, ran 2026-06-15T18:39Z, exit 0):** BTC nearest expiry 2026-06-16, 46 instruments — 23 strikes /
    23 calls / 23 puts; underlying_mark 66824.66; sample `BTC-16JUN26-56000-C` mark_iv 90.88% → 0.9088 fractional.
    Separate from the `--block-network` QG suite. NOT a backfill. (3) Tardis scaffold
    `market_interface/adapters/cefi/tardis_options_adapter.py` = BLOCKED-CREDENTIALS
    (`TardisOptionRow`+`normalise_tardis_option_row`→canonical entry, Tardis mark_iv already fractional;
    `TardisCredentialsNotConfiguredError` on no-key; mocked unit tests under `--block-network`, integration
    `@requires_credentials` skipped). Credential ask filed `ikenna_orchestrator/pings/slot_1.md` (source="tardis"). (4)
    Massive route `market_interface/adapters/tradfi/massive_tradfi_rest_connector.py` `_normalise_option_snapshot()`
    extended to emit `source="massive"` + canonical field names (symbol/strike/option_type/expiration) — existing vendor
    extended, no new vendor; fixed a pre-existing `classify_venue_error` 3-arg→2-arg bug. QG `--no-fix` exit 0.
  - ✅ **part (e) — features-service vol-surface/greeks features** — features-service@73daa7fd.
    `volatility/vol_surface_feature_extractor.py` + extended `volatility/schemas/feature_builder_registry.py` (group
    `vol_greeks_features`, sources `["greeks_snapshot","implied_vol_surface"]`).
    `extract_vol_greeks_feature_dict(surface, snapshots)` → flat `dict[str,float]` for a VOL\_\* engine `on_tick`. Keys:
    from `CanonicalImpliedVolSurface` → `iv_atm`, `iv_25d_call`, `iv_25d_put`, `iv_skew_25d`, `iv_term_1w/1m/3m/6m`,
    `iv_slope_1m_3m`; from `list[CanonicalGreeksSnapshot]` → `delta`, `gamma`, `vega`, `theta`, `rho` (rho only if a leg
    has non-None rho). HONEST ABSENCE: a bucket/leg with no data omits the key (never synthesised) — tested (OTM-only→no
    iv_atm; no-wings→no skew; single-tenor→no slope; all-rho-None→no rho). Pure transforms of canonical feed values (no
    invented numbers; no service↔service import — UAC types only). `formula_version=1` on all NEW features (no existing
    bump — no math change). 25 unit tests; QG exit 0.
  - 🔎 **Deribit PUBLIC-history probe (2026-06-15, live no-auth REST against `www.deribit.com/api/v2`) — does Deribit
    history alone let us backtest a VOL\_\* strategy credential-free? VERDICT: PARTIAL → Tardis still REQUIRED for the
    per-strike surface.** Real returned values:
    - **DVOL (`/public/get_volatility_index_data`) = DEEP, free.** BTC OHLC paged back to genesis **2021-03-24** (ETH
      first-page **2023-09-20**); resolutions `1`/`60`/`3600`/`43200`/`86400` (1m/1h/12h/1d) all return; 1000-row page
      cap + `continuation` token; sample row `[1738368000000, 53.32(o), 53.41(h), 51.05(l), 51.46(c)]`. ⇒ a
      **DVOL-index** time series back to 2021 is fully backtestable with NO creds.
    - **Per-strike option-mark history = NOT retrievable.** `/public/get_tradingview_chart_data` returns OHLC of an
      option's mark only for the **CURRENT live** instrument (BTC-31JUL26-90000-P → 169×60m bars from 2026-06-08); on an
      **expired** instrument (BTC-15JUN26-58000-C) → `status:no_data`, 0 rows.
    - **Trade-history (with per-trade `iv`) is PRUNED to ~1 day.** `/public/get_last_trades_by_currency_and_time` (BTC,
      kind=option, sorting=asc, 400-day window) → **oldest reachable trade 2026-06-14** (~1.0d retention, 14 pages,
      `has_more` exhausts at ~1d); every year-window 2020-2025 → 0 trades. Live trades DO carry `iv` (e.g.
      `BTC-31JUL26-80000-C iv=35.36`), so it's a retention limit, not a field gap.
    - **Expired instruments ARE listable** (`get_instruments?expired=true` → 44 BTC options) **but carry no usable
      history** — only same-settlement-day trades survive (11 of 12 expired strikes had 0 trades; the one had 4 trades
      all stamped today). Their per-strike chart/IV history is gone.
    - **`mark_iv` + full greeks (delta/gamma/vega/theta/rho) + bid/ask_iv exist on `/public/ticker` but are
      CURRENT-only** (live snapshot, no history endpoint).
    - **VERDICT — PARTIAL:** Deribit public history backtests the **DVOL-index archetypes** (vol-index timing / DVOL
      term-structure / vol-carry vs realised) to 2021 credential-free, but **CANNOT** reconstruct a historical
      **per-strike IV surface / skew / per-leg greeks** (mark-IV history pruned to ~1d, expired instruments empty). So
      the ~17 surface-dependent VOL\_\* engines (skew/RR/butterfly/dispersion/per-strike vega) **need Tardis** for
      history. **Tardis remains the route** for historical options backfill (the part-(c) `BLOCKED-CREDENTIALS` scaffold
      stands); Deribit public covers LIVE chains + DVOL only.
  - ✅ **part (d) — greeks-service in-house greeks + IV-surface assembler** — greeks-service@0299b03. In-house BS
    delta/gamma/vega/theta/rho (+ vanna/volga) + IV solver ALREADY existed (`kernels/black_scholes.py`, reused — not
    duplicated) with analytic ATM tests. NEW IV-surface assembler `kernels/iv_surface.py` (`assemble_iv_surface` →
    `IVSurface` of `SurfacePoint`s: IV by strike/moneyness x expiry/tenor-years from an option chain + underlying mark +
    per-leg mark IV; UTC datetimes; Decimal; fits IV in-house via `implied_vol_from_price` when only a mark price is
    present; honest-absence drops legs with no usable IV — no synthetic node). UNIT tests on KNOWN analytic cases (6
    tests): mark_iv passthrough, **fitted-IV round-trip recovers a known 20% vol to <1e-3** (priced via BS kernel then
    solved back), moneyness/tenor correctness, index grouping, honest-absence drop. QG `--no-fix` exit 0. No
    service↔service import (takes plain `OptionQuote` inputs, not the IS chain type). **Parts (a)+(c)+(e) now ALL landed
    (2026-06-15) — see sub-bullets above; the whole Phase D P1 todo is [x].**
- [ ] [SCRIPT] P2. **Build + connectivity-test the L2 microstructure feed (NO backfill).** Register `queue_position` +
      `order_flow_imbalance` (+ `depth_of_book_10`) data_types (UAC); MTDS WebSocket handler scaffolds
      (`book_snapshot_5` already live); expose book-microstructure features (spread/imbalance/microprice) from
      `book_snapshot_5` in features-service. Unblocks MARKET_MAKING_PASSIVE_SPREAD + INVENTORY_SKEW first
      (L5-sufficient), then QUEUE_MICROSTRUCTURE (needs queue_position). Repos: market-tick-data-service +
      features-service + unified-api-contracts.

> **E1/E2 below are BLOCKED-DATA pending Phase D** — do not build until the corresponding feed lands.

## Codex SSOT updates

- [ ] [DOC] P2. If any engine family ships, update `codex/09-strategy/architecture-v2/archetypes/` with the new engine
      contracts + which remain honestly-absent and why.

## Progress Log

(loop handoff lands here — never a separate _\_HANDOFF.md / _\_SUMMARY.md)

### 2026-06-15 — Phase D P1 (a)+(c)+(e) [in progress]

**Canonical schema settled (single-canonical, converges with greeks-service@0299b03):**

- New UAC file `canonical/domain/derivatives/greeks.py`: `CanonicalGreeksSnapshot` (per-leg greeks:
  delta/gamma/vega/theta/rho + iv_used + iv_source), `CanonicalIVSurfacePoint` (mirrors greeks-service
  `iv_surface.SurfacePoint` field-for-field:
  instrument_key/strike/expiry/right/moneyness/tenor_years/implied_vol/iv_source), `CanonicalImpliedVolSurface` (mirrors
  `IVSurface`: underlying/venue/underlying_mark/as_of/points). greeks-service's local dataclasses are
  SCHEMA_PROVENANCE_EXEMPT in-memory kernel I/O; the UAC types are the wire/manifest shape the assembled surface
  serialises to — ONE shape, no divergence. Exported through derivatives/**init** → domain/**init** → root facade + both
  **all**s.
- `CanonicalOptionsChain` provenance decision: LEFT local in instruments-service with its `SCHEMA_PROVENANCE_EXEMPT`
  note (it is the IS reference-data public interface, folded from unified-reference-data-interface — service-specific,
  not a general domain contract crossing a service boundary; greeks-service consumes plain OptionQuote inputs, never the
  IS chain type, so no cross-service coupling forces promotion). The canonical CONVERGENCE point is the
  greeks_snapshot/implied_vol_surface output, which IS now in UAC. Noted reason per schema-provenance rule.

**(a) UAC data_types + SOURCE_PRIORITY registered:**

- `data_type_capability.py`: live-capable crypto `options_chain` (DERIBIT, live_capable=True), `greeks_snapshot`
  (DERIBIT), `implied_vol_surface` (DERIBIT) — all live+batch. TradFi CME options_chain row UNCHANGED
  (live_capable=False).
- SOURCE_PRIORITY: `(cefi, greeks_snapshot)`/`(cefi, implied_vol_surface)`/`(tradfi, greeks_snapshot)`/
  `(tradfi, implied_vol_surface)` → `["greeks_service"]` (new COMPUTED_SOURCE). Crypto `options_chain` KEEPS
  `(cefi, options_chain): ["tardis"]` — tardis=BATCH primary, deribit=LIVE/REPLAY via venue-override (SAME pattern as
  cefi trades → batch==live preserved; deribit is NOT index-0 because it is live/replay-only). TradFi
  `(tradfi, options_chain): ["massive","databento"]` already present (Massive route). New `greeks_service` source:
  COMPUTED_SOURCES + SOURCE_MODE_CAPABILITY {BATCH,LIVE,REPLAY} + EMISSION_LATENCY 0 + PipelineMode
  BATCH/LIVE/REPLAY_GREEKS_SERVICE + validity-matrix exclusion (COMPUTED_SERVICE_OUTPUT x4). Unit test
  `test_greeks_snapshot_schema.py` (7 tests: exports, field parity with SurfacePoint, honest-absence, iv provenance,
  batch==live identical dump, extra-forbid).

**STILL TODO this session:** UAC QG green + quickmerge; (c) MTDS live handler + connectivity test + Tardis scaffold
(BLOCKED-CREDENTIALS ping) + Massive route; (e) features-service vol/greeks features.

### 2026-06-15 — Phase D P1 (a)+(c)+(e) ALL DONE — whole P1 todo flipped [x]

All five parts (a-e) landed; the Phase D P1 feed prereq for the 17 VOL*\* engines is COMPLETE (code + connectivity-test;
NO backfill per operator constraint). Shipped: UAC@fcc01ac (a), instruments-service@99a320d (b, prior), MTDS@4d32528
(c), greeks-service@0299b03 (d, prior), features-service@73daa7fd (e). batch==live VERIFIED: Deribit live + Tardis
historical (BLOCKED-CREDENTIALS scaffold) + Massive TradFi all emit the IDENTICAL canonical `options_chain`;
greeks-service computes the canonical `greeks_snapshot`/`implied_vol_surface` regardless of source; features-service
exposes them as `dict[str,float]`. Real Deribit connectivity proof captured (BTC 23/23/23 legs, mark_iv 0.9088
fractional). Tardis credential ask filed `ikenna_orchestrator/pings/slot_1.md`. NO divergence from batch==live was
forced. NOTE: a concurrent agent had also landed prior `slot_1.md` content; the Tardis ask was mis-filed by a sub-agent
to `rootm_orchestrator/pings/slot_1.md` and was migrated to the canonical `ikenna_orchestrator/pings/slot_1.md` (rootm
file deleted). The VOL*_/MARKET*MAKING*_ engine builds (Phase E1/E2) remain BLOCKED-DATA→now-unblocked-for-VOL\_\* — a
separate later wave, NOT in this (a)+(c)+(e) scope.

## Follow-ups discovered during Phase D / template wave (2026-06-15)

- [ ] [SCRIPT] P2. **Bump cryptography fleet-wide off the GHSA-537c-gmf6-5ccf line + drop its --ignore-vuln** — the 2026-06-15 advisory flagged cryptography 46.0.7 (statically-linked OpenSSL). Unlike aiohttp it is NOT vcrpy-deadlocked, so the PROPER fix is a floor bump + per-repo `uv lock` regen, not a permanent ignore. The ignore (PM base-service.sh + base-library.sh, PM@e6c7b52c9) is the transient speed>security unblock. Repos: fleet-wide (all repos declaring cryptography transitively) + remove the GHSA ignore from both base-*.sh once bumped.
- [ ] [SCRIPT] P3. **Ratchet DOWN the MTDS DTZ + fallback-import baselines** — after the DTZ noqa fix, MTDS is below both `ruff_rule_ratchet_baseline.yaml` (32) and `no_fallback_imports_baseline.yaml` (3); re-run `--update-baseline` for market-tick-data-service. Repo: unified-trading-pm.
