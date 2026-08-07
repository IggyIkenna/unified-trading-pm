---
doc_type: issue
title: >-
  HYPERLIQUID/EXTENDED/LIGHTER/BLAZESTAKE non-canonical defi.venues — 4 distinct root causes found + 2 fixed
  (2026-08-04)
summary: >-
  RESOLVED for 3 of 4 venues, 1 remaining live-data-gap finding. Root-caused all four non-canonical `defi.venues`
  distinct-values hits via bounded manifest/catalogue reads (pyarrow.fs.GcsFileSystem streaming, no corpus walk) —
  **four genuinely distinct mechanisms**, correcting every prior citation (none of which actually explained any of
  these): (1) **HYPERLIQUID** — genuine 2026-06-25 cefi reclassification residue that is a LIVE, actively-read
  determinism-critical data source (`CanonicalPerpFundingProvider`, CARRY_BASIS_PERP/CARRY_FUNDING_DISPERSION) — **do
  not touch**, no fix needed, disposition `no-still-authoritative`. (2) **EXTENDED + (3) LIGHTER** — a STALE
  instruments-service DEFI catalogue (`instruments-store-defi-prd-.../prod/catalog.parquet`) still carried 15
  EXTENDED-STARKNET + 18 LIGHTER-ZKSYNC PERPETUAL rows (never delisted post-reclassification, protected by
  `build_instrument_catalogue.py`'s catalogue-shrink guard); `enumerate_expected_universe.py --asset-group defi`
  re-materialised `expected_unattempted` placeholder rows for them into MTDS's manifest on every run (confirmed
  written_at as recent as 2026-08-04, today) — the SAME "stale-catalogue re-seed" mechanism as the GMX precedent.
  **FIXED**: purged the 33 stale rows from the defi catalogue 2026-08-04 (twin-confirmed: cefi's own catalogue already
  carries 286 + 221 real, actively-maintained rows for these venues), snapshot-first, verified 0 remaining —
  `instruments-service@14746732`. (4) **BLAZESTAKE** — a THIRD, unrelated mechanism: NOT part of the 2026-06-25 cefi
  reclassification at all; it's a legitimate DeFi LST venue whose canonical name is `SOLBLAZE-SOLANA` (still
  `phase=live`), and `BLAZESTAKE` is a historical pre-DF-4-fix alias. Real captured `lst_rates` data exists
  2022-12-14→2026-07-31, but the legacy writer (`pipeline_mode=batch_onchain_subgraph`/`batch_defillama`) STOPPED around
  2026-07-31/08-01 and the canonical `SOLBLAZE-SOLANA` name has **zero** manifest rows — no live producer of this data
  exists today. **NOT a delete/fold candidate** (Part 1 fails — no canonical twin) — filed as its own separate
  live-data-gap finding, not fixed here (needs an operator/design decision on which adapter should own `SOLBLAZE-SOLANA`
  production going forward).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service, instruments-service, strategy-service, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    defi,
    cefi,
    hyperliquid,
    extended,
    lighter,
    blazestake,
    venue-reclassification,
    distinct-values,
    manifest,
    catalogue,
    stale-catalogue,
    data-correctness,
    honest-coverage,
  ]
