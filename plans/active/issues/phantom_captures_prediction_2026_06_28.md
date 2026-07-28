---
doc_type: issue
title: Phantom captures — prediction manifest (2026-06-28)
summary: "Manifest: `gcp://market-data-tick-pred-prd-central-element-323112/_index/availability_index.parquet`"
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [manifest, prediction, phantom-captures, data-correctness, backfill, data-status, mtds]
related: []
created: 2026-06-28
parent_epic: observability_master
priority: P2
source: [reconcile_phantom_manifest_rows_all.py, mvp_catalogue_finalization_v10_2026_06_27.md (G3 phantom audit task)]
assigned_vm: planning
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-28
locked_since: 2026-05-21
---

# Phantom captures — prediction manifest (2026-06-28)

> Auto-filed by the G3 phantom-manifest audit
> (`reconcile_phantom_manifest_rows_all.py --asset-group prediction --dry-run`) run during Phase-0 catalogue
> finalization. Found 19,482 `capture_status=captured` rows in the MTDS prediction manifest
> (`market-data-tick-pred-prd-central-element-323112/_index/`) with no backing GCS parquet. These are NOT
> catalogue-shape (they are prediction market data records — book_snapshot_5/trades — not instrument definition files) →
> issue doc per plan triage rule.

## What I found

Manifest: `gcp://market-data-tick-pred-prd-central-element-323112/_index/availability_index.parquet`

- Manifest rows total: 679,245
- Captured rows in scope: 37,188
- Unique (date, venue[, chain], hive-vocab) prefixes listed: 3,059
- **Real captures (parquet exists):** 17,706
- **Phantom captures (captured → no parquet):** 19,482 ← will flip to `attempted_failed` on `--apply`

Phantom distribution by data_type (partial — top 2 shown from audit output):

| data_type       | phantom count |
| --------------- | ------------- |
| book_snapshot_5 | 9,305         |
| trades          | 5,143         |
| (other types)   | ~5,034        |
| **TOTAL**       | **19,482**    |

Note: prediction phantom count (19,482) exceeds real captures (17,706) — meaning more than half of all "captured" rows
in scope are phantoms. This is a significant manifest integrity issue for the prediction AG.

## Why it matters

19,482 phantom rows (52.4% of captured-scope rows) make the prediction availability signal unreliable. Downstream
readers relying on `capture_status=captured` will attempt to read non-existent parquets. The high ratio of phantoms to
real captures suggests a systematic writer failure or manifest/writer desynchronisation over a significant historical
window.

## Recommended decision

1. **Diagnose root cause**: check prediction fetcher/writer history for the phantom date range. Determine if this is a
   writer failure, a manifest double-booking, or a historical data purge without status update.
2. **Apply fix**: `python scripts/reconcile_phantom_manifest_rows_all.py --asset-group prediction` (no `--dry-run`, with
   `MANIFEST_PER_VM_SHARDS=true VM_NAME=pred-reconcile` per consolidator-SSOT) after `prefix_tpls` cover prediction
   data_type shapes.
3. **Backfill**: if real data gaps exist (fetcher outage), backfill missing prediction shards before flipping to
   `attempted_failed`.

Cold-start context: `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` +
`/codex/05-infrastructure/manifest-consolidator-ssot.md` + `/codex/02-data/availability-manifest-and-data-status.md`.

## Todos

- [x] ✅ [CODE] P1. Diagnose prediction phantom root cause (19,675 phantoms = 52% of captured scope — systematic
      failure?). Read `/codex/02-data/availability-manifest-and-data-status.md` first. Repo: `market-tick-data-service`.
      **DIAGNOSIS 2026-06-28T04:58Z (slot-10)**: Analyzed triage JSONL `triage_prediction_20260628_042738.jsonl`. - Date
      range: 2025-03-14 → 2026-06-27 (353 dates, non-clustered, ~55 records/day) - Venue: KALSHI=13,349 |
      POLYMARKET=6,326 - Data types: book_snapshot_5=9,305 | trades=5,336 | prediction_canonical_question_group=5,033 |
      blank=1 - Sample record: KXNFLGAME-26SEP13NODET-DET (2026-06-23 collection date, Sep 2026 NFL game) →
      `manifest_capture_time: 2026-06-24T12:47:43Z` (next-day batch); `parquet_row_count: 0` **ROOT CAUSE**: Writer
      reliability issue — manifest updated to `captured` but GCS write failed silently, OR pre-event contracts (future
      NFL/event games listed on Kalshi) were fetched with 0 trades → manifest says `captured` but no parquet written
      (writer should use `empty_confirmed` for 0-activity contracts). The 353-date spread rules out single outage. The
      `prediction_canonical_question_group` phantoms (5,033) may be IS-style metadata with wrong path templates in the
      phantom checker (data type not MTDS tick data). **CODE FIX needed in MTDS prediction adapter**
      (`market-tick-data-service`): when a contract exists on the collection date but has 0 trades/book5, writer must
      use `empty_confirmed` (not `captured`). The `attempted_failed` flip at 04:29Z is honest; re-attempts will
      re-trigger the same bug unless code fixed first. **Recommend**: Fix writer before re-attempting → re-fetch will
      naturally produce `empty_confirmed` for zero-activity contracts; only genuine data gaps need explicit backfill.
      Filed as CODE bug in MTDS.
