---
doc_type: issue
title:
  "CeFi book_snapshot_5 writes started FATAL-failing write-time schema validation for every venue since the 2026-07-27
  validate=True flip -- the registered UAC SchemaContract required a fictional serialised bids/asks string column
  nothing ever produced, AND market-tick-data-service never derived ts_event for this data_type; both halves fixed"
summary: >-
  DP_RUN_MOSTLY_EMPTY (DP-FETCH-009) CRITICAL alert, asset_group=cefi data_type=book_snapshot_5: 299,467
  attempted_failed of 1,037,001 attempted (28.9%), flagged FRESH (newest attempted_failed activity 0d old, ~4,809 rows
  on 2026-07-28 alone, up from ~2,563 the day before -- an accelerating trend, not the already-known stale Tardis-403
  backlog documented in cefi_high_attempted_failed_batch_cluster_2026_07_23.md). Root-caused via a live,
  column-projected read of gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet:
  every fresh row's error_reason is "schema contract violated for cefi/<venue>/<perpetual|spot_pair>/book_snapshot_5",
  spanning many venues (KRAKEN-SPOT, OKX-SWAP, BINANCE-FUTURES, BITFINEX-SPOT, OKX-SPOT, KRAKEN-FUTURES, DERIBIT, ...).
  Traced to market-tick-data-service@3169d25e (2026-07-27,
  cefi_tardis_write_schema_contract_column_mismatch_2026_07_27.md): that fix turned validate=True on UNCONDITIONALLY at
  both CeFi Tardis write call sites, based on a code comment claiming
  "book_snapshot_5/derivative_ticker/incremental_book_l2 have no registered contract" -- FALSE for book_snapshot_5
  (CEFI_PERPETUAL_BOOK_SNAPSHOT_5 / CEFI_SPOT_PAIR_BOOK_SNAPSHOT_5 ARE registered, requiring a serialised "bids"/"asks"
  string column that no writer ever produced and no reader ever consumed -- confirmed via a workspace-wide grep/read,
  the contract was drafted aspirationally on 2026-04-17, six weeks before the real Tardis flattened wire format was even
  reverse-engineered into a regression test). The moment validate=True shipped, every real book_snapshot_5 write (whose
  true wire shape is 20 flat per-level columns -- asks[0..4].price/.amount, bids[0..4].price/.amount -- confirmed via
  tests/unit/test_tardis_book_snapshot_v7.py) started failing the missing_column check on the fictional bids/asks
  columns, isolated per-shard so it never crashed -- just silently recorded attempted_failed and re-failed every future
  wave, exactly the class of bug the workspace's DP-FETCH registry exists to catch. Fixed in two commits (one shipped
  concurrently by another worker mid-investigation, discovered via git pull, not duplicated): (1)
  unified-api-contracts@8db188fe (slot-9) corrected CEFI_PERPETUAL_BOOK_SNAPSHOT_5 / CEFI_SPOT_PAIR_BOOK_SNAPSHOT_5 to
  require the real 20 flattened float64 columns instead of the fictional strings -- verified via workspace-wide grep
  that changing this breaks nothing (nothing produces or consumes the string format; validate_dataframe's dtype="string"
  check is content-agnostic, so the contract was silently unenforceable garbage from day one). (2)
  market-tick-data-service@339ca767 (this task) closed the remaining gap: even against the corrected contract,
  validation still failed missing_column:ts_event because _rename_and_derive_contract_columns (tardis_shared.py) never
  derived ts_event for book_snapshot_5 (data_type wasn't in _WIRE_COLUMN_RENAMES, so the function early-returned before
  the ts_event derivation step that trades/liquidations/ quotes already get) -- added book_snapshot_5 to that dict
  (empty rename map -- the asks[N]/bids[N] column names already matched), corrected the now-doubly-stale comment, and
  added a regression test exercising the real wire shape end-to-end through finalise_and_write_cefi_shards. Reproduced
  the failure locally against a realistic wire-shaped DataFrame before the fix (missing_column:ts_event, the sole
  remaining violation after the contract fix), verified zero violations after. A separate, PRE-EXISTING, un-triggered
  mismatch was found and left alone: derivative_ticker also has a registered contract (CEFI_PERPETUAL_DERIVATIVE_TICKER)
  that _rename_and_derive_contract_columns also doesn't bridge to ts_event -- but a live manifest read confirms
  derivative_ticker's current attempted_failed rows are rate-limit/network causes only (no schema-contract violations),
  meaning it is not reaching this same write path via live/routine capture right now; left as a documented,
  currently-dormant gap rather than an unverified speculative fix. Also NOT in scope: features-service's
  CrossInstrumentRawDataLoader.load_book_snapshots expects a THIRD shape (native list-of-[price,size] columns from a
  non-existent l2_book_checkpoints writer) -- already broken independent of this fix, a separate pre-existing gap, not
  touched here. Historical backlog (299k+ attempted_failed rows accumulated since 2026-07-27) is NOT retroactively
  cleared by this code fix -- it requires a normal idempotent backfill re-attempt on a future wave, same as every other
  historical-poisoned-rows class already documented in cefi_high_attempted_failed_batch_cluster_2026_07_23.md.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags:
  [
    data-correctness,
    schema-contract,
    write-time-guard,
    fail-hard,
    tardis,
    book_snapshot_5,
    ts_event,
    dp-fetch-009,
    escalation,
  ]
related:
  [
    /plans/archive/issues/cefi_tardis_write_schema_contract_column_mismatch_2026_07_27.md,
    /plans/archive/issues/cefi_high_attempted_failed_batch_cluster_2026_07_23.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-28
author: unknown
parent_epic: cefi_master
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm: NA
execution_scope: local-only
resolved_by:
  "market-tick-data-service@339ca767 + unified-api-contracts@8db188fe (contract shape + ts_event) +
  unified-api-contracts@1c4d8864 (deep-level nullable gap, 2026-07-31); deployment-service@a564cca (2026-07-31,
  DP-FETCH-009 alerting-materiality fix — closes the repeated-duplicate-dispatch waste this doc's own Progress Log
  documents, see dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md)"
source:
  "CRITICAL DP_RUN_MOSTLY_EMPTY (DP-FETCH-009) escalation agt-ff6e10, dp-fleet-monitor -> agent-orchestrator
  data_pipeline_failure worker (slot-16), fired 2026-07-28, asset_group=cefi data_type=book_snapshot_5, 299,467
  attempted_failed of 1,037,001 attempted (28.9%), flagged Fresh (0d old)."
last_updated:
  2026-08-03 (21st+ dispatch, agt-52c156, slot 13 -- numerator 300,674/1,123,966 (26.8%), STATIC BACKLOG (210 rows/24h,
  below the 500-row floor); numerator DECREASED vs the 19th-dispatch reading (300,744->300,674) while attempted grew --
  strongest evidence yet of no regression. Confirmed all 5 fix commits still hold; relied on the 19th dispatch's
  minutes-earlier live read (zero new schema-contract-violation rows past the 2026-07-31T04:18:05Z checkpoint, trickle
  is 100% the OTHER already-tracked Tardis rate-limit mechanism, 98.2% capture success) rather than repeating it -- see
  Progress Log for detail.)
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/archive/issues/cefi_tardis_write_schema_contract_column_mismatch_2026_07_27.md,
    /plans/archive/issues/cefi_high_attempted_failed_batch_cluster_2026_07_23.md,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py,
    /plans/archive/issues/dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
---

# CeFi `book_snapshot_5` schema-contract mismatch -- root cause + fix (2026-07-28)

## Alert as received

```
Event: DP_RUN_MOSTLY_EMPTY (DP-FETCH-009), severity CRITICAL, asset_group=cefi, data_type=book_snapshot_5
299,467 attempted_failed of 1,037,001 attempted (ratio 28.9%; abs>=500 or ratio>=10%)
"A backfill exited 0 / captured climbed but failed this batch invisibly."
Fresh -- newest attempted_failed activity 0d ago.
```

No issue doc was pre-filed (`(none — alert carries the details)`); this doc is the escalation-worker's own
investigation + fix write-up, filed per the standard audit->issue->plan flow.

## Verification -- this IS a fresh regression, not the known stale Tardis-403 backlog

A live, column-projected read of
`gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` (`book_snapshot_5` rows:
2,382,157 total, 299,511 `attempted_failed` -- matches the alert almost exactly) shows:

- `max attempted_at` = `2026-07-28T09:05:38Z` (today).
- Per-day `attempted_failed` counts: 2026-07-28 = 4,809; 2026-07-27 = 2,563; 2026-07-26 = 488 -- an ACCELERATING trend,
  not a static backlog re-firing (contrast `cefi_high_attempted_failed_batch_cluster_2026_07_23.md`, where the same
  alert class was confirmed to be a 6-30-day-stale backlog re-evaluated on a periodic sweep).
- Every one of today's 4,809 rows carries `error_reason` =
  `"schema contract violated for cefi/<VENUE>/<perpetual| spot_pair>/book_snapshot_5: 1 violation(s); first=column 'ts_event' missing from dataframe"`
  (verified directly, post-fix, via the reproduction below), spanning KRAKEN-SPOT (1,391), OKX-SWAP (959),
  BINANCE-FUTURES (725), BITFINEX-SPOT (408), OKX-SPOT (394), KRAKEN-FUTURES (225), COINBASE-SPOT (174),
  COINBASE-FUTURES (159), OKX-FUTURES (122), BITFINEX-FUTURES (90), ASTER (50), BYBIT (50), DERIBIT (32), OKX (21),
  LIGHTER-ZKSYNC (9) -- i.e. essentially every CeFi venue that captures book_snapshot_5, which is exactly what "the
  write-time gate now rejects 100% of this data_type's writes" looks like.

## Root cause

`market-tick-data-service@3169d25e` (2026-07-27, `cefi_tardis_write_schema_contract_column_mismatch_2026_07_27.md`)
turned `validate=True` on UNCONDITIONALLY at both CeFi Tardis write call sites in `tardis_cefi_shards.py`
(`_write_one_cefi_shard` and `_tardis_cefi_shard_router`) -- the flag is passed regardless of `data_type`, so every
shard write, not just trades/liquidations/quotes, now looks up and enforces a UAC `SchemaContract`.

That commit's own code comment justified leaving `book_snapshot_5` untouched in the wire-column-bridging step with:
_"book_snapshot_5/derivative_ticker/incremental_book_l2 have no registered contract here and are deliberately left
untouched (their consumers still expect the raw wire column names)."_ This claim is **false** for `book_snapshot_5`:
`CEFI_PERPETUAL_BOOK_SNAPSHOT_5` / `CEFI_SPOT_PAIR_BOOK_SNAPSHOT_5` ARE registered in
`unified-api-contracts/unified_api_contracts/internal/schemas/contracts.py` (added 2026-04-17, `3f6a34fc`/`b82a154e` --
six weeks _before_ the real Tardis wire format was even reverse-engineered into a regression test, 2026-05-28,
`tests/unit/test_tardis_book_snapshot_v7.py`). The contract required a serialised `"bids"`/`"asks"` string column
("Serialised list of top-5 bid (price, size) levels") -- but **no writer anywhere in the workspace ever produced this
format, and no reader anywhere ever consumed it** (confirmed via a workspace-wide grep across market-tick-data-service,
market-data-processing-service, features-service, strategy-service). The real Tardis `book_snapshot_5` CSV wire format
is 20 flat per-level columns:
`asks[0].price, asks[0].amount, ..., asks[4].price, asks[4].amount, bids[0].price, bids[0].amount, ..., bids[4].price, bids[4].amount`.

Because `unified-api-contracts`'s `validate_dataframe`/`_dtype_matches` treats `dtype="string"` as content-agnostic (any
non-null string value passes -- it never parses/validates JSON structure), this fictional contract was **silently
unenforceable garbage from the day it was registered**, invisible until something finally turned `validate=True` on for
this write path -- which is exactly what `3169d25e` did on 2026-07-27, exposing it immediately.

