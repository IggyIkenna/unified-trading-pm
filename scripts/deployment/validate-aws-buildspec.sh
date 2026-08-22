#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# validate-aws-buildspec.sh — Validates buildspec.aws.yaml files against AWS CodeBuild expectations.
#
# Reads a buildspec.aws.yaml from a given repo, validates YAML syntax, checks
# required sections (version, phases, artifacts), and performs dry-run structural
# validation against AWS CodeBuild conventions.
#
# Usage:
#   bash scripts/deployment/validate-aws-buildspec.sh <REPO_PATH> [OPTIONS]
#   bash scripts/deployment/validate-aws-buildspec.sh --canary     # Run against canary repos
#
# Arguments:
#   REPO_PATH    Path to the repo directory containing buildspec.aws.yaml
#
# Options:
#   --canary           Run against canary repos (instruments-service, unified-cloud-interface, unified-trading-library)
#   --workspace ROOT   Workspace root (default: parent of this script's PM repo)
#   --strict           Treat warnings as errors
#   --quiet            Suppress informational output
#
# Exit codes:
#   0 = all validations passed
#   1 = one or more validations failed
#   2 = usage error or missing dependencies

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# ── Defaults ──────────────────────────────────────────────────────────────────

CANARY_MODE=false
WORKSPACE_ROOT=""
STRICT=false
QUIET=false
REPO_PATHS=()
TOTAL_ERRORS=0
TOTAL_WARNINGS=0
TOTAL_REPOS=0
TOTAL_PASSED=0

# Canary repos — representative of service, library, and event bus patterns
CANARY_REPOS="instruments-service unified-cloud-interface unified-trading-library"

# ── Parse arguments ──────────────────────────────────────────────────────────

while [ $# -gt 0 ]; do
  case "$1" in
    --canary)    CANARY_MODE=true; shift ;;
    --workspace) WORKSPACE_ROOT="$2"; shift 2 ;;
    --strict)    STRICT=true; shift ;;
    --quiet)     QUIET=false; shift ;;
    --help|-h)
      head -30 "$0" | tail -28
      exit 0
      ;;
    *)
      REPO_PATHS+=("$1")
      shift
      ;;
  esac
done

# Determine workspace root
if [ -z "$WORKSPACE_ROOT" ]; then
  WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"
fi

# Resolve repo paths
if [ "$CANARY_MODE" = "true" ]; then
  for repo in $CANARY_REPOS; do
    REPO_PATHS+=("$WORKSPACE_ROOT/$repo")
  done
fi

