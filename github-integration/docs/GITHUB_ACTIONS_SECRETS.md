# GitHub Actions with Secrets - Authentication Strategy

**Scenario:** Run automation scripts (create projects, label CODs, etc.) via GitHub Actions without exposing tokens to
users

**Options:**

1. **GitHub Secrets** (Recommended - simpler)
2. **GCP Secret Manager** (More complex, but centralized secret management)

---

## Option 1: GitHub Secrets (Recommended)

### Why This is Better for GitHub Actions

- ✅ **Built-in:** No external dependencies (GCP)
- ✅ **Secure:** Never exposed in logs or to users
- ✅ **Simple:** No GCP authentication needed
- ✅ **Fast:** No API calls to fetch secrets
- ✅ **Free:** No GCP Secret Manager costs

### Setup

#### Step 1: Add Token to GitHub Secrets

1. Go to your repo: https://github.com/IggyIkenna/your-repo/settings/secrets/actions
2. Click **"New repository secret"**
3. Name: `PROJECT_MANAGEMENT_TOKEN`
4. Value: Your GitHub token (`ghp_...`)
5. Click **"Add secret"**

**For organization-wide access:**

- Go to: https://github.com/organizations/IggyIkenna/settings/secrets/actions
- Add as organization secret
- Select which repos can access it

#### Step 2: Use in GitHub Actions Workflow

```yaml
# .github/workflows/create-projects.yml
name: Create GitHub Projects

on:
  workflow_dispatch: # Manual trigger
    inputs:
      dry_run:
        description: "Run in dry-run mode"
        required: false
        default: "true"

jobs:
  create-projects:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install dependencies
        run: |
          pip install requests

      - name: Install GitHub CLI
        run: |
          sudo apt-get update
          sudo apt-get install -y gh

      - name: Create GitHub Projects
        env:
          GITHUB_TOKEN: ${{ secrets.PROJECT_MANAGEMENT_TOKEN }}
        run: |
          cd unified-trading-codex/11-project-management/github-integration

          if [ "${{ github.event.inputs.dry_run }}" = "true" ]; then
            python create-all-projects.py --org IggyIkenna --dry-run
          else
            python create-all-projects.py --org IggyIkenna --apply
          fi
```

#### Step 3: Trigger Workflow

**Via GitHub UI:**

1. Go to: https://github.com/IggyIkenna/your-repo/actions
2. Select "Create GitHub Projects" workflow
3. Click "Run workflow"
4. Choose dry-run: true/false
5. Click "Run workflow"

**Via GitHub CLI:**

```bash
# Dry run
gh workflow run create-projects.yml -f dry_run=true

# Apply changes
gh workflow run create-projects.yml -f dry_run=false
```

### Advantages

- ✅ No GCP setup needed
- ✅ No authentication complexity
- ✅ Other users can trigger workflow without seeing token
- ✅ Works immediately
- ✅ Free

### Limitations

