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
| `XCBF.PITCH` | Cboe Futures Exchange — **VIX / VX futures**. The operator calls this the "CFE" subscription, but Databento's dataset CODE is `XCBF.PITCH` (a bare `CFE` is rejected by the API with 400 validation_failed; verified live 2026-06-19). Coverage 2018-11-04→now; exposes `definition` / `ohlcv-1s` / `ohlcv-1m`.  |

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

**Source provenance differs between 1s and 1m (codified 2026-06-19).** `ohlcv_1s` is **Databento-EXCLUSIVE** — Massive's
flat-file connector does NOT serve a 1s schema (`massive_tradfi_rest_connector.SUPPORTED_DATA_TYPES` omits it). So
`SOURCE_PRIORITY[("tradfi","ohlcv_1s")] = ["databento"]` (databento-only) → `derive_pipeline_mode_for_row` stamps
`pipeline_mode=batch_databento` (provenance-correct). `ohlcv_1m` (and `trades`/`tbbo`) stay `["massive","databento"]`
(massive-first → `batch_massive`) because Massive DOES serve those. The MTDS download gate
(`umi_tick_provider._DATABENTO_SUPPORTED_DATA_TYPES`) and the IS/MTDS routing both carry `ohlcv_1s`; without it the
fetch silently wrote 0 rows. Wiring: CME `VENUE_DATA_TYPE_CAPABILITIES` + `EXPECTED_COVERAGE_BY_ASSET_GROUP` +
`_PER_INSTRUMENT_SHARD_DATA_TYPES` all carry `ohlcv_1s`; `"1s"` is in the `BarTimeframe` closed-set
(`canonical/crosscutting/bar_boundary.py`); `_OHLCV_DATA_TYPE_TIMEFRAME["ohlcv_1s"]="1s"` (MTDS edge conversion);
`TradfiOhlcv1sAdapter` (MDPS passthrough). **Backfill horizon is gated by instruments-service per-date catalog
coverage** — the download enumerates the IS instrument universe per date, so dates the IS catalog hasn't built yield 0
rows ("no active venues"), independent of the OHLCV wiring (which is proven on every covered date).

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

The CFE feed (`XCBF.PITCH` dataset) gives **VX futures** (the VIX futures curve). It does **NOT** provide the **VIX cash
index** at 15m. The VIX 15m **index** gap remains Barchart-preload + Yahoo-rolling-60d + honest gap (see
`registry/data_source_continuity.py` and the VIX 15m one-liner in CLAUDE.md). Adding CFE does **not** close that index
gap; it adds the futures.

## Source provenance is WRITE-STAMPED by the FETCHING adapter — SOURCE_PRIORITY is READ-time only (operator 2026-06-19)

**The bug this fixes.** The OHLCV write path used to stamp `source` + `pipeline_mode` from
`SOURCE_PRIORITY[(asset_group, data_type)][0]` — the read-time PRIORITY source, NOT the adapter that actually fetched.
For `("tradfi","ohlcv_1m")` priority is `["massive","databento"]`, so EVERY 1m row stamped `batch_massive` — including
**CBOE VX futures, which only Databento (`XCBF.PITCH`) carries** (Massive has no CFE). Those rows read as
`source=massive` on a venue Massive serves nothing on → silent mis-attribution.

**The rule (HARD).**

1. **`SOURCE_PRIORITY` is READ-time resolution ORDER only** (`select_primary_available_source` /
   `read_with_source_priority`). It MUST NEVER be used to WRITE-stamp provenance. A backfill that fetched a shard with
   vendor V stamps `source=V` + `pipeline_mode=batch_V`, full stop.
2. **Provenance is write-stamped by the FETCHING ADAPTER's vendor.** The MTDS OHLCV backfill CLI
   (`--operation download --asset-group tradfi`) requires an explicit **`--source databento|massive`** selector
   (non-empty; no `SOURCE_PRIORITY[0]` default). `--source` picks the fetch adapter AND drives the stamp:
   `derive_pipeline_mode_for_row(..., source=<vendor>)` (UTL `pipeline_mode_resolver`) builds `batch_<vendor>` directly
   via `pipeline_mode_for_source`, bypassing `SOURCE_PRIORITY` whenever an explicit `source` is given.
