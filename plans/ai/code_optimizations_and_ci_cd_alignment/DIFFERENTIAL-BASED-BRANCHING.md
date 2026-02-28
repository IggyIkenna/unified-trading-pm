# Differential-Based Branching Strategy

## Core Principle

**Use main by default, branch only when necessary.**

"Necessary" = Any dependency differs from `origin/main` (committed or uncommitted)

---

## The Key Check

### **Differential vs Main (Not Just Uncommitted)**

```bash
# OLD (Incomplete)
if [ -n "$(git status --porcelain)" ]; then
    # Only catches uncommitted changes
fi

# NEW (Complete)
if ! git diff origin/main --quiet; then
    # Catches:
    # - Uncommitted changes (staged or unstaged)
    # - Committed changes to a branch (not yet merged to main)
    # - Combination of both
fi
```

**Why this matters**:
```
Scenario: You committed changes to unified-trading-services on branch "test-feature"
  - git status --porcelain: Empty ✅ (no uncommitted changes)
  - git diff origin/main: HAS DIFF ❌ (branch differs from main)

OLD check: Would say "clean", merge to main ← ❌ WRONG
NEW check: Detects diff, requires --dep-branch ← ✅ CORRECT
```

---

## Three Workflow Modes

### **Mode 1: Main-Only (Default, No Conflicts)**

**When**: All dependencies match `origin/main`

**Command**:
```bash
bash scripts/quickmerge.sh "feat: new API"
# No --dep-branch flag
```

**Behavior**:
```
Stage 1: Check dependencies vs main
  ├─> For each dep: git diff origin/main --quiet
  ├─> All clean? → Use main for everything
  └─> Any diff? → ERROR, suggest --dep-branch

Stage 2-7: Normal quickmerge
  └─> Everything uses main
  └─> GitHub Actions clones from main
  └─> Cloud Build uses main
```

**Result**: Fast, simple, no branch overhead ✅

---

### **Mode 2: Auto-Detect (Error + Suggestion)**

**When**: Dependency differs from main, but no `--dep-branch` specified

**Command**:
```bash
bash scripts/quickmerge.sh "feat: new API"
# Dependency has diff from main
```

**Behavior**:
```
Stage 1: Check dependencies vs main
  ├─> unified-trading-services: git diff origin/main --quiet
  └─> ❌ HAS DIFF

❌ ERROR MESSAGE:

┌─────────────────────────────────────────────────────────────┐
│ Dependency Conflict Detected                                │
└─────────────────────────────────────────────────────────────┘

Repository: unified-trading-services
Status: DIFFERS FROM MAIN

Changes detected:
  • 5 files changed (committed to local branch)
  • 2 files staged (uncommitted)
  • 1 file modified (unstaged)

You CANNOT merge to main with divergent dependencies.

═══════════════════════════════════════════════════════════════

Choose one:

Option 1: DISCARD local dependency changes (go back to main)
  cd unified-trading-services
  git reset --hard origin/main
  cd - && bash scripts/quickmerge.sh "feat: new API"

Option 2: USE BRANCH ISOLATION (recommended)
  bash scripts/quickmerge.sh "feat: new API" --dep-branch "my-feature"
  
  This will:
  • Create "my-feature" branch in ALL repos (deps + current)
  • Cascade quickmerge dependencies FIRST
  • Isolate changes from main
  • Safe parallel development

═══════════════════════════════════════════════════════════════

Exiting. Please choose an option above.

exit 1
```

**Result**: Forces explicit decision, prevents accidental main pollution ✅

---

### **Mode 3: Branch Isolation (Explicit)**

**When**: User specifies `--dep-branch`

**Command**:
```bash
bash scripts/quickmerge.sh "feat: new API" --dep-branch "my-feature"
```

**Behavior**:
```
Stage 1: Check dependencies
  ├─> For each dep: git diff origin/main --quiet
  ├─> IF HAS DIFF:
  │   └─> Cascade quickmerge to "my-feature"
  └─> IF NO DIFF:
      └─> Still create "my-feature" branch (isolation)
      └─> Why? Prevent main changes during development

Stage 2: Cascade all deps to "my-feature"
  ├─> Even deps with no diff get "my-feature" branch
  └─> Complete isolation from main

Stage 3-7: Quickmerge current repo @ "my-feature"
  └─> GitHub Actions uses "my-feature" for all deps
  └─> Cloud Build uses "my-feature" for all deps
```

**Result**: Complete isolation, safe parallel dev ✅

---

## Implementation: Stage 1 (Differential Check)

### Enhanced Pre-Flight Audit

