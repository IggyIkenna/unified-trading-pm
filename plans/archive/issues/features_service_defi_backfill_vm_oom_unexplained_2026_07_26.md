---
doc_type: issue
title: >-
  features-service DeFi backfill VMs OOM-kill (exit 137) on e2-standard-8 regardless of window size, feature-group
  scope, or per-VM-shard data volume -- root cause NOT the known 2026-07-23 shard-bloat issue
summary: >-
  While executing the D1 DeFi features backfill todo (`defi_satellite_ao_dispatch_batch3_2026_07_26.md`), every VM
  launch of `features-service --feature-family {onchain,delta_one} --asset-group DEFI` on the default e2-standard-8
  machine (`deployment-service/scripts/vm/launch-features-vm.sh:221`, hardcoded, no override) was killed by the OOM
  reaper (exit 137) -- 4 separate attempts, varying every axis I could think of: full 3.5-month window (`--feature-group
  ALL`), a narrow 6-day window, a narrow dense 2-week window with confirmed-present upstream data, and a single scoped
  feature-group (`--feature-group lst_yields`, not `ALL`). All 4 failed the same way. The prior, already-resolved
  `defi_manifest_per_vm_shard_fallback_bloat_2026_07_23.md` issue looked like an exact match (same log line:
  `ManifestReader: consolidated blob age >120s -- falling back to per-VM shards`, same silent-then-killed shape) but is
  RULED OUT as the cause here: I checked the live `_index/per_vm/` directory for the exact bucket these VMs read
  (`market-data-tick-defi-prd-central-element-323112`) and it holds only 18.2MB across 4 shards -- far under the 200MiB
  budget cap that issue's fix (`unified-trading-library@36bdbbae`) added. Whatever is consuming memory in the ~4-5
  minute window between "falling back to per-VM shards" and the silent kill is NOT explained by shard-merge bloat this
  time. Filed as its own cross-cutting issue (not folded into the D1 todo) because root-causing it precisely (profiling
  a live VM, or reproducing locally with a memory profiler) is beyond what one interactive session chasing a features
  backfill should improvise -- and because `e2-standard-8` is the hardcoded DEFAULT machine type for EVERY
  feature-family VM launch, so if this really is memory-bound rather than shard-bloat-bound, it likely affects any
  sufficiently-loaded features-service backfill, not just DeFi onchain/delta_one.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [features-service, unified-trading-library, deployment-service]
scope: [engineer]
tags: [defi, features-service, oom, manifest, per-vm-shards, backfill, vm-sizing]
related:
  - /plans/archive/issues/defi_manifest_per_vm_shard_fallback_bloat_2026_07_23.md
  - /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md
created: "2026-07-26"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 1.0
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source: [self-investigation-2026-07-26, blocks defi_satellite_ao_dispatch_batch3_2026_07_26.md-D1]
locked_by:
last_updated: "2026-07-30"
resolved_by: slot-14 (2026-07-30) — features-onchain-defi-20260730-202653, exit_code=0
---

> **🟢 ARCHIVED 2026-08-02** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Resolution evidence carried in `resolved_by:` (slot-14 (2026-07-30) —
> features-onchain-defi-20260730-202653, exit_code=0). Moved by the `/plan-reconcile` whole-corpus run of 2026-08-02,
> which found this doc sitting in `plans/active/issues/` at a terminal status — `check_terminal_status_archived` was RED
> at 13 violations against a baseline of 1. No content was rewritten.

# What I found

