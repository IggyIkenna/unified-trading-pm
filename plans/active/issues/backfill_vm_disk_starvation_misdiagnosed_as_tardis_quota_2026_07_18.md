---
doc_type: issue
title: >-
  Backfill VMs were disk-starved by a pd-standard 50GB boot disk — misdiagnosed for hours as a Tardis account quota
summary: >-
  A pd-standard 50GB boot disk sustains only ~6 MB/s of writes and its burst credits deplete by CUMULATIVE BYTES
  WRITTEN. Vendor payloads are .csv.gz, so download RX is ~5x amplified on write — 2.4 MB/s of download is ~12 MB/s of
  disk. Every backfill VM therefore ran ~12 MB/s for ~7.5GB and then collapsed to ~2.4 MB/s permanently. Measured
  directly with iostat on a degraded VM: %util 99.94, w_await 1015ms, aqu-sz 51, CPU 93.5% idle / 6.2% iowait, RAM 115GB
  free of 128, disk 11% full. VALIDATED fix: on pd-balanced 250GB the same workload sustained 11.1 MB/s past 21GB with
  peaks of 18.15 MB/s and no cliff — 4.7x. Swept across 57 download-heavy launchers and QG-enforced.
status: resolved
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [cefi, tardis, throughput, quota, throttling, backfill, big-finding, capacity-planning]
related:
  [
    cefi_tardis_throughput_collapse_350x_2026_07_17.md,
    cefi_shard_enumeration_blindspots_and_canonical_fetch_dependency_2026_07_18.md,
  ]
created: 2026-07-18
source:
  - Operator asked to re-measure a fresh backfill with the RX counter over ~2h and profile whether the collapse was
    bundles, instrument types, venues, or degradation over time. Operator also flagged that throttling is probably
    ACCOUNT-level rather than IP-level — this data confirms it.
assigned_vm: NA
assigned_role: data_engineering
priority: P0
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
parent_epic: cefi_master
execution_scope: local-only
drift_direction: advance-code
last_updated: 2026-07-18
depends_on: []
locked_by:
locked_since:
resolved_by: >-
  deployment-service@9c82335 (5 Tardis launchers + first gate) + @d259f61 (57 download-heavy launchers swept, gate
  generalised to check_backfill_vm_disk_provisioning.py) + @69dbf72 + @3803f3d. Validated live on
  cefi-queue-heavy-binancefutu-x17-20260718-184320: 11.1 MB/s sustained past 21.69GB, peak 18.15 MB/s, no cliff.
---

> **✅ RESOLVED 2026-07-18 — ROOT CAUSE WAS OUR DISK, NOT TARDIS.** This doc originally concluded that Tardis throttles
> the account after ~7-8 GB. That was WRONG, and so were the two follow-up theories (VM/session-scoped quota, then
> source-IP). The real cause is a `pd-standard` 50GB boot disk saturating. Fixed in deployment-service@d259f61 (57
> launchers) + @9c82335, enforced by `scripts/quality_gates/check_backfill_vm_disk_provisioning.py`. The original
> analysis is kept below the resolution section as a record of how a measurement-led investigation still went wrong four
> times.

## Resolution — measured, then validated

### The evidence that settled it

`iostat` on the degraded VM, while it was running at 2.4 MB/s:

```
sda  w/s=50.4  wkB/s=12188  w_await=1015ms  aqu-sz=51  %util=99.94
CPU: 93.5% idle, 6.2% iowait   RAM: 115GB free of 128, swap 0   disk 11% full, inodes 3%
```

The disk was 100% utilised with one full second of write latency and 51 requests queued, while the CPU idled and 115GB
of RAM sat unused. RAM pressure, disk fullness and GC are all excluded by those same numbers.

### Why it looked like a vendor quota

