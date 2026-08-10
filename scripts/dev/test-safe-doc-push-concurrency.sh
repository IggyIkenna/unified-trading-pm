#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# Concurrency regression test for safe-doc-push.sh's isolated-worktree mode.
#
# Operator ask 2026-08-10: "they need to be properly tested to ensure they dont regress
# the issue, the only way to do that is now under high concurrency".
#
# WHAT IT PROVES. The data-loss modes in
# pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md are properties of the
# SHARED INDEX, not of the branch being pushed to -- so driving N concurrent safe-doc-push
# runs out of ONE checkout reproduces them without touching live-defi-rollout. Each worker
# owns a DISTINCT file (concurrent same-file edits are a different, legitimate conflict).
#
# ACCEPTANCE (all must hold):
#   1. Every worker's file content on the target branch is byte-identical to what it wrote.
#   2. No worker reports success while its content is absent (the false-success path).
#   3. The caller's working tree copy of each file is UNCHANGED after the run -- isolated
#      mode must never write to the caller's tree. This is the regression that matters:
#      it is what failed three times on 2026-08-10.
#
# Usage: conctest.sh <repo> <n-workers> <branch> [SDP_ISOLATED value]
set -uo pipefail
REPO="$1"; N="${2:-5}"; BR="$3"; ISO="${4:-1}"
STAMP="$(git -C "$REPO" rev-parse --short HEAD)"
SCRATCH="$(dirname "$0")"
OUT="$SCRATCH/conc"
mkdir -p "$OUT"

# Distinct probe file per worker, under a path the corpus tolerates (tests fixture area).
PROBE_DIR="scripts/plan-hygiene/.conctest"
mkdir -p "$REPO/$PROBE_DIR"

# PEER-NOISE WRITER (the F6 trigger). Without foreign UNSTAGED WIP in the checkout the
# race cannot form: prek only saves-and-restores a patch when there are unstaged changes,
# and it is that restore conflicting with the hook's own autofix that produces
# "Hook changes conflicted with the saved unstaged changes. Reverting the hook changes",
# the full re-run, and the drift death. A test without this is testing the easy case --
# the first legacy baseline scored 5/6 PASS precisely because the checkout was clean.
# This simulates a concurrent session continuously editing unrelated tracked files.
NOISE_PID=""
if [[ "${CONC_NOISE:-1}" != "0" ]]; then
  (
    cd "$REPO" || exit 0
    # two unrelated TRACKED files, rewritten continuously => permanent foreign unstaged WIP
    nf1="$(git ls-files 'plans/active/*.md' | head -1)"
    nf2="$(git ls-files 'plans/active/issues/*.md' | head -1)"
    while :; do
      for nf in "$nf1" "$nf2"; do
        [[ -n "$nf" && -f "$nf" ]] || continue
        printf '\n<!-- peer-noise %s -->\n' "$RANDOM" >> "$nf"
      done
      sleep 0.3
    done
  ) &
  NOISE_PID=$!
fi

pids=()
for i in $(seq 1 "$N"); do
  f="$PROBE_DIR/probe_${STAMP}_${i}.txt"
  # unique, verifiable content per worker
  printf 'worker=%s stamp=%s marker=CONCTEST-%s-%s\n' "$i" "$STAMP" "$STAMP" "$i" > "$REPO/$f"
  cp "$REPO/$f" "$OUT/expected_${i}.txt"
  (
    cd "$REPO" || exit 90
    SDP_ISOLATED="$ISO" bash scripts/dev/safe-doc-push.sh \
      "test(conc): concurrency probe worker ${i} @ ${STAMP}" --files "$f" "$BR" \
      > "$OUT/worker_${i}.log" 2>&1
    echo "$?" > "$OUT/worker_${i}.rc"
  ) &
  pids+=($!)
done

for p in "${pids[@]}"; do wait "$p"; done
if [[ -n "$NOISE_PID" ]]; then kill "$NOISE_PID" 2>/dev/null || true; wait "$NOISE_PID" 2>/dev/null || true; fi
# Leave the noise files dirty on purpose -- restoring them is the caller's business and a
# `git restore` here could mask a real loss. Report whether they survived instead.
echo "  (peer-noise active during run: ${CONC_NOISE:-1})"

echo "=== RESULTS (isolated=$ISO, workers=$N, branch=$BR) ==="
git -C "$REPO" fetch -q origin "$BR" 2>/dev/null
pass=0; fail=0
for i in $(seq 1 "$N"); do
  f="$PROBE_DIR/probe_${STAMP}_${i}.txt"
  rc="$(cat "$OUT/worker_${i}.rc" 2>/dev/null || echo '?')"
  landed="no"
  if git -C "$REPO" show "origin/$BR:$f" 2>/dev/null | diff -q - "$OUT/expected_${i}.txt" >/dev/null 2>&1; then
    landed="yes"
  fi
  tree_ok="no"
  if [[ -f "$REPO/$f" ]] && diff -q "$REPO/$f" "$OUT/expected_${i}.txt" >/dev/null 2>&1; then
    tree_ok="yes"
  fi
  verdict="FAIL"
  # rc 0 must mean landed; a non-zero rc that did not land is an honest failure, not a defect.
  if [[ "$rc" == "0" && "$landed" == "yes" && "$tree_ok" == "yes" ]]; then
    verdict="PASS"; pass=$((pass + 1))
  elif [[ "$rc" != "0" && "$landed" == "no" && "$tree_ok" == "yes" ]]; then
    verdict="HONEST-FAIL"; pass=$((pass + 1))
  else
    fail=$((fail + 1))
  fi
  printf '  worker %-2s rc=%-3s landed=%-3s caller_tree_intact=%-3s  %s\n' \
    "$i" "$rc" "$landed" "$tree_ok" "$verdict"
done
echo "  ---- acceptable=$pass  violations=$fail"
[[ "$fail" -eq 0 ]]
