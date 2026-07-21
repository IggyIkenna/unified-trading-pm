---
doc_type: issue
title:
  "SUPERSEDED by mtds_backfill_vm_startup_oom_rc137_2026_07_14.md — dex-pools/dex-swaps SIGKILL is the SAME
  ManifestFreshnessCache OOM already tracked there fleet-wide (9 DeFi handlers, CEFI too)"
summary:
  "Backfilling DeFi handlers via VM (originally found on dex-pools/dex-swaps here) fails: SIGKILL (exit 137) within
  seconds of 'handler initialized', reproduced twice more here (e2-standard-4 16GB + e2-small 2GB, both die identically)
  on top of the original 3 attempts. Investigating this independently led to the SAME bug already under active, much
  deeper multi-agent investigation in `mtds_backfill_vm_startup_oom_rc137_2026_07_14.md` (live kernel-dmesg-confirmed
  OOM inside `ManifestFreshnessCache.bulk_load()`, fleet-wide blast radius across CEFI+DEFI, 2 still-open [BACKEND] P0
  todos). Contributed a new full-path local repro there (peak ~24.3GB, exceeds even the kernel-confirmed 14.67GB real
  OOM) that narrows the remaining open question toward Python-level tuple/set construction rather than the
  self-shard-merge path. **This doc's own findings are consolidated into the canonical doc — read that one, not this
  one, for current status.**"
status: open
nature: notes
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-trading-library]
scope: [engineer, admin]
tags: [vm-launcher, backfill, dex-pools, dex-swaps, infra, sigkill, oom, manifest-freshness-cache, superseded]
related: [../mtds_defi_dex_zero_capture_protocols_2026_07_14.md, mtds_backfill_vm_startup_oom_rc137_2026_07_14.md]
created: 2026-07-14
parent_epic: infrastructure_master
assigned_vm:
resolved_by:
source:
  "Discovered 2026-07-14 attempting the real historical backfill for the 4 newly-wired DeFi dex protocols, per operator
  instruction to launch backfill VMs after confirming MVP scope + single write path. Re-investigated same day via 2
  additional real VM launches + a local tracemalloc repro (per /autonomous re-dispatch), which converged on the SAME bug
  already tracked in mtds_backfill_vm_startup_oom_rc137_2026_07_14.md — findings merged there."
priority: P1
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
---

## What happened

Launched `mtds-dex-pools-backfill` + `mtds-dex-swaps-backfill` (both via the newly-added `--protocols` scoping,
`deployment-service@ecb956e8e`) for the 4 new protocols, 2023-01-01→today, SPOT provisioning (the launcher default).

**Attempt 1 (SPOT, both VMs, full 4-protocol/3.5yr range)**: both VMs booted, Python started, logged
`TheGraph key pool loaded: 9 keys available` + `DEX pools/swaps handler initialized`, one `RESOURCE_SAMPLE` (mem ~10%,
cpu ~70%), then **`Killed` (exit 137)** within ~10-20s of the handler initializing. `VM_SHUTDOWN_ON_COMPLETION`
self-deleted both VMs.

**Attempt 2 (SPOT, retry, same config)**: identical failure — same log shape, same timing, same exit code, for BOTH VMs
independently.

**Attempt 3 (on-demand, minimal — single protocol `uniswap_v2`, single day `2026-07-01→2026-07-02`, pools only)**:
different failure mode. Serial console confirmed the process genuinely launched (`Task launched PID: 6975`), but **zero
further output** appeared anywhere — not in the GCS-uploaded `run.log`, not on the serial console (checked with
`--start=<offset>` to see only new output), not a fresh `deployments/active/*.json` registration — for over 6 minutes.
`gcloud compute ssh` to the VM timed out twice (45s and 90s) with no response, not even the `echo CONNECTED` sanity
check. Deleted the hung VM rather than continue waiting.

## Root causes ruled out (with real evidence, not assumption)

