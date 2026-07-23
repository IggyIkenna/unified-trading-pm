---
doc_type: plan
title: DevOps role charter — the cicd agent for deployment/CI issues
summary:
  Formalize the `cicd` agent as the DevOps registry row — a one-shot role tied into ANY deployment/CI issue (merge
  conflicts, failed promotions, stuck pipelines, SIT/QG walls) that escalates to main — plus the /ci-status skill,
  escalation-wiring confirmation, and a DevOps runbook for the common walls.
status: complete
nature: design
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [role-registry, devops, cicd, deployment, ci, escalation, charter]
related:
  [
    ../epics/agent_operating_framework_master.md,
    /plans/archive/2026_07/role_registry_schema_and_broker_mvp_2026_06_25.md,
    /plans/active/escalation_pipeline_mvp_2026_06_25.md,
  ]
created: 2026-06-27
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
last_updated: 2026-07-02
archived: 2026-07-02
locked_by: NA
locked_since: NA
supersedes:
superseded_by:
depends_on: role_registry_schema_and_broker_mvp_2026_06_25
source:
drift_direction: advance-code
---

# DevOps role charter — the cicd agent for deployment/CI issues

> **🗄️ ARCHIVED 2026-07-02 — COMPLETE, all 4 phases evidence-backed.** P0 charter row (agent-orchestrator@acbf930) · P1
> `/ci-status` skill (agent-orchestrator@79d3f15, `server/ci_status.py`, runtime-verified against the live gh state) ·
> P2 escalation wiring (done-differently: conflict-resolver/data-pipeline/cicd routing, regression-tested in
> `tests/test_escalation.py`) · P3 runbook (`/codex/15-runbooks/devops-ci-walls.md`, docspec hard=0, per-recipe
> `ci-cd-flow.md` citations). Durable SSOTs: `/codex/04-architecture/role-registry.md` (the cicd row) +
> `/codex/08-workflows/ci-cd-flow.md` (recipes) + the runbook.

> **W6 role instance** of `agent_operating_framework_master` — the **DevOps** role on the spine. DevOps = the existing
> `cicd` agent, formalized as a first-class registry row that is dispatched on **ANY** deployment- or CI-related issue
> (merge conflicts, failed promotions, stuck pipelines, SIT/QG walls). One-shot lifecycle (spawned per wall, exits on
> fix), escalates to `main`. Mostly **making-explicit**: `agents/cicd.md` already runs as the CI wall worker; this plan
> writes its charter, names its `/ci-status` skill, confirms the escalation wiring covers the deploy/merge/promotion
> walls, and lands a DevOps runbook.

## Why

Deployment and CI walls — a stuck `quality-gates-v2` promotion, a merge conflict on the integration branch, a failed
LDR→staging→main drain, a SIT/QG wall — block the whole shipping pipeline and need a role that owns diagnosing + fixing
them in real time. The `cicd` agent already performs this DevOps function, but it is not yet a _registry row_: there is
no machine-readable charter declaring its model/thinking/lifecycle/triggers/escalation, and its on-demand status verb is
not packaged as a named skill. Formalizing it (a) validates the spine (`role_registry_schema_and_broker_mvp`) against
the ops boundary, and (b) makes "dispatch the DevOps role at this wall" a broker lookup like any other. This is additive
— the live `cicd` worker keeps running; we add its charter + skill + runbook around it. SSOTs:
`/codex/04-architecture/role-registry.md`, `/codex/08-workflows/ci-cd-flow.md`.

## Locked design (operator, 2026-06-27)

- **DevOps is dispatched on ANY deploy/CI wall**: `triggers` = deploy-failure, merge-conflict, promotion-failure (LDR→
  staging→main drain stuck), stuck-pipeline, SIT/QG wall. It diagnoses + fixes the wall in-band (e.g. recover a
  `quality-gates-v2`-never-reported deadlock, rebase a behind-remote branch, re-run a stuck promotion).
- **One-shot lifecycle, escalates to `main`**: `lifecycle: one_shot` (spawned for one wall, exits on completion;
  `exit_reason="lifecycle-complete"`), `model: sonnet`, `thinking: high` (ops correctness). When it cannot self-resolve
  (a hard-stop or an ambiguous decision), it `escalation_to: main` (the PM/orchestrator), which routes to the operator
  per the generalized escalation pipeline.
- **No pipeline behavior change**: quickmerge / the Tier-C drain / the `quality-gates-v2` server gate are unchanged. The
  charter _describes_ how DevOps is wired into them; the runbook _documents_ the recovery recipes that already exist in
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

- [x] [CODE] P1. `/ci-status <repo>` skill → `gh run list` + `quality-gates-v2` state per repo as light JSON
      `{ repo, latest_run, conclusion, qg_v2_state, blocked }`. Reuses the existing CI-status read paths (Firestore
      `ci_status` SSOT / `gh` CLI). **Gate**: returns valid JSON for a known repo; matches the dashboard's CI state. ✅
      — agent-orchestrator@79d3f15: `server/ci_status.py` (`python -m server.ci_status <repo> [--branch]`), reuses
      `ci_reconcile.repo_ldr_qg_conclusion` (the reconcile loop's OWN read path → matches the dashboard by
      construction); `blocked=true` covers BOTH red AND never-reported v2; 6 unit tests (`tests/test_ci_status.py`);
      `agents/cicd.md` AVAILABLE SKILLS updated to invoke it. Gate MET at runtime 2026-07-02: real run for
      `unified-trading-pm` emitted valid one-line JSON with `qg_v2_state: success` == the direct
      `gh api …/quality-gates-v2.yml/runs?branch=live-defi-rollout` conclusion. AO quality-gates.sh PASSED (1055 tests +
      ruff + basedpyright); shipped via quickmerge to LDR.

