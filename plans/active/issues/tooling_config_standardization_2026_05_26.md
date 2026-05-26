---
title: "Tooling-config standardization — python + frontend tool-config drift across workspace repos"
created: 2026-05-26
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

**Frontend toolchain (2 UI repos):** `prettier`, `eslint` (flat config), `typescript` (tsc), `vitest`,
`@playwright/test`. `deployment-ui` = Vite; `unified-trading-system-ui` = Next.js + `tailwindcss` + `husky` +
`lint-staged`.

### Canonical config locations in PM (the rollout SSOT)

| Concern                                       | Canonical source                                                                              | Rollout                                                     |
| --------------------------------------------- | --------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| Pre-commit (per type)                         | `scripts/pre-commit-templates/{python-service,python-library,docs,ui}.pre-commit-config.yaml` | (setup propagates)                                          |
| Quality gates                                 | `scripts/quality-gates-base/base-{service,library}.sh`                                        | `scripts/propagation/rollout-quality-gates-unified.py`      |
| CI workflows (py + ui)                        | `scripts/workflow-templates/` + `scripts/workflow-templates-ui/`                              | `scripts/propagation/rollout-quality-gates-ci-workflows.py` |
| Editor strict-lint args (`--line-length=120`) | `scripts/propagation/update-workspace-strict-linting.py`                                      | (writes `.vscode`)                                          |
| Version pin drift                             | `scripts/quality_gates/check_workspace_pyproject_pin_drift.py`                                | (checks peer floors)                                        |
| Prose SSOT                                    | `codex/06-coding-standards/ruff-discipline.md` (line-length **120**) + `quality-gates.md`     | —                                                           |

**ROOT GAP:** pre-commit / QG / CI are templated + rolled out, but the actual **`[tool.ruff]` / `[tool.basedpyright]` /
`[tool.pytest]` sections in each repo's `pyproject.toml` are NOT centrally templated** — they're hand-maintained per
repo with only a version-floor drift checker. That absence is the root cause of every deviation below.

### Deviations

**Python:**

| #   | Deviation                                                                                                                           | Repos                                                                |
| --- | ----------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| P1  | **no Python tooling at all** (no pyproject/ruff/basedpyright/pytest) — 252 `.py` (7 real `scripts/`, 245 vendored `context/codex/`) | `unified-trading-system-ui`                                          |
| P2  | ruff `line-length = 100` (workspace std = 120)                                                                                      | `alerting-service`                                                   |
| P3  | basedpyright not strict — `standard` (pm), no `typeCheckingMode` + no `pyrightconfig.json` (agent-orchestrator)                     | `unified-trading-pm`, `agent-orchestrator`                           |
| P4  | `mypy` config alongside basedpyright (no mypy plugins used → redundant)                                                             | mdps, ml-training-service, UTL                                       |
| P5  | `bandit` config in only 2 repos (inconsistent)                                                                                      | market-tick-data-service, strategy-service                           |
| P6  | build-backend `setuptools` (std = hatchling)                                                                                        | alerting-service                                                     |
| P7  | `[tool.ruff.format]` section absent (falls back to defaults)                                                                        | e2e, ibkr, ml-service, ml-training, sys-int-tests, trading-agent, pm |
| P8  | ruff `target-version` absent                                                                                                        | e2e-testing, system-integration-tests                                |
| P9  | `[tool.ruff.lint.mccabe]` absent                                                                                                    | agent-orchestrator, batch-live-recon, ibkr                           |
| P10 | pytest + coverage config absent                                                                                                     | agent-orchestrator, ibkr-gateway-infra                               |
| P11 | typecheck config **conflict** (not just duplication) — see callout below                                                            | workspace-wide                                                       |

