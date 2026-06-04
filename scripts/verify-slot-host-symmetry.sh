#!/usr/bin/env bash
# verify-slot-host-symmetry.sh — does this host (operator laptop / VM / Harsh laptop)
# satisfy the local↔VM slot-host symmetry contract from CLAUDE.md § "Local slot host
# = VM slot host"?
#
# Returns exit 0 on full compliance, non-zero on any failure with a clear message.
#
# Checks:
#   1. slot-cron-ff-pull cron installed
#   2. slot-git-status-report cron installed
#   3. FF-pull log shows activity within last 10 min
#   4. git-status-report log shows activity within last 10 min
#   5. Last reporter post returned HTTP 200 (against $ORCH_URL)
#   6. ${WORKSPACE_ROOT}/.tabs/ exists with at least 1 slot worktree
#   7. ${ORCH_TOKEN_FILE:-$HOME/.orch_token} is readable
#   8. backend reachable + workflow-capable GH_TOKEN
#   9. per-worktree commit identity canonical (recurrence guard for the bot-email leak)
#  10. per-worktree @{upstream} == origin/live-defi-rollout (drift guard — phantom 'ahead N')
#  11. tab branch names are globally unique (VM-scoped on a VM, never generic root/rootm)
#
# Usage: bash unified-trading-pm/scripts/verify-slot-host-symmetry.sh
#        bash unified-trading-pm/scripts/verify-slot-host-symmetry.sh --quiet
#
# Used by:
#   - Operator on new-host setup (`bash scripts/verify-slot-host-symmetry.sh`)
#   - Harsh's migration recipe (Step 5 sanity check)
#   - CI (future — once we wire it into the workflow)
#
# Cross-platform: macOS + Linux. Uses POSIX-ish primitives only.

set -uo pipefail

QUIET=0; ALERT=0
for _a in "$@"; do case "${_a}" in --quiet) QUIET=1;; --alert) ALERT=1;; esac; done

ORCH_URL="${ORCH_URL:-https://api.agent-orchestrator.odum-research.com}"
TOKEN_FILE="${ORCH_TOKEN_FILE:-${HOME}/.orch_token}"

# Auto-detect workspace root: climb cwd until we find unified-trading-system-repos
detect_workspace() {
    local d
    d="$(pwd)"
    while [[ "$(basename "${d}")" != "unified-trading-system-repos" && "${d}" != "/" ]]; do
        d="$(dirname "${d}")"
    done
    if [[ "${d}" == "/" ]]; then
        # Try the common defaults
        for c in "${HOME}/Code/unified-trading-system-repos" "/home/ubuntu/unified-trading-system-repos"; do
            [[ -d "$c" ]] && d="$c" && break
        done
    fi
    echo "${d}"
}

WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(detect_workspace)}"

FF_LOG=/tmp/slot-cron-ff-pull.log
GS_LOG=/tmp/slot-git-status-report.log

pass=0
fail=0

ok() { [[ ${QUIET} -eq 0 ]] && echo "  ✓ $1"; pass=$((pass+1)); }
bad() { echo "  ✗ $1" >&2; fail=$((fail+1)); }
section() { [[ ${QUIET} -eq 0 ]] && echo; [[ ${QUIET} -eq 0 ]] && echo "=== $1 ==="; }

section "host: $(hostname -s) | workspace: ${WORKSPACE_ROOT}"

# 1. FF-pull cron installed
if crontab -l 2>/dev/null | grep -q "slot-cron-ff-pull"; then
    ok "slot-cron-ff-pull cron installed"
else
    bad "slot-cron-ff-pull cron MISSING — see CLAUDE.md § Local slot host"
fi

# 2. git-status-report cron installed
if crontab -l 2>/dev/null | grep -q "slot-git-status-report"; then
    ok "slot-git-status-report cron installed"
else
    bad "slot-git-status-report cron MISSING"
fi

# 3. FF-pull log activity in last 10 min
if [[ -f "${FF_LOG}" ]]; then
    last_mtime=$(stat -c %Y "${FF_LOG}" 2>/dev/null || stat -f %m "${FF_LOG}" 2>/dev/null || echo 0)
    age_min=$(( ($(date +%s) - last_mtime) / 60 ))
    if [[ ${age_min} -le 10 ]]; then
        ok "FF-pull log fresh (${age_min}m ago)"
    else
        bad "FF-pull log STALE (${age_min}m ago — cron not running?)"
    fi
