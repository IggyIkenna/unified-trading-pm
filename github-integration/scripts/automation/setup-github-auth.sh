#!/usr/bin/env bash
# Setup GitHub authentication for automation scripts on fresh VMs
# This script configures git/gh CLI to authenticate with GitHub using a PAT stored in GCP Secret Manager

set -euo pipefail

# Configuration
SECRET_NAME="${GITHUB_TOKEN_SECRET:-github-automation-token}"
GCP_PROJECT="${GCP_PROJECT:?GCP_PROJECT required}"

echo "🔐 Setting up GitHub authentication..."

# Check if running on GCP (has gcloud and metadata server)
if command -v gcloud &>/dev/null && curl -s -f -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/id &>/dev/null; then
  echo "  ✓ Running on GCP VM"

  # Fetch GitHub token from Secret Manager
  if ! GITHUB_TOKEN=$(gcloud secrets versions access latest --secret="$SECRET_NAME" --project="$GCP_PROJECT" 2>/dev/null); then
    echo "  ❌ Failed to fetch secret '$SECRET_NAME' from GCP Secret Manager"
    echo "  Create it with: echo -n 'ghp_yourToken' | gcloud secrets create $SECRET_NAME --data-file=-"
    exit 1
  fi
  echo "  ✓ Fetched GitHub token from Secret Manager"

elif [ -n "${GITHUB_TOKEN:-}" ]; then
  echo "  ✓ Using GITHUB_TOKEN from environment"
  # Token already in environment

else
  echo "  ❌ No GitHub token available"
  echo "  Options:"
  echo "    1. Run on GCP with secret in Secret Manager"
  echo "    2. Export GITHUB_TOKEN environment variable"
  echo "    3. Run 'gh auth login' manually"
  exit 1
fi

# Install Cursor CLI if not present (REQUIRED for automation)
if ! command -v cursor &>/dev/null; then
  echo "  Installing Cursor CLI..."
  if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS: Download and install
    curl -fsSL https://download.todesktop.com/210203cqcj00tw1/Cursor%20Setup%200.43.6%20-%20Build%20241206zzmzbh6mn-arm64.dmg -o /tmp/cursor.dmg
    hdiutil attach /tmp/cursor.dmg
    cp -R "/Volumes/Cursor/Cursor.app" /Applications/
    hdiutil detach "/Volumes/Cursor"
    rm /tmp/cursor.dmg
    # Add to PATH
    echo 'export PATH="/Applications/Cursor.app/Contents/Resources/app/bin:$PATH"' >>~/.zshrc
    export PATH="/Applications/Cursor.app/Contents/Resources/app/bin:$PATH"
  else
    # Linux: Install from official site
    curl -fsSL https://download.cursor.sh/linux/stable/latest -o /tmp/cursor.AppImage
    chmod +x /tmp/cursor.AppImage
    sudo mv /tmp/cursor.AppImage /usr/local/bin/cursor
    # Or use the CLI directly
    curl -fsSL https://download.cursor.sh/linux/cli/latest -o /tmp/cursor-cli
    chmod +x /tmp/cursor-cli
    sudo mv /tmp/cursor-cli /usr/local/bin/cursor
  fi
  echo "  ✓ Cursor CLI installed"
else
  echo "  ✓ Cursor CLI already installed"
fi

# Install gh CLI if not present
if ! command -v gh &>/dev/null; then
  echo "  Installing gh CLI..."
  if [[ "$OSTYPE" == "darwin"* ]]; then
    brew install gh
  else
    # Linux (Debian/Ubuntu)
    type -p curl >/dev/null || (sudo apt update && sudo apt install curl -y)
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
      && sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
      && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null \
      && sudo apt update \
      && sudo apt install gh -y
  fi
  echo "  ✓ gh CLI installed"
else
  echo "  ✓ gh CLI already installed"
fi

# Configure gh CLI authentication
echo "$GITHUB_TOKEN" | gh auth login --with-token
if gh auth status &>/dev/null; then
  echo "  ✓ gh CLI authenticated successfully"
else
  echo "  ❌ gh CLI authentication failed"
  exit 1
fi

# Configure git to use gh for authentication (recommended)
gh auth setup-git
echo "  ✓ Git configured to use gh CLI for authentication"

# Alternative: Configure git credential helper (if not using gh)
# git config --global credential.helper store
# echo "https://github-automation:${GITHUB_TOKEN}@github.com" > ~/.git-credentials
# echo "  ✓ Git credential helper configured"

# Configure git identity (for commits) — GUARDED so it NEVER clobbers an operator's
# already-set identity (root-cause of the fleet bot-email leak:
# commit_identity_misconfig_fleet_2026_06_03.md). An unconditional `git config --global
# user.email "<bot>"` here was the leak CLASS — it overwrote a worktree/global identity
# with a generic CI/bot value, so agent commits then masqueraded as the bot. Only write
# when UNSET, and prefer the canonical operator identity (env → per-machine
# slotIdentity.* → Ikenna fleet default) over the bot placeholder. Per-slot worktree
# identity is owned by setup-tab-worktrees.sh + the fix-commit-identity hook.
_gi_email="${GIT_USER_EMAIL:-${SLOT_CANON_EMAIL:-$(git config --global slotIdentity.email 2>/dev/null || true)}}"
_gi_name="${GIT_USER_NAME:-${SLOT_CANON_NAME:-$(git config --global slotIdentity.name 2>/dev/null || true)}}"
if [ -z "$(git config --global user.name 2>/dev/null)" ]; then
  git config --global user.name "${_gi_name:-ikennaigboaka}"
fi
if [ -z "$(git config --global user.email 2>/dev/null)" ]; then
  git config --global user.email "${_gi_email:-ikennaigboaka@gmail.com}"
fi
echo "  ✓ Git identity configured (guarded — did not overwrite an existing identity)"

# Test authentication
if gh repo view IggyIkenna/unified-trading-codex &>/dev/null; then
  echo "  ✓ GitHub authentication test passed"
else
  echo "  ❌ GitHub authentication test failed"
  exit 1
fi

echo "✅ GitHub authentication setup complete!"
echo ""
echo "You can now run batch-fix-v2.sh to automate issue fixes."
