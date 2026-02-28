# Dual Environment Setup: GitHub Actions + GCP VMs

Your GitHub PAT is now configured for **both** GitHub Actions workflows and GCP VMs.

---

## ✅ Setup Complete

### 1. GCP Secret Manager (for VMs)

```
Secret: github-automation-token
Project: test-project
Value: github_pat_11AJ7M73I... (70 chars)
Access: VM service account (1060025368044-compute@)
```

**Test it:**

```bash
gcloud secrets versions access latest \
  --secret=github-automation-token \
  --project=test-project
```

### 2. GitHub Repository Secrets (for Actions)

```
Secret: AUTOMATION_GITHUB_TOKEN
Added to: 4 repos (with Actions enabled)
  ✅ market-data-processing-service
  ✅ instruments-service
  ✅ ml-training-service
  ✅ unified-trading-codex

Skipped: 10 repos (Actions not enabled)
```

**View secrets:**

```bash
gh secret list --repo IggyIkenna/market-data-processing-service
```

---

## Usage in GitHub Actions

Create `.github/workflows/automation.yml`:

```yaml
name: Automated Fixes

on:
  workflow_dispatch:
    inputs:
      issue_number:
        description: "Issue number to fix"
        required: true

jobs:
  fix-issue:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
      issues: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -e ".[dev]"

      - name: Authenticate gh CLI
        env:
          GH_TOKEN: ${{ secrets.AUTOMATION_GITHUB_TOKEN }}
        run: |
          echo "$GH_TOKEN" | gh auth login --with-token
          gh auth setup-git

      - name: Fix issue
        env:
          GH_TOKEN: ${{ secrets.AUTOMATION_GITHUB_TOKEN }}
        run: |
          # Your automation script here
          bash scripts/fix-issue.sh ${{ inputs.issue_number }}

      - name: Create PR
        env:
          GH_TOKEN: ${{ secrets.AUTOMATION_GITHUB_TOKEN }}
        run: |
          gh pr create --title "Fixes #${{ inputs.issue_number }}" \
            --body "Automated fix" --base main
```

**Trigger manually:**

```bash
gh workflow run automation.yml \
  --repo IggyIkenna/market-data-processing-service \
  --field issue_number=46
```

---

## Usage on GCP VMs

### One-Time VM Setup

```bash
# 1. Create workspace
mkdir -p ~/unified-trading-repos && cd ~/unified-trading-repos

# 2. Clone repos
git clone https://github.com/IggyIkenna/unified-trading-codex.git
git clone https://github.com/IggyIkenna/unified-trading-services.git

# 3. Run setup (fetches secret, installs tools)
cd unified-trading-codex/11-project-management/github-integration/scripts/automation
bash setup-github-auth.sh

# 4. Clone service repos
cd ~/unified-trading-repos
for service in market-data-processing-service instruments-service \
               ml-training-service unified-trading-codex; do
    gh repo clone IggyIkenna/$service
done
```

### Run Automation

```bash
cd ~/unified-trading-repos/unified-trading-codex/11-project-management/github-integration/scripts/automation
bash run-cleanup-batch-fix.sh --model sonnet-4 --issues "46 47 48"
```

---

## Decision Matrix: When to Use Which?

| Scenario                     | Use GitHub Actions       | Use GCP VM               |
| ---------------------------- | ------------------------ | ------------------------ |
| Triggered by PR/commit       | ✅ Yes                   | ❌ No                    |
| Scheduled automation         | ✅ Yes (cron)            | ✅ Yes (Cloud Scheduler) |
| Long-running (>6 hours)      | ❌ No (timeout)          | ✅ Yes                   |
| Needs Cursor Agent           | ❌ No (not available)    | ✅ Yes                   |
| High compute (GPU, 64GB RAM) | ❌ Limited               | ✅ Yes                   |
| Many parallel issues (>10)   | ❌ Limited concurrency   | ✅ Yes                   |
| Simple linting/testing       | ✅ Yes                   | ⚪ Either                |
| Cost optimization            | ✅ Free (2000 min/month) | ⚪ Pay per use           |

---

## Architecture Comparison

### GitHub Actions Flow

```
PR Opened → GitHub Actions Runner
  ├─ Checkout code
  ├─ Install dependencies
  ├─ Run tests
  ├─ Use AUTOMATION_GITHUB_TOKEN for gh CLI
  └─ Push results / comment on PR
```

**Pros:**

- Zero setup (runs on GitHub infra)
- Integrated with GitHub events
- Free tier generous (2000 minutes/month)

**Cons:**

- 6-hour timeout
- No Cursor Agent
- Limited concurrency
- Can't access GCP resources easily

### GCP VM Flow

```
Manual/Scheduled → GCP VM
  ├─ Fetch github-automation-token from Secret Manager
  ├─ Configure gh CLI + Cursor CLI
  ├─ Clone repos + create workspaces
  ├─ Run Cursor agents in parallel
  └─ Push results to GitHub
```

