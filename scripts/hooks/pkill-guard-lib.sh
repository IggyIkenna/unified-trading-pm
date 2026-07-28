#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# pkill-guard-lib.sh — the SINGLE derivation of the pkill mechanical safety guard.
#
# Root incident: RECURRED TWICE the same day (2026-07-28), across two different slots,
# despite a prose-only RULES.md addendum from the first occurrence already being live and
# read at boot — see plans/active/issues/pkill_broad_pattern_cross_slot_qg_kill_2026_07_28.md.
# Every slot invokes shared scripts (e.g. `bash scripts/quality-gates.sh --no-fix`) with
# IDENTICAL argv, so a bare `pkill -f "quality-gates.sh"` / `pkill quality-gates.sh` matches
# EVERY slot's process on the shared host, not just the caller's own — enforcement had to
# move from documentation to a mechanical guard.
#
# Contract: sourcing this file defines a `pkill` shell FUNCTION that shadows the real
# /usr/bin/pkill for the sourcing shell. It REFUSES an invocation that lacks a
# slot-specific discriminator and otherwise passes straight through to the real binary
# (`command pkill "$@"`) — legitimate exact-PID/PGID or cwd-scoped usage is unaffected.
#
# Deliberately does NOT wrap `pgrep` — pgrep only LISTS matching PIDs, it never kills
# anything, so guarding it would block harmless diagnostics without closing any actual
# risk (the incidents were both pkill-driven kills, never a pgrep lookup).
# Deliberately does NOT wrap plain `kill <pid>` — that IS the exact-PID-only pattern this
# guard exists to push workers toward; blocking it would defeat the fix.
#
# A discriminator is EITHER of:
#   (a) a numeric target after -g/-P/-s (process-group / parent-pid / session-id) — an
#       exact number the caller must already have captured, not a name/regex pattern.
#       (-G/-U, real-group/uid, are deliberately EXCLUDED: every slot runs as the same
#       host user, so those would match host-wide too and are not a real scoping signal.)
#   (b) a pattern argument (after -f, or a bare trailing name) that embeds an absolute
#       `.tabs/<N>/` worktree path — and if the caller's OWN slot is derivable from $PWD,
#       it must be THAT slot's path (so slot 5 can't "safely" pattern-kill slot 2's
#       worktree either — only your own).
#
# Sourced by the managed ~/.bashrc / ~/.zshrc block installed by
# scripts/dev/install-pkill-guard-shell-env.sh (same idempotent-block convention as
# install-qg-governor-shell-env.sh / install-uv-cache-shell-env.sh — see those for the
# installer pattern this guard's installer mirrors). Also sourced directly by
# scripts/hooks/tests/test-pkill-guard.sh for regression coverage.

_pkill_guard_caller_slot() {
  # Absolute cwd of the CALLING shell → slot number, or "" if not inside a .tabs/<N> tree.
  # Mirrors slot-identity-lib.sh's PATH-based slot-label derivation (single convention).
  printf '%s' "${PWD:-}" | sed -nE 's#.*/\.tabs/([0-9]+)(/.*)?$#\1#p'
}

_pkill_guard_has_discriminator() {
  # Returns 0 (true) iff the given pkill argv ($@) carries a slot-specific discriminator.
  local caller_slot
  caller_slot="$(_pkill_guard_caller_slot)"

  local prev="" arg
  for arg in "$@"; do
    case "$prev" in
      -g | -P | -s)
        [[ "$arg" =~ ^[0-9]+$ ]] && return 0
        ;;
    esac
    if [[ "$arg" == *".tabs/"[0-9]*"/"* ]]; then
      if [ -n "$caller_slot" ]; then
        case "$arg" in
          *".tabs/${caller_slot}/"*) return 0 ;;
        esac
      else
        # Not running from inside a slot worktree (e.g. a root clone / the planning VM) —
        # can't check "is it MY slot", so any absolute slot-worktree-scoped pattern counts.
        return 0
      fi
    fi
    prev="$arg"
  done
  return 1
}

pkill() {
  if [ "$#" -eq 0 ]; then
    command pkill # no pattern at all — let the real binary print its own usage error
    return $?
  fi
  if _pkill_guard_has_discriminator "$@"; then
    command pkill "$@"
    return $?
  fi
  cat >&2 <<'EOF'
REFUSED: pkill pattern has no slot-specific discriminator.
Every slot invokes shared scripts with IDENTICAL argv (e.g. quality-gates.sh --no-fix), so
an unscoped `pkill -f <pattern>` / `pkill <name>` is host-wide, not slot-scoped, and can
silently kill a SIBLING slot's live QG/pytest run (confirmed TWICE: 2026-07-28).
Fix — kill the EXACT thing you launched, e.g.:
    kill <pid>                        # the exact PID you captured via $! at launch time
    pkill -g <pgid>                   # an exact process group you captured
    pkill -f ".tabs/<N>/.*<name>"     # YOUR OWN slot's absolute worktree path
See: plans/active/issues/pkill_broad_pattern_cross_slot_qg_kill_2026_07_28.md
EOF
  return 1
}
