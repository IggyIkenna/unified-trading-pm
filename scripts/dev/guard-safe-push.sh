#!/usr/bin/env bash
# Epic: live_defi_rollout_branch_has_no_delete_protection_2026_08_09
# Lifecycle: permanent
# Delete-when: NA
# guard-safe-push.sh — refuse a git push whose refspec has an empty/unset local (source) side.
#
# The `git commit-tree` fallback pattern (the documented recovery for shared-checkout
# contention) pushes an explicit refspec: `git push origin "<sha>:refs/heads/<branch>"`.
# If the source variable is unset/empty, that collapses to `git push origin ":<branch>"`
# — which DELETES the remote branch instead of pushing it. Confirmed near-miss 2026-08-09:
# a round-9 sweep agent force-deleted `live-defi-rollout` this exact way (unset
# commit-message var → empty source side), self-caught + restored same-turn, no data lost,
# but nothing structurally blocked it. Branch-protection rulesets (todo 1/2) cover the
# SERVER side; this guard covers the LOCAL accidental form — defense in depth, two layers.
#
# What it does: for every refspec argument (a token containing `:`) in the git push
# invocation, it checks the LOCAL (source) side:
#   - empty / unset / whitespace  → the deletion form `:<dst>` → REFUSE (exit 2)
#   - non-empty but not resolvable → `git rev-parse --verify` fails → REFUSE (exit 2)
# On a clean refspec set it `exec git push "$@"` — byte-identical behavior to a bare push.
#
# Usage:
#   bash scripts/dev/guard-safe-push.sh -- <git push args...>
#   bash scripts/dev/guard-safe-push.sh --repo <path> -- <git push args...>
#   bash scripts/dev/guard-safe-push.sh --allow-delete -- <git push args...>
#
#   --repo <path>      run git commands in <path> (default: cwd)
#   --allow-delete     permit empty-source (deletion) refspecs — for the ONE intentional
#                      delete path; the default is refuse. Everything after `--` is passed
#                      verbatim to `git push`.
#
# Deliberately NOT enforced here (out of this guard's scope): `--delete`/`-d` (explicit,
# unambiguous intent, not the accidental empty-var class), `--force`/`+` refspecs
# (non-fast-forward pushes of a shared branch are server-blocked by the
# `protect-live-defi-rollout` ruleset; this guard catches the accidental-deletion class).
#
# Test: scripts/quality-gates-base/tests/test-guard-safe-push.sh
# SSOT: codex/05-infrastructure/per-tab-worktrees.md § "git commit-tree fallback (push guard)"
set -uo pipefail

ALLOW_DELETE=0
REPO_DIR=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --allow-delete) ALLOW_DELETE=1; shift ;;
    --repo)
      REPO_DIR="${2:-}"
      [ -n "$REPO_DIR" ] || { echo "guard-safe-push: --repo requires a path" >&2; exit 2; }
      shift 2
      ;;
    --) shift; break ;;
    *)
      echo "guard-safe-push: unknown option '$1' — separate git-push args with '--'" >&2
      exit 2
      ;;
  esac
done

if [ "$#" -eq 0 ]; then
  echo "guard-safe-push: no git push args supplied — use 'guard-safe-push.sh -- <git push args>'" >&2
  exit 2
fi

if [ -n "$REPO_DIR" ]; then
  [ -d "$REPO_DIR/.git" ] || { echo "guard-safe-push: --repo '$REPO_DIR' is not a git repository" >&2; exit 2; }
fi
GIT=(git)
[ -z "$REPO_DIR" ] || GIT=(git -C "$REPO_DIR")

DANGEROUS=0
for tok in "$@"; do
  [[ "$tok" == *:* ]] || continue  # non-refspec token (remote name, -option, bare branch) — not a deletion form

  stripped="${tok#+}"              # strip a leading force-push marker (only valid at position 0)
  src="${stripped%%:*}"

  if [ -z "$src" ]; then
    # `:<dst>` / `:` / `+:<dst>` — empty local side = remote branch DELETION.
    if [ "$ALLOW_DELETE" -eq 1 ]; then
      echo "guard-safe-push: WARN: refspec '$tok' is a deletion (empty source side); allowed via --allow-delete" >&2
    else
      echo "guard-safe-push: REFUSED refspec '$tok' — empty/unset source side = remote branch DELETION (the 2026-08-09 live-defi-rollout bug class). Aborting before git push." >&2
      DANGEROUS=1
    fi
  elif [[ "$src" != *'*'* && "$src" != *'?'* ]]; then
    # Non-empty source must resolve to a real object. Skip glob patterns (a pattern push
    # is never a deletion; `rev-parse` would reject it as a false positive).
    if ! "${GIT[@]}" rev-parse --verify --quiet "$src" >/dev/null 2>&1; then
      echo "guard-safe-push: REFUSED refspec '$tok' — source '$src' does not resolve to a valid git object in ${REPO_DIR:-cwd}." >&2
      DANGEROUS=1
    fi
  fi
done

if [ "$DANGEROUS" -eq 1 ]; then
  echo "guard-safe-push: no push performed. If the deletion was INTENTIONAL, re-run with --allow-delete." >&2
  exit 2
fi

exec "${GIT[@]}" push "$@"
