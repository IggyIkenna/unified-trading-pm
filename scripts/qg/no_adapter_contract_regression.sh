#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# QG STEP 5.83 — no_adapter_contract_regression
# Per-file ratchet on adapter contract calls: once a file ships N calls of
#   classify_venue_error | ADAPTER_FETCH_FAILED | record_captured | record_empty | record_failed
# subsequent commits MUST keep >= N. Catches the regression class demonstrated
# 2026-05-20: execution-service@774602ea8 + @6ba53d526 silently wiped 31
# classify_venue_error calls from kalshi.py + polymarket_clob.py during
# lint/method-size sweeps.
#
# Reference incident: plans/active/issues/lint_sweep_774602ea8_regression_audit_2026_05_20.md
# Baseline:           unified-trading-pm/scripts/quality_gates/adapter_contract_baseline.yaml
# Scanner:            unified-trading-pm/scripts/quality_gates/check_adapter_contract_regression.py
#
# Usage: bash scripts/qg/no_adapter_contract_regression.sh <workspace_root>
# Returns: 0 (pass), 1 (violations found)
#
# owner: slot-1  cadence: CI (pre-merge)  verifier: quality-gates.sh
# last_executed: 2026-05-20

set -euo pipefail

WORKSPACE_ROOT="${1:-${WORKSPACE_ROOT:-}}"
if [[ -z "${WORKSPACE_ROOT}" ]]; then
    WORKSPACE_ROOT="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
fi

if [[ ! -d "${WORKSPACE_ROOT}" ]]; then
    echo "ERROR: workspace root not found: ${WORKSPACE_ROOT}" >&2
    exit 1
fi

SCANNER="${WORKSPACE_ROOT}/unified-trading-pm/scripts/quality_gates/check_adapter_contract_regression.py"
if [[ ! -f "${SCANNER}" ]]; then
    echo "ERROR: scanner not found: ${SCANNER}" >&2
    exit 1
fi

python3 "${SCANNER}" --workspace-root "${WORKSPACE_ROOT}"
