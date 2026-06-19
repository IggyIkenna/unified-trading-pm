---
status: retired
superseded_by: codex/08-workflows/ci-cd-flow.md
---

# Version Cascade Flow — RETIRED 2026-06-18

> **⚠️ RETIRED — superseded by the single CI/CD SSOT.** This doc described the retired three-tier
> `feat/* → staging → main` model with `--to-staging` per-unit ships and per-repo `version-bump.yml`. The as-built
> version cascade (semver-agent at the staging boundary, selective dependency-update fan-out, LDR-trunk promotion) is
> now documented in the one SSOT:
>
> - **Pipeline (as-built LDR-trunk + the mermaid):** `codex/08-workflows/ci-cd-flow.md` (§ "Dependency promotion")
> - **Cascade detail:** `codex/08-workflows/dependency-cascade.md` + `codex/08-workflows/version-graduation.md`
> - **Every workflow (auto-generated drill-down):** `docs/repo-management/CICD-WORKFLOW-CATALOG.md`
>
> The prior content lives in git history. Do not use this file.
