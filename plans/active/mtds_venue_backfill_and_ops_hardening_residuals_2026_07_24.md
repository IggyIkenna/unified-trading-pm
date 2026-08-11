---
doc_type: plan
title: MTDS venue onboarding + ops-hardening residuals
summary: >-
  Split 3 of 3 from instruments_mtds_subset_consistency_remediation_2026_06_17.md (2026-07-24 line-cap remediation,
  clean-partition). Carries the venue-onboarding + operational-hardening workstreams that accumulated inline in the
  parent during its 2026-06-18..2026-07-13 autonomous drives -- per-venue instrument backfill/diagnosis (Kraken,
  Lighter-zkSync, Pacifica-Solana, Extended-Starknet, Bitget, Drift, Aave_v3-Optimism, Deribit-Combo), the Databento
  subscription contract, Kalshi + SFI/Transfermarkt credential onboarding, the sports E2E twin-migration drive,
  gas-fees/SFI ops-hardening (VM parallelisation, rate-limit fixes, consolidator coverage), and the TradFi ICE/CME +
  DeFi EIGENLAYER legacy chain-tail fixes.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [deployment-api, deployment-service, e2e-testing, features-service, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags:
  [
    instruments,
    mtds,
    venue-onboarding,
    ops-hardening,
    backfill,
    manifest,
    sports,
    defi,
    tradfi,
    credentials,
    vm-launcher,
  ]
related:
  [
    /plans/archive/2026_07/mtds_venue_backfill_and_ops_hardening_residuals_history_2026_07_24.md,
    instruments_mtds_subset_consistency_remediation_2026_06_17,
    instruments_store_cf_canonicalization_single_walk_2026_07_24,
    instruments_mtds_consistency_remediation_residuals_2026_07_24,
    plans/audit/results/instruments_mtds_subset_and_consistency_audit_2026_06_17.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
  ]
created: "2026-07-24"
parent_epic: instruments_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
last_updated: "2026-08-11"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  [
    "instruments_mtds_subset_consistency_remediation_2026_06_17.md (split 3 of 3, plan-hygiene line-cap remediation,
    2026-07-24)",
    "plans/active/issues/plan_line_cap_remediation_2026_07_23.md",
  ]
drift_direction: advance-code
context_scope:
  [
    /plans/epics/instruments_master.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    instruments-service/scripts/build_instrument_catalogue.py,
    instruments-service/scripts/enumerate_expected_universe.py,
  ]
---

# MTDS venue onboarding + ops-hardening residuals

> **Split provenance (2026-07-24).** This file is split 3 of 3 out of
> `plans/active/instruments_mtds_subset_consistency_remediation_2026_06_17.md` (2168 lines, over the 1000-line hard-fail
> cap) per `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`'s bucket-(c) clean-partition classification
> (that plan was locked `live-defi-rollout`; operator granted `[unlock-plan]` for this specific split). Content below is
> moved **verbatim** from the parent -- no rewriting, no summarization. The parent plan is trimmed to a coordination
> index pointing here + to the other 2 siblings (`instruments_store_cf_canonicalization_single_walk_2026_07_24.md`,
> `instruments_mtds_consistency_remediation_residuals_2026_07_24.md`). Four source line ranges from the parent are
> concatenated here, in original order: L216-436 (Progress Log -- B0/B1/B2 autonomous run: per-venue instrument backfill
> diagnosis), L749-838 (forthcoming credentials + Databento subscription contract), L1230-1909 (sports E2E audit +
> twin-migration drive through the Kalshi Q&A canonical parser), L2004-2168 (TradFi ICE/CME + DeFi EIGENLAYER legacy
> chain-tail fixes + the parent's own "Deferred work -- migrated to:" closing note).

> **History extraction (2026-07-24).** 8 further heading-bounded sections (2026-06-19..2026-07-13, each verified to
> contain zero open `- [ ]` checkboxes) were moved VERBATIM out of this file into
> `plans/archive/2026_07/mtds_venue_backfill_and_ops_hardening_residuals_history_2026_07_24.md` to bring this plan back
> under its own 1000-line cap (it had grown past it since the split above). Sections that mixed closed and still-open
> todos under the same heading were left in place here, in full, unsplit. See that history file for the SPORTS E2E
> twin-migration/twin-coverage/legacy-delete drive, the tradfi IS-defs VM fan-out + close-out certification, the
> gas-fees/SFI ops-hardening diagnosis, the Kalshi enablement + Q&A canonical parser, and the TradFi ICE/CME + DeFi
> EIGENLAYER legacy chain-tail verify-and-delete operations.

## Progress Log — B0/B1/B2 autonomous run (2026-06-18, dispatch)

> Operator `/autonomous` 2026-06-18: NEW Databento key live in SM `databento-api-key`, Tardis public, DeFi creds exist →
> no credential blockers. Drive B0→B1→B2 to verified completion. This log is the loop's handoff memory (no summary doc).

**Discovery (read-first, 2026-06-18):**

- **Data state** (instrument_availability/by_date latest day): tradfi=2026-06-11, defi=2026-06-11, cefi=2026-06-17 →
  ~7-day tradfi/defi gap, ~1-day cefi gap. earliest: tradfi 2020-01-01, cefi 2019-03-30, defi 2020-01-20.
- **B1 schedulers**: `lifecycle-catalogue-regen-{cefi,defi,tradfi,sports,prediction}-daily` all PAUSED (asia-northeast1,
  `0 1 * * *` UTC), last ran ~2026-06-11. Cloud Run Jobs exist (lifecycle_catalogue_scheduler.tf).
  `prod/catalog.parquet` present per AG.
- **B2 — MVP IS ALREADY CODIFIED**: `unified_api_contracts.canonical.crosscutting.mvp_scope.MVP_SCOPE` + `is_mvp()`
  (config v3) — catalogue (`build_instrument_catalogue.py`) + enumerator already consume it. The "total reasonable
  universe" = the full lifecycle catalogue (could-exist), consumed by `enumerate_expected_universe.py` v2, but is NOT a
  NAMED/codified SSOT with explicit selection axes. **B2 gap = add a sibling `total_universe` SSOT** (the could-exist
  selection axes: base_currency Ã venue Ã data_type Ã DeFi-pool-volume Ã fixtures Ã
  hardcoded-genesis-vs-download-derived) next to MVP, + a predicate the enumerator reads, so both concepts are
  explicit + distinct.
- No code tarball in `gs://deployment-scripts-…/code/instruments-code.tar.gz` (need `create-code-tarballs.sh` first).
- No instr-backfill VM currently running.

**Discovery — instrument-store state per AG (read-first, 2026-06-18 22:30 UTC; IS@02cb876 + UAC@aeae389 + subscription
guard installed):** ran the IS `--operation status` + read each `instruments-store-{ag}-prd`
`_index/availability_index.parquet`:

- **tradfi — ALREADY FULLY BACKFILLED to date (B0 effectively done for tradfi):** 11,418 captured / 256 empty_confirmed,
  cov 1.0, **0 attempted_failed, 0 date gaps.** 6 venues continuous DAILY: CME/FX/ICE/CBOE 2020-01-01→2026-06-18,
  NASDAQ/NYSE 2023-04-15(subscription start)→2026-06-18 (distinct-days == calendar-span ⇒ no missing day). The new
  3-dataset subscription guard (`assert_databento_request_allowed`, dataset-level shard-isolation) is installed on the
  IS `definition` fetch but matters only for FUTURE/forced fetches — existing tradfi instrument rows are already the
  right universe (CBOE/CME/ICE/NASDAQ/NYSE/FX), no banned datasets present. `--force` re-fetch would isolate any
  off-allowlist dataset, not hard-fail. **Verdict: tradfi B0 = COMPLETE; no backfill action needed (only forward daily
  keep-green).**
- **cefi — cov 0.999 (28,552 captured / 22 attempted_failed); real F1/F2 gaps confirmed:** KRAKEN-SPOT/KRAKEN-FUTURES
  have only 2 days (2026-06-17/18) vs earliest_venue_date 2020-01-01 → **~6yr backfill needed**; LIGHTER-ZKSYNC
  (2024-08-01), EXTENDED-STARKNET (2024-10-01), PACIFICA-SOLANA (2025-06-01) **ABSENT entirely**; BITGET-FUTURES/SPOT
  578 days from 2024-11-08 (the F2 5-missing-days). 22 attempted_failed to diagnose.
- **defi — cov 0.998 (75,706 captured / 172 attempted_failed):** 95 venues, 2020-01-20→2026-06-18. 172 failed to
  diagnose.
- **sports — high cov on most entities;** RED-by-design: SFI_LEAGUES/SFI_STANDINGS/TRANSFERMARKT_LEAGUES cov 0.000 (all
  attempted_failed — credentialed/blocked sources, see F-track). INJURIES/ODDS ~0.96.
- **prediction — NO per-AG instruments-store entry in the bucket SSOT** (`Available: CEFI/DEFI/SPORTS/TRADFI`); resolves
  to the FLAT kind `instruments-store-pred-prd-central-element-323112`. 500 captured POLYMARKET,
  2025-03-14→**2026-06-09** (9-day stale; the `--operation status` path can't read the flat-kind bucket — status-CLI
  limitation, backfill path is fine via `resolve_instruments_store_kind`).
- **The IS CLI is idempotent + manifest-driven:** a re-run on a date already fresh in the manifest SKIPs ("all N
  venues/entities already fresh — use --force"). So a backfill targets dates NOT in the manifest (the absent venues /
  Kraken history) or uses `--force` to refresh.

**B0 plan (this run):** tradfi DONE. Drive cefi F1 (Kraken 6yr + 3 absent venues) + F2 (BITGET 5d) + prediction
freshness + diagnose defi/cefi attempted_failed. Monitored local CLI per venue (idempotent, skips fresh days), streamed
to logs.

**B0 EXECUTION — 2026-06-18 ~23:00 UTC (monitored local CLI, log dir `/tmp/is_backfill_logs/`):**

- **tradfi B0 = COMPLETE** (already; no action). cov 1.0, 0 gaps, 2020-01-01→2026-06-18, 3-dataset contract.
- **cefi F1 — Kraken 6yr backfill**:
  `instruments-service --asset-group cefi --venues KRAKEN-SPOT KRAKEN-FUTURES --start-date 2020-01-01 --end-date 2026-06-18`
  — RUNNING in background (Tardis source, ~40 records/day across both venues). The LONG leg (~2,360 days Ã 2 venues,
  ~10s/day) — ETA a few hours; left to run to completion + reports its state. Idempotent (skips fresh days). Log:
  `kraken_f1.log`.
- **cefi F1 — 3 absent venues backfilled DONE/near-done**: LIGHTER-ZKSYNC (2024-08-01→, 198 instr/day),
  EXTENDED-STARKNET (2024-10-01→, 103/day), PACIFICA-SOLANA (2025-06-01→2026-06-18 ✅ **DONE**, 10/day). All via
  Tardis/native adapters, creds present, 0 errors.
- **cefi F2 — BITGET 5 missing days**: re-fetched 2024-11-08→2026-06-18 (`--venues BITGET-FUTURES BITGET-SPOT`),
  near-done, fills the F2 gap.
- **prediction freshness — ✅ DONE**: `--asset-group prediction --start-date 2026-06-09 --end-date 2026-06-18` wrote
  **12,720 records across 30 venues** (POLYMARKET CLOB full scan ~1.4M markets + KALSHI 2000) to
  `instruments-store-pred-prd` (flat kind). The 9-day stale tail (last was 2026-06-09) is now current. NOTE: the IS
  `--operation status` CLI can't READ the flat-kind prediction bucket (`get_write_bucket_name` lacks a PREDICTION
  asset_group entry) — a status-CLI display gap, NOT a backfill blocker (the WRITE path resolves via
  `resolve_instruments_store_kind`).
