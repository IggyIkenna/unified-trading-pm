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

**Root cause (partially pinned)**: `unified_trading_library/manifest_consolidator.py`'s `consolidate()` docstring states
it is "memory-bounded so the 16 GiB Cloud Run job survives a 75M+-row cefi manifest" — its DuckDB merge is sized and
capped for the DEDICATED Cloud Run consolidator's platform-enforced 16GB ceiling. `_is_lock_fresh()` (same file,
~line 1074) detects a stale lock (>300s TTL), clears it, and returns `False`, which lets `consolidate()`'s caller
proceed past the "skip cycle, lock is fresh" check into the full merge-per-VM-shards + DuckDB-dedup + write-back cycle
(steps 2-4 of its own docstring) — the expensive part. This is CORRECT behavior for a legitimate Cloud Run consolidator
cycle recovering from a crashed sibling. **What's not yet confirmed**: the exact call site in the
market-tick-data-service CLI's manifest-write path that led to `consolidate()` running at all — `_writer_io.py`'s
`_wait_for_consolidator_lock_clear()` and `_state.py`'s `assert_consolidator_healthy` (~line 397-400) are candidates
(both reference consolidator-lock-awareness), but I did not trace the exact call chain this session (time-boxed; this
finding's evidence is strong enough to act on without it, and pinning it precisely is separately tracked below).

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

- [ ] [INFRA] P1. Pin the exact call site in market-tick-data-service / unified-trading-library's manifest-write path
      that leads to `manifest_consolidator.consolidate()` running inline from a CLI capture (candidates:
      `manifest_writer/_writer_io.py::_wait_for_consolidator_lock_clear`, `manifest_writer/_state.py`'s
      `assert_consolidator_healthy` ~line 397-400). Confirm whether this is intentional resilience (client self-heals a
      dead consolidator) or an unintended fallthrough. (repo: unified-trading-library)
- [ ] [INFRA] P1. Once the call site is confirmed, either (a) gate inline `consolidate()` invocation from non-Cloud-Run
      contexts behind an explicit memory cap (e.g. `CONSOLIDATOR_DUCKDB_MEMORY_LIMIT` env, or route through
      `scripts/dev/run-bounded-analysis.sh`'s mem-cap wrapper per `/codex/05-infrastructure/vm-launcher-runbook.md` §
      heavy-compute-on-shared-host), or (b) have the CLI-side caller skip inline consolidation entirely on a stale lock
      and instead defer/retry (the dedicated Cloud Run cron will eventually pick it up) — whichever preserves
      correctness without the unbounded-memory risk. (repo: unified-trading-library)
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
