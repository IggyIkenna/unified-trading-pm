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
last_updated: 2026-07-24
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

> **🟢 2026-07-24 — reason taxonomy + historical reclassification SHIPPED** (see Progress log). The numbered list below
> was the original recommendation; converted to checkboxes here so future todo-counters (grep-based, `- [ ]` only) don't
> silently miss this doc's open items the way the closeout plan's own audit did (it counted this doc as "0 open todos
> (closed)" purely because it used a numbered list, not checkboxes — that miscount is the reason this conversion
> exists).

- [x] [BACKEND] P1. **Add the `EXPECTED_SUBGRAPH_DEINDEXED` reason** to `EmptyConfirmedReason` (unified-api-contracts)
      so a permanently-deindexed subgraph can be recorded as honest `empty_confirmed` instead of `attempted_failed`.
      **SHIPPED** `unified-api-contracts@e893e5c9` — repo: `unified-api-contracts`.
- [x] [DATA] P1. **Write + dry-run-verify the CURVE/OPTIMISM `dex_pool_swaps` `attempted_failed` reclassification
      script** → `empty_confirmed[EXPECTED_SUBGRAPH_DEINDEXED]` via a one-shot manifest script (mirrors
      `reclassify_defi_reference_only_eu_2026_07_21.py`'s pattern: consolidated index + per_vm shards,
      backup-then-write, idempotent). **Script SHIPPED + dry-run VERIFIED** — `instruments-service@73100d4e`,
      `scripts/reclassify_defi_curve_optimism_subgraph_deindexed_2026_07_24.py`. Full result + evidence in "Verified
      live (2026-07-24)" below.
