# CI/CD Plans & Infrastructure

Core CI/CD infrastructure (quality gates, quickmerge, setup.sh) is implemented and in production use across all repos.

This directory contains remaining plans for ongoing improvements and reference data.

---

## Files

| File | Purpose |
|------|---------|
| `00-MASTER-CICD-PLAN.md` | Master CI/CD plan — canonical execution order |
| `02-background-agents-setup.md` | Background agent setup for parallel work |
| `05-schema-validation.md` | GCS + BigQuery schema validation |
| `07-quality-gates-performance.md` | Quality gates performance optimization |
| `DEPENDENCY-MATRIX-CANONICAL.json` | Canonical dependency matrix for all repos |
| `EXECUTION-SERVICES-50-PERCENT-COVERAGE-PLAN.md` | Test coverage plan for execution services |
| `UNIFIED-QUICKMERGE-TEMPLATE.sh` | Reference quickmerge template |
| `WORKSPACE-CONFIGS-ADJUSTMENT-PLAN.md` | Workspace configuration adjustment plan |

---

## Status

- **Implemented:** Claude Code integration, CI/CD alignment (quality-gates.sh, quickmerge.sh, setup.sh), multi-repo versioning
- **In progress:** Background agents, schema validation, quality gates performance, test coverage improvements
- **Reference:** Dependency matrix and quickmerge template are living reference docs
