#!/bin/bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# §6 — Observability
# Checks: health/readiness endpoints, correlation_id, Prometheus, MiFID/FCA compliance events,
#         test_event_logging.py presence, memory watchdog.
# Usage: bash unified-trading-pm/scripts/audit/s06-observability.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$SCRIPT_DIR/lib.sh"
cd "$WORKSPACE_ROOT"

echo "=== §6 Observability ==="

# Health/readiness router presence
health_repos=$(rg 'make_health_router|router.*health|/health|/readiness' \
  --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  --glob '!**/tests/**' \
  -l 2>/dev/null | wc -l | tr -d ' ')
if [ "$health_repos" -ge 10 ]; then
  emit "§6" "health/readiness endpoints present (≥10 repos)" "PASS" \
    "$health_repos repos"
elif [ "$health_repos" -ge 5 ]; then
  emit "§6" "health/readiness endpoints present (≥10 repos)" "WARN" \
    "only $health_repos repos — run: rg '/health|/readiness' --type py --glob '!.venv*' -l"
else
  emit "§6" "health/readiness endpoints present (≥10 repos)" "FAIL" \
    "only $health_repos repos"
fi

# correlation_id propagation
corr_repos=$(rg 'correlation_id' --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  --glob '!**/tests/**' \
  -l 2>/dev/null | wc -l | tr -d ' ')
if [ "$corr_repos" -ge 10 ]; then
  emit "§6" "correlation_id propagated (≥10 repos)" "PASS" "$corr_repos repos"
else
  emit "§6" "correlation_id propagated (≥10 repos)" "WARN" "only $corr_repos repos"
fi

# Prometheus metrics
prom_repos=$(rg 'prometheus_client|Histogram|Counter\(|Gauge\(' \
  --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  --glob '!**/tests/**' \
  -l 2>/dev/null | wc -l | tr -d ' ')
if [ "$prom_repos" -ge 5 ]; then
  emit "§6" "Prometheus metrics exported (≥5 repos)" "PASS" "$prom_repos repos"
else
  emit "§6" "Prometheus metrics exported (≥5 repos)" "WARN" "only $prom_repos repos"
fi

# MiFID/FCA compliance events
mifid_repos=$(rg 'TRADE_EXECUTED|ORDER_SUBMITTED|COMPLIANCE' \
  --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  -l 2>/dev/null | wc -l | tr -d ' ')
if [ "$mifid_repos" -ge 2 ]; then
  emit "§6" "MiFID/FCA compliance events (TRADE_EXECUTED, ORDER_SUBMITTED)" "PASS" \
    "$mifid_repos repos"
else
  emit "§6" "MiFID/FCA compliance events (TRADE_EXECUTED, ORDER_SUBMITTED)" "FAIL" \
    "only $mifid_repos repos — required in execution-service and alerting-service"
fi

# test_event_logging.py presence (target ≥40 repos)
event_log_tests=$(rg --files --glob 'test_event_logging.py' \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  2>/dev/null | wc -l | tr -d ' ')
if [ "$event_log_tests" -ge 40 ]; then
  emit "§6" "test_event_logging.py present (≥40 repos)" "PASS" "$event_log_tests files"
elif [ "$event_log_tests" -ge 20 ]; then
  emit "§6" "test_event_logging.py present (≥40 repos)" "WARN" \
    "only $event_log_tests — target is 40+"
else
  emit "§6" "test_event_logging.py present (≥40 repos)" "FAIL" \
    "only $event_log_tests files"
fi

# Grafana dashboard files
grafana_dash=$(rg --files --glob 'trading-overview.json' --glob 'system-health.json' \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  2>/dev/null | wc -l | tr -d ' ')
if [ "$grafana_dash" -ge 2 ]; then
  emit "§6" "Grafana dashboards present (trading-overview + system-health)" "PASS" \
    "$grafana_dash dashboard files"
else
  emit "§6" "Grafana dashboards present (trading-overview + system-health)" "WARN" \
    "only $grafana_dash files — expected trading-overview.json + system-health.json"
fi

# Memory watchdog (85% checkpoint)
mem_watchdog=$(rg 'memory.*85|85.*memory|psutil|memory_watchdog|checkpoint' \
  --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  --glob '!**/tests/**' \
  -l 2>/dev/null | wc -l | tr -d ' ')
if [ "$mem_watchdog" -ge 3 ]; then
  emit "§6" "memory watchdog in long-running services" "PASS" "$mem_watchdog repos"
else
  emit "§6" "memory watchdog in long-running services" "WARN" \
    "only $mem_watchdog repos — check execution-service, market-tick-data-service"
fi

audit_summary
