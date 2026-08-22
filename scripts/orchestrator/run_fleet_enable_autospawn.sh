#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# run_fleet_enable_autospawn.sh — Sequential per-VM rollout of ORCHESTRATOR_AUTOSPAWN_ENABLED=true.
#
# Rolls autospawn to all 11 orchestrator VMs ONE AT A TIME. After each VM:
#   1. Enables the flag via enable_autospawn.sh
#   2. Kills slot-1's worker (tmux kill-session -t orch-slot-1)
#   3. Waits up to 90s for autospawn to re-create the session
#   4. Confirms the new orch-slot-1 session exists before proceeding to next VM
#
# Aborts if autospawn doesn't fire within the wait window on the canary VM
# (vm-orchestrator). For subsequent VMs, failure is logged as a warning and
# rollout continues — operator reviews the results log.
#
# Prerequisites:
#   - AWS CLI configured with ssm:SendCommand + ssm:GetCommandInvocation permissions
#   - unified-trading-pm pulled on each VM (pm-pull.timer or manual git pull)
#     so that scripts/orchestrator/enable_autospawn.sh exists on the VM.
#   - Phase 2 PR (feat(autospawn): AutoSpawnLoop) merged to live-defi-rollout
#     and propagated to all VMs via pm-pull/ao-pull.
#
# Usage:
#   bash scripts/orchestrator/run_fleet_enable_autospawn.sh
#
# Output: per-VM enable-time + first-autospawn-time to STDOUT + /tmp/enable_autospawn_results_<ts>.txt
#
# Safety: SKIP_KILL_TEST=1 skips the kill-and-verify step (dry-enable only).
#         AUTOSPAWN_WAIT_S=N overrides wait after kill before checking session (default 90).
#         CANARY_ABORT=0 disables the abort-on-canary-failure behaviour.

set -euo pipefail

REGION="${AWS_REGION:-ap-northeast-1}"
PM_REPO_PATH="/home/ubuntu/unified-trading-system-repos/unified-trading-pm"
ENABLE_SCRIPT="$PM_REPO_PATH/scripts/orchestrator/enable_autospawn.sh"
AUTOSPAWN_WAIT_S="${AUTOSPAWN_WAIT_S:-90}"
SKIP_KILL_TEST="${SKIP_KILL_TEST:-0}"
CANARY_ABORT="${CANARY_ABORT:-1}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="/tmp/enable_autospawn_results_$TIMESTAMP.txt"

# Sequential VM list — vm-orchestrator first (canary), then alphabetical.
# api-host handled last (best-effort — known SSM issues).
INSTANCE_IDS=(
  "i-007e8d99d12831578"   # vm-orchestrator  (canary — first)
  "i-003be935f72c13d51"   # vm-cefi
  "i-05805eb07fdf180b6"   # vm-defi
  "i-02294132088f23e50"   # vm-ml
  "i-0e89a5f6bd7123521"   # vm-operator-ops
  "i-063bc8dbf59f36220"   # vm-prediction
  "i-005e1bada21b1653f"   # vm-sports
  "i-0a663001399ef5f49"   # vm-tradfi
  "i-0e51b9c73666b3a8b"   # vm-trading-core
  "i-06e33c6e188798333"   # vm-cross-cutting
  "i-0c9b283b31d6b5ca7"   # api-host        (last — best-effort)
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

KILL_AND_VERIFY_CMD="$(cat <<'SCRIPT'
SESSION="orch-slot-1"
WAIT="${AUTOSPAWN_WAIT_S:-90}"
if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "BEFORE: $SESSION exists"
    tmux kill-session -t "$SESSION"
    echo "killed $SESSION at $(date -u)"
else
    echo "BEFORE: $SESSION not running — autospawn will fire on next tick"
fi
echo "Waiting ${WAIT}s for autospawn to re-create $SESSION..."
DEADLINE=$(( $(date +%s) + WAIT ))
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
    if tmux has-session -t "$SESSION" 2>/dev/null; then
        echo "VERIFIED: $SESSION re-created at $(date -u +%H:%M:%SZ)"
        exit 0
    fi
    sleep 5
done
echo "TIMEOUT: $SESSION not re-created within ${WAIT}s"
exit 1
SCRIPT
)"

log "=== run_fleet_enable_autospawn.sh ==="
log "Started: $(ts)"
log "Region: $REGION"
log "Autospawn wait: ${AUTOSPAWN_WAIT_S}s"
log "Skip kill test: $SKIP_KILL_TEST"
log "Canary abort: $CANARY_ABORT"
log ""

