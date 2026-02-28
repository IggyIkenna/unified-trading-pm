# Running Batch Fix Automation on Fresh VMs

This guide covers setting up GitHub authentication for automated issue fixing on fresh GCP VMs or CI/CD environments.

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│ Fresh GCP VM                                     │
├─────────────────────────────────────────────────┤
│ 1. Fetch GitHub PAT from Secret Manager         │
│ 2. Configure gh CLI authentication               │
│ 3. Clone temporary workspaces                    │
│ 4. Run Cursor Agent to fix issues                │
│ 5. Push changes to GitHub (via gh/HTTPS)         │
│ 6. Create PR and enable auto-merge               │
└─────────────────────────────────────────────────┘
```

## One-Time Setup (Local Environment)

### 1. Create Fine-Grained Personal Access Token

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Click "Generate new token"
3. Configure:
   - **Name**: `github-automation-bot`
   - **Expiration**: 90 days (or no expiration for long-term automation)
   - **Repository access**: All repositories (or select specific repos)
   - **Permissions**:
     - Contents: Read and write
     - Pull requests: Read and write
     - Issues: Read and write
     - Workflows: Read (if needed for triggering CI)

4. Generate token → Copy it (starts with `ghp_`)

### 2. Store Token in GCP Secret Manager

```bash
# Store the token
echo -n "ghp_yourActualTokenHere" | gcloud secrets create github-automation-token \
    --project=test-project \
    --data-file=-

# Verify it was stored
gcloud secrets versions access latest \
    --secret=github-automation-token \
    --project=test-project
```

### 3. Grant VM Service Account Access to Secret

```bash
# Get your Compute Engine default service account
PROJECT_NUMBER=$(gcloud projects describe test-project --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Grant access
gcloud secrets add-iam-policy-binding github-automation-token \
    --project=test-project \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"
```

## Fresh VM Setup

When spinning up a new VM for automation:

```bash
# 1. Create workspace directory
mkdir -p ~/unified-trading-repos
cd ~/unified-trading-repos

# 2. Clone required repos (public repos, no auth needed yet)
git clone https://github.com/IggyIkenna/unified-trading-codex.git
git clone https://github.com/IggyIkenna/unified-trading-services.git

# 3. Run authentication setup (installs Cursor CLI, gh CLI, configures auth)
cd unified-trading-codex/11-project-management/github-integration/scripts/automation
bash setup-github-auth.sh

# 4. Clone all service repos (now that gh is authenticated)
cd ~/unified-trading-repos
for service in market-data-processing-service instruments-service order-book-service \
               ml-training-service portfolio-reporting-service portfolio-management-service \
               orchestration-service notifications-service position-aggregation-service \
               risk-management-service strategy-execution-service signal-generation-service \
               trade-execution-service; do
    gh repo clone IggyIkenna/$service
done

# 5. Run batch fix automation
cd unified-trading-codex/11-project-management/github-integration/scripts/automation
bash run-cleanup-batch-fix.sh
```

This script will:

- Fetch the GitHub token from Secret Manager
- Install gh CLI (if not present)
- Configure gh authentication
- Set up git credential helper
- Test the authentication

## Alternative: SSH Keys (Less Recommended)

If you prefer SSH keys over HTTPS tokens:

### Generate SSH Key on VM

```bash
ssh-keygen -t ed25519 -C "automation@yourdomain.com" -f ~/.ssh/github_automation -N ""
```

### Add Public Key to GitHub

```bash
# Print public key
cat ~/.ssh/github_automation.pub

# Add to GitHub → Settings → SSH and GPG keys → New SSH key
```

### Configure SSH Agent

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/github_automation

# Test
ssh -T git@github.com
```

### Configure Git

```bash
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

**Note**: SSH keys require more manual management and don't expire, making them less ideal for automation. PATs with gh
CLI are recommended.

## Security Best Practices

### 1. Token Scope (Least Privilege)

- Use fine-grained tokens instead of classic PATs
- Grant only required permissions (Contents, PRs, Issues)
- Limit to specific repositories if possible

### 2. Token Expiration

- Set expiration for contractor/temporary access (90 days)
- For long-term automation, monitor and rotate periodically
- Store rotation date in Secret Manager description

### 3. Secret Storage

- **Never** commit tokens to repositories
- **Never** store in shell history or log files
- Use GCP Secret Manager for centralized secrets
- Enable Secret Manager audit logging

### 4. Access Control

- Grant IAM permissions only to service accounts that need them
- Use separate service accounts for different automation tasks
- Review secret access logs periodically

### 5. Monitoring

- Enable Secret Manager audit logs
- Alert on unusual access patterns
- Track failed authentication attempts via gh CLI

## Troubleshooting

### "Failed to fetch secret from GCP Secret Manager"

**Cause**: VM service account doesn't have permission

**Fix**:

```bash
gcloud secrets add-iam-policy-binding github-automation-token \
    --member="serviceAccount:YOUR-SA@PROJECT.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### "gh CLI authentication test failed"

**Cause**: Token expired or has insufficient permissions

**Fix**:

1. Generate new token with correct permissions
2. Update secret:
   ```bash
   echo -n "ghp_newToken" | gcloud secrets versions add github-automation-token --data-file=-
   ```

### "remote: Repository not found"

**Cause**: Token doesn't have access to repository

**Fix**: Re-generate token with "All repositories" access or add specific repo

### SSH vs HTTPS Authentication Confusion

The `batch-fix-v2.sh` script now auto-detects:

1. If gh CLI is authenticated → uses HTTPS
2. If SSH keys exist → uses SSH
3. Otherwise → warns about missing auth

## Local Development (macOS)

For your local environment, you're already set up! The script detects:

- Existing gh CLI authentication (`gh auth status`)
- Existing SSH keys (~/.ssh/id_rsa or ~/.ssh/id_ed25519)

No additional setup needed - just run `bash run-cleanup-batch-fix.sh` as normal.

## CI/CD Integration (Future)

For GitHub Actions or Cloud Build:

### GitHub Actions

```yaml
- name: Authenticate GitHub
  run: |
    echo "${{ secrets.GITHUB_TOKEN }}" | gh auth login --with-token
    gh auth setup-git
```

### Cloud Build

```yaml
steps:
  - name: "gcr.io/cloud-builders/gcloud"
    entrypoint: "bash"
    args:
      - "-c"
      - |
        # Fetch token and configure gh
        TOKEN=$(gcloud secrets versions access latest --secret=github-automation-token)
        echo "$$TOKEN" | gh auth login --with-token
        gh auth setup-git
```

## Related Documentation

- [GitHub PAT Documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [GCP Secret Manager](https://cloud.google.com/secret-manager/docs)
- [gh CLI Authentication](https://cli.github.com/manual/gh_auth_login)
- [Git Credential Helpers](https://git-scm.com/doc/credential-helpers)
