---
doc_type: issue
title:
  DeFi strategy archetypes have no operator venue/currency curtailment lever; two unreconciled universe registries; one
  dead allow-list field
summary:
  A full per-archetype universe audit (19 DeFi/carry archetypes) found production decision logic exists for all of them,
  but there is no existing mechanism to constrain which venues/base-currencies a strategy config considers without
  editing catalog source; a plausible-looking allowed_venues config field is dead code; strategy-service's catalog and
  UAC's archetype_leg_spec_seeds describe the same domain with no cross-check.
status: open
nature: issue
asset_group: defi
stage: strategy
repos: [strategy-service, unified-api-contracts, unified-trading-pm]
scope: engineer
tags: [defi, strategy-archetypes, universe-constraint, dead-code, ssot-drift]
related:
  [
    pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21,
    e2e_testing_collateral_validation_dead_import_2026_07_23,
  ]
created: 2026-07-23
parent_epic: strategy_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.2
assigned_role: NA
drift_direction: NA
resolved_by:
locked_by:
source: agent-discovered (per-archetype DeFi universe mapping audit, 2026-07-23)
depends_on: []
---

# DeFi strategy archetype universe — no curtailment mechanism, two unreconciled registries, one dead field

## Context

Operator asked (2026-07-23) to map, per DeFi strategy archetype: base currency/underlying universe, staking venues,
lending/borrowing venues, trading venues, and data_type/instrument_type requirements — then wanted to know whether
production already has explicit decision logic for these, so venues/currencies could be **curtailed (constrained)** per
strategy config **without changing the archetype's decision/ranking logic**. Full per-archetype table is in the
2026-07-23 chat record (19 archetypes across `catalog_carry.py`/`catalog_staked_basis.py`/`catalog_yield_defi.py`/
`catalog_trading.py`); this doc captures the three findings that need a decision, not the full table.

**Headline answer:** all 19 DeFi/carry archetypes have real, registered v2 engines (`factory.py:59-92`) and an explicit,
hardcoded universe per archetype (tuples/lists in the catalog files) — so the "does production have the decision logic"
half is YES. The "can we curtail it today" half is NO — nothing operator-facing exists.

## Finding 1 — no venue/currency curtailment mechanism exists in production

Checked three layers, all insufficient:

- `TargetInstanceSpec` (`specs.py`) — flat, frozen dataclass, no allow-list field. Narrowing today means editing catalog
  source.
- `PaperUniverseConfig.archetypes` (`paper_run_handler.py`/`paper_universe.py`) — the closest existing lever, but it's
  **whole-archetype** granularity (not venue/currency within one), and it is **not wired to any CLI/operator surface** —
  `service_entry.py` calls `run_paper(...)` without ever passing `universe_config`, so production always runs the full
  default universe.
- Portfolio allocator (`guard_rails.py`, `archetypes_rank.py`) — caps by family/category and by economic threshold
  (`min_apy_bps`, `top_n`), not by venue/currency identity. Cannot express "only Lido + Deribit regardless of current
  economics."

**Design sketch (not yet built, needs a scoping decision):** the natural plug-in point is a post-filter applied
inside/after `specs_for_archetype()` — every archetype with a real enumerable universe already carries venue/currency
identity as literal `initial_config` keys (`staking_venue`, `lending_venue`, `perp_venue`, `spot_venue`, `chain`,
`native_asset`/`asset`/`coin`), so a generic `(archetype, config-key) → allowed-values` filter can drop non-conforming
specs before the allocator/paper-drivability gate ever sees them — the same shape as the existing
`_skip_reason_for_spec` honest-skip pattern in `paper_universe.py`, just a new skip reason
(`curtailed_by_operator_constraint`). Extending `PaperUniverseConfig` with a `venue_allowlist`/
`base_currency_allowlist` sibling field (next to the already-designed-but-unwired `archetypes` field) reuses an existing
extension point rather than inventing a new one.

**Known limitation — flag before building:** `ARBITRAGE_MEV_LIQUIDATION_BUNDLE` and `ARBITRAGE_MEV_BACKRUN` have NO
catalog-declared base-currency/instrument universe at all (`candidate_ids: ""`, opportunistic mempool/liquidation-feed
driven) — a catalog-level allow-list has nothing to filter on for their currency axis. A currency constraint for these
two would need new runtime logic inside the engines themselves. Building only the catalog-level filter and assuming it
covers all 19 archetypes would be a real, silent gap for these two.

