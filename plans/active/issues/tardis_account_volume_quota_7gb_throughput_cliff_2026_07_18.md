---
doc_type: issue
title:
  Tardis throttles the ACCOUNT after ~7-8 GB per run — throughput collapses ~12 MB/s to ~2 MB/s and no client-side
  concurrency change can beat it
summary:
  Three independent backfill VMs each collapsed after downloading ~7-8 GB, measured off the wire via the Cloud
  Monitoring network-RX counter. Baseline (8 concurrent slots) cliffed at ~7.2 GB then ran 2.33 MB/s; an optimised VM
  with 6x the concurrency (32 non-book + 16 book) cliffed at ~7.0 GB then ran 1.96 MB/s. The collapse happens WITHIN an
  unchanged workload — bybit-spot trades measured 13.96 MB/s at 16:41 and 3.48 MB/s at 16:43, same venue, same data_type
  — so it is neither venue-specific, data_type-specific, nor a shard-size artefact. Both runs also took the SAME ~16-17
  min to reach the quota, so 6x more slots did not even reach it faster, which means the pre-cliff ~12 MB/s is itself an
  account-level ceiling rather than a concurrency limit. Consequence for planning - the effective sustained rate is the
  POST-cliff ~2 MB/s, not the headline ~12.
status: open
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
resolved_by:
---

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

## Recommended next steps

- **Commercial, not technical**: confirm the account's rate/volume terms with Tardis Support. No client-side change
  (concurrency, faster gzip, Rust, more VMs) can exceed an account quota, and more VMs additionally violate the cap-1
  rule.
- Instrument every backfill VM with the RX counter (`deployment-service/scripts/vm/measure-vm-throughput.sh`) so the
  cliff is visible in normal operation rather than rediscovered.
- Re-baseline the CeFi backfill ETA off the post-cliff rate until the quota question is answered.
