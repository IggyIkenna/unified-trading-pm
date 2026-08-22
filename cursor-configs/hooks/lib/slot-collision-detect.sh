#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# slot-collision-detect.sh -- THE single source of truth for "is another live Claude session
# occupying this `.tabs/<N>` slot?". Sourceable as a library and runnable as a CLI.
#
# WHY THIS EXISTS AS A LIBRARY. This detection previously lived inline in exactly one consumer
# (session-start-collision-check.sh), where it read ONLY `/proc/<pid>/cwd` -- and macOS has no
# `/proc` at all. On the operator laptop where the collision incident was actually measured, the
# scan was therefore a structural no-op: it never looked for a peer, it just always concluded
# there wasn't one (fixed 2026-08-11, unified-trading-pm@83debfb40a). A second consumer arrived
# immediately afterwards (the PreToolUse guard), and copy-pasting the scan into it is precisely
# how a platform gap like that survives unnoticed in one copy while being fixed in the other.
# One implementation, two callers, one place to fix.
#
# CONTRACT: every function degrades to "no signal" rather than erroring. A caller must be able to
# treat any failure as "no collision detected" and proceed -- these are advisory signals feeding
# guardrails, and a detector that throws is worse than one that stays quiet.
#
# CLI:
#   slot-collision-detect.sh slot-dir <cwd>        -> prints the .tabs/<N> slot dir, or nothing
#   slot-collision-detect.sh foreign-pids <slot>   -> prints live foreign claude PIDs, one per line
#   slot-collision-detect.sh is-linked-worktree <dir> -> exit 0 if <dir> is a linked git worktree

# _ppid_of <pid> -> ppid on stdout, empty on failure. /proc first (fast, Linux), `ps` fallback
# (works on both, and is the ONLY option on macOS).
_ppid_of() {
  local pid="$1" v
  if [ -r "/proc/${pid}/status" ]; then
    v="$(awk '/^PPid:/{print $2}' "/proc/${pid}/status" 2>/dev/null || true)"
    [ -n "${v}" ] && {
      printf '%s' "${v}"
      return 0
    }
  fi
  v="$(ps -o ppid= -p "${pid}" 2>/dev/null | tr -d ' ')"
  [ -n "${v}" ] && printf '%s' "${v}"
}

# _cwd_of <pid> -> resolved absolute cwd on stdout, empty on failure. /proc first (Linux); lsof
# fallback (macOS/BSD -- no /proc cwd link exists there at all, so this is the only way to ask a
# macOS host "what directory is this OTHER process running in").
_cwd_of() {
  local pid="$1" cwd_link="/proc/$1/cwd" v
  if [ -r "${cwd_link}" ]; then
    v="$(readlink -f "${cwd_link}" 2>/dev/null || true)"
    [ -n "${v}" ] && {
      printf '%s' "${v}"
      return 0
    }
  fi
  if command -v lsof >/dev/null 2>&1; then
    # `lsof -a -d cwd -p <pid> -Fn` emits a field-per-line format; the path line is prefixed
    # with 'n'. Same-user processes need no elevated privileges to query on macOS.
    v="$(lsof -a -d cwd -p "${pid}" -Fn 2>/dev/null | awk '/^n/{sub(/^n/,""); print; exit}')"
    [ -n "${v}" ] && printf '%s' "${v}"
  fi
}

# slot_dir_for <cwd> -> the `.tabs/<N>` slot dir containing <cwd>, or empty. Anything outside a
# slot worktree (a root/base clone, a private worktree under /tmp) has no collision surface this
# check understands, and correctly yields nothing.
slot_dir_for() {
  local cwd="$1" rest slot_num
  case "${cwd}" in
    */.tabs/*) ;;
    *) return 0 ;;
  esac
  rest="${cwd#*/.tabs/}"
  slot_num="${rest%%/*}"
  case "${slot_num}" in
    '' | *[!0-9]*) return 0 ;; # not a bare integer -- not a real slot dir
  esac
  printf '%s' "${cwd%%/.tabs/*}/.tabs/${slot_num}"
}

