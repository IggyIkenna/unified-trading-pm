---
title: Backfill completion playbook — instruments-service + market-tick-data + market-data-processing
status: active
audience: dev / operator
last_updated: 2026-05-01
---

# Backfill completion playbook

Goal: every asset group at 100% honest coverage for the instrument & market-data pipelines. "Honest" means `captured` or
`empty_confirmed` in the manifest with the parquet actually existing at the canonical path; nothing left at
`attempted_failed` or claimed-but-phantom.

This playbook is operational — it tells you **what to run, in what order, with which cutoffs**. It does not re-derive
the architecture; for that, follow the linked SSOT docs.

## Credentials policy

**All venue / data-source API keys live in GCP Secret Manager.** Adapters fetch them via `ApiKeyReloader` (UTL) at
runtime. Nothing local — no `.env` files with API keys, no `~/.config/...` paths checked into the repo, no inline
constants in code. When you hit a "missing key" error, the secret name is logged; double-check the secret exists in
`central-element-323112` (or the appropriate project) before assuming it's an adapter bug. Ask Ikenna if a secret needs
to be provisioned or rotated.

## Currently in flight (sports — check on these before launching new work)

A separate agent is mid-stream on the sports instruments-service work. Confirm progress before starting Phase 1
backfills so they don't collide.

- **L2 GCS rename pass** — renames on-disk parquet paths to match the canonical `league_id` already in the manifest.
  Rough scope: 108,969 ops, ~25 ops/sec on local network → ~60 min wall clock once started. The manifest itself doesn't
  change — this just makes per-league downstream readers (FSS, ML feature joins) find the file at the league partition
  the manifest claims. Verify by sampling: pick a captured row from `_index/availability_index.parquet`, follow its
  `(date, league_id, data_type)` to GCS, confirm the parquet exists.
- **4 backfill VMs running** — `af` (api-football), `tm` (transfermarkt), `sfi` (soccer_football_info), `fs`
  (footystats). All write per-league with canonical IDs via the orchestrator helper `_canonical_league_id` so paths
  cannot regress to numeric IDs at write time. List with
  `gcloud compute instances list --filter='name~"^(af|tm|sfi|fs)-"' --format='table(name,status,zone)'`.
- **Consolidator daemon** — merges `_index/per_vm/<vm>.parquet` shards into the canonical
  `_index/availability_index.parquet` every ~60s. If the headline coverage % isn't moving, check the consolidator VM is
  alive (`gcloud compute instances list --filter='name~"^manifest-consolidator"'`).
- **Headline trajectory observed this session**: 74.43% → 83.10% (band-aid) → 75.49% (band-aid removed, bare-path
  fallback gone) → 79.97% (L1 rename complete). Expected post-L2 + post-backfills: ~80%+ — the L2 doesn't change the
  manifest, only the on-disk paths, so the % may not move; what changes is per-league downstream readability.
- **Architectural state achieved**:
  - Single SSOT — canonical league_ids in BOTH manifest and on disk.
  - Orchestrator helper `_canonical_league_id` enforces normalisation at every partition write.
  - Bare-path fallback removed (no more numeric-path compatibility shim).
  - 4 active backfills filling residual gaps under the new canonical layout.

What to check before kicking off Phase 1 sports work:

1. `gcloud compute instances list --filter='name~"^(af|tm|sfi|fs|manifest-consolidator)-"' --format='value(name,status)'`
   — if any of those is still `RUNNING`, let them finish (or coordinate with the running agent) before launching new
   sports backfill VMs. Multiple concurrent VMs writing to the same league partitions can race.
2. Re-snapshot the SPORTS headline coverage in deployment-ui drilldown — if you see ≥80% captured for sports overall,
   the L2 + 4-VM run has likely completed.
3. Sample a few `(captured, sports, day, league_id, data_type)` rows from the manifest and verify parquets exist at the
   canonical path (use `instruments-service/scripts/reconcile_phantom_manifest_rows.py --asset-group sports --dry-run`
   to bulk-verify in ~5 min).

