#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Regression test for the `scripts/setup.sh` "[3] BOOTSTRAP UV" pinned-version fallback
# (issues/uv_pin_fleet_drift_2026_06_22.md § "Durable fix").
#
# Bug (found 2026-06-22): when uv was present but the WRONG version (drifted off the
# pinned 0.10.8), the fallback shelled out to `$PYTHON_CMD -m pip install`, where
# $PYTHON_CMD is the uv-managed CPython that has NO pip → non-zero exit → `set -e`
# aborted the whole setup.sh (human-planning-vm's bootstrap reported "Failed: 25").
# Even had pip been present, a pip-installed uv would not replace the active
# ~/.local/bin/uv binary, so it would not have actually realigned the fleet.
#
# Fix (2026-07-26): a wrong-version uv now falls to the astral standalone installer
# (pip-free, replaces the active binary in place), with the pip path kept only as the
# last resort when curl itself is unavailable.
#
# Like test-quickmerge-untracked-new-file-guard.sh, this EXTRACTS the REAL "[3]
# BOOTSTRAP UV" block from setup.sh (not a replica) and runs it against a stubbed
# uv/curl fixture — no real network call, deterministic offline.
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-setup-sh-uv-bootstrap-fallback.sh
set -uo pipefail

PASS=0
FAIL=0
pass() { echo "PASS: $*"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $*"; FAIL=$((FAIL + 1)); }

SETUP_SH="$(cd "$(dirname "$0")/../.." && pwd)/setup.sh"
[ -f "$SETUP_SH" ] || { echo "FATAL: setup.sh not found at $SETUP_SH"; exit 2; }

# ── Extract the REAL "[3] BOOTSTRAP UV" block ─────────────────────────────────────
# Anchor on the UNIQUE preceding step comment, then capture from the UV_VERSION
# extraction line (the canonical-pin lookup) through the matching if/elif/else/fi —
# both are needed together since $UV_VERSION is now computed once, outside the if,
# and referenced by every branch (single-canonical-source refactor,
# infra_satellite_ao_dispatch_batch9_2026_08_09.md item 1).
BLOCK=$(awk '
  /^# ── \[3\] BOOTSTRAP UV/ { seen_marker = 1; next }
  seen_marker && /^UV_VERSION=/ { c = 1 }
  c { print }
  c && $0 ~ /^fi$/ { exit }
' "$SETUP_SH")
[ -n "$BLOCK" ] || { echo "FATAL: could not extract the bootstrap-uv block from setup.sh"; exit 2; }

# Structural anchor: the extracted block must carry the canonical-pin extraction ahead
# of the astral-installer branch ahead of the pip fallback — so a future edit that
# removes/reorders the fix fails here even if the fixtures below don't.
case "$BLOCK" in
  *"UV_VERSION="*"resolve-canonical-versions.py"*"grep -q \"\$UV_VERSION\""*"command -v curl"*'astral.sh/uv/${UV_VERSION}/install.sh'*"UV_UNMANAGED_INSTALL"*"hash -r"*'pip install "uv==$UV_VERSION"'*"--quiet"*)
    pass "structural: extracted block carries the canonical-pin lookup + pinned-version check + astral installer + pip-last-resort, in order" ;;
  *)
    fail "structural: extracted block missing an expected contract element"; echo "--- block ---"; echo "$BLOCK" ;;
esac

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# Stub canonical-versions source ($UV_VERSION is now read from here, not a setup.sh
# literal) — exercises the real grep-extraction mechanism, offline, against a fake
# WORKSPACE_ROOT rather than the real workspace.
FAKE_WS="$WORK/fake-workspace"
mkdir -p "$FAKE_WS/unified-trading-pm/scripts/workspace"
cat >"$FAKE_WS/unified-trading-pm/scripts/workspace/resolve-canonical-versions.py" <<'EOF'
UV_VERSION = "0.10.8"
EOF

# Minimal log_* stubs — setup.sh defines these as trivial one-liners; the block itself
# is what's under test, not the logging cosmetics.
LOG_STUBS='
log_ok()   { echo "[OK] $1"; }
log_skip() { echo "[SKIP] $1"; }
log_warn() { echo "[WARN] $1"; }
log_fail() { echo "[FAIL] $1"; }
'

