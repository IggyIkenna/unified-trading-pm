#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Fleet-wide zombie prune — runs prune_state_db_zombies.py on all 11 orchestrator VMs via AWS SSM.
#
# Prerequisites:
#   - AWS CLI configured with an IAM identity that has ssm:SendCommand on all VM instances
#   - All VMs must have the pm-pull.timer tick (or be manually pulled) so that
#     scripts/orchestrator/prune_state_db_zombies.py exists on the VM filesystem.
#   - Default PM repo path on each VM: /home/ubuntu/unified-trading-system-repos/unified-trading-pm
#
# Usage:
#   DRY_RUN=1 bash scripts/orchestrator/run_fleet_prune.sh    # dry-run on all VMs (default)
#   DRY_RUN=0 bash scripts/orchestrator/run_fleet_prune.sh    # --exec on all VMs
#
# Output: before/after counts per VM, written to /tmp/prune_results_<ts>.txt

set -euo pipefail

REGION="${AWS_REGION:-ap-northeast-1}"
DRY_RUN="${DRY_RUN:-1}"
PM_REPO_PATH="/home/ubuntu/unified-trading-system-repos/unified-trading-pm"
SCRIPT_PATH="$PM_REPO_PATH/scripts/orchestrator/prune_state_db_zombies.py"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="/tmp/prune_results_$TIMESTAMP.txt"

# All 11 orchestrator VM instance IDs (from orchestrator_vm_registry.yaml, 2026-05-29)
INSTANCE_IDS=(
  "i-05805eb07fdf180b6"   # vm-defi
  "i-003be935f72c13d51"   # vm-cefi
  "i-0a663001399ef5f49"   # vm-tradfi
  "i-005e1bada21b1653f"   # vm-sports
  "i-063bc8dbf59f36220"   # vm-prediction
  "i-02294132088f23e50"   # vm-ml
  "i-0e51b9c73666b3a8b"   # vm-trading-core
  "i-0e89a5f6bd7123521"   # vm-operator-ops
  "i-06e33c6e188798333"   # vm-cross-cutting
  "i-007e8d99d12831578"   # vm-orchestrator
)

VM_NAMES=(
  "vm-defi"
  "vm-cefi"
  "vm-tradfi"
  "vm-sports"
  "vm-prediction"
  "vm-ml"
  "vm-trading-core"
  "vm-operator-ops"
  "vm-cross-cutting"
  "vm-orchestrator"
)

if [[ "$DRY_RUN" == "1" ]]; then
  EXEC_FLAG=""
  MODE="DRY-RUN"
else
  EXEC_FLAG="--exec"
  MODE="EXEC"
fi

echo "Fleet zombie prune — mode=$MODE — $(date -u)" | tee "$RESULTS_FILE"
echo "Region: $REGION" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

# Step 1: ensure PM repo is pulled on all VMs (so the script exists)
echo "=== Step 1: Pull PM repo on all VMs ===" | tee -a "$RESULTS_FILE"
PULL_CMD="cd $PM_REPO_PATH && git fetch origin live-defi-rollout && git rebase origin/live-defi-rollout && echo pull-ok"

PULL_COMMAND_IDS=()
for INSTANCE_ID in "${INSTANCE_IDS[@]}"; do
  CMD_ID=$(aws ssm send-command \
    --instance-ids "$INSTANCE_ID" \
    --document-name "AWS-RunShellScript" \
    --parameters "commands=[\"$PULL_CMD\"]" \
    --comment "pm-pull for prune script" \
    --region "$REGION" \
    --query "Command.CommandId" \
    --output text)
  PULL_COMMAND_IDS+=("$CMD_ID")
  echo "  Sent pull to $INSTANCE_ID → command $CMD_ID" | tee -a "$RESULTS_FILE"
done

echo "  Waiting 30s for pulls to complete..." | tee -a "$RESULTS_FILE"
sleep 30

# Step 2: Run the prune script on all VMs (in parallel)
echo "" | tee -a "$RESULTS_FILE"
echo "=== Step 2: Run prune script (mode=$MODE) on all VMs ===" | tee -a "$RESULTS_FILE"
PRUNE_CMD="ORCHESTRATOR_MODE=live python3 $SCRIPT_PATH $EXEC_FLAG"

PRUNE_COMMAND_IDS=()
for INSTANCE_ID in "${INSTANCE_IDS[@]}"; do
  CMD_ID=$(aws ssm send-command \
    --instance-ids "$INSTANCE_ID" \
    --document-name "AWS-RunShellScript" \
    --parameters "commands=[\"$PRUNE_CMD\"]" \
    --comment "zombie prune $MODE" \
    --region "$REGION" \
    --query "Command.CommandId" \
    --output text)
  PRUNE_COMMAND_IDS+=("$CMD_ID")
  echo "  Sent prune to $INSTANCE_ID → command $CMD_ID" | tee -a "$RESULTS_FILE"
done

echo "  Waiting 60s for prune commands to complete..." | tee -a "$RESULTS_FILE"
sleep 60

# Step 3: Collect results
echo "" | tee -a "$RESULTS_FILE"
echo "=== Step 3: Results ===" | tee -a "$RESULTS_FILE"

for i in "${!INSTANCE_IDS[@]}"; do
  INSTANCE_ID="${INSTANCE_IDS[$i]}"
  VM_NAME="${VM_NAMES[$i]}"
  CMD_ID="${PRUNE_COMMAND_IDS[$i]}"

  echo "" | tee -a "$RESULTS_FILE"
  echo "--- $VM_NAME ($INSTANCE_ID) ---" | tee -a "$RESULTS_FILE"

  OUTPUT=$(aws ssm get-command-invocation \
    --command-id "$CMD_ID" \
    --instance-id "$INSTANCE_ID" \
    --region "$REGION" \
    --query "StandardOutputContent" \
    --output text 2>&1)
  echo "$OUTPUT" | tee -a "$RESULTS_FILE"
done

echo "" | tee -a "$RESULTS_FILE"
echo "Results saved to $RESULTS_FILE" | tee -a "$RESULTS_FILE"
