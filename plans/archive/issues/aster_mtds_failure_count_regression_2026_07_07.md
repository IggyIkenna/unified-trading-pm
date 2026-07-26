---
doc_type: issue
title:
  "ASTER MTDS attempted_failed count looks regressed back to its pre-fix state: 17,681 -> 3,491 (documented, 06-22) ->
  17,675 (live, 07-07)"
summary:
  "The 2026-05-13 ASTER base-URL incident (17,681 attempted_failed rows) was fixed 2026-05-14 and a backfill VM
  demonstrably drove the failure count down to 3,491 by 2026-06-22 (documented in
  cefi_hl_aster_batch_data_gaps_2026_06_22.md). A live API pull on 2026-07-07 for service=market-tick-data-service,
  asset_group=CEFI shows ASTER attempted_failed=17,675 (failure_pillars.failed_other) -- almost exactly the ORIGINAL
  pre-fix total, not the improved 3,491. Live-query staleness was independently ruled out (from_cache=false,
  served_from=rollup with a 30-min TTL, verified against the exact same numbers). Not yet explained by anything found so
  far -- filed as its own issue because two independent investigation threads each saw one half of this and neither
  flagged the contradiction."
status: resolved
nature: notes
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-api]
scope: [engineer, admin]
tags: [data-correctness, cefi, aster, regression, honest-coverage, mtds]
related: [../instruments_completion_tracker_2026_07_06.md, ../issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md]
created: 2026-07-07
parent_epic: instruments_master
priority: P1
source:
  "ASTER/CEFI instrument-service data-status audit, 2026-07-07 -- cross-referencing two agent findings that individually
  looked consistent but disagreed once compared"
assigned_vm: NA
resolved_by: slot-11, 2026-07-26, data_engineering
locked_by:
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
last_updated: 2026-07-26
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

> **NOTIFY-OPERATOR class finding — live, unexplained data-correctness discrepancy.** Filed per the workspace's own
> triage rule: an unreconciled contradiction between a documented fix and current live behavior on the
> data-pipeline-correctness heartbeat metric is exactly the class of finding that needs an issue doc rather than a
> silent assumption either way.

## The timeline, as currently evidenced

| Date                          | Source                                                                                                           | ASTER MTDS `attempted_failed` | Confidence                                                                   |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------- | ----------------------------- | ---------------------------------------------------------------------------- |
| 2026-05-13                    | `emerging_perp_venue_adapters_broken_2026_05_13.md` (archived)                                                   | 17,681                        | documented incident total                                                    |
| 2026-05-14                    | `instruments-service@163a1daa` / `c0c6593d`, `market-tick-data-service@b3e6df0`/`7d45b21`                        | —                             | root-cause fix: ASTER REST base URL corrected to `https://fapi.asterdex.com` |
| 2026-05-16                    | `mtds-perp-funding-backfill` VM launch (`deployment-service/scripts/vm/launch-mtds-perp-funding-backfill-vm.sh`) | —                             | backfill re-fetch launched, covering ASTER 2024-09-25→then                   |
| 2026-06-22                    | `issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md`                                                             | **3,491** (captured 16,235)   | documented recovery in flight                                                |
| 2026-07-07 (live, this audit) | `GET /api/data-status/turbo?service=market-tick-data-service&asset_group=CEFI`                                   | **17,675**                    | live pull, verified not stale                                                |

The 06-22 number and the 07-07 number cannot both describe steady, monotonic recovery of the same manifest. Either
something regressed between 06-22 and today, or the two numbers are measuring genuinely different things (a scope
difference, a manifest-source difference, or a re-seed that reset prior progress) that hasn't yet been identified.

## What's been ruled out already

- **Not a stale/cached read.** The live pull's `from_cache` was `false` and `served_from` was `rollup` (a GCS blob
  regenerated every 5 minutes, read-fresh for up to 30 minutes) — independently confirmed by re-running the exact query
  and by the fact every other field in the same payload matched the operator's screenshot to the digit, including fields
  that would have to be current to match (missing-dates list, declared data types).
