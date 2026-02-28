# Agent Cleanup Prompt (Comprehensive Reference)

**Location:**
`unified-trading-codex/11-project-management/github-integration/scripts/projects/initial-cleanup/AGENT_PROMPT.md`

**Project:** Initial Cleanup (Project #5)

## Overview

This document provides comprehensive instructions for fixing codex violations in any service repository. Use this as the
primary reference when working on Initial Cleanup issues.

---

## Infrastructure Context (READ FIRST)

### Quality Gates: Three-Environment Consistency

**CRITICAL:** Quality gates must be identical across all three environments:

| Environment        | Command                                          | unified-trading-services Installation                    |
| ------------------ | ------------------------------------------------ | -------------------------------------------------------- |
| **Local**          | `bash scripts/quality-gates.sh --no-fix`         | `uv pip install -e ../unified-trading-services`          |
| **GitHub Actions** | `bash scripts/quality-gates.sh --no-fix`         | `uv pip install --system -e ../unified-trading-services` |
| **Cloud Build**    | `bash scripts/quality-gates.sh --no-fix --quick` | `FROM unified-trading-services:latest` (in base image)   |

### unified-trading-services Dependency Pattern

**NEVER add unified-trading-services to `pyproject.toml` dependencies!**

```toml
# ❌ WRONG - DON'T DO THIS
[project]
dependencies = [
    "unified-trading-services @ git+ssh://...",  # NO!
]

# ✅ CORRECT - Installed separately per environment
[project]
dependencies = [
    "pandas>=2.2.0",
    "numpy>=1.26.0",
    # NOTE: unified-trading-services installed separately
]
```

**Why:** Different installation methods per environment prevent git authentication issues in Cloud Build and maintain
clean dependency separation.

### Version Consistency Requirements

All three environments must use:

- **Ruff version:** `ruff==0.15.0` (in `pyproject.toml`, `.pre-commit-config.yaml`, GitHub Actions)
- **Python version:** `>=3.13,<3.14` (in `pyproject.toml` → `python-version-file` in GitHub Actions)
- **Test flags:** `pytest -n auto` (parallel testing with pytest-xdist)
- **All 8 codex checks:** Same quality-gates.sh across all environments

### Dependency Deduplication

**unified-trading-services already provides common dependencies. Don't duplicate them!**

**Already in unified-trading-services:**

- pandas, numpy, pyarrow
- aiohttp, httpx
- google-cloud-storage, google-cloud-bigquery, google-cloud-secret-manager
- boto3 (AWS)
- pytest, pytest-xdist, pytest-asyncio, pytest-cov, pytest-mock
- ruff
- python-dotenv, pydantic, pyyaml

**Before adding a dependency to your service:**

```bash
# Check if unified-trading-services already has it
cat ../unified-trading-services/pyproject.toml | grep -A 50 "\[project.dependencies\]"
```

---

## Codex Violations to Fix (8 Checks)

All services must pass these 8 checks:

1. ✅ **print()** → `logger.info()` (production code only, `tests/` excluded)
2. ✅ **os.getenv()** → config class extending `UnifiedCloudServicesConfig`
3. ✅ **datetime.now()** → `datetime.now(timezone.utc)`
4. ✅ **bare except** → specific exceptions or `@handle_api_errors`
5. ✅ **imports inside functions** → move to top of file
6. ✅ **requests** → httpx/aiohttp in async code
7. ✅ **asyncio.run() in loops** → `asyncio.gather()`
8. ✅ **time.sleep() in async** → `asyncio.sleep()`

**Note:** File size violations (>1500 lines) are tracked separately in COD-SIZE issues (Project #6).

---

## Complete Workflow (9 Steps)

### Step 1: Pull Issue Details

```bash
# Navigate to repo
cd /path/to/[REPO_NAME]

# Get issue details
gh issue view [ISSUE_NUMBER] --repo "IggyIkenna/[REPO_NAME]" --json title,body,labels
```

**Extract from issue:**

- Specific violations to fix
- Success criteria
- Any special instructions

### Step 2: Stash Safety + Pull Latest Main

**CRITICAL:** Always stash before pulling to avoid losing work.

```bash
# Stash any local work first
git stash push -m "Pre-pull: partial cleanup work"

# Pull latest
git checkout main
git pull origin main

# Restore stashed work
git stash pop || echo "No stash to pop"
```

### Step 3: Verify Quality Gates Are Current

**Before fixing violations, ensure quality gates script has Check 5 (imports inside functions).**

```bash
# Check for Check 5
if ! grep -q "Check 5: Imports inside functions" scripts/quality-gates.sh; then
    echo "⚠️  Quality gates outdated - updating from unified-trading-services"

    # Stash your work
    git stash push -m "Pre-quality-gates-update: partial fixes"

    # Update quality gates
    cp ../unified-trading-services/scripts/quality-gates.sh ./scripts/quality-gates.sh

    # Commit separately
    bash scripts/quickmerge.sh "Update quality gates to match unified-trading-services" --files "scripts/quality-gates.sh"

    # Wait for PR to merge, then pop your work and continue
    git stash pop
fi
```

### Step 4: Check Manifest for Specific Violations

```bash
# Read the manifest to see exact violations and file paths
cat CODEX_VIOLATIONS_MANIFEST.md
```

If manifest doesn't exist or is outdated:

```bash
cd ../unified-trading-codex/11-project-management/github-integration/scripts/projects/initial-cleanup
python3 06-generate-manifests.py --repos "[REPO_NAME]"
```

### Step 5: Fix All Violations

Systematically fix each violation type using ripgrep to find patterns:

#### 5.1: print() → logger.info()

```bash
# Find all print() in production code (exclude tests/)
rg "print\(" --type py --glob "!tests/**" --glob "!scripts/**" .

# Fix: Add logger at top of file if not present
# import logging
# logger = logging.getLogger(__name__)
#
# Replace: print(f"Processing {item}")
# With: logger.info(f"Processing {item}")
```

#### 5.2: os.getenv() → config class

```bash
# Find all os.getenv()
rg "os\.getenv" --type py --glob "!tests/**" --glob "!scripts/**" .

# Fix: Replace with config class extending UnifiedCloudServicesConfig
# See: @unified-trading-codex/06-coding-standards/README.md#configuration
```

#### 5.3: datetime.now() → datetime.now(timezone.utc)

```bash
# Find all datetime.now()
rg "datetime\.now\(\)" --type py .

# Fix: Add timezone import and use UTC
# from datetime import datetime, timezone
# datetime.now(timezone.utc)
```

#### 5.4: bare except → specific exceptions

```bash
# Find all bare except:
rg "except:" --type py --glob "!tests/**" .

# Fix: Replace with specific exceptions or @handle_api_errors decorator
# from unified_trading_services import handle_api_errors
```

#### 5.5: imports inside functions → top of file

```bash
# Find imports inside functions
rg "^[[:space:]]+import |^[[:space:]]+from .* import" --type py --glob "!tests/**" --glob "!scripts/**" .

# Fix: Move all imports to top of file
# For optional dependencies, use try/except at module level:
# try:
#     import optional_dep
#     HAS_OPTIONAL = True
# except ImportError:
#     HAS_OPTIONAL = False
```

#### 5.6: requests → httpx/aiohttp (in async code)

```bash
# Find requests in async functions
rg "requests\." --type py .

# Fix: Replace with aiohttp for async functions or httpx for modern sync/async
```

#### 5.7: asyncio.run() in loops

```bash
# Find asyncio.run() in loops
rg "asyncio\.run\(" --type py .

# Fix: Replace with asyncio.gather() or run event loop once
```

#### 5.8: time.sleep() in async → asyncio.sleep()

```bash
# Find time.sleep in async functions
rg "time\.sleep\(" --type py .

# Fix: Replace with asyncio.sleep() in async functions
```

### Step 6: Run Quality Gates and Iterate

```bash
# Auto-fix formatting first
bash scripts/quality-gates.sh

# Verify all checks pass
bash scripts/quality-gates.sh --no-fix
```

**If tests fail:**

- ✅ Fix root cause (missing test deps like pytest-xdist, actual bugs)
- ❌ NEVER skip tests, exclude test paths, or add `|| true`
- ❌ NEVER remove functionality just to pass tests

**If quality gates script is outdated:**

1. Stash your fixes: `git stash push -m "WIP: partial fixes"`
2. Update quality gates from unified-trading-services (see Step 3)
3. Commit quality gates update separately
4. Pop fixes back: `git stash pop`
5. Re-run quality gates with updated script

### Step 7: Ensure Test Coverage Is Adequate

**Codex testing standards:**

- **Minimum coverage:** 35% (gate threshold to pass)
- **Target coverage:** 80% (audit readiness)
- **Test structure:** 4-tier (unit/integration/e2e/smoke)
- **Regression tests:** Every bug fix must have `test_regression_{issue}_{description}`
- **Unit test data:** Synthetic fixtures (5-20 rows), NOT real GCS data

```bash
# Check coverage
pytest --cov=. --cov-report=term-missing tests/

# If coverage drops below 35% due to your changes, add tests
```

**Test requirements:**

- Unit tests: Fast (<1s each), isolated, synthetic data
- Integration tests: <120s total
- E2e tests: Single shard, <180s total
- Smoke tests: `--max-results 1` flag

### Step 8: Submit PR with Quickmerge

```bash
# List all files you changed (relative to repo root)
CHANGED_FILES="path/to/file1.py path/to/file2.py path/to/config.py"

bash scripts/quickmerge.sh "Fix all COD violations for issue #[ISSUE_NUMBER]

- print() → logger.info() (production code only)
- os.getenv() → config class
- datetime.now() → datetime.now(timezone.utc)
- bare except → specific exceptions
- imports inside functions → top of file
- requests → httpx/aiohttp (async code)
- asyncio.run() in loops → asyncio.gather()
- time.sleep() → asyncio.sleep() (async code)

All quality gates pass locally.

Closes #[ISSUE_NUMBER]" --files "$CHANGED_FILES"
```

**Expected result:**

- ✅ Quality gates run and pass (Phase 1 + Phase 2)
- ✅ Branch created and pushed
- ✅ PR created with auto-merge enabled
- ✅ Stays on PR branch (doesn't return to main)

### Step 9: Monitor PR and Handle CI Failures

```bash
# Get PR number
PR_NUMBER=$(gh pr list --repo "IggyIkenna/[REPO_NAME]" --head "$(git branch --show-current)" --json number --jq '.[0].number')

# Watch CI status
gh pr checks $PR_NUMBER --repo "IggyIkenna/[REPO_NAME]" --watch
```

**CRITICAL: If local quality gates passed but GitHub Actions fails:**

This is an **infrastructure mismatch**, NOT a code problem!

#### Diagnosis Checklist

```bash
# 1. Does GitHub Actions install unified-trading-services?
grep "unified-trading-services" .github/workflows/quality-gates.yml

# 2. Does GitHub Actions use python-version-file?
grep "python-version-file" .github/workflows/quality-gates.yml

# 3. Does GitHub Actions call quality-gates.sh?
grep "bash scripts/quality-gates.sh" .github/workflows/quality-gates.yml

# 4. Are ruff versions consistent?
grep "ruff==" pyproject.toml .pre-commit-config.yaml .github/workflows/quality-gates.yml

# 5. Pull CI logs to see exact error
gh run view --repo "IggyIkenna/[REPO_NAME]" --log
```

#### Common Infrastructure Mismatches

| Symptom                         | Root Cause                             | Fix                                                          |
| ------------------------------- | -------------------------------------- | ------------------------------------------------------------ |
| CI fails: "ruff not found"      | CI not installing dev deps             | Add `uv pip install --system -e ".[dev]"`                    |
| CI fails: import error          | unified-trading-services not installed | Add `uv pip install --system -e ../unified-trading-services` |
| CI fails: different ruff errors | Different ruff versions                | Sync `ruff==0.15.0` everywhere                               |
| CI fails: different Python      | Different Python versions              | Use `python-version-file: 'pyproject.toml'`                  |
| CI fails: test not found        | Different test exclusions              | Call `bash scripts/quality-gates.sh --no-fix`                |
| CI fails: missing pytest-xdist  | Test dependency not installed          | Add to `[project.optional-dependencies] dev`                 |

#### Fix GitHub Actions Workflow (Infrastructure)

**Don't change the code. Fix the workflow to match local environment.**

```yaml
# .github/workflows/quality-gates.yml
name: Quality Gates

on: [push, pull_request]

jobs:
  quality-gates:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      # CRITICAL: Read Python version from pyproject.toml (same as local)
      - uses: actions/setup-python@v5
        with:
          python-version-file: "pyproject.toml"

      - name: Install dependencies
        run: |
          pip install uv  # Bootstrap uv

          # Install unified-trading-services from workspace (critical!)
          if [ -d "../unified-trading-services" ]; then
            uv pip install --system -e ../unified-trading-services
          fi

          # Install service dependencies
          uv pip install --system -e ".[dev]"

      - name: Run quality gates
        run: bash scripts/quality-gates.sh --no-fix
```

**Key fixes:**

1. ✅ Use `python-version-file: 'pyproject.toml'` (not hardcoded version)
2. ✅ Install unified-trading-services from workspace
3. ✅ Call `bash scripts/quality-gates.sh --no-fix` (not custom pytest)
4. ✅ Use `--system` flag for uv (no venv in CI)

#### Commit Infrastructure Fix Separately

```bash
# Stash any code changes (don't lose work)
git stash push -m "Code changes (waiting for infrastructure fix)"

# Fix GitHub Actions workflow
vim .github/workflows/quality-gates.yml
# (Apply fixes above)

# Commit infrastructure fix
git add .github/workflows/quality-gates.yml
git commit -m "Fix GitHub Actions to match local quality gates environment

- Use python-version-file: 'pyproject.toml'
- Install unified-trading-services from workspace
- Call bash scripts/quality-gates.sh --no-fix
- Use --system flag for uv installs

Fixes CI failure where local passed but GitHub Actions failed.
Root cause: Infrastructure mismatch, not code issue."

# Push infrastructure fix
git push

# Wait for CI to pass with infrastructure fix
gh pr checks --watch

# Pop code changes back
git stash pop

# Push code changes (CI should pass this time)
git add .
git commit --amend --no-edit
git push --force-with-lease
```

#### The Wrong Approach (Don't Do This!)

```bash
# ❌ WRONG: Changing code to work around CI issues
# - Don't add test exclusions
# - Don't downgrade dependencies
# - Don't skip tests
# - Don't comment out failing checks
# - Don't remove functionality to pass tests

# This treats the symptom, not the cause.
# Fix the infrastructure, not the code.
```

---

## Success Criteria

Before closing the issue, verify:

✅ **All violations fixed** (per issue description and manifest) ✅ **Quality gates pass locally:**
`bash scripts/quality-gates.sh --no-fix` ✅ **Test coverage ≥35%** (gate threshold), aim for 80% (audit readiness) ✅
**Tests follow 4-tier structure:** unit/integration/e2e/smoke ✅ **Three-environment consistency maintained:**

- Local and GitHub Actions use same `quality-gates.sh`
- GitHub Actions uses `python-version-file: 'pyproject.toml'`
- GitHub Actions installs unified-trading-services from workspace
- Cloud Build uses `FROM unified-trading-services:latest` ✅ **No duplicate dependencies** (checked
  unified-trading-services first) ✅ **PR created** with issue number in commit message (e.g., "Closes #147") ✅
  **GitHub Actions pass** (same checks as local) ✅ **Cloud Build will pass** (same checks, test-in-image pattern) ✅
  **Auto-merge enabled** (quickmerge does this automatically) ✅ **Issue auto-closes** when PR merges

---

## Key Principles

1. **Fix Root Cause:** Never skip tests, exclude paths, or remove functionality to pass gates
2. **Three-Environment Consistency:** Local, GitHub Actions, and Cloud Build must be identical
3. **Infrastructure Over Code:** If local passes but CI fails, fix infrastructure, not code
4. **Stash Safety:** Always stash before pulling or updating files
5. **Quality Gates First:** Update quality gates script before fixing violations
6. **Test Coverage:** Maintain ≥35% coverage, aim for 80%
7. **Dependency Deduplication:** Check unified-trading-services before adding dependencies
8. **Quickmerge Only:** Never push directly to main (branch protection enforced)
9. **Single Responsibility:** Each PR fixes one issue
10. **No Summary Docs:** Don't create SUMMARY.md or STATUS.md files (per workspace rules)

---

## Documentation References

**Core Standards:**

- Quality Gates: `@unified-trading-codex/06-coding-standards/quality-gates.md`
- Testing: `@unified-trading-codex/06-coding-standards/testing.md`
- Coding Standards: `@unified-trading-codex/06-coding-standards/README.md`
- Dependencies: `@unified-trading-codex/06-coding-standards/dependency-management.md`

**Infrastructure:**

- Three Environments:
  `@unified-trading-codex/11-project-management/github-integration/docs/QUALITY-GATES-ENVIRONMENTS.md`
- Dockerfiles: `@unified-trading-codex/06-coding-standards/dockerfile-standards.md`

**Workflow Details:**

- Complete Workflow: `@WORKFLOW.md` (899 lines, comprehensive reference)
- Project Overview: `@README.md` (project structure and scripts)

**Git Workflow:**

- Quickmerge: `@unified-trading-codex/.cursor/rules/git-workflow.mdc`

---

## Troubleshooting

### Issue: CI fails but local passed

**Root cause:** Infrastructure mismatch  
**Fix:** Update GitHub Actions to match local (see Step 9)

### Issue: Duplicate dependencies

**Root cause:** Service re-specifies dependency already in unified-trading-services  
**Fix:** Remove from service pyproject.toml, unified-trading-services already provides it

### Issue: Quality gates outdated

**Root cause:** Repo missing Check 5 (imports inside functions)  
**Fix:** Copy quality-gates.sh from unified-trading-services, commit separately (see Step 3)

### Issue: Tests fail after fixing violations

**Root cause:** Code changes exposed actual bugs or missing test dependencies  
**Fix:** Fix the bugs or add missing deps (pytest-xdist, pytest-cov), never skip tests

### Issue: Coverage drops below 35%

**Root cause:** Added new code without tests  
**Fix:** Add unit tests for the new/changed code

---

## Short Overlay Prompt Template

**Use this short prompt when invoking an agent. It references this comprehensive document.**

```
Fix all codex violations for issue #[ISSUE_NUMBER] in [REPO_NAME].

Follow the complete workflow in: @unified-trading-codex/11-project-management/github-integration/scripts/projects/initial-cleanup/AGENT_PROMPT.md

Key reminders:
- Run quality gates before submitting: bash scripts/quality-gates.sh --no-fix
- Use quickmerge with --files flag: bash scripts/quickmerge.sh "message" --files "file1 file2"
- If local passes but CI fails: fix infrastructure, not code
- Stash before pulling: git stash push -m "message"
- Maintain test coverage ≥35%

Issue link: https://github.com/IggyIkenna/[REPO_NAME]/issues/[ISSUE_NUMBER]
```

### Example Short Prompts

**For execution-services #147:**

```
Fix all codex violations for issue #147 in execution-services.

Follow: @unified-trading-codex/11-project-management/github-integration/scripts/projects/initial-cleanup/AGENT_PROMPT.md
```

**For instruments-service #58:**

```
Fix all codex violations for issue #58 in instruments-service.

Follow: @unified-trading-codex/11-project-management/github-integration/scripts/projects/initial-cleanup/AGENT_PROMPT.md
```

**For unified-trading-deployment-v2 #126:**

```
Fix all codex violations for issue #126 in unified-trading-deployment-v2.

Follow: @unified-trading-codex/11-project-management/github-integration/scripts/projects/initial-cleanup/AGENT_PROMPT.md
```
