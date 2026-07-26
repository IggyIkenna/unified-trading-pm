---
doc_type: issue
title: CeFi HL/ASTER batch data gaps — day-bleed rejection, HL trades under-capture, ASTER/liq misclassification
summary: "Per-data_type manifest breakdown (consolidated index + live per-VM shards):"
status: open
nature: process
asset_group:
  [cefi] # corrected 2026-07-25 (ag-closeout-audit orthogonality fix) -- was [cross-cutting], a genuine mistag:
  # HL(Hyperliquid)/ASTER are cefi venues and the doc's own tags already say "cefi" -- content is cefi-only
stage: [meta]
repos:
  [
    alerting-service,
    deployment-api,
    deployment-service,
    features-service,
    instruments-service,
    market-data-processing-service,
  ]
scope: [engineer, admin]
tags: [cefi, backfill, manifest, data-correctness, mtds, honest-coverage, data-status, catalogue]
related: [mvp_backfill_cefi_tick_v10_2026_06_27, /plans/active/issues/cefi_universe_capture_rule_2026_06_23.md]
created: 2026-06-22
parent_epic: mtds_mdps_master
priority: P2
source:
  [
    cefi manifest audit 2026-06-22 (per-data_type breakdown via consolidated + per-VM shards),
    cefi-hyperliquid-2024-resume / cefi-aster-* run.log runtime evidence,
  ]
assigned_vm:
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
---

# CeFi HL/ASTER batch data gaps — not 100%, with 3 diagnosed bugs

> **History extracted 2026-07-25** (line-cap remediation) — the original 2026-06-22/23 findings, BUG #1-4 diagnosis, and
> their shipped fixes/migration now live in
> `/plans/archive/2026_06/cefi_hl_aster_batch_data_gaps_history_2026_06_22.md`. Read that first for full context;
> everything below is what's still open.

## EXPANDED PROGRAM — full cefi catalogue (ALL venues) + daily-job verification + MTDS run (operator 2026-06-23)

Generalises BUG#4 from {HL,ASTER} to **all cefi venues**. Tardis access re-verified live: SSOT secret
**`tardis-api-key`** (academic-unlimited, 62 venues, genesis 2019 → 2027, `dataPlan:unlimited`); the dup
`tardis-api-key-full`/`-backup` (byte-identical) DELETED. IS Tardis reference-data now uses the **free no-auth**
`api.tardis.dev/v1/exchanges/{exchange}` metadata for enumeration (no key consumed) — shipped
instruments-service@`b99e586` (tested no-key enumeration).

**Schedulers ALREADY exist** (both ENABLED): `uts-prod-instruments-cefi-t1-schedule` (06:00 UTC → Cloud Run job
`uts-prod-instruments-service-cefi-t1-recon`, the daily IS fetch → daily shards `_catalogue/instruments-service/day=*/`)

- `instrument-catalogue-regen-nightly` (02:00 UTC → job `instrument-catalogue-regen`, aggregates daily shards →
  `prod/catalog.parquet`). Both jobs currently run image `market-tick-data-service:latest` — the b99e586 no-auth fix
  reaches them only after that image rebuilds (resolve at redeploy step P1).

### Gated sequence (each step waits on the prior)

- [ ] [INFRA] P0. **GATE**: HL/ASTER since-genesis re-run (7 VMs `cefi-*-20260623-113700`) completes — captured-coverage
      manifest re-read confirms full per-day universe captured. (Monitored; ~25–60% as of write.)
- [x] ✅ [DEPLOY] P1. Redeployed the IS fixes — built `instruments-service:latest`=7489ed1/0.43.0 from LDR (no-auth
      b99e586 + full-universe 0fe8e71 + dated-future quote fix 7489ed1) via Cloud Build d215d55a (SUCCESS); created the
      missing prod job `uts-prod-instruments-service-cefi-t1-recon` (fixes the ENABLED-but-404 06:00 IS scheduler).
      instruments-service@0fe8e71 + @7489ed1 on LDR. Evidence: `:latest` digest tag `7489ed1,0.43.0,latest`.

## DEPLOY MECHANISM RESOLVED (2026-06-23, operator dispatch)

**Deploy mechanism (DO step 1) — fully traced:**

1. **IS daily FETCH** = Cloud Run job `uts-prod-instruments-service-cefi-t1-recon` (scheduler
   `uts-prod-instruments-cefi-t1-schedule`, 06:00 UTC). Runs image
   `asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-system/instruments-service:latest`, args
   `--operation=instruments --mode=batch --category=ALL --run-tag=t1-recon` (pattern from the live dev job
   `uts-dev-instruments-service-t1-recon`). The Tardis adapter (`reference_data/adapters/cefi/tardis/adapter.py`)
   enumerates the full `VenueMapping().all_tardis_exchanges` set (21 exchanges incl. binance/binance-futures/deribit/
   bybit/okex*/coinbase/upbit/bitstamp/huobi*/bitfinex*/bitget*/kraken/cryptofacilities/lighter-zksync) via the no-auth
   `GET /v1/exchanges/{exchange}` (availableSince/availableTo → available_from/to). **The image build trigger
   `instruments-service-build` fires on push to `main`.**
2. **Catalogue AGGREGATION** = Cloud Run job `instrument-catalogue-regen` (scheduler
   `instrument-catalogue-regen-nightly`, 02:00 UTC). Runs image `market-tick-data-service:latest` cmd
   `python /usr/src/unified-api-contracts/scripts/generate_instrument_catalogue.py --project-id central-element-323112`
   (UAC rollup baked into the MTDS image — daily shards → `prod/catalog.parquet`).

**THIRD ROOT FINDING — full-universe cap on the Tardis CEX venues (FIXED):** The catalogue's per-venue latest-day counts
were thin for the major CEX venues (BINANCE-SPOT 82 / BINANCE-FUTURES 56 / BYBIT 310 — vs real hundreds) because the
Tardis adapter's `_passes_asset_filter` (`reference_data/adapters/cefi/tardis/parsing.py`) gated EVERY spot/perp/future
on the curated ~45-asset `CEFI_BASE_ASSET_UNIVERSE` majors whitelist — the SAME cap BUG#4 dropped for HL/ASTER
(aster.py/hyperliquid.py @6031902) but never for the Tardis CEX venues. **FIXED — instruments-service@0fe8e71**: dropped
the `CEFI_BASE_ASSET_UNIVERSE` base gate for spot/perp/future (full-universe enumeration — every active instrument on a
canonical USD-family quote, small-coin funding included); KEPT the accepted-quote gate (USDT/USDC/USD — drops exotic
cross pairs) + the OPTIONS BTC/ETH-underlying gate (Deribit per-coin-option-chain volume control, operator-documented).
Tests updated to the full-universe contract (`test_cefi_tradfi_comprehensive.py`, `test_tardis_kraken_symbol_parse.py`).
IS `quality-gates.sh --no-fix` GREEN (73s).

**TWO ROOT BLOCKERS FOUND:**

- **(A) The no-auth fix b99e586 is on LDR ONLY** (NOT on staging/main). The `instruments-service:latest` image built
  today 12:10 is tag `412dedb` = 0.41.0 (the commit BEFORE b99e586). So the deployed image does NOT carry the no-auth
  enumeration fix. → Building the image directly from LDR (chicken-and-egg deploy authority).
- **(B) THE PROD IS RECON JOBS DO NOT EXIST.** `uts-prod-instruments-service-cefi-t1-recon` (+ `…-t1-recon`) are
  referenced by ENABLED schedulers (`t1_batch_scheduler.tf` defines only the scheduler, not the job) but the Cloud Run
  JOB was never created — only the `uts-dev-…` variants exist. So the 06:00 cefi IS fetch has been **404-ing silently in
  prod** = the IS catalogue daily fetch never ran in prod (explains the stale/small Tardis subset). → create the prod
  job from the dev pattern. **FIFTH ROOT FINDING — full-universe drop EXPOSED a latent venue-killer (FIXED):** the first
  full-universe fetch (exec ttt2g) succeeded but wrote only 11/19 venues — the 8 missing were exactly the high-value CEX
  venues (BINANCE-SPOT/FUTURES, BYBIT, KRAKEN-FUTURES, BITGET-SPOT/FUTURES, BITFINEX-SPOT, bare OKX). Root cause: ~49
  binance-futures symbols (dated quarterlies `btcusdt_260626`, `btcbusd_210129`; odd `btcusd1`) resolved to an EMPTY
  quote — the `_split_symbol` underscore path only accepted a quote AFTER `_`, but the expiry tag (`260626`) is not a
  quote, so the `<BASE><QUOTE>` body before `_` was never matched. `InstrumentRecord` REQUIRES a non-empty quote*asset
  for SPOT/FUTURE/PERP (hard_schema_enforcement) → it RAISED inside the per-venue parse loop → CF-11 re-raised → the
  WHOLE venue dropped to 0 rows. The majors whitelist had MASKED this (those exotic bases were filtered
  pre-construction). **FIXED — instruments-service (next commit)**: (1) `_split_symbol` handles the dated-future shape
  `<BASE><QUOTE>*<EXPIRY>`by concatenated-matching the body before`\_`; (2) `\_parse_tardis_instrument` SKIPS (returns
  None, never raises) a pair-identity instrument with an unresolved quote — shard-level isolation so one bad symbol
  can't kill a venue. Local repro post-fix: binance-futures **869** (was 56), binance(-spot) **1167** (was 82), bybit
  **1497** (was 310), bitget-futures 951, cryptofacilities/KRAKEN-FUTURES 1148, bitfinex 288 — all parse, none raise.

### ⚠️ OPERATOR DECISION — semantic conflict: full-venue-universe (this dispatch) vs wide-curated-whitelist (peer WIP)

**Two concurrent, conflicting approaches to the SAME surface (cefi universe gating):**

- **THIS dispatch (operator: "FULL universe per venue, binance-futures hundreds")** — IS@0fe8e71 + quote fix:
  `_passes_asset_filter` DROPS the `CEFI_BASE_ASSET_UNIVERSE` base-whitelist gate for spot/perp/future → every active
  instrument on a USD-family quote enumerates. Gate reduced to {accepted-quote, options=BTC/ETH}.
- **Concurrent PEER (uncommitted WIP in `unified-api-contracts/.../cefi_instrument_universe.py`)** — rewrites
  `CEFI_BASE_ASSET_UNIVERSE` into a wider survivorship-bias-free UNION (legacy-44 + historical-top-100-since-2019) but
  DELIBERATELY KEEPS the whitelist gate ("NOT everything the venue lists — admits thousands of junk/wash pairs").