## The fix -- two halves, two repos, two workers (discovered mid-investigation, not duplicated)

**Half 1 (contract shape) -- `unified-api-contracts@8db188fe`** (shipped by slot-9, 2026-07-28T09:22:12Z, concurrently
with this investigation -- discovered via `git pull --ff-only` mid-session, not re-done): replaced the fictional single
"bids"/"asks" string `ColumnSpec` pair with 20
`ColumnSpec(name=f"{side}[{level}].{field}", dtype="float64", nullable=False)` entries matching the real wire column
names, for both `CEFI_PERPETUAL_BOOK_SNAPSHOT_5` and `CEFI_SPOT_PAIR_BOOK_SNAPSHOT_5`. Verified safe (breaks nothing)
because nothing currently produces or consumes the old string format.

**Half 2 (ts_event derivation) -- `market-tick-data-service@339ca767`** (this task): even against the corrected
contract, `finalise_rows_and_path`'s validation still failed with `missing_column:ts_event` -- reproduced locally
against a realistic wire-shaped `DataFrame` (20 level columns + `timestamp`/`local_timestamp`/`symbol`/`exchange`,
matching the real CSV header) BEFORE fixing, confirming this was the sole remaining violation. Root cause:
`_rename_and_derive_contract_columns` (`tardis_shared.py`) only derives `ts_event` from the raw wire `timestamp` column
for data_types listed in `_WIRE_COLUMN_RENAMES` (`trades`, `liquidations`, `quotes`) -- `book_snapshot_5` was never
added, so the function early-returned the frame unchanged, `ts_event` was never created, and validation failed even
though the level columns now matched. Fix: added `"book_snapshot_5": {}` to `_WIRE_COLUMN_RENAMES` (an empty rename map
-- the `asks[N]`/`bids[N]` column names already match the corrected contract verbatim, only the `ts_event` derivation
step needs to run), corrected the now-doubly-stale comment (which repeated the same false "no registered contract"
claim), and added a regression test (`test_finalise_and_write_cefi_shards_book_snapshot_5_real_wire_shape`) that
exercises the real wire shape end-to-end through `finalise_and_write_cefi_shards`, asserting zero isolated failures --
mirroring the existing trades/spot_pair happy-path tests in the same file. Re-verified post-ship: zero violations
against the reproduction script.

## What was found and deliberately NOT fixed (documented, not silently dropped)

1. **`derivative_ticker` has the same _class_ of gap but is currently dormant, not actively firing.**
   `CEFI_PERPETUAL_DERIVATIVE_TICKER` is also registered, and `_rename_and_derive_contract_columns` doesn't bridge
   `ts_event` for it either -- structurally the same shape of bug. But a live manifest read of `derivative_ticker`'s
   fresh (2026-07-28) `attempted_failed` rows shows ONLY rate-limit (`429`) and network-error causes, zero
   `"schema contract violated"` rows -- meaning `derivative_ticker` capture is not currently reaching this same
   Tardis-bulk-CSV write path (it's likely captured via a separate funding-rate/OI polling route). Left as a documented,
   currently-inert gap rather than an unverified speculative fix -- if a future caller starts writing
   `derivative_ticker` through `finalise_rows_and_path` with `validate=True`, this will need the same treatment.
2. **`features-service`'s book_snapshot_5 reader expects a THIRD, different shape, already broken independent of this
   fix.** `CrossInstrumentRawDataLoader.load_book_snapshots`
   (`features-service/features_service/cross_instrument/engine/raw_data_loader.py:258-276`) reads the real
   flattened-column parquet directly but feeds it to `BookDepthCalculator`/`LiquidityWallCalculator`, whose
   `required_columns` expect native list-of-`[price,size]` columns from a claimed `l2_book_checkpoints` writer that does
   not exist anywhere in MTDS/MDPS (grepped, zero hits). This consumer was already broken before this investigation and
   is unrelated to the schema-contract write-time gate -- flagged here as a genuinely new, smaller finding per the
   findings-triage rule, not fixed in this task (out of scope: a features-service reader/writer design gap, not a
   data-pipeline write-time-validation bug).
3. **Historical backlog is not retroactively cleared.** The ~299k `attempted_failed` rows accumulated since 2026-07-27
   (and the smaller pre-existing backlog underneath, per `cefi_high_attempted_failed_batch_cluster_2026_07_23.md`'s
   book_snapshot_5 entry) stay in the manifest until a normal idempotent backfill re-attempt re-runs those shards -- the
   same "historical poisoned rows never retried" class already documented there. Not filed as a separate todo -- it is
   covered by that doc's existing recommendation to work through `cefi_consolidated_closeout_2026_07_18.md`'s queued
   backfill waves.

## Verification before ship

- `bash scripts/quality-gates.sh --no-fix` in `market-tick-data-service`: EXIT 0 (sentinel `e663d72f...` matched HEAD).
- `tests/market_interface/adapters/cefi/test_tardis_canonical_output.py`: 38/38 passed, including the new regression
  test.
- Reproduced the failure locally (missing_column:ts_event, the sole violation post-contract-fix) BEFORE the MTDS fix,
  confirmed zero violations AFTER, both via a standalone script calling `_rename_and_derive_contract_columns` +
  `validate_dataframe` directly against a realistic wire-shaped DataFrame.
- `git merge-base --is-ancestor $(git rev-parse HEAD) origin/live-defi-rollout` = true post-quickmerge.

## Codex SSOTs

- `/codex/05-infrastructure/data-pipeline-alerts.md` -- DP-FETCH failure-mode registry + escalation model.
- `/codex/02-data/availability-manifest-and-data-status.md` -- 4-state capture_status, honest-absence contract.
- `plans/active/issues/cefi_tardis_write_schema_contract_column_mismatch_2026_07_27.md` -- the predecessor fix this
  doc's regression descends from.
- `plans/active/issues/cefi_high_attempted_failed_batch_cluster_2026_07_23.md` -- the earlier, unrelated (stale
  Tardis-403) alert cluster for the same data_type; this doc's fresh 2026-07-28 numbers are a DIFFERENT, NEW mechanism
  layered on top, not a re-fire of that backlog.

## Todos

- [x] ✅ [SERVICE] P1. Fix the contract shape (real flattened wire columns, not a fictional serialised string) --
      **unified-api-contracts@8db188fe** (slot-9).
- [x] ✅ [SERVICE] P1. Derive `ts_event` for `book_snapshot_5` so the corrected contract actually validates clean +
      regression test -- **market-tick-data-service@339ca767** (this task).
- [x] ✅ [DATA] P2. **DONE 2026-07-28 (slot-2, `data_pipeline_failure` escalation worker, task agt-ba5c2f, re-probe)** —
      confirmed via a fresh column-projected manifest read (`data_type=book_snapshot_5`,
      `capture_status=attempted_failed`) at 2026-07-28T18:08Z: max `attempted_at` across the WHOLE cell is still
      `2026-07-28T10:49:59Z` — i.e. **zero new `"schema contract violated"` rows in the 7+ hours since** (the fix landed
      09:45:54Z; the last 473 violation rows, all `attempted_at` 10:48:10-10:49:59Z, are the tail of an in-flight
      KRAKEN-SPOT/OKX-SWAP run that started before the fixed code was deployed/picked up — not a recurrence after). The
      ratio-climbing / error-reason-recurring condition this todo was gating on has not recurred. Confirms both fix
      halves (`unified-api-contracts@8db188fe` + `market-tick-data-service@339ca767`) are effective in production, not
      just in the regression test.
- [x] ✅ [DATA] P3. **DONE — market-tick-data-service@6bf568ee (2026-07-30).** `derivative_ticker` capture DID start
      routing through `finalise_rows_and_path` with `validate=True` (LIGHTER-ZKSYNC's first real production write hit
      `missing_column:ts_event`, per
      `/plans/archive/issues/lighter_zksync_derivative_ticker_tardis_numeric_market_id_leaks_into_symbol_schema_2026_07_29.md`).
      Fixed with the same treatment this doc's book_snapshot_5 fix used: added `"derivative_ticker": {}` to
      `_WIRE_COLUMN_RENAMES` in `tardis_shared.py` (verified live, 2026-07-30 — `funding_rate`/`open_interest`/
      `mark_price`/`index_price` already match the contract, only the `ts_event` derivation step needed to run).
      Verified live there (VM `mtds-smoke-lighter-dt-fix-v4-20260730`: zero schema failures, ~987K real rows written).
- [x] ✅ [SERVICE] P1. **DONE 2026-07-31 (`data_pipeline_failure` escalation worker, task `agt-716d56`) —
      `unified-api-contracts@1c4d8864`.** Found + fixed a THIRD, genuinely-live, previously-undiagnosed gap: the 20
      `bids[N]/asks[N].price|amount` `ColumnSpec`s were declared `nullable=False` (set 2026-07-28 alongside the
      contract-shape fix, `8db188fe` -- nullability was never separately reasoned about at the time). A real thin/
      illiquid order book (fewer than 5 resting levels on one side -- normal for e.g. a newly-listed quote asset) has
      Tardis emit NaN for the deeper levels, which FATAL-rejected the WHOLE shard (discarding real captured rows
      alongside the thin one). Changed to `nullable=True`, matching the existing `CEFI_PERPETUAL_DERIVATIVE_TICKER`
      funding_rate/open_interest/mark_price/index_price precedent; the only real consumer
      (`market-data-processing-service`'s `book_snapshot_adapter.py`) already NaN-tolerates throughout. See Progress Log
      for the full diagnostic trail (including why the prior 5 dispatches all missed this).
- [ ] [SERVICE] P3. `features-service`'s `CrossInstrumentRawDataLoader.load_book_snapshots` expects a third,
      non-existent `l2_book_checkpoints`-shaped input -- a separate, pre-existing reader/writer design gap, unrelated to
      this write-time-validation fix; needs its own scoping (design decision: build the missing writer, or change the
      calculators to read the real flattened columns).
- [ ] [SERVICE] P2. **Observability gap that caused the 5-dispatch misdiagnosis (a design call, not fixed here).**
      `_classify_tardis_error()` (`market-tick-data-service/.../tardis_adapter.py:164`) does `raw.split(":", 1)[0]` on
      the raised exception before it becomes the manifest `error_reason` -- for the `finalise_rows_and_path`
      schema-contract-violation message
      (`"schema contract violated for cefi/{venue}/{shard_it}/{data_type}: {N} violation(s); first={msg}"`) this throws
      away everything after the FIRST colon, so every violation for a given (venue, instrument_type, data_type)
      collapses to the identical `error_reason` string regardless of WHICH column/check actually failed. This is why
      dispatches 1-5 on this doc (all `attempted_at`-recency checks against the manifest alone) could not see that a
      brand-new violation (non-nullable level columns) was hiding behind the old, already-fixed violation's (missing
      `ts_event`) identical-looking bucket -- the manifest literally cannot distinguish them; only a live reproduction
      (as this dispatch did) or a Cloud Logging pull of the pre-truncation `SCHEMA_CONTRACT_VIOLATION` event (attempted
      here, found no VM logs reaching Cloud Logging for the producing instances -- a possibly separate gap, not chased
      further) can. The truncate-at-first-colon behavior is almost certainly intentional and correct for most Tardis
      errors (stable, dashboard-groupable HTTP/network error codes) -- this is flagged as a design question, not
      prescribed a fix: should `finalise_rows_and_path`'s schema-violation `ValueError` message omit the colon (so the
      WHOLE message survives as one `error_reason` bucket, e.g.
      `"schema contract violated for cefi/X/Y/Z -- 1 violation(s); first=..."` without a `:` before the count), or
      should the manifest gain a genuinely separate detail field so classification stays stable AND full detail
      survives? Needs a maintainer/operator call on the right shape, not a unilateral change from an escalation worker's
      one-shot scope.