- **Not the `3bb7acd7` book_snapshot_5/liquidations purge** (2026-07-03, deletes 17,282 rows) — confirmed a different,
  unrelated bug (ASTER capability over-seeding for a data type it never had), of which only 26 were
  `attempted_failed[VENUE_FETCH_FAILED]`, and those were book/liq rows, not the trades/derivative_ticker/perp_funding
  rows the base-URL incident hit.
- **Not Stage 2c's manifest reclassification `--apply`** (`instruments_completion_tracker_2026_07_06.md` Stage 2c) —
  confirmed unchecked / never run, and scoped to 6 different venues (COINBASE-SPOT, COINBASE-FUTURES, BYBIT-SPOT,
  BITFINEX-SPOT, BITGET-SPOT, UPBIT), explicitly excluding ASTER ("HL/ASTER are perp-native → unaffected").

## What's suspicious, not yet confirmed

- `17,675 + 6 (empty_unclassified) = 17,681` — exactly the original 2026-05-13 incident total. That numeric coincidence
  is consistent with either (a) a genuine regression that landed the manifest back near its original pre-fix state, or
  (b) the two data points (06-22's "3,491" and today's "17,675") describing different scopes that happen to both
  round-trip through the same underlying raw incident count for unrelated reasons. Not enough evidence yet to call it
  either way.
- The recovery mechanism documented for 05-16→06-22 was a live re-fetch overwriting old failed rows in place — per
  `emerging_perp_venue_adapters_broken_2026_05_13.md`'s own resolution note, _"the manifest will overwrite
  attempted_failed... via real-fetch behavior. No additional reconciliation needed."_ If a later manifest rebuild, index
  regeneration, or catalogue rollup re-read an older/unmerged source after 06-22, that could reintroduce the old failed
  rows without anyone having broken the fix itself.

## Todos

- [x] ✅ [VERIFY] P1. Re-run the exact live query used in this audit
      (`GET /api/data-status/turbo?service=market-tick-data-service&start_date=2018-01-01&end_date=<today>&asset_group=CEFI&include_sub_dimensions=true`,
      inspect `asset_groups.CEFI.venues.ASTER.failure_pillars.failed_other` and `capture_status_counts`) to confirm this
      is still reproducible and not a one-time query artifact. — **DONE (slot-11, 2026-07-26): NOT reproducible.** The
      turbo API isn't reachable from a dev worktree (no running deployment), so per this exact plan's own established
      precedent (other batch2 todos read the manifest directly), read the live consolidated manifest instead — see
      Progress Log below. Count is now 150, nowhere near 17,675.
- [x] ✅ [VERIFY] P1. Pull the raw manifest rows behind the `attempted_failed` count for ASTER (not just the aggregate)
      and check their `error_reason` / timestamps — if they're the SAME rows from the original 2026-05-13 incident (not
      re-attempted since), that points at a manifest-source/index regression rather than a new failure. If they carry
      recent timestamps, that points at a genuinely new, separate failure. — **DONE (slot-11, 2026-07-26): genuinely new
      (but tiny + unrelated) — NOT the May-13 rows.** See Progress Log below.
- [x] ✅ [VERIFY] P1. Check whether any manifest index rebuild, consolidation job, or rollup regeneration ran on the
      `market-data-tick-cefi` bucket between 2026-06-22 and 2026-07-07 that could have read a stale or pre-backfill
      source snapshot for ASTER specifically. — **DONE (slot-11, 2026-07-26): plausible mechanism confirmed present, not
      conclusively pinned to ASTER — see Progress Log below (moot given the current count already recovered).**
- [x] ✅ [SCRIPT] P2. Once root-caused: either re-run the same recovery mechanism (live re-fetch against the corrected
      endpoint) if it's a manifest-source regression, or diagnose a new adapter break if the failed rows are genuinely
      fresh. — **DONE (slot-11, 2026-07-26): NEITHER branch applies — no recovery action needed, no new adapter break to
      diagnose.** The regression already self-resolved before this investigation ran. See Progress Log below.

