# Batch Fix Automation Architecture

## Complete System Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. ONE-TIME SETUP (You, locally)                                    │
├─────────────────────────────────────────────────────────────────────┤
│ GitHub → Settings → PATs → Fine-grained                             │
│   ├─ Create token: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx         │
│   ├─ Permissions: Contents (RW), PRs (RW), Issues (RW)              │
│   └─ Expiration: 90 days or no expiration                           │
│                                                                      │
│ GCP Secret Manager                                                   │
│   ├─ gcloud secrets create github-automation-token                  │
│   ├─ Store token value                                              │
│   └─ Grant VM service account: secretAccessor role                  │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 2. FRESH GCP VM SETUP (One-time per VM)                             │
├─────────────────────────────────────────────────────────────────────┤
│ mkdir ~/unified-trading-repos && cd ~/unified-trading-repos         │
│                                                                      │
│ git clone https://github.com/IggyIkenna/unified-trading-codex.git   │
│ git clone https://github.com/IggyIkenna/unified-trading-services.git  │
│                                                                      │
│ cd unified-trading-codex/.../automation                             │
│ bash setup-github-auth.sh                                           │
│   ├─ Installs Cursor CLI (/usr/local/bin/cursor)                   │
│   ├─ Installs gh CLI                                                │
│   ├─ Fetches PAT from Secret Manager                                │
│   ├─ gh auth login --with-token                                     │
│   ├─ gh auth setup-git (git uses gh for auth)                       │
│   └─ Tests: gh repo view IggyIkenna/unified-trading-codex           │
│                                                                      │
│ for service in market-data-processing-service ...; do               │
│     gh repo clone IggyIkenna/$service                               │
│ done                                                                 │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 3. RUN BATCH FIX (Repeatable)                                       │
├─────────────────────────────────────────────────────────────────────┤
│ bash run-cleanup-batch-fix.sh --model sonnet-4 --issues "46 47 ..." │
│   ├─ Auto-detects WORKSPACE_ROOT (~/unified-trading-repos)          │
│   ├─ Validates: unified-trading-codex exists ✓                      │
│   ├─ Validates: unified-trading-services exists ✓                     │
│   └─ Calls batch-fix-v2.sh                                          │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 4. WORKSPACE POOLING (batch-fix-v2.sh)                              │
├─────────────────────────────────────────────────────────────────────┤
│ For each service with issues:                                       │
│   Create temporary clone workspace:                                 │
│     /tmp/workspace-pool/clone-001/                                  │
│       ├─ market-data-processing-service/  ← from local source       │
│       ├─ unified-trading-codex/           ← from local source       │
│       └─ unified-trading-services/          ← from local source       │
│                                                                      │
│   Fix git remote (point to GitHub):                                 │
│     cd market-data-processing-service                               │
│     if gh auth status; then                                         │
│       git remote set-url origin https://github.com/.../             │
│     elif [ -f ~/.ssh/id_ed25519 ]; then                             │
│       git remote set-url origin git@github.com:.../                 │
│     fi                                                               │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 5. CURSOR AGENT EXECUTION (auto-fix-issue.sh)                       │
├─────────────────────────────────────────────────────────────────────┤
│ For each issue assigned to this clone:                              │
│                                                                      │
│   WORKSPACE_ROOT=/tmp/workspace-pool/clone-001                      │
│   cursor agent --workspace $WORKSPACE_ROOT --model sonnet-4 \       │
│     --print --force "                                                │
│                                                                      │
│   Agent instructions:                                                │
│     1. cd market-data-processing-service                            │
│     2. Read CODEX_VIOLATIONS_MANIFEST.md (all violations)           │
│     3. Fix all violations (including examples/)                     │
│     4. Install unified-trading-services:                              │
│        cd ../unified-trading-services && uv pip install -e .          │
│     5. Run quality gates (4 phases):                                │
│        bash scripts/quality-gates.sh --no-fix                       │
│        - Config ✅                                                   │
│        - Linting ✅                                                  │
│        - Tests ✅ (now pass with unified-trading-services)            │
│        - Codex ✅                                                    │
│     6. Wait for: ✅ QUALITY GATES PASSED                            │
│     7. Quickmerge:                                                   │
│        bash scripts/quickmerge.sh \"Fixes #46: ...\" --files \"...\" │
│   "                                                                  │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 6. GIT PUSH TO GITHUB (via quickmerge.sh)                           │
├─────────────────────────────────────────────────────────────────────┤
│ Inside the clone:                                                    │
│   git checkout -b fix/cod-violations-46                             │
│   git add <changed files>                                           │
│   git commit -m "Fixes #46: Remove print() statements"              │
│   git push -u origin fix/cod-violations-46                          │
│     ↓                                                                │
│   Uses gh CLI for authentication:                                   │
│     - gh CLI authenticated with PAT from Secret Manager             │
│     - git uses gh (via gh auth setup-git)                           │
│     - Push succeeds to GitHub ✅                                     │
│                                                                      │
│   gh pr create --title "..." --body "Fixes #46"                     │
│   gh pr merge --auto --squash                                       │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 7. GITHUB ACTIONS (PR validation)                                   │
├─────────────────────────────────────────────────────────────────────┤
│ PR created → GitHub Actions triggered                               │
│   - Checkout code                                                    │
│   - Run quality gates (same as local)                               │
│   - If pass → auto-merge enabled → PR merges                        │
│   - Issue #46 auto-closed (due to "Fixes #46" in commit)            │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 8. CLEANUP (batch-fix-v2.sh)                                        │
├─────────────────────────────────────────────────────────────────────┤
│ Unless --keep-workspaces:                                           │
│   rm -rf /tmp/workspace-pool/                                       │
│                                                                      │
│ Report:                                                              │
│   ✅ 15 issues fixed                                                 │
│   ❌ 2 issues failed                                                 │
│   ⏱️  Total time: 25m 30s                                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Authentication Flow Details

