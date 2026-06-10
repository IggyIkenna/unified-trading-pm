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

# Default HOME when invoked outside a login shell (some cron / SSM RunShellScript
# contexts don't export it) so the ${HOME}-based workspace + token-file lookups
# below don't trip `set -u` with "HOME: unbound variable".
if [[ -z "${HOME:-}" ]]; then
    # `cd ~` expands via the passwd DB (getpwuid), independent of $HOME, and is a
    # bash builtin — portable across Linux (VMs) AND macOS (operator laptops),
    # unlike `getent` which doesn't exist on macOS. Subshell keeps cwd unchanged.
    HOME="$(cd ~ 2>/dev/null && pwd)" || HOME=""
    HOME="${HOME:-/home/$(id -un 2>/dev/null || echo ubuntu)}"
    export HOME
fi

INTEGRATION_BRANCH="${INTEGRATION_BRANCH:-live-defi-rollout}"
ORCH_URL="${ORCH_URL:-https://api.agent-orchestrator.odum-research.com}"
WORKSPACE_PATH="${WORKSPACE_PATH:-}"
TOKEN_FILE="${ORCH_TOKEN_FILE:-}"
SLOTS_FILTER="${SLOTS_FILTER:-}"   # comma-separated slot ids; empty = all numeric slots under .tabs/
QUIET=0

# FF-pull starvation watchdog (Item 5b). The reporter is the detector/alerter;
# slot-cron-ff-pull.sh stays the actor. Toggle off with FF_STARVE_WATCHDOG=0.
FF_STARVE_WATCHDOG="${FF_STARVE_WATCHDOG:-1}"
FF_STARVE_COMMIT_THRESHOLD="${FF_STARVE_COMMIT_THRESHOLD:-25}"
FF_STARVE_AGE_HOURS="${FF_STARVE_AGE_HOURS:-6}"
STARVE_DETECTOR="$(dirname "${BASH_SOURCE[0]}")/ff-starvation-detect.sh"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --workspace)          WORKSPACE_PATH="$2"; shift 2;;
        --orch-url)           ORCH_URL="$2"; shift 2;;
        --token-file)         TOKEN_FILE="$2"; shift 2;;
        --integration-branch) INTEGRATION_BRANCH="$2"; shift 2;;
        --slots)              SLOTS_FILTER="$2"; shift 2;;
        --quiet)              QUIET=1; shift;;
        -h|--help)
            sed -n '2,32p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
            exit 0;;
        *) echo "Unknown arg: $1" >&2; exit 2;;
    esac
done

slot_in_filter() {
    # Returns 0 if --slots is empty OR if slot_id is in the comma-separated list.
    local sid="$1"
    [[ -z "${SLOTS_FILTER}" ]] && return 0
    case ",${SLOTS_FILTER}," in
        *",${sid},"*) return 0 ;;
        *) return 1 ;;
    esac
}

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

