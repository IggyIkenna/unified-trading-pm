---
title: Agent Orchestrator Worker Topology
type: infrastructure
status: active
created: 2026-05-21
last_reviewed: 2026-05-22
owner: ikenna
---

# Agent Orchestrator Worker Topology

Fleet model: **1 planning VM + 10 epic GCE VMs** (as of 2026-05-22). Each VM runs the orchestrator service on port
8026 + a set of Claude Code worker slots. Planning VM holds 2 interactive slots; each epic VM holds 8 slots.

Total capacity: **82 worker slots** across 11 VMs.

Registry SSOT: `orchestrator_vm_registry.yaml` in `unified-trading-pm`. Every VM id + slot count + epic assignment is
canonical there. Do not duplicate the list here — read the registry.

---

## VM roles

| Role       | Count | Slots each | Purpose                                               |
| ---------- | ----- | ---------- | ----------------------------------------------------- |
| `planning` | 1     | 2          | Interactive Ikenna sessions; cross-cutting governance |
| `epic`     | 10    | 8          | Dispatched worker agents; each VM owns a set of epics |

---

## Current fleet (GCP asia-northeast1-c, commissioned 2026-05-21)

| VM id            | IP             | Epics / workstreams        | Health endpoint                   |
| ---------------- | -------------- | -------------------------- | --------------------------------- |
| planning-vm      | 34.146.53.106  | Cross-cutting + governance | http://34.146.53.106:8026/health  |
| vm-cefi          | 35.200.75.132  | CeFi                       | http://35.200.75.132:8026/health  |
| vm-cross-cutting | 34.104.133.72  | Cross-cutting infra        | http://34.104.133.72:8026/health  |
| vm-defi          | 35.200.55.185  | DeFi                       | http://35.200.55.185:8026/health  |
| vm-ml            | 35.200.66.186  | ML / features              | http://35.200.66.186:8026/health  |
| vm-operator-ops  | 34.85.27.215   | Operator ops               | http://34.85.27.215:8026/health   |
| vm-orchestrator  | 35.194.106.13  | Orchestrator self          | http://35.194.106.13:8026/health  |
| vm-prediction    | 136.110.98.16  | Predictions                | http://136.110.98.16:8026/health  |
| vm-sports        | 34.146.32.46   | Sports                     | http://34.146.32.46:8026/health   |
| vm-tradfi        | 35.200.59.184  | TradFi                     | http://35.200.59.184:8026/health  |
| vm-trading-core  | 35.200.121.156 | Trading core               | http://35.200.121.156:8026/health |

VM names follow `agent-orch-{vm-id}-{YYYYMMDD}`. Launched via `deployment-service/scripts/vm/launch-epic-vm.sh --all`.

---

## Bootstrap

Each VM is bootstrapped by `agent-orchestrator/scripts/bootstrap_vm.sh`:

1. Install system deps (git, tmux, Node.js ≥18)
2. Install Claude Code CLI
3. Clone workspace repos (unified-trading-pm, UTL, UAC, agent-orchestrator) on `live-defi-rollout`
4. Install systemd service via `scripts/install-orchestrator-service.sh`
5. Create Python venv (`su - ubuntu -c "uv venv .venv --python '>=3.13'"`) + install path deps explicitly
6. Fetch credentials (GCP Secret Manager `ORCHESTRATOR_ENV_LOCAL` + GCS `config/accounts.json` + `config/backlog.yaml`)
7. Enable + start orchestrator service
8. Emit `STARTED` event to GCS `gs://{project}-events/orchestrator/epic/{vm-name}/STARTED`

Key fix (2026-05-22, `agent-orch@cbf25e0`): `su -` login shell required for uv venv creation — `sudo -H` does not
reliably reset HOME when the calling shell inherits a foreign user's env (gcloud SSH as non-ubuntu user).

---

## Cloud provider toggle

Current: **GCP** (`CLOUD_PROVIDER=gcp`). AWS support in progress — `CLOUD_PROVIDER=aws|gcp` toggle in launcher +
bootstrap. AWS will be **default** when ready (existing AWS credits). GCP path remains fully functional.

See `plans/active/aws_epic_vm_fleet_2026_05_22.md`.

---

## Slot contract

Each slot worktree lives at `.tabs/{N}/{repo}/` on the VM's filesystem. Slot N maps to `tab/ubuntu/{N}` git branch.
Workers call `/api/slots/{N}/boot`, `/progress`, `/done`, `/blocked`, `/heartbeat`.

Full slot-as-worker contract: `agents/worker.md` in the agent-orchestrator repo.

---

## Event bus

| Event     | GCS path                                                      | Emitter           |
| --------- | ------------------------------------------------------------- | ----------------- |
| `STARTED` | `gs://{project}-events/orchestrator/{role}/{vm-name}/STARTED` | `bootstrap_vm.sh` |
| `STOPPED` | (future — SSH-spawn deferred work)                            | TBD               |
| `FAILED`  | (future — SSH-spawn deferred work)                            | TBD               |

---

## Deferred

- **SSH-spawn per backend_id**: slots map to backend_ids; orchestrator ssh-tunnels spawn. Ships post-cutover. See
  `plans/epics/orchestrator_master.md`.
- **`.tabs/` 8-slot worktree population**: epic VMs currently have 4 cross-cutting repos; full service-repo clone ships
  with ssh-spawn + tarball-deploy work.
- **DNS**: FQDNs `api-{vm}.agent-orchestrator.odum-research.com`. Not needed for May-23.
- **STOPPED/FAILED events**: post-SSH-spawn.
