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
    plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
    plans/archive/issues/defi_curve_optimism_subgraph_no_allocations_2026_07_15.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-27
parent_epic: defi_master
source: [data_engineering slot-2, 2026-07-27, dispatched via mvp_backfill_defi_onchain_v10-003]
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
last_updated: 2026-08-03
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
context_scope:
  [
    /plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/archive/issues/defi_curve_optimism_subgraph_no_allocations_2026_07_15.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/dex_swaps_handler.py,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
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
      reusing it — the semantics differ). Repo: market-tick-data-service, unified-api-contracts. **STILL OPEN — partial
      same-day re-probe evidence added 2026-07-27 (slot-5, ~2h later): PANCAKESWAP_V3/BSC self-healed (transient),
      UNISWAP_V3/OPTIMISM did NOT (identical 3 indexer addresses/errors both times) — see "Verified live (re-probe...)"
      below. Still same-day data; the multi-day re-check this todo asks for has not happened yet — do not close on this
      evidence alone.**
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
- [ ] [DATA] P3. **NEW finding, 2026-07-27 (slot-5 re-probe, see "Verified live (re-probe...)" below).**
      UNISWAP_V4/ETHEREUM carries 7 `dex_pool_swaps` `attempted_failed` rows whose `error_reason` starts with
      `build_instrument_id` — NOT a subgraph-query failure (the subgraph itself live-probed HEALTHY, fresh block, no
      indexing errors). This looks like a generic instrument-id-construction error (likely from a shared UAC
      `build_instrument_id()`-style helper, not `dex_swaps_handler.py`'s own cascade code — grep for
      `build_instrument_id` inside `dex_swaps_handler.py` returns zero hits) being surfaced as the row's error_reason.
      Root-cause not yet dug into — get the untruncated `error_reason` for these 7 rows from
      `_index/availability_index.parquet` (venue=UNISWAP_V4, chain=ETHEREUM, data_type=dex_pool_swaps,
      capture_status=attempted_failed, error_reason LIKE 'build_instrument_id%'), trace the actual raise site, and fix
      or reclassify. Small blast radius (7 rows). Repo: market-tick-data-service.

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

## Verified live (2026-07-28, DP-FETCH-009 escalation — VELODROME_V2/OPTIMISM newly joins the "bad indexers" bucket)

Dispatched as a `data_pipeline_failure` escalation worker off a fresh `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009) CRITICAL
page: `asset_group=defi data_type=dex_pool_swaps: 1087 attempted_failed cells of 3039478 attempted` (abs>=500
threshold), flagged "fresh — newest attempted_failed activity 0d ago". Re-read the live prod manifest
(`market-data-tick-defi-prd-central-element-323112`, `_index/availability_index.parquet`, 27,699,487 total rows) to get
the current per-(venue,chain,error_reason) breakdown rather than trust the alert's aggregate count alone:

| venue          | chain     | error_reason (90-char truncated)                                                 | count | min attempted_at     | max attempted_at     |
| -------------- | --------- | -------------------------------------------------------------------------------- | ----- | -------------------- | -------------------- |
| VELODROME_V2   | OPTIMISM  | All 5 cascade schemas drifted for velodrome_v2/OPTIMISM (subgraph=A4Y1A82YhSLTn9 | 662   | 2026-07-27T18:51:13Z | 2026-07-28T09:16:44Z |
| UNISWAP_V3     | OPTIMISM  | All 8 cascade schemas drifted for uniswap_v3/OPTIMISM (subgraph=Cghf4LfVqPiFw6fp | 356   | 2026-07-22T17:53:33Z | 2026-07-28T09:24:30Z |
| TRADER_JOE_V2  | AVALANCHE | All 5 cascade schemas returned GraphQL errors for trader_joe_v2/AVALANCHE        | 28    | 2026-07-23T07:56:40Z | 2026-07-23T19:36:07Z |
| PANCAKESWAP_V3 | BSC       | All 8 cascade schemas drifted for pancakeswap_v3/BSC                             | 15    | 2026-07-23T07:55:39Z | 2026-07-27T11:40:13Z |
| UNISWAP_V4     | ETHEREUM  | build_instrument_id / All 1 cascade schemas returned GraphQL errors              | 12    | 2026-07-22T20:52:46Z | 2026-07-27T05:32:25Z |
| UNISWAP_V2     | ETHEREUM  | All 1 cascade schemas returned GraphQL errors for uniswap_v2/ETHEREUM            | 5     | 2026-07-22T16:46:07Z | 2026-07-22T17:06:48Z |
| CURVE          | OPTIMISM  | All 5 cascade schemas returned GraphQL errors for curve/OPTIMISM (OLD signature) | 4     | 2026-07-28T07:16:58Z | 2026-07-28T09:16:17Z |
| PANCAKESWAP_V3 | ETHEREUM  | All 8 cascade schemas drifted for pancakeswap_v3/ETHEREUM                        | 2     | 2026-07-24T17:20:32Z | 2026-07-27T16:06:50Z |
| UNISWAP_V3     | POLYGON   | All 8 cascade schemas returned GraphQL errors for uniswap_v3/POLYGON             | 2     | 2026-07-24T17:20:31Z | 2026-07-25T13:29:00Z |
| AERODROME_V3   | BASE      | All 8 cascade schemas drifted for aerodrome_v3/BASE                              | 1     | 2026-07-24T23:21:21Z | 2026-07-24T23:21:21Z |

**Total 1087, matching the alert exactly.** 409 of the 1087 rows carry `attempted_at` on 2026-07-28 itself: 393
VELODROME_V2/OPTIMISM, 12 UNISWAP_V3/OPTIMISM, 4 CURVE/OPTIMISM — i.e. the alert's "fresh, 0d ago" signal is almost
entirely VELODROME_V2/OPTIMISM's brand-new regression, not the already-tracked long-tail residue below it.

**VELODROME_V2/OPTIMISM is a NEW finding — not the same as its historical 118-row entry this doc's first pass already
investigated.** That earlier probe (2026-07-27, this doc's first table) live-verified it HEALTHY via a minimal
`{ swaps(first:1) { id timestamp } }` probe (`hasIndexingErrors=false`). The 662 fresh rows here (all dated
2026-07-27T18:51Z onward — i.e. appearing a few hours AFTER that healthy verdict) are the actual PRODUCTION cascade
query failing, which a minimal probe never exercises. Live-diagnosed today with the real production client
(`market_tick_data_service.market_interface.clients.thegraph_base_client.async_post_to_subgraph`, subgraph
`A4Y1A82YhSLTn998BVVELC8eWzhi992k4ZitByvssxqA`):

- **Introspected the live `Swap` type** — confirms the correct field shape is `from` (String, not `account{id}`) +
  `pool` (not `liquidityPool`) — i.e. `messari_from`, cascade position 2 of 5 for this protocol (non-univ3 Messari
  family: messari → messari_from → messari_lp → messari_lp_from → sushi_custom).
- **`messari` (position 1)**: `Type \`Swap\` has no field \`account\`` — genuine schema-shape mismatch, correctly falls
  through (not the bug).
