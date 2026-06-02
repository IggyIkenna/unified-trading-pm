---
title: Orchestrator fleet worker-spawn enablement (FM7 operator-mismatch + autospawn + VM_ID + worktree hygiene)
parent_epic: orchestrator_master
assigned_vm: vm-orchestrator
priority: P0
status: active
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
created: 2026-06-02
related_plans:
  - plans/active/agent_orchestrator_e2e_workflow_and_execution_scope_2026_06_02.md
  - plans/epics/orchestrator_master.md
---

# Orchestrator fleet worker-spawn enablement

## Context

The 2026-06-02 e2e pipeline test proved the **discovery half** works end-to-end (push plan → `pm-pull` → `PlanRegenLoop`
→ backlog), but **no VM in the fleet can currently spawn a worker** — so the execution half (dispatch → worker → flip →
push) never runs. Diagnosed live across the central, `vm-orchestrator`, a freshly-started epic VM, **and reproduced +
validated on the local orchestrator** (`agent-orchestrator.service` on `:8026`). This plan captures the reproduced root
causes and the exact per-host / per-VM changes to apply when the VMs are started.

`execution_scope: local-only` — this is operator/host bootstrap work (chicken-and-egg: the orchestrator cannot spawn a
worker to fix its own spawn path), so it must NOT be ingested by the fleet backlog.

## Root causes (reproduced 2026-06-02, local orchestrator)

### RC1 — branch operator is derived from the Claude ACCOUNT, not the worktree/host (PRIMARY)

`tab/<operator>/<N>` identifies the **host** that owns the slot worktrees. But the spawn path derives the operator from
the **account**:

- `server/autospawn.py:210` → `operator = account.operator or slot.operator or "ikenna"`
- `server/server.py` spawn endpoint → `spawn_operator = acc_def.operator`

The pre-spawn FM7 gate (`worktree_clean_check.check_slot_branch_state`) then asserts every repo's HEAD ==
`tab/{operator}/{slot_id}`. When the account's operator (`harsh` / `ikenna`) ≠ the host's worktree operator (`hk` /
`hkm` locally; `rootm` / `ikennaigboaka` on the VMs), **every repo trips `wrong_branch` (FM7) → STOP → no spawn.** This
is why autospawn logs `spawn failed … branch-state quarantine (FM5/FM7)` on the central, and why a shared/cross-operator
account can never spawn.

**Reproduced (local, slot 21 on `tab/hk/21`):**

| operator passed | source                  | gate result                                                              |
| --------------- | ----------------------- | ------------------------------------------------------------------------ |
| `harsh`         | `harsh-primary` account | should_stop=True, **25/25 repos wrong_branch** (`expected tab/harsh/21`) |
| `ikenna`        | sub-\* accounts         | should_stop=True, 25/25 wrong_branch                                     |
| `hk`            | the actual worktree     | passes the operator check (then only the RC4 staleness remained)         |

**Proven green case (local, slot 1 on `tab/hkm/1`, operator `hkm`):** `should_stop=False`, **all 23 repos `ff_done`** —
a worker WOULD spawn. This is the success target.

### RC2 — per-VM `ORCHESTRATOR_VM_ID` is `unknown-vm` (assigned_vm routing broken)

The epic VMs and `vm-orchestrator` report `ORCHESTRATOR_VM_ID=unknown-vm` instead of their canonical id (`vm-cefi`,
`vm-defi`, …). So `assigned_vm:`-routed plans never reach the right VM (only global plans do), and multiple VMs sharing
`unknown-vm` collide on the same global tasks. (The central correctly reports `vm-0`.)

### RC3 — autospawn defaults OFF

`ORCHESTRATOR_AUTOSPAWN_ENABLED` defaults to false (`server/autospawn.py:18,338`; boot logs `AutoSpawnLoop disabled`).
`vm-orchestrator` and the local host have it unset → even a correctly-configured slot never auto-spawns. (The central
had it `true`, which is why it was _attempting_ spawns and failing on RC1.)

### RC4 — stale + dirty slot worktrees block the FF/branch-state gate

Even with the correct operator, slots fail if worktrees are behind upstream with uncommitted local changes (local slot
21: `behind 231 but ff-only merge failed: local changes would be overwritten`) or have stray repos left on the base
branch (local slot 2: 2 of 23 repos on `live-defi-rollout` instead of `tab/hkm/2`). The `slot-cron-ff-pull` must keep
them clean + current; dirty WIP must be committed/stashed (never blind-discarded — inherited-WIP rule).

### RC5 — operator naming is inconsistent within a host

A single host should have ONE operator. Locally worktrees mix `hk` (slots 21–28) and `hkm` (slots 1–2); VMs use `rootm`
and `ikennaigboaka`. Standardize one operator per host and brand all that host's worktrees `tab/<operator>/<N>`.

## Fixes

### F1 — code: decouple the branch operator from the account [P0]

The branch operator must come from the host/slot, not the Claude account (which is only for auth). Recommended:

- Resolve operator as
  `slot.operator or ORCHESTRATOR_OPERATOR (host env) or <derive from worktree HEAD> or account.operator` — i.e.,
  **prefer the worktree/host operator; account.operator becomes the last resort**. Apply in BOTH `autospawn.py:210` and
  the `server.py` spawn endpoint (`spawn_operator`).
- Populate `slot.operator` at slot-registration/bootstrap time from the `--operator` used to create the worktrees, so it
  is never `None`.
