# Branch Protection Management

**Status**: ✅ Fixed (2026-02-14) **Issue**: Backup/restore was broken due to read-only fields in backup format **Fix**:
`disable-branch-protection.sh` now uses `jq` to save only writable fields

---

## Problem: Direct Pushes to Main Blocked

```
remote: error: GH006: Protected branch update failed for refs/heads/main.
remote: - Required status check "quality-gates" is expected.
! [remote rejected] main -> main (protected branch hook declined)
```

This happens when you try to push directly to main with branch protection enabled.

---

## Solution: Temporarily Disable, Push, Re-enable

### Method 1: Via Scripts (Requires Admin PAT)

**Disable protection:**

```bash
cd unified-trading-codex/11-project-management/github-integration/scripts/one-time
bash disable-branch-protection.sh --all
```

**Push changes:**

```bash
git push origin main
```

**Re-enable protection:**

```bash
bash enable-branch-protection.sh --all
# Or restore from backup
bash enable-branch-protection.sh --restore /tmp/branch-protection-backup-XXXXXX
```

**If you get 403 errors:**

```
gh: Resource not accessible by personal access token (HTTP 403)
```

Your PAT needs **admin permissions**. See Method 2.

---

### Method 2: Via GitHub UI (When PAT Lacks Admin Scope)

When your PAT gives 403 errors, use the GitHub UI:

#### Step 1: Disable Protection (Per Repo)

For each repo needing push:

1. Go to: `https://github.com/IggyIkenna/<repo>/settings/branches`
2. Find "main" branch protection rule
3. Click "Edit" (or "Delete" to fully remove)
4. **Option A (Temporary):** Uncheck "Require status checks to pass before merging"
5. **Option B (Full disable):** Click "Delete protection rule" at bottom
6. Click "Save changes" (Option A) or confirm deletion (Option B)

#### Step 2: Push Changes

```bash
cd <repo>
git push origin main
```

#### Step 3: Re-enable Protection

1. Go back to branch protection settings
2. **Option A:** Re-check "Require status checks to pass before merging"
3. **Option B:** Click "Add branch protection rule"
   - Branch name pattern: `main`
   - ✅ Require status checks to pass: `quality-gates`
   - ✅ Require branches to be up to date
   - ✅ Include administrators
   - ✅ Allow auto-merge
   - ✅ Automatically delete head branches
4. Save changes

---

### Method 3: Bulk Disable Via GitHub UI Settings

**For organization-level changes:**

1. Go to: `https://github.com/organizations/IggyIkenna/settings/repository-defaults` (if org)
2. Or use GitHub's bulk settings tool (if available)

**Note:** This only works for org accounts, not personal accounts.

---

## Scripts Created

### 1. `disable-branch-protection.sh`

**Disables branch protection via GitHub API**

```bash
# All repos
bash disable-branch-protection.sh --all

# Specific repos
bash disable-branch-protection.sh unified-trading-services market-tick-data-handler

# Backup protection configs to restore later
# Automatically saves to /tmp/branch-protection-backup-YYYYMMDD-HHMMSS/
```

**Features:**

- Backs up existing protection configs (for restore)
- Handles 403 errors gracefully
- Shows which repos succeeded/failed

**Requirements:**

- GitHub CLI authenticated: `gh auth login`
- PAT with **admin** scope (fine-grained: "Administration: Read/Write")

### 2. `enable-branch-protection.sh`

**Re-enables branch protection**

```bash
# Restore from backup
bash enable-branch-protection.sh --restore /tmp/branch-protection-backup-YYYYMMDD-HHMMSS

# Use default config for all repos
bash enable-branch-protection.sh --all

# Specific repos with default config
bash enable-branch-protection.sh unified-trading-services
```

**Default protection config:**

- ✅ Require status checks: `quality-gates`
- ✅ Require branches up to date
- ✅ Enforce for admins
- ❌ No PR reviews required (self-managed repos)
- ❌ No restrictions (all users can push via PR)

---

## PAT Permissions Required

### For Classic PAT

Go to: https://github.com/settings/tokens

**Required scopes:**

- `repo` (full control of private repositories)

This includes:

- `repo:status`
- `repo_deployment`
- `public_repo`
- `repo:invite`
- `security_events`

### For Fine-Grained PAT

Go to: https://github.com/settings/tokens?type=beta

**Required permissions:**

- **Administration**: Read and Write
- **Contents**: Read and Write
- **Metadata**: Read-only

**Repository access:**

- Select all 14 repos, OR
- All repositories

