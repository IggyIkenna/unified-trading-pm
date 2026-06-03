#!/usr/bin/env bash
# setup-tab-worktrees.sh — provision + manage per-slot worktrees for parallel agent tabs.
#
# 3-tier isolation model (see codex/05-infrastructure/per-tab-worktrees.md):
#   Tier 1 — Operator (Ikenna ⊥ Harsh):  separate machines.
#   Tier 2 — Slot (this script's scope): per-slot worktree at .tabs/<N>/<repo>/ on
#            a permanent role-encoded branch.  Slot is durable identity;
#            theme is daily work-split assignment.
#
# Slot-number → role → branch-prefix scheme (operator-configurable):
#   Slots 1..MAIN_SLOT_MAX (default 20) = MAIN agents   → tab/${MAIN_PREFIX}/<N>
#   Slots > MAIN_SLOT_MAX                = WORKER agents → tab/${WORKER_PREFIX}/<N>
#   Harsh  (operator hk): MAIN_PREFIX=hkm  WORKER_PREFIX=hk   → tab/hkm/3 , tab/hk/21
#   Ikenna picks his own (e.g. --operator ii → tab/iim/3 , tab/ii/21, or override
#   WORKER_PREFIX/MAIN_PREFIX env for iggy/ikenna). The prefix alone tells you
#   BOTH operator and role at a glance — no collision since hk ≠ hkm as ref path
#   components.
#   Tier 3 — Sub-agents within a slot:   share the slot's worktree; master agent
#            partitions fan-out + reconciles.
#
# Usage:
#   setup-tab-worktrees.sh --init --slots <N> [--operator <name>]
#       One-time provisioning. Creates N slots; per-repo worktree on tab/<op>/<i>.
#
#   setup-tab-worktrees.sh --add-slot <N> [--operator <name>]
#       Grow fleet by one slot (e.g. 8 → 9). Idempotent (skip-if-exists).
#
#   setup-tab-worktrees.sh --reset-slot <N> [--operator <name>]
#       Prepare slot <N> for new theme. Verify clean → fetch → rebase onto
#       origin/live-defi-rollout. Abort if dirty; operator must commit / stash
#       / discard before retry.
#
#   setup-tab-worktrees.sh --list
#       List configured slots + their current themes (reads slot-theme table
#       from operator orchestrator LEDGER if available).
#
# Idempotent across all sub-commands. Sets PREK_CACHE_DIR per slot via the
# auto-generated .envrc inside each slot worktree (foot-gun #4 mitigation).
#
# Codex SSOT: unified-trading-pm/codex/05-infrastructure/per-tab-worktrees.md
# Plan      : unified-trading-pm/plans/active/per_agent_worktrees_2026_05_10.md

set -euo pipefail

# --- Resolve workspace root ------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
WORKSPACE_ROOT="${UNIFIED_TRADING_WORKSPACE_ROOT:-$(cd "${PM_DIR}/.." && pwd)}"
TABS_DIR="${WORKSPACE_ROOT}/.tabs"
MANIFEST="${PM_DIR}/workspace-manifest.json"
INTEGRATION_BRANCH="live-defi-rollout"

# Per-worktree commit identity (commit_identity_misconfig_fleet_2026_06_03). Provision
# the SAME identity the fix-commit-identity pre-commit hook expects, so the hook is a
# silent no-op rather than a fail-closed block on the first commit:
#   name  = "ikennaigboaka [slot-<N>·<host>]"   email = "ikennaigboaka@gmail.com"
# <host> = VM_NAME on a fleet VM, else "laptop". Worktrees SHARE the main clone's
# .git/config, so per-slot identity REQUIRES extensions.worktreeConfig + git config
# --worktree (a plain `git config user.name` is last-writer-wins across all slots).
# SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Commit attribution".
WORKTREE_HOST="${VM_NAME:-laptop}"
CANON_GIT_EMAIL="ikennaigboaka@gmail.com"

# FM6 (orchestrator_autonomy_audit_remediation): per-repo integration base. Reads
# workspace-manifest.json repositories.<repo>.integration_branch, defaulting to
# ${INTEGRATION_BRANCH} (live-defi-rollout). Per operator decision 2026-06-02,
# EVERY repo (incl. agent-orchestrator) integrates via live-defi-rollout — do NOT
# re-add an agent-orchestrator→main override (it made every AO slot read as diverged;
# the override was removed). Mirrors agent-orchestrator worktree_clean_check.base_branch_for_repo.
base_branch_for_repo() {
    local repo="$1" base=""
    base="$(python3 -c "import json; m=json.load(open('${MANIFEST}')); print(m.get('repositories',{}).get('${repo}',{}).get('integration_branch','') or '')" 2>/dev/null || true)"
    if [[ -n "${base}" ]]; then echo "${base}"; else echo "${INTEGRATION_BRANCH}"; fi
}

