#!/bin/bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Shared output helpers for audit scripts.
# Source this at the top of each section script:
#   source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

# Colours
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

AUDIT_FAILS=0
AUDIT_WARNS=0

# emit SECTION CRITERION STATUS EVIDENCE
emit() {
  local section="$1" criterion="$2" status="$3" evidence="$4"
  case "$status" in
    PASS) colour="$GREEN" ;;
    WARN) colour="$YELLOW"; AUDIT_WARNS=$((AUDIT_WARNS+1)) ;;
    FAIL) colour="$RED";    AUDIT_FAILS=$((AUDIT_FAILS+1)) ;;
    *)    colour="$NC" ;;
  esac
  printf "${colour}%-6s${NC} | %-55s | %-4s | %s\n" \
    "$section" "$criterion" "$status" "$evidence"
}

# pass_if_empty SECTION CRITERION "$(rg ...)" — PASS if empty, FAIL otherwise
pass_if_empty() {
  local section="$1" criterion="$2" result="$3"
  if [ -z "$result" ]; then
    emit "$section" "$criterion" "PASS" "none"
  else
    local count; count=$(echo "$result" | wc -l | tr -d ' ')
    emit "$section" "$criterion" "FAIL" "$count hits — first: $(echo "$result" | head -1)"
  fi
}

# warn_if_empty SECTION CRITERION "$(rg ...)" — PASS if populated, WARN if empty
warn_if_nonempty() {
  local section="$1" criterion="$2" result="$3" threshold="${4:-0}"
  local count=0
  [ -n "$result" ] && count=$(echo "$result" | wc -l | tr -d ' ')
  if [ "$count" -le "$threshold" ]; then
    emit "$section" "$criterion" "PASS" "count=$count"
  elif [ "$count" -le 10 ]; then
    emit "$section" "$criterion" "WARN" "$count hits — first: $(echo "$result" | head -1)"
  else
    emit "$section" "$criterion" "FAIL" "$count hits — first: $(echo "$result" | head -1)"
  fi
}

audit_summary() {
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  if [ "$AUDIT_FAILS" -gt 0 ]; then
    printf "${RED}GRADE: FAIL${NC}  (%d FAILs, %d WARNs)\n" "$AUDIT_FAILS" "$AUDIT_WARNS"
    exit 1
  elif [ "$AUDIT_WARNS" -gt 0 ]; then
    printf "${YELLOW}GRADE: CONDITIONAL${NC}  (0 FAILs, %d WARNs)\n" "$AUDIT_WARNS"
    exit 0
  else
    printf "${GREEN}GRADE: PASS${NC}  (0 FAILs, 0 WARNs)\n"
    exit 0
  fi
}

# Resolve workspace root from caller location
resolve_workspace_root() {
  # Called from scripts/audit/<script>.sh → ../../../ = workspace root
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[1]}")" && pwd)"
  cd "$script_dir/../../.." && pwd
}
