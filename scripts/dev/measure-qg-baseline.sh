#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# measure-qg-baseline.sh — per-repo QG resource baseline recorder.
#
# Plan: plans/active/quality_gates_resource_contention_speedup_2026_06_02.md (todo: qg-perrepo-baseline)
#
# WHAT / WHY
#   Distinct from benchmark-qg-under-load.sh (which measures cross-slot CONTENTION at K>1).
#   This measures the per-repo COST of a SINGLE quality-gates.sh run — wall-clock, peak RSS,
#   and CPU-seconds — and records it as a committed baseline keyed per-repo × {local,vm}.
#   Two consumers:
#     1. A 2× deviation guard in quality-gates-base/base-service.sh WARNs when a run exceeds
#        2× its baseline wall-clock or peak RSS → early detection of resource regressions
#        during code-freeze.
#     2. The worker-VM right-sizing decision (qg-vm-rightsizing): floor =
#        peak-per-run-RSS × peak-concurrent-QG-under-the-governor.
#
#   Runs are READ-ONLY (--no-fix): a measurement must never mutate the working tree.
#
# USAGE
#   bash scripts/dev/measure-qg-baseline.sh --env local|vm [--repos "r1 r2 ..."]
#                                           [--quick] [--out PATH] [--force]
#   --env     REQUIRED. Which side this measurement represents (local dev box vs AWS worker VM).
#   --repos   space-separated repo list (default: representative heavy/lib/small mix).
#   --quick   pass --quick to quality-gates.sh (faster, still real).
#   --out     baseline JSON path (default scripts/dev/qg_resource_baseline.json).
#   --force   bypass the anomaly guard below — always promote. For a deliberate, reviewed
#             manual re-baseline (the committed values ARE stale and you mean to bump them).
#
# ANOMALY GUARD (2026-08-16, qg_host_adaptive_resource_governor_2026_07_14.md "baseline
# freshness loop" / governor Trigger 3): a repo whose freshly measured peak_rss_mb is
# QG_BASELINE_ANOMALY_PCT (default 20) percent or more above its EXISTING committed value is
# NOT auto-promoted — a jump that size means real growth or a measurement fluke, either way
# worth a human look, not a silent bump (the exact instruments-service +182% case that
# motivated this plan). Instead it fires a WARNING via qg-host-governor.sh's
# _qg_governor_slack_alert() (best-effort — silent no-op with no webhook configured) and
# leaves the committed entry untouched. --force bypasses this for a reviewed re-baseline. A
# repo/env with NO existing committed value always promotes (nothing to compare against).
#
# The JSON is MERGED, not clobbered: re-running --env local leaves the vm entries intact,
# and vice-versa. Shape:
#   { "<repo>": { "local": {wall_s, peak_rss_mb, cpu_s, exit_code, quick, measured_at_utc},
#                 "vm":    {...} }, ... }
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
WORKSPACE_ROOT="$(cd "${PM_ROOT}/.." && pwd)"

ENV_TAG=""
QUICK=""
FORCE=""
JOBS=1
REPO_LIST="instruments-service unified-trading-library alerting-service deployment-api unified-api-contracts"
OUT="${PM_ROOT}/scripts/dev/qg_resource_baseline.json"
ANOMALY_PCT="${QG_BASELINE_ANOMALY_PCT:-20}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --env)   ENV_TAG="$2"; shift 2 ;;
        --repos) REPO_LIST="$2"; shift 2 ;;
        --quick) QUICK="--quick"; shift ;;
        --force) FORCE="true"; shift ;;
        --jobs)  JOBS="$2"; shift 2 ;;
        --out)   OUT="$2"; shift 2 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

# Best-effort: only needed for the anomaly-guard's Slack alert. Absence (e.g. a bare
# checkout without the governor file) must never break a measurement run.
GOVERNOR_SCRIPT="${PM_ROOT}/scripts/quality-gates-base/qg-host-governor.sh"
if [[ -f "$GOVERNOR_SCRIPT" ]]; then
    # shellcheck source=/dev/null
    source "$GOVERNOR_SCRIPT" 2>/dev/null || true
