---
doc_type: plan
title: Epic VM fleet commissioning — planning VM finalization + 9 epic VMs launch
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator, deployment-service]
scope: [engineer, admin]
tags: []
related:
  [agent_orchestrator_workers_on_vms_2026_05_19.md, /plans/archive/2026_05/agent_reliability_mitigations_2026_05_20.md]
created: "2026-05-21"
parent_epic: orchestrator_master
priority: P0
archived_date: 2026-05-22
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

> **ARCHIVED 2026-05-22** — All phases complete. Fleet of 10 GCE epic VMs healthy (T+10min verification passed).
> Deferred items migrated to `plans/epics/orchestrator_master.md` + `plans/active/aws_epic_vm_fleet_2026_05_22.md`.
> Codex alignment: `/codex/04-architecture/agent-orchestrator-overview.md` +
> `/codex/05-infrastructure/agent-orchestrator-worker-topology.md` updated 2026-05-22.

## Deferred work — migrated to:

- **SSH-spawn per backend_id** → `plans/epics/orchestrator_master.md` (post-cutover)
- **DNS wiring** → `plans/epics/orchestrator_master.md` (post-cutover)
- **`worker-host-preflight.sh` in bootstrap** → `plans/epics/orchestrator_master.md` (ships with ssh-spawn)
- **`.tabs/` 8-slot worktree population on epic VMs** → `plans/epics/orchestrator_master.md` (ships with ssh-spawn +
  tarball)
- **Codex SSOT `agent-orchestrator-worker-topology.md`** → COMPLETED at archive time 2026-05-22 (doc written)
- **Spawn endpoint preflight** → `plans/epics/orchestrator_master.md` (ships with ssh-spawn)
- **AWS cloud provider toggle** → `plans/active/aws_epic_vm_fleet_2026_05_22.md`

---

# Epic VM Fleet Commissioning

Bootstrap gap analysis (2026-05-21): orchestrator code is done; VM launch scripts + bootstrap_vm.sh are fixed; 3 Ikenna
Claude Code accounts are in GCS. Three gaps block epic VM launch: (1) `ORCHESTRATOR_ENV_LOCAL` secret doesn't exist in
Secret Manager → epic VMs start with empty .env.local (no JWT, no Telegram); (2) `backlog.yaml` + `accounts.json` not in
GCS → orchestrator crashes on first boot; (3) planning VM has empty .tabs/ and no external access.

Supersedes the old asymmetric model in `agent_orchestrator_workers_on_vms_2026_05_19.md` — that plan was Ikenna VM +
Harsh PC. New model: 1 planning VM + 9 epic VMs, all running orchestrator + 8 worker slots, 3-account round-robin
(sub-a/sub-b/sub-c Ikenna).

Codex SSOTs:

- `/codex/04-architecture/agent-orchestrator-overview.md` — updated 2026-05-22 (fleet topology, AWS toggle noted)
- `/codex/05-infrastructure/vm-tarball-deployment.md`
- `/codex/05-infrastructure/agent-orchestrator-worker-topology.md` — written 2026-05-22 (was stub)

---

## Phase 1 — Secret + config automation (prerequisites for any epic VM boot)

- [x] ✅ [AGENT] P0. Create `ORCHESTRATOR_ENV_LOCAL` Secret Manager secret with generic vars (JWT, Telegram, mode,
      users.json path) — VM-specific vars (VM_ID, VM_ROLE, PUBLIC_URL) appended by bootstrap per-VM. agent-orch@007b991.
      Secret Manager version 1 created 2026-05-21.
- [x] ✅ [AGENT] P0. Drop `harsh-primary` from `accounts.json` — 3 Ikenna accounts (sub-a/sub-b/sub-c) sufficient for
      all 9 epic VMs + planning VM. Clean version pushed to GCS `config/accounts.json` + planning VM updated.
      agent-orch@007b991.
- [x] ✅ [AGENT] P0. Push `backlog.yaml` + `accounts.json` to GCS
      `gs://central-element-323112-orchestrator-creds/config/`. Both objects confirmed 2026-05-21.
- [x] ✅ [AGENT] P0. Update `bootstrap_vm.sh` Step 5b+c — ORCHESTRATOR_ENV_LOCAL secret + VM-specific env var appends
      (VM_ID/VM_ROLE/PUBLIC_URL from metadata) + fetch accounts.json + backlog.yaml from GCS config/ into data/config/.
      agent-orch@97b1541.

## Phase 2 — Planning VM finalization

- [x] ✅ [AGENT] P1. Run `setup-tab-worktrees.sh --init --slots 2` on planning VM — `.tabs/1/` + `.tabs/2/` created with
      UAC, UTL, PM, agent-orchestrator worktrees. Service repos skipped (not cloned on planning VM — planning VM doesn't
      run service workers). 2026-05-21.
- [x] ✅ [AGENT] P1. External access: GCP firewall rule `allow-orch-8026` (tcp:8026, tags `orchestrator-planning-vm` +
      `orchestrator-epic-vm`) created. orchestrator.service ExecStart changed from `--host 127.0.0.1` →
      `--host 0.0.0.0`. Verified: `curl http://34.146.53.106:8026/health` = ok. agent-orch@007b991. DNS post-cutover.

## Phase 3 — Epic VM fleet launch

- [x] ✅ [AGENT] P0. `bash deployment-service/scripts/vm/launch-epic-vm.sh --all` — all 9 epic VMs launched 2026-05-21,
      all STATUS=RUNNING in asia-northeast1-c: vm-defi@35.200.55.185 · vm-cefi@35.200.75.132 · vm-tradfi@35.200.59.184 ·
      vm-sports@34.146.32.46 · vm-prediction@136.110.98.16 · vm-ml@35.200.66.186 · vm-trading-core@35.200.121.156 ·
      vm-operator-ops@34.85.27.215 · vm-cross-cutting@34.104.133.72 · vm-orchestrator@35.194.106.13
- [x] ✅ [AGENT] P0. T+10min verification PASSED 2026-05-22 — all 10 epic VMs health=ok + GCS STARTED events confirmed.
      All 10 VMs healthy: cefi@35.200.75.132 · cross-cutting@34.104.133.72 · defi@35.200.55.185 · ml@35.200.66.186 ·
      operator-ops@34.85.27.215 · orchestrator@35.194.106.13 · prediction@136.110.98.16 · sports@34.146.32.46 ·
      tradfi@35.200.59.184 · trading-core@35.200.121.156 — all `{"status":"ok"}`. GCS STARTED events confirmed at
      gs://central-element-323112-events/orchestrator/epic/agent-orch-<vm>-20260521/STARTED for all 10. Fix:
      bootstrap_vm.sh cbf25e0 — `su -` login shell + explicit path deps for venv creation.

## Phase 4 — Housekeeping

- [x] ✅ [AGENT] P2. Archive `agent_orchestrator_workers_on_vms_2026_05_19.md` — old asymmetric Ikenna+Harsh model
      superseded by this plan. Open deferred items (Phase 3 ssh-spawn, Phase 5 backend_id routing, Phase 6 codex SSOT,
      pending preflight items) migrated to Deferred section above. Archived to
      `plans/archive/agent_orchestrator_workers_on_vms_2026_05_19.plan.md`. pm@7c7f275.