- **defi**: 95 venues, cov 0.998, 2020-01-20→2026-06-18 — already broadly complete; 172 attempted_failed
  (MORPHO-ETH/BASE 41 each, DRIFT-SOLANA 41, AAVE_V3-OPTIMISM 41, TRADER_JOE_V2-AVALANCHE 6, SUSHISWAP_V3-BASE 2, all
  UNCLASSIFIED_ADAPTER_ERROR, 2026-05-09→06-18).
- **sports**: most entities high-cov; SFI_LEAGUES/SFI_STANDINGS/TRANSFERMARKT_LEAGUES cov 0.000 (all attempted_failed —
  credentialed/blocked scraper sources, tracked in sports_master DEFERRED-INDEFINITELY scraper set). Not a B0 gap.

- [x] ✅ [CODE] P3. **`--operation status --asset-group prediction` can't read the flat-kind bucket** — reconciled via
      `cross_cutting_satellite_ao_dispatch_batch11_2026_08_09.md` todo 1 (2026-08-10). `_run_coverage_status` was
      already fixed at `instruments-service@086eeffe` (2026-08-03); the ADJACENT same-class bug in
      `_run_reprocess_shards` (line 295, still used `get_write_bucket_name`) was fixed in the same batch-11 pass, routed
      through `_get_instruments_bucket_for_asset_group`. Repo: instruments-service@c8e3686ca4.
- [ ] [DATA] P2. **Stale `attempted_failed` rows survive a failed→captured retry in the consolidated `_index` (manifest
      dedup blank-column edge — KNOWN, already tracked)** (surfaced 2026-06-18 while backfilling the fixed venues).
      After re-fetching a previously-`attempted_failed` shard to `captured`, the consolidated
      `_index/availability_index.parquet` carries BOTH rows for the same (date, venue) — e.g. DERIBIT-COMBO 2026-05-23
      has `attempted_failed` (instrument_type='' pipeline_mode=None) AND `captured` (instrument_type='COMBO'
      pipeline_mode='batch_instruments_service'). ROOT CAUSE (documented in UTL `manifest_writer/_writer_io.py` ~line
      716): the dedup key adds the v6-v9 shard-atom cols (instrument_type/pipeline_mode/source) only when non-empty, and
      `record_failed` leaves them blank while the captured retry populates them → populated-vs-blank delta keeps BOTH
      rows; last-write-wins fails. The captured data IS present + correct; the stale failed row inflates the coverage
      DENOMINATOR (slight under-count) until collapsed. **Already tracked** as the wildcard-"" dedup follow-on
      `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05` (the fix: treat "" as a wildcard in the dedup
      key so a populated retry supersedes a blank failure). The scheduled manifest-consolidator does NOT currently
      collapse these either (same dedup logic). **Until that lands**, a targeted reconcile (drop the stale
      `attempted_failed` row where a same-(date,venue) `captured` row with a newer `written_at` exists) would clean the
      IS instruments-store indices — but do NOT hand-edit the dedup machine here (deliberate design tradeoff with a
      named owner). — unified-trading-library (dedup) — cross-link
      `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05`
