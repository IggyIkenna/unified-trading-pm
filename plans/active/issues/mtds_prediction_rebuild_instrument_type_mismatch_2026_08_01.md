---
doc_type: issue
title:
  rebuild_prediction_manifest.py's stale instrument_type="prediction" literal duplicated ~2,700+ manifest rows during
  the available_at backfill apply
summary: >
  Executing mtds_available_at_cross_asset_backfill_2026_07_13.md's prediction apply todo (-001, full-range
  rebuild_prediction_manifest.py --chunk-days) inflated the live prediction canonical manifest by ~2,700+ duplicate rows
  and left the real historical captured rows' available_at still blank (measured post-apply fill rate 20.08%, not the
  ~100% the plan expected) — every historical month showed EXACTLY 50% fill rate, the signature of a 1-old+1-new row
  pair per real cell. Root cause: rebuild_prediction_manifest.py's BUNDLED_INSTRUMENT_TYPE hardcoded the stale literal
  "prediction" (lowercase), while the live writer (engine/orchestrator/manifest_finalize.py's
  _finalize_prediction_bundles) stamps the UAC canonical InstrumentType.PREDICTION_MARKET.value ("PREDICTION_MARKET") —
  fixed there at market-tick-data-service@1ec415f8 (2026-07-19) for this EXACT failure mode ("a --force rebuild ...
  resurrected the migration's removed stragglers"). Since instrument_type is a manifest-consolidator dedup-key column,
  the mismatch meant every backfilled row landed on a NEW dedup key instead of updating the existing captured row —
  duplicating rather than backfilling. The rebuild script's own constant was never updated to match the 2026-07-19
  live-writer fix. Fixed in market-tick-data-service@b8a8fa7a (this session); the backfill apply is being re-run with
  the corrected script so it now updates history in place. The ~2,700+ duplicate rows already written under the stale
  key are a SEPARATE, operator-gated cleanup (todo 2 below) — an existing sanctioned tool
  (canonicalize_prediction_manifest_2026_07_18.py --remove-stragglers) already exists for exactly this, but its --apply
  path is explicitly HELD pending operator authorization by the script's own design.
status: open
nature: issue
asset_group: [prediction]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [data-correctness, available-at, manifest-writer, prediction, instrument-type, dedup-key, straggler-rows]
related:
  [
    /plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: 2026-07-31
parent_epic: manifest_master
priority: P1
source:
  mtds_available_at_cross_asset_backfill_2026_07_13.md task mtds_available_at_cross_asset_backfill-006, slot 4,
  2026-08-01
assigned_vm: planning
execution_scope: orchestrator-agent
locked_by:
resolved_by:
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-03
context_scope:
  [
    /plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    market-tick-data-service/market_tick_data_service/scripts/_rebuild_prediction_emit.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/manifest_finalize.py,
    market-tick-data-service/scripts/canonicalize_prediction_manifest_2026_07_18.py,
  ]
---

# rebuild_prediction_manifest.py instrument_type mismatch — duplicate rows during available_at backfill

## What I found

Picking up `mtds_available_at_cross_asset_backfill_2026_07_13.md` task `-006` ("Resume the prediction consolidator
cron"), a prior session had already run `-001`'s apply
(`rebuild_prediction_manifest.py --start-date 2021-06-30 --end-date 2026-07-31 --chunk-days 60/30`, per the plan's own
instruction) to completion in the background — confirmed via the GCS per-VM shard fragment listing (44 chunk fragments +
1 final CF-11 reemit, spanning the full range).

Force-consolidating (`manifest_consolidator --force`) and running the `available_at` fill-rate audit
(`plans/audit/results/available_at_fill_rate_audit_2026_07_13.py`'s logic, scoped to the prediction bucket) showed:

- Overall fill rate on `capture_status=captured` rows: **20.08%**, not the near-100% the plan's own reasoning expected
  for prediction ("prediction's entire captured-row corpus is bundled-by-design ... a full-date-range re-run backfills
  the full prediction corpus").
- **Every one of 62 historical months read EXACTLY 50.0% filled** (e.g. `2022-01: 124 captured, 62 filled`) — a strong
  signature of a systematic 1-old-unfilled + 1-new-filled row DUPLICATE per real cell, not a partial backfill.
- Row count rose by exactly the backfill's own new-row count after consolidation (1,949,995 → 1,952,699, +2,704),
  confirming NET NEW rows were added rather than existing rows being updated.

Row-level diagnosis (`market-tick-data-service`, `service_name=market-tick-data-service`, month `2022-01`) found the
old/unfilled rows carry `instrument_type="PREDICTION_MARKET"` (uppercase, `written_at≈2026-07-10`) while the rebuild's
new/filled rows carry `instrument_type="prediction"` (lowercase, `written_at≈2026-07-31/08-01`, matching this backfill's
own run window) — different strings, so they never collide on the manifest-consolidator's dedup key (`instrument_type`
is one of `_SHARD_DEDUP_KEY`'s optional columns, `unified_trading_library/manifest_consolidator.py`) and both persist as
separate rows.

Confirmed via code read: `market_tick_data_service/scripts/_rebuild_prediction_emit.py:43` hardcoded
`BUNDLED_INSTRUMENT_TYPE = "prediction"`. The live writer,
`market_tick_data_service/engine/orchestrator/manifest_finalize.py`'s `_finalize_prediction_bundles()` /
`_finalize_prediction_unclassified()`, stamps `InstrumentType.PREDICTION_MARKET.value` on the SAME shard atom's
`record_captured_from_counts`/`record_failed` row_key — fixed there at `market-tick-data-service@1ec415f8` (2026-07-19,
`fix(prediction): stamp canonical PREDICTION_MARKET at CQG-bundle writer root`), whose own commit message describes this
EXACT failure mode: _"a --force rebuild then RE-STAMPED the lowercase value and resurrected the migration's removed
stragglers... Emitting the canonical value here makes a rebuild reproduce exactly what --bundle-mode normalize writes."_
The rebuild script's own constant was never updated to match — confirmed via git log: its only two touches since
(`5bf8a3c7` file-size-gate split, `749ca622` `--chunk-days` addition) never touched the value.

This exact gap was ALSO already flagged as "FINDING 2" in
`market-tick-data-service/scripts/canonicalize_prediction_manifest_2026_07_18.py`'s own docstring (a Phase-B
prediction-manifest canonicalization migration authored 2026-07-18, one day BEFORE the live-writer fix landed) — its
"WRITER-ROOT FIX IS REQUIRED" checklist step 0 named both the live bundle writer and the per-CID writer as needing the
fix; it did not separately call out this rebuild/backfill script as a third write-root, but the same gap applies to it
identically.

## Why it matters

- The `mtds_available_at_cross_asset_backfill_2026_07_13.md` plan's prediction apply (`-001`) did NOT achieve its stated
  goal — the real historical captured rows are still blank on `available_at`.
- The live prediction manifest canonical is now inflated by ~2,700+ orphaned rows carrying a non-canonical
  `instrument_type`, a data-hygiene regression on top of the missed backfill.
- Any future `--force` (or plain) re-run of the (pre-fix) rebuild script would keep adding MORE such duplicates — this
  was a standing, repeatable bug, not a one-time fluke, confirmed by the 1ec415f8 commit message describing the
  identical failure mode occurring once before at the live-writer root.
- Per CLAUDE.md "Data pipeline correctness is the heartbeat" — this is a data-correctness finding requiring an issue
  doc + notification, which this document is.

## Recommended decision

1. Ship the code fix (done, see todo 1) and re-run the prediction apply with the corrected script so it updates the
   existing canonical `PREDICTION_MARKET`-keyed rows in place (same dedup key as the live writer) instead of creating
   more duplicates.
2. For the ~2,700+ pre-existing duplicate rows (from this session's pre-fix apply, plus whatever pre-existing drift
   `canonicalize_prediction_manifest_2026_07_18.py`'s own FINDING 2 already measured at ~652k stragglers corpus-wide as
   of 2026-07-18): that script's `--remove-stragglers --apply --confirm-prod-write` path is the SANCTIONED,
   already-built tool for an in-place CAS-REPLACE cleanup (snapshot-first, STOP-ON-SURPRISE guard against ever dropping
   a captured cell). Its docstring explicitly says the Phase-B prod run is HELD pending operator authorization and "do
   NOT self-execute" — recommend the operator review whether that HELD status should now lift, since its own checklist's
   step 0 (writer-root fix) is now fully landed at BOTH points (live writer 2026-07-19, this rebuild script 2026-08-01)
   — and if so, authorize a fresh dry-run + `--remove-stragglers --apply --confirm-prod-write` pass
   (pause/snapshot/apply/resume the consolidator cron per its own checklist).

## Todos

- [x] [DATA] P1. Fix `_rebuild_prediction_emit.py`'s `BUNDLED_INSTRUMENT_TYPE` to thread
      `unified_api_contracts.InstrumentType.PREDICTION_MARKET.value` instead of the stale local literal; add a
      regression test pinning the value. (repo: market-tick-data-service) — ✅ 2026-08-01 (data_engineering slot-4):
      `market-tick-data-service@b8a8fa7a`, quality-gates.sh green.
- [ ] [OPERATOR] P2. Review + decide whether to lift `canonicalize_prediction_manifest_2026_07_18.py`'s HELD prod-run
      status now that its checklist's writer-root-fix step 0 is fully landed (live writer 1ec415f8 + this rebuild script
      b8a8fa7a); if authorized, run a fresh `--remove-stragglers` dry-run against the LIVE prediction index to size the
      current straggler count, then (separately, after review) `--remove-stragglers --apply --confirm-prod-write` per
      that script's own operator-review checklist (pause/snapshot/apply/resume the consolidator cron). (repo:
      market-tick-data-service) — **Step 2 (dry-run) DONE 2026-08-03 (interactive session)**:
      `GCP_PROJECT_ID=central-element-323112 DEPLOYMENT_ENV=prod .venv/bin/python     scripts/canonicalize_prediction_manifest_2026_07_18.py --remove-stragglers`
      (bundle-mode=normalize, default) run live against the real 1,970,331-row canonical index. Results: **22,641
      stragglers** would be removed (rows_in 1,970,331 -> rows_out 1,947,690); corrected-target rows 2,477 `data_type` +
      902,636 `instrument_type` + 11 `source`. Safety check passed clean: CAPTURED cells 345,405 in -> 345,405 out (no
      STOP-ON-SURPRISE regression). **Steps 3-6 (pause consolidator / apply / resume / verify) NOT yet run — awaiting
      explicit operator go-ahead** per the script's own checklist gating on both `--apply` AND `--confirm-prod-write`,
      plus the separate consolidator-pause action this involves. Note: the 22,641 figure is smaller than FINDING 2's
      original corpus-wide ~652k straggler estimate (2026-07-18) — consistent with the doc's own note above about a
      pre-fix/partial apply having already cleaned most of the corpus in an earlier session; this dry-run reflects what
      remains right now, not the original full corpus. **Steps 3-6 (pause/apply/resume/verify) DONE 2026-08-03
      (interactive session, operator-authorized)** — see todo P3 below: the apply is NOT durable yet, a second, much
      larger straggler batch resurrected within ~20 minutes and needed a second full pause/apply/resume pass.
- [x] ✅ [DATA] P3. **NEW 2026-08-03 (interactive session).** **CORRECTION to an intermediate claim made earlier the
      same session** (recorded here for the record, not silently edited away): I first suspected the BATCH per-CID
      writer (`engine/orchestrator/manifest_finalize.py::_write_shard_counts_to_manifest`) was the unfixed gap, since it
      passes `instrument_type=itype_key` through verbatim. That is WRONG — `itype_key` reaches that function ALREADY
      canonical for prediction venues, stamped upstream in
      `engine/orchestrator/venue_fetch.py::_record_venue_shard_counts`
      (`if _is_prediction_market_venue(venue):     manifest_itype = InstrumentType.PREDICTION_MARKET.value`,
      `market-tick-data-service@71761d7f`, **2026-07-19** — predating the bad rows I'd found by over a week, which is
      what made the "never fixed" claim implausible on a closer look). A test already locks this exact chain
      (`tests/unit/engine/test_manifest_finalize_coverage.py::test_prediction_per_cid_manifest_row_stamps_canonical_prediction_market`).
      **The REAL, empirically-traced root cause**: the LIVE websocket-streaming capture path uses a COMPLETELY SEPARATE
      manifest-write mechanism (`live/websocket_runner.py`'s `LiveWebsocketRunner` + `live/_ws_window_helpers.py`'s
      `record_flush_captured`/`record_flush_failed`, backed by `live/manifest_recorder.py::MTDSShardManifestRecorder`)
      that the 2026-07-19 fix never touched — `instrument_type` there originates from
      `WsInstrumentBuffer`/`ReceivedTick.instrument_type`, which real Kalshi/Polymarket ticks never populate (no such
      field on the raw exchange message), so every live-captured prediction `book_snapshot_5`/`trades` row landed with a
      null `instrument_type`. Confirmed exactly matching the empirical 869,743-row resurrection: the 4 shard files
      causing it (`_index/per_vm/prediction-live-{kalshi,polymarket}-{book-snapshot-5,trades}-20260727-*.parquet`) are
      this LIVE runner's own continuously-appended output, not batch shards. `live/backfill_runner.py`'s
      `GapBackfillRunner` (a separate REST gap-fill scaffold, same manifest-recorder dependency) had the identical
      hardcoded `instrument_type=None` gap, though its own docstring flags it as framework-only/no venue adapters
      plugged in yet — fixed anyway for when one lands. **Shipped**: `market-tick-data-service@12992663` — canonical
      stamping (`asset_group == "prediction"` gate — simpler than `_is_prediction_market_venue`, and `asset_group` was
      already in scope at every call site, so no new cross-package import needed) at all 5 real call sites across the 3
      files (`_ws_window_helpers.py`'s 2 funnel functions, `websocket_runner.py`'s 3 `record_zero_rows`/`record_failed`
      calls, inlined rather than a dedicated helper method after the first attempt pushed the file to 916 lines against
      its 900-line cap, `backfill_runner.py`'s 2 calls), plus regression tests in `tests/unit/test_websocket_runner.py`
      (3 new tests) and `tests/unit/live/test_backfill_runner.py` (1 new test) — all pinning
      `instrument_type == "PREDICTION_MARKET"` for a prediction venue on every affected path. `quality-gates.sh` green.
      **Deployed + verified durable 2026-08-03 (interactive session, continued, operator-authorized)**: confirmed via
      the tarball manifest (`gs://deployment-scripts-.../code/mtds-code.manifest.json`, `commit_sha` = this exact
      commit, git-ancestor-verified not just string-matched) that the auto-rebuild scheduler already picked up the fix.
      The 4 live capture VMs (`prediction-live-{kalshi,polymarket}-{trades,book-snapshot-5}-20260727-*`) had been
      running continuously since 2026-07-27 — no in-place code-refresh path exists for this VM class (confirmed:
      `lc_verify_tarball_freshness` only warns, never re-pulls into a running VM) — so each was deleted + relaunched via
      `deployment-service/scripts/vm/launch-prediction-live.sh --venue <V> --data-type <DT>` onto the fresh tarball,
      verified RUNNING + actively writing manifest shards + emitting `PIPELINE_HEARTBEAT` at T+10min (bounded ~1min
      capture gap per shard during the swap, matching documented precedent for this exact VM family). Then ran
      `--remove-stragglers --apply --confirm-prod-write` a THIRD time (same safe-abort-and-retry-once pattern as rounds
      1-2 — a CAS race, no corruption) — 2,890,271 → 2,020,528 rows, 869,743 stragglers removed, 351,191 captured cells
      in/out (no regression). **This time it held**: a fresh read ~7 minutes and several consolidator cycles later shows
      0 null `instrument_type` rows and the canonical row count grew NORMALLY (+74,784 legitimate new live-captured
      rows, all stamped canonical) — "Nothing to canonicalize — every target is already canonical." The durability gap
      this todo opened with is closed. (repo: market-tick-data-service, deployment-service)

## Progress Log

- 2026-08-01 (data_engineering slot-4): filed this doc mid-dispatch on
  `mtds_available_at_cross_asset_backfill_2026_07_13.md` task `-006`; shipped the code fix
  (`market-tick-data-service@b8a8fa7a`); re-running the prediction apply with the corrected script (see that plan's
  Progress Log for the re-run's own checkpoint).
- **context-scout 2026-08-03**: populated context_scope (6 entries).
- **2026-08-03 (interactive session)**: backlog dispatch for this task hadn't been picked up after 2+ hours (546 queued,
  ordinary depth, not stuck) — operator asked me to run the dry-run directly to unblock. Ran it live (see todo P2's
  DONE-step-2 entry above for full numbers). Did NOT proceed to steps 3-6 (pause consolidator / apply / resume / verify)
  — that's a separate, harder-to-reverse action (live scheduler pause + CAS-write to the prod canonical index) the
  operator explicitly wants to review the numbers on first ("lemme know when they come back so we can run apply").
- **2026-08-03 (interactive session, continued) — operator authorized the full apply chain.** Ran it twice. **Round 1**:
  paused `uts-prod-manifest-consolidator-market-data-prediction-cron` via the maintenance-window primitive
  (`deployment_service.data_pipeline_monitors.scheduler_maintenance`), ran
  `--remove-stragglers --apply --confirm-prod-write` — first CAS attempt aborted safely (generation mismatch, an
  already-in-flight consolidator cycle raced the read-mutate-write window; no partial write, script's own guard worked
  as designed), retried once the window confirmed still held by me and it succeeded: 1,970,331 -> 1,947,690 rows, 22,641
  stragglers removed, 345,405 captured cells in/out (no regression). Resumed the cron. A fresh read confirmed 100%
  canonical (0 non-canonical rows) immediately after. **Then, as the "verify no resurrection" step, found a NEW
  869,743-row non-canonical population had reappeared ~20 minutes later** — traced this to root cause (see new todo P3
  above): the per-CID writer was never actually fixed, only the bundle writer was. **Round 2** (same operator
  authorization, since this was diagnosed as the SAME durability gap the script's own docstring warns about, not a new
  ask): paused again, ran `--remove-stragglers --apply --confirm-prod-write` a second time (same safe-abort-and-retry
  pattern on the first CAS attempt), 2,817,433 -> 1,947,690 rows, 869,743 stragglers removed, 345,409 captured cells
  in/out (no regression), resumed the cron. Both snapshots taken to `_index/backups/` before each write, per the
  script's own safety design. Filed the root-cause + fix recommendation as new todo P3 (this is a recurring cleanup need
  until the per-CID writer fix ships, not resolved by re-running the apply alone). **Correction to this doc's own
  earlier claim**: the 2026-08-01 entry and this doc's original "What I found" section said FINDING 2's checklist step 0
  named BOTH the bundle and per-CID writers as needing the fix, but only ever reported the bundle one (`1ec415f8`) as
  actually shipped — the per-CID half was silently left undone and never flagged as still-open until this session's
  empirical resurrection forced the investigation. **Also, en route**: diagnosed and corrected a red herring in my own
  reasoning — a local timestamp mismatch I initially attributed to "~37-40 minutes of clock drift" turned out to be
  simply BST (UTC+1) vs UTC display, not drift; see `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` for the
  durable note on checking a cloud resource's own UTC timestamp rather than trusting a local script's
  `%(asctime)s`-formatted log line when reasoning about elapsed time.
- **2026-08-03 (interactive session, continued) — fixed the real root cause (P3), operator-directed ("fix root**
  **cause").** Traced the actual gap (see P3's DONE entry): my FIRST hypothesis (batch per-CID writer never fixed) was
  wrong and self-corrected before shipping anything on it — `venue_fetch.py::_record_venue_shard_counts` already
  canonicalizes prediction per-CID rows, landed `71761d7f` (2026-07-19), with its own regression test. The REAL gap was
  the LIVE websocket-streaming path (`live/websocket_runner.py` + `live/_ws_window_helpers.py`, backed by
  `live/manifest_recorder.py`), which the 2026-07-19 fix never touched — confirmed by matching the exact 4 shard files
  causing the empirical resurrection to this runner's own continuously-appended output. Also fixed the same gap in
  `live/backfill_runner.py`'s `GapBackfillRunner` (framework-only scaffold, no venue adapter plugged in yet, but same
  bug). Shipped `market-tick-data-service@12992663` with 4 new regression tests. Hit + fixed a file-size ratchet
  violation along the way (`websocket_runner.py` pushed to 916L against the 900L cap by my first attempt at this fix;
  trimmed to exactly 900L by inlining the canonicalization check instead of adding a dedicated helper method+instance
  attribute) and rode out one unrelated foreign ratchet failure (`scripts/pipeline_e2e_check.py`'s
  `# type: ignore`-count ratchet, a false-positive matching a comment that merely MENTIONS the string in prose, not a
  real suppression — resolved on retry once whatever concurrent session caused it also resolved it, never touched by
  this change).