# Step 0: PM pull on all VMs (parallel)
log "--- Step 0: PM pull on all VMs (parallel) ---"
PULL_CMD="cd $PM_REPO_PATH && git fetch origin live-defi-rollout && git rebase origin/live-defi-rollout && echo pull-ok"
for INSTANCE_ID in "${INSTANCE_IDS[@]}"; do
  CMD_ID=$(aws ssm send-command \
    --instance-ids "$INSTANCE_ID" \
    --document-name "AWS-RunShellScript" \
    --parameters "commands=[\"$PULL_CMD\"]" \
    --comment "pm-pull before enable_autospawn" \
    --region "$REGION" \
    --query "Command.CommandId" \
    --output text 2>/dev/null) || CMD_ID="FAILED"
  log "  pull → $INSTANCE_ID: $CMD_ID"
done
log "Waiting 40s for pulls..."
sleep 40
log ""

# Sequential per-VM enable
IS_CANARY=true
FAILED_VMS=()

for i in "${!INSTANCE_IDS[@]}"; do
  INSTANCE_ID="${INSTANCE_IDS[$i]}"
  VM_NAME="${VM_NAMES[$i]}"

  log "--- $VM_NAME ($INSTANCE_ID) [$(ts)] ---"

  # Enable autospawn
  ENABLE_CMD="bash $ENABLE_SCRIPT"
  CMD_ID=$(aws ssm send-command \
    --instance-ids "$INSTANCE_ID" \
    --document-name "AWS-RunShellScript" \
    --parameters "commands=[\"$ENABLE_CMD\"]" \
    --comment "enable_autospawn on $VM_NAME" \
    --region "$REGION" \
    --query "Command.CommandId" \
    --output text 2>/dev/null) || { log "  WARN: ssm send-command failed for $VM_NAME"; FAILED_VMS+=("$VM_NAME"); IS_CANARY=false; continue; }

  log "  enable command: $CMD_ID"
  sleep 15

  OUTPUT=$(aws ssm get-command-invocation \
    --command-id "$CMD_ID" \
    --instance-id "$INSTANCE_ID" \
    --region "$REGION" \
    --query "StandardOutputContent" \
    --output text 2>/dev/null) || OUTPUT="(failed to retrieve)"
  log "$OUTPUT"
  log "  enabled at $(ts)"

  # Kill-and-verify step (unless skipped)
  if [[ "$SKIP_KILL_TEST" == "1" ]]; then
    log "  SKIP_KILL_TEST=1 — skipping kill-and-verify"
  else
    VERIFY_CMD_ID=$(aws ssm send-command \
      --instance-ids "$INSTANCE_ID" \
      --document-name "AWS-RunShellScript" \
      --parameters "commands=[\"AUTOSPAWN_WAIT_S=$AUTOSPAWN_WAIT_S && $KILL_AND_VERIFY_CMD\"]" \
      --comment "autospawn kill-verify on $VM_NAME" \
      --region "$REGION" \
      --query "Command.CommandId" \
      --output text 2>/dev/null) || { log "  WARN: verify ssm failed for $VM_NAME"; IS_CANARY=false; continue; }

    log "  verify command: $VERIFY_CMD_ID"
    log "  Waiting $(( AUTOSPAWN_WAIT_S + 30 ))s for kill+re-spawn cycle..."
    sleep $(( AUTOSPAWN_WAIT_S + 30 ))

    VERIFY_OUT=$(aws ssm get-command-invocation \
      --command-id "$VERIFY_CMD_ID" \
      --instance-id "$INSTANCE_ID" \
      --region "$REGION" \
      --query "StandardOutputContent" \
      --output text 2>/dev/null) || VERIFY_OUT="(failed to retrieve)"
    VERIFY_STATUS=$(aws ssm get-command-invocation \
      --command-id "$VERIFY_CMD_ID" \
      --instance-id "$INSTANCE_ID" \
      --region "$REGION" \
      --query "StatusDetails" \
      --output text 2>/dev/null) || VERIFY_STATUS="Unknown"

    log "$VERIFY_OUT"
    log "  verify status: $VERIFY_STATUS"

    if echo "$VERIFY_OUT" | grep -q "VERIFIED"; then
      log "  ✅ $VM_NAME autospawn confirmed"
    else
      log "  ⚠️  $VM_NAME autospawn NOT confirmed within window"
      FAILED_VMS+=("$VM_NAME")
      if [[ "$IS_CANARY" == "true" && "$CANARY_ABORT" == "1" ]]; then
        log "  🛑 CANARY ABORT: vm-orchestrator autospawn failed. Fix before rolling to fleet."
        log "Results: $RESULTS_FILE"
        exit 1
      fi
    fi
  fi

  IS_CANARY=false
  log ""
done

log "=== Summary ==="
if [[ "${#FAILED_VMS[@]}" -gt 0 ]]; then
  log "VMs with issues: ${FAILED_VMS[*]}"
else
  log "All VMs processed successfully."
fi
log "Results: $RESULTS_FILE"
log "Finished: $(ts)"
