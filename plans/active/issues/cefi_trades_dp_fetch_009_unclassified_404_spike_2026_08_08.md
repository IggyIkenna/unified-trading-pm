---
doc_type: issue
title:
  DP-FETCH-009 (cefi/trades, 15,615 attempted_failed in the 14d trailing window) — verified the new trailing-window
  fix is live and correct; root-caused the dominant driver to an UNCLASSIFIED 404/venue-error spike on 2026-08-04
summary:
  Escalation agt-9c00b5 (data_pipeline_failure, slot 4) triaged a DP-FETCH-009 CRITICAL page for asset_group=cefi
  data_type=trades (15,615 attempted_failed of 1,459,849 attempted, ratio 1.1%, abs>=500 path; boot context labeled it
  "STATIC BACKLOG — only 164 attempted_failed row(s) in the last 1d"). Read
  gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet directly (read-only, existing
  single-walk-compliant consolidated index, no new GCS walk) and confirmed the alert's 15,615 figure EXACTLY equals the
  sum of daily attempted_failed counts over the trailing 14 days (2026-07-26..08-08) — proving
  `ATTEMPTED_FAILED_TRAILING_WINDOW_DAYS=14` (shipped `deployment-service@96271280` earlier the same day, 2026-08-08,
  for the sibling cefi/liquidations DP-FETCH-009 finding) is live and computing correctly here too; the lifetime total
  for cefi/trades attempted_failed is actually 272,800 (17x the alert's number), so the trailing-window fix is already
  doing real work suppressing stale-history noise. Of the 15,615, 52% (8,142 rows) is a single-day spike on 2026-08-04
  dominated by `UNCLASSIFIED:404 GET https` (BYBIT 3,605 / BINANCE-FUTURES 2,269 / DERIBIT 223) and
  `UNCLASSIFIED:UNCLASSIFIED_VENUE_ERROR` (OKX 1,995) — i.e. `classify_venue_error()` does not recognize these
  error-code tokens for these venues on data_type=trades, so they fall through the `UNCLASSIFIED:` catch-all instead of
  being routed to honest-absence or a specific retry/fail action (the same class of gap the Tardis
  code=140/300 fix closed for book_snapshot_5/derivative_ticker/liquidations, per
  `tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md`, but NOT yet investigated for these
  REST-venue/trades combos). Another 36% (~5,653 rows, 07-27..07-29) is a mix of already-explained causes (HYPERLIQUID
  UNCLASSIFIED_ADAPTER_ERROR, Aster aggTrades HTTP 429 rate-limiting, the aiodns resolver crash whose fix
  `market-tick-data-service@6a067cf1` landed 2026-07-28T10:31 UTC mid-window). The most recent 3 days (08-06/07/08:
  1,122/236/150) show a clear decay, consistent with the boot context's own staleness label — this is NOT a live
  ongoing incident today. No code changed this escalation (the 404/venue-error root cause needs a venue-side
  investigation this bounded escalation did not have scope to complete — see Todos).
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, deployment-service]
scope: [engineer, admin]
tags:
  [cefi, trades, attempted-failed, manifest, alerting, dp-fetch-009, data-pipeline-alerts, classify-venue-error]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/issues/cefi_liquidations_attempted_failed_lifetime_count_stale_2026_07_30.md,
    /plans/active/issues/tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md,
  ]
created: 2026-08-08
author: unknown
parent_epic: observability_master
priority: P2
source: ["data_pipeline_failure escalation agt-9c00b5, slot 4, 2026-08-08"]
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-08
locked_since:
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    deployment-service/deployment_service/data_pipeline_monitors/meta_watchers.py,
    deployment-service/deployment_service/data_pipeline_monitors/attempted_failed_staleness.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/errors/cefi.py,
    /plans/active/issues/cefi_liquidations_attempted_failed_lifetime_count_stale_2026_07_30.md,
  ]
---

# DP-FETCH-009 (cefi/trades) — trailing-window fix verified live; 2026-08-04 UNCLASSIFIED 404/venue-error spike is

# the dominant unexplained driver

## What I found

Escalation context (agt-9c00b5): CRITICAL `DP_RUN_MOSTLY_EMPTY` (registry_id `DP-FETCH-009`) for
`asset_group=cefi data_type=trades` — 15,615 `attempted_failed` cells of 1,459,849 attempted (ratio 1.1%, `abs>=500`
path). Boot context carried `attempted_failed_staleness.stale_backlog_annotation`'s label: "STATIC BACKLOG — only 164
attempted_failed row(s) in the last 1d (below the 500-row materiality floor); a decaying trickle on already-tracked
backlog, not a fresh regression." No issue doc was pre-filed.

Read `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` directly (read-only,
existing single-walk-compliant consolidated index, via a DuckDB predicate-pushdown query wrapped in
`scripts/dev/run-bounded-analysis.sh --mem-cap 3G` per the heavy-analysis-on-shared-host rule) and filtered to
`data_type=trades`:

