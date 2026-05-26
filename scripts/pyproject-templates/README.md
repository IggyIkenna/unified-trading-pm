# Canonical Python tooling config (pyproject `[tool.*]`)

SSOT for the per-repo `pyproject.toml` tool sections. Closes the gap where
pre-commit / quality-gates / CI were templated but the actual `[tool.ruff]` /
`[tool.basedpyright]` / `[tool.pytest]` / `[tool.coverage]` sections were
hand-maintained per repo and drifted.

Audit + decisions: `plans/active/issues/tooling_config_standardization_2026_05_26.md`.

## Format decisions (2026-05-26)

| Tool | Lives in | Notes |
| --- | --- | --- |
| ruff (lint+format) | `pyproject.toml` `[tool.ruff]` | line-length 120, target py313, double-quote |
| basedpyright | `pyproject.toml` `[tool.basedpyright]` | **strict**; `pyrightconfig.json` is DELETED workspace-wide |
| pytest | `pyproject.toml` `[tool.pytest.ini_options]` | — |
| coverage | `pyproject.toml` `[tool.coverage.report]` | `fail_under` is a per-type **floor** |
| pre-commit | `.pre-commit-config.yaml` (YAML) | tool-mandated; see `../pre-commit-templates/` |
| build backend | `[build-system]` = **hatchling** | no setuptools, no per-repo backend drift |
| mypy | — | **removed** (basedpyright superset; no mypy plugins were used) |
| bandit | — | **pending**: prefer ruff `S` (flake8-bandit) rules over standalone bandit |

**Frontend (UI repos):** tool-mandated dedicated files — `eslint.config.mjs`,
`tsconfig.json`, `vitest.config.ts`, `playwright.config.ts`, and a canonical
`.prettierrc.json`. Version-align via `package.json`. (Frontend canonical base
configs are a follow-up; not in this template set yet.)

## Per-type / per-repo variation (intentional — do NOT flatten)

- **coverage `fail_under`**: floor = **library ≥ 80**, **service ≥ 70**. Above-floor
  ratchets (e.g. `unified-api-contracts` 84) are kept.
- **`include` / `omit`**: per-repo (package dir + integration-only modules).
- **`executionEnvironments[].extraPaths`**: per-repo (its workspace deps).
- `unified-trading-pm` is scripts-only (no package) — coverage/strictness as fit.

## basedpyright consolidation (why delete pyrightconfig.json)

`pyrightconfig.json` took runtime precedence over `[tool.basedpyright]`, and the
two had **diverged**: the JSON set `reportUnknown*=none` in 7 repos while the
TOML + the CLAUDE.md rule + QG STEP 5.21 declared `=error`. Net effect: the gate
asserted strict-on-paper while the actual type check ran softer. Deleting the
JSON + keeping the strict `[tool.basedpyright]` makes runtime == gate == docs.

The cross-repo resolution that lived in the JSON (`executionEnvironments` +
`extraPaths`) moves into `[[tool.basedpyright.executionEnvironments]]` — fully
supported in pyproject.

## Rollout (per repo)

1. Merge `canonical-tool-sections.toml` into the repo's `pyproject.toml`; fill
   `<PACKAGE_DIR>`, `extraPaths`, `fail_under` (70 service / 80 library or its
   existing higher ratchet), and the repo's `omit` list.
2. `git rm pyrightconfig.json`.
3. Ensure `[build-system].build-backend = "hatchling.build"`.
4. Run the repo's `bash scripts/quality-gates.sh` and clear any newly-surfaced
   strict type errors.

**Known restore backlog** — 7 repos had `reportUnknown*` relaxed to `none` and
will surface errors when strict is restored (5 during the March QG setup; 2 on
2026-05-15 during reportAny cleanup): `unified-trading-pm`, `unified-trading-library`,
`deployment-service`, `strategy-service`, `client-reporting-api`, **`execution-service`**,
**`features-service`** (the last two are the largest backlogs).
