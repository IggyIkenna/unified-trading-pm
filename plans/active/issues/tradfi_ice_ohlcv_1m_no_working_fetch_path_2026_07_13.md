---
doc_type: issue
title:
  TRADFI:ICE:ohlcv_1m has ZERO working fetch path — Databento routing is dead (ICE dropped from the 3-dataset
  subscription) and the documented Yahoo-DXY fallback for ICE was never actually wired in MTDS
summary:
  'Found 2026-07-13 during the pipeline_e2e_check TRADFI cluster diagnostic pass (data_pipeline_e2e_check_2026_07_10.md
  todo 25). `market_tick_data_service/adapters/umi_tick_provider.py:134`''s `_DATABENTO_VENUES` frozenset keeps ICE
  (`frozenset({"CME", "ICE", "NYSE", "NASDAQ", "CBOE", "ARCA", "BATS"})`), so any ICE tick-data request routes to the
  Databento path — but `unified-api-contracts/registry/tradfi_instrument_universe.py`''s `TRADFI_DATABENTO_INSTRUMENTS`
  has ZERO rows with `venue="ICE"` (confirmed via direct grep + read: the ICE Databento datasets IFEU.IMPACT/IFUS.IMPACT
  were deliberately dropped in the 3-dataset subscription lockdown, operator 2026-06-18 — already-known,
  already-excluded from `--source` forcing per an earlier 2026-07-13 session finding this session inherited). Meanwhile
  `unified_api_contracts/registry/market_data_categories.py` lines 313-320 explicitly documents the INTENDED design:
  ''ICE STAYS a venue here because the ICE/NYBOT US Dollar Index (DXY) is still sourced via Yahoo (non-Databento) under
  venue ICE'' — corroborated by `venue_mapping.py:211` (`"ICE": "yahoo_finance"`), `data_source_continuity.py:211`, and
  `tradfi_instrument_universe.py`''s `YAHOO_INDICES` registry (line 511: `YahooIndexDef("DXY", "ICE", "DXY", "DX-Y.NYB",
  date(2019, 1, 2), "fx")`). This isn''t just a stale comment —
  `instruments-service/instruments_service/reference_data/adapters/tradfi/databento/adapter.py`''s
  `_create_yahoo_index_records()` (lines 654-680) genuinely materializes a real, live
  `InstrumentRecord(instrument_key="ICE:INDEX:DXY-USD", venue="ICE", ...)` from `YAHOO_INDICES` — so IS''s discovered
  universe DOES contain a real ICE instrument today. But grepping `umi_tick_provider.py` for the only 2 Yahoo-fetch
  functions that exist — `_fetch_yahoo_equities` (KRX `.KS` single stocks) and `_fetch_yahoo_fx` (the `FX` venue''s
  currency pairs) — shows NEITHER is dispatched for `venue_upper == "ICE"` (confirmed: the only two `venue_upper ==`
  branches calling these are `"FX"` at line 559 and `"KRX"` at line 568; ICE falls through to the dead Databento branch
  at lines 582/586). Net result: `TRADFI:ICE:ohlcv_1m` (and, less coherently, `expected_coverage.py`''s ICE entry also
  lists `trades`/`tbbo`, tick-level types a Yahoo daily-index feed could never serve anyway) is declared expected +
  capable in every registry (`expected_coverage.py:151` `["trades", "ohlcv_1m", "tbbo"]`,
  `VENUE_DATA_TYPE_CAPABILITIES["ICE"]["ohlcv_1m"] = "2019-01-01"`) and a real instrument exists for it upstream, but
  there is no code path anywhere that can ever fetch it — the same class of registry-vs-adapter mismatch as the
  already-fixed KRX intraday gap (`krx_intraday_ohlcv_registry_vs_adapter_mismatch_2026_07_12.md`, resolved 2026-07-13),
  but for ICE, and structurally worse (KRX''s registry only over-promised intraday granularity beyond what Yahoo
  supports; ICE''s registry promises a data_type with a real upstream instrument and a real intended source, and the
  wiring for that source was simply never built).'
