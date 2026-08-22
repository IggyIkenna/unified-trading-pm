#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# fix-per-repo-cursor-rules-symlinks.sh — Replace per-repo .cursor/rules copies with symlinks
#
# Per-repo .cursor/rules (real dirs with 108 .mdc files) cause context bloat when Cursor loads
# rules per workspace folder. Replacing them with symlinks to unified-trading-pm/.cursor/rules
# eliminates ~80K–100K tokens of duplicate rule content.
#
# Before replacing: compares per-repo rules with workspace rules. If identical, replaces directly.
# If different (repo has unique or modified rules), creates a backup first.
#
# Usage: bash unified-trading-pm/scripts/workspace/fix-per-repo-cursor-rules-symlinks.sh
#        bash .../fix-per-repo-cursor-rules-symlinks.sh --dry-run  # show what would happen

set -euo pipefail

DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TARGET_DIR="$WORKSPACE_ROOT/unified-trading-pm/.cursor/rules"

if [ ! -d "$TARGET_DIR" ]; then
    echo "[ERROR] Target directory not found: $TARGET_DIR"
    exit 1
fi

echo "[OK] Target: $TARGET_DIR"
$DRY_RUN && echo "[DRY-RUN] No changes will be made"
echo ""

fixed=0
skipped=0
backed_up=0

for repo in "$WORKSPACE_ROOT"/*/; do

    # PM repo is the source of truth — skip it
    [ -d "$repo" ] || continue
    repo_name="$(basename "$repo")"
    # PM repo is the source of truth — skip it
    if [[ "$repo_name" == "unified-trading-pm" ]]; then
        continue
    fi
    rules_path="$repo/.cursor/rules"

    if [ ! -e "$rules_path" ]; then
        continue
    fi

    if [ -L "$rules_path" ]; then
        current="$(readlink "$rules_path")"
        if [[ "$current" == *"unified-trading-pm/.cursor/rules"* ]] || [[ "$current" == *".cursor/rules" ]]; then
            echo "[SKIP] $repo_name — already symlinked"
            ((skipped++)) || true
            continue
        fi
        if ! $DRY_RUN; then
            rm "$rules_path"
        fi
        echo "[FIX] $repo_name — removed incorrect symlink"
        ((fixed++)) || true
        continue
    fi

    if [ -d "$rules_path" ] && [ ! -L "$rules_path" ]; then
        # Compare per-repo rules with workspace rules
        if diff -rq "$rules_path" "$TARGET_DIR" >/dev/null 2>&1; then
            echo "[SAME] $repo_name — identical to workspace rules, replacing"
        else
            backup_dir="$repo/.cursor/rules-backup-$(date +%Y%m%d-%H%M%S)"
            echo "[DIFF] $repo_name — rules differ from workspace; backing up to $(basename "$backup_dir")"
            if ! $DRY_RUN; then
                cp -a "$rules_path" "$backup_dir"
                ((backed_up++)) || true
            fi
        fi

        if ! $DRY_RUN; then
            rm -rf "$rules_path"
            mkdir -p "$(dirname "$rules_path")"
            ln -sf "../../unified-trading-pm/.cursor/rules" "$rules_path"
        fi
        echo "[FIX] $repo_name — replaced real dir with symlink"
        ((fixed++)) || true
    fi
done

echo ""
echo "Done. Fixed: $fixed, Skipped: $skipped, Backed up: $backed_up"
$DRY_RUN && echo "[DRY-RUN] Run without --dry-run to apply changes"
