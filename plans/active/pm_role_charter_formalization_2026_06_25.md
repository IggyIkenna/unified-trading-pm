---
doc_type: plan
title: PM role charter formalization (make the live orchestrator-as-PM an explicit registry row)
summary: Formalize what the agent-orchestrator already does (PM role — plan authoring → dispatch → subworker fan-out) as an explicit role-registry charter, plus codify its skills/workflows pattern; mostly making-explicit, keeps the AO flow live.
status: active
nature: design
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [role-registry, project-management, orchestrator, charter]
related: [../epics/agent_operating_framework_master.md, role_registry_schema_and_broker_mvp_2026_06_25.md]
created: 2026-06-25
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
last_updated: 2026-06-25
locked_by: NA
locked_since: NA
supersedes:
superseded_by:
depends_on: role_registry_schema_and_broker_mvp_2026_06_25
source:
---

# PM role charter formalization (make the live orchestrator-as-PM an explicit registry row)

> **W6 role instance** of `agent_operating_framework_master`, the *first* role on the spine. Mostly **making-explicit**:
> the agent-orchestrator already IS the PM role (Opus main authoring backlog + delegating to Sonnet subworkers). This
> plan writes that down as a registry charter + names its skills/workflows, so PM is a first-class registry row like
> every other role — and proves the spine without disrupting the running planning flow.

## Why

The operator's hard constraint: **keep planning going.** The orchestrator's `main.md` agent already performs the PM
role — backlog authoring from plans, blocked-queue triage, dispatch to workers, operator chat. But it is not yet a
*registry row*: there is no machine-readable charter declaring PM's model/thinking/lifecycle/triggers/escalation, and
its on-demand capabilities are not packaged as named skills. Formalizing it (a) validates the spine
(`role_registry_schema_and_broker_mvp`) against the one role we understand best, and (b) makes "ask the PM role X" a
broker lookup like any other. This is additive — the live `main.md` keeps running; we add its charter + skills around
it. SSOTs: `codex/04-architecture/agent-orchestrator-overview.md`, `codex/12-agent-workflow/canonical-plan-flow.md`,
`codex/06-coding-standards/model-tier-selection.md`.

## Locked design (operator, 2026-06-25)

- **PM is a persistent, query-answering role**: `lifecycle: persistent`, standing holder = the main agent. It answers
  "what's the plan / what's in flight / what's the priority" from warm context (cheap reads), and spawns subworkers
  (AO slots) or Workflows for heavy authoring.
- **The orchestrator pattern generalizes**: PM = Opus (or operator-tier) at the *synthesis* layer, Sonnet/Haiku at the
  *fan-out*. Skills = on-demand verbs (light JSON out); Workflows = heavy multi-step authoring (Opus only at the synth).
  This plan names PM's first skills; it does NOT rebuild the orchestrator.
- **No dispatch behavior change**: plan→`backlog.yaml`→worker stays exactly as-is (`canonical-plan-flow`). The charter
  *describes* it; it does not alter `regen_backlog_from_plan.py`.

## Phased execution DAG

### Phase 0 — PM charter row [depends: spine Phase 1]

- [ ] [DOCS] P1. Write `agent-orchestrator/agents/main.md` frontmatter as the PM registry row: `role: project_management`,
      `model`/`thinking` (per `model-tier-selection`: opus-required for cross-plan/cross-repo authoring), `lifecycle:
      persistent`, `triggers` (plan ingest tick, operator chat, blocked-queue), `does`/`does_not` on the autonomy
      gradient, `escalation_to` (operator for hard-stops), `temperament_base` (diligent — plans are robust/non-conflicting).
      **Gate**: `docspec --check` clean; loads in `role_registry.py`.

### Phase 1 — PM skills (on-demand verbs) [depends: P0]

- [ ] [CODE] P1. `/plan-status <epic|plan>` skill → light JSON `{ done, in_flight, blocked, next_p0 }` from the backlog
      + plan checkboxes (reuses `GET /api/state` + `EpicsPlans` data). **Gate**: returns valid JSON for a known epic.
- [ ] [CODE] P1. `/whats-dispatched <vm>` skill → light JSON of currently-dispatched tasks per VM (reuses backlog).
      **Gate**: matches the dashboard's dispatched count.

### Phase 2 — PM workflow (heavy authoring fan-out) [depends: P0]

- [ ] [DOCS] P1. Document the PM "subdivide-an-epic" workflow pattern (Opus synth + Sonnet fan-out over candidate
      child-plans) referencing the existing dispatch; capture it as the template other roles copy. **Gate**: pattern
      doc cross-links the spine + `canonical-plan-flow`; no new dispatch code.

## Success criteria

- `main.md` carries a valid `agent-role` charter row; the PM role is loadable + routable via the broker `(role=
  project_management, domain=*)`.
- Two PM skills return light JSON; the heavy-authoring workflow pattern is documented as the role template.
- **Zero change** to the live planning flow (regen / dispatch tests green) — verified by running the orchestrator.

## Codex SSOT updates

- `codex/04-architecture/agent-orchestrator-overview.md` — note PM as the reference role-registry row + its skills.
- `codex/04-architecture/role-registry.md` (from the spine) — add PM as the worked example.

## Progress Log

- 2026-06-25: Plan created as the first W6 role instance on the spine. Chosen first because it is lowest-risk
  (making-explicit the already-live orchestrator-as-PM) and keeps the planning flow active per the operator's hard
  constraint. Human-driven (`assigned_vm: NA`). Depends on `role_registry_schema_and_broker_mvp`.
