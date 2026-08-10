#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# push-host-governor.sh -- host-shared concurrency control for the git remote critical
# section shared by quickmerge.sh and safe-doc-push.sh.
#
# WHY THIS EXISTS (2026-08-09, live incident): each interactive/AO slot on this host is a
# SEPARATE `git clone --reference` with its own .git dir (per-tab-worktrees architecture) --
# a flock scoped to "this checkout's .git dir" (quickmerge.sh's/safe-doc-push.sh's existing
# per-checkout commit locks, see _qm_locked_git_commit / locked_git_commit) only serialises
# processes WITHIN one clone. It provides ZERO cross-slot coordination -- the only shared
# contention point across slots is the remote ref on GitHub itself. Measured live: ~24
# distinct AO-dispatched slot identities (git log --format="%an" --since="1 hour ago") all
# independently committing to PM's live-defi-rollout at once produced sustained
# branch-drift-retry storms and at least one genuine `fatal: cannot lock ref 'HEAD'`
# git-object-level race -- diagnosed during the plans/active reference-path-fix shipping
# saga, 2026-08-09.
#
# DESIGN (operator-agreed, 2026-08-09): split the two phases differently.
#   - The VALIDATION phase (prek/QG hook chain a `git commit` call runs synchronously --
#     frontmatter/reference-path/prosewrap/lint/etc checks, I/O-bound rather than CPU-bound
#     the way quality-gates.sh's own heavy pytest/basedpyright phases are) tolerates real
#     concurrency, so it gets a token bucket exactly like qg-host-governor.sh's own heavy-phase
#     gate (default K=8, user-confirmed "8 seems reasonable").
#   - The actual git-remote critical section (fetch -> reconcile -> commit -> push) does NOT:
#     GitHub only accepts one fast-forward write to a given ref at a time, and more than ~2-3
#     concurrent pushers add pure collision/retry overhead, not throughput. This gets a TRUE
#     per-repo+branch MUTEX (K=1), not a wider token bucket. Different repos/branches never
#     contend with each other on GitHub, so the mutex is keyed by (repo, branch), not global.
#
# MECHANISM -- mirrors scripts/quality-gates-base/qg-host-governor.sh's proven shape exactly:
# same explicit-numeric-FD flock pattern (bash 3.2-safe -- the macOS operator host's bash
# predates the `exec {fd}>` auto-FD form), same _qg_shared_root-style /.tabs/<N> path-collapse
# so every slot clone on one host agrees on the same lock directory, same graceful degrade to
# ungoverned if flock(1) is missing or the lock dir can't be created -- a missing dependency
# here must never be able to block a commit/push fleet-wide.
#
# USAGE (sourced from quickmerge.sh / safe-doc-push.sh):
#   source "<this file>"
#   push_gov_acquire_validate                      # token bucket, K=8 default -- wrap ONLY
#   ... git commit (runs the prek/QG hook chain) ...  # the hook-chain-running commit call
#   push_gov_release_validate
#
#   push_gov_acquire_push "$REPO_NAME" "$BRANCH"    # true mutex -- wrap fetch+reconcile+push
#   ... git fetch / git pull --rebase --autostash / git push ...
#   push_gov_release_push
#
# Both gates also auto-release on process exit (flock drops when the holding FD closes, which
# the OS does unconditionally on process death) -- a hard `exit 1` mid-critical-section (a real
# conflict, a push failure) never leaves a stale lock behind for the next queued slot. Callers
# therefore only need ONE explicit release call, on the success path.
#
# ENV
#   PUSH_GOV_VALIDATE_CONCURRENCY   override K for the validation-phase token bucket (default 8)
#   PUSH_GOV_DIR                    lock root override (default: host-shared dir, see
#                                   _push_gov_shared_root)
#   PUSH_GOV_DISABLE                set to "true" to make every acquire/release a no-op
#
# Safe to source repeatedly; functions are idempotent (re-acquiring while already holding a
# gate is a no-op, matching qg-host-governor.sh's convention).