### Local Development (macOS)

```
You (IggyIkenna)
  ├─ Already authenticated: gh auth login (interactive)
  ├─ Or: SSH keys (~/.ssh/id_ed25519)
  └─ Pushes as you (your GitHub identity)
        ↓
batch-fix-v2.sh
  ├─ Auto-detects: gh auth status ✓
  ├─ Sets remote: https://github.com/IggyIkenna/...
  └─ git push → uses gh CLI → uses your session
```

### GCP VM (Automated)

```
GitHub PAT (fine-grained)
  ├─ Created by you in GitHub UI
  └─ Stored in GCP Secret Manager
        ↓
VM Service Account
  ├─ Has secretAccessor role
  └─ Can fetch PAT from Secret Manager
        ↓
setup-github-auth.sh
  ├─ Fetches: gcloud secrets versions access latest
  ├─ Authenticates: echo "$PAT" | gh auth login --with-token
  └─ Configures: gh auth setup-git
        ↓
batch-fix-v2.sh
  ├─ Auto-detects: gh auth status ✓
  ├─ Sets remote: https://github.com/IggyIkenna/...
  └─ git push → uses gh CLI → uses PAT → authenticated ✅
```

---

## Why unified-trading-services is Required

### The Problem

```
Service repos (market-data-processing-service, etc.)
  ├─ pyproject.toml: dependencies = ["unified-trading-services>=1.0.0"]
  └─ tests/: from unified_trading_services import ...
        ↓
Quality gates run tests
  ├─ pytest discovers tests/
  ├─ Imports: from unified_trading_services import ...
  └─ ❌ ModuleNotFoundError: No module named 'unified_trading_services'
```

### The Solution

```
Clone workspace structure:
/tmp/workspace-pool/clone-001/
  ├─ market-data-processing-service/  ← service under test
  ├─ unified-trading-codex/           ← for @ references
  └─ unified-trading-services/          ← for dependencies
        ↓
Agent prompt (auto-fix-issue.sh):
  if [ -d "../unified-trading-services" ]; then
    cd ../unified-trading-services
    uv pip install -e .  ← installs in editable mode
    cd ../market-data-processing-service
  fi
        ↓
Quality gates run tests
  ├─ pytest discovers tests/
  ├─ Imports: from unified_trading_services import ...
  └─ ✅ Module found (installed from ../unified-trading-services)
```

