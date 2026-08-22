#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Unit tests for qg_baseline_merge.py — the anomaly-guard decision behind
# measure-qg-baseline.sh's daily baseline-freshness promotion (governor Trigger 3, closes
# plans/active/qg_host_adaptive_resource_governor_2026_07_14.md's "baseline freshness loop"
# Phase-0 todo). Exercises the merge script directly with crafted JSON fixtures — no real
# quality-gates.sh run, no network — so it stays fast and deterministic. Covers:
#   (A) no prior entry for (repo, env)         -> always PROMOTED (nothing to compare)
#   (B) new peak within the anomaly threshold  -> PROMOTED, baseline value updated
#   (C) new peak >= threshold above prior      -> ANOMALY, baseline value UNCHANGED
#   (D) same (C) input but --force ("true")    -> PROMOTED despite exceeding the threshold
#   (E) new peak below the prior value         -> PROMOTED (a drop is never anomalous)
#   (F) exactly AT the threshold boundary       -> ANOMALY (>= is inclusive, per the script)
#
# Run: bash unified-trading-pm/scripts/dev/test-qg-baseline-anomaly-guard.sh
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MERGE="${SCRIPT_DIR}/qg_baseline_merge.py"
TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT
FAILFILE="$TMP/fails.log"
: > "$FAILFILE"
eq() { if [[ "$2" == "$3" ]]; then echo "PASS: $1 ($3)"; else echo "FAIL: $1 — expected '$2' got '$3'"; echo "$1" >> "$FAILFILE"; fi; }

seed_json() {
    # <path> <repo> <env> <peak_rss_mb>
    python3 -c "
import json
json.dump({'$2': {'$3': {'peak_rss_mb': $4, 'wall_s': 10.0, 'cpu_s': 5.0, 'exit_code': 0, 'quick': False, 'measured_concurrency': 1, 'measured_at_utc': '2026-01-01T00:00:00Z'}}}, open('$1', 'w'))
"
}

read_peak() {
    # <path> <repo> <env>
    python3 -c "
import json
d = json.load(open('$1'))
print(d.get('$2', {}).get('$3', {}).get('peak_rss_mb', 'MISSING'))
"
}

# ── (A) no prior entry — always PROMOTED ──────────────────────────────────────
(
    OUT="$TMP/a.json"
    echo '{}' > "$OUT"
    out="$(python3 "$MERGE" "$OUT" repo-a vm 10.0 1000 5.0 0 false 1 2026-08-16T00:00:00Z false 20)"
    eq "(A) no prior: decision PROMOTED" "PROMOTED 1000" "$out"
    eq "(A) no prior: baseline written" "1000" "$(read_peak "$OUT" repo-a vm)"
)

# ── (B) within threshold (1000 -> 1150, +15% < 20%) — PROMOTED, value updated ──
(
    OUT="$TMP/b.json"
    seed_json "$OUT" repo-b vm 1000
    out="$(python3 "$MERGE" "$OUT" repo-b vm 10.0 1150 5.0 0 false 1 2026-08-16T00:00:00Z false 20)"
    eq "(B) within threshold: decision PROMOTED" "PROMOTED 1150" "$out"
    eq "(B) within threshold: baseline bumped" "1150" "$(read_peak "$OUT" repo-b vm)"
)

# ── (C) over threshold (1000 -> 1300, +30% >= 20%) — ANOMALY, value UNCHANGED ──
(
    OUT="$TMP/c.json"
    seed_json "$OUT" repo-c vm 1000
    out="$(python3 "$MERGE" "$OUT" repo-c vm 10.0 1300 5.0 0 false 1 2026-08-16T00:00:00Z false 20)"
    eq "(C) over threshold: decision ANOMALY" "ANOMALY 1000 1300" "$out"
    eq "(C) over threshold: baseline NOT bumped" "1000" "$(read_peak "$OUT" repo-c vm)"
)

# ── (D) same jump as (C) but force=true — PROMOTED despite exceeding threshold ─
(
    OUT="$TMP/d.json"
    seed_json "$OUT" repo-d vm 1000
    out="$(python3 "$MERGE" "$OUT" repo-d vm 10.0 1300 5.0 0 false 1 2026-08-16T00:00:00Z true 20)"
    eq "(D) --force bypasses guard: decision PROMOTED" "PROMOTED 1300" "$out"
    eq "(D) --force bypasses guard: baseline bumped" "1300" "$(read_peak "$OUT" repo-d vm)"
)

# ── (E) a drop (1000 -> 800) is never anomalous — PROMOTED ────────────────────
(
    OUT="$TMP/e.json"
    seed_json "$OUT" repo-e vm 1000
    out="$(python3 "$MERGE" "$OUT" repo-e vm 10.0 800 5.0 0 false 1 2026-08-16T00:00:00Z false 20)"
    eq "(E) drop: decision PROMOTED" "PROMOTED 800" "$out"
    eq "(E) drop: baseline lowered" "800" "$(read_peak "$OUT" repo-e vm)"
)

# ── (F) exactly at the 20% boundary (1000 -> 1200) — inclusive >=, so ANOMALY ──
(
    OUT="$TMP/f.json"
    seed_json "$OUT" repo-f vm 1000
    out="$(python3 "$MERGE" "$OUT" repo-f vm 10.0 1200 5.0 0 false 1 2026-08-16T00:00:00Z false 20)"
    eq "(F) exact boundary: decision ANOMALY" "ANOMALY 1000 1200" "$out"
    eq "(F) exact boundary: baseline NOT bumped" "1000" "$(read_peak "$OUT" repo-f vm)"
)

echo "────────────────────────────────────────────"
if [[ -s "$FAILFILE" ]]; then
    echo "FAILURES: $(wc -l < "$FAILFILE" | tr -d ' ')"
    exit 1
else
    echo "ALL PASS"
fi
