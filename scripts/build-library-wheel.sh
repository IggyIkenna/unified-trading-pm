#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
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

# ── Phase-2 spike guards #1 (clean-checkout-at-tag) + #2 (publish-only-plain-3-part) ──────────────
# Under dynamic versioning (hatch-vcs/setuptools-scm), a DIRTY tree or a commit PAST the latest tag
# produces a prerelease like `0.18.18.dev1+g<sha>` / `0.1.dev2+g<sha>` (verified in the sandbox
# spike). Publishing that to AR lets a consumer silently resolve a `.devN` wheel under a `<X.0.0`
# range. So the release build must yield a PLAIN 3-part `X.Y.Z` — i.e. be a clean checkout AT the
# exact tag. We assert it on the BUILT artifact (catches dirty-tree AND commits-past-tag in one
# check). Static-versioned repos always pass (their version is a literal); only a dynamic repo built
# off-tag trips it. Override for deliberate local dev-wheel iteration with ALLOW_DEV_WHEEL=true.
NEWEST_WHEEL="$(ls -t dist/*.whl | head -1)"
WHEEL_VERSION="$(basename "$NEWEST_WHEEL" | cut -d- -f2)"
if ! printf '%s' "$WHEEL_VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
  echo "❌ Built wheel version '${WHEEL_VERSION}' is NOT a plain 3-part X.Y.Z (got a prerelease/local segment)." >&2
  echo "   Under dynamic versioning this means the build was NOT a clean checkout at a release tag" >&2
  echo "   (dirty tree or commits past the latest tag). Refusing to produce a publishable dev wheel." >&2
  echo "   Fix: build from a clean checkout AT the exact 'vX.Y.Z' tag. Override for local-only dev" >&2
  echo "   iteration with ALLOW_DEV_WHEEL=true." >&2
  if [ "${ALLOW_DEV_WHEEL:-false}" = "true" ]; then
    echo "   ALLOW_DEV_WHEEL=true — continuing with the dev wheel (local override; NEVER publish this)." >&2
  else
    exit 1
  fi
fi

echo "=== Wheel built successfully (version ${WHEEL_VERSION}) ==="
