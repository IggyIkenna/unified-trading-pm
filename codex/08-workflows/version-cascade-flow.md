---
scope: [engineer, admin]
---

# Version Cascade Flow — see ci-cd-flow.md (redirect)

> **Superseded 2026-06-18.** This was a thin mirror of a now-retired PM doc. The version cascade is documented as part
> of the single CI/CD SSOT:
>
> - **`codex/08-workflows/ci-cd-flow.md`** § "Dependency promotion" — the as-built cascade (semver-agent at the staging
>   boundary, range-pin floors, selective `dependency-update` fan-out, MAJOR-bump SIT cascade).
> - **`codex/08-workflows/dependency-cascade.md`** — the cascade mechanics in detail.
> - **`codex/08-workflows/version-graduation.md`** — the 0.x → 1.0.0 graduation rules.
>
> This stub remains only so existing index/rule references resolve. The retired three-tier / `--to-staging` / per-repo
> `version-bump.yml` model is gone (LDR-trunk decoupling).
