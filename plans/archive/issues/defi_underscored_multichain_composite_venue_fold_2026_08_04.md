---
doc_type: issue
title: >-
  DeFi distinct-values panel's 22 underscored multi-chain composite venues (UNISWAP_V3-ARBITRUM, BALANCER-ETHEREUM,
  etc.) are NOT a legacy-object-fold candidate like the resolved 9-venue precedent — they are a brand-new (last ~36h),
  unresolved manifest/GCS divergence with no located backing data
summary: >-
  Dispatched to investigate 22 non-canonical `venue` values on deployment-api's `GET /distinct-values/defi` panel
  (AERODROME_V3-BASE, BALANCER-{ARBITRUM,AVALANCHE,BASE,ETHEREUM,OPTIMISM,POLYGON}, CAMELOT_V3-ARBITRUM,
  CURVE-{AVALANCHE,ETHEREUM}, PANCAKESWAP_V3-{BASE,BSC,ETHEREUM}, SUSHISWAP-ARBITRUM,
  SUSHISWAP_V3-{AVALANCHE,BASE,ETHEREUM}, UNISWAP_V3-{ARBITRUM,BASE,ETHEREUM,OPTIMISM,POLYGON}), assumed to mirror the
  already-resolved `defi_legacy_precanonical_composite_venue_objects_2026_07_24.md` 9-venue fold (real 2024-2026 legacy
  GCS objects needing a copy-to-canonical-path script). Extensive verification (manifest coverage rollups, live
  catalogue read, ~20 bounded GCS prefix probes, direct code read of every plausible writer) DISPROVES that premise:
  these 22 venues carry substantial `capture_status=captured` manifest rows (273-3,017 rows/venue, 100% coverage, zero
  `expected_unattempted`) that **first appeared in the DeFi honest-coverage rollup between 2026-08-02T23:27Z and
  2026-08-04** (absent in 5 earlier rollups checked back to 2026-07-10) — i.e. this is an ACTIVE, VERY RECENT manifest
  anomaly, not 2024-2026 legacy residue. No backing GCS object was found at any plausible canonical or legacy path for
  21/22 venues across ~20 bounded probes; the live DeFi pool catalogue (`prod/catalog.parquet`) itself is confirmed
  clean (bare, correctly-split venue+chain columns). The likely writer was NOT identified within this session's
  time/tooling (see Blocker) — filed as a big finding (data-correctness, cross-repo, actively regressing
  honest-coverage) per workspace findings-triage rather than executing a purge or fabricated fold against an unconfirmed
  population.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos:
  [market-tick-data-service, market-data-processing-service, instruments-service, deployment-api, unified-trading-pm]
scope: [engineer, admin]
tags: [defi, canonicalisation, composite-venue, manifest, honest-coverage, data-correctness, distinct-values, blocker]
related:
  [
    /plans/active/issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md,
    /plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md,
    /plans/archive/issues/defi_dex_pools_catalogue_undercoverage_vs_historical_capture_2026_07_28.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
created: 2026-08-04
author: ikennaigboaka [main·planning]
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: worsening-slowly
source: >-
  Operator/dispatching-session task: "fold the 22 non-canonical composite venues on the DeFi distinct-values panel",
  premised on mirroring the resolved 9-venue precedent. Investigation disproved the premise; this doc is the resulting
  big-finding writeup, not the originally-requested fold script.
resolved_by: interactive session 2026-08-05, root-caused via trace_composite_venue_provenance_2026_08_05.py
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md,
    instruments-service/scripts/enumerate_expected_universe.py,
    instruments-service/scripts/expand_defi_pool_catalogue_from_manifest_2026_07_31.py,
    market-tick-data-service/market_tick_data_service/live/connectors/dex_swap_scaffold_ws.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/canonical_write.py,
    market-tick-data-service/scripts/migrate_defi_pool_instrument_type_casing_2026_08_04.py,
  ]
---

> **🟢 ARCHIVED 2026-08-06** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Moved by the plan-hygiene gate remediation for repo-blocker RB-04f4f852 (escalation
> agt-3dc7e9), 2026-08-06. No content was rewritten.

