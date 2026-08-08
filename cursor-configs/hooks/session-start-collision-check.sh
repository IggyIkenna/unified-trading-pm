#!/usr/bin/env bash
# SessionStart hook: warn (never refuse) when a new interactive Claude Code
# session starts inside a `.tabs/<N>` slot that another, still-LIVE process is
# already occupying. Candidate fix 2 of
# plans/active/issues/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md
# -- unblocked 2026-08-08 (operator ruling, ao round-5 apply item 15: "build a
# collision-warning mechanism ... not a hard block"). WARN-ONLY BY DESIGN: an
# operator may deliberately run two sessions in one slot for a review pass, so
# this NEVER exits non-zero and never blocks the session -- SessionStart is a
# non-blocking hook event regardless of exit code, which is exactly the
# semantics wanted here.
#
# Two independent liveness signals, both reused rather than reinvented:
#
#   1. .agent-claim's own `tmux_session` field, confirmed alive via the SAME
#      exact-match `tmux has-session -t "="` check candidate fix 1
#      (scripts/dev/slot-git-status-report.sh::refresh_agent_claim_heartbeat)
#      and the FM8 maker-liveness classifier
#      (agent-orchestrator/server/worktree_clean_check/_liveness.py) both use
#      -- prevents a bare `-t orch-slot-1` from prefix-matching `orch-slot-10`.
#      Fix 1's heartbeat means the claim file's OWN mtime is now a second,
#      independent freshness signal on top of `expires_at` (which for an
#      interactive claim is a flat 12h TTL that nothing else refreshes).
#   2. A live /proc/<pid>/cwd scan for any OTHER `claude` process rooted under
#      this slot dir -- the FM8 "addendum" signal
#      (`_default_proc_cwd_live` in the same `_liveness.py`), which exists
#      precisely because an interactive session may write NO `.agent-claim`
#      at all (nothing currently calls `/api/slots/<N>/claim-interactive`
#      automatically) and run under NO `orch-slot-*` tmux session. This is
#      the literal shape of the original incident: up to 6 concurrent bare
#      `claude` processes pointed at one `.tabs/1` checkout, most without any
#      claim file whatsoever.
#
# Reads the SessionStart JSON payload from stdin (`cwd` field) per Claude
# Code's documented hook contract; falls back to $CLAUDE_PROJECT_DIR / $PWD if
# stdin is empty/unparseable. Never fails the session on a parse error or a
# missing `tmux`/`jq` binary -- every failure path degrades to "say nothing",
# not "block" or "error".

set -uo pipefail  # NOT set -e: any single check failing must not abort the hook.

INPUT="$(cat 2>/dev/null || true)"
START_CWD=""
if [ -n "${INPUT}" ] && command -v jq >/dev/null 2>&1; then
  START_CWD="$(printf '%s' "${INPUT}" | jq -r '.cwd // empty' 2>/dev/null || true)"
fi
[ -z "${START_CWD}" ] && START_CWD="${CLAUDE_PROJECT_DIR:-${PWD}}"

# Derive the slot dir: walk the path for a `.tabs/<N>` component. Anything
# outside a slot worktree (e.g. a root/base clone) has no collision surface
# this check understands -- exit quietly.
SLOT_DIR=""
case "${START_CWD}" in
  */.tabs/*)
    # Strip everything after the first path segment following ".tabs/<N>".
    _rest="${START_CWD#*/.tabs/}"
    _slot_num="${_rest%%/*}"
    case "${_slot_num}" in
      ''|*[!0-9]*) ;;  # not a bare integer -- not a real slot dir, leave SLOT_DIR empty
      *) SLOT_DIR="${START_CWD%%/.tabs/*}/.tabs/${_slot_num}" ;;
    esac
    ;;
esac
[ -z "${SLOT_DIR}" ] && exit 0
[ -d "${SLOT_DIR}" ] || exit 0

CLAIM_FILE="${SLOT_DIR}/.agent-claim"
WARNINGS=()

