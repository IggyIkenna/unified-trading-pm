---
title: "Tooling-config standardization — python + frontend tool-config drift across workspace repos"
created: 2026-05-26
author: harsh-main
source:
  - "workspace-root audit 2026-05-26 (24 repos with Python + 2 UI repos)"
  - plans/active/issues/cme_legacy_instrument_id_renormalization_2026_05_26.md
priority: P2
status: active
locked_by: live-defi-rollout
locked_since: 2026-05-26
---

## What I found

### Tools in use

**Python toolchain (core 5, ~universal):** `ruff` (lint+format), `basedpyright` (typecheck), `pytest`, `coverage`,
`pre-commit`. Package manager: `uv`. **Inconsistent extras:** `mypy` (3 repos — drift), `bandit` (2 repos — drift).
Build backend: `hatchling` (21 repos) / `setuptools` (1 repo, alerting-service).

**Frontend toolchain (2 UI repos):** `prettier`, `eslint` (flat config), `typescript` (tsc), `vitest`, `@playwright/test`.
`deployment-ui` = Vite; `unified-trading-system-ui` = Next.js + `tailwindcss` + `husky` + `lint-staged`.

### Canonical config locations in PM (the rollout SSOT)

| Concern | Canonical source | Rollout |
| --- | --- | --- |
| Pre-commit (per type) | `scripts/pre-commit-templates/{python-service,python-library,docs,ui}.pre-commit-config.yaml` | (setup propagates) |
| Quality gates | `scripts/quality-gates-base/base-{service,library}.sh` | `scripts/propagation/rollout-quality-gates-unified.py` |
| CI workflows (py + ui) | `scripts/workflow-templates/` + `scripts/workflow-templates-ui/` | `scripts/propagation/rollout-quality-gates-ci-workflows.py` |
| Editor strict-lint args (`--line-length=120`) | `scripts/propagation/update-workspace-strict-linting.py` | (writes `.vscode`) |
| Version pin drift | `scripts/quality_gates/check_workspace_pyproject_pin_drift.py` | (checks peer floors) |
| Prose SSOT | `codex/06-coding-standards/ruff-discipline.md` (line-length **120**) + `quality-gates.md` | — |

**ROOT GAP:** pre-commit / QG / CI are templated + rolled out, but the actual **`[tool.ruff]` / `[tool.basedpyright]` /
`[tool.pytest]` sections in each repo's `pyproject.toml` are NOT centrally templated** — they're hand-maintained per
repo with only a version-floor drift checker. That absence is the root cause of every deviation below.

### Deviations

**Python:**

| # | Deviation | Repos |
| --- | --- | --- |
| P1 | **no Python tooling at all** (no pyproject/ruff/basedpyright/pytest) — 252 `.py` (7 real `scripts/`, 245 vendored `context/codex/`) | `unified-trading-system-ui` |
| P2 | ruff `line-length = 100` (workspace std = 120) | `alerting-service` |
| P3 | basedpyright not strict — `standard` (pm), no `typeCheckingMode` + no `pyrightconfig.json` (agent-orchestrator) | `unified-trading-pm`, `agent-orchestrator` |
| P4 | `mypy` config alongside basedpyright (no mypy plugins used → redundant) | mdps, ml-training-service, UTL |
| P5 | `bandit` config in only 2 repos (inconsistent) | market-tick-data-service, strategy-service |
| P6 | build-backend `setuptools` (std = hatchling) | alerting-service |
| P7 | `[tool.ruff.format]` section absent (falls back to defaults) | e2e, ibkr, ml-service, ml-training, sys-int-tests, trading-agent, pm |
| P8 | ruff `target-version` absent | e2e-testing, system-integration-tests |
| P9 | `[tool.ruff.lint.mccabe]` absent | agent-orchestrator, batch-live-recon, ibkr |
| P10 | pytest + coverage config absent | agent-orchestrator, ibkr-gateway-infra |
| P11 | typecheck config duplication: 21 repos carry **both** `[tool.basedpyright]` (pyproject) **and** `pyrightconfig.json` (basedpyright honors the JSON, ignores the pyproject section → silent drift); agent-orch = pyproject-only; e2e = json-only | workspace-wide |

