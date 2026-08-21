---
doc_type: plan
title: Strict Quality Gate Alignment
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, ibkr-gateway-infra, system-integration-tests, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-04"
overview:
  Reconcile PM and Codex Quality Gate SSOT, establish repo-type-specific templates, harden the audit prompt to cover all
  cursor rules and quickmerge behavior, and roll out setup.sh, quality-gates.sh, .cursorignore, and .gitignore to every
  repo (no skips; covers frontend, backend, libraries, Python, bash, TypeScript).
todos:
  - {
      id: reconcile-ssot,
      content: "Reconcile PM and Codex SSOT: update Codex quality-gates.md, cursor rules (35%→70%), and templates",
      status: completed,
    }
  - {
      id: repo-type-templates,
      content: "Define repo-type-specific templates: library, service, api, ui, infrastructure, test-harness",
      status: completed,
    }
  - {
      id: harden-audit-prompt,
      content: "Harden audit prompt: add all 106 cursor rules, quickmerge stages, extra quality gates",
      status: completed,
    }
  - {
      id: refactor-propagation,
      content: Refactor propagation scripts to use workspace-manifest.json,
      status: completed,
    }
  - {
      id: rollout-all-repos,
      content:
        "Roll out setup.sh, quality-gates.sh, .cursorignore, .gitignore, QUALITY_GATE_BYPASS_AUDIT.md to every repo",
      status: completed,
    }
  - { id: quickmerge-strict, content: Add quickmerge strict check when quality-gates.sh missing, status: completed }
  - {
      id: manifest-api-canonical,
      content: Add api-canonical doc_standard and ensure quality_gate_status for all repos,
      status: completed,
    }
  - { id: validate-all-repos, content: Validate all 60 repos with quickmerge --unit-only, status: completed }
isProject: false
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Strict Quality Gate Alignment Across All Repos

## Current State Summary

| Source                               | Role                             | Quality Gate Content                                                                         |
| ------------------------------------ | -------------------------------- | -------------------------------------------------------------------------------------------- |
| **PM** `scripts/quality-gates.sh`    | Canonical implementation (~39KB) | Full pipeline: env-setup → lint → import-check → type-check → tests → codex → ci-validators  |
| **Codex** `06-coding-standards/`     | Templates + spec                 | `quality-gates-service-template.sh`, `quality-gates-library-template.sh`, `quality-gates.md` |
| **PM** `cursor-rules/quality-gates/` | 9 rules                          | Limits, hardening, audit factors, production validators                                      |
| **Audit prompt**                     | Evaluation checklist             | Sections 1–18; references templates but not all 106 cursor rules                             |

**Repos:** 60 total — 17 libraries, 18 services, 5 API services, 12 UIs, 4 infrastructure, 1 devops, 1 test-harness, 1
deprecated.

**SSOT conflicts:** `quality-gates.mdc` and `quality-gates-audit-factors.mdc` use 35% coverage; Codex and
`code-quality-limits.mdc` use 70% for services. Codex library template uses 35% for libraries.

---

## Phase 1: Reconcile PM and Codex SSOT

### 1.1 Establish Single Source of Truth

**Codex** as authoritative spec; **PM** as canonical implementation.

**Actions:**

- Update
  [unified-trading-/codex/06-coding-standards/quality-gates.md](unified-trading-/codex/06-coding-standards/quality-gates.md)
  to define:
  - **Coverage by repo type:** `library: 70%`, `service: 70%`, `api-service: 70%`, `infrastructure: 50%` (docs-only:
    N/A)
  - **Size limits:** 900/700/100/500/50 (file, warn, function, class, method)
  - **Pipeline:** env-setup → lint → import-check → type-check → tests → codex → ci-validators
- Update
  [unified-trading-pm/cursor-rules/quality-gates/quality-gates.mdc](unified-trading-pm/cursor-rules/quality-gates/quality-gates.mdc):
  change 35% → 70% (align with Codex)
- Update
  [unified-trading-pm/cursor-rules/quality-gates/quality-gates-audit-factors.mdc](unified-trading-pm/cursor-rules/quality-gates/quality-gates-audit-factors.mdc):
  P2 35% → 70%
