---
doc_type: issue
title:
  "CF-8 captured-row targeted backfill (`sports_captured_available_at_targeted_backfill_2026_07_14.py`) drops the
  `timeframe` field, collapsing distinct `odds_horizon_bucket` rows into phantom duplicates instead of superseding them
  — third correctness bug found on this twice-regressed surface, non-destructive but leaves the backfill incomplete"
summary: >-
  Dispatched to execute the operator-approved CF-8 `available_at` captured-row backfill
  (`cf_manifest_audit_first_full_rollup_findings_2026_07_26.md`'s P3 todo). Small-scale (500-row) tests on both surfaces
  looked correct on spot-check. Scaling MDPS to the full ~285K-row backfill (across the per-service_name groups the
  2026-07-14 fix already established) surfaced a NEW bug: `_write_captured_rows()`
  (`market_tick_data_service/scripts/_rebuild_sports_write.py:305-327`) calls `writer.add()` WITHOUT a `timeframe=`
  kwarg. `ManifestWriter.add()` defaults `timeframe: str = ""` when the caller omits it
  (`unified_trading_library/manifest_writer/_writer_ingest.py:74`). For `data_type=odds_horizon_bucket` rows — which are
  legitimately bucketed by a `timeframe` axis (`T-6h`/`T-4h`/`T-10m`/`T-2h`/`T-12h`/`T-24h`/...) — every rewrite
  silently drops this value, so N distinct original rows sharing (date, venue, league_id, data_type, service_name) but
  differing ONLY on `timeframe` all canonicalize to the SAME blank-timeframe row_key on rewrite. Net effect: the rewrite
  does not supersede the row it was meant to fix — it creates a NEW, additional phantom row (timeframe blank) alongside
  the still-unfixed originals. Confirmed via direct row-key diff (see Evidence). NON-DESTRUCTIVE (no original row was
  overwritten or deleted — the bug is "backfill doesn't work as intended", not "backfill corrupts existing data" — a
  materially less severe class than the two prior real regressions on this exact surface), but it does mean today's
  backfill attempt did NOT complete and left ~26,982 phantom timeframe-blank rows in the MDPS canonical. Stopped
  immediately on discovery; both maintenance windows released, both crons resumed; did not attempt the IS-surface full
  backfill or the CF-3/CF-4 cleanup given the shared buggy write path.
status: open
resolved_by:
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [data-correctness, cf-8, available-at, sports, manifest-writer, row-key, timeframe, regression]
related:
  [
    /plans/active/issues/sports_cf8_available_at_backfill_regression_2026_07_13.md,
    /plans/active/issues/cf_manifest_audit_first_full_rollup_findings_2026_07_26.md,
  ]
created: 2026-08-15
author: data_engineering (slot-2)
priority: P0
source: "cf_manifest_audit_first_full_rollup_findings_2026_07_26.md P3 todo dispatch, slot 2, 2026-08-15"
parent_epic: infrastructure_master
assigned_vm: NA
locked_by:
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/issues/sports_cf8_available_at_backfill_regression_2026_07_13.md,
    market-tick-data-service/scripts/sports_captured_available_at_targeted_backfill_2026_07_14.py,
    market-tick-data-service/market_tick_data_service/scripts/_rebuild_sports_write.py,
    unified-trading-library/unified_trading_library/manifest_writer/_writer_ingest.py,
  ]
---

# CF-8 captured-row backfill drops `timeframe` — phantom duplicate rows, not a supersession

## What happened

Dispatched to execute the operator-approved (2026-08-11) CF-8 `available_at` captured-row backfill on both sports
surfaces. Followed the doc's own execution notes: acquired the `unified_trading_library.maintenance_window` lease on
both buckets, snapshotted both canonicals before any write, ran a 500-row small-scale test on each surface first,
spot-checked it (looked correct — 2 of a coarse 13-row sample showed the rewrite's fresh `written_at` with filled
`available_at`).

Scaling MDPS to the full backfill (~285,890 rows across the 3 `service_name` groups the 2026-07-14
`_group_target_rows_by_service_name` fix already established) hit repeated shared-host resource issues first (DuckDB's
`temp_directory` defaulting to the host's near-full 8GB tmpfs `/tmp`, then genuine OOM under heavy sibling-slot
contention, then a cross-slot collision — a different slot's independent `gcloud run jobs execute` on the same Cloud Run
consolidator job, which bypasses the Cloud Scheduler-based maintenance-window pause entirely — see "Maintenance-window
gap" below). Working through those, 2 of 3 groups (`market-data-processing-service` 109,312 rows,
`market-tick-data-service` 9,358 rows) were written and folded into the canonical via a real consolidation cycle.

