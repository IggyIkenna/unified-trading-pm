#!/bin/bash
#
# Verify GitHub Project Setup
#
# Validates that project is properly configured with issues, labels, and workflows.
#
# Usage:
#   bash 05-verify-setup.sh --project 6
#
# Requires:
#   - gh CLI authenticated
#
# Python 3.13+ / Bash 5+
#

set -euo pipefail

# Defaults
ORG="IggyIkenna"
PROJECT_NUMBER=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --project)
            PROJECT_NUMBER="$2"
            shift 2
            ;;
        --org)
            ORG="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: bash 05-verify-setup.sh --project <number> [--org <org>]"
            echo ""
            echo "Options:"
            echo "  --project  GitHub project number (required)"
            echo "  --org      GitHub organization/user (default: IggyIkenna)"
            echo ""
            echo "Example:"
            echo "  bash 05-verify-setup.sh --project 6"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate
if [ -z "$PROJECT_NUMBER" ]; then
    echo "Error: --project is required"
    exit 1
fi

echo "========================================="
echo "GitHub Project Verification"
echo "========================================="
echo ""
echo "Project: #$PROJECT_NUMBER"
echo "Owner: $ORG"
echo ""

# Verification checks
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

# Check 1: Project exists
echo "Check 1: Project exists..."
PROJECT_DATA=$(gh api graphql -f query='
query {
  user(login: "'"$ORG"'") {
    projectV2(number: '"$PROJECT_NUMBER"') {
      id
      title
      url
    }
  }
}' 2>/dev/null || echo "")

if [ -z "$PROJECT_DATA" ] || [ "$PROJECT_DATA" == "null" ]; then
    echo "  ❌ FAILED: Project #$PROJECT_NUMBER not found"
    ((CHECKS_FAILED++))
    exit 1
else
    PROJECT_TITLE=$(echo "$PROJECT_DATA" | jq -r '.data.user.projectV2.title')
    PROJECT_URL=$(echo "$PROJECT_DATA" | jq -r '.data.user.projectV2.url')
    echo "  ✅ PASSED: $PROJECT_TITLE"
    echo "     URL: $PROJECT_URL"
    ((CHECKS_PASSED++))
fi
echo ""

# Check 2: Count issues in project
echo "Check 2: Issues linked to project..."
ISSUE_COUNT=$(gh project item-list "$PROJECT_NUMBER" --owner "$ORG" --format json --limit 100 2>/dev/null | jq '. | length' || echo "0")

if [ "$ISSUE_COUNT" -eq 0 ]; then
    echo "  ⚠️  WARNING: No issues found in project"
    echo "     Run: python 02-create-issues.py --apply"
    echo "     Then: bash 03-link-issues-to-project.sh --project $PROJECT_NUMBER"
    ((CHECKS_WARNING++))
elif [ "$ISSUE_COUNT" -lt 51 ]; then
    echo "  ⚠️  WARNING: Only $ISSUE_COUNT issues found (expected 51)"
    echo "     Some issues may not be linked yet"
    ((CHECKS_WARNING++))
else
    echo "  ✅ PASSED: $ISSUE_COUNT issues linked"
    ((CHECKS_PASSED++))
fi
echo ""

# Check 3: Verify labels exist on issues
echo "Check 3: Labels on issues..."

# Get a sample of issues and check labels
SAMPLE_ISSUES=$(gh project item-list "$PROJECT_NUMBER" --owner "$ORG" --format json --limit 10 2>/dev/null || echo "[]")
LABEL_COUNT=$(echo "$SAMPLE_ISSUES" | jq '[.[] | select(.labels != null) | select(.labels | contains(["UNIFIED-LIBRARIES-REFACTOR"]))] | length' || echo "0")

if [ "$LABEL_COUNT" -eq 0 ]; then
    echo "  ⚠️  WARNING: No issues with UNIFIED-LIBRARIES-REFACTOR label found"
    echo "     Issues may need labels applied"
    ((CHECKS_WARNING++))
else
    echo "  ✅ PASSED: Issues have UNIFIED-LIBRARIES-REFACTOR label"
    ((CHECKS_PASSED++))
fi

# Check priority labels
PRIORITY_COUNT=$(echo "$SAMPLE_ISSUES" | jq '[.[] | select(.labels != null) | select(.labels | map(select(startswith("P0") or startswith("P1") or startswith("P2") or startswith("P3"))) | length > 0)] | length' || echo "0")

if [ "$PRIORITY_COUNT" -eq 0 ]; then
    echo "  ⚠️  WARNING: No priority labels (P0-P3) found"
    ((CHECKS_WARNING++))
else
    echo "  ✅ PASSED: Issues have priority labels"
    ((CHECKS_PASSED++))
fi
echo ""

# Check 4: Verify workflows configured
echo "Check 4: Project workflows..."
WORKFLOW_COUNT=$(gh api graphql -f query='
query {
  user(login: "'"$ORG"'") {
    projectV2(number: '"$PROJECT_NUMBER"') {
      workflows(first: 20) {
        totalCount
        nodes {
          name
          enabled
        }
      }
    }
  }
}' --jq '.data.user.projectV2.workflows.totalCount' 2>/dev/null || echo "0")

if [ "$WORKFLOW_COUNT" -eq 0 ]; then
    echo "  ⚠️  WARNING: No workflows configured"
    echo "     Run: bash 04-copy-workflows.sh --from 5 --to $PROJECT_NUMBER"
    echo "     Then manually configure 8 workflows in GitHub UI"
    ((CHECKS_WARNING++))
elif [ "$WORKFLOW_COUNT" -lt 8 ]; then
    echo "  ⚠️  WARNING: Only $WORKFLOW_COUNT workflows configured (expected 8)"
    echo "     Complete workflow configuration in GitHub UI"
    ((CHECKS_WARNING++))
else
    echo "  ✅ PASSED: $WORKFLOW_COUNT workflows configured"
    ((CHECKS_PASSED++))
fi
echo ""

# Summary
echo "========================================="
echo "Verification Summary"
echo "========================================="
echo ""
echo "Project: #$PROJECT_NUMBER - $PROJECT_TITLE"
echo ""
echo "Checks:"
echo "  ✅ Passed:   $CHECKS_PASSED"
echo "  ⚠️  Warning:  $CHECKS_WARNING"
echo "  ❌ Failed:   $CHECKS_FAILED"
echo ""

if [ $CHECKS_FAILED -gt 0 ]; then
    echo "❌ Verification FAILED"
    echo "   Fix failed checks above before proceeding"
    exit 1
elif [ $CHECKS_WARNING -gt 0 ]; then
    echo "⚠️  Verification PASSED with warnings"
    echo "   Consider addressing warnings for complete setup"
    exit 0
else
    echo "✅ Verification PASSED"
    echo "   Project is ready for development!"
    echo ""
    echo "Next steps:"
    echo "  1. View project:"
    echo "     gh project view $PROJECT_NUMBER --owner $ORG --web"
    echo ""
    echo "  2. Generate project README:"
    echo "     bash 06-generate-project-readme.sh --project $PROJECT_NUMBER > PROJECT_README.md"
    echo ""
    echo "  3. Start working on issues!"
    echo ""
fi

echo "========================================="
