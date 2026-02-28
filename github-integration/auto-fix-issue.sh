#!/bin/bash
#
# Auto-Fix GitHub Issue using Cursor Agent CLI
#
# Usage:
#   bash auto-fix-issue.sh <ISSUE_NUMBER> [OPTIONS]
#
# Options:
#   --dry-run         Show the prompt without executing
#   --interactive     Run in interactive mode (no --print)
#   --model <model>   Specify model to use (e.g., gpt-5, sonnet-4, sonnet-4-thinking)
#
# Example:
#   bash auto-fix-issue.sh 1234
#   bash auto-fix-issue.sh 1234 --dry-run
#   bash auto-fix-issue.sh 1234 --model sonnet-4-thinking
#   bash auto-fix-issue.sh 1234 --model gpt-5 --interactive
#

set -euo pipefail

ISSUE_NUMBER="${1:-}"
DRY_RUN=false
INTERACTIVE=false
MODEL=""
VERBOSE=false

if [ -z "$ISSUE_NUMBER" ]; then
    echo "Usage: bash auto-fix-issue.sh <ISSUE_NUMBER> [--dry-run] [--interactive] [--model <model>]"
    echo ""
    echo "Available models:"
    echo "  - gpt-4o-mini           (FREE: 500 requests/day - recommended for code standards)"
    echo "  - gpt-5                 (OpenAI GPT-5)"
    echo "  - sonnet-4              (Anthropic Claude Sonnet 4)"
    echo "  - sonnet-4-thinking     (Claude Sonnet 4 with extended reasoning)"
    echo "  - (or any model from: cursor agent --list-models)"
    exit 1
fi

shift
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --interactive)
            INTERACTIVE=true
            shift
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

CODEX_ISSUE_REPO="IggyIkenna/unified-trading-codex"
# Use environment variable if set, otherwise use default
WORKSPACE_ROOT="${WORKSPACE_ROOT:-/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos}"

echo "🤖 Auto-Fix Issue #$ISSUE_NUMBER"
echo "========================================================================"
echo ""

# Fetch issue details
echo "📋 Fetching issue from $CODEX_ISSUE_REPO..."
ISSUE_JSON=$(gh issue view "$ISSUE_NUMBER" --repo "$CODEX_ISSUE_REPO" --json number,title,body,labels)

ISSUE_TITLE=$(echo "$ISSUE_JSON" | jq -r '.title')
ISSUE_BODY=$(echo "$ISSUE_JSON" | jq -r '.body')
ISSUE_LABELS=$(echo "$ISSUE_JSON" | jq -r '.labels[].name' | tr '\n' ',' | sed 's/,$//')

echo "  Title: $ISSUE_TITLE"
echo "  Labels: $ISSUE_LABELS"
echo ""

# Extract service name from title (format: [service-name] ...)
SERVICE_NAME=$(echo "$ISSUE_TITLE" | grep -o '\[.*\]' | tr -d '[]' | head -1)

if [ -z "$SERVICE_NAME" ]; then
    echo "❌ Could not extract service name from issue title"
    echo "   Expected format: [service-name] GAP-ID: Description"
    exit 1
fi

# Skip if service name is "Subtask", "Task", or "Epic" (these are hierarchy issues, not service issues)
if [[ "$SERVICE_NAME" =~ ^(Subtask|Task|Epic)$ ]]; then
    echo "⚠️  Skipping hierarchy issue: $ISSUE_TITLE"
    echo "   This is not a service-specific issue."
    exit 0
fi

echo "🎯 Target Service: $SERVICE_NAME"
echo "📂 Workspace: $WORKSPACE_ROOT/$SERVICE_NAME"
echo ""

# Verify service exists
if [ ! -d "$WORKSPACE_ROOT/$SERVICE_NAME" ]; then
    echo "❌ Service directory not found: $WORKSPACE_ROOT/$SERVICE_NAME"
    exit 1
fi

# Build agent prompt
read -r -d '' AGENT_PROMPT << EOF || true
Implement GitHub Issue #${ISSUE_NUMBER} from ${CODEX_ISSUE_REPO}