```bash
# Stage 1: Dependency validation (differential-based)
check_dependencies_vs_main() {
    local dep_branch="$1"  # Empty if not specified
    local has_diff=false
    local diff_repos=()
    
    # Read dependency matrix
    if [ ! -f ".dependency-matrix.json" ]; then
        echo "✅ No dependencies"
        return 0
    fi
    
    local deps=$(jq -r '.dependencies[].name' .dependency-matrix.json)
    
    echo "Checking dependencies vs origin/main..."
    echo ""
    
    for dep in $deps; do
        dep_path="$WORKSPACE_ROOT/$dep"
        
        if [ ! -d "$dep_path" ]; then
            echo "⚠️  $dep: Not found (skipping)"
            continue
        fi
        
        cd "$dep_path"
        
        # Fetch latest main
        git fetch origin main --quiet 2>/dev/null || true
        
        # Check if local differs from origin/main
        if ! git diff origin/main --quiet 2>/dev/null; then
            has_diff=true
            diff_repos+=("$dep")
            
            # Get diff stats
            files_changed=$(git diff origin/main --numstat | wc -l | tr -d ' ')
            staged_files=$(git diff --cached --numstat | wc -l | tr -d ' ')
            unstaged_files=$(git diff --numstat | wc -l | tr -d ' ')
            
            echo "❌ $dep: DIFFERS FROM MAIN"
            echo "   • $files_changed file(s) differ from main"
            echo "   • $staged_files file(s) staged"
            echo "   • $unstaged_files file(s) modified (unstaged)"
            echo ""
        else
            echo "✅ $dep: Clean (matches origin/main)"
        fi
        
        cd "$REPO_DIR"
    done
    
    echo ""
    
    # Decision logic
    if [ "$has_diff" = true ]; then
        # Dependencies differ from main
        
        if [ -z "$dep_branch" ]; then
            # No --dep-branch specified → ERROR
            echo "═══════════════════════════════════════════════════════════════"
            echo "❌ DEPENDENCY CONFLICT DETECTED"
            echo "═══════════════════════════════════════════════════════════════"
            echo ""
            echo "The following dependencies DIFFER from origin/main:"
            for repo in "${diff_repos[@]}"; do
                echo "  • $repo"
            done
            echo ""
            echo "You CANNOT merge to main with divergent dependencies."
            echo ""
            echo "═══════════════════════════════════════════════════════════════"
            echo "Choose one:"
            echo ""
            echo "Option 1: DISCARD local dependency changes (reset to main)"
            for repo in "${diff_repos[@]}"; do
                echo "  cd $WORKSPACE_ROOT/$repo && git reset --hard origin/main"
            done
            echo "  cd $REPO_DIR && bash scripts/quickmerge.sh \"$COMMIT_MSG\""
            echo ""
            echo "Option 2: USE BRANCH ISOLATION (recommended)"
            echo "  bash scripts/quickmerge.sh \"$COMMIT_MSG\" --dep-branch \"my-feature\""
            echo ""
            echo "  This will:"
            echo "  • Create \"my-feature\" branch in ALL repos"
            echo "  • Cascade quickmerge dependencies FIRST"
            echo "  • Isolate your changes from main"
            echo "  • Enable safe parallel development"
            echo ""
            echo "═══════════════════════════════════════════════════════════════"
            exit 1
        else
            # --dep-branch specified → Cascade
            echo "✅ --dep-branch specified: Using branch isolation mode"
            echo "   Branch: $dep_branch"
            echo ""
            echo "Will cascade quickmerge to dependencies with diffs..."
            return 0
        fi
    else
        # All dependencies match main
        
        if [ -n "$dep_branch" ]; then
            # --dep-branch specified but no diffs
            echo "ℹ️  --dep-branch specified, but no dependencies differ from main"
            echo "   Still using branch isolation (as requested)"
            echo "   Branch: $dep_branch"
            echo ""
            echo "All dependencies will be moved to \"$dep_branch\" for isolation."
            return 0
        else
            # Normal main workflow
            echo "✅ All dependencies match origin/main"
            echo "   Using main branch (normal workflow)"
            return 0
        fi
    fi
}

# Call in Stage 1
check_dependencies_vs_main "$DEP_BRANCH"
```

---

## Cursor Rules Update

### `.cursor/rules/differential-based-branching.mdc`

```markdown
# Differential-Based Branching

## Golden Rule

**Use main by default. Branch only when dependencies differ from main.**

## Agent Instructions

### Default Workflow (Main)

```bash
# When all dependencies match origin/main
bash scripts/quickmerge.sh "feat: new API"
```

**Quickmerge will**:
- Check all dependencies vs origin/main
- If all clean → Use main for everything
- Fast, simple, no branch overhead

### Branch Isolation Workflow

```bash
# When dependencies differ from origin/main
bash scripts/quickmerge.sh "feat: new API" --dep-branch "my-feature"
```

**Quickmerge will**:
- Check all dependencies vs origin/main
- Cascade quickmerge to "my-feature" for diffs
- Create "my-feature" in ALL repos (isolation)
- GitHub/Cloud Build use "my-feature"

### When to Use --dep-branch

**Use --dep-branch when**:
1. You've made changes to a dependency (committed or uncommitted)
2. Dependency is on a feature branch (not merged to main)
3. You want complete isolation from main changes

**DON'T use --dep-branch when**:
1. All dependencies match origin/main
2. Just working on current repo (no dep changes)
3. Normal feature development

## Error Handling

If you forget --dep-branch:

```
❌ DEPENDENCY CONFLICT DETECTED
   unified-trading-services DIFFERS FROM MAIN
   
   Use: bash scripts/quickmerge.sh "msg" --dep-branch "my-feature"