# DeFi 22 underscored multi-chain composite venues — premise disproved, brand-new unresolved population (2026-08-04)

## What was asked vs. what was found

**Dispatched premise**: fold 22 `venue` values shown non-canonical on `GET /distinct-values/defi` (`AERODROME_V3-BASE`,
`BALANCER-{ARBITRUM,AVALANCHE,BASE,ETHEREUM,OPTIMISM,POLYGON}`, `CAMELOT_V3-ARBITRUM`, `CURVE-{AVALANCHE,ETHEREUM}`,
`PANCAKESWAP_V3-{BASE,BSC,ETHEREUM}`, `SUSHISWAP-ARBITRUM`, `SUSHISWAP_V3-{AVALANCHE,BASE,ETHEREUM}`,
`UNISWAP_V3-{ARBITRUM,BASE,ETHEREUM,OPTIMISM,POLYGON}`) — assumed to be the SAME shape as the already-resolved
[`defi_legacy_precanonical_composite_venue_objects_2026_07_24.md`](/plans/active/issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md)
precedent (9 venues, no-underscore protocol spellings, `-ETHEREUM` only, real 2024-05..2026-01 legacy GCS objects with
zero manifest rows, folded to canonical + registered 2026-08-01, `market-tick-data-service@13f14b78`, 5,332 objects →
324,867 canonical rows).

