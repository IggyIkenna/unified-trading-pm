#!/bin/bash
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

run_section() {
  local num="$1" script="$2"
  shift 2
  local extra_args=("$@")

  ! should_run "$num" && return 0

  echo ""
  # Hard timeout: each section must complete within 60s
  if timeout 60 bash "$SCRIPT_DIR/$script" "${extra_args[@]}" 2>/dev/null; then
    true
  else
    local rc=$?
    if [ "$rc" -eq 124 ]; then
      echo "  §$num TIMEOUT (>60s) — script killed to prevent runaway"
      OVERALL_FAILS=$((OVERALL_FAILS + 1))
    else
      OVERALL_FAILS=$((OVERALL_FAILS + 1))
    fi
  fi
}

# §13 can take --repo argument
s13_args=()
[ -n "$REPO_FILTER" ] && s13_args=("--repo" "$REPO_FILTER")

run_section 1  s01-governance.sh
run_section 2  s02-code-quality.sh
run_section 3  s03-security.sh
run_section 4  s04-architecture.sh
run_section 6  s06-observability.sh
run_section 8  s08-tech-debt.sh
run_section 9  s09-cross-repo.sh
run_section 11 s11-coverage.sh
run_section 13 s13-stubs.sh "${s13_args[@]}"
run_section 27 s27-contracts.sh

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
