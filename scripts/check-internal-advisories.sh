#!/usr/bin/env bash
# Check repo dependencies against internal vulnerability advisories.
# Invokes check-internal-advisories.py. Exit 0 = clean, 1 = violation.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CHECK_REPO_ROOT="${CHECK_REPO_ROOT:-$(pwd)}"

exec python3 "$PM_ROOT/scripts/check-internal-advisories.py" \
    --repo-root "$CHECK_REPO_ROOT" \
    --lock "$CHECK_REPO_ROOT/uv.lock"