**Then a precise, full-row-key verification (prompted by a suspicious "0 net change" reading on the
`market-data-processing-service` group's aggregate missing-count) surfaced the real bug.**

## Root cause

`market_tick_data_service/scripts/_rebuild_sports_write.py:305-327`, `_write_captured_rows()`:

```python
writer.add(
    processing_date=str(row.get("date", ...) or ""),
    venue=str(row.get("venue") or ""),
    data_type=str(row.get("data_type") or ""),
    league_id=str(row_key_write.get("league_id") or ""),
    instrument_type=str(row_key_write.get("instrument_type") or row.get("instrument_type") or ""),
    instrument_id=str(row.get("instrument_id") or ""),
    underlying=str(row_key_write.get("underlying") or ""),
    chain=str(row_key_write.get("chain") or ""),
    row_count=row_count,
    expected=True,
    available=row_count > 0,
    source=source or None,
    pipeline_mode=mode,
    available_at=_available_at_from_row(row),
    asset_group=asset_group,
)
```

No `timeframe=` kwarg. `ManifestWriter.add()` (`unified_trading_library/manifest_writer/_writer_ingest.py:65-74`)
declares `timeframe: str = ""` — a real, meaningful dimension (used elsewhere, e.g. TradFi OHLCV timeframes), not a
legacy/unused field. Every row `_write_captured_rows()` re-emits therefore gets `timeframe=""` regardless of what the
ORIGINAL captured row's `timeframe` value was.

For `data_type=odds_horizon_bucket` specifically, `timeframe` is NOT incidental — it IS the horizon-bucket axis (`T-6h`,
`T-4h`, `T-10m`, `T-2h`, `T-12h`, `T-24h`, ...). Multiple genuinely distinct captured rows share every OTHER
row-identity column (date, venue, league_id, data_type, service_name) and differ ONLY on `timeframe`. When the backfill
rewrites them, all of them canonicalize toward the same blank-`timeframe` row_key — the rewrite does not know which of
the N originals it's "fixing," so it doesn't fix any of them; it just adds one more row.

## Evidence

Direct row-key diff,
`(date=2020-06-07, venue=ODDS_API, league_id=SUPERLIGA, data_type=odds_horizon_bucket, service_name=market-data-processing-service)`
— 7 rows in the live MDPS canonical sharing this key:

| timeframe | written_at                            | available_at                                                                 |
| --------- | ------------------------------------- | ---------------------------------------------------------------------------- |
| `T-6h`    | 2026-05-05T22:07:40.697143 (orig)     | `None`                                                                       |
| **None**  | **2026-08-15T11:39:52.128293 (mine)** | **2026-05-05T22:07:40.697143** (copied from ONE of the 6 originals, not all) |
| `T-4h`    | 2026-05-05T22:07:40.697138 (orig)     | `None`                                                                       |
| `T-10m`   | 2026-05-05T22:07:40.697115 (orig)     | `None`                                                                       |
| `T-2h`    | 2026-05-05T22:07:40.697132 (orig)     | `None`                                                                       |
| `T-12h`   | 2026-05-05T22:07:40.697121 (orig)     | `None`                                                                       |
| `T-24h`   | 2026-05-05T22:07:40.697127 (orig)     | `None`                                                                       |

Every other differing column across the 7 rows (`instrument_count`, `row_count`) is consistent with these being 7
genuinely distinct captured cells, not accidental duplicates. Full column-diff script output preserved in this session's
Progress Log for reproduction.

## Blast radius

- **MDPS surface** (`market-data-tick-sports-prd`): of 63,223 rows written with a `written_at` timestamp in this
  session's window (2026-08-15T11:0x-2x UTC), 50,571 are `data_type=odds_horizon_bucket` (the affected type) and 12,652
  are `data_type=odds` (a type without a meaningful `timeframe` axis — NOT affected by this bug in the same way, though
  still worth a fresh audit). Of the total, 26,982 rows now show a blank `timeframe` — the phantom rows this bug created
  (a lower bound: this counts landed/consolidated rows only, not everything still sitting in an un-consolidated per-VM
  shard).
- **IS surface** (`instruments-store-sports-prd`): only the 500-row small-scale test was run (via a memory-bounded
  subset-read variant script I wrote, `_sports_is_captured_backfill_from_subset_2026_08_15.py`, same underlying
  `_write_captured_rows()` call — same bug applies). The full ~458K-row IS backfill was **NOT attempted** once this was
  found.
- **CF-3/CF-4 legacy-row cleanup** (the 3,833 `data_type=trades` rows on `instruments-store-sports-prd`, also part of
  this todo's scope): **NOT attempted** — out of caution once a new correctness bug surfaced on the sibling backfill in
  the same dispatch.

## Why this is NON-destructive (materially different from the 2026-07-13 regression)

The prior regression (`sports_cf8_available_at_backfill_regression_2026_07_13.md`) actively OVERWROTE/lost
previously-correct `available_at` values via a full `--force` corpus rebuild. This bug is different in kind: the rewrite
is additive (a new row_key, new row) — it does not touch, dedupe-supersede, or delete any of the original rows sharing
its coarse identity. Every one of the 7 example rows above still exists with its original content intact. The cost here
is (a) the intended fix didn't land for ~5 of every 6 target `odds_horizon_bucket` rows, and (b) the canonical now
carries some thousands of extra, malformed (blank-`timeframe`) rows that need a cleanup pass.

## Secondary finding — maintenance-window gap (direct Cloud Run job execution bypasses the scheduler pause)

While diagnosing an unexplained recurring lock-collision during this session, found a live
`gcloud run jobs execute uts-prod-manifest-consolidator-market-data-sports --wait` process (a DIFFERENT slot, working an
unrelated task, `sports_p2_raw_tick_live_writer_still_emits_trades-...`) running concurrently against the SAME bucket my
maintenance window was supposed to be protecting. `scheduler_maintenance.py`'s `pause_for_maintenance()` only pauses the
Cloud SCHEDULER trigger (`scheduler_v1.CloudSchedulerClient.pause_job`) — it has no way to prevent a DIRECT
`gcloud run jobs execute <job-name>` invocation, which bypasses the scheduler entirely and goes straight to Cloud Run.
This is a real gap in the exact mechanism Finding 1 of the 2026-07-13 doc built to close the cron-collision problem — it
closes the SCHEDULED-trigger collision class but not the direct-invocation one. Not root-caused/fixed here (out of this
issue's scope); flagged as a follow-up todo below.

## What I did (in order)

1. Confirmed the plan's operator approval + gate state was current (per the parent todo's own 2026-08-11 note).
2. Snapshotted both canonicals before any write
   (`_index/snapshots/pre_cf8_captured_backfill_20260815T11085{9,05}Z.parquet`).
3. Ran dry-runs on both surfaces to confirm scope (MDPS 285,968 missing → IS 15.7M-row full index exceeded safe
   direct-host memory bounds; wrote a memory-bounded row-group-streamed variant,
   `_sports_is_captured_stream_read_2026_08_15.py`, to read IS's captured-only subset without materializing the whole
   15.7M-row corpus).
4. Small-scale (500-row) `--no-dry-run` test on both surfaces, spot-checked, looked correct on a coarse sample.
5. Scaled MDPS toward the full backfill — hit and worked through (a) DuckDB temp-dir exhaustion on the host's near-full
   tmpfs `/tmp` (fixed via `TMPDIR=<real-disk-path>`), (b) genuine host-memory contention (fixed via
   `run-bounded-analysis.sh` RSS caps, retried across several host-load windows), (c) the cross-slot
   `gcloud run jobs execute` collision above.
6. A precise full-row-key re-verification (prompted by a "0 net change" aggregate anomaly) surfaced the `timeframe`-drop
   bug documented above.
7. **Stopped immediately.** Released both maintenance windows, resumed both Cloud Scheduler crons
   (`uts-prod-manifest-consolidator-market-data-sports-cron`, `uts-prod-manifest-consolidator-instruments-sports-cron`).
   Did not attempt the IS full backfill or the CF-3/CF-4 cleanup.

## Todos

- [x] [DATA] P0. Fix `_write_captured_rows()` (`market-tick-data-service/scripts/_rebuild_sports_write.py:305-327`) to
      thread `timeframe=str(row.get("timeframe") or "")` through the `writer.add()` call, so a rewrite carries the
      original row's real timeframe value instead of defaulting to blank. Add a regression test proving a
      multi-timeframe `odds_horizon_bucket` group re-emits N distinct rows (one per original timeframe), not one phantom
      blank-timeframe row. Needs review given this surface's 2 prior real regressions — small-scale test first, matching
      this doc's own established protocol. (repo: market-tick-data-service) — ✅ **LANDED**:
      `market-tick-data-service@e0b34e77fd` (fix + 2 regression tests
      `test_write_captured_rows_threads_original_timeframe_through`,
      `test_write_captured_rows_blank_timeframe_row_stays_blank` in
      `tests/unit/scripts/test_rebuild_sports_manifest_v9.py`), confirmed an ancestor of `origin/live-defi-rollout` via
      `git merge-base --is-ancestor e0b34e77fd origin/live-defi-rollout` (exit 0) and
      `git rev-list --count origin/live-defi-rollout..HEAD` = 0. Note: the sha churned from the original local commit
      `1c9a7858` to `e0b34e77fd` — quickmerge amended HEAD to add the missing `Quickmerge: agent` trailer before pushing
      (content unchanged, not a rebase this time), exactly the kind of sha drift this doc's own note warned about.
      `quality-gates.sh` was GREEN (10865 passed, 0 failed) before commit.
- [x] [DATA] P0. **NARROWED per 2026-08-15 FULL-POPULATION audit (see Progress Log) — do NOT blanket-delete.** (a) is
      now DONE: of the live 14,330 in-window phantom rows (full population, not sampled — confirmed exact, matching the
      200-sample extrapolation), 959 (6.69%) have NO non-blank-timeframe sibling under their coarse
      (date,venue,league_id,data_type,service_name) key — deleting THOSE would be destructive, contradicting this doc's
      original "NON-destructive" claim for that subset. Refined finding:
      `league_id=LA_LIGA_2, service_name=market-data-processing-service` accounts for 872/959 (91%) of no-sibling rows,
      and — cross-checked against the blast-radius breakdown — LA_LIGA_2's phantom-population count is ALSO exactly 872,
      meaning 100% of LA_LIGA_2's phantom rows lack a sibling (not the 92% the 200-row sample suggested). The remaining
      87 no-sibling rows spread thinly across ~20 other minor leagues (SOCCER_RUSSIA_PREMIER_LEAGUE 22,
      SOCCER_AUSTRALIA_ALEAGUE 12, SOCCER_SWITZERLAND_SUPERLEAGUE 9, ... all ≤9 each), ALL on
      `market-data-processing-service`, none observed on IS. (b) is now DONE — **CONFIRMED root cause (2026-08-15,
      direct query against the live manifest, not just correlation)**: the original hypothesis label
      ("single-horizon-bucket league") was imprecise; the actual mechanism is TEMPORAL, not bucket-count. Queried
      `read_availability_index_safe` directly for LA_LIGA_2 + 3 sampled minor leagues (SOCCER_RUSSIA_PREMIER_LEAGUE,
      SOCCER_AUSTRALIA_ALEAGUE, SOCCER_SWITZERLAND_SUPERLEAGUE — 915/959, 95% of the no-sibling population): for ALL 4,
      the (date,venue) keys carrying the phantom blank-timeframe rows have ZERO overlap with the (date,venue) keys that
      ever carry a non-blank timeframe value for that league. LA_LIGA_2's real timeframe-labeled rows (`15m`/`1h` — a
      DIFFERENT vocabulary than the `T-6h`-style buckets seen elsewhere) only exist from 2026-03-28 onward; its 872
      phantom rows span 2020-06-12..2026-02-20, entirely before that. The 3 sampled minor leagues have ZERO
      non-blank-timeframe rows at ANY date — `timeframe` has never been populated for their `odds_horizon_bucket`
      captures. Conclusion: these rows were NOT genuinely multi-timeframe originals that lost data — their pre-existing
      captured row already had blank `timeframe` (this predates the 2026-08-15 bug entirely), so the backfill's
      blank-timeframe rewrite is a correct same-row_key supersession, not a duplicate. "No sibling" is therefore not a
      warning sign here — it's expected, because there was never a second row to begin with. These 959 rows are safe to
      LEAVE AS-IS (already excluded from delete scope below) and this exclusion is now evidence-backed, not merely
      cautious. (c): exclude every no-sibling row (959, enumerated by date/venue/league_id/service_name in the retry
      audit log) from delete scope entirely (leave those as-is) — no further action needed on this sub-step, the
      confirmation above IS the justification. ✅ **EXECUTED 2026-08-15**: dry-run-verified on VM first (category
      `sports-cf8-tf-delete` added to `deployment-service/scripts/vm/launch-canonical-migration-vm.sh`,
      `deployment-service@f827fad297`), then a live `--confirm-prod-write` run on VM
      `canonical-migration-sports-cf8-tf-delete-20260815-214633` (per the workspace hard rule, this class of write
      never runs on a laptop). Pre-write snapshot:
      `gs://market-data-tick-sports-prd-central-element-323112/_index/snapshots/pre_cf8_phantom_timeframe_delete_20260815T215119Z.parquet`.
      Result: base=6,252,484 rows → removed 13,371 sibling-confirmed phantom blank-timeframe rows (959 no-sibling rows
      left as-is, per (b) above) → post-write base_rows=6,239,113 (exactly matched the expected count) →
      `>>> VERIFY PASSED`, exit 0. Full log:
      `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-sports-cf8-tf-delete-20260815-214633/run.log`.
      IS sub-step **DONE (2026-08-15)**: audited via
      `audit_sports_is_captured_phantom_timeframe_2026_08_16.py` (memory-bounded, row-group-streamed — IS's 15.7M-row
      index OOMs a naive full read). Answer to the literal question ("does the same phantom-row class exist on IS")
      is yes, trivially — but the real population found is **899,508 rows (84% of ALL IS odds_horizon_bucket data)**,
      ~1800x larger than the 500-row test and NOT explained by it (78.8% of the population was written 2026-08-08/09,
      before this session started). Root cause NOT confirmed to be this same CF-8 bug — filed as its own doc rather
      than folded in here, since it's plausibly a distinct/older writer-path issue, not this doc's narrow
      `_write_captured_rows()` regression:
      `/plans/archive/2026_08/issues/sports_is_odds_horizon_bucket_blank_timeframe_odds_api_dominant_2026_08_15.md`. (repo:
      market-tick-data-service, unified-trading-library)
- [x] [DATA] P1. **NEW finding, 2026-08-15 audit**: 14,982 blank-`timeframe` `data_type=odds_horizon_bucket` rows exist
      on MDPS OUTSIDE the session's 2026-08-15T11:0x-2x UTC window (i.e. NOT created by this session's bug) — a
      population almost as large as the in-window one, previously unknown. Root-cause: are these from an earlier,
      unrelated blank-timeframe write path (a different bug), or a legitimate case where `timeframe` is genuinely blank
      for some `odds_horizon_bucket` rows? Do not assume same disposition as the in-window population without
      independent investigation. (repo: market-tick-data-service) — ✅ **ROOT-CAUSED 2026-08-15** (extended
      `audit_sports_captured_phantom_timeframe_2026_08_16.py`): 100% venue=ODDS_API (14,982/14,982), `written_at`
      range [2026-05-05, 2026-07-13], overwhelmingly concentrated on 2026-07-13 (14,656 rows — one of the 5 known
      spike dates) with a small 326-row tail on 2026-05-05. **Sibling check: 0/200 sampled rows have ANY
      non-blank-timeframe sibling** under the coarse (date,venue,league_id,data_type,service_name) key — the OPPOSITE
      of the in-window phantom population (which was 100% sibling-confirmed-safe). This proves the out-of-window
      population is NOT an instance of this doc's `_write_captured_rows()` additive bug (that bug always leaves a
      sibling; this population never does) and it predates the 3 fix commits (2026-08-15 15:07-17:21 UTC) by over a
      month, so it cannot be that bug's output either way. Deleting these WOULD be destructive — excluded from all
      cleanup scope, no write attempted. Shape (100% ODDS_API, zero siblings) matches
      `/plans/archive/2026_08/issues/sports_is_odds_horizon_bucket_blank_timeframe_odds_api_dominant_2026_08_15.md`'s IS-surface
      finding (899,508 rows, 99.8% ODDS_API, also 0/899,508 sibling-confirmed on a full-population check) almost
      exactly — both surfaces show the same ODDS_API-specific, no-sibling, blank-`timeframe` pattern on different
      dominant dates, pointing to a shared structural/writer-path cause independent of this session's bug rather than
      two coincidentally-similar separate issues. Cross-referenced into that doc's todo #4. Deployment-archive +
      Cloud Logging checks (that doc's todo #2) found no launched-job execution explaining either population — see
      that doc for the evidence. No cleanup action taken; this todo is root-cause-only, a follow-up cleanup-scope
      decision is a new, not-yet-filed item since it needs a genuine root cause first, not just this negative
      evidence. (repo: market-tick-data-service)
- [ ] [DATA] P1. Once the fix + cleanup above are done, re-attempt the full CF-8 captured-row backfill on BOTH surfaces
      (MDPS ~285K rows minus whatever the 2 already-landed groups covered correctly; IS ~458K rows) plus the bundled
      CF-3/CF-4 legacy-row cleanup (3,833 rows) — this is the ORIGINAL scope of
      `cf_manifest_audit_first_full_rollup_findings_2026_07_26.md`'s P3 todo, not yet completed. Reuse the
      memory-bounded helper scripts this session added (`_sports_is_captured_stream_read_2026_08_15.py`,
      `_sports_is_captured_backfill_from_subset_2026_08_15.py`) for the IS surface — they only changed the READ path
      (streaming/filtering), not the write path, so they inherit whatever fix lands on `_write_captured_rows()`
      automatically. (repo: market-tick-data-service)
- [ ] [INFRA] P2. Close the maintenance-window gap: a direct `gcloud run jobs execute <job-name>` bypasses
      `scheduler_maintenance.py`'s pause entirely (it only pauses the Cloud Scheduler trigger, not the Cloud Run job
      itself). Consider either (a) `--wait`-based collision detection/warning when a caller runs
      `gcloud run jobs execute` against a job with a live maintenance window (would need the launcher script or a
      wrapper to check `maintenance_status()` first), or (b) documenting the direct-execution path as "ALSO check
      `--status` before running" in the same places the scheduler pause/resume guidance already lives. Scope/design not
      decided — routing to operator/infra owner. (repo: deployment-service or unified-trading-pm docs)