## Reference SSOT docs (read these once)

- **Manifest semantics + 3-state capture_status** —
  [02-data/availability-manifest-and-data-status.md](../02-data/availability-manifest-and-data-status.md).
- **Per-asset-group GCS path layouts** —
  [02-data/per-category-bucket-layouts.md](../02-data/per-category-bucket-layouts.md).
- **VM tarball deployment + launcher conventions** —
  [05-infrastructure/vm-tarball-deployment.md](../05-infrastructure/vm-tarball-deployment.md).
- **Backfill seed specs (per-service min_days / cold-start)** —
  [04-architecture/backfill-and-live-startup.md](../04-architecture/backfill-and-live-startup.md).
- **Schema governance (write-time validation, UAC as SSOT)** —
  [02-data/schema-governance.md](../02-data/schema-governance.md).
- **Drilldown UI + endpoints** — [02-data/data-status-drilldown.md](../02-data/data-status-drilldown.md).
- **Sports data-source coverage matrix + prediction-vs-reference league split** —
  [02-data/sports-data-source-coverage-matrix.md](../02-data/sports-data-source-coverage-matrix.md).
- **Sports schema paths + phantom audit** — [02-data/sports-schema-paths.md](../02-data/sports-schema-paths.md).
- **Sports adapter dependency order (api-football T0)** —
  [02-data/sports-adapter-dependency-order.md](../02-data/sports-adapter-dependency-order.md).
- **DeFi data type catalog** — [02-data/defi-data-types-catalog.md](../02-data/defi-data-types-catalog.md).
- **Prediction venues + sub-categories** — [02-data/prediction-schema-paths.md](../02-data/prediction-schema-paths.md).

### TradFi session learnings (2026-04-30, in-line summary)

The 2026-04-30 multi-year TradFi backfill session shipped 14 commits and resolved five pre-existing pipeline bugs. All
fixes are live in code on `live-defi-rollout`; this section is for "why does X work that way" context.

- **VM_VENUE=DATABENTO routed to nothing** — the orchestrator filters by canonical venue (CME / NYSE / NASDAQ / CBOE),
  not by data-source. Fixed by routing per-root: BTC/ETH/ES futures → CME, ETFs → NYSE, VIX index → CBOE. See
  `deployment-service/scripts/vm/launch-tradfi-backfill-vm.sh` `VM_VENUE` block.
- **Canonical instrument IDs treated as raw_symbols** — the Databento adapter must check the `.FUT` / `.OPT` suffix to
  switch to `stype_in=parent`; otherwise it sends `BTC.FUT` as a raw symbol and gets zero rows. Fixed in
  `market-tick-data-service/.../tradfi/databento_adapter.py`.
- **`--force` parsed but not threaded** — the CLI handler stored `self._force` but never passed it through to
  `process_ticks`, so `--force` re-runs silently no-op'd. Fixed in `cli/handlers/tick_data_handler.py`.
- **VM name underscores rejected by GCP** — the launcher built names like `tradfi-bf-es_opt-...` which GCE rejects.
  Normalised `_` → `-` in the launcher.
- **DBEQ.BASIC + NYSE/NASDAQ returned 0 records for ETFs** — Databento's consolidated equities feed doesn't surface
  newer spot-ETF tickers. Fixed via per-listing-exchange dataset routing in UAC `tradfi_instrument_universe.py`:
  IBIT/ETHA → `XNAS.ITCH`, GBTC/BITO/ETHE → `ARCX.PILLAR`, FBTC/FETH/ARKB → `BATS.PITCH`.

