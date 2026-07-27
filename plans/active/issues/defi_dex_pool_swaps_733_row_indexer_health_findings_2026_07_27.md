---
doc_type: issue
title: >-
  dex_pool_swaps 733-row attempted_failed investigation: CURVE/OPTIMISM's known-dead subgraph fix finally shipped;
  UNISWAP_V3/OPTIMISM + PANCAKESWAP_V3/BSC are a NEW indexer-health finding; TRADER_JOE_V2/AVALANCHE + 5 smaller pairs
  are live-healthy (retry-fixable, no code bug)
summary: >-
  Investigated mvp_backfill_defi_onchain_v10_2026_06_27.md's `dex_pool_swaps` 733-row attempted_failed todo
  (uniswap_v3/OPTIMISM=316, curve/OPTIMISM=312, trader_joe_v2/AVALANCHE=73, pancakeswap_v3/BSC=13, + smaller counts for
  aerodrome_v3/BASE, uniswap_v4/ETHEREUM, uniswap_v3/POLYGON, pancakeswap_v3/ETHEREUM, velodrome_v2/OPTIMISM) by
  live-probing every named subgraph deployment directly against the TheGraph gateway (not relying on stale manifest
  error strings). Three distinct root causes: (1) CURVE/OPTIMISM is the already-root-caused "no allocations" dead
  subgraph from `defi_curve_optimism_subgraph_no_allocations_2026_07_15.md` — its
  `EmptyConfirmedReason.EXPECTED_SUBGRAPH_DEINDEXED` taxonomy reason shipped 2026-07-24 but the writer-side runtime
  detection in `dex_swaps_handler.py` was never actually shipped (confirmed zero references in the codebase), so every
  backfill attempt since has kept re-creating fresh `attempted_failed` rows — that detection landed concurrently this
  session via slot-11 (`market-tick-data-service@dddd1b21`), verified functionally equivalent to my own independent
  implementation and adopted rather than duplicated. (2) UNISWAP_V3/OPTIMISM and PANCAKESWAP_V3/BSC both return a
  reproducible (3/3, identical indexer addresses) gateway `"bad indexers"` error (`Unavailable(too far behind)` /
  `BadResponse(no attestation: indexing_error)`) — a DIFFERENT condition than "no allocations", NOT covered by the
  existing taxonomy, and NEW since 2026-07-15 (the original curve issue doc live-verified PANCAKESWAP_V3/BSC as healthy
  on that date as one of its 5 comparison subgraphs). (3) TRADER_JOE_V2/AVALANCHE and all 5 smaller-count pairs are
  currently live-healthy — real swap data returned on direct probe — so their historical `attempted_failed` rows are
  retry-fixable, not a code bug.
status: open
nature: record
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [defi, dex_pool_swaps, thegraph, subgraph, honest-absence, indexer-health, mvp-gate]
related:
  [
    plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    plans/active/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
    plans/archive/issues/defi_curve_optimism_subgraph_no_allocations_2026_07_15.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-27
parent_epic: defi_master
source: [data_engineering slot-2, 2026-07-27, dispatched via mvp_backfill_defi_onchain_v10-003]
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
last_updated: 2026-07-27
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
---

## What I found

`mvp_backfill_defi_onchain_v10_2026_06_27.md`'s G2 gate flagged 733 `dex_pool_swaps` `attempted_failed` rows (live
through 2026-07-26), bucketed by error message into "All N cascade schemas returned GraphQL errors" / "All N cascade
schemas drifted" for: uniswap_v3/OPTIMISM (316), curve/OPTIMISM (312), trader_joe_v2/AVALANCHE (73), pancakeswap_v3/BSC
(13), plus smaller counts for aerodrome_v3/BASE, uniswap_v4/ETHEREUM, uniswap_v3/POLYGON, pancakeswap_v3/ETHEREUM,
velodrome_v2/OPTIMISM. Rather than trust the stale bucket label, live-probed every named subgraph ID (from UAC
`registry.capability_declarations._defi.SUBGRAPH_IDS`) directly against
`https://gateway.thegraph.com/api/{key}/subgraphs/id/{id}` this session (2026-07-27):

