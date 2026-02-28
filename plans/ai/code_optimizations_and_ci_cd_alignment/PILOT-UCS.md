# Pilot: unified-trading-services Quick Merge Implementation

**Goal**: Test complete flow on one repo, fix issues interactively, then scale.

---

## Current State

### unified-trading-services
- **Branch**: `type-fixes-1771875849`
- **Status**: Uncommitted changes (60+ files modified/deleted/added)
- **Diff from main**: 87 files changed (+2615, -7758)
- **Dependency**: unified-domain-client

### unified-domain-client
- **Diff from main**: 19 files changed (+542, -263)
- **Status**: Also differs from main

**Perfect for testing**: Branch isolation + cascade!

---

## Pilot Plan (Interactive, ~2-3 hours)

### **Step 1: Create Minimal Infrastructure** (30 min)

#### 1a. Create `.dependency-matrix.json` for UCS

```bash
cd unified-trading-services
```

Create file:
```json
{
  "name": "unified-trading-services",
  "dependencies": [
    {
      "name": "unified-domain-client",
      "path": "../unified-domain-client",
      "required": true
    }
  ]
}
```

#### 1b. Create `.env` for UCS

```bash
# .env
ENVIRONMENT=development
```

#### 1c. Set GitHub repo variables

```bash
cd unified-trading-services

# Set dev project ID (for now, same as prod)
gh variable set GCP_PROJECT_ID_DEV --body "central-element-323112"

# Verify
gh variable list
```

---

### **Step 2: Update quickmerge.sh** (45 min)

Instead of creating from scratch, let's **incrementally enhance** existing quickmerge:

```bash
cd unified-trading-services
cp scripts/quickmerge.sh scripts/quickmerge.sh.backup
```

#### Changes to make (in order):

**2a. Add `--dep-branch` argument parsing**

```bash
# After line ~43 (COMMIT_MSG parsing)
DEP_BRANCH=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dep-branch)
            DEP_BRANCH="$2"
            shift 2
            ;;
        --files)
            FILES_ARG="$2"
            shift 2
            ;;
        *)
            COMMIT_MSG="$1"
            shift
            ;;
    esac
done
```

**2b. Add differential dependency check (Stage 1)**

```bash
# After venv activation, BEFORE quality gates

echo "=========================================="
echo "STAGE 1: Dependency Validation"
echo "=========================================="
echo ""

# Check if .dependency-matrix.json exists
if [ -f ".dependency-matrix.json" ]; then
    DEPS=$(jq -r '.dependencies[].name' .dependency-matrix.json 2>/dev/null || echo "")
    
    if [ -n "$DEPS" ]; then
        echo "Checking dependencies vs origin/main..."
        HAS_DIFF=false
        
        for dep in $DEPS; do
            dep_path="$WORKSPACE_ROOT/$dep"
            
            if [ -d "$dep_path" ]; then
                cd "$dep_path"
                git fetch origin main --quiet 2>/dev/null || true
                
                if ! git diff origin/main --quiet 2>/dev/null; then
                    HAS_DIFF=true
                    echo "❌ $dep: DIFFERS from main"
                else
                    echo "✅ $dep: Matches main"
                fi
                
                cd "$REPO_DIR"
            fi
        done
        
        echo ""
        
        if [ "$HAS_DIFF" = "true" ] && [ -z "$DEP_BRANCH" ]; then
            echo "═══════════════════════════════════════════════════════════════"
            echo "❌ DEPENDENCY CONFLICT DETECTED"
            echo "═══════════════════════════════════════════════════════════════"
            echo ""
            echo "Dependencies differ from main, but no --dep-branch specified."
            echo ""
            echo "Choose one:"
            echo ""
            echo "Option 1: DISCARD local dependency changes"
            echo "  cd $dep_path && git reset --hard origin/main"
            echo ""
            echo "Option 2: USE BRANCH ISOLATION (recommended)"
            echo "  bash scripts/quickmerge.sh \"$COMMIT_MSG\" --dep-branch \"my-feature\""
            echo ""
            echo "═══════════════════════════════════════════════════════════════"
            exit 1
        fi
        
        if [ -n "$DEP_BRANCH" ]; then
            echo "✅ --dep-branch specified: $DEP_BRANCH"
            echo "   Will use branch isolation mode"
        fi
    else
        echo "✅ No dependencies found"
    fi
else
    echo "✅ No .dependency-matrix.json (no dependencies)"
fi

echo ""
```

**2c. Add environment-aware project ID**

```bash
# After dependency check, before quality gates

echo "=========================================="
echo "STAGE 2: Environment Configuration"
echo "=========================================="
echo ""

# Read .env if exists
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
    echo "Environment: $ENVIRONMENT"
else
    export ENVIRONMENT="production"
    echo "Environment: production (default)"
fi

echo ""
```

**2d. Keep existing quality gates section (Stage 3)**

No changes needed - existing quality gates work fine.

**2e. Update branch creation to use DEP_BRANCH if specified**

```bash
# Around line 160 (NEW_BRANCH creation)

if [ -n "$DEP_BRANCH" ]; then
    NEW_BRANCH="$DEP_BRANCH"
    echo "Using specified branch: $NEW_BRANCH"
else
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    NEW_BRANCH="quickmerge-${TIMESTAMP}"
    echo "Creating auto-generated branch: $NEW_BRANCH"
fi
```

