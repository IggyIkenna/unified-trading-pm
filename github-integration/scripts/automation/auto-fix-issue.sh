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
ORG="IggyIkenna"
# Use environment variable if set, otherwise use default
WORKSPACE_ROOT="${WORKSPACE_ROOT:-/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos}"

echo "🤖 Auto-Fix Issue #$ISSUE_NUMBER"
echo "========================================================================"
echo ""

# Parse issue (supports "repo:number" or just "number")
if [[ "$ISSUE_NUMBER" == *":"* ]]; then
    # Format: repo:number (e.g., "execution-services:147")
    SERVICE_NAME="${ISSUE_NUMBER%%:*}"
    ACTUAL_ISSUE_NUMBER="${ISSUE_NUMBER##*:}"
    ISSUE_REPO="$ORG/$SERVICE_NAME"
    echo "📋 Fetching issue #$ACTUAL_ISSUE_NUMBER from $ISSUE_REPO..."
else
    # Standard format - fetch from codex repo
    ACTUAL_ISSUE_NUMBER="$ISSUE_NUMBER"
    ISSUE_REPO="$CODEX_ISSUE_REPO"
    echo "📋 Fetching issue #$ACTUAL_ISSUE_NUMBER from $ISSUE_REPO..."
fi

ISSUE_JSON=$(gh issue view "$ACTUAL_ISSUE_NUMBER" --repo "$ISSUE_REPO" --json number,title,body,labels)

ISSUE_TITLE=$(echo "$ISSUE_JSON" | jq -r '.title')
ISSUE_BODY=$(echo "$ISSUE_JSON" | jq -r '.body')
ISSUE_LABELS=$(echo "$ISSUE_JSON" | jq -r '.labels[].name' | tr '\n' ',' | sed 's/,$//')

echo "  Title: $ISSUE_TITLE"
echo "  Labels: $ISSUE_LABELS"
echo ""

# Extract service name from title if not already from repo:number format
if [[ "$ISSUE_NUMBER" == *":"* ]]; then
    # Already have SERVICE_NAME from parsing
    :
else
    # Extract from title (format: [service-name] ...)
    SERVICE_NAME=$(echo "$ISSUE_TITLE" | grep -o '\[.*\]' | tr -d '[]' | head -1)
fi

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
Implement GitHub Issue #${ACTUAL_ISSUE_NUMBER} from ${ISSUE_REPO}

