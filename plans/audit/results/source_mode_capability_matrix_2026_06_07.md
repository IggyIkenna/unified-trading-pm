---
type: analysis
title: Source-mode capability matrix (M2 ratification input) — {batch/live/replay × transport} per data_source
epic: mtds_mdps_master
auditor: ikenna (slot-2, research)
date: "2026-06-07"
status: complete
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

| Source                       | AG(s)              | B   | L            | R               | Transport        | Conf | Evidence / note                                                                                                                                                                                                                                                                                                                                              |
| ---------------------------- | ------------------ | --- | ------------ | --------------- | ---------------- | ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **databento**                | tradfi             | ✓   | ✓            | ✓               | ws · rest        | C    | Live-API 24h intraday replay; Historical API 24h-embargoed → today-fill rides the LIVE path (plan UAC@8079b884).                                                                                                                                                                                                                                             |
| **massive** (Polygon.io)     | tradfi             | ✓   | ✓ (delayed○) | ✓               | rest · ws        | C    | REST tick-in-time-range = intraday replay. **Starter tier = 15-min delayed**; true real-time = paid upgrade ○.                                                                                                                                                                                                                                               |
| **tardis** (Tardis.dev)      | cefi               | ✓   | (n/a)        | ✗ (licence)     | flat_file · rest | C    | **RATIFIED `{batch}` (R1)**: our **academic licence blocks replay** (and we don't run CeFi live off Tardis). Tardis = the CeFi BATCH (T+1 archive) source. CeFi `live`/`replay` `source` = the exchange (binance/okx/…), per the corrected model below. (The vendor's _technical_ replay capability — HTTP API T-6min — is irrelevant: our tier forbids it.) |
| **hyperliquid_rest**         | defi (perp/solana) | ✓   | ✓            | ✓               | rest · ws        | C    | ws `wss://api.hyperliquid.xyz/ws` (candle/trades/funding) + REST `candleSnapshot(start,end)` + `fundingHistory`.                                                                                                                                                                                                                                             |
| **pyth_hermes**              | defi (oracle SOL)  | ✓   | ✓            | ✓               | sse · rest       | C    | Hermes SSE `/v2/updates/price/stream` (live) + Benchmarks `/v1/updates/price/{ts}` historical (replay).                                                                                                                                                                                                                                                      |
| **chainlink**                | defi (oracle EVM)  | ✓   | ✓            | ✓               | rpc(rest)        | H    | EVM aggregator: latestRoundData (live) + historical rounds queryable on-chain (deterministic replay).                                                                                                                                                                                                                                                        |
| **solana_rpc**               | defi               | ✓   | ✓            | ✓               | rpc(rest) · ws   | H    | Any past slot queryable (deterministic replay); ws account/slot subscriptions (live).                                                                                                                                                                                                                                                                        |
| **helius_rpc**               | defi               | ✓   | ✓            | ✓               | rpc(rest) · ws   | H    | Enhanced Solana RPC: same deterministic replay; webhooks/ws (live).                                                                                                                                                                                                                                                                                          |
| **onchain_rpc**              | defi               | ✓   | ✓            | ✓               | rpc(rest) · ws   | H    | Direct EVM node: any past block (replay); eth_subscribe (live).                                                                                                                                                                                                                                                                                              |
| **onchain_subgraph** (Graph) | defi               | ✓   | ~ (poll)     | ✓               | graphql(rest)    | H    | Block-historical GraphQL (replay); no native push → live = short-interval poll.                                                                                                                                                                                                                                                                              |
| **polymarket_clob**          | prediction         | ✓   | ✓            | ✓               | rest · ws        | H    | CLOB ws market channel (live) + data-api trade history (replay).                                                                                                                                                                                                                                                                                             |
| **polymarket_gamma_api**     | prediction         | ✓   | ~ (poll)     | n/a             | rest             | H    | Market metadata (created/resolution/settlement) — reference, re-fetchable; not a tick series.                                                                                                                                                                                                                                                                |
| **barchart**                 | tradfi (VIX)       | ✓   | ~            | ✗               | rest             | M    | Used only for VIX 15m historical PRELOAD (2020-2025); not on the live/replay path.                                                                                                                                                                                                                                                                           |
| **yahoo**                    | tradfi (VIX)       | ✓   | ~ (15min)    | ✗               | rest             | M    | VIX 15m rolling 60d; delayed quotes; limited intraday history → no reliable replay.                                                                                                                                                                                                                                                                          |
| **eia**                      | tradfi (commodity) | ✓   | ✗            | ✓ (by date)     | rest             | H    | Weekly storage series; no live; series re-fetchable by date.                                                                                                                                                                                                                                                                                                 |
| **open_meteo**               | sports (weather)   | ✓   | ~ (current)  | ✓               | rest             | H    | Forecast + historical-weather API by date.                                                                                                                                                                                                                                                                                                                   |
| **api_football**             | sports             | ✓   | ✓ (in-play○) | ✓ (by date)     | rest             | M    | Has live/in-play fixtures endpoint; fixtures fetchable by date. In-play live only if sports trades it ○.                                                                                                                                                                                                                                                     |
| **odds_api** (The Odds API)  | sports             | ✓   | ✓ (in-play○) | ~ (paid○)       | rest             | M    | Live in-play odds endpoint; **historical odds = paid tier** (replay gated on the plan) ○.                                                                                                                                                                                                                                                                    |
| **footystats**               | sports             | ✓   | ✗            | ✓ (date/season) | rest             | M    | Post-match stat aggregator.                                                                                                                                                                                                                                                                                                                                  |
| **understat**                | sports             | ✓   | ✗            | ✓               | rest             | M    | xG aggregator, post-match.                                                                                                                                                                                                                                                                                                                                   |
| **transfermarkt**            | sports             | ✓   | ✗            | ✓               | rest             | M    | Transfer/value reference.                                                                                                                                                                                                                                                                                                                                    |
| **soccer_football_info**     | sports             | ✓   | ✗            | ✓               | rest             | M    | Progressive-stats aggregator.                                                                                                                                                                                                                                                                                                                                |
| **mdps_odds_horizon_bucket** | sports             | ✓   | ✓            | ✓               | internal         | —    | MDPS-derived bucket — follows the MDPS service mode (not an external vendor).                                                                                                                                                                                                                                                                                |
| **instruments_service**      | all                | ✓   | ✓            | ✓               | internal         | —    | Service output (reference/fixtures) — batch=live symmetry; re-run = replay; `source`-exempt (computed).                                                                                                                                                                                                                                                      |
| **execution_service**        | cefi/defi          | ✓   | ✓            | ✓               | internal         | —    | Service output (`execution_fills`) — follows service mode; `source`-exempt.                                                                                                                                                                                                                                                                                  |
| **strategy_service**         | all                | ✓   | ✓            | ✓               | internal         | —    | Service output (`hedge_ratio_snapshot` / `decision_context`) — `source`-exempt.                                                                                                                                                                                                                                                                              |
| **features_onchain_service** | defi               | ✓   | ✓            | ✓               | internal         | —    | Service output (`feature_observation_snapshot`) — `source`-exempt.                                                                                                                                                                                                                                                                                           |
| **cross_instrument**         | all (features)     | ✓   | ✓            | ✓               | internal         | —    | features cross_instrument family output — `source`-exempt.                                                                                                                                                                                                                                                                                                   |

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

