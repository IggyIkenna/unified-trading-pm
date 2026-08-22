#!/usr/bin/env bash
# Epic: instruments_master
# Lifecycle: permanent
# Delete-when: NA
# QG: no-hardcoded-catalogue-attribute
# A T2 consumer (instruments-service/market-tick-data-service/
# market-data-processing-service) MUST query the instruments-service
# catalogue for a MUTABLE instrument attribute (contract_size today), never
# hardcode/derive it. Same discriminator class as no_hardcoded_venue_urls.sh
# / no_hardcoded_venue_universe.sh, applied to catalogue-owned reference
# data instead of venue endpoints/universes.
#
# AST-based (no_hardcoded_catalogue_attribute.py) rather than a grep pattern
# list — the violation shape (a literal bound to/compared against a field
# name) generalizes across arbitrary variable/dict-key spellings that a
# fixed regex would miss.
#
# SSOT: plans/active/instruments_catalogue_definitions_and_field_history_2026_08_17.md
#       § "The query-don't-derive gate"
#
# Usage: bash scripts/qg/no_hardcoded_catalogue_attribute.sh <repo_root>
# Returns: 0 (pass), 1 (violations found or a T2 repo missing)
#
# owner: slot-2  cadence: CI (pre-merge, instruments-service QG)  verifier: quality-gates.sh
# last_executed: 2026-08-22

set -euo pipefail

REPO_ROOT="${1:-$(git rev-parse --show-toplevel)/..}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PYTHON="${WORKSPACE_ROOT:+${WORKSPACE_ROOT}/.venv-workspace/bin/python3}"
PYTHON="${PYTHON:-python3}"
[[ -x "$PYTHON" ]] || PYTHON="python3"

"$PYTHON" "${SCRIPT_DIR}/no_hardcoded_catalogue_attribute.py" --repo-root "$REPO_ROOT"