- [x] [DATA] P2. **Root cause FOUND, 2026-08-15 (slot-2)**: blank-`timeframe` ODDS_API rows are **blank-by-design, not
      a bug**. The live per-date manifest writer `_write_shard_counts_to_manifest`
      (`market_tick_data_service/engine/orchestrator/manifest_finalize.py:323`, invoked from `_write_date_manifest`
      at line 720 — the real always-live capture path, not a rebuild/migration script) never passes `timeframe=` in
      its `venue_writer.add(...)` call (lines 481-497) for the ODDS_API `itype_key=="odds" and data_type_key=="odds"`
      branch (lines 430-443); `ManifestWriter.add()`
      (`unified-trading-library/unified_trading_library/manifest_writer/_writer_ingest.py:75`) defaults
      `timeframe: str = ""`, so every raw `data_type="odds"` ODDS_API row has always been written blank — for the
      entire lifetime of this code path, not a regression. The horizon-bucket/timeframe *concept* only exists for the
      separately-computed `data_type="odds_horizon_bucket"` rollup, built downstream in
      `market-data-processing-service`'s `SportsBucketAssignmentAdapter`
      (`market_data_processing_service/app/adapters/sports/bucket_assignment_adapter.py`) — raw `data_type="odds"`
      captures never carried a timeframe to begin with, which is exactly why zero siblings were ever found (no code
      path has ever written a non-blank timeframe under that coarse key). **Confidence: High** on the mechanism
      (confirmed at both call site and library default); **medium-high** on the "blank-by-design, safe to leave"
      framing — the investigating agent could not directly query the manifest to confirm the 899,508/14,982-row
      population is exclusively `data_type="odds"` rather than partially mixed with `odds_horizon_bucket` rows from a
      different write path (see follow-up P3 below). **Practical conclusion: do NOT delete these rows** — this is
      expected shape for raw ODDS_API captures, not corruption; no cleanup action is warranted absent the P3
      confirmation surfacing a different population mix. RULED OUT (unchanged from prior investigation): this doc's
      own `_write_captured_rows()` bug (fixed `market-tick-data-service@e0b34e77fd`, a different function in a
      v9-rebuild script that only re-threads pre-existing `timeframe` values, never derives new ones) and any known
      launched VM/Cloud Run job — see
      `/plans/archive/2026_08/issues/sports_is_odds_horizon_bucket_blank_timeframe_odds_api_dominant_2026_08_15.md`
      for that evidence trail. (repo: market-tick-data-service)
- [x] [DATA] P3. **Confirm population composition** before fully closing the "safe to leave" verdict above: verify the
      899,508-row IS population and 14,982-row MDPS population sampled for the zero-sibling finding are exclusively
      `data_type="odds"` rows (the structurally-blank-by-design population), not partially mixed with
      `data_type="odds_horizon_bucket"` rows written by a different path — a mixed population would need the
      `odds_horizon_bucket` subset re-examined separately since that data_type's timeframe is NOT structurally blank
      by design. Low urgency: mechanism confidence is already high and no destructive action is pending on this.
      (repo: market-tick-data-service) — ✅ **DONE 2026-08-15/16 — RESULT OVERTURNS P2's "blank-by-design, safe to
      leave" conclusion, does NOT confirm it.** Both populations are, by construction of the very audits that
      measured them, **100% `data_type="odds_horizon_bucket"`, never `data_type="odds"`**: (a) the archived IS-side
      doc (`/plans/archive/2026_08/issues/sports_is_odds_horizon_bucket_blank_timeframe_odds_api_dominant_2026_08_15.md`)
      states its own measurement plainly in its title and body — "`data_type=odds_horizon_bucket` on IS: 1,070,440
      rows total, 899,508 (84.03%) blank-timeframe" — the 899,508-row population was never anything but
      `odds_horizon_bucket`; (b) the MDPS 14,982-row out-of-window population was produced by
      `audit_sports_captured_phantom_timeframe_2026_08_16.py`, which queries
      `read_availability_index_safe(_BUCKET, ..., filters=[("data_type", "==", "odds_horizon_bucket")])` (line 109)
      BEFORE ever slicing into in-window/out-of-window — every row in that population is `odds_horizon_bucket` by
      construction of the query itself, not by later inspection. **This directly falsifies P2's mechanism**: P2's
      cited write path (`manifest_finalize.py::_write_shard_counts_to_manifest`, lines 430-497) is gated on
      `if itype_key == "odds" and data_type_key == "odds":` (confirmed by direct read, 2026-08-16) — it can only ever
      write `data_type="odds"` rows; it categorically cannot produce a `data_type="odds_horizon_bucket"` row, blank
      or otherwise. Whatever P2's write path explains, it is not these two populations. Full-file grep of
      `manifest_finalize.py` (852 lines) confirms **zero** references to `odds_horizon_bucket` anywhere in it — this
      file does not write that data_type at all. **P2's todo above is corrected accordingly** (its own text is left
      intact per this doc's history-preservation convention; this entry is the correction of record). The real
      `odds_horizon_bucket` writer is `market-data-processing-service`'s `SportsBucketAssignmentAdapter`
      (`market_data_processing_service/app/adapters/sports/bucket_assignment_adapter.py:687`, confirmed by direct
      read) — it builds `CandleOutput` objects per horizon bucket but does not itself call `ManifestWriter.add()` in
      that file; the actual manifest `timeframe=` write happens in a caller, not yet traced to completion (see new
      P1 todo below — this is now a genuinely separate, still-open root-cause chase, not resolved by this pass).
      **Practical consequence**: the "no cleanup action warranted" disposition on P2 above is **NO LONGER
      confirmed-safe** — it rested on a mechanism that provably does not apply to either audited population. This
      does not mean the ~914,490 rows (899,508 IS + 14,982 MDPS) ARE unsafe to leave — no destructive action is
      newly indicated by this finding either — but the stated justification for leaving them alone is wrong and the
      disposition is genuinely open again pending the real root cause. Per this workspace's big-finding rule
      (data-correctness, cross-repo doc/SSOT contradiction), flagged to the operator in-chat this session. (repo:
      market-tick-data-service, market-data-processing-service, unified-trading-pm)
- [ ] [DATA] P1. **NEW, 2026-08-16, follow-up to the P3 correction above**: find the ACTUAL root cause of blank
      `timeframe` on `data_type=odds_horizon_bucket` rows (899,508 IS + 14,982 MDPS, both 100% venue=ODDS_API,
      0-sibling). P2's candidate mechanism is now disproven (see P3 above). Lead evidence gathered this pass, not yet
      confirmed: `SportsBucketAssignmentAdapter.supported_timeframes = ["horizon"]`
      (`bucket_assignment_adapter.py:706`) — the adapter's declared timeframe token is the literal string
      `"horizon"`, not a per-row bucket name (`T-6h` etc, which lives in `horizon_idx`/`horizon_name` INSIDE the
      output, not as the top-level `timeframe=` the manifest write presumably uses). MDPS's
      `canonical_writer.py`/`canonical_writer_stamping.py` thread a `timeframe:` parameter through every write via
      `_normalise_timeframe()` (defined `canonical_writer_shaping.py:232`, not yet read) — if that function does not
      recognize `"horizon"` as a valid timeframe token (it appears calibrated for `"1m"`/`"15m"`/`"1h"`/`"1d"`-style
      values per its docstrings), it may normalise to blank, which would produce exactly the observed shape (100%
      blank timeframe, no code path has ever written non-blank). **NOT YET CONFIRMED** — needs (a) reading
      `_normalise_timeframe`'s implementation, (b) tracing the actual caller that invokes
      `SportsBucketAssignmentAdapter` and passes its `timeframe=` argument through to `canonical_writer.py`
      (candidates already found this pass: `live_workers_chain.py`, `canonical_writer.py` itself — grep did not
      isolate the exact call site), (c) confirming venue=ODDS_API specifically routes through this path (vs. the
      ~12 uppercase-bookmaker venues sharing the same blank shape per the archived IS doc — may be the same cause or
      a second one). Do not assume confirmed without doing (a)-(c). (repo: market-data-processing-service)
