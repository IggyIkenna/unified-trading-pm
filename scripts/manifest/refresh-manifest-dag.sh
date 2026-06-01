#!/usr/bin/env bash
# refresh-manifest-dag.sh — THE dedicated job that regenerates the workspace DAG
# SVG artifacts and commits them to live-defi-rollout. This is the single controlled
# writer for these generated files outside of quickmerge's promotion-time regen.
#
# WHY THIS EXISTS (root-cause fix, 2026-06-01)
#   WORKSPACE_MANIFEST_DAG.svg + DATA_FLOW_DAG.svg are tracked, generated artifacts,
#   and ci_status lives in the tracked workspace-manifest.json. Previously EVERY
#   agent's quality-gates.sh run regenerated the SVGs and flipped ci_status as a
#   side-effect — touched in 50/50 recent commits. That left every slot worktree
#   perpetually dirty, so the FF-pull cron skipped the slot (`[skip:dirty]`), the
#   branch fell behind LDR, direct-to-LDR pushes stopped fast-forwarding, and work
#   stranded on tab branches (the 70-ahead/68-behind drift).
#
#   The per-QG side-effect is now GATED OFF: base-*.sh + _ci-status-updater.sh only
#   write when MANIFEST_STATE_WRITER=1, which only this job sets. ci_status stays
#   owned by CI dispatch (authoritative); the DAG SVGs are refreshed here + at
#   quickmerge promotion. Slot worktrees stay clean → FF-pull works → no drift.
#
# RUNBOOK (SSOT fields — required by codex Runbook Execution-Owner rule)
#   owner:         planning/orchestrator host cron (one host owns the canonical refresh)
#   cadence:       */30 * * * *  (DAG only needs to track ci_status freshness)
#   verifier:      `git log origin/live-defi-rollout --oneline | grep refresh-workspace-dag`
#                  shows periodic commits; slot worktrees show 0 dirty SVG/json churn.
#   last_executed: see /tmp/refresh-manifest-dag.log on the owning host
#
# INSTALL (on the ONE host that owns the canonical refresh — not every slot):
#   */30 * * * * bash <PM_DIR>/scripts/manifest/refresh-manifest-dag.sh --commit \
#       >> /tmp/refresh-manifest-dag.log 2>&1
#
# USAGE
#   refresh-manifest-dag.sh            # regenerate in an isolated LDR worktree; no commit (dry)
#   refresh-manifest-dag.sh --commit   # regenerate + commit changed SVGs + FF-push to LDR
set -euo pipefail

INTEGRATION_BRANCH="live-defi-rollout"
COMMIT=0
[[ "${1:-}" == "--commit" ]] && COMMIT=1

log() { printf '[refresh-manifest-dag %s] %s\n' "$(date -u +%H:%M:%SZ)" "$*"; }

# Resolve the PM repo from this script's own location (PM/scripts/manifest/).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

git -C "${PM_DIR}" fetch --quiet origin "${INTEGRATION_BRANCH}" || { log "fetch failed (offline?) — abort"; exit 0; }

# Isolated worktree at the LDR tip so this job NEVER depends on (or disturbs) the
# host's slot worktree state. Self-contained: the generators only read
# workspace-manifest.json, no sibling repos required.
WT="$(mktemp -d)/ldr-dag"
cleanup() { git -C "${PM_DIR}" worktree remove --force "${WT}" 2>/dev/null || true; git -C "${PM_DIR}" worktree prune 2>/dev/null || true; }
trap cleanup EXIT
git -C "${PM_DIR}" worktree add --detach "${WT}" "origin/${INTEGRATION_BRANCH}" >/dev/null 2>&1

# Regenerate. MANIFEST_STATE_WRITER=1 marks this as the authorised writer (also lets
# any sourced helper know it may write); the generators themselves just read the json.
PY="$(command -v python3 || command -v python)"
export MANIFEST_STATE_WRITER=1
for gen in generate_workspace_dag.py generate_data_flow_dag.py; do
    if [[ -f "${WT}/scripts/manifest/${gen}" ]]; then
        ( cd "${WT}" && "${PY}" "scripts/manifest/${gen}" ) && log "regenerated via ${gen}" || log "WARN: ${gen} failed (non-blocking)"
    fi
done

# Stage ONLY the generated artifacts by name — never `git add .` (foreign-file safety).
ARTIFACTS=(WORKSPACE_MANIFEST_DAG.svg DATA_FLOW_DAG.svg)
cd "${WT}"
CHANGED=0
for a in "${ARTIFACTS[@]}"; do
    [[ -f "${a}" ]] || continue
    if ! git diff --quiet -- "${a}" 2>/dev/null; then git add "${a}"; CHANGED=1; log "changed: ${a}"; fi
done

if [[ "${CHANGED}" -eq 0 ]]; then log "no DAG changes — nothing to commit"; exit 0; fi
if [[ "${COMMIT}" -eq 0 ]]; then log "dry-run (--commit to push); leaving ${CHANGED} change(s) uncommitted in throwaway worktree"; exit 0; fi

git commit --quiet --no-verify -m "chore(manifest): refresh-workspace-dag — regenerate DAG SVG(s) [skip ci]

Dedicated single-writer job (refresh-manifest-dag.sh). Per-QG-run regeneration is
gated off (MANIFEST_STATE_WRITER) so slot worktrees stay clean for FF-pull."
if git push --quiet origin "HEAD:${INTEGRATION_BRANCH}" 2>/dev/null; then
    log "pushed DAG refresh to ${INTEGRATION_BRANCH} ($(git rev-parse --short HEAD))"
else
    log "WARN: push rejected (LDR advanced mid-run) — next tick retries"
fi