- ❌ Token only available in GitHub (can't use for local scripts without copying)
- ❌ Need to update in GitHub if token rotates

---

## Option 2: GCP Secret Manager (Centralized Secrets)

### Why Use This

- ✅ Centralized secret management (one place for all secrets)
- ✅ Can be used by both GitHub Actions AND local scripts
- ✅ Better audit trail (GCP logs all secret access)
- ✅ Automatic rotation support
- ✅ Fine-grained access control (IAM)

### Setup

#### Step 1: Store Token in GCP Secret Manager

```bash
# Create secret in GCP Secret Manager
gcloud secrets create github-project-token \
  --data-file=- <<< "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Verify
gcloud secrets versions access latest --secret=github-project-token
```

#### Step 2: Create Service Account for GitHub Actions

```bash
# Create service account
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions" \
  --description="Service account for GitHub Actions to access secrets"

# Grant access to Secret Manager
gcloud secrets add-iam-policy-binding github-project-token \
  --member="serviceAccount:github-actions@YOUR-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

#### Step 3: Set Up Workload Identity Federation (Recommended)

**Why:** No service account keys to manage (keys can leak, expire, etc.)

```bash
# Create Workload Identity Pool
gcloud iam workload-identity-pools create "github-actions-pool" \
  --project="YOUR-PROJECT-ID" \
  --location="global" \
  --display-name="GitHub Actions Pool"

# Create Workload Identity Provider
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project="YOUR-PROJECT-ID" \
  --location="global" \
  --workload-identity-pool="github-actions-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Grant service account access to GitHub repo
gcloud iam service-accounts add-iam-policy-binding \
  "github-actions@YOUR-PROJECT-ID.iam.gserviceaccount.com" \
  --project="YOUR-PROJECT-ID" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/PROJECT-NUMBER/locations/global/workloadIdentityPools/github-actions-pool/attribute.repository/IggyIkenna/REPO-NAME"
```

#### Step 4: Get Workload Identity Provider Name

```bash
gcloud iam workload-identity-pools providers describe "github-provider" \
  --project="YOUR-PROJECT-ID" \
  --location="global" \
  --workload-identity-pool="github-actions-pool" \
  --format="value(name)"

# Output: projects/PROJECT-NUMBER/locations/global/workloadIdentityPools/github-actions-pool/providers/github-provider
```

#### Step 5: Add Workload Identity Provider to GitHub Secrets

1. Go to: https://github.com/IggyIkenna/your-repo/settings/secrets/actions
2. Add secret:
   - Name: `GCP_WORKLOAD_IDENTITY_PROVIDER`
   - Value:
     `projects/PROJECT-NUMBER/locations/global/workloadIdentityPools/github-actions-pool/providers/github-provider`
3. Add another secret:
   - Name: `GCP_SERVICE_ACCOUNT`
   - Value: `github-actions@YOUR-PROJECT-ID.iam.gserviceaccount.com`

#### Step 6: GitHub Actions Workflow with GCP Secret Manager

```yaml
# .github/workflows/create-projects-gcp-secrets.yml
name: Create GitHub Projects (GCP Secrets)

on:
  workflow_dispatch:
    inputs:
      dry_run:
        description: "Run in dry-run mode"
        required: false
        default: "true"

jobs:
  create-projects:
    runs-on: ubuntu-latest

    permissions:
      contents: read
      id-token: write # Required for Workload Identity Federation

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}

      - name: Setup Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Fetch GitHub Token from Secret Manager
        id: secrets
        run: |
          GITHUB_TOKEN=$(gcloud secrets versions access latest --secret=github-project-token)
          echo "::add-mask::$GITHUB_TOKEN"
          echo "GITHUB_TOKEN=$GITHUB_TOKEN" >> $GITHUB_ENV

      - name: Install dependencies
        run: |
          pip install requests
          sudo apt-get update
          sudo apt-get install -y gh

      - name: Create GitHub Projects
        env:
          GITHUB_TOKEN: ${{ env.GITHUB_TOKEN }}
        run: |
          cd unified-trading-codex/11-project-management/github-integration

          if [ "${{ github.event.inputs.dry_run }}" = "true" ]; then
            python create-all-projects.py --org IggyIkenna --dry-run
          else
            python create-all-projects.py --org IggyIkenna --apply
          fi
```

### Advantages

- ✅ Centralized secret management
- ✅ No service account keys (Workload Identity is keyless)
- ✅ Can be used by local scripts too (just `gcloud secrets versions access latest --secret=github-project-token`)
- ✅ Better audit trail
- ✅ Automatic rotation support
- ✅ Other users can run scripts locally without seeing token (if they have GCP access)

### Limitations

- ❌ More complex setup
- ❌ Requires GCP project
- ❌ Small cost (Secret Manager: $0.06 per 10K access operations)
- ❌ Slower (API call to fetch secret)

---

## Option 3: Hybrid Approach (Best of Both Worlds)

### Scenario

- **GitHub Actions:** Use GCP Secret Manager (centralized, audited)
- **Local Development:** Use GCP Secret Manager OR local `.env` (developer choice)
- **Other Users:** Can run via GitHub Actions (no token access) OR via GCP (if they have permission)

### Setup

1. **Store token in GCP Secret Manager** (as in Option 2)
2. **GitHub Actions uses GCP Secret Manager** (as in Option 2)
3. **Local developers have two options:**

**Option A: Via GCP Secret Manager (if they have access)**

```bash
# Fetch token from GCP and export
export GITHUB_TOKEN=$(gcloud secrets versions access latest --secret=github-project-token)

# Run script
python create-all-projects.py --org IggyIkenna --apply
```

**Option B: Via local .env file (their own token)**

```bash
# Create .env with their own personal token
echo "GITHUB_TOKEN=ghp_their_personal_token" > .env

