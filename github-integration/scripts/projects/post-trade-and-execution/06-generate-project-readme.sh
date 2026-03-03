#!/bin/bash
#
# Generate Project README
#
# Creates comprehensive README documentation for the Post-Trade and Execution project.
#
# Usage:
#   bash 06-generate-project-readme.sh --project 7 > PROJECT_README.md
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
            echo "Usage: bash 06-generate-project-readme.sh --project <number> [--org <org>]"
            echo ""
            echo "Options:"
            echo "  --project  GitHub project number (required)"
            echo "  --org      GitHub organization/user (default: IggyIkenna)"
            echo ""
            echo "Example:"
            echo "  bash 06-generate-project-readme.sh --project 7 > PROJECT_README.md"
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
    echo "Error: --project is required" >&2
    exit 1
fi

# Fetch project data
PROJECT_DATA=$(gh api graphql -f query='
query {
  user(login: "'"$ORG"'") {
    projectV2(number: '"$PROJECT_NUMBER"') {
      id
      title
      url
      shortDescription
    }
  }
}' 2>/dev/null || echo "")

if [ -z "$PROJECT_DATA" ] || [ "$PROJECT_DATA" == "null" ]; then
    echo "Error: Project #$PROJECT_NUMBER not found" >&2
    exit 1
fi

PROJECT_TITLE=$(echo "$PROJECT_DATA" | jq -r '.data.user.projectV2.title')
PROJECT_URL=$(echo "$PROJECT_DATA" | jq -r '.data.user.projectV2.url')

# Generate README
cat <<EOF
# Project: $PROJECT_TITLE

**Project #$PROJECT_NUMBER**
**Owner:** $ORG
**URL:** $PROJECT_URL

---

## Overview

**Goal**: Split monolithic unified-trading-library into focused libraries while preserving cloud-agnostic foundation.

**Approach**: Option A (Full Separation) with phased delivery over 12 days.

**Key Deliverables**:
1. **Phase 1**: PubSub abstraction + unified-events-interface (coordination + observability)
2. **Phase 2**: unified-config-interface (centralized config with hot-reload)
3. **Phase 3**: unified-market-interface (market data feed normalization)
4. **Phase 4**: unified-order-interface (order execution normalization)

**Related Documentation:**
- Epic Overview: \`unified-trading-codex/11-project-management/epics/post-trade-and-execution-epic.md\`
- Epic Breakdown: \`unified-trading-codex/11-project-management/epic-breakdowns/epic-post-trade-and-execution.md\`
- Infrastructure Updates: \`~/.cursor/plans/infrastructure-updates-for-library-refactor.md\`

---

## Project Structure

### Repositories (5 total)

**New Libraries (4):**
- \`unified-events-interface\` - Observability (Cloud Logging) + Coordination (PubSub) events
- \`unified-config-interface\` - Centralized configuration with hot-reload
- \`unified-market-interface\` - Public market data feed normalization
- \`unified-order-interface\` - Private order execution normalization

**Existing:**
- \`unified-trading-library\` - Cloud-agnostic API (GCP ↔ AWS translation)

### Issue Breakdown (~20 subtasks)

- **Phase 0 (Infrastructure)**: 4 issues
  - Artifact Registry Python repo
  - IAM permissions
  - Local dev setup docs
  - Publish workflow template

- **Phase 1 (Events Interface)**: ~13 issues
  - PubSub abstraction in unified-trading-library
  - Create unified-events-interface repo
  - Migrate event logging code
  - Add re-exports for backward compat

- **Phase 2 (Config Interface)**: ~13 issues
  - Create unified-config-interface repo
  - Migrate config code
  - Add hot-reload capabilities

- **Phase 3 (Market Interface)**: ~13 issues
  - Create unified-market-interface repo
  - Migrate market data clients
  - Normalize feed interfaces

- **Phase 4 (Order Interface)**: ~8 issues
  - Create unified-order-interface repo
  - Migrate order execution clients
  - Normalize order interfaces

---

## Labels

### Project Label
- \`POST-TRADE-AND-EXECUTION\` - All issues in this project

### Priority Labels
- \`P0-critical\` - Blocking, must fix immediately
- \`P1-high\` - Important, fix soon
- \`P2-medium\` - Normal priority
- \`P3-low\` - Low priority, nice to have

### Type Labels
- \`epic\` - Large feature or initiative
- \`task\` - Standard work item
- \`subtask\` - Part of a larger task

---

## Workflows

**Configured Workflows:**
1. **Auto-add to project** - Issues with \`POST-TRADE-AND-EXECUTION\` label auto-add
2. **Auto-add sub-issues** - Sub-issues auto-add to project
3. **Item closed** - Closed issues move to 'Done' status
4. **Pull request merged** - Issues auto-close when PRs merge ⭐
5. **Auto-close issue** - Project items close when PRs merge
6. **Auto-archive items** - Completed items archive after 30 days
7. **Item added** - New items default to 'Todo' status
8. **PR linked** - Issues move to 'In Progress' when PR linked

**Configuration URL:** $PROJECT_URL/settings/workflows

---

## Progress Tracking

### View Project
\`\`\`bash
# Web UI
gh project view $PROJECT_NUMBER --owner $ORG --web

# Terminal
gh project view $PROJECT_NUMBER --owner $ORG
\`\`\`

### Filter Issues
\`\`\`bash
# All issues in project
gh issue list --label POST-TRADE-AND-EXECUTION --state all

# By priority
gh issue list --label POST-TRADE-AND-EXECUTION,P0-critical --state open

# By repo
gh issue list --repo $ORG/unified-events-interface --label POST-TRADE-AND-EXECUTION
\`\`\`

### Check PRs
\`\`\`bash
# All PRs for this project
gh pr list --label POST-TRADE-AND-EXECUTION --state open

# PRs ready for review
gh pr list --label POST-TRADE-AND-EXECUTION --state open --search "review:required"
\`\`\`

---

## Development Workflow

### 1. Pick an Issue
\`\`\`bash
# View available issues
gh project item-list $PROJECT_NUMBER --owner $ORG --format json | jq '[.[] | select(.status == "Todo")] | .[0]'

# Assign to yourself
gh issue view <ISSUE_NUMBER> --repo $ORG/<REPO> --web
# Click "Assign to yourself"
\`\`\`

### 2. Create Branch
\`\`\`bash
cd <repo>
git checkout main
git pull
git checkout -b <issue-number>-<descriptive-name>
\`\`\`

### 3. Implement Changes
- Follow codex standards (see \`unified-trading-codex/06-coding-standards/\`)
- Run quality gates: \`bash scripts/quality-gates.sh\`
- Commit with descriptive messages

### 4. Create PR
\`\`\`bash
# Push branch
git push -u origin HEAD

# Create PR (includes "Closes #<ISSUE_NUMBER>" in body)
gh pr create --title "<descriptive title>" --body "## Summary
<1-3 bullet points>

Closes #<ISSUE_NUMBER>

## Test plan
- [ ] Quality gates pass
- [ ] Tests added/updated
- [ ] Manual testing complete"
\`\`\`

### 5. Auto-Merge
- GitHub Actions quality gates run automatically
- PR auto-merges when checks pass (if enabled)
- Issue auto-closes when PR merges ⭐

---

## Key Architectural Decisions

### Backward Compatibility: Transitive Dependencies

**Services work with ZERO code changes:**

1. **unified-trading-library** lists new libraries as dependencies
2. Services depend on unified-trading-library
3. Services get new libraries **transitively** via \`uv pip install\`
4. **Re-exports** provide backward compatibility for 6 months

\`\`\`python
# Services continue using old imports (works via re-exports)
from unified_trading_library import log_event  # ✅ Works

# New imports also work (for early adopters)
from unified_events_interface import log_event  # ✅ Also works
\`\`\`

### Python Package Distribution

**GitHub Packages does NOT support Python** - using GCP Artifact Registry instead:

\`\`\`bash
# New libraries published to:
asia-northeast1-python.pkg.dev/${GCP_PROJECT_ID}/unified-libraries/

# One-time local setup:
gcloud artifacts print-settings python \\
    --project=${GCP_PROJECT_ID} \\
    --repository=unified-libraries \\
    --location=asia-northeast1
\`\`\`

### Cloud-Agnosticism

**Only unified-trading-library touches cloud providers**:
- New libraries use unified-trading-library abstractions internally
- Services continue to be cloud-agnostic
- GCP ↔ AWS translation stays in one place

---

## Troubleshooting

### Issue not in project
\`\`\`bash
# Add manually
gh project item-add $PROJECT_NUMBER --owner $ORG --url <ISSUE_URL>
\`\`\`

### PR not closing issue
- Ensure PR body contains "Closes #<ISSUE_NUMBER>" or "Fixes #<ISSUE_NUMBER>"
- Check workflow "Pull request merged → Close linked issues" is configured
- Verify PR merged to main branch (not just closed)

### Quality gates failing
\`\`\`bash
# Run locally
cd <service>
bash scripts/quality-gates.sh

# Fix issues
bash scripts/quality-gates.sh  # Auto-fixes formatting
bash scripts/quality-gates.sh --no-fix  # Verify passes
\`\`\`

### Can't install new libraries locally
\`\`\`bash
# Configure Artifact Registry auth
gcloud auth application-default login
gcloud artifacts print-settings python \\
    --project=${GCP_PROJECT_ID} \\
    --repository=unified-libraries \\
    --location=asia-northeast1

# Then install
uv pip install unified-events-interface
\`\`\`

---

## Success Criteria

- ✅ All 20 subtasks completed
- ✅ 4 new library repos created and published
- ✅ unified-trading-library refactored with re-exports
- ✅ All services work with ZERO code changes (backward compat)
- ✅ Quality gates passing across all repos
- ✅ Infrastructure updated (Artifact Registry, workflows, docs)
- ✅ Live testing ready by Mar 15, 2026

---

## Resources

**Codex Documentation:**
- Architecture: \`unified-trading-codex/04-architecture/\`
- Coding Standards: \`unified-trading-codex/06-coding-standards/\`
- Infrastructure: \`unified-trading-codex/05-infrastructure/\`

**GitHub:**
- Project Board: $PROJECT_URL
- All Issues: $PROJECT_URL?query=is%3Aopen

**Scripts:**
- Project setup: \`unified-trading-codex/11-project-management/github-integration/scripts/projects/post-trade-and-execution/\`

---

**Generated:** $(date '+%Y-%m-%d %H:%M:%S')
**Project:** #$PROJECT_NUMBER
EOF