---

## Workflow for Bulk Updates

### Standard Workflow (With quickmerge)

```bash
# 1. Make changes locally
# 2. Run quality gates
bash scripts/quality-gates.sh

# 3. Use quickmerge (creates PR, no branch protection issues)
bash scripts/quickmerge.sh "message" --files "..."
```

**Recommended:** Always use quickmerge for normal workflow.

### Exception Workflow (Direct push needed)

```bash
# 1. Disable protection
bash disable-branch-protection.sh --all

# 2. Push directly
cd unified-trading-deployment-v2
for repo in */; do
  cd "$repo"
  git push origin main 2>&1 | grep -v "Everything up-to-date"
  cd ..
done

# 3. Re-enable protection
bash enable-branch-protection.sh --all
```

**Use only when:**

- Bulk updates across many repos
- Workflow changes that affect PR creation itself
- Emergency fixes

---

## Troubleshooting

### 403 Forbidden

**Problem:**

```
gh: Resource not accessible by personal access token (HTTP 403)
```

**Solutions:**

**A. Update PAT permissions:**

1. Go to: https://github.com/settings/tokens
2. Click on your token
3. Add "Administration" permission (Read/Write)
4. Regenerate token
5. Update in terminal: `gh auth login --with-token < new_token.txt`

**B. Use GitHub UI** (see Method 2 above)

**C. Use organization admin account** (if org-owned repos)

### 404 Not Found

**Problem:**

```
gh: Not Found (HTTP 404)
```

**Cause:** Branch protection already disabled or repo doesn't exist

**Solution:** Already done! Just push.

### PAT Expired

**Problem:**

```
gh: Bad credentials (HTTP 401)
```

**Solution:**

```bash
gh auth login --with-token < ~/.github/token.txt
```

---

## Security Notes

1. **Minimize disable time**: Re-enable immediately after pushing
2. **Use backup/restore**: Preserve exact protection configs
3. **Prefer quickmerge**: Only disable for bulk operations
4. **Track changes**: Log who disabled and when
5. **Admin PATs**: Store securely (Secret Manager, not in code)

---

## Quick Reference

| Task           | Command                                                   |
| -------------- | --------------------------------------------------------- |
| Disable all    | `bash disable-branch-protection.sh --all`                 |
| Disable one    | `bash disable-branch-protection.sh <repo>`                |
| Push all       | `cd /workspace && git push origin main` (in each repo)    |
| Enable all     | `bash enable-branch-protection.sh --all`                  |
| Restore backup | `bash enable-branch-protection.sh --restore <dir>`        |
| Check status   | `gh api repos/IggyIkenna/<repo>/branches/main/protection` |

---

## Fixed: Backup/Restore Now Works

### Problem (Before 2026-02-14)

Backup files saved the full GitHub API GET response, which included read-only fields:

```json
{
  "url": "https://api.github.com/repos/...",  // ❌ Read-only
  "enforce_admins": {
    "url": "...",
    "enabled": true  // ❌ Should be boolean at top level
  },
  "required_status_checks": {
    "contexts": ["quality-gates"],
    "checks": [...]  // ❌ Read-only
  }
}
```

When restoring, GitHub API returned:

```
422 Invalid request: "enforce_admins", "required_pull_request_reviews",
"required_status_checks", "restrictions" weren't supplied.
```

### Solution (After 2026-02-14)

`disable-branch-protection.sh` now uses `jq` to transform GET response into PUT-compatible format:

```json
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["quality-gates"]
  },
  "enforce_admins": true, // ✅ Boolean, not object
  "required_pull_request_reviews": null,
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false
}
```

### Test the Fix

```bash
# Disable and backup
bash disable-branch-protection.sh unified-trading-services

# Verify backup has correct format
cat /tmp/branch-protection-backup-*/unified-trading-services.json | jq .

# Restore should work without errors
bash enable-branch-protection.sh --restore /tmp/branch-protection-backup-*
```

**Result**: ✅ Backup/restore now works perfectly for all repos.

---

## Alternative: Use Quickmerge Instead

If you find yourself frequently needing to disable protection, consider:

**Problem:** You're pushing directly to main

**Better solution:** Use the quickmerge workflow:

```bash
bash git-quickmerge.sh "message" --all
```

This:

- Creates PRs (no protection issues)
- Runs quality gates
- Auto-merges when gates pass
- No need to disable protection

**Only disable protection for:**

- Workflow file changes (that affect PR creation)
- Bulk updates across 10+ repos
- Emergency hotfixes
