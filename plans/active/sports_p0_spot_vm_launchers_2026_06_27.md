---
doc_type: plan
title: "Sports P0-spot — force SPOT/preemptible on all sports VM launchers"
summary:
  "Add SPOT/preemptible support to all 8 sports VM launchers to cut compute costs for idempotent backfill workloads."
nature: process
stage: [data-ingestion]
repos: [deployment-service]
scope: [engineer, admin]
tags: [sports, infra, spot-vm, preemptible, vm-launchers, cost-optimisation]
related: []
created: 2026-06-27
parent_epic: sports_master
priority: P0
status: active
assigned_vm: planning
assigned_role: infra
drift_direction: advance-code
last_updated: 2026-06-27
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.6
locked_by: live-defi-rollout
locked_since: 2026-06-27
depends_on: []
related_plans:
  - plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md
asset_group: cross-asset
---

> **Coordinator**: `sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` (Phase 0). Forces every sports VM the
> plan set launches to be **spot/preemptible** (cost). This is **infra-craft** (`assigned_role: infra`, Sonnet/medium) —
> it edits the deployment-service launcher scripts, which the `data_engineering` backfill plans then USE. It is a
> Phase-0 prereq for every VM-launching child (P1a/b/c/d, P2a/b/c/d). One agent, one repo (`deployment-service`).

# Sports P0-spot — force SPOT on all sports VM launchers

## Why (and the current gap)

The operator wants all sports backfill/compute VMs on **spot** — the cheap instances the cloud can reclaim and kill at
any moment (preemptible) — to cut cost. **None of the 8 sports launchers support it today** (`grep -c preemptible` = 0
across `launch-api-football-backfill-vm.sh`, `launch-sfi-backfill-vm.sh`, `launch-understat-backfill-vm.sh`,
`launch-transfermarkt-backfill-vm.sh`, `launch-openmeteo-backfill-vm.sh`, `launch-footystats-backfill-vm.sh`,
`launch-features-sports-parallel-backfill-vm.sh`, `launch-sports-scheduler-vm.sh`). The flag must be **added + defaulted
ON for sports**, following the existing repo pattern in `launch-mtds-dex-pools-backfill-vm.sh` /
`launch-mtds-gas-fees-backfill-vm.sh` (`PREEMPTIBLE=true → --preemptible --no-restart-on-failure` on the
`gcloud compute instances create` call). Modern equivalent:
`--provisioning-model=SPOT --instance-termination-action=DELETE`.

Spot is safe here because sports backfills are **idempotent + skip-existing** (the `data_engineering` craft north-star):
a reclaimed VM relaunches and resumes where it left off. The one real risk is the fleet monitors reading a spot
**preemption** as a silent failure (`DP_VM_GONE_NO_CAPTURE`) — so preemption must be made distinguishable from a crash.

## Codex SSOTs

- `codex/05-infrastructure/vm-tarball-deployment.md` — VM launcher conventions; `VM_PREFIX_TO_BUCKET` /
  `lifecycle_class`
- `codex/05-infrastructure/deployment-observability.md` — `DP_VM_GONE_NO_CAPTURE` / exit-code + heartbeat monitors (must
  not false-fire on preemption)

## Todos

- [x] [INFRA] P0. **Add forced SPOT provisioning to the 7 sports backfill/compute launchers.** Add a `PREEMPTIBLE`
      switch defaulting **ON for sports** (`--provisioning-model=SPOT --instance-termination-action=DELETE`, or the
      repo's `--preemptible --no-restart-on-failure` form) to: `launch-api-football-backfill-vm.sh`,
      `launch-sfi-backfill-vm.sh`, `launch-understat-backfill-vm.sh`, `launch-transfermarkt-backfill-vm.sh`,
      `launch-openmeteo-backfill-vm.sh`, `launch-footystats-backfill-vm.sh`,
      `launch-features-sports-parallel-backfill-vm.sh`. Provide an explicit `--on-demand` override for the rare case
      spot capacity is unavailable. **Gate**: each launcher's `gcloud compute instances create` carries the SPOT flag by
      default; a dry-run prints it; a real launched sports backfill VM shows `scheduling.provisioningModel=SPOT` via
      `gcloud compute instances describe`. ✅ — deployment-service@feb84bb (all 7 backfill launchers; `--on-demand` escape hatch; `--provisioning-model=SPOT --instance-termination-action=DELETE` pattern).
- [x] [INFRA] P0. **Sports-scheduler daemon on SPOT with auto-relaunch.** Add SPOT to `launch-sports-scheduler-vm.sh`;
      because it is a long-lived daemon, ensure a preemption triggers a relaunch (the singleton-lock + GCS
      `sports_scheduler_state/` make restart safe — it resumes its tier cadence). **Gate**: the scheduler VM launches
      SPOT; a simulated/observed preemption results in a fresh scheduler VM re-acquiring the singleton lock and
      continuing from GCS state (no tier double-fire, no gap > one poll interval). ✅ — deployment-service@5d24b3c (`--provisioning-model=SPOT --instance-termination-action=DELETE --no-restart-on-failure`; preemption detected via GCE metadata, shutdown-script relaunches a fresh scheduler VM with `nohup gcloud … --force` within the 30s preemption window).
- [ ] [INFRA] P0. **Make the fleet monitors preemption-aware (no false `DP_VM_GONE_NO_CAPTURE`).** A spot preemption
      self-deletes the VM the same way an OOM does — the exit-code / meta watcher must classify a GCE **preemption
      event** (`gcloud compute operations` `compute.instances.preempted`, or the `--instance-termination-action` signal)
      as a benign relaunch, not a CRITICAL silent-failure alert (R5 — no false errors). **Gate**: a preempted sports
      backfill VM produces NO `DP_VM_GONE_NO_CAPTURE` CRITICAL; instead a benign `preempted→relaunch` INFO;
      `quality-gates.sh` green with a unit test for the preemption-classification path.
- [ ] [QG] P0. **Ship via quickmerge.** `quality-gates.sh` green on `deployment-service`; shipped
      `--agent --files '<the launcher scripts + monitor change>'`. **Gate**: `.qg_last_passed_sha == HEAD`; quickmerge
      landed on `live-defi-rollout`.

**Full-execution criterion**:

- ✅ Every sports launcher defaults to SPOT + the monitors are preemption-aware, verified on a real launch.
  - **What ran**: a single real sports backfill VM launched via the updated launcher.
  - **Verification**: `gcloud compute instances describe <vm> --format='value(scheduling.provisioningModel)'` → `SPOT`;
    a forced/observed preemption produces a relaunch + zero false CRITICAL alert (paste both into the Progress Log).

## Success criteria

- All 8 sports launchers default to SPOT (with an `--on-demand` escape hatch); preemption is safe (idempotent resume)
  and does NOT raise a false `DP_VM_GONE_NO_CAPTURE` (preserves R5 alert-zero).

## Dependencies

- **Upstream**: none (Phase 0).
- **Blocks**: every VM-launching child — P1a, P1b, P1c, P1d, P2a, P2b, P2c, P2d (they launch via these launchers, so
  SPOT must be the default first).

## References

- `deployment-service/scripts/vm/launch-mtds-dex-pools-backfill-vm.sh` — the existing
  `--preemptible --no-restart-on-failure` pattern to mirror
- `codex/05-infrastructure/deployment-observability.md` — the monitor contract this must not regress
