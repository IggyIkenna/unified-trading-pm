#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# verify_fleet_autonomy_health.sh — standing deploy-currency + flag-liveness check
# for the 11-VM orchestrator fleet. READ-ONLY (no mutations) — safe to run any time.
#
# For each VM it reports, via SSM:
#   (a) deployed agent-orchestrator git HEAD vs origin/live-defi-rollout (behind-count)
#   (b) the four autonomy flags live in the orchestrator process environment:
#         ORCHESTRATOR_AUTOSPAWN_ENABLED / ORCHESTRATOR_WORKER_WATCHDOG_ENABLED /
#         ORCHESTRATOR_REGEN_PRUNE_STALE / ORCHESTRATOR_VM_ID
#   (c) the /health version string (localhost:8026)
#
# A VM is ✅ only when: behind-count == 0 AND all four flags present AND /health responds.
# Anything else is ⚠️ with the specific reason — that VM is not fully running the
# 24/7-autonomy loop. This is the live tool behind audit § M checks m1b/m2c/m3b/m3c.
#
# Prerequisites: AWS CLI with ssm:SendCommand + ssm:GetCommandInvocation.
# Usage:   bash scripts/orchestrator/verify_fleet_autonomy_health.sh
# Output:  per-VM ✅/⚠️ table to STDOUT + /tmp/fleet_autonomy_health_<ts>.txt
# Tunable: AWS_REGION (default ap-northeast-1), HEALTH_PORT (default 8026).

set -euo pipefail

REGION="${AWS_REGION:-ap-northeast-1}"
HEALTH_PORT="${HEALTH_PORT:-8026}"
AO_PATH="/home/ubuntu/unified-trading-system-repos/agent-orchestrator"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="/tmp/fleet_autonomy_health_$TIMESTAMP.txt"

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
  "i-0c9b283b31d6b5ca7"   # api-host
)
VM_NAMES=(
  "vm-orchestrator" "vm-cefi" "vm-defi" "vm-ml" "vm-operator-ops"
  "vm-prediction" "vm-sports" "vm-tradfi" "vm-trading-core" "vm-cross-cutting" "api-host"
)

log() { echo "$*" | tee -a "$RESULTS_FILE"; }
ts()  { date -u '+%Y-%m-%dT%H:%M:%SZ'; }

# Remote snippet — gathers all three signals into a parseable single block.
read -r -d '' REMOTE_PROBE <<PROBE || true
set +e
cd $AO_PATH 2>/dev/null || { echo "RESULT behind=NA flags=0/4 ver=NA note=AO_MISSING"; exit 0; }
# SSM runs as root but the repo is owned by ubuntu (orchestrator's user) → run
# git as ubuntu so it shares ubuntu's git identity + avoids dubious-ownership.
GIT="sudo -u ubuntu git -C $AO_PATH"
\$GIT fetch origin live-defi-rollout -q 2>/dev/null
HEADSHA=\$(\$GIT rev-parse --short HEAD 2>/dev/null)
REMOTESHA=\$(\$GIT rev-parse --short origin/live-defi-rollout 2>/dev/null)
BEHIND=\$(\$GIT rev-list --count HEAD..origin/live-defi-rollout 2>/dev/null)
PID=\$(systemctl show orchestrator --property=MainPID --value 2>/dev/null)
NFLAGS=\$(tr '\0' '\n' < /proc/\$PID/environ 2>/dev/null | grep -cE '^ORCHESTRATOR_(AUTOSPAWN_ENABLED|WORKER_WATCHDOG_ENABLED|REGEN_PRUNE_STALE|VM_ID)=')
MISSING=\$(for f in AUTOSPAWN_ENABLED WORKER_WATCHDOG_ENABLED REGEN_PRUNE_STALE VM_ID; do tr '\0' '\n' < /proc/\$PID/environ 2>/dev/null | grep -q "^ORCHESTRATOR_\$f=" || echo -n "\$f "; done)
VER=\$(curl -s --max-time 4 http://localhost:$HEALTH_PORT/health 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin).get("version","NA"))' 2>/dev/null || echo NA)
echo "RESULT head=\$HEADSHA remote=\$REMOTESHA behind=\${BEHIND:-NA} flags=\${NFLAGS:-0}/4 missing=[\${MISSING}] ver=\${VER}"
PROBE

log "=== verify_fleet_autonomy_health.sh ==="
log "Started: $(ts) | region: $REGION | health-port: $HEALTH_PORT"
log ""

CMD_IDS=()
for i in "${!INSTANCE_IDS[@]}"; do
  INSTANCE_ID="${INSTANCE_IDS[$i]}"
  CMD_ID=$(aws ssm send-command \
    --instance-ids "$INSTANCE_ID" \
    --document-name "AWS-RunShellScript" \
    --parameters commands="[\"$(echo "$REMOTE_PROBE" | sed 's/"/\\"/g')\"]" \
    --comment "fleet autonomy health probe" \
    --region "$REGION" \
    --query "Command.CommandId" \
    --output text 2>/dev/null) || CMD_ID="FAILED"
  CMD_IDS[$i]="$CMD_ID"
done

log "Probes dispatched to ${#INSTANCE_IDS[@]} VMs; waiting 25s..."
sleep 25
log ""
log "VM                  STATUS  detail"
log "------------------  ------  -------------------------------------------------"

OK=0; WARN=0
for i in "${!INSTANCE_IDS[@]}"; do
  VM_NAME="${VM_NAMES[$i]}"
  INSTANCE_ID="${INSTANCE_IDS[$i]}"
  CMD_ID="${CMD_IDS[$i]}"
  if [[ "$CMD_ID" == "FAILED" ]]; then
    printf -v ROW "%-18s  ⚠️     ssm send-command failed" "$VM_NAME"; log "$ROW"; WARN=$((WARN+1)); continue
  fi
  OUT=$(aws ssm get-command-invocation --command-id "$CMD_ID" --instance-id "$INSTANCE_ID" \
        --region "$REGION" --query "StandardOutputContent" --output text 2>/dev/null) || OUT="(no output)"
  LINE=$(echo "$OUT" | grep '^RESULT' | head -1 || true)
  [[ -z "$LINE" ]] && LINE="$OUT"
  BEHIND=$(echo "$LINE" | grep -oE 'behind=[^ ]+' | cut -d= -f2 || true)
  FLAGS=$(echo "$LINE"  | grep -oE 'flags=[^ ]+'  | cut -d= -f2 || true)
  VER=$(echo "$LINE"    | grep -oE 'ver=[^ ]+'    | cut -d= -f2 || true)
  if [[ "$BEHIND" == "0" && "$FLAGS" == "4/4" && -n "$VER" && "$VER" != "NA" ]]; then
    printf -v ROW "%-18s  ✅     behind=0 flags=4/4 ver=%s" "$VM_NAME" "$VER"; OK=$((OK+1))
  else
    MISS=$(echo "$LINE" | grep -oE 'missing=\[[^]]*\]' || true)
    printf -v ROW "%-18s  ⚠️     behind=%s flags=%s ver=%s %s" "$VM_NAME" "${BEHIND:-?}" "${FLAGS:-?}" "${VER:-?}" "${MISS:-}"; WARN=$((WARN+1))
  fi
  log "$ROW"
done

log ""
log "Summary: ✅ $OK  /  ⚠️ $WARN  (of ${#INSTANCE_IDS[@]} VMs) @ $(ts)"
log "Full results: $RESULTS_FILE"
[[ "$WARN" -eq 0 ]] && exit 0 || exit 1
