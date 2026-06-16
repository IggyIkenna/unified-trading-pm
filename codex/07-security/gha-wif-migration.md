---
scope: [engineer, admin]
---

# GHA Credential Hygiene: WIF + GitHub App Migration

**Status**: Phase 6.C of `api_keys_wallets_accounts_readiness_2026_05_10.md` **Operator action required**: GCP WIF pool
provisioning + GitHub App creation (BLOCKED-OPERATOR) **Secret scanning**: `.gitleaks.toml` SSOT at
`unified-trading-pm/.gitleaks.toml`

---

## Problem

Two classes of long-lived credentials exist in GHA workflows across all repos:

| Class                        | Current secret       | Risk                                                                        | Replacement                   |
| ---------------------------- | -------------------- | --------------------------------------------------------------------------- | ----------------------------- |
| GCP service account JSON     | `secrets.GCP_SA_KEY` | Committed to `benchmarks.yml`; GCP SA key rotates on a schedule; long-lived | GCP WIF (OIDC)                |
| GitHub Personal Access Token | `secrets.GH_PAT`     | Long-lived; account-level scope; leaked in `instruments-service` history    | GitHub App installation token |

---

## 1. GCP Workload Identity Federation (GCP WIF) — replaces `GCP_SA_KEY`

### What it does

GitHub Actions requests an OIDC token from GitHub → presents to GCP → GCP mints a short-lived SA access token. No
long-lived SA key JSON stored anywhere.

### Operator: provision WIF pool + provider (one-time, GCP Console or gcloud)

```bash
PROJECT_ID="central-element-323112"
POOL_ID="github-actions-pool"
PROVIDER_ID="github-actions-provider"
ORG="IggyIkenna"

# Create Workload Identity Pool
gcloud iam workload-identity-pools create "$POOL_ID" \
  --project="$PROJECT_ID" \
  --location="global" \
  --display-name="GitHub Actions WIF Pool"

# Create OIDC Provider for GitHub
gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_ID" \
  --project="$PROJECT_ID" \
  --location="global" \
  --workload-identity-pool="$POOL_ID" \
  --display-name="GitHub Actions OIDC" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Bind each repo's SA to the pool (repeat for every service SA)
# Format: REPO_SA = the GCP SA that the repo's workflows impersonate
REPO_SA="execution-service-sa@${PROJECT_ID}.iam.gserviceaccount.com"
gcloud iam service-accounts add-iam-policy-binding "$REPO_SA" \
  --project="$PROJECT_ID" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')/locations/global/workloadIdentityPools/${POOL_ID}/attribute.repository/${ORG}/execution-service"

# Get the WIF provider resource name (paste into GitHub secrets)
gcloud iam workload-identity-pools providers describe "$PROVIDER_ID" \
  --project="$PROJECT_ID" \
  --location="global" \
  --workload-identity-pool="$POOL_ID" \
  --format="value(name)"
# Output format: projects/123456789/locations/global/workloadIdentityPools/github-actions-pool/providers/github-actions-provider
```

### Operator: add GitHub repository secrets (per-repo)

After provisioning, add these secrets to each repo in GitHub:

- `WORKLOAD_IDENTITY_PROVIDER` = the provider resource name from above
- `GCP_SERVICE_ACCOUNT` = the SA email (`execution-service-sa@central-element-323112.iam.gserviceaccount.com`)

Keep `GCP_SA_KEY` secret in place until all workflows migrated and verified.

### Workflow pattern — dual-path (WIF preferred, SA key fallback)

```yaml
permissions:
  contents: read
  id-token: write # Required for WIF OIDC token request

jobs:
  build:
    steps:
      # WIF path (preferred — no long-lived key)
      - name: Authenticate to GCP via WIF
        if: ${{ secrets.WORKLOAD_IDENTITY_PROVIDER != '' }}
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}

      # Legacy fallback — remove once WIF pool provisioned and verified
      - name: Authenticate to GCP via SA key (legacy)
        if: ${{ secrets.WORKLOAD_IDENTITY_PROVIDER == '' && secrets.GCP_SA_KEY != '' }}
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
```

### Affected workflows (audit 2026-05-15)

| Repo              | Workflow            | Uses `GCP_SA_KEY`        | Migration status                            |
| ----------------- | ------------------- | ------------------------ | ------------------------------------------- |
| execution-service | `benchmarks.yml`    | Yes                      | BLOCKED-OPERATOR (WIF pool not provisioned) |
| All repos         | `quality-gates.yml` | Indirect (via VM launch) | Inherits from deployment-service            |

---

## 2. GitHub App Token — replaces `GH_PAT` for cross-repo GitHub API calls

### Why not WIF

WIF is GCP→GitHub auth. For GitHub→GitHub (cross-repo API calls, issue creation, PR management), the right replacement
is a **GitHub App installation token** — scoped per-repo, auto-rotating (1h TTL).

### Operator: create GitHub App

1. Go to `https://github.com/organizations/IggyIkenna/settings/apps/new`
2. Name: `unified-trading-semver-agent`
3. Homepage URL: `https://github.com/IggyIkenna`
4. Permissions:
   - Repository → Contents: Read and write
   - Repository → Issues: Read and write
   - Repository → Pull requests: Read and write
   - Repository → Workflows: Read and write (needed for cross-repo workflow dispatch)
