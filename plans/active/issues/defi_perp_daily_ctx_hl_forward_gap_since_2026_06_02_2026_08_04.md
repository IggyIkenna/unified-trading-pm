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
    /plans/active/issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md,
    /plans/active/defi_satellite_ao_dispatch_batch6_2026_07_30.md,
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
assigned_vm: NA
execution_scope: local-only
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
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
    market-tick-data-service/scripts/backfill_hl_mark_price_from_s3_asset_ctxs_2026_06_17.py,
    strategy-service/strategy_service/engine/core/canonical_perp_funding_provider.py,
    /plans/active/issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md,
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

- [ ] [DIAG] P2. Decide the fix approach for HYPERLIQUID `perp_daily_ctx` going forward: (a) add a `perp_daily_ctx`
      write to the existing daily `perp_funding_handler.py` cron path (mirrors how `perp_funding` itself is already
      produced live — likely the lowest-risk option since the manifest/schema plumbing this session added already covers
      the data_type), (b) revive the backfill script's HL S3 `asset_ctxs` read logic against a live/current source and
      wire it into a scheduled job, or (c) some other approach. Read `perp_funding_handler.py`'s current write logic
      first to scope the actual diff size before deciding. Repo: market-tick-data-service. Done when: an approach is
      chosen and recorded here (or a design doc), with a scoped follow-up `[CODE]` todo filed against it.
- [ ] [DIAG] P3. Once the forward-write gap is closed, confirm whether the CeFi Tardis `perp_funding_corpus.py` writer
      (features-service, fixed to include a manifest write this same session per
      `issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md`) has ever actually run in production since —
      it was confirmed NOT to have run as of 2026-07-13; re-check post-fix whether it's been invoked (scheduled or
      manual) and producing real CeFi `perp_daily_ctx` rows, or whether it too needs a live-scheduling gap closed. Repo:
      features-service.

## Progress Log

- **2026-08-04**: Filed while executing `defi_satellite_ao_dispatch_batch6_2026_07_30.md` todo -010 (manifest backfill
  for the historical `perp_daily_ctx` corpus). No code changed here — pure investigation + issue filing.
- **na-eligibility-audit 2026-08-04** (tranche=defi, dispatch agt-62865a): KEEP-NA valid — both open todos are an
  explicit design/ownership decision (pick among 3 unnamed fix approaches) that the doc itself says must not be
  dispatched as a bare AO todo until an operator/design pass names the approach. Doc stays `assigned_vm: NA`.
