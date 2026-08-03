---
doc_type: issue
title:
  "`read_availability_index(bucket, columns=[...])` — the documented `columns=` memory-bounding path — itself OOMs on
  the live DeFi manifest at its current ~33.4M-row scale"
summary: >-
  While re-verifying the DeFi v2 expected-universe enumerator OOM fix
  (`defi_v2_expected_universe_enumerator_oom_2026_08_01.md`), re-ran the SAME bounded, column-projected
  `read_availability_index(bucket, columns=["data_type","capture_status"])` call that issue's own opening evidence used
  successfully — and it OOM'd directly on the shared planning-vm, RSS spiking from 1.67GB to 15.5GB in ~5 seconds
  (caught + killed by an ad-hoc RSS-monitor safety net before host impact; no outage). The `columns=` kwarg is the
  documented, codex-referenced memory-bounding mechanism for this exact scenario
  (`read_availability_index_bare_defi_callers_2026_07_27.md` frames BARE (unprojected) callers as the risk and implies
  projected callers are safe) — but it does not actually bound memory at DeFi's current scale (33,406,812 rows as of
  this session, up from the 29,956,737 that same prior audit's evidence cited on 2026-07-27/08-01). The pandas/pyarrow
  read path this helper uses appears to still materialise substantially more than the 2 requested columns' worth of data
  for a DeFi-scale index.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-trading-library]
scope: [engineer]
tags: [manifest, read-availability-index, oom, defi, memory-bounding, data-pipeline]
related:
  [
    /plans/active/issues/read_availability_index_bare_defi_callers_2026_07_27.md,
    /plans/active/issues/read_availability_index_slim_path_silent_empty_return_2026_07_27.md,
    /plans/archive/issues/defi_v2_expected_universe_enumerator_oom_2026_08_01.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-08-01
last_updated: 2026-08-01
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
assigned_role: data_engineering
drift_direction: advance-code
resolved_by:
locked_by:
source: >-
  data_engineering worker (slot-15, planning VM), 2026-08-01, task defi_v2_expected_universe_enumerator_oom-002
  (verifying the DeFi v2 expected-universe enumerator OOM fix) — hit while re-running the issue's own manifest census
  helper post-fix; not that task's own scope (worked around via a DuckDB streaming aggregate instead), filed here per
  the findings-closure rule.
depends_on: []
supersedes:
superseded_by:
context_scope:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /plans/active/issues/read_availability_index_bare_defi_callers_2026_07_27.md,
    /plans/archive/issues/defi_v2_expected_universe_enumerator_oom_2026_08_01.md,
    unified-trading-library/unified_trading_library/manifest_writer/_read_index.py,
    unified-trading-pm/scripts/dev/run-bounded-analysis.sh,
  ]
---

# `read_availability_index(columns=[...])` OOMs on the live DeFi manifest at current scale

## What I found

Ran, on the shared planning-vm, the exact call `defi_v2_expected_universe_enumerator_oom_2026_08_01.md`'s own opening
evidence used to build its before/after census:

```python
from unified_trading_library.manifest_writer._read_index import read_availability_index
df = read_availability_index("market-data-tick-defi-prd-central-element-323112", columns=["data_type", "capture_status"])
```

Backgrounded with an RSS-monitor safety loop (5-second poll, 7GB kill threshold — the memory-bounding HARD RULE per
`unified-trading-pm/agents/data_engineering.md` STEP 0.56 / `unified-trading-pm/agents/RULES.md` § 1). RSS trace:

| time  | RSS         |
| ----- | ----------- |
| T+0s  | 4.4 MB      |
| T+5s  | 275 MB      |
| T+10s | 421 MB      |
| T+15s | 746 MB      |
| T+20s | 1.67 GB     |
| T+25s | **15.5 GB** |