> **basedpyright config reality (P11 — found by reading the configs, not just presence):** the duplication is NOT
> benign. The two files have **diverged** in every repo: `pyrightconfig.json` (which basedpyright actually runs at
> runtime) sets `reportUnknownMemberType/VariableType/ParameterType/ArgumentType = none`, while `[tool.basedpyright]` +
> the CLAUDE.md rule + **QG STEP 5.21** all declare them `= error`. STEP 5.21 lints the _pyproject_ section (strict on
> paper) but basedpyright runs from `pyrightconfig.json` (softer) → the workspace **believes** it's strict while the
> effective type check is softer. AND `pyrightconfig.json` carries `executionEnvironments` + `extraPaths` (e.g.
> `../unified-cloud-interface`, `../unified-internal-contracts`) for **cross-repo import resolution** that
> `[tool.basedpyright]` cannot express — so basedpyright **CANNOT move into TOML**. ⇒ Canonical rule: **ruff / pytest /
> coverage → TOML in pyproject; basedpyright → stays in `pyrightconfig.json` (functional SSOT)**. Remove/sync the
> `[tool.basedpyright]` block, point STEP 5.21 at the JSON, and **operator decides canonical strictness**:
> `reportUnknown* = error` (true strict — likely a large error surface to fix) vs `= none` (codify current reality).

### Frontend toolchain (2 repos: `deployment-ui`, `unified-trading-system-ui`)

| Tool                   | Purpose                  | py-equiv     | deployment-ui               | unified-trading-system-ui   |
| ---------------------- | ------------------------ | ------------ | --------------------------- | --------------------------- |
| Prettier               | format                   | ruff format  | ^3.1.1 (⚠ no `.prettierrc`) | ^3.6.2 (`.prettierrc.json`) |
| ESLint (flat v9)       | lint                     | ruff (lint)  | ^9.0.0                      | ^9.39.4                     |
| TypeScript / `tsc`     | typecheck                | basedpyright | ^5.3.0                      | 5.7.3                       |
| Vitest                 | unit tests               | pytest       | ^4.1.0                      | ^4.1.1                      |
| Playwright             | E2E / smoke              | —            | ^1.58.2                     | ^1.58.2                     |
| build/dev              | bundler/dev server       | —            | **Vite ^8.0.0**             | **Next.js** (+turbo)        |
| TailwindCSS            | styling                  | —            | —                           | ^4.2.0                      |
| husky + lint-staged    | git pre-commit hooks     | pre-commit   | —                           | ^9.1.7 / ^16.4.0            |
| eslint-config-prettier | eslint↔prettier conflict | —            | —                           | ^10.1.1                     |

Config files: `eslint.config.{js,mjs}` + `tsconfig.json` + `vitest.config.ts` + `playwright.config.ts` in both;
`.prettierrc.json` only in `unified-trading-system-ui`. **Frontend deviations:** version drift on every shared tool;
different build systems (Vite vs Next.js); `deployment-ui` under-tooled (no `.prettierrc`, no husky/lint-staged, no
tailwind); **no canonical frontend-config template in PM** (only
`scripts/pre-commit-templates/ui.pre-commit-config.yaml`

- `scripts/workflow-templates-ui/` CI — no shared prettier/eslint/tsconfig/vitest base). `agent-orchestrator` has a Vite
  dashboard but **no `package.json`** → frontend tooling entirely unenrolled. UI rules SSOT: `.claude/rules/ui.md` (tsc
  `--noEmit`, ESLint zero-warnings, Vitest `pool:"forks"` + `CI=true`, Playwright `smoketest`, Prettier `--write`).

### Per-repo current-state matrix — intentional variation vs drift (CHECK-FIRST)

> **Not every difference is drift.** Repo TYPE (library / service / ui / scripts-only) and independently-ratcheted
> thresholds are intentional. The canonical config must enforce per-type **floors** (lib coverage ≥80, service ≥70 per
> the workspace rules) and **preserve above-floor ratchets** — it must NOT flatten everyone to one number. Every
> below-floor / unset repo (⚠) must be confirmed (drift-to-fix vs intentional exemption) before rollout.

