#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# 2026-04-22 — QuestionnaireResponse UAC <-> UI parity (G1.10 §Deviations trigger).
#
# Confirms that the UI TypeScript mirror at
# ``unified-trading-system-ui/lib/questionnaire/types.ts`` still covers
# every field + Literal member declared by the UAC Pydantic model
# ``QuestionnaireResponse``. Wired into
# ``unified-trading-system-ui/scripts/quality-gates.sh`` so every UI push
# fails if the mirror drifts from UAC.
#
# Modes:
#   --check   (default) exit 1 on drift
#   --write   not implemented yet (hand-sync per Reg-Umbrella 2026-04-21)
#
# SSOT:
#   unified-api-contracts/unified_api_contracts/internal/architecture_v2/restriction_profiles.py

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "${HERE}/../.." && pwd)"
WORKSPACE_ROOT="${UNIFIED_TRADING_WORKSPACE_ROOT:-$(cd "${PM_ROOT}/.." && pwd)}"

if [[ ! -d "${WORKSPACE_ROOT}/unified-api-contracts" ]]; then
    echo "ERROR: UAC repo not found at ${WORKSPACE_ROOT}/unified-api-contracts" >&2
    echo "       Set UNIFIED_TRADING_WORKSPACE_ROOT or run from a sibling checkout." >&2
    exit 2
fi
if [[ ! -d "${WORKSPACE_ROOT}/unified-trading-system-ui" ]]; then
    echo "ERROR: UI repo not found at ${WORKSPACE_ROOT}/unified-trading-system-ui" >&2
    exit 2
fi

exec python3 "${HERE}/sync_questionnaire_response_to_ui.py" \
    --workspace-root "${WORKSPACE_ROOT}" "$@"
