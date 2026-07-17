#!/usr/bin/env bash
# Epic: deployment_and_user_management_master (CI/CD cost reduction — B1 self-hosted glue runners)
# Lifecycle: permanent
# Delete-when: the glue host is retired (B2/B3) AND every workflow is back on GitHub-hosted
#
# hosted-baseline.sh — snapshot / restore / audit the PRISTINE GitHub-hosted form of every workflow.
#
# ┌─ WHY (operator 2026-07-16) ────────────────────────────────────────────────────────────────────┐
# │ "take the backup of all the workflows first so that if we ever want to move the workflow from   │
# │  vm to github it would be easy thing ... not just the one we are moving to vm and of the ones   │
# │  we already made some changes from git history so we can preserve them."                        │
# │                                                                                                  │
# │ The self-hosted migration is a ONE-WAY door unless the hosted form is preserved. It is NOT just │
# │ `runs-on:` — flipping a workflow also let us DELETE work the VM already does (actions/          │
# │ setup-python, `pip install` of pre-seeded deps). Reverting `runs-on` ALONE would produce a       │
# │ workflow that runs on a hosted image with no Python set up and no deps installed: broken in a    │
# │ new way. This directory holds the exact bytes that ran on GitHub-hosted, so a revert is a copy,  │
# │ not an archaeology exercise.                                                                     │
# └────────────────────────────────────────────────────────────────────────────────────────────────┘
#
# PROVENANCE IS THE WHOLE POINT. For a workflow we already flipped, the working tree is NOT pristine
# — so `snapshot` reaches into git history for the version immediately BEFORE the first commit that
# introduced `self-hosted, glue` to that file. That parent predates every change this epic made to
# it (the flip was always the first), so it still carries the original runs-on, setup-python and
# install steps. For a workflow we never touched, the working tree IS the baseline.
#
#   ./hosted-baseline.sh snapshot   # (re)build the baseline + MANIFEST.tsv. Idempotent.
#   ./hosted-baseline.sh verify     # audit: baselines still hosted? unflipped ones still in sync?
#   ./hosted-baseline.sh diff [wf]  # what the flip actually changed, per workflow
#   ./hosted-baseline.sh restore <wf>|--all   # put the hosted form back into .github/workflows/
#
# The baseline lives OUTSIDE .github/workflows/ on purpose: GitHub only scans that one directory
# (non-recursively), so a copy here can never be picked up and run as a duplicate workflow.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../.." && pwd)"
WF_DIR="${REPO_ROOT}/.github/workflows"
OUT="${HERE}/hosted-baseline"
MANIFEST="${OUT}/MANIFEST.tsv"
# The marker that identifies a flip. If the flip recipe ever changes, this must change with it.
FLIP_MARKER='self-hosted, glue'

log() { printf '\033[36m[hosted-baseline]\033[0m %s\n' "$*"; }
warn() { printf '\033[33m[hosted-baseline] WARN:\033[0m %s\n' "$*" >&2; }
die() { printf '\033[31m[hosted-baseline] ERROR:\033[0m %s\n' "$*" >&2; exit 1; }

# The commit that FIRST introduced the flip marker to a file, or "" if never flipped.
# --reverse = oldest such commit first; -S counts occurrences, so this is the flip itself.
# NOT `git log | head -1`: under this script's `set -o pipefail`, a file whose marker history
# outgrows head's buffer gets git SIGPIPE'd -> pipeline exit 141 -> `set -e` kills the WHOLE
# script mid-snapshot, leaving a silently TRUNCATED MANIFEST (measured 2026-07-17: died at 43
# of 56 rows, no error printed). Capture everything, then take the first line in-shell.
first_flip_commit() {
  local all
  all="$(git -C "${REPO_ROOT}" log --reverse --format=%H -S"${FLIP_MARKER}" -- "$1" 2>/dev/null || true)"
  printf '%s' "${all%%$'\n'*}"
}

