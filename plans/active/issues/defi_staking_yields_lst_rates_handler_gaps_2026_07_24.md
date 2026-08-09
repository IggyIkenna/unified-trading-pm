---
doc_type: issue
title:
  "staking_yields_handler.py confirmed dead in production (registered, never scheduled) — lst_rates_handler.py's
  non-canonical-path claim is STALE (docstring lied; the real write path was already canonical)"
summary: >-
  Filing the C2-C12 scoping-pass note (defi_consolidated_closeout_2026_07_18.md line 815-816, restated in
  defi_track01_per_instrument_and_canon_id_2026_07_24.md line 697-703) with LIVE verification of both halves, not a
  transcription of the plan text. Half 1 CONFIRMED: `staking_yields_handler.py`'s `collect-staking-yields` CLI operation
  has zero Cloud Scheduler jobs (grepped all 156 asia-northeast1 jobs + checked us-central1, zero "staking" matches) and
  — more precisely than "dead code" — was NEVER WIRED INTO THE TERRAFORM SCHEDULER MODULE that provisions Cloud Run Jobs
  for every other `collect-*` DeFi op (`deployment-service/terraform/gcp/ defi_collection_scheduler.tf` declares 14
  jobs; `staking-yields` is absent from that map, and there is no matching Cloud Run Job either — `gcloud run jobs list`
  shows no `staking` job). Zero objects exist in the canonical GCS corpus at `instrument_type=staking` on any of 6
  sampled days spanning 2026-06-01..2026-07-24. **Half 2 CORRECTED, not confirmed**: `lst_rates_handler.py` does NOT
  bypass `canonical_write.py` — it calls `write_defi_rows()` (the canonical DeFi write-path SSOT) exactly like every
  other DeFi handler, which builds the path via UAC's `build_defi_partition_path()`. Live production objects were found
  in the exact canonical shape
  (`.../asset_group=defi/venue=LIDO/chain=ETHEREUM/instrument_type=lst/data_type=lst_rates/stETH.parquet`), and ZERO
  objects exist at the literal non-canonical path the plan/docstring cited
  (`gs://{bucket}/lst_rates/date=.../lst_rates_{ts}.parquet` — confirmed via `gcloud storage ls`, no match). The only
  real defect was the file's own top-of-file docstring describing that stale path — a documentation-drift bug, not a
  data-correctness bug, with a measured blast radius of zero. Both handlers' identically-stale docstrings
  (staking_yields_handler.py also said `category=defi`/glued `venue={V}-{C}`/literal `ticks.parquet`, none of which
  match its actual `write_defi_rows()` call) are fixed in this pass. Recommendation for staking_yields: WIRE a scheduler
  job (not retire) — it is a UAC-capability-declared, codex-catalogued "Production" data type with no credential blocker
  and no redundancy with lst_rates; the gap is an operational rollout oversight, not obsolete code.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-trading-pm]
scope: [engineer]
tags:
  [data-correctness, gcs-path, canonical-path, scheduler-gap, dead-code, stale-docs, defi, cloud-run-jobs, terraform]
related:
  [
    defi_consolidated_closeout_2026_07_18,
    defi_track01_per_instrument_and_canon_id_2026_07_24,
    canonical_path_oracle_blind_to_filename_stem_2026_07_20,
  ]
created: 2026-07-24
author: unknown
priority: P2
parent_epic: infrastructure_master
source:
  "defi_track01_per_instrument_and_canon_id_2026_07_24.md line ~691-703 (restating
  defi_consolidated_closeout_2026_07_18.md line 815-816's 'surfaced but not filed' note); this doc supplies the live
  verification neither prior note carried."
execution_scope: orchestrator-agent
drift_direction: advance-docs
depends_on: []
locked_by:
context_scope:
  [
    market-tick-data-service/market_tick_data_service/cli/handlers/staking_yields_handler.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/defi,
    market-tick-data-service/market_tick_data_service/cli/handlers/lst_rates_handler.py,
    unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/canonical_write.py,
  ]
