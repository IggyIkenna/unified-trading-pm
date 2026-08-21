---
doc_type: plan
title: Workspace Quickmerge Validation Plan
summary: Every repo passing quickmerge in dependency order across feature → staging → prod. Topological sort T0→T1→T2→T3→services;
  validate-workspace-quickmerge.sh script.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-05'
todos:
- {id: topological-sort, content: Topological sort from workspace-manifest.json (T0→T1→T2→T3→services→APIs→UIs), status: completed}
- {id: quickmerge-per-repo, content: Run quickmerge --unit-only per repo in dependency order, status: completed}
- {id: dep-branch-cascade, content: Use --dep-branch when deps have local changes; cascade validation, status: completed}
- {id: validate-script, content: 'Create unified-trading-pm/scripts/validate-workspace-quickmerge.sh. SPEC: (1) reads workspace-manifest.json to generate topological sort (T0→T1→T2→T3→services→APIs→UIs); (2) for each repo in sorted order: check scripts/quickmerge.sh exists, run quickmerge --unit-only --no-push, record exit code; (3) if a repo fails, cascade: skip all repos that depend on it (from manifest.dependencies); (4) write per-repo pass/fail matrix to artifacts/quickmerge-matrix.json with fields: repo, status (PASS/FAIL/SKIPPED), exit_code, skipped_dependents; (5) exit 0 if all non-skipped repos pass, exit 1 otherwise. GATE: script runs on canary set (all T0 repos) and produces artifacts/quickmerge-matrix.json with correct tier ordering.', status: completed}
- {id: ci-integration, content: 'CI integration for workspace-wide validation — DECISION: GitHub Actions (existing version-bump.yml pattern). Add unified-trading-pm/.github/workflows/workspace-quickmerge-validation.yml: triggers on workflow_dispatch and on schedule (weekly); runs validate-workspace-quickmerge.sh; uploads artifacts/quickmerge-matrix.json as workflow artifact; posts per-repo pass/fail matrix as workflow summary. GATE: workflow file exists and passes yamllint; manual dispatch from GitHub UI runs without error; matrix artifact uploaded.', status: completed}
isProject: false
---

# Workspace Quickmerge Validation Plan (Dependency Order)

**Order:** 1 (see master_pre_deployment_plan_chain.md) **Reference:** quickmerge.sh, 00-MASTER-CICD-PLAN.md

---

## Blockers

| Blocker                                      | Type          | Specific Dependency                                                                   | Resolution                                                                                                 |
| -------------------------------------------- | ------------- | ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| quickmerge.sh not rolled out to all 55 repos | `[PLAN_TODO]` | [phase1_foundation_prep.md](phase1_foundation_prep.md) § todo `ci-quickmerge-rollout` | scripts/quickmerge.sh must exist in all 55 repos before this plan can run validate-workspace-quickmerge.sh |
| Topological sort script not yet written      | `[PLAN_TODO]` | This plan § todo `validate-script`                                                    | validate-workspace-quickmerge.sh must be created first (todo `validate-script` in this plan)               |

---

## Goal

Every repo passing quickmerge in dependency order across 3 stages: feature → staging → prod.

---

## Stages

| Stage   | Branch  | Quickmerge behaviour             |
| ------- | ------- | -------------------------------- |
| feature | feat/\* | --no-pr; QG only                 |
| staging | staging | Full quickmerge + PR to main     |
| prod    | main    | Merge from staging; version bump |

---

## Dependency-Order Validation

1. Topological sort from workspace-manifest.json (T0→T1→T2→T3→services→APIs→UIs)
2. Run quickmerge --unit-only per repo in order
3. Cascade: --dep-branch when deps have local changes
4. Script: validate-workspace-quickmerge.sh (to be created)

---

## Deliverables

- Script to run quickmerge in dependency order
- Per-repo pass/fail matrix
- CI integration for workspace-wide validation