---

### **Step 3: Test Scenario 1 - Branch Isolation** (30 min)

**Current state**: Both UCS and UDS differ from main

```bash
cd unified-trading-services

# Try without --dep-branch (should error)
bash scripts/quickmerge.sh "feat: type fixes and refactor"

# Expected output:
# ❌ DEPENDENCY CONFLICT DETECTED
# unified-domain-client DIFFERS from main
# Use --dep-branch flag
```

**Then with --dep-branch**:

```bash
bash scripts/quickmerge.sh "feat: type fixes and refactor" --dep-branch "type-fixes-cascade"

# Expected flow:
# Stage 1: Check deps → unified-domain-client differs
# Stage 2: Environment → development
# Stage 3: Quality gates → Run (may fail, we'll fix)
# Stage 4: Create branch "type-fixes-cascade"
# Stage 5: (Skip act for now, add later)
# Stage 6: Push + create PR
```

**Fix issues as they arise** - This is where we'll iterate!

Likely issues:
1. Quality gates fail → Fix code
2. jq not installed → `brew install jq`
3. Path issues → Debug together
4. Git issues → Handle interactively

---

### **Step 4: Add Act Simulation** (30 min)

After basic flow works, add act:

```bash
# Install act if not already
brew install act

# Configure secrets
echo "GH_PAT=$GH_PAT" > ~/.secrets

# Test act separately first
cd unified-trading-services
act -l  # List workflows
act -j quality-gates --secret-file ~/.secrets --dryrun
```

Add to quickmerge (after branch creation, before push):

```bash
echo "=========================================="
echo "STAGE 5: Act Simulation (GitHub Actions)"
echo "=========================================="
echo ""

if command -v act >/dev/null 2>&1; then
    echo "Running act to simulate GitHub Actions..."
    
    if act -j quality-gates --secret-file ~/.secrets; then
        echo "✅ Act simulation passed"
    else
        echo "❌ Act simulation failed"
        echo ""
        echo "Fix issues above, then re-run quickmerge"
        exit 1
    fi
else
    echo "⚠️  act not installed, skipping GitHub Actions simulation"
    echo "   Install: brew install act"
fi

echo ""
```

---

### **Step 5: Test Scenario 2 - Normal Main Flow** (After branch merges)

After merging the branch PRs:

```bash
cd unified-trading-services

# Make a small change
echo "# test" >> README.md

# Run quickmerge (should use main since no dep diffs)
bash scripts/quickmerge.sh "docs: test main workflow"

# Expected:
# Stage 1: All deps match main → Use main
# Stage 3: Quality gates pass
# Stage 5: Act passes
# Stage 7: Push to main
```

---

### **Step 6: Add Cursor GitHub Actions Integration** (30 min)

Research Cursor's built-in GitHub Actions support:

**Option A: Cursor Bot** (if available)
- Check Cursor docs for GitHub App
- Install Cursor bot on repo
- Configure PR reviews

**Option B: Custom Workflow with Cursor CLI**

Create `.github/workflows/pr-watcher.yml`:

```yaml
name: PR Watcher (Cursor)

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  cursor-review:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Get Cursor API Key
        id: cursor-key
        run: |
          # Get from Secret Manager
          echo "CURSOR_API_KEY=$(gcloud secrets versions access latest \
            --secret=cursor-api-key \
            --project=central-element-323112)" >> $GITHUB_OUTPUT
      
      - name: Cursor Analysis
        env:
          CURSOR_API_KEY: ${{ steps.cursor-key.outputs.CURSOR_API_KEY }}
        run: |
          # Create analysis prompt
          PROMPT="Analyze this PR:

          Checks:
          1. Was quickmerge used? (check commit message pattern)
          2. Environment config correct?
          3. Dependencies properly handled?
          4. Quality gates passed?
          5. Any Codex/Cursor rule violations?

          PR Diff:
          $(git diff origin/main...HEAD)

          Return: ✅ PASS or ❌ FAIL with issues + suggestions"
          
          # Run Cursor agent (adapt based on Cursor's CLI)
          # This is placeholder - adjust based on actual Cursor CLI
          result=$(agent --api-key "$CURSOR_API_KEY" --model auto "$PROMPT")
          
          # Post as comment
          gh pr comment --body "$result"
          
          # Check result
          if echo "$result" | grep -q "❌ FAIL"; then
            echo "PR blocked due to issues"
            exit 1
          fi
```

**Research together**: What's the actual Cursor CLI for GitHub Actions?

---

## Success Criteria

After pilot:

✅ **Scenario 1 (Branch)**: UCS + UDS cascade to branch, PR created  
✅ **Scenario 2 (Main)**: Small change on main works  
✅ **Quality gates**: Pass in Docker  
✅ **Act**: Simulates GitHub Actions successfully  
✅ **Environment**: Dev project ID used correctly  
✅ **Cursor review**: PR watcher provides feedback  

---

## Next Steps After Pilot

1. Document issues encountered + fixes
2. Update master plan based on learnings
3. Create standardized templates
4. Roll out to remaining 31 repos (with confidence!)

---

## Let's Start!

Ready to begin? I'll guide you through each step interactively. Which step should we start with?

**Recommendation**: Start with Step 1 (infrastructure), then iterate through steps 2-6 together.
