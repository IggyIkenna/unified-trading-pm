---
doc_type: plan
title: AO remediation A — independent fixes (parallel-safe, one distinct file each)
summary:
  Plan A of the split AO issue-docs remediation (operator ruling 2026-07-23, Q1 = split). The 8 todos here each touch a
  DISTINCT file that no sibling todo touches, so they fan out concurrently across the fleet — the intended AO capacity
  test. The interdependent code chain and shared-doc recorders live in Plan B, which is gated behind this one. Two
  safety-sensitive backend todos (cross-role reply routing, wedge liveness gate) are HELD out of both plans per operator
  ruling Q2 and stay in their issue docs.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, doc-integrity, plan-hygiene, plan-reconcile]
related:
  [
    /plans/active/ao_issue_docs_consolidated_remediation_2026_07_23.md,
    /plans/active/ao_remediation_b_code_chain_2026_07_23.md,
    /plans/active/issues/ao_repo_docs_deleted_against_instructions_dead_code_refs_2026_07_23.md,
    /plans/active/issues/plan_quality_four_line_defense_architecture_2026_07_23.md,
  ]
created: 2026-07-23
last_updated: 2026-07-23
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
assigned_role: backend_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  "/plan-reconcile AO-scope run 2026-07-23, split per operator ruling Q1; parent
  ao_issue_docs_consolidated_remediation_2026_07_23"
---

# AO remediation A — independent fixes (parallel)

> **Split from `ao_issue_docs_consolidated_remediation_2026_07_23` per operator ruling 2026-07-23 (Q1 = split).** This
> plan holds the 8 todos that each touch a distinct file with no sibling overlap, so they are safe to run CONCURRENTLY
> (no `sequential:` — intra-plan concurrency is the default and is the point). Plan B
> (`ao_remediation_b_code_chain_2026_07_23`) holds the interdependent git-health/liveness code chain plus the shared-doc
> recorders, runs serially, and is `depends_on` this plan (its sports-audit todo needs this plan's
> `plan_health`/`docs-reconcile` fixes live). Every todo cites its source issue doc and states its done-gate.

> **Parallel-safety proof (checked at authoring):** the 8 todos touch, respectively — `agents/main.md`; the five
> `server/{bootstrap,models/__init__,db,orm,routes/slots_worker}.py` docstrings; `README.md`; `docs/REPO_PROVENANCE.md`;
> `/codex/12-agent-workflow/local-slot-host-symmetric-worker-model.md`;
> `plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md`; `server/plan_health.py`; and a NEW installer script. No
> two share a file. The two held safety todos (`_git_alerts.py`, `routes/agents.py`) are in neither plan.

## Codex SSOTs

- `/codex/12-agent-workflow/canonical-plan-flow.md` — corrected 2026-07-23; `assigned_vm` is `{planning, NA}`
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — dispatch + role semantics
- `/codex/08-workflows/ci-cd-flow.md` — branch flow (for the REPO_PROVENANCE fix)

## Todos

- [ ] [DOCS] P2. Codify the peer-versus-operator reply branch in `unified-trading-pm/agents/main.md` STEP 2B so the
      procedure is not folklore. Rule to state: `from_role == "operator"` uses `/reply`; any other `from_role` uses
      `POST /api/agents/by-role/<from_role>/message` with `from_agent_id`. The doc currently says to POST a reply for
      EVERY polled message regardless of `from_role`, and the interim mitigation was done ad hoc in one live session and
      never written down. **Gate**: the diff lands and the next live cross-role exchange shows a `to_agent` message in
      the recipient's poll.
- [ ] [BACKEND] P2. Repoint or remove the five dead documentation references in `agent-orchestrator/server/` that point
      at files deleted by `agent-orchestrator@19766e7`. The targets are `docs/AUDIT_FINDINGS_2026_05_18.md`,
      `docs/PLAN.md` and `docs/MAIN_AGENT_CUTOVER_REVIEW.md`, all confirmed absent, cited from `bootstrap.py`,
      `models/__init__.py`, `db.py`, `orm.py` and `routes/slots_worker.py`. Point each at the surviving SSOT or delete
      the dangling clause if the docstring stands alone — do NOT resurrect the deleted files. **Gate**:
      `rg -n 'AUDIT_FINDINGS_2026_05_18|docs/PLAN\.md|MAIN_AGENT_CUTOVER_REVIEW' agent-orchestrator/server/` returns
      zero hits and every replacement pointer resolves to a file that exists.
- [ ] [DOCS] P3. Replace `agent-orchestrator/README.md`'s "Files in This Directory" tree with a pointer, and fix its two
      inline `agents/*.md` links. The tree still lists an `agents/` directory and seven files under it that no longer
      exist — the directory was removed in `agent-orchestrator@5eaea29` and role prompts now live in
      `unified-trading-pm/agents/`. Use a pointer rather than re-listing files that will drift again. **Gate**: every
      path in the README tree resolves and no link targets a nonexistent `agents/` file.
- [ ] [DOCS] P3. Correct the branch-flow sentence in `agent-orchestrator/docs/REPO_PROVENANCE.md` to the current model —
      per-slot clones on `live-defi-rollout`, then LDR to `main` DIRECT with staging bypassed by the per-repo `ldr_main`
      toggle. It still describes the retired `tab -> live-defi-rollout -> staging -> main` flow. SSOT:
      `/codex/08-workflows/ci-cd-flow.md`. **Gate**: no `tab ->` flow description remains in the file.
- [ ] [DOCS] P3. Add a SUPERSEDED banner (or fix the text) in
      `/codex/12-agent-workflow/local-slot-host-symmetric-worker-model.md`, which still carries live
      `tab/<operator>/<N>` references to the RETIRED tab-branch model with no banner. Same class as the
      `canonical-plan-flow.md` correction already applied 2026-07-23. **Gate**: no unbannered tab-branch instruction
      remains in the file.
- [ ] [REVIEW] P3. Re-annotate or reopen the agent-orchestrator line in
      `plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md` that is still marked SHIPPED with no note about the
      post-pivot re-drift. A `[x]` that predates an architecture pivot reads as current coverage when it is not.
      **Gate**: the line carries either a re-verification date or an explicit reopen.
- [ ] [INFRA] P1. Route `plan_health.py::record_result()`'s `doc_drift` findings through `notify_slot_blocked` so drift
      reaches a worker's blocked queue instead of only a Slack WARN. Today `doc_drift` routes solely to
      `slack_notify.notify_plan_health_findings`, and `notify_slot_blocked` is never invoked from `plan_health.py`.
      **Gate**: a doc_drift finding produces a blocked-queue entry visible via the backlog API, with the existing Slack
      path unchanged.
- [ ] [INFRA] P2. Wire `/docs-reconcile` onto the same 24h cadence as the plan-reconciler by adding an installer timer
      alongside `agent-orchestrator/scripts/install-plan-reconciler-timer.sh`, and state the cadence in both skills' own
      docs. No docs-reconciler timer or cron exists anywhere in the repo today — the skill is operator-triggered only.
      **Gate**: `systemctl list-timers` on the orchestrator VM shows the docs-reconcile timer with a computed
      next-elapse, and one run posts a result.

## Progress Log

- **2026-07-23**: Authored by splitting `ao_issue_docs_consolidated_remediation_2026_07_23` per operator ruling Q1
  (split for parallelism) + Q2 (hold the 2 safety-sensitive backend todos). Born `status: active`,
  `assigned_vm: planning` — dispatchable to the AO fleet. The parent plan is retained as the holding/index doc for the 6
  non-dispatched items.