# --- Arg parsing -----------------------------------------------------------
OPERATOR="${USER:-unknown}"
# Slots 1..MAIN_SLOT_MAX are main agents; the rest are workers. Branch prefix is
# role-encoded: main → ${MAIN_PREFIX} (default ${OPERATOR}m), worker → ${WORKER_PREFIX}
# (default ${OPERATOR}). Both default-derived from OPERATOR; either can be env-overridden
# (e.g. Ikenna: WORKER_PREFIX=iggy MAIN_PREFIX=iim). Resolved AFTER arg parse (below).
MAIN_SLOT_MAX="${MAIN_SLOT_MAX:-20}"
MODE=""
SLOT_COUNT=""
SLOT_NUM=""

usage() {
    sed -n '2,30p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit "${1:-1}"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --init)         MODE="init";        shift;;
        --add-slot)     MODE="add-slot";    SLOT_NUM="$2"; shift 2;;
        --reset-slot)   MODE="reset-slot";  SLOT_NUM="$2"; shift 2;;
        --list)         MODE="list";        shift;;
        --slots)        SLOT_COUNT="$2";    shift 2;;
        --operator)     OPERATOR="$2";      shift 2;;
        -h|--help)      usage 0;;
        *)              echo "Unknown arg: $1" >&2; usage 1;;
    esac
done

[[ -z "${MODE}" ]] && { echo "ERROR: one of --init / --add-slot / --reset-slot / --list required" >&2; usage 1; }
if [[ "${MODE}" == "init" && -z "${SLOT_COUNT}" ]]; then
    echo "ERROR: --init requires --slots <N>" >&2; exit 1
fi

# Resolve branch prefixes now that --operator is known (env override wins).
WORKER_PREFIX="${WORKER_PREFIX:-${OPERATOR}}"
MAIN_PREFIX="${MAIN_PREFIX:-${OPERATOR}m}"

# --- Helpers ---------------------------------------------------------------
log()  { printf '[setup-tab-worktrees] %s\n' "$*"; }
err()  { printf '[setup-tab-worktrees] ERROR: %s\n' "$*" >&2; }

active_repos() {
    # Emit one repo name per line, active (not archived_into) only.
    python3 - "${MANIFEST}" <<'PY'
import json, sys
with open(sys.argv[1]) as f:
    d = json.load(f)
for k, v in d.get("repositories", {}).items():
    if not v.get("archived_into"):
        print(k)
PY
}

# Branch name encodes operator + role. Slots 1..MAIN_SLOT_MAX are main agents
# (tab/${MAIN_PREFIX}/<N>); higher slots are workers (tab/${WORKER_PREFIX}/<N>).
slot_branch() {
    local n="$1"
    if (( n <= MAIN_SLOT_MAX )); then
        printf 'tab/%s/%s\n' "${MAIN_PREFIX}" "$n"
    else
        printf 'tab/%s/%s\n' "${WORKER_PREFIX}" "$n"
    fi
}
slot_dir()    { printf '%s/%s\n' "${TABS_DIR}" "$1"; }

# Maps $USER/OPERATOR to the per-side orchestrator directory name.
_orchestrator_dir() {
    case "${OPERATOR}" in
        hk)              printf 'harsh_orchestrator';;
        ikennaigboaka)   printf 'ikenna_orchestrator';;
        *)               printf '%s_orchestrator' "${OPERATOR}";;
    esac
}

