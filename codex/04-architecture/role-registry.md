---
last_reviewed: 2026-06-27
doc_type: codex-ssot
title: Agent role registry — schema + model-tier SSOT
summary: The `agent-role` frontmatter schema every agent-orchestrator/agents/*.md carries, the typed registry that loads it (server/role_registry.py), and the per-role model/thinking/lifecycle defaults. This is the "model registry + roles that define which agent spawns per task" SSOT.
status: active
nature: contract
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [role, registry, model-tier, agent-orchestrator, boot-prompt, lifecycle]
related: [model-tier-selection.md, agent-orchestrator-overview.md, runtime-deployment-topology.md]
created: 2026-06-27
---

# Agent role registry

The orchestrator spawns one Claude session per task. **Which** session — its boot prompt, model, thinking budget,
lifecycle, and escalation target — is defined by a **role**. Every role is one `agent-orchestrator/agents/<role>.md`
file carrying an `agent-role` frontmatter block; `server/role_registry.py` loads all of them into a typed in-memory
registry that the dispatch/spawn paths read. This doc is the SSOT for that schema + the per-role defaults.

> Model-tier policy (when opus vs sonnet vs haiku, when thinking high/max) is owned by
> [`codex/06-coding-standards/model-tier-selection.md`](../06-coding-standards/model-tier-selection.md). This doc only
> records the *per-role assignment* that policy produces, and the schema that carries it.

## `agent-role` frontmatter schema

Every `agents/<role>.md` (except shared non-role docs `RULES.md`) MUST carry:

| field             | type / values                                         | meaning                                                                 |
| ----------------- | ----------------------------------------------------- | ----------------------------------------------------------------------- |
| `doc_type`        | `agent-role`                                           | marks the file as a registry row                                        |
| `role`            | kebab/snake id, == file stem                           | the routing key (matches plan `assigned_role:`)                         |
| `model`           | `opus` \| `sonnet` \| `haiku`                          | model the orchestrator spawns this role at                              |
| `thinking`        | `max` \| `high` \| `medium`                            | reasoning budget (`max` ⇒ requires `model: opus`)                       |
| `lifecycle`       | `persistent` \| `one_shot` \| `scheduled`             | reap policy — see below                                                 |
| `triggers`        | list                                                  | what causes this role to be dispatched                                  |
| `does`            | list                                                  | in-scope work                                                           |
| `does_not`        | list                                                  | out-of-scope (cross-role lines it must not cross)                       |
| `escalation_to`   | role id \| `operator`                                 | where this role escalates a wall / blocking decision                    |
| `temperament_base`| short adjective(s)                                    | tone the boot prompt adopts (e.g. `diligent`, `calm`, `decisive`)       |
| `reports_to`      | role id (optional)                                    | the QA/review boundary for the role's output                            |

`scope_tools`, `status`, `summary` etc. are optional metadata. A prose-only role file (no frontmatter) loads with
fallback defaults `model: sonnet`, `thinking: None`, `lifecycle: persistent` — a transition state, not the target.

## Lifecycle → reap policy

- **`persistent`** — long-lived; loops draining the queue / answering chat. Reaped only on a dead session (anomaly).
  Roles: `main`, `review`, generic `worker`, `monitor`.
- **`one_shot`** — spawned for ONE task/wall, exits on completion; the orchestrator kills its session when done
  (`exit_reason="lifecycle-complete"`, INFO not anomaly). Roles: the one-shot craft workers (`backend-engineer`,
  `ui-developer`, `quant-dev`, `infra`), `cicd`, `conflict-resolver`, `data_pipeline_failure`.
- **`scheduled`** — fired on a timer, exits each run. Roles: `data_engineering` (daily availability audits),
  `plan-health`, `plan-reconciler`.

## Per-role model/thinking/lifecycle registry (codex defaults)

| role                    | model  | thinking | lifecycle  | charter                                                                 |
| ----------------------- | ------ | -------- | ---------- | ---------------------------------------------------------------------- |
| `project_management`    | opus   | high     | persistent | **Project management** — orchestration, backlog, cross-plan authoring (file `agents/main.md`; runtime agent key stays `main`) |
| `review`                | sonnet | high     | persistent | **UAT/QA** — PR gate: impl-vs-plan (every PR), enhanced tests (major bump → escalate opus) |
| `data_engineering`      | sonnet | high     | scheduled  | **Data engineering** — pipeline code + daily availability audits        |
| `cicd`                  | sonnet | high     | one_shot   | **DevOps** — deploy/CI walls, merge conflicts, promotion failures       |
| `backend-engineer`      | sonnet | medium   | one_shot   | craft worker — Python service code                                      |
| `ui-developer`          | sonnet | medium   | one_shot   | craft worker — TypeScript/UI + playwright                               |
| `quant-dev`             | sonnet | medium   | one_shot   | craft worker — strategy/feature/ML math                                 |
| `infra`                 | sonnet | medium   | one_shot   | craft worker — provisioning, VM launches, cloud                         |
| `worker`                | sonnet | medium   | persistent | generic queue-draining worker (no craft role assigned)                  |
| `plan-reconciler`       | opus   | high     | scheduled  | daily plan/codex/cross-plan reconciliation + auto-archive               |
| `plan-health`           | haiku  | —        | scheduled  | fast skeleton plan-hygiene gate (cheap model)                           |
| `conflict-resolver`     | sonnet | medium   | one_shot   | escalation — merge-conflict adjudication                                |
| `data_pipeline_failure` | sonnet | medium   | one_shot   | escalation — data-pipeline alert triage                                 |
| `monitor`               | sonnet | medium   | persistent | manual-spawn fleet observer (boot prompt owned by operator)             |

**Reading the registry:** `server/role_registry.py::load_registry()` parses every `agents/*.md` frontmatter into a
`RoleSpec`; `get_role(role)` returns the spec (or the fallback). The spawn paths resolve a role's
`(model, thinking, lifecycle)` from this registry: `regen_backlog_from_plan.py::_role_tier()` (task workers via plan
`assigned_role`), `escalation.py` (cicd/conflict-resolver/data_pipeline_failure), and `main_agent_keeper.py` (main).
An explicit plan `model_tier:` still overrides the role default (more-specific wins).

## Skills

Roles gain specialised verbs as **skills** — documented commands a role's boot prompt instructs it to run (an existing
script or API call), surfaced under an `## Available skills` section inside the role's ` ```text ` boot-prompt block.
MVP skills: PM `/plan-status` + `/whats-dispatched`; data_engineering `/data-freshness`; review `/pr-check`; cicd
`/ci-status`. Skills are additive — a role without a skills section still works.
