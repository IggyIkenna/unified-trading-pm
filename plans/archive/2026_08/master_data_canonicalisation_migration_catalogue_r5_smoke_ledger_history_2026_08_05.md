---
doc_type: record
title: "Extracted R5 smoke ledger — master_data_canonicalisation_migration_catalogue (2026-08-05 line-cap remediation)"
summary: >-
  Verbatim extraction of the closed R5 smoke ledger section from the master migration catalogue coordinator — a one-time
  probe from 2026-06-11 whose every follow-up todo is done and whose data is stale history. Extracted to keep the live
  coordinator under the 1000-line hard cap.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [line-cap-remediation, historical, r5-smoke, migration]
created: "2026-08-05"
author: slot-14
parent_epic: manifest_master
source:
  [
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    /plans/archive/2026_08/issues/context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md,
  ]
---

# Extracted — R5 smoke ledger (2026-06-11)

> **Extracted verbatim 2026-08-05 → this file** (line-cap remediation pass 3,
> `/plans/archive/2026_08/issues/context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md` todo P3) — the full R5 smoke
> ledger (BLOCKED shards table, GREEN per-AG table, cross-cutting findings, promotion-to-main snapshot, and all 7
> remediation todos) from the master migration catalogue coordinator. Every R5-fix todo is `[x]` done; the one-time
> probe data (2026-06-11) is stale history; the Gate-State Board now reads G4 all-green across all 5 AGs. The live
> coordinator retains a one-line pointer.

### R5 smoke ledger — pending-post-migration-backfill shards (2026-06-11)

> **Method**: 26 live probes (12 by the session-limited predecessor 08:12–08:29 UTC + 14 on resume 09:12–09:35 UTC), all
> from the MAIN clones' `.venv` CLIs with real ADC + Secret Manager credentials, `--dry-run` +
> `VM_NAME=smoke-probe-<ag>` + `MANIFEST_PER_VM_SHARDS=true` (no prod manifest writes), 1 recent day, 1–2
> symbols/venues, `--max-instruments`. Raw logs: `/tmp/r5_smoke/*.log` (worker host). IS probes re-ran with
> `MANIFEST_ALLOW_STALE_FALLBACK=true` after every first-pass IS probe loud-failed on the DOWN consolidator (see
> cross-cutting findings). **Verdict grain = (asset_group × data_type × venue) — never whole-AG.**

#### BLOCKED shards (the pending-post-migration-backfill set)

