#!/usr/bin/env bash
# slot-git-status-report.sh — per-slot git-status snapshot reporter.
#
# Walks .tabs/<N>/<repo>/, builds a JSON snapshot of each repo's state
# (clean/dirty/ahead/behind/diverged + oldest dirty mtime + ahead/behind counts),
# and POSTs to the orchestrator's /api/slots/<N>/git-status endpoint.
#
# Cross-platform: macOS (bash 3.2, stat -f %m) + Linux (bash 5+, stat -c %Y).
# Uses python3 for JSON serialisation to avoid shell-quoting pain.
#
# Usage:
#   slot-git-status-report.sh [--workspace PATH] [--orch-url URL] [--token-file PATH]
#                             [--integration-branch BR] [--quiet]
#
# Env-var defaults:
#   WORKSPACE_PATH       — auto-detect: climb from cwd to .tabs/ parent, else $HOME/Code/unified-trading-system-repos
#   ORCH_URL             — https://api.agent-orchestrator.odum-research.com
#   ORCH_TOKEN_FILE      — $HOME/.orch_token (operator) or .tabs/<N>/.orch_token (per-slot)
#   INTEGRATION_BRANCH   — live-defi-rollout
#
# Cron install (5-min cadence, after slot-cron-ff-pull's :05 boundary):
#   2,7,12,17,22,27,32,37,42,47,52,57 * * * * \
#     bash unified-trading-pm/scripts/dev/slot-git-status-report.sh --quiet \
#       >> /tmp/slot-git-status-report.log 2>&1

set -uo pipefail   # NOT set -e: we want to keep walking even if one repo errors.

INTEGRATION_BRANCH="${INTEGRATION_BRANCH:-live-defi-rollout}"
ORCH_URL="${ORCH_URL:-https://api.agent-orchestrator.odum-research.com}"
WORKSPACE_PATH="${WORKSPACE_PATH:-}"
TOKEN_FILE="${ORCH_TOKEN_FILE:-}"
QUIET=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --workspace)          WORKSPACE_PATH="$2"; shift 2;;
        --orch-url)           ORCH_URL="$2"; shift 2;;
        --token-file)         TOKEN_FILE="$2"; shift 2;;
        --integration-branch) INTEGRATION_BRANCH="$2"; shift 2;;
        --quiet)              QUIET=1; shift;;
        -h|--help)
            sed -n '2,32p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
            exit 0;;
        *) echo "Unknown arg: $1" >&2; exit 2;;
    esac
done

log()       { printf '[%s] %s\n' "$(date -u +%H:%M:%SZ)" "$*"; }
log_quiet() { [[ "${QUIET}" -eq 0 ]] && log "$@" || true; }

# Resolve workspace.
if [[ -z "${WORKSPACE_PATH}" ]]; then
    cwd="$(pwd)"
    while [[ "$(basename "${cwd}")" != "unified-trading-system-repos" && "${cwd}" != "/" ]]; do
        cwd="$(dirname "${cwd}")"
    done
    if [[ "${cwd}" != "/" ]]; then
        WORKSPACE_PATH="${cwd}"
    elif [[ -d "${HOME}/Code/unified-trading-system-repos/.tabs" ]]; then
        WORKSPACE_PATH="${HOME}/Code/unified-trading-system-repos"
    elif [[ -d "/home/ubuntu/unified-trading-system-repos/.tabs" ]]; then
        WORKSPACE_PATH="/home/ubuntu/unified-trading-system-repos"
    else
        log "[err] could not auto-detect WORKSPACE_PATH; pass --workspace"
        exit 1
    fi
fi

TABS_DIR="${WORKSPACE_PATH}/.tabs"
if [[ ! -d "${TABS_DIR}" ]]; then
    log "[err] no .tabs/ dir under ${WORKSPACE_PATH}"
    exit 1
fi

# Cross-platform helpers.
HOST_OS="$(uname -s)"
HOSTNAME_SHORT="$(hostname -s 2>/dev/null || hostname 2>/dev/null || echo unknown)"

stat_mtime_epoch() {
    # Print mtime as epoch seconds for $1 ("" on failure).
    if [[ "${HOST_OS}" == "Darwin" ]]; then
        stat -f %m "$1" 2>/dev/null || true
    else
        stat -c %Y "$1" 2>/dev/null || true
    fi
}

