#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
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
# Loopback preference (git_status_reporter_stale_public_url_token_expiry_2026_07_24.md +
# orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24.md): when
# ORCH_URL is left at its default (no --orch-url flag, no ORCH_URL env var), this script
# probes LOOPBACK_ORCH_URL (default http://localhost:8765) first. If it answers
# /api/healthz, every POST in this run goes there instead — the orchestrator's own
# auth.py::_is_trusted_loopback lets a genuine same-box caller through with NO bearer
# token at all, so a rotated/expired ~/.orch_token can no longer silence this host's
# git-health view. An EXPLICIT --orch-url or ORCH_URL env var always wins (off-VM operator
# laptops keep using the public URL + token — loopback only helps a caller that is
# actually on the orchestrator box). Override the probed loopback address with
# LOOPBACK_ORCH_URL if the local port ever changes.
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
# _ORCH_URL_EXPLICIT tracks whether ORCH_URL was chosen by the caller (env var here, or
# --orch-url below) rather than left at its public-URL default — an explicit choice always
# wins over the loopback auto-probe (see header comment).
_ORCH_URL_EXPLICIT=0
[[ -n "${ORCH_URL:-}" ]] && _ORCH_URL_EXPLICIT=1
ORCH_URL="${ORCH_URL:-https://api.agent-orchestrator.odum-research.com}"
LOOPBACK_ORCH_URL="${LOOPBACK_ORCH_URL:-http://localhost:8765}"
IS_LOOPBACK=0
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

# Stash-pile regrowth watchdog (stash_pile_workspace_cleanup_2026_06_03.md Phase 5).
# Same detector/alerter split as the starvation watchdog above: this reporter only
# WARNS, it never touches `git stash` (no drop, no apply, no clear — that stays the
# operator-run audit-stash-pile.sh runbook). Toggle off with STASH_PILE_WATCHDOG=0.
STASH_PILE_WATCHDOG="${STASH_PILE_WATCHDOG:-1}"
STASH_WARN_COUNT="${STASH_WARN_COUNT:-15}"
STASH_WARN_AGE_DAYS="${STASH_WARN_AGE_DAYS:-14}"
STASH_DETECTOR="$(dirname "${BASH_SOURCE[0]}")/stash-pile-detect.sh"

# Token-near-expiry early warning
# (git_status_reporter_stale_public_url_token_expiry_2026_07_24.md option (a) —
# the reporter already resolves the bearer token to build the Authorization
# header; this decodes that SAME token's `exp` claim and warns before it lapses
# instead of after, since a lapsed token silences this whole host's git-health
# view while looking like a frozen-but-fine dashboard. Toggle off with
# TOKEN_EXPIRY_WATCHDOG=0. Does NOT raise the TTL — see the source doc: that just
# delays and worsens the eventual outage.
TOKEN_EXPIRY_WATCHDOG="${TOKEN_EXPIRY_WATCHDOG:-1}"
TOKEN_EXPIRY_WARN_DAYS="${TOKEN_EXPIRY_WARN_DAYS:-3}"
TOKEN_EXPIRY_STATE_DIR="${TOKEN_EXPIRY_STATE_DIR:-}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --workspace)          WORKSPACE_PATH="$2"; shift 2;;
        --orch-url)           ORCH_URL="$2"; _ORCH_URL_EXPLICIT=1; shift 2;;
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

# Loopback auto-probe (skipped entirely when the caller explicitly chose a URL — see
# header comment + _ORCH_URL_EXPLICIT above). Short timeouts so an off-VM host where
# :8765 is unreachable/firewalled doesn't stall the cron tick.
if [[ "${_ORCH_URL_EXPLICIT}" -eq 0 ]]; then
    _loopback_code=$(curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 1 --max-time 2 \
        "${LOOPBACK_ORCH_URL}/api/healthz" 2>/dev/null || echo "000")
    if [[ "${_loopback_code}" == "200" ]]; then
        ORCH_URL="${LOOPBACK_ORCH_URL}"
        IS_LOOPBACK=1
        log_quiet "[loopback] ${LOOPBACK_ORCH_URL} reachable — reporting trusted-local, no bearer token required"
    fi
