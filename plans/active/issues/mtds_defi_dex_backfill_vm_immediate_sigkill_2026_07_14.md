---
doc_type: issue
title: mtds-dex-pools/dex-swaps backfill VMs die immediately or hang silently on real launch — root cause unresolved
summary:
  "Backfilling the 4 newly-wired DeFi dex protocols (velodrome_v2/trader_joe_v2/uniswap_v4/uniswap_v2,
  mtds_defi_dex_zero_capture_protocols_2026_07_14.md) via launch-mtds-dex-{pools,swaps}-backfill-vm.sh consistently
  fails: on SPOT provisioning the Python process gets SIGKILL'd (exit 137) within ~10-20s of starting, right after
  'TheGraph key pool loaded' / handler init, at ~10% memory (ruling out OOM); on --on-demand the process launches
  (confirmed via serial console) but then produces zero further output — no log lines, no heartbeat, no deployment
  registration — for 6+ minutes, and SSH to the VM itself times out with no response. Reproduced 3 times (2x SPOT, 1x
  on-demand). Root cause NOT found; kill-switch, GCP-level preemption, and OOM were all ruled out with real evidence."
status: open
nature: notes
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [vm-launcher, backfill, dex-pools, dex-swaps, infra, sigkill, hang]
related: [../mtds_defi_dex_zero_capture_protocols_2026_07_14.md]
created: 2026-07-14
parent_epic: infrastructure_master
assigned_vm:
resolved_by:
source:
  "Discovered 2026-07-14 attempting the real historical backfill for the 4 newly-wired DeFi dex protocols, per operator
  instruction to launch backfill VMs after confirming MVP scope + single write path."
priority: P2
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
