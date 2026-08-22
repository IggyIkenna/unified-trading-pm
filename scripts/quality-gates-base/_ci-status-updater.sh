#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# SSOT for ci_status manifest updates — sourced by all base-*.sh scripts.
# Provides _resolve_repo_name(), _qg_update_ci_status_failing(), _qg_update_ci_status_pass().
# Uses fcntl file locking for safe parallel execution.

# ── RESOLVE REPO NAME ────────────────────────────────────────────────────────
# Unified name resolution: SERVICE_NAME > PACKAGE_NAME > git dirname > package.json name
_resolve_repo_name() {
    if [[ -n "${SERVICE_NAME:-}" ]]; then
        echo "$SERVICE_NAME"
    elif [[ -n "${PACKAGE_NAME:-}" ]]; then
        echo "$PACKAGE_NAME"
    elif command -v git &>/dev/null; then
        basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo ""
    elif [[ -f "package.json" ]] && command -v node &>/dev/null; then
        node -e "console.log(require('./package.json').name || '')" 2>/dev/null || echo ""
    else
        echo ""
    fi
}

# ── SHARED PYTHON CI_STATUS WRITER (with fcntl locking) ─────────────────────
# Args: $1 = manifest path, $2 = repo name, $3 = target status (FAILING or LOCAL_PASS)
_qg_write_ci_status() {
    local manifest="$1" repo_name="$2" target_status="$3"
    [[ -z "$manifest" || -z "$repo_name" ]] && return 0
    [[ ! -f "$manifest" ]] && return 0
    command -v python3 &>/dev/null || return 0

    MANIFEST_PATH="$manifest" REPO_NAME="$repo_name" TARGET_STATUS="$target_status" python3 -c '
import json, os, fcntl, signal
p = os.environ.get("MANIFEST_PATH")
r = os.environ.get("REPO_NAME")
s = os.environ.get("TARGET_STATUS")
if not p or not r or not s: exit(0)
lock_path = os.path.join(os.path.dirname(p), ".workspace-manifest.lock")
def _lock_timeout(signum, frame):
    raise TimeoutError("manifest lock held >5s — stale lock?")
signal.signal(signal.SIGALRM, _lock_timeout)
signal.alarm(5)
try:
    with open(lock_path, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        signal.alarm(0)
        with open(p) as f: m = json.load(f)
        repos = m.get("repositories", {})
        if r not in repos: exit(0)
        if s == "FAILING":
            repos[r]["ci_status"] = "FAILING"
            print(f"ci_status: {r} \u2192 FAILING (QG failed)")
        elif s == "LOCAL_PASS":
            current = repos[r].get("ci_status", "NOT_CONFIGURED")
            PROMOTABLE = {"NOT_CONFIGURED", "FAILING", "LOCAL_PASS", "EXEMPT"}
            if current in PROMOTABLE:
                repos[r]["ci_status"] = "LOCAL_PASS"
        with open(p, "w") as f: json.dump(m, f, indent=2); f.write("\n")
except TimeoutError as e:
    print(f"\u26a0\ufe0f  {e} \u2014 writing without lock", flush=True)
    with open(p) as f: m = json.load(f)
    repos = m.get("repositories", {})
    if r not in repos: exit(0)
    if s == "FAILING":
        repos[r]["ci_status"] = "FAILING"
        print(f"ci_status: {r} \u2192 FAILING (QG failed, no lock)")
    elif s == "LOCAL_PASS":
        current = repos[r].get("ci_status", "NOT_CONFIGURED")
        PROMOTABLE = {"NOT_CONFIGURED", "FAILING", "LOCAL_PASS", "EXEMPT"}
        if current in PROMOTABLE:
            repos[r]["ci_status"] = "LOCAL_PASS"
    with open(p, "w") as f: json.dump(m, f, indent=2); f.write("\n")
' 2>/dev/null || true
}

# ── PUBLIC API ───────────────────────────────────────────────────────────────

# ── RESOLVE WORKSPACE ROOT ────────────────────────────────────────────────────
# Services set REPO_ROOT, UIs set WORKSPACE_ROOT, fallback to git parent.
_resolve_workspace_root() {
    if [[ -n "${REPO_ROOT:-}" ]]; then
        echo "$REPO_ROOT"
    elif [[ -n "${WORKSPACE_ROOT:-}" ]]; then
        echo "$WORKSPACE_ROOT"
    elif command -v git &>/dev/null; then
        dirname "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || dirname "$(dirname "$PWD")"
    else
        dirname "$(dirname "$PWD")"
    fi
}

# Call from EXIT trap on failure (exit code != 0)
_qg_update_ci_status_failing() {
    # ci_status is owned by ONE place — CI dispatch (authoritative) + the dedicated
    # manifest-state job. Per-QG-run local writes churned the shared tracked
    # workspace-manifest.json on every agent's QG, leaving every slot worktree dirty
    # → FF-pull skip → branch drift. Local writes are gated off by default; only the
    # dedicated job sets MANIFEST_STATE_WRITER=1. See codex/06-coding-standards/quality-gates.md.
    [[ "${MANIFEST_STATE_WRITER:-0}" == "1" ]] || return 0
    local _ws; _ws="$(_resolve_workspace_root)"
    local _manifest="${_ws}/unified-trading-pm/workspace-manifest.json"
    local _name; _name="$(_resolve_repo_name)"
    _qg_write_ci_status "$_manifest" "$_name" "FAILING"
}

# Call at end of successful QG run
_qg_update_ci_status_pass() {
    [[ "${GITHUB_ACTIONS:-}" == "true" ]] && return 0  # GHA handles via dispatch
    # Gated off for per-QG-run agents (see _qg_update_ci_status_failing). Only the
    # dedicated manifest-state job (MANIFEST_STATE_WRITER=1) writes the shared json.
    [[ "${MANIFEST_STATE_WRITER:-0}" == "1" ]] || return 0
    local _ws; _ws="$(_resolve_workspace_root)"
    local _manifest="${_ws}/unified-trading-pm/workspace-manifest.json"
    local _name; _name="$(_resolve_repo_name)"
    _qg_write_ci_status "$_manifest" "$_name" "LOCAL_PASS"
}