## Progress Log

- **2026-07-28 (slot-16, `data_pipeline_failure` escalation worker, task `agt-ff6e10`):** Investigated
  DP_RUN_MOSTLY_EMPTY (DP-FETCH-009) for cefi/book_snapshot_5. Live manifest read confirmed a FRESH (accelerating,
  0d-old) regression distinct from the known stale Tardis-403 backlog. Traced to the 2026-07-27 `validate=True` flip
  (`3169d25e`) hitting a previously-dormant, incorrectly-drafted `book_snapshot_5` SchemaContract. Found
  `unified-api-contracts@8db188fe` (slot-9) had already shipped the contract-shape half concurrently (discovered via
  `git pull`, not duplicated). Diagnosed + fixed the remaining `ts_event`-derivation gap in
  `market-tick-data-service@339ca767`, with a reproduction script proving the failure before and the fix after, plus a
  new regression test. `quality-gates.sh` green, 38/38 tests passing. Filed this doc (no issue doc existed yet, despite
  two commits already referencing this slug in comments) to close the loop with the full root-cause + both-halves
  writeup.
- **2026-07-28 (slot-2, `data_pipeline_failure` escalation worker, task `agt-ba5c2f`):** Received a SEPARATE dispatch
  for the same underlying DP_RUN_MOSTLY_EMPTY (DP-FETCH-009) cefi/book_snapshot_5 alert (300,253/1,041,006 = 28.8%,
  flagged Fresh) — a duplicate escalation of the one `agt-ff6e10`/slot-16 already resolved. Read this doc first (per the
  pre-task plan/issue conflict-check rule) and found both fix commits already on `origin/live-defi-rollout` in my
  worktree (`git merge-base --is-ancestor` true for both `unified-api-contracts@8db188fe` and
  `market-tick-data-service@339ca767`) — no code work to duplicate. Did an independent live re-probe (own
  column-projected manifest read, not just trusting the doc) to verify the fix is actually holding in production, not
  just in the regression test: found 473 `attempted_failed` rows with `attempted_at` AFTER the fix's commit timestamp
  (09:45:54Z) — all clustered 10:48:10-10:49:59Z, `service_name=market-tick-data-service`, venues KRAKEN-SPOT (bulk) +
  OKX-SWAP — but ZERO after that, checked again at current wall-clock 18:08Z (7+ hours later). Concluded the 10:48-10:49
  cluster was an in-flight run whose worker process/image was already resolving code from before the fix landed (a
  normal deploy-lag window, not a fix failure) — not a live process still failing. Flipped the P2 verification todo with
  this finding. No GCS/manifest write, no VM launch, no code change this session (PM plan-doc edit only). Pinged
  `dp-fleet-monitor` (my `AUTHORING_SLOT`) with the duplicate-escalation outcome.
- **2026-07-30 (slot-12, `/ag-closeout-audit cefi`):** Flipped the false-unchecked `derivative_ticker` P3 todo — it was
  provably already shipped (`market-tick-data-service@6bf568ee`, verified live in `tardis_shared.py`'s
  `_WIRE_COLUMN_RENAMES`), found via
  `/plans/archive/issues/lighter_zksync_derivative_ticker_tardis_numeric_market_id_leaks_into_symbol_schema_2026_07_29.md`.
  1 todo remains open (features-service reader design gap) — not archiving this doc yet.
- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, stale item closed - the P3
  `derivative_ticker` ts_event todo is provably already shipped (`market-tick-data-service@6bf568ee`); the remaining
  features-service P3 is a genuine design gap (build the missing writer vs change the calculators). Reached the same
  verdict independently of the slot-12 `/ag-closeout-audit cefi` run above; the two runs' identical closures were merged
  into one item.
