---
doc_type: issue
title: >-
  CURVE/OPTIMISM dex_pool_swaps subgraph has ZERO indexer allocations on The Graph network — 952 of the dex_pool_swaps
  long-tail's ~1,038 attempted_failed rows are a permanently-dead subgraph, not a retryable/schema bug
summary: >-
  While re-running mvp_backfill_defi_onchain_v10-002's G2 gate check, root-caused the previously-"unexplored across
  every prior session" dex_pool_swaps long tail (~1,038 attempted_failed rows outside the known 2026-06-28 phantom-
  reconciliation batch). 952 of those rows (92%) are CURVE/OPTIMISM, spanning date=2021-01-01..2026-06-25 with
  attempted_at as recent as 2026-07-10T21:06Z — i.e. this is not a stale one-time outage, every backfill attempt against
  this venue/chain still fails today. Live-probed the exact subgraph ID (`CXDZPduZE6nWuWEkSzWkRoJSSJ6CneSqiDxdnhhURShX`,
  from UAC `SUBGRAPH_IDS["curve"]["OPTIMISM"]`) directly against `gateway-arbitrum.network.thegraph.com` right now:
  `{"errors":[{"message":"subgraph not found: no allocations"}]}` — a 200-status GraphQL-level error meaning zero
  indexers on The Graph's decentralized network currently service this subgraph (it has been abandoned/de-indexed, not
  merely rate-limited or drifted). Cross-checked 5 other subgraphs behind the remaining long-tail's smaller error
  buckets (BALANCER/POLYGON, UNISWAP_V3/POLYGON, PANCAKESWAP_V3/BSC, UNISWAP_V3/BASE, UNISWAP_V3/ETHEREUM) — all 5
  responded 200 with fresh `_meta.block` timestamps (live, healthy, genuinely just schema-drifted for a handful of
  rows), so this "no allocations" condition is isolated to CURVE/OPTIMISM, not systemic.
  `dex_swaps_handler.py._execute_subgraph_query` only special-cases an HTTP 404 as `_SubgraphNotFoundError`
  (`thegraph_base_client.SubgraphNotFoundError`); this is a 200-with-`errors[]` response, so it falls into the generic
  `"errors" in result` branch, fails `_is_schema_drift_error`, and the cascade burns all 5 schema variants before
  raising `RuntimeError("...add a matching query schema or update the existing one")` — a misleading message, since no
  query/schema change can ever succeed against a subgraph with zero allocations. UAC's own `_defi.py` already documents
  the sibling case for this exact protocol ("ARB/POLY only on hosted service (deprecated) — use api.curve.fi instead");
  OPTIMISM was believed migrated to the decentralized network but has since lost its indexers too. The codebase already
  has a working Curve REST integration elsewhere
  (`market_tick_data_service/market_interface/adapters/defi/curve_adapter.py`, `live/connectors/curve_defi_ws.py`) that
  is NOT currently wired into the batch `dex_swaps_handler.py` cascade path.
