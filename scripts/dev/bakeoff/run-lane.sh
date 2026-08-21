#!/usr/bin/env bash
# Epic: orchestrator_master (multi_provider_model_capability_bakeoff_2026_08_19)
# Lifecycle: TEMPORARY — delete when that plan archives.
#
# WHY THIS EXISTS: loops one model's remaining task queue through run-attempt.sh
# sequentially — the same slot's single git checkout can only run one attempt's
# branch at a time, so a lane's 6 tasks cannot run concurrently with each other
# (different lanes, in different slots, still run in parallel via separate
# invocations of this script).
#
# Caller must export ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN / ANTHROPIC_MODEL
# before invoking, same requirement as run-attempt.sh.
#
# Usage: run-lane.sh <slot> <repo> <model_label> <queue_dir> <out_root> [interval_s] [context_window]
set -uo pipefail  # deliberately NOT -e: one task's failure must not abort the rest of the queue

SLOT="$1"
REPO="$2"
MODEL_LABEL="$3"
QUEUE_DIR="$4"
OUT_ROOT="$5"
INTERVAL="${6:-30}"
CTX_WINDOW="${7:-1000000}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for prompt_file in "$QUEUE_DIR"/*.prompt.txt; do
  [[ -e "$prompt_file" ]] || continue
  slug=$(basename "$prompt_file" .prompt.txt)
  echo "=== lane $MODEL_LABEL (slot $SLOT): starting $slug ==="
  bash "$SCRIPT_DIR/run-attempt.sh" "$SLOT" "$REPO" "$MODEL_LABEL" "$slug" "$prompt_file" "$OUT_ROOT" "$INTERVAL" "$CTX_WINDOW"
  echo "=== lane $MODEL_LABEL (slot $SLOT): finished $slug (exit $?) ==="
done
echo "=== lane $MODEL_LABEL (slot $SLOT): queue complete ==="
