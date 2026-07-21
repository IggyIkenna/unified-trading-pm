---
doc_type: plan
title: DEX historical replay — LIGHTER-ZKSYNC + EXTENDED-STARKNET + PACIFICA-SOLANA
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-07
locked_by: live-defi-rollout
locked_since: 2026-05-07
---

## Deferred work — migrated to: `plans/active/cefi_consolidated_closeout_2026_07_18.md` — successor:

cefi_consolidated_closeout_2026_07_18 (24 open items: Lighter shipped mid-plan via `/candles` REST — not the original
subgraph-replay premise — per the in-body 2026-05-07 session log; Pacifica's `/kline` route was identified but "TODO
(mirror P1)"; Extended was left "BLOCKED on research" with no public OHLCV endpoint found. All three venues —
LIGHTER-ZKSYNC / PACIFICA-SOLANA / EXTENDED-STARKNET — are confirmed live in the current CeFi umbrella's canonical-id
coverage work (grep hits for all three, incl. "EXTENDED-STARKNET marker-less ids" canonicalisation), so any remaining
historical-replay completeness gap (Pacifica candles adapter, Extended's still-unresolved OHLCV source) is now that
plan's data-completeness surface to carry forward. Verified via grep, not a guess.

# DEX historical replay via on-chain event replay

## Problem

Three CeFi-on-chain CLOB venues lack historical bulk data:

| Venue             | Chain      | Live REST endpoint                                | Historical gap                               |
| ----------------- | ---------- | ------------------------------------------------- | -------------------------------------------- |
| LIGHTER-ZKSYNC    | zkSync Era | `mainnet.zklighter.elliot.ai/api/v1/recentTrades` | only "last ~100 trades", no time-bounded API |
| EXTENDED-STARKNET | Starknet   | `app.extended.exchange/api/v1`                    | 30-day rolling window, no full history       |
| PACIFICA-SOLANA   | Solana     | `api.pacifica.fi/v1`                              | last ~100 trades, no historical bulk         |

UAC `start_date` for these venues is `2024-08-01` / `2024-09-01` / `2024-10-01` — i.e. ~9-12 months of history we need
but can't fetch via REST. Tardis doesn't index these venues. `2026-05-06` user direction:

> "For the things that lack REST APIs for historical, we can do the unchained replay. That's fine. We have access to
> Unchained via the Graph Studio or Alchemy, so we can do those things."

## Approach

Each venue has a different settlement model — the right tool differs:

| Venue             | Settlement model                                     | Replay tool                          |
| ----------------- | ---------------------------------------------------- | ------------------------------------ |
| LIGHTER-ZKSYNC    | Fully on-chain CLOB; every match emits `Trade` event | The Graph subgraph (cheapest)        |
| EXTENDED-STARKNET | Off-chain matched, batched-proof settlement          | Alchemy Starknet `getEvents` + parse |
| PACIFICA-SOLANA   | Off-chain matched, Anchor program settlement         | Alchemy / Helius program-log parsing |

UAC `CHAIN_RPC_TEMPLATES` already has `https://zksync-mainnet.g.alchemy.com/v2/{api_key}` — the chain plumbing is in
place. What's missing is per-venue contract address + ABI + event-decode logic + the MTDS adapter wiring.

## Phase 1 — LIGHTER (canonical greenfield)

Pick Lighter first because it's the cleanest case (fully on-chain CLOB, every match is a contract event).

### Research items (must run before code)

- [ ] **Find the Lighter zkSync mainnet matching contract address(es).** Lighter docs at <https://docs.lighter.xyz/> —
      verify against the addresses they publish for the perp matching contracts. Likely one contract per market
      (BTC-USD, ETH-USD, SOL-USD, etc.) OR one router contract emitting a discriminated `Trade` event. Document in UAC.
- [ ] **Pull the contract ABI** from the deployed bytecode (zksync-explorer.io or sourcify.dev) and identify the `Trade`
      event signature. Expected fields: `marketId`, `price`, `size`, `takerSide` (or `isMakerAsk` matching the live REST
      shape), `tradeId`, `timestamp`. Confirm exact field names — they drive the schema.
- [ ] **Confirm subgraph availability**: check <https://thegraph.com/explorer/?search=lighter> for an existing community
      subgraph. If none, building one from scratch is ~1 day of work (subgraph definition + handler + deploy).
- [ ] **Validate row schema match**: cross-check the proposed historical-replay output against `_fetch_lighter_rest`
      (`market_tick_data_service/adapters/umi_tick_provider.py:1075`):
      ``python     {         "timestamp": <UTC datetime>,         "venue": "LIGHTER-ZKSYNC",         "symbol": <e.g. "BTC-USD">,         "data_type": "trades",         "instrument_type": "perpetual",         "price": <float>,         "amount": <float>,  # mapped from contract `size`         "side": "buy" | "sell",  # mapped from `is_maker_ask` -> "buy" if true else "sell"     }     ``
      The on-chain replay MUST emit the exact same shape so downstream features-onchain doesn't see schema drift. Per
      workspace rule "Live = batch — same data, same fields, same timing semantics, different sources OK".

### Implementation phases (after research)

#### Phase 1A — Subgraph

If no community subgraph exists:

1. Write `subgraphs/lighter_zksync.yaml` with the contract address + Trade event handler.
2. Write `subgraphs/lighter_zksync_mapping.ts` — handle the `Trade(...)` event → `Trade` GraphQL entity.
3. Deploy to Graph Studio / Hosted Service. Capture the subgraph URL.
4. Add subgraph URL to UAC `defi_venue_capabilities.py` as `LIGHTER_HISTORICAL_SUBGRAPH_URL`.

If a community subgraph exists:

1. Audit its schema for completeness (does it have `timestamp` + `marketId` + `price` + `size` + `side`?).
2. If yes, just point UAC at it. If partially missing fields, fork + extend.

#### Phase 1B — `_fetch_lighter_history` adapter

Add `_fetch_lighter_history(date, instrument_ids, ...)` to
`market-tick-data-service/market_tick_data_service/adapters/umi_tick_provider.py` next to `_fetch_lighter_rest`. Routing
sketch:

```python
async def _fetch_lighter_history(
    date: str,
    instrument_ids: list[str] | None = None,
    writer: ChunkWriter | None = None,
    ...,
) -> pd.DataFrame:
    """Historical Lighter trades via subgraph query.

    Live REST capped at ~100 trades; this path queries the Lighter zkSync
    subgraph for trades in [date 00:00 UTC, date 24:00 UTC) per market.
    Schema matches _fetch_lighter_rest exactly.
    """
    subgraph_url = os.environ["LIGHTER_HISTORICAL_SUBGRAPH_URL"]
    start_ms = ... # compute from date
    end_ms = start_ms + 86_400_000

    query = """
    query($start: BigInt!, $end: BigInt!, $first: Int!, $skip: Int!) {
      trades(
        where: {timestamp_gte: $start, timestamp_lt: $end}
        orderBy: timestamp
        orderDirection: asc
        first: $first
        skip: $skip
      ) {
        id timestamp marketId price size isMakerAsk
      }
    }
    """
    rows: list[dict[str, object]] = []
    skip = 0
    while True:
        # paginate via skip; subgraphs cap first=1000
        ...
    return pd.DataFrame(rows)
```

Routing: in `umi_tick_provider.py:177-180` route `LIGHTER-ZKSYNC` to `_fetch_lighter_history` when:

- `os.environ.get("LIGHTER_HISTORICAL_REPLAY", "false") == "true"` AND
- target date is more than 7 days ago (recent dates still use REST since subgraph indexing lags ~5-10 min behind tip)

#### Phase 1C — Schema-parity validation

Before flipping the route on for production:

- [ ] Run the historical replay for a date that's ALSO covered by `_fetch_lighter_rest` (e.g. yesterday's BTC-USD).
- [ ] Diff the two parquets row-by-row on `(timestamp, price, amount, side)` — they should match modulo ordering and
      precision.
- [ ] Confirm no missing trades in the historical replay vs REST (subgraph indexing completeness).

#### Phase 1D — Backfill

- [ ] Launch a `mtds-lighter-history-backfill-{ts}` VM (singleton-locked since The Graph Studio has rate limits) per
      `codex/05-infrastructure/vm-tarball-deployment.md`.
- [ ] Date range: `2024-08-01` (UAC `start_date`) → today. ~9 months × ~10-15 markets × ~5k trades/day → manageable.
- [ ] Add the `mtds-lighter-history-` prefix to `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET`.

## Phase 2 — EXTENDED-STARKNET

Same shape as Phase 1, with Starknet specifics:

### Research

- [ ] Extended contract address on Starknet mainnet (likely a single `Settlement` contract).
- [ ] Event signature for `Trade` / `Settlement` emissions.
- [ ] Test Alchemy Starknet `eth_getLogs` equivalent — Starknet uses `starknet_getEvents` JSON-RPC. UAC RPC template:
      `_defi_chain_data.py` (need to add Starknet — currently only zkSync + Solana there).

### Implementation

- [ ] Add Starknet RPC template to UAC `CHAIN_RPC_TEMPLATES`.
- [ ] `_fetch_extended_history` in `umi_tick_provider.py` mirroring `_fetch_lighter_history`.
- [ ] Schema-parity validation against `_fetch_extended_rest` (`umi_tick_provider.py:798`).
- [ ] Backfill VM.

## Phase 3 — PACIFICA-SOLANA

Solana program-log parsing — different shape:

### Research

- [ ] Pacifica program ID on Solana mainnet.
- [ ] Event-emit pattern: Anchor program `emit!` macros encode event data into program logs as base64. The
      [Anchor IDL](https://www.anchor-lang.com/docs/idl) for Pacifica should be on solscan.
- [ ] Test Helius (or Alchemy Solana) `getSignaturesForAddress` + `getTransaction` to parse program logs for `Trade`
      events.

### Implementation

- [ ] Anchor program log decoder utility in `unified_trading_library` (Solana-generic, not Pacifica-specific) since
      Pyth + future Solana adapters will need the same primitive.
- [ ] `_fetch_pacifica_history` in `umi_tick_provider.py`.
- [ ] Schema-parity validation against `_fetch_pacifica_rest` (`umi_tick_provider.py:611`).
- [ ] Backfill VM.

## Cross-cutting

### Schema parity (CRITICAL — workspace rule)

Every historical replay MUST emit rows that pass:

```python
def assert_schema_match(historical_df: pd.DataFrame, live_rest_df: pd.DataFrame) -> None:
    assert list(historical_df.columns) == list(live_rest_df.columns)
    assert (historical_df.dtypes == live_rest_df.dtypes).all()
```

Otherwise downstream features-onchain calculators see drift and one of either path produces garbage.

### Manifest concurrency principle

Same as every other backfill. Per CLAUDE.md "Manifest concurrency principle":

- read-once startup
- per-date freshness check
- write-time CAS via per-VM shards

The backfill VM launcher must set `MANIFEST_PER_VM_SHARDS=true` + unique `VM_NAME=<tag>` per worker.

### Cost budget per venue

- Lighter (zkSync): The Graph Studio free tier allows 100k queries/month. ~270 days × 15 markets × 1 query/day-market =
  ~4k queries for full backfill — well under quota.
- Extended (Starknet): Alchemy Growth tier 300M Starknet CU/month. `starknet_getEvents` per day-contract is ~20k events
  × ~few CU each. ~270 days × 1 contract × ~20k events × ~5 CU = ~27M CU for full backfill — well under quota.
- Pacifica (Solana): Helius free tier 500k credits/day. Backfill via getTransaction is heavy; budget to take 5-10 days
  at the free tier OR pay for the Pro tier ($99/mo) for one-shot backfill.

## Diagnostic scripts (operator-runnable, deferred to Phase 1A)

`market-tick-data-service/scripts/diagnose_lighter_subgraph.py` — given the Lighter contract address, query the subgraph
for one day's trades, validate schema vs `_fetch_lighter_rest` output, report row count + first/last timestamps. Pattern
follows `market-tick-data-service/scripts/diagnose_kraken_spot_tardis.py` (shipped 2026-05-07 commit `dae9bc4`).

Same shape for Extended + Pacifica — write per-venue diagnostic scripts before flipping the historical route on.

## Done when

- All three venues have `_fetch_*_history` adapters wired.
- `--historical-replay` flag (or env var) routes pre-7-day dates through history adapters and recent dates through REST.
- Schema-parity validation passes for one cross-checked day per venue.
- Backfill VMs have run end-to-end on the full date range and the manifest shows `captured` for ≥99% of expected days.
- `codex/02-data/mtds-data-source-coverage-matrix.md` updated with the new replay sources.
- This plan archived.

## Reference commits

(Reserved — none yet; tracking will populate as Phase 1 ships.)

## Out of scope

- Hyperliquid + Aster historical: both already have historical bulk REST endpoints — covered by existing MTDS adapters.
  NOT part of this plan.
- New DEX venues beyond the three named here. Add them to a separate plan.

---

## Session 2026-05-07 — empirical findings + Lighter Phase 1 SHIPPED

### What changed since the plan was written

The plan's "on-chain event replay via subgraph" premise turned out to be wrong for Lighter. Empirical probing of
`api.tardis.dev/v1/exchanges/lighter`, the Lighter Python SDK (`github.com/elliottech/lighter-python`), and the Lighter
mainnet REST endpoints from a Tokyo VM revealed:

1. **Lighter is not a fully on-chain CLOB at the per-trade level.** Its `block_height` field (~229M as of May 2026) is
   Lighter's own sequencer block, NOT zkSync L1 (~50M). The 80-hex-char `tx_hash` is also non-zkSync (zkSync uses 64-hex
   32-byte hashes). Per-trade events are NOT posted to zkSync mainnet — they live only in Lighter's centralized indexer.
2. **The Lighter SDK confirms `recent_trades` is hard-capped at `limit<=100` with no cursor parameter** — no `from_id` /
   `before_id` / `time_range` argument exists. The bare REST endpoint accepts and silently ignores those params (returns
   latest regardless).
3. **/candles is the ONE historical-capable endpoint.** Accepts `start_timestamp` (sec) + `end_timestamp` (sec) +
   `resolution` (1m / 5m / 15m / 1h / 4h / 1d) + `count_back`. Returns OHLCV bars with both base + quote volume + trade
   count. Goes back to Lighter genesis (`2024-08-01` per UAC `start_date`).

### Phase 1 — Lighter — SHIPPED via /candles route (not subgraph)

MTDS commit `10aa715` adds `_fetch_lighter_candles` in `umi_tick_provider.py` which routes `(LIGHTER-ZKSYNC, ohlcv_1m)`
to `/candles`. Schema matches the canonical ohlcv_1m row shape used by other OHLCV producers in MTDS (CBOE VIX 15m
bars):
`symbol, instrument_id, venue, instrument_type, data_type, timeframe, ts_event, ts_init, open, high, low, close, volume, trade_count`.

4 unit tests pin the contract: routing (ohlcv_1m → /candles, others → /recentTrades), schema parity, day-boundary
clipping, missing-market-id graceful handling.

**What's NOT covered**: per-trade historical for Lighter. The honest gap is that this data does not exist in any public
Lighter API. Forward-poll going forward (already running) is the only way to build per-trade history. Add `ohlcv_1m` to
UAC `data_types` for LIGHTER-ZKSYNC so backfill VMs can request it; `trades` and `book_snapshot_5` data_types stay
live-only.

### Phase 2 — Pacifica — `/kline` discovered

Empirical probe 2026-05-07 found Pacifica has `/api/v1/kline` with the same shape as Lighter's /candles, different field
names:

```
{symbol, interval, start_time (ms), end_time (ms)} -> {success, data: [{t, T, s, i, o, c, h, l, v, n}]}
```

- `t` / `T` = bar start / end (both ms)
- `s` = symbol, `i` = interval
- `o, c, h, l` = OHLC (string-typed, must `float()`)
- `v` = base volume (string)
- `n` = trade count

Verified data exists from ~2025-07-01 onward (probed BTC 1m → 1437 bars on 2026-04-01; empty for 2024-12-01 —
pre-launch). UAC `start_date` for PACIFICA-SOLANA should match this empirical floor.

**Implementation TODO**: clone the Lighter shape into `_fetch_pacifica_candles` next to `_fetch_pacifica_rest` in the
same file. Routing rule identical to Lighter: `(PACIFICA-SOLANA, ohlcv_1m)` → `/kline`; other data_types stay on REST.
Cluster-validation + manifest concurrency rules apply identically.

### Phase 3 — Extended — no public OHLCV endpoint found

Empirical probe 2026-05-07 returned 404 / empty for all candidate paths under `https://api.extended.exchange/api/v1`:
`info/markets/{symbol}/candles`, `info/candles`, `candles`, `info/markets/{symbol}/klines`, `klines`. Extended's
historical OHLCV may live behind authenticated routes only, or may genuinely not be exposed publicly.

**Implementation TODO**: deeper probe needed before writing an adapter:

1. Read Extended docs at `docs.extended.exchange` — find the documented historical endpoint.
2. If none, Extended may need a Starknet event subgraph (unlike Lighter, Extended IS Starknet-native — settlement events
   SHOULD be on-chain).
3. If on-chain replay is the path, add `STARKNET_RPC_TEMPLATE` to UAC `CHAIN_RPC_TEMPLATES` (currently only zkSync +
   Solana).

### Updated phase summary

| Phase | Venue             | Path               | Status                              |
| ----- | ----------------- | ------------------ | ----------------------------------- |
| 1     | LIGHTER-ZKSYNC    | REST `/candles`    | SHIPPED 2026-05-07 (MTDS `10aa715`) |
| 2     | PACIFICA-SOLANA   | REST `/kline`      | TODO (mirror P1)                    |
| 3     | EXTENDED-STARKNET | TBD (probe deeper) | BLOCKED on research                 |

### Reference commits — Session 2026-05-07

- MTDS `10aa715` — `_fetch_lighter_candles` + 4 unit tests
- PM `<this commit>` — empirical findings update
