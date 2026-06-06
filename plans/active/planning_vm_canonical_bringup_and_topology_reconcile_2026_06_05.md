---
title: Planning-VM canonical bring-up + multi-VM topology reconciliation
parent_epic: orchestrator_master
assigned_vm: planning
priority: P1
status: active
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
created: 2026-06-05
locked_by: live-defi-rollout
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
- [x] ✅ [INFRA] P1. **Provision 5 interactive planning slots on the central VM as `tab/planning/N`.** SHIPPED
      2026-06-05 (clean re-provision of the live central VM, `i-0c9b283b…`/`13.113.200.22`). Done: backed up
      `.env.local`/`backends.json`/`state.db`; stopped orchestrator; killed the 5 `orch-slot-*` workers; set
      `ORCHESTRATOR_VM_ID=vm-0→planning` + `ORCHESTRATOR_VM_ROLE=epic→planning` in `.env.local`; renamed
      `ikenna-vm→planning` in `backends.json`; tore down all **489** `tab/vm-0/*` worktrees; re-init **5** slots
      `tab/planning/1-5` (uniform `planning` prefix, `.worktree-identity.conf` persisted) + ff-pull cron; restarted
      orchestrator. **VERIFIED**: API `/health`=200 on the EIP, backend `VM_ID=planning ROLE=planning`, 5 slots, 0
      `vm-0` worktrees left, orphan remote `tab/vm-0/10` deleted. No backlog auto-assign (ROLE=planning + no plans
      `assigned_vm: planning` → empty backlog → humans drive; escalation+plan-health remain ping-driven). **It WAS a
      rename** from the 3-named box (`planning-vm` / `vm-0` / "Central API VM" / `ikenna-vm`). Original detail: SSH into
      `13.113.200.22` →
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
- [x] ✅ [SCRIPT] P1. **Plan-health agent triggered on each LDR→main reconciliation.** SHIPPED 2026-06-05 — RECONCILED
      with existing work (avoided a duplicate): the plan-health AGENT + dispatch ALREADY existed on LDR
      (`agent-orchestrator/server/plan_health.py` + `agents/plan-health.md` + `POST /api/plan-health/dispatch`, the
      `$0`-API Max-plan-slot cross-plan-contradiction + governance-doc-drift detector). Its header said it was "BUILT
      but only runs once the planning-VM orchestrator is live" — which THIS plan's re-provision just made true (5 live
      planning slots). The only GAP was the on-merge trigger: wired `main-backmerge-to-ldr.yml` (PM-only step, gated on
      `decision != noop`) to `POST /api/plan-health/dispatch` after each main↔LDR back-merge, so the agent runs on every
      LDR→main reconciliation (not just the daily cron) and the plans stay clean as the branches sync. The FF main→LDR
      itself is the deterministic back-merge job (already there). I dropped my initial escalation.py
      `wall_type=plan_health` duplicate in favour of the existing `/api/plan-health/dispatch`. Repos:
      `unified-trading-pm` (workflow template + copy). parent_epic: orchestrator_master.
