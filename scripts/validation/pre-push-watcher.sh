#!/bin/bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Pre-Push Watcher with LLM Auto-Fix
# Monitors pre-push hook (act), auto-fixes failures via LLM agent
#
# Usage (standalone):
#   ./pre-push-watcher.sh
#
# Usage (from quickmerge with --watch):
#   bash scripts/quickmerge.sh "fix: update" --watch
#
# What it does:
# 1. Runs pre-push hook (act -j quality-gates)
# 2. If act fails, captures error output
# 3. Calls LLM agent wrapper to fix issues
# 4. Re-runs act to verify fixes
# 5. Repeats up to MAX_ATTEMPTS times
# 6. Returns 0 if act passes, 1 if max attempts exceeded

set -e

REPO_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
REPO_NAME=$(basename "$REPO_DIR")
WORKSPACE_ROOT="$(cd "$REPO_DIR/.." && pwd)"

MAX_ATTEMPTS=3
ATTEMPT=1

# Temporary files for capturing output
# Trailing X's, no suffix: BSD mktemp only substitutes X's at the END of the template, so
# `/tmp/act-errors-XXXXXX.log` would be taken LITERALLY — a fixed filename shared by every
# concurrent run, and any run that died before its cleanup trap would wedge all later runs
# with "mkstemp failed: File exists". Measured 2026-08-12 via the same pattern elsewhere.
ERROR_LOG=$(mktemp /tmp/act-errors-XXXXXX)
ACT_OUTPUT=$(mktemp /tmp/act-output-XXXXXX)

# Cleanup on exit
cleanup() {
  rm -f "$ERROR_LOG" "$ACT_OUTPUT"
}
trap cleanup EXIT

echo "🔍 Pre-Push Watcher: Monitoring act quality gates..."
echo "Repository: $REPO_NAME"
echo "Max attempts: $MAX_ATTEMPTS"
echo ""

run_act() {
  echo "[$ATTEMPT/$MAX_ATTEMPTS] Running act quality-gates..."

  # Run act and capture output
  if act -j quality-gates --secret-file ~/.secrets >"$ACT_OUTPUT" 2>&1; then
    echo "✅ Act quality-gates PASSED"
    cat "$ACT_OUTPUT"
    return 0
  else
    echo "❌ Act quality-gates FAILED"
    cat "$ACT_OUTPUT"
    cat "$ACT_OUTPUT" >"$ERROR_LOG"
    return 1
  fi
}

# Initial attempt
if run_act; then
  echo ""
  echo "✅ Pre-push hook passed on first attempt"
  exit 0
fi

# Auto-fix loop
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  ATTEMPT=$((ATTEMPT + 1))

  echo ""
  echo "🤖 Attempting auto-fix with LLM agent (attempt $ATTEMPT/$MAX_ATTEMPTS)..."

  # Call LLM agent wrapper
  if bash "$WORKSPACE_ROOT/.cursor/scripts/llm-agent-wrapper.sh" \
    "$REPO_NAME" \
    "$ERROR_LOG" \
    "Fix the CI/CD errors reported by act quality-gates. Run quality gates locally to verify fixes."; then

    echo "✅ LLM agent completed fixes"

    # Re-run act to verify
    if run_act; then
      echo ""
      echo "✅ Pre-push hook passed after auto-fix (attempt $ATTEMPT/$MAX_ATTEMPTS)"
      exit 0
    fi
  else
    echo "❌ LLM agent failed to fix issues"
  fi
done

echo ""
echo "❌ Pre-push hook still failing after $MAX_ATTEMPTS attempts"
echo ""
echo "Manual intervention required:"
echo "1. Review errors in act output above"
echo "2. Fix issues manually"
echo "3. Run: bash scripts/quality-gates.sh"
echo "4. Re-run: git push"
echo ""
echo "Or skip pre-push hook (not recommended):"
echo "  git push --no-verify"

exit 1
