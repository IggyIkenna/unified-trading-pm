#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Verify that every repo in workspace-manifest.json with a github_url has a matching
# GitHub repo name (i.e. the last segment of github_url equals the manifest key).
# Usage: from unified-trading-pm: ./scripts/verify-github-repo-names.sh
# Requires: jq, gh (optional: to check actual GitHub repo name via gh repo view)

set -euo pipefail
# Resolve workspace root from cwd (must run from workspace root)
if [ -f "$(pwd)/unified-trading-pm/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(pwd)"
elif [ -f "$(pwd)/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(cd .. && pwd)"
else
  echo "Error: Run from workspace root. Expected unified-trading-pm/workspace-manifest.json"
  exit 1
fi
MANIFEST="$WORKSPACE_ROOT/unified-trading-pm/workspace-manifest.json"

if [[ ! -f "$MANIFEST" ]]; then
  echo "Missing $MANIFEST"
  exit 1
fi

echo "Checking workspace-manifest.json github_url vs repo key..."
echo ""

mismatch=0
while IFS= read -r line; do
  # line format: "repo-key" or with github_url on next lines; we parse key and url
  :
done < <(jq -r '.repositories | to_entries[] | "\(.key)|\(.value.github_url // "")"' "$MANIFEST")

while IFS='|' read -r key url; do
  if [[ -z "$url" || "$url" == "null" ]]; then
    continue
  fi
  # url is https://github.com/OWNER/REPO or https://github.com/OWNER/REPO/
  expected_repo="${url%/}"
  expected_repo="${expected_repo##*/}"
  if [[ "$key" != "$expected_repo" ]]; then
    echo "MISMATCH: manifest key '$key' vs github_url repo '$expected_repo'"
    mismatch=1
  fi
done < <(jq -r '.repositories | to_entries[] | "\(.key)|\(.value.github_url // "")"' "$MANIFEST")

if [[ $mismatch -eq 0 ]]; then
  echo "OK: All github_url repo names match their manifest keys."
else
  echo ""
  echo "Fix: Update github_url in workspace-manifest.json so the repo segment matches the key."
  exit 1
fi

# Optional: verify folder exists and remote matches (if gh and git available)
echo ""
echo "Checking workspace folders and remotes (when .git present)..."
for key in $(jq -r '.repositories | keys[]' "$MANIFEST"); do
  url=$(jq -r --arg k "$key" '.repositories[$k].github_url // ""' "$MANIFEST")
  [[ -z "$url" ]] && continue
  dir="$WORKSPACE_ROOT/$key"
  if [[ ! -d "$dir" ]]; then
    echo "  (no folder: $key)"
    continue
  fi
  if [[ -d "$dir/.git" ]]; then
    remote=$(git -C "$dir" remote get-url origin 2>/dev/null || true)
    if [[ -n "$remote" ]]; then
      # normalize: strip .git, get repo name
      remote_repo="${remote%.git}"
      remote_repo="${remote_repo##*[:/]}"
      expected="${url%/}"
      expected="${expected##*/}"
      if [[ "$remote_repo" != "$expected" ]]; then
        echo "  REMOTE MISMATCH: $key has origin $remote_repo, manifest expects $expected"
        mismatch=1
      fi
    fi
  fi
done

if [[ $mismatch -eq 0 ]]; then
  echo "OK: Folders and remotes consistent with manifest."
fi
exit $mismatch