related:
  [
    /plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md,
    /plans/archive/2026_07/defi_venue_phase_live_definition_contradiction_2026_07_22.md,
    /plans/active/instruments_foundation_completeness_2026_06_24.md,
    /plans/active/issues/defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
created: "2026-08-04"
author: unknown
last_updated: "2026-08-05"
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
source: >-
  Operator (interactive session 2026-08-04), cross-checking distinct_values non-canonical audit citations while
  investigating defi_cefi_venue_chain_axis_contamination_2026_07_28.md under /autonomous dispatch; root-caused +
  partially fixed by a sub-agent dispatch the same day (mandated to execute, not just diagnose)
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: >-
  instruments-service@14746732 (EXTENDED/LIGHTER catalogue fix) + instruments-service@141bb384 (purge script — not
  needed, data self-resolved via manifest consolidator)
depends_on: []
context_scope:
  [
    /codex/02-data/defi-canonical-naming-ssot.md,
    /plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
    instruments-service/scripts/build_instrument_catalogue.py,
    strategy-service/strategy_service/engine/core/canonical_perp_funding_provider.py,
    /plans/active/issues/defi_mtds_lst_rates_cloud_run_job_oom_2026_08_04.md,
  ]
---

# HYPERLIQUID/EXTENDED/LIGHTER/BLAZESTAKE non-canonical `defi.venues` — root-caused + fixed (2026-08-04)

## Citation-trail correction (unchanged from the original filing)

The registry is unambiguous (`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`): line 403
puts `HYPERLIQUID` in `VENUES_BY_ASSET_GROUP["cefi"]`; line 461's `VENUES_BY_ASSET_GROUP["defi"]` derivation can never
include it (absent from `_ALL_DEFI_VENUES` entirely). The two prior docs blaming
`defi_venue_phase_live_definition_contradiction_2026_07_22.md` for HYPERLIQUID's/BLAZESTAKE's residual presence do not
hold up: that doc's actual scope is 11 unrelated venues excluded by a `phase=="pipeline"` DENOMINATOR filter bug, zero
mentions of HYPERLIQUID, and (per this session's fresh read) it EXPLICITLY states "(BLAZESTAKE, KAMINO_LENDING,
MORPHOVAULTS were already correctly 'live' or fixed 2026-07-22)" — i.e. that doc's own text says BLAZESTAKE was NOT
excluded by its bug either. The genuine reclassification SSOT (`instruments_foundation_completeness_2026_06_24.md`) also
never names HYPERLIQUID or BLAZESTAKE — its cited 1,802-row purge names EXTENDED/PACIFICA/LIGHTER only. All four venues
needed independent root-causing; below is what each turned out to be, confirmed via bounded, column-projected,
row-group-pushdown reads (`pyarrow.fs.GcsFileSystem` — genuine HTTP-range streaming, never a full-object download; one
dataset open + one filtered scan per corpus, never a corpus walk) rather than inference.

## HYPERLIQUID — genuine reclassification residue, LIVE READER, disposition `no-still-authoritative`

Bounded manifest read (`market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`, filtered
`asset_group=="defi" and venue=="HYPERLIQUID"`): **205,395 rows**, `date` range 2023-05-12→2026-06-09, 100%
`capture_status=captured`, `pipeline_mode=batch_hyperliquid` (100%), `chain=HYPERLIQUID` for every row (this is the SAME
physical rows as the separately-flagged `defi.chains=HYPERLIQUID` non-canonical hit — not a second issue). `data_type`
split: `perp_daily_ctx` 170,521 / `perp_mark_price` 22,374 / `perp_funding` 12,500. `written_at` range
2026-07-23→2026-08-04 — recent, because this exact corpus was freshly RE-REGISTERED this week by
`defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md`'s manifest-backfill work (real historical data, just
re-stamped recently — not evidence of an active mis-write).

**Live-reader check (mandatory per this dispatch's cautionary precedent)**: CONFIRMED live and load-bearing.
`strategy-service/strategy_service/engine/core/canonical_perp_funding_provider.py`'s `CanonicalPerpFundingProvider`
resolves its bucket ONCE in `__init__` via `resolve_bucket_name(kind="tick-data", asset_group="defi")` — a **literal
hardcoded "defi"**, no cefi fallback, no dynamic resolution by current venue classification. `catalog_carry.py:214`
configures `("hyperliquid", "HYPERLIQUID", ShareClass.USDC)` as 1 of 11 `_CARRY_BASIS_PERP_VENUE_BUNDLES`;
`catalog_staked_basis.py:89,105` also lists HYPERLIQUID in `_STAKED_BASIS_ETH_PERP_VENUES`/
`_STAKED_BASIS_SOL_PERP_VENUES`. `paper_run_handler.py:1984-1988` (`_load_funding_ticks`) resolves
`venue=_funding_spec_venue(config)` → `"HYPERLIQUID"` and calls
`CanonicalPerpFundingProvider().funding_window(window_start, window_end, venue=venue)` — live, reachable,
CARRY_BASIS_PERP/CARRY_FUNDING_DISPERSION archetypes. This exactly mirrors the BINANCE-FUTURES/BITGET-FUTURES precedent
already found in `defi_cefi_venue_chain_axis_contamination_2026_07_28.md`'s P1 entry (same provider, same disposition
`no-still-authoritative`). **Do not touch. No fix needed or executed.**

## EXTENDED + LIGHTER — stale defi-bucket instrument catalogue, LIVE re-seed bug, FIXED

**These are NOT the same mechanism as HYPERLIQUID.** Bounded manifest read confirmed: **EXTENDED 4,980 rows / LIGHTER
5,976 rows**, `date` range 2026-02-20→2026-08-04 (today), `written_at` 2026-08-01→2026-08-04 (today/this week) — and
**100% `capture_status=expected_unattempted`** (never `captured` — no real data ever existed or was lost).
`chain=STARKNET`/`ZKSYNC` respectively; `data_type` = `oracle_prices` + `perp_funding` in equal split;
`pipeline_mode=batch_pyth_hermes` (oracle_prices) / `batch_hyperliquid` (perp_funding — itself a symptom of the SAME
mis-registered `SOURCE_PRIORITY[("defi","perp_funding")]=["hyperliquid"]` fallback that caused the already-fixed GMX
pipeline_mode bug, `defi_gmx_pipeline_mode_mislabeled_hyperliquid_2026_07_21.md`). A **bounded per-(day,venue) GCS
`match_glob` sweep** (23 sample dates, 2023-01-01→2026-08-04, day always fixed — an unbounded venue-only glob is
confirmed impractically slow, GCS has to lexicographically scan the whole bucket with no day bound) found **zero**
physical `raw_tick_data` objects for bare `venue=EXTENDED`/`venue=LIGHTER` on ANY sampled date — confirming these are
pure phantom placeholder rows with no captured data behind them, currently and historically.

