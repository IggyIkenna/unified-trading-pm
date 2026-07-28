---
doc_type: issue
title: PYTH oracle_prices — 830 stale ghost `attempted_failed` manifest rows survive a successful re-run
summary:
  Post-re-run manifest verification for the PYTH oracle_prices aiodns-fix backfill found 831 attempted_failed rows (not
  the expected 0); 830 are stale day-level ghost failures from before the fix, never superseded by the fixed writer's
  per-instrument-granularity captures for the same dates — a manifest-hygiene phantom-row bug, not a live data gap.
  Proposes extending reconcile_phantom_manifest_rows_all.py to cover this mirror-image case.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service, market-tick-data-service]
scope: [engineer]
tags: [manifest, phantom-row, data-hygiene, oracle_prices, pyth]
related:
  [/plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md, /codex/02-data/availability-manifest-and-data-status.md]
created: 2026-07-28
author: slot-7 (data_engineering)
source: ["mvp_backfill_defi_onchain_v10-002 verification, 2026-07-28"]
assigned_vm: NA
execution_scope: local-only
priority: P2
parent_epic: infrastructure_master
resolved_by:
locked_by:
---

## What I found

The `mvp_backfill_defi_onchain_v10_2026_06_27.md` plan's P1 todo ("Re-run PYTH `oracle_prices` for the
2023-10-01→2026-07-22 date range now that `market-tick-data-service@533514c2` [the aiodns-fallback fix] is shipped")
launched `mtds-pyth-archive-20260727-144533` (2026-07-27T14:45Z), which ran to completion successfully: `exit_code=0`,
`DEPLOYMENT_COMPLETED`, self-deleted per `VM_SHUTDOWN_ON_COMPLETION=true`, log confirms it processed through the full
range including the final day (2026-07-22) with real writes.

**Post-run manifest measurement
(`gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`, scoped read
`venue=PYTH, data_type=oracle_prices`)**:

| capture_status   |  count |
| ---------------- | -----: |
| captured         | 11,277 |
| empty_confirmed  |    442 |
| attempted_failed |    831 |
| **total**        | 12,550 |

The plan's stated gate was "the 1,026 legacy `attempted_failed` rows converted to `captured`/`empty_confirmed`" — this
is NOT met at face value (831 ≠ 0). Digging into the 831 residual:

- **830 of 831** carry `error_reason = "Resolver requires aiodns library"` — the EXACT pre-fix error, which should be
  impossible post-fix.
- **All 830** have `instrument_id = None` (a day-level failure entry, not per-instrument) and `attempted_at` **BEFORE**
  this VM's run window (2026-07-27T14:45Z–2026-07-28T00:26Z) — i.e. these rows were NEVER TOUCHED by the successful
  re-run, despite the re-run unconditionally re-processing every day in the target range (no skip-if-captured logic
  exists on this handler, confirmed by the prior session).
- For every sampled date among the 830, **14 legitimately `captured` per-instrument PYTH rows already exist for that
  same date** — written by this run (or an earlier successful run). Example: `date=2024-04-30` has 1 stale
  `attempted_failed` (instrument_id=None) row AND 14 `captured` rows.
- The 1 remaining residual row (not aiodns) is `PYTH_HERMES_HISTORICAL_HTTP_520` for `date=2025-08-08`,
  `attempted_at=2026-07-27T21:11:59Z` — genuinely occurred DURING this run, a transient upstream 5xx, trivial to retry
  separately (not part of this finding's root cause).

## Why it matters

This is a **manifest-hygiene / phantom-row bug**, not a live data gap — the actual PYTH oracle_prices data for all 830
affected dates IS captured (14 instruments/day). But the manifest still carries a stale day-level `attempted_failed`
ghost row for each date because the failure was originally recorded at day-granularity (`instrument_id=None`) while the
fixed writer succeeds at per-instrument granularity — different shard-key components mean the old row is never
overwritten/superseded, it just sits there forever as a second, contradictory entry for the same date.

This blocks: (1) the plan's own gate from ever reading 0 attempted_failed for PYTH oracle_prices without a targeted fix
(any future re-run will hit the exact same non-skip-if-captured unconditional re-fetch and still leave the ghost rows
untouched, since the writer never deletes/supersedes them); (2) any downstream consumer trusting
`capture_status=attempted_failed` as "this date has no usable PYTH oracle data" — which is FALSE for these 830 dates.

`reconcile_phantom_manifest_rows_all.py` (the existing phantom-row reconciler in this repo) does **not** cover this case
— its own docstring states "Idempotent: `attempted_failed` rows are skipped, real captures are left at `captured`, only
true phantoms [captured-but-no-file] get flipped." This finding is the mirror-image case (a phantom `attempted_failed`,
not a phantom `captured`) and needs a distinct reconciliation pass.

## Recommended decision

Extend `reconcile_phantom_manifest_rows_all.py` (or write a sibling script following its exact safety pattern —
staleness guard via `merge_canonical_with_outstanding_shards`, identity-key relocation before write, dry-run first) to
also detect and flip **stale day-level `attempted_failed` rows** (`instrument_id=None` or absent) where a `captured` row
already exists for the same `(date, venue, data_type)` with a real `instrument_id` — i.e. the failure was superseded by
a later successful per-instrument capture. Flip these to a status consistent with the sibling captured rows (or delete
the redundant day-level entry — needs a design call on which is more consistent with the manifest's schema v9
semantics).

**Scope check before generalizing**: this was found for `PYTH oracle_prices` specifically (day-level-vs-per-instrument
granularity mismatch is a DeFi oracle-handler pattern); confirm whether other DeFi handlers with the same
`shard_exists_prefix`-disabled dead-stub pattern (already flagged as its own P3 todo in the parent plan) exhibit the
same day-vs-instrument granularity split before assuming this generalizes beyond PYTH.

- [ ] [SCRIPT] P2. Extend `reconcile_phantom_manifest_rows_all.py` (or a sibling script, same safety pattern) to
      detect + flip stale day-level `attempted_failed` rows (`instrument_id=None`) superseded by a later `captured` row
      for the same `(date, venue, data_type)` with a real `instrument_id`. Scope to `defi/PYTH/oracle_prices` first (830
      known rows); dry-run and manually verify a sample before any `--apply`. Repo: `instruments-service`.
- [ ] [DATA] P2. Once the reconciler lands, re-measure PYTH oracle_prices coverage
      (`measure_honest_coverage.py --asset-group defi`, scoped read on `venue=PYTH, data_type=oracle_prices`) and flip
      `mvp_backfill_defi_onchain_v10-002`'s original checkbox citing the post-cleanup before/after counts.
- [ ] [SCRIPT] P3. Retry the single `PYTH_HERMES_HISTORICAL_HTTP_520` residual (`date=2025-08-08`) — transient upstream
      5xx, unrelated to the aiodns root cause. Repo: `market-tick-data-service`.
