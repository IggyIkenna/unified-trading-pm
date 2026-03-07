# Repo Audit Checklist (Repo-by-Repo)

**Reference:** plans_to_deployable_unified_audit Phase 6 (run_validators.py --scope/--repo-type) **Deployment
checklist:** deployment-service/configs/checklist.template.service.yaml

---

## Phases 1–7 (from deployment checklist)

| Phase | Focus                                                                      |
| ----- | -------------------------------------------------------------------------- |
| 1     | Repository foundation (pyproject, uv.lock, UnifiedCloudConfig, Dockerfile) |
| 2     | Testing & Quality (unit tests, quality gates, cloudbuild)                  |
| 3     | Deployment infrastructure (sharding, dependencies.yaml, terraform)         |
| 4     | Local validation (runs locally, schema, timestamp alignment)               |
| 5     | Production deployment (image build, deployment)                            |
| 6     | Documentation (README, architecture, schema)                               |
| 7     | Data catalogue (data-catalogue.yaml, pipeline chain)                       |

---

## Per-Repo Audit

1. Run `run_validators.py --scope <repo>` (when available)
2. Run `bash scripts/quality-gates.sh --no-fix`
3. Check checklist.{service}.yaml exists and is filled
4. Verify alignment with docs (no orphan README, no superseded patterns)
5. Audit-worthy: document blockers, partial items, next actions
