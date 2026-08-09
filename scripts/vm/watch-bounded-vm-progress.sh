#!/usr/bin/env bash
# Epic: sports_master
# Lifecycle: reusable
# Delete-when: no open todo needs a bounded VM watchdog (re-check before deleting; async-wait
#   HARD RULE requires this pattern for every future VM launch, not just the sports census).
#
# Why this exists: async-wait HARD RULE bans fire-and-forget VM launches -- every launch needs a
# run_in_background heartbeat watchdog verifying STARTED, ongoing progress, and a genuine terminal
# state (gcloud describe returning NOT_FOUND after self-delete -- an early bootstrap log line or a
# report's mere existence is NOT sufficient evidence; a checkpoint-flushed report can look
# "complete" for hours while the VM is still mid-walk).
#
# This script is BOUNDED (exits after MAX_ROUNDS regardless of VM state) by design: a long
# corpus-scale walk (e.g. the sports schema census, ~2255 days point-by-point) can run for hours,
# far past any single interactive session/context window. Exhausting all rounds with the VM still
# RUNNING and non-stalled is a NORMAL, EXPECTED exit -- re-invoke this same script again (same
# args) to arm a fresh cycle. Only a NOT_FOUND status is a real terminal signal.
#
# Traps hit building this (2026-08-09 sports schema census):
#   - Do NOT wrap the launch in `nohup ... & disown` with output redirected to /dev/null "for
#     safety" -- that makes the run_in_background harness see the *launcher* exit immediately
#     (task reports "completed") while the actual watchdog keeps running invisibly with no
#     tracked output. Just run this script directly under run_in_background; the harness handles
#     backgrounding and output capture on its own.
#   - `gcloud storage du -s` byte-count staying flat for one round is not automatically a stall --
#     confirm via the `validated_lines` counter too before treating stall_count as meaningful.
#
# Usage:
#   watch-bounded-vm-progress.sh <VM_NAME> <ZONE> <LOG_URI> <REPORT_URI> [MAX_ROUNDS] [SLEEP_SECS]
#
# Example (sports schema census, instruments-store leg):
#   watch-bounded-vm-progress.sh \
#     sports-schema-census-instruments-store-20260809-224053 \
#     asia-northeast1-c \
#     gs://deployment-scripts-central-element-323112/vm-logs/sports-schema-census-instruments-store-20260809-224053/run.log \
#     gs://instruments-store-sports-prd-central-element-323112/_index/audit/sports_reference_schema_census_sports-schema-census-instruments-store-20260809-224053.parquet
set -euo pipefail

VM="${1:?VM_NAME required}"
ZONE="${2:?ZONE required}"
LOG_URI="${3:?LOG_URI required}"
REPORT_URI="${4:?REPORT_URI required}"
MAX_ROUNDS="${5:-9}"
SLEEP_SECS="${6:-180}"
stall_count=0
prev_bytes=-1

echo "[watchdog] $(date -u +%FT%TZ) started, watching ${VM}"

for round in $(seq 1 "${MAX_ROUNDS}"); do
    sleep "${SLEEP_SECS}"
    status=$(gcloud compute instances describe "${VM}" --zone="${ZONE}" --format='value(status)' 2>/dev/null || echo "NOT_FOUND")
    bytes=$(gcloud storage du -s "${LOG_URI}" 2>/dev/null | awk '{print $1}')
    bytes="${bytes:-0}"
    validated=$(gcloud storage cat "${LOG_URI}" 2>/dev/null | grep -c "validated" || true)
    if [[ "${bytes}" == "${prev_bytes}" ]]; then
        stall_count=$((stall_count + 1))
    else
        stall_count=0
    fi
    prev_bytes="${bytes}"
    echo "[watchdog] $(date -u +%FT%TZ) round ${round}: status=${status} log_bytes=${bytes} validated_lines=${validated} stall_count=${stall_count}"
    if [[ "${status}" == "NOT_FOUND" ]]; then
        echo "[watchdog] $(date -u +%FT%TZ) instance gone (self-deleted) -- checking terminal state"
        break
    fi
done

echo "[watchdog] $(date -u +%FT%TZ) checking report parquet"
gcloud storage ls "${REPORT_URI}" 2>&1 || echo "[watchdog] report NOT found"
echo "[watchdog] $(date -u +%FT%TZ) done"