| Observation                                                | Read as a Tardis quota      | Actually                                         |
| ---------------------------------------------------------- | --------------------------- | ------------------------------------------------ |
| Cliff tracks cumulative VOLUME (~7.5GB), not time or venue | a bytes-based account quota | PD burst credits deplete by bytes written        |
| A fresh VM always starts fast again                        | a per-session/VM allowance  | a fresh disk has fresh burst credits             |
| ZERO HTTP 429s, only ConnectionTimeouts                    | an invisible throttle       | nobody was throttling us; writes were backing up |
| 6x concurrency changed nothing (7.67 vs 7.58 MB/s)         | an account-level ceiling    | the bottleneck was never concurrency             |
| An in-place source-IP swap changed nothing                 | quota is account-scoped     | the IP was never relevant                        |

Tardis serves `.csv.gz`, so ~2.4 MB/s of compressed RX becomes ~12 MB/s of decompressed/parquet writes (~5x). The whole
investigation measured RX and never asked whether the SINK could absorb it.

### Validation (VM `cefi-queue-heavy-binancefutu-x17-20260718-184320`, pd-balanced 250GB)

```
19:06  cum= 9.50GB  recent5=11.21 MB/s  peak=14.67
19:10  cum=12.79GB  recent5=13.91 MB/s  peak=14.73
19:14  cum=16.79GB  recent5=15.92 MB/s  peak=18.15
19:22  cum=21.69GB  recent5=11.16 MB/s  peak=18.15
```

Nearly 3x past the 7.5GB point where pd-standard died every time, with throughput intact. **11.1 MB/s sustained vs 2.36
MB/s = 4.7x**, and the peak clears the 15 MB/s target.

### What shipped

- **deployment-service@9c82335** — pd-balanced 250GB on the 5 Tardis launchers; first version of the gate; rotation
  supervisor hardened.
- **deployment-service@d259f61** — swept 57 download-heavy launchers (Tardis + Databento/TradFi + every `*backfill*`
  - every `*forward-poll*`); gate generalised + renamed to `check_backfill_vm_disk_provisioning.py`, now resolving
    indirect `--boot-disk-size="${BOOT_DISK_GB}GB"` forms; verified red-on-regression on both the type and size paths.
- **deployment-service@69dbf72** — dropped the superseded gate file.

### Two further bugs found on the way

1. **Manual VM delete is indistinguishable from SPOT preemption.** The shutdown-script emits the preemption signal, so
   the fleet relauncher (`scripts/recovery/relaunch_backfill_vm.py`) replays the launch params. Deleting a VM and
   launching a replacement produced TWO VMs 469ms apart (`...-181342` / `...-181344`, identical venues + data types),
   i.e. two source IPs on one Tardis account → **HTTP 403 `concurrent-IP-lock`, 1181 rejections, zero bytes**. The
   account recovered on its own once back to a single VM. `rotate-cefi-backfill-vm.sh` now waits `ADOPT_WAIT` and ADOPTS
   an auto-relaunched VM instead of racing it, and asserts cap-1 every cycle.
2. **`launch-legacy-bucket-migration-sharded.sh` referenced `${BOOT_DISK_GB}` with no assignment anywhere**, so it
   expanded to `--boot-disk-size=GB` and gcloud would have rejected the launch. Found by the new gate.

### Open follow-up

- ~65 non-backfill launchers (live/cron/utility) still specify no `--boot-disk-type`. They are not download-heavy so
  they are out of the gate's scope, but any that write sustained data should be reviewed.
- The `2.65x VM-rotation` workaround documented below is now **obsolete** — it treated the symptom. Rotation is retained
  only as a preemption-recovery path, not a throughput strategy.

---

## Original (WRONG) analysis — kept as a record

# Tardis account-level volume quota — ~7-8 GB, then ~2 MB/s

## Evidence (network-RX counter, not completion-derived)

| Run                   | Concurrency           | Cliff after | Pre-cliff  | Post-cliff |
| --------------------- | --------------------- | ----------- | ---------- | ---------- |
| baseline `...155131`  | 8 total (cap bug)     | ~7.2 GB     | 9-13 MB/s  | 2.33 MB/s  |
| optimised `...162137` | 32 non-book + 16 book | ~7.0 GB     | 10-14 MB/s | 1.96 MB/s  |
| earlier `...142025`   | 8 total               | ~8.6 GB     | 5-13 MB/s  | ~2.5 MB/s  |

