---
doc_type: issue
title: >-
  UAC VENUES_BY_ASSET_GROUP["defi"] is missing 33 canonical ALL_DEFI_VENUES members, letting them silently mis-bucket as
  "cefi" in MTDS
summary: >-
  While sweeping the `.get(venue, "cefi")`-style silent-default resolvers tracked in
  sports_taxonomy_p1_capture_and_contracts_2026_08_08.md, found that UAC's `VENUES_BY_ASSET_GROUP["defi"]`
  (market_data_categories.py, 103 members) is missing 33 venues that ARE registered in `ALL_DEFI_VENUES`
  (defi_venues.py, 135 members) — all pipeline-mode-only DeFi venues (ALCHEMY-*, FLASHBOTS-ETHEREUM,
  MORPHO-ARBITRUM/OPTIMISM/POLYGON, COMPOUND-ETHEREUM, UNISWAP-ETHEREUM, STARGATE-ETHEREUM, ACROSS-ETHEREUM,
  METEORA/LIFINITY/PHOENIX-SOLANA, and others). Because `VENUE_TO_ASSET_GROUP` is derived directly from
  `VENUES_BY_ASSET_GROUP`, `.get(venue)` returns `None` (not `"defi"`) for these 33 venues. This let them silently
  escape MTDS's `_build_active_venues_for_date` DeFi-strip filter (which keyed off `VENUE_TO_ASSET_GROUP.get(v) ==
  "defi"`) and fall through into the CeFi tick-fetch path, where they would then hit the `.get(venue, "cefi")`-style
  resolvers this same sweep audited. Fixed the strip-filter escape as defense-in-depth (see Progress), but the UAC-side
  registry gap itself is the root cause and is still open.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service, instruments-service]
scope: [engineer]
tags: [defi, venue-registry, silent-default, asset-group-resolution, shard-level-failure-isolation, data-correctness]
related:
  [
    /plans/archive/2026_08/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
  ]
created: 2026-08-09
author: data_engineering (slot 20)
last_updated: 2026-08-09
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 1.0
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  ["sports_taxonomy_p1_capture_and_contracts_2026_08_08.md's `.get(venue, \"cefi\")` sweep todo, 2026-08-09"]
depends_on: []
context_scope:
  [
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
    unified-api-contracts/unified_api_contracts/registry/defi_venues.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/__init__.py,
    market-tick-data-service/market_tick_data_service/reader.py,
    /codex/04-architecture/shard-level-failure-isolation.md,
  ]
---

# UAC `VENUES_BY_ASSET_GROUP["defi"]` registry gap (2026-08-09)

## What I found

`sports_taxonomy_p1_capture_and_contracts_2026_08_08.md`'s Block B todo asked to sweep the remaining
`.get(venue, "cefi")`-style silent-default resolvers found in the 2026-08-08 `_asset_group_for_venue` enumeration pass
(a prior todo in the same plan had already fixed MTDS `reader.py`'s equivalent resolver, converting it to a typed
`UnknownVenueAssetGroupError` raise once a DeFi legacy-bare-alias gap was closed).

Measured (workspace `.venv-workspace`, live UAC registries):

```
tardis + defi venue universe (all_defi_venues ∪ tardis_to_venue.values()): 155
missing from VENUE_TO_ASSET_GROUP: 33
  AAVE_V3-ZKSYNC, MORPHO-ARBITRUM, COMPOUND_V3-POLYGON, ACROSS-ETHEREUM, MORPHO-POLYGON,
  UNISWAP-ETHEREUM, IDLE-POLYGON, ALCHEMY-BASE, BEEFY-POLYGON, ALCHEMY-ONCHAIN,
  FLASHBOTS-ETHEREUM, COMPOUND-ETHEREUM, ALCHEMY-POLYGON, ALCHEMY-OPTIMISM, IDLE-ARBITRUM,
  YEARN_V3-OPTIMISM, MORPHO-OPTIMISM, COMPOUND_V3-SCROLL, ALCHEMY-ARBITRUM, AAVE_V3-SCROLL,
  FRAX-ETHEREUM, PHOENIX-SOLANA, SUSHISWAP_V3-ARBITRUM, STARGATE-ETHEREUM, MORPHOVAULTS-ETHEREUM,
  METEORA-SOLANA, ALCHEMY-ETHEREUM, SUSHISWAP_V2-ARBITRUM, LIFINITY-SOLANA, EULER_V2-ARBITRUM,
  PANCAKESWAP_V3-ARBITRUM, FLUID-ARBITRUM
VENUES_BY_ASSET_GROUP["defi"] count: 103   ALL_DEFI_VENUES count: 135
```