cmd_snapshot() {
  install -d -m 0755 "${OUT}"
  printf 'workflow\tsource\tprovenance_sha\tcaptured_from\n' > "${MANIFEST}"
  local f base first rel n_hist=0 n_live=0
  for f in "${WF_DIR}"/*.yml; do
    [ -e "${f}" ] || continue
    base="$(basename "${f}")"
    rel=".github/workflows/${base}"
    first="$(first_flip_commit "${rel}")"
    if [ -n "${first}" ]; then
      # Flipped: the tree is NOT pristine. Take the parent of the flip commit.
      git -C "${REPO_ROOT}" show "${first}^:${rel}" > "${OUT}/${base}" \
        || die "cannot read ${rel} at ${first}^ — history rewritten? Fix before trusting this baseline."
      printf '%s\thistory\t%s\t%s\n' "${base}" "${first}^" "pre-flip parent of ${first:0:9}" >> "${MANIFEST}"
      n_hist=$((n_hist + 1))
    else
      # Never flipped: the working tree IS the hosted form.
      cp "${f}" "${OUT}/${base}"
      printf '%s\tworktree\t%s\t%s\n' "${base}" "$(git -C "${REPO_ROOT}" rev-parse --short HEAD)" "never flipped" >> "${MANIFEST}"
      n_live=$((n_live + 1))
    fi
  done
  log "snapshot: $((n_hist + n_live)) workflows — ${n_hist} recovered from history (flipped), ${n_live} copied live"
  cmd_verify
}

cmd_verify() {
  [ -d "${OUT}" ] || die "no baseline at ${OUT} — run: $0 snapshot"
  local bad=0 f base rel first drift=0 missing=0

  # 1. A baseline that mentions the flip marker is not a hosted baseline at all.
  for f in "${OUT}"/*.yml; do
    [ -e "${f}" ] || continue
    if grep -q "${FLIP_MARKER}" "${f}"; then
      warn "$(basename "${f}") baseline CONTAINS '${FLIP_MARKER}' — it is not a hosted baseline"
      bad=$((bad + 1))
    fi
    grep -qE '^\s*runs-on:' "${f}" || true # reusable callers legitimately have none
  done

  # 2. Every live workflow must have a baseline (a new workflow added since the last snapshot has none).
  for f in "${WF_DIR}"/*.yml; do
    [ -e "${f}" ] || continue
    base="$(basename "${f}")"
    if [ ! -f "${OUT}/${base}" ]; then
      warn "${base} has NO baseline — added since the last snapshot; re-run: $0 snapshot"
      missing=$((missing + 1))
    fi
  done

  # 3. Drift: an UNFLIPPED workflow's baseline should still equal the live file. If it does not,
  # someone edited the hosted workflow and the baseline is stale — a silent revert-to-wrong-version
  # hazard, which is the one failure mode that would make this whole directory a liability.
  for f in "${WF_DIR}"/*.yml; do
    [ -e "${f}" ] || continue
    base="$(basename "${f}")"
    rel=".github/workflows/${base}"
    [ -f "${OUT}/${base}" ] || continue
    first="$(first_flip_commit "${rel}")"
    if [ -z "${first}" ] && ! diff -q "${f}" "${OUT}/${base}" >/dev/null 2>&1; then
      warn "${base} is NOT flipped but its baseline differs from the live file — baseline is STALE"
      drift=$((drift + 1))
    fi
  done

  if [ "${bad}" -gt 0 ] || [ "${missing}" -gt 0 ] || [ "${drift}" -gt 0 ]; then
    die "verify FAILED: ${bad} non-hosted baseline(s), ${missing} missing, ${drift} stale. Re-run: $0 snapshot"
  fi
  log "verify OK — every baseline is hosted, present, and in sync"
}

cmd_diff() {
  [ -d "${OUT}" ] || die "no baseline — run: $0 snapshot"
  local target="${1:-}" f base
  for f in "${WF_DIR}"/*.yml; do
    [ -e "${f}" ] || continue
    base="$(basename "${f}")"
    [ -n "${target}" ] && [ "${base}" != "${target}" ] && [ "${base}" != "${target}.yml" ] && continue
    [ -f "${OUT}/${base}" ] || continue
    if ! diff -q "${OUT}/${base}" "${f}" >/dev/null 2>&1; then
      printf '\033[1m=== %s (hosted baseline -> live) ===\033[0m\n' "${base}"
      diff -u "${OUT}/${base}" "${f}" || true
    fi
  done
}

# Restore is a COPY, deliberately: it puts back the exact bytes that ran on GitHub-hosted, including
# the setup-python / pip-install steps the flip removed. Reverting `runs-on` alone would leave a
# hosted job with no Python set up — broken in a NEW way, which is the trap this exists to prevent.
cmd_restore() {
  local target="${1:-}"
  [ -n "${target}" ] || die "usage: $0 restore <workflow.yml>|--all"
  [ -d "${OUT}" ] || die "no baseline — run: $0 snapshot"
  if [ "${target}" = "--all" ]; then
    local f n=0
    for f in "${OUT}"/*.yml; do
      [ -e "${f}" ] || continue
      cp "${f}" "${WF_DIR}/$(basename "${f}")"; n=$((n + 1))
    done
    log "restored ${n} workflows to their GitHub-hosted form"
  else
    [ -f "${OUT}/${target}" ] || die "no baseline for '${target}' (see ${MANIFEST})"
    cp "${OUT}/${target}" "${WF_DIR}/${target}"
    log "restored ${target} to its GitHub-hosted form"
  fi
  warn "runs-on is now ubuntu-latest again — the runners will NOT pick these up. Review + commit."
}

case "${1:-verify}" in
  snapshot) cmd_snapshot ;;
  verify)   cmd_verify ;;
  diff)     shift; cmd_diff "${1:-}" ;;
  restore)  shift; cmd_restore "${1:-}" ;;
  *) die "usage: $0 {snapshot|verify|diff [workflow]|restore <workflow>|--all}" ;;
esac
