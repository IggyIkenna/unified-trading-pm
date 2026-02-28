# GitHub Personal Access Token Setup

## You've Created the Token ✅

You're at: GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens

**IMPORTANT**: Copy the token now (starts with `ghp_`). You won't see it again!

```
ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Where to Store It: GCP Secret Manager (NOT Repo Secrets)

### ❌ Don't Use GitHub Repository Secrets

GitHub repository secrets are for GitHub Actions workflows only. They **cannot** be accessed by external VMs or scripts.

```yaml
# This is for GitHub Actions only:
jobs:
  build:
    steps:
      - uses: actions/checkout@v4
      - run: echo ${{ secrets.MY_SECRET }} # Only works in GitHub Actions
```

### ✅ Use GCP Secret Manager

For running automation on GCP VMs, store the token in Secret Manager:

```bash
# Store your GitHub PAT in Secret Manager
echo -n "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" | \
  gcloud secrets create github-automation-token \
    --project=test-project \
    --data-file=-
```

**Verify it was stored**:

```bash
gcloud secrets versions access latest \
  --secret=github-automation-token \
  --project=test-project
```

You should see your token printed (starts with `ghp_`).

---

## Grant VM Access to the Secret

Your VMs need permission to read the secret:

### Option 1: Default Compute Engine Service Account

```bash
# Get your project number
PROJECT_NUMBER=$(gcloud projects describe test-project --format="value(projectNumber)")

# The default service account
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Grant access
gcloud secrets add-iam-policy-binding github-automation-token \
  --project=test-project \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"
```

### Option 2: Specific Service Account (More Secure)

If you created a custom service account for automation:

```bash
gcloud secrets add-iam-policy-binding github-automation-token \
  --project=test-project \
  --member="serviceAccount:github-automation@test-project.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

## Test Access from VM

SSH into any GCP VM and test:

```bash
gcloud secrets versions access latest \
  --secret=github-automation-token \
  --project=test-project
```

If you see your token, it works! ✅

If you get a permission denied error:

- Check the service account has `secretAccessor` role
- Verify you're running on a VM with the correct service account attached

---

## Token Permissions (What You Set in GitHub)

When you created the fine-grained token, you should have set:

### Repository Access

- **All repositories** (or select specific ones)

### Permissions

- ✅ **Contents**: Read and write (to push commits)
- ✅ **Pull requests**: Read and write (to create PRs)
- ✅ **Issues**: Read and write (to close issues)
- ⚪ **Workflows**: Read (optional, if triggering CI)

### Expiration

- **90 days** (recommended for security)
- **No expiration** (for long-term automation, but less secure)

---

## How the Setup Script Uses It

When you run `setup-github-auth.sh` on a VM:

```bash
# 1. Fetch token from Secret Manager
GITHUB_TOKEN=$(gcloud secrets versions access latest \
    --secret="github-automation-token" \
    --project="test-project")

# 2. Configure gh CLI
echo "$GITHUB_TOKEN" | gh auth login --with-token

# 3. Configure git to use gh
gh auth setup-git

# 4. Now git push works!
git push  # Uses gh CLI → uses token → authenticated to GitHub
```

---

## Security Best Practices

### ✅ DO

- Store token in GCP Secret Manager
- Use fine-grained tokens (not classic)
- Set expiration dates
- Grant minimal permissions (only what's needed)
- Use service accounts, not your personal credentials
- Enable Secret Manager audit logging

### ❌ DON'T

- Commit tokens to git repositories
- Store in plaintext files
- Use classic PATs (broader access)
- Share tokens between projects
- Log tokens in scripts or output

---

## Troubleshooting

### "Permission denied" when accessing secret

**Cause**: Service account doesn't have permission

**Fix**:

```bash
# List who has access
gcloud secrets get-iam-policy github-automation-token

# Add your service account
gcloud secrets add-iam-policy-binding github-automation-token \
  --member="serviceAccount:YOUR-SA@PROJECT.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### "Secret not found"

**Cause**: Wrong project or secret name

**Fix**:

```bash
# List all secrets in your project
gcloud secrets list --project=test-project

# Make sure you're using the right project
gcloud config set project test-project
```

### "gh: command not found" on VM

**Cause**: gh CLI not installed

**Fix**: Run `setup-github-auth.sh` - it installs gh CLI automatically

### Token expired

**Cause**: Token reached expiration date

**Fix**: Generate new token, update secret:

```bash
echo -n "ghp_newTokenHere" | \
  gcloud secrets versions add github-automation-token --data-file=-
```

---

## One-Time Setup Checklist

- [x] Create fine-grained PAT in GitHub
- [x] Copy token (starts with `ghp_`)
- [ ] Store in Secret Manager: `gcloud secrets create github-automation-token`
- [ ] Grant VM service account access: `gcloud secrets add-iam-policy-binding`
- [ ] Test access: `gcloud secrets versions access latest`
- [ ] Run `setup-github-auth.sh` on VM
- [ ] Verify: `gh auth status`

---

## Related Files

- `setup-github-auth.sh` - Fetches token and configures gh/git
- `VM-SETUP.md` - Complete fresh VM setup guide
- `QUICK-START.md` - Quick reference for local and VM usage