- Update
  [unified-trading-pm/cursor-rules/testing/test-coverage-targets.mdc](unified-trading-pm/cursor-rules/testing/test-coverage-targets.mdc):
  35% → 70% (blocking)
- Update Codex library template: `MIN_COVERAGE=35` → `MIN_COVERAGE=70` (or document library exception: 35% for leaf-only
  libraries)

### 1.2 Define Repo-Type-Specific Templates

| Repo Type          | Template                            | Script                  | Coverage   | QUALITY_GATE_BYPASS_AUDIT |
| ------------------ | ----------------------------------- | ----------------------- | ---------- | ------------------------- |
| **library**        | `quality-gates-library-template.sh` | Python                  | 70%        | Required                  |
| **service**        | `quality-gates-service-template.sh` | Python                  | 70%        | Required                  |
| **api-service**    | Same as service                     | Python                  | 70%        | Required                  |
| **ui**             | TypeScript (rollout script)         | tsc, ESLint, Playwright | N/A        | Not required              |
| **infrastructure** | Hybrid (Python vs docs)             | Per repo                | 50% or N/A | Required                  |
| **test-harness**   | Service-like                        | Python                  | 70%        | Required                  |
| **devops**         | PM-like                             | Python                  | 70%        | Required                  |

**Codex:** Add `quality-gates-api-template.sh` (or document that api-service uses service template). Add
`quality-gates-infrastructure-template.sh` for docs-only (codex: markdown lint, no pytest).

---

## Phase 2: Harden Audit Prompt

**File:**
[unified-trading-pm/plans/active/trading-system-audit-prompt.md](unified-trading-pm/plans/active/trading-system-audit-prompt.md)

### 2.1 Cursor Rules Coverage

**Audit prompt must explicitly reference all 106 cursor rules.** Add a section:

- **Section 6.1:** Map each rule category (architecture, ci-cd, config, core, dependencies, etc.) to audit criteria
- **Section 6.2:** BLOCKING rules (strict-quality-gates, no-type-any, runtime-verification, etc.) → mandatory PASS
- **Section 6.3:** Add checklist items for rules not yet covered: e.g. `agents-follow-cursor-rules`, `no-summary-docs`,
  `plan-placement`, `hook-tooling-policy`, `concurrency-max-workers`, etc.

### 2.2 Quality Gate + Quickmerge Coverage

**Add to audit prompt:**

- **Section 8.x:** Quickmerge stages: dependency validation, pre-flight audit, two-phase quality gates, act simulation,
  PR creation
- **Section 8.x:** `--dep-branch` usage when deps differ from main
- **Section 8.x:** `--unit-only`, `--quick`, `--skip-tests`, `--skip-typecheck` usage
- **Section 8.x:** Production-readiness validators (33 validators, 9 categories)
- **Section 8.x:** QUALITY_GATE_BYPASS_AUDIT presence and content per doc_standard

### 2.3 Extra Quality Gates Not in Audit

**Gap analysis:** Audit prompt sections 8–17 cover linting, type safety, security, etc. **Add:**

- basedpyright-safety: `timeout 120 basedpyright <source_dir>/` (never run without source dir)
- safe-linting-execution: timeout for ruff, never on workspace root
- exclude-build-artifacts: build/, dist/, .venv/ excluded from type check
- UCS_DOMAIN_IMPORT quality gate (blocking)
- E501 enforced

---

## Phase 3: Infrastructure Rollout

### 3.1 Propagation Scripts

**Refactor `rollout-quality-gates-python.py`:**

- **Source:** `workspace-manifest.json` instead of hardcoded `ALL_REPOS`
- **Per-repo:** Use `type`, `doc_standard`, `arch_tier`, `quality_gate_status` from manifest
- **Actions:** Add `scripts/quality-gates.sh` (from PM canonical or Codex template), `pyproject.toml` config,
  `QUALITY_GATE_BYPASS_AUDIT.md` stub if required

**Refactor `rollout-quality-gates-typescript.py`:**

- **Source:** `workspace-manifest.json` for UI repos
- **Ensure:** All 12 UI repos + embedded UIs get `scripts/quality-gates.sh` (TypeScript)

**New script:** `rollout-quality-gates-unified.py` (or extend existing) that:

