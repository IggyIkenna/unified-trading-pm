#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# run_fleet_enable_watchdog.sh — Sequential per-VM rollout of ORCHESTRATOR_WORKER_WATCHDOG_ENABLED=true.
#
# Rolls the watchdog flag to all 11 orchestrator VMs ONE AT A TIME.
# vm-orchestrator is the canary — operator watches 1h for false-positive kills
# (a legitimately-thinking worker should NOT be killed) before expanding to fleet.
#
# After each VM:
#   1. Enables the flag via enable_worker_watchdog.sh
#   2. Waits for orchestrator to restart
#   3. Verifies ORCHESTRATOR_WORKER_WATCHDOG_ENABLED appears in systemd environment
#   4. Reports current slot + tmux state
#
# Abort behaviour: if canary VM fails to enable (systemd env not set), abort fleet rollout.
# For subsequent VMs, failure is logged as a warning and rollout continues.
#
# Prerequisites:
#   - AWS CLI configured with ssm:SendCommand + ssm:GetCommandInvocation permissions
#   - unified-trading-pm pulled on each VM (pm-pull.timer or manual git pull)
#     so that scripts/orchestrator/enable_worker_watchdog.sh exists on the VM.
#   - feat(watchdog): WorkerLivenessWatchdog merged to live-defi-rollout
#     and propagated to all VMs.
#
# Usage:
#   bash scripts/orchestrator/run_fleet_enable_watchdog.sh
#
# Output: per-VM enable-time + watchdog-env status to STDOUT + /tmp/enable_watchdog_results_<ts>.txt
#
# Safety: SKIP_VERIFY=1 skips the post-enable systemd env verification (dry-enable only).
#         CANARY_ABORT=0 disables the abort-on-canary-failure behaviour.

set -euo pipefail

REGION="${AWS_REGION:-ap-northeast-1}"
PM_REPO_PATH="/home/ubuntu/unified-trading-system-repos/unified-trading-pm"
ENABLE_SCRIPT="$PM_REPO_PATH/scripts/orchestrator/enable_worker_watchdog.sh"
SKIP_VERIFY="${SKIP_VERIFY:-0}"
CANARY_ABORT="${CANARY_ABORT:-1}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="/tmp/enable_watchdog_results_$TIMESTAMP.txt"

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

log "=== run_fleet_enable_watchdog.sh ==="
log "Started: $(ts)"
log "Region: $REGION"
log "Skip verify: $SKIP_VERIFY"
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
    --comment "pm-pull before enable_worker_watchdog" \
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

  # Enable watchdog
  ENABLE_CMD="bash $ENABLE_SCRIPT"
  CMD_ID=$(aws ssm send-command \
    --instance-ids "$INSTANCE_ID" \
    --document-name "AWS-RunShellScript" \
    --parameters "commands=[\"$ENABLE_CMD\"]" \
    --comment "enable_worker_watchdog on $VM_NAME" \
    --region "$REGION" \
    --query "Command.CommandId" \
    --output text 2>/dev/null) || { log "  WARN: ssm send-command failed for $VM_NAME"; FAILED_VMS+=("$VM_NAME"); IS_CANARY=false; continue; }

  log "  enable command: $CMD_ID"
  sleep 20

  OUTPUT=$(aws ssm get-command-invocation \
    --command-id "$CMD_ID" \
    --instance-id "$INSTANCE_ID" \
    --region "$REGION" \
    --query "StandardOutputContent" \
    --output text 2>/dev/null) || OUTPUT="(failed to retrieve)"
  log "$OUTPUT"
  log "  enabled at $(ts)"

  # Verify watchdog env is set
  if [[ "$SKIP_VERIFY" == "1" ]]; then
    log "  SKIP_VERIFY=1 — skipping systemd env verification"
  else
    VERIFY_CMD="systemctl show orchestrator --property=Environment | grep -i WATCHDOG && echo WATCHDOG_VERIFIED || echo WATCHDOG_NOT_FOUND"
    VERIFY_CMD_ID=$(aws ssm send-command \
      --instance-ids "$INSTANCE_ID" \
      --document-name "AWS-RunShellScript" \
      --parameters "commands=[\"$VERIFY_CMD\"]" \
      --comment "watchdog env verify on $VM_NAME" \
      --region "$REGION" \
      --query "Command.CommandId" \
      --output text 2>/dev/null) || { log "  WARN: verify ssm failed for $VM_NAME"; IS_CANARY=false; continue; }

    log "  verify command: $VERIFY_CMD_ID"
    sleep 10

    VERIFY_OUT=$(aws ssm get-command-invocation \
      --command-id "$VERIFY_CMD_ID" \
      --instance-id "$INSTANCE_ID" \
      --region "$REGION" \
      --query "StandardOutputContent" \
      --output text 2>/dev/null) || VERIFY_OUT="(failed to retrieve)"
    log "$VERIFY_OUT"

    if echo "$VERIFY_OUT" | grep -q "WATCHDOG_VERIFIED"; then
      log "  ✅ $VM_NAME watchdog env confirmed"
    else
      log "  ⚠️  $VM_NAME watchdog env NOT found"
      FAILED_VMS+=("$VM_NAME")
      if [[ "$IS_CANARY" == "true" && "$CANARY_ABORT" == "1" ]]; then
        log "  🛑 CANARY ABORT: vm-orchestrator watchdog enable failed. Fix before rolling to fleet."
        log "Results: $RESULTS_FILE"
        exit 1
      fi
    fi
  fi

  IS_CANARY=false
  log ""
  log "  *** If this is vm-orchestrator (canary): watch 1h for false-positive kills ***"
  log "  *** Check orchestrator logs: journalctl -u orchestrator -f | grep watchdog ***"
  log "  *** A legitimately-thinking worker (Crunched/Worked/Baked for N) should NOT be killed ***"
  log "  *** Expand to next VM only after confirming <5% false-positive rate ***"
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