The kill threshold (7GB) tripped and the process was terminated before it could take down the shared host — but the
growth from 1.67GB to 15.5GB in a single 5-second poll interval shows this was already on an uncontrolled trajectory,
not a slow/bounded one. This is the SAME helper + SAME 2-column projection kwarg
`read_availability_index_bare_defi_callers_2026_07_27.md` frames as the safe path (that audit's scope was specifically
BARE, unprojected callers — it did not test whether the projected path itself holds at DeFi's current row count).

An earlier attempt via `scripts/dev/run-bounded-analysis.sh` (the sanctioned wrapper for ad-hoc scratchpad memory
bounding) failed differently — `pyarrow.lib.ArrowMemoryError: malloc of size 4423744 failed` under an 8G `ulimit -v`
(RLIMIT_AS) cap, even though the failing allocation was only ~4.2MB. This is a separate, secondary finding: RLIMIT_AS is
virtual-address-space accounting, not RSS — pyarrow/grpc reserve large virtual address ranges (arena allocators, mmap
pools) that count against `ulimit -v` even when not physically resident, so `run-bounded-analysis.sh`'s documented
RLIMIT_AS fallback (used whenever `systemd-run`/cgroups are unavailable, as on this host) is fundamentally incompatible
with pyarrow-heavy workloads — it will spuriously fail well below the intended cap. The wrapper's PRIMARY path
(systemd-run cgroup, RSS-based) would not have this problem; only the fallback does.

Worked around for the immediate need (the enumerator OOM issue's own Todo 2) by downloading the manifest once locally
(`gcloud storage cp`, a single 1.07GB file, not a corpus walk) and querying it via DuckDB's native columnar aggregate
engine instead of `read_availability_index` — DuckDB never materialises a 30M-row Python/pandas object, so a
`GROUP BY capture_status` / `GROUP BY data_type` census completed with `memory_limit='2GB'` and no incident. This
matches `run-bounded-analysis.sh`'s own documented "prefer DuckDB over pandas" precedent.

## Why it matters

`read_availability_index(bucket, columns=[...])` is the documented, codex-referenced fast-path for downstream services
to check manifest state without a GCS walk (`/codex/02-data/availability-manifest-and-data-status.md`), and its own
docstring specifically claims the `columns=` kwarg "reduc[es] peak in-process memory ... to the size of the requested
columns." `read_availability_index_bare_defi_callers_2026_07_27.md` already found ~35-40 call sites across 8 repos that
call this helper WITHOUT `columns=`/`filters=` against DeFi buckets and flagged them as OOM-risk — but that audit's own
premise (a projected call is safe) does not hold at DeFi's current scale. Any of those ~35-40 sites that get migrated to
add `columns=` per that audit's own recommended fix may STILL OOM on DeFi, silently defeating the fix. This is a
tooling/library-level gap, not specific to the expected-universe enumerator — any caller against a DeFi-scale manifest
inherits the same risk.

## Recommended decision

Root-cause why the `columns=` slim path (`_read_availability_index_slim` → `_read_parquet_columns_safe` →
`pd.read_parquet(io.BytesIO(data), columns=columns, ...)`) materialises far more than 2 columns' worth of memory for
DeFi's manifest — candidates: (a) the "augmented with the merge-required base cols" behaviour the function's own
docstring mentions may be pulling in more columns than expected at defi's row count, (b) `io.BytesIO(data)` holding the
full downloaded bytes AND the decoded table simultaneously (2x peak), (c) per-VM shard merge logic duplicating data. Fix
should keep peak memory bounded independent of asset_group scale — e.g. stream via
`pyarrow.parquet.ParquetFile.iter_batches` (the same pattern `instruments-service@66adbc1d` just applied in the
enumerator) rather than a single `pd.read_parquet` call, or push aggregation into DuckDB/pyarrow-native operations for
callers that only need counts/distinct-values rather than a full DataFrame.

## Todos

- [x] ✅ [DATA] P1. Root-cause `read_availability_index`'s `columns=` slim path
      (`unified_trading_library/manifest_writer/_read_index.py::_read_availability_index_slim` /
      `_read_parquet_columns_safe`) — confirm which step accounts for the 1.67GB→15.5GB spike at DeFi's ~33.4M-row scale
      (bare `pd.read_parquet` vs. base-col augmentation vs. per-VM shard merge) and fix it to stream/bound memory
      independent of asset_group row count, mirroring the `iter_batches`-based streaming pattern
      `instruments-service@66adbc1d` already applied for the same class of problem in `enumerate_expected_universe.py`.
      Re-verify against the live DeFi bucket with an RSS-monitored run (not a whole corpus walk — one real read). (repo:
      unified-trading-library) — unified-trading-library@65ae1e89
- [ ] [DATA] P2. Fix `scripts/dev/run-bounded-analysis.sh`'s RLIMIT_AS fallback path (used whenever `systemd-run` is
      unavailable) to not spuriously fail on pyarrow/grpc-heavy workloads — either document the incompatibility
      prominently (so agents route pyarrow-heavy ad-hoc scripts to a manual RSS-monitor pattern instead, as done in this
      session) or find an RSS-based (not RLIMIT_AS-based) fallback mechanism that doesn't require systemd (e.g. a
      background poll-and-kill loop on `/proc/<pid>/status` VmRSS, exactly what this session improvised). (repo:
      unified-trading-pm)

## Progress Log

- 2026-08-01 (slot-15, data_engineering): Filed while verifying
  `defi_v2_expected_universe_enumerator_oom_2026_08_01.md`'s Todo 2. Full evidence above (RSS trace, ArrowMemoryError
  traceback, DuckDB workaround that unblocked the parent task). Not fixed in this session — root-causing the UTL
  helper's own memory behaviour is out of scope for the enumerator OOM task; scoped as its own follow-up per the
  findings-closure rule.
