---
name: agent-orchestrator-workers-on-vms-2026-05-19
overview: |
  Move worker tmux execution off operator laptops onto an asymmetric box mix:
  Ikenna-primary = dedicated GCE VM; Ikenna-backup = laptop; Harsh-primary = local PC;
  Harsh-backup = GCE VM. Both push state.db to GCS daily for cross-machine sync + DR.
  The Cloud Run backend (P5 prod) remains the always-on dispatcher; this plan adds
  the ssh-spawn glue so the dispatcher can launch tmux sessions on the appropriate
  worker box per slot affinity. Unblocks `agent_orchestrator_cloud_run_deployment_2026_05_19.md`
  P5 "Harsh laptop decommission" — with this asymmetric design that step gets reframed
  as "laptop nginx removed (backend is Cloud Run); laptop stays as primary worker host
  for Harsh's slots".
type: infra
status: active
epic: epic-infra

estimate_class: infra
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 6.4

locked_by: live-defi-rollout
locked_since: 2026-05-19

completion_gates:
  code: C5
  deployment: D3
  business: none

repo_gates:
  - repo: agent-orchestrator # ssh-spawn glue + backend_id-aware tmux_spawn
    code: C0
    deployment: none
    business: none
  - repo: deployment-service # VM launcher scripts
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-pm # plan + codex doc
    code: C0
    deployment: none
    business: none

depends_on:
  - agent-orchestrator-cloud-run-deployment-2026-05-19 # P3+ — backend already live; P5 prod cutover gates on this plan reaching D3

