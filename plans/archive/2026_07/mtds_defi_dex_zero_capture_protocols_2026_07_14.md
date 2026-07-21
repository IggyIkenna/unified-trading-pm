---
doc_type: plan
title: MTDS dex_pools/dex_swaps zero-forward-capture fix — uniswap_v2, uniswap_v4, trader_joe_v2, velodrome_v2
summary:
  4 DeFi protocols have zero forward capture in market-tick-data-service's dex_pools_handler.py/dex_swaps_handler.py —
  not because instruments-service reference-data adapters are missing (they exist and produce real rows), but because
  MTDS's own protocol dispatch (_DEFAULT_PROTOCOLS list + fallbacks dict in _dex_pools_subgraph.py) never registered
  these 4 protocols. Fix is per-protocol dispatch wiring, not new adapter classes — 2 protocols (velodrome_v2,
  trader_joe_v2) reuse an existing Messari-schema query template with zero new code; uniswap_v4/uniswap_v2 need a new
  query template + parser each.
status: active
nature: design
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, dex-pools, dex-swaps, capture-gap, subgraph, uniswap, velodrome, trader-joe]
related:
  [
    issues/instrument_id_format_canonicalization_2026_07_08.md,
    issues/defi_dead_storage_shape_b_cleanup_candidate_2026_07_10.md,
  ]
created: 2026-07-14
last_updated: 2026-07-14
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  "Operator, 2026-07-14: confirmed 'Real gap — build capture code for all 4' in response to the 4-zero-capture-protocol
  finding from instrument_id_format_canonicalization_2026_07_08.md:611. A fresh scoping pass (2026-07-14) corrected the
  original framing: the gap is in market-tick-data-service's dispatch tables, not instruments-service adapters (which
  already work for all 4 protocols)."
assigned_role: backend_engineer
drift_direction: advance-code
---

# MTDS dex_pools/dex_swaps zero-forward-capture fix

## 1. Background

