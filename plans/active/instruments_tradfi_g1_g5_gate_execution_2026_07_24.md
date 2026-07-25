---
doc_type: plan
title: Instruments Foundation — tradfi G1→G5 gate execution
summary:
  Split out of instruments_foundation_completeness_2026_06_24.md (2026-07-24 line-cap remediation, 4-way split,
  operator- approved). Owns tradfi's gated G1→G5 rebuild — billable-venue guard, calendar/session fail-closed, CME/ES
  ohlcv + Yahoo FX/Treasuries/DXY/KRX-KOSPI universe, `available_to` venue-truth + per-venue latest_day, VIX-15m INDEX
  retirement, G1 retirement (ICE/OPRA/CBOE pollution), G4 catalogue-as-filter — plus the tradfi-specific historical
  execution log (slot-3 G1.a-h shipped code, KRX/ICE mis-sourcing fix, CME ohlcv_1m 2020-Q1 writer fix, manifest
  stale-row cruft) and the folded-in tradfi residuals migrated from 2 archived plans. depends_on the Phase-0
  cross-cutting child for GATE 0.
status: active
nature: process
asset_group: [tradfi]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags:
  [instruments, catalogue, honest-coverage, data-correctness, backfill, tradfi, manifest, foundation, gate-execution]
related:
  [
    instruments_foundation_completeness_2026_06_24,
    instruments_foundation_phase0_cross_cutting_2026_07_24,
    instruments_cefi_g1_g5_gate_execution_2026_07_24,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /codex/02-data/instruments-foundation-and-catalogue-completeness.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: design
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 5
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [instruments_foundation_phase0_cross_cutting_2026_07_24]
source:
  [
    "plan-hygiene split of instruments_foundation_completeness_2026_06_24.md, 2026-07-24 (operator-approved, see
    plans/active/issues/plan_line_cap_remediation_2026_07_23.md row #14)",
  ]
---

# Instruments Foundation — tradfi G1→G5 gate execution

**Split provenance (2026-07-24):** this plan was extracted from
[`instruments_foundation_completeness_2026_06_24.md`](instruments_foundation_completeness_2026_06_24.md) (the umbrella)
as part of the operator-approved plan-line-cap remediation
(`plans/active/issues/plan_line_cap_remediation_2026_07_23.md`, row #14 — 4-way split). **`depends_on`
[`instruments_foundation_phase0_cross_cutting_2026_07_24.md`](instruments_foundation_phase0_cross_cutting_2026_07_24.md)
for GATE 0** — the cross-cutting prerequisites (observability, Honest-Coverage v2, canonical-form single-SoT migration)
that block G2. The umbrella (`instruments_foundation_completeness_2026_06_24.md`) stays the process SSOT + rolling
status index across all 4 children (this one, Phase-0, cefi, and the defi/sports plans it already delegates to).

**Codex SSOT (the standard this plan executes):** `/codex/02-data/instruments-foundation-and-catalogue-completeness.md`.

---

## Gated Phase 2 — tradfi (same G0→G5 as cefi/defi)

- [ ] [INFRA] P1. **tradfi** — same gates; Databento universe (GLBX/DBEQ/XCBF) + Yahoo (KRX/FX). ("tradfi perps" =
      Binance single-stocks/commodities are **cefi**.) DeFi-distinct tradfi work (§7): **billable-venue guard** —
      enumerated venues == subscribed allowlist (ICE non-billable, 8,856→1; §7.1); **fail-closed per-venue calendars +
      sessions** (KRX in NO calendar SSOT → 24/7 default mis-handles Seollal/Chuseok; FX is the declared 24/7 exception;
      §7.2); **`available_to` per-venue + trading-day-aware** (global-`latest_day` falsely delists lagging KRX; §7.3);
      **equities pre-2023-04-15 silently absent**; **depth oracle** (NASDAQ ~41 / NYSE ~224 shallow); verify the tradfi
      daily-capture trigger isn't PAUSED. Baseline §9.
  - **Already-fixed G1 code (this session, IS `50bf1c8`, QG-green, 7/7 venues now write):** KRX→databento routing
    (`CANONICAL_VENUE_TO_ADAPTER`) + the `AssetClass("cefi")` crash on NASDAQ/NYSE equities (`_resolve_asset_group`
    guarded so domain values fall through to the dataset-default EQUITY). **Remaining G1 refinements (NOT yet done):**
    (i) the cefi-domain equity-perp singles (NVDA/MSFT/AAPL…, `DatabentoInstrumentDef.asset_group="cefi"`) currently
    resolve to EQUITY and **stay in the tradfi pipeline** — per the registry-comment intent ("keeps them out of the
    tradfi data pipeline") they must be **EXCLUDED** from the tradfi adapter (they belong to cefi), not just un-crashed;
    (ii) `_DATASET_TO_asset_group["XCBF.PITCH"]=EQUITY` + XCBF absent from `_FUTURES_DATASETS` — VX are FUTURE (the
    `instrument_type` lands FUTURE, but the asset-class map is wrong → fix to FUTURE/COMMODITY).

---

## Expanded scope — CME + ES ohlcv + Yahoo FX/Treasuries/DXY (operator 2026-06-26, moved from the umbrella Near-term-target section)

#### Expanded scope (operator 2026-06-26): tradfi CME + ES ohlcv + Yahoo FX/Treasuries/DXY

- [x] [INFRA] P0. ✅ **tradfi instrument-definition backfill LAUNCHED** — `launch-tradfi-is-defs-sharded.sh` 9-shard
      fleet RUNNING (`instr-backfill-tradfi-{cboe,nasdaq,…}-*`), covers CME + all tradfi venue defs (current: 14,192
      captured, CME 3,532 rows 2020→06-24).
- [ ] [DATA] P0. **ES CME futures ohlcv 1s+1m — IN FLIGHT** (`tradfi-bf-cme-ohlcv-1m-es-{2020,2025,2026}` RUNNING;
      launcher lib defaults to BOTH `ohlcv_1m;ohlcv_1s`). REMAINING: confirm ALL years 2020-2026 covered (only
      2020/25/26 VMs seen — verify 2021-24 done or launch), manifest-verify per-year. Billing-fail-closed (Databento
      PAYG, shared singleton lock).
- [ ] [DATA] P0. **ES CME OPTIONS (ES_OPT) ohlcv 1s+1m — NOT yet launched** (singleton Databento lock held by the
      futures fleet). Launch `launch-tradfi-bf-cme-ohlcv-1m.sh --only-root ES_OPT` once the lock frees (11-cluster
      ES_OPT_PARENTS set).
- [x] [DATA] P1. ✅ **Yahoo FX / Treasuries / DXY instruments — universe COMPLETE.** Treasuries (all 5 tenors:
      US3M/US2Y/US5Y/US10Y/US30Y → ^IRX/2YY=F/^FVX/^TNX/^TYX) + DXY (DX-Y.NYB) were ALREADY enumerated in UAC
      `YAHOO_INDICES`. Gap was FX (only KRW/USD) → added the **10 G10 FX majors** (EUR/GBP/JPY/AUD/CAD/CHF/NZD crosses +
      USD/MXN). Shipped `UAC@526f3c83` + `instruments-service@97cdf92`, QG-green, runtime-verified (16 records
      enumerate). FX ohlcv backfill running (`tradfi-bf-fx-ohlcv-24h-2026`); existing FX/DXY/treasury defs captured by
      the running tradfi backfill; the NEW G10 FX majors capture once the image carries UAC@526f3c83.
- NEXT: monitor all backfill fleets to completion (climbing metric = captured days/cells); launch ES_OPT when lock
  frees; once instrument backfills done + image carries f739a41 → regen cefi+defi catalogues + verify honest coverage;
  the all-AG producer crash (sports/tradfi/pred have no daily producer) stays a tracked finding.

#### Checkpoint 12:40 — ALL-5-AG foundation drive (operator: complete instruments+catalogue+coverage+MTDS for every AG)

- **Daily-producer truth (live GCP):** cefi has 06:00 job ✅; defi = repurposed 00:00 job ✅; **tradfi/sports/prediction
  have NO prod daily producer** (sports only `uts-dev-…-sports-fixtures`). The durable fix = the all-AG crash fix (agent
  a81f8) → restore the 00:00 `uts-prod-instruments-service-t1-recon` to no-`--asset-group` (covers SPORTS/DEFI/TRADFI;
  PREDICTION is separate per `is_all` — agent to confirm). Until then today's capture is covered by the backfill fleets.
- **IMAGE BUILD is MANUAL + STALE** (`image:latest` last built 2026-06-23 via `instruments-service/cloudbuild.yaml`, NO
  auto-trigger on main). f739a41 reached main 12:33 but the cloud jobs still run 06-23 code. **DO NOT build yet:** the
  IS working tree is dirty with two agents' WIP (Yahoo universe a80ad + all-AG crash fix a81f8). **SEQUENCE: agents land
  their IS code → backfills done → build the image ONCE (`gcloud builds submit --config cloudbuild.yaml`) from a CLEAN
  f739a41+ tree → redeploy cloud producer/catalogue jobs → re-run producers (seed EU) → regen catalogues → verify.** Do
  NOT run producer/catalogue LOCALLY from the current dirty tree either.
- **In flight:** cefi+defi instrument backfills (verified writing: defi wrote 6285 rows/52 venues for 05-19, honest
  attempted_failed for 2 dead venues; cefi gap days 06-22/23 now present). tradfi IS-defs 9-shard fleet. tradfi CME
  ohlcv ES 1s+1m (es-2020/25/26) + CL/GC/HG/NG/NQ/SI + FX/NASDAQ/NYSE. 3 agents: Yahoo (a80ad), all-AG-crash (a81f8),
  sports+prediction backfills (a8c9).
- **Loop drivers:** watchdog b9ermg8qr (Databento lock → ES_OPT) + the 3 agents' completion notifications.

---

## Historical progress log (tradfi track, moved verbatim from the umbrella 2026-07-24)

> Cross-referenced with the interleaved cefi narrative from the same sessions — see
> [`instruments_cefi_g1_g5_gate_execution_2026_07_24.md`](instruments_cefi_g1_g5_gate_execution_2026_07_24.md)`s
> Historical progress log section for the cefi side of the same 2026-06-25 → 2026-06-27 sessions.

- 2026-06-24 — **tradfi audit + the foundation-first PIVOT (this session).** Started as the KRX/equities OPS pass; the
  operator's "how do we know instruments is honestly at coverage" probe surfaced the foundation gaps → reset to
  audit-first. **Shipped G1 code:** KRX routing + the cefi-`AssetClass` crash (IS `50bf1c8`, 7/7 venues write). **Audit
  findings** (now §9 + the tradfi todos above): ICE non-billable yet enumerated (8,856→1); CBOE pollution (91 SPOT_PAIR
  - 5 un-deleted VIX-INDEX); KRX 96% silently absent + no Korea calendar; `available_to` false-delistings (global
    `latest_day`); equities pre-2023 absent; shallow NASDAQ/NYSE. **PAUSED everything** (operator "no point wasting time
    and money"): catalogue-regen execution **cancelled** (it would have baked false KRX delistings, §7.3),
    `uts-prod-tradfi-wave-launcher-cron` **paused**, the 18 `tradfi-bf` OHLCV VMs **deleted**; live producer +
    non-tradfi VMs left. **Nothing builds downstream until G1 fixes land + GATE-0/G1 sign-off.** (Separate + still LIVE:
    the tradfi market-data EU-drain fix — massive purged, EU collapsed 1.08M→1,349 MVP, durable — not part of this
    foundation gate.)

- 2026-06-25 — **TRADFI track dispatched directly (operator), slot-3.** Sequencing: tradfi G1→G5 driven NOW (ahead of
  cefi-first ordering — the documented intent for this dispatch); reversible work driven to done, expensive/irreversible
  (G2 fleet launch, real-GCS purge) HARD-PAUSE for operator confirm. Composes with the Phase-0 canonical-form single-SoT
  migration item (above) — tradfi is one AG of it.
  - **Read-only audit of `prod/catalog.parquet` (814,011 rows) + `by_date/` + code — full tradfi pollutant inventory,
    root-caused, each fix STOPS it at source; stale rows = retirement (operator-confirm GCS purge):** daily-capture is
    BROKEN (`by_date/day=2026-06-24/` = ONLY `venue=CME`, 1 of 7 venues). Pollutants (cumulative catalogue counts): ICE
    COMBO+FUTURE BRN-Brent **16,157** (stale avail_to=2023-12-21; IFEU/IFUS non-billable maps) · ICE INDEX DXY **1** ·
    CBOE OPTION OPRA-SPX `O:SPX…` **33,258** (stale; OPRA non-billable) · CBOE SPOT_PAIR VX-spreads
    `VX/F1:1:S - VX/G1:1:B` **4,216** (ACTIVE; XCBF class-S→SPOT_PAIR) · CBOE INDEX **6** (^VIX, I:VIX,
    ^IRX/^FVX/^TNX/^TYX) · NASDAQ/NYSE SPOT_PAIR **102/216** (ACTIVE; DBEQ class-S equity-spot mis-typed) · cefi-singles
    in EQUITY (NVDA/MSFT/AAPL/CRCL/INTC/GOOGL/AMD/ TSLA/AMZN/META/HOOD/BABA, mvp=True; 50bf1c8 fixed only the crash NOT
    exclusion) · VX FUTURE asset_group=EQUITY **82** (should be COMMODITY) · `available_to`
    global-`latest_day`/last-seen bug (all →2026-06-23; VX/F7 falsely active) · MVP broken (895/814,011 True; VX futures
    all False) · KRX/FX in NO calendar SSOT (`is_non_trading_day` fails-OPEN → silent 24/7 → Korean holidays
    mishandled).
  - **MACRO-INDEX / CURRENCY decision (operator clarifications 2026-06-25):** (1) "DXY canonical along with KRWUSD as
    the currencies daily from Yahoo, **not one-offs**" → **KEEP + canonicalise** DXY (re-home venue ICE→**FX**,
    asset_group=fx)
    - KRWUSD (already FX) + the treasury-yield rate indices ^IRX/^FVX/^TNX/^TYX (Yahoo daily macro rates, venue=CBOE
      issuer-correct, asset_group=fixed_income). Yahoo daily series have NO billing issue → they stay (the §7.1
      yahoo-allowlist generalises beyond `{KRX,FX}` to the canonical Yahoo daily currency/macro series — codex §7.1 to
      update). (2) **REMOVE only VIX cash** (^VIX Yahoo + I:VIX OPRA) — redundant, VX futures cover VIX-15m
      (`is_vix_15m_gap_date` always False). (3) "**ICE is databento billing-blocked → purge EVERYWHERE**" → the ICE
      Databento BRN-Brent (16,158) purged across by_date + manifest + catalogue + surfaces; DXY moves off ICE so ICE
      venue is GONE. (This REVERSES the earlier "drop all YAHOO_INDICES" reading — DXY/treasuries/KRWUSD are
      canonical-keep.) DEPTH todo: expand the Yahoo currencies universe beyond DXY/KRWUSD ("not just one-offs").
  - **TRADFI G1 code checklist (slot-3; tradfi-databento files = NON-colliding with the cefi agent; the AG-agnostic
    `build_instrument_catalogue.py` §7.3 `available_to`/per-venue-`latest_day` fix is the cefi agent's item 4 — SHARED,
    coordinate, one fix covers both AGs):**
    - [x] ✅ [SCRIPT] P0. **G1.a billable-venue guard (§7.1)** — IS@92084d5c QG-green. Stripped non-billable datasets
          (IFEU/IFUS/OPRA/XNAS.ITCH/XNAS.BASIC/XNYS.PILLAR) from `_DATASET_TO_VENUE`/`_DATASET_TO_asset_group`/
          `_FUTURES_DATASETS` (now only the 3 billable) + exclusion-marker comments; the
          `assert_databento_request_allowed` fetch gate was already present (adapter.py L424). Regression:
          `test_g1a_billable_dataset_maps_only_three`. **Follow-up todos filed below**: router.py + massive.py still
          reference non-billable datasets (the latter is the actual OPRA/I:VIX pollution source).
    - [x] ✅ [SCRIPT] P0. **G1.b exclude cefi-domain equity singles** — IS@92084d5c. `get_instruments` filters curated
          defs to `asset_group ∈ frozenset(AssetClass)` → the 12 cefi-singles (asset_group="cefi") not enumerated as
          tradfi; SP500-overlap tickers still enter via the SP500 path. Regression:
          `test_g1b_cefi_singles_excluded_from_tradfi_enumeration`.
    - [x] ✅ [SCRIPT] P0. **G1.c XCBF.PITCH = COMMODITY + outright-only** — UAC@256dfc4a (`_CFE_FUTURES` VX.FUT
          "equity"→"commodity" + UAC regression test) + IS@92084d5c (`_DATASET_TO_asset_group["XCBF.PITCH"]`→COMMODITY;
          drop XCBF class-S VX spreads in `_parse_row_to_record`). Regression:
          `test_g1c_xcbf_outright_only_drops_vx_spreads` (IS) + `test_vx_future_asset_group_is_commodity` (UAC). The
          IS↔UAC test coupling was DECOUPLED (UAC content asserted in UAC's suite, not IS) to avoid false-fails under
          UAC promotion lag.
    - [x] ✅ [SCRIPT] P0. **G1.d DBEQ.BASIC class-S → EQUITY** — IS@92084d5c. Equity-spot rows no longer mis-typed
          SPOT_PAIR. Regression: `test_g1d_dbeq_class_s_is_equity_not_spot_pair`.
    - [x] ✅ [SCRIPT] P0. **G1.e calendars+sessions FAIL-CLOSED** — IS@92084d5c. Declared KRX (XKRX cal + KST hours) +
          FX (24/7 explicit) + `is_non_trading_day` raises `UndeclaredTradfiVenueError` for an undeclared tradfi venue
          (was silent 24/7). ICE re-DECLARED in sessions pending the whole-venue retirement (so no spurious raise
          mid-transition; curated enumeration already drops ICE instruments). Regression:
          `test_g1e_krx_uses_korean_calendar` + `test_g1e_fx_is_24_7` + `test_g1e_undeclared_venue_fail_closed`; updated
          the prior fail-open test.
    - [x] ✅ [SCRIPT] P0. **G1.f macro/currency canonicalise** — PARTIAL (operator-reshaped 2026-06-25): VIX cash-index
          REMOVED from UAC `YAHOO_INDICES` ✅ (uac@43db03f8 + databento VIX-USD tests IS@fb13355e); DXY KEEPS venue=ICE
          ✅ (operator REVERSED the planned ICE→FX — DXY IS the ICE/NYBOT US Dollar Index, Yahoo-sourced, the ONLY
          retained ICE exception, documented in-registry; ICE→FX key-migration CANCELLED). REMAINING split into G1.f.2
          (VIX-15m index removal) + G1.f.3 (treasuries actually reach the catalogue) below — both DONE, nothing left
          open under G1.f itself.
    - [x] ✅ [SCRIPT] P1. **G1.f.2 — retire the VIX-15m INDEX (superseded by VX futures 1s OHLCV; operator 2026-06-25)**
          — remove `CBOE:INDEX:VIX-USD` ohlcv_15m as a distinct index. 3-repo, consumers-first. VX.FUT futures
          (`CBOE:FUTURE:VX`, XCBF.PITCH ohlcv-1s/1m, aggregated downstream) is KEPT — it IS the VIX-vol source;
          features=0 consumers of the VIX-15m index. **STAGE 1 — MTDS DONE ✅ mtds@833fa14c (QG-green):** removed
          `fetch_yahoo_vix_15m` (`_umi_yahoo.py`) + the CBOE+ohlcv_15m→Yahoo routing (`umi_tick_provider.py`) +
          `download_vix_15m` + the `VIX_INDEX_INSTRUMENT` special-case in `YahooFinanceAdapter.fetch_instruments` (→
          `[]`). A direct `(CBOE, ohlcv_15m)` fetch now returns empty (no Yahoo, no error) — VERIFIED. Tests: deleted
          `test_vix_15m_source_layering.py`; dropped the obsolete Yahoo-routing tests; `CBOE+ohlcv_15m` asserts
          empty-no-Yahoo. **STAGE 2 — MDPS DONE ✅ mdps@79fbb16:** deleted `_record_vix_gap_empty` + its
          `orchestration_service.py` caller block + the unused VIX UAC imports (`VIX_INSTRUMENT_KEY`,
          `is_vix_15m_gap_date`, `PipelineMode`, `MarketAssetGroup`) + module docstring cleanup. Deleted
          `TestRecordVixGapEmptyPipelineMode` test class. **STAGE 3 — UAC DONE ✅ uac@599acf93 (QG-green, breaking):**
          removed `get_vix_15m_source` / `is_vix_15m_gap_date` / `get_yahoo_vix_15m_start` / `VIX_15M_SOURCE_HISTORY` /
          `YAHOO_VIX_15M_WINDOW_DAYS` / `DATABENTO_VX_FUTURES_FIRST_DATE` / `VIX_PROD_BUCKET` / `VIX_DEV_BUCKET` /
          `VIX_INSTRUMENT_KEY` / `VIX_DATA_TYPE` / `VIX_TYPE_PREFIX` from `data_source_continuity.py`; removed
          `VIX_INDEX_INSTRUMENT` + `VIX_INSTRUMENT` from `tradfi_symbology.py`; removed VIX-USD entry from
          `TRADFI_INSTRUMENTS`/`TRADFI_DATA_BINDINGS`; removed all 13 VIX symbols from `registry/__init__.py`
          re-exports. Also fixed pre-existing backward-compat docstring in `events/__init__.py` (QG sentinel unblock).
          Tests updated (6 files). Staged → LDR; Tier-C drain ≤15min → staging; detect_breaking_change.py fires SIT
          (~30min). **NB (data-correctness, verify at G2): VIX-15m now depends on `CBOE:FUTURE:VX` being captured at
          ohlcv-1s/1m + the downstream 1s/1m→15m aggregation — confirm that path is wired so removing the Yahoo fetch
          leaves no silent 15m gap.** Provenance: operator 2026-06-25.
    - [x] ✅ [SCRIPT] P0. **G1.f.3 — CBOE treasury-yield INDICES into the daily instrument definitions (operator
          2026-06-25)** — DONE uac@0b8a775c + IS@2536d9b4. **US2Y ADDED** to UAC `YAHOO_INDICES` as
          `CBOE:INDEX:US2Y-USD` via Yahoo `2YY=F` (operator: "use Yahoo, don't care which ticker"; the only Yahoo 2Y is
          the 2YY=F future — no ^-series cash 2Y exists) + the shared treasury source-resolver + genesis 2018-08-13 (CME
          yield-futures launch, best-estimate — VERIFY at backfill; honest-absence surfaces freshness since 2YY=F was
          noted stale). Target curve = **3M / 2Y / 5Y / 10Y** (operator) + 30Y KEPT (the features
          `treasury_yields_calculator` depends on it; operator curve is a subset). US5Y/US10Y/US3M/US30Y already in the
          registry. Tests updated (UAC `_TREASURY_TENORS` + resolver-coverage gate; IS `_create_yahoo_index_records`
          loop). **Catalogue population is OPERATIONAL, not a code gap**: CBOE IS in `_TRADFI_VENUES`
          (venue_core.py:138) + `build_instrument_catalogue.py` rolls up from the written
          `instrument_availability/venue=CBOE/` parquets WITHOUT filtering INDEX — so the treasuries reach the catalogue
          once a CBOE instruments-backfill writes the `CBOE:INDEX:USxY-USD` records (rides **G2**). The operator's
          "never in the catalogue" = no CBOE-index backfill has run since the yahoo-index path landed, not a code
          exclusion. **FOLLOW-UP (features): `treasury_yields_calculator.py` builds the curve from 5Y/10Y/30Y — wiring
          it to consume the new 2Y/3M points is a features-track todo (not blocking the instrument-definition add).**
          Provenance: operator 2026-06-25.
    - [ ] [SCRIPT] P1. **G1.g MVP tags on the tradfi MVP universe** (VX futures + basis tickers).
    - [x] ✅ [SCRIPT] P0. **G1.h §7.3 `available_to` venue-truth + per-venue `latest_day`** — SHIPPED
          instruments-service@8261203 (the SHARED `build_instrument_catalogue.py` fix; ONE edit covers tradfi G1.h AND
          cefi G1.1 — checked git log 665966b clean before+after, no double-edit). `build_catalogue_dataframe` now uses
          a PER-VENUE thin-day-aware last-full-trading-day (`_venue_last_full_day`) instead of the global `latest_day`
          (so a lagging KRX/divergent-calendar venue is no longer falsely delisted off a CME-fuller day) + venue-truth
          `expiry`/`delisted_at` for dated instruments. QG-green, 54 roll-up tests pass. NOTE: tradfi prod-regen verify
          rides tradfi G3 (catalogue-regen-tradfi is operator-PAUSED pending tradfi G1 retirement/sign-off — do NOT
          regen it before the §9 retirement purge or it re-bakes the ICE/OPRA pollutants).
    - [ ] [INFRA] P0. **G1 retirement (§8, 4 legs) — OPERATOR-CONFIRM before purge** — ICE (whole venue, 16,158) · CBOE
          OPRA OPTION (33,258) · CBOE VX-spread SPOT_PAIR (4,216) · VIX-cash INDEX (^VIX+I:VIX) · NASDAQ/NYSE mis-class
          SPOT_PAIR (318) · cefi-singles. Pause consolidator→snapshot→filter→resume; verify gone all 4 legs.
    - [x] ✅ [SCRIPT] P1. **G1.a.2 §7.1 follow-up — massive.py (the OPRA/I:VIX pollution source)** — DONE
          instruments-service@1198549 (LDR). massive KEPT as the tradfi FALLBACK (operator 2026-06-25); endpoint
          `https://api.polygon.io` VERIFIED correct (Polygon.io→Massive 2025-10-30 rebrand kept the host). Removed the
          two pollution-fetch paths the databento §7.1 guard (G1.a) does not touch: `_fetch_indices` (CBOE cash-index /
          VIX-cash over YAHOO*INDICES) + `_fetch_index_options` (OPRA SPX/VIX cash-index OPTION chains) — both retired
          (VX vol rides Databento XCBF.PITCH) — plus ICE from `_FUTURES_VENUES` (ICE \_commodity* FUTURES = Brent/Gasoil
          via IFEU/IFUS are Databento-billing-blocked, no canonical source — that subscription ask stands. NB ICE _DXY_
          index DOES have a canonical source now: Yahoo `DX-Y.NYB`, shipped `uac@5480f5d5`, 2026-06-27 — only the
          futures are blocked). massive now fetches NASDAQ/NYSE equities + FX + CME futures ONLY, ending CBOE-OPTION
          (33,258) / VIX-cash / ICE-futures catalogue pollution at source. Regression:
          `test_cboe_and_ice_filters_yield_no_pollution` (CBOE+ICE venue filters yield zero records); dead index/option
          fixtures + coverage-boost tests removed. QG-green, 58 tests pass, basedpyright 0. NOTE: this is the SOURCE fix
          (stop writing pollution); the GCS PURGE of the already-written CBOE-OPTION/VIX-cash/ICE parquets stays in the
          operator-gated G1 retirement (§9). Actual method names were `_fetch_indices`/`_fetch_index_options` (plan's
          earlier `_fetch_opra_options`/ `_fetch_index_universe` were guesses). Provenance: slot-3 G1.a diagnosis
          2026-06-25.
    - [x] ✅ [SCRIPT] P2. **G1.a.3 §7.1 follow-up — router.py dead non-billable dataset config** — DONE
          instruments-service@5ef1958f (LDR). DELETED (not realigned) the whole dead path: the databento adapter
          resolves each instrument's dataset PER-INSTRUMENT from the curated `TRADFI_DATABENTO_INSTRUMENTS` registry
          (§7.1 billable allowlist DBEQ.BASIC / GLBX.MDP3 / XCBF.PITCH), so the router's `_DATABENTO_VENUE_DATASETS`
          venue→dataset map (nasdaq/nyse/apple/binance→XNAS.ITCH/XNYS.PILLAR + cboe_options→OPRA.PILLAR, all
          non-billable) + `_resolve_databento_datasets` resolver + `_route_databento`'s resolve-and-pass + the unused
          `datasets=` ctor param (all callers kwargs-only) were 100% dead. Removed all four + the misleading docstring
          annotations. Routing behaviour unchanged (databento still → DatabentoReferenceDataAdapter); only the dead
          non-billable annotation is gone. Tests: removed `TestResolveDatabentoDatasetsRouter` + dead import;
          `test_router` routing assertions unchanged (still pass — they assert isinstance, not datasets). QG-green, 68
          tests pass, basedpyright 0. Provenance: slot-3 G1.a diagnosis 2026-06-25.

- 2026-06-25 — **TRADFI G1.a–e SHIPPED + tradfi compute fully stopped (slot-3).** **Code (QG-green, both repos):**
  UAC@256dfc4a (`_CFE_FUTURES` VX.FUT "equity"→"commodity" + UAC regression test) + instruments-service@92084d5c
  (symbology billable-venue map cleanup → only the 3 billable datasets; `get_instruments` excludes cefi-domain singles;
  XCBF class-S VX spreads dropped + XCBF→COMMODITY; DBEQ class-S→EQUITY; KRX XKRX-calendar + FX-24/7 + fail-closed
  `UndeclaredTradfiVenueError`; ICE re-declared in sessions pending the whole-venue retirement; **8 regression tests**
  in `test_databento_tardis_adapter.py::TestTradfiG1FoundationRegression` + the IS↔UAC VX assertion DECOUPLED into UAC's
  suite to avoid UAC-promotion-lag false-fails). These STOP the active catalogue pollution at source (4,216 VX-spread
  SPOT_PAIR + 318 equity-spot mis-class + cefi-singles + VX=EQUITY); stale rows (ICE 16,158 / OPRA 33,258 / VIX-cash)
  are the operator-gated retirement. **Findings filed** (above): OPRA/I:VIX pollution actually comes from massive.py
  (G1.a.2); router.py dead non-billable config (G1.a.3). **Awaiting G1 sign-off.**
  - **Tradfi compute STOPPED (operator P0 2026-06-25 — "another track relaunched the tradfi-bf fleet overnight despite
    the pause"):** killed the 18 RUNNING `tradfi-bf-*` OHLCV backfills (the ~6 KRX ones had self-completed); deleted the
    `tradfi-fwd-daily-cron` launcher host (was a 06:00 forward-poll launcher — same gate-jump class);
    `uts-prod-tradfi- wave-launcher-cron` + `instruments-daily-backfill` schedulers confirmed PAUSED (the automated
    relaunch path — it never actually fired; the overnight launch was external/manual). Also paused
    **`lifecycle-catalogue-regen-tradfi-daily` (01:00)** + **`instrument-catalogue-regen-nightly` (02:00)** at 01:38 UTC
    — protective, before the 02:00 fire would re-bake the §7.3 false-delistings into the tradfi catalogue SSOT. **Left
    running** (per dispatch "leave the live producer"): `mtds-live-tradfi-cme-trades` (live `databento` WS) — flagged
    for the operator. **Cross-AG flag:** the other AGs' `lifecycle-catalogue-regen-{cefi,defi,sports,prediction}`
    (01:00) + `catalogue-regen-nightly` (04:30) are still ENABLED (cefi has the same §7.3 bug) — operator to decide a
    fleet-wide catalogue-regen pause.
  - **G1.f / G1.h / retirement sequencing:** G1.f (macro/currency: VIX-cash removal + DXY venue ICE→FX) is a canonical
    key-migration (UAC `YAHOO_INDICES` + `data_source_continuity._SOURCE_RESOLVERS`
    `ICE:INDEX:DXY-USD`→`FX:INDEX:DXY-USD`
    - EU enumerator + massive + the existing DXY market-data GCS re-key) → done COORDINATED with the operator-gated
      retirement/canonical-migration (a standalone code change would create the exact dual-SoT the operator banned).
      Operator clarified DXY+KRWUSD+treasuries are canonical Yahoo-daily KEEP (not one-offs); only VIX-cash is removed.
      G1.h §7.3 `available_to`/per-venue-`latest_day` is the cefi agent's item-4 (AG-agnostic
      `build_instrument_catalogue.py`) — coordinate, one fix both AGs.

- 2026-06-25 — **G4 catalogue-as-filter BUG fixed (tradfi) — market-tick-data-service@dda5040d (QG-green).**
  Read-verified the MTDS catalogue-as-filter and found a real bug: `TradFiCatalogReader` probed a DEAD prefix
  `reference_data/instruments/asset_group=tradfi/` (absent in the bucket — only `prod/catalog.parquet` exists) AND read
  the legacy `available_*_datetime` column names (the roll-up uses un-suffixed `available_from`/`available_to`), so it
  ALWAYS returned an empty iterator → the MTDS sentinel fan-out silently fell back to the UAC ("BTC"/"ETH") MVP seed and
  never filtered the real tradfi catalogue. Fixed: probe `{prod,staging,dev}/catalog.parquet` + canonical
  `available_from`/`available_to` (mirrors the `CeFiCatalogReader` BUG #4 fix, 2026-06-22) + 2 regression tests. **G4
  mechanism is now functional** (active-on-date window filter + FUTURE/OPTION root dedup); the gate's DoD (MTDS attempts
  == catalogue-active-for-day) becomes verifiable once the catalogue is clean (post-retirement + §7.3). NB the
  `catalog_list_instruments(ag)` sentinel path (sentinels.py) is a SEPARATE Tier-1 reader from this Tier-3 chain reader.

- 2026-06-26 — **G1.f.2 (VIX-15m INDEX retirement) COMPLETE — all 3 stages shipped.** MDPS mdps@79fbb16 (Stage 2:
  `_record_vix_gap_empty` deleted + test class); UAC uac@599acf93 (Stage 3 breaking: 13 VIX public symbols removed +
  backward-compat docstring fix that unblocked QG sentinel). Plan flip committed pm@7f5932caf. CI fires via Tier-C drain
  (UAC breaking → detect_breaking_change.py → SIT ~30min). **Data-correctness finding (P2, zero live impact):** two
  stale capability registrations remain post-retirement — `expected_coverage.py` CBOE `ohlcv_15m` entry + a
  `DataTypeCapability(venue="CBOE", data_type="ohlcv_15m", instrument_type="")` entry in `data_type_capability.py` both
  reference the now-deleted VIX cash INDEX. Zero downstream consumers of CBOE ohlcv_15m (features=0). Filed as a plan
  todo under G1.f.2 post-retirement cleanup above. Notify operator if a 15m VX-futures consumer is added before cleanup.

---

## Deferred work after 2026-06-26

| #   | Item                                                                                                                                                                                                                      | Repo       | Priority | Blocked on                   |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | -------- | ---------------------------- |
| 1   | Clean stale CBOE ohlcv_15m capability entries (expected_coverage.py + data_type_capability.py + MDPS adapter docstring) post VIX-INDEX retirement                                                                         | UAC + MDPS | P2       | Nothing (no live consumers)  |
| 2   | Verify UAC uac@599acf93 SIT passes (~30min Tier-C drain → staging → quality-gates-v2)                                                                                                                                     | UAC        | P1       | CI auto                      |
| 3   | ~~G1.f (partial — DXY key migration ICE→FX)~~ — RESOLVED 2026-06-25: operator REVERSED the planned migration, DXY KEEPS venue=ICE, ICE→FX key-migration CANCELLED outright (see G1.f above). No decision remains pending. | UAC + IS   | —        | Resolved (no longer blocked) |
| 4   | G1.g MVP tags; G1.a.2 massive.py §7.1; G1.a.3 router.py dead config                                                                                                                                                       | IS + MTDS  | P1/P2    | None                         |

---

## Folded-in tradfi residuals (I-1 consolidation 2026-06-26 — tradfi portion; cross-cutting portion moved to the Phase-0 child)

> Continuation of the `proper_instrument_catalogue_lifecycle_rollup_2026_06_04` (archived) folded-in items — the
> cross-cutting items from that same archived plan moved to the Phase-0 child.

- [ ] [DATA] P1. **FINDING — IS `by_date` capture frozen ~2026-05-21 fleet-wide; tradfi degraded from ~2026-05-04.**
      Applied catalogues are honest snapshots-as-of-freeze (cefi usable; tradfi marks ~651K "delisted" → liveness not
      trustworthy until tradfi capture fixed + catalogue regenerated). Diagnose the tradfi 16K→2/day anomaly (slot-6 /
      tradfi vertical) + add a coverage-horizon staleness check to producer/audit. (MIGRATED FROM: same.)
- [ ] [DATA] P1. **FINDING — ICE futures + CME futures-options not on Massive → BLOCKED-CREDENTIALS.** Massive covers
      CME-group only, no options-on-futures product; old databento ~16-18K/day was CME ES futures-options. **Operator
      ask**: an ICE-futures + CME-futures-options reference source, or unblock Databento billing. Repo:
      instruments-service. assigned_vm: vm-tradfi. (MIGRATED FROM: same.)
- [ ] [DATA] P1. **tradfi CME futures reference gap from 2026-06-08** — Massive `/futures/vX/{products,contracts}` 404
      (worked 2026-06-07). `BLOCKED-UPSTREAM-OUTAGE`: re-probe, on restore re-run
      `--asset-group TRADFI --source massive` for missing days so `venue=CME` refills, then regen the tradfi catalogue.
      Repo: instruments-service. (MIGRATED FROM: same.)
- [ ] [CODE] P2. **FINDING — MTDS Massive connector uses the wrong futures endpoint.**
      `massive_tradfi_rest_connector.py` maps futures→`/v3/reference/futures/contracts` (404s); working path is
      `/futures/vX/contracts` (+ `/futures/vX/products` for contract size). Repo: market-tick-data-service. assigned_vm:
      vm-tradfi. (MIGRATED FROM: same.)

### From `tradfi_databento_subscription_universe_lockdown_2026_06_18` (archived; 26/33 done — universe lockdown + billing guards SHIPPED)

- [ ] [IS] P1. **Backfill the IS CME (GLBX.MDP3) catalog for 2019-01-01→present** (the IS-side universe producer — owned
      HERE) so the tradfi OHLCV download has a per-date instrument universe (definition schema is L0/free, 16y). CME
      futures expire daily — never copy definitions between dates. Repo: instruments-service. **The downstream MTDS
      market-data download is M-1's** (`path_to_100pct_backfill_mtds_is`); the CME EC\* event-contract slice is the
      tradfi-domain plan-of-record `tradfi_cme_event_contract_backfill_2026_06_20` (tradfi_master) — coordinate, don't
      duplicate. (MIGRATED FROM: `tradfi_databento_subscription_universe_lockdown_2026_06_18`.)
- [ ] [SCRIPT] P1. **(→ M-1) MTDS tradfi market-data backfill across all 3 datasets** (GLBX.MDP3 + DBEQ.BASIC + CFE) ×
      the L0 16y window, sharded; verify per-dataset manifest coverage (captured + honest-absence); confirm equity cells
      re-routed to DBEQ.BASIC and CFE/VX cells exist. **EXECUTE UNDER M-1** (`path_to_100pct_backfill_mtds_is`, which
      owns MTDS market-data backfill-to-100% and already ran the Databento OHLCV pass 2026-06-19) — gated on the IS CME
      catalog backfill above. Listed here only as the cross-link. (MIGRATED FROM: same.)
- [ ] [SCRIPT] P1. **instruments-service — post tradfi-v9 close-out, tombstone dropped Databento instruments.** Run
      `reconcile_manifest_after_entity_change.py --mode remove --asset-group tradfi` for the dropped ICE roots
      (BRN/G/DX, softs CT/CC/KC/SB/OJ; datasets IFEU.IMPACT/IFUS.IMPACT) → `REMOVED_ENTITY_TOMBSTONE` (dry-run → audit
      CSV → apply), then a phantom sweep. Repo: instruments-service. (MIGRATED FROM: same.)
- [ ] [UAC] P1. **Unit tests for `databento_subscription_allowlist`** (allowed/blocked dataset, banned OHLCV schema,
      per-level lookback floor boundaries, batch ban, break-glass, enum-repr normalization). Repo:
      unified-api-contracts. (MIGRATED FROM: same.)
- [ ] [PM] P1. **QG grep-ratchet** — no raw `batch.submit_job` outside the guarded `submit_batch_job`; no off-allowlist
      dataset string literal in tradfi fetch paths. Wire into market-tick-data-service `quality-gates.sh`. Repo: PM +
      market-tick-data-service. (MIGRATED FROM: same.)
- [ ] [SCRIPT] P2. **instruments-service — re-fetch a sample of old tradfi dates whose `instrument_count` changed**
      (equity ETFs XNAS.ITCH→DBEQ.BASIC; CME cells now include EC\* event contracts) to confirm the new parquet's
      instrument set matches the new universe; enumerate the un-refetched range. Repo: instruments-service. (MIGRATED
      FROM: same.)
- [ ] [SCRIPT] P3. **OPTIONAL physical-GCS cleanup of old ICE-Databento instrument parquets** once tombstone
      reconciliation confirms 0 consumers (twin-verify; operator-gated delete, never blind). Repo: deployment-service +
      instruments-service. (MIGRATED FROM: same.)

### G1.f.2 post-retirement cleanup (2026-06-26)

- [ ] [UAC] P2. **Clean up stale CBOE `ohlcv_15m` capability registrations post VIX-INDEX retirement.** Two stale
      artifacts remain in UAC after G1.f.2: (a) `expected_coverage.py` line 135 still says "CBOE provides VIX 15m" and
      line 156 still includes `"ohlcv_15m"` in CBOE's list — the comment is stale (that entry was the now-deleted VIX
      cash INDEX source; VX futures are `ohlcv_1s`/`ohlcv_1m` only); (b) `data_type_capability.py` has a
      `DataTypeCapability(venue="CBOE", data_type="ohlcv_15m", instrument_type="")` with empty instrument_type — this
      entry was for the INDEX type and has no live source post-retirement. Also: `TradfiOhlcv15mAdapter` docstring ("for
      15-minute OHLCV data (Barchart VIX)") in MDPS `ohlcv_passthrough.py` is stale. Current impact = **zero**
      (features=0 consumers; 15m VX-futures data was never requested downstream — VX futures are used at 1s/1m
      granularity). Cleanup path: remove `ohlcv_15m` from CBOE's `expected_coverage` + remove the stale CBOE `ohlcv_15m`
      `DataTypeCapability` + update the MDPS adapter docstring. IMPORTANT: if a consumer of `CBOE:FUTURE:VX ohlcv_15m`
      is added in the future, the 1s/1m→15m aggregation path must be wired first (MDPS `TradfiOhlcv1sAdapter` comment
      says "Coarser bars aggregate downstream" but NO aggregation code exists — that's a doc-ahead-of-implementation
      gap). Repos: unified-api-contracts + market-data-processing-service. **Operator notification**: retiring VIX-INDEX
      left stale `ohlcv_15m` entries in UAC and MDPS; zero live impact but cleanup needed before adding any 15m VX
      futures consumer.