# _ancestor_pids -> space-delimited " pid pid " of THIS process and its ancestors. A liveness
# check that matches its own process tree reports a collision with itself; that self-match is the
# defect this walk exists to prevent, and it is the same class as the `pgrep`-substring trap
# recorded in /codex/12-agent-workflow/async-wait-and-poll-discipline.md.
_ancestor_pids() {
  local acc=" $$ " walk="${PPID:-0}" hops=0 next
  while [ "${walk}" != "0" ] && [ "${walk}" != "1" ] && [ "${hops}" -lt 10 ]; do
    acc="${acc}${walk} "
    next="$(_ppid_of "${walk}")"
    [ -z "${next}" ] && break
    walk="${next}"
    hops=$((hops + 1))
  done
  printf '%s' "${acc}"
}

# _cwd_of_batch <pid> [<pid> ...] -> "<pid> <cwd>" pairs on stdout, one per line, for every pid
# whose cwd could be resolved. Tries /proc per-pid first (no subprocess, cheap even for many
# pids); whatever's left over (macOS, or a /proc read that failed) is resolved with exactly ONE
# `lsof -p pid1,pid2,...` call instead of one `lsof` invocation per leftover pid -- under host
# load, N separate `lsof` fork+execs is what pushed foreign_claude_pids's walk past the caller's
# 10s budget (measured load 48, then 164 twenty minutes later --
# plans/active/issues/slot_collision_guard_bats_fails_open_under_host_load_2026_08_15.md).
_cwd_of_batch() {
  local pid v cwd_link leftover=()
  for pid in "$@"; do
    cwd_link="/proc/${pid}/cwd"
    if [ -r "${cwd_link}" ]; then
      v="$(readlink -f "${cwd_link}" 2>/dev/null || true)"
      if [ -n "${v}" ]; then
        printf '%s %s\n' "${pid}" "${v}"
        continue
      fi
    fi
    leftover+=("${pid}")
  done
  [ "${#leftover[@]}" -eq 0 ] && return 0
  command -v lsof >/dev/null 2>&1 || return 0
  # `-Fn` emits one `p<pid>` line per matched process followed by the `n<path>` line(s) for its
  # matched fds; `-d cwd` restricts matches to exactly the cwd fd, so at most one `n` line follows
  # each `p` line -- the awk below just needs to remember the most recent `p` to label each `n`.
  lsof -a -d cwd -p "$(
    IFS=,
    printf '%s' "${leftover[*]}"
  )" -Fn 2>/dev/null | awk '
    /^p/ { pid = substr($0, 2); next }
    /^n/ { if (pid != "") print pid, substr($0, 2) }
  '
}