epoch_to_iso() {
    # Epoch → ISO-8601 UTC ("" if epoch is empty).
    [[ -z "$1" ]] && return 0
    if [[ "${HOST_OS}" == "Darwin" ]]; then
        date -u -r "$1" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || true
    else
        date -u -d "@$1" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || true
    fi
}

NOW_ISO="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Classify one repo worktree → emits TAB-separated row to stdout:
#   name<TAB>branch<TAB>state<TAB>dirty_files<TAB>ahead<TAB>behind<TAB>local_sha<TAB>int_branch<TAB>dirty_oldest_iso
classify_repo() {
    local repo_dir="$1"
    local repo_name branch local_sha int_branch state dirty_files ahead behind dirty_oldest_iso
    repo_name=$(basename "${repo_dir}")
    int_branch="${INTEGRATION_BRANCH}"

    pushd "${repo_dir}" >/dev/null 2>&1 || return 0
    branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "DETACHED")
    local_sha=$(git rev-parse --short=12 HEAD 2>/dev/null || echo "")

    if [[ "${branch}" == "DETACHED" || "${branch}" == "HEAD" || -z "${local_sha}" ]]; then
        printf '%s\t%s\tdetached\t0\t0\t0\t%s\t%s\t\n' "${repo_name}" "${branch:-DETACHED}" "${local_sha}" "${int_branch}"
        popd >/dev/null
        return 0
    fi

    local porcelain
    porcelain=$(git status --porcelain 2>/dev/null || echo "")
    dirty_files=0
    dirty_oldest_iso=""
    if [[ -n "${porcelain}" ]]; then
        dirty_files=$(printf '%s\n' "${porcelain}" | wc -l | tr -d ' ')
        # Find oldest mtime among dirty files (relative paths from porcelain col 4+).
        local oldest_epoch="" line file ep
        while IFS= read -r line; do
            [[ -z "${line}" ]] && continue
            file="${line:3}"
            file="${file%% -> *}"
            [[ -f "${file}" || -d "${file}" ]] || continue
            ep=$(stat_mtime_epoch "${file}")
            [[ -z "${ep}" ]] && continue
            if [[ -z "${oldest_epoch}" || "${ep}" -lt "${oldest_epoch}" ]]; then
                oldest_epoch="${ep}"
            fi
        done <<< "${porcelain}"
        dirty_oldest_iso=$(epoch_to_iso "${oldest_epoch}")
    fi

    ahead=0
    behind=0
    local remote_ref="origin/${int_branch}"
    if git rev-parse --verify --quiet "${remote_ref}" >/dev/null 2>&1; then
        ahead=$(git rev-list --count "${remote_ref}..HEAD" 2>/dev/null || echo 0)
        behind=$(git rev-list --count "HEAD..${remote_ref}" 2>/dev/null || echo 0)
    else
        # Try to infer integration branch when default doesn't exist on this repo (e.g. agent-orchestrator → main).
        if git rev-parse --verify --quiet "origin/main" >/dev/null 2>&1; then
            int_branch="main"
            remote_ref="origin/main"
            ahead=$(git rev-list --count "${remote_ref}..HEAD" 2>/dev/null || echo 0)
            behind=$(git rev-list --count "HEAD..${remote_ref}" 2>/dev/null || echo 0)
        else
            state="no-remote-ref"
            printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
                "${repo_name}" "${branch}" "${state}" "${dirty_files}" "${ahead}" "${behind}" "${local_sha}" "${int_branch}" "${dirty_oldest_iso}"
            popd >/dev/null
            return 0
        fi
    fi

    # State precedence: dirty > ahead+diverged > ahead > diverged > behind > clean.
    if [[ "${dirty_files}" -gt 0 ]]; then
        state="dirty"
    elif [[ "${ahead}" -gt 0 && "${behind}" -gt 0 ]]; then
        state="diverged"
    elif [[ "${ahead}" -gt 0 ]]; then
        state="ahead"
    elif [[ "${behind}" -gt 0 ]]; then
        state="behind"
    else
        state="clean"
    fi

    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
        "${repo_name}" "${branch}" "${state}" "${dirty_files}" "${ahead}" "${behind}" "${local_sha}" "${int_branch}" "${dirty_oldest_iso}"
    popd >/dev/null
}