Other shipped state: VIX index migrated to canonical
`asset_group=tradfi/venue=CBOE/instrument_type=index/data_type=ohlcv_15m/VIX.parquet` (1,585 days; legacy path wiped);
combo bundling collapsed ~13M legacy per-combo parquets into ~36k bundled per-underlying `ticks.parquet` files via 5
year-sharded GCE migration VMs (~170× file reduction); TradFi data-types canonical set is `{ohlcv_1m, trades, tbbo}`
(mbp_10 + quotes both dropped); phantom recon flipped ~8,300 stale `captured` rows to `attempted_failed` across 3
passes.

## Known gotchas (silent failures the dev should watch for)

These have bitten previous sessions. They fail quietly — no stack trace, just empty output or a missing field.

- **`validate_api_keys_for_venues` expects canonical venue names, not data-source slugs.** Pass `UNISWAPV3-ETHEREUM`,
  `AAVEV3-ETHEREUM`, etc. — NOT `thegraph` / `databento`. Returns an empty dict silently when given the wrong shape, so
  downstream adapters look like they're missing keys when they actually got nothing. Fixed in instruments-service
  `96867e8` for the DeFi side; reapplied the same pattern.
- **CeFi VM `rc=137` (OOM-kill) does NOT write `EXIT_STATUS`.** `atexit` handlers don't fire on `SIGKILL`, so the
  startup-script wrapper never logs the failure code. Symptom: VM ends, no `EXIT_STATUS` line in `run.log`, manifest
  shows nothing for the half-completed shard. Diagnose by checking `dmesg | grep -i kill` on the VM (if still alive) or
  via Cloud Logging `kernel: ... oom` queries. Bump machine type or shard year-by-year.
- **Tardis bulk grouped `FUTURES` request returns empty.** The Tardis bulk endpoint silently returns nothing for the
  `FUTURES` group; you must enumerate per-instrument and fan out. The CeFi launcher already does this but if you write a
  new adapter, don't trust the grouped path.
- **Concurrent VM boots can race on the deadsnakes PPA.** Symptom: ~3 of N parallel VMs hang at `python3.13` install.
  Mitigation: kill the hung VMs and relaunch one-at-a-time, or stagger boots ≥30 s apart. The setup script already
  serialises within a single VM.
- **GCS sentinel-lock needs proactive stale cleanup.** `if_generation_match=0` deadlocks against any preexisting blob,
  so the freshness check MUST `blob.delete()` before falling through to acquire — otherwise stale-recovery is
  unreachable and the consolidator (or any other singleton) silently stops working. Fixed in UTL `9d7962ce`; flag if you
  copy the pattern elsewhere.
- **Tarball install pins the VM to local `pyproject.toml` floors.** VM tarball install runs
  `uv pip install --no-sources -e <local-dir>`, so version floors in dependent repos' `pyproject.toml` are irrelevant
  for VM-deployed services. Cloud Run Jobs (consolidator, DeFi collection, deployment-api) use the MTDS Docker image
  with a `unified-trading-library:latest` base — those need a Docker rebuild after a UTL change, not a tarball refresh.
  Tarball refresh: `bash deployment-service/scripts/vm/create-code-tarballs.sh --all` (or `--asset-group <X>`).

## Cutoffs

### Global (upper bound on history)

| Asset group | Earliest day to attempt | Why                                                                                                                               |
| ----------- | ----------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Sports      | **2020-06-01**          | First odds_api data lands ~2020-06-06; rest of pipeline only useful with odds available                                           |
| CeFi        | **2019-01-01**          | Tardis/Binance/etc. coverage good from 2019                                                                                       |
| TradFi      | **2019-01-01**          | Databento equities/futures back to 2003+, but no need before 2019 for our strategies                                              |
| Prediction  | source-launch date      | POLYMARKET 2020-06-12, KALSHI 2021-07-19 (per `unified_api_contracts.canonical.coverage_starts.PREDICTION_SOURCE_COVERAGE_START`) |
| DeFi        | per-protocol launch     | Aave V3 2022-03-16, Uniswap V3 2021-05-05, etc. — `DEFI_SOURCE_COVERAGE_START` SSOT                                               |