## Finding 2 — `SmartOrderRoutingConfig.allowed_venues` is dead code that looks like exactly this feature

`strategy_service/engine/core/config_loader.py:145-160`, `strategy_service/types.py:80-103`
(`DeFiSORConfigDict.allowed_venues`), documented in `docs/CONFIG_SCHEMA.md:167-172`, populated in multiple
`configs/*.yaml` (e.g. `basis_trade_multi_venue.yaml:82-87`). Reads exactly like an operator venue allow-list. **Zero
engine consumers** — parsed/validated at load time by Pydantic, covered by one construction test
(`tests/unit/test_config_loader.py`), never read again. `ConfigLoader` itself is used in exactly one production place
(`strategy_service/risk/drawdown_investigation_writer.py`), not by any live strategy engine.

Anyone setting `allowed_venues` in a strategy config today, believing it constrains routing, is wrong — the field is
inert. Per the workspace's "delete deprecated code, no shims" rule this should be wired up for real or removed, not left
as a plausible-looking trap.

## Finding 3 — two independently-maintained "eligible venues per archetype" registries, no cross-check

- `strategy-service`'s `target_universe` catalog files (hardcoded per-archetype tuples — what actually runs in
  production).
- UAC's `ARCHETYPE_LEG_STRUCTURES`/`archetype_leg_spec_seeds.py`
  (`unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_leg_spec_seeds.py:82-133`) — a
  separate, hand-maintained structure feeding ONLY `generate_capability_verdict_matrix.py` (execution-algo-validity
  matrix, a different question: "which algo is valid for this cell," not "what's the currency/venue universe").

`strategy-service` never imports the UAC leg-spec module. The seed file's own comment (line 106) says its
`_SPOT_VENUES_STAKED` union should match `catalog_staked_basis.py`'s output — but nothing enforces that at build time;
it's an unchecked cross-repo assumption. If the two ever diverge, nothing would catch it.

## Recommendation (operator decision needed — not actioned)