3. **Fail-closed capability validation** (before a single byte is fetched/stamped). UAC
   `assert_source_capable_for_venue(asset_group, data_type, venue, source)` raises `SourceNotCapableForVenueError` when
   the source is not in `SOURCE_PRIORITY[(ag, dt)]` OR is excluded for the venue via `_VENUE_SOURCE_EXCLUSIONS` (e.g.
   `("CBOE","ohlcv_1m"): {massive}` — Massive carries no CFE). So `--source massive` for CBOE/VX **raises**.
4. **Adapter-identity assertion** — the MTDS routing (`umi_tick_provider.fetch_tick_data_for_venue`) routes a `massive`
   request to the Massive adapter (CME futures S3 flat-files; NYSE/NASDAQ equities REST aggs) and a `databento` request
   to the Databento adapter; the Databento branch's `assert_databento_source_ok` raises if a non-databento `--source`
   reaches it (mirrors `_VENUE_SOURCE_EXCLUSIONS` / `_MASSIVE_INCAPABLE_VENUES={CBOE}`). The fetcher's vendor can never
   silently differ from the stamped source.
5. **Free-switch.** The operator picks the vendor per backfill: CFE/VX → `databento`; CME/equities `ohlcv_1s` →
   `databento` (1s is Databento-exclusive); CME/equities `ohlcv_1m` → `massive` (Massive flat-files/REST serve 1m).
   `ohlcv_15m`/`ohlcv_24h` are NOT Databento (VIX index = Yahoo/Barchart; coarser bars aggregate downstream).

**Code:** UTL `pipeline_mode_resolver.derive_pipeline_mode_for_row(source=...)` + `_VENUE_DT_OVERRIDES`
(`("CBOE","ohlcv_1m"|"ohlcv_1s") → batch_databento`); UAC `source_priority.assert_source_capable_for_venue` /
`is_source_capable_for_venue` / `_VENUE_SOURCE_EXCLUSIONS`; MTDS `cli/main.py --source`,
`tick_data_handler._resolve_source` (required for tradfi OHLCV), `_umi_massive.assert_databento_source_ok` /
`MASSIVE_INCAPABLE_VENUES` / `_route_massive` (venue-aware FUTURE/EQUITY). Re-stamp of historically-wrong CBOE cells:
`plans/active/tradfi_databento_subscription_universe_lockdown_2026_06_18.md` § "Source-provenance write-stamp fix".

## Operational gotchas — backfill launchers + live producers (codified 2026-06-21)

Learned the hard way (a whole-fleet silent 0-row failure). The TradFi OHLCV **backfill launchers** in
`deployment-service/scripts/vm/` MUST get three things right or every payload silently fails (rc=0/1, **0 rows
captured**, manifest unmoved):

1. **`VM_TASK=mtds-backfill` — NOT `cefi-backfill`.** Only `mtds-backfill` routes to the chunked MTDS-download branch in
   `setup-data-pipeline-vm.sh` that builds the CLI + passes `--source`. `cefi-backfill` (a copy-paste in the old
   `_tradfi-ohlcv-launcher-lib.sh` / `launch-tradfi-forward-poll.sh`) falls to the catch-all no-op → the download still
   runs via a fallback but **without `--source`** → fails. Fixed fleet-wide ds@9aca3a5 + ds@47c56d7.
2. **`VM_SOURCE` MUST be in the VM metadata AND `setup-data-pipeline-vm.sh` MUST forward it** as `--source $VM_SOURCE`
   in the mtds-backfill `BASE_CLI` — the `TickDataHandler` raises `--source databento|massive is REQUIRED` for ANY
   tradfi OHLCV download (provenance-ambiguous massive-vs-databento; no `SOURCE_PRIORITY[0]` default). Per the source
   model above: `ohlcv_1m`→`massive` (canonical) **or** `databento` (operator free-switch; both serve 1m, dual-source);
   `ohlcv_1s`→`databento` only. The GCS-hosted `setup-data-pipeline-vm.sh` is what the VM actually runs — re-upload it
   after editing (a peer's `create-code-tarballs` re-upload can clobber an un-committed edit; commit to LDR so the next
   tarball preserves it).
