---
doc_type: issue
title: Reconcile MDPS cefi candle-manifest rows orphaned by pre-fix-era OOM crashes (real files, zero manifest row)
summary: >-
  Extracted from `mdps_cefi_candle_manifest_never_emitted_2026_07_26.md` (archived, resolved) before archival so its
  still-open P2 follow-up survives as its own tracked, AO-eligible unit rather than being silently buried inside a
  resolved doc. That doc's root-cause trace confirmed MDPS's candle-manifest emission logic is correct TODAY, but found
  a genuine PAST (already-fixed-going-forward) gap: any `processed_candles/` parquet file written by a backfill VM that
  OOM-crashed mid-run BEFORE `market-data-processing-service@335e9cc` landed (the per-date memory-scaling OOM fix) may
  have lost its in-flight `ManifestWriter.record_captured` write, leaving real file content on disk with zero manifest
  row — confirmed for BITGET-FUTURES/BITFINEX-FUTURES/KRAKEN-FUTURES `day=2026-05-03` specifically. The corpus-wide
  extent of this orphan set is unknown.
status: resolved
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service, unified-trading-library]
scope: [engineer]
tags: [mdps, candle, manifest, cefi, reconciliation, backfill, oom]
related:
  [
    /plans/archive/2026_07/cefi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/archive/issues/mdps_cefi_candle_manifest_never_emitted_2026_07_26.md,
    /plans/active/issues/mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-31"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: advance-code
source: >-
  Extracted 2026-07-26 (cicd plan_health wall-clear, escalation agt-37cd1c) from
  `/plans/archive/issues/mdps_cefi_candle_manifest_never_emitted_2026_07_26.md`'s unresolved P2 todo, at archival time,
  per CLAUDE.md issue-doc-lifecycle (never archive a doc while leaving real open work stranded inside it).
locked_by:
locked_since:
resolved_by: slot-5-review-2026-07-31
depends_on: []
---

> **🟢 ARCHIVED 2026-08-02** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Resolution evidence carried in `resolved_by:` (slot-5-review-2026-07-31). Moved by the
> `/plan-reconcile` whole-corpus run of 2026-08-02, which found this doc sitting in `plans/active/issues/` at a terminal
> status — `check_terminal_status_archived` was RED at 13 violations against a baseline of 1. No content was rewritten.

> **🟢 RESOLVED 2026-07-31 (slot-5, `review`).** This doc's own todo is superseded, not executed as written — the
> corpus-wide `backfill_candle_manifest.py` campaign in
> `/plans/active/issues/mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md` (todo 2, DONE 2026-07-27) closed
> this exact gap as a byproduct, via a DIFFERENT tool than the `merge_manifest_from_canonical_paths()` recipe below
> (which was never run). See "Resolution" section under the todo for the live-verified evidence. Archived here;
> superseded by the corpus-wide doc above.

# MDPS cefi candle-manifest: reconcile pre-fix-era orphaned rows

## What I found

See the parent doc's "Root cause (found 2026-07-26, slot-12 `data_engineering`)" section for the full trace. Summary:
MDPS's candle-manifest emission path is correct today (live-verified for both `pipeline_mode=batch_hyperliquid` and
`batch_tardis`), but candle files written by a backfill VM that OOM-killed mid-run BEFORE
`market-data-processing-service@335e9cc` (the per-date memory-scaling OOM fix) may have lost their in-flight
`ManifestWriter.record_captured` write — real file, zero manifest row, forever, unless reconciled. Confirmed for
BITGET-FUTURES/BITFINEX-FUTURES/KRAKEN-FUTURES `day=2026-05-03`; the full extent across dates/venues is unmeasured.

## Recommended fix path

> **🟥 CORRECTED 2026-07-27 (slot-12) — the original recipe below was UNSAFE, caught before execution.**
> `rebuild_manifest_from_canonical_paths(bucket, service_name="market-data-processing-service", prefix="processed_candles/by_date")`
> does **not** "only add missing rows" — it builds its output purely from the `prefix` walk and **uploads that as the
> bucket's WHOLE consolidated manifest index**, silently deleting every OTHER prefix's rows sharing the same bucket. The
> CEFI tick bucket co-locates `raw_tick_data/` (MTDS, millions of rows) with `processed_candles/` (MDPS) in ONE index —
> running this as originally written would have wiped essentially the entire CEFI raw-tick manifest to backfill a
> comparatively tiny candle-orphan set. Full analysis + fix:
> `/plans/active/issues/rebuild_manifest_from_canonical_paths_prefix_scoped_wipe_2026_07_27.md`. **Do not run the
> original recipe.**
>
> **UNBLOCKED 2026-07-27 (slot-12)** — the additive fix shipped: `unified-trading-library@2352e7c8` adds
> `merge_manifest_from_canonical_paths(bucket, service_name="market-data-processing-service", prefix="processed_candles/by_date")`,
> which only backfills genuinely-missing shard keys and leaves every other row (including the MTDS raw-tick rows sharing
> this bucket) untouched — 2 regression tests prove it directly. This todo can now proceed via that function; still
> requires a Tier-2 SPOT VM run per the heavy-I/O rule (not attempted in this session — the actual reconciliation run is
> separate follow-up work).

