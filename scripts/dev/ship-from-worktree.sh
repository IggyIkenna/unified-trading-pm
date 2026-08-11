#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# ship-from-worktree.sh — worktree-FIRST helper for holding uncommitted work
# in an interactive session, so a peer session sharing this slot's shared
# checkout can never revert it mid-edit.
#
# WHY THIS EXISTS (pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md,
# the "Two interactive sessions in ONE slot checkout" P1): interactive Claude
# Code sessions have no allocation mechanism, unlike AO-dispatched workers —
# an operator (or two operators) can point two live sessions at one
# `.tabs/<N>/<repo>` checkout, sharing its ONE `.git` index/HEAD/config.
# Measured live 2026-08-11 in slot 4: a peer session's own reconcile
# (quickmerge's autostash-quarantine path) reverted this session's tracked
# edits to HEAD TWICE in ~30 minutes, with `git status` reporting clean and
# the content recoverable only from a `pre-reconcile quarantine` stash by
# path. The only thing that reliably worked was to stop holding uncommitted
# work in the shared checkout at all, and hold it in a private linked
# `git worktree` instead — unreachable from the shared checkout's reconciles,
# because it has its own working tree, index, and HEAD (see
# /codex/05-infrastructure/per-tab-worktrees.md § "What worktree isolation
# does NOT cover" for the surfaces it does *not* fix — refs/stash and
# COMMIT_EDITMSG stay shared; this script never touches either).
#
# This is NOT the ephemeral per-commit worktree that safe-doc-push.sh /
# quickmerge.sh already build internally (those exist for the DURATION of one
# push and are torn down immediately after). This is a session-lifetime
# workspace: set it up once, edit and commit inside it for as long as you
# need, ship from it via the existing safe-doc-push.sh / quickmerge.sh (which
# will happily run from inside it — nesting one more throwaway worktree layer
# off the same object store is legal git), then tear it down when you're done.
#
# Deliberately does NOT reimplement reconcile/retry/push logic — that stays
# owned by safe-doc-push.sh and quickmerge.sh. This script only solves
# "give me a place to hold work that a peer session cannot touch."
#
# ---------------------------------------------------------------------------
# Usage:
#   ship-from-worktree.sh setup   [--dest <path>] [--branch <branch>]
#                                 [--repo-root <path>] [--with-venv]
#                                 [--no-siblings] [--quiet]
#   ship-from-worktree.sh cleanup <dest-path> [--quiet]
#   ship-from-worktree.sh --help
#
# setup:
#   --dest <path>       Parent directory to build the worktree + sibling
#                        symlinks under. Default: a fresh dir under
#                        ${TMPDIR:-/tmp}/ship-wt-<repo>-<timestamp>-<pid>.
#   --branch <branch>   Integration branch to detach onto. Default:
#                        live-defi-rollout (override for a repo whose
#                        integration branch differs, e.g. unified-trading-ci
#                        uses main — see slot-git-status-report.sh's
#                        per-repo override table for the current list).
#   --repo-root <path>  Repo to build the worktree FROM. Default: resolved
#                        via `git rev-parse --show-toplevel` from cwd — never
#                        assumed from a hardcoded directory name, so this
#                        keeps working if the F7-adjacent P1 (quickmerge's own
#                        directory-name assumptions, owned by another agent
#                        concurrently) relaxes those assumptions later.
#   --with-venv         Provision a Python venv inside the worktree, via the
#                        SAME shared per-repo cache quickmerge.sh's own
#                        isolated mode already uses (QM_ISO_VENV_CACHE,
#                        default $HOME/.cache/qm-iso-venv/<repo>) — so the
#                        cost is paid once across BOTH tools, not per tool.
#                        Deliberately never symlinks the worktree's .venv to
#                        the CALLER's real .venv: quickmerge.sh's own header
#                        comment (scripts/quickmerge.sh, "private, CACHED
#                        venv -- never the caller's") and this very issue
#                        doc's "Lessons carried forward" record that doing so
#                        let `uv sync --frozen` PRUNE packages out of the
#                        operator's live environment (measured 2026-08-10).
#                        Omit this flag for a docs-only session — bats/bash
#                        tests need no venv at all.
#   --no-siblings       Skip symlinking sibling repos into the workspace
#                        parent dir. Sibling symlinks exist only so a
#                        subsequent `quickmerge.sh` run from inside this
#                        worktree can resolve its own STAGE 1.5 dependency
#                        alignment (see per-tab-worktrees.md) — harmless to
#                        skip for a docs-only session.
#   --quiet             Suppress the non-essential progress lines.
#
# cleanup:
#   <dest-path>          The SAME --dest path `setup` printed. Removes the
#                         linked worktree via `git worktree remove --force`
#                         (git's own removal — never a raw `rm -rf`, which is
#                         blocked by a guardrail hook on this host anyway),
#                         prunes worktree admin state, unlinks the sibling
#                         symlinks one at a time by name, then rmdir's the
#                         now-empty parent (never forced — if anything
#                         unexpected is left behind, rmdir fails loudly
#                         instead of silently deleting it).
#                         Idempotent: cleaning up a dest with nothing left in
#                         it is a no-op, not an error.
#
# Exit codes: 0 success/no-op. 2 bad usage. 3 not inside a git repo (setup,
# no --repo-root given). 4 worktree add failed. 5 cleanup found more than one
# candidate worktree under --dest and refused to guess.
set -uo pipefail

