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
- [ ] [DATA] P0. Once the fix above ships, identify + clean up the phantom timeframe-blank rows this session created on
      MDPS (~26,982 lower-bound, `data_type=odds_horizon_bucket`, `written_at` in the 2026-08-15T11:0x-2x UTC window,
      `timeframe` blank) — either delete them (they carry no information the corrected rewrite won't re-derive) or leave
      them as harmless-but-wasteful duplicates if delete-safety can't be cleanly established; snapshot first, verify via
      row-count before/after. Also audit whether the same class of phantom row exists on IS from the 500-row test there.
      (repo: market-tick-data-service, unified-trading-library)
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
