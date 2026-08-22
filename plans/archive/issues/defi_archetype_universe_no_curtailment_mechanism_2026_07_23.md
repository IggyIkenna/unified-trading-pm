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
    defi_catalog_engine_config_key_contract_drift_2026_07_23,
  ]
created: 2026-07-23
author: unknown
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
context_scope:
  [
    /codex/04-architecture/tier-and-import-architecture.md,
    strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/recursive_staked.py,
    execution-service/execution_service/defi_execution/orchestrators/recursive_loop_orchestrator.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/_mvp_scope_predicate.py,
    strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog.py,
    /plans/active/defi_archetype_catalog_identity_extension_ao_dispatch_2026_08_16.md,
  ]
---

> **📦 ARCHIVED 2026-08-22 (archival pass 2)** — BRIDGE resolved: 0 open todos since the na-eligibility-audit
> 2026-08-16 pass; this dispatch's archival pass 2 is the follow-on pass the bridge note deferred to. Kept as a
> historical design/investigation record.
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

**RESOLVED 2026-07-24 (`strategy-service@813ec66b`) — DELETED, not wired up.** Re-verified before deleting: the class
has exactly two fields (`enabled`, `allowed_venues`) and BOTH have zero consumers repo-wide (grepped
`smart_order_routing` across all `.py`/`.yaml`/`.md` — only definition sites, YAML config population, and one
construction test, never an attribute read) — so the whole `SmartOrderRoutingConfig` class was dead, not just
`allowed_venues` within an otherwise-live class. Removed: the `SmartOrderRoutingConfig` Pydantic model
(`config_loader.py`) + its `smart_order_routing` field on `StrategyConfig`; `DeFiSORConfigDict` TypedDict + its
`smart_order_routing` field on `DeFiStrategyConfigDict` (`types.py`); the `smart_order_routing:` block (both `enabled:`
and `allowed_venues:` keys) from all 7 YAML configs that set it (`configs/liquidation_capture_eth.yaml`,
`strategy_service/configs/{active_lp_eth_usdc,active_lp_sol_usdc,basis_trade_multi_coin,basis_trade_multi_venue, lending_arb_arbitrum,lending_arb_eth}.yaml`);
the "Smart Order Routing (DeFi)" section + JSON example block from `docs/CONFIG_SCHEMA.md`; the
`SmartOrderRoutingConfig` import + construction call from `tests/unit/test_config_loader.py`. **Correction to this doc's
own file list**: `tests/unit/test_schema_robustness.py` was NOT touched — re-grepping found its `allowed_venues` tests
exercise a completely different, UAC-defined `StrategyInstruction.allowed_venues` field
(`unified_api_contracts.internal.domain.strategy_service.instruction`, re-exported via
`strategy_service/models/instruction.py`), unrelated to `SmartOrderRoutingConfig`/`DeFiSORConfigDict` — same field name,
different class/repo, real (not verified dead) execution-routing field on the instruction schema. Final grep for
`SmartOrderRoutingConfig|DeFiSORConfigDict|smart_order_routing` across the repo: zero hits. Quality gates green (fresh
foreground run, exit 0); pushed via quickmerge, landed on `live-defi-rollout`.

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

### Addendum 2026-07-24 — Finding 3 reconciliation-direction analysis (investigation only, not actioned)

