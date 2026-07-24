---
doc_type: issue
title:
  Drift V2 sig-index parts-cache build downloads FULL file content just to read parquet footer metadata (~110GB, ~40min
  cold-start cost)
summary: >
  `_load_drift_v2_sig_index`'s first-call cache-building loop (market-tick-data-service `solana_defi_drift.py`) calls
  `storage.download_bytes(bucket, name)` to fetch the ENTIRE content of every part file under
  `drift_v2_sig_index_parts/` + `drift_v2_sig_index_parts_gap/` before calling `pq.read_metadata(io.BytesIO(part_raw))`
  to extract the row-group blockTime min/max. The comment above the loop ("Read footer only to track coverage") is
  misleading — it downloads the whole object first, THEN reads the footer from the in-memory bytes. Measured 2026-07-15:
  the two prefixes total ~16,206 parts / ~110.6GB (`gsutil du -s`); confirmed via `/proc/<pid>/io` on a
  freshly-relaunched `mtds-solana-drift-backfill` VM that `rchar` grew to ~24.9GB within ~9 minutes of a cold start,
  consistent with full-file downloads at observed throughput. Every process restart (VM relaunch, SPOT preemption +
  resume) pays this full ~40-minute, ~110GB-egress cost before ANY day-processing can resume, since the metadata cache
  is in-process-memory only (`self._drift_v2_parts_meta_cache`, reset on every new process). Genuine parquet footer
  reads need only the last few KB of each file (footer length + footer) via an HTTP byte-range GET, not the full object.
status: superseded
nature: notes
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [efficiency, gcs-cost, drift, sig-index, cold-start, single-walk]
related: [plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md]
created: 2026-07-15
parent_epic: defi_master
priority: P2
source: [mvp_backfill_defi_onchain_v10-003 verify-todo, data_engineering slot-14]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-15
locked_since:
---

> 🔴 **SUPERSEDED (2026-07-16, operator ruling, verbatim):** "kill drift entirely from our whole system it's pointless —
> Jupiter is the main one let's just use that. kill all other solana perp dex's. uac, code, adaptors, manifest, gcs,
> everything. no instruments no mvp nothing." The DRIFT venue this doc's finding concerns has been **removed entirely**
> (Drift was hacked ~$280M on 2026-04-01, rebranded to Velocity DEX 2026-07-01, now a ~2-week-old private beta with ~$0
> listed TVL) — all Solana perp DEXes are dropped except Jupiter (not integrated). This doc's finding/fix is now moot;
> kept for historical record only. SSOT for the removal: `/codex/04-architecture/solana-defi-coverage.md` (tombstone
> banner).

# Drift V2 sig-index parts-cache full-download inefficiency (2026-07-15)

## What I found

`solana_defi_drift.py`'s `_load_drift_v2_sig_index` first-call cache-building branch, per part file:

```python
part_raw = storage.download_bytes(bucket, name)   # <-- downloads FULL object
...
p_meta = pq.read_metadata(io.BytesIO(part_raw))    # <-- then reads footer from in-memory bytes
```

This downloads the complete content of every `.parquet` part under BOTH `drift_v2_sig_index_parts/` and
`drift_v2_sig_index_parts_gap/` just to extract each part's `blockTime` min/max for the coverage cache —
`pq.read_metadata` only needs the parquet footer (the last few KB: footer length + footer bytes), not the whole file.

Measured today: `gsutil du -s` on the two prefixes = 94.7GB + 15.9GB = **~110.6GB total**, across **~16,206 objects**
(13,909 + 2,297, via `gsutil ls | wc -l`). Confirmed via `/proc/<backfill-pid>/io` on a just-relaunched
`mtds-solana-drift-backfill` VM: `rchar` (cumulative bytes read) reached ~24.9GB within ~9 minutes of a cold process
start, matching the expected full-download pattern (not footer-only reads, which would total well under 1GB for 16K
files).

## Why it matters

The resulting in-process cache (`self._drift_v2_parts_meta_cache`) lives ONLY in memory — it is rebuilt from scratch on
every process (re)start: VM relaunch (as happened today, `mvp_backfill_defi_onchain_v10-003`), SPOT preemption +
auto-resume, or any future code deploy that requires a fresh VM. Each such restart currently pays ~40 minutes of
wall-clock time and ~110GB of GCS egress before ANY day-processing can resume — a real, recurring, avoidable cost that
compounds every time the DRIFT backfill fleet needs to restart (which the fleet's own history shows happens often:
429-exhaustion incidents, quota-restore relaunches, code-fix relaunches like today's).

## Recommended fix (not actioned here — separate, non-trivial change from today's concurrency fix)

Read only the parquet footer via an HTTP byte-range GET instead of downloading the full object:

1. GET the last ~64KB of each part (parquet footer is bounded: 8-byte magic + footer length varint + footer bytes,
   standardly well under 64KB even for wide schemas).
2. Parse footer length from the trailing 8 bytes, GET the exact footer range if the initial 64KB didn't cover it (rare
   fallback).
