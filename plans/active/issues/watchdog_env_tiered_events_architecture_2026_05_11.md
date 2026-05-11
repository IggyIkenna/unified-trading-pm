---
title: "Watchdog architecture for env-tiered events buckets (1 watchdog reads 3 OR 3 per-env)"
created: 2026-05-11
author: ikenna-slot8
source:
  - plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md Q7(c)
  - deployment-service/scripts/vm/vm_zombie_watchdog.py
  - CLAUDE.md "No fire-and-forget VM launches" rule (events bucket SSOT)
locked_by: live-defi-rollout
locked_since: 2026-05-11
---

# Watchdog architecture for env-tiered events buckets

> **Severity**: P1 — follow-up; not blocking Phase 2.6 cutover 2026-05-15→05-19.
> **Blast radius**: `vm_zombie_watchdog.py` + events-bucket consumer surface (deployment-api event-status reads,
> unified-events-interface UI, every service that calls `log_event`).
> **Suggested owner**: deployment-service maintainer; can spawn from any Ikenna or Harsh slot.

## What I found

Operator decision 2026-05-11 PM resolved Q7(c) of `bucket_name_ssot_canonicalisation_2026_05_10.md` — **events bucket
goes env-tiered** (option c-i: `gs://{pid}-events-{env}/events/{service}/...` per env). The decision unblocks the
bucket-SSOT migration but leaves an open watchdog architecture question:

[`deployment-service/scripts/vm/vm_zombie_watchdog.py`](../../deployment-service/scripts/vm/vm_zombie_watchdog.py)
today reads from a single `{pid}-events` bucket. After Phase 2.6 cutover, three env-tiered events buckets exist
(`{pid}-events-prod` / `-staging` / `-dev`) and the watchdog must decide:

- **(i) Single watchdog reads all 3 env buckets concurrently** — one VM, one Python process, fans 3 GCS list streams.
  Simpler ops (one watchdog to launch/monitor); risk: throughput ceiling if event volume × 3 exceeds the machine's
  list_blobs budget (currently `e2-standard-2` with `HTTP_POOL_SIZE=2*workers`).
- **(ii) Per-env watchdog VMs (3 total)** — one watchdog per env. Cleaner isolation (staging burst doesn't starve prod
  monitoring); operational cost ~3× (3 VMs, 3 dict-relaunch cycles, 3 sets of events to operator).

## Why it matters

- **VMs invisible to watchdog = silent money burn** per CLAUDE.md "VM Naming Convention" rule + the 2026-05-05 incident
  (5 prefixes silently zombied for hours before manual detection).
- **Throughput uncertainty** — staging + dev are not in active use today; per-env event volume post-cutover is unknown.
- **Operator direction 2026-05-11 PM**: *"depends on throughput"* — needs data, not a guess.

## Recommended decision

**Sequence**:
1. **Phase 1 (this issue)**: ship watchdog architecture as option (i) — single watchdog with multi-bucket fan-in.
   Lower-cost default; easier rollback if throughput proves insufficient.
2. **Phase 2 (post-cutover)**: instrument watchdog for `list_blobs/sec` per bucket + max-event-age-detection latency.
   If watchdog stays under ~50% throughput headroom across all 3 envs for 7 days continuous, lock option (i) as final.
3. **Phase 3 (only if needed)**: split to option (ii) — per-env watchdog VMs. Code change: per-env launcher
   (`launch-vm-zombie-watchdog-{env}.sh`), per-env dict scoping (watchdog Python reads `VM_PREFIX_TO_BUCKET_<ENV>`
   subset), per-env shutdown coordination.

**Why option (i) first**: single-watchdog is the smaller code change (~30 LOC to add multi-bucket loop) + the only
operational unknown is throughput which we'll measure. Option (ii) is the bigger rebase (per-env launcher + dict
sharding + cross-env event correlation if any VM straddles envs).

## Cross-references

- Bucket-SSOT plan Q7(c): `bucket_name_ssot_canonicalisation_2026_05_10.md` § "Open questions Q7"
- CLAUDE.md "No fire-and-forget VM launches" rule (events bucket SSOT)
- CLAUDE.md "VM Naming Convention" rule (watchdog dict requirement)
- Phase 2.6 cutover window: 2026-05-15→05-19 (`code_freeze_migrate_backfill_sequencing_2026_05_10.md` GAP-2.4.B/C/D)

## Resolution status

🟡 OPEN — awaiting Phase 2.6 cutover (events bucket migrates first) + watchdog throughput instrumentation. Pick up
in next-cycle work-split after Phase 2.6 ships.