| AG         | data_type (shard)                                                 | venue × source                                                           | Classification           | Evidence + detail                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ---------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------ | ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| cefi       | `trades`, `book_snapshot_5`, `derivative_ticker`, `futures_chain` | BINANCE-FUTURES × tardis (and any venue on the shared tardis batch path) | **CODE-BUG**             | `Invalid comparison between dtype=datetime64[ns] and date` — deterministic on HEAD mtds@eb33603, raised inside the venue shard (shard-isolated), instruments load fine (10 instruments). Repro: `--operation download --asset-group cefi --venues BINANCE-FUTURES --start-date 2026-06-09 --data-types trades --max-instruments 1 --dry-run`. Log `mtds-cefi-tardis-retry.log`. Tardis key present + ApiKeyReloader-validated; bug fires BEFORE any tardis HTTP, so actual CSV download remains unproven. |
| tradfi     | `ohlcv_1m` (+ all databento data_types)                           | CME, NASDAQ × databento                                                  | **BLOCKED-CREDENTIALS**  | `403 auth_account_locked` — "Your account has been locked for security reasons" on GLBX.MDP3, XNAS.ITCH, DBEQ.BASIC (mtds) AND on IS definitions fetch. Logs `mtds-tradfi-{cme,nasdaq}-ohlcv1m.log`, `is-tradfi-databento-cme-fb.log`. **Operator ask: unlock the Databento account** (vendor support / dashboard).                                                                                                                                                                                       |
| tradfi     | `instrument_definitions`                                          | CME × massive                                                            | **BLOCKED-UPSTREAM-4XX** | MASSIVE_API_KEY valid (auth passes); `https://api.polygon.io/futures/vX/contracts?product_code=MES&…` → 404 ×3 attempts. Same finding as R4's CME re-probe P1 todo (`proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md`) — endpoint shape, not creds. Log `is-tradfi-massive-cme-fb.log`.                                                                                                                                                                                                        |
| tradfi     | `ohlcv_24h` (FX daily)                                            | FX × yahoo                                                               | **CODE-BUG**             | Yahoo fetch GREEN (KRWUSD=X, 1 row) but write fails pre-write validation: `[missing_column] required column 'instrument_id' missing from dataframe`. Log `mtds-tradfi-fx-ohlcv24h.log`.                                                                                                                                                                                                                                                                                                                   |
| defi       | `lst_rates` (14 EVM + 2 Solana tokens)                            | LIDO-ETHEREUM et al × onchain/subgraph                                   | **BLOCKED-PRECONDITION** | `assert_defi_catalog_fresh` routes honest absence — defi instrument-catalog stale/missing at probe time (age=None). Creds present (thegraph/RPC). R4 has since re-promoted catalogues → **re-probe post-R4** before classifying further. Logs `mtds-defi-lst-rates*.log`.                                                                                                                                                                                                                                 |
| defi       | `dex_pools` (subgraph daily metrics)                              | UNISWAP_V3-ETHEREUM × thegraph                                           | **BLOCKED-PRECONDITION** | Same `assert_defi_catalog_fresh` gate (catalog age=None at 09:16 UTC, post-R4-promote — verify catalogue freshness contract). TheGraph credential proven GREEN out-of-band (gateway HTTP 200, pool data, key `thegraph-api-key`). Log `mtds-defi-dexpools-subgraph.log`.                                                                                                                                                                                                                                  |
| prediction | `instrument_definitions`                                          | KALSHI × kalshi REST                                                     | **BLOCKED-UPSTREAM-4XX** | `GET https://api.elections.kalshi.com/trade-api/v2/markets?limit=200&status=active` → HTTP 400 Bad Request (×retries, classified AUTH-free public endpoint — request shape, likely the `status=active` param no longer valid). Logs `is-pred-kalshi{,-fb}.log`.                                                                                                                                                                                                                                           |
| prediction | `trades`                                                          | KALSHI × kalshi REST                                                     | **BLOCKED-PRECONDITION** | mtds: "No active venues for date=2026-06-09" — zero KALSHI rows in `instruments-store-pred-prd` (`instrument_availability/by_date/day=2026-06-09/` carries POLYMARKET only). Downstream of the KALSHI 400 above. Log `mtds-pred-kalshi.log`.                                                                                                                                                                                                                                                              |
| sports     | `ODDS` (IS footystats odds snapshot — manifest write)             | FOOTYSTATS × footystats                                                  | **CODE-BUG**             | Fetch GREEN (8 odds rows) but manifest write rejected: `source='odds_api' … not a registered source for asset_group='sports' data_type='ODDS'. Allowed: ['footystats']` (UAC SOURCE_PRIORITY fail_fast). Wrong source label in `instruments-service.footystats_odds_fetch`. Logs `is-sports-footystats{,-fb}.log`.                                                                                                                                                                                        |