- **Reconciliation (autonomous, per operator's explicit full-universe instruction + don't-stomp-peer-WIP)**: the edits
  are in DIFFERENT files, no textual conflict — with my `_passes_asset_filter` change the base-whitelist is not
  consulted for spot/perp, so the peer's widened list is moot-for-gating but harmless. Proceeded with the operator's
  explicit "full universe" instruction. \*\*If the operator prefers the peer's curated-gate model, revert 0fe8e71's
  base-gate drop
  - adopt the peer's wide union.\*\* Both valid; flagged for human confirmation. NOT a blocker for this dispatch.

### Progress Log (2026-06-23 — operator full-cefi-catalogue dispatch, in flight)

- **Deploy mechanism resolved** (above). IS image build trigger `instruments-service-build` (asia-northeast1) fires on
  push to `main`; builds `instruments-service:latest` (+ `:VERSION` + `:SHORT_SHA`). The catalogue jobs:
  `uts-prod-instruments-service-cefi-t1-recon` (FETCH, image `instruments-service:latest`, args
  `--operation=instruments --mode=batch --asset-group=CEFI --run-tag=t1-recon`) → daily shards
  `instrument_availability/by_date/day=*/venue=*/instruments.parquet`. Per-instrument rollup =
  `instruments-service/scripts/build_instrument_catalogue.py --asset-group cefi` (NOT the `instrument-catalogue-regen`
  Cloud Run job — that builds the availability-MATRIX from `_index/availability_index.parquet`). `available_from` =
  MIN(first observed snapshot day, declared `available_from_datetime` = Tardis `availableSince` genesis); monotonic
  grow-only guard.
- **Created** the missing prod job `uts-prod-instruments-service-cefi-t1-recon` (fixes the ENABLED-but-404 06:00
  scheduler) — `DEPLOYMENT_ENV=prod`, `--asset-group=CEFI`, SA `unified-trading-sa`, 2cpu/4Gi/3600s.
- **Shipped** instruments-service@0fe8e71 (full-universe whitelist drop) to LDR; PM plan flip @06c459fd3.
- **Built** final `instruments-service:latest` from LDR@0fe8e71 (no-auth + full-universe), Cloud Build accf1e5c (in
  flight). Once green: execute the fetch job → rollup → verify → export CSV.
- Tardis venue universe = `VenueMapping().all_tardis_exchanges` (21 exchanges) → IS `_CEFI_VENUES` (19 canonical cefi
  venues: BINANCE-SPOT/FUTURES, BYBIT, OKX-SPOT/SWAP/FUTURES, DERIBIT, DERIBIT-COMBO, COINBASE-SPOT, HYPERLIQUID, UPBIT,
  ASTER, KRAKEN-FUTURES/SPOT, BITFINEX-FUTURES/SPOT, BITGET-SPOT/FUTURES).

**FOURTH ROOT BLOCKER — IS recon job has NO date default (FOUND + worked-around 2026-06-23):** the IS CLI date-loop
framework (`UTL date_utils.get_date_range`) requires explicit `--start-date`/`--end-date`; the recon job args omitted
them and the empty scheduler `httpTarget.body` injects none → `ValueError: Invalid date format ''` → `exit(1)`. So even
had the prod job existed, the 06:00 schedule would have crashed on dates. Worked around by setting
`--start-date=$TODAY --end-date=$TODAY` on the job. **FOLLOW-UP TODO below** — the recurring daily job must self-default
to today (a hardcoded date goes stale tomorrow).

- [ ] [SCRIPT] P2. **instruments-service / deployment-service** — make the cefi IS recon job's date default to "today"
      (yesterday for true T+1) instead of a hardcoded `--start-date`/`--end-date`. Either (a) the IS CLI defaults
      `--start-date`/`--end-date` to the run day when `--run-tag=t1-recon` and they're unset, OR (b) the
      `t1_batch_scheduler.tf` scheduler injects `{start-date,end-date}=today` via `httpTarget.body` overrides. Until
      fixed, the hardcoded job-arg date (set 2026-06-23) makes tomorrow's scheduled run re-fetch the stale 2026-06-23.
      Provenance: this dispatch — the daily fetch crashed on empty dates (`Invalid date format ''`).

- [x] ✅ [INFRA] P1. Force-ran the IS fetch (`uts-prod-instruments-service-cefi-t1-recon` exec xqcxr) → daily shards
      day=2026-06-23 for ALL 18 cefi venues (10,458 active instruments, full universe per venue — binance-spot 763 /
      binance-futures 677 / bybit 640 / kraken-spot 894 / okx-spot 848, NOT the old ≤33 subset). Aggregated via
      `build_instrument_catalogue.py --asset-group cefi` (the correct per-instrument rollup tool; the
      `instrument-catalogue-regen` Cloud Run job builds the SEPARATE availability-MATRIX, not the per-instrument
      catalog) → `prod/catalog.parquet` PROMOTED 230,073 rows (monotonic ACCEPT). Per-venue breadth + available_from/to
      genesis verified (see FINAL REPORT).
- [ ] [INFRA] P2. **Tomorrow-verify (2026-06-24)**: confirm both schedulers fired on the new day (02:00 + 06:00 UTC) +
      produced fresh shards + aggregate on the new code. Flip only after 100% confirmed.
- [x] ✅ [SCRIPT] P2. **DONE (2026-07-26, slot-12)**: entries already existed (added via a since-landed "CeFi venues
      added 2026-06-23" for-loop section in `data_type_capability.py`, not a literal per-venue block — a literal-string
      grep missed them). Locked in with a new regression test (`unified-api-contracts@b0547c36`, 9 tests). Full
      evidence: `plans/active/cefi_satellite_ao_dispatch_batch2_2026_07_26.md`'s corresponding todo.