| protocol/chain                                                                                             | subgraph_id (short) | live probe result                                                                                                                                                                     | verdict                                                                      |
| ---------------------------------------------------------------------------------------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| uniswap_v3/OPTIMISM                                                                                        | `Cghf4Lf...`        | `errors: bad indexers: {...Unavailable(too far behind), ...BadResponse(no attestation: indexing_error), ...Unavailable(no status: indexer not available)}` — reproduced 3/3 identical | indexer-health, NOT schema drift                                             |
| curve/OPTIMISM                                                                                             | `CXDZPdu...`        | `errors: subgraph not found: no allocations` — reproduced 2/2 identical                                                                                                               | zero indexer allocations — permanently dead (already root-caused 2026-07-15) |
| pancakeswap_v3/BSC                                                                                         | `Hv1GncL...`        | `errors: bad indexers: {...BadResponse(no attestation: indexing_error), ...BadResponse(expected value at line 1 column 1)}` — reproduced 3/3 identical                                | indexer-health, NOT schema drift                                             |
| trader_joe_v2/AVALANCHE                                                                                    | `H2VGe2t...`        | schema #1 (`messari`, `account{id}`) drifts (`Type Swap has no field account`, confirmed via introspection); schema #2 (`messari_from`, `from`) returns real swap rows                | **currently healthy** — cascade already succeeds at schema #2                |
| aerodrome_v3/BASE, uniswap_v4/ETHEREUM, uniswap_v3/POLYGON, pancakeswap_v3/ETHEREUM, velodrome_v2/OPTIMISM | (various)           | all returned real `swaps` data on a minimal probe                                                                                                                                     | **currently healthy**                                                        |

### 1. CURVE/OPTIMISM — dead subgraph, fix now actually shipped

This is the exact condition `defi_curve_optimism_subgraph_no_allocations_2026_07_15.md` (archived, status `resolved`)
root-caused: `SUBGRAPH_IDS["curve"]["OPTIMISM"]` has zero indexer allocations on The Graph's decentralized network — a
200-status response carrying `errors: [{"message": "subgraph not found: no allocations"}]`, permanent until a new
indexer picks it up. That doc's item 1 (add `EmptyConfirmedReason.EXPECTED_SUBGRAPH_DEINDEXED`) shipped
`unified-api-contracts@e893e5c9` 2026-07-24. Item 4 — the actual runtime detection in `dex_swaps_handler.py` so a live
backfill attempt records `empty_confirmed(EXPECTED_SUBGRAPH_DEINDEXED)` instead of `attempted_failed` — was marked
"still OPEN... covered by `defi_satellite_ao_dispatch_batch1_2026_07_25.md`" in the archived doc, and that batch1 plan
(still active, todo at lines 276-294) still shows it as an open `- [ ]`. Grepped the current `market-tick-data-service`
tree for `EXPECTED_SUBGRAPH_DEINDEXED` / `_SubgraphDeindexedError` / `"no allocations"`: **zero hits** — the detection
was never actually shipped despite the reason existing since 2026-07-24, which is exactly why my task's 312 fresh
`attempted_failed` rows (dated through 2026-07-26) kept accumulating.

