---
title: "Source-mode capability matrix (M2 ratification input) — {batch/live/replay × transport} per data_source"
created: 2026-06-07
author: ikenna (slot-2, research)
source:
  - pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md (M1/M2 — this is the M2-ratify input)
  - master_data_canonicalisation_migration_catalogue_2026_06_07.md (G0 root: this matrix unblocks the M1 enum)
  - vendor docs (web-verified 2026-06-07): Pyth/Hyperliquid/Tardis; code (`pipeline_mode.py`, `source_priority.py`)
---

# Source-mode capability matrix — the M2 ratification input (built, not punted)

> **Purpose**: the FIRST thing on the master coordinator's critical path is the G0 `{mode}_{source}[_{transport}]` enum
> (M1), which is blocked on the M2 per-source capability matrix being RATIFIED. This is that matrix — researched from
> vendor docs + code, not guessed. **batch = always YES** (the floor; every source can be pulled into a batch). The
> question per source is live + replay + transport. **REPLAY** = on-demand retrieval of _today-since-start_ to fill an
> intraday/startup/live-downtime gap (format-agnostic). Only the items in "§ Residuals for operator" need your call;
> everything else is determined with cited evidence.

## The matrix (28 canonical sources)

Legend: **B**=batch · **L**=live · **R**=replay (intraday today-since-start) · transport ∈ {rest, ws, sse, rpc, graphql,
flat_file, internal}. Confidence: **C**=confirmed (vendor doc / code) · **H**=high (source-type deterministic) ·
**M**=medium (reasoned, low-stakes) · **○**=operator residual.

