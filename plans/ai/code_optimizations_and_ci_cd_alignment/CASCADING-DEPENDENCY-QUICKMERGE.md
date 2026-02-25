# Cascading Dependency Quickmerge with Branch Isolation

## Problem Statement

When working on a feature that requires changes across multiple repos:
- Make changes to `unified-cloud-services`
- Make changes to `instruments-service` (depends on UCS)
- Need to test them together
- Need to ensure all dependencies are committed BEFORE downstream

**Current pain**: Manual coordination - "Did I commit UCS? Did I push it? What branch?"

**Solution**: **Automatic cascading quickmerge** - One command handles entire dependency tree.

---

## Core Concept: Single Branch for Entire Tree

### Old Approach (Complex)
```bash
--dep-branches "unified-cloud-services:branch-a,unified-config-interface:branch-b"
# Different branches for each dependency → Hard to track
```

### New Approach (Simple)
```bash
--dep-branch "my-feature"
# ONE branch name for ENTIRE dependency tree → Easy isolation
```

**Benefits**:
- ✅ All related changes on one branch across repos
- ✅ Easy to track: "What's on my-feature branch?"
- ✅ Safe: Isolated from main branch changes
- ✅ Clean: When merged, all branches merge together

---

## Dependency Matrix

### Configuration File: `.dependency-matrix.json`

Create in each repo:

```json
{
  "name": "instruments-service",
  "dependencies": [
    {
      "name": "unified-cloud-services",
      "path": "../unified-cloud-services",
      "required": true
    },
    {
      "name": "unified-config-interface",
      "path": "../unified-config-interface",
      "required": true
    },
    {
      "name": "unified-events-interface",
      "path": "../unified-events-interface",
      "required": true
    }
  ],
  "dev_dependencies": [
    {
      "name": "unified-trading-deployment-v3",
      "path": "../unified-trading-deployment-v3",
      "required": false
    }
  ]
}
```

### Why JSON/YAML Instead of Parsing pyproject.toml?

✅ **Explicit** - Clear dependency relationships  
✅ **Fast** - No parsing needed  
✅ **Metadata** - Can add levels, priority, etc.  
✅ **Cross-language** - Works for Python, Node, etc.  

---

## Cascading Quickmerge Algorithm

### Step 1: Read Dependency Matrix

```bash
# Read .dependency-matrix.json
DEPS=$(jq -r '.dependencies[].name' .dependency-matrix.json)
DEP_PATHS=$(jq -r '.dependencies[] | "\(.name):\(.path)"' .dependency-matrix.json)
```

### Step 2: Build Dependency Graph (Topological Sort)

```bash
# For each dependency, read ITS dependency matrix
# Build graph: repo -> [deps]
# Topologically sort to get execution order

# Example result:
# Level 0: unified-config-interface (no deps)
# Level 1: unified-cloud-services (depends on UCI)
# Level 1: unified-events-interface (depends on UCI)
# Level 2: instruments-service (depends on UCS, UEI)
```

### Step 3: Check for Uncommitted Changes (Bottom-Up)

```bash
# Start from Level 0 (no deps) → Level N (most deps)
for level in sorted_levels:
    for repo in level:
        cd $repo
        
        # Check for uncommitted changes
        if [ -n "$(git status --porcelain)" ]; then
            echo "🔄 $repo has uncommitted changes, cascading quickmerge..."
            
            # Recurse: quickmerge this dependency FIRST
            bash scripts/quickmerge.sh \
                "chore: auto-merge from downstream" \
                --dep-branch "$BRANCH_NAME"
            
            # This will cascade further down if needed
        else
            echo "✅ $repo is clean"
        fi
    done
done
```

### Step 4: Quickmerge Current Repo (Top-Level)

```bash
# All dependencies now committed to $BRANCH_NAME
# Safe to quickmerge current repo
bash scripts/quickmerge.sh "$COMMIT_MSG" --dep-branch "$BRANCH_NAME"
```

---

## Complete Flow Example

### Scenario: 3-level dependency tree

```
instruments-service
  ├─> unified-cloud-services
  │   └─> unified-config-interface
  └─> unified-events-interface
      └─> unified-config-interface
```

### User Action

```bash
cd instruments-service

# Make changes to instruments-service AND dependencies
vim instruments_service/main.py
vim ../unified-cloud-services/unified_cloud_services/core.py
vim ../unified-config-interface/unified_config_interface/config.py

# Run quickmerge with branch name
bash scripts/quickmerge.sh "feat: new API" --dep-branch "my-feature"
```

