#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# G1.7 — UAC restriction-profile YAMLs <-> UI restriction-profiles.ts parity.
#
# Reads the 6 committed YAML files at
# ``codex/14-playbooks/demo-ops/profiles/*.yaml`` and renders / verifies the
# UI's ``lib/architecture-v2/restriction-profiles.ts``. Wired into
# ``unified-trading-system-ui/scripts/quality-gates.sh`` so every UI push
# fails if the TS mirror drifts from PM YAML.
#
# Modes:
#   --check   (default) exit 1 on drift
#   --write   rewrite restriction-profiles.ts
#
# SSOTs:
#   unified-trading-pm/codex/14-playbooks/demo-ops/profiles/*.yaml
#   unified-trading-pm/codex/14-playbooks/demo-ops/_tools/validate_profiles.py

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "${HERE}/../.." && pwd)"
WORKSPACE_ROOT="${UNIFIED_TRADING_WORKSPACE_ROOT:-$(cd "${PM_ROOT}/.." && pwd)}"

if [[ ! -d "${WORKSPACE_ROOT}/unified-trading-pm" ]]; then
    echo "ERROR: PM repo not found at ${WORKSPACE_ROOT}/unified-trading-pm" >&2
    echo "       Set UNIFIED_TRADING_WORKSPACE_ROOT or run from a sibling checkout." >&2
    exit 2
fi
if [[ ! -d "${WORKSPACE_ROOT}/unified-trading-system-ui" ]]; then
    echo "ERROR: UI repo not found at ${WORKSPACE_ROOT}/unified-trading-system-ui" >&2
    exit 2
fi

exec python3 "${HERE}/sync_restriction_profiles_to_ui.py" \
    --workspace-root "${WORKSPACE_ROOT}" "$@"
