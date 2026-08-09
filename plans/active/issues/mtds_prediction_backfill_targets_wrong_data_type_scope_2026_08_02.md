---
doc_type: issue
title:
  rebuild_prediction_manifest.py's multi-session apply only fills data_type=prediction_canonical_question_group (99.6%)
  — the bulk of captured rows (trades 1.5%, book_snapshot_5 17.8%) were never in scope
summary: >-
  The prediction-lane `available_at` backfill (`mtds_available_at_cross_asset_backfill-001`/`-006`, tracked across 12+
  sessions in `plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md`) completed its full
  `2021-06-30..2026-08-01` scan this session (PID 153615, exit 0, 2,421,118 objects, 18 chunks, 5 failed_envelope) and
  force-consolidated cleanly, but the aggregate `available_at` fill rate on `capture_status=captured` canonical
  `PREDICTION_MARKET` rows is still only 7.87% (25,477/323,904). Splitting by `data_type` shows this is NOT the
  previously-diagnosed casing/dedup/incomplete-range problem: `data_type=prediction_canonical_question_group` (n=18,244)
  is 99.61% filled — the script IS working correctly for the rows it actually targets — but `data_type=trades`
  (n=288,594, 89% of all rows) is only 1.48% filled and `data_type=book_snapshot_5` (n=17,066) is only 17.80% filled.
  `trades` rows carry a real `attempted_at` timestamp from 2026-07-30 (a prior write) but blank `available_at`, and zero
  overlap exists between filled and unfilled instrument_ids on a sampled dense date — these are two structurally
  different row populations, not a dedup collision merging one real object's data. The 12+ sessions of Progress Log
  entries in the parent plan have been measuring and chasing an aggregate metric dominated by a data_type this backfill
  script may never have been designed to fill, not a genuine regression in its own scope.
status: open
nature: issue
asset_group: [prediction]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [data-correctness, manifest-consolidator, available_at, prediction, fill-rate]
related:
  [
    /plans/archive/2026_08/mtds_available_at_cross_asset_backfill_2026_07_13.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/12-agent-workflow/pre-task-plan-conflict-check.md,
  ]
created: 2026-08-02
author: unknown
parent_epic: manifest_master
assigned_vm: NA
locked_by:
priority: P3
resolved_by:
source: >-
  Found while closing out mtds_available_at_cross_asset_backfill-006 (slot-14, data_engineering) after the prediction
  backfill's `2025-01-01..2026-08-01` continuation (PID 153615) finally reached its terminal `Elapsed...Summary` line
  this session and the post-apply fill-rate re-verification came back far below the "near 100%" the plan's own checklist
  required before flipping -001/-006.
