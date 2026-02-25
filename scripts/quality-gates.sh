#!/usr/bin/env bash
# quality-gates.sh — quality checks for unified-trading-pm
#
# Usage:
#   bash scripts/quality-gates.sh          # run + auto-fix where possible
#   bash scripts/quality-gates.sh --quick  # skip bats (for fast local checks)
#   bash scripts/quality-gates.sh --no-fix # verify only, no fixes
#
# Checks (in order):
#   1. shellcheck — lint all .sh scripts
#   2. JSON validate — workspace-manifest.json must be valid JSON
#   3. bats — run tests/test_*.bats
#
# No Python quality gates — this repo has no source code.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ── Colors ────────────────────────────────────────────────────────────────────
if command -v tput >/dev/null 2>&1 && [ -t 1 ]; then
    RED=$(tput setaf 1); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3)
    CYAN=$(tput setaf 6); BOLD=$(tput bold); NC=$(tput sgr0)
else
    RED=""; GREEN=""; YELLOW=""; CYAN=""; BOLD=""; NC=""
fi

QUICK=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --quick)  QUICK=true; shift ;;
        --no-fix) shift ;;   # accepted for API compatibility with service quality gates
        *)        shift ;;
    esac
done

PASS=0; FAIL=0; WARN=0
START_TIME=$(date +%s)

section() { echo ""; echo "${BOLD}${CYAN}── $* ──${NC}"; }
ok()      { echo "${GREEN}✓${NC} $*"; ((PASS++)) || true; }
fail()    { echo "${RED}✗${NC} $*" >&2; ((FAIL++)) || true; }
warn()    { echo "${YELLOW}⚠${NC}  $*"; ((WARN++)) || true; }

# ── 1. shellcheck ─────────────────────────────────────────────────────────────
section "shellcheck"

if ! command -v shellcheck >/dev/null 2>&1; then
    warn "shellcheck not installed — skipping (brew install shellcheck)"
else
    SHELL_ERRORS=0

    # All .sh scripts — sourced libs get SC1091 disabled (they're not standalone)
    while IFS= read -r -d '' script; do
        basename_script="$(basename "$script")"
        flags=(-S warning)
        [[ "$basename_script" == _* ]] && flags+=(-e SC1091)

        if shellcheck "${flags[@]}" "$script" 2>/dev/null; then
            ok "$basename_script"
        else
            fail "$basename_script has shellcheck warnings"
            shellcheck "${flags[@]}" "$script" 2>&1 | sed 's/^/    /' >&2
            ((SHELL_ERRORS++)) || true
        fi
    done < <(find "$REPO_ROOT/scripts" -name "*.sh" -print0 | sort -z)
fi

# ── 2. JSON validation ────────────────────────────────────────────────────────
section "JSON validation"

MANIFEST="$REPO_ROOT/workspace-manifest.json"
if [ ! -f "$MANIFEST" ]; then
    fail "workspace-manifest.json not found"
elif python3 -c "import json; json.load(open('$MANIFEST'))" 2>/dev/null; then
    ok "workspace-manifest.json is valid JSON"

    # Check required top-level keys
    MISSING_KEYS=$(python3 -c "
import json, sys
data = json.load(open('$MANIFEST'))
required = ['title', 'repositories']
missing = [k for k in required if k not in data]
print(' '.join(missing))
" 2>/dev/null)
    if [ -n "$MISSING_KEYS" ]; then
        fail "workspace-manifest.json missing required keys: $MISSING_KEYS"
    else
        ok "workspace-manifest.json has required keys (title, repositories)"
    fi
else
    fail "workspace-manifest.json has invalid JSON"
    python3 -c "import json; json.load(open('$MANIFEST'))" 2>&1 | sed 's/^/    /' >&2
fi

# ── 3. Validate cursor-rules/ matches .cursor/rules/ count (if local) ─────────
section "Cursor rules consistency"

PM_RULES="$REPO_ROOT/cursor-rules"
WORKSPACE_ROOT="$(cd "$REPO_ROOT/.." && pwd)"
LOCAL_RULES="$WORKSPACE_ROOT/.cursor/rules"

if [ -d "$PM_RULES" ] && [ -d "$LOCAL_RULES" ]; then
    repo_count=$(find "$PM_RULES"  -maxdepth 1 -name "*.mdc" | wc -l | tr -d ' ')
    local_count=$(find "$LOCAL_RULES" -maxdepth 1 -name "*.mdc" | wc -l | tr -d ' ')
    if [ "$repo_count" -eq "$local_count" ]; then
        ok "cursor-rules/ ($repo_count) matches .cursor/rules/ ($local_count)"
    else
        warn "cursor-rules/ ($repo_count) differs from .cursor/rules/ ($local_count) — run quickmerge to sync"
    fi
elif [ ! -d "$PM_RULES" ]; then
    warn "cursor-rules/ not found — run quickmerge to populate"
fi

# ── 4. bats tests ─────────────────────────────────────────────────────────────
if [ "$QUICK" = false ]; then
    section "bats tests"

    if ! command -v bats >/dev/null 2>&1; then
        warn "bats not installed — skipping tests"
        echo "  Install: brew install bats-core"
        echo "  Or: npm install -g bats"
    else
        BATS_FILES=("$REPO_ROOT"/tests/test_*.bats)
        if [ ${#BATS_FILES[@]} -eq 0 ] || [ ! -f "${BATS_FILES[0]}" ]; then
            warn "No test files found in tests/"
        else
            if bats --tap "${BATS_FILES[@]}" 2>&1; then
                ok "All bats tests passed"
            else
                fail "bats tests failed"
            fi
        fi
    fi
fi

# ── Summary ───────────────────────────────────────────────────────────────────
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "${BOLD}── Quality Gate Summary ──${NC}"
echo "  ${GREEN}✓ Passed:${NC}  $PASS"
[ "$WARN" -gt 0 ] && echo "  ${YELLOW}⚠ Warnings:${NC} $WARN"
[ "$FAIL" -gt 0 ] && echo "  ${RED}✗ Failed:${NC}  $FAIL"
echo "  Duration: ${DURATION}s"
echo ""

if [ "$FAIL" -gt 0 ]; then
    echo "${RED}${BOLD}QUALITY GATES FAILED${NC}" >&2
    exit 1
else
    echo "${GREEN}${BOLD}QUALITY GATES PASSED${NC}"
    exit 0
fi