- [x] ✅ [DATA] P2. **Diagnosed all 172 defi attempted_failed cells (2026-05-09→06-18) — 4 of 6 venues fixed, 2 are
      deeper upstream changes (split below)**. Each was UNCLASSIFIED_ADAPTER_ERROR from a distinct upstream API
      change: - **MORPHO-ETHEREUM (41) + MORPHO-BASE (41) — ✅ ADAPTER FIXED + RE-FETCHED**
      (instruments-service@ec3fd3a): Morpho renamed `Market.uniqueKey`→`marketId` (HTTP 400 "Cannot query field
      uniqueKey"). Live verify: 968 markets fetched (was 0); re-fetched 2026-05-09→06-18 (164 captured rows written
      2026-06-18 23:1x). **The captured rows land under the CANONICAL bare venue `MORPHO`** (the writer keys the shard
      by the adapter's `venue` property `"morpho"`→`MORPHO`, NOT the per-record chain-suffixed `venue_tag`
      `MORPHO-ETHEREUM`) — and `MORPHO` already has **1,669 captured rows 2024-01-08→2026-06-18** (the historical
      canonical capture). So the 41+41 `MORPHO-ETHEREUM`/ `MORPHO-BASE` `attempted_failed` rows are an ANOMALOUS
      chain-suffixed venue-naming VARIANT, NOT a genuine data gap — the morpho lending markets ARE captured + current
      under `MORPHO`. (Same multi-source venue-naming drift the manifest-canonicalisation track owns — see the
      venue-naming P2 below.) - **TRADER_JOE_V2-AVALANCHE (6) + SUSHISWAP_V3-BASE (2) — ✅ SELF-RECOVERED +
      canonical-tag captured**: both fetch 1000 pool instruments cleanly (transient subgraph rate-limits, not a code
      bug). Re-fetched; captured under the canonical bare `TRADER_JOE_V2` (74 captured 2026-05-09→06-18) +
      `SUSHISWAP_V3` (2,606 captured 2023-04-05→06-18). The `-AVALANCHE`/`-BASE` chain-suffixed `attempted_failed` rows
      are the same anomalous variant — data captured under the canonical bare venue. - **DRIFT-SOLANA (41) +
      AAVE_V3-OPTIMISM (41)**: genuine deeper upstream changes — split to the two P2 todos below. — instruments-service
- [x] ✅ [DATA] P2. **DeFi manifest venue-naming drift — `_index` reconcile DONE (grain DECIDED = PROTOCOL-CHAIN)**
      (surfaced 2026-06-18, resolved 2026-06-19). The defi instruments-store `_index` carried THREE drifted spellings of
      one protocol-on-chain (bare `AAVEV3`/`MORPHO`, chain-suffixed-ghost `AAVEV3-ARBITRUM`/`MORPHO-ETHEREUM`,
      already-canonical `AAVE_V3`+chain). **GRAIN DECISION: PROTOCOL-CHAIN** — the UAC SSOT `ALL_DEFI_VENUES` is 150/159
      protocol-chain, so the canonical instrument venue grain is `PROTOCOL-CHAIN` (`AAVE_V3-ETHEREUM`), NOT bare. The
      live `_index` venue column was canonicalised 91→58 venues (71,799 rows re-pointed via the reader-SSOT
      `VenueMapping.normalize_defi_venue` resolver) + 861 captured legacy↔canonical spelling-dedup, folded into the v9
      column-population walk (instruments-service@7a63be9 → APPLIED). Captured preserved 75,942→75,081 (−861
      all-captured twins, 0 captured cell shadowed). — instruments-service
- [x] ✅ [CODE] P2. **DeFi venue-grain — align the ADAPTER/writer shard key to the decided PROTOCOL-CHAIN grain** —
      reconciled via `cross_cutting_satellite_ao_dispatch_batch11_2026_08_09.md` todo 2 (2026-08-09) — STALE PREMISE,
      already shipped `instruments-service@6b7fbadf`/`ec73983e` (2026-08-05, four days before this doc's next audit
      pass). Verified live against current HEAD: all 57 non-oracle multi-chain DeFi adapters' `venue` property +
      `InstrumentRecord.venue` + the manifest writer's `_canonical_manifest_venue_chain()` split already emit the
      canonical combined/split PROTOCOL-CHAIN form consistently; test coverage current. No code change needed. Repo:
      instruments-service (verified, no change needed) / unified-trading-library (verified, no change needed).
- [x] [DATA] P2. **DRIFT-SOLANA instrument adapter — `data.api.drift.trade/stats/markets` now 404** (diagnosed
      2026-06-18). The Drift Data API endpoint moved: `/stats/markets`→404, `/markets`→403, `/contracts`/`/perpMarkets`
      →403 (auth-gated), `dlob.drift.trade`→502. Find Drift's current PUBLIC markets endpoint (docs at
      `https://docs.drift.trade/`); if all current endpoints are auth-gated this becomes **BLOCKED-CREDENTIALS** (file a
      Drift API-key ask per external-data-always-available). Fix `drift.py` `_DATA_API_URL`/path (the URL resolves via
      UAC `get_solana_protocol_url("drift","api_url")` — update the registry value, not a hardcode), classify the breach
      properly, backfill 2026-05-09→06-18. — instruments-service / unified-api-contracts (registry URL) ✅ SHIPPED
      2026-06-19: rewrote `drift.py` to parse Drift SDK TypeScript constants on GitHub
      (`MainnetPerpMarkets`/`MainnetSpotMarkets`) via regex bracket-depth walk — 55 active perps + 73 spots. SDK URLs in
      UAC registry at `sdk_perp_markets_url`/`sdk_spot_markets_url`. Backfill ran 2026-05-09→2026-06-19 (42 dates, 40
      instruments/day). Manifest now shows `DRIFT` + `chain=SOLANA` = `captured` (42 rows). IS@87099cc, UAC@74509df.
- [x] [DATA] P2. **AAVE_V3-OPTIMISM IS instruments adapter must route to the RPC fallback (KNOWN abandoned subgraph —
      NOT a subgraph-ID hunt)** (diagnosed 2026-06-18). The instruments adapter queries the subgraph
      `3RWFxWNstn4nP3dXiDfKi9GgBoHx7xzc7APkXs1MLEgi` which raises `Type Query has no field reserves` → attempted_failed.
      **This is the DOCUMENTED operator policy (UAC `_defi.py` aave_v3 OPTIMISM comment, decision 2026-05-30): Aave
      silently abandoned the Optimism subgraph (republished to an empty v0.0.5 entity store); the CANONICAL data source
      for AAVE_V3-OPTIMISM is the RPC fallback (14-row daily), not the subgraph.** So do NOT chase a new subgraph ID
      (none exists per the policy). The fix is in the IS `aave_v3.py` adapter: for OPTIMISM, route to the same RPC
      fallback the MTDS rate handler uses (or `record_empty(reason=...)` honest-absence if the IS layer has no RPC path)
      — never leave it attempted_failed (a known-policy state masquerading as a fetch failure). The sibling chains
      (ETH/ARB/POLY/BASE/AVALANCHE) work fine. — instruments-service (NOT a UAC subgraph-ID change) ✅ SHIPPED
      2026-06-19: added static 7-reserve fallback (`_AAVE_V3_OPTIMISM_STATIC_RESERVES`) with DERIVED citations per STEP
      5.97. `get_instruments()` shortcircuits for OPTIMISM chain before subgraph call — returns 12 instruments (5
      borrowing-enabled Ã 2 = 10 + 2 non-borrowing Ã 1 = 2). Backfill 2026-05-09→2026-06-19 (42 dates). Manifest:
      `AAVE_V3` + `chain=OPTIMISM` = `captured` (42 rows). IS@87099cc.

**DERIBIT-COMBO — fixed a NEVER-WORKING venue (4 stacked breaks, found during cefi diagnosis) — ✅ SHIPPED:** cefi's 22
attempted_failed were ALL DERIBIT-COMBO (0 captured days since added 2026-05-23). Root cause = 4 stacked bugs, all
fixed: (1) Deribit retired `get_instruments?kind=combo` (HTTP 400) → switched to `public/get_combos`; (2) adapter tagged
records `venue=DERIBIT` but batch canonical is `DERIBIT-COMBO` → URDI venue-tag filter dropped all rows → fixed the
venue property; (3) legs were always empty (`_parse_combo_legs` always returned `[]`) and validation rejects leg-less
COMBOs → build `InstrumentLeg` from `get_combos` structured legs; (4) `DERIBIT-COMBO` was absent from UAC
`VENUES_BY_ASSET_GROUP["cefi"]` + `CEFI_VENUE_LAUNCH_DATES` → validation rejected "unknown venue" → registered it.
Verified live: **117 combos written/day** (was 0). Removed dead `_parse_combo_legs`/`_extract_structure_code`. Tests
updated (332 IS combo tests + 907 UAC venue/coverage tests green; IS QG `--no-fix` exit 0). Shipped:
unified-api-contracts@dfe7e6f (venue registration) + instruments-service@dedae75 (adapter). Re-fetch of the 22 failed
days running (`deribit_combo.log`) — combos active today land captured; expired-combo days the get_combos endpoint no
longer returns stay honest (the API only returns currently-active combos — historical combo state is not retrievable, an
upstream limitation, NOT a silent placeholder).

