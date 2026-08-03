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
last_updated: 2026-08-01
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
      remains right now, not the original full corpus.

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