- `capture_status` counts (lifetime, whole manifest): `captured`=1,444,234, `expected_unattempted`=1,316,563,
  `empty_confirmed`=697,711, `attempted_failed`=**272,800**.
- **The alert's 15,615 is NOT the lifetime count** — it is the trailing-14-day sum. Summing `attempted_at`-by-day counts
  for 2026-07-26 through 2026-08-08 (the exact `ATTEMPTED_FAILED_TRAILING_WINDOW_DAYS=14` window) gives **exactly
  15,615**: 08-08=150, 08-07=236, 08-06=1,122, 08-05=71, 08-04=8,142, 08-03=39, 08-02=41, 08-01=0, 07-31=0, 07-30=0,
  07-29=1,538, 07-28=2,350, 07-27=1,765, 07-26=161. This is direct confirmation that `deployment-service@96271280`
  ("feat(monitors): trailing-window threshold for check_high_attempted_failed (DP-FETCH-009)", shipped earlier the same
  day for the sibling cefi/liquidations finding) is deployed and computing correctly for cefi/trades too — the lifetime
  total (272,800) would have paged this cell at CRITICAL indefinitely under the old lifetime-count logic; the new window
  correctly suppresses 94.3% of that historical volume.
- **error_reason breakdown of the full 272,800 lifetime attempted_failed rows** (for context; NOT all in the alert
  window): `UNCLASSIFIED:Tardis HTTP 403`=112,600, `VENUE_FETCH_FAILED`=93,935, `Tardis HTTP 403`=44,665,
  `UNCLASSIFIED:404 GET https`=8,763, `UNCLASSIFIED:UNCLASSIFIED_VENUE_ERROR`=2,045, and a long tail (Tardis 400/500,
  aiodns, Aster 429s, etc.) — the huge Tardis-403 buckets are old history (matches the same
  `tardis-concurrency-guard.sh` N>1 storm + code=274 concurrent-IP-lock classes already root-caused and fixed in the
  sibling cefi/liquidations doc) and mostly predate the 14-day window, hence excluded from the alert's count.
