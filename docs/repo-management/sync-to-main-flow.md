---
status: retired
superseded_by: codex/08-workflows/ci-cd-flow.md
---

# Sync-to-Main Flow — RETIRED 2026-06-18

> **⚠️ RETIRED — superseded by the single CI/CD SSOT.** This doc described the pre-LDR-trunk "quickmerge → PR to main"
> per-repo sync, which is no longer the model. Today a unit lands on `live-defi-rollout` via
> `quickmerge --agent --files` and the **Tier-C drain** (`ldr-to-staging-promote`, every 15 min) promotes it onward. The
> one SSOT is:
>
> - **Pipeline (as-built LDR-trunk + the mermaid):** `codex/08-workflows/ci-cd-flow.md`
> - **Every workflow (auto-generated drill-down):** `docs/repo-management/CICD-WORKFLOW-CATALOG.md`
>
> The prior content lives in git history. For the `sync-all-to-main.sh` script itself, see its `--help` /
> `scripts/repo-management/README-ALIGNMENT-AND-SETUP.md`.