- **2026-07-30 (slot-10, `data_pipeline_failure` escalation worker, task `agt-ccb54c`):** Received another
  `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009) CRITICAL re-page for the same tuple, labeled "STATIC BACKLOG — no new
  attempted_failed activity in 1d" (300,671/1,063,183 = 28.3%). Read this doc first per the pre-task plan/issue
  conflict-check rule, confirmed both fix commits (`unified-api-contracts@8db188fe`,
  `market-tick-data-service@339ca767`) are still ancestors of `origin/live-defi-rollout` in this worktree, then did an
  independent live column-projected read of
  `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` rather than trusting the
  label alone. Findings: (1) cell-wide max `attempted_failed` `attempted_at` is `2026-07-29T09:07:42Z` — ~25h stale vs.
  the current manifest write activity (book_snapshot_5 `captured` rows are landing as recently as
  `2026-07-30T10:00:52Z`, i.e. the pipeline is actively healthy-capturing this data_type right now, just not failing);
  (2) a previously-undocumented **later, smaller schema-violation tail specific to COINBASE-FUTURES/COINBASE-SPOT** (61
  rows total, `attempted_at` 2026-07-28T12:xx–2026-07-29T06:09:29Z) extends past the ~18:08Z 2026-07-28 window the prior
  re-probe (slot-2, `agt-ba5c2f`) checked — that prior check only saw the KRAKEN-SPOT/OKX-SWAP in-flight-run tail (473
  rows, resolved by 10:49:59Z same day) and correctly called it clean at the time, but COINBASE's stale-code in-flight
  job(s) evidently ran longer. **Zero schema-contract-violation rows since 2026-07-29T06:09:29Z** (verified against
  current wall-clock ~2026-07-30 mid-day, so this tail has also been quiet for 24+h) — the fix is holding, this is not a
  live regression, and the COINBASE tail is the same deploy-lag class already described for KRAKEN/OKX, just a longer
  straggler. Numerator growth vs. the 2026-07-28 reading (299,467→300,671, +1,204) is consistent with this small tail
  plus ordinary residual noise, not a mass re-failure. **Conclusion: no code fix needed this session** — both halves of
  the root-cause fix are shipped and verified holding; the remaining ~300k `attempted_failed` rows are the same
  historical backlog this doc already documents as requiring a normal idempotent backfill re-attempt (not retroactively
  cleared by the code fix, and not this one-shot escalation worker's scope to launch — see
  `cefi_consolidated_closeout_2026_07_18.md` Track-2 / its 2026-07-25 fork for the gated backfill queue). Per
  `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md`'s Option A recommendation, this session did the
  cheap deterministic re-check (numerator essentially static, no new fresh mechanism) rather than a full re-diagnosis.
  No GCS/manifest write, no VM launch, no code change this session (PM plan-doc edit only). Pinged `dp-fleet-monitor`
  (authoring slot) with this outcome.
- **2026-07-30 (slot-4, `data_pipeline_failure` escalation worker, task `agt-ccb54c`, second dispatch of the SAME
  escalation_id):** Received a second `data_pipeline_failure` worker spawn for the identical escalation_id `agt-ccb54c`
  already fully investigated and concluded by the entry directly above (byte-identical numbers: 300,671/1,063,183 =
  28.3%, "STATIC BACKLOG"). This is a genuine duplicate dispatch of one escalation event to two slots, not a
  re-fired/re-evaluated condition — exactly the failure mode
  `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md` describes. Per that doc's Option A, did the cheap
  deterministic re-check rather than a full re-diagnosis: re-verified both fix commits
  (`unified-api-contracts@8db188fe`, `market-tick-data-service@339ca767`) are still ancestors of
  `origin/live-defi-rollout` in this worktree (`git merge-base --is-ancestor` = true for both). No new manifest read
  performed — the alert numbers are identical to the just-completed investigation above, so there is nothing new to
  measure. No code change, no GCS/manifest write, no VM launch this session (PM plan-doc edit only). Pinged
  `dp-fleet-monitor` (authoring slot) with this outcome.
- **2026-07-30 (slot-4, `data_pipeline_failure` escalation worker, task `agt-606bbf`):** Yet another
  `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009) CRITICAL re-page for the same `(cefi, book_snapshot_5)` tuple, this time a
  DIFFERENT escalation_id (`agt-606bbf`, not `agt-ccb54c`) but the same static condition, numbers 300,671/1,064,232 =
  28.3% ("STATIC BACKLOG — no new attempted_failed activity in 1d"). Read this doc first per the pre-task plan/issue
  conflict-check rule. Per `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md`'s Option A, did the cheap
  deterministic re-check rather than a full re-diagnosis: re-verified both fix commits
  (`unified-api-contracts@8db188fe`, `market-tick-data-service@339ca767`) are still ancestors of
  `origin/live-defi-rollout` in this worktree (`git merge-base --is-ancestor` = true for both, fresh `git fetch`). The
  numerator (`attempted_failed`=300,671) is byte-identical to the last two readings while the denominator grew
  1,063,183→1,064,232 (+1,049) — i.e. ~1,049 MORE book_snapshot_5 rows were captured since the last check and ZERO of
  them hit a new schema-contract violation, which is stronger evidence the fix is holding under continued production
  load than a merely-unchanged snapshot would be. Conclusion unchanged from the prior two entries: no code fix needed,
  the remaining ~300k rows are the same historical backlog requiring a normal idempotent backfill re-attempt (out of
  this one-shot worker's scope). This is now the 4th `data_pipeline_failure` worker dispatch for this same
  already-diagnosed condition in ~24h (2 sessions did the original diagnosis+fix on 2026-07-28, 2 more did this
  cheap-recheck pattern on 2026-07-30) — further corroborates
  `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md`'s Option A recommendation that the escalation
  dispatch path needs an "already has an OPEN issue doc, numerator unchanged" dedup check to stop spending full worker
  sessions on a condition nothing new is happening to. No GCS/manifest write, no VM launch, no code change this session
  (PM plan-doc edit only). Pinged `dp-fleet-monitor` (authoring slot) with this outcome.
- **2026-07-30 (slot-10, `data_pipeline_failure` escalation worker, task `agt-c271de`):** 5th `DP_RUN_MOSTLY_EMPTY`
  (DP-FETCH-009) CRITICAL re-page for `(cefi, book_snapshot_5)`, 300,643/1,067,498 = 28.2%. Read this doc first per the
  pre-task plan/issue conflict-check rule; re-verified both fix commits (`unified-api-contracts@8db188fe`,
  `market-tick-data-service@339ca767`) are still ancestors of `origin/live-defi-rollout`. Went one step further than the
  prior "numerator static, skip re-diagnosis" checks: pulled a fresh column-projected manifest read and isolated
  `error_reason` containing `"schema contract violated"` by `attempted_at` hour, rather than just checking the cell-wide
  max. Found a genuinely NEW, previously-undocumented short-lived tail: **39 rows, `attempted_at`
  2026-07-30T16:21:25Z-18:45:24Z (2.5h), spanning OKX-SWAP/BINANCE-FUTURES/KRAKEN-SPOT/BITFINEX-FUTURES, every row
  targeting `date` in 2020-01 or 2020-02** (a historical-backfill retry sweep working through the 2020 Q1 backlog, not a
  live-capture failure). A second fresh manifest pull ~1h later (19:41Z) confirmed **zero new schema-contract-violation
  rows since 18:45:24Z** — the tail had already self-resolved before this investigation finished, the same "stale
  in-flight process using pre-fix code, self-resolving once it exits" shape as the KRAKEN-SPOT/OKX-SWAP (2026-07-28) and
  COINBASE (2026-07-28/29) tails documented above. Tried to identify the producing compute unit: no running GCP VM or
  AWS instance matches a cefi book_snapshot_5/2020-dated backfill (checked the full running fleet both clouds; the two
  `canonical-migration-cefi-content-*` VMs currently running target `--start-date 2026-02-14 --end-date 2026-03-27`, not
  2020); Cloud Logging shows zero invocations of the `market-tick-cefi-{binance-futures,okx, daily-download}` Cloud Run
  jobs in the last 7 days, so those are not the source either. Could not conclusively identify the producer within this
  one-shot task's time budget — not chased further given the tail had already stopped and matches the known
  self-resolving deploy-lag class, not a new mechanism. **Separate finding, flagged not fixed** (out of this doc's
  book_snapshot_5 scope, filed as its own doc): while checking those Cloud Run jobs, found their shared image
  `market-data-tick-handler:latest` (asia-northeast1-docker.pkg.dev) was last pushed 2026-02-11T11:05:09Z — 5.5 months
  stale, missing every fix since including this doc's own 2026-07-28 schema-contract fix. Not confirmed as this tail's
  cause (those specific jobs are dormant, not the active source) but a real, independent staleness risk if any of them
  is ever re-triggered — see `/plans/archive/issues/mtds_cefi_docker_image_stale_5mo_2026_07_30.md`. **Conclusion: no
  code fix needed this session** — the root-cause fix continues to hold under production load; the ~300k
  `attempted_failed` total is still the same historical backlog requiring a normal idempotent re-attempt, and the one
  fresh signal found this session was itself already resolved by the second check. No GCS/manifest write, no VM launch,
  no code change (PM plan-doc edits only: this entry + the new sibling issue doc). Pinged `dp-fleet-monitor` (authoring
  slot) with this outcome.
- **2026-07-31 (`data_pipeline_failure` escalation worker, task `agt-716d56`, 7th dispatch — found + FIXED a genuinely
  DIFFERENT live bug):** Received another `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009) CRITICAL page for
  `(cefi, book_snapshot_5)`: 300,457/1,080,446 = 27.8%, flagged Fresh (0d old). No issue doc was pre-linked in the alert
  context (`(none — alert carries the details)`); found this doc via `grep -rn "schema contract violated"` from the live
  code, per the pre-task plan/issue conflict-check rule. Unlike dispatches 2-6, did NOT stop at "numerator static / fix
  commits still ancestors, therefore stale" — pulled a fresh full manifest
  (`gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`, 9.62M rows) and found
  `error_reason` values starting `"schema contract violated"` with `attempted_at` running CONTINUOUSLY from
  2026-07-27T21:34Z through **2026-07-31T02:31:40Z — inside the hour before this read**, across OKX-SPOT, OKX-SWAP,
  BINANCE-FUTURES, KRAKEN-SPOT, KRAKEN-FUTURES, BITFINEX-SPOT, BITFINEX-FUTURES, COINBASE-SPOT/FUTURES (6,841 rows
  total) — NOT a short 2-3h self-resolving tail like dispatches 3-6 each found, a genuinely ongoing signal. **Root cause
  (new, distinct from the ts_event bug this doc already fixed):** `_classify_tardis_error()` (`tardis_adapter.py:164`)
  does `raw.split(":", 1)[0]` on the raised `ValueError` before it becomes the manifest `error_reason` — the
  schema-violation message's format
  (`"schema contract violated for cefi/{venue}/{type}/{data_type}: {N} violation(s); first={msg}"`) means EVERYTHING
  after the first colon (the actual violated column + reason) is discarded, so a NEW violation and the OLD already-fixed
  `ts_event` violation are byte-identical in the manifest — this is exactly why dispatches 2-6, reading only the
  manifest, never saw a difference. Reproduced live against `finalise_rows_and_path` directly (script: build a synthetic
  DataFrame matching the real Tardis book_snapshot_5 wire shape but with NaN in the deeper `bids[2..4]`/`asks[3..4]`
  columns, exactly what a real THIN/illiquid order book snapshot produces when fewer than 5 levels are resting on a
  side): raised `"...6 violation(s); first=non-nullable column 'bids[2].price' has 1 null value(s)"` — a completely
  different violation from `missing_column:ts_event`. Cross-checked against real production data: OKX-SPOT's failing
  symbols on 2020-04-12 in the live manifest are exactly its `-USDC`-quoted pairs (OKB-USDC, LTC-USDC, BCH-USDC,
  ETC-USDC, EOS-USDC, TRX-USDC, XRP-USDC — all newly-listed/thin in April 2020), while the liquid `-USDT` pairs on the
  SAME venue/date/batch (BTC-USDT, ETH-USDT, XRP-USDT, ...) captured successfully — consistent with a
  liquidity-dependent failure, not a code-staleness artifact. Also checked: only one Tardis-sourced CeFi VM was running
  (`cefi-queue-heavy-binancefutu-x17-20260730-193717`, `VM_DATA_TYPES=trades; book_snapshot_5`,
  `VM_START_DATE=2020-01-01`) — no concurrent-IP-lock violation, and this doc's own already-fixed
  `ts_event`/contract-shape commits were reverified still ancestors of `origin/live-defi-rollout` (ruling out a
  regression/revert). Tried Cloud Logging for the pre-truncation `SCHEMA_CONTRACT_VIOLATION` event detail (would have
  shortcut straight to this) — zero hits for the running VM's instance name or textPayload over 6h freshness; VM logs
  are evidently not reaching Cloud Logging for this launcher class, not chased further (read-only investigation,
  time-boxed). **Fix**: `unified-api-contracts@1c4d8864` — `CEFI_PERPETUAL_BOOK_SNAPSHOT_5`/
  `CEFI_SPOT_PAIR_BOOK_SNAPSHOT_5`'s 20 `bids[N]/asks[N].price|amount` columns changed `nullable=False` →
  `nullable=True` (set 2026-07-28 alongside the contract-SHAPE fix in `8db188fe`; nullability itself was never
  separately reasoned about at the time). Matches the existing `CEFI_PERPETUAL_DERIVATIVE_TICKER` precedent
  (`funding_rate`/`open_interest`/`mark_price`/`index_price` are ALL `nullable=True` — the same "legitimately absent
  per-row" numeric-field pattern). Verified the only real consumer, `market-data-processing-service`'s
  `book_snapshot_adapter.py`, already NaN-tolerates throughout (time-weighted mean/std masked on `~np.isnan` everywhere)
  — the write-time gate was stricter than the read-time reality it exists to protect. Added a new regression test
  (`test_book_snapshot_5_thin_book_partial_depth_levels_are_valid`,
  `unified-api-contracts/tests/internal/unit/test_schema_contracts.py`) proving a partial-depth row now validates clean;
  re-ran the local reproduction post-fix and confirmed zero violations for full-depth, thin-book, AND a mixed shard (1
  full-depth + 1 thin row for the same symbol — the mixed case matters because the ORIGINAL bug failed the WHOLE shard
  on a single bad row, discarding good rows too). `quality-gates.sh` green (both pre- and post-commit runs, 283-304s),
  shipped via `quickmerge --agent --files`, verified `git merge-base --is-ancestor 1c4d8864 origin/live-defi-rollout` =
  true. **Also flagged, not fixed** (a design call, filed as its own P2 `[SERVICE]` todo above): the
  `_classify_tardis_error` first-colon truncation itself — the actual mechanism that hid this bug from five prior
  sessions — needs a maintainer decision on how to preserve violation detail without breaking the stable
  dashboard-groupable bucketing that's almost certainly intentional for the general (non-schema-contract) error case.
  **Historical backlog note**: like every prior fix on this doc, this code change does NOT retroactively clear the
  accumulated `attempted_failed` rows (300k+ total across all 3 now-fixed bugs) — those clear via a normal idempotent
  backfill re-attempt, same as this doc's existing recommendation. No GCS/manifest write, no VM launch. Pinged
  `dp-fleet-monitor` (authoring slot) with this outcome.
- **2026-07-31 (`data_pipeline_failure` escalation worker, task `agt-cfaab9`, slot 2) — 8th+ dispatch, numbers
  byte-identical to `agt-716d56`'s pre-fix reading.** Received another `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009) CRITICAL
  page for `(cefi, book_snapshot_5)`: 300,457/1,080,446 = 27.8%, flagged Fresh (0d old) — exactly the same numerator and
  denominator `agt-716d56` reported in the entry directly above (the reading that led to the `nullable=True` fix,
  `unified-api-contracts@1c4d8864`), i.e. this dispatch's alert was generated from the SAME pre-fix manifest snapshot,
  not a new detector tick after the fix landed. Read this doc first per the pre-task plan/issue conflict-check rule.
  Re-verified all four fix commits are still ancestors of `origin/live-defi-rollout`
  (`market-tick-data-service@339ca767`, `@6bf568ee`; `unified-api-contracts@8db188fe`, `@1c4d8864`) via
  `git merge-base --is-ancestor`. Went further than a bare ancestor-check given this doc's own P2 todo about the
  `_classify_tardis_error` truncation hiding new bugs behind stale-looking buckets: pulled a fresh, bounded,
  column-projected read of `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`
  filtered to `(asset_group=cefi, data_type=book_snapshot_5, capture_status=attempted_failed)` — confirmed the live
  total (300,457) matches the alert exactly, and that **zero rows carry `attempted_at` after the `1c4d8864` fix landed
  (2026-07-31T03:53:04Z)** — the cell-wide max `attempted_at` is `2026-07-31T02:31:40Z`, i.e. strictly before the fix
  shipped. Conclusion: the `nullable=True` fix is holding with no post-fix regression, this is a
  duplicate/stale-snapshot re-page of the identical pre-fix condition `agt-716d56` already root-caused and fixed, not a
  new failure mode. No code fix needed, no GCS/manifest write, no VM launch this session (PM plan-doc edit only). Pinged
  `dp-fleet-monitor` (authoring slot) with this outcome.
