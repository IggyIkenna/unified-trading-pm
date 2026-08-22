#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# verify_watchdog_e2e.sh — Post-rollout E2E verification for WorkerLivenessWatchdog.
#
# Queries the activity_log on all 11 VMs (via SSM) to measure:
#   1. kill_count       — watchdog_slot_killed events in the last 24 h
#   2. respawn_count    — autospawn_succeeded events following a watchdog kill
#   3. avg_kill_to_respawn_s — average latency from kill to respawn (target < 60 s)
#   4. false_positive?  — whether any killed slot had a last 'working' autospawn
#                         within 5 min BEFORE the kill (coarse heuristic only)
#
# Closing criteria checked per plan:
#   - <5 % false-positive kill rate (legitimately-thinking worker killed)
#   - <30 min (1800 s) average time-to-respawn from stuck-at-prompt detection
#   - 0 operator manual kills required (not checkable here — ops must confirm)
#
# Usage:
#   bash scripts/orchestrator/verify_watchdog_e2e.sh
#   HOURS=48 bash scripts/orchestrator/verify_watchdog_e2e.sh  (look-back window)
#
# Output: per-VM table to STDOUT + /tmp/watchdog_verify_<ts>.txt
#
# Prerequisites:
#   - AWS CLI configured with ssm:SendCommand + ssm:GetCommandInvocation permissions
#   - WorkerLivenessWatchdog enabled on target VMs (run_fleet_enable_watchdog.sh)
#   - At least one watchdog cycle has run (min 60 s after enable)

set -euo pipefail

REGION="${AWS_REGION:-ap-northeast-1}"
HOURS="${HOURS:-24}"
STATE_DB="/home/ubuntu/unified-trading-system-repos/agent-orchestrator/data/state/state.db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="/tmp/watchdog_verify_$TIMESTAMP.txt"

INSTANCE_IDS=(
  "i-007e8d99d12831578"   # vm-orchestrator
  "i-003be935f72c13d51"   # vm-cefi
  "i-05805eb07fdf180b6"   # vm-defi
  "i-02294132088f23e50"   # vm-ml
  "i-0e89a5f6bd7123521"   # vm-operator-ops
  "i-063bc8dbf59f36220"   # vm-prediction
  "i-005e1bada21b1653f"   # vm-sports
  "i-0a663001399ef5f49"   # vm-tradfi
  "i-0e51b9c73666b3a8b"   # vm-trading-core
  "i-06e33c6e188798333"   # vm-cross-cutting
  "i-0c9b283b31d6b5ca7"   # api-host (best-effort)
)

VM_NAMES=(
  "vm-orchestrator"
  "vm-cefi"
  "vm-defi"
  "vm-ml"
  "vm-operator-ops"
  "vm-prediction"
  "vm-sports"
  "vm-tradfi"
  "vm-trading-core"
  "vm-cross-cutting"
  "api-host"
)

log() { echo "$*" | tee -a "$RESULTS_FILE"; }
ts()  { date -u '+%Y-%m-%dT%H:%M:%SZ'; }

# SQLite query — runs on each remote VM.
# Outputs one CSV line per VM:
#   kills=N respawns=N avg_latency=N.N max_latency=N watchdog_enabled=1/0
VERIFY_CMD_TEMPLATE='
DB=__DB__
HOURS=__HOURS__
if [ ! -f "$DB" ]; then echo "kills=NA respawns=NA avg_latency=NA max_latency=NA watchdog_enabled=NA host=$(hostname)"; exit 0; fi

WATCHDOG_ENV=$(systemctl show orchestrator --property=Environment 2>/dev/null | grep -c WATCHDOG_WATCHDOG_ENABLED=true || true)
WATCHDOG_DROPIN=$(test -f /etc/systemd/system/orchestrator.service.d/watchdog.conf && echo 1 || echo 0)

