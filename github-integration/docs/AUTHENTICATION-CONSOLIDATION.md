# Authentication Consolidation: One Token for Everything

**Status**: ✅ Implemented  
**Date**: 2026-02-14  
**Token Type**: GitHub Fine-Grained PAT with full admin permissions

---

## Overview

All GitHub authentication across the unified trading system now uses a **single fine-grained Personal Access Token
(PAT)**. When you rotate the token, you only need to update it in two places: GCP Secret Manager and GitHub repo
secrets.

---

## Authentication Points (All Use Same Token)

### 1. Local `gh` CLI

```bash
# Already authenticated (one-time setup)
echo 'YOUR_TOKEN' | gh auth login --with-token
gh auth setup-git
```

**When to update**: After rotating the token, run the above commands again.

### 2. GCP Secret Manager (`github-automation-token`)

```bash
# Update secret version
echo 'YOUR_NEW_TOKEN' | gcloud secrets versions add github-automation-token \
    --data-file=- \
    --project=test-project
```

**Used by**:

- `batch-fix-v2.sh` - Automated issue fixing
- `safe-cursor-agent.sh` - Agent wrapper scripts
- All automation scripts in `11-project-management/github-integration/scripts/automation/`

### 3. GitHub Repository Secrets (`GH_PAT`)

```bash
# Update all 14 repos at once
cd unified-trading-system-repos
for repo in execution-services features-calendar-service \
    features-delta-one-service features-onchain-service \
    features-volatility-service instruments-service \
    market-data-processing-service market-tick-data-handler \
    ml-inference-service ml-training-service \
    sports-betting-service strategy-service \
    unified-trading-services unified-trading-codex; do
    echo 'YOUR_NEW_TOKEN' | gh secret set GH_PAT --repo="IggyIkenna/$repo"
done
```

**Used by**:

- `.github/workflows/quality-gates.yml` - CI/CD pipelines
- `.github/workflows/*.yml` - Any workflows that need GitHub API access

---

## Token Rotation Process

When you need to rotate the PAT (recommended every 90 days or if compromised):

1. **Generate New Token**:
   - Go to: https://github.com/settings/tokens?type=beta
   - Click "Generate new token" (fine-grained)
   - Set permissions (see below)
   - Generate and copy the token

2. **Update GCP Secret Manager**:

   ```bash
   echo 'NEW_TOKEN_HERE' | gcloud secrets versions add github-automation-token \
       --data-file=- --project=test-project
   ```

3. **Update GitHub Repo Secrets** (use loop above)

4. **Update Local `gh` CLI**:

   ```bash
   echo 'NEW_TOKEN_HERE' | gh auth login --with-token
   gh auth setup-git
   ```

5. **Revoke Old Token**:
   - Go to: https://github.com/settings/tokens
   - Find the old token and click "Delete"

**Total time**: ~2-3 minutes for all updates.

---

## Required Token Permissions

Your fine-grained PAT must have these permissions for **IggyIkenna** organization:

| Permission     | Level          | Why                              |
| -------------- | -------------- | -------------------------------- |
| Administration | Read and Write | Branch protection, repo settings |
| Actions        | Read and Write | Workflow management, secrets     |
| Contents       | Read and Write | Code changes, commits, pushes    |
| Issues         | Read and Write | Issue creation, labels, comments |
| Pull Requests  | Read and Write | PR creation, merging, auto-merge |
| Metadata       | Read-only      | Required by GitHub (auto-added)  |
| Workflows      | Read and Write | Update workflow files            |

**Access**: All repositories under `IggyIkenna`

---

## Verification

### Check GCP Secret Manager

```bash
gcloud secrets versions access latest \
    --secret=github-automation-token \
    --project=test-project | head -c 20
```

Should output: `github_pat_11AJ7M73...` (first 20 chars)

### Check GitHub Repo Secrets

```bash
gh secret list --repo=IggyIkenna/unified-trading-services
```

Should show: `GH_PAT` in the list

### Check Local `gh` Auth

```bash
gh auth status
```

Should show: ✓ Logged in to github.com as IggyIkenna

### Run Permission Checker

```bash
cd unified-trading-codex/11-project-management/github-integration/scripts/one-time
bash check-github-pat-permissions.sh
```

