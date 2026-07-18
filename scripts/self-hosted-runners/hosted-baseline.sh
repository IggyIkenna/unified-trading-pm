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
# PROVENANCE IS THE WHOLE POINT, and it has THREE cases (revised 2026-07-18):
#
#   never flipped        -> the working tree IS the hosted baseline. Copy it.
#   flipped, mechanically -> the flip commit touched only runs-on/comments, so the hosted form is
#                            just the LIVE file with the flip reverted (hosted_form.py). This keeps
#                            current logic.
#   flipped, with logic   -> the flip ALSO changed real steps (cassette-drift-check.yml deleted its
#                            `Set up Python` + `Install uv` because the glue image ships them;
#                            ubuntu-latest still needs them). hosted_form() alone cannot recover
#                            that, so the human judgement is recorded ONCE as a rehost overlay in
#                            hosted-baseline/rehost/ and applied to CURRENT live on every snapshot:
#                              <workflow>.patch  re-add hosted-only steps / revert a glue-only
#                                                workaround to its hosted equivalent
#                              <workflow>.ok     reviewed: hosted_form(live) is already correct
#                                                (e.g. the flip was only a prettier reflow)
#                            With no overlay it falls back to the pre-flip parent, which is
#                            LOGIC-STALE by construction: recorded as such, reported every run, and
#                            restore refuses it without --force.
#   born self-hosted      -> the "flip" commit CREATED the file, so there is no hosted ancestor at
#                            all (ldr-docs-gate.yml). Without an overlay NO baseline is written and
#                            check 2 reports it missing — loudly absent beats quietly wrong.
#
# The original design used the pre-flip parent for ALL flipped workflows, on the assumption that
# "that parent predates every change this epic made to it (the flip was always the first)". That
# assumption expired: measured 2026-07-18, 22 of 32 mechanically-flipped baselines had gone
# logic-stale, so `restore --all` would have rolled back days of work — turning the safety net into
# the hazard it exists to prevent. verify now catches that (check 4).
#
#   ./hosted-baseline.sh snapshot   # (re)build the baseline + MANIFEST.tsv. Idempotent.
#   ./hosted-baseline.sh verify     # audit: hosted? present? unflipped in sync? flipped logic-stale?
#   ./hosted-baseline.sh diff [wf]  # what the flip actually changed, per workflow
#   ./hosted-baseline.sh restore [--force] <wf>|--all   # put the hosted form back
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
# ...but the LITERAL marker is not sufficient on its own. ldr-docs-gate.yml uses
# `runs-on: [self-hosted, Linux, X64, glue]`, which never contains the substring "self-hosted, glue",
# so -S/grep on FLIP_MARKER alone silently classified it "never flipped" and copied it verbatim —
# its "hosted baseline" still pointed at the glue pool (measured 2026-07-18). Detection and
# validation therefore use this REGEX, which matches every self-hosted runs-on form in the fleet
# ([self-hosted, glue], [self-hosted, Linux, X64, glue], [self-hosted, Linux, X64, glue-writer]).
FLIP_RE='runs-on:[[:space:]]*\[self-hosted'

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
  # -G (regex on the diff) not -S (literal string): -S"${FLIP_MARKER}" misses the
  # [self-hosted, Linux, X64, glue] form entirely. See FLIP_RE above.
  all="$(git -C "${REPO_ROOT}" log --reverse --format=%H -G"${FLIP_RE}" -- "$1" 2>/dev/null || true)"
  printf '%s' "${all%%$'\n'*}"
}

# Did the flip commit change ONLY runs-on / comments for this file?
#
# If yes, the live file can be transformed straight back to a CORRECT hosted form, which keeps every
# post-flip logic change. If no, the flip bundled real edits — cassette-drift-check.yml also DELETED
# its `Set up Python` step because the glue image ships Python, and ubuntu-latest still needs it — so
# only the pre-flip history is a trustworthy hosted form, at the cost of being logic-stale.
flip_was_mechanical() {
  local rel="$1" first="$2" n
  n="$(git -C "${REPO_ROOT}" show "${first}" -- "${rel}" 2>/dev/null |
    grep -E '^[+-]' | grep -vE '^(\+\+\+|---)' |
    grep -vcE '^[+-][[:space:]]*(#|runs-on:)')"
  [ "${n:-1}" -eq 0 ]
}