**Confirmed FIRST (per the dispatching session's own instruction) that the two populations are genuinely distinct**:
zero string overlap on protocol spelling (this population is underscore-canonical — `UNISWAP_V3` not `UNISWAPV3`,
`AERODROME_V3` not `AERODROMEV3`) except `CURVE` (no version suffix either way); this population spans 7 real chains
(ARBITRUM/AVALANCHE/BASE/BSC/ETHEREUM/OPTIMISM/POLYGON) vs. the precedent's `-ETHEREUM`-only. Confirmed via grep of both
this doc's own venue list against the precedent's 9 venues (`AAVEV3-ETHEREUM`, `CURVE-ETHEREUM`, `ETHENA-ETHEREUM`,
`ETHERFI-ETHEREUM`, `LIDO-ETHEREUM`, `MORPHO-ETHEREUM`, `UNISWAPV2/V3/V4-ETHEREUM`) — only `CURVE-ETHEREUM`
string-collides, and per the GCS check below, that collision is coincidental (a leftover, already-accounted-for artifact
of the OLD precedent, not new data).

**What execution actually found, in order**:

1. **Manifest-driven measurement (via the live honest-coverage rollup, not the raw ~1.7GB manifest index — see Blocker)
   shows real, substantial `captured` data, not the "real legacy tick-data, zero manifest rows" shape the precedent
   had.** `gs://central-element-323112-honest-coverage/2026-08-04/coverage.json` (`by_venue.defi`), all 22 venues:

   | venue                   | captured | expected_unattempted | coverage_pct | data_type      | instrument_type  |
   | ----------------------- | -------: | -------------------: | -----------: | -------------- | ---------------- |
   | AERODROME_V3-BASE       |      273 |                    0 |        100.0 | dex_pool_swaps | POOL (uppercase) |
   | BALANCER-ARBITRUM       |    3,010 |                    0 |        100.0 | dex_pool_swaps | POOL             |
   | BALANCER-AVALANCHE      |    2,058 |                    0 |        100.0 | dex_pool_swaps | POOL             |
   | BALANCER-BASE           |    2,002 |                    0 |        100.0 | dex_pool_swaps | POOL             |
   | BALANCER-ETHEREUM       |    3,004 |                    0 |        100.0 | dex_pool_swaps | POOL             |
   | BALANCER-OPTIMISM       |    2,135 |                    0 |        100.0 | dex_pool_swaps | POOL             |
   | BALANCER-POLYGON        |    2,758 |                    0 |        100.0 | dex_pool_swaps | POOL             |
   | CAMELOT_V3-ARBITRUM     |    2,289 |                    0 |        100.0 | dex_pool_swaps | POOL             |
   | CURVE-AVALANCHE         |    3,003 |                    0 |        100.0 | dex_pool_swaps | POOL             |
   | CURVE-ETHEREUM          |    3,003 |                    0 |        100.0 | dex_pool_swaps | POOL             |
   | PANCAKESWAP_V3-BASE     |    1,771 |                    0 |        100.0 | dex_pool_swaps | POOL             |
   | PANCAKESWAP_V3-BSC      |    2,450 |                    0 |        100.0 | dex_pool_swaps | POOL             |
   | PANCAKESWAP_V3-ETHEREUM |    2,835 |                    0 |        100.0 | dex_pool_swaps | POOL             |
   | SUSHISWAP-ARBITRUM      |    3,017 |                    0 |        100.0 | dex_pool_swaps | POOL             |
   | SUSHISWAP_V3-AVALANCHE  |    2,821 |                    0 |        100.0 | dex_pool_swaps | POOL             |
   | SUSHISWAP_V3-BASE       |    1,883 |                    0 |        100.0 | dex_pool_swaps | POOL             |
   | SUSHISWAP_V3-ETHEREUM   |    2,772 |                    0 |        100.0 | dex_pool_swaps | POOL             |
   | UNISWAP_V3-ARBITRUM     |    2,989 |                    0 |        100.0 | dex_pool_swaps | POOL             |
   | UNISWAP_V3-BASE         |    1,981 |                    0 |        100.0 | dex_pool_swaps | POOL             |
   | UNISWAP_V3-ETHEREUM     |    2,884 |                    0 |        100.0 | dex_pool_swaps | POOL             |
   | UNISWAP_V3-OPTIMISM     |    3,010 |                    0 |        100.0 | dex_pool_swaps | POOL             |
   | UNISWAP_V3-POLYGON      |    3,003 |                    0 |        100.0 | dex_pool_swaps | POOL             |

   Every row is `data_type=dex_pool_swaps` / `instrument_type=POOL` (uppercase), single data_type per venue. **Nothing
   is `expected_unattempted`** — ruling out "stale placeholder/denominator seed row" as the explanation (my working
   hypothesis for the first half of this investigation, before this measurement).

2. **TIMING — this is brand new, not legacy residue.** Fetched 6 earlier daily `coverage.json` rollups from the same
   bucket and checked the same venues:

   | rollup date              | AERODROME_V3-BASE         | UNISWAP_V3-ARBITRUM | (all 22, spot-checked)       |
   | ------------------------ | ------------------------- | ------------------- | ---------------------------- |
   | 2026-07-10T00:36:39Z     | absent (key not present)  | absent              | absent                       |
   | 2026-07-20T00:35:14Z     | absent                    | absent              | absent                       |
   | 2026-07-28T00:36:37Z     | absent                    | absent              | absent                       |
   | 2026-07-29 .. 2026-07-31 | absent                    | absent              | absent                       |
   | 2026-08-01T10:31:26Z     | absent                    | absent              | absent                       |
   | 2026-08-02T23:27:52Z     | absent                    | absent              | absent                       |
   | 2026-08-03               | rollup MISSING (cron gap) | —                   | —                            |
   | **2026-08-04 (today)**   | **captured=273**          | **captured=2,989**  | **all 22 present, captured** |

   So thousands of manifest rows per venue, 22 venues, materialised inside a **~29-40 hour window** (2026-08-02T23:27Z →
   sometime before today's rollup). This rules out "long-standing legacy residue nobody noticed" — matches instead the
   shape of a recent bulk backfill/registration run (one `written_at` cluster), the same pattern as the already-solved
   cross-AG contamination precedent's Pattern B (`defi_cefi_venue_chain_axis_contamination_2026_07_28.md`, 35 rows from
   one `backfill_orphan_class_e.py` `--apply` run).

3. **No backing GCS object located for 21/22 venues despite ~20 bounded prefix probes** (never a corpus-wide walk —
   every probe below is a single, explicit, bounded `list_blobs(prefix=...)` call):
   - Canonical split-hive shape
     (`raw_tick_data/by_date/day={D}/pipeline_mode=batch_onchain_subgraph/asset_group=defi/venue={PROTOCOL}/chain={CHAIN}/...`)
     on 2026-08-01: confirmed `UNISWAP_V3/chain=ETHEREUM` exists (real, current, correctly-split data) but **no
     `chain=ARBITRUM/BASE/OPTIMISM/POLYGON` sub-prefix exists under `venue=UNISWAP_V3/` on that day** — yet the manifest
     claims ARBITRUM/BASE/OPTIMISM/POLYGON are 100% captured. Full venue-prefix listing for that day/pipeline_mode found
     only 8 venues total
     (`AERODROME_V3, EIGENLAYER, SUSHISWAP, TRADER_JOE_V2, UNISWAP_V2, UNISWAP_V3, UNISWAP_V4, VELODROME_V2`) — no
     `BALANCER`, `CAMELOT_V3`, `PANCAKESWAP_V3` at all that day.
   - Combined-venue-as-one-segment shape (`.../asset_group=defi/venue={PROTOCOL}-{CHAIN}/...`, with and without a
     `pipeline_mode=` prefix): zero objects across all 22 venues × 4 sample days
     (2024-06-15/2025-06-15/2026-01-15/2026-07-15) — 88 checks, only exception below.
   - Legacy `dex_pools/{protocol}/{chain}/...` top-level prefix (the pre-2026-07-21 Solana fold's original shape):
     confirmed empty (0 objects) — consistent with that population's already-completed fold+delete.
   - **One exception**: `CURVE-ETHEREUM` has 3 objects at
     `raw_tick_data/by_date/day={2024-06-15,2025-06-15,2026-01-15}/asset_group=defi/venue=CURVE-ETHEREUM/ticks_migrated_20260418T*.parquet`
     — but these are the **already-accounted-for leftover SOURCE objects from the closed 2026-07-24/08-01 precedent
     fold** (same filename pattern `ticks_migrated_20260418T*`, same historical window, CURVE-ETHEREUM was one of that
     fold's original 9 venues, deliberately left un-deleted by that fold's own design). Per that precedent's own
     root-cause finding, objects at this legacy shape get **zero manifest representation** (`parse_hive_path()` → `None`
     → neither captured nor honest-absence), so these 3 objects are STRUCTURALLY UNABLE to be the source of
     CURVE-ETHEREUM's 3,003 `captured` manifest rows found in step 1 — coincidental string collision, not new data.

4. **The live DeFi pool catalogue is clean — ruling out the most obvious upstream candidate.** Downloaded + read the
   live `gs://instruments-store-defi-prd-central-element-323112/prod/catalog.parquet` directly (79,035 rows, small
   enough to fetch reliably unlike the manifest — see Blocker). Every row for
   BALANCER/PANCAKESWAP_V3/AERODROME_V3/CAMELOT_V3/SUSHISWAP/SUSHISWAP_V3 carries a **bare, correctly-split** `venue`
   column (`BALANCER`, `PANCAKESWAP_V3`, ...) with chain in its own separate `chain` column (`AVALANCHE`, `BSC`,
   `ETHEREUM`, `ARBITRUM`, `BASE`, `POLYGON`) — no combined venue string anywhere. This rules out the catalogue itself
   as the direct source, despite its suspicious timing correlation (see next point).

5. **Suspicious but unconfirmed timing correlation**: `instruments-service`'s DeFi pool catalogue historical-discovery
   backfill (`expand_defi_pool_catalogue_from_manifest_2026_07_31.py`) was run 2026-08-03T01:20:49Z, promoting
   `prod/catalog.parquet` 71,545 → 78,267 rows across 29 (venue,chain) pairs — including several of this doc's 22 venues
   (per
   [`defi_dex_pools_catalogue_undercoverage_vs_historical_capture_2026_07_28.md`](/plans/archive/issues/defi_dex_pools_catalogue_undercoverage_vs_historical_capture_2026_07_28.md),
   BALANCER/PANCAKESWAP_V3/SUSHISWAP/CAMELOT_V3 sit at 100% "catalogue never tracked this pool" gap — 786,490/794,142
   flagged addresses across the 8-protocol quantification are `balancer` alone). The standing daily
   `expected-universe-v2-defi` Cloud Run Job (01:30 UTC, reads the catalogue fresh every run) would have run against the
   freshly-expanded catalogue the same morning (2026-08-03 or 2026-08-04) — timing matches this doc's own
   captured-population appearance window closely. **However, this enumerator's own `--apply-write` code path
   (`_write_v2_per_vm_shard_chunk`, `enumerate_expected_universe.py:4169-4246`) is RULED OUT as the direct writer**: it
   unconditionally stamps `"row_count": 0` on every row it writes (line 4215) and its `ExpectedRow.capture_status` is
   always `"empty_confirmed"` or `"expected_unattempted"`, never `"captured"` — structurally incapable of producing the
   substantial-row-count `captured` rows found in step 1. So SOMETHING downstream of (or parallel to) the catalogue
   expansion + enumerator run is the real writer, not yet identified.

6. **Genuinely relevant but NOT the direct cause (documented for the next investigator, not a red herring to discard)**:
   `market_tick_data_service/live/connectors/dex_swap_scaffold_ws.py`'s `DEX_SWAP_SCAFFOLD_VENUES` tuple is a
   pre-existing (2026-07-06), SANCTIONED vocabulary of 22 combined `PROTOCOL-CHAIN` strings used as the **live
   WS-connector REGISTRY dispatch key** (a deliberately different namespace from the GCS/manifest venue+chain axis, per
   that module's own docstring: "grepping UAC's `unified_api_contracts/registry` — the SSOT of canonical (protocol x
   chain) venue keys"). 16 of this doc's 22 venues exact-match entries in that tuple (the mismatch: the scaffold also
   covers `UNISWAP_V2-ETHEREUM`/`UNISWAP_V4-ETHEREUM`/
   `TRADER_JOE_V2-AVALANCHE`/`VELODROME_V2-OPTIMISM`/`PANCAKESWAP_V3-ARBITRUM`, none of which are in this doc's 22; this
   doc additionally has `CURVE-AVALANCHE`/`CURVE-ETHEREUM`/`SUSHISWAP_V3-{AVALANCHE,BASE, ETHEREUM}`, none of which are
   in the scaffold tuple — overlapping but not identical vocabularies). This overlap is too precise (16/22) to be
   coincidental and is the single strongest lead for whoever picks this up. **Ruled out as the DIRECT writer** because:
   the scaffold's placeholder connector's `connect()` always raises `NotImplementedError` immediately (never emits a
   tick, confirmed by direct read of `DexSwapPlaceholderWSFeedConnector.connect()`), and only ONE real connector has
   shipped against this scaffold (`dex_swap_uniswap_v3_ws.py` → `UNISWAP_V3-ETHEREUM` only, per its own docstring "the
   other 21 scaffold venues are untouched"), and even that one connector's row-level venue stamp is bare lowercase
   (`"venue": "uniswap_v3"`, confirmed by direct read) — so this live path cannot explain captured rows for the other 21
   venues, or even fully explain UNISWAP_V3-ETHEREUM's (whose current GCS data was independently confirmed to sit
   correctly split, `venue=UNISWAP_V3/chain=ETHEREUM/`). **Best lead for the next investigator**: find whichever
   script/job iterates a UAC-registry-sourced combined `(protocol, chain)` key list (this `DEX_SWAP_SCAFFOLD_VENUES`
   tuple or its underlying UAC source) and calls `record_captured` using the tuple's own combined string as `venue=`
   directly, instead of splitting it first — the exact bug class already fixed once this session-week in
   `instruments-service/scripts/migration_orphan_sweep.py` (`instruments-service@f651ff8b`, 2026-08-04) for a
   structurally similar (though smaller, 35-row) case.

7. **Also ruled out, confirmed via direct code read (no live writer regression found in the paths checked)**:
   - `market_tick_data_service/cli/handlers/dex_pools_handler.py` / `_dex_pools_subgraph.py` — `venue=protocol` (bare,
     lowercase `_DEFAULT_PROTOCOLS` entry) passed to `write_defi_rows`/`record_captured` throughout.
   - `market_tick_data_service/cli/handlers/dex_swaps_handler.py` — same, `venue=protocol` bare.
   - `market_tick_data_service/market_interface/adapters/defi/canonical_write.py::write_defi_rows()` —
     `_normalize_venue()` is `venue.upper()` ONLY (its own docstring claims it "strips any trailing -CHAIN suffix" but
     the implementation never has, confirmed via `git log -p` back to this function's origin, `b9b37c87419e`, May 2026 —
     a real, longstanding docstring/code mismatch, but DEFENSIVE/dormant since no current caller passes a combined venue
     into this function) — so this function is a real place a FUTURE combined-venue bug could land silently if a caller
     regresses, but is not itself creating one today.
   - `instruments-service/scripts/enumerate_expected_universe.py::_enumerate_v2_defi` (per-instrument path) and
     `_yield_v2_defi_pre_launch_rows` (venue-grain pre-launch path) — both confirmed to emit BARE, correctly-split venue
     via `VenueMapping._canonicalise_defi_protocol_spelling` + `rsplit("-", 1)` (the 2026-06-21-dated "gotcha #3" fix in
     `/codex/02-data/defi-canonical-naming-ssot.md`) or `protocol.upper()` respectively.
   - `instruments-service/scripts/migration_orphan_sweep.py::shard_key_from_segments()` (post-`f651ff8b` fix,
     2026-08-04) — now guards its `PROTOCOL-CHAIN` split against `MAINNET_CHAIN_IDS`; for real chain suffixes like
     `ARBITRUM`/`BASE`/etc. this SPLITS correctly (not the bug source for THIS population, though it was the confirmed
     root cause of the structurally similar 35-row Pattern-B case in the sibling contamination doc).
   - A same-day (2026-08-04) sibling script,
     `market-tick-data-service/scripts/migrate_defi_pool_instrument_type_casing_2026_08_04.py`, confirms
     `instrument_type=="POOL"` (uppercase) is a KNOWN, independently-tracked, much LARGER pre-existing residue
     (1,919,789 rows across MTDS+MDPS combined, per that script's own 2026-08-04 census) — but that script only touches
     `instrument_type`, never `venue`/`chain`, so it explains why this doc's 22 venues carry uppercase `POOL` (a
     correlated, separately-known attribute) without explaining the venue combination itself.

## Why this is a big finding, not a fold-and-ship task

- **Data-correctness, actively regressing, not dormant**: unlike the resolved precedent (frozen 2024-2026 historical
  data, safe to fold at leisure), this population appeared within the last ~1.5 days and — if the writer is still active
  — may keep growing or recur on the next `expected-universe-v2-defi` Cloud Run Job cycle (01:30 UTC daily) or the next
  catalogue-expansion-adjacent backfill run.
- **Cross-repo, SSOT-adjacent**: touches `instruments-service` (catalogue + enumerator), `market-tick-data-service`
  (manifest, live-connector registry), and `deployment-api` (the panel surfacing it) — matches CLAUDE.md's "big finding"
  criteria (data-correctness / cross-repo / SSOT contradiction) verbatim.
- **Executing either candidate fix would be premature and risky given what's actually known**:
  - A **fold** (copy legacy GCS objects to canonical + register manifest rows, the originally-requested action) requires
    real source GCS objects to fold FROM — none were found for 21/22 venues despite extensive bounded probing.
    Fabricating a fold script against a population with no located backing data would either no-op (harmless but
    useless) or, worse, risk the investigator guessing wrong about where the "real" data lives and silently registering
    incorrect manifest rows.
  - A **purge** (delete the manifest rows as phantom/fabricated) was seriously considered but explicitly NOT executed: I
    cannot rule out that real backing data exists at a GCS path shape I did not think to try (my probes, while numerous,
    are not exhaustive), and if it does, deleting the manifest's only record of it would be a genuine, unrecoverable
    data-correctness regression — the opposite of safe. Per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`,
    a delete requires the five-part proof (twin resolves, content verified, no live writer, no live reader, twin
    coverage) — Part 1 (does a canonical twin exist with the SAME data) is UNRESOLVED here, not merely unverified: I
    don't know if this "captured" claim is fabricated or points at real data I simply haven't located, which is a
    categorically different, more dangerous state than the precedent's "twin doesn't exist, legacy source does" case.

## Blocker (measured, not a proxy for "ran out of time")

This session's interactive/local-like environment could not complete a full or column-filtered read of the live
`_index/availability_index.parquet` (~1.7 GB, ~33M+ rows) within reasonable time, blocking the row-level provenance
trace (`service_name` / `written_at` / `enumerator_run_id` columns, which WOULD conclusively identify the writer) that
this finding still needs:

- `unified_trading_library.manifest_writer.read_availability_index(bucket, columns=[...], filters=[("venue", "in", VENUES)])`
  (the documented "5MB for a bounded filter" fast path) — timed out at 100s+, repeatedly.
- A raw sequential `download_bytes()` of the full 1.73 GB consolidated index — observed effective throughput ~100-150
  KB/s in this session (would take 3+ hours), confirmed via direct file-size-growth monitoring, not guessed.
- `gcsfs` + `pyarrow.dataset` with a venue-`isin` filter (should support row-group-level predicate pushdown) — completed
  the schema/metadata read in ~10s (fast, small) but the actual filtered `to_table()` scan failed twice with
  `OSError: Couldn't deserialize thrift ... Deserializing page header failed` (a transient read-corruption/retry issue,
  not a design flaw in the approach).
- By contrast: single small-object downloads (`download_as_bytes` on an 8.6KB blob) completed in 1-2s reliably;
  `list_blobs` prefix listings completed in seconds throughout — the constraint is specific to large/many-request reads
  against the manifest object, not GCS access in general.
- **Independently corroborated as a real, known constraint**, not a session-specific fluke: the same-day
  `migrate_defi_pool_instrument_type_casing_2026_08_04.py` script's own docstring states "this is a manifest-index
  read-transform-write over the WHOLE `_index/availability_index.parquet` (~29M+ rows) — per
  `/codex/05-infrastructure/vm-launcher-runbook.md` § heavy-I/O rule this MUST run on a VM in-region, never from the
  operator's local machine" — i.e. this exact class of read is already known workspace-wide to need VM-grade
  network/compute, not an interactive session.

**What would unblock this**: run the row-level provenance query
(`SELECT venue, chain, service_name, written_at, enumerator_run_id, pipeline_mode, source FROM availability_index WHERE venue IN (<22 venues>)`)
from a proper in-region VM (per the heavy-I/O rule) or via a Cloud Run / BigQuery-backed read path rather than this
interactive session's local network path.

## RESOLVED 2026-08-05 — NOT a bug, NOT phantom data. False alarm from probing the wrong path/vocabulary.

**Root cause of this doc's own false "no backing data" verdict**: every GCS probe in this doc's original investigation
checked the MTDS `raw_tick_data/` path convention — but `service_name=market-data-processing-service` (identified via a
VM-run row-level provenance trace, `trace_composite_venue_provenance_2026_08_05.py`, the exact query this doc's own
Blocker section specified) writes to a COMPLETELY DIFFERENT top-level prefix in the SAME bucket:
`processed_candles/by_date/day={D}/pipeline_mode=batch_onchain_subgraph/timeframe={TF}/data_type=dex_pool_swaps/ instrument_type=POOL/venue={VENUE}/*.parquet`
— derived candle data, not raw ticks. This is the SAME wrong-vocabulary/wrong-path trap this workspace's own CLAUDE.md
already warns about (Solana AMM writes `instrument_type=solana_amm_pool`, not `pool` — this session made the analogous
mistake at the PATH-PREFIX level instead of the vocabulary level).

**Real backing data CONFIRMED** via a live `gcloud storage ls` check against MDPS's actual path shape, sampled across 4
dates (2023-01-01, 2024-06-01, 2025-01-01, 2025-06-01): real parquet objects exist for all 22 flagged venues, e.g.
`venue=SUSHISWAP_V3-AVALANCHE/SUSHISWAP_V3-AVALANCHE:POOL:0x8c29...parquet`, Creation Time `2026-08-03T22:00:38Z` —
squarely inside the flagged `written_at` window (2026-08-03T08:50:32Z..2026-08-04T08:52:52Z), proving this object was
genuinely copied, not fabricated.

**One-time, already-completed backfill campaign, NOT a live/recurring writer**: the code is
`market-data-processing-service/scripts/backfill_defi_dex_pool_swaps_source_correction.py` (`# Lifecycle: oneoff`),
launched via `deployment-service/scripts/vm/launch-backfill-defi-dex-swaps-source-correction-vm.sh` (a singleton-locked
one-off SPOT VM, never a Cloud Scheduler/Cloud Run Job — confirmed zero Terraform references anywhere). It copies
`dex_pool_swaps` bytes from a mistagged `pipeline_mode=batch_onchain_rpc` path to the correct
`pipeline_mode=batch_onchain_subgraph` path (`gcs_copy_object`, real content, no fabrication) and calls
`ManifestWriter(...).record_captured(...)` per cell. This campaign is independently documented in
`plans/archive/2026_08/mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md` (launched 2026-08-03T09:38Z, survived
5+ SPOT preemptions, terminal VERDICT at 2026-08-04T08:53:03Z:
`already_covered=6055 needs_copy=813150 copied=813150 recorded_cells=46683 copy_errors=0`) — matching this doc's own
flagged window end to within 11 seconds.

**Disposition**: no fold, no purge, no fix needed. The manifest rows are correct; the "big finding" is closed as a false
alarm caused by this doc's own investigation checking the wrong bucket path prefix. The remaining open question (NOT
urgent, NOT this doc's scope) is whether the DeFi distinct-values panel should exempt `processed_candles`-layer venues
from the same canonicalisation rule that flags composite `PROTOCOL-CHAIN` names as non-canonical in `raw_tick_data/` —
that's a panel-scoping question for whoever owns the distinct-values UI, not a data-correctness bug.

## Todos

- [x] ✅ [DIAG] P1. **DONE 2026-08-05.** Ran the row-level provenance query on a VM
      (`trace_composite_venue_provenance_2026_08_05.py`,
      `canonical-migration-defi-composite-venue-trace-20260805-183909`). Writer = `market-data-processing-service`,
      `pipeline_mode=batch_onchain_subgraph`, `source=onchain_subgraph`, `written_at`
      2026-08-03T08:50:32Z..2026-08-04T08:52:52Z (98,351 rows, 100% `capture_status=captured`).
- [x] ✅ [DIAG] P1. **DONE 2026-08-05 — one-off, already stopped, will NOT recur.** Confirmed via the script's own
      `# Lifecycle: oneoff` marker + zero Cloud Scheduler/Terraform wiring + the archived plan's own terminal VERDICT
      log line. No fix needed — it already finished successfully.
- [x] ✅ [DATA] P2. **DONE 2026-08-05 — real backing data CONFIRMED, no fold/purge needed.** Re-ran the GCS probe
      against MDPS's actual `processed_candles/` path (not the guessed `raw_tick_data/` paths this doc's original
      investigation tried) — real parquet objects exist for all 22 venues, content-timestamped inside the exact campaign
      window. See "RESOLVED" section above for full detail.

