# Market Data Infrastructure - Project Setup Scripts

**Project**: GitHub Project #8 (TBD) **Epic**: Market Data Infrastructure **Issues**: 4 subtasks in 1 repo
(market-tick-data-handler)

---

## Overview

This directory contains scripts to automate GitHub Project setup for the Market Data Infrastructure epic.

**What this does:**

1. Creates GitHub Project with proper fields and views
2. Creates 1 new service repository (market-tick-data-handler)
3. Parses epic breakdown → 4 GitHub issues in market-tick-data-handler
4. Links all issues to the project
5. Provides workflow configuration instructions
6. Validates setup
7. Generates project documentation

**Service:**

- NEW: market-tick-data-handler (batch + live modes for market data ingestion)

**Total time:** 20-30 minutes

---

## Prerequisites

### Required Tools

```bash
# GitHub CLI (authenticated)
gh --version  # Should be v2.0.0+
gh auth status  # Should show: repo, project, workflow scopes

# Python 3.13+
python3 --version

# jq (JSON processor)
jq --version
```

### Required Access

- GitHub user: `IggyIkenna`
- Permissions: Create projects, create repos, create issues, configure workflows
- GH_TOKEN with scopes: `repo`, `project`, `workflow`

---

## Quick Start

### Option A: Run All Stages Sequentially

```bash
cd unified-trading-codex/11-project-management/github-integration/scripts/projects/market-data-infrastructure

# Stage 1: Create project
bash 01-create-project.sh --org IggyIkenna
# Output: Project #8 created

# Stage 2: Create repo
gh repo create "IggyIkenna/market-tick-data-handler" --private \
    --description "Part of Market Data Infrastructure - Unified market data ingestion (batch + live)" \
    --gitignore Python --license MIT

# Stage 3: Create issues (dry run first)
python 02-create-issues.py \
    --org IggyIkenna \
    --epic-file "../../epic-breakdowns/epic-market-data-infrastructure.md" \
    --dry-run

# Review output, then apply
python 02-create-issues.py \
    --org IggyIkenna \
    --epic-file "../../epic-breakdowns/epic-market-data-infrastructure.md" \
    --apply

# Stage 4: Link issues to project
bash 03-link-issues-to-project.sh --project 8 --issue-manifest issue-manifest.json

# Stage 5: Configure workflows (interactive)
bash 04-copy-workflows.sh --from 5 --to 6
# Follow interactive prompts to configure 8 workflows manually

# Stage 6: Verify setup
bash 05-verify-setup.sh --project 8

# Stage 7: Generate docs
bash 06-generate-project-readme.sh --project 8 > PROJECT_README.md
```

### Option B: Manual (Stage by Stage)

Follow the detailed instructions below for each stage.

---

## Stage 1: Create GitHub Project (2 min)

**Script:** `01-create-project.sh`

**What it does:**