| Repo                                                                                                                                      | QG type | coverage `fail_under` | basedpyright | note                                                  |
| ----------------------------------------------------------------------------------------------------------------------------------------- | ------- | --------------------- | ------------ | ----------------------------------------------------- |
| unified-api-contracts                                                                                                                     | library | 84                    | strict       | ✅ lib ≥80                                            |
| unified-trading-library                                                                                                                   | library | 80                    | strict       | ✅ lib ≥80                                            |
| batch-live-reconciliation-service / ml-training-service                                                                                   | service | 80                    | strict       | ratcheted ↑ (keep)                                    |
| alerting-service                                                                                                                          | service | 78                    | strict       | ratcheted ↑                                           |
| instruments-service / market-data-processing-service                                                                                      | service | 77                    | strict       | ratcheted ↑                                           |
| strategy-service                                                                                                                          | service | 74                    | strict       | ratcheted ↑                                           |
| market-tick-data-service                                                                                                                  | service | 71                    | strict       | ratcheted ↑                                           |
| client-reporting-api, deployment-api, deployment-service, execution-service, ml-inference, ml-service, trading-agent, unified-trading-api | service | 70                    | strict       | ✅ at service floor                                   |
| **ibkr-gateway-infra**                                                                                                                    | service | **51**                | strict       | ⚠ below 70 floor — confirm                            |
| **system-integration-tests**                                                                                                              | service | **15**                | strict       | ⚠ test harness — confirm exemption                    |
| **features-service**                                                                                                                      | service | **0**                 | strict       | ⚠ coverage disabled (1097 py) — confirm               |
| **e2e-testing**                                                                                                                           | service | **0**                 | strict       | ⚠ test harness — likely intentional                   |
| **unified-trading-pm**                                                                                                                    | service | (none)                | **standard** | scripts-only — strictness/coverage likely intentional |
| **agent-orchestrator**                                                                                                                    | (none)  | (none)                | **unset**    | newest repo — not enrolled                            |
| **deployment-ui**                                                                                                                         | (none)  | (none)                | strict       | ~0 py (vestigial pyrightconfig)                       |
| **unified-trading-system-ui**                                                                                                             | (none)  | (none)                | **none**     | 252 py ungoverned                                     |

**Intentional (keep):** per-type coverage floors, above-floor ratchets, `pm=standard` (scripts-only). **Drift /
to-confirm:** the ⚠ rows + every P1–P11 deviation.

## Why it matters

Tool-config drift produces (a) the cross-repo "spurious formatting diff" incident (alerting LL=100 vs a 120 format pass
— see linked CME issue context), (b) per-repo quality gates that enforce different rules, (c) under-enrolled new repos
(agent-orchestrator), and (d) 252 ungoverned `.py` in the UI repo. Single source of truth for tool config is missing at
the `pyproject [tool.*]` layer.

## Recommended decision (operator-directed 2026-05-26)

**Decided:**

1. **alerting-service** `line-length` 100 → **120** (P2).
2. **ruff** pinned **`==0.15`** consistently workspace-wide; add `target-version = "py313"` where missing (P8).
3. **basedpyright** strictness levels kept **as-is** (strict standard); `agent-orchestrator` gets strict on enrollment.
   (`unified-trading-pm = standard` retained per operator — scripts-only repo.)
4. **agent-orchestrator** (newest repo — tooling not yet enrolled): enroll **full Python tooling** (ruff incl.
   `ruff.format` + mccabe, pytest, coverage, basedpyright strict + `pyrightconfig.json`) **and UI tooling** (Vite
   dashboard → prettier/eslint/tsc/vitest/playwright).
5. **mypy** removed from the 3 repos — basedpyright (strict) is a superset of the workspace's usage; confirmed **no mypy
   plugins** in any of them, so nothing is lost.
6. **build backend**: no `setuptools` anywhere → fix alerting-service. **DECISION POINT**: target = uv-native `uv_build`
   (per operator "all build backend should be uv") **vs** the current 21-repo de-facto standard `hatchling` — switching
   to `uv_build` is a 21-repo change; aligning alerting to `hatchling` is 1-repo. Operator to confirm target.
7. **`[tool.basedpyright]` vs `pyrightconfig.json`**: pick ONE per repo (basedpyright honors `pyrightconfig.json` when
   present) and apply consistently; remove the redundant one (P11).
8. **unified-trading-system-ui**: add Python tooling for its `scripts/*.py` (ruff + basedpyright), excluding the
   vendored `context/codex/` copies.

**Decision needed:**

- **bandit** (P5): standardize — recommend enabling ruff's `S` (flake8-bandit) ruleset workspace-wide (already available
  in ruff, no extra tool) instead of the standalone `bandit` in 2 repos. Operator to confirm scope.

