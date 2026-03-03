#!/bin/bash
#
# Create "Initial Cleanup" Project with One Task Per Repo
#
# Strategy:
#   - One GitHub Project: "Initial Cleanup"
#   - One issue per repo (14 repos total)
#   - Each issue covers ALL COD issues for that repo
#   - Simple, clean slate approach
#   - Run with batch-fix-v2.sh (7 workers → 7 repos at a time)
#
# Usage:
#   bash create-initial-cleanup-project.sh
#

set -euo pipefail

ORG="IggyIkenna"
CODEX_REPO="unified-trading-codex"
PROJECT_NAME="Initial Cleanup"

# 14 service repos
REPOS=(
    "execution-services"
    "strategy-service"
    "instruments-service"
    "unified-trading-library"
    "market-data-processing-service"
    "ml-training-service"
    "ml-inference-service"
    "features-delta-one-service"
    "features-volatility-service"
    "features-calendar-service"
    "features-onchain-service"
    "market-tick-data-handler"
    "portfolio-manager-service"
    "unified-trading-deployment-v2"
)

echo "========================================="
echo "Initial Cleanup Project Setup"
echo "========================================="
echo ""
echo "Strategy:"
echo "  - 1 project: Initial Cleanup"
echo "  - 14 issues: One per repo"
echo "  - Each issue: Fix ALL COD violations for that repo"
echo "  - Execution: batch-fix-v2.sh with 7 workers"
echo ""

# Step 1: Create project
echo "Step 1: Creating project '$PROJECT_NAME'..."