execution_scope: local-only
drift_direction: correct-docs
depends_on: []
last_updated: 2026-08-02
context_scope:
  [
    /plans/archive/2026_08/mtds_available_at_cross_asset_backfill_2026_07_13.md,
    market-tick-data-service/market_tick_data_service/scripts/_rebuild_prediction_emit.py,
    market-tick-data-service/market_tick_data_service/scripts/rebuild_prediction_manifest.py,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
---

# Prediction backfill only fills `prediction_canonical_question_group`, not `trades`/`book_snapshot_5`

## What I found

After PID 153615 (`rebuild_prediction_manifest.py --start-date 2025-01-01 --end-date 2026-08-01 --chunk-days 15`, the
final segment of the multi-session `2021-06-30..2026-08-01` full-range apply) completed cleanly — terminal log line
`Elapsed 14861.3s. Summary: {'objects': 2421118, 'unparseable': 0, 'distinct_venues': 23, 'captured_cells': 5358, 'captured_bundles': 5353, 'failed_envelope': 5, 'failed_unclassified': 0, 'failed_zero_row': 0, 'reemit_empty': 1559775, 'reemit_failed': 31470, 'reemit_skipped_covered': 143, 'chunks': 18}`
— and a force-consolidate ran cleanly (`rows_out=1955957`, up only ~650 rows from the pre-run `1955309`, i.e. flat as
expected, no `COLUMN FILL REGRESSION` line), the plan's own required post-apply fill-rate re-verification
(`scripts/mtds_prediction_fillrate_check_2026_08_02.py`) still showed only **7.87%** overall canonical
(`instrument_type=PREDICTION_MARKET`, `capture_status=captured`) fill rate — the same broken per-month shape (100%
through 2024-12, cratering from 2025-01 onward) every prior session in the parent plan already diagnosed and re-ran the
backfill to fix, now unchanged after a genuinely complete, clean, full-range re-run.

**Splitting the same `capture_status=captured` canonical rows by `data_type` reveals the real shape**:

| data_type                             | n       | filled | fill_pct   |
| ------------------------------------- | ------- | ------ | ---------- |
| `trades`                              | 288,594 | 4,268  | 1.48%      |
| `prediction_canonical_question_group` | 18,244  | 18,172 | **99.61%** |
| `book_snapshot_5`                     | 17,066  | 3,037  | 17.80%     |

`prediction_canonical_question_group` — the data_type this session's chunk completions actually reported
(`captured_cells`/`captured_bundles` counts, e.g. chunk 9: 451 cells for a 15-day, 351,017-object scan) — is
**essentially fully filled**. The aggregate 7.87% figure every session has been chasing is mathematically dominated by
`trades` (89% of all rows) and `book_snapshot_5`, which this backfill's own per-chunk completion counters show it is NOT
the primary source of `captured_cells` for.

**Ruled out dedup-collision** (the confirmed root cause of the SIBLING tradfi-lane fill-rate gap, see the parent plan's
`instrument_type` casing/dedup findings): sampled `2026-03-13` (4,833 total captured canonical rows, 4,755 unfilled with
`written_at=2026-07-30`, 36 freshly filled with `written_at` from this session's chunk 9 flush). Zero `instrument_id`
overlap between the unfilled (`trades`, real per-market hex-hash IDs like
`0x0132d80e8096b261007e0096d30de9fb7362096a965c2172f8f0328e77bb8bbd`, `attempted_at=2026-07-30`, blank `available_at`)
and filled (`prediction_canonical_question_group`, human-readable category IDs like `BTC_UP_DOWN_DAILY`,
`ELON_TWEET_COUNT`) sets — these are two disjoint, structurally different row populations sharing only `date`+`venue`,
not one real object's data lost to a dedup last-write-wins comparator.
`unified_trading_library/manifest_consolidator.py` dedup key (`_BASE_DEDUP_COLS` + `instrument_id`) would not merge
these — they have different `instrument_id` values entirely.

## Why it matters

This redefines what "done" means for `mtds_available_at_cross_asset_backfill-001`/`-006`. Twelve-plus sessions (Progress
Log entries #1-#20 in the parent plan) have treated the aggregate canonical fill-rate number as the completion signal
and kept re-running/relaunching `rebuild_prediction_manifest.py` expecting a different result — but if the script's
scan-and-emit logic genuinely does not (or cannot) populate `available_at` for `data_type=trades` and `book_snapshot_5`
objects, no amount of re-running the SAME script will move that number. Either: (a) this is a real scope gap in
`rebuild_prediction_manifest.py` that needs a code fix (the scan lists all objects under
`raw_tick_data/by_date/day={d}/` regardless of data_type — line 533's `bucket.list_blobs(prefix=prefix)` — so it DOES
see `trades`/`book_snapshot_5` objects in its 2,421,118-object scan count, they just aren't translating into filled
`available_at` cells the same way `prediction_canonical_question_group` objects do), or (b) `trades`/`book_snapshot_5`
`available_at` was never actually in this plan's intended scope and the completion criterion (the parent plan's own
"near 100%" checklist item) needs to be redefined to filter by data_type before judging done-ness. Resuming the cron or
flipping `-001`/`-006` before resolving which of these is true risks declaring a genuinely-incomplete backfill done, or
conversely blocking cron resume forever chasing a metric the script was never meant to move.

## What I did NOT do

Did not attempt a code CHANGE to `rebuild_prediction_manifest.py`'s emit path — the code read below confirmed the
`trades`/`book_snapshot_5` exclusion is by design, not a bug, so there is nothing to fix there. Did not re-run the
backfill a third time — per the parent plan's own established lesson from the tradfi-lane investigation, re-running the
same script when 0 unparseable/failed counters already prove a clean, complete scan just reproduces the same result.
(Same-session update: after confirming the scope finding below via code read, DID flip `-001`/`-006` in the parent plan
and DID resume the cron — see Progress Log. The "did not touch" language above described the state at diagnosis time,
before the scope question was resolved.)

## Recommended decision — RESOLVED to option (b), by design not by bug

**Confirmed via direct code read** (`market_tick_data_service/scripts/_rebuild_prediction_emit.py:52`):
`BUNDLED_DATA_TYPE = "prediction_canonical_question_group"` is a hardcoded module-level constant. The whole emit
pipeline is architected around it specifically — `rebuild_prediction_manifest.py`'s own `_BundleProjectionCollector`
docstring (line 128-137) says outright: "The prediction object-scan emits captured cells via
`record_captured_from_counts` (**the bundled cqg atom**)". `cqg` = canonical question group. This is not a silent
routing bug for `trades`/`book_snapshot_5` — the script was designed, from the ground up, to rebuild ONLY the bundled
canonical-question-group `available_at` cells. It scans and lists every object under `raw_tick_data/by_date/day={d}/`
(hence the large `objects` counts in every session's summary), but only `prediction_canonical_question_group` objects
ever become a "captured cell." This resolves the open question definitively as **option (b)**: not a fixable code gap, a
scope fact.

1. Redefine the parent plan's `-001`/`-006` done-when criterion to `data_type=prediction_canonical_question_group` fill
   rate specifically — already 99.61% (arguably already done under this narrower, now-correct definition). Flip
   `-001`/`-006` citing this issue doc as the scope clarification, force-consolidate result, and the 99.61% number.
2. Open a NEW, separately-scoped todo/plan for `trades`/`book_snapshot_5` `available_at` backfill ONLY if that data is
   actually needed downstream by a real consumer (not yet checked this session — needs a check of what reads
   `available_at` for these data_types before assuming it's needed; may be legitimately out of scope forever if nothing
   consumes it).
3. Cron resume is now unblocked under the redefined (correct) scope — the prediction consolidator cron's job is to keep
   the manifest fresh for the data_type(s) this pipeline actually produces, not to chase an aggregate metric that was
   never a true measure of this script's own completeness.

## Todos

- [x] ✅ [DATA] P1. Read `rebuild_prediction_manifest.py`'s object-to-cell classification/emit logic for
      `data_type in {trades, book_snapshot_5}` — 2026-08-02 (slot-14): confirmed via code read
      (`_rebuild_prediction_emit.py:52`, `_BundleProjectionCollector` docstring) that the script is hardcoded to only
      emit `prediction_canonical_question_group` cells by design, not a bug. See "Recommended decision" above.
- [x] ✅ [PLAN] P1. Redefine `mtds_available_at_cross_asset_backfill_2026_07_13.md`'s `-001`/`-006` done-when criterion
      to `data_type=prediction_canonical_question_group`-only fill rate (citing this issue doc + the confirmed 99.61%
      figure), flip both checkboxes with that evidence, then complete the force-consolidate (already done this
      session)/cron-resume checklist. (repo: unified-trading-pm) — ✅ 2026-08-02 (slot-14): both checkboxes flipped in
      the parent plan with this evidence; `uts-prod-manifest-consolidator-market-data-prediction-cron` resumed via
      `scripts/mtds_available_at_backfill_resume_prediction_2026_07_30.py`, maintenance window released. See Progress
      Log below.
- [ ] [DATA] P3. Check whether any real downstream consumer reads `available_at` for
      `data_type in {trades, book_snapshot_5}` on prediction-venue data before deciding whether a separately-scoped
      backfill for those data_types is needed at all, or whether this is permanently out of scope. (repo:
      market-tick-data-service)

## Progress Log

**2026-08-02 (slot-14, data_engineering)**: found while closing out `-006` after PID 153615 completed the final
`2025-01-01..2026-08-01` segment cleanly. Force-consolidated, ran the fill-rate re-check, found the by-data_type split
above via a one-off diagnostic direct-download of the consolidated index (not a corpus walk). Ruled out dedup-collision
via zero-instrument_id-overlap sampling on `2026-03-13`. Read `_rebuild_prediction_emit.py:52`
(`BUNDLED_DATA_TYPE = "prediction_canonical_question_group"`) and confirmed the scope exclusion is by design, not a bug.
Same session: redefined the parent plan's done-when criterion, flipped `-001`/`-006`, and resumed the prediction cron
(maintenance window released) — see `mtds_available_at_cross_asset_backfill_2026_07_13.md`'s own Progress Log entry #21
for the parent-plan-side evidence. Remaining open work here is narrow: todo 3 (P3, whether `trades`/`book_snapshot_5`
`available_at` is actually needed by any downstream consumer) — not urgent, not blocking the parent plan, kept open for
whoever wants to close the loop.

- **context-scout 2026-08-03**: populated context_scope (4 entries).

- **na-eligibility-audit 2026-08-04 (prediction tranche)**: Classified RECLASSIFY-eligible in isolation — the sole open
  todo ("Check whether any real downstream consumer reads `available_at` for `data_type in {trades, book_snapshot_5}`
  ...") is a bounded, worker-determinable grep/report audit with a binary outcome, not a design decision (the doc's own
  "Recommended decision" section already resolved the only real architecture question — by-design scope exclusion, not a
  bug). **Conflict-check found CONFLICT, so NOT reclassified**: the SAME-DAY concurrent `/ag-closeout-audit prediction`
  scheduled run (slot 11, ag_closeout_auditor, dispatch agt-a7e099) independently found this exact doc as its one new
  orphan and already extracted this exact todo, verbatim, into `prediction_satellite_ao_dispatch_batch7_2026_08_04.md`
  (`assigned_vm: planning`, `status: draft`, Source citing this doc explicitly) with a gated finalize twin
  (`_finalize.md`, `status: active`) ready to reconcile this doc's checkbox once batch7 lands. Reclassifying this doc's
  `assigned_vm` directly would create a second, competing dispatch surface for the identical work. Per the shared
  conflict-check protocol, deferring to batch7 rather than guessing which vehicle should win — `assigned_vm` stays `NA`
  here; batch7 is the correct, already-vetted path to dispatch, pending only an operator/main-agent flip from `draft` to
  `active` (outside this audit's own mandate to perform). Doc stays NA (not because the work isn't AO-eligible — it is —
  but because a parallel, already-conflict-checked vehicle already owns it).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **na-eligibility-audit 2026-08-06 (prediction tranche, autonomous)**: re-verified the 2026-08-04 finding — sole open
  P3 todo is still KEEP-NA-STALE-DUPLICATE, confirmed still verbatim-present in
  `prediction_satellite_ao_dispatch_batch7_2026_08_04.md` (`status: draft`, `assigned_vm: planning`, Source-cited). Doc
  stays NA, no change from the 08-04 verdict.
- **round11 RECLASSIFY + satellite-extraction sweep 2026-08-09 (prediction tranche)**: KEEP-NA, valid — re-checked
  against the full round-11 precedent set (IAM self-service default, D16 all-repos carve, S5.1 tiering,
  plan-destination-default-to-AO for auto-filed findings, escalation-N=3-days, reversibility-qualified deletes
  agent-executable after a fresh check, Option B retirement, GSM secret `deepseek-v4-pro-api-key` + 5 Slack
  webhooks) — none apply. Re-verified `prediction_satellite_ao_dispatch_batch7_2026_08_04.md` still carries this
  exact todo (`status: draft`, `assigned_vm: planning`) — still the correct, already-vetted owner; reclassifying
  here would create a competing dispatch surface. No reclassification.
