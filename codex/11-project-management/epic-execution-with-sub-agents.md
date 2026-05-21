---
scope: [engineer, admin]
last_reviewed: 2026-05-21
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

Full VM topology details: [`../../plans/active/orchestrator_master.md`](../../plans/active/orchestrator_master.md).

Composes with:

- [`README.md`](README.md) — codex section 11 index with epic registry
- [`active-plan-inventory-tracker.md`](active-plan-inventory-tracker.md) — orphan detection logic
- [`../08-workflows/estimation-calibration.md`](../08-workflows/estimation-calibration.md) — epic-exempt estimation
- [`../12-agent-workflow/`](../12-agent-workflow/) — agent workflow + sub-agent mandatory rules