if [ ${#REPO_PATHS[@]} -eq 0 ]; then
  echo "ERROR: No repo path specified. Use --canary or provide a repo path."
  echo "Usage: bash $0 <REPO_PATH> [--strict] [--workspace ROOT]"
  echo "       bash $0 --canary [--strict] [--workspace ROOT]"
  exit 2
fi

# ── Dependency check ─────────────────────────────────────────────────────────

check_yaml_tool() {
  if command -v python3 &>/dev/null; then
    # Check if PyYAML is available
    if python3 -c "import yaml" 2>/dev/null; then
      echo "python3"
      return 0
    fi
  fi
  if command -v yq &>/dev/null; then
    echo "yq"
    return 0
  fi
  echo ""
  return 1
}

YAML_TOOL=$(check_yaml_tool) || true
if [ -z "$YAML_TOOL" ]; then
  echo "ERROR: No YAML parser found. Install PyYAML (pip install pyyaml) or yq."
  exit 2
fi

# ── Helper functions ─────────────────────────────────────────────────────────

log() {
  if [ "$QUIET" = "false" ]; then
    echo "$@"
  fi
}

log_error() {
  echo "  ERROR: $*" >&2
}

log_warn() {
  echo "  WARN:  $*"
}

log_ok() {
  log "  OK:    $*"
}

# Validate YAML syntax using python3+PyYAML
validate_yaml_syntax() {
  local file="$1"

  if [ "$YAML_TOOL" = "python3" ]; then
    if python3 -c "
import yaml, sys
try:
    with open('$file') as f:
        yaml.safe_load(f)
    sys.exit(0)
except yaml.YAMLError as e:
    print(f'YAML syntax error: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/tmp/yaml_err.txt; then
      return 0
    else
      cat /tmp/yaml_err.txt >&2
      return 1
    fi
  elif [ "$YAML_TOOL" = "yq" ]; then
    if yq eval '.' "$file" > /dev/null 2>/tmp/yaml_err.txt; then
      return 0
    else
      cat /tmp/yaml_err.txt >&2
      return 1
    fi
  fi
}

# Extract a top-level YAML key's value using python3
yaml_has_key() {
  local file="$1"
  local key="$2"

  python3 -c "
import yaml, sys
with open('$file') as f:
    doc = yaml.safe_load(f)
if doc is None:
    sys.exit(1)
if '$key' in doc:
    sys.exit(0)
else:
    sys.exit(1)
" 2>/dev/null
}

# Extract nested value
yaml_get() {
  local file="$1"
  local keys="$2"  # dot-separated path like "phases.build"

  python3 -c "
import yaml, sys
with open('$file') as f:
    doc = yaml.safe_load(f)
keys = '$keys'.split('.')
val = doc
for k in keys:
    if isinstance(val, dict) and k in val:
        val = val[k]
    else:
        sys.exit(1)
print(val if not isinstance(val, (dict, list)) else type(val).__name__)
sys.exit(0)
" 2>/dev/null
}

# Check if a phase exists
yaml_has_phase() {
  local file="$1"
  local phase="$2"

  python3 -c "
import yaml, sys
with open('$file') as f:
    doc = yaml.safe_load(f)
phases = doc.get('phases', {})
if phases and '$phase' in phases:
    sys.exit(0)
sys.exit(1)
" 2>/dev/null
}

# Check if a phase has commands
yaml_phase_has_commands() {
  local file="$1"
  local phase="$2"

  python3 -c "
import yaml, sys
with open('$file') as f:
    doc = yaml.safe_load(f)
phases = doc.get('phases', {})
phase_data = phases.get('$phase', {})
if phase_data and 'commands' in phase_data:
    cmds = phase_data['commands']
    if isinstance(cmds, list) and len(cmds) > 0:
        sys.exit(0)
sys.exit(1)
" 2>/dev/null
}

# Get version value
yaml_get_version() {
  local file="$1"

  python3 -c "
import yaml, sys
with open('$file') as f:
    doc = yaml.safe_load(f)
v = doc.get('version')
if v is not None:
    print(v)
    sys.exit(0)
sys.exit(1)
" 2>/dev/null
}

# Check for anti-patterns in commands
check_antipatterns() {
  local file="$1"
  local errors=0
  local warnings=0

  # Check for pip install without uv (anti-pattern per project rules)
  # Note: `pip install uv` itself is acceptable in CodeBuild (bootstrapping uv)
  if grep -qE '^\s*-\s*(pip install (?!uv))' "$file" 2>/dev/null; then
    log_warn "Found 'pip install' without uv — prefer 'uv pip install'"
    warnings=$((warnings + 1))
  fi

  # Check for .[dev] extras (flat deps rule)
  if grep -qE '\.\[dev\]' "$file" 2>/dev/null; then
    log_warn "Found '.[dev]' extras — flat deps only (no optional-dependencies)"
    warnings=$((warnings + 1))
  fi

  # Check for pytest direct invocation (should use quality-gates.sh)
  # This is acceptable in CodeBuild context, just warn
  if grep -qE '^\s*-\s*pytest ' "$file" 2>/dev/null; then
    log_warn "Direct pytest invocation — consider using quality-gates.sh for consistency"
    warnings=$((warnings + 1))
  fi

  echo "$errors $warnings"
}

# ── Main validation loop ────────────────────────────────────────────────────

for REPO_PATH in "${REPO_PATHS[@]}"; do
  REPO_NAME=$(basename "$REPO_PATH")
  BUILDSPEC="$REPO_PATH/buildspec.aws.yaml"
  ERRORS=0
  WARNINGS=0

  TOTAL_REPOS=$((TOTAL_REPOS + 1))
  log ""
  log "=== Validating: $REPO_NAME ==="
  log "  File: $BUILDSPEC"

  # ── Check 1: File exists ───────────────────────────────────────────────

  if [ ! -f "$BUILDSPEC" ]; then
    log_error "buildspec.aws.yaml not found at $BUILDSPEC"
    TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
    continue
  fi

  log_ok "File exists"

  # ── Check 2: YAML syntax ──────────────────────────────────────────────

  if validate_yaml_syntax "$BUILDSPEC"; then
    log_ok "YAML syntax valid"
  else
    log_error "YAML syntax invalid"
    ERRORS=$((ERRORS + 1))
    # Cannot continue if YAML is broken
    TOTAL_ERRORS=$((TOTAL_ERRORS + ERRORS))
    continue
  fi

  # ── Check 3: Required top-level key: version ──────────────────────────

  if yaml_has_key "$BUILDSPEC" "version"; then
    VERSION_VAL=$(yaml_get_version "$BUILDSPEC")
    if [ "$VERSION_VAL" = "0.2" ]; then
      log_ok "version: 0.2 (current CodeBuild spec)"
    else
      log_warn "version: $VERSION_VAL (expected 0.2 — current CodeBuild spec version)"
      WARNINGS=$((WARNINGS + 1))
    fi
  else
    log_error "Missing required key: version"
    ERRORS=$((ERRORS + 1))
  fi

  # ── Check 4: Required top-level key: phases ───────────────────────────

  if yaml_has_key "$BUILDSPEC" "phases"; then
    log_ok "phases section present"

    # Check required phases: install, build
    for phase in install build; do
      if yaml_has_phase "$BUILDSPEC" "$phase"; then
        if yaml_phase_has_commands "$BUILDSPEC" "$phase"; then
          log_ok "phases.$phase has commands"
        else
          log_error "phases.$phase exists but has no commands"
          ERRORS=$((ERRORS + 1))
        fi
      else
        log_error "Missing required phase: $phase"
        ERRORS=$((ERRORS + 1))
      fi
    done

    # Optional but recommended phases
    for phase in pre_build post_build; do
      if yaml_has_phase "$BUILDSPEC" "$phase"; then
        log_ok "phases.$phase present (optional)"
      else
        log_warn "phases.$phase not present (recommended)"
        WARNINGS=$((WARNINGS + 1))
      fi
    done
  else
    log_error "Missing required key: phases"
    ERRORS=$((ERRORS + 1))
  fi

  # ── Check 5: artifacts section ────────────────────────────────────────

  if yaml_has_key "$BUILDSPEC" "artifacts"; then
    log_ok "artifacts section present"
  else
    log_warn "No artifacts section (CodeBuild may have no output artifacts)"
    WARNINGS=$((WARNINGS + 1))
  fi

  # ── Check 6: env section (recommended for CodeBuild) ──────────────────

  if yaml_has_key "$BUILDSPEC" "env"; then
    log_ok "env section present"
  else
    log_warn "No env section — consider defining variables or secrets-manager refs"
    WARNINGS=$((WARNINGS + 1))
  fi

  # ── Check 7: Anti-patterns ───────────────────────────────────────────

  AP_RESULT=$(check_antipatterns "$BUILDSPEC")
  AP_ERRORS=$(echo "$AP_RESULT" | cut -d' ' -f1)
  AP_WARNINGS=$(echo "$AP_RESULT" | cut -d' ' -f2)
  ERRORS=$((ERRORS + AP_ERRORS))
  WARNINGS=$((WARNINGS + AP_WARNINGS))

  # ── Check 8: cache section (recommended) ──────────────────────────────

  if yaml_has_key "$BUILDSPEC" "cache"; then
    log_ok "cache section present (build caching enabled)"
  else
    log_warn "No cache section — consider adding uv/pip cache paths for faster builds"
    WARNINGS=$((WARNINGS + 1))
  fi

  # ── Summary for this repo ─────────────────────────────────────────────

  if [ "$STRICT" = "true" ]; then
    EFFECTIVE_ERRORS=$((ERRORS + WARNINGS))
  else
    EFFECTIVE_ERRORS=$ERRORS
  fi

  TOTAL_ERRORS=$((TOTAL_ERRORS + ERRORS))
  TOTAL_WARNINGS=$((TOTAL_WARNINGS + WARNINGS))

  if [ "$EFFECTIVE_ERRORS" -eq 0 ]; then
    log ""
    log "  RESULT: PASS ($WARNINGS warning(s))"
    TOTAL_PASSED=$((TOTAL_PASSED + 1))
  else
    log ""
    log "  RESULT: FAIL ($ERRORS error(s), $WARNINGS warning(s))"
  fi
done

# ── Final summary ───────────────────────────────────────────────────────────

log ""
log "============================================"
log "  Buildspec Validation Summary"
log "============================================"
log "  Repos checked: $TOTAL_REPOS"
log "  Passed:        $TOTAL_PASSED"
log "  Failed:        $((TOTAL_REPOS - TOTAL_PASSED))"
log "  Total errors:  $TOTAL_ERRORS"
log "  Total warnings: $TOTAL_WARNINGS"
log "  Strict mode:   $STRICT"
log "============================================"

if [ "$STRICT" = "true" ]; then
  FINAL_ERRORS=$((TOTAL_ERRORS + TOTAL_WARNINGS))
else
  FINAL_ERRORS=$TOTAL_ERRORS
fi

if [ "$FINAL_ERRORS" -gt 0 ]; then
  exit 1
fi

exit 0