All 33 are real, currently-registered `ALL_DEFI_VENUES` members (`defi_venues.py`, in
`unified-api-contracts/unified_api_contracts/registry/`), each with an explicit `"pipeline"`-mode comment
(backfill-only, not live-trading) — they are not stale/dead entries, they are legitimately part of the DeFi venue
universe UAC itself declares. They are simply absent from `VENUES_BY_ASSET_GROUP["defi"]` (`market_data_categories.py`
in the same directory), the dict `VENUE_TO_ASSET_GROUP` is mechanically derived from
(`{venue: ag for ag, venues in VENUES_BY_ASSET_GROUP.items() for venue in venues}`).

**Concrete measured live path this gap enables** (MTDS `market_tick_data_service/engine/orchestrator/ __init__.py`):

1. `tick_data_handler.py` defaults `_asset_groups = ["ALL"]` when no `--asset-group` flag is given (also directly
   reachable via an explicit `--asset-group defi`/`--asset-group all` run) — not a rare code path.
2. `get_venues_for_asset_groups(["ALL"])` extends the venue list with `_VENUE_MAPPING.all_defi_venues` — all 135
   members, including the 33 ungapped ones.
3. `_build_active_venues_for_date` is supposed to then strip every DeFi venue back out
   (`# DeFi venues stripped (use collect-* handlers)`) before dispatching to the CeFi-shaped `_process_venue`/tick-fetch
   path. Before this fix, that strip keyed off `VENUE_TO_ASSET_GROUP.get(v) == "defi"` alone — which returns `None` (not
   `"defi"`) for the 33 gap venues, so they silently SURVIVED the strip.
4. Surviving venues then reach `_process_venue` → `_check_instruments_available` (`preflight.py`) and the manifest-row
   writers (`manifest_finalize.py`), both of which resolve `VENUE_TO_ASSET_GROUP.get(venue, "cefi")` — the exact
   silent-default bug class this plan's sweep targets. For these 33 venues the default fires and wrongly stamps
   `asset_group="cefi"` (wrong instrument bucket, wrong manifest asset_group, wrong `get_primary_source` lookup).

## Why it matters

This is the same "wrong bucket is a silent wrong answer" bug class already fixed once for MTDS `reader.py` (sports
ODDS_API/FOOTYSTATS silently landing in the cefi bucket until 2026-08-08) and once more for DeFi legacy bare-name
aliases (ANKR/LIDO/UNISWAP_V2, same reader.py fix) — except this time the root cause is a genuine UAC registry gap
(missing entries), not a caller-side lookup-order bug. Left unfixed, any future consumer that trusts
`VENUE_TO_ASSET_GROUP` as a complete map over `ALL_DEFI_VENUES` will make the same silent-cefi mistake MTDS's
`_build_active_venues_for_date` made.

## Progress (this session, 2026-08-09, data_engineering slot 20)

Fixed the concrete, currently-live escape hatch as defense-in-depth (does NOT close the underlying UAC registry gap —
see the two follow-up todos below):

- `market-tick-data-service@8ba50fac` — `_build_active_venues_for_date`'s DeFi-strip filter now also checks
  `v in _VENUE_MAPPING.all_defi_venues`, not just `VENUE_TO_ASSET_GROUP.get(v) == "defi"`, so all 135 `ALL_DEFI_VENUES`
  members are stripped from the CeFi tick-fetch path regardless of the UAC registry gap.
- Added `logger.warning` breadcrumbs at the 4 `.get(venue, "cefi")`/`.get(venue_str, "cefi")` call sites this plan's
  sweep todo named (`preflight.py:_check_instruments_available`, `manifest_finalize.py: _write_bundle_shard_row` +
  `_write_shard_counts_to_manifest`, instruments-service `writers.py: _classify_venue_write`) so any FUTURE occurrence
  of an unregistered venue is now visible in logs instead of purely silent. **Deliberately NOT converted to a fail-loud
  raise** (unlike the `reader.py` precedent): all 4 call sites sit inside per-shard/per-venue loops with NO exception
  isolation (`asyncio.gather(*tasks)` in MTDS `_process_venue` has no `return_exceptions=True`; instruments-service's
  `for venue_name, venue_df in df.groupby("venue")` in `process_write.py` has no per-venue try/except) — a raise there
  would abort the WHOLE date's fetch/write run for every venue, not just the misclassified one, which is a worse
  operational outcome than today's silent-wrong-bucket bug and would violate the shard-level-failure- isolation
  architecture (`/codex/04-architecture/shard-level-failure-isolation.md`). Full reasoning is inline at each site.

## Progress (2026-08-09, data_engineering slot 23) — todo 1 closed, with a deliberate deviation from the literal text

