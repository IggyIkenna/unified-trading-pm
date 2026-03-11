#!/bin/bash
# approve-major-bump.sh — Admin script to trigger the major-bump-approval GHA workflow
#
# Usage:
#   bash unified-trading-pm/scripts/approve-major-bump.sh <repo> <version> \
#     --reason "Breaking API change: removed /v1/orders endpoint" \
#     [--issue 123] \
#     [--approver IggyIkenna] \
#     --admin-pat $GH_PAT
#
# Example:
#   bash scripts/approve-major-bump.sh execution-service 2.0.0 \
#     --reason "Removed REST /v1/positions endpoint (replaced by gRPC)" \
#     --issue 42 \
#     --admin-pat $GH_PAT
#
# What this does:
#   Triggers major-bump-approval.yml via GitHub API workflow_dispatch on the target repo.
#   The GHA workflow then: verifies approver access, checks v1.0.0 readiness gates,
#   dispatches version-bump to unified-trading-pm, updates codex BR8, and closes the Issue.
#
# Note: --admin-pat must have workflow write access (Settings > Actions) on the target repo.

set -euo pipefail

# ── PARSE ARGS ────────────────────────────────────────────────────────────────
REPO=""
VERSION=""
REASON=""
ISSUE_NUMBER=""
ADMIN_PAT="${GH_PAT:-}"
APPROVER="${GITHUB_ACTOR:-IggyIkenna}"
GH_ORG="IggyIkenna"

if [ $# -lt 2 ]; then
  echo "Usage: $0 <repo> <version> --reason <reason> [--issue <num>] [--approver <handle>] --admin-pat <token>"
  exit 1
fi

REPO="$1"
VERSION="$2"
shift 2

while [[ $# -gt 0 ]]; do
  case "$1" in
    --reason)   REASON="$2";       shift 2 ;;
    --issue)    ISSUE_NUMBER="$2"; shift 2 ;;
    --approver) APPROVER="$2";     shift 2 ;;
    --admin-pat) ADMIN_PAT="$2";   shift 2 ;;
    *) echo "Unknown flag: $1"; exit 1 ;;
  esac
done

# ── VALIDATE ──────────────────────────────────────────────────────────────────
if [ -z "$REPO" ] || [ -z "$VERSION" ] || [ -z "$REASON" ]; then
  echo "ERROR: --repo, --version, and --reason are required"
  echo "Usage: $0 <repo> <version> --reason <reason> [--issue <num>] [--approver <handle>] --admin-pat <token>"
  exit 1
fi

if [ -z "$ADMIN_PAT" ]; then
  echo "ERROR: --admin-pat <token> required (or set GH_PAT env var)"
  exit 1
fi

# Validate version format (MAJOR.MINOR.PATCH)
if ! echo "$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
  echo "ERROR: version must be MAJOR.MINOR.PATCH format (e.g. 2.0.0), got: $VERSION"
  exit 1
fi

# Check that this is actually a MAJOR bump (proposed major > 0)
MAJOR_COMPONENT=$(echo "$VERSION" | cut -d. -f1)
if [ "$MAJOR_COMPONENT" -lt 1 ] 2>/dev/null; then
  echo "ERROR: proposed version $VERSION is not a MAJOR bump (major component must be >= 1)"
  exit 1
fi

echo "=========================================="
echo "Major Bump Approval — Admin Trigger"
echo "=========================================="
echo "  Repo:     $REPO"
echo "  Version:  $VERSION"
echo "  Approver: $APPROVER"
echo "  Reason:   $REASON"
[ -n "$ISSUE_NUMBER" ] && echo "  Issue:    #$ISSUE_NUMBER"
echo ""

# ── TRIGGER WORKFLOW ──────────────────────────────────────────────────────────
echo "Triggering major-bump-approval.yml on $GH_ORG/$REPO..."

INPUTS_JSON=$(python3 -c "
import json
inputs = {
    'repo': '$REPO',
    'proposed_version': '$VERSION',
    'reason': '''$REASON''',
    'approver': '$APPROVER',
}
if '$ISSUE_NUMBER':
    inputs['issue_number'] = '$ISSUE_NUMBER'
print(json.dumps(inputs))
" 2>/dev/null || echo "{\"repo\": \"$REPO\", \"proposed_version\": \"$VERSION\", \"reason\": \"$REASON\", \"approver\": \"$APPROVER\"}")

HTTP_STATUS=$(curl -s -o /tmp/dispatch_response.json -w "%{http_code}" \
  -X POST \
  -H "Authorization: Bearer $ADMIN_PAT" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/${GH_ORG}/${REPO}/actions/workflows/major-bump-approval.yml/dispatches" \
  -d "{\"ref\": \"main\", \"inputs\": $INPUTS_JSON}")

if [ "$HTTP_STATUS" = "204" ]; then
  echo "✅ Workflow triggered successfully"
  echo ""
  echo "The major-bump-approval.yml workflow is now running on $GH_ORG/$REPO."
  echo "Monitor: https://github.com/${GH_ORG}/${REPO}/actions/workflows/major-bump-approval.yml"
  [ -n "$ISSUE_NUMBER" ] && echo "Issue:   https://github.com/${GH_ORG}/${REPO}/issues/${ISSUE_NUMBER}"
else
  echo "ERROR: HTTP $HTTP_STATUS — workflow dispatch failed"
  cat /tmp/dispatch_response.json 2>/dev/null || true
  echo ""
  echo "Possible causes:"
  echo "  - major-bump-approval.yml has not been rolled out to $REPO yet"
  echo "  - GH_PAT lacks 'workflow' scope (repo write is not enough for workflow dispatch)"
  echo "  - The repo does not exist: https://github.com/${GH_ORG}/${REPO}"
  exit 1
fi
