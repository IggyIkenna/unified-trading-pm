#!/bin/bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
set -e

# Check if private package versions in pyproject.toml are published to Artifact Registry
# This prevents pushing code that depends on unpublished package versions

# Private packages published to Artifact Registry
PRIVATE_PACKAGES=(
  "unified-trading-library"
  "unified-config-interface"
  "unified-trading-library"
  "unified-domain-client"
  "unified-market-interface"
  "unified-trade-execution-interface"
  "execution-algo-library"
)

# GCP Configuration
GCP_PROJECT="${GCP_PROJECT:?GCP_PROJECT required}"
ARTIFACT_REGISTRY_REPO="python-packages"
ARTIFACT_REGISTRY_LOCATION="us-central1"

echo "🔍 Checking private package versions against Artifact Registry..."
echo ""

# Check if pyproject.toml exists
if [ ! -f "pyproject.toml" ]; then
  echo "⚠️  No pyproject.toml found in current directory"
  echo "   Run this script from a service/library root"
  exit 1
fi

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" >/dev/null 2>&1; then
  echo "❌ Not authenticated with gcloud"
  echo "   Run: gcloud auth login"
  exit 1
fi

MISSING_VERSIONS=0

for pkg in "${PRIVATE_PACKAGES[@]}"; do
  # Check if package is a dependency
  if ! grep -q "\"$pkg" pyproject.toml; then
    continue # Not a dependency, skip
  fi

  # Extract required version from pyproject.toml
  # Handles formats: "pkg>=1.2.3", "pkg>=1.2.3,<2.0.0"
  required_version=$(grep "\"$pkg" pyproject.toml | grep -oP '>=\K[0-9.]+' | head -1)

  if [ -z "$required_version" ]; then
    echo "⚠️  $pkg: Could not parse version requirement"
    continue
  fi

  echo -n "   Checking $pkg>=$required_version... "

  # Check if version exists in Artifact Registry
  # Note: This requires gcloud auth and permissions
  if gcloud artifacts versions list \
    --package="$pkg" \
    --repository="$ARTIFACT_REGISTRY_REPO" \
    --location="$ARTIFACT_REGISTRY_LOCATION" \
    --project="$GCP_PROJECT" \
    --format="value(name)" \
    2>/dev/null | grep -q "$required_version"; then
    echo "✅"
  else
    echo "❌ NOT FOUND"
    echo "      Version $required_version not published to Artifact Registry"
    echo "      Either:"
    echo "        1. Publish $pkg v$required_version first (run quickmerge in that repo)"
    echo "        2. Lower version requirement in pyproject.toml"
    MISSING_VERSIONS=$((MISSING_VERSIONS + 1))
  fi
done

echo ""

if [ $MISSING_VERSIONS -gt 0 ]; then
  echo "❌ $MISSING_VERSIONS private package version(s) not found in Artifact Registry"
  echo ""
  echo "This means GitHub Actions and Cloud Build will FAIL when they try to install deps."
  echo ""
  echo "Action required:"
  echo "  1. Navigate to the missing package repo"
  echo "  2. Bump version in pyproject.toml if needed"
  echo "  3. Run: bash scripts/quickmerge.sh \"publish version\""
  echo "  4. Wait for Cloud Build to publish to Artifact Registry (~5 min)"
  echo "  5. Come back and try again"
  exit 1
else
  echo "✅ All private package versions are published to Artifact Registry"
  echo "   Safe to push to GitHub!"
fi