1. Reads `workspace-manifest.json`
2. For each repo: `type` → template selection
3. Copies `scripts/quality-gates.sh` from PM or Codex template
4. Replaces `REPO_MODULE` with package name
5. Creates `QUALITY_GATE_BYPASS_AUDIT.md` stub if `doc_standard` requires it

### 3.1b Mandatory Repo Files (No Skips)

**Every repo must have these four files** — no exceptions by type:

| File                       | SSOT                                | Purpose                                                                                                                               |
| -------------------------- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `scripts/setup.sh`         | unified-trading-pm/scripts/setup.sh | Idempotent env bootstrap; required for cloud agents, background agents. Local dev can skip if VM has deps, but the option must exist. |
| `scripts/quality-gates.sh` | PM or Codex template (per type)     | Lint, type, tests.                                                                                                                    |
| `.cursorignore`            | Repo-type template                  | Excludes build artifacts, .venv, node_modules from Cursor indexing.                                                                   |
| `.gitignore`               | Repo-type template                  | Standard exclusions for Python/Node/Terraform.                                                                                        |

**Why setup.sh everywhere:** Cloud agents and background agents (e.g. running qa-doc-gaps.sh or other utilities) need a
reproducible bootstrap. Local devs with pre-provisioned VM can skip; the file must still exist.

**No skips by repo type:** All deviations must be covered:

| Repo type                  | setup.sh                 | quality-gates.sh    | .cursorignore | .gitignore |
| -------------------------- | ------------------------ | ------------------- | ------------- | ---------- |
| library (Python)           | Python path              | Python template     | Python        | Python     |
| service (Python)           | Python path              | Python template     | Python        | Python     |
| api-service                | Python path              | Python template     | Python        | Python     |
| ui (TypeScript)            | UI path (npm install)    | TypeScript template | Node/TS       | Node/TS    |
| infrastructure (Python)    | Python path              | Per-repo            | Python        | Python     |
| infrastructure (Terraform) | Minimal / uv for scripts | terraform validate  | Terraform     | Terraform  |
| infrastructure (docs-only) | Minimal (ripgrep, etc.)  | Markdown lint       | Docs          | Docs       |
| test-harness               | Python path              | Python template     | Python        | Python     |
| devops                     | Python path              | Python template     | Python        | Python     |

Canonical setup.sh already detects UI vs Python and branches; propagation copies it as-is.

### 3.2 Repo Coverage

**Every repo gets quality gate infrastructure:**

| Repo Type      | Count | Action                                                                                                        |
| -------------- | ----- | ------------------------------------------------------------------------------------------------------------- |
| library        | 17    | Python template; REPO_MODULE; QUALITY_GATE_BYPASS_AUDIT                                                       |
| service        | 18    | Python template; REPO_MODULE; QUALITY_GATE_BYPASS_AUDIT                                                       |
| api-service    | 5     | Same as service                                                                                               |
| ui             | 12    | TypeScript template; no QUALITY_GATE_BYPASS_AUDIT                                                             |
| infrastructure | 4     | deployment-service, unified-trading-codex, ibkr-gateway-infra, unified-trading-deployment-v3 — per-repo logic |
| devops         | 1     | unified-trading-pm — already has canonical                                                                    |
| test-harness   | 1     | system-integration-tests — service-like                                                                       |
| deprecated     | 1     | sports-betting-services-previous — skip or minimal                                                            |

** infra specifics:**

- **deployment-service:** Python service; use service template
- **unified-trading-codex:** Markdown only; docs lint/format; no pytest
- **ibkr-gateway-infra:** Terraform; `terraform validate`, `tflint` (optional); no Python
- **unified-trading-deployment-v3:** Python + UI; hybrid: Python + TypeScript for embedded UI

### 3.3 Repos Not Fully Built

**Use plans and Codex to infer target structure:**

- **strategy-validation-service:** `service`; engine/adapters/cli per TASK_SERVICE_STRUCTURE
- **features-multi-timeframe-service:** `service`; feature layout per multi-tf plan
- **market-data-api, execution-analytics-ui, ml-training-ui:** NO_TESTS — add quality gates anyway; tests can fail
  initially

**Rule:** Quality gate infrastructure exists even if tests fail. `QUALITY_GATE_BYPASS_AUDIT.md` documents temporary
exceptions.

---

## Phase 4: Quickmerge Integration

