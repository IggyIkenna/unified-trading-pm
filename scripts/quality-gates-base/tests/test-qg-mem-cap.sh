#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Smoke tests for the QG_MEM_CAP / MEM_WRAP block in base-service.sh.
#
# Tests:
#   (a) Linux path: systemd-run available → MEM_WRAP is populated.
#   (b) macOS-simulated: fake systemd-run fails → MEM_WRAP empty + warning emitted.
#   (c) QG_MEM_CAP=0: MEM_WRAP empty + no warning regardless of systemd-run.
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-qg-mem-cap.sh
set -euo pipefail

PASS=0
FAIL=0
FAKE_BIN=$(mktemp -d)
trap 'rm -rf "$FAKE_BIN"' EXIT

pass() { echo "PASS: $*"; ((PASS += 1)); }
fail() { echo "FAIL: $*"; ((FAIL += 1)); }

BASE_SERVICE="$(cd "$(dirname "$0")/.." && pwd)/base-service.sh"
MEM_CAP_BLOCK=$(sed -n '96,114p' "$BASE_SERVICE")

# Create a fake systemd-run that always fails (simulates macOS / no cgroup).
cat > "$FAKE_BIN/systemd-run" << 'FAKE'
#!/bin/bash
exit 1
FAKE
chmod +x "$FAKE_BIN/systemd-run"

# ── Test (a): Linux systemd path ─────────────────────────────────────────────
if command -v systemd-run >/dev/null 2>&1 \
   && systemd-run --user --scope -p MemoryMax=100M --quiet -- true >/dev/null 2>&1; then
    wrap_len=$(bash -c "
        QG_MEM_CAP=10G
        ${MEM_CAP_BLOCK}
        echo \"\${#MEM_WRAP[@]}\"
    " 2>/dev/null)
    if [[ "$wrap_len" -gt 0 ]]; then
        pass "(a) Linux systemd path: MEM_WRAP populated (len=$wrap_len) when QG_MEM_CAP=10G"
    else
        fail "(a) Linux systemd path: MEM_WRAP empty despite working systemd-run"
    fi
else
    pass "(a) Linux systemd path: SKIP — systemd-run not available on this host"
fi

# ── Test (b): macOS-simulated (fake systemd-run that always fails) ────────────
combined_b=$(PATH="$FAKE_BIN:/usr/bin:/bin" bash -c "
    unset _QG_OOM_WARN_SHOWN
    QG_MEM_CAP=10G
    ${MEM_CAP_BLOCK}
    echo \"wrap_len=\${#MEM_WRAP[@]}\"
" 2>&1)

wrap_len_b=$(echo "$combined_b" | grep "^wrap_len=" | sed 's/wrap_len=//')
warning_count=$(echo "$combined_b" | grep -c "QG_MEM_CAP.*set but systemd-run unavailable" || true)

if [[ "${wrap_len_b:-1}" == "0" ]]; then
    pass "(b) macOS-simulated: MEM_WRAP empty when systemd-run unavailable"
else
    fail "(b) macOS-simulated: MEM_WRAP should be empty (got ${wrap_len_b:-?})"
fi

if [[ "$warning_count" -gt 0 ]]; then
    pass "(b) macOS-simulated: warning emitted on stderr"
else
    fail "(b) macOS-simulated: expected warning but none seen"
fi

# ── Test (c): QG_MEM_CAP=0 silences warning ──────────────────────────────────
combined_c=$(PATH="$FAKE_BIN:/usr/bin:/bin" bash -c "
    unset _QG_OOM_WARN_SHOWN
    QG_MEM_CAP=0
    ${MEM_CAP_BLOCK}
    echo \"wrap_len=\${#MEM_WRAP[@]}\"
" 2>&1)

wrap_len_c=$(echo "$combined_c" | grep "^wrap_len=" | sed 's/wrap_len=//')
warning_count_c=$(echo "$combined_c" | grep -c "QG_MEM_CAP.*set but systemd-run unavailable" || true)

if [[ "${wrap_len_c:-1}" == "0" ]]; then
    pass "(c) QG_MEM_CAP=0: MEM_WRAP empty"
else
    fail "(c) QG_MEM_CAP=0: MEM_WRAP should be empty (got ${wrap_len_c:-?})"
fi

if [[ "$warning_count_c" -eq 0 ]]; then
    pass "(c) QG_MEM_CAP=0: no warning emitted (silenced correctly)"
else
    fail "(c) QG_MEM_CAP=0: warning should be suppressed but appeared"
fi

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
if [[ "$FAIL" -eq 0 ]]; then
    echo "QG_MEM_CAP smoke tests: ALL ${PASS} PASSED"
    exit 0
else
    echo "QG_MEM_CAP smoke tests: ${PASS} passed, ${FAIL} FAILED"
    exit 1
fi
