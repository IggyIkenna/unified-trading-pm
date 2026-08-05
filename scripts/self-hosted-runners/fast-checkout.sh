#!/usr/bin/env bash
# Epic: deployment_and_user_management_master (CI/CD cost reduction — B1 self-hosted glue runners)
# Lifecycle: permanent
# Delete-when: glue moves to serverless (B2) or a managed runner (B3) and this host is retired
#
# fast-checkout.sh — hardlink-copy the runner slot's pre-staged mirror (RUNNER_BASE/repo,
# maintained by refresh-slot-repo.sh on github-glue-slot-refresh.timer) into place instead of
# a cold `actions/checkout@v4` network clone, when a fresh mirror exists.
#
# WHY: measured 2026-08-05 (fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md +
# an independent analysis from Harsh) — ~1.7 GB written per glue qg-slices checkout, x up to 25
# concurrent runs competing for the same EBS volume, was a real contributor to the disk-I/O
# saturation that caused that day's incident. The slot mirror already exists and is refreshed
# on a timer FOR EVERY POOL, but nothing consumed it — actions/checkout@v4 has no native
# `--reference`/mirror-aware mode, so every job re-cloned cold regardless.
#
# TWO REAL BUGS caught live on the first canary run (2026-08-05), both fixed here — recorded so
# neither regresses:
#   1. RUNNER_BASE does NOT propagate into the job's own environment. It's set via the wrapper's
#      systemd EnvironmentFile (glue-runner-run.sh's process env), but self-hosted runners do not
#      leak arbitrary host env vars into job `run:` steps — only GHA-native vars (GITHUB_*,
#      RUNNER_WORKSPACE, etc.) are guaranteed present. Trusting `${RUNNER_BASE:-default}` silently
#      resolved to the WRONG (untagged) pool path on every tagged pool, so the mirror was never
#      found at all. Fixed: derive RUNNER_BASE from GITHUB_WORKSPACE's own path structure instead
#      (GHA always sets this correctly) — see derive_runner_base() below.
#   2. `rm -rf "${TARGET}"` where TARGET == the shell's OWN current working directory (GHA sets a
#      `run:` step's cwd to $GITHUB_WORKSPACE by default) yanks the directory out from under the
#      running shell — every subsequent command fails with "fatal: Unable to read current working
#      directory". Fixed: cd to TARGET's parent BEFORE any removal, never operate from inside a
#      directory this script is about to delete.
#
# SAFETY MODEL (this is what makes it safe to ship fleet-wide immediately, not just to a
# canaried repo): the mirror is UNEVENLY maintained across the fleet today (confirmed live —
# some pools' refresh timer isn't even installed, staleness ranged 5 minutes to 47 hours) and
# is a plain fast-forward mirror of the DEFAULT branch only, not every ref this workflow might
# need to check out (PR merge refs, other branches). So the fast path is opportunistic, not
# assumed: falls back to a normal `git clone` for ANY of —
#   - no mirror at the derived RUNNER_BASE (expected on ubuntu-latest, or a repo with no pool yet)
#   - mirror older than MAX_STALENESS_SECONDS (its own refresher may be broken/disabled)
#   - the hardlink-copy itself fails (cross-filesystem, permissions)
#   - the post-copy fetch/checkout of the actual target ref fails
#   - VERIFIED HEAD MISMATCH: after checkout, `git rev-parse HEAD` MUST equal the exact SHA
#     the caller asked for — this is the hard backstop against ever silently building the
#     wrong tree. A mismatch is treated as a fast-path FAILURE (fall back to plain clone),
#     never a warning-and-continue.
# Every failure mode degrades to EXACTLY today's behavior — a job never fails or produces a
# wrong checkout because of this script; worst case is "no speedup this run."
#
# Usage: fast-checkout.sh <target-dir>
#   Env (from the calling workflow step): GITHUB_REPOSITORY, GITHUB_SHA, GITHUB_REF,
#   GITHUB_WORKSPACE (all set by GitHub Actions automatically), GH_TOKEN (the job's
#   github.token — needed to replicate actions/checkout@v4's credential setup, see below).
set -euo pipefail

TARGET="${1:?usage: fast-checkout.sh <target-dir>}"
: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY not set (expected inside a GitHub Actions job)}"
: "${GITHUB_SHA:?GITHUB_SHA not set}"
: "${GITHUB_REF:?GITHUB_REF not set}"
: "${GH_TOKEN:?GH_TOKEN not set — needed to configure git credentials for later steps}"

# BUG 2 FIX: move off TARGET before anything might rm -rf it — GHA's default cwd for a `run:`
# step IS $GITHUB_WORKSPACE (== TARGET here), so removing it while it's still the shell's cwd
# breaks every subsequent command's getcwd(), not just the ones touching TARGET directly.
cd "$(dirname "${TARGET}")"