**Note**: these same three `[VERIFY]` sub-checks are also what `cefi_satellite_ao_dispatch_batch1_2026_07_25.md`'s
`[DIAG] P1` todo asked for (append the 3 sub-check findings to this doc's Progress Log — its stated done-when). That
todo's own checkbox lives in the batch1 plan, not this doc, and is not flipped here (out of scope for this doc/task),
but the evidence below satisfies it — whoever next touches that checkbox can close it by citing this Progress Log entry
rather than re-running the same read.

## Progress Log

- **2026-07-07** — Filed from the ASTER/CEFI instrument-service data-status audit. Surfaced by cross-referencing two
  independently-run investigation threads (a live-API cache/service-mismatch trace and a git-history
  reprocessing-history trace) whose individual conclusions were each internally consistent but disagreed with each other
  once compared side by side. No files edited; no writes to any bucket.
- **2026-07-26 (slot-11, data_engineering)** — **RESOLVED. Live re-measurement finds the regression has already
  self-cleared** — current count is not just back at the 06-22 baseline, it's well below it. Read-only, single bounded
  read of the consolidated manifest
  (`gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`, via
  `read_availability_index`, column-pruned, no corpus walk), venue=ASTER filtered in-process (879,580 ASTER rows of
  9,157,525 total):
  - **capture_status breakdown**: `empty_confirmed=581,848` · `captured=217,492` · `expected_unattempted=80,090` ·
    **`attempted_failed=150`**.
  - **(a) Reproducibility**: NOT reproducible at the 07-07 magnitude — count is 150, not 17,675 (also below the 06-22
    "recovered" figure of 3,491). The turbo API itself wasn't reachable from this dev worktree (no deployed service
    listening), so this is a direct manifest read rather than the literal HTTP query — same underlying data source the
    turbo endpoint reads from, per `deployment-api/services/data_status/coverage_metrics.py`'s
    `compute_failure_pillar_counts` (buckets `attempted_failed` rows by `error_reason` prefix; unmatched →
    `failed_other`).
  - **(b) Same-rows-as-incident check**: **NO** — all 150 `attempted_failed` rows carry
    `error_reason = "UNCLASSIFIED:UpstreamTimestampBiasError"` and `attempted_at` timestamps clustered at
    **2026-07-25T01:44:39 UTC** (a single tight batch, not spread over months). This is NOT the 2026-05-13
    base-URL/connection-failure class the original incident hit (that would show as a `VENUE_FETCH_FAILED`-style network
    error, not a timestamp-bias data-quality error), and the timestamps are recent (yesterday relative to this read),
    not stale May rows carried forward. So neither of the todo's two anticipated branches applies as literally worded:
    this is not "the same stale rows" (ruled out by both error class and timestamp), and it is also not a "genuinely new
    adapter break" in the sense the todo meant (a fresh large-scale failure needing diagnosis) — 150 rows is 0.017% of
    ASTER's 879,580 total rows, a negligible, already-past, single-batch blip in an unrelated typed-error class.
  - **(c) Manifest-rebuild-in-window check**: a scoped listing of the bucket's `_index/` prefix (single shallow prefix,
    not a corpus walk) confirms MULTIPLE manifest rebuild/snapshot events occurred in the 06-22→07-07-adjacent window
    that could match the doc's own "stale re-read after rebuild" hypothesis —
    `_index/snapshots/pre_mvp_reclassify_20260623T170449Z.parquet`,
    `_index/snapshots/pre_mvp_reclassify_20260623T182306Z.parquet`,
    `_index/snapshots/pre_notlisted_purge_2026_06_24.parquet`,
    `_index/snapshots/pre_futures_chain_reclass_20260703.parquet` all exist. This is consistent with — but not
    conclusive proof of — the hypothesized mechanism; reading each snapshot's ASTER-specific content to pin the exact
    trigger was not done, since it's moot: whatever happened, the live count has since fully recovered (below baseline)
    with no further action needed. Sub-check (c) is closed as "plausible mechanism present, not further pursued —
    non-blocking" rather than "conclusively proven," consistent with the DIAG todo's own stated done-when ("root cause
    need not be conclusively identified — the deliverable is the evidence").
  - **Resolution**: Done-when criterion (i) is met — "the count is back down near the 2026-06-22 baseline (~3,491, not
    17,675)" — 150 is well below 3,491. No recovery mechanism run (nothing to recover — already healthy). No new issue
    doc filed (150 rows in a data-quality typed-error class is not a genuine new adapter break worth a fresh P0/P1 doc;
    noted here for visibility only). `status:` flipped to `resolved`.
  - No writes to any bucket or manifest row; no code changed; no VM launched.