- [ ] [DATA] P1. **Run `--apply` on a VM + verify the manifest rows actually flipped.** Blocked by the heavy-I/O hard
      rule (must run on a VM, not locally). Per `defi_consolidated_closeout_2026_07_18.md`'s tracking of this same
      action: **NOT YET RUN** — 2 VM-launch attempts 2026-07-24 both FAILED differently (rc=2 file-not-found from a
      `setup-data-pipeline-vm.sh` hardcoded-path bug; a workaround attempt's `run.log` never got created), stopped
      rather than blind-retry a 3rd time. Split out 2026-07-25 (apply_batch_12) from the prior single checked-off todo,
      which incorrectly read as fully done while the actual data mutation had not happened.
- [ ] [SCRIPT] P2. In `dex_swaps_handler.py`, recognize a 200-status GraphQL response whose `errors[]` message matches
      `subgraph not found: no allocations` (or more generally, any non-schema-drift GraphQL-level error that repeats
      across all 5 cascade schemas) as a **distinct, terminal condition** at FETCH TIME — do not raise the generic
      `RuntimeError`; instead raise/return a typed `_SubgraphNotFoundError`-equivalent (or a new
      `_SubgraphDeindexedError`) so the manifest writer calls `record_empty(reason=EXPECTED_SUBGRAPH_DEINDEXED)` going
      forward instead of `record_failed`. **Still OPEN** — the reason now exists (item 1 above), but the writer-side
      detection to USE it at capture time has not shipped; without this, the next backfill VM run against CURVE/OPTIMISM
      will re-create fresh `attempted_failed` rows that item 2's retroactive script would then need to re-run to clean
      up again. Repo: `market-tick-data-service` (out of scope for the 2026-07-24 dispatch that shipped items 1-2 — that
      dispatch was scoped to unified-api-contracts + instruments-service only).
- [x] ✅ [DESIGN] P3. **DONE 2026-07-26 (slot 4) — NO-GO.** Evaluate wiring the existing
      `curve_adapter.py`/`api.curve.fi` REST path into the batch `dex_pool_swaps` collection for CURVE/OPTIMISM
      (mirroring the "ARB/POLY only on hosted service" precedent already noted in UAC `_defi.py`) so this cell can
      actually capture real data instead of staying a permanent honest absence. Not urgent — `dex_pool_swaps` coverage
      for every OTHER venue is unaffected, and 952 rows is a small fraction of the asset_group's total gap. Repo:
      `market-tick-data-service`. Full evidence-cited verdict in "Evaluated (2026-07-26, slot 4)" below — the existing
      REST integration is pool-discovery-only (not swap-history), hardcoded to Ethereum, and the actual swap-fetch path
      is Graph-only with an unimplemented REST fallback stub; no follow-up implementation todo opened.
- [ ] [SCRIPT] P3. Do the same live-subgraph-health spot-check for the remaining un-investigated long-tail buckets
      (`UNISWAP_V3` `TimeoutError`×25, `UNISWAP_V3`/POLYGON schema-drift×24, and the handful of 1-8-row buckets) —
      plausibly genuine transient/schema issues (all 5 sampled subgraphs from this session were healthy), but not
      confirmed row-by-row. Repo: `market-tick-data-service`.

## Verified live (2026-07-15, ~12:57Z)

- `SUBGRAPH_IDS["curve"]["OPTIMISM"]` = `CXDZPduZE6nWuWEkSzWkRoJSSJ6CneSqiDxdnhhURShX` — direct gateway probe returns
  `{"errors":[{"message":"subgraph not found: no allocations"}]}` (HTTP 200).
- 5 comparison subgraphs (BALANCER/POLYGON, UNISWAP_V3/POLYGON, PANCAKESWAP_V3/BSC, UNISWAP_V3/BASE,
  UNISWAP_V3/ETHEREUM) all returned live `_meta.block` data — confirms the dead-subgraph condition is isolated to this
  one (protocol, chain) pair, not a gateway-wide or API-key issue.

## Verified live (2026-07-24) — reclassification script shipped, `--apply` still pending

Direct pandas inspection of prod `_index/availability_index.parquet` (23,932,764 rows,
`market-data-tick-defi-prd- central-element-323112`) today: **144** rows currently match `venue=CURVE`,
`chain=OPTIMISM`, `data_type=dex_pool_swaps`, `capture_status=attempted_failed`, `error_reason` starting with
`"All 5 cascade schemas returned GraphQL errors for curve/OPTIMISM"` — down from the 952 measured 2026-07-15. Not
re-investigated why the count shrank (plausibly consolidator dedup / an intervening backfill VM run re-attempting and
re-failing a subset with a fresh `attempted_at` that then got superseded) — out of scope for this dispatch; the script
is idempotent and safe to re-run whenever, so the exact live count at apply-time is authoritative regardless.

**Bug found + fixed during verification**: the first version of
`scripts/reclassify_defi_curve_optimism_subgraph_deindexed_2026_07_24.py` matched `error_reason` against the FULL
45-character subgraph id (`CXDZPduZE6nWuWEkSzWkRoJSSJ6CneSqiDxdnhhURShX`) and found **0** rows on `--dry-run` — not
because the condition had resolved, but because the manifest's `error_reason` column is **truncated at 80 characters**
on write (confirmed: every real row's stored value ends exactly at `"...(subgraph=CXDZP"`, i.e. only 5 of the 45
subgraph-id characters survive). Fixed to match the untruncated prefix
`"All 5 cascade schemas returned GraphQL errors for curve/OPTIMISM"` instead, then re-confirmed against an independent
raw-pandas count of the same 144 rows. This 80-char truncation is a general manifest-writer characteristic worth knowing
for ANY future `error_reason`-substring-matching script in this workspace, not specific to this issue.

**`--apply` NOT run** — the newly-landed heavy-I/O hard rule (`/codex/05-infrastructure/vm-launcher-runbook.md` § heavy
I/O) classifies this operation ("a manifest-index read-transform-write over the whole `_index`") as heavy I/O that must
run on a VM in-region, never the operator's local machine. Follow-up (mechanical, no design work needed): launch via the
generic `canonical-migration` `VM_TASK`/ `VM_MIGRATION_CMD` dispatch in
`deployment-service/scripts/vm/setup-data-pipeline-vm.sh` (`VM_SERVICE=instruments_service`, command
`python scripts/reclassify_defi_curve_optimism_subgraph_deindexed_2026_07_24.py --apply`), or add a new one-off category
to `launch-canonical-migration-vm.sh`'s dispatch table. Shipped: `unified-api-contracts@e893e5c9` (reason),
`instruments-service@73100d4e` (script).

## Evaluated (2026-07-26, slot 4) — wiring `curve_adapter.py`'s REST path into the batch cascade

**Verdict: NO-GO as currently scoped — the "existing REST path" doesn't do what this todo assumed.** Read
`market_tick_data_service/market_interface/adapters/defi/curve_adapter.py` and
`market_tick_data_service/cli/handlers/dex_swaps_handler.py` directly (not just the module docstrings):

1. **The REST integration is pool-DISCOVERY only, not swap-HISTORY.** `_safe_fetch_curve_rest_pools()` calls
   `CURVE_REST_API_POOLS = f"{_CURVE_REST_BASE}/v1/getPools/all/ethereum"` — this endpoint returns pool metadata
   (address/name/coins), which is what `fetch_markets()` (instrument discovery, consumed by instruments-service) needs.
   It returns nothing resembling a swap/trade record. `dex_pool_swaps` needs per-swap history
   (timestamp/tx_hash/amounts) — this REST endpoint cannot produce that at all, regardless of chain.
2. **The actual swap-history path (`download_market_data` → `_download_swaps`) is NOT REST-based — it's The Graph, the
   SAME failure mode.** `_download_swaps()` calls `_download_swaps_from_decentralized_graph()` (PRIORITY 1, queries
   `THEGRAPH_CURVE_MAINNET` — the decentralized network, exactly what's dead for OPTIMISM) and on failure falls through
   to a literal stub:
   `# PRIORITY 2: Fall back to hosted subgraph ... return []  # Hosted subgraph implementation omitted for brevity`
   (`curve_adapter.py:612-614`). Calling `CurveAdapter.download_market_data()` for CURVE/OPTIMISM today would return
   **zero swap rows** — it would fail the same way the batch cascade already does, just through a different code path.
3. **The discovery path (the only genuinely-REST part) is hardcoded to Ethereum, not chain-parameterized.**
   `CURVE_REST_API_POOLS` hardcodes the literal `/ethereum` URL segment, and `_build_curve_pool_instrument()` hardcodes
   `"venue": "CURVE-ETHEREUM"` / `instrument_key = f"CURVE-ETHEREUM:POOL:{safe_name}"` regardless of `self.chain` — this
   adapter has no working OPTIMISM code path today, discovery or otherwise, despite being instantiable with
   `chain="OPTIMISM"`.
4. **UAC's `EVM_DEFI_REST_URLS["curve"]` registers only a bare `api_url` host** (`https://api.curve.finance`,
   `_defi.py:1303-1307`) — no per-chain path template, no second URL type for a volume/swap-history endpoint. There is
   no existing evidence in this codebase that Curve's public REST API even exposes swap-level history for any chain (its
   adapter usage here is 100% pool-metadata); confirming that would need an external-API check, which is itself a
   prerequisite for any real build, not something "wiring the existing path" can shortcut.
