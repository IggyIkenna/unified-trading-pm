#!/usr/bin/env bash
# CI gate: fail if any codex/**/*.md lacks `scope:` frontmatter or declares
# an invalid scope value.
#
# SSOT: codex/14-playbooks/_ssot-rules/11-codex-scope-registry.md
#
# Invoked from unified-trading-pm/scripts/quality-gates.sh.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

if [[ ! -f "${PM_ROOT}/codex/00-SSOT-INDEX.md" ]]; then
    echo "ERROR: expected PM repo root at ${PM_ROOT} (missing codex/00-SSOT-INDEX.md)" >&2
    exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
    echo "ERROR: python3 not found on PATH (override with PYTHON_BIN=...)" >&2
    exit 1
fi

exec "${PYTHON_BIN}" "${SCRIPT_DIR}/build_scope_manifest.py" \
    --root "${PM_ROOT}" \
    --check-only "$@"
