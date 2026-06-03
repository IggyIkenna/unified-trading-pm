#!/usr/bin/env bash
# benchmark-qg-under-load.sh — AGGREGATE-load quality-gates benchmark.
#
# Plan: plans/active/quality_gates_resource_contention_speedup_2026_06_02.md (todo: qg-bench-aggregate)
#
# WHY THIS EXISTS
#   The archived predecessor benchmark (deployment-service/scripts/benchmark-quality-gates.sh)
#   timed ONE repo's quality-gates.sh sequentially. That is structurally blind to the problem
#   this plan exists to fix: the dev host runs 8 slots × 2 operator sides of parallel agents,
#   and contention only appears when SEVERAL slots gate AT ONCE. This harness fires K slots'
#   quality-gates.sh concurrently and measures the host under that aggregate load:
#     • per-run wall-clock  → p50 / p95 at each K
#     • CPU steal (vmstat `st`)        → scheduler oversubscription
#     • swap-in / swap-out (vmstat si/so) → memory oversubscription (the OOM/thrash signal)
#     • load average (/proc/loadavg)
#     • peak RSS per run (/usr/bin/time -v)
#   Output: one CSV (per-run + per-K summary rows) + a one-line verdict
#   (oversubscribed Y/N at each K).
#
# SOUNDNESS / SAFETY
#   • Firing K=8 concurrent QGs on the SHARED dev host deliberately induces the thrash the
#     workspace rules warn against — it WILL contend with other slots/teammates. Run high-K
#     sweeps only in a coordinated window. Default is a light K=1,2 smoke.
#   • Runs set IGNORE_TIMEOUT=true so the QG meta duration-gate does not fail a run we are
#     deliberately slowing down — we measure wall-clock, not pass/fail.
#   • Each concurrent run uses a DISTINCT repo (QG writes coverage.xml/.qg_last_passed_sha in
#     the repo root; two runs in one repo would collide). K is therefore capped at pool size.
#
# USAGE
#   bash scripts/dev/benchmark-qg-under-load.sh [--k 1,2,4,8] [--reps N] [--repos "r1 r2 ..."]
#                                               [--out PATH] [--quick] [--dry-run]
#   --k       comma list of concurrency levels (default "1,2")
#   --reps    repetitions per K level (default 1)
#   --repos   space-separated repo pool (default: representative heavy/lib/small mix)
#   --quick   pass --quick to each quality-gates.sh (lighter per-run; still real contention)
#   --out     CSV path (default scripts/dev/qg-bench-under-load-<UTC>.csv)
#   --dry-run print the plan and exit without running any QG
set -euo pipefail

# ── locate workspace root (this script lives in unified-trading-pm/scripts/dev) ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
WORKSPACE_ROOT="$(cd "${PM_ROOT}/.." && pwd)"

# ── defaults ──
K_LIST="1,2"
REPS=1
QUICK=""
DRY_RUN=false
# Representative pool: a heavy service, a big lib, a couple of small services.
# Override with --repos. Order matters: K uses the first K entries.
REPO_POOL="instruments-service unified-trading-library alerting-service deployment-api unified-api-contracts market-tick-data-service execution-service unified-trading-pm"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="${PM_ROOT}/scripts/dev/qg-bench-under-load-${TS}.csv"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --k)      K_LIST="$2"; shift 2 ;;
        --reps)   REPS="$2"; shift 2 ;;
        --repos)  REPO_POOL="$2"; shift 2 ;;
        --quick)  QUICK="--quick"; shift ;;
        --out)    OUT="$2"; shift 2 ;;
        --dry-run) DRY_RUN=true; shift ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

