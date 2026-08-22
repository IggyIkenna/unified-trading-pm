#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# G1.8 — UAC <-> UI archetype-capability parity.
#
# Reads the committed UAC manifest
# (``archetype_capability_manifest.json``) and renders / verifies the UI's
# ``lib/architecture-v2/coverage.ts``. Wired into
# ``unified-trading-system-ui/scripts/quality-gates.sh`` so every UI push
# fails if the TS mirror drifts from UAC.
#
# Modes:
#   --check   (default) exit 1 on drift
#   --write   rewrite coverage.ts
#
# SSOT:
#   unified-api-contracts/unified_api_contracts/internal/architecture_v2/
#   archetype_capability_manifest.json

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

exec python3 "${HERE}/sync_archetype_capability_to_ui.py" \
    --workspace-root "${WORKSPACE_ROOT}" "$@"
