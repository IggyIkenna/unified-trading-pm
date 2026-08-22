#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Self-test for base-service.sh STEP 5.63 run_lifecycle pairing gate.
# Builds three throwaway fixture trees and asserts the matcher logic in
# base-service.sh either flags or accepts each as expected.
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-step-5-63-run-lifecycle.sh
set -euo pipefail

WORKDIR="$(mktemp -d -t step_5_63.XXXXXX)"
trap 'rm -rf "$WORKDIR"' EXIT

# Replica of the matcher in base-service.sh STEP 5.63.
# Exits 0 if no violations, 1 if any file is missing pairing.
check_dir() {
    local source_dir="$1"
    local files violations="" f
    files=$(rg -l 'setup_events\(' --type py \
        --glob '!.venv*' \
        --glob '!**/tests/**' \
        --glob '!**/run_lifecycle.py' \
        --glob '!**/events/__init__.py' \
        "$source_dir/" 2>/dev/null || :)
    for f in $files; do
        if grep -q 'def setup_events' "$f" 2>/dev/null; then continue; fi
        if grep -q 'ServiceBootstrap(' "$f" 2>/dev/null; then continue; fi
        if grep -q 'run_lifecycle(' "$f" 2>/dev/null; then continue; fi
        if grep -qE '_RUN_STARTED' "$f" 2>/dev/null && \
           grep -qE '_RUN_(COMPLETED|FAILED)' "$f" 2>/dev/null; then
            continue
        fi
        violations="${violations}${f} "
    done
    if [ -n "$violations" ]; then
        echo "VIOLATIONS: $violations"
        return 1
    fi
    return 0
}

# ── Fixture A: bad — setup_events without lifecycle pairing ──────────────────
mkdir -p "$WORKDIR/bad"
cat > "$WORKDIR/bad/script.py" <<'PYEOF'
from unified_trading_library import setup_events, log_event
def main() -> int:
    setup_events(service_name="bad-script", mode="local")
    log_event("WORK_DONE", metadata={})
    return 0
PYEOF

if check_dir "$WORKDIR/bad"; then
    echo "FAIL: bad fixture should have been flagged but passed"
    exit 1
fi
echo "PASS: bad fixture correctly flagged"

# ── Fixture B: good — uses run_lifecycle ─────────────────────────────────────
mkdir -p "$WORKDIR/good_run_lifecycle"
cat > "$WORKDIR/good_run_lifecycle/script.py" <<'PYEOF'
from unified_trading_library import run_lifecycle, setup_events
def main() -> int:
    setup_events(service_name="good-script", mode="local")
    with run_lifecycle(service_name="good-script", details={}) as run:
        run.update(rows=1)
    return 0
PYEOF

if ! check_dir "$WORKDIR/good_run_lifecycle"; then
    echo "FAIL: good_run_lifecycle fixture should have passed but was flagged"
    exit 1
fi
echo "PASS: good_run_lifecycle fixture accepted"

# ── Fixture C: good — uses ServiceBootstrap ──────────────────────────────────
mkdir -p "$WORKDIR/good_bootstrap"
cat > "$WORKDIR/good_bootstrap/svc.py" <<'PYEOF'
from unified_trading_library import ServiceBootstrap, setup_events
def main() -> int:
    setup_events(service_name="svc", mode="local")
    ServiceBootstrap(service_name="svc").run(lambda: None)
    return 0
PYEOF

if ! check_dir "$WORKDIR/good_bootstrap"; then
    echo "FAIL: good_bootstrap fixture should have passed but was flagged"
    exit 1
fi
echo "PASS: good_bootstrap fixture accepted"

# ── Fixture D: good — explicit legacy *_RUN_STARTED + *_RUN_FAILED pair ──────
mkdir -p "$WORKDIR/good_legacy"
cat > "$WORKDIR/good_legacy/script.py" <<'PYEOF'
from unified_trading_library import setup_events, log_event
def main() -> int:
    setup_events(service_name="legacy-script", mode="local")
    log_event("LEGACY_RUN_STARTED", metadata={})
    try:
        do_work()
    except Exception:
        log_event("LEGACY_RUN_FAILED", metadata={})
        raise
    log_event("LEGACY_RUN_COMPLETED", metadata={})
    return 0
PYEOF

if ! check_dir "$WORKDIR/good_legacy"; then
    echo "FAIL: good_legacy fixture should have passed but was flagged"
    exit 1
fi
echo "PASS: good_legacy fixture accepted"

# ── Fixture E: helper-defining file (UTL run_lifecycle.py itself) ────────────
mkdir -p "$WORKDIR/helper_self"
cat > "$WORKDIR/helper_self/run_lifecycle.py" <<'PYEOF'
def setup_events(): pass
def def_setup_events_marker(): pass
PYEOF

if ! check_dir "$WORKDIR/helper_self"; then
    echo "FAIL: helper_self fixture should have been skipped by glob"
    exit 1
fi
echo "PASS: helper_self fixture correctly skipped"

echo ""
echo "STEP 5.63 self-test: ALL PASSED"