> **Dependency order (operator 2026-06-18):** (B0) backfill instruments to NO-MISSING first → (B1) regen the instrument
> catalogue (it aggregates instruments) → (B2) codify MVP-universe vs total-reasonable-universe (so the backfill config
>
> - data-status "could-exist" are correct) — these gate/inform each other. Research-data canonical-copy (B3) is
>   independent. Cross-links: `path_to_100pct_backfill_mtds_is_2026_06_17.md` (the backfill-to-100% home).

- [x] ✅ [INFRA] P1. **B3 — copy e2e research data to CANONICAL placement + e2e doc** — reconciled via
      `cross_cutting_satellite_ao_dispatch_batch11_2026_08_09.md` todo 3 (2026-08-09) — STALE PREMISE, no copy needed.
      Both the legacy research buckets and the `-prd-` twins this todo assumed existed are confirmed DELETED
      (`gcloud storage buckets describe` → 404 on all 4). The real canonical home is the SHARED
      `market-data-tick-defi-prd-central-element-323112` bucket — the dedicated `perp-funding`/`lst-rates` `kind=`
      entries were removed 2026-07-13, data already carried forward. Content-verified via targeted
      `read_availability_index` spot-check: HYPERLIQUID `perp_funding`/`perp_daily_ctx` + `lst_rates` present in the
      shared bucket. e2e doc updated with a SUPERSEDED banner recording the true final state. Repo: e2e-testing@ea38428.
- [ ] [INFRA] P1. **B1 — instrument catalogue regen + un-pause (aggregation/dedup; "has this instrument ever existed" +
      available-from/to)**: `instruments-service/scripts/build_instrument_catalogue.py` +
      `reference_data/catalogue/catalogue_builder.py` EXIST; Cloud Run jobs
      `lifecycle-catalogue-regen-{cefi,defi,tradfi,     sports,prediction}` exist but the `*-daily` SCHEDULERS are
      **PAUSED** + last ran ~2026-06-11/15 (STALE, pre-backfill). AFTER B0 (instrument backfill no-missing): re-run the
      regen jobs per AG → verify the catalogue reflects the full deduped instrument lifecycle
      (genesis/first-seen/last-seen per instrument) → decide cadence + un-pause the daily schedulers (or keep manual).
      data-status "could-exist" + the expected_unattempted enumerator (`enumerate_expected_universe.py`) read this —
      stale catalogue = wrong could-exist universe. — instruments-service/deployment-service
- [x] ✅ [DESIGN] P1. **B2 — codify MVP-universe vs TOTAL-REASONABLE-universe (NOT codified anywhere — confirmed gap)**:
      define in UAC (registry) the two distinct expected-universes so we know what we SHOULD have (drives the backfill
      config + data-status denominators): dimensions = base_currency Ã venue Ã data_type Ã (DeFi-pool by volume
      threshold) Ã fixtures (sports) Ã combinations; canonical sources = hardcoded (chain genesis dates, VIX-index) vs
      download-derived (must have had the right fetch config to cover the full universe). **TOTAL-REASONABLE** = the
      full could-exist universe; **MVP** = the subset the May-23 archetypes need. Scan
      `path_to_100pct_backfill_mtds_is_2026_06_17.md` + the current `enumerate_expected_universe.py` + UAC registry for
      how far this exists + outliers; codify the gap as a UAC SSOT both the enumerator + the backfill config +
      data-status read from. — unified-api-contracts/instruments-service — **UAC SSOT SHIPPED:
      unified-api-contracts@b654eb6** — `canonical/crosscutting/total_universe.py` (`TOTAL_UNIVERSE_AXES` per-AG
      selection-axis taxonomy with base_currency/venue/data_type/defi_pool_volume/ fixtures/combinations;
      `UniverseProvenance` HARDCODED_GENESIS-vs-DOWNLOAD_DERIVED taxonomy; `UniverseTier` + `universe_membership()`
      classifier MVP⊆TOTAL; config-version descriptor) + 9 unit tests, all exported from the UAC root facade. The
      instruments-service consumer wiring (`enumerate_expected_universe.py` reading these axes for the could-exist
      denominator) is the downstream half, tracked under B0/B1 + path_to_100pct backfill.
- [ ] [DATA] P0. **B0 — backfill instruments to NO-MISSING (prereq for B1 catalogue + all expected-universe
      consumers)**: the F1/F2 instrument backfills below + the broader could-exist instrument backfill tracked in
      `path_to_100pct_backfill_mtds_is_2026_06_17.md`. Other services rely on instruments to know what's
      available/expected → this runs FIRST. — instruments-service

## Forthcoming credentials (operator 2026-06-19 — note now, unblock on arrival)

Operator is acquiring these — record as pending-credential so the backfill runs the moment the keys land (NOT memory;
tracked here per the durable-facts rule):

- [x] ✅ **Kalshi credential UPLOADED 2026-06-19** — `kalshi-api-credentials` v1 in Secret Manager (JSON
      `api_key_id`/`key_id` + RSA `private_key` PEM; account has no funds, market-data-only). The credential-registry
      already maps `"kalshi" → kalshi-api-credentials`.
- [x] ✅ [CODE] P1. **Wire Kalshi into the pipeline (hist + live market data)** — re-verified 2026-08-11 (batch-11
      finalize twin, per its "Flagged, not extracted" note) against CURRENT code, not just the two cited prior docs:
      `instruments-service/instruments_service/reference_data/adapters/prediction/kalshi.py` fully implements RSA-PSS
      request signing (`_parse_kalshi_creds` reads both `api_key_id`/`key_id` + `private_key` from the injected
      `kalshi-api-credentials` blob; `_signed_headers` signs via `KALSHI-ACCESS-KEY`/`KALSHI-ACCESS-SIGNATURE`) —
      exactly the field-name match this todo asked to verify. MTDS carries the live half:
      `market_tick_data_service/market_interface/adapters/prediction/kalshi_adapter.py::KalshiAdapter.get_trades_with_status` +
      4 live WS connectors (`kalshi_ws.py`, `kalshi_trades_ws.py`, `kalshi_clob_ws.py`, `kalshi_perp_ws.py`) +
      `scripts/ingest_kalshi_bulk_to_canonical.py` for the hist bulk path. Corroborates the two prior-referenced docs
      (`data_completion_to_100_all_ag_2026_06_21.md` Kalshi deep-history seed backfill ran;
      `prediction_live_clob_depth_capture_2026_07_24.md` trades-adapter URL fix shipped) — the checkbox was stale, work
      is done. No code change needed. Repo: instruments-service / market-tick-data-service (verified, no change needed).
- [x] ✅ **Extended public market data needs NO API key — "operator applying for API" was a FALSE blocker for the data
      pipeline (verified live 2026-06-22).** `api.starknet.extended.exchange/api/v1/info/{markets,candles,funding}` all
      return HTTP 200 with only a `User-Agent` header (no `X-Api-Key`, no stark key). The stark private key is needed
      ONLY for order placement (post-cutover execution), never read-only market data. The placeholder SM secrets do NOT
      block instrument/candle/funding capture.