log() { printf '[fast-checkout] %s\n' "$*"; }

# BUG 1 FIX: derive RUNNER_BASE from GITHUB_WORKSPACE's own structure instead of trusting an
# env var that doesn't actually reach this process. This fleet's runner registration always
# passes work_folder="_work" (glue-runner-run.sh), so GITHUB_WORKSPACE is always
# <RUNNER_BASE>/<INSTANCE>/_work/<REPO>/<REPO> — strip 4 trailing path components to recover it.
derive_runner_base() {
  dirname "$(dirname "$(dirname "$(dirname "$1")")")"
}
RUNNER_BASE="$(derive_runner_base "${TARGET}")"

# Replicates actions/checkout@v4's own credential setup (an `http.<url>/.extraheader` with a
# base64 basic-auth token) so any LATER step in the job that does its own git operation
# (push, fetch a private dep) keeps working exactly as it would after a normal checkout —
# without this, replacing the checkout step would silently break any such step.
configure_git_credentials() {
  local dir="$1"
  local basic_auth
  basic_auth="$(printf 'x-access-token:%s' "${GH_TOKEN}" | base64 -w0 2>/dev/null || printf 'x-access-token:%s' "${GH_TOKEN}" | base64)"
  git -C "${dir}" config --local "http.https://github.com/.extraheader" "AUTHORIZATION: basic ${basic_auth}"
}

MIRROR="${RUNNER_BASE}/repo"
STAMP="${RUNNER_BASE}/repo.refreshed-at"
MAX_STALENESS_SECONDS=1800 # matches setup-glue-runners.sh's own "STALE — refresher broken?" threshold
REPO_URL="https://github.com/${GITHUB_REPOSITORY}.git"

plain_clone() {
  log "plain clone path: ${REPO_URL} @ ${GITHUB_SHA}"
  rm -rf "${TARGET}"
  git clone --quiet --no-checkout "${REPO_URL}" "${TARGET}"
  configure_git_credentials "${TARGET}"
  git -C "${TARGET}" fetch --quiet --depth=2 origin "${GITHUB_REF}"
  git -C "${TARGET}" checkout --force --quiet "${GITHUB_SHA}"
}

log "derived RUNNER_BASE=${RUNNER_BASE} from GITHUB_WORKSPACE=${TARGET}"

# ── Eligibility: mirror present and fresh ────────────────────────────────────────────────────
if [ ! -d "${MIRROR}/.git" ]; then
  log "no mirror at ${MIRROR} — plain clone (expected on ubuntu-latest / a repo without a pool yet)"
  plain_clone
  exit 0
fi

if [ ! -f "${STAMP}" ]; then
  log "mirror has no freshness stamp (${STAMP}) — treating as unverified, plain clone"
  plain_clone
  exit 0
fi

stamp_val="$(cat "${STAMP}" 2>/dev/null || echo 0)"
now="$(date -u +%s)"
age=$(( now - stamp_val ))
if [ "${age}" -gt "${MAX_STALENESS_SECONDS}" ]; then
  log "mirror stale (${age}s > ${MAX_STALENESS_SECONDS}s — its refresher may be broken) — plain clone"
  plain_clone
  exit 0
fi

# ── Fast path: hardlink-copy + incremental fetch of the exact ref ───────────────────────────
log "mirror fresh (${age}s old) — attempting hardlink-copy fast path"
rm -rf "${TARGET}"
if ! cp -al "${MIRROR}" "${TARGET}" 2>/dev/null; then
  log "hardlink-copy failed (cross-filesystem? permissions?) — plain clone"
  plain_clone
  exit 0
fi

git config --global --add safe.directory "${TARGET}" 2>/dev/null || true
# Overwrite whatever credential header the mirror clone carried (possibly stale/different-
# scoped) with THIS job's own fresh token before any fetch that needs auth.
configure_git_credentials "${TARGET}"

if ! git -C "${TARGET}" fetch --quiet --depth=2 origin "${GITHUB_REF}" 2>/dev/null; then
  log "post-copy fetch of ${GITHUB_REF} failed — plain clone"
  plain_clone
  exit 0
fi

if ! git -C "${TARGET}" checkout --force --quiet "${GITHUB_SHA}" 2>/dev/null; then
  log "post-copy checkout of ${GITHUB_SHA} failed — plain clone"
  plain_clone
  exit 0
fi

git -C "${TARGET}" clean -fdx --quiet

# Hard backstop: never trust the fast path without verifying it actually built the exact tree
# the caller asked for.
actual_head="$(git -C "${TARGET}" rev-parse HEAD)"
if [ "${actual_head}" != "${GITHUB_SHA}" ]; then
  log "VERIFICATION FAILED: HEAD=${actual_head} != expected ${GITHUB_SHA} — plain clone"
  plain_clone
  exit 0
fi

log "OK via hardlink-copy fast path (verified HEAD=${actual_head})"