# Script loads from .env
python create-all-projects.py --org IggyIkenna --apply
```

---

## Comparison Table

| Feature                   | GitHub Secrets | GCP Secret Manager | Hybrid            |
| ------------------------- | -------------- | ------------------ | ----------------- |
| **Setup Complexity**      | Low            | High               | High              |
| **Cost**                  | Free           | ~$0.06/10K access  | ~$0.06/10K access |
| **Access Control**        | GitHub only    | GCP IAM            | Both              |
| **Audit Trail**           | GitHub logs    | GCP logs           | Both              |
| **Local Script Access**   | No (must copy) | Yes (via gcloud)   | Yes               |
| **GitHub Actions Access** | Yes (native)   | Yes (via API)      | Yes               |
| **Token Rotation**        | Manual update  | Automatic support  | Automatic support |
| **Multi-cloud**           | No             | Yes                | Yes               |
| **Recommended For**       | Simple setups  | Enterprise         | Enterprise        |

---

## Recommendation by Use Case

### Use Case 1: Only GitHub Actions Needs Token

**Recommendation:** GitHub Secrets (Option 1)

**Why:** Simplest, fastest, free, built-in

**Setup time:** 5 minutes

---

### Use Case 2: Both GitHub Actions AND Local Scripts Need Token

**Recommendation:** GCP Secret Manager (Option 2)

**Why:** Centralized, audited, no token duplication

**Setup time:** 30 minutes (Workload Identity setup)

---

### Use Case 3: Multiple Developers + GitHub Actions

**Recommendation:** Hybrid (Option 3)

**Why:**

- GitHub Actions uses centralized secret (audit trail)
- Developers can use centralized secret (if they have GCP access) OR their own tokens
- No need to share the main token with developers

**Setup time:** 30 minutes (GCP setup) + 5 minutes per developer

---

## For Your Specific Question

> "Can GitHub Actions authenticate to GCP, use that to pull the thing from Secret Manager?"

**Yes!** That's exactly what Workload Identity Federation does:

1. **GitHub Actions starts** → Generates an OIDC token (proves it's from your GitHub repo)
2. **Exchanges OIDC token** → Gets GCP access token (via Workload Identity Federation)
3. **Uses GCP access token** → Fetches secret from Secret Manager
4. **Uses GitHub token** → Runs your scripts

**No chicken-and-egg problem** because:

- GitHub Actions OIDC token is provided automatically by GitHub
- Workload Identity Federation trusts that OIDC token
- No keys needed!

---

## Quick Start: GitHub Secrets (5 minutes)

```bash
# 1. Add token to GitHub Secrets
# Go to: https://github.com/IggyIkenna/your-repo/settings/secrets/actions
# Name: PROJECT_MANAGEMENT_TOKEN
# Value: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 2. Create workflow file
cat > .github/workflows/create-projects.yml << 'EOF'
name: Create Projects

on:
  workflow_dispatch:
    inputs:
      dry_run:
        default: 'true'

jobs:
  create:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - run: pip install requests
      - run: sudo apt-get install -y gh
      - env:
          GITHUB_TOKEN: ${{ secrets.PROJECT_MANAGEMENT_TOKEN }}
        run: |
          cd unified-trading-codex/11-project-management/github-integration
          python create-all-projects.py --org IggyIkenna --dry-run
EOF

# 3. Commit and push
git add .github/workflows/create-projects.yml
git commit -m "Add GitHub Actions workflow for project creation"
git push

# 4. Trigger via GitHub UI
# Go to: Actions → Create Projects → Run workflow
```

---

## Quick Start: GCP Secret Manager (30 minutes)

```bash
# 1. Store token in GCP
echo "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" | gcloud secrets create github-project-token --data-file=-

# 2. Set up Workload Identity (see Step 3-5 above)

# 3. Add GCP secrets to GitHub (see Step 5 above)

# 4. Create workflow (see Step 6 above)

# 5. Done!
```

---

## Which Should You Use?

**For your use case (automation scripts + multiple users):**

I recommend **Hybrid Approach**:

1. **Store token in GCP Secret Manager** (centralized, audited)
2. **GitHub Actions uses GCP Secret Manager** (via Workload Identity Federation)
3. **Users trigger via GitHub Actions** (never see token)
4. **Advanced users can use GCP locally** (if they have permission)

**Benefits:**

- ✅ Users can trigger automation without seeing token
- ✅ Centralized secret management
- ✅ Full audit trail (who accessed when)
- ✅ Easy to rotate token (update in one place)
- ✅ Can be extended to other secrets (GCP credentials, API keys, etc.)

**Start with:** GitHub Secrets (simple, works today)
**Migrate to:** GCP Secret Manager (when you need centralized management)

---

**Status:** ✅ Ready to implement
**Recommended:** Start with GitHub Secrets (Option 1), migrate to GCP later if needed
**Last Updated:** 2026-02-13
