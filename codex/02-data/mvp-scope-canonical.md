---
scope: [engineer, admin]
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

| Axis                  | MVP                                                                                                                                                                                                                                                                                                                        |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Venues                | BINANCE-SPOT/-FUTURES · BYBIT(/-SPOT) · OKX-SPOT/-SWAP/-FUTURES · DERIBIT · HYPERLIQUID · ASTER · KRAKEN-SPOT/-FUTURES · COINBASE-SPOT/-FUTURES · BITFINEX-SPOT/-FUTURES · BITGET-SPOT/-FUTURES · UPBIT · **LIGHTER-ZKSYNC · EXTENDED-STARKNET · PACIFICA-SOLANA**                                                         |
| Instrument types      | SPOT_PAIR · PERPETUAL · FUTURE (dated/quarterly) · OPTION · EQUITY_PERP · TOKENIZED_EQUITY                                                                                                                                                                                                                                 |
| Base universe         | `CEFI_BASE_ASSET_UNIVERSE` ∪ `CEFI_EQUITY_PERP_BASE_UNIVERSE` (~490 + equity tickers, survivorship-bias-free)                                                                                                                                                                                                              |
| Options base universe | BTC + ETH only (`CEFI_OPTIONS_UNDERLYINGS`) — Deribit is the only CeFi OPTION venue                                                                                                                                                                                                                                        |
| **data_type cut**     | **trades + book_snapshot_5 + funding** (derivative_ticker/funding_rate) for spot/perp/dated-future/equity-perp; **OPTION = `options_chain` ONLY** (carries marks + IVs; per-strike trades + book_snapshot_5 EXCLUDED — too heavy)                                                                                          |
| Perp-gate             | a SPOT / dated-FUTURE is in the CAPTURE universe ONLY IF the venue lists a perp for the base (`is_in_mvp_capture_universe`, `has_perp_for_base`); PERP/EQUITY_PERP self-qualify; OPTION rides the Deribit BTC/ETH carve-out (not perp-gated); UPBIT spot + `STAKING_SPOT_EXCEPTION` bases are spot-without-perp carve-outs |
| **NOT MVP**           | **BINANCE-DELIVERY** (COIN-M inverse/delivery — dropped, decision #3); options trades + book5; spot-without-perp (non-exception)                                                                                                                                                                                           |
| Genesis               | per `VenueMapping.venue_start_dates` — capture clipped to venue launch                                                                                                                                                                                                                                                     |
| Deferred-no-source    | HL **trades** pre-2025-03-22 (HL S3 has no trades before then); ASTER **book_snapshot_5** + liquidations are LIVE-ONLY (Binance-compat REST has no historical depth) — honest-absent in batch, never an empty cell                                                                                                         |

### DeFi

MVP-tag-all today (`defi_mvp_tag_all_2026_06_26`): the IS catalogue tags ALL DeFi rows mvp=true (the UAC DeFi
`MVP_SCOPE` rule is the narrower Uniswap-V3/Curve/Orca/… venue + POOL/DEX_POOL/LST/LENDING set used by `is_mvp`, but the
production catalogue is wider, so `_add_mvp_column` short-circuits DeFi to all-MVP until a real per-instrument DeFi
screen lands). data_types: dex_pool_state/dex_pool_swaps/lst_rates/lending_indices/perp_funding/oracle_prices.

### TradFi

| Axis              | MVP                                                                                                                   |
| ----------------- | --------------------------------------------------------------------------------------------------------------------- |
| Venue             | CME (futures complex). Equity-basis carve-out: NASDAQ/NYSE/ARCA/KRX EQUITY/ETF in `TRADFI_EQUITY_PERP_BASIS_UNIVERSE` |
| Instrument types  | FUTURE · **OPTION** (CME options — MVP once ingested; catalogue has 0 CME OPTION rows today)                          |
| **data_type cut** | **ohlcv_1m ONLY** (decision #7 — NO ohlcv_1s, NO trades/tbbo)                                                         |
| Underliers        | ES · NQ · VX + the CME commodity roots backing a Binance tradfi-perp (GC/SI/PL/PA/NG/CL/HG)                           |

> **CME options ingestion is a SEPARATE agent's job** — this rule only ensures CME options tag MVP at ohlcv_1m once the
> option instrument-definitions are ingested into instruments-service.

### Sports

| Axis       | MVP                                                                                                                                                                                                                                                                                                 |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Leagues    | the **94-league FOOTBALL universe** — EVERY `LEAGUE_REGISTRY` league with `sport == "FOOTBALL"` (33 Prediction + 22 Features + 39 Reference). The 7 non-football leagues (NFL/NBA/MLB/NHL/ATP/WTA/EUROLEAGUE) are EXCLUDED. Derived, not a literal (the prior EPL+LA_LIGA 2-league drift is fixed). |
| data_types | odds / ODDS / odds_snapshot / markets / outcomes / settlements (MTDS odds market-data)                                                                                                                                                                                                              |
| Sources    | 6 reference sources (api_football / footystats / understat / transfermarkt / soccer_football_info / open_meteo) + odds_api                                                                                                                                                                          |

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

`MVP_SCOPE_CONFIG_VERSION = 10` / `MVP_SCOPE_CONFIG_HASH` flips IFF `MVP_SCOPE` content changes (a scope-change vs a
data-change, surfaced in data-status). The sports-leagues config (`SPORTS_LEAGUES_CONFIG_VERSION`) versions
`LEAGUE_REGISTRY` independently. Bump the version on any rule-content change — keep the predicate deterministic.
