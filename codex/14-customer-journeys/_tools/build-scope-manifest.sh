#!/usr/bin/env bash
# Build the codex scope manifest (rule 11).
#
# Walks every codex/**/*.md under the PM repo, parses YAML frontmatter, and
# emits codex/14-playbooks/_generated/scope-manifest.json mapping each audience
# (sales | engineer | admin | prospect | investor) to the list of codex paths
# visible to it.
#
# SSOT: codex/14-playbooks/_ssot-rules/11-codex-scope-registry.md
#
# Usage:
#   bash codex/14-playbooks/_tools/build-scope-manifest.sh [--verbose]
#
# Exit non-zero on malformed YAML, unknown scope values, or non-array scope
# fields. Does not fail on missing `scope:` — defaults to [engineer, admin]
# and emits a per-file warning. For strict coverage enforcement, use
# check-scope-coverage.sh.

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

exec "${PYTHON_BIN}" "${SCRIPT_DIR}/build_scope_manifest.py" --root "${PM_ROOT}" "$@"
