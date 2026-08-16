---
doc_type: issue
title: >-
  A same-day corrective manifest migration over-broadly reclassified 14,112 honest LIVE cefi
  empty windows as attempted_failed, triggering DP-FETCH-009 for depth_of_book_10 (fixed); a
  further 149,309-row batch-side population from the same migration is unverified
summary: >-
  `migrate_cefi_queue_mode_false_empty_confirmed_2026_08_16.py` (issue
  `cefi_queue_mode_tier3_sentinel_false_empty_confirmed_2026_08_16.md`) targeted a BATCH-only
  defect in `sentinels.py::_emit_tier3_for_dt` but matched candidates purely on
  `error_reason=SOURCE_RETURNED_ZERO` + a written_at window, with no `pipeline_mode` filter.
  `SOURCE_RETURNED_ZERO` is ALSO the reason the LIVE `websocket_runner.py::_record_empty_window`
  path writes for a genuinely-quiet WS window — an architecturally separate code path never
  touched by the batch bug. The migration incorrectly swept 14,112 honest live rows (dated
  2026-08-15/16, `pipeline_mode` `live_bybit`/`live_deribit`/`live_okx`/`live_kraken`/
  `live_binance`/`live_mtds_microstructure`) into `attempted_failed`, which — unlike batch —
  has no re-verification mechanism, so they'd have sat permanently mislabeled. This directly
  caused escalation `agt-080d9f` (DP-FETCH-009, cefi/depth_of_book_10, 4038 attempted_failed of
  15952 attempted, 25.3%). Fixed + verified for the live population; the migration's much larger
  batch-side population (149,309 rows across aster/extended/hyperliquid/tardis) was NOT
  investigated here and is flagged as an open follow-up.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [cefi, dp-fetch-009, depth_of_book_10, manifest, empty_confirmed, attempted_failed, data-correctness, corrective-migration]
related:
  [
    /plans/active/issues/cefi_queue_mode_tier3_sentinel_false_empty_confirmed_2026_08_16.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
parent_epic: cefi_master
source: >-
  DP-FETCH-009 escalation agt-080d9f (data_pipeline_failure worker, slot 17, 2026-08-16) —
  CRITICAL DP_RUN_MOSTLY_EMPTY for asset_group=cefi data_type=depth_of_book_10: 4038
  attempted_failed of 15952 attempted (25.3%). Investigation traced every candidate row's
  error_reason to a same-day corrective migration, not a live-capture regression.
assigned_vm: NA
created: 2026-08-16
resolved_by:
locked_by:
locked_since:
priority: P1
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/issues/cefi_queue_mode_tier3_sentinel_false_empty_confirmed_2026_08_16.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    market-tick-data-service/scripts/migrate_cefi_queue_mode_false_empty_confirmed_2026_08_16.py,
    market-tick-data-service/scripts/revert_cefi_live_corrective_migration_overreach_2026_08_16.py,
    market-tick-data-service/market_tick_data_service/live/websocket_runner.py,
  ]
---

# DP-FETCH-009 cefi/depth_of_book_10 — root cause was a corrective-migration scoping overreach

## What I found

Escalation `agt-080d9f` fired DP-FETCH-009 (CRITICAL DP_RUN_MOSTLY_EMPTY) for
`asset_group=cefi data_type=depth_of_book_10`: 4038 `attempted_failed` cells of 15952 attempted
(25.3%), fresh in the last 1 day. A live-manifest read (queried directly, no candidate CSV was
filed with the alert) showed every one of the 4038 rows carried
`error_reason=CORRECTIVE_MIGRATION_queue_mode_tier3_sentinel_no_prior_capture_check_2026_08_16`
— the exact sentinel `migrate_cefi_queue_mode_false_empty_confirmed_2026_08_16.py` stamps.

That migration (see `cefi_queue_mode_tier3_sentinel_false_empty_confirmed_2026_08_16.md`,
status `open`, all 3 P0 todos already closed same-day) was built to correct a confirmed BATCH
bug: `sentinels.py::_emit_tier3_for_dt`'s Tier-3 fan-out decided captured-vs-empty using only
the current run's own in-memory fetch results, never checking the manifest/GCS for a prior
`captured` row — so a transient per-instrument fetch miss could permanently overwrite real data
as `empty_confirmed`. The migration script deliberately scoped its candidate match by
`error_reason=SOURCE_RETURNED_ZERO` alone (no venue/launcher filter), reasoning
(docstring, verbatim): *"any row carrying it in this window, from ANY CeFi launcher, shares the
same code-level defect... since every CeFi backfill routes through this same shared sentinel
function."*

That reasoning is incomplete. `SOURCE_RETURNED_ZERO` (`EmptyConfirmedReason.SOURCE_RETURNED_ZERO`)
is also the reason MTDS's **live** capture path writes for a genuinely-quiet WS window:
`market_tick_data_service/live/websocket_runner.py::_record_empty_window` (when NOT in a
connectivity gap) calls `manifest_recorder.record_zero_rows(reason=SOURCE_RETURNED_ZERO,
was_expected=False, ...)`. This is an entirely separate module from the batch orchestrator's
`sentinels.py` — live and batch never share code per the tier/import architecture — so it was
never touched by the Tier-3 sentinel bug. A live row that genuinely saw zero ticks in a window
(a far-dated illiquid quarterly future is a plausible, honest example) legitimately carries
this exact `error_reason`, and the migration's error-reason-only match swept it up anyway.

