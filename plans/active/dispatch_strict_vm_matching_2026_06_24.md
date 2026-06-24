---
title: Strict per-plan VM matching — fail-closed dispatch
parent_epic: agent_operating_framework_master
assigned_vm: harsh_pc
priority: P0
status: active
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
created: 2026-06-24
last_updated: 2026-06-24
locked_by: NA
locked_since: NA
depends_on: NA
---

# Strict per-plan VM matching — fail-closed dispatch

> **W1** of `agent_operating_framework_master`. Ships independently of the rest of the epic — it is the dispatch
> correctness fix, no dependency on the frontmatter-schema build-out (W2+).

## Problem

The local `harsh_pc` agent-orchestrator backend ingested **34 tasks**, of which only **1**
(`scripts_lifecycle_marker_rollout`) was actually assigned to `harsh_pc`; the other **33** came from ~14 data-pipeline
plans owned by `vm-tradfi`/`vm-defi`/`vm-cefi`/`vm-prediction`/`vm-sports`/`vm-ml`. Two compounding causes:

1. **Matching is non-strict by default.** `ORCHESTRATOR_REGEN_REQUIRE_VM_MATCH` defaults `False`
   (`agent-orchestrator/server/config.py:538`), so a backend ingests its own plans **plus every "global/unassigned"
   plan**.
2. **Epic→VM delegation silently resolves to "global".** Active plans carry no own `assigned_vm`; they delegate via
   `parent_epic`. But regen reads plans from a `git archive <LDR> plans/active` snapshot that omits `plans/epics/` — so
   `_resolve_plan_vms` can't read the epic's VM, returns an empty set ("global"), and every backend adopts the plan.
   (Regression of the bug the code's own docstring says was fixed 2026-06-16, re-introduced by the 2026-06-23
   LDR-snapshot change.)

## Design decisions (LOCKED — operator, 2026-06-24)

- **D1.** Strict, fail-closed matching is the enforced default: a backend ingests a plan **iff**
  `plan.assigned_vm == backend_id`. Unset/`NA` → **nobody**; mismatch → skip.
- **D2.** `assigned_vm` is mandatory per-plan; **epic→VM delegation is DROPPED for matching** (`parent_epic` stays for
  orphan-check + priority rollup only → the `plans/epics`-not-in-snapshot bug becomes moot, the matcher never reads
  epics again). **A plan's `assigned_vm` SUPERSEDES its `parent_epic`'s if they differ** (operator 2026-06-24) — not a
  conflict, not a validation error; the epic's `assigned_vm` is the epic's own rollup default, never consulted for a
  plan's dispatch.
- **D3.** `assigned_vm` valid domain = `{registry VM ids}` ∪ `{NA}`. `NA` = intentionally unassigned / future plan →
  matches no backend → not dispatched.
- **D4.** Reassignment = edit `assigned_vm`, push to LDR. Old backend prunes its **queued** tasks (already wired — prune
  shares the match gate, `regen_backlog_from_plan.py:338-346`); new backend ingests on next regen. Task ids are stable
  (`plan_ref` + item) → no id-level duplication.
- **D5.** Mid-flight reassignment is operator-managed (small effort-dup window tolerated; operator has the per-backend
  dispatched-count signal — drain first or accept the dup).
- **D6.** Down VM → manual reassignment only (agents do it, operator-gated). No automated failover, no `fallback_vm`.

### Considered & REJECTED (do not re-propose)

Per-task "claim marker" pushed to LDR at task START (a `<!--claim:backend@ts-->` tag so a reassigned backend sees
in-flight items). Correct in principle but rejected for cost: a claim commit would fire on _every task pickup
fleet-wide_, ~doubling commit volume + PR-sync CI for a dedup benefit that only materializes in the rare, operator-gated
mid-flight case. Operator-awareness (D5) covers it at zero cost. A zero-commit dashboard soft-warning on the
reassignment path is the only acceptable future upgrade — out of scope.

## Phased execution DAG

