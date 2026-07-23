---
doc_type: plan
title: PM role charter formalization (make the live orchestrator-as-PM an explicit registry row)
summary:
  Formalize what the agent-orchestrator already does (PM role — plan authoring → dispatch → subworker fan-out) as an
  explicit role-registry charter, plus codify its skills/workflows pattern; mostly making-explicit, keeps the AO flow
  live.
status: complete
nature: design
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [role-registry, project-management, orchestrator, charter, archived]
related:
  [
    ../epics/agent_operating_framework_master.md,
    /plans/archive/2026_07/role_registry_schema_and_broker_mvp_2026_06_25.md,
  ]
created: 2026-06-25
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
last_updated: 2026-07-16
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: role_registry_schema_and_broker_mvp_2026_06_25
source:
assigned_role: backend_engineer
drift_direction: advance-code
---

# PM role charter formalization (make the live orchestrator-as-PM an explicit registry row)

> **🗄️ ARCHIVED 2026-07-16 — core delivered + live (operator decision).** The PM charter (Phase 0) is DONE and in daily
> use: `unified-trading-pm/agents/main.md` carries the full `agent-role` registry row (`role: project_management`,
> `model: opus`, `thinking: high`, `lifecycle: persistent`, triggers/does/does_not/escalation_to/temperament_base),
> loads in `role_registry.py`, and is `docspec`-green (schema SSOT `scripts/docs/docspec.py`; `role-registry.md` codex
> doc deleted 2026-07-16). Phase 1 skills shipped at **MVP** (`/plan-status` + `/whats-dispatched` documented as
> boot-prompt commands in `main.md § Available skills`); the Phase 2 decompose/fan-out pattern is documented in
> `main.md` (Cold-start + Overnight sections). The remaining "fuller" scope — backend light-JSON skill endpoints + a
> standalone workflow-template doc — is **NOT REQUIRED**: it's the deferred "real skill-dispatch framework", and this
> plan is one of the 4 role pilots `agent_operating_framework_master` defers to next quarter.

> **W6 role instance** of `agent_operating_framework_master`, the _first_ role on the spine. Mostly **making-explicit**:
> the agent-orchestrator already IS the PM role (Opus main authoring backlog + delegating to Sonnet subworkers). This
> plan writes that down as a registry charter + names its skills/workflows, so PM is a first-class registry row like
> every other role — and proves the spine without disrupting the running planning flow.

## Why

The operator's hard constraint: **keep planning going.** The orchestrator's `main.md` agent already performs the PM role
— backlog authoring from plans, blocked-queue triage, dispatch to workers, operator chat. But it is not yet a _registry
row_: there is no machine-readable charter declaring PM's model/thinking/lifecycle/triggers/escalation, and its
on-demand capabilities are not packaged as named skills. Formalizing it (a) validates the spine
(`role_registry_schema_and_broker_mvp`) against the one role we understand best, and (b) makes "ask the PM role X" a
broker lookup like any other. This is additive — the live `main.md` keeps running; we add its charter + skills around
it. SSOTs: `/codex/04-architecture/agent-orchestrator-overview.md`, `/codex/12-agent-workflow/canonical-plan-flow.md`,
`/codex/06-coding-standards/model-tier-selection.md`.

## Locked design (operator, 2026-06-25)

- **PM is a persistent, query-answering role**: `lifecycle: persistent`, standing holder = the main agent. It answers
  "what's the plan / what's in flight / what's the priority" from warm context (cheap reads), and spawns subworkers (AO
  slots) or Workflows for heavy authoring.
- **The orchestrator pattern generalizes**: PM = Opus (or operator-tier) at the _synthesis_ layer, Sonnet/Haiku at the
  _fan-out_. Skills = on-demand verbs (light JSON out); Workflows = heavy multi-step authoring (Opus only at the synth).
  This plan names PM's first skills; it does NOT rebuild the orchestrator.
- **No dispatch behavior change**: plan→`backlog.yaml`→worker stays exactly as-is (`canonical-plan-flow`). The charter
  _describes_ it; it does not alter `regen_backlog_from_plan.py`.

## Phased execution DAG

### Phase 0 — PM charter row [depends: spine Phase 1]

