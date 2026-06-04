---
title: Agent Orchestrator Worker Topology
type: infrastructure
status: active
created: 2026-05-21
last_reviewed: 2026-05-28
owner: ikenna
---

# Agent Orchestrator Worker Topology

Fleet model: **1 planning VM (GCP) + 10 epic VMs (AWS)** as of 2026-05-22. Each VM runs the orchestrator service on port
8765 + a set of Claude Code worker slots. Planning VM holds 2 interactive slots; each epic VM holds 8 slots.

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

## LIVE STATUS — what is actually supposed to be alive (SSOT, audited 2026-06-04)

> **Only ONE orchestrator VM is live, and it is the only one that must be: `vm-0` = `agent-orchestrator-vm-1` =
> `i-0c9b283b31d6b5ca7`** (m8i.4xlarge, ap-northeast-1). It is **THE CI-responder** —
> `api.agent-orchestrator.odum-research.com → 13.113.200.22 → vm-0` — and the worker host (10 slots `tab/vm-0/N`,
> AutoSpawn ON, backend uvicorn `:8765` behind nginx). **This is the only VM whose health/alerts matter.**
>
> **NOT live (do NOT treat their silence — or alerts about them — as an incident):**
>
> - `i-007e8d99d12831578` (`vm-orchestrator` in the table below) — **STOPPED 2026-06-04** (vestigial: ran duplicate
>   PlanRegen/Failover against an isolated DB, not in `backends.json`, `VM_ID=unknown-vm`, not the CI-responder). Revive
>   only if a distinct purpose is defined; otherwise terminate.
> - The per-epic VMs in the table below (`vm-defi`/`vm-cefi`/…) — **commissioned 2026-05-22 but NOT running** (stopped;
>   the listed IPs are stale). They are **post-cutover / aspirational**, not a live fleet.
>
> **Alert-scoping rule (HARD):** `fleet-git-health-guard.sh` + slot-stale + worker-liveness alerts must scope to the
> **live set above** (currently just vm-0). The guard is a per-VM cron, so a stopped VM self-stops alerting — but the
> guard also has NO internal scoping (it fsck's every `.git` incl. ~478 worktrees → 500+-line dumps) and does NOT
> self-heal (it should `git fetch` to recover missing-but-reachable objects, which is what the 2026-06-04 recovery did
> by hand). When a VM is intentionally stopped, record it here so a stale alert isn't mistaken for a dead-VM incident.
> SSOT for live-vs-planned = **this block**; the table below is the historical/planned commissioning map, NOT a
> liveness statement.

## Current fleet — AWS EC2 ap-northeast-1 (commissioned 2026-05-22; see LIVE STATUS above for what actually runs)

> **AWS is the default cloud provider** as of 2026-05-22 (Phase 4 smoke passed). GCP path remains fully functional via
> `CLOUD_PROVIDER=gcp`. GCP epic fleet decommissioned 2026-05-22 to avoid cost; planning VM at 34.146.53.106 remains
> live until DNS is wired to AWS.

| VM id            | Cloud | IP             | Instance ID         | Epics / workstreams         |
| ---------------- | ----- | -------------- | ------------------- | --------------------------- |
| planning-vm      | GCP   | 34.146.53.106  | (GCE)               | Interactive + governance    |
| vm-defi          | AWS   | 43.207.178.164 | i-05805eb07fdf180b6 | DeFi + manifest             |
| vm-cefi          | AWS   | 43.207.36.161  | i-003be935f72c13d51 | CeFi + instruments          |
| vm-tradfi        | AWS   | 18.181.221.162 | i-0a663001399ef5f49 | TradFi                      |
| vm-sports        | AWS   | 13.115.221.87  | i-005e1bada21b1653f | Sports                      |
| vm-prediction    | AWS   | 43.207.224.187 | i-063bc8dbf59f36220 | Predictions                 |
| vm-ml            | AWS   | 13.114.121.99  | i-02294132088f23e50 | MTDS/MDPS + features + ML   |
| vm-trading-core  | AWS   | 54.238.66.156  | i-0e51b9c73666b3a8b | Strategy + execution        |
| vm-operator-ops  | AWS   | 18.183.155.33  | i-0e89a5f6bd7123521 | DART + promote + deploy-ui  |
| vm-cross-cutting | AWS   | 13.158.82.128  | i-06e33c6e188798333 | Infrastructure + governance |
| vm-orchestrator  | AWS   | 52.193.229.193 | i-007e8d99d12831578 | Orchestrator self           |

IPs are dynamic (no EIPs yet — deferred post-cutover). All VMs use instance profile `uts-orchestrator-epic` in account
427895769566 / ap-northeast-1 / security group sg-0080310387e84f613.

### Fleet dashboard entry point

Fleet tab at `agent-orchestrator.odum-research.com/#fleet` reads `data/config/backends.json` in the agent-orchestrator
repo. Each VM's URL is the direct `http://<public-ip>:8765` endpoint. Port 8765 is open to 0.0.0.0/0 in the security
group.

Re-launch fleet:
`AWS_SECURITY_GROUP_IDS=sg-0080310387e84f613 AWS_SUBNET_ID=subnet-fc09eca6 AWS_KEY_PAIR_NAME=agent-orchestrator-key bash deployment-service/scripts/vm/launch-epic-vm-aws.sh --all`

Re-launch GCP fleet: `bash deployment-service/scripts/vm/launch-epic-vm.sh --all`

---

## Bootstrap

Each VM is bootstrapped by `agent-orchestrator/scripts/bootstrap_vm.sh` (`CLOUD_PROVIDER=aws` default since
`agent-orch@ff0d5ff`, 2026-05-22):

1. Install system deps (git, tmux, Node.js ≥18, python3-yaml)
2. Install AWS CLI v2 (Ubuntu 24.04 doesn't ship it)
3. Install Claude Code CLI
4. Clone workspace repos (unified-trading-pm, UTL, UAC, agent-orchestrator) on `live-defi-rollout`
5. Install systemd service via `scripts/install-orchestrator-service.sh`
6. Create Python venv (`su - ubuntu -c "uv venv .venv --python '>=3.13'"`) + install path deps explicitly
7. Fetch credentials:
   - **AWS**: `aws secretsmanager get-secret-value --secret-id ORCHESTRATOR_ENV_LOCAL` +
     `aws s3 cp s3://uts-orchestrator-creds-{account}/config/{accounts.json,backlog.yaml}`
   - **GCP**: `gcloud secrets versions access latest --secret=ORCHESTRATOR_ENV_LOCAL` + `gcloud storage cp gs://...`
8. Enable + start orchestrator service
9. Emit `STARTED` event:
   - **AWS**: `aws s3 cp - s3://uts-orchestrator-events-{account}/orchestrator/{role}/{vm-name}/STARTED`
   - **GCP**: `gcloud storage cp - gs://{project}-events/orchestrator/{role}/{vm-name}/STARTED`

Key fix (`agent-orch@cbf25e0`): `su -` login shell required for uv venv creation on both GCP and EC2.

---

## Cloud provider toggle

| Toggle       | Value                | Effect                                       |
| ------------ | -------------------- | -------------------------------------------- |
| Default      | `CLOUD_PROVIDER=aws` | AWS Secrets Manager + S3 for all cloud calls |
| GCP fallback | `CLOUD_PROVIDER=gcp` | gcloud secrets + GCS (fully maintained)      |

Set via `--cloud-provider aws|gcp` arg to `bootstrap_vm.sh`, or `CLOUD_PROVIDER` env var in launcher user-data.

AWS launcher: `deployment-service/scripts/vm/launch-epic-vm-aws.sh` GCP launcher:
`deployment-service/scripts/vm/launch-epic-vm.sh` IAM setup: `deployment-service/scripts/aws/setup-orchestrator-iam.sh`

---

## Slot contract

Each slot worktree lives at `.tabs/{N}/{repo}/` on the VM's filesystem. Slot N maps to `tab/ubuntu/{N}` git branch.
Workers call `/api/slots/{N}/boot`, `/progress`, `/done`, `/blocked`, `/heartbeat`.

Full slot-as-worker contract: `agents/worker.md` in the agent-orchestrator repo.

---

## Event bus

| Event     | AWS S3 path                                                                    | GCP GCS path                                                  | Emitter           |
| --------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------- | ----------------- |
| `STARTED` | `s3://uts-orchestrator-events-{account}/orchestrator/{role}/{vm-name}/STARTED` | `gs://{project}-events/orchestrator/{role}/{vm-name}/STARTED` | `bootstrap_vm.sh` |
| `STOPPED` | (post-cutover — SSH-spawn deferred work)                                       | (post-cutover)                                                | TBD               |
| `FAILED`  | (post-cutover — SSH-spawn deferred work)                                       | (post-cutover)                                                | TBD               |

---

> **[DELTA 2026-05-22]** **Current state:** Only `STARTED` events are emitted at bootstrap. `STOPPED` and `FAILED` event
> emission requires the SSH-spawn per-backend-id feature. **Planned delta:** SSH-spawn work tracked under
> `plans/epics/orchestrator_master.md`. **Target architecture:** Full STARTED/STOPPED/FAILED event lifecycle per
> orchestrator VM.

## Deferred (post-cutover)

- **EIP allocation**: shippable recipe in `deployment-service/scripts/aws/allocate-orchestrator-eips.sh`.
  Operator-runnable; idempotent. Allocates + associates + tags one EIP per fleet VM. Run any time; safe to defer until
  backends.json churn becomes a real pain point.
- **DNS**: FQDNs `api-{vm}.agent-orchestrator.odum-research.com` per
  [`./agent-orchestrator-dns-cutover.md`](agent-orchestrator-dns-cutover.md). Requires EIPs first. Operator-side action
  on the `odum-research.com` zone.
- **Prebaked AMI provisioning** (Phase 9): Packer template at `deployment-service/packer/agent-orchestrator/` bakes
  Steps 1-2 + Step 4.5 of `bootstrap_vm.sh` into an AMI; `bootstrap_vm.sh` detects `/etc/orchestrator-ami-version` and
  short-circuits the baked steps. Cuts cold-boot from ~5-15 min to <5 min. Operator-runnable via `packer build`; pass
  `AMI_ID=<id>` to `launch-epic-vm-aws.sh` to use it.
- **SSH-spawn per backend_id**: slots map to backend_ids; orchestrator ssh-tunnels spawn. Ships post-cutover.
- **`.tabs/` 8-slot worktree population**: epic VMs currently have 4 cross-cutting repos; full service-repo clone ships
  with ssh-spawn + tarball-deploy work.
- **STOPPED/FAILED events**: post-SSH-spawn.
- **backends.json auto-sync**: currently updated manually when fleet is re-launched with new IPs. Should be driven by
  the registry `api_url` field post-EIP/DNS cutover.
- **GCP planning VM**: decommissioned 2026-05-22 → 23 during the AWS migration. The central API role moved to
  `13.113.200.22` (EC2 EIP) which is the "ikenna-vm" backend.
