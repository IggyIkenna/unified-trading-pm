#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# setup-workspace-root.sh — Portable workspace root configuration
# Works on macOS and Linux with bash/zsh
# Sets UNIFIED_TRADING_WORKSPACE_ROOT and updates all Cursor workspace configs
#
# Usage:
#   bash setup-workspace-root.sh                    # Interactive prompt
#   bash setup-workspace-root.sh /path/to/workspace # Direct path

set -euo pipefail

# ── Colors ────────────────────────────────────────────────────────────────────
if command -v tput >/dev/null 2>&1 && [ -t 1 ]; then
  RED=$(tput setaf 1)
  GREEN=$(tput setaf 2)
  YELLOW=$(tput setaf 3)
  CYAN=$(tput setaf 6)
  BOLD=$(tput bold)
  NC=$(tput sgr0)
else
  RED=""
  GREEN=""
  YELLOW=""
  CYAN=""
  BOLD=""
  NC=""
fi

# ── Helper functions ──────────────────────────────────────────────────────────
log_info() { echo "${CYAN}ℹ${NC} $*"; }
log_success() { echo "${GREEN}✅${NC} $*"; }
log_warning() { echo "${YELLOW}⚠${NC} $*"; }
log_error() { echo "${RED}✗${NC} $*" >&2; }

die() {
  log_error "$*"
  exit 1
}

# ── Detect OS and shell ────────────────────────────────────────────────────────
detect_shell_config() {
  # Detect which shell and config file to use
  local shell_name
  if [ -n "${ZSH_VERSION:-}" ]; then
    shell_name="zsh"
    echo "$HOME/.zshrc"
  elif [ -n "${BASH_VERSION:-}" ]; then
    shell_name="bash"
    if [[ "$OSTYPE" == "darwin"* ]]; then
      # macOS bash uses .bash_profile
      echo "$HOME/.bash_profile"
    else
      # Linux bash uses .bashrc
      echo "$HOME/.bashrc"
    fi
  else
    # Try to detect from SHELL env var
    case "$SHELL" in
      */zsh) echo "$HOME/.zshrc" ;;
      */bash)
        if [[ "$OSTYPE" == "darwin"* ]]; then
          echo "$HOME/.bash_profile"
        else
          echo "$HOME/.bashrc"
        fi
        ;;
      *) die "Unsupported shell: $SHELL (only bash/zsh supported)" ;;
    esac
  fi
}

# ── Get workspace root ────────────────────────────────────────────────────────
get_workspace_root() {
  local provided_path="$1"
  local detected_root

  if [ -n "$provided_path" ]; then
    # Path provided as argument
    if [ ! -d "$provided_path" ]; then
      die "Provided path does not exist: $provided_path"
    fi
    echo "$provided_path"
    return
  fi

  # Try to detect from script location
  # This script is in: <repos-parent>/unified-trading-system-repos/unified-trading-pm/scripts/workspace/
  # We want the parent of unified-trading-system-repos/ (4 levels up)
  detected_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"

  log_info "Detected workspace root: ${BOLD}${detected_root}${NC}"
  echo ""
  echo "Common paths:"
  echo "  • Current Mac (iCloud):     /Users/$(whoami)/Documents/Documents - Mac/repos"
  echo "  • Other laptop:             /Users/$(whoami)/Documents/Documents - MacOld/repos"
  echo "  • Linux:                    /home/$(whoami)/repos"
  echo "  • Before iCloud:            /Users/$(whoami)/Documents/repos"
  echo ""

  read -r -p "Enter workspace root path [${detected_root}]: " input_path

  if [ -z "$input_path" ]; then
    echo "$detected_root"
  else
    # Expand ~ if present
    input_path="${input_path/#\~/$HOME}"
    if [ ! -d "$input_path" ]; then
      die "Path does not exist: $input_path"
    fi
    echo "$input_path"
  fi
}

# ── Update shell config ────────────────────────────────────────────────────────
update_shell_config() {
  local workspace_root="$1"
  local shell_config="$2"

  log_info "Updating shell configuration: ${BOLD}${shell_config}${NC}"

  # Check if variable already exists
  if [ -f "$shell_config" ] && grep -q "^export UNIFIED_TRADING_WORKSPACE_ROOT=" "$shell_config"; then
    log_warning "UNIFIED_TRADING_WORKSPACE_ROOT already exists in ${shell_config}"
    read -r -p "Update it? [y/N]: " update_choice
    if [[ ! "$update_choice" =~ ^[Yy]$ ]]; then
      log_info "Skipping shell config update"
      return
    fi

    # Update existing line (works on both macOS and Linux)
    if [[ "$OSTYPE" == "darwin"* ]]; then
      # macOS sed
      sed -i '' "s|^export UNIFIED_TRADING_WORKSPACE_ROOT=.*|export UNIFIED_TRADING_WORKSPACE_ROOT=\"${workspace_root}\"|" "$shell_config"
    else
      # GNU sed
      sed -i "s|^export UNIFIED_TRADING_WORKSPACE_ROOT=.*|export UNIFIED_TRADING_WORKSPACE_ROOT=\"${workspace_root}\"|" "$shell_config"
    fi
    log_success "Updated existing variable"
  else
    # Append new variable
    cat >>"$shell_config" <<EOF

# ===== Unified Trading System Workspace Root =====
# Auto-configured by unified-trading-pm/scripts/setup-workspace-root.sh
# Change this path when switching machines:
# - iCloud Mac: /Users/$(whoami)/Documents/Documents - Mac/repos
# - Other laptop: /Users/$(whoami)/Documents/Documents - MacOld/repos
# - Linux: /home/$(whoami)/repos
export UNIFIED_TRADING_WORKSPACE_ROOT="${workspace_root}"
EOF
    log_success "Added UNIFIED_TRADING_WORKSPACE_ROOT to ${shell_config}"
  fi
}