`instrument_id_format_canonicalization_2026_07_08.md:611` found "uniswap_v2/uniswap_v4/trader_joe_v2/velodrome_v2 have
zero forward capture code at all in dex_pools_handler.py/dex_swaps_handler.py" — originally read as an
instruments-service reference-data gap. A 2026-07-14 scoping pass (research-only, no writes) corrected this: IS already
has working, wired adapters for all 4 protocols (`uniswap_v2.py`, `uniswap_v4.py` standalone; `velodrome_v2` and
`trader_joe_v2` routed through `UniswapV3ReferenceDataAdapter(protocol_slug=...)` via UAC's `PROTOCOL_TO_ADAPTER_KEY`),
confirmed by real non-zero POOL row counts in `prod/catalog.parquet` (UNISWAP_V4=413, TRADER_JOE_V2=304,
VELODROME_V2=96, UNISWAP_V2=24 — per `instruments-service/docs/DEFI_INSTRUMENTS.md`, 2026-07-09).

The real gap is in `market-tick-data-service`: `cli/handlers/dex_pools_handler.py`'s `_DEFAULT_PROTOCOLS` (line 196)
omits all 4 protocols, and `_dex_pools_subgraph.py`'s `fallbacks` dict (lines 207-217) has no entry for any of them — an
unlisted protocol just warns and returns an empty DataFrame. `dex_swaps_handler.py` imports the same
`_DEFAULT_PROTOCOLS` and is assumed (not yet independently verified — first todo below) to have the same dispatch
pattern via its own query/dispatch file.

## 2. Per-protocol scope (revised ordering from the 2026-07-14 scoping pass)

- **velodrome_v2, trader_joe_v2 — trivial, tied easiest.** Both use the Messari schema (`liquidityPoolDailySnapshots`)
  already implemented for `curve`/`sushiswap`/`gmx` (`_CURVE_QUERY`/`_parse_curve`, "messari_basic" `_Entry`). Fix = add
  both protocol slugs to `_DEFAULT_PROTOCOLS` + `fallbacks["velodrome_v2"] = [messari_basic]` /
  `fallbacks["trader_joe_v2"] = [messari_basic]`. **No new query template or parser.**
- **uniswap_v4 — second.** Subgraph exposes `pools{totalValueLockedUSD}`, close to V3's native shape but not confirmed
  identical — needs a new `_UNISWAP_V4_QUERY[_FILTERED]` (verify the daily-snapshot entity is `poolDayDatas` like V3,
  not something else, before writing the parser) in `dex_pools_handler.py`, likely reusable `_parse_uniswap_v3` in
  `_dex_pools_parsers.py` if the shape matches, + a `fallbacks["uniswap_v4"]` entry.
- **uniswap_v2 — hardest.** No `feeTier`; uses `pairs`/`pairDayDatas`, not `pools`/`poolDayDatas` — a genuinely
  different schema. Closest template is either the SushiSwap-legacy `pairs` handling
  (`_SUSHISWAP_CUSTOM_QUERY`/`_parse_sushiswap_custom`) or porting IS's own `uniswap_v2.py::_PAIRS_QUERY_TEMPLATE`.
  Needs a new `_UNISWAP_V2_QUERY[_FILTERED]` + a new `_parse_uniswap_v2` in `_dex_pools_parsers.py` + a
  `fallbacks["uniswap_v2"]` entry.

All 4: same fix pattern presumed to apply symmetrically to `dex_swaps_handler.py`'s own dispatch — **not yet
independently verified**, first todo below.

## 3. Todos

- [x] ✅ [BACKEND] P1. Read `dex_swaps_handler.py` + its query/dispatch module — confirmed real filenames
      (`_dex_swaps_queries.py`) and found the dispatch pattern DIFFERS from dex_pools: an ordered
      `(query,     schema_name)` cascade selected by set-membership (`_build_cascade`), not a per-protocol `fallbacks`
      dict. §2 updated accordingly — `market-tick-data-service@476d30994`.
- [x] ✅ [BACKEND] P1. Wired `velodrome_v2` + `trader_joe_v2` into both `dex_pools_handler.py`'s `_DEFAULT_PROTOCOLS` +
      `fallbacks` dict (reusing `messari_basic`, zero new queries) AND `_dex_swaps_queries.py`'s `_DEFAULT_PROTOCOLS`
      (default messari-first cascade, also zero new queries). Unit tests added — `market-tick-data-service@476d30994`.
- [x] ✅ [BACKEND] P1. Verified the real uniswap_v4 subgraph shape against the official `Uniswap/v4-subgraph` schema
      (fetched live). Pools side: `poolDayDatas`/`pool{...}` matches V3's shape exactly, reused `_parse_uniswap_v3`.
      Swaps side: the real `Swap` entity has **no `recipient` field** (replaced with `origin`) — reusing the univ3 swaps
      cascade would have exhausted every fallback via schema drift and produced zero rows. Caught by adversarial review
      before shipping; fixed with a dedicated `_UNISWAP_V4_SWAPS_QUERY` + `_parse_uniswap_v4_swaps` (maps
      `origin`→`recipient` output column) and its own single-entry cascade. Unit tests added —
      `market-tick-data-service@476d30994`.
- [x] ✅ [BACKEND] P1. Implemented `_UNISWAP_V2_QUERY[_FILTERED]` (pairs/pairDayDatas shape, no feeTier — hardcoded
      30bps) + `_parse_uniswap_v2` in `_dex_pools_parsers.py`, wired `fallbacks["uniswap_v2"]`; swaps side got its own
      `_UNISWAP_V2_SWAPS_QUERY` (`amount0In`/`amount1In`/`amount0Out`/`amount1Out` directional shape) +
      `_parse_uniswap_v2_swaps`. Verified against the real, long-stable public `Uniswap/v2-subgraph` schema. Unit tests
      added — `market-tick-data-service@476d30994`.
- [x] ✅ [BACKEND] P1. Applied the 4-protocol wiring to `dex_swaps_handler.py`'s dispatch — confirmed it needed
      protocol-specific handling, not a blind mirror of dex_pools (per todo 1's finding): uniswap_v2 and uniswap_v4 each
      got dedicated cascade entries, velodrome_v2/trader_joe_v2 use the default cascade. Unit tests added —
      `market-tick-data-service@476d30994`.
- [x] ✅ [SCRIPT] P1. Full `market-tick-data-service` quality-gates run (green, 48s) — hit and fixed one real gate
      violation along the way (`dex_swaps_handler.py` grew past the 900-line file cap; relocated the new V4 swaps parser
      to the module-level `_dex_swaps_queries.py`, matching the existing `_parse_uniswap_v2_swaps` pattern, to land
      exactly at the cap). Quickmerge shipped `market-tick-data-service@476d30994`.
- [x] ✅ [DATA] P2. **Real end-to-end smoke run, all 8 shard combinations (4 protocols × pools/swaps), real day
      (2026-07-12), real live subgraph calls — 100% success, zero errors:**

      | protocol       | chain     | pools rows | swaps rows |
                                  | -------------- | --------- | ---------: | ---------: |
                                  | velodrome_v2   | OPTIMISM  |        296 |       1000 |
                                  | trader_joe_v2  | AVALANCHE |        950 |       1000 |
                                  | uniswap_v4     | ETHEREUM  |       1000 |       1000 |
                                  | uniswap_v2     | ETHEREUM  |       1000 |       1000 |

                                  Called `_query_and_parse`/`_run_cascade` directly against the real subgraph endpoints (bypassing manifest
                                  writes, so nothing touched prod GCS) with a real loaded `TheGraph` API key pool (9 keys). uniswap_v4's swaps
                                  side — the exact shard the adversarial review's uniswap_v4/`recipient` finding predicted would fail — came back
                                  1000 real rows with the `token_a`/`token_b` normalized columns present, confirming the dedicated-query fix
                                  actually works against the live schema, not just the unit tests. velodrome_v2/trader_joe_v2 pools legitimately
                                  hit the messari-schema-drift fallback path once each before landing on the working schema — expected cascade
                                  behavior, not an error.

- [x] ✅ [BACKEND] P2. **CORRECTION to the todo below's original claim: the 4 protocols ARE already MVP — no scope
      change needed.** My first check used wrong parameter names (`is_mvp(venue="UNISWAP_V2", data_type="dex_pools")` —
      bare venue instead of the real chain-suffixed form, and a made-up `data_type` label instead of the real canonical
      ones). Re-tested with the actual values (`venue="UNISWAP_V2-ETHEREUM"`, `instrument_type="POOL"`,
      `data_type="dex_pool_state"`/`"dex_pool_swaps"` — the real constants from `dex_pools_handler.py`'s
      `_DEX_POOLS_DATA_TYPE` / `dex_swaps_handler.py`'s `_DEX_SWAPS_DATA_TYPE`): all 4 protocols return `is_mvp=True`,
      identically to `UNISWAP_V3-ETHEREUM` (control). v13's "DeFi MVP = every IS-producible venue" ruling already covers
      them via `_mvp_defi_venues()` (all 4 have `DEFI_VENUE_PHASE="live"`) + `_mvp_defi_data_types()` (both
      `dex_pool_state`/`dex_pool_swaps` are in the full DeFi data_type set). No UAC change shipped — none needed.
- [x] ✅ [BACKEND] P2. **Checked whether `/data-pipeline-check-mtds` will now exercise these protocols — yes,
      automatically**, once real historical data exists for them (see backfill below); the skill's matrix reads
      `is_mvp()` live, so it needs no code change either.
- [x] ✅ [INFRA] P1. **Verified single write path before backfilling (no repeat of the shape-B/TradFi-CME bucket-name
      class of bug)**: both `dex_pools_handler.py` (`get_write_bucket_name("market_data", "defi")`) and
      `dex_swaps_handler.py` (`resolve_bucket_name(cloud="gcp", kind="market-data", asset_group="defi")`) resolve to the
      identical canonical env-tiered bucket `market-data-tick-defi-prd-central-element-323112`. Confirmed its manifest
      consolidator (`uts-prod-manifest-consolidator-market-data-defi`) is the only one, cron ENABLED, and the manifest
      is fresh (updated within the last hour) — no paused/legacy sibling consolidator watching a different bucket name
      for this asset_group.
- [x] ✅ [INFRA] P1. **Launched backfill VMs for the 4 protocols, scoped (not a full re-run of all 13 protocols)**:
      added a `--protocols` passthrough (`VM_DEX_POOLS_PROTOCOLS`/`VM_DEX_SWAPS_PROTOCOLS` metadata keys, mirroring the
      existing `VM_LENDING_PROTOCOLS` pattern) to `setup-data-pipeline-vm.sh` +
      `launch-mtds-dex-{pools,swaps}-backfill-vm.sh` — `deployment-service@ecb956e8e`. Launched both
      `mtds-dex-pools-backfill` and `mtds-dex-swaps-backfill` (2023-01-01→today, SPOT,
      `--protocols     "velodrome_v2;trader_joe_v2;uniswap_v4;uniswap_v2"` — semicolons, not commas, to avoid colliding
      with gcloud's `--metadata` key-separator). Found + deleted a dead `mtds-dex-swaps-backfill` VM first (TERMINATED
      since 2026-06-27, heartbeats stopped ~12h before this launch — a stale leftover, not live work) before relaunching
      under that name. Both VMs confirmed `RUNNING` at launch; tarball-freshness warnings for mtds/UAC were checked
      against real git ancestry (`git merge-base --is-ancestor`) and confirmed to already include both the
      canonical_instrument_id/glued_pair_id fix and this plan's own capture-code fix — the "stale" tarballs just trailed
      HEAD by unrelated sibling commits, not missing anything this backfill needs.
- [ ] [DATA] P2. Verify the backfill VMs actually produced real historical rows once they've run a while — spot-check
      row counts + manifest `capture_status=captured` for a sample of dates for each of the 4 protocols, both
      dex_pool_state and dex_pool_swaps.
- [ ] [BACKEND] P3. Post-phase codex audit — check whether `codex/02-data/defi-canonical-naming-ssot.md` documents the
      dex_pools/dex_swaps protocol dispatch list; update if it asserts the old (incomplete) set.

## Progress Log

- **2026-07-14** — Plan authored from the 2026-07-14 scoping pass's findings (operator already confirmed this is real,
  in-scope work). Implementation done via a verify→implement→adversarial-review workflow: the verify pass corrected 2 of
  the plan's own assumptions (dex_swaps dispatch pattern; IS adapters give no evidence about daily-snapshot entity
  shapes), the adversarial review caught one real, concrete, would-have-shipped-broken bug (uniswap_v4 swaps reusing a
  query field that doesn't exist in the real v4 schema) before it reached prod. Fixed directly, quality-gates verified
  green, shipped `market-tick-data-service@476d30994`. Remaining: real end-to-end smoke test (P2) and codex audit (P3).
