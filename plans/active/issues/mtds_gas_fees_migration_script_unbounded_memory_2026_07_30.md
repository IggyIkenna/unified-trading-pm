---
doc_type: issue
title: >-
  migrate_legacy_gas_fees_venue_2026_07_30.py had an unbounded-memory ManifestWriter call — killed a slot-7 subprocess
  TWICE in ~15 minutes, both times taking down the whole orchestrator API (fleet-wide outage, not scoped to this
  migration) — ROOT-CAUSED + FIXED
summary: >-
  While investigating an unrelated question, main found orchestrator.service's cgroup pinned at `MemoryAvailable: 0`
  with every HTTP endpoint returning `HTTP:000`. Root-caused to a single subprocess spawned by slot-7's worker:
  `market-tick-data-service/scripts/migrate_legacy_gas_fees_venue_2026_07_30.py --limit 5 --log-level INFO` (PID
  3062883) had grown to 44.5GB RSS (68.6% of the host's 64GB RAM) over 57 minutes. Killed it (SIGTERM, died gracefully
  within 5s), memory recovered instantly. ~15 minutes later the SAME script recurred, this time launched WITHOUT
  `--limit` (full run) by the SAME slot-7 worker, and reached 45.4GB RSS in just 7 minutes — faster, not slower — before
  being killed again. **Root cause (confirmed by slot-7, data_engineering)**: the script's `ManifestWriter(...)`
  construction omitted `per_vm_shards=True`.
  `unified_trading_library.manifest_writer._state._resolve_per_vm_shards(None)` defaults to `False` unless the caller
  passes it explicitly or the process has `MANIFEST_PER_VM_SHARDS=true` in its environment — production services get
  that from deployment config, but this standalone one-off script never set it. Every `.add()`/`.close()` flush
  therefore took the LEGACY direct-CAS path against the canonical `_index/availability_index.parquet` for the DeFi
  bucket — a read-merge-write of the FULL consolidated index (~14.86 GiB / 27M+ rows for this bucket unfiltered),
  independent of the migration's own worklist size (explaining why even `--limit 5` leaked to 42GB+). **Fixed**: pass
  `per_vm_shards=True` explicitly (market-tick-data-service@8016c7e4); verified safe under a real throwaway probe write
  inside a `ulimit -v 3000000` (3GB) cap — completed in ~1s, wrote a fresh ~22KB per-VM shard, no OOM.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library, agent-orchestrator]
scope: [engineer, admin]
tags: [defi, gas-fees, memory-leak, manifest-writer, incident, fleet-wide-outage, migration-script, slot-7]
related:
  [
    /plans/archive/issues/defi_gas_fees_historical_venue_path_migration_2026_07_28.md,
    /plans/active/issues/orchestrator_api_full_outage_stale_cgroup_memory_cap_2026_07_30.md,
    /plans/active/issues/expand_defi_pool_catalogue_script_unbounded_memory_2026_07_31.md,
    /codex/02-data/availability-manifest-and-data-status.md,
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
  Discovered incidentally by main while investigating an unrelated `/api/backlog` hang on 2026-07-30, which turned out
  to be a symptom of this script consuming nearly all host RAM. Root-caused + fixed by slot-7 (data_engineering) the
  same session.
resolved_by:
locked_by:
locked_since:
---

# gas_fees migration script — unbounded memory via ManifestWriter legacy path, caused 2 fleet-wide API outages in ~15 minutes

## What's confirmed (incident forensics — main)

1. **First occurrence, ~09:58 UTC 2026-07-30**: `orchestrator.service`'s cgroup showed `available: 0B` (a separate,
   already-fixed incident from earlier the same morning,
   `orchestrator_api_full_outage_stale_cgroup_memory_cap_2026_07_30.md`, ruled out the cgroup CAP being stale this time
   — the cap was already correctly scaled to 64GB). `ps aux --sort=-%mem` found the actual cause: PID 3062883,
   `.venv/bin/python scripts/migrate_legacy_gas_fees_venue_2026_07_30.py --limit 5 --log-level INFO`,
   `VmRSS: 44559256 kB` (~42.5GB), state `D` (uninterruptible disk sleep), running 57m21s. Confirmed via
   `/proc/<pid>/cgroup` this process lives INSIDE `orchestrator.service`'s cgroup (a child of slot-7's tmux session —
   every slot's spawned subprocess does), so it was directly consuming the same memory budget as the API process itself.
2. **Ownership confirmed**: `sudo -u ubuntu tmux capture-pane -p -t orch-slot-7` showed the worker's own todo list —
   "Copy + manifest-verify each of 14 legacy prefixes to venue=ALCHE…" — mid-flight on
   `defi_gas_fees_historical_venue_path_migration_2026_07_28.md`'s migration, currently polling a backgrounded "smoke
   test" Task Output with no output yet. This was a genuine, in-progress, legitimate task — the SCRIPT had the bug, not
   the worker's usage of it.
3. **Killed (SIGTERM → died in <5s, no SIGKILL needed)** — memory recovered immediately (`free -m` available: 10,164MB →
   53,268MB in the same check). API responded HTTP:200 within seconds.