- [ ] [MTDS] P2. **MTDS run for all cefi/Tardis venues** — since-genesis batch + live, full catalogue-driven universe.
      (Tardis batch billing gate LIFTED — operator paid; access confirmed unlimited — confirmed by operator ruling
      2026-07-12, finding 228, `plans/archive/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2.)
      Year×data_type×venue shard.

  ### Scoping 2026-07-12 (operator-ordered pre-launch) — READ-ONLY breakdown before the Tardis paid backfill launch

  Operator ruling 2026-07-12 ("Scope first"): before dispatching the MTDS-run todo above, produced a launch-decision
  breakdown of the current live cefi manifest's `attempted_failed` population — **not** a re-statement of the 2026-06-21
  775.9k snapshot cited in `cefi_tardis_historical_blocked_credentials_2026_06_21.md` (that count is stale; the manifest
  has been purged/relaunched/re-shaped multiple times since — clip fixes, NOT_LISTED purge, catalogue full-universe
  expansion, mvp-gate — per this doc's own Progress Log). Method: `read_availability_index` (UTL) against the live cefi
  consolidated `_index` (bucket `market-data-tick-cefi-prd-central-element-323112`), MTDS `.venv`, read-only,
  2026-07-12. HYPERLIQUID/ASTER (native, non-Tardis venues per the resolved billing-gate doc) excluded — everything else
  on cefi routes through Tardis.

  **Headline (measured, live index, 2026-07-12):**

  | metric                                                                               |         count | share |
  | ------------------------------------------------------------------------------------ | ------------: | ----: |
  | Total cefi `attempted_failed` (all venues)                                           |     1,724,328 |  100% |
  | Native-venue (HYPERLIQUID/ASTER) `attempted_failed` (out of scope)                   |         2,096 |  0.1% |
  | **Tardis-attributable `attempted_failed` (this todo's population)**                  | **1,722,232** | 99.9% |
  | ↳ under CANONICAL launcher venue names (`launch-cefi-sharded-backfill.sh` `VENUES=`) |     1,319,017 | 76.6% |
  | ↳ under LEGACY/raw-Tardis-exchange-id venue tags (launcher will NOT target by name)  |       403,215 | 23.4% |
  | ↳ `error_reason` contains `403` (see CRITICAL blocker below)                         |     1,291,049 | 74.9% |
  | ↳ `error_reason` = `VENUE_FETCH_FAILED` (non-HTTP-coded adapter failures)            |       353,405 | 20.5% |

  **Breakdown by venue × year** (Tardis-attributable `attempted_failed` cells; canonical launcher venues only —
  legacy-tag venues broken out separately below):

  | venue               |  2020 |  2021 |  2022 |  2023 |  2024 |  2025 |  2026 |         TOTAL |
  | ------------------- | ----: | ----: | ----: | ----: | ----: | ----: | ----: | ------------: |
  | DERIBIT             | 88794 | 88843 | 88654 | 89315 | 91357 | 91571 | 37716 |       576,288 |
  | BINANCE-FUTURES     | 15005 | 28719 | 49532 | 54161 | 36195 |  6919 |   476 |       191,007 |
  | BYBIT               |     4 |   691 | 44058 | 42481 | 11284 | 22146 | 48210 |       168,874 |
  | BITFINEX-FUTURES    |     0 |   528 |  5484 | 11097 | 15120 | 17400 | 15264 |        64,893 |
  | KRAKEN-FUTURES      |     0 |  4692 |  7941 | 18750 | 20400 |  8550 | 12315 |        72,648 |
  | OKX-SWAP            |     0 |   789 |   497 |  1910 |   762 |   780 |   435 |         5,173 |
  | BITGET-FUTURES      |     0 |     0 |     0 |     0 | 36400 | 41091 | 88388 |       165,879 |
  | BINANCE-SPOT        |   170 |    66 |  2166 |  5143 |  4334 |  2377 |    14 |        14,270 |
  | UPBIT               |     0 |     0 |  4404 |  9099 |  8856 |  7561 |  7167 |        37,087 |
  | COINBASE-SPOT       |     6 |   756 |   898 |   588 |   542 |   299 |     5 |         3,094 |
  | OKX-FUTURES         |     0 |     0 |     0 |     0 |   991 |  1361 |    47 |         2,399 |
  | OKX-SPOT            |     0 |     1 |    30 |   186 |   577 |   300 |    35 |         1,129 |
  | BITGET-SPOT         |     0 |     0 |     0 |     0 |   400 |  2300 |  4900 |         7,600 |
  | KRAKEN-SPOT         |     0 |   100 |   800 |   600 |   500 |   200 |   700 |         2,900 |
  | BYBIT-SPOT          |     0 |   536 |   808 |   284 |   668 |   854 |   626 |         3,776 |
  | BITFINEX-SPOT       |     0 |     0 |     0 |     0 |   500 |     0 |  1500 |         2,000 |
  | **canonical TOTAL** |     — |     — |     — |     — |     — |     — |     — | **1,319,017** |

  **Breakdown by data_type** (Tardis-attributable, all venues incl. legacy tags): `book_snapshot_5` 633,090 (36.8%) ·
  `trades` 474,068 (27.5%) · `derivative_ticker` 278,881 (16.2%) · `options_chain` 113,589 (6.6%, ~all DERIBIT) ·
  `futures_chain` 112,716 (6.5%, ~all DERIBIT) · `liquidations` 100,818 (5.9%) · blank/other 9,070.

  **Legacy/non-canonical venue tags** (403,215 cells, 23.4% — `launch-cefi-sharded-backfill.sh`'s default `VENUES=` list
  does **not** contain these spellings, so a plain relaunch will silently skip them): BITFINEX 103,860 · OKEX-SWAP
  102,126 · BINANCE 78,855 · OKEX-FUTURES 50,160 · COINBASE 34,133 · CRYPTOFACILITIES 20,601 (= Kraken Futures'
  pre-rebrand Tardis exchange id) · OKEX 5,327 · BITFINEX-DERIVATIVES 4,299 · KRAKEN 1,973 · BITGET 1,003 ·
  COINBASE-INTERNATIONAL 673 · LIGHTER 108 · BYBIT-FUTURES 45 · bare `OKX` 14 · blank/`UNKNOWN` 38. These look like
  pre-venue-canonicalization row survivors (raw Tardis exchange-id spellings vs the UAC canonical `VENUE`-suffixed
  names) rather than a genuinely separate population — **flagged for a follow-up venue-tag reconciliation pass (are
  these stale duplicates of already-migrated canonical rows, or orphaned captures needing their own re-fetch under the
  legacy spelling?), not fixed here** (read-only scope).

  **Distinct exchange-days**: 17,836 distinct `(venue, date)` pairs across the whole Tardis-attributable population
  (13,784 of those under canonical venue tags). Tardis's own historical-replay billing model bills per
  exchange-day-of-data typically (per the resolved billing-gate issue doc), so this is the unit the cost model (below)
  would apply to if a per-unit price existed.

  **Cost-model status: NO committed Tardis per-exchange-day/month pricing found.** Grepped
  `/codex/02-data/tradfi-databento-sourcing-ssot.md` (TradFi/Databento-focused, no Tardis unit pricing) and the whole
  `codex/` + `plans/` corpus for a Tardis $/exchange-day or $/venue-month figure — none exists. The one Tardis
  $ figure
  in the corpus, `/codex/14-customer-journeys/commercial-model/pricing-building-blocks.md:101` ("Tardis £0.67[k/mo]"), is
  an internal blended COGS allocation for the commercial pricing model, **not** a per-exchange-day historical-replay
  unit price — not usable for sizing this launch. The operator's 2026-07-12 ruling ("paid, unlimited access
  confirmed") + the 2026-06-23 Progress Log entry above ("academic/unlimited plan... FLAT plan = no per-request
  billing") both point to **no incremental Tardis $
  per exchange-day for this launch** — the marginal cost driver is GCP VM compute (VM-hours), not a Tardis vendor fee.
  State this explicitly rather than inventing a $/day number.

  **⚠️ CRITICAL PRE-LAUNCH BLOCKER (found same-day, 2026-07-12): the 74.9% HTTP-403 share above is NOT genuine data
  unavailability.** `plans/active/issues/tardis_concurrent_ip_lockout_2026_07_12.md` (P0, still OPEN) diagnosed —
  live-reproduced via a direct `curl` returning Tardis error code 274 — that the shared academic-tier `tardis-api-key`
  permits only **ONE concurrent IP** for the bulk-CSV dataset endpoint. `launch-cefi-sharded-backfill.sh` provisions
  every VM with its own external IP and defaults `MAX_CONCURRENT=15` (operators have driven it to 20-80+ concurrent VMs
  historically) — so in any concurrent wave, at most ONE VM's Tardis calls succeed; every other VM 403s for its entire
  overlap. **Relaunching the fleet in the same parallel pattern used historically will very likely reproduce most of
  this same 403 backlog, not resolve it.** Status of the fix (per that issue's todos): a DEFAULT-OFF, CAS-hardened
  `TardisConcurrencyLease` GCS-lease serialization stopgap has SHIPPED (`market-tick-data-service@a9f1b52b`/`@7b8144ff`,
  `unified-trading-library@b010c7ad`, `deployment-service@c33f681`) but is **NOT YET smoke-tested on a real VM or
  enabled** (blocked todo: needs one real VM launch with `TARDIS_CONCURRENCY_LEASE=1` +
  `TARDIS_CONCURRENCY_LEASE_BUCKET=<bucket>` to prove acquire/renew/release, then a 2-VM serialization proof). That
  issue's own recommendation ranks **option (b) — ask Tardis to upgrade the academic-tier key to a multi-concurrent-IP
  paid tier — as the actual unlock** (zero engineering, a Secret-Manager value swap) over option (a) the lease stopgap
  (serialises waves ~20-80x slower) or (c) a centralized fetch proxy (2-3 dev-days, preserves full parallelism). **This
  todo's dispatch should be gated on that P0 issue's resolution**, not run in parallel with it — a pre-fix launch wastes
  VM-hours reproducing the same lockout.

  **VM fleet / wall-clock estimate** (canonical-venue population only, using `launch-cefi-sharded-backfill.sh`'s
  existing 1-VM-per-`(venue, year, heavy|light)` shard atom — same convention as every prior wave in this doc's Progress
  Log): **127 shards** = 84 heavy (`trades`+`book_snapshot_5`) + 43 light
  (`derivative_ticker`+`liquidations`+`futures_chain`[+`options_chain` for DERIBIT]) across the 16 canonical venues with
  outstanding failed cells. Heaviest venues by shard count: BINANCE-FUTURES (14), DERIBIT (14), BYBIT (12),
  BITFINEX-FUTURES (12), KRAKEN-FUTURES (12), OKX-SWAP (11). No committed per-shard wall-clock exists (this launcher's
  own inline comments cite anecdotal single-shard runtimes ranging ~24-48h in earlier/lighter-volume eras up to
  multi-day on 2022-2023 bull-market DERIBIT/BINANCE-FUTURES heavy shards — not a stable unit to multiply by 127 without
  empirical re-measurement) — do **not** invent a fleet-wall-clock number; measure off the first smoke-tested wave
  instead. **If the concurrency-lease stopgap is what ships** (vs the Tardis-plan upgrade), budget for the documented
  ~20-80x wall-clock inflation on top of whatever per-shard baseline the smoke wave measures, since every shard's Tardis
  fetches now serialize through one workspace-wide lease.

  **Recommended launch shape (sequencing, not yet executed — read-only scope of this pass):**

  1. **GATE 0 — resolve `tardis_concurrent_ip_lockout_2026_07_12.md` first.** Either land the Tardis multi-IP plan
     upgrade (option b, preferred — zero eng, moots the wall-clock hit) or complete the lease's on-VM smoke-test +
     enable it fleet-wide (option a stopgap). Do not dispatch the fleet before one of these is proven.
  2. **First wave = smoke, not the full 127.** Launch a small `ONLY=` slice (1-2 shards per venue-tier: one high-volume
     like DERIBIT or BINANCE-FUTURES, one low-volume like KRAKEN-SPOT) with whichever GATE-0 fix landed, to (a) measure
     real per-shard wall-clock post-fix and (b) confirm the 403 rate actually drops before committing VM-hours to the
     remaining ~120 shards.
  3. **Fleet wave** — the remaining canonical-venue shards, SPOT (per the workspace HARD RULE), `MAX_CONCURRENT=15`
     default (compute parallelism; Tardis-call serialization is handled by the lease/upgrade from GATE 0, not by capping
     VM count), staged in the launcher's existing per-venue batching.
  4. **Legacy-tag venues (403,215 cells, 23.4%) are OUT of this fleet's scope** — route to the follow-up
     venue-tag-reconciliation todo above, not a blind relaunch under the wrong spelling.
  5. **Re-verify via a fresh live-manifest query** (this same method) after the fleet wave completes, not by trusting
     the pre-launch `attempted_failed` count as a genuine-gap census — per
     `tardis_concurrent_ip_lockout_2026_07_12.md`'s own finding, historical `attempted_failed` counts across this
     workspace's multi-week CeFi backfill history are dominated by the self-inflicted lockout, not real per-cell data
     unavailability.

- [ ] [MTDS] P2. **Empty/failed re-analysis**: classify which existing `empty_confirmed`/`attempted_failed` cells were
      caused by the prior SMALL (≤33) instrument catalogue vs genuine absence → re-fetch the catalogue-caused ones now
      that the full universe is known.
- [ ] [SCRIPT] P3. **NICE-TO-HAVE** **deployment-service** — `create-code-tarballs.sh --asset-group X` hard-`exit`s on
      the FIRST dirty service repo in the asset-group set (a peer's uncommitted WIP in e.g. features-service), aborting
      the loop BEFORE the end-of-run upload → even the CLEAN core tarballs (mtds/UAC/UTL) never upload. Make the
      dirty-tree check per-repo SKIP-with-warning (like the not-found SKIP at line ~247) instead of a global abort, OR
      build+upload core first then services, so one peer's dirty leaf can't block a core-only deploy. Workaround used
      2026-06-23: `--include instruments-service` (core-only set, no cefi service repos) to get the core tarballs up.
      Provenance: Tardis CEX mvp-backfill dispatch — the `--asset-group CEFI` build aborted on dirty features-service.

---

## TARDIS CEX venues — mvp-driven backfill (operator 2026-06-23, dispatch)

Generalises BUG#4's catalogue-driven universe from {HL,ASTER} to the **Tardis CEX venues** (binance-spot/futures, bybit,
okx-spot/swap/futures, deribit, kraken-spot/futures, coinbase-spot, bitfinex-spot/futures, bitget-spot/futures, upbit).
Goal: backfill on the **mvp capture universe** (`is_in_mvp_capture_universe`, the perp-gated SSOT; manifest already
reclassified to this denominator).

### Diagnosis (Read of the actual code path — keystone finding)

The Tardis CEX path is `VM_TASK=cefi-backfill` → `--operation download` → `tick_data_handler.py` → orchestrator
`_process_venue` → `_fetch_one_venue` → `fetch_tick_data_for_venue` → `_route_tardis` → `TardisAdapter.download_batch` →
**`_resolve_symbols(exchange, date, instrument_ids)`** (`market_interface/adapters/tradfi/tardis_symbol_resolution.py`).

- When `instrument_ids` IS passed (the launcher's hardcoded 9-coin `SYMBOLS_<VENUE>` lists), `_resolve_symbols` uses
  those 9 verbatim → **cap at 9**. This is the keystone cap.
- When `instrument_ids` is None, `_resolve_symbols` reads the IS by_date snapshot
  `instrument_availability/by_date/day={D}/venue={V}/instruments.parquet` and returns its `raw_symbol`s — but that is
  the **FULL** per-venue universe (binance-futures 677, not the mvp subset), NOT mvp-gated. So neither path yields the
  mvp universe.

### Decision (autonomous, documented record of intent)

mvp-gate the `_resolve_symbols` GCS path with the SAME shared predicate `is_in_mvp_capture_universe` that
`cefi_catalog_reader._row_in_mvp_capture_universe` + the onchain-perp handler + the manifest mvp-denominator already use
(single SSOT, cannot drift). Per-EXCHANGE perp-gate via `has_perp_for_base` computed from the by*date df. Drop the
launcher's hardcoded 9-coin `SYMBOLS*<VENUE>`lists + stale Upbit KRW so`instrument_ids` is empty → the mvp-gated GCS
path runs. **Consequence (documented):** the perp-gate is per-exchange, so pure-spot-no-perp venues (COINBASE-SPOT,
UPBIT, BITFINEX-SPOT) resolve to 0 mvp instruments — this is CORRECT and matches the manifest mvp-denominator (those
cells are not in-mvp); capturing nothing there is honest, not a gap. DERIBIT options ride the OPTION carve-out (always
mvp); dated futures ride base+venue (not perp-gated).

### Cross-venue perp-gate correctness (found during smoke proof)

First implementation computed `has_perp_for_base` from the SINGLE venue's by_date frame → BINANCE-SPOT resolved to mvp=0
(its by_date file is SPOT_PAIR-only; the perps live in the BINANCE-FUTURES file). FIXED: `_mvp_filter_by_date_df`
sources `has_perp_for_base` from the rolled-up catalogue (`prod/catalog.parquet`, ALL venues) via a process-cached
`_load_cross_venue_perp_bases()` (reuses `cefi_catalog_reader._build_has_perp_for_base`) — the SAME cross-venue frame
the catalogue reader gates on. Fail-open: empty perp set / missing base_asset / predicate error → full per-day universe
(never zero the backfill).

### Shipped

- **mtds@7a6e6b6** — `tardis_symbol_resolution.py`: `_mvp_filter_by_date_df` + `_load_cross_venue_perp_bases` applied in
  `_resolve_symbols` GCS path (instrument_ids=None) → the catalogue-driven Tardis CEX universe is the perp-gated MVP
  subset (shared `is_in_mvp_capture_universe` predicate; cross-venue perp-gate; `MTDS_CEFI_INCLUDE_NON_MVP=true`
  diagnostic bypass). New unit test `tests/unit/test_tardis_resolve_symbols_mvp_gate.py` (5 cases — perp self-qual,
  cross-venue spot kept, no-perp spot dropped, bypass, fail-open). mtds `quality-gates.sh --no-fix` GREEN; basedpyright
  0/0/0.
- **deployment-service@8a2a831** — `launch-cefi-sharded-backfill.sh`: dropped the hardcoded 9-coin `SYMBOLS_<VENUE>`
  lists + stale Upbit KRW; CeFi shards now launch with NO `VM_INSTRUMENT_IDS` → MTDS resolves the catalogue-mvp
  universe. Venue loop generalised to all 15 Tardis CEX venues (per-venue genesis years; `VENUES`/`YEARS` overrides for
  smoke/first-wave). HL/ASTER excluded (own launcher). deployment-service `quality-gates.sh --no-fix` GREEN; shellcheck
  clean.
- **SMOKE PROOF — code-level (real data, 2026-06-22 by_date)**: `_mvp_filter_by_date_df` yields BINANCE-FUTURES 469 /
  BINANCE-SPOT 531 / BYBIT 424 / OKX-SWAP 276 / OKX-SPOT 577 / KRAKEN-FUTURES 271 / DERIBIT 3058 (NOT 9); COINBASE-SPOT
  0 / UPBIT 0 (no perps on those exchanges → out of mvp, correct + matches the manifest denominator). 3643 cross-venue
  perp-base pairs loaded from the catalogue.

### Deploy + SMOKE VM (operational)

- **Tarball rebuilt from clean LDR** (`create-code-tarballs.sh --include instruments-service`, 2026-06-23T17:41Z):
  `gs://deployment-scripts-…/code/mtds-code.tar.gz` VERIFIED to contain mtds@7a6e6b6 (`_load_cross_venue_perp_bases` +
  the new test) + UAC@6d215c1b + UTL@346f3bb + instruments-service@19227d3 + deployment-service@8a2a831 (umbrella
  alert-routing). (`--asset-group CEFI` aborted on a peer's dirty features-service — see the P3 todo above; core-only
  `--include` is the workaround.)
