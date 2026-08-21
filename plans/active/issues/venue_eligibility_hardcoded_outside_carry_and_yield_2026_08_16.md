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

## Venue-literal capability audit — 2026-08-21

Ran the todo-2 audit early (useful regardless of todo 1's outcome per that todo's own note) against
`strategy_service/engine/strategies/v2/target_universe/catalog_trading.py` (1020 lines) and
`catalog_directional.py` (526 lines). Agent-dispatched, WebSearch-verified against each venue's own current docs,
not blog summaries. Full findings:

**Confirmed accurate** (no action needed): Deribit BTC/ETH options (`catalog_trading.py:528-546,684-742`) — still
dominant, 55%+ BTC options market share; Hyperliquid perps+spot on BTC/ETH/SOL (`catalog_trading.py:437,461`,
`catalog_directional.py:33,284,501`) — 150+ perp markets confirmed; dYdX BTC/ETH perps
(`catalog_directional.py:105-129`) — dYdX Chain v4 confirmed; CME micro BTC/ETH futures
(`catalog_trading.py:287-311`) — MBT/MET confirmed live; CME event contracts on SPX/Bitcoin
(`catalog_trading.py:957-1020`) — confirmed, CME expanded event contracts to Bitcoin May 2026; Camelot V3
(Arbitrum) — confirmed active; Kalshi/Polymarket BTC/ETH up-down markets (`catalog_trading.py:224-268`) —
confirmed, framing as prediction-market (not perp) trades is still correct.

**Drifted — real findings**:
- `catalog_trading.py:962-1020` — the exact CME event-contract root-symbol literals `"ECES"` (SPX) and `"ECBTC"`
  (BTC) could NOT be verified against CME's own symbol directory (CME's public docs surface the *futures* roots
  ES/MBT and describe event contracts generically, without a confirmed root-symbol table in reachable sources).
  The underlying capability (CME event contracts on SPX + Bitcoin) is real and current — only the specific root
  strings are unconfirmed. Needs a follow-up against CME's live product/symbol reference, not a blog.
- `catalog_trading.py:321-333` — **Phoenix (Solana) listed as a live CLMM/spot liquidity venue for SOL/USDC
  dispersion is drifted.** Phoenix's original CLOB spot exchange is now "Phoenix Legacy"; the actively-developed
  product, Phoenix Perpetuals, is in **private beta/waitlist** (announced Breakpoint 2025) — not a
  generally-available spot liquidity venue today. Treating it as live general-access spot liquidity is
  questionable as currently written.

**Not independently verified this pass** (flagged, not guessed): Aerodrome V3 (Base); the sports-family tokens
`unity`/`3et`/`sharpbet`/`vx` in `catalog_directional.py` (appear to be internal/codenamed venue keys, not public
sportsbook names — not verifiable against public docs either way); Betfair, Matchbook, Binance/OKX/Bybit
spot+perp, IBKR/CBOE options+equities+futures, and the remaining DEX list (Uniswap V3, Pancakeswap V3, Sushiswap
V3, Orca, Raydium) — long-standing, well-documented capabilities with no plausible drift signal found, deprioritized
vs. the two findings above.

## Todos

- [x] [OPERATOR] P1. ✅ **RULED 2026-08-21 — see "OPERATOR RULING" section above, citing
      `/codex/04-architecture/cross-domain-state-fabric.md` §12 (R17).** This todo went stale the
      moment the ruling landed (same recurring class the workspace flags — retag in the same edit, never leave
      it stale). ONE declarative capability-gated resolver, generalized to every family, fail-closed. Flipping
      now; todo 3 below is the buildable next step.
- [x] [AGENT] P2. ✅ **DONE 2026-08-21 — see "Venue-literal capability audit" section above.** pm@0fa40df01d.
- [ ] [AGENT] P2. **Build the resolver per the ruling — DON'T build the table from scratch, it already exists.**
      Audit finding 2026-08-21: `unified_api_contracts/internal/architecture_v2/archetype_capability.py`'s
      `ARCHETYPE_CAPABILITY_REGISTRY` is a genuine, hand-authored, per-`(archetype, asset_group, instrument_type)`
      cell table (status SUPPORTED/PARTIAL/BLOCKED, `venue_ids`, `roll_mode`, `block_list_refs`) covering EVERY
      archetype — loaded from `archetype_capability_manifest.json`. It has **zero callers in strategy-service**
      (only consumed inside `unified-api-contracts` itself, for slot-label generation and doc generation);
      neither `catalog_trading.py` nor `catalog_directional.py` imports it. This is broader than
      `venue_capabilities.py` (which is real capability-CHECKED but non-empty for only
      `carry_staked_basis`/`carry_basis_perp`) — the resolver should wire THIS table into the catalog builders as
      its primary source, not build a new venue-requirement declaration mechanism from scratch. Fail closed on an
      undeclared/unsupported combination. Fix the 2 real drift findings from the audit above (CME root-symbol
      confirmation, Phoenix's stale spot/CLMM-venue listing) as part of building the registry's baseline, not as
      a separate pass. **Also verify `archetype_capability_manifest.json`'s data is itself current** — it's
      hand-authored, not derived from live margin-model/execution-mechanics checks, so it may have its own drift
      independent of the catalog-literal drift already found.
- [ ] [AGENT] P3. **Add a regression check**: a catalog row whose venue lacks the assumed capability should fail
      loudly at build/test time, not silently ship a slot that can't actually trade.

## Progress Log

- **2026-08-16** — Filed from an interactive session, generalizing the DeFi-scoped centralization finding to all
  strategy families per operator direction. Agent-dispatched, read-only investigation; no code changed. The
  operator's original framing ("centralization is missing") was correct in spirit but pointed at the wrong
  evidence — `venue_capabilities.py` isn't being bypassed by the other 8 families, it was never built for them.
- **na-eligibility-audit 2026-08-17** (infra tranche) [body-hash:4e09dc58212eb9a8]: KEEP-NA, valid — todo 1 is explicitly [OPERATOR] P1-tagged (generalize vs accept hardcoded catalog literals, a genuine unresolved design decision); todos 2-3 are textually gated on todo 1's outcome.
- **na-eligibility-audit 2026-08-17** (infra tranche) [body-hash:4e09dc58212eb9a8]: KEEP-NA, valid — todo 1 is explicitly [OPERATOR] P1-tagged (generalize vs accept hardcoded catalog literals, a genuine unresolved design decision); todos 2-3 are textually gated on todo 1's outcome.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-20**: refreshed context_scope (5 entries)
- **2026-08-21** (T3 tranche): ran the todo-2 P2 audit ahead of todo 1's operator decision, per that todo's own
  "useful regardless" note. See new "Venue-literal capability audit" section above. Two real drift findings
  (CME event-contract root symbols unconfirmed; Phoenix listed as live spot venue but is now legacy/private-beta
  perps-only). Todo 2 left `[ ]` — it is textually gated on todo 1's outcome (whether to build the centralized
  lookup at all), not fully closed by this audit alone; the findings stand ready to seed that lookup's baseline
  once todo 1 resolves.
