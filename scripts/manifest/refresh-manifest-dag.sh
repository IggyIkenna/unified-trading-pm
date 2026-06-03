#!/usr/bin/env bash
# refresh-manifest-dag.sh — local, on-demand regenerator for the workspace DAG SVGs.
#
# RETIRED AS A COMMITTING CRON (2026-06-03, item H option a — cicd_contract_hardening_2026_06_01.md)
#   WORKSPACE_MANIFEST_DAG.svg + DATA_FLOW_DAG.svg are now GITIGNORED generated artifacts (untracked
#   + .gitignore'd). That removes the worktree churn at the source, so the dedicated single-writer
#   job this script used to be — regenerate in an isolated LDR worktree, commit, FF-push on a */30
#   cron — is obsolete (it would only ever find "nothing to commit" now). The codex/04-architecture
#   symlinks point at the gitignored root SVGs, which every local `quality-gates.sh` run now
#   regenerates (the former MANIFEST_STATE_WRITER gate on that regen was removed in base-*.sh), so
#   the SVGs stay fresh with no cron and no commits.
#
#   ACTION FOR THE HOST THAT RAN THE OLD CRON: remove the `*/30 ... refresh-manifest-dag.sh --commit`
#   crontab line — it is now a no-op. This script remains only as a manual convenience to regenerate
#   the SVGs on demand (e.g. right after editing workspace-manifest.json, to preview the diagram).
#
# USAGE
#   refresh-manifest-dag.sh            # regenerate both DAG SVGs in place (gitignored output)
#   refresh-manifest-dag.sh --commit   # DEPRECATED no-op: the SVGs are gitignored — nothing to commit
set -euo pipefail

log() { printf '[refresh-manifest-dag %s] %s\n' "$(date -u +%H:%M:%SZ)" "$*"; }

if [[ "${1:-}" == "--commit" ]]; then
    log "NOTE: --commit is retired — DAG SVGs are gitignored generated artifacts (item H). Regenerating locally only."
fi

# Resolve the PM repo from this script's own location (PM/scripts/manifest/).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PY="$(command -v python3 || command -v python)"

for gen in generate_workspace_dag.py generate_data_flow_dag.py; do
    if [[ -f "${PM_DIR}/scripts/manifest/${gen}" ]]; then
        ( cd "${PM_DIR}" && "${PY}" "scripts/manifest/${gen}" ) \
            && log "regenerated via ${gen} (gitignored output)" \
            || log "WARN: ${gen} failed (non-blocking)"
    fi
done
log "done — codex/04-architecture symlinks now resolve to the freshly generated root SVGs"
