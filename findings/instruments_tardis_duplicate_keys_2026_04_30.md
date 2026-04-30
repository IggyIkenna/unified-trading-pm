---
title: Instruments — Duplicate `instrument_key` from URDI Tardis adapter
status: mitigated
severity: medium
created: 2026-04-30
last_updated: 2026-04-30
owners:
  - URDI maintainers (root cause)
  - instruments-service (write-side mitigation)
  - unified-trading-api (read-side mitigation)
related:
  - URDI adapter: .extra/unified-reference-data-interface/unified_reference_data_interface/adapters/tardis.py
  - Catalogue builder: instruments-service/instruments_service/reference_data/catalogue/catalogue_builder.py
  - API route: unified-trading-api/unified_trading_api/routes/instruments.py
  - UAC builder: unified-api-contracts/unified_api_contracts/internal/reference/canonical_id_builder.py
---

# Instruments — Duplicate `instrument_key` from URDI Tardis adapter (multi-fiat-rail collapse)

## TL;DR

For exchanges that list the same crypto on multiple fiat rails (OKX-SPOT
listing `BTC-TRY`, `BTC-BRL`, `BTC-AUD`, `BTC-AED`, `BTC-USD`), Tardis
returns `quoteCurrency = "USD"` on **all** of them — collapsing 5 distinct
exchange listings into 1 canonical `instrument_key = OKX-SPOT:SPOT_PAIR:BTC-USD`
in the URDI adapter. The instruments-service catalogue parquet then has
multiple rows per canonical key.

Two mitigations live in the codebase as of 2026-04-30:

1. **catalogue_builder dedupe** — instruments-service drops duplicate-key
   rows before writing the GCS parquet. First record wins.