todos:
  - id: p1-design-confirm
    content: |
      - [ ] [AGENT] P1. Confirm asymmetric design with operators
        - [ ] Document the 4 box roles (Ikenna VM + Ikenna laptop + Harsh PC + Harsh VM) with concrete specs (machine type, RAM, disk, region)
        - [ ] Confirm tmux-spawn vs ssh-spawn — does the Cloud Run backend ssh into worker boxes, or do worker boxes poll the backend over HTTP?
        - [ ] Confirm slot-to-box mapping shape: `data/config/backends.json` `backend_id` field already exists; slot affinity in `accounts.json` already maps slot → account. Mapping account → backend_id is the new piece.
        - [ ] Operator sign-off on VM specs + monthly cost estimate (~$30-60/mo for 2 small VMs always-on, n2-standard-2 4 vCPU 8 GB; less if right-sized down to e2-small)
      Full-execution criterion: design doc landed at codex/05-infrastructure/agent-orchestrator-worker-topology.md with explicit per-box config + sign-off captured.
    status: todo

  - id: p2-vm-provisioning
    content: |
      - [ ] [AGENT] P2. Provision the two GCE VMs (Ikenna-primary + Harsh-backup)
        - [ ] deployment-service/scripts/vm/launch-agent-orchestrator-worker.sh — modeled on existing scripts/vm/ launcher pattern (per CLAUDE.md VM Launcher SSOT). Args: --operator=ikenna|harsh, --role=primary|backup
        - [ ] VM naming: agent-orch-worker-ikenna-prod / agent-orch-worker-harsh-backup. Both first segment in VM_PREFIX_TO_BUCKET (per CLAUDE.md VM naming HARD RULE)
        - [ ] Per VM: clone agent-orchestrator + install Claude Code CLI + configure ssh keys for backend ssh-spawn + systemd service for `claude` worker process + state.db sync cron
        - [ ] Boot the 2 VMs; verify STARTED → ≥1 progress/hour → STOPPED/FAILED at exit (CLAUDE.md no-fire-and-forget HARD RULE)
        - [ ] T+10min verification (per CLAUDE.md): deployment registry heartbeat + `gcloud compute instances describe` = RUNNING
      Full-execution criterion: `gcloud compute instances list --filter="name~agent-orch-worker"` shows 2 RUNNING VMs (Ikenna-primary in primary region, Harsh-backup in secondary). SSH connectivity from the Cloud Run backend SA to both VMs verified via test `claude --version` over ssh.
    status: todo

  - id: p3-ssh-spawn-backend
    content: |
      - [ ] [AGENT] P3. Add ssh-spawn capability to agent-orchestrator/server/tmux_spawn.py
        - [ ] Backend reads `backend_id` from slot config → looks up box in `backends.json` → ssh-tunnels to that box → `tmux new-session -d -s slot_${N} 'claude --dangerously-skip-permissions'`
        - [ ] Loadbuffer/pastebuffer the boot prompt over ssh (same flow as current local tmux_spawn, just remoted)
        - [ ] Heartbeat path: backend POSTs slot heartbeat to its own /api/heartbeat which records `last_ping` — same as today, no changes there
        - [ ] Auth: backend uses a dedicated ssh keypair generated at VM provision time; key stored in GCP Secret Manager + mounted into Cloud Run as file
        - [ ] Fallback: if ssh-spawn fails to remote box, return error to dashboard with "box unreachable" + suggest manual remediation (don't silently spawn local — would re-introduce the Cloud-Run-can't-tmux problem)
      Full-execution criterion: from dashboard, spawn a test worker assigned to `ikenna-primary-vm` backend_id → tmux session lands on the VM, worker boots, picks up a backlog task, /done arrives at the Cloud Run backend within 5min. Repeat for `harsh-backup-vm`. Both work end-to-end.
    status: todo

  - id: p4-gcs-state-sync
    content: |
      - [ ] [AGENT] P4. Daily state.db → GCS sync (cross-machine sync + DR)
        - [ ] Existing gs://agent-orchestrator-state-prod/ bucket (asia-northeast1, created at parent plan P5)
        - [ ] Cron on each worker box (Ikenna laptop, Ikenna VM, Harsh PC, Harsh VM): nightly `sqlite3 .backup` → `gsutil cp` to `gs://agent-orchestrator-state-prod/snapshots/<box-id>/<date>.db`
        - [ ] Restore path: documented in codex/05-infrastructure/agent-orchestrator-worker-topology.md — `gsutil cp` from GCS + sqlite restore + symlink
        - [ ] Snapshot retention: 30-day versioned per the parent plan P5 bucket lifecycle policy
      Full-execution criterion: snapshots from all 4 boxes visible in `gsutil ls gs://agent-orchestrator-state-prod/snapshots/` within 24 hours of P4 ship; manual restore-from-snapshot drill on a test box succeeds.
    status: todo

  - id: p5-backend-id-routing
    content: |
      - [ ] [AGENT] P5. Wire backend_id-aware slot routing in the backend
        - [ ] Schema: extend `data/config/accounts.json` to include `default_backend_id` per account (e.g. ikenna's account → `ikenna-primary-vm`)
        - [ ] Slot boot: when worker calls /boot, backend looks up `backend_id` from slot config → spawns there
        - [ ] Failover: if primary box is unreachable for >5min, dashboard exposes a "Move to backup" button → backend re-spawns slot on backup box (Ikenna-laptop or Harsh-VM)
        - [ ] No-silent-fallback: if BOTH primary + backup unreachable, slot status = `box_unreachable` (new state); operator notified via Slack
      Full-execution criterion: 5-step end-to-end test: (a) slot spawns on Ikenna's VM, (b) Ikenna-VM cordoned (gcloud instances stop), (c) dashboard shows slot as unreachable + Move-to-backup button, (d) operator clicks → slot re-spawns on Ikenna-laptop, (e) worker resumes work within 60s.
    status: todo

  - id: p6-docs-rollout
    content: |
      - [ ] [AGENT] P6. Codex SSOT + operator-runbook updates
        - [ ] New codex doc: codex/05-infrastructure/agent-orchestrator-worker-topology.md (per-box config, VM provisioning recipe, state.db sync flow, failover procedure)
        - [ ] Update codex/08-workflows/agent-orchestrator-e2e-operator-runbook.md: add "How to handle box unreachable" section + ssh-spawn debug recipe
        - [ ] Update codex/04-architecture/agent-orchestrator-overview.md "Workers" row: change "tmux-spawn on operator's laptop (pre-P5); dedicated GCE VMs post workers-on-VMs plan" → "asymmetric: primary = VM or PC per operator; backup on the other; backend ssh-spawns into the assigned box"
        - [ ] Update parent plan's P5 row: "shut down laptop nginx" → "laptop nginx already gone (backend is Cloud Run); laptop stays as primary or backup worker host per operator"
      Full-execution criterion: 4 codex doc updates committed + parent plan's P5 entry reworded + grep `tmux-spawn on operator's laptop` returns 0 hits (replaced with the new asymmetric description).
    status: todo

isProject: true
---

# Workers-on-VMs (asymmetric design) — 2026-05-19

## Context

The original "all workers move to VMs" idea (captured in `agent_orchestrator_cloud_run_deployment_2026_05_19.md`
Out-of-scope table) was revised on 2026-05-19 ~14:30 UTC per a Slack discussion between Ikenna and Harsh. The new design
is **asymmetric** — different primary host per operator based on their work pattern:

| Operator   | Primary worker host                                                                                     | Backup                                         |
| ---------- | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| **Ikenna** | Dedicated GCE VM (always-on, work-from-anywhere, mobile-friendly, no contention with local UI overhead) | Laptop (ad-hoc tests, paper trading, backfill) |
| **Harsh**  | Local PC (more RAM, free, always-on for him)                                                            | GCE VM (work-from-anywhere fallback)           |

Both push `data/state/state.db` to GCS daily for cross-machine sync + DR.

The Cloud Run backend (live at `agent-orchestrator.staging.odum-research.com` as of 2026-05-19) remains the **always-on
dispatcher**. What changes is WHERE the worker tmux sessions live — moving them off the backend host (which is now a
stateless Cloud Run container that can't tmux-spawn anyway) onto the 4 worker boxes.

## Architecture sketch

```
                    Cloud Run backend (always-on dispatcher)
                       │  reads slot config → backend_id
                       │
                       ├── ssh-spawn ──► ikenna-primary-vm   (GCE)  ─┐
                       ├── ssh-spawn ──► ikenna-laptop        (local) ├─ daily state.db
                       ├── ssh-spawn ──► harsh-primary-pc     (local) ├─    → GCS
                       └── ssh-spawn ──► harsh-backup-vm      (GCE)  ─┘

                       Slots have backend_id affinity:
                         slot 1-5  → ikenna-primary-vm    (or fallback ikenna-laptop)
                         slot 6-10 → harsh-primary-pc     (or fallback harsh-backup-vm)
```

## Phase DAG

```
P1 (design confirm) ─┐
                     ▼
              P2 (VM provisioning)
                     │
                     ▼
              P3 (ssh-spawn backend)
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   P4 (GCS sync)  P5 (routing)  P6 (docs)
```

## Phase 0 — Worker-host spawn prerequisites (root-caused 2026-05-20)

> **Why this is here**: during the orchastrator→agent-orchestrator cutover, all worker API spawns failed with the
> opaque `tmux session did not become ready within 30.0s`. Four silent first-run gates were the cause (theme picker,
> OAuth login, folder-trust, and — the nastiest — `/tmp` read-only under `ProtectSystem=strict`). On a headless VM these
> are far harder to detect. Full root-cause + fix table: `agent-orchestrator/docs/WORKER_SPAWN_PREREQUISITES.md`.
> Interim fixes already landed on Harsh-primary (PC): unit `ReadWritePaths=/tmp`, claude onboarding flags + per-worktree
> trust, and `scripts/worker-host-preflight.sh`.

- [x] [INFRA] P0. Add `ReadWritePaths=/tmp` to `scripts/orchestrator.service` template + live unit (else `tmux` can't
      create its socket in the service namespace). — agent-orchestrator (template fixed; live unit patched 2026-05-20)
- [x] [SCRIPT] P0. `scripts/worker-host-preflight.sh` — idempotent: claude theme/onboarding flags, per-worktree
      `hasTrustDialogAccepted`, credentials-present check, `/tmp` writability, + live self-test spawn. — agent-orchestrator
- [x] [DOC] P0. `docs/WORKER_SPAWN_PREREQUISITES.md` — the four gates + the `nsenter` diagnostic + provisioning steps. — agent-orchestrator
- [x] ✅ [AGENT] P0. `server/worker_liveness.py` — `WorkerLivenessKicker` daemon thread (mirrors `TmuxPruner`): classify pane (working/frozen/idle), kick frozen+idle via send-keys+sleep1+C-m, per-slot debounce (2×interval), `worker_kicked` activity event. Wired into `server.lifespan` next to `TmuxPruner`. Tests in `tests/test_worker_liveness.py` (21 tests, classifier fixtures, blocked-skip, debounce). ruff+basedpyright+pytest green; CI green. — agent-orchestrator@9e18f97
- [ ] [SCRIPT] P1. Spawn endpoint auto-ensures folder-trust + onboarding flags in `~/.claude.json` for the target
      worktree before launching claude (reuse the `worktree_setup` bootstrap hook that already runs on spawn). — agent-orchestrator
- [ ] [SCRIPT] P1. Spawn endpoint preflights `/tmp` writability **in its own namespace** and returns a specific 5xx
      ("/tmp read-only — add ReadWritePaths=/tmp") instead of the opaque 30s timeout. — agent-orchestrator
- [ ] [SCRIPT] P2. VM launcher runs `worker-host-preflight.sh` as a post-boot step + refuses to register the box as a
      worker host until green. Surface result in `backends.json` health. — deployment-service + agent-orchestrator
- [ ] [TEST] P2. CI/QG smoke: assert the unit template contains `ReadWritePaths=/tmp` so the regression can't silently
      come back. — agent-orchestrator

## Pre-audit manifest

Already exists:

- `data/config/backends.json` — per-box `id` + `url` + `account_id`. Just needs `default_backend_id` field per account
  in accounts.json.
- `server/tmux_spawn.py` — local tmux-spawn logic (the box where backend runs). Needs to gain ssh-spawn-to-remote-box
  mode.
- `deployment-service/scripts/vm/` — VM launcher SSOT. New launcher fits the pattern.
- `gs://agent-orchestrator-state-prod/` bucket scheduled for creation at parent plan P5. This plan can land BEFORE that
  bucket exists; just creates it earlier here.

## Out-of-scope / named successor plans

| Item                                                        | Successor                                                                |
| ----------------------------------------------------------- | ------------------------------------------------------------------------ |
| Multi-Claude-account failover (Anthropic rate limits)       | Already named: `agent_orchestrator_multi_account_failover_2026_05_XX.md` |
| Slack notifications for `slot_box_unreachable` event        | Wires into the Slack successor plan                                      |
| Worker box scaling beyond 4 boxes (e.g. 10 slots / 4 boxes) | Defer — current capacity is enough                                       |

## Codex SSOT updates (per HARD RULE)

| Codex doc                                                       | Action                                        |
| --------------------------------------------------------------- | --------------------------------------------- |
| `codex/05-infrastructure/agent-orchestrator-worker-topology.md` | NEW at P6                                     |
| `codex/08-workflows/agent-orchestrator-e2e-operator-runbook.md` | UPDATE at P6 — add "box unreachable" recovery |
| `codex/04-architecture/agent-orchestrator-overview.md`          | UPDATE at P6 — Workers row                    |

## Risks

1. **SSH key management** — backend needs ssh-keypair access to 4 boxes. Keys in Secret Manager + mounted into Cloud
   Run. If key rotates, all 4 boxes need authorized_keys update. Mitigation: use a single shared keypair stored in
   Secret Manager; rotation is a documented runbook step.
2. **Local PC reliability** — Harsh's PC isn't 100% uptime. Mitigation: backup VM kicks in via Move-to-backup button at
   P5.
3. **VM cost** — ~$30-60/mo for 2 always-on small VMs. Acceptable per parent plan's Cost row (~$15-25/mo Cloud Run +
   this).
4. **Network egress** — Cloud Run backend → on-prem PC (Harsh) is a NAT-traversal problem. Mitigation: PC needs a
   static-IP setup or use Cloud IAP TCP tunneling.

## Full-Execution closeout summary (filled at archive)

| Phase | What ran  | Verification | SHA |
| ----- | --------- | ------------ | --- |
| P1    | _pending_ | _pending_    | —   |
| P2    | _pending_ | _pending_    | —   |
| P3    | _pending_ | _pending_    | —   |
| P4    | _pending_ | _pending_    | —   |
| P5    | _pending_ | _pending_    | —   |
| P6    | _pending_ | _pending_    | —   |