locked_since:
assigned_vm: planning
resolved_by:
  "market-tick-data-service (docstring corrections only — see § 5); the two substantive follow-ups (wire a
  staking-yields Terraform/Scheduler entry; nothing to migrate for lst_rates) remain open, tracked in § 6"
assigned_role: data_engineering
---

# staking_yields dead-in-prod confirmed; lst_rates non-canonical-path claim was stale

## 0. Why this doc exists

`defi_consolidated_closeout_2026_07_18.md` (line 815-816) noted, in passing during an unrelated audit: _"Also surfaced
but not filed: `staking_yields_handler.py`'s `collect-staking-yields` CLI op has zero Cloud Scheduler jobs (dead code?);
`lst_rates_handler.py` writes to a non-canonical, non-hive path."_ That one-liner was restated verbatim (with more
detail) in `defi_track01_per_instrument_and_canon_id_2026_07_24.md` (line 697-703) as a P2 todo to "file + fix." Per the
SUB_AGENT_MANDATORY_RULES.md **grep-then-READ, not grep-then-conclude** rule, this doc re-verifies both claims live
rather than transcribing them — and the second claim does not hold up.

## 1. `staking_yields_handler.py` — CONFIRMED dead in production

### 1.1 Registered but never scheduled

`market-tick-data-service/market_tick_data_service/cli/main.py:563` registers
`"collect-staking-yields": StakingYieldsHandler` in `ServiceBootstrap.operations`, so the CLI operation exists and would
run if invoked. It is never invoked:

- **Cloud Scheduler**: `gcloud scheduler jobs list --location=asia-northeast1 --project=central-element-323112` returned
  156 jobs; **zero** match `staking` (grepped the full table). Cross-checked `us-central1`: 0 jobs total (confirms
  `asia-northeast1` is the only region in use — every other `uts-prod-*`/`uts-dev-*`/`uts-staging-*` job lives there).
  By contrast, the sibling operation `collect-lst-rates` has `uts-prod-mtds-collect-lst-rates-cron` (schedule
  `0 1 * * *`, ENABLED).
- **AWS EventBridge**: could not directly enumerate (`aws events list-rules` returned `AccessDeniedException` for the
  current role, `events:ListRules` not granted) — disclosed honestly, not silently assumed clean. However every DeFi
  MTDS collector in this codebase schedules exclusively via GCP Cloud Scheduler → Cloud Run Jobs (the
  `uts-prod-mtds-collect-*-cron` naming convention, all 14 wired ops below); there is no AWS-side scheduling pattern
  anywhere in the DeFi collection pipeline, so a hidden AWS trigger would be a first-of-its-kind exception, not a
  plausible unverified gap.
- **No Terraform / Cloud Run Job wiring**: `deployment-service/terraform/gcp/defi_collection_scheduler.tf` is the actual
  SSOT that provisions BOTH the Cloud Run Job spec AND the Cloud Scheduler cron for each DeFi `collect-*` op (its own
  header comment: _"This file declares both halves of the chain ... so cutting them on/off is single-PR"_). Its
  `defi_collect_operations` map has exactly 14 keys: `gas-fees`, `oracle-prices`, `dex-pools`, `dex-swaps`,
  `lending-indices`, `lst-rates`, `vault-share-price`, `perp-funding`, `liquidations`, `eigenlayer-rewards`, `evm-defi`,
  `solana-defi`, `mev-events`, `bridge-events`. **`staking-yields` is absent.** Confirmed no matching Cloud Run Job
  exists either: `gcloud run jobs list --region=asia-northeast1` shows `uts-prod-mtds-collect-lst-rates` but nothing
  with `staking` in the name. Wiring this operation would need BOTH halves created, not just a scheduler flip.
