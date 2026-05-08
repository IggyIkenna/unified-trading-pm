---
status: archived
superseded_by: cicd_code_rollout_master_2026_03_13
archived_date: "2026-03-13"
archive_reason: >
  Old plan references act simulation, separate Docker QG images, pr-watcher.yml, and llm-agent-wrapper.sh — none of
  which exist in the current system. Superseded by the consolidated CI/CD code rollout master plan.
---

# MASTER CI/CD PLAN - Production-Grade Development Workflow (ARCHIVED)

**Status**: ARCHIVED — superseded by `cicd_code_rollout_master_2026_03_13.md` **Priority**: P0 (Foundation for all
development) **Estimated Time**: 8-12 hours with parallel agents **Scope**: 32 repos + Codex docs + Cursor rules

---

## 📖 Executive Summary

**Goal**: Zero-surprise merges with production-grade CI/CD infrastructure.

**What We're Building**:

1. **Unified Quickmerge** - Single command for all quality checks
2. **Differential Branching** - Smart branch isolation when needed
3. **Cascading Dependencies** - Automatic multi-repo coordination
4. **Dev Environment** - Separate project ID for safe testing
5. **GitHub Actions Watcher** - Mandatory LLM-enhanced validation
6. **Docker Parity** - Same environment everywhere

**Philosophy**: Make it impossible to accidentally break things.

---

## 🎯 Core Principles

### 1. **ALWAYS Use Quickmerge** (Enforced)

- ✅ Cursor rules mandate quickmerge
- ✅ GitHub Actions watcher blocks bypasses
- ✅ One workflow, zero exceptions

### 2. **Main by Default, Branch When Necessary** (Smart)

- ✅ Use main if all deps match `origin/main`
- ✅ Auto-detect diffs, force `--dep-branch` decision
- ✅ Complete isolation on branch

### 3. **Fail Fast, Fix Automatically** (Efficient)

- ✅ Dependency validation FIRST (cheapest check)
- ✅ Pre-flight audit catches Codex violations
- ✅ LLM auto-fixes when possible

### 4. **Dev ≠ Prod** (Safe)

- ✅ Separate GCP projects for dev/prod
- ✅ Environment-aware workflows
- ✅ Safe experimentation

### 5. **GitHub Actions is Final Safety Net** (Mandatory)

- ✅ LLM-enhanced watcher reviews ALL PRs
- ✅ Blocks if issues detected
- ✅ Provides rich context + fix suggestions

---

## 🏗️ Complete Architecture

### **Unified Quickmerge Pipeline**

```
bash scripts/quickmerge.sh "feat: update" [--dep-branch "my-feature"]

STAGE 1: Dependency Validation (10s - BLOCKING)
  ├─> Check: Do dependencies differ from origin/main?
  │   ├─> YES + no --dep-branch → ❌ ERROR + guidance
  │   ├─> YES + --dep-branch → Cascade mode
  │   └─> NO → Main mode (normal)
  │
  └─> Cascade: Quickmerge dependencies FIRST (if needed)
      └─> Topological sort ensures correct order

STAGE 2: Pre-Flight Audit (15s - AUTO-FIX)
  ├─> Codex compliance (E722, large files, etc.)
  ├─> Cursor rules audit
  └─> 🔧 LLM agent fixes violations (optional)

STAGE 3: Local Quality Gates - Docker (30s - FAST)
  ├─> Ruff format + check
  ├─> Basedpyright
  └─> Pytest (quick mode)

STAGE 4: Create PR Branch & Commit (5s)
  └─> Stash, branch, stage, commit

STAGE 5: Act - Full GitHub Simulation (1-2min - ACCURATE)
  ├─> Simulates exact GitHub Actions
  ├─> Uses environment-aware project ID
  │   └─> ENVIRONMENT=development → GCP_PROJECT_ID_DEV
  │   └─> ENVIRONMENT=production → GCP_PROJECT_ID
  └─> Catches GitHub-specific issues

STAGE 6: Main Agent Handles Failures (inline)
  ├─> If act fails: Read errors
  ├─> Fix directly (no separate watcher process)
  └─> Re-run act (max 3 attempts)

STAGE 7: Push & Create PR (5s)
  └─> git push + gh pr create --auto-merge

TOTAL: ~2-5 minutes (all checks, auto-fix if needed)
```

