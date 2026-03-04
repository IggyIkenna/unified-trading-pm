#!/bin/bash
# UNIFIED QUICKMERGE - All-In-One Quality Pipeline
# Runs ALL checks in optimal order before creating PR
#
# Usage:
#   ./scripts/quickmerge.sh "commit message"
#   ./scripts/quickmerge.sh "commit message" --files "path1 path2"
#   ./scripts/quickmerge.sh "commit message" --no-watch  # Disable watch mode
#
# Pipeline (optimal ordering):
#   1. Dependency validation (10s - fast, blocking)
#   2. Pre-flight audit (15s - fast, auto-fix)
#   3. Local quality gates - Docker (30s - fast)
#   4. Create PR branch & commit (5s)
#   5. Act - full GitHub simulation (1-2min - slow, accurate)
#   6. Watch mode - auto-fix if act fails (1-3min if needed)
#   7. Push & create PR (5s)

set -e

# ==========================================
# SETUP
# ==========================================

# Parse arguments
COMMIT_MSG="chore: automated update"
FILES_ARG=""
WATCH_MODE=true  # DEFAULT: watch enabled

while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-watch)
            WATCH_MODE=false
            shift
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

REPO_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
REPO_NAME=$(basename "$REPO_DIR")
WORKSPACE_ROOT="$(cd "$REPO_DIR/.." && pwd)"

cd "$REPO_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "UNIFIED QUICKMERGE: $REPO_NAME"
echo "=========================================="
echo ""

# ==========================================
# STAGE 1: DEPENDENCY VALIDATION (10s)
# ==========================================

echo -e "${BLUE}Stage 1: Dependency Validation${NC}"
echo ""

if bash "$WORKSPACE_ROOT/.cursor/scripts/pre-flight-audit.sh" "$REPO_NAME" --deps-only; then
    echo -e "${GREEN}✅ Dependency validation PASSED${NC}"
else
    echo -e "${RED}❌ Dependency validation FAILED${NC}"
    echo ""
    echo "Action required: Commit changes in path dependencies first"
    exit 1
fi

echo ""

# ==========================================
# STAGE 2: PRE-FLIGHT AUDIT (15s)
# ==========================================

echo -e "${BLUE}Stage 2: Pre-Flight Audit (Codex & Cursor Rules)${NC}"
echo ""

# Option A: Shell-based audit (fast, recommended)
if bash "$WORKSPACE_ROOT/.cursor/scripts/pre-flight-audit.sh" "$REPO_NAME"; then
    echo -e "${GREEN}✅ Pre-flight audit PASSED${NC}"
else
    echo -e "${RED}❌ Pre-flight audit FAILED${NC}"
    echo ""
    echo "Action required: Fix Codex/Cursor violations above"
    exit 1
fi

# Option B: LLM-powered audit (uncomment to enable)
# if bash "$WORKSPACE_ROOT/.cursor/scripts/pre-flight-audit-agent.sh" "$REPO_NAME"; then
#     echo -e "${GREEN}✅ Pre-flight audit PASSED (agent auto-fixed)${NC}"
# else
#     echo -e "${RED}❌ Pre-flight audit FAILED (agent)${NC}"
#     exit 1
# fi

echo ""

# ==========================================
# STAGE 3: LOCAL QUALITY GATES - DOCKER (30s)
# ==========================================

echo -e "${BLUE}Stage 3: Local Quality Gates (Docker)${NC}"
echo ""

if [ -f "scripts/quality-gates.sh" ]; then
    # Run quality gates in Docker (default) for environment parity
    if bash scripts/quality-gates.sh --quick; then
        echo -e "${GREEN}✅ Local quality gates PASSED${NC}"
    else
        echo -e "${RED}❌ Local quality gates FAILED${NC}"
        echo ""
        echo "Fix issues above before continuing."
        echo "Tip: Run 'bash scripts/quality-gates.sh' to see full output"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  No quality-gates.sh found (skipping)${NC}"