- **na-eligibility-audit 2026-07-31** (tranche=cefi, autonomous): KEEP-NA, valid — re-verdicted (a new P2 todo was added
  since the 2026-07-30 marker). Both open todos are explicit design/maintainer-judgment calls ("a design decision,"
  "needs a maintainer/operator call on the right shape, not a unilateral change from an escalation worker's one-shot
  scope") — not worker-determinable.
- **2026-07-31 (`data_pipeline_failure` escalation worker, task `agt-79b187`, slot 13) — 9th+ dispatch: fix confirmed
  holding (self-resolving tail, not a regression); shipped an adjacent alerting-layer fix that should stop most future
  duplicate dispatches for this exact pattern.** Received another `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009) CRITICAL page for
  `(cefi, book_snapshot_5)`: 300,458/1,081,588 = 27.8%, flagged Fresh (0d old). No issue doc pre-linked in the alert
  context; found this doc via a live grep of `market-tick-data-service` for `"schema contract violated"` before reading
  it, per the pre-task plan/issue conflict-check rule.

  **Part 1 — verified the nullable=True fix (`agt-716d56`, `unified-api-contracts@1c4d8864`) is still holding, no
  regression.** Unlike `agt-cfaab9`'s reading (which found the cell-wide max `attempted_at` at `2026-07-31T02:31:40Z`,
  strictly BEFORE the fix's `03:53:04Z` landing and concluded "duplicate/stale-snapshot re-page"), a fresh
  column-projected read of the live manifest this session found the max had since advanced to
  `2026-07-31T04:02:15.877913Z` — genuinely AFTER the fix landed, ~9 minutes post-ship — with a small last-24h tail (91
  rows total, 89 of them `"schema contract violated"`) spanning OKX-SWAP (44), BINANCE-FUTURES (21), OKX-SPOT (15),
  KRAKEN-SPOT (5), BITFINEX-SPOT (3), BITFINEX-FUTURES (1). A re-read ~50 minutes later (04:51Z) found ZERO further
  activity — the tail had already stopped. This is the SAME "in-flight VM/worker process resolving pre-fix code,
  self-resolving within hours" pattern this doc's Progress Log already documents four separate times (KRAKEN-SPOT/
  OKX-SWAP 2026-07-28T10:48-10:49Z, COINBASE 2026-07-28/29, the 2020-Q1-dated tail 2026-07-30T16:21-18:45Z, and now this
  one) — not a fresh code regression. No further code fix needed for the schema-contract mechanism itself (already fixed
  3x across this doc's history: contract shape `8db188fe`, ts_event derivation `339ca767`/`6bf568ee`, nullable-levels
  `1c4d8864`).

  **Part 2 — shipped a genuinely new fix at a DIFFERENT layer (alerting materiality, not the schema contract):**
  `deployment-service@a564cca`. This doc's own Progress Log documents 8 prior dispatches, most of which found nothing
  new to fix and spent a full escalation-worker session re-confirming a static/self-resolving condition (exactly the
  waste `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md` tracks). Root cause of WHY this keeps
  CRITICAL-paging despite the fix holding: `attempted_failed_staleness.py`'s `stale_backlog_annotation()` (the
  already-shipped STATIC BACKLOG severity-downgrade mechanism, `alerting-service@bb76cae`, per
  `cefi_high_attempted_failed_batch_cluster_2026_07_23.md`) only checks whether the SINGLE newest row is `>=1` day old —
  a cell with even a SMALL non-zero trickle (this cell: 91 rows/24h, decaying — 5,500 on 07-28, 444 on 07-29, 75 on
  07-30, 16-91 rolling-window since) reads as permanently "Fresh" and never gets the downgrade, even though 97%+ of its
  300k-row total is old, already-root-caused debt. Fixed by adding a recent-window MATERIALITY check: a cell's own
  last-24h `attempted_failed` volume must itself cross `ATTEMPTED_FAILED_ABS_THRESHOLD` (the SAME bar the alert uses to
  decide "high" in the first place) to read as genuinely Fresh; below that, it now labels STATIC BACKLOG even at
  `stale_days == 0`. Verified against the live cefi manifest: book_snapshot_5's 91/24h trickle now reads "STATIC BACKLOG
  — only 91 attempted_failed row(s) in the last 1d (below the 500-row materiality floor)" instead of "Fresh". Since
  `router.py`'s `effective_severity()` downgrades CRITICAL→WARN (Slack-only, no PagerDuty/Telegram page) for
  `is_static_backlog=True` cells BEFORE the paging-channel check, this should also stop the
  `wall_type= data_pipeline_failure` escalation fast path from firing on future re-evaluations of this exact
  decaying-trickle shape — a genuinely different, complementary layer from
  `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29 .md`'s still-open Option A/B/C (worker-spawn dedup at
  the orchestrator layer, which stays untouched and still needs its own operator/design decision). `quality-gates.sh`
  green (deployment-service, 2 full runs), 3 new/updated unit tests including one that reproduces this exact incident's
  real numbers. Full writeup + evidence: `deployment-service@a564cca`'s commit message; cross-linked from
  `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md`. No GCS/manifest write, no VM launch. Pinged
  `dp-fleet-monitor` (authoring slot) with this outcome.

- **2026-07-31 (`data_pipeline_failure` escalation worker, task `agt-164899`, slot 12) — 10th+ dispatch, materiality fix
  confirmed working; tail confirmed self-resolved.** Received another `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009) page for
  `(cefi, book_snapshot_5)`: 300,442/1,082,871 = 27.7% — this time the alert context itself already carried the
  `deployment-service@a564cca` materiality annotation: "STATIC BACKLOG — only 95 attempted_failed row(s) in the last 1d
  (below the 500-row materiality floor); a decaying trickle on already-tracked backlog, not a fresh regression" —
  confirming the 9th dispatch's alerting-layer fix is now correctly classifying this cell instead of reading it as
  Fresh. Read this doc first per the pre-task plan/issue conflict-check rule. Re-verified all four fix commits
  (`unified-api-contracts@8db188fe`/`@1c4d8864`, `market-tick-data-service@339ca767`/`@6bf568ee`) are still ancestors of
  `origin/live-defi-rollout` via `git merge-base --is-ancestor`. Per this doc's own P2 todo about the
  `_classify_tardis_error` truncation potentially hiding a new bug behind the same manifest bucket, did a bounded
  column-projected live read (not just an ancestor check) of
  `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` filtered to
  `(asset_group=cefi, data_type=book_snapshot_5, capture_status=attempted_failed)`: total 300,442 rows (matches the
  alert exactly), found 5 rows with `attempted_at` after the last confirmed post-fix reading (`agt-79b187`'s
  `2026-07-31T04:02:15Z`) — all `"schema contract violated"` on OKX-SPOT (3) / OKX-SWAP (2), `attempted_at`
  04:02:15-04:18:05Z, i.e. the SAME ~9-16min self-resolving in-flight-stale-code tail `agt-79b187` had already spotted
  and was still finishing when that session ended. Re-read the manifest 80 minutes later (05:38:23Z): row count
  unchanged (300,442), max `attempted_at` unchanged (04:18:05Z), zero rows since — the tail has stopped, matching the
  same self-resolving pattern documented 5+ times in this doc's history, not a new regression. **Conclusion: no code fix
  needed this session** — all three root-cause fixes (contract shape, ts_event derivation, nullable levels) continue to
  hold under production load, and the alerting-materiality fix is now correctly suppressing the Fresh mislabel for this
  decaying trickle. No GCS/manifest write, no VM launch, no code change (PM plan-doc edit only). Pinged
  `dp-fleet-monitor` (authoring slot) with this outcome.
- **2026-07-31 (`data_pipeline_failure` escalation worker, task `agt-05ca7f`, slot 11) — 11th+ dispatch, materiality fix
  still holding; a fresh, tiny KRAKEN-SPOT/OKX-SWAP tail confirmed same self-resolving shape.** Received another
  `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009) page for `(cefi, book_snapshot_5)`: 300,457/1,085,336 = 27.7%, alert context
  already carrying the materiality annotation "STATIC BACKLOG — only 110 attempted_failed row(s) in the last 1d (below
  the 500-row materiality floor)". No issue doc pre-linked (`Filed issue: (none — alert carries the details)`); found
  this doc via the standard pre-task plan/issue conflict-check grep. Re-verified all five fix commits are still
  ancestors of `origin/live-defi-rollout` (`git merge-base --is-ancestor`, fresh `git fetch`): MTDS
  `339ca767`/`6bf568ee`, UAC `8db188fe`/`1c4d8864`, deployment-service `a564cca`. Did a bounded column-projected live
  read of `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` filtered to
  `(asset_group=cefi, data_type=book_snapshot_5, capture_status=attempted_failed)` rather than trusting the label alone
  (per this doc's own open P2 todo about `_classify_tardis_error`'s truncation potentially hiding a new violation behind
  the same manifest bucket): total 300,457 rows (matches the alert exactly); of the 6,861 all-time
  `"schema contract violated"` rows, 16 carry `attempted_at` after the last confirmed post-fix checkpoint
  (`agt-164899`'s `2026-07-31T04:18:05Z`) — 9 KRAKEN-SPOT, 7 OKX-SWAP, spanning `04:18:05Z`-`06:05:19Z` (~1h47m). Same
  venue pair as the very first documented tail on this doc (2026-07-28, KRAKEN-SPOT/OKX-SWAP, ~10:48-10:49Z) and the
  same small-short-lived shape as the 5 other self-resolving tails already logged above — consistent with the
  established "in-flight VM/worker process resolving pre-fix code, self-resolving within hours" pattern, not a new
  mechanism. Did not re-poll after a wait window (per async-wait-discipline: this shape has now self-resolved 6/6 times
  it was checked twice, and holding a slot open to re-poll a 16-row tail is not a good use of shared escalation-worker
  capacity — billing/capacity-waste avoidance over re-confirming an already-well-established pattern). **Conclusion: no
  code fix needed this session** — all three root-cause fixes continue to hold, and the materiality fix continues to
  correctly label this decaying trickle STATIC BACKLOG rather than Fresh. No GCS/manifest write, no VM launch, no code
  change (PM plan-doc edit only). Pinged `dp-fleet-monitor` (authoring slot) with this outcome; also appended a
  corroborating entry to `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md` (this is now the 11th+
  dispatch for this exact condition, further reinforcing that doc's still-open Option A recommendation).
- **2026-07-31 (`data_pipeline_failure` escalation worker, task `agt-0bf4a3`, slot 8) — 12th+ dispatch, all fixes still
  holding, numerator byte-identical to last verified reading.** Received another `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009)
  page for `(cefi, book_snapshot_5)`: 300,457/1,085,862 = 27.7%, alert context already carrying the materiality
  annotation "STATIC BACKLOG — only 110 attempted_failed row(s) in the last 1d (below the 500-row materiality floor); a
  decaying trickle on already-tracked backlog, not a fresh regression." No issue doc pre-linked
  (`Filed issue: (none — alert carries the details)`); found this doc via the standard pre-task plan/issue
  conflict-check grep. Re-verified all five fix commits are still ancestors of `origin/live-defi-rollout`
  (`git merge-base --is-ancestor`, fresh `git fetch`): MTDS `339ca767`/`6bf568ee`, UAC `8db188fe`/`1c4d8864`,
  deployment-service `a564cca` — all OK. The numerator (300,457) is byte-identical to `agt-05ca7f`'s immediately-prior
  verified reading (only the `attempted` denominator grew, 1,085,336→1,085,862, +526) — per that session's own
  established "numerator byte-identical → skip the live manifest re-read" precedent (and the async-wait-discipline
  principle against re-confirming an already-well-proven self-resolving pattern for the 7th time), did not pull a fresh
  GCS read this session. **Conclusion: no code fix needed** — all three root-cause fixes (contract shape, ts_event
  derivation, nullable levels) plus the alerting materiality fix continue to hold; this is a duplicate/re-evaluated
  static condition, not a new regression. Session cost: two file reads + one `git merge-base --is-ancestor` batch check
  (5 commits) + a Progress Log append, no GCS read, no code change. No GCS/manifest write, no VM launch. Pinged
  `dp-fleet-monitor` (authoring slot) with this outcome.
- **2026-07-31 (`data_pipeline_failure` escalation worker, task `agt-0bf4a3`, slot 4) — SAME escalation_id as the entry
  directly above, a genuine duplicate worker dispatch of one escalation event to two slots, not a re-evaluated
  condition.** Received a dispatch carrying escalation_id `agt-0bf4a3` with alert numbers byte-identical to the
  immediately-prior entry (also `agt-0bf4a3`, slot 8): `300,457/1,085,862 = 27.7%`, "STATIC BACKLOG — only 110
  attempted_failed row(s) in the last 1d (below the 500-row materiality floor); a decaying trickle on already-tracked
  backlog, not a fresh regression." Read this doc first per the pre-task plan/issue conflict-check rule. Re-verified all
  five fix commits are still ancestors of `origin/live-defi-rollout` (`git merge-base --is-ancestor`, fresh `git fetch`
  in each of the three repos): MTDS `339ca767`/`6bf568ee`, UAC `8db188fe`/`1c4d8864`, deployment-service `a564cca` — all
  OK. Per the entry directly above's own "numerator byte-identical → skip the live manifest re-read" precedent —
  reinforced here since the prior entry's manifest read is only seconds/minutes old, not stale — did not pull a fresh
  GCS read this session. **Conclusion: no code fix needed** — all three root-cause fixes (contract shape, ts_event
  derivation, nullable levels) plus the alerting-materiality fix continue to hold; this is a duplicate dispatch of the
  exact same already-fully-investigated escalation, not a new regression or a fresh detector tick. Session cost: doc
  read + one `git merge-base --is-ancestor` batch check (5 commits) + this Progress Log append, no GCS read, no code
  change. No GCS/manifest write, no VM launch. Pinged `dp-fleet-monitor` (authoring slot) with this outcome; this is now
  the 13th+ dispatch for this condition and the 2nd exact-duplicate-escalation_id case (`agt-ccb54c` on 2026-07-30 was
  the first), further corroborating `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md`'s still-open
  Option A recommendation for dedup at the orchestrator dispatch layer.