read -r -a POOL <<< "$REPO_POOL"
POOL_N=${#POOL[@]}
NPROC="$(nproc)"
MEM_GB="$(free -g | awk '/^Mem:/{print $2}')"

# Validate pool repos exist + have a QG script.
VALID=()
for r in "${POOL[@]}"; do
    if [[ -f "${WORKSPACE_ROOT}/${r}/scripts/quality-gates.sh" ]]; then
        VALID+=("$r")
    else
        echo "⚠️  skipping '$r' (no scripts/quality-gates.sh under ${WORKSPACE_ROOT})" >&2
    fi
done
POOL=("${VALID[@]}"); POOL_N=${#POOL[@]}
[[ $POOL_N -eq 0 ]] && { echo "no valid repos in pool" >&2; exit 1; }

IFS=',' read -r -a KS <<< "$K_LIST"

echo "════════════════════════════════════════════════════════════════════"
echo " QG aggregate-load benchmark"
echo "   host        : ${NPROC} cores / ${MEM_GB} GB RAM"
echo "   workspace   : ${WORKSPACE_ROOT}"
echo "   K levels    : ${KS[*]}     reps/level: ${REPS}     quick: ${QUICK:-no}"
echo "   repo pool   : ${POOL[*]} (${POOL_N})"
echo "   out CSV     : ${OUT}"
echo "════════════════════════════════════════════════════════════════════"
for K in "${KS[@]}"; do
    if (( K > POOL_N )); then
        echo "⚠️  K=$K exceeds pool size ${POOL_N} — clamp the pool or pass more --repos; this K will be skipped." >&2
    fi
done

if $DRY_RUN; then
    echo "[dry-run] would run the above sweep. Exiting without launching QG."
    exit 0
fi

# ── CSV header ──
mkdir -p "$(dirname "$OUT")"
echo "row_type,k,rep,repo,wall_s,max_rss_mb,exit_code,max_swap_in,max_swap_out,max_steal,loadavg_1m_peak" > "$OUT"

TMP="$(mktemp -d "${TMPDIR:-/tmp}/qgbench.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

# Run one repo's QG, wrapped in /usr/bin/time -v. Writes "<wall_s> <rss_mb> <exit>" to $1.
run_one() {
    local repo="$1" outfile="$2"
    local tlog="${TMP}/time.${repo}.$$"
    local start end wall rss_kb rss_mb ec
    start="$(date +%s.%N)"
    # IGNORE_TIMEOUT: we deliberately slow runs; don't let the meta duration-gate fail them.
    # `&& ec=0 || ec=$?` so a non-zero QG exit does NOT trip set -e and abort before we
    # write the outfile — a RED gate is a valid measurement, not a harness error.
    ec=0
    # MUST cd into the repo: quality-gates.sh resolves its repo via `git rev-parse
    # --show-toplevel` from CWD, so running it from elsewhere measures the wrong repo.
    # --no-fix: a benchmark must be READ-ONLY — never let ruff --fix mutate the tree
    # (critical when benchmarking primary/live working trees).
    ( cd "${WORKSPACE_ROOT}/${repo}" && \
      IGNORE_TIMEOUT=true /usr/bin/time -v -o "$tlog" \
        bash scripts/quality-gates.sh --no-fix ${QUICK} > "${TMP}/qg.${repo}.log" 2>&1 ) || ec=$?
    end="$(date +%s.%N)"
    wall="$(awk "BEGIN{printf \"%.1f\", ${end}-${start}}")"
    rss_kb="$(awk -F': ' '/Maximum resident set size/{print $2}' "$tlog" 2>/dev/null || echo 0)"
    rss_mb="$(awk "BEGIN{printf \"%.0f\", ${rss_kb:-0}/1024}")"
    echo "${wall} ${rss_mb} ${ec}" > "$outfile"
}

# percentile helper: $1=file of numbers, $2=pct(0-100)
pct() {
    local f="$1" p="$2"
    sort -n "$f" | awk -v p="$p" '{a[NR]=$1} END{ if(NR==0){print 0; exit} idx=int((p/100)*NR); if(idx<1)idx=1; if(idx>NR)idx=NR; print a[idx]}'
}

for K in "${KS[@]}"; do
    (( K > POOL_N )) && continue
    walls="${TMP}/walls.k${K}"; : > "$walls"
    for (( rep=1; rep<=REPS; rep++ )); do
        echo "── K=${K} rep=${rep}/${REPS} : launching ${K} concurrent QG runs ──"
        # background host sampler: vmstat 1 for the batch duration → si so st
        local_vm="${TMP}/vmstat.k${K}.r${rep}"
        vmstat 1 > "$local_vm" 2>/dev/null &
        VMSTAT_PID=$!
        load_log="${TMP}/load.k${K}.r${rep}"; : > "$load_log"
        ( while :; do awk '{print $1}' /proc/loadavg >> "$load_log"; sleep 1; done ) &
        LOAD_PID=$!

        pids=(); repos_used=(); outs=()
        for (( i=0; i<K; i++ )); do
            repo="${POOL[$i]}"; repos_used+=("$repo")
            of="${TMP}/run.k${K}.r${rep}.${i}"; outs+=("$of")
            run_one "$repo" "$of" &
            pids+=($!)
        done
        # wait for all K runs
        for pid in "${pids[@]}"; do wait "$pid" || true; done

        kill "$VMSTAT_PID" "$LOAD_PID" 2>/dev/null || true
        wait "$VMSTAT_PID" "$LOAD_PID" 2>/dev/null || true

        # host-metric peaks for this batch
        max_si=$(awk 'NR>2{print $7}' "$local_vm" | sort -n | tail -1); max_si=${max_si:-0}
        max_so=$(awk 'NR>2{print $8}' "$local_vm" | sort -n | tail -1); max_so=${max_so:-0}
        max_st=$(awk 'NR>2{print $17}' "$local_vm" | sort -n | tail -1); max_st=${max_st:-0}
        max_load=$(sort -n "$load_log" | tail -1); max_load=${max_load:-0}

        # per-run rows
        for (( i=0; i<K; i++ )); do
            read -r wall rss ec < "${outs[$i]}"
            echo "run,${K},${rep},${repos_used[$i]},${wall},${rss},${ec},${max_si},${max_so},${max_st},${max_load}" >> "$OUT"
            echo "$wall" >> "$walls"
        done
    done
    # per-K summary row
    p50="$(pct "$walls" 50)"; p95="$(pct "$walls" 95)"
    # reuse last batch's host peaks for the summary line
    echo "summary,${K},,,${p50}|p50 ${p95}|p95,,,${max_si:-0},${max_so:-0},${max_st:-0},${max_load:-0}" >> "$OUT"
    echo "   K=${K}  p50=${p50}s  p95=${p95}s  swap_in_peak=${max_si:-0}  steal_peak=${max_st:-0}  load_peak=${max_load:-0}"
done

echo "════════════════════════════════════════════════════════════════════"
echo " VERDICT"
# K=1 p95 baseline
base_p95="$(awk -F, '$1=="summary" && $2==1 {print $5}' "$OUT" | head -1 | sed -n 's/.* \([0-9.]*\)|p95/\1/p')"
echo "   baseline p95 (K=1): ${base_p95:-n/a}s"
oversub="N"
while IFS=, read -r rt k _ _ wallfield _ _ si _ st _; do
    [[ "$rt" == "summary" ]] || continue
    [[ "$k" == "1" ]] && continue
    kp95="$(echo "$wallfield" | sed -n 's/.* \([0-9.]*\)|p95/\1/p')"
    ratio="n/a"
    if [[ -n "${base_p95:-}" && "${base_p95}" != "0" && -n "$kp95" ]]; then
        ratio="$(awk "BEGIN{printf \"%.2f\", ${kp95}/${base_p95}}")"
    fi
    flag="ok"
    if [[ "${si:-0}" -gt 0 ]] || { [[ "$ratio" != "n/a" ]] && awk "BEGIN{exit !(${ratio}>1.5)}"; }; then
        flag="OVERSUBSCRIBED (swap_in=${si:-0}, p95 ratio=${ratio})"; oversub="Y"
    fi
    echo "   K=${k}: p95=${kp95}s  ratio_vs_K1=${ratio}  steal_peak=${st:-0}  → ${flag}"
done < "$OUT"
echo "   ──> host oversubscribed under this sweep: ${oversub}"
echo "   CSV: ${OUT}"
echo "════════════════════════════════════════════════════════════════════"