### **GitHub Actions (Mandatory Final Check)**

```yaml
# Runs AFTER PR created
# Cannot be bypassed

name: PR Watcher (LLM-Enhanced)

on: pull_request

jobs:
  llm-watcher:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: LLM Analysis (Cursor/Claude)
        env:
          CURSOR_API_KEY: ${{ secrets.CURSOR_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          # Run LLM analysis
          bash .github/scripts/llm-pr-watcher.sh

      - name: Block if Issues
        if: failure()
        run: |
          echo "❌ LLM Watcher detected issues"
          echo "Review feedback in PR comments"
          exit 1
```

**What LLM Watcher Checks**:

- ✅ Did they use quickmerge? (check commit message)
- ✅ Is environment config correct? (dev vs prod)
- ✅ Are dependencies properly cascaded?
- ✅ Any Codex/Cursor violations?
- ✅ Quality gates passed?
- ✅ Proper branch strategy used?

**Output**:

- 💬 PR comment with rich context
- 🔧 Specific fix suggestions
- ❌ Blocks merge if critical issues

---

## 📦 Component Details

### **1. Dev Environment Support**

#### `.env` Configuration

```bash
# Each repo has .env
ENVIRONMENT=development  # or production

# Quickmerge reads this and switches project IDs
```

#### Project ID Mapping

```bash
# Repository variables (set via gh CLI)
GCP_PROJECT_ID=central-element-323112      # Production
GCP_PROJECT_ID_DEV=central-element-dev     # Development

# Automatic selection
if [ "$ENVIRONMENT" = "development" ]; then
    PROJECT_ID="$GCP_PROJECT_ID_DEV"
else
    PROJECT_ID="$GCP_PROJECT_ID"
fi
```

#### Benefits

✅ **Safe testing** - Dev changes don't affect prod data ✅ **A/B testing** - Run experiments in dev ✅ **Hotfix
testing** - Test prod fixes in dev first ✅ **Parallel workflows** - Dev and prod can evolve independently

---

### **2. Differential-Based Branching**

#### Decision Logic

```bash
# Check dependencies vs origin/main
for dep in dependencies:
    if ! git diff origin/main --quiet:
        has_diff=true

if has_diff and not --dep-branch:
    ❌ ERROR: "Use --dep-branch for isolation"
    exit 1

if --dep-branch:
    # Cascade ALL deps to branch (even clean ones)
    # Complete isolation from main
fi
```

#### Three Modes

| Mode                 | Condition                      | Behavior                         |
| -------------------- | ------------------------------ | -------------------------------- |
| **Main**             | All deps match main            | Fast, simple, no branch overhead |
| **Error**            | Deps differ, no `--dep-branch` | Blocks with guidance             |
| **Branch Isolation** | `--dep-branch` specified       | Complete isolation, cascade      |

---

### **3. Cascading Dependencies**

#### Dependency Matrix (`workspace-manifest.json`)

```json
{
  "name": "instruments-service",
  "dependencies": [
    {
      "name": "unified-trading-services",
      "path": "../unified-trading-services"
    },
    {
      "name": "unified-config-interface",
      "path": "../unified-config-interface"
    }
  ]
}
```

#### Cascade Algorithm

```
1. Build dependency graph (read all workspace-manifest.json)
2. Topological sort (lowest deps first)
3. For each dep with diff from main:
   → Quickmerge to --dep-branch
4. Finally quickmerge current repo
```

#### Example Flow

```
instruments-service depends on:
  └─> unified-trading-services depends on:
      └─> unified-config-interface

Cascade order:
  1. unified-config-interface @ my-feature
  2. unified-trading-services @ my-feature (after UCI)
  3. instruments-service @ my-feature (after UCS)
```