# ── Update workspace configs ──────────────────────────────────────────────────
update_workspace_configs() {
  local workspace_root="$1"
  local configs_dir="${workspace_root}/unified-trading-system-repos/.cursor/workspace-configs"

  if [ ! -d "$configs_dir" ]; then
    log_warning "Workspace configs directory not found: ${configs_dir}"
    return
  fi

  log_info "Updating Cursor workspace configurations..."

  # Build old path patterns dynamically
  local old_patterns=()

  # If UNIFIED_TRADING_WORKSPACE_ROOT is set and differs, use it as an old path
  if [ -n "${UNIFIED_TRADING_WORKSPACE_ROOT:-}" ] && [ "$UNIFIED_TRADING_WORKSPACE_ROOT" != "$workspace_root" ]; then
    old_patterns+=("$UNIFIED_TRADING_WORKSPACE_ROOT")
  fi

  # Scan config files for any path that ends with the workspace dir name
  # and differs from the new workspace_root
  local ws_dirname
  ws_dirname="$(basename "$workspace_root")"
  for config_file in "$configs_dir"/*.code-workspace; do
    [ -f "$config_file" ] || continue
    # Extract unique path prefixes that reference the workspace dirname
    while IFS= read -r found_path; do
      # Normalize: strip trailing slash and workspace dirname suffix to get the parent
      local candidate="${found_path%/}"
      if [ "$candidate" != "$workspace_root" ] && [ -n "$candidate" ]; then
        # Check it's not already in old_patterns
        local already=false
        for existing in "${old_patterns[@]+"${old_patterns[@]}"}"; do
          if [ "$existing" = "$candidate" ]; then
            already=true
            break
          fi
        done
        if [ "$already" = false ]; then
          old_patterns+=("$candidate")
        fi
      fi
    done < <(grep -oE '[^"]*'"$ws_dirname"'[^"]*' "$config_file" 2>/dev/null \
      | sed "s|/${ws_dirname}.*|/${ws_dirname}|" \
      | sort -u)
  done

  if [ ${#old_patterns[@]} -eq 0 ]; then
    log_info "No workspace configs needed updating (no stale paths found)"
    return
  fi

  local updated_count=0
  for config_file in "$configs_dir"/*.code-workspace; do
    if [ ! -f "$config_file" ]; then
      continue
    fi

    local file_updated=false
    for old_path in "${old_patterns[@]}"; do
      if grep -q "$old_path" "$config_file" 2>/dev/null; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
          # macOS sed
          sed -i '' "s|${old_path}|${workspace_root}|g" "$config_file"
        else
          # GNU sed
          sed -i "s|${old_path}|${workspace_root}|g" "$config_file"
        fi
        file_updated=true
      fi
    done

    if [ "$file_updated" = true ]; then
      ((updated_count++))
      log_success "Updated: $(basename "$config_file")"
    fi
  done

  if [ $updated_count -eq 0 ]; then
    log_info "No workspace configs needed updating"
  else
    log_success "Updated ${updated_count} workspace configuration(s)"
  fi
}

# ── Update Claude Code ───────────────────────────────────────────────────────
update_claude_code() {
  local workspace_root="$1"

  local claude_dir="${HOME}/.claude"

  if [ ! -d "$claude_dir" ]; then
    log_info "Claude Code not installed (no ~/.claude directory)"
    return
  fi

  log_info "Updating Claude Code configuration..."

  # Create symlink for conversation history
  local projects_dir="${claude_dir}/projects"
  local old_path="-Users-${USER}-Documents-repos-unified-trading-system-repos"
  local new_path

  # Encode the new path for Claude's naming scheme
  if [[ "$workspace_root" == *"Documents - Mac"* ]]; then
    new_path="-Users-${USER}-Documents-Documents - Mac-repos-unified-trading-system-repos"
  elif [[ "$workspace_root" == *"Documents - MacOld"* ]]; then
    new_path="-Users-${USER}-Documents-Documents - MacOld-repos-unified-trading-system-repos"
  else
    # Default case
    new_path=$(echo "$workspace_root/unified-trading-system-repos" | sed 's|/|-|g')
  fi

  # Create symlink if old conversations exist and new path doesn't
  if [ -d "${projects_dir}/${old_path}" ] && [ ! -e "${projects_dir}/${new_path}" ]; then
    cd "$projects_dir" && ln -s "./${old_path}" "./${new_path}" 2>/dev/null
    if [ $? -eq 0 ]; then
      log_success "Created symlink for Claude Code conversation history"
    else
      log_warning "Could not create Claude Code symlink (may already exist)"
    fi
  fi

  # Update settings.json permissions
  local settings_file="${claude_dir}/settings.json"
  if [ -f "$settings_file" ]; then
    local workspace_repos="${workspace_root}/unified-trading-system-repos"
    # Escape spaces for the permission string
    local escaped_path
    escaped_path=$(echo "$workspace_repos" | sed 's/ /\\ /g')

    # Check if path already in settings
    if ! grep -q "$escaped_path" "$settings_file" 2>/dev/null; then
      # Use Python to safely add to JSON array (if python3 available)
      if command -v python3 >/dev/null 2>&1; then
        python3 <<EOF
import json
import sys

try:
    with open("$settings_file", "r") as f:
        data = json.load(f)

    if "permissions" not in data:
        data["permissions"] = {}
    if "allow" not in data["permissions"]:
        data["permissions"]["allow"] = []

    new_perm = "Bash(ls -d $escaped_path/unified-*/)"
    if new_perm not in data["permissions"]["allow"]:
        data["permissions"]["allow"].append(new_perm)

        with open("$settings_file", "w") as f:
            json.dump(data, f, indent=2)
        print("updated")
