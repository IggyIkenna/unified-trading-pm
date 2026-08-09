---
doc_type: issue
title: >-
  HYPERLIQUID perp_daily_ctx has produced zero rows since 2026-06-02 — no live writer covers it, mark_price silently
  absent going forward for the funding-driven strategy archetypes
summary: >-
  While backfilling manifest rows for the already-migrated historical perp_daily_ctx corpus
  (defi_satellite_ao_dispatch_batch6_2026_07_30.md todo -010), a real bounded GCS scan found the HYPERLIQUID
  perp_daily_ctx corpus (CanonicalPerpFundingProvider's mark-price source) spans exactly 2023-05-20..2026-06-01 with
  zero gap days, then stops dead — no objects exist for any day on/after 2026-06-02. Confirmed via direct grep that
  neither of the two candidate writers currently produces it: the retired MTDS backfill script targets a
  confirmed-deleted bucket, and the live perp_funding_handler.py never writes perp_daily_ctx at all (only perp_funding).
  CanonicalPerpFundingProvider will silently return mark_price=None for HYPERLIQUID from 2026-06-02 onward
  (honest-absence by design, not a crash) — a real, growing forward coverage gap for the CARRY_BASIS_PERP /
  CARRY_FUNDING_DISPERSION archetypes' mark price. Not fixed here (out of the dispatching todo's scope) — filed as its
  own tracked follow-up per the workspace's "every follow-up is a tracked todo, never prose" rule.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, strategy-service]
scope: [engineer]
tags: [defi, perp-daily-ctx, perp-funding, hyperliquid, mark-price, honest-absence, forward-gap, live-writer-gap]
related:
  [
    /plans/archive/issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md,
    /plans/active/defi_satellite_ao_dispatch_batch6_2026_07_30.md,
    /plans/active/defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04_finalize_2026_08_08.md,
  ]
created: "2026-08-04"
author: unknown
last_updated: "2026-08-04"
parent_epic: defi_master
priority: P2
source: >-
  Found while executing defi_satellite_ao_dispatch_batch6_2026_07_30.md's todo -010 (perp_daily_ctx manifest
  registration), 2026-08-04 — a real bounded GCS scan of the historical corpus surfaced this forward gap as a byproduct
  of establishing the corpus's exact date range.
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    market-tick-data-service/market_tick_data_service/cli/handlers/perp_funding_handler.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/_perp_funding_hyperliquid.py,
    market-tick-data-service/scripts/backfill_hl_mark_price_from_s3_asset_ctxs_2026_06_17.py,
    strategy-service/strategy_service/engine/core/canonical_perp_funding_provider.py,
    /plans/active/defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04_finalize_2026_08_08.md,
  ]
---

# HYPERLIQUID `perp_daily_ctx` forward gap since 2026-06-02

## What was found

Executing `defi_satellite_ao_dispatch_batch6_2026_07_30.md`'s todo -010 (register `perp_daily_ctx` manifest rows for the
already-migrated historical corpus) required establishing the corpus's real date range via a live, bounded GCS scan
(`unified-trading-pm/scripts/migration/register_perp_daily_ctx_manifest_backfill_2026_08_04.py`). That scan found:

- HYPERLIQUID `perp_daily_ctx` objects exist for EVERY day 2023-05-20..2026-06-01 (1,109 calendar days, zero gaps).
- **Zero objects exist for 2026-06-02 or any later day** (verified against today, 2026-08-04 — a 63-day-and-growing
  gap).

## Why: no live writer covers this data_type

Grepped the entire `market-tick-data-service` repo (excluding tests) for `perp_daily_ctx` — it appears in exactly ONE
file:

