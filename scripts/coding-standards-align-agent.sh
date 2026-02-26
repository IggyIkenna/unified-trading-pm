#!/bin/bash
# Coding Standards Alignment Agent
#
# Propagates canonical rules from SSOT docs to the rest of 06-coding-standards.
# Use when: You've updated README, config-types, quality-gates, or QUALITY_GATES_COMPREHENSIVE
# and want to ensure all other docs (STANDARDS, configuration-management, audit-compliance, etc.)
# are aligned.
#
# Usage:
#   ./coding-standards-align-agent.sh              # Align all docs (uses Cursor agent if available)
#   ./coding-standards-align-agent.sh --check-only # Report contradictions only, no edits
#   ./coding-standards-align-agent.sh --dry-run    # Show what would be updated
#
# Human rule: When updating coding standards, run this agent to propagate.
# Eventually: Add to GitHub workflow on changes to unified-trading-codex/06-coding-standards/

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CODEX_ROOT="$WORKSPACE_ROOT/unified-trading-codex"
STANDARDS_DIR="$CODEX_ROOT/06-coding-standards"
SSOT_CONFIG="$SCRIPT_DIR/CODING_STANDARDS_SSOT.config"
PARSER="$WORKSPACE_ROOT/.cursor/plans/tasks_claude_code/simple-parser.py"

CHECK_ONLY=false
DRY_RUN=false
for arg in "$@"; do
    [[ "$arg" == "--check-only" ]] && CHECK_ONLY=true
    [[ "$arg" == "--dry-run" ]] && DRY_RUN=true
done

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "📐 Coding Standards Alignment Agent"
echo "   SSOT: $(tr '\n' ' ' < "$SSOT_CONFIG" 2>/dev/null || echo 'README, config-types, quality-gates, QUALITY_GATES_COMPREHENSIVE')"
echo "   Target: $STANDARDS_DIR/"
echo ""