The decisive observation is that the collapse happens **inside an unchanged workload**:

```
16:38  11.73 MB/s  bybit-spot  trades
16:41  13.96 MB/s  bybit-spot  trades
16:43   3.48 MB/s  bybit-spot  trades   <-- same venue, same data_type
16:46   1.15 MB/s  bybit       book_snapshot_5
```

CPU falls to 0.6-1.2 of 16 cores at the cliff (idle-waiting on the network), rss stays ~8.6 GB, and there are ZERO HTTP
429s, timeouts, upload failures or tracebacks in the run log. The client is healthy; the bytes simply stop arriving.

## Decisive A/B — 6x concurrency changed NOTHING

Two VMs, same queue, same day, profiled identically with the RX counter, at EQUAL sample size (n=17 one-minute windows
each):

| Configuration                                    | mean      | median    | max        |
| ------------------------------------------------ | --------- | --------- | ---------- |
| baseline — 8 concurrent slots (the cap bug)      | 7.67 MB/s | 9.62 MB/s | 12.92 MB/s |
| optimised — 32 non-book + 16 book (6x the slots) | 7.58 MB/s | 9.91 MB/s | 13.96 MB/s |

Statistically identical. The optimised VM also reached the ~7 GB cliff in the SAME ~16 min. If the client were the
constraint, 6x the in-flight downloads would have moved at least one of these numbers.

## Mechanism — connection timeouts, NOT HTTP 429

Post-cliff the run log carries **137 `ConnectionTimeoutError` to `s3.us-east-1.wasabisys.com` (datasets.tardis.dev's
storage backend) and ZERO HTTP 429 / TooManyRequests**. So the throttle is enforced by making connections slow or
unavailable rather than by returning an explicit rate-limit status. Two consequences:

- Nothing in our stack can detect it as throttling — there is no 429 to back off from — which is why it presented for a
  whole session as a mysterious "throughput collapse".
- **Worth raising with Tardis Support explicitly**: ask whether the account has a per-run/per-window volume allowance
  and whether it is signalled anywhere, because silent connection starvation is indistinguishable from a network fault
  at the client.

**Ruled out — connector exhaustion (checked, not assumed):** `connection_pool_size` is aiohttp's `limit_per_host` = 128,
and the download semaphore caps real concurrency at 32 + 16 = 48, comfortably under it. Note the run log's "requests
minus successes" is QUEUE DEPTH, not open connections — the request line is emitted BEFORE the semaphore is acquired —
so figures like "264 in flight" describe the backlog, not sockets.

## What this rules out

- **NOT venue-specific** — bitget-futures `book_snapshot_5` ran 12.9 MB/s while bybit `book_snapshot_5` ran 1.7 MB/s
  later in the same run, but bybit `trades` ran 11.4 MB/s in between.
- **NOT data_type / bundle-specific** — both `trades` and `book_snapshot_5` measured fast pre-cliff and slow post-cliff.
- **NOT client concurrency** — 6x more in-flight slots changed neither the cliff threshold (~7 GB) nor the time to reach
  it (~16-17 min).
- **NOT IP-level** — a single VM (one IP) throughout; the collapse is mid-run on that one IP.

## What this means for capacity planning

The headline ~12 MB/s is only available for the first ~7 GB of a run. **Sustained throughput is the post-cliff ~2
MB/s**, so 15-20 TB is on the order of MONTHS at current account terms, not the ~12 days implied by peak-rate
arithmetic. Any ETA quoted from a short measurement window will be wrong by ~6x — this is exactly how four successive
over-claims were produced on 2026-07-18 before the RX counter was used (see the measurement-discipline section added to
the `data-pipeline-check-*` skills).

## Open questions (need a longer observation than this session allowed)

1. **Does the quota reset, and on what window?** If it is ~7 GB/hour, a burst-then-idle schedule could sustain a higher
   average than one long-running VM. If daily, it is a hard ceiling.
2. **Is the pre-cliff ~12 MB/s also an account ceiling?** Both runs plateaued there despite 8-vs-48 slots, which
   suggests yes.
