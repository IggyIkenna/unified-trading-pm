#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# sync-workspace-venv.sh — Refresh .venv-workspace after version alignment.
#
# SSOT: unified-trading-pm/scripts/workspace/sync-workspace-venv.sh
# Wraps: unified-trading-pm/scripts/setup-workspace-venv.sh (full idempotent venv setup)
#
# Run this after:
#   - git pull on unified-trading-pm (version alignment bumped repo deps)
#   - run-version-alignment.sh (cascade updated downstream repos)
#   - Adding a new repo to workspace-manifest.json
#   - Any change to a repo's pyproject.toml that affects the union of workspace deps
#
# Usage:
#   bash unified-trading-pm/scripts/workspace/sync-workspace-venv.sh          # Refresh (idempotent)
#   bash unified-trading-pm/scripts/workspace/sync-workspace-venv.sh --check  # Verify only
#   bash unified-trading-pm/scripts/workspace/sync-workspace-venv.sh --force  # Full recreate from scratch
#
# Pinned versions enforced:
#   ruff         == 0.15.0  (workspace + per-repo; QG templates check this)
#   basedpyright == 1.38.2   (workspace IDE only; QG resolves from per-repo .venv)
#
# Environment model (SSOT — see quality-gates.md § Tool Version Pinning):
#   .venv-workspace  IDE cross-repo IntelliSense + ruff linting only
#                    NEVER used as PYTHON_CMD or BASEDPYRIGHT_CMD in QG checks.
#   .venv (per-repo) QG Python, basedpyright, pytest — CI-faithful, strict isolation.
#
# This script is NOT a substitute for workspace-bootstrap.sh (new machine setup).
# workspace-bootstrap.sh: fresh machine → clone all repos + system deps + this script.
# sync-workspace-venv.sh: day-to-day refresh after version alignment.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SETUP_SCRIPT="$PM_ROOT/scripts/setup-workspace-venv.sh"

RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  sync-workspace-venv.sh — refresh .venv-workspace${NC}"
echo -e "${BLUE}  ruff==0.15.0  basedpyright==1.38.2${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ ! -f "$SETUP_SCRIPT" ]; then
    echo -e "${RED}ERROR: setup-workspace-venv.sh not found at $SETUP_SCRIPT${NC}"
    exit 1
fi

# Delegate entirely to setup-workspace-venv.sh — it is idempotent, handles
# create/reinstall, and reads workspace-manifest.json for editable installs.
exec bash "$SETUP_SCRIPT" "$@"
