#!/bin/bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Generate .act-secrets at workspace root for act (nektos/act) CI simulation.
#
# Run manually. Do NOT commit the generated file — it contains GH_PAT.
# Same relative path for everyone: <workspace-root>/.act-secrets
#
# Usage:
#   bash unified-trading-pm/scripts/workspace/generate-act-secrets.sh
#
# After running: edit .act-secrets and add your GitHub PAT (no quotes):
#   GH_PAT=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# Workspace root = parent of unified-trading-pm
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SECRETS_FILE="${WORKSPACE_ROOT}/.act-secrets"

# --refresh: re-pull GH_PAT from Secret Manager even if .act-secrets exists (P2 493 — keeps the
# cache fresh proactively so it rarely goes stale; complements load-gh-token.sh's runtime
# validity-probe). Safe to wire into workspace-bootstrap.sh / a cron.
REFRESH=false
[ "${1:-}" = "--refresh" ] && REFRESH=true

# Authoritative GH_PAT source = Secret Manager (same order as load-gh-token.sh: GCP SM -> AWS SM).
_sm_pat=""
if command -v gcloud >/dev/null 2>&1; then
  _sm_pat="$(gcloud secrets versions access latest --secret=GH_PAT 2>/dev/null | tr -d '\n' || true)"
fi
if [ -z "$_sm_pat" ] && command -v aws >/dev/null 2>&1; then
  _sm_pat="$(aws secretsmanager get-secret-value --secret-id GH_PAT --query SecretString --output text 2>/dev/null | tr -d '\n' || true)"
fi

if [ -f "$SECRETS_FILE" ] && [ "$REFRESH" != true ]; then
  echo "[generate-act-secrets] $SECRETS_FILE already exists — not overwriting"
  echo "  Re-pull GH_PAT from Secret Manager with:  bash $0 --refresh"
  exit 0
fi

if [ -f "$SECRETS_FILE" ] && [ "$REFRESH" = true ]; then
  if [ -z "$_sm_pat" ]; then
    echo "[generate-act-secrets] --refresh: GH_PAT unavailable from Secret Manager (gcloud/aws) — leaving existing file unchanged" >&2
    exit 0
  fi
  # In-place refresh of ONLY the GH_PAT line, preserving any other secrets in the file.
  if grep -qE '^GH_PAT=' "$SECRETS_FILE"; then
    _tmp="$(mktemp)"; sed "s|^GH_PAT=.*|GH_PAT=${_sm_pat}|" "$SECRETS_FILE" > "$_tmp" && mv "$_tmp" "$SECRETS_FILE"
  else
    printf 'GH_PAT=%s\n' "$_sm_pat" >> "$SECRETS_FILE"
  fi
  chmod 600 "$SECRETS_FILE"
  echo "[generate-act-secrets] refreshed GH_PAT in $SECRETS_FILE from Secret Manager"
  exit 0
fi

# Fresh file: populate GH_PAT from Secret Manager when available, else leave blank for manual fill.
cat > "$SECRETS_FILE" << EOF
# act secrets — never commit this file
# GH_PAT auto-pulled from Secret Manager when available (else add manually:
# https://github.com/settings/tokens — needs 'repo' + 'workflow' scope). Re-pull: $0 --refresh
GH_PAT=${_sm_pat}
EOF

chmod 600 "$SECRETS_FILE"

# Ensure .act-secrets is ignored at workspace root
GITIGNORE="${WORKSPACE_ROOT}/.gitignore"
if [ -f "$GITIGNORE" ]; then
  if ! grep -q "^\.act-secrets$" "$GITIGNORE" 2>/dev/null; then
    echo "" >> "$GITIGNORE"
    echo "# act secrets (generate-act-secrets.sh)" >> "$GITIGNORE"
    echo ".act-secrets" >> "$GITIGNORE"
    echo "[generate-act-secrets] Added .act-secrets to $GITIGNORE"
  fi
else
  echo ".act-secrets" > "$GITIGNORE"
  echo "[generate-act-secrets] Created $GITIGNORE with .act-secrets"
fi

echo ""
echo "Created: $SECRETS_FILE"
echo ""
echo "Next steps:"
echo "  1. Edit $SECRETS_FILE"
echo "  2. Add your GitHub PAT:  GH_PAT=ghp_xxxxxxxxxxxx"
echo "     (Create at https://github.com/settings/tokens — needs 'repo' + 'workflow' scope"
echo "      for ci-status-update dispatch; Status 400 = token lacks workflow scope)"
echo "  3. Save (file is chmod 600)"
echo ""
echo "Quickmerge will use this file for act simulation when present."
echo "Run propagate-github-secrets.sh to push GH_PAT to all repos (CI needs it for ci-status-update)."
