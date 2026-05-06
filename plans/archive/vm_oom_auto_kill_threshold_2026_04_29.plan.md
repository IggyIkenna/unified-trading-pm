---
title: "VM OOM Auto-Kill Threshold + Manifest Mark-Failed"
priority: P2
status: active
owner: agent
created: 2026-04-29
type: feature
epic: none
completion_gates:
  code: C3
  deployment: D2
  business: none
repo_gates:
  - repo: deployment-service
    code: C2
    deployment: D0
  - repo: market-tick-data-service
    code: C0
    deployment: D0
  - repo: unified-trading-pm
    code: C0
    business: B0
depends_on: []
isProject: false
---

## Context

The 2026-04-29 364-VM CeFi probe (`run-ts=20260429-112352`) deterministically OOM-killed ~200 VMs (rc=137 from systemd
OOM-killer) on the 7.6M-row DERIBIT BTC-PERPETUAL `book_snapshot_5` shard at e2-standard-8. The OOMs were silent from
the orchestrator's perspective:

- Python's `atexit` flush + `DEPLOYMENT_FAILED` archive **do NOT fire** on SIGKILL — the process never gets a signal
  handler chance.
- The wrapper's `EXIT_STATUS` file is also never written (rc captured in the wrapper requires the workload to return).
- `run.log` ends mid-sentence; manifest rows for the shard remain in their pre-failure state (`captured` from prior runs
  OR no manifest row at all).
- Only signal: kernel logs in Cloud Logging (`textPayload=~"OOM"` filtered by VM name).

Observed cost: ~200 VMs ran for 30-90 minutes each before being OOM-killed, all on a deterministic shard, all wasting
fleet-hours. Operator noticed only after manual `gcloud compute instances list` showed the OOM rate, ~1h after launch.

**v2 had this**: `unified-trading-deployment-v2/api/main.py:120-145` parsed serial-console logs for SERVICE_EVENT + OOM
patterns and auto-killed VMs after `OOM_KILL_THRESHOLD=5` repeated OOM messages (`api/settings.py:81`). v2's threshold
was tuned for deployment-orchestrator-side memory pressure (multi-instance), not workload OOMs — but the pattern (poll
kernel logs, kill VM, mark its shards `attempted_failed`) is the right shape for our use case.

## What we want

A separate per-rollout watcher process (cron-driven, NOT inline in the launcher) that:

1. Polls Cloud Logging for OOM kernel events tagged with `run-ts=<launcher-run-ts>` (since launcher labels every VM with
   this).
2. For each VM with ≥1 OOM event in the last 5 minutes:
   - Captures the VM's metadata (`VM_START_DATE` / `VM_END_DATE` / `VM_ASSET_GROUP`) so we know what shards it was
     processing.
   - Calls `gcloud compute instances delete --quiet` to halt the burning VM.
   - Updates the availability manifest: rewrites every shard row in the VM's date range from `captured` (if it was ever
     set) to `attempted_failed` with `error_reason="VM_OOM_KILL run-ts=<run-ts> vm=<vm-name>"`, `attempted_at=now()`.
     The next rollout (or auto-retry pass) will retry these shards.
   - Optionally, if the rollout has at least one machine-tier headroom available, re-launch a single replacement VM at
     the next-tier-up machine (e2-highmem-8 → e2-highmem-16) for the same date range. Defer this decision; manual retry
     is acceptable for v1.

A single OOM is sufficient signal: Python is dead at that point, there's no recovery within the same VM.

## Pre-audit

| Repo / file                                                                        | Why                                                                                                         |
| ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `deployment-service/scripts/vm/launch-cefi-massive-rollout.sh`                     | Already labels every VM with `labels.run-ts=<ts>` ✓ — no launcher change needed for the watcher to find VMs |
| `deployment-service/deployment_service/vm/`                                        | New module `oom_watcher.py` lives here                                                                      |
| `deployment-service/scripts/vm/oom-watcher.sh`                                     | Convenience wrapper for cron / one-off invocation                                                           |
| `unified-trading-library/unified_trading_library/manifest_writer.py`               | `record_failed(row_key=, error=, attempted_at=)` already exists from manifest v5 — no UTL change needed     |
| `unified-api-contracts/unified_api_contracts/external/...`                         | `classify_venue_error()` already exists — `VenueErrorCode.VM_OOM_KILL` may need to be added (confirm)       |
| `market-tick-data-service/market_tick_data_service/engine/shard_memory_profile.py` | Watcher consults this to suggest the next-tier machine for retry                                            |

