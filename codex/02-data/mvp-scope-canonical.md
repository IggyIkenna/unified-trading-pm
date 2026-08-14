---
doc_type: codex-ssot
title: Canonical MVP Scope — the SSOT for "what MVP means" per asset_group × venue × data_type
summary: >-
  Canonical MVP-scope SSOT — the strict rules-derived subset of the could-exist universe per (asset_group, venue,
  instrument_type, data_type): CeFi perp-gate + options_chain-only + Coinbase trades-only, TradFi CME ohlcv_1m-only +
  OPTION narrowed to the ES/S&P-500 complex only, DeFi tag-all, Sports 96-league football, Prediction Polymarket+Kalshi
  arb-overlap; code SSOT MVP_SCOPE at config version 16.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-api, instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [mvp, cefi, defi, tradfi, sports, prediction, uac]
related:
  [
    /codex/02-data/cefi-capture-universe.md,
    /codex/02-data/mtds-data-source-coverage-matrix.md,
    /codex/02-data/per-asset-group-bucket-layouts.md,
  ]
created: 2026-06-27
authoritative_for: [canonical MVP scope definition per asset_group]
referenced_by:
  [
    /codex/04-architecture/instrument-universe-registry-consolidation.md,
    /codex/09-strategy/mvp-universe-per-asset-group.md,
  ]
owner:
last_reviewed: 2026-07-28
code_refs: [unified-api-contracts/unified_api_contracts/canonical/crosscutting/mvp_scope.py]
codified: 2026-06-27
---

# Canonical MVP Scope — the SSOT for "what MVP means" per asset_group × venue × data_type

> **Anchor**: the operator's canonical MVP definition (2026-06-27, 7 decisions reconciling a prior audit's drifts). This
> doc is the durable concise reference; the CODE SSOT is
> `unified-api-contracts/unified_api_contracts/canonical/crosscutting/mvp_scope.py` (`MVP_SCOPE`, `is_mvp`,
> `is_in_mvp_capture_universe`, config **v10**) + the sports structural-gap registry in
> `…/canonical/domain/sports/league_data.py` (`SPORTS_STRUCTURAL_GAPS` / `SPORTS_SOURCE_LEAGUE_ALLOWLIST` /
> `is_sports_structural_gap`). Related: [`cefi-capture-universe.md`](cefi-capture-universe.md) (the perp-gate layer).

MVP is a strict, rules-derived SUBSET of the could-exist universe, evaluated on-the-fly (no manifest column) by the IS
catalogue (`_add_mvp_column` → `is_mvp` / `is_in_mvp_capture_universe`), the MTDS capture filter, and deployment-api's
`scope=mvp` coverage denominator. Grain = `(asset_group, venue, instrument_type, data_type[, base_ccy])` (+ `league` for
sports, `market_group` for prediction). A blank `data_type` / `market_group` means "any MVP value" (instrument-grain
callers carry no such axis).

## The MVP definition per asset_group

### CeFi