- [x] ✅ **IS Extended adapter: per-instrument genesis (honest `available_from`)** — instruments-service@9bb7cdfd.
      Probes each market's earliest daily candle (P1D `/info/candles`) and stamps `available_from_datetime`
      per-instrument instead of a single global `2024-07-26`. Genesis audited across all 103 active markets: spans
      2024-07-26→2026-05-22; **50/103 markets have candle history pre-dating their `createdAt`** (BTC/ETH from
      2024-07-26 testnet vs createdAt 2025-07-18 mainnet-migration bulk-stamp), so neither a global constant nor
      `createdAt` is honest — only the probed candle-genesis is. Fix produces 58 distinct `available_from` dates (was
      1). basedpyright clean; IS QG green (88.24% cov).
- [x] ✅ [DATA] P2. **Run the Extended public instrument + perp backfill (UNBLOCKED — no key needed)** — reconciled via
      `cross_cutting_satellite_ao_dispatch_batch11_2026_08_09.md` todo 4 (2026-08-09). Ran IS daily-listing refresh +
      catalogue rollup, then launched 13 sharded SPOT VMs (`cefi-extended-starknet-*`) covering 2024-10-01→2026-08-08
      (the real venue-launch floor for funding/trades; OHLCV was already fully captured pre-2024-10-01). Bounded per-VM
      manifest-shard verification (677 files, ~17MB) confirmed 0 date gaps and 0 remaining `expected_unattempted` across
      107,096 attempted shards. Repo: instruments-service@catalogue-rollup-cefi-20260809T203518Z +
      market-tick-data-service (13 backfill VMs).
- [x] ✅ [CODE] P2. **Harden MTDS Extended candle sharp edge (silent truncation)** — reconciled via
      `cross_cutting_satellite_ao_dispatch_batch11_2026_08_09.md` todo 5 (2026-08-09) — STALE PREMISE, already shipped
      `market-tick-data-service@3b9b27e` (2026-06-22, 48 days before this batch was authored):
      `_extended_candle_params()` already startTime-bounds the request, caps `limit`, and loudly warns on an oversized
      window. The remaining gap (a regression test) was closed: added
      `test_extended_candle_params_within_cap_no_truncation_warning` +
      `test_extended_candle_params_oversized_window_warns_loudly_instead_of_silent_truncation`. Repo:
      market-tick-data-service@f8d9033b5.
- [x] ✅ [CODE] P3. **Align/consolidate the two parallel Extended candle paths** — reconciled via
      `cross_cutting_satellite_ao_dispatch_batch11_2026_08_09.md` todo 6 (2026-08-09) — STALE PREMISE, already shipped.
      The parallel `ExtendedAdapter` (`market_interface/adapters/onchain_perps/extended_adapter.py`) was already deleted
      at `market-tick-data-service@f6bda91b` (2026-06-24, six weeks before this batch was authored). Verified against
      current HEAD: zero `extended_adapter`/`ExtendedAdapter`/`extended_base_client` references anywhere; exactly one
      candle-fetch path remains (`fetch_extended_candles` in `_umi_extended.py`). No code change needed. Repo:
      market-tick-data-service (verified, no change needed) @f6bda91b.
- Tardis: `tardis-api-key` (+ `-backup`, `-full`) already in SM — provisioned (not a gap).

## Databento SUBSCRIPTION CONTRACT (operator 2026-06-18 — supersedes PAYG model)

**No longer PAYG** — subscription + ~$150 credits (more than enough to stream all instruments). **ONE API key**
(`databento-api-key`, single-key — operator chose collapse-to-single-key) across **exactly 3 datasets**: `GLBX.MDP3`
(CME) + `DBEQ.BASIC` (Databento US Equities) + `CFE` (CBOE Futures). Any other dataset → reject.