5. Subscribe to events: none needed
6. Installation: Only on specific repositories (select all service repos)
7. After creation: note the **App ID** and generate a **Private key** (`.pem`)
8. Install the App on all service repos

### Operator: add GitHub repository secrets (workspace-wide)

In each repo settings, add:

- `APP_ID` = the App ID from step 7
- `APP_PRIVATE_KEY` = contents of the `.pem` file from step 7

### Workflow pattern — GitHub App token generation

```yaml
jobs:
  semver:
    steps:
      # Generate short-lived installation token
      - name: Generate GitHub App token
        id: app-token
        uses: actions/create-github-app-token@v1
        with:
          app-id: ${{ secrets.APP_ID }}
          private-key: ${{ secrets.APP_PRIVATE_KEY }}
          # For cross-repo access, specify the owner:
          owner: IggyIkenna

      # Use the token anywhere GH_PAT was used
      - name: Checkout (with App token)
        uses: actions/checkout@v4
        with:
          token: ${{ steps.app-token.outputs.token }}

      - name: Cross-repo API call
        env:
          GH_TOKEN: ${{ steps.app-token.outputs.token }}
        run: |
          gh api repos/IggyIkenna/unified-trading-library/issues \
            -H "Authorization: Bearer $GH_TOKEN"
```

### Affected workflows (audit 2026-05-15)

| Repo                | Workflow                       | Uses `GH_PAT` / `GH_TOKEN`    | Migration status                   |
| ------------------- | ------------------------------ | ----------------------------- | ---------------------------------- |
| execution-service   | `semver-agent.yml`             | Yes (cross-repo dispatch)     | BLOCKED-OPERATOR (App not created) |
| execution-service   | `major-bump-issue-handler.yml` | Yes (issue creation)          | BLOCKED-OPERATOR                   |
| execution-service   | `request-major-bump.yml`       | Yes (checkout + API)          | BLOCKED-OPERATOR                   |
| execution-service   | `staging-lock-check.yml`       | Yes (API call)                | BLOCKED-OPERATOR                   |
| execution-service   | `benchmarks.yml`               | Yes (git clone private repos) | BLOCKED-OPERATOR                   |
| All repos           | `semver-agent.yml` (copy)      | Yes                           | BLOCKED-OPERATOR                   |
| instruments-service | `.env` + `.env.example`        | Leaked in history             | P1 — revoke + history rewrite      |

---

## 3. Gitleaks pre-commit hook — prevents future leaks

Config SSOT: `unified-trading-pm/.gitleaks.toml` Pre-commit template SSOT:
`unified-trading-pm/scripts/pre-commit-templates/`

All templates (python-service, python-library, docs) now include:

```yaml
- repo: https://github.com/gitleaks/gitleaks
  rev: v8.27.2
  hooks:
    - id: gitleaks
      args: ["--config", "${WORKSPACE_ROOT:-..}/unified-trading-pm/.gitleaks.toml"]
```

**To propagate to all repos** (after template update):

```bash
bash unified-trading-pm/scripts/propagation/rollout-pre-commit-configs.sh
```

The hook scans files staged for commit (not full git history). For CI-level scanning, see Phase 0.A gitleaks GHA
workflow (to be added per Phase 6.C completion).

---

## 4. Gitleaks CI workflow — periodic history + file scan

Add to all repos as `gitleaks-scan.yml`:

```yaml
name: Gitleaks Secret Scan
on:
  push:
    branches: [main, live-defi-rollout, staging]
  schedule:
    - cron: "0 2 * * 1" # Weekly Monday 02:00 UTC

jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0 # Full history for git-mode scan

      - name: Run gitleaks (git mode — full history)
        uses: gitleaks/gitleaks-action@v2
        with:
          config: unified-trading-pm/.gitleaks.toml
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }} # Optional for team use
```

---

## Operator Action Checklist

| Action                                                           | Priority | ETA    | Status |
| ---------------------------------------------------------------- | -------- | ------ | ------ |
| Revoke GCP SA key `e35fb0ddafe2`                                 | P0       | ≤1h    | `[ ]`  |
| Run `git filter-repo` on 4 repos                                 | P0       | ≤4h    | `[ ]`  |
| Revoke GitHub PAT `ghp_QJOtg6N...`                               | P1       | ≤15min | `[ ]`  |
| Provision GCP WIF pool + provider                                | P1       | ≤2h    | `[ ]`  |
| Add `WORKLOAD_IDENTITY_PROVIDER` + `GCP_SERVICE_ACCOUNT` secrets | P1       | ≤30min | `[ ]`  |
| Create GitHub App `unified-trading-semver-agent`                 | P2       | ≤1h    | `[ ]`  |
| Add `APP_ID` + `APP_PRIVATE_KEY` secrets to all repos            | P2       | ≤30min | `[ ]`  |
| Run `rollout-pre-commit-configs.sh` after template update        | P2       | ≤10min | `[ ]`  |

---

## Related Documents

- P0 issue: `plans/active/issues/gcp_sa_private_key_in_git_history_execution_service_2026_05_15.md`
- P1 issue: `plans/active/issues/github_pat_in_instruments_service_env_2026_05_15.md`
- Rotation runbook: `codex/14-customer-journeys/credentials/rotation-runbook.md`
- Credentials matrix: `codex/05-infrastructure/credentials-matrix.md`
- AWS IAM matrix: `codex/05-infrastructure/aws-iam-matrix.md`
