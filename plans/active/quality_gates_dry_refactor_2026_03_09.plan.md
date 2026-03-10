---
name: Quality Gates DRY Refactor — Centralized Base Scripts
overview: |
  Every Python repo's scripts/quality-gates.sh is a near-identical ~473–641 line copy.
  Only 3–6 lines differ per repo: SERVICE_NAME, SOURCE_DIR, MIN_COVERAGE, RUN_INTEGRATION,
  PYTEST_WORKERS, LOCAL_DEPS. With ~44 Python repos (27 services + 17 libraries/interfaces
  + codex + PM), ~25,000 lines of identical gate logic exist in parallel across the workspace.
  Any bug fix or new check must be manually propagated to all repos.

  This plan extracts the shared body into 3 base scripts hosted in
  unified-trading-pm/scripts/quality-gates-base/ (PM is already a transitive dependency
  of every repo). Each repo's quality-gates.sh becomes a ~10-line config-and-source stub.

  Repo type mapping (confirmed from audit 2026-03-10):
    - Service  (28 repos, 647L): SERVICE_NAME + SOURCE_DIR + MIN_COVERAGE + LOCAL_DEPS
      Includes: all service/* repos + API repos (client-reporting-api, deployment-api,
      execution-results-api, market-data-api) + ibkr-gateway-infra + trading-agent-service
      + system-integration-tests. No separate base-api variant needed — APIs are FastAPI
      services and use base-service.sh identically.
    - Library  (17 repos, 473L): PACKAGE_NAME + SOURCE_DIR + MIN_COVERAGE + LOCAL_DEPS
    - Codex    (1 repo,  488L):  SOURCE_DIR="" + docs-only variant
    - PM       (1 repo,  641L):  self-hosting — owns the base scripts themselves
    - UIs      (~12 repos, 39–75L): JS/TS stub — already minimal, out of scope.
      No base-ui variant needed.

status: in-progress
created: 2026-03-09
updated: 2026-03-11
isProject: false
todos:
  - id: extract-service-base
    content: >-
      Extract the shared body of scripts/quality-gates.sh (service variant, 623L canonical) into
      unified-trading-pm/scripts/quality-gates-base/base-service.sh. The base script must: (a) NOT define SERVICE_NAME,
      SOURCE_DIR, MIN_COVERAGE, RUN_INTEGRATION, PYTEST_WORKERS, or LOCAL_DEPS — these are set by the caller; (b)
      validate that all required variables are set and non-empty before proceeding (fail with a clear message if
      missing); (c) keep run_timeout, all mode flags (--no-fix, --quick, --lint, --test, --skip-typecheck), all
      size-limit checks, ruff, basedpyright, pytest, pip-audit, bandit sections verbatim; (d) add a version header
      comment "# quality-gates-base-service v1.0 — owned by unified-trading-pm". Test by sourcing from
      features-calendar-service manually before any other migration. Commit to unified-trading-pm.
    status: done

  - id: extract-library-base
    content: >-
      Extract the shared body of scripts/quality-gates.sh (library variant, 473L canonical — use
      unified-events-interface as reference) into unified-trading-pm/scripts/quality-gates-base/base-library.sh.
      Differences from service variant: uses PACKAGE_NAME instead of SERVICE_NAME; no RUN_INTEGRATION flag
      (libraries run unit tests only by default); workspace venv preference in bootstrap; BASEDPYRIGHT_CACHE_DIR
      keyed on PACKAGE_NAME; conditional pip check (only if Dockerfile exists); schema placement check is advisory
      (log_warn not log_fail); UCI-specific os.getenv bypass for unified-config-interface. Validate required vars:
      PACKAGE_NAME, SOURCE_DIR, MIN_COVERAGE. Add version header "# quality-gates-base-library v1.0 — owned by
      unified-trading-pm". Commit to unified-trading-pm.
    status: todo
    notes: >-
      Previously marked done but base-library.sh was subsequently deleted (README said "no callers"). Architecture
      decision reversed 2026-03-11: all 17 library repos will use source stubs (Option A). Must recreate
      base-library.sh before migrate-library-repos can proceed.

  - id: extract-codex-base
    content: >-
      Extract the shared body of unified-trading-codex/scripts/quality-gates.sh (488L, SOURCE_DIR="", docs-only variant)
      into unified-trading-pm/scripts/quality-gates-base/base-codex.sh. The codex base skips all Python checks (no
      basedpyright, no pytest, no ruff source scan) and only runs: link validation, prettier formatting check, markdown
      lint. Validate required var: SERVICE_NAME (documentation repo name). Add version header "#
      quality-gates-base-codex v1.0". Test by sourcing from unified-trading-codex. Commit to unified-trading-pm.
    status: completed
    notes: >-
      base-codex.sh created at unified-trading-pm/scripts/quality-gates-base/base-codex.sh. Runs markdown lint, prettier
      check, link validation (non-blocking), codex structure checks. Skips all Python checks. Tested from
      unified-trading-codex (--quick passes). README.md updated with CODEX stub template. Committed to PM as
      8cec4ef (feat(quality-gates): add base-codex.sh for docs-only repos).

  - id: define-stub-template
    status: done
    content: >-
      Define the canonical thin-wrapper stub template for each repo type. Document in
      unified-trading-pm/scripts/quality-gates-base/README.md. Stubs must follow this shape:

      SERVICE stub (~12 lines):
        #!/usr/bin/env bash
        # Repo-specific settings only. Body: unified-trading-pm/scripts/quality-gates-base/base-service.sh
        SERVICE_NAME="<repo-name>"
        SOURCE_DIR="<package_dir>"
        MIN_COVERAGE=<N>
        RUN_INTEGRATION=false
        PYTEST_WORKERS=${PYTEST_WORKERS:-2}
        LOCAL_DEPS=("dep-a" "dep-b")
        WORKSPACE_ROOT="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
        source "${WORKSPACE_ROOT}/unified-trading-pm/scripts/quality-gates-base/base-service.sh"

      LIBRARY stub (~10 lines):
        #!/usr/bin/env bash
        SOURCE_DIR="<package_dir>"
        MIN_COVERAGE=<N>
        LOCAL_DEPS=()
        WORKSPACE_ROOT="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
        source "${WORKSPACE_ROOT}/unified-trading-pm/scripts/quality-gates-base/base-library.sh"

      CODEX stub (~8 lines):
        #!/usr/bin/env bash
        SERVICE_NAME="unified-trading-codex"
        WORKSPACE_ROOT="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
        source "${WORKSPACE_ROOT}/unified-trading-pm/scripts/quality-gates-base/base-codex.sh"

      Note on path resolution: git rev-parse --show-toplevel returns the invoking repo's root (e.g.
      /workspace/features-calendar-service). Parent dir (..) is the workspace root, where unified-trading-pm is always a
      sibling. This assumption holds for all CI and local runs.
    status: done

  - id: migrate-service-repos
    content: >-
      Migrate all 28 service repos to the thin-wrapper stub. Repos: alerting-service, client-reporting-api,
      deployment-api, deployment-service, execution-results-api, execution-service, features-calendar-service,
      features-commodity-service, features-cross-instrument-service, features-delta-one-service,
      features-multi-timeframe-service, features-onchain-service, features-sports-service, features-volatility-service,
      ibkr-gateway-infra, instruments-service, market-data-api, market-data-processing-service,
      market-tick-data-service, ml-inference-service, ml-training-service, pnl-attribution-service,
      position-balance-monitor-service, risk-and-exposure-service, strategy-service, strategy-validation-service,
      system-integration-tests, trading-agent-service. For each: (a) preserve existing SERVICE_NAME, SOURCE_DIR,
      MIN_COVERAGE, RUN_INTEGRATION, LOCAL_DEPS values exactly; (b) replace body with source stub; (c) run `bash
      scripts/quality-gates.sh --lint --skip-typecheck` to verify stub sources correctly; (d) commit per-repo with
      message "chore(quality-gates): replace body with centralized base-service.sh stub". Run in parallel batches of
      5-6 repos. Note: all 28 repos confirmed present in workspace 2026-03-11 (ibkr-gateway-infra, trading-agent-service,
      system-integration-tests all verified to exist with 647L full-inline quality-gates.sh).
    status: todo
    notes: >-
      Verified 2026-03-11: all 28 service repos have full-inline quality-gates.sh (647L). Migration not yet
      performed. Count corrected from 27→28 (ibkr-gateway-infra, trading-agent-service, system-integration-tests
      all exist in workspace — previous "not found" note was incorrect).

  - id: migrate-library-repos
    content: >-
      Migrate all 17 library/interface repos to the library stub. Repos: execution-algo-library,
      matching-engine-library, unified-api-contracts, unified-cloud-interface, unified-config-interface,
      unified-defi-execution-interface, unified-domain-client, unified-events-interface,
      unified-feature-calculator-library, unified-internal-contracts, unified-market-interface, unified-ml-interface,
      unified-position-interface, unified-reference-data-interface, unified-sports-execution-interface,
      unified-trade-execution-interface, unified-trading-library. For each: preserve SOURCE_DIR and MIN_COVERAGE
      exactly; replace body with library stub; run `bash scripts/quality-gates.sh --quick`; commit with message
      "chore(quality-gates): replace body with centralized base-library.sh stub".
    status: todo
    notes: >-
      Verified 2026-03-11: all 17 library/interface repos have full-inline quality-gates.sh (473L).
      Migration blocked on extract-library-base completing first (base-library.sh must exist).
      Library stub uses PACKAGE_NAME (not SERVICE_NAME) and sources base-library.sh.

  - id: migrate-codex
    content: >-
      Migrate unified-trading-codex/scripts/quality-gates.sh to the codex stub. Preserve any existing markdown-lint or
      link-check commands not already in base-codex.sh. Run `bash scripts/quality-gates.sh` to verify. Commit to
      unified-trading-codex.
    status: completed
    notes: >-
      unified-trading-codex/scripts/quality-gates.sh replaced with 5-line stub sourcing base-codex.sh.
      Verified: bash scripts/quality-gates.sh --quick passes. Committed to unified-trading-codex as
      f2dd3d4 (chore(quality-gates): replace body with centralized base-codex.sh stub).

  - id: migrate-pm-self
    content: >-
      Migrate unified-trading-pm/scripts/quality-gates.sh to source its own base scripts from the canonical location
      (scripts/quality-gates-base/base-service.sh). PM's stub sets SERVICE_NAME="unified-trading-pm",
      SOURCE_DIR="scripts", MIN_COVERAGE=70. This avoids PM being the only repo that still has the full body inline. Run
      `bash scripts/quality-gates.sh --quick`. Commit to unified-trading-pm.
    status: completed
    notes: >-
      unified-trading-pm/scripts/quality-gates.sh replaced with 10-line stub sourcing base-service.sh.
      All gates pass (--quick --skip-typecheck). Typecheck exits 1 due to pre-existing basedpyright error
      in scripts/manifest/check-pyrightconfig-extrapaths.py (not a regression). Committed to PM as
      b08ddfb (chore(quality-gates): replace body with centralized base-service.sh stub).

  - id: add-base-version-check
    content: >-
      Add a version-mismatch guard to each base script. At the top of each base-*.sh, define:
        REQUIRED_BASE_VERSION="1.0"
      Each stub can optionally declare EXPECTED_BASE_VERSION before sourcing. If set and mismatched, the base script
      warns: "⚠️  Stub expects base v$EXPECTED_BASE_VERSION but base is v$REQUIRED_BASE_VERSION". This prevents silent
      regressions when the base evolves. Document the version bump protocol in
      unified-trading-pm/scripts/quality-gates-base/README.md: "Increment REQUIRED_BASE_VERSION on any breaking change
      to base interface variables."
    status: done

  - id: update-codex-standard
    content: >-
      Update unified-trading-codex/06-coding-standards/README.md to document the new quality gates structure: (a) base
      scripts live in unified-trading-pm/scripts/quality-gates-base/; (b) per-repo quality-gates.sh is a config-stub
      only — never a full implementation; (c) to add a new check for all repos, modify the base script in PM (not
      individual repos); (d) new-repo setup instructions now reference the stub template from README.md. Commit to
      unified-trading-codex.
    status: completed
    notes: >-
      Added "Quality Gates Structure (Centralized Base Scripts)" section to README.md covering (a)-(d).
      Updated quality-gates.md: Canonical Template reference updated to base scripts; Repo-Type-Specific
      Templates table updated to base-service/library/codex.sh. Committed to unified-trading-codex as
      8318139 (docs(quality-gates): document centralized base scripts structure).

  - id: update-quickmerge-template
    content: >-
      Update the quickmerge new-service template in unified-trading-pm/cursor-configs/ or deployment-service scaffold to
      generate the stub form (not the full copy) when bootstrapping a new repo. The template should source the
      appropriate base (service/library) based on the repo type selected during scaffolding.
    status: completed
    notes: >-
      No template files found in cursor-configs/ (only workspace config files). Updated the canonical
      new-repo scaffolding docs in unified-trading-codex: new-repo-setup.md Step 5 now generates stub
      form with service/library variants commented; library-setup-checklist.md Phase 5 generates library
      stub. Committed to unified-trading-codex as 6f62de8 (docs(quality-gates): update new-repo setup
      templates to use stub form).
---

# Quality Gates DRY Refactor — Centralized Base Scripts

## Problem Statement

Every Python repo has a copy of `scripts/quality-gates.sh`. The files are 473–641 lines each. Only ~6 lines differ per
repo. With ~44 Python repos, this is ~25,000 lines of parallel maintenance.

Any new gate (e.g. a new lint rule, a new security check, an updated timeout) must be manually applied to all 44+ repos.
Missed repos silently run stale gates.

## Why unified-trading-pm is the Right Host

- PM is already a transitive dependency of every repo in the workspace
- PM owns `scripts/quickmerge.sh` — it's the established home for shared scripts
- All repos are workspace siblings; `$(git rev-parse --show-toplevel)/..` resolves to workspace root from any repo,
  making `../unified-trading-pm/scripts/quality-gates-base/` a stable relative path

## Repo Type Distribution (confirmed 2026-03-09)

| Type                 | Count  | Current Lines | After Refactor | Lines Saved         |
| -------------------- | ------ | ------------- | -------------- | ------------------- |
| Services + APIs      | 28     | 647           | ~12            | ~17,780             |
| Libraries/Interfaces | 17     | 473           | ~10            | ~7,900              |
| Codex (docs-only)    | 1      | 488           | ~8             | ~480                |
| PM (self)            | 1      | 641           | ~10            | ~630                |
| **Total**            | **47** |               |                | **~26,790**         |
| UIs                  | ~12    | 39–75         | unchanged      | 0 (already minimal) |

Note: APIs (client-reporting-api, deployment-api, execution-results-api, market-data-api) are FastAPI services — no
separate base-api variant. UIs have JS/TS toolchain — no base-ui variant.

## Base Script Variants

```
unified-trading-pm/scripts/quality-gates-base/
├── base-service.sh      # Services (FastAPI apps, workers, APIs) — ~620L body
├── base-library.sh      # Libraries and interfaces — ~470L body
├── base-codex.sh        # Docs-only repos (no Python source) — ~480L body
└── README.md            # Stub templates + version bump protocol
```

## Per-Repo Variables (what stubs declare)

### Service repos

| Variable        | Required            | Example                      |
| --------------- | ------------------- | ---------------------------- |
| SERVICE_NAME    | yes                 | "features-calendar-service"  |
| SOURCE_DIR      | yes                 | "features_calendar_service"  |
| MIN_COVERAGE    | yes                 | 70                           |
| RUN_INTEGRATION | no (default: false) | true                         |
| PYTEST_WORKERS  | no (default: 2)     | 4                            |
| LOCAL_DEPS      | no (default: ())    | ("unified-events-interface") |

### Library repos

| Variable     | Required         | Example                    |
| ------------ | ---------------- | -------------------------- |
| SOURCE_DIR   | yes              | "unified_events_interface" |
| MIN_COVERAGE | yes              | 99                         |
| LOCAL_DEPS   | no (default: ()) | ()                         |

## Path Resolution (stable across all CI environments)

```bash
WORKSPACE_ROOT="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
source "${WORKSPACE_ROOT}/unified-trading-pm/scripts/quality-gates-base/base-service.sh"
```

`git rev-parse --show-toplevel` returns the invoking repo root (e.g. `/workspace/features-calendar-service`). Parent
directory is always the workspace root where `unified-trading-pm` is a sibling. Works in local dev and CI (Cloud Build /
AWS CodeBuild) where workspace is checked out flat.

## Sequence

1. Extract base-service.sh → test on 1 repo
2. Extract base-library.sh → test on 1 repo
3. Extract base-codex.sh → test on codex
4. Document stub templates in README.md
5. Migrate all 27 service repos (batches of 5)
6. Migrate all 17 library repos (batches of 5)
7. Migrate codex + PM-self
8. Add version guard to bases
9. Update codex standard + quickmerge template

## Non-Goals

- Do NOT change any gate logic during migration — pure structural refactor
- Do NOT merge the 3 base variants into one (different concerns, different sections)
- Do NOT touch UI repos (39L stubs, JS toolchain, out of scope)
- Do NOT change MIN_COVERAGE values during migration (separate calibration effort)
