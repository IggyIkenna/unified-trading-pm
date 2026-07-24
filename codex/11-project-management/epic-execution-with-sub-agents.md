---
doc_type: codex-ssot
title: Epic Execution with Sub-Agents
summary:
  Codex quick-reference to `plans/epics/README.md` (the epic-flow SSOT) — what an epic is, the audit→active-plan→epic
  flow, epic vs active-plan frontmatter requirements, the epic×tier registry, and epic audit-lifecycle table.
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
last_reviewed: 2026-05-22
code_refs:
---

# Epic Execution with Sub-Agents

**SSOT**: [`../../plans/epics/README.md`](../../plans/epics/README.md)

The epic-flow SSOT lives at `plans/epics/README.md`. It covers:

- What an epic is (planning orchestrator for one persistent code surface; everlasting)
- The audit → active plan → epic flow (planning VM produces audits; gaps become active plans; epics absorb them)
- Epic frontmatter (no date suffix; no `estimate_*` fields; required `assigned_vm` + `tier` + `priority`)
- Active plan frontmatter (required `parent_epic:` — orphans are review-blocking)
- Priority blocks within an epic (P0/P1/P2/P3 sections — VM workers pick up in priority order)
- 19-epic × 5-tier registry + 10-VM topology mapping
- Lifecycle (active / paused / cancelled — NEVER "complete")
- Migration discipline (splits / consolidates / renames)

Full VM topology details: [`/plans/epics/orchestrator_master.md`](/plans/epics/orchestrator_master.md).

---

## Audit lifecycle

**SSOT for how**: [`../../plans/audit/README.md`](../../plans/audit/README.md) **SSOT for flow diagram**:
`plans/epics/README.md` § "The audit → active plan → epic flow"

Every epic has a corresponding audit instruction file that documents _how_ to audit it:

| What                                          | Where                                                              | Lifecycle                                                             |
| --------------------------------------------- | ------------------------------------------------------------------ | --------------------------------------------------------------------- |
| Audit instruction templates (how-to per epic) | `plans/audit/instructions/<epic_slug>_audit_instructions.md`       | **Everlasting** — never archived; updated when epic scope changes     |
| Audit result snapshots (timestamped findings) | `plans/audit/results/<slug>_YYYY_MM_DD.md`                         | **One-shot** — archives when all findings are `- [x]` in parent plans |
| Audit scripts + data files                    | `plans/audit/results/*.py / *.csv / *.parquet`                     | **Permanent** analytics infrastructure                                |
| Who runs audits                               | Planning VM (Ikenna + Harsh, Opus 4.7 1M context)                  | Per `plans/epics/README.md` flow                                      |
| Minimum cadence                               | Monthly per epic + event-driven triggers (new venue, QG RED, etc.) | See instruction file `## Triggers`                                    |

**Epic creation rule**: when a new epic is created in `plans/epics/`, a corresponding
`plans/audit/instructions/<new_epic_slug>_audit_instructions.md` MUST be created in the same commit. An epic without an
instruction file is **review-blocking** — same rule as orphan active plans.

**Audit hygiene** (planning VM cadence): (a) any result with all findings shipped → archive to `results/archive/`; (b)
monthly: review instruction files for epic scope drift; (c) `diff` epics vs instructions to find missing files.

---

## Composes with

- [`README.md`](README.md) — codex section 11 index with epic registry
- [`active-plan-inventory-tracker.md`](active-plan-inventory-tracker.md) — orphan detection logic
- [`issue-doc-lifecycle.md`](issue-doc-lifecycle.md) — how pre-audit diagnostics in issues/ get archived once acked
- [`/codex/08-workflows/estimation-calibration.md`](/codex/08-workflows/estimation-calibration.md) — epic-exempt
  estimation
- [`../12-agent-workflow/`](../12-agent-workflow/) — agent workflow + sub-agent mandatory rules
- [`../../plans/audit/README.md`](../../plans/audit/README.md) — audit lifecycle SSOT