### Secondary (shard-level — was data even possible)

The shard concept differs per asset group; the launcher + manifest writer must respect both layers so we don't flag
legitimately-empty days as missing.

- **Sports shard = (data_type, day, league_id)**.
  - **Prediction leagues** (33 leagues, `get_prediction_leagues()` in UAC) — must capture every data_type with rich
    features.
  - **Reference leagues** (40 leagues, `get_leagues_by_classification("REFERENCE")`) — only need basic api*football
    data: FIXTURES, FIXTURE_EVENTS (results-level detail), STANDINGS. Don't push for FIXTURE_FEATURES / PLAYER_VALUES /
    SFI*\* on these — those endpoints expect prediction-level depth.
  - **Per-(source, data_type) coverage starts** — `SOURCE_COVERAGE_START` + `DATA_TYPE_COVERAGE_START` in UAC
    `unified_api_contracts.sports`. Already documents `(soccer_football_info, SFI_PROGRESSIVE_STATS) = 2020-01-01`,
    `(api_football, FIXTURE_EVENTS|FIXTURE_LINEUPS|FIXTURE_STATS|PLAYER_STATS)` = 2020-06-06.
- **TradFi shard = (data_type, day, instrument)**.
  - **Per-ticker listing dates** for ETFs — `TRADFI_TICKER_COVERAGE_START` (UAC canonical/coverage_starts.py):
    IBIT/FBTC/GBTC/ARKB = 2024-01-11; ETHA/FETH/ETHE = 2024-07-23; BITO = 2021-10-19. Pre-listing days are auto-clipped
    by the launcher (`listing_date_for_root` in `cme-expiry-calendars.sh`).
  - **Futures roll forward** — no per-ticker clip needed; the parent symbol chain (BTC.FUT / ES.FUT / etc.) covers
    everything Databento has.
- **CeFi shard = (data_type, day, venue, instrument)**.
  - Per-venue inception (Binance Futures launched 2019-09, Bybit 2018-12, etc.).
- **DeFi shard = (data_type, day, venue, chain)**.
  - Per-protocol-per-chain inception. Many protocols are L2-only after a date.
- **Prediction shard = (venue, sub_category, day, market)**.
  - Per-sub-category inception. POLYMARKET crypto vs football have different starts.

## Priority order

Always start with the worst-covered data type per asset group. Per the current UI screenshot (sports — 79.9% captured,
100% attempted, 62% empty), the sub-60% items are the targets:

1. **FIXTURE_FEATURES** (0%) — never captured. P0.
2. **PLAYER_VALUES** (2%) — Transfermarkt; per-player. P0.
3. **SFI_LEAGUES** (14%) — soccer_football_info reference. P0.
4. **SFI_PROGRESSIVE_STATS** (15%) — progressive endpoint, 2020-01-01 cutoff. P1.
5. **MATCHES** (18%) — spot-check before relaunching; this is the API_FOOTBALL match endpoint and should be near 100%.
   P0.
6. **TRANSFERMARKT_LEAGUES** (50%) — P1.
7. **PLAYER_STATS** (78%) — P2 (gap-fill).

Repeat the sub-60% triage for each asset group when its data-status drilldown loads. Use the deployment-ui drilldown
(with the fixes from the companion plan applied) to see which data types are red.

## Per-asset-group execution

### Sports (worst-coverage first)

For each P0/P1 data type:

1. **Identify the source + the expected league set** via
   [02-data/sports-data-source-coverage-matrix.md](../02-data/sports-data-source-coverage-matrix.md) Table 2.
2. **Apply the prediction-vs-reference league filter** — for non-prediction leagues, only attempt FIXTURES +
   FIXTURE*EVENTS + STANDINGS. Skip FIXTURE_FEATURES / PLAYER_VALUES / SFI*\* / understat for reference leagues.