**Live-manifest measurement (2026-08-16, this investigation)**: of the migration's 163,421
total touched rows, **14,112 carry a `live_*` `pipeline_mode`** (`live_bybit` 10,256,
`live_deribit` 1,844, `live_okx` 779, `live_aster` 532, `live_kraken` 454, `live_hyperliquid`
221, `live_binance` 18, `live_mtds_microstructure` 8), **dated 2026-08-15/2026-08-16** — not
the original incident's 2020-01-01..2020-09-12 window (`date` value directly confirms this,
ruling out any residual ambiguity). By `data_type`: `depth_of_book_10` 4,038, `trades` 3,417,
`derivative_ticker` 3,190, `book_snapshot_5` 2,938, `liquidations` 529.

The remaining **149,309 rows carry a `batch_*` `pipeline_mode`** (`batch_aster` 62,417,
`batch_extended` 59,317, `batch_tardis` 21,802, `batch_hyperliquid` 5,773) — but even this
population's dates are NOT confined to 2020: a spot-check found `2025-01-01` and
`2026-07-30`..`2026-08-02` dates present, and `batch_aster`/`batch_extended`/`batch_hyperliquid`
were explicitly named in the migration's OWN docstring as an "entirely unrelated launcher"
family from an earlier, deliberately-excluded over-catch pass — yet they're present here too,
matched purely because they also emit `SOURCE_RETURNED_ZERO` for something. Whether these are
correctly captured by the migration (i.e., ALSO produced by the same Tier-3-sentinel-class bug,
via a shared code path this investigation didn't trace) or a second instance of the same
error-reason-collision mistake is **NOT determined here** — see Todo 2.

## Why it matters

The live population has no self-correction mechanism the migration's own justification relied
on ("a corrective re-attempt is self-correcting either way... once the write-side bug is fixed
first" — true for batch's `check_shard_freshness(..., retry_failed=True)` re-verification pass,
NOT true for live, which only ever processes new windows going forward and never revisits a
past `attempted_failed` cell). Left uncorrected, these 14,112 cells would have stayed
permanently mislabeled — corrupting the honest-absence contract for every affected cefi live
data_type indefinitely, and continuing to trip `DP-FETCH-009` (and likely other coverage-rate
consumers) on every future sweep, not just this one.

The unresolved batch-side question (149,309 rows) is a materially larger population than even
the original incident (13,476 rows) — if any meaningful fraction of it shares this same
error-reason-collision mistake rather than the genuine Tier-3-sentinel defect, that's a second,
larger data-correctness regression riding on the same commit.

## What I did

- [x] ✅ [DATA] P1. **Reverted the live-side overreach.** Wrote
      `market-tick-data-service/scripts/revert_cefi_live_corrective_migration_overreach_2026_08_16.py`
      (pyarrow-based, not pandas — the cefi index is 29.9M rows / 43 columns and a full pandas
      read OOMs even at an 18G RSS cap on the shared host; pyarrow's columnar path stayed under
      10G). Scoped to exactly `(capture_status=attempted_failed,
      error_reason=CORRECTIVE_MIGRATION_queue_mode_tier3_sentinel_no_prior_capture_check_2026_08_16,
      pipeline_mode startswith "live_")` → reverted to `(empty_confirmed, SOURCE_RETURNED_ZERO)`.
      Consolidator cron (`uts-prod-manifest-consolidator-market-data-cefi-cron`) confirmed
      PAUSED before the CAS write, RESUMED immediately after. Applied: generation
      `1786899624148135` → `1786921866108814`, 14,112 rows reverted, self-verify 0 remaining.
      **Independently re-verified** (fresh manifest read, not the script's own self-verify):
      generation matches live, 0 rows still carry the migration sentinel under `live_*`, cefi
      `depth_of_book_10` `attempted_failed` count is now 0 (was 4038) —
      **the DP-FETCH-009 condition that fired this escalation no longer holds.**
      **DONE 2026-08-16 — `market-tick-data-service@d0e2194cb6`** (QG green, 235s; landed on
      `live-defi-rollout` via quickmerge, post-push ancestry-verified).
- [ ] [DATA] P1. **Determine whether the 149,309-row batch population (`batch_aster` 62,417,
      `batch_extended` 59,317, `batch_tardis` 21,802, `batch_hyperliquid` 5,773) is correctly
      or also incorrectly caught by the migration.** Not investigated in this session (out of
      scope for a DP-FETCH-009/depth_of_book_10-triggered escalation; needs per-launcher-family
      code reads this worker didn't have budget for). Approach: for each launcher family, trace
      whether its OWN write path shares `sentinels.py::_emit_tier3_for_dt` (the actual buggy
      code) or writes `SOURCE_RETURNED_ZERO` via a separate, correct mechanism (mirroring how
      this doc found live's separate mechanism) — then, for any family found NOT to share the
      buggy path, build the same kind of scoped revert this doc's script demonstrates. The
      presence of 2025/2026 dates (not just the original 2020 incident window) in this
      population is itself a signal worth re-checking, not necessarily proof of a problem.
- [ ] [DATA] P3. Consider whether `migrate_cefi_queue_mode_false_empty_confirmed_2026_08_16.py`
      (still present, not yet deleted per its own `# Delete-when:` header) should be annotated
      with a pointer to this doc's finding, so a future reader of that script doesn't trust its
      "any row carrying this error_reason shares the same defect" claim at face value.

## Progress Log

- 2026-08-16, `data_pipeline_failure` worker (slot 17, escalation `agt-080d9f`): filed after
  root-causing DP-FETCH-009 for cefi/depth_of_book_10 to this corrective-migration overreach.
  Reverted + independently re-verified the live-side population (14,112 rows); the batch-side
  question is left open per findings-triage ("ambiguous → diagnose both sides", not guess).
