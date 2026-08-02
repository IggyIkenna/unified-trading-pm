---
doc_type: codex-ssot
title: Codex Delta Canonical Brief
summary:
  Durable PM strategy memory for the "Codex Delta" program (pre-dates the May-23 cutover master plan) — mission
  (batch-85pct/live-90pct targets), client/delivery focus, `pending→uat_accepted→done` lifecycle model, ownership
  defaults, and a decision log; preserves context that workspace-scoped chat history can lose.
status: stale
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [codex-delta, strategy-memory, decision-log, pm-context, ownership]
related: []
created: 2026-03-27
authoritative_for: [codex delta canonical decision log (historical)]
referenced_by:
owner:
last_reviewed: 2026-09-08
code_refs:
---

# Codex Delta Canonical Brief

> **⚠️ HISTORICAL — `status: stale` is correct (re-confirmed 2026-07-31).** This brief predates the May-23 cutover and
> the agent-orchestrator era. Two of its operating decisions are now **superseded** and MUST NOT be followed:
>
> - **"GitHub Projects v2 is the execution surface"** — it is not. Work is tracked as `- [ ]` todos in
>   `plans/active/*.md`, from which the orchestrator backlog is derived (`regen_backlog_from_plan.py`; never hand-edit
>   `backlog.yaml`). SSOT
>   [`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`](/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md).
> - **The `pending → in_progress → ready_for_testing → uat_accepted → done` checklist lifecycle** — superseded by the
>   plan-todo + evidence-backed-completion model (SSOT [`/plans/PLAN_FORMAT.md`](/plans/PLAN_FORMAT.md) § 8b and
>   [`/codex/12-agent-workflow/commit-push-flip-rule.md`](/codex/12-agent-workflow/commit-push-flip-rule.md)).
>
> Retained only as the **decision log of record** for Feb-2026 program intent (mission targets, client focus, ownership
> defaults). Do not cite it for current process.

**Last updated:** 2026-02-11
**Purpose:** Durable strategy memory for Codex Delta planning, timeline intent, client focus, rollout policy, and
decision ownership.

---

## Why This Exists

This file is the durable source for strategic PM context that can be lost in workspace-scoped chat history (for example,
when Cursor workspace IDs change and a conversation tab disappears).
Plan files remain execution artifacts; this brief preserves business and delivery intent.

---

## Current Mission

Build a single operating model where Codex is the source of truth and GitHub + deployment checklists are synchronized to
one lifecycle, with enough structure to support:

- Batch readiness progress toward `batch-85pct`
- Live readiness progress toward `live-90pct`
- Weekly planning and daily issue/bug standups
- Historical backlog reconstruction with explicit historical metadata

Current-state reality:

- The existing codebase is still below target audit standards in multiple areas.
- Program execution must handle both audit remediation and new capability expansion in one system.

---

## Client and Delivery Focus

Primary client context to preserve in all planning and rollout choices:

- Multi-domain trading clients across CEFI/DEFI/TRADFI and SPORTS pathways
- Strategy rollout expectations spanning execution, risk, and UI observability
- Commercially meaningful milestones over one-week iterations
- UAT signal quality as the final acceptance gate for user-facing intent

This means timelines are not only engineering-complete timelines; they are "implementation + validation + UAT
acceptance" timelines.

---

## Scope Promoted to Core (Not Deferred)

The following are treated as core Codex Delta scope now:

- Sports integration tracks
- Options execution and backtesting depth
- Risk/exposure/PnL service coverage
- UI service set and UAT validation surfaces

---

## Lifecycle Model (Canonical)

Work progresses through the following state machine:

`pending -> in_progress -> ready_for_testing -> uat_accepted -> done`

Completion policy:

- `ready_for_testing` means implementation is complete (quality gates + quickmerge pass)
- `done` requires `uat_accepted` where UAT is applicable
- Bugs/regressions can move checklist state backward to reflect reopened risk

---

## Ownership Defaults

Role+person hybrid default ownership:

- Infra/security/disaster-recovery defaults to Ikenna
- Sports-domain defaults to Harsh
- Non-sports ML/strategy defaults to Ikenna
- UAT and finish-line validation often defaults to Harsh (with explicit overrides allowed)

---

## Timeline and Cadence Model

- Planning cadence: one-week iterations
- Top milestones: fixed dates
- Lower milestones/tasks: sprint-relative sequencing
- Status/reporting cadence:
  - Daily: handover and checklist synchronization
  - Weekly: standup summary and milestone review

---

## Historical Backlog Policy

When reconstructing prior work, create/close items now with explicit historical attribution:

- Include historical completion note in issue body
- Include source commit hash/date references where available
- Keep backfilled work distinguishable from newly discovered deltas

---

## System Operating Decisions

1. Delivery flow is ordered: `Delta Q&A -> Codex updates -> repo/deployment deltas -> GitHub issue/project automation`
2. GitHub Projects v2 is the execution surface (status, assignee, iteration, priority fields).
3. Checklist YAMLs in deployment must stay synchronized with GitHub lifecycle state.
4. Quickmerge-first and quality-gate-first behavior is enforced before completion marking.
5. Audit-remediation and new capability requests are treated as parallel lanes under one PM lifecycle.

---

## Decision Log (Initial Canonical Entries)

| Date       | Decision                                                           | Why                                                        |
| ---------- | ------------------------------------------------------------------ | ---------------------------------------------------------- |
| 2026-02-11 | Promote sports/market-making/options/risk+PnL/UI scope to core     | Avoid Stage-2 drift on commercially critical capabilities  |
| 2026-02-11 | Use two-stage completion (`ready_for_testing` then `uat_accepted`) | Prevent false "done" states before intent validation       |
| 2026-02-11 | Backfill historical work as explicit historical issues             | Preserve auditability and avoid timeline ambiguity         |
| 2026-02-11 | Use one-week iteration model in Projects v2                        | Improve planning granularity and standup reporting quality |

---

## Context Durability Protocol

After major planning conversations, mirror key decisions into this file (or linked Codex PM docs) within the same day:

1. Add decision summary
2. Add owner default/override
3. Add acceptance signal (`quality_gates`, `uat_accepted`, or both)
4. Add timeline implication

This protocol ensures strategic context survives any chat/session loss.
