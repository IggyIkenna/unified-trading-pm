# Branch-Based Dependency Workflow

## Problem Statement

When working on features that span multiple repos, you need to:
1. Branch unified-trading-services (e.g., "fix-linter-issue")
2. Branch instruments-service (e.g., "use-new-ucs-api")
3. Test them together locally
4. Have GitHub Actions test with same branches
5. Have Cloud Build use same branches

**Challenge**: How to ensure local/GitHub/Cloud Build all use the SAME committed code?

---

## Solution Architecture

### Key Principle: **Dependencies Installed at Runtime, Not Baked In**

```
Docker Image (quality-gates:latest)
  ├─> Python 3.13
  ├─> Tools (ruff, pytest, basedpyright)
  └─> NO application dependencies

Dependencies (unified-trading-services, etc.)
  ├─> Local: Installed from path (MUST be committed)
  ├─> GitHub: Cloned and installed at specific branch/commit
  └─> Cloud Build: Cloned and installed at specific branch/commit
```

---

## Workflow: Branch-Based Dependencies

### Step 1: Make Changes in Dependency Repo

```bash
cd unified-trading-services

# Make changes
vim unified_trading_services/some_file.py

# Commit changes (REQUIRED before downstream)
git add -A
git commit -m "fix: update linter rules"

# Push to branch
bash scripts/quickmerge.sh "fix: update linter rules"
# This creates PR for unified-trading-services on branch like "quickmerge-20260224-123456"
```

### Step 2: Use Branched Dependency in Downstream Repo

```bash
cd instruments-service

# Update to use new UCS API
vim instruments_service/main.py

# Run quickmerge with dependency branch specified
bash scripts/quickmerge.sh "feat: use new UCS API" \
  --dep-branches "unified-trading-services:quickmerge-20260224-123456"

# What this does:
# 1. Validates unified-trading-services @ branch has NO uncommitted changes
# 2. Runs local quality gates using that branch (from path)
# 3. Creates PR with branch metadata
# 4. Runs act with same branch
# 5. GitHub Actions will use same branch
# 6. Cloud Build will use same branch
```

---

## Implementation: Enhanced Quickmerge

### Parse --dep-branches Argument

```bash
# Parse --dep-branches "repo1:branch1,repo2:branch2"
DEP_BRANCHES=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dep-branches)
            DEP_BRANCHES="$2"
            shift 2
            ;;
        # ... other args
    esac
done

# Parse into array
# Example: "unified-trading-services:fix-linter,unified-config-interface:main"
IFS=',' read -ra DEP_BRANCH_ARRAY <<< "$DEP_BRANCHES"

# Build dependency branch map
declare -A DEP_BRANCH_MAP
for entry in "${DEP_BRANCH_ARRAY[@]}"; do
    IFS=':' read -r repo branch <<< "$entry"
    DEP_BRANCH_MAP[$repo]=$branch
done
```

### Stage 1: Validate Dependencies on Correct Branches

```bash
# Stage 1: Dependency validation
for dep in "${PATH_DEPS[@]}"; do
    dep_path="$WORKSPACE_ROOT/$dep"
    cd "$dep_path"
    
    # Check if branch specified
    expected_branch="${DEP_BRANCH_MAP[$dep]:-main}"
    current_branch=$(git rev-parse --abbrev-ref HEAD)
    
    if [ "$current_branch" != "$expected_branch" ]; then
        echo "❌ $dep: Expected branch '$expected_branch', but on '$current_branch'"
        echo "   Run: cd $dep_path && git checkout $expected_branch"
        exit 1
    fi
    
    # Check for uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        echo "❌ $dep @ $expected_branch: HAS UNCOMMITTED CHANGES"
        echo "   Commit changes first, then re-run quickmerge"
        exit 1
    fi
    
    # Record commit hash for reproducibility
    commit_hash=$(git rev-parse HEAD)
    echo "✅ $dep @ $expected_branch (commit: $commit_hash)"
    
    DEP_COMMIT_MAP[$dep]=$commit_hash
done
```

### Stage 4: Create PR with Dependency Metadata

