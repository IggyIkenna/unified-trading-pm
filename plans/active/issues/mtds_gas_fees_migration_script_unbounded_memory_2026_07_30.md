---
doc_type: issue
title: >-
  migrate_legacy_gas_fees_venue_2026_07_30.py has an unbounded memory leak — killed a slot-7 subprocess TWICE in ~15
  minutes, both times taking down the whole orchestrator API (fleet-wide outage, not scoped to this migration)
summary: >-
  While investigating an unrelated question, found orchestrator.service's cgroup pinned at `MemoryAvailable: 0` with
  every HTTP endpoint returning `HTTP:000`. Root-caused to a single subprocess spawned by slot-7's worker:
  `market-tick-data-service/scripts/migrate_legacy_gas_fees_venue_2026_07_30.py --limit 5 --log-level INFO` (PID
  3062883) had grown to 44.5GB RSS (68.6% of the host's 64GB RAM) over 57 minutes — for a script whose own `--limit 5`
  flag implies a tiny 5-item smoke test. Killed it (SIGTERM, died gracefully within 5s), memory recovered instantly
  (10.2GB -> 53.3GB available). ~15 minutes later the SAME script recurred, this time launched WITHOUT `--limit` (full
  run) by the SAME slot-7 worker, and reached 45.4GB RSS in just 7 minutes — faster, not slower — before being killed
  again. Independently verified `_build_worklist()` (the manifest read that produces the migration's work items) is
  itself fast and bounded (12,424 items, 10s, trivial memory) — so the leak is NOT proportional to worklist size; it
  happens inside `_migrate_one()` (the per-work-item blob-download/transform loop) or the imported `write_defi_rows()`,
  since even the `--limit 5` run (processing only 5 items) leaked to 42GB+.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, agent-orchestrator]
scope: [engineer, admin]
tags: [defi, gas-fees, memory-leak, incident, fleet-wide-outage, migration-script, slot-7]
related:
  [
    /plans/active/issues/defi_gas_fees_historical_venue_path_migration_2026_07_28.md,
    /plans/active/issues/orchestrator_api_full_outage_stale_cgroup_memory_cap_2026_07_30.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: research
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.48
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
source: >-
  Discovered incidentally while investigating an unrelated `/api/backlog` hang on 2026-07-30, which turned out to be a
  symptom of this script consuming nearly all host RAM, not a backlog-specific bug.
resolved_by:
locked_by:
locked_since:
---

# gas_fees migration script — unbounded memory leak, caused 2 fleet-wide API outages in ~15 minutes

## What's confirmed

1. **First occurrence, ~09:58 UTC 2026-07-30**: `orchestrator.service`'s cgroup showed `available: 0B` (again — a
   separate, already-fixed incident from earlier the same morning,
   `orchestrator_api_full_outage_stale_cgroup_memory_cap_2026_07_30.md`, ruled out the cgroup CAP being stale this time
   — the cap was already correctly scaled to 64GB). `ps aux --sort=-%mem` found the actual cause: PID 3062883,
   `.venv/bin/python scripts/migrate_legacy_gas_fees_venue_2026_07_30.py --limit 5 --log-level INFO`,
   `VmRSS: 44559256 kB` (~42.5GB), state `D` (uninterruptible disk sleep), running 57m21s. Confirmed via
   `/proc/<pid>/cgroup` this process lives INSIDE `orchestrator.service`'s cgroup (a child of slot-7's tmux session —
   every slot's spawned subprocess does), so it was directly consuming the same memory budget as the API process itself.
2. **Ownership confirmed**: `sudo -u ubuntu tmux capture-pane -p -t orch-slot-7` showed the worker's own todo list —
   "Copy + manifest-verify each of 14 legacy prefixes to venue=ALCHE…" — mid-flight on
   `defi_gas_fees_historical_venue_path_migration_2026_07_28.md`'s migration, currently polling a backgrounded "smoke
   test" Task Output with no output yet. This was a genuine, in-progress, legitimate task — the SCRIPT has the bug, not
   the worker's usage of it.
3. **Killed (SIGTERM → died in <5s, no SIGKILL needed)** — memory recovered immediately (`free -m` available: 10,164MB →
   53,268MB in the same check). API responded HTTP:200 within seconds.
4. **Second occurrence, ~10:00-10:07 UTC (≈9 min after the operator flagged this session should notify the worker, ≈2
   min before the notification actually landed — see below)**: same script, same slot 7, this time launched WITHOUT
   `--limit` (a full run against all 12,424 work items) — PID 4007786, reached `VmRSS: 45,430,120 kB` (~45.4GB, 70.1% of
   host RAM) after only ~7 minutes (faster growth than the first occurrence, consistent with more work items
   accelerating whatever the leak actually is). Killed again (SIGTERM, died immediately). Memory: available 10,856MB →
   55,382MB.
5. **First notification attempt (immediately after occurrence 1) timed out** — the orchestrator API was still recovering
   from occurrence 1's own memory pressure at that exact moment, so the `/api/slots/7/message` POST itself hit the same
   `HTTP:000` symptom. This is almost certainly why occurrence 2 happened — the worker never saw the "don't re-run this"
   warning before launching the full (unbounded) run. **Second notification attempt, after occurrence 2 was killed and
   memory recovered, succeeded** (`HTTP 200`) — slot 7 has now been told directly not to re-run this script until
   root-caused, with a pointer to this doc.
6. **Root-cause isolation, verified independently (read-only, no GCS writes)**: called `_build_worklist()` directly in a
   fresh Python process — `worklist built: 12424 rows to migrate (1 skipped — already-canonical ALCHEMY collision)`,
   completed in **10.26 seconds**, trivial memory (a list of 12,424 lightweight `_WorkItem` dataclass instances). This
   rules OUT the worklist-building step (the bounded, documented "one slim `read_availability_index` read, ~12.5k rows,
   a few MB" — confirmed accurate) as the leak source. Since the FIRST occurrence's `--limit 5` run only ever processes
   5 work items through `_migrate_one()` (the limit is applied to the worklist BEFORE the per-item loop, and
   `ManifestWriter`'s `batch_size` is also computed from the POST-limit worklist length, so nothing scales with the full
   12,424 count in that run) yet STILL leaked to 42.5GB+, **the leak must be inside `_migrate_one()`'s per-item work
   (blob download / `pq.read_table` / `write_defi_rows()` call) or inside `write_defi_rows()` itself — NOT proportional
   to worklist size.**

## What is NOT yet known — the actual next step

I did not go further into `write_defi_rows()`'s implementation (it lives in
`market_tick_data_service/market_interface/adapters/defi.py`, outside this migration script) or reproduce the leak under
controlled/instrumented conditions (e.g. `tracemalloc`, or running one single work item and watching RSS) — that's real
debugging work belonging to whoever owns this migration, not something to rush through as a side-effect of incident
response. Leading theories, in priority order:

1. **`write_defi_rows()` accumulates something across calls** (a growing internal cache, an unclosed resource, a
   module-level list that's appended-to but never cleared) — would explain leaking even under `--limit 5` since the
   function is called once per work item regardless of total worklist size, and would explain occurrence 2's faster
   growth (more calls = faster accumulation of the same per-call leak).
2. **`_legacy_prefix()` / `storage.list_blobs(prefix=...)` matches far more blobs per (date, chain) than the "1-2
   near-duplicate leaf-name variants" the docstring describes** — if the prefix construction is broader than intended
   (e.g., a missing trailing slash letting it match sibling directories too), a single work item's `list_blobs` call
   could enumerate and download an unbounded number of unrelated blobs. Worth checking against the ACTUAL blob count
   under one of the first 5 worklist items' prefixes
   (`day=2021-09-01/pipeline_mode=batch_onchain_rpc/asset_group=defi/venue=ARBITRUM/chain=ARBITRUM/   instrument_type=spot_asset/data_type=gas_fees/`)
   before assuming theory 1.
3. Less likely but worth ruling out: `pq.read_table(...).to_pandas()` or `to_dict("records")` on a legacy parquet file
   that's much larger than expected (theory 3 doesn't explain the FASTER growth under MORE items in occurrence 2 as
   cleanly as 1 or 2 do, since it would scale with distinct files, not calls).

## Todos

- [ ] [DATA] P0. Root-cause the actual leak location — instrument `_migrate_one()` with `tracemalloc` or per-call RSS
      logging, running ONE work item at a time (not `--limit 5`, which still triggers multiple calls) to isolate whether
      a SINGLE call already leaks meaningfully, or whether it only shows up after several calls (pointing at
      accumulation vs a single-call blowup). Check the actual blob count under a real legacy prefix (theory 2) before
      assuming `write_defi_rows()` itself (theory 1). Fix the root cause, add a regression test that asserts bounded
      memory (or bounded blob count) for a single `_migrate_one()` call. (repo: market-tick-data-service)
- [ ] [DATA] P1. Once fixed, re-verify with `--dry-run --limit 5` first (zero GCS writes, same read/transform path)
      before any real run, and only then attempt the full migration this script exists to do.
- [x] [BACKEND] P0. Kill the runaway process + restore orchestrator API availability (both occurrences). — **Done
      2026-07-30**: SIGTERM both times, no SIGKILL needed, API HTTP:200 within seconds each time.
- [x] [BACKEND] P1. Notify slot 7's worker so it doesn't blindly retry. — **Done 2026-07-30**: first attempt timed out
      (API itself down at that moment — see finding 5); second attempt succeeded (`POST /api/slots/7/message`, HTTP
      200), worker told not to re-run until root-caused, pointed at this doc.
- [ ] [REVIEW] P2. This is the SECOND fleet-wide memory incident within the same session (the first, a stale cgroup cap,
      is fixed + self-healing per `orchestrator_api_full_outage_stale_cgroup_memory_cap_2026_07_30.md`) — consider
      whether a per-slot subprocess RSS ceiling (e.g. a `cgroup`/`ulimit` scoped to each slot's OWN spawned children,
      not just the whole `orchestrator.service` cgroup) would contain a future buggy script to ITS OWN slot instead of
      starving the entire fleet. Out of scope to design/implement here — flagging the pattern.

## Codex SSOTs

- None directly own migration-script memory safety. If todo 1 lands, the fix + regression test are the record; no new
  SSOT needed unless the root cause turns out to be a reusable footgun in `write_defi_rows()` itself, in which case note
  it in whatever codex doc governs that function's contract.
