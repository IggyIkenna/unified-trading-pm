#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# stash-pile-detect.sh — detect a regrown git-stash pile for ONE repo worktree.
#
# Failure mode (stash_pile_workspace_cleanup_2026_06_03.md Phase 5): `git stash`
# entries accumulate from repeated `git pull --rebase --autostash` cycles whose
# reapply conflicts (per-tab-worktrees.md multi-agent safety — a foreign WIP stash
# is NEVER auto-dropped/auto-applied), so a pile regrows silently between manual
# `audit-stash-pile.sh` sweeps. Measured 2026-07-30 across 4 populated slots on one
# laptop: healthy slots sit at 0; a "still normal churn" slot sits at 10-11 entries
# with a max age of ~10 days; a genuinely regrown pile sits at 33-45 entries with
# entries up to 5-8 weeks old. Thresholds below are picked from that split, not
# invented — see codex/05-infrastructure/per-tab-worktrees.md § "Stash-pile
# regrowth signal" for the full rationale + measured distribution.
#
# This is the DETECTOR/ALERTER ONLY. It never touches `git stash` — no drop, no
# apply, no clear. Remediation stays the existing audit-stash-pile.sh runbook
# (dry-run classify, `--apply` only after a human eyeballs the report).
#
# Detection rule (per repo, evaluated each cron tick):
#   count       = `git stash list | wc -l`
#   oldest_days = age in days of the OLDEST stash entry (stash list is newest-first)
#   WARN        = count > STASH_WARN_COUNT OR oldest_days > STASH_WARN_AGE_DAYS
#
# Output contract:
#   WARN        → prints the human-readable signal payload to stdout, exits 0.
#   not WARN    → prints NOTHING to stdout, exits 0.
#   bad args / not a git repo → message on stderr, exits 2.
# Always cron-safe: read-only (`git stash list` only), never mutates refs or the
# working tree, never fails the caller (every internal git call is `|| echo`
# guarded so a single failure degrades to "not WARN" rather than propagating).
#
# Usage:
#   stash-pile-detect.sh <repo_dir> [--slot N]
# Env-var defaults:
#   STASH_WARN_COUNT      default 15   (entry-count gate)
#   STASH_WARN_AGE_DAYS   default 14   (oldest-entry age gate, days)
#
# Codex SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Stash-pile regrowth signal"
# Plan of record: unified-trading-pm/plans/active/stash_pile_workspace_cleanup_2026_06_03.md (Phase 5)

set -uo pipefail   # NOT set -e: a single failing git call must not abort detection.

WARN_COUNT="${STASH_WARN_COUNT:-15}"
WARN_AGE_DAYS="${STASH_WARN_AGE_DAYS:-14}"
SLOT_ID=""
REPO_DIR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --slot)   SLOT_ID="$2"; shift 2;;
        -h|--help)
            sed -n '2,38p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
            exit 0;;
        -*) echo "Unknown arg: $1" >&2; exit 2;;
        *)  if [[ -z "${REPO_DIR}" ]]; then REPO_DIR="$1"; shift; else echo "Unexpected arg: $1" >&2; exit 2; fi;;
    esac
done

if [[ -z "${REPO_DIR}" ]]; then
    echo "usage: stash-pile-detect.sh <repo_dir> [--slot N]" >&2
    exit 2
fi
if [[ ! -d "${REPO_DIR}" ]]; then
    echo "not a directory: ${REPO_DIR}" >&2
    exit 2
fi

cd "${REPO_DIR}" || { echo "cannot cd: ${REPO_DIR}" >&2; exit 2; }

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "not a git worktree: ${REPO_DIR}" >&2
    exit 2
fi

REPO_NAME="$(basename "$(pwd)")"

count="$(git stash list 2>/dev/null | wc -l | tr -d ' ' || echo 0)"
[[ -n "${count}" ]] || count=0
[[ "${count}" -gt 0 ]] || exit 0   # empty pile → nothing to warn about.

# Oldest entry's commit-epoch (stash list is newest-first, so the last line is
# oldest). A single `git stash list` call, reused for both count and age.
oldest_epoch="$(git stash list --format='%ct' 2>/dev/null | tail -1 || echo "")"
oldest_days=0
now_epoch="$(date -u +%s 2>/dev/null || echo 0)"
if [[ -n "${oldest_epoch}" && "${now_epoch}" -gt 0 ]]; then
    oldest_days=$(( (now_epoch - oldest_epoch) / 86400 ))
    [[ "${oldest_days}" -lt 0 ]] && oldest_days=0
fi

warn=0
[[ "${count}" -gt "${WARN_COUNT}" ]] && warn=1
[[ "${oldest_days}" -gt "${WARN_AGE_DAYS}" ]] && warn=1
[[ "${warn}" -eq 1 ]] || exit 0

slot_label="${SLOT_ID:+slot ${SLOT_ID} / }"
cat <<EOF
STASH PILE REGROWTH — ${slot_label}${REPO_NAME}
count: ${count} entries (warn threshold: >${WARN_COUNT}) | oldest: ${oldest_days} days (warn threshold: >${WARN_AGE_DAYS})
this is a WARNING only — nothing was touched, no stash was read, applied, or dropped
remediation: bash scripts/dev/audit-stash-pile.sh --repo ${REPO_NAME} (dry-run; --apply only after eyeballing the report)
EOF
exit 0