- [x] ✅ [DOCS] P1. Write `unified-trading-pm/agents/main.md` frontmatter as the PM registry row:
      `role: project_management`, `model`/`thinking` (per `model-tier-selection`: opus-required for
      cross-plan/cross-repo authoring), `lifecycle:     persistent`, `triggers` (plan ingest tick, operator chat,
      blocked-queue), `does`/`does_not` on the autonomy gradient, `escalation_to` (operator for hard-stops),
      `temperament_base` (diligent — plans are robust/non-conflicting). **Gate**: `docspec --check` clean; loads in
      `role_registry.py`. — DONE `agent-orchestrator@acbf930`/`@c9184b4`: `main.md` carries the full agent-role charter
      (`temperament_base` shipped as `decisive`); `role_registry.load_registry()` validates it; docspec-green.

### Phase 1 — PM skills (on-demand verbs) [depends: P0]

- [ ] [CODE] P1. `/plan-status <epic|plan>` skill → light JSON `{ done, in_flight, blocked, next_p0 }` from the
      backlog + plan checkboxes (reuses `GET /api/state` + `EpicsPlans` data). **Gate**: returns valid JSON for a known
      epic. — MVP-DONE as a documented boot-prompt command (`main.md § Available skills`); the backend light-JSON
      endpoint is deferred (real skill-dispatch framework). NOT REQUIRED for archival.
- [ ] [CODE] P1. `/whats-dispatched <vm>` skill → light JSON of currently-dispatched tasks per VM (reuses backlog).
      **Gate**: matches the dashboard's dispatched count. — MVP-DONE as a documented boot-prompt command
      (`main.md § Available skills`); the backend light-JSON endpoint is deferred. NOT REQUIRED for archival.

### Phase 2 — PM workflow (heavy authoring fan-out) [depends: P0]

- [ ] [DOCS] P1. Document the PM "subdivide-an-epic" workflow pattern (Opus synth + Sonnet fan-out over candidate
      child-plans) referencing the existing dispatch; capture it as the template other roles copy. **Gate**: pattern doc
      cross-links the spine + `canonical-plan-flow`; no new dispatch code. — Substantively documented in `main.md`
      (Cold-start + Overnight "keep the PLANS decomposed" sections); a standalone template doc is deferred. NOT REQUIRED
      for archival.

## Success criteria

- `main.md` carries a valid `agent-role` charter row; the PM role is loadable + routable via the broker
  `(role= project_management, domain=*)`.
- Two PM skills return light JSON; the heavy-authoring workflow pattern is documented as the role template.
- **Zero change** to the live planning flow (regen / dispatch tests green) — verified by running the orchestrator.

## Codex SSOT updates

- `/codex/04-architecture/agent-orchestrator-overview.md` — note PM as the reference role-registry row + its skills.
- `unified-trading-pm/agents/main.md` is the PM worked-example registry row (`agent-role` schema enforced by
  `scripts/docs/docspec.py`; the `/codex/04-architecture/role-registry.md` doc was retired 2026-07-16, consolidated into
  docspec + the charters).

## Progress Log

- 2026-06-25: Plan created as the first W6 role instance on the spine. Chosen first because it is lowest-risk
  (making-explicit the already-live orchestrator-as-PM) and keeps the planning flow active per the operator's hard
  constraint. Human-driven (`assigned_vm: NA`). Depends on `role_registry_schema_and_broker_mvp`.
- 2026-07-16: **ARCHIVED** (operator decision). PM charter (Phase 0) delivered + live — `agents/main.md` is the running
  PM agent's `agent-role` registry row (`role: project_management`, opus/high/persistent), loads in `role_registry.py`,
  docspec-green (schema SSOT now `scripts/docs/docspec.py`; `/codex/04-architecture/role-registry.md` deleted
  2026-07-16). Phase 1 skills shipped at MVP (documented boot-prompt commands in `main.md`); Phase 2 pattern documented
  in `main.md`. The fuller scope (backend light-JSON skill endpoints + standalone workflow-template doc) is NOT REQUIRED
  — deferred "real skill-dispatch framework" per `agent_operating_framework_master` (one of the 4 role pilots deferred
  to next quarter). Moved to `plans/archive/2026_07/`.