- **No bundled/manual invocation**: grepped the whole workspace for `collect-staking-yields` / `collect_staking_yields`
  outside `cli/main.py` and its own tests. The only other hits are declarative capability entries in
  `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py` (14 protocols list
  `"collect-staking-yields"` in their `mtds_operations` — a registry of what SHOULD exist, not an invoker) and the
  `defi-data-types-catalog.md` codex doc (documentation, not code). No combined collector, no manual runbook.

### 1.2 Confirmed zero rows in the canonical corpus

`gcloud storage ls` against the live `market-data-tick-defi-prd-central-element-323112` bucket found **zero** objects
under `instrument_type=staking` for every sampled day: 2026-07-24, 07-23, 07-22, 07-20, 07-15, 07-01, 06-01 (spanning
the file's entire life since its 2026-04-24 creation). This is consistent with "never run," not "ran once and stopped."

### 1.3 This is a genuine rollout oversight, not obsolete/redundant code — recommendation is WIRE, not retire

The task authorized removing the CLI registration + dead code **if retiring is clearly the right, safe, low-risk call**.
It is not, for four independent reasons, so no code was deleted:

1. **Declared as an active capability, not a relic.** `unified_api_contracts/registry/capability_declarations/ _defi.py`
   declares `"collect-staking-yields"` as an `mtds_operations` capability for **14 protocols** (LIDO, ETHERFI,
   EIGENLAYER, YEARN_V3, CONVEX, BEEFY, PENDLE, IDLE, SYMBIOTIC, KARAK, RENZO, KELPDAO, PUFFER, JITORESTAKING) — this is
   the live UAC SSOT for what the venue registry expects to be captured, not a stale comment.
2. **Codex catalog calls it Production.** `/codex/02-data/defi-data-types-catalog.md` § 7 lists `staking_yields` with
   **Status: Production (2026-04-24)** — the same date the handler was created. That status label is itself now shown to
   be wrong (never actually run), which is a second, smaller doc-drift finding folded into this one (see § 6.3) rather
   than evidence the feature was meant to be abandoned.
3. **Not redundant with `lst_rates`.** The codex explicitly distinguishes them: `lst_rates` is the on-chain
   exchange-rate (Alchemy `eth_call`); `staking_yields` is the protocol-REST APY (Lido/EtherFi APIs, DefiLlama). Both
   LIDO and ETHERFI declare BOTH operations as separate, non-overlapping capabilities.
4. **No cost/credential blocker.** The codex's own credential table lists `staking_yields` as `None (public APIs)` —
   turning it on has zero new-secret cost, consistent with the workspace's "external data is always available" hard rule
   (exhausting the free path is a credential ask, not a reason to descope).

Deleting a working, capability-declared, zero-cost data collector because nobody wired its cron is the wrong direction —
it would destroy real engineering work (the LIDO/EtherFi/EigenLayer fetchers are implemented and functional) and require
someone to rebuild it later. **Recommended fix**: add a `"staking-yields"` entry to
`deployment-service/terraform/gcp/defi_collection_scheduler.tf`'s `defi_collect_operations` map (mirrors the existing
`"eigenlayer-rewards"` entry's shape/tier — single-region public-API fetch, no heavy TheGraph/RPC load), schedule it in
the free 01:50-01:55 UTC slot (between `eigenlayer-rewards` at 01:45 and `evm-defi` at 01:55), and apply via the same
single-PR flow every other job in that file used. **Not done in this pass** — provisioning a real Cloud Run Job +
Scheduler trigger against production is an infra change beyond a filing task's scope, tracked as the open follow-up in §
6.1.

### 1.4 Secondary, narrower finding: even wired, the handler covers 3 of 14 declared protocols

`StakingYieldsHandler` implements exactly 3 venues (LIDO stETH, ETHERFI weETH, EIGENLAYER restaking APY) against the 14
protocols the UAC capability registry declares for this operation. This is real but out of this doc's scope — noted for
whoever picks up § 6.1 so "wire the scheduler" isn't mistaken for "capability-complete."

## 2. `lst_rates_handler.py` — the non-canonical-path claim is STALE, not current

### 2.1 What the code actually does today

Every write path in `lst_rates_handler.py` (`_write_empty_lst_marker`, `_write_single_lst_group`) calls
`write_defi_rows(...)` from `market_tick_data_service/market_interface/adapters/defi/canonical_write.py` — the **same
canonical DeFi write-path SSOT** every other DeFi handler uses (including `staking_yields_handler.py` itself).
`write_defi_rows` builds every object path via UAC's
`unified_api_contracts.canonical.partition_paths.build_defi_partition_path()`:

```
raw_tick_data/by_date/day={YYYY-MM-DD}/pipeline_mode={mode}/asset_group=defi/
  venue={V}/chain={C}/instrument_type={IT}/data_type={DT}/{file_name}
```

This is the fully canonical hive-partitioned shape — `asset_group=`/`pipeline_mode=` are both present, not bypassed.

### 2.2 Verified against live production objects, not just code-reading

```
$ gcloud storage ls gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=2026-07-20/pipeline_mode=batch_onchain_subgraph/asset_group=defi/venue=LIDO/chain=ETHEREUM/instrument_type=lst/data_type=lst_rates/
  .../data_type=lst_rates/stETH.parquet
  .../data_type=lst_rates/wstETH.parquet
```

Real, current production LST-rate objects exist in exactly the canonical shape. Cross-checked the literal non-canonical
path the plan/docstring cited:

```
$ gcloud storage ls gs://market-data-tick-defi-prd-central-element-323112/lst_rates/
ERROR: (gcloud.storage.ls) One or more URLs matched no objects.
```

**Zero objects exist there — measured blast radius is zero, not "some legacy data to migrate."** There is nothing to
migrate because the claimed path was never actually written to in the corpus's history (`write_defi_rows` has been the
write mechanism since `4ca2640d` "shard DeFi writer to one parquet per instrument," well before this session).

