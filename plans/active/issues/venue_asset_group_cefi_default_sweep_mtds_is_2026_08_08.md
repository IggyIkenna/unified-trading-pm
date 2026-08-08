---
doc_type: issue
title: Sweep for `.get(venue, "cefi")`-class silent asset-group defaults beyond MTDS reader.py — 4 sites found, not yet fixed
summary: >-
  Follow-up from `sports_taxonomy_p1_capture_and_contracts_2026_08_08.md`'s "Make MTDS's `_asset_group_for_venue` FAIL
  LOUD instead of defaulting to cefi" todo. That todo's own text asked for a sweep of "other `.get(..., <default asset
  group>)` lookups in the same class of resolver across MTDS/MDPS/IS" — the READ-path defect in
  `market_tick_data_service/reader.py::_asset_group_for_venue` is fixed (raises `UnknownVenueAssetGroupError` now,
  `market-tick-data-service` this commit), but the sweep surfaced 4 more sites carrying the exact same
  `.get(venue, "cefi")` silent-default shape, all left UNFIXED — 3 in MTDS write/manifest-finalize code, 1 in
  instruments-service's manifest writer. MDPS was swept and is clean: its own
  `config.py::get_asset_group_for_venue` already returns `None` on an unknown venue (the correct pattern), not a
  silent default.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer]
tags: [venue-asset-group, silent-default, data-correctness, honest-absence, sweep-followup]
related:
  [
    /plans/active/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-08-08
author: data_engineering (slot 27)
source: ["sports_taxonomy_p1_capture_and_contracts_2026_08_08.md, MTDS `_asset_group_for_venue` fail-loud todo"]
assigned_vm: planning
---

# Sweep for `.get(venue, "cefi")`-class silent asset-group defaults — 4 unfixed sites

## What I found

Grepped both repos for the exact defect shape fixed in
`market_tick_data_service/reader.py::_asset_group_for_venue` — a `VENUE_TO_ASSET_GROUP.get(venue, "cefi")` (or
`.get(venue, "cefi").lower()`) call, i.e. an unconditional default to the `cefi` asset group for a venue this
process cannot classify, rather than a `None`/raise. This is the SAME bug class the 2026-08-08 sports venue-axis
split proved dangerous: 146,163 ODDS_API/FOOTYSTATS shards silently misrouted to the cefi bucket when those tokens
dropped out of `VENUE_TO_ASSET_GROUP`.

**Fixed this task** (read path):

- `market-tick-data-service/market_tick_data_service/reader.py:203` (`_asset_group_for_venue`) — now raises
  `UnknownVenueAssetGroupError` (`market_tick_data_service/reader_errors.py`).

**NOT fixed — same shape, different (write/finalize-path) blast radius, needs its own review**:

1. `market-tick-data-service/market_tick_data_service/engine/orchestrator/preflight.py:428` —
   `cat = _orch.VENUE_TO_ASSET_GROUP.get(venue, "cefi")` inside `_check_instruments_available`, used to pick the
   instruments bucket to probe. Lower risk: wrapped in a broad `except (..., Exception): return False`, so raising
   here would likely just make an unregistered venue read as "no instruments" (same effective outcome as today,
   minus the risk of probing the WRONG bucket and getting a false hit).
2. `market-tick-data-service/market_tick_data_service/engine/orchestrator/manifest_finalize.py:195` —
   `ag = _orch.VENUE_TO_ASSET_GROUP.get(venue_name, "cefi").lower()`, used to gate CME options/futures-chain
   "not-listed" sub-shard emission. Manifest-WRITE path.
3. `market-tick-data-service/market_tick_data_service/engine/orchestrator/manifest_finalize.py:375` —
   `_row_ag = _orch.VENUE_TO_ASSET_GROUP.get(venue_name, "cefi").lower()`, used to resolve `get_primary_source(...)`
   for a manifest row's `source` column when pipeline_mode has no extractable source. Manifest-WRITE path.
4. `instruments-service/instruments_service/engine/orchestrator/writers.py:286` —
   `_cat = "defi" if manifest_chain else (VENUE_TO_ASSET_GROUP.get(venue_str, "cefi"))`, used to stamp the
   asset-group category on non-DeFi instrument-definition manifest rows. Manifest-WRITE path — **arguably the
   highest-severity of the four**: a wrong category here PERSISTS in the manifest (a bad write is durable) rather
   than just misdirecting one read.

## Why it matters

Same silent-wrong-answer shape as the fixed reader.py bug: a venue that is genuinely new/unregistered (or a typo)
gets classified as `cefi` with no signal, so downstream code reads/writes the WRONG bucket/category with no error
and no log line distinguishing it from a real cefi venue. Sites 2-4 are on the WRITE side, so a bad classification
here can land a permanently-mis-stamped manifest row, not just a transient bad read.

## Why I didn't fix these in the same commit

The parent todo's own text scoped the risk explicitly: "a genuinely-unknown cefi venue currently relies on this
default, so the raise needs its own enumeration pass first" — that caution applied to the READ path (reader.py,
now fixed with its own enumeration: 2 unit tests + 1 integration-style test asserting the old cefi-default
behavior were found and updated to assert the raise instead, no other call site relied on it). The 4 sites above
are write/finalize-path, used by the LIVE instrument-capture and manifest-finalize orchestrators — flipping them
to raise without individually verifying no in-flight venue currently depends on the default (and without the
corresponding test updates, which I have not audited for these files) risks breaking live capture, which is
explicitly out of this task's declared scope (`[CODE] P1. Make MTDS's _asset_group_for_venue FAIL LOUD` — singular,
named function).

## Recommended decision

- [ ] [CODE] P2. Fix `market-tick-data-service/market_tick_data_service/engine/orchestrator/preflight.py:428` —
      replace `.get(venue, "cefi")` with `.get(venue)` + explicit `None`-handling (the existing broad
      `except (..., Exception): return False` already absorbs a raise safely; confirm via a targeted test with an
      unregistered venue). (repo: market-tick-data-service)
- [ ] [CODE] P2. Fix `market-tick-data-service/market_tick_data_service/engine/orchestrator/manifest_finalize.py:195`
      and `:375` — replace both `.get(venue_name, "cefi").lower()` sites with a raise/loud-log, after enumerating
      whether any currently-live venue relies on the cefi default reaching this code path (CME options/futures-chain
      gating + primary-source resolution). (repo: market-tick-data-service)
- [ ] [CODE] P2. Fix `instruments-service/instruments_service/engine/orchestrator/writers.py:286` — replace
      `VENUE_TO_ASSET_GROUP.get(venue_str, "cefi")` with a raise/loud-log before it stamps a manifest row's
      asset-group category; this is the highest-severity of the four (persists a wrong category into the
      manifest). Enumerate whether any currently-live venue relies on this default first. (repo: instruments-service)
