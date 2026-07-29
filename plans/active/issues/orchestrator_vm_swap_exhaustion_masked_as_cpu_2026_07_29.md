---
doc_type: issue
title: >-
  i-0c9b283b31d6b5ca7 was measured 100% swap-exhausted + thrashing (65.9% iowait) while CPU sat at a moderate 26% — a
  sharper diagnosis than the standing crisis doc's "CPU/disk contention" framing, now visible on the AO dashboard going
  forward
summary: >-
  While investigating the fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md-blocked agent-orchestrator
  promote PR on 2026-07-29, the operator caught a real discrepancy: the AO dashboard's Host Resources panel showed CPU
  26%, which contradicted a claim (mine) that the host was severely oversubscribed based on a raw load-average reading
  (16.4/29.4/39.7). Direct measurement (vmstat/top on i-0c9b283b31d6b5ca7) resolved it: swap is 100% exhausted
  (16384MB/16384MB used, actively thrashing at 14-18MB/s continuous swap-in/out) and %wa (iowait) is 65.9% — the load
  average was almost entirely processes blocked on I/O from swap thrashing, not CPU-runnable work. CPU itself genuinely
  is fine. This refines (does not contradict) the standing crisis doc's "~20 self-hosted runners competing for 16 vCPUs"
  structural diagnosis: the proximate mechanism is that many runner+agent processes are collectively exhausting the
  host's 64GB RAM + 16GB swap, not fighting over CPU cycles per se. The standing doc's own 2026-07-28 ~23:08 Progress
  Log entry already caught "swap 14/15GB" in passing on instruments-service's investigation -- this doc's contribution
  is a fresh, fuller measurement (100% now, not 14/15) proving it's a still-recurring condition a day later, plus
  closing the actual gap that made it hard to see: the dashboard now surfaces swap% directly (shipped this session,
  agent-orchestrator@4742ce2), so the next person doesn't need to SSM in and run vmstat/top to catch this.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [runner-capacity, memory-pressure, swap, observability, host-resources, i-0c9b283b31d6b5ca7]
related:
  [
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
    /plans/active/issues/orchestrator_vm_disk_io_contention_runner_burst_2026_07_28.md,
  ]
created: 2026-07-29
last_updated: 2026-07-29
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source: >-
  Operator caught a real contradiction between a claimed "CPU oversubscription" diagnosis and the AO dashboard's own
  CPU% reading (26%), and asked for better visibility ("its not just about how many tasks its the cpu usage that matters
  some tasks are I.O heavy and wait heavy") rather than accepting the hand-wavy load-average-only explanation.
resolved_by:
locked_by:
locked_since:
---

# Swap exhaustion, not CPU contention, is the proximate mechanism right now

## What's confirmed (measured live, 2026-07-29 ~01:00 UTC, i-0c9b283b31d6b5ca7)

```
free -m:  Mem 31551 total / 27767 used / 275 free   Swap 16383 total / 16383 used / 0 free
top:      %Cpu(s): 4.5 us, 17.9 sy, 9.0 ni, 2.7 id, 65.9 wa   load average: 40.45, 38.24, 37.97
vmstat:   si/so (swap in/out) 11804-14880 / 12540-18433 KB/s, continuous across 3 samples
          procs b (uninterruptible sleep) 37-49, r (runnable) only 5-8
```

Swap is **completely exhausted** (0 free of 16GB) and actively thrashing. Load average of ~38-40 on a 16-core box looks
like ~2.5x CPU oversubscription at a glance, but `%wa` (65.9%) shows most of that is processes blocked on I/O
(swap-driven paging), not CPU-runnable work — genuine CPU usage (`us`+`sy`+`ni`) is only ~31%. This matches the AO
dashboard's own CPU% tile (26%, confirmed via a fresh operator screenshot) — the dashboard was right, my initial
load-average-based claim was the wrong inference.

**This is not a one-off.** The standing crisis doc's own 2026-07-28 ~23:08 UTC entry (instruments-service investigation)
already noted "swap 14/15GB" in passing while diagnosing a different symptom. Today's measurement (0/16 free, i.e. worse
— fully exhausted, not just high) confirms the memory-pressure component is a persistent, recurring state of this host,
not a transient spike.

## Relationship to the standing crisis doc

`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` (P0/P1, actively being worked by multiple slots)
correctly identifies the structural cause — ~20+ self-hosted runner processes registered on one 16-vCPU/64GB host
(`i-0c9b283b31d6b5ca7`) that never had per-repo capacity planned before the allowlist rollout. This doc does not dispute
that. It refines the **proximate mechanism**: the doc's "What I found" section frames symptoms as "CPU/disk contention";
the measurement here shows the dominant resource actually being exhausted right now is memory (RAM + swap), which
manifests as I/O wait, not CPU saturation. Fixing runner _count_ would still fix this (fewer concurrent processes = less
combined memory footprint) — this doesn't change the crisis doc's recommended remedy, it sharpens what's actually being
measured when someone checks in on the host. **Filed as a separate doc, not appended to the standing one, because that
doc is at its 1000-line hard cap and is being actively written to by multiple concurrent slots** — annotating in place
risked both a line-cap violation and a collision.

## What's fixed

`agent-orchestrator@4742ce2` (shipped 2026-07-29, this session) adds `swap_used_bytes`/
`swap_total_bytes`/`swap_percent` to `HostResources` (`server/host_resources.py`, `/proc/meminfo`'s
`SwapTotal`/`SwapFree`) and a new "Swap" tile on the dashboard's Host Resources panel, sharing the existing iowait
tile's lower-threshold colour scale (swap climbing at all is already abnormal, unlike RAM/disk running high being
normal). Manually dispatched `deploy-dashboard.yml` against `live-defi-rollout` (`workflow_dispatch`, target=prod) to
get this live without waiting on the stuck LDR→main promotion the crisis doc itself is about. Full backend + dashboard
test coverage, full `quality-gates.sh` green.

## Todos

- [ ] [BACKEND] P3. Once the runner-capacity crisis's remedy (whatever the standing doc's owners land on — reduced
      runner count, more RAM, per-runner memory limits/cgroups) ships, spot-check swap% on the dashboard to confirm it
      actually returns to near-0% and stays there — the metric now exists to make that verification trivial instead of
      another manual SSM session.
- [ ] [REVIEW] P3. Consider whether the crisis doc's "What I found" section is worth a one-line correction the next time
      someone touches that file for other reasons (swap/memory, not just CPU/disk) — not worth a dedicated edit on its
      own given the line cap, but cheap to fold in opportunistically.

## Codex SSOTs

- None directly own host-resource-panel metrics. No new contract established here — an existing pattern (the 2026-07-28
  iowait addition) extended with one more metric.
