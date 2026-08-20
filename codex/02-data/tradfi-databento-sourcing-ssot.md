---
doc_type: codex-ssot
title: TradFi Databento Sourcing — Subscription Universe + Billing-Safety SSOT
summary: Databento sourcing SSOT — exactly 3 subscribed datasets (GLBX.MDP3/DBEQ.BASIC/XCBF.PITCH), a fail-closed
  schema+lookback allowlist so metered PAYG never fires silently, databento-first SOURCE_PRIORITY, and write-stamped
  source provenance.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, instruments-service, market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [tradfi, databento, cost, data-correctness, pipeline-mode, ssot-audit]
related:
  [
    /codex/02-data/tradfi-data-types-catalog.md,
    /codex/04-architecture/tradfi-batch-live.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/pipeline-mode-partition.md,
  ]
created: 2026-06-18
authoritative_for:
  [
    Databento 3-dataset subscription universe and billing-safety allowlist,
    TradFi Databento source provenance write-stamping,
  ]
referenced_by:
  [
    /codex/02-data/tradfi-data-types-catalog.md,
    /codex/04-architecture/tradfi-batch-live.md,
    plans/archive/issues/dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md,
    plans/audit/instructions/tradfi_master_audit_instructions.md,
    plans/audit/results/tradfi_massive_migration_audit_2026_06_08.md,
    plans/epics/tradfi_master.md,
  ]
owner:
last_reviewed: 2026-08-03
code_refs:
---

# TradFi Databento Sourcing — Subscription Universe + Billing-Safety SSOT

> **🔴 2026-07-19 — MASSIVE (formerly Polygon.io) REMOVED as a tradfi source** (operator ruling: Databento = batch SoT,
> Yahoo = daily candles). `massive` is **no longer in `SOURCE_PRIORITY`** — the 6 `("tradfi", …)` cells (trades, tbbo,
> ohlcv_1m, ohlcv_15m, options_chain, futures_chain) are now `["databento"]` / `["databento","yahoo"]` only, and the
> runtime routing (`_umi_massive`, the two vendor adapters, `massive-futures-backfill`, `--source massive`) is DELETED
> (`uac@a2beed46` + `mtds@362a487e`). **Everything below that says `["databento","massive"]` / "massive live-capable" /
> "massive-first" is HISTORICAL** — read it for provenance, not current state. **PURGE COMPLETED 2026-07-21**: 1,701,422
> historical `pipeline_mode=batch_massive/` GCS objects → 0, accepted permanent loss (operator Option C, subscription
> terminated). `batch_massive` `PipelineMode` + `possible_manifest` recognition are no longer guarding any on-disk
> objects and can now be removed from code — tracked separately, not yet done as of this doc's last edit. Full plan:
> `plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md`.
>
> **2026-08-03 — the removal is NOW COMPLETE ACROSS ALL REPOS.** The two commits cited above (`uac@a2beed46` +
> `mtds@362a487e`) only ever covered the **read-time `SOURCE_PRIORITY` dict** and **MTDS tick routing** — neither
> touched **instruments-service**, whose Massive **reference-data** adapter stayed live, tested and fully wired for two
> more weeks (found by `/plans/archive/issues/tradfi_adapter_dead_code_fallback_audit_2026_07_25.md` Finding I-2; the
> same inconsistent-sweep root cause also left `VENUE_DATA_AVAILABILITY["POLYGON"]` behind, see
> `/plans/archive/issues/uac_venue_data_availability_stale_polygon_entry_2026_08_02.md`). Operator ruling 2026-08-02
> chose option A (finish the removal). `instruments-service@e7933317` deletes
> `reference_data/adapters/tradfi/massive.py` + `tests/unit/test_massive_adapter.py` and unwires every call site — the
> factory `_ADAPTERS`/`ADAPTER_DATA_SOURCES` entries, `_resolve_source_aware_adapter_key`, the `--source` CLI flag and
> its whole `source=` plumbing (that chain existed solely to re-point a Databento venue at Massive), the `MASSIVE`
> pseudo-venue key-reloader branch, and the `sessions.py` `EXCHANGE_HOURS`/`get_session_metadata` aliases whose only
> consumer was `massive.py`. **Databento is now the sole TradFi reference-data source in code as well as in policy.**
> Deliberately still present (NOT a gap): UAC's `external/massive/` normalisers + schemas, `PipelineMode.BATCH_MASSIVE`
> / `possible_manifest` recognition, and the `source="massive"` mentions in instruments-service `scripts/` +
> `tests/scripts/` — those describe **historical data provenance**, not adapter wiring.
>
> **2026-07-20 operator ruling — WRITE-side hard-reject of `source='massive'` is ACCEPTED.** Because the UTL
> manifest-writer source gate is registry-driven off UAC `SOURCE_PRIORITY`
> (`unified-trading-library/unified_trading_library/manifest_writer/_schema.py` `MissingSourceError`), dropping
> `massive` makes any manifest write carrying `source='massive'` raise. That is **intended**: no new Massive fetches
> exist, and the legacy `batch_massive` rows this ruling originally protected are now moot — the gated GCS purge
> **COMPLETED 2026-07-21** (1,701,422 objects → 0), so there is nothing left to accidentally re-stamp. **READ-side
> recognition** (`batch_massive` `PipelineMode` and `possible_manifest`) is technically still present in code but no
> longer guards any real objects — safe to remove, per the paragraph above. So this ruling narrows only the write path.
> Side effect of the same registry change: the 6 tradfi cells are now single-source, so `source_required()` returns
> `False` for them and the writer auto-stamps the sole remaining source instead of leaving `source=""`.