3. **Is it bytes or requests?** Distinguishable by running one large-shard-only and one small-shard-only VM and
   comparing where each cliffs.

## ROTATION TEST — the throttle is VM/SESSION-scoped, NOT account-scoped (2026-07-18)

Decisive experiment: delete the throttled VM and launch a fresh one (new IP, SAME account, still exactly ONE VM so cap-1
is never violated), ~15 min after the previous VM had collapsed to 1-2 MB/s.

```
17:03   1.16 MB/s   (boot ramp)
17:04   6.03 MB/s
17:05  13.30 MB/s   <-- FULL SPEED RESTORED
17:06  10.33 MB/s
```

The fresh VM immediately regained full throughput. **The quota therefore attaches to the VM / session / IP, not to the
account**, which means it IS addressable on our side — contrary to this doc's original "commercial, not technical"
conclusion, which is hereby corrected.

### What rotation buys (MEASURED, not estimated)

Per-minute RX over the rotation VM's full life (n=24):

| Phase                  | n   | Mean          | Volume   |
| ---------------------- | --- | ------------- | -------- |
| Pre-cliff (min 0-15)   | 16  | 7.60 MB/s     | 7.52 GB  |
| Post-cliff (min 16-23) | 8   | **2.36 MB/s** | +0.91 GB |

Peak 13.30 MB/s at min 3. The pre-cliff mean is dragged down by the boot ramp and two zero-sample gaps, so the true
steady pre-cliff rate is higher than 7.60.

| Strategy                    | Behaviour                                         | Effective sustained rate |
| --------------------------- | ------------------------------------------------- | ------------------------ |
| One long-running VM (today) | 7.52 GB, then 2.36 MB/s indefinitely              | **2.36 MB/s**            |
| Rotate at ~6.5 GB           | 7.52 GB per 20 min cycle (16 productive + 4 boot) | **6.26 MB/s**            |

**2.65x**, using only scheduling — no extra VMs, no cap-1 violation, no change to the fetch path. The cliff is at **7.52
GB / 16 min**, so the shipped `--rotate-gb 6.5` default fires just before it.

**It does NOT reach 15 MB/s.** The pre-cliff peak is ~13 MB/s and only for the first ~7.5 GB, so ~6.3 MB/s is the
realistic ceiling for rotation. A sustained 15 MB/s still requires better account terms.

### Implementation — SHIPPED

`deployment-service/scripts/vm/rotate-cefi-backfill-vm.sh` (deployment-service@cb347ac, fixes @1f483b5). Supervises the
single live VM and rotates on EITHER trigger: cumulative RX >= `--rotate-gb` (default 6.5) or sustained rx <
`--floor-mbps` (default 4) for 3 ticks, so it still fires if the threshold moves. Also relaunches on SPOT preemption. It
replays the rotated VM's own `VM_START_DATE`/`VM_VENUE`/`VM_YEARS` rather than hardcoding them, and enforces its
`--cycles` budget BEFORE the delete so it can never exit between delete and relaunch and strand the backfill.

**NOT yet armed on live infra** — it deletes and relaunches VMs unattended, so it wants an operator go-ahead:

```
cd deployment-service && ./scripts/vm/rotate-cefi-backfill-vm.sh --cycles 6   # ~2h, leaves a VM running
```

A mid-shard rotation is equivalent to a SPOT preemption, which the idempotent shard design already handles, so no data
is lost. Boot is ~4 min of each 20 min cycle (20% overhead); a pre-baked image would push the effective rate toward ~7
MB/s.

## Recommended next steps

- **Implement VM rotation** — the measured 2.65x, cap-1-safe. Script shipped above; needs arming.
- **Still worth raising with Tardis Support**: the throttle is invisible (connection starvation, no 429), and confirming
  the per-session allowance would let the rotation threshold be set precisely rather than empirically. A better account
  tier remains the only route to a sustained 15 MB/s.
- Instrument every backfill VM with the RX counter (`deployment-service/scripts/vm/measure-vm-throughput.sh`) so the
  cliff is visible in normal operation rather than rediscovered.
- Re-baseline the CeFi backfill ETA off the post-cliff rate until the quota question is answered.
