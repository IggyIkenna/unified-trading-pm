---
doc_type: issue
title:
  "A routine CLI capture (market-tick-data-service collect-lending-indices) triggered manifest_consolidator's full
  DuckDB merge inline, ballooning to 44GB+ RSS on a shared host with no memory cap"
summary: >-
  While completing defi_plasma_chain_onboarding_gap_2026_07_26.md's manifest-write leg (a routine single-day,
  single-venue AAVE-PLASMA capture), the CLI process's `RESOURCE_SAMPLE` log lines showed RSS growing from a 639MiB
  baseline to 44.4GB (68.6% of a 61GB host) within ~90 seconds at 100%+ CPU, immediately preceded by
  `ManifestConsolidator: clearing stale lock for market-data-tick-defi-prd-central-element-323112 (age=327.8s >
  TTL=300.0s)`. Host swap usage climbed from ~16GB to 24GB+ used and available memory dropped to ~3.2GB before the
  process was killed (SIGTERM then SIGKILL, mine, exact PID, per the runaway-process-endangering-the-host rule). Root
  cause: `unified_trading_library.manifest_consolidator.consolidate()`'s own docstring states it is "memory-bounded so
  the 16 GiB Cloud Run job survives a 75M+-row cefi manifest" — it is designed and bounded for the DEDICATED Cloud Run
  consolidator service's platform-enforced memory ceiling, not for inline invocation from an arbitrary CLI process on a
  shared VM with no equivalent cap. Something in the manifest-write path (exact call site not pinned this session — see
  Recommended next steps) decided to run a full stale-lock-triggered consolidation cycle synchronously inside the
  capture CLI instead of deferring to the dedicated service, per this repo's own domain rule ("Manifest consolidator =
  Cloud Run / Batch-Fargate, NOT a VM"). The 18 real AAVE-PLASMA rows this capture produced were already durably written
  to GCS before this occurred (data is safe); the manifest registration for that write did NOT complete (confirmed: 0
  rows for venue=AAVE_V3/chain=PLASMA in the current availability index, cross-validated against AAVE_V3/ETHEREUM's
  70,069 existing rows using the identical query).