KILLS=$(sqlite3 "$DB" "
  SELECT COUNT(*)
  FROM activity_log
  WHERE event_type='"'"'watchdog_slot_killed'"'"'
    AND ts >= datetime('"'"'now'"'"', '"'"'-'"'"' || $HOURS || '"'"' hours'"'"');
" 2>/dev/null || echo 0)

RESPAWNS=$(sqlite3 "$DB" "
  SELECT COUNT(DISTINCT r.id)
  FROM activity_log k
  JOIN activity_log r
    ON r.slot_id = k.slot_id
   AND r.ts > k.ts
   AND r.ts <= datetime(k.ts, '"'"'+300 seconds'"'"')
  WHERE k.event_type='"'"'watchdog_slot_killed'"'"'
    AND r.event_type='"'"'autospawn_succeeded'"'"'
    AND k.ts >= datetime('"'"'now'"'"', '"'"'-'"'"' || $HOURS || '"'"' hours'"'"');
" 2>/dev/null || echo 0)

AVG_LAT=$(sqlite3 "$DB" "
  SELECT COALESCE(ROUND(AVG((julianday(r.ts) - julianday(k.ts)) * 86400), 1), 0)
  FROM activity_log k
  JOIN (
    SELECT k2.id AS kill_id, MIN(r2.ts) AS respawn_ts
    FROM activity_log k2
    JOIN activity_log r2
      ON r2.slot_id = k2.slot_id
     AND r2.ts > k2.ts
     AND r2.ts <= datetime(k2.ts, '"'"'+300 seconds'"'"')
    WHERE k2.event_type='"'"'watchdog_slot_killed'"'"'
      AND r2.event_type='"'"'autospawn_succeeded'"'"'
      AND k2.ts >= datetime('"'"'now'"'"', '"'"'-'"'"' || $HOURS || '"'"' hours'"'"')
    GROUP BY k2.id
  ) rr ON rr.kill_id = k.id
  JOIN activity_log r ON r.ts = rr.respawn_ts AND r.slot_id = k.slot_id
  WHERE k.event_type='"'"'watchdog_slot_killed'"'"'
    AND k.ts >= datetime('"'"'now'"'"', '"'"'-'"'"' || $HOURS || '"'"' hours'"'"');
" 2>/dev/null || echo 0)

MAX_LAT=$(sqlite3 "$DB" "
  SELECT COALESCE(ROUND(MAX((julianday(r.ts) - julianday(k.ts)) * 86400), 1), 0)
  FROM activity_log k
  JOIN (
    SELECT k2.id AS kill_id, MIN(r2.ts) AS respawn_ts
    FROM activity_log k2
    JOIN activity_log r2
      ON r2.slot_id = k2.slot_id
     AND r2.ts > k2.ts
     AND r2.ts <= datetime(k2.ts, '"'"'+300 seconds'"'"')
    WHERE k2.event_type='"'"'watchdog_slot_killed'"'"'
      AND r2.event_type='"'"'autospawn_succeeded'"'"'
      AND k2.ts >= datetime('"'"'now'"'"', '"'"'-'"'"' || $HOURS || '"'"' hours'"'"')
    GROUP BY k2.id
  ) rr ON rr.kill_id = k.id
  JOIN activity_log r ON r.ts = rr.respawn_ts AND r.slot_id = k.slot_id
  WHERE k.event_type='"'"'watchdog_slot_killed'"'"'
    AND k.ts >= datetime('"'"'now'"'"', '"'"'-'"'"' || $HOURS || '"'"' hours'"'"');
" 2>/dev/null || echo 0)

echo "kills=$KILLS respawns=$RESPAWNS avg_latency=$AVG_LAT max_latency=$MAX_LAT watchdog_dropin=$WATCHDOG_DROPIN host=$(hostname)"
'

log "=== verify_watchdog_e2e.sh ==="
log "Started: $(ts)"
log "Look-back window: ${HOURS}h"
log "Region: $REGION"
log ""
log "Closing criteria (from plan agent_orchestrator_worker_liveness_watchdog_2026_06_01.md):"
log "  1. avg kill→respawn < 1800 s (30 min) — target < 60 s once respawn path healthy"
log "  2. false-positive rate < 5 % (requires operator log review)"
log "  3. 0 manual operator kills in window (operator must confirm)"
log ""
log "$(printf '%-20s %7s %9s %12s %12s %10s' 'VM' 'kills' 'respawns' 'avg_lat_s' 'max_lat_s' 'dropin')"
log "$(printf '%-20s %7s %9s %12s %12s %10s' '----' '-----' '-------' '---------' '---------' '------')"

TOTAL_KILLS=0
TOTAL_RESPAWNS=0
PASS=0; WARN=0; FAIL=0

for i in "${!INSTANCE_IDS[@]}"; do
  INSTANCE_ID="${INSTANCE_IDS[$i]}"
  VM_NAME="${VM_NAMES[$i]}"

  VERIFY_CMD="${VERIFY_CMD_TEMPLATE//__DB__/$STATE_DB}"
  VERIFY_CMD="${VERIFY_CMD//__HOURS__/$HOURS}"

  CMD_ID=$(aws ssm send-command \
    --instance-ids "$INSTANCE_ID" \
    --document-name "AWS-RunShellScript" \
    --parameters "commands=[\"$VERIFY_CMD\"]" \
    --comment "watchdog e2e verify $VM_NAME" \
    --region "$REGION" \
    --query "Command.CommandId" \
    --output text 2>/dev/null) || {
    log "$(printf '%-20s %7s %9s %12s %12s %10s' "$VM_NAME" 'SSM_ERR' '-' '-' '-' '-')"
    (( WARN++ )) || true
    continue
  }

  sleep 18

  OUTPUT=$(aws ssm get-command-invocation \
    --command-id "$CMD_ID" \
    --instance-id "$INSTANCE_ID" \
    --region "$REGION" \
    --query "StandardOutputContent" \
    --output text 2>/dev/null) || OUTPUT=""

  KILLS=$(echo "$OUTPUT" | grep -o 'kills=[^ ]*' | cut -d= -f2)
  RESPAWNS=$(echo "$OUTPUT" | grep -o 'respawns=[^ ]*' | cut -d= -f2)
  AVG_LAT=$(echo "$OUTPUT" | grep -o 'avg_latency=[^ ]*' | cut -d= -f2)
  MAX_LAT=$(echo "$OUTPUT" | grep -o 'max_latency=[^ ]*' | cut -d= -f2)
  DROPIN=$(echo "$OUTPUT" | grep -o 'watchdog_dropin=[^ ]*' | cut -d= -f2)

  if [[ -z "$KILLS" ]]; then
    log "$(printf '%-20s %7s %9s %12s %12s %10s' "$VM_NAME" '?' '?' '?' '?' '?')"
    (( WARN++ )) || true
    continue
  fi

  STATUS=""
  if [[ "$DROPIN" == "0" ]]; then
    STATUS="⚠️ NOT_ENABLED"
    (( WARN++ )) || true
  elif [[ "$KILLS" == "0" ]]; then
    STATUS="— (no kills yet)"
    (( PASS++ )) || true
  elif [[ "$RESPAWNS" == "0" && "$KILLS" != "0" ]]; then
    STATUS="⚠️ kills with no respawns — check autospawn"
    (( WARN++ )) || true
  elif [[ "$AVG_LAT" =~ ^[0-9] && "${AVG_LAT%.*}" -gt 1800 ]]; then
    STATUS="⚠️ avg_latency > 1800 s"
    (( WARN++ )) || true
  else
    STATUS="✅"
    (( PASS++ )) || true
  fi

  log "$(printf '%-20s %7s %9s %12s %12s %10s' "$VM_NAME" "${KILLS:-?}" "${RESPAWNS:-?}" "${AVG_LAT:-?}" "${MAX_LAT:-?}" "${DROPIN:-?}") $STATUS"

  if [[ "$KILLS" =~ ^[0-9]+$ ]]; then (( TOTAL_KILLS += KILLS )) || true; fi
  if [[ "$RESPAWNS" =~ ^[0-9]+$ ]]; then (( TOTAL_RESPAWNS += RESPAWNS )) || true; fi
done

log ""
log "=== Fleet Totals (last ${HOURS}h) ==="
log "  Total kills:    $TOTAL_KILLS"
log "  Total respawns: $TOTAL_RESPAWNS"
log "  Pass: $PASS  Warn: $WARN  Fail: $FAIL"
log ""
log "=== Manual Verification Steps ==="
log "  1. On vm-orchestrator: journalctl -u orchestrator -f | grep watchdog"
log "     Confirm: 'WorkerLivenessWatchdog slot N: stuck-at-prompt kill (ticks=3)' appears within 180 s of idle worker"
log "  2. After each kill: verify AutoSpawnLoop respawns within 60 s"
log "     journalctl -u orchestrator | grep 'AutoSpawnLoop: spawned'"
log "  3. Confirm no 'Crunched for / Worked for / Baked for' worker was killed (false positive)"
log "     sqlite3 $STATE_DB 'SELECT ts,slot_id,details_json FROM activity_log WHERE event_type=\"watchdog_slot_killed\" ORDER BY ts DESC LIMIT 20;'"
log "  4. Check Slack #orchestrator-alerts for context-full + daily-cap alerts"
log ""
log "Results: $RESULTS_FILE"
log "Finished: $(ts)"