4. **Second occurrence, ~10:00-10:07 UTC**: same script, same slot 7, this time launched WITHOUT `--limit` (a full run
   against all 12,424 work items) — PID 4007786, reached `VmRSS: 45,430,120 kB` (~45.4GB, 70.1% of host RAM) after only
   ~7 minutes (faster growth than the first occurrence). Killed again (SIGTERM, died immediately). Memory: available
   10,856MB → 55,382MB.
5. **First notification attempt (immediately after occurrence 1) timed out** — the orchestrator API was still recovering
   from occurrence 1's own memory pressure at that exact moment, so the `/api/slots/7/message` POST itself hit the same
   `HTTP:000` symptom. This is almost certainly why occurrence 2 happened — the worker never saw the "don't re-run this"
   warning before launching the full (unbounded) run. **Second notification attempt, after occurrence 2 was killed and
   memory recovered, succeeded** (`HTTP 200`).

## Root cause (confirmed — slot-7, data_engineering)

`unified_trading_library/manifest_writer/_state.py::_resolve_per_vm_shards()` defaults to `False` (the legacy CAS path)
unless the caller passes `per_vm_shards=True` explicitly OR the process has `MANIFEST_PER_VM_SHARDS=true` in its
environment. Production services get that env var from their deployment config; the standalone migration script (run
directly via `.venv/bin/python` with only
`GCP_PROJECT_ID`/`PROJECT_ID`/`CLOUD_PROVIDER`/`DEPLOYMENT_ENV`/`CLOUD_MOCK_MODE` set) never set it, so its
`ManifestWriter(service_name=..., catalogue_bucket=..., batch_size=...)` construction silently took the legacy path.

The legacy path's flush reads the ENTIRE consolidated `_index/availability_index.parquet` for the DeFi bucket into a
pandas DataFrame to merge new rows in — documented elsewhere in this codebase as ~14.86 GiB unfiltered for this bucket
(27M+ rows). This explains both the memory scale AND why it's independent of worklist size: the 5 GCS object writes in
the `--limit 5` run themselves completed in ~1.5s (confirmed via slot-7's own log capture) — the leak was entirely
inside the subsequent `ManifestWriter.close()` legacy-path flush, which happens once per run regardless of how many work
items were processed (occurrence 2's faster growth is consistent with the `batch_size=500` auto-flush boundary being hit
sooner once more items were already fast-resume-skipped between the two runs).

This rules out every theory in the original "What is NOT yet known" section below (kept for the record —
`write_defi_rows()` accumulation, an over-broad `list_blobs` prefix, and an oversized legacy parquet were all plausible
before this was traced, but none of them is the actual cause).

**Fix applied** (`scripts/migrate_legacy_gas_fees_venue_2026_07_30.py@8016c7e4`): pass `per_vm_shards=True` explicitly
to `ManifestWriter(...)`. This routes every write to this host's own `_index/per_vm/{instance}.parquet` shard (small,
host-scoped) instead of the full consolidated index. **Verified safe**: ran a real (throwaway) probe write —
`ManifestWriter(..., per_vm_shards=True).add(...); .close()` — under a hard `ulimit -v 3000000` (3GB virtual-memory cap)
via a wrapped subshell; completed in ~1s, produced a fresh ~22KB per-VM shard, no OOM. The probe row
(`chain="TESTCHAIN_SAFETY_PROBE"`) and its tiny shard file were deleted immediately after verification — no fake data
left in the manifest.

## Why it matters

- **Any ad-hoc/one-off script that constructs `ManifestWriter` directly (not via a deployed service with
  `MANIFEST_PER_VM_SHARDS=true` already in its env) is exposed to this same failure mode** — not unique to the gas_fees
  migration; it's a missing safe-default in a widely-used shared utility. A one-off script author has no way to know the
  legacy path exists, let alone that it's ~14GB-scale for a populous bucket, without reading `_state.py` internals.
- **This took down the entire orchestrator fleet twice**, not just one slot — a shared-host blast radius far beyond the
  scope of a single migration task, exactly the class of incident the "confirmed runaway process...may be killed" HARD
  RULE (CLAUDE.md, codified same day) exists to catch and recover from quickly.
- **`ManifestWriter`'s own default is the unsafe one** — `per_vm_shards` defaulting to `None`→`False` means every caller
  who doesn't know to opt in inherits the expensive path silently, with no warning at construction time about the memory
  cost this implies for a large bucket.

## What was investigated but is NOT the cause (kept for the record)

Before the root cause above was traced, three theories were live candidates — none panned out, but the elimination
process is worth keeping so a future similar incident doesn't re-walk the same dead ends:

1. `write_defi_rows()` accumulating something across calls — ruled out; the function is stateless per-call and the leak
   reproduces identically with a trivial `ManifestWriter.add()+close()` probe that never calls `write_defi_rows()` at
   all.
2. `_legacy_prefix()` / `list_blobs(prefix=...)` matching far more blobs than the "1-2 near-duplicate leaf-name
   variants" the script's docstring describes — ruled out; the real blob count under a sampled worklist prefix was
   confirmed to be exactly 2, both small, both already downloaded successfully in ~1.5s total for all 5 work items.