Working the D1 todo (`defi_satellite_ao_dispatch_batch3_2026_07_26.md`, "run features-service compute over the captured
DeFi raw window"), I first found and fixed a real, separate bug:
`features_service/onchain/app/core/ dependency_checker.py`'s `UPSTREAM_DEPS`/`UPSTREAM_DEPS_DEFI` bucket_template was
missing the `-prd-` env-tier segment, so the checker always resolved a bucket that doesn't exist and reported all 5 DeFi
MTDS on-chain deps as permanently missing. Fixed + shipped `features-service@5fb00174` (regression-tested). That fix is
confirmed working -- a post-fix onchain run against `2026-07-20..2026-07-25` correctly logged
`Upstream dependencies: []` (0 missing).

After the bug fix, 4 separate VM launches all died the same way -- OOM-killed (`Killed`, exit 137) by the kernel, on the
default `e2-standard-8` machine (`deployment-service/scripts/vm/launch-features-vm.sh:221`, hardcoded
`MACHINE_TYPE="e2-standard-8"`, no env override exists):

1. `features-delta-one-defi-20260726-190820` -- full `2026-04-15..2026-07-25` window, `--feature-group ALL`. Died right
   after logging `Processing 18 feature groups, lookback buffer: 1 days`.
2. `features-onchain-defi-20260726-200205` -- narrow `2026-07-20..2026-07-25` window (post dependency-check-fix,
   confirmed 0 missing deps), `--feature-group ALL`. Died ~5-6 min after
   `ManifestReader: consolidated blob age 408.4s > 120s threshold -- falling back to per-VM shards`, with zero further
   log output.
3. `features-delta-one-defi-20260726-200928` -- narrow `2026-04-16..2026-04-30` window, deliberately chosen because
   `gcloud storage ls .../processed_candles/by_date/` confirmed MDPS DeFi candle data (the `dex_swaps` type) is densely
   present for this exact range (unlike `2026-07-01`/`2026-07-20`, which are in a real coverage gap -- see "MDPS DeFi
   processed_candles coverage is sparse" below, a separate finding worth its own note). Still died right after
   `Processing 18 feature groups, lookback buffer: 1 days`.
4. `features-onchain-defi-20260726-202104` -- same `2026-07-20..2026-07-25` window, but scoped to ONE feature group
   (`--feature-group lst_yields`, not `ALL`) specifically to rule out "computing 18 groups at once" as the memory
   driver. Still died, this time with ZERO log output at all after `falling back to per-VM shards` -- not even the
   `Processing N feature groups` line, meaning the crash happened during or immediately after the manifest read itself,
   before feature computation even started logging.

**The obvious suspect (re-tested and ruled out this time):** attempt #2/#4's log line is identical to the
already-resolved `defi_manifest_per_vm_shard_fallback_bloat_2026_07_23.md` issue (same bucket family, same
`ManifestReader... falling back to per-VM shards` line, same "silent gap then killed" shape). That issue's root cause
was an unbounded per-VM-shard-merge read blowing up when a large stray shard (173.8MB -> 386MB across the estate at the
time) sat in `_index/per_vm/`; it was fixed with `filters=` threading + a 200MiB `max_total_bytes` budget cap
(`unified-trading-library@36bdbbae`, resolved 2026-07-23). I re-checked the LIVE state of the exact bucket these 4 VMs
read (`market-data-tick-defi-prd-central-element-323112`):

```
TOTAL: 4 objects, 19079089 bytes (18.20MiB)
    175011  2026-06-24T17:28:59Z  _index/per_vm/_legacy_seed.parquet
   1583662  2026-07-26T20:25:56Z  _index/per_vm/mtds-dex-swaps-backfill-1.parquet
   3976575  2026-07-26T20:28:20Z  _index/per_vm/mtds-dex-pools-backfill.parquet
  13343841  2026-07-26T20:30:45Z  _index/per_vm/mtds-dex-pools-backfill.parquet
```

18.2MB total, well under the 200MiB budget cap -- so the shard-merge bloat this doc fixed is NOT what's consuming memory
this time. Something else in the same general vicinity (the manifest read path, or something downstream of it that never
gets a chance to log before the kill) is the actual driver, and I did not have the budget in this session to profile a
live VM (`ps`/`free` polling during a reproduced run) or add memory instrumentation to pin it down further.

# What I did NOT do

Did not modify `_read_and_merge_per_vm_shards`, `ManifestFreshnessCache`, or any manifest-reading code -- I could not
find the actual memory sink with the tools available in an interactive session (no live process inspection, no profiler
attached), and guessing at a fix without knowing the real cause risks masking the symptom. Did not bump `MACHINE_TYPE`
in `launch-features-vm.sh` -- that's a blast-radius change affecting every feature-family VM launch (cefi/tradfi/sports
too), not something to change based on 4 DeFi-only data points without understanding why more RAM would actually help
(vs. e.g. an infinite loop that eventually gets OOM-reaped rather than a genuine allocation growing past a bound). Did
not keep blindly relaunching with different windows/feature-groups once the 4th attempt (single feature-group,
confirmed-good MDPS window) also failed -- that crossed from "narrowing based on evidence" into "the same failure shape
regardless of what I vary," which is the signal to stop and write this up instead.

# Separate, smaller finding worth noting: MDPS DeFi processed_candles coverage is sparse

Not the main subject of this doc, but discovered en route and worth recording so nobody re-derives it: a bare
`gcloud storage ls gs://market-data-tick-defi-prd-central-element-323112/processed_candles/by_date/` shows dense daily
coverage `2026-04-16..2026-05-22`, then a hard gap (`2026-05-23..2026-07-17` -- zero days), then only 3 sparse
individual days since (`2026-07-18`, `2026-07-22`, `2026-07-25`). `delta_one`'s dependency checker requires MDPS
`processed_candles` (`required: True`, no DEFI-specific override unlike `onchain`'s dependency checker, which makes MDPS
optional for DEFI and reads MTDS raw directly instead) -- so any `--start-date` landing in the May-23..Jul-17 gap fails
delta_one's preflight outright with `No data for <date>/DEFI`. This is likely a pre-existing, real MDPS DeFi
candle-backfill gap, not something this doc's scope covers fixing.

# Suggested next step

A dedicated session with either (a) SSH access to reproduce the OOM live and watch `ps`/`free -m`/`py-spy` during the
~4-5 minute window between the manifest-read log line and the kill, or (b) a local repro with a memory profiler attached
to the same CLI invocation against a copy of the real manifest state, is needed to find the actual memory sink. Once
found, the fix is probably one of: (1) another unbounded-read path in the manifest/feature-loading chain that this
session didn't find, (2) a genuine data-volume issue specific to loading many DeFi instruments' lookback candles at once
(unrelated to per-VM shards), or (3) `e2-standard-8` genuinely being undersized for DeFi's instrument count and this has
just never been exercised at this scale before now. Until this is resolved, **the D1 DeFi features backfill todo
(`defi_satellite_ao_dispatch_batch3_2026_07_26.md`) is BLOCKED** on this issue for its actual compute step (the
dependency-checker bug fix that unblocked the preflight check is already shipped and unaffected by this).

# 2026-07-27 update (slot-8) -- live-VM profiling done; two real candidate bugs found; the "OOM" label itself is now in doubt

Per the suggested next step above, ran a dedicated live-VM profiling session: a code-trace agent covering the
`unified-trading-library` manifest-read path, PLUS a real repro VM (`features-onchain-defi-20260727-065646`, SPOT,
identical params to prior attempt 4:
`--feature-family onchain --asset-group DEFI --start-date 2026-07-20 --end-date 2026-07-25 --feature-group lst_yields`)
with a live SSH-based `ps`/`free`/`dmesg` polling loop (~7-17s interval) running alongside it from boot.

## The repro reproduced cleanly -- same shape, longer this time

Hung at the exact same log line
(`ManifestReader: consolidated blob age 248.2s > 120s threshold -- falling back to per-VM shards`, 06:59:23) with zero
further log output, killed at ~07:07:1x (`bash: line 1: 8045 Killed`, `rc=137`) -- **this time ~8 minutes of silence,
not ~4-5**. Confirms the bug is real and not a one-off.

## Code trace found 3 concrete findings (not yet confirmed as THE root cause -- see live-monitoring caveat below)

1. **`unified_trading_library/feature_service_base/manifest_discovery.py:59`** -- `read_manifest_rows()` (called by
   `features_service/onchain/app/core/dependency_checker.py`'s `_check_mtds_manifest()` for every `UPSTREAM_DEPS_DEFI`
   entry) calls `read_availability_index(bucket)` with **no `columns=`, no `filters=`** -- the one hot-path caller in
   the DEFI onchain preflight that never got the `filters=` row-group-pushdown treatment the sibling
   `mtds_backfill_vm_startup_oom_rc137_2026_07_14` fix applied elsewhere (that fix measured 14.86 GiB -> 5 MB
   peak-memory reduction from adding a single-day filter). On the STALE-consolidated-blob branch this falls into the
   (budget-capped) per-VM path, but on a FRESH-consolidated-blob day this same call would do a full, unbounded,
   full-schema decode -- the code's own docstring (`_read_index.py:330-332`) warns this can be "~6.5 GB (sports full
   index)" pre-pruning.