> **Status:** authoritative (operator decision 2026-06-18). **Code SSOT:**
> `unified-api-contracts/unified_api_contracts/registry/databento_subscription_allowlist.py` (exported from
> `unified_api_contracts.registry`). **Plan:**
> `plans/archive/2026_06/tradfi_databento_subscription_universe_lockdown_2026_06_18.md`.

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

- **Brent crude (BRN), Gasoil** — ICE Europe only → dropped from Databento. WTI (CL) + nat gas (NG) remain via CME
  Globex.
- **ICE softs (cotton/cocoa/coffee/sugar/OJ)** — ICE US only → dropped. Major-currency **futures**
  (6E/6B/6J/6A/6C/6N/6S) remain via CME Globex.
- Re-adding any of these requires an explicit ICE / OPRA subscription + adding the dataset to
  `ALLOWED_DATABENTO_DATASETS`.

### DBEQ.BASIC has no dividends / corporate-actions schema (equity-basis arb dividend yield sourced from yfinance instead)

Confirmed by grepping every Databento adapter in `market-tick-data-service` and `instruments-service` for "dividend" —
zero hits. Databento's US-equities dataset (`DBEQ.BASIC`) exposes price/trade schemas only; it carries no dividends or
corporate-actions schema at any tier we subscribe to — a genuine, permanent dataset gap, not a subscription-tier upsell.
Consumers needing dividend yield (e.g. the crypto-venue equity-perp basis-arb NET-basis calculation — see
[`carry-basis-perp.md`](/codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md) § "Crypto-venue equity-perp basis
variant") source it from **yfinance** instead: trailing-12mo dividend sum ÷ last close, computed directly from
`Ticker.dividends` raw history — NOT the `info["dividendYield"]` field, which has a documented stale/pre-split bug (e.g.
it read 0.45% for NVDA vs. the raw-history-derived 0.125%). This mirrors the established yfinance precedent already used
elsewhere for non-Databento TradFi data (`market-tick-data-service`'s `yahoo_finance_adapter.py`, `features-service`'s
`yfinance_earnings_adapter.py`). Polygon's corporate-actions adapter would close this gap but needs a separate
`polygon-api-key` secret + a cross-repo import from `features-service` — not adopted for this one consumer. Do not add a
Databento dividends fetch path; there is no such schema to fetch.

### KRX + ICE + FX are YAHOO FINANCE, not Databento, and NOT operator-blocked (operator correction 2026-06-27)

Three venues are sourced from **Yahoo Finance**, gated by no subscription and blocked by no operator (UAC@5480f5d5,
IS@dc0d99a):

- **KRX** = Yahoo KOSPI indices — `^KS11` (KOSPI) + `^KS200` (KOSPI200), stamped `KRX:INDEX:KOSPI-USD` /
  `KRX:INDEX:KOSPI200-USD`, `venue_to_data_provider['KRX']='yahoo_finance'`, genesis **2019-01-02**
  (`KRX_INDEX_DAILY_FIRST_DATE`; `get_krx_index_daily_source()` resolver). KRX single stocks also use Yahoo `.KS`
  tickers.
- **ICE** = Yahoo **DXY** (US Dollar Index) — `venue_to_data_provider['ICE']='yahoo_finance'`. ICE was **REMOVED from
  `venue_to_databento`** (the IFUS.IMPACT routing raised `DatabentoDatasetNotAllowedError`); the DXY index remains,
  served by Yahoo.
- **FX** = Yahoo KRW/USD spot pair — `venue_to_data_provider['FX']='yahoo_finance'`
  (`unified_api_contracts/registry/venue_mapping.py`). Daily `ohlcv_24h`, dispatched via
  `market_tick_data_service/adapters/_umi_yahoo.py::fetch_yahoo_fx` (venue-routed, bypasses `--source`); wave-launcher
  wiring shipped `deployment-service@eab5aeb` (`tradfi_multisource_backfill_2026_06_22.md`, archived
  `/plans/archive/2026_08/`).

**HARD: none of KRX, ICE, or FX is "operator-blocked", "Databento-sourced", "needs an adapter", or "off-allowlist".**
Any codex/plan line framing KRX, ICE, or FX as Databento, operator-blocked, or requiring a new subscription/adapter is
STALE — the data is freely available via Yahoo and the adapters exist. (This was an explicit operator correction; do not
re-introduce the "ICE → Databento" or "KRX blocked" framing.)

### CBOE is DUAL-SOURCED — Databento VX-futures AND Yahoo Treasury INDEX, data-type-scoped (fixed 2026-08-09)

Unlike the venues above, **CBOE is not exclusively Databento.** `CBOE:INDEX:US3M/US5Y/US10Y/US30Y-USD` (the Treasury
yield-curve `ohlcv_24h` payload) is Yahoo-routed, same as KRX/ICE/FX — only CBOE's `ohlcv_1s`/`ohlcv_1m` VX-futures
payload (§ above, `XCBF.PITCH`) is Databento. Until `market-tick-data-service@af2c53ce`,
`tick_data_handler.py::_resolve_source()`'s `--source databento REQUIRED` gate was VENUE-scoped only and missing CBOE
from the Yahoo-routed exemption FX/KRX/ICE/FRED already had — every CBOE `ohlcv_24h` payload silently wrote a
blank-instrument `empty_confirmed` placeholder since the launcher's creation (2026-07-21), with ZERO real coverage ever
captured. The fix is **data-type-scoped** (only the `ohlcv_24h` INDEX payload is exempted), so it does not
blanket-exempt CBOE's VX-futures `ohlcv_1s`/`ohlcv_1m` traffic, which still correctly requires `--source databento`.

**Follow-on limitation — FIXED 2026-08-12.** `is_venue_available()` (the discovery-floor check) used to be venue-level,
not venue+data_type — CBOE's registered floor is the Databento VX-futures genesis (2020-06-01, table below), so CBOE
`ohlcv_24h` dates before that were honest-absence-skipped even though the real Yahoo Treasury series has genuine
history back to 2000-01-03 (4 of 5 tenors) / 2018-08-13 (US2Y). Shipped `UAC@a65c2fa9` (`_data_type_floor_overrides`
field on `VenueMapping`) + `MTDS@fe000178` (`data_type` param threaded onto `is_venue_available()`), so a CBOE
`ohlcv_24h` request now resolves against the Yahoo-specific floor instead of the Databento genesis. **The code fix
shipping does not mean the backfill is done** — relaunching the CBOE Treasury-INDEX backfill for the newly-unblocked
window (`launch-tradfi-bf-cboe-indices-ohlcv-24h.sh --start-floor 2018-01-01`, capped at 2018 rather than the real
2000-01-03 floor per operator decision 2026-08-10) is still open, tracked in
`/plans/active/tradfi_satellite_ao_dispatch_batch12_2026_08_10.md` todo 2. Full history:
`/plans/active/issues/cboe_venue_level_discovery_floor_blocks_yahoo_treasury_pre_2020_2026_08_09.md`.

### Per-venue genesis / discovery-start floors — never backfill below them (expected-absent)

The authoritative per-venue lower bound is UAC `get_instrument_discovery_start(venue)` (=`get_venue_start_date` unless
an entry in `venue_instrument_discovery_overrides` narrows it). Dates below the floor are **expected-absent**, not gaps
— the discovery/archive simply has nothing there. TradFi floors (`venue_mapping.py` `venue_start_dates`):

| Venue          | Floor          | Why                                                         |
| -------------- | -------------- | ----------------------------------------------------------- |
| NASDAQ / NYSE  | **2023-04-15** | DBEQ.BASIC equity archive earliest date (nothing before)    |
| CME / FX / ICE | **2020-01-01** | earliest manifest/archive data                              |
| CBOE           | **2020-06-01** | VX-futures (XCBF.PITCH) captured-history floor              |
| KRX            | **2019-01-02** | Yahoo daily backfill floor (history confirmed back to 2019) |

**The TradFi OHLCV backfill launchers ENFORCE these floors** (2026-07-16): `ohlcv_clamp_floor_to_venue` in
`deployment-service/scripts/vm/_tradfi-ohlcv-launcher-lib.sh` raises each launcher's `--start-floor` to the venue's
`get_instrument_discovery_start()` (monotone max — a stricter wrapper floor like CBOE's `2026-01-01` is preserved), so
no year-shard entirely below the floor is ever launched and a below-floor `--year` errors cleanly instead of spawning a
0-row VM that fires a false-CRITICAL `DP_VM_GONE_NO_CAPTURE` (the 2019 CME OHLCV incident). Backstop: if a below-floor
date is still processed (`--force-window` / non-launcher caller), MTDS `_emit_pre_coverage_expected_empties`
(orchestrator `preflight.py`) records `EXPECTED_PRE_SOURCE_COVERAGE_START` sentinels + a `HONEST_ABSENCE` run.log signal
so the exit-code fleet monitor classifies the run benign, not silent-zero.

`venue_instrument_discovery_overrides` narrows the discovery floor ABOVE the market-data floor where the
instrument-discovery API has narrower coverage (e.g. HYPERLIQUID market-data S3 from 2023-04-15 but discovery snapshots
only from 2023-11-01 — without the override the gap renders as `attempted_failed` phantoms). CeFi venues likewise have
an **adapter-registration date distinct from the discovery-start floor** (e.g. BINANCE-DELIVERY adapter added
2026-06-24); the discovery-start map is the floor, not the adapter-add date. SSOT = `get_instrument_discovery_start()`
in `venue_mapping.py`; the instruments-service orchestrator MUST consult it (not `venue_start_dates` directly) when
deciding whether a `(venue, date)` shard is expected to produce records.

## Schema allowlist + included-history windows (the billing guard)

Databento bundles a **rolling, trailing-from-today** free history window per schema **level**. Older than the window =
metered. We enforce a hard per-level lookback floor: a request whose `start` predates the floor raises
`DatabentoLookbackExceededError`.

| Level | Schemas                                                      | Free window                             | Lookback floor (`LEVEL_MAX_LOOKBACK_DAYS`) |
| ----- | ------------------------------------------------------------ | --------------------------------------- | ------------------------------------------ |
| L0    | `ohlcv-1s`, `ohlcv-1m`, `definition`, `statistics`, `status` | no rolling metered boundary (see below) | `5908` days                                |
| L1    | `trades`, `tbbo`, `mbp-1`, `bbo-1s`, `bbo-1m`                | 367 days                                | `367` days                                 |
| L2    | `mbp-10`                                                     | 33 days                                 | `33` days                                  |
| L3    | `mbo`                                                        | 33 days                                 | `33` days                                  |

**Exact boundary, binary-searched live 2026-08-09 (`metadata.get_cost` on GLBX.MDP3/ES.c.0, a cost-estimate endpoint —
no data fetched, no billing risk;** `/plans/archive/2026_08/cefi_satellite_ao_dispatch_batch11_2026_08_09.md` todo 4,
full evidence in that doc's Progress Log — supersedes the 2026-06-24 conservative spot-check below): **L1 (trades)
exactly 367d free / 368d metered** (prior conservative constant was 365d); **L2 (mbp-10) and L3 (mbo) exactly 33d free /
34d metered** (prior conservative constant was 30d) — L1's boundary cross-checked identical on DBEQ.BASIC/AAPL,
confirming the boundary is LEVEL-scoped, not per-dataset. **L0 has NO rolling metered boundary at all**: probed
5850d-5908d back on GLBX.MDP3, every point $0.0000, then 5909d+ raises a hard 422 `data_start_before_available_start`
(GLBX.MDP3's own archive starts 2010-06-06) — never a metered charge.
`_FULL_HISTORY_DAYS`/`LEVEL_MAX_LOOKBACK_DAYS["L0"]` updated from the arbitrary `16*365=5840` approximation to the
measured 5908d (exact distance from 2026-08-09 to GLBX.MDP3's inception — the oldest of the 3 subscribed datasets, so
the widest value safe for all three; XCBF.PITCH starts 2018-11-04, DBEQ.BASIC equities 2023-04-15, both cross-checked
live).

**Prior (2026-06-24) conservative spot-check, for provenance**: `get_cost` at `stype_in="continuous"` — L1 free at 364d
($0) → charged at 371d ($0.12); L2/L3 free at 28d ($0) → charged at 35d ($2.23); L0 $0 at 2000d. That earlier pass only
established the constants were SAFE (inside the true boundary), not exact — the 2026-08-09 binary search above found the
precise boundary and the constants now match it. **The ~241k beyond-free cells in the historical backfill universe stay
clipped** (fetching them would be charged at metered PAYG rates) — the guardrail FAILS-CLOSED so they are never fetched.

### OHLCV policy — fetch `ohlcv-1s` + `ohlcv-1m`

We fetch **both `ohlcv-1s` and `ohlcv-1m`** (both L0 / free 16y) and **aggregate the coarser bars (15m / 1h / 24h)
downstream**. `ohlcv-1m` is kept because we already hold a large 1m corpus — completing it is a deliberate exercise of
the migration / manifest / data-status path; `ohlcv-1s` is the finer-grained add (slower to backfill, also wanted).
Therefore only `ohlcv-1h` / `ohlcv-1d` are **NOT** fetch schemas — requesting them raises
`DatabentoSchemaNotAllowedError`. Both `ohlcv_1s` and `ohlcv_1m` are registered TradFi `data_type`s
(`registry/market_data_categories.py`).

**Source provenance differs between 1s and 1m (codified 2026-06-19; SOURCE_PRIORITY updated to DATABENTO-FIRST
2026-06-24).** `ohlcv_1s` is **Databento-EXCLUSIVE** — Massive's flat-file connector does NOT serve a 1s schema
(`massive_tradfi_rest_connector.SUPPORTED_DATA_TYPES` omits it). So
`SOURCE_PRIORITY[("tradfi","ohlcv_1s")] = ["databento"]` (databento-only) → `derive_pipeline_mode_for_row` stamps
`pipeline_mode=batch_databento` (provenance-correct).

**TradFi SOURCE_PRIORITY is DATABENTO-FIRST (2026-06-24, coordinator-directed; supersedes the 2026-06-05/2026-06-11
massive-first ordering):** `(tradfi, trades/tbbo/ohlcv_1m/ohlcv_15m/options_chain/futures_chain) = [databento, massive]`
— databento is the PRIMARY [0] (verified-complete for the live MVP universe: Binance tradfi-perp basis tickers 56/56 +
10/10 representative ETFs in DBEQ.BASIC, GLBX.MDP3 CME futures, XCBF.PITCH CFE/VX which massive never carried). massive
is now the **FALLBACK [1]** — the broad-corpus bulk-backfill path + the per-venue granular slot via
`_VENUE_SOURCE_EXCLUSIONS` for any future cell databento genuinely lacks (e.g. a non-US venue). `ohlcv_1s` stays
databento-only. Live + batch now CONVERGE on databento (the `live_massive` source-stamp bug — `live_source_for_venue`
resolving via the OLD batch `SOURCE_PRIORITY[0]=massive`, UAC@1205ae44 — is doubly-moot since the batch primary is
databento too). `massive` IS still live-capable (operator 2026-06-05 — do NOT remove its `Mode.LIVE`) but the sole
tradfi live WS producer is `databento_tradfi_ws`. Deploy: the live VM bakes UAC from a GCS tarball — a
`create-code-tarballs.sh` rebuild from clean LDR + relaunch is required to pick up the databento-first `SOURCE_PRIORITY`
order.

`ohlcv_1m` (and `trades`/`tbbo`) are now databento-first (`["databento","massive"]`). The MTDS download gate
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

## CME OHLCV fetch — GLBX.MDP3 symbology mechanics (MTDS@dc8075da, @b35ecb74)

Fetching CME OHLCV from `GLBX.MDP3` via parent symbols (`ES.FUT` / `ES.OPT`, `stype_in=parent`) has three HARD
requirements — getting any wrong silently produces `attempted_failed` cells (3355 cells on the 2020 CME backfill before
the fix):

1. **`stype_out=instrument_id`, NOT `stype_out=raw_symbol`.** `timeseries.get_range` rejects `stype_out=raw_symbol` with
   `stype_in=parent` (HTTP 422). Fetch with `stype_out=instrument_id`, then **post-fetch resolve** iid→raw via a
   separate `symbology.resolve(stype_in=instrument_id, stype_out=raw_symbol)` call, building an `iid_to_raw` map that
   `_process_chunk` injects as a `raw_symbol` column before enrichment (so the classifier sees `ESM0` / `E1AG0 C3240`,
   not `ES.FUT` / `ES.OPT`).
2. **Paginate `symbology.resolve` in batches of `PAGE_SIZE=2000`.** `ES.FUT`+`ES.OPT` over even a ~7-day window yields
   ~2075 instrument_ids — over Databento's 2000-symbol-per-request limit → another 422. Batch the resolve so every iid
   is mapped.
3. **CME option symbols contain SPACES — normalize + classify, never leave `instrument_type=UNKNOWN`.** CME short
   options (e.g. `E1AG0 C3240`) and OSI-packed options carry a space; `classify_databento_symbol` (UAC
   `external/databento/databento_classifier.py`) handles them via `_CME_SHORT_OPTION_RE` / `_OSI_OPTION_RE`
   (`symbol.replace(" ", "")`) and classifies to canonical `InstrumentKey` + `OPTION`/`FUTURE`. An unclassified symbol
   landing as `instrument_type=UNKNOWN` is REJECTED by the writer — so classification must succeed for every fetched
   symbol.

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

    > **⚠️ CODE CORRECTION (2026-07-10, CF-11 IS audit).** The above describes the intent, but the **current** code
    > distinguishes two cases: (a) a **transient in-universe vendor fetch failure** (`BentoError` / network on the real
    > `timeseries.get_range`) DOES classify → log → **re-raise as `RuntimeError` → `attempted_failed`** (correct,
    > mirrors cefi); (b) a **`DatabentoSubscriptionError` entitlement breach** (an off-allowlist dataset / too-old
    > window) is a **permanent pre-request** condition and is **caught + dataset-level ISOLATED** in `get_instruments`
    > (`adapter.py` `DatabentoSubscriptionError` handlers `continue` / empty-batch), **NOT** re-raised per-instrument —
    > deliberate shard isolation from the 2026-06-18 3-dataset subscription cutover (regression test
    > `tests/unit/test_databento_tardis_adapter.py`). This masks nothing today: `TRADFI_DATABENTO_INSTRUMENTS` /
    > `TRADFI_TICKER_UNIVERSE` carry **zero** off-allowlist entries (ICE/IFEU/IFUS dropped; IBIT/ETHA moved to
    > in-allowlist `DBEQ.BASIC`). So the sentence above should read: transient in-universe failure → `attempted_failed`;
    > permanent entitlement breach → dataset-isolated (filtered from the universe, not a per-cell failure).

The DEFINITION-schema symbology path (`databento_symbology.py`) is L0/free and unaffected.

### Exchange-code → human-name mapping (`tradfi_symbology.py::EXCHANGE_CODE_TO_NAME`)

`unified_api_contracts/registry/tradfi_symbology.py` is the SSOT module for Databento parent/options symbol
validation, exchange-code mappings, and TradFi venue instrument definitions — "previously scattered across
instruments-service config files, centralized here as the system SSOT per UAC registry pattern" (module docstring).
Its `EXCHANGE_CODE_TO_NAME: dict[str, str]` (root ticker code → human-readable product name, e.g. `"ES": "SP500"`,
`"CL": "CRUDE"`, `"6A": "AUD"`, 33 entries) is the one re-exported through `unified_api_contracts.registry`
(`from unified_api_contracts.registry import EXCHANGE_CODE_TO_NAME`) and is the live, fleet-consumed SSOT —
canonicalization/migration scripts, chain-bundle rewrite tooling, `_tradfi_manifest_shard.py`, and `reader.py` all
resolve root→human-name through it.

**A second, same-named module-level `EXCHANGE_CODE_TO_NAME` dict lives in
`unified_api_contracts/registry/tradfi_instrument_universe.py`** (added 2026-08-07, extends the naming convention to
MICRO-contract codes, e.g. `"M6A": "MICRO-AUD"`). It is **not** re-exported through `registry/__init__.py` — that
file's `tradfi_instrument_universe` import block does not include it — and has zero confirmed consumers, including
within its own module (checked: not imported elsewhere, and not referenced past its own definition). Grepping the
bare name `EXCHANGE_CODE_TO_NAME` will surface both files; `tradfi_symbology.py`'s is the one that's actually part of
the public UAC registry surface.

## PAYG re-frame — cost emission is credit-burn telemetry, not a hard block

We are **subscription** (not PAYG) since 2026-06-18. The existing `_emit_payg_spend()` in `databento_fetch.py` is kept
as **credit-burn telemetry** — it emits a `DATABENTO_PAYG_SPEND` event with a best-effort `cost_usd` lookup (wrapped in
try/except → `cost_usd=None` on failure) and **never raises / never blocks** a successful fetch. The `402` /
`DATABENTO_PAYMENT_REQUIRED` venue-error stays a FAIL-no-retry (a genuine billing failure / quota exhaustion), but the
**primary** guard is now the window+dataset entitlement (`DATABENTO_ENTITLEMENT`, above), not the 402.

## Billing-health verification MUST include one real scoped data-pull — never `list_datasets()`/`warmup()` alone

**HARD RULE (codified 2026-08-14, `plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md`).**
Confirming the Databento account is billing-healthy (after a suspension, or before resuming a paused backfill/live
producer) requires at least one **real, scoped** call — a `timeseries.get_range` / `definition` fetch for a known
instrument, or the live WS actually receiving a tick — not just `DatabentoBaseClient.warmup()` /
`metadata.list_datasets()` in isolation. Those two are unscoped, account-level calls: they confirm the API key
authenticates, but they do **not** prove every access path (in particular the live WS session) is actually functional.

**The incident this closes.** On 2026-08-10, `warmup()` + `list_datasets()` succeeded (29 datasets returned, no
401/403/locked/suspended error) and that was treated as evidence the WHOLE account — batch and live — was restored. It
wasn't independently re-verified for the live `databento_tradfi_ws` connector. On 2026-08-12 the account was suspended
again (`api_key_deactivated` / `CRAM authentication error: ... unpaid invoice`) and the live producer's feed died
silently — the process kept heartbeating for ~50h with zero real ticks, invisible to any liveness check, and was only
caught 2026-08-14 during an unrelated diagnosis.

**The rule going forward**: after any billing-suspension recovery, or before trusting an existing "account restored"
verification to resume backfills, re-verify EACH access path you intend to rely on with a real scoped pull specific to
that path — a batch/historical `timeseries.get_range` call for the MTDS/instruments-service backfill paths, AND a real
received tick (not just a successful connect) for the live WS path if live capture depends on it. An unscoped
`warmup()`/`list_datasets()` success is a necessary but NOT sufficient signal.

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
aggregator, and never execute on a non-Databento adapter. So **Yahoo VIX `ohlcv_15m`** (a separate source; **Barchart
was RETIRED 2026-06-24** — see below, no longer a live adapter) is fully unaffected: `ohlcv_15m` and `ohlcv_24h` remain
registered TradFi `data_types` (`registry/market_data_categories.py`), existing 15m/24h parquets are not deleted, and
the Yahoo adapter never calls the Databento allowlist. (Note: Databento doesn't even serve a 15m schema — `ohlcv-15m`
would only raise if someone wrongly routed it through the Databento fetch path, which nothing does.)

## VIX — futures vs the cash index (do not conflate)

**⚠️→✅ CORRECTED 2026-07-25** — this section previously described Barchart as a live VIX 15m source; Barchart was
RETIRED 2026-06-24 (operator ruling, plan-reconcile finding 375, §A2 B-queue — see
`/plans/archive/tradfi_massive_dual_source_2026_05_28.md` line 64) and is no longer wired anywhere. Ground-truth
`SOURCE_PRIORITY` for `("tradfi", "ohlcv_15m")` is now `["databento", "massive", "yahoo"]` (was:
`["databento", "yahoo", "barchart"]`).

The CFE feed (`XCBF.PITCH` dataset) gives **VX futures** (the VIX futures curve). It does **NOT** provide the **VIX cash
index** at 15m. The VIX 15m **index** gap remains Yahoo-rolling-60d + honest gap (Barchart-preload is retired, no longer
part of this picture; see `registry/data_source_continuity.py` and the VIX 15m one-liner in CLAUDE.md). Adding CFE does
**not** close that index gap; it adds the futures.

**Retired manifest rows — disposition (operator ruling 2026-07-20, re-verified 2026-07-30): quarantine-with-tracking,
NOT purge.** The live tradfi manifest still carries 9,119 `venue=BARCHART` rows, 100% `capture_status=empty_confirmed`
(0 captured — no real historical VIX data at risk); 4,655 of those carry the retired `source=barchart` stamp from a
single stale pre-databento-flip seed (`enumerator_run_id=enum-universe-tradfi-20260507-144921`), the rest are
current-source (`databento`/`yahoo`) honest-absence rows for the same venue. Unlike the `massive` orphan class, these
rows sit in the terminal `empty_confirmed` state (not `expected_unattempted`), so they are outside the wave-launcher's
`NEEDS_WORK` set and cause zero wasted compute — they are inert. KEEP as-is; do not purge. Full audit trail:
`/plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md`,
`/plans/archive/issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md`.

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
5. **Free-switch.** The operator picks the vendor per backfill: CFE/VX → `databento` (Massive never carried XCBF.PITCH);
   CME/equities `ohlcv_1s` → `databento` (1s is Databento-exclusive); CME/equities `ohlcv_1m` / `trades` / `tbbo` →
   `databento` (now the PRIMARY; `massive` is the fallback per the 2026-06-24 databento-first order — still valid if
   databento is unavailable for a specific venue/cell). `ohlcv_15m`/`ohlcv_24h` are NOT Databento schemas (VIX index =
   Yahoo/Barchart; coarser bars aggregate downstream).

**Code:** UTL `pipeline_mode_resolver.derive_pipeline_mode_for_row(source=...)` + `_VENUE_DT_OVERRIDES`
(`("CBOE","ohlcv_1m"|"ohlcv_1s") → batch_databento`); UAC `source_priority.assert_source_capable_for_venue` /
`is_source_capable_for_venue` / `_VENUE_SOURCE_EXCLUSIONS`; MTDS `cli/main.py --source`,
`tick_data_handler._resolve_source` (required for tradfi OHLCV), `_umi_massive.assert_databento_source_ok` /
`MASSIVE_INCAPABLE_VENUES` / `_route_massive` (venue-aware FUTURE/EQUITY). Re-stamp of historically-wrong CBOE cells:
`plans/archive/2026_06/tradfi_databento_subscription_universe_lockdown_2026_06_18.md` § "Source-provenance write-stamp
fix".

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
   model above (2026-06-24 databento-first): `ohlcv_1m` / `trades` / `tbbo` → `databento` (PRIMARY) **or** `massive`
   (fallback; both serve 1m, dual-source); `ohlcv_1s` → `databento` only. The GCS-hosted `setup-data-pipeline-vm.sh` is
   what the VM actually runs — re-upload it after editing (a peer's `create-code-tarballs` re-upload can clobber an
   un-committed edit; commit to LDR so the next tarball preserves it).
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
`databento` (mirrors `_PREDICTION_LIVE_SOURCE_FOR_VENUE`); batch path updated to databento-first
(`get_primary_source(tradfi,*)=databento` since 2026-06-24 coordinator change). Verified
`live_pipeline_mode_for_venue(tradfi,*) → live_databento`. **Deploy note:** the live VM bakes UAC from a GCS **tarball**
(working-tree tar), so the RUNNING producer keeps `live_massive` until its tarball is rebuilt from clean LDR
(`create-code-tarballs.sh`) + relaunched — the daily forward-poll cron relaunches but reuses the existing tarball, so a
tarball rebuild is required to deploy the label fix. (c) instrument-ids need the `venue:type:underlying` form
(`CME:FUTURES:ES`), not bare `ES`.

## Related SSOTs

- `/codex/02-data/tradfi-data-types-catalog.md` — TradFi data_type catalog.
- `/codex/04-architecture/tradfi-batch-live.md` — TradFi batch/live seam + Databento usage.
- `/codex/02-data/availability-manifest-and-data-status.md` — `source=` provenance (write-stamp by fetcher, all
  asset_groups).
- `registry/data_source_continuity.py` — VIX 15m index source windows.
