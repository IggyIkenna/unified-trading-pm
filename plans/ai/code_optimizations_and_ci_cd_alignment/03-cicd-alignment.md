# 03: CI/CD Alignment (Local → GitHub Actions → Cloud Build)

**Status**: ⬜ Not Started
**Priority**: P1 (Prevents "works locally, fails in CI")
**Estimated Time**: 2-3 hours
**Expected Benefit**: 30-60 min/day saved, fewer CI failures

---

## 📖 Overview

Ensure identical behavior across all three stages: Local development, GitHub Actions, and Cloud Build. Prevents the frustrating "works on my machine" problem.

### Current State
- Local quality gates pass
- GitHub Actions fails with dependency/version issues
- Cloud Build fails with different errors
- Must debug each stage separately

### Target State
- Identical environment across all three stages
- Same ruff version (0.15.0)
- Same Python version (3.13)
- Same dependencies
- Same test commands
- Failures reproducible locally

---

## 🔗 Dependencies

- **Requires**: Claude Code integration (#01) for cost-effective testing
- **Blocks**: Multi-repo versioning (#06) needs reliable CI

---

## 🚧 Blockers

- [ ] Need to identify current version mismatches
- [ ] Need Docker setup for local Cloud Build simulation
- [ ] Need `act` tool for local GitHub Actions

---

## GCP project ID in workflows (standard)

**Rule:** Do not hardcode GCP project IDs in workflow files. Use a **repository variable** (not a secret), so different environments and forks can use different projects.

### Standard pattern

1. **In workflow YAML** use the repo variable:
   ```yaml
   env:
     GCP_PROJECT_ID: ${{ vars.GCP_PROJECT_ID }}
     # When building image URLs:
     UCS_IMAGE: asia-northeast1-docker.pkg.dev/${{ vars.GCP_PROJECT_ID }}/unified-trading-services/unified-trading-services:latest
   ```

2. **Set the variable** (one-time per repo) via GitHub CLI from the repo directory:
   ```bash
   cd <repo>
   gh variable set GCP_PROJECT_ID --body "your-gcp-project-id"
   ```
   Or in GitHub: **Settings → Secrets and variables → Actions → Variables → New repository variable**.

3. **Repos that need `GCP_PROJECT_ID`** (workflows that pull from Artifact Registry or deploy to GCP):
   - ml-inference-service, ml-training-service (quality-gates: UCS image)
   - features-delta-one-service, features-volatility-service, features-onchain-service (batch/target workflows)
   - unified-trading-deployment-v3 (deploy-dashboard, deploy-dashboard-gce-vm)
   - execution-services (deploy-cloud-run: default when input not provided)

4. **Bulk set variable** in all repos (from workspace root, with `gh` authenticated):
   ```bash
   for repo in ml-inference-service ml-training-service features-delta-one-service features-volatility-service features-onchain-service unified-trading-deployment-v3 execution-services; do
     (cd "$repo" && gh variable set GCP_PROJECT_ID --body "your-gcp-project-id" && echo "Set in $repo")
   done
   ```

**Why variable not secret:** Project ID is not sensitive (it’s an identifier, not a credential). Use **Variables** for non-secret config; use **Secrets** for keys and tokens.

**Related:** `.cursor/rules/no-hardcoded-project-ids.mdc` — no hardcoded project IDs in code or config.

---

## 🔍 Current State Analysis

### Step 1: Check Version Alignment

```bash
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/instruments-service

# Check local versions
echo "=== LOCAL ==="
python --version
ruff --version
pytest --version

# Check GitHub Actions
echo "=== GITHUB ACTIONS ==="
grep "python-version:" .github/workflows/quality-gates.yml
grep "ruff==" .github/workflows/quality-gates.yml
grep "pytest" .github/workflows/quality-gates.yml

# Check Cloud Build
echo "=== CLOUD BUILD ==="
grep "FROM python:" cloudbuild.yaml
grep "ruff" cloudbuild.yaml
grep "pytest" cloudbuild.yaml
```

### Step 2: Verify Ruff Consistency

Per workspace rules, all three stages must use `ruff==0.15.0`:

```bash
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/unified-trading-deployment-v3

# Run consistency checker
./scripts/check-ruff-versions.sh

# Should show:
# ✅ pyproject.toml: ruff==0.15.0
# ✅ .pre-commit-config.yaml: v0.15.0
# ✅ GitHub Actions: ruff==0.15.0
# ✅ Cloud Build: ruff==0.15.0
```

---

## 🛠️ Implementation

### Part 1: Install Local CI Tools

#### Install `act` (Run GitHub Actions Locally)

```bash
# Install act
brew install act

# Verify installation
act --version

# Test in a service
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/instruments-service

# List available workflows
act -l

# Run quality gates workflow locally (dry-run)
act -n -j quality-gates

# Run quality gates workflow locally (actual run)
act -j quality-gates
```

**Benefits**:
- ✅ Test GitHub Actions before pushing
- ✅ Catch dependency issues locally
- ✅ Faster iteration (no push required)

#### Install Docker (For Cloud Build Simulation)

```bash
# Check if Docker installed
docker --version

# If not installed:
# Download from https://www.docker.com/products/docker-desktop

# Verify Docker running
docker ps
```

### Part 2: Create Unified Docker Image

Create a base image used by all three stages:

```dockerfile
# unified-trading-deployment-v3/docker/quality-gates.Dockerfile
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (package manager)
RUN pip install --no-cache-dir uv==0.5.0

# Install quality gate tools (exact versions)
RUN uv pip install --system \
    ruff==0.15.0 \
    pytest==9.0.1 \
    pytest-cov==7.0.0 \
    pytest-asyncio==0.25.0 \
    basedpyright==1.21.0

# Set working directory
WORKDIR /workspace

# Default command
CMD ["bash"]
```

Build and push:

```bash
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/unified-trading-deployment-v3

# Build image
docker build -t quality-gates:latest -f docker/quality-gates.Dockerfile .

# Test image
docker run --rm quality-gates:latest python --version
docker run --rm quality-gates:latest ruff --version

# Push to Artifact Registry (for Cloud Build)
# Use your GCP project ID (set GCP_PROJECT_ID repo variable in workflows)
docker tag quality-gates:latest asia-northeast1-docker.pkg.dev/YOUR_PROJECT_ID/quality-gates:latest
docker push asia-northeast1-docker.pkg.dev/YOUR_PROJECT_ID/quality-gates:latest
```

### Part 3: Update Local Quality Gates

```bash
# instruments-service/scripts/quality-gates.sh
# Add Docker option

if [ "$USE_DOCKER" = "true" ]; then
    echo "Running quality gates in Docker (matches CI)..."
    docker run --rm \
        -v $(pwd):/workspace \
        -w /workspace \
        quality-gates:latest \
        bash scripts/quality-gates.sh --no-docker
    exit $?
fi

# Rest of script unchanged...
```

Usage:

```bash
# Run locally (native)
bash scripts/quality-gates.sh

# Run in Docker (matches CI)
USE_DOCKER=true bash scripts/quality-gates.sh
```

### Part 4: Update GitHub Actions

```yaml
# .github/workflows/quality-gates.yml
name: Quality Gates

on: [push, pull_request]

jobs:
  quality-gates:
    runs-on: ubuntu-latest

    # Use same Docker image as local and Cloud Build (GCP_PROJECT_ID = repo variable)
    container:
      image: asia-northeast1-docker.pkg.dev/${{ vars.GCP_PROJECT_ID }}/quality-gates:latest
      credentials:
        username: _json_key
        password: ${{ secrets.GCP_SA_KEY }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Checkout dependencies
        env:
          GH_PAT: ${{ secrets.GH_PAT }}
        run: |
          # Clone path deps (per .cursor/rules/path-dependency-ci.mdc)
          git clone https://x-access-token:${GH_PAT}@github.com/IggyIkenna/unified-trading-services.git ../unified-trading-services
          git clone https://x-access-token:${GH_PAT}@github.com/IggyIkenna/unified-config-interface.git ../unified-config-interface
          git clone https://x-access-token:${GH_PAT}@github.com/IggyIkenna/unified-events-interface.git ../unified-events-interface

      - name: Install dependencies
        run: |
          # Install in DAG order
          uv pip install --system -e ../unified-trading-services
          uv pip install --system -e ../unified-config-interface
          uv pip install --system -e ../unified-events-interface
          uv pip install --system -e ".[dev]"

      - name: Run quality gates
        run: bash scripts/quality-gates.sh --no-fix --quick
```

### Part 5: Update Cloud Build

```yaml
# cloudbuild.yaml
steps:
  # Use same Docker image as local and GitHub Actions (substitute PROJECT_ID in Cloud Build substitution)
  - name: 'asia-northeast1-docker.pkg.dev/$PROJECT_ID/quality-gates:latest'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        # Clone dependencies
        git clone https://github.com/IggyIkenna/unified-trading-services.git ../unified-trading-services
        git clone https://github.com/IggyIkenna/unified-config-interface.git ../unified-config-interface
        git clone https://github.com/IggyIkenna/unified-events-interface.git ../unified-events-interface

        # Install dependencies
        uv pip install --system -e ../unified-trading-services
        uv pip install --system -e ../unified-config-interface
        uv pip install --system -e ../unified-events-interface
        uv pip install --system -e ".[dev]"

        # Run quality gates
        bash scripts/quality-gates.sh --no-fix --quick
```

### Part 6: Install Pre-Push Git Hooks

Install pre-push hook in all 32 repos to run `act` before pushing:

```bash
# unified-trading-deployment-v3/scripts/install-pre-push-hooks.sh
#!/bin/bash

set -e

REPOS=(
  "instruments-service"
  "strategy-service"
  "position-balance-monitor-service"
  "risk-and-exposure-service"
  "execution-services"
  "execution-algo-library"
  "market-data-processing-service"
  "market-tick-data-handler"
  "ml-inference-service"
  "ml-training-service"
  "features-calendar-service"
  "features-delta-one-service"
  "features-onchain-service"
  "features-volatility-service"
  "pnl-attribution-service"
  "alerting-system"
  "unified-trading-services"
  "unified-config-interface"
  "unified-domain-client"
  "unified-events-interface"
  "unified-market-interface"
  "unified-ml-interface"
  "unified-trade-execution-interface"
  "backtest-ui"
  "trading-analytics-ui"
  "live-health-monitor-ui"
  "logs-dashboard-ui"
  "batch-audit-ui"
  "client-reporting-ui"
  "ml-deployment-ui"
  "onboarding-ui"
  "settlement-ui"
)

WORKSPACE_ROOT="/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos"

for repo in "${REPOS[@]}"; do
  echo "Installing pre-push hook in $repo..."

  HOOK_PATH="$WORKSPACE_ROOT/$repo/.git/hooks/pre-push"

  cat > "$HOOK_PATH" << 'EOF'
#!/bin/bash

echo "🔍 Running GitHub Actions locally with act..."

# Run quality-gates workflow locally
act -j quality-gates --secret-file ~/.secrets

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Local GitHub Actions simulation failed"
    echo "Fix issues before pushing, or use 'git push --no-verify' to skip"
    exit 1
fi

echo "✅ Local simulation passed, proceeding with push"
exit 0
EOF

  chmod +x "$HOOK_PATH"
  echo "✅ Installed: $HOOK_PATH"
done

echo ""
echo "✅ Pre-push hooks installed in all 32 repos"
echo "ℹ️  To skip hook: git push --no-verify"
```

Run installation:

```bash
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/unified-trading-deployment-v3

# Make script executable
chmod +x scripts/install-pre-push-hooks.sh

# Install hooks in all repos
./scripts/install-pre-push-hooks.sh
```

**Benefits**:
- ✅ Catches CI failures in 30-60 seconds locally (vs 3-5 min on GitHub)
- ✅ Prevents failed CI runs (saves GitHub Actions minutes)
- ✅ Faster feedback loop
- ✅ Can skip with `git push --no-verify` for urgent pushes

**Configure secrets** (one-time setup):

```bash
# Store GH_PAT for act to use
echo "GH_PAT=$GH_PAT" > ~/.secrets

# Verify
cat ~/.secrets
```

### Part 7: Create Verification Script

```bash
# unified-trading-deployment-v3/scripts/verify-ci-alignment.sh
#!/bin/bash

set -e

echo "=== Verifying CI/CD Alignment ==="

ERRORS=0

# Check Python version
echo "Checking Python version..."
LOCAL_PYTHON=$(python --version | cut -d' ' -f2)
GH_PYTHON=$(grep "python-version:" .github/workflows/quality-gates.yml | cut -d"'" -f2)
CB_PYTHON=$(grep "FROM python:" cloudbuild.yaml | cut -d':' -f2 | cut -d'-' -f1)

if [ "$LOCAL_PYTHON" != "$GH_PYTHON" ] || [ "$LOCAL_PYTHON" != "$CB_PYTHON" ]; then
    echo "❌ Python version mismatch:"
    echo "  Local: $LOCAL_PYTHON"
    echo "  GitHub Actions: $GH_PYTHON"
    echo "  Cloud Build: $CB_PYTHON"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ Python version aligned: $LOCAL_PYTHON"
fi

# Check ruff version
echo "Checking ruff version..."
LOCAL_RUFF=$(ruff --version | cut -d' ' -f2)
GH_RUFF=$(grep "ruff==" .github/workflows/quality-gates.yml | cut -d'=' -f3)
CB_RUFF=$(grep "ruff==" cloudbuild.yaml | cut -d'=' -f3)

if [ "$LOCAL_RUFF" != "$GH_RUFF" ] || [ "$LOCAL_RUFF" != "$CB_RUFF" ]; then
    echo "❌ Ruff version mismatch:"
    echo "  Local: $LOCAL_RUFF"
    echo "  GitHub Actions: $GH_RUFF"
    echo "  Cloud Build: $CB_RUFF"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ Ruff version aligned: $LOCAL_RUFF"
fi

# Check pytest version
echo "Checking pytest version..."
LOCAL_PYTEST=$(pytest --version | cut -d' ' -f2)
GH_PYTEST=$(grep "pytest" .github/workflows/quality-gates.yml | grep -oP 'pytest==\K[0-9.]+')
CB_PYTEST=$(grep "pytest" cloudbuild.yaml | grep -oP 'pytest==\K[0-9.]+')

if [ "$LOCAL_PYTEST" != "$GH_PYTEST" ] || [ "$LOCAL_PYTEST" != "$CB_PYTEST" ]; then
    echo "❌ Pytest version mismatch:"
    echo "  Local: $LOCAL_PYTEST"
    echo "  GitHub Actions: $GH_PYTEST"
    echo "  Cloud Build: $CB_PYTEST"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ Pytest version aligned: $LOCAL_PYTEST"
fi

if [ $ERRORS -eq 0 ]; then
    echo ""
    echo "✅ All stages aligned!"
    exit 0
else
    echo ""
    echo "❌ Found $ERRORS misalignment(s)"
    exit 1
fi
```

Make executable:

```bash
chmod +x unified-trading-deployment-v3/scripts/verify-ci-alignment.sh
```

---

## ✅ Verification

### Test 1: Local Quality Gates

```bash
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/instruments-service

# Run natively
bash scripts/quality-gates.sh --no-fix

# Run in Docker (should produce identical results)
USE_DOCKER=true bash scripts/quality-gates.sh --no-fix
```

**Expected**: Both pass or both fail with same errors.

### Test 2: Local GitHub Actions

```bash
# Run GitHub Actions locally with act
act -j quality-gates --secret-file ~/.secrets

# Should produce same results as actual GitHub Actions
```

### Test 3: Pre-Push Hook

```bash
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/instruments-service

# Make a small change
echo "# test" >> README.md

# Stage and commit
git add README.md
git commit -m "test: verify pre-push hook"

# Try to push (hook will run act automatically)
git push

# Expected: Hook runs act, then pushes if successful
```

### Test 4: Version Alignment

```bash
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/unified-trading-deployment-v3

# Run verification script
./scripts/verify-ci-alignment.sh

# Should show all ✅ (no mismatches)
```

### Test 5: End-to-End

1. Make a small code change
2. Run local quality gates (native)
3. Run local quality gates (Docker)
4. Stage and commit changes
5. Push to GitHub (pre-push hook runs act automatically)
6. Verify GitHub Actions passes
7. Verify Cloud Build passes

**Expected**: All stages pass (or all fail with same error).

---

## 📊 Success Metrics

- [ ] All three stages use same Python version (3.13)
- [ ] All three stages use same ruff version (0.15.0)
- [ ] All three stages use same pytest version
- [ ] Local Docker run matches GitHub Actions
- [ ] GitHub Actions matches Cloud Build
- [ ] Verification script passes
- [ ] Pre-push hooks installed in all 32 repos
- [ ] `~/.secrets` configured with GH_PAT
- [ ] Zero "works locally, fails in CI" issues

---

## 🔄 Rollback Plan

If Docker-based approach causes issues:

1. Keep existing local/GitHub/Cloud Build configs
2. Use verification script to manually check alignment
3. Fix version mismatches one by one
4. Continue with native execution (not Docker)

---

## 📚 Related Documentation

- Workspace rules: `.cursorrules` → "Quality Gates: Three-Stage Consistency"
- Quality gates guide: `unified-trading-codex/06-coding-standards/quality-gates.md`
- Path dependency CI: `.cursor/rules/path-dependency-ci.mdc`
- Ruff version consistency: `unified-trading-deployment-v3/scripts/check-ruff-versions.sh`

---

## 💡 Tips

1. **Use Docker for critical changes**: When in doubt, test in Docker before pushing
2. **Run verification script regularly**: Add to pre-commit hooks
3. **Keep base image updated**: Rebuild when tool versions change
4. **Cache Docker layers**: Faster local builds
5. **Document version changes**: Update all three stages simultaneously

---

## ✏️ Notes

- Docker-based approach ensures 100% consistency
- `act` tool catches GitHub Actions issues before push
- Verification script prevents drift over time
- Expected to save 30-60 min/day debugging CI failures

---

## 📋 Complete Implementation Plan (Unified Quickmerge Approach)

This plan implements **unified quickmerge** - all checks in one optimal pipeline.

**Key Change**: Quickmerge runs **everything** (dependency validation, pre-flight audit, local quality gates, act simulation, watch mode). Agents **always** use quickmerge, never standalone quality gates.

**Template**: See `UNIFIED-QUICKMERGE-TEMPLATE.sh` for complete implementation

### Architecture Summary (Unified Quickmerge)

```
SINGLE COMMAND - DOES EVERYTHING:
  bash scripts/quickmerge.sh "fix: update"

PIPELINE (Optimal Ordering):

Stage 1: Dependency Validation (10s - FAST, BLOCKING)
  └─> Check uncommitted changes in path deps
      ❌ FAIL FAST if deps dirty

Stage 2: Pre-Flight Audit (15s - FAST, AUTO-FIX)
  ├─> Codex compliance (E722, large files, etc.)
  ├─> Cursor rules audit
  └─> 🔧 Auto-fix violations via LLM agent

Stage 3: Local Quality Gates - Docker (30s - FAST)
  ├─> Ruff format + check
  ├─> Basedpyright
  └─> Pytest (quick mode)

Stage 4: Create PR Branch & Commit (5s)
  └─> Stash, branch, stage, commit

Stage 5: Act - Full GitHub Simulation (1-2min - SLOW, ACCURATE)
  └─> Simulates exact GitHub Actions environment

Stage 6: Watch Mode - Auto-Fix (1-3min if needed)
  ├─> If act fails: capture errors
  ├─> Call LLM agent to fix (Cursor/Claude/Aider)
  ├─> Re-run act (max 3 attempts)
  └─> Push when passes

Stage 7: Push & Create PR (5s)
  └─> git push + gh pr create --auto-merge

TOTAL TIME: ~2-5 minutes (all checks, auto-fix if needed)

AGENT RULE: ALWAYS use quickmerge, NEVER standalone quality gates
```

### Phase 1: Core Infrastructure (2-3 hours with 4 parallel agents)

#### Agent 1: Docker & Act Setup
- [ ] Create unified Docker image (`quality-gates:latest`)
- [ ] Push to Artifact Registry
- [ ] Install `act` tool
- [ ] Configure `~/.secrets` with `GH_PAT`
- [ ] Create `.actrc` template

#### Agent 2: Pre-Push Hooks & Watcher
- [ ] Create `install-pre-push-hooks.sh` script for 32 repos
- [ ] Create `pre-push-watcher.sh` (monitors act, triggers auto-fix)
- [ ] Create `llm-agent-wrapper.sh` (LLM-agnostic wrapper)
- [ ] Test pre-push hook + watcher in 2-3 repos

#### Agent 3: Pre-Flight Audit Scripts
- [ ] Create `pre-flight-audit.sh` (shell-based, fast)
- [ ] Create `pre-flight-audit-agent.sh` (LLM-powered, thorough)
- [ ] Test in 2-3 repos with path dependencies
- [ ] Verify uncommitted dep detection works

#### Agent 4: Verification Scripts
- [ ] Create `verify-ci-alignment.sh`
- [ ] Create `cloud-build-local` optional setup guide
- [ ] Document rollback procedures

### Phase 2: Update Quality Gates Scripts (1-2 hours with 4 parallel agents)

All 32 repos need `scripts/quality-gates.sh` updated to use Docker by default.

#### Changes to `quality-gates.sh`:
```bash
# Add at top of script (after argument parsing)

# Default to Docker unless explicitly disabled
if [ "$NO_DOCKER" != "true" ]; then
    echo "Running quality gates in Docker (matches CI)..."
    
    # Create cache volume for faster dependency installs
    docker volume create quality-gates-cache 2>/dev/null || true
    
    docker run --rm \
        -v $(pwd):/workspace \
        -v quality-gates-cache:/root/.cache/uv \
        -w /workspace \
        quality-gates:latest \
        bash -c "
            uv pip install --system -e '.[dev]'
            NO_DOCKER=true bash scripts/quality-gates.sh \$@
        "
    exit $?
fi

# Rest of native quality gates script continues...
```

**Repos to update (32 total):**
- instruments-service, strategy-service, position-balance-monitor-service
- risk-and-exposure-service, execution-services, execution-algo-library
- market-data-processing-service, market-tick-data-handler
- ml-inference-service, ml-training-service
- features-calendar-service, features-delta-one-service
- features-onchain-service, features-volatility-service
- pnl-attribution-service, alerting-system
- unified-trading-services, unified-config-interface
- unified-domain-client, unified-events-interface
- unified-market-interface, unified-ml-interface, unified-trade-execution-interface
- backtest-ui, trading-analytics-ui, live-health-monitor-ui
- logs-dashboard-ui, batch-audit-ui, client-reporting-ui
- ml-deployment-ui, onboarding-ui, settlement-ui

### Phase 3: Update Quick Merge Scripts (1-2 hours with 4 parallel agents)

All 32 repos have `scripts/quickmerge.sh` that currently runs quality gates.

#### Changes to `quickmerge.sh`:

**Goal**: Add pre-flight audit, enable watch mode by default, remove quality gates execution

**REMOVE** this section (lines 115-127):
```bash
# Run quality gates in two phases: (1) auto-fix ruff format/lint, (2) verify
if [ -f "scripts/quality-gates.sh" ]; then
    echo "[$REPO_NAME] Phase 1: Running quality gates (auto-fix ruff format + check)..."
    bash scripts/quality-gates.sh
    echo "[$REPO_NAME] Phase 2: Verifying quality gates (--no-fix)..."
    if ! bash scripts/quality-gates.sh --no-fix; then
        echo "[$REPO_NAME] ❌ Quality gates FAILED - Fix remaining issues before merging"
        exit 1
    fi
    echo "[$REPO_NAME] ✅ Quality gates PASSED - Proceeding with merge"
else
    echo "[$REPO_NAME] ⚠️  No quality-gates.sh found (skipping quality gate check)"
fi
```

**REPLACE** with:
```bash
# ==========================================
# PRE-FLIGHT AUDIT (BEFORE quality gates)
# ==========================================

echo "[$REPO_NAME] Running pre-flight audit (before quality gates)..."

# Option 1: Shell-based audit (fast, basic checks)
if bash "$WORKSPACE_ROOT/.cursor/scripts/pre-flight-audit.sh" "$REPO_NAME"; then
    echo "[$REPO_NAME] ✅ Pre-flight audit PASSED (shell)"
else
    echo "[$REPO_NAME] ❌ Pre-flight audit FAILED"
    echo ""
    echo "Common fixes:"
    echo "  - Commit changes in path dependencies first"
    echo "  - Fix E722 in global ruff ignore"
    echo "  - Address large files (>1500 lines)"
    exit 1
fi

# Option 2: LLM-powered audit (thorough, auto-fixes violations)
# Uncomment to enable agent-based audit:
# if bash "$WORKSPACE_ROOT/.cursor/scripts/pre-flight-audit-agent.sh" "$REPO_NAME"; then
#     echo "[$REPO_NAME] ✅ Pre-flight audit PASSED (agent)"
# else
#     echo "[$REPO_NAME] ❌ Pre-flight audit FAILED (agent)"
#     exit 1
# fi

echo ""

# Note: Quality gates run AFTER pre-flight audit passes
# This is handled by pre-push hook (via act) + watch mode
```

**Update header comment** (lines 14-21):
```bash
# What it does:
#   1. Runs pre-flight audit (checks path deps, Codex compliance)
#   2. Stashes changes, creates new branch from origin/main
#   3. Restores stashed changes onto new branch
#   4. Stages changes (--files or -A), commits
#   5. Pushes branch (pre-push hook runs act + watch mode for auto-fix)
#   6. Creates PR with auto-merge (squash)
#   7. Stays on PR branch (does NOT checkout main)
#
# Note: Quality gates run via act in quickmerge Stage 3 (Docker + GitHub workflows)
```

### Phase 4: Update Codex Documentation (30-45 min with 2 parallel agents)

#### Agent 1: Update `quality-gates.md`

File: `/unified-trading-codex/06-coding-standards/quality-gates.md`

**Line 8** - Update TL;DR:
```markdown
operates in two phases: Phase 1 (auto-fix with `ruff format --line-length 120` + `ruff check --fix --line-length 120`)
and Phase 2 (verify with `--no-fix`, exits non-zero if any issue remains). Type checking uses **basedpyright**
(blocking). Quality gates run in Docker by default for environment parity. Quickmerge runs pre-merge checks only
(quality gates handled by pre-push hook via act). **Watch mode enabled by default** - auto-fixes pre-push failures
via LLM agent (Cursor/Claude/Aider). If quality gates fail, fix the root cause -- never bypass.
```

**Add new section after line 33**:
```markdown
## Three-Stage Consistency (Local → GitHub Actions → Cloud Build)

**Architecture:** All three stages use the same Docker image for 100% environment parity.

### Local Development (Docker by Default)
```bash
# Runs in Docker automatically (matches CI)
bash scripts/quality-gates.sh

# Skip Docker for debugging (native execution)
NO_DOCKER=true bash scripts/quality-gates.sh
```

### Pre-Push Hook (Act Simulation)
```bash
# Automatically runs on git push
# Simulates full GitHub Actions workflow
git push  # Pre-push hook runs: act -j quality-gates
```

### Quick Merge (Pre-Merge Checks Only)
```bash
# NO LONGER runs quality gates (handled by pre-push hook)
# Focuses on additional checks: dependency versions, breaking changes, etc.
# Watch mode enabled by default (auto-fixes pre-push failures via LLM)
bash scripts/quickmerge.sh "feat: add feature"

# Disable watch mode (manual fixes if pre-push fails)
bash scripts/quickmerge.sh "feat: add feature" --no-watch
```

**Why This Architecture:**
- **Local quality gates (Docker):** Ensures environment parity (~30s with caching)
- **Pre-push hook (act):** Catches GitHub-specific issues before push (~1-2min)
- **Quick merge (watch mode):** Auto-fixes pre-push failures via LLM agent (default)
- **No duplication:** Quality gates run once in pre-push hook/watcher

**Setup:** See `.cursor/plans/code_optimizations_and_ci_cd_alignment/03-cicd-alignment.md`
**Watch Mode:** See `.cursor/plans/code_optimizations_and_ci_cd_alignment/03-cicd-alignment-watcher-addon.md`
```

#### Agent 2: Create New Codex Doc

File: `/unified-trading-codex/05-infrastructure/local-ci-simulation.md`

```markdown
# Local CI/CD Simulation

## Overview

Run GitHub Actions and Cloud Build locally before pushing to catch issues early.

## Tools

### 1. Act (GitHub Actions Simulation)

**Install:**
```bash
brew install act
```

**Configure secrets:**
```bash
echo "GH_PAT=$GH_PAT" > ~/.secrets
```

**Run workflow locally:**
```bash
act -j quality-gates --secret-file ~/.secrets
```

### 2. Docker (Environment Parity)

**Pull quality gates image:**
```bash
docker pull asia-northeast1-docker.pkg.dev/YOUR_PROJECT_ID/quality-gates:latest
```

**Run quality gates in Docker:**
```bash
bash scripts/quality-gates.sh  # Uses Docker by default
```

### 3. cloud-build-local (Optional, Best Effort)

**Install:**
```bash
gcloud components install cloud-build-local
```

**Run cloudbuild.yaml locally:**
```bash
cloud-build-local --config=cloudbuild.yaml --dryrun=false .
```

**Limitations:** No Cloud Build substitutions, no Secret Manager, no Artifact Registry auth.
**Recommendation:** Use Docker approach for true parity.

## Pre-Push Hook

Automatically installed in all 32 repos. Runs act before each push.

**Skip hook for urgent pushes:**
```bash
git push --no-verify
```

## Workflow

1. **Daily development:** `bash scripts/quality-gates.sh` (Docker, ~30s)
2. **Ready to merge:** `bash scripts/quickmerge.sh` (pre-merge checks)
3. **Push:** `git push` (pre-push hook runs act automatically, ~1-2min)

## Troubleshooting

**Act fails with authentication error:**
- Check `~/.secrets` has valid `GH_PAT`
- Regenerate token if expired

**Docker build slow:**
- Check volume cache: `docker volume ls | grep quality-gates-cache`
- Prune old layers: `docker system prune -a`

**Pre-push hook always passes:**
- Verify hook installed: `ls -la .git/hooks/pre-push`
- Check hook is executable: `chmod +x .git/hooks/pre-push`
```

### Phase 5: Update Cursor Rules (15-30 min)

Create new file: `/.cursor/rules/local-ci-simulation.mdc`

```markdown
# Local CI/CD Simulation

## Quality Gates Default Behavior

**Rule:** `scripts/quality-gates.sh` MUST use Docker by default to ensure CI parity.

```bash
# Correct (Docker by default)
bash scripts/quality-gates.sh

# Debugging only (skip Docker)
NO_DOCKER=true bash scripts/quality-gates.sh
```

## Quick Merge Behavior

**Rule:** `scripts/quickmerge.sh` MUST NOT run quality gates (handled by pre-push hook).

Quick merge runs:
- Pre-merge checks (dependency versions, breaking changes)
- Creates PR branch
- Pushes (pre-push hook runs act automatically)

## Pre-Push Hook

**Rule:** All 32 repos MUST have pre-push hook that runs act.

Hook location: `.git/hooks/pre-push`

Skip hook: `git push --no-verify` (only for urgent fixes)

## Act Configuration

**Rule:** Use `~/.secrets` for local secrets (never commit).

```bash
# One-time setup
echo "GH_PAT=$GH_PAT" > ~/.secrets
```

## Documentation References

- Full guide: `unified-trading-codex/05-infrastructure/local-ci-simulation.md`
- Implementation plan: `.cursor/plans/code_optimizations_and_ci_cd_alignment/03-cicd-alignment.md`
- Quality gates: `unified-trading-codex/06-coding-standards/quality-gates.md`
```

### Phase 6: Rollout & Testing (2-3 hours with 8 parallel agents)

#### Validation Checklist (per repo):
- [ ] `quality-gates.sh` updated (Docker default)
- [ ] `quickmerge.sh` updated (removed quality gates)
- [ ] Pre-push hook installed
- [ ] Test quality gates locally
- [ ] Test pre-push hook
- [ ] Test quickmerge flow

#### Agent Assignment (8 agents × 4 repos each):
- Agent 1: instruments-service, strategy-service, position-balance-monitor-service, risk-and-exposure-service
- Agent 2: execution-services, execution-algo-library, market-data-processing-service, market-tick-data-handler
- Agent 3: ml-inference-service, ml-training-service, features-calendar-service, features-delta-one-service
- Agent 4: features-onchain-service, features-volatility-service, pnl-attribution-service, alerting-system
- Agent 5: unified-trading-services, unified-config-interface, unified-domain-client, unified-events-interface
- Agent 6: unified-market-interface, unified-ml-interface, unified-trade-execution-interface, backtest-ui
- Agent 7: trading-analytics-ui, live-health-monitor-ui, logs-dashboard-ui, batch-audit-ui
- Agent 8: client-reporting-ui, ml-deployment-ui, onboarding-ui, settlement-ui

### Phase 7: Final Verification (30 min)

- [ ] Run `verify-ci-alignment.sh` in all repos
- [ ] Test end-to-end flow in 3 representative repos (Python service, UI, interface)
- [ ] Update this plan status to "✅ COMPLETED"
- [ ] Document any issues encountered

---

## 🔄 Migration Path for Agents

**Before (Current):**
```bash
# Agent workflow
bash scripts/quality-gates.sh --no-fix  # Check first
# ... make changes ...
bash scripts/quickmerge.sh "fix: update" # Runs quality gates again (DUPLICATE)
```

**After (New):**
```bash
# Agent workflow
bash scripts/quality-gates.sh  # Docker by default, ~30s
# ... make changes ...
bash scripts/quickmerge.sh "fix: update"  # Pre-merge checks only, no duplication
git push  # Pre-push hook runs act automatically
```

**Key Changes for Agents:**
1. Quality gates now run in Docker by default (transparent)
2. Quickmerge no longer runs quality gates (pre-push hook handles it)
3. Pre-push hook runs act automatically (catches GitHub-specific issues)

---

## 📊 Updated Success Metrics

### Core CI/CD Alignment
- [ ] All three stages use same Python version (3.13)
- [ ] All three stages use same ruff version (0.15.0)
- [ ] All three stages use same pytest version
- [ ] Local Docker run matches GitHub Actions
- [ ] GitHub Actions matches Cloud Build
- [ ] Verification script passes

### Pre-Push Infrastructure
- [ ] Pre-push hooks installed in all 32 repos
- [ ] `~/.secrets` configured with GH_PAT
- [ ] Act runs successfully in pre-push hook

### Script Updates
- [ ] Quality gates scripts updated in all 32 repos (Docker default)
- [ ] Quick merge scripts updated in all 32 repos (removed quality gates, watch mode default)

### Pre-Flight Audit
- [ ] Pre-flight audit script created (shell-based)
- [ ] Pre-flight audit agent created (LLM-powered)
- [ ] Uncommitted path dependency detection working
- [ ] Codex compliance checks working
- [ ] Cursor rules audit working
- [ ] Integrated into quickmerge (runs before quality gates)

### Watch Mode (Auto-Fix)
- [ ] LLM agent wrapper created and tested
- [ ] Pre-push watcher created and tested
- [ ] Watch mode enabled by default in quickmerge
- [ ] Cursor CLI agent working (model: auto - FREE)
- [ ] Claude Code CLI fallback working
- [ ] API key setup documented (`/tmp/cursor_key.txt`)

### Documentation
- [ ] Codex docs updated (quality-gates.md + new local-ci-simulation.md)
- [ ] Cursor rules created (local-ci-simulation.mdc + quickmerge-watch-mode.mdc)
- [ ] Watch mode documented in all relevant places

### Results
- [ ] Zero "works locally, fails in CI" issues
- [ ] No double execution of quality gates
- [ ] Auto-fix success rate >70% on first attempt
