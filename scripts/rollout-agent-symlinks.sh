#!/usr/bin/env bash
#
# rollout-agent-symlinks.sh — Commit cursor rules + CLAUDE.md + AGENTS.md symlinks to ALL repos
#
# For each repo in workspace-manifest.json (including UI repos), creates relative symlinks:
#   .cursor/rules         → ../../unified-trading-pm/cursor-rules/
#   .claude/CLAUDE.md     → ../../unified-trading-pm/cursor-configs/CLAUDE.md
#   .cursorrules          → ../unified-trading-pm/cursor-configs/cursorrules
#   AGENTS.md             → ../unified-trading-pm/AGENTS.md
#
# These relative symlinks work both locally (sibling repos) and in GHA (after PM is cloned).
# Enables autonomous Cursor agents and Claude Code agents to find rules/instructions in every repo.
#
# Usage:
#   bash scripts/rollout-agent-symlinks.sh [--dry-run] [--repo <name>] [--skip-commit]
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_DIR="$(dirname "$SCRIPT_DIR")"
WORKSPACE_ROOT="$(dirname "$PM_DIR")"
MANIFEST_PATH="$PM_DIR/workspace-manifest.json"

DRY_RUN=false
SKIP_COMMIT=false
FILTER_REPO=""
ARGS=("$@")

i=0
while [ $i -lt ${#ARGS[@]} ]; do
    case "${ARGS[$i]}" in
        --dry-run)     DRY_RUN=true ;;
        --skip-commit) SKIP_COMMIT=true ;;
        --repo)        i=$((i+1)); FILTER_REPO="${ARGS[$i]}" ;;
    esac
    i=$((i+1))
done

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Verify PM source files exist
PM_CURSOR_RULES="$PM_DIR/cursor-rules"
PM_CLAUDE_MD="$PM_DIR/cursor-configs/CLAUDE.md"
PM_CURSORRULES="$PM_DIR/cursor-configs/cursorrules"
PM_AGENTS_MD="$PM_DIR/AGENTS.md"

[ -d "$PM_CURSOR_RULES" ]   || { echo -e "${RED}❌ Missing: $PM_CURSOR_RULES${NC}" >&2; exit 1; }
[ -f "$PM_CLAUDE_MD" ]      || { echo -e "${RED}❌ Missing: $PM_CLAUDE_MD${NC}" >&2; exit 1; }
[ -f "$PM_CURSORRULES" ]    || { echo -e "${RED}❌ Missing: $PM_CURSORRULES${NC}" >&2; exit 1; }
[ -f "$PM_AGENTS_MD" ]      || { echo -e "${RED}❌ Missing: $PM_AGENTS_MD${NC}" >&2; exit 1; }

# Get all repos (all types including UI, excluding only PM itself)
get_all_repos() {
    python3 - "$MANIFEST_PATH" "$FILTER_REPO" <<'PYEOF'
import json, sys
manifest_path = sys.argv[1]
filter_repo   = sys.argv[2] if len(sys.argv) > 2 else ""
with open(manifest_path) as f:
    manifest = json.load(f)
repos = manifest.get("repositories", {})
SKIP_NAMES = {"unified-trading-pm"}
for name, data in repos.items():
    if filter_repo and name != filter_repo:
        continue
    if name in SKIP_NAMES:
        continue
    print(name)
PYEOF
}

# Create a relative symlink, replacing existing if different
ensure_symlink() {
    local link_path="$1"   # absolute path where symlink should live
    local target="$2"      # relative target (relative to symlink's parent dir)
    local dry_run="$3"

    local link_dir
    link_dir="$(dirname "$link_path")"

    # Check if already correct
    if [ -L "$link_path" ]; then
        existing_target=$(readlink "$link_path")
        if [ "$existing_target" = "$target" ]; then
            return 0  # already correct, nothing to do
        fi
        $dry_run && { echo "  DRY-RUN: update symlink $link_path -> $target (was: $existing_target)"; return 0; }
        rm "$link_path"
    elif [ -e "$link_path" ]; then
        $dry_run && { echo "  DRY-RUN: replace file with symlink $link_path -> $target"; return 0; }
        rm -rf "$link_path"
    else
        $dry_run && { echo "  DRY-RUN: create symlink $link_path -> $target"; return 0; }
    fi

    mkdir -p "$link_dir"
    ln -sfn "$target" "$link_path"
}

