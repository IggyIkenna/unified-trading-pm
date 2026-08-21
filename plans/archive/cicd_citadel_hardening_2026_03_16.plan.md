---
doc_type: plan
title: cicd-citadel-hardening-2026-03-16
summary: Post-bootstrap CI/CD hardening. Lowers SIT filter to 0.1.0+ so deployment tests run for all repos. Adds plan locking
  to prevent premature archival. Adds smart context loading for conflict-resolution-agent. Adds PM/codex fast-path routing
  (plans/docs -> main, scripts/workflows -> staging). Changes PM semver policy from always_patch to agent for proper breaking-change
  detection on infrastructure files. Adds quickmerge integration smoke test to SIT.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [system-integration-tests, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-16'
type: infra
epic: epic-infra
completion_gates: {code: C5, deployment: D3, business: none}
repo_gates:
- {repo: system-integration-tests, code: C0, deployment: none, business: none}
- {repo: unified-trading-pm, code: C0, deployment: none, business: none}
- {repo: unified-trading-codex, code: C0, deployment: none, business: none}
depends_on: []
todos:
- {id: sit-lower-version-filter, content: '- [x] [AGENT] P0. Lower SIT deployment test filter from v1.0.0+ to v0.1.0+ in system-integration-tests smoke-test-gate.yml. Find the line that checks `Version(v) >= Version("1.0.0")` and change to `Version(v) >= Version("0.1.0")`. This ensures deployment tests run for all repos, not just graduated ones.

    ', status: done}
- {id: conflict-agent-context-window, content: '- [x] [AGENT] P0. Increase conflict-resolution-agent context window: change `head -80` to `head -250` per plan, total cap from `head -800` to `head -5000` in conflict-resolution-agent.yml lines 257-262. Prevents agents from missing todos buried past line 80.

    ', status: done}
- {id: conflict-agent-smart-plan-loading, content: '- [x] [AGENT] P0. Add smart plan loading to conflict-resolution-agent: pre-step that identifies which active plans mention the conflicted repo name, loads those plans in FULL (not truncated), and loads remaining plans at head -250. Replaces the current uniform head -80 approach. This ensures the agent always sees the complete context for plans relevant to the repo it is resolving conflicts in.

    ', status: done}
- {id: plan-format-structural-order, content: '- [x] [AGENT] P0. Update PLAN_FORMAT.md: add "Structural Order" section requiring todos BEFORE notes/context. Why: conflict-resolution-agent reads head -250 per plan; todos after line 250 are invisible. Order: frontmatter -> todos -> gates -> notes -> diagrams.

    ', status: done}
- {id: plan-structure-order-cursor-rule, content: '- [x] [AGENT] P0. Create cursor rule `cursor-rules/documentation/plan-structure-order.mdc` enforcing todos-before-notes order. Rule must specify: YAML frontmatter (with todos array) comes first, then completion/QG gates section, then notes/context/diagrams. Agents and humans MUST follow this order when creating or editing plans.

    ', status: done}
- {id: plan-locking-spec, content: '- [x] [AGENT] P0. Add `locked_by` and `locked_since` support to plan frontmatter spec in PLAN_FORMAT.md. Document: locked plans MUST NOT be archived by agents; only human with `[unlock-plan]` in commit message can delete. `locked_by` is a string (agent name or human username), `locked_since` is ISO 8601 date. Both fields are optional; presence of `locked_by` activates the lock.

    ', status: done}
- {id: plan-health-agent-locking, content: '- [x] [AGENT] P0. Update plan-health-agent.yml prompt: add locked_by check — skip archiving plans with locked_by field; report locked plans in output but don''t touch them. Add plan-level depends_on check — block archiving plan B if plan A depends_on it and plan A is not yet archived. Both checks prevent premature plan archival by autonomous agents.

    ', status: done}
- {id: quickmerge-doc-only-fastpath, content: '- [x] [AGENT] P0. Add PM/codex doc-only fast-path to quickmerge.sh: when repo is unified-trading-pm or unified-trading-codex AND only plans/**, docs/**, cursor-configs/**, cursor-rules/**, .cursorrules changed -> PR targets main directly (skip staging). Script/workflow changes still route through staging. Detection: `git diff --name-only` filtered against allowed doc-only paths. If ANY file is outside the allow-list, normal staging routing applies.

    ', status: done}
- {id: locked-plan-removal-qg-check, content: '- [x] [AGENT] P1. Add locked-plan-removal-check to PM quality-gates.sh: if git diff shows a locked plan being deleted and commit message lacks [unlock-plan], QG fails. Implementation: parse `git diff --cached --name-status` for deleted .md files, check each for `locked_by:` in the old version (via `git show HEAD:<path>`), reject if present and commit message missing `[unlock-plan]`.

    ', status: done}
- {id: pm-semver-policy-agent, content: '- [x] [AGENT] P1. Change PM semver_policy from `always_patch` to `agent` in workspace-manifest.json. PM''s semver-agent already exists — with `agent` policy, it will analyze commit diffs for scripts/ and .github/workflows/ and compute proper bump types (fix: -> PATCH, feat: -> MINOR, feat!: breaking change -> requires staging + SIT). This ensures infrastructure-breaking changes in PM are properly detected and routed.

    ', status: done}
- {id: quickmerge-integration-smoke-test, content: '- [x] [AGENT] P1. Add quickmerge integration smoke test to system-integration-tests: test that base-service.sh and base-library.sh source correctly, quality-gates.sh runs in dry-run mode for 1 sample repo per type (library, service, UI, API). Tests the 4-5 QG script inheritance paths without running full QG for all 70 repos. Validates that quickmerge two-pass model works end-to-end for each repo archetype.

    ', status: done}
- {id: docs-claude-md-update, content: '- [x] [AGENT] P1. Update CLAUDE.md (workspace root .claude/CLAUDE.md): add section on 1.0.0 graduation process (request-major-bump workflow dispatch, Telegram alert, /approve on GitHub issue). Add plan locking docs. Add doc-only fast-path routing explanation.

    ', status: done}
- {id: docs-sub-agent-rules-update, content: '- [x] [AGENT] P1. Update SUB_AGENT_MANDATORY_RULES.md: add rule that locked plans must never be archived or deleted by agents. Add rule that plan todos must appear before notes sections.

    ', status: done}
- {id: docs-codex-version-graduation, content: '- [x] [AGENT] P1. Update codex docs: add version-graduation.md in unified-trading-codex/08-workflows/ documenting the full 1.0.0 process. Update CI-CD-FLOW.md with the doc-only fast-path.

    ', status: done}
- {id: docs-agents-md-update, content: '- [x] [AGENT] P1. Update AGENTS.md: add locked plan protection rule and doc-only fast-path routing info.

    ', status: done}
isProject: false
---

## Execution DAG

```
Phase 1 (PARALLEL, no deps)
├── sit-lower-version-filter
├── conflict-agent-context-window
└── conflict-agent-smart-plan-loading
    ↓ QG gate: system-integration-tests QG pass, PM QG pass
Phase 2 (PARALLEL, no deps on Phase 1)
├── plan-format-structural-order
├── plan-structure-order-cursor-rule
├── plan-locking-spec
└── plan-health-agent-locking
    ↓ QG gate: PM QG pass
Phase 3 (SEQUENTIAL, depends on Phase 2)
├── quickmerge-doc-only-fastpath
└── locked-plan-removal-qg-check
    ↓ QG gate: PM QG pass
Phase 4 (SEQUENTIAL, depends on Phase 3)
├── pm-semver-policy-agent
└── quickmerge-integration-smoke-test
    ↓ QG gate: PM QG pass, SIT QG pass
Phase 5 (PARALLEL, depends on Phase 4)
├── docs-claude-md-update
├── docs-sub-agent-rules-update
├── docs-codex-version-graduation
└── docs-agents-md-update
    ↓ QG gate: PM QG pass, codex QG pass
```

## Success Criteria

### Per-Phase Gates

- **Phase 1**: system-integration-tests `bash scripts/quality-gates.sh` pass. PM `bash scripts/quality-gates.sh` pass.
  SIT deployment tests now run for 0.1.0+ repos. Conflict agent context window increased.
- **Phase 2**: PM `bash scripts/quality-gates.sh` pass. PLAN_FORMAT.md updated with structural order + locking spec.
  Cursor rule created. plan-health-agent.yml updated.
- **Phase 3**: PM `bash scripts/quality-gates.sh` pass. Quickmerge correctly routes doc-only PM/codex changes to main.
  QG correctly blocks locked plan deletion without `[unlock-plan]`.
- **Phase 4**: PM `bash scripts/quality-gates.sh` pass. SIT `bash scripts/quality-gates.sh` pass. PM semver_policy is
  `agent`. Quickmerge smoke test passes in SIT.
- **Phase 5**: PM `bash scripts/quality-gates.sh` pass. Codex `bash scripts/quality-gates.sh` pass. All documentation
  updated and consistent.

### Final Validation

- All 3 affected repos (system-integration-tests, unified-trading-pm, unified-trading-codex) pass
  `bash scripts/quality-gates.sh`
- No regressions in existing CI/CD pipeline behavior
- Quickmerge two-pass model still works for all repo types

## Pre-Audit Manifest

| Repo                     | Files Affected                                        | Action                                    |
| ------------------------ | ----------------------------------------------------- | ----------------------------------------- |
| system-integration-tests | `.github/workflows/smoke-test-gate.yml`               | Lower version filter to 0.1.0+            |
| unified-trading-pm       | `.github/workflows/conflict-resolution-agent.yml`     | Increase context window + smart loading   |
| unified-trading-pm       | `plans/PLAN_FORMAT.md`                                | Add structural order + locking spec       |
| unified-trading-pm       | `cursor-rules/documentation/plan-structure-order.mdc` | New cursor rule                           |
| unified-trading-pm       | `.github/workflows/plan-health-agent.yml`             | Add locking + depends_on checks           |
| unified-trading-pm       | `scripts/quickmerge.sh`                               | Add doc-only fast-path                    |
| unified-trading-pm       | `scripts/quality-gates.sh`                            | Add locked-plan-removal check             |
| unified-trading-pm       | `workspace-manifest.json`                             | Change PM semver_policy to agent          |
| unified-trading-pm       | `.claude/CLAUDE.md`                                   | Add graduation + locking + fast-path docs |
| unified-trading-pm       | `cursor-configs/SUB_AGENT_MANDATORY_RULES.md`         | Add locking + structure rules             |
| unified-trading-pm       | `cursor-configs/AGENTS.md`                            | Add locking + fast-path info              |
| unified-trading-codex    | `08-workflows/version-graduation.md`                  | New doc: 1.0.0 process                    |
| unified-trading-codex    | `08-workflows/CI-CD-FLOW.md`                          | Add doc-only fast-path                    |
| system-integration-tests | New test file for quickmerge smoke test               | Quickmerge integration test               |

## Notes

### Why Lower SIT Filter to 0.1.0+

All repos are currently at 0.x.x (pre-1.0.0). The existing 1.0.0+ filter means SIT deployment tests run for zero repos,
making them effectively dead code. Lowering to 0.1.0+ activates deployment tests for the entire workspace immediately.

### Why Smart Plan Loading for Conflict Agent

The conflict-resolution-agent resolves merge conflicts by reading active plans for context. With uniform `head -80`,
plans with todos after line 80 have their todos invisible to the agent. Smart loading ensures plans mentioning the
conflicted repo are loaded in full, while other plans get the expanded `head -250` truncation.

### Why Doc-Only Fast-Path

PM and codex repos contain both infrastructure code (scripts, workflows) and documentation (plans, cursor rules, docs).
Documentation changes are low-risk and should merge to main directly. Infrastructure changes (scripts/,
.github/workflows/) affect all repos and must go through staging + SIT validation. The fast-path avoids unnecessary SIT
cycles for pure documentation updates.

### Why PM Semver Policy Change

With `always_patch`, every PM commit gets a PATCH bump regardless of content. A breaking change to `quickmerge.sh` or
`quality-gates.sh` that affects all 67 repos would silently ship as a PATCH. With `agent` policy, the semver-agent
analyzes the diff and assigns MINOR/MAJOR bumps for breaking infrastructure changes, ensuring proper staging + SIT
routing.