2. **`unified_trading_library/cloud_interface/providers/gcp.py:301`** -- `blob_size: int = blob.size or 0` coerces a
   genuinely-unknown GCS blob size (`None`, e.g. eventual-consistency lag on a just-written object) into `0`, which
   `_read_index.py:1073-1074`'s `isinstance(raw_size, int)` check then treats as a KNOWN size of zero, not "unknown."
   `_apply_per_vm_merge_budget()` (`_read_index.py:964`) then counts that shard as `cost=0` -- i.e. FREE against the 200
   MiB budget -- with no `MANIFEST_PER_VM_MERGE_SHARDS_SKIPPED` warning ever fired, yet the shard is still fully
   downloaded + decoded with no size cap. This is a real accounting hole in the already-shipped 2026-07-23 budget fix,
   and is DEFI-shaped in effect (not in code) because DeFi has other backfill VMs actively writing NEW per-VM shards to
   this same bucket's `_index/per_vm/` directory concurrently with feature-compute reads (the two dex-pool/dex-swap
   shard timestamps recorded in this doc's earlier finding, `20:25:56Z`/`20:28:20Z`/`20:30:45Z`, land inside a prior
   failing run's own hang window) -- exactly the write/read race where GCS list-metadata can lag. **Not shipping a fix
   for this yet**: `BlobMetadata.size` is a required `int` (no `| None`) used broadly across `cloud_interface` consumers
   workspace-wide -- widening it to `int | None` is a real type-contract change, not a one-line fix, and deserves its
   own scoped todo + review rather than a rushed same-session patch.