# Build SSOT file list
SSOT_FILES=""
while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" ]] && continue
    [[ "$line" =~ ^# ]] && continue
    if [[ -f "$STANDARDS_DIR/$line" ]]; then
        SSOT_FILES="${SSOT_FILES}${STANDARDS_DIR}/${line} "
    fi
done < "$SSOT_CONFIG" 2>/dev/null || true

[[ -z "$SSOT_FILES" ]] && SSOT_FILES="${STANDARDS_DIR}/README.md ${STANDARDS_DIR}/config-types.md ${STANDARDS_DIR}/quality-gates.md ${STANDARDS_DIR}/QUALITY_GATES_COMPREHENSIVE.md"

# Docs to scan for contradictions (exclude SSOT) - used in ALIGN_PROMPT find command
# shellcheck disable=SC2034
SCAN_DIRS="$STANDARDS_DIR"
# shellcheck disable=SC2034
EXCLUDE_PATTERN="README\.md|config-types\.md|quality-gates\.md|QUALITY_GATES_COMPREHENSIVE\.md"

ALIGN_PROMPT="WORKSPACE: $WORKSPACE_ROOT
CODEX: $CODEX_ROOT
STANDARDS_DIR: $STANDARDS_DIR

TASK: Coding Standards Alignment

SSOT (canonical rules — DO NOT change these):
- $STANDARDS_DIR/README.md
- $STANDARDS_DIR/config-types.md
- $STANDARDS_DIR/quality-gates.md
- $STANDARDS_DIR/QUALITY_GATES_COMPREHENSIVE.md

CANONICAL RULES (from SSOT — use these to fix others):
1. Config: UnifiedCloudConfig from unified-config-interface (NOT UnifiedCloudServicesConfig)
2. Logging: setup_events(), log_event() from unified-events-interface (NOT get_logger from unified_cloud_services)
3. Coverage: 35% min (quality gates), 80% audit goal (NOT 70-80% as blocking)
4. File size: Service 900/700, Library 1500/1200 (per templates)
5. Formatting ref: formatting-standards.md, README (NOT FORMATTING_STANDARDS_MASTER.md — does not exist)
6. E501: NOT ignored (line length enforced)

SCAN these docs for contradictions:

$(find "$STANDARDS_DIR" -maxdepth 1 -name '*.md' ! -name 'README.md' ! -name 'config-types.md' ! -name 'quality-gates.md' ! -name 'QUALITY_GATES_COMPREHENSIVE.md' -exec basename {} \; 2>/dev/null | grep -v CONFLICT_REPORT | tr '\n' ' ')

STEPS:
1. Read each scanned doc
2. Find any references to: UnifiedCloudServicesConfig, get_logger, setup_cloud_logging, FORMATTING_STANDARDS_MASTER, --cov-fail-under=70/80 (as blocking)
3. For each contradiction: UPDATE the doc to match SSOT
4. Fix broken references (e.g. FORMATTING_STANDARDS_MASTER.md → formatting-standards.md)
5. Add clarification to audit-compliance if needed: \"Quality gates enforce X; this doc is aspirational\"

RESTRICTIONS:
- ONLY edit files in $STANDARDS_DIR/
- DO NOT edit the 4 SSOT files
- DO NOT edit CONFLICT_REPORT.md (it's a snapshot)
- Preserve document structure and intent; only fix contradictory values

OUTPUT:
- List each file updated and what changed
- If no contradictions found, say \"No contradictions found\"
"

if [[ "$CHECK_ONLY" == true ]]; then
    echo "🔍 Check-only mode: Report contradictions, no edits."
    echo ""
    ALIGN_PROMPT="$ALIGN_PROMPT

MODE: CHECK ONLY. Do NOT make any edits. Report contradictions only.
"
fi

if [[ "$DRY_RUN" == true ]]; then
    echo "🔍 Dry-run: Show what would be updated."
    echo ""
    ALIGN_PROMPT="$ALIGN_PROMPT

MODE: DRY RUN. Do NOT make edits. List what would be changed.
"
fi

# Check for agent CLI
if ! command -v agent &>/dev/null; then
    echo -e "${YELLOW}⚠️  'agent' CLI not found. Run manually in Cursor:${NC}"
    echo ""
    echo "  1. Open: unified-trading-codex/06-coding-standards/"
    echo "  2. Use this prompt:"
    echo ""
    echo "---"
    echo "$ALIGN_PROMPT"
    echo "---"
    echo ""
    echo "  Or install: https://github.com/cursor/agent"
    exit 0
fi

# Check for API key (never write to world-readable temp file)
if [ -z "${CURSOR_API_KEY:-}" ]; then
    if [ -n "${GCP_PROJECT_ID:-}" ]; then
        echo "Getting API key from Secret Manager..."
        CURSOR_API_KEY=$(gcloud secrets versions access latest --secret=cursor-api-key --project="$GCP_PROJECT_ID" 2>/dev/null) || true
        [ -n "${CURSOR_API_KEY:-}" ] && export CURSOR_API_KEY
    fi
    if [ -z "${CURSOR_API_KEY:-}" ]; then
        echo -e "${YELLOW}⚠️  No CURSOR_API_KEY. Set GCP_PROJECT_ID and ensure gcloud auth, or: export CURSOR_API_KEY=\$(gh auth token 2>/dev/null || echo 'your-key')${NC}"
        exit 1
    fi
fi

export PATH="$HOME/.local/bin:$PATH"

echo "Running alignment agent..."
if [ -f "$PARSER" ]; then
    agent --api-key "$CURSOR_API_KEY" \
        --print \
        --model auto \
        --trust \
        --force \
        --output-format stream-json \
        --stream-partial-output \
        --workspace "$WORKSPACE_ROOT" \
        "$ALIGN_PROMPT" \
        2>&1 | python3 "$PARSER"
else
    agent --api-key "$CURSOR_API_KEY" \
        --print \
        --model auto \
        --trust \
        --force \
        --workspace "$WORKSPACE_ROOT" \
        "$ALIGN_PROMPT"
fi

exit_code=$?
echo ""
if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}✅ Coding Standards Alignment Agent completed${NC}"
else
    echo "❌ Alignment agent failed (exit code: $exit_code)"
fi
exit $exit_code