3. **`ohlcv_1s` is FUTURES-only (CME + CBOE).** UAC `expected_coverage`: `CME:[trades,ohlcv_1s,ohlcv_1m,tbbo]`,
   `CBOE:[ohlcv_15m,ohlcv_1s,ohlcv_1m]`, but **`NASDAQ:[ohlcv_1m]`, `NYSE:[ohlcv_1m]`** — equities (DBEQ.BASIC) have no
   1s; the MTDS pre-flight drops it (`dropping data_types not supported per UAC: ['ohlcv_1s']`). So a 1s wave for equity
   venues is a pure no-op; only launch 1s for CME/CBOE. The launcher lib default is `ohlcv_1m;ohlcv_1s`
   (`OHLCV_DATA_TYPES` env override) — harmless for equities (pre-flight drops 1s, keeps 1m).
4. **CME event contracts** (binary/event markets: `ECES/ECBTC/ECRTY/ECYM/ECGC/ECCL/ECNG/EC6E/ECNQ`, GLBX.MDP3 `.OPT`
   parents, coverage from 2025-09-28) need BOTH the IS instruments backfill (`launch-tradfi-event-contract-backfill.sh`,
   `--operation instruments`, no `--source`) AND MTDS OHLCV (pass the `EC*.OPT` parents as instrument-ids to a CME OHLCV
   launch). Sparse/event-driven → low row counts are normal.
5. **VM `end_date` must be ≤ yesterday** — Databento historical is T+1; requesting today returns
   `DATA_NOT_AVAILABLE: is in the future` for the final day.

**Live producer (`live_databento`, websocket) — VERIFIED WORKING 2026-06-21:** the `databento_tradfi_ws` connector +
`launch-mtds-live.sh` path CONNECTS, authenticates against the Databento Live gateway (`wss://live.databento.com`,
`session_id` issued), and streams real databento ticks. **Live data IS in our subscription** (operator 2026-06-21 — the
usage-based plan includes Live + 1yr L1 / 1mo L2-L3 history), so the live WS is NOT subscription-blocked. Notes: (a)
`_get_api_key()` resolves the `databento-api-key` **secret** correctly — VERIFIED locally (32-char key via
`get_secret_client(project_id=cfg.gcp_project_id).get_secret(cfg.databento_secret_name)`). A
`no API key — connection skipped` log is a VM-env / SM-access cascade (check `GCP_PROJECT_ID` + Secret-Manager access on
the VM), **NOT a code bug**. (b) **Source-stamp bug FIXED — UAC@1205ae44 (2026-06-21):**
`live_source_for_venue(tradfi,…)` returned the BATCH `SOURCE_PRIORITY[0]=massive` → live rows mis-stamped
`pipeline_mode=live_massive`. `massive` **is** live-capable (operator 2026-06-05, Polygon.io 15-min-delayed REST — do
NOT "fix" by removing its `Mode.LIVE`), but the SOLE tradfi live **WS producer** is `databento_tradfi_ws`
(massive/yahoo/barchart have no live WS connector). Fix = a `tradfi` branch in `live_source_for_venue` returning
`databento` (mirrors `_PREDICTION_LIVE_SOURCE_FOR_VENUE`); batch path unchanged
(`get_primary_source(tradfi,*)=massive`). Verified `live_pipeline_mode_for_venue(tradfi,*) → live_databento`. **Deploy
note:** the live VM bakes UAC from a GCS **tarball** (working-tree tar), so the RUNNING producer keeps `live_massive`
until its tarball is rebuilt from clean LDR (`create-code-tarballs.sh`) + relaunched — the daily forward-poll cron
relaunches but reuses the existing tarball, so a tarball rebuild is required to deploy the label fix. (c) instrument-ids
need the `venue:type:underlying` form (`CME:FUTURES:ES`), not bare `ES`.

## Related SSOTs

- `codex/02-data/tradfi-data-types-catalog.md` — TradFi data_type catalog.
- `codex/04-architecture/tradfi-batch-live.md` — TradFi batch/live seam + Databento usage.
- `codex/02-data/availability-manifest-and-data-status.md` — `source=` provenance (write-stamp by fetcher, all
  asset_groups).
- `registry/data_source_continuity.py` — VIX 15m index source windows.