status: resolved
nature: notes
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, instruments-service]
scope: [engineer, admin]
tags:
  [
    tradfi,
    ice,
    dxy,
    yahoo-finance,
    databento,
    expected-coverage,
    honest-coverage,
    data-correctness,
    registry-adapter-mismatch,
  ]
related:
  [
    ../data_pipeline_e2e_check_2026_07_10.md,
    krx_intraday_ohlcv_registry_vs_adapter_mismatch_2026_07_12.md,
    tradfi_databento_ohlcv_silent_zero_rows_2026_07_12.md,
    ../../../codex/02-data/honest-coverage-model.md,
    ../../../codex/02-data/tradfi-databento-sourcing-ssot.md,
  ]
created: 2026-07-13
parent_epic: infrastructure_master
priority: P3
source:
  [pipeline_e2e_check todo-25 TRADFI diagnostic pass, real code read across 3 repos (no live VM needed), 2026-07-13]
assigned_vm: NA
resolved_by: unified-api-contracts@753fb81a + market-tick-data-service@971bdd35 (operator decision 2026-07-13)
locked_by:
execution_scope: local-only
estimate_class: research
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.5
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
---

# TRADFI:ICE:ohlcv_1m has zero working fetch path (Databento dead, Yahoo-DXY never wired)

## Context

`data_pipeline_e2e_check_2026_07_10.md` todo 25's TRADFI cluster diagnostic pass (2026-07-13) turned up 4 distinct real
issues; 3 were fixed directly (YAHOO_FINANCE crash in IS, CBOE's expired live-leg smoke symbol, KRX's
`VENUE_DATA_TYPE_CAPABILITIES` registry gap). This 4th one is filed rather than fixed — it needs an operator/
architecture decision, not a mechanical patch.

## The gap, precisely

1. **Databento path is structurally dead for ICE.** `market_tick_data_service/adapters/umi_tick_provider.py:134`:

   ```python
   _DATABENTO_VENUES = frozenset({"CME", "ICE", "NYSE", "NASDAQ", "CBOE", "ARCA", "BATS"})
   ```

   ICE is still in this set, so any ICE tick-data request routes to the Databento fetch branch
   (`umi_tick_provider.py:582`/`586`). But `unified-api-contracts/registry/tradfi_instrument_universe.py`'s
   `TRADFI_DATABENTO_INSTRUMENTS` (line 390) has ZERO entries with `venue="ICE"` — the file's own comment (lines
   293-303) explains why: the ICE Databento datasets (`IFEU.IMPACT`/`IFUS.IMPACT` — Brent/Gasoil/US softs/the ICE
   Dollar-Index future) are OUT of the paid 3-dataset subscription (operator 2026-06-18, GLBX.MDP3 + DBEQ.BASIC + CFE
   only) and were deliberately dropped. This part is already-known, already-excluded from `--source` forcing per an
   earlier session finding this session inherited — not new.

2. **The documented INTENDED fallback (Yahoo DXY) was never implemented.** `market_data_categories.py` lines 313-320
   explains the actual intent:

   > "ICE STAYS a venue here because the ICE/NYBOT US Dollar Index (DXY) is still sourced via Yahoo (non-Databento)
   > under venue ICE, and the market-session / data-status / source-resolution registries key off it."

   Corroborated independently by `venue_mapping.py:211` (`"ICE": "yahoo_finance"`), `data_source_continuity.py:211`, and
   `tradfi_instrument_universe.py`'s `YAHOO_INDICES` list (line 511:
   `YahooIndexDef("DXY", "ICE", "DXY", "DX-Y.NYB", date(2019, 1, 2), "fx")`).

3. **This isn't a stale comment — a real ICE instrument genuinely exists today.**
   `instruments-service/instruments_service/reference_data/adapters/tradfi/databento/adapter.py`'s
   `_create_yahoo_index_records()` (lines 654-680) reads `YAHOO_INDICES` and materializes real `InstrumentRecord`s,
   including `instrument_key="ICE:INDEX:DXY-USD", venue="ICE"`. So instruments-service's discovered universe DOES
   contain a live ICE instrument MTDS is expected to fetch tick data for.

