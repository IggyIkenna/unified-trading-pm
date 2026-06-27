---
doc_type: plan
title: DevOps role charter — the cicd agent for deployment/CI issues
summary: Formalize the `cicd` agent as the DevOps registry row — a one-shot role tied into ANY deployment/CI issue (merge conflicts, failed promotions, stuck pipelines, SIT/QG walls) that escalates to main — plus the /ci-status skill, escalation-wiring confirmation, and a DevOps runbook for the common walls.
status: active
nature: design
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [role-registry, devops, cicd, deployment, ci, escalation, charter]
related: [../epics/agent_operating_framework_master.md, role_registry_schema_and_broker_mvp_2026_06_25.md, escalation_pipeline_mvp_2026_06_25.md]
created: 2026-06-27
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
last_updated: 2026-06-27
locked_by: NA
locked_since: NA
supersedes:
superseded_by:
depends_on: role_registry_schema_and_broker_mvp_2026_06_25
source:
---

# DevOps role charter — the cicd agent for deployment/CI issues

> **W6 role instance** of `agent_operating_framework_master` — the **DevOps** role on the spine. DevOps = the existing
> `cicd` agent, formalized as a first-class registry row that is dispatched on **ANY** deployment- or CI-related issue
> (merge conflicts, failed promotions, stuck pipelines, SIT/QG walls). One-shot lifecycle (spawned per wall, exits on
> fix), escalates to `main`. Mostly **making-explicit**: `agents/cicd.md` already runs as the CI wall worker; this plan
> writes its charter, names its `/ci-status` skill, confirms the escalation wiring covers the deploy/merge/promotion
> walls, and lands a DevOps runbook.

## Why

Deployment and CI walls — a stuck `quality-gates-v2` promotion, a merge conflict on the integration branch, a failed
LDR→staging→main drain, a SIT/QG wall — block the whole shipping pipeline and need a role that owns diagnosing + fixing
them in real time. The `cicd` agent already performs this DevOps function, but it is not yet a *registry row*: there is
no machine-readable charter declaring its model/thinking/lifecycle/triggers/escalation, and its on-demand status verb is
not packaged as a named skill. Formalizing it (a) validates the spine (`role_registry_schema_and_broker_mvp`) against the
ops boundary, and (b) makes "dispatch the DevOps role at this wall" a broker lookup like any other. This is additive —
the live `cicd` worker keeps running; we add its charter + skill + runbook around it. SSOTs:
`codex/04-architecture/role-registry.md`, `codex/08-workflows/ci-cd-flow.md`.

## Locked design (operator, 2026-06-27)

- **DevOps is dispatched on ANY deploy/CI wall**: `triggers` = deploy-failure, merge-conflict, promotion-failure (LDR→
  staging→main drain stuck), stuck-pipeline, SIT/QG wall. It diagnoses + fixes the wall in-band (e.g. recover a
  `quality-gates-v2`-never-reported deadlock, rebase a behind-remote branch, re-run a stuck promotion).
- **One-shot lifecycle, escalates to `main`**: `lifecycle: one_shot` (spawned for one wall, exits on completion;
  `exit_reason="lifecycle-complete"`), `model: sonnet`, `thinking: high` (ops correctness). When it cannot self-resolve
  (a hard-stop or an ambiguous decision), it `escalation_to: main` (the PM/orchestrator), which routes to the operator
  per the generalized escalation pipeline.
- **No pipeline behavior change**: quickmerge / the Tier-C drain / the `quality-gates-v2` server gate are unchanged. The
  charter *describes* how DevOps is wired into them; the runbook *documents* the recovery recipes that already exist in
  `ci-cd-flow.md`.

## Phased execution DAG

### Phase 0 — DevOps charter row [depends: spine Phase 1]

- [x] ✅ [DOCS] P1. Schematize `agent-orchestrator/agents/cicd.md` as the DevOps registry row: `role: cicd`,
      `model: sonnet`, `thinking: high`, `lifecycle: one_shot`, `triggers` (deploy failure, merge conflict, promotion
      failure, stuck pipeline, SIT/QG wall), `does`/`does_not` (fixes CI/deploy walls; does NOT author plans or change
      product code), `escalation_to: main`, `temperament_base` (decisive). **Note**: this is being done now under the AO
      MVP. **Gate**: `docspec --check` clean; loads in `role_registry.py` as `role=cicd`, `lifecycle=one_shot`. — DONE
      `agent-orchestrator@acbf930` (cicd.md agent-role row + DevOps role framing).

### Phase 1 — /ci-status skill (the on-demand status verb) [depends: P0]

- [ ] [CODE] P1. `/ci-status <repo>` skill → `gh run list` + `quality-gates-v2` state per repo as light JSON
      `{ repo, latest_run, conclusion, qg_v2_state, blocked }`. Reuses the existing CI-status read paths (Firestore
      `ci_status` SSOT / `gh` CLI). **Gate**: returns valid JSON for a known repo; matches the dashboard's CI state.

### Phase 2 — confirm escalation wiring [depends: P0]

- [ ] [CODE] P1. Confirm escalation wiring: verify `POST /api/escalate` → cicd worker dispatch covers the deploy wall +
      the merge-conflict wall + the promotion-failure wall (all three route to a `cicd` one-shot). Add coverage for any
      wall type not already routed. **Gate**: each of the three wall types dispatches a `cicd` worker; a regression check
      asserts the routing.

### Phase 3 — DevOps runbook for the common walls [depends: P0]

- [ ] [DOCS] P1. A DevOps runbook (declares `owner` / `cadence` / `verifier` / `last_executed` per the runbook HARD
      rule) for the common walls: `quality-gates-v2`-never-reported deadlock recovery, behind-remote rebase, stuck
      LDR→main promotion, SIT/QG wall. Cross-links `ci-cd-flow.md` (does not duplicate it). **Gate**: runbook carries
      all four required runbook fields; each recipe cites the `ci-cd-flow.md` section it references.

## Success criteria

- `cicd.md` carries a valid `agent-role` charter row (`one_shot`, `escalation_to: main`); the DevOps role is loadable +
  routable via the broker `(role=cicd, domain=*)`.
- `/ci-status` returns light JSON (`gh run list` + `quality-gates-v2` state per repo).
- Escalation wiring is confirmed to cover the deploy + merge-conflict + promotion-failure walls (regression-checked).
- The DevOps runbook documents the common walls with all four runbook fields, cross-linking `ci-cd-flow.md`.
- **Zero change** to the live shipping pipeline (quickmerge / drain / `quality-gates-v2`) — verified by dispatching a
  `cicd` worker at a real wall.

## Codex SSOTs

- `codex/04-architecture/role-registry.md` — DevOps = the `cicd` row (`role=cicd`, `model=sonnet`, `thinking=high`,
  `lifecycle=one_shot`, escalation worker); add DevOps as the worked example for the one-shot ops role.
- `codex/08-workflows/ci-cd-flow.md` — the runbook recovery recipes (quickmerge / drain / `quality-gates-v2` /
  behind-remote / promotion) are owned here; the DevOps runbook cross-links, does not duplicate.

## Progress Log

- 2026-06-27: Plan created as the DevOps role instance on the spine. Mostly making-explicit — the `cicd` agent already
  works CI/deploy walls; this plan writes its charter (one-shot, escalates to main), names `/ci-status`, confirms the
  `POST /api/escalate` → cicd wiring covers deploy + merge-conflict + promotion-failure walls, and adds a DevOps runbook
  for the common walls. Human-driven (`assigned_vm: NA`, `execution_scope: local-only`). Depends on
  `role_registry_schema_and_broker_mvp`.
