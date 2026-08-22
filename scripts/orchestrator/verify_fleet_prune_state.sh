#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# verify_fleet_prune_state.sh — Post-rollout verification: confirm queued counts
# match /api/backlog totals on all 11 VMs.
#
# Run after run_fleet_enable_prune.sh has completed and at least one regen
# cycle has passed on every VM.
#
# What it checks per VM:
#   - state.db queued+unassigned row count
#   - backlog.yaml task count (wc -l / 22 lines per task)
#   - Drift = abs(db_count - yaml_count) — must be ≤ 5
#
# Usage:
#   bash scripts/orchestrator/verify_fleet_prune_state.sh
#
# Output: table to STDOUT + /tmp/prune_verify_<ts>.txt

set -euo pipefail

REGION="${AWS_REGION:-ap-northeast-1}"
PM_REPO_PATH="/home/ubuntu/unified-trading-system-repos/unified-trading-pm"
ORCH_BASE="/home/ubuntu/unified-trading-system-repos/agent-orchestrator"
STATE_DB="$ORCH_BASE/data/state/state.db"
BACKLOG_YAML="$ORCH_BASE/backlog.yaml"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="/tmp/prune_verify_$TIMESTAMP.txt"

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

VERIFY_CMD="$(cat <<'SCRIPT'
DB="/home/ubuntu/unified-trading-system-repos/agent-orchestrator/data/state/state.db"
YAML="/home/ubuntu/unified-trading-system-repos/agent-orchestrator/backlog.yaml"
DB_Q="N/A"; YAML_Q="N/A"
if [ -f "$DB" ]; then
  DB_Q=$(sqlite3 "$DB" "SELECT COUNT(*) FROM tasks WHERE status='queued' AND dispatched_to IS NULL;" 2>/dev/null || echo "ERR")
fi
if [ -f "$YAML" ]; then
  # Count "id:" lines as task count proxy
  YAML_Q=$(grep -c "^  id:" "$YAML" 2>/dev/null || echo "0")
fi
echo "db_queued=$DB_Q yaml_tasks=$YAML_Q host=$(hostname)"
SCRIPT
)"

log "=== verify_fleet_prune_state.sh ==="
log "Started: $(date -u)"
log ""
log "$(printf '%-20s %10s %10s %8s' 'VM' 'db_queued' 'yaml_tasks' 'drift')"
log "$(printf '%-20s %10s %10s %8s' '----' '---------' '----------' '-----')"

PASS=0; WARN=0; FAIL=0

for i in "${!INSTANCE_IDS[@]}"; do
  INSTANCE_ID="${INSTANCE_IDS[$i]}"
  VM_NAME="${VM_NAMES[$i]}"

  CMD_ID=$(aws ssm send-command \
    --instance-ids "$INSTANCE_ID" \
    --document-name "AWS-RunShellScript" \
    --parameters "commands=[\"$VERIFY_CMD\"]" \
    --comment "prune verify $VM_NAME" \
    --region "$REGION" \
    --query "Command.CommandId" \
    --output text 2>/dev/null) || { log "$(printf '%-20s %10s %10s %8s' "$VM_NAME" 'SSM_FAIL' '-' '-')"; (( WARN++ )) || true; continue; }

  sleep 15

  OUTPUT=$(aws ssm get-command-invocation \
    --command-id "$CMD_ID" \
    --instance-id "$INSTANCE_ID" \
    --region "$REGION" \
    --query "StandardOutputContent" \
    --output text 2>/dev/null) || OUTPUT=""

  DB_Q=$(echo "$OUTPUT" | grep -o 'db_queued=[^ ]*' | cut -d= -f2)
  YAML_Q=$(echo "$OUTPUT" | grep -o 'yaml_tasks=[^ ]*' | cut -d= -f2)

  if [[ -z "$DB_Q" || -z "$YAML_Q" ]]; then
    log "$(printf '%-20s %10s %10s %8s' "$VM_NAME" '?' '?' '?')"
    (( WARN++ )) || true
    continue
  fi

  if [[ "$DB_Q" =~ ^[0-9]+$ && "$YAML_Q" =~ ^[0-9]+$ ]]; then
    DRIFT=$(( DB_Q - YAML_Q ))
    DRIFT_ABS=${DRIFT#-}
    if [[ "$DRIFT_ABS" -le 5 ]]; then
      STATUS="✅"
      (( PASS++ )) || true
    else
      STATUS="⚠️"
      (( WARN++ )) || true
    fi
    log "$(printf '%-20s %10s %10s %8s' "$VM_NAME" "$DB_Q" "$YAML_Q" "$DRIFT") $STATUS"
  else
    log "$(printf '%-20s %10s %10s %8s' "$VM_NAME" "$DB_Q" "$YAML_Q" 'err')"
    (( FAIL++ )) || true
  fi
done

log ""
log "Results: pass=$PASS warn=$WARN fail=$FAIL"
log "Results saved: $RESULTS_FILE"
log "Finished: $(date -u)"