3. An oversized legacy parquet file — ruled out; same timing evidence as (2), and doesn't explain occurrence 2's faster
   growth under more work items as cleanly as the confirmed `ManifestWriter` legacy-path cause does.

## Todos

- [x] [DATA] P0. Root-cause the actual leak location. — **Done 2026-07-30 (slot-7)**: traced to `ManifestWriter(...)`
      missing `per_vm_shards=True`, hitting the legacy direct-CAS full-index read-merge-write path. Fixed + verified
      safe under a `ulimit -v` cap (see above). (repo: market-tick-data-service)
- [x] [BACKEND] P0. Kill the runaway process + restore orchestrator API availability (both occurrences). — **Done
      2026-07-30**: SIGTERM both times, no SIGKILL needed, API HTTP:200 within seconds each time.
- [x] [BACKEND] P1. Notify slot 7's worker so it doesn't blindly retry. — **Done 2026-07-30**: first attempt timed out
      (API itself down at that moment); second attempt succeeded, worker told not to re-run until root-caused, pointed
      at this doc.
- [ ] [DATA] P1. Add a construction-time safety check to `ManifestWriter.__init__`
      (`unified-trading-library/unified_trading_library/manifest_writer/_writer.py`): when `per_vm_shards` resolves to
      `False` (no explicit arg, no `MANIFEST_PER_VM_SHARDS` env), log a loud one-time warning naming the legacy path's
      memory cost for the target bucket (or refuse construction outside a recognized deployed-service context) so a
      future one-off script doesn't silently inherit the unsafe default. (repo: unified-trading-library)
- [ ] [DATA] P2. Audit `market-tick-data-service/scripts/` (and sibling repos' `scripts/`) one-offs for any OTHER direct
      `ManifestWriter(...)` construction missing `per_vm_shards=True` against a populous bucket (defi/cefi/sports) —
      same failure mode is latent wherever found. (repo: market-tick-data-service, instruments-service,
      market-data-processing-service) **na-eligibility-audit 2026-08-01: extracted to
      `defi_satellite_ao_dispatch_batch7_2026_08_01.md` (conflict-check cleared — the failure mode has since recurred a
      3rd time via `DefiManifestRecorder@77738598`, strengthening the case for the sweep, no one has yet run it) — track
      completion there, close this checkbox by citation once its batch-7 todo lands.**
- [ ] [REVIEW] P2. This is the SECOND fleet-wide memory incident within the same session (the first, a stale cgroup cap,
      is fixed + self-healing per `orchestrator_api_full_outage_stale_cgroup_memory_cap_2026_07_30.md`) — consider
      whether a per-slot subprocess RSS ceiling (e.g. a `cgroup`/`ulimit` scoped to each slot's OWN spawned children,
      not just the whole `orchestrator.service` cgroup) would contain a future buggy script to ITS OWN slot instead of
      starving the entire fleet. Out of scope to design/implement here — flagging the pattern.

## Codex SSOTs

- None directly own migration-script memory safety today. If the `ManifestWriter.__init__` safety-check todo above
  lands, that + its regression test are the record; no new SSOT needed unless this turns out to be a reusable footgun
  broad enough to warrant one in `/codex/02-data/availability-manifest-and-data-status.md`.

## Progress Log

- **2026-07-30 (main)**: discovered incidentally, killed both runaway occurrences, restored API availability twice,
  notified slot-7, documented incident forensics + 3 leading (later-ruled-out) theories.
- **2026-07-30 (data_engineering slot-7)**: root-caused to `ManifestWriter`'s default legacy-CAS path (`per_vm_shards`
  unresolved → `False`); fixed the gas_fees migration script (market-tick-data-service@8016c7e4); verified the fix safe
  under a 3GB `ulimit -v` cap with a real throwaway probe write (cleaned up immediately after). Ruled out all 3 of
  main's leading theories. Added two standing follow-up todos (ManifestWriter safety warning, audit sibling scripts).
  Resuming the actual gas_fees migration next, in small monitored chunks.
- **2026-07-31 (review)**: cross-linked a same-class READ-side sibling incident — instruments-service's
  `expand_defi_pool_catalogue_from_manifest_2026_07_31.py` hit an unbounded manifest read + a lingering-process issue
  the same day (PID 2108132, killed by review; fix in-flight on slot 16, independently verified working). See
  `/plans/active/issues/expand_defi_pool_catalogue_script_unbounded_memory_2026_07_31.md` for full detail — that doc
  also notes this is now the fourth incident against the same availability manifest in ~36h (2 read-side, this
  write-side one, plus delta_one's and UTL's siblings), which is the basis for todo 4's "shared safe-read helper"
  question there.
- **na-eligibility-audit 2026-08-01**: MIXED — 3 open items. The construction-time safety-check item (line 154) and the
  per-slot RSS-ceiling item (line 163) stay KEEP-NA valid (design calls, the latter explicitly self-flagged out of scope
  here). The sibling-scripts audit item (line 159) extracted to `defi_satellite_ao_dispatch_batch7_2026_08_01.md` after
  conflict-check clear. Doc stays `assigned_vm: NA` overall.
