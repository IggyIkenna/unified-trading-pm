# Secret Rotation Plan

## Secret Inventory

| Secret Name                   | Type                         | Scope                                                     | Rotation Schedule | Last Rotated | Owner |
| ----------------------------- | ---------------------------- | --------------------------------------------------------- | ----------------- | ------------ | ----- |
| `GH_PAT`                      | GitHub Personal Access Token | All repos (cross-repo dispatch, PR creation)              | 90 days           | TBD          | Admin |
| `GCP_SA_KEY`                  | GCP Service Account Key      | Deployment workflows                                      | 90 days           | TBD          | Admin |
| `ANTHROPIC_API_KEY_SYSHEALTH` | Anthropic API Key            | Agent workflows (overnight orchestrator, audit)           | 90 days           | TBD          | Admin |
| `TELEGRAM_BOT_TOKEN`          | Telegram Bot API Token       | Alert notifications                                       | 180 days          | TBD          | Admin |
| `TELEGRAM_CHAT_ID`            | Telegram Chat ID             | Alert notifications (stored as repo variable, not secret) | N/A (stable)      | N/A          | Admin |

## Rotation Procedures

### GH_PAT (GitHub Personal Access Token)

1. Go to GitHub Settings > Developer Settings > Personal Access Tokens > Fine-grained tokens
2. Create new token with scopes: `repo`, `workflow`, `admin:org` (read)
3. Update the secret in all repos that reference it:
   ```bash
   # List all repos in manifest
   REPOS=$(python3 -c "import json; m=json.load(open('workspace-manifest.json')); print('\n'.join(m['repositories'].keys()))")
   # Update each repo
   for repo in $REPOS; do
     gh secret set GH_PAT --repo "IggyIkenna/$repo" --body "$NEW_TOKEN"
   done
   # Also update PM itself
   gh secret set GH_PAT --repo "IggyIkenna/unified-trading-pm" --body "$NEW_TOKEN"
   ```
4. Verify: `gh api user` should return your user info
5. Revoke the old token

### GCP_SA_KEY (Service Account Key)

1. Create new key: `gcloud iam service-accounts keys create key.json --iam-account=<SA_EMAIL>`
2. Base64 encode: `base64 -i key.json | tr -d '\n'`
3. Update in relevant repos: `gh secret set GCP_SA_KEY --repo "IggyIkenna/<repo>" --body "$(cat key.json | base64)"`
4. Verify a deployment workflow runs successfully
5. Delete old key: `gcloud iam service-accounts keys delete <OLD_KEY_ID> --iam-account=<SA_EMAIL>`
6. Securely delete local key file: `rm -f key.json`

### ANTHROPIC_API_KEY_SYSHEALTH

1. Generate new API key from Anthropic Console
2. Update: `gh secret set ANTHROPIC_API_KEY_SYSHEALTH --repo "IggyIkenna/unified-trading-pm" --body "$NEW_KEY"`
3. Verify: trigger a manual overnight orchestrator run and confirm agent steps work
4. Revoke old key in Anthropic Console

### TELEGRAM_BOT_TOKEN

1. Message @BotFather on Telegram: `/revoke` then `/token` to get a new token
2. Update: `gh secret set TELEGRAM_BOT_TOKEN --repo "IggyIkenna/unified-trading-pm" --body "$NEW_TOKEN"`
3. Verify: trigger dead-man-switch workflow manually; confirm Telegram message received
4. Old token is automatically revoked by BotFather

## Health Check

The `secret-health-check.yml` workflow runs weekly and validates that critical secrets are still functional. It checks:

- GH_PAT validity via `gh api user`
- Reports status to workflow logs (does not expose secret values)