5. **No integration seam exists in `dex_swaps_handler.py` for a non-subgraph source.** `_collect_protocol_chain` →
   `_paginate_swaps` → `_query_and_parse` → `_run_cascade` is subgraph-only end-to-end, gated by
   `subgraph_id = get_subgraph_id(protocol, chain)` at entry (`dex_swaps_handler.py:407-409`). There is no branch point
   today for "if no subgraph, try an adapter fetch instead" — adding one is new architecture, not "wiring."

**What integration point WOULD exist, if pursued for real** (not recommended without the external-API check in point 4):
a new branch in `_collect_protocol_chain` before the `subgraph_id` early-return, calling a genuinely-new `CurveAdapter`
method (the existing `_download_swaps` cannot be reused as-is — its Graph-first priority order would need inverting for
OPTIMISM specifically, and its discovery hardcoding would need chain-parameterizing), then mapping whatever record shape
that new REST call returns onto `_write_swap_shard`'s expected row schema (per-swap timestamp/tokens/amounts — same as
`_curve_swap_to_dict`'s shape).

**Recommendation: do not open a follow-up implementation todo yet.** The right next step, if this is ever prioritized,
is a _separate, smaller_ research todo — confirm whether `api.curve.finance` (or any other Curve public endpoint)
exposes real swap-level history for OPTIMISM at all — before scoping a build. Given the small blast radius already
established (952→144 rows, one (venue, chain) pair, honest `EXPECTED_SUBGRAPH_DEINDEXED` absence already shipping via
the existing follow-up chain), leaving this as a permanent honest absence remains the pragmatic default unless that
external-API check comes back positive.
