---
title:
  "Orchestrator topology — split the merged Central/Planning VM into a Central-Orchestrator VM + a dedicated Human
  Planning VM"
created: 2026-06-12
parent_epic: orchestrator_master
assigned_vm: planning
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
status: active
locked_by: live-defi-rollout
source:
  - operator decision 2026-06-12 — "one VM for humans (Ikenna + Harsh), another for the VM playing agent orchestrator
    (CI escalation etc.)"
---

# Orchestrator human / central VM split (2026-06-12)

**Supersedes** the archived `planning_vm_canonical_bringup_and_topology_reconcile_2026_06_05.md`, which had merged the
human planning role and the central API role onto ONE VM ("Central API VM == Planning VM"). Operator 2026-06-12: split
them so human interactive planning does not share a host with the CI-escalation / plan-health / AutoSpawn machinery.

## Canonical topology (post-split)

| VM                         | registry id            | instance                                                   | role       | runs                                                                                                                                                                                                                                                                      |
| -------------------------- | ---------------------- | ---------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Central / Orchestrator** | `planning` (legacy id) | `i-0c9b283b31d6b5ca7` / `13.113.200.22` (EIP), m8i.4xlarge | `central`  | the API everything pings (`api.agent-orchestrator.odum-research.com`, nginx :443 → :8765), CI-escalation (`/api/escalate`), plan-health (`/api/plan-health/dispatch`), AutoSpawn for agent workers, review. **NO human daily work.** Only this VM's health/alerts matter. |
| **Human Planning**         | `human-planning`       | `i-0dd9812a96cdda5dc` / `35.76.120.160`, m7i.2xlarge       | `planning` | Ikenna (slot1) + Harsh (slot2) interactive only (`tab/human-planning/N`). Local backend self-registers with central; owns NO EIP/DNS/central-API. `ORCHESTRATOR_REGEN_REQUIRE_VM_MATCH=true` → never auto-adopts fleet/global plans. `ssh human-planning-vm`.             |

**Why the central role stays on `i-0c9b283b31d6b5ca7`**: it holds the Elastic IP + DNS + the hand-wired secrets (incl.
`ORCHESTRATOR_INTERNAL_SECRET`). Re-homing the central role would mean re-pointing the EIP + DNS + re-wiring secrets for
zero benefit and real risk. So the human role is the one that moved to a fresh box.

**Why the legacy id `planning` stays on the central VM**: its runtime `ORCHESTRATOR_VM_ID=planning` is hand-wired and
drives `tab/planning/N` + regen scoping; renaming it would orphan live operator sessions. The id is a documented legacy
artifact — the central VM is NOT the human box (that is `human-planning`).

## No-disruption migration (operator does step 4 at their own pace)

- [x] [INFRA] P0. Provision the human VM —
      `launch-orchestrator-worker-vm.sh --vm-id human-planning --role planning     --slots 2 --instance-type m7i.2xlarge --lifecycle long-running --env ORCHESTRATOR_REGEN_REQUIRE_VM_MATCH=true`.
      **DONE 2026-06-12 — `i-0dd9812a96cdda5dc` / `35.76.120.160`; bootstrap complete ~3 min; `verify_vm_e2e.sh` = PASS
      (8/8: running · SSM · bootstrap · backend :8765 healthy · pm-pull timer · main-agent tmux live · strict-scoping 0
      tasks · 3 accounts).**
- [x] [SCRIPT] P0. Registry + SSH config: split `planning` → `central` + add `human-planning`; `~/.ssh/config` host
      `human-planning-vm → 35.76.120.160`. **DONE 2026-06-12 — `orchestrator_vm_registry.yaml`; `regen --check` green
      (11 vm-ids).**
- [x] [DOC] P0. Align topology docs (no regression): CLAUDE.md "LIVE orchestrator",
      `codex/04-architecture/     agent-orchestrator-overview.md`,
      `codex/05-infrastructure/agent-orchestrator-worker-topology.md`,
      `codex/12-agent-workflow/orchestrator-multi-vm-topology.md`, `plans/epics/orchestrator_master.md`. **DONE
      2026-06-12.**
- [ ] [OPERATOR] P1. **Migrate at your pace** (no forced session loss — provisioning did NOT touch the central VM): on
      the central VM, commit/push the WIP in your 2 open Claude Code tabs, then close them; `ssh human-planning-vm` and
      resume interactive work there (`setup-tab-worktrees.sh` already ran for slots 1-2). The central VM keeps serving
      throughout.
- [ ] [SCRIPT] P2. Once humans are off the central VM, free its slots 1-2 for AutoSpawn agent workers (or leave idle).
      Optional cleanup — no urgency.

## Verification

- [x] Human VM serves + is isolated + main-agent-attended (`verify_vm_e2e.sh` PASS).
- [ ] Central orchestrator shows `human-planning` registered (after the registry reaches `main` → central `pm-pull`).
- [ ] QG runs green on a human-VM slot (interactive parity with a laptop slot).
- [ ] [DOC] P3. SPLITPINGSENTINEL20260612 — orchestrator-pickup smoke: confirm the central PlanRegenLoop ingests this
      line into the backlog (proves the split didn't break plan→backlog regen). Remove after the orchestrator picks it
      up.

## Codex SSOT updates

`codex/04-architecture/agent-orchestrator-overview.md` · `codex/05-infrastructure/agent-orchestrator-worker-topology.md`
· `codex/12-agent-workflow/orchestrator-multi-vm-topology.md` — all updated to the two-VM split (see DOC P0 above).