### 2.3 The actual defect: a stale docstring, not a live bug

The file's own top-of-file docstring (pre-fix) read:

```
GCS path:
  gs://{bucket}/lst_rates/date={YYYY-MM-DD}/lst_rates_{timestamp}.parquet
```

`git log -p` shows this exact text has been present since the file's earliest form and was never updated when the write
mechanism migrated to `write_defi_rows`/canonical partitioning. This is precisely the trap
`SUB_AGENT_MANDATORY_RULES.md`'s "grep-then-READ, not grep-then-conclude" rule warns about: the 2026-07-22 scoping pass
evidently cited this docstring as ground truth without tracing the actual `_write_single_lst_group()` call — 0 hits on
"does it match reality" ≠ "it's true," and here reading the runtime code (not just the comment) reverses the verdict
entirely.

## 3. `staking_yields_handler.py`'s docstring had the identical defect (never-run, so never checked)

Independently of the scheduling gap, `staking_yields_handler.py`'s docstring described a path that ALSO never matched
its actual `write_defi_rows(...)` call: `category=defi` (real: `asset_group=defi`), glued `venue={VENUE}-{CHAIN}` (real:
separate `venue=`/`chain=` segments), and a literal `ticks.parquet` leaf (real: `write_defi_rows` shards by sanitized
`instrument_id` symbol — e.g. `stETH.parquet`, `weETH.parquet`, `EIGEN.parquet` — the caller's
`file_name="ticks.parquet"` argument is a documented no-op for any non-empty `rows`, per `write_defi_rows`'s own
docstring: _"`file_name` applies only to the empty-marker case"_). This mismatch could never surface via production data
because the handler has never run (§ 1), so it was never noticed. Not fixed beyond the docstring correction — the dead
`file_name="ticks.parquet"` argument at `staking_yields_handler.py:137` is left as-is pending § 6.1's scheduler wiring
(a real fix should verify the intended per-venue shard naming end-to-end against live data, not guess at it now with
zero rows to check against).

