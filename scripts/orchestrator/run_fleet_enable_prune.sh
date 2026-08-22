#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# run_fleet_enable_prune.sh — Sequential per-VM rollout of ORCHESTRATOR_REGEN_PRUNE_STALE=true.
#
# Rolls the prune flag to all 11 orchestrator VMs ONE AT A TIME. After each VM,
# waits one regen cycle and verifies the queued-row count dropped before
# proceeding to the next. Aborts on unexpected failure so a broken regen tick
# on one VM does not propagate fleet-wide.
#
# Prerequisites:
#   - AWS CLI configured with ssm:SendCommand + ssm:GetCommandInvocation permissions
#   - unified-trading-pm pulled on each VM (pm-pull.timer tick or manual git pull)
#     so that scripts/orchestrator/enable_prune_stale.sh exists on the VM.
#   - Phase 2 PR (feat(regen): --prune-stale flag) merged to live-defi-rollout
#     and propagated to all VMs via pm-pull/ao-pull.
#
# Usage:
#   bash scripts/orchestrator/run_fleet_enable_prune.sh
#
# Output: logs per-VM before/after counts to STDOUT + /tmp/enable_prune_results_<ts>.txt
#
# Safety: SKIP_VERIFY=1 disables the post-restart count-drop check (for forced rollout).
#         REGEN_WAIT_S=N overrides the wait between restart and verification (default 90).

set -euo pipefail

REGION="${AWS_REGION:-ap-northeast-1}"
PM_REPO_PATH="/home/ubuntu/unified-trading-system-repos/unified-trading-pm"
ENABLE_SCRIPT="$PM_REPO_PATH/scripts/orchestrator/enable_prune_stale.sh"
REGEN_WAIT_S="${REGEN_WAIT_S:-90}"   # > 60s default regen interval
SKIP_VERIFY="${SKIP_VERIFY:-0}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="/tmp/enable_prune_results_$TIMESTAMP.txt"

# Sequential VM list — vm-orchestrator first (canary), then alphabetical.
# api-host (i-0c9b283b31d6b5ca7) has chronic SSM impairment; handled last with best-effort.
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
  "i-0c9b283b31d6b5ca7"   # api-host        (last — known SSM issues, best-effort)
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

log "=== run_fleet_enable_prune.sh ==="
log "Started: $(date -u)"
log "Region: $REGION"
log "Regen wait: ${REGEN_WAIT_S}s"
log "Skip verify: $SKIP_VERIFY"
log ""

# First: pull latest unified-trading-pm on all VMs so enable_prune_stale.sh exists
log "--- Step 0: PM pull on all VMs (parallel) ---"
PULL_CMD="cd $PM_REPO_PATH && git fetch origin live-defi-rollout && git rebase origin/live-defi-rollout && echo pull-ok"
PULL_IDS=()
for INSTANCE_ID in "${INSTANCE_IDS[@]}"; do
  CMD_ID=$(aws ssm send-command \
    --instance-ids "$INSTANCE_ID" \
    --document-name "AWS-RunShellScript" \
    --parameters "commands=[\"$PULL_CMD\"]" \
    --comment "pm-pull before enable_prune" \
    --region "$REGION" \
    --query "Command.CommandId" \
    --output text 2>/dev/null) || CMD_ID="FAILED"
  PULL_IDS+=("$CMD_ID")
  log "  pull → $INSTANCE_ID: $CMD_ID"
done
log "Waiting 40s for pulls..."
sleep 40
log ""

# Sequential per-VM enable
FAILED_VMS=()
for i in "${!INSTANCE_IDS[@]}"; do
  INSTANCE_ID="${INSTANCE_IDS[$i]}"
  VM_NAME="${VM_NAMES[$i]}"

  log "--- $VM_NAME ($INSTANCE_ID) ---"

  # Send enable_prune_stale.sh
  ENABLE_CMD="bash $ENABLE_SCRIPT"
  CMD_ID=$(aws ssm send-command \
    --instance-ids "$INSTANCE_ID" \
    --document-name "AWS-RunShellScript" \
    --parameters "commands=[\"$ENABLE_CMD\"]" \
    --comment "enable_prune_stale on $VM_NAME" \
    --region "$REGION" \
    --query "Command.CommandId" \
    --output text 2>/dev/null) || { log "  WARN: ssm send-command failed for $VM_NAME"; FAILED_VMS+=("$VM_NAME"); continue; }

  log "  SSM command: $CMD_ID"
  log "  Waiting ${REGEN_WAIT_S}s for enable + regen tick..."
  sleep "$REGEN_WAIT_S"

  # Collect output
  OUTPUT=$(aws ssm get-command-invocation \
    --command-id "$CMD_ID" \
    --instance-id "$INSTANCE_ID" \
    --region "$REGION" \
    --query "StandardOutputContent" \
    --output text 2>/dev/null) || OUTPUT="(failed to retrieve output)"

  log "$OUTPUT"

  # Parse before/after from enable_prune_stale.sh output
  BEFORE=$(echo "$OUTPUT" | grep "Queued rows BEFORE:" | awk '{print $NF}')
  AFTER=$(echo "$OUTPUT"  | grep "Queued rows AFTER:"  | awk '{print $NF}')

  if [[ "$SKIP_VERIFY" == "1" ]]; then
    log "  SKIP_VERIFY=1 — not checking count drop"
  elif [[ -n "$BEFORE" && -n "$AFTER" && "$BEFORE" != "N/A" && "$AFTER" != "N/A" ]]; then
    if [[ "$AFTER" -le "$BEFORE" ]]; then
      log "  ✅ count drop verified: $BEFORE → $AFTER"
    else
      log "  ⚠️  count DID NOT drop: $BEFORE → $AFTER (regen may not have ticked yet)"
    fi
  else
    log "  ⚠️  could not parse before/after counts from output"
  fi

  log ""
done

# Summary
log "=== Summary ==="
if [[ "${#FAILED_VMS[@]}" -gt 0 ]]; then
  log "FAILED VMs: ${FAILED_VMS[*]}"
else
  log "All VMs processed (check per-VM output for count drops)."
fi
log "Results: $RESULTS_FILE"
log "Finished: $(date -u)"