fi

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
TOKEN_EXPIRY_STATE_DIR="${TOKEN_EXPIRY_STATE_DIR:-${TABS_DIR}/.token-expiry-state}"

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
FF_DIRTY_CONSECUTIVE_TICKS=0
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
    FF_DIRTY_CONSECUTIVE_TICKS=$(python3 -c 'import json,sys
try:
    d = json.load(open(sys.argv[1]))
    print(int(d.get("dirty_consecutive_ticks", 0)))
except Exception:
    print(0)' "${FF_RESULT_FILE}" 2>/dev/null || echo 0)
fi

# Read ONE repo's own dirty_consecutive_ticks out of FF_RESULT_FILE's per-repo
# repo_dirty_ticks map (0 if the file/repo/field is absent or unparseable). This is
# the reporter-side counterpart of slot-cron-ff-pull.sh's own _read_repo_dirty_ticks —
# same FF_RESULT_FILE, same repo_key convention (the repo clone's OWN resolved
# absolute path, set by classify_repo() via `pwd` post-pushd, matching ff_one()'s
# `repo_key="$(pwd)"` exactly, so a lookup here always hits the same key the FF-cron
# wrote). Fixes git_health_not_clean_since_pinned_constant_2026_07_27.md finding
# (iii): before this, the reporter forwarded only the HOST-WIDE aggregate
# (FF_DIRTY_CONSECUTIVE_TICKS above), so one repo's confirmed dirty streak could
# block EVERY repo on the host from clearing not_clean_since. agent-orchestrator's
# server side (RepoStatus.dirty_consecutive_ticks, _propagate_not_clean_since) already
# prefers this per-repo value when present — this is the companion reporter change
# named in that fix's commit message (agent-orchestrator@5d6752b).
read_repo_dirty_ticks() {
    local repo_key="$1"
    if [[ -s "${FF_RESULT_FILE}" ]]; then
        python3 -c "
import json, sys
try:
    d = json.load(open(sys.argv[1]))
    print(int(d.get('repo_dirty_ticks', {}).get(sys.argv[2], 0)))
except Exception:
    print(0)
" "${FF_RESULT_FILE}" "${repo_key}" 2>/dev/null || echo 0
    else
        echo 0
    fi
}

# Excluded frozen-snapshot clones — 2026-08-05 pre-history-rewrite backups, e.g.
# <repo>.stale-pre-history-rewrite-<ts>/ (git-health-scan exclusion, 2026-08-10:
# plans/active/issues/git_health_scan_exclusion_infra_routing_2026_08_10.md). These
# are intentional backups, NOT real drift/dirt — skip them in every per-repo
# enumeration so they never inflate the dirty/drift picture, accrue repo_dirty_ticks,
# or get starve/stash/parked-wip pings.
is_frozen_snapshot_clone() {
    [[ "$(basename "$1")" == *.stale-* ]]
}

# Defensive instrumentation (ao_remediation_b_code_chain_2026_07_23.md item 2 — the
# diagnostic half of item 1). Item 1 made dirty_files := len(sample_list), so
# `dirty_files>0 with an empty sample` is now structurally unreachable through
# classify_repo()'s own control flow — but it must survive as a tripwire in case a
# future edit reintroduces an independent count, or some other path recomputes
# dirty_files without going through sample_list. Standalone + parameterised (not
# inlined) specifically so a test can FORCE the condition directly — call it with a
# contrived (dirty_files, sample_list length) pair that classify_repo() itself can no
# longer produce — and still prove the raw-bytes log line fires
# (git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md: pins the next
# occurrence of whatever upstream mechanism injects a stray count, cause-agnostic).
# Args: $1=dirty_files count, $2=raw `git status --porcelain` capture, $3=sample
# array length actually kept. Logs (never log_quiet — an anomaly, not routine noise)
# and returns 0 if it fired, 1 otherwise.
log_df_sample_mismatch_if_any() {
    local df="$1" porcelain_raw="$2" sample_len="$3"
    if [[ "${df}" -gt 0 && "${sample_len}" -eq 0 ]]; then
        log "[anomaly] dirty_files=${df} with an empty dirty_files_sample — raw porcelain (cat -A): $(printf '%s' "${porcelain_raw}" | cat -A | tr '\n' ';')"
        return 0
    fi
    return 1
}

# Classify one repo worktree → emits TAB-separated row to stdout:
#   name<TAB>branch<TAB>state<TAB>dirty_files<TAB>ahead<TAB>behind<TAB>local_sha<TAB>int_branch<TAB>dirty_oldest_iso<TAB>unpushed_plans<TAB>dirty_sample<TAB>repo_dirty_ticks
#
# repo_dirty_ticks: THIS repo's own dirty_consecutive_ticks from slot-cron-ff-pull.sh's
#   repo_dirty_ticks map (see read_repo_dirty_ticks above) — always a non-negative int
#   (0 when the FF-cron has never observed this specific repo dirty, or hasn't run at
#   all on this host). Forwarded per-repo in post_snapshot() so the server's confirm-
#   gate keys on THIS repo's own streak, not the host-wide aggregate.
# unpushed_plans: pipe-separated list of plan file basenames (plans/active/*.md or
#   plans/active/issues/*.md) that are dirty or untracked in a unified-trading-pm worktree.
#   Empty string for all other repos.
# dirty_sample: pipe-separated raw `git status --porcelain` lines (status code + path),
#   up to 5, when dirty_files > 0. Empty when clean. Lets a dirty-worktree report be
#   reconciled against the actual file(s) instead of just a count
#   (slot5_deployment_api_dirty_false_positive_2026_07_13.md — a bare "1 dirty file"
#   with no path could never be cross-checked against a simultaneous manual `git status`).
#   dirty_files is DERIVED from this same sample array's length (never an independent
#   count) — see the note inline below — so for a repo with >5 dirty files dirty_files
#   reads as 5 (capped), not the true total. Accepted trade-off: dirty_files and
#   dirty_files_sample can never diverge (ao_remediation_b_code_chain_2026_07_23.md
#   item 1); every consumer only ever tests dirty_files >0/==0, never an exact count.
classify_repo() {
    local repo_dir="$1"
    local repo_name branch local_sha int_branch state dirty_files ahead behind dirty_oldest_iso unpushed_plans dirty_sample
    local repo_key repo_dirty_ticks
    repo_name=$(basename "${repo_dir}")
    int_branch="${INTEGRATION_BRANCH}"

    pushd "${repo_dir}" >/dev/null 2>&1 || return 0
    # Per-repo identity for the dirty-ticks lookup — the resolved cwd (post-pushd),
    # same convention slot-cron-ff-pull.sh's ff_one() uses for repo_key, so two
    # slots' clones of the same repo NAME never collide (see read_repo_dirty_ticks
    # above).
    repo_key="$(pwd)"
    repo_dirty_ticks="$(read_repo_dirty_ticks "${repo_key}")"
    branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "DETACHED")
    local_sha=$(git rev-parse --short=12 HEAD 2>/dev/null || echo "")

    if [[ "${branch}" == "DETACHED" || "${branch}" == "HEAD" || -z "${local_sha}" ]]; then
        printf '%s\t%s\tdetached\t0\t0\t0\t%s\t%s\t\t\t\t%s\n' "${repo_name}" "${branch:-DETACHED}" "${local_sha}" "${int_branch}" "${repo_dirty_ticks}"
        popd >/dev/null || return 0
        return 0
    fi

    local porcelain
    porcelain=$(git status --porcelain 2>/dev/null || echo "")
    dirty_files=0
    dirty_oldest_iso=""
    unpushed_plans=""
    dirty_sample=""
    if [[ -n "${porcelain}" ]]; then
        # Find oldest mtime among dirty files; also collect unpushed plan files for
        # unified-trading-pm repos (paths matching plans/active/*.md or plans/active/issues/*.md).
        # Also capture up to 5 raw porcelain lines (status code + path) so a false-positive
        # report is immediately diagnosable from the dashboard/nudge instead of requiring a
        # blind manual re-check (slot5_deployment_api_dirty_false_positive_2026_07_13.md —
        # "1 dirty file" with no path meant the claim could never be reconciled against
        # a simultaneous clean `git status`).
        local oldest_epoch="" line file ep plan_list=() sample_list=()
        while IFS= read -r line; do
            [[ -z "${line}" ]] && continue
            file="${line:3}"
            file="${file%% -> *}"
            if [[ "${#sample_list[@]}" -lt 5 ]]; then
                sample_list+=("${line}")
            fi
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
        # dirty_files is DERIVED from sample_list's length — the same array the loop
        # above populates — never an independent `wc -l` on the raw capture. This is
        # the single source of truth: the two numbers can no longer diverge, which is
        # what made `dirty_files=1` with an empty `dirty_files_sample` possible before
        # (git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md — review proved
        # via cat -A/hexdump the tree emitted ZERO bytes while the old wc-l-based count
        # still posted 1). Cause-agnostic: whatever upstream artifact injects a stray
        # byte, dirty_files can never exceed what this loop actually kept.
        dirty_files="${#sample_list[@]}"
        dirty_oldest_iso=$(epoch_to_iso "${oldest_epoch}")
        # Build pipe-separated list of unpushed plan basenames.
        if [[ "${#plan_list[@]}" -gt 0 ]]; then
            unpushed_plans="$(printf '%s|' "${plan_list[@]}")"
            unpushed_plans="${unpushed_plans%|}"   # strip trailing pipe
        fi
        if [[ "${#sample_list[@]}" -gt 0 ]]; then
            dirty_sample="$(printf '%s|' "${sample_list[@]}")"
            dirty_sample="${dirty_sample%|}"   # strip trailing pipe
        fi
        # Tripwire: dirty_files is derived from sample_list above, so this can't fire
        # through this code path today — kept for whatever regresses that invariant.
        log_df_sample_mismatch_if_any "${dirty_files}" "${porcelain}" "${#sample_list[@]}"
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
            printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
                "${repo_name}" "${branch}" "${state}" "${dirty_files}" "${ahead}" "${behind}" "${local_sha}" "${int_branch}" "${dirty_oldest_iso}" "${unpushed_plans}" "${dirty_sample}" "${repo_dirty_ticks}"
            popd >/dev/null || return 0
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

    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
        "${repo_name}" "${branch}" "${state}" "${dirty_files}" "${ahead}" "${behind}" "${local_sha}" "${int_branch}" "${dirty_oldest_iso}" "${unpushed_plans}" "${dirty_sample}" "${repo_dirty_ticks}"
    popd >/dev/null || return 0
}

