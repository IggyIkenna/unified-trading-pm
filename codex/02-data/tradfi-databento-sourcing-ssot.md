---
scope: [engineer, admin]
status: canonical
last_reviewed: 2026-06-18
---

# TradFi Databento Sourcing — Subscription Universe + Billing-Safety SSOT

> **Status:** authoritative (operator decision 2026-06-18). **Code SSOT:**
> `unified-api-contracts/unified_api_contracts/registry/databento_subscription_allowlist.py` (exported from
> `unified_api_contracts.registry`). **Plan:**
> `plans/active/tradfi_databento_subscription_universe_lockdown_2026_06_18.md`.

We subscribe to **exactly three** Databento datasets and ingest **only** the schemas whose history is included free in
that subscription. Anything outside this allowlist is billed **pay-as-you-go (metered)**. Every code path that talks to
Databento gates its `(dataset, schema, start)` through the `assert_*` helpers in the allowlist module — the guards
**fail closed (raise)**, so a metered request never reaches the vendor and **we can never be billed silently**.

## Subscribed datasets (the whole universe)

| Dataset      | Covers                                                                                                                                                                                                                                                                                                           |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GLBX.MDP3`  | CME Globex — S&P futures (ES/MES), BTC/ETH futures (BTC/MBT, ETH/MET), gold (GC/COMEX), WTI crude (CL) + Henry Hub nat gas (NG) futures **and options-on-futures**, FX futures (6E/6B/6J…), E-mini sector index futures, **CME event contracts** (`EC*` series — ECES/ECNQ/ECRTY/ECYM/ECGC/ECCL/ECNG/EC6E/ECBTC) |
| `DBEQ.BASIC` | Databento US Equities — single stocks (S&P constituents), ETFs (BTC/ETH spot ETFs, GLD, sector SPDRs)                                                                                                                                                                                                            |
| `CFE`        | Cboe Futures Exchange — **VIX / VX futures**                                                                                                                                                                                                                                                                     |

**Explicitly NOT subscribed** (querying them raises `DatabentoDatasetNotAllowedError`): all ICE feeds (`IFEU.IMPACT`
Brent/Gasoil, `IFUS.IMPACT` ICE Dollar-Index + softs), `OPRA` (listed options), `EEX`, `Eurex`, and the per-venue equity
feeds (`XNAS.ITCH`/`XNYS.TRADES`/`XCBO.TRADES`/`ARCX.TRADES`/`BATS.TRADES` — consolidated into `DBEQ.BASIC`).

**Event contracts** (operator 2026-06-18): CME event contracts (the `EC*` series —
ECES/ECNQ/ECRTY/ECYM/ECGC/ECCL/ECNG/EC6E/ECBTC) trade on `GLBX.MDP3`, so they are **fully covered by the existing
subscription** — no extra dataset. They are captured under the same lockdown (fetch `ohlcv-1s` + `ohlcv-1m` +
`trades`/`tbbo`; the `("tradfi","event_contract")` validity matrix admits exactly these). Cboe-listed event/binary
contracts (if ever wanted) would need a separate dataset.

### Consequences of the 3-dataset choice (forced drops)

- **Brent crude (BRN), Gasoil** — ICE Europe only → dropped. WTI (CL) + nat gas (NG) remain via CME Globex.
- **ICE Dollar Index (DX), softs (cotton/cocoa/coffee/sugar/OJ)** — ICE US only → dropped. Major-currency **futures**
  (6E/6B/6J/6A/6C/6N/6S) remain via CME Globex.
- Re-adding any of these requires an explicit ICE / OPRA subscription + adding the dataset to
  `ALLOWED_DATABENTO_DATASETS`.

## Schema allowlist + included-history windows (the billing guard)

Databento bundles a **rolling, trailing-from-today** free history window per schema **level**. Older than the window =
metered. We enforce a hard per-level lookback floor: a request whose `start` predates the floor raises
`DatabentoLookbackExceededError`.

| Level | Schemas                                                      | Free window | Lookback floor (`LEVEL_MAX_LOOKBACK_DAYS`) |
| ----- | ------------------------------------------------------------ | ----------- | ------------------------------------------ |
| L0    | `ohlcv-1s`, `ohlcv-1m`, `definition`, `statistics`, `status` | 16 years    | `16 * 365` days                            |
| L1    | `trades`, `tbbo`, `mbp-1`, `bbo-1s`, `bbo-1m`                | 1 year      | `365` days                                 |
| L2    | `mbp-10`                                                     | 1 month     | `30` days                                  |
| L3    | `mbo`                                                        | 1 month     | `30` days                                  |

The floor constants are **conservative approximations** of Databento's rolling boundary (which may be calendar-based) —
if any metered charge ever appears, **reduce** the relevant value in the allowlist module.

### OHLCV policy — fetch `ohlcv-1s` + `ohlcv-1m`

We fetch **both `ohlcv-1s` and `ohlcv-1m`** (both L0 / free 16y) and **aggregate the coarser bars (15m / 1h / 24h)
downstream**. `ohlcv-1m` is kept because we already hold a large 1m corpus — completing it is a deliberate exercise of
the migration / manifest / data-status path; `ohlcv-1s` is the finer-grained add (slower to backfill, also wanted).
Therefore only `ohlcv-1h` / `ohlcv-1d` are **NOT** fetch schemas — requesting them raises
`DatabentoSchemaNotAllowedError`. Both `ohlcv_1s` and `ohlcv_1m` are registered TradFi `data_type`s
(`registry/market_data_categories.py`).

### Batch policy — `batch.submit_job` is BANNED

`batch.submit_job` is the API most likely to silently rack up a large metered bill, so it is **hard-blocked**
(`assert_batch_api_allowed("batch.submit_job")` raises `DatabentoBatchApiBannedError`). Use **streaming**
(`timeseries.get_range`) or the **live client** only. Re-downloading an already-completed legacy job (`batch.download`,
free within TTL) is not gated. A deliberate, audited one-off bulk pull may pass `break_glass=True` in code — never wire
it to a silent default.

## Where the guards are wired (BOTH Databento adapters)

**market-tick-data-service** (market data):

- `market_interface/adapters/tradfi/databento_fetch.py`
  - `_resolve_databento_schema()` → `assert_schema_allowed(data_type)` (loud raise for coarser OHLCV / off-allowlist).
  - `_fetch_timeseries_range()` → `assert_databento_request_allowed(dataset, schema, start)` at the SDK call site (the
    chokepoint for every `timeseries.get_range`).
- `market_interface/clients/databento_batch_jobs.py`
  - `submit_batch_job()` → `assert_batch_api_allowed("batch.submit_job")` (hard block).

**instruments-service** (reference data — instrument `definition` schema):

- `instruments_service/reference_data/adapters/tradfi/databento/adapter.py`
  - `_fetch_symbols()` → `assert_databento_request_allowed(dataset, "definition", start)` before the
    `timeseries.get_range` call. `definition` is L0 (16-year window) → the full-universe instrument backfill stays free
    within the 3-dataset subscription, but an off-allowlist dataset (e.g. `IFEU`) or a too-old `start` raises
    `DatabentoSubscriptionError` BEFORE the vendor is hit. The breach is classified as the `DATABENTO_ENTITLEMENT`
    venue-error (403/entitlement, FAIL no-retry — **NOT** 402/PAYG), emits `ADAPTER_FETCH_FAILED`, and re-raises as
    `RuntimeError` so the per-venue `_fetch_one` handler records `attempted_failed` (shard isolation preserved).

The DEFINITION-schema symbology path (`databento_symbology.py`) is L0/free and unaffected.

## PAYG re-frame — cost emission is credit-burn telemetry, not a hard block

We are **subscription** (not PAYG) since 2026-06-18. The existing `_emit_payg_spend()` in `databento_fetch.py` is kept
as **credit-burn telemetry** — it emits a `DATABENTO_PAYG_SPEND` event with a best-effort `cost_usd` lookup (wrapped in
try/except → `cost_usd=None` on failure) and **never raises / never blocks** a successful fetch. The `402` /
`DATABENTO_PAYMENT_REQUIRED` venue-error stays a FAIL-no-retry (a genuine billing failure / quota exhaustion), but the
**primary** guard is now the window+dataset entitlement (`DATABENTO_ENTITLEMENT`, above), not the 402.

## Single API key (collapse-to-single-key, operator 2026-06-18)

Multi-key rotation is **OFF by default** — one canonical secret `databento-api-key`. Defaults flipped:
`MarketDataProviderConfig.databento_use_multi_key_rotation=False` / `databento_num_api_keys=1`;
`DatabentoClientConfig.use_multi_key_rotation=False` / `num_api_keys=1`; `databento_key_cache.DEFAULT_NUM_API_KEYS=1`.
The shard→key-index round-robin (`get_key_index_for_shard`) collapses to index 1 for every shard, and the single-key
`secret_name` resolves to the bare `databento-api-key` (no `-{index}` suffix). The multi-key code path + its
"job-namespace isolation" docstring are kept **dormant/historical** (not removed) — re-enabling requires provisioning
`databento-api-key-N` secrets again. The transitional `databento-api-key-1` secret was deleted at cutover.

## Non-Databento sources are UNTOUCHED by these guards

The allowlist + `assert_*` guards gate **Databento requests only** (the MTDS streaming fetch + the IS definition fetch).
They do **not** delete stored data, do **not** touch the manifest / data-status, do **not** run inside the candle
aggregator, and never execute on a non-Databento adapter. So **Barchart / Yahoo VIX `ohlcv_15m`** (a separate source) is
fully unaffected: `ohlcv_15m` and `ohlcv_24h` remain registered TradFi `data_types`
(`registry/market_data_categories.py`), existing 15m/24h parquets are not deleted, and the Barchart/Yahoo adapters never
call the Databento allowlist. (Note: Databento doesn't even serve a 15m schema — `ohlcv-15m` would only raise if someone
wrongly routed it through the Databento fetch path, which nothing does.)

## VIX — futures vs the cash index (do not conflate)

`CFE` gives **VX futures** (the VIX futures curve). It does **NOT** provide the **VIX cash index** at 15m. The VIX 15m
**index** gap remains Barchart-preload + Yahoo-rolling-60d + honest gap (see `registry/data_source_continuity.py` and
the VIX 15m one-liner in CLAUDE.md). Adding CFE does **not** close that index gap; it adds the futures.

## Related SSOTs

- `codex/02-data/tradfi-data-types-catalog.md` — TradFi data_type catalog.
- `codex/04-architecture/tradfi-batch-live.md` — TradFi batch/live seam + Databento usage.
- `registry/data_source_continuity.py` — VIX 15m index source windows.