# Check if project exists (using GraphQL for user projects)
EXISTING_PROJECT=$(gh api graphql -f query='
query {
  user(login: "'"$ORG"'") {
    projectsV2(first: 100) {
      nodes {
        number
        title
      }
    }
  }
}' --jq '.data.user.projectsV2.nodes[] | select(.title == "'"$PROJECT_NAME"'") | .number' 2>/dev/null || echo "")

if [ -n "$EXISTING_PROJECT" ]; then
    echo "✅ Project already exists: #$EXISTING_PROJECT"
    PROJECT_NUMBER=$EXISTING_PROJECT
else
    # Create project using GraphQL API (user project, not org)
    OWNER_ID=$(gh api user --jq .node_id)

    PROJECT_DATA=$(gh api graphql -f query='
      mutation {
        createProjectV2(input: {
          ownerId: "'"$OWNER_ID"'"
          title: "'"$PROJECT_NAME"'"
        }) {
          projectV2 {
            id
            number
            title
          }
        }
      }' --jq '.data.createProjectV2.projectV2')

    PROJECT_NUMBER=$(echo "$PROJECT_DATA" | jq -r '.number')
    echo "✅ Project created: #$PROJECT_NUMBER"
fi

echo ""
echo "========================================="
echo "IMPORTANT: Configure Workflows (Required)"
echo "========================================="
echo ""
echo "GitHub API limitation: Workflows must be configured manually"
echo ""
echo "✅ Quick Setup: Copy workflows from Project #3 (COD template)"
echo ""
echo "Run:"
echo "  bash scripts/utilities/copy-project-workflows.sh --from 3 --to $PROJECT_NUMBER"
echo ""
echo "This will show you:"
echo "  - 8 workflows configured on Project #3"
echo "  - Exact settings for each workflow"
echo "  - Step-by-step instructions to replicate"
echo ""
echo "⭐ CRITICAL: 'Pull request merged → Close linked issues' workflow"
echo "   Without this, PRs merge but issues stay open (manual tracking)"
echo ""
echo "Press Enter to continue with issue creation..."
read -r

echo ""

# Step 2: Create issues (one per repo)
echo "Step 2: Creating issues (one per repo)..."
echo ""

ISSUE_NUMBERS=()

for repo in "${REPOS[@]}"; do
    echo "Creating issue for $repo..."

    # Issue title
    TITLE="[CLEANUP] Fix all COD violations in $repo"

    # Issue body
    BODY="## Objective

Fix **all** Code-Owned Debt (COD) violations in \`$repo\`.

## Scope

This issue covers **all** COD types for this repo:
- **COD-SIZE**: Files exceeding 1500 lines (violate Single Responsibility Principle)
- **COD-STANDARDS**: Files violating coding standards (future)
- **COD-TESTS**: Files missing test coverage (future)

## Approach

1. **Scan repo** for COD violations
2. **Fix violations sequentially** (one COD at a time)
3. **Create PR** for each fix with \`quickmerge --files\`
4. **Verify** quality gates pass (git-aware mode)
5. **Auto-merge** when CI passes

## Expected Fixes

- Split large files (>1500 lines) into smaller, focused modules
- Extract responsibilities into separate files
- Update imports across codebase
- Add/update tests for new modules

## Execution

This issue will be processed by **batch-fix-v2.sh** with workspace pooling:
- Isolated workspace clone for this repo
- All COD fixes for this repo handled sequentially
- No conflicts with other repos (parallel processing)

## Success Criteria

- ✅ All COD-SIZE violations resolved (no files >1500 lines)
- ✅ All quality gates passing
- ✅ Tests passing
- ✅ Clean slate for future development

## Labels

- \`cod\`: Code-Owned Debt
- \`cleanup\`: Initial cleanup task

## Project

Attached to: **Initial Cleanup** (#$PROJECT_NUMBER)

---

**Note**: This is a meta-issue. Individual COD fixes will be handled as part of this cleanup task."

    # Check if issue already exists
    EXISTING_ISSUE=$(gh issue list \
        --repo "$ORG/$repo" \
        --search "\"$TITLE\" in:title" \
        --json number \
        --jq '.[0].number' 2>/dev/null || echo "")

    if [ -n "$EXISTING_ISSUE" ] && [ "$EXISTING_ISSUE" != "null" ]; then
        echo "  ✅ Issue already exists: #$EXISTING_ISSUE"
        ISSUE_NUMBER=$EXISTING_ISSUE
    else
        # Create issue
        ISSUE_NUMBER=$(gh issue create \
            --repo "$ORG/$repo" \
            --title "$TITLE" \
            --body "$BODY" \
            --label "cod,cleanup" \
            --assignee "@me" \
            2>&1 | grep -o "[0-9]*$")

        echo "  ✅ Created issue: #$ISSUE_NUMBER"
    fi

    ISSUE_NUMBERS+=("$ISSUE_NUMBER")

    # Add to project
    gh project item-add "$PROJECT_NUMBER" --owner "$ORG" --url "https://github.com/$ORG/$repo/issues/$ISSUE_NUMBER" 2>/dev/null || true

    sleep 0.5  # Rate limiting
done

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Project: #$PROJECT_NUMBER - $PROJECT_NAME"
echo "Issues created: ${#ISSUE_NUMBERS[@]}"
echo ""
echo "Issue numbers:"
for i in "${!ISSUE_NUMBERS[@]}"; do
    repo="${REPOS[$i]}"
    issue="${ISSUE_NUMBERS[$i]}"
    printf "  #%-5s → %s\n" "$issue" "$repo"
done
echo ""

# Step 3: Configure project workflows (MANUAL - GitHub API limitation)
echo "========================================="
echo "IMPORTANT: Configure Project Workflows"
echo "========================================="
echo ""
echo "⚠️  GitHub API doesn't support workflow creation (yet)"
echo "    You MUST configure these manually for auto-close to work:"
echo ""
echo "1. Go to project settings:"
echo "   https://github.com/users/$ORG/projects/$PROJECT_NUMBER/settings/workflows"
echo ""
echo "2. Create workflow: 'Auto-add cleanup issues'"
echo "   Trigger: Item added to repository"
echo "   Filters: Label = 'cleanup'"
echo "   Action: Add to project"
echo ""
echo "3. Create workflow: 'Auto-close on PR merge'"
echo "   Trigger: Pull request merged"
echo "   Filters: Pull request closes issue"
echo "   Action: Set status to 'Done'"
echo ""
echo "4. (Optional) Create workflow: 'Auto-archive'"
echo "   Trigger: Item status changed"
echo "   Filters: Status = 'Done' for 30 days"
echo "   Action: Archive item"
echo ""
echo "📝 Without these workflows:"
echo "   - Issues won't auto-close when PRs merge"
echo "   - You'll need to manually update status"
echo "   - Project won't track completion automatically"
echo ""
echo "========================================="
echo "Next Steps (After Configuring Workflows)"
echo "========================================="
echo ""
echo "1. View project:"
echo "   gh project view $PROJECT_NUMBER --owner $ORG --web"
echo ""
echo "2. Run initial cleanup (7 workers, processes 7 repos at a time):"
echo "   cd unified-trading-codex/11-project-management/github-integration"
echo "   bash scripts/automation/batch-fix-v2.sh \\"
echo "       --model gemini-3-flash \\"
echo "       --issues \"${ISSUE_NUMBERS[*]}\" \\"
echo "       --max-parallel 7"
echo ""
echo "3. Monitor progress:"
echo "   gh pr list --label cod --state open"
echo "   gh project view $PROJECT_NUMBER --owner $ORG"
echo ""
echo "4. What happens:"
echo "   - 7 workers process 7 repos simultaneously"
echo "   - Each worker fixes ALL COD issues for its repo sequentially"
echo "   - Isolated workspace per repo (no conflicts)"
echo "   - Git-aware quality gates (no deadlock)"
echo "   - Clean slate when complete"
echo ""
echo "========================================="
echo "Strategy Rationale"
echo "========================================="
echo ""
echo "Why one issue per repo (not per file)?"
echo "  ✅ Simpler project management (14 tasks vs 200+)"
echo "  ✅ One worker owns one repo (clear responsibility)"
echo "  ✅ Sequential fixes per repo (easier to verify)"
echo "  ✅ Clean slate per repo before moving on"
echo "  ✅ Easier to track progress (14 repos, not 200 files)"
echo ""
echo "Why 7 workers?"
echo "  ✅ Processes half the repos at once (good parallelism)"
echo "  ✅ Not too aggressive (avoids API rate limits)"
echo "  ✅ Manageable monitoring (7 PRs at a time)"
echo "  ✅ Second batch picks up remaining 7 repos"
echo ""
echo "Why workspace pooling (v2)?"
echo "  ✅ Isolated clones per repo (zero conflicts)"
echo "  ✅ True parallelism (7 repos at once)"
echo "  ✅ Resource-aware (doesn't over-clone)"
echo ""
echo "========================================="
