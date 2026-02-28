# Agent Cleanup Workflow - Local Execution

**Location:**
`unified-trading-codex/11-project-management/github-integration/scripts/projects/initial-cleanup/WORKFLOW.md`

**Project:** Initial Cleanup (Project #5)

## Purpose

This document provides instructions for an AI agent to fix codex violations in a single repository, matching the batch
automation workflow but running locally.

## Prerequisites

- Repository must have a quality gates script: `scripts/quality-gates.sh`
- Repository must have a quickmerge script: `scripts/quickmerge.sh`
- Agent has access to GitHub via `gh` CLI
- Agent can run bash scripts

## CRITICAL: Unified Infrastructure Context

**Before making any changes, understand the three-environment quality gates infrastructure:**

### Core Documentation

| Document                       | Purpose                                | Location                                                                                             |
| ------------------------------ | -------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **Quality Gates**              | Core quality gates spec                | `@unified-trading-codex/06-coding-standards/quality-gates.md`                                        |
| **Quality Gates Environments** | Local vs GitHub Actions vs Cloud Build | `@unified-trading-codex/11-project-management/github-integration/docs/QUALITY-GATES-ENVIRONMENTS.md` |
| **Dockerfile Standards**       | unified-trading-services base image    | `@unified-trading-codex/06-coding-standards/dockerfile-standards.md`                                 |
| **Dependency Management**      | unified-trading-services installation  | `@unified-trading-codex/06-coding-standards/dependency-management.md`                                |

### Three-Environment Consistency

**ALL three environments run the SAME command:**

```bash
bash scripts/quality-gates.sh --no-fix
```

**The unified infrastructure ensures:**

#### 1. Local Development

```bash
# Quality gates handles everything automatically:
bash scripts/quality-gates.sh

# It will:
- Create .venv if missing
- Install unified-trading-services from workspace: ../unified-trading-services
- Install dev dependencies: uv pip install -e ".[dev]"
- Run ruff + pytest
- Check codex compliance
```

#### 2. GitHub Actions

```yaml
# .github/workflows/quality-gates.yml
steps:
  - uses: actions/checkout@v4
  - uses: actions/setup-python@v5
    with:
      python-version-file: "pyproject.toml" # Reads requires-python

  - name: Install dependencies
    run: |
      pip install uv  # Bootstrap uv
      # Install unified-trading-services from workspace
      uv pip install --system -e ../unified-trading-services
      uv pip install --system -e ".[dev]"

  - name: Run quality gates
    run: bash scripts/quality-gates.sh --no-fix
```

**Key:** Uses `--system` flag (no venv in CI), installs from local workspace clone.

#### 3. Cloud Build

```dockerfile
# Dockerfile
FROM unified-trading-services:latest  # Base image includes Python 3.13, uv, ripgrep

# unified-trading-services is already in the base image!
# Just install service dependencies:
RUN uv pip install --system -e ".[dev]"
```

```yaml
# cloudbuild.yaml
steps:
  - name: test-in-image
    run: docker run my-service:latest bash scripts/quality-gates.sh --no-fix --quick
```

**Key:** unified-trading-services is baked into the base image, service just installs its own deps.

### unified-trading-services Dependency Pattern

**NEVER add unified-trading-services to pyproject.toml dependencies!**

```toml
# ❌ WRONG - DON'T DO THIS
[project]
dependencies = [
    "unified-trading-services @ git+ssh://...",  # NO!
]

# ✅ CORRECT - Installed separately
[project]
dependencies = [
    "pandas>=2.2.0",
    "numpy>=1.26.0",
    # NOTE: unified-trading-services installed separately
]
```

**Why:** Different installation methods per environment:

- **Local:** `uv pip install -e ../unified-trading-services` (workspace)
- **GitHub Actions:** `uv pip install --system -e deps/unified-trading-services` (cloned)
- **Cloud Build:** Already in `unified-trading-services:latest` base image

### When Updating Quality Gates

**ALWAYS ensure three-way consistency:**

| File                                  | Ruff Version           | Python Version                                       | pytest Flags                 |
| ------------------------------------- | ---------------------- | ---------------------------------------------------- | ---------------------------- |
| `pyproject.toml`                      | `ruff==0.15.0`         | `>=3.13,<3.14`                                       | `pytest-xdist`, `pytest-cov` |
| `.github/workflows/quality-gates.yml` | `ruff==0.15.0`         | `python-version-file: 'pyproject.toml'`              | Same as local                |
| `Dockerfile`                          | (from UCS base)        | `FROM unified-trading-services:latest` (Python 3.13) | Same as local                |
| `scripts/quality-gates.sh`            | Uses installed version | Inherits from venv                                   | `-n auto` for parallel       |

**Verification script:**

```bash
# Check consistency across all repos
cd unified-trading-deployment-v2
./scripts/check-ruff-versions.sh
```

### Key Principles

1. **Single Source of Truth:** `unified-trading-services/scripts/quality-gates.sh` is the template
2. **No Divergence:** All repos use same checks, same ruff version, same Python version
3. **Test What You Deploy:** Cloud Build tests inside the Docker image (test-in-image architecture)
4. **Workspace Installation:** Local and CI install unified-trading-services from workspace, not git URLs
5. **Base Image:** Docker uses `unified-trading-services:latest` base (includes Python 3.13, uv, ripgrep)
6. **No Duplicate Dependencies:** If unified-trading-services has a dependency, don't re-specify it in service
   pyproject.toml
7. **CI Failure = Infrastructure Problem:** If local passes but CI fails, fix the infrastructure mismatch, not the code

### Dependency Deduplication

**CRITICAL:** unified-trading-services already includes common dependencies. Don't duplicate them in service repos.

**unified-trading-services provides:**

- pandas, numpy, pyarrow
- aiohttp, httpx
- google-cloud-storage, google-cloud-bigquery, google-cloud-secret-manager
- boto3 (AWS)
- All testing deps: pytest, pytest-xdist, pytest-asyncio, pytest-cov, pytest-mock
- Linting: ruff
- Other: python-dotenv, pydantic, pyyaml

**In service pyproject.toml:**

```toml
# ❌ WRONG - duplicates unified-trading-services deps
[project]
dependencies = [
    "pandas>=2.2.0",           # Already in unified-trading-services!
    "google-cloud-storage",    # Already in unified-trading-services!
    "pytest>=8.0.0",           # Already in unified-trading-services!
]

# ✅ CORRECT - only service-specific deps
[project]
dependencies = [
    "lightgbm>=4.5.0",         # ML library (service-specific)
    "tardis-client>=2.5.0",    # Market data API (service-specific)
]

[project.optional-dependencies]
dev = [
    # Testing deps already in unified-trading-services, no need to duplicate
    # ruff, pytest, pytest-xdist already there!
]
```

**Why this matters:**

- **Wastes time:** Installing same package twice
- **Wastes memory:** Two copies of same package in image
- **Version conflicts:** Service might specify different version than unified-trading-services
- **Maintenance burden:** Update dependency in two places

**How to check:**

```bash
# See what unified-trading-services provides
cat ../unified-trading-services/pyproject.toml | grep -A 50 "\[project.dependencies\]"

# If your service needs a package, check UCS first
# Only add to service if it's NOT in unified-trading-services
```

### CI Failure After Local Pass = Infrastructure Mismatch

**CRITICAL RULE:** If quality gates pass locally but fail in GitHub Actions, it's NOT a code problem - it's an
**infrastructure mismatch**.

**The fix is NEVER to change the code. The fix is to align the environments.**

#### Common Mismatches

| Symptom                           | Root Cause                                   | Fix                                                                                |
| --------------------------------- | -------------------------------------------- | ---------------------------------------------------------------------------------- |
| CI fails: "ruff not found"        | CI not installing dependencies correctly     | Fix GitHub Actions: add `uv pip install --system -e ".[dev]"`                      |
| CI fails: import error            | unified-trading-services not installed in CI | Fix GitHub Actions: add `uv pip install --system -e deps/unified-trading-services` |
| CI fails: different ruff errors   | Different ruff versions                      | Sync ruff version in pyproject.toml, .pre-commit-config.yaml, GitHub Actions       |
| CI fails: different Python        | Different Python versions                    | GitHub Actions must use `python-version-file: 'pyproject.toml'`                    |
| CI fails: test not found          | Different test exclusions                    | Align pytest flags in quality-gates.sh and GitHub Actions                          |
| CI fails: missing test dependency | pytest-xdist or pytest-cov not installed     | Add to `[project.optional-dependencies] dev` in pyproject.toml                     |

#### Diagnosis Flow

```bash
# 1. Local quality gates pass
bash scripts/quality-gates.sh --no-fix
# ✅ PASS

# 2. Push to GitHub → CI fails
# ❌ FAIL

# 3. STOP! This is an infrastructure problem, not a code problem.
#    Don't try to fix the code. Fix the infrastructure.

# 4. Compare environments:
diff scripts/quality-gates.sh <(gh workflow view quality-gates.yml)

# 5. Check common issues:
echo "=== Checking GitHub Actions workflow ==="

# 5a. Does CI install unified-trading-services?
grep -q "uv pip install.*unified-trading-services" .github/workflows/quality-gates.yml
if [ $? -ne 0 ]; then
    echo "❌ CI not installing unified-trading-services!"
    echo "Fix: Add 'uv pip install --system -e ../unified-trading-services'"
fi

# 5b. Does CI use same Python version?
grep -q "python-version-file: 'pyproject.toml'" .github/workflows/quality-gates.yml
if [ $? -ne 0 ]; then
    echo "❌ CI not reading Python version from pyproject.toml!"
    echo "Fix: Use 'python-version-file: pyproject.toml' instead of hardcoded version"
fi

# 5c. Does CI call quality-gates.sh?
grep -q "bash scripts/quality-gates.sh --no-fix" .github/workflows/quality-gates.yml
if [ $? -ne 0 ]; then
    echo "❌ CI not running quality-gates.sh!"
    echo "Fix: Replace custom pytest commands with 'bash scripts/quality-gates.sh --no-fix'"
fi

# 5d. Does CI have same ruff version?
local_ruff=$(grep "ruff==" pyproject.toml | head -1)
ci_ruff=$(grep "ruff==" .github/workflows/quality-gates.yml | head -1)
if [ "$local_ruff" != "$ci_ruff" ]; then
    echo "❌ CI using different ruff version!"
    echo "Local: $local_ruff"
    echo "CI: $ci_ruff"
    echo "Fix: Sync ruff versions"
fi

# 6. Fix the infrastructure mismatch, NOT the code
# 7. Re-run local quality gates to verify fix
# 8. Push again → CI should now pass
```

#### The Golden Rule

**If local environment is correct (passes quality gates), CI MUST match local.**

- ✅ Fix CI to match local
- ❌ Don't "fix" local to match broken CI
- ❌ Don't change code to work around CI issues
- ❌ Don't add test exclusions to make CI pass
- ❌ Don't downgrade dependencies to make CI pass

**Why:** Local environment is your source of truth. It has the correct dependencies, correct Python version, correct
quality gates script. CI should be a faithful copy of local.

## Key Safety Pattern: Stash Before Pulling

**CRITICAL:** Always stash local changes before pulling or updating files to avoid losing work.

```bash
# Before any git pull or file copy:
git stash push -m "Descriptive message about what's stashed"

# After pull/update:
git stash pop  # Reapplies your changes on top of updates
```

**Why this matters:**

- You may start fixing violations with an outdated quality gates script
- When you pull latest main or update quality gates, your fixes could be lost
- Stashing preserves your work-in-progress changes

**Common scenarios:**

1. **Before pulling main** (Step 2): Stash any exploratory fixes
2. **Before updating quality gates** (Step 4a): Stash partial violation fixes
3. **Before copying files**: Stash to preserve local edits

## Workflow Steps

### Step 1: Pull Issue Details

```bash
# Get issue number and repo from context
REPO_NAME="[REPO_NAME]"  # e.g., "execution-services"
ISSUE_NUMBER="[ISSUE_NUMBER]"  # e.g., "147"

# Fetch issue details
gh issue view $ISSUE_NUMBER --repo "IggyIkenna/$REPO_NAME" --json title,body,labels
```

**Extract from issue:**

- Title (e.g., "[CLEANUP] Fix all COD violations")
- Codex violations to fix (print→logger, os.getenv→config, imports, etc.)
- Success criteria

### Step 2: Ensure Latest Quality Gates

**CRITICAL:** Before fixing violations, ensure quality gates are up-to-date with Check 5 (imports inside functions).

```bash
cd /path/to/$REPO_NAME

# Stash any local changes first (safety)
git stash push -m "Pre-pull stash: partial cleanup work"

# Pull latest main
git checkout main
git pull origin main

# Pop stashed changes back (if any)
git stash pop || echo "No stash to pop"

# Verify quality gates has Check 5
if ! grep -q "Check 5: Imports inside functions" scripts/quality-gates.sh; then
    echo "⚠️  Quality gates outdated - needs Check 5"

    # Option A: Wait for PR to merge (check if PR exists)
    gh pr list --repo "IggyIkenna/$REPO_NAME" --search "Rollout Check 5" --state open

    # Option B: Apply Check 5 locally (if urgent)
    # Copy Check 5 from unified-trading-services/scripts/quality-gates.sh
fi
```

### Step 3: Fix Codex Violations

**Fix each violation type:**

#### 3.1: print() → logger

```bash
# Find all print() in production code (exclude tests/)
rg "print\(" --type py --glob "!tests/**" --glob "!scripts/**" .

# Replace with logger.info()
# Add at top of file if not present:
# import logging
# logger = logging.getLogger(__name__)

# Example fix:
# Before: print(f"Processing {item}")
# After:  logger.info(f"Processing {item}")
```

#### 3.2: os.getenv() → config class

```bash
# Find all os.getenv()
rg "os\.getenv" --type py --glob "!tests/**" --glob "!scripts/**" .

# Replace with config class that extends UnifiedCloudServicesConfig
# See: unified-trading-codex/06-coding-standards/README.md#configuration
```

#### 3.3: datetime.now() → datetime.now(timezone.utc)

```bash
# Find all datetime.now()
rg "datetime\.now\(\)" --type py .

# Replace with:
# from datetime import datetime, timezone
# datetime.now(timezone.utc)
```

#### 3.4: bare except → specific exceptions

```bash
# Find all bare except:
rg "except:" --type py --glob "!tests/**" .

# Replace with specific exceptions or @handle_api_errors decorator
```

#### 3.5: Imports inside functions → top of file

```bash
# Find imports inside functions
rg "^[[:space:]]+import |^[[:space:]]+from .* import" --type py --glob "!tests/**" --glob "!scripts/**" .

# Move all imports to top of file
# For optional dependencies, use try/except at module level:
# try:
#     import optional_dep
#     HAS_OPTIONAL = True
# except ImportError:
#     HAS_OPTIONAL = False
```

#### 3.6: requests → httpx/aiohttp (in async code)

```bash
# Find requests in async functions
rg "requests\." --type py .

# Replace with:
# - aiohttp for async functions
# - httpx for modern sync/async
```

#### 3.7: asyncio.run() in loops

```bash
# Find asyncio.run() in loops
rg "asyncio\.run\(" --type py .

# Replace with asyncio.gather() or run event loop once
```

#### 3.8: time.sleep() in async → asyncio.sleep()

```bash
# Find time.sleep in async functions
rg "time\.sleep\(" --type py .

# Replace with asyncio.sleep() in async functions
```

### Step 4: Run Quality Gates

```bash
cd /path/to/$REPO_NAME

# Run with auto-fix first
bash scripts/quality-gates.sh

# Then verify they pass
bash scripts/quality-gates.sh --no-fix
```

**If quality gates FAIL:**

#### 4a: Check if it's a quality gates script issue

```bash
# Compare quality gates versions
diff scripts/quality-gates.sh ../unified-trading-services/scripts/quality-gates.sh

# If outdated, stash your fixes and update quality gates
git stash push -m "Pre-quality-gates-update: partial fixes"

# Update to latest quality gates
cp ../unified-trading-services/scripts/quality-gates.sh ./scripts/quality-gates.sh

# Commit quality gates update
git add scripts/quality-gates.sh
git commit -m "Update quality gates to match unified-trading-services

- Add Check 5 (imports inside functions)
- Update check numbering (5,6,7,8)
- Improve heuristic checks"

# Pop your fixes back
git stash pop

# Now re-run quality gates with your fixes + updated script
bash scripts/quality-gates.sh --no-fix
```

#### 4b: If tests fail due to missing dependencies

```bash
# Check if pytest-xdist is installed
pip show pytest-xdist

# If missing, add to pyproject.toml:
# [project.optional-dependencies]
# dev = ["pytest-xdist>=3.3.1"]

# Then re-run: uv pip install -e ".[dev]"
```

#### 4c: If genuine code issues remain

**Go back to Step 3** and fix remaining violations shown by quality gates.

### Step 5: Submit PR

```bash
cd /path/to/$REPO_NAME

# Run quickmerge (includes quality gates + creates PR)
bash scripts/quickmerge.sh \
    "Fix all COD violations for issue #$ISSUE_NUMBER

- print() → logger.info() (production code only)
- os.getenv() → config class
- datetime.now() → datetime.now(timezone.utc)
- bare except → specific exceptions
- imports inside functions → top of file
- requests → httpx/aiohttp (async code)
- asyncio.run() in loops → asyncio.gather()
- time.sleep() → asyncio.sleep() (async code)

All quality gates pass.

Closes #$ISSUE_NUMBER" \
    --files "[list of changed files]"
```

**Expected result:**

- ✅ Quality gates pass
- ✅ PR created with auto-merge enabled
- ✅ Branch pushed to GitHub

### Step 6: Verify PR Passes CI

```bash
# Check PR status
PR_NUMBER=$(gh pr list --repo "IggyIkenna/$REPO_NAME" --head "$(git branch --show-current)" --json number --jq '.[0].number')

# Monitor CI status
gh pr view $PR_NUMBER --repo "IggyIkenna/$REPO_NAME"

# Wait for checks to pass
gh pr checks $PR_NUMBER --repo "IggyIkenna/$REPO_NAME" --watch
```

**If CI fails:**

**STOP! If local quality gates passed, this is an infrastructure mismatch, NOT a code problem.**

#### 6a: Diagnose Infrastructure Mismatch (Don't Fix Code!)

```bash
# Pull the CI logs to see what failed
gh run view --repo "IggyIkenna/$REPO_NAME" --log

# Common infrastructure issues:

# 1. unified-trading-services not installed in CI
if grep -q "ModuleNotFoundError.*unified_trading_services" /tmp/ci-log.txt; then
    echo "❌ CI not installing unified-trading-services"
    echo "Fix: Update .github/workflows/quality-gates.yml"
    echo "Add: uv pip install --system -e ../unified-trading-services"
fi

# 2. Different ruff version
if grep -q "ruff.*not found\|ruff.*version" /tmp/ci-log.txt; then
    echo "❌ CI ruff version mismatch"
    echo "Fix: Sync ruff==0.15.0 in pyproject.toml, .pre-commit-config.yaml, GitHub Actions"
fi

# 3. Different Python version
if grep -q "python.*version" /tmp/ci-log.txt; then
    echo "❌ CI Python version mismatch"
    echo "Fix: GitHub Actions should use python-version-file: 'pyproject.toml'"
fi

# 4. pytest dependencies missing
if grep -q "pytest-xdist\|pytest-cov.*not found" /tmp/ci-log.txt; then
    echo "❌ CI missing test dependencies"
    echo "Fix: Ensure pytest-xdist, pytest-cov in [project.optional-dependencies] dev"
fi

# 5. CI not running quality-gates.sh
if grep -q "pytest.*tests/" /tmp/ci-log.txt && ! grep -q "quality-gates.sh" /tmp/ci-log.txt; then
    echo "❌ CI running pytest directly instead of quality-gates.sh"
    echo "Fix: GitHub Actions should call: bash scripts/quality-gates.sh --no-fix"
fi
```

#### 6b: Fix GitHub Actions Workflow (Infrastructure)

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
3. ✅ Call `bash scripts/quality-gates.sh --no-fix` (not custom pytest commands)
4. ✅ Use `--system` flag for uv (no venv in CI)

#### 6c: Commit Infrastructure Fix

```bash
# Stash any code changes (don't lose work)
git stash push -m "Code changes (waiting for infrastructure fix)"

# Fix GitHub Actions workflow
vim .github/workflows/quality-gates.yml
# (Apply fixes from 6b above)

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

# Now push code changes (CI should pass this time)
git add .
git commit -m "Fix codex violations for issue #$ISSUE_NUMBER"
git push
```

#### 6d: The Wrong Approach (Don't Do This!)

```bash
# ❌ WRONG: Changing code to work around CI issues
# - Don't add test exclusions
# - Don't downgrade dependencies
# - Don't skip tests
# - Don't comment out failing checks

# Example of what NOT to do:
git add .
git commit -m "Skip test that fails in CI"  # ❌ WRONG!

# This is treating the symptom, not the cause.
# Fix the infrastructure, not the code.
```

### Step 7: Handle Edge Cases

#### 7a: Quality Gates Script Needs Update

If the quality gates script itself is outdated:

1. **Stash your work-in-progress fixes:**

   ```bash
   git stash push -m "WIP: partial codex violation fixes"
   ```

2. **Copy latest from unified-trading-services:**

   ```bash
   cp ../unified-trading-services/scripts/quality-gates.sh ./scripts/quality-gates.sh
   ```

3. **Verify three-environment consistency:**

   ```bash
   # Check that this repo uses unified infrastructure correctly

   # 1. GitHub Actions should use quality-gates.sh
   grep "bash scripts/quality-gates.sh" .github/workflows/quality-gates.yml || echo "⚠️  GitHub Actions not using quality-gates.sh!"

   # 2. GitHub Actions should install unified-trading-services from workspace
   grep "uv pip install.*unified-trading-services" .github/workflows/quality-gates.yml || echo "⚠️  Not installing unified-trading-services!"

   # 3. Dockerfile should use unified-trading-services base image
   grep "FROM unified-trading-services:latest" Dockerfile || echo "⚠️  Not using UCS base image!"

   # 4. pyproject.toml should NOT have unified-trading-services in dependencies
   ! grep -q "unified-trading-services" pyproject.toml || echo "⚠️  Remove unified-trading-services from pyproject.toml!"
   ```

4. **Update GitHub Actions if needed:**

   ```yaml
   # .github/workflows/quality-gates.yml should match this pattern:

   - name: Install dependencies
     run: |
       pip install uv
       # Install unified-trading-services from workspace (critical!)
       if [ -d "../unified-trading-services" ]; then
         uv pip install --system -e ../unified-trading-services
       fi
       uv pip install --system -e ".[dev]"

   - name: Run quality gates
     run: bash scripts/quality-gates.sh --no-fix
   ```

5. **Update Dockerfile if needed:**

   ```dockerfile
   # Must use unified-trading-services base image
   FROM unified-trading-services:latest

   # unified-trading-services already in base image - just install service deps
   RUN uv pip install --system -e ".[dev]"
   ```

6. **Commit quality gates update:**

   ```bash
   git add scripts/quality-gates.sh .github/workflows/quality-gates.yml Dockerfile
   git commit -m "Update quality gates to match unified-trading-services

   - Add Check 5 (imports inside functions)
   - Update check numbering
   - Improve heuristic checks
   - Ensure three-environment consistency (Local, GitHub Actions, Cloud Build)

   See: unified-trading-codex/06-coding-standards/quality-gates.md"
   git push
   ```

7. **Pop your fixes back:**

   ```bash
   git stash pop
   ```

8. **Then go back to Step 3** to fix violations with updated quality gates

#### 7b: Dependency Updates Needed

If quality gates require new dependencies:

1. **Add to pyproject.toml:**

   ```toml
   [project.optional-dependencies]
   dev = [
       "pytest-xdist>=3.3.1",
       "pytest-asyncio>=0.21.0",
       # ... other deps
   ]
   ```

2. **Update lockfile:**

   ```bash
   uv lock
   ```

3. **Commit both:**
   ```bash
   git add pyproject.toml uv.lock
   git commit -m "Add missing dev dependencies"
   ```

#### 7c: Examples/ Directory Has Violations

Examples directory is often excluded from quality gates. If not:

```bash
# Check if examples/ should be in .gitignore or excluded
# If violations are legitimate example code, exclude in quality gates:
# --glob "!examples/**"
```

## Success Criteria

- ✅ All codex violations fixed (per issue description)
- ✅ Quality gates pass locally
- ✅ PR created with issue number in title/body
- ✅ PR passes GitHub Actions quality gates
- ✅ Auto-merge enabled (PR will merge when checks pass)
- ✅ Issue will be auto-closed when PR merges

## Example: Full Workflow

```bash
# Context
REPO_NAME="execution-services"
ISSUE_NUMBER="147"

# Step 1: Get issue
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/execution-services
gh issue view 147 --repo "IggyIkenna/execution-services"

# Step 2: Ensure latest quality gates
git stash push -m "Pre-pull safety stash"
git pull origin main
git stash pop || echo "No stash to pop"
grep -q "Check 5: Imports" scripts/quality-gates.sh || echo "Need to update quality gates!"

# Step 3: Fix violations (example: print statements)
rg "print\(" --type py --glob "!tests/**" execution_services/
# ... make fixes ...

# Step 4: Run quality gates
bash scripts/quality-gates.sh --no-fix

# If quality gates fail due to outdated script:
if [ $? -ne 0 ]; then
    echo "Quality gates failed - checking if script needs update..."

    # Stash your fixes
    git stash push -m "WIP: partial fixes before quality gates update"

    # Update quality gates
    cp ../unified-trading-services/scripts/quality-gates.sh ./scripts/quality-gates.sh
    git add scripts/quality-gates.sh
    git commit -m "Update quality gates to match unified-trading-services"

    # Pop fixes back
    git stash pop

    # Re-run quality gates
    bash scripts/quality-gates.sh --no-fix
fi

# Step 5: Submit PR
bash scripts/quickmerge.sh \
    "Fix all COD violations for issue #147" \
    --files "execution_services/main.py execution_services/config.py"

# Step 6: Monitor PR
PR_NUM=$(gh pr list --head "$(git branch --show-current)" --json number --jq '.[0].number')
gh pr checks $PR_NUM --watch

# Done! PR will auto-merge when checks pass.
```

## Notes for Agent

- **Be thorough:** Check every violation type from the issue
- **Test incrementally:** Run quality gates after each major change
- **Infrastructure first:** If CI fails but local passed, fix infrastructure (not code)
- **Don't skip tests:** If tests fail, fix them (don't comment out)
- **Don't duplicate deps:** Check if unified-trading-services already has the dependency
- **Quality gates first:** If quality gates script is outdated, fix it before fixing violations
- **Use quickmerge:** Always use quickmerge (never manual git push to main)
- **Auto-merge:** Let PRs auto-merge (don't merge manually unless blocked)
- **CI = Local:** GitHub Actions should be exact copy of local environment

## Related Documentation

### Core Infrastructure (READ FIRST)

- **Quality gates:** `@unified-trading-codex/06-coding-standards/quality-gates.md`
- **Quality gates environments:**
  `@unified-trading-codex/11-project-management/github-integration/docs/QUALITY-GATES-ENVIRONMENTS.md`
- **Dockerfile standards:** `@unified-trading-codex/06-coding-standards/dockerfile-standards.md`
- **Dependency management:** `@unified-trading-codex/06-coding-standards/dependency-management.md`

### Coding Standards

- **Coding standards:** `@unified-trading-codex/06-coding-standards/README.md`
- **Git workflow:** `@unified-trading-codex/.cursor/rules/git-workflow.mdc`
- **UV package manager:** `@unified-trading-codex/.cursor/rules/uv-package-manager.mdc`
- **Python version consistency:** `@unified-trading-codex/.cursor/rules/python-version-consistency.mdc`

### Automation

- **Batch automation:** `@unified-trading-codex/11-project-management/github-integration/scripts/automation/`
- **Enhanced batch fix:**
  `@unified-trading-codex/11-project-management/github-integration/scripts/automation/ENHANCED_BATCH_FIX_README.md`