- [ ] [DATA] P1. **NEW, 2026-08-16, follow-up (b) partial progress on the P1 todo above**: `_normalise_timeframe()`
      (`canonical_writer_shaping.py:232-240`, now read in full) is a trivial passthrough — it only special-cases
      `"24h"` → `"1d"` and returns every other token, including `"horizon"`, unchanged. **This disproves the P1
      todo's leading hypothesis**: `_normalise_timeframe` does NOT blank `"horizon"`. `CandleOutput`
      (`unified_api_contracts.internal`) also carries no `timeframe` field at all — every constructor call site
      (`base_adapter.py::_make_empty_candle_output`/`_make_zero_activity_candle_output`, and
      `SportsBucketAssignmentAdapter.process_to_candles`'s real return) omits it, confirming `timeframe` is threaded
      alongside `candles_df` by the caller, not carried inside it. **New candidate mechanism found**: the caller
      chain is `live_workers_chain.py::_process_all_timeframes` (line 356) → for each `timeframe` in
      `sorted_tfs = sorted(valid_tfs, ...)` where `valid_tfs = adapter.get_valid_output_timeframes(timeframes)`
      (`base_adapter.py:164-174`) → `_write_or_record_empty_timeframe(timeframe=timeframe, ...)` (line 542, body
      unread past line 569). `get_valid_output_timeframes` filters via
      `TIMEFRAME_SECONDS.get(tf, 0) >= base_secs` — **an unrecognized token defaults to 0 seconds**, and the code's
      own comment at that line names this exact defaulting shape as the "confirmed root cause of the 2026-08-12
      liquidations 1d re-derive silent no-op" (a prior, different-timeframe instance of the same class of bug).
      `"horizon"` is very likely not a `TIMEFRAME_SECONDS` key. **Still open, precise next steps**: (i) confirm
      whether `"horizon"` is actually absent from `TIMEFRAME_SECONDS` (definition/import origin not yet located —
      a plain-text grep for its assignment came back empty in this pass, so it's probably re-exported from a shared
      constants module); (ii) read `get_base_granularity()`'s default (`base_adapter.py:155`, not yet read) —
      `SportsBucketAssignmentAdapter` does not override it, so it inherits whatever the base default returns, which
      determines whether `0 >= base_secs` passes or fails for `"horizon"`; if it fails, `"horizon"` is filtered out
      of `valid_tfs` entirely and `_process_all_timeframes` returns early with zero candles written — **this needs
      reconciling against the observed non-empty blank-timeframe row population** (a total-drop wouldn't produce a
      blank-but-present row, so either this filter isn't the actual mechanism, or `base_secs` also resolves to 0 and
      `"horizon"` passes through this filter intact — in which case the string `"horizon"` reaches
      `_write_or_record_empty_timeframe` un-blanked, meaning the blanking happens somewhere in that function's
      unread body (`live_workers_chain.py:542-569+`) or in the canonical-writer call it eventually makes); (iii)
      read that unread body next. Do not assume confirmed without doing (i)-(iii). (repo:
      market-data-processing-service)
- [ ] [DATA] P1. **NEW, 2026-08-16, follow-up (c) — items (i)-(iii) from the todo above, now read**:
      `TIMEFRAME_SECONDS`/`BASE_GRANULARITY_BY_DATA_TYPE` import from `unified_api_contracts.registry`
      (`base_adapter.py:22`) — not readable from this checkout's shell (`unified_api_contracts` not on the bare
      `python3` path; needs the repo's `.venv`, not yet run). `get_base_granularity()`
      (`base_adapter.py:155-161`): priority is a `base_granularity` class attribute (confirmed
      `SportsBucketAssignmentAdapter` does NOT define one — zero grep hits) > `BASE_GRANULARITY_BY_DATA_TYPE.get(
      self.data_type, "15s")`. So if `"odds_horizon_bucket"` is an unregistered key there, `base_secs` resolves via
      the recognized `"15s"` fallback (a real, non-zero `TIMEFRAME_SECONDS` entry), NOT via the same
      defaults-to-0 hole as `"horizon"` itself. That means `get_valid_output_timeframes(["horizon"])`'s check
      `TIMEFRAME_SECONDS.get("horizon", 0) >= base_secs` very likely evaluates `0 >= 15` = **False**, filtering
      `"horizon"` out of `valid_tfs` entirely — `sorted_tfs` would be empty and `_process_all_timeframes`
      (`live_workers_chain.py:356`) returns early with **zero candles written**, not a blank-timeframe row. **This
      contradicts the observed non-empty blank-timeframe population** — so `live_workers_chain.py`'s batch/chain
      path is likely NOT the one producing these rows; the true production entry point for
      `odds_horizon_bucket` is probably `live_workers_streaming.py` (checked this pass — its
      `_streaming_write_per_tf`/`_record_streaming_empty_timeframe` also thread a `timeframe`/`tf` parameter
      straight through to `record_captured`/`record_empty_for_shard`/`record_failed_for_shard`, never re-deriving
      it from `candles_df`, so the same open question applies there too). **Ruled out this pass**: the
      `live_workers_streaming.py:756` comment ("this is the actual root cause of
      mdps_sports_odds_horizon_bucket_candle_write_targets_prod_bucket_2026_08_02.md") is a DIFFERENT, already-fixed
      bug (wrong write-bucket resolution, not a timeframe field) — read in full and confirmed unrelated to this
      todo. **Precise next step, still open**: run inside the MDPS `.venv` to actually read
      `TIMEFRAME_SECONDS`/`BASE_GRANULARITY_BY_DATA_TYPE`'s real values for `"horizon"`/`"odds_horizon_bucket"` (the
      one fact this pass could not directly measure), which resolves whether `get_valid_output_timeframes` filters
      `"horizon"` out (contradicts observed data — wrong mechanism) or passes it through (right track — then trace
      one level further into `_streaming_write_per_tf`'s eventual `record_captured`/writer call to find where the
      string actually goes blank). Do not assume confirmed without running this. (repo:
      market-data-processing-service)
- [x] [DATA] P1. **RESOLVED this pass, 2026-08-16 — MAJOR REDIRECT, overturns the P1 chase above**: ran the
      registry lookup via `market-tick-data-service/.venv/bin/python` (MDPS itself has no `.venv` in this checkout;
      MTDS shares the same `unified_api_contracts` install). Confirmed: `BASE_GRANULARITY_BY_DATA_TYPE.get(
      "odds_horizon_bucket")` = `"15m"` (a real, registered, non-zero-seconds token — NOT the `"15s"` fallback),
      and `"horizon" in TIMEFRAME_SECONDS` = **False** (confirmed absent, defaults to 0 per
      `get_valid_output_timeframes`'s `.get(tf, 0)`). So `get_valid_output_timeframes(["horizon"])` evaluates
      `TIMEFRAME_SECONDS.get("horizon", 0) >= base_secs` → `0 >= 900` (15m in seconds) → **False** —
      `"horizon"` is filtered out of `valid_tfs` entirely. Then also confirmed
      `live_workers_streaming.py:874-875` calls the IDENTICAL `adapter.get_valid_output_timeframes(timeframes)` →
      `sorted_tfs` construction as the chain path (not a different, unfiltered list as hoped). **Conclusion: BOTH
      of MDPS's live-dispatch write paths (`live_workers_chain.py::_process_all_timeframes` AND
      `live_workers_streaming.py`'s streaming equivalent) filter `"horizon"` out before ever reaching a write call
      — neither can produce an `odds_horizon_bucket` row, blank-timeframe or otherwise.** This means the entire
      chase through `live_workers_chain.py`/`live_workers_streaming.py`/`canonical_writer*.py` in the two todos
      above was down the WRONG code path — the ~914,490 observed rows were NOT written by MDPS's standard live
      adapter dispatch mechanism at all. **New, precise next step**: the real writer must be a batch/backfill/
      reprocessing script that calls `SportsBucketAssignmentAdapter.process_to_candles`/
      `process_to_bucketed_df` directly and constructs its own write call, bypassing
      `get_valid_output_timeframes` — strong candidates already named in this doc's own repo (all under
      `market-data-processing-service/scripts/`, none read yet this pass):
      `backfill_odds_horizon_bucket_missing_shards_2026_07_28.py`, `reprocess_sports_odds.py`,
      `reclassify_odds_horizon_bucket_unresolvable_rows_2026_07_28.py`,
      `close_odds_horizon_bucket_expected_unattempted_cells_2026_07_25.py`,
      `migrate_odds_horizon_bucket_venue_to_bookmaker_2026_07_27.py`. Read each for how it calls the adapter and
      what `timeframe` value (if any) it threads into its own write call — one of these is the actual culprit.
      (repo: market-data-processing-service)
- [ ] [DATA] P1. **NEW, 2026-08-16, follow-up — 1 of 5 candidates read, narrows the search**:
      `reprocess_sports_odds.py` (grepped, not fully read) writes REAL per-horizon `timeframe` values — it maps
      `horizon_name` (e.g. `"T-24h"`) straight into its `ManifestWriter.add(...)` call (`timeframe=horizon_name,`
      at line 1226, sourced from a dict built at line 739 per the `horizon_name`→manifest-`timeframe` mapping
      documented at line 726). **This script is very likely NOT the culprit for the FINE (per-league_id,
      per-timeframe) rows** — its `timeframe` is never blank by construction. BUT its own sibling script
      `migrate_odds_horizon_bucket_venue_to_bookmaker_2026_07_27.py` documents (in its own header, not yet read in
      full) that `reprocess_sports_odds.py` ALSO writes a **second, COARSE per-day row with NO `league_id`/
      `timeframe` — "the aggregate" row, by design**, distinct from the FINE per-(league_id, timeframe) row. This
      is a candidate legitimately-blank-by-design write, but from a DIFFERENT writer than the one the P3 entry
      above already ruled out (`manifest_finalize.py`'s coarse path, which can't write this `data_type` at all) —
      **not yet checked whether reprocess_sports_odds.py's own coarse write could be misclassified/queried as if
      it were a fine row** (i.e., whether the audit script's `read_availability_index_safe` query conflates the
      two row shapes). **Next, most precise step**: read `reprocess_sports_odds.py` lines ~700-760 (the coarse-row
      write call, sibling to the line-739/1226 fine-row path already found) to confirm whether its coarse rows are
      tagged with a `data_type` that could land in the audited `odds_horizon_bucket` population, and if so whether
      that's legitimate-by-design (closes this P1 todo with "no bug, working as intended, audit query needs a
      coarse/fine filter") or itself a bug. The other 4 candidate scripts remain unread. (repo:
      market-data-processing-service)
- [x] [DATA] P1. **RESOLVED, 2026-08-15 (later pass) — ROOT CAUSE CLOSED for the bulk of both populations; the
      whole MDPS live-dispatch/reprocess-script chase above was a MISATTRIBUTION, not a dead end with a real
      answer elsewhere.** Confirmed `_coarse_row_key()` (`reprocess_sports_odds.py:706-720`) is used ONLY by
      `writer.record_empty(...)` (line 988) and `writer.record_failed(...)` (line 1010) — **never**
      `record_captured`/`writer.add()` with a captured status. So the coarse-row mechanism can only ever explain
      blank-timeframe rows with `capture_status=empty_confirmed`/`attempted_failed`, never `captured`. Measured
      directly against the prod MDPS canonical
      (`market-data-tick-sports-prd-central-element-323112`, `data_type=odds_horizon_bucket`, via
      `read_availability_index_safe` through the MTDS venv — full population, not a sample):
        - Total blank-timeframe rows: 15,941 (959 in the 2026-08-15 session's backfill-attempt window, 14,982
          outside it — exactly the doc's own previously-cited "14,982 MDPS-surface" figure, now root-caused
          rather than just counted).
        - Of the 14,982 out-of-window rows: 652 have blank `league_id` + `capture_status=empty_confirmed` — this
          IS the legitimate `_coarse_row_key` mechanism, confirmed working as designed, no bug.
        - The other **14,330 have a NON-blank, real `league_id` (e.g. `LA_LIGA`, `SUPERLIGA`, `SUPER_LIG`) AND
          `capture_status=captured`** — i.e., genuine FINE per-shard rows, not coarse aggregates, that are
          missing only `timeframe`. **14,656 of the 14,982 (98%) carry `service_name=market-tick-data-service`**,
          not `market-data-processing-service` (only 326 are MDPS-attributed) — `written_at` clusters at
          `2026-07-13T23:5x` (14,656 rows) and `2026-05-05T22:07` (326 rows). This is the EXACT signature of the
          already-known, already-fixed bug — `_write_captured_rows()` in
          `market_tick_data_service/scripts/_rebuild_sports_write.py` omitting `timeframe=` on `writer.add()`
          (fixed at `market-tick-data-service@e0b34e77fd`, this doc's own header) — just from TWO EARLIER, PRE-FIX
          invocations of that same targeted-backfill script (2026-07-13 and 2026-05-05), in addition to today's
          959-row in-window occurrence. **None of MDPS's write paths (`live_workers_chain.py`,
          `live_workers_streaming.py`, `reprocess_sports_odds.py` fine or coarse) are implicated** — the two
          preceding P1 todos' "MDPS live-dispatch"/"5-candidate-script" chase was chasing the wrong service; MDPS
          genuinely cannot write this row shape at all (confirmed via the `TIMEFRAME_SECONDS`/
          `get_valid_output_timeframes` registry check), and the observed population's own `service_name` column
          says so directly — this should have been checked before the deep MDPS code trace, not after.
      **Residual open sub-item (small, not blocking)**: the 326 `service_name=market-data-processing-service`,
      `written_at=2026-05-05T22:07`, non-blank-`league_id`, `captured`-status rows are NOT explained by this
      finding (MDPS itself can't hit this write shape per the registry check) — plausible explanation is an MDPS
      script that reuses/duplicates `_rebuild_sports_write.py`'s row-key construction (same bug class, different
      repo, unread) or a `service_name` mislabel on a cross-repo call; low priority given the 2%-of-population
      size, tracked as its own follow-up rather than blocking archival of this todo. **Cleanup scope for the full
      15,941-row phantom population (959 in-window + 14,982 out-of-window, all non-destructive per this doc's own
      `audit_sports_captured_phantom_timeframe_2026_08_16.py` sibling-check design) is now todo #2's job, unchanged
      from before this pass** — this todo closes the ROOT-CAUSE question, not the cleanup-execution one.
      Measurement scripts used (scratchpad, not promoted — trivial one-off `read_availability_index_safe` queries,
      fully superseded by the `audit_sports_captured_phantom_timeframe_2026_08_16.py` script's own
      capture_status-aware query if it's ever extended to bucket by that column; the dry-run audit script itself
      IS already promoted and re-runnable). (repo: market-data-processing-service, market-tick-data-service)
