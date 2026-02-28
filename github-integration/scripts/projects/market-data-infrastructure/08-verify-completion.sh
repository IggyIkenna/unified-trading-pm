#!/bin/bash
#
# Verify Market Data Infrastructure Project Completion
#
# Checks status of all 4 subtasks and generates completion report.
#
# Usage:
#   bash 08-verify-completion.sh [--issue-manifest issue-manifest.json]
#

set -euo pipefail

ORG="IggyIkenna"
ISSUE_MANIFEST="${1:-issue-manifest.json}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --issue-manifest)
            ISSUE_MANIFEST="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: bash 08-verify-completion.sh [--issue-manifest <file>]"
            echo ""
            echo "Options:"
            echo "  --issue-manifest <file>  Path to issue manifest (default: issue-manifest.json)"
            echo ""
            echo "Example:"
            echo "  bash 08-verify-completion.sh --issue-manifest issue-manifest.json"
            exit 0
            ;;
        *)
            ISSUE_MANIFEST="$1"
            shift
            ;;
    esac
done

if [ ! -f "$ISSUE_MANIFEST" ]; then
    echo "❌ Error: Issue manifest not found: $ISSUE_MANIFEST"
    echo ""
    echo "Run Stage 3 first:"
    echo "  python 02-create-issues.py --org $ORG --epic-file ../../epic-breakdowns/epic-market-data-infrastructure.md --apply"
    exit 1
fi

echo "========================================="
echo "Market Data Infrastructure - Status Report"
echo "========================================="
echo ""

# Initialize counters
TOTAL=0
OPEN=0
CLOSED=0
IN_PROGRESS=0
ERRORS=0

# Phase counters
declare -A PHASE_TOTAL
declare -A PHASE_OPEN
declare -A PHASE_CLOSED
declare -A PHASE_IN_PROGRESS

for phase in 0 1 2 3 4; do
    PHASE_TOTAL[$phase]=0
    PHASE_OPEN[$phase]=0
    PHASE_CLOSED[$phase]=0
    PHASE_IN_PROGRESS[$phase]=0
done

# Repo counters
declare -A REPO_TOTAL
declare -A REPO_OPEN
declare -A REPO_CLOSED
declare -A REPO_IN_PROGRESS

echo "| Phase | Repo | Issue | State | Subtask | Priority |"
echo "|-------|------|-------|-------|---------|----------|"

# Read repos from manifest
REPOS=$(jq -r 'keys[]' "$ISSUE_MANIFEST")

for repo in $REPOS; do
    # Initialize repo counters
    REPO_TOTAL[$repo]=0
    REPO_OPEN[$repo]=0
    REPO_CLOSED[$repo]=0
    REPO_IN_PROGRESS[$repo]=0

    # Get number of issues for this repo
    ISSUE_COUNT=$(jq -r ".[\"$repo\"] | length" "$ISSUE_MANIFEST")

    # Process each issue
    for i in $(seq 0 $((ISSUE_COUNT - 1))); do
        ISSUE_NUMBER=$(jq -r ".[\"$repo\"][$i].number" "$ISSUE_MANIFEST")
        SUBTASK_ID=$(jq -r ".[\"$repo\"][$i].subtask_id" "$ISSUE_MANIFEST")
        ISSUE_TITLE=$(jq -r ".[\"$repo\"][$i].title" "$ISSUE_MANIFEST")

        # Skip if no issue number
        if [ "$ISSUE_NUMBER" == "null" ] || [ -z "$ISSUE_NUMBER" ]; then
            continue
        fi

        # Extract phase from subtask ID (e.g., "Subtask 1.2.3" → phase 1)
        PHASE=$(echo "$SUBTASK_ID" | cut -d'.' -f1 | sed 's/Subtask //g')

        # Extract priority from title (look for P0-P3)
        if [[ "$ISSUE_TITLE" == *"P0-critical"* ]]; then
            PRIORITY="P0"
        elif [[ "$ISSUE_TITLE" == *"P1-high"* ]]; then
            PRIORITY="P1"
        elif [[ "$ISSUE_TITLE" == *"P2-medium"* ]]; then
            PRIORITY="P2"
        elif [[ "$ISSUE_TITLE" == *"P3-low"* ]]; then
            PRIORITY="P3"
        else
            PRIORITY="-"
        fi

        # Get issue state from GitHub
        ISSUE_DATA=$(gh issue view "$ISSUE_NUMBER" \
            --repo "$ORG/$repo" \
            --json state,labels \
            --jq '{state: .state, labels: [.labels[].name]}' 2>/dev/null || echo '{"state":"ERROR","labels":[]}')

        STATE=$(echo "$ISSUE_DATA" | jq -r '.state // "ERROR"')
        LABELS=$(echo "$ISSUE_DATA" | jq -r '.labels[]' | tr '\n' ',' | sed 's/,$//')

        # Count totals
        TOTAL=$((TOTAL + 1))
        REPO_TOTAL[$repo]=$((${REPO_TOTAL[$repo]} + 1))
        PHASE_TOTAL[$PHASE]=$((${PHASE_TOTAL[$PHASE]:-0} + 1))

        # Determine status
        if [ "$STATE" = "OPEN" ]; then
            # Check if in progress (has linked PR)
            if [[ "$LABELS" == *"in-progress"* ]] || gh pr list --repo "$ORG/$repo" --search "is:open linked:issue-$ISSUE_NUMBER" --json number --jq '.[0].number' &>/dev/null; then
                IN_PROGRESS=$((IN_PROGRESS + 1))
                REPO_IN_PROGRESS[$repo]=$((${REPO_IN_PROGRESS[$repo]} + 1))
                PHASE_IN_PROGRESS[$PHASE]=$((${PHASE_IN_PROGRESS[$PHASE]:-0} + 1))
                echo "| $PHASE | $repo | #$ISSUE_NUMBER | 🔄 IN_PROGRESS | $SUBTASK_ID | $PRIORITY |"
            else
                OPEN=$((OPEN + 1))
                REPO_OPEN[$repo]=$((${REPO_OPEN[$repo]} + 1))
                PHASE_OPEN[$PHASE]=$((${PHASE_OPEN[$PHASE]:-0} + 1))
                echo "| $PHASE | $repo | #$ISSUE_NUMBER | 🟡 OPEN | $SUBTASK_ID | $PRIORITY |"
            fi
        elif [ "$STATE" = "CLOSED" ]; then
            CLOSED=$((CLOSED + 1))
            REPO_CLOSED[$repo]=$((${REPO_CLOSED[$repo]} + 1))
            PHASE_CLOSED[$PHASE]=$((${PHASE_CLOSED[$PHASE]:-0} + 1))
            echo "| $PHASE | $repo | #$ISSUE_NUMBER | ✅ CLOSED | $SUBTASK_ID | $PRIORITY |"
        else
            ERRORS=$((ERRORS + 1))
            echo "| $PHASE | $repo | #$ISSUE_NUMBER | ❌ ERROR | $SUBTASK_ID | $PRIORITY |"
        fi
    done