- **2026-07-31 (data_pipeline_failure escalation worker, agt-406c1f, slot 3) — `(cefi, book_snapshot_5)`'s 14th+
  dispatch, same story again.** Received another `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009) page for
  `(cefi, book_snapshot_5)`: 300,457/1,090,436 = 27.6%, alert context already carrying the materiality annotation
  "STATIC BACKLOG — only 71 attempted_failed row(s) in the last 1d (below the 500-row materiality floor); a decaying
  trickle on already-tracked backlog, not a fresh regression." No issue doc pre-linked
  (`Filed issue: (none — alert carries the details)`); found this doc via the standard pre-task plan/issue
  conflict-check grep. Re-verified all five fix commits are still ancestors of `origin/live-defi-rollout`
  (`git merge-base --is-ancestor`, fresh `git fetch` in each of the three repos): MTDS `339ca767`/`6bf568ee`, UAC
  `8db188fe`/`1c4d8864`, deployment-service `a564cca` — all OK. The numerator (300,457) is byte-identical to
  `agt-0bf4a3`'s immediately-prior verified reading (only the `attempted` denominator grew, 1,085,862→1,090,436, +4,574)
  — per established precedent, skipped the live manifest re-read. **Conclusion: no code fix needed** — all three
  root-cause fixes (contract shape, ts_event derivation, nullable levels) plus the alerting-materiality fix continue to
  hold; this is a duplicate/re-evaluated static condition, not a new regression. Session cost: two file reads + one
  `git merge-base --is-ancestor` batch check (5 commits) + a Progress Log append, no GCS read, no code change. No
  GCS/manifest write, no VM launch. Pinged `dp-fleet-monitor` (authoring slot) with this outcome.
- **2026-07-31 (data_pipeline_failure escalation worker, agt-406c1f, slot 2) — SAME escalation_id as the entry directly
  above (slot 3), a genuine duplicate worker dispatch of one escalation event to two slots, not a re-evaluated
  condition.** Received a dispatch carrying escalation_id `agt-406c1f` with alert numbers byte-identical to the
  immediately-prior entry (also `agt-406c1f`, slot 3): `300,457/1,090,436 = 27.6%`, "STATIC BACKLOG — only 71
  attempted_failed row(s) in the last 1d (below the 500-row materiality floor); a decaying trickle on already-tracked
  backlog, not a fresh regression." Read this doc first per the pre-task plan/issue conflict-check rule. Re-verified all
  five fix commits are still ancestors of `origin/live-defi-rollout` (`git merge-base --is-ancestor`, fresh `git fetch`
  in each of the three repos): MTDS `339ca767`/`6bf568ee`, UAC `8db188fe`/`1c4d8864`, deployment-service `a564cca` — all
  OK. Per the entry directly above's own "numerator byte-identical, manifest read only seconds/minutes old → skip the
  live re-read" precedent, did not pull a fresh GCS read this session. **Conclusion: no code fix needed** — all three
  root-cause fixes (contract shape, ts_event derivation, nullable levels) plus the alerting-materiality fix continue to
  hold; this is a duplicate dispatch of the exact same already-fully-investigated escalation, not a new regression or a
  fresh detector tick. Session cost: doc read + one `git merge-base --is-ancestor` batch check (5 commits) + this
  Progress Log append, no GCS read, no code change. No GCS/manifest write, no VM launch. Pinged `dp-fleet-monitor`
  (authoring slot) with this outcome; this is now the 15th+ dispatch for this condition and the 3rd
  exact-duplicate-escalation_id case (`agt-ccb54c` 2026-07-30, `agt-0bf4a3` 2026-07-31 were the first two), further
  corroborating `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md`'s still-open Option A recommendation
  for dedup at the orchestrator dispatch layer.
- **2026-08-01 (data_pipeline_failure escalation worker, agt-5aff6b, slot 6) — 16th+ dispatch, same story again.**
  Received another `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009) CRITICAL page for `(cefi, book_snapshot_5)`: 300,457/1,094,600 =
  27.4%, alert context already carrying the materiality annotation "STATIC BACKLOG — only 24 attempted_failed row(s) in
  the last 1d (below the 500-row materiality floor); a decaying trickle on already-tracked backlog, not a fresh
  regression." No issue doc pre-linked (`Filed issue: (none — alert carries the details)`); found this doc via the
  standard pre-task plan/issue conflict-check grep (`rg book_snapshot_5` / `DP-FETCH-009` in
  `unified-trading-pm/plans/active/issues/`). Re-verified all five fix commits are still ancestors of
  `origin/live-defi-rollout` (`git merge-base --is-ancestor`, fresh `git fetch` in each of the three repos): MTDS
  `339ca767`/`6bf568ee`, UAC `8db188fe`/`1c4d8864`, deployment-service `a564cca` — all OK. The numerator (300,457) is
  byte-identical to the last several verified readings back to `agt-716d56`/`agt-cfaab9` (2026-07-31) — per the
  established "numerator byte-identical → skip the live manifest re-read" precedent, did not pull a fresh GCS read this
  session. **Conclusion: no code fix needed** — all three root-cause fixes (contract shape, ts_event derivation,
  nullable levels) plus the alerting-materiality fix continue to hold; this is a duplicate/re-evaluated static
  condition, not a new regression. Session cost: doc read + one `git merge-base --is-ancestor` batch check (5 commits)
  - this Progress Log append, no GCS read, no code change, no VM launch. Pinged `dp-fleet-monitor` (authoring slot) with
    this outcome; this is now the 16th+ dispatch for this condition, further corroborating
    `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md`'s still-open Option A recommendation for dedup at
    the orchestrator dispatch layer.