Sub-agent investigation into HOW to reconcile the two registries (per this doc's own Finding-3 open question). Read in
full: `/codex/04-architecture/tier-and-import-architecture.md`, `strategy-service`'s `target_universe/catalog*.py` (all
5 family files + `catalog.py`'s dispatcher), and UAC's `archetype_leg_spec_seeds.py` (1644 lines, full file).

**1. Tier constraint — CONFIRMED, no ambiguity.** `unified_api_contracts` (UAC) is `T0-base` — "true leaves, no
workspace imports … stdlib + pydantic ONLY — zero unified-\* imports, not even in tests" (tier doc line 93-96, 216-217).
`strategy-service` is `T4` (Services). Import rule #2: "Higher tiers may import from SAME or LOWER tiers only" + "No
service ↔ service imports" — T4 may import T0-3, never the reverse, and UAC may NEVER import a service regardless of
tier direction (T0-base's own rule is even stricter: zero workspace imports at all, full stop). So any design where
UAC's `archetype_leg_spec_seeds.py` reads `strategy-service`'s catalog live is a hard architecture violation, not just a
style preference — confirms the premise driving this whole analysis.

**2. The two structures are NOT the same granularity of fact — confirmed by reading both, and this is the load-bearing
finding.** `strategy-service`'s catalog builders (`build_carry_basis_perp()`, `build_carry_staked_basis()`, etc.) emit
**one `TargetInstanceSpec` per fully-resolved DEPLOYABLE INSTANCE** — a concrete
`(venue × coin × share_class × capital_budget × engine-specific config-key literals)` combo with a unique `slot_label`
(`CARRY_BASIS_PERP@binance-btc-1h-usdt-v3-prod` etc.) that gets registered with the live engine factory. E.g.
`build_carry_basis_perp()` alone emits 130 rows just for its "single-venue netted" bundle (10 venue bundles × 13 coins),
each carrying literal `spot_venue`/`perp_venue`/`instrument`/`coin`/`hold_policy`/`target_funding_bps` string values.
UAC's `ArchetypeLegStructure` (`archetype_leg_spec_seeds.py`) is **one structure per ARCHETYPE, not per instance** — a
coarse leg-role MODEL (`leg_id`, `role` enum, `instrument_types` enum tuple, `asset_groups` enum tuple,
`eligible_venue_ids` — a hand-curated UNION across all rows for that leg, not tied to any specific coin/capital/
instance, `constraints` describing atomic-bundling/collateral semantics, `execution_coupling` mode). It has **no concept
of coin, capital budget, share class, or engine config values at all** — those simply have no field to live in.
Conversely, the catalog's flat `initial_config: dict[str,str]` has **no concept of leg role, atomicity constraint, or
execution-coupling mode** — those are baked into engine `_build_legs()`/`on_tick()` logic, never surfaced as catalog
data. Each side structurally cannot express what the other captures — this is not a "same fact, different format"
mismatch, it's two genuinely different facts (instance provisioning data vs. archetype capability metadata) that happen
to overlap on ONE shared sub-fact: which venues are eligible per leg role.

**3. That shared sub-fact has ALREADY silently diverged — found by direct comparison, not theoretical.** Comparing UAC's
`_basis_perp_structure()` (CARRY_BASIS_PERP) `eligible_venue_ids` against `catalog_carry.py`'s
`_CARRY_BASIS_PERP_VENUE_BUNDLES` (the catalog's actual live venue set):

- UAC's **perp leg** lists `(binance, bitget, bybit, deribit, gmx_v2, hyperliquid, kraken, okx)` — **missing `aster`,
  `kalshi-perp`, and `polymarket-perp`**, all three of which are live rows in the catalog's
  `_CARRY_BASIS_PERP_VENUE_BUNDLES` today (kalshi-perp "live from 2026-05-29" per the catalog's own comment). Also a
  naming drift: catalog emits bare `"gmx"`, UAC's seed has `"gmx_v2"`.
- UAC's **spot leg** lists `(binance, bitfinex, bitget, bybit, coinbase, hyperliquid, kraken, okx, uniswap_v3)` —
  **missing `deribit` and `aster`** (both are live catalog spot-leg venues in the netted-bundle form), while including
  `coinbase` (only appears in the catalog's separate "cross-venue" rows, not the netted-bundle rows the perp leg draws
  from).

This is exactly the risk Finding 3 flagged in the abstract — confirmed concretely for the very first archetype checked,
same-day as this addendum. Zero effort was spent hunting for this; it fell out of the first side-by-side read. This
raises confidence that a systematic diff would find more.

**4. Recommendation: (A), the diff/gate-fail variant — NOT full regeneration, and NOT (B).**

- **(A) wins because of point 2**: only the `eligible_venue_ids` field is even mechanically derivable from the catalog
  (via a per-archetype mapping of config-keys → leg role, e.g. `spot_venue`→SPOT leg, `perp_venue`→PERP leg,
  `staking_venue`→STAKE leg, `lending_venue`→LEND leg). Everything else in `ArchetypeLegStructure` (leg roles,
  `instrument_types`, `constraints`, `execution_coupling`) is sourced from reading the ENGINE's actual `_build_legs`/
  `on_tick` code + codex docs (per the seed file's own docstring) — work that is not catalog-derivable at all, so full
  auto-regeneration (A-a) can only ever repopulate one field of the structure regardless of effort spent. That collapses
  A-a and A-b into practically the same shape of fix: **a script that computes the per-archetype per-leg-role venue
  union from `TARGET_UNIVERSE` and asserts catalog-venues ⊆ UAC eligible_venue_ids** (one-directional containment, not
  equality — UAC's list may legitimately be broader, e.g. citing a codex-documented venue not yet live in the catalog),
  failing the gate on any catalog venue absent from UAC's set. This would have caught the aster/kalshi/polymarket/gmx_v2
  drift above today.
- **(B) — SSOT inversion — is NOT actually a full inversion once you account for point 2.** Even under (B), UAC's schema
  would need **new fields it doesn't have today** (coin/capital-budget/share-class/hold-policy/engine-config- literal
  equivalents) to become the catalog's real source, because `ArchetypeLegStructure` currently models
  capability/eligibility, not provisioning. Without those new fields, "invert the SSOT" only ever means "catalog reads
  UAC's venue-eligibility union and layers everything else on top itself" — which is functionally closer to (A) than a
  true single-source model. A true (B) would require designing and shipping a materially bigger UAC schema first
  (schema-design risk, version bump, migration), THEN rewriting **all ~18-19 DeFi/carry catalog builder functions**
  across 3 files (`catalog_carry.py` — 7 builders, `catalog_staked_basis.py` — 2 builders, `catalog_yield_defi.py` — 9
  builders; `catalog_trading.py`'s `build_arbitrage_price_dispersion` is the 19th if counted per this doc's own
  DeFi-touching scope) to consume it instead of hardcoding tuples, while preserving every archetype's idiosyncratic
  per-engine config-key contract (e.g. `CARRY_STAKED_BASIS_DATED`'s `dated_expiry`+`roll_on_dte` vs the plain
  archetype's static `perp_instrument`; `CARRY_RECURSIVE_BORROW_LENDING_ONLY`'s 7-field per-cell
  lender/chain/collateral/debt/mode tuples) — exactly the class of catalog↔engine key-mismatch bug this same doc's Phase
  1 and Phase 3 addenda ALREADY found twice, independently, in unrelated work this week. Rewriting 18-19 builder
  functions at once meaningfully raises the odds of reintroducing that bug class at scale, for an architectural
  cleanliness gain that (per point 2) is smaller than it first appears — the instance-level facts would still need a
  home, and that home is legitimately `strategy-service` (a T4/provisioning concern), not UAC (a T0/schema concern).

**Sizing**: **(A) is roughly a half-day-to-1-day script** — the per-archetype config-key→leg-role mapping is the fiddly
part (~19 archetypes, key names vary per engine, as evidenced by the Phase-1/Phase-3 key-naming bugs already found), the
containment-check + CI wiring itself is small. **(B) is a multi-day refactor, realistically 3-5+ AI-days minimum** — new
UAC schema fields + a version bump + migration + rewriting 18-19 builder functions + full regression against
`test_target_universe_disjoint_from_legacy` and every engine's `REQUIRED_PARAMS`, with real risk of reintroducing the
same silent config-key-mismatch bug class this doc already tracks twice. **Recommend (A).**

**What was surprising**: that the two registries had ALREADY diverged (not just "could diverge in theory") — three live
venues (aster, kalshi-perp, polymarket-perp) missing from UAC's CARRY_BASIS_PERP perp-leg union, found on the very first
archetype spot-checked, with zero targeted search. Also surprising: how thin the actual schema overlap between the two
structures is once read side-by-side — they share almost nothing except venue-id strings; the "two unreconciled
registries" framing undersells how differently-shaped they are, which argues strongly against a naive full-diff or
full-regeneration approach and toward the narrower per-leg-role venue-containment check.

---

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
- [x] [BACKEND] P1. **Phase 1 — CARRY_STAKED_BASIS_DATED — FULLY SHIPPED 2026-07-23.** Config-shape blocker resolved
      (`strategy-service@606f2fb5`): `catalog_staked_basis.py` now emits the engine's real key names, DROPPING a static
      `perp_instrument` entirely in favor of `dated_expiry`+`roll_on_dte`, which `CarryStakedBasisEngine` now
      DYNAMICALLY resolves every tick via a new pure `resolve_current_dated_contract()`
      (`carry_and_yield/dated_contract_resolver.py`) implementing Deribit's real quarterly-roll rule (verified against
      real captured dated-future symbols, not assumed from convention). Paper-replay tick-loader wiring shipped
      separately, same day (`strategy-service@795fa10c`): `_load_staked_basis_dated_ticks()` in `paper_run_handler.py` +
      a new `CanonicalDatedFutureMarkProvider` (`engine/core/canonical_dated_future_mark_provider.py`) reading real
      Deribit dated-`FUTURE` `book_snapshot_5` mid-prices per day for whichever contract the resolver says is currently
      held (handles both the legacy `{ASSET}-{DD}{MON}{YY}` and wire-canonical
      `DERIBIT:FUTURE:{ASSET}-{QUOTE}@{INV|LIN}-{YYYYMMDD}` naming conventions, tried in a fixed deterministic priority
      order) + passive/attribution wiring for the STAKING leg (reusing `CanonicalLstYieldsIndexProvider`, identical to
      the plain archetype) and the dated-futures mark-to-market leg + `CARRY_STAKED_BASIS_DATED` added to
      `paper_universe.py`'s `_ENGINE_DRIVABLE_ARCHETYPES`. Full evidence trail:
      `defi_catalog_engine_config_key_contract_drift_2026_07_23.md`'s `CARRY_STAKED_BASIS_DATED` row + this session's
      chat record.
- [x] [BACKEND] P1. **Phase 2 (= E3) — NARROWED to CARRY_RECURSIVE_STAKED only, 2026-07-23 — SHIPPED
      `strategy-service@23bd8b76`** (verified before dispatch, learning Phase 1's lesson):
      `CARRY_RECURSIVE_BORROW_LENDING_ONLY` and `CARRY_BASIS_PERP_INV` are **NOT buildable via a tick-loader at all** —
      both set `staking_yield_enabled=false` in their catalog config, and the shared engine
      `CarryRecursiveStakedEngine.on_tick()` (`recursive_staked.py:194-199`) explicitly returns `[]` unconditionally
      whenever that flag is false, with an in-code comment: "execution via RecursiveLoopOrchestrator landed in Phase 5.
      Stub returns [] until orchestrator wiring is in place." Grepped the ENTIRE repo for `RecursiveLoopOrchestrator` —
      it exists NOWHERE except this one comment; no class, no file, no partial impl. **These two archetypes are
      non-functional in every environment today (paper, batch, live), not merely paper-replay-unwired.** Building a tick
      loader for them would feed real data into an engine guaranteed to no-op — do NOT do this; it would look like
      progress and be nothing. Filed as its own tracked gap below. `CARRY_RECURSIVE_STAKED` itself is verified SAFE to
      build (its catalog rows don't set `staking_yield_enabled`, defaulting true → real `on_tick` logic runs; config
      keys independently verified correctly dual-injected — `_RECURSIVE_STAKED_LST`/`_RECURSIVE_STAKED_LEND` lookup
      dicts inject `staking_protocol`/`lending_protocol`/ `native_asset`/`lst_asset` alongside the
      `staking_venue`/`lending_venue` keys, per the catalog's own comment "Both key sets must be present" — this is NOT
      the Phase-1 class of bug). Phase 2 now = wire `CARRY_RECURSIVE_STAKED`'s tick loader + the new Aave `borrow_index`
      sample-to-sample accrual leg (mirrors `index_ratio_accrual()`, fed the borrow index instead of the LST
      exchange-rate index) for its lending/debt side — this IS the previously-tracked "E3" follow-on from
      [[pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21]]. **Shipped, evidence**:
      `strategy_service/cli/handlers/paper_run_handler.py::_load_recursive_staked_ticks` (real per-day ticks from
      `lst_yields.staking_apy_bps` + `lending_rates.aave_borrow_apy`, per-reserve honest-skip on absence), new
      `strategy_service/engine/core/canonical_aave_borrow_index_provider.py` (`CanonicalAaveBorrowIndexProvider`,
      day-over-day `aave_borrow_index` differencing), `CARRY_RECURSIVE_STAKED` added to `paper_universe.py`'s
      `_ENGINE_DRIVABLE_ARCHETYPES` (own satisfiability gate — this archetype has no perp/spot-swap leg, so the generic
      carry-tick-config gate would always reject it), and NEW dedicated
      `build_recursive_staked_passive`/`build_recursive_staked_attribution` producers (2-leg: STAKING_REWARD via
      `CanonicalLstYieldsIndexProvider` reused directly + a debt-cost leg via the new provider, booked negative, keyed
      `{lending_protocol}:DEBT_TOKEN:{native_asset}` — verified end-to-end to match the engine's REAL `BORROW`
      `AtomicLeg` instrument_key). Accrual notional sized from the REAL executed fill sums (STAKE/BORROW leg totals),
      not the idealized `target_leverage × capital` (verified empirically these diverge ~2%/~18% due to the discrete
      loop's break condition). Verified END-TO-END against REAL prod GCS (`features-defi-prd-central-element-323112`,
      2026-04-15, `lido-aave` spec): real tick → real 9-fill 3-loop `AtomicInstruction` → real
      `staking_index_by_day`/`borrow_index_by_day` resolved → real STAKING_REWARD=+25.88/debt-cost=-16.54 booked.
      **Per-reserve honest-absence confirmed empirically** (5 real prod days spot-checked): `AAVE_V3_ETHEREUM` has 100%
      populated `aave_borrow_index` (real accrual); `COMPOUND_V3_ETHEREUM` has real rows (DefiLlama-Yields-sourced APY —
      engine still trades on it) but ZERO `aave_borrow_index` ever (debt-cost leg honestly books zero — MTDS has no
      on-chain Compound V3 collector at all); `KAMINO_SOLANA` never appears as a `protocol` value in `lending_rates` at
      all (both legs skip). Deliberately NOT wired in this build (documented, tracked, out of the "tick builder +
      borrow-index leg" scope): the TRANSFERS/treasury ledger for this archetype's STAKE→LEND→BORROW loop (this
      archetype's config has no `perp_venue`/`spot_venue` for `build_paper_run_transfers`'s carry_staked_basis-shaped
      signature, so it is deliberately skipped rather than fed fabricated venue defaults — see the new code's
      `continue` + comment in `run_paper`'s per-spec loop). Minor pre-existing discrepancy noted, not fixed (out of
      scope): the catalog's `max_loops` config value ("5") is never read by `_build_loop_legs` (which hardcodes 10 as
      its own safety cap) — does not crash, does not affect correctness (the loop already terminates on the
      `cumulative > capital * target_leverage` condition well before either cap binds in the sampled real data). Quality
      gates: `strategy-service` `quality-gates.sh --no-fix` GREEN (fresh, non-cached full run: 5326 tests passed incl.
      91 new/updated for this build; basedpyright clean on every touched file — 5 pre-existing unrelated errors in
      `manifest_allocation_guard.py`; STEP 5.101 empty-string-fallback baseline held at 166).
- [x] ✅ [BACKEND] P2. **DONE — flipped 2026-08-12 (/plan-reconcile).** RULED 2026-08-09 + shipped: real commit SHAs
      independently re-verified as ancestors of `origin/live-defi-rollout` with fresh green `quality-gates.sh` on all 3
      touched repos — `strategy-service@817bb4e0` (Family-1 on_tick), `strategy-service@f2ac7fdf` (Family-2 on_tick),
      `execution-service@2352a17e` (RecursiveLoopOrchestrator's first production caller). Cross-link:
      `defi_catalog_engine_config_key_contract_drift_2026_07_23.md`'s already-flipped `[DESIGN]` twin, and the dedicated
      finalize plan `recursive_loop_orchestrator_wiring_finalize_2026_08_09.md`. **NEW finding 2026-07-23 —
      `RecursiveLoopOrchestrator` does not exist in strategy-service; 2 archetypes are production no-ops.**
      `CARRY_RECURSIVE_BORROW_LENDING_ONLY` and `CARRY_BASIS_PERP_INV` need real execution logic built from scratch (the
      "Phase 5" the in-code comment references was never actually shipped, or the comment is aspirational/stale — not
      determined which). This is materially bigger than a tick-loader wiring task — it's new production
      strategy-execution logic, live-path-affecting. Needs its own scoping pass before any build; do not fold into the
      "complete the orphaned archetypes" tick-builder effort. **Minor factual correction (2026-07-23, Phase 2 build
      agent, no action taken — out of scope)**: the earlier "grepped the ENTIRE repo, exists NOWHERE" claim was scoped
      to `strategy-service` only. A REAL, tested `RecursiveLoopOrchestrator` class DOES exist —
      `execution-service/execution_service/defi_execution/orchestrators/recursive_loop_orchestrator.py` (+
      `tests/defi_execution/unit/test_recursive_loop_orchestrator.py`) — and UAC carries its request/response schemas
      (`unified_api_contracts/internal/architecture_v2/recursive_loop_orchestrator.py`). This does NOT change the
      verdict above: `CarryRecursiveStakedEngine.on_tick()`'s `if not staking_yield_enabled: return []` fires
      UNCONDITIONALLY before any instruction is ever built, so the strategy engine never emits a signal for these two
      archetypes regardless of execution-service's own readiness — the blocker is strategy-side, not
      execution-service-side. Worth a scoping pass to confirm whether execution-service's orchestrator is real/complete
      enough that ONLY the strategy-side `on_tick` stub needs finishing (a smaller task than assumed) — flagging, not
      re-scoping unilaterally. **Scoping pass completed 2026-07-24 (read-only investigation, no code changed — the
      actual build stays correctly un-dispatched, see verdict below).** `RecursiveLoopOrchestrator` (711 lines,
      `execution-service/execution_service/defi_execution/orchestrators/recursive_loop_orchestrator.py`) is genuinely
      real and substantially complete: `open()`/`unwind()` entry points, health-factor-triggered abort handling, both
      persistent (iterative on-chain loop) and flash-loan (single-tx) open/close variants, 353 lines of unit tests. So
      execution-service's side is NOT the gap. **But the strategy-side gap is bigger than "finish a stub" — it needs NEW
      decision logic, not plumbing.** Read `CarryRecursiveStakedEngine.on_tick()` in full (`recursive_staked.py`): when
      `staking_yield_enabled=true` (the already-built `CARRY_RECURSIVE_STAKED` case, Phase 2), a real pipeline runs —
      `_preflight()` (APY/LTV/leverage checks), `_build_loop_legs()`, `_build_instruction()` — none of which exists for
      the `staking_yield_enabled=false` path (Families 1/2 =
      `CARRY_RECURSIVE_BORROW_LENDING_ONLY`/`CARRY_BASIS_PERP_INV`). Those two archetypes are a economically DIFFERENT
      recursive structure (pure lending-rate-differential leverage / inverse basis-perp leverage, no staking leg) — they
      need their OWN preflight/leg-building/instruction logic analogous to but distinct from the staked case, including
      real risk-parameter decisions this session should not invent unilaterally: what
      leverage-target/health-factor-abort thresholds trigger an open vs. unwind, what economic signal (funding
      differential? lending-rate spread?) drives entry for each family. **Verdict: still correctly NOT AO-dispatchable**
      — per the workspace's dispatch-scope-eligibility rule, an open-ended "invent the trading logic and its risk
      thresholds" task is a human design decision wearing a todo's clothes, not a checkable, worker-determinable
      outcome. Remains parked pending an operator design/scoping session (which SHOULD now be materially faster given
      execution-service's readiness is confirmed and the exact missing piece is precisely named, not vague). **Operator
      correction 2026-07-24 (chat) + a bigger self-caught correction while verifying it — read before dispatching either
      build, this changes the scoping above for BOTH archetypes, not just one.** The paragraph above treats
      `CARRY_RECURSIVE_BORROW_LENDING_ONLY` and `CARRY_BASIS_PERP_INV` as one pair needing the same "new recursive-loop
      decision logic." Operator clarified `CARRY_BASIS_PERP_INV` specifically is NOT a recursive/looping structure — it
      is `CARRY_BASIS_PERP` with both legs inverted: instead of long spot / short perp, it is **short spot (funded by
      borrowing the asset via the lending leg) / long perp**. Verifying that against the code surfaced a bigger fact
      this doc had wrong: I initially drafted (below, now corrected) that `CARRY_RECURSIVE_BORROW_LENDING_ONLY` "DOES
      carry `max_loops`" to justify treating it differently — **that was false, caught by re-checking rather than
      asserting.** `grep -c max_loops catalog_carry.py` returns exactly **one** hit, in `build_carry_recursive_staked()`
      only. NEITHER `build_carry_recursive_borrow_lending_only()` NOR `build_carry_basis_perp_inv()` sets `max_loops` OR
      `target_leverage` anywhere. `CarryRecursiveStakedEngine`'s real recursive-loop pipeline
      (`_preflight()`/`_build_loop_legs()`, `recursive_staked.py`) is built entirely around a `target_leverage` scalar
      (default 2.5x) driving a `STAKE → LEND → BORROW → STAKE → ...` loop to reach it — a parameter neither archetype's
      catalog config carries at all. **So BOTH archetypes are single-position structures, not iterative loops, despite
      the "RECURSIVE" family name and the shared engine class** — the "recursive" framing likely describes the
      EXECUTION-layer mechanics `RecursiveLoopOrchestrator` may use internally to reach a single target position (an
      implementation detail of how it fills, not a strategy-level loop-count parameter), not something either strategy
      config needs to specify. `CARRY_RECURSIVE_BORROW_LENDING_ONLY`'s actual shape (`perp_leg_enabled: "false"`, no
      perp keys at all): a single borrow of `debt_asset` against `collateral_asset` at `ltv_mode`,
      `target_net_delta: "0"` — a plain lending-rate-differential carry, no staking leg, no perp, no loop.
      `CARRY_BASIS_PERP_INV`'s shape is the SAME lending structure PLUS `perp_leg_enabled: "true"` +
      `perp_venue`/`perp_pair` — matching the operator's description exactly. `CarryBasisPerpEngine` (`basis_perp.py`,
      the plain `CARRY_BASIS_PERP`'s real, already- shipped engine) is itself **perp-leg-only by design** — its own
      docstring: "Spot hedge leg is expected to be wired separately by the orchestrator... the engine here is perp-side
      only — delta hedging is the orchestrator's concern." It reads `funding_rate_annualised_bps`, flips direction on
      sign (`funding>0` → SHORT perp; `funding<0` → LONG perp), and declares a `LegPortfolioState`/`LeveragedLeg` for
      downstream leg composition — so `CARRY_BASIS_PERP_INV`'s real shape looks much closer to a **sign-inverted variant
      of `CarryBasisPerpEngine`** (same funding-driven perp-direction logic, inverted, plus a lending-borrow leg
      declared instead of a bought-spot leg) than to `CarryRecursiveStakedEngine`'s loop-building machinery — **the
      current engine mapping in `factory.py` (`StrategyArchetype.CARRY_BASIS_PERP_INV: CarryRecursiveStakedEngine`) is
      very likely a misassignment**, not just a missing-logic gap; the same may hold for
      `CARRY_RECURSIVE_BORROW_LENDING_ONLY` given its config is equally non-recursive, though no equally-close existing
      engine analog has been identified for the no-perp case yet. **Net effect: this narrows (does NOT eliminate) the
      "new trading logic, operator judgment needed" verdict for both** — the funding/direction signal for the
      perp-enabled one is now well-understood and likely not a fresh design question; what remains genuinely open for
      both is how the lending-borrow leg (`lending_protocol`/`collateral_asset`/`debt_asset`) gets declared/triggered,
      and (for `CARRY_RECURSIVE_BORROW_LENDING_ONLY`) what signal drives entry/exit for a leg-less pure lending-carry
      position. Plausibly a materially smaller build for both than previously scoped, but NOT yet re-scoped or
      dispatched — pending a closer read of `declare_leg_portfolio_state()`'s multi-leg composition contract and how the
      orchestrator (execution-service) resolves a lending-leg vs. a spot-buy leg from the SAME `LegPortfolioState`
      shape, and pending operator input on the still-genuinely-open signal/threshold questions.
- [x] [BACKEND] P1. **Phase 3 — CARRY_BASIS_DATED / CARRY_BASIS_DATED_INV — SHIPPED 2026-07-24,
      `strategy-service@b280d27a`.** The config-key mismatch this entry originally flagged (catalog emitting
      `cash_venue`/`dated_venue`/`instrument` vs the engine's `spot_venue`/`future_venue`/`spot_instrument`/
      `future_instrument`) was ALREADY FIXED by an earlier same-day commit (`strategy-service@b5d293d0`, "fix(strategy):
      align CARRY_BASIS_DATED(_INV) catalog config keys with CarryBasisDatedEngine" — verified via
      `git log`/`git blame` + 139 lines of its own contract tests before this build started); this shipment is
      specifically the remaining tick-loader-wiring half. Real catalog row count (re-verified by reading
      `catalog_carry.py` directly, not the audit's "11 rows" figure, which undercounted): `build_carry_basis_dated()`
      has 16 rows (3 commodity + 2 equity-index + 2 crypto + 2 ETF-vs-CME-micro + 2 intra-Deribit + 5
      `status=databento_pending` placeholders), `build_carry_basis_dated_inv()` has 3 (2 crypto + 1 commodity) — 19 rows
      total across both archetypes. **Data-coverage finding (the catalog's own comment pointed at
      `paired_price_dispersion` — verified, not assumed):** that feature group has **NEVER been computed/persisted in
      prod for ANY row** — direct GCS listing (2026-07-24) found ZERO `xinstrument/` objects in the CEFI/TRADFI/DEFI
      `features-*` buckets (the features-cross-instrument-service batch dispatch that would write it has never run). So
      the tick loader instead computes `basis_bps` DIRECTLY from real raw-tick mid-prices, independently re-implementing
      the exact same formula the (unrun) kernel documents (`spread_bps = (future_mid - spot_mid) / spot_mid * 10_000`,
      annualised `× 365 / days_to_expiry`; spot=left/future=right, so positive = contango, matching the engine's
      documented sign convention with no flip needed) — a new `CanonicalSpotMarkProvider` (Binance spot
      `book_snapshot_5`, real `BTCUSDT.parquet`/`ETHUSDT.parquet` verified) for the spot leg, reusing Phase 1's
      already-shipped `CanonicalDatedFutureMarkProvider` (Deribit dated-future `book_snapshot_5`, real objects verified
      2026-07-01..2026-07-20) for the future leg, referencing the front-quarter ("q1") contract via the same
      `resolve_current_dated_contract_expiry` resolver Phase 1 built. **Only 4 of the 19 rows are honestly wired** (the
      2 binance/deribit crypto rows in each archetype — real data verified on BOTH legs); the other 15 are excluded via
      a new `_basis_dated_config_satisfiable()` gate (`paper_universe.py`, mirroring the
      `_yield_rotation_lending_config_satisfiable`/`_yield_staking_simple_config_satisfiable` pattern) with typed skip
      reason `missing_basis_dated_market_data:spot_venue=…,future_venue=…`: TradFi rows (3 commodity + 2 equity-index +
      2 ETF-vs-CME-micro in DATED, 1 commodity in DATED_INV) — the `features-tradfi-{env}-{pid}` bucket carries ZERO
      feature output of any kind (only manifest `_index/` files, verified by direct listing); the RAW tick bucket DOES
      carry real CME/ICE/CBOE data but under `instrument_type={futures_chain,combo,options_chain,index}`, none of which
      any existing reader parses as a flat per-contract shard (NASDAQ/NYSE ETF ticks also appear only intermittently) —
      a from-scratch TradFi bundled-chain/index/ETF resolver across 5 venues is a materially bigger, separately-scoped
      build, flagged not attempted; intra-Deribit rows (2) — the catalog's own comment already documents this ingestion
      as "currently partial…deferred," independently reconfirmed (no `instrument_type=index`/`spot` shard exists for
      DERIBIT); the 5 `databento_pending` placeholder rows — self-documented pending in the catalog already. **New
      finding, not fixed (documented, not silently papered over):** `CARRY_BASIS_DATED_INV`'s catalog sets a
      `direction: "SHORT_BASIS"` key that `CarryBasisDatedEngine.on_tick()` never reads at all (grepped the engine —
      zero references) — both archetypes share the identical engine class and currently behave IDENTICALLY; whether
      `SHORT_BASIS` should invert entry logic, restrict entries to backwardation only, or something else is a real
      product/design decision this build did not make unilaterally (same reasoning as Phase 1's dated-expiry- resolution
      hold) — the tick loader wires both archetypes against the engine's REAL current (shared) behavior, not a guessed
      one. `CARRY_BASIS_DATED_INV` added to `E2E_UNIVERSE_ARCHETYPES`; both archetypes added to
      `_ENGINE_DRIVABLE_ARCHETYPES` + the Layer-3 curtailment identity maps (`_VENUE_IDENTITY_KEYS`/
      `_CURRENCY_IDENTITY_KEYS`). New attribution/passive/transfers wiring in `run_paper` mirrors the
      ARBITRAGE_PRICE_DISPERSION dex-dispersion branch's shape (a venue-spread capture, not an accrual position) —
      `r.carry_rates_by_day` carries `(day, basis_bps, 0.0)` per day (genuine zero funding leg, no funding exists for
      this archetype). 12 new/updated unit tests (`test_canonical_spot_mark_provider.py`,
      `test_basis_dated_tick_wiring.py`, `test_paper_universe.py`): golden mid-price math, honest-absence (missing spot
      mark / missing future mark / unregistered venue), sign-convention proof (contango positive, backwardation
      negative), determinism (byte-identical ticks across independent runs against the same fixture corpus), and the
      satisfiability-gate regression guard (exactly 2 selected + 14 skipped for DATED, 2 selected + 1 skipped for
      DATED_INV). Quality gates: `strategy-service` `quality-gates.sh --no-fix` GREEN (fresh run, 5583 passed/206
      skipped/5 xfailed, all pre-existing; basedpyright clean on every touched file; STEP 5.101 empty-string-fallback
      ratchet held at the 166 baseline — this build's own new `.get(key, "")` sites were rewritten to direct indexing
      instead, since the satisfiability gate had already guaranteed key presence). Pushed via quickmerge, landed on
      `live-defi-rollout`; verified `git merge-base --is-ancestor b280d27a origin/live-defi-rollout` +
      `git rev-list --count origin/live-defi-rollout..HEAD` == 0.
- [x] [BACKEND] P2. **Phase 4a — YIELD_STAKING_SIMPLE — SHIPPED 2026-07-24, `strategy-service@5cc6e98b`.** Config keys
      (`staking_protocol`/`asset`) were pre-verified CLEAN this session (no catalog/engine contract-drift bug, unlike
      Phases 1/3's landmines) — a genuine tick-loader-wiring task. Real data-coverage finding: the catalog's 6th row
      (`ethena`) is DELIBERATELY EXCLUDED from this build, not a "couldn't find it" punt — sUSDe (UAC
      `LST_TOKEN_TO_PROTOCOL_ASSET`'s `ETHENA`/`USDE` token) was REMOVED from MTDS's `lst_rates` collector 2026-07-23
      (`lst_venue_registry_gap_and_cron_crash_loop_2026_07_22.md`, same day as this doc) because it is an ERC-4626
      yield-bearing vault share, not a genuine staking-derivative redemption rate; its real, current data home is
      `vault_share_price_handler.py`'s `vault_share_price` feature group (a DIFFERENT corpus from `lst_yields`), already
      consumed by DEFI_LP_VAULT's own `ethena`/`sUSDe` catalog row (`catalog_yield_defi.py:: build_defi_lp_vault()`) —
      no proxying attempted, held out with a static, typed `paper_universe.py` skip reason
      (`missing_lst_yields_coverage:staking_protocol=ethena`, visible in `skipped_specs.json`). Shipped the other 5 rows
      (lido/rocketpool/etherfi/jito/marinade): `_load_yield_staking_simple_ticks()` +
      `_build_yield_staking_simple_tick()` (`paper_run_handler.py`, single-leg — no `leg_state` needed, a
      `StakeInstruction`/`UnstakeInstruction` fill reads the snapshot's top-level fields directly), a new
      `YIELD_STAKING_SIMPLE_LST_ASSET` static protocol→token map + `_yield_staking_simple_config_satisfiable()` gate
      (`paper_universe.py`, since this archetype's catalog carries no `lst_asset` key at all — only
      `staking_protocol`/`asset` — unlike the other LST archetypes), `YIELD_STAKING_SIMPLE` added to
      `_ENGINE_DRIVABLE_ARCHETYPES`, and dedicated minimal single-leg passive/attribution producers
      (`build_yield_staking_simple_passive`/`build_yield_staking_simple_attribution` — ONE `STAKING_REWARD`/`CARRY` leg
      only, no lending/funding leg exists for this archetype, reusing `CanonicalLstYieldsIndexProvider` +
      `index_ratio_accrual` unchanged). Quality gates: lint/basedpyright clean on every touched file; 121 new/updated
      unit tests green (satisfiability gate, tick-loader honest-absence + determinism, passive/attribution single-leg
      shape). In passing, fixed a PRE-EXISTING, unrelated empty-string-fallback ratchet regression (2 lines,
      `pnl_input_builder.py:293`/`signal_broadcast/transport.py:369`, both genuinely-safe optional-field cases —
      `# noqa: qg-empty-fallback` added) that had pushed `strategy-service` from 166 to 168 sites (baseline 166),
      blocking `quality-gates.sh` STEP 5.101 for the whole repo regardless of archetype.
- [x] [BACKEND] P2. **Phase 4b — YIELD_ROTATION_LENDING — DONE 2026-07-24, `strategy-service@aa2abae3`.** The pre-check
      found a real config-key mismatch (catalog's `rotation_min_delta_apy_bps` vs the engine's never-set
      `min_apy_advantage_bps` — every row's real per-row threshold was silently discarded for a hardcoded 25bps
      default); fixed by making the engine read the catalog's real key. Also fixed the dead cross-chain/bridge logic
      (`current_chain` now falls back to the catalog's real `chain` key, exact for 11 of 12 rows; the one cross-chain
      "meta-rotation" row's real bridge-routing decision is deliberately left unbuilt — a documented judgment call, not
      a guess). New `CanonicalLendingSupplyApyProvider` reads real features-onchain `lending_rates` supply APY (verified
      against real prod GCS, 2026-07-24): AAVE_V3/COMPOUND_V3/SPARK resolve for real coverage; MORPHO and KAMINO never
      appear in the corpus at all (permanent data gaps, not transient) — the KAMINO-only catalog row is honestly
      excluded via a new satisfiability gate, mirroring the Phase 4a precedent, rather than fed guaranteed-empty data.
- [x] ✅ [BACKEND] P2. **Phase 5 — LIQUIDATION_CAPTURE — HELD-FINDING, 2026-07-31 (slot 11, backend_engineer),
      `defi_satellite_ao_dispatch_batch3-005`.** Ran the mechanical pre-check (catalog `initial_config` keys vs
      `LiquidationCaptureEngine.on_tick`/read pattern) and confirmed the engine `on_tick` (`liquidation_capture.py:68`)
      is NOT a stub — real gating logic (health-factor threshold, profit-after-gas/slippage) and a real 5-leg
      `AtomicInstruction` emission. But structurally it can NEVER fire from a day-partition paper-replay tick: `on_tick`
      hard-gates on `if not all([protocol, chain, debt_asset, collateral_asset, underwater_address]): return []` (line
      ~115), and BOTH catalog sources — `catalog_yield_defi.py::build_liquidation_capture()` (7 rows) and
      `archetype_slots_defi.py`'s `DEFI_SLOTS["LIQUIDATION_CAPTURE"]` (1 row) — leave `debt_asset`/`underwater_address`
      DELIBERATELY EMPTY on every row (re-read both sources directly this session, not trusting the 2026-07-23 finding:
      both carry the exact comment confirming this is intentional, not an oversight). Re-verified fresh (not
      re-guessing) that no live-injection/params-mutation path has been added since 2026-07-23: `orchestrator.py`'s
      `register_instance()` still constructs the engine's `params` ONCE via `ArchetypeEngineFactory.build(...)` and
      `on_allocation_directive()` only carries rebalance/equity fields — no API exists anywhere in
      `BaseArchetypeEngineV2`/`V2EngineOrchestrator` to inject a per-event identity (`debt_asset`/`underwater_address`)
      into a running engine instance mid-replay. This is unchanged from this doc's own 2026-07-23 finding (same section,
      above) — the blocker is a genuine unbuilt live-injection integration (same class as
      `CARRY_RECURSIVE_BORROW_LENDING_ONLY`'s `RecursiveLoopOrchestrator` gap), not a threshold/config decision, and per
      this doc's `Recommendation` section that live-injection integration is already flagged as its own not-yet-scoped
      follow-on requiring operator/design input — building it here would mean either fabricating
      `debt_asset`/`underwater_address` values (a fake signal, explicitly disallowed) or adding LIQUIDATION_CAPTURE to
      `_ENGINE_DRIVABLE_ARCHETYPES` as dead code that can never actually emit. **Not adding LIQUIDATION_CAPTURE to
      `strategy_service/cli/handlers/paper_universe.py`'s `_ENGINE_DRIVABLE_ARCHETYPES`, and not building a
      `_load_liquidation_capture_ticks()` tick loader** — zero fabricated wiring, per this doc's and the batch3 todo's
      own stated honest-finding branch. No code shipped this session (investigation-only, confirmed via fresh code
      reads). Cross-referenced to `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s todo 5, flipped there too citing
      this entry.
- [x] [BACKEND] P1. **After Phases 1-5 — Layer-3 curtailment mechanism SHIPPED 2026-07-24,
      `strategy-service@f3e9d748`.** Built exactly the design sketch in this doc's Finding 1 + the RESUME POINT 3-layer
      architecture: `PaperUniverseConfig` gains two sibling fields to the (still separately unwired) `archetypes` field
      — `venue_allowlist: dict[StrategyArchetype, frozenset[str]] | None` and
      `base_currency_allowlist: dict[StrategyArchetype, frozenset[str]] | None`, both `None`-default (byte-identical to
      today when unset — verified by an explicit regression test comparing a default-constructed config against one with
      both fields explicitly passed as `None`). Per-archetype key-role maps (`_VENUE_IDENTITY_KEYS` /
      `_CURRENCY_IDENTITY_KEYS`, `paper_universe.py`) reconcile each archetype's own literal `initial_config` key names
      for venue vs currency identity — read from all 4 catalog family files
      (`catalog_carry.py`/`catalog_staked_basis.py`/`catalog_yield_defi.py`/`catalog_trading.py`) for the 11 archetypes
      in `_ENGINE_DRIVABLE_ARCHETYPES` (e.g. `staking_protocol`+`perp_venue`+`spot_venue` for CARRY_STAKED_BASIS;
      `candidate_venues`/`instrument` — both comma/`/`-delimited multi-value, split + ANDed — for
      ARBITRAGE_PRICE_DISPERSION) plus the 2 MEV archetypes' `chain` key. The filter (`_curtailment_reason_for_spec` in
      `paper_universe.py`) runs as a new, dedicated function called INSIDE `_resolve_drivable()` BEFORE
      `_skip_reason_for_spec()` — a curtailed spec never reaches the paper-drivability gate at all — and reuses that
      function's exact honest-skip convention with the new typed reason `curtailed_by_operator_constraint` (carrying
      `axis=venue|currency` + the actual disallowed token(s), e.g.
      `curtailed_by_operator_constraint:axis=venue,disallowed=ARBITRUM`). Semantics: per archetype+axis, EVERY identity
      token a spec's `initial_config` carries must be within the operator's allow-list for the spec to survive (an "only
      Lido + Deribit" constraint curtails a row that ALSO touches some other venue, not merely one that fails to touch
      Lido/Deribit) — case-insensitive (catalog casing varies row-to-row, e.g. `"DERIBIT"` vs `"deribit"`). **The two
      MEV archetypes' known limitation is handled explicitly, not silently**:
      `ARBITRAGE_MEV_LIQUIDATION_BUNDLE`/`ARBITRAGE_MEV_BACKRUN` are mapped to an EXPLICIT empty tuple in
      `_CURRENCY_IDENTITY_KEYS` (deliberate, not an omission) since both genuinely have no catalog-declared
      base-currency key (`candidate_ids: ""`); a `base_currency_allowlist` entry for either is a documented,
      logged-once-per-archetype NO-OP (`_warn_if_currency_axis_is_noop`) — never applied, never silently "succeeds",
      never a crash (proven by a dedicated test asserting the run doesn't raise AND the skip reason stays the
      pre-existing `engine_tick_builder_unwired`, never the curtailment one). Venue-axis filtering DOES apply to these
      two — verified (not assumed) by reading both catalog builders: `chain` is a real, enumerable, per-row identity
      value (ETHEREUM/ARBITRUM/BASE) — proven by a second dedicated test showing a `venue_allowlist` entry genuinely
      curtails the non-matching chains' rows. 9 new unit tests (`tests/unit/cli/handlers/test_paper_universe.py`):
      backward-compat no-op, single-axis narrowing (venue and currency each), AND-composition across both axes, an
      unlisted archetype staying unconstrained, case-insensitive matching, and the two MEV no-op/does-apply proofs.
      Quality gates green (`quality-gates.sh --no-fix`, fresh run, 5568 passed/206 skipped/5 xfailed — the xfails are
      Phase-4/pre-existing catalog/engine contract-drift findings unrelated to this change; basedpyright clean on both
      touched files; STEP 5.101 empty-string-fallback ratchet held, my one new `.get(key, "")` site carries
      `# noqa: qg-empty-fallback` matching the established convention). **Deliberately NOT built (documented follow-on,
      not silently claimed done)**: no CLI/operator-facing surface to actually SET these fields on a live `run_paper`
      invocation. This doc's own Finding 1 already flags that `PaperUniverseConfig.archetypes` — the pre-existing,
      already-shipped sibling field this todo explicitly builds alongside — has the identical gap (`service_entry.py`
      calls `run_paper(...)` without ever passing `universe_config`); there is no existing `--archetypes`-style CLI flag
      to mirror for the new fields, and inventing one from scratch (argparse plumbing + a flat-string encoding for a
      `dict[StrategyArchetype, frozenset[str]]` structure, e.g.
      `--venue-allowlist 'CARRY_STAKED_BASIS:DERIBIT,BINANCE'`) is a materially separate, bigger piece of work than the
      mechanism itself, per this todo's own scope note ("build the mechanism, not necessarily full operator-facing
      plumbing"). Follow-on, not filed as a new gap since it's the same pre-existing one Finding 1 already named.
- [x] [BACKEND] P3. **DONE 2026-07-24, `strategy-service@3ad3f0b5`**. Layer-1 dynamic ADV-ranked candidate discovery
      folded into `CARRY_BASIS_PERP`/`CARRY_FUNDING_DISPERSION`'s catalogs, replacing the static 13-coin list as an
      opt-in (`ENABLE_DYNAMIC_CARRY_UNIVERSE`, default `False` — byte-identical to today's catalog, zero GCS I/O, when
      unset; verified via `test_build_carry_basis_perp/_funding_dispersion_is_byte_identical_to_static_baseline`). New
      `canonical_adv_ranked_universe_provider.py` independently re-implements the honest-absence-gated rolling-ADV read
      (does NOT import features-service's `adv.py` — verified against real prod GCS that `adv.py`'s own documented
      path/schema convention returns zero rows unconditionally today: wrong timeframe key `24h` vs real `1d`, a missing
      `instrument_type=` path segment, a non-existent `quote_volume` column, and `derivative_ticker`'s hardcoded-zero
      `volume` — flagged in-module for features-service's own owners, not fixed here). Falls back to the static list on
      any read failure or empty ranked result.
- [x] [DOCS] P3. **DONE 2026-07-26, `strategy-service@8d7c6549`**. Explicitly OUT of the tick-builder-wiring scope:
      `ARBITRAGE_MEV_LIQUIDATION_BUNDLE`, `ARBITRAGE_MEV_JIT_LIQUIDITY`, `ARBITRAGE_MEV_BACKRUN` — architecturally
      opportunistic/runtime-mempool-driven, no catalog-declared currency universe to build a day-partition tick loader
      against. Flagged, not silently dropped — a currency constraint for these three would need new logic inside the
      engines themselves, a materially different (and separately-scoped) piece of work. Written down permanently in
      `strategy_service/cli/handlers/paper_universe.py` directly after the `_ENGINE_DRIVABLE_ARCHETYPES` frozenset
      definition (module-level comment naming all 3 archetypes + this doc as source).
- [x] [BACKEND] P2. Side-decision 1 — **DELETED 2026-07-24, `strategy-service@813ec66b`** (dead code, Finding 2 above;
      whole class was dead, not just `allowed_venues` — see Finding 2's resolution note).
- [x] [BACKEND] P2. Side-decision 2 — **SHIPPED 2026-07-24, `unified-api-contracts@211e0d05` + `e2e-testing@0000f5d8`**.
      Built the addendum's recommended (A) — a one-directional containment gate (catalog TargetInstanceSpec venues ⊆ UAC
      eligible_venue_ids per leg role, NOT equality) — and ran it against the REAL current corpus for all 19 in-scope
      archetypes (`e2e-testing/scripts/defi/archetype_venue_containment.py`, 531 real `TargetInstanceSpec` rows
      scanned). Found 17 distinct (archetype, leg, venue) violations beyond the addendum's 2 already-known ones
      (CARRY_BASIS_PERP's aster/kalshi-perp/polymarket-perp on the perp leg + deribit/aster on the spot leg) — ALL
      genuine catalog-has-it-UAC-doesn't gaps, none triaged away: missing `etherfi` (CARRY_STAKED_BASIS/_DATED stake
      leg + CARRY_RECURSIVE_STAKED loop_stake), missing `compound_v3` (CARRY_RECURSIVE_STAKED
      loop_collateral/loop_borrow), missing `ice`/`cme`/`nymex`/`cboe` (CARRY_BASIS_DATED(_INV) spot leg — the
      commodity/equity-index TradFi rows), missing `aster`/`kalshi_perp`/`polymarket_perp` (CARRY_FUNDING_DISPERSION),
      missing `ethena` (YIELD_STAKING_SIMPLE), missing `spark` (YIELD_ROTATION_LENDING), missing `aerodrome`/`raydium`
      (LIQUIDATION_CAPTURE swap leg), missing `ethena`/`maker` (DEFI_LP_VAULT), missing `raydium` (CARRY_BASIS_PERP's
      cross-venue-DEX spot row), and — the largest cluster — ARBITRAGE_PRICE_DISPERSION's buy/sell legs missing
      `aave_v3`/`compound_v3`/`morpho` (lending-protocol-arb sub-family), `betfair`/`matchbook`/ `kalshi` (bare
      event-market ids, distinct from the routing-specific `betfair_direct`/`kalshi_perp` already cited), `cme`
      (cross-venue dated-futures-arb sub-family), and `camelot_v3`/`pancakeswap_v3`/`orca`/`raydium`/`phoenix`/
      `aerodrome_v3`/`sushiswap_v3` (the DEX cross-venue spot-dispersion sub-family — 10 DEX pairs read off
      `unified-api-contracts/.../archetype_leg_spec_seeds.py`'s `_price_dispersion_structure()`). Fixed every one
      directly in `archetype_leg_spec_seeds.py` (never touched strategy-service's catalog — containment direction is
      catalog→UAC only). **gmx/gmx_v2 naming question resolved as legitimately-different, NOT a bug**: grepped both
      systems' consumers — UAC's OWN `registry/` layer (`venue_collateral.py`, `venue_adapter_keys.py`,
      `defi_venues.py`) canonically keys this perp DEX as bare `GMX` (matching what the catalog emits), while UAC's
      `architecture_v2/` layer (`archetype_leg_spec_seeds.py` + 4 sibling modules — `collateral_registry.py`,
      `jurisdiction_overlay.py`, `order_semantics.py`, `simulation_assumptions.py`, `liquidation_bonus_schedule.py`)
      independently, consistently uses `gmx_v2` for the SAME real venue (GMX's V2 contracts per
      `venue_launch_dates.py`'s own comment). Kept `gmx_v2` as-is (consistent with its own module family); the
      containment check aliases `gmx`↔`gmx_v2` (+ `aave`↔`aave_v3`, `compound`↔`compound_v3`, `uniswap`↔`uniswap_v3`,
      `balancer`↔`balancer_v2` — same catalog-short-token-vs-UAC-versioned-token pattern, each verified via
      `venue_adapter_keys.VENUE_PREFIX_TO_PROTOCOL` before aliasing, never guessed). **Homed in `e2e-testing`
      (`scripts/defi/archetype_venue_containment.py`), not either repo it checks**: `unified_api_contracts` is T0-base —
      zero workspace imports, not even in tests (`/codex/04-architecture/tier-and-import-architecture.md`, re-verified,
      not just cited) — so a check importing both strategy-service (T4) and UAC (T0) can never live in UAC, and putting
      it in strategy-service would make one T4 service arbiter of a T0 schema; e2e-testing already declares editable
      deps on both. 36 unit tests (`e2e-testing/tests/unit/test_archetype_venue_containment.py`) cover the containment
      LOGIC itself on synthetic catalog/UAC fixtures (pass/fail/alias/CSV-split/excluded-token/UAC-broader-is-fine
      cases) PLUS a real-corpus regression test (`test_real_corpus_is_currently_contained`) that is now the ongoing CI
      gate catching this class of drift automatically going forward. Both repos' `quality-gates.sh --no-fix` green;
      pushed + verified reachable on `origin/live-defi-rollout` (`git merge-base --is-ancestor` both shas).
- **[BACKEND] P2. CANCELLED — extracted 2026-08-16 (na-eligibility-audit) → `/plans/active/defi_archetype_catalog_identity_extension_ao_dispatch_2026_08_16.md` (+ finalize)** — the
      scope/sequencing decision this item was blocked on was ruled 2026-08-16 (build for all ~26-29 archetypes now, see
      this doc's own 2026-08-16 Progress Log entry); the resulting AO-dispatchable work is tracked there, not here.
      Original finding 2026-07-28, redirected here from `mvp_scope_resolver_code_read_2026_07_24.md`'s P2
      todo — MVP_SCOPE catalog enforcement was blocked on a MISSING catalog-identity precondition, not just a missing
      filter. That doc's own audit (2026-07-26) found strategy-service's catalog never restricts itself to UAC's
      canonical `MVP_SCOPE` (`unified_api_contracts.canonical.crosscutting._mvp_scope_predicate.is_mvp`) and asked for
      an `is_mvp(...)` post-filter inside/after `catalog.py`'s `specs_for_archetype()` — the SAME shape as this doc's
      own Layer-2 design sketch (Finding 1) and Layer-3 `_curtailment_reason_for_spec`/`_VENUE_IDENTITY_KEYS` mechanism.
      **Verified blocker (2026-07-28, this session)**: `is_mvp()`'s `instrument_type` parameter is REQUIRED with no
      default and no "unbound" convention (unlike `data_type`, which explicitly treats blank as "any MVP data_type" —
      `_data_type_in_rule`'s docstring) — passing an empty/guessed `instrument_type` fails the CeFi/DeFi/TradFi
      membership check outright (`if instrument_type not in rule.instrument_types: return False`). Grepped every catalog
      builder for a literal `"instrument_type"` key: only 3 rows declare it (`catalog_trading.py`'s
      `MARKET_MAKING_CONTINUOUS`, and even those use non-canonical lowercase values `"spot"`/`"perp"`/`"options"`
      instead of UAC's canonical `SPOT_PAIR`/`PERPETUAL`/`OPTION` enum strings) — every CARRY/YIELD/ARBITRAGE/
      DIRECTIONAL builder (~26 of ~29 archetypes) has NO instrument_type identity in `initial_config` at all; it's
      implicit in the engine's `on_tick()` logic, never surfaced as catalog data. `asset_group` (cefi/defi/tradfi/
      sports/prediction) is similarly not a stored field, and is NOT even a per-archetype constant — e.g.
      `CARRY_BASIS_PERP`'s venue bundles mix CeFi (`deribit`/`binance`/`bybit`) and DeFi (`gmx`/`hyperliquid`) venues in
      the SAME archetype (per this doc's own Addendum 2026-07-24), so it must be derived per-VENUE via a UAC
      venue→asset_group classifier that doesn't currently exist as a single ready function (would need composing
      `unified_api_contracts.registry.defi_venues.ALL_DEFI_VENUES` + a CeFi venue set + a TradFi venue set). **Real,
      scoped follow-on (NOT actioned — needs an operator scoping decision, same as this doc's own Recommendation
      section)**: (1) extend the per-archetype catalog builders with a canonical `instrument_type`/`asset_group`
      identity per row (mirroring how `_VENUE_IDENTITY_KEYS`/`_CURRENCY_IDENTITY_KEYS` reconcile each archetype's own
      literal config-key names for the venue/currency axes) — this is genuinely per-archetype, per-engine domain work
      (same "fiddly part" this doc's own Finding-1/A-recommendation already flagged for the venue-containment check, at
      comparable or greater size given ~26 archetypes vs. the venue check's already-built subset), NOT a small
      filter-function task; (2) only once that identity exists can a real `is_mvp()`-backed curtailment reason
      (`not_mvp_scope`, alongside the existing `curtailed_by_operator_constraint`) be added safely to
      `_resolve_drivable()`. Do NOT guess `instrument_type`/`asset_group` values to unblock this faster — a wrong guess
      silently mis-filters the LIVE/paper production strategy universe (drops MVP specs or keeps non-MVP ones), worse
      than leaving the gap open. Scope/sequencing decision needed before dispatch: build this for all ~29 archetypes vs.
      the already-`_ENGINE_DRIVABLE_ARCHETYPES` subset first (mirrors this doc's own Layer-3 phasing).

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

**RESOLVED 2026-07-23 (`strategy-service@606f2fb5`) — decisions (1) and (2) above, made**: (1) `dated_expiry` resolves
to the CURRENT wire-executable Deribit symbol via a new pure `resolve_current_dated_contract()`
(`carry_and_yield/dated_contract_resolver.py`), targeting the legacy-style `{ASSET}-{DD}{MON}{YY}` grammar (e.g.
`ETH-25SEP26`) — this is the form `execution-service`'s real `deribit.py` order-placement adapter
(`_canonical_to_deribit_symbol`/`_deribit_to_canonical_id`) round-trips today, NOT the newer decomposed wire-canonical
MTDS/GCS filename form (`ETH-USD@INV-20260925`) — the two are orthogonal (data-storage convention vs order-placement
convention) and this fix deliberately targets the latter, matching the plain archetype's existing
opaque-`perp_instrument`-string contract. The rule itself: Deribit's real quarterly expiry is the LAST FRIDAY of
March/June/September/December — verified against 4 independent real dated-future symbols (`ETH-27MAR20`, `ETH-26JUN20`,
the 2026-07-15 `DERIBIT:FUTURE:ETH-USD@INV-20260925` wire object, and execution-service's own `BTC-29DEC23` docstring
example), not assumed from convention alone. (2) Roll logic SHIPS NOW (not deferred): the resolver rolls `"q1"` forward
to the next quarter once within `roll_on_dte` days (inclusive) of the held contract's expiry, and `"q2"` is always
defined as "the quarter after whichever contract q1 currently resolves to" so the front/back-quarter strategy instances
stay mutually consistent. Wired into `_extract_config` (gated on `dated_expiry` presence, so the plain archetype's
static-literal path is untouched) and threaded through `on_tick` / `declare_leg_portfolio_state` /
`react_to_equity_change`. Pure + deterministic: identical `(native_asset, dated_expiry_tag, now_utc, roll_on_dte)`
always re-derives the identical symbol (a batch rerun over the same window re-derives the identical held-contract
sequence a paper run saw). Catalog config keys fixed in the SAME change as this resolver (per this doc's own
recommendation above) — `build_carry_staked_basis_dated()` now emits
`staking_protocol`/`perp_venue`/`spot_venue`/`start_token` matching `REQUIRED_PARAMS`, with `perp_instrument` dropped in
favor of `dated_expiry`+`roll_on_dte`. The paper-replay TICK-LOADER build itself (`_load_staked_basis_dated_ticks()` +
`_ENGINE_DRIVABLE_ARCHETYPES` registration) is intentionally NOT part of this change — it is the remaining, still-open
half of the Phase 1 checkbox above, now unblocked for a follow-on dispatch. Full test evidence:
`tests/unit/engine/strategies/v2/test_carry_staked_basis_dated_contract_resolution.py` (golden dated-future values,
roll-boundary + determinism proofs, and a real-catalog-spec construction/`on_tick` proof).

## Progress Log addendum

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 7, operator ruling)**: the MVP_SCOPE catalog-identity
  precondition's scope/sequencing question is RULED — build for all ~26-29 archetypes now, not just the
  `_ENGINE_DRIVABLE_ARCHETYPES` subset. Extracted to
  `/plans/active/defi_archetype_catalog_identity_extension_ao_dispatch_2026_08_16.md` (+ finalize) for AO dispatch,
  since this doc stays `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-01**: KEEP-NA valid — both remaining open checkboxes (RecursiveLoopOrchestrator gap,
  MVP_SCOPE catalog-identity precondition) are explicitly operator-design-gated per their own text ("Verdict: still
  correctly NOT AO-dispatchable ... Remains parked pending an operator design/scoping session"; "Scope/sequencing
  decision needed before dispatch"). No stale/duplicate/reclassify-eligible items found. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-01**: populated/refreshed context_scope (6 entries).
- **na-eligibility-audit 2026-08-03**: KEEP-NA valid — re-confirmed independently. Only diff since 2026-08-01 was the
  context-scout metadata backfill (no content change). Both open checkboxes remain explicitly operator-design-gated per
  their own text. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-03**: found the prior marker's entry count (6) did not match the actual list (11, grown past
  the 2-6 budget) — trimmed to 6 entries, retargeted at the two genuinely still-open todos (RecursiveLoopOrchestrator
  gap; MVP_SCOPE catalog-identity precondition), dropping fully-resolved-phase references
  (`defi_catalog_engine_config_key_contract_drift_2026_07_23.md`,
  `pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md`, `archetype_leg_spec_seeds.py`, `factory.py`,
  `basis_perp.py`, the bare `target_universe/` dir).
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **context-scout 2026-08-07**: re-scouted; context_scope re-verified (6 entries), unchanged — all 6 still resolve and
  still map directly onto the 2 genuinely-open, operator-design-gated todos (recursive-loop archetype gap; MVP_SCOPE
  catalog-identity precondition).
- **na-eligibility-audit 2026-08-06** (tranche=defi, dispatch agt-e00d37): KEEP-NA valid — both open checkboxes (line
  389 recursive-loop archetype design gap w/ 3 layered dated corrections, most recently 2026-07-24; line 687 MVP_SCOPE
  catalog-identity precondition, explicit operator-scoping-decision gate) independently re-confirmed against the
  2026-08-01/08-03 audit passes. Zero corpus traps found (no DECOMMISSIONED/RE-TRIAGE/revert markers). Incidental, not
  actioned: 1 untracked prose-only item (CLI/operator plumbing to set already-shipped `PaperUniverseConfig` fields on
  `run_paper`) and 1 stale "Recommendation" section (lines 236-244) whose 3 decisions were already made+shipped later in
  this same doc — hygiene cleanup candidates for a future pass, not reclassification triggers. Doc stays
  `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA valid — re-confirmed independently; no content change
  since the 2026-08-06 audit (context-scout metadata only, per git log). Both open checkboxes (recursive-loop archetype
  design gap; MVP_SCOPE catalog-identity precondition) remain explicit operator-design-gated per their own text.
- **round11-sweep 2026-08-09** (defi tranche, satellite-extraction + RECLASSIFY re-check): re-read end to end (2 open
  checkboxes at entry: the `RecursiveLoopOrchestrator` new-trading-logic gap for `CARRY_RECURSIVE_BORROW_LENDING_ONLY`
  /`CARRY_BASIS_PERP_INV`, needing operator-supplied risk-threshold/entry-signal decisions; the MVP_SCOPE
  catalog-identity precondition, needing an operator scope/sequencing decision across ~26-29 archetypes). Checked
  against every accumulated round11 precedent (IAM self-service, D16 all-repos, S5.1 tiering,
  plan-destination-defaults-AO-dispatched, escalation-N=3-days, reversibility-qualified deletes, Option B retired, GSM
  secret + 5 Slack webhooks now existing) — none bear on either item: both are open-ended trading-logic/architecture
  design calls (dispatch-scope-eligibility rule: "figure out how X should look" is a human decision, not a checkable
  worker todo), not blocked by any infra/credential/process precedent this round settled. No satellite-extraction
  candidate found. Doc stays `assigned_vm: NA` (KEEP-NA valid, round11). Doc stays `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-16** [body-hash:6bb357488f3768d0]: KEEP-NA-STALE (already-duplicated), applied — 891-line issue doc, almost entirely shipped/checked off across Phases 0-5. Sole remaining open item (the MVP_SCOPE catalog-identity precondition, line ~693) was flagged in-doc as blocked on a scope/sequencing decision; this doc's own 2026-08-16 Progress Log entry records that ruling landing today (build for all ~26-29 archetypes now) and the resulting work extracted to /plans/active/defi_archetype_catalog_identity_extension_ao_dispatch_2026_08_16.md (+ finalize, both confirmed live on disk: assigned_vm:planning, status:active, correct Source: citation). Converted the stale open checkbox to a citation marker this run (was never flipped despite the extraction already existing). Doc now has 0 open checkboxes remaining.
- **na-eligibility-audit 2026-08-17**: ARCHIVE-ready, reconfirmed — 0 open todos (fence-aware grep). archive_exempt: true remains deliberately set per this doc's own note (flip-then-mv two-commit pattern, check_archive_candidates.sh convention) — not executed this run (out of this skill's scope; hand off to the dedicated archive-candidates-audit pass).
- **CLOSED BY CITATION 2026-08-16 (defi_satellite_ao_dispatch_batch9_2026_08_06_finalize, source-doc reconciliation
  pass, slot 23, data_engineering)**: the "1 untracked prose-only item (CLI/operator plumbing to set already-shipped
  `PaperUniverseConfig` fields on `run_paper`)" flagged incidental-not-actioned by the 2026-08-06 na-eligibility-audit
  entry above is now shipped — `defi_satellite_ao_dispatch_batch9_2026_08_06.md` todo 5 (`strategy-service@8ee9894e`)
  added `--archetypes`/`--venue-allowlist`/`--currency-allowlist` CLI flags to `run_paper`'s `service_entry.py`,
  threaded into `PaperUniverseConfig` via `build_paper_universe_config`, with 16 unit tests + green
  `quality-gates.sh --no-fix`. No further hygiene action needed on this item.
- **context-scout 2026-08-17**: refreshed context_scope (6 entries) — swapped the archived MVP_SCOPE investigation doc
  for the active extraction plan (`defi_archetype_catalog_identity_extension_ao_dispatch_2026_08_16.md`) now owning the
  doc's one ruled-but-not-yet-shipped remaining scope; the doc itself is at 0 open checkboxes, archive-ready.