Schema → free-window entitlement (a request's `start` must be ≥ `today − window`; clip/reject otherwise):

| Level | Schemas                                          | Free window | Guard                |
| ----- | ------------------------------------------------ | ----------- | -------------------- |
| L0    | `ohlcv-1s`, `definition`, `statistics`, `status` | 16 years    | start ≥ today − 16y  |
| L1    | `trades`, `tbbo`, `mbp-1`, `bbo-*`               | 1 year      | start ≥ today − 365d |
| L2    | `mbp-10`                                         | 1 month     | start ≥ today − ~30d |
| L3    | `mbo`                                            | 1 month     | start ≥ today − ~30d |

Codify this (schema→window table + 3-dataset allowlist) as the SSOT (UAC) + enforce as a pre-request guard in the
Databento adapter(s) — replaces the PAYG-cost-blocker framing (cost emission stays as credit-burn telemetry; the hard
guard is now entitlement window + dataset, surfaced as 403/entitlement not 402/payment). Instruments = `definition`
schema = L0 (16y window) → the instrument backfill can pull the FULL universe within the 3 datasets, cost-free within
credits. Tracked todos below.

- [x] ✅ [CODE] P1. **Databento subscription cutover (MTDS+UAC+IS)** — DONE: single-key config
      (`use_multi_key_rotation=False`, `num_api_keys=1`, `DEFAULT_NUM_API_KEYS=1`; num_keys-asserting test fixed to read
      `get_num_api_keys()`; transitional secret `databento-api-key-1` DELETED — only `databento-api-key` remains) +
      schema→free-window + 3-dataset allowlist SSOT (`databento_subscription_allowlist.py` @31db3b0) enforced as the
      pre-request guard at the MTDS get_range chokepoint AND the IS `definition`-schema fetch (with dataset-level shard
      isolation so an off-allowlist dataset doesn't hard-fail siblings). — market-tick-data-service@88d1c65e /
      instruments-service@86ecc67b / unified-api-contracts@3b76c0bc | all QG green.
- [x] ✅ [SCRIPT] P1. **B0 instrument backfill within contract**: backfill `definition` (L0, 16y) for GLBX.MDP3 +
      DBEQ.BASIC + CFE — full universe (credits cover it). — instruments-service — **ALREADY COMPLETE** (verified
      2026-06-18, instruments-service@dedae75 run): `instruments-store-tradfi-prd` `_index` = 11,418 captured / 256
      empty_confirmed, cov **1.0, 0 attempted_failed, 0 date gaps**. 6 venues continuous DAILY: CME/FX/ICE/CBOE
      2020-01-01→2026-06-18, NASDAQ/NYSE 2023-04-15(subscription start)→2026-06-18 (distinct-days == calendar-span ⇒ no
      missing day). The 3-dataset subscription guard (`assert_databento_request_allowed`, dataset-level shard-isolation)
      is installed on the `definition` fetch — banned datasets isolate (not hard-fail), existing rows are already the
      right 6-venue universe (no banned datasets present). Forward daily keep-green only. See Progress Log "B0
      EXECUTION".
- [ ] [CODE] P1. **`ohlcv-1s` has NO `BarTimeframe` member → OHLCV close-edge conversion raises** (surfaced 2026-06-18
      during the subscription cutover): the contract fetches ONLY `ohlcv-1s`, but `_OHLCV_DATA_TYPE_TIMEFRAME` (mtds
      `databento_adapter.py`) + the UAC `BarTimeframe` closed set (`bar_boundary.py` — smallest unit is `15s`) have no
      `1s`/`ohlcv_1s` entry, so `_convert_ohlcv_open_edge_to_close` raises `ValueError` for a real `ohlcv_1s` OHLCV
      write. Adding `"1s"` is a deliberate workspace-wide closed-set extension (per the `BarTimeframe` docstring: extend
      the Literal + `BAR_TIMEFRAME_SECONDS` (1s divides 86400 so the midnight-grid clause holds) + audit every
      `record_captured` OHLCV write-callsite + features-\* DAG + data-status drilldown + cluster-validation registry,
      ALL in one commit). Until landed, the OHLCV path must AGGREGATE `ohlcv-1s`→1m/15m/24h before the close-edge stamp
      (the written bar is the aggregated bar, which DOES have a `BarTimeframe`), never write raw 1s bars. (Workaround
      shipped: the 4 `test_databento_path_streaming.py` tests now exercise `trades` not the banned `ohlcv_1m`, so they
      no longer depend on this gap.) — unified-api-contracts / market-tick-data-service / features-service

### Sports IS `_index` v9-column populate + fleet-wide finding (2026-06-19, autonomous tick 3)

- [x] ✅ [SCRIPT] P1. **Sports instruments-store `_index` v9-COLUMN populate** — DONE 2026-06-19
      (instruments-service@5d7f6f0 `populate_sports_is_index_v9_2026_06_19.py`, APPLIED+verified live
      `instruments-store-sports-prd`). schema_version **mix(v4/5/6/8, 75k/2.6M v9) → 100% v9**, asset_group **13k/2.6M →
      100% sports**, source **0 → 93.4%** (2,435,436 via the EXISTING UAC SSOT
      `unified_api_contracts.sports.get_source_for_data_type`; 171,227 / 6.6% blank = SSOT-unmapped catalog/retired
      data_types LEAGUES/VENUES/SFI_LEAGUES/SFI_STANDINGS/TRANSFERMARKT_LEAGUES — honest, the SSOT defines what is
      source-attributable). ROW-PRESERVING — captured 659,693 unchanged. pipeline_mode left blank (reference data, no
      mode model). Snapshot pre_sports_is_v9_20260619. — instruments-service
- [ ] [DATA] P2. **FLEET-WIDE: instruments-store `_index` v9-COLUMN populate for cefi/tradfi/defi (+ prediction
      source)** — the plan's earlier "instruments-store `_index` v9-canonical for ALL 5 AGs — DONE" (line ~575)
      OVERCLAIMS: it ran only the blank-status/dedup canonicalisation, NOT the v9 columns. VERIFIED 2026-06-19 all IS
      indices are the SAME as sports-was: schema_version mixed, **source=0** (cefi/tradfi/defi), asset_group ABSENT
      column. Sports is now populated (above); apply the same per-AG (`get_source_for_data_type` analogue per AG —
      cefi/defi need a UAC source SSOT; tradfi has databento/massive in UAC SOURCE_PRIORITY). The live-WRITER
      source-auto-stamp (so NEW rows carry source, not just the historical backfill) is the larger scope. — homed under
      `data_source_provenance_all_asset_groups_2026_06_01.md` (the named owning plan for the source RED gap). —
      instruments-service / unified-trading-library (writer) / unified-api-contracts (per-AG source SSOT)

### Sports credentialed sources (C) + MD twin-verify (2026-06-19, autonomous tick 4)

- [x] ✅ [DATA] P2. **SFI + Transfermarkt sports keys — UNBLOCKED + backfill launched** — DONE 2026-06-19. Operator
      provisioned the RapidAPI subscription (new key `840373…` on BOTH `soccer-football-info-api-key` v2 +
      `transfermarkt-api-key` v4, same key). **LIVE-SMOKED 2026-06-19 (slot-6, instruments-service .venv, real GCP)**:
      (a) SFI `get_match_descriptors_for_date(2025-03-01)` → HTTP 200, 1525 completed matches; `_fetch_sfi_data`
      end-to-end wrote **21,014 SFI_PROGRESSIVE_STATS rows** + manifest per-VM shard. (b) Transfermarkt RapidAPI
      `competitions/standings` GB1/2024 → HTTP 200 (NOT apify path);
      `_fetch_transfermarkt_data(PLAYER_VALUES, GB1, 2024)` → 20 player_values rows + master/snapshot tables + manifest
      shard. Prior 403 "not subscribed" is RESOLVED. Backfill VMs launched (auto-shutdown-on-completion, per-VM shards):
      4Ã `sfi-backfill-chunk-{1..4}of4-20260619-161036` (2020-01-01→2026-06-19, SFI 4 req/s; backfills ~69.7k
      expected_unattempted SFI cells) + 1Ã `tm-backfill-20260619-161123` (PLAYER_VALUES 2015-01-01→2026-06-19;
      per-league-trigger self-throttle keeps it inside the 120k/mo budget; backfills ~71k expected_unattempted TM
      cells). Disjoint from the running `af-backfill` (api-football) MTDS fan-out.
      SFI_LEAGUES/SFI_STANDINGS/TRANSFERMARKT_LEAGUES stay RETIRED (runtime-only UAC catalog). — instruments-service +
      deployment-service VM launchers
- [ ] [DATA] P2. **Verify SFI+TM backfill VMs ran to completion + manifest cells flipped** — the 5 backfill VMs (run-id
      `20260619-161036` SFI Ã4 + `tm-backfill-20260619-161123`) auto-shutdown on completion. After they drain: (1)
      `gcloud compute instances list --filter='name~"^sfi-backfill" OR name~"^tm-backfill"'` = empty/STOPPED; (2) run
      `deployment-service/scripts/vm/launch-sports-manifest-rescan-vm.sh` to materialise empty_confirmed rows; (3)
      re-read the sports availability index — `expected_unattempted` for `source∈{soccer_football_info,transfermarkt}`
      should drop sharply as cells flip to `captured`/`empty_confirmed`. — instruments-service [VM RUNNING]

### Sports A2/A3/D read-only verification — ALL PASS (2026-06-19, autonomous tick 4)

- [x] ✅ [AUDIT] P1. **Sports A2/A3/D e2e consistency verification** — DONE 2026-06-19 (read-only sub-agent):
  - **A2a catalogue PASS** — `gs://instruments-store-sports-prd/prod/catalog.parquet` = 789-league roll-up, FRESH
    (rebuilt 2026-06-19T08:38Z), correct columns (instrument_id/league_id/available_from/mvp). available_to 100% null =
    open-ended-active (correct). Finding → todo below.
  - **A2b MVP vs TOTAL_UNIVERSE PASS** — sports present in `TOTAL_UNIVERSE_AXES["sports"]` (2 axes: fixtures
    DOWNLOAD_DERIVED + data_type HARDCODED_GENESIS) AND `MVP_SCOPE["sports"]` (`SportsMvpRule` 4 leagues EPL/LA_LIGA/
    NFL/NBA Ã 6 data_types); `universe_membership()` classifies MVP⊆TOTAL correctly (total_universe.py:241-254,
    mvp_scope.py:475-498/755-761).
    > **[v10 RECONCILED 2026-06-27]** The "4 leagues EPL/LA_LIGA/NFL/NBA" count above reflects the PRE-v10
    > `SportsMvpRule`. The canonical v10 MVP scope for sports is **94 FOOTBALL leagues** via
    > `_mvp_football_league_ids()` (`mvp_scope.py` v10). Do NOT act on the 4-league count as a current scope definition.
    > SSOT: `/codex/02-data/mvp-scope-canonical.md`.
  - **A3 paths PASS** — all 6 representative data_types (FIXTURES/STANDINGS/ODDS/PLAYER_VALUES/SFI_PROGRESSIVE_STATS/
    WEATHER) resolve to actual GCS objects via `candidate_parquet_paths()`. No reader-shape drift.
  - **D shard-atom PASS** — `(data_type, league_id, date)` atom IDENTICAL across IS SSOT
    (`registry/data_status_axis_matrix.py:70`), MTDS SSOT (`:105` + `manifest_recorder.py:25`), data-status drilldown
    (`deployment-api/.../data_status_hierarchical.py:15,43`), and the deployment-api drilldown alignment test. No
    surface drops league_id. — verified read-only
- [x] ✅ [DATA] P3. **Sports catalogue `mvp` column is 100% False (numeric league IDs vs is_mvp() canonical strings)** —
      reconciled via `cross_cutting_satellite_ao_dispatch_batch11_2026_08_09.md` todo 7 (2026-08-10, slot 24) — STALE
      PREMISE, ALREADY WORKING. No code change needed — the numeric→canonical mapping concern is moot because the
      catalogue `league_id` is already canonical end-to-end. Measured against the LIVE prod catalogue (rebuilt
      2026-08-10 10:52Z): 0 numeric `league_id` rows (532,868 rows, all canonical strings); all 96 v10 MVP football
      leagues tagged `mvp=True` (0 false negatives), 272,006 rows `mvp=True`. One stale false positive
      (`SEGUNDA_DIVISION`, cosmetic, tag unused downstream) — see batch-11's todo 7 note. The numeric-ID premise
      reflects the 2026-06-19 catalogue verify; the sports by_date source has since canonicalized league_id. Repo:
      instruments-service (verified, no change needed).

### Follow-up todos (tracked)

- [x] ✅ [INFRA] P1. deployment-service — gas-fees consolidator job+cron APPLIED + VERIFIED. Foreign
      `paper_week_determinism_scheduler.tf` dup-`blrs_image` was fixed by its owner; `tofu apply` (targeted, 2 add/0
      change/0 destroy) created `uts-prod-manifest-consolidator-gas-fees` job + `*/1` cron; ran once to seed the index;
      relaunched gas-fees (`mtds-gas-fees-20260619-211114`) which now CLIMBS past the crash point (ETHEREUM+BSC
      sampling, 2021-01-01/02, **no ManifestConsolidatorStaleError**) — deployment-service@f0f7ded.
- [x] ✅ [SCRIPT] P2. **Diagnose the sfi backfill mid-processing hang + add a request timeout + per-date isolation** —
      reconciled via `cross_cutting_satellite_ao_dispatch_batch11_2026_08_09.md` todo 8 (2026-08-09) — STALE PREMISE,
      already shipped well before this batch: bounded per-request HTTP timeouts (`instruments-service@0261e4259`,
      2026-06-19), per-match `asyncio.wait_for` shard isolation (`instruments-service@367afc6e0`, 2026-06-24), the
      `--chunks` ban for SFI's shared-key rate limit (`deployment-service@51cbacd9d`, 2026-06-19), a VM-level
      silent-stall watchdog (`deployment-service@a8ee104e5`, 2026-06-22). Verified via 3 real recent production SFI
      backfill VMs (`sfi-backfill-20260806-140815`,`-20260807-101503`,`-20260807-123519`) — all completed cleanly
      despite hitting real transient errors mid-run, each correctly shard-isolated without stalling. No code change
      needed. Distinct low-frequency data-quality finding (JSON truncation, not a hang) filed as
      `/plans/active/issues/sfi_progressive_stats_json_truncation_2026_08_09.md`. Repo: instruments-service (verified,
      no change needed) / deployment-service (verified, no change needed).
- [ ] [SCRIPT] P2. **DEFERRED** — the silent-worker watchdog (already a pending residual) is the systemic fix for the
      gas/sfi "VM RUNNING but work-process silent, log-tee daemon alive" class: detect work-process silence (run.log
      object mtime frozen N min while VM RUNNING) and auto-kill+alert, distinct from the existing heartbeat watchdog.
      Target repo: deployment-service.

### Follow-up todos (tracked)

- [x] ✅ [SCRIPT] P2. **Apply the parallelization pattern to the sfi/sports collector's per-date sequential loop within
      the RapidAPI rate budget** — reconciled via `cross_cutting_satellite_ao_dispatch_batch11_2026_08_09.md` todo 9
      (2026-08-09). Correction to this todo's own repo attribution: SFI is entirely owned by instruments-service (no
      SFI/RapidAPI code in market-tick-data-service — MTDS sports adapters are a separate Sportradar/odds provider).
      Applied `asyncio.Semaphore(5)` + `gather` to the per-match progressive-stats fetch in `_fetch_sfi_data()` (mirrors
      the api_football pattern). The adapter's existing `_throttle()` token bucket serialises the actual send-rate
      regardless of added concurrency (structurally cannot raise 429s). QG green. Repo: instruments-service@8afe2053;
      market-tick-data-service has no SFI involvement.
- [x] ✅ [CREDENTIALS] P1. SUPERSEDED — NOT a tier ask. Operator 2026-06-19: SFI RapidAPI is **4 req/s (max tier 6
      req/s) + 100k req/day**, so a tier upgrade is negligible (4→6). The 429s were SELF-INFLICTED: we ran **4
      chunk-parallel VMs sharing ONE RapidAPI key** (each self-pacing 0.34s≈2.94/s → 4Ã2.94≈11.8/s vs the 4/s ACCOUNT
      limit) → constant 429 collisions → 60s back-off sleeps → aggregate throughput WORSE than one clean stream. **Fix =
      collapse to a single stream** (sfi-backfill-20260619-221723, chunk=single, 2.94/s < 4/s, no collision);
      incremental skip resumes from the chunks' captured dates. Binding ceiling is the 100k/day cap (a single ~2.94/s
      stream saturates it in ~9.4h), NOT rps.
