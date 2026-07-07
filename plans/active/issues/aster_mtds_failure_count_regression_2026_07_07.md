---
doc_type: issue
title: 'ASTER MTDS attempted_failed count looks regressed back to its pre-fix state: 17,681 -> 3,491 (documented, 06-22) -> 17,675 (live, 07-07)'
summary:
  'The 2026-05-13 ASTER base-URL incident (17,681 attempted_failed rows) was fixed 2026-05-14 and a backfill VM
  demonstrably drove the failure count down to 3,491 by 2026-06-22 (documented in
  cefi_hl_aster_batch_data_gaps_2026_06_22.md). A live API pull on 2026-07-07 for
  service=market-tick-data-service, asset_group=CEFI shows ASTER attempted_failed=17,675 (failure_pillars.failed_other) --
  almost exactly the ORIGINAL pre-fix total, not the improved 3,491. Live-query staleness was independently ruled
  out (from_cache=false, served_from=rollup with a 30-min TTL, verified against the exact same numbers). Not yet
  explained by anything found so far -- filed as its own issue because two independent investigation threads each
  saw one half of this and neither flagged the contradiction.'
status: open
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
source: 'ASTER/CEFI instrument-service data-status audit, 2026-07-07 -- cross-referencing two agent findings that individually looked consistent but disagreed once compared'
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
last_updated: 2026-07-07
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

| Date | Source | ASTER MTDS `attempted_failed` | Confidence |
|---|---|---|---|
| 2026-05-13 | `emerging_perp_venue_adapters_broken_2026_05_13.md` (archived) | 17,681 | documented incident total |
| 2026-05-14 | `instruments-service@163a1daa` / `c0c6593d`, `market-tick-data-service@b3e6df0`/`7d45b21` | — | root-cause fix: ASTER REST base URL corrected to `https://fapi.asterdex.com` |
| 2026-05-16 | `mtds-perp-funding-backfill` VM launch (`deployment-service/scripts/vm/launch-mtds-perp-funding-backfill-vm.sh`) | — | backfill re-fetch launched, covering ASTER 2024-09-25→then |
| 2026-06-22 | `issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md` | **3,491** (captured 16,235) | documented recovery in flight |
| 2026-07-07 (live, this audit) | `GET /api/data-status/turbo?service=market-tick-data-service&asset_group=CEFI` | **17,675** | live pull, verified not stale |

The 06-22 number and the 07-07 number cannot both describe steady, monotonic recovery of the same manifest. Either
something regressed between 06-22 and today, or the two numbers are measuring genuinely different things (a scope
difference, a manifest-source difference, or a re-seed that reset prior progress) that hasn't yet been identified.

## What's been ruled out already

- **Not a stale/cached read.** The live pull's `from_cache` was `false` and `served_from` was `rollup` (a GCS blob
  regenerated every 5 minutes, read-fresh for up to 30 minutes) — independently confirmed by re-running the exact
  query and by the fact every other field in the same payload matched the operator's screenshot to the digit,
  including fields that would have to be current to match (missing-dates list, declared data types).
- **Not the `3bb7acd7` book_snapshot_5/liquidations purge** (2026-07-03, deletes 17,282 rows) — confirmed a
  different, unrelated bug (ASTER capability over-seeding for a data type it never had), of which only 26 were
  `attempted_failed[VENUE_FETCH_FAILED]`, and those were book/liq rows, not the trades/derivative_ticker/perp_funding
  rows the base-URL incident hit.
- **Not Stage 2c's manifest reclassification `--apply`** (`instruments_completion_tracker_2026_07_06.md` Stage 2c) —
  confirmed unchecked / never run, and scoped to 6 different venues (COINBASE-SPOT, COINBASE-FUTURES, BYBIT-SPOT,
  BITFINEX-SPOT, BITGET-SPOT, UPBIT), explicitly excluding ASTER ("HL/ASTER are perp-native → unaffected").

## What's suspicious, not yet confirmed

- `17,675 + 6 (empty_unclassified) = 17,681` — exactly the original 2026-05-13 incident total. That numeric
  coincidence is consistent with either (a) a genuine regression that landed the manifest back near its original
  pre-fix state, or (b) the two data points (06-22's "3,491" and today's "17,675") describing different scopes that
  happen to both round-trip through the same underlying raw incident count for unrelated reasons. Not enough
  evidence yet to call it either way.
- The recovery mechanism documented for 05-16→06-22 was a live re-fetch overwriting old failed rows in place — per
  `emerging_perp_venue_adapters_broken_2026_05_13.md`'s own resolution note, *"the manifest will overwrite
  attempted_failed... via real-fetch behavior. No additional reconciliation needed."* If a later manifest
  rebuild, index regeneration, or catalogue rollup re-read an older/unmerged source after 06-22, that could
  reintroduce the old failed rows without anyone having broken the fix itself.

## Todos

- [ ] [VERIFY] P1. Re-run the exact live query used in this audit
      (`GET /api/data-status/turbo?service=market-tick-data-service&start_date=2018-01-01&end_date=<today>&asset_group=CEFI&include_sub_dimensions=true`,
      inspect `asset_groups.CEFI.venues.ASTER.failure_pillars.failed_other` and `capture_status_counts`) to confirm
      this is still reproducible and not a one-time query artifact.
- [ ] [VERIFY] P1. Pull the raw manifest rows behind the `attempted_failed` count for ASTER (not just the aggregate)
      and check their `error_reason` / timestamps — if they're the SAME rows from the original 2026-05-13 incident
      (not re-attempted since), that points at a manifest-source/index regression rather than a new failure. If
      they carry recent timestamps, that points at a genuinely new, separate failure.
- [ ] [VERIFY] P1. Check whether any manifest index rebuild, consolidation job, or rollup regeneration ran on the
      `market-data-tick-cefi` bucket between 2026-06-22 and 2026-07-07 that could have read a stale or pre-backfill
      source snapshot for ASTER specifically.
- [ ] [SCRIPT] P2. Once root-caused: either re-run the same recovery mechanism (live re-fetch against the corrected
      endpoint) if it's a manifest-source regression, or diagnose a new adapter break if the failed rows are
      genuinely fresh.

## Progress Log

- **2026-07-07** — Filed from the ASTER/CEFI instrument-service data-status audit. Surfaced by cross-referencing
  two independently-run investigation threads (a live-API cache/service-mismatch trace and a git-history
  reprocessing-history trace) whose individual conclusions were each internally consistent but disagreed with each
  other once compared side by side. No files edited; no writes to any bucket.