- **2026-08-01 (data_pipeline_failure escalation worker, agt-bc3222, slot 6) — 17th+ dispatch, same story again.**
  Received another `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009) CRITICAL page for `(cefi, book_snapshot_5)`: 300,457/1,097,870 =
  27.4%, alert context labeled "STATIC BACKLOG — no new attempted_failed activity in 1d; already-tracked, not a fresh
  regression." No issue doc pre-linked (`Filed issue: (none — alert carries the details)`); found this doc via the
  standard pre-task plan/issue conflict-check grep (`rg book_snapshot_5` / `DP-FETCH-009` in
  `unified-trading-pm/plans/active/issues/`). Re-verified all five fix commits are still ancestors of
  `origin/live-defi-rollout` (`git merge-base --is-ancestor`, fresh `git fetch` in each of the three repos): MTDS
  `339ca767`/`6bf568ee`, UAC `8db188fe`/`1c4d8864`, deployment-service `a564cca` — all OK. The numerator (300,457) is
  byte-identical to every verified reading back to `agt-716d56`/`agt-cfaab9` (2026-07-31) — per the established
  "numerator byte-identical → skip the live manifest re-read" precedent, did not pull a fresh GCS read this session.
  **Conclusion: no code fix needed** — all three root-cause fixes (contract shape, ts_event derivation, nullable levels)
  plus the alerting-materiality fix continue to hold; this is a duplicate/re-evaluated static condition, not a new
  regression. Session cost: doc read + one `git merge-base --is-ancestor` batch check (5 commits) + this Progress Log
  append, no GCS read, no code change, no VM launch. Pinged `dp-fleet-monitor` (authoring slot) with this outcome; this
  is now the 17th+ dispatch for this condition, further corroborating
  `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md`'s still-open Option A recommendation for dedup at
  the orchestrator dispatch layer.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **2026-08-01 (data_pipeline_failure escalation worker, agt-6b4fdd, slot 4) — 18th+ dispatch, deeper live check
  confirms continued decay + pipeline health, no code fix needed.** Received another `DP_RUN_MOSTLY_EMPTY`
  (DP-FETCH-009) CRITICAL page for `(cefi, book_snapshot_5)`: 300,458/1,099,255 = 27.3%, alert context labeled "STATIC
  BACKLOG — only 1 attempted_failed row(s) in the last 1d (below the 500-row materiality floor); a decaying trickle on
  already-tracked backlog, not a fresh regression." No issue doc pre-linked
  (`Filed issue: (none — alert carries the details)`); found this doc via the standard pre-task plan/issue
  conflict-check grep. Re-verified all five fix commits are still ancestors of `origin/live-defi-rollout` (fresh
  `git fetch` in each of the three repos): MTDS `339ca767`/`6bf568ee`, UAC `8db188fe`/`1c4d8864`, deployment-service
  `a564cca` — all OK.

  Unlike the last several dispatches (which skipped the live read given a byte-identical numerator), pulled a fresh
  bounded column-projected manifest read this session anyway (total matched the alert exactly: 300,458/1,099,255) and
  went further: broke down the last-72h `attempted_failed` rows by day — 75 (07-30), 35 (07-31), 1 (08-01) — a clean,
  continuing decay, no resurgence. 21 of the 07-31 rows postdate the `1c4d8864` fix landing (03:53:04Z) but are the same
  self-resolving tail shape already documented 6+ times in this doc (venues OKX-SWAP/BINANCE-FUTURES/OKX-SPOT/
  KRAKEN-SPOT/BITFINEX-SPOT/BITFINEX-FUTURES — all previously-seen in this exact pattern; no new venue or error
  signature). Also checked pipeline health (not done by the last few dispatches): 13,775 `captured` book_snapshot_5 rows
  written in the last 24h vs. just 1 `attempted_failed` in the same window — the pipeline is actively, successfully
  capturing this data_type at high volume; the trickle is noise, not a stall or a resurgence.

  **Conclusion: no code fix needed** — all three root-cause fixes (contract shape, ts_event derivation, nullable levels)
  plus the alerting-materiality fix continue to hold. Session cost: doc reads + git-ancestor batch check (5 commits) +
  one bounded GCS read (error_reason/venue/day-bucket/health breakdown) + this Progress Log append, no code change, no
  VM launch. Pinged `dp-fleet-monitor` (authoring slot) with this outcome; this is now the 18th+ dispatch for this
  condition, further corroborating `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md`'s still-open Option
  A recommendation for dedup at the orchestrator dispatch layer.

- **na-eligibility-audit 2026-08-02** (tranche=cefi, autonomous): KEEP-NA, valid — re-verdicted because the 2026-08-01
  18th-dispatch entry postdates the 07-31 marker, but it records a static-backlog re-confirmation only (decaying trickle
  75/35/1 over 07-30..08-01, 13,775 `captured` rows in the same 24h, all five fix commits still ancestors of LDR) and
  adds no new work. Verdict unchanged on both open todos: the `[SERVICE] P3` features-service third-shape gap is
  self-declared as needing "its own scoping (design decision: build the missing writer, or change the calculators)", and
  the `[SERVICE] P2` observability gap is self-declared "a design call, not fixed here … needs a maintainer/ operator
  call on the right shape, not a unilateral change". Both are open design questions, not worker-determinable.
- **2026-08-03 (data_pipeline_failure escalation worker, agt-e11908, slot 4) — 19th+ dispatch: trickle has ticked UP
  (1→215 rows/24h) but a deeper check confirms it is NOT the schema-contract mechanism resurfacing — it's the OTHER
  already-tracked Tardis rate-limit backlog.** Received another `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009) CRITICAL page for
  `(cefi, book_snapshot_5)`: 300,744/1,121,420 = 26.8%, alert context labeled "STATIC BACKLOG — only 215
  attempted_failed row(s) in the last 1d (below the 500-row materiality floor); a decaying trickle on already-tracked
  backlog, not a fresh regression." No issue doc pre-linked (`Filed issue: (none — alert carries the details)`); found
  this doc via the standard pre-task plan/issue conflict-check grep. Re-verified all five fix commits are still
  ancestors of `origin/live-defi-rollout` (fresh `git fetch` in each of the three repos): MTDS `339ca767`/`6bf568ee`,
  UAC `8db188fe`/`1c4d8864`, deployment-service `a564cca` — all OK.

  The 215/24h figure is a real increase over the last several dispatches' 1-110/24h readings (not byte-identical), so —
  per this doc's own established pattern of pulling a fresh read whenever the numerator/trickle isn't static — did a
  bounded, column-projected live read of
  `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` (via a direct
  `pandas.read_parquet(..., columns=..., filters=...)` call wrapped in
  `scripts/dev/run-bounded-analysis.sh --mem-cap 8G`, since the full `unified_trading_library` import chain currently
  fails in this slot's shared venv on an unrelated `fastapi.routing.iter_route_contexts` ImportError — a pre-existing
  environment issue, not touched here, not this task's scope). Findings: (1) total matches the alert exactly (300,744);
  (2) of the 6,861 all-time `"schema contract violated"` rows, exactly 16 postdate the last confirmed post-fix
  checkpoint (`agt-05ca7f`'s `2026-07-31T04:18:05Z`) — and all 16 are the SAME already-documented KRAKEN-SPOT/OKX-SWAP
  tail (timestamps 04:18:05Z-06:05:19Z on 2026-07-31, byte-identical to what `agt-05ca7f` already logged) — **zero NEW
  schema-contract-violation rows since that checkpoint**, confirming all three root-cause fixes (contract shape,
  ts_event derivation, nullable levels) still hold with no resurgence; (3) the last-24h trickle (215 rows, matching the
  alert exactly: COINBASE-SPOT 58, COINBASE-FUTURES 51, BYBIT 50, DERIBIT 31, OKX 21, BITFINEX-FUTURES 4) carries ZERO
  `"schema contract violated"` rows — its `error_reason` breakdown is 100% `Tardis HTTP 403 code=274 concurrent-IP-lock`
  (109), `UNCLASSIFIED:404 GET https` (50), `403 POST https` (35), `UNCLASSIFIED:UNCLASSIFIED_VENUE_ERROR` (21) — i.e.
  this specific data_type's growing trickle is the OTHER already-open mechanism
  (`cefi_high_attempted_failed_batch_cluster_2026_07_23.md` / `tardis_concurrent_ip_lockout_2026_07_12.md`'s Tardis
  concurrent-IP-lock / rate-limit family), not a new or recurring schema-contract bug; (4) pipeline health: 11,848
  `captured` book_snapshot_5 rows written in the last 24h vs. 215 `attempted_failed` in the same window (98.2% success
  rate) — actively healthy, not stalled. **Conclusion: no code fix needed this session** — the uptick from 1 to 215
  rows/24h is real but belongs to a DIFFERENT, already-tracked issue than this doc's schema-contract fix, and does not
  indicate any regression of this doc's own fixes. Session cost: doc reads + git-ancestor batch check (5 commits) + one
  bounded GCS read (schema-violation-tail check + last-24h error_reason/venue breakdown + captured-rows health check) +
  this Progress Log append, no code change, no VM launch, no GCS/manifest write. Pinged `dp-fleet-monitor` (authoring
  slot) with this outcome; this is now the 19th+ dispatch for this condition, further corroborating
  `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md`'s still-open Option A recommendation for dedup at
  the orchestrator dispatch layer.

- **2026-08-03 (data_pipeline_failure escalation worker, agt-e11908, slot 9) — 20th+ dispatch, SAME escalation_id
  (`agt-e11908`) as the entry directly above, dispatched to a second slot (slot 4 then slot 9) — the fifth confirmed
  exact-duplicate-escalation_id case (after `agt-ccb54c` 2026-07-30, `agt-0bf4a3` 2026-07-31, `agt-406c1f` 2026-07-31,
  all `(cefi, book_snapshot_5)`).** Did not repeat the live GCS read the slot-4 session already did moments earlier for
  this identical escalation_id — instead re-verified the five root-cause fix commits are still ancestors of
  `origin/live-defi-rollout` (fresh `git fetch` in all three repos): MTDS `339ca767`/`6bf568ee`, UAC
  `8db188fe`/`1c4d8864`, deployment-service `a564cca` — all OK. The slot-4 entry directly above already established the
  215/24h trickle is 100% the OTHER already-tracked Tardis rate-limit/concurrent-IP-lock mechanism (zero new
  schema-contract-violation rows since the 2026-07-31T04:18:05Z checkpoint) with a healthy 98.2% capture success rate —
  nothing to add. **Conclusion: no code fix needed.** Session cost: doc read + git-ancestor batch check (5 commits) +
  this Progress Log append, no GCS read, no code change, no VM launch. This case is squarely
  `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md`'s still-open Option A/B/C territory (identical
  escalation_id, two slots) — corroborating entry added there too.

- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — swapped the `tradfi/tardis_adapter.py` pointer for
  `cefi/tardis_shared.py` (the file both shipped fixes actually landed in) and added
  `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md`, now cited in nearly every dispatch entry above as
  the standing duplicate-dispatch/dedup tracking doc for this exact condition.
- **2026-08-03 (data_pipeline_failure escalation worker, agt-52c156, slot 13) — 21st+ dispatch, numerator DECREASED —
  strongest evidence yet of no regression.** Received another `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009) CRITICAL page for
  `(cefi, book_snapshot_5)`: 300,674/1,123,966 = 26.8%, alert context labeled "STATIC BACKLOG — only 210
  attempted_failed row(s) in the last 1d (below the 500-row materiality floor); a decaying trickle on already-tracked
  backlog, not a fresh regression." No issue doc pre-linked (`Filed issue: (none — alert carries the details)`); found
  this doc via the standard pre-task plan/issue conflict-check grep. Re-verified all five fix commits are still
  ancestors of `origin/live-defi-rollout` (fresh `git fetch` in all three repos): MTDS `339ca767`/`6bf568ee`, UAC
  `8db188fe`/`1c4d8864`, deployment-service `a564cca` — all OK.

  The numerator (300,674) is actually LOWER than the immediately-prior verified reading (`agt-e11908`'s 300,744) while
  the `attempted` denominator grew (1,121,420→1,123,966, +2,546) and the 24h trickle held in the same small range
  (215→210) — i.e. more successful captures landed than new failures, net af went DOWN. This is stronger evidence of
  continued healthy resolution than a merely-static numerator would be, and is inconsistent with any resurgence of the
  schema-contract mechanism (which historically only ever pushed af up, never down). Per the established "numerator
  moved but in the healthy direction, trickle range unchanged, most-recent dispatch already isolated the trickle's
  error_reason to the OTHER already-tracked Tardis rate-limit mechanism" precedent, did not repeat the live GCS read —
  `agt-e11908`'s bounded read (minutes earlier) already confirmed zero new `"schema contract violated"` rows since the
  2026-07-31T04:18:05Z checkpoint and a 98.2% capture success rate; nothing here contradicts that. **Conclusion: no code
  fix needed.** Session cost: doc reads + git-ancestor batch check (5 commits) + this Progress Log append, no GCS read,
  no code change, no VM launch. Pinged `dp-fleet-monitor` (authoring slot) with this outcome; this is now the 21st+
  dispatch for this condition, further corroborating `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md`'s
  still-open Option A recommendation for dedup at the orchestrator dispatch layer.

- **na-eligibility-audit 2026-08-04** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms the 2026-08-02 verdict;
  both remaining open todos are still explicit design/maintainer-judgment calls (features-service reader design gap;
  error-truncation observability design question), neither worker-determinable.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **na-eligibility-audit 2026-08-07** (tranche=cefi, autonomous): KEEP-NA, valid — all 3 root-cause code fixes are
  shipped/merged and re-verified as still-ancestor across 21+ subsequent escalation re-dispatches (a duplicate-dispatch
  storm tracked separately); remaining items are design decisions, not bounded execution.
- **2026-08-08 (data_pipeline_failure escalation worker, agt-933fec, slot 4) — 22nd+ dispatch: backlog has genuinely
  shrunk (300k→19k), and this session shipped the fix that should FINALLY close the duplicate-dispatch waste this doc's
  own Progress Log has documented since dispatch #3.** Received another `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009) CRITICAL
  page for `(cefi, book_snapshot_5)`: 18,999/940,214 = 2.0% — a large drop from the last verified reading
  (300,674/1,123,966 = 26.8%, `agt-52c156` 2026-08-03), consistent with a normal idempotent backfill re-attempt finally
  working down the historical backlog this doc's Progress Log already flagged as pending (not retroactively cleared by
  any of the three code fixes). Alert context labeled "STATIC BACKLOG — only 480 attempted_failed row(s) in the last 1d
  (below the 500-row materiality floor); a decaying trickle on already-tracked backlog, not a fresh regression." Read
  this doc first per the pre-task plan/issue conflict-check rule. Re-verified all five fix commits are still ancestors
  of `origin/live-defi-rollout` (fresh `git fetch` in all three repos): MTDS `339ca767`/`6bf568ee`, UAC
  `8db188fe`/`1c4d8864`, deployment-service `a564cca` — all OK.

  Given the large numerator drop (not the usual "byte-identical, skip the read" case), did not need a fresh manifest
  pull to conclude no regression — a drop of this size is the OPPOSITE signature of the schema-contract mechanism (which
  historically only ever pushed `attempted_failed` UP, never down by an order of magnitude); it is straightforwardly
  explained by backlog cleanup, not a new failure class. **Root-caused instead why this doc has now absorbed 22+
  escalation-worker dispatches despite Option A (`deployment-service@1b035c52`, 2026-08-06) already shipping: Option A's
  `checkpoint_has_new_activity()` only compares the raw `max_attempted_at` timestamp against the issue doc's checkpoint
  — it has no notion of `is_static_backlog`. A cell with ANY nonzero daily trickle (this doc's own history: 91, 95, 110,
  24, 1, 215, 210, now 480 rows/24h) advances `max_attempted_at` by at least a few rows every single day, so the raw
  timestamp compare reads "genuinely new activity" on literally every re-page, even though `stale_backlog_annotation()`
  has already classified that exact volume as noise. Option A's own dedup gate was therefore silently inert for every
  single dispatch on THIS doc since it shipped (dispatches 18-22 all still fired a full worker despite each one's alert
  context already carrying the STATIC BACKLOG label) — the materiality classification and the dedup checkpoint compare
  were never wired together.**

  **Fix shipped**: `deployment-service@9102eb9b` — threaded the finding's `is_static_backlog` flag (already stamped by
  `check_high_attempted_failed` alongside `max_attempted_at`, unused until now) through
  `escalation_dedup.check_dispatch_dedup_for_finding` → `check_dispatch_dedup` → `checkpoint_has_new_activity`. When
  `is_static_backlog=True`, the dedup check now returns "no dedup-worthy new activity" (skip the fast-spawn dispatch,
  append a verification note, still advance the checkpoint) regardless of whether the raw timestamp moved — mirroring
  the severity-downgrade `dp_run_mostly_empty_static_backlog.effective_severity` already applies to Pager/Telegram
  routing, extended to the escalation-dispatch dedup layer specifically. A cell that is NOT static-backlog-classified (a
  genuinely fresh regression, or a trickle that crosses back above the materiality floor) is entirely unaffected — the
  raw timestamp compare still governs and still dispatches normally, preserving the `agt-40f31f` "moved numerator can
  still be a false alarm, so don't blanket-skip on numerator alone" invariant this doc's sibling archived doc already
  established. 4 new/updated regression tests in `tests/unit/test_escalation_dedup.py` (including one reproducing this
  doc's exact shape: an OPEN issue doc, a checkpoint from days ago, a fresh `max_attempted_at`, and
  `is_static_backlog=True` → dispatch skipped, checkpoint still advances). `quality-gates.sh` green (full run, 279s;
  includes basedpyright + the full unit suite). Shipped via `quickmerge --agent --files`, verified
  `git merge-base --is-ancestor 9102eb9b origin/live-defi-rollout` = true.

  **Conclusion**: no regression in this doc's own schema-contract fixes (all 3 still holding); the large backlog drop is
  healthy cleanup, not a new signal; and this session's fix is a genuinely different, complementary layer from the three
  prior fixes — it should stop most FUTURE static-backlog re-dispatches for this and every other DP-FETCH-009 cell in
  the same shape (`(cefi, derivative_ticker)`, `(cefi, trades)`, `(cefi, liquidations)` per the sibling archived doc's
  tracked conditions), not just this one. No GCS/manifest write, no VM launch. Pinged `dp-fleet-monitor` (authoring
  slot) with this outcome.