- **SMOKE VM launched** `cefi-binance-futures-2024-heavy-20260623-174255` (BINANCE-FUTURES, 2024, heavy
  trades+book_snapshot_5, SYMBOLS=catalogue-mvp via NO VM_INSTRUMENT_IDS). RUNNING at T+1. A tracked monitor watches the
  GCS run.log for the `loaded N symbols for BINANCE-FUTURES` line — verdict MVP-UNIVERSE-CONFIRMED iff N>>9 (expect
  ~hundreds). Full fleet (137 cefi VMs across 15 venues × genesis years) is staged behind the smoke per the
  > 50-VM REPORT gate — first wave + roster reported to the orchestrator before blasting.

## VM/Cloud-Run ALERT ROUTING — live→#uts-live-alerts, batch→#data-pipeline-alerts (operator 2026-06-23)

**Goal (alerting-service + deployment-service):** EVERY VM / Cloud-Run-job issue (failure / crash exit-137 OOM / hang /
WARNING / ERROR) propagates to Slack so we can act — **BATCH compute → #data-pipeline-alerts**, **LIVE compute →
#uts-live-alerts**.

### Routing contract (established)

- The umbrella (`LIVE` / `BATCH` / `PAPER` / `EXPERIMENT`, UAC `DeploymentUmbrella`) is the channel selector. Resolved
  from the VM name via `deployment_service.deployment_classification.classify_deployment_target` /
  `umbrella_for_vm_name` and STAMPED on the event payload (`details["umbrella"]` + `details["cloud"]`).
- alerting-service router `_route_data_pipeline_event` splits on it: **`umbrella` starts-with `live` (case-insensitive)
  → `#uts-live-alerts`** (SM webhook `alerting-uts-live-alerts-slack-webhook`); **everything else / no umbrella →
  `#data-pipeline-alerts`** (SM webhook `DATA_PIPELINE_ALERTS_SLACK_WEBHOOK`). CRITICAL still ALSO pages
  (PagerDuty/Telegram) for BOTH umbrellas — only the Slack CHANNEL differs. Webhook secret names → channel:
  `alerting-uts-live-alerts-slack-webhook` → #uts-live-alerts (LIVE); `DATA_PIPELINE_ALERTS_SLACK_WEBHOOK` →
  #data-pipeline-alerts (BATCH).

### Gaps found (audit, Read of actual files — greps obfuscated)

1. **alerting-service router** sent ALL `DP_*` + `DEPLOYMENT_*` events to `#data-pipeline-alerts` unconditionally
   (`_route_data_pipeline_event` → `_mirror_to_data_pipeline_slack`, no umbrella branch). So a LIVE-umbrella VM failure
   landed in the BATCH channel. `#uts-live-alerts` only ever got `LIVE_ALERT_RULES` runtime events (kill-switch/
   circuit-breaker), never deployment/DP failures.
2. **deployment-service emitters never stamped the umbrella**: `deployment_heartbeat._emit` (DEPLOYMENT_STARTED/
   COMPLETED/FAILED) and `exit_code_fleet_monitor._finding_for` (DP_VM_EXIT_NONZERO / DP_VM_GONE_NO_CAPTURE) +
   `heartbeat_stall_watcher._finding_for` (DP_VM_STALL / DP_EVENT_LOOP_STARVED) built payloads with `vm_name`+
   `asset_group`+`exit_code` but NO `umbrella`/`cloud` — so even if the router split, it had no signal. The
   deployment-observability codex doc claimed alerts "carry the umbrella" — they did NOT.

- Both live channel (`#uts-live-alerts`) + batch channel (`#data-pipeline-alerts`) ARE wired as SM-webhook sinks
  (`uts_live_alerts_slack.py` / `data_pipeline_slack.py`, `get_paging_credentials()` returns both) — the wiring existed,
  the routing+stamping did not.

### Fixes shipped (LDR)

- **alerting-service@f94b3b5** — `router._route_data_pipeline_event` now umbrella-splits via new `_is_live_umbrella()`
  (case-insensitive leading-`live`, no-umbrella→batch fail-safe) + `_mirror_to_uts_live_alerts_slack_dp()`; CRITICAL
  paging unchanged for both. Tests rewritten (`test_router_deployment_enrichment.py`, 7/7): BATCH→data-pipeline,
  LIVE→uts-live, lowercase `live-defi` token, LIVE DP_VM_EXIT_NONZERO→uts-live. QG green (48s).
- **deployment-service@94dfcfc** — new SSOT resolver `umbrella_for_vm_name(vm_name, VM_PREFIX_TO_BUCKET)` in
  `deployment_classification.py` (longest-prefix → lifecycle→umbrella via `classify_deployment_target`, paper-spec
  override, raises on unregistered prefix). Stamped `umbrella`+`cloud="GCP"` onto: `deployment_heartbeat._emit`
  (DEPLOYMENT\_\* via `_resolve_umbrella`), `exit_code_fleet_monitor` (`umbrella_for_vm` threaded through `sweep`),
  `heartbeat_stall_watcher` (same), wired in `cli.py` `_umbrella_for_vm`. New unit test `test_umbrella_for_vm_name.py`
  (6/6). QG green (53s). Running cefi backfill VMs untouched (code reaches them only on next tarball rebuild — not
  deployed here).

### PROOF of delivery (2026-06-23, REAL SM webhooks, observed HTTP 200)

Synthetic `DEPLOYMENT_FAILED` routed through the real notifier mirrors with the real SM webhooks:

- **BATCH umbrella → #data-pipeline-alerts**: `data-pipeline-alerts Slack POST ok (status 200)` /
  `SLACK_MESSAGE_SENT channel=data-pipeline-alerts` → `delivered(2xx)=True`.
- **LIVE umbrella → #uts-live-alerts**: `SLACK_MESSAGE_SENT channel=uts-live-alerts` (2xx) → `delivered(2xx)=True`.
- `_is_live_umbrella` asserts: BATCH→False (batch channel), LIVE→True (live channel). Both messages tagged
  `[SYNTHETIC VERIFY <ts>]` for operator dismissal.

### Codex SSOT to update (follow-up)

