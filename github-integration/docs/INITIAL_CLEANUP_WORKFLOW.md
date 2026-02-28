# Initial Cleanup Workflow

**Strategy**: One issue per repo → Clean slate before parallel COD fixes

## Why This Approach?

### The Problem with Per-File Issues

**Complex**: 200+ COD issues across 14 repos

- instruments-service: 20 files with COD-SIZE violations
- execution-services: 15 files with COD-SIZE violations
- strategy-service: 10 files with COD-SIZE violations
- ... (11 more repos)

**Challenges**:

- Managing 200+ issues is complex
- Multiple workers per repo → git conflicts possible
- Hard to verify repo is "clean" (scattered PRs)
- Difficult to track progress (200 issues vs 14 repos)

### The Solution: One Issue Per Repo

**Simple**: 14 issues (one per repo)

- Each issue: "Fix ALL COD violations in [repo-name]"
- One worker per repo (clear ownership)
- Sequential fixes within repo (simpler)
- Clean slate per repo before moving on

**Benefits**: ✅ Simple project management (14 tasks, not 200+)  
✅ Clear ownership (1 worker = 1 repo)  
✅ Sequential fixes per repo (easier to verify)  
✅ Clean slate per repo  
✅ Easy progress tracking (14 repos, not 200 files)

---

## Project Structure

### GitHub Project: "Initial Cleanup"

**Purpose**: Temporary project for initial COD cleanup

**Issues**: 14 total (one per repo)

| Issue | Repo                           | Est. COD Violations |
| ----- | ------------------------------ | ------------------- |
| #639  | execution-services             | 15 files            |
| #640  | strategy-service               | 10 files            |
| #641  | instruments-service            | 20 files            |
| #642  | unified-trading-services       | 5 files             |
| #643  | market-data-processing-service | 8 files             |
| #644  | ml-training-service            | 3 files             |
| #645  | ml-inference-service           | 2 files             |
| #646  | features-delta-one-service     | 4 files             |
| #647  | features-volatility-service    | 3 files             |
| #648  | features-calendar-service      | 2 files             |
| #649  | features-onchain-service       | 3 files             |
| #650  | market-tick-data-handler       | 2 files             |
| #651  | portfolio-manager-service      | 5 files             |
| #652  | unified-trading-deployment-v2  | 3 files             |

**Total**: ~85 COD-SIZE violations across 14 repos

---

## Workflow

### Step 1: Create Project & Issues

```bash
cd unified-trading-codex/11-project-management/github-integration

# Run setup script
bash scripts/one-time/create-initial-cleanup-project.sh

# Output:
#   ✅ Project created: #5 "Initial Cleanup"
#   ✅ Created 14 issues (one per repo)
#   ✅ All issues attached to project
#   ⚠️  IMPORTANT: Configure workflows manually (GitHub API limitation)
```

### Step 2: Configure Project Workflows (REQUIRED)

**GitHub API Limitation**: Workflows must be configured manually.

**✅ RECOMMENDED: Copy workflows from Project #3 (COD template)**:

```bash
# After creating project #5, copy 8 workflows from template
bash scripts/utilities/copy-project-workflows.sh --from 3 --to 5
```

This will show you:

- All 8 workflows configured on Project #3
- Exact settings for each workflow
- Step-by-step instructions to replicate

**Critical Workflows**:

- ⭐ **Pull request merged → Close linked issues** (CRITICAL)
- Auto-add issues (label: cleanup)
- Item closed → Set status to 'Done'
- Auto-archive after 30 days (optional)
- Plus 4 more state management workflows

**Alternative: Generic Interactive Setup**:

```bash
bash scripts/utilities/setup-project-workflows.sh --project-number 5
```

**Alternative: Manual Setup**:

1. Go to: https://github.com/users/IggyIkenna/projects/5/settings/workflows
2. Create workflows using the same configuration as Project #3

**Why this is critical**:

- ❌ Without workflows: PRs merge but issues stay open (manual tracking)
- ✅ With workflows: PRs merge → issues auto-close (automatic tracking)

### Step 3: Run Batch Fix (7 Workers)

```bash
# Get issue numbers from setup script output
ISSUE_NUMBERS="639 640 641 642 643 644 645 646 647 648 649 650 651 652"

# Run batch fix with 7 workers
cd unified-trading-codex/11-project-management/github-integration

bash scripts/automation/batch-fix-v2.sh \
    --model gemini-3-flash \
    --issues "$ISSUE_NUMBERS" \
    --max-parallel 7
```

**What happens**:

1. **Workspace Pooling**: Creates 7 isolated workspace clones
2. **Parallel Repos**: Processes 7 repos simultaneously (first batch)
3. **Sequential Fixes**: Each worker fixes ALL CODs for its repo sequentially
4. **Git-Aware**: Quality gates check only changed files (no deadlock)
5. **Auto-Merge**: PRs auto-merge when CI passes
6. **Second Batch**: After first 7 complete, picks up remaining 7 repos

### Step 4: Monitor Progress

```bash
# Check project status
gh project view 5 --owner IggyIkenna --web

# Check open PRs
gh pr list --label cod --state open

# Check quality gate results
gh pr checks <PR-number>
```

---

## Execution Flow

### High-Level Flow