| Axis                  | MVP                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Venues                | BINANCE-SPOT/-FUTURES · BYBIT(/-SPOT) · OKX-SPOT/-SWAP/-FUTURES · DERIBIT · HYPERLIQUID · ASTER · KRAKEN-SPOT/-FUTURES · COINBASE-SPOT/-FUTURES · BITFINEX-SPOT/-FUTURES · BITGET-SPOT/-FUTURES · UPBIT · **LIGHTER-ZKSYNC · EXTENDED-STARKNET**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Instrument types      | SPOT_PAIR · PERPETUAL · FUTURE (dated/quarterly) · OPTION. **Crypto-venue equity instruments carry NO distinct type (operator 2026-07-16): a single-stock perp is `PERPETUAL`, a tokenized stock is `SPOT_PAIR`; the equity identity rides the catalogue tags `is_equity_perp` + `tracks_equity`, not a type.**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| Base universe         | `CEFI_BASE_ASSET_UNIVERSE` ∪ `CEFI_EQUITY_PERP_BASE_UNIVERSE` ∪ `CEFI_TOKENIZED_EQUITY_BASE_UNIVERSE` (~490 + equity tickers + 67 OKX/Bybit tokenized-equity bases, survivorship-bias-free)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| Options base universe | BTC + ETH only (`CEFI_OPTIONS_UNDERLYINGS`) — Deribit is the only CeFi OPTION venue                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| **data_type cut**     | **trades + book_snapshot_5 + funding** (derivative_ticker/funding_rate) for spot/perp/dated-future; **PERPETUAL ALSO adds `liquidations` (v15, 2026-07-15)** — the PERPETUAL `instrument_type_data_types` override = the flat set + liquidations, for PERPETUAL cells ONLY (equity perps are `PERPETUAL` too, so a liq-feed-venue equity perp rides it; NOT spot/dated-future — dated-futures liq negligible), venue-gated by `VENUE_DATA_TYPE_CAPABILITIES` to the 6 real-feed venues BINANCE-FUTURES/OKX-SWAP/BYBIT/KRAKEN-FUTURES/BITFINEX-FUTURES/BITGET-FUTURES; **OPTION = `options_chain` ONLY** (carries marks + IVs; per-strike trades + book_snapshot_5 EXCLUDED — too heavy); **per-venue override (v11): COINBASE-SPOT/-FUTURES = `trades` ONLY** (book_snapshot_5 + liquidations dropped — VMs too heavy, no depth features derived; operator 2026-06-28; the venue override wins over the PERPETUAL override for its perp cells). DERIBIT perp/future keep trades+book5 (NO Deribit override in v11; DERIBIT liquidations NOT MVP — not a real feed) |
| Perp-gate             | a SPOT / dated-FUTURE is in the CAPTURE universe ONLY IF the venue lists a perp for the base (`is_in_mvp_capture_universe`, `has_perp_for_base`); PERP self-qualifies (incl. crypto-venue equity perps, typed PERPETUAL); OPTION rides the Deribit BTC/ETH carve-out (not perp-gated); UPBIT spot + `STAKING_SPOT_EXCEPTION` bases + `CEFI_TOKENIZED_EQUITY_BASE_UNIVERSE` bases (OKX `X<UNDERLYING>` tokens / Bybit `xstocks` — no perp leg exists) are spot-without-perp carve-outs (v26, 2026-08-13)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **NOT MVP**           | **BINANCE-DELIVERY** (COIN-M inverse/delivery — dropped, decision #3); options trades + book5; **COINBASE-SPOT/-FUTURES book_snapshot_5 (v11 — trades-only)**; spot-without-perp (non-exception)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Genesis               | per `VenueMapping.venue_start_dates` — capture clipped to venue launch                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Deferred-no-source    | HL **trades** pre-2025-03-22 (HL S3 has no trades before then); ASTER **book_snapshot_5** + **liquidations** are LIVE-ONLY (Binance-compat REST has no historical depth) — honest-absent in batch, never an empty cell. **v15 (2026-07-15): ASTER `liquidations` REMOVED from the batch `VENUE_DATA_TYPE_CAPABILITIES` gate** so the now-MVP PERPETUAL liquidations data_type does NOT seed ASTER into the BATCH honest-coverage denominator (live-only feeds must not seed batch; 0 captured batch rows). ASTER book_snapshot_5's live-vs-batch seeding is tracked separately (WS-I)                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |

### DeFi

MVP-tag-all today (`defi_mvp_tag_all_2026_06_26`): the IS catalogue tags ALL DeFi rows mvp=true (the UAC DeFi
`MVP_SCOPE` rule is the narrower Uniswap-V3/Curve/Orca/… venue + POOL/DEX_POOL/LST/A_TOKEN/DEBT_TOKEN set used by
`is_mvp`, but the production catalogue is wider, so `_add_mvp_column` short-circuits DeFi to all-MVP until a real
per-instrument DeFi screen lands). data_types:
dex_pool_state/dex_pool_swaps/lst_rates/lending_indices/perp_funding/oracle_prices. (Lending: the HOLDINGS screen keys
on `A_TOKEN`/`DEBT_TOKEN` — the operator-ruled SSOT; market/event lending data_types such as `lending_indices` key to
the interim `LENDING`/`SOLANA_LENDING` instrument_type. **⛔ corrected 2026-07-20, operator ruling D2 — ~~"PARKED per
`issues/canonical_closeout_open_questions_2026_07_18.md` § D — NOT 'LENDING retired'"~~.** The full retire (all lending
data_types) IS now the RULED TARGET, but is NOT yet implemented — it is `migration_pending`, gated on the MTDS
lending-writer fix (`../../plans/archive/2026_07/defi_lending_writer_retire_prerequisite_2026_07_20.md`); the interim
`LENDING`/`SOLANA_LENDING` keying holds until the migration lands.)

