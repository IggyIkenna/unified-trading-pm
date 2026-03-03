# GitHub Token Setup for Project Management

**Purpose:** Create a GitHub token with permissions to manage projects (read/write) for automated scripts

**Use case:** Running scripts like `setup-cod-project.py`, `create-all-projects.py` that create/modify GitHub projects

---

## Option 1: Personal Access Token (Classic) - Recommended for Scripts

### Step 1: Generate the Token

1. Go to GitHub Settings: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Give it a descriptive name: `Project Management - Automation Scripts`
4. Set expiration: **No expiration** (or 90 days if you prefer, but you'll need to regenerate)

### Step 2: Select Required Scopes

**For user-level projects (IggyIkenna is a user, not org):**

✅ **Required scopes:**

- `repo` (Full control of private repositories)
  - Includes: repo:status, repo_deployment, public_repo, repo:invite, security_events
- `project` (Full control of projects)
  - Includes: project:read, project:write
- `read:org` (Read org and team membership, read org projects)
- `write:org` (Read and write org and team membership, read and write org projects) - **IF** you need org-level projects

**For user projects specifically (IggyIkenna):**

- `project` scope is sufficient for user-level projects
- `repo` scope gives access to create issues, labels, etc.

### Step 3: Generate and Copy Token

1. Click **"Generate token"** at the bottom
2. **CRITICAL:** Copy the token immediately (you won't see it again!)
3. Save it securely (password manager, `.env` file, etc.)

**Token format:** `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (starts with `ghp_`)

---

## Option 2: Fine-Grained Personal Access Token (New, More Secure)

### Step 1: Generate Fine-Grained Token

1. Go to: https://github.com/settings/personal-access-tokens/new
2. Token name: `Project Management - Automation Scripts`
3. Expiration: 90 days (max for fine-grained tokens)
4. Description: "Token for automated project creation and management"

### Step 2: Resource Owner

- Select: **IggyIkenna** (your user account)

### Step 3: Repository Access

Choose one:

- **All repositories** (recommended for scripts that work across all repos)
- **Only select repositories** (if you want to limit access)

### Step 4: Permissions

**Repository permissions:**

- Issues: **Read and write**
- Metadata: **Read-only** (automatically selected)
- Projects: **Read and write**

**Account permissions (under user):**

- Projects: **Read and write** ← **CRITICAL for user-level projects**

### Step 5: Generate and Copy

1. Click **"Generate token"**
2. Copy the token: `github_pat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (starts with `github_pat_`)
3. Save securely

---

## Which Option to Choose?

| Feature                  | Classic Token        | Fine-Grained Token         |
| ------------------------ | -------------------- | -------------------------- |
| **Max expiration**       | No expiration        | 90 days                    |
| **Granular permissions** | No (scope-based)     | Yes (resource-based)       |
| **Org-level access**     | Easy                 | Requires org approval      |
| **Recommended for**      | Long-term automation | Short-term, specific tasks |

**For automation scripts:** Use **Classic Token** with `repo` + `project` scopes.

**Why:** No expiration means scripts won't break after 90 days. Fine-grained tokens expire and require regeneration.

---

## Step 3: Configure Token for Scripts

### Option A: Environment Variable (Recommended)

```bash
# Add to your shell profile (~/.zshrc or ~/.bashrc)
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Reload shell
source ~/.zshrc  # or source ~/.bashrc
```

**Verify:**

```bash
echo $GITHUB_TOKEN
# Should print: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Option B: .env File (For Local Development)

Create `.env` in your workspace root:

```bash
# .env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**CRITICAL:** Add `.env` to `.gitignore`:

```bash
echo ".env" >> .gitignore
git add .gitignore
git commit -m "Ignore .env files"
```

Load in Python scripts:

```python
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("GITHUB_TOKEN")
```

### Option C: Pass Directly to gh CLI

```bash
# Set for gh CLI
gh auth login --with-token <<< "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Verify
gh auth status

# Get token from gh CLI in scripts
token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()
```

---

## Step 4: Test Token Permissions

### Test with GitHub API (curl)

```bash
# Test authentication
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user

# Test project access (user-level)
curl -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/users/IggyIkenna/projects

# Test repo access
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user/repos
```

**Expected result:** JSON response with your user info, projects, repos.

### Test with gh CLI

```bash
# Set token
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Test project list
gh project list --owner IggyIkenna

# Test issue creation (will create real issue - delete after)
gh issue create --repo IggyIkenna/test-repo --title "Test" --body "Testing token"

# Clean up
gh issue close <issue-number> --repo IggyIkenna/test-repo
```

### Test with Python Scripts

```bash
# Test with setup-cod-project.py (dry run)
cd unified-trading-codex/11-project-management/github-integration
python setup-cod-project.py --org IggyIkenna --dry-run

# Test with create-all-projects.py (dry run)
python create-all-projects.py --org IggyIkenna --dry-run
```

**Expected result:** Scripts run without authentication errors.

---

## Troubleshooting

### Error: "Resource not accessible by personal access token"

**Cause:** Token doesn't have required permissions.

**Fix:**

1. Go back to token settings: https://github.com/settings/tokens
2. Click on your token
3. Check **BOTH**:
   - `repo` (for repository access)
   - `project` (for project access)
4. Click **"Update token"**
5. Regenerate if needed

### Error: "Bad credentials"

**Cause:** Token not set or incorrect.

**Fix:**

```bash
# Check if token is set
echo $GITHUB_TOKEN

# If empty, set it
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Test
gh auth status
```

### Error: "Not Found" when accessing projects

**Cause:** Wrong project scope (org vs user).

**Fix:**

- For user projects: `https://github.com/users/IggyIkenna/projects`
- For org projects: `https://github.com/orgs/IggyIkenna/projects`

**Check account type:**

```bash
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/users/IggyIkenna

# Look for "type": "User" or "type": "Organization"
```

If "User", you have user-level projects, not org-level.

### Error: "gh: command not found"

**Fix:** Install GitHub CLI:

```bash
# macOS
brew install gh

# Verify
gh --version
```

### Token Expired (Fine-Grained Tokens)

**Fix:** Regenerate token every 90 days:

1. Go to: https://github.com/settings/personal-access-tokens
2. Click **"Regenerate token"** next to your token
3. Copy new token
4. Update `GITHUB_TOKEN` environment variable

**Better solution:** Use Classic Token with no expiration for automation.

---

## Security Best Practices

### 1. Never Commit Tokens to Git

```bash
# Check if token is in any files
rg "ghp_" --no-ignore

# If found, remove and add to .gitignore
```

### 2. Use Minimal Permissions

Only grant scopes you actually need:

- Projects only? → Just `project` scope
- Need repo access too? → Add `repo` scope
- Don't need org access? → Don't add `write:org`

### 3. Rotate Tokens Regularly

Even with "no expiration", rotate every 6-12 months:

1. Generate new token
2. Update scripts
3. Delete old token

### 4. Use GitHub Secrets for CI/CD

If running scripts in GitHub Actions:

1. Add token to repository secrets: Settings → Secrets → Actions
2. Name it: `PROJECT_MANAGEMENT_TOKEN`
3. Reference in workflow: `${{ secrets.PROJECT_MANAGEMENT_TOKEN }}`

### 5. Audit Token Usage

Check token usage: https://github.com/settings/tokens

- See when token was last used
- Review which repos accessed
- Revoke if suspicious activity

---

## For Our Scripts

### setup-cod-project.py

**Requires:**

- `repo` scope (create labels, find issues, add to projects)
- `project` scope (create project, add items)

**Setup:**

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
python setup-cod-project.py --org IggyIkenna --apply
```

### create-all-projects.py

**Requires:**

- `repo` scope (create labels in repos)
- `project` scope (create projects)

**Setup:**

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
python create-all-projects.py --org IggyIkenna --apply
```

### manage-cods.sh

**Requires:**

- Token set in environment OR authenticated with `gh auth login`

**Setup:**

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
bash manage-cods.sh setup
```

---

## Quick Start (TL;DR)

```bash
# 1. Generate token
# Go to: https://github.com/settings/tokens
# Select: repo + project scopes
# Copy token: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 2. Set environment variable
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# 3. Add to shell profile (persist across sessions)
echo 'export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"' >> ~/.zshrc
source ~/.zshrc

# 4. Test
gh auth status
gh project list --owner IggyIkenna

# 5. Run scripts
python setup-cod-project.py --org IggyIkenna --dry-run
python create-all-projects.py --org IggyIkenna --dry-run
```

---

## Verification Checklist

Before running scripts, verify:

- [ ] Token generated with correct scopes (`repo` + `project`)
- [ ] Token saved securely (password manager or .env file)
- [ ] `GITHUB_TOKEN` environment variable set
- [ ] `gh auth status` shows authenticated
- [ ] `gh project list --owner IggyIkenna` returns projects
- [ ] Scripts run in dry-run mode without errors
- [ ] Token NOT committed to git (check with `git status`)

---

## References

- GitHub PAT Documentation:
  https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token
- GitHub Projects API: https://docs.github.com/en/rest/projects
- GitHub CLI Auth: https://cli.github.com/manual/gh_auth_login
- Token Scopes: https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps

---

**Status:** ✅ Ready to use  
**Last Updated:** 2026-02-13  
**Version:** 1.0