- **`messari_from` (position 2, the STRUCTURALLY CORRECT query)**: reproduced 3/3 identical across 3 different API keys
  from the round-robin pool —
  `bad indexers: {0x8cc22436ba6f07a4d5dd2043e3109267eee5aab8: Unavailable(no status: failed to get indexing progress), 0xf92f430dd8567b0d466358c79594ab58d919a6d4: BadResponse(expected value at line 1 column 1)}`.
  This is NOT a schema bug — the correct query is already in the cascade at position 2; it fails at the gateway's
  indexer-selection layer before ever reaching real data.
- **`messari_lp`/`messari_lp_from` (positions 3-4)**: `has no field liquidityPool` / `has no field account` — the
  post-2024-upgrade schema variant genuinely doesn't apply here, correctly falls through.
- Net effect: the cascade exhausts all 5 (1 genuine drift, 1 bad-indexers on the otherwise-correct query, 2 more genuine
  drift, presumably sushi_custom too) and raises "All 5 cascade schemas drifted" — collapsing a bad-indexers condition
  into the SAME error bucket as genuine schema drift, same ambiguity this doc's item 2 already flagged for
  UNISWAP_V3/OPTIMISM.

**This directly corroborates item 2's "still open" question in the other direction**: indexer
`0xf92f430dd8567b0d466358c79594ab58d919a6d4` appears in BOTH the UNISWAP_V3/OPTIMISM bad-indexers signature (this doc's
original table, reproduced 3/3 same-day AND again several hours later) AND now VELODROME_V2/OPTIMISM's — the **same
indexer node serving (at least) two independent Optimism-chain subgraphs is unhealthy simultaneously**. That is stronger
evidence toward "a real indexer-fleet health problem on Optimism-chain subgraphs specifically" than either
single-subgraph observation alone, though still not proof of "permanent" (the existing todo's multi-day bar still
applies — this is one more same-week data point, not a multi-day recheck).