status: open
nature: record
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [defi, dex_pool_swaps, curve, optimism, subgraph, the-graph, honest-absence, mvp-gate]
related:
  [
    plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    plans/active/defi_manifest_canonicalisation_2026_06_01.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-15
parent_epic: defi_master
source:
  [data_engineering slot-5, 2026-07-15, discovered while re-running mvp_backfill_defi_onchain_v10-002's G2 gate check]
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.24
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
last_updated: 2026-07-15
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
---

## What I found

`mvp_backfill_defi_onchain_v10-002`'s G2 gate (`attempted_failed=0 AND expected_unattempted=0` for all 6 MVP data_types)
has never passed `dex_pool_swaps` — 21,624 `attempted_failed` rows as of every prior session's coverage run. 20,586 of
those were already root-caused (2026-06-28 phantom-reconciliation reclassification, since re-run and fixed by slot-14's
`mtds-dex-swaps-backfill` launch). The remaining ~1,038-row long tail was flagged by slot-14 and slot-9 as "not
investigated this session" across every dispatch since. This session dug into it:

```
venue            error_reason (prefix)                                                          count
CURVE            All 5 cascade schemas returned GraphQL errors for curve/OPTIMISM (subgraph=CXDZP  952
UNISWAP_V3        TimeoutError                                                                      25
UNISWAP_V3        All 8 cascade schemas drifted for uniswap_v3/POLYGON                               24
BALANCER          balancer/POLYGON                                                                    8
PANCAKESWAP_V3    All 8 cascade schemas drifted for pancakeswap_v3/BSC                                 6
...                                                                                              (long tail, 1-5 each)
```

CURVE/OPTIMISM is 952 of ~1,038 (92%). `date` range for these rows is 2021-01-01→2026-06-25; `attempted_at` range is
2026-06-21T16:11Z→2026-07-10T21:06Z — this venue has been failing on every single backfill attempt for at least 3 weeks,
not a one-time blip.

**Live-reproduced right now** (not relying on stale manifest rows): direct POST to
`https://gateway-arbitrum.network.thegraph.com/api/{key}/subgraphs/id/CXDZPduZE6nWuWEkSzWkRoJSSJ6CneSqiDxdnhhURShX` (the
exact subgraph ID `unified_api_contracts.registry.capability_declarations._defi.SUBGRAPH_IDS["curve"]["OPTIMISM"]`
resolves) returns HTTP 200 with `{"errors":[{"message":"subgraph not found: no allocations"}]}` — The Graph's
decentralized network has zero indexers currently allocated to this subgraph. This is a **permanent, not transient**
condition (an indexer-economics/deprecation state, not a rate-limit or outage) until either a new indexer picks it up or
the code stops depending on it.

**Confirmed isolated, not systemic**: live-probed the subgraph IDs behind the next 5 largest long-tail error buckets
(BALANCER/POLYGON, UNISWAP_V3/POLYGON, PANCAKESWAP_V3/BSC, UNISWAP_V3/BASE, UNISWAP_V3/ETHEREUM) — all 5 returned fresh
`_meta.block.timestamp` values matching current chain heads. Those failures are genuine (much smaller-scale) schema
drift, unrelated to this finding.

**Root-caused why the cascade doesn't fail fast / classify honestly**: `dex_swaps_handler.py._execute_subgraph_query`
only converts an HTTP 404 into `_SubgraphNotFoundError` (via `thegraph_base_client.SubgraphNotFoundError`). A 200
response carrying a top-level `errors[]` (which is what "no allocations" is) instead falls into the generic
`if "errors" in result` branch (`_run_cascade`, ~L598-630): it's checked against `_is_schema_drift_error` (false — the
message doesn't match a schema-drift pattern), so it just logs a warning and returns `None`, causing the cascade to burn
all 5 CURVE schema variants before raising a generic
`RuntimeError("All 5 cascade schemas returned GraphQL errors ... Diagnose: add a matching query schema or update the existing one")`
— actively misleading, since no schema change fixes an unindexed subgraph. UAC's own `_defi.py` comment for this exact
protocol already flags the sibling case ("ARB/POLY only on hosted service (deprecated) — use api.curve.fi instead"), so
OPTIMISM going the same way is a known failure mode for this protocol, just not yet detected for this specific chain.

A working, unrelated Curve REST integration already exists in this repo
(`market_tick_data_service/market_interface/adapters/defi/curve_adapter.py`, `live/connectors/curve_defi_ws.py`) but is
not wired into the batch `dex_swaps_handler.py` cascade for `dex_pool_swaps`.

## Why it matters

- This gate cell (CURVE/OPTIMISM `dex_pool_swaps`) cannot be closed by re-running the existing backfill VM no matter how
  many times it's relaunched — every attempt will fail identically until the code either (a) stops querying a dead
  subgraph and reclassifies the window as an honest, typed absence, or (b) routes through the existing
  `curve_adapter.py`/`api.curve.fi` REST path instead. Continuing to relaunch `mtds-dex-swaps-backfill` against this
  cell burns compute for zero possible gain.
- The generic `RuntimeError` message actively misdirects the next engineer toward "add a schema" when the real fix is
  "this subgraph has no indexers, route around it or classify as absence" — worth fixing the classification even before
  deciding the data-sourcing question, so this doesn't cost another multi-session root-cause dig.
- Small blast radius: isolated to one (protocol, chain) pair out of ~40+ dex_pool_swaps (venue, chain) combinations
  checked; the other 5 spot-checked subgraphs in the same long tail are healthy.

## Recommended decision

1. **[SCRIPT] P2.** In `dex_swaps_handler.py`, recognize a 200-status GraphQL response whose `errors[]` message matches
   `subgraph not found: no allocations` (or more generally, any non-schema-drift GraphQL-level error that repeats across
   all 5 cascade schemas) as a **distinct, terminal condition** — do not raise the generic `RuntimeError`; instead
   raise/return a typed `_SubgraphNotFoundError`-equivalent (or a new `_SubgraphDeindexedError`) so the manifest writer
   can record an honest absence (e.g. `EXPECTED_SUBGRAPH_DEINDEXED`) instead of `attempted_failed`, matching this
   workspace's honest-absence-vs-attempted-failed convention (`/codex/02-data/honest-absence-downstream-handling.md`).
   Repo: `market-tick-data-service`.
2. **[DESIGN] P3.** Evaluate wiring the existing `curve_adapter.py`/`api.curve.fi` REST path into the batch
   `dex_pool_swaps` collection for CURVE/OPTIMISM (mirroring the "ARB/POLY only on hosted service" precedent already
   noted in UAC `_defi.py`) so this cell can actually capture real data instead of staying a permanent honest absence.
   Not urgent — `dex_pool_swaps` coverage for every OTHER venue is unaffected, and 952 rows is a small fraction of the
   asset_group's total gap. Repo: `market-tick-data-service`.
3. **[SCRIPT] P3.** Do the same live-subgraph-health spot-check for the remaining un-investigated long-tail buckets
   (`UNISWAP_V3` `TimeoutError`×25, `UNISWAP_V3`/POLYGON schema-drift×24, and the handful of 1-8-row buckets) —
   plausibly genuine transient/schema issues (all 5 sampled subgraphs from this session were healthy), but not confirmed
   row-by-row. Repo: `market-tick-data-service`.

## Verified live (2026-07-15, ~12:57Z)

- `SUBGRAPH_IDS["curve"]["OPTIMISM"]` = `CXDZPduZE6nWuWEkSzWkRoJSSJ6CneSqiDxdnhhURShX` — direct gateway probe returns
  `{"errors":[{"message":"subgraph not found: no allocations"}]}` (HTTP 200).
- 5 comparison subgraphs (BALANCER/POLYGON, UNISWAP_V3/POLYGON, PANCAKESWAP_V3/BSC, UNISWAP_V3/BASE,
  UNISWAP_V3/ETHEREUM) all returned live `_meta.block` data — confirms the dead-subgraph condition is isolated to this
  one (protocol, chain) pair, not a gateway-wide or API-key issue.
