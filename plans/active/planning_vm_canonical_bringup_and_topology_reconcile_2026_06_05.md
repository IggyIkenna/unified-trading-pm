---
title: Planning-VM canonical bring-up + multi-VM topology reconciliation
parent_epic: orchestrator_master
assigned_vm: planning-vm
priority: P1
status: active
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
created: 2026-06-05
source:
  - operator session 2026-06-05 (slot tab/ikennaigboaka/1) — planning-VM spin-up + static-IP/topology clarification
related_plans:
  - plans/active/agent_orchestrator_e2e_workflow_and_execution_scope_2026_06_02.md
  - plans/active/cicd_contract_hardening_2026_06_01.md
---

# Planning-VM canonical bring-up + topology reconciliation

> Driver (operator 2026-06-05): "spin up the planning VM properly, slots like my laptop so Ikenna/Harsh can orchestrate
> plans + audit in parallel." Investigation found the planning VM **is already the central API VM** (EC2
> `i-0c9b283b31d6b5ca7`, Elastic IP `13.113.200.22`, m8i.4xlarge, RUNNING, `/health`=200) — it just lacks
> properly-branded interactive slots, and the registry/docs are stale + conflate it with the _epic_ VM `vm-orchestrator`
> (a SEPARATE, currently-stopped box that owns the agent-orchestrator codebase epic). Static-IP question resolved: only
> the ONE central API needs a stable public IP and it HAS the EIP; epic VMs are private (central proxies over the VPC),
> dynamic IPs are fine. SSOT topology: `codex/12-agent-workflow/orchestrator-multi-vm-topology.md`.

## Canonical topology (confirmed 2026-06-05)

- **Central API VM == Planning VM** — `i-0c9b283b31d6b5ca7`, EIP `13.113.200.22`, DNS
  `api.agent-orchestrator.odum-research.com` → that EIP, nginx :443 → orchestrator backend :8765. THE single endpoint
  (CI escalations + dashboard + operator chat all hit it; survives reboots; no DNS churn). Hosts the interactive
  PLANNING slots. Auto-spawns SLOTS, never auto-assigns JOBS — "workers" here are humans in isolated worktrees.
- **`vm-orchestrator`** — `i-007e8d99d12831578`, STOPPED (operator-stopped 2026-06-04 15:51 GMT). One of the 10 _epic_
  VMs; owns the `orchestrator_master` epic (the agent-orchestrator codebase). NOT the running central orchestrator.
  Parked until CI/CD + epic dispatch is ready. Its registry `public_ip: 52.193.229.193` is a DEAD IP.
- **Epic VMs** (10): private (`172.31.x.x:8026`), central reverse-proxies to them; each = orchestrator + slot1 main +
  slot2 review + slot3+ workers; owns its epic master plan. Not running yet.

## Todos

- [x] ✅ [SCRIPT] P1. **Fix the active-host filter — drop `vm-orchestrator`, add `planning`.** The always-on
      escalation/CI responder is the PLANNING VM (central, `13.113.200.22`), NOT the epic VM `vm-orchestrator`
      (stopped). Active set → `ikennaigboaka hk planning`. SHIPPED 2026-06-05 (see evidence on flip). Repo:
      `unified-trading-pm` (`scripts/workflow-templates/tab-mirror-to-ldr.yml` + PM copy; re-rollout to fleet).
      parent_epic: orchestrator_master.
- [ ] [INFRA] P1. **Provision 5 interactive planning slots on the central VM as `tab/planning/N`** (the old
      `tab/ikenna/*` were its mis-named slots, now deleted; zero `tab/planning/*` exist). SSH into `13.113.200.22` →
      `ORCHESTRATOR_VM_ID=planning bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --init --slots 5 --operator planning`
      (uniform `planning` prefix via the durable fix) + `install-slot-cron-ff-pull.sh` +
      `verify-slot-host-symmetry.sh`=0. **Slot roles (operator 2026-06-05 — review ≠ CI-escalation ≠ plan-health, three
      distinct agents `review.md` / `escalate.md` / plan-health):** slot1 = Ikenna (interactive planning, Opus), slot2 =
      Harsh (interactive planning, Opus), slot3 = **review** (code review of THIS machine's slot_done output —
      `review.md` watches completed-worker commits vs the task done_definition; it is NOT a global PR reviewer), slot4 =
      **CI-escalation** (`escalate.md` — merge-conflict / SIT / label-mismatch fixes on LDR; dedicated so escalations
      never grab Ikenna's/Harsh's interactive slots), slot5 = **plan-health agent** (see next todo).
      **BLOCKED-OPERATOR-CONFIRM**: touches the live central box — awaiting operator go. Repo: `agent-orchestrator`
      (bootstrap) + the central VM. parent_epic: orchestrator_master.