**No code fix applies here**: the correct query schema (`messari_from`) is already in the cascade at the correct
position; there is no missing schema variant to add and no bug to ship. Re-ordering the cascade wouldn't help either — a
structurally-valid query still has to reach a real indexer to execute, and gateway-level "bad indexers" routing is
independent of which valid query hits it. This is a genuine `BLOCKED-UPSTREAM-OUTAGE` (external Graph Protocol indexer
health), not an `attempted_failed`-vs-`empty_confirmed` misclassification and not a canonical-path/bucket-env/cron bug —
none of the `data_pipeline_failure` agent's fixable DP-FETCH-009 root-cause classes apply. Marking VELODROME_V2/OPTIMISM
`known_dead` would be a HONEST-ABSENCE VIOLATION in the wrong direction — it captured 14,272-16,195 real rows per run as
recently as 2026-07-23 and is expected to resume once the indexer heals (mirrors PANCAKESWAP_V3/BSC's confirmed same-day
self-heal in this doc's first pass) — the alert is correctly surfacing a real, current capture gap, not a false
positive.

- [ ] [DATA] P2. **Extends the existing P2 todo above (still open).** Re-probe UNISWAP_V3/OPTIMISM AND
      VELODROME_V2/OPTIMISM (subgraph `A4Y1A82YhSLTn998BVVELC8eWzhi992k4ZitByvssxqA`, correct query = `messari_from`) on
      a later date — if `0xf92f430dd8567b0d466358c79594ab58d919a6d4` is still serving both and still unhealthy after a
      multi-day window, this crosses from "transient dip" into "file an upstream/Graph-Protocol-side report and consider
      whether our indexer-preference/allowlist options (if any exist at the gateway API level) can steer routing away
      from it" — out of scope to research further in this one-shot escalation. Repo: market-tick-data-service.
- [ ] [DATA] P3. **Now 122 rows (was 4, 2026-07-28; confirmed still live 2026-08-01, see "Verified live (2026-08-01"
      below) — growth rate ~24/day/VM, still well under the 500-row materiality floor.** CURVE/OPTIMISM is STILL
      generating fresh `attempted_failed` rows with the pre-fix error signature, a full week after the
      `EXPECTED_SUBGRAPH_DEINDEXED` runtime-detection fix (`market-tick-data-service@dddd1b21`) landed on
      live-defi-rollout. `mtds-dex-swaps-backfill-1`/`mtds-dex-swaps-backfill-2` (GCP, `asia-northeast1-c`) have been
      RUNNING continuously since 2026-07-23T07:03Z per `TARBALL_PINS.json` (floating
      `MTDS_TARBALL_SHA`/`UTL_TARBALL_SHA`, baked at VM launch — VMs don't live-reload) — i.e. before the fix shipped,
      so they are still writing pre-fix rows; directly confirmed live in `run.log` 2026-08-01 (still logging the exact
      old error string). **BLOCKING PRECONDITION found 2026-08-01, do not skip**: neither VM has a `PROGRESS.json`
      checkpoint (`gs://deployment-scripts-{project}/     vm-logs/<vm>/` has only `run.log` + `TARBALL_PINS.json`) and
      `dex_swaps_handler.py`'s per-`target_day` cycle pattern (sharply varying record counts every ~45-90min cycle)
      indicates these VMs are still walking the launcher's default `START_DATE=2023-01-01` historical range day-by-day,
      9+ days in — a naive delete+relaunch replays from 2023-01-01 and discards that progress (no checkpoint to resume
      from). Before restarting: either (a) add a monotonic `record_vm_progress`/`PROGRESS.json` checkpoint to this
      launcher/handler so a relaunch can resume from the last-completed date (mirrors the SPOT-preemption +
      stall-relaunch contract other launchers already have), or (b) determine the current date-frontier from the per-VM
      manifest shard (`_index/per_vm/mtds-dex-swaps-backfill-{1,2}.parquet`, most-recent `date` column value) and pass
      it explicitly as `--start` on the relaunch. Repo: deployment-service (VM restart + checkpoint wiring),
      market-tick-data-service (schema-detection fix already shipped).

Source: `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009) CRITICAL page, `data_pipeline_failure` escalation `agt-38b3d6`, slot 7,
2026-07-28.

## Verified live (re-probe, 2026-07-27, ~2h later — slot-5)

Dispatched as `defi_satellite_ao_dispatch_batch1-014` ("spot-check live subgraph health for the remaining
un-investigated `dex_pool_swaps` long-tail", source
`plans/archive/issues/defi_curve_optimism_subgraph_no_allocations_2026_07_15.md`). That todo predates this doc — by the
time this session started, the comprehensive same-day investigation above (slot-2) already covered every named subgraph.
Rather than fork a duplicate issue doc, re-ran the live-probe against the same subgraph IDs a few hours later (23:2x
UTC) using the exact production path
(`market_tick_data_service.market_interface.clients.thegraph_base_client.async_post_to_subgraph`, i.e. aiohttp +
`https://gateway.thegraph.com/api/{key}/subgraphs/id/{id}` — a bare `urllib` probe from this host gets Cloudflare error
1010, client-fingerprint-blocked; the aiohttp path production actually uses does not).

**Current row counts** (fresh read of prod `_index/availability_index.parquet`, 26,819,985 total rows,
`market-data-tick-defi-prd-central-element-323112`), `dex_pool_swaps` `attempted_failed` = 866 total, grouped by (venue,
chain, error_reason):

| venue          | chain     | error_reason (80-char truncated)                                                 | count | date range             | max attempted_at (UTC) |
| -------------- | --------- | -------------------------------------------------------------------------------- | ----- | ---------------------- | ---------------------- |
| UNISWAP_V3     | OPTIMISM  | All 8 cascade schemas drifted for uniswap_v3/OPTIMISM (subgraph=Cghf4LfVqPiFw6fp | 344   | 2023-01-01..2026-07-26 | 2026-07-27T22:55:33Z   |
| CURVE          | OPTIMISM  | All 5 cascade schemas returned GraphQL errors for curve/OPTIMISM (subgraph=CXDZP | 339   | 2023-01-01..2026-07-25 | 2026-07-27T22:31:01Z   |
| VELODROME_V2   | OPTIMISM  | All 5 cascade schemas drifted for velodrome_v2/OPTIMISM (subgraph=A4Y1A82YhSLTn9 | 118   | 2023-01-01..2025-06-10 | 2026-07-27T23:07:36Z   |
| TRADER_JOE_V2  | AVALANCHE | All 5 cascade schemas returned GraphQL errors for trader_joe_v2/AVALANCHE (subgr | 28    | 2024-10-07..2026-01-01 | 2026-07-23T19:36:07Z   |
| PANCAKESWAP_V3 | BSC       | All 8 cascade schemas drifted for pancakeswap_v3/BSC (subgraph=Hv1GncLY5docZoGtX | 15    | 2024-10-12..2025-06-09 | 2026-07-27T11:40:13Z   |
| UNISWAP_V4     | ETHEREUM  | build_instrument_id                                                              | 7     | 2026-02-15..2026-04-20 | 2026-07-26T15:27:17Z   |
| UNISWAP_V4     | ETHEREUM  | All 1 cascade schemas returned GraphQL errors for uniswap_v4/ETHEREUM (subgraph= | 5     | 2023-01-31..2026-04-28 | 2026-07-27T05:32:25Z   |
| UNISWAP_V2     | ETHEREUM  | All 1 cascade schemas returned GraphQL errors for uniswap_v2/ETHEREUM (subgraph= | 5     | 2023-01-06..2023-01-10 | 2026-07-22T17:06:48Z   |
| PANCAKESWAP_V3 | ETHEREUM  | All 8 cascade schemas drifted for pancakeswap_v3/ETHEREUM (subgraph=CJYGNhb7Rvnh | 2     | 2025-05-21..2025-06-09 | 2026-07-27T16:06:50Z   |
| UNISWAP_V3     | POLYGON   | All 8 cascade schemas returned GraphQL errors for uniswap_v3/POLYGON (subgraph=3 | 2     | 2024-11-05..2024-11-19 | 2026-07-25T13:29:00Z   |
| AERODROME_V3   | BASE      | All 8 cascade schemas drifted for aerodrome_v3/BASE (subgraph=GENunSHWLBXm59mBSg | 1     | 2026-02-09..2026-02-09 | 2026-07-24T23:21:21Z   |

**Live-probe verdicts** (`{ _meta { block { number timestamp } hasIndexingErrors } }` against each subgraph ID):

| venue/chain             | subgraph (short) | verdict this probe                                                                                                                                                                                                                                                                          |
| ----------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| UNISWAP_V3/OPTIMISM     | `Cghf4Lf...`     | **STILL "bad indexers"** — `{0xeccdf823...: Unavailable(too far behind), 0xf92f430d...: BadResponse(no attestation: indexing_error), 0xfeff9093...: Unavailable(no status: indexer not available)}` — **identical 3 addresses/errors** to the original probe several hours earlier          |
| VELODROME_V2/OPTIMISM   | `A4Y1A82Y...`    | HEALTHY — `block.timestamp=1785194945 block.number=154798084 hasIndexingErrors=false`                                                                                                                                                                                                       |
| PANCAKESWAP_V3/BSC      | `Hv1GncLY...`    | **SELF-HEALED** (was "bad indexers" earlier same day) — HEALTHY now, `block.timestamp=1777378878 block.number=95169690`, but `hasIndexingErrors=true` (gateway routing recovered; the subgraph itself still self-reports indexing errors — worth another look if this bucket keeps failing) |
| UNISWAP_V4/ETHEREUM     | `DiYPVdyg...`    | HEALTHY — `block.timestamp=1785194927`. Confirms the 7 `build_instrument_id` rows are NOT a subgraph-health issue (see new todo above).                                                                                                                                                     |
| UNISWAP_V2/ETHEREUM     | `A3Np3RQb...`    | HEALTHY — `block.timestamp=1785194939`                                                                                                                                                                                                                                                      |
| PANCAKESWAP_V3/ETHEREUM | `CJYGNhb7...`    | HEALTHY — `block.timestamp=1785194939`                                                                                                                                                                                                                                                      |
| UNISWAP_V3/POLYGON      | `3hCPRGf4...`    | HEALTHY — `block.timestamp=1785194946`                                                                                                                                                                                                                                                      |
| AERODROME_V3/BASE       | `GENunSHW...`    | HEALTHY — `block.timestamp=1785194945`                                                                                                                                                                                                                                                      |

**Takeaways**:

1. **PANCAKESWAP_V3/BSC's "bad indexers" condition is confirmed transient** — same subgraph, same day, healed within a
   few hours. This directly answers half of the open P2 todo above (it does NOT need a taxonomy reason / runtime
   detection / replacement deployment ID — a plain retry resolves it).
2. **UNISWAP_V3/OPTIMISM's condition reproduced IDENTICALLY** (same 3 indexer addresses, same error kinds) several hours
   apart — stronger evidence it is NOT a random blip like PANCAKESWAP_V3/BSC's, but still same-day so this alone does
   not prove "permanent" (the todo's own bar is a multi-day re-check). Left the P2 todo OPEN.
3. **CURVE/OPTIMISM is still generating fresh `attempted_failed` rows with the OLD pre-fix error signature as of
   2026-07-27T22:31Z** — ~30min before the CURVE/OPTIMISM `EXPECTED_SUBGRAPH_DEINDEXED` runtime-detection fix
   (`market-tick-data-service@dddd1b21`, this doc's item 1, marked DONE) would have suppressed it. Most likely
   explanation: a currently-running backfill VM was launched on the pre-fix code and hasn't picked up the new deploy
   (VMs don't live-reload) — an operational note, not a new root cause; out of scope to chase down further in this
   read-only todo. Flagging here so whoever next touches CURVE/OPTIMISM row counts isn't surprised the count didn't drop
   to zero immediately after the fix shipped.
4. **NEW finding**: UNISWAP_V4/ETHEREUM's 7 `build_instrument_id`-prefixed `attempted_failed` rows are a distinct,
   not-yet-root-caused bug unrelated to subgraph health (the subgraph itself is healthy) — new todo added above.

Source task: `defi_satellite_ao_dispatch_batch1_2026_07_25.md` ("Spot-check live subgraph health for the remaining
un-investigated `dex_pool_swaps` long-tail").

## Verified live (2026-07-28, DP-FETCH-009 escalation #2 — agt-077924, slot 3)

Dispatched as another fresh `data_pipeline_failure` escalation off a `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009) CRITICAL page
firing on the same ~30min re-nag cooldown as the section above (`agt-38b3d6`, slot 7):
`asset_group=defi data_type=dex_pool_swaps: 1097 attempted_failed cells of 3306806 attempted`. Re-read the live prod
manifest (`market-data-tick-defi-prd-central-element-323112`, `_index/availability_index.parquet`, 28,166,318 total
rows, 4,627,955 `dex_pool_swaps` rows) and diffed the per-cell counts against the section immediately above:

| venue/chain                                                | count now | count ~section above | delta | verdict                                               |
| ---------------------------------------------------------- | --------- | -------------------- | ----- | ----------------------------------------------------- |
| VELODROME_V2/OPTIMISM (drifted/bad-indexers)               | 665       | 662                  | +3    | still actively failing (already tracked)              |
| UNISWAP_V3/OPTIMISM (drifted/bad-indexers)                 | 360       | 356                  | +4    | still actively failing (already tracked)              |
| CURVE/OPTIMISM (OLD pre-fix GraphQL-errors signature)      | 7         | 4                    | +3    | pre-fix VMs still running (already tracked, P3 above) |
| TRADER_JOE_V2/AVALANCHE                                    | 28        | 28                   | 0     | frozen — confirms "currently healthy" verdict holds   |
| PANCAKESWAP_V3/BSC                                         | 15        | 15                   | 0     | frozen — confirms "self-healed" verdict holds         |
| UNISWAP_V4/ETHEREUM (build_instrument_id + GraphQL-errors) | 12        | 12                   | 0     | frozen — separate open P3 todo above, unaffected      |
| UNISWAP_V2/ETHEREUM                                        | 5         | 5                    | 0     | frozen                                                |
| PANCAKESWAP_V3/ETHEREUM                                    | 2         | 2                    | 0     | frozen                                                |
| UNISWAP_V3/POLYGON                                         | 2         | 2                    | 0     | frozen                                                |
| AERODROME_V3/BASE                                          | 1         | 1                    | 0     | frozen                                                |

**Total 1097, matching this escalation's alert exactly.** Every bucket the section above verdicted "currently healthy"
or "separate tracked bug" is byte-identical (zero new rows since that check) — strong corroboration those verdicts still
hold. Only the three already-tracked active-failure cells grew, each by a small amount consistent with an ongoing
backfill continuing to retry a still-broken condition. **No new root cause, no new venue/chain pair.**

Independently live-reproduced both dominant conditions with a freshly-fetched `thegraph-api-key` (not relying on
manifest error strings alone) — same production query shapes and gateway URL the real handler uses
(`https://gateway.thegraph.com/api/{key}/subgraphs/id/{id}`):

- uniswap_v3/OPTIMISM (`univ3` schema — the structurally-correct query, cascade position 1):
  `{"errors":[{"message":"bad indexers: {0xeccdf8231326a9c5aad32df76a633aaa4c49b104: Unavailable(too far behind), 0xf92f430dd8567b0d466358c79594ab58d919a6d4: BadResponse(no attestation: indexing_error), 0xfeff9093f6b32d0e5cddba743b06a1fedb87c004: Unavailable(no status: indexer not available)}"}]}`
  — **the identical 3 indexer addresses + identical error kinds** as both 2026-07-27 probes below.
- velodrome_v2/OPTIMISM (`messari_from` schema — the structurally-correct query per this doc's introspection above):
  `{"errors":[{"message":"bad indexers: {0x8cc22436ba6f07a4d5dd2043e3109267eee5aab8: Unavailable(no status: failed to get indexing progress), 0xf92f430dd8567b0d466358c79594ab58d919a6d4: BadResponse(expected value at line 1 column 1)}"}]}`
  — identical to the section above's same-day-earlier probe.

`0xf92f430dd8567b0d466358c79594ab58d919a6d4` is now confirmed unhealthy across **four independent probes spanning
2026-07-27 through 2026-07-28** (>24h), on **two different Optimism-chain subgraphs**. This is the strongest
same-fingerprint persistence evidence gathered so far. Whether it now satisfies the open P2 todo's "multi-day window"
bar for escalating to an upstream Graph-Protocol report / indexer-allowlist research is a judgment call for whoever next
picks up that todo — flagging the stronger evidence here rather than deciding it myself (that follow-up research is
explicitly out of scope for a one-shot escalation, same conclusion the section above already reached).

**No code fix applies, same as every prior pass**: the correct query schema is already in the cascade at the correct
position for both protocols; this is a live, ongoing `BLOCKED-UPSTREAM-OUTAGE` (Graph Protocol indexer health), not a
`data_pipeline_failure`-agent-fixable root-cause class (not a misclassification, not a canonical-path/env/cron/key-pool
bug). Marking either cell `known_dead` would still be the wrong direction per this doc's reasoning above (both have
captured real rows within the last week and are expected to resume once the indexer heals).

No existing todo above is resolved or newly stale by this pass — all three (P2 re-probe/multi-day, P3 CURVE/OPTIMISM VM
restart, P3 UNISWAP_V4 `build_instrument_id`) remain open exactly as scoped.

Source: `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009) CRITICAL page, `data_pipeline_failure` escalation `agt-077924`, slot 3,
2026-07-28.

## Verified live (2026-07-28, DP-FETCH-009 escalation #3 — agt-0afc1b, slot 3) — corroborates, no new finding

Another `data_pipeline_failure` dispatch off the same cooldown-gated `DP_RUN_MOSTLY_EMPTY` page
(`asset_group=defi data_type=dex_pool_swaps: 1099 attempted_failed cells of 3410476 attempted`). Independently
re-derived the full per-(venue,chain) breakdown from a fresh `availability_index.parquet` pull (28,264,019 total rows)
BEFORE reading this doc's two prior 2026-07-28 sections, then cross-checked against them: VELODROME_V2/OPTIMISM=666,
UNISWAP_V3/OPTIMISM=360, TRADER_JOE_V2/AVALANCHE=28, PANCAKESWAP_V3/BSC=15, CURVE/OPTIMISM=8, UNISWAP_V4/ETHEREUM=12 (7
`build_instrument_id` + 5 GraphQL-errors), UNISWAP_V2/ETHEREUM=5, PANCAKESWAP_V3/ETHEREUM=2, UNISWAP_V3/POLYGON=2,
AERODROME_V3/BASE=1 — total 1099, matching this escalation's alert exactly and consistent with the small ongoing-retry
growth the section above already characterized (+2 VELODROME_V2, CURVE unchanged at this snapshot).

Independently reproduced the two dominant conditions via GraphQL schema introspection + 5 fresh probes against the live
production client (not reusing the manifest's cached error text): VELODROME_V2/OPTIMISM's `Swap` type currently exposes
`from`/`pool` (not `account`/`liquidityPool`/`pair`) — confirming `messari_from` (cascade position 2 of 5) is the
structurally-correct schema — yet all 5/5 fresh attempts against it return the identical `bad indexers` fingerprint
(`0x8cc22436...`, `0xf92f430d...`) already documented above; CURVE/OPTIMISM's subgraph still returns
`"subgraph not found: no allocations"` on all 5 schema attempts, which the current codebase's
`_is_subgraph_deindexed_error`/`dex_swaps_handler.py` correctly detects (confirmed by direct code read — the `dddd1b21`
fix is present and correct), so the 8 residual rows are exclusively the already-flagged stale-VM artifact.

**Independently reached the identical verdict as both prior 2026-07-28 sections**: no code fix applies (the correct
query schema is already in the cascade; the block is an external Graph Protocol indexer-health condition, not a
`data_pipeline_failure`-agent-fixable class), and both existing open todos (P2 re-probe/multi-day, P3 CURVE/OPTIMISM VM
restart) remain correctly scoped as-is — not editing them further to avoid duplicate-todo churn across three
back-to-back escalation dispatches of the same cooldown-gated alert. **Process note for whoever owns
`DP_RUN_MOSTLY_EMPTY`'s dedup config**: this is the third `data_pipeline_failure` worker dispatched against the exact
same static, already-fully-diagnosed, non-code-fixable condition within roughly the alert's own 1800s cooldown window
(`agt-38b3d6`→`agt-077924`→`agt-0afc1b`, all `dex_pool_swaps`/defi) — mirrors the alerting-hygiene question already
raised and left `[OPERATOR]`-gated for cefi's `DP_RUN_MOSTLY_EMPTY` cluster
(`plans/active/issues/cefi_high_attempted_failed_batch_cluster_2026_07_23.md`); not re-opening that policy question here
(same operator-gated scope), just noting the pattern is now reproducing across asset_groups.

Source: `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009) CRITICAL page, `data_pipeline_failure` escalation `agt-0afc1b`, slot 3,
2026-07-28.

## Verified live (2026-08-01, DP-FETCH-009 escalation — agt-35d769, slot 8) — same condition, plus a new checkpoint-safety finding on the P3 VM-restart todo

Dispatched off a `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009) page framed differently this time — "STATIC BACKLOG: only 89
attempted_failed row(s) in the last 1d (below the 500-row materiality floor); a decaying trickle on already-tracked
backlog, not a fresh regression" — i.e. the monitor itself now distinguishes this from a fresh spike. Re-read the live
prod manifest (bounded `read_availability_index(..., columns=[...], filters=[...])` slim-path read, not a full-index
load): `dex_pool_swaps` `attempted_failed` = 1407 total. Breakdown matches every prior pass — VELODROME_V2/OPTIMISM=700,
UNISWAP_V3/OPTIMISM=477, CURVE/OPTIMISM=122, TRADER_JOE_V2/AVALANCHE=28 (frozen), PANCAKESWAP_V3/BSC=17+13
(`build_instrument_id`), UNISWAP_V4/ETHEREUM=17+8, UNISWAP_V2/ETHEREUM=5+1, PANCAKESWAP_V3/BASE=5 (new small bucket, all
`build_instrument_id`-shaped), AERODROME_V3/BASE=2, PANCAKESWAP_V3/ETHEREUM=2, UNISWAP_V3/POLYGON=2. **No new
venue/chain root cause** — the top-2 buckets (VELODROME_V2 + UNISWAP_V3, both OPTIMISM) are still 84% of the total and
still the confirmed external Graph-Protocol "bad indexers" condition this doc already root-caused as
`BLOCKED-UPSTREAM-OUTAGE` four passes running; no code fix applies to them.

**New this pass — directly observed the P3 CURVE/OPTIMISM stale-VM finding live, not just inferred from row-count
deltas.** `gcloud compute instances list` confirms `mtds-dex-swaps-backfill-1`/`-2` are still RUNNING, both launched
2026-07-23T07:0x — a full day before the `EXPECTED_SUBGRAPH_DEINDEXED` fix (`market-tick-data-service@dddd1b21`) shipped
2026-07-24, and (per `market_tick_data_service.cli.handlers.dex_swaps_handler`'s VM-boot-time floating-tarball contract
— VMs don't live-reload) still running that pre-fix binary. Tailed `mtds-dex-swaps-backfill-1`'s live `run.log`
directly: at `2026-08-01T09:44:06Z`, mid-cycle, it logged
`curve/OPTIMISM: messari schema failed... sushi_custom schema failed... WARNING Failed to collect swaps curve/OPTIMISM: All 5 cascade schemas returned GraphQL errors for curve/OPTIMISM`
— the exact OLD pre-fix message/`attempted_failed` classification, reproduced in real time about an hour after the
previous identical occurrence (`08:47:57Z`). Confirms CURVE/OPTIMISM's continued growth (8 rows 2026-07-28 → 122 rows
today) is exactly this stale-VM artifact, still live, not a new condition.

**Why the P3 todo's VM restart is NOT a quick fix (new safety finding, explains the repeated "out of scope" deferrals
above rather than just restating them)**: `dex_swaps_handler.process()` takes one `target_day` per invocation and the
VM's own `run.log` shows "DEX swaps collection complete" cycles ~45-90min apart with sharply different total record
counts each time (809022 / 716927 / 580236) — consistent with the VM walking a **calendar-day-by-day historical
backfill** from the launcher's default `START_DATE=2023-01-01`, not a "re-poll today" loop. Checked
`gs://deployment-scripts-central-element-323112/vm-logs/mtds-dex-swaps-backfill-1/` directly: **no `PROGRESS.json`
exists** for this VM (only `run.log` + `TARBALL_PINS.json`, the latter carrying no pinned SHA — `"pins": {}`,
`"floating": ["MTDS_TARBALL_SHA", "UTL_TARBALL_SHA"]`). Per the workspace's own PROGRESS-checkpoint contract
(`/codex/05-infrastructure/vm-launcher-runbook.md`), a relaunch with no monotonic checkpoint present replays
`START_DATE` from scratch — i.e. simply deleting + relaunching these two VMs today would silently discard **9 days of
real 2023-01-01-forward historical backfill progress**, not just pick up the CURVE/OPTIMISM fix. That is a materially
worse outcome than the current 122-row/~24-per-day-per-VM trickle, so **not attempting the restart this pass either** —
same conclusion as every prior escalation, but now with the concrete mechanism (`dex_swaps_handler.py` / the
`launch-mtds-dex-swaps-backfill-vm.sh` launcher have no `record_vm_progress`/`PROGRESS.json` wiring) rather than a
restated "out of scope" note. **Updated the P3 todo below** with this precondition so whoever next picks it up doesn't
attempt a naive delete+relaunch.

No code fix ships this pass — every fixable class already has its fix on `live-defi-rollout` (`dddd1b21`); the remaining
volume is either external-upstream (84%) or blocked on the VM-checkpoint gap above (9%) or noise-level new buckets (<1%,
`build_instrument_id`/PANCAKESWAP_V3/BASE, `"has allocated indexers but"` on
UNISWAP_V3/OPTIMISM+UNISWAP_V3/BASE+UNISWAP_V4/ETHEREUM x4 rows, a `521` gateway error on PANCAKESWAP_V3/BSC x2 rows —
all single-digit counts, not chased further, consistent with this doc's established bar for what's worth a dedicated
follow-up).

Source: `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009) CRITICAL page ("STATIC BACKLOG" framing), `data_pipeline_failure`
escalation `agt-35d769`, slot 8, 2026-08-01.

## Verified live (2026-08-02, slot 8, data_engineering) — UNISWAP_V3/OPTIMISM crosses the multi-day bar; PANCAKESWAP_V3/BSC's earlier "self-heal" reveals a DIFFERENT, still-open condition

Re-probed both subgraph IDs directly against the gateway
(`https://gateway-arbitrum.network.thegraph.com/api/{key}/subgraphs/id/{id}`, `thegraph-api-key` GSM secret, same
credential path `scripts/subgraph_health_probe.py` uses — the sanctioned daily/6h Cloud Run probe for exactly this
purpose), 3 tries each, plus the sanctioned probe's own `--dry-run --no-write-fingerprints` mode for a second
independent signal:

**UNISWAP_V3/OPTIMISM — VERDICT: permanent/structural, not transient.** 3/3 identical:
`bad indexers: {0xeccdf8231326a9c5aad32df76a633aaa4c49b104: Unavailable(too far behind), 0xf92f430dd8567b0d466358c79594ab58d919a6d4: BadResponse(no attestation: indexing_error), 0xfeff9093f6b32d0e5cddba743b06a1fedb87c004: Unavailable(no status: indexer not available)}`
— **byte-identical to every probe this doc has recorded since 2026-07-27** (now 6+ consecutive days, 6 independent probe
sessions across 2 slots/escalation workers, same 3 indexer addresses every time). This crosses the todo's own "multi-day
window" bar: a condition reproducing identically for 6 days, unmoved by whatever transient recovery healed
PANCAKESWAP_V3/BSC's original bad-indexers symptom same-day on 2026-07-27, is a structural indexer-fleet/allocation
problem, not a blip. Manifest confirms: `UNISWAP_V3/OPTIMISM` `dex_pool_swaps` `attempted_failed` = 495 rows (up from
477 on 2026-08-01, still actively growing, freshest row `2026-08-02T17:06:03Z`). **Answering the todo's own open
question: yes, escalate** — this now warrants either (a) replacement subgraph deployment-ID research via The Graph
Explorer, or (b) a taxonomy reason + runtime detection for the "bad indexers" condition (mirroring but not reusing
`EXPECTED_SUBGRAPH_DEINDEXED`, per this doc's own established reasoning against conflating the two). Filing that as its
own properly-scoped follow-up todo below rather than absorbing unplanned scope into this investigation (same practice as
every prior pass of this doc).

**PANCAKESWAP_V3/BSC — NEW, DIFFERENT finding: NOT "bad indexers" anymore, but its indexer head is frozen.** The `_meta`
probe returns clean (no GraphQL error, `hasIndexingErrors: true`) — confirming the 2026-07-27 "self-heal" verdict for
the _gateway-routing_ symptom still holds (no repeat of the original bad-indexers error). But the returned head block is
**byte-identical across all 3 tries THIS session** (`block.number=95170462`, `block.timestamp=1777379226` =
**2026-04-28T12:27:06Z**) **and matches the 2026-07-27 probe's own recorded block/timestamp to within 348 seconds of
block-time** (`1777378878` = `2026-04-28T12:21:18Z`, from this doc's "Verified live (re-probe, 2026-07-27...)" section)
— i.e., **this subgraph's indexer has not meaningfully advanced past 2026-04-28 in over 3 months**, including through
the entire span this doc has been tracking it (2026-07-27 → 2026-08-02). The earlier "SELF-HEALED... HEALTHY now"
verdict was based only on the absence of a gateway error on that day's probe and correctly noted
`hasIndexingErrors=true` as "worth another look" — it did not check block-timestamp staleness, which is what actually
reveals the real condition: **a stalled/dead indexer for forward data, structurally similar in effect to
CURVE/OPTIMISM's "no allocations" (permanently stuck) but with a different fingerprint (frozen head +
`hasIndexingErrors=true`, not a query-level rejection)**. This directly explains why the manifest's PANCAKESWAP_V3/BSC
`dex_pool_swaps` `attempted_failed` count has resumed growing: 15 (2026-07-28, frozen) → 30 (2026-08-01, new
`build_instrument_id`-shaped bucket) → **41 today** (freshest row `2026-08-02T13:24:28Z`) — any backfill day past
~2026-04-28 now structurally cannot be captured from this subgraph. **This is NOT the same condition this todo asks
about** (it explicitly investigates "bad indexers", which for PANCAKESWAP_V3/BSC is confirmed resolved/self-healed) —
filing as its own new todo below so it isn't conflated with or silently closed alongside the UNISWAP_V3/OPTIMISM
bad-indexers verdict.

Ephemeral verification scripts (raw gateway probe + bounded manifest count read) were scratchpad-only, not committed —
no code changes ship with this update, per this doc's own established practice that a root-cause/verdict pass does not
absorb the actual remediation work.

- [x] ✅ [DATA] P2. Investigate whether UNISWAP_V3/OPTIMISM + PANCAKESWAP_V3/BSC's "bad indexers" gateway errors are a
      transient indexer-fleet health dip or a permanent de-indexing event — **RESOLVED 2026-08-02 (slot 8)**: re-probed
      both subgraph IDs live (3/3 each) after a 6-day window (2026-07-27→2026-08-02). **UNISWAP_V3/OPTIMISM: PERMANENT
      /STRUCTURAL** — identical 3-indexer bad-indexers fingerprint across 6 consecutive days, 495 attempted_failed rows
      and growing; needs the taxonomy-reason/runtime-detection or replacement-deployment-ID follow-up (new todo below).
      **PANCAKESWAP_V3/BSC: bad-indexers condition itself CONFIRMED TRANSIENT/RESOLVED** (self-healed 2026-07-27, no
      repeat since) — but see the NEW, separate stalled-indexer-head finding filed as its own todo below; do not
      conflate the two. (repo: market-tick-data-service)
- [ ] [DATA] P2. **NEW, 2026-08-02 (slot 8).** Fix or replace UNISWAP_V3/OPTIMISM's dead subgraph deployment
      (`Cghf4LfVqPiFw6fp6Y5X5Ubc8UpmUhSfJL82zwiBFLaj`) — confirmed structural "bad indexers" condition (6+ days,
      identical fingerprint, 495+ growing `attempted_failed` rows). Either (a) research a replacement subgraph
      deployment ID via The Graph Explorer/Network Subgraph for uniswap_v3/OPTIMISM, or (b) add a distinct taxonomy
      reason + runtime detection for "bad indexers" (mirroring, NOT reusing, `EXPECTED_SUBGRAPH_DEINDEXED` — the
      semantics differ: this subgraph HAS allocations, the serving indexers are unhealthy) so future backfill attempts
      record an honest `empty_confirmed`-class outcome instead of accumulating `attempted_failed` forever. Out of scope
      for this investigation pass (root-causing != safely fixing, same reasoning this doc has applied to every other
      finding). Repo: market-tick-data-service, unified-api-contracts.
- [ ] [DATA] P2. **NEW, 2026-08-02 (slot 8).** Investigate PANCAKESWAP_V3/BSC's stalled indexer head — the subgraph
      (`Hv1GncLY5docZoGtXjo4kwbTvxm3MAhVZqBZE4sUT9eZ`) has not advanced past block 95170462 / 2026-04-28T12:27:06Z in
      over 3 months (`hasIndexingErrors=true`, confirmed byte-identical head across 2026-07-27 and 2026-08-02 probes).
      This is a DIFFERENT condition from the "bad indexers" gateway-routing symptom this doc already resolved as
      self-healed/transient for this same subgraph — it's a dead/stalled indexer for forward data, structurally similar
      to CURVE/OPTIMISM's "no allocations" case but with a different fingerprint. Explains the resumed growth in this
      cell's `dex_pool_swaps` `attempted_failed` count (15→30→41 rows, 2026-07-28→2026-08-02) for backfill dates past
      ~2026-04-28. Needs root-cause (is this genuinely dead, or an upstream re-indexing-in-progress state?) + a fix
      scoped separately from the UNISWAP_V3/OPTIMISM todo above (possibly a replacement deployment ID, possibly its own
      taxonomy reason if the "frozen head" signature turns out to be common enough to warrant runtime detection). Repo:
      market-tick-data-service.

## Progress Log

- **2026-08-03 (data_pipeline_failure escalation worker, agt-e2a77a, slot 11) — same static backlog, no new root cause,
  no code change.** Dispatched off another `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009) CRITICAL page for
  `(asset_group=defi, data_type=dex_pool_swaps)`: 1494 attempted_failed cells of 4,618,154 attempted, framed by the
  monitor itself as "STATIC BACKLOG — only 37 attempted_failed row(s) in the last 1d (below the 500-row materiality
  floor); a decaying trickle on already-tracked backlog, not a fresh regression." That 37-row/1d figure is consistent
  with the small ongoing growth this doc has tracked every pass (1087→1097→1099, 2026-07-28; 1407, 2026-08-01; ~1450s
  implied 2026-08-02) — ordinary continued trickle from the two still-open, already-diagnosed conditions
  (UNISWAP_V3/OPTIMISM's confirmed-structural "bad indexers", PANCAKESWAP_V3/BSC's frozen-indexer-head), not a new
  venue/chain or a new failure class. Per this doc's own established precedent (skip the expensive live manifest re-read
  when the dispatch context already carries the monitor's own materiality/staleness verdict — see the 2026-08-01 entries
  above), did not re-pull `availability_index.parquet` this pass; instead verified the one already-shipped code fix is
  still live: `git merge-base --is-ancestor dddd1b21 origin/live-defi-rollout` in `market-tick-data-service` —
  **confirmed still an ancestor** (CURVE/OPTIMISM's `EXPECTED_SUBGRAPH_DEINDEXED` detection is intact). No code change
  ships this pass. The three still-open todos below (UNISWAP_V3/OPTIMISM dead-subgraph fix/replace, PANCAKESWAP_V3/BSC
  frozen-indexer investigation, CURVE/OPTIMISM stale-VM restart blocked on the missing `PROGRESS.json` checkpoint)
  remain correctly scoped and are the actual remaining work — not something this one-shot escalation pass re-derives or
  re-decides. This is another data point for the still-open cross-asset-group dedup gap
  (`/plans/active/issues/dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md`, Option A/B/C, operator/design
  decision still pending): a full `data_pipeline_failure` orchestrator-agent session dispatched for a condition whose
  root-cause-relevant state has not changed since the last verified reading. Commit is doc-only (`unified-trading-pm`).
- 2026-08-02T~21:10Z (slot 8, data_engineering, task `defi_dex_pool_swaps_733_row_indexer_health_findings-001`):
  resolved the open P2 "bad indexers transient vs. permanent" todo. Re-probed both subgraphs live (gateway + the
  sanctioned `scripts/subgraph_health_probe.py --dry-run` tool) after the 6-day window this todo's own bar required.
  UNISWAP_V3/OPTIMISM: confirmed PERMANENT/structural (identical fingerprint 6 days running, 495 attempted_failed rows
  growing) — flipped the investigation todo, filed a properly-scoped follow-up fix todo. PANCAKESWAP_V3/BSC: the
  specific "bad indexers" symptom this todo asks about IS resolved/transient (confirmed self-healed, no repeat) — but
  found a NEW, distinct condition while re-checking (indexer head frozen since ~2026-04-28, `hasIndexingErrors=true`,
  explains the cell's resumed attempted_failed growth) and filed it as its own separate todo rather than conflating it
  with the resolved bad-indexers finding. See "Verified live (2026-08-02...)" section above for full evidence. No
  service code changed this pass (root-causing != safely fixing, per this doc's established practice) — this commit is
  doc-only (unified-trading-pm).
- **na-eligibility-audit 2026-07-30**: RECLASSIFY -> assigned_vm: planning (conflict-check CLEAR against 231 active
  planning docs; no open todo elsewhere duplicates this claim) - all 4 todos are bounded re-probes / per-venue
  diagnostics / a VM restart onto current code; no design or authority call left
- **context-scout 2026-08-01**: populated context_scope (5 entries).
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — deduplicated a repeated
  `defi_satellite_ao_dispatch_batch1_2026_07_25.md` entry (no content change beyond the dedup).
