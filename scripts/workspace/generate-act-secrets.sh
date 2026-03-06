#!/bin/bash
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

if [ -f "$SECRETS_FILE" ]; then
  echo "[generate-act-secrets] $SECRETS_FILE already exists — not overwriting"
  echo "  Edit it manually to update GH_PAT"
  exit 0
fi

cat > "$SECRETS_FILE" << 'EOF'
# act secrets — never commit this file
# Add your GitHub PAT (create at https://github.com/settings/tokens)
GH_PAT=
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
echo "  3. Save (file is chmod 600)"
echo ""
echo "Quickmerge will use this file for act simulation when present."
