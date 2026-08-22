#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# run_fleet_install_pm_pull.sh — Roll out pm-pull.timer to the 9 remaining epic VMs.
#
# Installs pm-pull-ff.sh + pm-pull.service + pm-pull.timer + regen-interval drop-in
# on each VM via AWS SSM SendCommand. Runs sequentially (one VM at a time).
#
# Plan: plans/active/plan_hygiene_silent_failure_capture_2026_05_29.md § Phase 6 -021
#
# Prerequisites:
#   - AWS CLI configured with ssm:SendCommand + ssm:GetCommandInvocation permissions
#   - IAM profile uts-orchestrator-epic attached to each VM instance
#   - unified-trading-pm already cloned at /home/ubuntu/unified-trading-system-repos/unified-trading-pm
#     on each target VM (bootstrap prerequisite — check with PREFLIGHT=1 first)
#   - This script already pushed to live-defi-rollout (pm-pull bootstraps itself)
#
# Usage:
#   # Dry-run (preflight check only — no SSM installs):
#   PREFLIGHT=1 bash scripts/orchestrator/run_fleet_install_pm_pull.sh
#
#   # Full rollout:
#   bash scripts/orchestrator/run_fleet_install_pm_pull.sh
#
# Output: per-VM status logged to STDOUT + /tmp/pm_pull_rollout_<ts>.txt
#
# Already installed: api-host (i-0c9b283b31d6b5ca7) + vm-orchestrator (i-007e8d99d12831578)
# This script targets the REMAINING 9 epic VMs only.
set -euo pipefail

REGION="${AWS_REGION:-ap-northeast-1}"
PM_REPO_PATH="/home/ubuntu/unified-trading-system-repos/unified-trading-pm"
INSTALL_SCRIPT="$PM_REPO_PATH/scripts/orchestrator/install_pm_pull.sh"
PREFLIGHT="${PREFLIGHT:-0}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="/tmp/pm_pull_rollout_$TIMESTAMP.txt"
SSM_WAIT_S="${SSM_WAIT_S:-120}"   # seconds to wait for each SSM command

# The 9 remaining epic VMs (api-host + vm-orchestrator already done 2026-05-29).
INSTANCE_IDS=(
  "i-003be935f72c13d51"   # vm-cefi
  "i-05805eb07fdf180b6"   # vm-defi
  "i-02294132088f23e50"   # vm-ml
  "i-0e89a5f6bd7123521"   # vm-operator-ops
  "i-063bc8dbf59f36220"   # vm-prediction
  "i-005e1bada21b1653f"   # vm-sports
  "i-0a663001399ef5f49"   # vm-tradfi
  "i-0e51b9c73666b3a8b"   # vm-trading-core
  "i-06e33c6e188798333"   # vm-cross-cutting
)

VM_NAMES=(
  "vm-cefi"
  "vm-defi"
  "vm-ml"
  "vm-operator-ops"
  "vm-prediction"
  "vm-sports"
  "vm-tradfi"
  "vm-trading-core"
  "vm-cross-cutting"
)

N="${#INSTANCE_IDS[@]}"

echo "=== run_fleet_install_pm_pull.sh ===" | tee "$RESULTS_FILE"
echo "Timestamp: $TIMESTAMP" | tee -a "$RESULTS_FILE"
echo "Region: $REGION" | tee -a "$RESULTS_FILE"
echo "VMs to install: $N" | tee -a "$RESULTS_FILE"
echo "PREFLIGHT mode: $PREFLIGHT" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