### TradFi

| Axis                                | MVP                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Venue                               | CME (futures complex). Equity-basis carve-out: NASDAQ/NYSE/ARCA/KRX EQUITY/ETF in `TRADFI_EQUITY_PERP_BASIS_UNIVERSE`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| Instrument types                    | FUTURE · OPTION (CME options — ingested 2026-07-14, 739,278 catalogue rows)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| **data_type cut**                   | **ohlcv_1m ONLY** (decision #7 — NO ohlcv_1s, NO trades/tbbo)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| Underliers (FUTURE)                 | ES · NQ · VX + the CME commodity roots backing a Binance tradfi-perp (GC/SI/PL/PA/NG/CL/HG)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| **Underliers (OPTION only)**        | **ES ONLY** (`TradFiMvpRule.option_underliers` / `TRADFI_MVP_OPTION_UNDERLYING_ROOTS`, operator ruling 2026-07-14) — GC/CL/NG/SI/PL/PA/HG/NQ/VX options are explicitly OUT of MVP even though those roots stay MVP for FUTURE cells                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| **Extra cells (`extra_mvp_cells`)** | Non-underlier MVP cells tagged individually (venue/instrument_type/base_ccy triples, not part of the flat `underliers`/`option_underliers` sets above): CBOE daily Treasury yield-curve INDEX (US3M/US2Y/US5Y/US10Y/US30Y, `ohlcv_24h`, Yahoo-sourced) and FX KRW/USD spot (`FX:SPOT_PAIR:KRW-USD`, `ohlcv_24h`, Yahoo-sourced) — both operator-ruled MVP 2026-07-21 ("+409 expansion", `/plans/active/tradfi_consolidated_closeout_2026_07_18.md` § MVP universe). **DXY (ICE US Dollar Index, `ohlcv_24h`, Yahoo-sourced) is registered + fetched in production but NOT in `extra_mvp_cells`** as of 2026-08-09 — added to the in-scope backfill list by `/plans/active/issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md`, MVP-tag code change tracked as that doc's own todo, not yet shipped. CME Treasury **bond futures** (ZN/ZB/ZF/ZT) are registered + launcher-ready but deliberately NOT in `underliers` or `extra_mvp_cells` — operator ruling 2026-08-09 defers them to November, do not confuse with the yield-curve INDEX above. |

> **CME options are now ingested** (739,278 catalogue rows as of the 2026-07-14 tradfi lifecycle-catalogue-regen). Once
> ingested, the naive rule (every FUTURE underlier's OPTION also MVP) tagged ALL 739,278 rows `mvp=True` — the `is_mvp`
> grain has no per-instrument_type underlier narrowing before v14. **Operator ruling (2026-07-14,
> `tradfi_eu_not_draining_source_axis_drift_2026_06_24.md`, verbatim): "We DO want tradfi options for S&P 500 — options
> and futures — but NO other options in tradfi MVP; just the single stocks, ETFs and futures already in MVP."**
> Implemented as a new `option_underliers` field on `TradFiMvpRule` (mirrors the pre-existing CeFi `options_base_ccys`
> Deribit-options narrowing pattern) — OPTION cells resolve their underlying FUTURE contract's root
> (`build_instrument_catalogue.py::_tradfi_contract_code_to_root`) and gate on `option_underliers` instead of the flat
> `underliers` set. Post-narrowing: OPTION `mvp=True` rows dropped from 739,278 → 414,140 (raw catalogue leaves; all
> resolve to an `ES*` underlying contract code). The historical (2018–2026) `expected_unattempted` catch-up this
> narrowing unblocked: full-history scan-only 1,711,386 → 498,840 candidates (well under the 1,000,000 enumerator safety
> cap), applied via `enumerate_expected_universe.py --enumerator-version v2 --apply-write` (498,840 rows: 290,688
> `expected_unattempted` + 208,152 typed `empty_confirmed`; 95,785 of those are the `options_chain` bundle grain). SSOT:
> `unified-api-contracts@1753a084`.

### Sports

| Axis       | MVP                                                                                                                                                                                                                                                                                                 |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Leagues    | the **96-league FOOTBALL universe** — EVERY `LEAGUE_REGISTRY` league with `sport == "FOOTBALL"` (33 Prediction + 24 Features + 39 Reference). The 7 non-football leagues (NFL/NBA/MLB/NHL/ATP/WTA/EUROLEAGUE) are EXCLUDED. Derived, not a literal (the prior EPL+LA_LIGA 2-league drift is fixed). |
| data_types | odds / ODDS / odds_snapshot / markets / outcomes / settlements (MTDS odds market-data)                                                                                                                                                                                                              |
| Sources    | 6 reference sources (api_football / footystats / understat / transfermarkt / soccer_football_info / open_meteo) + odds_api                                                                                                                                                                          |

**Sources row caveat (ruled 2026-08-10)**: the "6 reference sources + odds_api" list above is the MVP _business_ scope,
not each source's actual capture scope — `open_meteo`/`soccer_football_info`/`odds_api` are deliberately capped at the
33-league PREDICTION tier only (`get_expected_leagues_for_source(source, ["Prediction"])`), narrower than the 96-league
football universe that `api_football`/`footystats`/`transfermarkt` cover. This is INTENDED behaviour, not a gap —
weather/SFI/odds data outside Prediction-tier leagues is genuinely out of scope (not wanted), so it must not be
attempted, must not inflate the honest-coverage numerator/denominator via `empty_confirmed`, and should carry a distinct
out-of-scope tag instead. See `sports-data-source-coverage-matrix.md` §1/§2 for the per-source league counts.

**Structural honest-absence (decision #6)** — `(league × source)` combos a source structurally NEVER carries are
expected-absent AND skipped by the IS producers (no attempt → no `attempted_failed`). SSOT:
`is_sports_structural_gap(source, league)`:

- **A_LEAGUE × footystats** — footystats does not carry the A-League.
- **GREEK_SUPER_LEAGUE × transfermarkt** — transfermarkt has no market-values for the Greek Super League (the league's
  `data_sources` was reconciled to drop transfermarkt so both SSOTs agree).
- **understat = big-5 ONLY** (EPL / LA_LIGA / BUNDESLIGA / SERIE_A / LIGUE_1) — the other 89 football leagues ×
  understat are structural gaps (allow-list complement). understat's per-league `data_sources` already encodes exactly
  the big-5, so `get_expected_leagues_for_source("understat")` (which drives the IS understat orchestrator's expected
  denominator + skip) already skips the 89.

**Per-fixture ENRICHMENT entity scope (`SPORTS_ENTITY_LEAGUE_COVERAGE`)** — the 96-league MVP set above bounds
FIXTURES-level per-entity enrichment fan-out for SOME api_football entities, not all. SSOT:
`unified_api_contracts.canonical.domain.sports.provider_league_ids.SPORTS_ENTITY_LEAGUE_COVERAGE` (consulted via
`get_entity_league_coverage(entity)`, `None` = all 383 curated-universe leagues, a `frozenset` = restricted to it):

| Entity                             | Scope                    | Why                                                                                                                        |
| ---------------------------------- | ------------------------ | -------------------------------------------------------------------------------------------------------------------------- |
| `FIXTURES`, `TEAMS`, `STANDINGS`   | all 383 leagues (`None`) | core reference data, expected on every fixture date regardless of prediction scope                                         |
| `INJURIES`                         | all 383 leagues (`None`) | need to know if players are injured across the full universe, not just MVP (2026-07-13 fix)                                |
| `FIXTURE_STATS`, `FIXTURE_LINEUPS` | all 383 leagues (`None`) | game results + lineups needed across the full curated universe — operator ruling 2026-07-28, moved off the MVP-only bucket |
| `FIXTURE_EVENTS`, `PLAYER_STATS`   | 96-league MVP frozenset  | per-event/per-player granularity — pure API-Football quota cost with no consumer outside MVP/prediction scope              |

The gap-emission denominator (`emit_empty_gaps_for_entity` in `instruments-service/.../sports_reference_core.py`) is
entity-scope-aware to match: an MVP-restricted entity's "expected" set is intersected with its coverage frozenset, so a
non-MVP league is excluded from the denominator entirely (not flagged as any kind of gap) rather than showing as a
permanent, un-resolvable coverage hole.

### Prediction

| Axis          | MVP                                                                                                                                                                                                                                      |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Venues        | **POLYMARKET + KALSHI** (decision #5 — Kalshi flipped in; the prior post-MVP TODO is resolved)                                                                                                                                           |
| MVP universe  | the **Kalshi ↔ Polymarket arbitrage overlap** (`arbitrage_price_dispersion`) — REQUIRES BOTH venues; the tradeable set is the per-instrument same-settlement cross-venue join built by `cross_venue_mapping.build_cross_venue_mapping`   |
| market_groups | crypto · politics · sports (the arb-overlap categories; `financial` excluded). UNBOUND axis: a blank market_group = any MVP market_group (instrument-grain catalogue rows carry no market_group, so POLYMARKET/KALSHI rows tag mvp=true) |
| data_types    | trades · prediction_canonical_question_group · market_lifecycle/MARKET_LIFECYCLE                                                                                                                                                         |

## Two-layer split (IS vs MTDS)

- **IS catalogue** = full could-exist enumeration; the `mvp` flag is an on-the-fly TAG (`_add_mvp_column`), never a
  capture gate. For CeFi the tag uses the perp-gated `is_in_mvp_capture_universe`; other AGs use `is_mvp`.
- **MTDS capture filter** = what tick data is actually downloaded — the MVP universe + perp-gate + the CeFi options
  data_type cut (options_chain only). data_type cuts (cefi options = options_chain; tradfi = ohlcv_1m) live at the MTDS
  layer; the IS instrument-grain `mvp` flag is data_type-agnostic (an in-scope instrument is mvp=true even if only some
  of its data_types are MVP).

## Config versioning

`MVP_SCOPE_CONFIG_VERSION = 16` (v16 = CeFi `COMBO` instrument_type added to `CeFiMvpRule.instrument_types` — tags
DERIBIT-COMBO rows as `COMBO`, distinct from OPTION, so the 68,847-row DERIBIT-COMBO catalogue is MVP-in without minting
a phantom `options_chain` cell, 2026-07-16; v15 = `liquidations` restored as a PERPETUAL-leg CeFi MVP data_type (a FULL
replacement for PERPETUAL cells, venue-gated to the 6 real-feed futures venues
BINANCE-FUTURES/OKX-SWAP/BYBIT/KRAKEN-FUTURES/BITFINEX-FUTURES/BITGET-FUTURES), 2026-07-15; v14 = tradfi OPTION
underlier narrowing to `option_underliers={"ES"}`, 2026-07-14; v13 = DeFi "everything we capture" broadening; v12 = DeFi
ROCKETPOOL-ETHEREUM exclusion; v11 = COINBASE-SPOT/-FUTURES trades-only, drop book_snapshot_5, Coinbase-only, NO Deribit
override) / `MVP_SCOPE_CONFIG_HASH` flips IFF `MVP_SCOPE` content changes (a scope-change vs a data-change, surfaced in
data-status). The sports-leagues config (`SPORTS_LEAGUES_CONFIG_VERSION`) versions `LEAGUE_REGISTRY` independently. Bump
the version on any rule-content change — keep the predicate deterministic. Full per-version changelog:
`unified-api-contracts/unified_api_contracts/canonical/crosscutting/mvp_scope.py` docstring on
`MVP_SCOPE_CONFIG_VERSION`.