else
    bad "FF-pull log missing (${FF_LOG} — cron has never run?)"
fi

# 4. git-status-report log activity in last 10 min
if [[ -f "${GS_LOG}" ]]; then
    last_mtime=$(stat -c %Y "${GS_LOG}" 2>/dev/null || stat -f %m "${GS_LOG}" 2>/dev/null || echo 0)
    age_min=$(( ($(date +%s) - last_mtime) / 60 ))
    if [[ ${age_min} -le 10 ]]; then
        ok "git-status-report log fresh (${age_min}m ago)"
    else
        bad "git-status-report log STALE (${age_min}m ago)"
    fi
else
    bad "git-status-report log missing (${GS_LOG})"
fi

# 5. Last reporter post returned 200 (grep [ok] in recent log)
if [[ -f "${GS_LOG}" ]]; then
    if tail -50 "${GS_LOG}" | grep -qE "^\[[0-9:]+Z\] \[ok\] slot"; then
        ok "git-status reporter posted [ok] recently"
    else
        bad "git-status reporter has NO [ok] in last 50 lines (auth issue? backend down?)"
    fi
fi

# 6. Workspace .tabs/ exists with ≥1 slot worktree
if [[ -d "${WORKSPACE_ROOT}/.tabs" ]]; then
    # Portable numeric-dir count. BSD find (macOS) -regex uses basic regex where `+`
    # is literal, so '.*/[0-9]+' matched nothing → false "no slot dirs" on the operator
    # laptop. Count via a shell glob + bash numeric test instead (works on macOS + Linux).
    slot_count=0
    for _d in "${WORKSPACE_ROOT}"/.tabs/*/; do
        _b="$(basename "${_d}")"
        [[ "${_b}" =~ ^[0-9]+$ ]] && slot_count=$((slot_count + 1))
    done
    if [[ ${slot_count} -ge 1 ]]; then
        ok "${slot_count} slot worktree(s) under .tabs/"
    else
        bad "no numeric slot dirs under ${WORKSPACE_ROOT}/.tabs/"
    fi
else
    bad ".tabs/ missing at ${WORKSPACE_ROOT} — run setup-tab-worktrees.sh --init"
fi

# 7. Orch token readable
if [[ -r "${TOKEN_FILE}" ]]; then
    ok "orch token readable at ${TOKEN_FILE}"
else
    # try per-slot fallback
    fallback_found=""
    for slot_dir in "${WORKSPACE_ROOT}/.tabs"/*/; do
        if [[ -r "${slot_dir}.orch_token" ]]; then
            fallback_found="${slot_dir}.orch_token"
            break
        fi
    done
    if [[ -n "${fallback_found}" ]]; then
        ok "orch token readable via per-slot fallback (${fallback_found})"
    else
        bad "no orch token at ${TOKEN_FILE} or per-slot fallback (reporter will skip every slot)"
    fi
fi

# 8. Backend reachable
section "backend reachability"
if [[ -r "${TOKEN_FILE}" ]]; then
    TOKEN=$(cat "${TOKEN_FILE}")
    code=$(curl -sS -o /tmp/.symcheck.$$ -w '%{http_code}' \
        -H "Authorization: Bearer $TOKEN" \
        "${ORCH_URL}/api/mode" 2>/dev/null || echo "000")
    if [[ "$code" == "200" ]]; then
        mode=$(python3 -c 'import json, sys; print(json.load(sys.stdin).get("mode","?"))' < /tmp/.symcheck.$$ 2>/dev/null || echo "?")
        ok "backend reachable @ ${ORCH_URL} (mode=${mode})"
    else
        bad "backend HTTP ${code} @ ${ORCH_URL}/api/mode"
    fi
    rm -f /tmp/.symcheck.$$
fi