# --- Signal 1: .agent-claim tmux_session, exact-match liveness ---
if [ -f "${CLAIM_FILE}" ] && command -v jq >/dev/null 2>&1; then
  claim_tmux="$(jq -r '.tmux_session // empty' "${CLAIM_FILE}" 2>/dev/null || true)"
  claim_operator="$(jq -r '.operator // "unknown"' "${CLAIM_FILE}" 2>/dev/null || true)"
  claim_role="$(jq -r '.role // "unknown"' "${CLAIM_FILE}" 2>/dev/null || true)"
  # Our OWN tmux session name, if this hook is itself running inside tmux
  # (env var $TMUX is inherited by the hook subprocess). Absent -> we cannot
  # self-identify against the claim, so this specific signal is skipped
  # (signal 2 below still covers the no-tmux case).
  own_tmux=""
  if [ -n "${TMUX:-}" ] && command -v tmux >/dev/null 2>&1; then
    own_tmux="$(tmux display-message -p '#S' 2>/dev/null || true)"
  fi
  if [ -n "${claim_tmux}" ] && [ "${claim_tmux}" != "${own_tmux}" ] && command -v tmux >/dev/null 2>&1; then
    if tmux has-session -t "=${claim_tmux}" 2>/dev/null; then
      WARNINGS+=("a live .agent-claim (operator=${claim_operator}, role=${claim_role}, tmux_session=${claim_tmux}) already occupies this slot")
    fi
  fi
fi

# --- Signal 2: live /proc/<pid>/cwd scan for another `claude` process under this slot dir ---
if command -v pgrep >/dev/null 2>&1; then
  # Ancestor PIDs of THIS hook invocation (the CLI process that spawned it,
  # its own parent, etc.) must never be reported as "another" process.
  ancestors=" $$ "
  _walk_pid="${PPID:-0}"
  _hops=0
  while [ "${_walk_pid}" != "0" ] && [ "${_walk_pid}" != "1" ] && [ "${_hops}" -lt 10 ]; do
    ancestors="${ancestors}${_walk_pid} "
    _next="$(awk '/^PPid:/{print $2}' "/proc/${_walk_pid}/status" 2>/dev/null || true)"
    [ -z "${_next}" ] && break
    _walk_pid="${_next}"
    _hops=$((_hops + 1))
  done

  SLOT_DIR_REAL="$(readlink -f "${SLOT_DIR}" 2>/dev/null || echo "${SLOT_DIR}")"
  foreign_count=0
  for pid in $(pgrep -f claude 2>/dev/null || true); do
    case "${ancestors}" in *" ${pid} "*) continue ;; esac
    cwd_link="/proc/${pid}/cwd"
    [ -r "${cwd_link}" ] || continue
    resolved="$(readlink -f "${cwd_link}" 2>/dev/null || true)"
    [ -z "${resolved}" ] && continue
    case "${resolved}" in
      "${SLOT_DIR_REAL}"|"${SLOT_DIR_REAL}"/*) foreign_count=$((foreign_count + 1)) ;;
    esac
  done
  if [ "${foreign_count}" -gt 0 ]; then
    WARNINGS+=("${foreign_count} other live process(es) matching 'claude' have their cwd inside this slot (${SLOT_DIR})")
  fi
fi

[ "${#WARNINGS[@]}" -eq 0 ] && exit 0

MSG="SLOT COLLISION WARNING (candidate fix 2, multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md): this session started in ${SLOT_DIR}, which appears to already have a LIVE occupant -- $(IFS='; '; echo "${WARNINGS[*]}"). This is a WARNING ONLY (never a refusal) -- an operator may deliberately run two sessions in one slot for a review pass. But per CLAUDE.md's per-tab-worktrees model, each slot is meant to be ONE agent at a time; two live sessions sharing one checkout risk git index contention (.git/index.lock races), lost/re-fought edits, and wrong commit attribution (a shared .git/config means commits can land under the OTHER session's identity). If this is unintentional, consider moving to an unclaimed slot instead."

if command -v jq >/dev/null 2>&1; then
  jq -n --arg msg "${MSG}" '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $msg}}'
else
  printf '%s\n' "${MSG}"
fi

exit 0