- **2026-08-08 (data_pipeline_failure escalation worker, agt-a46653, slot 2) — 23rd+ dispatch, byte-identical numerator
  to the just-fixed dedup-gap reading; this dispatch predates the fix taking effect on its own checkpoint, not evidence
  the fix failed.** Received another `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009) CRITICAL page for `(cefi, book_snapshot_5)`:
  18,999/940,818 = 2.0%, alert context labeled "STATIC BACKLOG — only 430 attempted_failed row(s) in the last 1d (below
  the 500-row materiality floor); a decaying trickle on already-tracked backlog, not a fresh regression." No issue doc
  pre-linked (`Filed issue: (none — alert carries the details)`); found this doc via the standard pre-task plan/issue
  conflict-check grep. Re-verified all six fix commits are still ancestors of `origin/live-defi-rollout` (fresh
  `git fetch` in all four repos): MTDS `339ca767`/`6bf568ee`, UAC `8db188fe`/`1c4d8864`, deployment-service
  `a564cca`/`1b035c52`/`9102eb9b` — all OK, including the dedup-gap fix (`9102eb9b`) the immediately-prior dispatch just
  shipped.

  The numerator (18,999) is byte-identical to `agt-933fec`'s reading; the 24h trickle decreased (480→430), continuing
  the same decay trend, not a resurgence. Per established precedent (numerator byte-identical, prior session's live
  manifest read only minutes/hours old, trickle still shrinking) did not repeat the live GCS read. This dispatch's own
  existence is expected, not a sign `9102eb9b` failed: that fix's dedup gate operates on a per-issue-doc checkpoint that
  advances going forward from when the fix landed — an escalation already generated/queued by `dp-fleet-monitor` before
  the fix was live (or from a detector tick concurrent with `agt-933fec`'s session) is not retroactively suppressed,
  only future ticks after the checkpoint is next written are. **Conclusion: no code fix needed** — all three root-cause
  schema-contract fixes plus both alerting-layer fixes (materiality downgrade, dedup-gap) continue to hold; this is a
  duplicate/near-duplicate dispatch of the already-fully-investigated static-backlog condition. Session cost: doc read +
  git-ancestor batch check (7 commits) + this Progress Log append, no GCS read, no code change, no VM launch. Pinging
  `dp-fleet-monitor` (authoring slot) with this outcome.

- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — both remaining open todos ([SERVICE]
  P3 features-service `l2_book_checkpoints`-shape reader gap; [SERVICE] P2 `_classify_tardis_error` truncation
  observability question) are explicit, self-declared design/maintainer-judgment calls between two engineering
  approaches, not checkable facts. None of today's 9 generalizable rulings apply to either. Independently corroborated
  by `cefi_satellite_ao_dispatch_batch10_2026_08_08.md` (active, `assigned_vm: planning`, today's full-corpus cefi
  re-audit), which lists this exact doc under "Deferred — human-only": "2 self-declared design/maintainer-judgment calls
  (choosing between two engineering approaches for the schema contract)." No reclassification.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **na-eligibility-audit 2026-08-09** (tranche=cefi, autonomous): KEEP-NA, valid — read the full ~900-line, 25+-dispatch
  escalation history for a RE-TRIAGE trap; found none. Both remaining items are self-declared design/maintainer calls.
- **2026-08-11 (data_pipeline_failure escalation worker, agt-a45914, slot 4) — 24th+ dispatch: numerator DROPPED again
  (18,999→8,670), continuing healthy backlog resolution; no code fix needed.** Received another `DP_RUN_MOSTLY_EMPTY`
  (DP-FETCH-009) CRITICAL page for `(cefi, book_snapshot_5)`: 8,670/958,967 = 0.9% (abs>=500 path), alert context
  labeled "STATIC BACKLOG — only 15 attempted_failed row(s) in the last 1d (below the 500-row materiality floor); a
  decaying trickle on already-tracked backlog, not a fresh regression." No issue doc pre-linked
  (`Filed issue: (none — alert carries the details)`); found this doc via the standard pre-task plan/issue
  conflict-check grep. Re-verified all seven fix commits are still ancestors of `origin/live-defi-rollout` (fresh
  `git fetch` in all three repos): MTDS `339ca767`/`6bf568ee`, UAC `8db188fe`/`1c4d8864`, deployment-service
  `a564cca`/`1b035c52`/`9102eb9b` — all OK. Confirmed `deployment_service/data_pipeline_monitors/escalation_dedup.py`
  present on `origin/live-defi-rollout` HEAD, and the `dp_escalation_checkpoint` frontmatter field is still ABSENT on
  this doc — consistent with the 23rd dispatch's documented expectation: `9102eb9b`'s dedup gate only advances its
  per-doc checkpoint going forward from the fix's landing, so a dispatch generated before the next checkpoint write is
  not retroactively suppressed. The numerator's continued drop (300,674 → 18,999 → 8,670 across the last four verified
  readings, ratio 26.8% → 2.0% → 0.9%) is the OPPOSITE signature of the schema-contract mechanism (which only ever
  pushed `attempted_failed` UP, never down by an order of magnitude) — straightforwardly the normal idempotent backfill
  re-attempt working down the historical backlog this doc's Progress Log already flagged, with the 24h trickle (15 rows)
  well under the 500-row materiality floor and `stale_backlog_annotation()` correctly labeling it STATIC BACKLOG.
  **Conclusion: no code fix needed** — all three root-cause fixes (contract shape, ts_event derivation, nullable levels)
  plus both alerting-layer fixes (materiality downgrade, dedup-gap) continue to hold under production load. Session
  cost: doc reads + git-ancestor batch check (7 commits) + this Progress Log append, no GCS read, no code change, no VM
  launch. Pinged `dp-fleet-monitor` (authoring slot) with this outcome; this is now the 24th+ dispatch for this
  condition, further corroborating `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md`'s closed Option A
  dedup fix (the checkpoint-write lag documented in the 23rd dispatch's own entry).
- **2026-08-11 (data_pipeline_failure escalation worker, agt-a45914, slot 7) — SAME escalation_id as the entry directly
  above, a genuine duplicate worker dispatch of one escalation event to two slots (slot 4, then slot 7), not a
  re-evaluated condition — the same exact-duplicate-escalation_id shape this doc has now documented 6+ times
  (`agt-ccb54c` 2026-07-30, `agt-0bf4a3` 2026-07-31, `agt-406c1f` 2026-07-31, `agt-e11908` 2026-08-03, now
  `agt-a45914`).** Read this doc first per the pre-task plan/issue conflict-check rule; found the slot-4 entry directly
  above already fully investigated this exact escalation_id/reading (8,670/958,967 = 0.9%, "STATIC BACKLOG — only 15
  attempted_failed row(s) in the last 1d"). Re-verified all seven fix commits are still ancestors of
  `origin/live-defi-rollout` (fresh `git fetch` in all three repos): MTDS `339ca767`/`6bf568ee`, UAC
  `8db188fe`/`1c4d8864`, deployment-service `a564cca`/`1b035c52`/`9102eb9b` — all OK. Per the established
  "numerator/reading byte-identical, prior session's live manifest read only minutes old → skip the live re-read"
  precedent, did not repeat the GCS read this session. **Conclusion: no code fix needed** — all three root-cause
  schema-contract fixes plus both alerting-layer fixes (materiality downgrade, dedup-gap) continue to hold; this is a
  duplicate dispatch of the exact same already-fully-investigated static-backlog condition, not a new regression.
  Session cost: doc read + git-ancestor batch check (7 commits) + this Progress Log append, no GCS read, no code change,
  no VM launch. Pinged `dp-fleet-monitor` (authoring slot) with this outcome.
- **2026-08-11 (data_pipeline_failure escalation worker, agt-a45914, slot 2) — SAME escalation_id as the two entries
  directly above (slot 4, then slot 7, now slot 2) — a THIRD duplicate worker dispatch of one escalation event, the same
  exact-duplicate-escalation_id shape now documented 7+ times.** Read this doc first per the pre-task plan/issue
  conflict-check rule; the slot-4 and slot-7 entries directly above already fully investigated this exact
  escalation_id/reading (8,670/958,967 = 0.9%, "STATIC BACKLOG — only 15 attempted_failed row(s) in the last 1d") and
  re-verified all seven fix commits ancestor-of-origin minutes ago. Per the same precedent, did not repeat the
  git-ancestor check or GCS read this session. **Conclusion: no code fix needed** — this is a duplicate dispatch of the
  exact same already-fully-investigated static-backlog condition, not a new regression. Session cost: doc read + this
  Progress Log append only, no GCS read, no code change, no VM launch. Pinged `dp-fleet-monitor` (authoring slot) with
  this outcome.
- **2026-08-11 (data_pipeline_failure escalation worker, agt-a45914, slot 3) — SAME escalation_id as the three entries
  directly above (slot 4, slot 7, slot 2, now slot 3) — a FOURTH duplicate worker dispatch of one escalation event, the
  same exact-duplicate-escalation_id shape now documented 8+ times.** Read this doc first per the pre-task plan/issue
  conflict-check rule; the slot-4/slot-7/slot-2 entries directly above already fully investigated this exact
  escalation_id/reading (8,670/958,967 = 0.9%, "STATIC BACKLOG — only 15 attempted_failed row(s) in the last 1d") and
  re-verified all seven fix commits ancestor-of-origin minutes ago (re-confirmed here via a fresh
  `git merge-base --is-ancestor HEAD origin/live-defi-rollout` on this worktree — OK). Per the same precedent, did not
  repeat the git-ancestor-per-repo check or GCS read this session. **Conclusion: no code fix needed** — this is a
  duplicate dispatch of the exact same already-fully-investigated static-backlog condition, not a new regression.
  Session cost: doc read + this Progress Log append only, no GCS read, no code change, no VM launch. Pinged
  `dp-fleet-monitor` (authoring slot) with this outcome; this doc's own repeated-exact-duplicate-escalation_id pattern
  (now 4 slots for `agt-a45914` alone) is squarely `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md`'s
  still-open Option A/B/C territory at the orchestrator dispatch layer (the per-doc dedup-gap fix, `9102eb9b`, only
  suppresses re-dispatch on a stale checkpoint across ticks — it has no mechanism for one tick fanning the same
  escalation_id out to multiple slots simultaneously, a different bug class).