section "workflow-capable GH_TOKEN (no permission-based work-stoppage)"
# Every slot host must have a GH_TOKEN that can edit .github/workflows (GH_PAT with
# Workflows:write). The keyring gho_ login token lacks 'workflow' scope and silently blocks
# CI workflow migrations. SSOT: scripts/workspace/load-gh-token.sh.
_ghtok="${GH_TOKEN:-}"
if [[ -z "${_ghtok}" ]] && [[ -f "${WORKSPACE_ROOT}/unified-trading-pm/scripts/workspace/load-gh-token.sh" ]]; then
    # shellcheck disable=SC1091
    source "${WORKSPACE_ROOT}/unified-trading-pm/scripts/workspace/load-gh-token.sh" >/dev/null 2>&1 || true
    _ghtok="${GH_TOKEN:-}"
fi
if [[ -z "${_ghtok}" ]]; then
    bad "no GH_TOKEN — gh/HTTPS workflow edits will be refused (run: source scripts/workspace/load-gh-token.sh)"
else
    _code=$(curl -s -o /dev/null -w '%{http_code}' -X PUT \
        -H "Authorization: token ${_ghtok}" -H "Accept: application/vnd.github+json" \
        "https://api.github.com/repos/IggyIkenna/unified-trading-pm/contents/.github/workflows/quality-gates-v2.yml" \
        -d '{"message":"symcheck probe","content":"eA==","sha":"0000000000000000000000000000000000000000","branch":"live-defi-rollout"}' 2>/dev/null || echo "000")
    case "${_code}" in
        409|422) ok "GH_TOKEN is workflow-capable (Workflows:write)" ;;
        403)     bad "GH_TOKEN lacks Workflows:write (HTTP 403) — workflow migrations will block" ;;
        *)       bad "GH_TOKEN workflow-capability probe inconclusive (HTTP ${_code})" ;;
    esac
fi

# Snapshot HOST-level failures (checks 1-8: crons, logs, backend, token, .tabs) BEFORE the
# per-worktree checks below. The per-worktree checks (#9 identity, #10 upstream) iterate
# hundreds of worktrees and can report hundreds of nits — real, but commit-hygiene/drift
# concerns, NOT host symmetry. The --alert Slack post fires ONLY on host_fail>0 so a host
# that's fully symmetric doesn't spam "475 failed" every 30 min over per-worktree nits.
host_fail=${fail}

# 9. Per-worktree commit identity (recurrence guard for commit_identity_misconfig_fleet_2026_06_03).
#    Every slot worktree must carry the canonical identity — user.email == the GitHub-
#    attributed account AND user.name == "ikennaigboaka [slot-<N>·…". A bot/CI email
#    (semver-rollout[bot] / agent@ci.local) or a bare "ikennaigboaka" name means a
#    persistent-config leak recurred (root-caused in rollout-semver-agent.sh +
#    setup-workspace-from-manifest.sh). Fix: re-run setup-tab-worktrees.sh (provisions
#    per-worktree identity) or the manual fallback in CLAUDE.md § "Commit attribution".
section "per-worktree commit identity (recurrence guard)"
CANON_EMAIL="ikennaigboaka@gmail.com"
if [[ -d "${WORKSPACE_ROOT}/.tabs" ]]; then
    bad_identity=0
    checked=0
    for _slot_dir in "${WORKSPACE_ROOT}"/.tabs/*/; do
        _slot="$(basename "${_slot_dir}")"
        [[ "${_slot}" =~ ^[0-9]+$ ]] || continue
        for _repo_dir in "${_slot_dir}"*/; do
            [[ -d "${_repo_dir}/.git" || -f "${_repo_dir}/.git" ]] || continue
            checked=$((checked + 1))
            _email="$(git -C "${_repo_dir}" config user.email 2>/dev/null || echo '')"
            _name="$(git -C "${_repo_dir}" config user.name 2>/dev/null || echo '')"
            if [[ "${_email}" != "${CANON_EMAIL}" ]] || [[ "${_name}" != *"[slot-${_slot}·"* ]]; then
                bad "slot-${_slot}/$(basename "${_repo_dir}"): identity '${_name} <${_email}>' (want '…[slot-${_slot}·…] <${CANON_EMAIL}>')"
                bad_identity=$((bad_identity + 1))
            fi
        done
    done
    if [[ ${checked} -eq 0 ]]; then
        bad "no slot worktrees found to check identity (run setup-tab-worktrees.sh --init)"
    elif [[ ${bad_identity} -eq 0 ]]; then
        ok "all ${checked} slot worktree(s) carry canonical per-worktree identity"
    else
        bad "${bad_identity}/${checked} slot worktree(s) have non-canonical identity (commit-attribution leak recurred)"
    fi