- [x] ✅ [SCRIPT] P1. Apply phantom reconciliation for prediction. **DONE 2026-06-28T04:29Z**: 19,675 phantoms flipped
      (cap→attempted_failed); manifest uploaded (688,494 rows). KALSHI 13,349 + POLYMARKET 6,326. Triage JSONL:
      `gs://central-element-323112-phantom-triage/triage_prediction_20260628_042738.jsonl`. Updated count: 19,675 vs
      initial 19,482 (193 new captures since prior dry-run).
- [x] ✅ [CODE] P2. Fix MTDS prediction writer to use `empty_confirmed` for 0-activity contracts (pre-event future
      contracts + genuinely empty trading days). **VERIFIED 2026-07-28 (slot-15, full code-path trace, no new code
      needed — writer-fix half of this todo was already shipped)**: - `kalshi_adapter.py::_collect_kalshi_frames`
      (L637-667) and `polymarket_adapter.py::_fetch_trades_for_market` (trades) + `_fetch_books_for_date` (L761-805,
      book_snapshot_5) each `continue` past a zero-result ticker/token_id — `writer.write_chunk()` is NEVER called for a
      genuinely-empty contract, so no `captured` row can ever be stamped for it (`ManifestWriter.add()` in
      `unified-trading-library/.../_writer_ingest.py:341-381` unconditionally stamps `CaptureStatus.CAPTURED` — the fix
      is upstream of it, in the adapters never writing the chunk at all). - `venue_fetch.py::_record_venue_shard_counts`
      (L465-475) populates `captured_per_instrument_shards` / `shard_counts` ONLY from `writer.underlying_counts`, which
      itself only increments on an actual `write_chunk` call — so the manifest-finalize captured-row path
      (`manifest_finalize.py::_write_shard_counts_to_manifest`) structurally cannot emit a 0-row `captured` record for
      these data_types. - The expected-but-uncaptured case is closed by `sentinels.py::_emit_tier3_for_dt` (L615-772): a
      real transport failure surfaces via `failed_per_dt` (CF-11, landed `21cb2fa6` 2026-06-08 Polymarket / `7455ffb8`
      2026-06-11 Kalshi) → `record_failed` (`attempted_failed`); a lifecycle-window miss → `record_expected_empty`
      (prediction Tier-3 lifecycle gate, landed 2026-07-14, tested in
      `tests/unit/engine/test_sentinels_prediction_lifecycle_tier3.py`); otherwise →
      `record_empty(SOURCE_RETURNED_ZERO)` (`empty_confirmed`) — never `captured`. `trades`/`book_snapshot_5` are
      confirmed in UAC `_PER_INSTRUMENT_SHARD_DATA_TYPES` (`market_data_categories.py:2406`) so both venues route
      through this Tier-3 path, not the venue-level Tier-2 path. - CF-11 coverage for both venues has dedicated
      regression tests (`tests/unit/test_kalshi_cf11_fetch_failure.py`,
      `tests/unit/test_polymarket_cf11_fetch_failure.py`) that predate + postdate this pass. - QG evidence: did NOT
      re-run `quality-gates.sh` locally (host was at load 56/16 cores, 934Mi free RAM, 13Gi swap used at verification
      time — re-running risked the same OOM class as `plans/active/issues/` host-overload incidents already on record).
      Used CI instead: `market-tick-data-service`'s `quality-gates-v2` on `live-defi-rollout` is GREEN as of runs
      `30370413969`/`30364200148`/`30359839136` (2026-07-28, all `completed       success`), which post-date the
      adapters' most recent commits (`b7272103` 2026-07-27, `84154e1a` 2026-07-28) — satisfies the Gate's "QG green"
      clause without adding load to an already-overloaded shared host. - **Re-fetch / backfill scope descoped from this
      todo**: the "THEN determine true data gaps by re-running the daily fetcher across 2025-03-14→2026-06-27 ...
      backfill via `launch-mtds-prediction-backfill-vm.sh` / `launch-kalshi-bulk-seed-vm.sh`" clause is a separate, much
      larger operator-scale VM backfill effort (15 months of history, live API credential + cost implications) — out of
      scope for this CODE todo's done_definition ("Checkbox flipped in plan + code shipped"). Filed as a follow-up so it
      isn't silently dropped: see `## Deferred work after 2026-07-28` below. - Tracked home cross-reference unchanged:
      `plans/active/cross_cutting_consolidated_closeout_2026_07_25.md` Track 22 already cites this doc.

- [ ] [SCRIPT] P2. Re-run the KALSHI/POLYMARKET daily fetcher across 2025-03-14→2026-06-27 (the 19,675 rows reconciled
      to `attempted_failed` by the P1 todo above) to classify each shard as a TRUE data gap (fetch returns real
      trade/book data — needs explicit backfill) vs. correctly-empty (0-activity contract — now writer-honest, no
      backfill needed) now that the writer fix (this doc's P2 todo, verified 2026-07-28) prevents new phantoms. Backfill
      any TRUE gaps found via `launch-mtds-prediction-backfill-vm.sh` (POLYMARKET, repo: `deployment-service`) and
      `launch-kalshi-bulk-seed-vm.sh` (KALSHI, repo: `deployment-service`) — SPOT provisioning per the backfill-VM
      default, idempotent re-run safe. Repo: `market-tick-data-service` (fetch) + `deployment-service` (launchers).
      Descoped from the writer-fix todo above because it is a 15-month live-API re-fetch + operator-scale VM backfill,
      not a code change.