**Frontend (deployment-ui vs unified-trading-system-ui):** version drift (prettier 3.1.1 vs 3.6.2; eslint 9.0 vs 9.39;
ts 5.3 vs 5.7; vitest 4.1.0 vs 4.1.1); `deployment-ui` has **no `.prettierrc` file** + no husky/lint-staged; different
build systems (Vite vs Next.js). No canonical frontend-config template in PM (only `ui.pre-commit-config.yaml`).

## Why it matters

Tool-config drift produces (a) the cross-repo "spurious formatting diff" incident (alerting LL=100 vs a 120 format
pass — see linked CME issue context), (b) per-repo quality gates that enforce different rules, (c) under-enrolled new
repos (agent-orchestrator), and (d) 252 ungoverned `.py` in the UI repo. Single source of truth for tool config is
missing at the `pyproject [tool.*]` layer.

## Recommended decision (operator-directed 2026-05-26)

**Decided:**

1. **alerting-service** `line-length` 100 → **120** (P2).
2. **ruff** pinned **`==0.15`** consistently workspace-wide; add `target-version = "py313"` where missing (P8).
3. **basedpyright** strictness levels kept **as-is** (strict standard); `agent-orchestrator` gets strict on enrollment.
   (`unified-trading-pm = standard` retained per operator — scripts-only repo.)
4. **agent-orchestrator** (newest repo — tooling not yet enrolled): enroll **full Python tooling** (ruff incl.
   `ruff.format` + mccabe, pytest, coverage, basedpyright strict + `pyrightconfig.json`) **and UI tooling** (Vite
   dashboard → prettier/eslint/tsc/vitest/playwright).
5. **mypy** removed from the 3 repos — basedpyright (strict) is a superset of the workspace's usage; confirmed **no
   mypy plugins** in any of them, so nothing is lost.
6. **build backend**: no `setuptools` anywhere → fix alerting-service. **DECISION POINT**: target = uv-native
   `uv_build` (per operator "all build backend should be uv") **vs** the current 21-repo de-facto standard `hatchling`
   — switching to `uv_build` is a 21-repo change; aligning alerting to `hatchling` is 1-repo. Operator to confirm
   target.
7. **`[tool.basedpyright]` vs `pyrightconfig.json`**: pick ONE per repo (basedpyright honors `pyrightconfig.json` when
   present) and apply consistently; remove the redundant one (P11).
8. **unified-trading-system-ui**: add Python tooling for its `scripts/*.py` (ruff + basedpyright), excluding the
   vendored `context/codex/` copies.

**Decision needed:**

- **bandit** (P5): standardize — recommend enabling ruff's `S` (flake8-bandit) ruleset workspace-wide (already
  available in ruff, no extra tool) instead of the standalone `bandit` in 2 repos. Operator to confirm scope.

**Root remediation (unblocks all above):**

- Create a **canonical `pyproject [tool.*]` snippet template** in PM (ruff / basedpyright / pytest / coverage) +
  a rollout script, and extend `check_workspace_pyproject_pin_drift.py` to enforce **sections + values** (not just
  version floors). Add a canonical **frontend** tool-config template set (prettier/eslint/tsconfig/vitest/playwright).

## Phased plan

- **Phase 0** — write canonical `[tool.*]` pyproject template + frontend template in PM (this is the missing SSOT).
- **Phase 1** — quick decided fixes: alerting LL→120 + build-backend, ruff `==0.15` + `target-version`, mypy removal.
- **Phase 2** — agent-orchestrator full enrollment (py + ui).
- **Phase 3** — basedpyright/pyrightconfig dedup + `ruff.format`/mccabe/pytest/coverage section backfill across repos.
- **Phase 4** — UI repo python tooling + frontend version alignment; wire section-level drift enforcement into QG.

## Resolution

_(updated as phases land)_