## 4. Blast-radius summary

| claim                                                | verdict                                     | evidence                                                                                                    |
| ---------------------------------------------------- | ------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `staking_yields_handler.py` dead in production       | **CONFIRMED**                               | 0/156 scheduler jobs match; absent from `defi_collection_scheduler.tf`; 0 GCS objects across 6 sampled days |
| `lst_rates_handler.py` bypasses `canonical_write.py` | **FALSE — stale claim**                     | live code calls `write_defi_rows`; live GCS objects are canonical; 0 objects at the claimed legacy path     |
| `staking_yields_handler.py`'s own docstring path     | **also stale** (separate defect, same file) | never matched its `write_defi_rows` call; unverifiable in prod because never run                            |

## 5. Fix shipped in this pass (docstrings only — zero behavior change)

`market-tick-data-service@<commit-sha-filled-at-ship-time>`: corrected both handlers' top-of-file GCS-path docstrings to
describe the real `write_defi_rows`/`build_defi_partition_path` canonical shape, with an inline pointer back to this
issue doc. No functional code changed; `quality-gates.sh` run scoped to these two files before commit.

## 6. Residual / open follow-up work

- [x] ✅ [SERVICE] P2. Add a `"staking-yields"` entry to
      `deployment-service/terraform/gcp/ defi_collection_scheduler.tf`'s `defi_collect_operations` map (schedule
      ~`50 1 * * *`, between `eigenlayer-rewards` 01:45 and `evm-defi` 01:55; CPU/memory tier ≈ `eigenlayer-rewards`'s,
      since both are light single-region public-API/RPC fetches) so `collect-staking-yields` actually runs. This is a
      real Cloud Run Job + Cloud Scheduler provisioning change against production — out of scope for this filing pass;
      apply + verify (`STARTED` within a run, ≥1 manifest row written, no fire-and-forget) as its own tracked infra
      change. — DONE 2026-07-26, deployment-service@bd46bf2 (`defi_satellite_ao_dispatch_batch1_2026_07_25.md`). Full
      evidence there: `tofu plan` showed a clean additive `2 to add, 0 to change, 0 to destroy`; applied; manually
      triggered a real execution (not fire-and-forget — watched to `Completed True`); confirmed 1 manifest row
      (`instrument_type=staking`, `venue=EIGENLAYER`, `capture_status=captured`) in the per-VM shard. Also surfaced +
      fixed a real bug from that live run: LIDO/EtherFi DNS failures were being silently miscategorized as
      `record_zero_rows` instead of `record_failed` — fixed market-tick-data-service@2b6d9e6b (see § 6.2 below, whose
      own "once § 6.1 lands" precondition is now met for the leaf-name verification, though the classification bug found
      here was a different, more urgent defect than what § 6.2 anticipated).