status: open
nature: issue
asset_group: [infrastructure]
stage: [data]
repos: [unified-trading-library, market-tick-data-service]
scope: [engineer, admin]
tags: [infrastructure, manifest-consolidator, oom, duckdb, shared-host, memory-safety, cli]
related:
  [
    /plans/active/issues/defi_plasma_chain_onboarding_gap_2026_07_26.md,
    /plans/archive/issues/sports_manifest_consolidator_duckdb_crash_and_silent_empty_read_2026_07_12.md,
    /plans/archive/issues/instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: 2026-07-31
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.4
assigned_role: infra
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Surfaced while completing defi_plasma_chain_onboarding_gap_2026_07_26.md's manifest-write leg (slot 15, 2026-07-31) —
  the capture itself worked (RPC-fallback fix confirmed via 18 real rows written to GCS), but the manifest registration
  step triggered this unrelated, more severe host-safety issue.
drift_direction: advance-code
---

# CLI-triggered inline manifest consolidation has no memory cap, unlike the dedicated Cloud Run job

## What I found

Running a routine `market-tick-data-service --operation collect-lending-indices` capture (single day, single chain,
expected ~18 rows) for `AAVE-PLASMA`/`PLASMA`/2026-07-30, the process wrote its data successfully
(`Wrote 18 rows across 18 instrument shard(s) to gs://market-data-tick-defi-prd-central-element-323112` at `21:15:54Z`),
then went quiet except for periodic `RESOURCE_SAMPLE` heartbeats — until, at `21:19:12Z`, it logged
`ManifestConsolidator: clearing stale lock for market-data-tick-defi-prd-central-element-323112 (age=327.8s > TTL=300.0s)`.
Immediately after, `RESOURCE_SAMPLE` lines show:

| time     | cpu    | rss    | swap used |
| -------- | ------ | ------ | --------- |
| 21:16:59 | 0.0%   | 639MiB | 16.6GB    |
| 21:17:59 | 451.9% | 14.5GB | 16.4GB    |
| 21:18:31 | 99.6%  | 33.3GB | 16.6GB    |
| 21:19:05 | 100.3% | 36.3GB | 17.0GB    |

`ps` moments later showed **44.4GB RSS (68.6% of a 61GB host)**, and `free -h` showed only 3.2GB free / 10GB available
with swap climbing to 24GB+ used — a real, ongoing risk to every other process on this shared host (several other slots
had concurrent `quality-gates.sh` runs in flight at the time). I killed the process (SIGTERM, then SIGKILL after it
didn't respond — my own process, exact PID, per the runaway-process-endangering-the-host rule); host memory recovered
fully within seconds both times.

**Root cause (CONFIRMED 2026-07-31, slot 4 — corrects the original hypothesis below)**: it is NOT
`manifest_consolidator.consolidate()` running inline. `consolidate()` (and its DuckDB merge) has exactly ONE production
call site in the whole workspace: its own CLI `__main__` entrypoint
(`unified_trading_library/manifest_consolidator.py:3344`, the dedicated Cloud Run job). Every other reference is a
docstring/comment or a one-off `--force` remediation script run by a human. Nothing in the market-tick-data-service
write path imports or calls `consolidate()`.

The "clearing stale lock" log line IS real and DOES fire from inside this CLI process, but it comes from
`_is_lock_fresh()` (`manifest_consolidator.py:1074`) being called directly — not via `consolidate()`, but via
`ManifestWriterIoMixin._wait_for_consolidator_lock_clear()`
(`unified_trading_library/manifest_writer/_writer_io.py:982`, deferred-imports `_is_lock_fresh` at line 998-999
specifically to dodge the circular import with `manifest_consolidator`). `_is_lock_fresh()` itself is cheap (one
lock-blob read + best-effort delete, `manifest_consolidator.py:1074-1127`) — it does NOT run DuckDB and cannot explain
44GB RSS on its own. The actual unbounded operation is what `_wait_for_consolidator_lock_clear()` falls through into
once its bounded poll ends (never blocks indefinitely, per its own docstring):

**The real chain** — `ManifestWriterIoMixin._write_to_gcs()` (`_writer_io.py:600`) branches on `self._per_vm_enabled`.
That flag resolves via `_resolve_per_vm_shards()` (`unified_trading_library/manifest_writer/_state.py:204-224`):
explicit arg → `UnifiedCloudConfig.manifest_per_vm_shards` (env `MANIFEST_PER_VM_SHARDS`) → **`False` (legacy CAS path)
as the default**. Per this repo's own VM-launcher convention (`per-VM shards VM_NAME=<tag>` +
`MANIFEST_PER_VM_SHARDS=true` — CLAUDE.md § "Launching VMs / infra"), that env var is set by fleet/backfill launchers,
NOT by an ad-hoc interactive CLI capture like this one — so this session's `DefiManifestRecorder`'s `ManifestWriter`
(constructed with no explicit `per_vm_shards=` arg,
`market-tick-data-service/market_tick_data_service/cli/handlers/_defi_manifest.py:131-135`) defaulted to
`_per_vm_enabled=False`. `_write_to_gcs()`'s own docstring names this exact path: **"Legacy mode (default): single
canonical `_index/availability_index.parquet` blob updated via GCS generation-match CAS with retry. Sound when there's
at most one writer per bucket; melts under fleet load."** (`_writer_io.py:619-623`). That routes to
`_write_with_generation_match()` (`_writer_io.py:924`) → `_wait_for_consolidator_lock_clear()` (explains the log line) →
falls through to `_try_conditional_write()` (`_writer_io.py:897`) → `_read_with_generation()` (`_writer_io.py:1010`, a
full unbounded `pd.read_parquet()` of the ENTIRE canonical `_index/availability_index.parquet` blob — every venue, every
asset_group sharing that bucket's manifest, not scoped to this capture's single day/venue) → `_merge_dataframes()`
(`_writer_io.py:1228-1299`, an unbounded `pd.concat([existing_df, new_df])` + multi-column `.drop_duplicates()` across
every row of that full frame). This is plain pandas with NO memory cap of any kind (unlike `consolidate()`'s DuckDB
path, which at least targets the Cloud Run job's 16GB ceiling) — a perfect match for the observed CPU-heavy (451.9%,
string-column dedup) RSS ramp (639MiB→44.4GB in ~90s). **Ruled out as candidates**: `_state.py`'s
`assert_consolidator_healthy` (~line 368-403) is called ONLY from the READ preflight path (`_read_index.py:173`, "that
preflight now wraps assert_consolidator_healthy"), never from any write path — confirmed via a full-repo grep of every
call site (`grep -rn assert_consolidator_healthy unified_trading_library/`), so it cannot be involved in a
manifest-WRITE capture's OOM.

**Confirmed safe**: the 18 real capture rows this session's RPC-fallback fix produced (see the parent doc,
`market-tick-data-service@9d6fc8cc` and 2 prior commits, already shipped + QG-green) were durably written to GCS BEFORE
this occurred — no data loss. **Confirmed NOT complete**: the manifest registration for that write. Verified via a
targeted, column-projected, filtered read of `_index/availability_index.parquet` (NOT a bucket-wide walk — downloaded
the single index blob, then used `pyarrow.parquet.read_table(..., filters=[...])`, never a full-table `astype(str)`
scan, which I also mistakenly tried once and had to kill for the same memory reason — see lesson below):
`venue='AAVE_V3', chain='PLASMA'` → 0 rows, vs. `venue='AAVE_V3', chain='ETHEREUM'` → 70,069 rows spanning 2022-12-30 to
2026-07-30 (proves the query method itself is correct; PLASMA is genuinely unregistered, not a query bug). The
manifest's `venue` column is the bare protocol name (`AAVE_V3`), NOT the chain-suffixed UAC venue constant
(`AAVE-PLASMA`) — a second, separate naming-convention trap worth flagging for whoever writes the next manifest query
against this bucket.

## Why it matters

This is NOT specific to Plasma or to my capture — ANY defi (or other-asset-group) capture CLI invocation that happens to
run while the dedicated Cloud Run consolidator's lock has gone stale (crashed cycle, restart, deploy, or simply a long
legitimate cycle exceeding the 300s TTL) could trigger the identical inline full-corpus consolidation, unbounded, on
whatever host is running that CLI — a shared planning/orchestrator VM with many concurrent slots, not a single-tenant
Cloud Run container. The prior related incident
(`sports_manifest_consolidator_duckdb_crash_and_silent_empty_read_2026_07_12.md`) documents the DEDICATED Cloud Run job
itself OOM-crashing on this same `_duckdb_consolidate_and_write` path — this finding shows the SAME heavy function is
also reachable, unprotected, from client CLI processes, which is a materially larger blast radius (a shared host running
many agents' work, not an isolated container).

## Recommended next steps

- [x] [INFRA] P1. ✅ Pin the exact call site in market-tick-data-service / unified-trading-library's manifest-write path
      that leads to the unbounded inline merge from a CLI capture — unified-trading-library@(this commit), 2026-07-31.
      **Not `manifest_consolidator.consolidate()`** (it has exactly one production call site, its own Cloud Run
      `__main__`, confirmed via full-repo grep). The real chain: `ManifestWriterIoMixin._write_to_gcs()` defaults to
      `_per_vm_enabled=False` (legacy CAS mode — `MANIFEST_PER_VM_SHARDS` unset for this ad-hoc interactive capture,
      `manifest_writer/_state.py:204-224`) → `_write_with_generation_match()` (`_writer_io.py:924`) →
      `_wait_for_consolidator_lock_clear()` (explains the "clearing stale lock" log via `_is_lock_fresh`) → falls
      through to `_try_conditional_write()` → `_read_with_generation()` (`_writer_io.py:1010`, unbounded full-index
      `pd.read_parquet()`) → `_merge_dataframes()` (`_writer_io.py:1228`, unbounded `pd.concat`+`.drop_duplicates()`
      across the ENTIRE canonical index). `_write_to_gcs()`'s own docstring already names this "Legacy mode (default)
      ... melts under fleet load." This IS an unintended fallthrough for a shared-host ad-hoc CLI invocation (not
      resilience) — a routine single-day/single-venue capture should never default to a full-bucket-manifest
      read-merge-write. `assert_consolidator_healthy` ruled out (read-preflight-only, no write-path caller). See "Root
      cause (CONFIRMED 2026-07-31)" above for the full evidence chain. (repo: unified-trading-library)