- [x] ✅ [DATA] P2. **SUPERSEDED, not executed as written — 2026-07-31 (slot-5, `review`).** The specific gap this todo
      targeted (candle files orphaned by PAST OOM crashes before `market-data-processing-service@335e9cc` landed,
      confirmed for BITGET-FUTURES/BITFINEX-FUTURES/KRAKEN-FUTURES `day=2026-05-03`) is now CLOSED — but via the
      corpus-wide `backfill_candle_manifest.py` campaign
      (`/plans/active/issues/mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md` todo 2, DONE 2026-07-27,
      `market-data-processing-service@cf94e23` + `deployment-service@fafde10`/`@b947d9f`), NOT the
      `merge_manifest_from_canonical_paths()` recipe this todo prescribed (that function was shipped
      `unified-trading-library@2352e7c8` but never actually invoked against prod — no VM launch for it exists in any
      log). The corpus-wide backfill's `backfill_candle_manifest.py` is record-only (footer-reads each report row's
      object at its existing path, calls `record_captured`, never deletes/re-uploads/rebuilds the index), so it carries
      the same non-destructive safety property this todo's corrected recipe was designed to guarantee — just via a
      different, already-shipped tool that happened to sweep the WHOLE cefi candle corpus (not just this doc's
      3-venue/1-day known slice), superseding the narrower scope entirely.

      **Live-verified 2026-07-31** (read-only spot-check, `read_availability_index` with a single-day
                          `filters=[("date",">=","2026-05-03"),("date","<=","2026-05-03")]` row-group-pushdown read — not a corpus walk):
                          all three flagged venues now carry real `captured` MDPS manifest rows for `day=2026-05-03`:
                          - `BITGET-FUTURES`: 29 rows (`trades`/`derivative_ticker`/`book_snapshot_5`/`liquidations` × all 7 timeframes),
                            `written_at` spanning `2026-07-26T23:10:28Z` (the archived `mdps_cefi_candle_manifest_never_emitted_2026_07_26.md`
                            doc's own live-trace `--force`-reprocess test of this exact shard) through `2026-07-27T16:23:49Z` (the
                            corpus-wide backfill campaign's cefi VM, `backfill-candle-manifest-cefi-20260727-151741`).
                          - `BITFINEX-FUTURES`: 14 rows (`derivative_ticker`/`liquidations` × all 7 timeframes), `written_at` uniformly
                            `2026-07-27T16:23:49.93-.95Z` — entirely from the corpus-wide backfill VM (no rows predate it for this venue).
                          - `KRAKEN-FUTURES`: 7 rows (`derivative_ticker` × all 7 timeframes), `written_at` uniformly
                            `2026-07-27T16:23:49.97-.98Z` — same corpus-wide backfill VM.

                          This doc's own "done when" bar (previously-orphaned shards show real manifest rows; the reconciliation run is
                          evidenced) is satisfied by the corpus-wide backfill's evidence trail instead of a dedicated run of this todo's
                          recipe. The MTDS raw-tick-row-unchanged safety check this todo called for is satisfied by construction —
                          `backfill_candle_manifest.py` only ever calls `record_captured` for `processed_candles/` shard keys it footer-read
                          from the sweep report, never touching or rebuilding any other prefix's rows (unlike the original unsafe
                          `rebuild_manifest_from_canonical_paths` call this doc's own corrected banner already ruled out).

## Progress Log

- **2026-07-31** (AO dispatch, slot 5, `review`) — Dispatched as `mdps_candle_manifest_near_total_coverage_gap-004`'s
  own REVIEW cross-check todo (is this doc's narrower CEFI-only scope superseded by the corpus-wide
  near-total-coverage-gap measurement + backfill?). Verdict: YES. Live-verified via a single-day, row-group-pushdown
  `read_availability_index` read (not a corpus walk) that BITGET-FUTURES/ BITFINEX-FUTURES/KRAKEN-FUTURES
  `day=2026-05-03` — the exact shards this doc's own evidence named — now carry real `captured` MDPS manifest rows, with
  `written_at` timestamps matching the corpus-wide `backfill_candle_manifest.py` campaign's cefi VM
  (`backfill-candle-manifest-cefi-20260727-151741`, finished ~16:23:49Z 2026-07-27) plus (for BITGET-FUTURES
  specifically) the earlier 2026-07-26T23:10Z live-trace test from the now-archived
  `mdps_cefi_candle_manifest_never_emitted_2026_07_26.md`. This doc's own recommended-fix recipe
  (`merge_manifest_from_canonical_paths()`) was never actually invoked against prod — the gap closed via the corpus-wide
  campaign instead, which happens to satisfy this doc's own "done when" bar and non-destructive safety property by
  construction. Flipped the todo, archiving this doc per the 6-step ritual (referrers fixed in the same commit).
