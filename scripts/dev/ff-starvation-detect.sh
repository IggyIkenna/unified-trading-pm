#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# ff-starvation-detect.sh — detect FF-pull starvation for ONE repo worktree.
#
# Failure mode (Item 5 of workspace_config_drift_remediation): a slot worktree
# sits N commits BEHIND origin/<integration-branch> with the remote configured
# correctly, but the FF-pull cron (slot-cron-ff-pull.sh) silently no-ops every
# run because an *uncommitted local edit COLLIDES with an incoming changed file*,
# so every `git pull --ff-only` aborts. Nothing alerts; the slot falls further
# behind indefinitely. (Reference incident: slot-5 unified-trading-pm 963 behind.)
#
# This is the DETECTOR/ALERTER. slot-cron-ff-pull.sh stays the ACTOR (does the FF).
# It does NOT auto-resolve the collision (that needs the stash-by-name + adjudicate
# judgment from the two-teammates HARD RULE).
#
# Detection rule (per repo, evaluated each cron tick):
#   behind    = git rev-list --count HEAD..origin/<branch>
#   ff_clean  = (behind > 0) AND (merge-base HEAD origin/<branch> == HEAD)  # true FF possible
#   dirty     = git status --porcelain is non-empty
#   collision = ff_clean AND dirty AND (incoming changed-file set ∩ dirty file set ≠ ∅)
#   STARVED   = collision AND (behind >= FF_STARVE_COMMIT_THRESHOLD
#                              OR oldest colliding dirty file age > FF_STARVE_AGE_HOURS)
#
# `collision` (not merely `dirty`) is the precise trigger: a dirty file that does
# NOT intersect the incoming change set does not block --ff-only, so it is not a
# starvation cause and must not page. The behind>=THRESHOLD / age gate avoids
# paging on normal in-flight work (a slot 1-2 commits behind mid-edit is healthy).
#
# Output contract:
#   STARVED     → prints the human-readable signal payload to stdout, exits 0.
#   not starved → prints NOTHING to stdout, exits 0.
#   bad args / not a git repo → message on stderr, exits 2.
# Always cron-safe (never destructive, never mutates refs or the working tree).
#
# Usage:
#   ff-starvation-detect.sh <repo_dir> [--branch BR] [--slot N]
# Env-var defaults:
#   FF_STARVE_COMMIT_THRESHOLD  default 25  (behind-count gate)
#   FF_STARVE_AGE_HOURS         default 6   (oldest-colliding-file age gate, hours)
#   FF_BEHIND_BACKSTOP_COMMITS  default 75  (cause-agnostic backstop, behind-count)
#   FF_BEHIND_BACKSTOP_HOURS    default 6   (cause-agnostic backstop, oldest-unpulled-commit age)
#   INTEGRATION_BRANCH          default live-defi-rollout
#
# TWO independent verdicts (2026-08-10):
#   1. STARVATION — modelled cause: a dirty∩incoming collision is blocking the FF.
#   2. FF-BEHIND BACKSTOP — CAUSE-AGNOSTIC. A clone that CAN fast-forward, is far behind, and
#      has stayed that way, pages regardless of WHY. Every other signal in this fleet is keyed
#      to a cause someone already modelled, so an UNmodelled cause drifts silently forever.
#      Two such causes were measured in one session on 2026-08-10:
#        (a) non-colliding tracked dirt — the actor skipped it, verdict 1 stayed silent by
#            construction (it requires a collision); 15 repos hit 206/113/109 behind over
#            three days. Fixed at the actor, but only because a human happened to look.
#        (b) STILL UNEXPLAINED — once those repos were clean, three consecutive sweeps still
#            did not FF them; they had to be fast-forwarded by hand. No modelled verdict
#            covers that, and this backstop is what would have caught it.
#      Deliberately NOT gated on dirty/collision/clean: the point is to fire without a theory.
#      Threshold sits above verdict 1's so it is a backstop, not a duplicate page.
#
# Codex SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Step 7 — troubleshooting"

set -uo pipefail   # NOT set -e: a single failing git call must not abort detection.

