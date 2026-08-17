---
doc_type: plan
title: Extend canonical instrument_type/asset_group identity to all ~26-29 DeFi strategy-archetype catalog rows
summary: >-
  Operator-ruled 2026-08-16 (na-eligibility-audit follow-up Q&A round 7) on
  defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md's open scope/sequencing question: extend to ALL
  ~26-29 archetypes now, not just the already-`_ENGINE_DRIVABLE_ARCHETYPES` subset (7-19 of them). Per-archetype
  catalog builders (CARRY/YIELD/ARBITRAGE/DIRECTIONAL) currently have NO stored `instrument_type`/`asset_group`
  identity in `initial_config` — it's implicit in engine `on_tick()` logic only. `asset_group` must be derived
  per-VENUE (some archetypes mix CeFi+DeFi venues in one archetype) via a UAC venue→asset_group classifier composed
  from `unified_api_contracts.registry.defi_venues.ALL_DEFI_VENUES` + CeFi/TradFi venue sets — no such single
  ready function exists yet. Do NOT guess values — a wrong guess silently mis-filters the live/paper production
  strategy universe.
status: active
nature: process
asset_group: [defi]
stage: [meta]
repos: [strategy-service, unified-api-contracts]
scope: [engineer]
tags: [defi, canonicalization, instrument_type, asset_group, strategy-catalog]
related:
  [
    /plans/active/issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 1.6
assigned_role: backend_engineer
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 7, 2026-08-16 — operator ruling: extend to all ~26-29 rows"
locked_by:
context_scope:
  [
    /plans/active/issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md,
    strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog.py,
    strategy-service/strategy_service/cli/handlers/paper_universe.py,
    unified-api-contracts/unified_api_contracts/registry/defi_venues.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/_mvp_scope_predicate.py,
  ]
locked_since:
resolved_by:
---

# Extend canonical instrument_type/asset_group identity to all DeFi archetype catalog rows

## Todos

- [x] ✅ [BACKEND] P2. **DONE 2026-08-17, `unified-api-contracts@bc91cdecee` + `strategy-service@5578afbbbf`
      — parts (1)+(2) of the original 3-part todo (part (3) split out below, NOT done here).** (1) Built
      `unified_api_contracts.registry.venue_asset_group.classify_venue_asset_group()`, composed from
      `market_data_categories.VENUES_BY_ASSET_GROUP` (cefi/tradfi/sports/prediction — the SAME registry
      `is_mvp()`'s per-asset-group rules key off) + `defi_venues.ALL_DEFI_VENUES` (defi, exact + legacy-alias +
      base-token match) + a small, individually-verified residual table for tokens neither registry resolves
      (bare `OKX`/`BINANCE` — both removed from `VENUES_BY_ASSET_GROUP["cefi"]` in favor of sub-venues but still
      used generically by several catalog rows; `IBKR`/`NYMEX` — real venues absent from the tradfi venue list;
      `DYDX` — a live on-chain perp DEX with no MTDS collector registered yet; `UNITY`/bare `BETFAIR`/`3ET`/
      `SHARPBET` — sports-context tokens the canonical sports venue list doesn't carry bare forms of; bare DeFi
      chain names `ETHEREUM`/`ARBITRUM`/etc.). 22 unit tests
      (`unified-api-contracts/tests/unit/test_venue_asset_group.py`), including 2 regression tests for real
      collisions found empirically (bare `binance` vs. the `BINANCE-ETHEREUM`/`BINANCE-BSC` wBETH-issuer LST
      venues sharing that base token; bare `okx` no longer being a `VENUES_BY_ASSET_GROUP["cefi"]` member at
      all). (2) Added `catalog_common.stamp_instrument_identity()` (merges a canonical `instrument_type` + a
      per-row DERIVED `asset_group` into every spec's `initial_config` post-construction, raising loudly if no
      identity key resolves) and applied it across every `CARRY_*`/`YIELD_*`/`LIQUIDATION_CAPTURE`/`DEFI_LP_*`/
      `ARBITRAGE_*`/`MARKET_MAKING_*`/`EVENT_DRIVEN`/`VOL_TRADING_OPTIONS`/`STAT_ARB_*`/`ML_DIRECTIONAL_*`/
      `RULES_DIRECTIONAL_*`/`TSMOM_BTC_CTA` builder (all 5 `target_universe/catalog_*.py` files) — 549 total
      specs, verified 0 missing `instrument_type`/`asset_group` after the change. Per-archetype
      instrument_type/asset_group_keys assignments are documented inline at each `stamp_instrument_identity(...)`
      call site (not restated here) — e.g. `CARRY_BASIS_PERP`'s cross-venue rows anchor `asset_group` on
      `perp_venue` first (matching `instrument_type=PERPETUAL`), not the DEX `spot_venue` some rows also carry, so
      a genuinely CeFi+DeFi-mixed row still resolves correctly. `MARKET_MAKING_CONTINUOUS`'s 3 pre-existing
      non-canonical lowercase `instrument_type` values (`spot`/`perp`/`options`) are replaced with canonical
      `SPOT_PAIR`/`PERPETUAL`/`OPTION`. The 3 pre-existing non-canonical `"asset_group": "CRYPTO"/"FUTURES"/"FX"/
      "EQUITY_ETF"` category tags on `RULES_DIRECTIONAL_CONTINUOUS`/`STAT_ARB_PAIRS_FIXED`/`TSMOM_BTC_CTA` (a
      DIFFERENT axis — an `AssetClass`-style category, verified zero engine/allocator consumer reads them from
      `initial_config`, the same write-only-documentation shape as Finding 2's dead `SmartOrderRoutingConfig` in
      the parent issue doc) are renamed to `instrument_class` (value unchanged) so the new canonical
      `is_mvp()`-scoped `asset_group` value doesn't silently collide with/overwrite them. Also updated the A4
      catalogue-key-coverage-gate ratchet baseline (`catalog_engine_coverage.py` — 46 new `(archetype, key)`
      entries; see that file's own new comment block) since `instrument_type`/`asset_group`/`instrument_class`
      are read by the catalog-selection layer (`paper_universe.py`), never by an archetype engine, which is
      exactly the shape that gate's docstring already documents an exemption for. Also fixed 2 pre-existing,
      unrelated red tests found while re-running `unified-api-contracts`'s `quality-gates.sh` (both verified
      pre-existing via `git stash` against a clean tree before touching them): a stale `COINBASE-FUTURES` entry
      in `tests/data/mtds_batch_live_coverage_baseline.json` (it now has real live MTDS coverage) and a missing
      `coinbase_intx_ws` → `coinbase` entry in `test_ws_cassette_coexistence.py`'s `_CONNECTOR_TO_VENUE` map.
      Both repos' full `quality-gates.sh` green (fresh runs, not cached). Cross-repo sequencing note for future
      reference: `strategy-service`'s `unified-api-contracts` dependency is an EDITABLE path dependency
      (`uv.lock`: `editable = "../unified-api-contracts"`), so `strategy-service` could NOT ship ahead of
      `unified-api-contracts` landing the new `venue_asset_group` module — a fresh LDR checkout of
      `strategy-service` without that module already on `unified-api-contracts`'s LDR would ImportError in CI;
      shipped `unified-api-contracts` first, verified it landed on origin, then shipped `strategy-service`.
- [ ] [BACKEND] P2. **Part (3) of the original todo, split out — wire the real `is_mvp()`-backed `not_mvp_scope`
      curtailment reason into `strategy_service/cli/handlers/paper_universe.py`'s `_resolve_drivable()`, alongside
      the existing `curtailed_by_operator_constraint`.** NOT done in the above build: verified (not assumed) that
      this needs MORE than the `instrument_type`/`asset_group` identity the above todo built — `is_mvp()` also
      requires (a) the EXACT canonical venue string `is_mvp()`'s per-asset-group rule actually checks membership
      against, not just a loosely-classified asset_group, and (b) a `base_ccy` argument that is CONFIRMED
      load-bearing, not optional-to-omit: both `CeFiMvpRule.base_ccys` and `TradFiMvpRule.underliers` are
      non-empty in the live rules (`unified_api_contracts/canonical/crosscutting/_mvp_scope_rules.py`), so
      passing `base_ccy=None` would make EVERY cefi/tradfi row fail axis 4/the underlier gate regardless of
      whether it's genuinely in MVP scope — a false-curtailment bug, not a safe default. Concretely open before
      this can be wired: (i) `TradFiMvpRule.venues == frozenset({"CME"})` ONLY — every `IBKR`-brokered row
      (`EVENT_DRIVEN`/`ML_DIRECTIONAL_CONTINUOUS`/`RULES_DIRECTIONAL_CONTINUOUS`/`STAT_ARB_*` tradfi rows) needs
      the NASDAQ/NYSE/ARCA/AMEX/BATS/KRX equity-basis carve-out branch in `is_mvp()`'s `TradFiMvpRule` handling
      or it never resolves via the flat `venue in rule.venues` check at all; (ii) several DeFi rows carry only a
      BARE lowercase protocol token (`"aave"`) or a bare chain name (`"ethereum"`) as their identity, neither of
      which is a valid `DeFiMvpRule.venues` member (canonical `PROTOCOL-CHAIN` strings like `AAVE_V3-ETHEREUM`) —
      needs a protocol+chain → canonical-venue resolver (a SEPARATE, narrower table from
      `classify_venue_asset_group`'s asset_group-only classification, which deliberately tolerates loose/bare
      tokens); (iii) a verified per-archetype `base_ccy` source key for every cefi/tradfi archetype (the DeFi
      case doesn't need one — `DeFiMvpRule` has no `base_ccys` field at all). Do NOT guess any of (i)-(iii) — a
      wrong canonical-venue or base_ccy resolution would silently mis-curtail genuinely in-scope rows, which the
      parent issue doc's own Finding 1 explicitly calls out as WORSE than leaving the gap open. Repos:
      strategy-service, unified-api-contracts (if a shared canonical-venue resolver belongs there instead).

## Progress Log

- **2026-08-17 (slot-22, backend_engineer) — concrete verification of the part-(3) todo's (i)-(iii) open items;
  NOT implemented, per the todo's own "do NOT guess" instruction.** Read `is_mvp()` in full
  (`unified_api_contracts/canonical/crosscutting/_mvp_scope_predicate.py`) plus the catalog builders
  (`catalog_carry.py`, `catalog_yield_defi.py`, `catalog_trading.py`) and `_mvp_defi_venues()`
  (`_mvp_scope_rules.py:316`, `= VENUES_BY_ASSET_GROUP["defi"]`, 103 canonical `PROTOCOL-CHAIN` strings). Findings,
  each independently measured, not assumed:
  - **(i) TradFi/IBKR — CONFIRMED real gap, and it's a design question, not a lookup gap.** The equity-basis
    carve-out branch (`is_mvp()` lines ~380-392) already EXISTS in the code and checks
    `_venue_root in ("NASDAQ","NYSE","ARCA","AMEX","BATS","KRX")` — the todo's framing ("needs the carve-out
    branch... or it never resolves") is slightly stale; the branch is there. The real gap: every IBKR-brokered
    catalog row's `venue` config value is the literal bare broker token `"ibkr"` (verified,
    `catalog_trading.py:611,833,860,941` etc.) — never the real LISTING EXCHANGE the carve-out actually checks
    against. IBKR is a broker, not an exchange; the catalog has no field carrying the real
    NASDAQ/NYSE/ARCA/AMEX/BATS-per-symbol exchange today. Two candidate fixes are BOTH real design decisions, not a
    lookup: (a) add `"IBKR"` itself to the carve-out's accepted venue-root set (broadens a shared, live
    `is_mvp()` semantic used by every other IBKR-routed asset_group check, not just this archetype set — needs a
    scope decision on whether that's correct for ALL IBKR-routed instruments or just these equity-basis rows), or
    (b) build a real per-symbol exchange lookup (new data dependency, not currently captured anywhere). Neither is
    safely guessable.
  - **(ii) DeFi bare-token → canonical-venue resolver — CONFIRMED, with a MEASURED edge case that breaks the
    obvious naive approach.** `staking_protocol`+`chain` config-key pairs (`catalog_carry.py`) DO compose cleanly
    for most rows via a simple `f"{protocol}-{chain.upper()}"` concat — verified against the real
    `VENUES_BY_ASSET_GROUP["defi"]` set: `LIDO`+`ethereum`→`LIDO-ETHEREUM` ✅, `JITO`+`solana`→`JITO-SOLANA` ✅,
    `ETHERFI`+`ethereum`→`ETHERFI-ETHEREUM` ✅ (all 3 are real registry members). **But** `catalog_carry.py`'s
    `lending_protocol: "KAMINO_SOLANA"` (a single already-chain-suffixed token) does NOT concat-resolve — the
    registry's real member is `KAMINO-SOLANA` (hyphen, not underscore, and the naive concat would try to build
    `KAMINO_SOLANA-<chain>` and fail). A uniform concat resolver would be WRONG for this row specifically —
    exactly the class of bug the todo warned about, now with a concrete repro rather than a hypothetical. Also
    confirmed a SEPARATE, harder shape: `catalog_yield_defi.py`'s `YIELD_ROTATION_LENDING` archetype's
    `candidate_protocols` field is a comma-joined multi-value string with NO chain pairing at all (e.g.
    `"aave,compound,morpho"`, `catalog_yield_defi.py:47`) — bare lowercase protocol names, zero chain context in
    that field, needing either a separate per-protocol default-chain table or a different resolution strategy
    entirely for this one archetype. A resolver good enough for the staking rows would silently mis-handle this
    shape if applied uniformly.
  - **(iii) Per-archetype `base_ccy` source key — NOT surveyed this session (ran out of budget after (i)/(ii));
    the existing `_CURRENCY_IDENTITY_KEYS` map (`paper_universe.py:670-694`) is a Layer-3-curtailment map for a
    DIFFERENT axis (`curtailed_by_operator_constraint`, operator allow/block-list) — it is a plausible STARTING
    point (same underlying config-key intuition: `coin`/`instrument`/`native_asset`/`asset`) but its correctness
    for `is_mvp()`'s specific `base_ccy` semantics (CeFi `base_ccys` set membership, TradFi `underliers`/
    `option_underliers` set membership) has NOT been independently verified per archetype — do not assume it
    transfers unchanged.
  - **Net assessment**: this is NOT safely completable as a single "wire it up" session even with the concrete
    evidence above — (i) needs an operator/design decision on carve-out scope, (ii) needs a per-archetype-family
    resolver (at least 3 distinct shapes confirmed: clean-concat / underscore-mismatch / comma-joined-no-chain),
    and (iii) is unverified. Recommending this stays split rather than force-implemented — a wrong resolver here
    would silently mis-curtail genuinely in-scope production rows, which this doc's own Finding 1
    (`defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md`) explicitly calls out as WORSE than leaving
    the gap open. Not flipping the checkbox. Recommend the next pass either (a) get an operator ruling on the (i)
    carve-out-scope question first (the smallest, most decision-shaped blocker), or (b) scope (ii)+(iii) as their
    own per-archetype-family verification pass before any code change.

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 7, operator ruling)**: extracted from
  `defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md`'s "NEW finding 2026-07-28" todo; operator chose
  the full-scope option (all ~26-29 rows) over starting with the smaller already-drivable subset.
**context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **2026-08-17 (slot-11 build)**: shipped parts (1)+(2) of the original todo
  (`unified-api-contracts@bc91cdecee`, `strategy-service@5578afbbbf`), verified both landed on
  `origin/live-defi-rollout`. Split part (3) into its own todo above after concrete verification found it needs
  meaningfully more work than "wire a function call" — a canonical-venue resolver + a per-archetype base_ccy map,
  neither of which existed before and both of which are correctness-load-bearing for `is_mvp()`. See that todo's
  own body for the exact open sub-items.