```bash
# Stage 4: Create PR with branch metadata
PR_BODY="## Changes

$COMMIT_MSG

## Dependencies

This PR depends on specific branches/commits of dependencies:

"

# Add dependency info
for dep in "${!DEP_BRANCH_MAP[@]}"; do
    branch="${DEP_BRANCH_MAP[$dep]}"
    commit="${DEP_COMMIT_MAP[$dep]}"
    PR_BODY+="- **$dep**: \`$branch\` @ \`$commit\`
"
done

PR_BODY+="

## Testing

Local quality gates and act simulation completed with these dependency versions.

"

# Create PR with metadata
gh pr create \
    --title "$COMMIT_MSG" \
    --body "$PR_BODY" \
    --label "automated" \
    --label "quickmerge"
```

### Stage 5: Act with Branch-Specific Workflow

```bash
# Before running act, generate temporary workflow with branch info
TEMP_WORKFLOW=".github/workflows/quality-gates-temp.yml"

cat > "$TEMP_WORKFLOW" << EOF
name: Quality Gates (Branch-Specific)

on: [push, pull_request]

jobs:
  quality-gates:
    runs-on: ubuntu-latest
    
    container:
      image: asia-northeast1-docker.pkg.dev/\${{ vars.GCP_PROJECT_ID }}/quality-gates:latest
      credentials:
        username: _json_key
        password: \${{ secrets.GCP_SA_KEY }}
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Checkout dependencies (branch-specific)
        env:
          GH_PAT: \${{ secrets.GH_PAT }}
        run: |
EOF

# Add clone commands for each dependency with branch
for dep in "${!DEP_BRANCH_MAP[@]}"; do
    branch="${DEP_BRANCH_MAP[$dep]}"
    commit="${DEP_COMMIT_MAP[$dep]}"
    cat >> "$TEMP_WORKFLOW" << EOF
          # $dep @ $branch (commit: $commit)
          git clone --branch $branch https://x-access-token:\${GH_PAT}@github.com/IggyIkenna/$dep.git ../$dep
          cd ../$dep && git checkout $commit && cd -
EOF
done

cat >> "$TEMP_WORKFLOW" << EOF
      
      - name: Install dependencies
        run: |
EOF

# Add install commands
for dep in "${PATH_DEPS[@]}"; do
    cat >> "$TEMP_WORKFLOW" << EOF
          uv pip install --system -e ../$dep
EOF
done

cat >> "$TEMP_WORKFLOW" << EOF
          uv pip install --system -e ".[dev]"
      
      - name: Run quality gates
        run: bash scripts/quality-gates.sh --no-fix --quick
EOF

# Run act with temporary workflow
act -j quality-gates --workflow "$TEMP_WORKFLOW" --secret-file ~/.secrets

# Clean up
rm "$TEMP_WORKFLOW"
```

---

## GitHub Actions: Branch-Aware Workflow

Update `.github/workflows/quality-gates.yml`:

```yaml
name: Quality Gates

on: [push, pull_request]

jobs:
  quality-gates:
    runs-on: ubuntu-latest
    
    container:
      image: asia-northeast1-docker.pkg.dev/${{ vars.GCP_PROJECT_ID }}/quality-gates:latest
      credentials:
        username: _json_key
        password: ${{ secrets.GCP_SA_KEY }}
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Extract dependency branches from PR
        id: deps
        run: |
          # Parse PR body for dependency info
          # Example: "- **unified-trading-services**: `fix-linter` @ `abc123`"
          
          # Default to main if not specified
          echo "ucs_branch=main" >> $GITHUB_OUTPUT
          echo "uci_branch=main" >> $GITHUB_OUTPUT
          echo "uei_branch=main" >> $GITHUB_OUTPUT
          
          # Extract from PR body (if available)
          if [ -n "${{ github.event.pull_request.body }}" ]; then
            # Parse and extract branches
            # ... (parsing logic)
          fi
      
      - name: Checkout dependencies
        env:
          GH_PAT: ${{ secrets.GH_PAT }}
        run: |
          # Clone dependencies at specified branches
          git clone --branch ${{ steps.deps.outputs.ucs_branch }} \
            https://x-access-token:${GH_PAT}@github.com/IggyIkenna/unified-trading-services.git \
            ../unified-trading-services
          
          git clone --branch ${{ steps.deps.outputs.uci_branch }} \
            https://x-access-token:${GH_PAT}@github.com/IggyIkenna/unified-config-interface.git \
            ../unified-config-interface
          
          git clone --branch ${{ steps.deps.outputs.uei_branch }} \
            https://x-access-token:${GH_PAT}@github.com/IggyIkenna/unified-events-interface.git \
            ../unified-events-interface
      
      - name: Install dependencies
        run: |
          uv pip install --system -e ../unified-trading-services
          uv pip install --system -e ../unified-config-interface
          uv pip install --system -e ../unified-events-interface
          uv pip install --system -e ".[dev]"
      
      - name: Run quality gates
        run: bash scripts/quality-gates.sh --no-fix --quick
```