### Automatic Cascade (What Quickmerge Does)

```
[instruments-service] Starting quickmerge...
[instruments-service] Reading dependency matrix...
[instruments-service] Dependencies: unified-cloud-services, unified-events-interface

[instruments-service] Building dependency graph...
  Level 0: unified-config-interface
  Level 1: unified-cloud-services, unified-events-interface
  Level 2: instruments-service

[instruments-service] Checking Level 0: unified-config-interface
  [unified-config-interface] Has uncommitted changes: YES
  [unified-config-interface] 🔄 Cascading quickmerge...
  [unified-config-interface] No dependencies, proceeding with quickmerge
  [unified-config-interface] Stage 1-7: Full pipeline
  [unified-config-interface] ✅ Pushed to branch "my-feature"

[instruments-service] Checking Level 1: unified-cloud-services
  [unified-cloud-services] Has uncommitted changes: YES
  [unified-cloud-services] 🔄 Cascading quickmerge...
  [unified-cloud-services] Dependency: unified-config-interface
  [unified-config-interface] Already committed @ "my-feature" ✅
  [unified-cloud-services] Stage 1-7: Full pipeline
  [unified-cloud-services] Uses unified-config-interface @ "my-feature"
  [unified-cloud-services] ✅ Pushed to branch "my-feature"

[instruments-service] Checking Level 1: unified-events-interface
  [unified-events-interface] Has uncommitted changes: NO
  [unified-events-interface] ✅ Already clean, skipping

[instruments-service] All dependencies committed, proceeding with quickmerge
[instruments-service] Stage 1-7: Full pipeline
[instruments-service] Uses:
  - unified-cloud-services @ "my-feature"
  - unified-events-interface @ "my-feature"
  - unified-config-interface @ "my-feature"
[instruments-service] ✅ Pushed to branch "my-feature"

🎉 Complete! All repos pushed to branch "my-feature"
  - unified-config-interface PR: #123
  - unified-cloud-services PR: #456
  - instruments-service PR: #789
```

---

## GitHub Actions: Safe by Design

### Why It Works

```
Cascade order ensures commits happen in dependency order:

1. unified-config-interface pushed @ "my-feature" (t=0)
2. unified-cloud-services pushed @ "my-feature" (t=1)
3. instruments-service pushed @ "my-feature" (t=2)

When instruments-service GitHub Actions runs:
  → Clones unified-cloud-services @ "my-feature" ✅ (already pushed at t=1)
  → Clones unified-config-interface @ "my-feature" ✅ (already pushed at t=0)
  → All dependencies available
```

### GitHub Workflow (Auto-Generated)

```yaml
# instruments-service/.github/workflows/quality-gates.yml
name: Quality Gates

on: [push, pull_request]

jobs:
  quality-gates:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Determine branch name
        id: branch
        run: |
          # Extract branch from github ref
          BRANCH=${GITHUB_REF#refs/heads/}
          echo "branch=$BRANCH" >> $GITHUB_OUTPUT
      
      - name: Checkout dependencies (same branch)
        env:
          GH_PAT: ${{ secrets.GH_PAT }}
        run: |
          # Clone all deps at same branch (cascade ensures they exist)
          git clone --branch ${{ steps.branch.outputs.branch }} \
            https://x-access-token:${GH_PAT}@github.com/IggyIkenna/unified-cloud-services.git \
            ../unified-cloud-services || \
            git clone https://x-access-token:${GH_PAT}@github.com/IggyIkenna/unified-cloud-services.git \
            ../unified-cloud-services  # Fallback to main if branch doesn't exist
          
          # Repeat for other deps
```

---

## Cloud Build: Dependency Ordering Challenge

### Problem

```
Cloud Build triggers run in parallel:
  - unified-config-interface Cloud Build starts (t=0)
  - unified-cloud-services Cloud Build starts (t=0)  ← ❌ Needs UCI package!
  - instruments-service Cloud Build starts (t=0)  ← ❌ Needs UCS + UCI packages!
```

### Solution: Dependency-Aware Cloud Build Triggers

#### Option A: Sequential Triggers (Simple, Slow)

