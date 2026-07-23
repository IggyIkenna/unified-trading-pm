---
doc_type: codex-ssot
title: Audit Lifecycle
summary:
  Codex quick-reference for the three-layer audit lifecycle (instructions/results/scripts) whose full spec is
  `plans/audit/README.md` — epic-creation rule, result archival triggers, and audit-hygiene cadence.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [audit-lifecycle, audit, epic-execution, plan-hygiene, archival]
related:
  [
    ../../plans/audit/README.md,
    /codex/11-project-management/epic-execution-with-sub-agents.md,
    ../../plans/epics/README.md,
    /codex/11-project-management/issue-doc-lifecycle.md,
  ]
created: 2026-05-23
authoritative_for: [codex audit-lifecycle quick-reference]
referenced_by:
owner:
last_reviewed: 2026-05-23
code_refs:
---

# Audit Lifecycle

**SSOT**: [`../../plans/audit/README.md`](../../plans/audit/README.md)

The full audit lifecycle spec — directory structure, file formats, archival rules, epic-creation rule, and hygiene
cadence — lives at `plans/audit/README.md`. This codex entry is a pointer + quick-reference summary.

---

## Three-layer structure

| Layer              | Path                                                         | Lifecycle                                                         |
| ------------------ | ------------------------------------------------------------ | ----------------------------------------------------------------- |
| **Instructions**   | `plans/audit/instructions/<epic_slug>_audit_instructions.md` | **Everlasting** — never archived; updated when epic scope changes |
| **Results**        | `plans/audit/results/<slug>_YYYY_MM_DD.md`                   | **One-shot snapshot** — archives when all findings are `- [x]`    |
| **Scripts + data** | `plans/audit/results/*.py / *.csv / *.parquet`               | **Permanent** analytics infrastructure — never archived           |

Currently: 19 instruction files (one per epic), results in `plans/audit/results/`, root-level legacy thematic audits.

---

## Key rules (summary — full spec in `plans/audit/README.md`)

**Epic creation rule (HARD)**: when a new epic is created in `plans/epics/`, a corresponding
`plans/audit/instructions/<new_epic_slug>_audit_instructions.md` MUST be created in the same commit. An epic without an
instruction file is **review-blocking** — same rule as orphan active plans.

**Result archival**: move to `plans/audit/results/archive/` when (a) every gap item the result spawned is `- [x]` in its
parent active plan, (b) no remaining AMBER or RED items without a plan absorbing them. Update the Linked Results table
in the instruction file when archiving.

**Audit hygiene** (planning VM cadence):

1. Any result with all findings shipped → archive to `results/archive/`
2. Monthly: review instruction files for epic scope drift; update `## Triggers` + `## Checklist` sections
3. Run `diff <(ls plans/epics/*.md | ...) <(ls plans/audit/instructions/*.md | ...)` to find missing instruction files

**Instructions never archive** — they are templates. Update them when the epic scope changes. Delete only if the epic is
cancelled (and mark the instruction file `status: cancelled` before deletion).

---

## Instruction file format (required frontmatter)

```yaml
---
name: <epic_slug>_audit_instructions
type: audit-instructions
epic: <epic_slug>
assigned_vm: <from orchestrator_vm_registry.yaml>
tier: L0|L1|L2|L3|L4|L5
last_updated: YYYY-MM-DD
---
```

Required body sections: `## Epic Scope`, `## Triggers`, `## Checklist`, `## Success Criteria`, `## Output Format`,
`## Linked Results`.

---

## Cross-references

- [`../../plans/audit/README.md`](../../plans/audit/README.md) — canonical SSOT; full lifecycle diagram + file formats
- [`epic-execution-with-sub-agents.md`](epic-execution-with-sub-agents.md) — audit lifecycle table + epic creation rule
- [`../../plans/epics/README.md`](../../plans/epics/README.md) — `## Audit instructions per epic`; flow diagram
- [`issue-doc-lifecycle.md`](issue-doc-lifecycle.md) — pre-audit diagnostics in `issues/` archive once acked into plan