- [x] ✅ [INFRA] P3. deployment-service / unified-trading-pm — cosmetic `qg-common.sh:159` bug: `stat` output leaks into
      an arithmetic `(( ))` expression in the pip-audit deps-hash cache check → "syntax error in expression" + a
      redundant full pip-audit run (non-fatal). Fix the cache-hash comparison. Target repo: unified-trading-pm
      (qg-common.sh SSOT). — unified-trading-pm `qg-common.sh:162` (GNU-first guarded
      `stat -c %Y 2>/dev/null || stat -f %m` shipped).

### Follow-up todos (corrected)

- [x] ✅ [SCRIPT] P2. **`launch-sfi-backfill-vm.sh` must DEFAULT SFI to a single stream (or refuse `--chunks N>1`)** —
      reconciled via `cross_cutting_satellite_ao_dispatch_batch11_2026_08_09.md` todo 10 (2026-08-09) — STALE FINDING,
      already fixed pre-audit. `launch-sfi-backfill-vm.sh` has hard-refused `--chunks N>1` since
      `deployment-service@51cbacd9` (2026-06-19), which predates this doc's 2026-07-24 source scan; `--chunks` now only
      accepts `1`/unset, `N>1` exits 1. The optional pace tighten (0.34s→0.25s) was NOT applied (explicitly optional,
      outside this item's done-when). Repo: deployment-service (verified, no change needed).

### Follow-up todos

- [ ] [SCRIPT] P2. **paper_engine.py** (foreign paper-determinism Cloud Run job; source not yet on LDR) — emit
      `margin.gross_usd_now` (= Î£|position notional|) + `gross_leverage_now` explicitly, like
      `net_usd_now`/`net_leverage_now`, instead of a single `gross_usd` that conflates planned-ceiling vs live (it flips
      15M/6x ↔ 5.6M/2.2x between runs). UI currently derives gross-now from positions as the interim. Target: whoever
      owns paper_engine.py (batch-live-reconciliation / citadel paper-determinism).
- [x] ✅ [SCRIPT] P3. **`launch-mtds-prediction-backfill-vm.sh` singleton lock must be per-venue** — reconciled via
      `cross_cutting_satellite_ao_dispatch_batch11_2026_08_09.md` todo 11 (2026-08-11, slot 28) — the per-venue
      singleton lock (`^mtds-prediction-${VENUE_LOWER}-`), `VENUE_LOWER` variable, updated error message, DRY'd VM_NAME
      landed before this task was dispatched. Verified against current HEAD: KALSHI and POLYMARKET runs no longer block
      each other. Repo: deployment-service@fce66018.

### Follow-up todos

- [ ] [INFRA] P2. deployment-service — once the foreign dirty trees clear (MTDS scripts/quality-gates.sh + UTL
      honest_coverage_ratchet), rebuild the PREDICTION code tarball (`create-code-tarballs.sh --asset-group PREDICTION`)
      and relaunch the Kalshi backfill
      (`launch-mtds-prediction-backfill-vm.sh --force --venue KALSHI 2026-03-21 2026-06-19`); verify it fetches (not "No
      active venues"). Same tarball also delivers the gas parallelization (mtds@7421693, ~14x) to gas-fees VMs. Target
      repo: deployment-service.

### Side-finding (2026-06-20, non-blocking)

- [x] ✅ [TEST] P3. **Re-baseline the UEI-lifecycle contract-call ratchet for
      `canonical/crosscutting/honest_coverage.py` post-split** — reconciled via
      `cross_cutting_satellite_ao_dispatch_batch11_2026_08_09.md` todo 12 (2026-08-09) — STALE PREMISE, baseline already
      accurate. Verified live: `adapter_contract_baseline.yaml` already carries separate correct entries for
      `honest_coverage.py` (38) + the three split-out registries (`_honest_coverage_clusters.py` 4,
      `_honest_coverage_empty_reasons.py` 5, `_honest_coverage_logic.py` 11 — sum 58). Running
      `check_adapter_contract_regression.py --regenerate-baseline` produced a byte-identical baseline (`git diff --stat`
      empty). No baseline edit, no code change needed. Repo: unified-api-contracts (verified, no change needed).

## Deferred work — migrated to:

Two genuine hits in this plan:

1. (line ~293) "SFI_LEAGUES/SFI_STANDINGS/TRANSFERMARKT_LEAGUES cov 0.000 (all attempted_failed — credentialed/blocked
   scraper sources, tracked in sports_master DEFERRED-INDEFINITELY scraper set)." **`plans/epics/sports_master.md`** §
   "Scrapers DEFERRED-INDEFINITELY 2026-05-12 per operator" — this is the real, already-documented named successor: a
   formal 2026-05-12 operator ruling that these credentialed/blocked scraper sources are out of scope for the active
   sports universe indefinitely (see also `plans/archive/issues/wsfeedconnector_phase35_gap_2026_07_06.md` for the same
   ruling applied to DRAFTKINGS/FANDUEL). Not a B0 gap for this plan.
2. (line ~1724) "**DEFERRED** — the silent-worker watchdog (already a pending residual) is the systemic fix for the
   gas/sfi 'VM RUNNING but work-process silent' class." **Not yet identified** — no separate successor plan exists; this
   is tracked as this same plan's own open `- [ ]` [SCRIPT] P2 todo (line ~1724), Target repo: deployment-service. It
   remains this plan's responsibility until shipped; grepping `plans/active/` and `plans/epics/` found no other plan
   that has picked up the "silent-worker watchdog" item.

- **na-eligibility-audit 2026-08-02** (re-confirms 2026-07-30; only change since = context-scout `context_scope`
  frontmatter, body byte-identical): KEEP-NA, valid — open set spans credential-gated venue onboarding, a cross-plan
  B0→B1→B2 dependency chain the operator sequenced 2026-06-18, and cost-gated backfill scope.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) -- added the IS catalogue-build + expected-universe
  scripts B0/B1 target; body's own `path_to_100pct_backfill_mtds_is_2026_06_17.md` cite is now archived, not active.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — reaffirms 2026-08-02 (unchanged): genuine mix of
  credential/cost-gated backfill scope (B0), an operator-sequenced B0→B1→B2 dependency chain (2026-06-18 ruling), and
  several independently-bounded items; whole doc stays NA.
