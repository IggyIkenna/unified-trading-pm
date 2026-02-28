#!/bin/bash
# Test: Create Epic → Task → Subtask and verify linking

ORG="IggyIkenna"
REPO="unified-trading-codex"

echo "🧪 Testing Epic → Task → Subtask creation and linking"
echo ""

# Create Epic
echo "1️⃣ Creating Epic..."
EPIC_NUM=$(gh issue create \
  --repo "$ORG/$REPO" \
  --title "[TEST Epic] Test Service" \
  --body "Test epic for sub-issue linking" \
  --label "epic,p2-medium" \
  --json number --jq '.number')
echo "   ✅ Created Epic #$EPIC_NUM"

# Create Task
echo ""
echo "2️⃣ Creating Task..."
TASK_NUM=$(gh issue create \
  --repo "$ORG/$REPO" \
  --title "[TEST Task] Test Task" \
  --body "Test task under epic #$EPIC_NUM" \
  --label "task,p2-medium" \
  --json number --jq '.number')
echo "   ✅ Created Task #$TASK_NUM"

# Create Subtask
echo ""
echo "3️⃣ Creating Subtask..."
SUBTASK_NUM=$(gh issue create \
  --repo "$ORG/$REPO" \
  --title "[TEST Subtask] Test Subtask" \
  --body "Test subtask under task #$TASK_NUM" \
  --label "subtask,p2-medium" \
  --json number --jq '.number')
echo "   ✅ Created Subtask #$SUBTASK_NUM"

# Get node IDs
echo ""
echo "4️⃣ Getting node IDs for GraphQL..."
EPIC_NODE=$(gh api "/repos/$ORG/$REPO/issues/$EPIC_NUM" --jq '.node_id')
TASK_NODE=$(gh api "/repos/$ORG/$REPO/issues/$TASK_NUM" --jq '.node_id')
SUBTASK_NODE=$(gh api "/repos/$ORG/$REPO/issues/$SUBTASK_NUM" --jq '.node_id')
echo "   Epic node: $EPIC_NODE"
echo "   Task node: $TASK_NODE"
echo "   Subtask node: $SUBTASK_NODE"

# Link Task → Epic
echo ""
echo "5️⃣ Linking Task #$TASK_NUM → Epic #$EPIC_NUM..."
gh api graphql -f query="
mutation {
  addSubIssue(input: {
    issueId: \"$EPIC_NODE\",
    subIssueId: \"$TASK_NODE\"
  }) {
    issue { number title }
    subIssue { number title }
  }
}"
echo "   ✅ Linked!"

# Link Subtask → Task
echo ""
echo "6️⃣ Linking Subtask #$SUBTASK_NUM → Task #$TASK_NUM..."
gh api graphql -f query="
mutation {
  addSubIssue(input: {
    issueId: \"$TASK_NODE\",
    subIssueId: \"$SUBTASK_NODE\"
  }) {
    issue { number title }
    subIssue { number title }
  }
}"
echo "   ✅ Linked!"

# Verify hierarchy
echo ""
echo "7️⃣ Verifying hierarchy via GraphQL..."
gh api graphql -f query="
{
  repository(owner: \"$ORG\", name: \"$REPO\") {
    epic: issue(number: $EPIC_NUM) {
      number
      title
      subIssues(first: 10) {
        totalCount
        nodes {
          number
          title
          subIssues(first: 10) {
            totalCount
            nodes {
              number
              title
            }
          }
        }
      }
    }
  }
}" --jq '.data.repository.epic'

echo ""
echo "✅ Test complete! View at:"
echo "   https://github.com/$ORG/$REPO/issues/$EPIC_NUM"