THRESHOLD="${FF_STARVE_COMMIT_THRESHOLD:-25}"
AGE_HOURS="${FF_STARVE_AGE_HOURS:-6}"
BACKSTOP_COMMITS="${FF_BEHIND_BACKSTOP_COMMITS:-75}"
BACKSTOP_HOURS="${FF_BEHIND_BACKSTOP_HOURS:-6}"
INTEGRATION_BRANCH="${INTEGRATION_BRANCH:-live-defi-rollout}"
SLOT_ID=""
REPO_DIR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --branch) INTEGRATION_BRANCH="$2"; shift 2;;
        --slot)   SLOT_ID="$2"; shift 2;;
        -h|--help)
            sed -n '2,45p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
            exit 0;;
        -*) echo "Unknown arg: $1" >&2; exit 2;;
        *)  if [[ -z "${REPO_DIR}" ]]; then REPO_DIR="$1"; shift; else echo "Unexpected arg: $1" >&2; exit 2; fi;;
    esac
done

if [[ -z "${REPO_DIR}" ]]; then
    echo "usage: ff-starvation-detect.sh <repo_dir> [--branch BR] [--slot N]" >&2
    exit 2
fi
if [[ ! -d "${REPO_DIR}" ]]; then
    echo "not a directory: ${REPO_DIR}" >&2
    exit 2
fi

HOST_OS="$(uname -s)"
stat_mtime_epoch() {
    # Print mtime as epoch seconds for $1 ("" on failure). macOS + Linux.
    if [[ "${HOST_OS}" == "Darwin" ]]; then
        stat -f %m "$1" 2>/dev/null || true
    else
        stat -c %Y "$1" 2>/dev/null || true
    fi
}

# now-epoch via `date +%s` (portable). Subshell keeps env clean.
now_epoch() { date -u +%s 2>/dev/null || echo 0; }

cd "${REPO_DIR}" || { echo "cannot cd: ${REPO_DIR}" >&2; exit 2; }

# Must be a git worktree.
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "not a git worktree: ${REPO_DIR}" >&2
    exit 2
fi

REPO_NAME="$(basename "$(pwd)")"

# Resolve the integration branch ref; fall back to origin/main ONLY as a last
# resort for a repo with no live-defi-rollout ref (a genuinely main-only repo).
# NB: agent-orchestrator is NOT such a repo — it integrates via live-defi-rollout
# (server ships from LDR; main is dashboard-SPA + CI only), so this fallback never
# fires for it. (Corrected 2026-06-01; cron override removed 2026-05-24 after a
# `main` base caused false-diverged slot reports.)
remote_ref="origin/${INTEGRATION_BRANCH}"
if ! git rev-parse --verify --quiet "${remote_ref}" >/dev/null 2>&1; then
    if git rev-parse --verify --quiet "origin/main" >/dev/null 2>&1; then
        INTEGRATION_BRANCH="main"
        remote_ref="origin/main"
    else
        exit 0   # no integration ref in this worktree → nothing to detect.
    fi
fi

local_sha="$(git rev-parse HEAD 2>/dev/null || echo "")"
[[ -n "${local_sha}" ]] || exit 0

behind="$(git rev-list --count "HEAD..${remote_ref}" 2>/dev/null || echo 0)"
[[ "${behind}" -gt 0 ]] || exit 0   # up-to-date or ahead → not starved.

# ff_clean: a true fast-forward is possible iff merge-base == HEAD (remote is a
# strict descendant of local). Diverged/ahead is a DIFFERENT failure mode handled
# by slot-cron-ff-pull.sh's [skip:diverged]/[skip:ahead] — not starvation.
merge_base="$(git merge-base HEAD "${remote_ref}" 2>/dev/null || echo "")"
[[ -n "${merge_base}" && "${merge_base}" == "${local_sha}" ]] || exit 0

# ── VERDICT 2: cause-agnostic FF-BEHIND BACKSTOP ──────────────────────────────
# Runs BEFORE the clean-tree exit below — which is precisely where a clean-but-massively-
# behind clone used to leave silently. Age proxy = committer date of the OLDEST unpulled
# commit ("how long have we been missing commits"), which needs no dirty file to measure
# and therefore works for clean clones too.
if [[ "${behind}" -ge "${BACKSTOP_COMMITS}" ]]; then
    oldest_ct="$(git log --format=%ct "HEAD..${remote_ref}" 2>/dev/null | tail -1)"
    now_bs="$(now_epoch)"
    if [[ -n "${oldest_ct}" && "${now_bs}" -gt 0 ]]; then
        lag_h=$(( (now_bs - oldest_ct) / 3600 ))
        if [[ "${lag_h}" -ge "${BACKSTOP_HOURS}" ]]; then
            bs_dirty="$(git status --porcelain 2>/dev/null | head -c1)"
            cat <<EOF