- [x] ✅ [INFRA] P1. **Make `ORCHESTRATOR_VM_ID=planning` durable in the central VM's provisioning.** SHIPPED 2026-06-05
      at the PROVISIONING SOURCE (no live-API outage): `deployment-service/scripts/vm/launch-planning-vm.sh` now
      `export ORCHESTRATOR_VM_ID=planning` in the startup script before `bootstrap_vm.sh` + bumped `--slots 2 → 5`, so a
      fresh planning-VM launch brands `tab/planning/N` instead of falling back to the dated `VM_NAME`
      (`agent-orch-planning-vm-YYYYMMDD`) — the `VM_ID=${ORCHESTRATOR_VM_ID:-${VM_NAME}}` bug. **Deliberately did NOT
      stop the live AWS box to edit its instance user-data**: that user-data runs ONCE at first launch (so editing it
      changes nothing for this instance) and the running box is already `planning` via `.env.local` +
      `.worktree-identity.conf` (survives reboots) — a fresh launch uses the LAUNCHER, not the old instance's user-data,
      so fixing the launcher is the real durable fix and an outage would be pure cost. **Residual (optional, no urgency)
      — CORRECTED 2026-06-05:** the live central box is NOT a repurposed epic (earlier note conflated it with the
      STOPPED epic `vm-orchestrator`/`i-007e8d99`). It is a DEDICATED central box — AWS Name `agent-orchestrator-vm-1`,
      role tag `ikenna-brain`, `i-0c9b283b…` — with no scripted launcher (provisioned manually/one-off; no
      `launch-brain.sh`). So an epic-VM launch CANNOT collide with it: `launch-epic-vm-aws.sh --vm-id vm-defi` makes a
      SEPARATE instance `agent-orch-vm-defi-<date>` (own `ORCHESTRATOR_VM_ID=vm-defi` → `tab/vm-defi/N`),
      singleton-locked on `agent-orch-vm-defi-*` which never matches `agent-orchestrator-vm-1`. **Gap RESOLVED
      2026-06-05:** wrote `deployment-service/scripts/vm/launch-central-brain-aws.sh` (modeled on
      `launch-epic-vm-aws.sh`) — canonical from-scratch relaunch of the central box: fixed Name
      `agent-orchestrator-vm-1` + role tag `ikenna-brain` + singleton-locked on `agent-orchestrator-vm-` (one brain),
      `m8i.4xlarge`/60GB, user-data `export ORCHESTRATOR_VM_ID=planning` → `bootstrap_vm.sh --role planning --slots 5`,
      installs nginx, and **auto-re-associates the EIP** (`eipalloc-07b7bfe509d63c477` / 13.113.200.22)
      post-`instance-running` (DNS stays valid). `--dry-run`/`--force` supported; `bash -n` + `shellcheck -S error`
      clean. Documented prereqs (prebaked AMI with nginx+cert, and keeping the `ORCHESTRATOR_ENV_LOCAL` Secrets-Manager
      secret's `ORCHESTRATOR_VM_ID=planning` in sync — bootstrap fetches that for the running backend id). Repo:
      `deployment-service`. parent_epic: orchestrator_master.
- [ ] [SCRIPT] P2. **BLOCKED-OPERATOR-DECISION: shared planning-VM per-operator commit attribution — Harsh's slots
      masquerade as Ikenna.** DISCOVERED 2026-06-05: `agent-orchestrator-vm-1` is genuinely SHARED — Harsh's
      `harsh-primary` Claude account (operator=harsh) drives its slots alongside Ikenna's three (`sub-a-ikenna` /
      `sub-b-iggy2london` / `sub-c-ikenna-odum`); registry design is slot1=Ikenna, slot2=Harsh interactive. BUT all 5
      slot worktrees commit as `ikennaigboaka [slot-N·planning] <ikennaigboaka@gmail.com>` (AWS role tag `ikenna-brain`,
      GCP label `operator=ikenna`) → Harsh's interactive planning on the box is git-attributed to Ikenna, violating the
      commit-attribution HARD RULE (Harsh's work masquerading as Ikenna). ROOT: the identity mechanism is per-MACHINE
      (one canonical id per host — correct for laptops ikennaigboaka/hk, wrong for a shared box), with no
      per-slot/per-operator notion; and the accounts are NOT slot-pinned (`pinned_slot: -`), so even cost attribution
      isn't operator-stable per slot. FIX MODELS (operator picks): **(a) per-slot operator map** — pin slot1→Ikenna /
      slot2→Harsh, `setup-tab-worktrees.sh` sets each slot's `--worktree user.name/email` to its operator + pin
      `harsh-primary` to slot2 in `accounts.json` (simple, but Harsh is fixed to slot2); **(b) per-account identity** —
      the worker derives git identity from the driving account's `operator` field at spawn (most correct: attribution
      follows whoever actually drives, any slot); **(c) accept** — the shared box stays Ikenna-attributed, per-operator
      attribution happens only on each operator's own laptop. Also fix slot4's stale `·laptop` host tag → `·planning`.
      Repo: `unified-trading-pm` (`scripts/dev/setup-tab-worktrees.sh`) + `agent-orchestrator` (accounts/spawn).
      parent_epic: orchestrator_master.
- [x] ✅ [DOC] P2. **Align the registry id `planning-vm` → `planning`** to match the running
      `ORCHESTRATOR_VM_ID=planning` + the `tab/planning/N` branches. SHIPPED 2026-06-05: renamed the
      `orchestrator_vm_registry.yaml` `id:` + every live `assigned_vm: planning-vm` ref (this plan +
      `master_to_live_defi_2026_05_23.md` (frontmatter-only edit; lock blocks archival not edits) + the
      `plan_hygiene_master.md` epic) + the id-refs in `codex/12-agent-workflow/orchestrator-multi-vm-topology.md` +
      `epic-keyword-surface.yaml`, and updated the historical note in `agent-orchestrator-worker-topology.md`.
      **Preserved** the `launch-planning-vm.sh` script-name refs in `vm-tarball-deployment.md` (those are filenames, not
      the id). `regen_vm_registry.py --check` = OK (11 vm-ids valid). The last name-mismatch is closed: registry id ==
      `ORCHESTRATOR_VM_ID` == branch prefix == `planning`. Repo: `unified-trading-pm`. parent_epic: orchestrator_master.
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