# foreign_claude_pids <slot_dir> -> PIDs (one per line) of live `claude` processes whose cwd is
# inside <slot_dir>, EXCLUDING this process's own ancestry. Empty output means no collision.
foreign_claude_pids() {
  local slot_dir="$1" ancestors slot_real pid resolved candidates=()
  [ -n "${slot_dir}" ] || return 0
  command -v pgrep >/dev/null 2>&1 || return 0
  ancestors="$(_ancestor_pids)"
  slot_real="$(readlink -f "${slot_dir}" 2>/dev/null || echo "${slot_dir}")"
  # `command -p` (POSIX default PATH, bypasses any PATH-prepended wrapper) rather than a
  # bare `pgrep` call: every AO-spawned worker pane has scripts/hooks/pkill-guard-bin/
  # prepended to PATH (tmux_spawn.py; see per-tab-worktrees.md's pkill/pgrep cross-slot-
  # kill guard), which REFUSES any bare name-only pattern -- including THIS call, since a
  # slot-agnostic "claude" search across every peer slot has no per-slot discriminator by
  # design (that's the whole point of a cross-slot collision scan). On a guarded pane the
  # bare form silently returns zero candidates every time, independent of host load --
  # confirmed by direct reproduction 2026-08-22 (misdiagnosed for a week as the load-driven
  # lsof-timeout flakiness this file's own header describes; that mechanism is real for the
  # PYTHON guard's lsof calls, but this bash-side pgrep call was unconditionally refused
  # regardless of load). This scan is read-only detection, never a kill, so the guard's own
  # documented bypass ("command pgrep ...", printed in its refusal message) is the correct,
  # safe fix -- not a workaround around the guard's actual purpose.
  # See plans/active/issues/slot_collision_guard_bats_fails_open_under_host_load_2026_08_15.md.
  for pid in $(command -p pgrep -f claude 2>/dev/null || true); do
    case "${ancestors}" in *" ${pid} "*) continue ;; esac
    candidates+=("${pid}")
  done
  [ "${#candidates[@]}" -eq 0 ] && return 0
  while read -r pid resolved; do
    [ -z "${pid}" ] && continue
    case "${resolved}" in
      "${slot_real}" | "${slot_real}"/*) printf '%s\n' "${pid}" ;;
    esac
  done < <(_cwd_of_batch "${candidates[@]}")
}

# is_linked_worktree <dir> -> exit 0 iff <dir> is inside a LINKED git worktree (not the main
# checkout). In a linked worktree `--git-dir` points at `.git/worktrees/<name>` while
# `--git-common-dir` points at the shared `.git`; in the main checkout they are the same path.
# This is the general test for "this command runs against a private index", so it covers
# ship-from-worktree.sh, quickmerge's isolation, and any hand-rolled worktree equally.
is_linked_worktree() {
  local dir="${1:-.}" gd cd_
  gd="$(git -C "${dir}" rev-parse --absolute-git-dir 2>/dev/null || true)"
  [ -n "${gd}" ] || return 1
  cd_="$(git -C "${dir}" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"
  [ -n "${cd_}" ] || return 1
  [ "${gd}" != "${cd_}" ]
}

# workspace_root_for <path> -> the nearest ancestor of <path> that directly contains a `.tabs`
# subdirectory, or empty if none is found within a bounded walk. Purely path-based -- no
# dependency on $CLAUDE_PROJECT_DIR (which reflects wherever the CALLING session itself is
# rooted -- a slot, the bare workspace, or a single repo -- not necessarily the multi-repo
# container a given TARGET path lives under). Bounded at 20 hops for the same reason
# `_ancestor_pids` is: a detector that can loop forever on a malformed input is worse than one
# that gives up and reports nothing.
workspace_root_for() {
  local dir hops=0
  dir="$(dirname -- "$1" 2>/dev/null)" || return 0
  while [ "${dir}" != "/" ] && [ "${hops}" -lt 20 ]; do
    [ -d "${dir}/.tabs" ] && {
      printf '%s' "${dir}"
      return 0
    }
    dir="$(dirname -- "${dir}")"
    hops=$((hops + 1))
  done
}

# bare_root_repo_with_slot_sibling <path> -> prints "<workspace_root> <repo>" iff <path> is a
# BARE-ROOT checkout path (`<workspace_root>/<repo>/...`, no `.tabs` component) for a <repo>
# that has at least one live `.tabs/*/<repo>` sibling -- i.e. slots are actively used for this
# repo, so a bare-root write is anomalous rather than "this repo has no slot workflow at all".
# Empty otherwise, including when <path> is already inside a slot. This is the INVERSE of
# `slot_dir_for` -- that answers "which slot is this path in"; this answers "this path is
# OUTSIDE every slot, but should it be".
bare_root_repo_with_slot_sibling() {
  local path="$1" root rest repo cand
  case "${path}" in
    */.tabs/*) return 0 ;; # already in a slot -- nothing to warn about
  esac
  root="$(workspace_root_for "${path}")"
  [ -n "${root}" ] || return 0
  case "${path}" in
    "${root}"/*) ;;
    *) return 0 ;;
  esac
  rest="${path#"${root}"/}"
  repo="${rest%%/*}"
  [ -n "${repo}" ] || return 0
  for cand in "${root}"/.tabs/*/"${repo}"; do
    [ -d "${cand}" ] && {
      printf '%s %s' "${root}" "${repo}"
      return 0
    }
  done
}

# CLI dispatch -- only when executed directly, never when sourced.
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  case "${1:-}" in
    slot-dir) slot_dir_for "${2:-}" ;;
    foreign-pids) foreign_claude_pids "${2:-}" ;;
    is-linked-worktree) is_linked_worktree "${2:-.}" ;;
    bare-root-repo) bare_root_repo_with_slot_sibling "${2:-}" ;;
    *)
      echo "usage: $(basename "$0") {slot-dir <cwd>|foreign-pids <slot>|is-linked-worktree <dir>|bare-root-repo <path>}" >&2
      exit 64
      ;;
  esac
fi