## Progress Log

- **2026-08-04 (initial investigation + writeup)**: confirmed distinctness from the 9-venue precedent per the
  dispatching session's own instruction; measured manifest capture_status via the honest-coverage rollup (full/filtered
  manifest reads blocked, see Blocker); pinned the appearance window to 2026-08-02T23:27Z..2026-08-04 via 6 historical
  rollup fetches; ran ~20 bounded GCS prefix probes across canonical, combined-segment, and legacy path shapes (all
  negative except CURVE-ETHEREUM's 3 already-accounted-for precedent-fold source objects); read + ruled out every
  plausible current writer (dex_pools_handler.py, dex_swaps_handler.py, canonical_write.py, dex_swap_uniswap_v3_ws.py,
  enumerate_expected_universe.py's two DeFi enumeration paths, migration_orphan_sweep.py post-fix); confirmed the live
  DeFi pool catalogue itself is clean (bare split venue+chain) via a direct download+read; identified
  `dex_swap_scaffold_ws.py`'s `DEX_SWAP_SCAFFOLD_VENUES` tuple as the strongest (16/22 exact-overlap) but
  not-yet-confirmed lead. Filed this doc rather than executing a fold (no source objects found) or a purge (cannot rule
  out real backing data existing at an untried path) against an unconfirmed population, per the delete-safety protocol's
  Part-1 requirement and this workspace's big-finding escalation rule.