- Creates GitHub Project "Market Data Infrastructure"
- Adds custom fields: Priority, Type, Estimated Hours
- Returns project number (e.g., #6)

**Usage:**

```bash
bash 01-create-project.sh --org IggyIkenna
```

**Output:**

```
✅ Project created: #6
   URL: https://github.com/users/IggyIkenna/projects/6

Project Number: 6
```

**Save the project number** - you'll need it for subsequent stages.

---

## Stage 2: Create Repositories (5 min manual, 2 min automated)

**Goal:** Create 4 new library repos

### Option A: Manual (GitHub UI)

1. Go to https://github.com/new
2. Create each repo:
   - Name: `unified-trading-library`
   - Private: ✅
   - Initialize with README: ✅
   - .gitignore: Python
   - License: MIT
3. Repeat for: `unified-config-interface`, `unified-market-interface`, `unified-order-interface`

### Option B: Automated (gh CLI)

```bash
for repo in unified-trading-library unified-config-interface \
            unified-market-interface unified-order-interface; do
    gh repo create "IggyIkenna/$repo" \
        --private \
        --description "Part of Market Data Infrastructure - cloud-agnostic $repo" \
        --gitignore Python \
        --license MIT

    echo "✅ Created $repo"
    sleep 1
done
```

**Verify:**

```bash
gh repo list IggyIkenna | grep unified-
```

---

## Stage 3: Create Issues from Epic (15 min)

**Script:** `02-create-issues.py`

**What it does:**

- Parses `epic-market-data-infrastructure.md`
- Extracts 4 subtasks with metadata
- Auto-detects target repo from "Files to modify" field
- Creates GitHub issues in appropriate repos
- Generates `issue-manifest.json` for Stage 4

**Usage:**

```bash
# Dry run first (preview)
python 02-create-issues.py \
    --org IggyIkenna \
    --epic-file "../../epic-breakdowns/epic-market-data-infrastructure.md" \
    --dry-run

# Review output, then apply
python 02-create-issues.py \
    --org IggyIkenna \
    --epic-file "../../epic-breakdowns/epic-market-data-infrastructure.md" \
    --apply
```

**Output:**

```
📊 Parsing epic breakdown...
   Found: 4 subtasks

   Distribution:
     - unified-trading-library: 10 issues
     - unified-config-interface: 10 issues
     - unified-market-interface: 12 issues
     - unified-order-interface: 12 issues
     - unified-trading-services: 7 issues

📋 Creating issues...
  [Creates 4 issues across 1 repo]

📝 Issue manifest saved to: issue-manifest.json
```

**Files created:**

- `issue-manifest.json` - Mapping of subtasks to issue numbers

---

## Stage 4: Link Issues to Project (2 min)

**Script:** `03-link-issues-to-project.sh`

**What it does:**

- Reads `issue-manifest.json` from Stage 3
- Adds all 4 issues to Project #8
- Sets default status: "Todo"

**Usage:**

```bash
bash 03-link-issues-to-project.sh \
    --project 8 \
    --issue-manifest issue-manifest.json
```

**Output:**

```
🔗 Linking 4 issues to Project #8...
  ✅ Added issue #1 to project
  ✅ Added issue #2 to project
  [... 49 more issues]

✅ Linked 4 issues to Project #8
   View: https://github.com/users/IggyIkenna/projects/6
```

---

## Stage 5: Copy Workflows from Project 5 (20 min)

**Script:** `04-copy-workflows.sh`

**What it does:**

- Fetches workflows from Project #5 (Initial Cleanup)
- Provides step-by-step manual instructions for each workflow
- **Critical:** Updates label filter from "cleanup" to "MARKET-DATA-INFRASTRUCTURE"

**Usage:**

```bash
bash 04-copy-workflows.sh --from 5 --to 6
```

**Interactive prompts:**

- Shows 8 workflows from template
- Provides exact configuration for each
- **Most critical:** "Pull request merged → Close linked issues"

**Workflows to configure:**

1. Auto-add to project (label: `MARKET-DATA-INFRASTRUCTURE`)
2. Auto-add sub-issues
3. Item closed → Set status to 'Done'
4. **Pull request merged → Close linked issues** ⭐
5. Auto-close issue
6. Auto-archive items (30 days)
7. Item added → Set status to 'Todo'
8. PR linked → Set status to 'In Progress'

**Manual steps:**

- Go to: https://github.com/users/IggyIkenna/projects/6/settings/workflows
- Follow instructions for each workflow (~2-3 min each)

---

## Stage 6: Verify Setup (1 min)

**Script:** `05-verify-setup.sh`

**What it does:**

- Validates project exists
- Counts issues (should be 51)
- Checks labels present
- Verifies workflows configured (should be 8)

**Usage:**

```bash
bash 05-verify-setup.sh --project 8
```

**Output:**

```
✅ Verification PASSED

Project: #6 - Market Data Infrastructure
  Issues: 51 ✅
  Labels: MARKET-DATA-INFRASTRUCTURE, P0-P3 ✅
  Workflows: 8 ✅

Ready to start development! 🚀
```

---

## Stage 7: Generate Project README (7 min)

**Script:** `06-generate-project-readme.sh`

**What it does:**

- Generates comprehensive project documentation
- Includes: overview, structure, workflows, progress tracking, troubleshooting

**Usage:**

```bash
bash 06-generate-project-readme.sh --project 8 > PROJECT_README.md

# Review and commit
less PROJECT_README.md
git add PROJECT_README.md
git commit -m "Add Market Data Infrastructure project README"
```

---

## Troubleshooting

### "gh: command not found"

```bash
# Install GitHub CLI
brew install gh  # macOS
# Or see: https://cli.github.com/

# Authenticate
gh auth login
```

### "Permission denied" when creating project

```bash
# Check authentication
gh auth status

# Should show:
#   ✓ Logged in to github.com as IggyIkenna
#   ✓ Token: repo, project, workflow
```

### "Epic file not found"

```bash
# Verify path (relative to script location)
ls -la ../../epic-breakdowns/epic-market-data-infrastructure.md

# Or use absolute path
python 02-create-issues.py \
    --epic-file "/full/path/to/epic-market-data-infrastructure.md" \
    --apply
```

### "Issue already exists"

Script automatically detects existing issues and skips creation. Safe to re-run.

### Workflows not working

- Verify you configured "Pull request merged → Close linked issues"
- Check PR body contains "Closes #<ISSUE_NUMBER>"
- Ensure PR merged to main (not just closed)

---

## Files Generated

```
.
├── 01-create-project.sh             # Creates GitHub Project
├── 02-create-issues.py              # Creates 4 issues from epic
├── 03-link-issues-to-project.sh     # Links issues to project
├── 04-copy-workflows.sh             # Workflow configuration
├── 05-verify-setup.sh               # Validates setup
├── 06-generate-project-readme.sh    # Generates docs
├── 08-verify-completion.sh          # Checks project completion (after execution)
├── run-batch-fix.sh                 # Batch agent automation
├── AGENT_PROMPT.md                  # Agent quick-start prompt template
├── AGENT_WORKFLOW.md                # Agent detailed workflow guide
├── COMPLETION-INTEGRATION.md        # Post-completion Codex integration checklist
├── STATUS.md                        # Current status and next steps
├── PROJECT-COMPARISON.md            # Comparison with Initial Cleanup
├── README.md                        # This file
├── issue-manifest.json              # Generated by Stage 3
└── PROJECT_README.md                # Generated by Stage 7
```

---

## Next Steps After Setup

1. **View Project:**

   ```bash
   gh project view 6 --owner IggyIkenna --web
   ```

2. **Start Working:**
   - Pick an issue from "Todo" column
   - Assign to yourself
   - Create branch, implement, create PR
   - PR auto-merges when quality gates pass
   - Issue auto-closes when PR merges

3. **Track Progress:**
   ```bash
   gh issue list --label MARKET-DATA-INFRASTRUCTURE --state open
   gh pr list --label MARKET-DATA-INFRASTRUCTURE --state open
   ```

---

---

## Stage 8: Verify Project Completion (After Execution)

**Script:** `08-verify-completion.sh`

**What it does:**

- Checks status of all 4 subtasks from issue manifest
- Groups by phase (0-4) and repo
- Shows completion percentage per phase and repo
- Identifies remaining tasks

**Usage:**

```bash
bash 08-verify-completion.sh --issue-manifest issue-manifest.json
```

**Expected Output:**

```
========================================
Market Data Infrastructure - Status Report
========================================

| Phase | Repo | Issue | State | Subtask | Priority |
|-------|------|-------|-------|---------|----------|
| 0 | unified-trading-services | #1 | ✅ CLOSED | Subtask 0.1 | P0 |
| 0 | unified-trading-services | #2 | ✅ CLOSED | Subtask 0.2 | P0 |
...

========================================
Summary
========================================

Overall Progress:
  Total subtasks: 51
  Completed: 45 / 51 (88.2%)
  In Progress: 3
  Open: 3
  Errors: 0

By Phase:
  Phase 0 (Infrastructure): 4/4 (100.0%)
  Phase 1 (Events Interface): 13/13 (100.0%)
  Phase 2 (Config Interface): 10/13 (76.9%)
    In Progress: 2
    Open: 1
  Phase 3 (Market Interface): 12/13 (92.3%)
  Phase 4 (Order Interface): 6/8 (75.0%)

By Repo:
  unified-trading-library: 10/10 (100.0%)
  unified-config-interface: 8/10 (80.0%)
  unified-market-interface: 12/12 (100.0%)
  unified-order-interface: 10/12 (83.3%)
  unified-trading-services: 5/7 (71.4%)

========================================
📋 Next Steps
========================================

Phase 2 (Config Interface) - 1 task remaining:
  bash run-batch-fix.sh --model auto --phase 2 --max-parallel 3
```

**Manual Steps:** None (reads from GitHub API)

**Time:** 1-2 minutes

**Run This:** After batch execution or periodically to check progress

---

## Agent Automation

### Local Agent Execution

**For working on a single subtask locally with an AI agent:**

1. **Read the agent prompt:** `AGENT_PROMPT.md`
   - Copy-paste template for quick agent tasks
   - Includes workflow overview and examples

2. **Read the agent workflow:** `AGENT_WORKFLOW.md`
   - Detailed step-by-step instructions
   - Handles all subtask types (new repos, existing repos, infrastructure)
   - Includes troubleshooting and edge cases

3. **Give agent the task:**

   ```
   Complete subtask for Market Data Infrastructure issue #3 in unified-trading-library.

   Follow the workflow in @AGENT_WORKFLOW.md for detailed steps.
   ```

### Batch Agent Execution

**For processing multiple subtasks in parallel:**

```bash
# All subtasks from issue manifest
bash run-batch-fix.sh --model auto --max-parallel 3

# Filter by phase
bash run-batch-fix.sh --model auto --phase 1 --max-parallel 5  # Phase 1 (events interface)

# Filter by repo
bash run-batch-fix.sh --model auto --repos unified-trading-library,unified-config-interface

# Filter by priority
bash run-batch-fix.sh --model auto --priority P0-critical --max-parallel 5

# Dry run (preview)
bash run-batch-fix.sh --model auto --dry-run
```

**How it works:**

1. Reads `issue-manifest.json` (created by `02-create-issues.py`)
2. Filters issues by repo/phase/priority
3. Spawns parallel agent workers (via `batch-fix-v2.sh`)
4. Each agent completes one subtask end-to-end
5. PRs auto-merge when quality gates pass
6. Issues auto-close when PRs merge

**Prerequisites:**

- `GH_PAT` configured in GitHub Actions secrets and Google Secret Manager (admin permissions including projects)
- Issue manifest exists: `bash 02-create-issues.py --apply`
- Batch fix script: `../automation/batch-fix-v2.sh`

### Verify Project Completion

**After running batch automation or working on tasks:**

```bash
# Check completion status
bash 08-verify-completion.sh --issue-manifest issue-manifest.json
```

**Output shows:**

- Overall completion percentage
- Breakdown by phase (0-4)
- Breakdown by repo
- Remaining tasks (with suggested commands)
- Next steps

**Run periodically to track progress.**

---

## Stage 9: Post-Completion Codex Integration (After 100% Complete)

**CRITICAL:** When all 4 subtasks are complete, the epic is NOT done until Codex docs are updated!

**What it does:**

- Ensures epic learnings are integrated into Codex
- Makes new architecture the standard for future work
- Creates migration guide for remaining 11 services
- Documents lessons learned
- Closes project properly

**Usage:**

```bash
# After 08-verify-completion.sh shows 100%, follow this guide:
cat COMPLETION-INTEGRATION.md
```

**Checklist includes:**

- ✅ Create 5 new Codex docs (unified-libraries/)
- ✅ Update 8 existing Codex docs
- ✅ Create migration guide
- ✅ Document lessons learned
- ✅ Create migration issues for 11 services
- ✅ Close GitHub Project with docs links
- ✅ Team announcement

**Estimated time:** 6-8 hours

**Why this matters:** Without Codex integration, the epic's learnings won't benefit future work. Developers will
continue using old patterns and documentation will be outdated.

**See:** `COMPLETION-INTEGRATION.md` for full checklist and detailed instructions.

---

### Agent Files

```
.
├── AGENT_PROMPT.md          # Quick copy-paste prompt template
├── AGENT_WORKFLOW.md         # Detailed step-by-step workflow
├── run-batch-fix.sh          # Batch automation wrapper
└── 08-verify-completion.sh   # Completion status checker
```

---

## Related Documentation

- **Epic Overview:** `unified-trading-codex/11-project-management/epics/market-data-infrastructure-epic.md`
- **Epic Breakdown:** `unified-trading-codex/11-project-management/epic-breakdowns/epic-market-data-infrastructure.md`
- **Infrastructure:** `~/.cursor/plans/infrastructure-updates-for-library-refactor.md`
- **Plan:** `~/.cursor/plans/github_project_setup_cb974903.plan.md`
- **Agent Prompt:** `AGENT_PROMPT.md` (quick copy-paste)
- **Agent Workflow:** `AGENT_WORKFLOW.md` (detailed guide)

---

**Last Updated:** 2026-02-14 **Maintainer:** Ikenna **Status:** Ready for use
