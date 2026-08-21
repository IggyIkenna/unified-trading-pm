#!/usr/bin/env bash
# Epic: orchestrator_master (multi_provider_model_capability_bakeoff_2026_08_19)
# Lifecycle: TEMPORARY — delete when that plan archives.
#
# WHY THIS EXISTS: runs one real bake-off attempt (one model, one task) as an
# isolated, non-interactive `claude -p` subprocess on its own branch, with a
# companion usage-poll.sh watcher sampling context/token/turn stats at <=60s
# cadence for the attempt's full duration (operator requirement 2026-08-19).
# Caller must export ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN / ANTHROPIC_MODEL
# (or ANTHROPIC_API_KEY, provider-dependent) before invoking — this script does
# not know which of the 6 models' credentials to use, only how to run one.
#
# Usage: run-attempt.sh <slot_num> <repo_name> <model_label> <task_slug> <prompt_file> <out_dir_root> [poll_interval_s] [context_window_tokens]
set -euo pipefail

SLOT="$1"
REPO="$2"
MODEL_LABEL="$3"
TASK_SLUG="$4"
PROMPT_FILE="$5"
OUT_ROOT="$6"
POLL_INTERVAL="${7:-30}"
CONTEXT_WINDOW="${8:-1000000}"

REPO_DIR="/active/unified-trading-system-repos/.tabs/${SLOT}/${REPO}"
BRANCH="bakeoff/${MODEL_LABEL}/${TASK_SLUG}"
OUT_DIR="${OUT_ROOT}/${MODEL_LABEL}/${TASK_SLUG}"
SESSION_UUID=$(python3 -c 'import uuid; print(uuid.uuid4())')
PROJECT_DIR_ENCODED=$(echo "$REPO_DIR" | sed 's/[\/.]/-/g')

mkdir -p "$OUT_DIR"
cd "$REPO_DIR"

git fetch origin live-defi-rollout --quiet
git checkout live-defi-rollout --quiet
git reset --hard origin/live-defi-rollout --quiet
git checkout -B "$BRANCH" --quiet

echo "attempt: slot=$SLOT repo=$REPO model=$MODEL_LABEL task=$TASK_SLUG branch=$BRANCH session=$SESSION_UUID" | tee "$OUT_DIR/meta.txt"
date -u -Iseconds > "$OUT_DIR/started_at.txt"

nohup claude -p "$(cat "$PROMPT_FILE")" \
  --output-format json \
  --session-id "$SESSION_UUID" \
  --dangerously-skip-permissions \
  > "$OUT_DIR/result.json" 2> "$OUT_DIR/stderr.log" &
CLAUDE_PID=$!
echo "$CLAUDE_PID" > "$OUT_DIR/claude.pid"

nohup bash "$(dirname "$0")/usage-poll.sh" "$SESSION_UUID" "$CLAUDE_PID" "$OUT_DIR" "$PROJECT_DIR_ENCODED" "$POLL_INTERVAL" "$CONTEXT_WINDOW" \
  > "$OUT_DIR/poller.log" 2>&1 &
POLLER_PID=$!
echo "$POLLER_PID" > "$OUT_DIR/poller.pid"

set +e  # a non-zero claude exit (any real API/task failure) must NOT abort this
        # script under errexit — the postprocessing below (exit_code.txt,
        # finished_at.txt, git_status.txt) must always run, or a failed attempt
        # silently loses its own failure evidence (found the hard way: 2 real
        # multi-hour attempts that hit a late quota error left NO exit_code.txt/
        # finished_at.txt/git_status.txt at all).
wait "$CLAUDE_PID"
CLAUDE_EXIT=$?
set -e
date -u -Iseconds > "$OUT_DIR/finished_at.txt"
echo "$CLAUDE_EXIT" > "$OUT_DIR/exit_code.txt"

wait "$POLLER_PID" 2>/dev/null || true

git status --porcelain > "$OUT_DIR/git_status.txt"
git diff --stat >> "$OUT_DIR/git_status.txt" 2>/dev/null || true

echo "attempt done: exit=$CLAUDE_EXIT out_dir=$OUT_DIR branch=$BRANCH"
