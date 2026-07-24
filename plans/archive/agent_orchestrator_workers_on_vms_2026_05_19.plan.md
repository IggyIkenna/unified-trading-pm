---
doc_type: plan
title: agent-orchestrator workers on VMs (asymmetric Ikenna+Harsh topology)
summary:
status: superseded
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator, deployment-service]
scope: [engineer, admin]
tags: []
related: []
created: "2026-05-22"
parent_epic: orchestrator_master
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 3.2
locked_by: live-defi-rollout
locked_since: 2026-05-19
archived: 2026-05-22
archived_by: slot-7
superseded_by: plans/active/epic_vm_fleet_commissioning_2026_05_21.md
---

> **SUPERSEDED 2026-05-22** — asymmetric Ikenna VM + Harsh PC topology replaced by 10-VM fleet (1 planning VM + 9 epic
> VMs + 1 orchestrator VM). All VMs run orchestrator on port 8026. Open deferred items migrated to
> `plans/active/epic_vm_fleet_commissioning_2026_05_21.md` Deferred section.

# Agent-Orchestrator Workers on VMs

Move agent-orchestrator workers from laptop tmux-spawn to dedicated GCE VMs (asymmetric: Ikenna-primary VM +
Harsh-backup PC). Backend ssh-spawns into assigned worker box. Required before Cloud Run prod cutover (Harsh laptop
nginx shutdown). Also includes worker-liveness kicker daemon + preflight script shipped.

Codex SSOTs: `/codex/05-infrastructure/agent-orchestrator-worker-topology.md` (to be created at Phase 6) ·
`/codex/04-architecture/agent-orchestrator-overview.md`

---

## Pre-Phase — Worker liveness kicker (shipped)

- [x] [INFRA] P0. `ReadWritePaths=/tmp` added to `scripts/orchestrator.service` template + live unit.
      (agent-orchestrator)
- [x] [SCRIPT] P0. `scripts/worker-host-preflight.sh` — idempotent: claude theme/onboarding flags, per-worktree
      folder-trust, Claude CLI verification.
- [x] [DOC] P0. `docs/WORKER_SPAWN_PREREQUISITES.md` — the four gates + `nsenter` diagnostic + provisioning steps.
- [x] ✅ [AGENT] P0. `server/worker_liveness.py` `WorkerLivenessKicker` daemon thread — classifies stale/crashed/blocked
      workers; emits Slack notification via Phase 2 Block Kit.

## Phase 1 — Confirm asymmetric design

- [ ] [AGENT] P1. Document 4 box roles — **SUPERSEDED**: new topology is 10-VM fleet, not asymmetric. See
      `epic_vm_fleet_commissioning_2026_05_21.md`.

## Phase 2 — Provision GCE VMs

- [ ] [AGENT] P2. `launch-agent-orchestrator-worker.sh` — **SUPERSEDED**: replaced by
      `deployment-service/scripts/vm/launch-epic-vm.sh --all`. 10 VMs launched 2026-05-21.

## Phase 3 — SSH-spawn capability

- [ ] [AGENT] P3. `server/tmux_spawn.py` backend ssh-tunnels to box → `tmux new-session`. **DEFERRED-POST-CUTOVER** →
      migrated to `epic_vm_fleet_commissioning_2026_05_21.md` Deferred.

## Phase 4 — Daily state.db → GCS sync

- [x] ✅ [AGENT] P4. SQLite hot-backup via `sqlite3.connect().backup()` API. `SnapshotLoop` fires every 12 ticks. GCS
      path: `backups/sqlite/<date>/<mode>_<ts>.db`. agent-orch@tab/ikennaigboaka/1.

## Phase 5 — Backend_id-aware slot routing

- [ ] [AGENT] P5. Extend `accounts.json` with `default_backend_id`; failover "Move to backup" button.
      **DEFERRED-POST-CUTOVER** → migrated to `epic_vm_fleet_commissioning_2026_05_21.md` Deferred.

## Phase 6 — Codex SSOT

- [ ] [AGENT] P6. NEW `/codex/05-infrastructure/agent-orchestrator-worker-topology.md`. **DEFERRED-POST-CUTOVER** →
      migrated to `epic_vm_fleet_commissioning_2026_05_21.md` Deferred.

## Pending preflight items

- [ ] [SCRIPT] P1. Spawn endpoint auto-ensures folder-trust + onboarding flags. **DEFERRED-POST-CUTOVER** → migrated to
      `epic_vm_fleet_commissioning_2026_05_21.md` Deferred.
- [ ] [SCRIPT] P1. Spawn endpoint preflights `/tmp` writability. **DEFERRED-POST-CUTOVER** → migrated.
- [ ] [SCRIPT] P2. VM launcher runs `worker-host-preflight.sh` post-boot. **DEFERRED-POST-CUTOVER** → migrated.
- [ ] [TEST] P2. CI/QG smoke: assert unit template contains `ReadWritePaths=/tmp`. **DEFERRED-POST-CUTOVER**.

## Deferred work — migrated to:

All open items migrated to `plans/active/epic_vm_fleet_commissioning_2026_05_21.md` Deferred section:

- SSH-spawn per backend_id (Phase 3 + 5)
- worker-host-preflight.sh + spawn preflight items
- Codex SSOT `agent-orchestrator-worker-topology.md` (Phase 6)

## Temporary states + canonical follow-up plans

- All deferred items tracked in `epic_vm_fleet_commissioning_2026_05_21.md`.