else
    bad ".tabs/ missing — cannot verify per-worktree identity"
fi

# 10. Per-worktree upstream tracking (drift guard — codified 2026-06-04). A stray `git push -u`
#     re-points @{upstream} off origin/live-defi-rollout → phantom "ahead N" in the IDE vs the
#     stale remote tab. slot-cron-ff-pull auto-heals it each tick; this asserts the steady state.
#     SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Upstream tracking".
section "per-worktree upstream tracking (drift guard)"
WANT_UPSTREAM="origin/live-defi-rollout"
if [[ -d "${WORKSPACE_ROOT}/.tabs" ]]; then
    bad_upstream=0
    checked_up=0
    for _slot_dir in "${WORKSPACE_ROOT}"/.tabs/*/; do
        _slot="$(basename "${_slot_dir}")"
        [[ "${_slot}" =~ ^[0-9]+$ ]] || continue
        for _repo_dir in "${_slot_dir}"*/; do
            [[ -d "${_repo_dir}/.git" || -f "${_repo_dir}/.git" ]] || continue
            checked_up=$((checked_up + 1))
            _up="$(git -C "${_repo_dir}" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null || echo '')"
            # empty upstream (never pushed) is acceptable; only a non-LDR upstream is drift.
            if [[ -n "${_up}" && "${_up}" != "${WANT_UPSTREAM}" ]]; then
                bad "slot-${_slot}/$(basename "${_repo_dir}"): @{upstream}='${_up}' (want '${WANT_UPSTREAM}' — stray 'git push -u' drifted it; fix: git -C <dir> branch --set-upstream-to=${WANT_UPSTREAM} <branch>)"
                bad_upstream=$((bad_upstream + 1))
            fi
        done
    done
    if [[ ${checked_up} -eq 0 ]]; then
        bad "no slot worktrees found to check upstream"
    elif [[ ${bad_upstream} -eq 0 ]]; then
        ok "all ${checked_up} slot worktree(s) track ${WANT_UPSTREAM}"
    else
        bad "${bad_upstream}/${checked_up} slot worktree(s) drifted off ${WANT_UPSTREAM} (slot-cron-ff-pull auto-heals next tick)"
    fi
else
    bad ".tabs/ missing — cannot verify upstream tracking"
fi