- Keep FM7 as-is (it correctly verifies all repos share `tab/<operator>/<N>`); only the _source_ of `operator` changes.

Blast radius: this gate runs on every spawn fleet-wide → land behind `scripts/check.sh` + a unit test that asserts a
worktree on `tab/hk/N` spawns under account `harsh-primary` (operator `harsh`). Owner: agent-orchestrator (sole-owned).

- [x] ✅ [SCRIPT] P0. **DONE — agent-orchestrator@cfece08.** Added `config.host_operator()` (resolution:
      `ORCHESTRATOR_OPERATOR` > `ORCHESTRATOR_VM_ID` > `slot.operator` > OS-user > `account.operator`); wired into
      `autospawn.py:210` + `server.py` spawn endpoint (`spawn_operator`). 7 unit tests (`tests/test_host_operator.py`);
      ruff + basedpyright `server/` 0/0 green (tsc N/A — server-only change). **Validated live**: with the fix the
      resolver returns `hk` (the host) not `harsh` (the account), and slot 21's FM7 `wrong_branch` count dropped **25/25
      → 0/25** — RC1 fixed. Note: `slot.operator` bootstrap-population was NOT needed (the `VM_ID`/OS-user fallback
      covers a `None` slot.operator), so it's dropped from scope rather than deferred.

### F2 — per-VM config: fix `ORCHESTRATOR_VM_ID` [P0]

- [x] ✅ [INFRA] P0. **Baked into the scripts + validated.** `bootstrap_vm.sh` (agent-orchestrator@129dc6a) now UPSERTs
      `ORCHESTRATOR_VM_ID` from the launcher's short canonical id (fixes stale `unknown-vm`); the launchers
      (deployment-service@eaccd8d) `export ORCHESTRATOR_VM_ID=${vm_id}` into bootstrap's env (AWS + GCP). **Verified on
      vm-cefi** (VM_ID set, regen ingested the test plan). **Per-VM fleet rollout** to the 9 stopped epic VMs +
      vm-orchestrator is automatic on each VM's next re-bootstrap — pending because the fleet is intentionally OFF
      (operator). Existing stopped VMs need a re-bootstrap (or the manual upsert I did on vm-cefi) to clear their stale
      `unknown-vm`.

### F3 — per-host config: enable autospawn [P0]

- [x] ✅ [INFRA] P0. `bootstrap_vm.sh` now upserts `ORCHESTRATOR_AUTOSPAWN_ENABLED=true` (@129dc6a). Epic VMs already
      had it `true` (systemd) — `vm-orchestrator` + the local host were the only gaps. Confirmed live:
      `AutoSpawnLoop started` then `spawned=2 failed=0` on vm-cefi (was `failed=8` FM7-quarantine before the fix).

### F4 — worktree hygiene + operator standardization [P0]

- [x] ✅ [INFRA] P0. `bootstrap_vm.sh` brands ALL slot worktrees uniformly `tab/<VM_ID>/<slot>`
      (`MAIN_PREFIX=WORKER_PREFIX=VM_ID`, dropping the `+m` main/worker split) so they match `host_operator()==VM_ID`
      (@129dc6a). **Validated on vm-cefi**: rebranded `tab/rootm/N → tab/vm-cefi/N`, gate `should_stop=False` (20 ok / 1
      ff_done). Per-VM rebrand auto-applies on re-bootstrap; the FF/clean part is handled by the existing
      `slot-cron-ff-pull` + the gate's FF-repair (unchanged).

### F5 — validation gate [P0]

- [x] ✅ [INFRA] P0. **Validated end-to-end on vm-cefi 2026-06-02.** Gate `should_stop=False` (slot 1); autospawn
      `spawned=2 failed=0`; a worker completed the FULL loop — execute → flip checkbox → push to LDR (`64901d5ef`).
      Discovery half independently confirmed (push → pm-pull → regen → backlog `vm_pipeline_e2e_test-001` queued). The
      local one-shot also pushed its marker (`5ab77fc0c`). Pipeline green discovery→execution. (Test plan removed +
      vm-cefi stopped afterward; the premature flip a worker made was reverted @de9644c7f.)

## Per-VM application runbook (when a VM is started)

1. `ORCHESTRATOR_VM_ID=<canonical>` + `ORCHESTRATOR_AUTOSPAWN_ENABLED=true` in `.env.local`; `systemctl restart`.
2. Standardize the VM's operator; realign all slot worktrees to `tab/<operator>/<N>`, clean + FF-current.
3. Confirm the F1 code fix is deployed (AO on LDR HEAD with the operator-decoupling commit).
4. Run F5 validation; then the VM auto-executes its `assigned_vm` backlog.

## Validation evidence (local, 2026-06-02)

- Reproduced RC1 via `worktree_clean_check.check_slot_branch_state` directly: account operator → 25/25 `wrong_branch`.
- Proven green: slot 1 (`tab/hkm/1`, operator `hkm`) → `should_stop=False`, 23/23 `ff_done`.
- RC2/RC3 confirmed from `.env.local` + boot logs (`unknown-vm`, `AutoSpawnLoop disabled`).
- RC4 confirmed: slot 21 `behind 231 + ff-only failed`; slot 2 has 2 repos on `live-defi-rollout`.

## Full-execution criterion

A started VM, after the runbook, auto-ingests its `assigned_vm` plans AND spawns a worker that executes a task, flips
the checkbox, and pushes to `live-defi-rollout` — verified by the `orchestrator_pipeline_e2e_test` round-trip going
green through the execution half (not just discovery).
