#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# probe_plan_regen_pipeline.sh — synthetic health probe for the
# PM-pull → PlanRegenLoop → /api/backlog ingestion pipeline.
#
# orchestrator_master.md P3 (MIGRATED FROM e2e_test_plan_regen_pipeline_2026_05_29):
# the one-shot e2e test verified the pipeline once but left no continuous guard —
# a silent regression of PM-pull or regen would go undetected. This probe POSTs
# /api/backlog/regen on the local orchestrator and asserts the round-trip is alive:
# `ok==true` AND `scanned_plans>0` (scanned_plans>0 proves the PM repo is present +
# current on this VM — i.e. PM-pull is working — AND that regen walked the plans).
#
# Run on the orchestrator VM (loopback caller is inside the auth trust boundary, so
# no token needed). Intended as a daily cron:
#   0 6 * * * bash .../scripts/orchestrator/probe_plan_regen_pipeline.sh >> /var/log/plan-regen-probe.log 2>&1
#
# Exit 0 = healthy; exit 1 = pipeline degraded (cron mailer / log surfaces it).
# Override the URL with ORCHESTRATOR_URL (default loopback :8026).
set -uo pipefail

TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# The central orchestrator listens on 127.0.0.1:8765 (behind nginx); worker/other
# VMs may use :8026. Try ORCHESTRATOR_URL if set, else probe both ports.
if [[ -n "${ORCHESTRATOR_URL:-}" ]]; then
  CANDIDATES=("${ORCHESTRATOR_URL}")
else
  CANDIDATES=("http://localhost:8765" "http://localhost:8026")
fi

resp=""
URL=""
for u in "${CANDIDATES[@]}"; do
  resp="$(curl -sS -m 30 -X POST "${u}/api/backlog/regen" -H 'Content-Type: application/json' 2>/dev/null || echo "")"
  if [[ -n "${resp}" ]]; then URL="${u}"; break; fi
done
if [[ -z "${resp}" ]]; then
  echo "[plan-regen-probe ${TS}] FAIL — no response from ${CANDIDATES[*]} /api/backlog/regen (orchestrator down / unreachable)"
  exit 1
fi

# Parse with python3 (always present on the VMs; avoids a jq dependency).
read -r ok scanned new total < <(python3 - "$resp" <<'PY'
import json, sys
try:
    d = json.loads(sys.argv[1])
except Exception:
    print("parse_error 0 0 0"); raise SystemExit(0)
print(
    str(d.get("ok", False)).lower(),
    int(d.get("scanned_plans", 0) or 0),
    int(d.get("new_tasks", 0) or 0),
    int(d.get("total_tasks", 0) or 0),
)
PY
)

if [[ "${ok}" != "true" ]]; then
  echo "[plan-regen-probe ${TS}] FAIL — regen returned ok=${ok} (resp: ${resp:0:200})"
  exit 1
fi
if [[ "${scanned}" -le 0 ]]; then
  echo "[plan-regen-probe ${TS}] FAIL — scanned_plans=${scanned} (PM repo missing/empty on this VM → PM-pull broken?)"
  exit 1
fi

echo "[plan-regen-probe ${TS}] OK — pipeline alive: scanned_plans=${scanned} new_tasks=${new} total_tasks=${total}"
exit 0
