#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Pre-Flight Audit Agent (LLM-Powered)
# Uses agent (model: auto - FREE) to audit quality compliance & Cursor rules
# Runs BEFORE quality gates in quickmerge
#
# Usage: ./pre-flight-audit-agent.sh <repo-name>

set -euo pipefail

REPO_NAME="$1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PARSER="$WORKSPACE_ROOT/unified-trading-pm/plans/tasks/claude-code/simple-parser.py"

# Colors
GREEN='\033[0;32m'
NC='\033[0m'

echo "🤖 Running Pre-Flight Audit Agent for $REPO_NAME..."
echo ""

# ── Cloud auth pre-flight ────────────────────────────────────────────────────
# GCP ADC
if command -v gcloud &>/dev/null; then
  if ! gcloud auth application-default print-access-token &>/dev/null 2>&1; then
    echo "⚠️  GCP ADC not active — run: gcloud auth application-default login"
  fi
fi

# AWS credentials
if command -v aws &>/dev/null; then
  if ! aws sts get-caller-identity &>/dev/null 2>&1; then
    echo "⚠️  AWS credentials not configured — run: aws configure"
  else
    AWS_ACCT=$(aws sts get-caller-identity --query 'Account' --output text 2>/dev/null || echo "unknown")
    echo "  AWS account: $AWS_ACCT"
  fi
fi

# Check for API key (never write to world-readable temp file)
if [ -z "${CURSOR_API_KEY:-}" ]; then
  PROJECT_ID="${GCP_PROJECT_ID:?GCP_PROJECT_ID must be set to fetch cursor-api-key from Secret Manager}"
  echo "Getting API key from Secret Manager..."
  CURSOR_API_KEY=$(gcloud secrets versions access latest --secret=cursor-api-key --project="$PROJECT_ID")
  export CURSOR_API_KEY
fi
export CURSOR_API_KEY
export PATH="$HOME/.local/bin:$PATH"

# Enhanced prompt for audit
AUDIT_PROMPT="WORKSPACE CONTEXT:
- Workspace root: $WORKSPACE_ROOT
- Target repo: $REPO_NAME/
- You have READ access to entire workspace (dependencies, workspace rules)
- You can EDIT files in $REPO_NAME/ to fix violations
- Read workspace .cursorrules and .cursor/rules/*.mdc

TASK FOR $REPO_NAME:
Pre-flight audit BEFORE running quality gates. Check for violations and fix them.

STAGE 1: Path Dependency Audit
1. Read $REPO_NAME/pyproject.toml
2. Find all path dependencies (e.g., unified-trading-library = { path = \"../unified-trading-library\" })
3. For EACH path dependency:
   - Change to that repo directory
   - Run: git status --porcelain
   - If output is NOT empty → FAIL with error:
     \"❌ Uncommitted changes in <dep-name>. Commit dependency before downstream repo.\"
4. If ALL path dependencies clean → PASS

STAGE 2: Quality Compliance Audit
Check the following (from .cursor/rules/quality-gates-audit-factors.mdc):

1. E722 (bare except) - MUST NOT be in global ruff ignore
   - Check pyproject.toml [tool.ruff.lint]
   - If E722 in global ignore → AUTO-FIX: Move to per-file-ignores for scripts/* only

2. Hardcoded project IDs in tests
   - Search tests/ for \"central-element-323112\"
   - If found → REPORT (don't auto-fix, needs manual review)

3. Large files (>1500 lines)
   - Find .py files with >1500 lines (excluding tests/, scripts/)
   - If found → REPORT (don't auto-fix, needs splitting)

4. Empty fallbacks for required config
   - Search for .get(\"KEY\", \"\") or os.environ.get(\"KEY\", \"\")
   - If found in non-test code → REPORT

5. Lazy imports (outside TYPE_CHECKING)
   - Search for imports inside functions (not at top of file)
   - If found → REPORT (need to verify if justified)

STAGE 3: Cursor Rules Audit
Read .cursor/rules/*.mdc and check for common violations:

1. Quality gates must use Docker by default
   - Check scripts/quality-gates.sh for NO_DOCKER check
   - Should default to Docker unless NO_DOCKER=true

2. Quickmerge should NOT run quality gates
   - Check scripts/quickmerge.sh
   - Should NOT call scripts/quality-gates.sh

3. Path dependency CI patterns
   - Check .github/workflows/*.yml
   - Should clone path deps before installing

CRITICAL RESTRICTIONS:
- ONLY edit files in $REPO_NAME/ directory
- DO NOT edit unified-trading-library/ or other repos
- You can read everything, but edit only $REPO_NAME/
- AUTO-FIX only simple violations (E722, Docker defaults)
- REPORT complex issues (large files, hardcoded IDs)

OUTPUT FORMAT:
Return a summary with:
✅ PASS: <what passed>
❌ FAIL: <what failed and why>
🔧 FIXED: <what was auto-fixed>
⚠️  WARNING: <what needs manual review>

IMPORTANT: Only run git status/grep commands 2-3 times total, not per file.
Be efficient with tool calls.
"

# Run agent
echo "Running audit agent..."
agent --api-key "$CURSOR_API_KEY" \
  --print \
  --model auto \
  --trust \
  --force \
  --output-format stream-json \
  --stream-partial-output \
  --workspace "$WORKSPACE_ROOT" \
  "$AUDIT_PROMPT" \
  2>&1 | python3 "$PARSER"

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
  echo -e "${GREEN}✅ Pre-Flight Audit Agent completed${NC}"
else
  echo "❌ Pre-Flight Audit Agent failed (exit code: $exit_code)"
fi

exit $exit_code