```yaml
# instruments-service/cloudbuild.yaml
steps:
  # Wait for dependency builds to complete
  - name: 'gcr.io/cloud-builders/gcloud'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        # Wait for unified-cloud-services build on this branch
        echo "Waiting for dependencies to build..."
        
        # Poll for package availability
        while ! gcloud artifacts docker images list \
          asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-cloud-services \
          --filter="tags:${BRANCH_NAME}" \
          --limit=1 | grep -q "${BRANCH_NAME}"; do
          echo "Waiting for unified-cloud-services@${BRANCH_NAME}..."
          sleep 30
        done
        
        echo "✅ unified-cloud-services@${BRANCH_NAME} available"
  
  # Now proceed with build
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'asia-northeast1-docker.pkg.dev/${PROJECT_ID}/instruments-service:${BRANCH_NAME}', '.']
```

**Pros**: Simple, reliable  
**Cons**: Slow (waits for deps serially)

#### Option B: Cloud Build Triggers with Dependencies (Fast, Complex)

```yaml
# Cloud Build Trigger Config (via gcloud or UI)
# unified-config-interface trigger
name: uci-build
includedFiles: ['**']
substitutions:
  _BRANCH_NAME: $(body.ref)

---
# unified-cloud-services trigger (depends on UCI)
name: ucs-build
includedFiles: ['**']
substitutions:
  _BRANCH_NAME: $(body.ref)
# Wait for UCI trigger to complete
waitFor: ['uci-build']  # ← Cloud Build feature

---
# instruments-service trigger (depends on UCS)
name: instruments-build
includedFiles: ['**']
substitutions:
  _BRANCH_NAME: $(body.ref)
waitFor: ['ucs-build']  # ← Cloud Build feature
```

**Pros**: Fast, Cloud Build handles ordering  
**Cons**: Complex setup, requires Cloud Build trigger dependencies

#### Option C: Pub/Sub Orchestration (Most Robust)

```
1. unified-config-interface build completes
   → Publishes to topic: "uci-build-complete"

2. Cloud Function subscribes to "uci-build-complete"
   → Triggers unified-cloud-services build

3. unified-cloud-services build completes
   → Publishes to topic: "ucs-build-complete"

4. Cloud Function subscribes to "ucs-build-complete"
   → Triggers instruments-service build
```

**Pros**: Robust, observable, can add retry logic  
**Cons**: Most complex

### **Recommendation: Option A (Polling) for Now**

- Simple to implement
- Reliable
- Acceptable for branch-based development (not production)
- Can optimize later if needed

---

## Implementation: Enhanced Quickmerge

### Parse --dep-branch Argument

```bash
DEP_BRANCH=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dep-branch)
            DEP_BRANCH="$2"
            shift 2
            ;;
        *)
            COMMIT_MSG="$1"
            shift
            ;;
    esac
done

# If --dep-branch specified, use it; otherwise use auto-generated branch
if [ -z "$DEP_BRANCH" ]; then
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    NEW_BRANCH="quickmerge-${TIMESTAMP}"
else
    NEW_BRANCH="$DEP_BRANCH"
fi
```

### Read Dependency Matrix

```bash
read_dependency_matrix() {
    local repo_path="$1"
    
    if [ ! -f "$repo_path/.dependency-matrix.json" ]; then
        echo "{\"dependencies\": []}"
        return
    fi
    
    cat "$repo_path/.dependency-matrix.json"
}

# Read current repo's dependencies
DEPS_JSON=$(read_dependency_matrix "$REPO_DIR")
DEP_NAMES=$(echo "$DEPS_JSON" | jq -r '.dependencies[].name')
```

### Topological Sort (Dependency Graph)

```bash
topological_sort() {
    local start_repo="$1"
    local branch="$2"
    
    # Build dependency graph
    declare -A graph
    declare -A in_degree
    
    # BFS to discover all repos in tree
    queue=("$start_repo")
    visited=()
    
    while [ ${#queue[@]} -gt 0 ]; do
        repo="${queue[0]}"
        queue=("${queue[@]:1}")
        
        if [[ " ${visited[@]} " =~ " ${repo} " ]]; then
            continue
        fi
        
        visited+=("$repo")
        
        # Read this repo's dependencies
        repo_path="$WORKSPACE_ROOT/$repo"
        deps=$(jq -r '.dependencies[].name' "$repo_path/.dependency-matrix.json" 2>/dev/null || echo "")
        
        graph[$repo]="$deps"
        
        # Add to queue
        for dep in $deps; do
            queue+=("$dep")
            in_degree[$dep]=$((in_degree[$dep] + 1))
        done
    done
    
    # Topological sort (Kahn's algorithm)
    # ... (standard implementation)
    
    # Return sorted order
    echo "${sorted[@]}"
}

# Get execution order
SORTED_REPOS=$(topological_sort "$REPO_NAME" "$NEW_BRANCH")
```

