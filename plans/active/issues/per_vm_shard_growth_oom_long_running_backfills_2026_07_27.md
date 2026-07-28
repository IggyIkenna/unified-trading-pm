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
  **First fix attempt (2026-07-27, routing through chunked `instruments-backfill`) was INSUFFICIENT** — confirmed live
  on the relaunch `af-backfill-20260727-064958`: 14 of 25 chunks still got OOM-killed (chunks 12-25), each time silently
  advancing past the killed chunk's remainder because the loop's bare `|| true` swallowed the failure, leaving ~832 days
  of FIXTURES coverage (2023-05-13 → 2026-07-25, mostly chunks 13-25) never actually processed despite the VM
  self-reporting `exit_code=0`. Root cause of the insufficiency: `VM_NAME` (and therefore `ManifestWriter`'s per-VM
  shard path `_index/per_vm/{VM_NAME}.parquet`) is set ONCE at VM boot and stays constant for the VM's entire lifetime —
  a fresh python process per 90-day chunk resets that PROCESS's own memory, but every chunk still reads, merges, and
  re-uploads the SAME ever-growing shared shard object (confirmed via the run.log's `total entries` climbing
  161K→175K→…→281K straight through every chunk restart), so the OOM threshold (~155-165K accumulated rows) was hit
  again and again as soon as the cumulative shard crossed it, regardless of chunking. **Real fix (2026-07-27,
  `deployment-service@20ce4c9`)**: scope `VM_NAME` to a per-chunk suffix (`${VM_NAME}-c${CHUNK_NUM}`) for just the
  python subprocess invocation — bounds each chunk's per-VM shard to that chunk's own ~90 days of rows instead of the
  cumulative multi-year total (the manifest consolidator merges every `_index/per_vm/*.parquet` shard generically
  regardless of naming, and prunes on mtime/generation, never VM-liveness name-matching, so this is safe); the outer
  tee-wrapper/heartbeat's own `VM_NAME` — used for `vm-logs/{vm}/PROGRESS.json` and liveness reporting — is untouched.
  Also added a bounded (4-attempt) per-chunk retry so a killed chunk resumes via skip-if-fresh instead of the loop
  silently moving on. Zero shared `unified-trading-library` code touched — this is entirely a launcher-script fix.
  **VERIFIED RESOLVED 2026-07-28**: relaunch `af-backfill-20260728-091755` completed all 25/25 chunks cleanly on the
  first attempt (target end date `2026-07-25` reached) — a full-log audit (115,631 lines) confirms zero `Killed`, zero
  `CHUNK_EXHAUSTED`, zero `CHUNK_RETRY`, zero `Traceback`; chunk 14 (one of the 14 that died in the take-2-insufficient
  run) completed its full range this time. The core incident is closed; the two audit/generalization todos below remain
  open as separate, non-blocking follow-on work.
status: resolved
resolved_by: deployment-service@20ce4c9e0524 (verified live af-backfill-20260728-091755, 2026-07-28)
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [deployment-service, unified-trading-library, instruments-service]
scope: [engineer]
tags: [oom, memory-leak, manifest-writer, per-vm-shard, backfill, vm-launcher, recurring-bug-class]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/archive/issues/read_availability_index_unfiltered_callsite_audit_2026_07_26.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
  ]
created: 2026-07-27
last_updated: 2026-07-28
priority: P2
parent_epic: infrastructure_master
source: >-
  Operator, mid-session while monitoring the sports FIXTURES backfill: "fix the memory accumulation issue seems like a
  leak from the backfill af fixtures."
assigned_vm: planning
execution_scope: orchestrator-agent
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

## Fix history

**Attempt 1 (2026-07-27, INSUFFICIENT)**: `deployment-service/scripts/vm/launch-api-football-backfill-vm.sh` — an
explicit start/end-date run now sets `VM_TASK=instruments-backfill` instead of `VM_TASK=sports-backfill`, routing
through the EXISTING chunked branch in `scripts/vm/setup-data-pipeline-vm.sh` (90-day windows, fresh process per chunk).
This reset each chunk's OWN process memory but NOT the shared per-VM manifest shard (see summary) — verified
insufficient live: the relaunch `af-backfill-20260727-064958` still OOM-killed 14/25 chunks.

