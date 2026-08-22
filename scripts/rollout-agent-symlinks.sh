#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# rollout-agent-symlinks.sh — Commit CLAUDE.md + SUB_AGENT_MANDATORY_RULES.md symlinks to ALL repos
#
# For each repo in workspace-manifest.json (including UI repos), creates relative symlinks:
#   .claude/CLAUDE.md                    → ../../unified-trading-pm/cursor-configs/CLAUDE.md
#   .claude/SUB_AGENT_MANDATORY_RULES.md → ../../unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md
#   AGENTS.md: ephemeral — copied by setup-workspace, NOT symlinked
#
# NOTE: SUB_AGENT_MANDATORY_RULES.md in cursor-configs/ is itself a symlink to CLAUDE.md
# (single SSOT — sub-agents need everything CLAUDE.md has, no content duplication / drift).
# The per-repo .claude/SUB_AGENT_MANDATORY_RULES.md symlink resolves through both hops to
# CLAUDE.md content, so existing references like "read SUB_AGENT_MANDATORY_RULES.md" continue
# to work at the canonical path while delivering the full workspace-rules surface.
#
# NOTE: .cursor/rules and .cursorrules are intentionally NOT committed as symlinks.
# Committing them to every repo causes Cursor IDE to read 60+ rule sets simultaneously.
# Instead, setup-workspace-from-manifest.sh copies cursor rules as ephemeral real files
# during GHA runs, cleaned up before quickmerge. See scripts/setup-workspace-from-manifest.sh.
#
# These relative symlinks work both locally (sibling repos) and in GHA (after PM is cloned).
# Enables autonomous Claude Code agents and Codex runners to find instructions in every repo.
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
PM_CLAUDE_MD="$PM_DIR/cursor-configs/CLAUDE.md"
PM_CHECK_IMPORT="$PM_DIR/scripts/validation/check-import-patterns.py"

[ -f "$PM_CLAUDE_MD" ]       || { echo -e "${RED}❌ Missing: $PM_CLAUDE_MD${NC}" >&2; exit 1; }
[ -f "$PM_CHECK_IMPORT" ]    || { echo -e "${RED}❌ Missing: $PM_CHECK_IMPORT${NC}" >&2; exit 1; }

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
echo "  Rollout: CLAUDE.md + check-import-patterns.py symlinks (AGENTS.md + cursor rules = ephemeral)"
echo "  Repos:   $TOTAL targets (all types incl. UI; check-import-patterns.py: Python repos only)"
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

    # Detect Python repos (have pyproject.toml)
    _is_python_repo=false
    [ -f "$repo_dir/pyproject.toml" ] && _is_python_repo=true

    if $DRY_RUN; then
        echo "DRY-RUN: $repo"
        echo "  .claude/CLAUDE.md -> ../../unified-trading-pm/cursor-configs/CLAUDE.md"
        echo "  .claude/SUB_AGENT_MANDATORY_RULES.md -> ../../unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md"
        $_is_python_repo && echo "  .cursor/scripts/check-import-patterns.py -> ../../../unified-trading-pm/scripts/validation/check-import-patterns.py"
        echo "  (cursor rules: ephemeral copy at GHA runtime, NOT committed)"
        PASS=$((PASS + 1))
        continue
    fi

    # ── CREATE SYMLINKS ────────────────────────────────────────────────────────
    # .claude/CLAUDE.md  (relative: from .claude/ dir → PM/cursor-configs/CLAUDE.md)
    ensure_symlink "$repo_dir/.claude/CLAUDE.md" "../../unified-trading-pm/cursor-configs/CLAUDE.md" false

    # .claude/SUB_AGENT_MANDATORY_RULES.md  (PM file is itself a symlink to CLAUDE.md;
    # this per-repo link resolves through both hops to CLAUDE.md content, so sub-agents
    # reading SUB_AGENT_MANDATORY_RULES.md at the canonical path get the full
    # workspace-rules surface without content duplication or drift).
    ensure_symlink "$repo_dir/.claude/SUB_AGENT_MANDATORY_RULES.md" "../../unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md" false

    # .cursor/scripts/check-import-patterns.py (Python repos only)
    # relative: from .cursor/scripts/ → ../../../unified-trading-pm/scripts/validation/check-import-patterns.py
    if $_is_python_repo; then
        ensure_symlink "$repo_dir/.cursor/scripts/check-import-patterns.py" \
            "../../../unified-trading-pm/scripts/validation/check-import-patterns.py" false
    fi


    # Remove any previously committed cursor rules symlinks (if accidentally added before)
    _remove_cursor_symlinks=false
    if [ -L "$repo_dir/.cursor/rules" ] || [ -L "$repo_dir/.cursorrules" ]; then
        rm -f "$repo_dir/.cursor/rules" "$repo_dir/.cursorrules"
        _remove_cursor_symlinks=true
    fi

    # Remove AGENTS.md from repo — it is ephemeral (copied by setup-workspace, not committed)
    _remove_agents_md=false
    if [ -e "$repo_dir/AGENTS.md" ]; then
        rm -f "$repo_dir/AGENTS.md"
        _remove_agents_md=true
    fi

    if $SKIP_COMMIT; then
        ok "$repo: symlinks set (no commit)"
        PASS=$((PASS + 1))
        continue
    fi

    # ── COMMIT ─────────────────────────────────────────────────────────────────
    (
        cd "$repo_dir"

        git add ".claude/CLAUDE.md" ".claude/SUB_AGENT_MANDATORY_RULES.md" 2>/dev/null || true
        # Stage check-import-patterns.py symlink for Python repos
        $_is_python_repo && git add ".cursor/scripts/check-import-patterns.py" 2>/dev/null || true
        # If cursor rule symlinks were removed, stage their deletion
        $_remove_cursor_symlinks && git rm --cached ".cursor/rules" ".cursorrules" 2>/dev/null || true
        $_remove_agents_md && git rm --cached "AGENTS.md" 2>/dev/null || true

        if git diff --cached --quiet; then
            info "$repo: no changes to commit"
        else
            git commit -m "chore: add CLAUDE.md + check-import-patterns.py symlinks; AGENTS.md + cursor rules ephemeral

Committed symlinks for Claude Code + agent runners:
  .claude/CLAUDE.md -> ../../unified-trading-pm/cursor-configs/CLAUDE.md
  .cursor/scripts/check-import-patterns.py -> ../../../unified-trading-pm/scripts/validation/check-import-patterns.py (Python repos only)

AGENTS.md and cursor rules (.cursor/rules, .cursorrules) are NOT committed —
they are copied as real files ephemerally by setup-workspace-from-manifest.sh
during GHA runs. This prevents Cursor IDE from reading 60+ rule sets at once.

Auto-generated by scripts/rollout-agent-symlinks.sh"
            ok "$repo: committed"
        fi
    ) && PASS=$((PASS + 1)) || { warn "$repo: failed"; FAIL=$((FAIL + 1)); }

done <<< "$ALL_REPOS"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Rollout complete"
echo "  ✅ Updated: $PASS  |  ⏭  Skipped: $SKIP  |  ❌ Failed: $FAIL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

[ "$FAIL" -eq 0 ] || exit 1
