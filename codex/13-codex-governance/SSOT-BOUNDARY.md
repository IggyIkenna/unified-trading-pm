---
doc_type: codex-ssot
title: "SSOT Boundary: Codex vs PM"
summary:
  "Canonical rule for where content belongs — codex (evergreen standards/specs/ADRs) vs PM
  (plans/tracking/runbooks/automation) — via a 9-question decision tree, content categories, cross-reference formats,
  governance rules, and the Renames-in-Flight field-deprecation table."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service, unified-trading-pm]
scope: [engineer, admin]
tags: [codex, governance, ssot-audit, plan-hygiene, docspec]
related: [/codex/13-codex-governance/SECTION-REGISTRY.md]
created: 2026-03-27
authoritative_for: [codex-vs-PM content-placement boundary (decision tree + renames-in-flight table)]
referenced_by:
  [
    /codex/06-coding-standards/uac-internal-module-docstring.md,
    /codex/11-project-management/codex-audit-playbook.md,
    /codex/13-codex-governance/SECTION-REGISTRY.md,
  ]
owner:
last_reviewed:
code_refs:
---

# SSOT Boundary: Codex vs PM

This document is the canonical rule for where content belongs. All agents and developers must consult this before
creating or moving files in either repo.

## The Governing Principle

| Dimension                          | `unified-trading-codex`                    | `unified-trading-pm`                         |
| ---------------------------------- | ------------------------------------------ | -------------------------------------------- |
| Question answered                  | "What MUST be true across all repos?"      | "What IS the current state?"                 |
| Content type                       | Standards, specs, ADRs, methodology        | Plans, tracking, runbooks, automation        |
| Evergreen?                         | YES — must not go stale                    | NO — expected to be replaced by next version |
| Absolute / machine-specific paths? | **NEVER**                                  | **NEVER** — always workspace-relative        |
| Update trigger                     | Architecture decision or pattern change    | Code change, audit finding, sprint planning  |
| Audience                           | Any developer or agent joining the project | Current active developers and agents         |

**Path rule (both repos):** All file paths in documentation must be workspace-relative from the repo root. Example:
`unified-trading-pm/codex/scripts/validate-alignment.py`, not `/Users/...` or `$HOME/...`.

---

## Decision Tree

When placing a document, answer these questions in order:

**Q1: Does it track work status, assignees, timelines, or % completion?**

- YES → `unified-trading-pm/plans/` (active) or `unified-trading-pm/plans/archive/` (done)

**Q2: Is it an Architecture Decision Record — a permanent record of WHY a choice was made (options considered,
rationale, outcome)?**

- YES → `unified-trading-pm/codex/11-project-management/decisions/`

**Q3: Is it a process standard that ALL repos must follow (e.g., how to define backlog lanes, how to run audits, how to
do dual-cloud readiness)?**

- YES → `unified-trading-pm/codex/11-project-management/` or `unified-trading-pm/codex/06-coding-standards/`

**Q4: Is it a scope specification — what is being built, success criteria, ownership (not the execution task list)?**

- YES → `unified-trading-pm/codex/11-project-management/epics/`

**Q5: Is it an agent execution procedure (how to task agents, how to recover from failures, how to do human review)?**

- YES → `unified-trading-pm/codex/12-agent-workflow/`

**Q6: Is it a copy-paste operational runbook (shell commands, environment-specific steps)?**

- YES → `unified-trading-pm/docs/runbooks/` (write from scratch with workspace-relative paths)
- If stale and machine-specific → `unified-trading-pm/plans/archive/`

**Q7: Is it an active execution plan with sprint items, task IDs, or agent prompts?**

- YES → `unified-trading-pm/plans/active/` or `unified-trading-pm/plans/cursor-plans/`

**Q8: Is it CI/CD infrastructure planning (pipeline design, coverage targets per milestone)?**

- YES → `unified-trading-pm/plans/cicd/`

**Q9: Does it document workspace automation or scripts that operate across repos?**

- YES → `unified-trading-pm/scripts/` (script) + `unified-trading-pm/docs/` (guide if needed)

If none of the above fit: default to **codex** if the content is durable standards; default to **PM** if it is
operational.

---

## Content Categories

| Category              | Definition                                                       | Correct home                                             |
| --------------------- | ---------------------------------------------------------------- | -------------------------------------------------------- |
| **Standard**          | Rules and patterns all repos must follow                         | Codex `06-coding-standards/` or `11-project-management/` |
| **Specification**     | Canonical definition of HOW something works (not tracking state) | Codex (section matching the domain)                      |
| **ADR**               | Permanent record of an architectural decision + rationale        | Codex `11-project-management/decisions/`                 |
| **Scope spec / Epic** | What is being built, success criteria, ownership                 | Codex `11-project-management/epics/`                     |
| **Agent procedure**   | How to task agents, how to recover, how to review                | Codex `12-agent-workflow/`                               |
| **Runbook**           | Step-by-step commands for executing a task right now             | PM `docs/runbooks/`                                      |
| **Active plan**       | Time-bounded plan with targets, metrics, status                  | PM `plans/active/`                                       |
| **CI/CD plan**        | Pipeline infrastructure, coverage milestones                     | PM `plans/cicd/`                                         |
| **Archive**           | Historical content with reference value, no longer active        | Nearest `archive/` subdirectory in the correct repo      |