# Resolve token for a slot. Per-slot token preferred; fall back to global token.
resolve_token_for_slot() {
    local slot_id="$1"
    local per_slot="${TABS_DIR}/${slot_id}/.orch_token"
    if [[ -n "${TOKEN_FILE}" && -r "${TOKEN_FILE}" ]]; then
        cat "${TOKEN_FILE}"
        return 0
    fi
    if [[ -r "${per_slot}" ]]; then
        cat "${per_slot}"
        return 0
    fi
    if [[ -r "${HOME}/.orch_token" ]]; then
        cat "${HOME}/.orch_token"
        return 0
    fi
    if [[ -r "/tmp/orch_token" ]]; then
        cat "/tmp/orch_token"
        return 0
    fi
    return 1
}

# Build + POST one slot's snapshot. Reads TSV rows passed as a single string arg
# (NOT stdin — we previously used a heredoc which clobbered python's stdin with
# its own source, hence "0 repos" for non-empty slots).
post_snapshot() {
    local slot_id="$1"
    local rows_tsv="$2"
    local token
    token=$(resolve_token_for_slot "${slot_id}") || {
        log "[skip:no-token] slot ${slot_id} — no readable token"
        return 0
    }

    local payload
    payload=$(printf '%s' "${rows_tsv}" | python3 -c '
import json, sys
slot_id = int(sys.argv[1])
host = sys.argv[2]
reported_at = sys.argv[3]
repos = []
for line in sys.stdin:
    line = line.rstrip("\n")
    if not line:
        continue
    parts = line.split("\t")
    if len(parts) < 9:
        parts += [""] * (9 - len(parts))
    name, branch, state, dirty_files, ahead, behind, local_sha, int_branch, dirty_oldest = parts[:9]
    repo = {
        "name": name,
        "branch": branch,
        "state": state,
        "dirty_files": int(dirty_files or 0),
        "ahead": int(ahead or 0),
        "behind": int(behind or 0),
        "local_sha": local_sha,
        "integration_branch": int_branch,
    }
    if dirty_oldest:
        repo["dirty_oldest_mtime"] = dirty_oldest
    repos.append(repo)
print(json.dumps({"reported_at": reported_at, "host": host, "repos": repos}))
' "${slot_id}" "${HOSTNAME_SHORT}" "${NOW_ISO}")
    if [[ -z "${payload}" ]]; then
        log "[skip:empty-payload] slot ${slot_id}"
        return 0
    fi

    local http_status
    http_status=$(curl -sS -o /tmp/.git-status-resp.$$ -w '%{http_code}' \
        -X POST "${ORCH_URL}/api/slots/${slot_id}/git-status" \
        -H "Authorization: Bearer ${token}" \
        -H "Content-Type: application/json" \
        -d "${payload}" 2>/dev/null || echo "000")
    if [[ "${http_status}" == "200" ]]; then
        local repo_count
        repo_count=$(printf '%s\n' "${payload}" | python3 -c 'import json,sys; print(len(json.load(sys.stdin).get("repos",[])))' 2>/dev/null || echo "?")
        log_quiet "[ok] slot ${slot_id} — ${repo_count} repos reported (host=${HOSTNAME_SHORT})"
    else
        log "[fail] slot ${slot_id} — HTTP ${http_status}; body: $(head -c 200 /tmp/.git-status-resp.$$ 2>/dev/null || echo '')"
    fi
    rm -f /tmp/.git-status-resp.$$
}

# Walk each slot.
for slot_dir in "${TABS_DIR}"/*/; do
    [[ -d "${slot_dir}" ]] || continue
    slot_id_str=$(basename "${slot_dir}")
    [[ "${slot_id_str}" =~ ^[0-9]+$ ]] || continue

    rows_tsv=""
    for repo_dir in "${slot_dir}"*/; do
        [[ -d "${repo_dir}" ]] || continue
        [[ -d "${repo_dir}.git" || -f "${repo_dir}.git" ]] || continue
        rows_tsv+="$(classify_repo "${repo_dir}")"$'\n'
    done
    post_snapshot "${slot_id_str}" "${rows_tsv}"
done

log_quiet "=== git-status sweep complete (host=${HOSTNAME_SHORT}, workspace=${WORKSPACE_PATH}) ==="