### Phase 2 — confirm escalation wiring [depends: P0]

- [x] [CODE] P1. Confirm escalation wiring: verify `POST /api/escalate` → cicd worker dispatch covers the deploy wall +
      the merge-conflict wall + the promotion-failure wall. Add coverage for any wall type not already routed. **Gate**:
      each wall type dispatches a one-shot worker; a regression check asserts the routing. ✅ — DONE DIFFERENTLY
      (verified 2026-07-02): all three walls are covered, but the design evolved past "all three → generic cicd" —
      `merge_conflict` + `stuck_promotion_pr` route to the dedicated **conflict-resolver** one-shot,
      `data_pipeline_failure` to its own prompt, and the remainder (`ldr_qg_failure`, `sit_failure`, `main_ci_red`,
      `label_mismatch`) default to `cicd` (`server/escalation.py` `_prompt_template_for`, line ~84-93). Regression
      checks exist: `tests/test_escalation.py::test_escalate_merge_conflict_routes_to_conflict_resolver` (asserts both
      conflict walls) + the data-pipeline routing assertion. Evidence: agent-orchestrator@acbf930 + escalation.py wall
      registry.

### Phase 3 — DevOps runbook for the common walls [depends: P0]

- [x] [DOCS] P1. A DevOps runbook (declares `owner` / `cadence` / `verifier` / `last_executed` per the runbook HARD
      rule) for the common walls: `quality-gates-v2`-never-reported deadlock recovery, behind-remote rebase, stuck
      LDR→main promotion, SIT/QG wall. Cross-links `ci-cd-flow.md` (does not duplicate it). **Gate**: runbook carries
      all four required runbook fields; each recipe cites the `ci-cd-flow.md` section it references. ✅ —
      `/codex/15-runbooks/devops-ci-walls.md` (this commit): all four fields present (docspec `codex-runbook` hard=0); 4
      recipes each citing exact `ci-cd-flow.md` § titles (verified against the live headers); `/ci-status` named as the
      triage entry point; wall→prompt routing table matches `server/escalation.py` `_prompt_template_for`; explicit
      escalation boundary section.

## Success criteria

- `cicd.md` carries a valid `agent-role` charter row (`one_shot`, `escalation_to: main`); the DevOps role is loadable +
  routable via the broker `(role=cicd, domain=*)`.
- `/ci-status` returns light JSON (`gh run list` + `quality-gates-v2` state per repo).
- Escalation wiring is confirmed to cover the deploy + merge-conflict + promotion-failure walls (regression-checked).
- The DevOps runbook documents the common walls with all four runbook fields, cross-linking `ci-cd-flow.md`.
- **Zero change** to the live shipping pipeline (quickmerge / drain / `quality-gates-v2`) — verified by dispatching a
  `cicd` worker at a real wall.

## Codex SSOTs

- `/codex/04-architecture/role-registry.md` — DevOps = the `cicd` row (`role=cicd`, `model=sonnet`, `thinking=high`,
  `lifecycle=one_shot`, escalation worker); add DevOps as the worked example for the one-shot ops role.
- `/codex/08-workflows/ci-cd-flow.md` — the runbook recovery recipes (quickmerge / drain / `quality-gates-v2` /
  behind-remote / promotion) are owned here; the DevOps runbook cross-links, does not duplicate.

## Progress Log

- 2026-07-02 (later, same session): **Phases 1 + 3 completed → plan COMPLETE, archived.** P1: `server/ci_status.py`
  shipped via quickmerge (agent-orchestrator@79d3f15) — reuses the reconcile loop's `repo_ldr_qg_conclusion` read path,
  6 unit tests, AO QG green (1055 passed), runtime-verified: real JSON for `unified-trading-pm` matched the direct gh v2
  query; `agents/cicd.md` skill section now invokes it. P3: `/codex/15-runbooks/devops-ci-walls.md` — four runbook
  fields (docspec hard=0), 4 recipes citing exact `ci-cd-flow.md` sections, escalation boundary declared.
- 2026-07-02: Closure review (slot session): Phase 0 re-verified (acbf930 resolves; cicd.md carries the full agent-role
  row). **Phase 2 flipped — done differently**: wall coverage complete + regression-tested, but merge-conflict/promotion
  walls route to the dedicated conflict-resolver one-shot (not generic cicd) per the evolved design. Phase 1 (JSON
  skill) + Phase 3 (runbook) identified as the genuinely-open remainder.
- 2026-06-27: Plan created as the DevOps role instance on the spine. Mostly making-explicit — the `cicd` agent already
  works CI/deploy walls; this plan writes its charter (one-shot, escalates to main), names `/ci-status`, confirms the
  `POST /api/escalate` → cicd wiring covers deploy + merge-conflict + promotion-failure walls, and adds a DevOps runbook
  for the common walls. Human-driven (`assigned_vm: NA`, `execution_scope: local-only`). Depends on
  `role_registry_schema_and_broker_mvp`.