# Truncate a slot's per-slot ping file to a fresh stub.
# Called by --reset-slot after the worktree rebase succeeds.
# Writes the stub + commits with [reset-slot] tag so CI / cross-side acks
# recognise this as a known reset event.
truncate_slot_ping() {
    local slot="$1"
    local orch_dir ping_file today
    orch_dir="${PM_DIR}/$(_orchestrator_dir)/pings"
    ping_file="${orch_dir}/slot_${slot}.md"
    today="$(date -u +'%Y-%m-%d %H:%M UTC')"

    # Ensure pings directory exists (first --init may race with provision).
    mkdir -p "${orch_dir}"

    cat > "${ping_file}" <<EOF
# Slot ${slot} ping file — re-themed $(date -u +'%Y-%m-%d')

> Doorbell only. One line per active blocker/question (slot N → main) or direction (main → slot N).
> Full Q&A lives in the slot's plan-of-record § "Open questions". Resolved entries removed by main.
> Format: \`[YYYY-MM-DD HH:MM UTC] <agent-tag> — <one-line>\`

[${today}] [main → slot ${slot}] — RE-THEMED via --reset-slot.
Prior theme: TBD (main fills from yesterday's LEDGER + prior plan's DONE block on first read).
New theme: TBD (main fills from today's work-split + plan-of-record + spawn prompt).
EOF
    log "  PING  slot ${slot} ping stub written (${ping_file})"

    # Commit the truncated stub from the PM worktree.
    local pm_wt
    pm_wt="$(slot_dir "${slot}")/unified-trading-pm"
    if [[ -d "${pm_wt}/.git" || -f "${pm_wt}/.git" ]]; then
        git -C "${pm_wt}" add "${ping_file}" 2>/dev/null || true
        if ! git -C "${pm_wt}" diff --cached --quiet; then
            git -C "${pm_wt}" commit -m "[reset-slot] slot ${slot} ping stub reset for re-theme" \
                --no-verify 2>/dev/null && log "  COMMIT slot ${slot} ping stub ([reset-slot] tag)" || \
                log "  WARN  ping stub commit failed — file still written, commit manually."
        fi
    else
        log "  WARN  no PM worktree at ${pm_wt}; ping stub written but NOT committed."
    fi
}

set_worktree_identity() {
    # Provision the canonical per-worktree commit identity (idempotent). Worktrees share
    # the main clone's .git/config, so a plain `git config user.name` is last-writer-wins
    # across all slots — per-slot identity REQUIRES extensions.worktreeConfig (once per
    # repo's shared config) + `git config --worktree`. Produces EXACTLY the name the
    # fix-commit-identity pre-commit hook expects → the hook stays a silent no-op.
    # SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Commit attribution".
    local slot="$1" slot_repo_dir="$2"
    [[ -d "${slot_repo_dir}/.git" || -f "${slot_repo_dir}/.git" ]] || return 0
    git -C "${slot_repo_dir}" config extensions.worktreeConfig true 2>/dev/null || true
    git -C "${slot_repo_dir}" config --worktree user.name "ikennaigboaka [slot-${slot}·${WORKTREE_HOST}]" 2>/dev/null || true
    git -C "${slot_repo_dir}" config --worktree user.email "${CANON_GIT_EMAIL}" 2>/dev/null || true
}

ensure_repo_worktree() {
    # Create worktree for one repo at one slot. Idempotent.
    local repo="$1" slot="$2"
    local branch sibling slot_repo_dir
    branch="$(slot_branch "${slot}")"
    sibling="${WORKSPACE_ROOT}/${repo}"
    slot_repo_dir="$(slot_dir "${slot}")/${repo}"

    if [[ ! -d "${sibling}/.git" ]]; then
        log "  SKIP ${repo} (no sibling clone at ${sibling})"
        return 0
    fi
    if [[ -e "${slot_repo_dir}" ]]; then
        log "  OK   ${repo} (worktree exists)"
        set_worktree_identity "${slot}" "${slot_repo_dir}"  # re-assert identity on re-run (idempotent fix)
        return 0
    fi
    mkdir -p "$(slot_dir "${slot}")"

    # Branch resolution, in priority order:
    #   1. Local branch exists           → reuse it.
    #   2. origin/<branch> exists         → reuse the PUSHED slot branch (so a
    #      fresh VM / worker host lands on the SAME branch state another host
    #      already created + pushed, instead of forking a divergent branch off
    #      the integration branch). This is the case that lets remote hosts pick
    #      up slot branches the operator's laptop created.
    #   3. neither                        → create fresh from origin/<integration>.
    if git -C "${sibling}" show-ref --verify --quiet "refs/heads/${branch}"; then
        git -C "${sibling}" worktree add "${slot_repo_dir}" "${branch}" >/dev/null
        log "  ADD  ${repo} → ${slot_repo_dir} (branch ${branch}, local)"
        set_worktree_identity "${slot}" "${slot_repo_dir}"
        return 0
    fi
    # Refresh remote-tracking refs for both the slot branch + the integration
    # branch before deciding (operator/host may not have fetched in a while).
    local base; base="$(base_branch_for_repo "${repo}")"
    git -C "${sibling}" fetch --quiet origin \
        "+${branch}:refs/remotes/origin/${branch}" 2>/dev/null || true
    git -C "${sibling}" fetch --quiet origin "${base}" 2>/dev/null || true
    if git -C "${sibling}" show-ref --verify --quiet "refs/remotes/origin/${branch}"; then
        git -C "${sibling}" worktree add --track -b "${branch}" \
            "${slot_repo_dir}" "origin/${branch}" >/dev/null
        log "  ADD  ${repo} → ${slot_repo_dir} (branch ${branch}, tracking origin)"
    else
        git -C "${sibling}" worktree add "${slot_repo_dir}" -b "${branch}" \
            "origin/${base}" >/dev/null
        log "  ADD  ${repo} → ${slot_repo_dir} (branch ${branch}, new from ${base})"
    fi
    set_worktree_identity "${slot}" "${slot_repo_dir}"
}

write_slot_envrc() {
    # Per-slot .envrc isolates PREK_CACHE_DIR + sets WORKSPACE_ROOT.
    # Foot-gun #4 mitigation (prek patches stay per-slot, never cross-restore).
    local slot="$1" sd
    sd="$(slot_dir "${slot}")"
    mkdir -p "${sd}/.cache/prek"
    cat > "${sd}/.envrc" <<EOF
# Auto-generated by setup-tab-worktrees.sh — slot ${slot} environment.
# Sourced when shell / Cursor / direnv opens a slot worktree.
export UNIFIED_TRADING_WORKSPACE_ROOT="${sd}"
export PREK_CACHE_DIR="${sd}/.cache/prek"
export SLOT_NUMBER="${slot}"
export SLOT_OPERATOR="${OPERATOR}"
EOF
    log "  ENV  slot ${slot} .envrc written (PREK_CACHE_DIR=${sd}/.cache/prek)"
}

copy_workspace_file() {
    # Materialise the canonical multi-root .code-workspace into the slot dir so the
    # operator can `File → Open Workspace from File` and get the labelled multi-root
    # view, with each `folders[].path` pointing at the slot's OWN worktree.
    #
    # Canonical vs slot copies — path-style contract (SSOT for this divergence):
    #   * Canonical (`${WORKSPACE_ROOT}/unified-trading-system-repos.code-workspace`,
    #     a symlink → unified-trading-pm/cursor-configs/...) uses `../../<repo>` paths,
    #     correct for its real home 2 levels deep under `cursor-configs/` → they resolve
    #     to the repos-root (main worktree). The repos-root symlink view consumes this.
    #   * Slot copies live at `.tabs/N/unified-trading-system-repos.code-workspace` (ONE
    #     level deep). A plain `cp` would carry the `../../<repo>` paths verbatim, which
    #     from `.tabs/N/` resolve to the MAIN worktree's `/repos/<repo>` — NOT the slot's
    #     `.tabs/N/<repo>`. That fails SILENTLY (the dirs exist), so the operator edits in
    #     slot N but the SCM panel / multi-root tree points at the main checkout.
    #   * Fix: rewrite paths to BARE-RELATIVE on copy — `../../<repo>` → `<repo>` and the
    #     workspace-root `../../` → `.` — so they resolve against the slot dir. This is the
    #     style the deployed tab files already use. Settings arrays (git.scanRepositories /
    #     git.ignoredRepositories) hold absolute paths and are copied as-is (harmless).
    local slot="$1" sd src dst
    sd="$(slot_dir "${slot}")"
    src="${WORKSPACE_ROOT}/unified-trading-system-repos.code-workspace"
    dst="${sd}/unified-trading-system-repos.code-workspace"
    if [[ -f "${src}" ]]; then
        # Order matters: collapse the exact `"../../"` workspace-root first, then strip
        # the `"../../` prefix from the remaining `"../../<repo>"` entries. Use a redirect
        # (not `sed -i`) for BSD/GNU portability.
        sed -e 's#"\.\./\.\./"#"."#g' -e 's#"\.\./\.\./#"#g' "${src}" > "${dst}"
        log "  WS   slot ${slot} workspace file written, paths slot-relative (${dst})"
    else
        log "  WS   slot ${slot} skipped (no canonical .code-workspace at ${src})"
    fi
}

