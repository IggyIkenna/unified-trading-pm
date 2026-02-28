# Integrating GCP GitHub Auth Test into Quality Gates

## Quick Start

Run the standalone test:

```bash
# Full test (fetches secret + authenticates)
bash test-gcp-github-auth.sh

# Check only (don't re-authenticate)
bash test-gcp-github-auth.sh --check-only

# Quick mode (just verify secret exists)
bash test-gcp-github-auth.sh --quick
```

---

## What It Tests

1. ✅ **gcloud CLI** installed and configured
2. ✅ **gh CLI** installed
3. ✅ **GCP Secret Manager** accessible
4. ✅ **github-automation-token** secret exists and can be fetched
5. ✅ **gh authentication** works with the token
6. ✅ **GitHub API** accessible

---

## Exit Codes

| Code | Meaning                              |
| ---- | ------------------------------------ |
| 0    | All tests passed                     |
| 1    | GCP Secret Manager not accessible    |
| 2    | Secret not found or can't be fetched |
| 3    | gh CLI authentication failed         |
| 4    | gh CLI not installed                 |

---

## Integration Option 1: Add to Quality Gates (Manual)

Add this to any service's `scripts/quality-gates.sh`:

```bash
# After the existing phases (Config, Linting, Tests, Codex)
# Add a new phase for GCP Auth verification

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}[5/5] GCP GitHub Auth Verification${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Path to auth test script (adjust based on repo structure)
AUTH_TEST_SCRIPT="${REPO_ROOT}/unified-trading-codex/11-project-management/github-integration/scripts/automation/test-gcp-github-auth.sh"

if [ -f "$AUTH_TEST_SCRIPT" ]; then
    if bash "$AUTH_TEST_SCRIPT" --check-only; then
        echo -e "${GREEN}✅ GCP GitHub Auth verified${NC}"
    else
        echo -e "${RED}❌ GCP GitHub Auth test failed${NC}"
        echo ""
        echo "This is non-critical for local development."
        echo "On VMs, ensure Secret Manager is properly configured."
        # Don't fail quality gates for this (optional check)
        # exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Auth test script not found (skipping)${NC}"
fi
```

---

## Integration Option 2: Conditional (Only on VMs)

Only run the auth test on VMs (skip on local dev):

```bash
# Only test GCP auth on VMs (not local dev)
if [ -n "${CI:-}" ] || [ -n "${CLOUD_BUILD:-}" ] || [ -n "${VM_ENV:-}" ]; then
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}[5/5] GCP GitHub Auth Verification (VM Environment)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    AUTH_TEST_SCRIPT="${REPO_ROOT}/unified-trading-codex/11-project-management/github-integration/scripts/automation/test-gcp-github-auth.sh"

    if bash "$AUTH_TEST_SCRIPT" --quick; then
        echo -e "${GREEN}✅ GCP GitHub Auth configured${NC}"
    else
        echo -e "${RED}❌ GCP GitHub Auth not configured${NC}"
        echo "   Required for automation on VMs"
        exit 1
    fi
fi
```

---

## Integration Option 3: Pre-Flight Check (Before Batch Fix)

Add to the beginning of `batch-fix-v2.sh` or `run-cleanup-batch-fix.sh`:

```bash
# Pre-flight check: Verify GitHub authentication
echo "🔐 Pre-flight: Verifying GitHub authentication..."
AUTH_TEST_SCRIPT="$SCRIPT_DIR/test-gcp-github-auth.sh"

if [ -f "$AUTH_TEST_SCRIPT" ]; then
    if ! bash "$AUTH_TEST_SCRIPT" --check-only; then
        echo "❌ GitHub authentication test failed"
        echo "   Run: bash $AUTH_TEST_SCRIPT"
        exit 1
    fi
else
    echo "⚠️  Auth test script not found, skipping verification"
fi
echo ""
```

---

## Usage Examples

### Local Development (Manual Test)

```bash
cd unified-trading-codex/11-project-management/github-integration/scripts/automation

# Test everything
bash test-gcp-github-auth.sh

# Check only (don't modify current auth)
bash test-gcp-github-auth.sh --check-only
```

### VM Setup Script

Add to `setup-github-auth.sh`:

```bash
# After gh auth login, verify it works
if bash "$SCRIPT_DIR/test-gcp-github-auth.sh" --check-only; then
    echo "✅ GitHub authentication verified"
else
    echo "❌ GitHub authentication failed"
    exit 1
fi
```

### CI/CD Pipeline

Add to GitHub Actions workflow:

```yaml
- name: Verify GCP GitHub Auth
  run: |
    cd unified-trading-codex/11-project-management/github-integration/scripts/automation
    bash test-gcp-github-auth.sh --quick
```

---

## Environment Variables

Override defaults:

```bash
# Custom secret name
export GITHUB_TOKEN_SECRET="my-custom-secret"

# Custom GCP project
export GCP_PROJECT="my-project-id"

# Run test
bash test-gcp-github-auth.sh
```

---

## Troubleshooting

### "gcloud not authenticated"

```bash
gcloud auth login
gcloud config set project test-project
```

### "Permission denied" (Secret Manager)

```bash
# Grant service account access
gcloud secrets add-iam-policy-binding github-automation-token \
  --member="serviceAccount:YOUR-SA@PROJECT.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### "Secret not found"

```bash
# List secrets
gcloud secrets list --project=test-project

# Create if missing (see GITHUB-PAT-SETUP.md)
echo -n "YOUR_TOKEN" | gcloud secrets create github-automation-token --data-file=-
```

### "gh CLI not installed"

```bash
# macOS
brew install gh

# Linux
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
# ... (see setup-github-auth.sh for full Linux install)
```

---

## When to Use Each Mode

| Mode           | Use Case                | Speed          | Modifies Auth |
| -------------- | ----------------------- | -------------- | ------------- |
| `--quick`      | CI/CD health check      | Fastest (1-2s) | No            |
| `--check-only` | Pre-flight verification | Fast (2-3s)    | No            |
| (default)      | VM setup, debugging     | Full (3-5s)    | Yes           |

---

## Security Notes

- **Backup**: The script backs up your existing `~/.config/gh/hosts.yml` before re-authenticating
- **Token**: Never logs the full token (only prefix + length)
- **Audit**: All Secret Manager access is logged in Cloud Logging
- **Scope**: Only tests read access to the secret (doesn't modify it)

---

## Example Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔐 Testing GCP Secret Manager GitHub Authentication
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/5] Checking gcloud CLI...
✅ gcloud CLI configured
   Account: your-email@domain.com
   Project: test-project

[2/5] Checking gh CLI...
✅ gh CLI installed
   Version: gh version 2.86.0

[3/5] Fetching GitHub token from Secret Manager...
   Secret: github-automation-token
   Project: test-project
✅ Token fetched successfully
   Length: 93 characters
   Prefix: github_pat_11AJ7M73I...

[4/5] Checking current gh auth status...
✅ Already authenticated to GitHub
   User: IggyIkenna

ℹ️  Skipping re-authentication (--check-only)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ All checks passed (already authenticated)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Related Files

- `test-gcp-github-auth.sh` - Main authentication test script
- `setup-github-auth.sh` - Full VM setup (includes auth test)
- `GITHUB-PAT-SETUP.md` - How to create and store the token
- `VM-SETUP.md` - Complete VM setup guide
- `ARCHITECTURE.md` - System architecture