**Independently implemented + shipped CONCURRENTLY by slot-11**, `market-tick-data-service@dddd1b21` ("fix(defi):
classify CURVE/OPTIMISM 'no allocations' as honest empty_confirmed(EXPECTED_SUBGRAPH_DEINDEXED), not attempted_failed")
— landed while I was mid-session on the same file. My own equivalent implementation
(`_is_deindexed_error`/`_SubgraphDeindexedError`/ `record_swap_deindexed`, 6 new tests) hit a real
`git pull --rebase --autostash` conflict against theirs; verified their version is functionally equivalent (same
fingerprint, same terminal short-circuit in `_run_cascade`, same `record_empty(reason=EXPECTED_SUBGRAPH_DEINDEXED)`
routing, equivalent test coverage including the schema-drift/transient-error negative cases) and adopted it rather than
ship a duplicate — no separate SHA from this session for this specific fix. Confirmed green:
`tests/unit/test_dex_swaps_handler.py` (37 tests) + `tests/unit/test_dex_swaps_handler_coverage.py` (54 tests), 84
passed.

### 2. UNISWAP_V3/OPTIMISM + PANCAKESWAP_V3/BSC — NEW finding, "bad indexers" ≠ "no allocations"

Both return a `"bad indexers"` gateway error listing 2-3 specific indexer addresses each as
`Unavailable(too far behind)` / `BadResponse(no attestation: indexing_error)` /
`BadResponse(expected value at line 1 column 1)` — reproduced identically 3/3 tries each (not a transient blip). This is
a DIFFERENT condition from CURVE/OPTIMISM's "no allocations": here the subgraph HAS indexer allocations, but the
specific indexers currently serving it are all unhealthy/behind at the gateway's routing layer — before any query even
reaches real data. Whether this is (a) a temporary indexer-fleet health dip that will self-heal, or (b) the leading edge
of the same de-indexing process CURVE/OPTIMISM already went through, cannot be determined from a same-day probe.

**This is genuinely new information**: the original 2026-07-15 curve issue doc explicitly live-verified
PANCAKESWAP_V3/BSC as one of its 5 "comparison subgraphs... all responded live with fresh `_meta.block` timestamps" —
i.e. PANCAKESWAP_V3/BSC was healthy 12 days ago and is now consistently broken. No existing taxonomy reason or runtime
detection covers "bad indexers" — I did **not** fold this into `EXPECTED_SUBGRAPH_DEINDEXED` (that reason's own
docstring is specific to the "no allocations" fingerprint; misclassifying a possibly-transient indexer-health dip as
"permanent deindexed" would be its own honest-absence violation in the other direction). Left as `attempted_failed`
(accurate — a genuine, currently-unresolved fetch failure) pending the follow-up below.

### 3. TRADER_JOE_V2/AVALANCHE + 5 smaller pairs — currently healthy, retry-fixable

`defi_satellite_ao_dispatch_batch1_2026_07_25.md`'s open combined todo (lines 276-294, sub-item b) describes
TRADER_JOE_V2/AVALANCHE as "confirmed 0% capture 2023-2026, all 5 cascade schemas fail with bad indexers" as of
2026-07-25 and recommends a new query schema variant or a deployment-ID swap. Live-probing the SAME subgraph ID
(`H2VGe2tYavUEosSjomHwxbvCKy3LaNaW8Kjw2KhhHs1K`) today (2026-07-27) shows it has since healed: cascade schema #1
(`messari`, using `account{id}`) still drifts (confirmed via GraphQL introspection — the live `Swap` type has no
`account` field), but schema #2 (`messari_from`, using `from`) — already present in the existing cascade, no code change
needed — returns real, current swap rows (verified 5 real trades with pool names/token symbols/amounts on a live date
window). **That 2026-07-25 fix premise is now stale**: no new query schema or deployment-ID swap is needed for
TRADER_JOE_V2/AVALANCHE; the existing cascade already resolves it. The 5 smaller-count pairs (aerodrome_v3/BASE,
uniswap_v4/ETHEREUM, uniswap_v3/POLYGON, pancakeswap_v3/ETHEREUM, velodrome_v2/OPTIMISM) are also all currently healthy
on a minimal probe. For all 6 of these pairs, the historical `attempted_failed` residue is retry-fixable (mirrors this
same plan's PYTH `oracle_prices` category-1 finding) — a fresh backfill run should convert them to `captured`, no code
change required.

## Why it matters

- CURVE/OPTIMISM's 312 rows (and every future day this subgraph stays dead) will keep re-appearing as fresh
  `attempted_failed` on every backfill re-run until the shipped fix reaches production — this was flagged as the exact
  failure mode in the 2026-07-15 doc ("without this, the next backfill VM run against CURVE/OPTIMISM will re-create
  fresh attempted_failed rows") and is precisely what happened: 12 days later, 312 fresh rows.
- The UNISWAP_V3/OPTIMISM + PANCAKESWAP_V3/BSC "bad indexers" finding (329 rows combined) is new and currently uncovered
  by any taxonomy reason — worth tracking distinctly rather than silently lumping into the deindexed bucket, so a future
  re-probe can tell whether it self-heals or hardens into a second "no allocations" case.
- `defi_satellite_ao_dispatch_batch1_2026_07_25.md`'s open combined todo (lines 276-294) bundles a now-partially-stale
  premise (TRADER_JOE_V2 needing a schema/deployment fix) with the still-valid CURVE/OPTIMISM detection ask (now
  shipped) — flagging here so nobody re-does the shipped half or chases a TRADER_JOE_V2 code fix that live evidence
  shows isn't needed.

## Recommended decision

- [x] [SCRIPT] P1. Ship the CURVE/OPTIMISM (and any future "no allocations" subgraph) `EXPECTED_SUBGRAPH_DEINDEXED`
      runtime detection in `dex_swaps_handler.py` — **DONE 2026-07-27, shipped concurrently by slot-11**,
      `market-tick-data-service@dddd1b21`. Repo: market-tick-data-service.
- [ ] [DATA] P2. Investigate whether UNISWAP_V3/OPTIMISM + PANCAKESWAP_V3/BSC's "bad indexers" gateway errors are a
      transient indexer-fleet health dip or a permanent de-indexing event — re-probe both subgraph IDs on a later date
      (a same-day probe cannot distinguish transient from structural); if still broken after a multi-day window,
      research replacement subgraph deployment IDs via The Graph Explorer/Network Subgraph, or add a taxonomy reason +
      runtime detection for this distinct "bad indexers" condition (mirroring `EXPECTED_SUBGRAPH_DEINDEXED` but NOT
      reusing it — the semantics differ). Repo: market-tick-data-service, unified-api-contracts.
- [x] ✅ [SCRIPT] P2. **PARTIALLY DONE 2026-07-27 (slot-11), independently converged on the same finding.**
      TRADER_JOE_V2/AVALANCHE + VELODROME_V2/OPTIMISM: SPOT backfill VM `mtds-dex-swaps-historical`
      (`--protocols trader_joe_v2,velodrome_v2 --start 2023-01-01 --end 2024-10-06`) launched, T+10min health-verified
      RUNNING (`defi_satellite_ao_dispatch_batch1_2026_07_25.md` lines 276-294). **Still open**: the remaining 3
      smaller-count pairs (aerodrome_v3/BASE, uniswap_v4/ETHEREUM, uniswap_v3/POLYGON, pancakeswap_v3/ETHEREUM) — no
      backfill launched for these yet, no code change needed, all verified live-healthy this session. Repo:
      deployment-service.
- [x] ✅ [PM] P3. **DONE 2026-07-27 — moot.** `defi_satellite_ao_dispatch_batch1_2026_07_25.md`'s combined todo (lines
      276-294) was independently flipped `[x]` by slot-11 in the same window, citing this doc directly ("folded as
      corroborating evidence into the existing 2026-07-27 (slot-2) scope-extension todo in the source issue doc") — no
      annotation needed, already cross-referenced both ways. Repo: unified-trading-pm.

## Verified live (2026-07-27)

Full probe transcript (subgraph IDs, exact curl commands, and raw responses) is in this session's `/done` evidence;
summarized in the table above. Key raw responses:

- uniswap_v3/OPTIMISM:
  `{"errors":[{"message":"bad indexers: {0xeccdf8231326a9c5aad32df76a633aaa4c49b104: Unavailable(too far behind), 0xf92f430dd8567b0d466358c79594ab58d919a6d4: BadResponse(no attestation: indexing_error), 0xfeff9093f6b32d0e5cddba743b06a1fedb87c004: Unavailable(no status: indexer not available)}"}]}`
  (3/3 identical retries).
- curve/OPTIMISM: `{"errors":[{"message":"subgraph not found: no allocations"}]}` (2/2 identical retries).
- pancakeswap_v3/BSC:
  `{"errors":[{"message":"bad indexers: {0x1b7e0068ca1d7929c8c56408d766e1510e54d98d: BadResponse(no attestation: indexing_error), 0xf92f430dd8567b0d466358c79594ab58d919a6d4: BadResponse(expected value at line 1 column 1)}"}]}`
  (3/3 identical retries).
- trader_joe_v2/AVALANCHE: `messari` schema → `{"errors":[{"message":"Type \`Swap\` has no field
  \`account\`"}]}`; `messari_from` schema → real swap data (5 rows, pool names/tokens/amounts populated).
- aerodrome_v3/BASE, uniswap_v4/ETHEREUM, uniswap_v3/POLYGON, pancakeswap_v3/ETHEREUM, velodrome_v2/OPTIMISM: minimal
  `{ swaps(first: 1) { id timestamp } }` probe returned real data for all 5.