---

### **4. GitHub Actions Watcher (Mandatory)**

#### Why Mandatory?

**Catches bypasses**: If someone doesn't use quickmerge, watcher detects it.

**Example**:

```bash
# Developer bypasses quickmerge
git add -A
git commit -m "quick fix"
git push

# GitHub Actions watcher detects:
❌ Commit message doesn't match quickmerge pattern
❌ No act simulation evidence
❌ Dependencies not validated

# Blocks PR with guidance:
💬 "This PR was not created via quickmerge.
    Run: bash scripts/quickmerge.sh \"quick fix\"
    This ensures all quality checks pass."
```

#### Implementation

```bash
# .github/scripts/llm-pr-watcher.sh
#!/bin/bash

# Check 1: Was quickmerge used?
if ! git log --format=%s -1 | grep -qE "^(feat|fix|chore|refactor):"; then
    echo "❌ Non-standard commit message"
    echo "💡 Use: bash scripts/quickmerge.sh \"type: message\""
    exit 1
fi

# Check 2: Environment config
ENVIRONMENT=$(grep ENVIRONMENT .env | cut -d= -f2)
if [ "$ENVIRONMENT" = "development" ]; then
    # Verify dev project ID is set
    if [ -z "$GCP_PROJECT_ID_DEV" ]; then
        echo "❌ ENVIRONMENT=development but GCP_PROJECT_ID_DEV not set"
        exit 1
    fi
fi

# Check 3: LLM deep analysis
PROMPT="Analyze this PR for:
- Quickmerge usage
- Environment config correctness
- Dependency cascade correctness
- Codex/Cursor compliance
- Quality gate results

PR Diff:
$(git diff origin/main...HEAD)

PR Description:
$(gh pr view --json body -q .body)

Return:
✅ PASS or ❌ FAIL with specific issues + fix suggestions
"

# Call LLM (Cursor or Claude)
llm_result=$(agent --api-key "$CURSOR_API_KEY" --model auto "$PROMPT")

# Post result as PR comment
gh pr comment --body "$llm_result"

# Block if failed
if echo "$llm_result" | grep -q "❌ FAIL"; then
    exit 1
fi
```

---

## 📋 Implementation Plan (8-12 Hours)

### **Phase 1: Core Infrastructure** (3-4h, 4 agents)

#### Agent 1: Docker & Act Setup

- [ ] Create `quality-gates:latest` Docker image (tools only)
- [ ] Push to Artifact Registry
- [ ] Install `act` tool
- [ ] Configure `~/.secrets` with GH_PAT
- [ ] Test in 2-3 repos

#### Agent 2: Pre-Flight & Cascade Scripts

- [ ] Create `workspace-manifest.json` template
- [ ] Create `pre-flight-audit.sh` (differential check)
- [ ] Create `cascade-dependencies.sh` (topological sort)
- [ ] Create `llm-agent-wrapper.sh`
- [ ] Test cascade in multi-level dependency tree

#### Agent 3: Dev Environment Support

- [ ] Create `.env` template (ENVIRONMENT variable)
- [ ] Add to all 32 repos
- [ ] Set `GCP_PROJECT_ID_DEV` repo variable
- [ ] Update quickmerge to read `.env`
- [ ] Update workflows to use env-aware project ID

#### Agent 4: GitHub Actions Watcher

- [ ] Create `llm-pr-watcher.sh`
- [ ] Create workflow `.github/workflows/pr-watcher.yml`
- [ ] Test in 2-3 repos
- [ ] Verify PR blocking works

---

### **Phase 2: Unified Quickmerge** (2-3h, 4 agents)

Update `scripts/quickmerge.sh` in all 32 repos:

**Changes**:

- [ ] Add differential dependency check (Stage 1)
- [ ] Add pre-flight audit (Stage 2)
- [ ] Add local quality gates - Docker (Stage 3)
- [ ] Add cascade logic (if `--dep-branch`)
- [ ] Add act simulation (Stage 5)
- [ ] Add inline error handling (Stage 6)
- [ ] Add environment-aware project ID

**Agent assignment**: 8 agents × 4 repos each

---

### **Phase 3: GitHub Actions Updates** (2-3h, 4 agents)

Update `.github/workflows/quality-gates.yml` in all 32 repos:

**Changes**:

- [ ] Add environment-aware project ID
- [ ] Add branch-aware dependency cloning
- [ ] Add PR watcher workflow
- [ ] Test end-to-end

**Agent assignment**: 8 agents × 4 repos each

---

### **Phase 4: Cloud Build Updates** (1-2h, 2 agents)

Update `cloudbuild.yaml` in affected repos:

**Changes**:

- [ ] Add environment-aware project ID
- [ ] Add dependency polling (wait for branch packages)
- [ ] Test in dev environment

**Affected repos**: ~10 repos with Cloud Build configs

---

### **Phase 5: Documentation** (1-2h, 2 agents)

#### Agent 1: Codex Docs

Update/create in `unified-trading-codex/`:

- [ ] `06-coding-standards/quickmerge.md` - Complete guide
- [ ] `06-coding-standards/dev-environment.md` - Dev setup
- [ ] `06-coding-standards/branching-strategy.md` - Differential branching
- [ ] `05-infrastructure/github-actions-watcher.md` - Watcher guide

#### Agent 2: Cursor Rules

Update/create in `.cursor/rules/`:

- [ ] `always-use-quickmerge.mdc` - Mandatory quickmerge
- [ ] `differential-branching.mdc` - Branch decision logic
- [ ] `dev-environment.mdc` - Dev vs prod
- [ ] **Update existing rules** to reference quickmerge

**Existing rules to update**:

- `quality-gates-*.mdc` → Point to quickmerge
- `path-dependency-ci.mdc` → Mention cascade
- Any rule mentioning quality gates directly

---

### **Phase 6: Validation** (1h, 4 agents)

#### Test Scenarios

**Scenario 1: Normal main workflow**

```bash
cd instruments-service
vim instruments_service/main.py
bash scripts/quickmerge.sh "feat: add feature"
# ✅ All deps match main → Uses main
```

**Scenario 2: Branch isolation (single repo)**

```bash
cd unified-trading-services
vim unified_trading_services/core.py
bash scripts/quickmerge.sh "fix: update" --dep-branch "my-fix"
# ✅ No deps → Simple branch
```

**Scenario 3: Multi-repo cascade**

```bash
cd instruments-service
vim instruments_service/main.py
vim ../unified-trading-services/core.py
vim ../unified-config-interface/config.py
bash scripts/quickmerge.sh "feat: major update" --dep-branch "major"
# ✅ Cascades: UCI → UCS → instruments
```

**Scenario 4: Dev environment**

```bash
cd instruments-service
echo "ENVIRONMENT=development" > .env
bash scripts/quickmerge.sh "test: dev mode"
# ✅ Uses GCP_PROJECT_ID_DEV
```

**Scenario 5: Bypass attempt (caught by watcher)**

```bash
cd instruments-service
git add -A
git commit -m "quick fix"
git push
gh pr create
# ❌ GitHub Actions watcher blocks PR
```

**Agent assignment**: Each agent tests 1-2 scenarios in different repos

---

## ✅ Success Metrics

### Core CI/CD

- [ ] All three stages use same Python 3.13
- [ ] All three stages use same ruff 0.15.0
- [ ] All three stages use same pytest version
- [ ] Docker image contains tools only (no deps)
- [ ] Local/GitHub/Cloud Build use same committed code

### Quickmerge

- [ ] Differential check works (detects committed+uncommitted diffs)
- [ ] Cascade works (multi-level dependency tree)
- [ ] Act simulation catches GitHub-specific issues
- [ ] Inline error handling works (no separate watcher process)
- [ ] Quickmerge complete in <5 minutes