---

## Cursor CLI on Fresh VM

### Why It's Needed

```
batch-fix-v2.sh calls:
  cursor agent --workspace /tmp/clone-001 --model sonnet-4 ...
        ↓
Without Cursor CLI:
  ❌ bash: cursor: command not found
        ↓
With setup-github-auth.sh:
  ✅ Installs Cursor CLI to /usr/local/bin/cursor
  ✅ Available in PATH
  ✅ Agent can run
```

### What setup-github-auth.sh Installs

#### On Linux (GCP VM)

```bash
# Downloads Cursor CLI for Linux
curl -fsSL https://download.cursor.sh/linux/cli/latest \
  -o /tmp/cursor-cli
chmod +x /tmp/cursor-cli
sudo mv /tmp/cursor-cli /usr/local/bin/cursor
```

#### On macOS (Local Dev)

```bash
# Usually already installed (Cursor.app)
# But script adds to PATH if needed:
export PATH="/Applications/Cursor.app/Contents/Resources/app/bin:$PATH"
```

---

## Files Reference

| File                       | Purpose                                                   |
| -------------------------- | --------------------------------------------------------- |
| `GITHUB-PAT-SETUP.md`      | Step-by-step PAT creation & Secret Manager setup          |
| `VM-SETUP.md`              | Complete fresh VM setup guide                             |
| `QUICK-START.md`           | Quick reference for local and VM                          |
| `setup-github-auth.sh`     | Installs Cursor CLI, gh CLI, fetches PAT, configures auth |
| `batch-fix-v2.sh`          | Main automation (workspace pooling, parallel execution)   |
| `auto-fix-issue.sh`        | Single issue fix (called by batch-fix-v2.sh)              |
| `run-cleanup-batch-fix.sh` | Wrapper (ensures Bash 5+, calls batch-fix-v2.sh)          |

---

## Security Model

### Secrets Storage

| Secret Type | Storage                 | Access             | Lifetime            |
| ----------- | ----------------------- | ------------------ | ------------------- |
| GitHub PAT  | GCP Secret Manager      | VM service account | 90 days (renewable) |
| Git commits | Signed by bot identity  | Public on GitHub   | Permanent           |
| SSH keys    | N/A (using HTTPS + PAT) | N/A                | N/A                 |

### Permissions

| Component    | Needs Access To  | Via                                  |
| ------------ | ---------------- | ------------------------------------ |
| VM           | Secret Manager   | IAM role: `secretAccessor`           |
| gh CLI       | GitHub API       | PAT (Contents RW, PRs RW, Issues RW) |
| git push     | GitHub repos     | gh CLI (uses PAT)                    |
| Cursor agent | Local files only | Filesystem (in clone workspace)      |

### Audit Trail

```
GCP Secret Manager
  └─ Access logs: who fetched secret, when
        ↓
GitHub
  ├─ Commits: signed by bot identity
  ├─ PRs: created by bot
  └─ Issue comments: posted by bot
        ↓
Cloud Logging
  └─ batch-fix-v2.sh output (success/failure per issue)
```

---

## Troubleshooting Quick Reference

| Error                                           | Cause                       | Fix                                       |
| ----------------------------------------------- | --------------------------- | ----------------------------------------- |
| `cursor: command not found`                     | Cursor CLI not installed    | Run `setup-github-auth.sh`                |
| `gh: command not found`                         | gh CLI not installed        | Run `setup-github-auth.sh`                |
| `Permission denied (Secret Manager)`            | VM lacks IAM role           | Grant `secretAccessor` to service account |
| `remote: Repository not found`                  | PAT lacks repo access       | Regenerate PAT with "All repos"           |
| `ModuleNotFoundError: unified_trading_services` | Dependency not installed    | Already fixed (auto-installs in clone)    |
| `Service directory not found`                   | Wrong workspace structure   | Already fixed (auto-detects workspace)    |
| `Quality gates failed` but agent claims success | Insufficient prompt clarity | Already fixed (explicit verification)     |