done

echo ""
echo "========================================="
echo "Summary"
echo "========================================="
echo ""
echo "Overall Progress:"
echo "  Total subtasks: $TOTAL"
echo "  Completed: $CLOSED / $TOTAL ($(awk "BEGIN {printf \"%.1f\", ($CLOSED / $TOTAL) * 100}")%)"
echo "  In Progress: $IN_PROGRESS"
echo "  Open: $OPEN"
echo "  Errors: $ERRORS"
echo ""

echo "By Phase:"
for phase in 0 1 2 3 4; do
    total=${PHASE_TOTAL[$phase]:-0}
    if [ $total -gt 0 ]; then
        closed=${PHASE_CLOSED[$phase]:-0}
        in_progress=${PHASE_IN_PROGRESS[$phase]:-0}
        open=${PHASE_OPEN[$phase]:-0}
        pct=$(awk "BEGIN {printf \"%.1f\", ($closed / $total) * 100}")

        case $phase in
            0) phase_name="Phase 0 (Infrastructure)" ;;
            1) phase_name="Phase 1 (Events Interface)" ;;
            2) phase_name="Phase 2 (Config Interface)" ;;
            3) phase_name="Phase 3 (Market Interface)" ;;
            4) phase_name="Phase 4 (Order Interface)" ;;
        esac

        echo "  $phase_name: $closed/$total ($pct%)"
        [ $in_progress -gt 0 ] && echo "    In Progress: $in_progress"
        [ $open -gt 0 ] && echo "    Open: $open"
    fi
done
echo ""

echo "By Repo:"
for repo in $REPOS; do
    total=${REPO_TOTAL[$repo]:-0}
    if [ $total -gt 0 ]; then
        closed=${REPO_CLOSED[$repo]:-0}
        in_progress=${REPO_IN_PROGRESS[$repo]:-0}
        open=${REPO_OPEN[$repo]:-0}
        pct=$(awk "BEGIN {printf \"%.1f\", ($closed / $total) * 100}")

        echo "  $repo: $closed/$total ($pct%)"
        [ $in_progress -gt 0 ] && echo "    In Progress: $in_progress"
        [ $open -gt 0 ] && echo "    Open: $open"
    fi
done
echo ""

# Completion status
if [ $OPEN -eq 0 ] && [ $IN_PROGRESS -eq 0 ] && [ $ERRORS -eq 0 ]; then
    echo "========================================="
    echo "🎉 PROJECT COMPLETE!"
    echo "========================================="
    echo ""
    echo "All 4 subtasks resolved. Market Data Infrastructure is complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Verify all new libraries published to Artifact Registry:"
    echo "     gcloud artifacts packages list --repository=unified-libraries --location=asia-northeast1"
    echo ""
    echo "  2. Test backward compatibility (services should work with zero changes)"
    echo ""
    echo "  3. Update documentation if needed"
    echo ""
    echo "  4. Archive project:"
    echo "     gh project view 6 --owner $ORG --web"
    echo ""
elif [ $OPEN -gt 0 ]; then
    echo "========================================="
    echo "📋 Next Steps"
    echo "========================================="
    echo ""

    # Suggest running remaining tasks by phase
    for phase in 0 1 2 3 4; do
        open=${PHASE_OPEN[$phase]:-0}
        if [ $open -gt 0 ]; then
            case $phase in
                0) phase_name="Infrastructure" ;;
                1) phase_name="Events Interface" ;;
                2) phase_name="Config Interface" ;;
                3) phase_name="Market Interface" ;;
                4) phase_name="Order Interface" ;;
            esac

            echo "Phase $phase ($phase_name) - $open tasks remaining:"
            echo "  bash run-batch-fix.sh --model auto --phase $phase --max-parallel 3"
            echo ""
        fi
    done

    echo "Or run all remaining tasks:"
    echo "  bash run-batch-fix.sh --model auto --max-parallel 3"
    echo ""
    echo "Or work on individual tasks locally (see AGENT_PROMPT.md)"
else
    echo "========================================="
    echo "⏳ In Progress"
    echo "========================================="
    echo ""
    echo "$IN_PROGRESS tasks currently in progress."
    echo ""
    echo "Monitor PRs:"
    echo "  gh pr list --label MARKET-DATA-INFRASTRUCTURE --state open"
    echo ""
    echo "Check again after PRs merge:"
    echo "  bash 08-verify-completion.sh"
fi

echo ""
echo "========================================="