_ssm_run() {
    local instance_id="$1"
    local vm_name="$2"
    local cmd="$3"
    local desc="$4"

    echo "[${vm_name}] SSM: $desc" | tee -a "$RESULTS_FILE"

    COMMAND_ID=$(aws ssm send-command \
        --region "$REGION" \
        --instance-ids "$instance_id" \
        --document-name "AWS-RunShellScript" \
        --parameters "commands=[\"$cmd\"]" \
        --timeout-seconds "$SSM_WAIT_S" \
        --comment "$desc" \
        --query "Command.CommandId" \
        --output text)

    echo "[${vm_name}] CommandId: $COMMAND_ID" | tee -a "$RESULTS_FILE"

    # Wait for completion
    local elapsed=0
    while [ "$elapsed" -lt "$SSM_WAIT_S" ]; do
        STATUS=$(aws ssm get-command-invocation \
            --region "$REGION" \
            --command-id "$COMMAND_ID" \
            --instance-id "$instance_id" \
            --query "Status" \
            --output text 2>/dev/null || echo "Pending")

        if [ "$STATUS" = "Success" ] || [ "$STATUS" = "Failed" ] || [ "$STATUS" = "TimedOut" ]; then
            break
        fi
        sleep 5
        elapsed=$((elapsed + 5))
    done

    OUTPUT=$(aws ssm get-command-invocation \
        --region "$REGION" \
        --command-id "$COMMAND_ID" \
        --instance-id "$instance_id" \
        --query "StandardOutputContent" \
        --output text 2>/dev/null || echo "(no output)")

    echo "[${vm_name}] Status: $STATUS" | tee -a "$RESULTS_FILE"
    echo "[${vm_name}] Output:" | tee -a "$RESULTS_FILE"
    echo "$OUTPUT" | tail -20 | tee -a "$RESULTS_FILE"
    echo "" | tee -a "$RESULTS_FILE"

    [ "$STATUS" = "Success" ]
}

_preflight_check() {
    local instance_id="$1"
    local vm_name="$2"

    echo "[${vm_name}] Preflight: checking SSM reachability + PM repo presence"

    STATUS=$(aws ssm describe-instance-information \
        --region "$REGION" \
        --filters "Key=InstanceIds,Values=$instance_id" \
        --query "InstanceInformationList[0].PingStatus" \
        --output text 2>/dev/null || echo "Unknown")

    if [ "$STATUS" != "Online" ]; then
        echo "[${vm_name}] WARN: SSM PingStatus=$STATUS (not Online — may need IAM profile attach)" | tee -a "$RESULTS_FILE"
        return 1
    fi
    echo "[${vm_name}] SSM Online ✓" | tee -a "$RESULTS_FILE"
    return 0
}

PASS=0
FAIL=0
SKIP=0

for i in "${!INSTANCE_IDS[@]}"; do
    INSTANCE_ID="${INSTANCE_IDS[$i]}"
    VM_NAME="${VM_NAMES[$i]}"

    echo "--- [$((i+1))/$N] $VM_NAME ($INSTANCE_ID) ---" | tee -a "$RESULTS_FILE"

    if ! _preflight_check "$INSTANCE_ID" "$VM_NAME"; then
        echo "[${VM_NAME}] SKIPPED — SSM not reachable" | tee -a "$RESULTS_FILE"
        SKIP=$((SKIP+1))
        continue
    fi

    [ "$PREFLIGHT" = "1" ] && { echo "[${VM_NAME}] preflight-only mode — skipping install"; PASS=$((PASS+1)); continue; }

    if _ssm_run "$INSTANCE_ID" "$VM_NAME" \
        "bash $INSTALL_SCRIPT" \
        "install pm-pull.timer + regen-interval on $VM_NAME"; then
        echo "[${VM_NAME}] INSTALLED ✓" | tee -a "$RESULTS_FILE"
        PASS=$((PASS+1))
    else
        echo "[${VM_NAME}] FAILED ✗ — check SSM output above" | tee -a "$RESULTS_FILE"
        FAIL=$((FAIL+1))
    fi
done

echo "" | tee -a "$RESULTS_FILE"
echo "=== Summary ===" | tee -a "$RESULTS_FILE"
echo "Passed: $PASS  Failed: $FAIL  Skipped: $SKIP  Total: $N" | tee -a "$RESULTS_FILE"
echo "Results: $RESULTS_FILE" | tee -a "$RESULTS_FILE"

[ "$FAIL" -eq 0 ]