- [ ] [SCRIPT] P1. **Plan-health AGENT (slot5) pinged on each LDR→main merge attempt + FF main→LDR (operator
      2026-06-05).** Distinct from the two EXISTING pieces — `plan-health-agent.yml` (daily, **report-only** digest) and
      `main-backmerge-to-ldr.yml` (deterministic `merge` + FF main→LDR on push to main). The GAP: an ACTIVE judgment
      agent the **LDR→main promotion workflow pings** (escalation-style `POST /api/escalate` with a `plan-health` role)
      so that on every main↔LDR reconciliation the plans are actively kept clean (flip/dedup/hygiene), and main is FF'd
      back to LDR cleanly. Build: (a) a `plan-health.md` (or reuse `escalate.md` with a plan-health prompt) agent role;
      (b) wire the LDR→main promote/back-merge workflow to ping it; (c) it runs on planning slot5. Repos:
      `agent-orchestrator` (agent role + ping) + `unified-trading-pm` (workflow). parent_epic: orchestrator_master.
- [ ] [INFRA] P1. **Make `ORCHESTRATOR_VM_ID=planning` durable in the central VM's provisioning** so its slots can't
      regress to a long instance-name prefix. Its user-data exports `VM_NAME="agent-orch-vm-..."` but NOT
      `ORCHESTRATOR_VM_ID`, so `bootstrap_vm.sh`'s `VM_ID=${ORCHESTRATOR_VM_ID:-${VM_NAME}}` would brand the long name.
      Add `export ORCHESTRATOR_VM_ID=planning` to the central VM's user-data before the bootstrap call (same
      VM_NAME≠VM_ID bug class fixed in setup-tab-worktrees.sh). Repo: `agent-orchestrator` / launch config. parent_epic:
      orchestrator_master.
- [x] ✅ [DOC] P1. **Fix `orchestrator_vm_registry.yaml` staleness.** SHIPPED 2026-06-05. (a) `planning-vm` entry: added
      real instance id `i-0c9b283b31d6b5ca7` + `public_ip: 13.113.200.22` (Elastic IP) + `api_url`/`fqdn`
      `api.agent-orchestrator.odum-research.com` + instance_type + the "THIS IS THE CENTRAL API VM" note + 5-slot
      composition. (b) `vm-orchestrator`: nulled the DEAD `52.193.229.193`/`api_url`, added `status: parked-stopped` +
      relabelled "Orchestrator-codebase epic VM … PARKED/stopped". `regen_vm_registry.py --check` = OK (11 vm-ids
      valid). Repo: `unified-trading-pm`. parent_epic: orchestrator_master.
- [x] ✅ [DOC] P1. **Reconcile conflicting docs so the `vm-orchestrator`-vs-central naming confusion is killed.**
      SHIPPED 2026-06-05. Swept `vm-orchestrator` + `52.193.229.193` across `codex/` + `plans/` + `agent-orchestrator/`:
      the topology SSOT (`orchestrator-multi-vm-topology.md`) was ALREADY correct ("Central API VM = Planning VM @
      13.113.200.22"); the overview + canonical-plan-flow do NOT conflate (no central/escalation claim on
      vm-orchestrator); the only live stale ref was the dead-IP row in
      `codex/05-infrastructure/agent-orchestrator-worker-topology.md` → fixed (vm-orchestrator marked parked + a
      "central = planning VM, EIP 13.113.200.22" clarifier added). Remaining 52.193.229.193 refs are in an ARCHIVED plan
      (left as-is). Repo: `unified-trading-pm`. parent_epic: orchestrator_master.
