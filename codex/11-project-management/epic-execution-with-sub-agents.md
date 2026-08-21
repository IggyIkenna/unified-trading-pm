---
doc_type: codex-ssot
title: Epic Execution with Sub-Agents
summary:
  Codex quick-reference to `plans/epics/README.md` (the epic-flow SSOT) — what an epic is, the audit→active-plan→epic
  flow, epic vs active-plan frontmatter requirements, the epic×tier registry, and the audit lifecycle.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [epic-execution, sub-agents, audit-lifecycle, plan-hygiene, orchestrator]
related:
  [
    ../../plans/epics/README.md,
    ../../plans/epics/orchestrator_master.md,
    /codex/11-project-management/active-plan-inventory-tracker.md,
    /codex/11-project-management/issue-doc-lifecycle.md,
    /codex/08-workflows/estimation-calibration.md,
    ../../plans/audit/README.md,
  ]
created: 2026-03-27
authoritative_for: [epic-execution codex quick-reference]
referenced_by:
  [
    /codex/11-project-management/README.md,
    /codex/11-project-management/audit-lifecycle.md,
    plans/epics/README.md,
    plans/epics/client_isolation_and_governance_master.md,
    plans/epics/strategy_master.md,
  ]
owner:
last_reviewed: 2026-08-21
code_refs:
---

# Epic Execution with Sub-Agents

**SSOT**: [`../../plans/epics/README.md`](../../plans/epics/README.md)

The epic-flow SSOT lives at `plans/epics/README.md`. It covers:

- What an epic is (planning orchestrator for one persistent code surface; everlasting)
- The audit → active plan → epic flow (planning VM produces audits; gaps become active plans; epics absorb them)
- Epic frontmatter (no date suffix; no `estimate_*` fields; required `name`, `title`, `priority`, and `status`)
- Active plan frontmatter (required `parent_epic:` — orphans are review-blocking)
- Priority blocks within an epic (P0/P1/P2/P3 sections — VM workers pick up in priority order)
- 22-epic × 6-tier registry (regenerated 2026-08-19)
- Historical 10-VM topology, superseded by the single `planning` VM and role-based dispatch
- Lifecycle (active / paused / cancelled — NEVER "complete")
- Migration discipline (splits / consolidates / renames)

Historical VM topology details are retained in [`/plans/epics/orchestrator_master.md`](/plans/epics/orchestrator_master.md);
do not use the per-epic VM model for dispatch.

---

## Audit lifecycle

**SSOT for how**: [`../../plans/audit/README.md`](../../plans/audit/README.md) **SSOT for flow diagram**:
`plans/epics/README.md` § "The audit → active plan → epic flow"

Audits are periodic planning-VM reviews. Timestamped findings land in `plans/audit/results/<slug>_YYYY_MM_DD.md`,
and gaps become active plans carrying `parent_epic:`; completed result snapshots archive after their findings ship.
Audit instructions are embedded in each epic file directly. Audit scripts and data in `plans/audit/results/` are
permanent infrastructure.

---

## Composes with

- [`README.md`](README.md) — codex section 11 index with epic registry
- [`active-plan-inventory-tracker.md`](active-plan-inventory-tracker.md) — orphan detection logic
- [`issue-doc-lifecycle.md`](issue-doc-lifecycle.md) — how pre-audit diagnostics in issues/ get archived once acked
- [`/codex/08-workflows/estimation-calibration.md`](/codex/08-workflows/estimation-calibration.md) — epic-exempt
  estimation
- [`../12-agent-workflow/`](../12-agent-workflow/) — agent workflow + sub-agent mandatory rules
- [`../../plans/audit/README.md`](../../plans/audit/README.md) — audit lifecycle SSOT