**Root remediation (unblocks all above):**

- Create a **canonical `pyproject [tool.*]` snippet template** in PM (ruff / basedpyright / pytest / coverage) + a
  rollout script, and extend `check_workspace_pyproject_pin_drift.py` to enforce **sections + values** (not just version
  floors). Add a canonical **frontend** tool-config template set (prettier/eslint/tsconfig/vitest/playwright).

## Phased plan

- **Phase 0 (CHECK-FIRST)** — classify every repo by type (library/service/ui/scripts), record each repo's intentional
  above-floor coverage ratchet + strictness, and confirm the ⚠ below-floor/unset repos (drift vs exemption). THEN write
  canonical **per-type** `[tool.*]` pyproject templates + a frontend template in PM (coverage = per-type **floor**, not
  a fixed value) — the missing SSOT.
- **Phase 1** — quick decided fixes: alerting LL→120 + build-backend, ruff `==0.15` + `target-version`, mypy removal.
- **Phase 2** — agent-orchestrator full enrollment (py + ui).
- **Phase 3** — basedpyright/pyrightconfig dedup + `ruff.format`/mccabe/pytest/coverage section backfill across repos.
- **Phase 4** — UI repo python tooling + frontend version alignment; wire section-level drift enforcement into QG.

## Resolution

**Format decisions LOCKED (operator, 2026-05-26):**

- Python tool config → **TOML in `pyproject.toml`** (ruff / basedpyright / pytest / coverage). **Delete every
  `pyrightconfig.json`** and consolidate basedpyright into `[tool.basedpyright]`, **strict** (`reportUnknown*=error`),
  with cross-repo `extraPaths` via `[[tool.basedpyright.executionEnvironments]]`.
- **mypy removed** (basedpyright superset; no plugins were used).
- **build-backend = hatchling** everywhere (fix the lone `setuptools` repo, alerting-service); no uv_build migration.
- Frontend → tool-mandated dedicated files (eslint/tsconfig/vitest/playwright) + canonical `.prettierrc.json`.
- bandit → **pending** (prefer ruff `S` rules over standalone bandit).

**Phase 0 — canonical SSOT created:** Python = `scripts/pyproject-templates/canonical-tool-sections.toml` + `README.md`
(full `[tool.*]`: ruff + basedpyright-strict + pytest + coverage run+report + bandit). Frontend =
`unified-trading-system-ui/tooling-templates/{.prettierrc.json, tsconfig.base.json, README.md}` (lives in the UI repo —
the SSOT for frontend tooling, not PM; prettier canonical + strict tsconfig base + eslint shared-layer conventions +
devDep version pins; framework base Next-vs-Vite is the documented per-repo split). Coverage `fail_under` = per-type **floor** (lib ≥80 / service ≥70), above-floor ratchets preserved.

**Strictness history (operator asked):** `reportUnknown*=none` is a **7-repo drift, not the standard** — 16/23 repos are
still strict. Relaxed: `unified-trading-pm`, `unified-trading-library`, `deployment-service`, `strategy-service`,
`client-reporting-api` (5 during the March QG setup) + **`execution-service`, `features-service`** (2026-05-15, during
`reportAny` cleanup — the "recent relaxation"). Canonical = **strict**; the 7 are a tracked restore backlog (last 2 =
largest error surface).

**Remaining:** roll the canonical out per repo (Phases 1–4); write the frontend canonical base; restore the 7 relaxed
repos to strict; decide bandit.

## Rollout log (repo-by-repo — LOCAL edits, NOT committed)

**Operating model (operator-clarified 2026-05-26):** scope = **tooling config files only** (`pyproject [tool.*]`, delete
`pyrightconfig.json`, frontend configs, pre-commit). **Do NOT** fix lint/type errors (separate large task). **Do NOT**
reformat or touch the already-formatted `.py` files (operator fixes those later). **Do NOT** run tools
(ruff/basedpyright/QG). **Do NOT** commit (pre-commit hooks would run tools; workspace already has ~224 uncommitted
changes). All edits stay local + uncommitted. Other agents are active — only touch tooling-config files, never their
code/dirty files.