# _push_gov_shared_root -- collapses this checkout's own /.tabs/<N> per-slot path suffix down
# to ONE host-shared directory every slot clone on this host agrees on. Identical rule to
# qg-host-governor.sh's _qg_shared_root (duplicated rather than sourced: this file must stay
# independently loadable from a bare checkout with no quality-gates-base/ dependency, and the
# rule itself is a single, stable one-liner, unlikely to drift out of sync).
_push_gov_shared_root() {
    local ws="${WORKSPACE_ROOT:-}"
    case "$ws" in
        "")        echo "${TMPDIR:-/tmp}" ;;
        */.tabs/*) echo "${ws%/.tabs/*}" ;;
        *)         echo "$ws" ;;
    esac
}
_push_gov_dir() { echo "${PUSH_GOV_DIR:-$(_push_gov_shared_root)/.benchmarks/push-governor}"; }

# ── validation-phase token bucket (K=8 default) ──────────────────────────────────────────
_PUSH_GOV_VALIDATE_FD_BASE=400
_push_gov_validate_k() { echo "${PUSH_GOV_VALIDATE_CONCURRENCY:-8}"; }

push_gov_acquire_validate() {
    [[ "${PUSH_GOV_DISABLE:-}" == "true" ]] && return 0
    command -v flock >/dev/null 2>&1 || { echo "[push-governor] flock(1) absent -- validation phase ungoverned" >&2; return 0; }
    [[ -n "${_PUSH_GOV_VALIDATE_FD:-}" ]] && return 0   # already holding a token (idempotent)

    local k dir fd
    k="$(_push_gov_validate_k)"; dir="$(_push_gov_dir)/validate"
    mkdir -p "$dir" 2>/dev/null || { echo "[push-governor] cannot create $dir -- validation phase ungoverned" >&2; return 0; }

    local waited=0
    while true; do
        local i
        for (( i=1; i<=k; i++ )); do
            fd=$(( _PUSH_GOV_VALIDATE_FD_BASE + i ))
            eval "exec ${fd}>\"\$dir/slot.\$i\"" 2>/dev/null || continue
            if flock -n "$fd"; then
                _PUSH_GOV_VALIDATE_FD=$fd
                [[ "$waited" -gt 0 ]] && echo "[push-governor] validate token $i/$k acquired after ${waited}s wait" >&2
                return 0
            fi
            eval "exec ${fd}>&-"   # slot busy -- close and try next
        done
        sleep 1; waited=$(( waited + 1 ))
        (( waited % 30 == 0 )) && echo "[push-governor] all ${k} validate tokens busy -- queued ${waited}s" >&2
    done
}

push_gov_release_validate() {
    [[ -n "${_PUSH_GOV_VALIDATE_FD:-}" ]] || return 0
    flock -u "$_PUSH_GOV_VALIDATE_FD" 2>/dev/null || true
    eval "exec ${_PUSH_GOV_VALIDATE_FD}>&-" 2>/dev/null || true   # explicit FD (bash 3.2-compatible)
    _PUSH_GOV_VALIDATE_FD=""
}

# ── push-critical-section mutex (K=1, keyed per repo+branch) ────────────────────────────
_PUSH_GOV_PUSH_FD=500

# push_gov_acquire_push <repo> <branch> -- true mutex, one lock file per (repo, branch) pair
# (key sanitised: anything outside [A-Za-z0-9_.-] -> _) so unrelated repos/branches never
# wait on each other. Blocks with no timeout until free -- this IS the queue; there is no
# "busy, try elsewhere" fallback, because the whole point is exactly one slot at a time
# touching a given ref's remote state.
push_gov_acquire_push() {
    [[ "${PUSH_GOV_DISABLE:-}" == "true" ]] && return 0
    command -v flock >/dev/null 2>&1 || { echo "[push-governor] flock(1) absent -- push section ungoverned (cross-slot collisions possible)" >&2; return 0; }
    [[ -n "${_PUSH_GOV_PUSH_HELD:-}" ]] && return 0   # already holding (idempotent -- e.g. a caller re-entering its own retry loop)

    local repo="${1:?push_gov_acquire_push: repo required}" branch="${2:?push_gov_acquire_push: branch required}"
    local key dir lockfile fd=$_PUSH_GOV_PUSH_FD
    key="$(printf '%s__%s' "$repo" "$branch" | tr -c 'A-Za-z0-9_.-' '_')"
    dir="$(_push_gov_dir)/push"
    mkdir -p "$dir" 2>/dev/null || { echo "[push-governor] cannot create $dir -- push section ungoverned" >&2; return 0; }
    lockfile="$dir/$key.lock"

    eval "exec ${fd}>\"\$lockfile\"" 2>/dev/null || { echo "[push-governor] cannot open $lockfile -- push section ungoverned" >&2; return 0; }

    local waited=0
    while ! flock -n "$fd" 2>/dev/null; do
        sleep 1; waited=$(( waited + 1 ))
        (( waited % 30 == 0 )) && echo "[push-governor] queued for the ${repo}@${branch} push slot -- another slot is pushing, ${waited}s" >&2
    done
    _PUSH_GOV_PUSH_HELD=1
    [[ "$waited" -gt 0 ]] && echo "[push-governor] push slot on ${repo}@${branch} acquired after ${waited}s wait" >&2
    return 0
}

push_gov_release_push() {
    [[ -n "${_PUSH_GOV_PUSH_HELD:-}" ]] || return 0
    flock -u "$_PUSH_GOV_PUSH_FD" 2>/dev/null || true
    eval "exec ${_PUSH_GOV_PUSH_FD}>&-" 2>/dev/null || true   # explicit FD (bash 3.2-compatible)
    _PUSH_GOV_PUSH_HELD=""
}

# ── introspection ─────────────────────────────────────────────────────────────────────
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    case "${1:-}" in
        --status)
            echo "validate: K=$(_push_gov_validate_k) dir=$(_push_gov_dir)/validate"
            echo "push:     dir=$(_push_gov_dir)/push"
            ;;
        *)
            echo "Usage: bash $0 --status" >&2
            exit 2
            ;;
    esac
fi