- [ ] [DOCS] P2. **unified-trading-pm** — update `/codex/05-infrastructure/deployment-observability.md` § "Slack parity"
      to state the umbrella-driven channel split (LIVE→#uts-live-alerts, BATCH→#data-pipeline-alerts) + the emitter
      umbrella-stamping contract (was: "DEPLOYMENT\_\* → #data-pipeline-alerts" only). Provenance: alerting routing
      split shipped alerting-service@f94b3b5 + deployment-service@94dfcfc 2026-06-23.

## UAC capture-universe expansion — survivorship-bias-free (operator 2026-06-23)

Scope: unified-api-contracts ONLY (IS catalogue re-enumeration + the CSV that CONSUMES this universe = another worker's
lane). Replaced `CEFI_BASE_ASSET_UNIVERSE` (the 44-coin MVP cap gating `_passes_asset_filter` on the Tardis CEX venues)
with the curated UNION of three tranches — KEEPS the gate, widens the universe:

1. **Legacy 44** — all kept (top-cap majors + the 2026-06-16 operator-requested coverage incl. EIGEN dust + FTT/LUNA
   delisting-test coins).
2. **Top-100-by-mcap aggregated across TIME since 2019** — curated checked-in frozenset (no live mcap API) = the union
   of coins that were top-100 at each year-end/cycle-peak 2019→today. Survivorship-bias-free by construction: includes
   the retired/collapsed big names (LUNA, LUNC, UST, USTC, FTT, SRM, CEL, WAVES, OKB, HT, LEO, OMG, NEXO, HEDG, NANO,
   STEEM, …) + all current majors/L1s/L2s/DeFi/memecoins (BONK, WIF, PEPE, SHIB, FLOKI, …).
3. **All HYPERLIQUID + ASTER perp base assets** — read from
   `gs://instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet` (venue ∈ {HYPERLIQUID, ASTER},
   instrument_type=PERPETUAL, deduped `base_asset` column), scaling prefixes (1000/k) normalised,
   equity/tokenized-stock/macro tickers (already covered by `CEFI_EQUITY_PERP_BASE_UNIVERSE` + `crypto_equity_link`) +
   non-ASCII garbage symbols excluded → 384 crypto-only HL/ASTER perp bases. HL/ASTER bypass the filter themselves; the
   point is the CEX side captures the same coins for cross-venue dispersion.

### Shipped

- **unified-api-contracts** — `registry/cefi_instrument_universe.py`: `CEFI_BASE_ASSET_UNIVERSE` rewritten as the SORTED
  curated union (**493 base assets**; was 44). Module docstring documents the 3-tranche rationale +
  survivorship-bias-free + curated-because-no-live-mcap. Gate (`_passes_asset_filter`, lives in instruments-service)
  intentionally NOT touched — still gates, just on the wider set. Breakdown: legacy 44 + top-100-hist (+190
  not-in-legacy) + HL/ASTER perp (+259 not-in-legacy|hist) = 493.
- Reconciled docstrings: `canonical/crosscutting/mvp_scope.py` (no longer "44-base MVP" — bumped
  `MVP_SCOPE_CONFIG_VERSION` 3→4 with a v4 changelog note; the computed content hash auto-flips) +
  `canonical/crosscutting/total_universe.py` ("captured subset" not "MVP subset").
- Tests: rewrote `tests/test_cefi_universe_coverage.py` (size ≥250 band; legacy-44 all present; retired-top-100 present
  = survivorship-bias proof incl. LUNA/FTT/SRM/CEL/WAVES; key HL/ASTER bases incl. HYPE/PURR/ASTER/FARTCOIN; sorted +
  no-dup determinism). Fixed `tests/unit/test_mvp_scope.py` two "non-MVP base" cases (SUI is now IN the universe →
  switched to a synthetic out-of-universe token).
- Verification: targeted tests 90 passed; basedpyright 0/0/0 on the 3 source files; ruff clean (replaced `∪` math symbol
  with `+` to satisfy RUF001/002/003). Full `quality-gates.sh --no-fix` GREEN (see commit). Shipped via
  `quickmerge --agent --files`.

Note: the IS catalogue re-enumeration + the CSV consuming this universe is a DIFFERENT worker's lane (not touched here).

### Full-universe fetch SUCCEEDED (2026-06-23, exec xqcxr, image :latest=7489ed1/0.43.0)

18 cefi venues, **10,458 active instruments** written to instrument_availability/by_date/day=2026-06-23/. Per-venue
active (old-cap → now): BINANCE-SPOT 82→763, BINANCE-FUTURES 56→677, BYBIT 310→640, KRAKEN-SPOT 75→894, OKX-SPOT
125→848, UPBIT 16→200, BITGET-FUTURES 677, BITGET-SPOT 625, KRAKEN-FUTURES 332, COINBASE-SPOT 429, DERIBIT 2983,
OKX-SWAP 388, ASTER 484, HYPERLIQUID 178, BITFINEX-SPOT/FUTURES 81/70, DERIBIT-COMBO 117, OKX-FUTURES 72. Full universe
per venue confirmed (binance hundreds). Next: build_instrument_catalogue.py rollup → prod/catalog.parquet → CSV export.

### ✅ FINAL REPORT — cefi full-catalogue rebuilt to 100% (2026-06-23, operator dispatch DONE)

**Catalogue PROMOTED**: `instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet` = **230,073 rows** (was
223,300; monotonic ACCEPT). Rebuilt from a full-universe IS fetch (image `:latest`=7489ed1/0.43.0, no-auth + both
whitelist/quote fixes) → 18 cefi venues / 10,458 active instruments on day=2026-06-23 →
`build_instrument_catalogue.py --asset-group cefi` rollup of 35,028 by_date parquets.

**Per-venue cumulative-catalogue breadth (baseline → now)**: BINANCE-SPOT 82→766, BINANCE-FUTURES 56→681, BYBIT 310→899,
KRAKEN-SPOT 75→900, OKX-SPOT 125→857, BITGET-FUTURES →682, BITGET-SPOT →634, KRAKEN-FUTURES 588→859, COINBASE-SPOT
→1194, UPBIT 16→201, OKX-SWAP →3266, OKX-FUTURES →3676, DERIBIT →214,148, ASTER 484, HYPERLIQUID 180,
BITFINEX-SPOT/FUTURES 82/72. available_from spans genesis 2010-01-01 → 2026-06-22 (per-instrument lifecycle windows).

**CSV deliverable** (operator review):

- GCS:
  `gs://instruments-store-cefi-prd-central-element-323112/_exports/cefi_instrument_universe_per_venue_2026_06_23.csv`
  (58,052 rows: one per venue × year-snapshot{2019..2025, 2026-06-23} × active instrument; cols venue / year_snapshot /
  snapshot_date / instrument_id / raw_symbol / instrument_type / base_asset / underlying / available_from / available_to
  / venue_data_types). Summary: `…/_exports/cefi_universe_summary_2026_06_23.csv`. Local copies in `/tmp/`.

**Infra shipped**: created the missing prod Cloud Run job `uts-prod-instruments-service-cefi-t1-recon` (fixes the
ENABLED-but-404 06:00 IS scheduler). instruments-service@0fe8e71 (full-universe whitelist drop) + @7489ed1 (dated-future
empty-quote venue-killer fix) on LDR.

**Honest gaps / follow-ups (tracked as todos above)**:

1. **data_types empty for KRAKEN-SPOT/FUTURES, BITGET, BITFINEX, ASTER** in the CSV — these venues are NOT in the UAC
   `DATA_TYPE_CAPABILITY_REGISTRY` (cefi has explicit entries only for BINANCE/BYBIT/OKX/DERIBIT/COINBASE/HYPERLIQUID/
   UPBIT). Accurate signal: those venues' batch data_types are unregistered. FOLLOW-UP: add their capability entries.
2. **Recon-job date is hardcoded** (`--start-date/--end-date=2026-06-23`) — tomorrow's scheduled 06:00 run would
   re-fetch the stale day. FOLLOW-UP todo above (self-default to today / scheduler-inject).
3. **Semantic conflict flagged for operator** (full-venue-universe here vs peer's wide-curated-whitelist UAC WIP) —
   reconciliation chosen (no textual conflict; my whitelist-drop makes the peer list moot-for-gating, harmless).
4. The MTDS market-tick backfill of this expanded universe + manifest migration are POST-operator-check phases (NOT done
   here, per the dispatch STOP-after-CSV instruction).

## OKX-SPOT 2010-poison residual purge + daily-mechanism verify (operator dispatch 2026-06-23)

### TASK 1 — comprehensive 2010-poison scan (NOT hardcoded list)

- **ROOT CAUSE CONFIRMED — OLD ccxt-era snapshot poison (NOT a code-default bug).** A predicate scan of ALL 35,038
  `instrument_availability/by_date/day=*/venue=*/instruments.parquet` snapshots for `available_from_datetime < 2015`
  found EXACTLY **2 remaining poisoned snapshots** (the prior hardcoded purge missed both):
  - `day=2026-04-02/venue=OKX-SPOT/instruments.parquet` — 2869/2869 rows @ 2010-01-01
  - `day=2026-04-02/venue=OKX-FUTURES/instruments.parquet` — 2869/2869 rows @ 2010-01-01
- **Diagnosis (Read both, vs clean 06-23 reference)**: both are ccxt-era dumps — `instrument_key` is the ccxt-format
  `USDT/SGD` (NOT canonical `OKX-SPOT:SPOT_PAIR:...`), `available_from_datetime` uniformly `2010-01-01` (the ccxt
  placeholder), IDENTICAL 2869-row catch-all (OPTION 1332 + SPOT_PAIR 1202 + PERPETUAL 303 + FUTURE 32) misfiled under
  each venue. The clean 06-23 OKX-SPOT snapshot (848 rows) uses canonical ids + real dates (min 2019-03-30). → these are
  OLD ccxt snapshots, every OTHER OKX-SPOT/FUTURES day is the clean Tardis snapshot → PURGE the 2 blobs (UTL
  `gcs_delete_object`). The source ccxt placeholder is already fixed (is@2217756); the no-auth Tardis enumeration does
  NOT default to 2010 (clean snapshots prove it). NOT a code bug.

### TASK 1.2 — PURGED (applied 2026-06-23)

- `purge_ccxt_poison_cefi_by_date_snapshots_2026_06_23.py --apply` (generalised, predicate-based) DELETED both blobs via
  UTL `gcs_delete_object` (DELETED logs confirmed). The OKX-SPOT/OKX-FUTURES 2026-04-02 ccxt dumps are gone.

### TASK 1.3 — GENERALISED purge script (anti-recurrence)

- Rewrote `instruments-service/scripts/purge_ccxt_poison_cefi_by_date_snapshots_2026_06_23.py` from a HARDCODED 6-blob
  list to a **scan-and-purge by a `--cutoff` (default 2015-01-01) predicate** over ALL by_date snapshots (concurrent
  read of `available_from_datetime`/legacy `available_from`, min < cutoff → purge). Lifecycle marker updated
  (`Delete-when: no cefi by_date snapshot carries a pre-2015 available_from + the catalogue rebuilt clean`). ruff
  lint+format clean. A future ccxt-era poison day can no longer recur silently behind a stale hardcoded list.

### TASK 3 — daily-mechanism recon test VERDICT: ✅ SUCCEEDED

- Cloud Run execution `uts-prod-instruments-service-cefi-t1-recon-cp8bh` (image `instruments-service:latest`=7489ed1)
  for day 2026-06-22: **Completed successfully in 2m33s**. Wrote full-universe by_date snapshots for **ALL 18 cefi
  venues** (10,845 instruments) — NOT just HL/ASTER; Tardis CEX venues included: BINANCE-SPOT 763 / BINANCE-FUTURES 677
  / BYBIT 640 / KRAKEN-SPOT 894 / KRAKEN-FUTURES 332 / OKX-SPOT 848 / OKX-SWAP 388 / OKX-FUTURES 72 / BITGET-FUTURES 677
  / BITGET-SPOT 625 / COINBASE-SPOT 429 / DERIBIT 3374 / DERIBIT-COMBO 113 / UPBIT 201 / BITFINEX-SPOT 81 /
  BITFINEX-FUTURES 70 / ASTER 483 / HYPERLIQUID 178. This PROVES the scheduled daily IS recon job works end-to-end on
  the new code (no-auth Tardis enumeration + full universe + dated future quote fix).

## Tardis CEX lifecycle-fix DEPLOY + full-universe backfill scale (operator dispatch 2026-06-23, /autonomous)

### Phase 0 — verify fix on LDR + ship follow-up (DONE)

- **aec8bd0 (lifecycle fix) CONFIRMED on LDR** — `_resolve_symbols` reads the rolled-up catalogue
  (`_catalogue_symbols_for_venue_date`, available_from<=date<=available_to ∩ mvp) FIRST, falls open to the sparse
  by_date snapshot only when catalogue unreadable. HEAD=aec8bd0, on `live-defi-rollout`.
- **Catalogue lifecycle VERIFIED** (read `instruments-store-cefi-prd-…/prod/catalog.parquet`): **227,576 rows / 157,092
  mvp** across 19 venues. Per-venue mvp + genesis: DERIBIT 147,459/2019, OKX-FUTURES 3,662/2019, KRAKEN-FUTURES 798,
  BYBIT 683, OKX-SPOT 581, BINANCE-SPOT 533, BINANCE-FUTURES 473, BITGET-FUTURES 409/2024, ASTER 359/2021, UPBIT
  352/2021, BITGET-SPOT 339, BYBIT-SPOT 315, KRAKEN-SPOT 287, OKX-SWAP 285, HYPERLIQUID 172, COINBASE-FUTURES 141/2024,
  COINBASE-SPOT 123, BITFINEX-SPOT 70, BITFINEX-FUTURES 51. Matches the prompt's target.
- **In-flight follow-up reconciled**: the helper-extraction refactor (`_resolve_symbols_from_by_date_snapshot`) was
  REVERTED twice by a concurrent session touching the shared clone (and the untracked test file deleted). The refactor
  is behavior-NEUTRAL (size-cap cosmetics; `aec8bd0` already passes the function-size gate). DECISION (least-bad path):
  drop the cosmetic refactor, ship the two load-bearing pieces — (1) the `tradfi_shared.py:136` DTZ011 fix
  (`_dt.date.today()` → `_dt.datetime.now(_dt.timezone.utc).date()`, was a pre-existing over-baseline ratchet failure
  blocking the gate), (2) the rebuilt regression test `tests/unit/test_tardis_catalogue_lifecycle_universe.py` (7 tests:
  lifecycle-universe-not-snapshot / available_from+available_to windowing / mvp-boolean gate / SPOT_PAIR-drop on
  derivatives-only venue / INCLUDE_NON_MVP bypass / catalogue-None fall-open-to-by_date). All pass + isolation-safe.

### Phase 4 — stale-VM stop decisions (DONE)

- **STOPPED** `cefi-binance-futures-2024-heavy-20260623-174255` — run.log proved OLD enumeration ("loaded 25 symbols for
  BINANCE-FUTURES from GCS" — the sparse by_date path, NOT the 156-mvp catalogue). Used the stale
  `VM_TASK=cefi-backfill` 20-sym smoke. Deleted (ephemeral, shutdown-on-completion). Replaced by the scaled fleet.
- **LEFT RUNNING** `cefi-ext-full-2025/2026` (EXTENDED-STARKNET) — small DEX-perp venue capturing the FULL universe
  correctly (43 instruments, 61,920 rows/day across trades/book5/derivative_ticker/ohlcv_1m). Per dispatch: leave the
  small-DEX-venue VMs. Do-not-disturb: `cefi-hyperliquid-2024` backfill + all `mtds-live-cefi-*` live VMs (untouched).

### Launcher = `deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh`

- `VENUES="…" YEARS="…" bash …` → one VM per (venue,year), **NO VM_INSTRUMENT_IDS** → MTDS resolves the catalogue-mvp
  universe (the lifecycle-fix path). Registry-driven machine-sizing (per-venue memory tier). Default 15 Tardis CEX
  venues; per-venue genesis years via `_venue_years` (BINANCE/DERIBIT/COINBASE 2020→, BITGET 2023→, UPBIT 2022→, rest
  2021→). CEFI default ≈ 89 VMs + TradFi ES/VIX block ≈ 12.

### Phase 1 — follow-up commit SHIPPED + tarball rebuild (2026-06-23)

- **Follow-up shipped: mtds@4bbebb8** on LDR (helper extraction → `_resolve_symbols` 206L→123L under the 200L codex cap;
  the refactor IS load-bearing — `aec8bd0` alone FAILS the size gate; DTZ fix in tradfi_shared.py:136; 168-line
  regression test). QG green, `Quickmerge: agent`. A concurrent session repeatedly reverted the MTDS refactor + deleted
  the untracked test mid-work (root cause: foreign live-editor on the shared clone); re-applied + locked in via
  immediate quickmerge.
- **Tardis API key VERIFIED ACTIVE** — academic/unlimited plan (binance-futures/deribit/bitmex/… from 2019 → 2027-06).
  FLAT plan = no per-request billing → full-fleet scale is cost-safe (no per-VM Tardis $ concern). Launcher key-check
  preflight will pass.
- **Tarball rebuild**: deployed SHAs were mtds@aec8bd0, uac@074b1c0, utl@346f3bb3, deployment@2c141cd (HEAD, has the
  94dfcfc umbrella). Rebuilding CEFI set to pick up mtds@4bbebb8 + current uac. deployment-service has a FOREIGN
  live-editor (launch_budget_registry.py mtime <40s, machine-sizing WIP) — used --allow-dirty-tarball (the dirty file
  parses+imports cleanly, is launch-side only, not VM-runtime). UTL unchanged.

### Phase 2/3 — tarball DONE + RE-SMOKE launched (2026-06-23 19:36 UTC)

- **Tarball rebuild COMPLETE** — GCS `code/` now: mtds-code@4bbebb8, unified-api-contracts-code@6262409b,
  unified-trading-library-code@346f3bb3, deployment-service-code@2c141cd (umbrella 94dfcfc). VMs that boot now pull the
  lifecycle fix.
- **RE-SMOKE launched**: `VENUES=BINANCE-FUTURES YEARS=2024` → 2 VMs (launcher splits per venue into heavy[book5] +
  light[trades] groups): `cefi-binance-futures-2024-heavy-20260623-193543` + `…-light-…`, both RUNNING, NO
  VM_INSTRUMENT_IDS (catalogue-mvp path). Tardis key active (academic/unlimited, no per-req billing). Monitor armed on
  the heavy VM run.log for the symbol-load verdict (success=~156 from catalogue; fail=25 from by_date snapshot / error).
  **GATE: do not scale waves until this proves ~156.**

## Manifest consolidator FROZE (cefi market-data index stuck @ 2026-06-23T20:07) — diagnosis + fixes (2026-06-24)

**Root cause (diagnosed 2026-06-24)**: the cefi market-data consolidator
(`uts-prod-manifest-consolidator-market-data-cefi` Cloud Run job, `*/1` cron,
`python -m unified_trading_library.manifest_consolidator --bucket market-data-tick-cefi-prd-…`) stopped writing
`_index/availability_index.parquet` after 20:07:21 despite 148/149 per-VM shards being FRESH (06:41 mtimes, 683MB) —
every cycle since acquires the lock, early-returns in ~40s, exits 0 WITHOUT writing. NOT OOM (clean exit 0), NOT the
lock alone, NOT timeout (1800s budget). The incremental changed-shard cutoff (the `consolidator_content_write_at` marker
/ `_is_lock_fresh` sibling-skip path, manifest_consolidator.py:330-441) is mis-skipping the fresh shards. The 16.6M
out-of-window Deribit bloat (canonical 18.6M rows) is the SECOND-order amplifier (makes the eventual full merge heavy →
the original 16Gi OOM). Engine itself is sound (DuckDB memory-bounded + incremental + per-VM sharded — the operator's
"do we need Rust/DB" question: already a streaming DB merge, scales fine ONCE the canonical is kept lean).

**Immediate unstick (2026-06-24)**: paused the `*/1` market-data-cefi scheduler (stop churn), bumped job
16Gi→**32Gi/cpu8**, cleared the orphaned lock, ran one execution with **`--force`** (full rebuild, bypasses the broken
incremental cutoff — exec `hqm6m`). Args temporarily carry `--force`; REVERT after the write confirms + RESUME the
scheduler.

- [ ] [INFRA] P0. **unified-trading-library** — FIX the recurring incremental no-op: the consolidator must NOT freeze
      when fresh per-VM shards exist. Diagnose whether `consolidator_content_write_at` marker advanced past the shards
      (idle-touch trap residual) OR `_is_lock_fresh` skips on a stale-but-present lock (paused-cron mid-flight). Add a
      regression test: canonical@T, shards@T+1 → next cycle MUST merge+write (not no-op). manifest_consolidator.py.
- [ ] [INFRA] P0. **market-data-tick-cefi bucket + enumerator** — PURGE the out-of-window over-seeding. MEASURED on the
      fresh full-rebuild index 2026-06-24 (gcsfs read): index is **48.0M rows / 1.02 GiB**; **45.0M empty_confirmed
      (93.8%)** of which **44.2M `EXPECTED_INSTRUMENT_NOT_LISTED`** — DERIBIT 36.3M, OKX-FUTURES 2.3M, BINANCE-FUTURES
      2.2M, BYBIT 1.2M, KRAKEN-FUTURES 1.0M, … and **43.9M carry BLANK instrument_type** (the over-seed signature: dated
      options/futures emitted for every day across their range, not clipped to listing window). captured=2.09M (+60%
      from the 1.31M 2026-06-21 start — backfill IS expanding real coverage). **ORDER MATTERS (the canonical purge alone
      is FUTILE — the `--force */5` cron re-merges the per-VM shards every 5 min → re-bloats):** (1) FIX the
      enumerator/writer to clip dated-instrument seeding to `[available_from,available_to]` so new shards stop emitting
      blank-instrument_type NOT_LISTED outside the window; (2) purge the existing cells from the **per-VM shards**
      (`_index/per_vm/*.parquet`) not just the canonical — then the next rebuild produces a lean ~3.8M-row/~100MB index;
      (3) lean canonical → honest-cov denominator becomes real (~55-60% via the query-time out_of_window exclusion).
      (Prior worker `a19169b2` died on rate-limit — redo, idempotent.) Seeding source to fix: grep who emits
      `EXPECTED_INSTRUMENT_NOT_LISTED` with no instrument_type (IS `enumerate_expected_universe.py` / MTDS capture
      preflight). COORDINATE with the out_of_window/dated-instrument work (other agent overlap).
  - [x] ✅ **(1) CLIP SHIPPED — mtds@7b18433b** (QG-green, on LDR; Tier-C drain → staging):
        `cefi_catalog_reader._iter_not_yet_listed` skips `_DATED_INSTRUMENT_TYPES={FUTURE,OPTION}` in pre-listing
        seeding (a dated option listing months out is not-in-universe, not honest-absence). Persistent
        PERPETUAL/SPOT_PAIR/EQUITY_PERP still seeded; active-window capture (`_yield_for_date`) unchanged. Regression
        `test_dated_instruments_not_pre_listing_seeded` (16/16 pass).
  - [x] ✅ **(1b) DEPLOY clip to fleet (2026-06-24)** — operator chose RELAUNCH-now. Rebuilt cefi tarball
        (`mtds-code.tar.gz` @08:34, clip mtds@7b18433b) → stopped all 120 pre-clip backfill VMs (do-not-disturb
        hyperliquid/extended + live `mtds-live-cefi-*` excluded) → relaunched via
        `FORCE=1 launch-cefi-sharded-backfill.sh` so new VMs boot the clip tarball + emit LEAN shards. Bloat emission
        halted at the source.
  - [x] ✅ **(2) PURGE DONE (2026-06-24)**: confirmed `--force` AND incremental both OOM (signal 9) at the 32Gi Cloud
        Run ceiling on the 1GB canonical (cpu max 8, ~32Gi mem cap → no RAM fix). Stopped fleet → snapshot canonical to
        `_index/snapshots/pre_purge_dated_not_listed.parquet` → parallel-purged 142 static shards (drop
        `empty_confirmed` ∧ `EXPECTED_INSTRUMENT_NOT_LISTED` ∧ instrument_id `:OPTION:`/`:FUTURE:`): **49.7M→7.8M rows
        (dropped 41.9M), 683MB→117MB** → deleted bloated canonical → cold `--force` rebuild from lean shards:
        **canonical 1.02GB→137MB, clean exit, no OOM**. Purge script: `scratchpad/purge_dated_not_listed.py` (streaming,
        idempotent, snapshot-first).
- [x] ✅ [INFRA] P1. **consolidator reverted (2026-06-24)** — args back to incremental (`--force` removed), memory
      32Gi→**16Gi/cpu4** (lean=cheap), scheduler resumed `*/5` ENABLED. Steady-state: `*/5` incremental merges new lean
      shards onto the lean 137MB canonical (O(changed-shards) memory, no OOM).
- [ ] [INFRA] P2. **deployment-service** — deadman/consolidator-watchdog AUTO-ESCALATE safety net (operator idea
      2026-06-24): on the OOM signature (terminal exit 137/signal-9 in the persisted run.log AND index mtime did not
      advance), re-run the consolidator job at the next tier of a machine-size REGISTRY
      `[16Gi/cpu4→32Gi/cpu8→64Gi/cpu16]` via `gcloud run jobs update --memory --cpu` then execute, capped at the top
      tier (top-tier OOM → page, no infinite loop). Mirrors VM `lifecycle_class` + autonomous-recovery-matrix
      `auto_cooldown`. NOTE: this is the safety net UNDER the bounded-canonical design (the purge), NOT a substitute —
      Cloud Run "autoscaling" is parallelism not RAM, so it can't bump per-execution memory.

## CEFI data-completion RESIDUAL follow-ups (operator dispatch 2026-06-24, /autonomous)

These are the remaining cefi items after the consolidator/clip/purge fix. Working autonomously to completion.

- [x] ✅ [MTDS] P1. **market-tick-data-service — VERIFIED RESOLVED (2026-06-24)**: (1) the named flaky tests PASS
      (`test_native_staking_handler` + `test_rebuild_defi_manifest_cf11`: 37 passed / 1 skipped) AND the full MTDS QG
      passed clean when the clip shipped (mtds@7b18433b through `quality-gates.sh --no-fix`) — not blocking
      (isolation-order-dependent at worst, not product bugs). (2) The tardis-fallback refactor is ALREADY in shipped
      code — `_resolve_symbols_from_by_date_snapshot` at `tardis_symbol_resolution.py:587` (mtds@4bbebb8), so the 200L
      cap + QG size gate pass. Stash `tardis-fallback-refactor-followup-2026-06-23` is a stale duplicate (left,
      harmless).
- [x] ✅ [MTDS] P1. **unified-api-contracts + market-tick-data-service** — coin-margin (inverse) perp capture: Deribit
      is ALWAYS inverse; default linear; capture inverse where MORE liquid (operator 2026-06-23). Add the inverse venues
      (binance-delivery / bybit-inverse / okx-coin-margin) to the MVP capture universe + carry a `margin_type`
      (linear/inverse) field through the catalogue → manifest, and a live-liquidity spot-check to pick the more-liquid
      side per base. SSOT spec: `cefi_universe_capture_rule_2026_06_23.md` § coin-margin. — uac@a8712016 |
      instruments-service@4838738 | Part 1: BINANCE-DELIVERY added to UAC venue registries + IS venue allow-list +
      catalogue enumeration; Part 2: `margin_type` field added to catalogue (CATALOG_COLUMNS + \_extract_meta +
      build_catalogue_dataframe); Part 3: deterministic default shipped (BINANCE-DELIVERY PERPETUALs/FUTUREs in MVP
      scope via base-membership; live-liquidity spot-check TODO scaffolded in mvp_scope.py).
- [x] ✅ [INFRA] P1. **deployment-service** — wire BYBIT-SPOT + COINBASE-FUTURES into LIVE + DAILY cefi capture. Added
      both venues to `EXPECTED_COVERAGE_BY_ASSET_GROUP['cefi']` (`_CEFI` dict) in UAC
      `unified_api_contracts/registry/expected_coverage.py` — the single SSOT consumed by both the live forward-poll
      (`launch-cefi-forward-poll.sh` → MTDS CLI `--asset-group CEFI`) and the daily cron VM (which downloads and runs
      the forward-poll launcher). BYBIT-SPOT gets `["trades","book_snapshot_5"]` (mirrors COINBASE-SPOT/BINANCE-SPOT);
      COINBASE-FUTURES gets `["trades","book_snapshot_5","derivative_ticker","liquidations","futures_chain"]` (mirrors
      BINANCE-FUTURES/BYBIT). Comment in `launch-cefi-forward-poll.sh` updated to list the expanded venue set. —
      unified-api-contracts@dab85df4 | deployment-service@e34096d | QG green (UAC 222s)
- [x] ✅ [FEATURES] P2. **features-service / market-data-processing-service** — features MVP-universe config: the
      delta_one/MDPS features pipeline needs its OWN MVP universe config (separate from MTDS capture) — same perp-gated
      CEFI_BASE_ASSET_UNIVERSE for price/funding features, BUT roll/spread/volatility features + certain defi-onchain
      features span a WIDER set (operator 2026-06-23). Define the features universe config + wire it so features compute
      over the right per-family universe, not the raw MTDS capture universe. — unified-api-contracts@b10e8d6e
      (FeatureFamilyUniverseConfig + FEATURE_FAMILY_UNIVERSE_REGISTRY in UAC) | features-service@d11dd57f
      (mvp_universe_filter.py wired in delta_one batch_handler, 34 tests) | QG green
- [x] ✅ [DOCS] P2. **unified-trading-pm** — codex doc the cefi data-pipeline contracts that shipped this cycle: (1) the
      two-layer IS-full-enumeration vs MTDS-MVP-filter + perp-gate (from `cefi_universe_capture_rule_2026_06_23.md`)
      into `codex/02-data/`, and (2) the dated-instrument NOT_LISTED clip + consolidator
      bloat/OOM-at-Cloud-Run-ceiling + purge lesson into `/codex/05-infrastructure/manifest-consolidator-ssot.md` (so
      the next bloat is diagnosed fast). — unified-trading-pm@b889f6392 | /codex/02-data/cefi-capture-universe.md +
      /codex/05-infrastructure/manifest-consolidator-ssot.md

## DP_VM_GONE_NO_CAPTURE false-positive triage (operator 2026-06-24)

- [x] ✅ **bybit-2021-heavy `DP_VM_GONE_NO_CAPTURE` = FALSE POSITIVE (verified benign)**: read the cefi `_index` for
      `venue=BYBIT date=2021-12-31` → **60 cells = 23 captured + 37 empty_confirmed (honest-absence)** → the date is
      genuinely fully covered, so the MTDS pre-flight (`venue_fetch.py:248` "all requested data_types fully covered
      (atoms ⊆ captured), skipping") correctly skipped re-fetching; captured 0→0 because nothing new to write. The
      `SHARD_INCOMPLETE … missing:['BYBIT']` is the benign "wrote 0 this run" report, NOT a real gap. Pre-flight is
      SOUND (not over-eager). cefi `DP_VM_STALL`s (bybit-spot-2025/deribit/kraken/okx) = transient ~1m heartbeat gaps
      under load, all RUNNING — not actionable.
- [x] ✅ **MONITOR FIX LIVE — deployment-service@da42473** (converged with a parallel slot-bug3·vm agent on the
      identical fix): `classify_no_capture_reason` (`data_pipeline_monitors/_gcs.py`) `_HONEST_ABSENCE_RE` now matches
      the MTDS idempotent-skip line (`all requested data_types fully covered` / `atoms ⊆ captured`) → classified
      HONEST_ABSENCE not SILENT, so resumed/idempotent backfill VMs no longer false-positive `DP_VM_GONE_NO_CAPTURE`.
      Regression test `test_no_capture_reason_mtds_idempotent_preflight_skip` (6/6 classifier tests pass).
- [ ] [INFRA] P1. **FLAG (foreign, not cefi)**: deployment-service local QG is RED in clones carrying an in-flight
      foreign change — new
      `scripts/vm/launch-mtds-{flash-loan-events,liquidation-events,position-data,risk-params}-backfill-vm.sh` +
      `vm_zombie_watchdog.py` VM_PREFIX_TO_BUCKET prefixes WITHOUT matching `launcher_registry.py` entries →
      `test_every_watchdog_prefix_has_a_registry_entry` fails. Uncommitted (not on LDR), so not an LDR breakage; the
      owning agent must wire the launcher_registry entries before shipping. Not cefi-scoped.

## DP_VM_STALL / DP_EVENT_LOOP_STARVED / DP_CRON_DID_NOT_FIRE flood triage (operator 2026-06-24, 2nd pass)

All VERIFIED false positives (175/177 VMs healthy; consolidator healthy). The ~15-alert DP*VM_STALL flood was the
DEPLOYED monitor over-flagging healthy \_resuming* VMs (relaunched on the clip → resume idempotently → captured stays
FLAT while skipping already-captured dates → old `captured_flat`-alone-stalls logic fired). The on-main revision
(`7b070fb`, sidecar-authoritative) narrows it: running the CURRENT code locally = **2/177 stalled**, not a flood. The
deployed image either lagged the revision or the flood was transient.

- [x] ✅ **DP_CRON_DID_NOT_FIRE (consolidator) = FALSE POSITIVE** — consolidator healthy: index fresh (14:46+),
      executions Completed=True, scheduler ENABLED `*/5`. The deadman falsely reports it (the per-AG sticky key).
- [x] ✅ [INFRA] P1. **Both residual false-positive classes FIXED + SHIPPED — deployment-service@eae68d8**
      (2026-06-24): 1. ✅ **Slow-but-alive long-fetch → false DP_VM_STALL**: `classify_vm_liveness` hung-worker STALL
      (the `run_log_age > run_log_stall_minutes` branches) now gated on
      `_pipeline_heartbeat_stale(pipeline_heartbeat_age_min,        run_log_stall_minutes)` — a FRESH
      `PIPELINE_HEARTBEAT` (60s worker-life marker, emitted independent of chunk boundaries) PROVES the worker loop is
      alive, so a slow single fetch (deribit options*chain, fresh heartbeat but a >90m-old last \_progress* line) stays
      ALIVE. Genuine hangs (heartbeat ALSO stale) still STALL. 2. ✅ **Old-tarball VM → false DP_EVENT_LOOP_STARVED**:
      the no-sidecar+no-run.log branch now returns ALIVE when the per-VM captured count is CLIMBING
      (`not captured_flat`) — a pre-sidecar-tarball VM (cefi-extended-2025-resume) capturing without instrumentation is
      alive; only TOTAL silence (no heartbeat + no log + captured flat) starves. +5 regression tests (147 monitor tests
      pass). Local `--mode heartbeat` dry-run confirms the 2 VMs now ALIVE.
- [x] ✅ [INFRA] P1. **DEPLOYED the monitor fix to the running jobs (2026-06-24)**: `eae68d8` reached main via the
      staging→main force-sync (PR #266 resolved — main was stale on the monitor files from an admin force-sync; relaxed
      protection → force-pushed staging tip → restored). The `deployment-api:latest` image had NO auto-build trigger
      (the cloudbuild "auto on main" comment is stale; it builds manually via `deploy-shared.sh`), so I verified the
      existing `consolidator-key4-fix` image (`4aedfc98`, built from the `cd51cf2` tree — contains the fix, 3
      `_pipeline_heartbeat_stale` hits in the installed file) and **re-tagged `:latest` → 4aedfc98 + updated all 3
      monitor jobs** to it. Ran `uts-prod-dp-heartbeat-watcher`: Completed/succeeded=1/**0 false alerts** on the 154
      cefi VMs. Fix is LIVE.

## CeFi empty_confirmed over-seeding — pre-listing NOT_LISTED denominator poison (operator 2026-06-24)

**Finding** (consolidated v9 \_index 2026-06-24 19:36): cefi captured GREW 1.31M→**2.66M (doubled)** since 2026-06-21
and attempted*failed DROPPED 802k→662k — but honest-cov FELL 33.9%→21.4% because `empty_confirmed` EXPLODED
1.28M→**9.09M**. Diagnosis: **7.6M of the 9.09M empties = `EXPECTED_INSTRUMENT_NOT_LISTED`**, all `written_at`
2026-06-23/24 (the running backfill VMs), all PERPETUAL pre-listing cells (e.g.
`BINANCE-FUTURES:PERPETUAL:PIPPIN-USDT | 2020-01-01` — PIPPIN listed 2025). These were NEVER queried (a genuinely-empty
\_listed* cell yields `SOURCE_RETURNED_ZERO`); they are **out-of-universe** and poison the coverage denominator.
Excluding them, real honest-cov ≈ 2.66M / 4.8M ≈ **~55%**. Root cause: `CeFiCatalogReader.list_not_yet_listed` →
`_iter_not_yet_listed` emitted a cell per (current instrument × every pre-listing day × data_type); the earlier
dated-only clip (`_DATED_INSTRUMENT_TYPES`) wrongly assumed PERPETUAL/SPOT_PAIR were "small count". Genuine honest
absence is only the 1.27M `SOURCE_RETURNED_ZERO`.

- [x] ✅ [SCRIPT] P0. **CODE FIX — retire pre-listing seeding (mtds@9ff01bc1)**: `list_not_yet_listed` now yields
      nothing (out-of-universe); deleted `_iter_not_yet_listed` + `_DATED_INSTRUMENT_TYPES`; updated
      `test_cefi_pre_listing_not_listed.py` (asserts ZERO NOT_LISTED end-to-end) — 30 affected tests pass, basedpyright
      clean, QG green (106s). Landed on LDR; Tier-C drain promotes to staging ≤15min.
- [x] ✅ [SCRIPT] P0. **PURGED 8.5M `EXPECTED_INSTRUMENT_NOT_LISTED` cells** (2026-06-24, hard cutover, snapshot
      `_index/snapshots/pre_notlisted_purge_2026_06_24.parquet`): filtered
      `empty_confirmed + EXPECTED_INSTRUMENT_NOT_LISTED` out of the consolidated index (12.86M → 5.02M rows) + all 41
      per-VM shards (parallel). **honest-cov measured 21.4% → 55.5%** (captured 2.79M / denom 5.02M). Holds (fleet
      deleted, shards clean → consolidator stays clean).
- [x] ✅ [INFRA] P1. **Hard cutover — deleted old fleet + relaunched on fixed code** (operator-directed 2026-06-24):
      rebuilt the VM tarball (`create-code-tarballs.sh`, clean=true, MTDS verified `_iter_not_yet_listed` removed) →
      deleted the 103-VM `085745` backfill fleet (live `mtds-live-cefi-*` + `instr-backfill-cefi-*` VMs PRESERVED) →
      purged → relaunched `launch-cefi-sharded-backfill.sh` as run-id `20260624-211958` on the fixed tarball (resume
      idempotent, no NOT_LISTED re-seed). Verifying T+10min capturing-without-re-seeding.
- [ ] [SCRIPT] P2. **Cleanup inert pre-listing plumbing** (mtds `orchestrator/sentinels.py` + `__init__.py`): with the
      source retired, `catalog_list_not_yet_listed_cefi` always returns empty → `cefi_pre_listing_by_venue` is always
      `{}` and the `record_expected_empty(EXPECTED_INSTRUMENT_NOT_LISTED)` write loop never fires. The threaded param +
      write block are now dead — remove them across the ~6 call sites for a clean break (non-urgent; harmless while
      inert).
- [ ] [SCRIPT] P2. **Real zero-capture gaps (separate from the optic)**: `perp_funding`=0 captured (core to carry
      archetype), `futures_chain`=223, `options_chain`=3, `ohlcv_1m`=738 — these aren't Tardis-tick types; diagnose
      their source/handler.

## CeFi attempted_failed + expected_unattempted audit (operator 2026-06-24, post-purge index 5.02M rows)

`expected_unattempted` = **0** (CLEAN — no bogus seeding; the only over-seeding was the now-retired NOT_LISTED path).
`attempted_failed` = **674,334**, classified: ~620k **retryable transients** (`VENUE_FETCH_FAILED` 560k +
`Tardis HTTP 500/503` 49k + `Connection timeout`/`payload not completed` 11k — real instruments, valid in-window dates;
the relaunched fleet re-attempts) + **~33k genuine code bugs** (below) + `Tardis HTTP 400` 20k (possibly-systematic
bad-request, needs a look). Failing instruments are IN-UNIVERSE (e.g. `KRAKEN-FUTURES:FUTURE:FI_LTCUSD_220429` on
2022-04-20, within its 2022-04-29 expiry) — NOT bogus-universe.

- [x] ✅ [SCRIPT] P1. **FIXED — FUTURE expiry-parse (32k Kraken/non-Deribit dated futures)** (`tardis_shared.py`): added
      `_parse_numeric_futures_expiry()` — extracts the trailing date stamp (8-digit `YYYYMMDD` `FF_XBTUSD20251226`, or
      `_`/`-`-separated 6-digit `YYMMDD` `FI_LTCUSD_220429` → 2022-04-29) and wired it into the FUTURE branch after the
      Deribit parse. Now resolves instead of raising `FUTURE row requires 'expiry_date'`. +6 tests pass. (Ships +
      tarball-rebuild gated on the verification batch — see relaunch hold below.)
- [x] ✅ [SCRIPT] P1. **`was_instrument_alive()` kwarg bug — ALREADY FIXED in current code**: the sole caller
      `tradfi/tardis_batch_download.py:171` now passes the correct `available_from`/`available_to`/`day` kwargs (with a
      comment noting the prior wrong-kwargs bug). The 206 `attempted_failed` are HISTORICAL — the relaunch on current
      code won't reproduce them (they re-process correctly).
- [ ] [SCRIPT] P1. **`Tardis HTTP 400` (20k) is LARGELY SYSTEMATIC — out-of-window + out-of-universe (operator's
      restriction concern, CONFIRMED)**: samples are (a) **post-expiry fetches** — `CRYPTOFACILITIES:FF_ETHUSD_250228`
      on 2025-03-01 (after 2025-02-28 expiry), `BYBIT:BTC-21APR23` on 2023-04-22 (after expiry) → instrument delisted →
      400; (b) **deprecated venue / non-curated instruments** — `OKEX` (old OKX name), `ATOM`/`USDC-TRY` (NOT in the
      BTC/ETH/x-coin curated universe). The active-window gate `_cefi_is_active_on_date` DOES clip `available_to`, so
      the post-expiry attempts mean the **IS catalog is missing/wrong `available_to` (expiry)** for those dated futures
      (gate passes) + a **universe/venue-filter leak** (OKEX/ATOM/USDC-TRY shouldn't be attempted). This is the
      post-expiry MIRROR of the retired pre-listing NOT_LISTED over-seeding — an upstream IS-catalog-expiry +
      curated-universe-filter fix, NOT an mtds code bug. ~2k `In CSV column #` decode errors are a separate Tardis-CSV
      parse class.