provision_slot() {
    local slot="$1"
    log "Provisioning slot ${slot} (branch tab/${OPERATOR}/${slot}) ..."
    write_slot_envrc "${slot}"
    copy_workspace_file "${slot}"
    while IFS= read -r repo; do
        ensure_repo_worktree "${repo}" "${slot}"
    done < <(active_repos)
}

verify_slot_clean() {
    # Walk every repo's worktree in the slot, ensure dirty=0 + ahead/behind=0/0
    # against origin/<integration-branch>. Used by --reset-slot.
    local slot="$1" sd repo dirty ah_be ok=1
    sd="$(slot_dir "${slot}")"
    [[ -d "${sd}" ]] || { err "Slot ${slot} not provisioned (no ${sd}). Run --init or --add-slot first."; return 1; }
    while IFS= read -r repo; do
        local rd="${sd}/${repo}"
        [[ -d "${rd}/.git" || -f "${rd}/.git" ]] || continue
        dirty=$(git -C "${rd}" status --porcelain=v1 2>/dev/null | wc -l | tr -d ' ')
        if [[ "${dirty}" != "0" ]]; then
            err "Slot ${slot} ${repo}: ${dirty} dirty file(s). Commit/stash/discard before --reset-slot."
            git -C "${rd}" status --short
            ok=0
        fi
    done < <(active_repos)
    return $(( ! ok ))
}