- **Kill-switch**: `KillSwitchBus` is confirmed process-local/in-memory with no boot-time state restore anywhere in
  `unified_trading_library/kill_switch/` — a fresh process always starts with an empty, unarmed bus. MTDS itself has
  zero `kill_switch`/`KillSwitch` references in its own codebase. The "subscribers registered" log line that appears
  right before the SPOT crashes is provably inert (only registers a logging-only default handler, never checks armed
  state).
- **GCP-level SPOT preemption**: `gcloud compute operations list --filter="targetLink~<vm-name>"` shows only my own
  `insert`/`delete` operations (matching known launches + `VM_SHUTDOWN_ON_COMPLETION` self-deletes) — no
  `compute.instances.preempted` system operation, which GCP normally logs as a distinct operation type for a genuine
  preemption.
- **OOM**: the SPOT crashes' own `RESOURCE_SAMPLE` line, logged seconds before the kill, shows `mem=10.4%`/`mem=9.9%` —
  nowhere near the 85% `mem_crit` threshold, and `ResourceProfiler` itself only emits events/calls opt-in callbacks, it
  never sends SIGKILL directly (confirmed by reading `unified_trading_library/lifecycle/resource_profiler.py`).

## Still unexplained

- What sends SIGKILL to the SPOT runs within ~10-20s of the TheGraph handler initializing, consistently, twice.
- Why the on-demand run produces literally zero observable output (not even the OS-level heartbeat echo, which runs in
  an independent backgrounded subshell) for 6+ minutes, when the SPOT runs produced full, clean log output within
  seconds of Python starting.
- Why SSH to the VM itself is non-responsive — this is a separate signal from the workload failure and may point at a
  genuinely different problem (network/firewall/OS Login propagation) rather than something specific to the
  dex-pools/dex-swaps code.

## What's NOT the problem

The actual capture code is confirmed working — the real end-to-end smoke test
(`mtds_defi_dex_zero_capture_protocols_2026_07_14.md` §3) called the same `_query_and_parse`/`_run_cascade` functions
directly (bypassing VM/manifest infra) for all 8 shard combinations and got 100% real, non-empty rows. This is an
infrastructure/VM-launch problem, not a code correctness problem.

## Recommended next step

1. Try a DIFFERENT zone or a smaller/different machine type to rule out a zone-specific capacity/networking issue.
2. Check whether OTHER sibling agents' concurrent VMs in the same zone (several were found running healthily at the same
   time — `cefi-deribit-2026-heavy-*`, `tradfi-bf-cme-ohlcv-1m-*`, `af-backfill-*`) share any resource contention with
   mtds-dex-pools/swaps specifically (e.g., a per-service quota, not a zone-wide one).
3. If SSH genuinely can't reach ANY VM in this project/zone combination right now, that's a separate, broader diagnostic
   than this specific backfill.
4. Not retried a 3rd/4th time blindly — real diagnostic input is needed before another attempt is worth the VM cost.

## Progress Log

- **2026-07-14** — Filed after 3 failed real launch attempts (2 SPOT, 1 on-demand) with real, evidence-based elimination
  of kill-switch/preemption/OOM as causes. The historical backfill for the 4 new DeFi dex protocols remains un-run; the
  capture code itself is independently verified working via the direct smoke test.

## 🔴 2026-07-14 (later same day) — ROOT CAUSE FOUND: `ManifestFreshnessCache` reads the ENTIRE DeFi manifest into

memory at handler init, real peak ~24.3GB — genuine OOM, was invisible to `ResourceProfiler`'s 5s sampling, affects ALL
9 DeFi handlers that call it, not just dex_pools/dex_swaps

Picked this back up per `/autonomous` (operator dispatched a fresh diagnostic pass). Ran 2 more real VM launches to
gather evidence the original 3 attempts didn't have, then root-caused it with a local repro — full chain below.