# Derive the hosted form of "$1" into "$2". Returns non-zero when the result is NOT trustworthy.
#
# The self-check matters: flip_was_mechanical only inspects the FIRST flip commit, so
# self-hosted-specific logic added LATER slips past it. rules-alignment-agent.yml is the live
# example — its flip was purely runs-on, but a later commit added an npm global-prefix workaround
# that only applies on the glue pool. If the derived file still mentions the flip marker, there is
# self-hosted-specific content beyond the banner and the derivation cannot be a hosted baseline.
derive_hosted() {
  "${HERE}/hosted_form.py" "$1" >"$2" 2>/dev/null || return 1
  ! grep -q "${FLIP_MARKER}" "$2" && ! grep -qE "${FLIP_RE}" "$2"
}

# ── REHOST OVERLAYS: the recorded human judgement for a flip that carried real logic ───────────
#
# Some flips changed more than runs-on, so hosted_form() alone cannot produce a correct hosted
# baseline (cassette-drift-check's flip DELETED `Set up Python` + `Install uv`, which ubuntu-latest
# still needs). Freezing a hand-written baseline would just rot again, so the judgement is stored as
# an overlay applied to CURRENT live on every snapshot:
#
#   rehost/<workflow>.patch  apply this diff to hosted_form(live) — re-adds hosted-only steps, or
#                            reverts a glue-only workaround to its hosted equivalent
#   rehost/<workflow>.ok     hand-reviewed: hosted_form(live) is already a valid hosted baseline
#                            (e.g. the flip was only a prettier reflow)
#
# A patch that stops applying is a LOUD failure, not a silent one: the workflow drops back to
# history-logic-stale and verify starts reporting it again. That is the intended signal that live
# has moved far enough to need re-reviewing.
REHOST_DIR="${OUT}/rehost"

rehost_hosted() {
  local base="$1" live="$2" dest="$3" tmp
  tmp="$(mktemp)"
  if ! "${HERE}/hosted_form.py" "${live}" >"${tmp}" 2>/dev/null; then
    rm -f "${tmp}"
    return 1
  fi
  if [ -f "${REHOST_DIR}/${base}.patch" ]; then
    if ! patch --quiet --batch --forward -r - "${tmp}" "${REHOST_DIR}/${base}.patch" >/dev/null 2>&1; then
      rm -f "${tmp}"
      return 1
    fi
  elif [ ! -f "${REHOST_DIR}/${base}.ok" ]; then
    rm -f "${tmp}"
    return 1
  fi
  # Validate before it is allowed to become a baseline: no flip marker, and still parseable YAML.
  if grep -q "${FLIP_MARKER}" "${tmp}" || grep -qE "${FLIP_RE}" "${tmp}" ||
    ! python3 -c 'import sys,yaml;yaml.safe_load(open(sys.argv[1]))' "${tmp}" >/dev/null 2>&1; then
    rm -f "${tmp}"
    return 1
  fi
  mv "${tmp}" "${dest}"
}