- `scripts/backfill_hl_mark_price_from_s3_asset_ctxs_2026_06_17.py` — a one-off campaign script whose target bucket
  (`perp-funding-{project}`) is confirmed DELETED (`gcloud storage buckets describe` → 404, per
  `issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md` fact #4). This script cannot produce new rows —
  any `--apply` run would error immediately on the missing bucket, not silently succeed.

`market_tick_data_service/cli/handlers/perp_funding_handler.py` (the LIVE, scheduled, daily-cron handler that DOES
successfully write `perp_funding` — confirmed manifest-registered and running daily per
`issues/defi_onchain_perp_funding_permanently_unsatisfiable_dependency_2026_07_31.md`) was checked directly: it never
references `perp_daily_ctx` anywhere. It only writes `perp_funding`.

So there is currently **no code path, live or dead-but-fixable, that produces new `perp_daily_ctx` rows for
HYPERLIQUID**. The historical corpus (2023-05-20..2026-06-01) is exactly what got copied over by the 2026-07-13
dedicated-bucket-to-shared-bucket migration — after that migration, nothing has continued writing this data_type.

## Downstream impact

`CanonicalPerpFundingProvider` (`strategy-service/strategy_service/engine/core/canonical_perp_funding_provider.py`)
reads `perp_daily_ctx` for the day's `mark_price` per coin, joined against `perp_funding`'s funding-rate rows
(`_marks_for_day` → `funding_for_day`). Per the module's own "Honest absence" contract, a day/venue with no
`perp_daily_ctx` shard yields `mark_price=None` for every `FundingObservation` that day — **not a crash, not a
fabricated value, but a real degradation**: this is the real production feed for the `CARRY_BASIS_PERP` /
`CARRY_FUNDING_DISPERSION` archetypes (confirmed live caller: `paper_run_handler.py:931-932`). Since 2026-06-02, every
HYPERLIQUID funding observation these archetypes consume has carried `mark_price=None` — silently degrading whatever
computation depends on the mark (e.g., price-PnL legs of a funding-carry backtest/paper run), without any error or alert
surfacing it.

## What this issue does NOT resolve

This doc intentionally does not decide HOW to close the gap — that is a real design/ownership question (revive the
backfill script's logic against a live source instead of the dead dedicated bucket? wire `perp_daily_ctx` into
`perp_funding_handler.py` directly, mirroring how `perp_funding` itself is written daily? something else?), which is
exactly the class of decision `task_template.md`'s "dispatch-scope eligibility" bar says should NOT be dispatched as a
bare AO todo until an operator/design pass names the approach. This doc establishes the fact + impact; the fix approach
is the open question below.

## Todos

- [x] N. ✅ [DIAG] P2. **RULED 2026-08-08 (operator): approach (a)** — add a `perp_daily_ctx` write to the existing
      daily `perp_funding_handler.py` cron path. Read `perp_funding_handler.py` + its `_perp_funding_hyperliquid.py`
      stage module before this ruling was applied, to scope the real diff (see the follow-up `[CODE]` todo below). **Key
      scoping facts found**: (1) `_collect_hyperliquid()` (`_perp_funding_hyperliquid.py`) currently calls ONLY the HL
      `/info` `fundingHistory` endpoint (`_fetch_coin_funding`), which returns `funding_rate`/`premium`/ `timestamp` —
      no mark price / notional volume / open interest at all; a NEW HL `/info` request (mirroring the old dead backfill
      script's source data — `type: metaAndAssetCtxs`/`assetCtxs`, the live-REST equivalent of the S3 `asset_ctxs`
      archive it read historically) is needed to get `mark_px`/`day_ntl_vlm`/`open_interest` per coin. (2) The **write
      path itself must NOT reuse the old dead backfill script's path convention** — that script wrote to the
      now-confirmed-DELETED dedicated `perp-funding-{project}` bucket via a bare
      `pipeline_mode=batch_hyperliquid/asset_group=defi/...` shape; HYPERLIQUID was reclassified DeFi→CeFi 2026-07-06,
      so the LIVE write path (matching `perp_funding`'s own current write) is the CeFi partition path —
      `build_cefi_partition_path(venue="HYPERLIQUID", instrument_type=InstrumentType.PERPETUAL, data_type="perp_daily_ctx", day=..., pipeline_mode=...)`
      via `_write_hyperliquid_perp_funding_rows`'s own sharding pattern — written to
      `get_write_bucket_name("market_data", "cefi")`, registered through
      `DefiManifestRecorder(..., asset_group="cefi")`, exactly mirroring how `perp_funding` rows are produced today. (3)
      Target row schema (from the dead backfill script's own `_records_for_day`, adapted to the live per-coin `/info`
      response shape instead of the CSV archive): `coin`/`mark_price`/`day_ntl_vlm`/`open_interest`/
      `timestamp`/`instrument_id`/`venue`/`chain`/`instrument_type`/`data_type=perp_daily_ctx`.
- [x] N. ✅ [CODE] P2. **Implement the perp_daily_ctx forward-write per the ruled approach (a) scoping above.** In
      `market_tick_data_service/cli/handlers/_perp_funding_hyperliquid.py`: add a new fetch step alongside
      `_fetch_coin_funding` that calls HL `/info` for the day's per-coin mark price / day notional volume / open
      interest (the live equivalent of the `asset_ctxs` archive
      `backfill_hl_mark_price_from_s3_asset_ctxs_2026_06_17.py` reads historically — confirm the exact live request
      `type` against HL's public API docs before coding, do not assume `metaAndAssetCtxs` without checking); build +
      write `perp_daily_ctx` rows via the SAME `_write_hyperliquid_perp_funding_rows`-style CeFi partition-path sharding
      `perp_funding` already uses (NOT the old dead-bucket path — see scoping note above); register via
      `DefiManifestRecorder(asset_group="cefi")`, `record_captured`/`record_zero_rows`/`record_failed` per the existing
      honest-absence contract. Wire the new fetch into `_collect_hyperliquid()`'s existing per-coin-batch loop so it
      lands in the same daily cron run `perp_funding` already produces (no new scheduled job). Unit tests: mock the new
      HL endpoint response, assert a `perp_daily_ctx` shard is written per instrument with the columns above; assert
      honest-absence (`record_zero_rows`/`record_failed`) on an empty/error response, mirroring `perp_funding`'s own
      pattern. Repo: market-tick-data-service. Done-when: a live/backfill run produces real `perp_daily_ctx` manifest
      rows for HYPERLIQUID on a fresh date (closing the forward gap since 2026-06-02) and existing `perp_funding` tests
      stay green.
- [ ] [DIAG] P3. Once the forward-write gap is closed, confirm whether the CeFi Tardis `perp_funding_corpus.py` writer
      (features-service, fixed to include a manifest write this same session per
      `issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md`) has ever actually run in production since —
      it was confirmed NOT to have run as of 2026-07-13; re-check post-fix whether it's been invoked (scheduled or
      manual) and producing real CeFi `perp_daily_ctx` rows, or whether it too needs a live-scheduling gap closed. Repo:
      features-service.

## Progress Log

- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: RECLASSIFY → `assigned_vm: planning` (was `NA`),
  `execution_scope: orchestrator-agent`. Both open todos are bounded/worker-determinable: the operator's
  round5-na-digest-defi ruling (item 73, same day) named the exact approach and the `[CODE] P2` todo below already
  carries the full scoping (write path, schema, wiring point, Done-when criterion) — this is exactly the invitation the
  same-day filer left ("a future `/na-eligibility-audit` pass may reclassify it"). The `[DIAG] P3` todo is a small,
  independently bounded follow-up check. Conflict-check clear: no active `assigned_vm: planning` plan in
  `parent_epic: defi_master` claims this work; `defi_satellite_ao_dispatch_batch9/batch10` (still active) don't
  reference this doc; the consolidated-closeout doesn't cite it either. Gated finalize companion authored:
  `defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04_finalize_2026_08_08.md`.
- **round5-na-digest-defi 2026-08-08 (apply pass, item 73)**: operator ruled approach (a) — add the `perp_daily_ctx`
  write to the existing `perp_funding_handler.py` cron path. Read `perp_funding_handler.py` +
  `_perp_funding_hyperliquid.py` before writing the follow-up to scope the real diff: the current handler has no
  mark-price/volume/OI fetch at all (only `fundingHistory`), and — importantly — the write path must NOT reuse the old
  dead backfill script's now-deleted-bucket convention; it needs the CURRENT CeFi partition-path shape `perp_funding`
  itself already uses (HYPERLIQUID reclassified DeFi→CeFi 2026-07-06). Filed a concrete `[CODE]` P2 implementation todo
  with the exact write-path/schema/wiring scope (not built this session — real code build, not a small inline fix). Doc
  stays `assigned_vm: NA` for now (not asked to flip this one); the new todo is a bounded, worker-determinable
  implementation task, so a future `/na-eligibility-audit` pass may reclassify it.
- **2026-08-04**: Filed while executing `defi_satellite_ao_dispatch_batch6_2026_07_30.md` todo -010 (manifest backfill
  for the historical `perp_daily_ctx` corpus). No code changed here — pure investigation + issue filing.
- **na-eligibility-audit 2026-08-04** (tranche=defi, dispatch agt-62865a): KEEP-NA valid — both open todos are an
  explicit design/ownership decision (pick among 3 unnamed fix approaches) that the doc itself says must not be
  dispatched as a bare AO todo until an operator/design pass names the approach. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA valid — both open todos remain unresolved design/judgment
  decisions (no predetermined fix approach); todo 2 sequenced after todo 1.
- **context-scout 2026-08-09**: re-scouted; context_scope refreshed to 5 entries (added the gated finalize companion
  `defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04_finalize_2026_08_08.md`, authored during the
  2026-08-08 RECLASSIFY sweep, since the prior 2026-08-05 marker's 4-entry list).
- **2026-08-09 (AO worker, slot 13)**: `[CODE] P2` shipped — market-tick-data-service@f5753479.
  `_perp_funding_hyperliquid.py`'s `_collect_hyperliquid()` now also fetches HL `/info` `metaAndAssetCtxs` (confirmed
  against the module's own `activeAssetCtx` WS ticker channel field shape — `markPx`/`dayNtlVlm`/`openInterest`, same
  fields the retired S3 `asset_ctxs` backfill read) and writes `perp_daily_ctx` rows via the SAME CeFi partition-path
  sharding `perp_funding` uses (refactored into a shared `_write_hyperliquid_cefi_rows` helper, parameterised by
  `data_type`), registered through the SAME `DefiManifestRecorder` already threaded through `_dispatch_protocol` →
  `_collect_hyperliquid`, with `record_captured`/`record_zero_rows`/`record_failed` honest-absence semantics isolated
  from `perp_funding`'s own row count/exceptions (a `perp_daily_ctx` fetch failure never aborts or mis-attributes to the
  `perp_funding` shard). Rides the existing daily cron run — no new scheduled job. Evidence: `quality-gates.sh` green on
  the shipped SHA (10324 passed, 0 failed); new coverage in `tests/unit/test_perp_funding_hyperliquid.py`
  (`TestPerpDailyCtxForwardWrite`, `TestFetchAssetCtxs`) asserts a `perp_daily_ctx` shard is written per instrument,
  honest-absence on an empty response, `record_failed` on a genuine fetch error (not conflated with a zero-row day), and
  a malformed `metaAndAssetCtxs` response shape raises rather than silently returning empty. **Not verified here**: an
  actual live/backfill run producing real `perp_daily_ctx` manifest rows in production — this todo's own scope is the
  code + unit-level proof; the finalize plan's `[REVIEW] P2` todo re-verifies against a real fresh-date manifest read
  once this deploys and the next daily cron cycle runs. `[DIAG] P3` (CeFi Tardis writer re-check) remains open —
  separate scope, not part of this todo.
