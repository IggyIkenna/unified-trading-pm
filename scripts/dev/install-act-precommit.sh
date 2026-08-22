#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# install-act-precommit.sh — opt-in installer for the act-preflight pre-push git hook.
#
# Phase 2 P1 of deployment_and_qg_strategy_implementation_2026_05_13.md.
#
# Installs a per-repo `.git/hooks/pre-push` that refuses the push if
# `act-preflight.sh --repo <name>` fails. Opt-in only — NOT mandatory.
#
# Usage:
#   bash unified-trading-pm/scripts/dev/install-act-precommit.sh --repo <name>
#   bash unified-trading-pm/scripts/dev/install-act-precommit.sh --repo <name> --uninstall
#
# Status: Opt-in. The hook is NEVER installed without an explicit --repo invocation.
# Owner: workspace-platform (script ownership; the developer who runs --install owns their own hook).
# Cadence: one-shot per repo (developer opts in).
# Verifier: cat <repo>/.git/hooks/pre-push | grep act-preflight
# Last executed: n/a — opt-in installer.

set -euo pipefail

REPO=""
UNINSTALL=false
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && cd .. && pwd)}"

usage() {
    cat <<EOF
Usage: $0 --repo <name> [--uninstall]

  --repo <name>   Service repo under \$WORKSPACE_ROOT (e.g. deployment-api)
  --uninstall     Remove the installed hook (restores .sample if present)

The installed hook:
  - Runs act-preflight.sh --repo <name> on every git push
  - If act-preflight fails, push is rejected
  - Bypass with: git push --no-verify (logged to stderr)

Exit codes: 0 success / 2 arg or pre-flight error
EOF
    exit 2
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo) REPO="$2"; shift 2 ;;
        --uninstall) UNINSTALL=true; shift ;;
        --help|-h) usage ;;
        *) echo "Unknown arg: $1" >&2; usage ;;
    esac
done

if [[ -z "$REPO" ]]; then
    echo "ERROR: --repo is required" >&2
    usage
fi

REPO_DIR="$WORKSPACE_ROOT/$REPO"
if [[ ! -d "$REPO_DIR" ]]; then
    echo "ERROR: repo not found at $REPO_DIR" >&2
    exit 2
fi

# Find the actual .git directory (handles worktrees: .git is a file, not a dir)
GIT_FILE="$REPO_DIR/.git"
if [[ -f "$GIT_FILE" ]]; then
    # Worktree case: .git is `gitdir: <path>`
    GITDIR=$(sed -n 's/^gitdir: //p' "$GIT_FILE")
    HOOK_DIR="$GITDIR/hooks"
elif [[ -d "$GIT_FILE" ]]; then
    HOOK_DIR="$GIT_FILE/hooks"
else
    echo "ERROR: $REPO_DIR is not a git repo (no .git)" >&2
    exit 2
fi

mkdir -p "$HOOK_DIR"
HOOK_FILE="$HOOK_DIR/pre-push"

if [[ "$UNINSTALL" == "true" ]]; then
    if [[ -f "$HOOK_FILE" ]] && grep -q "act-preflight.sh" "$HOOK_FILE"; then
        rm -f "$HOOK_FILE"
        if [[ -f "$HOOK_FILE.sample.bak" ]]; then
            mv "$HOOK_FILE.sample.bak" "$HOOK_FILE.sample"
        fi
        echo "✅ Uninstalled act-preflight pre-push hook from $REPO"
    else
        echo "WARN: no act-preflight hook found at $HOOK_FILE — nothing to do"
    fi
    exit 0
fi

# Back up existing .sample if present
if [[ -f "$HOOK_FILE.sample" ]] && [[ ! -f "$HOOK_FILE.sample.bak" ]]; then
    mv "$HOOK_FILE.sample" "$HOOK_FILE.sample.bak"
fi

# Refuse to overwrite a non-act hook silently
if [[ -f "$HOOK_FILE" ]] && ! grep -q "act-preflight.sh" "$HOOK_FILE"; then
    echo "ERROR: existing $HOOK_FILE is not act-preflight; refusing to overwrite" >&2
    echo "       Move it aside manually first if you want to replace it." >&2
    exit 2
fi

cat > "$HOOK_FILE" <<'HOOK_EOF'
#!/usr/bin/env bash
# pre-push hook installed by unified-trading-pm/scripts/dev/install-act-precommit.sh.
# Runs act-preflight.sh; rejects push on failure.
# Bypass: git push --no-verify

set -euo pipefail

REPO_NAME="$(basename "$(git rev-parse --show-toplevel)")"
WORKSPACE_ROOT="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
PREFLIGHT="$WORKSPACE_ROOT/unified-trading-pm/scripts/dev/act-preflight.sh"

if [[ ! -x "$PREFLIGHT" ]]; then
    echo "WARN: act-preflight.sh not found at $PREFLIGHT — skipping pre-push gate" >&2
    exit 0
fi

echo "→ pre-push: running act-preflight for $REPO_NAME..." >&2
if ! bash "$PREFLIGHT" --repo "$REPO_NAME"; then
    echo "" >&2
    echo "❌ act-preflight FAILED — push blocked." >&2
    echo "   Bypass with: git push --no-verify" >&2
    exit 1
fi

echo "✅ act-preflight passed — proceeding with push" >&2
HOOK_EOF

chmod +x "$HOOK_FILE"
echo "✅ Installed act-preflight pre-push hook at $HOOK_FILE"
echo ""
echo "Test: cd $REPO_DIR && git push --dry-run"
echo "Uninstall: bash $0 --repo $REPO --uninstall"
