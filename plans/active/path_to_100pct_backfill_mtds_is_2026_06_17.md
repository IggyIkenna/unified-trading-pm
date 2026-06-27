---
doc_type: plan
title: Path to 100% — post-migration backfill across MTDS + instruments-store
summary:
  Drive post-v9-migration data backfill to 100% across MTDS and instruments-store for all asset groups, gated on the v9
  migration and IS catalog rebuild landing first.
status: active
nature: process
stage: [meta]
repos: [deployment-api, deployment-service, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [backfill, mtds, instruments, data-completion, vm-launch, 100pct, post-migration]
related: []
created: 2026-06-17
parent_epic: mtds_mdps_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 20
estimate_calibrated_ai_days: 16
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-06-17
supersedes:
superseded_by:
depends_on: [instruments_mtds_subset_consistency_remediation_2026_06_17]
source:
  - operator 2026-06-17 ("after the migration, what's left to have everything backfilled to 100% across MTDS and IS?")
  - depends on plans/active/instruments_mtds_subset_consistency_remediation_2026_06_17.md (the migration +
    manifest-honesty work)
  - { audit: plans/audit/results/instruments_mtds_subset_and_consistency_audit_2026_06_17.md }
asset_group: cross-asset
drift_direction: advance-code
---

# Path to 100% — post-migration backfill (MTDS + instruments-store)

> **🟡 GATED — starts AFTER the v9 migration lands.** This plan does NOT begin until
> `instruments_mtds_subset_consistency_remediation_2026_06_17.md` has shipped the rebuild-script fixes, regenerated the
> projections, and run `--apply` per-AG. The migration backfills NOTHING — it makes the manifest HONEST + canonical and
> gives a TRUE denominator + accurate gap list. THIS plan then drives the actual data backfill to 100%.
>
> **🟠 SECOND GATE (consolidation 2026-06-26) — market-data backfill needs a FRESH instruments catalog.** A tradfi/defi
> MTDS download against a stale catalog writes ~0 rows. I-1 `instruments_foundation_completeness` records that the IS
> `by_date` catalog is **frozen ~2026-05-21** and the **daily definition producer points at dead infra** (I-1 P0
> "rebuild the IS daily definition producer"). So per-AG market-data backfill here is gated on I-1 landing the
> catalog-rebuild + producer-rebuild for that AG — not only on the I-2 v9 `--apply`. The 2026-06-19 VM launch ran ahead
> of this; re-verify its written-row counts against the post-rebuild catalog before declaring any AG done.
>
> **🟢 VM RUNNING — Step-1 credentialed backfill LAUNCHED 2026-06-19 15:00–15:04 UTC (operator "spin up VMs + download
> everything we have credentials for", EXCLUDING cefi + SFI/Transfermarkt = BLOCKED-OPERATOR billing).** v9 `--apply` is
> COMPLETE for all 5 AGs (per `instruments_mtds_subset_consistency_remediation` + `master_data_canonicalisation`), so
> the migration-drain consolidator freeze is lifted: I RESUMED the 11 paused market-data + instruments
> consolidator/watchdog crons (`gcloud scheduler jobs resume`, asia-northeast1) and manually ran the md consolidator
> jobs (the tradfi/defi/pred/sports `_index` heartbeat was >1900s stale). **Launched (EPHEMERAL_BATCH, per-VM shard
> isolation `MANIFEST_PER_VM_SHARDS=true`+unique `VM_NAME`, self-stop at completion, zone asia-northeast1-c):** **defi =
> 7 collect-\* handler VMs** `mtds-{dex-pools,dex-swaps,liquidations}-backfill` +
> `mtds-{lst-rates,lending-indices,gas-fees,vault-share-price}-2026...` (CORRECTED — the initial 5 `--asset-group DEFI`
> unified VMs SKIP all 124 defi venues; defi market-data needs the per-data_type `collect-*` ops → deleted + relaunched
> as these 7); sports odds_api = 3 VMs `mtds-backfill-odds-{y2020-22,y2023-24-fix,y2025-26}` + api-football fixtures
> `af-backfill-20260619-150255`; prediction Polymarket = 3 VMs
> `mtds-prediction-20260619-{150326,150344(self-done), 150357}`. **tradfi NOT relaunched** — the Databento OHLCV
> backfill (CFE `XCBF.PITCH` / CME `GLBX.MDP3` / DBEQ.BASIC equities) already ran to completion today
> (`/tmp/{cfe_vx,cme,dbeq}_ohlcv_backfill_v2.log` rc=0); the running `instr-backfill-tradfi-*` IS-def fan-out extends
> the catalog and a tradfi MTDS top-up runs after it lands. Banner-removed by launcher at completion.

## Definition of 100% (read this first)

**100% = `captured` covers 100% of the COULD-EXIST universe**, i.e. `attempted_failed = 0` AND
`expected_unattempted = 0` per AG. **Honest-empty is EXCLUDED from the denominator** and is NOT a gap: pre-genesis
chains, pre-venue-launch, no-fixture days, weekends/holidays, instrument-not-listed, and documented structural gaps
(e.g. VIX/VX uncovered by Massive → Barchart+Yahoo). Formula (UTL/UI SSOT):
`% = captured / (captured + empty_confirmed + attempted_failed + expected_unattempted)` where the target is to drive
`attempted_failed` and `expected_unattempted` to zero — NOT to eliminate honest `empty_confirmed`.

> **Separate dimension — v9 `schema_version` uniformity (P3, gated on THIS fleet stopping).** "100% capture" (above) and
> "100% manifest v9" are different axes. A residual tail of pre-v9 manifest rows remains (cefi 131,034 / tradfi 6,415 /
> pred 1,454; written 2026-04-05..04-24; defi+sports already 100% v9). Re-stamping them to v9 is **HARD-gated on a
> pre-migration VM drain**, so it runs **AFTER the backfill VMs this plan launched have STOPPED** — when the fleet is
> idle, trigger the re-stamp. Owner/characterisation/run-order: `migration_verification_orphan_safety_2026_06_10.md`
> **§P3** (deferred by operator 2026-06-22).

> **Expectation-setting:** post-migration the % will JUMP vs today's dashboard even before any backfill — today's low
> numbers are inflated-missing by recon-noise (cefi 1.4M "failed" → ~88k real) + honest-empty mis-counted. Size the real
> backfill from the REGENERATED projection, not the current one.

## Step 0 (PREREQUISITE) — materialize the could-exist universe (defines "100%")

- [ ] [DATA] P0. **Run the IS `enumerate_expected_universe.py` v2 enumerator + the MTDS instruments-service pre-flight
      `record_expected_unattempted`** so every IS-listed × post-genesis × post-launch × in-coverage cell is seeded as
      `expected_unattempted` at shard grain, per AG. Until this is correct the denominator is undefined and the backfill
      is unsized. Verify: data-status shows a real `expected_unattempted` count per AG (the precise gap list). —
      instruments-service / market-tick-data-service

## Step 1 — MTDS market-data backfill (the bulk: drive expected_unattempted + genuine failed → captured)

- [ ] [DATA] P0. **CeFi** — backfill every `expected_unattempted` (instrument × venue × data_type × date) + re-fetch the
      ~88k genuine `VENUE_FETCH_FAILED`/`HTTP_429`. Run to completion on real infra; manifest-verified rows. —
      market-tick-data-service
- [~] [DATA] P0. **DeFi** — backfill the post-launch could-exist (dex*pool_swaps/state, rate_indices, utilization,
  risk_params, swaps_ohlcv*\*) for every listed protocol × chain; re-fetch the genuine failed (~41k pre-de-noise). (Most
  of the 75% "empty" is honest pre-launch/not-listed — backfill only the genuine could-exist.) — IN FLIGHT 2026-06-19: 5
  EPHEMERAL_BATCH VMs `mtds-backfill-defi-{y2021-22,y2023,y2024,y2025,y2026}-20260619-150025`
  (`launch-mtds-backfill-vm.sh --asset-group DEFI`, year-sharded, per-VM shard isolation; honest-absence preserved by
  `DefiManifestRecorder.record_zero_rows` launch-date-aware). — market-tick-data-service
- [~] [DATA] P1. **TradFi** — backfill expected_unattempted trades/ohlcv/options_chain/tbbo across venues × instruments
  × dates; re-fetch genuine failed (~6k post-de-noise). — DATABENTO OHLCV (3 datasets: CFE `XCBF.PITCH` / CME
  `GLBX.MDP3` / DBEQ.BASIC equities) ran to completion 2026-06-19 (`/tmp/{cfe_vx,cme,dbeq}_ohlcv_backfill_v2.log` rc=0,
  billing-fail-closed `--source databento`); IS-def fan-out `instr-backfill-tradfi-*` extends catalog → tradfi MTDS
  top-up after it lands. — market-tick-data-service
- [~] [DATA] P1. **Sports** — backfill odds/fixtures/stats for every canonised league × fixture × date in coverage. — IN
  FLIGHT 2026-06-19: odds_api = 3 VMs `mtds-backfill-odds-{y2020-22,y2023-24,y2025-26}-20260619-150224`
  (`launch-mtds-sports-odds-backfill-vm.sh`, tier-2) + api-football fixtures `af-backfill-20260619-150255`. SFI +
  Transfermarkt EXCLUDED (BLOCKED-OPERATOR billing — NOT launched). — market-tick-data-service
- [~] [DATA] P1. **Prediction** — backfill prediction data for every canonised market × date post-genesis (2025-03-14+).
  — IN FLIGHT 2026-06-19: Polymarket = 3 VMs `mtds-prediction-20260619-{150326,150344,150357}`
  (`launch-mtds-prediction-backfill-vm.sh`, quarter-sharded). **Kalshi gap** — see new P1 item below (adapter exists, no
  VM launcher). — market-tick-data-service
- [ ] [SCRIPT] P2. **`launch-mtds-sports-odds-backfill-vm.sh --tier` arg rejected by MTDS CLI (intermittent)** — one of
      the three 2026-06-19 odds shards (`y2023-24`) failed with
      `market-tick-data-service: error: unrecognized arguments:     --tier 2` while two siblings with identical
      `--tier 2` progressed; relaunched the window without `--tier` (`mtds-backfill-odds-y2023-24-fix-151253`, RUNNING).
      The launcher sets `VM_TIER` → the VM startup translates it to a `--tier` CLI flag the MTDS CLI does not declare.
      Diagnose whether the startup should drop the flag (CLI never accepts it) or the CLI should declare `--tier`
      (Odds-API tier selection), then fix the right side. **Provenance**: T+10 verification of the 2026-06-19 sports
      backfill. — deployment-service / market-tick-data-service
- [ ] [DATA] P1. **Prediction Kalshi launcher gap** — `KalshiAdapter` exists in MTDS
      (`market_interface/adapters/prediction/kalshi_adapter.py`, wired in the factory) but
      `launch-mtds-prediction-backfill-vm.sh` hardcodes `VM_VENUE=POLYMARKET` only, so the Kalshi prediction venue has
      NO backfill launcher and was NOT backfilled in the 2026-06-19 run. Add a `--venues` pass-through (or a sibling
      `launch-mtds-prediction-kalshi-backfill-vm.sh`) so Kalshi markets backfill alongside Polymarket; Kalshi trade-api
      (`api.elections.kalshi.com/trade-api/v2`) is keyless-public for historical reads. **Provenance**: discovered
      2026-06-19 during the credentialed-MTDS-backfill VM fan-out. — deployment-service / market-tick-data-service

## Step 2 — instruments-store backfill (IS = 100% of its could-exist; MTDS↔IS subset exactly equal)

- [ ] [DATA] P1. **Backfill IS historical listings for the venues MTDS has but IS lacks** (Kraken ~6yr,
      LIGHTER/PACIFICA/ EXTENDED, BITGET gap days — the F1/F2 remediation items) + any other IS enumeration holes, so IS
      lists every instrument that could exist on every in-coverage day. Re-run the IS daily CLI per date (never copy
      between dates). Verify: the cefi (venue,date) subset closes; IS captured/could-exist ≈ 100%. — instruments-service

## Step 3 — cross-data_type completeness (every expected data_type per listed instrument)

- [ ] [DATA] P2. **For each listed instrument, capture the FULL expected data_type set**, not just `trades`: cefi
      (trades/book*snapshot_5/derivative_ticker/liquidations/ohlcv*\*), defi (pool_swaps/pool_state/rate_indices/
      utilization), tradfi (trades/ohlcv/options_chain/tbbo), per the per-venue `venue_data_types.yaml`. Flag + backfill
      instruments that have one data_type but not the expected set. — market-tick-data-service

## Step 4 — credential-gated venues (the ONLY operator-gated piece)

- [ ] [DATA] P1. `BLOCKED-CREDENTIALS` — file the credential/subscription asks for any venue/source behind a paid tier
      whose could-exist cells can't be backfilled on free/public access (per external-data-always-available rule:
      Helius/Alchemy, Glassnode/Kaiko, Tardis, Databento, Sportradar/The-Odds-API, …). Build the adapter scaffold + unit
      tests now; status `BLOCKED-CREDENTIALS` with a named ping; backfill once the operator provides creds. This is the
      only step an autonomous agent cannot self-close. — market-tick-data-service

## Step 5 — keep it 100% (live=batch parity + continuous verification)

- [ ] [DATA] P1. **Live capture running for every AG** (batch=live: same code path) so new days land captured forward,
      not re-opening the gap. — market-tick-data-service
- [ ] [INFRA] P1. **Continuous verification green**: manifest consolidator healthy + the data-status dashboard reads
      `captured / could-exist ≈ 100%` per AG as the standing proof; alert on regression. — deployment-api / mtds

## Success criteria

- data-status per AG: `attempted_failed = 0`, `expected_unattempted = 0`, captured = 100% of could-exist (honest-empty
  excluded), for cefi / defi / tradfi / sports / prediction.
- MTDS shard set == IS could-exist set (subset closed both ways).
- Live capture keeping each AG at 100% forward; consolidator green; dashboard is the continuous proof.
- Every credential gap has a named operator ask (the only non-autonomous remainder).

## Folded-in (M-1 consolidation 2026-06-26)

> Open todos migrated here from 3 archived plans during the instruments/MTDS plan consolidation
> (`instruments_mtds_plan_consolidation_2026_06_26.md`). This survivor (M-1) is now the live home for backfill-to-100% +
> DeFi catalogue→per-pool capture + the honest-absence swallow remediation. Full detail lives in the archived sources
> under `archive/2026_06/`.

### From `defi_instrument_catalogue_and_capture_pipeline_2026_06_23` (archived — 11/22 done; 3 catalogue-filter prod-proof backfill VMs were running @mtds c9255555)

> **⚖️ RECONCILED 2026-06-26 (code-checked — overlap with I-1 resolved).** The original framing here ("build a per-day
> TVL-ranked DeFi catalogue, the SSOT MTDS reads") assumed a separate TVL artifact. **It does not exist and is not
> needed.** Verified in code: there is ONE DeFi catalogue — the lifecycle-rollup `{env}/catalog.parquet` produced by
> `build_instrument_catalogue.py` (defi APPLIED 2026-06-05; **catalogue PRODUCTION is owned by I-1**
> `instruments_foundation_completeness`, not here). MTDS reads exactly that file via
> `cli/handlers/_catalogue_filter.py`. **TVL is applied at CAPTURE time, not build time**: catalogue pools the subgraph
> returns 0 for are stamped `EXPECTED_NOT_ENOUGH_TVL` via `record_catalogue_residual_empty` (shipped @3b901087/c4c5f15).
> So the three "IS — build catalogue" P0 bullets below are SUPERSEDED — M-1 owns only the MTDS capture/filter side; the
> one genuine producer enhancement (discontinuous availability ranges) moves to I-1.

- [ ] [CODE] P3. **(→ I-1) DeFi catalogue: model discontinuous `available_from`/`available_to` ranges** — ⏸️ **NOT
      ESSENTIAL TO GET STARTED (operator 2026-06-26)**; the single first-day/last-day window per pool is fine for now.
      The single window misrepresents the DeFi liquidity-can-drop-then-recover nuance; ONLY IF drop-then-recover
      modelling later proves necessary, enhance the catalogue PRODUCER (`build_instrument_catalogue.py`) to emit
      discontinuous `(from,to)` ranges. **Owned by I-1 (catalogue production)** — listed here only as the cross-link; do
      not build a parallel catalogue. (RECONCILED FROM: `defi_instrument_catalogue_and_capture_pipeline_2026_06_23` —
      the "IS build per-day TVL snapshot / daily aggregation / single catalogue file" P0s, now superseded by the
      existing lifecycle catalogue.)
- [ ] [CODE] P0. **MTDS reads the IS catalogue as the MVP filter** (TVL-qualifying pools/day, no extra filters); capture
      the 4 DeFi data_types per-pool via VMs. FOUNDATION SHIPPED @3b901087 (per-pool
      `record_empty(EXPECTED_NOT_ENOUGH_TVL)` + helpers); REMAINING = handler-loop wiring of the residual-empty call
      after the bulk backfill measures the genuinely-low-TVL residual. Repo: market-tick-data-service. (MIGRATED FROM:
      same.)
- [ ] [CODE] P1. **risk_params (193,042 EU) has NO MTDS handler** — the only EU data_type no capture op produces.
      DECIDE: (a) add a `RiskParamsHandler` + `collect-risk-params` op (Aave/Compound/Morpho per-market params from the
      lending subgraphs) + launcher, OR (b) if risk_params is derived not captured, reclassify + stop the enumerator
      seeding 193k EU. Repo: market-tick-data-service + instruments-service. (MIGRATED FROM: same.)
- [ ] [MTDS] P1. **After capture, record genuine zeros honestly** — any catalogue pool×date the source truly returns 0
      for → `record_empty(SOURCE_RETURNED_ZERO)` with FetchEvidence (not skip-cap misses). FOUNDATION SHIPPED @08b45468
      (`EXPECTED_NOT_ENOUGH_TVL` wired in both dex handlers); residual = SOURCE_RETURNED_ZERO-with-evidence after the
      backfill measures the genuine-zero set. (MIGRATED FROM: same.)
- [ ] [MTDS] P1. **Catalogue-filter residual venue-coverage tail** — add subgraphs for catalogue venues the dex handlers
      never query (TRADER_JOE_V2/UNISWAP_V4/ORCA/KAMINO/VELODROME_V2/RAYDIUM, ~1,082 pools; no subgraph →
      BLOCKED-CREDENTIALS/known-gap, document never silent-drop) + reconcile Balancer `pool_id` (66-char) ↔ catalogue
      `pool_address` (40-hex) id form. Repo: market-tick-data-service. (MIGRATED FROM: same.)
- [ ] [VERIFY] P1. **Catalogue monotonicity check** — per-day catalogue must be monotonically ≥ the previous day for
      every (venue,chain,data_type,pool) (a drop = a bug); assert in a daily check + dump the catalogue CSV, READ it,
      report per-venue/chain/data_type counts + available_from/to distributions + growth-over-time. Repo:
      instruments-service. (MIGRATED FROM: same — two VERIFY items merged.)
- [ ] [DATA] P1. **MIGRATE-then-delete legacy GCS sibling trees** `dex_pools/` (6 obj) + `lending_indices/` (2 obj) in
      `market-data-tick-defi-prd-…` — single-day (2026-04-14) Solana live snapshots, **NOT duplicates** (the `_index`
      carries 1,044 `expected_unattempted` cells for these venues that day). Re-key each into canonical
      `raw_tick_data/by_date/day=2026-04-14/pipeline_mode=…/venue=…/data_type=…` + `record_captured` per-pool
      (EU→captured), THEN `gcs_delete_object` the 8 legacy objects. KEEP `processed_candles/` (legit fresh MDPS output).
      DO NOT blind-delete. Repo: market-tick-data-service. (MIGRATED FROM: same.)
- [ ] [QG] P1. **DEFERRED — restore `dex_swaps_handler.py` adapter-contract baseline** (QG 5.70 regression: 4 contract
      calls vs baseline 5, likely from the Phase-4 per-pool writer refactor ec877b8). Regenerate baseline ONLY if the
      current pattern is correct, else restore the missing call. Repo: market-tick-data-service. (MIGRATED FROM: same.)

### From `defi_mtds_subgraph_and_adapter_fixes_2026_06_20` (archived — 3/5 done; DEX-swaps + Compound V3 subgraph + Hyperliquid OHLCV stub SHIPPED)

- [ ] [HUMAN] P1. **BLOCKED-OPERATOR-DECISION — asset_group classification for CLOB-on-chain venues** (Lighter /
      Pacifica / Extended, at the DeFi-settlement vs CeFi-matching boundary). Option (a) fold into DeFi (current
      default); option (b) a new `clob_dex` asset_group (clean but workspace-wide vocab churn). Source issue recommended
      (b). **Decision needed before the Extended Phase-5 ships.** (MIGRATED FROM:
      `defi_mtds_subgraph_and_adapter_fixes_2026_06_20`.)
- [ ] [SCRIPT] P1. **Extended-Starknet unblocking** (gated on the classification decision above) — Starknet RPC template
      (`STARKNET_RPC_TEMPLATES` in UAC `_defi_chain_data.py`) + OHLCV adapter: (1) re-read `docs.extended.exchange` for
      a documented historical endpoint; (2) failing that, build a Starknet event subgraph against the Extended
      Settlement contract; forward-poll only if both fail. Repo: market-tick-data-service + UAC. (MIGRATED FROM: same.)

### From `mtds_honest_absence_swallow_remediation_2026_06_10` (archived — 14/17 done; P0 CF-11 transport-swallow batch SHIPPED)

- [ ] [CODE] P1. **DefiManifestRecorder pass-through** — `_defi_manifest.py` `record_empty` (:359) / `record_failed`
      (:485) forward `source=` + `asset_group="defi"` to the shipped UTL kwargs (auto-stamps single-source DeFi cells on
      non-captured rows). Repo: market-tick-data-service. (MIGRATED FROM:
      `mtds_honest_absence_swallow_remediation_2026_06_10`.)
- [ ] [CODE] P1. **GraphQL body-error swallows** (CF-11 class) — `liquidations_handler.py` subgraph `errors→return None`
      (~~:589) + Morpho `errors→empty df` (~~:778) still degrade to honest-empty after the transport fix; route to
      `record_failed`. Repo: market-tick-data-service. (MIGRATED FROM: same.)
- [ ] [CODE] P2. **polymarket_adapter `_load_instruments_from_gcs`** two inner `except Exception: pass` fallbacks
      (parquet→json→{}) — an IS-store read failure degrades to "no instruments" instead of failing loud. Repo:
      market-tick-data-service. (MIGRATED FROM: same.)