cmd_snapshot() {
  install -d -m 0755 "${OUT}"
  printf 'workflow\tsource\tprovenance_sha\tcaptured_from\n' > "${MANIFEST}"
  local f base first rel n_hist=0 n_live=0 n_derived=0 n_rehost=0
  for f in "${WF_DIR}"/*.yml; do
    [ -e "${f}" ] || continue
    base="$(basename "${f}")"
    rel=".github/workflows/${base}"
    first="$(first_flip_commit "${rel}")"
    local derived_ok=1
    if [ -n "${first}" ] && flip_was_mechanical "${rel}" "${first}"; then
      derive_hosted "${f}" "${OUT}/${base}.tmp" && derived_ok=0
      rm -f "${OUT}/${base}.tmp"
    fi
    if [ "${derived_ok}" -eq 0 ]; then
      # Flipped, but the flip was PURELY runs-on: derive the hosted form from the LIVE file so the
      # baseline carries current logic. Reaching into history here (the original behaviour) froze the
      # baseline at the flip: measured 2026-07-18, 22 of 32 mechanically-flipped baselines had gone
      # logic-stale, so `restore --all` would have rolled back days of work — the exact
      # revert-to-wrong-version hazard this directory exists to prevent.
      "${HERE}/hosted_form.py" "${f}" > "${OUT}/${base}" \
        || die "hosted_form.py failed on ${rel} — refusing to write a half-baked baseline."
      printf '%s\tderived\t%s\t%s\n' "${base}" "$(git -C "${REPO_ROOT}" rev-parse --short HEAD)" \
        "live minus the mechanical flip ${first:0:9}" >> "${MANIFEST}"
      n_derived=$((n_derived + 1))
    elif [ -n "${first}" ] && rehost_hosted "${base}" "${f}" "${OUT}/${base}"; then
      # Flip carried real logic, but a hand-reviewed rehost overlay exists — apply it to CURRENT
      # live so this baseline tracks the live file instead of freezing at the flip.
      printf '%s\trehosted\t%s\t%s\n' "${base}" "$(git -C "${REPO_ROOT}" rev-parse --short HEAD)" \
        "live + rehost/$([ -f "${REHOST_DIR}/${base}.patch" ] && echo "${base}.patch" || echo "${base}.ok")" >> "${MANIFEST}"
      n_rehost=$((n_rehost + 1))
    elif [ -n "${first}" ]; then
      # Flipped, flip carried real logic, and there is no overlay (or the overlay stopped applying).
      # Only the pre-flip parent is a valid hosted form; it is logic-stale by construction, so record
      # that — cmd_verify reports it and cmd_restore refuses to apply it without --force.
      if ! git -C "${REPO_ROOT}" cat-file -e "${first}^:${rel}" 2>/dev/null; then
        # BORN self-hosted: the "flip" commit CREATED the file, so no hosted ancestor exists and
        # there is nothing to fall back to (ldr-docs-gate.yml, created 2026-07-17 directly on glue).
        # Writing a derived guess here would be a baseline nobody reviewed, so write NOTHING and let
        # check 2 report it as missing — loudly absent beats quietly wrong.
        warn "${base} was BORN self-hosted (no hosted ancestor) and has no rehost overlay — add rehost/${base}.patch or .ok; NO baseline written"
        rm -f "${OUT}/${base}"
        printf '%s\tNO-HOSTED-FORM\t%s\t%s\n' "${base}" "${first:0:9}" \
          "created self-hosted; needs a reviewed rehost overlay" >> "${MANIFEST}"
        continue
      fi
      git -C "${REPO_ROOT}" show "${first}^:${rel}" > "${OUT}/${base}" \
        || die "cannot read ${rel} at ${first}^ — history rewritten? Fix before trusting this baseline."
      printf '%s\thistory-logic-stale\t%s\t%s\n' "${base}" "${first}^" \
        "pre-flip parent of ${first:0:9} (flip bundled logic changes)" >> "${MANIFEST}"
      n_hist=$((n_hist + 1))
    else
      # Never flipped: the working tree IS the hosted form.
      cp "${f}" "${OUT}/${base}"
      printf '%s\tworktree\t%s\t%s\n' "${base}" "$(git -C "${REPO_ROOT}" rev-parse --short HEAD)" "never flipped" >> "${MANIFEST}"
      n_live=$((n_live + 1))
    fi
  done
  log "snapshot: $((n_hist + n_live + n_derived + n_rehost)) workflows — ${n_derived} derived from live (mechanical flip), ${n_rehost} rehosted from live via a reviewed overlay, ${n_hist} recovered from history (UNREVIEWED flip logic), ${n_live} copied live"
  cmd_verify
}

cmd_verify() {
  [ -d "${OUT}" ] || die "no baseline at ${OUT} — run: $0 snapshot"
  local bad=0 f base rel first drift=0 missing=0

  # 1. A baseline that mentions the flip marker is not a hosted baseline at all.
  for f in "${OUT}"/*.yml; do
    [ -e "${f}" ] || continue
    if grep -q "${FLIP_MARKER}" "${f}" || grep -qE "${FLIP_RE}" "${f}"; then
      warn "$(basename "${f}") baseline still carries a self-hosted runs-on or the flip marker — it is not a hosted baseline"
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

  # 4. LOGIC drift on FLIPPED workflows — the blind spot that made this directory a liability.
  # Checks 1-3 only ever asked "is the baseline hosted?" and "are UNFLIPPED baselines in sync?", so a
  # flipped workflow could accumulate any amount of post-flip logic change and still verify clean
  # while its baseline silently rotted. Measured 2026-07-18: 22 of 32 mechanically-flipped baselines
  # were logic-stale, i.e. `restore --all` would have rolled back days of work with no warning.
  for f in "${WF_DIR}"/*.yml; do
    [ -e "${f}" ] || continue
    base="$(basename "${f}")"
    rel=".github/workflows/${base}"
    [ -f "${OUT}/${base}" ] || continue
    first="$(first_flip_commit "${rel}")"
    [ -n "${first}" ] || continue
    _vtmp="$(mktemp)"
    if flip_was_mechanical "${rel}" "${first}" && derive_hosted "${f}" "${_vtmp}"; then
      if ! diff -q "${_vtmp}" "${OUT}/${base}" >/dev/null 2>&1; then
        warn "${base} is FLIPPED and its baseline is LOGIC-STALE (live has changed since) — re-run: $0 snapshot"
        drift=$((drift + 1))
      fi
      rm -f "${_vtmp}"
    elif rehost_hosted "${base}" "${f}" "${_vtmp}" && diff -q "${_vtmp}" "${OUT}/${base}" >/dev/null 2>&1; then
      rm -f "${_vtmp}" # rehost overlay reproduces the baseline from current live — in sync.
    elif [ -f "${REHOST_DIR}/${base}.patch" ] || [ -f "${REHOST_DIR}/${base}.ok" ]; then
      rm -f "${_vtmp}"
      warn "${base} has a rehost overlay that NO LONGER APPLIES (or is out of sync) — re-review rehost/${base}.* against live"
      drift=$((drift + 1))
    else
      rm -f "${_vtmp}"
      # Not auto-fixable: the flip bundled real edits, so the pre-flip parent is the only valid
      # hosted form AND is logic-stale by construction. Report it every run — this is a standing
      # condition a human must resolve by hand, not something snapshot can repair.
      warn "${base} baseline is pre-flip history (the flip bundled logic changes) — LOGIC-STALE by construction; hand-review before any restore"
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
# A baseline recorded as history-logic-stale is a valid HOSTED form but an OLD one: restoring it
# silently reverts every logic change made since the flip. Refuse by default; --force is the
# deliberate "I know, I want the pre-flip version" escape hatch.
restore_is_logic_stale() {
  grep -qE "^$1	history-logic-stale	" "${MANIFEST}" 2>/dev/null
}

cmd_restore() {
  local target="${1:-}" force=0
  if [ "${target}" = "--force" ]; then force=1; target="${2:-}"; fi
  [ "${2:-}" = "--force" ] && force=1
  [ -n "${target}" ] || die "usage: $0 restore [--force] <workflow.yml>|--all"
  [ -d "${OUT}" ] || die "no baseline — run: $0 snapshot"
  if [ "${force}" -eq 0 ]; then
    local stale_n
    stale_n="$(awk -F'\t' 'NR>1 && $2=="history-logic-stale"{n++} END{print n+0}' "${MANIFEST}" 2>/dev/null)"
    if [ "${target}" = "--all" ] && [ "${stale_n:-0}" -gt 0 ]; then
      die "refusing --all: ${stale_n} baseline(s) are logic-stale (flip bundled logic changes) and would REVERT current logic. Review with '$0 diff <wf>', then re-run with --force, or restore the safe ones individually."
    fi
    if [ "${target}" != "--all" ] && restore_is_logic_stale "${target}"; then
      die "refusing ${target}: its baseline is pre-flip history and would REVERT every change since the flip. Review with '$0 diff ${target}', then re-run: $0 restore --force ${target}"
    fi
  fi
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
