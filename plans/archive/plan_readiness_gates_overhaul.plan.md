---
doc_type: plan
title: plan-readiness-gates-overhaul
summary: Introduce 3-tier readiness gates (Code/Deployment/Business) into every plan; add ai/ vs active/ split; propagate
  rules to all agent contexts
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-11'
type: infra
epic: none
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: unified-trading-pm, code: C2, deployment: none, business: none}
depends_on: []
todos:
- {id: phase-0-self-register, content: Create this plan file in active/, status: done, note: Done 2026-03-11 — this file}
- {id: phase-1a-plan-format-ssot, content: Create unified-trading-pm/plans/PLAN_FORMAT.md (canonical gate spec), status: in_progress, note: ''}
- {id: phase-1b-ai-readme, content: Create unified-trading-pm/plans/ai/README.md (explain ai/ vs active/), status: in_progress, note: ''}
- {id: phase-1c-cursor-rule, content: Create cursor-rules/core/plan-readiness-gates.mdc, status: in_progress, note: ''}
- {id: phase-1d-plan-placement, content: Update cursor-rules/core/plan-placement.mdc — add ai/ promotion workflow, status: in_progress, note: ''}
- {id: phase-1e-workflow-rule, content: Update cursor-rules/workflow/plans-to-deployable-workflow.mdc — reference 3-tier model, status: in_progress, note: ''}
- {id: phase-1f-sub-agent-rules, content: Update cursor-configs/SUB_AGENT_MANDATORY_RULES.md — add Plan Format Rules section, status: in_progress, note: ''}
- {id: phase-2-reformat-group-a, content: Add completion_gates + repo_gates YAML to Group A plans (CI/CD/QG/AI-agent), status: todo, note: ''}
- {id: phase-2-reformat-group-b, content: Full 3-tier reformat for all remaining ~27 feature/business plans, status: todo, note: ''}
- {id: phase-3-index-update, content: 'Update INDEX.md — epic structure, gate legend, plan classification table', status: todo, note: ''}
- {id: phase-3-verify, content: Verify all active .md files have completion_gates + repo_gates, status: todo, note: ''}
isProject: true
---

# Plan Readiness Gates Overhaul

## Overview

Introduces a 3-tier readiness model (Code → Deployment → Business) and per-plan completion gates to every plan in
`plans/active/`. Also separates AI-generated plans (`plans/ai/`) from user-approved active plans (`plans/active/`), and
propagates the new rules to all agent contexts.

## Gate Definitions

### Code Readiness (C)

- C0: Not started
- C1: Implementation complete (code written, not tested)
- C2: Unit tests passing (no regression, coverage maintained)
- C3: Linter + Codex gates (ruff, basedpyright)
- C4: Full quality-gates.sh Pass 1
- C5: Quickmerge complete (merged to staging/main)

### Deployment Readiness (D)

- D1: Deployable (infra provisioned, configs, Docker builds)
- D2: CI/GHA smoke tests pass (emulators/mocks, no real service calls)
- D3: Staging integration tests pass (real service/API calls, SIT suite)
- D4: Load/performance tests pass in staging
- D5: Production-ready (all security + operational gates)

### Business Readiness (B)

- B1: Acceptance criteria defined
- B2: Scenario analysis complete (edge cases, load, adversarial)
- B3: Performance targets met (ML accuracy, strategy P&L, execution alpha, latency KPIs)
- B4: Batch vs live validation (t+1 check, batch output matches live expectations)
- B5: Staging vs live parity (N-minute replay against prod-equivalent environment)
- B6: User approved (human sign-off)

## Archive Criteria by Plan Type

| Type                   | Minimum to archive                                                         |
| ---------------------- | -------------------------------------------------------------------------- |
| `code`                 | C5 for all repos in repo_gates                                             |
| `infra` / `deployment` | D3 for all repos in repo_gates (required even during code-completion epic) |
| `business`             | B6 (user approved) + domain-specific B3 targets declared                   |
| `mixed`                | Highest required gate across all types declared                            |

## SSOT

- Full spec: `unified-trading-pm/plans/PLAN_FORMAT.md`
- Cursor rule: `unified-trading-pm/cursor-rules/core/plan-readiness-gates.mdc`
- Sub-agent rules: `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` §9