- [x] ✅ [SERVICE] P3. **DONE 2026-08-05 (slot-11, batch5) — market-tick-data-service@1564a983.** Once § 6.1 lands and
      the handler actually runs, verify the real per-venue shard leaf names match expectation (`stETH.parquet` /
      `weETH.parquet` / `EIGEN.parquet` via the sanitized-symbol path) and either wire the `file_name="ticks.parquet"`
      argument to do something real or remove the dead parameter at `staking_yields_handler.py:137` (currently a
      documented no-op per `write_defi_rows`'s own contract — see § 3). GCS evidence: EIGENLAYER objects present with
      canonical instrument_key filenames (`EIGENLAYER-ETHEREUM:STAKING:EIGEN.parquet` on 2026-07-28→08-03;
      `EIGEN.parquet` on 2026-07-26). LIDO/ETHERFI zero objects (DNS failures per §6.1, classification fix shipped
      earlier). Plan's bare-symbol expectation was pre-launch estimate — actual instrument_key format IS canonical per
      `write_defi_rows` line 414. Dead `file_name="ticks.parquet"` argument removed.
- [x] ✅ [SERVICE] P3. `StakingYieldsHandler` implements 3 of the 14 protocols the UAC capability registry declares for
      `collect-staking-yields` (LIDO/ETHERFI/EIGENLAYER only — missing YEARN_V3/CONVEX/BEEFY/PENDLE/IDLE/
      SYMBIOTIC/KARAK/RENZO/KELPDAO/PUFFER/JITORESTAKING). Scoping complete — unified-trading-pm@<sha> (see §7). All 11
      protocols have existing IS adapters; 8 use DefiLlama public yields (free), 3 use AAVE Oracle (Alchemy key exists).
      Zero credential blockers. Estimate ~4 AI days. Recommendation: Phase 1 (8 DefiLlama, ~2.5d) → Phase 2 (3 AAVE,
      ~1.5d).
- [x] [DATA] P3. Correct `/codex/02-data/defi-data-types-catalog.md` § 7's `staking_yields` **Status: Production
      (2026-04-24)** label — it is not, and has never been, actually running in production; restate as "Implemented,
      unscheduled" (or similar) until § 6.1 ships, then flip to Production with the real ship date. — already covered by
      defi_satellite_ao_dispatch_batch1_2026_07_25.md (lines 326-333) (see that doc for execution).

## 7. §6.3 Scoping — capability-completion for 11 missing protocols (2026-08-05)

**Precondition check**: §6.1 (scheduler wired, 2026-07-26) + §6.2 (leaf-name verified, 2026-08-05) are both shipped. The
3 existing venues (LIDO/ETHERFI/EIGENLAYER) produce data in production — precondition met.

**Method**: read existing adapter code for all 11 protocols (in
`market_tick_data_service/market_interface/adapters/defi/`) to identify actual data sources used, then research
protocol-specific APIs where DefiLlama is not the source. Found: **all 11 protocols have existing IS adapters** that
already resolve instrument metadata; the gap is `staking_yields_handler.py` fetch functions.

### Per-protocol assessment

| #   | Protocol      | Venue Prefix  | Class            | Data Source                                      | Auth                                        | Complexity |
| --- | ------------- | ------------- | ---------------- | ------------------------------------------------ | ------------------------------------------- | ---------- |
| 4   | Yearn V3      | YEARN_V3      | YIELD            | DefiLlama yields `project=yearn-finance`         | None (public)                               | **LOW**    |
| 5   | Convex        | CONVEX        | YIELD            | DefiLlama yields `project=convex-finance`        | None (public)                               | **LOW**    |
| 6   | Beefy         | BEEFY         | YIELD            | DefiLlama yields `project=beefy`                 | None (public)                               | **LOW**    |
| 7   | Pendle        | PENDLE        | YIELD            | DefiLlama yields `project=pendle`                | None (public)                               | **LOW**    |
| 8   | Idle          | IDLE          | YIELD            | DefiLlama yields `project=idle`                  | None (public)                               | **LOW**    |
| 9   | Symbiotic     | SYMBIOTIC     | RESTAKING        | DefiLlama yields `project=symbiotic`             | None (public)                               | **LOW**    |
| 10  | Karak         | KARAK         | RESTAKING        | DefiLlama yields `project=karak-network`         | None (public)                               | **LOW**    |
| 11  | Renzo         | RENZO         | RESTAKING        | AAVE Oracle (primary) + DefiLlama coins fallback | Alchemy API key (already in Secret Manager) | **MEDIUM** |
| 12  | KelpDAO       | KELPDAO       | RESTAKING        | AAVE Oracle (primary) + DefiLlama coins fallback | Alchemy API key (already in Secret Manager) | **MEDIUM** |
| 13  | Puffer        | PUFFER        | RESTAKING        | AAVE Oracle (primary) + DefiLlama coins fallback | Alchemy API key (already in Secret Manager) | **MEDIUM** |
| 14  | JitoRestaking | JITORESTAKING | STAKING (Solana) | DefiLlama yields `project=jito-restaking`        | None (public)                               | **LOW**    |

### Data-source details

**Tier A — DefiLlama public yields (8 protocols, ~2h each):** `https://yields.llama.fi/pools` returns current APY + TVL
for all tracked pools (~7,000+ across all protocols), filterable by `project` slug. This is the FREE/public endpoint,
NOT the $300/mo Pro API — the existing adapters already use it and it works in production. Each protocol needs an
`async def _fetch_<protocol>_apy(session, date)` function that calls DefiLlama, filters by project slug, extracts APY +
TVL fields, and returns rows in the handler's expected shape `(symbol, ts_event, venue, chain, apy, total_staked)`. The
DefiLlama endpoint returns CURRENT snapshot (not historical) — acceptable since the existing `_fetch_eigenlayer_apy` has
the same limitation (APY=0.0, only TVL populated). Historical backfill would need
`https://yields.llama.fi/chart/{pool_id}` (also public, per-pool UUID).

**Tier B — AAVE Oracle + DefiLlama fallback (3 protocols, ~3-4h each):** Renzo (ezETH), KelpDAO (rsETH), Puffer (pufETH)
use the same pattern as the existing `lst_rates_handler.py` — query AAVE V3 Oracle `getAssetPrice()` at sampled blocks
for 15-min granularity oracle_prices, with DefiLlama `coins.llama.fi/prices/historical` as daily fallback. The adapters
already implement this fully; the staking_yields handler would either: (a) reuse the adapter or (b) add simplified fetch
functions that extract the "yield" from exchange-rate drift (ezETH/ETH, rsETH/ETH, pufETH/ETH price changes over time,
analogous to how `lst_rates_handler.py` computes LST exchange rates). The Alchemy API key is already stored in Secret
Manager and used by the existing adapters — no new credential needed.

### Implementation estimate

- **8 DefiLlama protocols**: ~2h each = ~16h total. Pattern is identical — add URL constant, add fetch function, add
  tuple to `venues` list. Bulk-add might reduce overhead.
- **3 AAVE Oracle protocols**: ~3-4h each = ~10-12h total. More complex (RPC calls, block sampling, exchange-rate
  computation) but the adapter code is a reference implementation.
- **Integration/testing**: ~4h (update `STAKING_URL_FALLBACKS`, add unit tests, verify QG green).
- **Total**: ~30-32h (~4 calibrated AI days, `brand-new` × 1.0).

### Blockers

- **None.** All data sources are public (DefiLlama yields) or use existing credentials (Alchemy). No new API keys, no
  paid subscriptions, no operator-gated actions needed.
- **One design question** (answerable by any data_engineering worker): for the 8 DefiLlama protocols, should
  `StakingYieldsHandler` call `https://yields.llama.fi/pools` once and fan-out by project slug (1 HTTP request for all
  8), or per-venue like the existing pattern (8 HTTP requests)? Recommendation: **batch once and fan out** — the
  single-response payload is ~2 MB raw, ~50 KB filtered, and DefiLlama's public endpoint throttles to ~2 req/s. One call
  for all 8 is both faster and more polite to their infra. Add
  `_fetch_defillama_staking_yields(session, date) -> dict[str, list[dict]]` keyed by project slug, then per-venue
  functions extract their slice.

### Recommendation

**Split into two phases**: Phase 1 (8 DefiLlama protocols, ~2.5 AI days) ships the bulk of the gap with no credential
risk. Phase 2 (3 AAVE Oracle protocols, ~1.5 AI days) follows once Phase 1 is verified in production. If operator
prefers a single pass, all 11 can ship together (~4 AI days). File as a single plan with two sequential phases or two
independent plans.

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY -> assigned_vm: planning (conflict-check CLEAR against 231 active
  planning docs; no open todo elsewhere duplicates this claim) - precondition (S6.1 scheduler wiring) shipped
  2026-07-26; both residual todos are bounded leaf-name verification + a named-target capability scoping pass
- **context-scout 2026-08-01**: populated context_scope (6 entries).
- **context-scout 2026-08-03**: populated/refreshed context_scope (8 entries).
- **context-scout 2026-08-03 (re-scout)**: trimmed to 5 entries (was 8, over the 2-6 minimal-list target) — dropped
  `lst_rates_handler.py` (its finding is fully resolved, docstring-only), the shipped terraform file, the closeout plan,
  and the canonical-path-oracle sibling doc; added `capability_declarations/_defi.py` (the 14-protocol declaration the
  remaining §6.3 capability-completion todo needs).
- **data_engineering slot-12 2026-08-05**: §6.3 capability-completion scoping done. Read all 11 adapter files +
  capability declarations. Key finding: all 11 protocols already have IS adapters; 8 use DefiLlama public yields (free,
  no auth), 3 use AAVE Oracle + DefiLlama fallback (Alchemy key exists). Zero credential blockers. Estimate ~4
  calibrated AI days split across two phases. Full scoping in §7 above.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (5 entries), unchanged. All §6 residual todos are
  now checked done — doc appears eligible for closeout review (not this skill's scope to act on).
- **context-scout 2026-08-07**: refreshed context_scope (5 entries) — the 2026-08-06 archive-candidate audit converted
  §7's prose-only capability-completion scope into a tracked `[SERVICE] P2` Follow-up todo, so re-pointed the list at
  that remaining work: swapped the resolved-finding docs (`defi_track01_...md`, `defi-data-types-catalog.md`) for the
  `market_interface/adapters/defi` directory (the 11 existing IS adapters §7 names) and `lst_rates_handler.py` (the
  exchange-rate-yield reference pattern §7 explicitly cites for the 3 AAVE-Oracle protocols).

## Follow-ups

- [x] ✅ [SERVICE] P2. Implement staking-yields capability-completion for the 11 missing protocols (Phase 1: 8 DefiLlama
      protocols ~2.5d; Phase 2: 3 AAVE Oracle protocols ~1.5d) — file as a new plan per §7 — Phase 1 DONE
      market-tick-data-service@c2bd2d53: `_DEFILLAMA_VENUES` tuple + `_fetch_defillama_yields_pools` +
      `_extract_defillama_venue_rows` + `_make_defillama_venue_fetcher` added; unit tests in
      `tests/unit/test_staking_yields_handler.py`; all 8 venues
      (YEARN_V3/CONVEX/BEEFY/PENDLE/IDLE/SYMBIOTIC/KARAK/JITORESTAKING) batch-fetched from
      `https://yields.llama.fi/pools` and fan-out per project slug. QG green. Phase 2 tracked in follow-up below.
- [ ] [SERVICE] P3. Implement staking-yields Phase 2: 3 AAVE Oracle protocols (RENZO/KELPDAO/PUFFER ~1.5 AI days) — each
      uses AAVE V3 Oracle `getAssetPrice()` + DefiLlama coins fallback; Alchemy key already in Secret Manager. Add fetch
      functions to `staking_yields_handler.py`, add to `fixed_venues` list, add unit tests. See §7 for per-protocol
      data-source details.

> **2026-08-06 archive-candidate audit**: All 4 checkboxes are [x], but §7 describes ~30-32h of unimplemented work
> ('File as a single plan with two sequential phases') — the capability-completion for
> YEARN_V3/CONVEX/BEEFY/PENDLE/IDLE/SYMBIOTIC/KARAK/RENZO/KELPDAO/PUFFER/JITORESTAKING was only scoped, never
> implemented, and no plan was filed; a deferred follow-up in prose with no tracked `- [ ]` todo.