fi

# <repo> <env> <prior_mb> <new_mb> — fires the Trigger-3 WARNING via the shared governor
# alert helper if it's available; silent no-op otherwise (mirrors this file's existing
# graceful-degradation posture, e.g. the RUNNABLE-filter skip above).
_qg_baseline_anomaly_alert() {
    local repo="$1" env="$2" prior="$3" new="$4" pct
    command -v _qg_governor_slack_alert >/dev/null 2>&1 || return 0
    pct="$(awk -v p="$prior" -v n="$new" 'BEGIN{ if (p > 0) printf "%.0f", (n - p) * 100 / p; else print "?" }')"
    _qg_governor_slack_alert "WARNING" "qg-baseline-stale:${repo}:${env}" "${QG_SLACK_BASELINE_ANOMALY_COOLDOWN_MIN:-1440}" \
        "QG baseline-freshness: ${repo} (${env}) observed peak ${new}MB is +${pct}% above committed baseline ${prior}MB — NOT auto-promoted (>=${ANOMALY_PCT}% guard). Investigate real growth vs measurement noise, then re-baseline deliberately if legitimate: bash scripts/dev/measure-qg-baseline.sh --env ${env} --repos ${repo} --force"
}
[[ "$JOBS" =~ ^[0-9]+$ ]] && (( JOBS >= 1 )) || { echo "ERROR: --jobs must be a positive integer" >&2; exit 2; }

case "$ENV_TAG" in
    local|vm) ;;
    *) echo "ERROR: --env must be 'local' or 'vm' (got '${ENV_TAG:-<empty>}')" >&2; exit 2 ;;
esac

command -v /usr/bin/time >/dev/null || { echo "ERROR: /usr/bin/time required (GNU time)" >&2; exit 1; }
command -v python3 >/dev/null || { echo "ERROR: python3 required for JSON merge" >&2; exit 1; }

read -r -a REPOS <<< "$REPO_LIST"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/qgbaseline.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

echo "════════════════════════════════════════════════════════════════════"
echo " QG per-repo baseline   env=${ENV_TAG}   quick=${QUICK:-no}   jobs=${JOBS}"
echo "   workspace : ${WORKSPACE_ROOT}"
echo "   repos     : ${REPOS[*]}"
echo "   out       : ${OUT}"
if (( JOBS > 1 )); then
    echo "   NOTE: jobs>1 — wall_s may inflate under contention; peak_rss_mb + cpu_s stay"
    echo "         parallelism-invariant. measured_concurrency=${JOBS} recorded per entry."
fi
echo "════════════════════════════════════════════════════════════════════"

QUICK_BOOL=$([[ -n "$QUICK" ]] && echo true || echo false)
FORCE_BOOL=$([[ -n "$FORCE" ]] && echo true || echo false)

# Run ONE repo's full QG (read-only) and write "wall rss_mb cpu ec" to $2. No JSON here
# (JSON writes are serialized in the parent to avoid concurrent read-modify-write races).
measure_one() {
    local repo="$1" resfile="$2"
    local tlog="${TMP}/time.${repo}"
    local start end wall rss_kb rss_mb usr_s sys_s cpu_s ec=0
    start="$(date +%s.%N)"
    # QG_SENTINEL_DISABLE=true: a baseline must measure the FULL gate cost (tests +
    # typecheck actually run), never a green-sentinel SKIP — else the recorded wall is a
    # cache-hit time and the 2×-drift WARN (base-service.sh) false-fires on every real
    # full run. (Fixed 2026-06-17: the tool previously honored the sentinel → mixed
    # skip/full baselines.) The drift WARN reads wall only; cpu/rss are informational.
    ( cd "${WORKSPACE_ROOT}/${repo}" && \
      IGNORE_TIMEOUT=true QG_SENTINEL_DISABLE=true /usr/bin/time -v -o "$tlog" \
        bash scripts/quality-gates.sh --no-fix ${QUICK} > "${TMP}/qg.${repo}.log" 2>&1 ) || ec=$?
    end="$(date +%s.%N)"
    wall="$(awk "BEGIN{printf \"%.1f\", ${end}-${start}}")"
    rss_kb="$(awk -F': ' '/Maximum resident set size/{print $2}' "$tlog" 2>/dev/null || echo 0)"
    rss_mb="$(awk "BEGIN{printf \"%.0f\", ${rss_kb:-0}/1024}")"
    usr_s="$(awk -F': ' '/User time/{print $2}' "$tlog" 2>/dev/null || echo 0)"
    sys_s="$(awk -F': ' '/System time/{print $2}' "$tlog" 2>/dev/null || echo 0)"
    cpu_s="$(awk "BEGIN{printf \"%.1f\", ${usr_s:-0}+${sys_s:-0}}")"
    echo "${wall} ${rss_mb} ${cpu_s} ${ec}" > "$resfile"
}

