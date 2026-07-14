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
assigned_role: backend-engineer
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

- [ ] [BACKEND] P1. Read `dex_swaps_handler.py` + its query/dispatch module (name TBD — confirm real filename, the
      `_dex_pools_subgraph.py` naming was a guess by analogy) and confirm/refute whether it mirrors
      `dex_pools_handler.py`'s `_DEFAULT_PROTOCOLS`/`fallbacks` dispatch pattern exactly, or differs. Update this plan's
      §2 if it differs before proceeding.
- [ ] [BACKEND] P1. Wire `velodrome_v2` + `trader_joe_v2` into `dex_pools_handler.py`'s `_DEFAULT_PROTOCOLS` +
      `_dex_pools_subgraph.py`'s `fallbacks` dict (reuse `messari_basic`). Add/extend unit tests covering both new
      dispatch entries.
- [ ] [BACKEND] P1. Verify the real uniswap_v4 subgraph daily-snapshot entity shape (read IS's `uniswap_v4.py` query +,
      if feasible, a live/cached subgraph schema introspection) before writing `_UNISWAP_V4_QUERY`. Implement
      `_UNISWAP_V4_QUERY[_FILTERED]` + wire `fallbacks["uniswap_v4"]`, reusing `_parse_uniswap_v3` if the shape matches
      or a new parser if it doesn't. Unit tests.
- [ ] [BACKEND] P1. Implement `_UNISWAP_V2_QUERY[_FILTERED]` (pairs/pairDayDatas shape) + `_parse_uniswap_v2` in
      `_dex_pools_parsers.py` + wire `fallbacks["uniswap_v2"]`. Unit tests.
- [ ] [BACKEND] P1. Apply the same 4-protocol wiring to `dex_swaps_handler.py`'s dispatch (path/design depends on todo
      1's finding — may reuse the same query templates or need swap-specific ones; do not assume without checking). Unit
      tests.
- [ ] [SCRIPT] P1. Full `market-tick-data-service` quality-gates run, quickmerge ship.
- [ ] [DATA] P2. Real end-to-end smoke: run `dex_pools_handler`/`dex_swaps_handler` for each of the 4 protocols against
      a real (small, bounded) date range and confirm non-empty, schema-valid rows — not just unit-test green. Evidence:
      row counts + a sample row per protocol.
- [ ] [BACKEND] P3. Post-phase codex audit — check whether `codex/02-data/defi-canonical-naming-ssot.md` documents the
      dex_pools/dex_swaps protocol dispatch list; update if it asserts the old (incomplete) set.

## Progress Log

- **2026-07-14** — Plan authored from the 2026-07-14 scoping pass's findings (operator already confirmed this is real,
  in-scope work). Implementation not yet started.
