# Initial Cleanup Project (Project #5)

## Overview

**Goal:** Fix all codex violations across 13 service repositories.

**GitHub Project:** https://github.com/users/IggyIkenna/projects/5

**Status:** In Progress (11 open issues, 2 closed)

---

## Project Structure

This directory contains all scripts and documentation for the Initial Cleanup project:

```
initial-cleanup/
├── utilities/
│   └── check-codex-violations.py  # Core violation checker (from core/02-run-diff-checker.py)
├── 01-create-project.sh           # Create GitHub Project #5
├── 02-create-issues.sh            # Create cleanup issues (one per repo)
├── 03-link-issues-to-project.sh   # Add issues to project
├── 04-run-batch-fix.sh            # Run batch automation with filtering
├── 05-verify-completion.sh        # Check completion status
├── 06-generate-manifests.py       # Generate CODEX_VIOLATIONS_MANIFEST.md files
├── AGENT_PROMPT.md                # Quick copy-paste prompt for agents
├── WORKFLOW.md                    # Detailed workflow (892 lines)
└── README.md                      # This file
```

---

## Quick Start

### Setup (One-Time)

```bash
# 1. Create project
bash 01-create-project.sh

# 2. Create issues (one per repo)
bash 02-create-issues.sh

# 3. Link issues to project
bash 03-link-issues-to-project.sh

# 4. Configure workflows manually:
# https://github.com/users/IggyIkenna/projects/5/settings/workflows
# Copy workflows from Project #3 (use: copy-project-workflows.sh --from 3 --to 5)
```

### Run Batch Automation

```bash
# Process all open, unblocked cleanup issues (recommended)
bash 04-run-batch-fix.sh \
  --model auto \
  --require-labels "cleanup" \
  --state open \
  --max-parallel 4
```

### Run Single Repo Locally

```bash
# Copy prompt from AGENT_PROMPT.md
# Example:
"Fix all codex violations for execution-services issue #147.
Follow @WORKFLOW.md for detailed steps."
```

### Check Completion

```bash
# View status report
bash 05-verify-completion.sh
```

---

## Codex Violations Tracked

All 8 checks from quality gates:

1. **print()** → logger.info() (production code only)
2. **os.getenv()** → config class extending UnifiedCloudServicesConfig
3. **datetime.now()** → datetime.now(timezone.utc)
4. **bare except** → specific exceptions or @handle_api_errors
5. **imports inside functions** → move to top of file ✨ NEW
6. **requests** → httpx/aiohttp in async code
7. **asyncio.run() in loops** → asyncio.gather()
8. **time.sleep() in async** → asyncio.sleep()

