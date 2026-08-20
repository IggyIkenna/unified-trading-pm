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
last_updated: "2026-08-20"
# was: defi_master (epic-assignment audit 2026-08-19) -- stamp_instrument_identity()/is_mvp() curtailment wiring spans ALL 5 target_universe/catalog_*.py builders (549 specs incl. CeFi Deribit/Bybit + TradFi IBKR rows, not just DeFi archetypes) -- a strategy-service catalog mechanism surfaced via a DeFi curtailment issue, not DeFi-specific itself
parent_epic: strategy_master
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
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
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
- [x] ✅ [BACKEND] P2. **DONE 2026-08-17 (Part 3a ONLY), `strategy-service@43352916` — wired the real
      `is_mvp()`-backed `not_mvp_scope` curtailment reason into `strategy_service/cli/handlers/
      paper_universe.py`'s `_resolve_drivable()`, alongside the existing `curtailed_by_operator_constraint`, for
      the 7 archetypes where every drivable row resolves to a single, unambiguous, verified DeFi venue string
      with no `base_ccy` axis needed: `CARRY_STAKED_BASIS`, `CARRY_STAKED_BASIS_DATED`, `CARRY_RECURSIVE_STAKED`,
      `YIELD_STAKING_SIMPLE`, `DEFI_LP_CONCENTRATED`, `DEFI_LP_POOL`, `DEFI_LP_VAULT`.** New
      `_mvp_scope_reason_for_spec()` runs as the FINAL gate in the `or` chain, after drivability — it only
      narrows specs that would otherwise already be driven, and only for archetypes it can resolve confidently
      (an archetype absent from the new `_DEFI_MVP_VENUE_KEYS` map, or a spec whose venue doesn't confidently
      resolve, is untouched). Zero behavior change for the current catalog: every covered row resolves
      in-MVP-scope today (verified by a new regression test, `test_mvp_scope_reason_confirms_the_real_covered_
      archetypes_stay_in_scope_today`), so this is correct wiring that only starts to matter if a covered
      venue's `DEFI_VENUE_PHASE` ever narrows. **Part (3b) — every other archetype this todo originally
      scoped — is split into 3 separate todos below, NOT done here.** The original scoping text below (this
      session's own investigation, cross-verified against the prior 2026-08-17 slot-22 session's findings) is
      preserved as the evidence trail for why the rest is split out rather than guessed:
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
      or it never resolves via the flat `venue in rule.venues` check at all — **RE-VERIFIED 2026-08-17 (this
      session, independent of slot-22): moot for THIS wiring today.** None of `EVENT_DRIVEN`/
      `ML_DIRECTIONAL_CONTINUOUS`/`RULES_DIRECTIONAL_CONTINUOUS`/`STAT_ARB_*` are in `E2E_UNIVERSE_ARCHETYPES`
      (the paper book's default `config.archetypes`) NOR in `_ENGINE_DRIVABLE_ARCHETYPES` — every spec of theirs
      is ALREADY honestly skipped with `engine_tick_builder_unwired` by the pre-existing drivability gate,
      which now runs BEFORE the new mvp-scope check in `_resolve_drivable`'s `or` chain, so these archetypes
      never reach an MVP-scope question at all (confirmed: `service_entry.py`/`paper_run_handler.py` always
      construct `PaperUniverseConfig()` with the default `archetypes`; only an explicit operator
      `--archetypes` CLI override could ever reach them, and even then the drivability gate intercepts first).
      This item only becomes live if/when those archetypes' tick builders get wired — a separate, currently
      out-of-scope initiative; (ii) several DeFi rows carry only a
      BARE lowercase protocol token (`"aave"`) or a bare chain name (`"ethereum"`) as their identity, neither of
      which is a valid `DeFiMvpRule.venues` member (canonical `PROTOCOL-CHAIN` strings like `AAVE_V3-ETHEREUM`) —
      needs a protocol+chain → canonical-venue resolver (a SEPARATE, narrower table from
      `classify_venue_asset_group`'s asset_group-only classification, which deliberately tolerates loose/bare
      tokens); (iii) a verified per-archetype `base_ccy` source key for every cefi/tradfi archetype (the DeFi
      case doesn't need one — `DeFiMvpRule` has no `base_ccys` field at all). Do NOT guess any of (i)-(iii) — a
      wrong canonical-venue or base_ccy resolution would silently mis-curtail genuinely in-scope rows, which the
      parent issue doc's own Finding 1 explicitly calls out as WORSE than leaving the gap open. Repos:
      strategy-service, unified-api-contracts (if a shared canonical-venue resolver belongs there instead).
- [x] ✅ [BACKEND] P2. **Part (3b-i) — CeFi `base_ccy` verification + wiring for `CARRY_BASIS_DATED` /
      `CARRY_BASIS_DATED_INV` — DONE 2026-08-17, `strategy-service@dc46670cf6`.** Verified before wiring (not
      guessed): `"DERIBIT"` is a literal `CeFiMvpRule.venues` member and `"BTC"`/`"ETH"` are literal
      `CEFI_BASE_ASSET_UNIVERSE` members (both `unified-api-contracts`, grep-confirmed, no code change needed
      there — the read-only verification this todo scoped). Added `_CEFI_BASIS_DATED_MVP_KEYS`/
      `_resolve_cefi_basis_dated_mvp_cell()` (parallel to `_DEFI_MVP_VENUE_KEYS`/`_resolve_defi_mvp_venue`) to
      `paper_universe.py`, wired into `_mvp_scope_reason_for_spec` as a second branch calling
      `is_mvp("cefi", venue, instrument_type, base_ccy=base_ccy)` — `is_mvp()` itself performs the real
      venue/base_ccy membership check, the resolver only confirms it's asking a CONFIDENT question (gated on
      `future_venue.upper() == "DERIBIT"`; every TradFi basis-dated row sharing the same config-key shape stays
      unresolved, `None`, never a guess). Note for the plan's own next reader: the actually-drivable count today
      is the 2 real binance/deribit crypto rows per archetype (4 total across both archetypes) per
      `_BASIS_DATED_SATISFIABLE_VENUE_PAIRS = frozenset({("binance", "deribit")})` — the bybit-spot rows this
      todo's own text cited exist in the catalog (4 rows/archetype, 8 total) but do NOT pass the pre-existing
      `_basis_dated_config_satisfiable` drivability gate (no captured bybit/deribit raw-tick data), so they never
      reach this MVP-scope check at all; this wiring is correct for whichever set is drivable at any given time,
      it doesn't hardcode a row count. 4 new unit tests
      (`tests/unit/cli/handlers/test_paper_universe.py`): resolver-level (resolves the verified Deribit rows,
      never guesses a TradFi venue), and `_mvp_scope_reason_for_spec`-level (every real drivable-satisfiable
      Deribit row of both archetypes stays in-scope today; a synthetic non-universe base_ccy is correctly
      curtailed with the typed `not_mvp_scope:asset_group=cefi,...` reason). `strategy-service`
      `quality-gates.sh --no-fix` GREEN (fresh run, exit 0, sentinel matches shipped SHA).
- [ ] [BACKEND] P2. **[OPERATOR] Part (3b-ii) — BYBIT-FUTURES naming-gap fix + multi-venue `is_mvp()`
      semantics decision, needed before `CARRY_BASIS_PERP` / `CARRY_FUNDING_DISPERSION` /
      `ARBITRAGE_PRICE_DISPERSION` can be wired.** Genuine judgment calls, not a lookup — needs an operator
      ruling before dispatch, same class as the original (i) TradFi/IBKR question. Two open sub-questions,
      found 2026-08-17 (this session, NOT in the prior slot-22 investigation):
      (1) **Bybit naming gap (NEW finding).** The catalog emits `"BYBIT-FUTURES"` as the perp venue
      (`_CARRY_BASIS_PERP_VENUE_BUNDLES` / `_FUNDING_DISPERSION_VENUES` in `catalog_carry.py`), but
      `CeFiMvpRule.venues` only declares bare `"BYBIT"` + `"BYBIT-SPOT"` (the rule's own docstring documents the
      `BYBIT-SPOT↔BYBIT` pairing as Bybit's one exception to the `-FUTURES`-suffix convention every other
      venue uses) — a direct `is_mvp("cefi", "BYBIT-FUTURES", ...)` call would incorrectly return False for a
      row meant to stay in scope, affecting 13 `CARRY_BASIS_PERP` rows + all `CARRY_FUNDING_DISPERSION` Bybit
      rows. Two candidate fixes, both real decisions: (a) extend `is_mvp()`'s `_CEFI_SUB_VENUE_BASES` fallback
      (today OKX-only) to cover Bybit too — widens a shared, heavily-consumed predicate; (b) normalize
      caller-side in `paper_universe.py` only. (2) **Multi-venue rows have no defined `is_mvp()` semantics.**
      `is_mvp()` is single-venue by signature; several drivable row-families are inherently multi-venue with no
      defined AND/OR/anchor rule: `CARRY_BASIS_PERP`'s multi-coin `venue`-rotation family + its comma-joined
      `venues="binance,okx"` family (plus: bare `venue="binance"`/`"okx"` is itself spot-vs-futures-ambiguous,
      unlike Hyperliquid's unsplit bare form); `ARBITRAGE_PRICE_DISPERSION`'s `cex_cex_arb` (2-token
      `candidate_venues`) and `dex_dispersion` (5-7 tokens, sometimes spanning chains a listed venue doesn't
      even operate on — e.g. a SOL/USDC row listing `UNISWAP_V3` first, which doesn't run on Solana at all, so
      "first token wins" isn't just under-specified, it can pick an economically wrong venue). Separately,
      `CARRY_BASIS_PERP` / `CARRY_FUNDING_DISPERSION` rows on `perp_venue`∈{`KALSHI-PERP`,`POLYMARKET-PERP`}
      ARE confidently resolvable today with NO guess needed (neither string is a member of `CeFiMvpRule.venues`
      — confirmed absent, so `is_mvp()` returns False decisively on the venue axis alone) — these could be
      wired as a narrow first slice of this todo without waiting on (1)/(2), once dispatched. Repos:
      strategy-service, unified-api-contracts (only if fix (a) is chosen for the Bybit gap).
- [x] ✅ [BACKEND] P2. **DONE 2026-08-17, `strategy-service@6d79dfe3df` — Part (3b-iii)
      `YIELD_ROTATION_LENDING` structural venue resolver.** The todo's own investigation instruction ("read which
      chain each `candidate_protocols` token is ACTUALLY captured on in real prod `lending_rates` GCS data —
      `CanonicalLendingSupplyApyProvider`'s own per-protocol coverage spot-check is a starting point") turned out
      to already have its answer VERIFIED and committed in that exact module:
      `PROTOCOL_ID_TO_LENDING_RATES_PROTOCOL` (`canonical_lending_supply_apy_provider.py`, built for the
      pre-existing drivability gate) maps catalog token -> real `lending_rates`-corpus protocol string —
      `{"aave": "AAVE_V3", "compound": "COMPOUND_V3", "spark": "SPARK"}`, empirically verified against 5 real
      prod-GCS days (module docstring), with `morpho`/`kamino` confirmed PERMANENT gaps (never appear in the
      corpus at all). Those values ARE ALREADY the exact `ALL_DEFI_VENUES` canonical PROTOCOL-CHAIN prefix — no
      naive `f"{protocol}-{chain}"` concat of the catalog's bare lowercase tokens needed (that's what would have
      broken); this reuses the drivability gate's own verified evidence rather than re-deriving anything.
      New `_resolve_yield_rotation_lending_mvp_venues()` (`paper_universe.py`): only resolves rows carrying a
      singular `chain` key (9 of 10 in-scope rows — the 8 stablecoin-rotation rows + ETH row + wBTC row all
      pair 2-3 candidate protocols against ONE explicit chain); for each candidate token present in
      `PROTOCOL_ID_TO_LENDING_RATES_PROTOCOL`, builds `f"{prefix}-{chain.upper()}"` and keeps it only if it's a
      literal `ALL_DEFI_VENUES` member (never trusted blind). The ONE remaining row (`chains_eligible`,
      multi-chain cross-chain meta-rotation, 4 protocols x 5 chains with no explicit pairing) is deliberately
      left UNRESOLVED — returns no venues, never a guess at which protocol runs on which chain. Wired into
      `_mvp_scope_reason_for_spec` as a new branch: since this archetype ROTATES capital across candidate
      protocols, a row stays in-scope iff AT LEAST ONE confidently-resolved candidate venue is MVP (mirrors
      `_yield_rotation_lending_config_satisfiable`'s own "any candidate resolves" semantics for drivability).
      5 new unit tests (`tests/unit/cli/handlers/test_paper_universe.py`): resolver-level (resolves the real
      aave/compound rows, drops morpho, never guesses the cross-chain/kamino rows), and
      `_mvp_scope_reason_for_spec`-level (every real drivable+resolvable row stays in-scope today; a synthetic
      `COMPOUND_V3-SCROLL` venue — real registry member, `DEFI_VENUE_PHASE="pipeline"` not `"live"` — is
      correctly curtailed with the typed `not_mvp_scope:asset_group=defi,venues=...` reason, confirming
      `is_mvp()`'s own venue-membership check is actually reached, not bypassed). Also fixed a now-stale comment
      block above `_DEFI_MVP_VENUE_KEYS` that still claimed this archetype was "structurally unresolvable" — it
      was correct when written (before this todo), so left as-is would have misled the next reader. `strategy-service`
      `quality-gates.sh --no-fix` GREEN (fresh, post-commit run: 6099 passed, sentinel matches shipped SHA).

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
- **2026-08-17 (slot-8, backend_engineer) — Part (3a) shipped, Part (3b) split into 3 new todos.** Resumed
  slot-22's session (its verification was thorough and cross-verified clean, not re-derived from scratch).
  Found a scope-narrowing fact slot-22's own investigation had not checked: `_resolve_drivable()` is the ONLY
  caller-path that needs an MVP-scope check, and it can run as the FINAL gate (after drivability) rather than a
  first-pass filter — this means it only ever needs to resolve venues for the 13 `_ENGINE_DRIVABLE_ARCHETYPES`
  (drivability's own `engine_tick_builder_unwired` check already excludes everything else, including the
  TradFi/IBKR archetypes item (i) worried about). Used a forked sub-agent (full context inherited) to extract
  the exact per-archetype config-key shapes for all 13 across `catalog_carry.py`/`catalog_staked_basis.py`/
  `catalog_yield_defi.py`/`catalog_trading.py`, then independently re-verified the specific rows I intended to
  implement against direct reads (not trusted secondhand) before writing any code. 7 of the 13 resolve
  confidently to a single unambiguous DeFi venue with no `base_ccy` axis needed — shipped
  (`strategy-service@43352916` + a QG-ratchet fix `strategy-service@b412c138`; see the flipped todo above for
  the exact archetype list + the new `_mvp_scope_reason_for_spec`/`_resolve_defi_mvp_venue` functions). The
  remaining 6 needed a genuine judgment call, a bounded-but-unverified sub-task, or a structural blocker — split
  into 3 new todos below (3b-i/ii/iii) rather than guessed, per this doc's own repeated warning that a wrong
  venue/currency resolution silently mis-curtails genuinely in-scope production rows. Also surfaced ONE new
  finding neither this session nor slot-22 had before: a confirmed `BYBIT-FUTURES` vs. bare `BYBIT` naming gap
  between the catalog and `CeFiMvpRule.venues` (todo 3b-ii) — a naive direct `is_mvp()` call on the catalog's
  literal venue string would have produced a false-positive curtailment for 13+ real Bybit rows had it been
  wired without noticing this.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