---

## Cloud Build: Branch-Aware Config

Similar approach for `cloudbuild.yaml`.

---

## Key Guarantees

### 1. **No Uncommitted Changes in Docker**

❌ **WRONG** - Baking deps into Docker image:
```dockerfile
# BAD: Includes uncommitted local changes
COPY ../unified-trading-services /deps/unified-trading-services
RUN pip install /deps/unified-trading-services
```

✅ **CORRECT** - Install at runtime from committed repos:
```bash
docker run -v $WORKSPACE_ROOT:/workspace-root quality-gates:latest bash -c "
    uv pip install -e /workspace-root/unified-trading-services  # Uses committed code only
    ruff check .
"
```

### 2. **Stage 1 Blocks Uncommitted Changes**

```bash
# Pre-flight audit FAILS FAST if uncommitted
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Uncommitted changes detected"
    echo "   Commit first: bash scripts/quickmerge.sh in dependency repo"
    exit 1
fi
```

### 3. **All Three Stages Use Same Commits**

```
Local (Docker):
  ├─> Mounts workspace
  └─> Installs from path (committed code only, verified by Stage 1)

GitHub Actions:
  ├─> Clones branch @ specific commit (from PR metadata)
  └─> Installs from cloned repos

Cloud Build:
  ├─> Clones branch @ specific commit (from PR metadata)
  └─> Installs from cloned repos

RESULT: All three use EXACT SAME committed code ✅
```

---

## Workflow Comparison

### Production Workflow (All Dependencies on Main)

```bash
bash scripts/quickmerge.sh "feat: update"
# Uses main branches for all dependencies
```

### Branch-Based Workflow (Some Dependencies on Feature Branches)

```bash
bash scripts/quickmerge.sh "feat: use new API" \
  --dep-branches "unified-trading-services:fix-linter-issue"
# Uses fix-linter-issue branch for UCS, main for others
```

---

## Benefits

✅ **Reproducible** - Local/GitHub/Cloud Build use same commits  
✅ **Safe** - Pre-flight audit blocks uncommitted changes  
✅ **Traceable** - PR metadata shows exact dependency versions  
✅ **Flexible** - Can work on features spanning multiple repos  
✅ **Fast** - Docker only has tools, deps installed at runtime  

---

## Implementation Checklist

- [ ] Update quickmerge to parse `--dep-branches`
- [ ] Add dependency branch validation to Stage 1
- [ ] Generate branch-specific act workflow
- [ ] Update PR body template with dependency metadata
- [ ] Update GitHub Actions to parse dependency branches from PR
- [ ] Update Cloud Build to parse dependency branches
- [ ] Add Cursor rule for branch-based workflow
- [ ] Document in Codex

---

## Example: Full Multi-Repo Feature Development

```bash
# Step 1: Work on dependency
cd unified-trading-services
vim unified_trading_services/core/service.py
bash scripts/quickmerge.sh "feat: add new validation method"
# PR created: unified-trading-services#123 on branch quickmerge-20260224-123456

# Step 2: Work on downstream repo
cd ../instruments-service
vim instruments_service/main.py  # Use new validation method
bash scripts/quickmerge.sh "feat: use new UCS validation" \
  --dep-branches "unified-trading-services:quickmerge-20260224-123456"
# PR created: instruments-service#456
# PR description includes:
#   Dependencies:
#     - unified-trading-services: quickmerge-20260224-123456 @ abc123

# Step 3: Both PRs test with exact same versions
# ✅ unified-trading-services#123 CI passes (tests itself)
# ✅ instruments-service#456 CI passes (tests with UCS branch)

# Step 4: Merge in order
# 1. Merge unified-trading-services#123 to main
# 2. Update instruments-service PR to use main (or merge as-is)
# 3. Merge instruments-service#456 to main
```

---

## Summary

**Docker image**: Tools only (Python, ruff, pytest)  
**Dependencies**: Installed at runtime from committed repos  
**Pre-flight audit**: Blocks uncommitted changes (Stage 1)  
**Branch tracking**: PR metadata captures exact dependency versions  
**Reproducibility**: Local/GitHub/Cloud Build use same commits  

**Result**: Zero "works locally, fails in CI" due to dependency mismatches ✅
