# Quality Gate Bypass Audit

<!-- e2e version-bump flow test -->

## 1. PM Repo — Non-Standard Structure (Audited Exception)

**unified-trading-pm** is not a deployable package. It is the project management, docs, and scripts canonical repo. Quality gates apply PM-specific handling:

| Check               | Standard (deployable package)           | PM Exception                                           |
| ------------------- | --------------------------------------- | ------------------------------------------------------ |
| **basedpyright**    | `REPO_MODULE/` (e.g. `my_service/`)     | `scripts/ github-integration/` — no Python package dir |
| **cloudbuild.yaml** | Required                                | Skipped — PM is not deployed                           |
| **coverage**        | `--cov=REPO_MODULE --cov-fail-under=70` | `--cov=scripts/manifest --cov-fail-under=0`            |
| **SOURCE_DIRS**     | `REPO_MODULE/ tests/`                   | `scripts/ github-integration/ tests/`                  |

**Rationale:** PM hosts automation scripts, cursor rules, workspace manifest, and plans — not a Cloud Run service or installable library. Documented in `.cursor/rules/pm-repo-context.mdc`.

---

## 2.1 File Size Exceptions

None.

## 2.2 Ruff Exceptions

None.

## 2.3 Basedpyright Exceptions

None.