3. **Run the relevant backfill VM** —
   `deployment-service/scripts/vm/launch-{api-football|footystats|understat|transfermarkt|openmeteo|sfi}-backfill-vm.sh`.
   Each launcher has `--league` / `--data-type` / `--start-date` /`--end-date` filters; combine to scope tightly.
4. **After completion, run phantom recon** — `instruments-service/scripts/reconcile_phantom_manifest_rows.py` to flip
   stale captured-no-parquet rows to `attempted_failed` (then re-run; idempotent).
5. **Verify in deployment-ui** — drilldown should show data type green or yellow with `empty_confirmed` for the
   legitimately-empty leagues.

### CeFi (Tardis + Binance + Bybit + OKX + Hyperliquid)

1. From **2019-01-01 → today**, sharded per (venue, year, instrument).
2. Use `launch-cefi-sharded-backfill.sh` (366-VM rollout pattern; SSOT in
   [05-infrastructure/vm-tarball-deployment.md](../05-infrastructure/vm-tarball-deployment.md)).
3. Existing rollout `run-ts=20260429-154202` covers options+futures combined; verify completion + gap-fill any
   `attempted_failed` shards.

### TradFi

1. **Already substantially complete** per `project_tradfi_backfill_session_2026_04_30.md` memory: BTC/ETH crypto-basis
   (2022..today + heavy May 2023 + Jun 2024), ES futures + ES_OPT 11 chains, IBIT/ETHA/GBTC/ETHE/FBTC/FETH spot ETFs,
   VIX index migrated to canonical path, combo bundling fixed + 5 year-sharded migration VMs ran.
2. **Per-ticker listing-date clip is shipped** — `TRADFI_TICKER_COVERAGE_START` (UAC) + launcher `listing_date_for_root`
   clip. Pre-listing days no longer counted as missing.
3. **Outstanding**: VIX futures full-tick chain (UAC `_CBOE_INSTRUMENTS = []` + declarative VX contract calendar —
   separate plan); MBP_10 (deep book) if microstructure strategy needs it.

### Prediction

1. **POLYMARKET**: from 2020-06-12 (Polymarket launch date in `PREDICTION_SOURCE_COVERAGE_START`).
2. **KALSHI**: from 2021-07-19 (launch).
3. Per-sub-category cutoffs (crypto / macro / football) for POLYMARKET — see
   [02-data/prediction-schema-paths.md](../02-data/prediction-schema-paths.md).

### DeFi

1. Per-protocol-per-chain inception dates from `DEFI_SOURCE_COVERAGE_START` (UAC).
2. Use the `collect-evm-defi` / `collect-dex-swaps` CLI handlers (NOT the `download` operation — DeFi venues are in
   `VENUE_TO_ASSET_GROUP['defi']`).

## How to verify completion

A data-type is "done" when:

1. Drilldown shows ≥99% captured + empty_confirmed for the secondary-cutoff denominator (i.e. only counting (data_type,
   day, league/instrument/venue) tuples where data was actually expected).
2. Schema modal in the UI returns the same columns as the registered `SchemaDefinition` in the service code (write-time
   validation has been running so this should match by construction).
3. `instruments-service/scripts/reconcile_phantom_manifest_rows.py --dry-run` reports zero phantom flips for that
   data_type.
4. CSV download from the drilldown returns >0 rows when the shard is captured.

## Pre-requisites that block execution today

The drilldown UI has known bugs that make this playbook hard to execute. They are tracked in the active plan
`plans/active/instruments_and_market_tick_data_completion_2026_05_01.plan.md`:

- CSV download returns headers-only (won't verify shard content).
- Day-shard list capped at 60 days (can't see the rest of a 2,500-day window).
- League/day → fixture drilldown for sports has an aggregated-day-CSV button not wired up.
- Market-tick-data and market-data-processing are split across separate views instead of a unified one.

Fix these first or work around them by querying the backend directly during backfill execution.