fi

echo ""

# ==========================================
# STAGE 4: CREATE PR BRANCH & COMMIT (5s)
# ==========================================

echo -e "${BLUE}Stage 4: Create PR Branch & Commit${NC}"
echo ""

# Check for changes
if [ -z "$(git status --porcelain)" ]; then
    echo "No changes to commit in $REPO_NAME"
    exit 0
fi

# Fetch latest main
git fetch origin main --quiet 2>/dev/null || true

# Check if changes differ from main
if git diff origin/main --quiet 2>/dev/null; then
    echo "No changes from main - nothing to merge"
    exit 0
fi

# Create new branch
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
NEW_BRANCH="quickmerge-${TIMESTAMP}"

echo "Creating branch: $NEW_BRANCH"
git stash --include-untracked --quiet 2>/dev/null || true
git checkout -b "$NEW_BRANCH"
git stash pop --quiet 2>/dev/null || true

# Stage changes
if [ -n "$FILES_ARG" ]; then
    echo "Staging specified files: $FILES_ARG"
    git add $FILES_ARG
else
    echo "Staging all changes"
    git add -A
fi

# Commit
git commit -m "$COMMIT_MSG"
echo -e "${GREEN}✅ Branch created and changes committed${NC}"

echo ""

# ==========================================
# STAGE 5: ACT - FULL GITHUB SIMULATION (1-2min)
# ==========================================

echo -e "${BLUE}Stage 5: Act - Full GitHub Actions Simulation${NC}"
echo ""

if [ "$WATCH_MODE" = true ]; then
    echo "Watch mode enabled (default) - will auto-fix if act fails"
    echo ""

    # Call pre-push watcher (includes act + auto-fix)
    if bash "$WORKSPACE_ROOT/.cursor/scripts/pre-push-watcher.sh"; then
        echo -e "${GREEN}✅ Act simulation PASSED${NC}"
    else
        echo -e "${RED}❌ Act simulation FAILED after auto-fix attempts${NC}"
        echo ""
        echo "Manual intervention required:"
        echo "1. Review errors above"
        echo "2. Fix issues manually"
        echo "3. Re-run: bash scripts/quickmerge.sh \"$COMMIT_MSG\""
        exit 1
    fi
else
    echo "Watch mode disabled (--no-watch) - running act without auto-fix"
    echo ""

    # Run act directly (no auto-fix)
    if act -j quality-gates --secret-file ~/.secrets; then
        echo -e "${GREEN}✅ Act simulation PASSED${NC}"
    else
        echo -e "${RED}❌ Act simulation FAILED${NC}"
        echo ""
        echo "Fix issues above, then re-run quickmerge"
        exit 1
    fi
fi

echo ""

# ==========================================
# STAGE 7: PUSH & CREATE PR (5s)
# ==========================================

echo -e "${BLUE}Stage 7: Push & Create PR${NC}"
echo ""

# Push branch (skip hook since act already ran)
echo "Pushing branch: $NEW_BRANCH"
git push --no-verify -u origin "$NEW_BRANCH"

# Create PR with auto-merge
echo "Creating PR with auto-merge..."
gh pr create \
    --fill \
    --label "automated" \
    --label "quickmerge"

# Enable auto-merge
echo "Enabling auto-merge..."
gh pr merge "$NEW_BRANCH" --auto --squash

echo ""
echo "=========================================="
echo -e "${GREEN}✅ QUICKMERGE COMPLETE${NC}"
echo "=========================================="
echo ""
echo "Summary:"
echo "  ✅ Dependency validation passed"
echo "  ✅ Pre-flight audit passed"
echo "  ✅ Local quality gates passed (Docker)"
echo "  ✅ Act simulation passed (GitHub Actions)"
echo "  ✅ PR created with auto-merge enabled"
echo ""
echo "PR will auto-merge when GitHub Actions pass."
echo ""
echo "View PR: gh pr view"
echo "Monitor CI: gh pr checks"
echo ""