**Attempt 4 (SPOT, `e2-small`, scoped to `--protocols uniswap_v2 --start 2026-07-01 --end 2026-07-03`)**: same failure
signature as before — `TheGraph key pool loaded` → `DEX pools handler initialized` → `Killed` (rc=137) within <1s. **New
finding this time**: the VM _instance_ stayed `RUNNING` in `gcloud compute instances describe` for the full watched
window (10 min) even though the actual work process died in the first few seconds — `VM_SHUTDOWN_ON_COMPLETION`
self-delete didn't fire for ~5.5 minutes after the kill, and this instance ended up STUCK (never actually self-deleted;
had to be manually `gcloud compute instances delete`d ~20 min later). **This invalidates instance-status-based
monitoring for this failure class** — watch the GCS-tee'd `run.log` content, not `gcloud compute instances describe`
status, to catch this kind of early-death-but-instance-lingers failure.

**Investigated whether a relevant fix had already landed**: found `unified-trading-library@0fc088a9`
("ManifestFreshnessCache uses slim column-pruned read_availability_index, not the ~6.5GB full-schema path") — filed
under incident tag `mtds_backfill_vm_startup_oom_rc137_2026_07_14`, landed same-day, matches this symptom almost exactly
(rc=137, crash right after handler init, before any per-venue output). Confirmed via `git merge-base --is-ancestor` that
this fix WAS present in the tarball SHA (`unified-trading-library-code@4378685816b1`) used for attempt 4. **The fix did
NOT resolve the crash** — attempt 4 still died identically despite running fixed code.

**Attempt 5 (SPOT, `e2-standard-4` — the ORIGINAL machine type, now confirmed running the fix)**: same crash, same
signature, `mem=11.2% rss=800MiB` sampled right before the kill (vs `mem=9.8% rss=543MiB` on attempt 4 — RSS climbing
between samples, consistent with a fast ramp mid-read). **Both a 2GB and a 16GB machine died identically** — this argues
AGAINST simple memory-exhaustion-relative-to-VM-size and (correctly, per the local repro below) toward a peak that
exceeds even 16GB.

**Local repro (the actual root cause)**: ran the exact code path
(`ManifestFreshnessCache(bucket=<defi-bucket>) ._maybe_refresh()`, matching the VM's
`MANIFEST_CONSOLIDATED_STALENESS_SEC=86400` env var so the fast/direct-read branch executes, not the stale-fallback
branch) locally with `tracemalloc` + `resource.getrusage`:

```
elapsed: 176.9s
tracemalloc current=17440.7MB peak=24286.5MB
ru_maxrss after=5888528.0 (KB, i.e. ~5.9GB resident at process end)
captured rows: 3,010,913
```

**Peak ~24.3GB, 3 million captured rows, for ONE unscoped read of the DeFi manifest.** This exceeds even the failed
`e2-standard-4` (16GB) attempt — explaining why both machine sizes died identically, and why `ResourceProfiler`'s 5s
sampling never caught it climbing (the whole read-to-peak cycle can complete faster than one sample interval on a
memory-constrained VM, since the kernel OOM-killer strikes as soon as available memory is exhausted — well before the
176.9s this took to run to completion, uninterrupted, on a local machine with enough RAM to actually finish it).

**Why the 0fc088a9 column-pruning fix wasn't enough**: read the actual implementation chain
(`unified_trading_library/manifest_writer/_read_index.py::_read_parquet_columns_safe`) — it does
`pd.read_parquet(io.BytesIO(data), columns=columns)`, which requires the FULL compressed bytes (`data`, ~445MB for the
DeFi manifest) to be downloaded into memory BEFORE column pruning is applied at decode time; column pruning shrinks the
DECODED DataFrame, but with 3M rows even a handful of pruned string columns is substantial, and
`ManifestFreshnessCache._refresh_locked` then builds a Python-level `set` of tuples from that DataFrame
(`_index_to_tuples`/`_index_to_skip_worthy_tuples`) — sets of tuples are notoriously memory-hungry in Python (tuple +
set/hash overhead routinely 3-5x the raw data size). **There is no date/asset-scoped filtering anywhere in this read
path** — `read_availability_index` has no predicate-pushdown parameter, only column selection; every caller gets the
ENTIRE bucket's manifest regardless of what date range it actually needs. This matches the ORIGINAL issue doc's own
observation that the crash is "insensitive to date-range size" — a 2-day backfill window pulls the exact same 3M-row,
24GB-peak read as an all-time backfill would.