FF-BEHIND BACKSTOP — ${SLOT_ID:+slot ${SLOT_ID} / }${REPO_NAME}
behind: ${behind} commits (fast-forwardable) | oldest unpulled commit: ${lag_h}h old
tree: $([[ -n "${bs_dirty}" ]] && echo "dirty" || echo "CLEAN — nothing is blocking this; the cause is NOT modelled")
cause: UNKNOWN by design — this verdict is cause-agnostic and fires on lag alone.
why it matters: this clone is running an ${lag_h}h-stale base. Agents on it re-implement
  fixes already upstream and produce conflicting work; a green CI here proves nothing.
remediation: cd <repo> && git merge --ff-only ${remote_ref}
  If that succeeds, the puller was starving it — check this repo's verdict in
  /tmp/slot-cron-ff-pull.log and treat a silent skip as a puller defect, not as noise.
EOF
            exit 0
        fi
    fi
fi

porcelain="$(git status --porcelain 2>/dev/null || echo "")"
[[ -n "${porcelain}" ]] || exit 0   # clean → FF would succeed → not starved.

# Dirty file set (repo-relative paths). Handle renames ("R  old -> new" → new)
# and untracked ("?? path" — untracked files that the incoming change adds also
# block --ff-only with "untracked working tree files would be overwritten").
dirty_files=()
while IFS= read -r line; do
    [[ -z "${line}" ]] && continue
    file="${line:3}"
    file="${file##* -> }"   # rename → keep the new path
    [[ -n "${file}" ]] && dirty_files+=("${file}")
done <<< "${porcelain}"
[[ "${#dirty_files[@]}" -gt 0 ]] || exit 0

# Incoming changed-file set (paths touched between local HEAD and the remote tip).
incoming="$(git diff --name-only "HEAD..${remote_ref}" 2>/dev/null || echo "")"
[[ -n "${incoming}" ]] || exit 0

# collision = dirty ∩ incoming. Collect the colliding paths.
colliding=()
for df in "${dirty_files[@]}"; do
    while IFS= read -r inf; do
        [[ -z "${inf}" ]] && continue
        if [[ "${df}" == "${inf}" ]]; then
            colliding+=("${df}")
            break
        fi
    done <<< "${incoming}"
done
[[ "${#colliding[@]}" -gt 0 ]] || exit 0   # dirty but non-colliding → FF still works.

# Gate: behind >= THRESHOLD OR oldest colliding file age > AGE_HOURS.
# (The reporter cannot read the ff-pull cron's "last successful FF" timestamp, so
# the oldest colliding-file mtime is the available proxy for how long the
# collision has been blocking the FF.)
gate_met=0
if [[ "${behind}" -ge "${THRESHOLD}" ]]; then
    gate_met=1
else
    now="$(now_epoch)"
    age_limit_secs=$(( AGE_HOURS * 3600 ))
    for cf in "${colliding[@]}"; do
        [[ -e "${cf}" ]] || continue
        ep="$(stat_mtime_epoch "${cf}")"
        [[ -z "${ep}" ]] && continue
        if [[ "${now}" -gt 0 && $(( now - ep )) -gt "${age_limit_secs}" ]]; then
            gate_met=1
            break
        fi
    done
fi
[[ "${gate_met}" -eq 1 ]] || exit 0   # collision below threshold/age → in-flight, no signal.

# STARVED — emit the signal payload.
last_ff="unknown"
colliding_csv="$(IFS=', '; echo "${colliding[*]}")"
slot_label="${SLOT_ID:+slot ${SLOT_ID} / }"
cat <<EOF
FF-PULL STARVATION — ${slot_label}${REPO_NAME}
behind: ${behind} commits | last successful FF: ${last_ff}
blocking dirty files (collide with incoming): ${colliding_csv}
owner hint: untracked/unowned? → likely foreign WIP — stash-by-name + FF, do NOT discard
remediation: git stash push -- ${colliding_csv} && git pull --ff-only && (commit-or-restore the stash)
EOF
exit 0
