---
scope: [engineer, admin]
last_reviewed: 2026-05-17
---

# CI/CD Setup

> **SSOT**: `codex/08-workflows/ci-cd-flow.md`
>
> That document is the canonical reference for: which scripts own what (QG base scripts, reusable workflows, rollout
> scripts), how to add a dependency correctly (no direct installs), the two-pass quickmerge model, branch model and CI
> triggers, and adding a new repo.

Do not duplicate CI/CD setup steps here. Read the SSOT first.

## Quick Reference

| Task                                          | Where                                                                                                                                                                                          |
| --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Fix a quality gate check                      | `unified-trading-pm/scripts/quality-gates-base/base-service.sh`                                                                                                                                |
| Fix a CI workflow step                        | `unified-trading-pm/.github/workflows/python-quality-gates-v2.yml` (v1 `python-quality-gates.yml` kept as ghost-target only)                                                                   |
| Customize CI Telegram alert / failure excerpt | `ci-cd-ssot.md` § 5c "Telegram Notification Flow"                                                                                                                                              |
| Add a dep to a repo                           | `pyproject.toml` → `workspace-manifest.json` → `uv lock` → `uv sync`                                                                                                                           |
| Generate / update a repo's CI workflow        | `bash scripts/workflow-templates/rollout-workflow-templates.sh --repo <name> --template quality-gates-v2.yml` (renders `quality-gates-v2.yml.tmpl`; the action ref is baked into the template) |

See also: `05-infrastructure/new-repo-setup.md` — full new-repo checklist. See also: `05-infrastructure/README.md` —
infrastructure overview.