4. **But no Yahoo-fetch function is wired to ICE in MTDS.** Grep of `umi_tick_provider.py` for Yahoo-fetch functions
   shows exactly 2: `_fetch_yahoo_equities` (KRX `.KS` single stocks) and `_fetch_yahoo_fx` (the `FX` venue's currency
   pairs). The only two `venue_upper ==` dispatch branches that call them are `"FX"` (line 559) and `"KRX"` (line 568).
   ICE is not one of them — it falls straight through to the dead Databento branch (step 1 above).

Net effect: `TRADFI:ICE:ohlcv_1m` is declared BOTH expected (`expected_coverage.py:151`:
`"ICE": ["trades", "ohlcv_1m", "tbbo"]`) and capable (`VENUE_DATA_TYPE_CAPABILITIES["ICE"]["ohlcv_1m"] = "2019-01-01"`),
and a real upstream instrument exists for it — but there is no code path anywhere in this codebase that can ever
successfully fetch it. Same class of registry-vs-adapter mismatch as the already-resolved KRX intraday gap
(`krx_intraday_ohlcv_registry_vs_adapter_mismatch_2026_07_12.md`), but structurally worse: KRX's registry merely
over-promised a granularity Yahoo can't serve; ICE's registry promises a data_type with a real, live, intended source
that was simply never wired up.

Side note (not the primary finding, but adjacent and worth flagging): `expected_coverage.py`'s ICE entry also lists
`trades` and `tbbo` — tick-level data types a Yahoo daily-bar DXY index feed could never serve even if the Yahoo path
were wired. Whichever resolution direction is chosen below should also address whether `trades`/`tbbo` belong in ICE's
expected coverage at all.

## Two resolution paths (operator/architecture decision needed)

1. **Build the missing Yahoo-DXY route for ICE**, mirroring how KRX/FX already have one: add an `"ICE"` dispatch branch
   in `umi_tick_provider.py` (or extend `_fetch_yahoo_fx`/a new small helper) that fetches `DX-Y.NYB` daily bars and
   writes them as `ohlcv_1m`-labeled... except DXY is a DAILY Yahoo series (`^`-prefixed cash index, no intraday Yahoo
   feed backing it per the existing `YAHOO_INDICES` genesis-date convention) — so a literal `ohlcv_1m` label would be
   dishonest labeling of daily data. This path likely also requires deciding whether ICE's REAL servable granularity is
   `ohlcv_24h` (matching what Yahoo can actually deliver), not `ohlcv_1m` — i.e., this option may itself resolve into
   option 2's registry-narrowing plus a real (renamed) fetch path, not a literal fetch-path build against the CURRENT
   `ohlcv_1m` label.
2. **Narrow ICE's `expected_coverage.py` entry**, the same way KRX's was narrowed today (2026-07-13,
   `unified-api-contracts@a2751f36`): drop `ohlcv_1m` (and likely `trades`/`tbbo`, per the side note above) since
   Databento's ICE datasets are excluded by subscription and no other path exists; decide whether to keep a narrowed
   `ohlcv_24h`-only entry (would still need a NEW Yahoo-DXY-daily fetch wire-up, just a smaller one than option 1) or
   drop ICE from expected coverage entirely (would leave the already-materialized `ICE:INDEX:DXY-USD` instrument
   permanently unfetched — an honest-absence outcome, not a bug, but worth confirming no downstream consumer
   (features/strategy) actually needs DXY).

Not resolved here — flagging for an operator/architecture decision rather than guessing at product intent, per the same
triage pattern used for the KRX gap.

## Progress log

- 2026-07-13: Filed during the pipeline_e2e_check TRADFI cluster diagnostic pass, after confirming via direct code read
  across 3 repos (instruments-service, market-tick-data-service, unified-api-contracts) — no live VM run needed, the gap
  is structural and fully visible from static code + registry inspection. Not fixed (per the operator's explicit
  instruction: this needs a real architecture decision, not a guess).