### Phase 0 — Pre-audit (no code change)

- [ ] [SCRIPT] P0. Enumerate every `plans/active/*.md`: current `assigned_vm` coverage vs the registry-valid VM ids
      (`orchestrator_vm_registry.yaml` — 13 ids incl. `harsh_pc`); list the ~20 active plans lacking own `assigned_vm`
      and the value each _should_ get (its epic's VM, or `NA` if future). Output a table into this plan's Progress Log.
      **Gate**: table present + the delegating-plan list confirmed against the registry.

### Phase 1 — Strict matcher (agent-orchestrator) [depends: P0]

- [ ] [CODE] P0. In `server/regen_backlog_from_plan.py`: `_resolve_plan_vms` returns the plan's OWN `assigned_vm` only
      (drop the `parent_epic` resolution branch — D2); matcher fail-closed on unset/`NA` (D1/D3); make strict the
      **only** mode (retire the non-strict default of `ORCHESTRATOR_REGEN_REQUIRE_VM_MATCH` in `config.py:538`). Verify
      `_prune_stale` still shares the gate so reassigned-away plans' queued tasks GC (D4). **Gate**: unit tests — match
      / mismatch / `NA` / unset all fail-closed; reassignment prunes queued + leaves dispatched/done;
      `bash scripts/quality-gates.sh` green.
- [ ] [INFRA] P0. **Immediate relief for the running `harsh_pc` box**: set strict mode + restart so the 33 mis-ingested
      tasks drop on the next regen (operator-applied on their host; queued-only prune, no data loss). **Gate**:
      `harsh_pc` backlog == only `harsh_pc`-assigned plan tasks.

### Phase 2 — Supersede-audit of prior owners [depends: P1; parallel-ok]

- [ ] [DOCS] P0. Audit `plans/active/orchestrator_v07_multi_vm_topology_2026_05_21.md` (introduced `assigned_vm`
      mandatory) + `plans/active/agent_orchestrator_backlog_state_alignment_2026_05_29.md` (backlog regen) for tasks
      overlapping this scope (VM-assignment / strict matching / regen-prune). For each overlapping task: **migrate it
      into this epic, OR confirm it's already done / not required**. Some may already be shipped (e.g. the prune gate is
      already wired). **NOT a wholesale supersede** — leave their other scope intact; add a partial-supersede banner
      pointing here only for the VM-assignment + matching scope. **Gate**: every overlapping task accounted for
      (migrated / done / not-required), banners added.

### Phase 3 — Docs [depends: P1, P2]

- [ ] [DOCS] P1. Update CLAUDE.md: the strict-matching rule (`assigned_vm == backend` iff; unset/`NA` → nobody) +
      `assigned_vm` domain = registry ∪ `NA` + the reassignment/prune model. Update the codex SSOT
      `codex/12-agent-workflow/` (regen strict-matching + reassignment/prune) — fix the docstring that claimed the
      epic-delegation path was the fix (it's now removed).

## Success criteria

- A backend ingests ONLY plans whose `assigned_vm` equals its id; `NA`/unset → nobody (proven by unit test).
- Reassignment moves queued tasks cleanly; dispatched/done untouched.
- `harsh_pc` backlog holds only `harsh_pc`-assigned tasks after the relief restart.
- Prior plans carry partial-supersede banners; overlapping tasks migrated or closed.
- CLAUDE.md + codex reflect strict matching.

## Codex SSOT updates

- `codex/12-agent-workflow/` — regen strict-matching + reassignment/prune model (correct the stale "epic-delegation is
  the fix" docstring).

## Progress Log

- 2026-06-24: Plan created as W1 of `agent_operating_framework_master` (split out of the design-capture appendix's
  Phased DAG Phases 0/1 + the supersede note). Decisions D1–D6 locked; claim-marker rejected (cost). Local AO stack
  already torn down + task state pruned during diagnosis (both backends killed, systemd disabled, tmux/dashboard killed;
  backups kept).