# Merge one repo's result into the JSON (called ONLY by the parent, serially). Prints
# "PROMOTED <rss_mb>" or "ANOMALY <prior_mb> <rss_mb>" to stdout — the caller reads this to
# decide whether to fire the anomaly alert (network/alerting stays in bash; this stays a
# pure JSON read-compare-write, consistent with the file's existing no-network-in-python
# design).
merge_result() {
    local repo="$1" wall="$2" rss="$3" cpu="$4" ec="$5"
    python3 "${SCRIPT_DIR}/qg_baseline_merge.py" \
        "$OUT" "$repo" "$ENV_TAG" "$wall" "$rss" "$cpu" "$ec" "$QUICK_BOOL" "$JOBS" "$TS" "$FORCE_BOOL" "$ANOMALY_PCT"
}

# Filter to repos that actually have a gate script.
RUNNABLE=()
for repo in "${REPOS[@]}"; do
    if [[ -f "${WORKSPACE_ROOT}/${repo}/scripts/quality-gates.sh" ]]; then
        RUNNABLE+=("$repo")
    else
        echo "⚠️  skip ${repo} (no scripts/quality-gates.sh)"
    fi
done

# Wave scheduler: launch up to JOBS measure_one in parallel, then drain + merge serially.
total=${#RUNNABLE[@]}
idx=0
while (( idx < total )); do
    pids=(); wave_repos=(); wave_res=()
    for (( j=0; j<JOBS && idx<total; j++, idx++ )); do
        repo="${RUNNABLE[$idx]}"; res="${TMP}/res.${repo}"
        wave_repos+=("$repo"); wave_res+=("$res")
        measure_one "$repo" "$res" &
        pids+=($!)
    done
    for pid in "${pids[@]}"; do wait "$pid" || true; done
    # merge this wave's results in the parent (serialized JSON writes)
    for (( w=0; w<${#wave_repos[@]}; w++ )); do
        repo="${wave_repos[$w]}"; res="${wave_res[$w]}"
        if [[ -f "$res" ]]; then
            read -r wall rss_mb cpu_s ec < "$res"
            echo "   ${repo}: wall=${wall}s peak_rss=${rss_mb}MB cpu=${cpu_s}s exit=${ec}"
            merge_out="$(merge_result "$repo" "$wall" "$rss_mb" "$cpu_s" "$ec")"
            case "$merge_out" in
                ANOMALY*)
                    read -r _ prior_mb new_mb <<< "$merge_out"
                    echo "   ${repo}: ⚠️  ANOMALY — observed ${new_mb}MB is >=${ANOMALY_PCT}% above committed baseline ${prior_mb}MB (env=${ENV_TAG}) — NOT promoted, alerting instead of a silent bump"
                    _qg_baseline_anomaly_alert "$repo" "$ENV_TAG" "$prior_mb" "$new_mb"
                    ;;
            esac
        else
            echo "   ${repo}: NO RESULT (measure_one produced no file)"
        fi
    done
done

echo "════════════════════════════════════════════════════════════════════"
echo " baseline written: ${OUT}"
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(f'   repos recorded: {len(d)}; envs per repo: '+', '.join(sorted({e for v in d.values() for e in v})))" "$OUT" 2>/dev/null || true
echo "════════════════════════════════════════════════════════════════════"