except Exception as e:
    print(f"error: {e}", file=sys.stderr)
    sys.exit(1)
EOF
        if [ $? -eq 0 ]; then
          log_success "Updated Claude Code permissions"
        else
          log_warning "Could not update Claude Code settings (manual update needed)"
        fi
      else
        log_warning "Python3 not found - manually add path to ${settings_file}"
      fi
    else
      log_info "Claude Code settings already include this path"
    fi
  fi
}

# ── Verify setup ──────────────────────────────────────────────────────────────
verify_setup() {
  local workspace_root="$1"

  log_info "Verifying setup..."

  # Check Python interpreter exists
  local python_path="${workspace_root}/unified-trading-system-repos/.venv-workspace/bin/python"
  if [ -f "$python_path" ] || [ -L "$python_path" ]; then
    local python_version
    python_version=$("$python_path" --version 2>&1)
    log_success "Python interpreter found: ${python_version}"
  else
    log_warning "Python interpreter not found: ${python_path}"
    log_warning "You may need to set up the workspace venv"
  fi

  # Check key repos exist
  local key_repos=(
    "unified-trading-pm"
    "unified-trading-library"
    "unified-config-interface"
  )

  local missing_repos=()
  for repo in "${key_repos[@]}"; do
    if [ ! -d "${workspace_root}/unified-trading-system-repos/${repo}" ]; then
      missing_repos+=("$repo")
    fi
  done

  if [ ${#missing_repos[@]} -eq 0 ]; then
    log_success "All key repos found"
  else
    log_warning "Missing repos: ${missing_repos[*]}"
  fi
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
  echo "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo "${BOLD}  Unified Trading System - Workspace Setup${NC}"
  echo "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""

  # Get workspace root
  local workspace_root
  workspace_root=$(get_workspace_root "${1:-}")

  # Verify it looks like a valid workspace
  if [ ! -d "${workspace_root}/unified-trading-system-repos" ]; then
    log_warning "Directory 'unified-trading-system-repos' not found in workspace root"
    read -r -p "Continue anyway? [y/N]: " continue_choice
    [[ "$continue_choice" =~ ^[Yy]$ ]] || die "Setup cancelled"
  fi

  echo ""
  log_info "Workspace root: ${BOLD}${workspace_root}${NC}"
  echo ""

  # Detect shell config
  local shell_config
  shell_config=$(detect_shell_config)
  log_info "Shell config: ${BOLD}${shell_config}${NC}"
  echo ""

  # Update shell config
  update_shell_config "$workspace_root" "$shell_config"
  echo ""

  # Update workspace configs
  update_workspace_configs "$workspace_root"
  echo ""

  # Update Claude Code
  update_claude_code "$workspace_root"
  echo ""

  # Verify setup
  verify_setup "$workspace_root"
  echo ""

  # Final instructions
  echo "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo "${BOLD}  Setup Complete!${NC}"
  echo "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
  echo "Next steps:"
  echo ""
  echo "1. Reload your shell configuration:"
  echo "   ${CYAN}source ${shell_config}${NC}"
  echo ""
  echo "2. Verify the variable is set:"
  echo "   ${CYAN}echo \$UNIFIED_TRADING_WORKSPACE_ROOT${NC}"
  echo ""
  echo "3. Restart Cursor IDE and Claude Code (Cmd+Q / Ctrl+Q, then reopen)"
  echo ""
  echo "4. (Optional) Set up workspace venv if not already done:"
  echo "   ${CYAN}bash ${workspace_root}/unified-trading-system-repos/.cursor/workspace-configs/setup-workspace-venv-complete.sh${NC}"
  echo ""

  log_info "Documentation: ${workspace_root}/unified-trading-pm/WORKSPACE_SETUP.md"
}

# Run main if not sourced
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  main "$@"
fi