## Phased execution DAG

```
Phase 1 — Watcher core (P0, ~1d engineering)
   1.1 Add VenueErrorCode.VM_OOM_KILL to UAC if missing
   1.2 Implement oom_watcher.py:
       - poll Cloud Logging for OOM events by run-ts label
       - dedupe per VM (one delete + one manifest mark per VM)
       - delete the VM via gcloud
       - rewrite manifest rows for the VM's date range to attempted_failed
   1.3 Unit tests with fake Cloud Logging client + fake gcloud + fake manifest writer
   1.4 Integration test on a deliberately-OOM'd VM (deploy a tiny e2-standard-2 + force-load 8GB into RAM)
              ─────────── QG: oom_watcher detects + marks + kills ───────────
                                       ↓
Phase 2 — Operator tooling (P1, ~half day)
   2.1 oom-watcher.sh wrapper that takes --run-ts as arg, polls every 60s,
       prints a structured summary every poll cycle
   2.2 Optional cron entry in deployment-service that auto-launches a watcher
       when a new run-ts is detected with >=10 VMs (so probe runs auto-watch)
              ─────────── QG: dry-run on completed run-ts shows the OOMs ─────
                                       ↓
Phase 3 — Auto-retry at next-tier machine (P2, deferred)
   3.1 Watcher consults shard_memory_profile, picks next tier,
       relaunches a single replacement VM with the same date range
   3.2 Cap the retry chain at 1 (second OOM at next-tier means a real bug,
       not a sizing miss — alert operator)
              ─────────── QG: synthetic OOM auto-recovers at higher tier ─────
```

## Success criteria

- **Phase 1**: A test run that deliberately OOM'd 5 VMs auto-detects all 5, deletes them within 60-90s, and the manifest
  shows `capture_status=attempted_failed` for every affected shard.
- **Phase 2**: A `oom-watcher.sh --run-ts <ts>` invocation prints a structured summary every minute. Tested by replaying
  the 2026-04-29 probe's OOM signals.
- **Phase 3** (deferred): A synthetic OOM at e2-standard-8 auto-launches replacement at e2-highmem-8 and the replacement
  completes successfully.

## What we are NOT doing

- Not adding inline OOM detection to the launcher itself. The launcher already exits after spawning all VMs — it's not
  running while VMs are being killed. A separate watcher process is the right shape.
- Not re-architecting the orchestrator to be multi-instance. v2's heartbeat / multi-instance lock pattern was for
  orchestrator API resilience, not workload OOMs. Single-instance deployment-api is fine.
- Not changing the launcher's batching / quota / round-robin logic. Those work.
- Not adding ML / heuristic prediction of which shards will OOM ahead of time — `shard_memory_profile.py` is the
  proactive sizing path; this plan is about reactive cleanup.

## Verification

End-to-end check:

1. Launch a deliberate-OOM probe: 5 VMs at e2-standard-2 (8 GB) with a workload that allocates 16 GB. They will all OOM.
2. Start `oom-watcher.sh --run-ts <ts>` in another terminal.
3. Within 60-120s, all 5 VMs should be `TERMINATED` (deleted by watcher), and the manifest should show 5x
   `attempted_failed` rows with `error_reason="VM_OOM_KILL ..."`.
4. Re-run the same shard set with the watcher's recommended next-tier machine — should complete successfully.

## Owner / when

P2 — not blocking the current rollout (which is healthy at e2-highmem-16, 0 OOMs observed). Pick up after the current
rollout completes (~2h ETA at the time this plan was written, 2026-04-29 ~15:30Z). Reference incident:
`run-ts=20260429-112352` 364-VM probe.