_SFW_SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"

_sfw_log() {
    [[ "${SFW_QUIET:-0}" == "1" ]] && return 0
    printf '%s\n' "$*"
}

_sfw_usage() {
    sed -n '2,70p' "${_SFW_SELF}" | sed 's/^# \{0,1\}//'
}

# ── setup ──────────────────────────────────────────────────────────────────

_sfw_setup() {
    local dest="" branch="live-defi-rollout" repo_root="" with_venv=0 link_siblings=1

    while [[ $# -gt 0 ]]; do
        case "$1" in
        --dest) dest="$2"; shift 2 ;;
        --branch) branch="$2"; shift 2 ;;
        --repo-root) repo_root="$2"; shift 2 ;;
        --with-venv) with_venv=1; shift ;;
        --no-siblings) link_siblings=0; shift ;;
        --quiet) SFW_QUIET=1; shift ;;
        *) echo "Unknown arg to setup: $1" >&2; return 2 ;;
        esac
    done

    if [[ -z "${repo_root}" ]]; then
        repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
    fi
    if [[ -z "${repo_root}" || ! -d "${repo_root}/.git" && ! -f "${repo_root}/.git" ]]; then
        echo "❌ not inside a git repo, and no --repo-root given. Run this from inside the" >&2
        echo "   checkout you want to isolate, or pass --repo-root <path>." >&2
        return 3
    fi
    repo_root="$(cd "${repo_root}" && pwd)"
    local leaf slot_dir
    leaf="$(basename "${repo_root}")"
    slot_dir="$(dirname "${repo_root}")"

    if [[ -z "${dest}" ]]; then
        dest="${TMPDIR:-/tmp}/ship-wt-${leaf}-$(date -u +%Y%m%dT%H%M%SZ)-$$"
    fi
    mkdir -p "${dest}" || { echo "❌ could not create --dest ${dest}" >&2; return 2; }
    dest="$(cd "${dest}" && pwd)"

    local leaf_path="${dest}/${leaf}"
    if [[ -e "${leaf_path}" ]]; then
        echo "❌ ${leaf_path} already exists — pick a fresh --dest or clean up the old one first" >&2
        echo "   (bash ${_SFW_SELF} cleanup ${dest})" >&2
        return 2
    fi

    _sfw_log "→ fetching origin/${branch} (${repo_root})"
    if ! git -C "${repo_root}" fetch origin "${branch}" --quiet; then
        echo "❌ fetch of origin/${branch} failed from ${repo_root}" >&2
        return 4
    fi

    _sfw_log "→ creating detached worktree at ${leaf_path}"
    if ! git -C "${repo_root}" worktree add --detach -q "${leaf_path}" "origin/${branch}"; then
        echo "❌ git worktree add failed — is ${branch} the right integration branch for this repo?" >&2
        echo "   (some repos use a non-default branch, e.g. --branch main)" >&2
        return 4
    fi

    local linked=0
    if [[ "${link_siblings}" == "1" ]]; then
        local d n
        for d in "${slot_dir}"/*/; do
            [[ -d "${d}" ]] || continue
            n="$(basename "${d}")"
            [[ "${n}" == "${leaf}" ]] && continue
            case "${n}" in
            *.stale-*) continue ;;
            esac
            [[ -e "${d}.git" ]] || continue
            if [[ ! -e "${dest}/${n}" ]]; then
                ln -s "${d%/}" "${dest}/${n}" 2>/dev/null && linked=$((linked + 1))
            fi
        done
        _sfw_log "→ linked ${linked} sibling repo(s) into ${dest} (for quickmerge's own STAGE 1.5 dependency alignment)"
    fi

    if [[ "${with_venv}" == "1" ]]; then
        if command -v uv >/dev/null 2>&1; then
            local venv_cache
            venv_cache="${QM_ISO_VENV_CACHE:-${HOME}/.cache/qm-iso-venv}/${leaf}"
            mkdir -p "$(dirname "${venv_cache}")" 2>/dev/null || true
            ln -sfn "${venv_cache}" "${leaf_path}/.venv" 2>/dev/null
            if [[ ! -x "${venv_cache}/bin/python" ]]; then
                _sfw_log "→ provisioning private venv for ${leaf} (first run — one-time cost, shared with quickmerge's own isolated runs)"
                if ! (cd "${leaf_path}" && UV_PROJECT_ENVIRONMENT="${venv_cache}" uv sync --frozen) >/dev/null 2>&1; then
                    (cd "${leaf_path}" && UV_PROJECT_ENVIRONMENT="${venv_cache}" uv sync) >/dev/null 2>&1 \
                        || echo "  ⚠ uv sync failed — quality-gates.sh will fail closed on the missing venv rather than silently degrade" >&2
                fi
            else
                _sfw_log "→ reusing cached venv for ${leaf} at ${venv_cache}"
            fi
        else
            echo "  ⚠ --with-venv requested but no 'uv' on PATH — skipping venv provisioning" >&2
        fi
    fi

    _sfw_log ""
    _sfw_log "✅ private worktree ready: ${leaf_path}  (detached at origin/${branch})"
    _sfw_log "   Your edits here are invisible to, and unreachable from, ${repo_root}'s"
    _sfw_log "   reconciles — a peer session sharing that checkout cannot revert this."
    _sfw_log ""
    _sfw_log "   Work here, committing as you go (edit → git add <names> → git commit,"
    _sfw_log "   same discipline as the shared checkout). When ready to ship:"
    _sfw_log "     cd ${leaf_path}"
    _sfw_log "     bash scripts/dev/safe-doc-push.sh \"msg\" --files '<paths>'    # docs-only"
    _sfw_log "     bash scripts/quickmerge.sh \"msg\" --agent --files '<paths>'   # code"
    _sfw_log ""
    _sfw_log "   When you're done with this worktree:"
    _sfw_log "     bash ${_SFW_SELF} cleanup ${dest}"
    echo "${leaf_path}"
    return 0
}

# ── cleanup ────────────────────────────────────────────────────────────────

_sfw_cleanup() {
    local dest=""
    while [[ $# -gt 0 ]]; do
        case "$1" in
        --quiet) SFW_QUIET=1; shift ;;
        -*) echo "Unknown arg to cleanup: $1" >&2; return 2 ;;
        *)
            if [[ -n "${dest}" ]]; then
                echo "cleanup takes exactly one <dest-path>" >&2
                return 2
            fi
            dest="$1"
            shift
            ;;
        esac
    done
    if [[ -z "${dest}" ]]; then
        echo "cleanup requires a <dest-path> (the same --dest 'setup' printed)" >&2
        return 2
    fi
    if [[ ! -d "${dest}" ]]; then
        _sfw_log "Nothing to do — ${dest} does not exist."
        return 0
    fi
    dest="$(cd "${dest}" && pwd)"

    # Find the linked worktree(s) under dest: a directory whose .git is a FILE
    # (linked-worktree marker), never a directory (that would be a real clone
    # we should NOT touch).
    local candidates=() d
    for d in "${dest}"/*/; do
        [[ -d "${d}" ]] || continue
        [[ -f "${d}.git" ]] || continue
        candidates+=("${d%/}")
    done

    if [[ "${#candidates[@]}" -gt 1 ]]; then
        echo "❌ found ${#candidates[@]} linked worktrees under ${dest} — refusing to guess which to remove:" >&2
        printf '   %s\n' "${candidates[@]}" >&2
        echo "   Remove the unwanted one(s) by hand (git worktree remove --force <path>) and re-run." >&2
        return 5
    fi

    if [[ "${#candidates[@]}" -eq 1 ]]; then
        local leaf_path="${candidates[0]}" common_dir origin_repo
        common_dir="$(git -C "${leaf_path}" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"
        if [[ -n "${common_dir}" ]]; then
            origin_repo="$(dirname "${common_dir}")"
            _sfw_log "→ removing worktree ${leaf_path} (origin repo: ${origin_repo})"
            git -C "${origin_repo}" worktree remove --force "${leaf_path}" 2>/dev/null \
                || echo "  ⚠ git worktree remove failed for ${leaf_path} — leaving it in place" >&2
            git -C "${origin_repo}" worktree prune 2>/dev/null || true
        else
            echo "  ⚠ could not resolve ${leaf_path}'s origin repo — leaving it in place, remove by hand" >&2
        fi
    fi

    # Unlink sibling symlinks one at a time, by name — never a wildcard rm.
    local unlinked=0
    for d in "${dest}"/*; do
        [[ -L "${d}" ]] || continue
        rm -f -- "${d}" && unlinked=$((unlinked + 1))
    done
    _sfw_log "→ removed ${unlinked} sibling symlink(s)"

    # rmdir, never rm -rf: succeeds only if truly empty, so anything
    # unexpected left behind fails loudly instead of being force-deleted.
    if rmdir "${dest}" 2>/dev/null; then
        _sfw_log "✅ ${dest} fully cleaned up"
    else
        _sfw_log "⚠ ${dest} not empty after cleanup — left in place, remaining contents:"
        ls -la "${dest}" >&2 2>/dev/null || true
    fi
    return 0
}

# ── dispatch ───────────────────────────────────────────────────────────────

main() {
    local cmd="${1:-}"
    case "${cmd}" in
    setup)
        shift
        _sfw_setup "$@"
        ;;
    cleanup)
        shift
        _sfw_cleanup "$@"
        ;;
    -h | --help | "")
        _sfw_usage
        [[ -z "${cmd}" ]] && return 2
        return 0
        ;;
    *)
        echo "Unknown command: ${cmd} (expected 'setup', 'cleanup', or --help)" >&2
        return 2
        ;;
    esac
}

main "$@"