**Pros:**

- No timeout (run for days)
- Full control (custom images, GPUs)
- Cursor Agent available
- High parallelism (100+ workers)
- Access to GCP services

**Cons:**

- Manual setup required
- Pay for compute time
- Need to manage VM lifecycle

---

## Hybrid Approach (Recommended)

Use **both** for different tasks:

### GitHub Actions (Fast, Simple)

```yaml
# .github/workflows/quality-gates.yml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: bash scripts/quality-gates.sh
```

**Use for:**

- PR validation (quality gates)
- Automated tests on push
- Dependency updates (Dependabot)
- Documentation builds

### GCP VM (Slow, Complex)

```bash
# Run batch fixes for 23 issues across 14 services
bash run-cleanup-batch-fix.sh --model sonnet-4 --issues "46-68"
```

**Use for:**

- Batch issue fixes (Cursor Agent)
- Large-scale refactoring
- ML model training
- Data processing pipelines
- Long-running migrations

---

## Security Best Practices

### Token Rotation (Recommended)

Since your token was posted in plaintext, rotate it after testing:

```bash
# 1. Revoke old token
gh auth token | gh api user --jq .login  # Verify it's you
# Then: GitHub → Settings → PATs → Find token → Delete

# 2. Create new token (same permissions)
# GitHub → Settings → PATs → Fine-grained → Generate

# 3. Update GCP Secret Manager
echo -n "NEW_TOKEN_HERE" | \
  gcloud secrets versions add github-automation-token --data-file=-

# 4. Update GitHub repo secrets
# Edit and re-run: add-github-secret-to-all-repos.sh

# 5. Test both environments
gcloud secrets versions access latest --secret=github-automation-token
gh secret list --repo IggyIkenna/market-data-processing-service
```

### Secret Scope Comparison

| Secret             | Scope                  | Access Method      | Lifetime           |
| ------------------ | ---------------------- | ------------------ | ------------------ |
| GCP Secret Manager | Cross-project, all VMs | IAM policy         | Managed (versions) |
| GitHub Repo Secret | Single repo            | Repo collaborators | Until deleted      |
| GitHub Org Secret  | All repos in org       | Org members        | Until deleted      |

**Recommendation**: Keep GCP Secret Manager as source of truth. GitHub repo secrets are derived copies.

---

## Monitoring

### GitHub Actions

```bash
# View recent workflow runs
gh run list --repo IggyIkenna/market-data-processing-service

# View logs for a specific run
gh run view <run-id> --log
```

### GCP VMs

```bash
# View secret access logs
gcloud logging read "resource.type=secretmanager.googleapis.com/Secret" \
  --limit 50 --format json

# VM instance logs
gcloud compute instances get-serial-port-output <instance-name>
```

---

## Troubleshooting

### "Secret not found" in GitHub Actions

**Cause**: Secret not added to repo or workflow doesn't have access

**Fix**:

```bash
# Check secrets exist
gh secret list --repo IggyIkenna/YOUR-REPO

# Add if missing
echo "YOUR_TOKEN" | gh secret set AUTOMATION_GITHUB_TOKEN --repo IggyIkenna/YOUR-REPO
```

### "Permission denied" on GCP VM

**Cause**: VM service account lacks `secretAccessor` role

**Fix**:

```bash
gcloud secrets add-iam-policy-binding github-automation-token \
  --member="serviceAccount:VM-SA@PROJECT.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Token expired

**Cause**: PAT reached expiration date

**Fix**: Follow "Token Rotation" steps above

---

## Cost Comparison

| Environment                | Cost               | Free Tier                  | Best For                   |
| -------------------------- | ------------------ | -------------------------- | -------------------------- |
| **GitHub Actions**         | $0.008/min (Linux) | 2000 min/month             | Quick tests, PR validation |
| **GCP VM (e2-medium)**     | ~$0.04/hour        | $300 credit (new accounts) | Long-running, Cursor Agent |
| **GCP VM (n2-standard-8)** | ~$0.39/hour        | Same                       | Parallel batch processing  |

**Example costs:**

- GitHub Actions: 100 PRs/month × 5 min = 500 min = **FREE**
- GCP VM: 10 hours/month batch fixes = **$0.40-$4.00**

---

## Next Steps

1. ✅ **Done**: Secrets configured in both environments
2. **Test GitHub Actions**: Create a workflow in one repo
3. **Test GCP VM**: Run `setup-github-auth.sh` on a VM
4. **Rotate token**: After verifying everything works
5. **Enable Actions**: For the 10 repos that were skipped (if needed)

---

## Related Files

- `setup-github-auth.sh` - GCP VM setup (fetches secret, installs tools)
- `add-github-secret-to-all-repos.sh` - Add secret to GitHub repos (DELETE AFTER USE)
- `GITHUB-PAT-SETUP.md` - Detailed PAT creation guide
- `VM-SETUP.md` - Complete GCP VM setup
- `ARCHITECTURE.md` - System architecture diagrams