Non-blocking / N-A rows (recorded so nobody re-probes them as gaps): tradfi `trades` × CME = **expected drop** (UAC
declares trades unsupported for CME — pre-flight drops it, not a failure); tradfi × BARCHART = **N/A by design** (VIX
15m 2020→2025-11 is a static GCS preload via `scripts/upload_vix_barchart_local.py`; no live Barchart adapter exists);
prediction `trades` × POLYMARKET on 2026-06-09 = **honest-empty** (clob fetch GREEN — 914 ticks returned — but lifecycle
gating dropped all as post-settlement for that date's settled markets; fetchability proven); mtds massive market-tick
path = **not wired** (`MassiveTradfiRestConnector` exists in mtds but has zero consumers — IS `--source massive` is the
only live massive surface; tracked in remediation todos below) **(HISTORICAL — Massive removed as a source 2026-07-19;
connector deleted)**.

#### GREEN per AG (probe-grain counts)

| AG         | GREEN probes                                                                                                                                                                                            | BLOCKED shards (table above)  |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| cefi       | 1 — IS definitions × BINANCE-FUTURES (fresh `by_date` through 2026-06-11 post-R4; tardis/hyperliquid/aster keys validated)                                                                              | 1 (tardis tick path)          |
| defi       | 5 — IS definitions (320 records, 2 venues); `gas_fees` × ETHEREUM RPC (449 rows); `gas_fees` × SOLANA RPC (109 rows); `perp_funding` × HYPERLIQUID (5,520 rows); thegraph credential (gateway HTTP 200) | 2 (both catalog-precondition) |
| tradfi     | 1 — `ohlcv_15m` × CBOE VIX via yahoo (52 rows) (+2 N/A-by-design rows)                                                                                                                                  | 4                             |
| sports     | 2 — mtds `trades`(odds) × ODDS_API (699 rows / 20 bookmakers); IS footystats fetch (8 predictions + 1 match + 8 odds)                                                                                   | 1 (manifest source label)     |
| prediction | 2 — IS definitions × POLYMARKET gamma (9,420 instruments); mtds `trades` × POLYMARKET clob (914 ticks fetched; honest-empty for the probed date)                                                        | 2 (both KALSHI)               |

#### Cross-cutting findings

1. **Manifest consolidator DOWN/stale for every probed bucket** — consolidated `availability_index` ages at probe time:
   `instruments-store-*` ≈ 3.2 d, `gas-fees` ≈ 21.8 d, `perp-funding` ≈ 21.8 d, `lst-rates` ≈ 9.8 d, `dex-pools` ≈ 12.2
   d — all > the 120 s threshold while per-VM shards exist, so EVERY IS CLI run loud-fails
   (`ManifestConsolidatorStaleError`) without `MANIFEST_ALLOW_STALE_FALLBACK=true`. Partially expected under the
   pre-migration drain, but the instruments-store consolidator gates R-wave tooling too — needs the Cloud Run Job +
   Scheduler back before (or as part of) the post-apply restart.
2. **Predecessor's 08:15/08:19 cefi failures explained**: `day=2026-05-21` instruments parquet 404 = the R4 IS capture
   freeze (now backfilled); the `cannot access local variable 'pq'` error no longer reproduces on HEAD (tardis_adapter
   split mtds@eb33603); the datetime64-vs-date bug DOES reproduce (table row 1).

#### Promotion-to-main snapshot (2026-06-11 ~09:15 UTC) — stale-image caveat

**NO repo's 2026-06-10/11 LDR ships have fully reached `origin/main`** — every repo in the workspace carries real
content delta LDR→main (so Cloud Build images on `main` are stale relative to all R-wave/canonicalisation code). Key
repos (main-tip → LDR-tip, content delta):

| Repo                     | `origin/main` tip                   | LDR tip                                 | LDR ahead (content)                                                           |
| ------------------------ | ----------------------------------- | --------------------------------------- | ----------------------------------------------------------------------------- |
| market-tick-data-service | b1bffd4 06-10 15:02 (promote #177)  | eb33603 06-11 04:43 (tardis split)      | 57 commits / 130 files                                                        |
| instruments-service      | b0df1c6 06-10 08:47                 | 87f93ff 06-11 08:54 (CF-18 alias-aware) | 108 commits / 82 files                                                        |
| unified-api-contracts    | 1adfc65 06-11 03:33 (hotfix merge)  | 0e0ed8c 06-11 08:53                     | 60 commits / 44 files                                                         |
| unified-trading-library  | e0c557be 06-11 03:36 (hotfix merge) | 6680ea26 06-11 02:36                    | 14 commits / 3 files (+422); PM ci_status marks UTL **FAILING** on main 09:10 |
| deployment-service       | 7f0b720 06-10 22:45 (promote #46)   | 04e3d20 06-11 01:36                     | 35 commits / 12 files                                                         |
| unified-trading-pm       | a07ea1042 06-11 09:10               | 44bc76cfc 06-11 10:11                   | 3 commits / 11 files (standing PR drains ~15 min)                             |

Remaining 19 service repos: 7–64 commits of real content each ahead of main (full sweep in the R5 session log). The R5
smoke matrix therefore ran on LDR-tip code (the MAIN clones), NOT the stale main images — correct for proving
current-code fetchability; the image-rebuild ride happens when the LDR→staging→main drains catch up.

#### R5 remediation todos (dispatch — surface per repo)

- [x] ✅ [BUG] P0. **R5-fix-1 — cefi tardis datetime64-vs-date comparison — DONE mtds@657f615 (2026-06-16
      /autonomous).** DIAGNOSIS: at LDR-tip the raw `datetime64[ns] vs date` comparison no longer exists — every date
      compare in the cefi tardis path uses safe `.dt.date` (vectorized, `tardis_symbol_resolution._resolve_symbols` GCS
      branch) or scalar `pd.Timestamp(x).date()` (`cefi_catalog_reader`); exhaustive scan = 0 unguarded compares; the
      `eb33603` repro now exits 0. The durable guard SHIPPED: new
      `tests/unit/test_tardis_resolve_symbols_date_boundary.py` — 9 tests feeding a **real datetime64[ns]** availability
      parquet at the boundary (from==target / ±1d, to==target / ±1d, NaT), asserting NO `Invalid comparison` raises +
      correct pre-listing/expired filtering (would re-catch a `.dt.date`→raw regression). **Live re-smoke of the actual
      BINANCE-FUTURES Tardis CSV download = BLOCKED-LIVE-VERIFY** (needs real Tardis creds + network; `--block-network`
      here) — the bug-class is closed + test-guarded regardless. Repo: market-tick-data-service.
- [x] ✅ [BUG] P1. **R5-fix-2 — tradfi FX yahoo writer missing `instrument_id`** — DONE mtds@ed23954. Added
      `rec["instrument_id"] = f"{fx_pair.base}-{fx_pair.quote}"` in `umi_tick_provider._fetch_yahoo_fx` (mirrors the VIX
      path) + 75-line regression test. (Yahoo FX path lives in `umi_tick_provider.py`, not a separate adapter.)
      QG-green.
- [x] ✅ [BUG] P1. **R5-fix-3 — footystats ODDS manifest source label** — **instruments-service@b475ae8** (/autonomous).
      NOT already correct: `_sports_ref_source("footystats_odds")` returned `odds_api` (stripped `batch_` off the
      pipeline_mode path-key `batch_odds_api`) → `record_captured(data_type=ODDS, source='odds_api')` failed
      `MissingSourceError` (UAC `SOURCE_PRIORITY[(sports, ODDS)]==['footystats']`). Fix = scoped
      `_SPORTS_REF_SOURCE_OVERRIDE` (path-key ≠ source case) → returns `footystats`; the two existing tests codifying
      the wrong `odds_api` corrected (they ARE the regression guard). Evidence:
      `tests/unit/test_sports_reference_v9_path.py`.
- [x] ✅ [BUG] P1. **R5-fix-4 — kalshi instruments 400** — DONE is@4562dad (code). Root-caused: Kalshi `status` is a
      LIFECYCLE filter whose valid values are `unopened`/`open`/`closed`/`settled` — `status=active` is rejected 400
      (the per-MARKET `status` field IS `"active"` for tradeable markets, but the REQUEST filter is `status=open`).
      Changed `status=active`→`status=open` in `prediction/kalshi.py` + test. **Residual (still open):** the actual IS
      kalshi prediction backfill RUN + mtds re-smoke (operational, gated on the capture-restart sequencing). Repo:
      instruments-service.
- [x] ✅ [INFRA] P1. **R5-fix-5 — restore manifest consolidator** for `instruments-store-*` (+ the defi data buckets) as
      part of the post-apply restart sequencing — every IS CLI loud-fails on the stale index today
      (`MANIFEST_ALLOW_STALE_FALLBACK=true` is the interim recovery). Repo: deployment-service (Cloud Run Job +
      Scheduler). — DONE 2026-07-26 (`cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`). Re-measured live, 46
      days after this finding: the consolidator is genuinely healthy today — no code/infra change was needed. All 6
      relevant Cloud Run Jobs + Schedulers (`instruments-{cefi,tradfi,defi,sports,prediction}` + `market-data-defi`) are
      ENABLED and completing successfully on their 60s cadence (≥5 consecutive runs verified); a real
      `instruments-service --operation status` CLI run against all 5 `instruments-store-*` buckets succeeded with
      `MANIFEST_ALLOW_STALE_FALLBACK` unset, returning real coverage data with zero `ManifestConsolidatorStaleError`.
      Full evidence in `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`'s copy of this todo.
- [x] ✅ [DATA] P2. **R5-fix-6 — `MassiveTradfiRestConnector` RETIRED.** Massive removed as a tradfi source 2026-07-19
      (operator: Databento=batch SoT, Yahoo=daily); the mtds connector + both vendor adapters + `--source massive`
      runtime routing DELETED (`uac@a2beed46` + `mtds@362a487e`); subscription terminated + GCS estate purged 2026-07-21
      (operator Option C). The "wire" option and the "DEFERRED until the massive futures endpoint 404 resolves" gate are
      moot — the vendor is gone. `batch_massive` PipelineMode/possible_manifest recognition is deliberately kept only
      until the gated legacy-GCS purge (per `tradfi-databento-sourcing-ssot.md`). Repo: market-tick-data-service.
- [x] ✅ [DATA] P2. **DONE (na-eligibility-audit 2026-08-04)** — R5-fix-7 — re-probe defi `lst_rates` + `dex_pools`
      post-R4 catalog re-promote (the probes hit the stale-catalog honest-absence gate even after R4's re-promote —
      verify the catalogue freshness contract the preflight reads, then 1-day dry-run both to GREEN). Repo:
      market-tick-data-service. `assert_defi_catalog_fresh` root-caused + fixed 2026-06-21
      (`instruments-service@de8e164`+`e8acef1`, `data_completion_defi_2026_07_15.md` `[x]`); canary confirmed GREEN,
      dex_pools/dex_swaps sharding shipped (`mtds@5830cc8`) — already happened via the broader active DeFi backfill
      plan.