**Root cause, fully confirmed** (matches this dispatch's GMX-precedent hint exactly, just in a different registry than
guessed): the **instruments-service DEFI instrument catalogue**
(`instruments-store-defi-prd-central-element-323112/prod/catalog.parquet`) still carried **15 EXTENDED-STARKNET + 18
LIGHTER-ZKSYNC `PERPETUAL` rows**, `available_to=None` (never delisted) — leftover from before the 2026-06-25 defi→cefi
reclassification. That reclassification (`purge_cefi_perp_defi_contamination_2026_06_25.py`) fixed the CAPTURE path
(`instruments_service/engine/orchestrator/defi.py::_build_defi_venues()`) and purged the `_index` manifest rows, but its
own comment explicitly left the catalogue alone: _"Catalogue (prod/catalog.parquet) is asset_group-AGNOSTIC venue-keyed
instrument defs → left intact (valid instrument definitions; asset_group is in UAC)"_ — true in principle, but
`enumerate_expected_universe.py`'s v2 per-instrument enumerator does NOT re-resolve asset_group per row: for a
`--asset-group defi` run it downloads the DEFI bucket's `catalog.parquet` wholesale
(`scripts/enumerate_expected_universe.py:4500-4519`) and treats every row in it as defi-expected, asset_group being
implicit in "which bucket you read from." `build_instrument_catalogue.py`'s catalogue-shrink guard
(`--allow-catalogue-shrink`, default OFF) plus `--mode incremental`'s frozen-tail design meant these 33 rows survived
every rebuild since 2026-06-25 — the G3b anti-false-delist logic (correctly) never inferred delisting from mere
capture-silence, but these venues were EXPLICITLY removed from the universe, not merely quiet, so nothing ever forced
`available_to`. Net effect: `enumerate_expected_universe.py --asset-group defi` re-materialises fresh
`expected_unattempted` rows for bare EXTENDED/LIGHTER into MTDS's manifest **on every run** — confirmed by the
`written_at` range reaching literally today, 2026-08-04, before any fix.