| Source                       | AG(s)              | B   | L            | R               | Transport             | Conf | Evidence / note                                                                                                                                                                                                                                                                                                 |
| ---------------------------- | ------------------ | --- | ------------ | --------------- | --------------------- | ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **databento**                | tradfi             | ✓   | ✓            | ✓               | ws · rest             | C    | Live-API 24h intraday replay; Historical API 24h-embargoed → today-fill rides the LIVE path (plan UAC@8079b884).                                                                                                                                                                                                |
| **massive** (Polygon.io)     | tradfi             | ✓   | ✓ (delayed○) | ✓               | rest · ws             | C    | REST tick-in-time-range = intraday replay. **Starter tier = 15-min delayed**; true real-time = paid upgrade ○.                                                                                                                                                                                                  |
| **tardis** (Tardis.dev)      | cefi               | ✓   | ✓            | ✓ (T-6min)      | ws · rest · flat_file | C ○  | **CORRECTS the M2 seed** ("live-not-replay" is WRONG): HTTP API gives same-day replay at **T-6min**; CSV next-day only; tardis-node switches live↔replay. Consolidated multi-venue → it is BOTH the CeFi live AND replay source (no per-venue sources needed). Last ~6min needs direct-exchange ws if required. |
| **hyperliquid_rest**         | defi (perp/solana) | ✓   | ✓            | ✓               | rest · ws             | C    | ws `wss://api.hyperliquid.xyz/ws` (candle/trades/funding) + REST `candleSnapshot(start,end)` + `fundingHistory`.                                                                                                                                                                                                |
| **pyth_hermes**              | defi (oracle SOL)  | ✓   | ✓            | ✓               | sse · rest            | C    | Hermes SSE `/v2/updates/price/stream` (live) + Benchmarks `/v1/updates/price/{ts}` historical (replay).                                                                                                                                                                                                         |
| **chainlink**                | defi (oracle EVM)  | ✓   | ✓            | ✓               | rpc(rest)             | H    | EVM aggregator: latestRoundData (live) + historical rounds queryable on-chain (deterministic replay).                                                                                                                                                                                                           |
| **solana_rpc**               | defi               | ✓   | ✓            | ✓               | rpc(rest) · ws        | H    | Any past slot queryable (deterministic replay); ws account/slot subscriptions (live).                                                                                                                                                                                                                           |
| **helius_rpc**               | defi               | ✓   | ✓            | ✓               | rpc(rest) · ws        | H    | Enhanced Solana RPC: same deterministic replay; webhooks/ws (live).                                                                                                                                                                                                                                             |
| **onchain_rpc**              | defi               | ✓   | ✓            | ✓               | rpc(rest) · ws        | H    | Direct EVM node: any past block (replay); eth_subscribe (live).                                                                                                                                                                                                                                                 |
| **onchain_subgraph** (Graph) | defi               | ✓   | ~ (poll)     | ✓               | graphql(rest)         | H    | Block-historical GraphQL (replay); no native push → live = short-interval poll.                                                                                                                                                                                                                                 |
| **polymarket_clob**          | prediction         | ✓   | ✓            | ✓               | rest · ws             | H    | CLOB ws market channel (live) + data-api trade history (replay).                                                                                                                                                                                                                                                |
| **polymarket_gamma_api**     | prediction         | ✓   | ~ (poll)     | n/a             | rest                  | H    | Market metadata (created/resolution/settlement) — reference, re-fetchable; not a tick series.                                                                                                                                                                                                                   |
| **barchart**                 | tradfi (VIX)       | ✓   | ~            | ✗               | rest                  | M    | Used only for VIX 15m historical PRELOAD (2020-2025); not on the live/replay path.                                                                                                                                                                                                                              |
| **yahoo**                    | tradfi (VIX)       | ✓   | ~ (15min)    | ✗               | rest                  | M    | VIX 15m rolling 60d; delayed quotes; limited intraday history → no reliable replay.                                                                                                                                                                                                                             |
| **eia**                      | tradfi (commodity) | ✓   | ✗            | ✓ (by date)     | rest                  | H    | Weekly storage series; no live; series re-fetchable by date.                                                                                                                                                                                                                                                    |
| **open_meteo**               | sports (weather)   | ✓   | ~ (current)  | ✓               | rest                  | H    | Forecast + historical-weather API by date.                                                                                                                                                                                                                                                                      |
| **api_football**             | sports             | ✓   | ✓ (in-play○) | ✓ (by date)     | rest                  | M    | Has live/in-play fixtures endpoint; fixtures fetchable by date. In-play live only if sports trades it ○.                                                                                                                                                                                                        |
| **odds_api** (The Odds API)  | sports             | ✓   | ✓ (in-play○) | ~ (paid○)       | rest                  | M    | Live in-play odds endpoint; **historical odds = paid tier** (replay gated on the plan) ○.                                                                                                                                                                                                                       |
| **footystats**               | sports             | ✓   | ✗            | ✓ (date/season) | rest                  | M    | Post-match stat aggregator.                                                                                                                                                                                                                                                                                     |
| **understat**                | sports             | ✓   | ✗            | ✓               | rest                  | M    | xG aggregator, post-match.                                                                                                                                                                                                                                                                                      |
| **transfermarkt**            | sports             | ✓   | ✗            | ✓               | rest                  | M    | Transfer/value reference.                                                                                                                                                                                                                                                                                       |
| **soccer_football_info**     | sports             | ✓   | ✗            | ✓               | rest                  | M    | Progressive-stats aggregator.                                                                                                                                                                                                                                                                                   |
| **mdps_odds_horizon_bucket** | sports             | ✓   | ✓            | ✓               | internal              | —    | MDPS-derived bucket — follows the MDPS service mode (not an external vendor).                                                                                                                                                                                                                                   |
| **instruments_service**      | all                | ✓   | ✓            | ✓               | internal              | —    | Service output (reference/fixtures) — batch=live symmetry; re-run = replay; `source`-exempt (computed).                                                                                                                                                                                                         |
| **execution_service**        | cefi/defi          | ✓   | ✓            | ✓               | internal              | —    | Service output (`execution_fills`) — follows service mode; `source`-exempt.                                                                                                                                                                                                                                     |
| **strategy_service**         | all                | ✓   | ✓            | ✓               | internal              | —    | Service output (`hedge_ratio_snapshot` / `decision_context`) — `source`-exempt.                                                                                                                                                                                                                                 |
| **features_onchain_service** | defi               | ✓   | ✓            | ✓               | internal              | —    | Service output (`feature_observation_snapshot`) — `source`-exempt.                                                                                                                                                                                                                                              |
| **cross_instrument**         | all (features)     | ✓   | ✓            | ✓               | internal              | —    | features cross_instrument family output — `source`-exempt.                                                                                                                                                                                                                                                      |

## What this means for the MVP live legs (the load-bearing rows)

- **DeFi live (the May-23 archetypes)** — ALL replay-capable + live-capable: chain RPCs
  (solana/helius/onchain/subgraph), chainlink, pyth_hermes, hyperliquid_rest. On-chain is deterministic → a
  startup/downtime gap is always backfillable. **No source gap for DeFi live/replay.**
- **TradFi live** — databento + massive both batch+live+replay (confirmed); only the massive real-time _tier_ is a cost
  knob.
- **CeFi live** — tardis covers batch+live+replay (T-6min), consolidated across venues → **the earlier "need per-venue
  live sources" worry is dissolved**; the only edge is the last ~6 min (direct-exchange ws if a strategy needs sub-6-min
  freshness).
- **Computed/service sources** — batch=live symmetry; replay = re-run; `source`-exempt for provenance.

## § Residuals for operator (the only items I could NOT settle myself)