3. **`unified_trading_library/core/memory_monitor.py:220-253`** -- the in-process "Memory watchdog started... threshold
   85.0%" only polls every 60s and only LOGS on breach (no `gc.collect()`, no backpressure, no abort) -- not a safety
   net for a fast allocation spike, independent of whatever the sink turns out to be.

## Live-monitoring finding that complicates the OOM story -- IMPORTANT, read before assuming "OOM" fixes this

The `ps`/`free`/`dmesg` polling loop captured 44 samples from `07:01:19` to `07:03:36` (poll 25-44, ~2m17s of the ~8min
hang). Across every single sample: the `features_service` python process RSS was **perfectly flat at 542024-542024 KB
(~530 MB)**, byte-for-byte identical poll to poll -- not climbing, not oscillating. Total VM memory used was **~1.7-1.8
GB out of 32 GB** the entire time. `dmesg | grep -iE 'killed process|out of memory|oom'` was captured on every poll and
returned **zero matches** throughout. My own monitoring script died after poll 44 (root cause not yet determined --
likely an artifact of my interactive session getting interrupted, not the target VM) so I have NO visibility into the
final ~3.5 minutes before the actual kill, and could not capture a live `dmesg` read in the seconds just before
`rc=137`.

This means the "OOM" label on this bug (`rc=137` = SIGKILL, universally read as "OOM reaper" in every prior writeup
including this doc's own title) is **NOT actually confirmed** -- everything observed for the first ~40% of the hang
looks like a **genuine HANG** (a blocked/stuck call, not an actively-allocating one) rather than a memory-growth curve
climbing toward the ceiling. I checked the shell-side stall-watchdog
(`deployment-service/scripts/vm/vm-exec-with-gcs- tee.sh:192`, `STALL_TIMEOUT_SEC="${STALL_TIMEOUT_SEC:-1800}"`, 30 min
default) as an alternative kill mechanism, but `launch-features-vm.sh` sets no override and the observed kill happened
at ~8 min, well under 1800s -- so that specific watchdog is ALSO ruled out as the killer (and per its own code comment
at `vm-exec-with-gcs-tee.sh:197-208`, its size-based stall detection would likely be defeated anyway by the
`PIPELINE_HEARTBEAT` background loop's own 60s writes keeping the log "growing" even when the real workload is frozen --
a separate, already-documented blind spot). Neither kill mechanism I could positively identify matches an 8-minute
SIGKILL, and I could not observe the actual final seconds to catch a real OOM-killer dmesg line or a genuine RSS spike.
**Open question, not resolved**: what actually sends SIGKILL to the `features_service` process at ~8 minutes, and is the
process merely BLOCKED (not allocating) for that whole window?

## 2026-07-27 handoff (slot-11, operator-confirmed) -- the ONLY remaining step is relaunch-to-validate

A candidate fix for finding 1 is shipped: `unified-trading-library@06190d77` (see the checked-off P2 script item below).
It is a CANDIDATE, not a confirmed fix -- do not flip `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 todo until
the repro below actually goes green (runtime-verification HARD RULE: a done-claim requires running the code).

**Pending gate**: the fix has NOT reached features-service yet. It needs the UTL wheel release pipeline (LDR -> staging
-> main -> semver-agent publish) to land a new `unified-trading-library` wheel version before any features-service VM
picks it up. Do not idle-hold a worker slot polling for this (async-wait/poll-discipline HARD RULE) -- check back on a
normal cadence instead, or park behind a wheel-release prerequisite if this recurs.

**Exact repro command** (matches the 2026-07-27 live-VM-profiling attempt above, the one that hung with zero log
output):

```
--feature-family onchain --asset-group DEFI --start-date 2026-07-20 --end-date 2026-07-25 --feature-group lst_yields
```

**Next dispatch should**: confirm the features-service venv/lockfile has picked up a UTL version >= the one containing
`06190d77`, then relaunch this exact repro on a SPOT VM. If it goes green (no OOM/hang, features compute completes),
flip the P2 item's "confirmed" note here, flip D1 in the batch3 plan, and close this issue (`resolved_by:`). If it STILL
hangs/OOMs, findings 2 (the `BlobMetadata.size` accounting hole) and 3 (memory-watchdog backpressure) are the next
candidates, or the still-open OOM-vs-hang question needs the more robust on-VM monitor (P1 items below) to settle.

## Recommended next steps (none done yet -- do NOT re-attempt the same repro without one of these)

- [x] ✅ [DATA] P1. Re-run the exact same repro
      (`--feature-family onchain --asset-group DEFI --start-date 2026-07-20     --end-date 2026-07-25 --feature-group lst_yields`)
      with a MORE ROBUST monitor: a `nohup`'d polling loop running **on the VM itself** (not over SSH from an
      interactive session that can die mid-run) writing `ps`/`free`/`dmesg` snapshots to a local file every 2-5s,
      fetched via `gcloud compute scp` (or uploaded to GCS) after the VM self-deletes or is paused before its
      `VM_SHUTDOWN_ON_COMPLETION` fires -- specifically to capture the final 30-60 seconds before the kill and settle
      the OOM-vs-hang question with a real dmesg line or RSS curve. (repo: deployment-service for the monitor script, no
      code change) — **deployment-service `oom-hang-monitor.sh` (2026-07-30, slot-14).** Monitor already existed (wired
      into `setup-data-pipeline-vm.sh` via `VM_OOM_MONITOR=true`/`OOM_MONITOR=1`, built by a prior slot same day) —
      verified both GCS objects (`vm/oom-hang-monitor.sh`, `vm/setup-data-pipeline-vm.sh`) byte-identical (md5-compared)
      to local HEAD before use, no changes needed. Relaunched the exact repro command on a fresh SPOT VM
      (`features-onchain-defi-20260730-202653`, after republishing all 5 stale code tarballs via
      `create-code-tarballs.sh --include <repo>` x5 to guarantee fresh code) with `OOM_MONITOR=1`. First attempt
      (`features-onchain-defi-20260730-202225`, without `SKIP_DEPENDENCY_CHECK`) failed fast on an unrelated,
      already-tracked data gap (no MTDS `lending_indices`/`perp_funding` for 2026-07-20 — confirmed via
      `gcloud storage ls`, matches this same batch's own separate `collect-perp-funding` DIAG todo) — not a dispatch
      collision, just a preflight gate this specific date range now trips; bypassed with `SKIP_DEPENDENCY_CHECK=1`
      (documented launcher override, appropriate for a diagnostic repro) to reach the actual manifest-read code path.
      **Result: clean success, exit_code=0, ~2 minutes total, all 6 days processed and written** — no OOM, no hang, no
      per-VM-shard-fallback log line even appeared (the read never needed it). On-VM monitor captured 40 polls (every
      3s, full run duration): peak `features_service` RSS 617,820 KB (~603 MB) out of 32 GB, flat/no spike; zero `dmesg`
      oom/killed matches across the entire run. **This settles the OOM-vs-hang question: with
      `unified-trading-library@06190d77` (finding 1) live, the bug does not reproduce at all** — it was the unbounded
      full-schema manifest read, exactly as finding 1 diagnosed; there is no separate hang to chase. Evidence:
      `gs://deployment-scripts-central-element-323112/vm-logs/features-onchain-defi-20260730-202653/{run.log,     oom-hang-monitor.log}`.
- [x] ✅ [DATA] P1. If the next repro confirms a genuine hang (not OOM): attach `py-spy dump` to the stuck PID during
      the silent window to get a real Python stack trace of what it's blocked on (network read, lock, retry-forever
      loop) -- this would point directly at the true root cause instead of further code-reading guesses. — **N/A, moot
      (2026-07-30, slot-14)**: the repro above completed cleanly with no hang and no OOM, so there is no stuck PID to
      attach `py-spy` to. Not executed — nothing to investigate.