3. Feed the footer bytes to `pq.read_metadata` (it accepts a `pyarrow.BufferReader` over just the footer — verify the
   exact API needed; `pyarrow.parquet.read_metadata` may need a full-file-shaped reader, in which case use
   `pyarrow.fs.GcsFileSystem` + `pq.ParquetFile(..., pre_buffer=False)` which natively does range-reads under the hood
   instead of hand-rolling it).
4. Only fall back to a full `download_bytes` for parts that actually overlap the requested date window (the EXISTING
   code already does full-content reads for those, correctly, since it needs the actual row data — that part is fine and
   should NOT change).

Consider also persisting the built cache to GCS (a small JSON/parquet manifest keyed by part name → (min_bt, max_bt)) so
a warm-start VM can load a tiny cache file instead of re-scanning 16K objects every time — this would cut the cold-start
cost from ~40min to seconds. Either fix alone (range-reads or a persisted cache) meaningfully helps; both together are
ideal.

## Todos

- [x] ✅ [DATA] P2. Replace `storage.download_bytes` + `pq.read_metadata(io.BytesIO(...))` in
      `_load_drift_v2_sig_index`'s cache-building loop with a footer-only byte-range read (or
      `pyarrow.fs.GcsFileSystem` + `ParquetFile(pre_buffer=False)`) so non-overlapping parts are never fully downloaded
      (repo: market-tick-data-service, `market_tick_data_service/cli/handlers/solana_defi_drift.py`) —
      `market-tick-data-service@4d7e45b4`. Validated against 6 real GCS parts (identical min/max blockTime vs full
      download, ~99% fewer bytes, single 64KB range read each) before shipping. 3 new regression tests (non-overlapping
      never fully downloaded / overlapping still gets full row data / missing-size fallback correct); 15/15 related +
      75/75 full-file tests green; QG exit 0, sentinel `546ddce2` == shipped HEAD.
- [x] ✅ [DATA] P3. Persist the built `_drift_v2_parts_meta_cache` to GCS as a small manifest (part name → min/max
      blockTime) so a fresh process warm-loads it instead of rescanning all parts on every restart (repo:
      market-tick-data-service) — `market-tick-data-service@20f55709`. Reconciled with the concurrent P2 landing
      (`4d7e45b4`, another slot): new parts get a footer-only range read for metadata (P2's fix); an already-known,
      non-overlapping part warm-loaded from the persisted manifest is never touched again on a warm restart (this fix).
      Extracted the build/warm-load/persist logic into a new `solana_defi_drift_parts_cache.py` module (mirrors the
      existing `solana_defi_drift_helius.py` split) to stay under the 900-line file-size gate. 3 new regression tests
      (full-scan-then-persist / warm-start skips cached non-overlapping part / new part merged + re-persisted); QG exit
      0, sentinel `5b36d1e9` == shipped pre-quickmerge-trailer HEAD.

## Progress log

- 2026-07-15: Discovered while relaunching `mtds-solana-drift-backfill` to pick up the concurrency fix
  (`market-tick-data-service@16756a19`, see `mvp_backfill_defi_onchain_v10_2026_06_27.md` Progress Log). Not fixed in
  this session — separate, larger change; filed for a dedicated future pass. `assigned_vm: planning` so the orchestrator
  can pick this up as a standalone backlog item.
- 2026-07-15: P3 shipped (`market-tick-data-service@20f55709`, slot 7). Both todos now complete — the parts-cache
  cold-start cost is addressed from both directions (footer-only reads for new parts, GCS-persisted warm-load for known
  parts). Issue can be closed/archived on the next hygiene sweep.
- 2026-07-15 (same session, data_engineering slot-14): the P2 todo above got auto-ingested into the backlog and
  immediately re-dispatched back to this slot. Implemented + shipped `market-tick-data-service@4d7e45b4` (footer-only
  range-reads via a small `_LazyRangeReadFile` shim over `download_bytes_range` + `_read_parquet_footer_metadata`).
  Validated correctness against 6 real production parts before touching test/production code (byte-identical min/max
  blockTime, ~99% fewer bytes). P3 (persist cache to GCS) remains open — not attempted this session.
