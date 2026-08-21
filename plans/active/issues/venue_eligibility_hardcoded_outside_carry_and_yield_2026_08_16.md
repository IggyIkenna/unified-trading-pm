---
doc_type: issue
title: >-
  Venue eligibility is centralized for exactly one family — every other strategy family hardcodes venue lists
  directly in the catalog builders, with no capability/collateral check against any registry
summary: >-
  `target_universe/venue_capabilities.py` looks like a general venue-eligibility gate but its own docstring admits
  it's single-purpose: real venue resolution only for carry_and_yield's perp-hedge leg
  (`carry_staked_basis`/`carry_basis_perp`); every other archetype gets `frozenset()` and a note to "consult the
  archetype catalog directly." Confirmed by grep: none of the other 8 in-scope families
  (arbitrage_structural, event_driven, market_making, mev, ml_directional, rules_directional, stat_arb_pairs,
  vol_trading) import `venue_capabilities.py`, `VENUE_COLLATERAL_MATRIX`, or `COLLATERAL_REGISTRY` anywhere. Their
  venues are plain string literals hardcoded directly into `catalog_trading.py`/`catalog_directional.py`'s catalog
  builder functions, with no eligibility/collateral/leverage check against any registry at build time or at the
  engine layer. Filed per operator direction to generalize centralized, config-driven, registration-based patterns
  beyond the DeFi-specific fix already filed.
status: open
nature: issue
asset_group: [meta]
stage: [execution]
repos: [strategy-service, unified-api-contracts]
scope: [engineer]
tags: [architecture, centralization, venue-eligibility, target-universe, config-driven]
related:
  [
    /plans/active/issues/defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md,
    /codex/04-architecture/position-risk-centralization.md,
  ]
created: 2026-08-16
author: interactive-session
parent_epic: security_and_cross_cutting_master
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4
assigned_role:
assigned_vm: NA
execution_scope: local-only
drift_direction: none
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
context_scope:
  [
    /codex/04-architecture/position-risk-centralization.md,
    strategy-service/strategy_service/engine/strategies/v2/target_universe/venue_capabilities.py,
    strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog_trading.py,
    strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog_directional.py,
    /plans/active/issues/defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md,
  ]
source: >-
  Interactive session 2026-08-16. Follow-up to the DeFi-scoped health-factor centralization finding — operator
  asked whether the audit covered all strategy families, not just DeFi/carry, and to generalize the pattern search.
  Agent-dispatched investigation confirmed and precisely scoped the gap for venue eligibility specifically.
---

# Venue eligibility is centralized for exactly one family

## Finding

`strategy_service/engine/strategies/v2/target_universe/venue_capabilities.py` reads like a general
asset-group/archetype-agnostic venue-eligibility resolver, but its own docstring says otherwise:
`perp_hedge_candidate_venues()` returns a real, capability-checked venue set only for `carry_staked_basis` and
`carry_basis_perp` — for every other archetype it returns an empty `frozenset()` with a note that "their venue set
is defined inline per slot... callers should consult the archetype catalog directly" (lines 184-189).

**Confirmed by grep: zero of the other 8 in-scope families import it, `VENUE_COLLATERAL_MATRIX`, or
`COLLATERAL_REGISTRY` anywhere** — `arbitrage_structural`, `event_driven`, `market_making`, `mev`,
`ml_directional`, `rules_directional`, `stat_arb_pairs`, `vol_trading` all have zero hits.

Where their venues actually come from instead: **plain string literals hardcoded directly into the catalog
builder functions**, no eligibility/collateral/leverage check against any registry, at build time or at the
engine layer:

- `catalog_trading.py:375,400` — `for venue in ("binance", "okx", "bybit", "hyperliquid"):` /
  `("binance", "bybit", "hyperliquid")` (MARKET_MAKING_CONTINUOUS)
- `catalog_trading.py:463` — `for venue in ("raydium", "orca")`
- `catalog_trading.py:502` — `for venue in ("betfair", "matchbook"):` (MARKET_MAKING_EVENT_SETTLED)
- `catalog_trading.py:477,574,639,657,685,717,740,775,800,819` — literal single venues (`"deribit"`, `"binance"`,
  `"cboe"`, `"ibkr"`) across VOL_TRADING_OPTIONS/EVENT_DRIVEN/STAT_ARB rows