**Twin check** (Part 1 of the delete-safety proof): the CEFI catalogue
(`instruments-store-cefi-prd-.../prod/catalog.parquet`) already carries the real, actively-maintained instruments —
**286 EXTENDED-STARKNET + 221 LIGHTER-ZKSYNC rows** (vs. the defi bucket's stale 15+18) — confirming the defi-bucket
copies are pure duplication in the wrong bucket, not unique data. **Part 3/4** (no live writer/reader depends on the
DEFI-bucket copies): confirmed — `_build_defi_venues()` doesn't enumerate them, and the only consumer found
(`enumerate_expected_universe.py --asset-group defi`) is the buggy re-seeder being fixed, not a legitimate dependent.

**FIXED 2026-08-04**: shipped `instruments-service/scripts/purge_defi_catalogue_cefi_reclassified_venues_2026_08_04.py`
(mirrors `purge_cefi_perp_defi_contamination_2026_06_25.py`'s exact structure — snapshot-first, backup, CAS-adjacent
overwrite, round-trip verify). Dry-run confirmed EXACTLY 33 rows would be dropped (15 EXTENDED-STARKNET + 18
LIGHTER-ZKSYNC), matching the independent bounded-read count precisely. `--apply` run: fresh
`gcs_bucket_soft_delete_retention_seconds()` check passed (604800s, at the 7-day §3a floor) → snapshot written to
`prod/snapshots/pre_cefi_reclassified_venue_purge_2026_08_04.parquet` → `.bak` backup written → catalogue rewritten
79,035→79,002 rows → **live round-trip verify: 0 stale rows remaining**. See Progress Log for the commit SHA. This
closes the ROOT CAUSE — future `enumerate_expected_universe.py --asset-group defi` runs will no longer re-seed
`expected_unattempted` rows for these venues. The already-materialised 4,980+5,976 `expected_unattempted` MTDS-manifest
rows are harmless placeholders (zero real captured data, so zero data-loss risk either way) — left untouched; a
low-priority follow-up could clean them up but it is not required for correctness (no new ones will be added, and
`expected_unattempted` is a normal, honest manifest state for a not-yet-attempted shard — though for a venue that will
never legitimately be attempted, the future correction is to make the shard atom itself stop enumerating, which this fix
already delivers).

## BLAZESTAKE — different, THIRD mechanism: real historical data, legacy writer recently stopped, no live replacement

**NOT part of the 2026-06-25 cefi reclassification cohort at all.** `VENUES_BY_ASSET_GROUP["cefi"]`'s "On-chain CLOBs"
block is exactly {HYPERLIQUID, ASTER, EXTENDED-STARKNET, LIGHTER-ZKSYNC} — BLAZESTAKE is absent. BLAZESTAKE is a
legitimate DeFi Solana liquid-staking (LST) venue whose CANONICAL registered name is `SOLBLAZE-SOLANA`
(`unified_api_contracts/registry/defi_venues.py:624`, `phase="live"`, IS-wired 2026-07-18 via `solblaze.py`).
`BLAZESTAKE`/`BLAZESTAKE-SOLANA` are non-canonical ALIASES resolving to `SOLBLAZE-SOLANA` via `defi_venues.py:385-386`
("DF-4: `_defi_lst.py` uses BLAZESTAKE; canonical is SOLBLAZE" — a 2026-07 case-folding drift fix). The prior citation
blaming `defi_venue_phase_live_definition_contradiction_2026_07_22.md`'s `phase=="pipeline"` mechanism is ALSO wrong for
BLAZESTAKE specifically — that doc's own text confirms BLAZESTAKE was already correctly `phase=="live"` as of
2026-07-22.

Bounded manifest read: **1,402 rows**, `date` 2022-12-14→2026-07-31, 100% `capture_status=captured` (REAL data, not
placeholders), `data_type=lst_rates` (100%), `chain=SOLANA`, `pipeline_mode=batch_onchain_subgraph` (1,311) +
`batch_defillama` (91). **Live writer check**:
`market_tick_data_service/market_interface/adapters/defi/ lst_solblaze_adapter.py:40` sets
`self.venue = "SOLBLAZE-SOLANA"` directly (correct, canonical) — no live code path writes bare `BLAZESTAKE` today. A
**bounded per-day GCS `match_glob` sweep** (23 dates spanning 2023-01-01→2026-08-04) found real objects on EVERY sampled
date from 2023-01-01 through **2026-06-30 AND 2026-07-05/07-10/07-20** (both naming variants present since ~2026-06-01:
legacy leaf `bSOL.parquet` alongside a newer glued-instrument_id leaf `BLAZESTAKE-SOLANA:LST:bSOL.parquet` — same
`venue=BLAZESTAKE` tag on both, just a leaf-naming change) — then **zero** objects on 2026-08-01, 2026-08-03, and
2026-08-04. **The legacy writer stopped producing data sometime between 2026-07-20 and 2026-08-01** (exact date not
pinned down further — not needed for this finding).

**Critically: the canonical `SOLBLAZE-SOLANA` venue has ZERO manifest rows under `asset_group=defi`** (confirmed via the
same bounded read). Despite `lst_solblaze_adapter.py` writing the correct venue name when it runs, it has apparently
never produced a captured row in this manifest — meaning **there is currently no live producer of BlazeStake/SolBlaze
LST-rate data at all**, canonical or not, as of this session (2026-08-04). This is a genuine, separate **live data
gap**, not a delete-safety question:

- **Not a delete/fold candidate**: Part 1 of the delete-safety proof (canonical twin resolves) FAILS outright — no
  `SOLBLAZE-SOLANA` twin exists to fold into or migrate to.
- **Not urgent from a live-strategy-reader angle**: confirmed via code read that strategy-service's CARRY_STAKED_BASIS
  STAKING leg (`CanonicalLstYieldsIndexProvider`) reads a DOWNSTREAM COMPUTED `features-onchain` bucket corpus
  (`onchain/by_date/day={D}/feature_group=lst_yields/features.parquet`), not the raw MTDS defi tick-data bucket this
  finding is about — and `YIELD_STAKING_SIMPLE_LST_ASSET` (`paper_universe.py:162`) only maps 5 protocols
  (lido/rocketpool/etherfi/jito/marinade); solblaze/blazestake isn't in that allowlist at all, canonical or not. So no
  live strategy path is currently broken by this gap (features-service's own upstream `lst_features.py` computation
  layer was not independently checked — outside this dispatch's 5-repo scope — but is irrelevant to the live-reader
  question since strategy-service's own allowlist already excludes this protocol).
- **NOT fixed in this dispatch** — this needs an operator/design decision (who should own producing `SOLBLAZE-SOLANA`
  data going forward: revive/redirect the legacy `batch_onchain_subgraph` writer, or confirm `lst_solblaze_adapter.py`
  is the intended replacement and diagnose why it has zero captured rows), which is a judgment call, not a
  bounded/deterministic todo — tracked as its own `[DIAG]` todo below.

## Todos

- [x] ✅ [DIAG] P2. Bounded manifest reads for all 4 venues + chain=HYPERLIQUID — DONE 2026-08-04, see sections above
      (exact row counts, date ranges, data_type/capture_status/pipeline_mode distributions for each).
- [x] ✅ [DIAG] P2. Live-reader check for all 4 venues (strategy-service + MTDS write-path grep+read) — DONE 2026-08-04:
      HYPERLIQUID has a confirmed live reader (do not touch); EXTENDED/LIGHTER/BLAZESTAKE do not.
- [x] ✅ [DATA] P2. EXTENDED/LIGHTER root cause fixed at source — DONE 2026-08-04. Purged 33 stale
      EXTENDED-STARKNET/LIGHTER-ZKSYNC rows from the defi instrument catalogue
      (`instruments-service/scripts/purge_defi_catalogue_cefi_reclassified_venues_2026_08_04.py --apply`),
      snapshot-first, live-verified 0 remaining. See Progress Log for the shipped commit SHA.
- [x] ✅ [DIAG] P2. **BLAZESTAKE — DIAGNOSED 2026-08-04 (slot 10).** Two independent write paths exist, NEITHER
      producing data today. Operator decision needed; see Progress Log for the full diagnostic breakdown (Options
      A/B/C). **RULED OUT (c):** the legacy handler is still imported + wired in the active `lst_rates_handler.py` →
      `fetch_solana_lst_rates` call chain — it was NOT intentionally removed; its stop is a live gap, not a design
      pause. **Options narrowed to (a) or (b) below.**
- [x] ✅ [DATA] P3. Low-priority hygiene follow-up — DONE 2026-08-05 (slot 7). The 10,956 already-materialised
      `expected_unattempted` MTDS-manifest rows (4,980 EXTENDED + 5,976 LIGHTER) **self-resolved** — the manifest
      consolidator naturally dropped them after the root-cause catalogue fix at `instruments-service@14746732` stopped
      re-seeding. Verified 2026-08-05: bounded column-projected read of the live `_index` (42,212,211 rows, 1,555 MB)
      confirms **0 remaining** defi+EXTENDED/LIGHTER+expected_unattempted rows. A purge script was authored
      (`instruments-service/scripts/purge_defi_mtds_manifest_extended_lighter_expected_unattempted_2026_08_05.py`,
      `instruments-service@141bb384`) as a reusable pattern for future manifest-row purges (PyArrow mmap + incremental
      ParquetWriter for memory-bounded operation on large manifests) but was not needed — the data was already clean.

## Progress Log

- **interactive session 2026-08-04 (autonomous, `/autonomous`)**: filed this doc after confirming the existing citation
  trail doesn't hold up, per the pre-task plan/issue conflict-check + "0 hits ≠ missing, grep-then-READ" rules. Root
  cause investigation not started at filing time (P3, correctly scoped as DIAG-first).
- **sub-agent dispatch 2026-08-04 (mandated to execute, not just diagnose)**: root-caused all 4 venues via bounded,
  genuinely-streaming reads (`pyarrow.fs.GcsFileSystem` — this local environment's plain GCS client downloads proved
  impractically slow for the ~1.7GB MTDS manifest, ~500s even filtered; the footer+row-group-pushdown streaming path was
  the actual fix for that, not a workaround to route around — documented here in case a future bounded read on this same
  corpus hits the identical wall). Confirmed HYPERLIQUID is a live, do-not-touch reclassification residue (no fix
  needed). Root-caused EXTENDED/LIGHTER to a stale defi-bucket instrument-catalogue entry surviving the 2026-06-25
  reclassification's catalogue-shrink guard, confirmed via a twin check against the cefi catalogue (286+221 real rows),
  and FIXED it — shipped + ran
  `instruments-service/scripts/purge_defi_catalogue_cefi_reclassified_venues_2026_08_04.py --apply` (dry-run confirmed
  exact 33-row diff first), snapshot+backup+verify all clean. Found BLAZESTAKE is an unrelated third mechanism (real
  historical data, legacy writer recently stopped, no working canonical replacement) — filed as its own live-data-gap
  finding, not fixed (genuinely needs an operator/design call on ownership, not a bounded execution). Priority raised
  P3→P2 given confirmed live-data-correctness content (a currently-firing daily-reseed bug for 2 venues, now fixed, plus
  a genuine live data gap for a 3rd).
- **worker slot 10, 2026-08-04 (dispatched for the Blazestake DIAG todo)**: completed the full diagnostic read of both
  write paths (code-only, bounded reads — no corpus walk). Findings below.

### Blazestake SOLBLAZE-SOLANA — full diagnostic (slot 10, 2026-08-04)

**Two independent data-producing systems exist. Neither is producing data today.**

#### System 1 — Legacy `lst_rates_handler.py` (the actual historical producer)

- **Call chain**: `lst_rates_handler.py:345` → `_fetch_solana_rows` → `_fetch_solana_lst_rates` (wrapper at
  `lst_rates_handler.py:730`) → `solana_lst_archival.fetch_solana_lst_rates` → `_fetch_bsol_rate` (4-tier fallback)
- **4-tier fetch for bSOL/SOL rate**: Tier 1 Alchemy `getAccountInfo` on `BLAZESTAKE_STAKE_POOL_ACCOUNT`
  (`stk9ApL5HeVAwPLr3TLhDXdZS8ptVu7zp6ov84HpwHA`, SPL stake-pool layout decode) → Tier 2 The Graph subgraph → Tier 3
  REST `/api/v1/stats` → Tier 4 DeFiLlama historical price ratio (market-price proxy, not genuine on-chain data)
- **Write path**: Rows grouped by `(protocol, chain)` in `_lst_rates_write.py:67-73` → `write_defi_rows(venue=protocol)`
  where `protocol="blazestake"` → **venue in manifest + GCS path = `"blazestake"` (lowercase, non-canonical)**
- **Data type**: `lst_rates` (exchange rate bSOL/SOL) — NOT oracle_prices
- **Pipeline mode**: `batch_onchain_subgraph` (Tier 1-3) or `batch_defillama` (Tier 4 DeFiLlama fallback)
- **Historical data**: 1,402 manifest rows, `date` 2022-12-14→2026-07-31, 100% `capture_status=captured`
- **Current status**: STOPPED. Last captured date 2026-07-31; no data for 2026-08-01, 2026-08-03, 2026-08-04. Handler
  code is still actively imported + wired (`lst_rates_handler.py` line 60 imports `fetch_solana_lst_rates`; called at
  line 345 inside `_fetch_solana_rows` at line 515) — this is NOT an intentional removal (rules out option c).
- **Why it stopped**: not determined (scheduler configs live in deployment-service Terraform, not readable in-slot).
  Likely a Cloud Run cron job failure, API key expiry, or RPC endpoint change — the 4 tiers all depend on external
  services (Alchemy, The Graph, stake.solblaze.org, DefiLlama).

#### System 2 — Canonical `SolblazeAdapter` (`lst_solblaze_adapter.py`)

- **Registered**: MTDS factory `factory.py:180` → `"solblaze": ("defi", SolblazeAdapter)`; IS `defi.py:206` →
  `"SOLBLAZE-SOLANA"` in `_build_defi_venues()` live-venue set; UAC `defi_venues.py:624` → `"SOLBLAZE-SOLANA": "live"`
- **Venue**: `self.venue = "SOLBLAZE-SOLANA"` (canonical — correct)
- **Data type produced**: `oracle_prices` (via `_default_data_types()` returning `["oracle_prices"]`) — USD price of
  bSOL from DeFiLlama, NOT an LST exchange rate. This is a DIFFERENT data product than the legacy handler's `lst_rates`.
- **Data source**: DeFiLlama coins API only (`https://coins.llama.fi/prices/historical/{timestamp}/solana:<mint>`),
  public, no auth. Single-source — no fallback tiers.
- **Manifest rows**: **ZERO** captured rows under `asset_group=defi` for venue `SOLBLAZE-SOLANA`
- **Current status**: Adapter code exists and is correctly registered at all 3 layers (UAC, IS, MTDS factory), but has
  apparently never been scheduled/deployed to production — no Terraform scheduler config found in-slot, and zero
  captured manifest rows confirm it has never run.

#### Key structural observations

1. **Different data types — not interchangeable**: Legacy produces `lst_rates` (exchange rate); canonical adapter
   produces `oracle_prices` (USD price). Both are legitimate data products but they serve different downstream
   consumers. If the canonical adapter is chosen as the replacement, the data_type mismatch must be resolved explicitly.
2. **Different venue names**: Legacy writes `venue="blazestake"`; canonical writes `venue="SOLBLAZE-SOLANA"`. The legacy
   name is non-canonical per UAC registry (alias at `defi_venues.py:385-386`, DF-4 fix). Any restart/revival of the
   legacy path should rename to the canonical venue.
3. **Different robustness**: Legacy has 4-tier fallback; canonical adapter has 1 source. Legacy is more resilient.
4. **No live strategy dependency**: Confirmed `YIELD_STAKING_SIMPLE_LST_ASSET` in `paper_universe.py:162` only maps 5
   protocols (lido/rocketpool/etherfi/jito/marinade) — solblaze/blazestake is absent. No live strategy is currently
   broken by this gap.
5. **Features-service**: No solblaze/blazestake references found — no downstream computed-feature dependency either.

#### Options (operator decision required)

**Option A — Restart the legacy handler under the canonical venue name (recommended — fastest, lowest risk)**

- The legacy `lst_rates_handler.py` already works end-to-end and has 2.5 years of proven production data
- Fix: (1) diagnose why it stopped (check Cloud Run scheduler, Alchemy/The Graph API keys, RPC endpoint health), (2)
  rename `protocol="blazestake"` → `"SOLBLAZE-SOLANA"` in `solana_lst_archival.py` and the freshness-check
  `venue="SOLBLAZE"` → `venue="SOLBLAZE-SOLANA"` (currently at line 736), (3) restart
- Data type stays `lst_rates`; pipeline mode stays `batch_onchain_subgraph`
- This gets data flowing again fastest (~1-2 hours of investigation + 1-line rename)
- Repos: market-tick-data-service

**Option B — Deploy the canonical SolblazeAdapter as the production writer**

- The adapter is correctly registered but has never been deployed; needs: (1) a Terraform scheduler entry in
  deployment-service, (2) end-to-end verification, (3) a decision on data_type — keep `oracle_prices` (new data product)
  or switch to `lst_rates` (replace legacy), (4) historical backfill for the gap since 2026-08-01
- Cleaner long-term but more work (~1-3 days) and single-source (DeFiLlama only — less resilient than legacy)
- Repos: market-tick-data-service, deployment-service

**Option C — RULED OUT**: the legacy handler is still actively imported and wired in `lst_rates_handler.py` (lines 60,
345, 515) — this was NOT an intentional removal. The gap is real, not a design pause.

- **worker slot 7, 2026-08-05 (dispatched for the P3 hygiene todo)**: Verified the 10,956 EXTENDED/LIGHTER
  `expected_unattempted` MTDS-manifest rows were already gone — the manifest consolidator naturally dropped them after
  the root-cause catalogue fix at `instruments-service@14746732` stopped re-seeding. Dry-run of purge script (bounded
  column-projected read, 42,212,211 rows, PyArrow mmap) confirmed 0 remaining purge targets. Authored a reusable purge
  script at `instruments-service/scripts/purge_defi_mtds_manifest_extended_lighter_expected_unattempted_2026_08_05.py`
  (`instruments-service@141bb384`) for future manifest-row purge operations (incremental ParquetWriter pattern for
  memory-bounded large-manifest processing) — not applied (already clean). All 5 todos now done; plan is
  archive-eligible (no lock).
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **worker slot 10, 2026-08-06 (dispatched for the P1 follow-up — operator/design decision on ownership)**: **Producer
  stoppage ROOT-CAUSED** (the "why it stopped" the 08-04 diagnostic couldn't determine): NOT venue-specific — the
  `collect-lst-rates` Cloud Run job OOM-crashed (signal 9, "The configured memory limit was reached") on EVERY scheduled
  run since 2026-08-02 at ~70% of its 2Gi cap (rss ~2040MiB) inside `ManifestFreshnessCache.bulk_load()`'s warmup thread
  racing the handler's EVM/Solana RPC fetch work against the now ~42M-row defi index — full evidence in
  `defi_mtds_lst_rates_cloud_run_job_oom_2026_08_04.md`. The scheduler entry
  (`deployment-service/terraform/gcp/defi_collection_scheduler.tf` `"lst-rates"`, `0 1 * * *`) was NEVER removed. **OOM
  FIXED + applied**: 2Gi→4Gi IaC bump `deployment-service@51f9fbe`, live update verified 2026-08-05 (manual execution
  `-b5f4t` completed 2m53s, all 15 LST venues incl. SolBlaze written), targeted prod `tofu apply` synced the lst-rates
  scheduler description 2026-08-06 (slot 11). **Canonical-name fix shipped on LDR**: `market-tick-data-service@2c451c33`
  — the bSOL write path now emits `protocol="SOLBLAZE-SOLANA"` (freshness-check `venue="SOLBLAZE-SOLANA"`). **⚠️ DEPLOY
  LAG (2026-08-06): the fix is NOT yet in the live Cloud Run image.** `market-tick-data-service:latest` is built from
  `main` (`image-build-gate.yml` / `quality-gates-v2.yml`'s dispatch-cloud-build fire on `main`), and `main` is **1,091
  commits behind LDR** (stalled LDR→main promote backlog — the same fleet-wide CI-capacity blocker noted for
  KAMINO_LENDING in `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`). The LIVE job therefore still runs
  pre-fix code and writes `venue=BLAZESTAKE` on every successful daily run (execution `-zzptg`, 2026-08-06 01:00 →
  01:02, Completed True at 4Gi); its fresh SolBlaze rows land under the legacy name and get retired/relabeled only by
  the next one-off migration. **Historical corpus consolidated by the parallel dispatch**
  (`defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`): the 1,406-object / 1,318-day legacy
  `venue=BLAZESTAKE` corpus relabeled + retired to canonical (`relabel_retire_blazestake_venue_2026_08_06.py --apply`,
  prod 2026-08-06). **Live-state verification (bounded filter-pushdown index read, 2026-08-06)**: `SOLBLAZE-SOLANA`
  captured=1,319 (2022-12-14→2026-08-05; `written_at` up to 2026-08-06T01:58 UTC is the migration's re-registration, NOT
  a fresh canonical write from the producer), `BLAZESTAKE` captured=0 (`attempted_failed`=1,404 — reflects the
  migration's retirement, not post-fix producer behaviour). **Closing the residual therefore depends on the LDR→main
  promote clearing (so `2c451c33` reaches the deployed image), not on shipping more code.** **Decision escalated to
  operator via /blocked (BLK-db79e592)**: recommend **Option A** (formalize the legacy `collect-lst-rates` job as the
  owner — already wired + proven) over Option B (canonical `SolblazeAdapter` would change the data product from
  `lst_rates` exchange-rate to `oracle_prices` USD price and is single-source DeFiLlama). **Residual**: 3-day data gap
  2026-08-01..08-03 (the OOM window) → bounded backfill candidate, scoped as a follow-up.
- **worker slot 10, 2026-08-06 (operator decision received)**: **Option A CONFIRMED** — operator directive "proceed now"
  via interactive session. The legacy `collect-lst-rates` Cloud Run job is now the **formal, declared canonical owner**
  of SOLBLAZE-SOLANA `lst_rates` production. Rationale: already wired + proven (2.5 years production data, 4-tier
  fallback), OOM fixed (2Gi→4Gi `deployment-service@51f9fbe`), canonical-name fix on LDR
  (`market-tick-data-service@2c451c33`). The only remaining deployment gap is the LDR→main promote (1,091 commits behind
  — infra, not code) so `2c451c33` reaches the live Cloud Run image; until then, daily runs still write
  `venue=BLAZESTAKE` which the migration script handles. **P1 residual RESOLVED** — the venue now has a declared,
  operating producer. P2 backfill (2026-08-01..08-03 OOM window) remains as follow-up.
- **context-scout 2026-08-07**: refreshed context_scope (6 entries) — swapped `enumerate_expected_universe.py` (the
  now-closed EXTENDED/LIGHTER catalogue fix) for `defi_mtds_lst_rates_cloud_run_job_oom_2026_08_04.md` (the root-cause
  doc the sole remaining open todo, the SOLBLAZE-SOLANA backfill, actually depends on).

## Follow-ups

- [x] ✅ [DATA] P1. Resolve the BLAZESTAKE/SOLBLAZE-SOLANA zero-live-producer residual: operator/design decision
      (Options A/B/C) on adapter ownership, then wire the producer — **DONE 2026-08-06 (slot 10). Option A confirmed:
      legacy `collect-lst-rates` Cloud Run job formalized as canonical SOLBLAZE-SOLANA owner; code shipped
      `market-tick-data-service@2c451c33` (canonical venue name) + `deployment-service@51f9fbe` (OOM fix). Producer
      operating at 4Gi; LDR→main promote lag tracked as infra, not code.**
- [x] [DATA] P2. Backfill the 2026-08-01..08-03 `lst_rates` gap for `SOLBLAZE-SOLANA` (the OOM window — those dates are
      absent from the canonical captured set). Mechanism per the chosen ownership option: Option A → re-run the legacy
      `collect-lst-rates` path for those dates (after `2c451c33` deploys); Option B → adapter-based backfill. Repo:
      market-tick-data-service. Note: if the LDR→main promote stays stalled past 2026-08-07, pre-deploy daily runs keep
      re-creating `venue=BLAZESTAKE` rows that need the same relabel+retire re-run. ✅ deployment-service@46eddc9
      (terraform 8Gi/2CPU bump) + Cloud Run REST API override executions at 8Gi/2CPU: f8m4d (2026-08-01 ✅ 1m52s), q9mkx
      (2026-08-02 ✅ 1m42s), vqg8n (2026-08-03 ✅ 1m55s). GCS verified: 1 canonical SOLBLAZE-SOLANA lst_rates parquet
      per date under venue=SOLBLAZE-SOLANA/chain=SOLANA/instrument_type=lst/ data_type=lst_rates/. Deployed image
      (2c451c33) writes SOLBLAZE-SOLANA directly; no relabel+retire needed. 4Gi/1CPU OOM on historical backfill; bumped
      to 8Gi/2CPU (Cloud Run constraint: >4Gi requires >=2 CPU).

> **2026-08-06 archive-candidate audit**: Summary says 'RESOLVED for 3 of 4 venues, 1 remaining live-data-gap finding' —
> BLAZESTAKE/SOLBLAZE-SOLANA has zero live producer, explicitly 'NOT fixed in this dispatch', operator/design decision
> on adapter ownership (Options A/B/C) still pending. [KEEP_OPEN todo synthesized from justification by archive sweep]