rebase_slot() {
    # For each repo's worktree, fetch origin + rebase slot branch onto
    # origin/<integration-branch>. Aborts the whole reset if any repo fails.
    local slot="$1" sd repo branch ok=1
    sd="$(slot_dir "${slot}")"
    while IFS= read -r repo; do
        local rd="${sd}/${repo}"
        [[ -d "${rd}/.git" || -f "${rd}/.git" ]] || continue
        branch="$(slot_branch "${slot}")"
        local base; base="$(base_branch_for_repo "${repo}")"
        if ! git -C "${rd}" fetch --quiet origin "${base}" 2>/dev/null; then
            err "${repo}: fetch failed"; ok=0; continue
        fi
        if ! git -C "${rd}" rebase --quiet "origin/${base}" 2>/dev/null; then
            err "${repo}: rebase onto origin/${base} failed; manual resolution required."
            git -C "${rd}" rebase --abort 2>/dev/null || true
            ok=0; continue
        fi
        log "  REBASED ${repo} on origin/${base}"
    done < <(active_repos)
    return $(( ! ok ))
}

# --- Sub-commands ----------------------------------------------------------
case "${MODE}" in
    init)
        log "Initialising ${SLOT_COUNT} slots for operator '${OPERATOR}' under ${TABS_DIR}/"
        mkdir -p "${TABS_DIR}"
        for ((i=1; i<=SLOT_COUNT; i++)); do
            provision_slot "${i}"
        done
        log "Done. ${SLOT_COUNT} slots ready. Next: assign themes via the daily work-split plan + ${OPERATOR}_orchestrator/LEDGER.md slot↔theme table."
        ;;
    add-slot)
        log "Adding slot ${SLOT_NUM} for operator '${OPERATOR}'"
        mkdir -p "${TABS_DIR}"
        provision_slot "${SLOT_NUM}"
        ;;
    reset-slot)
        log "Resetting slot ${SLOT_NUM} for new theme (operator '${OPERATOR}')"
        verify_slot_clean "${SLOT_NUM}" || { err "Slot ${SLOT_NUM} dirty — see above. Aborting reset."; exit 2; }
        rebase_slot "${SLOT_NUM}" || { err "Slot ${SLOT_NUM} rebase failed. Resolve manually, then re-run."; exit 3; }
        # Re-assert per-worktree commit identity (idempotent) so a re-themed slot keeps the
        # canonical slot·host attribution.
        while IFS= read -r repo; do
            set_worktree_identity "${SLOT_NUM}" "$(slot_dir "${SLOT_NUM}")/${repo}"
        done < <(active_repos)
        truncate_slot_ping "${SLOT_NUM}"
        log "Slot ${SLOT_NUM} reset complete. Ready for new theme assignment."
        ;;
    list)
        log "Slots configured under ${TABS_DIR}/:"
        if [[ ! -d "${TABS_DIR}" ]]; then
            log "  (none — run --init first)"
            exit 0
        fi
        for d in "${TABS_DIR}"/*/; do
            [[ -d "${d}" ]] || continue
            slot="$(basename "${d}")"
            pm_wt="${d}unified-trading-pm"
            if [[ -d "${pm_wt}/.git" || -f "${pm_wt}/.git" ]]; then
                br=$(git -C "${pm_wt}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')
                head_sha=$(git -C "${pm_wt}" rev-parse --short HEAD 2>/dev/null || echo '?')
                log "  slot ${slot}: branch=${br} head=${head_sha}"
            else
                log "  slot ${slot}: (PM worktree missing — partial provision; re-run --add-slot ${slot})"
            fi
        done
        ;;
esac