---

## Cross-Reference Format Standard

Use these formats consistently so agents can resolve references programmatically:

**Codex → PM (pointing to operational content):**

```
See: unified-trading-pm/[path] (PM — operational content)
```

**PM → Codex (pointing to the authoritative standard):**

```
Standard: unified-trading-pm/codex/[section]/[file]
```

**Cursor rule referencing a codex standard:**

```
CODEX: 06-coding-standards/[file]
```

---

## Anti-Patterns to Avoid

| Anti-pattern                                                 | Correct action                                                                       |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| Roadmap or priority matrix in codex                          | Move to `unified-trading-pm/plans/archive/`                                          |
| Runbook with absolute paths in either repo                   | Archive it; write a fresh version with workspace-relative paths if needed            |
| Epic file with hour estimates and GitHub task links in codex | Extract ADR from it if it has architectural decisions; move execution tracking to PM |
| Generated JSON artifact committed to codex                   | Delete; generated outputs are not source                                             |
| The same `quality-gates.sh` template in both repos           | PM has the canonical; codex has reference templates only (in `06-coding-standards/`) |
| Agent task definition files in codex                         | Move to `unified-trading-pm/plans/tasks/`                                            |
| Personal handoff documents (dated, person-specific) in codex | Move to `unified-trading-pm/plans/archive/`                                          |

---

## Governance Rules

**Rule 1:** No absolute paths in documentation in either repo. Always workspace-relative.

**Rule 2:** No epic files with GitHub Project links, hour estimates, or status tracking in codex root. Scope specs
belong in `epics/`; execution tracking belongs in PM.

**Rule 3:** Audit output artifacts (violation reports, coverage checklists, classification JSONs) belong in
`unified-trading-pm/docs/audit/` or `plans/archive/` — not in codex sections.

**Rule 4:** Templates used by agents live in `unified-trading-pm/templates/` for agent access. Standards-defining
templates live in codex. Cross-reference rather than copy.

**Rule 5:** ADR promotion protocol — when an epic or planning document contains a locked architecture decision, create a
proper ADR in `11-project-management/decisions/` before archiving the source document. The ADR date should match the
original decision date.

**Rule 6:** Canonical scripts (`quality-gates.sh`, `quickmerge.sh`, propagation scripts) live in PM. Reference templates
(e.g., `06-coding-standards/quality-gates-template.sh`) may exist in codex for documentation purposes only and must be
clearly labelled as templates, not the canonical source.

---

## Renames in Flight

Tracks JSON / CLI / gRPC field renames currently mid-deprecation across the workspace. Each row lists the surface, the
canonical (new) key, the legacy key (kept as `validation_alias` or coalesce-fallback), and the ADR / plan that pinned
the rename. Remove rows from this table after the deprecation window closes and the legacy alias is dropped.

Legend: **migrate** = legacy alias kept for one release; **document** = legacy literal grandfathered (wire-format pin).

| Surface (file:line)                                                                                         | Canonical key | Legacy key                | Decision       | ADR / pin                                                           |
| ----------------------------------------------------------------------------------------------------------- | ------------- | ------------------------- | -------------- | ------------------------------------------------------------------- |
| `execution-service/execution_service/api/manual_schemas.py:65` (`ManualInstructionRequest`)                 | `asset_group` | `category`                | migrate        | `decisions/adr-2026-04-25-category-and-asset-group-field-naming.md` |
| `execution-service/execution_service/cli/backtest_checks.py:206` (preflight structured log)                 | `category`    | n/a (preflight bucket)    | document       | `decisions/adr-2026-04-25-...` (not asset_group axis)               |
| `strategy-service/strategy_service/cli/handlers/batch_handler.py:861` (`_build_backtest_result`)            | `asset_group` | `category`                | migrate        | `decisions/adr-2026-04-25-...`                                      |
| `strategy-service/strategy_service/cli/grid_generator.py:223` (`generate_strategy_id`)                      | `asset_group` | `category`                | migrate (read) | `decisions/adr-2026-04-25-...`                                      |
| `strategy-service/strategy_service/config.py:715` (`build_sports_strategy_config`)                          | `asset_group` | `category`                | migrate        | `decisions/adr-2026-04-25-...`                                      |
| `strategy-service/strategy_service/engine/core/config_loader.py:200` (`set_domain_from_category`)           | `asset_group` | `category`                | migrate (read) | `decisions/adr-2026-04-25-...`                                      |
| `strategy-service/strategy_service/models/output_schemas.py:33,128,...` (parquet `dimension_keys`)          | `category`    | n/a (parquet column)      | document       | `decisions/adr-2026-04-25-...` §3 (GCS / parquet pin)               |
| `strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog.py:429` (Polymarket params) | `category`    | n/a (Polymarket topic)    | document       | `decisions/adr-2026-04-25-...` (not asset_group axis)               |
| `position-balance-monitor-service/.../adapters/bybit.py:97,136` (Bybit v5 API)                              | `category`    | n/a (Bybit contract axis) | document       | `decisions/adr-2026-04-25-...` (Bybit wire format)                  |