```
14 Repos → 14 Issues → 7 Workers → 2 Batches

Batch 1 (7 repos):
  Worker 1: execution-services (15 CODs sequential)
  Worker 2: strategy-service (10 CODs sequential)
  Worker 3: instruments-service (20 CODs sequential)
  Worker 4: unified-trading-services (5 CODs sequential)
  Worker 5: market-data-processing-service (8 CODs sequential)
  Worker 6: ml-training-service (3 CODs sequential)
  Worker 7: ml-inference-service (2 CODs sequential)

Batch 2 (7 repos):
  Worker 1: features-delta-one-service (4 CODs sequential)
  Worker 2: features-volatility-service (3 CODs sequential)
  Worker 3: features-calendar-service (2 CODs sequential)
  Worker 4: features-onchain-service (3 CODs sequential)
  Worker 5: market-tick-data-handler (2 CODs sequential)
  Worker 6: portfolio-manager-service (5 CODs sequential)
  Worker 7: unified-trading-deployment-v2 (3 CODs sequential)
```

### Per-Worker Flow (Example: Worker 1 → execution-services)

```bash
# Worker 1 assigned to execution-services (issue #639)

# Step 1: Clone to isolated workspace
/tmp/batch-fix-pool-XXXXXX/execution-services_clone_1/

# Step 2: Scan for COD violations (15 files)
files_to_fix = [
    "execution_services/order_manager.py (2100 lines)",
    "execution_services/position_tracker.py (1850 lines)",
    "execution_services/risk_manager.py (1750 lines)",
    ... (12 more)
]

# Step 3: Fix each file sequentially
for file in files_to_fix:
    # a. Agent analyzes file
    # b. Splits into smaller modules (e.g., order_manager.py → 3 files)
    # c. Stages changed files (3-5 files)
    # d. Runs quickmerge --files
    # e. quality-gates.sh checks ONLY staged files (git-aware)
    # f. ✅ PASS → PR created
    # g. CI runs, auto-merge when passes
    # h. Move to next file

# Step 4: Cleanup workspace
rm -rf /tmp/batch-fix-pool-XXXXXX/execution-services_clone_1/

# Result: 15 PRs for execution-services, all merged
```

---

## Timeline Estimate

### Assumptions

- 85 total COD violations across 14 repos
- 20 minutes per COD fix (average)
- 7 workers in parallel
- 2 batches (7 + 7 repos)

### Calculation

**Sequential (no parallelism)**:

- 85 CODs × 20 min = **1700 minutes (~28 hours)**

**Service Grouping (v1 - parallel services)**:

- Longest repo: 20 CODs (instruments-service)
- 20 CODs × 20 min = **400 minutes (~6.7 hours)**

**Workspace Pooling (v2 - 7 workers)**:

- Batch 1: 7 repos in parallel
  - Longest repo in batch 1: 20 CODs (instruments-service)
  - 20 CODs × 20 min = 400 minutes (~6.7 hours)
- Batch 2: 7 repos in parallel
  - Longest repo in batch 2: 5 CODs (portfolio-manager-service)
  - 5 CODs × 20 min = 100 minutes (~1.7 hours)
- **Total: ~8.4 hours**

**Speedup**: **3.4x faster** than sequential

---

## Why Keep Deadlock Protection?

### Current Use Case: Simple

- One worker per repo
- Sequential fixes within repo
- No multi-worker conflicts on same repo
- Git-aware quality gates still useful (other unrelated linter errors)

### Future Use Case: Complex

When we have **cross-file COD issues**:

- Multiple files need fixes simultaneously
- Multiple workers per repo (true parallelism within repo)
- Git conflicts possible (without workspace pooling)
- Deadlock possible (without git-aware quality gates)

**Example Future Scenario**:

```
instruments-service has 50 COD violations

With deadlock protection:
  - 5 workers × 5 isolated clones
  - Each clone handles 10 files
  - True parallelism: 50 fixes in ~4 hours

Without deadlock protection:
  - 1 worker, shared workspace
  - Sequential: 50 fixes in ~17 hours
```

**Keep the logic**: It's already built, tested, and will be essential later.

---

## Success Criteria

### Per Repo

- ✅ All COD-SIZE violations resolved (no files >1500 lines)
- ✅ All quality gates passing
- ✅ All tests passing
- ✅ Clean slate (ready for future development)

### Overall

- ✅ All 14 repos cleaned up
- ✅ All PRs merged
- ✅ Project closed
- ✅ Ready to transition to per-service projects

---

## After Initial Cleanup

### Transition to Service Projects

Once all 14 repos are clean:

1. **Close "Initial Cleanup" project**
2. **Create 32 service-level projects** (using `create-all-service-projects.py`)
3. **Enable granular COD tracking** per service
4. **Use parallel workers per service** (when needed)

### Ongoing COD Prevention

- COD-SIZE checks in CI (fail if file >1500 lines)
- Monthly scans for new COD violations
- Per-service projects for tracking
- Automated fixes with batch-fix-v2.sh

---

## Quick Reference

### Setup

```bash
cd unified-trading-codex/11-project-management/github-integration

# Step 1: Create project & issues
bash scripts/one-time/create-initial-cleanup-project.sh

# Step 2: Configure workflows (REQUIRED - manual)
bash scripts/utilities/setup-project-workflows.sh --project-number 5 --org IggyIkenna
```

### Execution

```bash
bash scripts/automation/batch-fix-v2.sh \
    --model gemini-3-flash \
    --issues "639 640 641 642 643 644 645 646 647 648 649 650 651 652" \
    --max-parallel 7
```

### Monitoring

```bash
gh project view 5 --owner IggyIkenna
gh pr list --label cod,cleanup --state open
```

---

## Files

- **Setup Script**: `scripts/one-time/create-initial-cleanup-project.sh`
- **This Doc**: `docs/INITIAL_CLEANUP_WORKFLOW.md`
- **COD Status**: `docs/COD_WORKFLOW_STATUS.md`
- **Workspace Pooling**: `docs/WORKSPACE_POOLING.md`
- **Deadlock Solution**: `../../../06-coding-standards/cod-deadlock-solution.md`
