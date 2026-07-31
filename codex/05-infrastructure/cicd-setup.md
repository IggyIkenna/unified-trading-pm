---
doc_type: codex-ssot
title: CI/CD Setup
summary:
  Quick-reference pointer to the CI/CD SSOT (/codex/08-workflows/ci-cd-flow.md) — a table of where to fix a quality-gate
  check, a CI workflow step, add a dependency, or regenerate a repo's quality-gates-v2 workflow via
  rollout-workflow-templates.sh.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quality-gates, quickmerge, infrastructure, ci-cd]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /codex/05-infrastructure/new-repo-setup.md,
    /codex/05-infrastructure/dual-cloud-image-builds.md,
  ]
created: 2026-03-27
authoritative_for: [redirect stub — CI/CD flow SSOT is /codex/08-workflows/ci-cd-flow.md]
referenced_by:
  [
    /codex/05-infrastructure/README.md,
    /codex/05-infrastructure/act-preflight-coverage.md,
    /codex/05-infrastructure/auth-setup.md,
    /codex/05-infrastructure/deployment-clusters-live-vs-batch.md,
  ]
owner:
last_reviewed: 2026-09-06
code_refs:
---

# CI/CD Setup

> **SSOT**: `/codex/08-workflows/ci-cd-flow.md`
>
> That document is the canonical reference for: which scripts own what (QG base scripts, reusable workflows, rollout
> scripts), how to add a dependency correctly (no direct installs), the two-pass quickmerge model, branch model and CI
> triggers, and adding a new repo.

Do not duplicate CI/CD setup steps here. Read the SSOT first.

> **[2026-07-31 freshness re-review]** Two pointers in the table below were stale and are corrected: the CI notification
> path is **Slack** (`ci-failures` channel via the reusable `notify-slack.yml` carrier), not Telegram, and the file
> `ci-cd-ssot.md` no longer exists — it is now
> [`/codex/08-workflows/ci-cd-flow.md`](/codex/08-workflows/ci-cd-flow.md). Everything else in the table verified
> present.

## Quick Reference

| Task                                          | Where                                                                                                                                                                                          |
| --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Fix a quality gate check                      | `unified-trading-pm/scripts/quality-gates-base/base-service.sh`                                                                                                                                |
| Fix a CI workflow step                        | `unified-trading-pm/.github/workflows/python-quality-gates-v2.yml` (the v1 `python-quality-gates.yml` ghost-target no longer exists)                                                           |
| Customize a CI failure alert / failure excerpt | **Slack**, not Telegram — the reusable `notify-slack.yml` carrier into the `ci-failures` channel; SSOT [`/codex/04-architecture/ci-alerting.md`](/codex/04-architecture/ci-alerting.md)        |
| Add a dep to a repo                           | `pyproject.toml` → `workspace-manifest.json` → `uv lock` → `uv sync`                                                                                                                           |
| Generate / update a repo's CI workflow        | `bash scripts/workflow-templates/rollout-workflow-templates.sh --repo <name> --template quality-gates-v2.yml` (renders `quality-gates-v2.yml.tmpl`; the action ref is baked into the template) |

See also: [`/codex/05-infrastructure/new-repo-setup.md`](/codex/05-infrastructure/new-repo-setup.md) — full new-repo checklist. See also: [`/codex/05-infrastructure/README.md`](/codex/05-infrastructure/README.md) —
infrastructure overview.