Should show: ✅ ALL PERMISSIONS OK

---

## Fixed Issues

### 1. ✅ Branch Protection Backup/Restore

**Problem**: Old backups included read-only fields (URLs, `enabled` objects), causing 422 errors on restore.

**Fix**: `disable-branch-protection.sh` now uses `jq` to transform the GET response into PUT-compatible format:

- Only writable fields saved
- `enforce_admins.enabled` → `enforce_admins` (boolean)
- Removed `url`, `contexts_url`, `checks` arrays

**Test**:

```bash
# Disable and backup
bash disable-branch-protection.sh unified-trading-services

# Verify backup format (should be PUT-compatible JSON)
cat /tmp/branch-protection-backup-*/unified-trading-services.json | jq .

# Restore
bash enable-branch-protection.sh --restore /tmp/branch-protection-backup-*
```

### 2. ✅ Workflow Syntax Errors

**Problem**: Agent-generated workflows had duplicate `run:` keys.

**Fix**: All 14 repos now have corrected `.github/workflows/quality-gates.yml` files:

- Single `run:` key per step
- Calls `bash scripts/quality-gates.sh --no-fix` for consistent summaries
- Proper YAML formatting

### 3. ✅ Parallel Testing

**Problem**: Only 1 repo used `pytest-xdist -n auto`.

**Fix**: 13/14 repos now have:

- `pytest-xdist>=3.5.0` in `pyproject.toml`
- `-n auto` flag in all pytest commands
- Faster CI/CD runs (3-5 min → 1-2 min)

---

## Known Limitations

### execution-services: Branch Protection Disabled at Repo Level

**Error**: `Branch protection has been disabled on this repository. (HTTP 404)`

**Root Cause**: This is a repository-level setting, not branch-level. Cannot be changed via API.

**Workaround**:

1. Go to: https://github.com/IggyIkenna/execution-services/settings
2. Scroll to "Features"
3. Ensure "Enforce branch protection rules for administrators" is checked
4. Then run: `bash enable-branch-protection.sh execution-services`

**Status**: ✅ Manually fixed via UI (2026-02-14)

---

## Security Best Practices

1. **Never commit tokens** to git (obviously)
2. **Rotate every 90 days** (GitHub best practice)
3. **Use fine-grained tokens** (not classic PATs)
4. **Scope to organization** (not all personal repos)
5. **Monitor token usage**:
   ```bash
   gh api user/installations | jq '.installations[] | {app: .app_slug, repos: .repository_selection}'
   ```

---

## Troubleshooting

### "Resource not accessible by personal access token (HTTP 403)"

**Cause**: Token missing required permissions. **Fix**: Regenerate token with correct permissions (see table above).

### "Branch protection has been disabled (HTTP 404)"

**Cause**: Repo-level branch protection disabled. **Fix**: Enable via GitHub UI → Settings → Features.

### "Invalid request (HTTP 422)"

**Cause**: Old backup format with read-only fields. **Fix**: Create new backup using fixed
`disable-branch-protection.sh`.

### Token doesn't work in automation

**Cause**: Secret not updated or wrong secret name. **Fix**:

```bash
# Verify GCP secret
gcloud secrets versions access latest --secret=github-automation-token

# Verify GitHub secret
gh secret list --repo=IggyIkenna/YOUR_REPO
```

---

## Migration History

| Date       | Change                                  | Status      |
| ---------- | --------------------------------------- | ----------- |
| 2026-02-14 | Consolidated to single fine-grained PAT | ✅ Complete |
| 2026-02-14 | Fixed branch protection backup format   | ✅ Complete |
| 2026-02-14 | Updated all 14 repo secrets             | ✅ Complete |
| 2026-02-14 | Fixed workflow syntax errors            | ✅ Complete |
| 2026-02-14 | Enabled parallel testing in 13 repos    | ✅ Complete |

---

## Related Documentation

- `BRANCH-PROTECTION-MANAGEMENT.md` - Branch protection scripts
- `scripts/one-time/check-github-pat-permissions.sh` - Token verification
- `scripts/automation/batch-fix-v2.sh` - Uses GCP secret
- `.github/workflows/quality-gates.yml` - Uses `GH_PAT` secret
