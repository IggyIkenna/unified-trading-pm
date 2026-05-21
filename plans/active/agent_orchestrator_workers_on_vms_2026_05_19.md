---
title: agent-orchestrator workers on VMs (asymmetric Ikenna+Harsh topology)
parent_epic: orchestrator_master
priority: P1
status: active
estimate_class: infra
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 3.2
locked_by: live-defi-rollout
locked_since: 2026-05-19
related_plans:
  - agent_orchestrator_cloud_run_deployment_2026_05_19.md
  - master_to_live_defi_2026_05_23.md
---

# Agent-Orchestrator Workers on VMs

Move agent-orchestrator workers from laptop tmux-spawn to dedicated GCE VMs (asymmetric: Ikenna-primary VM +
Harsh-backup PC). Backend ssh-spawns into assigned worker box. Required before Cloud Run prod cutover (Harsh laptop
nginx shutdown). Also includes worker-liveness kicker daemon + preflight script shipped.

Codex SSOTs: `codex/05-infrastructure/agent-orchestrator-worker-topology.md` (to be created at Phase 6) ·
`codex/04-architecture/agent-orchestrator-overview.md`

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

- [ ] [AGENT] P1. Document 4 box roles (Ikenna VM + Ikenna laptop + Harsh PC + Harsh VM); confirm tmux-spawn vs
      ssh-spawn; confirm slot-to-box mapping shape (`accounts.json` account → `backend_id`); operator sign-off on VM
      specs + cost estimate (~$30-60/mo n2-standard-2).

## Phase 2 — Provision GCE VMs

- [ ] [AGENT] P2. `launch-agent-orchestrator-worker.sh` (--operator=ikenna|harsh, --role=primary|backup); VM naming
      `agent-orch-worker-ikenna-prod` / `agent-orch-worker-harsh-backup`; clone + install Claude Code CLI + systemd
      service + state.db sync cron; T+10min verification.

## Phase 3 — SSH-spawn capability

- [ ] [AGENT] P3. `server/tmux_spawn.py` backend reads `backend_id` from slot config → ssh-tunnels to box →
      `tmux new-session`; auth via dedicated keypair in Secret Manager; no-silent-fallback: if ssh fails →
      `box_unreachable` state.

## Phase 4 — Daily state.db → GCS sync

- [x] ✅ [AGENT] P4. SQLite hot-backup via `sqlite3.connect().backup()` API (safe under concurrent writes). `SnapshotLoop`
      fires every 12 ticks (~6h at 1800s interval). GCS path: `backups/sqlite/<date>/<mode>_<ts>.db`. Restore:
      `scripts/restore_from_gcs.sh`. agent-orch@tab/ikennaigboaka/1 2026-05-21.

## Phase 5 — Backend_id-aware slot routing

- [ ] [AGENT] P5. Extend `accounts.json` with `default_backend_id`; slot boot looks up backend_id + spawns there;
      failover "Move to backup" button if primary unreachable >5min; `box_unreachable` Slack alert if both unreachable.

## Phase 6 — Codex SSOT

- [ ] [AGENT] P6. NEW `codex/05-infrastructure/agent-orchestrator-worker-topology.md`; update
      `codex/04-architecture/agent-orchestrator-overview.md` Workers row; update
      `agent-orchestrator-e2e-operator-runbook.md`.

## Pending preflight items

- [ ] [SCRIPT] P1. Spawn endpoint auto-ensures folder-trust + onboarding flags in `~/.claude.json` for target worktree.
- [ ] [SCRIPT] P1. Spawn endpoint preflights `/tmp` writability in its own namespace + returns specific 5xx if fails.
- [ ] [SCRIPT] P2. VM launcher runs `worker-host-preflight.sh` as post-boot step + refuses to register box without
      passing.
- [ ] [TEST] P2. CI/QG smoke: assert unit template contains `ReadWritePaths=/tmp`.

## Temporary states + canonical follow-up plans

- All phases gated on Phase 1 operator decision on topology.
- Phase 5 (D3) is the hard prerequisite for Cloud Run prod cutover in `agent_orchestrator_cloud_run_deployment` Phase 5.