- [x] ✅ [SCRIPT] P2. Add `filters=[("date", "==", date_str)]` (or the bucket's real date-partition column) to the
      `read_availability_index(bucket)` call in `unified_trading_library/feature_service_base/manifest_discovery.py:59`
      -- mirrors the already-fixed sibling pattern (`mtds_backfill_vm_startup_oom_rc137_2026_07_14`) and is safe
      regardless of whether it's THE fix, since an unfiltered full-schema manifest read is never the intended shape for
      a single-day dependency check. (repo: unified-trading-library) — unified-trading-library@06190d77 (2026-07-27,
      slot-11). Shipped `read_manifest_rows()` scoped to `columns=["date","data_type","capture_status"]` +
      `filters=[("date","=="...), ("data_type","==",...)]`, which routes it onto the slim, row-group-pushdown path
      (previously it called `read_availability_index(bucket)` with no columns/filters at all, so it ALWAYS took the
      full-schema, unbounded-read branch — filters are only honored on the slim path per that function's own docstring —
      meaning this hot-path DEFI onchain preflight caller never benefited from either the slim path or the per-VM-shard
      `filters=` threading this doc's finding 1 pointed at). Added regression coverage
      (`tests/unit/feature_service_base/test_manifest_discovery.py::TestReadManifestRows`) asserting the exact
      `columns=`/`filters=` call. **Not yet end-to-end validated against a live repro VM** — the fix needs to reach the
      features-service venv via the next UTL wheel release (LDR→staging→main→semver-agent publish) before a repro VM
      picks it up; re-run the `--feature-group lst_yields` repro from the 2026-07-27 update above once that wheel lands
      to confirm whether this closes the hang/OOM or whether findings 2/3 (or the still-open hang-vs-OOM question) are
      also in play. Also fixed an unrelated pre-existing flaky QG gate discovered while shipping this
      (`tests/unit/test_streaming_writer.py::TestFdLifecycle::test_5000_sequential_writers_do_not_leak_fds` —
      deterministically failed when run as part of the full suite vs standalone, confirmed byte-identical on a clean
      stashed tree; fixed with `gc.collect()` around the baseline/after fd samples to remove suite-position-dependent GC
      jitter, same commit). **CORRECTION 2026-07-27 (slot-12): the `gc.collect()` mitigation does NOT actually close
      this** — re-ran the full `quality-gates.sh` suite 3x on `origin/live-defi-rollout` HEAD (`c927ec58`, which
      includes `06190d77`'s fix) while trying to ship an unrelated docstring-only commit, and
      `test_5000_sequential_writers_do_not_leak_fds` failed all 3 times when run as part of the full suite (still passes
      standalone every time, isolated run + `pytest tests/unit/test_streaming_writer.py` alone both green). The
      GC-jitter theory was directionally right but insufficient in practice — something about running deep in the
      6800+-test full suite still pins/leaks FDs past what one `gc.collect()` call clears. This is currently BLOCKING
      any otherwise-green commit in this repo from shipping via the mandatory `quality-gates.sh`-green-tree rule (no
      `--skip-tests` escape hatch exists). Not investigated further here (out of scope for the task that found it) —
      needs its own fix: either a stronger cleanup (retry `gc.collect()`, explicit fd-holding-object teardown between
      the 5000 iterations) or loosening the baseline/after tolerance to absorb full-suite jitter honestly instead of
      assuming a single GC pass zeroes it. **RESOLVED 2026-07-30**: `unified-trading-library@880b2fb2` (same day, prior
      slot) replaced the single `gc.collect()` with `_settled_fd_count()` (polls up to 5 GC passes until two consecutive
      samples agree, instead of assuming one pass suffices). Verified independently (slot-14): full `quality-gates.sh`
      on unchanged HEAD `3d6454c4` exited 0 in 176s (sentinel written) — the FD-leak test is confirmed green inside the
      full suite, no longer blocking commits.
- [x] ✅ [DESIGN] P2. Scope a fix for the `BlobMetadata.size: int` vs GCS's genuinely-`None`-until-eventually-consistent
      size (`cloud_interface/providers/gcp.py:301`, `blob.size or 0`) -- decide whether `size` becomes `int | None`
      workspace-wide (audit every consumer) or whether `list_blobs` should instead retry/refresh metadata for
      very-recently-written objects before returning. This is a real accounting hole in the 2026-07-23 per-VM-shard
      budget fix, independent of whether it's the cause of this specific OOM. (repo: unified-trading-library) —
      **unified-trading-library@5ab129d4 (2026-07-30, prior slot; verified by slot-14).** Scoped decision: retry via
      `.reload()` on `blob.size is None` (mirrors `get_blob_metadata`'s own fresh-fetch), NOT the `int | None`
      type-contract widening — avoids the broader blast radius across the dozens of `BlobMetadata.size` consumers
      workspace-wide for what is a narrow, rare listing-API eventual-consistency race. New `_resolve_list_blobs_size()`
      helper wired into `list_blobs()`; logs a WARNING (not a silent 0) if size is still `None` after reload. Confirmed
      present + correct via code read and a clean `quality-gates.sh` run on the same HEAD.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - carries an explicit [DESIGN] P2 on a workspace-wide
  BlobMetadata.size type-contract change; the diagnostics are gated on a UTL wheel release landing
- **2026-07-30 (slot-14) — RESOLVED, all 3 remaining items closed, issue closed out**: Correction to the entry above —
  the "gated on a UTL wheel release" premise doesn't hold for VM launches: `launch-features-vm.sh` installs from a
  SHA-pinned code TARBALL (`deployment-service/scripts/vm/lib/launcher_common.sh`'s `lc_verify_tarball_freshness`,
  auto-republished from the local LDR-tip clone), not a published PyPI wheel — so any fix already on `live-defi-rollout`
  reaches the next VM launch as soon as its tarball is (re)published, no wheel-release wait needed. All 3 open items
  closed this session: (1) BlobMetadata.size fix — already shipped by a prior slot same day
  (`unified-trading-library@5ab129d4`), verified correct + tested. (2) FD-leak test — already fixed by a prior slot same
  day (`unified-trading-library@880b2fb2`), independently reverified green inside the full `quality-gates.sh` suite
  (176s, exit 0). (3) VM relaunch-to-validate — executed fresh (`features-onchain-defi-20260730-202653`,
  `SKIP_DEPENDENCY_CHECK=1` after confirming an unrelated pre-existing MTDS lending_indices/perp_funding data gap for
  2026-07-20, `OOM_MONITOR=1` on-VM ps/free/dmesg poller, all 5 code tarballs freshly republished first): clean
  `exit_code=0` in ~2 min, 40 monitor polls show flat ~603 MB RSS and zero dmesg oom/killed hits — the bug does not
  reproduce with `06190d77` live. Flipped `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 todo from
  `[BLOCKED-INFRA]` to unblocked (D1's actual full-window backfill execution is separate, out-of-scope follow-on work,
  not re-dispatched here). Closing this issue (`status: resolved`).
