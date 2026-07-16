#!/usr/bin/env bash
# Epic: deployment_and_user_management_master (CI/CD cost reduction — B1 self-hosted glue runners)
# Lifecycle: permanent
# Delete-when: glue host retired (B2/B3)
#
# refresh-slot-repo.sh — keep the runner slot's OWN clone current with the default branch.
#
# WHY THIS EXISTS: STEP 2b pre-stages ci_status_store.py in the slot so the high-frequency writer does
# NO checkout at all (that's most of the trim). A pre-staged clone that is pinned at install time
# silently drifts from `main`, and the writer then keeps emitting Firestore rows with STALE logic —
# quiet wrongness, which is the bad kind. So: refresh on a timer, and stamp a freshness marker the
# writer can assert on so staleness fails LOUDLY instead of being invisible.
#
# This clone is a READ-ONLY MIRROR — nothing ever commits from it, so `pull --ff-only` must always
# succeed. If it does NOT fast-forward, someone/something dirtied the mirror: fail loudly rather than
# force it (no reset --hard here; that would silently discard whatever went wrong).
set -euo pipefail

: "${RUNNER_BASE:=/opt/github-glue-runners}"
: "${SLOT_REPO:=${RUNNER_BASE}/repo}"
: "${DEFAULT_BRANCH:=main}"
STAMP="${RUNNER_BASE}/repo.refreshed-at"

log() { printf '[slot-refresh] %s\n' "$*"; }

[ -d "${SLOT_REPO}/.git" ] || { echo "[slot-refresh] no clone at ${SLOT_REPO} — run setup-glue-runners.sh install" >&2; exit 1; }

before="$(git -C "${SLOT_REPO}" rev-parse HEAD)"
if ! git -C "${SLOT_REPO}" pull --ff-only origin "${DEFAULT_BRANCH}" --quiet; then
  echo "[slot-refresh] FF-pull FAILED — the mirror is dirty or diverged. NOT forcing." >&2
  echo "[slot-refresh] inspect: git -C ${SLOT_REPO} status && git -C ${SLOT_REPO} log --oneline -3" >&2
  exit 1
fi
after="$(git -C "${SLOT_REPO}" rev-parse HEAD)"

# Freshness marker (epoch seconds). A consumer can assert on age; the timer runs every 10 min, so
# anything older than ~30 min means the refresher itself is broken.
date -u +%s > "${STAMP}"

if [ "${before}" = "${after}" ]; then
  log "already current at ${after:0:9} (${DEFAULT_BRANCH})"
else
  log "advanced ${before:0:9} -> ${after:0:9} (${DEFAULT_BRANCH})"
fi