- 2026-08-01 (slot-2, data_engineering): Independent corroboration from a DIFFERENT task
  (`cross_cutting_satellite_ao_dispatch_batch2-006`, the dp-audit daily digest OOM fix,
  `e2e-testing/scripts/audit/_dp_common.py` + `data_pipeline_daily_digest.py` — a separate, independently-implemented
  download+read helper, not this doc's `unified_trading_library.read_availability_index`). Same defi-scale row count
  (~33.4M) produced two further memory blowups beyond a simple `columns=` restriction: (a) `.astype(str).str.lower()` on
  the `capture_status` column speculatively allocated a stray 510MiB `complex128` array via pandas' `map_infer_mask` →
  `maybe_convert_objects` type-sniffing (fixed by switching to the pyarrow-backed `"string"` dtype, whose `.str.lower()`
  calls `pyarrow.compute.utf8_lower` directly); (b) a defensive `df.copy()` forced block consolidation via `np.vstack`,
  an extra ~1.24GiB single allocation (fixed by removing the unneeded copy). Also **independently reproduced the P2
  `run-bounded-analysis.sh` RLIMIT_AS finding**: an 8G `ulimit -v` cap spuriously MemoryError'd on this session's own
  column-restricted digest read too (before either of the two fixes above); raising the cap to 16-24G let the SAME code
  complete cleanly at a genuine peak RSS of ~11.8GiB (`VmHWM`-measured) — confirming this is a real, cap-independent
  virtual-vs-physical-memory accounting gap in the wrapper's fallback path, not specific to `read_availability_index`.
  After all three of this session's fixes, the digest completes a real 5-AG production run end-to-end; tracked as its
  own P3 follow-up (further reduction toward the ~4-8Gi aspirational target) at
  `/plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md`. Shipped: `e2e-testing@5d7f53a`,
  `e2e-testing@edd12c6`.
- 2026-08-01 (slot-15, data_engineering): Todo 1 root-caused + shipped — `unified-trading-library@65ae1e89`. **Root
  cause confirmed via code read**: `_read_availability_index_slim` unconditionally widens `columns=` to
  `_SLIM_MERGE_BASE_COLS | set(columns)` — 4 hard-required merge cols (date/venue/data_type/service_name) UNION
  `_OPTIONAL_DEDUP_COLS` (12 more, incl. high-cardinality `instrument_id`) UNION `_MERGE_TIEBREAK_COLS`
  (capture_status/attempted_at/written_at) = **19 columns total**, applied to the CONSOLIDATED-blob read regardless of
  whether a per-VM self-shard actually exists to merge. A caller's 2-column request (e.g.
  `["data_type","capture_status"]`) therefore silently decoded 19 columns across the FULL ~33.4M-row DeFi index — nearly
  a full-width read in all but name, explaining the 15.5GB spike (the `_read_parquet_columns_safe` docstring's own
  pre-existing note that an UNFILTERED read is ~14.86GiB on a comparable 27.4M-row DeFi index corroborates that even the
  widened-but-still-partial column set is the dominant cost, on top of the inherent full-corpus-no-filters decode cost
  `filters=` exists to solve). **Fix**: `_read_self_shard` is now called FIRST, with the caller's NARROW `columns`
  (cheap — self-shards are small, single-VM, short-lived writes), to learn whether a merge will actually happen BEFORE
  deciding how wide to read the consolidated blob — widening only applies when a self-shard genuinely exists (re-fetched
  once more, widened, negligible extra cost given shard size). The dedup-safety guarantee `_SLIM_MERGE_BASE_COLS` exists
  for (regression `api_football_enrichment_stale_ns_fixture_status_and_gate_ reader_inconsistency_2026_07_19`, covered
  by `test_slim_read_column_selection_does_not_change_dedup_result`) is UNCHANGED — that test exercises the SEPARATE
  `_read_slow_path` per-VM-shard-recovery branch (multiple shards, no consolidated blob), which this fix does not touch
  and which still always widens (correctly — any of N shards could carry a dedup-relevant column). Also corrected both
  this function's and the public `read_availability_index`'s own docstrings, which overstated `columns=`'s protective
  power without warning that a full-corpus UNFILTERED read on a large index remains several-to-tens-of-GB regardless —
  `filters=` is the mechanism that actually bounds memory there, and a genuinely streaming/DuckDB-style approach is
  recommended for full-corpus census/aggregate use cases (`filters=` can't bound those — no date window to prune to).
  Added 2 new regression tests (`test_slim_read_no_self_shard_uses_narrow_columns_for_consolidated_read`,
  `test_slim_read_with_self_shard_widens_consolidated_read_and_merges_correctly` — the latter also proves the merge
  still correctly reconciles a self-shard's fresher write against a stale consolidated row post-fix). Full
  `quality-gates.sh` green (6900+ pre-existing tests pass, no regressions; 87.17% coverage). Todo 2
  (`run-bounded-analysis.sh`'s RLIMIT_AS fallback) is now independently corroborated by slot-2's finding above but not
  attempted in this session — scoped as its own follow-up.

- **context-scout 2026-08-03**: populated context_scope (5 entries).
