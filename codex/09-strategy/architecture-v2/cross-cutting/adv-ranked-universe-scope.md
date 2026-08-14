---
doc_type: codex-ssot
title: ADV-Ranked Universe Resolution — Scope Ruling
summary:
  "ADV-ranked (liquidity-ranked) dynamic universe resolution (`rank_top_n_by_adv`, `engine/core/
  canonical_adv_ranked_universe_provider.py`) applies to archetypes whose tradeable universe is a BROAD, evolving
  candidate-coin pool filtered by liquidity — not to every archetype. Ruling: CARRY_BASIS_PERP and
  CARRY_FUNDING_DISPERSION are in scope; CARRY_STAKED_BASIS is deliberately NOT, because its universe is a small,
  curated (LST protocol × spot venue × perp venue) combinatorial set, not a liquidity-filtering problem."
status: current
nature: ssot
asset_group: [defi]
stage: [meta]
repos: [strategy-service]
scope: [engineer]
tags: [strategy, archetype, catalogue, universe-resolution, carry, adv]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-funding-dispersion.md,
    /plans/active/strategy_service_expansion_overlays_config_and_wizard_2026_08_12.md,
  ]
created: 2026-08-13
authoritative_for: [ADV-ranked dynamic universe resolution scope — which archetypes it applies to, and why]
referenced_by: []
owner:
last_reviewed: 2026-08-13
code_refs:
  [
    strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog_carry.py,
    strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog_staked_basis.py,
    strategy-service/strategy_service/engine/core/canonical_adv_ranked_universe_provider.py,
  ]
---

# ADV-ranked universe resolution — scope ruling

## The question

`rank_top_n_by_adv(candidates, venue, asset_group, as_of_date, top_n, window_days)`
(`engine/core/canonical_adv_ranked_universe_provider.py`) is archetype-blind by construction — it takes no `archetype`
parameter and ranks any candidate pool by measured average daily volume. As of 2026-08-12 it was wired into exactly **1
of 32** registered catalogue builders: `catalog_carry.py`'s `_resolve_dynamic_carry_coins()`, consumed by
`build_carry_basis_perp()` and `build_funding_dispersion()`. Every other builder — including
`build_carry_staked_basis()` in the same carry family — hardcodes its universe as a static tuple. Because the provider
itself doesn't care which archetype calls it, this asymmetry needed a stated reason or a fix, not silence.

## Ruling: scope is the SHAPE of the universe, not "carry vs. non-carry"

**ADV-ranked resolution applies to an archetype iff its tradeable universe is a broad, evolving pool of candidate COINS
that must be FILTERED BY LIQUIDITY to a tractable top-N.** It does not apply merely because an archetype is in the carry
family.

| Archetype                  | Universe shape                                                                                                                                                        | ADV-ranked? | Why                                                                                                                                                                                                                                                                           |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CARRY_BASIS_PERP`         | Any of ~30+ perp-listed coins across ~10 venues — a genuinely large, growing candidate pool where liquidity is the binding constraint                                 | **Yes**     | This is exactly the problem ADV-ranking exists to solve: rank a large pool, take the top N by measured volume                                                                                                                                                                 |
| `CARRY_FUNDING_DISPERSION` | Same shape — a cross-venue funding-dispersion book drawing from the same broad coin pool                                                                              | **Yes**     | Same reasoning as above; shares the provider and candidate pool machinery                                                                                                                                                                                                     |
| `CARRY_STAKED_BASIS`       | A small, curated (staking_protocol × lst_asset × spot_venue × perp_venue) combinatorial set — 3 ETH LSTs, 2 SOL LSTs, each crossed with a handful of spot/perp venues | **No**      | This is NOT a liquidity-filtering problem. There is no broad pool of "LST candidates" to rank by ADV — the universe is bounded by which LSTs exist and which venues accept them as collateral (`VENUE_COLLATERAL_MATRIX`), a capability question, not a liquidity-ranking one |

The test for a future archetype: **is its candidate set large enough, and liquid enough to vary meaningfully, that
picking the wrong N coins matters?** If yes, wire it onto `rank_top_n_by_adv` via the same pattern `catalog_carry.py`
uses. If the universe is instead bounded by a small, enumerable capability matrix (which venues accept which collateral,
which protocols exist), ADV-ranking adds no value — hardcoding (or a capability-matrix-driven enumeration, per
`_resolve_start_token`'s USDC_MARGIN_BUFFERED fallback,
`/codex/09-strategy/architecture-v2/cross-cutting/adv-ranked-universe-scope.md` § below) is the right mechanism.

## What this ruling does NOT do

It does not lift `rank_top_n_by_adv` to a shared "any archetype can opt in" helper today — the provider is already
archetype-blind at the function-signature level (no code change needed to make it callable from elsewhere), so
"platform-wide" was never a wiring question, only a per-archetype judgment call about whether that archetype's universe
is shaped like a liquidity-filtering problem. This doc is that judgment call, recorded once, so the next agent auditing
`target_universe/` doesn't have to re-derive it from the disclosed code.

## Provenance

Raised in `unified-trading-pm/plans/active/strategy_service_expansion_overlays_config_and_wizard_2026_08_12.md` §
"Decide whether ADV-ranked universe resolution is a carry feature or a platform one" (2026-08-12 audit) as an open
decision; resolved here 2026-08-13 (A7 follow-up, `service_config_ownership_and_instruction_contract_2026_08_12.md` § J7
dispatch).