### Dev Environment

- [ ] `.env` in all 32 repos
- [ ] `GCP_PROJECT_ID_DEV` repo variable set
- [ ] Workflows use environment-aware project ID
- [ ] Dev mode tested successfully

### GitHub Actions Watcher

- [ ] Watcher runs on all PRs
- [ ] Detects quickmerge bypasses
- [ ] Detects environment config issues
- [ ] Provides LLM-enhanced feedback
- [ ] Blocks PRs with critical issues

### Documentation

- [ ] Codex docs updated (4+ docs)
- [ ] Cursor rules updated (4+ rules)
- [ ] Existing rules reference quickmerge
- [ ] All docs consistent with implementation

### Results

- [ ] Zero "works locally, fails in CI" issues
- [ ] Zero accidental main pollution (differential check)
- [ ] Zero manual dep coordination (cascade)
- [ ] <5% PR blocks (watcher catches real issues)

---

## 🔄 Rollback Plan

If issues arise:

1. **Keep old quality-gates.sh** (backup)
2. **Disable watcher** (make non-blocking)
3. **Use main-only mode** (skip `--dep-branch`)
4. **Fix issues** in subset of repos first
5. **Gradual rollout** to remaining repos

---

## 📚 Related Files

### Created During Planning

- `UNIFIED-QUICKMERGE-TEMPLATE.sh` - Template
- `QUICKMERGE-FLOW-DIAGRAM.md` - Visual guide
- `BRANCH-BASED-DEPENDENCIES.md` - Branch mechanics
- `CASCADING-DEPENDENCY-QUICKMERGE.md` - Cascade logic
- `DIFFERENTIAL-BASED-BRANCHING.md` - Decision logic
- `00-MASTER-CICD-PLAN.md` - This file

### To Be Created

- `workspace-manifest.json` (32 repos)
- `.env` (32 repos)
- `llm-pr-watcher.sh` (shared)
- Updated quickmerge.sh (32 repos)
- Updated workflows (32 repos)
- Updated Codex docs (4+ files)
- Updated Cursor rules (4+ files)

---

## 💡 Key Innovations

1. **Differential-based branching** - Detects ALL divergence (not just uncommitted)
2. **Automatic cascade** - No manual dep coordination
3. **Dev environment** - Separate project ID for safe testing
4. **Mandatory watcher** - Catches bypasses, blocks bad PRs
5. **LLM-enhanced feedback** - Rich context, not just logs
6. **Single command** - Quickmerge does everything

---

## 🚀 Next Steps

1. Review this plan
2. Confirm phase order
3. Launch Phase 1 (4 parallel agents)
4. Iterate through phases
5. Validate end-to-end
6. Document any deviations
7. Roll out to all 32 repos

---

## 📊 Estimated Timeline

| Phase                        | Duration   | Parallelism        | Wall Time              |
| ---------------------------- | ---------- | ------------------ | ---------------------- |
| Phase 1: Core Infrastructure | 3-4h       | 4 agents           | 1h                     |
| Phase 2: Unified Quickmerge  | 2-3h       | 8 agents           | 30min                  |
| Phase 3: GitHub Actions      | 2-3h       | 8 agents           | 30min                  |
| Phase 4: Cloud Build         | 1-2h       | 2 agents           | 1h                     |
| Phase 5: Documentation       | 1-2h       | 2 agents           | 1h                     |
| Phase 6: Validation          | 1h         | 4 agents           | 30min                  |
| **Total**                    | **10-15h** | **Up to 8 agents** | **~5 hours wall time** |

With efficient parallel execution: **Can complete in single work session (5-6 hours)**

---

## ✏️ Notes

- This consolidates 5+ separate docs into one actionable plan
- All repos (32) covered in scope
- All documentation (Codex + Cursor rules) covered
- Dev environment support built-in from start
- GitHub Actions watcher makes it production-grade
- Quickmerge is only workflow (enforced)

**Ready to implement!** 🚀