# Resolve token for a slot. Per-slot token preferred; fall back to global token.
# In loopback mode (IS_LOOPBACK=1) a missing/unreadable token is NOT fatal — prints
# nothing and returns 0 (success, empty token) so post_snapshot/post_starve_ping send
# the request with no Authorization header at all; the orchestrator's own
# auth.py::_is_trusted_loopback accepts a genuine same-box caller anonymously. The
# off-VM path (IS_LOOPBACK=0) is unchanged: no token found → return 1 (skip + log).
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
    if [[ "${IS_LOOPBACK}" -eq 1 ]]; then
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
    if len(parts) < 12:
        parts += [""] * (12 - len(parts))
    name, branch, state, dirty_files, ahead, behind, local_sha, int_branch, dirty_oldest, unpushed_raw, dirty_sample_raw, repo_dirty_ticks_raw = parts[:12]
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
    if dirty_sample_raw:
        repo["dirty_files_sample"] = [p for p in dirty_sample_raw.split("|") if p]
    # Per-repo dirty-tick count (git_health_not_clean_since_pinned_constant_2026_07_27.md
    # finding (iii) fix): keys RepoStatus.dirty_consecutive_ticks so the server
    # not_clean_since confirm-gate reads this repos own streak, not the host-wide
    # aggregate below. Always present (classify_repo always computes it, default "0"),
    # so this branch only skips on a genuinely malformed/short row.
    if repo_dirty_ticks_raw != "":
        repo["dirty_consecutive_ticks"] = int(repo_dirty_ticks_raw)
    repos.append(repo)
