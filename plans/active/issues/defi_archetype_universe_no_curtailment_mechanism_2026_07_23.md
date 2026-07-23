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
- [ ] [BACKEND] P1. **Phase 1 — CARRY_STAKED_BASIS_DATED** (IN FLIGHT as of this addendum — dispatched to a background
      build agent, not yet confirmed shipped). Reuses `CanonicalLstYieldsIndexProvider` for the STAKING leg; adds a new
      dated-futures short-leg tick loader (Deribit ETH quarterly `instrument_type=FUTURE` — confirmed via
      `unified-api-contracts`'s `CeFiMvpRule` that `FUTURE` is genuinely MVP for Deribit with real
      `trades`/`book_snapshot_5` capture, NOT the same thing as the explicitly-non-MVP `futures_chain` bundled-chain
      data_type — agent was instructed to verify real GCS-captured data exists before wiring, hold if not).
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
