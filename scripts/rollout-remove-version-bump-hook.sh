#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# rollout-remove-version-bump-hook.sh
#
# Removes the local bump-library-version pre-commit hook from all repos.
# The GHA version-bump.yml is the sole authoritative version bumper —
# the local hook causes double-bumps and incorrect PATCH pre-bumps on feature branches.
#
# Usage: bash unified-trading-pm/scripts/rollout-remove-version-bump-hook.sh [--dry-run]
#
# Idempotent: skips repos where the hook is already absent.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
MANIFEST="${WORKSPACE_ROOT}/unified-trading-pm/workspace-manifest.json"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
  echo "[dry-run] No changes will be committed."
fi

if [ ! -f "$MANIFEST" ]; then
  echo "ERROR: workspace-manifest.json not found at $MANIFEST"
  exit 1
fi

# Get all repo names from manifest
REPOS=$(python3 -c "
import json
with open('$MANIFEST') as f:
    m = json.load(f)
for name in m.get('repositories', {}).keys():
    print(name)
")

SKIPPED=()
CHANGED=()
FAILED=()

for REPO in $REPOS; do
  REPO_DIR="${WORKSPACE_ROOT}/${REPO}"

  if [ ! -d "$REPO_DIR" ]; then
    echo "[skip] $REPO — directory not found"
    SKIPPED+=("$REPO")
    continue
  fi

  PRE_COMMIT="${REPO_DIR}/.pre-commit-config.yaml"
  BUMP_SCRIPT="${REPO_DIR}/scripts/bump-library-version.sh"

  # Check if hook is present
  if [ ! -f "$PRE_COMMIT" ] || ! grep -q "bump-library-version" "$PRE_COMMIT" 2>/dev/null; then
    if [ ! -f "$BUMP_SCRIPT" ]; then
      echo "[skip] $REPO — hook already absent"
      SKIPPED+=("$REPO")
      continue
    fi
  fi

  echo ""
  echo "=== $REPO ==="

  if [ "$DRY_RUN" = true ]; then
    if [ -f "$PRE_COMMIT" ] && grep -q "bump-library-version" "$PRE_COMMIT"; then
      echo "  [dry-run] would remove bump-library-version from .pre-commit-config.yaml"
    fi
    if [ -f "$BUMP_SCRIPT" ]; then
      echo "  [dry-run] would delete scripts/bump-library-version.sh"
    fi
    CHANGED+=("$REPO")
    continue
  fi

  MODIFIED=false

  # Remove the bump-library-version stanza from .pre-commit-config.yaml
  # The stanza looks like:
  #   # Auto-bump version for library changes (must run first)
  #   - repo: local
  #     hooks:
  #       - id: bump-library-version
  #         name: Auto-bump library version
  #         entry: bash scripts/bump-library-version.sh
  #         language: system
  #         pass_filenames: false
  #         stages: [commit]
  if [ -f "$PRE_COMMIT" ] && grep -q "bump-library-version" "$PRE_COMMIT"; then
    python3 - <<PYEOF
import re, sys

with open("${PRE_COMMIT}") as f:
    content = f.read()

# Remove the comment line before the stanza (if present) + the local repo block containing bump-library-version
# Pattern: optional comment line + '- repo: local' block that contains bump-library-version
# We match from the comment (or start of the repo block) to the next top-level repo entry or EOF
pattern = r'(?m)^  # Auto-bump version for library changes.*?\n(?=  - repo:|\Z)|^  - repo: local\n    hooks:\n      - id: bump-library-version\n(?:        .*\n)*'
new_content = re.sub(pattern, '', content)

# Also clean up double blank lines that may result
new_content = re.sub(r'\n{3,}', '\n\n', new_content)

if new_content == content:
    # Try a simpler block removal: find the local repo block with bump-library-version
    # and remove it and any preceding comment
    lines = content.splitlines(keepends=True)
    result = []
    i = 0
    while i < len(lines):
        # Skip comment line before the stanza
        if lines[i].strip().startswith('# Auto-bump version') and 'bump' in lines[i].lower():
            i += 1
            continue
        # Skip the local repo block containing bump-library-version
        if lines[i].rstrip() == '  - repo: local':
            # Look ahead to see if next hooks section contains bump-library-version
            block = [lines[i]]
            j = i + 1
            while j < len(lines) and (lines[j].startswith('    ') or lines[j].strip() == ''):
                block.append(lines[j])
                j += 1
            block_text = ''.join(block)
            if 'bump-library-version' in block_text:
                i = j  # skip entire block
                continue
        result.append(lines[i])
        i += 1
    new_content = ''.join(result)
    new_content = re.sub(r'\n{3,}', '\n\n', new_content)

if new_content == content:
    print("  WARNING: could not remove bump-library-version stanza automatically")
    sys.exit(0)

with open("${PRE_COMMIT}", 'w') as f:
    f.write(new_content)
print("  Removed bump-library-version from .pre-commit-config.yaml")
PYEOF
    MODIFIED=true
  fi

  # Delete the bump-library-version.sh script
  if [ -f "$BUMP_SCRIPT" ]; then
    rm "$BUMP_SCRIPT"
    echo "  Deleted scripts/bump-library-version.sh"
    MODIFIED=true
  fi

  if [ "$MODIFIED" = false ]; then
    echo "  Nothing to change"
    SKIPPED+=("$REPO")
    continue
  fi

  # Commit changes
  (
    cd "$REPO_DIR"

    # Stage only the specific files (never -A)
    [ -f ".pre-commit-config.yaml" ] && git add .pre-commit-config.yaml 2>/dev/null || true
    # Stage the deletion of bump-library-version.sh
    if ! git ls-files --error-unmatch scripts/bump-library-version.sh 2>/dev/null; then
      : # already deleted from git (wasn't tracked), nothing to stage
    else
      git rm --cached scripts/bump-library-version.sh 2>/dev/null || true
    fi
    # Ensure the deleted file is staged
    git add -u scripts/bump-library-version.sh 2>/dev/null || true

    # Check if there's anything to commit
    if git diff --cached --quiet; then
      echo "  [skip-commit] No staged changes in $REPO"
      return 0
    fi

    git commit -m "chore(ci): remove local bump-library-version pre-commit hook (version-bump.yml GHA is canonical) [skip ci]" \
      --no-verify 2>/dev/null || {
        echo "  WARNING: commit failed in $REPO (pre-commit hook may have fired)"
        FAILED+=("$REPO")
        return 1
      }
    echo "  Committed in $REPO"
  ) && CHANGED+=("$REPO") || FAILED+=("$REPO")

done

echo ""
echo "========================================"
echo "Rollout complete."
echo "  Changed: ${#CHANGED[@]} repos"
echo "  Skipped: ${#SKIPPED[@]} repos (hook already absent)"
echo "  Failed:  ${#FAILED[@]} repos"

if [ "${#CHANGED[@]}" -gt 0 ]; then
  echo ""
  echo "Changed repos:"
  for r in "${CHANGED[@]}"; do echo "  $r"; done
fi

if [ "${#FAILED[@]}" -gt 0 ]; then
  echo ""
  echo "Failed repos (manual intervention required):"
  for r in "${FAILED[@]}"; do echo "  $r"; done
  exit 1
fi