PASS=0; SKIP=0; FAIL=0
ALL_REPOS=$(get_all_repos)
TOTAL=$(echo "$ALL_REPOS" | grep -c . || true)

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Rollout: agent symlinks (cursor rules + CLAUDE.md + AGENTS.md)"
echo "  Repos:   $TOTAL targets (all types incl. UI)"
echo "  DRY_RUN: $DRY_RUN | SKIP_COMMIT: $SKIP_COMMIT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

while IFS= read -r repo; do
    [ -z "$repo" ] && continue

    repo_dir="$WORKSPACE_ROOT/$repo"
    if [ ! -d "$repo_dir" ]; then
        warn "$repo: not found at $repo_dir — skipping"
        SKIP=$((SKIP + 1))
        continue
    fi

    if $DRY_RUN; then
        echo "DRY-RUN: $repo"
        echo "  .cursor/rules -> ../../unified-trading-pm/cursor-rules/"
        echo "  .claude/CLAUDE.md -> ../../unified-trading-pm/cursor-configs/CLAUDE.md"
        echo "  .cursorrules -> ../unified-trading-pm/cursor-configs/cursorrules"
        echo "  AGENTS.md -> ../unified-trading-pm/AGENTS.md"
        PASS=$((PASS + 1))
        continue
    fi

    # ── CREATE SYMLINKS ────────────────────────────────────────────────────────
    # .cursor/rules  (relative: from .cursor/ dir, ../../unified-trading-pm/cursor-rules/)
    ensure_symlink "$repo_dir/.cursor/rules" "../../unified-trading-pm/cursor-rules/" false

    # .claude/CLAUDE.md  (relative: from .claude/ dir, ../../unified-trading-pm/cursor-configs/CLAUDE.md)
    ensure_symlink "$repo_dir/.claude/CLAUDE.md" "../../unified-trading-pm/cursor-configs/CLAUDE.md" false

    # .cursorrules  (relative: from repo root, ../unified-trading-pm/cursor-configs/cursorrules)
    ensure_symlink "$repo_dir/.cursorrules" "../unified-trading-pm/cursor-configs/cursorrules" false

    # AGENTS.md  (relative: from repo root, ../unified-trading-pm/AGENTS.md)
    ensure_symlink "$repo_dir/AGENTS.md" "../unified-trading-pm/AGENTS.md" false

    if $SKIP_COMMIT; then
        ok "$repo: symlinks created (no commit)"
        PASS=$((PASS + 1))
        continue
    fi

    # ── COMMIT ─────────────────────────────────────────────────────────────────
    (
        cd "$repo_dir"

        # Stage only the symlinks (not any other dirty state)
        git add \
            ".cursor/rules" \
            ".claude/CLAUDE.md" \
            ".cursorrules" \
            "AGENTS.md" \
            2>/dev/null || true

        if git diff --cached --quiet; then
            info "$repo: no changes to commit (symlinks already up-to-date)"
        else
            git commit -m "chore: add agent symlinks for cursor rules + CLAUDE.md + AGENTS.md

Relative symlinks so Cursor and Claude Code agents find workspace rules in every repo:
  .cursor/rules         -> ../../unified-trading-pm/cursor-rules/
  .claude/CLAUDE.md     -> ../../unified-trading-pm/cursor-configs/CLAUDE.md
  .cursorrules          -> ../unified-trading-pm/cursor-configs/cursorrules
  AGENTS.md             -> ../unified-trading-pm/AGENTS.md

Symlinks resolve after PM is cloned (via setup-workspace.sh or agent-audit.yml bootstrap).
Enables autonomous Cursor and Claude Code agents in all repos.

Auto-generated by scripts/rollout-agent-symlinks.sh"
            ok "$repo: committed symlinks"
        fi
    ) && PASS=$((PASS + 1)) || { warn "$repo: failed"; FAIL=$((FAIL + 1)); }

done <<< "$ALL_REPOS"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Rollout complete"
echo "  ✅ Updated: $PASS  |  ⏭  Skipped: $SKIP  |  ❌ Failed: $FAIL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

[ "$FAIL" -eq 0 ] || exit 1