**Attempt 2 (2026-07-27→28, the real fix)**: `deployment-service@20ce4c9` — `setup-data-pipeline-vm.sh`'s
`instruments_chunk_loop.sh` template now (a) suffixes `VM_NAME` per chunk (`${VM_NAME}-c${CHUNK_NUM}`) scoped to just
the `python -m instruments_service` subprocess, bounding the per-VM shard to one chunk's rows instead of the whole
backfill's cumulative total, and (b) retries a killed chunk up to 4 times (skip-if-fresh resumes past whatever that
chunk already captured) before logging `CHUNK_EXHAUSTED` and moving on — so a genuinely irrecoverable chunk is now LOUD
instead of silently absorbed by `|| true`. Verified via a standalone fake-subprocess harness (transient-failure
retry-then-succeed, and permanent-failure bounded-exhaustion, both behave correctly) plus `quality-gates.sh` green. Zero
shared `unified-trading-library` code touched.

**Gap remediation**: the ~832 missing days from Attempt 1's insufficiency (2023-05-13 → 2026-07-25, mostly chunks 13-25)
are being refilled by relaunching the SAME launcher command with the fixed script — skip-if-fresh fast-forwards through
everything already captured and does real work only on the gap.

## What's NOT fixed — genuinely open

- [ ] [DATA] P2. **Audit other launchers for the same latent risk — INCLUDING already-chunked ones.** The original
      framing (single-shot dispatch only) was incomplete: Attempt 1 above proves a launcher that's ALREADY routed
      through a chunked `setup-data-pipeline-vm.sh` branch (e.g. `cefi-hl-aster-backfill`, or any other `elif` branch
      reusing one `VM_NAME` across many chunk-loop iterations over a long enough total range) carries the SAME latent
      risk unless it also scopes `VM_NAME` per chunk. Audit every chunked branch in `setup-data-pipeline-vm.sh` (not
      just single-shot `--operation ...` dispatches) for reused-VM_NAME-across-chunks exposure, cross-referenced against
      whether that launcher is ever invoked with a range wide enough to grow the shard past the ~155-165K-row OOM
      threshold in practice. **Done when**: every such launcher is either confirmed low-risk (bounded cumulative-shard
      growth for its realistic invocation range) or given the same per-chunk `VM_NAME` suffix.
- [ ] [CODE] P3. **Library-level fix for the `ManifestWriter` per-VM-shard flush cost — NO LONGER BLOCKING, still worth
      doing eventually.** Re-evaluated 2026-07-28: caching the merged DataFrame + GCS-generation-check (the originally
      proposed fix) would reduce REDUNDANT download+parse work across flushes, but would NOT reduce PEAK memory at the
      moment of `merged.to_parquet()` — that allocation is proportional to the CURRENT shard size regardless of whether
      `existing_df` came from a fresh download or a cache, so it would not actually have fixed this incident. The
      per-chunk `VM_NAME` suffix (this doc's real fix) addresses the acute case (any launcher that chunks into fresh
      processes) by capping shard size directly. This item remains open only for the residual case of a genuinely
      long-running SINGLE process with a constant `VM_NAME` that never restarts (e.g. a live/forward VM) — lower
      urgency, no longer incident-driving. If picked up: cache the merged per-VM shard DataFrame + its GCS generation in
      the `ManifestWriter` instance across flushes, generation-checked before trusting the cache (falls back to a full
      read on any mismatch — must preserve the existing concurrent-writer correctness guarantee exactly, same invariant
      `test_concurrent_writers_same_shard_lose_no_entries` already covers). **Done when**: (a) both existing suites stay
      green (`test_manifest_writer_per_vm.py`, `test_manifest_writer_per_vm_debounce.py`), AND (b) a NEW adversarial
      test proves the generation-check detects a concurrent mutation and falls back to a full read-merge (not just that
      the happy-path cache hit works). `quality-gates.sh` green on `unified-trading-library`.