2. **API route dedupe** — `unified-trading-api`'s `/instruments/list` and
   `/instruments/live-universe` re-dedupe at read time as defense-in-depth
   (catches any pre-existing GCS data that wasn't rebuilt).

The **root fix** lives in the URDI Tardis adapter and is **deferred** —
changing canonical IDs across the platform has unclear blast radius for
MTDS / features / strategy / PnL services that may already key off the
collapsed IDs.

## Concrete reproduction

```bash
gcloud storage cp \
  "gs://instruments-store-cefi-central-element-323112/instrument_availability/by_date/day=2026-04-14/venue=OKX-SPOT/instruments.parquet" \
  /tmp/okx.parquet

python3 -c "
import pyarrow.parquet as pq
t = pq.read_table('/tmp/okx.parquet').to_pandas()
print('rows:', len(t))                                    # 115
print('unique instrument_key:', t['instrument_key'].nunique())  # 72
print('dup rows:', len(t[t['instrument_key'].duplicated(keep=False)]))  # 66
"
```

For `BTC` alone — 7 rows in this parquet, one canonical key for 5 of them:

| `raw_symbol` | `base_asset` | `quote_asset` | `instrument_key` |
|--------------|--------------|---------------|------------------|
| BTC-USDT | BTC | USDT | `OKX-SPOT:SPOT_PAIR:BTC-USDT` |
| BTC-USDC | BTC | USDC | `OKX-SPOT:SPOT_PAIR:BTC-USDC` |
| BTC-TRY | BTC | **USD** | `OKX-SPOT:SPOT_PAIR:BTC-USD` ← collision |
| BTC-BRL | BTC | **USD** | `OKX-SPOT:SPOT_PAIR:BTC-USD` ← collision |
| BTC-AUD | BTC | **USD** | `OKX-SPOT:SPOT_PAIR:BTC-USD` ← collision |
| BTC-AED | BTC | **USD** | `OKX-SPOT:SPOT_PAIR:BTC-USD` ← collision |
| BTC-USD | BTC | **USD** | `OKX-SPOT:SPOT_PAIR:BTC-USD` |

## Root cause — Tardis vendor quirk

Tardis is the upstream data vendor (third-party). Their
`TardisInstrumentDetail` schema has three fields the URDI adapter relies
on:

```
id            = "BTC-TRY"   ← actual exchange ticker, preserved
baseCurrency  = "BTC"       ← correct
quoteCurrency = "USD"       ← WRONG. Tardis stamps this for non-USD-rail pairs.
                              Probably a USD-anchor normalization on their side
                              (cross-venue analytics convenience). Unclear if
                              documented.
```

The URDI Tardis adapter at
`.extra/unified-reference-data-interface/unified_reference_data_interface/adapters/tardis.py:599-623`
trusts `quoteCurrency`:

```python
base = item.baseCurrency or ""               # "BTC"
quote = item.quoteCurrency or ""             # "USD" ← from Tardis
symbol = f"{base}-{quote}"                   # "BTC-USD"
instrument_key = f"{venue}:{type}:{symbol}"  # "OKX-SPOT:SPOT_PAIR:BTC-USD"
```

Result: the actual exchange listing (`BTC-TRY`) is preserved on `raw_symbol`,
but the canonical `instrument_key` collapses 5 listings into 1.

## Affected venues (CEFI, observed 2026-04-30)

| Venue | Total rows | Unique keys | Duplicates |
|---|---:|---:|---:|
| OKX-SPOT | 115 | 72 | 43 |
| BINANCE-SPOT, BYBIT, COINBASE-SPOT, … | varies | varies | low/zero |
| HYPERLIQUID, ASTER (perps only) | — | — | none |

OKX-SPOT is the dominant offender because OKX explicitly lists fiat-rail
pairs for emerging-market access. Other major CEFI exchanges typically
quote in `USDT` / `USDC` / `USD` and are not affected.

TRADFI and DEFI buckets are **unaffected** — different adapter chains,
different canonical-id construction.

## What it broke

UI symptom: React console warnings on the Terminal watchlist:

```
Encountered two children with the same key, `OKX-SPOT:SPOT_PAIR:USDC-USDC`.
Encountered two children with the same key, `OKX-SPOT:SPOT_PAIR:DAI-USD`.
Encountered two children with the same key, `OKX-SPOT:SPOT_PAIR:NEAR-USD`.
```

The watchlist used `instrument_key` as the React `key=` prop. React
requires uniqueness; duplicates cause "behavior is unsupported and could
change in a future version" warnings and (in extreme cases) reconciler
bugs where rows get duplicated or omitted on re-render.

Other impact surfaces:

- **MDPS shard keys** — if the canonical `instrument_id` collides, two
  exchange listings can't be written to distinct candle parquets.
  Currently this isn't a problem because MDPS writes per `raw_symbol`
  filename, not per `instrument_id`, so each fiat rail still gets its
  own parquet on the candles side. But any tool keying on
  `instrument_id` (catalogue joins, manifest lookups) will see the
  collision.
- **Feature caches / strategy contexts** — anything keying off
  `instrument_key` deduplicates without realising it. A strategy that
  thinks it's tracking BTC-AUD on OKX-SPOT may actually be looking at
  the BTC-USD row's data.

## Mitigations in place (2026-04-30)

### 1. catalogue_builder dedupe (write-side, single source)

`instruments-service/instruments_service/reference_data/catalogue/catalogue_builder.py`
in `build_category_async` — after `_ensure_canonical_id` + `_populate_availability`
runs on each record, drop subsequent records that share an
`instrument_key` with an already-emitted record. First-wins.

Effect: future parquet writes contain one row per canonical key. The
"winning" record's `raw_symbol` reflects whichever rail Tardis returned
first — typically the USD rail itself, because that's how Tardis orders
its response.

Trade-off: we **lose** the per-fiat-rail rows entirely. If we later
need per-rail liquidity / pricing for arbitrage analytics, the data is
gone from the catalogue (still in raw Tardis if we re-fetch). Acceptable
because the lost rows have an incorrect canonical key anyway — the
fields that disambiguate them (`raw_symbol`) are not load-bearing for
any downstream service today.

### 2. API route dedupe (read-side, defense-in-depth)

`unified-trading-api/unified_trading_api/routes/instruments.py` —
`/instruments/list` and `/instruments/live-universe` re-dedupe by
`instrument_key` at response time. Catches:

- Existing GCS data written before the catalogue-builder fix.
- Any future regression at the write layer.
- Any other adapter that hits the same class of bug.

### 3. UI display surface (planned)

The watchlist row needs to show `venue` next to symbol so users can
distinguish `BINANCE-FUTURES BTC-USDT` from `OKX-SPOT BTC-USDT`. Even
without dedupe issues, this is required UX — `BTC-USDT` is listed on
8+ CEFI venues and the user needs to know which one a row represents.

Tracked separately as a watchlist UI enhancement; not blocked by this
issue.

## Root fix — deferred to URDI maintainer

`.extra/unified-reference-data-interface/unified_reference_data_interface/adapters/tardis.py:599-623`
should NOT trust `item.quoteCurrency` when it disagrees with the suffix
of `item.id`. Fix sketch:

```python
base = item.baseCurrency or ""
quote = item.quoteCurrency or ""

# Defensive: when raw_id has a "-XYZ" suffix and that XYZ != quoteCurrency,
# trust the raw_id's suffix. Tardis stamps quoteCurrency=USD as a USD-anchor
# normalization for non-USD-rail pairs (TRY, BRL, AUD, AED) which collapses
# distinct listings into the same canonical key.
if "-" in raw_id:
    raw_base, _, raw_quote = raw_id.upper().rpartition("-")
    if raw_quote and raw_quote != quote:
        quote = raw_quote  # prefer the rail visible in the actual ticker
```

**Why this is not done yet**: changing canonical instrument IDs
ripples across MTDS, features, strategy, execution, risk, PnL — every
service that may have cached references to the current keys. Needs:

1. An audit of which services persist `instrument_key` (vs deriving it
   each run).
2. A coordinated migration window.
3. Backfill of historical data already in GCS under the bad keys.

That's a multi-week cross-team effort, not a quick patch. Until then
the two mitigations above keep downstream surfaces functional.

## How to verify the mitigations

After the catalogue rebuilds (next instruments-service `refresh-catalogue`
run):

```bash
# GCS parquet should have one row per canonical key:
gcloud storage cp \
  "gs://instruments-store-cefi-{project}/instrument_availability/by_date/day={today}/venue=OKX-SPOT/instruments.parquet" \
  /tmp/okx.parquet
python3 -c "
import pyarrow.parquet as pq
t = pq.read_table('/tmp/okx.parquet').to_pandas()
assert t['instrument_key'].is_unique, 'still has duplicates'
print('clean — %d rows, all unique keys' % len(t))
"
```

For older parquets that still have duplicates, the API route will
dedupe at read time:

```bash
curl -s 'http://localhost:8030/instruments/live-universe?asset_group=cefi' \
  | python3 -c "
import sys, json
from collections import Counter
d = json.load(sys.stdin)
keys = [r['instrument_key'] for r in d['data']]
dups = {k:c for k,c in Counter(keys).items() if c>1}
assert not dups, f'response has dupes: {dups}'
print('response clean — %d unique instruments' % len(keys))
"
```

## Cross-venue duplicates (NOT this issue)

`BTC-USDT` exists on `BINANCE-FUTURES`, `BYBIT`, `OKX-FUTURES`, etc. as
distinct canonical IDs:

```
BINANCE-FUTURES:PERPETUAL:BTCUSDT
BYBIT:PERPETUAL:BTCUSDT
OKX-FUTURES:PERPETUAL:BTC-USDT
```

These are **not** duplicates — they're genuinely different instruments
(different exchange, different liquidity, different price). The watchlist
must show `venue` per row so users can distinguish them; this is a
display concern, not a data-quality issue.

## Related notes

- The duplicate-row bug also affects **OPTION** and **FUTURE** types in
  principle, but in practice Deribit/CME options carry expiry+strike in
  the canonical ID which makes collisions much rarer. Spot pairs are
  the dominant exposure surface for this class of bug.
- DeFi venues use a different canonical-ID path
  (`PROTOCOL-CHAIN:TYPE:SYMBOL`) and are not affected.
- TRADFI venues route through Databento (not Tardis) and are not
  affected.