- `catalog_directional.py:27,248,435` — `("binance", "okx", "bybit", "hyperliquid")` variants for
  ML_DIRECTIONAL/RULES_DIRECTIONAL/TSMOM
- `catalog_directional.py:59,79,140,161,182,203,224,286,308,366,385,408` — literal venues (`"ibkr"`, `"cme"`,
  `"unity"`, `"betfair"`, `"polymarket"`) across sports/tradfi rows

Downstream, the engines just consume whatever `venue_universe` string the catalog handed them (e.g.
`arbitrage_structural/price_dispersion.py:597`, `_parse_venue_universe`) — no re-check at the engine layer either.

**Practical risk**: nothing verifies these hardcoded venue/instrument pairings are still valid. If a venue changes
its supported instruments, delists something, or was never actually correct for a given row, there's no
capability check anywhere in the chain that would catch it — a config value gets treated as a fact.

## What is NOT a duplication problem (checked, ruled out)

`catalog_engine_coverage.py` is unrelated — a QG heuristic verifying catalogue config keys are read somewhere in
engine source, not a venue resolver. `archetype_slots_{cefi,defi,tradfi,sports}.py` are also not a duplication
problem — they're a mechanical 900-line-file split (2026-06-11) of one legacy-string→archetype/slot registration
table, sharing a common row dataclass and helper in `archetype_slots_common.py`. No reimplemented algorithm to
consolidate there; each file is a data table for a distinct asset class's legacy dispatch strings, not independent
eligibility logic.

## OPERATOR RULING 2026-08-21 — generalisation shape

ONE declarative capability-gated resolver per R17 (`/codex/04-architecture/cross-domain-state-fabric.md` §12):
each archetype DECLARES its venue requirements; a single generic resolver checks them against the UAC venue
capability registry; fail closed. No per-archetype bespoke gates. This closes the Wave-0 "venue-eligibility
generalisation shape" open ruling.

## Todos

- [ ] [OPERATOR] P1. **Decide the generalization shape**: extend `venue_capabilities.py`'s existing pattern to
      cover every family (grow `VENUE_COLLATERAL_MATRIX`/`COLLATERAL_REGISTRY` coverage, or build an equivalent
      catalog-wide venue-capability lookup keyed by asset_group/venue/instrument_type), versus accepting hardcoded
      catalog literals as a deliberate, lower-priority design choice for families where venue support changes
      rarely. Not free either way — scope before committing.
- [ ] [AGENT] P2. **If generalizing: audit every hardcoded venue literal above against the venue's actual current
      capabilities** (does OKX/Bybit/Hyperliquid/CME/IBKR/etc. genuinely support what each catalog row assumes,
      today) before building the lookup — the point of centralizing is catching drift, so start from a clean,
      verified baseline rather than encoding today's possibly-stale assumptions into the new registry.
- [ ] [AGENT] P3. **Add a regression check** once centralized: a catalog row whose venue lacks the assumed
      capability should fail loudly at build/test time, not silently ship a slot that can't actually trade.

## Progress Log

- **2026-08-16** — Filed from an interactive session, generalizing the DeFi-scoped centralization finding to all
  strategy families per operator direction. Agent-dispatched, read-only investigation; no code changed. The
  operator's original framing ("centralization is missing") was correct in spirit but pointed at the wrong
  evidence — `venue_capabilities.py` isn't being bypassed by the other 8 families, it was never built for them.
- **na-eligibility-audit 2026-08-17** (infra tranche) [body-hash:4e09dc58212eb9a8]: KEEP-NA, valid — todo 1 is explicitly [OPERATOR] P1-tagged (generalize vs accept hardcoded catalog literals, a genuine unresolved design decision); todos 2-3 are textually gated on todo 1's outcome.
- **na-eligibility-audit 2026-08-17** (infra tranche) [body-hash:4e09dc58212eb9a8]: KEEP-NA, valid — todo 1 is explicitly [OPERATOR] P1-tagged (generalize vs accept hardcoded catalog literals, a genuine unresolved design decision); todos 2-3 are textually gated on todo 1's outcome.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-20**: refreshed context_scope (5 entries)