- [x] [INFRA] P1. ✅ Now that the call site is `_write_with_generation_match`'s legacy-CAS full-index read-merge-write
      (NOT `manifest_consolidator.consolidate()` — retitled from the original DuckDB-focused framing), fix the
      unbounded-memory risk: either (a) make `DefiManifestRecorder` (and any other CLI-facing `ManifestWriter`
      construction site) default to per-VM shard mode (`per_vm_shards=True`) for ad-hoc/interactive captures instead of
      silently falling back to the fleet-only legacy CAS path, or (b) bound `_read_with_generation` /
      `_merge_dataframes` (row/byte budget, mirroring the existing `_resolve_per_vm_merge_max_bytes()` guard already
      used by the READ side's `_read_slow_path`) so a legacy-mode write on a large bucket can't runaway even when per-VM
      mode isn't enabled — whichever preserves correctness without the unbounded-memory risk. (repo:
      unified-trading-library) — **unified-trading-library@74fdeeca6ee58957d7d15591d566fef353fdcc76, 2026-07-31.**
      Implemented as a variant of (b) that REFUSES rather than truncates: this single canonical blob is fully
      overwritten on every write, so silently reading only part of it (as the per-VM merge budget safely does for its
      many-shards case) would drop untouched rows from the rewritten index — a truncated read is not a safe bound here.
      New `ManifestWriterIoMixin._refuse_if_legacy_read_oversized()` cheap-checks the existing canonical blob's
      compressed size via a metadata-only `blob.reload()` (no download) BEFORE `_try_conditional_write` /
      `_read_with_generation` would otherwise download + `pd.read_parquet` the whole blob; oversized (default >200 MiB,
      mirroring `_resolve_per_vm_merge_max_bytes`'s existing budget) raises the new `ManifestLegacyWriteRefusedError`
      instead of proceeding. Escape hatches: `MANIFEST_LEGACY_READ_MAX_BYTES=0` (env opt-out) or
      `ManifestWriter(allow_oversized_legacy_write=True)` (per-writer force flag) for a deliberate one-off correction
      script. 6 new unit tests (`tests/unit/test_manifest_writer_legacy_read_size_guard.py`) cover: refusal before any
      read, normal write within budget, the force flag, the env opt-out, the fresh-index no-op case, and the unset-env
      default budget. `quality-gates.sh` green (182s, sentinel=74fdeeca).
- [ ] [DATA] P2. Once (a)/(b) ships, re-run the AAVE-PLASMA manifest registration for `2026-07-30` (the GCS data already
      exists — this is a re-register, not a re-capture) and confirm rows land via the same targeted `pyarrow`
      filtered-read method documented above (never a bucket-wide walk or whole-table `astype(str)` scan). Then flip
      `defi_venues.py`'s `AAVE-PLASMA` phase from `pipeline` to `live` and close
      `defi_plasma_chain_onboarding_gap_2026_07_26.md`'s P3 todo. (repo: market-tick-data-service,
      unified-api-contracts, unified-trading-pm)

## Lesson for whoever picks this up

**Don't retry the exact same capture command a third time expecting a different outcome** — the stale-lock condition
that triggered this is a property of the BUCKET's consolidator state, not this specific capture's inputs; a blind retry
could hit the identical unbounded-memory path again. **Also**: when inspecting a large manifest parquet in-session,
NEVER `df.astype(str).apply(...)` across all columns to search for a value (I made this exact mistake once myself,
mid-investigation, on a 29.5M-row/40-column index — killed it at ~41GB RSS) — use
`pyarrow.parquet.read_table(path, columns=[...], filters=[...])` for a column-projected, predicate-pushed read instead,
and verify the query method against a KNOWN-present value before trusting a zero-result on the value you're actually
checking.