- [ ] [DATA] P1. **CORRECTION to the entry immediately above, same pass, 2026-08-15 — its specific mechanism claim
      is FALSIFIED, reopening this todo.** The `_write_captured_rows()`-residue theory is directly contradicted by
      evidence already in THIS doc (line ~263 above): a full sibling check on this exact 14,982-row out-of-window
      population found **0/200 sampled rows have ANY non-blank-timeframe sibling** under the coarse
      (date,venue,league_id,data_type,service_name) key. `_write_captured_rows()`'s bug is additive by
      construction (per this doc's own header: "does not supersede the row... creates a NEW, additional phantom
      row... alongside the still-unfixed originals") — it ALWAYS leaves a sibling with the original real
      `timeframe`. Zero siblings found is the opposite signature and had already ruled this mechanism out before
      the entry above was written; that ruling-out was missed because this pass worked from a stale
      conversation-summary that did not carry the sibling-check result forward, and the entry above was written
      from `service_name`+`written_at` correlation alone without re-deriving or re-checking that a sibling check
      applies — a measurement-discipline gap (correlation ≠ the same proof standard already met elsewhere in this
      doc). **What survives, corrected**: the entry above's negative results on MDPS's OWN write paths remain
      valid and unaffected by this correction — `get_valid_output_timeframes` filtering `"horizon"` out of both
      `live_workers_chain.py` and `live_workers_streaming.py` (confirmed via direct UAC registry query, ruling out
      MDPS's live-dispatch chain entirely), and `reprocess_sports_odds.py`'s fine-row path always writing a real
      `horizon_name`-derived `timeframe` (ruling out that specific writer) — both hold regardless of this
      correction. The `service_name=market-tick-data-service` (14,656/14,982, 98%) attribution also still holds as
      a measured fact — it narrows the writer to MTDS, not MDPS — but the SPECIFIC MTDS mechanism is back to
      unknown: NOT `_write_captured_rows()` (sibling-check-falsified, this entry) and NOT
      `manifest_finalize.py::_write_shard_counts_to_manifest` (already falsified by the P3 entry above — that
      function is gated `data_type=="odds"` and cannot write `odds_horizon_bucket` at all, and this population is
      100% `odds_horizon_bucket` by the audit query's own construction). **This todo is therefore back to
      genuinely open**, narrowed to: some MTDS write path, not yet identified, that calls
      `ManifestWriter.add()`/`record_captured` for `data_type=odds_horizon_bucket` with a real `league_id` but no
      `timeframe`, active on 2026-05-05 and 2026-07-13 specifically. Not yet searched this pass: MTDS's own
      `odds_horizon_bucket`-touching scripts beyond the two already-ruled-out ones (`_rebuild_sports_write.py`,
      `manifest_finalize.py`) — a repo-wide grep for `odds_horizon_bucket` writers under
      `market-tick-data-service/` (not yet run) is the precise next step, not another MDPS-side read. (repo:
      market-tick-data-service)
- [ ] [DATA] P1. **NEW, 2026-08-15 (later pass) — repo-wide MTDS script search run, exhausted with a negative
      result; narrowed to one unconfirmed structural candidate.** All 24 MTDS files referencing
      `odds_horizon_bucket` (`grep -rl`) were triaged by write-call presence, then each real candidate checked:
        - `manifest_swap_2026_07_22.py`: EXPLICITLY excludes `odds_horizon_bucket` from scope (its own header,
          lines 68-70: lists it among data_types "none of which are in this relocation's scope") — its REMOVE
          filter is deliberately restricted to `data_type=trades`/`instrument_type=odds` specifically to avoid
          touching it. Ruled out.
        - `migrate_sports_league_id_casing_2026_07_21.py`: its own docstring states it "never writes a manifest
          row" (pure GCS object copy, confirmed by `manifest_swap_2026_07_22.py`'s header which independently
          verified this via grep) — and its scope is `data_type=trades` raw ticks, not the computed
          `odds_horizon_bucket` rollup. Ruled out.
        - `preflight.py`, `pipeline_e2e_check.py`, `recover_sports_mtds_index_leagues_2026_06_19.py`: initial grep
          hits for `.add(`/`record_captured` were ALL false positives — generic Python `set.add()`/`dict.add()`
          calls or docstring/comment mentions, not actual manifest write call sites. Ruled out.
      **One structural candidate found, NOT yet confirmed live**: `MTDSShardManifestRecorder.record_captured()`
      (`market_tick_data_service/live/manifest_recorder.py:136-185`) — the live WebSocket-ingest manifest writer
      (per its own docstring, superseded 2026-07-30 by `LiveEventFacadeSink` → Pub/Sub → Cloud-Storage-sink, but
      possibly still the active path during our population's 2026-05-05/07-13 write dates, i.e. BEFORE that
      correction). Its `record_captured()` signature has **no `timeframe` parameter at all** — not merely omitted
      at a call site (this doc's `_write_captured_rows()` bug class) but structurally absent from the function
      itself — so any row written through it inherits `ManifestWriter.record_captured`'s blank default
      unconditionally. Its caller, `websocket_streaming_handler.py:259`, passes `data_type=data_type` generically
      (whatever an upstream adapter classifies a tick as), so this is NOT confirmed to ever fire for
      `odds_horizon_bucket` specifically — and per `pipeline_e2e_check.py`'s own comment, the `SOURCE_PRIORITY`
      registry lists ZERO raw-vendor sources for `odds_horizon_bucket` (MDPS's `mdps_odds_horizon_bucket` is the
      only registered producer), which argues AGAINST a raw WS adapter ever emitting this data_type. Stopping here
      rather than asserting this as the answer without that confirmation — this session already shipped one
      incorrect root-cause claim this pass (see the CORRECTION entry above) and the same
      correlation-without-proof mistake must not repeat. **Precise next step**: trace which adapter(s) wired into
      `websocket_streaming_handler.py`'s dispatch table can classify an ODDS_API tick as
      `data_type="odds_horizon_bucket"` — if none, this candidate is ALSO ruled out and the search should pivot to
      `git log --since=2026-04-01 --until=2026-07-15 -- '**/*.py'` across MTDS for any now-deleted/superseded
      script matching the bug signature, since the population's write dates (2026-05-05, 2026-07-13) both predate
      this repo's current script inventory and a removed one-off is plausible. (repo: market-tick-data-service)
- [ ] [DATA] P1. **NEW, 2026-08-16, follow-up to the entry above — 2 more candidates ruled out, one important new
      clue found; still not confirmed.** (1) **RULED OUT**: MTDS's batch per-league sports writer
      (`venue_fetch.py::_process_sports_venue_with_leagues`, line 695) — read in full. It receives the venue's
      WHOLE `venue_data_types` list (which, per `configs/venue_data_types.yaml` lines ~449-469, includes
      `odds_horizon_bucket` for ODDS_API/BETFAIR/PINNACLE — this contradicts the earlier "zero raw-vendor sources"
      framing from an earlier pass; `SOURCE_PRIORITY` and `venue_data_types.yaml` answer different questions, the
      latter governs what a venue's raw capture is allowed to be tagged as, not just literal vendor-fetch types).
      But its shard-count key is **hardcoded** `shard_counts[(bm_str, "odds", league_str, "odds", fixture_str)]`
      (line 796, literal string `"odds"` in both data_type-like slots) — structurally cannot produce an
      `odds_horizon_bucket`-tagged manifest row regardless of what `venue_data_types` requested. Confirmed by
      direct read, not inference. (2) **Traced but NOT ruled out — live WS shard path**: confirmed
      `websocket_streaming_handler.py`'s `data_type` is a raw CLI `--shard-spec asset_group:venue:data_type`
      argument (not adapter-classified); `_resolve_connector` looks up the connector by VENUE only
      (`resolve_ws_feed_venue_key`), never validating `data_type` against what that venue's connector actually
      produces. The ODDS_API connector (`live/connectors/odds_api_ws.py`) stores `self._data_type` (line 232) but
      never reads it anywhere else in the 424-line file — meaning if a shard WERE launched with
      `--shard-spec sports:ODDS_API:odds_horizon_bucket`, it would stream the exact same raw odds ticks as a
      normal `odds` shard, just manifest-recorded under the wrong `data_type` label via the already-identified
      `MTDSShardManifestRecorder.record_captured()` (structurally no `timeframe` param). Found the live-shard
      launcher (`deployment-service/scripts/vm/launch-mtds-live.sh`) — it requires an explicit, manually-supplied
      `--shard-spec` per invocation; it does **not** auto-iterate `venue_data_types.yaml` to launch one shard per
      declared data_type, so this path needs a deliberate launch decision, not something that falls out of config
      alone. Not yet found (or ruled out): any actual launch record/log of a
      `sports:ODDS_API:odds_horizon_bucket` shard. (3) **New clue, argues AGAINST the live-shard hypothesis**: the
      two write-timestamp clusters for the 14,982-row population — 14,656 rows at `2026-07-13T23:5x`, 326 rows at
      `2026-05-05T22:07` — are each a TIGHT SINGLE-MINUTE cluster. Continuous live WS ingest stamps
      `available_at` per-tick throughout a shard's runtime (hours+), so a single-minute cluster of thousands of
      rows is a poor fit for "a live shard ran with the wrong data_type for a while" and a much better fit for "a
      single batch/script invocation wrote many rows in one pass" — reinforcing the original, still-unconfirmed
      hypothesis that this is a one-off script, not the live path. **Precise next step**: search MTDS's script
      inventory (both current and via `git log` on MODIFIED, not just deleted, files) for anything that could have
      run as a single batch job at `2026-07-13T23:5x` and `2026-05-05T22:07` UTC specifically — the exact
      characters-since-midnight granularity of both timestamps suggests these are real job-completion stamps, not
      per-row `available_at` values, so cross-referencing against any cron/systemd job log or VM launch history
      for those two exact windows may be more direct than further code tracing. Do not assume the live-shard
      candidate confirmed OR ruled out — it remains genuinely open, just deprioritized by this clue. (repo:
      market-tick-data-service, deployment-service)
- [ ] [DATA] P1. **NEW, 2026-08-16, follow-up — deployment-archive check attempted, result is UNINFORMATIVE (not a
      negative), a measurement trap caught before it was asserted.** Re-ran this doc's own scratchpad deploy-history
      checker (`check_deploy_history_cf8_2026_08_15.py`, extended with the 2026-05-05 date) against
      `deployment-scripts-central-element-323112/deployments/archive/<date>/` for both target write dates: **0
      records for 2026-05-05, 0 records for 2026-07-13.** Before treating that as "no VM/deploy job ran on either
      date" (which would have ruled out every deployment-service-tracked launch mechanism, including
      `launch-mtds-live.sh`), checked when the archive itself starts: **earliest archived date is 2026-07-16** (32
      total archived dates, all ≥2026-07-16). **Both target dates predate the archive mechanism's existence
      entirely** — the 0-record result is uninformative by construction, not a real absence signal (CLAIM ≤
      MEASUREMENT: 0 hits ≠ missing when the search tool itself doesn't cover the queried range). This neither
      confirms nor rules out a deployment-service-launched job on either date; it just means this particular tool
      can't answer that question for dates this old. **Precise next step, not yet tried**: (a) check whether MTDS
      or the underlying VM hosts retain systemd/journal logs reaching back to 2026-05-05/07-13 (unlikely at this
      remove, but worth one cheap check before ruling it out); (b) a more promising angle — read the GCS object
      metadata (not the manifest row) on a small sample of the actual phantom-timeframe parquet shard files
      themselves (`gcs_describe_object` per this repo's storage conventions, never subprocess `gsutil`) — object
      `time_created`/`updated` plus any custom metadata (uploader identity, generating host/job name if stamped)
      may carry a clue the manifest row itself doesn't, since the manifest and the underlying shard file are
      written by the same process but the object metadata layer hasn't been inspected at all yet this entire
      investigation. (repo: market-tick-data-service)
- [ ] [DATA] P2. **NEW, 2026-08-16 — GCS-path angle BLOCKED; redirect filed; no new root cause.** Manifest has NO
      `path`/`gcs_path` column (`_V8_COLUMNS`, UTL `_read_index.py:488-569`); rebuilding a real object path needs
      `build_canonical_candle_object_path`/`registry.py:362`, itself requiring `timeframe` — circular for these
      rows. **Next**: a bounded per-shard prefix LIST (not a corpus walk) on one known captured/blank-timeframe
      row, to check whether ANY real object exists (none = these `captured` rows have no backing data). Also ruled
      out a 3rd coarse-write site (`reprocess_sports_odds.py:1210-1217`, captured branch, omits timeframe/
      league_id) vs. the 652/14,330 split (~line 484-493) — shape matches neither bucket. This pass's narrow query
      (4 `empty_confirmed`/MDPS rows at `2026-05-05T22:07`) vs. the doc's 326 `captured`/MDPS rows for "the same
      cluster" — different status, NOT reconciled. `MTDSShardManifestRecorder.record_captured()` (line 561-568)
      remains the correct, untouched lead. (repo: market-tick-data-service, market-data-processing-service, UTL)

## Progress Log

- **data_engineering slot-2, 2026-08-15**: dispatched onto
  `cf_manifest_audit_first_full_rollup_findings_2026_07_26.md`'s P3 todo (operator-approved 2026-08-11). Worked through
  3 shared-host obstacles (tmpfs-exhaustion, OOM, cross-slot collision) to land 2 of 3 MDPS service_name groups, then
  found this `timeframe`-drop bug via a precise row-key re-verification before scaling further. Stopped, released both
  maintenance windows, resumed both crons, filed this issue. No data destroyed; backfill genuinely incomplete on both
  surfaces.
- **data_engineering slot-2, 2026-08-15 (checkpoint)**: this doc + the parent todo's Progress Log entry are pushed
  (`unified-trading-pm@e6d24727aa`). One remaining shipping item: the 2 memory-bounded read-path helper scripts this
  session added (`_sports_is_captured_stream_read_2026_08_15.py`,
  `_sports_is_captured_backfill_from_subset_2026_08_15.py`) are committed locally on `market-tick-data-service`
  (`28109508`) but not yet pushed — `quality-gates.sh` has been retried 8+ times and keeps getting starved by
  exceptional, sustained fleet-wide QG contention (30+ concurrent `quality-gates.sh` instances observed across the
  fleet; matches the ALREADY-TRACKED, unresolved `qg_host_governor_caps_instances_not_fanout_2026_08_10.md` P2 infra
  issue, not something this session can work around). Retrying; will ship via `quickmerge --agent` the moment a QG pass
  completes. If this session ends before that lands: the commit is safe on disk (`git log --oneline -1` on the
  market-tick-data-service slot-2 checkout), just needs Pass-1 QG + Pass-2 quickmerge to reach origin — non-urgent (2
  new diagnostic-only files, zero production risk sitting uncommitted-to-origin).
- **data_engineering slot-2, 2026-08-15 (pre-compact checkpoint, corrects the entry above)**: the SHA cited above
  (`e6d24727aa`) is stale — this doc's own edits (and the parent plan's Progress Log entry) actually landed via the PM
  push-governor at `unified-trading-pm@9cf09fbda8` (confirmed via the push-governor's own log:
  `✅ Pushed 9cf09fbda8 -> live-defi-rollout`, after an 1128s queue wait + one origin-moved reconciliation retry). The
  market-tick-data-service commit (local `28109508`, `908cfecf43f90d32ba3dbcd4dcb62ca2b7a7cb09` after quickmerge's
  rebase) remains queued in the qg-host-governor (`market-tick-data-service` sub-cap 1 / host-wide cap 6) for 110+
  minutes this session alone — the longest single wait observed on this task — still the SAME already-tracked
  `qg_host_governor_caps_instances_not_fanout_2026_08_10.md` P2 condition, not a new failure; the quickmerge PID has
  been confirmed alive and unchanged throughout. `git merge-base --is-ancestor` against `origin/live-defi-rollout` still
  returns NOT-LANDED as of this checkpoint (drift `ahead=1/behind=6`). A background heartbeat is polling for landing;
  once confirmed, `/done` will be called for `task_id=cf_manifest_audit_first_full_rollup_findings-d1fc625d0914` with
  the landed SHA and evidence citing both `unified-trading-pm@9cf09fbda8` and the landed market-tick-data-service SHA —
  explicitly noting the backfill itself was NOT completed this session (the `timeframe`-drop correctness bug above was
  found instead, and is the actual blocker on re-attempting it).
- **data_engineering slot-2, 2026-08-15 (later checkpoint — queue cleared, gate now genuinely RED, not queued)**: the
  qg-host-governor queue for `market-tick-data-service` finally admitted this job into actual test execution after ~171+
  min of pure queue wait. The run completed (`10854 items, 166.20s`) with
  `2 failed, 10823 passed, 28 skipped, 1 xpassed` — both failures are
  `test_build_casing_frame_upgrades_every_known_residual_token` and
  `test_cme_combo_shard_itype_now_canonicalizes_uppercase`, i.e. the SAME two tests already filed as
  `/plans/archive/2026_08/issues/mtds_tradfi_combo_casing_qg_red_2026_08_15.md` (P1, repo-blocker, filed by slot-29,
  unrelated in-flight tradfi COMBO casing migration). Confirmed as a THIRD independent data point (a separate Pass-2
  quickmerge attempt earlier this session, and now this Pass-N re-gate, both hit byte-identical failures) — the
  condition is stable, not flapping, and it is NOT caused by this session's shipped sports/CF-8 diagnostic scripts
  (unrelated files). Per that issue doc's own "likely self-resolves" expectation: it has NOT yet resolved — `behind`
  drift climbed from ~9 to 21 across this session's checks (many more commits landed on `live-defi-rollout` in the
  interim) and the same 2 tests are still red, so self-resolution is taking longer than that doc anticipated. This
  session's `market-tick-data- service` commit (`908cfecf43f90d32ba3dbcd4dcb62ca2b7a7cb09`) remains genuinely NOT-LANDED
  — now blocked on `mtds_tradfi_combo_casing_qg_red_2026_08_15.md` clearing (someone else's fix), not on
  qg-host-governor queue admission (that part cleared). Not attempting to fix the tradfi casing bug myself — out of this
  task's scope and already owned. `/done` for `task_id=cf_manifest_audit_first_full_rollup_findings-d1fc625d0914` has
  NOT been called: the standing instruction conditions it on landing, and landing is now blocked on a separate,
  already-tracked P1 repo-blocker with no ETA. Next session/window: re-check
  `mtds_tradfi_combo_casing_qg_red_2026_08_15.md`'s `status:` — once it flips to resolved (or the 2 named tests pass
  independently), retry the quickmerge; if still open after a long gap, consider escalating that issue's priority rather
  than continuing to poll here.
- **data_engineering slot-2, 2026-08-15 (pre-compact checkpoint, still blocked — watchdog #6 armed)**: re-confirmed
  directly (not from stale cache) that `mtds_tradfi_combo_casing_qg_red_2026_08_15.md` is still `status: open` and the
  market-tick-data-service commit (`908cfecf43f90d32ba3dbcd4dcb62ca2b7a7cb09`) is still NOT-LANDED; drift has climbed to
  `ahead=1/behind=24` (remote advancing, not a regression here). Five prior background heartbeat watchdogs (`bic38kbwy`,
  `br77dd2be`, `btme3cpyp`, `bizkfhjjq`, `bu1luwlak`) each ran their full 8-check (~8 min) cycle and timed out without
  landing; a 6th (`bwyrxn16q`) is now armed and polling. Both repos' working trees are clean; this PM repo is fully
  pushed (`ahead=0` vs `origin/live-defi-rollout`) — the only durability gap is the already-diagnosed, already-tracked
  MTDS commit sitting local-only behind someone else's P1 repo-blocker, which is a "cannot be done yet" condition (needs
  slot-29's fix or the blocker's self-resolution), not lost/uncommitted work. Also searched this session's available
  tools for an AO `/progress` heartbeat mechanism (`ToolSearch` query `"heartbeat progress done task_id"`) and found
  none — only generic session tools (Monitor, TaskUpdate, PushNotification, etc.). No AO-specific `/progress` call
  exists in this tool surface; per the standing instruction to not guess it, it remains un-sent. `/done` still NOT
  called — still conditioned on MTDS landing. Next session/window: read whichever watchdog is live at resume time, and
  if it TIMED OUT, re-check `mtds_tradfi_combo_casing_qg_red_2026_08_15.md`'s `status:` before relaunching watchdog #7
  (cheap single grep, avoids relaunching a watchdog for a blocker that already cleared).
- **data_engineering slot-2, 2026-08-15 (2nd pre-compact checkpoint — 6 consecutive watchdog timeouts, flagging
  stall)**: watchdog #6 (`bwyrxn16q`) completed its full 8-check cycle and TIMED OUT — drift climbed
  `ahead=1/behind=24→26` across its run; the market-tick-data-service commit
  (`908cfecf43f90d32ba3dbcd4dcb62ca2b7a7cb09`) remains NOT-LANDED. Re-confirmed
  `mtds_tradfi_combo_casing_qg_red_2026_08_15.md` still `status: open`. Re-confirmed — this time via actual
  `ToolSearch(select:...)` schema inspection, not just name-matching — that none of `PushNotification` (desktop/phone
  alert, not task-scoped), `RemoteTrigger` (claude.ai trigger API), `SendMessage` (inter-agent chat), `TaskUpdate`
  (session-local `TaskList` only, not the AO backlog), or `DesignSync` (design-system sync) is an AO
  `/progress`/`/heartbeat` call — no such mechanism exists anywhere in this tool surface; not fabricated, and this
  should stop future sessions re-deriving the same negative result. Pre-compact Step 1 scratchpad audit: `duckdb-tmp/`
  holds 3 `manifest-consolidate-*` dirs — regenerable DuckDB temp state from the earlier (already-completed) MDPS
  consolidate diagnosis, not referenced by any committed doc (grep confirmed clean), not needed by any open todo;
  deliberately not promoted. `qm-watchdog-2.log` is a 0-byte watchdog-script artifact; deliberately not promoted. No
  secrets found. Both repos' working trees clean; this PM repo `ahead=0`. **This is now 6 consecutive watchdog timeouts
  (~48+ min of pure wait) with `behind` climbing from ~11 to 26 over the session** — the blocking doc's own "likely
  self-resolves" expectation has clearly not held on this timescale; flagging to the operator in-chat per this ritual's
  Step 3 (interactive mode, operator present) rather than escalating unilaterally, since the fix itself is out of this
  task's scope and already owned by slot-29. `/done` still NOT called — still conditioned on MTDS landing. Next
  session/window: same as above — re-check the blocker's `status:` before relaunching another watchdog; if still open
  after a much longer gap, escalating THAT issue's priority (not this one) is the right lever, not further polling here.
- **backend_engineer slot-3, 2026-08-15**: the blocker HAS CLEARED. Picked up
  `/plans/archive/2026_08/issues/mtds_tradfi_combo_casing_qg_red_2026_08_15.md` as a dispatched task; both named tests
  (`test_build_casing_frame_upgrades_every_known_residual_token`,
  `test_cme_combo_shard_itype_now_canonicalizes_uppercase` — the latter renamed/superseded by
  `test_cme_combo_shard_itype_stays_lowercase_bundle_grain` per a 2026-08-11 operator ruling) pass on current
  `live-defi-rollout` HEAD with zero code changes needed; `bash scripts/quality-gates.sh` ran full green on
  `market-tick-data-service` (sentinel matches HEAD `24afa00b8a6d0a3dc1931efd3440dba30cef8c93`). Issue doc flipped to
  `status: archived` + `git mv`'d to `plans/archive/2026_08/issues/`. Whoever resumes this watchdog can retry landing
  `market-tick-data-service` commit `908cfecf43f90d32ba3dbcd4dcb62ca2b7a7cb09` immediately — no further wait needed on
  this specific blocker (a fresh `live-defi-rollout` pull may still surface unrelated drift; that's ordinary trunk
  churn, not this blocker recurring).
- **data_engineering slot-2, 2026-08-15 (landing confirmed, correcting stale SHA above)**: retried and landed. The
  diagnostic-scripts commit is now `market-tick-data-service@820bb93527f6252d52d4822163e40b5ecc68e70f` — the
  `908cfecf...` SHA cited in the checkpoints above is a pre-rebase intermediate that churned through several
  `git pull --rebase --autostash` cycles (`908cfecf`→`42b90b74`→`820bb935`) before landing; this is expected rebase
  churn, not lost work (verified `git merge-base --is-ancestor 820bb935 origin/live-defi-rollout` = true, both scripts
  present under `market_tick_data_service/scripts/`). AO
  `task_id=cf_manifest_audit_first_full_rollup_findings-d1fc625d0914` marked `completed`. **This closes only the
  diagnostic-script shipping loose end** — the CF-8 backfill itself remains genuinely incomplete; the 4 todos below (P1
  `timeframe=` fix, P2 phantom-row cleanup, P2 backfill re-attempt, P3 maintenance-window gap) are still open and still
  the actual remaining scope. Picking up todo #1 next.
- **data_engineering slot-2, 2026-08-15 (todo #2 audit — dry-run only, NO write performed)**: built + ran
  `market-tick-data-service/scripts/audit_sports_captured_phantom_timeframe_2026_08_16.py` (dry-run only, no `--apply`,
  same posture as `drop_sports_odds_phantom_uppercase_2026_07_26.py`) against the live MDPS canonical. Three findings
  that change this todo's scope, none acted on yet:
  1. **Live in-window phantom count is 14,330, not the doc's ~26,982 lower-bound.** The original estimate only counted
     landed/consolidated rows at write time; live count differs (consolidation churn since, or the estimate was simply a
     bound, not a measurement — not further diagnosed here, noting the discrepancy rather than treating either number as
     ground truth going forward).
  2. **NEW: 14,982 blank-`timeframe` `odds_horizon_bucket` rows exist OUTSIDE the session window** — a comparably-sized
     population this doc never scoped, previously unknown. Filed as a new P1 todo below; NOT assumed same
     cause/disposition as the in-window bug.
  3. **The "NON-destructive" claim does NOT hold for the full population.** A 200-row sibling-check sample (does a
     non-blank-timeframe row survive under the same coarse key?) found 13/200 (6.5%) with NO surviving sibling — 12 of
     which share `league_id=LA_LIGA_2, service_name=market-data-processing-service`. Deleting those specific rows WOULD
     be destructive. Todo #2 above is narrowed accordingly: blanket delete is now explicitly ruled out; only a
     sibling-confirmed subset (pending a full-population, not sampled, sibling check) is safe to act on. Script + this
     doc update are being shipped now; the actual cleanup write remains NOT started, correctly gated on the exclusion
     work above.
- **data_engineering slot-2, 2026-08-15 (todo #1 QG green + committed, quickmerge in flight)**: background
  `bash scripts/quality-gates.sh --no-fix` (task `bd0xbn5xh`) finished GREEN (exit 0) after ~592s queued behind the
  qg-governor cap — environment/dep/lint gates + full pytest suite (10,894 items) all passed. Staged exactly the 2
  intended files by name (`git status`/`git diff --cached --stat` confirmed nothing else picked up), committed as
  `market-tick-data-service@e0b34e77`, and launched `bash scripts/quickmerge.sh "..." --agent --files '...'` in the
  background (task `bjrk1mgbl`). As of this checkpoint quickmerge is re-gating (a peer push moved HEAD mid-run — normal,
  self-resolving per this doc's own established pattern) and queued again behind qg-governor;
  `git rev-list --count origin/live-defi-rollout..HEAD` = 1, so the fix is **NOT YET LANDED**. Scratchpad audit: besides
  the already-accounted-for `duckdb-tmp/` and `qm-watchdog-2.log` (see above, still deliberately not promoted),
  `mtds_qg_timeframe_fix.log` (77KB QG output capture) is new this session, not referenced by any committed doc, and now
  superseded by the actual commit + task-output record — deliberately not promoted, safe to lose. No secrets found. Both
  repos' working trees clean except the 1 unpushed local commit noted above; PM repo itself `ahead=0`. Next
  session/window: check quickmerge task `bjrk1mgbl`'s outcome (rely on the harness's own completion notification, don't
  poll), verify landing via `git merge-base --is-ancestor 1c9a7858 origin/live-defi-rollout` (sha may churn through
  rebase, check `git log --oneline -5` for the real landed sha), then flip todo #1 with that sha. Only after todo #1 is
  actually landed does todo #2 (phantom-row cleanup) become actionable.
- **data_engineering slot-2, 2026-08-15 (landing checkpoint)**: quickmerge task `bjrk1mgbl` completed exit 0. Its own
  internal `quality-gates.sh` run (STAGE 3) re-gated once (peer-push HEAD move, self-resolving as predicted above),
  queued ~153s behind the host's qg-governor cap, then ran the full 10,894-item suite clean (10,865 passed, 28 skipped,
  1 xpassed, 0 failed, 81.83% coverage) and all remaining gate stages green (`ALL QUALITY GATES PASSED (380s)`). At
  STAGE 5 (Create PR) quickmerge found the working tree already committed but noted it was **missing the `Quickmerge:`
  trailer**, so it amended HEAD to add `Quickmerge: agent` before pushing — this changed the local sha from `1c9a7858`
  to `e0b34e77fd` (content-identical, trailer-only amend, not a rebase). Pushed and self-verified:
  `[market-tick-data-service] ✅ post-push ancestry verified — e0b34e77f is an ancestor of origin/live-defi-rollout`.
  Independently re-confirmed this session: `git merge-base --is-ancestor e0b34e77fd origin/live-defi-rollout` (exit 0)
  and `git rev-list --count origin/live-defi-rollout..HEAD` = 0. Todo #1 flipped to `[x]` with the real landed sha.
  **Lesson for future sessions on this doc**: sha drift on this repo isn't only from rebase — a missing Quickmerge
  trailer on an already-committed tree triggers a silent amend at push time too; always re-derive the landed sha from
  the ship script's own "post-push ancestry verified" line or `git log`, never assume the pre-quickmerge local sha
  survives. **Next actionable item**: todo #2 (P0, phantom blank-timeframe row cleanup on MDPS, ~26,982 lower-bound) is
  now unblocked — pick it up next.
- **data_engineering slot-2, 2026-08-15 (3rd pre-compact checkpoint — audit script quickmerge fix + resubmit)**:
  quickmerge task `b3l0jzbxk` (shipping the new dry-run audit script for todo #2) FAILED — root-caused via
  `.venv/bin/python .cursor/scripts/check-import-patterns.py --verbose`: the script's own
  `from unified_trading_library.manifest_writer import read_availability_index_safe` is a banned deep import (checker
  requires the top-level re-export). Confirmed `read_availability_index_safe` IS re-exported at the top level
  (`unified_trading_library/__init__.py:1012`), fixed the import, verified clean with the checker scoped to just this
  file, and re-shipped via
  `bash scripts/quickmerge.sh ... --files 'scripts/audit_sports_captured_phantom_timeframe_2026_08_16.py'` (task
  `bze6dwost`) — as of this checkpoint it has progressed cleanly past pre-flight/lint into the pytest suite (~10%+, no
  failures), not stalled. Also re-synced PM twice this window (both times genuinely behind via
  `rev-list --left-right --count`, both clean `--ff-only` fast-forwards, `749f578c53→2b1721e9dc`, 8 unrelated
  plan-reconcile/archival commits from other sessions — confirmed none touch this doc). Scratchpad audit:
  `phantom_timeframe_audit_2026_08_16.log` (3.7KB, new this window) is a local dry-run capture, superseded by the
  committed script + this doc's own findings — deliberately not promoted, safe to lose. No secrets found.
  `mtds_tradfi_combo_casing_qg_red_2026_08_15.md` (the earlier repo-wide QG-red blocker referenced in this doc's own
  history) is now `status: archived` — confirms it self-resolved, unrelated to this window's failure (which was a
  genuine bug in this doc's own script, not a shared-repo condition). **Next session/window**: verify `bze6dwost` landed
  (`git rev-list --count origin/live-defi-rollout..HEAD` = 0 for the audit script commit — rely on the harness
  completion notification, don't poll), then run the FULL-population sibling check (not the 200-row sample) to finalize
  todo #2's exclusion scope.
- **data_engineering slot-2, 2026-08-15 (4th pre-compact checkpoint — second, DIFFERENT quickmerge failure on the same
  script, fixed + re-shipped)**: `bze6dwost` (the re-ship from the prior checkpoint) also FAILED — but on a genuinely
  DIFFERENT gate than `b3l0jzbxk`: `RUF005` (list-concat style) at
  `scripts/audit_sports_captured_phantom_timeframe_2026_08_16.py:137` (`_ROW_IDENTITY_COLS[:-1] + ["service_name"]` →
  `[*_ROW_IDENTITY_COLS[:-1], "service_name"]`). Per the ritual's Step-7 retry discipline: two DIFFERENT failures in a
  row on a brand-new file is expected friction (each finding is a real, distinct gate result on genuinely new code, not
  a flapping/foreign-session condition) — diagnosed via the task's own output tail, applied the one-line ruff-suggested
  fix, verified clean with both `ruff check` and `check-import-patterns.py` scoped to the file, and re-shipped as task
  `bpdxo4199` (in flight as of this checkpoint, not polled further per async-wait discipline — pick up on the harness
  completion notification). **Lesson for future sessions**: a quickmerge failure on your own newly-authored file should
  be diagnosed fresh EACH time, not assumed to be "the same bug again" — this file hit two unrelated gates
  (import-pattern, then lint) back to back, and blind-retry without re-reading the new failure's own output would have
  wasted a cycle. Re-verified PM clean at `824e7e5e25` (4 more unrelated plan-reconcile/archival commits ff-pulled, none
  touching this doc) and MTDS behind by exactly the routine `chore(deps): refresh base-image digest pin` commit
  (unrelated). **Next session/window**: verify `bpdxo4199` landed (`git rev-list --count origin/live-defi-rollout..HEAD`
  = 0 for the audit script commit), THEN run the FULL-population sibling check (not the 200-row sample) to finalize todo
  #2's exclusion scope.
- **data_engineering slot-2, 2026-08-15 (5th pre-compact checkpoint — bpdxo4199 FAILED on a new failure mode, fixed by
  clean re-ship, now LANDED)**: `bpdxo4199` came back `failed` (exit code 1) with a genuinely different signature than
  the two prior failures on this file — its output file was 0 bytes, meaning the ship script never produced any
  stdout/stderr (a dispatch-level crash, not a content/gate failure like the import-pattern or RUF005 misses). Diagnosed
  the local MTDS checkout before retrying: no stale `.git/index.lock`, local `HEAD` unchanged (no stray partial commit),
  staged diff exactly the intended 185-line addition (`git diff --cached --stat`) — environment was clean, so this was
  safe to blind-retry rather than needing a content fix. Re-shipped via
  `bash scripts/quickmerge.sh "fix: apply RUF005 fix to sports captured phantom-timeframe audit script (re-ship after bpdxo4199 dispatch failure)" --agent --files 'scripts/audit_sports_captured_phantom_timeframe_2026_08_16.py'`
  (task `bi1euby72`), which ran the full pipeline cleanly (cascade, pre-flight audit, QG sentinel-skip on Pass 2, all
  pre-commit hooks passed including Conventional Commit) and landed. Independently verified:
  `market-tick-data-service@e91c3ef2` is `git log`-visible on `origin/live-defi-rollout` for this exact path, working
  tree clean, `git rev-list --count origin/live-defi-rollout..HEAD` = 0. **Lesson**: a 0-byte task output file on a
  "failed" background ship is a distinct signal from a populated one showing a gate failure — it means the process never
  got far enough to report anything, so check local repo state (lock files, stray commits, staged diff) for corruption
  before assuming the retry needs a content fix; here it didn't, and blind retry was correct. **Next actionable item**:
  the dry-run audit script (with both the import-pattern and RUF005 fixes) is now fully landed — run the FULL-population
  sibling check (not the 200-row sample) via `audit_sports_captured_phantom_timeframe_2026_08_16.py` to finalize todo
  #2's exclusion scope, per the todo's own already-narrowed spec above.
- **data_engineering slot-2, 2026-08-15 (6th checkpoint — full-population sibling check DONE, with a background-task
  measurement trap caught and corrected first)**: ran the landed `e91c3ef2` script with `--sibling-sample-size 50000`
  (exceeds the 14,330 phantom count, forcing full-population coverage per the script's own
  `sample = phantom if len(phantom) <= args.sibling_sample_size else ...` logic). First attempt was backgrounded as
  `cmd | tee logfile` and the harness reported it `completed, exit code 0` — but both the tee'd scratchpad log and the
  harness's own `.output` file were stable at only 7-8 lines, cut off immediately after the "PerformanceWarning:
  indexing past lexsort depth" line, with NONE of the script's final `logger.info` summary lines (sibling-check result,
  blast radius, would-delete count) present. Per CLAIM ≤ MEASUREMENT, treated the "completed/exit 0" claim as unverified
  rather than trusting it: `dmesg`/`journalctl` were unreadable (`Operation not permitted`, not informative either way),
  no lingering process was found via `ps aux`, and the harness had already reaped the task record (`TaskOutput` → "No
  task found"). Root cause not fully confirmed (plausible: `tee`/pipe exit-code masking a killed upstream process, since
  a bare `cmd | tee file` without `pipefail` reports `tee`'s exit code, not the script's), but the fix was
  straightforward: re-ran the identical script synchronously with a direct `> file 2>&1` redirect (no pipe, explicit
  `echo EXIT_CODE=$?` after) instead of backgrounding through `tee`. **This run genuinely completed** (27-line log, all
  summary sections present, real exit 0). **Lesson for future sessions**: a background task's reported exit code is only
  as trustworthy as the command that produced it — `cmd | tee file &` can report the wrapper's/tee's exit code rather
  than the real command's; either add `set -o pipefail` before piping through `tee`, or skip `tee` entirely and redirect
  straight to a file with an explicit `echo EXIT_CODE=$?` when the file's own line count/final-section presence is the
  only reliable completion signal available. **Full-population results** (see todo #2 above for the narrative): 14,330
  total phantom rows (exact, matches the 200-sample extrapolation), 959 (6.69%) with no sibling, 872 of those (91%) are
  `league_id=LA_LIGA_2`/MDPS — and LA_LIGA_2's no-sibling count (872) exactly equals its total phantom count (872), i.e.
  100% of LA_LIGA_2 phantom rows have no sibling, strengthening the single-horizon-bucket-league hypothesis over "a
  second bug" (not yet independently confirmed against MDPS's capture config). Remaining ~20 minor leagues each
  contribute ≤22 no-sibling rows, all MDPS, none IS. Full retry-audit log preserved at
  `market-tick-data-service/scripts/audit_sports_captured_phantom_timeframe_2026_08_16.py`'s own scratchpad output
  (ephemeral, regenerable by re-running the script — not promoted, since the script itself is the durable artifact and
  is already landed). **Next actionable item**: todo #2 sub-step (b) — confirm the single-horizon-bucket hypothesis
  against MDPS's actual capture/backfill config for LA_LIGA_2 (and the ~20 minor leagues) rather than relying on the
  100% correlation alone — then sub-step (c) (exclude the 959 rows from delete scope) and the still-untouched IS-side
  check (the script only audits MDPS; IS's 500-row test population has not been checked for the same phantom-row class).
- **data_engineering slot-2, 2026-08-15 (7th checkpoint — todo #2 sub-step (b) CONFIRMED via direct query, no longer
  just correlation)**: ran ad-hoc `read_availability_index_safe` queries (no new script — a direct interactive
  investigation, findings transcribed here + into todo #2 above) against the live MDPS manifest for LA_LIGA_2 and 3
  sampled minor leagues (SOCCER_RUSSIA_PREMIER_LEAGUE, SOCCER_AUSTRALIA_ALEAGUE, SOCCER_SWITZERLAND_SUPERLEAGUE —
  covering 915/959 = 95% of the no-sibling population). For LA_LIGA_2: out-of-window rows are NOT blank — they carry
  real `15m`/`1h` timeframe values (a different vocabulary than the `T-6h`-style buckets seen on other leagues like
  SUPERLIGA), but ONLY from 2026-03-28 onward (458 rows); the 872 phantom rows span 2020-06-12..2026-02-20 with ZERO
  (date,venue) overlap against the non-blank population. For the 3 sampled minor leagues: zero non-blank-timeframe rows
  exist at ANY date — `timeframe` has literally never been populated for their `odds_horizon_bucket` rows. Revised
  conclusion (corrects the original "single-horizon-bucket league" framing, which implied a bucket-COUNT explanation):
  the real mechanism is TEMPORAL/coverage-based — these leagues' pre-existing captured rows for the backfill-targeted
  historical dates already had blank `timeframe` BEFORE this session's bug ever ran, so the backfill's blank-timeframe
  rewrite lands on the SAME row_key as the original (supersession, not duplication) — there was never a second,
  differently-timeframed row to lose. This is a stronger, directly-measured confirmation than the earlier 100%
  correlation observation, and it means the 959-row exclusion (todo #2c) is evidence-backed rather than merely cautious.
  **Lesson**: "no sibling under the coarse key" in this audit script's output can mean either "data was destroyed" (the
  risk it was designed to catch) or "there was legitimately only ever one row" (a false-positive-shaped but actually
  benign case) — the two are indistinguishable from the sibling-check alone; only a date-range/vocabulary cross-check
  against the SPECIFIC league's own historical population disambiguates them, as done here. Did not check the remaining
  ~20 minor leagues individually (87-27=60 rows, ≤9 each) — the pattern is consistent enough across 4/4 checked leagues
  (all MDPS, same service_name, same shape) that further per-league verification is diminishing-returns for a 959-row
  population already excluded from any write regardless of root cause. **Next actionable item**: todo #2 sub-step's
  remaining open piece — audit whether the same phantom-row class exists on IS (the 500-row test population there has
  not been checked); then todo #2b (root-cause the 14,982 out-of-window blank-timeframe MDPS population — note
  LA_LIGA_2's real timeframe-labeled rows only starting 2026-03-28 may be a relevant clue for that investigation too,
  since it establishes a precedent for "no timeframe data before a certain date" on this same surface).
- **data_engineering slot-2, 2026-08-15 (execution prep for the 13,371-row MDPS delete)**: built + landed
  `market-tick-data-service/scripts/sports/delete_cf8_phantom_timeframe_sibling_confirmed_2026_08_15.py`
  (`market-tick-data-service@27484b18e9`), adapted directly from the proven
  `purge_sport_residue_and_blank_venue_manifest_rows_2026_08_14.py` template (same row-group-streamed CAS-write shape,
  same §3a fresh soft-delete-retention check, same snapshot-before-write, same independent post-write re-verify).
  Predicate: `data_type=odds_horizon_bucket`, blank `timeframe`, `written_at` in the session window, HAS a non-blank
  sibling under the coarse key — i.e. exactly the 13,371-row subset this todo scoped, excluding the 959 no-sibling
  rows. Hard-refuses `--confirm-prod-write` unless the LIVE count matches 13,371/959 exactly (extra caution beyond the
  template, since this predicate is a compound sibling-join, not a flat mask). **Dry-run executed against the live
  prod index** (safe — column-projected read only): `live index rows: 6,246,538`, `MATCH: 13,371` (exact match to this
  doc's confirmed count), `NO-SIBLING: 959` (exact match) — full re-confirmation, not reused from the earlier audit.
  Fresh §3a check also run standalone: `market-data-tick-sports-prd-central-element-323112` soft-delete retention =
  604800s (qualifies). **NOT yet executed** (`--confirm-prod-write` unrun): per
  `purge_sport_residue_and_blank_venue_manifest_rows_2026_08_14.py`'s own docstring, a local `--confirm-prod-write`
  attempt on a comparable `odds_horizon_bucket` MDPS-index rewrite already OOM-killed twice this session (sandbox
  cgroup limit, not genuine host exhaustion) — that precedent is why this doc's own P0 sits under the VM-launcher
  runbook's heavy-I/O hard rule, not a plain local run. Investigated wiring a new category into
  `deployment-service/scripts/vm/launch-canonical-migration-vm.sh` (the sanctioned reuse path, `sports-manifest-
  cleanup` is the closest precedent) but stopped short of editing it this session: it is a single 2911-line file shared
  across ~90 launch categories in a repo this session has not otherwise touched, and the mode-flag-append convention
  differs per category (some bake `--apply`/`--confirm-prod-write` inline, some use a generic suffix) — a
  same-session, first-read edit to it carries real blast-radius risk for an unrelated category if mis-wired. **Next
  actionable item**: either (a) add a new `sports-cf8-phantom-timeframe` category to that launcher (5 touch-points:
  usage string, the compound-chain case block ~line 1642, VM_SERVICE dispatch ~2450 — likely NOT needed, this script
  lives in mtds which is the dispatcher default, unlike instruments-service-based `sports-manifest-cleanup` — asset-
  group dispatch ~2493, main dispatch case ~2896), mirroring `sports-manifest-cleanup`'s compound-chain pattern but
  with the `--confirm-prod-write` flag this script actually uses (not `--apply`); or (b) a raw one-off
  `gcloud compute instances create` VM per the generic `VM_MIGRATION_CMD`/`setup-data-pipeline-vm.sh` pattern, IF
  registered under an existing `VM_PREFIX_TO_BUCKET` prefix first (never hand-roll a name — the runbook's own 2026-07-09
  incident). Either way: launch, verify STARTED + TERMINAL, confirm `>>> VERIFY PASSED` in the run.log, then flip this
  todo with the base/removed/remaining row counts + run.log path as evidence.
- **data_engineering slot-2, 2026-08-15 (session resumption)**: Two updates. (1) **Closes the stale note directly
  above** — its "NOT yet executed" / VM-launcher-wiring plan was carried out within the same original session: a new
  `sports-cf8-tf-delete` category WAS added to `launch-canonical-migration-vm.sh` (`deployment-service@f827fad297`)
  and the `--confirm-prod-write` run completed successfully on VM
  `canonical-migration-sports-cf8-tf-delete-20260815-214633` (dry-run-verified on a sibling VM first, then live) —
  see the P0 todo above for the full run.log path and row counts. This entry exists only so a reader scanning this
  Progress Log's chronological tail doesn't trust a since-superseded plan over the Todos section, which was already
  correct. (2) Root-caused the 14,982-row out-of-window P1 todo (see above): 100% venue=ODDS_API, zero-sibling
  (0/200 sampled), predates this session's bug by over a month, shape matches the sibling IS-surface doc almost
  exactly. No writes made. Remaining open work on this doc: the full CF-8 backfill re-attempt (blocked on a
  maintenance window) and the Cloud Scheduler bypass gap (operator-owned, INFRA P2) — both correctly untouched this
  session.
- **data_engineering slot-2, 2026-08-15 (ship checkpoint)**: the root-cause-profiling extension to
  `audit_sports_captured_phantom_timeframe_2026_08_16.py` cited in the P1 out-of-window todo above landed as
  `market-tick-data-service@53bea812a2` (dry-run-only audit script, no prod write; `quality-gates.sh` green before
  commit; post-push ancestry verified against `origin/live-defi-rollout`). Also filed and pushed
  `unified-trading-pm@982f87d110` — a residual, reproduced `safe-doc-push.sh` gap found while archiving the
  IS-surface doc (a caller-pre-staged `git mv` still trips the pre-fix pathspec error;
  `safe_doc_push_extreme_stash_quarantine_drops_renamed_file_content_2026_08_15.md` P1 todo, not scoped to this
  doc's own investigation). Every actionable item from this session's resumption list is now committed and pushed.
- **data_engineering slot-2, 2026-08-15 (P2 DATA root-cause CLOSED)**: dispatched a read-only Explore agent to trace
  the exact ODDS_API `timeframe`-derivation code path. It returned a conclusive finding: blank-`timeframe` is
  **blank-by-design** in the live manifest writer (`manifest_finalize.py::_write_shard_counts_to_manifest`, never
  passes `timeframe=` for the ODDS_API `data_type="odds"` branch; `ManifestWriter.add()` defaults it to `""`), not a
  bug and not related to the already-fixed `_write_captured_rows()` bug. Full evidence + file:line citations recorded
  directly on the P2 todo above; flipped to `[x]`. Filed a low-urgency P3 follow-up to confirm the sampled
  zero-sibling populations are exclusively `data_type="odds"` (not mixed with `odds_horizon_bucket`) before treating
  the "safe to leave, do not delete" conclusion as fully closed. No code changed — this was pure investigation; no
  cleanup action is scoped or warranted by this finding.
- **data_engineering slot-2, 2026-08-16 (P3 DONE — overturns P2, not confirms it; big finding, operator notified)**:
  ran the P3 confirmation and got the opposite of the expected result. Both audited populations (899,508 IS-side,
  14,982 MDPS out-of-window) are, by construction of the very audits that measured them, 100%
  `data_type="odds_horizon_bucket"` — never `data_type="odds"`. Confirmed two independent ways: the archived IS doc's
  own title/body state the 899,508-row count as an `odds_horizon_bucket`-filtered measurement directly; the MDPS
  14,982-row population came from a script that filters `data_type == "odds_horizon_bucket"` (line 109) before ever
  computing the out-of-window slice. Direct-read of P2's cited write path
  (`manifest_finalize.py::_write_shard_counts_to_manifest`) confirms it is gated on
  `if itype_key == "odds" and data_type_key == "odds":` — it cannot write `odds_horizon_bucket` rows at all, and a
  full-file grep confirms zero references to that data_type anywhere in the 852-line file. P2's mechanism is
  therefore proven not to explain either audited population; the "blank-by-design, safe to leave" verdict rested on
  a write path that never touched the rows in question. Traced the REAL `odds_horizon_bucket` writer to
  `market-data-processing-service`'s `SportsBucketAssignmentAdapter`
  (`bucket_assignment_adapter.py:687`) and found a plausible (not yet confirmed) lead: its
  `supported_timeframes = ["horizon"]` is a literal, non-standard timeframe token that may not survive
  `canonical_writer_shaping.py`'s `_normalise_timeframe()` (not yet read) — filed as a new P1 todo with the full
  evidence trail so the next session can pick it up without re-deriving any of this. Did not attempt any write —
  pure read-only investigation across `market-tick-data-service`, `market-data-processing-service`, and this doc.
  Per the big-finding HARD RULE (data-correctness, cross-repo, contradicts a previously-recorded "safe to leave"
  conclusion), notified the operator directly in-chat this session rather than only filing the todo.