## CORRECTED MODEL (operator 2026-06-07) — there is NO per-venue "fallback" decision; replay-capability is just a fact

> **My earlier "buffer-live-to-disk vs flat-file vs exclude" framing was a conflation — withdrawn.** Writing live to
> disk IS the `live` pipeline_mode; it is not a separate mechanism. `batch`/`live`/`replay` are **the same logical data,
> same schema, on the same GCS/bus paths — three CAPTURE MODES**, differing only in how/when the bytes landed:
>
> - **`live`** = output of a live-mode service generator, streamed to disk as it happens.
> - **`replay`** = an **intraday re-fetch** of a window `live` missed (cold start, or the live service was down),
>   written with the SAME schema but **tagged `replay` purely for the audit trail** (so a cell records that it was not a
>   true live capture). Wants to be as live-like as possible.
> - **`batch`** = the T+1 floor (deep history).
>
> **Read precedence** (consumers — MDPS/features/strategy — assembling a gap-free series on cold start despite
> batch-provider delay): **`live` (primary) → `replay` → `batch`** (the M4 mode-contextual precedence). **Lifecycle**:
> pre-intraday = batch; the `[batch-cutoff → now]` tail = live, else replay; over time you accumulate >1-day live + some
> long-lived historical `replay` (where batch never existed); a **TTL clears `live` once the T+1 batch/live
> reconciliation (MTDS → … → execution) confirms batch is symmetric**.
>
> **Therefore replay-capability is a per-(source, data_type) FACT that feeds M3/M4/M6 — NOT an operator gate.** A source
> that cannot re-fetch intraday simply means: a live-downtime gap on that source is **honestly absent until batch fills
> it** (T+1); the precedence + 4-state manifest already handle that. No `buffer vs flat-file vs exclude` decision
> exists.

### Replay-capability fact table (the M2 input — heterogeneous, web-verified 2026-06-07)

| Source / CeFi venue                                   | Intraday re-fetch (replay)?                          | If NO → gap behaviour                       |
| ----------------------------------------------------- | ---------------------------------------------------- | ------------------------------------------- |
| chain RPC / subgraph / pyth / chainlink / hyperliquid | ✓ deterministic / time-range REST                    | n/a                                         |
| databento · massive · OKX · Deribit · Kraken          | ✓ time-range REST                                    | n/a                                         |
| Binance                                               | ✓ last-24h aggTrades (≤1h windows — covers same-day) | n/a (deep gap > 24h → batch)                |
| **Bybit**                                             | ✗ public REST recent-only (no time-range tick)       | live-downtime gap **waits for batch (T+1)** |
| **Aster**                                             | ❓ unverified (newer venue)                          | until verified, treat as replay=NO → batch  |
| Tardis                                                | ✗ **academic licence blocks replay** (R1)            | CeFi batch source; live/replay = exchanges  |

**Consequence (mechanical, not a decision):** CeFi `live`/`replay` `source` = the **venue** (`source=binance` etc.)
while CeFi `batch` `source` = `tardis` — the SAME shard carries different `source` per mode (the `source` COLUMN already
models this). M2 is keyed `(source/venue, data_type) → {modes}`; Bybit/Aster get `replay` absent (not "blocked").

## The actual next work (pure implementation — no operator blocker remains)

The model is now fully specified by you. Nothing needs an operator call to proceed:

1. **M1 enum + M2 registry** (the agent prompt below / prior) — encode the matrix + this replay-fact table; ship now.
2. **M4 mode-contextual precedence reader** (`live → replay → batch`) — the consumer read path
   (batch-live-reconciliation-service + the per-service readers).
3. **M6 cold-start gate + M7 autonomous replay** — on startup, if the `[batch-cutoff→now]` tail isn't covered by on-disk
   `live`, and the source is replay-capable, autostart `replay`; else honest gap until batch.
4. **T+1 batch/live reconciliation + `live` TTL** — the batch-live-reconciliation-service confirms batch≈live, then the
   TTL clears the now-redundant `live` cells. (Only config knobs, sensible defaults: reconciliation tolerance + TTL
   horizon — tunable, not blocking.)
