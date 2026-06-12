#!/usr/bin/env bash
# _workspace-lib.sh — shared helpers for unified-trading-pm scripts
# Source this file: source "$(dirname "${BASH_SOURCE[0]}")/_workspace-lib.sh"
# Do NOT execute directly.

# ── Colors ────────────────────────────────────────────────────────────────────
if command -v tput >/dev/null 2>&1 && [ -t 1 ]; then
  RED=$(tput setaf 1)
  GREEN=$(tput setaf 2)
  YELLOW=$(tput setaf 3)
  BOLD=$(tput bold)
  NC=$(tput sgr0)
else
  RED=""
  GREEN=""
  YELLOW=""
  BOLD=""
  NC=""
fi
export RED GREEN YELLOW BOLD NC

# ── Path resolution ───────────────────────────────────────────────────────────
# Every script that sources this sets SCRIPT_DIR before sourcing.
# PM_ROOT  = unified-trading-pm/ directory
# WORKSPACE_ROOT = parent directory containing all repos as siblings

_lib_script_dir() { cd "$(dirname "${BASH_SOURCE[1]}")" && pwd; }

# Callers set these themselves (adjust ../ depth based on subdirectory):
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"   # from scripts/subdir/
#   WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"

# ── Workspace structure validation ───────────────────────────────────────────
# Required structure:
#
#   <WORKSPACE_ROOT>/                 ← e.g. ~/repos/unified-trading-system-repos/
#   ├── .cursor/
#   │   └── rules/                    ← local working copy (IDE reads here)
#   ├── .cursorrules                  ← workspace-level Cursor config
#   ├── unified-trading-pm/           ← THIS repo (must be a sibling, not the root)
#   │   ├── .cursor/rules/            ← git-tracked source of truth
#   │   ├── cursor-configs/
#   │   ├── scripts/
#   │   └── workspace-manifest.json
#   └── <other repos>/                 (unified-trading-codex is ARCHIVED — folded into PM at codex/)

KNOWN_SIBLING_REPOS=("instruments-service" "unified-trading-library" "deployment-service")

validate_workspace_structure() {
  local errors=0

  echo "${BOLD}Validating workspace structure...${NC}"

  # 1. PM_ROOT must not equal WORKSPACE_ROOT
  if [ "$PM_ROOT" = "$WORKSPACE_ROOT" ]; then
    echo "${RED}✗ ERROR: unified-trading-pm appears to BE the workspace root.${NC}" >&2
    echo "  Expected: unified-trading-pm/ is a subdirectory inside the workspace root." >&2
    echo "  Got:      PM_ROOT=$PM_ROOT" >&2
    echo "" >&2
    echo "  Required structure:" >&2
    echo "    ~/repos/unified-trading-system-repos/   ← workspace root" >&2
    echo "    ├── unified-trading-pm/                 ← this repo" >&2
    echo "    ├── unified-trading-codex/" >&2
    echo "    └── instruments-service/ ..." >&2
    ((errors++))
  fi

  # 2. WORKSPACE_ROOT must have .cursor/ directory
  if [ ! -d "$WORKSPACE_ROOT/.cursor" ]; then
    echo "${RED}✗ ERROR: No .cursor/ directory found at workspace root.${NC}" >&2
    echo "  Expected: $WORKSPACE_ROOT/.cursor/" >&2
    echo "  Fix: Open your workspace root in Cursor IDE at least once, or create it:" >&2
    echo "       mkdir -p '$WORKSPACE_ROOT/.cursor/rules'" >&2
    ((errors++))
  fi

  # 3. .cursor/rules/ must exist (symlink to .cursor/rules/)
  if [ -L "$WORKSPACE_ROOT/.cursor/rules" ]; then
    # Symlink — verify it points to the right place
    local rules_target
    rules_target="$(readlink "$WORKSPACE_ROOT/.cursor/rules")"
    if [ ! -d "$WORKSPACE_ROOT/.cursor/rules" ]; then
      echo "${RED}✗ ERROR: .cursor/rules symlink is broken (target: $rules_target)${NC}" >&2
      echo "  Fix: bash unified-trading-pm/scripts/workspace/setup-cursor-rules-symlink.sh" >&2
      ((errors++))
    fi
  elif [ -d "$WORKSPACE_ROOT/.cursor/rules" ]; then
    echo "${YELLOW}⚠  WARNING: .cursor/rules/ is a directory, not a symlink.${NC}" >&2
    echo "  Run: bash unified-trading-pm/scripts/workspace/setup-cursor-rules-symlink.sh" >&2
    echo "  This will migrate to a symlink (edits go directly to git-tracked source)." >&2
  elif [ ! -e "$WORKSPACE_ROOT/.cursor/rules" ]; then
    echo "${YELLOW}⚠  WARNING: .cursor/rules/ does not exist.${NC}" >&2
    echo "  Fix: bash unified-trading-pm/scripts/workspace/setup-cursor-rules-symlink.sh" >&2
  fi

  # 4. unified-trading-pm must be a git repo
  if [ ! -d "$PM_ROOT/.git" ]; then
    echo "${RED}✗ ERROR: unified-trading-pm/ is not a git repository.${NC}" >&2
    echo "  Expected: $PM_ROOT/.git to exist" >&2
    echo "  Fix: git init '$PM_ROOT' && git remote add origin <url>" >&2
    ((errors++))
  fi

  # 5. At least one known sibling repo must exist
  local found_sibling=false
  for repo in "${KNOWN_SIBLING_REPOS[@]}"; do
    if [ -d "$WORKSPACE_ROOT/$repo" ]; then
      found_sibling=true
      break
    fi
  done
  if [ "$found_sibling" = false ]; then
    echo "${RED}✗ ERROR: No known sibling repos found at workspace root.${NC}" >&2
    echo "  Expected one of: ${KNOWN_SIBLING_REPOS[*]}" >&2
    echo "  Looked in: $WORKSPACE_ROOT" >&2
    echo "" >&2
    echo "  Is unified-trading-pm/ cloned into the right parent directory?" >&2
    echo "  Required sibling layout:" >&2
    echo "    $WORKSPACE_ROOT/" >&2
    echo "    ├── unified-trading-pm/     ← you are here" >&2
    echo "    ├── unified-trading-codex/" >&2
    echo "    ├── instruments-service/" >&2
    echo "    └── ... (other repos)" >&2
    ((errors++))
  fi

  # 6. cursor-rules/ must exist in PM repo (for pull)
  if [ ! -d "$PM_ROOT/.cursor/rules" ]; then
    echo "${YELLOW}⚠  WARNING: $PM_ROOT/.cursor/rules/ does not exist.${NC}" >&2
    echo "  Run 'git pull' to fetch the latest rules from the remote." >&2
  fi

  if [ "$errors" -gt 0 ]; then
    echo "" >&2
    echo "${RED}${BOLD}Workspace structure is invalid ($errors error(s)). Aborting.${NC}" >&2
    echo "" >&2
    echo "See: unified-trading-codex/05-infrastructure/workspace-setup.md" >&2
    return 1
  fi

  echo "${GREEN}✓ Workspace structure OK${NC}"
  echo "  Workspace root: $WORKSPACE_ROOT"
  echo "  PM repo:        $PM_ROOT"
  local sibling_count
  sibling_count=$(ls -d "$WORKSPACE_ROOT"/*/ 2>/dev/null | wc -l | tr -d ' ')
  echo "  Sibling repos:  $sibling_count directories"
  return 0
}

# NOTE: Last-sync and rule diff helpers were removed when rules switched
# from copy-based sync to symlinks. See setup-cursor-rules-symlink.sh.
