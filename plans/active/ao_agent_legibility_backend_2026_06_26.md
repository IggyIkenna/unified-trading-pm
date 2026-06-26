---
doc_type: plan
title:
  AO agent legibility + role-dispatch — backend (kind roster · role-dispatch wiring · per-agent fields · dispatch fixes
  · resume)
summary:
  Backend half of agent legibility — clean the kind roster (remove recovery_audit, escalate→cicd, schematize
  main/review), wire role-dispatch (`assigned_role` → boot prompt + model), expose every agent's source/task/plan/role +
  full log + the activity query via the API, fix the stand-up dispatch bugs, and verify session-resume. This is the data
  layer the fleet dashboard UI renders, plus the keystone that makes the craft-role boot prompts functional.
status: active
nature: design
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, agent-kinds, observability, dispatch, session-resume, backend]
related:
  [
    ao_blocked_questions_backend_2026_06_26.md,
    ao_dashboard_fleet_ui_2026_06_26.md,
    ../epics/orchestrator_master.md,
    ../../codex/12-agent-workflow/work-philosophy.md,
    ../../codex/04-architecture/agent-orchestrator-overview.md,
  ]
created: 2026-06-26
parent_epic: orchestrator_master
assigned_vm: harsh_pc
assigned_role: backend-engineer
drift_direction: advance-code
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4
last_updated: 2026-06-26
locked_by: live-defi-rollout
locked_since: 2026-06-26
supersedes:
superseded_by:
depends_on:
source:
---

# AO agent legibility — backend

> **Backend lane** of the AO agent-observability + kind-fixes work — a work-philosophy **L4** role split into 4 plans
> (DAG: 1→3 · 2→4). The fleet-UI plan (`ao_dashboard_fleet_ui`) depends on the fields this exposes. Durable rules:
> `codex/12-agent-workflow/work-philosophy.md`; this is the work-order.
>
> **Cross-epic:** this plan's `parent_epic` is `orchestrator_master` (the runtime), but it also carries the
> `agent_operating_framework_master` **KEEP keystone** — the role-dispatch wiring (`assigned_role` → boot prompt +
> model) + schematizing `main`/`review`. The two epics overlap by design (runtime vs operating-model); see
> `plans/epics/agent_operating_framework_master.md` (2026-06-26 re-scope banner).

## Kind roster

- [ ] [CODE] P0. Remove the `recovery_audit` kind end-to-end — delete `agents/recovery-audit.md`, its `agent_kind`
      references, the `NEVER_LAUNCH` frozenset entry, and any dashboard/escalation mapping. **Gate**:
      `rg recovery.?audit` clean; agent-keeper/escalation tests green.
- [ ] [CODE] P0. Rename agent kind `escalate` → `cicd` — `agents/escalate.md`→`cicd.md`, the `escalation.py` CI-wall
      `agent_kind` map, the kind value, dashboard label "CICD". **Gate**: a CI-wall escalation registers
      `agent_kind=cicd`; no `"escalate"` kind remains.
- [ ] [DOCS] P0. Reframe the CICD charter in `cicd.md`: resolves **#ci-failures** Slack alerts; cross-link the
      alerting-service route. **Gate**: boot prompt states the #ci-failures scope.

- [ ] [DOCS] P1. **Schematize `main.md` + `review.md` as agent-role docs** — both have no frontmatter today. Add the
      `agent-role` frontmatter block (`doc_type`/`role`/`model`/`thinking`/`lifecycle`/`does`/`does_not`/`triggers`,
      mirroring the craft-role boot prompts) so the operational roles are first-class in the registry + render their
      `role` in the fleet/tabs UI. These are operational (not craft) roles — lighter than the craft set. **Gate**:
      `docspec --check agents/main.md agents/review.md` hard=0; both expose `role` + `model`.

## Per-agent fields (API)

- [ ] [CODE] P0. Add a **`plan_ref` column** to the slot/agent row + populate from the dispatched task's `plan_ref`
      (`bootstrap.py` migration). **Gate**: a dispatched worker row has `plan_ref` = its plan path; migration
      idempotent.
- [ ] [CODE] P0. Populate **`current_task`** for ALL fleet agents (`worker`, `cicd`, `data_pipeline_failure`,
      `plan_health`, `monitor`) at spawn/dispatch — backend-owned. **Gate**: every live fleet agent has non-null
      `current_task`.
- [ ] [CODE] P0. Per-kind **`source`/`task`/`role` serialization** in the agents/slots API: `cicd`→repo/PR ·
      `data_pipeline_failure`→alert/asset-group · `plan_health`→"plan health"/finding · `worker`→plan/task_id. `role`
      (the `agents.role` column) populated for every fleet agent — craft for workers (from `assigned_role`), kind for
      the rest. **Gate**: the agents API returns source/task/role per kind.