**File:** [unified-trading-pm/scripts/quickmerge.sh](unified-trading-pm/scripts/quickmerge.sh)

**Current:** Stage 3 runs `bash scripts/quality-gates.sh` if present; else warns and skips.

**Changes:**

- **Strict mode:** If `scripts/quality-gates.sh` is missing, **fail** (exit 1) instead of warn — for repos that should
  have it per manifest
- **Manifest-driven:** Quickmerge reads `workspace-manifest.json`; if repo has `type` in [library, service, api-service,
  infrastructure, devops, test-harness] and `quality_gate_status` != "NO_QG", require quality-gates.sh

**No execution:** This plan builds infrastructure only; does not run quality gates or quickmerge.

---

## Phase 5: Manifest and Doc Standards

### 5.1 Define `api-canonical`

**workspace-manifest.json** references `api-canonical` for deployment-api but it is not defined. Add:

```json
"api-canonical": {
  "required": ["README.md", "docs/ARCHITECTURE.md", "docs/DEPLOYMENT_GUIDE.md", "docs/TESTING.md", "QUALITY_GATE_BYPASS_AUDIT.md"],
  "optional_dir": "specs/"
}
```

### 5.2 Quality Gate Status

**Ensure every repo has `quality_gate_status`** in manifest. Values: `BASELINE_READY`, `PARTIAL`, `NEEDS_WORK`,
`NOT_CONFIGURED`, `NO_TESTS`, `NO_QG`.

- **NO_QG:** Only for repos that explicitly do not need quality gates (e.g. deprecated, archived)
- **UI repos:** Use `NO_QG` for Python; they have TypeScript quality gates only

---

## Phase 6: Rollout Order

1. **PM + Codex:** Reconcile SSOT (Phase 1)
2. **Audit prompt:** Harden (Phase 2)
3. **Propagation scripts:** Refactor to use manifest (Phase 3.1)
4. **Repos:** Roll out in tier order: T0 libraries → T1 → T2 → T3 → services → APIs → UIs → infrastructure
5. **Quickmerge:** Add strict check (Phase 4)
6. **Manifest:** Add api-canonical, ensure quality_gate_status (Phase 5)

---

## Deliverables

| Deliverable                            | Location                                                                                |
| -------------------------------------- | --------------------------------------------------------------------------------------- |
| Reconciled Codex quality-gates.md      | unified-trading-/codex/06-coding-standards/quality-gates.md                             |
| Updated cursor rules (coverage 70%)    | unified-trading-pm/cursor-rules/quality-gates/_.mdc, testing/_.mdc                      |
| Hardened audit prompt                  | unified-trading-pm/plans/active/trading-system-audit-prompt.md                          |
| Refactored propagation script          | unified-trading-pm/scripts/propagation/rollout-quality-gates-unified.py (or equivalent) |
| scripts/setup.sh in every repo         | Per-repo scripts/ (SSOT: unified-trading-pm/scripts/setup.sh)                           |
| scripts/quality-gates.sh in every repo | Per-repo scripts/                                                                       |
| .cursorignore in every repo            | Per-repo root (repo-type template)                                                      |
| .gitignore in every repo               | Per-repo root (repo-type template)                                                      |
| QUALITY_GATE_BYPASS_AUDIT.md stubs     | Per-repo (where required)                                                               |
| api-canonical doc_standard             | workspace-manifest.json                                                                 |
| Quickmerge strict check                | unified-trading-pm/scripts/quickmerge.sh                                                |

---

## Success Criteria and Validation

- **Success:** All 60 repos pass `quickmerge --unit-only` (lint + type + unit tests)
- **Skip act:** `--quick` or `--unit-only` already skips act
- **Linter strict:** Errors only, not warnings — `ruff check` should fail on errors
- **CI may fail:** Integration tests may fail — that's OK for now
- **Minimal validation:** basedpyright (with `run_timeout 120`) + unit tests
- **basedpyright:** MUST use `run_timeout` (or `timeout`/`gtimeout`) — never raw
- **Cross-platform:** Use `run_timeout` helper (checks `timeout` vs `gtimeout`) — works on Mac + Linux

---

## Out of Scope (Per User)

- **No execution:** Do not run quality gates or quickmerge
- **Infrastructure only:** Build the files and config; no validation runs