**IMPORTANT: Check if Already Fixed**
Before making changes:
1. Read the affected file(s) mentioned in the issue
2. Verify the violation still exists
3. If the file is ALREADY compliant (issue already fixed):
   - Run quality gates to confirm: \`bash scripts/quality-gates.sh\`
   - If they pass, run quickmerge with message "Issue #${ACTUAL_ISSUE_NUMBER} already resolved - verified compliant"
   - This ensures the issue gets closed even though no new changes were needed
   - DO NOT make unnecessary code changes if already compliant

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
- @${SERVICE_NAME}/CODEX_VIOLATIONS_MANIFEST.md (detailed list of ALL violations to fix)

**Critical Requirements**:

1. **Navigate to service directory**:
   \`\`\`bash
   cd ${SERVICE_NAME}
   \`\`\`

2. **Read CODEX_VIOLATIONS_MANIFEST.md** - it contains the complete list of ALL violations:
   - Exact file paths and line numbers
   - Violation types (print(), os.getenv(), imports, etc.)
   - Fix instructions for each type
   - **YOU MUST FIX EVERY VIOLATION LISTED** - the manifest is comprehensive

3. **Read the issue body above** for additional context

4. **Fix ALL violations** listed in CODEX_VIOLATIONS_MANIFEST.md
   - Do not skip any files (including examples/ directory)
   - Do not assume any files are exempt
   - Fix every single violation documented

5. **Install dependencies** (if in a clone environment):
   \`\`\`bash
   # Install unified-trading-library if available in workspace
   if [ -d "../unified-trading-library" ]; then
       cd ../unified-trading-library && uv pip install -e . && cd ../${SERVICE_NAME}
   fi
   \`\`\`

6. **Run quality gates** (ALL 4 phases MUST pass):
   \`\`\`bash
   bash scripts/quality-gates.sh --no-fix
   \`\`\`

   **CRITICAL**: This runs 4 phases - ALL must pass:
   - [1/4] Config validation ✅
   - [2/4] Linting (ruff format + check) ✅
   - [3/4] Tests (unit + smoke) ✅
   - [4/4] Codex compliance (print, os.getenv, imports, asyncio, etc.) ✅

   **DO NOT claim success unless you see**:
   \`\`\`
   ✅ QUALITY GATES PASSED
   \`\`\`

   If any phase fails, fix the issues and run again until ALL pass.

7. **Commit with issue reference**:
   \`\`\`bash
   bash scripts/quickmerge.sh "Fixes #${ACTUAL_ISSUE_NUMBER}: <SHORT_DESCRIPTION>" --files "<space-separated-files>"
   \`\`\`

   **CRITICAL**: Use \`Fixes #${ACTUAL_ISSUE_NUMBER}\` in commit message (PR auto-closes issue on merge in ${ISSUE_REPO})

**Success Criteria**:
- [ ] ALL violations in CODEX_VIOLATIONS_MANIFEST.md are fixed (including examples/ directory)
- [ ] Quality gates pass with explicit "✅ QUALITY GATES PASSED" message
- [ ] All 4 phases passed: Config ✅, Linting ✅, Tests ✅, Codex ✅
- [ ] Quickmerge creates PR with correct issue reference
- [ ] PR title/body contains: "Fixes #${ACTUAL_ISSUE_NUMBER}"

**DO NOT**:
- Skip quality gates
- Push directly to main
- Commit without --files flag
- Leave any violations unfixed

**Verification**:
After quickmerge completes, verify:
\`\`\`bash
# Check PR was created in correct repo
gh pr list --repo ${ISSUE_REPO}

# Verify PR references the issue
gh pr view <PR_NUMBER> --repo ${ISSUE_REPO} | grep "Fixes.*#${ACTUAL_ISSUE_NUMBER}"
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

# Retry wrapper for cursor agent (handles race conditions on config file)
run_cursor_agent_with_retry() {
    local max_retries=3
    local retry_count=0
    local wait_time=2

    while [ $retry_count -lt $max_retries ]; do
        if [ $retry_count -gt 0 ]; then
            echo "⚠️  Retry $retry_count/$max_retries (waiting ${wait_time}s)..."
            sleep $wait_time
            wait_time=$((wait_time * 2))  # Exponential backoff
        fi

        # Try to run cursor agent
        if "$@"; then
            return 0
        fi

        local exit_code=$?

        # Check if it's the config file race condition error
        if grep -q "ENOENT.*cli-config.json" /tmp/cursor-agent-error.log 2>/dev/null; then
            echo "⚠️  Config file race condition detected, retrying..."
            retry_count=$((retry_count + 1))
            continue
        fi

        # Other errors, don't retry
        return $exit_code
    done

    echo "❌ Failed after $max_retries retries"
    return 1
}

# Safe cursor agent wrapper (with file locking to prevent race conditions)
SAFE_WRAPPER="$(dirname "$0")/safe-cursor-agent.sh"
if [ -f "$SAFE_WRAPPER" ]; then
    CURSOR_CMD="bash $SAFE_WRAPPER"
else
    CURSOR_CMD="cursor agent"
    echo "⚠️  Safe wrapper not found, using direct cursor agent (may have race conditions)"
fi

# Execute cursor agent
if [ "$INTERACTIVE" = true ]; then
    # Interactive mode
    if [ -n "$MODEL" ]; then
        $CURSOR_CMD \
            --force \
            --workspace "$WORKSPACE_ROOT" \
            --model "$MODEL" \
            "$AGENT_PROMPT"
    else
        $CURSOR_CMD \
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
            $CURSOR_CMD \
                --print \
                --force \
                --workspace "$WORKSPACE_ROOT" \
                --model "$MODEL" \
                --output-format "$OUTPUT_FORMAT" \
                "$AGENT_PROMPT" | python3 "$PARSER"
        else
            $CURSOR_CMD \
                --print \
                --force \
                --workspace "$WORKSPACE_ROOT" \
                --output-format "$OUTPUT_FORMAT" \
                "$AGENT_PROMPT" | python3 "$PARSER"
        fi
    else
        # Normal: clean text output
        if [ -n "$MODEL" ]; then
            $CURSOR_CMD \
                --print \
                --force \
                --workspace "$WORKSPACE_ROOT" \
                --model "$MODEL" \
                "$AGENT_PROMPT"
        else
            $CURSOR_CMD \
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
    echo "1. Verify PR was created: gh pr list --repo ${ISSUE_REPO}"
    echo "2. Check issue status: gh issue view ${ACTUAL_ISSUE_NUMBER} --repo ${ISSUE_REPO}"
    echo "3. Monitor PR merge and issue auto-close"
else
    echo "❌ Agent failed with exit code: $EXIT_CODE"
    echo ""
    echo "Check the output above for errors"
fi
echo "========================================================================"

exit $EXIT_CODE
