#!/usr/bin/env bash
# quickmerge for unified-trading-pm
#
# Usage:
#   bash scripts/quickmerge.sh "commit message"
#   bash scripts/quickmerge.sh "commit message" --files "path1 path2"
#
# What it does (in order):
#   Stage 0: Auto-sync .cursor/rules/ and workspace configs INTO this repo
#            (captures any local rule/config changes before committing)
#   Stage 1: Validate workspace-manifest.json is valid JSON
#   Stage 2: Stash changes, create branch from origin/main
#   Stage 3: Restore stash, stage files (--files or all), commit
#   Stage 4: Push branch, create PR with auto-merge (squash)
#   Stage 5: Stay on PR branch
#
# No Python quality gates — this repo has no source code.
# Rules sync is automatic: any .cursor/rules/ changes you made locally
# are captured and included in the commit without extra steps.
#
# Prerequisites:
#   - gh CLI installed and authenticated
#   - Auto-merge enabled on this repo (Settings > General > Allow auto-merge)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PM_ROOT="$REPO_ROOT"
WORKSPACE_ROOT="$(cd "$REPO_ROOT/.." && pwd)"

# shellcheck source=./_workspace-lib.sh
source "$SCRIPT_DIR/_workspace-lib.sh"

log()  { echo "${BOLD}[unified-trading-pm]${NC} $*"; }
ok()   { echo "${GREEN}✓${NC} $*"; }
warn() { echo "${YELLOW}⚠${NC}  $*"; }
fail() { echo "${RED}✗${NC} $*" >&2; exit 1; }

# ── Validate workspace structure first ───────────────────────────────────────
echo ""
validate_workspace_structure || exit 1
echo ""

# ── Parse arguments ───────────────────────────────────────────────────────────
COMMIT_MSG="chore: update workspace tooling"
FILES_ARG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --files) FILES_ARG="$2"; shift 2 ;;
        --no-sync) NO_SYNC=true; shift ;;
        *) COMMIT_MSG="$1"; shift ;;
    esac
done

NO_SYNC="${NO_SYNC:-false}"

# ── Stage 0: Auto-sync cursor rules and configs ───────────────────────────────
if [ "$NO_SYNC" = false ]; then
    log "Stage 0: Syncing .cursor/rules/ → cursor-rules/ ..."

    CURSOR_RULES_SRC="$WORKSPACE_ROOT/.cursor/rules"
    CURSOR_RULES_DST="$REPO_ROOT/cursor-rules"
    CURSOR_CONFIGS_DST="$REPO_ROOT/cursor-configs"

    if [ -d "$CURSOR_RULES_SRC" ]; then
        mkdir -p "$CURSOR_RULES_DST"
        cp -r "$CURSOR_RULES_SRC"/. "$CURSOR_RULES_DST/"
        ok "Synced $(ls "$CURSOR_RULES_DST" | wc -l | tr -d ' ') rules"
    else
        warn ".cursor/rules/ not found at $CURSOR_RULES_SRC — skipping rules sync"
    fi

    # Sync .cursorrules
    if [ -f "$WORKSPACE_ROOT/.cursorrules" ]; then
        mkdir -p "$CURSOR_CONFIGS_DST"
        cp "$WORKSPACE_ROOT/.cursorrules" "$CURSOR_CONFIGS_DST/cursorrules"
        ok "Synced .cursorrules"
    fi

    # Sync workspace .code-workspace files
    WORKSPACE_CONFIGS_SRC="$WORKSPACE_ROOT/.cursor/workspace-configs"
    if [ -d "$WORKSPACE_CONFIGS_SRC" ]; then
        mkdir -p "$CURSOR_CONFIGS_DST"
        cp "$WORKSPACE_CONFIGS_SRC"/*.code-workspace "$CURSOR_CONFIGS_DST/" 2>/dev/null || true
    fi
    # Also sync root-level .code-workspace files
    find "$WORKSPACE_ROOT" -maxdepth 1 -name "*.code-workspace" -exec cp {} "$CURSOR_CONFIGS_DST/" \; 2>/dev/null || true

    # Update .last-sync timestamp
    date -u +"%Y-%m-%dT%H:%M:%SZ" > "$REPO_ROOT/.last-sync"
fi

# ── Stage 1: Validate workspace-manifest.json ────────────────────────────────
log "Stage 1: Validating workspace-manifest.json ..."
if [ -f "$REPO_ROOT/workspace-manifest.json" ]; then
    if python3 -c "import json; json.load(open('$REPO_ROOT/workspace-manifest.json'))" 2>/dev/null; then
        ok "workspace-manifest.json is valid JSON"
    else
        fail "workspace-manifest.json has invalid JSON — fix before committing"
    fi
else
    warn "workspace-manifest.json not found — skipping validation"
fi

# ── Stage 2: Stash + create branch from origin/main ──────────────────────────
cd "$REPO_ROOT"

log "Stage 2: Creating branch from origin/main ..."

# Check for uncommitted changes
if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then
    git stash push --include-untracked -m "quickmerge: $COMMIT_MSG" 2>/dev/null || true
    STASHED=true
else
    STASHED=false
fi

# Fetch latest
git fetch origin main --quiet 2>/dev/null || warn "Could not fetch origin/main — working from local"

# Create branch from origin/main
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BRANCH="auto/${TIMESTAMP}-pm"
git checkout -b "$BRANCH" origin/main 2>/dev/null || git checkout -b "$BRANCH" 2>/dev/null

ok "Branch: $BRANCH"

# ── Stage 3: Restore, stage, commit ──────────────────────────────────────────
log "Stage 3: Staging and committing ..."

if [ "$STASHED" = true ]; then
    git stash pop 2>/dev/null || warn "Stash pop failed — changes may already be present"
fi

if [ -n "$FILES_ARG" ]; then
    # shellcheck disable=SC2086
    git add $FILES_ARG
else
    git add -A
fi

# Check if there's anything to commit
if git diff --cached --quiet; then
    warn "Nothing to commit — no changes staged"
    git checkout - 2>/dev/null || true
    exit 0
fi

git commit -m "$COMMIT_MSG"
ok "Committed: $COMMIT_MSG"

# ── Stage 4: Push + PR with auto-merge ───────────────────────────────────────
log "Stage 4: Pushing and creating PR ..."

git push -u origin "$BRANCH"

PR_URL=$(gh pr create \
    --title "$COMMIT_MSG" \
    --body "Automated PR from quickmerge. Includes cursor rules sync if rules were changed." \
    --base main \
    2>&1 | grep "https://" || echo "")

if [ -n "$PR_URL" ]; then
    gh pr merge --auto --squash "$PR_URL" 2>/dev/null || warn "Could not enable auto-merge (check repo settings)"
    ok "PR created: $PR_URL"
else
    warn "PR creation failed or already exists — check gh pr list"
fi

# ── Stage 5: Stay on branch ───────────────────────────────────────────────────
log "Stage 5: Done. Staying on branch $BRANCH"
echo ""
echo "${GREEN}✓ quickmerge complete${NC}"
echo "  Branch:  $BRANCH"
echo "  Commit:  $COMMIT_MSG"
[ -n "$PR_URL" ] && echo "  PR:      $PR_URL"
echo ""
echo "Rules sync: local .cursor/rules/ → cursor-rules/ captured in this commit"
echo "Team pull:  cd unified-trading-pm && git pull && ./scripts/sync-rules-pull.sh"
