#!/bin/bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Unified Trading System — Scriptable Audit Runner
#
# Runs all scriptable audit sections (~80% of the 28-section audit prompt).
# Each section uses rg/grep/find — no Python DOTALL regex, no runaway processes.
#
# Usage:
#   bash unified-trading-pm/scripts/audit/run-audit-scriptable.sh
#   bash unified-trading-pm/scripts/audit/run-audit-scriptable.sh --sections 2,3,4
#   bash unified-trading-pm/scripts/audit/run-audit-scriptable.sh --sections 13 --repo execution-service
#
# Scriptable sections (this script):
#   §1  Workspace Governance       — manifest fields, DAG, repo count
#   §2  Code Quality               — QG stub size, os.getenv, file size, basedpyright
#   §3  Security                   — hardcoded secrets, verify=False, AUTH_FAILURE
#   §4  Architecture + §12         — cross-service imports, cloud SDK confinement
#   §6  Observability              — health/readiness, correlation_id, Prometheus, MiFID
#   §8  Technical Debt             — type:ignore, baselines, except ImportError, noqa
#   §9  Cross-Repo Alignment       — SSOT-INDEX, manifest↔topology, orphan repos
#   §11 Coverage Regression        — MIN_COVERAGE calibration, fail_under alignment
#   §13 No Stubs                   — NotImplementedError, TODO, FIXME, STUB
#   §27 Contract Adoption          — UIC/UAC/UTL checkers, VCR cassettes
#
# Requires semantic review (NOT scripted here):
#   §5  Schema Governance          — Decimal vs float decisions need review
#   §7  Deployment                 — topology YAML + checklist phase review
#   §10 Integration Test Coverage  — T3+ presence check (some, not all)
#   §14 Orphaned Code              — vulture + cross-repo rg (slow, semi-manual)
#   §15 CI/CD Pipeline Quality     — workflow YAML review
#   §16 UI/npm Governance          — package.json + vitest presence
#   §17 Tooling SSOT & DRY         — semantic review
#   §18 Semver Hardening           — version bump approval gate logic
#   §19 Repository Readiness       — CR/DR/BR gate per-repo checklist
#   §20-26 Domain/Perf/E2E         — mostly semantic + manual test runs

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$WORKSPACE_ROOT"

# ── Argument parsing ──────────────────────────────────────────────────────────
SECTIONS_FILTER=""
REPO_FILTER=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sections) SECTIONS_FILTER="$2"; shift 2 ;;
    --repo)     REPO_FILTER="$2";     shift 2 ;;
    --help|-h)
      grep '^#' "$0" | sed 's/^# //' | sed 's/^#//'
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

should_run() {
  local section="$1"  # e.g. "1", "13"
  [ -z "$SECTIONS_FILTER" ] && return 0
  echo "$SECTIONS_FILTER" | tr ',' '\n' | grep -qx "$section"
}

# ── Header ────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║   Unified Trading System — Scriptable Audit                     ║"
echo "║   CATEGORY | CRITERION | STATUS | EVIDENCE                      ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

OVERALL_FAILS=0
OVERALL_WARNS=0

TMPDIR_AUDIT=$(mktemp -d)
trap 'rm -rf "$TMPDIR_AUDIT"' EXIT

run_section_bg() {
  local num="$1" script="$2"
  shift 2
  local extra_args=("$@")

  ! should_run "$num" && return 0

  local outfile="$TMPDIR_AUDIT/s${num}.out"
  local rcfile="$TMPDIR_AUDIT/s${num}.rc"
  (
    set +e  # prevent -e from killing subshell before rcfile is written
    timeout 60 bash "$SCRIPT_DIR/$script" "${extra_args[@]}" > "$outfile" 2>/dev/null
    echo $? > "$rcfile"
  ) &
}

# §13 can take --repo argument
s13_args=()
[ -n "$REPO_FILTER" ] && s13_args=("--repo" "$REPO_FILTER")

# Launch all sections in parallel (they are independent rg/grep/find scans).
# Each section writes to a temp file; we wait for all, then print in canonical order.
run_section_bg 1  s01-governance.sh
run_section_bg 2  s02-code-quality.sh
run_section_bg 3  s03-security.sh
run_section_bg 4  s04-architecture.sh
run_section_bg 6  s06-observability.sh
run_section_bg 8  s08-tech-debt.sh
run_section_bg 9  s09-cross-repo.sh
run_section_bg 11 s11-coverage.sh
run_section_bg 13 s13-stubs.sh "${s13_args[@]}"
run_section_bg 27 s27-contracts.sh

# Wait for all background jobs to finish (|| true: prevent -e on non-zero section exit)
wait || true

# Print results in canonical section order and tally FAILs
for num in 1 2 3 4 6 8 9 11 13 27; do
  ! should_run "$num" && continue
  outfile="$TMPDIR_AUDIT/s${num}.out"
  rcfile="$TMPDIR_AUDIT/s${num}.rc"
  echo ""
  cat "$outfile" 2>/dev/null || true
  rc=0
  [ -f "$rcfile" ] && rc=$(cat "$rcfile")
  if [ "$rc" -eq 124 ]; then
    echo "  §$num TIMEOUT (>60s) — script killed to prevent runaway"
    OVERALL_FAILS=$((OVERALL_FAILS + 1))
  elif [ "$rc" -ne 0 ]; then
    OVERALL_FAILS=$((OVERALL_FAILS + 1))
  fi
done

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
if [ "$OVERALL_FAILS" -gt 0 ]; then
  printf "║  \033[0;31mOVERALL: FAIL\033[0m  (%d section(s) with FAILs)%*s║\n" \
    "$OVERALL_FAILS" $((30 - ${#OVERALL_FAILS})) ""
  echo "╚══════════════════════════════════════════════════════════════════╝"
  echo ""
  echo "Sections NOT covered by this script (require semantic review):"
  echo "  §5 §7 §10 §14-26 — see trading_system_audit_prompt.md"
  exit 1
else
  echo "║  OVERALL: PASS (scriptable sections)                            ║"
  echo "╚══════════════════════════════════════════════════════════════════╝"
  echo ""
  echo "Sections NOT covered by this script (require semantic review):"
  echo "  §5 §7 §10 §14-26 — see trading_system_audit_prompt.md"
  exit 0
fi
