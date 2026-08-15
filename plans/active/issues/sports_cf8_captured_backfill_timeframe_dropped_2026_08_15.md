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
      `/plans/active/issues/sports_is_odds_horizon_bucket_blank_timeframe_odds_api_dominant_2026_08_15.md`. (repo:
      market-tick-data-service, unified-trading-library)
- [ ] [DATA] P1. **NEW finding, 2026-08-15 audit**: 14,982 blank-`timeframe` `data_type=odds_horizon_bucket` rows exist
      on MDPS OUTSIDE the session's 2026-08-15T11:0x-2x UTC window (i.e. NOT created by this session's bug) — a
      population almost as large as the in-window one, previously unknown. Root-cause: are these from an earlier,
      unrelated blank-timeframe write path (a different bug), or a legitimate case where `timeframe` is genuinely blank
      for some `odds_horizon_bucket` rows? Do not assume same disposition as the in-window population without
      independent investigation. (repo: market-tick-data-service)
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