Canonical ruff `select` corrected to the rich union `E F W I N UP B C4 SIM RUF G C90` (the de-facto standard, 6 repos).

**Canonical full tool set (every repo must have ALL of these):** `[tool.ruff]` + `[tool.ruff.format]` +
`[tool.ruff.lint]` (+mccabe +per-file-ignores) · `[tool.basedpyright]` (strict; **no `pyrightconfig.json`**) ·
`[tool.pytest.ini_options]` · `[tool.coverage.run]` **+** `[tool.coverage.report]` · `[tool.bandit]` ·
`.pre-commit-config.yaml` · `[build-system].build-backend = "hatchling.build"`. (ruff `S` rule deferred; bandit stays.)
Minor per-repo config deviations allowed + documented below.

| # | Repo | Status | Tooling changes | Deviations (+ reason) |
| --- | --- | --- | --- | --- |
| 1 | ibkr-gateway-infra | config migrated (local, uncommitted) | `pyproject [tool.*]` → canonical: ruff +exclude/+format/+mccabe/+per-file-ignores, select → rich union (+G +C90); `[tool.basedpyright]` → full explicit strict set, ported `venvPath`/`venv` from JSON; added `[tool.pytest.ini_options]`, `[tool.coverage.run]` (source+branch), `[tool.bandit]` (skips=[]). Deleted `pyrightconfig.json`. build-backend already hatchling. `config.py` + formatted files left untouched. | `fail_under = 51` kept — gateway special-case (QG `MIN_COVERAGE=51`), documented in `pyproject_workspace_audit_2026_05_15`. `repo_arch_tier="infrastructure"` kept. Strict surfaces a pre-existing unresolved `get_ibkr_credentials` (stale `.venv`/UTL drift) → error-backlog, NOT fixed here. |
| 2 | unified-trading-system-ui | reviewed + gaps added (local, uncommitted) | **Frontend configs already canonical** — this repo was the SOURCE the frontend canonical was extracted from (`.prettierrc.json`, `eslint.config.mjs`, `tsconfig.json`, `vitest.config.ts`, `playwright.config.ts`, `.pre-commit-config.yaml`, all 8 devDep pins verified identical to canonical). Gaps added: (a) `package.json` → `smoketest` script = `playwright test --config playwright.static.config.ts` (closes P (no `npm run smoketest` per `.claude/rules/ui.md`); static config runs `static-smoke`/`tier0-app-route-coverage`/`tier0-behavior-audit` specs). (b) **NEW `pyproject.toml`** added for the 7 `scripts/*.py` (P1) — canonical `[tool.ruff]`+format+lint(rich union)+mccabe+per-file-ignores, `[tool.basedpyright]` strict (`include=["scripts"]`), `[tool.pytest.ini_options]`, `[tool.coverage.run]`+`[tool.coverage.report]`, `[tool.bandit]`. | UI repo deviations (documented in the `pyproject.toml` header): no `[build-system]` (config-only, scripts not a buildable package); basedpyright `include=["scripts"]` only; `coverage fail_under = 0` (no Python test suite — frontend coverage gated via vitest/base-ui.sh); vendored `context/` (245 `.py`) excluded from every tool. `tooling-templates/` dir (earlier template artifact) flagged for removal — env blocks `rm`; remove manually. |

### Workspace-wide rollout — COMPLETE 2026-05-26 (local, uncommitted)

**Pre-rollout cleanup:** reverted 108 provably formatting-only `.py` files workspace-wide (test: `ruff format(HEAD) == ruff format(working)` → no false positives; 10 alerting-service files with substantive diffs correctly skipped). Backup at `/tmp/fmt_revert_backup.*`.

**All 24 repos now carry the full canonical `[tool.*]` set** (`ruff` + `format` + `lint`+mccabe+per-file-ignores · `basedpyright` strict + `executionEnvironments` · `pytest` · `coverage.run`+`report` · `bandit`). **Every `pyrightconfig.json` deleted workspace-wide (0 remain).** Done via parallel Sonnet sub-agents, 1 repo each, config-only (no tool runs, no commits).

