---
doc_type: plan
title: Role registry schema + message-broker MVP (the role-based-agent spine)
summary: Schema-ify the 11 agents/*.md charters into a machine-readable role registry, and generalize by-role/message into a tagged ingest→queue→route broker — so "any role, any situation" becomes a lookup, additive to the live AO.
status: active
nature: design
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [role-registry, message-broker, routing, dispatch]
related: [../epics/agent_operating_framework_master.md, pm_role_charter_formalization_2026_06_25.md, data_eng_role_vertical_pilot_2026_06_25.md, ../epics/escalation_and_disaster_recovery_master.md]
created: 2026-06-25
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: brand-new
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 5
last_updated: 2026-06-25
locked_by: NA
locked_since: NA
supersedes:
superseded_by:
depends_on: NA
source:
---

# Role registry schema + message-broker MVP (the role-based-agent spine)

> **W6 (registry schema realization) + W9 (broker)** of `agent_operating_framework_master`. This is the **spine**: the
> PM-role plan, the Data-Eng-role plan, and the escalation MVP all consume the registry + broker this ships. Built
> **additively** — the existing plan→`backlog.yaml` ingestion + strict `assigned_vm` matching keep working untouched;
> this adds a *second* (role-tagged message) entry path beside them. No new DNS — new endpoints on the existing AO
> FastAPI (`api.agent-orchestrator.odum-research.com`).

## Why

We are not building a registry from scratch. Four things already exist (operator + scout audit, 2026-06-25):

- **11 role charters** in `agent-orchestrator/agents/*.md` (main, worker, review, escalate, conflict-resolver,
  plan-health, plan-reconciler, monitor, data_pipeline_failure, recovery-audit, + shared RULES) — prose + prompt
  templates with `model`/`effort`/`thinking` filled at spawn. They are **un-schematized registry rows**.
- **Per-task model/thinking** already derived from plan frontmatter (`model_tier`/`thinking_tier`) by
  `regen_backlog_from_plan.py`.
- **By-role messaging** already exists: `POST /api/agents/by-role/{role}/message` queues to whoever holds a role and
  delivers on poll — the **seed of the broker**.
- **Strict dispatch** routes by `assigned_vm == ORCHESTRATOR_VM_ID`.

So the spine is **three generalizations**: (1) charters → machine-readable rows; (2) dispatch key `assigned_vm` (where)
→ `(role, domain)` (who + what); (3) `by-role/message` → a tagged ingest→queue→route broker. SSOT for the runtime this
rides on: `codex/04-architecture/agent-orchestrator-overview.md`.

## Locked design (operator, 2026-06-25)

- **Registry row = `agents/<role>.md` frontmatter** (the `agent-role` doc_type already defined in W2's schema:
  `role`, `does`/`does_not` on the autonomy gradient, `triggers`, `scope`/`tools`), **plus**: `model`, `thinking`,
  `lifecycle` (`persistent | one_shot | scheduled` — AO already groups by this), `escalation_to` (peer roles to ask
  before a human), `temperament_base` (diligence dial base — see W10). Grep-native, validated by `docspec` (W2). **No
  vector store.**
- **Broker is a NEW ingest path, not a rewrite.** A tagged message `{ role, domain, payload, reply_to }` →
  durable queue → route by `(role, domain)`. **Dumb router**: machine senders (CI, deploy, `DP_*`) self-tag; the only
  human free-text boundary gets a dropdown or one cheap Haiku classifier — **no smart routing agent.**
- **Lifecycle decides standing-vs-cold-spawn**: query-answering roles (DevOps "is it deployed?", Data-Eng "is data
  flowing?") = standing holder + skills; fix-it roles (CI-escalate, DP-fix) = cold one-shot + workflow, killed on done.
- **Reuse, don't replace**: the broker generalizes `AgentMessageRow.target_role`; the dispatch key generalization is
  additive to `_resolve_plan_vms` (a `(role,domain)` resolver beside the `assigned_vm` one — strict matching preserved).

## Phased execution DAG

### Phase 0 — Registry schema SSOT [no code]

- [ ] [DOCS] P0. Role-registry SSOT `codex/04-architecture/role-registry.md`: the `agent-role` frontmatter row (extends
      W2's `agent-role` doc_type) + the `(role, domain)` routing-key spec + the lifecycle/escalation/temperament fields.
      Dogfoods W2's schema. **Gate**: `docspec --check` clean on the SSOT's own frontmatter.

### Phase 1 — Schema-ify the 11 charters [depends: P0]

- [ ] [DOCS] P0. Add `agent-role` frontmatter to all 11 `agent-orchestrator/agents/*.md` (the registry rows): `role`,
      `model`, `thinking`, `lifecycle`, `triggers`, `does`/`does_not`, `scope`/`tools`, `escalation_to`,
      `temperament_base`. **Gate**: all 11 pass `docspec --check`; `recovery-audit.md` keeps its WIP banner.
- [ ] [CODE] P0. `role_registry.py` loader: reads the 11 frontmatters → a typed in-memory registry; one unit test per
      row that the lifecycle/model enums validate. **Gate**: loader test green; bad enum → loud fail.
- [x] ✅ [CODE] P1. Registry realization follow-ons — `agent-orchestrator@c9184b4` (QG-green: ruff/format/basedpyright
      0-0-0 + 965 pytest + 72 vitest). (a) Read-only **Registry** dashboard tab (`GET /api/roles` route +
      `RoleSpec.skills` parsing + `RolesPanel` table: Role|Model|Thinking|Lifecycle|Escalates→|Reports→|Skills).
      (b) **Reap-on-done** for `one_shot` craft workers — `done_slot` kills the drained slot's tmux session (off the DB
      lock) + finishes a bound `AgentRow`; one_shot resolved from the completed task's `assigned_role` via the registry
      (fleet path: task workers have a SlotRow, no AgentRow) OR a bound AgentRow's lifecycle; `_default_kind_lifecycle`
      now resolves craft lifecycle from the registry. (c) `/compact`-when-context-full line in the worker/main/cicd boot
      prompts. **Deferred (todo):** register an `AgentRow` for autospawned craft workers in `autospawn._do_spawn`
      (mirror `escalation.py:~442`) so they appear in the dashboard roster + get a true one_shot-per-task kill — left
      out as it touches the live dispatch path.

### Phase 2 — Dispatch-key generalization (additive) [depends: P1]

- [ ] [CODE] P0. `(role, domain)` resolver beside `assigned_vm` in dispatch: a message tagged `(role, domain)` resolves
      to the registry row → spawn config (model/thinking/lifecycle). Strict `assigned_vm` plan-ingestion path UNCHANGED.
      **Gate**: existing dispatch tests green (no regression); new resolver test green.

### Phase 3 — Message broker MVP [depends: P2]

- [ ] [CODE] P0. `POST /api/messages` ingest: accepts `{ role, domain, payload, reply_to }` from any authenticated
      sender → durable queue (generalize `AgentMessageRow`, add TTL + delivery ack). **Gate**: ingest + queue unit test.
- [ ] [CODE] P0. Router: drain queue → route by `(role, domain)` → standing holder (deliver on poll) OR cold-spawn a
      one-shot per the row's `lifecycle`; reply routed back to `reply_to`. **Gate**: end-to-end test (message in →
      handler spawned → light-JSON reply out).
- [ ] [CODE] P1. One human-boundary tagger: a dropdown (role+domain) on the dashboard "ask a role" box; optional Haiku
      classifier behind a flag (default off). **Gate**: a tagged message routes with zero agent involvement.

## Success criteria

- The 11 charters carry machine-readable `agent-role` frontmatter; `role_registry.py` loads them; `docspec` is green.
- A `(role, domain)`-tagged message ingested at `POST /api/messages` routes to the right handler (standing or
  cold-spawned per `lifecycle`) and returns a light-JSON reply to `reply_to` — with **zero change** to the existing
  plan→`assigned_vm` dispatch (regression tests green).
- "Any role, any situation" is a registry lookup, demonstrated by the PM-role + Data-Eng-role plans riding this spine.

## Codex SSOT updates

- `codex/04-architecture/role-registry.md` (NEW) — the registry-row schema + `(role, domain)` routing-key + broker
  contract.
- `codex/04-architecture/agent-orchestrator-overview.md` — add the broker ingest path beside plan-ingestion; cross-link
  the registry.

## Progress Log

- 2026-06-25: Plan created as the role-based-agent spine (W6 registry realization + new W9 broker) in the operator
  design pass. Human-driven (`assigned_vm: NA`) — it modifies the live AO dispatch, so operator-driven + additive (no
  rewrite of plan-ingestion / strict `assigned_vm`). Unblocks the PM-role, Data-Eng-role, and escalation-MVP plans.
- 2026-06-27: Registry realization follow-ons shipped — `agent-orchestrator@c9184b4` (read-only Registry dashboard tab +
  `RoleSpec.skills` parsing + reap-on-done for one_shot workers + context-compaction boot-prompt lines; QG-green). Phases
  2–3 (dispatch-key generalization + `POST /api/messages` broker) NOT started — operator-gated, out of this MVP slice.
  Hygiene note: Phase 0/1 (codex `role-registry.md` SSOT @`3fc71129b`; `agent-role` frontmatter on every `agents/*.md` +
  `role_registry.py` loader + `test_role_registry.py` @`acbf930`) appear shipped but their checkboxes are still `[ ]` —
  left for the operator/author to confirm the `docspec --check` gate before flipping (not flipped here to avoid claiming
  a gate this session did not run).