### Cascade Quickmerge

```bash
cascade_quickmerge() {
    local sorted_repos="$1"
    local branch="$2"
    local commit_msg="$3"
    
    for repo in $sorted_repos; do
        repo_path="$WORKSPACE_ROOT/$repo"
        
        # Skip if current repo (will be done at end)
        if [ "$repo" = "$REPO_NAME" ]; then
            continue
        fi
        
        cd "$repo_path"
        
        # Check for uncommitted changes
        if [ -n "$(git status --porcelain)" ]; then
            echo "🔄 $repo has uncommitted changes, cascading quickmerge..."
            
            # Recursive quickmerge
            bash scripts/quickmerge.sh \
                "chore: auto-merge from downstream ($REPO_NAME)" \
                --dep-branch "$branch"
            
            if [ $? -ne 0 ]; then
                echo "❌ Cascade failed for $repo"
                exit 1
            fi
            
            echo "✅ $repo quickmerge complete"
        else
            echo "✅ $repo is clean, skipping"
        fi
    done
}

# Run cascade
cascade_quickmerge "$SORTED_REPOS" "$NEW_BRANCH" "$COMMIT_MSG"
```

---

## Validation: Error Cases

### Error 1: Circular Dependencies

```bash
# instruments-service depends on unified-cloud-services
# unified-cloud-services depends on instruments-service ← ❌ Circular

# Topological sort will detect this
echo "❌ Circular dependency detected: instruments-service ↔ unified-cloud-services"
exit 1
```

### Error 2: --dep-branch with No Dependencies

```bash
if [ -n "$DEP_BRANCH" ] && [ -z "$DEP_NAMES" ]; then
    echo "❌ Error: --dep-branch specified but no dependencies found"
    echo "   This repo has no dependencies in .dependency-matrix.json"
    exit 1
fi
```

### Error 3: Missing Dependency Matrix

```bash
if [ ! -f "$repo_path/.dependency-matrix.json" ]; then
    echo "⚠️  Warning: $repo has no .dependency-matrix.json"
    echo "   Assuming no dependencies"
fi
```

---

## Benefits

✅ **Automatic** - No manual dep coordination  
✅ **Safe** - Cascade ensures commit order  
✅ **Isolated** - All changes on one branch  
✅ **Traceable** - Clear dependency tree  
✅ **Fast** - Parallel where possible  
✅ **Reproducible** - Same branch across all repos  

---

## Usage Examples

### Example 1: Simple (No Dependencies)

```bash
cd unified-config-interface
bash scripts/quickmerge.sh "fix: update validation"
# No dependencies → quickmerge as usual
```

### Example 2: With Dependencies (Auto-Branch)

```bash
cd instruments-service
bash scripts/quickmerge.sh "feat: new API"
# Auto-generates branch: quickmerge-20260224-123456
# Cascades to dependencies if needed
```

### Example 3: With Dependencies (Named Branch)

```bash
cd instruments-service
bash scripts/quickmerge.sh "feat: new API" --dep-branch "my-feature"
# Uses "my-feature" for entire dependency tree
# Cascades to dependencies if needed
```

### Example 4: Multi-Level Cascade

```bash
cd instruments-service

# Edit files across dependency tree
vim instruments_service/main.py
vim ../unified-cloud-services/core.py
vim ../unified-config-interface/config.py

# One command handles everything
bash scripts/quickmerge.sh "feat: new API" --dep-branch "my-feature"

# Automatic cascade:
# 1. unified-config-interface quickmerge
# 2. unified-cloud-services quickmerge (uses UCI @ my-feature)
# 3. instruments-service quickmerge (uses UCS @ my-feature)
```

---

## Implementation Checklist

- [ ] Create `.dependency-matrix.json` template
- [ ] Add to all 32 repos
- [ ] Implement topological sort function
- [ ] Implement cascade_quickmerge function
- [ ] Update quickmerge template with cascade logic
- [ ] Update GitHub Actions to use same-branch cloning
- [ ] Implement Cloud Build polling for dependencies
- [ ] Add validation for circular dependencies
- [ ] Document in Codex
- [ ] Update Cursor rules

---

## Summary

**One command**: `bash scripts/quickmerge.sh "feat: update" --dep-branch "my-feature"`

**Automatic cascade**:
- Detects uncommitted changes in dependency tree
- Quickmerges dependencies FIRST (lowest to highest)
- Ensures all repos on same branch
- GitHub/Cloud Build safe by design

**Result**: Zero manual dependency coordination ✅