ff_last_run = sys.argv[4] if len(sys.argv) > 4 else ""
ff_last_result = sys.argv[5] if len(sys.argv) > 5 else ""
dirty_ticks = int(sys.argv[6]) if len(sys.argv) > 6 else 0
out = {"reported_at": reported_at, "host": host, "repos": repos}
if ff_last_run:
    out["ff_pull_last_run"] = ff_last_run
if ff_last_result:
    out["ff_pull_last_result"] = ff_last_result
if dirty_ticks:
    out["dirty_consecutive_ticks"] = dirty_ticks
print(json.dumps(out))
' "${slot_id}" "${HOSTNAME_SHORT}" "${NOW_ISO}" "${FF_LAST_RUN}" "${FF_LAST_RESULT}" "${FF_DIRTY_CONSECUTIVE_TICKS}")
    if [[ -z "${payload}" ]]; then
        log "[skip:empty-payload] slot ${slot_id}"
        return 0
    fi

    # No Authorization header at all when token is empty (loopback, no token found) —
    # not "Bearer " with an empty value — so the request qualifies for the server's
    # trusted-loopback anonymous fallback rather than a bad-token rejection.
    local http_status
    if [[ -n "${token}" ]]; then
        http_status=$(curl -sS -o /tmp/.git-status-resp.$$ -w '%{http_code}' \
            -X POST "${ORCH_URL}/api/slots/${slot_id}/git-status" \
            -H "Authorization: Bearer ${token}" \
            -H "Content-Type: application/json" \
            -d "${payload}" 2>/dev/null || echo "000")
    else
        http_status=$(curl -sS -o /tmp/.git-status-resp.$$ -w '%{http_code}' \
            -X POST "${ORCH_URL}/api/slots/${slot_id}/git-status" \
            -H "Content-Type: application/json" \
            -d "${payload}" 2>/dev/null || echo "000")
    fi
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
    # Log-line label (5th, optional arg): distinguishes which watchdog is calling in
    # the shared [xxx-ping]/[xxx-ping-fail] log lines below — without this both the
    # FF-starvation watchdog and the stash-pile watchdog would log identical
    # "[starve-ping...]" text, making on-call triage guess which one actually fired.
    local label="${5:-starve-ping}"
    # Reuse the message endpoint (from_role must be one of main/review/operator;
    # the watchdog speaks for the orchestrator → "main"). Same curl+token shape
    # as post_snapshot.
    local body http_status
    body=$(printf '%s' "${payload}" | python3 -c '
import json, sys
print(json.dumps({"text": sys.stdin.read(), "from_role": "main"}))
')
    [[ -n "${body}" ]] || return 0
    if [[ -n "${token}" ]]; then
        http_status=$(curl -sS -o /dev/null -w '%{http_code}' \
            -X POST "${ORCH_URL}/api/slots/${slot_id}/message" \
            -H "Authorization: Bearer ${token}" \
            -H "Content-Type: application/json" \
            -d "${body}" 2>/dev/null || echo "000")
    else
        http_status=$(curl -sS -o /dev/null -w '%{http_code}' \
            -X POST "${ORCH_URL}/api/slots/${slot_id}/message" \
            -H "Content-Type: application/json" \
            -d "${body}" 2>/dev/null || echo "000")
    fi
    if [[ "${http_status}" == "200" ]]; then
        log "[${label}] slot ${slot_id}/${repo_name} — signalled"
        return 0
    fi
    log "[${label}-fail] slot ${slot_id}/${repo_name} — HTTP ${http_status}"
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
        is_frozen_snapshot_clone "${repo_dir}" && { log_quiet "[skip:stale-snapshot] ${repo_name}"; continue; }
        marker="${STARVE_STATE_DIR}/slot-${slot_id}__${repo_name}.starved"
        payload=$(FF_STARVE_COMMIT_THRESHOLD="${FF_STARVE_COMMIT_THRESHOLD}" \
                  FF_STARVE_AGE_HOURS="${FF_STARVE_AGE_HOURS}" \
                  INTEGRATION_BRANCH="${INTEGRATION_BRANCH}" \
                  bash "${STARVE_DETECTOR}" "${repo_dir}" --slot "${slot_id}" 2>/dev/null || echo "")
        if [[ -n "${payload}" ]]; then
            # STARVED. Ping once per episode (skip if already marked).
            if [[ ! -f "${marker}" ]]; then
                if post_starve_ping "${slot_id}" "${repo_name}" "${payload}" "${token}" "starve-ping"; then
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

# Stash-pile regrowth watchdog. For each repo under a slot, run the detector
# (stash-pile-detect.sh); if the pile is over-threshold, POST a ONE-PER-(slot,repo)
# WARNING to the slot's message inbox — same mechanism + dedup-marker pattern as
# check_starvation_for_slot above (reuses post_starve_ping: it just posts whatever
# payload text it's given, the name predates this second caller). Read-only: the
# detector never touches `git stash`, so this can never lose or move anyone's WIP.
check_stash_pile_for_slot() {
    local slot_id="$1" slot_dir="$2"
    [[ "${STASH_PILE_WATCHDOG}" -eq 1 ]] || return 0
    [[ -x "${STASH_DETECTOR}" || -f "${STASH_DETECTOR}" ]] || return 0
    local token
    token=$(resolve_token_for_slot "${slot_id}") || return 0
    mkdir -p "${STARVE_STATE_DIR}" 2>/dev/null || true

    local repo_dir repo_name marker payload
    for repo_dir in "${slot_dir}"*/; do
        [[ -d "${repo_dir}" ]] || continue
        [[ -d "${repo_dir}.git" || -f "${repo_dir}.git" ]] || continue
        repo_name=$(basename "${repo_dir}")
        is_frozen_snapshot_clone "${repo_dir}" && { log_quiet "[skip:stale-snapshot] ${repo_name}"; continue; }
        marker="${STARVE_STATE_DIR}/slot-${slot_id}__${repo_name}.stash-warn"
        payload=$(STASH_WARN_COUNT="${STASH_WARN_COUNT}" \
                  STASH_WARN_AGE_DAYS="${STASH_WARN_AGE_DAYS}" \
                  bash "${STASH_DETECTOR}" "${repo_dir}" --slot "${slot_id}" 2>/dev/null || echo "")
        if [[ -n "${payload}" ]]; then
            # Over-threshold. Ping once per episode (skip if already marked).
            if [[ ! -f "${marker}" ]]; then
                if post_starve_ping "${slot_id}" "${repo_name}" "${payload}" "${token}" "stash-warn"; then
                    : > "${marker}" 2>/dev/null || true
                fi
            else
                log_quiet "[stash-warn-dup] slot ${slot_id}/${repo_name} — already signalled this episode"
            fi
        else
            # Back under threshold → clear any prior marker (a future regrowth re-pings).
            [[ -f "${marker}" ]] && rm -f "${marker}" 2>/dev/null || true
        fi
    done
}

# Decode the `exp` (Unix epoch, UTC) claim from a JWT's second (payload) segment.
# Prints the epoch on success; prints nothing and returns non-zero on any malformed/
# undecodable input — callers MUST treat that as "can't tell, skip" rather than
# "expired", so an unexpected token shape (e.g. a future non-JWT credential format)
# never gets misread as an emergency and spams a false warning.
decode_jwt_exp() {
    local token="$1" payload_seg
    payload_seg=$(printf '%s' "${token}" | cut -d. -f2)
    [[ -n "${payload_seg}" ]] || return 1
    python3 -c '
import base64, json, sys
seg = sys.argv[1]
try:
    padded = seg + "=" * (-len(seg) % 4)
    claims = json.loads(base64.urlsafe_b64decode(padded))
    exp = claims.get("exp")
    if exp is None:
        sys.exit(1)
    print(int(exp))
except Exception:
    sys.exit(1)
' "${payload_seg}" 2>/dev/null
}

# Token-near-expiry early warning
# (git_status_reporter_stale_public_url_token_expiry_2026_07_24.md option (a) — the
# smallest fix, needs no new credential surface). Reuses the token this reporter
# already resolved to build its own Authorization header (resolve_token_for_slot),
# decodes its `exp` claim, and fires ONE warning per state-transition into the
# near-expiry window into the AO activity feed (via the slot message inbox — same
# post_starve_ping mechanism + one-marker-per-episode dedup pattern the
# FF-starvation/stash-pile watchdogs above already use), never every tick. Clears
# on transition OUT of the window (a re-mint via remint-orch-token.sh, or this host
# switching to a longer-lived token) so a fresh near-expiry episode re-warns. Never
# raises the TTL itself — see the source doc: that just delays and worsens the
# eventual outage.
check_token_expiry_for_slot() {
    local slot_id="$1"
    [[ "${TOKEN_EXPIRY_WATCHDOG}" -eq 1 ]] || return 0
    local token
    token=$(resolve_token_for_slot "${slot_id}") || return 0
    [[ -n "${token}" ]] || return 0   # loopback/anonymous — no bearer token to expire

    local exp_epoch
    exp_epoch=$(decode_jwt_exp "${token}") || return 0
    [[ -n "${exp_epoch}" ]] || return 0

    mkdir -p "${TOKEN_EXPIRY_STATE_DIR}" 2>/dev/null || true
    local marker="${TOKEN_EXPIRY_STATE_DIR}/slot-${slot_id}.near-expiry"
    local now_epoch remaining_secs warn_secs
    now_epoch=$(date -u +%s)
    remaining_secs=$(( exp_epoch - now_epoch ))
    warn_secs=$(( TOKEN_EXPIRY_WARN_DAYS * 86400 ))

    if [[ "${remaining_secs}" -le "${warn_secs}" ]]; then
        if [[ ! -f "${marker}" ]]; then
            local exp_iso payload
            exp_iso=$(date -u -d "@${exp_epoch}" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null \
                || date -u -r "${exp_epoch}" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null \
                || echo "${exp_epoch}")
            payload="orch_token near expiry: exp ${exp_iso} (~$(( remaining_secs / 3600 ))h remaining). Re-mint via scripts/dev/remint-orch-token.sh before it lapses — do not just raise the TTL (/plans/active/issues/git_status_reporter_stale_public_url_token_expiry_2026_07_24.md)."
            if post_starve_ping "${slot_id}" "orch_token" "${payload}" "${token}" "token-expiry-warn"; then
                : > "${marker}" 2>/dev/null || true
            fi
        else
            log_quiet "[token-expiry-dup] slot ${slot_id} — already signalled this episode"
        fi
    else
        # Back outside the warn window (re-mint or a longer-lived token) → clear any
        # prior marker so a future near-expiry episode re-warns.
        [[ -f "${marker}" ]] && rm -f "${marker}" 2>/dev/null || true
    fi
}

# Live heartbeat on .agent-claim (multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md
# candidate fix 1, unblocked by operator ruling 2026-08-08: "build a collision-warning mechanism"). The claim
# file's own `expires_at` is a poor liveness signal on its own: an AO-dispatched worker's claim already gets
# `expires_at` refreshed server-side on every heartbeat (worktree_claim.refresh_expiry, called from
# routes/slots_worker.py), but an INTERACTIVE session's claim is written ONCE at spawn with a flat 12-hour TTL
# (INTERACTIVE_CLAIM_TTL) and nothing refreshes it afterward — for up to 12 hours an abandoned interactive claim
# reads identically to a genuinely active one. This gives every claim (interactive or AO-dispatched) a SEPARATE,
# independently-checkable liveness signal: the file's own mtime. Each tick, if the claim's OWN `tmux_session` is
# confirmed alive (same exact-match has-session check FM8's maker-liveness classifier uses —
# server/worktree_clean_check/_liveness.py / server/tmux_spawn.py's exact_target(), which prevents a bare
# `-t orch-slot-1` from prefix-matching `orch-slot-10`), `touch` the claim file so its mtime advances; if the
# session is gone (or tmux itself isn't installed on this host), the mtime is left untouched and ages naturally.
# A future consumer (candidate fix 2, the session-start collision warning) can then treat "mtime within the last
# ~2 cron ticks" as "claimed AND alive right now" — distinguishable from "claimed" alone, which is all
# `expires_at` can currently tell you. Read-only w.r.t. the claim's JSON content (never rewrites
# agent_id/expires_at/etc.) — only the file's own mtime changes, so this can never race the server's own
# `refresh_expiry()` writes or corrupt a legitimate claim.
# Surface a `.parked-wip` notice to whoever actually owns this checkout.
#
# The gap this closes (2026-08-10): when a ship's reconcile parks a PEER's uncommitted work — or
# an agent stashes it deliberately to unblock a gate — every warning goes to the SHIPPING run's
# stderr, i.e. to the wrong person. The owner is in another session and the only trace is a stash
# entry they have no reason to look at. This reporter already runs every 5 minutes in each slot,
# so it is the one channel that reliably reaches them without inventing a new one.
report_parked_wip() {
    local slot_id="$1" slot_dir="$2" notice repo
    for repo in "${slot_dir}"*/; do
        is_frozen_snapshot_clone "${repo}" && continue
        notice="${repo}.parked-wip"
        [[ -f "${notice}" ]] || continue
        [[ -s "${notice}" ]] || continue
        log "[parked-wip] slot ${slot_id} — $(basename "${repo}"): uncommitted work was PARKED by another session."
        log "[parked-wip]   recovery instructions are in ${notice} — read it before re-applying anything."
    done
}

refresh_agent_claim_heartbeat() {
    local slot_id="$1" slot_dir="$2" claim_file tmux_session
    claim_file="${slot_dir}.agent-claim"
    [[ -f "${claim_file}" ]] || return 0
    tmux_session=$(python3 -c '
import json, sys
try:
    d = json.load(open(sys.argv[1]))
    print(d.get("tmux_session", ""))
except Exception:
    print("")' "${claim_file}" 2>/dev/null || echo "")
    if [[ -z "${tmux_session}" ]]; then
        log_quiet "[claim-heartbeat:skip] slot ${slot_id} — claim present but unparseable/no tmux_session field"
        return 0
    fi
    if command -v tmux >/dev/null 2>&1 && tmux has-session -t "=${tmux_session}" 2>/dev/null; then
        if touch "${claim_file}" 2>/dev/null; then
            log "[claim-heartbeat] slot ${slot_id} — refreshed (tmux session ${tmux_session} alive)"
        fi
    else
        log "[claim-heartbeat:stale] slot ${slot_id} — tmux session ${tmux_session} not found; mtime left untouched"
    fi
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
        is_frozen_snapshot_clone "${repo_dir}" && continue
        rows_tsv+="$(classify_repo "${repo_dir}")"$'\n'
    done
    post_snapshot "${slot_id_str}" "${rows_tsv}"
    refresh_agent_claim_heartbeat "${slot_id_str}" "${slot_dir}"
    report_parked_wip "${slot_id_str}" "${slot_dir}"
    check_starvation_for_slot "${slot_id_str}" "${slot_dir}"
    check_stash_pile_for_slot "${slot_id_str}" "${slot_dir}"
    check_token_expiry_for_slot "${slot_id_str}"
done

# Slot 0 = the un-slotted main workspace checkout (the base copy the per-slot
# Path-B reference-clones share, at ${WORKSPACE_PATH}/<repo>/ — NOT under .tabs/).
# Reported so its git hygiene shows alongside the worker slots; the orchestrator
# auto-registers slot 0 as a PAUSED slot on first report (set_slot_git_status),
# so it is tracked but never a spawn target. Only swept when 0 is in --slots.
if slot_in_filter "0"; then
    rows_tsv=""
    for repo_dir in "${WORKSPACE_PATH}"/*/; do
        [[ -d "${repo_dir}" ]] || continue
        [[ "$(basename "${repo_dir}")" == ".tabs" ]] && continue
        [[ -d "${repo_dir}.git" || -f "${repo_dir}.git" ]] || continue
        is_frozen_snapshot_clone "${repo_dir}" && continue
        rows_tsv+="$(classify_repo "${repo_dir}")"$'\n'
    done
    if [[ -n "${rows_tsv//[$'\n\t ']/}" ]]; then
        post_snapshot "0" "${rows_tsv}"
    else
        log_quiet "[skip:empty] slot 0 (main workspace) — no git repos found"
    fi
else
    log_quiet "[skip:not-in-filter] slot 0 (main workspace)"
fi

log_quiet "=== git-status sweep complete (host=${HOSTNAME_SHORT}, workspace=${WORKSPACE_PATH}) ==="