**Blast radius — this affects ALL 9 DeFi handlers that call `ManifestFreshnessCache`, not just dex_pools/dex_swaps**:
`liquidations_handler.py`, `lst_rates_handler.py`, `gas_fee_handler.py`, `risk_params_handler.py`,
`liquidation_events_handler.py`, `dex_swaps_handler.py`, `perp_funding_handler.py`, `lending_indices_handler.py`,
`dex_pools_handler.py` — every one of them instantiates `ManifestFreshnessCache(bucket=...)` at handler init. Any VM
backfill for ANY of these 9 DeFi data types will hit the same crash once the DeFi manifest grows large enough (it
already has at 3M+ captured rows). **This is a cross-cutting DeFi infrastructure blocker, not a dex-pools-specific bug**
— reclassifying this doc's scope accordingly.

**Secondary, separate finding (not the root cause, but real)**: the DeFi manifest consolidator's blob was >5.8 hours
stale when checked locally (`ManifestReader: consolidated blob age 20934.0s > 120s threshold`) — well within the VM's
own 86400s tolerance so it did NOT contribute to this specific crash, but worth a consolidator-health check separately
(the local default 120s threshold existing at all suggests staleness is expected to matter for OTHER callers that don't
override it).

**Not fixed here.** A real fix requires restructuring `read_availability_index`'s read path to support row-group-level
predicate pushdown (date-range filtering BEFORE decode, e.g. via `pyarrow.parquet.read_table(..., filters=[...])`
instead of `pd.read_parquet(io.BytesIO(full_bytes), columns=columns)`) and/or replacing the Python-level tuple/set
materialization with something more memory-proportional to the ACTUALLY-needed scope — this is a genuine, non-trivial
change to a shared library function with 9 real production consumers, and rushing it without time to validate each
consumer risks exactly the "silent fleet regression" this workspace's own `AUTONOMOUS_AGENT_RULES.md` rule 11 warns
against. Recommended fix design for whoever picks this up: add an optional `date_range: tuple[str, str] | None` (or
similar) parameter to `ManifestFreshnessCache.__init__`/`read_availability_index`, defaulting to `None` (today's
unscoped behavior, zero blast radius for existing callers that don't pass it), and have the 9 DeFi handlers that DO know
their real backfill date range pass it through — this alone should cut the read from "entire manifest" to "the handful
of days actually being backfilled."

**Status**: while writing this up, found `mtds_backfill_vm_startup_oom_rc137_2026_07_14.md` — a much deeper,
already-in-progress, multi-agent/multi-slot investigation of this EXACT bug (live kernel-`dmesg`-confirmed OOM inside
`ManifestFreshnessCache.bulk_load()`, fleet-wide blast radius across CEFI+DEFI, not just DeFi). The "root cause
CONFIRMED" analysis above (independently reached the same `ManifestFreshnessCache` conclusion, plus a NEW full-path
local repro measuring ~24.3GB peak — exceeding even that doc's kernel-confirmed 14.67GB figure) is now merged into that
canonical doc as a new dated section, which directly answers one of its 2 still-open `[BACKEND] P0` todos. **This doc is
superseded — see `mtds_backfill_vm_startup_oom_rc137_2026_07_14.md` for current status, the 2 remaining open fix todos,
and the full multi-session investigation history.** Not closing this doc outright (it has its own useful narrower
history — the original 5-attempt dex-pools/dex-swaps reproduction, the stuck-instance-self-delete timing finding, and
the manifest-consolidator-staleness secondary finding) but treat the canonical doc as the source of truth going forward.
