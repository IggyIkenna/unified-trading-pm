# Quick Start: Running Batch Fix Automation

## Local Environment (macOS) - Already Set Up ✅

Your local environment is ready to go! Just run:

```bash
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/unified-trading-codex/11-project-management/github-integration/scripts/automation
bash run-cleanup-batch-fix.sh
```

The script auto-detects your existing:

- ✅ gh CLI authentication (`gh auth status`)
- ✅ SSH keys (~/.ssh/id_ed25519)
- ✅ Local repos (service + codex + unified-trading-services)

## Fresh GCP VM Setup

### Prerequisites (One-Time)

1. Store GitHub PAT in Secret Manager (see `GITHUB-PAT-SETUP.md`)
2. Grant VM service account access to secret

### VM Setup Commands

```bash
# 1. Create workspace and clone repos
mkdir -p ~/unified-trading-repos && cd ~/unified-trading-repos
git clone https://github.com/IggyIkenna/unified-trading-codex.git
git clone https://github.com/IggyIkenna/unified-trading-services.git

# 2. Setup authentication (installs Cursor CLI, gh CLI, configures auth)
cd unified-trading-codex/11-project-management/github-integration/scripts/automation
bash setup-github-auth.sh

# 3. Clone service repos (now that gh is authenticated)
cd ~/unified-trading-repos
for service in market-data-processing-service instruments-service \
               order-book-service ml-training-service \
               portfolio-reporting-service portfolio-management-service \
               orchestration-service notifications-service \
               position-aggregation-service risk-management-service \
               strategy-execution-service signal-generation-service \
               trade-execution-service; do
    gh repo clone IggyIkenna/$service
done

# 4. Run batch fix automation
cd unified-trading-codex/11-project-management/github-integration/scripts/automation
bash run-cleanup-batch-fix.sh --model sonnet-4 --issues "46 47 48 ..."
```

## What Was Fixed

### 1. **GitHub Authentication** ✅

- **Problem**: Clones couldn't push to GitHub (pointed to local filesystem)
- **Solution**:
  - Auto-detect gh CLI or SSH keys
  - Set remote URL to `https://github.com/IggyIkenna/...` (uses gh for auth)
  - Fallback to SSH if SSH keys detected

### 2. **Missing Dependencies** ✅

- **Problem**: Tests failed with `ModuleNotFoundError: No module named 'unified_trading_services'`
- **Solution**:
  - Clone unified-trading-services into workspace
  - Agent prompt installs it before running quality gates

### 3. **Agent Quality Gates Compliance** ✅

- **Problem**: Agent claimed success without running full quality gates
- **Solution**:
  - Explicit step-by-step instructions in prompt
  - Must see "✅ QUALITY GATES PASSED"
  - Updated all 13 GitHub issues with critical instructions

### 4. **Bash Version** ✅

- **Problem**: macOS default Bash 3.2 lacks associative arrays
- **Solution**: Use `#!/usr/bin/env bash` (finds Homebrew Bash 5.3)

## Architecture

```
Local Repos (Source of Truth)
├── market-data-processing-service/ (origin: GitHub)
├── unified-trading-codex/ (origin: GitHub)
└── unified-trading-services/ (origin: GitHub)
            ↓ (clones locally)
Temporary Clone Workspace
├── market-data-processing-service/ ← remote: https://github.com/IggyIkenna/...
├── unified-trading-codex/
└── unified-trading-services/
            ↓ (agent works here)
Cursor Agent
├── 1. Reads CODEX_VIOLATIONS_MANIFEST.md
├── 2. Fixes all violations
├── 3. Installs unified-trading-services
├── 4. Runs quality gates (4 phases)
└── 5. Quickmerge → pushes to GitHub → creates PR
```

## Security Model

### Local Development

- Uses existing `gh auth` or SSH keys
- No additional setup needed
- Pushes as you (IggyIkenna)

### GCP VM / CI/CD

- GitHub PAT stored in Secret Manager
- VM service account has `secretAccessor` role
- `gh auth login --with-token` (ephemeral, VM-only)
- Token scoped to: Contents (RW), PRs (RW), Issues (RW)

## Files Changed

1. **batch-fix-v2.sh**:
   - Auto-detect auth method (gh/SSH/none)
   - Clone unified-trading-services
   - Fix remote URL to GitHub

2. **auto-fix-issue.sh**:
   - Install unified-trading-services step
   - Explicit quality gates instructions
   - Renumbered steps (1-7)

3. **setup-github-auth.sh** (NEW):
   - Fetch PAT from Secret Manager
   - Configure gh CLI
   - Test authentication

4. **VM-SETUP.md** (NEW):
   - Complete GCP setup guide
   - Security best practices
   - Troubleshooting

## Next Steps

1. **Test locally** (no changes needed):

   ```bash
   cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/unified-trading-codex/11-project-management/github-integration/scripts/automation
   bash run-cleanup-batch-fix.sh
   ```

2. **Set up GCP Secret** (one-time):

   ```bash
   # Generate token: GitHub → Settings → Developer settings → PATs → Fine-grained
   # Permissions: Contents (RW), PRs (RW), Issues (RW)

   echo -n "ghp_yourToken" | gcloud secrets create github-automation-token \
       --project=test-project \
       --data-file=-
   ```

3. **Run on GCP VM** (when ready):
   - Spin up VM
   - Clone codex
   - Run `setup-github-auth.sh`
   - Run `run-cleanup-batch-fix.sh`

## Monitoring

Watch for:

- ✅ Agent completion messages
- ✅ PRs created on GitHub
- ✅ Issues auto-closed when PRs merge
- ❌ Authentication failures (check gh/SSH)
- ❌ Test failures (check unified-trading-services installed)

## Troubleshooting

| Issue                                           | Fix                                                    |
| ----------------------------------------------- | ------------------------------------------------------ |
| "Service directory not found"                   | Fixed - clones into subdirectories now                 |
| "gh: command not found"                         | Install: `brew install gh` (macOS) or see setup script |
| "remote: Repository not found"                  | Check gh auth: `gh auth status`                        |
| "ModuleNotFoundError: unified_trading_services" | Fixed - clones and installs automatically              |
| "Quality gates failed" but agent claims success | Fixed - prompt now explicit about verification         |

## Related Docs

- `VM-SETUP.md` - Complete GCP VM setup guide
- `setup-github-auth.sh` - Auth configuration script
- `batch-fix-v2.sh` - Main automation script
- `auto-fix-issue.sh` - Single issue fix script (called by batch-fix)