| Repo | fail_under | pyrightconfig extraPaths ported | Notable deviation (reason) |
| --- | --- | --- | --- |
| ibkr-gateway-infra | 51 (gateway special-case) | exec-env added (1: utl) | venvPath/venv kept |
| unified-trading-library | 80 (lib floor) | 3 | removed `[tool.mypy]` |
| unified-api-contracts | 84 (ratchet kept) | 0 | `reportPrivateUsage="warning"` kept (external consumers import normalize_utils) |
| alerting-service | 78 (kept) | 5 | **setuptools→hatchling** (+`[tool.hatch.build.targets.wheel]`); max-complexity 7→26, line-length 100→120; dropped pytest addopts |
| batch-live-reconciliation-service | 80 (kept) | 5 | — |
| client-reporting-api | 70 | 4 | max-complexity 7 kept (stricter); strict restored (was relaxed-backlog) |
| deployment-api | 70 | 3 | merged `B008` ignore |
| deployment-service | 70 | 4 | max-complexity 55 kept (looser — many complex files w/ per-file C901); strict restored |
| execution-service | 70 | 14 | `stubPath="stubs"` kept; strict restored (largest backlog) |
| features-service | 0→70 (ratcheted up) | 4 | per-family test layout preserved; strict restored |
| instruments-service | 77 (kept) | 5 | E501 kept in ignore |
| market-data-processing-service | 77 (kept) | 6 | ruff `external` noqa list kept; debt-bypass excludes kept |
| market-tick-data-service | 71 (kept) | 0 | bandit skips B608/B104/B108/B310 kept; market_interface excluded |
| ml-inference-service | 70 | 7 | max-complexity 7 kept (stricter) |
| ml-service | 70 | 2 | max-complexity 7→26 |
| ml-training-service | 80 (kept) | 7 | max-complexity 7 kept (stricter) |
| strategy-service | 74 (kept) | 6 | C901 in ignore (Phase-5 deferral) so 26 ceiling is no-op; strict restored |
| trading-agent-service | 70 | 5 | max-complexity 7 kept (stricter); dropped non-canonical pytest python_functions/addopts |
| unified-trading-api | 70 | 0 | `reportCallInDefaultInitializer="none"` kept; max-complexity 10→26 |
| agent-orchestrator | 70 | n/a (no pyrightconfig) | package dir = `server`; Vite `dashboard/` excluded; E501 kept |
| e2e-testing | 0 (scripts-only) | 0 | **no build-system** (config-only); include=`["scripts"]` |
| system-integration-tests | 0 (tests-only) | 6 | **no build-system**; include=`["tests","scripts","system_integration_tests"]` |
| unified-trading-pm | 0 (scripts-only) | 2 | **no build-system**; include=`["scripts"]` |
| unified-trading-system-ui | n/a (added pyproject for `scripts/`) | n/a | **no build-system**; coverage floor 0; vendored `context/` excluded |

**Frontend (2 repos):**
- `unified-trading-system-ui` — already canonical (the reference); added `smoketest` script + scripts-scoped `pyproject.toml`.
- `deployment-ui` (Vite) — added `.prettierrc.json` (verbatim from UI), bumped shared pins (prettier/eslint/eslint-config-prettier/typescript/vitest/@playwright/test), added husky ^9.1.7 + lint-staged ^16.4.0 + `prepare:husky` + lint-staged block + `.husky/pre-commit`, `eslintConfigPrettier` confirmed last, deleted vestigial `pyrightconfig.json` (0 Python files). Vite-specific eslint/tsconfig untouched (intentional framework deviation).
- `user-management-ui` — NOT checked out in this workspace; pending if/when present.

**Convention adopted (max-complexity):** canonical floor is 26; repos with a STRICTER existing ratchet (7) keep it (never loosen); `deployment-service` keeps its looser 55 as a documented carve-out.

**Next (operator runs later — NOT done here):** run each repo's `quality-gates.sh`/`ruff`/`basedpyright` to surface + fix the strict-mode type errors now unmasked (esp. the 7-repo strict-relaxed backlog: execution-service, features-service, strategy-service, deployment-service, client-reporting-api, unified-trading-library, unified-trading-pm). All edits remain local + uncommitted.