**Excluded:** File size violations (>1500 lines) tracked separately in COD-SIZE issues (Project #6)

---

## Issue Status

### Open Issues (11)

| Repo                           | Issue | Violations |
| ------------------------------ | ----- | ---------- |
| execution-services             | #147  | 20         |
| strategy-service               | #23   | 20         |
| instruments-service            | #58   | 25         |
| market-data-processing-service | #46   | 14         |
| ml-training-service            | #38   | 31         |
| ml-inference-service           | #28   | 5          |
| features-delta-one-service     | #34   | 22         |
| features-volatility-service    | #25   | 7          |
| features-calendar-service      | #37   | 5          |
| features-onchain-service       | #27   | 11         |
| unified-trading-deployment-v2  | #126  | 57         |

**Total:** 217 violations (down from 1210 after excluding tests/scripts and COD-SIZE)

### Closed Issues (2)

| Repo                     | Issue | Status                                      |
| ------------------------ | ----- | ------------------------------------------- |
| unified-trading-services | #48   | ✅ CLOSED (PR #51 merged)                   |
| market-tick-data-handler | #51   | ✅ CLOSED (but has 34 remaining violations) |

---

## Scripts Guide

### 01-create-project.sh

**Purpose:** Create GitHub Project #5  
**When to use:** One-time setup  
**Output:** Project number

```bash
bash 01-create-project.sh
# ✅ Project created: #5
```

### 02-create-issues.sh

**Purpose:** Create cleanup issues in each repo  
**When to use:** One-time setup (or to create missing issues)  
**Dry run:** `--dry-run` flag

```bash
# Create all issues
bash 02-create-issues.sh

# Preview without creating
bash 02-create-issues.sh --dry-run
```

**What it creates:**

- Issue title: `[CLEANUP] Fix all COD violations in [repo]`
- Labels: `cod`, `cleanup`
- Assignee: @me
- Body: Comprehensive scope + manifest reference + workflow link

### 03-link-issues-to-project.sh

**Purpose:** Add cleanup issues to Project #5  
**When to use:** After creating issues  
**Project number:** Default 5 (or specify: `--project-number N`)

```bash
bash 03-link-issues-to-project.sh

# Or for different project:
bash 03-link-issues-to-project.sh 5
```

### 04-run-batch-fix.sh

**Purpose:** Run batch automation with intelligent filtering  
**When to use:** To process multiple issues in parallel

**Features:**

- Filter by issue state (open/closed/all)
- Filter by labels (require/exclude)
- Filter by repos
- Dry run mode

**Common usage:**

```bash
# Process all open cleanup issues (recommended)
bash 04-run-batch-fix.sh \
  --model auto \
  --require-labels "cleanup" \
  --state open \
  --max-parallel 4

# Process specific repos only
bash 04-run-batch-fix.sh \
  --model auto \
  --repos "execution-services,strategy-service" \
  --state open

# Preview what would run
bash 04-run-batch-fix.sh \
  --model auto \
  --require-labels "cleanup" \
  --dry-run
```

**Label filtering examples:**

```bash
# Only process cleanup issues
--require-labels "cleanup"

# Exclude blocked issues
--exclude-labels "blocked"

# Both
--require-labels "cleanup" --exclude-labels "blocked,wip"
```

**Wraps:** `../../automation/run-cleanup-batch-fix.sh` → `../../automation/batch-fix-v2.sh`

### 05-verify-completion.sh

**Purpose:** Check completion status and generate report  
**When to use:** Anytime to check progress

```bash
bash 05-verify-completion.sh
```

**Output:**

- Table with all issues (state, labels, violation count)
- Summary statistics
- Next steps recommendation

### 06-generate-manifests.py

**Purpose:** Generate CODEX_VIOLATIONS_MANIFEST.md files for all repos  
**When to use:** After quality gates updates or to refresh violation counts

```bash
# Generate manifests for all repos
python3 06-generate-manifests.py

# Dry run (preview only)
python3 06-generate-manifests.py --dry-run

# Specific repos only
python3 06-generate-manifests.py --repos "execution-services,strategy-service"
```

**What it does:**

- Scans each repo for codex violations using `utilities/check-codex-violations.py`
- Generates `CODEX_VIOLATIONS_MANIFEST.md` in each repo root
- Provides human-readable list of all violations with file paths and line numbers
- Excludes `tests/` and `scripts/` directories
- Shows total violation count per repo

**Output example:**

```markdown
# Codex Violations Manifest

## COD-PRINT: print() statements (5 violations)

- execution_services/main.py:45
- execution_services/config.py:12 ...

## COD-IMPORT: Imports inside functions (3 violations)

...

Total violations: 8
```

**Used by:**

- Issue bodies (reference manifest for violation list)
- Agents (check what needs fixing)
- 05-verify-completion.sh (read violation counts from manifest)

---

## Utilities

### utilities/check-codex-violations.py

**Purpose:** Core violation checker (moved from core/02-run-diff-checker.py)  
**Used by:** 06-generate-manifests.py

**Direct usage (advanced):**

```bash
python3 utilities/check-codex-violations.py \
  --repo "IggyIkenna/execution-services" \
  --codex-dir "path/to/unified-trading-codex" \
  --workspace-dir "path/to/workspace" \
  --dry-run \
  --output-json violations.json
```

**What it checks:**

1. print() statements (COD-PRINT)
2. os.getenv() usage (COD-GETENV)
3. datetime.now() without UTC (COD-DATETIME)
4. bare except clauses (COD-BARE)
5. imports inside functions (COD-IMPORT) ✨
6. requests in async code (COD-ASYNC-REQUESTS)
7. asyncio.run() in loops (COD-ASYNC-RUN)
8. time.sleep() in async (COD-ASYNC-SLEEP)

**Excludes:** `tests/`, `scripts/` directories

**Note:** This script was moved from `scripts/core/` to be project-specific. For COD-SIZE checking (file size
violations), see `scripts/core/05-check-file-size-cods.py` (will move to COD-SIZE project when created).

---

## Agent Documentation

### AGENT_PROMPT.md

**Purpose:** Quick copy-paste prompts for local agent execution  
**When to use:** Running one repo at a time with full control

**Example:**

```
Fix all codex violations for execution-services issue #147.

INFRASTRUCTURE CONTEXT: @WORKFLOW.md sections 1-5
WORKFLOW: [8 steps...]
```

### WORKFLOW.md

**Purpose:** Comprehensive 892-line workflow guide  
**When to use:** Reference for agents (local or batch)

**Key sections:**

1. **Infrastructure Context** - Unified Cloud Services dependency pattern
2. **Stash Safety** - Never lose work when pulling
3. **8-Step Workflow** - Complete execution flow
4. **CI Failure Diagnosis** - Fix infrastructure, not code
5. **Edge Cases** - Quality gates updates, dependency issues, etc.

---

## Infrastructure Requirements

### Unified Cloud Services Dependency Pattern

**CRITICAL:** All repos must use unified-trading-services correctly:

| Environment        | Installation Method                                            |
| ------------------ | -------------------------------------------------------------- |
| **Local**          | `uv pip install -e ../unified-trading-services`                |
| **GitHub Actions** | `uv pip install --system -e deps/unified-trading-services`     |
| **Cloud Build**    | `FROM unified-trading-services:latest` (already in base image) |

**NEVER add unified-trading-services to pyproject.toml dependencies!**

### Quality Gates Consistency

All 3 environments must run the same command:

```bash
bash scripts/quality-gates.sh --no-fix
```

**Template:** `unified-trading-services/scripts/quality-gates.sh`

**Required checks (8 total):**

1. print() statements
2. os.getenv() usage
3. datetime.now() without UTC
4. bare except clauses
5. imports inside functions ✨
6. requests in async code
7. asyncio.run() in loops
8. time.sleep() in async

---

## Execution Strategies

### Strategy 1: Batch Automation (Parallel)

**Best for:** Processing multiple repos quickly

```bash
bash 04-run-batch-fix.sh \
  --model auto \
  --require-labels "cleanup" \
  --state open \
  --max-parallel 4
```

**Pros:**

- ✅ Fast (4 repos in parallel)
- ✅ Isolated workspaces (no conflicts)
- ✅ Automated PR creation
- ✅ Auto-merge enabled

**Cons:**

- ❌ Less visibility per repo
- ❌ Harder to debug if issues arise

### Strategy 2: Local Agent (Sequential)

**Best for:** Full control and visibility

```bash
# Copy prompt from AGENT_PROMPT.md:
"Fix all codex violations for execution-services issue #147.
Follow @WORKFLOW.md for detailed steps."
```

**Pros:**

- ✅ Full visibility into changes
- ✅ Can iterate and test incrementally
- ✅ Easier to handle edge cases
- ✅ Learn repo-specific patterns

**Cons:**

- ❌ Slower (one repo at a time)
- ❌ Manual execution for each repo

### Strategy 3: Hybrid

**Best for:** Balance of speed and control

```bash
# Run batch for simple repos
bash 04-run-batch-fix.sh \
  --model auto \
  --repos "features-calendar-service,features-onchain-service,ml-inference-service" \
  --state open

# Run locally for complex repos (execution-services, unified-trading-deployment-v2)
# Use AGENT_PROMPT.md
```

---

## Related Projects

### Project #6: COD-SIZE Refactoring

**Blocked by:** Initial Cleanup (this project)

**Scope:** Fix files >1500 lines  
**Directory:** `scripts/projects/cod-size-refactoring/` (to be created)

**Issues:**

- unified-trading-services #52 (not blocked)
- instruments-service #59 (blocked)
- strategy-service #25 (blocked)
- execution-services #150 (blocked)
- unified-trading-deployment-v2 #127 (blocked)
- market-tick-data-handler #54 (not blocked)

---

## Key Infrastructure Docs

**Read these before making changes:**

- **Quality Gates:** `@unified-trading-codex/06-coding-standards/quality-gates.md`
- **Quality Gates Environments:**
  `@unified-trading-codex/11-project-management/github-integration/docs/QUALITY-GATES-ENVIRONMENTS.md`
- **Dockerfile Standards:** `@unified-trading-codex/06-coding-standards/dockerfile-standards.md`
- **Dependency Management:** `@unified-trading-codex/06-coding-standards/dependency-management.md`

---

## Troubleshooting

### Issue: CI fails but local passed

**Root cause:** Infrastructure mismatch  
**Fix:** Update GitHub Actions to match local (see WORKFLOW.md Step 6)

### Issue: Duplicate dependencies

**Root cause:** Service re-specifies dependency already in unified-trading-services  
**Fix:** Remove from service pyproject.toml, unified-trading-services already provides it

### Issue: Quality gates outdated

**Root cause:** Repo missing Check 5 (imports inside functions)  
**Fix:** Copy quality-gates.sh from unified-trading-services, commit separately

---

## Timeline

| Date       | Event                                                      |
| ---------- | ---------------------------------------------------------- |
| 2026-02-13 | Project created (#5)                                       |
| 2026-02-13 | 13 issues created (one per repo)                           |
| 2026-02-14 | Added Check 5 (imports inside functions)                   |
| 2026-02-14 | Rolled out Check 5 to all 12 repos                         |
| 2026-02-14 | Created enhanced batch fix (label filtering)               |
| 2026-02-14 | Created agent documentation (WORKFLOW.md, AGENT_PROMPT.md) |
| 2026-02-14 | Organized into project-focused structure                   |

---

## Success Metrics

- ✅ 2 repos complete (unified-trading-services, market-tick-data-handler)
- 🟡 11 repos in progress
- 📊 217 violations remaining (down from 1210)
- 🎯 Target: 0 violations across all repos

**Completion:** When all 13 issues are closed and manifests show 0 violations.