- [ ] **R1 — Tardis replay correction (ratify)**: the M2 seed encodes Tardis as "live, NOT replay." Vendor docs
      (docs.tardis.dev) show Tardis **IS** intraday-replay-capable via the HTTP API at **T-6min** (CSV is next-day; the
      replay API is not). Confirm I update `SOURCE_MODE_CAPABILITY[tardis] = {batch, live, replay}` (was
      `{batch,     live}`) — this materially improves CeFi continuity (replay-fill from Tardis vs "replay from the
      exchange"). Caveat to accept: the last ~6 min of a gap needs direct-exchange ws.
- [ ] **R2 — paid-tier cost calls** (you flagged massive-vs-databento on cost): (a) **massive/Polygon real-time** — do
      we pay for the real-time tier, or accept Starter 15-min-delayed live (fine for batch + replay, not for sub-15-min
      live)? (b) **The Odds API historical** — pay for the historical-odds tier (enables sports `replay`), or batch +
      in-play-live only?
- [ ] **R3 — sports in-play live scope**: do we run `live_<source>` for api_football / odds_api in-play (only needed if
      a sports strategy trades in-play), or keep sports `{batch, replay}` only for now? Recommend `{batch, replay}`
      until a sports live archetype exists.

> Everything not marked ○ above is determined with cited evidence and ready for the M1 enum (the `LIVE_<source>` /
> `REPLAY_<source>` members + `SOURCE_MODE_CAPABILITY` round-trip). Owner of the M1/M2 code is `vm-cross-cutting` per
> the standardisation plan; this doc is the ratified-content input.

## RATIFIED (operator 2026-06-07) — residuals closed + corrections

- **R1 — Tardis replay = NO (licence, not technical).** We hold a Tardis **academic licence which does NOT permit
  replay** (verified); the upgrade is too expensive. So **`SOURCE_MODE_CAPABILITY[tardis] = {batch, live}`** (the
  original M2 seed was right, for a licence reason — my web finding was the _technical_ capability, which our tier
  blocks). **Consequence: CeFi replay does NOT come from Tardis — it comes from the EXCHANGES' own REST** (see next
  blocker).
- **R2 — massive/Polygon real-time = YES (pay).** `SOURCE_MODE_CAPABILITY[massive] = {batch, live, replay}`; code it all
  now, **final testing gated on the paid-tier account upgrade** (a deploy-time gate, not a code blocker).
- **R2 — The Odds API historical = ALREADY HAVE IT.** Secret-Manager API keys + already-downloaded historical odds →
  `SOURCE_MODE_CAPABILITY[odds_api] = {batch, replay}` (replay-capable now).
- **R3 — sports = `{batch, replay}`** (no in-play `live_<source>`) until a sports live archetype exists.

## NEXT BLOCKER (introduced by R1) — CeFi per-venue exchange replay model

Because Tardis can't replay (licence), CeFi `replay` must come from **per-venue exchange REST**, and that capability is
**heterogeneous per (venue, data_type)** — web-verified 2026-06-07:

| Venue           | REST intraday replay (fill today-since-start)                                 | Deep history         |
| --------------- | ----------------------------------------------------------------------------- | -------------------- |
| **Binance**     | ✓ futures aggTrades last 24h, **≤1h windows** (enough for a same-day gap)     | flat-file dumps      |
| **OKX**         | ✓ `history-trades` tick from 2019-07-11 (deep via REST)                       | REST                 |
| **Deribit**     | ✓ `get_last_trades_by_currency` all-history via REST                          | REST                 |
| **Kraken**      | ✓ `Trades` REST `since` cursor                                                | REST                 |
| **Bybit**       | ⚠️ public REST is **recent-only** (no time-range tick) → intraday replay weak | flat-file (next-day) |
| **Hyperliquid** | ✓ `candleSnapshot(start,end)` (already confirmed)                             | REST                 |
| **Aster**       | ❓ newer venue — REST replay depth UNVERIFIED                                 | ❓                   |

**The blocker = a design/operator decision for the REST-replay-weak venues (Bybit + Aster):** to guarantee a gap-free
series at the live-flip (the M6 continuity contract), how do we replay-fill a venue whose REST can't? Closed-set: (a)
**buffer the live ws to disk** so a restart replays from the local buffer; (b) accept **next-day flat-file** (NOT
intraday — breaks same-day continuity); (c) **exclude that venue from the live MVP**. This also forces the **source
model**: CeFi `live`/`replay` are **per-venue** (`live_binance`/`replay_okx`/…), NOT a single generic — so the M2
registry is keyed `(venue, data_type) → modes`, and the SAME shard carries `source=tardis` in batch but `source=<venue>`
in live/replay (multi-source-per-shard, which the `source` COLUMN already models).

**Does NOT block the foundation code** — the M1 enum + M2 registry for every SETTLED source can land now; the per-venue
CeFi `replay_<venue>` rows ship as scaffold with Bybit/Aster flagged, pending this decision.