- [ ] [CODE] P0. **Full-log endpoint** returns the COMPLETE agent log capture for ANY state (running/stale/killed) —
      today it returns only the first boot-prompt chunk. **Gate**: the endpoint returns the full capture (> boot prompt)
      for a killed agent.
- [ ] [CODE] P1. **Activity query**: datetime-range filter (default **last 2h**), `limit` default **100** (up from 50),
      event-type include/exclude filter, cursor pagination, + a **maintained signal-vs-noise event set** (noise =
      `agent_replied`/`agent_message_sent`/`tmux_session_lost`/`session_checkpoint`/`agent_registered`/`agentkeeper_*`).
      **Gate**: `GET /api/activity?since=…&until=…&limit=…&exclude=…` returns windowed/filtered/paginated rows; a new
      plumbing event is in the noise set.

## Role-dispatch wiring (`assigned_role` → boot prompt + model — the keystone)

> Reuses the `assigned_role` parse the role-column task above already adds. This is the
> `agent_operating_framework_master` KEEP-item ("AO dispatch reads `assigned_role` → boot prompt + model, no broker")
> landing in the AO runtime — today `assigned_role` is referenced nowhere in `server/`, so the craft-role boot prompts
>
> - plan `assigned_role` tags are inert until this lands. Fail-soft: `assigned_role` unset / role file missing → today's
>   generic boot + default model (no regression).

- [ ] [CODE] P0. **Boot-prompt injection** — when a dispatched task's plan carries `assigned_role`, prepend
      `agents/<assigned_role>.md` to the worker's spawn prompt (alongside the inherited `worker.md` + `RULES.md`), so
      the worker boots its craft role. **Gate**: a worker dispatched from a plan with `assigned_role: backend-engineer`
      has the backend-engineer boot prompt in its spawn context; an unset plan boots the generic worker unchanged; unit
      test.
- [ ] [CODE] P0. **Model/thinking from the role** — read `model`/`thinking` from `agents/<assigned_role>.md` frontmatter
      and apply them to the spawned worker, overriding the default per-task derivation; `assigned_role` unset or role
      file absent → the existing default. **Gate**: a `backend-engineer`-assigned task spawns a `sonnet`/`medium` worker
      per the role frontmatter; an unset task keeps today's default; unit test.

## Dispatch fixes + resume (found during stand-up)

- [ ] [CODE] P1. Fix **`/api/backlog` HTTP 500** — the dashboard backlog view can't render. **Gate**: `GET /api/backlog`
      returns 200 with the task list.
- [ ] [CODE] P1. **Don't dispatch operator-deferred tasks** — briefs marked
      `DEFER`/`DEFERRED`/`NICE-TO-HAVE`/`OPTIONAL`/ `LATER` (e.g. `cicd_consolidated_remaining-037` is P0 yet
      "DEFERRED-AWS — leave as-is") are dispatched because they aren't `blocked`. Honor the marker at regen/dispatch.
      **Gate**: a DEFERRED-marked task is not dispatched; unit test.
- [ ] [VERIFY] P1. **Verify `claude_session_id` `--resume` restores context** across a failover / account-switch restart
      (D3). **Gate**: spawn → kill → resume on a different account → same session continues the task with prior context.
- [ ] [DOCS] P2. **Flag the oversized backlog plan** (`cicd_consolidated_remaining` = 73 tasks) to the operator as a
      split candidate (work-philosophy L3/L8). **Gate**: a split-candidate note filed; operator acked.

## Handoff

- [ ] [DELEGATED] P1. **`monitor` boot prompt — owned by Ikenna.** `monitor` extends the VM-health/heartbeat watchdog;
      Ikenna populates `agents/monitor.md` + its `source`/`task` semantics. **Gate**: `monitor.md` finalized by Ikenna.

## Success criteria

- Roster clean (no `recovery_audit`; `cicd` scoped to #ci-failures); every agent exposes source/task/plan/role + a full
  log via the API; activity query windowed + denoised; `/api/backlog` 200; deferred tasks don't dispatch; resume proven.
- **Runtime-verified on the local `harsh_pc` AO.**

## Codex SSOT updates

- `codex/04-architecture/agent-orchestrator-overview.md` — cleaned kind roster, the per-kind source/task/role contract,
  the `plan_ref` field, the activity noise-set.

## Progress Log

- 2026-06-26: Split from the AO-observability tracker (backend lane). `assigned_vm: harsh_pc`,
  `assigned_role: backend-engineer`. Unblocks `ao_dashboard_fleet_ui`.
