#!/bin/bash
#
# Link Issues to GitHub Project
#
# Reads issue-manifest.json from Stage 3 and adds all issues to the project.
#
# Usage:
#   bash 03-link-issues-to-project.sh --project 7 --issue-manifest issue-manifest.json
#
# Requires:
#   - gh CLI authenticated with project scope
#   - issue-manifest.json from Stage 3
#
# Python 3.13+ / Bash 5+
#

set -euo pipefail

# Defaults
ORG="IggyIkenna"
PROJECT_NUMBER=""
ISSUE_MANIFEST="issue-manifest.json"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)
      PROJECT_NUMBER="$2"
      shift 2
      ;;
    --issue-manifest)
      ISSUE_MANIFEST="$2"
      shift 2
      ;;
    --org)
      ORG="$2"
      shift 2
      ;;
    -h | --help)
      echo "Usage: bash 03-link-issues-to-project.sh --project <number> [--issue-manifest <file>] [--org <org>]"
      echo ""
      echo "Options:"
      echo "  --project          GitHub project number (required)"
      echo "  --issue-manifest   Path to issue manifest JSON (default: issue-manifest.json)"
      echo "  --org              GitHub organization/user (default: IggyIkenna)"
      echo ""
      echo "Example:"
      echo "  bash 03-link-issues-to-project.sh --project 7 --issue-manifest issue-manifest.json"
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

if [ ! -f "$ISSUE_MANIFEST" ]; then
  echo "Error: Issue manifest not found: $ISSUE_MANIFEST"
  echo "Run Stage 3 first: python 02-create-issues.py --apply"
  exit 1
fi

echo "========================================="
echo "Link Issues to GitHub Project"
echo "========================================="
echo ""
echo "Project: #$PROJECT_NUMBER"
echo "Owner: $ORG"
echo "Manifest: $ISSUE_MANIFEST"
echo ""

# Count total issues
TOTAL_ISSUES=$(jq '[.[] | length] | add' "$ISSUE_MANIFEST")

echo "Total issues to link: $TOTAL_ISSUES"
echo ""

# Process each repo
REPOS=$(jq -r 'keys[]' "$ISSUE_MANIFEST")
LINKED=0
SKIPPED=0

for repo in $REPOS; do
  echo "========================================="
  echo "Repo: $repo"
  echo "========================================="

  # Get issues for this repo
  ISSUE_COUNT=$(jq -r ".[\"$repo\"] | length" "$ISSUE_MANIFEST")
  echo "Issues: $ISSUE_COUNT"
  echo ""

  # Process each issue
  for i in $(seq 0 $((ISSUE_COUNT - 1))); do
    ISSUE_NUMBER=$(jq -r ".[\"$repo\"][$i].number" "$ISSUE_MANIFEST")
    ISSUE_TITLE=$(jq -r ".[\"$repo\"][$i].title" "$ISSUE_MANIFEST")
    ISSUE_URL=$(jq -r ".[\"$repo\"][$i].url" "$ISSUE_MANIFEST")

    # Skip if dry run or no issue number
    if [ "$ISSUE_NUMBER" == "null" ] || [ -z "$ISSUE_NUMBER" ]; then
      echo "  ⚠️  Skipping (no issue number): $ISSUE_TITLE"
      ((SKIPPED++))
      continue
    fi

    echo "  #$ISSUE_NUMBER: $(echo "$ISSUE_TITLE" | cut -c1-60)..."

    # Add to project
    if [ -n "$ISSUE_URL" ] && [ "$ISSUE_URL" != "null" ]; then
      gh project item-add "$PROJECT_NUMBER" --owner "$ORG" --url "$ISSUE_URL" 2>/dev/null || {
        echo "    ⚠️  Already in project or failed to add"
      }
    else
      gh project item-add "$PROJECT_NUMBER" --owner "$ORG" --url "https://github.com/$ORG/$repo/issues/$ISSUE_NUMBER" 2>/dev/null || {
        echo "    ⚠️  Already in project or failed to add"
      }
    fi

    echo "    ✅ Added to project"
    ((LINKED++))

    # Rate limiting
    sleep 0.3
  done

  echo ""
done

# Summary
echo "========================================="
echo "Summary"
echo "========================================="
echo ""
echo "Project: #$PROJECT_NUMBER"
echo "  URL: https://github.com/users/$ORG/projects/$PROJECT_NUMBER"
echo ""
echo "Issues processed: $TOTAL_ISSUES"
echo "  Linked: $LINKED"
echo "  Skipped: $SKIPPED"
echo ""

if [ $LINKED -gt 0 ]; then
  echo "✅ Successfully linked $LINKED issues to project"
  echo ""
  echo "Next steps:"
  echo "  1. Configure workflows (Stage 5):"
  echo "     bash 04-copy-workflows.sh --from 5 --to $PROJECT_NUMBER"
  echo ""
  echo "  2. View project:"
  echo "     gh project view $PROJECT_NUMBER --owner $ORG --web"
  echo ""
fi

echo "========================================="