Todo 1 asked to "add the 33 measured venues to `VENUES_BY_ASSET_GROUP[\"defi\"]`" — but its own verification clause
("check downstream consumers ... for any code that assumed the smaller (103-venue) set on purpose ... this may be
additive-only but verify") flagged exactly the trap that clause exists to catch: `VENUES_BY_ASSET_GROUP["defi"]` is NOT
a static list, it is computed as
`list(dict.fromkeys(v for v in _ALL_DEFI_VENUES if _DEFI_VENUE_PHASE.get(v) == "live"))` (market_data_categories.py,
same file) — deliberately narrowed to the IS-producible/"live"-phase subset as the honest-coverage denominator (see that
key's own comment). All 33 gap venues are `DEFI_VENUE_PHASE == "pipeline"` (confirmed in `defi_venues.py`), i.e. NOT
IS-producible by design. instruments-service's `test_defi_set_equals_uac_denominator_drift_guard`
(`tests/unit/test_orchestrator_helpers.py`) asserts EXACT set equality between `VENUES_BY_ASSET_GROUP["defi"]` and
`_build_defi_venues()` — adding the 33 pipeline venues there would have broken that cross-repo test and silently widened
the honest-coverage denominator with venues nothing captures yet (the same trap UAC's own
`test_defi_venues_sushiswap_arbitrum_registration.py:: test_new_venues_excluded_from_defi_denominator` locks down for 2
of these same 33 venues).

**Actual fix shipped** (`unified-api-contracts@7b96791e`): left `VENUES_BY_ASSET_GROUP["defi"]` untouched (still 103,
still == the IS-producible set) and instead extended `VENUE_TO_ASSET_GROUP` with a `"defi"` fallback for any
`ALL_DEFI_VENUES` member not already mapped —
`VENUE_TO_ASSET_GROUP.update({v: "defi" for v in _ALL_DEFI_VENUES if v not in VENUE_TO_ASSET_GROUP})`. This closes the
actual root cause (asset-group RESOLUTION for these 33 venues, which is what every `.get(venue, "cefi")`-style call site
in the "Concrete measured live path" above actually needs) without touching the denominator semantics. Verified:
`ALL_DEFI_VENUES - VENUE_TO_ASSET_GROUP.keys()` now returns `set()` (was 33); `VENUES_BY_ASSET_GROUP["defi"]` count
unchanged at 103; `VENUE_TO_ASSET_GROUP` now maps all 135 `ALL_DEFI_VENUES` members to `"defi"`. unified-api-contracts
full `quality-gates.sh` green on the shipped SHA. Did NOT run instruments-service's own test suite live (env issue in
this checkout unrelated to this change —
`ImportError: cannot import name 'iter_route_contexts' from 'fastapi.routing'`), but the drift-guard test only reads
`VENUES_BY_ASSET_GROUP["defi"]`, which this change never touches, so it cannot be affected by this diff.

> **Owner for the stale-venv / `iter_route_contexts` ImportError**:
> /plans/archive/2026_08/issues/stale_service_venvs_below_declared_fastapi_floor_2026_08_11.md

## Recommended decision

- [x] ✅ [CODE] P2. **Close the UAC registry gap itself** — `unified-api-contracts@7b96791e`. **Close the UAC registry
      gap itself**: add the 33 measured venues to `VENUES_BY_ASSET_GROUP["defi"]` in `market_data_categories.py`
      (`unified-api-contracts/unified_api_contracts/registry/`) so `VENUE_TO_ASSET_GROUP` becomes a complete map over
      `ALL_DEFI_VENUES`. Re-run the same enumeration this issue doc used
      (`ALL_DEFI_VENUES - VENUE_TO_ASSET_GROUP.keys()`) to confirm it returns empty. Check downstream consumers of
      `VENUES_BY_ASSET_GROUP["defi"]`/`VENUE_TO_ASSET_GROUP` for any code that assumed the smaller (103-venue) set on
      purpose before landing (e.g. EXPECTED_COVERAGE_BY_ASSET_GROUP, capability declarations) — this may be
      additive-only but verify. (repo: unified-api-contracts)
- [ ] [CODE] P3. **Add per-venue exception isolation** so the 4 sites hardened with a warning-log in this session can be
      safely upgraded to a fail-loud raise later: MTDS `_process_venue`'s `asyncio.gather(*tasks)` →
      `asyncio.gather(*tasks, return_exceptions=True)` + classify/log each exception via UAC `classify_venue_error()`
      rather than letting one bad venue crash the whole date; and instruments-service's
      `for venue_name, venue_df in df.groupby("venue")` write loop in `process_write.py` wrapped with a per-venue
      try/except that logs + continues rather than aborting the batch. Once isolated, the 4 `.get(venue, "cefi")`
      defaults touched in this session's Progress Log can follow the `reader.py` precedent and become typed raises.
      (repos: market-tick-data-service, instruments-service)
