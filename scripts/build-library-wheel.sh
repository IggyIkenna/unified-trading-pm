#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# build-library-wheel.sh — Build Python wheel for a library (local or CI)
#
# Keeps wheel builds consistent: uv + python -m build. No Docker.
# Use before publish when validating locally, or in CI before Cloud Build publish.
#
# Usage:
#   bash scripts/build-library-wheel.sh [REPO_PATH]
#   bash scripts/build-library-wheel.sh ../unified-api-contracts
#
# If REPO_PATH omitted, uses current directory (must have pyproject.toml).
# Output: dist/*.whl
#
# Does NOT publish. For publish use Cloud Build or twine manually.

set -e

REPO_PATH="${1:-.}"
REPO_PATH="$(cd "$REPO_PATH" && pwd)"

if [ ! -f "$REPO_PATH/pyproject.toml" ]; then
  echo "ERROR: No pyproject.toml in $REPO_PATH"
  exit 1
fi

cd "$REPO_PATH"
echo "=== Building wheel in $REPO_PATH ==="

# Prefer uv; fallback to pip
if command -v uv >/dev/null 2>&1; then
  uv pip install build
  uv run python -m build --wheel --outdir dist/
else
  pip install build
  python -m build --wheel --outdir dist/
fi

ls -lh dist/*.whl
echo "=== Wheel built successfully ==="