- **context-scout 2026-08-07**: populated/refreshed context_scope (5 entries) — re-verified all 5 still resolve;
  unchanged (still the right minimal set across this doc's many topics).
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — re-confirms 2026-08-06 (same-day standing verdict, unchanged).
  Read all 22 open todos: real mix holds — credential-adjacent/dependency-chained items (B0→B1→B2 sequencing, the
  FLEET-WIDE `_index` v9-populate homed under an archived doc — `data_source_provenance_all_asset_groups_2026_06_01.md`
  is now folded→M-1 and archived per `master_data_canonicalisation_migration_catalogue_2026_06_07.md`'s sub-plan
  registry, a stale citation worth fixing on a future touch but not actioned here since the item itself is still
  genuinely open, not done), a foreign-repo dependency (paper_engine.py, source not yet on LDR), and a dirty-tree
  dependency (PREDICTION tarball rebuild). **Secondary finding (not actioned, per the established 2026-08-06 ruling to
  keep the whole doc together)**: roughly half the 22 open items (`--operation status` prediction bucket fix, DeFi
  venue-grain adapter alignment, B3 e2e-data canonical copy, Kalshi pipeline wiring, Extended backfill+hardening,
  `ohlcv-1s` BarTimeframe gap, sports mvp-column league-id fix, SFI hang diagnosis, VM-launcher script fixes, UEI
  ratchet re-baseline) read as independently bounded/mechanical with no operator or credential gate of their own — a
  candidate for a future doc-split (mirroring how this doc's own siblings were split out of
  `instruments_mtds_subset_consistency_remediation_2026_06_17.md`), not executed this run.
- **round11 RECLASSIFY + satellite-extraction sweep 2026-08-09**: this is that future doc-split. Extracted 11 of the
  ~10-12 items the 2026-08-07 entry above named to
  [`cross_cutting_satellite_ao_dispatch_batch11_2026_08_09.md`](/plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch11_2026_08_09.md)
  (+ gated finalize twin): prediction status-bucket fix, DeFi venue-grain adapter alignment, B3 e2e-data canonical copy,
  Extended public backfill, Extended candle sharp-edge hardening, Extended candle path consolidation, sports mvp-column
  fix, SFI hang diagnosis, sfi/sports parallelization, both VM-launcher script fixes, and the UEI ratchet re-baseline.
  **"Wire Kalshi into the pipeline" was checked but NOT extracted** — live evidence in
  `data_completion_to_100_all_ag_2026_06_21.md` (Kalshi deep-history seed VMs ran, `live_kalshi` present/captured) and
  `prediction_live_clob_depth_capture_2026_07_24.md` (Kalshi trades-adapter URL fix shipped+verified) strongly suggests
  this checkbox is stale, not open — flagged for the batch 11 finalize twin to re-verify against current manifest state
  and flip or correct, rather than re-dispatched as fresh work. **`ohlcv-1s`/`BarTimeframe` was also checked but NOT
  extracted** — on full read it is a multi-service, one-commit closed-set schema extension (UAC + MTDS +
  features-service + every OHLCV write-callsite), too broad a blast radius for a single bounded AO todo; left as-is. Doc
  stays `assigned_vm: NA` (the remaining ~10 open items are genuinely credential/dependency/design-gated, per the
  entries above). Extracted items' source checkboxes stay open here until batch 11's finalize twin reconciles them.
- **batch-11 finalize reconcile 2026-08-11** (`cross_cutting_satellite_ao_dispatch_batch11_2026_08_09_finalize.md` todo
  1, slot 3): flipped all 11 corresponding checkboxes in this doc against batch 11's now-done todos, citing the shipped
  commit(s)/verification evidence per item (verified against batch 11's own text, not assumed verbatim — prediction
  status-bucket fix, DeFi venue-grain alignment, B3 e2e-data canonical copy, Extended backfill, Extended candle
  hardening, Extended candle path consolidation, sports mvp-column fix, SFI hang diagnosis, sfi/sports parallelization,
  launch-sfi-backfill-vm.sh chunks default, launch-mtds-prediction-backfill-vm.sh singleton lock, UEI ratchet
  re-baseline). Also re-verified the flagged "Wire Kalshi into the pipeline" checkbox against CURRENT code (not just the
  two previously-cited docs): confirmed `instruments-service/.../adapters/prediction/kalshi.py` fully implements RSA-PSS
  signing reading both `api_key_id`/`key_id` + `private_key`, and MTDS carries `KalshiAdapter.get_trades_with_status` +
  4 live WS connectors + a bulk-ingest script — flipped as done. **9 open todos remain** (B0/B1/B2/B3-adjacent
  backfill+catalogue-regen scope, `ohlcv-1s`/`BarTimeframe` closed-set extension, the manifest dedup blank-column fix,
  the FLEET-WIDE v9-column populate, the silent-worker watchdog, `paper_engine.py` foreign-repo dependency, the
  dirty-tree-gated PREDICTION tarball rebuild) — genuinely credential/dependency/design- gated, confirming the finalize
  plan's own expectation ("unlikely" to reach 0). Doc does NOT archive; stays `assigned_vm: NA`.