# Runs the EXTRACTED block in a subshell with IN_CI/CHECK_ONLY/PYTHON_CMD/HOME/PATH set
# by the caller, printing a sentinel AFTER the block so we can distinguish "ran to
# completion" (exit 0) from an early `set -e`-style abort.
run_block() {
  (
    set -e  # mirrors setup.sh's own `set -e` (line 80) — the exact mechanism the bug fired through
    eval "$LOG_STUBS"
    eval "$BLOCK"
    echo "SUBSHELL_COMPLETED"
  )
}

echo "── Case 1: uv present but WRONG version (drifted) — must realign via the astral installer, not pip ──"
home1="$WORK/home1"
bindir1="$home1/.local/bin"
fakebin1="$WORK/fakebin1"
mkdir -p "$bindir1" "$fakebin1"

# The "drifted" uv already living at the pinned real-world location (~/.local/bin/uv).
cat >"$bindir1/uv" <<'EOF'
#!/usr/bin/env bash
echo "uv 0.11.21 (fake, drifted)"
EOF
chmod +x "$bindir1/uv"

# A fake `curl` that — instead of hitting the real network — prints a tiny installer
# script to stdout. The real block pipes this straight into `sh`, which is exactly
# what the genuine astral one-liner does; only the network fetch is stubbed.
cat >"$fakebin1/curl" <<'EOF'
#!/usr/bin/env bash
cat <<'INSTALLER'
mkdir -p "$UV_UNMANAGED_INSTALL"
cat > "$UV_UNMANAGED_INSTALL/uv" <<'REALUV'
#!/usr/bin/env bash
echo "uv 0.10.8 (fake, realigned)"
REALUV
chmod +x "$UV_UNMANAGED_INSTALL/uv"
INSTALLER
EOF
chmod +x "$fakebin1/curl"

out1=$(HOME="$home1" PATH="$fakebin1:$bindir1:$PATH" WORKSPACE_ROOT="$FAKE_WS" IN_CI=false CHECK_ONLY=false PYTHON_CMD=python3 run_block)
rc1=$?
if [ "$rc1" -eq 0 ] && printf '%s\n' "$out1" | grep -q "SUBSHELL_COMPLETED"; then
  pass "case1: block completed (exit 0) on a drifted-version uv"
else
  fail "case1: block did not complete cleanly on a drifted-version uv (rc=$rc1)"; echo "--- output ---"; printf '%s\n' "$out1"
fi
if printf '%s\n' "$out1" | grep -q "Installed/realigned uv 0.10.8 (pinned, astral installer)"; then
  pass "case1: realigned via the astral installer branch, not pip"
else
  fail "case1: did not take the astral-installer branch"; echo "--- output ---"; printf '%s\n' "$out1"
fi
new_version=$("$bindir1/uv" --version)
if [ "$new_version" = "uv 0.10.8 (fake, realigned)" ]; then
  pass "case1: the on-disk uv binary at \$HOME/.local/bin/uv is now the realigned 0.10.8 stub"
else
  fail "case1: the on-disk uv binary was not realigned — got: $new_version"
fi

echo "── Case 2: uv already pinned at 0.10.8 — must skip, no curl/pip invoked (no regression) ──"
home2="$WORK/home2"
bindir2="$home2/.local/bin"
mkdir -p "$bindir2"
cat >"$bindir2/uv" <<'EOF'
#!/usr/bin/env bash
echo "uv 0.10.8"
EOF
chmod +x "$bindir2/uv"
# No fake curl on PATH for this case — if the block wrongly fell through to the
# astral branch, `command -v curl` would resolve the REAL system curl and this test
# would (harmlessly) attempt a real network call, which is itself the regression this
# case exists to catch, so we assert on the skip message instead of relying on that.
out2=$(HOME="$home2" PATH="$bindir2:$PATH" WORKSPACE_ROOT="$FAKE_WS" IN_CI=false CHECK_ONLY=false PYTHON_CMD=python3 run_block)
if printf '%s\n' "$out2" | grep -q "uv 0.10.8 already installed (pinned)"; then
  pass "case2: already-pinned uv is skipped, no reinstall attempted"
else
  fail "case2: already-pinned uv was not skipped as expected"; echo "--- output ---"; printf '%s\n' "$out2"
fi

echo
echo "── result: ${PASS} passed / ${FAIL} failed ──"
[ "$FAIL" -eq 0 ] || exit 1