```

**Action**: Add --dep-branch flag and re-run

## Key Difference: Differential vs Uncommitted

**OLD (Incomplete)**:
- Only checked uncommitted changes
- Missed committed-to-branch changes

**NEW (Complete)**:
- Checks local vs origin/main (git diff)
- Catches ALL divergence (committed or uncommitted)
```

---

## Codex Documentation Update

### `unified-trading-codex/06-coding-standards/quickmerge-branching.md`

```markdown
# Quickmerge Branching Strategy

## Overview

Quickmerge uses **differential-based branching**:
- Default: main branch (fast, simple)
- Branch isolation: When dependencies differ from main

## Workflow Decision Tree

```
Start: bash scripts/quickmerge.sh "msg"
  │
  ├─> Check: Do dependencies differ from origin/main?
  │   │
  │   ├─> NO → Use main (normal workflow)
  │   │   └─> GitHub/Cloud Build use main
  │   │
  │   └─> YES → Do you have --dep-branch flag?
  │       │
  │       ├─> NO → ERROR + Suggest --dep-branch
  │       │   └─> Exit
  │       │
  │       └─> YES → Branch isolation mode
  │           ├─> Cascade deps to branch
  │           └─> GitHub/Cloud Build use branch
```

## Examples

### Example 1: Normal (Main)

```bash
cd instruments-service
vim instruments_service/main.py  # Edit current repo only

bash scripts/quickmerge.sh "feat: add validation"
# ✅ Deps match main → Uses main
# ✅ Fast, simple
```

### Example 2: Dependency Changed (Branch Required)

```bash
cd instruments-service
vim ../unified-trading-services/core.py  # Edit dependency

bash scripts/quickmerge.sh "feat: update API"
# ❌ Error: unified-trading-services differs from main
# 💡 Suggestion: Use --dep-branch

bash scripts/quickmerge.sh "feat: update API" --dep-branch "my-feature"
# ✅ Cascade: unified-trading-services @ my-feature
# ✅ Then: instruments-service @ my-feature
# ✅ Complete isolation
```

### Example 3: Multi-Repo Feature

```bash
# Scenario: Feature spans 3 repos
cd instruments-service
vim instruments_service/main.py
vim ../unified-trading-services/core.py
vim ../unified-config-interface/config.py

# One command handles everything
bash scripts/quickmerge.sh "feat: major refactor" --dep-branch "refactor-2024"

# Automatic cascade:
# 1. unified-config-interface @ refactor-2024
# 2. unified-trading-services @ refactor-2024
# 3. instruments-service @ refactor-2024

# All on same branch, complete isolation
```

## Benefits

✅ **Safe**: Can't accidentally merge divergent deps to main  
✅ **Simple**: Default is main (no branch overhead)  
✅ **Isolated**: Branch mode creates complete isolation  
✅ **Automatic**: Cascade handles dependency order  
✅ **Clear**: Error messages guide correct usage  
```

---

## Summary: Key Changes

### 1. **Differential Check (Not Just Uncommitted)**
```bash
# NEW: Checks local vs origin/main
if ! git diff origin/main --quiet; then
    # Has diff (committed or uncommitted)
fi
```

### 2. **Three Modes**
- **Main-only** (default, no diffs)
- **Error** (diffs detected, no --dep-branch)
- **Branch isolation** (--dep-branch specified)

### 3. **Prevents Accidental Main Pollution**
```bash
# ❌ Can't do this anymore:
bash scripts/quickmerge.sh "feat: update"
# (when deps differ from main)

# ✅ Must be explicit:
bash scripts/quickmerge.sh "feat: update" --dep-branch "my-feature"
```

### 4. **Complete Isolation on Branch**
```bash
# When --dep-branch specified:
# - ALL deps move to that branch (even clean ones)
# - Prevents main changes during development
# - Complete isolation
```

---

## Files to Update

- [ ] `UNIFIED-QUICKMERGE-TEMPLATE.sh` - Add differential check
- [ ] `.cursor/rules/differential-based-branching.mdc` - New rule
- [ ] `unified-trading-codex/06-coding-standards/quickmerge-branching.md` - New doc
- [ ] `pre-flight-audit.sh` - Use differential check
- [ ] All GitHub workflows - Support branch mode
- [ ] All cloudbuild.yaml - Add polling logic

---

Created: **`DIFFERENTIAL-BASED-BRANCHING.md`** ✅

This ensures:
- ✅ Main by default (fast, simple)
- ✅ Branch only when necessary (differential from main)
- ✅ Complete isolation on branch (all deps)
- ✅ Prevents accidental main pollution
