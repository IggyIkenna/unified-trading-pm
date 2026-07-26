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
status: open
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
last_updated: "2026-07-26"
resolved_by:
---

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