**IMPORTANT: Check if Already Fixed**
Before making changes:
1. Read the affected file(s) mentioned in the issue
2. Verify the violation still exists
3. If the file is ALREADY compliant (issue already fixed):
   - Run quality gates to confirm: \`bash scripts/quality-gates.sh\`
   - If they pass, report: "Issue already resolved - file is compliant"
   - Exit successfully without running quickmerge
   - DO NOT add comments or make unnecessary changes

**Issue Details:**
Title: ${ISSUE_TITLE}
Labels: ${ISSUE_LABELS}

**Service**: ${SERVICE_NAME}

**Task**:
${ISSUE_BODY}

**Context Files** (use @ to reference):
- @unified-trading-codex/06-coding-standards/README.md
- @unified-trading-codex/.cursorrules (workspace rules)
- @${SERVICE_NAME}/.cursorrules (service-specific rules)

**Critical Requirements**:

1. **Navigate to service directory**:
   \`\`\`bash
   cd ${SERVICE_NAME}
   \`\`\`

2. **Read the issue details above** - it contains:
   - Affected files to fix
   - Codex reference for guidance
   - Expected pattern/fix

3. **Fix all affected files** listed in the issue

4. **Run quality gates** (MUST pass):
   \`\`\`bash
   bash scripts/quality-gates.sh
   \`\`\`

5. **Commit with cross-repo reference**:
   \`\`\`bash
   bash scripts/quickmerge.sh "Fixes ${CODEX_ISSUE_REPO}#${ISSUE_NUMBER}: <SHORT_DESCRIPTION>" --files "<space-separated-files>"
   \`\`\`

   **CRITICAL**: Use full repo reference: \`${CODEX_ISSUE_REPO}#${ISSUE_NUMBER}\`

**Success Criteria**:
- [ ] All files in "Affected Files" section are fixed
- [ ] Quality gates pass (ruff format, ruff check, pytest, codex compliance)
- [ ] Quickmerge creates PR with correct issue reference
- [ ] PR title/body contains: "Fixes ${CODEX_ISSUE_REPO}#${ISSUE_NUMBER}"

**DO NOT**:
- Skip quality gates
- Push directly to main
- Use just "Fixes #${ISSUE_NUMBER}" (missing repo name)
- Commit without --files flag

**Verification**:
After quickmerge completes, verify:
\`\`\`bash
# Check PR was created
gh pr list --repo ${CODEX_ISSUE_REPO%/*}/${SERVICE_NAME}

# Verify PR references the issue
gh pr view <PR_NUMBER> --repo ${CODEX_ISSUE_REPO%/*}/${SERVICE_NAME} | grep "Fixes.*#${ISSUE_NUMBER}"
\`\`\`
EOF

if [ "$DRY_RUN" = true ]; then
    echo "📄 Generated Prompt:"
    echo "========================================================================"
    echo "$AGENT_PROMPT"
    echo "========================================================================"
    echo ""
    if [ -n "$MODEL" ]; then
        echo "🤖 Model: $MODEL"
        echo ""
    fi
    echo "✅ Dry run complete. To execute, remove --dry-run flag."
    exit 0
fi

# Execute Cursor Agent
echo "🚀 Starting Cursor Agent..."
if [ -n "$MODEL" ]; then
    echo "🤖 Model: $MODEL"
fi
echo ""

# Execute cursor agent
if [ "$INTERACTIVE" = true ]; then
    # Interactive mode
    if [ -n "$MODEL" ]; then
        cursor agent \
            --force \
            --workspace "$WORKSPACE_ROOT" \
            --model "$MODEL" \
            "$AGENT_PROMPT"
    else
        cursor agent \
            --force \
            --workspace "$WORKSPACE_ROOT" \
            "$AGENT_PROMPT"
    fi
else
    # Headless mode
    # Choose output format based on verbosity
    if [ "$VERBOSE" = true ]; then
        # Verbose: stream-json piped through parser
        OUTPUT_FORMAT="stream-json"
        PARSER="$(dirname "$0")/parse-agent-logs.py"

        if [ -n "$MODEL" ]; then
            cursor agent \
                --print \
                --force \
                --workspace "$WORKSPACE_ROOT" \
                --model "$MODEL" \
                --output-format "$OUTPUT_FORMAT" \
                "$AGENT_PROMPT" | python3 "$PARSER"
        else
            cursor agent \
                --print \
                --force \
                --workspace "$WORKSPACE_ROOT" \
                --output-format "$OUTPUT_FORMAT" \
                "$AGENT_PROMPT" | python3 "$PARSER"
        fi
    else
        # Normal: clean text output
        if [ -n "$MODEL" ]; then
            cursor agent \
                --print \
                --force \
                --workspace "$WORKSPACE_ROOT" \
                --model "$MODEL" \
                "$AGENT_PROMPT"
        else
            cursor agent \
                --print \
                --force \
                --workspace "$WORKSPACE_ROOT" \
                "$AGENT_PROMPT"
        fi
    fi
fi

EXIT_CODE=$?

echo ""
echo "========================================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Agent completed successfully"
    echo ""
    echo "Next steps:"
    echo "1. Verify PR was created: gh pr list --repo ${CODEX_ISSUE_REPO%/*}/${SERVICE_NAME}"
    echo "2. Check issue status: gh issue view $ISSUE_NUMBER --repo $CODEX_ISSUE_REPO"
    echo "3. Monitor PR merge and issue auto-close"
else
    echo "❌ Agent failed with exit code: $EXIT_CODE"
    echo ""
    echo "Check the output above for errors"
fi
echo "========================================================================"

exit $EXIT_CODE