- Decide whether to build the curtailment layer now (design sketch above), and at what scope (all 19 archetypes, or
  start with the already-drivable 7 in `paper_universe.py`'s `_ENGINE_DRIVABLE_ARCHETYPES`).
- Decide Finding 2: wire `SmartOrderRoutingConfig.allowed_venues` for real, or delete it.
- Decide Finding 3: reconcile the two registries (e.g. UAC's seed file imports/derives from the catalog, or vice versa),
  or accept the drift risk and document it as intentional.
- Per plan-destination HARD RULE: if this becomes build work, ask the operator whether it's an agent-orchestrator plan
  or a human plan before authoring one.

## Evidence

Full per-archetype table + file:line citations for every claim above live in the 2026-07-23 chat transcript (per-
archetype DeFi universe mapping audit agent run). Key files read:
`strategy-service/strategy_service/engine/ strategies/v2/target_universe/{catalog.py,catalog_carry.py,catalog_staked_basis.py,catalog_yield_defi.py, catalog_trading.py,specs.py}`,
`strategy_service/cli/handlers/{paper_run_handler.py,paper_universe.py}`,
`strategy_service/portfolio_allocator/{guard_rails.py,archetypes_rank.py}`,
`strategy_service/engine/core/ config_loader.py`, `strategy_service/types.py`,
`unified-api-contracts/unified_api_contracts/internal/ architecture_v2/archetype_leg_spec_seeds.py`,
`unified-trading-pm/scripts/openapi/ generate_capability_verdict_matrix.py`.

---

## RESUME POINT 2026-07-23 (mid-session addendum) — operator-approved build scope, 3-layer universe design, phased plan

**Operator context that changed this doc's scope**: a follow-up question ("we grabbed hundreds of candidates in
e2e-testing backtests, why does prod hardcode 13 coins for CARRY_BASIS_PERP?") surfaced a real audit gap — the earlier
per-archetype table above was checked only against strategy-service's _production_ catalog, never diffed against
`e2e-testing`'s own broader exploratory scripts for the same archetypes. Concrete correction:

- `e2e-testing/scripts/defi/staked_basis_funding_scan.py`'s `_DEFAULT_COINS` = a **40-coin** default list, includes
  HYPE, PEPE, WIF, BONK, JUP, JTO, TAO, ORDI. My earlier "HYPE never appears anywhere" answer was scoped ONLY to
  strategy-service's production catalog — wrong to state unqualified.
- `e2e-testing/scripts/defi/funding_ensemble_engine.py`'s `_top_volume()` doesn't use a fixed list at all — it reads a
  **live per-venue snapshot of every coin the exchange lists** (genuinely hundreds per venue: Binance/Bybit/Aster),
  filters by a min-volume floor, takes top-N (default 40) by 24h USD volume. `SURVIVORS` in the same file = 30 coins,
  with its own docstring: _"operator 2026-06-18: the live ensemble was Binance-only/30-survivors — far narrower than the
  backtest."_ — a real, previously-made, documented operator narrowing decision.
- That file's own lifecycle marker:
  `Delete-when: ensemble orchestrator folded into strategy-service multi-strategy allocator (production)`. The fold was
  always the intent; it never happened. Production's `CARRY_BASIS_PERP`/ `CARRY_FUNDING_DISPERSION` catalog is still the
  static 13-coin `catalog_carry.py` list, not this dynamic mechanism.
- `catalog_carry.py`'s own comment on `_CARRY_BASIS_PERP_COINS` says the intent was always "this can be generous; [the]
  allocator filters" (economic threshold, 250bps) — i.e. the STATIC list was only ever meant to be a stand-in candidate
  pool, with the real candidate-discovery mechanism (dynamic, volume-ranked) never actually wired in.

### Operator-specified target architecture (verbatim intent, 2026-07-23) — THREE layers, do not collapse them

> "we were supposed to use features service ohlcv derived volume per coins to understand candidates dynamically based on
> volume. in addition strategy service catalogue should be able to screen down to a filtered list if it wants (allow
> list and block list) on base currency, venues, instrument types and data types per archetype. then finally an
> individual strategy id config (for a given client and axis and version of a strategy archetype) should be able to
> allow additional filters that then allows us to keep universe wide but specifics targeted."

- **Layer 1 — dynamic candidate discovery, sourced from features-service (batch-deterministic, NOT a live API call)**.
  Confirmed reusable building block already exists:
  `features-service/features_service/cross_instrument/app/calculators/adv.py` — a real, production rolling-ADV reader
  over MDPS `timeframe=24h` processed candles, per `(venue, instrument_id, asset_group, as_of_date)`, already has
  honest-absence handling (`AdvStatus.NO_DATA`/`.OK`, "≥7 days observed" gate) and an explicit "operator ask" docstring
  matching this exact need. **Do not build a new volume pipeline — wrap this calculator with a "rank candidates by ADV,
  return top-N" reader** that strategy-service's catalog layer can call. This replaces `e2e-testing`'s live-API
  `_top_volume()` with a deterministic, GCS-sourced equivalent (batch=live discipline).
- **Layer 2 — archetype-level catalog allow-list/block-list** on `{base_currency, venue, instrument_type, data_type}`,
  applied per archetype. This GENERALIZES what `catalog_staked_basis.py`'s `_resolve_start_token()` →
  `accepted_perp_collateral()` already does ad hoc for ONE archetype into a reusable cross-archetype filter — every
  other archetype's catalog builder should get the same kind of structural gate, not a copy-pasted one-off.
- **Layer 3 — per-strategy-instance config-level filter**, scoped to `(client_id, axis, archetype version)` for one
  deployed `TargetInstanceSpec`/strategy_id. This is the mechanism from this doc's original "Finding 1" design sketch
  (`PaperUniverseConfig` extension / `specs_for_archetype()` post-filter) — but it is explicitly the NARROWEST/LAST
  layer, sitting on top of a wide Layer-1 candidate pool and a Layer-2 structural filter, not a replacement for either.
  Purpose: "keep universe wide but specifics targeted" — an individual client's specific strategy instance can narrow
  further without touching the archetype's general eligibility rules or the dynamic candidate pool.

**Explicit architectural point (do not build these as one flat filter)**: Layer 1 answers "what COULD this archetype
ever consider" (liquidity-gated, dynamic); Layer 2 answers "what is this ARCHETYPE structurally allowed to touch"
(collateral/venue/instrument eligibility, static-ish, rarely changes); Layer 3 answers "what does THIS specific client
strategy instance want today" (operator-tunable, changes often). Collapsing them loses the "wide universe, targeted
specifics" property the operator explicitly asked for.

### Build plan — "complete the orphaned archetypes" (operator-approved 2026-07-23, in progress)

Per `paper_universe.py`'s `_ENGINE_DRIVABLE_ARCHETYPES`, only 7 of 19 DeFi/carry archetypes currently have a working
paper-replay tick builder; the other 12 are honestly marked `engine_tick_builder_unwired`. Operator approved wiring the
rest, phased to avoid concurrent edits to the same shared files (`paper_run_handler.py`/`paper_universe.py`) — phases
run SEQUENTIALLY, not in parallel:

- [x] [BACKEND] P1. Phase 0 (this session, prerequisite): `CARRY_STAKED_BASIS`'s STAKING_REWARD leg wired to real
      `lst_yields` index-ratio — `strategy-service@e93902d8`. New `CanonicalLstYieldsIndexProvider` is the reusable
      building block Phase 1 below reuses directly.
- [ ] [BACKEND] P1. **Phase 1 — CARRY_STAKED_BASIS_DATED — BLOCKED 2026-07-23, not on data, on a deeper pre-existing
      catalog/engine config-shape mismatch** (build agent held per its own STOP instruction; see addendum below for the
      full finding + evidence — do not re-dispatch until the config-shape question is resolved, or the build agent will
      hit the identical `ValueError` at `register_instance()` before it ever reaches the tick loader).
- [ ] [BACKEND] P1. **Phase 2 (= E3) — CARRY_RECURSIVE_STAKED + CARRY_RECURSIVE_BORROW_LENDING_ONLY +
      CARRY_BASIS_PERP_INV**. All three share the same new building block: an Aave `borrow_index` sample-to-sample
      accrual leg (mirrors the already-built `index_ratio_accrual()` primitive, just fed the borrow index instead of the
      LST exchange-rate index). This IS the previously-tracked "E3" follow-on from
      [[pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21]] — build it once, wire into all 3 archetypes
      (they differ only in whether they ALSO have a staking leg or a perp hedge on top).
- [ ] [BACKEND] P2. **Phase 3 — CARRY_BASIS_DATED + CARRY_BASIS_DATED_INV**. New data source: the
      `paired_price_dispersion` calculator (features-cross-instrument-service) for dated-futures-vs-cash/ETF basis. Note
      `catalog_carry.py`'s own comment flags some rows as `status=databento_pending` placeholders — confirm real data
      exists per-cell before wiring each; some cells may have to stay honestly unwired pending Databento integration.
- [ ] [BACKEND] P2. **Phase 4 — YIELD_ROTATION_LENDING + YIELD_STAKING_SIMPLE**. Pure yield archetypes (no hedge leg) —
      reuse `lending_rates`/`lst_yields` readers already established.
- [ ] [BACKEND] P2. **Phase 5 — LIQUIDATION_CAPTURE**. New data source: on-chain liquidation-cascade feed +
      `health_factor_trigger`.
- [ ] [BACKEND] P1. **After Phases 1-5**: build the Layer-3 curtailment mechanism (`PaperUniverseConfig` venue/currency
      allowlist) on the now-larger drivable-archetype set.
- [ ] [BACKEND] P3. **Separate, NOT yet explicitly confirmed as in-scope**: fold Layer-1's dynamic ADV-ranked candidate
      discovery into `CARRY_BASIS_PERP`/`CARRY_FUNDING_DISPERSION`'s catalogs, replacing the static 13-coin list — this
      is the concrete first real consumer of Layer 1 once built.
- [ ] [DOCS] P3. **Explicitly OUT of the tick-builder-wiring scope**: `ARBITRAGE_MEV_LIQUIDATION_BUNDLE`,
      `ARBITRAGE_MEV_JIT_LIQUIDITY`, `ARBITRAGE_MEV_BACKRUN` — architecturally opportunistic/runtime-mempool-driven, no
      catalog-declared currency universe to build a day-partition tick loader against. Flagged, not silently dropped — a
      currency constraint for these three would need new logic inside the engines themselves, a materially different
      (and separately-scoped) piece of work.
- [ ] [BACKEND] P2. Side-decision 1 (not started): wire `SmartOrderRoutingConfig.allowed_venues` for real, or delete it
      (dead code, Finding 2 above).
- [ ] [BACKEND] P2. Side-decision 2 (not started): reconcile strategy-service's catalog vs UAC's
      `archetype_leg_spec_seeds.py` (Finding 3 above, two unreconciled registries).

**Lesson recorded**: an audit that maps only the PRODUCTION side of a question ("what does the catalog declare") can
miss a real gap that only shows up by diffing against the EXPLORATORY/backtest side ("what did we already prove out that
never got folded in"). Check both sides before answering "is X supported" with a flat no.

---

## BLOCKED addendum 2026-07-23 — Phase 1 (CARRY_STAKED_BASIS_DATED) build agent findings

Dispatched to wire `_load_staked_basis_dated_ticks()` in `strategy-service`'s `paper_run_handler.py` (mirroring the
already-shipped `CARRY_STAKED_BASIS` STAKING-leg pattern, `strategy-service@e93902d8`). Held before writing any code —
here is what was verified and why.

**Data precondition (the thing the agent was asked to confirm) — CONFIRMED REAL, not the blocker.** Read
`unified_api_contracts.canonical.crosscutting._mvp_scope_rules.CeFiMvpRule` (~line 380-500): `FUTURE` is a genuinely MVP
CeFi `instrument_type` for DERIBIT (base-membership + perp-gate), flat
`data_types = {trades, book_snapshot_5, derivative_ticker, funding_rate}` — the SAME per-instrument set as
SPOT_PAIR/PERPETUAL, distinct from the explicitly non-MVP `futures_chain` bundled-chain data_type. Confirmed empirically
against the real manifest + real GCS objects (`market-data-tick-cefi-prd-central-element-323112`, read via
`unified_trading_library.read_availability_index` + `get_storage_client().list_blobs`,
GCP_PROJECT_ID=central-element-323112):

- Real per-contract quarterly ETH futures parquets exist under
  `raw_tick_data/by_date/day={D}/pipeline_mode=batch_tardis/asset_group=cefi/venue=DERIBIT/instrument_type=future/ data_type={trades,book_snapshot_5}/`
  — e.g. `ETH-26JUN20.parquet` / `ETH-27MAR20.parquet` (2020-01-05 legacy naming) through
  `DERIBIT:FUTURE:ETH-USD@INV-20260925.parquet` / `DERIBIT:FUTURE:ETH-USDC@LIN-20260925.parquet` (2026-07-15 current
  wire naming) — genuine per-expiry files, both inverse (USD) and linear (USDC) margin, quarterly + monthly expiries,
  NOT a proxy from the perpetual.
- Manifest `capture_status='captured'` rows for
  `(venue=DERIBIT, instrument_type=FUTURE, data_type=trades, instrument_id='ETH')` (a per-underlying rollup row the
  writer emits alongside the per-contract files, not one row per contract) span 503 dates 2020-01-01 → 2026-06-27
  (`book_snapshot_5` rollup rows run through 2026-07-20); real, substantial coverage, not a sparse token presence.

**The actual blocker — CarryStakedBasisEngine cannot even be CONSTRUCTED with `build_carry_staked_basis_dated()`'s own
catalog config.** `factory.py:69` registers `StrategyArchetype.CARRY_STAKED_BASIS_DATED` to the SAME
`CarryStakedBasisEngine` class as the plain archetype (`staked_basis.py:596-601`, `ALLOWED_ARCHETYPES` includes both).
That engine's `REQUIRED_PARAMS` (`staked_basis.py:602-611`) — cross-confirmed by the machine-readable
`PARAM_SCHEMA_REGISTRY["CARRY_STAKED_BASIS_DATED"]` SSOT (`param_schema.py:159-186`, explicit comment "Same engine
(CarryStakedBasisEngine) — shares the schema") AND by two independent test fixtures
(`tests/integration/test_phase8_archetype_factory_smoke.py:72-78`,
`tests/unit/engine/strategies/v2/ test_equity_rescaling.py:79-86`) — is
`{staking_protocol, native_asset, lst_asset, perp_venue, perp_instrument, spot_venue}`. Both test fixtures pass
`perp_venue="DERIBIT"`/`"deribit"` + a literal dated-symbol-shaped `perp_instrument` (`"ETH-31MAR25"` /
`"ETH-QUARTERLY"`) — i.e. the engine treats the dated variant as _structurally identical_ to the plain perpetual
variant, with the ONLY difference being what string is passed in `perp_instrument`.

`catalog_staked_basis.py:389-429`'s real `build_carry_staked_basis_dated()` emits none of that: its `initial_config` is
`{lst_protocol, lst_asset, native_asset, dated_venue, dated_expiry, hold_policy, roll_on_dte}` — no `staking_protocol`
(renamed `lst_protocol`), no `perp_venue`/`perp_instrument`/`spot_venue` at all. Reproduced empirically
(`strategy-service/.venv`, both live catalog slots):

```
CARRY_STAKED_BASIS_DATED@lido-deribit-eth-q1-usdc-v1-prod
{'lst_protocol': 'lido', 'lst_asset': 'stETH', 'native_asset': 'ETH', 'dated_venue': 'deribit',
 'dated_expiry': 'q1', 'hold_policy': 'HOLD_UNTIL_FLIP', 'roll_on_dte': '10'}
RAISED: ValueError CarryStakedBasisEngine missing required params:
  ['perp_instrument', 'perp_venue', 'spot_venue', 'staking_protocol']
```

`ArchetypeEngineFactory.build(...)` is called synchronously inside `V2EngineOrchestrator.register_instance`
(`orchestrator.py:156`), itself called synchronously inside `GroupBRunner.register_instance` — i.e. this `ValueError`
fires immediately at registration, in ANY environment (paper replay, live promotion, the allocator's own preflight),
before a single tick is ever built. **This is not "unwired for paper-replay" — `CARRY_STAKED_BASIS_DATED` as currently
cataloged is unrunnable everywhere, including live**, a latent landmine independent of this build task.

**Second, compounding gap found while tracing the consumer** (per the task's own instruction to trace `staked_basis.py`
"enough to understand how it distinguishes the plain vs `_DATED` variant"): it doesn't.
`grep -n "DATED\|dated_expiry\| dated_venue\|roll_on_dte\|HOLD_UNTIL_FLIP" staked_basis.py` returns exactly one hit —
the `ALLOWED_ARCHETYPES` tuple. There is no roll-forward logic anywhere in the engine: `_extract_config` reads
`perp_instrument` once, as a static per-tick config string (not a tick feature), and `on_tick` never re-resolves it.
Even a config-key rename fix (map `lst_protocol`→`staking_protocol`, add a literal `spot_venue`) would leave the engine
holding ONE fixed dated-contract symbol for the strategy instance's entire life — no mechanism consumes
`roll_on_dte`/`hold_policy` to roll to the next quarter as the held contract approaches expiry, which is the entire
economic point of a "dated" (vs perpetual) basis trade. `dated_expiry: "q1"/"q2"` in the catalog is also not itself
resolvable to a concrete, real contract symbol without a decision on which calendar year/quarter it means and how it
advances over time.

**Why this is reported here rather than fixed in place**: fixing the config-key mismatch is mechanical, but fixing it
usefully requires an actual product/design decision this agent is not positioned to make unilaterally — (a) how
`dated_expiry` maps to a real, current `perp_instrument` symbol day-by-day (the manifest confirms real symbols exist in
both legacy `ETH-27MAR20`-style and current `DERIBIT:FUTURE:ETH-USD@INV-20260925`-style naming — a resolver needs to
pick the right one per day), and (b) whether the roll-on-expiry logic belongs in the engine (new code, affects the live
architecture too) or is deferred as an explicit known-limitation for a first cut (e.g. hold a single contract to
expiry/HOLD_UNTIL_FLIP literally, never roll, and accept the position naturally closes out or requires manual re-catalog
at the next quarter). Per the workspace's async-wait/blocked discipline ("a held, unwired, well-documented state is
better than a plausible-but-wrong wiring"), this was held rather than guessed.

**Recommendation**: before Phase 1 is re-dispatched, decide (1) the `dated_expiry`→`perp_instrument` resolution rule,
(2) whether roll logic ships now or is explicitly deferred, then fix `build_carry_staked_basis_dated()`'s config keys to
match `PARAM_SCHEMA_REGISTRY`/`REQUIRED_PARAMS` in the SAME change as the tick-loader build (fixing the catalog alone,
with no tick loader, would make the engine constructible but still produce zero paper runs — the archetype would just
move from "crashes at registration" to "no ticks, honest-skip", i.e. exactly Phase 1's original scope, once the config
shape is right).