# Cron-liveness attestation (fleet_git_health_orchestrator_2026_06_10.md Phase 3).
# slot-cron-ff-pull.sh writes a host-global result file each sweep; read it here so
# every slot's POST carries ff_pull_last_run/ff_pull_last_result → the orchestrator
# flags a dead FF-pull cron (ff_cron_stale) as a first-class fleet state. Absent /
# unreadable file → empty strings (the server treats absence as honest-unknown, the
# payload stays backward-compatible).
FF_RESULT_FILE="${SLOT_FF_PULL_RESULT_FILE:-${TMPDIR:-/tmp}/slot-cron-ff-pull.result.json}"
FF_LAST_RUN=""
FF_LAST_RESULT=""
if [[ -f "${FF_RESULT_FILE}" ]]; then
    FF_LAST_RUN=$(python3 -c 'import json,sys
try:
    d = json.load(open(sys.argv[1]))
    print(d.get("ff_pull_last_run", ""))
except Exception:
    print("")' "${FF_RESULT_FILE}" 2>/dev/null || echo "")
    FF_LAST_RESULT=$(python3 -c 'import json,sys
try:
    d = json.load(open(sys.argv[1]))
    print(d.get("ff_pull_last_result", ""))
except Exception:
    print("")' "${FF_RESULT_FILE}" 2>/dev/null || echo "")
fi

# Classify one repo worktree → emits TAB-separated row to stdout:
#   name<TAB>branch<TAB>state<TAB>dirty_files<TAB>ahead<TAB>behind<TAB>local_sha<TAB>int_branch<TAB>dirty_oldest_iso<TAB>unpushed_plans
#
# unpushed_plans: pipe-separated list of plan file basenames (plans/active/*.md or
#   plans/active/issues/*.md) that are dirty or untracked in a unified-trading-pm worktree.
#   Empty string for all other repos.
classify_repo() {
    local repo_dir="$1"
    local repo_name branch local_sha int_branch state dirty_files ahead behind dirty_oldest_iso unpushed_plans
    repo_name=$(basename "${repo_dir}")
    int_branch="${INTEGRATION_BRANCH}"

    pushd "${repo_dir}" >/dev/null 2>&1 || return 0
    branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "DETACHED")
    local_sha=$(git rev-parse --short=12 HEAD 2>/dev/null || echo "")

    if [[ "${branch}" == "DETACHED" || "${branch}" == "HEAD" || -z "${local_sha}" ]]; then
        printf '%s\t%s\tdetached\t0\t0\t0\t%s\t%s\t\t\n' "${repo_name}" "${branch:-DETACHED}" "${local_sha}" "${int_branch}"
        popd >/dev/null
        return 0
    fi

    local porcelain
    porcelain=$(git status --porcelain 2>/dev/null || echo "")
    dirty_files=0
    dirty_oldest_iso=""
    unpushed_plans=""
    if [[ -n "${porcelain}" ]]; then
        dirty_files=$(printf '%s\n' "${porcelain}" | wc -l | tr -d ' ')
        # Find oldest mtime among dirty files; also collect unpushed plan files for
        # unified-trading-pm repos (paths matching plans/active/*.md or plans/active/issues/*.md).
        local oldest_epoch="" line file ep plan_list=()
        while IFS= read -r line; do
            [[ -z "${line}" ]] && continue
            file="${line:3}"
            file="${file%% -> *}"
            # Detect plan files (dirty or untracked) in unified-trading-pm worktrees.
            if [[ "${file}" == plans/active/*.md || "${file}" == plans/active/issues/*.md ]]; then
                plan_list+=("$(basename "${file}")")
            fi
            [[ -f "${file}" || -d "${file}" ]] || continue
            ep=$(stat_mtime_epoch "${file}")
            [[ -z "${ep}" ]] && continue
            if [[ -z "${oldest_epoch}" || "${ep}" -lt "${oldest_epoch}" ]]; then
                oldest_epoch="${ep}"
            fi
        done <<< "${porcelain}"
        dirty_oldest_iso=$(epoch_to_iso "${oldest_epoch}")
        # Build pipe-separated list of unpushed plan basenames.
        if [[ "${#plan_list[@]}" -gt 0 ]]; then
            unpushed_plans="$(printf '%s|' "${plan_list[@]}")"
            unpushed_plans="${unpushed_plans%|}"   # strip trailing pipe
        fi
    fi

    ahead=0
    behind=0
    local remote_ref="origin/${int_branch}"
    if git rev-parse --verify --quiet "${remote_ref}" >/dev/null 2>&1; then
        ahead=$(git rev-list --count "${remote_ref}..HEAD" 2>/dev/null || echo 0)
        behind=$(git rev-list --count "HEAD..${remote_ref}" 2>/dev/null || echo 0)
    else
        # Last-resort fallback ONLY when this repo has no live-defi-rollout ref at all
        # (e.g. a main-only repo). NB: agent-orchestrator is NOT such a repo — it
        # integrates via live-defi-rollout like every repo (server ships from LDR;
        # main is only the dashboard-SPA deploy + CI gate), so this branch never fires
        # for it. (Corrected 2026-06-01 — the old "agent-orchestrator → main" belief
        # was the cause of false-diverged slot reports; cron override removed 2026-05-24.)
        if git rev-parse --verify --quiet "origin/main" >/dev/null 2>&1; then
            int_branch="main"
            remote_ref="origin/main"
            ahead=$(git rev-list --count "${remote_ref}..HEAD" 2>/dev/null || echo 0)
            behind=$(git rev-list --count "HEAD..${remote_ref}" 2>/dev/null || echo 0)
        else
            state="no-remote-ref"
            printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
                "${repo_name}" "${branch}" "${state}" "${dirty_files}" "${ahead}" "${behind}" "${local_sha}" "${int_branch}" "${dirty_oldest_iso}" "${unpushed_plans}"
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

    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
        "${repo_name}" "${branch}" "${state}" "${dirty_files}" "${ahead}" "${behind}" "${local_sha}" "${int_branch}" "${dirty_oldest_iso}" "${unpushed_plans}"
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
    if len(parts) < 10:
        parts += [""] * (10 - len(parts))
    name, branch, state, dirty_files, ahead, behind, local_sha, int_branch, dirty_oldest, unpushed_raw = parts[:10]
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
    if unpushed_raw:
        repo["unpushed_plans"] = [p for p in unpushed_raw.split("|") if p]
    repos.append(repo)
ff_last_run = sys.argv[4] if len(sys.argv) > 4 else ""
ff_last_result = sys.argv[5] if len(sys.argv) > 5 else ""
out = {"reported_at": reported_at, "host": host, "repos": repos}
if ff_last_run:
    out["ff_pull_last_run"] = ff_last_run
if ff_last_result:
    out["ff_pull_last_result"] = ff_last_result
print(json.dumps(out))
' "${slot_id}" "${HOSTNAME_SHORT}" "${NOW_ISO}" "${FF_LAST_RUN}" "${FF_LAST_RESULT}")
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
        # Always log the success heartbeat (symmetric with [fail] below). The cron runs
        # --quiet, and verify-slot-host-symmetry.sh greps the log for [ok] — using
        # log_quiet here suppressed it under --quiet → the symmetry check could never pass.
        log "[ok] slot ${slot_id} — ${repo_count} repos reported (host=${HOSTNAME_SHORT})"
    else
        log "[fail] slot ${slot_id} — HTTP ${http_status}; body: $(head -c 200 /tmp/.git-status-resp.$$ 2>/dev/null || echo '')"
    fi
    rm -f /tmp/.git-status-resp.$$
}

# FF-pull starvation watchdog. For each repo under a slot, run the detector
# (ff-starvation-detect.sh); if STARVED, POST a ONE-PER-(slot,repo) ping to the
# slot's message inbox the same way post_snapshot posts git-status. De-duplicated
# via a local marker dir so we ping once per starvation episode (the marker clears
# the moment the repo is no longer starved → re-pings on a fresh episode).
STARVE_STATE_DIR="${TABS_DIR}/.ff-starve-state"

post_starve_ping() {
    local slot_id="$1" repo_name="$2" payload="$3" token="$4"
    # Reuse the message endpoint (from_role must be one of main/review/operator;
    # the watchdog speaks for the orchestrator → "main"). Same curl+token shape
    # as post_snapshot.
    local body http_status
    body=$(printf '%s' "${payload}" | python3 -c '
import json, sys
print(json.dumps({"text": sys.stdin.read(), "from_role": "main"}))
')
    [[ -n "${body}" ]] || return 0
    http_status=$(curl -sS -o /dev/null -w '%{http_code}' \
        -X POST "${ORCH_URL}/api/slots/${slot_id}/message" \
        -H "Authorization: Bearer ${token}" \
        -H "Content-Type: application/json" \
        -d "${body}" 2>/dev/null || echo "000")
    if [[ "${http_status}" == "200" ]]; then
        log "[starve-ping] slot ${slot_id}/${repo_name} — FF-pull starvation signalled"
        return 0
    fi
    log "[starve-ping-fail] slot ${slot_id}/${repo_name} — HTTP ${http_status}"
    return 1
}

check_starvation_for_slot() {
    local slot_id="$1" slot_dir="$2"
    [[ "${FF_STARVE_WATCHDOG}" -eq 1 ]] || return 0
    [[ -x "${STARVE_DETECTOR}" || -f "${STARVE_DETECTOR}" ]] || return 0
    local token
    token=$(resolve_token_for_slot "${slot_id}") || return 0
    mkdir -p "${STARVE_STATE_DIR}" 2>/dev/null || true

    local repo_dir repo_name marker payload
    for repo_dir in "${slot_dir}"*/; do
        [[ -d "${repo_dir}" ]] || continue
        [[ -d "${repo_dir}.git" || -f "${repo_dir}.git" ]] || continue
        repo_name=$(basename "${repo_dir}")
        marker="${STARVE_STATE_DIR}/slot-${slot_id}__${repo_name}.starved"
        payload=$(FF_STARVE_COMMIT_THRESHOLD="${FF_STARVE_COMMIT_THRESHOLD}" \
                  FF_STARVE_AGE_HOURS="${FF_STARVE_AGE_HOURS}" \
                  INTEGRATION_BRANCH="${INTEGRATION_BRANCH}" \
                  bash "${STARVE_DETECTOR}" "${repo_dir}" --slot "${slot_id}" 2>/dev/null || echo "")
        if [[ -n "${payload}" ]]; then
            # STARVED. Ping once per episode (skip if already marked).
            if [[ ! -f "${marker}" ]]; then
                if post_starve_ping "${slot_id}" "${repo_name}" "${payload}" "${token}"; then
                    : > "${marker}" 2>/dev/null || true
                fi
            else
                log_quiet "[starve-dup] slot ${slot_id}/${repo_name} — already signalled this episode"
            fi
        else
            # Not starved → clear any prior marker (next episode re-pings).
            [[ -f "${marker}" ]] && rm -f "${marker}" 2>/dev/null || true
        fi
    done
}

# Walk each slot.
for slot_dir in "${TABS_DIR}"/*/; do
    [[ -d "${slot_dir}" ]] || continue
    slot_id_str=$(basename "${slot_dir}")
    [[ "${slot_id_str}" =~ ^[0-9]+$ ]] || continue
    slot_in_filter "${slot_id_str}" || { log_quiet "[skip:not-in-filter] slot ${slot_id_str}"; continue; }

    rows_tsv=""
    for repo_dir in "${slot_dir}"*/; do
        [[ -d "${repo_dir}" ]] || continue
        [[ -d "${repo_dir}.git" || -f "${repo_dir}.git" ]] || continue
        rows_tsv+="$(classify_repo "${repo_dir}")"$'\n'
    done
    post_snapshot "${slot_id_str}" "${rows_tsv}"
    check_starvation_for_slot "${slot_id_str}" "${slot_dir}"
done

log_quiet "=== git-status sweep complete (host=${HOSTNAME_SHORT}, workspace=${WORKSPACE_PATH}) ==="
