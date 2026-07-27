---
doc_type: issue
title:
  Long-running per-VM-sharded backfills eventually OOM — ManifestWriter's per-VM shard read-merge-write grows with
  cumulative shard size, not bounded by any single date's work
summary: >-
  `af-backfill-20260726-110610` (sports FIXTURES backfill) crashed `exit_code=137` after running cleanly for ~20.5 hours
  / 2,400+ dates / ~159,000 accumulated per-VM manifest shard rows — NOT a repeat of the previously-fixed
  unfiltered-manifest-read OOM class (zero enrichment calls were queued this run). Root-caused to
  `unified_trading_library.manifest_writer.ManifestWriter._flush_per_vm_pending`: every flush downloads, parses, merges,
  re-serializes, and re-uploads the ENTIRE existing per-VM shard — a correctness requirement for concurrent writers
  sharing one shard object (e.g. MDPS's per-unit finalize threads), but one whose peak memory and I/O cost per flush
  grows linearly with cumulative shard size. A single process that runs long enough (regardless of how efficient any
  individual date's processing is) will eventually exceed available memory once its own per-VM shard gets large enough.
  Fixed for the sports FIXTURES launcher by routing it through the EXISTING chunked `instruments-backfill` VM_TASK
  (90-day chunks, fresh process per chunk) instead of the unbounded single-shot dispatch — a launcher-only change, zero
  shared library/dispatcher code touched. Flagging as a corpus-wide finding because ANY launcher still using the generic
  single-shot dispatch for a genuinely multi-year date range carries the same latent risk.
status: open
resolved_by:
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [deployment-service, unified-trading-library, instruments-service]
scope: [engineer]
tags: [oom, memory-leak, manifest-writer, per-vm-shard, backfill, vm-launcher, recurring-bug-class]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/active/issues/read_availability_index_unfiltered_callsite_audit_2026_07_26.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
  ]
created: 2026-07-27
last_updated: 2026-07-27
priority: P2
parent_epic: infrastructure_master
source: >-
  Operator, mid-session while monitoring the sports FIXTURES backfill: "fix the memory accumulation issue seems like a
  leak from the backfill af fixtures."
assigned_vm: NA
execution_scope: local-only
estimate_class: research
drift_direction: advance-code
locked_by:
depends_on: []
---

# Per-VM shard growth causes long-running backfills to eventually OOM

## Root cause (confirmed via code read, not assumed)

`unified_trading_library/manifest_writer/_writer_io.py::ManifestWriter._flush_per_vm_pending`:

```python
existing_df = self._read_per_vm_shard(client)          # download + parse the ENTIRE existing shard
merged = self._merge_dataframes(existing_df, pending_new)
buf = io.BytesIO()
merged.to_parquet(buf, ...)                             # serialize the WHOLE (growing) shard
payload = buf.getvalue()
_upload_with_backoff_on_429(..., payload=payload, ...)  # upload the WHOLE (growing) shard
```

This happens on every flush (debounced to ~once per date for a typical backfill loop). The docstring is explicit about
WHY it re-reads-merges-uploads the whole object every time: a process-level lock (`_per_vm_shard_lock`) serializes
concurrent writer INSTANCES targeting the same shard path (the real scenario: MDPS's finalize path creates a fresh
`ManifestWriter` per concurrent unit, all writing to `_index/per_vm/{instance}.parquet`) — this is a hard-won
correctness fix (`test_concurrent_writers_same_shard_lose_no_entries`, `unified-trading-library`'s own test suite) for a
previously-real lost-entry bug. Bypassing it for a sequential-writer optimization risks reintroducing that exact bug.

The consequence: for a SINGLE long-running sequential writer (one process, one `ManifestWriter` instance, looping over
thousands of dates — e.g. any multi-year backfill), every flush's cost (network download + parquet decode + concat +
re-serialize + upload) grows with the CURRENT cumulative shard size, not with that date's own work. Measured on
`af-backfill-20260726-110610`: shard grew from ~36K rows (3.5hrs in) to ~159K rows (20.5hrs in) before the process was
`Killed` (exit 137). The per-fixture enrichment path was NOT involved (0 enrichment calls queued this run,
`--sports-entity FIXTURES` only) — this is a distinct root cause from the previously-fixed unfiltered
`read_availability_index(bucket)` OOM class.

## Fix applied (scoped to the one launcher that hit this)

`deployment-service/scripts/vm/launch-api-football-backfill-vm.sh`: an explicit start/end-date run (the case that can
span years) now sets `VM_TASK=instruments-backfill` instead of `VM_TASK=sports-backfill`, routing through the EXISTING
chunked branch in `scripts/vm/setup-data-pipeline-vm.sh` (already used by `launch-sports-instruments-reference-vm.sh` /
`launch-sports-full-sweep-vm.sh` / `launch-sports-is-gap-fill.sh` / `launch-sports-entity-sweep-vm.sh`) — splits the
range into `VM_CHUNK_DAYS=90`-day windows, each run as a fresh process. Memory resets between chunks (a fresh process's
per-VM shard read starts from whatever the PREVIOUS chunk's process already wrote — the read-merge-write cost is bounded
by chunk size, not total range). A rolling-window run (always a few days wide) and a `--recovery-fixture-ids` run (the
chunked branch doesn't plumb that flag) are deliberately excluded from the redirect — both stay on the original
dispatch, unaffected. Zero shared dispatcher/library code changed. Verified live: `af-backfill-20260727-011039` run.log
shows `task=instruments-backfill`, `Chunk 1/25: 2020-06-06 → 2020-09-03`.

## What's NOT fixed — genuinely open

- [ ] [DATA] P2. **Audit other launchers for the same latent risk.** Any launcher that (a) uses the generic single-shot
      `--operation ...` dispatch (not a dedicated chunked `elif` branch) AND (b) can be invoked with a genuinely
      multi-year date range carries the same OOM risk once its own per-VM shard grows large enough. Grep
      `deployment-service/scripts/vm/launch-*.sh` for launchers setting a `VM_TASK` with no dedicated branch in
      `setup-data-pipeline-vm.sh` (falls through to the generic dispatch), cross-referenced against whether that
      launcher is ever invoked with a wide date range in practice. **Done when**: every such launcher is either
      confirmed low-risk (always invoked with a bounded range) or redirected to a chunked task type the same way this
      one was.
- [ ] [CODE] P3. **Consider a proper library-level fix** (not attempted here — too risky to rush): cache the merged
      per-VM shard DataFrame + its GCS generation in the `ManifestWriter` instance across flushes, using a
      generation-check to detect whether another writer touched the object since this instance's last upload before
      trusting the cache (falls back to a full read on any mismatch — preserves the existing concurrent-writer
      correctness guarantee exactly). Would eliminate the redundant download+parse cost for the common
      single-sequential-writer case without a chunking workaround, but touches `unified-trading-library`'s
      concurrency-critical shared code (used fleet-wide, not just sports) — needs its own dedicated session with full
      test coverage of `test_manifest_writer_per_vm.py` / `test_manifest_writer_per_vm_debounce.py`, not a rushed
      mid-incident change.