# 11. Tab branch names globally unique (tab_branch_global_uniqueness 2026-06-04). A tab
#     branch name is a GLOBAL key — exactly one host fleet-wide — because the server-side
#     LDR→tab FF mirror + divergence monitor glob `tab/*`. setup-tab-worktrees.sh now bases
#     the prefix on VM_NAME on a fleet VM (else OPERATOR on a laptop). This asserts the steady
#     state: every slot branch here carries THIS host's prefix base, and never the generic
#     `root`/`rootm` (the $USER-on-a-VM collision class — live: tab/rootm/1..8).
#     SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Global branch-name uniqueness".
section "tab branch name global uniqueness"
EXPECT_BASE="${VM_NAME:-}"   # only enforce VM containment when on a fleet VM
if [[ -d "${WORKSPACE_ROOT}/.tabs" ]]; then
    bad_name=0
    checked_name=0
    for _slot_dir in "${WORKSPACE_ROOT}"/.tabs/*/; do
        _slot="$(basename "${_slot_dir}")"
        [[ "${_slot}" =~ ^[0-9]+$ ]] || continue
        for _repo_dir in "${_slot_dir}"*/; do
            [[ -d "${_repo_dir}/.git" || -f "${_repo_dir}/.git" ]] || continue
            _br="$(git -C "${_repo_dir}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '')"
            [[ "${_br}" == tab/*/* ]] || continue   # only check tab/<prefix>/<N> branches
            checked_name=$((checked_name + 1))
            _prefix="${_br#tab/}"; _prefix="${_prefix%/*}"   # tab/<prefix>/<N> → <prefix>
            # (a) generic $USER-derived prefix is always a collision class
            if [[ "${_prefix}" == "root" || "${_prefix}" == "rootm" ]]; then
                bad "slot-${_slot}/$(basename "${_repo_dir}"): branch '${_br}' uses generic prefix '${_prefix}' (\$USER-on-VM collision — re-provision with VM_NAME set: setup-tab-worktrees.sh --reset-slot ${_slot})"
                bad_name=$((bad_name + 1))
            # (b) on a fleet VM the prefix MUST contain the (globally-unique) VM_NAME
            elif [[ -n "${EXPECT_BASE}" && "${_prefix}" != "${EXPECT_BASE}" && "${_prefix}" != "${EXPECT_BASE}m" ]]; then
                bad "slot-${_slot}/$(basename "${_repo_dir}"): branch '${_br}' prefix '${_prefix}' is not VM-scoped (want '${EXPECT_BASE}' or '${EXPECT_BASE}m' — collides across hosts; re-provision with --reset-slot ${_slot})"
                bad_name=$((bad_name + 1))
            fi
        done
    done
    if [[ ${checked_name} -eq 0 ]]; then
        ok "no tab/* slot branches to check for name uniqueness"
    elif [[ ${bad_name} -eq 0 ]]; then
        ok "all ${checked_name} slot branch(es) globally-unique-named$([[ -n "${EXPECT_BASE}" ]] && echo " (VM-scoped: ${EXPECT_BASE})")"
    else
        bad "${bad_name}/${checked_name} slot branch(es) have collision-prone names (see above)"
    fi
else
    bad ".tabs/ missing — cannot verify tab branch name uniqueness"
fi

section "result: ${pass} passed / ${fail} failed"

if [[ ${fail} -gt 0 ]]; then
    # --alert (periodic-cron mode): post a Slack drift alert ONLY on HOST-level breaks
    # (crons/logs/backend/token/.tabs) — NOT per-worktree nits (#9/#10), which can number in
    # the hundreds and would spam. Per-worktree drift is logged + exit-1'd, just not alerted.
    if [[ ${ALERT} -eq 1 && ${host_fail:-0} -gt 0 ]]; then
        _wt_fail=$(( fail - host_fail ))
        _wh="${AGENT_ORCHESTRATOR_SLACK_WEBHOOK:-$(gcloud secrets versions access latest --secret=AGENT_ORCHESTRATOR_SLACK_WEBHOOK --project=central-element-323112 2>/dev/null || true)}"
        if [[ -n "${_wh}" ]]; then
            _host="$(hostname)"
            curl -sS -X POST "${_wh}" -H 'Content-Type: application/json' \
                -d "{\"text\":\":warning: slot-host-symmetry DRIFT on \`${_host}\` — ${host_fail} HOST-level check(s) failed (crons/logs/backend/token)$([ ${_wt_fail} -gt 0 ] && echo " + ${_wt_fail} per-worktree nit(s)"). Run verify-slot-host-symmetry.sh on that host. SSOT: CLAUDE.md § 'Local slot host = VM slot host'.\"}" \
                >/dev/null 2>&1 && echo "[alert] posted host-level symmetry-drift alert to Slack" || echo "[alert] WARN: Slack post failed"
        else
            echo "[alert] WARN: no Slack webhook — host-level drift NOT alerted"
        fi
    elif [[ ${ALERT} -eq 1 ]]; then
        echo "[alert] host-level checks PASS; $(( fail - host_fail )) per-worktree nit(s) only — NOT alerting (logged + exit-1)"
    fi
    [[ ${QUIET} -eq 0 ]] && cat <<EOF

This host is NOT fully compliant with the local↔VM slot-host symmetry contract.
See CLAUDE.md § "Local slot host = VM slot host — symmetric worker model".

To fix common issues:
  - Missing crons: see codex/12-agent-workflow/harsh-laptop-migration-2026-05-20.md Step 5
  - Missing token: ask Ikenna to issue one (or mint via auth.issue_token if on VM)
  - Backend unreachable: check that you can curl https://api.agent-orchestrator.odum-research.com/api/mode
  - Stale log: cron may be installed but failing — \`tail -30 /tmp/slot-cron-ff-pull.log\`
EOF
    exit 1
fi
exit 0