- **2026-08-04 (8,142 rows, 52% of the alert's window total) — the dominant driver, NOT previously investigated for
  data_type=trades**: `error_reason` x `venue` breakdown:
  - `UNCLASSIFIED:404 GET https` — BYBIT 3,605 / BINANCE-FUTURES 2,269 / DERIBIT 223 = 6,097 rows.
  - `UNCLASSIFIED:UNCLASSIFIED_VENUE_ERROR` — OKX 1,995 rows.
  - Small remainders: `UNCLASSIFIED_ADAPTER_ERROR` ASTER 21, `build_partition_path built a non-canonical GCS...`
    BINANCE-DELIVERY 20, `schema contract violated for cefi/BINANCE-FUTU...` BINANCE-FUTURES 8, `Tardis HTTP 500`
    OKX-FUTURES 1.
  - The `UNCLASSIFIED:` prefix (`market_tick_data_service/engine/orchestrator/sentinels.py:227`/`656`) is stamped
    whenever `classify_venue_error(venue, code_token)` returns `None` — i.e. UAC has no registered classification for
    this venue+error-code combination, so the row falls through to a generic `attempted_failed` with no signal on
    whether it's honest-absence (permanent, should not retry, should not depress coverage) vs a genuine transient/
    config error (should retry). `unified_api_contracts/canonical/crosscutting/errors/cefi.py` registers entries keyed
    by lowercase venue names (`"binance"`, etc.) — I did NOT find entries for `bybit`/`deribit`/`okx`/ `binance-futures`
    404s in a quick grep, but did not exhaustively trace the venue-key normalization used at the classification call
    site, so I cannot yet say definitively whether this is a missing-registration gap (mirrors the Tardis code=140/300
    precedent) or a genuinely-correct "these venues have no 404 special-case, and 404 legitimately means fail-and-retry
    for them" design. That distinction requires reading the actual BYBIT/BINANCE-FUTURES/DERIBIT/ OKX trades adapter
    code + a live sample response to know what triggered the 404/UNCLASSIFIED_VENUE_ERROR on that specific day — out of
    this bounded escalation's scope (see Todos).
- **2026-07-27/28/29 (~5,653 rows, 36% of the window total) — already-explained mix**: HYPERLIQUID
  `UNCLASSIFIED_ADAPTER_ERROR` 1,438; Aster `aggTrades HTTP 429 for <SYMBOL>` rate-limiting spread across ~15+ symbols
  (~900 total); `Resolver requires aiodns library` on OKX-FUTURES 220 + BITFINEX-FUTURES 58 (the aiodns crash fixed by
  `market-tick-data-service@6a067cf1`, landed 2026-07-28T10:31 UTC — mid-window, so some of these rows predate the fix
  and are expected residual, matching the sibling liquidations doc's finding);
  `RECLASS_REVERT_ORIGINAL_REASON_ UNKNOWN_2026_07_29` on BYBIT 150 + BINANCE-FUTURES 138 (an artifact of a prior
  reclassification-revert operation on that date — did not trace which script produced it, flagging for whoever picks up
  the todos below); smaller `UNCLASSIFIED:404 GET https` on DERIBIT/BYBIT/BINANCE-FUTURES.
- **Trend**: the 3 most recent days (08-06=1,122, 08-07=236, 08-08=150) show clear decay from the 08-04 spike — this
  matches the boot context's "STATIC BACKLOG... decaying trickle... not a fresh regression" label. This is NOT an active
  incident happening today; the 08-04 spike is 4 days old and already resolving on its own (either the underlying
  condition self-cleared, or later retries are succeeding).

## Why it matters

The trailing-window fix (shipped hours earlier the same day for the sibling liquidations cell) is confirmed working
correctly here — this validates that fix generally, not just for its original liquidations case. But the fix only hides
OLD noise; it does not explain or fix the 2026-08-04 spike, which is still real, recent (within the alert window), and
un-investigated. An `UNCLASSIFIED:` error reason means the pipeline itself doesn't know what this failure means — it
can't tell the operator or the coverage denominator whether these 8,142 rows are inflating the CeFi trades
attempted_failed count with genuinely-fixable honest-absence data (the Tardis 140/300 precedent) or are a real,
possibly-still-latent adapter/venue issue for BYBIT/BINANCE-FUTURES/DERIBIT/OKX trades fetches.

## Todos

- [ ] [DIAG] P2. Root-cause the 2026-08-04 `UNCLASSIFIED:404 GET https` spike for BYBIT (3,605) / BINANCE-FUTURES
      (2,269) / DERIBIT (223) trades fetches: pull the actual adapter code path + (if available) Cloud Logging / request
      logs for that day to determine what specifically 404'd (bad endpoint, stale instrument catalogue entry, genuine
      vendor-side gap, transient outage) and whether it recurred after 08-04. Repo: market-tick-data-service.
- [ ] [DIAG] P2. Same for `UNCLASSIFIED:UNCLASSIFIED_VENUE_ERROR` on OKX (1,995 rows, same day) — this reason string
      itself signals `classify_venue_error` couldn't even extract a usable code token, which is a step below the 404
      case. Repo: market-tick-data-service.
- [ ] [CODE] P2. Once the above two are root-caused: if either is a genuine structural/permanent absence (mirrors the
      Tardis code=140/300 pattern), register it in `unified_api_contracts/canonical/crosscutting/errors/cefi.py`
      (`classify_venue_error`) so it routes to honest-absence instead of `attempted_failed` going forward, and confirm
      whether `bybit`/`deribit`/`okx`/`binance-futures` have ANY existing 404 registration today (the quick grep in this
      doc found none, but venue-key normalization at the classification call site was not traced — verify before
      assuming a gap). If it's a genuine transient/config error, leave it in `attempted_failed` but ensure it's
      correctly classified (not `UNCLASSIFIED:`) so retry/backoff behavior applies. Repo: unified-api-contracts.
- [ ] [DIAG] P3. Trace the source of `RECLASS_REVERT_ORIGINAL_REASON_UNKNOWN_2026_07_29` (288 rows, BYBIT+
      BINANCE-FUTURES trades) — identify which reclassification script produced this reversion and whether it needs a
      follow-up. Repo: market-tick-data-service.

## Progress Log

- 2026-08-08: Filed by `data_pipeline_failure` escalation `agt-9c00b5` (slot 4). Verified the newly-shipped
  `ATTEMPTED_FAILED_TRAILING_WINDOW_DAYS=14` fix (`deployment-service@96271280`, shipped earlier the same day for the
  sibling cefi/liquidations DP-FETCH-009 finding) is live and computing correctly for cefi/trades — the alert's 15,615
  figure exactly matches the 14-day daily sum, independently confirming the fix generalizes beyond its original case.
  Root-caused the dominant window driver (52%, the 2026-08-04 spike) to two `UNCLASSIFIED:` error-reason buckets (404 on
  BYBIT/BINANCE-FUTURES/DERIBIT, `UNCLASSIFIED_VENUE_ERROR` on OKX) that `classify_venue_error()` does not recognize — a
  code-classification-gap class matching the Tardis code=140/300 precedent, but NOT yet investigated for these REST
  venues on data_type=trades. Did not attempt a code fix: the correct classification (honest-absence vs
  genuine-retryable-failure) requires reading the actual adapter/vendor response semantics for that day, which is
  outside this bounded escalation's scope — filed as DIAG todos instead of guessing. No code changed.