- 2026-07-13 (later same day): **RESOLVED.** Operator decision (this session): narrow ICE expected coverage to
  `ohlcv_24h` ONLY (dropping `ohlcv_1m`/`trades`/`tbbo`) AND build the Yahoo-DXY daily fetch route, mirroring the KRX
  narrowing precedent (`unified-api-contracts@a2751f36`/`@c9f32889`) exactly.
  - **unified-api-contracts@753fb81a**: `expected_coverage.py` ICE `["trades","ohlcv_1m","tbbo"]` → `["ohlcv_24h"]`;
    `VENUE_DATA_TYPE_CAPABILITIES["ICE"]` `{"ohlcv_1m":"2019-01-01"}` → `{"ohlcv_24h":"2019-01-02"}` (YAHOO_INDICES DXY
    genesis, KRX convention). Verified ICE was never in `_mvp_scope_predicate.py`'s tradfi MVP scope
    (`venues=frozenset({"CME"})`) so no MVP carve-out edit was needed, unlike KRX. New
    `TestIceExpectedCoverageNarrowedToDailyDxy` regression class + ICE dropped from the Databento-OHLCV-only-MVP
    parametrize with a dedicated `ohlcv_24h`-only pin. UAC targeted suites: 545 passed.
  - **market-tick-data-service@971bdd35**: ICE removed from `umi_tick_provider._DATABENTO_VENUES` (dead-but-reachable
    branch, zero venue=ICE Databento instruments) and routed through the new `_umi_yahoo.route_yahoo_tradfi()` (the
    FX/KRX/ICE Yahoo cluster's shared home): `ohlcv_24h` only, honest-empty for any other data_type, fetch via
    `fetch_yahoo_indices()` which resolves ticker/genesis from the UAC `YAHOO_INDICES` registry at call time (never
    hardcodes `DX-Y.NYB`) and writes `instrument_id="ICE:INDEX:DXY-USD"` — byte-identical to instruments-service's
    `_create_yahoo_index_records()` catalogue key (read-only confirmed, `adapter.py:655-695`). 8 new tests; 110 umi
    tests + a 294-test regression sweep pass; full MTDS QG green.
  - **instruments-service@c6a97052**: tradfi expected-universe golden regenerated (the 3 `(ICE, *, ohlcv_1m)` cells
    removed, 43→40 tuples) via the sanctioned regen script against the committed UAC.
  - The side-note is resolved by the same narrowing (`trades`/`tbbo` dropped).
  - **Honest residuals** (small, tracked on the parent plan): (1) first real ICE `ohlcv_24h` capture lands on the next
    TRADFI backfill/sweep run — the route is unit/registry-verified but not yet exercised by a live VM; (2)
    discovered-adjacent, NOT fixed: instruments-service `TRADFI_VENUE_INSTRUMENT_TYPES["ICE"]` lacks `"index"`, so the
    D2a "could-exist" expected-universe enumeration doesn't count ICE's DXY index cell (pre-existing, independent of
    this fix); (3) `venue_mapping.py`'s separate per-venue start-date `"ICE": "2020-01-01"` was not aligned to the
    2019-01-02 DXY genesis (different mechanism; KRX's precedent commit didn't touch its equivalent either).
- 2026-07-14: **Historical non-24h ICE residue PURGED** (operator descope ruling 2026-07-14, executing the narrowing's
  data-side counterpart). The 2026-07-13 registry narrowing left the live tradfi manifest + tick bucket carrying the
  dead granularities' history; today's operator ruling ("ICE isn't in MVP outside 24h bars from Yahoo Finance … purged
  from manifest and honest status and GCS data") authorized removing it: market-tick-data-service@fffd7f82
  `scripts/purge_tradfi_ice_non_24h_2026_07_14.py` reclassed 12,444 `captured` + 77 `attempted_failed` ICE non-24h
  manifest rows → `empty_confirmed[EXPECTED_NO_PROVIDER_COVERAGE]` (row-preserving; total 5,090,813 rows unchanged;
  snapshot `pre_ice_purge_2026_07_14.parquet`) and deleted the 10,918 non-24h ICE GCS objects (re-list verified 0
  remain). Zero `ohlcv_24h` rows/objects touched — the DXY route's first capture is still pending (honest residual (1)
  above, unchanged). The consolidator cron was paused/resumed around the write (11:06:16Z → 11:12:43Z, first post-resume
  run Completed=True 11:13:59Z).
