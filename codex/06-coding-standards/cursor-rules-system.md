---
doc_type: codex-ssot
title: Cursor Rules System
summary: How cursor rules work — directory layout, priority tiers, glob triggers, and how to add a rule
status: living
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer]
tags: [cursor-rules, meta]
related: []
created: "2026-03-27"
owner: pm-orchestrator
last_reviewed: "2026-06-25"
code_refs: [.cursor/rules/]
---

# Cursor Rules System

> How the `.cursor/rules/` system works — where rules live, how they load, and how to add one. Index of all rules:
> `.cursor/rules/README.md`.

---

## How rules load

Cursor loads `.mdc` files recursively from `.cursor/rules/`. Two loading modes:

| Mode                  | Frontmatter                           | When active                                                                  |
| --------------------- | ------------------------------------- | ---------------------------------------------------------------------------- |
| **Always-apply**      | `alwaysApply: true`                   | Every context, every file                                                    |
| **Context-sensitive** | `alwaysApply: false` + `description:` | Cursor selects via semantic match on `description:` + optional glob triggers |

Only `core/` rules set `alwaysApply: true`. All other rules are context-sensitive — they fire when Cursor judges the
active task matches the rule's `description:`.

---

## Directory layout

```
.cursor/rules/
  core/           # alwaysApply: true — always active
  quality-gates/  # QG, basedpyright, ruff, complexity limits
  testing/        # Test standards, coverage, integration layers
  ci-cd/          # CI/CD, quickmerge, Cloud Build
  architecture/   # DAG, batch-live symmetry, service structure
  imports/        # External imports, UAC contracts, API usage
  config/         # ConfigStore, project IDs, workspace config
  dependencies/   # Dep management, uv, version pinning
  documentation/  # Codex, plans, prettier, adding rules
  ui/             # TypeScript QG, UI setup
  services/       # Service setup, ServiceCLI
  standards/      # Coding standards, anti-patterns
  workflow/       # Agent workflow, rollout, PR review
  misc/           # Observability, validators, sync
```

---

## Priority tiers

| Priority | Tier          | Meaning                                                                      |
| -------- | ------------- | ---------------------------------------------------------------------------- |
| P100     | Blocking      | `no-summary-docs`: violations block task completion                          |
| P95      | Structure     | `plan-placement`, `sub-agent-workflow-standard`: controls where artifacts go |
| P90      | Safety        | Runtime verification, never-revert-local-changes, basedpyright-safety        |
| P80      | Standards     | Coding standards, import rules, type rules                                   |
| P70      | Maintenance   | Codex updates, rollout tracking, deprecation                                 |
| P50      | Informational | Workflow guidance, sub-agent patterns                                        |

Higher priority rules take precedence when two rules conflict.

---

## Glob triggers (context-sensitive)

Some rules additionally restrict to specific file patterns. Examples:

| File pattern                      | Rules triggered                                                                     |
| --------------------------------- | ----------------------------------------------------------------------------------- |
| `**/pyproject.toml`, `**/uv.lock` | `uv-lock-file.mdc`, `workspace-venv-sync.mdc`                                       |
| `**/.github/workflows/*.yml`      | `path-dependency-ci.mdc`                                                            |
| `**/*.py`                         | `no-type-any-use-specific.mdc`, `no-empty-fallbacks.mdc`, `code-quality-limits.mdc` |
| `**/tests/**`                     | `test-quality-standards.mdc`, `test-coverage-targets.mdc`                           |

---

## Rule file format

```yaml
---
description: "One-line description Cursor uses for semantic matching"
alwaysApply: false # true only in core/
priority: 70 # see tier table above
tags: [tag1, tag2]
---
# Rule Title
RULE: what to do
WHY: rationale (often a past incident)
CODEX: path/to/codex/ssot.md # the durable SSOT for detail
DO: examples of correct usage
NEVER: examples of banned patterns
```

The `CODEX:` line is the pointer to the corresponding codex doc (this document, or another). Deep-link anchors
(`codex/foo.md#section-name`) require that section to actually exist in the codex doc — otherwise the deep-link is a
broken pointer.

---

## How to add a rule

1. Pick the right directory (match the category table above).
2. Set `alwaysApply: false` unless the rule must fire on EVERY file (reserve `core/` for that).
3. Write a crisp `description:` — Cursor uses it for semantic matching.
4. Set `priority:` using the tier table.
5. Add a `CODEX:` line pointing to the durable SSOT (create the codex doc first if it doesn't exist).
6. Keep the rule body short: `RULE` / `WHY` / `DO` / `NEVER` — detail belongs in the codex doc.
7. Never hand-edit per-repo workflow copies — cursor rules live only in `unified-trading-pm/`.

---

## SSOT ownership

The canonical rules directory is `unified-trading-pm/.cursor/rules/`. The workspace symlink at `.cursorrules` (root)
forwards to the workspace-level rules. Per-repo `.cursor/rules/` directories do NOT exist — all rules are centrally
managed in PM.
